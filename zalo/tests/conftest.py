"""Integration fixture — spawn ``python -m zalo_module.cli`` subprocesses.

The child env REPLACES ``PYTHONPATH`` with ``<repo>/src`` only (never appended
to the ambient value), so nothing outside this repo — in particular any
``notary*`` package — is importable inside module subprocesses. Runtime state
(DB, access.jsonl, media/packages/outbox) lives in a per-test tmp dir.
"""
from __future__ import annotations

import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"


class ModuleProcess:
    """A zalo-intake module runtime driven entirely through CLI subprocesses.

    ``start``/``stop``/``restart`` manage the persistent side (``cli serve``);
    ``replay``/``cli``/``python`` run one-shot subprocesses. ``get_capture``
    and ``access_log`` inspect the on-disk runtime directly from the test
    process — they model an outside observer, not the module.
    """

    def __init__(self, runtime_dir: Path, python_exe: str | None = None):
        self.runtime_dir = Path(runtime_dir)
        self.db_path = self.runtime_dir / "zalo_intake.db"
        self.port = self._free_port()
        self._python = python_exe or sys.executable
        self._proc: subprocess.Popen | None = None
        self._log = None
        self.env = self._build_env()

    # -- environment ---------------------------------------------------------
    def _build_env(self) -> dict:
        env = dict(os.environ)
        # REPLACE, not append: the ambient PYTHONPATH must not leak in.
        env["PYTHONPATH"] = str(SRC_DIR)
        env.pop("PYTHONHOME", None)
        env["ZALO_INTAKE_RUNTIME_DIR"] = str(self.runtime_dir)
        env["ZALO_INTAKE_DB_URL"] = f"sqlite:///{self.db_path.as_posix()}"
        # serve fails fast without a registered consumer (decision sheet §2);
        # the fixture models a serve environment, so provide a test consumer.
        env["ZALO_INTAKE_CONSUMER_ID"] = (
            "c0000000-0000-4000-8000-000000000001"
        )
        return env

    @staticmethod
    def _free_port() -> int:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    # -- subprocess helpers ----------------------------------------------------
    def cli(self, *cli_args: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run ``python -m zalo_module.cli <args>`` in the isolated env."""
        return subprocess.run(
            [self._python, "-m", "zalo_module.cli", *cli_args],
            cwd=REPO_ROOT,
            env=self.env,
            capture_output=True,
            text=True,
            check=check,
            timeout=60,
        )

    def python(self, code: str) -> subprocess.CompletedProcess:
        """Run ``python -c <code>`` in the same isolated env."""
        return subprocess.run(
            [self._python, "-c", code],
            cwd=REPO_ROOT,
            env=self.env,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )

    # -- persistent process ----------------------------------------------------
    def start(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            return
        log_path = self.runtime_dir / "serve.log"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._log = open(log_path, "ab")
        self._proc = subprocess.Popen(
            [
                self._python,
                "-m",
                "zalo_module.cli",
                "serve",
                "--port",
                str(self.port),
            ],
            cwd=REPO_ROOT,
            env=self.env,
            stdout=self._log,
            stderr=subprocess.STDOUT,
        )
        self._wait_ready()

    def _wait_ready(self, timeout: float = 30.0) -> None:
        url = f"http://127.0.0.1:{self.port}/intake/v1/status"
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._proc.poll() is not None:
                raise RuntimeError(
                    f"serve exited early with {self._proc.returncode}; "
                    f"log: {self.runtime_dir / 'serve.log'}"
                )
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    if resp.status == 200:
                        return
            except OSError:
                pass
            time.sleep(0.25)
        raise TimeoutError(
            f"serve not ready after {timeout}s; log: {self.runtime_dir / 'serve.log'}"
        )

    def stop(self) -> None:
        if self._proc is not None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=15)
            self._proc = None
        if self._log is not None:
            self._log.close()
            self._log = None

    def restart(self) -> None:
        self.stop()
        self.start()

    # -- module-facing helpers ---------------------------------------------------
    def replay(self, event_path) -> dict:
        """``cli replay <event.json>`` -> parsed stdout JSON."""
        out = self.cli("replay", str(event_path))
        return json.loads(out.stdout)

    def status(self) -> dict:
        """``cli status`` -> parsed stdout JSON."""
        out = self.cli("status")
        return json.loads(out.stdout)

    # -- outside-observer helpers (test process, not the module) -----------------
    def get_capture(self, capture_id: str) -> dict | None:
        """Read the ``journal_entries`` row straight from the sqlite DB."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM journal_entries WHERE capture_id = ?",
                (capture_id,),
            ).fetchone()
            return dict(row) if row is not None else None
        finally:
            conn.close()

    def journal_entry_count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0]
        finally:
            conn.close()

    def access_log(self) -> list[dict]:
        path = self.runtime_dir / "access.jsonl"
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def notary_accesses(self) -> list[dict]:
        """Access-log entries outside runtime_root or mentioning 'notary'."""
        root = self.runtime_dir.resolve()
        bad = []
        for entry in self.access_log():
            raw = str(entry.get("path", ""))
            inside = False
            try:
                inside = Path(raw).resolve().is_relative_to(root)
            except (OSError, ValueError):
                inside = False
            if "notary" in raw.lower() or not inside:
                bad.append(entry)
        return bad


@pytest.fixture()
def module_process(tmp_path_factory) -> ModuleProcess:
    """Fresh module runtime per test; serve is started and always torn down."""
    runtime_dir = tmp_path_factory.mktemp("zalo_runtime")
    proc = ModuleProcess(runtime_dir)
    proc.start()
    try:
        yield proc
    finally:
        proc.stop()

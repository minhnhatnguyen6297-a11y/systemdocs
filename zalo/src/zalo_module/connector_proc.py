"""Connector subprocess manager — MIN-103 slice B port.

Ported from ``notary_v2/routers/zalo_inbox.py`` (lines 55-229): spawns
``node connector/bin/run.mjs`` with a whitelist environment, watches the
child on a daemon thread, and records a ``gap_started_at`` marker when a
previously-receiving connector dies unexpectedly.

Differences vs baseline (see ``docs/migration-notes.md``):

- Stateless module: settings/engine arrive as parameters — the module-level
  ``SessionLocal`` of the legacy is replaced by a ``session_factory``
  argument supplied by the API layer.
- ``ZALO_INBOX_BACKEND_URL`` defaults to ``http://{bind}:{port}`` of this
  module; ``ZALO_INBOX_STORAGE_ROOT`` = ``{runtime_root}/media``;
  ``ZALO_CONNECTOR_STATE_ROOT`` = ``settings.connector_state_root``.
- ``serve`` never auto-spawns the connector (deliberate safety choice);
  ``POST /connector/v1/connectors/start`` is the only trigger.
"""
from __future__ import annotations

import atexit
import os
import subprocess
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from zalo_module.intake.engine import (
    InboxConfigurationError,
    _iso,
    utcnow,
)
from zalo_module.models import ConnectorAccount

if TYPE_CHECKING:
    from zalo_module.settings import Settings

_connector_process: subprocess.Popen | None = None
_connector_lock = threading.RLock()
_connector_error: str | None = None
CONNECTOR_STOPPED_MESSAGE = (
    "Zalo connector đã dừng. Kiểm tra cấu hình và thử lại."
)


def _repo_root() -> Path:
    """``<repo>`` — this file lives at ``src/zalo_module/connector_proc.py``."""
    return Path(__file__).resolve().parents[2]


def _connector_entrypoint() -> Path:
    return _repo_root() / "connector" / "bin" / "run.mjs"


def _connector_environment(
    settings: "Settings", *, force_qr: bool = False
) -> dict[str, str]:
    """Whitelist env for the child; raise ``InboxConfigurationError`` early."""
    missing = []
    if not settings.bootstrap_secret:
        missing.append("ZALO_INBOX_BOOTSTRAP_SECRET")
    if not settings.webhook_secret:
        missing.append("ZALO_INBOX_WEBHOOK_SECRET")
    if missing:
        raise InboxConfigurationError(
            f"Thiếu cấu hình connector: {', '.join(missing)}"
        )
    quota_bytes = settings.connector_quota_bytes
    if (
        not isinstance(quota_bytes, int)
        or quota_bytes <= 0
        or quota_bytes > 2**53 - 1
    ):
        raise InboxConfigurationError("ZALO_CONNECTOR_QUOTA_BYTES không hợp lệ")
    retention_hours = settings.connector_retention_hours
    if not retention_hours or retention_hours <= 0:
        raise InboxConfigurationError(
            "ZALO_CONNECTOR_RETENTION_HOURS không hợp lệ"
        )
    child_env = {
        name: os.environ[name]
        for name in ("PATH", "Path", "SYSTEMROOT", "SystemRoot", "TEMP", "TMP")
        if name in os.environ
    }
    child_env.update(
        {
            "ZALO_INBOX_BACKEND_URL": os.getenv(
                "ZALO_INBOX_BACKEND_URL",
                f"http://{settings.bind}:{settings.port}",
            ),
            "ZALO_INBOX_BOOTSTRAP_SECRET": settings.bootstrap_secret,
            "ZALO_INBOX_WEBHOOK_SECRET": settings.webhook_secret,
            "ZALO_INBOX_STORAGE_ROOT": str(
                (Path(settings.runtime_root) / "media").resolve()
            ),
            "ZALO_CONNECTOR_QUOTA_BYTES": str(quota_bytes),
            "ZALO_CONNECTOR_RETENTION_HOURS": str(retention_hours),
            "ZALO_CONNECTOR_PARENT_PID": str(os.getpid()),
            "ZALO_CONNECTOR_STATE_ROOT": str(
                Path(settings.connector_state_root).resolve()
            ),
        }
    )
    if force_qr:
        child_env["ZALO_CONNECTOR_FORCE_QR"] = "1"
    return child_env


def terminate_connector_process() -> None:
    """Terminate the managed child (idempotent); clears the error marker."""
    global _connector_error, _connector_process
    with _connector_lock:
        process = _connector_process
        _connector_process = None
        _connector_error = None
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass


# Backwards-compatible alias matching the legacy private name used by tests.
_terminate_connector_process = terminate_connector_process


def _receiving_connector_identity(
    session_factory: Callable[[], Session],
) -> tuple[str, int] | None:
    """``(account_id, listener_generation)`` of the single receiving account."""
    session = session_factory()
    try:
        account = (
            session.execute(
                select(ConnectorAccount).order_by(
                    ConnectorAccount.created_at.asc(),
                    ConnectorAccount.connector_account_id.asc(),
                )
            )
            .scalars()
            .first()
        )
        if account is not None and account.session_state == "usable":
            return (
                account.connector_account_id,
                account.listener_generation,
            )
        return None
    finally:
        session.close()


def _record_connector_gap(
    identity: tuple[str, int] | None,
    session_factory: Callable[[], Session],
) -> None:
    """Stamp ``gap_started_at`` once when the receiving connector vanishes."""
    if identity is None:
        return
    account_id, listener_generation = identity
    session = session_factory()
    try:
        account = session.get(ConnectorAccount, account_id)
        if (
            account is not None
            and account.session_state == "usable"
            and account.listener_generation == listener_generation
            and account.gap_started_at is None
        ):
            account.gap_started_at = _iso(utcnow())
            session.commit()
    finally:
        session.close()


def _watch_connector_process(
    process: subprocess.Popen,
    identity: tuple[str, int] | None,
    session_factory: Callable[[], Session],
) -> None:
    global _connector_error, _connector_process
    process.wait(timeout=None)
    with _connector_lock:
        if _connector_process is not process:
            return
        _connector_process = None
        _connector_error = CONNECTOR_STOPPED_MESSAGE
        _record_connector_gap(identity, session_factory)


def connector_runtime_error() -> str | None:
    """Sanitized connector error for ops snapshots (``GET /state``)."""
    global _connector_error, _connector_process
    with _connector_lock:
        if (
            _connector_process is not None
            and _connector_process.poll() is not None
        ):
            _connector_error = CONNECTOR_STOPPED_MESSAGE
    return _connector_error


def start_connector_process(
    settings: "Settings",
    session_factory: Callable[[], Session],
    *,
    force_restart: bool = False,
    force_qr: bool = False,
) -> bool:
    """Spawn the connector; returns True when a new process was started.

    Raises ``InboxConfigurationError`` for missing entrypoint/env or an
    immediately-dead child (mapped to 503 by the API layer).
    """
    global _connector_error, _connector_process
    with _connector_lock:
        if _connector_process is not None and _connector_process.poll() is None:
            if not force_restart:
                return False
            terminate_connector_process()
        entrypoint = _connector_entrypoint()
        if not entrypoint.is_file():
            raise InboxConfigurationError("Không tìm thấy Zalo connector")
        child_env = _connector_environment(settings, force_qr=force_qr)
        identity = _receiving_connector_identity(session_factory)
        try:
            _connector_process = subprocess.Popen(
                ["node", str(entrypoint)],
                cwd=str(_repo_root()),
                env=child_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        except OSError as exc:
            raise InboxConfigurationError(
                "Không thể khởi động Zalo connector"
            ) from exc
        _connector_error = None
        if _connector_process.poll() is not None:
            _connector_process = None
            _connector_error = CONNECTOR_STOPPED_MESSAGE
            raise InboxConfigurationError(CONNECTOR_STOPPED_MESSAGE)
        process = _connector_process
        threading.Thread(
            target=_watch_connector_process,
            args=(process, identity, session_factory),
            daemon=True,
        ).start()
        return True


atexit.register(terminate_connector_process)

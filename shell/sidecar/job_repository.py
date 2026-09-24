"""JobRepository — command/job journal ben trong workspace.sqlite3.

Cung FILE SQLite voi UploadWorkspaceStore (plan §3.2) — khong tao
database/scheduler thu hai. Table `sidecar_jobs` giu command identity +
snapshot cho MOI command desktopcommand.v1 (khong chi upload.*):

- `command_id` UNIQUE: resubmit cung id + cung noi dung → tra lai job cu
  (handler khong chay lai — chong replay upload sau restart, §7.4);
  cung id + noi dung khac → JobStore bao `command_id_conflict`.
- `status` + `snapshot_json`: process moi doc lai de materialize job
  cu — non-terminal → JobStore danh dau failed{engine_restarted} roi
  ghi nguoc marker terminal; terminal giu nguyen.
- Reconnect theo `job_id`/`command_id` hoat dong xuyen restart
  (contract §5 Reconnect).

KHONG persist credential/cookie/token/storage_state — snapshot chi gom
truong Job.snapshot() (status/result/error/progress) + identity;
payload tho khong luu (chi request_hash).
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from errors import CommandError

TERMINAL_STATUSES = ("succeeded", "failed", "canceled", "partial")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sidecar_jobs (
    job_id TEXT PRIMARY KEY,
    command_id TEXT NOT NULL UNIQUE,
    request_hash TEXT NOT NULL,
    command TEXT NOT NULL,
    status TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sidecar_jobs_status ON sidecar_jobs(status);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z")


class JobRepository:
    """Journal sidecar_jobs — thread-safe qua lock + connection rieng."""

    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self):
        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------ writes
    def record_submit(self, job):
        """Dong identity khi command duoc nhan (status accepted).

        command_id UNIQUE: trung → command_id_conflict tran ra (JobStore
        da check truoc — day la phong ve cuoi cho truong hop race giua
        hai process/thread ghi cung file)."""
        snap = job.snapshot()
        with self._lock:
            try:
                self._conn.execute(
                    "INSERT INTO sidecar_jobs(job_id, command_id,"
                    " request_hash, command, status, snapshot_json,"
                    " updated_at) VALUES(?,?,?,?,?,?,?)",
                    (job.job_id, job.command_id, job.request_hash,
                     job.command, snap["status"],
                     json.dumps(snap, ensure_ascii=False), _now()))
            except sqlite3.IntegrityError as exc:
                raise CommandError(
                    "command_id_conflict",
                    "command_id da duoc dung cho mot request khac — "
                    "retry co chu y phai dung command_id moi",
                    retryable=False) from exc
            self._conn.commit()

    def record_snapshot(self, snapshot):
        """Upsert snapshot sau moi transition (identity khong doi)."""
        with self._lock:
            self._conn.execute(
                "INSERT INTO sidecar_jobs(job_id, command_id, request_hash,"
                " command, status, snapshot_json, updated_at)"
                " VALUES(?,?,?,?,?,?,?)"
                " ON CONFLICT(job_id) DO UPDATE SET"
                " status=excluded.status,"
                " snapshot_json=excluded.snapshot_json,"
                " updated_at=excluded.updated_at",
                (snapshot["job_id"], snapshot["command_id"], "",
                 snapshot["command"], snapshot["status"],
                 json.dumps(snapshot, ensure_ascii=False), _now()))
            self._conn.commit()

    # ------------------------------------------------------------ reads
    def load_unfinished(self) -> list:
        """Row non-terminal cua process truoc — JobStore se danh dau
        engine_restarted; khong bao gio chay lai handler."""
        marks = ",".join("?" for _ in TERMINAL_STATUSES)
        with self._lock:
            rows = self._conn.execute(
                f"SELECT * FROM sidecar_jobs WHERE status NOT IN ({marks})"
                " ORDER BY updated_at",
                TERMINAL_STATUSES).fetchall()
        return [self._row(r) for r in rows]

    def find_by_command_id(self, command_id) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM sidecar_jobs WHERE command_id = ?",
                (command_id,)).fetchone()
            return self._row(row) if row else None

    def find_by_job_id(self, job_id) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM sidecar_jobs WHERE job_id = ?",
                (job_id,)).fetchone()
            return self._row(row) if row else None

    @staticmethod
    def _row(row) -> dict:
        try:
            snap = json.loads(row["snapshot_json"])
        except (TypeError, ValueError):
            snap = {}
        return {"job_id": row["job_id"], "command_id": row["command_id"],
                "request_hash": row["request_hash"],
                "command": row["command"], "status": row["status"],
                "snapshot": snap, "updated_at": row["updated_at"]}

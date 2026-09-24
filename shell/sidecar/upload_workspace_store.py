"""Upload workspace store — workspace.sqlite3 o data root (MIN-69 plan §3.2).

Mot file SQLite o `<data_root>/workspace.sqlite3` giu trang thai xuyen
website cua luong upload.workflow.v1:

- `kv` — selected_website_id, revision (tang khi website/nguon/binding doi)
- `runs` — binding run_id → website + manifest_path (+sha256) + queue_revision
- `audits` / `run_audits` — audit_id → website + file + khoang ngay; run↔audit
- `browsers` — browser_id → website, trang thai mo/dong
- `workflow_jobs` — thong tin recovery toi thieu (KHONG cookie): command_id,
  request_hash, website/run/browser/audit, record_ids, ket qua da xac minh,
  status. Job con non-terminal cua mot website chan doi website
  (workflow_busy).
- `open_tabs` — record_id dang mo cho kiem tra tren browser cua website
- `needs_reconcile` — ho so can doi chieu truoc khi cho chuan bi lai
- `preferences` — chunk_size/cong_chung_vien/thu_ky THEO website

Khong co truong credential/cookie/token/storage_state — dung y contract §7.4.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

TERMINAL_STATUSES = ("succeeded", "failed", "canceled", "partial")
DEFAULT_CHUNK_SIZE = 10
MIN_CHUNK_SIZE = 1
MAX_CHUNK_SIZE = 30

_SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    website_id TEXT NOT NULL,
    manifest_path TEXT NOT NULL,
    manifest_sha256 TEXT,
    manifest_size INTEGER,
    queue_revision INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_website ON runs(website_id, created_at);
CREATE TABLE IF NOT EXISTS audits (
    audit_id TEXT PRIMARY KEY,
    website_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_sha256 TEXT,
    from_date TEXT,
    to_date TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audits_website ON audits(website_id, created_at);
CREATE TABLE IF NOT EXISTS run_audits (
    run_id TEXT NOT NULL,
    audit_id TEXT NOT NULL,
    bound_at TEXT NOT NULL,
    PRIMARY KEY (run_id, audit_id)
);
CREATE TABLE IF NOT EXISTS browsers (
    browser_id TEXT PRIMARY KEY,
    website_id TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    closed_at TEXT
);
CREATE TABLE IF NOT EXISTS workflow_jobs (
    job_id TEXT PRIMARY KEY,
    command_id TEXT,
    request_hash TEXT,
    command TEXT,
    website_id TEXT,
    browser_id TEXT,
    run_id TEXT,
    audit_id TEXT,
    record_ids TEXT,
    verified_record_ids TEXT,
    status TEXT NOT NULL,
    waiting_on TEXT,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wjobs_website ON workflow_jobs(website_id, status);
CREATE TABLE IF NOT EXISTS open_tabs (
    website_id TEXT NOT NULL,
    run_id TEXT,
    browser_id TEXT,
    record_id INTEGER NOT NULL,
    opened_at TEXT NOT NULL,
    PRIMARY KEY (website_id, record_id)
);
CREATE TABLE IF NOT EXISTS needs_reconcile (
    website_id TEXT NOT NULL,
    run_id TEXT,
    record_id INTEGER NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (website_id, record_id)
);
CREATE TABLE IF NOT EXISTS preferences (
    website_id TEXT PRIMARY KEY,
    chunk_size INTEGER NOT NULL DEFAULT 10,
    cong_chung_vien TEXT,
    thu_ky TEXT,
    updated_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z")


class UploadWorkspaceStore:
    """Store SQLite theo plan §3.2 — thread-safe qua lock + WAL."""

    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self):
        with self._lock:
            self._conn.close()

    # ---------- kv / revision ----------

    def _kv_get(self, key, default=None):
        row = self._conn.execute(
            "SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def _kv_set(self, key, value):
        self._conn.execute(
            "INSERT INTO kv(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value))

    def selected_website_id(self):
        with self._lock:
            v = self._kv_get("selected_website_id")
            return v if v else None

    def revision(self) -> int:
        with self._lock:
            return int(self._kv_get("revision", "0") or 0)

    def bump_revision(self) -> int:
        """Tang revision workspace (doi website/nguon/binding). Tra gia tri moi."""
        with self._lock:
            new = self.revision() + 1
            self._kv_set("revision", str(new))
            self._conn.commit()
            return new

    def select_website(self, website_id) -> int:
        """Ghi website dang chon + bump revision. Tra revision moi."""
        with self._lock:
            self._kv_set("selected_website_id", website_id)
            return self.bump_revision()

    # ---------- runs ----------

    def add_run(self, website_id, run_id, manifest_path, *,
                manifest_sha256=None, manifest_size=None) -> dict:
        with self._lock:
            self._conn.execute(
                "INSERT INTO runs(run_id, website_id, manifest_path, "
                " manifest_sha256, manifest_size, queue_revision, created_at)"
                " VALUES(?,?,?,?,?,0,?) "
                "ON CONFLICT(run_id) DO UPDATE SET "
                " website_id=excluded.website_id,"
                " manifest_path=excluded.manifest_path,"
                " manifest_sha256=excluded.manifest_sha256,"
                " manifest_size=excluded.manifest_size",
                (run_id, website_id, str(manifest_path), manifest_sha256,
                 manifest_size, _now()))
            self._conn.commit()
            return self.run_for(run_id)

    def run_for(self, run_id) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            return dict(row) if row else None

    def latest_run(self, website_id) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM runs WHERE website_id = ? "
                "ORDER BY created_at DESC, rowid DESC LIMIT 1",
                (website_id,)).fetchone()
            return dict(row) if row else None

    def queue_revision(self, run_id) -> int:
        rec = self.run_for(run_id)
        return int(rec["queue_revision"]) if rec else 0

    def bump_queue_revision(self, run_id) -> int:
        with self._lock:
            self._conn.execute(
                "UPDATE runs SET queue_revision = queue_revision + 1 "
                "WHERE run_id = ?", (run_id,))
            self._conn.commit()
            return self.queue_revision(run_id)

    # ---------- audits ----------

    def add_audit(self, website_id, audit_id, file_path, *,
                  file_sha256=None, from_date=None, to_date=None) -> dict:
        with self._lock:
            self._conn.execute(
                "INSERT INTO audits(audit_id, website_id, file_path, "
                " file_sha256, from_date, to_date, created_at)"
                " VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(audit_id) DO UPDATE SET "
                " website_id=excluded.website_id,"
                " file_path=excluded.file_path,"
                " file_sha256=excluded.file_sha256,"
                " from_date=excluded.from_date,"
                " to_date=excluded.to_date",
                (audit_id, website_id, str(file_path), file_sha256,
                 from_date, to_date, _now()))
            self._conn.commit()
            return self.audit_for(audit_id)

    def audit_for(self, audit_id) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM audits WHERE audit_id = ?",
                (audit_id,)).fetchone()
            return dict(row) if row else None

    def bind_run_audit(self, run_id, audit_id):
        with self._lock:
            self._conn.execute(
                "INSERT INTO run_audits(run_id, audit_id, bound_at)"
                " VALUES(?,?,?) ON CONFLICT(run_id, audit_id) DO NOTHING",
                (run_id, audit_id, _now()))
            self._conn.commit()

    def audit_for_run(self, run_id) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT a.* FROM audits a "
                "JOIN run_audits ra ON ra.audit_id = a.audit_id "
                "WHERE ra.run_id = ? ORDER BY ra.bound_at DESC LIMIT 1",
                (run_id,)).fetchone()
            return dict(row) if row else None

    def has_excel(self, website_id) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM audits WHERE website_id = ? LIMIT 1",
                (website_id,)).fetchone()
            return row is not None

    # ---------- browsers ----------

    def open_browser(self, website_id, browser_id) -> dict:
        with self._lock:
            self._conn.execute(
                "INSERT INTO browsers(browser_id, website_id, status, created_at)"
                " VALUES(?,?,?,?) ON CONFLICT(browser_id) DO UPDATE SET "
                " website_id=excluded.website_id, status='open', closed_at=NULL",
                (browser_id, website_id, "open", _now()))
            self._conn.commit()
            return self.browser_for(browser_id)

    def browser_for(self, browser_id) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM browsers WHERE browser_id = ?",
                (browser_id,)).fetchone()
            return dict(row) if row else None

    def current_browser(self, website_id) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM browsers WHERE website_id = ? AND status='open'"
                " ORDER BY created_at DESC LIMIT 1", (website_id,)).fetchone()
            return dict(row) if row else None

    def close_browser(self, browser_id):
        with self._lock:
            self._conn.execute(
                "UPDATE browsers SET status='closed', closed_at=? "
                "WHERE browser_id = ?", (_now(), browser_id))
            self._conn.commit()

    # ---------- workflow jobs (recovery toi thieu) ----------

    def upsert_job(self, job_id, *, command_id=None, request_hash=None,
                   command=None, website_id=None, browser_id=None,
                   run_id=None, audit_id=None, record_ids=None,
                   verified_record_ids=None, status="running",
                   waiting_on=None):
        with self._lock:
            self._conn.execute(
                "INSERT INTO workflow_jobs(job_id, command_id, request_hash,"
                " command, website_id, browser_id, run_id, audit_id,"
                " record_ids, verified_record_ids, status, waiting_on,"
                " updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)"
                " ON CONFLICT(job_id) DO UPDATE SET"
                " command_id=COALESCE(excluded.command_id, workflow_jobs.command_id),"
                " request_hash=COALESCE(excluded.request_hash, workflow_jobs.request_hash),"
                " command=COALESCE(excluded.command, workflow_jobs.command),"
                " website_id=COALESCE(excluded.website_id, workflow_jobs.website_id),"
                " browser_id=COALESCE(excluded.browser_id, workflow_jobs.browser_id),"
                " run_id=COALESCE(excluded.run_id, workflow_jobs.run_id),"
                " audit_id=COALESCE(excluded.audit_id, workflow_jobs.audit_id),"
                " record_ids=COALESCE(excluded.record_ids, workflow_jobs.record_ids),"
                " verified_record_ids=COALESCE(excluded.verified_record_ids,"
                "   workflow_jobs.verified_record_ids),"
                " status=excluded.status, waiting_on=excluded.waiting_on,"
                " updated_at=excluded.updated_at",
                (job_id, command_id, request_hash, command, website_id,
                 browser_id, run_id, audit_id,
                 json.dumps(record_ids) if record_ids is not None else None,
                 json.dumps(verified_record_ids)
                 if verified_record_ids is not None else None,
                 status, waiting_on, _now()))
            self._conn.commit()

    def job_for(self, job_id) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM workflow_jobs WHERE job_id = ?",
                (job_id,)).fetchone()
            return self._job_dict(row) if row else None

    @staticmethod
    def _job_dict(row) -> dict:
        d = dict(row)
        for key in ("record_ids", "verified_record_ids"):
            if d.get(key):
                try:
                    d[key] = json.loads(d[key])
                except ValueError:
                    d[key] = []
        return d

    def set_job_status(self, job_id, status, *, waiting_on=None):
        with self._lock:
            self._conn.execute(
                "UPDATE workflow_jobs SET status=?, waiting_on=?, updated_at=?"
                " WHERE job_id=?", (status, waiting_on, _now(), job_id))
            self._conn.commit()

    def active_job_ids(self, website_id) -> list:
        with self._lock:
            marks = ",".join("?" for _ in TERMINAL_STATUSES)
            rows = self._conn.execute(
                f"SELECT job_id FROM workflow_jobs WHERE website_id = ? "
                f"AND status NOT IN ({marks}) ORDER BY updated_at",
                (website_id, *TERMINAL_STATUSES)).fetchall()
            return [r["job_id"] for r in rows]

    # ---------- open tabs ----------

    def add_open_tabs(self, website_id, record_ids, *, run_id=None,
                      browser_id=None):
        with self._lock:
            for rid in record_ids:
                self._conn.execute(
                    "INSERT INTO open_tabs(website_id, run_id, browser_id,"
                    " record_id, opened_at) VALUES(?,?,?,?,?)"
                    " ON CONFLICT(website_id, record_id) DO UPDATE SET"
                    " run_id=excluded.run_id, browser_id=excluded.browser_id,"
                    " opened_at=excluded.opened_at",
                    (website_id, run_id, browser_id, int(rid), _now()))
            self._conn.commit()

    def remove_open_tabs(self, website_id, record_ids):
        with self._lock:
            self._conn.executemany(
                "DELETE FROM open_tabs WHERE website_id=? AND record_id=?",
                [(website_id, int(r)) for r in record_ids])
            self._conn.commit()

    def open_tab_record_ids(self, website_id) -> list:
        with self._lock:
            rows = self._conn.execute(
                "SELECT record_id FROM open_tabs WHERE website_id = ?"
                " ORDER BY record_id", (website_id,)).fetchall()
            return [int(r["record_id"]) for r in rows]

    def clear_open_tabs(self, website_id):
        with self._lock:
            self._conn.execute(
                "DELETE FROM open_tabs WHERE website_id=?", (website_id,))
            self._conn.commit()

    # ---------- needs reconcile ----------

    def add_needs_reconcile(self, website_id, record_ids, *, run_id=None,
                            reason=""):
        with self._lock:
            for rid in record_ids:
                self._conn.execute(
                    "INSERT INTO needs_reconcile(website_id, run_id,"
                    " record_id, reason, created_at) VALUES(?,?,?,?,?)"
                    " ON CONFLICT(website_id, record_id) DO UPDATE SET"
                    " run_id=excluded.run_id, reason=excluded.reason,"
                    " created_at=excluded.created_at",
                    (website_id, run_id, int(rid), reason, _now()))
            self._conn.commit()

    def needs_reconcile_ids(self, website_id, *, run_id=None) -> list:
        with self._lock:
            if run_id is None:
                rows = self._conn.execute(
                    "SELECT record_id FROM needs_reconcile WHERE website_id=?"
                    " ORDER BY record_id", (website_id,)).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT record_id FROM needs_reconcile WHERE website_id=?"
                    " AND run_id=? ORDER BY record_id",
                    (website_id, run_id)).fetchall()
            return [int(r["record_id"]) for r in rows]

    def clear_needs_reconcile(self, website_id, record_ids):
        with self._lock:
            self._conn.executemany(
                "DELETE FROM needs_reconcile WHERE website_id=? AND record_id=?",
                [(website_id, int(r)) for r in record_ids])
            self._conn.commit()

    # ---------- preferences ----------

    def get_preferences(self, website_id) -> dict:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM preferences WHERE website_id=?",
                (website_id,)).fetchone()
            if row is None:
                return {"website_id": website_id,
                        "chunk_size": DEFAULT_CHUNK_SIZE,
                        "cong_chung_vien": None,
                        "thu_ky": None}
            return {"website_id": website_id,
                    "chunk_size": int(row["chunk_size"]),
                    "cong_chung_vien": row["cong_chung_vien"],
                    "thu_ky": row["thu_ky"]}

    def save_preferences(self, website_id, values: dict):
        allowed = {"chunk_size", "cong_chung_vien", "thu_ky"}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"preferences key la: {sorted(unknown)}")
        with self._lock:
            cur = self.get_preferences(website_id)
            new = dict(cur)
            for key in allowed:
                if key in values:
                    new[key] = values[key]
            new["chunk_size"] = max(
                MIN_CHUNK_SIZE, min(int(new["chunk_size"]), MAX_CHUNK_SIZE))
            self._conn.execute(
                "INSERT INTO preferences(website_id, chunk_size,"
                " cong_chung_vien, thu_ky, updated_at) VALUES(?,?,?,?,?)"
                " ON CONFLICT(website_id) DO UPDATE SET"
                " chunk_size=excluded.chunk_size,"
                " cong_chung_vien=excluded.cong_chung_vien,"
                " thu_ky=excluded.thu_ky, updated_at=excluded.updated_at",
                (website_id, new["chunk_size"], new["cong_chung_vien"],
                 new["thu_ky"], _now()))
            self._conn.commit()
            return self.get_preferences(website_id)

    # ---------- snapshot contract §6.2 ----------

    def workspace_snapshot(self, website_id) -> dict:
        with self._lock:
            run = self.latest_run(website_id) if website_id else None
            audit = self.audit_for_run(run["run_id"]) if run else None
            browser = self.current_browser(website_id) if website_id else None
            return {
                "website_id": website_id,
                "revision": self.revision(),
                "run_id": run["run_id"] if run else None,
                "audit_id": audit["audit_id"] if audit else None,
                "browser_id": browser["browser_id"] if browser else None,
                "active_job_ids": self.active_job_ids(website_id)
                if website_id else [],
                "needs_reconcile_record_ids":
                    self.needs_reconcile_ids(website_id)
                    if website_id else [],
                "has_excel": bool(audit) or (
                    self.has_excel(website_id) if website_id else False),
                "queue_revision": (int(run["queue_revision"])
                                   if run else None),
            }

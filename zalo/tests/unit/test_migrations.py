"""Slice B tests — migrations + engine wiring (decision-sheet §4/§8).

Covered:
(a) fresh temp sqlite db -> run_migrations applies 1 migration and creates
    all 9 tables + idx_jobs_claim index;
(b) second run_migrations applies 0 (idempotent);
(c) SCHEMA_VERSION == 1 and schema_migrations holds a version=1 row;
(d) get_engine(settings) records an access-log entry kind="db" via
    zalo_module.audit (slice A dependency — skipped if not landed yet).
"""
from __future__ import annotations

import dataclasses
import json
from datetime import datetime
from pathlib import Path

import pytest
import sqlalchemy as sa

from zalo_module.database import (
    SCHEMA_VERSION,
    get_engine,
    init_db,
    run_migrations,
    session_scope,
)
from zalo_module.migrations import MIGRATIONS

try:  # slice A owns settings.py; fall back to the sheet §2 signature meanwhile
    from zalo_module.settings import Settings, get_settings
except ImportError:  # pragma: no cover - only while slice A has not landed
    get_settings = None

    @dataclasses.dataclass(frozen=True)
    class Settings:  # noqa: D101 - stub per decision-sheet §2
        runtime_root: Path
        db_url: str
        consumer_id: str | None = None
        bind: str = "127.0.0.1"
        port: int = 8790
        qwen_api_base: str = "https://dashscope-intl.aliyuncs.com"
        qwen_model: str = "qwen-vl-ocr-2025-11-20"
        qwen_api_key: str | None = None
        account_id: str | None = None
        ocr_config_version: str = "ocr-config-v1"
        access_log_path: Path = Path("runtime/access.jsonl")


def _make_settings(runtime_root: Path, db_url: str) -> Settings:
    if get_settings is not None:
        return get_settings(
            {
                "ZALO_INTAKE_RUNTIME_DIR": str(runtime_root),
                "ZALO_INTAKE_DB_URL": db_url,
            }
        )
    return Settings(runtime_root=runtime_root, db_url=db_url)


EXPECTED_TABLES = {
    "schema_migrations",
    "journal_entries",
    "sources",
    "records",
    "media_assets",
    "jobs",
    "ocr_requests",
    "packages",
    "listener_sessions",
}


def _tmp_url(tmp_path: Path, name: str = "t.db") -> str:
    return f"sqlite:///{(tmp_path / name).as_posix()}"


def _reset_audit(audit, monkeypatch) -> None:
    if hasattr(audit, "reset_for_tests"):
        audit.reset_for_tests()
    else:  # sanctioned by slice-B brief: poke the module-level state directly
        monkeypatch.setattr(audit, "_access_log", None)


# --- (a) fresh migrate creates everything -----------------------------------


def test_run_migrations_fresh_creates_all_objects(tmp_path):
    engine = sa.create_engine(_tmp_url(tmp_path))
    assert run_migrations(engine) == 3  # m0001+m0002+m0003 (packaged_in marker)

    inspector = sa.inspect(engine)
    assert EXPECTED_TABLES <= set(inspector.get_table_names())

    index_names = {ix["name"] for ix in inspector.get_indexes("jobs")}
    assert "idx_jobs_claim" in index_names

    uniques = {
        tuple(u["column_names"])
        for t in EXPECTED_TABLES - {"schema_migrations"}
        for u in inspector.get_unique_constraints(t)
    }
    assert ("logical_id", "revision") in uniques  # records
    assert ("consumer_id", "sequence") in uniques  # packages
    assert ("source_key",) in uniques  # journal_entries


# --- (b) idempotent ----------------------------------------------------------


def test_run_migrations_idempotent(tmp_path):
    engine = sa.create_engine(_tmp_url(tmp_path))
    assert run_migrations(engine) == 3
    assert run_migrations(engine) == 0
    init_db(engine)  # must not explode / double-apply
    assert run_migrations(engine) == 0


# --- (c) version marker ------------------------------------------------------


def test_schema_version_and_marker_row(tmp_path):
    assert SCHEMA_VERSION == 3
    assert [m.version for m in MIGRATIONS] == sorted(
        m.version for m in MIGRATIONS
    )
    assert {1, 2, 3} <= {m.version for m in MIGRATIONS}

    engine = sa.create_engine(_tmp_url(tmp_path))
    run_migrations(engine)
    with engine.connect() as conn:
        rows = conn.execute(
            sa.text("SELECT version, applied_at FROM schema_migrations")
        ).all()
    assert [r[0] for r in rows] == [1, 2, 3]
    for row in rows:
        datetime.fromisoformat(row[1])  # ISO-8601 per DDL


# --- (e) m0003 is idempotent on a partially-patched schema --------------------


def test_m0003_column_present_but_version_absent(tmp_path):
    """M5: a db that already gained ``records.packaged_in`` (manual patch /
    crash mid-migration) but has no version-3 row must still migrate — the
    ALTER is guarded by PRAGMA table_info, not only by the version gate."""
    from zalo_module.migrations import m0003_record_packaged as m0003

    engine = sa.create_engine(_tmp_url(tmp_path))
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "CREATE TABLE records (record_id TEXT PRIMARY KEY)"
            )
        )
        conn.execute(
            sa.text(
                "CREATE TABLE schema_migrations"
                " (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
        )
        # Simulate a partially-patched db: column exists, marker row does not.
        conn.execute(
            sa.text("ALTER TABLE records ADD COLUMN packaged_in TEXT")
        )
        conn.execute(
            sa.text("INSERT INTO schema_migrations (version, applied_at)"
                    " VALUES (1, '2026-09-25T00:00:00+00:00')")
        )

    m0003.upgrade(engine)

    with engine.connect() as conn:
        cols = [r[1] for r in conn.execute(
            sa.text("PRAGMA table_info(records)")
        ).all()]
        assert cols.count("packaged_in") == 1  # no duplicate column
        versions = [r[0] for r in conn.execute(
            sa.text("SELECT version FROM schema_migrations ORDER BY version")
        ).all()]
        assert versions == [1, 3]
        index_names = {
            ix["name"] for ix in sa.inspect(conn).get_indexes("records")
        }
        assert "ix_records_packaged_in" in index_names


# --- (d) audit hook in get_engine -------------------------------------------


def test_get_engine_records_db_access(tmp_path, monkeypatch):
    audit = pytest.importorskip("zalo_module.audit")  # slice A lands in parallel
    _reset_audit(audit, monkeypatch)

    log_path = tmp_path / "access.jsonl"
    audit.configure(log_path)

    db_file = tmp_path / "rec.db"
    settings = _make_settings(
        runtime_root=tmp_path / "rt",
        db_url=f"sqlite:///{db_file.as_posix()}",
    )
    engine = get_engine(settings)
    assert engine.dialect.name == "sqlite"

    entries = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(
        e["kind"] == "db" and Path(e["path"]).resolve() == db_file.resolve()
        for e in entries
    ), entries


def test_get_engine_skips_access_log_for_memory_db(tmp_path, monkeypatch):
    audit = pytest.importorskip("zalo_module.audit")
    _reset_audit(audit, monkeypatch)
    calls: list[tuple[Path, str]] = []
    monkeypatch.setattr(
        audit, "record_access", lambda p, k: calls.append((p, k))
    )
    settings = _make_settings(
        runtime_root=tmp_path / "rt", db_url="sqlite:///:memory:"
    )
    get_engine(settings)
    assert calls == []


# --- session_scope smoke -----------------------------------------------------


def test_session_scope_commit_and_rollback(tmp_path):
    from zalo_module.models import JournalEntry

    engine = sa.create_engine(_tmp_url(tmp_path))
    run_migrations(engine)

    with session_scope(engine) as s:
        s.add(
            JournalEntry(
                capture_id="c-1",
                source_key="k-1",
                event_json="{}",
                captured_at="2026-09-25T00:00:00+00:00",
                recorded_at="2026-09-25T00:00:00+00:00",
            )
        )
    with session_scope(engine) as s:
        assert s.get(JournalEntry, "c-1") is not None

    with pytest.raises(sa.exc.IntegrityError):
        with session_scope(engine) as s:
            s.add(
                JournalEntry(
                    capture_id="c-2",
                    source_key="k-1",  # violates UNIQUE(source_key)
                    event_json="{}",
                    captured_at="x",
                    recorded_at="x",
                )
            )
    with session_scope(engine) as s:
        assert s.get(JournalEntry, "c-2") is None

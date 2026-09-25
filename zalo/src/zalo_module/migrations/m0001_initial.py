"""m0001 — initial schema, DDL per decision-sheet §4 (verbatim).

All 9 CREATE TABLE statements + idx_jobs_claim + schema_migrations itself.
``IF NOT EXISTS`` is used for safety, but ``schema_migrations`` rows remain
the authoritative record of what was applied.
"""
from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa

version = 1

_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
      version INTEGER PRIMARY KEY,
      applied_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS journal_entries (
      capture_id TEXT PRIMARY KEY,
      source_key TEXT NOT NULL UNIQUE,
      event_json TEXT NOT NULL,
      captured_at TEXT NOT NULL,
      recorded_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sources (
      logical_id TEXT PRIMARY KEY,
      scope TEXT NOT NULL,
      account_id TEXT,
      conversation_id TEXT,
      provider_message_id TEXT,
      attachment_id TEXT,
      page_index INTEGER,
      captured_at TEXT NOT NULL,
      current_revision INTEGER NOT NULL DEFAULT 1,
      image_available INTEGER NOT NULL DEFAULT 0,
      enabled INTEGER NOT NULL DEFAULT 1,
      image_expires_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS records (
      record_id TEXT PRIMARY KEY,
      logical_id TEXT NOT NULL,
      revision INTEGER NOT NULL,
      kind TEXT NOT NULL,
      canonical_sha256 TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      captured_at TEXT NOT NULL,
      recorded_at TEXT NOT NULL,
      UNIQUE(logical_id, revision)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS media_assets (
      attachment_id TEXT PRIMARY KEY,
      sha256 TEXT NOT NULL,
      rel_path TEXT NOT NULL,
      state TEXT NOT NULL,
      captured_at TEXT NOT NULL,
      expires_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS jobs (
      job_id TEXT PRIMARY KEY,
      kind TEXT NOT NULL,
      state TEXT NOT NULL,
      logical_id TEXT,
      request_id TEXT,
      payload_json TEXT NOT NULL,
      attempts INTEGER NOT NULL DEFAULT 0,
      max_attempts INTEGER NOT NULL DEFAULT 3,
      lease_owner TEXT,
      lease_expires_at TEXT,
      run_after TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      result_json TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_claim ON jobs(state, run_after)
    """,
    """
    CREATE TABLE IF NOT EXISTS ocr_requests (
      request_id TEXT PRIMARY KEY,
      consumer_id TEXT NOT NULL,
      logical_id TEXT NOT NULL,
      variant TEXT NOT NULL,
      preset TEXT,
      reason_code TEXT NOT NULL,
      observed_revision INTEGER NOT NULL,
      submitted_at TEXT NOT NULL,
      body_canonical_sha256 TEXT NOT NULL,
      job_id TEXT,
      state TEXT NOT NULL,
      deduped_from TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS packages (
      package_id TEXT PRIMARY KEY,
      consumer_id TEXT NOT NULL,
      sequence INTEGER NOT NULL,
      manifest_sha256 TEXT NOT NULL,
      record_count INTEGER NOT NULL,
      dir_rel_path TEXT NOT NULL,
      created_at TEXT NOT NULL,
      sealed_at TEXT,
      status TEXT NOT NULL DEFAULT 'pending',
      receipt_json TEXT,
      UNIQUE(consumer_id, sequence)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS listener_sessions (
      session_id TEXT PRIMARY KEY,
      account_id TEXT,
      state TEXT NOT NULL,
      observed_at TEXT NOT NULL,
      last_heartbeat_at TEXT,
      reason TEXT
    )
    """,
)


def upgrade(engine_or_conn) -> None:
    """Apply the DDL and record version 1; accepts an Engine or Connection."""
    if hasattr(engine_or_conn, "execute"):
        _apply(engine_or_conn)
    else:
        with engine_or_conn.begin() as conn:
            _apply(conn)


def _apply(conn: sa.engine.Connection) -> None:
    for statement in _STATEMENTS:
        conn.execute(sa.text(statement))
    conn.execute(
        sa.text(
            "INSERT INTO schema_migrations (version, applied_at)"
            " VALUES (:version, :applied_at)"
        ),
        {
            "version": version,
            "applied_at": datetime.now(timezone.utc).isoformat(),
        },
    )

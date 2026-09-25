"""m0002 — engine tables for the ported Zalo listener engine (MIN-103 B).

Decision sheet §3: mirror the legacy ``zalo_connector_accounts`` /
``zalo_sources`` / ``zalo_data_sync_runs`` columns under module-internal
table names (``connector_accounts`` / ``conv_sources`` / ``data_sync_runs``).
All timestamps are TEXT ISO-8601; booleans are INTEGER. ``data_sync_runs``
keeps the "at most one running run per account" rule as a partial unique
index (``WHERE status = 'running'``).
"""
from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa

version = 2

_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS connector_accounts (
      connector_account_id TEXT PRIMARY KEY,
      bound_zalo_id TEXT,
      session_state TEXT NOT NULL DEFAULT 'login_required',
      listener_generation INTEGER NOT NULL DEFAULT 0,
      last_seen_at TEXT,
      qr_image TEXT,
      qr_expires_at TEXT,
      storage_full INTEGER NOT NULL DEFAULT 0,
      intake_consented_at TEXT,
      policy_version INTEGER NOT NULL DEFAULT 0,
      policy_acked_version INTEGER NOT NULL DEFAULT 0,
      source_sync_request_version INTEGER NOT NULL DEFAULT 0,
      source_sync_acked_version INTEGER NOT NULL DEFAULT 0,
      gap_started_at TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS conv_sources (
      conv_source_id TEXT PRIMARY KEY,
      connector_account_id TEXT NOT NULL,
      conversation_id TEXT NOT NULL,
      conversation_type TEXT NOT NULL,
      source_type TEXT,
      display_name TEXT NOT NULL,
      enabled INTEGER NOT NULL DEFAULT 0,
      enabled_explicit INTEGER,
      acked_enabled INTEGER,
      policy_version INTEGER NOT NULL DEFAULT 0,
      policy_acked_version INTEGER NOT NULL DEFAULT 0,
      last_activity_at TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      UNIQUE(connector_account_id, conversation_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS data_sync_runs (
      run_id TEXT PRIMARY KEY,
      connector_account_id TEXT NOT NULL,
      status TEXT NOT NULL,
      cutoff_at TEXT NOT NULL,
      deadline_at TEXT NOT NULL,
      source_ids_json TEXT NOT NULL DEFAULT '[]',
      counters_json TEXT NOT NULL DEFAULT '{}',
      error_code TEXT,
      started_at TEXT NOT NULL,
      completed_at TEXT
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_data_sync_runs_running_account
      ON data_sync_runs(connector_account_id) WHERE status = 'running'
    """,
)


def upgrade(engine_or_conn) -> None:
    """Apply the DDL and record version 2; accepts an Engine or Connection."""
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

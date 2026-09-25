"""m0003 — ``records.packaged_in`` marks which package a record was emitted in.

Decision sheet MIN-94/95/97: package builds must be crash-safe and
monotonic. A durable per-record marker (``packaged_in = packages.package_id``)
is the cheapest way to compute "records not yet packaged" without parsing
manifests, and keeps package rebuilds idempotent.

The ``ALTER TABLE`` is guarded by ``PRAGMA table_info(records)`` so a
partially-patched database (column present, version row absent) can still be
brought to version 3 — SQLite has no ``ADD COLUMN IF NOT EXISTS``.
"""
from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa

version = 3


def upgrade(engine_or_conn) -> None:
    """Apply the DDL and record version 3; accepts an Engine or Connection."""
    if hasattr(engine_or_conn, "execute"):
        _apply(engine_or_conn)
    else:
        with engine_or_conn.begin() as conn:
            _apply(conn)


def _apply(conn: sa.engine.Connection) -> None:
    columns = {
        row[1]
        for row in conn.execute(sa.text("PRAGMA table_info(records)")).all()
    }
    if "packaged_in" not in columns:
        conn.execute(
            sa.text("ALTER TABLE records ADD COLUMN packaged_in TEXT")
        )
    conn.execute(
        sa.text(
            """
            CREATE INDEX IF NOT EXISTS ix_records_packaged_in
              ON records(packaged_in)
            """
        )
    )
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

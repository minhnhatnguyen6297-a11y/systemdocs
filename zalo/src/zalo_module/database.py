"""Engine / session / migration runner — API per decision-sheet §4.

``SCHEMA_VERSION`` is the highest known migration version. ``run_migrations``
applies pending entries from ``zalo_module.migrations.MIGRATIONS`` in version
order and is idempotent — ``schema_migrations`` rows are the authority.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import sqlalchemy as sa
from sqlalchemy.orm import Session

SCHEMA_VERSION = 3


def _sqlite_db_path(db_url: str) -> Path | None:
    """Return the on-disk file for a sqlite URL, else ``None``.

    Handles ``sqlite:///...`` (and ``sqlite+<drv>:///...``); ``:memory:`` and
    non-sqlite URLs return ``None``.
    """
    url = sa.engine.make_url(db_url)
    if not url.drivername.startswith("sqlite"):
        return None
    database = url.database
    if not database or database == ":memory:":
        return None
    return Path(database)


def get_engine(settings) -> sa.engine.Engine:
    """Create an engine for ``settings.db_url`` and audit the DB file access."""
    engine = sa.create_engine(settings.db_url)
    db_path = _sqlite_db_path(settings.db_url)
    if db_path is not None:
        # Lazy import: audit.py is owned by slice A and may land after this
        # module is first imported. Resolved at call time on purpose.
        from zalo_module import audit

        audit.record_access(db_path, "db")
    return engine


def init_db(engine) -> None:
    """Create/upgrade the schema to the latest known version."""
    run_migrations(engine)


def _applied_versions(conn: sa.engine.Connection) -> set[int]:
    if not sa.inspect(conn).has_table("schema_migrations"):
        return set()
    rows = conn.execute(
        sa.text("SELECT version FROM schema_migrations")
    ).fetchall()
    return {row[0] for row in rows}


def run_migrations(engine) -> int:
    """Apply unapplied migrations in version order; return count applied.

    Each migration runs inside its own transaction and records its version in
    ``schema_migrations``; safe to call repeatedly (idempotent).
    """
    from zalo_module.migrations import MIGRATIONS

    with engine.begin() as conn:
        applied_versions = _applied_versions(conn)

    count = 0
    for migration in MIGRATIONS:  # registry is sorted by version
        if migration.version in applied_versions:
            continue
        with engine.begin() as conn:
            migration.upgrade(conn)
        applied_versions.add(migration.version)
        count += 1
    return count


@contextmanager
def session_scope(engine) -> Iterator[Session]:
    """Yield a ``Session``; commit on success, rollback on error, always close."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

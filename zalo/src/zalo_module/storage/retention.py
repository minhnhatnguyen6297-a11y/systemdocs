"""Media retention: ``captured_at`` + retention hours, then expire.

The retention window comes from ``settings.connector_retention_hours``
(``ZALO_CONNECTOR_RETENTION_HOURS``, default 168 — the contract's 7-day
media lifetime). Expiry deletes the original file at
``runtime_root/rel_path`` plus any derived variants under
``runtime_root/media/derived/`` named after the ``attachment_id`` —
``derived/<attachment_id>/...`` or ``derived/<attachment_id>-*`` /
``<attachment_id>_*`` / ``<attachment_id>.*``. Records and packages are
never touched: the ``media_assets`` row stays with ``state='expired'``.
"""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select

from zalo_module.audit import record_access
from zalo_module.models import MediaAsset

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from zalo_module.settings import Settings

IMAGE_TTL_HOURS = 168


def image_expires_at(
    captured_at: datetime, hours: float | None = None
) -> datetime:
    """Exactly ``captured_at`` + retention ``hours`` (default 168h TTL).

    ``hours`` is the configured media lifetime — callers holding a
    ``Settings`` pass ``settings.connector_retention_hours``
    (``ZALO_CONNECTOR_RETENTION_HOURS``) so the stored expiry matches the
    ``expire_media`` sweep. Anything missing or non-positive falls back to
    the contract default ``IMAGE_TTL_HOURS``.
    """
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    if not isinstance(hours, (int, float)) or hours <= 0:
        hours = IMAGE_TTL_HOURS
    return captured_at + timedelta(hours=float(hours))


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _retention_hours(settings: "Settings") -> float:
    hours = getattr(settings, "connector_retention_hours", None)
    if not isinstance(hours, (int, float)) or hours <= 0:
        return float(IMAGE_TTL_HOURS)
    return float(hours)


def _env_retention_hours() -> float:
    """``ZALO_CONNECTOR_RETENTION_HOURS`` parsed leniently (default 168).

    Fallback for callers that cannot supply a ``Settings`` object — the env
    var is the same source ``settings.connector_retention_hours`` reads, so
    rows registered this way stay consistent with the ``expire_media``
    sweep. Missing/invalid values fall back to the contract default rather
    than raising (settings.py owns the strict parse at startup).
    """
    raw = os.environ.get("ZALO_CONNECTOR_RETENTION_HOURS")
    if raw is None:
        return float(IMAGE_TTL_HOURS)
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError):
        return float(IMAGE_TTL_HOURS)
    if not (value > 0):
        return float(IMAGE_TTL_HOURS)
    return value


def _derived_paths(derived_root: Path, attachment_id: str) -> list[Path]:
    """Files/dirs under ``media/derived`` belonging to ``attachment_id``.

    Convention (MIN-95+): derived variants are written as
    ``derived/<attachment_id>/<file>`` or ``derived/<attachment_id>-*.`` /
    ``_*`` / ``.*`` siblings. Anything else is left alone.
    """
    if not derived_root.is_dir():
        return []
    matches: list[Path] = []
    for path in derived_root.rglob("*"):
        rel = path.relative_to(derived_root)
        if rel.parts and rel.parts[0] == attachment_id:
            matches.append(path)
            continue
        name = path.name
        if name.startswith(
            f"{attachment_id}-"
        ) or name.startswith(f"{attachment_id}_") or name.startswith(
            f"{attachment_id}."
        ):
            matches.append(path)
    return matches


def _unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _prune_empty_dirs(leaf: Path, stop: Path) -> None:
    """Remove empty parent dirs of ``leaf`` up to (excluding) ``stop``."""
    directory = leaf.parent
    while directory != stop and stop in directory.parents:
        try:
            directory.rmdir()
        except OSError:
            break
        directory = directory.parent


def expire_media(now: datetime, session: "Session", settings: "Settings") -> int:
    """Expire due ``media_assets`` rows and delete their files.

    A row is due when ``captured_at + connector_retention_hours`` has passed
    (stored ``expires_at`` is the same value for rows written by
    ``register_media`` and serves as fallback when ``captured_at`` cannot be
    parsed). Expiry is unconditional — package ACK does not extend it.
    The original file at ``runtime_root/rel_path`` and derived variants
    under ``media/derived/`` are removed; records, sources and packages
    survive. ``state='missing'`` rows age out the same way. Returns the
    number of rows expired.
    """
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    retention = _retention_hours(settings)
    rows = (
        session.execute(select(MediaAsset).where(MediaAsset.state != "expired"))
        .scalars()
        .all()
    )
    runtime_root = Path(settings.runtime_root).resolve()
    media_root = (runtime_root / "media").resolve()
    derived_root = media_root / "derived"
    expired = 0
    for row in rows:
        captured = _parse_iso(row.captured_at)
        if captured is not None:
            due = captured + timedelta(hours=retention)
        else:
            due = _parse_iso(row.expires_at)
        if due is None or due > now:
            continue
        path = Path(settings.runtime_root) / row.rel_path
        try:
            resolved = path.resolve()
            # Containment: never unlink outside runtime_root.
            if resolved != runtime_root and resolved.is_relative_to(runtime_root):
                _unlink(resolved)
                _prune_empty_dirs(resolved, media_root)
        except OSError:
            pass  # scaffold: state flips even if the file cannot be removed
        for derived in _derived_paths(derived_root, row.attachment_id):
            if derived.is_dir():
                shutil.rmtree(derived, ignore_errors=True)
            else:
                _unlink(derived)
            _prune_empty_dirs(derived, derived_root)
        record_access(path, "media")
        row.state = "expired"
        expired += 1
    return expired

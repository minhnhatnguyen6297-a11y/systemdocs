"""Media asset path + registration helpers.

Path/registration only - this module never reads or writes file content.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from zalo_module.audit import record_access
from zalo_module.models import MediaAsset
from zalo_module.storage.retention import (
    _env_retention_hours,
    _retention_hours,
    image_expires_at,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from zalo_module.settings import Settings


def media_path(attachment_id: str, ext: str, settings: "Settings") -> Path:
    """Return ``runtime_root/media/{attachment_id}.{ext}`` (dir ensured)."""
    path = (
        Path(settings.runtime_root)
        / "media"
        / f"{attachment_id}.{ext.lstrip('.')}"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    record_access(path, "media")
    return path


def register_media(
    attachment_id: str,
    sha256: str,
    rel_path: str,
    captured_at,
    session: "Session",
    *,
    state: str = "captured",
    settings: "Settings | None" = None,
) -> None:
    """Insert a ``media_assets`` row; ``expires_at`` = captured_at + retention.

    ``rel_path`` is the path relative to ``runtime_root`` (e.g.
    ``media/<id>.jpg``). ``captured_at`` accepts tz-aware datetime or ISO str.
    ``state`` is the contract media_state — ``'captured'`` for real bytes,
    ``'missing'`` for a failed-attachment placeholder (no bytes observed,
    ``sha256`` empty).

    When ``settings`` is given, ``expires_at`` uses
    ``settings.connector_retention_hours`` (``ZALO_CONNECTOR_RETENTION_HOURS``)
    — the same window ``expire_media`` enforces. Without ``settings`` the
    env var itself is read (``_env_retention_hours``) so configured
    retention still applies; the contract default is 168h.
    """
    if isinstance(captured_at, str):
        captured_dt = datetime.fromisoformat(captured_at)
    else:
        captured_dt = captured_at
    if captured_dt.tzinfo is None:
        captured_dt = captured_dt.replace(tzinfo=timezone.utc)
    session.add(
        MediaAsset(
            attachment_id=attachment_id,
            sha256=sha256,
            rel_path=str(rel_path),
            state=state,
            captured_at=captured_dt.isoformat(),
            expires_at=image_expires_at(
                captured_dt,
                (
                    _retention_hours(settings)
                    if settings is not None
                    else _env_retention_hours()
                ),
            ).isoformat(),
        )
    )

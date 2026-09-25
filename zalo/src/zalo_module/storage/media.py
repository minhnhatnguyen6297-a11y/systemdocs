"""Media asset path + registration helpers.

Path/registration only - this module never reads or writes file content.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from zalo_module.audit import record_access
from zalo_module.models import MediaAsset
from zalo_module.storage.retention import image_expires_at

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
) -> None:
    """Insert a ``media_assets`` row; ``expires_at`` = captured_at + 168h.

    ``rel_path`` is the path relative to ``runtime_root`` (e.g.
    ``media/<id>.jpg``). ``captured_at`` accepts tz-aware datetime or ISO str.
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
            state="captured",
            captured_at=captured_dt.isoformat(),
            expires_at=image_expires_at(captured_dt).isoformat(),
        )
    )

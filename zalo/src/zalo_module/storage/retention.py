"""Image retention: fixed 168h TTL from capture, then expire."""
from __future__ import annotations

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


def image_expires_at(captured_at: datetime) -> datetime:
    """Exactly ``captured_at`` + 168h."""
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    return captured_at + timedelta(hours=IMAGE_TTL_HOURS)


def expire_media(now: datetime, session: "Session", settings: "Settings") -> int:
    """Expire due ``media_assets`` rows and delete their files.

    Every row with ``state != 'expired'`` and ``expires_at <= now`` gets its
    file at ``runtime_root/rel_path`` deleted (missing files ignored) and its
    state set to ``'expired'``. Returns the number of rows expired.
    """
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    rows = (
        session.execute(select(MediaAsset).where(MediaAsset.state != "expired"))
        .scalars()
        .all()
    )
    expired = 0
    for row in rows:
        try:
            expires_at = datetime.fromisoformat(row.expires_at)
        except (TypeError, ValueError):
            continue
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at > now:
            continue
        path = Path(settings.runtime_root) / row.rel_path
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass  # scaffold: state flips even if the file cannot be removed
        record_access(path, "media")
        row.state = "expired"
        expired += 1
    return expired

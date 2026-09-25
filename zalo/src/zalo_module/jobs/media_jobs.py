"""MIN-94 media jobs — retention sweep.

Two entry points consumed by ``jobs/handlers.py``:

- ``register(handlers)`` registers the ``retention_sweep`` job kind so an
  operator can force expiry by enqueueing a ``retention_sweep`` job
  (``jobs.payload_json`` is ignored — the sweep always scans all due rows).
- ``register_sweepers(sweepers)`` registers the periodic sweeper that runs
  at the top of every worker ``run_once`` pass.

Expiry semantics live in ``zalo_module.storage.retention.expire_media``:
``captured_at + ZALO_CONNECTOR_RETENTION_HOURS`` (168h default), deletes
the original file plus derived variants under ``media/derived/``, and
flips ``media_assets.state`` to ``'expired'`` — regardless of package ACK.
Records and packages are never deleted.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from zalo_module.storage.retention import expire_media

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from zalo_module.models import Job
    from zalo_module.settings import Settings

logger = logging.getLogger(__name__)


def expire_media_sweep(session: "Session", settings: "Settings") -> None:
    """Periodic sweeper (``fn(session, settings)``) for worker passes."""
    expired = expire_media(datetime.now(timezone.utc), session, settings)
    if expired:
        logger.info("retention sweep expired %d media assets", expired)


def retention_sweep(
    session: "Session", job: "Job", settings: "Settings"
) -> dict:
    """``retention_sweep`` job handler — force one expiry pass now."""
    expired = expire_media(datetime.now(timezone.utc), session, settings)
    return {"expired": expired}


def register(handlers: dict) -> None:
    handlers["retention_sweep"] = retention_sweep


def register_sweepers(sweepers: list) -> None:
    sweepers.append(expire_media_sweep)

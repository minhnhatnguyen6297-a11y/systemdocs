"""Job queue primitives: enqueue, lease-claim and lease reclaim.

Scaffold provides the primitives only - there is no real worker loop here.
Leases are 300s; a running job whose ``lease_expires_at`` passed goes back to
``retry_wait`` (or ``failed`` once ``attempts >= max_attempts``).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy import select, update

from zalo_module.models import Job

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

JOB_STATES = {"queued", "running", "retry_wait", "succeeded", "failed", "expired"}

LEASE_SECONDS = 300


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def enqueue_job(
    kind: str,
    payload: dict,
    session: "Session",
    *,
    logical_id: str | None = None,
    request_id: str | None = None,
    run_after=None,
    max_attempts: int = 3,
) -> str:
    """Insert a ``queued`` job row; returns ``job_id`` (uuid4 str).

    ``run_after`` accepts a datetime or an ISO 8601 string (or None).
    """
    job_id = str(uuid.uuid4())
    now_iso = _iso(datetime.now(timezone.utc))
    if isinstance(run_after, datetime):
        run_after = _iso(run_after)
    session.add(
        Job(
            job_id=job_id,
            kind=kind,
            state="queued",
            logical_id=logical_id,
            request_id=request_id,
            payload_json=json.dumps(
                payload, ensure_ascii=False, sort_keys=True
            ),
            attempts=0,
            max_attempts=max_attempts,
            run_after=run_after,
            created_at=now_iso,
            updated_at=now_iso,
        )
    )
    return job_id


def claim_jobs(
    now: datetime, worker_id: str, session: "Session", limit: int = 2
) -> list[Job]:
    """Move claimable jobs to ``running`` under a 300s lease.

    Claimable = state in {queued, retry_wait} and (run_after NULL or
    run_after <= now), selected oldest-first (idx_jobs_claim order). Each
    candidate is claimed with an **atomic state-CAS UPDATE** — only the
    transaction that actually flips ``state`` wins the lease; a candidate
    already taken by a racing worker is skipped (rowcount 0), never
    double-claimed.
    """
    now_iso = _iso(now)
    rows = (
        session.execute(
            select(Job)
            .where(Job.state.in_(("queued", "retry_wait")))
            .where((Job.run_after.is_(None)) | (Job.run_after <= now_iso))
            .order_by(Job.created_at, Job.job_id)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    lease_expires_at = _iso(now + timedelta(seconds=LEASE_SECONDS))
    claimed: list[Job] = []
    for job in rows:
        result = session.execute(
            update(Job)
            .where(Job.job_id == job.job_id)
            .where(Job.state.in_(("queued", "retry_wait")))
            .values(
                state="running",
                lease_owner=worker_id,
                lease_expires_at=lease_expires_at,
                attempts=Job.attempts + 1,
                updated_at=now_iso,
            )
            .execution_options(synchronize_session="fetch")
        )
        if result.rowcount == 1:
            claimed.append(job)
        # rowcount == 0 → another worker claimed it first; skip.
    return claimed


def reclaim_expired_leases(now: datetime, session: "Session") -> int:
    """Requeue ``running`` jobs whose lease expired.

    state -> 'retry_wait', lease_owner -> NULL, attempts unchanged;
    jobs with attempts >= max_attempts -> 'failed'. Returns rows reclaimed.
    """
    now_iso = _iso(now)
    rows = (
        session.execute(
            select(Job).where(
                Job.state == "running",
                Job.lease_expires_at.isnot(None),
                Job.lease_expires_at < now_iso,
            )
        )
        .scalars()
        .all()
    )
    for job in rows:
        job.lease_owner = None
        job.lease_expires_at = None
        job.state = (
            "failed" if (job.attempts or 0) >= job.max_attempts else "retry_wait"
        )
        job.updated_at = now_iso
    return len(rows)


# --- Worker runner (MIN-103 §worker-contract) -------------------------------
#
# A job handler is ``fn(session, job, settings) -> dict | None``:
# - returns a dict  -> job 'succeeded', dict stored in result_json
# - raises JobExpired -> job 'expired' (e.g. media past image_expires_at)
# - raises anything else -> 'retry_wait' with backoff run_after, or 'failed'
#   once attempts >= max_attempts
#
# Handler kinds are registered in ``jobs/handlers.py`` (media/ocr/package).

import logging
import socket
import time

logger = logging.getLogger(__name__)

JOB_BACKOFF_BASE_SECONDS = 30


class JobExpired(Exception):
    """Raised by a handler when the job's subject no longer exists/valid."""


def _backoff_seconds(attempts: int) -> int:
    # 30s, 60s, 120s, ... capped at 10 minutes.
    return min(600, JOB_BACKOFF_BASE_SECONDS * (2 ** max(0, attempts - 1)))


def run_once(
    engine,
    settings,
    handlers: dict,
    sweepers: list | None = None,
    *,
    worker_id: str | None = None,
    limit: int = 2,
    now: datetime | None = None,
) -> int:
    """Run registered sweeps, then claim+run up to ``limit`` jobs."""
    from zalo_module.database import session_scope

    now = now or datetime.now(timezone.utc)
    worker_id = worker_id or f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"

    with session_scope(engine) as session:
        reclaim_expired_leases(now, session)
        for sweep in sweepers or ():
            try:
                sweep(session, settings)
            except Exception:  # noqa: BLE001 - a bad sweep must not starve jobs
                logger.exception("sweep %s failed", getattr(sweep, "__name__", sweep))
        claimed = claim_jobs(now, worker_id, session, limit)
        payloads = [
            (j.job_id, j.kind, json.loads(j.payload_json or "{}")) for j in claimed
        ]

    for job_id, kind, _payload in payloads:
        handler = handlers.get(kind)
        with session_scope(engine) as session:
            job = session.get(Job, job_id)
            if job is None:
                continue
            try:
                if handler is None:
                    raise RuntimeError(f"no handler registered for {kind}")
                result = handler(session, job, settings)
                job.state = "succeeded"
                job.result_json = json.dumps(
                    result or {}, ensure_ascii=False, sort_keys=True
                )
            except JobExpired as exc:
                job.state = "expired"
                job.result_json = json.dumps(
                    {"error": str(exc)}, ensure_ascii=False
                )
            except Exception as exc:  # noqa: BLE001 - job isolation boundary
                logger.exception("job %s (%s) failed", job_id, kind)
                exhausted = (job.attempts or 0) >= (job.max_attempts or 3)
                job.state = "failed" if exhausted else "retry_wait"
                job.run_after = _iso(
                    now + timedelta(seconds=_backoff_seconds(job.attempts or 1))
                )
                job.result_json = json.dumps(
                    {"error": f"{type(exc).__name__}: {exc}"[:2000]},
                    ensure_ascii=False,
                )
            finally:
                job.lease_owner = None
                job.lease_expires_at = None
                job.updated_at = _iso(now)

    return len(payloads)


def run_forever(
    engine,
    settings,
    handlers: dict,
    sweepers: list | None = None,
    *,
    interval_seconds: float = 2.0,
    limit: int = 2,
    stop=None,
) -> None:
    """Loop ``run_once`` forever (or until ``stop()`` returns truthy)."""
    while True:
        if stop is not None and stop():
            return
        try:
            run_once(engine, settings, handlers, sweepers, limit=limit)
        except Exception:  # noqa: BLE001 - worker must survive DB hiccups
            logger.exception("worker pass failed")
        time.sleep(interval_seconds)

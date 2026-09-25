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

from sqlalchemy import select

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
    run_after <= now). Sets lease_owner=worker_id,
    lease_expires_at=now+300s and increments attempts.
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
    for job in rows:
        job.state = "running"
        job.lease_owner = worker_id
        job.lease_expires_at = lease_expires_at
        job.attempts = (job.attempts or 0) + 1
        job.updated_at = now_iso
    return list(rows)


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

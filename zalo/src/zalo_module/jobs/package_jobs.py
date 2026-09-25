"""Package jobs — MIN-97 slice C (contract §3/§7/§8).

Job kinds (pinned in decision-sheet §0):

- ``package_build`` — collect unpackaged records, validate each payload
  against the vendored ``raw-record.schema.json``, seal them into an
  immutable raw package (staging → fsync → atomic rename), then mark
  ``records.packaged_in``.
- ``package_sweep`` — post-ACK retention: expire ``acked`` packages whose
  ACK anchor is older than 30 days, or evict oldest acked packages when the
  acked byte total exceeds 1 GiB. Pending/sealed packages are never touched.

Sweepers (top of each ``run_once`` pass):

- ``scan_unpacked_records`` — enqueue ``package_build`` when packageable
  records wait and no build job is already active.
- ``package_retention_sweep`` — run :func:`expire_packages` every pass
  (mirrors MIN-94's ``expire_media_sweep`` pattern; the ``package_sweep``
  job kind exists to force the same pass manually).

Crash-safety: the build writes into ``packages/.staging-<package_id>/`` and
publishes by atomic rename; a crash leaves an orphan staging dir which the
next build removes before collecting. ``records.packaged_in`` is only set
inside the same transaction as the sealed ledger row, so a crash mid-build
re-runs cleanly — records are simply collected again (idempotent rebuild).
"""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select

from zalo_module.audit import record_access
from zalo_module.delivery.package import build_package
from zalo_module.delivery.record_check import validate_record
from zalo_module.jobs.worker import JobExpired, enqueue_job
from zalo_module.models import Job, Package, Record

logger = logging.getLogger(__name__)

# Contract §5.3 + decision-sheet: package bodies carry these record kinds.
# ``listener_session`` records ARE contract body kinds (raw-record enum);
# only internal ``discovery`` rows are excluded — those are written with
# ``packaged_in="__internal__"`` at ingest so ``IS NULL`` skips them.
PACKAGE_KINDS = frozenset(
    {"message_text", "ocr_page", "processing_status", "source_event", "listener_session"}
)
_PACKAGE_KINDS_ORDER = (
    "message_text", "ocr_page", "processing_status", "source_event", "listener_session",
)

# Quantitative limits — contract §3.6.
PACKAGE_RECORD_LIMIT = 1000
PACKAGE_BYTES_LIMIT = 16 * 1024 * 1024  # records.jsonl ≤ 16 MiB

# Post-ACK retention — contract §8.3 / decision-sheet §4.5.
ACK_TTL_DAYS = 30
ACK_CAP_BYTES = 1 << 30  # 1 GiB

_ACTIVE_JOB_STATES = ("queued", "running", "retry_wait")
_STAGING_PREFIX = ".staging-"
# A published-looking package dir with no ledger row is only deleted once it
# is provably stale — guards against racing a build whose rename already
# landed while its ledger row is still uncommitted.
ORPHAN_PUBLISHED_MIN_AGE_SECONDS = 600  # 10 minutes


# ---------------------------------------------------------------------------
# registration (consumed by jobs.handlers.build_handlers/build_sweepers)
# ---------------------------------------------------------------------------


def register(handlers: dict) -> None:
    handlers["package_build"] = handle_package_build
    handlers["package_sweep"] = handle_package_sweep


def register_sweepers(sweepers: list) -> None:
    sweepers.append(scan_unpacked_records)
    sweepers.append(package_retention_sweep)


# ---------------------------------------------------------------------------
# sweeper: enqueue a build when unpackaged records exist
# ---------------------------------------------------------------------------


def scan_unpacked_records(session, settings) -> None:
    """Enqueue ``package_build`` when packageable records are waiting.

    Skipped when no consumer is registered (a build cannot name a consumer)
    or when a build job is already queued/running/retrying — sweeps must not
    pile up duplicate builds.
    """
    if not getattr(settings, "consumer_id", None):
        return
    waiting = session.execute(
        select(func.count())
        .select_from(Record)
        .where(Record.packaged_in.is_(None), Record.kind.in_(PACKAGE_KINDS))
    ).scalar_one()
    if not waiting:
        return
    active = session.execute(
        select(func.count())
        .select_from(Job)
        .where(Job.kind == "package_build", Job.state.in_(_ACTIVE_JOB_STATES))
    ).scalar_one()
    if active:
        return
    enqueue_job("package_build", {}, session, max_attempts=3)


# ---------------------------------------------------------------------------
# package_build handler
# ---------------------------------------------------------------------------


def _canonical_payload_bytes(payload: dict) -> bytes:
    return (
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _dir_mtime(path: Path) -> float:
    """Newest mtime across ``path`` and its contents (safe on Windows)."""
    try:
        latest = path.stat().st_mtime
    except OSError:
        return 0.0
    for child in path.rglob("*"):
        try:
            latest = max(latest, child.stat().st_mtime)
        except OSError:
            pass
    return latest


def _clean_orphan_staging(settings, session) -> int:
    """Remove orphan dirs under ``packages/`` left by crashed builds.

    Two shapes:

    - ``packages/.staging-*`` — always orphaned (a published package never
      carries that name); removed unconditionally.
    - ``packages/<id>`` — a *published-looking* dir with **no** ledger row.
      A crash between the atomic rename and the ledger commit leaves one;
      removed only when its newest mtime is older than
      ``ORPHAN_PUBLISHED_MIN_AGE_SECONDS`` so an in-flight build on another
      worker is never swept out from under it.
    """
    root = Path(settings.runtime_root) / "packages"
    removed = 0
    if not root.is_dir():
        return 0
    known_ids = {
        pid for (pid,) in session.execute(select(Package.package_id)).all()
    }
    stale_before = time.time() - ORPHAN_PUBLISHED_MIN_AGE_SECONDS
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith(_STAGING_PREFIX):
            shutil.rmtree(entry, ignore_errors=True)
            removed += 1
        elif entry.name not in known_ids and _dir_mtime(entry) <= stale_before:
            shutil.rmtree(entry, ignore_errors=True)
            removed += 1
    return removed


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_sha256_text(payload: dict) -> str:
    blob = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _latest_revision(session, logical_id: str, extra: dict) -> int:
    """Max revision for ``logical_id`` across stored rows + in-flight notes."""
    rev = session.execute(
        select(func.max(Record.revision)).where(Record.logical_id == logical_id)
    ).scalar()
    return max(rev or 0, extra.get(logical_id, 0))


def _record_at_revision(session, logical_id: str, revision: int) -> Record | None:
    return session.execute(
        select(Record).where(
            Record.logical_id == logical_id, Record.revision == revision
        )
    ).scalar_one_or_none()


def _make_skip_note(
    session, invalid: Record, codes: list[str], note_rev: dict
) -> tuple[Record, dict] | None:
    """Build a ``processing_status`` {code: note} record explaining a skip.

    The note is a new revision of the *same* logical_id (contract §5.3:
    processing_status is attachment/page-scoped). It reuses the invalid
    record's ``captured_at`` and ``source`` verbatim — contract §5.1 makes
    those immutable across revisions — and ships inside the same package so
    the skip is never silent. Returns ``(Record row, payload)`` or None when
    the invalid payload cannot even supply a usable source block.
    """
    try:
        payload = json.loads(invalid.payload_json)
    except (TypeError, ValueError):
        payload = None
    source = payload.get("source") if isinstance(payload, dict) else None
    if not isinstance(source, dict):
        return None
    required = ("provider", "account_id", "conversation_id", "conversation_type")
    if any(source.get(k) is None for k in required):
        return None

    revision = _latest_revision(session, invalid.logical_id, note_rev) + 1
    prev = _record_at_revision(session, invalid.logical_id, revision - 1)
    # Prev is an in-flight note when the latest revision was created by an
    # earlier skip in the same build.
    prev_id = (
        prev.record_id
        if prev is not None
        else note_rev.get(f"{invalid.logical_id}:record_id")
    )
    if prev_id is None:
        return None

    detail = ",".join(codes)[:380]
    note_payload = {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "processing_status",
        "record_id": str(uuid.uuid4()),
        "logical_id": invalid.logical_id,
        "revision": revision,
        "supersedes": {"record_id": prev_id, "revision": revision - 1},
        "captured_at": invalid.captured_at,
        "recorded_at": _now_iso(),
        "source": source,
        "status": {
            "code": "note",
            "note": (
                f"record {invalid.record_id} (kind {invalid.kind}) failed "
                f"raw-record validation and was not packaged: {detail}"
            )[:500],
        },
    }
    # Never emit a note that itself fails the contract schema.
    if validate_record(note_payload):
        return None

    payload_json = json.dumps(
        note_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    row = Record(
        record_id=note_payload["record_id"],
        logical_id=invalid.logical_id,
        revision=revision,
        kind="processing_status",
        canonical_sha256=_canonical_sha256_text(note_payload),
        payload_json=payload_json,
        captured_at=invalid.captured_at,
        recorded_at=note_payload["recorded_at"],
    )
    # note_rev is only consumed once the caller commits to emitting the note
    # (a note dropped for package-limit reasons must not burn a revision).
    return row, note_payload


def handle_package_build(session, job, settings) -> dict:
    """Seal all unpackaged records into one raw package.

    Selection: ``records.packaged_in IS NULL`` and ``kind`` in the four
    package kinds, oldest first. Each payload is validated against the
    vendored raw-record schema; failures are skipped *loudly* — a
    ``processing_status`` note record goes into the same package when the
    invalid record still yields a usable source block, and the skip is
    reported in the job result. Records whose ``packaged_in`` is a sentinel
    (``__discovery__``/``__internal__`` — not a real package id) are never
    collected; ``listener_session`` **is** packageable (``PACKAGE_KINDS``).
    """
    orphan_dirs = _clean_orphan_staging(settings, session)

    consumer_id = getattr(settings, "consumer_id", None)
    if not consumer_id:
        raise JobExpired("consumer_id is not configured; cannot name a consumer")

    rows = list(
        session.execute(
            select(Record)
            .where(Record.packaged_in.is_(None), Record.kind.in_(PACKAGE_KINDS))
            .order_by(Record.captured_at, Record.record_id)
        )
        .scalars()
    )
    if not rows:
        return {"built": False, "orphan_staging_removed": orphan_dirs}

    packaged_rows: list[Record] = []
    payloads: list[dict] = []
    note_rows: list[Record] = []
    skipped: list[dict] = []
    note_rev: dict = {}  # logical_id -> newest in-flight revision (+ :record_id)
    used_bytes = 0
    limit_hit = False

    for row in rows:
        if limit_hit:
            break  # remaining rows stay unpackaged for the next build
        try:
            payload = json.loads(row.payload_json)
        except (TypeError, ValueError):
            payload = None
        codes = validate_record(payload) if payload is not None else ["json_invalid"]

        # A single record that can never fit an empty package is treated as
        # unpackageable — otherwise it would stall the build queue forever.
        size = len(_canonical_payload_bytes(payload)) if isinstance(payload, dict) else 0
        if payload is None or codes or size > PACKAGE_BYTES_LIMIT:
            if not codes:
                codes = ["size_limit_exceeded"]
            note_emitted = False
            note = _make_skip_note(session, row, codes, note_rev)
            if note is not None:
                note_row, note_payload = note
                note_size = len(_canonical_payload_bytes(note_payload))
                if (
                    len(payloads) < PACKAGE_RECORD_LIMIT
                    and used_bytes + note_size <= PACKAGE_BYTES_LIMIT
                ):
                    session.add(note_row)
                    session.flush()
                    note_rows.append(note_row)
                    payloads.append(note_payload)
                    used_bytes += note_size
                    note_emitted = True
                    note_rev[row.logical_id] = note_row.revision
                    note_rev[f"{row.logical_id}:record_id"] = note_row.record_id
                else:
                    # The note itself would overflow this package — drop the
                    # in-flight note row so it is never persisted.
                    note_emitted = False
            if not note_emitted:
                logger.warning(
                    "record %s (%s) failed packaging validation and cannot "
                    "emit a note in this package: %s",
                    row.record_id, row.kind, codes,
                )
            skipped.append({"record_id": row.record_id, "codes": codes})
            # Mark the invalid row as consumed by this build so it never
            # re-enters the collection — its disposition is the note above
            # (or the job-result entry when a note could not be emitted).
            packaged_rows.append(row)
            continue

        if (
            len(payloads) >= PACKAGE_RECORD_LIMIT
            or used_bytes + size > PACKAGE_BYTES_LIMIT
        ):
            limit_hit = True
            break
        packaged_rows.append(row)
        payloads.append(payload)
        used_bytes += size

    package_id = build_package(payloads, consumer_id, settings, session)
    pkg = session.get(Package, package_id)

    marked = 0
    for row in packaged_rows:
        row.packaged_in = package_id
        marked += 1
    for row in note_rows:
        row.packaged_in = package_id

    return {
        "built": True,
        "package_id": package_id,
        "sequence": pkg.sequence if pkg else None,
        "record_count": len(payloads),
        "skipped_invalid": skipped,
        "orphan_staging_removed": orphan_dirs,
    }


def handle_package_sweep(session, job, settings) -> dict:
    """Force a post-ACK retention pass (same code as the periodic sweeper)."""
    return expire_packages(session, settings)


# ---------------------------------------------------------------------------
# post-ACK retention (contract §8.3)
# ---------------------------------------------------------------------------


def _parse_iso(value) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _ack_anchor(pkg: Package) -> datetime | None:
    """Retention anchor: the later of ``sealed_at`` and the receipt's
    ``received_at`` — never expires earlier than *either* the sheet's
    ``sealed_at + 30d`` pin or the contract's "30 days from receipt accepted"
    (§8.3). Returns None when neither timestamp parses."""
    candidates = [_parse_iso(pkg.sealed_at)]
    if pkg.receipt_json:
        try:
            receipt = json.loads(pkg.receipt_json)
        except (TypeError, ValueError):
            receipt = None
        if isinstance(receipt, dict):
            candidates.append(_parse_iso(receipt.get("received_at")))
    candidates = [c for c in candidates if c is not None]
    return max(candidates) if candidates else None


def _package_dir(settings, pkg: Package) -> Path:
    return Path(settings.runtime_root) / pkg.dir_rel_path


def _dir_bytes(path: Path) -> int:
    total = 0
    if path.is_dir():
        for f in path.iterdir():
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    return total


def _expire_one(settings, pkg: Package) -> int:
    """Delete the package dir and mark the ledger row ``expired``.

    The ledger row is kept — expiry is about payload bytes, not history.
    Returns the freed byte count.
    """
    pkg_dir = _package_dir(settings, pkg)
    freed = _dir_bytes(pkg_dir)
    shutil.rmtree(pkg_dir, ignore_errors=True)
    record_access(pkg_dir, "package")
    pkg.status = "expired"
    return freed


def expire_packages(
    session,
    settings,
    *,
    now: datetime | None = None,
    ttl_days: int = ACK_TTL_DAYS,
    cap_bytes: int = ACK_CAP_BYTES,
) -> dict:
    """Expire acked packages past retention; never touch un-ACKed rows.

    - ``acked`` and ``max(sealed_at, receipt.received_at) + ttl_days <= now``
      → delete dir, status ``expired``.
    - total acked bytes > ``cap_bytes`` → expire *oldest* acked packages
      (ascending sequence) until under the cap.
    - ``pending``/``sealed`` (un-ACKed) packages are retained forever — even
      under disk pressure (contract §8.3).
    """
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    rows = list(
        session.execute(
            select(Package)
            .where(Package.status == "acked")
            .order_by(Package.sequence)
        )
        .scalars()
    )
    expired: list[str] = []
    freed = 0
    cutoff = now - timedelta(days=ttl_days)

    for pkg in rows:
        anchor = _ack_anchor(pkg)
        if anchor is not None and anchor <= cutoff:
            freed += _expire_one(settings, pkg)
            expired.append(pkg.package_id)

    remaining = [p for p in rows if p.status == "acked"]
    total = sum(_dir_bytes(_package_dir(settings, p)) for p in remaining)
    for pkg in remaining:  # already ordered by sequence (oldest first)
        if total <= cap_bytes:
            break
        size = _expire_one(settings, pkg)
        total -= size
        freed += size
        expired.append(pkg.package_id)

    if expired:
        session.flush()
    return {
        "expired": expired,
        "expired_count": len(expired),
        "freed_bytes": freed,
        "acked_bytes_after": total,
    }


def package_retention_sweep(session, settings) -> None:
    """Periodic sweeper: enforce post-ACK retention every worker pass."""
    expire_packages(session, settings)

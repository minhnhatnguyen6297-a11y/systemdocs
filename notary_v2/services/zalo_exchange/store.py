"""Persistence helpers for the Zalo raw-package consumer (MIN-99).

Wraps the exchange models written by the controller — ``ZaloRawRecord``,
``ZaloImportLedger``, ``ZaloSyncState``, ``ZaloParseJob``,
``ZaloIntakeResult`` (models.py — DO NOT EDIT). No writes to business tables
(customers/properties/cases/participants) and no legacy ``zalo_*`` inbox
tables live here.

Layering rule: functions add/flush rows and leave ``db.commit()`` to the
caller (sync.py) so ledger + raw rows + parse job land in ONE commit —
contract §7.3's "durable before ACK" requirement.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import (
    ZaloImportLedger,
    ZaloIntakeResult,
    ZaloParseJob,
    ZaloRawRecord,
    ZaloSyncState,
)

DECISION_IMPORTED = "imported"
DECISION_QUARANTINED = "quarantined"
RECEIPT_ACCEPTED = "accepted"
RECEIPT_REJECTED = "rejected"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value) -> datetime | None:
    """ISO-8601 with mandatory offset (contract §3.5) → aware datetime."""
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ---------------------------------------------------------------------------
# zalo_sync_state — small kv store (cursors, run metadata, receipt docs).
# ---------------------------------------------------------------------------


def get_state(db: Session, key: str, default: str | None = None) -> str | None:
    row = db.get(ZaloSyncState, key)
    return row.value if row is not None else default


def set_state(db: Session, key: str, value: str) -> None:
    row = db.get(ZaloSyncState, key)
    if row is None:
        db.add(ZaloSyncState(key=key, value=value))
    else:
        row.value = value


def get_state_json(db: Session, key: str, default=None):
    raw = get_state(db, key)
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except ValueError:
        return default


# ---------------------------------------------------------------------------
# zalo_import_ledger — one row per package_id; replay is idempotent.
# ---------------------------------------------------------------------------


def ledger_get(db: Session, package_id: str) -> ZaloImportLedger | None:
    return db.get(ZaloImportLedger, package_id)


def last_imported_sequence(db: Session) -> int:
    """Highest sequence with decision=imported (0 when none).

    Quarantined packages do not advance the cursor: a rejected package never
    becomes importable, so it must not block later sequences forever.
    """
    value = db.execute(
        select(func.max(ZaloImportLedger.sequence)).where(
            ZaloImportLedger.decision == DECISION_IMPORTED
        )
    ).scalar()
    return int(value or 0)


def ledger_counts(db: Session) -> dict:
    rows = db.execute(
        select(ZaloImportLedger.decision, func.count())
        .group_by(ZaloImportLedger.decision)
    ).all()
    return {decision: count for decision, count in rows}


# ---------------------------------------------------------------------------
# Record dedupe / conflict checks — contract §5.1/§7.3 (§11.3 codes).
# ---------------------------------------------------------------------------


def check_record_conflicts(db: Session, records: list) -> tuple[list, list]:
    """Split ``records`` — ``[(parsed_obj, raw_line)]`` pairs — into
    ``(errors, to_insert)`` where ``to_insert`` is ``[(obj, digest, raw_line)]``.

    - same ``record_id`` with a different canonical hash → ``record_conflict``
    - same ``logical_id``+``revision`` with different content →
      ``source_revision_conflict``
    - ``supersedes`` must point at revision ``rev-1`` of a record already
      imported or earlier in the same package → ``revision_chain_broken``
    - ``captured_at`` differing between revisions of one ``logical_id`` →
      ``immutable_field_changed`` (a revision is a re-ingest of the SAME
      capture — contract §5.3)
    - a byte-identical record already stored (or repeated inside the
      package) is a no-op: dropped from ``to_insert``, no error
      (re-import of the same bytes is idempotent, contract §7.3)
    """
    from .validate import _parse_iso, canonical_sha256  # local: avoid a cycle

    parsed = [obj for obj, _raw in records]
    record_ids = {r.get("record_id") for r in parsed}
    supersedes_ids = {
        r["supersedes"]["record_id"] for r in parsed
        if isinstance(r.get("supersedes"), dict)
        and isinstance(r["supersedes"].get("record_id"), str)
    }
    lookup_ids = {i for i in record_ids | supersedes_ids if isinstance(i, str)}
    logical_ids = {r.get("logical_id") for r in parsed
                   if isinstance(r.get("logical_id"), str)}

    existing_by_id: dict = {}
    if lookup_ids:
        for row in db.execute(
            select(ZaloRawRecord).where(ZaloRawRecord.record_id.in_(lookup_ids))
        ).scalars():
            existing_by_id[row.record_id] = row
    # One logical_id query feeds both the (lid,rev) dedupe map and the
    # cross-revision captured_at check. captured_at is compared on the
    # VERBATIM payload string (payload_json) — the DB column is a naive
    # wall-clock on SQLite and cannot represent the instant faithfully.
    existing_by_key: dict = {}
    existing_by_lid: dict = {}
    if logical_ids:
        for row in db.execute(
            select(ZaloRawRecord).where(
                ZaloRawRecord.logical_id.in_(logical_ids))
        ).scalars():
            existing_by_key[(row.logical_id, row.revision)] = row
            existing_by_lid.setdefault(row.logical_id, []).append(
                (row.revision, _payload_captured_at(row)))

    # (record_id, revision) pairs the supersedes pointer may legitimately
    # reference: everything already imported plus everything in this package.
    known_targets = {
        (row.record_id, row.revision) for row in existing_by_id.values()
    }
    known_targets |= {
        (r.get("record_id"), r.get("revision")) for r in parsed
    }

    errors: list = []
    to_insert: list = []
    seen_ids: dict = {}
    seen_keys: dict = {}
    seen_lids: dict = {}
    for index, (rec, raw_line) in enumerate(records, 1):
        rid = rec.get("record_id")
        lid = rec.get("logical_id")
        key = (lid, rec.get("revision"))
        digest = canonical_sha256(rec)
        where = f"records.jsonl line {index}"

        prior = existing_by_id.get(rid) or seen_ids.get(rid)
        prior_hash = prior.canonical_sha256 if prior is not None else None
        prior_key = existing_by_key.get(key) or seen_keys.get(key)
        prior_key_hash = prior_key.canonical_sha256 if prior_key is not None else None

        if prior_hash is not None and prior_hash != digest:
            errors.append(("record_conflict",
                           f"{where}: record_id {rid} already imported with a "
                           "different canonical_sha256"))
            continue
        if prior_key_hash is not None and prior_key_hash != digest:
            errors.append(("source_revision_conflict",
                           f"{where}: (logical_id, revision) {key} already "
                           "imported with different content"))
            continue
        if prior_hash is not None or prior_key_hash is not None:
            continue  # byte-identical re-import — no-op

        sup = rec.get("supersedes")
        rev = rec.get("revision")
        if isinstance(rev, int) and not isinstance(rev, bool) and rev >= 2:
            target = (sup.get("record_id"), sup.get("revision")) \
                if isinstance(sup, dict) else None
            if sup is None or sup.get("revision") != rev - 1 \
                    or target not in known_targets:
                errors.append(("revision_chain_broken",
                               f"{where}: revision {rev} must supersede revision "
                               f"{rev - 1} of a record already published to this "
                               "consumer (or earlier in this package)"))
                continue

        # captured_at is immutable across revisions of one logical_id: a new
        # revision re-ingests the same capture, so the timestamp cannot move
        # (contract rules_record: erev < rev → same captured_at, compared on
        # string equality or parsed-instant equality).
        if isinstance(rev, int) and not isinstance(rev, bool) and rev >= 2:
            cap_raw = rec.get("captured_at")
            cap = _parse_iso(cap_raw)
            broken = False
            priors = list(existing_by_lid.get(lid, ()))
            priors += seen_lids.get(lid, ())
            for erev, raw in priors:
                if isinstance(erev, int) and erev < rev and raw is not None:
                    same = raw == cap_raw
                    if not same:
                        old = _parse_iso(raw)
                        same = old is not None and cap is not None and old == cap
                    if not same:
                        errors.append(("immutable_field_changed",
                                       f"{where}: captured_at differs between "
                                       f"revision {erev} and {rev} of "
                                       f"logical_id {lid}"))
                        broken = True
                        break
            if broken:
                continue

        seen_ids[rid] = _Ref(digest)
        seen_keys[key] = _Ref(digest)
        seen_lids.setdefault(lid, []).append((rev, rec.get("captured_at")))
        to_insert.append((rec, digest, raw_line))
    return errors, to_insert


def _payload_captured_at(row) -> str | None:
    """The verbatim captured_at string inside a stored payload_json."""
    try:
        payload = json.loads(row.payload_json or "")
    except ValueError:
        return None
    return payload.get("captured_at") if isinstance(payload, dict) else None


class _Ref:
    """Tiny stand-in for a stored row when the row only exists in this batch."""

    __slots__ = ("canonical_sha256",)

    def __init__(self, canonical_sha256: str):
        self.canonical_sha256 = canonical_sha256


# ---------------------------------------------------------------------------
# Import / quarantine — rows are flushed by these helpers, committed by caller.
# ---------------------------------------------------------------------------


def insert_raw_records(db: Session, to_insert: list, *, package_id: str,
                       package_sequence: int) -> int:
    """Add one ZaloRawRecord per ``(record, digest, raw_line)`` triple;
    payload_json is the verbatim JSONL line (never re-serialized).
    Returns rows added."""
    added = 0
    for rec, digest, raw_line in to_insert:
        raw_text = raw_line if raw_line is not None else json.dumps(
            rec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        db.add(ZaloRawRecord(
            record_id=rec["record_id"],
            logical_id=rec["logical_id"],
            revision=rec["revision"],
            kind=rec["record_kind"],
            package_id=package_id,
            package_sequence=package_sequence,
            captured_at=_parse_iso(rec.get("captured_at")) or utcnow(),
            recorded_at=_parse_iso(rec.get("recorded_at")) or utcnow(),
            canonical_sha256=digest,
            payload_json=raw_text,
        ))
        added += 1
    return added


def add_ledger_row(db: Session, *, package_id: str, consumer_id: str,
                   sequence: int, manifest_sha256: str, record_count: int,
                   decision: str, sealed_at=None,
                   quarantine_reason: str | None = None) -> ZaloImportLedger:
    """Add the ledger row for a decided package. ``receipt_id`` is minted now
    so a re-send replays the exact same idempotency key."""
    row = ZaloImportLedger(
        package_id=package_id,
        consumer_id=consumer_id,
        sequence=sequence,
        manifest_sha256=manifest_sha256,
        record_count=record_count,
        sealed_at=sealed_at,
        decision=decision,
        quarantine_reason=quarantine_reason,
        receipt_id=str(uuid.uuid4()),
        imported_at=utcnow() if decision == DECISION_IMPORTED else None,
    )
    db.add(row)
    return row


def mark_receipt(db: Session, package_id: str, status: str) -> None:
    row = db.get(ZaloImportLedger, package_id)
    if row is not None:
        row.receipt_status = status


def enqueue_parse_job(db: Session, package_id: str) -> ZaloParseJob:
    """Durable parse job; idempotent — a live job for the package is reused."""
    existing = db.execute(
        select(ZaloParseJob).where(
            ZaloParseJob.package_id == package_id,
            ZaloParseJob.state.in_(("pending", "running")),
        )
    ).scalars().first()
    if existing is not None:
        return existing
    job = ZaloParseJob(job_id=str(uuid.uuid4()), package_id=package_id,
                       state="pending", attempts=0)
    db.add(job)
    return job


# ---------------------------------------------------------------------------
# Receipt documents — stored verbatim so a lost-ACK replay re-sends the exact
# same canonical body (producer-side replay key is receipt_id + body).
# ---------------------------------------------------------------------------

_RECEIPT_KEY_PREFIX = "receipt:"


def store_receipt_doc(db: Session, package_id: str, receipt: dict) -> None:
    set_state(db, _RECEIPT_KEY_PREFIX + package_id,
              json.dumps(receipt, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")))


def load_receipt_doc(db: Session, package_id: str) -> dict | None:
    doc = get_state_json(db, _RECEIPT_KEY_PREFIX + package_id)
    return doc if isinstance(doc, dict) else None


def records_for_package(db: Session, package_id: str) -> list:
    """Raw rows of one imported package in file order (parser input, slice B)."""
    return list(db.execute(
        select(ZaloRawRecord).where(ZaloRawRecord.package_id == package_id)
    ).scalars())


def pending_parse_jobs(db: Session) -> list:
    return list(db.execute(
        select(ZaloParseJob).where(ZaloParseJob.state == "pending")
    ).scalars())


# ---------------------------------------------------------------------------
# zalo_intake_results — revisioned parser output (used by slice B runner).
# ---------------------------------------------------------------------------


def next_result_revision(db: Session, package_id: str) -> int:
    value = db.execute(
        select(func.count()).select_from(ZaloIntakeResult).where(
            ZaloIntakeResult.package_id == package_id
        )
    ).scalar()
    return int(value or 0) + 1


def add_intake_result(db: Session, *, package_id: str, parser_version: str,
                      result_json: str, warnings_json: str = "[]") -> ZaloIntakeResult:
    row = ZaloIntakeResult(
        result_id=str(uuid.uuid4()),
        package_id=package_id,
        revision=next_result_revision(db, package_id),
        parser_version=parser_version,
        result_json=result_json,
        warnings_json=warnings_json,
    )
    db.add(row)
    return row


def results_for_package(db: Session, package_id: str) -> list:
    return list(db.execute(
        select(ZaloIntakeResult)
        .where(ZaloIntakeResult.package_id == package_id)
        .order_by(ZaloIntakeResult.revision)
    ).scalars())

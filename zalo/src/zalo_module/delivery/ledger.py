"""Delivery ledger — pending feed + receipt bookkeeping (contract §7).

``record_receipt`` does the contract-consistent handling for
``intake.receipt.v1`` documents: the body is validated against the vendored
``schemas/receipt.schema.json`` (required fields, closed
``additionalProperties``, uuid/sha256 formats and the RFC 3339 ``received_at``
format with mandatory offset — contract §3.5), then the ledger applies the
semantic checks. ``ValueError`` messages are stable internal codes that the
API layer maps onto the contract error catalog (§11):

- ``schema_invalid``      → ``schema_invalid``      (400)
- ``package_not_found``   → ``package_unknown``     (404)
- ``package_conflict``    → ``package_conflict``    (409)
- ``consumer_mismatch``   → ``receipt_consumer_mismatch`` (409)
- ``manifest_mismatch``   → ``receipt_hash_mismatch``     (409)
- ``count_mismatch``      → ``receipt_count_mismatch``    (409)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from sqlalchemy import select

from zalo_module.delivery._schema import load_schema, validate
from zalo_module.models import Package

# Repo-rooted vendored schemas (byte-identical to contracts/zalo-intake/*) —
# same resolution rule as delivery.record_check.
_SCHEMAS_DIR = Path(
    os.environ.get("ZALO_INTAKE_SCHEMAS_DIR")
    or (Path(__file__).resolve().parents[3] / "schemas")
)

_receipt_schema = None


def _schema():
    """Lazily load the vendored ``receipt.schema.json``."""
    global _receipt_schema
    if _receipt_schema is None:
        _receipt_schema = load_schema(_SCHEMAS_DIR / "receipt.schema.json")
    return _receipt_schema


def _canonical(obj: dict) -> str:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def list_pending(consumer_id, session, after_sequence: int = 0) -> list[Package]:
    """Pending-feed packages for ``consumer_id`` with sequence > after_sequence.

    The ``delivery=pending`` feed (contract §7.2) contains packages in status
    ``sealed`` — READY.json published, not yet ACKed. ``pending`` rows (a
    pre-seal ledger state nothing currently writes) are *not* READY packages
    and are never listed.
    """
    stmt = (
        select(Package)
        .where(
            Package.consumer_id == consumer_id,
            Package.status == "sealed",
            Package.sequence > after_sequence,
        )
        .order_by(Package.sequence)
    )
    return list(session.execute(stmt).scalars())


def _stored_receipts(session) -> list[dict]:
    """All stored receipt documents (any package), parsed."""
    rows = session.execute(
        select(Package.receipt_json).where(Package.receipt_json.isnot(None))
    ).all()
    receipts: list[dict] = []
    for (raw,) in rows:
        try:
            doc = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if isinstance(doc, dict):
            receipts.append(doc)
    return receipts


def record_receipt(receipt: dict, session, settings) -> str:
    """Store an ``intake.receipt.v1`` decision; return ``receipt_id``.

    Semantics (contract §7.3 + fix-round-1 I1):

    - Schema-validated first — anything the vendored schema bounds
      (``received_at`` RFC 3339 with mandatory offset, uuid/sha256 formats,
      ``error`` required-on-rejected/forbidden-on-accepted, closed key set)
      fails as ``schema_invalid``; a malformed timestamp can therefore never
      silently land in the retention anchor.
    - Byte-identical replay of the stored receipt returns the stored
      decision (idempotency key = ``receipt_id``) without re-validating.
    - A stored decision is **immutable**: the same ``receipt_id`` with a
      different canonical body, or *any* new receipt for a package that
      already recorded a decision (``acked`` or ``rejected``), raises
      ``package_conflict`` — nothing overwrites ``receipt_json`` and the
      package status never flips.

    ``settings`` is part of the pinned signature (reserved for retention
    accounting in MIN-97); currently unused.
    """
    if not isinstance(receipt, dict):
        raise ValueError("schema_invalid")
    # Every failure the schema reports maps to the same contract code —
    # receipt.schema.json carries no x-error-code branches.
    if validate(receipt, _schema()):
        raise ValueError("schema_invalid")

    pkg = session.get(Package, receipt["package_id"])
    if pkg is None:
        raise ValueError("package_not_found")

    canonical = _canonical(receipt)

    # Idempotent replay (contract §7.3): a byte-identical receipt returns
    # the stored decision. This fast path runs before the conflict branches
    # so a replayed ACK still works after the package left the pending feed.
    if pkg.receipt_json is not None and pkg.receipt_json == canonical:
        return receipt["receipt_id"]

    # Same ``receipt_id`` with a different canonical body — the idempotency
    # key is being reused for a different decision; conflict, never
    # overwrite. Scoped across packages: a receipt_id may not migrate.
    for stored in _stored_receipts(session):
        if stored.get("receipt_id") == receipt["receipt_id"]:
            raise ValueError("package_conflict")

    # This package already recorded a decision (rejected receipts also
    # store their document): a different receipt is a conflict, not a new
    # decision — ``rejected`` stays pending, ``acked`` stays acked.
    if pkg.receipt_json is not None:
        raise ValueError("package_conflict")

    if pkg.consumer_id != receipt["consumer_id"]:
        raise ValueError("consumer_mismatch")
    if pkg.manifest_sha256 != receipt["manifest_sha256"]:
        raise ValueError("manifest_mismatch")
    if receipt["record_count"] != pkg.record_count:
        raise ValueError("count_mismatch")

    pkg.receipt_json = canonical
    # Only an `accepted` receipt removes the package from the pending feed;
    # `rejected` leaves it pending per contract §7.2.
    if receipt["status"] == "accepted":
        pkg.status = "acked"
    return receipt["receipt_id"]

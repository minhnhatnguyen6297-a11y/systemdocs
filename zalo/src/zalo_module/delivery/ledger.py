"""Delivery ledger — pending feed + receipt bookkeeping (contract §7).

``record_receipt`` does the minimal contract-consistent handling for
``intake.receipt.v1`` documents; ``ValueError`` messages are stable internal
codes that the API layer maps onto the contract error catalog (§11):

- ``schema_invalid``      → ``schema_invalid``      (400)
- ``package_not_found``   → ``package_unknown``     (404)
- ``consumer_mismatch``   → ``receipt_consumer_mismatch`` (409)
- ``manifest_mismatch``   → ``receipt_hash_mismatch``     (409)
- ``count_mismatch``      → ``receipt_count_mismatch``    (409)
"""

from __future__ import annotations

import json

from sqlalchemy import select

from zalo_module.models import Package

_RECEIPT_REQUIRED = {
    "schema_version",
    "receipt_id",
    "package_id",
    "consumer_id",
    "status",
    "received_at",
    "manifest_sha256",
    "record_count",
}


def _canonical(obj: dict) -> str:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def list_pending(consumer_id, session, after_sequence: int = 0) -> list[Package]:
    """Pending packages for ``consumer_id`` with sequence > after_sequence."""
    stmt = (
        select(Package)
        .where(
            Package.consumer_id == consumer_id,
            Package.status == "pending",
            Package.sequence > after_sequence,
        )
        .order_by(Package.sequence)
    )
    return list(session.execute(stmt).scalars())


def record_receipt(receipt: dict, session, settings) -> str:
    """Store an ``intake.receipt.v1`` decision; return ``receipt_id``.

    Idempotent: replaying a receipt whose ``receipt_id`` is already stored
    returns the stored decision without re-validating (contract §7.3).
    ``settings`` is part of the pinned signature (reserved for retention
    accounting in MIN-97); currently unused.
    """
    # TODO(MIN-97): full receipt validation — sha256/uuid formats,
    # ISO timestamps.
    if not isinstance(receipt, dict):
        raise ValueError("schema_invalid")
    if receipt.get("schema_version") != "intake.receipt.v1":
        raise ValueError("schema_invalid")
    if not _RECEIPT_REQUIRED.issubset(receipt):
        raise ValueError("schema_invalid")
    status = receipt["status"]
    if status not in ("accepted", "rejected"):
        raise ValueError("schema_invalid")
    # Schema if/then/else: error required on rejected, forbidden on accepted.
    if status == "rejected" and "error" not in receipt:
        raise ValueError("schema_invalid")
    if status == "accepted" and "error" in receipt:
        raise ValueError("schema_invalid")
    if not isinstance(receipt["record_count"], int) or receipt["record_count"] < 0:
        raise ValueError("schema_invalid")

    pkg = session.get(Package, receipt["package_id"])
    if pkg is None:
        raise ValueError("package_not_found")

    # Idempotent replay (contract §7.3): only a byte-identical receipt (same
    # canonical body, hence same receipt_id) returns the stored decision.
    # Same receipt_id with a *different* body is NOT a replay — it falls
    # through to normal validation and fails consumer/hash/count checks.
    if pkg.receipt_json and pkg.receipt_json == _canonical(receipt):
        return receipt["receipt_id"]

    if pkg.consumer_id != receipt["consumer_id"]:
        raise ValueError("consumer_mismatch")
    if pkg.manifest_sha256 != receipt["manifest_sha256"]:
        raise ValueError("manifest_mismatch")
    if receipt["record_count"] != pkg.record_count:
        raise ValueError("count_mismatch")

    pkg.receipt_json = _canonical(receipt)
    # Only an `accepted` receipt removes the package from the pending feed;
    # `rejected` leaves it pending per contract §7.2.
    if status == "accepted":
        pkg.status = "acked"
    return receipt["receipt_id"]

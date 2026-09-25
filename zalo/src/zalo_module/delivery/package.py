"""Raw package builder — byte-exact per contracts/zalo-intake §3/§4.

Write order (contract §3.2): ``records.jsonl``, then ``manifest.json``, then
``READY.json`` last inside a staging dir; publish is the atomic rename to
``runtime/packages/{package_id}/``. All bytes are UTF-8 (no BOM), LF-only,
compact canonical JSON — ``json.dumps(sort_keys=True, separators=(",",":"),
ensure_ascii=False, allow_nan=False)`` — one document per line, every line
terminated by ``\n``.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from zalo_module import __version__
from zalo_module.audit import record_access
from zalo_module.models import Package

PACKAGE_FILES = ("records.jsonl", "manifest.json", "READY.json")


def _canonical_bytes(obj: dict) -> bytes:
    """One compact canonical JSON document + terminating LF, UTF-8 no BOM."""
    text = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_flushed(path: Path, data: bytes) -> None:
    with path.open("wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def build_package(records: list[dict], consumer_id: str, settings, session) -> str:
    """Seal ``records`` into an immutable raw package; return ``package_id``.

    ``records`` are already intake.raw-record.v1 payload dicts produced by the
    domain layer; the session commits the ``packages`` ledger row.
    """
    # Record-level schema validation happens in the caller (jobs/package_jobs
    # validates each payload against vendored raw-record.schema.json before
    # invoking this primitive); build_package stays a pure byte-writer.
    package_id = str(uuid.uuid4())
    max_seq = session.execute(
        select(func.max(Package.sequence)).where(
            Package.consumer_id == consumer_id
        )
    ).scalar()
    sequence = (max_seq or 0) + 1

    records_bytes = b"".join(_canonical_bytes(r) for r in records)

    manifest = {
        "schema_version": "intake.raw-package.v1",
        "package_id": package_id,
        "producer": {"service": "zalo-intake", "build_id": __version__},
        "consumer_id": consumer_id,
        "created_at": _utcnow_iso(),
        "sequence": sequence,
        "files": [
            {
                "path": "records.jsonl",
                "sha256": hashlib.sha256(records_bytes).hexdigest(),
                "bytes": len(records_bytes),
            }
        ],
        "record_count": len(records),
    }
    manifest_bytes = _canonical_bytes(manifest)

    ready = {
        "schema_version": "intake.ready.v1",
        "package_id": package_id,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "sealed_at": _utcnow_iso(),
    }
    ready_bytes = _canonical_bytes(ready)

    packages_root = Path(settings.runtime_root) / "packages"
    packages_root.mkdir(parents=True, exist_ok=True)
    staging = packages_root / f".staging-{package_id}"
    final = packages_root / package_id
    staging.mkdir()
    try:
        _write_flushed(staging / "records.jsonl", records_bytes)
        _write_flushed(staging / "manifest.json", manifest_bytes)
        # READY.json is written last — it seals the manifest bytes.
        _write_flushed(staging / "READY.json", ready_bytes)
        staging.rename(final)  # atomic publish on the same filesystem
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    for name in PACKAGE_FILES:
        record_access(final / name, "package")

    session.add(
        Package(
            package_id=package_id,
            consumer_id=consumer_id,
            sequence=sequence,
            manifest_sha256=ready["manifest_sha256"],
            record_count=len(records),
            dir_rel_path=final.relative_to(settings.runtime_root).as_posix(),
            created_at=manifest["created_at"],
            sealed_at=ready["sealed_at"],
            # Sealed = READY.json written + atomic rename done + ledger row in
            # this same transaction; the row now enters the pending feed until
            # a receipt `accepted` flips it to `acked` (contract §7.2/§8.3).
            status="sealed",
        )
    )
    return package_id

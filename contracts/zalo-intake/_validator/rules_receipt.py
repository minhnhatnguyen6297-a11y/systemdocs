"""Slice A — consumer ACK checks (kind `receipt`).

A receipt case holds receipt.json plus an optional package/ subdirectory standing
in for the already-imported package on the consumer side. The "known packages"
lookup comes from context.existing_packages = [{package_id, manifest_sha256,
record_count}], overlaid by package/manifest.json when that subdir is present.
The receipt must name a known package and repeat its manifest hash and record
count, and it must belong to the context consumer.
"""
from pathlib import Path

from . import CONTRACT_DIR
from .cases import register, register_error_codes
from .io import ContractDataError, read_json_bytes, sha256_hex
from .schema_subset import load_schema, validate

register_error_codes([
    "package_unknown", "receipt_consumer_mismatch", "receipt_hash_mismatch",
    "receipt_count_mismatch", "file_missing", "file_unexpected",
    "size_limit_exceeded",
])

RECEIPT_SCHEMA = load_schema(CONTRACT_DIR / "receipt.schema.json")

MAX_RECEIPT_BYTES = 16 * 1024


@register("receipt")
def check_receipt(case_dir, case):
    case_dir = Path(case_dir)
    ctx = case.get("context") or {}
    errors = []

    receipt_bytes = None
    for path in sorted(p for p in case_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(case_dir).as_posix()
        if rel == "case.json":
            continue
        if rel == "receipt.json":
            receipt_bytes = path.read_bytes()
            continue
        if rel.startswith("package/"):
            continue
        errors.append(("file_unexpected",
                       f"{rel}: unexpected file in a receipt case"))
    if receipt_bytes is None:
        errors.append(("file_missing", "receipt.json: required file is absent"))
        return errors

    if len(receipt_bytes) > MAX_RECEIPT_BYTES:
        errors.append(("size_limit_exceeded",
                       f"receipt.json is {len(receipt_bytes)} bytes "
                       f"(limit {MAX_RECEIPT_BYTES})"))
        return errors
    try:
        obj = read_json_bytes(receipt_bytes)
    except ContractDataError as e:
        errors.append((e.code, f"receipt.json: {e.detail}"))
        return errors
    schema_errors = validate(obj, RECEIPT_SCHEMA)
    for code, detail in schema_errors:
        errors.append((code, f"receipt.json {detail}"))
    if not isinstance(obj, dict) or schema_errors:
        return errors

    # Known packages on the consumer side: context entries, then an embedded
    # package/ subdir (its manifest hash is computed over real bytes).
    known = {}
    for entry in ctx.get("existing_packages") or []:
        if isinstance(entry, dict) and isinstance(entry.get("package_id"), str):
            known[entry["package_id"]] = entry
    embedded_manifest = case_dir / "package" / "manifest.json"
    if embedded_manifest.is_file():
        try:
            mbytes = embedded_manifest.read_bytes()
            mobj = read_json_bytes(mbytes)
        except ContractDataError as e:
            errors.append((e.code, f"package/manifest.json: {e.detail}"))
        else:
            if isinstance(mobj, dict) and isinstance(mobj.get("package_id"), str):
                known[mobj["package_id"]] = {
                    "package_id": mobj["package_id"],
                    "manifest_sha256": sha256_hex(mbytes),
                    "record_count": mobj.get("record_count"),
                }

    pkg = known.get(obj["package_id"])
    if pkg is None:
        errors.append(("package_unknown",
                       f"receipt package_id {obj['package_id']} is not among the "
                       "consumer's imported packages"))
    else:
        if obj["manifest_sha256"] != pkg.get("manifest_sha256"):
            errors.append(("receipt_hash_mismatch",
                           "receipt manifest_sha256 does not match the imported "
                           f"package ({pkg.get('manifest_sha256')})"))
        if obj["record_count"] != pkg.get("record_count"):
            errors.append(("receipt_count_mismatch",
                           f"receipt record_count {obj['record_count']} != "
                           f"imported package record_count {pkg.get('record_count')}"))

    expected_consumer = ctx.get("consumer_id")
    if expected_consumer is not None and obj["consumer_id"] != expected_consumer:
        errors.append(("receipt_consumer_mismatch",
                       f"receipt consumer_id {obj['consumer_id']} != session "
                       f"consumer {expected_consumer}"))

    return errors

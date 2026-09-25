"""Slice A — GET /intake/v1/status checks (kind `service_status`).

The schema owns the document shape (listener.state enum, pending oldest_* pair
rule and the packages == 0 absence rule). This module adds the two semantic
consistencies the schema cannot express:
  * storage.ack_warn must be true exactly when ack_bytes >= 80% of ack_cap_bytes;
  * pending.packages > 0 requires oldest_sequence + oldest_age_seconds.
Violations report status_invalid.
"""
from pathlib import Path

from . import CONTRACT_DIR
from .cases import register, register_error_codes
from .io import ContractDataError, read_json_bytes
from .schema_subset import load_schema, validate

register_error_codes(["status_invalid", "file_missing", "file_unexpected"])

STATUS_SCHEMA = load_schema(CONTRACT_DIR / "service-status.schema.json")
# Smoke-load the API response schemas no case kind exercises directly, so an
# unsupported keyword or a broken $ref there fails loudly at import time.
_PACKAGE_LIST_SCHEMA = load_schema(CONTRACT_DIR / "package-list.schema.json")
_ERROR_SCHEMA = load_schema(CONTRACT_DIR / "error.schema.json")


@register("service_status")
def check_service_status(case_dir, case):
    case_dir = Path(case_dir)
    errors = []

    status_bytes = None
    for path in sorted(p for p in case_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(case_dir).as_posix()
        if rel == "case.json":
            continue
        if rel == "status.json":
            status_bytes = path.read_bytes()
            continue
        errors.append(("file_unexpected",
                       f"{rel}: unexpected file in a service_status case"))
    if status_bytes is None:
        errors.append(("file_missing", "status.json: required file is absent"))
        return errors

    try:
        obj = read_json_bytes(status_bytes)
    except ContractDataError as e:
        errors.append((e.code, f"status.json: {e.detail}"))
        return errors
    schema_errors = validate(obj, STATUS_SCHEMA)
    for code, detail in schema_errors:
        errors.append((code, f"status.json {detail}"))
    if not isinstance(obj, dict) or schema_errors:
        return errors

    storage = obj["storage"]
    # Integer-exact form of ack_bytes >= 0.8 * ack_cap_bytes.
    warn_expected = storage["ack_bytes"] * 5 >= storage["ack_cap_bytes"] * 4
    if storage["ack_warn"] != warn_expected:
        errors.append(("status_invalid",
                       f"storage.ack_warn is {storage['ack_warn']} but "
                       f"ack_bytes={storage['ack_bytes']} of "
                       f"ack_cap_bytes={storage['ack_cap_bytes']} "
                       f"requires {warn_expected}"))

    pending = obj["pending"]
    if pending["packages"] > 0 and (
            "oldest_sequence" not in pending
            or "oldest_age_seconds" not in pending):
        errors.append(("status_invalid",
                       "pending.packages > 0 requires oldest_sequence and "
                       "oldest_age_seconds"))

    return errors

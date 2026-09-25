"""Slice A — raw package transport checks (kinds `package`, `package_sequence`).

A v1 raw package is exactly three flat files: manifest.json + records.jsonl +
READY.json. This module validates the envelope only: file whitelist, byte limits,
strict JSON/JSONL framing, manifest/READY schema, hash/size/count bindings and the
sync context (consumer, expected sequence, previously imported packages). Record
payload semantics belong to slice B's `record` kind — records.jsonl is only
framing-checked here, never record-validated.
"""
from pathlib import Path

from . import CONTRACT_DIR
from .cases import register, register_error_codes
from .io import ContractDataError, read_json_bytes, read_jsonl_bytes, sha256_hex
from .schema_subset import load_schema, validate

register_error_codes([
    "file_missing", "file_unexpected", "file_forbidden", "path_escape",
    "manifest_hash_mismatch", "ready_hash_mismatch", "size_mismatch",
    "size_limit_exceeded", "record_count_mismatch", "consumer_mismatch",
    "producer_mismatch", "sequence_invalid", "package_conflict",
])

MANIFEST_SCHEMA = load_schema(CONTRACT_DIR / "manifest.schema.json")
READY_SCHEMA = load_schema(CONTRACT_DIR / "ready.schema.json")

MAX_MANIFEST_BYTES = 64 * 1024
MAX_READY_BYTES = 64 * 1024
MAX_RECORDS_BYTES = 16 * 1024 * 1024
MAX_RECORD_COUNT = 1000

PACKAGE_FILES = ("manifest.json", "records.jsonl", "READY.json")

# manifest.files[] can only ever declare records.jsonl: a manifest cannot hash
# itself, and READY.json is written after the manifest is final.
DECLARABLE = frozenset({"records.jsonl"})

_PACKAGE_NAMES_LOWER = {n.lower() for n in PACKAGE_FILES}

# Names that carry protocol meaning elsewhere and must never sit inside a package
# (results.json is the retired pre-v1 payload; receipt.json is an API object).
_FORBIDDEN_NAMES = {"results.json", "receipt.json"}
_FORBIDDEN_NAMES_LOWER = {n.lower() for n in _FORBIDDEN_NAMES}

# Packages carry OCR text/status/metadata only — never image bytes.
_IMAGE_EXT = frozenset({
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff",
    ".heic", ".heif", ".svg", ".ico",
})
# Executables/scripts inside a data package are a security problem, not a format
# deviation — hence file_forbidden rather than file_unexpected.
_EXEC_EXT = frozenset({
    ".exe", ".dll", ".com", ".scr", ".msi", ".msp", ".bat", ".cmd", ".ps1",
    ".psm1", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh", ".hta", ".jar",
    ".apk", ".py", ".pyc", ".pyo", ".sh", ".cpl", ".msc", ".reg",
})


def _classify_file(name):
    """Whitelist verdict for one top-level package file -> (code, why) | (None, '')."""
    if set(name) <= {"."} or ".." in name:
        return "file_forbidden", "dot-segment names are not safe basenames"
    if name in PACKAGE_FILES:
        return None, ""
    low = name.lower()
    if low in _PACKAGE_NAMES_LOWER:
        return "file_forbidden", "case-variant of a package file name breaks on Windows"
    if low in _FORBIDDEN_NAMES_LOWER:
        return "file_forbidden", "protocol payload that must not travel inside a package"
    ext = low[low.rfind("."):] if "." in low else ""
    if ext in _IMAGE_EXT:
        return "file_forbidden", "image bytes never travel inside a package"
    if ext in _EXEC_EXT:
        return "file_forbidden", "executable/script content is not package data"
    return "file_unexpected", "not one of the three raw package files"


def _parse_json_file(data, label, max_bytes, schema, prefix, errors):
    """Size limit + strict JSON + schema for one document file.

    Appends errors and returns (parsed_object, n_schema_errors); parsed_object is
    None when the size limit or strict-JSON read failed.
    """
    if len(data) > max_bytes:
        errors.append(("size_limit_exceeded",
                       f"{prefix}{label} is {len(data)} bytes (limit {max_bytes})"))
        return None, 0
    try:
        obj = read_json_bytes(data)
    except ContractDataError as e:
        errors.append((e.code, f"{prefix}{label}: {e.detail}"))
        return None, 0
    schema_errors = validate(obj, schema)
    for code, detail in schema_errors:
        errors.append((code, f"{prefix}{label} {detail}"))
    return obj, len(schema_errors)


def _parse_records_file(data, prefix, errors):
    """Size limit + JSONL framing; returns the record list or None."""
    if len(data) > MAX_RECORDS_BYTES:
        errors.append(("size_limit_exceeded",
                       f"{prefix}records.jsonl is {len(data)} bytes "
                       f"(limit {MAX_RECORDS_BYTES})"))
        return None
    try:
        records = read_jsonl_bytes(data)
    except ContractDataError as e:
        errors.append((e.code, f"{prefix}records.jsonl: {e.detail}"))
        return None
    if len(records) > MAX_RECORD_COUNT:
        errors.append(("size_limit_exceeded",
                       f"{prefix}records.jsonl holds {len(records)} records "
                       f"(limit {MAX_RECORD_COUNT})"))
    return records


def _manifest_sequence(pkg_dir):
    """Best-effort manifest.sequence read for the sequence layer; None when unreadable."""
    try:
        obj = read_json_bytes((pkg_dir / "manifest.json").read_bytes())
    except (ContractDataError, OSError):
        return None
    if not isinstance(obj, dict):
        return None
    seq = obj.get("sequence")
    return seq if isinstance(seq, int) and not isinstance(seq, bool) else None


def _check_package_dir(pkg_dir, ctx, prefix="", ignore=frozenset()):
    """Run every package-envelope check on one directory.

    ctx keys (all optional): consumer_id, expected_sequence, previously_imported.
    `ignore` holds relative paths (e.g. case.json at the case root) that are not
    package content.
    """
    pkg_dir = Path(pkg_dir)
    errors = []

    # --- inventory: flat whitelist, forbidden names, nested paths -------------
    present = {}
    for path in sorted(p for p in pkg_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(pkg_dir).as_posix()
        if rel in ignore:
            continue
        if "/" in rel:
            errors.append(("file_forbidden",
                           f"{prefix}{rel}: package files must be flat (no directories)"))
            continue
        present[rel] = path.read_bytes()
        code, why = _classify_file(rel)
        if code:
            errors.append((code, f"{prefix}{rel}: {why}"))
    for entry in sorted(pkg_dir.iterdir(), key=lambda e: e.name):
        if entry.is_dir():
            errors.append(("file_forbidden",
                           f"{prefix}{entry.name}/: directories are not allowed "
                           "inside a package"))
    for name in PACKAGE_FILES:
        if name not in present:
            errors.append(("file_missing",
                           f"{prefix}{name}: required package file is absent"))

    # --- parse the three documents -------------------------------------------
    manifest_bytes = present.get("manifest.json")
    manifest_raw = manifest = None
    if manifest_bytes is not None:
        manifest_raw, n_err = _parse_json_file(
            manifest_bytes, "manifest.json", MAX_MANIFEST_BYTES,
            MANIFEST_SCHEMA, prefix, errors)
        if isinstance(manifest_raw, dict) and n_err == 0:
            manifest = manifest_raw

    records = None
    if "records.jsonl" in present:
        records = _parse_records_file(present["records.jsonl"], prefix, errors)

    ready = None
    if "READY.json" in present:
        ready_raw, n_err = _parse_json_file(
            present["READY.json"], "READY.json", MAX_READY_BYTES,
            READY_SCHEMA, prefix, errors)
        if isinstance(ready_raw, dict) and n_err == 0:
            ready = ready_raw

    # --- manifest-driven checks (only on a schema-valid manifest) -------------
    if manifest is not None:
        declared = set()
        for entry in manifest["files"]:
            path = entry["path"]
            if path not in DECLARABLE:
                errors.append(("file_forbidden",
                               f"{prefix}manifest.json files[] entry {path!r}: "
                               "only records.jsonl may be declared"))
                continue
            declared.add(path)
            data = present.get(path)
            if data is None:
                errors.append(("file_missing",
                               f"{prefix}{path}: declared in manifest but absent "
                               "from the package"))
                continue
            if sha256_hex(data) != entry["sha256"]:
                errors.append(("manifest_hash_mismatch",
                               f"{prefix}{path}: sha256 does not match manifest"))
            if len(data) != entry["bytes"]:
                errors.append(("size_mismatch",
                               f"{prefix}{path}: manifest declares {entry['bytes']} "
                               f"bytes, file holds {len(data)}"))
        for name in DECLARABLE:
            if name in present and name not in declared:
                errors.append(("file_unexpected",
                               f"{prefix}{name}: on disk but not declared in "
                               "manifest files[]"))
        if records is not None and manifest["record_count"] != len(records):
            errors.append(("record_count_mismatch",
                           f"{prefix}manifest record_count is "
                           f"{manifest['record_count']} but records.jsonl has "
                           f"{len(records)} lines"))
        consumer_id = ctx.get("consumer_id")
        if consumer_id is not None and manifest["consumer_id"] != consumer_id:
            errors.append(("consumer_mismatch",
                           f"{prefix}manifest consumer_id "
                           f"{manifest['consumer_id']} != expected {consumer_id}"))
        if manifest["producer"].get("service") != "zalo-intake":
            errors.append(("producer_mismatch",
                           f"{prefix}producer.service is "
                           f"{manifest['producer'].get('service')!r}, "
                           "expected 'zalo-intake'"))
        expected = ctx.get("expected_sequence")
        if expected is not None and manifest["sequence"] != expected:
            errors.append(("sequence_invalid",
                           f"{prefix}manifest sequence is {manifest['sequence']}, "
                           f"expected {expected}"))
        for prev in ctx.get("previously_imported") or []:
            if not isinstance(prev, dict):
                continue
            if prev.get("package_id") == manifest["package_id"] \
                    and prev.get("manifest_sha256") != sha256_hex(manifest_bytes):
                errors.append(("package_conflict",
                               f"{prefix}package_id {manifest['package_id']} was "
                               "already imported under a different manifest hash"))

    # --- READY binds the manifest bytes (independent of manifest validity) ----
    if ready is not None and manifest_bytes is not None:
        if ready["manifest_sha256"] != sha256_hex(manifest_bytes):
            errors.append(("ready_hash_mismatch",
                           f"{prefix}READY.json manifest_sha256 does not equal "
                           "sha256(manifest.json)"))
        elif isinstance(manifest_raw, dict) \
                and manifest_raw.get("package_id") is not None \
                and ready["package_id"] != manifest_raw["package_id"]:
            errors.append(("ready_hash_mismatch",
                           f"{prefix}READY.json package_id does not match "
                           "manifest.json package_id"))

    return errors


@register("package")
def check_package(case_dir, case):
    ctx = case.get("context") or {}
    pkg_ctx = {
        "consumer_id": ctx.get("consumer_id"),
        "expected_sequence": ctx.get("expected_sequence"),
        "previously_imported": ctx.get("previously_imported"),
    }
    return _check_package_dir(case_dir, pkg_ctx, ignore=frozenset({"case.json"}))


@register("package_sequence")
def check_package_sequence(case_dir, case):
    """package_* subdirs in name order; each must be a valid package and their
    sequences must run consecutively from context.expected_start (or from the
    first package's own sequence when the context omits it)."""
    case_dir = Path(case_dir)
    ctx = case.get("context") or {}
    errors = []

    pkg_dirs = sorted((d for d in case_dir.iterdir()
                       if d.is_dir() and d.name.startswith("package_")),
                      key=lambda d: d.name)
    for entry in sorted(case_dir.iterdir(), key=lambda e: e.name):
        if entry.name == "case.json" or entry in pkg_dirs:
            continue
        kind = "directory" if entry.is_dir() else "file"
        errors.append(("file_unexpected",
                       f"{entry.name}: unexpected {kind} in a package_sequence case"))

    sub_ctx = {
        "consumer_id": ctx.get("consumer_id"),
        "previously_imported": ctx.get("previously_imported"),
    }
    sequences = []
    for d in pkg_dirs:
        errors += _check_package_dir(d, sub_ctx, prefix=f"{d.name}/")
        sequences.append(_manifest_sequence(d))

    expected = ctx.get("expected_start")
    if expected is None:
        expected = sequences[0] if sequences and sequences[0] is not None else 1
    for i, (d, seq) in enumerate(zip(pkg_dirs, sequences)):
        want = expected + i
        if seq != want:
            errors.append(("sequence_invalid",
                           f"{d.name}/manifest.json sequence is {seq!r}, "
                           f"expected {want}"))

    return errors

"""Raw-record validation for packaging — contract §5 + §11.3.

Every record destined for ``records.jsonl`` is checked against the vendored
``schemas/raw-record.schema.json`` with the contract's own schema engine
(``delivery._schema``) — the same validator the consumer side runs — plus the
forbidden-content rules of §11.3 that a JSON Schema cannot express
(``image_payload_forbidden`` / ``provider_payload_forbidden``).

``validate_record(payload) -> list[str]`` returns the sorted set of contract
error codes; an empty list means the record may be sealed into a package.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from zalo_module.delivery._schema import load_schema, validate

# Repo-rooted vendored schemas (byte-identical to contracts/zalo-intake/*).
# Overridable for packaged deployments where the schemas dir lives elsewhere.
_SCHEMAS_DIR = Path(
    os.environ.get("ZALO_INTAKE_SCHEMAS_DIR")
    or (Path(__file__).resolve().parents[3] / "schemas")
)

_record_schema = None


def _schema():
    global _record_schema
    if _record_schema is None:
        _record_schema = load_schema(_SCHEMAS_DIR / "raw-record.schema.json")
    return _record_schema


# --- §11.3 forbidden-content scan --------------------------------------------

_PROVIDER_DUMP_KEYS = frozenset(
    {"provider_raw", "provider_response", "raw_response"}
)
_IMAGE_DOC_EXT = r"(?:jpe?g|png|webp|pdf)"
_RE_DATA_IMAGE = re.compile(r"data:\s*image", re.I)
# whitespace-free token ending in an image/document extension
_RE_IMAGE_DOC_REF = re.compile(
    r"\S+\." + _IMAGE_DOC_EXT + r"(?:[?#]\S*)?(?=\s|$)", re.I
)
# long unbroken base64-alphabet run (>=128 chars) = smuggled payload bytes
_RE_B64_BLOB = re.compile(r"[A-Za-z0-9+/]{128,}={0,3}")


def _scan_forbidden(node, out: set) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in _PROVIDER_DUMP_KEYS:
                out.add("provider_payload_forbidden")
            _scan_forbidden(value, out)
    elif isinstance(node, list):
        for value in node:
            _scan_forbidden(value, out)
    elif isinstance(node, str):
        if _RE_DATA_IMAGE.search(node) or _RE_IMAGE_DOC_REF.search(node):
            out.add("image_payload_forbidden")
        elif _RE_B64_BLOB.search(node):
            out.add("image_payload_forbidden")


def forbidden_codes(payload) -> set:
    """Contract §11.3 forbidden-content codes found anywhere in ``payload``."""
    out: set = set()
    _scan_forbidden(payload, out)
    return out


def validate_record(payload) -> list:
    """Schema + forbidden-content check; returns sorted contract error codes."""
    if not isinstance(payload, dict):
        return ["schema_invalid"]
    codes = {code for code, _detail in validate(payload, _schema())}
    codes |= forbidden_codes(payload)
    return sorted(codes)

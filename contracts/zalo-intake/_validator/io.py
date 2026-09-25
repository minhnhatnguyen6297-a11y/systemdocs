"""Byte-exact helpers: documents are handled as bytes, never through text-mode files.

Text-mode writes would turn "\\n" into "\\r\\n" on Windows (this repo also has
core.autocrlf=true), which changes hashes and breaks the JSONL framing rules.
"""
import codecs
import hashlib
import json
import math
from pathlib import Path

JSON_INVALID = "json_invalid"
RECORDS_FORMAT_INVALID = "records_format_invalid"


class ContractDataError(Exception):
    """Document bytes break the contract's byte/JSON rules; `code` is a stable error code."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


def _unique_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ContractDataError(JSON_INVALID, f"duplicate object key {json.dumps(key)}")
        obj[key] = value
    return obj


def _no_constant(token):
    raise ContractDataError(JSON_INVALID, f"non-finite number {token}")


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ContractDataError(JSON_INVALID, "non-finite number (overflow)")
    return value


def _loads(text: str, syntax_code: str, line: int | None = None):
    """json.loads with the strict profile (unique keys, finite numbers); `line` = JSONL line number."""
    try:
        return json.loads(text, object_pairs_hook=_unique_keys, parse_constant=_no_constant,
                          parse_float=_finite_float)
    except json.JSONDecodeError as e:
        raise ContractDataError(syntax_code, f"line {line or e.lineno} column {e.colno}: {e.msg}") from None
    except ContractDataError as e:
        if line is None:
            raise
        raise ContractDataError(e.code, f"line {line}: {e.detail}") from None


def read_json_bytes(data: bytes):
    """Parse one JSON document: UTF-8 without BOM, unique keys, no NaN/Infinity, no trailing data."""
    if data.startswith(codecs.BOM_UTF8):
        raise ContractDataError(JSON_INVALID, "UTF-8 BOM is not allowed")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ContractDataError(JSON_INVALID, f"invalid UTF-8 at byte {e.start}") from None
    return _loads(text, JSON_INVALID)


def _records_error(line: int, why: str) -> ContractDataError:
    return ContractDataError(RECORDS_FORMAT_INVALID, f"line {line}: {why}")


def read_jsonl_bytes(data: bytes) -> list:
    """Parse JSON Lines: UTF-8 without BOM, every line (the last too) ends with "\\n", no "\\r",
    no empty line, each line exactly one JSON object. An empty file has no records.

    Framing violations, including a line that is not exactly one JSON value, raise
    records_format_invalid; duplicate keys or NaN/Infinity inside a line raise json_invalid.
    Details start with "line N" (1-based).
    """
    if data.startswith(codecs.BOM_UTF8):
        raise _records_error(1, "UTF-8 BOM is not allowed")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise _records_error(data.count(b"\n", 0, e.start) + 1, "invalid UTF-8") from None
    if "\r" in text:
        raise _records_error(text.count("\n", 0, text.index("\r")) + 1, "carriage return is not allowed")
    lines = text.split("\n")
    if lines[-1]:
        raise _records_error(len(lines), "missing final newline")
    records = []
    for number, line in enumerate(lines[:-1], 1):
        if not line:
            raise _records_error(number, "empty line")
        value = _loads(line, RECORDS_FORMAT_INVALID, number)
        if not isinstance(value, dict):
            raise _records_error(number, "not a JSON object")
        records.append(value)
    return records


def sha256_hex(data: bytes) -> str:
    """Lowercase hex SHA-256 of the exact bytes."""
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(obj) -> str:
    """SHA-256 of the sorted-key, compact, UTF-8 JSON of obj (Python json, not RFC 8785)."""
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return sha256_hex(text.encode("utf-8"))


def write_bytes_exact(path, data: bytes) -> None:
    """Authoring helper: write exactly these bytes (creating parent folders)."""
    if not isinstance(data, bytes):
        raise TypeError("write_bytes_exact takes bytes; encode text explicitly")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

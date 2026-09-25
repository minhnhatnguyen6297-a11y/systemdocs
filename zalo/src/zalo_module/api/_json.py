"""Strict JSON body profile — contract §4 byte rules for API documents.

Rejects: UTF-8 BOM, invalid UTF-8, duplicate object keys at any depth,
``NaN``/``Infinity``/``-Infinity`` literals and trailing data after the JSON
value. Any violation raises :class:`StrictJsonError`; the endpoint maps it to
the ``intake.error.v1`` envelope with code ``json_invalid`` (HTTP 400).
"""

from __future__ import annotations

import json


class StrictJsonError(ValueError):
    """Contract §4 violation on a request body."""


def _reject_constant(name: str):
    raise StrictJsonError(f"non-finite literal {name!r}")


def _object_no_dupes(pairs: list) -> dict:
    obj: dict = {}
    for key, value in pairs:
        if key in obj:
            raise StrictJsonError(f"duplicate object key {key!r}")
        obj[key] = value
    return obj


def parse_strict_body(raw: bytes):
    """Parse one JSON document under the strict profile; return the value."""
    if raw.startswith(b"\xef\xbb\xbf"):
        raise StrictJsonError("body starts with a UTF-8 BOM")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StrictJsonError("body is not valid UTF-8") from exc
    try:
        return json.loads(
            text,
            parse_constant=_reject_constant,
            object_pairs_hook=_object_no_dupes,
        )
    except json.JSONDecodeError as exc:
        raise StrictJsonError(f"not a single JSON document: {exc}") from exc


__all__ = ["StrictJsonError", "parse_strict_body"]

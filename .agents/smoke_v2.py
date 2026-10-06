# -*- coding: utf-8 -*-
"""Smoke check v2 engine with real ledger; output to file (shell mangles input)."""
from notary_v2.services.administrative_address import (
    lookup_address, _has_diacritics, expand_abbreviation, split_query,
)
import unicodedata

QUERIES = [
    "x\u00e3 Y\u00ean B\u00ecnh",          # xa Yen Binh (diacritic)
    "yen binh",                            # undiacritic
    "P. yen binh",                         # abbrev + undiacritic
    "P. y\u00ean b\u00ecnh",               # abbrev + diacritic
    "t\u1ec9nh Nam \u0110\u1ecbnh",        # tinh Nam Dinh (diacritic)
    "huy\u1ec7n \u00dd Y\u00ean",          # huyen Y Yen
    "abcxyz123",
    "  , - ,",
    "",
    "x" * 4001,
]

lines = []
for q in QUERIES:
    nfc = unicodedata.normalize("NFC", q) if q else q
    try:
        hd = _has_diacritics(nfc) if q else "-"
    except Exception as exc:  # noqa: BLE001
        hd = repr(exc)
    r = lookup_address({"query": q, "presentation": "drafting"})
    lines.append(f"Q={q[:24]!r} has_diac={hd} -> {r['status']} total={r['total']}")
    for row in r["results"][:3]:
        lines.append("    " + row["display"])
    lines.append(f"    schema={r['schema_version']} pres={r['presentation']}")

# invalid shapes
for payload in [
    {"query": "yen binh", "presentation": "drafting", "source_date": "2020"},
    {"query": "", "presentation": "drafting"},
    {"query": "yen binh", "presentation": "bogus"},
    {"query": 123, "presentation": "drafting"},
]:
    r = lookup_address(payload)
    lines.append(f"P={str(payload)[:60]!r} -> {r['status']} pres={r['presentation']} total={r['total']}")

# full over threshold
r = lookup_address({"query": "yen binh", "presentation": "full"})
lines.append(f"FULL yen binh -> {r['status']} total={r['total']} n={len(r['results'])}")
for row in r["results"][:3]:
    lines.append("    " + row["display"][:120])

with open("C:/Users/MINH/AppData/Local/Temp/opencode/r3.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("wrote", len(lines), "lines")

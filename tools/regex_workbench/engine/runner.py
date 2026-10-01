"""Runner: nạp profile JSON và chạy pipeline zoning -> extraction.

Pipeline: raw input -> normalize (kèm char_ranges) -> fold (kèm fold_map)
-> span_of (folded -> raw) -> title/kind -> zones -> fields + parties.
Mọi span trả về trỏ vào văn bản nguồn người dùng nhập; `regex_timeout_ms`
áp cho MỌI regex do profile điều khiển (title kind_rules, zone markers,
field rules, side markers, person delimiter/fields, validators).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .extractor import (
    DEFAULT_REGEX_TIMEOUT_MS,
    extract_fields,
    extract_parties,
    lint_pattern,
)
from .textnorm import (
    fold_with_index_map,
    make_span_mapper,
    normalize_with_index_map,
)
from .zoner import detect_title, find_zones, fold_lines

PROFILES_DIR = Path(__file__).resolve().parent / "profiles"
DEFAULT_PROFILE = "transfer"


def load_profile(source: str | Path | dict) -> dict[str, Any]:
    """Nạp profile từ tên (trong profiles/), đường dẫn file, hoặc dict."""
    if isinstance(source, dict):
        return source
    path = Path(str(source))
    if not path.suffix:
        path = PROFILES_DIR / f"{source}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def validate_profile(profile: Any) -> list[str]:
    """Kiểm tra CẤU TRÚC profile (shape) trước khi lint/run.

    Profile là JSON hợp lệ nhưng sai kiểu (vd `fields: null`, `zones` là
    string, `title` là list) từng làm engine ném exception ngầm. Trả về
    danh sách lỗi — rỗng nghĩa là shape đủ dùng. Đây là contract cho cả
    `run()` lẫn HTTP layer (`serve.py` trả 400 khi problems không rỗng).
    """
    if not isinstance(profile, dict):
        return ["profile phải là object JSON (dict)"]

    problems: list[str] = []

    def _check_list(owner: str, value: Any) -> None:
        if not isinstance(value, list):
            problems.append(f"'{owner}' phải là list, nhận {type(value).__name__}")

    def _check_dict(owner: str, value: Any) -> None:
        if not isinstance(value, dict):
            problems.append(f"'{owner}' phải là object, nhận {type(value).__name__}")

    if "title" in profile:
        _check_dict("title", profile["title"])
    title = profile.get("title")
    if isinstance(title, dict):
        if "kind_rules" in title:
            _check_list("title.kind_rules", title["kind_rules"])
        for i, kr in enumerate(title.get("kind_rules") or []):
            _check_dict(f"title.kind_rules[{i}]", kr)

    if "zones" in profile:
        _check_list("zones", profile["zones"])
    for i, zone in enumerate(profile.get("zones") or []):
        if not isinstance(zone, dict):
            problems.append(f"zones[{i}] phải là object, nhận {type(zone).__name__}")
            continue
        if "start_markers" in zone:
            _check_list(f"zones[{i}].start_markers", zone["start_markers"])
        if "end_markers" in zone:
            _check_list(f"zones[{i}].end_markers", zone["end_markers"])

    if "fields" in profile:
        _check_list("fields", profile["fields"])
    for i, rule in enumerate(profile.get("fields") or []):
        if not isinstance(rule, dict):
            problems.append(f"fields[{i}] phải là object, nhận {type(rule).__name__}")
            continue
        if "validators" in rule:
            _check_list(f"fields[{i}].validators", rule["validators"])

    if "parties" in profile:
        _check_dict("parties", profile["parties"])
    parties = profile.get("parties")
    if isinstance(parties, dict):
        if "side_markers" in parties:
            _check_list("parties.side_markers", parties["side_markers"])
        if "person_delimiter" in parties:
            _check_dict("parties.person_delimiter", parties["person_delimiter"])
        if "person_fields" in parties:
            _check_list("parties.person_fields", parties["person_fields"])

    if "regex_timeout_ms" in profile and not isinstance(
        profile["regex_timeout_ms"], (int, float)
    ):
        problems.append("'regex_timeout_ms' phải là số (ms)")

    return problems


def lint_profile(profile: dict[str, Any]) -> list[str]:
    """Kiểm tra tĩnh toàn bộ pattern trong profile trước khi chạy."""
    problems: list[str] = []
    title = profile.get("title")
    for rule in ((title or {}).get("kind_rules") or []) if isinstance(title, dict) else []:
        if not isinstance(rule, dict):
            continue
        msg = lint_pattern(str(rule.get("rule_id", "title.rule")), str(rule.get("pattern", "")))
        if msg:
            problems.append(msg)
    for zone in profile.get("zones") or []:
        if not isinstance(zone, dict):
            continue
        zone_id = str(zone.get("zone_id", "?"))
        for marker in (*(zone.get("start_markers") or []), *(zone.get("end_markers") or [])):
            msg = lint_pattern(f"zone.{zone_id}", str(marker))
            if msg:
                problems.append(msg)
    for rule in profile.get("fields") or []:
        if not isinstance(rule, dict):
            continue
        msg = lint_pattern(str(rule.get("rule_id", "field.?")), str(rule.get("pattern", "")))
        if msg:
            problems.append(msg)
        for validator in rule.get("validators") or []:
            vmsg = lint_pattern(
                str(validator.get("rule_id") or rule.get("rule_id", "field.?")),
                str(validator.get("pattern", "")),
            )
            if vmsg:
                problems.append(vmsg)
    pcfg = profile.get("parties") or {}
    if not isinstance(pcfg, dict):
        return problems
    for marker in pcfg.get("side_markers") or []:
        if not isinstance(marker, dict):
            continue
        msg = lint_pattern(str(marker.get("rule_id", "party.side")), str(marker.get("pattern", "")))
        if msg:
            problems.append(msg)
    delim = pcfg.get("person_delimiter") or {}
    if delim.get("pattern"):
        msg = lint_pattern(str(delim.get("rule_id", "party.person")), str(delim.get("pattern", "")))
        if msg:
            problems.append(msg)
    for frule in pcfg.get("person_fields") or []:
        if not isinstance(frule, dict):
            continue
        msg = lint_pattern(str(frule.get("rule_id", "person.?")), str(frule.get("pattern", "")))
        if msg:
            problems.append(msg)
    return problems


def run(text: str, profile: dict[str, Any]) -> dict[str, Any]:
    """Chạy pipeline đầy đủ: normalize -> title/kind -> zones -> fields+parties."""
    raw = str(text or "")
    timeout_ms = int(profile.get("regex_timeout_ms", DEFAULT_REGEX_TIMEOUT_MS))

    normalized, char_ranges = normalize_with_index_map(raw)
    folded, fold_map = fold_with_index_map(normalized)
    span_of = make_span_mapper(fold_map, char_ranges)

    # folded_lines cho detect_title: offset quy về raw ngay tại đây để
    # title span/raw_snippet trỏ đúng văn bản nguồn người dùng nhập.
    folded_lines_raw = [
        (char_ranges[s][0], char_ranges[e - 1][1], folded_line)
        for s, e, folded_line in fold_lines(normalized)
    ]

    errors: list[str] = []
    title = detect_title(raw, folded_lines_raw, profile, timeout_ms, errors)
    zones = find_zones(raw, folded, span_of, profile, timeout_ms, errors)
    fields = extract_fields(raw, folded, span_of, zones, profile, timeout_ms, errors)
    parties = extract_parties(raw, folded, span_of, zones, profile, timeout_ms, errors)

    return {
        "profile_id": profile.get("profile_id"),
        "profile_version": profile.get("version"),
        "doc_kind": title["kind"],
        "title": {
            "value": title["title"],
            "state": title["state"],
            "span": title["span"],
            "raw_snippet": title["raw_snippet"],
            "rule_id": title["rule_id"],
            "note": title.get("note"),
        },
        "zones": zones,
        "fields": fields,
        "parties": parties,
        "errors": errors,
    }

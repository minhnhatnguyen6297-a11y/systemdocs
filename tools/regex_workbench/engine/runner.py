"""Runner: nạp profile JSON và chạy pipeline zoning -> extraction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .extractor import extract_fields, extract_parties, lint_pattern
from .textnorm import fold_with_index_map, normalize_text
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


def lint_profile(profile: dict[str, Any]) -> list[str]:
    """Kiểm tra tĩnh toàn bộ pattern trong profile trước khi chạy."""
    problems: list[str] = []
    for rule in (profile.get("title", {}) or {}).get("kind_rules", []):
        msg = lint_pattern(str(rule.get("rule_id", "title.rule")), str(rule.get("pattern", "")))
        if msg:
            problems.append(msg)
    for zone in profile.get("zones", []):
        zone_id = str(zone.get("zone_id", "?"))
        for marker in (*zone.get("start_markers", []), *zone.get("end_markers", [])):
            msg = lint_pattern(f"zone.{zone_id}", str(marker))
            if msg:
                problems.append(msg)
    for rule in profile.get("fields", []):
        msg = lint_pattern(str(rule.get("rule_id", "field.?")), str(rule.get("pattern", "")))
        if msg:
            problems.append(msg)
    pcfg = profile.get("parties") or {}
    for marker in pcfg.get("side_markers", []):
        msg = lint_pattern(str(marker.get("rule_id", "party.side")), str(marker.get("pattern", "")))
        if msg:
            problems.append(msg)
    delim = pcfg.get("person_delimiter") or {}
    if delim.get("pattern"):
        msg = lint_pattern(str(delim.get("rule_id", "party.person")), str(delim.get("pattern", "")))
        if msg:
            problems.append(msg)
    for frule in pcfg.get("person_fields", []):
        msg = lint_pattern(str(frule.get("rule_id", "person.?")), str(frule.get("pattern", "")))
        if msg:
            problems.append(msg)
    return problems


def run(text: str, profile: dict[str, Any]) -> dict[str, Any]:
    """Chạy pipeline đầy đủ: normalize -> title/kind -> zones -> fields+parties."""
    normalized = normalize_text(text)
    folded, index_map = fold_with_index_map(normalized)
    folded_line_list = fold_lines(normalized)

    title = detect_title(normalized, folded_line_list, profile)
    zones = find_zones(normalized, folded, index_map, profile)
    fields, errors = extract_fields(normalized, folded, index_map, zones, profile)
    parties = extract_parties(normalized, folded, index_map, zones, profile)

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
        },
        "zones": zones,
        "fields": fields,
        "parties": parties,
        "errors": errors,
    }

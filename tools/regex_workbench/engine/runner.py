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
from .extractor import _guarded_finditer
import regex

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
    if "asset_groups" in profile:
        cfg = profile["asset_groups"]
        if not isinstance(cfg, dict) or not isinstance(cfg.get("delimiter"), str):
            problems.append("asset_groups phải là object có delimiter string")
        elif "land_rows" in cfg:
            rows = cfg["land_rows"]
            if not isinstance(rows, dict) or not isinstance(rows.get("delimiter"), str) or not isinstance(rows.get("fields"), list):
                problems.append("asset_groups.land_rows cần delimiter và fields")
            else:
                for i, rule in enumerate(rows["fields"]):
                    owner = f"asset_groups.land_rows.fields[{i}]"
                    if not isinstance(rule, dict):
                        problems.append(f"{owner} phải là object")
                        continue
                    for key in ("name", "rule_id", "pattern"):
                        if not isinstance(rule.get(key), str) or not rule[key]:
                            problems.append(f"{owner}.{key} phải là string không rỗng")
                    if "group" in rule and (isinstance(rule["group"], bool) or not isinstance(rule["group"], (int, str))):
                        problems.append(f"{owner}.group phải là số hoặc tên nhóm")

    return problems


def lint_profile(profile: dict[str, Any]) -> list[str]:
    """Kiểm tra tĩnh toàn bộ pattern trong profile trước khi chạy."""
    problems = validate_profile(profile)
    if problems:
        return problems
    cfg = profile.get("asset_groups") or {}
    if isinstance(cfg, dict):
        for owner, group in (("asset.groups", cfg), ("asset.land_rows", cfg.get("land_rows") or {})):
            if group.get("delimiter"):
                msg = lint_pattern(owner, group["delimiter"])
                if msg:
                    problems.append(msg)
            for rule in group.get("fields", []):
                msg = lint_pattern(rule.get("rule_id", owner), rule.get("pattern", ""))
                if msg:
                    problems.append(msg)
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
    groups = []
    cfg = profile.get("asset_groups") or {}
    if cfg:
        pattern = str(cfg.get("delimiter", ""))
        problem = lint_pattern("asset.groups", pattern)
        if problem:
            errors.append(problem)
        else:
            matches, problem = _guarded_finditer(regex.compile(pattern, regex.MULTILINE), folded, timeout_ms)
            if problem:
                errors.append("asset.groups: " + problem)
            else:
                asset_zone = next((z for z in zones if z.get("name") == "asset" and z.get("fold_span")), None)
                starts = [m.start() for m in matches or []]
                if not starts and asset_zone:
                    starts = [asset_zone["fold_span"][0]]
                if not starts:
                    starts = [0]  # A standalone certificate still uses the same field rules.
                end = (asset_zone["fold_span"][1] if asset_zone else len(folded))
                starts = [start for start in starts if start < end]
                for i, start in enumerate(starts):
                    stop = min(starts[i + 1], end) if i + 1 < len(starts) else end
                    if stop <= start:
                        continue
                    group_zone = [{"name": "asset", "state": "matched", "fold_span": [start, stop]}]
                    results = extract_fields(raw, folded, span_of, group_zone,
                                             {"fields": [r for r in profile.get("fields", []) if r.get("zone") == "asset"]},
                                             timeout_ms, errors)
                    land_rows = []
                    land_cfg = cfg.get("land_rows") or {}
                    if land_cfg:
                        row_pattern = str(land_cfg.get("delimiter", ""))
                        problem = lint_pattern("asset.land_rows", row_pattern)
                        if not problem:
                            row_matches, problem = _guarded_finditer(regex.compile(row_pattern, regex.MULTILINE), folded[start:stop], timeout_ms)
                            for j, row_match in enumerate(row_matches or []):
                                row_start = start + row_match.start()
                                row_stop = start + row_matches[j + 1].start() if j + 1 < len(row_matches) else stop
                                land_rows.append(extract_fields(raw, folded, span_of,
                                        [{"name": "land_row", "state": "matched", "fold_span": [row_start, row_stop]}],
                                        {"fields": [{**r, "zone": "land_row"} for r in land_cfg.get("fields", [])]}, timeout_ms, errors))
                        if problem:
                            errors.append("asset.land_rows: " + problem)
                    groups.append({"span": list(span_of(start, stop)), "fields": results,
                                   "land_rows": land_rows, "state": "matched" if matches else "ambiguous_group"})

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
        "asset_groups": groups,
        "errors": errors,
    }

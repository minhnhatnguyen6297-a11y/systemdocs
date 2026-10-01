"""Field extraction second: khớp regex bên trong từng vùng cô lập.

Mọi trường trích xuất trả về provenance đầy đủ: span [start, end] trên
văn bản gốc, raw_snippet và rule_id. Pattern chạy trên văn bản đã fold
(lowercase, không dấu) nên regex trong profile viết dạng folded; giá trị
và snippet luôn cắt từ văn bản gốc theo index map.

Regex lỗi hoặc chạy quá timeout được báo rõ bằng state `error`, không
nuốt lỗi lặng lẽ.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any

from .model import (
    STATE_AMBIGUOUS,
    STATE_ERROR,
    STATE_MATCHED,
    STATE_MISSING,
    STATE_WARNING,
    make_span_result,
)
from .textnorm import map_span

DEFAULT_REGEX_TIMEOUT_MS = 1000

# Heuristic ReDoS: nhóm chứa quantifier rồi lại được lặp — vd (a+)+, (.*)*.
_NESTED_QUANTIFIER = re.compile(r"\([^()]*[*+][^()]*\)\s*[*+{]")


def lint_pattern(rule_id: str, pattern: str) -> str | None:
    """Kiểm tra tĩnh một pattern: lỗi cú pháp hoặc nguy cơ backtracking."""
    try:
        re.compile(pattern)
    except re.error as exc:
        return f"{rule_id}: regex không hợp lệ — {exc}"
    if _NESTED_QUANTIFIER.search(pattern):
        return f"{rule_id}: nested quantifier, nguy cơ catastrophic backtracking"
    return None


def _guarded_finditer(
    compiled: re.Pattern,
    folded_scope: str,
    timeout_ms: int,
) -> tuple[list[re.Match] | None, str | None]:
    """Chạy finditer với timeout best-effort.

    Python re không hủy được giữa chừng; khi quá hạn ta báo lỗi rõ cho rule
    và bỏ qua kết quả (thread nền tự kết thúc). Đủ cho dev tool địa phương.
    """
    if timeout_ms <= 0:
        return list(compiled.finditer(folded_scope)), None
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(lambda: list(compiled.finditer(folded_scope)))
    try:
        return future.result(timeout=timeout_ms / 1000.0), None
    except FuturesTimeout:
        return None, f"timeout sau {timeout_ms}ms"
    finally:
        executor.shutdown(wait=False)


def _match_value(match: re.Match, group) -> tuple[int, int] | None:
    try:
        span = match.span(group)
    except IndexError:
        return None
    if span == (-1, -1):
        return None
    return span


def _apply_validators(rule: dict, raw_value: str, state: str) -> tuple[str, list[dict]]:
    """Chạy validators trên giá trị raw; trả về (state, warnings)."""
    warnings: list[dict] = []
    final_state = state
    for validator in rule.get("validators", []):
        vpattern = str(validator.get("pattern", ""))
        try:
            ok = bool(re.search(vpattern, raw_value))
        except re.error as exc:
            warnings.append({"rule_id": rule.get("rule_id"), "message": f"validator lỗi: {exc}"})
            continue
        if not ok:
            on_fail = str(validator.get("on_fail", STATE_WARNING))
            warnings.append(
                {
                    "rule_id": rule.get("rule_id"),
                    "message": str(validator.get("message", "giá trị chưa đúng chuẩn")),
                    "on_fail": on_fail,
                }
            )
            final_state = on_fail
    return final_state, warnings


def _render_value(match: re.Match, index_map: list[int], fold_offset: int, source_text: str, rule: dict) -> str:
    """Dựng value từ group hoặc value_template, cắt từ văn bản gốc."""
    template = rule.get("value_template")
    if template:
        parts = {}
        for gidx in range(0, len(match.groups()) + 1):
            gspan = _match_value(match, gidx)
            if gspan is None:
                parts[gidx] = ""
                continue
            mapped = map_span(index_map, fold_offset + gspan[0], fold_offset + gspan[1])
            parts[gidx] = source_text[mapped[0] : mapped[1]] if mapped else ""
        try:
            return str(template).format(*[parts.get(i, "") for i in range(len(match.groups()) + 1)])
        except (IndexError, KeyError):
            return str(template)
    group = rule.get("group", 1)
    gspan = _match_value(match, group)
    if gspan is None:
        return ""
    mapped = map_span(index_map, fold_offset + gspan[0], fold_offset + gspan[1])
    return source_text[mapped[0] : mapped[1]] if mapped else ""


def extract_fields(
    text: str,
    folded: str,
    index_map: list[int],
    zones: list[dict],
    profile: dict[str, Any],
) -> tuple[list[dict], list[str]]:
    """Chạy toàn bộ field rules trong profile theo vùng cô lập."""
    zones_by_id = {z.get("name"): z for z in zones}
    timeout_ms = int(profile.get("regex_timeout_ms", DEFAULT_REGEX_TIMEOUT_MS))
    fields: list[dict] = []
    errors: list[str] = []

    for rule in profile.get("fields", []):
        rule_id = str(rule.get("rule_id", "field.unknown"))
        name = str(rule.get("name", rule_id))
        zone_id = str(rule.get("zone", "any"))

        if zone_id == "any":
            fold_start, fold_end = 0, len(folded)
        else:
            zone = zones_by_id.get(zone_id)
            if not zone or zone.get("state") != STATE_MATCHED or not zone.get("fold_span"):
                fields.append(
                    make_span_result(STATE_MISSING, text, None, rule_id=rule_id, name=name,
                                     note=f"zone '{zone_id}' khong tim thay")
                )
                continue
            fold_start, fold_end = zone["fold_span"]

        lint_msg = lint_pattern(rule_id, str(rule.get("pattern", "")))
        if lint_msg:
            errors.append(lint_msg)
            fields.append(
                make_span_result(STATE_ERROR, text, None, rule_id=rule_id, name=name, note=lint_msg)
            )
            continue

        compiled = re.compile(str(rule.get("pattern", "")), re.MULTILINE)
        scope = folded[fold_start:fold_end]
        matches, timeout_err = _guarded_finditer(compiled, scope, timeout_ms)
        if timeout_err:
            errors.append(f"{rule_id}: {timeout_err}")
            fields.append(
                make_span_result(STATE_ERROR, text, None, rule_id=rule_id, name=name, note=timeout_err)
            )
            continue

        group = rule.get("group", 1)
        hits: list[tuple[tuple[int, int], str]] = []
        for match in matches or []:
            gspan = _match_value(match, group)
            if gspan is None:
                continue
            mapped = map_span(index_map, fold_start + gspan[0], fold_start + gspan[1])
            if not mapped:
                continue
            raw = text[mapped[0] : mapped[1]].strip()
            value = _render_value(match, index_map, fold_start, text, rule)
            hits.append((mapped, value if rule.get("value_template") else raw))

        expect = str(rule.get("expect", "one"))
        if not hits:
            fields.append(
                make_span_result(STATE_MISSING, text, None, rule_id=rule_id, name=name)
            )
            continue

        if expect == "many":
            values = [v for _, v in hits]
            fields.append(
                make_span_result(
                    STATE_MATCHED, text, hits[0][0], rule_id=rule_id, name=name,
                    value=values,
                    candidates=[{"span": list(s), "value": v} for s, v in hits],
                )
            )
            continue

        if len(hits) > 1:
            fields.append(
                make_span_result(
                    STATE_AMBIGUOUS, text, hits[0][0], rule_id=rule_id, name=name,
                    value=hits[0][1],
                    candidates=[{"span": list(s), "value": v} for s, v in hits],
                    note=f"{len(hits)} ket qua kha di",
                )
            )
            continue

        (span, value) = hits[0]
        state, warnings = _apply_validators(rule, value, STATE_MATCHED)
        fields.append(
            make_span_result(state, text, span, rule_id=rule_id, name=name,
                             value=value, warnings=warnings or None)
        )
    return fields, errors


def extract_parties(
    text: str,
    folded: str,
    index_map: list[int],
    zones: list[dict],
    profile: dict[str, Any],
) -> dict:
    """Bóc đương sự trong vùng parties: side markers -> blocks -> persons.

    Mỗi block gắn với một side (A/B) và role (vd "Bên chuyển nhượng",
    "Đồng sử dụng"). Person delimiter cắt từng người trong block; các trường
    con (họ tên, năm sinh, CCCD...) khớp trong chunk của riêng người đó nên
    không bao giờ lẫn sang người khác.
    """
    pcfg = profile.get("parties") or {}
    zones_by_id = {z.get("name"): z for z in zones}
    zone_id = str(pcfg.get("zone", "parties"))
    zone = zones_by_id.get(zone_id)
    if not zone or zone.get("state") != STATE_MATCHED or not zone.get("fold_span"):
        return {"state": STATE_MISSING, "blocks": [], "zone": zone_id}

    fold_start, fold_end = zone["fold_span"]
    scope = folded[fold_start:fold_end]
    timeout_ms = int(profile.get("regex_timeout_ms", DEFAULT_REGEX_TIMEOUT_MS))

    markers: list[tuple[int, int, dict]] = []
    for marker_def in pcfg.get("side_markers", []):
        pattern = str(marker_def.get("pattern", ""))
        rule_id = str(marker_def.get("rule_id", "party.side"))
        lint_msg = lint_pattern(rule_id, pattern)
        if lint_msg:
            return {"state": STATE_ERROR, "blocks": [], "zone": zone_id, "note": lint_msg}
        compiled = re.compile(pattern, re.MULTILINE)
        matches, _ = _guarded_finditer(compiled, scope, timeout_ms)
        for m in matches or []:
            markers.append((m.start(), m.end(), marker_def))
    markers.sort(key=lambda item: item[0])

    if not markers:
        return {"state": STATE_MISSING, "blocks": [], "zone": zone_id}

    delim_cfg = pcfg.get("person_delimiter", {})
    delim_pattern = str(delim_cfg.get("pattern", ""))
    delim_rule_id = str(delim_cfg.get("rule_id", "party.person"))
    lint_msg = lint_pattern(delim_rule_id, delim_pattern)
    if lint_msg:
        return {"state": STATE_ERROR, "blocks": [], "zone": zone_id, "note": lint_msg}
    delim_re = re.compile(delim_pattern, re.MULTILINE)

    person_field_rules = pcfg.get("person_fields", [])
    compiled_fields: list[tuple[dict, re.Pattern]] = []
    for frule in person_field_rules:
        frule_id = str(frule.get("rule_id", f"person.{frule.get('name', '?')}"))
        lint_msg = lint_pattern(frule_id, str(frule.get("pattern", "")))
        if lint_msg:
            return {"state": STATE_ERROR, "blocks": [], "zone": zone_id, "note": lint_msg}
        compiled_fields.append((frule, re.compile(str(frule.get("pattern", "")), re.MULTILINE)))

    blocks: list[dict] = []
    for idx, (m_start, m_end, marker_def) in enumerate(markers):
        block_end = markers[idx + 1][0] if idx + 1 < len(markers) else len(scope)
        block_scope = scope[m_start:block_end]
        block_orig = map_span(index_map, fold_start + m_start, fold_start + block_end)

        persons: list[dict] = []
        delimiters = list(delim_re.finditer(block_scope))
        for pidx, dmatch in enumerate(delimiters):
            p_start = dmatch.start()
            p_end = delimiters[pidx + 1].start() if pidx + 1 < len(delimiters) else len(block_scope)
            chunk = block_scope[p_start:p_end]
            chunk_fold_abs = fold_start + m_start + p_start
            person_orig = map_span(index_map, chunk_fold_abs, chunk_fold_abs + len(chunk))

            person_fields: dict[str, dict] = {}
            for frule, fcompiled in compiled_fields:
                fname = str(frule.get("name", "field"))
                frule_id = str(frule.get("rule_id", f"person.{fname}"))
                fmatch = fcompiled.search(chunk)
                if not fmatch:
                    person_fields[fname] = make_span_result(
                        STATE_MISSING, text, None, rule_id=frule_id, name=fname
                    )
                    continue
                group = frule.get("group", 1)
                gspan = _match_value(fmatch, group)
                if gspan is None:
                    person_fields[fname] = make_span_result(
                        STATE_MISSING, text, None, rule_id=frule_id, name=fname
                    )
                    continue
                mapped = map_span(index_map, chunk_fold_abs + gspan[0], chunk_fold_abs + gspan[1])
                raw = text[mapped[0] : mapped[1]] if mapped else ""
                state, warnings = _apply_validators(frule, raw, STATE_MATCHED)
                person_fields[fname] = make_span_result(
                    state, text, mapped, rule_id=frule_id, name=fname,
                    value=raw.strip() if raw else "", warnings=warnings or None,
                )

            persons.append(
                {
                    "side": str(marker_def.get("side", "?")),
                    "role": str(marker_def.get("role", "")),
                    "span": list(person_orig) if person_orig else None,
                    "raw_snippet": text[person_orig[0] : person_orig[1]] if person_orig else "",
                    "rule_id": delim_rule_id,
                    "fields": person_fields,
                }
            )

        blocks.append(
            {
                "side": str(marker_def.get("side", "?")),
                "role": str(marker_def.get("role", "")),
                "rule_id": str(marker_def.get("rule_id", "party.side")),
                "span": list(block_orig) if block_orig else None,
                "raw_snippet": text[block_orig[0] : block_orig[1]] if block_orig else "",
                "state": STATE_MATCHED if persons else STATE_MISSING,
                "persons": persons,
            }
        )
    return {"state": STATE_MATCHED, "blocks": blocks, "zone": zone_id}

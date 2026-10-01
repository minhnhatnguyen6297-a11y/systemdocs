"""Zoning first: nhận loại văn bản từ tiêu đề rồi cắt vùng cấu trúc.

Nguyên lý: tiêu đề (và câu mở đầu) quyết định loại văn bản — thân văn bản
không tự quyết định loại. Sau đó các zone (header -> parties -> asset ->
clauses -> notary) được cắt tuần tự bằng marker trên văn bản đã fold.

Mọi pattern trong profile viết ở dạng folded: chữ thường, không dấu, đ -> d.
Pattern đi qua engine `regex` với timeout thật (TimeoutError ngay trong
match) — kind_rules lẫn zone markers đều được guard, lỗi ghi vào `errors`
kèm rule_id thay vì im lặng.
"""

from __future__ import annotations

import re  # chỉ cho _clean_title_text/fold_lines (không phải pattern profile)
import unicodedata
from typing import Any

import regex

from .extractor import _guarded_search
from .model import STATE_ERROR, STATE_MATCHED, STATE_MISSING, make_span_result


def _clean_title_text(text: str) -> str:
    cleaned = unicodedata.normalize("NFC", str(text or ""))
    return re.sub(r"\s+", " ", cleaned).strip()


def detect_title(
    text: str,
    folded_lines: list[tuple[int, int, str]],
    profile: dict[str, Any],
    timeout_ms: int,
    errors: list[str],
) -> dict:
    """Tìm dòng tiêu đề và nhận loại văn bản.

    folded_lines: list (raw_start, raw_end, folded_line_text) cho từng dòng
    không rỗng — offset đã quy về văn bản nguồn gốc nên span/raw_snippet trỏ
    đúng input người dùng.
    """
    tcfg = profile.get("title", {})
    scan_lines = int(tcfg.get("scan_lines", 25))
    candidate_prefixes = tuple(tcfg.get("candidate_prefixes", ()))
    continuation_prefixes = tuple(tcfg.get("continuation_prefixes", ()))
    stop_prefixes = tuple(tcfg.get("stop_prefixes", ()))
    kind_rules = sorted(
        tcfg.get("kind_rules", []),
        key=lambda r: int(r.get("priority", 0)),
        reverse=True,
    )

    title_line_idx = None
    title_end_idx = None
    for idx, (_, _, folded_line) in enumerate(folded_lines[:scan_lines]):
        if stop_prefixes and folded_line.startswith(stop_prefixes):
            break
        if folded_line.startswith(candidate_prefixes):
            title_line_idx = idx
            title_end_idx = idx
            # Ghép dòng tiếp theo nếu là phần nối của tiêu đề
            # (vd "HỢP ĐỒNG" + "CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT").
            nxt = idx + 1
            if nxt < len(folded_lines):
                next_folded = folded_lines[nxt][2]
                if next_folded.startswith(continuation_prefixes):
                    title_end_idx = nxt
            break

    if title_line_idx is None:
        return {
            "kind": "unknown",
            "title": "",
            "state": STATE_MISSING,
            "span": None,
            "raw_snippet": "",
            "rule_id": None,
        }

    orig_start = folded_lines[title_line_idx][0]
    orig_end = folded_lines[title_end_idx][1]
    title_raw = _clean_title_text(" ".join(text[folded_lines[i][0] : folded_lines[i][1]] for i in range(title_line_idx, title_end_idx + 1)))
    title_folded = " ".join(folded_lines[i][2] for i in range(title_line_idx, title_end_idx + 1))

    kind = "generic"
    rule_id = "title.generic"
    for rule in kind_rules:
        krule_id = str(rule.get("rule_id", "title.rule"))
        try:
            pattern = regex.compile(str(rule.get("pattern", "")), regex.MULTILINE)
        except regex.error as exc:
            errors.append(f"{krule_id}: regex không hợp lệ — {exc}")
            continue
        match, timeout_err = _guarded_search(pattern, title_folded, timeout_ms)
        if timeout_err:
            errors.append(f"{krule_id}: {timeout_err}")
            continue
        if match:
            kind = str(rule.get("kind", "generic"))
            rule_id = krule_id
            break

    return {
        "kind": kind,
        "title": title_raw,
        "state": STATE_MATCHED,
        "span": [orig_start, orig_end],
        "raw_snippet": text[orig_start:orig_end],
        "rule_id": rule_id,
    }


def fold_lines(text: str) -> list[tuple[int, int, str]]:
    """Trả về (start, end, folded_line) cho các dòng không rỗng.

    start/end là offset TRÊN `text` đầu vào (bỏ qua whitespace đầu dòng);
    caller chịu trách nhiệm quy về hệ tọa độ cần thiết. folded_line là nội
    dung dòng đã fold và gom khoảng trắng.
    """
    from .textnorm import fold_with_index_map

    lines: list[tuple[int, int, str]] = []
    offset = 0
    for raw_line in str(text).split("\n"):
        stripped = raw_line.strip()
        line_start = offset + (len(raw_line) - len(raw_line.lstrip()))
        if stripped:
            folded_line = re.sub(r"\s+", " ", fold_with_index_map(stripped)[0]).strip()
            lines.append((line_start, line_start + len(stripped), folded_line))
        offset += len(raw_line) + 1
    return lines


def find_zones(
    text: str,
    folded: str,
    span_of,
    profile: dict[str, Any],
    timeout_ms: int,
    errors: list[str],
) -> list[dict]:
    """Cắt vùng tuần tự theo start_markers của từng zone trong profile.

    Zone i kéo dài tới điểm bắt đầu của zone i+1 tìm thấy; zone cuối dùng
    end_markers hoặc EOF. Marker hỏng/quá hạn ghi vào `errors` kèm rule_id:
    zone không marker nào khớp vẫn `missing`, còn zone có marker bị ngắt giữa
    chừng mà không marker nào khác chạy được báo `error` để không im lặng.
    """
    zone_defs = profile.get("zones", [])
    starts: list[tuple[int, int] | None] = []  # (start_fold, marker_end_fold)
    zone_had_error: list[bool] = []
    cursor = 0
    for zone_def in zone_defs:
        zone_id = str(zone_def.get("zone_id", "?"))
        zrule_id = str(zone_def.get("rule_id", f"zone.{zone_id}"))
        if zone_def.get("implicit_start"):
            starts.append((0, 0))
            zone_had_error.append(False)
            continue
        best = None
        had_error = False
        for marker in zone_def.get("start_markers", []):
            try:
                mre = regex.compile(str(marker), regex.MULTILINE)
            except regex.error as exc:
                errors.append(f"{zrule_id}: regex không hợp lệ — {exc}")
                had_error = True
                continue
            match, timeout_err = _guarded_search(mre, folded[cursor:], timeout_ms)
            if timeout_err:
                errors.append(f"{zrule_id}: {timeout_err}")
                had_error = True
                continue
            if not match:
                continue
            candidate = (cursor + match.start(), cursor + match.end())
            if best is None or candidate[0] < best[0]:
                best = candidate
        starts.append(best)
        zone_had_error.append(had_error)
        if best is not None:
            cursor = best[1]

    zones: list[dict] = []
    for idx, zone_def in enumerate(zone_defs):
        zone_id = str(zone_def.get("zone_id", f"zone_{idx}"))
        rule_id = str(zone_def.get("rule_id", f"zone.{zone_id}"))
        found = starts[idx]
        if found is None:
            state = STATE_ERROR if zone_had_error[idx] else STATE_MISSING
            note = "marker khong danh gia duoc (xem errors)" if zone_had_error[idx] else None
            zones.append(
                make_span_result(state, text, None, rule_id=rule_id, name=zone_id, note=note)
            )
            continue

        start_fold = found[0]
        end_fold = len(folded)
        for nxt in starts[idx + 1 :]:
            if nxt is not None:
                end_fold = nxt[0]
                break
        else:
            # Zone cuối cùng được tìm thấy: cắt tại end_markers nếu có.
            for marker in zone_def.get("end_markers", []):
                try:
                    mre = regex.compile(str(marker), regex.MULTILINE)
                except regex.error as exc:
                    errors.append(f"{rule_id}: regex không hợp lệ — {exc}")
                    continue
                end_match, timeout_err = _guarded_search(mre, folded[start_fold:], timeout_ms)
                if timeout_err:
                    errors.append(f"{rule_id}: {timeout_err}")
                    continue
                if end_match and start_fold + end_match.start() < end_fold:
                    end_fold = start_fold + end_match.start()

        span = span_of(start_fold, max(start_fold, end_fold))
        zone = make_span_result(STATE_MATCHED, text, span, rule_id=rule_id, name=zone_id)
        zone["fold_span"] = [start_fold, max(start_fold, end_fold)]
        zones.append(zone)
    return zones

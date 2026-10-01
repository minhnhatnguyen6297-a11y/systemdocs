"""Trạng thái trường và helper dựng kết quả kèm provenance.

Mọi field/zone kết quả đều mang: state, span [start, end] trên văn bản
nguồn gốc, raw_snippet (đoạn gốc đúng tại span) và rule_id đã tạo ra nó.
Engine không tự suy ra giá trị thiếu: thiếu là `missing`, nhiều nghiệm là
`ambiguous`, lệch chuẩn hiện hành là `warning_nonstandard` (giữ raw).
"""

from __future__ import annotations

STATE_MATCHED = "matched"
STATE_AMBIGUOUS = "ambiguous"
STATE_WARNING = "warning_nonstandard"
STATE_MISSING = "missing"
STATE_ERROR = "error"

VALID_STATES = (
    STATE_MATCHED,
    STATE_AMBIGUOUS,
    STATE_WARNING,
    STATE_MISSING,
    STATE_ERROR,
)


def make_span_result(
    state: str,
    source_text: str,
    span: tuple[int, int] | None,
    *,
    rule_id: str,
    value=None,
    name: str = "",
    **extra,
) -> dict:
    """Dựng record kết quả chuẩn có provenance."""
    start = end = None
    raw = ""
    if span is not None:
        start, end = int(span[0]), int(span[1])
        raw = source_text[start:end]
    result = {
        "name": name,
        "value": value,
        "state": state,
        "span": [start, end] if start is not None else None,
        "raw_snippet": raw,
        "rule_id": rule_id,
    }
    result.update(extra)
    return result

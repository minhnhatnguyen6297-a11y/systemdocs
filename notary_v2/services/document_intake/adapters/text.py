"""Pasted-text source adapter — common parser over raw text.

Thứ tự thử: CCCD QR pipe-format → native OCR doc parser. Không trích được
thực thể → intake.parse_failed. source_refs dùng span [start, end].
"""

from __future__ import annotations

from .. import ocr_pipeline
from ..models import AdapterContext, SourceFailed, SourceSpec
from ..normalization import (
    doc_to_suggestion,
    make_source_ref,
    person_data_to_suggestion,
    unsupported_target_code,
)


async def extract(spec: SourceSpec, ctx: AdapterContext) -> list[dict]:
    text = spec.text or ""
    span_ref = make_source_ref(span=[0, len(text)])
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise SourceFailed("intake.parse_failed", "text source rỗng")

    # QR định dạng "id|cccd|name|dob|gender|address|issue" — parse trực tiếp.
    qr = ocr_pipeline.parse_cccd_qr(text)
    if isinstance(qr, dict):
        data = ocr_pipeline._normalize_person_data(qr)
        sug = person_data_to_suggestion(data, [], spec.source_id, [span_ref])
        if sug:
            return [sug]

    parsed = ocr_pipeline._normalize_native_ocr_doc(lines, "text")
    suggestion = doc_to_suggestion(parsed, spec.source_id, span_ref)
    if not suggestion:
        raise SourceFailed(
            unsupported_target_code(parsed),
            "không trích được thực thể nào từ text")
    return [suggestion]

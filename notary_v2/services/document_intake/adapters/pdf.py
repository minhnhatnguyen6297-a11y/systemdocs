"""PDF source adapter — PyMuPDF text layer + Qwen OCR cho trang scan.

- Trang có text layer → parse deterministic (dùng chung _normalize_native_ocr_doc).
- Trang scan-only → render pixmap → Qwen OCR (ctx.ocr_call injectable);
  thiếu API key → per-source ocr.engine_unavailable.
- > MAX_PDF_PAGES trang → per-source intake_source_too_large (lỗi chỉ biết
  sau khi mở file; không hủy các nguồn khác trong batch).
- check_cancel giữa các trang.
- Person docs qua _pair_persons để ghép mặt trước/sau trên nhiều trang.
"""

from __future__ import annotations

import re
from typing import Optional

from .. import ocr_pipeline
from ..models import (
    AdapterContext,
    MAX_PDF_PAGES,
    SourceFailed,
    SourceSpec,
)
from ..normalization import (
    doc_to_suggestion,
    make_source_ref,
    person_data_to_suggestion,
    unsupported_target_code,
)
from . import check_cancel

_PAGE_TAG = re.compile(r"#p(\d+)$")


async def _ocr_page(page, spec: SourceSpec, ctx: AdapterContext, page_no: int):
    """Render 1 trang scan → Qwen OCR → parsed doc (hoặc None)."""
    if not ctx.api_key:
        raise SourceFailed(
            "ocr.engine_unavailable",
            "thiếu API key OCR cho trang scan (QWEN_API_KEY/DASHSCOPE_API_KEY)")
    pix = page.get_pixmap(dpi=200)
    res = await ocr_pipeline.process_image_bytes(
        pix.tobytes("png"),
        f"{spec.filename}#p{page_no}",
        model=ctx.model,
        api_key=ctx.api_key,
        ai_semaphore=ctx.semaphore,
        client=ctx.client,
        ocr_call=ctx.ocr_call,
    )
    if res.get("error"):
        stage = str(res.get("error_stage") or "model")
        code = "ocr.engine_unavailable" if stage == "model" else "intake.parse_failed"
        raise SourceFailed(code, str(res["error"])[:240])
    doc = res.get("ai_doc")
    return doc if isinstance(doc, dict) else None


def _person_entry(doc: dict, filename: str, page_no: int) -> dict:
    """Person dict theo shape _pair_persons mong đợi (_append_ai_doc)."""
    data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
    return {
        **data,
        "_source": "AI",
        "source_type": "AI",
        "side": doc.get("side", "unknown"),
        "_files": [f"{filename}#p{page_no}"],
        "_qr": False,
        "field_sources": {},
        "warnings": list(doc.get("warnings") or []),
    }


def _pages_of(merged: dict) -> list[int]:
    pages = []
    for f in merged.get("_files") or []:
        m = _PAGE_TAG.search(str(f))
        if m:
            pages.append(int(m.group(1)))
    return pages


async def extract(spec: SourceSpec, ctx: AdapterContext) -> list[dict]:
    content = ctx.read_file(spec)
    try:
        import fitz

        pdf = fitz.open(stream=content, filetype="pdf")
    except SourceFailed:
        raise
    except Exception as exc:
        raise SourceFailed("intake.parse_failed", f"không mở được PDF: {exc}") from exc

    try:
        page_count = pdf.page_count
        if page_count > MAX_PDF_PAGES:
            # Limit §5.2 nhưng chỉ phát hiện được khi mở file → per-source
            # error (giống file size thật), không hủy các nguồn khác.
            raise SourceFailed(
                "intake_source_too_large",
                f"PDF vượt {MAX_PDF_PAGES} trang ({page_count})")
        page_docs: list[tuple[int, dict]] = []
        last_unmapped: Optional[dict] = None
        for i in range(page_count):
            check_cancel(ctx)
            page = pdf.load_page(i)
            text = page.get_text("text") or ""
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            if lines:
                parsed = ocr_pipeline._normalize_native_ocr_doc(
                    lines, f"{spec.filename}#p{i + 1}")
            else:
                parsed = await _ocr_page(page, spec, ctx, i + 1)
            if parsed and parsed.get("doc_type") in ("person", "property"):
                page_docs.append((i + 1, parsed))
            elif parsed and unsupported_target_code(parsed) == "intake.unsupported_target":
                # Trang nhận diện được loại nhưng chưa map person/asset
                # (vd marriage) — ghi nhớ để error code cuối chính xác.
                last_unmapped = parsed
    finally:
        pdf.close()

    suggestions: list[dict] = []
    person_inputs: list[tuple[int, dict]] = []
    for page_no, doc in page_docs:
        if doc.get("doc_type") == "property":
            sug = doc_to_suggestion(
                doc, spec.source_id,
                make_source_ref(filename=spec.filename, page=page_no))
            if sug:
                suggestions.append(sug)
        else:
            person_inputs.append((page_no, doc))

    if person_inputs:
        merged_persons = ocr_pipeline._pair_persons(
            [_person_entry(doc, spec.filename, page_no)
             for page_no, doc in person_inputs])
        for merged in merged_persons:
            pages = _pages_of(merged)
            refs = [make_source_ref(filename=spec.filename, page=p) for p in pages]
            if not refs:
                refs = [make_source_ref(filename=spec.filename)]
            sug = person_data_to_suggestion(
                merged, merged.get("warnings") or [], spec.source_id, refs)
            if sug:
                suggestions.append(sug)

    if not suggestions:
        raise SourceFailed(
            unsupported_target_code(last_unmapped or {}),
            "không trích được thực thể nào từ PDF")
    return suggestions

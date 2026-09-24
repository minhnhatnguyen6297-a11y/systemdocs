"""Image source adapter → shared Qwen OCR pipeline (ocr_pipeline.py).

Reuse trực tiếp process_image_bytes — không copy parser. Thiếu API key hoặc
engine lỗi → per-source `ocr.engine_unavailable`, các nguồn khác vẫn chạy.
"""

from __future__ import annotations

from pathlib import Path

from .. import ocr_pipeline
from ..models import AdapterContext, SourceFailed, SourceSpec
from ..normalization import doc_to_suggestion, make_source_ref

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


async def extract(spec: SourceSpec, ctx: AdapterContext) -> list[dict]:
    ext = Path(spec.path or spec.filename or "").suffix.lower()
    if ext and ext not in _IMAGE_EXTS:
        raise SourceFailed(
            "intake.parse_failed",
            f"định dạng ảnh không hỗ trợ: {ext or spec.filename}")
    content = ctx.read_file(spec)
    if not ctx.api_key:
        raise SourceFailed(
            "ocr.engine_unavailable",
            "thiếu API key OCR (QWEN_API_KEY/DASHSCOPE_API_KEY)")
    res = await ocr_pipeline.process_image_bytes(
        content,
        spec.filename,
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
    suggestion = doc_to_suggestion(
        doc if isinstance(doc, dict) else {},
        spec.source_id,
        make_source_ref(filename=spec.filename),
    )
    if not suggestion:
        raise SourceFailed(
            "intake.parse_failed",
            "không nhận diện được giấy tờ trong ảnh")
    return [suggestion]

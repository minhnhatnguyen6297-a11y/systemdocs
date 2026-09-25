"""OCR primitives for the independent Zalo intake module (MIN-103 slice C).

Public surface — Qwen call/prep (``qwen``), ingest-time media prep (``prep``)
and the module-owned error taxonomy (``errors``). No FastAPI imports here.
"""
from .errors import OcrApiError, OcrError, OcrParseError, OcrTransportError
from .prep import (
    inspect_media,
    proposed_crop,
    render_pdf_pages,
    write_processed_image,
)
from .qwen import (
    AI_MAX_IMAGE_PX,
    AI_TIMEOUT_SECONDS,
    DEFAULT_MODEL,
    JPEG_QUALITY,
    OCR_AI_CONCURRENCY,
    QWEN_OCR_BASE_URL,
    QWEN_OCR_ENABLE_ROTATE,
    QWEN_OCR_MAX_PIXELS,
    QWEN_OCR_MIN_PIXELS,
    build_qwen_ocr_body,
    call_qwen_ocr,
    clean_text,
    extract_native_ocr_lines,
    prepare_ai_image_bytes,
    resolve_api_key,
    resolve_base_url,
    resolve_model,
)

__all__ = [
    "AI_MAX_IMAGE_PX",
    "AI_TIMEOUT_SECONDS",
    "DEFAULT_MODEL",
    "JPEG_QUALITY",
    "OCR_AI_CONCURRENCY",
    "QWEN_OCR_BASE_URL",
    "QWEN_OCR_ENABLE_ROTATE",
    "QWEN_OCR_MAX_PIXELS",
    "QWEN_OCR_MIN_PIXELS",
    "OcrApiError",
    "OcrError",
    "OcrParseError",
    "OcrTransportError",
    "build_qwen_ocr_body",
    "call_qwen_ocr",
    "clean_text",
    "extract_native_ocr_lines",
    "inspect_media",
    "prepare_ai_image_bytes",
    "proposed_crop",
    "render_pdf_pages",
    "resolve_api_key",
    "resolve_base_url",
    "resolve_model",
    "write_processed_image",
]

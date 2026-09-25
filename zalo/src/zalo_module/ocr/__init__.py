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
from .pipeline import (
    SubmittedFrame,
    parse_provider_lines,
    prepare_default_frame,
    prepare_variant_frame,
    run_ocr_call,
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
    QwenOcrResult,
    build_qwen_ocr_body,
    call_qwen_ocr,
    call_qwen_ocr_detailed,
    clean_text,
    extract_native_ocr_lines,
    extract_words_info,
    prepare_ai_image_bytes,
    resolve_api_key,
    resolve_base_url,
    resolve_model,
)
from .variants import CROP_FRACTIONS, VARIANTS, crop_fraction, normalize_preset

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
    "CROP_FRACTIONS",
    "OcrApiError",
    "OcrError",
    "OcrParseError",
    "OcrTransportError",
    "QwenOcrResult",
    "SubmittedFrame",
    "VARIANTS",
    "build_qwen_ocr_body",
    "call_qwen_ocr",
    "call_qwen_ocr_detailed",
    "clean_text",
    "crop_fraction",
    "extract_native_ocr_lines",
    "extract_words_info",
    "inspect_media",
    "normalize_preset",
    "parse_provider_lines",
    "prepare_ai_image_bytes",
    "prepare_default_frame",
    "prepare_variant_frame",
    "proposed_crop",
    "render_pdf_pages",
    "resolve_api_key",
    "resolve_base_url",
    "resolve_model",
    "run_ocr_call",
    "write_processed_image",
]

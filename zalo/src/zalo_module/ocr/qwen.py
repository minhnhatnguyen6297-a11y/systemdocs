"""Qwen OCR primitives — DashScope call + image prep, ported verbatim-behavior
from ``notary_v2/services/document_intake/ocr_pipeline.py`` (MIN-103 slice C).

Parity notes vs the legacy source:

- Constants and env names are identical (``QWEN_OCR_BASE_URL``, ``OCR_MODEL``,
  ``QWEN_API_KEY``/``DASHSCOPE_API_KEY``, ``QWEN_OCR_MIN_PIXELS``,
  ``QWEN_OCR_MAX_PIXELS``, ``QWEN_OCR_ENABLE_ROTATE``, ``QWEN_MAX_IMAGE_PX``,
  ``OCR_AI_TIMEOUT_SECONDS``, ``OCR_AI_CONCURRENCY``). Module-level values are
  resolved at import, same as legacy.
- Legacy additionally read ``notary_v2/.env`` via ``dotenv_values`` for the
  api key/model. The module reads ``os.environ`` only — no .env file coupling.
- ``fastapi.HTTPException`` is replaced by ``zalo_module.ocr.errors`` types:
  ``httpx.RequestError``/timeout → ``OcrTransportError`` (was HTTP 502
  "Cannot reach…"), non-2xx → ``OcrApiError`` carrying status + body[:300]
  (was HTTP 502 with the same truncated body), invalid JSON body →
  ``OcrParseError`` (legacy let ``resp.json()`` raise into the "model"
  error_stage bucket).
- Request body shape is byte-identical to ``_call_qwen_native_ocr_single``:
  ``POST {base}/api/v1/services/aigc/multimodal-generation/generation`` with
  ``{model, input:{messages:[{role:"user", content:[{image:
  "data:image/jpeg;base64,{b64}", min_pixels, max_pixels, enable_rotate}]}]},
  parameters:{ocr_options:{task:"text_recognition"}}}``.
"""
from __future__ import annotations

import base64
import io
import logging
import os
import re
from time import perf_counter
from typing import Any

import httpx
from PIL import Image, ImageOps

from .errors import OcrApiError, OcrError, OcrParseError, OcrTransportError

_logger = logging.getLogger("zalo_module.ocr.qwen")

# ---------------------------------------------------------------------------
# Constants — values verbatim from ocr_pipeline.py:36-48.
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "qwen-vl-ocr-2025-11-20"
QWEN_OCR_BASE_URL = os.getenv(
    "QWEN_OCR_BASE_URL", "https://dashscope-intl.aliyuncs.com"
).rstrip("/")
QWEN_OCR_MIN_PIXELS = int(os.getenv("QWEN_OCR_MIN_PIXELS", "3072"))
QWEN_OCR_MAX_PIXELS = int(os.getenv("QWEN_OCR_MAX_PIXELS", "8388608"))
QWEN_OCR_ENABLE_ROTATE = os.getenv("QWEN_OCR_ENABLE_ROTATE", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OCR_AI_CONCURRENCY = max(1, int(os.getenv("OCR_AI_CONCURRENCY", "6")))
AI_TIMEOUT_SECONDS = float(os.getenv("OCR_AI_TIMEOUT_SECONDS", "90"))
AI_MAX_IMAGE_PX = max(640, int(os.getenv("QWEN_MAX_IMAGE_PX", "1800")))
JPEG_QUALITY = 82

_QWEN_API_PATH = "/api/v1/services/aigc/multimodal-generation/generation"


def _ms(seconds: float) -> float:
    return round(max(0.0, float(seconds)) * 1000.0, 2)


def clean_text(value: Any) -> str:
    """Verbatim port of ``_clean_text`` (ocr_pipeline.py:90-91)."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


# ---------------------------------------------------------------------------
# Resolution helpers — explicit kwarg > module Settings > env > default.
# ---------------------------------------------------------------------------


def _resolve_model(configured: str | None) -> str:
    """Port of ``_get_model`` (ocr_pipeline.py:59-65) minus .env reading."""
    configured = (configured or "").strip()
    if configured.lower().startswith("models/"):
        configured = configured.split("/", 1)[1]
    if configured and "qwen" not in configured.lower():
        return DEFAULT_MODEL
    return (configured or DEFAULT_MODEL).lower()


def resolve_model(model: str | None = None, settings: Any = None) -> str:
    configured = model
    if configured is None and settings is not None:
        configured = getattr(settings, "qwen_model", None)
    if configured is None:
        configured = os.getenv("OCR_MODEL", "")
    return _resolve_model(configured)


def resolve_api_key(api_key: str | None = None, settings: Any = None) -> str:
    """Port of ``_get_api_key`` (ocr_pipeline.py:68-75) minus .env reading."""
    if api_key:
        return api_key
    if settings is not None:
        key = getattr(settings, "qwen_api_key", None)
        if key:
            return key
    return os.getenv("QWEN_API_KEY", "") or os.getenv("DASHSCOPE_API_KEY", "")


def resolve_base_url(base_url: str | None = None, settings: Any = None) -> str:
    if base_url:
        return base_url.rstrip("/")
    if settings is not None:
        value = getattr(settings, "qwen_api_base", None)
        if value:
            return str(value).rstrip("/")
    return QWEN_OCR_BASE_URL


def _resolve_enable_rotate(enable_rotate: bool | str | None) -> bool:
    if enable_rotate is None:
        return QWEN_OCR_ENABLE_ROTATE
    if isinstance(enable_rotate, str):
        return enable_rotate.strip().lower() in {"1", "true", "yes", "on"}
    return bool(enable_rotate)


# ---------------------------------------------------------------------------
# Image prep — verbatim port of ``_prepare_ai_image_bytes`` (:322-343).
# ---------------------------------------------------------------------------


def prepare_ai_image_bytes(file_bytes: bytes, max_px: int | None = None) -> bytes:
    """EXIF transpose → RGB → LANCZOS downscale to ≤max_px → JPEG q82 optimize.

    ``max_px`` defaults to ``AI_MAX_IMAGE_PX`` (env ``QWEN_MAX_IMAGE_PX``,
    default 1800, floor 640). Any decode/transform error returns the original
    bytes, same as legacy — the call stays non-blocking for malformed input.
    """
    limit = AI_MAX_IMAGE_PX if max_px is None else max_px
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        if img.mode == "L":
            img = img.convert("RGB")

        width, height = img.size
        max_side = max(width, height)
        if max_side > limit:
            scale = limit / float(max_side)
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            img = img.resize(new_size, Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return buf.getvalue()
    except Exception:
        # Keep flow non-blocking for tests or malformed inputs.
        return file_bytes


# ---------------------------------------------------------------------------
# Response parse — verbatim port of ``_extract_native_ocr_lines`` (:346-374).
# ---------------------------------------------------------------------------


def extract_native_ocr_lines(payload: dict[str, Any]) -> list[str]:
    choices = payload.get("output", {}).get("choices", [])
    if not choices:
        return []
    message = choices[0].get("message", {})
    content = message.get("content")
    raw_text = ""
    if isinstance(content, str):
        raw_text = content
    elif isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text)
            elif isinstance(item, str) and item.strip():
                chunks.append(item)
        raw_text = "\n".join(chunks)
    elif isinstance(message.get("text"), str):
        raw_text = message.get("text", "")

    lines = []
    raw_text = (raw_text or "").replace("\\n", "\n")
    for line in re.split(r"[\r\n]+", raw_text):
        clean = clean_text(line)
        if clean:
            lines.append(clean)
    return lines


# ---------------------------------------------------------------------------
# DashScope call — port of ``_call_qwen_native_ocr_single`` (:377-449).
# ---------------------------------------------------------------------------


def build_qwen_ocr_body(
    *,
    model: str,
    image_b64: str,
    min_pixels: int,
    max_pixels: int,
    enable_rotate: bool,
) -> dict[str, Any]:
    """The exact legacy request body — kept as a separate builder so tests can
    golden-diff the serialized shape against ocr_pipeline.py."""
    return {
        "model": model,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": f"data:image/jpeg;base64,{image_b64}",
                            "min_pixels": min_pixels,
                            "max_pixels": max_pixels,
                            "enable_rotate": enable_rotate,
                        }
                    ],
                }
            ]
        },
        "parameters": {"ocr_options": {"task": "text_recognition"}},
    }


async def call_qwen_ocr(
    image: bytes | str,
    *,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    min_pixels: int | None = None,
    max_pixels: int | None = None,
    enable_rotate: bool | str | None = None,
    timeout: float | None = None,
    filename: str = "",
    settings: Any = None,
    client: httpx.AsyncClient | None = None,
) -> list[str]:
    """POST one image to DashScope native OCR, return cleaned text lines.

    ``image`` is raw bytes (base64-encoded here) or a pre-encoded base64 str.
    Per-parameter resolution: explicit kwarg > ``settings`` (module Settings
    duck-typed: ``qwen_api_base``/``qwen_model``/``qwen_api_key``) > env/module
    constants. No internal retry — same as legacy.
    """
    key = resolve_api_key(api_key, settings)
    if not key:
        raise OcrError("Missing API key for OCR AI model")
    resolved_model = resolve_model(model, settings)
    url = f"{resolve_base_url(base_url, settings)}{_QWEN_API_PATH}"
    resolved_min = QWEN_OCR_MIN_PIXELS if min_pixels is None else int(min_pixels)
    resolved_max = QWEN_OCR_MAX_PIXELS if max_pixels is None else int(max_pixels)
    rotate_flag = _resolve_enable_rotate(enable_rotate)
    resolved_timeout = AI_TIMEOUT_SECONDS if timeout is None else float(timeout)

    image_b64 = (
        base64.b64encode(image).decode() if isinstance(image, (bytes, bytearray)) else str(image)
    )
    body = build_qwen_ocr_body(
        model=resolved_model,
        image_b64=image_b64,
        min_pixels=resolved_min,
        max_pixels=resolved_max,
        enable_rotate=rotate_flag,
    )
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    t0 = perf_counter()

    async def _send(active_client: httpx.AsyncClient) -> httpx.Response:
        return await active_client.post(
            url, headers=headers, json=body, timeout=resolved_timeout
        )

    try:
        if client is not None:
            resp = await _send(client)
        else:
            async with httpx.AsyncClient(timeout=resolved_timeout) as owned:
                resp = await _send(owned)
    except httpx.RequestError as exc:
        _logger.warning(
            "[OCR] qwen_call error filename=%s model=%s latency_ms=%s network: %s",
            filename,
            resolved_model,
            _ms(perf_counter() - t0),
            exc,
        )
        raise OcrTransportError(f"Cannot reach Qwen OCR endpoint: {exc}") from exc

    if not resp.is_success:
        detail = resp.text[:300]
        _logger.warning(
            "[OCR] qwen_call error filename=%s model=%s latency_ms=%s %s",
            filename,
            resolved_model,
            _ms(perf_counter() - t0),
            detail,
        )
        raise OcrApiError(resp.status_code, detail)

    try:
        payload = resp.json()
    except Exception as exc:
        raise OcrParseError(f"Qwen OCR returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise OcrParseError("Qwen OCR response is not a JSON object")

    lines = extract_native_ocr_lines(payload)
    _logger.info(
        "[OCR] qwen_call ok filename=%s model=%s latency_ms=%s lines=%s",
        filename,
        resolved_model,
        _ms(perf_counter() - t0),
        len(lines),
    )
    return lines


# Boundary kept for MIN-95 (was the original stub in this file).
def ocr_attachment(attachment_id: str) -> list:
    """Adapter Qwen trả records cho từng trang, kể cả status lỗi (plan §3.1)."""
    raise NotImplementedError("MIN-95")

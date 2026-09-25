"""OCR-layer exceptions for the independent Zalo intake module.

Ported from ``notary_v2/services/document_intake/ocr_pipeline.py`` (MIN-103
slice C). The legacy code raised ``fastapi.HTTPException`` from the Qwen call
boundary; the module keeps the OCR layer free of FastAPI — HTTP mapping lives
in ``zalo_module.api`` only.
"""
from __future__ import annotations


class OcrError(Exception):
    """Base for every OCR-layer failure (media prep + Qwen call + parse)."""


class OcrTransportError(OcrError):
    """Qwen OCR endpoint unreachable or the request timed out.

    Maps legacy ``httpx.RequestError`` (incl. ``httpx.TimeoutException``)
    handling — the legacy facade surfaced these as HTTP 502
    "Cannot reach Qwen OCR endpoint".
    """


class OcrApiError(OcrError):
    """Qwen OCR returned a non-2xx response.

    Carries ``status_code`` and ``body`` (truncated to 300 chars, same cap as
    the legacy ``resp.text[:300]`` detail).
    """

    def __init__(self, status_code: int, body: str = "") -> None:
        self.status_code = int(status_code)
        self.body = body or ""
        super().__init__(f"Qwen OCR error (status {self.status_code}): {self.body}")


class OcrParseError(OcrError):
    """The Qwen HTTP response body could not be decoded/used.

    Raised when a 2xx response is not valid JSON or has no usable payload —
    the stage the legacy pipeline reported as ``error_stage="model"`` vs
    ``"parse"`` split is kept by callers, not by this exception family.
    """

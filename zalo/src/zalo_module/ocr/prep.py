"""Zalo-owned media prep primitives — ported verbatim-behavior from
``notary_v2/services/zalo_inbox.py`` (MIN-103 slice C).

These are the *ingest-time* prep steps (2400px thumbnail, MedianFilter(3),
Contrast×1.12, autocontrast crop proposal, PyMuPDF ``Matrix(2,2)`` PDF render)
— a different pipeline from the OCR-time ``prepare_ai_image_bytes`` in
``qwen.py`` (1800px, JPEG q82). FR-031 forbids re-running crop/denoise/contrast
on a snapshot, so the two stay separate.

Error mapping: legacy raised ``InboxValidationError``; the module raises
``OcrError`` with the same Vietnamese messages so upstream wording is kept.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import fitz
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from .errors import OcrError

# Verbatim tuning constants from zalo_inbox.py.
CROP_THRESHOLD = 24            # mask cutoff in _proposed_crop (:979)
CROP_MIN_AREA_RATIO = 0.40     # bbox area gate (:986)
CROP_MAX_AREA_RATIO = 0.97
PROCESSED_MAX_PX = 2400        # thumbnail box in _write_processed_image (:993)
PROCESSED_MEDIAN_SIZE = 3      # MedianFilter(size=3) (:994)
PROCESSED_CONTRAST = 1.12      # Contrast enhance factor (:995)
PROCESSED_JPEG_QUALITY = 90    # save quality (:997,:1002)
PDF_RENDER_ZOOM = 2            # fitz.Matrix(2,2) ≈144dpi (:1030)


def _read_source(source: str | Path | bytes) -> tuple[Any, bytes | None]:
    """Normalize ``source`` into (fitz/PIL-openable, head-bytes-or-None)."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        with open(path, "rb") as fh:
            head = fh.read(8)
        return path, head
    data = bytes(source)
    return io.BytesIO(data), data[:8]


def _detect_mime(source: str | Path | bytes, head: bytes | None) -> str:
    if head is None:
        head = b""
    if head.startswith(b"%PDF-"):
        return "application/pdf"
    if isinstance(source, (str, Path)) and str(source).lower().endswith(".pdf"):
        return "application/pdf"
    return "image"


def inspect_media(
    source: str | Path | bytes, mime_type: str | None = None
) -> tuple[int, int]:
    """Port of ``_inspect_media`` (zalo_inbox.py:859-884) → ``(items, pixels)``.

    PDF: ``(page_count, Σ int(rect.w*2) * int(rect.h*2))`` — the same 2× zoom
    pixel estimate the batch limits used. Image: ``(1, w*h)`` after
    ``verify()``. ``mime_type`` defaults to magic-byte sniffing (``%PDF-``).
    Raises ``OcrError`` on passworded/empty/corrupt PDF or unreadable image.
    """
    openable, head = _read_source(source)
    mime = mime_type or _detect_mime(source, head)

    if mime == "application/pdf":
        try:
            if isinstance(openable, io.BytesIO):
                document = fitz.open(stream=openable.getvalue(), filetype="pdf")
            else:
                document = fitz.open(openable)
            if document.needs_pass:
                raise OcrError("PDF có mật khẩu")
            pages = document.page_count
            pixels = 0
            for page in document:
                rect = page.rect
                pixels += int(rect.width * 2) * int(rect.height * 2)
            document.close()
            if pages < 1:
                raise OcrError("PDF không có trang")
            return pages, pixels
        except OcrError:
            raise
        except Exception as exc:
            raise OcrError("PDF hỏng hoặc không đọc được") from exc
    try:
        with Image.open(openable) as image:
            image.verify()
        with Image.open(_read_source(source)[0]) as image:
            return 1, image.width * image.height
    except Exception as exc:
        raise OcrError("Ảnh hỏng hoặc không đọc được") from exc


def proposed_crop(image: Image.Image) -> tuple[int, int, int, int] | None:
    """Port of ``_proposed_crop`` (zalo_inbox.py:976-988).

    Autocontrast → invert → threshold>24 mask → bbox; rejected when the bbox
    area ratio is outside [0.40, 0.97].
    """
    gray = ImageOps.autocontrast(ImageOps.grayscale(image))
    inverted = ImageOps.invert(gray)
    mask = inverted.point(lambda value: 255 if value > CROP_THRESHOLD else 0)
    bbox = mask.getbbox()
    if not bbox:
        return None
    width, height = image.size
    area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    ratio = area / max(1, width * height)
    if ratio < CROP_MIN_AREA_RATIO or ratio > CROP_MAX_AREA_RATIO:
        return None
    return bbox


def write_processed_image(
    src: Image.Image | str | Path | bytes,
    dst_full: str | Path,
    dst_crop: str | Path | None = None,
) -> tuple[Path, Path | None]:
    """Port of ``_write_processed_image`` (zalo_inbox.py:991-1003).

    EXIF transpose → RGB → ≤2400 LANCZOS thumbnail → MedianFilter(3) →
    Contrast×1.12 → JPEG q90 to ``dst_full``. Then ``proposed_crop`` runs on
    the *processed* image; when a bbox exists and ``dst_crop`` is given the
    crop is written as JPEG q90. Returns ``(full_path, crop_path|None)``.
    """
    if isinstance(src, Image.Image):
        image = src
    elif isinstance(src, (str, Path)):
        image = Image.open(src)
    else:
        image = Image.open(io.BytesIO(bytes(src)))

    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((PROCESSED_MAX_PX, PROCESSED_MAX_PX), Image.Resampling.LANCZOS)
    image = image.filter(ImageFilter.MedianFilter(size=PROCESSED_MEDIAN_SIZE))
    image = ImageEnhance.Contrast(image).enhance(PROCESSED_CONTRAST)

    full_path = Path(dst_full)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(full_path, "JPEG", quality=PROCESSED_JPEG_QUALITY, optimize=True)

    bbox = proposed_crop(image)
    if bbox is None or dst_crop is None:
        return full_path, None
    crop_path = Path(dst_crop)
    crop_path.parent.mkdir(parents=True, exist_ok=True)
    image.crop(bbox).save(crop_path, "JPEG", quality=PROCESSED_JPEG_QUALITY, optimize=True)
    return full_path, crop_path


def render_pdf_pages(pdf: str | Path | bytes) -> list[bytes]:
    """Render each PDF page to PNG bytes via ``fitz.Matrix(2,2), alpha=False``
    (zalo_inbox.py:1030, ≈144dpi). Raises ``OcrError`` on unreadable PDFs."""
    try:
        if isinstance(pdf, (str, Path)):
            document = fitz.open(pdf)
        else:
            document = fitz.open(stream=bytes(pdf), filetype="pdf")
    except Exception as exc:
        raise OcrError("PDF hỏng hoặc không đọc được") from exc
    try:
        pages: list[bytes] = []
        for page in document:
            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(PDF_RENDER_ZOOM, PDF_RENDER_ZOOM), alpha=False
            )
            pages.append(pixmap.tobytes("png"))
        return pages
    finally:
        document.close()

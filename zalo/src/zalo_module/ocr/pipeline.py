"""OCR-time pipeline helpers (MIN-95) — submitted-frame prep, closed
variant transforms, provider-geometry parsing, and a synchronous call
wrapper around the async Qwen primitive.

Everything here is offline-friendly: the provider call goes through
``call_qwen_ocr_detailed`` with an injectable ``client``.

Contract anchors (raw-record.schema.json + contracts/zalo-intake §6/§9):

- ``transform_chain`` records the client-side ops actually applied
  (``exif_transpose`` / ``resize`` / ``crop`` / ``rotate``); provider-side
  ``enable_rotate`` is *not* a client transform and is carried on the
  frame instead.
- ``submitted_frame`` holds the *real* sent dimensions.
- ``provider_lines`` keep provider ``words_info`` values verbatim
  (``text``/``location``/``rotate_rect``) + module-assigned
  ``element_index``; malformed geometry flips the attempt to
  ``present_invalid`` and is *not* stored (it could not validate).
- ``present_mapping_verified`` is never emitted (contract-reserved).
"""
from __future__ import annotations

import asyncio
import io
import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from PIL import Image, ImageOps

from . import variants
from .qwen import (
    AI_MAX_IMAGE_PX,
    JPEG_QUALITY,
    QwenOcrResult,
    call_qwen_ocr_detailed,
)

# Prep policies (sent-image bounds). The default pass uses the legacy
# prepare_ai_image_bytes policy (<=1800px JPEG q82); full_res re-reads at the
# processed scale (<=2400px JPEG q90) — contract appendix + fixture rec-11.
DEFAULT_MAX_SIDE = AI_MAX_IMAGE_PX          # 1800 env floor 640
FULL_RES_MAX_SIDE = 2400
FULL_RES_QUALITY = 90
# PDF page renders arrive as PNG bytes (prep.render_pdf_pages).

TASKS = {"text_recognition", "advanced_recognition"}
GEOMETRY_STATUSES = {
    "not_applicable",
    "absent",
    "present_unverified",
    "present_invalid",
}


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _finite_seq(value: Any, length: int) -> bool:
    return (
        isinstance(value, (list, tuple))
        and len(value) == length
        and all(_is_finite_number(v) for v in value)
    )


@dataclass
class SubmittedFrame:
    """One image frame actually submitted to the provider."""

    image_bytes: bytes
    width: int
    height: int
    transform_chain: list[dict]
    region: dict
    operation: str                       # original|rotate|crop_bottom|full_res
    enable_rotate: bool | None = None    # None → module/provider default
    frame_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def submitted_frame_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "width": int(self.width),
            "height": int(self.height),
        }


def _open_rgb(raw: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(raw))
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    if img.mode == "L":
        img = img.convert("RGB")
    return img


def _resize_cap(img: Image.Image, cap: int) -> tuple[Image.Image, bool]:
    width, height = img.size
    max_side = max(width, height)
    if max_side <= cap:
        return img, False
    scale = cap / float(max_side)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return img.resize(new_size, Image.LANCZOS), True


def _save_jpeg(img: Image.Image, quality: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def prepare_default_frame(raw: bytes) -> SubmittedFrame:
    """Default OCR frame: EXIF → RGB → ≤1800px → JPEG q82 (legacy policy)."""
    img = _open_rgb(raw)
    chain: list[dict] = [{"op": "exif_transpose"}]
    img, resized = _resize_cap(img, DEFAULT_MAX_SIDE)
    if resized:
        chain.append(
            {
                "op": "resize",
                "params": {"max_side": DEFAULT_MAX_SIDE, "quality": JPEG_QUALITY},
            }
        )
    data = _save_jpeg(img, JPEG_QUALITY)
    return SubmittedFrame(
        image_bytes=data,
        width=img.width,
        height=img.height,
        transform_chain=chain,
        region={"kind": "full_image"},
        operation="original",
    )


def prepare_variant_frame(raw: bytes, variant: str, preset) -> SubmittedFrame:
    """Build the submitted frame for a closed request variant (contract §9.2).

    - ``rotate``      → default-prep frame + provider ``enable_rotate=true``
      (no client-side rotation; ``image_operation=rotate``).
    - ``crop_bottom`` → EXIF → ≤2400 normalize → crop bottom ``fraction`` →
      ≤1800 → JPEG q82; ``region={kind:"bottom_fraction", fraction}``.
    - ``full_res``    → EXIF → ≤2400 → JPEG q90 (processed-scale re-read).

    Raises ``ValueError`` (contract code prefix) on invalid variant/preset.
    """
    preset = variants.normalize_preset(variant, preset)
    img = _open_rgb(raw)
    chain: list[dict] = [{"op": "exif_transpose"}]

    if variant == "crop_bottom":
        img, normalized = _resize_cap(img, FULL_RES_MAX_SIDE)
        if normalized:
            chain.append(
                {
                    "op": "resize",
                    "params": {"max_side": FULL_RES_MAX_SIDE, "quality": FULL_RES_QUALITY},
                }
            )
        fraction = variants.crop_fraction(preset)
        top = int(round(img.height * (1.0 - fraction)))
        top = min(max(0, top), img.height - 1)
        img = img.crop((0, top, img.width, img.height))
        chain.append(
            {"op": "crop", "params": {"top_fraction": round(1.0 - fraction, 6)}}
        )
        img, shrunk = _resize_cap(img, DEFAULT_MAX_SIDE)
        if shrunk:
            chain.append(
                {
                    "op": "resize",
                    "params": {"max_side": DEFAULT_MAX_SIDE, "quality": JPEG_QUALITY},
                }
            )
        data = _save_jpeg(img, JPEG_QUALITY)
        return SubmittedFrame(
            image_bytes=data,
            width=img.width,
            height=img.height,
            transform_chain=chain,
            region={"kind": "bottom_fraction", "fraction": fraction},
            operation="crop_bottom",
        )

    if variant == "full_res":
        img, resized = _resize_cap(img, FULL_RES_MAX_SIDE)
        if resized:
            chain.append(
                {
                    "op": "resize",
                    "params": {"max_side": FULL_RES_MAX_SIDE, "quality": FULL_RES_QUALITY},
                }
            )
        data = _save_jpeg(img, FULL_RES_QUALITY)
        return SubmittedFrame(
            image_bytes=data,
            width=img.width,
            height=img.height,
            transform_chain=chain,
            region={"kind": "full_image"},
            operation="full_res",
        )

    # rotate — provider-side rotation, client frame identical to default.
    img, resized = _resize_cap(img, DEFAULT_MAX_SIDE)
    if resized:
        chain.append(
            {
                "op": "resize",
                "params": {"max_side": DEFAULT_MAX_SIDE, "quality": JPEG_QUALITY},
            }
        )
    data = _save_jpeg(img, JPEG_QUALITY)
    return SubmittedFrame(
        image_bytes=data,
        width=img.width,
        height=img.height,
        transform_chain=chain,
        region={"kind": "full_image"},
        operation="rotate",
        enable_rotate=True,
    )


def parse_provider_lines(
    words_info: list | None, task: str
) -> tuple[str, list[dict] | None]:
    """Map provider ``words_info`` to (geometry_status, provider_lines).

    - ``text_recognition`` → ``("not_applicable", None)`` (schema: no
      provider_lines allowed).
    - empty/absent ``words_info`` → ``("absent", None)``.
    - otherwise every element is kept verbatim (``text`` + ``location`` +
      ``rotate_rect`` as returned) under a module ``element_index``;
      malformed/non-finite geometry values are *dropped* (they could not
      pass schema) and flip the status to ``present_invalid``.
    """
    if task == "text_recognition":
        return "not_applicable", None
    if not words_info:
        return "absent", None
    provider_lines: list[dict] = []
    any_invalid = False
    for index, element in enumerate(words_info):
        entry: dict[str, Any] = {"element_index": index, "text": ""}
        if isinstance(element, dict):
            text = element.get("text")
            if isinstance(text, str):
                entry["text"] = text
            elif text is not None:
                entry["text"] = str(text)
            location = element.get("location")
            if location is not None:
                if _finite_seq(location, 8):
                    entry["location"] = list(location)
                else:
                    any_invalid = True
            if "rotate_rect" in element:
                rect = element.get("rotate_rect")
                if rect is None:
                    entry["rotate_rect"] = None
                elif _finite_seq(rect, 5):
                    entry["rotate_rect"] = list(rect)
                else:
                    any_invalid = True
        else:
            any_invalid = True
        provider_lines.append(entry)
    status = "present_invalid" if any_invalid else "present_unverified"
    return status, provider_lines


def run_ocr_call(
    image_bytes: bytes,
    *,
    settings: Any = None,
    task: str = "text_recognition",
    enable_rotate: bool | None = None,
    filename: str = "",
    client: Any = None,
) -> QwenOcrResult:
    """Synchronous wrapper: ``asyncio.run`` around the async Qwen call.

    ``client`` is the offline injection point (object with async ``post``).
    """
    return asyncio.run(
        call_qwen_ocr_detailed(
            image_bytes,
            task=task,
            enable_rotate=enable_rotate,
            filename=filename,
            settings=settings,
            client=client,
        )
    )

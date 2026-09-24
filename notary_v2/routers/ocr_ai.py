"""
AI OCR router (cloud path) with native Qwen OCR task.

Design goals:
1) Keep API contract stable: POST /api/ocr/analyze, GET /api/ocr/config.
2) Qwen-only: every accepted image is sent through native Qwen OCR.
3) AI is text-only OCR. Field parsing, MRZ parsing, side detection, and pairing
   are deterministic in backend — implementation lives in
   services/document_intake/ocr_pipeline.py (shared voi intake service).
4) No fallback waves (no MRZ rescue AI, no chat prompt reasoning loop).
"""

from __future__ import annotations

import asyncio

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from time import perf_counter
from typing import Any

from services.document_intake import ocr_pipeline as _ocr_pipeline
from services.document_intake.ocr_pipeline import *  # noqa: F401,F403
from services.document_intake.ocr_pipeline import (
    _call_qwen_native_ocr_single,
    _should_retry_property_rotate,
)

# Re-export toan bo machinery (ke ca private `_name`) de giu nguyen surface
# `ocr_ai.<name>` cho tests, routers/zalo_inbox.py va sidecar adapter.
for _name in dir(_ocr_pipeline):
    if _name.startswith("_") and not _name.startswith("__"):
        globals()[_name] = getattr(_ocr_pipeline, _name)
del _name


router = APIRouter(tags=["OCR"])


async def _process_single_image(
    upload: UploadFile,
    *,
    model: str,
    api_key: str,
    ai_semaphore: asyncio.Semaphore,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    filename = upload.filename or "unknown"
    file_bytes = await upload.read()
    return await _ocr_pipeline.process_image_bytes(
        file_bytes,
        filename,
        model=model,
        api_key=api_key,
        ai_semaphore=ai_semaphore,
        client=client,
        ocr_call=_call_qwen_native_ocr_single,
    )


async def _process_single_property_image(
    upload: UploadFile,
    *,
    model: str,
    api_key: str,
    ai_semaphore: asyncio.Semaphore,
    client: httpx.AsyncClient,
    side: str = "unknown",
    enable_footer_date_rescue: bool = True,
) -> dict[str, Any]:
    filename = upload.filename or "unknown"
    file_bytes = await upload.read()
    return await _ocr_pipeline.process_property_image_bytes(
        file_bytes,
        filename,
        model=model,
        api_key=api_key,
        ai_semaphore=ai_semaphore,
        client=client,
        side=side,
        enable_footer_date_rescue=enable_footer_date_rescue,
        ocr_call=_call_qwen_native_ocr_single,
        should_retry=_should_retry_property_rotate,
    )


def shape_cached_ocr(raw_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Rebuild the OCR response from stored Qwen documents without a model call."""
    persons: list[dict[str, Any]] = []
    properties: list[dict[str, Any]] = []
    marriages: list[dict[str, Any]] = []
    shaped_raw: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for raw in raw_results:
        if not isinstance(raw, dict):
            errors.append({"filename": "unknown", "error": "Invalid cached OCR result", "stage": "parse"})
            continue
        filename = _clean_text(raw.get("input_item_id") or raw.get("filename")) or "unknown"
        lines = raw.get("text_lines") if isinstance(raw.get("text_lines"), list) else []
        try:
            doc = _normalize_native_ocr_doc(lines, filename)
            _append_ai_doc(doc=doc, persons=persons, properties=properties, raw_results=shaped_raw)
            shaped_raw[-1] = {**raw, **shaped_raw[-1], "filename": filename, "source_type": "AI", "status": "ok"}
        except Exception as exc:
            shaped_raw.append(
                {**raw, "filename": filename, "doc_type": "unknown", "text_lines": lines, "status": "error", "source_type": "AI"}
            )
            errors.append({"filename": filename, "error": str(exc), "stage": "parse"})

    try:
        persons = _pair_persons(persons)
    except Exception as exc:
        errors.append({"filename": "batch", "error": str(exc), "stage": "pair"})
    unknowns = sum(1 for item in shaped_raw if item.get("doc_type") == "unknown")
    return {
        "persons": persons,
        "properties": properties,
        "marriages": marriages,
        "raw_results": shaped_raw,
        "errors": errors,
        "summary": {
            "total_images": len(shaped_raw),
            "model": "cached",
            "qr_hits": 0,
            "ai_runs": 0,
            "ocr_runs": 0,
            "ai_started": 0,
            "ai_selected": 0,
            "ai_discarded_by_qr": 0,
            "persons": len(persons),
            "paired_persons": sum(1 for person in persons if person.get("paired")),
            "properties": len(properties),
            "marriages": len(marriages),
            "unknowns": unknowns,
            "ocr_native_ms": 0.0,
            "backend_parse_ms": 0.0,
            "pair_ms": 0.0,
            "total_ms": 0.0,
        },
    }


@router.post("/analyze")
async def analyze_images(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No images uploaded")

    t_total = perf_counter()
    t_ocr_start = perf_counter()

    persons: list[dict[str, Any]] = []
    properties: list[dict[str, Any]] = []
    marriages: list[dict[str, Any]] = []
    raw_results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    model = _get_model()
    api_key = _get_api_key()
    ai_semaphore = asyncio.Semaphore(OCR_AI_CONCURRENCY)

    results: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
        tasks = [
            _process_single_image(
                upload,
                model=model,
                api_key=api_key,
                ai_semaphore=ai_semaphore,
                client=client,
            )
            for upload in files
        ]
        for item in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(item, Exception):
                errors.append({"filename": "unknown", "error": str(item)})
            else:
                results.append(item)

    ocr_native_ms = perf_counter() - t_ocr_start
    ai_started = len(files)
    ai_selected = 0

    t_parse_start = perf_counter()
    for item in results:
        filename = item["filename"]
        if item.get("error"):
            stage = str(item.get("error_stage") or "model")
            errors.append({"filename": filename, "error": str(item["error"]), "stage": stage})
            if item.get("raw_lines"):
                raw_results.append(
                    {
                        "filename": filename,
                        "doc_type": "unknown",
                        "text_lines": list(item["raw_lines"]),
                        "source_type": "AI",
                        "status": "error",
                    }
                )
            continue

        doc = item.get("ai_doc")
        if isinstance(doc, dict):
            ai_selected += 1
            _append_ai_doc(doc=doc, persons=persons, properties=properties, raw_results=raw_results)
        else:
            errors.append({"filename": filename, "error": "No OCR result"})

    backend_parse_ms = perf_counter() - t_parse_start

    t_pair_start = perf_counter()
    try:
        persons = _pair_persons(persons)
    except Exception as exc:
        errors.append({"filename": "batch", "error": str(exc), "stage": "pair"})
    pair_ms = perf_counter() - t_pair_start

    unknowns = sum(1 for item in raw_results if item.get("doc_type") == "unknown")
    paired_count = sum(1 for person in persons if person.get("paired"))
    total_ms = perf_counter() - t_total

    _log_ocr_ai(
        "ocr_ai_done",
        model=model,
        images=len(files),
        total_ms=_ms(total_ms),
        ocr_native_ms=_ms(ocr_native_ms),
        backend_parse_ms=_ms(backend_parse_ms),
        pair_ms=_ms(pair_ms),
        ai_runs=ai_selected,
        errors=len(errors),
    )

    return {
        "persons": persons,
        "properties": properties,
        "marriages": marriages,
        "raw_results": raw_results,
        "errors": errors,
        "summary": {
            "total_images": len(files),
            "model": model,
            "qr_hits": 0,
            "ai_runs": ai_started,
            "ocr_runs": ai_started,
            "ai_started": ai_started,
            "ai_selected": ai_selected,
            "ai_discarded_by_qr": 0,
            "persons": len(persons),
            "paired_persons": paired_count,
            "properties": len(properties),
            "marriages": len(marriages),
            "unknowns": unknowns,
            "ocr_native_ms": _ms(ocr_native_ms),
            "backend_parse_ms": _ms(backend_parse_ms),
            "pair_ms": _ms(pair_ms),
            "total_ms": _ms(total_ms),
        },
    }


@router.post("/analyze-property")
async def analyze_property_images(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No images uploaded")

    t_total = perf_counter()
    properties: list[dict[str, Any]] = []
    raw_results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    model = _get_model()
    api_key = _get_api_key()
    ai_semaphore = asyncio.Semaphore(OCR_AI_CONCURRENCY)

    results: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
        tasks = [
            _process_single_property_image(
                upload,
                model=model,
                api_key=api_key,
                ai_semaphore=ai_semaphore,
                client=client,
                side="unknown",
            )
            for upload in files
        ]
        for item in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(item, Exception):
                detail = item.detail if isinstance(item, HTTPException) else str(item)
                errors.append({"filename": "unknown", "error": str(detail)})
            else:
                results.append(item)

    used_rotate_retry = 0
    used_footer_date_rescue = 0
    unknowns = 0
    for item in results:
        filename = str(item.get("filename") or "unknown")
        doc = item.get("doc") if isinstance(item.get("doc"), dict) else {}
        used_rotate_retry += 1 if item.get("used_rotate_retry") else 0
        used_footer_date_rescue += 1 if item.get("used_footer_date_rescue") else 0
        if not doc:
            errors.append({"filename": filename, "error": "No OCR result"})
            continue

        doc_type = str(doc.get("doc_type") or "unknown")
        data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
        warnings = doc.get("warnings") if isinstance(doc.get("warnings"), list) else []
        missing_fields = doc.get("missing_fields") if isinstance(doc.get("missing_fields"), list) else []
        raw_results.append(
            {
                "doc_type": doc_type,
                "filename": filename,
                "side": "unknown",
                "source_type": "AI",
                "data": data,
                "text_lines": doc.get("text_lines") if isinstance(doc.get("text_lines"), list) else [],
                "warnings": warnings,
                "missing_fields": missing_fields,
                "status": "ok" if doc_type == "property" else "skipped",
            }
        )
        if doc_type == "property":
            properties.append(
                {
                    **data,
                    "_file": filename,
                    "_source": "AI",
                    "source_type": "AI",
                    "warnings": warnings,
                    "missing_fields": missing_fields,
                }
            )
        else:
            unknowns += 1

    total_ms = perf_counter() - t_total
    _log_ocr_ai(
        "ocr_property_done",
        model=model,
        images=len(files),
        properties=len(properties),
        unknowns=unknowns,
        errors=len(errors),
        rotate_retry=used_rotate_retry,
        footer_date_rescue=used_footer_date_rescue,
        total_ms=_ms(total_ms),
    )
    return {
        "persons": [],
        "properties": properties,
        "marriages": [],
        "raw_results": raw_results,
        "errors": errors,
        "summary": {
            "total_images": len(files),
            "model": model,
            "persons": 0,
            "properties": len(properties),
            "marriages": 0,
            "unknowns": unknowns,
            "rotate_retry": used_rotate_retry,
            "footer_date_rescue": used_footer_date_rescue,
            "total_ms": _ms(total_ms),
        },
    }


@router.post("/analyze-property-pair")
async def analyze_property_pair(
    front_file: UploadFile = File(...),
    back_file: UploadFile = File(...),
):
    t_total = perf_counter()
    model = _get_model()
    api_key = _get_api_key()
    ai_semaphore = asyncio.Semaphore(OCR_AI_CONCURRENCY)

    errors: list[dict[str, Any]] = []
    front_result: dict[str, Any] | None = None
    back_result: dict[str, Any] | None = None

    async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
        tasks = [
            _process_single_property_image(
                front_file,
                model=model,
                api_key=api_key,
                ai_semaphore=ai_semaphore,
                client=client,
                side="front",
                enable_footer_date_rescue=False,
            ),
            _process_single_property_image(
                back_file,
                model=model,
                api_key=api_key,
                ai_semaphore=ai_semaphore,
                client=client,
                side="back",
                enable_footer_date_rescue=False,
            ),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, item in enumerate(results):
            side = "front" if idx == 0 else "back"
            filename = front_file.filename if side == "front" else back_file.filename
            safe_filename = str(filename or f"{side}.jpg")
            if isinstance(item, Exception):
                detail = item.detail if isinstance(item, HTTPException) else str(item)
                errors.append({"side": side, "filename": safe_filename, "error": str(detail)})
                continue
            if side == "front":
                front_result = item
            else:
                back_result = item

    front_doc = (
        (front_result or {}).get("doc")
        if isinstance((front_result or {}).get("doc"), dict)
        else {"doc_type": "unknown", "side": "front", "data": {}, "filename": str(front_file.filename or "front.jpg")}
    )
    back_doc = (
        (back_result or {}).get("doc")
        if isinstance((back_result or {}).get("doc"), dict)
        else {"doc_type": "unknown", "side": "back", "data": {}, "filename": str(back_file.filename or "back.jpg")}
    )

    merged = _merge_property_pair(front_doc, back_doc)
    property_data = {
        **{k: merged.get(k, "") for k in _PROPERTY_FORM_FIELDS},
        "land_rows": merged.get("land_rows") if isinstance(merged.get("land_rows"), list) else [],
        "field_sources": merged.get("field_sources") if isinstance(merged.get("field_sources"), dict) else {},
        "missing_fields": merged.get("missing_fields") if isinstance(merged.get("missing_fields"), list) else [],
        "warnings": merged.get("warnings") if isinstance(merged.get("warnings"), list) else [],
        "_source": "AI",
        "source_type": "AI",
        "_files": [
            str(front_doc.get("filename") or front_file.filename or "front.jpg"),
            str(back_doc.get("filename") or back_file.filename or "back.jpg"),
        ],
    }

    per_side = {
        "front": {
            "file": str(front_doc.get("filename") or front_file.filename or "front.jpg"),
            "doc_type": str(front_doc.get("doc_type") or "unknown"),
            "data": front_doc.get("data") if isinstance(front_doc.get("data"), dict) else {},
            "warnings": front_doc.get("warnings") if isinstance(front_doc.get("warnings"), list) else [],
            "missing_fields": front_doc.get("missing_fields") if isinstance(front_doc.get("missing_fields"), list) else [],
            "status": "ok" if str(front_doc.get("doc_type") or "") == "property" else "skipped",
            "text_lines": front_doc.get("text_lines") if isinstance(front_doc.get("text_lines"), list) else [],
        },
        "back": {
            "file": str(back_doc.get("filename") or back_file.filename or "back.jpg"),
            "doc_type": str(back_doc.get("doc_type") or "unknown"),
            "data": back_doc.get("data") if isinstance(back_doc.get("data"), dict) else {},
            "warnings": back_doc.get("warnings") if isinstance(back_doc.get("warnings"), list) else [],
            "missing_fields": back_doc.get("missing_fields") if isinstance(back_doc.get("missing_fields"), list) else [],
            "status": "ok" if str(back_doc.get("doc_type") or "") == "property" else "skipped",
            "text_lines": back_doc.get("text_lines") if isinstance(back_doc.get("text_lines"), list) else [],
        },
    }

    total_ms = perf_counter() - t_total
    _log_ocr_ai(
        "ocr_property_pair_done",
        model=model,
        front_file=per_side["front"]["file"],
        back_file=per_side["back"]["file"],
        front_doc_type=per_side["front"]["doc_type"],
        back_doc_type=per_side["back"]["doc_type"],
        missing_fields=len(property_data.get("missing_fields") or []),
        errors=len(errors),
        total_ms=_ms(total_ms),
    )

    return {
        "property": property_data,
        "per_side": per_side,
        "warnings": property_data.get("warnings") or [],
        "missing_fields": property_data.get("missing_fields") or [],
        "summary": {
            "model": model,
            "total_ms": _ms(total_ms),
            "errors": len(errors),
            "front_doc_type": per_side["front"]["doc_type"],
            "back_doc_type": per_side["back"]["doc_type"],
        },
        "errors": errors,
    }


@router.get("/config")
async def ocr_config():
    model = _get_model()
    configured = bool(_get_api_key())
    return {
        "configured": configured,
        "model": model,
        "provider": "qwen_native_ocr" if "qwen" in model.lower() else "other",
        "max_image_px": AI_MAX_IMAGE_PX,
        "ocr_ai_concurrency": OCR_AI_CONCURRENCY,
        "qwen_ocr": {
            "base_url": QWEN_OCR_BASE_URL,
            "min_pixels": QWEN_OCR_MIN_PIXELS,
            "max_pixels": QWEN_OCR_MAX_PIXELS,
            "enable_rotate": QWEN_OCR_ENABLE_ROTATE,
        },
        "pairing": {
            "fuzzy_max_id_mismatch": PAIR_FUZZY_MAX_ID_MISMATCH,
            "fuzzy_name_threshold": PAIR_FUZZY_NAME_THRESHOLD,
        },
    }

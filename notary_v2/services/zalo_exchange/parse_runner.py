"""Parse runner ben vung cho goi raw Zalo da import (MIN-99, slice B).

Moi goi sau khi import duoc enqueue mot `zalo_parse_jobs` row. Runner nay doc
job `pending` (va `failed` — retry duoc o luot sau), load raw records cua goi
tu `zalo_raw_records`, chay deterministic parser cua `ocr_pipeline` tren
text-only transcript va ghi `zalo_intake_results` (revision tang dan).

Bao dam:
- Parser loi KHONG huy ACK raw: job -> failed + error da sanitize, retry tu
  raw da luu; ledger/receipt khong bi cham.
- Khong network/Qwen, khong doc byte/path anh — chi dung `ocr.text_lines` va
  `message.text` da nhap san.
- Ban ghi bi supersede (cung `logical_id`, revision thap hon) khong dua vao
  aggregate person/property — chi ghi marker trong raw_results.
- message_text la ngu canh hoi thoai: van normalize vao raw_results nhung
  khong aggregate len persons/properties (khong phai giay to).
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from sqlalchemy import text as _sa_text
from sqlalchemy.orm import Session

from models import ZaloIntakeResult, ZaloParseJob, ZaloRawRecord
from services.document_intake import ocr_pipeline as _ocr

_logger = logging.getLogger("zalo_exchange.parse_runner")

PARSER_VERSION = "ocr_pipeline-2026-09-24"
_MAX_PARSE_ATTEMPTS = 8
_MAX_ERROR_CHARS = 500


def _sanitize_error(exc: BaseException) -> str:
    """Loi gon cho `zalo_parse_jobs.error` — khong stack trace, cat ngan."""
    message = f"{type(exc).__name__}: {exc}"
    message = " ".join(str(message).split())
    return message[:_MAX_ERROR_CHARS]


def _record_payload(record: ZaloRawRecord) -> dict[str, Any]:
    try:
        payload = json.loads(record.payload_json)
    except (TypeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _transcript_lines(payload: dict[str, Any]) -> list[str]:
    """Text lines cua default transcript cho ocr_page.

    `ocr.text_lines` la flat list, moi dong mang `ocr_pass_id`; default
    transcript = cac dong thuoc `selected_pass_ids`. Khi producer khong gui
    selected_pass_ids thi lay toan bo lines (giu thu tu).
    """
    ocr = payload.get("ocr") if isinstance(payload.get("ocr"), dict) else {}
    lines = ocr.get("text_lines") if isinstance(ocr.get("text_lines"), list) else []
    selected_raw = ocr.get("selected_pass_ids")
    selected = (
        {s for s in selected_raw if isinstance(s, str)}
        if isinstance(selected_raw, list)
        else set()
    )
    out: list[str] = []
    for line in lines:
        if not isinstance(line, dict):
            continue
        if selected and line.get("ocr_pass_id") not in selected:
            continue
        text = _ocr._clean_text(line.get("text"))
        if text:
            out.append(text)
    return out


def _message_lines(payload: dict[str, Any]) -> list[str]:
    message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
    text = message.get("text") if isinstance(message.get("text"), str) else ""
    return [ln for ln in (part.strip() for part in text.splitlines()) if ln]


def _record_label(record: ZaloRawRecord, payload: dict[str, Any]) -> str:
    """Ten hien thi on dinh cho record — nhan label, KHONG phai path anh."""
    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    page = source.get("page_index")
    suffix = f":p{page}" if isinstance(page, int) and page > 0 else ""
    return f"zalo:{record.record_id[:8]}{suffix}"


def _latest_per_logical(records: list[ZaloRawRecord]) -> tuple[list[ZaloRawRecord], list[ZaloRawRecord]]:
    """Giu record moi nhat theo (logical_id, revision desc); con lai la superseded."""
    latest: dict[str, ZaloRawRecord] = {}
    order: list[str] = []
    superseded: list[ZaloRawRecord] = []
    for record in records:
        prev = latest.get(record.logical_id)
        if prev is None:
            latest[record.logical_id] = record
            order.append(record.logical_id)
            continue
        if record.revision > prev.revision:
            superseded.append(prev)
            latest[record.logical_id] = record
        else:
            superseded.append(record)
    return [latest[key] for key in order], superseded


def _append_zalo_doc(
    *,
    doc: dict[str, Any],
    persons: list[dict[str, Any]],
    property_docs: list[dict[str, Any]],
) -> None:
    """Dua doc da parse vao list aggregate (person) hoac property_docs."""
    if doc.get("doc_type") == "property":
        property_docs.append(doc)
        return
    if doc.get("doc_type") != "person":
        return
    data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
    persons.append(
        {
            **data,
            "_source": "zalo",
            "source_type": "zalo",
            "side": doc.get("side", "unknown"),
            "_files": [doc.get("filename") or "unknown"],
            "_qr": False,
            "field_sources": _ocr._field_sources(data, "zalo"),
            "warnings": list(doc.get("warnings") or []),
            "_raw_text": "\n".join(doc.get("text_lines") or []),
        }
    )


def _merge_property_docs(property_docs: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Gop cac trang GCN thanh mot property bang _merge_property_pair cua pipeline.

    >2 trang: fold tuan tu — ket qua merge truoc lam "front" cho vong sau.
    """
    if not property_docs:
        return None
    first = property_docs[0]
    data = first.get("data") if isinstance(first.get("data"), dict) else {}
    merged: dict[str, Any] = {
        **data,
        "field_sources": {
            key: "zalo" for key, value in data.items() if _ocr._property_has_value(value)
        },
        "missing_fields": list(first.get("missing_fields") or []),
        "warnings": list(first.get("warnings") or []),
    }
    files = [first.get("filename") or "unknown"]
    for doc in property_docs[1:]:
        merged = _ocr._merge_property_pair(
            {"doc_type": "property", "data": merged},
            {"doc_type": doc.get("doc_type") or "unknown", "data": doc.get("data") if isinstance(doc.get("data"), dict) else {}},
        )
        files.append(doc.get("filename") or "unknown")
    merged["_files"] = files
    merged["_source"] = "zalo"
    merged["source_type"] = "zalo"
    return merged


def _build_package_result(package_id: str, records: list[ZaloRawRecord]) -> dict[str, Any]:
    """Parse toan bo raw records cua mot package -> result_json payload."""
    persons: list[dict[str, Any]] = []
    property_docs: list[dict[str, Any]] = []
    raw_results: list[dict[str, Any]] = []
    warnings: list[str] = []

    latest_records, superseded = _latest_per_logical(records)

    for record in superseded:
        raw_results.append(
            {
                "record_id": record.record_id,
                "logical_id": record.logical_id,
                "revision": record.revision,
                "record_kind": record.kind,
                "status": "superseded",
            }
        )

    for record in latest_records:
        payload = _record_payload(record)
        label = _record_label(record, payload)
        kind = record.kind or str(payload.get("record_kind") or "")

        if kind == "ocr_page":
            ocr = payload.get("ocr") if isinstance(payload.get("ocr"), dict) else {}
            ocr_status = str(ocr.get("status") or "")
            lines = _transcript_lines(payload)
            if not lines:
                status = "ocr_failed" if ocr_status == "failed" else "no_text_lines"
                warnings.append(f"{status}:{record.record_id[:8]}")
                raw_results.append(
                    {
                        "record_id": record.record_id,
                        "logical_id": record.logical_id,
                        "revision": record.revision,
                        "record_kind": kind,
                        "filename": label,
                        "doc_type": "unknown",
                        "text_lines": [],
                        "status": status,
                    }
                )
                continue
            doc = _ocr._normalize_native_ocr_doc(lines, label)
            raw_results.append(
                {
                    **doc,
                    "record_id": record.record_id,
                    "logical_id": record.logical_id,
                    "revision": record.revision,
                    "record_kind": kind,
                    "filename": label,
                    "status": "ok" if doc.get("doc_type") != "unknown" else "skipped",
                }
            )
            _append_zalo_doc(doc=doc, persons=persons, property_docs=property_docs)
            continue

        if kind == "message_text":
            lines = _message_lines(payload)
            doc = _ocr._normalize_native_ocr_doc(lines, label) if lines else {
                "doc_type": "message",
                "side": "unknown",
                "data": {},
                "filename": label,
                "text_lines": [],
            }
            raw_results.append(
                {
                    **doc,
                    "record_id": record.record_id,
                    "logical_id": record.logical_id,
                    "revision": record.revision,
                    "record_kind": kind,
                    "filename": label,
                    "status": "message",
                }
            )
            continue

        # Cac record_kind khac (listener_event, source_event, ...) giu nguyen
        # marker — khong phai trang giay to.
        raw_results.append(
            {
                "record_id": record.record_id,
                "logical_id": record.logical_id,
                "revision": record.revision,
                "record_kind": kind or "unknown",
                "status": "not_document",
            }
        )

    try:
        persons = _ocr._pair_persons(persons)
    except Exception as exc:  # pair loi khong lam mat ket qua per-page
        warnings.append(f"pair_error:{_sanitize_error(exc)}")

    # _merge_person_group hardcode _source="AI"; ket qua nay den tu goi Zalo.
    for person in persons:
        person["_source"] = "zalo"
        person["source_type"] = "zalo"

    merged_property = _merge_property_docs(property_docs)
    properties = [merged_property] if merged_property else []

    return {
        "package_id": package_id,
        "persons": persons,
        "properties": properties,
        "raw_results": raw_results,
        "warnings": warnings,
        "record_count": len(records),
        "superseded_count": len(superseded),
    }


def _run_one_parse_job(db: Session, job: ZaloParseJob) -> None:
    job_id = job.job_id
    package_id = job.package_id
    job.state = "running"
    job.attempts = (job.attempts or 0) + 1
    db.commit()

    try:
        records = (
            db.query(ZaloRawRecord)
            .filter(ZaloRawRecord.package_id == package_id)
            .order_by(_sa_text("rowid"))
            .all()
        )
        result = _build_package_result(package_id, records)
    except Exception as exc:
        db.rollback()
        fresh = db.get(ZaloParseJob, job_id)
        if fresh is not None:
            fresh.state = "failed"
            fresh.error = _sanitize_error(exc)
            db.commit()
        _logger.warning("zalo parse job %s failed: %s", job_id, _sanitize_error(exc))
        return

    revision = (
        db.query(ZaloIntakeResult)
        .filter(ZaloIntakeResult.package_id == package_id)
        .count()
        + 1
    )
    db.add(
        ZaloIntakeResult(
            result_id=str(uuid.uuid4()),
            package_id=package_id,
            revision=revision,
            parser_version=PARSER_VERSION,
            result_json=json.dumps(result, ensure_ascii=False),
            warnings_json=json.dumps(result["warnings"], ensure_ascii=False),
        )
    )
    job.state = "succeeded"
    job.error = None
    db.commit()


def run_pending_parse_jobs(db: Session, *, limit: int | None = None) -> int:
    """Chay cac parse job pending/failed (retry). Tra so job da xu ly luot nay.

    `_run_one_parse_job` commit `running` truoc khi lam viec: crash o giua de
    job wedge mai o `running`. Runner chi co mot tien trinh nen row `running`
    tai entry la do phien truoc de lai — reclaim ve pending. Job `failed`
    vuot `_MAX_PARSE_ATTEMPTS` giu nguyen de quan sat, khong retry nua.
    """
    stale = db.query(ZaloParseJob).filter(ZaloParseJob.state == "running").all()
    for row in stale:
        row.state = "pending"
    if stale:
        db.commit()
    jobs = (
        db.query(ZaloParseJob)
        .filter(
            (ZaloParseJob.state == "pending")
            | (
                (ZaloParseJob.state == "failed")
                & (ZaloParseJob.attempts < _MAX_PARSE_ATTEMPTS)
            )
        )
        .order_by(ZaloParseJob.created_at.asc(), ZaloParseJob.job_id.asc())
        .all()
    )
    processed = 0
    for job in jobs:
        if limit is not None and processed >= limit:
            break
        _run_one_parse_job(db, job)
        processed += 1
    return processed

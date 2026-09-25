"""Router /api/zalo — consumer phia may chinh cho module Zalo intake (MIN-99).

Surface:
- POST   /api/zalo/sync                          chay run_sync + drain parse jobs
- GET    /api/zalo/sync/state                    cursor + ledger/parse counts
- POST   /api/zalo/ocr-requests                  tao intake.ocr-request.v1
- GET    /api/zalo/ocr-requests/{request_id}     doc intake.ocr-request-status.v1
- GET    /api/zalo/results?package_id=           zalo_intake_results da luu

Loi duoc tra theo convention codebase: HTTPException(status_code, detail).
Module Zalo khong reachable -> 503; module tu choi (intake.error.v1) -> 502
voi detail {"code","message"}. Core sync (slice A) duoc import lazy ben trong
ham de router van load duoc khi services/zalo_exchange/{client,sync}.py chua co.
"""

from __future__ import annotations

import dataclasses
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import (
    ZaloImportLedger,
    ZaloIntakeResult,
    ZaloParseJob,
    ZaloRawRecord,
    ZaloSyncState,
)

router = APIRouter(prefix="/api/zalo", tags=["zalo-exchange"])

_OCR_VARIANTS = {"rotate", "crop_bottom", "full_res"}
_OCR_REASON_CODES = {
    "missing_issue_date",
    "missing_identity_number",
    "missing_parcel_info",
    "suspected_rotation",
    "insufficient_text",
    "truncated_footer",
    "other",
}
_CROP_PRESETS = {"bottom_quarter", "bottom_third", "bottom_42pct"}
_OCR_REQUEST_FIELDS = {
    "schema_version",
    "request_id",
    "consumer_id",
    "logical_id",
    "variant",
    "preset",
    "reason_code",
    "note",
    "observed_revision",
    "submitted_at",
}


# ---------------------------------------------------------------------------
# Cau hinh tu env (decision sheet MIN-99 §Environment)
# ---------------------------------------------------------------------------


def _module_url() -> str:
    return os.getenv("ZALO_MODULE_URL", "http://127.0.0.1:8765").rstrip("/")


def _api_token() -> str | None:
    return os.getenv("ZALO_INTAKE_API_TOKEN") or None


def _consumer_id() -> str:
    return os.getenv("ZALO_CONSUMER_ID", "").strip()


def _exchange_root() -> Path:
    env = os.getenv("ZALO_EXCHANGE_ROOT")
    if env:
        return Path(env)
    # Mac dinh neo vao repo root, khong phu thuoc CWD luc chay app.
    return Path(__file__).resolve().parents[1] / "data" / "zalo_exchange"


def _sync_interval_seconds() -> float:
    try:
        return float(os.getenv("ZALO_SYNC_INTERVAL_SECONDS", "300"))
    except ValueError:
        return 300.0


# ---------------------------------------------------------------------------
# Lazy seam toi slice A — services/zalo_exchange/{client,sync}.py
# ---------------------------------------------------------------------------


def _intake_client():
    """Tao IntakeClient theo env; lazy import de router load duoc truoc slice A."""
    try:
        from services.zalo_exchange.client import IntakeClient
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "exchange_unavailable", "message": f"Zalo exchange core chua san sang: {exc}"},
        ) from exc
    return IntakeClient(base_url=_module_url(), token=_api_token())


def _raise_client_http(exc: Exception) -> None:
    """Map loi IntakeClient/transport -> HTTPException (convention codebase)."""
    try:
        from services.zalo_exchange.client import IntakeClientError
    except Exception:
        IntakeClientError = None  # slice A chua merge — chi con transport errors
    if IntakeClientError is not None and isinstance(exc, IntakeClientError):
        code = str(getattr(exc, "code", "intake_error") or "intake_error")
        message = str(getattr(exc, "message", "") or exc)
        raise HTTPException(status_code=502, detail={"code": code, "message": message}) from exc
    if isinstance(exc, httpx.HTTPError):
        raise HTTPException(
            status_code=503,
            detail={"code": "module_unreachable", "message": str(exc)},
        ) from exc
    raise HTTPException(
        status_code=500,
        detail={"code": "internal", "message": str(exc)[:300]},
    ) from exc


def _build_sync_settings(core: Any) -> Any:
    """Dung SyncSettings tu env (fields da chot o services/zalo_exchange/sync.py)."""
    values = {
        "module_url": _module_url(),
        "token": _api_token(),
        "consumer_id": _consumer_id(),
        "exchange_root": _exchange_root(),
        "timeout": 30.0,
    }
    cls = getattr(core, "SyncSettings", None)
    return cls(**values) if cls is not None else SimpleNamespace(**values)


def _report_payload(report: Any) -> dict[str, Any]:
    """SyncReport -> dict (dataclass/pydantic/dict deu chap nhan)."""
    if report is None:
        return {}
    if dataclasses.is_dataclass(report) and not isinstance(report, type):
        return dataclasses.asdict(report)
    dump = getattr(report, "model_dump", None)
    if callable(dump):
        return dump()
    if isinstance(report, dict):
        return dict(report)
    data = getattr(report, "__dict__", None)
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if not k.startswith("_")}
    return {"report": str(report)}


_sync_lock = threading.Lock()


def run_sync_once(db: Session) -> dict[str, Any]:
    """Mot luot sync + drain parse jobs. Dung chung POST /sync va periodic task.

    Contract §7.2.5: mot luot active tai mot thoi diem. Luot thu hai bo qua
    nhe nhang (khong doi) — staging/ready dung chung, hai luot song song co
    the xoa staging dang download -> quarantine oan.
    """
    if not _sync_lock.acquire(blocking=False):
        return {"already_running": True}
    try:
        try:
            from services.zalo_exchange import sync as zalo_sync_core
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail={"code": "sync_unavailable", "message": f"Zalo exchange core chua san sang: {exc}"},
            ) from exc

        settings = _build_sync_settings(zalo_sync_core)
        try:
            report = zalo_sync_core.run_sync(db, settings)
        except HTTPException:
            raise
        except Exception as exc:
            _raise_client_http(exc)
            raise  # pragma: no cover — _raise_client_http luon raise

        payload: dict[str, Any] = {"report": _report_payload(report)}
        try:
            from services.zalo_exchange import parse_runner

            payload["parse_jobs_processed"] = parse_runner.run_pending_parse_jobs(db)
        except Exception as exc:  # parse loi khong lam mat thanh cong cua import
            payload["parse_error"] = str(exc)[:300]
        return payload
    finally:
        _sync_lock.release()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/sync")
def sync_now(db: Session = Depends(get_db)):
    """Nút Sync thu cong — chay run_sync dong bo roi drain parse jobs."""
    return run_sync_once(db)


@router.get("/sync/state")
def sync_state(db: Session = Depends(get_db)):
    """Trang thai sync loop: kv cursor + dem ledger/raw/parse_jobs/results."""
    state: dict[str, Any] = {}
    for row in db.query(ZaloSyncState).all():
        try:
            state[row.key] = json.loads(row.value)
        except (TypeError, json.JSONDecodeError):
            state[row.key] = row.value

    parse_counts: dict[str, int] = {"pending": 0, "running": 0, "succeeded": 0, "failed": 0}
    for job in db.query(ZaloParseJob).all():
        parse_counts[job.state] = parse_counts.get(job.state, 0) + 1

    ledger_rows = db.query(ZaloImportLedger).all()
    return {
        "module_url": _module_url(),
        "consumer_id": _consumer_id(),
        "exchange_root": str(_exchange_root()),
        "sync_interval_seconds": _sync_interval_seconds(),
        "state": state,
        "cursor": state.get("last_sequence"),
        "last_run_at": state.get("last_run_at"),
        "last_error": state.get("last_error"),
        "ledger": {
            "total": len(ledger_rows),
            "imported": sum(1 for row in ledger_rows if row.decision == "imported"),
            "quarantined": sum(1 for row in ledger_rows if row.decision == "quarantined"),
            "receipts_pending": sum(1 for row in ledger_rows if not row.receipt_status),
        },
        "raw_records": db.query(ZaloRawRecord).count(),
        "parse_jobs": parse_counts,
        "results": db.query(ZaloIntakeResult).count(),
    }


def _bad_request(message: str) -> None:
    raise HTTPException(status_code=400, detail=message)


def _validate_ocr_request(body: Any) -> dict[str, Any]:
    """Validate toi thieu intake.ocr-request.v1 phia consumer truoc khi proxy.

    Khong can jsonschema: kiem required + enum + uuid format + rule preset.
    request_id/submitted_at/consumer_id tu sinh khi thieu (manual button).
    """
    if body is None:
        body = {}
    if not isinstance(body, dict):
        _bad_request("Body phai la JSON object")

    extra = sorted(set(body) - _OCR_REQUEST_FIELDS)
    if extra:
        _bad_request(f"Truong khong thuoc intake.ocr-request.v1: {', '.join(extra)}")

    req = dict(body)
    req["schema_version"] = "intake.ocr-request.v1"
    if not req.get("request_id"):
        req["request_id"] = str(uuid.uuid4())
    if not req.get("consumer_id"):
        req["consumer_id"] = _consumer_id()
    if not req.get("submitted_at"):
        req["submitted_at"] = datetime.now(timezone.utc).isoformat()

    for field in ("request_id", "consumer_id", "logical_id", "variant", "reason_code", "observed_revision", "submitted_at"):
        if req.get(field) in (None, ""):
            _bad_request(f"Thieu truong {field}")

    for field in ("request_id", "consumer_id", "logical_id"):
        try:
            uuid.UUID(str(req[field]))
        except (ValueError, AttributeError, TypeError):
            _bad_request(f"{field} phai la uuid")

    if req["variant"] not in _OCR_VARIANTS:
        _bad_request("variant phai la mot trong: rotate, crop_bottom, full_res")
    if req["reason_code"] not in _OCR_REASON_CODES:
        _bad_request("reason_code khong hop le")
    if not isinstance(req["observed_revision"], int) or isinstance(req["observed_revision"], bool) or req["observed_revision"] < 1:
        _bad_request("observed_revision phai la so nguyen >= 1")
    if not isinstance(req["submitted_at"], str):
        _bad_request("submitted_at phai la chuoi ISO datetime")

    preset = req.get("preset")
    if req["variant"] == "crop_bottom":
        if preset not in _CROP_PRESETS:
            _bad_request("crop_bottom yeu cau preset: bottom_quarter | bottom_third | bottom_42pct")
    elif req["variant"] == "rotate":
        if preset not in (None, "auto"):
            _bad_request("rotate chi chap nhan preset 'auto' hoac bo trong")
    elif preset is not None:
        _bad_request("full_res khong nhan preset")

    note = req.get("note")
    if note is not None and (not isinstance(note, str) or len(note) > 500):
        _bad_request("note phai la chuoi <= 500 ky tu")
    if isinstance(note, str) and ("data:" in note or "base64," in note):
        _bad_request("note khong duoc chua data URI/base64")
    return req


@router.post("/ocr-requests")
def create_ocr_request(body: Any = Body(default=None)):
    """Tao yeu cau OCR lai (intake.ocr-request.v1) tren module Zalo."""
    request = _validate_ocr_request(body)
    client = _intake_client()
    try:
        return client.create_ocr_request(request)
    except Exception as exc:
        _raise_client_http(exc)
    finally:
        client.close()


@router.get("/ocr-requests/{request_id}")
def ocr_request_status(request_id: str):
    """Doc lai trang thai OCR re-run request (intake.ocr-request-status.v1)."""
    try:
        uuid.UUID(request_id)
    except ValueError:
        _bad_request("request_id phai la uuid")
    client = _intake_client()
    try:
        return client.get_ocr_request(request_id)
    except Exception as exc:
        _raise_client_http(exc)
    finally:
        client.close()


def _result_payload(row: ZaloIntakeResult) -> dict[str, Any]:
    try:
        result = json.loads(row.result_json)
    except (TypeError, json.JSONDecodeError):
        result = {}
    try:
        warnings = json.loads(row.warnings_json or "[]")
    except (TypeError, json.JSONDecodeError):
        warnings = []
    return {
        "result_id": row.result_id,
        "package_id": row.package_id,
        "revision": row.revision,
        "parser_version": row.parser_version,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "warnings": warnings,
        "result": result,
    }


@router.get("/results")
def intake_results(package_id: str | None = None, db: Session = Depends(get_db)):
    """Ket qua parser da luu. Co package_id -> moi revision; khong -> latest/package."""
    rows = db.query(ZaloIntakeResult).order_by(
        ZaloIntakeResult.package_id.asc(),
        ZaloIntakeResult.revision.desc(),
    ).all()
    if package_id:
        rows = [row for row in rows if row.package_id == package_id]
    else:
        latest: dict[str, ZaloIntakeResult] = {}
        for row in rows:
            latest.setdefault(row.package_id, row)
        rows = list(latest.values())
    return {"results": [_result_payload(row) for row in rows]}

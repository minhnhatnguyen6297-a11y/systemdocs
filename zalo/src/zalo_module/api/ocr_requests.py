"""OCR re-run request API — ``/intake/v1/ocr-requests`` (contract §9).

Scaffold scope: strict JSON parsing, schema_version/required-field checks,
variant+preset matrix, single-consumer check, request_id idempotency
(same body → stored decision; different body → ``request_conflict``), cheap
source checks (``unknown_source``/``source_not_enabled``/``stale_revision``),
then a durable ``ocr_requests`` row + ``ocr_request`` job. Responses are
``intake.ocr-request-status.v1``; errors are ``intake.error.v1``.
"""

from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select

from zalo_module.api._json import StrictJsonError, parse_strict_body
from zalo_module.database import get_engine, session_scope
from zalo_module.models import Job, OcrRequest, Source
from zalo_module.settings import get_settings

router = APIRouter(prefix="/intake/v1")

REASON_CODES = {
    "missing_issue_date",
    "missing_identity_number",
    "missing_parcel_info",
    "suspected_rotation",
    "insufficient_text",
    "truncated_footer",
    "other",
}
CROP_PRESETS = {"bottom_quarter", "bottom_third", "bottom_42pct"}
BODY_LIMIT = 16 * 1024  # contract §3.6

# jobs.state (worker enum) → intake.ocr-request-status.v1 state enum.
_JOB_STATE_MAP = {
    "queued": "queued",
    "running": "running",
    "retry_wait": "running",
    "succeeded": "completed",
    "failed": "failed",
    "expired": "failed",
}

_engines: dict = {}


def _deps(request: Request):
    """Resolve ``(settings, engine)`` — same convention as api.intake."""
    app = request.app
    settings = getattr(app.state, "settings", None) or get_settings()
    engine = getattr(app.state, "engine", None) or _engines.get(settings.db_url)
    if engine is None:
        engine = get_engine(settings)
        _engines[settings.db_url] = engine
    return settings, engine


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "schema_version": "intake.error.v1",
            "error": {"code": code, "message": message},
        },
    )


def _canonical_sha256(body: dict) -> str:
    canonical = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _status_doc(row: OcrRequest, session, *, deduplicated: bool) -> dict:
    job = session.get(Job, row.job_id) if row.job_id else None
    state = _JOB_STATE_MAP.get(job.state, row.state) if job else row.state
    doc = {
        "schema_version": "intake.ocr-request-status.v1",
        "request_id": row.request_id,
        "job_id": row.job_id,
        "state": state,
        "attempt": job.attempts if job else 0,
        "max_attempts": job.max_attempts if job else 3,
        "deduplicated": deduplicated,
    }
    if job is not None and job.created_at:
        # accepted_at = producer intake time; the durable job row timestamp is
        # the closest stored value in scaffold (no dedicated column yet).
        doc["accepted_at"] = job.created_at
    return doc


def _validate_body(body: dict) -> JSONResponse | None:
    """Screening stage — returns an error response or None when clean."""
    if not isinstance(body, dict):
        return _error(400, "schema_invalid", "body must be a JSON object")
    if body.get("schema_version") != "intake.ocr-request.v1":
        return _error(400, "schema_invalid", "schema_version must be intake.ocr-request.v1")
    required = {
        "request_id",
        "consumer_id",
        "logical_id",
        "variant",
        "reason_code",
        "observed_revision",
        "submitted_at",
    }
    if not required.issubset(body):
        return _error(400, "schema_invalid", "missing required request fields")
    if len(body.get("note") or "") > 500:
        return _error(400, "schema_invalid", "note exceeds 500 chars")

    variant = body["variant"]
    preset = body.get("preset")
    if variant == "crop_bottom":
        if preset is None:
            return _error(400, "missing_preset", "crop_bottom requires a preset")
        if preset not in CROP_PRESETS:
            return _error(400, "unsupported_variant", f"unsupported crop_bottom preset {preset!r}")
    elif variant == "rotate":
        if preset not in (None, "auto"):
            return _error(400, "unsupported_variant", "rotate preset must be 'auto' or null")
    elif variant == "full_res":
        if preset is not None:
            return _error(400, "unsupported_variant", "full_res takes no preset")
    else:
        return _error(400, "unsupported_variant", f"unsupported variant {variant!r}")

    if body["reason_code"] not in REASON_CODES:
        return _error(400, "schema_invalid", f"unknown reason_code {body['reason_code']!r}")
    if not isinstance(body["observed_revision"], int) or body["observed_revision"] < 1:
        return _error(400, "schema_invalid", "observed_revision must be an int >= 1")
    return None


@router.post("/ocr-requests")
async def create_ocr_request(request: Request):
    settings, engine = _deps(request)
    raw = await request.body()
    if len(raw) > BODY_LIMIT:
        return _error(413, "request_too_large", "ocr-request body exceeds 16 KiB")
    try:
        body = parse_strict_body(raw)
    except StrictJsonError as exc:
        return _error(400, "json_invalid", str(exc))

    bad = _validate_body(body)
    if bad is not None:
        return bad

    # TODO(MIN-97): recursive request_forbidden_field scan (image/base64/url/
    # prompt/secret key segments and value patterns, contract §9.2).
    # TODO(MIN-97): bearer auth; scaffold trusts the configured consumer only.
    # Fail closed: when no consumer is registered (settings.consumer_id None)
    # every request is unauthorized — never silently accept any consumer_id.
    if not settings.consumer_id or body["consumer_id"] != settings.consumer_id:
        return _error(401, "unauthorized", "consumer_id does not match the registered consumer")

    body_sha = _canonical_sha256(body)

    with session_scope(engine) as session:
        existing = session.get(OcrRequest, body["request_id"])
        if existing is not None:
            if existing.body_canonical_sha256 == body_sha:
                # Idempotent replay — return the stored decision, no re-checks.
                return _status_doc(existing, session, deduplicated=True)
            return _error(409, "request_conflict", "request_id replayed with a different body")

        source = session.get(Source, body["logical_id"])
        if source is None:
            return _error(404, "unknown_source", "logical_id not handed over to this consumer")
        if not source.enabled:
            return _error(409, "source_not_enabled", "source is not enabled")
        if body["observed_revision"] < source.current_revision:
            return _error(409, "stale_revision", "consumer observed an older revision; sync first")

        # TODO(MIN-97): dedupe on (logical_id, variant, preset, config_version)
        # for jobs queued/running/completed; image expiry (source_image_expired)
        # and availability; quota budget_exceeded + rate_limited.
        payload = {
            "request_id": body["request_id"],
            "logical_id": body["logical_id"],
            "variant": body["variant"],
            "preset": body.get("preset"),
            "reason_code": body["reason_code"],
            "observed_revision": body["observed_revision"],
            "config_version": settings.ocr_config_version,
        }
        # Lazy import: jobs.worker is owned by slice C and lands independently;
        # keeping the import inside the endpoint lets this router load early.
        from zalo_module.jobs.worker import enqueue_job

        job_id = enqueue_job(
            "ocr_request",
            payload,
            session,
            logical_id=body["logical_id"],
            request_id=body["request_id"],
            max_attempts=3,
        )
        row = OcrRequest(
            request_id=body["request_id"],
            consumer_id=body["consumer_id"],
            logical_id=body["logical_id"],
            variant=body["variant"],
            preset=body.get("preset"),
            reason_code=body["reason_code"],
            observed_revision=body["observed_revision"],
            submitted_at=body["submitted_at"],
            body_canonical_sha256=body_sha,
            job_id=job_id,
            state="queued",
            deduped_from=None,
        )
        session.add(row)
        session.flush()
        return _status_doc(row, session, deduplicated=False)


@router.get("/ocr-requests/{request_id}")
def get_ocr_request(request: Request, request_id: str):
    settings, engine = _deps(request)
    with session_scope(engine) as session:
        row = session.execute(
            select(OcrRequest).where(OcrRequest.request_id == request_id)
        ).scalar()
        if row is None:
            # Contract §11.4 has no dedicated "request not found" code;
            # unknown_source is the closest catalog-legal value (see report).
            return _error(404, "unknown_source", f"unknown request_id {request_id}")
        return _status_doc(row, session, deduplicated=row.deduped_from is not None)

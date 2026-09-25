"""OCR re-run request API — ``/intake/v1/ocr-requests`` (contract §9).

Accept pipeline follows contract §9.3 stage order:

1. **auth** — bearer token when ``settings.api_token`` is set (router-level
   dependency); body ``consumer_id`` must equal ``settings.consumer_id`` →
   ``unauthorized``.
2. **screening** — strict JSON profile (``json_invalid``), body ≤ 16 KiB
   (``request_too_large``), vendored ``ocr-request.schema.json``
   (``schema_invalid`` / ``unsupported_variant`` / ``missing_preset``) and the
   recursive forbidden-field scan (``request_forbidden_field``), unioned.
3. **source** — ``logical_id`` must exist → ``unknown_source``; disabled →
   ``source_not_enabled``.
4. **idempotent replay** — same ``request_id`` + same canonical body → stored
   decision; different body → ``request_conflict`` envelope.
5. **dedupe** — same ``(logical_id, variant, preset, config_version)`` with an
   active/completed job → persisted deduped row + old job's status.
6. **revision** — ``observed_revision`` older than current → ``stale_revision``.
7. **image lifetime** — past ``captured_at + 168h`` → ``source_image_expired``;
   image not retrievable → ``source_image_unavailable``.
8. **budget** — 2 jobs/key · 100 calls/24h · 2 concurrent →
   ``budget_exceeded`` / ``rate_limited``.
9. **accept** — durable ``ocr_requests`` row + ``ocr_request`` job
   (payload ``{request_id, …}``; execution is slice B's handler).

Stages 3–8 produce *persisted rejections* (contract §9.5): an
``ocr_requests`` row (``state=rejected``) + ledger job id, and the response
is the ``intake.ocr-request-status.v1`` document — so a replayed request_id
returns the same stored decision after a restart. Stages 1–2 and
``request_conflict`` answer with the ``intake.error.v1`` envelope.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import case, func, select

from zalo_module.api._auth import IntakeRoute, require_consumer_auth
from zalo_module.api._json import StrictJsonError, parse_strict_body
from zalo_module.database import get_engine, session_scope
from zalo_module.delivery._schema import load_schema
from zalo_module.models import Job, OcrRequest, Package, Record, Source
from zalo_module.settings import get_settings

router = APIRouter(
    prefix="/intake/v1",
    route_class=IntakeRoute,
    dependencies=[Depends(require_consumer_auth)],
)

BODY_LIMIT = 16 * 1024          # contract §3.6
IMAGE_TTL = timedelta(hours=168)  # contract §8.1
QUOTA_KEY_JOBS = 2              # supplementary jobs per logical_id (§9.6)
QUOTA_DAY_CALLS = 100           # provider calls / consumer / sliding 24 h
QUOTA_CONCURRENT = 2            # simultaneous ocr_request jobs
DAY_WINDOW = timedelta(hours=24)
MAX_ATTEMPTS = 8                # headroom for §9.4 single-flight requeues;
                                # response `attempt` still capped at 3 (§9.5)
_DOC_STATES = ("queued", "running", "completed", "rejected", "failed")
# Job states that still satisfy a dedupe match (contract §9.4):
# queued|running|completed in doc terms, plus retry_wait (still in flight).
_DEDUPE_JOB_STATES = ("queued", "running", "retry_wait", "succeeded")
# Concurrent-budget states: everything that still occupies a worker slot.
_CONCURRENT_JOB_STATES = ("queued", "running", "retry_wait")

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
_request_schema = None


def _schemas_dir() -> Path:
    import os

    return Path(
        os.environ.get("ZALO_INTAKE_SCHEMAS_DIR")
        or (Path(__file__).resolve().parents[3] / "schemas")
    )


def _schema():
    global _request_schema
    if _request_schema is None:
        _request_schema = load_schema(
            _schemas_dir() / "ocr-request.schema.json"
        )
    return _request_schema


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
            "error": {"code": code, "message": message[:500]},
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


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _parse_iso(value) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# request_forbidden_field scan — ported verbatim semantics from
# contracts/zalo-intake/_validator/rules_ocr_request.py (contract §9.2).
# ---------------------------------------------------------------------------

_BANNED_KEY_PARTS = frozenset({
    "image", "base64", "url", "uri", "href", "link",
    "path", "file", "prompt", "token", "secret", "key",
    "password", "credential", "data", "payload", "blob", "bytes",
})
_KEY_SEGMENTS = re.compile(r"[^a-z0-9]+")
_IMAGE_EXT = r"(?:jpe?g|png|gif|bmp|webp|tiff?|heic|heif)"
_RE_IMAGE_REF = re.compile(
    r"\S+\." + _IMAGE_EXT + r"(?:[?#]\S*)?(?=\s|$)", re.I
)
_RE_DATA_URI = re.compile(r"data:\s*[a-z0-9.+-]+/[a-z0-9.+-]+", re.I)
_RE_B64_BLOB = re.compile(r"[A-Za-z0-9+/]{256,}={0,3}")


def _key_banned(key: str) -> bool:
    low = key.lower()
    return any(part in _BANNED_KEY_PARTS for part in _KEY_SEGMENTS.split(low))


def _scan_forbidden(node, out: list) -> None:
    """Append request_forbidden_field findings for banned keys/values."""
    if isinstance(node, dict):
        for key, value in node.items():
            if _key_banned(key):
                out.append(f"/{key}: key name is not allowed in an OCR request")
            _scan_forbidden(value, out)
    elif isinstance(node, list):
        for value in node:
            _scan_forbidden(value, out)
    elif isinstance(node, str):
        if _RE_DATA_URI.search(node):
            out.append("data: URI / inline bytes are not allowed")
        elif _RE_IMAGE_REF.search(node):
            out.append("image URL/path/file name is not allowed")
        elif _RE_B64_BLOB.search(node):
            out.append("base64-looking payload is not allowed")


# ---------------------------------------------------------------------------
# status document — intake.ocr-request-status.v1
# ---------------------------------------------------------------------------


def _result_from_job(session, job: Job) -> dict | None:
    """Resolve the ``{package_id, manifest_sha256, new_revision}`` pointer a
    completed request must expose (contract §9.5/§9.7).

    Preferred source is ``job.result_json`` — the handler stores the full
    triple after sealing the dedicated result package. Fallback: the
    produced ``record_id`` resolves through ``records.packaged_in`` to the
    ``packages`` ledger row (covers dedupe replays and results written by
    an earlier build).
    """
    try:
        blob = json.loads(job.result_json or "")
    except (TypeError, ValueError):
        return None
    if not isinstance(blob, dict):
        return None
    result = blob.get("result") if isinstance(blob.get("result"), dict) else blob
    if all(
        result.get(k) is not None
        for k in ("package_id", "manifest_sha256", "new_revision")
    ):
        return {
            "package_id": result["package_id"],
            "manifest_sha256": result["manifest_sha256"],
            "new_revision": result["new_revision"],
        }
    record_id = blob.get("record_id")
    if not isinstance(record_id, str) or not record_id:
        return None
    record = session.get(Record, record_id)
    if record is None or not record.packaged_in:
        return None
    package = session.get(Package, record.packaged_in)
    if package is None:
        # ``__internal__``/``__discovery__`` sentinels are not real packages.
        return None
    return {
        "package_id": package.package_id,
        "manifest_sha256": package.manifest_sha256,
        "new_revision": record.revision,
    }


# Terminal codes the ``ocr_request`` handler is allowed to surface — used to
# keep error-code extraction from picking random ``word:`` prefixes out of
# free-text exception strings.
_REQUEST_ERROR_CODES = frozenset(
    {
        "budget_exceeded",
        "empty_result",
        "invalid_variant",
        "json_invalid",
        "missing_preset",
        "rate_limited",
        "request_conflict",
        "request_forbidden_field",
        "request_too_large",
        "schema_invalid",
        "source_image_expired",
        "source_image_unavailable",
        "source_not_enabled",
        "stale_revision",
        "status_invalid",
        "unauthorized",
        "unknown_source",
        "unsupported_variant",
    }
)
_ERROR_PREFIX = re.compile(r"^[A-Za-z_]*Error: ([a-z0-9_]+): ", re.S)


def _error_from_job(job: Job) -> dict:
    """Normalize the persisted terminal error into a contract error_object.

    Lookup order: ``job.payload_json.terminal_error`` (durable structured
    error written by the handler before it raises — the worker overwrites
    ``result_json`` on failure), then a structured ``result_json.error``
    dict, then the ``"XxxError: <code>: <message>"`` string form the
    worker stores for raised exceptions.
    """
    code = "provider_failed"
    message = None
    retryable = None
    try:
        in_payload = json.loads(job.payload_json or "")
    except (TypeError, ValueError):
        in_payload = None
    if isinstance(in_payload, dict):
        stored = in_payload.get("terminal_error")
        if isinstance(stored, dict):
            code = str(stored.get("code") or code)
            message = stored.get("message")
            retryable = stored.get("retryable")
    try:
        blob = json.loads(job.result_json or "")
    except (TypeError, ValueError):
        blob = None
    if isinstance(blob, dict):
        err = blob.get("error")
        if isinstance(err, dict):
            code = err.get("code") or code
            message = err.get("message")
            retryable = err.get("retryable")
        elif isinstance(err, str) and err:
            message = err
            match = _ERROR_PREFIX.match(err)
            if match is not None and match.group(1) in _REQUEST_ERROR_CODES:
                code = match.group(1)
                message = err[match.end():][:500] or message
    if job.state == "expired" and code == "provider_failed":
        # JobExpired is raised for out-of-lifetime subjects (worker contract).
        code = "source_image_expired"
    out = {"code": code}
    if message:
        out["message"] = str(message)[:500]
    if isinstance(retryable, bool):
        out["retryable"] = retryable
    return out


def _status_doc(row: OcrRequest, session, *, deduplicated: bool = False) -> dict:
    job = session.get(Job, row.job_id) if row.job_id else None
    if row.state == "rejected":
        state = "rejected"
    elif job is not None:
        state = _JOB_STATE_MAP.get(job.state, "failed")
    elif row.state in _DOC_STATES:
        state = row.state
    else:
        state = "failed"

    # Contract §9.5 exposes provider-retry semantics: max 3. Internal job
    # max_attempts=8 includes §9.4 single-flight requeue headroom which is
    # not a provider attempt — the wire doc is capped at 3 on both fields.
    doc = {
        "schema_version": "intake.ocr-request-status.v1",
        "request_id": row.request_id,
        "job_id": row.job_id,
        "state": state,
        "attempt": min(job.attempts, 3) if job else 0,
        "max_attempts": 3,
    }
    if deduplicated or row.deduped_from is not None:
        doc["deduplicated"] = True
    if job is not None and job.created_at:
        doc["accepted_at"] = job.created_at
    if state in ("completed", "rejected", "failed") and job is not None:
        doc["finished_at"] = job.updated_at
    if state == "completed" and job is not None:
        result = _result_from_job(session, job)
        if result is not None:
            doc["result"] = result
    if state in ("rejected", "failed") and job is not None:
        doc["error"] = _error_from_job(job)
    return doc


# ---------------------------------------------------------------------------
# screening helpers
# ---------------------------------------------------------------------------


def _schema_errors(body) -> list:
    """[(code, detail)] from the vendored ocr-request schema."""
    errors = _schema().validate(body)
    return sorted(set(errors))


def _primary_schema_code(errors: list) -> str:
    """Prefer an x-error-code (unsupported_variant/missing_preset) over the
    generic schema_invalid when the schema flagged several problems."""
    codes = sorted({code for code, _ in errors})
    for code in codes:
        if code != "schema_invalid":
            return code
    return "schema_invalid"


def _reject(
    session,
    settings,
    body: dict,
    body_sha: str,
    code: str,
    message: str,
    *,
    retryable: bool = False,
) -> dict:
    """Persist a pre-run rejection (contract §9.5) and return the status doc.

    A marker Job row (state ``failed``, ``attempts=0``) supplies the durable
    ``job_id`` the status schema requires plus the stored error for replay;
    it is never claimable by the worker.
    """
    now_iso = _iso(_now())
    job_id = str(uuid.uuid4())
    session.add(
        Job(
            job_id=job_id,
            kind="ocr_request",
            state="failed",
            logical_id=body["logical_id"],
            request_id=body["request_id"],
            payload_json=json.dumps(
                {
                    "request_id": body["request_id"],
                    "logical_id": body["logical_id"],
                    "variant": body["variant"],
                    "preset": body.get("preset"),
                    "reason_code": body["reason_code"],
                    "observed_revision": body["observed_revision"],
                    "config_version": settings.ocr_config_version,
                    "rejected": True,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            attempts=0,
            max_attempts=MAX_ATTEMPTS,
            created_at=now_iso,
            updated_at=now_iso,
            result_json=json.dumps(
                {
                    "error": {
                        "code": code,
                        "message": message[:500],
                        "retryable": retryable,
                    },
                    "rejected": True,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        )
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
        state="rejected",
        deduped_from=None,
    )
    session.add(row)
    session.flush()
    return _status_doc(row, session, deduplicated=False)


# ---------------------------------------------------------------------------
# endpoints
# ---------------------------------------------------------------------------


@router.post("/ocr-requests")
async def create_ocr_request(request: Request):
    settings, engine = _deps(request)

    # -- stage 2a: transport limit ------------------------------------------
    raw = await request.body()
    if len(raw) > BODY_LIMIT:
        return _error(413, "request_too_large", "ocr-request body exceeds 16 KiB")

    # -- stage 2b: strict JSON profile --------------------------------------
    try:
        body = parse_strict_body(raw)
    except StrictJsonError as exc:
        return _error(400, "json_invalid", str(exc))

    # -- stage 2c/2d: schema + forbidden-field scan (independent, unioned) ---
    schema_errors = _schema_errors(body)
    forbidden_hits: list = []
    if isinstance(body, (dict, list)):
        _scan_forbidden(body, forbidden_hits)
    if forbidden_hits:
        details = "; ".join(forbidden_hits[:4])
        if schema_errors:
            details += "; schema: " + "; ".join(d for _, d in schema_errors[:3])
        return _error(400, "request_forbidden_field", details)
    if schema_errors:
        details = "; ".join(d for _, d in schema_errors[:6])
        return _error(400, _primary_schema_code(schema_errors), details)

    # -- stage 1 tail: body consumer_id must be the registered consumer -----
    registered = settings.consumer_id
    if not registered or body["consumer_id"] != registered:
        # Fail closed when no consumer is configured (never accept-all).
        return _error(
            401, "unauthorized",
            "consumer_id does not match the registered consumer",
        )

    body_sha = _canonical_sha256(body)

    with session_scope(engine) as session:
        # -- stage 4 semantics run FIRST: request_id is the idempotency key,
        # so a replay must return the *stored* decision — including stored
        # rejections from stages 3/6/7/8 — before any of them can run again
        # (re-running _reject for the same request_id would violate the PK).
        existing = session.get(OcrRequest, body["request_id"])
        if existing is not None:
            if existing.body_canonical_sha256 == body_sha:
                return _status_doc(existing, session, deduplicated=True)
            return _error(
                409, "request_conflict",
                "request_id was already used with a different body",
            )

        # -- stage 3: source must exist and be enabled ----------------------
        source = session.get(Source, body["logical_id"])
        if source is None:
            return _reject(
                session, settings, body, body_sha,
                "unknown_source",
                "logical_id was never handed over to this consumer",
            )
        if not source.enabled:
            return _reject(
                session, settings, body, body_sha,
                "source_not_enabled",
                "source is not enabled for OCR requests",
            )

        # -- stage 5: dedupe on (logical_id, variant, preset, config_version)
        candidates = session.execute(
            select(OcrRequest, Job)
            .join(Job, OcrRequest.job_id == Job.job_id)
            .where(
                OcrRequest.logical_id == body["logical_id"],
                OcrRequest.variant == body["variant"],
                OcrRequest.state != "rejected",
                OcrRequest.deduped_from.is_(None),
                Job.kind == "ocr_request",
                Job.state.in_(_DEDUPE_JOB_STATES),
            )
        ).all()
        dedupe_hit = None
        for req_row, job_row in candidates:
            if req_row.preset != body.get("preset"):
                continue
            try:
                jpayload = json.loads(job_row.payload_json or "{}")
            except (TypeError, ValueError):
                jpayload = {}
            if jpayload.get("config_version") == settings.ocr_config_version:
                dedupe_hit = req_row
                break
        if dedupe_hit is not None:
            # Persist a deduped ledger row pointing at the existing job —
            # replayed GETs resolve to the same status across restarts.
            dup = OcrRequest(
                request_id=body["request_id"],
                consumer_id=body["consumer_id"],
                logical_id=body["logical_id"],
                variant=body["variant"],
                preset=body.get("preset"),
                reason_code=body["reason_code"],
                observed_revision=body["observed_revision"],
                submitted_at=body["submitted_at"],
                body_canonical_sha256=body_sha,
                job_id=dedupe_hit.job_id,
                state="queued",
                deduped_from=dedupe_hit.request_id,
            )
            session.add(dup)
            session.flush()
            return _status_doc(dup, session, deduplicated=True)

        # -- stage 6: revision freshness ------------------------------------
        if body["observed_revision"] < (source.current_revision or 0):
            return _reject(
                session, settings, body, body_sha,
                "stale_revision",
                "consumer analyzed an older revision; sync and re-analyze first",
            )

        # -- stage 7: image lifetime and availability -----------------------
        now = _now()
        expires = _parse_iso(source.image_expires_at)
        if expires is None:
            captured = _parse_iso(source.captured_at)
            expires = captured + IMAGE_TTL if captured is not None else None
        if expires is not None and now >= expires:
            return _reject(
                session, settings, body, body_sha,
                "source_image_expired",
                f"source image expired at {_iso(expires)}",
            )
        if not source.image_available:
            return _reject(
                session, settings, body, body_sha,
                "source_image_unavailable",
                "the source image is not retrievable on the module",
            )

        # -- stage 8: quota — three independent limits ----------------------
        key_jobs = session.execute(
            select(func.count())
            .select_from(OcrRequest)
            .where(
                OcrRequest.logical_id == body["logical_id"],
                OcrRequest.state != "rejected",
                OcrRequest.deduped_from.is_(None),
            )
        ).scalar_one()
        # §9.6 counts provider *calls*, not requests: SUM(attempts) is the
        # call proxy; accepted-but-not-yet-run jobs (attempts=0) count one
        # projected call. `updated_at` keeps straddling retries in window —
        # both choices over-count rather than under-count (contract-safe).
        day_calls = session.execute(
            select(
                func.coalesce(
                    func.sum(case((Job.attempts > 0, Job.attempts), else_=1)),
                    0,
                )
            )
            .select_from(Job)
            .join(OcrRequest, OcrRequest.job_id == Job.job_id)
            .where(
                Job.kind == "ocr_request",
                Job.updated_at >= _iso(now - DAY_WINDOW),
                OcrRequest.consumer_id == body["consumer_id"],
                OcrRequest.state != "rejected",
                OcrRequest.deduped_from.is_(None),
            )
        ).scalar_one()
        concurrent = session.execute(
            select(func.count())
            .select_from(Job)
            .where(
                Job.kind == "ocr_request",
                Job.state.in_(_CONCURRENT_JOB_STATES),
            )
        ).scalar_one()

        violations = []
        if key_jobs >= QUOTA_KEY_JOBS:
            violations.append("budget_exceeded")
        if day_calls >= QUOTA_DAY_CALLS:
            violations.append("rate_limited")
        if concurrent >= QUOTA_CONCURRENT:
            violations.append("rate_limited")
        if violations:
            code = "budget_exceeded" if "budget_exceeded" in violations else "rate_limited"
            retryable = code == "rate_limited"
            return _reject(
                session, settings, body, body_sha,
                code,
                f"OCR request quota exceeded ({', '.join(violations)}): "
                f"key_jobs={key_jobs} day_calls={day_calls} concurrent={concurrent}",
                retryable=retryable,
            )

        # -- stage 9: accept — durable job + ledger row ---------------------
        payload = {
            "request_id": body["request_id"],
            "logical_id": body["logical_id"],
            "variant": body["variant"],
            "preset": body.get("preset"),
            "reason_code": body["reason_code"],
            "observed_revision": body["observed_revision"],
            "config_version": settings.ocr_config_version,
        }
        from zalo_module.jobs.worker import enqueue_job

        job_id = enqueue_job(
            "ocr_request",
            payload,
            session,
            logical_id=body["logical_id"],
            request_id=body["request_id"],
            max_attempts=MAX_ATTEMPTS,
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
            # Contract §11.4 has no dedicated request-not-found code;
            # unknown_source is the closest catalog-legal value.
            return _error(
                404, "unknown_source", f"unknown request_id {request_id}"
            )
        return _status_doc(row, session, deduplicated=row.deduped_from is not None)

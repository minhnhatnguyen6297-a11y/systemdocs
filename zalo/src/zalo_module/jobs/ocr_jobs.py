"""OCR job handlers + media→OCR sweeper (MIN-95 slice B).

Kinds (decision-sheet §0 pins): ``ocr_default`` — capture-time default pass,
payload ``{"attachment_id": "<uuid>"}``; ``ocr_request`` — consumer
supplementary pass, payload ``{"request_id": "<uuid>"}`` (the API writes the
rich copy; the durable ``ocr_requests`` row is authoritative).

Behavior summary (contract §5.3/§6/§8/§9):

- One ``ocr_page`` logical per *page* (Source scope="page", page_index
  1-based); attachment-wide outcomes go to scope="attachment"
  processing_status records (``media_missing`` / ``image_expired`` /
  ``ocr_partial``).
- Default pass: ``image_operation="original"``, task from env
  ``ZALO_INTAKE_OCR_TASK`` (default ``text_recognition``;
  ``advanced_recognition`` retains provider ``words_info`` as
  ``provider_lines`` with unverified geometry status — never
  ``present_mapping_verified``).
- Error taxonomy: HTTP 401/403 → failure recorded, **no retry**;
  timeout/429/5xx/transport/parse → raise for worker backoff, and on the
  last attempt the remaining pages still get failure records (bounded);
  multi-page partial success → successful pages keep their records +
  ``ocr_partial`` status on the attachment. Empty provider output is never
  ``succeeded``.
- ``ocr_request`` resolves ``logical_id`` → page source → media; expired
  image → request state ``expired`` + ``JobExpired`` (a status revision is
  still published, contract §9.3/§9.5); dedupe on
  (logical_id, variant, preset, config_version, media sha256) → request
  ``completed`` with ``deduplicated`` result and *no* provider call;
  otherwise a new revision appends the attempt (request_id tagged) while
  ``text_lines``/``selected_pass_ids`` of the default transcript stay
  untouched (owner decision, §6.3).

Offline testing: set ``OCR_CLIENT`` to an object with an async
``post(url, headers=..., json=..., timeout=...)`` — the real
``call_qwen_ocr_detailed`` code path (body build, error taxonomy, payload
parse) still runs.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import and_, or_, select

from zalo_module.audit import record_access
from zalo_module.delivery.package import build_package
from zalo_module.delivery.record_check import validate_record
from zalo_module.jobs.worker import JobExpired, enqueue_job
from zalo_module.models import (
    Job,
    MediaAsset,
    OcrRequest,
    Package,
    Record,
    Source,
)
from zalo_module.ocr.errors import (
    OcrApiError,
    OcrError,
    OcrParseError,
    OcrTransportError,
)
from zalo_module.ocr.pipeline import (
    SubmittedFrame,
    parse_provider_lines,
    prepare_default_frame,
    prepare_variant_frame,
    run_ocr_call,
)
from zalo_module.ocr.prep import inspect_media, render_pdf_pages
from zalo_module.ocr.qwen import resolve_model
from zalo_module.ocr.records import (
    Provenance,
    attempt_dict,
    aware,
    build_ocr_page_payload,
    build_processing_status_payload,
    clean_message,
    ensure_attachment_source,
    ensure_page_source,
    find_provenance,
    has_record,
    image_expires_iso,
    insert_record,
    iso,
    latest_attachment_status,
    latest_record,
    records_for,
    source_block,
    text_line_dicts,
    utcnow,
)
from zalo_module.ocr.variants import crop_fraction, normalize_preset, preset_for_fraction

logger = logging.getLogger(__name__)

# Bounded sweeps (decision-sheet §3.1) — ~20 jobs per pass, oldest first.
SCAN_LIMIT = 20
# Bound on permanently-failing attachments: stop sweeping once this many
# ``ocr_default`` jobs have been created for the same attachment_id.
JOB_CAP_PER_ASSET = 5

TASK_ENV = "ZALO_INTAKE_OCR_TASK"
TASKS = {"text_recognition", "advanced_recognition"}

NON_RETRYABLE_HTTP = {401, 403}   # publish failure, never retry (§3.2)
# Everything else provider-side (429/5xx/odd statuses), transport errors
# (incl. timeout) and parse errors are retryable via the worker backoff.

# Test hook — offline transport injection (see module docstring).
OCR_CLIENT = None


def _iso_now() -> str:
    return iso(utcnow()) or ""


def _ocr_task() -> str:
    task = (os.environ.get(TASK_ENV) or "").strip()
    return task if task in TASKS else "text_recognition"


def _invoke_ocr(
    image_bytes: bytes,
    *,
    settings,
    task: str,
    enable_rotate: bool | None,
    filename: str,
):
    """Provider-call seam — monkeypatchable; default goes through
    ``pipeline.run_ocr_call`` (asyncio.run around call_qwen_ocr_detailed)."""
    return run_ocr_call(
        image_bytes,
        settings=settings,
        task=task,
        enable_rotate=enable_rotate,
        filename=filename,
        client=OCR_CLIENT,
    )


def _error_code(exc: BaseException) -> str:
    """Map a provider exception to a stable attempt ``error.code``."""
    if isinstance(exc, OcrApiError):
        if exc.status_code == 429:
            return "provider_rate_limited"
        if exc.status_code >= 500:
            return "provider_unavailable"
        return f"provider_http_{exc.status_code}"
    if isinstance(exc, OcrParseError):
        return "provider_invalid_json"
    if isinstance(exc, OcrTransportError):
        return "provider_transport"
    return "provider_failed"


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, OcrApiError):
        return exc.status_code not in NON_RETRYABLE_HTTP
    return isinstance(exc, (OcrTransportError, OcrParseError))


def _exhausted(job: Job) -> bool:
    return (job.attempts or 0) >= (job.max_attempts or 3)


def _cap_attempts(job: Job) -> None:
    """Force the worker's exhausted-branch → job ``failed`` on raise."""
    job.attempts = job.max_attempts


# ---------------------------------------------------------------------------
# Coverage — "has the default pipeline reached a terminal state per page?"
# ---------------------------------------------------------------------------


def _attachment_sources(session, attachment_id: str) -> list[Source]:
    return (
        session.execute(
            select(Source).where(Source.attachment_id == attachment_id)
        )
        .scalars()
        .all()
    )


def _records_by_logical(session, logical_ids: list[str]) -> dict[str, list[Record]]:
    if not logical_ids:
        return {}
    rows = (
        session.execute(select(Record).where(Record.logical_id.in_(logical_ids)))
        .scalars()
        .all()
    )
    grouped: dict[str, list[Record]] = {}
    for row in rows:
        grouped.setdefault(row.logical_id, []).append(row)
    return grouped


def _needs_ocr(session, settings, asset: MediaAsset) -> bool:
    """True when the attachment still lacks a terminal default-OCR outcome.

    Covered = every page-scope source has ≥1 record, *or* an
    attachment-scope terminal status exists (``media_missing`` /
    ``image_expired``). A lone ``media_missing`` marker is *not* terminal
    when the file is present and no ``ocr_default`` job has completed —
    covers late-arriving media.
    """
    sources = _attachment_sources(session, asset.attachment_id)
    if not sources:
        return True
    by_logical = _records_by_logical(
        session, [s.logical_id for s in sources]
    )
    page_sources = [s for s in sources if s.scope == "page"]
    if page_sources:
        return any(not by_logical.get(s.logical_id) for s in page_sources)
    # Only attachment-scope sources exist → need ≥1 terminal status record.
    terminal = False
    for source in sources:
        for rec in by_logical.get(source.logical_id, []):
            if rec.kind != "processing_status":
                if rec.kind == "ocr_page":
                    return False
                continue
            try:
                code = (json.loads(rec.payload_json).get("status") or {}).get("code")
            except ValueError:
                continue
            if code == "image_expired":
                terminal = True
            elif code == "media_missing":
                path = Path(settings.runtime_root) / asset.rel_path
                if not path.exists():
                    terminal = True
                elif _default_job_count(session, asset.attachment_id) > 0:
                    # A completed job already tried a present file and still
                    # recorded media_missing → unreadable; terminal.
                    terminal = True
    return not terminal


def _default_job_count(session, attachment_id: str) -> int:
    count = 0
    rows = (
        session.execute(
            select(Job.payload_json).where(Job.kind == "ocr_default")
        )
        .scalars()
        .all()
    )
    for payload in rows:
        try:
            if json.loads(payload or "{}").get("attachment_id") == attachment_id:
                count += 1
        except ValueError:
            continue
    return count


def scan_media_for_ocr(session, settings) -> int:
    """Enqueue ``ocr_default`` jobs for media lacking a default pass.

    Candidates: ``media_assets`` in state ``captured``|``retained``, not yet
    expired — oldest ``captured_at`` first, bounded at ``SCAN_LIMIT`` per
    pass. Skips assets with an in-flight ``ocr_default`` job, fully-covered
    attachments and attachments that already burned ``JOB_CAP_PER_ASSET``
    jobs (permanent-failure bound).
    """
    active: set[str] = set()
    for job in (
        session.execute(
            select(Job).where(
                Job.kind == "ocr_default",
                Job.state.in_(("queued", "running", "retry_wait")),
            )
        )
        .scalars()
        .all()
    ):
        try:
            aid = json.loads(job.payload_json or "{}").get("attachment_id")
        except ValueError:
            aid = None
        if aid:
            active.add(aid)

    # ISO strings may mix "+00:00"/"Z" suffixes across writers — compare
    # expiry as datetimes in Python rather than lexically in SQL.
    now = utcnow()
    rows = [
        asset
        for asset in (
            session.execute(
                select(MediaAsset)
                .where(MediaAsset.state.in_(("captured", "retained")))
                .order_by(MediaAsset.captured_at)
            )
            .scalars()
            .all()
        )
        if (aware(asset.expires_at) or now) > now
    ]
    enqueued = 0
    for asset in rows:
        if enqueued >= SCAN_LIMIT:
            break
        aid = asset.attachment_id
        if aid in active:
            continue
        if _default_job_count(session, aid) >= JOB_CAP_PER_ASSET:
            continue
        if not _needs_ocr(session, settings, asset):
            continue
        enqueue_job("ocr_default", {"attachment_id": aid}, session)
        enqueued += 1
    return enqueued


# ---------------------------------------------------------------------------
# Record writers
# ---------------------------------------------------------------------------


def _page_sources(session, attachment_id: str) -> list[Source]:
    return [
        s
        for s in _attachment_sources(session, attachment_id)
        if s.scope == "page"
    ]


def _write_page_record(
    session,
    *,
    source: Source,
    asset: MediaAsset,
    prov: Provenance | None,
    attempt: dict,
    lines: list[str],
    page_index: int,
    recorded_at: str,
) -> Record:
    """Write the revision-1 ``ocr_page`` record for a default pass."""
    captured = iso(asset.captured_at)
    text_lines = (
        text_line_dicts(
            lines,
            captured_at=captured,
            page_index=page_index,
            ocr_pass_id=attempt["ocr_pass_id"],
        )
        if attempt["status"] == "succeeded"
        else []
    )
    selected = [attempt["ocr_pass_id"]] if text_lines else []
    payload = build_ocr_page_payload(
        logical_id=source.logical_id,
        revision=1,
        supersedes=None,
        captured_at=captured,
        recorded_at=recorded_at,
        source=source_block(prov, asset.attachment_id, page_index),
        image_sha256=asset.sha256,
        image_expires_at=image_expires_iso(captured),
        image_state=asset.state,
        attempts=[attempt],
        text_lines=text_lines,
        selected_pass_ids=selected,
    )
    return insert_record(session, payload)


def _ensure_attachment_status(
    session,
    *,
    asset: MediaAsset,
    prov: Provenance | None,
    code: str,
    note: str | None = None,
) -> Record | None:
    """Idempotently write an attachment-scope ``processing_status`` record.

    Skips the write when the latest status already carries the same
    code+note (sweep retries must not churn revisions).
    """
    source = ensure_attachment_source(session, asset, prov)
    latest = latest_attachment_status(session, source.logical_id)
    if latest is not None:
        status = latest.get("status") or {}
        if status.get("code") == code and (status.get("note") or None) == note:
            return None
    prior = latest_record(session, source.logical_id)
    revision = (prior.revision + 1) if prior is not None else 1
    supersedes = (
        {"record_id": prior.record_id, "revision": prior.revision}
        if prior is not None
        else None
    )
    payload = build_processing_status_payload(
        logical_id=source.logical_id,
        revision=revision,
        supersedes=supersedes,
        captured_at=iso(asset.captured_at),
        recorded_at=_iso_now(),
        source=source_block(prov, asset.attachment_id, None),
        code=code,
        note=note,
    )
    return insert_record(session, payload)


def _new_request_revision(
    session,
    *,
    source: Source,
    asset: MediaAsset,
    prov: Provenance | None,
    attempt: dict,
    lines: list[str],
    recorded_at: str,
) -> Record:
    """Append a supplementary-pass attempt as a new immutable revision.

    Per contract §9.5/§6.3: same ``logical_id``, ``supersedes`` the latest
    revision, preserved ``captured_at``/``source``/``image_*`` envelope;
    ``ocr.attempts`` gains the request-tagged attempt; the default
    transcript (``text_lines``/``selected_pass_ids``) is unchanged — except
    when no transcript exists yet, in which case a successful pass supplies
    it so ``status=succeeded`` stays schema-consistent.
    """
    prior = latest_record(session, source.logical_id)
    prev: dict[str, Any] = {}
    if prior is not None:
        try:
            prev = json.loads(prior.payload_json) or {}
        except ValueError:
            prev = {}
    prev_ocr = prev.get("ocr") if isinstance(prev.get("ocr"), dict) else {}
    attempts = list(prev_ocr.get("attempts") or []) + [attempt]
    text_lines = list(prev_ocr.get("text_lines") or [])
    selected = list(prev_ocr.get("selected_pass_ids") or [])
    if not text_lines and attempt["status"] == "succeeded" and lines:
        text_lines = text_line_dicts(
            lines,
            captured_at=iso(asset.captured_at),
            page_index=source.page_index or 1,
            ocr_pass_id=attempt["ocr_pass_id"],
        )
        selected = [attempt["ocr_pass_id"]]
    revision = (prior.revision + 1) if prior is not None else 1
    supersedes = (
        {"record_id": prior.record_id, "revision": prior.revision}
        if prior is not None
        else None
    )
    source_block_payload = (
        prev.get("source")
        if isinstance(prev.get("source"), dict)
        else source_block(prov, asset.attachment_id, source.page_index)
    )
    payload = build_ocr_page_payload(
        logical_id=source.logical_id,
        revision=revision,
        supersedes=supersedes,
        captured_at=iso(asset.captured_at),
        recorded_at=recorded_at,
        source=source_block_payload,
        image_sha256=asset.sha256,
        image_expires_at=image_expires_iso(iso(asset.captured_at)),
        image_state=asset.state,
        attempts=attempts,
        text_lines=text_lines,
        selected_pass_ids=selected,
    )
    return insert_record(session, payload)


def _media_path(settings, asset: MediaAsset) -> Path:
    return Path(settings.runtime_root) / asset.rel_path


def _is_expired(asset: MediaAsset, now: datetime) -> bool:
    if asset.state == "expired":
        return True
    expires = aware(asset.expires_at)
    return expires is not None and expires <= now


def _is_pdf(path: Path, data: bytes) -> bool:
    return data[:5] == b"%PDF-" or path.suffix.lower() == ".pdf"


# ---------------------------------------------------------------------------
# ocr_default handler
# ---------------------------------------------------------------------------


def handle_ocr_default(session, job: Job, settings) -> dict:
    payload = json.loads(job.payload_json or "{}")
    attachment_id = payload.get("attachment_id")
    if not attachment_id:
        raise ValueError("ocr_default payload missing attachment_id")
    asset = session.get(MediaAsset, attachment_id)
    if asset is None:
        raise LookupError(f"media asset {attachment_id} not found")
    prov = find_provenance(session, attachment_id)
    if prov is None or not (
        prov.account_id and prov.conversation_id and prov.conversation_type
    ):
        # Schema cannot produce a conformant record without provenance —
        # fail loudly rather than writing a non-conformant one.
        raise LookupError(
            f"no provenance for attachment {attachment_id} "
            "(media dedupe journal entry missing)"
        )
    now = utcnow()

    # --- expiry before any read → publish source_image_expired (§8.1). ----
    if _is_expired(asset, now):
        _ensure_attachment_status(
            session, asset=asset, prov=prov, code="image_expired"
        )
        return {"status": "source_image_expired", "attachment_id": attachment_id}

    path = _media_path(settings, asset)
    record_access(path, "media")
    if not path.is_file():
        _ensure_attachment_status(
            session,
            asset=asset,
            prov=prov,
            code="media_missing",
            note="media file absent before expiry",
        )
        return {"status": "media_missing", "attachment_id": attachment_id}
    try:
        data = path.read_bytes()
    except OSError as exc:
        _ensure_attachment_status(
            session,
            asset=asset,
            prov=prov,
            code="media_missing",
            note=clean_message(f"media file unreadable: {exc}"),
        )
        return {"status": "media_missing", "attachment_id": attachment_id}

    # --- split into pages -------------------------------------------------
    try:
        if _is_pdf(path, data):
            pages = render_pdf_pages(data)
        else:
            inspect_media(data)  # validates decodability
            pages = [data]
    except OcrError as exc:
        _ensure_attachment_status(
            session,
            asset=asset,
            prov=prov,
            code="media_missing",
            note=clean_message(f"media unreadable: {exc}"),
        )
        return {"status": "media_missing", "attachment_id": attachment_id}
    if not pages:
        _ensure_attachment_status(
            session,
            asset=asset,
            prov=prov,
            code="media_missing",
            note="media produced zero pages",
        )
        return {"status": "media_missing", "attachment_id": attachment_id}

    task = _ocr_task()
    model = resolve_model(settings=settings)
    config_version = settings.ocr_config_version
    succeeded: list[int] = []
    failed: list[int] = []
    page_sources = {
        idx: ensure_page_source(session, asset, prov, idx)
        for idx in range(1, len(pages) + 1)
    }

    for idx, page_bytes in enumerate(pages, start=1):
        source = page_sources[idx]
        if has_record(session, source.logical_id):
            # Idempotent retry: a previously written outcome is kept.
            prior = latest_record(session, source.logical_id)
            prior_status = "failed"
            if prior is not None:
                try:
                    prior_status = (
                        json.loads(prior.payload_json)
                        .get("ocr", {})
                        .get("status", "failed")
                    )
                except ValueError:
                    pass
            (succeeded if prior_status == "succeeded" else failed).append(idx)
            continue

        started = _iso_now()
        frame: SubmittedFrame | None = None
        try:
            frame = prepare_default_frame(page_bytes)
            result = _invoke_ocr(
                frame.image_bytes,
                settings=settings,
                task=task,
                enable_rotate=frame.enable_rotate,
                filename=f"{attachment_id}#p{idx}.jpg",
            )
            completed = _iso_now()
            geometry_status, provider_lines = parse_provider_lines(
                result.words_info, task
            )
            ok = bool(result.lines)
            attempt = attempt_dict(
                ocr_pass_id=str(uuid.uuid4()),
                model=result.model,
                task=task,
                image_operation="original",
                region=frame.region,
                transform_chain=frame.transform_chain,
                geometry_status=geometry_status,
                status="succeeded" if ok else "failed",
                config_version=config_version,
                submitted_frame=frame.submitted_frame_dict(),
                provider_lines=provider_lines,
                error=None
                if ok
                else {
                    "code": "empty_result",
                    "message": "provider returned no text",
                    "retryable": False,
                },
                started_at=started,
                completed_at=completed,
            )
            _write_page_record(
                session,
                source=source,
                asset=asset,
                prov=prov,
                attempt=attempt,
                lines=result.lines if ok else [],
                page_index=idx,
                recorded_at=completed,
            )
            (succeeded if ok else failed).append(idx)
        except Exception as exc:  # noqa: BLE001 - taxonomy below decides
            completed = _iso_now()
            if isinstance(exc, OcrApiError) and exc.status_code in NON_RETRYABLE_HTTP:
                # 401/403 → publish failure for this AND all unprocessed
                # pages (credentials cannot recover mid-job), no retry.
                for rest in range(idx, len(pages) + 1):
                    rest_source = page_sources[rest]
                    if has_record(session, rest_source.logical_id):
                        continue
                    attempt = attempt_dict(
                        ocr_pass_id=str(uuid.uuid4()),
                        model=model,
                        task=task,
                        image_operation="original",
                        region={"kind": "full_image"},
                        transform_chain=[],
                        geometry_status=(
                            "not_applicable"
                            if task == "text_recognition"
                            else "absent"
                        ),
                        status="failed",
                        config_version=config_version,
                        error={
                            "code": _error_code(exc),
                            "message": clean_message(str(exc)),
                            "retryable": False,
                        },
                        started_at=started,
                        completed_at=completed,
                    )
                    _write_page_record(
                        session,
                        source=rest_source,
                        asset=asset,
                        prov=prov,
                        attempt=attempt,
                        lines=[],
                        page_index=rest,
                        recorded_at=completed,
                    )
                    failed.append(rest)
                break
            if _is_retryable(exc) and not _exhausted(job):
                # Retryable provider/transport failure → raise for worker
                # backoff. Commit first — the worker session rolls back on
                # raise, and completed page records must survive.
                session.commit()
                raise
            # Last attempt (or non-taxonomy error): record the failure so
            # the page reaches a terminal state instead of looping forever.
            if not has_record(session, source.logical_id):
                attempt = attempt_dict(
                    ocr_pass_id=str(uuid.uuid4()),
                    model=model,
                    task=task,
                    image_operation="original",
                    region=frame.region if frame else {"kind": "full_image"},
                    transform_chain=(
                        frame.transform_chain if frame else []
                    ),
                    geometry_status=(
                        "not_applicable"
                        if task == "text_recognition"
                        else "absent"
                    ),
                    status="failed",
                    config_version=config_version,
                    submitted_frame=(
                        frame.submitted_frame_dict() if frame else None
                    ),
                    error={
                        "code": _error_code(exc),
                        "message": clean_message(str(exc)),
                        "retryable": _is_retryable(exc),
                    },
                    started_at=started,
                    completed_at=completed,
                )
                _write_page_record(
                    session,
                    source=source,
                    asset=asset,
                    prov=prov,
                    attempt=attempt,
                    lines=[],
                    page_index=idx,
                    recorded_at=completed,
                )
            failed.append(idx)

    if failed and succeeded:
        _ensure_attachment_status(
            session,
            asset=asset,
            prov=prov,
            code="ocr_partial",
            note=f"pages failed: {','.join(map(str, failed))}"[:500],
        )
    status = (
        "succeeded"
        if succeeded and not failed
        else ("failed" if not succeeded else "partial")
    )
    return {
        "status": status,
        "attachment_id": attachment_id,
        "pages": len(pages),
        "succeeded": len(succeeded),
        "failed": len(failed),
    }


# ---------------------------------------------------------------------------
# ocr_request handler
# ---------------------------------------------------------------------------


def _request_terminal_error(session, req: OcrRequest, job: Job, code: str, message: str):
    """Mark the request failed and raise so the job lands ``failed``
    immediately (attempt counter is capped — the error is permanent).
    Commits first: the worker session rolls back on raise, and the ledger
    row + any published revision must survive.

    The structured error is persisted *before* raising — the worker
    overwrites ``job.result_json`` with ``"RuntimeError: <code>: <msg>"``
    on the failure path, so the durable copy lives on
    ``job.payload_json.terminal_error`` (the API status doc reads it back
    to recover the real error code).
    """
    req.state = "failed"
    _cap_attempts(job)
    error_obj = {
        "code": code,
        "message": clean_message(str(message))[:500],
        "retryable": False,
    }
    try:
        payload = json.loads(job.payload_json or "{}")
    except ValueError:
        payload = {}
    payload["terminal_error"] = error_obj
    job.payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    job.result_json = json.dumps(
        {"error": error_obj}, ensure_ascii=False, sort_keys=True
    )
    session.commit()
    raise RuntimeError(f"{code}: {message}")


def _publish_result_package(session, record: Record | None, settings) -> dict | None:
    """Seal the revision an OCR request produced into its own raw package.

    Contract §9.5 — a completed request publishes an immutable raw-package
    revision and the status doc points at it via
    ``{package_id, manifest_sha256, new_revision}``. Building the package
    inside the request job (instead of waiting for the periodic
    ``package_build`` sweep) makes the pointer resolvable immediately —
    the package is sealed in the same transaction as the job's terminal
    state, so it also survives worker restarts. Returns ``None`` when no
    consumer is configured or the payload cannot validate (the record
    then goes through the normal feed build, which flags it loudly).
    """
    if record is None or not getattr(settings, "consumer_id", None):
        return None
    if record.packaged_in:
        # ``__internal__``/``__discovery__`` sentinels are not real packages.
        pkg = session.get(Package, record.packaged_in)
        if pkg is None:
            return None
        return {
            "package_id": pkg.package_id,
            "manifest_sha256": pkg.manifest_sha256,
            "new_revision": record.revision,
        }
    try:
        payload = json.loads(record.payload_json)
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict) or validate_record(payload):
        return None
    package_id = build_package(
        [payload], settings.consumer_id, settings, session
    )
    record.packaged_in = package_id
    pkg = session.get(Package, package_id)
    if pkg is None:
        return None
    return {
        "package_id": pkg.package_id,
        "manifest_sha256": pkg.manifest_sha256,
        "new_revision": record.revision,
    }


def _request_records(session, logical_id: str) -> list[tuple[Record, dict]]:
    out = []
    for rec in records_for(session, logical_id):
        try:
            out.append((rec, json.loads(rec.payload_json)))
        except ValueError:
            continue
    return out


def _dedupe_hit(
    session,
    *,
    source: Source,
    asset: MediaAsset,
    variant: str,
    preset: str | None,
    config_version: str,
) -> tuple[str | None, str | None]:
    """Find an existing successful pass matching
    (logical_id, variant, preset, config_version, media sha256).

    Returns ``(deduped_from, record_id)`` or ``(None, None)``. Only
    ``succeeded`` attempts count — a failed pass never blocks a new
    request (contract §9.4).
    """
    for rec, payload in _request_records(session, source.logical_id):
        if payload.get("record_kind") != "ocr_page":
            continue
        if payload.get("image_sha256") != asset.sha256:
            continue
        ocr = payload.get("ocr") or {}
        for attempt in ocr.get("attempts") or []:
            if attempt.get("status") != "succeeded":
                continue
            if attempt.get("image_operation") != variant:
                continue
            if attempt.get("config_version") != config_version:
                continue
            if variant == "crop_bottom":
                region = attempt.get("region") or {}
                if region.get("kind") != "bottom_fraction":
                    continue
                if preset_for_fraction(region.get("fraction")) != preset:
                    continue
            return (
                attempt.get("request_id") or rec.record_id,
                rec.record_id,
            )
    return None, None


class SameLogicalBusyError(RuntimeError):
    """Retryable: another ocr_request job for this logical_id is running."""


def _check_single_flight(session, job: Job, logical_id: str) -> None:
    """Contract §9.4 — at most one running ``ocr_request`` per logical_id.

    Deterministic: among running same-logical jobs the *oldest*
    (created_at, then job_id) proceeds; younger claimants requeue via a
    retryable raise. Attempts were bumped at claim, so request jobs run
    with ``max_attempts=8`` for requeue headroom (response ``attempt``
    still reports min(attempts,3) per §9.5).
    """
    blocker = (
        session.execute(
            select(Job.job_id)
            .where(
                Job.kind == "ocr_request",
                Job.logical_id == logical_id,
                Job.state == "running",
                Job.job_id != job.job_id,
                or_(
                    Job.created_at < job.created_at,
                    and_(
                        Job.created_at == job.created_at,
                        Job.job_id < job.job_id,
                    ),
                ),
            )
            .limit(1)
        )
        .scalar()
    )
    if blocker is not None:
        raise SameLogicalBusyError(
            f"ocr_request {blocker} already running for {logical_id}"
        )


def handle_ocr_request(session, job: Job, settings) -> dict:
    payload = json.loads(job.payload_json or "{}")
    request_id = payload.get("request_id") or job.request_id
    if not request_id:
        raise ValueError("ocr_request payload missing request_id")
    req = session.get(OcrRequest, request_id)
    if req is None:
        raise LookupError(f"ocr_requests row {request_id} not found")
    _check_single_flight(session, job, req.logical_id)
    req.state = "running"

    variant = req.variant
    try:
        preset = normalize_preset(variant, req.preset)
    except ValueError as exc:
        _request_terminal_error(session, req, job, "unsupported_variant", str(exc))

    source = session.get(Source, req.logical_id)
    if source is None or not source.attachment_id:
        _request_terminal_error(
            session,
            req,
            job,
            "unknown_source",
            f"logical_id {req.logical_id} is not an image page",
        )
    asset = session.get(MediaAsset, source.attachment_id)
    if asset is None:
        _request_terminal_error(
            session,
            req,
            job,
            "source_image_unavailable",
            f"media asset {source.attachment_id} not found",
        )
    prov = find_provenance(session, asset.attachment_id)
    now = utcnow()
    config_version = settings.ocr_config_version
    model = resolve_model(settings=settings)
    task = _ocr_task()
    page_index = source.page_index or 1

    # --- expiry re-check right before image read (contract §9.3) ---------
    source_expires = aware(source.image_expires_at)
    asset_expires = aware(asset.expires_at)
    expired = asset.state == "expired" or any(
        e is not None and e <= now for e in (source_expires, asset_expires)
    )
    if expired:
        attempt = attempt_dict(
            ocr_pass_id=str(uuid.uuid4()),
            model=model,
            task=task,
            image_operation=variant,
            region=(
                {"kind": "bottom_fraction", "fraction": crop_fraction(preset)}
                if variant == "crop_bottom"
                else {"kind": "full_image"}
            ),
            transform_chain=[],
            geometry_status=(
                "not_applicable" if task == "text_recognition" else "absent"
            ),
            status="source_image_expired",
            config_version=config_version,
            error={
                "code": "source_image_expired",
                "message": "image past 168h retention before OCR",
                "retryable": False,
            },
            started_at=_iso_now(),
            completed_at=_iso_now(),
            request_id=request_id,
        )
        _new_request_revision(
            session,
            source=source,
            asset=asset,
            prov=prov,
            attempt=attempt,
            lines=[],
            recorded_at=_iso_now(),
        )
        req.state = "expired"
        session.commit()  # survives the rollback the worker does on raise
        raise JobExpired("source_image_expired")

    path = _media_path(settings, asset)
    record_access(path, "media")
    if not path.is_file():
        _publish_request_failure(
            session,
            source=source,
            asset=asset,
            prov=prov,
            req=req,
            variant=variant,
            preset=preset,
            task=task,
            model=model,
            config_version=config_version,
            code="source_image_unavailable",
            message="media file absent before expiry",
            request_id=request_id,
        )
        _request_terminal_error(
            session, req, job, "source_image_unavailable",
            "media file absent before expiry",
        )
    try:
        data = path.read_bytes()
    except OSError as exc:
        _publish_request_failure(
            session,
            source=source,
            asset=asset,
            prov=prov,
            req=req,
            variant=variant,
            preset=preset,
            task=task,
            model=model,
            config_version=config_version,
            code="source_image_unavailable",
            message=clean_message(f"media file unreadable: {exc}"),
            request_id=request_id,
        )
        _request_terminal_error(
            session, req, job, "source_image_unavailable", str(exc)
        )

    # --- resolve the single page this logical_id covers ------------------
    try:
        if _is_pdf(path, data):
            pages = render_pdf_pages(data)
            if source.page_index is None:
                _request_terminal_error(
                    session, req, job, "unsupported_variant",
                    "logical_id is attachment-scope for multi-page media",
                )
            if source.page_index > len(pages):
                _request_terminal_error(
                    session, req, job, "source_image_unavailable",
                    f"page {source.page_index} beyond {len(pages)}-page PDF",
                )
            page_bytes = pages[source.page_index - 1]
        else:
            inspect_media(data)
            page_bytes = data
    except OcrError as exc:
        _publish_request_failure(
            session,
            source=source,
            asset=asset,
            prov=prov,
            req=req,
            variant=variant,
            preset=preset,
            task=task,
            model=model,
            config_version=config_version,
            code="source_image_unavailable",
            message=clean_message(f"media unreadable: {exc}"),
            request_id=request_id,
        )
        _request_terminal_error(
            session, req, job, "source_image_unavailable", str(exc)
        )

    # --- dedupe (logical_id, variant, preset, config_version, media sha) --
    deduped_from, record_id = _dedupe_hit(
        session,
        source=source,
        asset=asset,
        variant=variant,
        preset=preset,
        config_version=config_version,
    )
    if deduped_from is not None:
        req.state = "completed"
        req.deduped_from = deduped_from
        result_package = _publish_result_package(
            session, session.get(Record, record_id), settings
        )
        session.flush()
        return {
            "deduplicated": True,
            "deduped_from": deduped_from,
            "record_id": record_id,
            "request_id": request_id,
            **(result_package or {}),
        }

    frame = prepare_variant_frame(page_bytes, variant, preset)
    started = _iso_now()
    try:
        result = _invoke_ocr(
            frame.image_bytes,
            settings=settings,
            task=task,
            enable_rotate=frame.enable_rotate,
            filename=f"{req.logical_id}-{variant}.jpg",
        )
    except Exception as exc:  # noqa: BLE001 - taxonomy below decides
        if _is_retryable(exc) and not _exhausted(job):
            session.commit()  # keep req.state="running" + prior writes
            raise  # worker backoff; nothing recorded yet
        code = _error_code(exc)
        _publish_request_failure(
            session,
            source=source,
            asset=asset,
            prov=prov,
            req=req,
            variant=variant,
            preset=preset,
            task=task,
            model=model,
            config_version=config_version,
            code=code,
            message=clean_message(str(exc)),
            request_id=request_id,
            frame=frame,
            started_at=started,
        )
        _request_terminal_error(session, req, job, code, str(exc))

    completed = _iso_now()
    geometry_status, provider_lines = parse_provider_lines(
        result.words_info, task
    )
    ok = bool(result.lines)
    attempt = attempt_dict(
        ocr_pass_id=str(uuid.uuid4()),
        model=result.model,
        task=task,
        image_operation=variant,
        region=frame.region,
        transform_chain=frame.transform_chain,
        geometry_status=geometry_status,
        status="succeeded" if ok else "failed",
        config_version=config_version,
        submitted_frame=frame.submitted_frame_dict(),
        provider_lines=provider_lines,
        error=None
        if ok
        else {
            "code": "empty_result",
            "message": "provider returned no text",
            "retryable": False,
        },
        started_at=started,
        completed_at=completed,
        request_id=request_id,
    )
    record = _new_request_revision(
        session,
        source=source,
        asset=asset,
        prov=prov,
        attempt=attempt,
        lines=result.lines if ok else [],
        recorded_at=completed,
    )
    if not ok:
        _request_terminal_error(
            session, req, job, "empty_result", "provider returned no text"
        )
    req.state = "completed"
    result_package = _publish_result_package(session, record, settings)
    session.flush()
    return {
        "deduplicated": False,
        "new_revision": record.revision,
        "record_id": record.record_id,
        "logical_id": source.logical_id,
        "request_id": request_id,
        **(result_package or {}),
    }


def _publish_request_failure(
    session,
    *,
    source: Source,
    asset: MediaAsset,
    prov: Provenance | None,
    req: OcrRequest,
    variant: str,
    preset: str | None,
    task: str,
    model: str,
    config_version: str,
    code: str,
    message: str,
    request_id: str,
    frame: SubmittedFrame | None = None,
    started_at: str | None = None,
) -> None:
    """Contract §9.5: a completed-with-error job still publishes a new
    revision carrying the failed attempt — old text is kept verbatim."""
    attempt = attempt_dict(
        ocr_pass_id=str(uuid.uuid4()),
        model=model,
        task=task,
        image_operation=variant,
        region=(
            {"kind": "bottom_fraction", "fraction": crop_fraction(preset)}
            if variant == "crop_bottom"
            else {"kind": "full_image"}
        ),
        transform_chain=frame.transform_chain if frame else [],
        geometry_status=(
            "not_applicable" if task == "text_recognition" else "absent"
        ),
        status="failed",
        config_version=config_version,
        submitted_frame=frame.submitted_frame_dict() if frame else None,
        error={"code": code, "message": message[:500], "retryable": False},
        started_at=started_at,
        completed_at=_iso_now(),
        request_id=request_id,
    )
    _new_request_revision(
        session,
        source=source,
        asset=asset,
        prov=prov,
        attempt=attempt,
        lines=[],
        recorded_at=_iso_now(),
    )


# ---------------------------------------------------------------------------
# Registration (decision-sheet §0 worker contract)
# ---------------------------------------------------------------------------


def register(handlers: dict) -> None:
    handlers["ocr_default"] = handle_ocr_default
    handlers["ocr_request"] = handle_ocr_request


def register_sweepers(sweepers: list) -> None:
    sweepers.append(scan_media_for_ocr)

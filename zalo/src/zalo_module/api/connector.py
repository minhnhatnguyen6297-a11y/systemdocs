"""Connector-facing API — ``/connector/v1`` (MIN-103 slice B).

Port of ``notary_v2/routers/zalo_inbox.py``: bootstrap auth, HMAC webhook
events, signed config/commands reads, consent/policy/data-sync mutations,
media content, ops state, and the connector process trigger. All engine
logic lives in ``zalo_module.intake.engine`` — this module only adapts
exceptions onto the ``{"error": {"code", "message"}}`` envelope.

Route shape preserved from the legacy prefix ``/zalo/inbox`` → now
``/connector/v1`` (one deliberate rename; wire contract otherwise stable).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from zalo_module.api._json import StrictJsonError, parse_strict_body
from zalo_module.connector_proc import (
    connector_runtime_error,
    start_connector_process,
)
from zalo_module.database import session_scope
from zalo_module.intake.engine import (
    InboxConfigurationError,
    InboxConflict,
    InboxError,
    InboxTerminalError,
    InboxValidationError,
    apply_intake_consent,
    connector_state,
    data_sync_command,
    ingest_webhook_event,
    protected_media_object_keys,
    public_qr,
    request_source_sync,
    set_source_policy,
    source_ready,
    start_data_sync,
)
from zalo_module.intake.security import (
    command_secret,
    verify_webhook_signature,
)
from zalo_module.models import (
    ConnectorAccount,
    ConvSource,
    DataSyncRun,
    MediaAsset,
)
from zalo_module.settings import Settings

router = APIRouter(prefix="/connector/v1")


def _asset_path(settings: Settings, rel_path: str) -> "Path | None":
    """Resolve a stored ``rel_path`` under ``runtime_root`` with containment."""
    root = Path(settings.runtime_root).resolve()
    path = (root / str(rel_path)).resolve()
    if root != path and root not in path.parents:
        return None
    return path


def _request_settings(request: Request) -> Settings:
    return request.app.state.settings


def _error(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def _error_code(exc: Exception) -> str:
    if isinstance(exc, InboxValidationError):
        return "validation_failed"
    if isinstance(exc, InboxConflict):
        return "conflict"
    if isinstance(exc, InboxTerminalError):
        return "terminal_state"
    if isinstance(exc, InboxConfigurationError):
        return "service_unavailable"
    return "internal_error"


def _mapped(exc: Exception) -> JSONResponse:
    """Exception → error envelope (legacy ``_raise_http`` status mapping)."""
    if isinstance(exc, InboxConfigurationError):
        return _error(_error_code(exc), str(exc), 503)
    if isinstance(exc, (InboxConflict, InboxTerminalError)):
        return _error(_error_code(exc), str(exc), 409)
    if isinstance(exc, InboxError):
        return _error(_error_code(exc), str(exc), 400)
    raise exc


def _first_account(session: Session) -> ConnectorAccount | None:
    return (
        session.execute(
            select(ConnectorAccount).order_by(
                ConnectorAccount.created_at.asc(),
                ConnectorAccount.connector_account_id.asc(),
            )
        )
        .scalars()
        .first()
    )


def _source_public(source: ConvSource) -> dict[str, Any]:
    # ``enabled``/``desired_enabled``/``acked_enabled`` are wire booleans —
    # the connector filters on ``acked_enabled === true`` (parity with
    # legacy config payload at routers/zalo_inbox.py:477-487).
    return {
        "conv_source_id": source.conv_source_id,
        "conversation_id": source.conversation_id,
        "conversation_type": source.conversation_type,
        "source_type": source.source_type,
        "display_name": source.display_name,
        "enabled": bool(source.enabled),
        "desired_enabled": bool(source.enabled),
        "acked_enabled": bool(source.acked_enabled),
        "policy_version": source.policy_version,
        "policy_acked_version": source.policy_acked_version,
    }


@router.post("/connectors/onboard")
def onboard_connector(
    request: Request,
    settings: Settings = Depends(_request_settings),
) -> Any:
    if (
        not settings.bootstrap_secret
        or request.headers.get("x-zalo-bootstrap") != settings.bootstrap_secret
    ):
        # Legacy returns 403 here (routers/zalo_inbox.py:368).
        return _error("unauthorized", "Bootstrap secret không hợp lệ", 403)
    with session_scope(request.app.state.engine) as session:
        account = _first_account(session)
        if account is None:
            account = ConnectorAccount()
            session.add(account)
            session.flush()
        return {"connector_account_id": account.connector_account_id}


@router.post("/events")
async def receive_event(
    request: Request,
    settings: Settings = Depends(_request_settings),
) -> Any:
    body = await request.body()
    try:
        verify_webhook_signature(
            body,
            request.headers.get("x-zalo-timestamp", ""),
            request.headers.get("x-zalo-signature", ""),
            settings.webhook_secret,
        )
        payload = parse_strict_body(body)
        with session_scope(request.app.state.engine) as session:
            result = ingest_webhook_event(session, settings, payload)
            # Normalize ORM results to their public id while the session is
            # still bound (commit() expires attributes).
            if isinstance(result, ConvSource):
                result = result.conv_source_id
            elif isinstance(result, MediaAsset):
                result = result.attachment_id
            elif isinstance(result, DataSyncRun):
                result = result.run_id
    except StrictJsonError as exc:
        return _error("validation_failed", str(exc), 400)
    except InboxError as exc:
        return _mapped(exc)
    # ACK shape parity with legacy routers/zalo_inbox.py:420-426.
    event_type = payload.get("event_type")
    if event_type == "message":
        return {"ack": True, "components": result["components"]}
    if event_type in {"policy_ack", "source_sync_ack"}:
        return {"ack": True, **result}
    if event_type in {
        "data_sync_progress",
        "data_sync_complete",
        "data_sync_failed",
    }:
        return {"ack": True}
    # discovery / heartbeat / state / media / ignored — legacy emits a
    # single ``id`` key (None for dict results).
    if isinstance(result, dict):
        result = result.get("attachment_id")
    return {"ack": True, "id": result}


@router.get("/connectors/{account_id}/config")
def connector_config(
    account_id: str,
    request: Request,
    settings: Settings = Depends(_request_settings),
) -> Any:
    try:
        verify_webhook_signature(
            b"",
            request.headers.get("x-zalo-timestamp", ""),
            request.headers.get("x-zalo-signature", ""),
            settings.webhook_secret,
        )
    except InboxValidationError as exc:
        return _error("unauthorized", str(exc), 400)
    with session_scope(request.app.state.engine) as session:
        account = session.get(ConnectorAccount, account_id)
        if account is None:
            # Legacy 404 (routers/zalo_inbox.py:447).
            return _error("not_found", "Không tìm thấy connector", 404)
        sources = (
            session.execute(
                select(ConvSource).where(
                    ConvSource.connector_account_id == account_id
                )
            )
            .scalars()
            .all()
        )
        return {
            "listener_generation": account.listener_generation,
            "policy_version": account.policy_version,
            "policy_acked_version": account.policy_acked_version,
            "source_sync_request_version": account.source_sync_request_version,
            "source_sync_acked_version": account.source_sync_acked_version,
            "sources": [_source_public(source) for source in sources],
            "protected_media_object_keys": protected_media_object_keys(session),
        }


@router.get("/connectors/{account_id}/commands/next")
def next_command(
    account_id: str,
    request: Request,
    settings: Settings = Depends(_request_settings),
) -> Any:
    try:
        verify_webhook_signature(
            b"",
            request.headers.get("x-zalo-timestamp", ""),
            request.headers.get("x-zalo-signature", ""),
            command_secret(settings.webhook_secret, account_id),
        )
    except InboxValidationError as exc:
        return _error("unauthorized", str(exc), 400)
    with session_scope(request.app.state.engine) as session:
        # Unknown-but-validly-signed account → 404 (legacy
        # routers/zalo_inbox.py:513-514), not a bare 204.
        if session.get(ConnectorAccount, account_id) is None:
            return _error("not_found", "Không tìm thấy connector", 404)
        command = data_sync_command(session, account_id)
        if command is None:
            return Response(status_code=204)
        return command


@router.post("/connectors/{account_id}/consent")
def apply_consent(
    account_id: str,
    request: Request,
    settings: Settings = Depends(_request_settings),
) -> Any:
    with session_scope(request.app.state.engine) as session:
        try:
            policy_version = apply_intake_consent(session, account_id)
        except InboxError as exc:
            return _mapped(exc)
        return {"policy_version": policy_version}


@router.post("/connectors/{account_id}/sources/refresh")
def refresh_sources(
    account_id: str,
    request: Request,
    settings: Settings = Depends(_request_settings),
) -> Any:
    with session_scope(request.app.state.engine) as session:
        try:
            version = request_source_sync(session, account_id)
        except InboxError as exc:
            return _mapped(exc)
        return {"source_sync_request_version": version}


@router.post("/connectors/{account_id}/data-sync")
def request_data_sync(
    account_id: str,
    request: Request,
    _body: dict = Body(default_factory=dict),
    settings: Settings = Depends(_request_settings),
) -> Any:
    with session_scope(request.app.state.engine) as session:
        try:
            run = start_data_sync(session, settings, account_id)
        except InboxError as exc:
            return _mapped(exc)
        # Legacy response shape (routers/zalo_inbox.py:541).
        return {"run_id": run.run_id, "status": run.status}


@router.patch("/sources/{source_id}")
def patch_source(
    source_id: str,
    request: Request,
    body: dict = Body(...),
    settings: Settings = Depends(_request_settings),
) -> Any:
    enabled = body.get("enabled")
    if not isinstance(enabled, bool):
        return _error("validation_failed", "enabled phải là boolean", 400)
    with session_scope(request.app.state.engine) as session:
        try:
            set_source_policy(session, source_id, enabled)
        except InboxError as exc:
            return _mapped(exc)
        source = session.get(ConvSource, source_id)
        # Legacy response shape (routers/zalo_inbox.py:702-708): the source
        # snapshot, not the policy version.
        return {
            "id": source.conv_source_id,
            "enabled": bool(source.enabled),
            "desired_enabled": bool(source.enabled),
            "acked_enabled": (
                None
                if source.acked_enabled is None
                else bool(source.acked_enabled)
            ),
            "pending": not source_ready(source),
        }


@router.get("/media/{attachment_id}/content")
def media_content(
    attachment_id: str,
    request: Request,
    settings: Settings = Depends(_request_settings),
) -> Any:
    with session_scope(request.app.state.engine) as session:
        asset = session.get(MediaAsset, attachment_id)
        if asset is None:
            # Legacy 404 (routers/zalo_inbox.py:715).
            return _error("not_found", "Không tìm thấy media", 404)
        path = _asset_path(settings, asset.rel_path)
        if path is None or not path.is_file():
            # Legacy maps the missing-file case through _raise_http → 400.
            return _error("not_found", "File media không còn", 400)
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".pdf": "application/pdf",
        }.get(path.suffix.lower(), "application/octet-stream")
        return FileResponse(path, media_type=media_type)


@router.get("/state")
def ops_state(
    request: Request,
    settings: Settings = Depends(_request_settings),
) -> Any:
    """Ops snapshot: connector/policy/sources/data-sync only.

    Deliberately excludes batch/media-grid consumer state (no ``ZaloBatch``
    in the module — MIN-95 territory).
    """
    with session_scope(request.app.state.engine) as session:
        account = _first_account(session)
        if account is None:
            return {
                "connector": {
                    "state": "login_required",
                    "listener_generation": 0,
                    "qr_image": None,
                    "storage_full": False,
                },
                "policy": {
                    "policy_version": 0,
                    "policy_acked_version": 0,
                    "source_sync_request_version": 0,
                    "source_sync_acked_version": 0,
                },
                "sources": [],
                "data_sync": None,
                "connector_error": connector_runtime_error(),
            }
        sources = (
            session.execute(
                select(ConvSource).where(
                    ConvSource.connector_account_id
                    == account.connector_account_id
                )
            )
            .scalars()
            .all()
        )
        running = session.execute(
            select(DataSyncRun).where(
                DataSyncRun.connector_account_id
                == account.connector_account_id,
                DataSyncRun.status == "running",
            )
        ).scalar_one_or_none()
        return {
            "connector": {
                "connector_account_id": account.connector_account_id,
                "state": connector_state(account),
                "listener_generation": account.listener_generation,
                "bound_zalo_id": account.bound_zalo_id,
                "qr_image": public_qr(account),
                "storage_full": bool(account.storage_full),
                "gap_started_at": account.gap_started_at,
                "last_seen_at": account.last_seen_at,
            },
            "policy": {
                "intake_consented": account.intake_consented_at is not None,
                "policy_version": account.policy_version,
                "policy_acked_version": account.policy_acked_version,
                "source_sync_request_version": (
                    account.source_sync_request_version
                ),
                "source_sync_acked_version": account.source_sync_acked_version,
            },
            "sources": [
                {
                    **_source_public(source),
                    "enabled_explicit": source.enabled_explicit,
                    # Ops surface keeps the legacy nullable shape (True /
                    # False / None = not-yet-acked), unlike the strict bool
                    # the connector-facing config payload requires.
                    "acked_enabled": (
                        None
                        if source.acked_enabled is None
                        else bool(source.acked_enabled)
                    ),
                    "last_activity_at": source.last_activity_at,
                }
                for source in sources
            ],
            "data_sync": (
                {
                    "run_id": running.run_id,
                    "status": running.status,
                    "cutoff_at": running.cutoff_at,
                    "deadline_at": running.deadline_at,
                    "counters": json.loads(running.counters_json),
                    "source_ids": json.loads(running.source_ids_json),
                    "started_at": running.started_at,
                }
                if running
                else None
            ),
            "connector_error": connector_runtime_error(),
        }


@router.post("/connectors/start")
async def start_connector(
    request: Request,
    settings: Settings = Depends(_request_settings),
) -> Any:
    body: dict = {}
    raw = await request.body()
    if raw:
        try:
            parsed = parse_strict_body(raw)
        except StrictJsonError as exc:
            return _error("validation_failed", str(exc), 400)
        if not isinstance(parsed, dict):
            return _error("validation_failed", "Body phải là JSON object", 400)
        body = parsed
    try:
        started = start_connector_process(
            settings,
            lambda: Session(request.app.state.engine),
            force_restart=bool(body.get("force_restart")),
            force_qr=bool(body.get("force_qr")),
        )
    except InboxConfigurationError as exc:
        return _error("service_unavailable", str(exc), 503)
    # Legacy body (routers/zalo_inbox.py:395); status stays 200 — the
    # module does not emit the legacy 202-on-spawn variant.
    return {"status": "starting" if started else "running"}

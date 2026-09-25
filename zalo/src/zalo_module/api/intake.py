"""Intake delivery API — ``/intake/v1`` status, pending feed, receipts.

Response shapes follow contracts/zalo-intake verbatim (SOT for API shapes):
``intake.service-status.v1`` (§10.1), ``intake.package-list.v1`` (§7.2),
``intake.receipt.v1`` (§7.3 — body and response are the same document), and
``intake.error.v1`` (§10.2) for every non-2xx outcome.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func, select

from zalo_module import __version__
from zalo_module.api._auth import IntakeRoute, require_consumer_auth
from zalo_module.api._json import StrictJsonError, parse_strict_body
from zalo_module.audit import record_access
from zalo_module.database import get_engine, session_scope
from zalo_module.delivery import ledger
from zalo_module.models import ListenerSession, Package
from zalo_module.settings import get_settings

# IntakeRoute translates ConsumerAuthError (raised by require_consumer_auth)
# into the intake.error.v1 401 envelope — no app-factory wiring needed.
router = APIRouter(prefix="/intake/v1", route_class=IntakeRoute)

# Statuses: sealed = READY published + awaiting ACK (the pending feed);
# acked = receipt accepted retained under §8.3 policy; expired = payload
# bytes evicted post-ACK (ledger row kept). `pending` is a pre-seal state
# nothing currently writes — never served as READY.
_PKG_SEALED = "sealed"

ACK_CAP_BYTES = 1 << 30  # 1 GiB post-ACK raw retention cap — contract §8.3

# Internal ValueError codes from delivery.ledger → (HTTP, contract code §11).
_RECEIPT_ERROR_MAP = {
    "schema_invalid": (400, "schema_invalid"),
    "package_not_found": (404, "package_unknown"),
    "package_conflict": (409, "package_conflict"),
    "consumer_mismatch": (409, "receipt_consumer_mismatch"),
    "manifest_mismatch": (409, "receipt_hash_mismatch"),
    "count_mismatch": (409, "receipt_count_mismatch"),
}

# Engines are cheap to reuse; keyed by db_url so tests/app can coexist.
_engines: dict = {}


def _deps(request: Request):
    """Resolve ``(settings, engine)``.

    Prefers ``app.state.settings`` / ``app.state.engine`` when the app factory
    (slice E) wires them; otherwise falls back to env settings + a cached
    engine per db_url. See report: app.state attribute names are an
    assumption to confirm with slice E.
    """
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


def _parse_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/status")
def service_status(request: Request) -> dict:
    settings, engine = _deps(request)
    now = datetime.now(timezone.utc)
    with session_scope(engine) as session:
        latest = session.execute(
            select(
                ListenerSession.session_id,
                ListenerSession.state,
                ListenerSession.last_heartbeat_at,
            )
            .order_by(ListenerSession.observed_at.desc())
            .limit(1)
        ).first()
        pending_rows = session.execute(
            select(Package.sequence, Package.created_at)
            .where(Package.status == _PKG_SEALED)
            .order_by(Package.sequence)
        ).all()
        ack_dirs = session.execute(
            select(Package.dir_rel_path).where(Package.status == "acked")
        ).all()

    if latest is None:
        listener = {"state": "disconnected"}
    else:
        listener = {"state": latest.state}
        if latest.session_id:
            listener["session_id"] = latest.session_id
        if latest.last_heartbeat_at:
            listener["last_heartbeat_at"] = latest.last_heartbeat_at

    pending = {"packages": len(pending_rows)}
    if pending_rows:
        oldest_seq, oldest_created = pending_rows[0]
        pending["oldest_sequence"] = oldest_seq
        pending["oldest_age_seconds"] = max(
            0, int((now - _parse_iso(oldest_created)).total_seconds())
        )

    ack_bytes = 0
    for (rel,) in ack_dirs:
        pkg_dir = Path(settings.runtime_root) / rel
        # No record_access here: /status is polled — the audit trail only
        # logs real byte serves (manifest/records/READY endpoints), not a
        # stats pass over package dirs.
        if pkg_dir.is_dir():
            for f in pkg_dir.iterdir():
                if f.is_file():
                    ack_bytes += f.stat().st_size
    storage = {
        "ack_bytes": ack_bytes,
        "ack_cap_bytes": ACK_CAP_BYTES,
        "ack_warn": 5 * ack_bytes >= 4 * ACK_CAP_BYTES,
    }

    return {
        "schema_version": "intake.service-status.v1",
        "producer": {"service": "zalo-intake", "build_id": __version__},
        "observed_at": now.isoformat(),
        "listener": listener,
        "pending": pending,
        "storage": storage,
        # zca-js 2.1.2 emits undo (recall) + reaction, never edit (contract §10.1).
        "capabilities": {
            "source_event_types": {
                "recall": "supported",
                "reaction": "supported",
                "edit": "unsupported",
            }
        },
    }


@router.get("/packages", dependencies=[Depends(require_consumer_auth)])
def list_packages(
    request: Request,
    after: int = 0,
    until_sequence: int | None = None,
    limit: int = 100,
    delivery: str = "pending",
):
    settings, engine = _deps(request)
    if delivery != "pending":
        return _error(400, "schema_invalid", "only delivery=pending is served")
    if after < 0 or (until_sequence is not None and until_sequence < 0):
        return _error(400, "schema_invalid", "sequence cursors must be >= 0")
    if limit < 1:
        return _error(400, "schema_invalid", "limit must be >= 1")
    limit = min(limit, 100)  # contract §7.2/§3.6 cap

    with session_scope(engine) as session:
        if until_sequence is None:
            # First page of a sync run fixes the high-water mark (§7.2).
            until_sequence = (
                session.execute(
                    select(func.max(Package.sequence)).where(
                        Package.status == _PKG_SEALED,
                        Package.consumer_id == settings.consumer_id,
                    )
                ).scalar()
                or 0
            )
        # Plain columns — ORM instances would detach after session close.
        rows = session.execute(
            select(Package.package_id, Package.sequence, Package.manifest_sha256)
            .where(
                Package.status == _PKG_SEALED,
                Package.consumer_id == settings.consumer_id,
                Package.sequence > after,
                Package.sequence <= until_sequence,
            )
            .order_by(Package.sequence)
            .limit(limit + 1)
        ).all()

    has_more = len(rows) > limit
    page = rows[:limit]
    return {
        "schema_version": "intake.package-list.v1",
        "packages": [
            {
                "package_id": p.package_id,
                "sequence": p.sequence,
                "manifest_sha256": p.manifest_sha256,
            }
            for p in page
        ],
        "next_after": page[-1].sequence if page else after,
        "until_sequence": until_sequence,
        "has_more": has_more,
    }


# --- package byte endpoints (contract §7.2) ---------------------------------
#
# Byte-exact re-serves of the three package files. Both the contract path
# (…/manifest, …/records, …/ready) and the on-disk file name (…/manifest.json,
# …/records.jsonl, …/READY.json) are routed to the same handler — the task
# spec spells the file names, the contract spells the API names.
_PACKAGE_FILE_ROUTES = {
    "manifest": ("manifest.json", "application/json"),
    "manifest.json": ("manifest.json", "application/json"),
    "records": ("records.jsonl", "application/x-ndjson"),
    "records.jsonl": ("records.jsonl", "application/x-ndjson"),
    "ready": ("READY.json", "application/json"),
    "READY.json": ("READY.json", "application/json"),
}


def _package_file(request: Request, package_id: str, name: str):
    settings, engine = _deps(request)
    file_name, media_type = _PACKAGE_FILE_ROUTES[name]
    with session_scope(engine) as session:
        pkg = session.get(Package, package_id)
        rel = pkg.dir_rel_path if pkg is not None else None
    if rel is None:
        return _error(404, "package_unknown", f"unknown package_id {package_id}")
    path = Path(settings.runtime_root) / rel / file_name
    record_access(path, "package")
    if not path.is_file():
        # Expired (payload evicted) or manually removed — the consumer sees
        # the package as unavailable.
        return _error(404, "package_unknown", f"package {package_id} has no {file_name}")
    return FileResponse(path, media_type=media_type)


# routes.py-style registration: one handler per contract/file spelling.
for _name in _PACKAGE_FILE_ROUTES:

    def _make(name: str):
        @router.get(
            f"/packages/{{package_id}}/{name}",
            dependencies=[Depends(require_consumer_auth)],
        )
        def _serve(package_id: str, request: Request):
            return _package_file(request, package_id, name)

        return _serve

    _make(_name)


@router.post("/receipts", dependencies=[Depends(require_consumer_auth)])
async def post_receipt(request: Request):
    settings, engine = _deps(request)
    raw = await request.body()
    if len(raw) > 16 * 1024:  # receipt body limit — contract §3.6
        return _error(413, "request_too_large", "receipt body exceeds 16 KiB")
    try:
        receipt = parse_strict_body(raw)
    except StrictJsonError as exc:
        return _error(400, "json_invalid", str(exc))

    with session_scope(engine) as session:
        try:
            ledger.record_receipt(receipt, session, settings)
        except ValueError as exc:
            status_code, code = _RECEIPT_ERROR_MAP.get(
                str(exc), (400, "schema_invalid")
            )
            return _error(status_code, code, str(exc))
        pkg = session.get(Package, receipt["package_id"])
        stored = json.loads(pkg.receipt_json)

    # Response is the stored intake.receipt.v1 document itself (contract §7.3).
    return stored

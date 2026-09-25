"""Zalo listener engine — MIN-103 slice B port of notary_v2 services.

Parity-first port of ``notary_v2/services/zalo_inbox.py`` producer-side
functions onto the module schema (m0001 contract tables + m0002 engine
tables). Deliberate differences vs the baseline are tracked in
``docs/migration-notes.md`` — the notable ones:

- No FastAPI/UploadFile imports; ``InboxError`` hierarchy is module-local.
- Message/media dedupe anchors on ``journal_entries.source_key`` (unique)
  instead of the legacy ``zalo_message_texts`` / ``zalo_media`` unique keys;
  ``event_json`` stores ``{"component": ..., "result_id": ...}`` so
  same-identity-different-payload conflicts keep parity.
- Text-quota FIFO eviction (baseline services/zalo_inbox.py:717-740) is NOT
  ported — retention is uniform 168h per contract [MIN-94].
- ``data_sync_runs`` JSON columns are TEXT (canonical JSON strings);
  timestamps are TEXT ISO-8601; booleans are INTEGER.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from zalo_module.models import (
    ConnectorAccount,
    ConvSource,
    DataSyncRun,
    JournalEntry,
    ListenerSession,
    MediaAsset,
    Record,
    Source,
)
from zalo_module.storage.media import register_media

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from zalo_module.settings import Settings

UTC = timezone.utc
QR_TTL_SECONDS = 100
MY_DOCUMENTS_REALTIME_VERIFIED = False
SUPPORTED_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}


class InboxError(Exception):
    pass


class InboxValidationError(InboxError):
    pass


class InboxConfigurationError(InboxError):
    pass


class InboxConflict(InboxError):
    pass


class InboxTerminalError(InboxError):
    pass


# --- time / identity helpers -------------------------------------------------


def utcnow() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | str | None) -> datetime | None:
    """Coerce a stored TEXT ISO value or datetime to an aware UTC datetime."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _iso(value: datetime | str | None) -> str | None:
    """Canonical stored/wire timestamp: aware UTC, ``Z`` suffix."""
    if value is None:
        return None
    if isinstance(value, str):
        value = _aware(value)
        if value is None:
            return None
        return value.isoformat().replace("+00:00", "Z")
    aware = _aware(value) or value
    return aware.isoformat().replace("+00:00", "Z")


def _uuid() -> str:
    return str(uuid.uuid4())


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return _aware(value) or value
    if not isinstance(value, str):
        raise InboxValidationError("Timestamp bắt buộc")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError as exc:
        raise InboxValidationError("Timestamp không hợp lệ") from exc


def _canonical_digest(payload: dict[str, Any]) -> str:
    packed = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(packed.encode()).hexdigest()


def _canonical_json(value: Any) -> str:
    """Canonical JSON text for JSON-valued TEXT columns (stable CAS compare)."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _media_root(settings: "Settings") -> Path:
    return Path(settings.runtime_root) / "media"


# --- connector account state -------------------------------------------------


def public_qr(
    account: ConnectorAccount, *, now: datetime | None = None
) -> str | None:
    if not account.qr_image:
        return None
    expires = _aware(account.qr_expires_at)
    if expires is None or expires <= (_aware(now) or utcnow()):
        return None
    return account.qr_image


def connector_state(
    account: ConnectorAccount,
    *,
    now: datetime | None = None,
    stale_after_seconds: int = 45,
) -> str:
    if account.session_state == "login_required":
        return "login_required"
    if account.session_state == "disconnected":
        return "disconnected"
    seen = _aware(account.last_seen_at)
    current = _aware(now) or utcnow()
    if seen is None or current - seen > timedelta(seconds=stale_after_seconds):
        return "disconnected"
    return "connected"


SOURCE_TYPES = {"friend", "group", "stranger", "my_documents"}


def _source_default(source_type: str | None) -> bool:
    return source_type in {"friend", "group", "my_documents"}


def _restage_policy_snapshot(
    session: "Session", account: ConnectorAccount
) -> int:
    session.execute(
        update(ConnectorAccount)
        .where(
            ConnectorAccount.connector_account_id
            == account.connector_account_id
        )
        .values(policy_version=ConnectorAccount.policy_version + 1)
    )
    session.flush()
    session.refresh(account)
    session.execute(
        update(ConvSource)
        .where(ConvSource.connector_account_id == account.connector_account_id)
        .values(policy_version=account.policy_version)
    )
    return account.policy_version


def _account_or_error(
    session: "Session", account_id: str
) -> ConnectorAccount:
    account = session.get(ConnectorAccount, account_id)
    if account is None:
        raise InboxValidationError("connector_account_id chưa onboard")
    return account


def source_ready(source: ConvSource) -> bool:
    return (
        source.acked_enabled is not None
        and source.policy_version == source.policy_acked_version
        and bool(source.enabled) == bool(source.acked_enabled)
    )


def _touch(account_or_source, now: datetime | None = None) -> None:
    """Maintain ``updated_at`` (legacy relied on onupdate; TEXT here)."""
    account_or_source.updated_at = _iso(_aware(now) or utcnow())


def apply_intake_consent(session: "Session", account_id: str) -> int:
    account = _account_or_error(session, account_id)
    account.intake_consented_at = _iso(utcnow())
    _touch(account)
    sources = (
        session.execute(
            select(ConvSource).where(
                ConvSource.connector_account_id == account.connector_account_id
            )
        )
        .scalars()
        .all()
    )
    for source in sources:
        if source.enabled_explicit is None:
            source.enabled = int(_source_default(source.source_type))
            source.enabled_explicit = 0
            _touch(source)
    _restage_policy_snapshot(session, account)
    session.commit()
    return account.policy_version


def set_source_policy(
    session: "Session", source_id: str, enabled: bool
) -> int:
    source = session.get(ConvSource, source_id)
    if source is None:
        raise InboxValidationError("Không tìm thấy nguồn")
    account = _account_or_error(session, source.connector_account_id)
    source.enabled = int(bool(enabled))
    source.enabled_explicit = 1
    _touch(source)
    _restage_policy_snapshot(session, account)
    session.commit()
    return account.policy_version


def ack_policy(
    session: "Session", account_id: str, policy_version: int
) -> int:
    account = _account_or_error(session, account_id)
    if policy_version != account.policy_version:
        raise InboxValidationError("policy_version không phải bản hiện hành")
    if policy_version == account.policy_acked_version:
        return policy_version
    sources = (
        session.execute(
            select(ConvSource).where(
                ConvSource.connector_account_id == account.connector_account_id
            )
        )
        .scalars()
        .all()
    )
    for source in sources:
        source.acked_enabled = int(bool(source.enabled))
        source.policy_acked_version = policy_version
        _touch(source)
    account.policy_acked_version = policy_version
    _touch(account)
    session.commit()
    return policy_version


def request_source_sync(session: "Session", account_id: str) -> int:
    account = _account_or_error(session, account_id)
    session.execute(
        update(ConnectorAccount)
        .where(
            ConnectorAccount.connector_account_id
            == account.connector_account_id
        )
        .values(
            source_sync_request_version=ConnectorAccount.source_sync_request_version
            + 1
        )
    )
    session.flush()
    session.refresh(account)
    _touch(account)
    session.commit()
    return account.source_sync_request_version


def ack_source_sync(
    session: "Session", account_id: str, source_sync_request_version: int
) -> int:
    account = _account_or_error(session, account_id)
    if source_sync_request_version != account.source_sync_request_version:
        raise InboxValidationError(
            "source_sync_request_version không phải bản hiện hành"
        )
    if source_sync_request_version == account.source_sync_acked_version:
        return source_sync_request_version
    account.source_sync_acked_version = source_sync_request_version
    _touch(account)
    session.commit()
    return source_sync_request_version


def _ack_version(payload: dict[str, Any], field: str) -> int:
    value = payload.get(field)
    if isinstance(value, bool):
        raise InboxValidationError(f"{field} không hợp lệ")
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError as exc:
            raise InboxValidationError(f"{field} không hợp lệ") from exc
    if not isinstance(value, int) or value < 0:
        raise InboxValidationError(f"{field} không hợp lệ")
    return value


def apply_connector_report(
    account: ConnectorAccount,
    reported_state: str,
    generation: int,
    observed_at: datetime,
    *,
    qr_login_success: bool = False,
    qr_image: str | None = None,
    storage_full: bool | None = None,
    bound_zalo_id: str | None = None,
) -> bool:
    previous_generation = account.listener_generation or 0
    was_receiving = account.session_state == "usable"
    if generation < previous_generation:
        return False
    if reported_state not in {"connected", "login_required", "disconnected"}:
        raise InboxValidationError("Trạng thái connector không hợp lệ")
    incoming_zalo_id = str(bound_zalo_id or "").strip()
    if bound_zalo_id is not None and not incoming_zalo_id:
        raise InboxValidationError("Định danh tài khoản Zalo không hợp lệ")
    if (
        incoming_zalo_id
        and account.bound_zalo_id
        and account.bound_zalo_id != incoming_zalo_id
    ):
        raise InboxConflict("Connector đã bind với tài khoản Zalo khác")
    if qr_login_success:
        if not incoming_zalo_id:
            raise InboxValidationError("Thiếu định danh tài khoản Zalo")
        account.bound_zalo_id = incoming_zalo_id

    account.listener_generation = generation
    observed_iso = _iso(observed_at)
    if qr_image is not None:
        account.qr_image = qr_image
        if qr_image:
            account.qr_expires_at = _iso(
                observed_at + timedelta(seconds=QR_TTL_SECONDS)
            )
        else:
            account.qr_expires_at = None
    if storage_full is not None:
        account.storage_full = int(bool(storage_full))

    if reported_state == "login_required":
        account.session_state = "login_required"
        account.last_seen_at = observed_iso
        if was_receiving and account.gap_started_at is None:
            account.gap_started_at = observed_iso
        _touch(account, observed_at)
        return True
    if account.session_state == "login_required" and not qr_login_success:
        return False
    if reported_state == "disconnected":
        account.session_state = "disconnected"
        account.last_seen_at = observed_iso
        if was_receiving and account.gap_started_at is None:
            account.gap_started_at = observed_iso
        _touch(account, observed_at)
        return True
    if reported_state == "connected":
        if (
            was_receiving
            and generation > previous_generation
            and account.gap_started_at is None
        ):
            account.gap_started_at = observed_iso
        account.session_state = "usable"
        account.last_seen_at = observed_iso
        if qr_login_success:
            account.qr_image = None
            account.qr_expires_at = None
        _touch(account, observed_at)
        return True
    return False


# --- media object validation --------------------------------------------------


def resolve_media_object(
    storage_root: str | Path,
    connector_account_id: str,
    media_object_key: str,
    mime_type: str,
    size_bytes: int,
) -> Path:
    """Containment + size + magic-bytes check under the media root."""
    if mime_type not in SUPPORTED_MIME:
        raise InboxValidationError("Loại media không được hỗ trợ")
    key = Path(media_object_key)
    if (
        key.is_absolute()
        or ".." in key.parts
        or not key.parts
        or key.parts[0] != connector_account_id
    ):
        raise InboxValidationError("media_object_key nằm ngoài storage cho phép")
    root = Path(storage_root).resolve()
    path = (root / key).resolve()
    if root != path and root not in path.parents:
        raise InboxValidationError("media_object_key nằm ngoài storage cho phép")
    if not path.is_file():
        raise InboxValidationError("File nguồn không còn")
    actual_size = path.stat().st_size
    if actual_size != int(size_bytes):
        raise InboxValidationError("Kích thước media không khớp metadata")
    prefix = path.read_bytes()[:8]
    matches = {
        "image/jpeg": prefix.startswith(b"\xff\xd8\xff"),
        "image/png": prefix.startswith(b"\x89PNG\r\n\x1a\n"),
        "application/pdf": prefix.startswith(b"%PDF-"),
    }
    if not matches[mime_type]:
        raise InboxValidationError("Nội dung media không khớp MIME")
    return path


# --- journal-backed dedupe ----------------------------------------------------
# Dedupe anchor: journal_entries.source_key (UNIQUE). Message text component
# -> key (account, conversation, msg_id); each attachment -> same + index.
# event_json stores {"component": <digest basis>, "result_id": <module id>}.


def _message_key(account_id: str, conversation_id: str, msg_id: str) -> str:
    return _canonical_digest(
        {
            "connector_account_id": account_id,
            "conversation_id": conversation_id,
            "msg_id": msg_id,
        }
    )


def _media_key(
    account_id: str, conversation_id: str, msg_id: str, attachment_index: int
) -> str:
    return _canonical_digest(
        {
            "connector_account_id": account_id,
            "conversation_id": conversation_id,
            "msg_id": msg_id,
            "attachment_index": attachment_index,
        }
    )


def _capture_key() -> str:
    """Audit-only journal key — unique per call, never a dedupe anchor."""
    return _canonical_digest({"capture": _uuid()})


def _journal(
    session: "Session",
    source_key: str,
    event_obj: Any,
    captured_at: datetime | str | None,
) -> str:
    capture_id = _uuid()
    session.add(
        JournalEntry(
            capture_id=capture_id,
            source_key=source_key,
            event_json=_canonical_json(event_obj)
            if not isinstance(event_obj, str)
            else event_obj,
            captured_at=_iso(captured_at) or _iso(utcnow()),
            recorded_at=_iso(utcnow()),
        )
    )
    return capture_id


def _journal_dedupe(
    session: "Session",
    source_key: str,
    component: dict,
    result_id: str | None,
    captured_at: datetime | str | None,
) -> str:
    return _journal(
        session,
        source_key,
        {"component": component, "result_id": result_id},
        captured_at,
    )


def _dedupe_row(session: "Session", source_key: str) -> JournalEntry | None:
    return session.execute(
        select(JournalEntry).where(JournalEntry.source_key == source_key)
    ).scalar_one_or_none()


def _dedupe_digest(row: JournalEntry) -> str:
    stored = json.loads(row.event_json)
    return _canonical_digest(stored.get("component", stored))


def _dedupe_result_id(row: JournalEntry) -> str | None:
    try:
        return json.loads(row.event_json).get("result_id")
    except (ValueError, AttributeError):
        return None


# --- conversation sources (conv_sources) --------------------------------------


def _source_from_payload(
    session: "Session",
    payload: dict[str, Any],
    *,
    require_source_type: bool = False,
) -> ConvSource:
    account_id = str(payload.get("connector_account_id") or "")
    conversation_id = str(payload.get("conversation_id") or "")
    conversation_type = str(payload.get("conversation_type") or "")
    display_name = str(payload.get("source_display_name") or "").strip()
    source_type = str(payload.get("source_type") or "")
    if (
        not account_id
        or not conversation_id
        or conversation_type not in {"user", "group"}
        or not display_name
        or (require_source_type and source_type not in SOURCE_TYPES)
    ):
        if require_source_type and source_type not in SOURCE_TYPES:
            raise InboxValidationError("source_type không hợp lệ")
        raise InboxValidationError("Metadata nguồn không hợp lệ")
    last_activity_provided = "last_activity_at" in payload
    last_activity = payload.get("last_activity_at")
    if last_activity is not None:
        last_activity = _iso(_parse_timestamp(last_activity))
    account = _account_or_error(session, account_id)
    source = session.execute(
        select(ConvSource).where(
            ConvSource.connector_account_id == account_id,
            ConvSource.conversation_id == conversation_id,
        )
    ).scalar_one_or_none()
    now_iso = _iso(utcnow())
    if source is None:
        enabled = (
            _source_default(source_type)
            if account.intake_consented_at and source_type
            else False
        )
        source = ConvSource(
            conv_source_id=_uuid(),
            connector_account_id=account_id,
            conversation_id=conversation_id,
            conversation_type=conversation_type,
            display_name=display_name,
            source_type=source_type or None,
            enabled=int(enabled),
            enabled_explicit=0 if account.intake_consented_at else None,
            policy_version=account.policy_version,
            last_activity_at=last_activity,
            created_at=now_iso,
            updated_at=now_iso,
        )
        session.add(source)
        session.flush()
        if account.intake_consented_at:
            _restage_policy_snapshot(session, account)
    else:
        source.display_name = display_name
        source.conversation_type = conversation_type
        _touch(source)
        if last_activity_provided:
            source.last_activity_at = last_activity
        if source_type:
            default_enabled = _source_default(source_type)
            if (
                account.intake_consented_at
                and source.enabled_explicit != 1
                and bool(source.enabled) != default_enabled
            ):
                source.enabled = int(default_enabled)
                _restage_policy_snapshot(session, account)
            source.source_type = source_type
    return source


# --- data sync -----------------------------------------------------------------


DATA_SYNC_COUNTERS = (
    "received",
    "duplicates",
    "imported_text",
    "imported_media",
    "media_download_failures",
)


def start_data_sync(
    session: "Session",
    settings: "Settings",
    account_id: str,
    now: datetime | None = None,
) -> DataSyncRun:
    account = _account_or_error(session, account_id)
    current = _aware(now) or utcnow()
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
    if account.intake_consented_at is None:
        raise InboxValidationError("Chưa đồng ý tiếp nhận dữ liệu")
    if connector_state(account, now=current) != "connected":
        raise InboxConflict("Connector chưa kết nối")
    if account.policy_version != account.policy_acked_version or any(
        not source_ready(source) for source in sources
    ):
        raise InboxConflict("Chính sách nguồn đang chờ đồng bộ")
    source_ids = sorted(
        source.conversation_id
        for source in sources
        if source.enabled
        and source.acked_enabled
        and source_ready(source)
        and source.source_type != "my_documents"
    )
    if not source_ids:
        raise InboxValidationError("Không có nguồn phù hợp để đồng bộ")
    run = DataSyncRun(
        run_id=_uuid(),
        connector_account_id=account.connector_account_id,
        status="running",
        cutoff_at=_iso(current),
        deadline_at=_iso(
            current + timedelta(seconds=settings.data_sync_timeout_seconds)
        ),
        source_ids_json=_canonical_json(source_ids),
        counters_json=_canonical_json({key: 0 for key in DATA_SYNC_COUNTERS}),
        started_at=_iso(current),
    )
    session.add(run)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        detail = str(getattr(exc, "orig", exc)).lower()
        if "unique constraint failed" not in detail or "data_sync" not in detail:
            raise
        raise InboxConflict("Đang có Data Sync hoạt động") from exc
    session.refresh(run)
    return run


def _timeout_data_sync_run(
    session: "Session",
    run: DataSyncRun,
    account_id: str,
    current: datetime,
) -> bool:
    result = session.execute(
        update(DataSyncRun)
        .where(
            DataSyncRun.run_id == run.run_id,
            DataSyncRun.connector_account_id == account_id,
            DataSyncRun.status == "running",
            DataSyncRun.deadline_at <= _iso(current),
        )
        .values(
            status="error",
            error_code="timeout",
            completed_at=_iso(current),
        )
    )
    return result.rowcount == 1


def data_sync_command(
    session: "Session", account_id: str, now: datetime | None = None
) -> dict[str, Any] | None:
    run = session.execute(
        select(DataSyncRun).where(
            DataSyncRun.connector_account_id == account_id,
            DataSyncRun.status == "running",
        )
    ).scalar_one_or_none()
    if run is None:
        return None
    current = _aware(now) or utcnow()
    if (_aware(run.deadline_at) or run.deadline_at) <= current:
        if _timeout_data_sync_run(session, run, account_id, current):
            session.commit()
        else:
            session.rollback()
            session.expire_all()
        return None
    return {
        "command_type": "data_sync",
        "run_id": run.run_id,
        "cutoff_at": _iso(run.cutoff_at),
        "deadline_at": _iso(run.deadline_at),
        "source_ids": json.loads(run.source_ids_json),
    }


def apply_data_sync_report(
    session: "Session", payload: dict[str, Any]
) -> DataSyncRun:
    event_type = payload.get("event_type")
    expected = {
        "schema_version",
        "event_type",
        "connector_account_id",
        "run_id",
        "counters",
    }
    if event_type == "data_sync_failed":
        expected.add("error_code")
    if payload.get("schema_version") != 1 or set(payload) != expected:
        raise InboxValidationError("Data Sync report không hợp lệ")
    if event_type not in {
        "data_sync_progress",
        "data_sync_complete",
        "data_sync_failed",
    }:
        raise InboxValidationError("Data Sync event không hợp lệ")
    counters = payload.get("counters")
    if (
        not isinstance(counters, dict)
        or set(counters) != set(DATA_SYNC_COUNTERS)
        or any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            for value in counters.values()
        )
    ):
        raise InboxValidationError("Data Sync counters không hợp lệ")
    error_code = payload.get("error_code")
    if event_type == "data_sync_failed" and (
        not isinstance(error_code, str)
        or not re.fullmatch(r"[a-z0-9_]{1,64}", error_code)
    ):
        raise InboxValidationError("Data Sync error_code không hợp lệ")
    run_id = str(payload.get("run_id") or "")
    account_id = str(payload.get("connector_account_id") or "")
    terminal_status = {
        "data_sync_complete": "completed_best_effort",
        "data_sync_failed": "error",
    }.get(event_type)
    for _attempt in range(3):
        session.expire_all()
        run = session.get(DataSyncRun, run_id)
        if run is None or run.connector_account_id != account_id:
            raise InboxConflict("Data Sync report không khớp account/run")
        run_counters = json.loads(run.counters_json)
        if run.status != "running":
            if (
                terminal_status == run.status
                and run_counters == counters
                and run.error_code == error_code
            ):
                return run
            raise InboxConflict("Data Sync run đã kết thúc")
        current = utcnow()
        if (_aware(run.deadline_at) or run.deadline_at) <= current:
            if _timeout_data_sync_run(session, run, account_id, current):
                session.commit()
                raise InboxConflict("Data Sync run đã hết hạn")
            session.rollback()
            continue
        prior_counters = dict(run_counters)
        if any(
            counters[key] < prior_counters[key] for key in DATA_SYNC_COUNTERS
        ):
            raise InboxConflict("Data Sync counters không được giảm")
        values: dict[str, Any] = {"counters_json": _canonical_json(counters)}
        if terminal_status:
            values.update(
                {
                    "status": terminal_status,
                    "error_code": error_code,
                    "completed_at": _iso(utcnow()),
                }
            )
        result = session.execute(
            update(DataSyncRun)
            .where(
                DataSyncRun.run_id == run_id,
                DataSyncRun.connector_account_id == account_id,
                DataSyncRun.status == "running",
                DataSyncRun.counters_json == _canonical_json(prior_counters),
            )
            .values(**values)
        )
        if result.rowcount == 1:
            session.commit()
            session.expire_all()
            return session.get(DataSyncRun, run_id)
        session.rollback()
    raise InboxConflict("Data Sync report xung đột đồng thời")


# --- record/source row helpers for ingest --------------------------------------


def _message_source(
    session: "Session",
    account_id: str,
    conversation_id: str,
    msg_id: str,
    sent_at: datetime,
    *,
    has_media: bool,
) -> Source:
    """Upsert the per-message provenance row (scope="msg").

    ``logical_id`` is the message-level identity the ``records`` row links to.
    """
    source = session.execute(
        select(Source).where(
            Source.scope == "msg",
            Source.account_id == account_id,
            Source.conversation_id == conversation_id,
            Source.provider_message_id == msg_id,
        )
    ).scalar_one_or_none()
    if source is not None:
        if has_media and not source.image_available:
            source.image_available = 1
            source.image_expires_at = _iso(sent_at + timedelta(hours=168))
        return source
    source = Source(
        logical_id=_uuid(),
        scope="msg",
        account_id=account_id,
        conversation_id=conversation_id,
        provider_message_id=msg_id,
        captured_at=_iso(sent_at),
        current_revision=1,
        image_available=1 if has_media else 0,
        enabled=1,
        image_expires_at=_iso(sent_at + timedelta(hours=168))
        if has_media
        else None,
    )
    session.add(source)
    session.flush()
    return source


def _message_record(
    session: "Session",
    source: Source,
    component: dict,
    sent_at: datetime,
    conv_source: ConvSource,
) -> str:
    """Insert the ``message_text`` record; returns ``record_id``.

    The payload validates against ``schemas/raw-record.schema.json`` —
    module-internal fields (``conv_source_id``, attachment descriptors)
    live on the dedupe ``journal_entries.event_json`` instead [MIN-97].
    """
    record_id = _uuid()
    now_iso = _iso(utcnow())
    payload: dict[str, Any] = {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "message_text",
        "record_id": record_id,
        "logical_id": source.logical_id,
        "revision": 1,
        "captured_at": _iso(sent_at),
        "recorded_at": now_iso,
        "source": {
            "provider": "zalo_personal",
            "account_id": component["connector_account_id"],
            "conversation_id": component["conversation_id"],
            "conversation_type": conv_source.conversation_type,
            "provider_message_id": component["msg_id"],
            "sender_id": component["sender_id"],
            "source_sent_at": component["sent_at"],
        },
        "message": {"text": component["raw_text"]},
    }
    payload_json = _canonical_json(payload)
    session.add(
        Record(
            record_id=record_id,
            logical_id=source.logical_id,
            revision=1,
            kind="message_text",
            canonical_sha256=hashlib.sha256(
                payload_json.encode("utf-8")
            ).hexdigest(),
            payload_json=payload_json,
            captured_at=_iso(sent_at),
            recorded_at=now_iso,
        )
    )
    return record_id


def _source_event_record(
    session: "Session",
    source: ConvSource,
    payload: dict[str, Any],
) -> str:
    """Discovery event → ``source_event`` record (journal-only alternative
    rejected per sheet §4 default)."""
    src_row = Source(
        logical_id=_uuid(),
        scope="source_event",
        account_id=source.connector_account_id,
        conversation_id=source.conversation_id,
        captured_at=_iso(utcnow()),
        current_revision=1,
        image_available=0,
        enabled=int(bool(source.enabled)),
    )
    session.add(src_row)
    session.flush()
    record_id = _uuid()
    now_iso = _iso(utcnow())
    # Internal envelope — deliberately NO ``schema_version`` claim: the
    # contract ``event_body`` enum only covers recall|reaction, so a
    # discovery payload cannot validate as intake.raw-record.v1 until the
    # contract gains a source_event body [MIN-97].
    doc: dict[str, Any] = {
        "record_kind": "source_event",
        "record_id": record_id,
        "logical_id": src_row.logical_id,
        "revision": 1,
        "captured_at": _iso(_parse_timestamp(payload.get("last_activity_at")))
        if payload.get("last_activity_at") is not None
        else now_iso,
        "recorded_at": now_iso,
        "source": {
            "provider": "zalo_personal",
            "account_id": source.connector_account_id,
            "conversation_id": source.conversation_id,
            "conversation_type": source.conversation_type,
            "conv_source_id": source.conv_source_id,
        },
        "event": {
            "event_type": "discovery",
            "observed_at": now_iso,
        },
    }
    payload_json = _canonical_json(doc)
    session.add(
        Record(
            record_id=record_id,
            logical_id=src_row.logical_id,
            revision=1,
            kind="source_event",
            canonical_sha256=hashlib.sha256(
                payload_json.encode("utf-8")
            ).hexdigest(),
            payload_json=payload_json,
            captured_at=doc["captured_at"],
            recorded_at=now_iso,
        )
    )
    return record_id


def _register_media_asset(
    session: "Session",
    path: Path,
    component: dict,
    sent_at: datetime,
) -> str:
    """Insert ``media_assets`` for one connector media object."""
    attachment_id = _uuid()
    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    rel_path = f"media/{component['media_object_key']}"
    register_media(attachment_id, sha256, rel_path, sent_at, session)
    return attachment_id


# --- ingest --------------------------------------------------------------------


def ingest_message_envelope(
    session: "Session", settings: "Settings", payload: dict[str, Any]
) -> dict[str, Any]:
    required = (
        "connector_account_id",
        "conversation_id",
        "conversation_type",
        "source_type",
        "source_display_name",
        "msg_id",
        "sender_id",
        "sent_at",
    )
    if (
        payload.get("schema_version") != 1
        or payload.get("event_type") != "message"
        or any(payload.get(field) is None for field in required)
    ):
        raise InboxValidationError("Message envelope thiếu field bắt buộc")
    account_id = str(payload["connector_account_id"])
    conversation_id = str(payload["conversation_id"])
    msg_id = str(payload["msg_id"])
    sender_id = str(payload["sender_id"])
    if not account_id or not conversation_id or not msg_id or not sender_id:
        raise InboxValidationError("Message envelope có định danh không hợp lệ")
    account = _account_or_error(session, account_id)
    sent_at = _parse_timestamp(payload["sent_at"])
    raw_text = payload.get("raw_text")
    if raw_text is not None and not isinstance(raw_text, str):
        raise InboxValidationError("raw_text không hợp lệ")
    attachments = payload.get("attachments", [])
    if not isinstance(attachments, list):
        raise InboxValidationError("attachments không hợp lệ")

    storage_root = _media_root(settings)
    checked: list[tuple[dict[str, Any], int, str, Path]] = []
    indexes: set[int] = set()
    for attachment in attachments:
        if not isinstance(attachment, dict) or any(
            attachment.get(field) is None
            for field in (
                "attachment_index",
                "media_object_key",
                "mime_type",
                "size_bytes",
            )
        ):
            raise InboxValidationError("Attachment thiếu field bắt buộc")
        index = attachment["attachment_index"]
        size = attachment["size_bytes"]
        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or index < 0
            or index in indexes
        ):
            raise InboxValidationError("attachment_index không hợp lệ")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise InboxValidationError("size_bytes không hợp lệ")
        indexes.add(index)
        path = resolve_media_object(
            storage_root,
            account_id,
            str(attachment["media_object_key"]),
            str(attachment["mime_type"]),
            size,
        )
        component = {
            "connector_account_id": account_id,
            "conversation_id": conversation_id,
            "msg_id": msg_id,
            "attachment_index": index,
            "media_object_key": str(attachment["media_object_key"]),
            "mime_type": str(attachment["mime_type"]),
            "size_bytes": size,
            "sent_at": _iso(sent_at),
        }
        checked.append((component, index, _canonical_digest(component), path))

    text_component = {
        "connector_account_id": account_id,
        "conversation_id": conversation_id,
        "msg_id": msg_id,
        "sender_id": sender_id,
        "sent_at": _iso(sent_at),
        "raw_text": raw_text,
    }
    existing_text = None
    if raw_text is not None:
        existing_text = _dedupe_row(
            session, _message_key(account_id, conversation_id, msg_id)
        )
        if existing_text is not None and _dedupe_digest(
            existing_text
        ) != _canonical_digest(text_component):
            raise InboxConflict("Message text trùng khóa nhưng payload khác")
    existing_media: dict[int, JournalEntry] = {}
    for _component, index, digest, _path in checked:
        row = _dedupe_row(
            session, _media_key(account_id, conversation_id, msg_id, index)
        )
        if row is not None and _dedupe_digest(row) != digest:
            raise InboxConflict("Message media trùng khóa nhưng payload khác")
        if row is not None:
            existing_media[index] = row

    source_payload = dict(payload, last_activity_at=_iso(sent_at))
    source = _source_from_payload(
        session, source_payload, require_source_type=True
    )
    eligible = (
        account.intake_consented_at is not None
        and source_ready(source)
        and bool(source.enabled)
        and source.source_type != "stranger"
        and (
            source.source_type != "my_documents"
            or MY_DOCUMENTS_REALTIME_VERIFIED
        )
    )
    text_status = (
        "absent"
        if raw_text is None
        else ("duplicate" if existing_text is not None else "ignored")
    )
    media_statuses = [
        {
            "attachment_index": index,
            "status": "duplicate" if index in existing_media else "ignored",
        }
        for _component, index, _digest, _path in checked
    ]
    text_id = _dedupe_result_id(existing_text) if existing_text else None
    media_ids = [
        _dedupe_result_id(existing_media[index])
        for _component, index, _digest, _path in checked
        if index in existing_media
    ]

    if eligible:
        imported_attachments: list[dict] = []
        if raw_text is not None or checked:
            msg_source = _message_source(
                session,
                account_id,
                conversation_id,
                msg_id,
                sent_at,
                has_media=bool(checked),
            )
        for component, index, digest, path in checked:
            if index in existing_media:
                continue
            attachment_id = _register_media_asset(
                session, path, component, sent_at
            )
            _journal_dedupe(
                session,
                _media_key(account_id, conversation_id, msg_id, index),
                component,
                attachment_id,
                sent_at,
            )
            media_ids.append(attachment_id)
            imported_attachments.append(
                {
                    "attachment_id": attachment_id,
                    "attachment_index": index,
                    "media_object_key": component["media_object_key"],
                    "mime_type": component["mime_type"],
                    "size_bytes": component["size_bytes"],
                }
            )
            next(
                item
                for item in media_statuses
                if item["attachment_index"] == index
            )["status"] = "imported"
        if raw_text is not None and existing_text is None:
            # [MIN-94] text-quota FIFO eviction dropped — retention is a
            # uniform 168h per contract; every eligible text is recorded.
            record_attachments = imported_attachments + [
                {
                    "attachment_id": _dedupe_result_id(
                        existing_media[index]
                    ),
                    "attachment_index": index,
                    "media_object_key": component["media_object_key"],
                    "mime_type": component["mime_type"],
                    "size_bytes": component["size_bytes"],
                }
                for component, index, _digest, _path in checked
                if index in existing_media
            ]
            text_id = _message_record(
                session,
                msg_source,
                text_component,
                sent_at,
                source,
            )
            _journal(
                session,
                _message_key(account_id, conversation_id, msg_id),
                {
                    "component": text_component,
                    "result_id": text_id,
                    # Module-internal linkage (not contract vocabulary):
                    # kept on the dedupe journal entry so the record
                    # payload itself stays intake.raw-record.v1-conformant
                    # [MIN-97]. ``_dedupe_digest`` reads ``component`` only.
                    "conv_source_id": source.conv_source_id,
                    "attachments": record_attachments,
                },
                sent_at,
            )
            text_status = "imported"
    # Audit row for the raw envelope — same commit as the dedupe rows so a
    # rejected/conflicting envelope leaves nothing behind (parity).
    _journal(session, _capture_key(), payload, sent_at)
    session.commit()
    return {
        "text_id": text_id,
        "media_ids": media_ids,
        "ignored": not eligible,
        "components": {"text": text_status, "media": media_statuses},
    }


def ingest_webhook_event(
    session: "Session", settings: "Settings", payload: dict[str, Any]
) -> Any:
    if payload.get("schema_version") != 1:
        raise InboxValidationError("schema_version không được hỗ trợ")
    event_type = payload.get("event_type")
    account_id = str(payload.get("connector_account_id") or "")
    account = session.get(ConnectorAccount, account_id)
    if account is None:
        raise InboxValidationError("connector_account_id chưa onboard")

    if event_type == "discovery":
        source = _source_from_payload(session, payload, require_source_type=True)
        _source_event_record(session, source, payload)
        _journal(session, _capture_key(), payload, utcnow())
        session.commit()
        return source
    if event_type == "policy_ack":
        if set(payload) != {
            "schema_version",
            "event_type",
            "connector_account_id",
            "policy_version",
        }:
            raise InboxValidationError("policy_ack không hợp lệ")
        result = {
            "policy_version": ack_policy(
                session, account_id, _ack_version(payload, "policy_version")
            )
        }
        _journal(session, _capture_key(), payload, utcnow())
        session.commit()
        return result
    if event_type == "source_sync_ack":
        if set(payload) != {
            "schema_version",
            "event_type",
            "connector_account_id",
            "source_sync_request_version",
        }:
            raise InboxValidationError("source_sync_ack không hợp lệ")
        result = {
            "source_sync_request_version": ack_source_sync(
                session,
                account_id,
                _ack_version(payload, "source_sync_request_version"),
            )
        }
        _journal(session, _capture_key(), payload, utcnow())
        session.commit()
        return result
    if event_type in {"heartbeat", "state"}:
        observed_at = _parse_timestamp(payload.get("observed_at"))
        received_at = utcnow()
        reported = str(payload.get("state") or "")
        changed = apply_connector_report(
            account,
            reported,
            int(payload.get("listener_generation", 0)),
            received_at,
            qr_login_success=bool(payload.get("qr_login_success")),
            qr_image=payload.get("qr_image"),
            storage_full=payload.get("storage_full"),
            bound_zalo_id=payload.get("bound_zalo_id"),
        )
        if changed:
            # Session log reflects accepted observations only (stale
            # generations / pre-login connects return False).
            session.add(
                ListenerSession(
                    session_id=_uuid(),
                    account_id=account.connector_account_id,
                    state=reported,
                    observed_at=_iso(observed_at),
                    last_heartbeat_at=_iso(received_at),
                )
            )
        _journal(session, _capture_key(), payload, observed_at)
        session.commit()
        return {"changed": changed, "state": connector_state(account)}
    if event_type == "message":
        return ingest_message_envelope(session, settings, payload)
    if event_type in {
        "data_sync_progress",
        "data_sync_complete",
        "data_sync_failed",
    }:
        run = apply_data_sync_report(session, payload)
        _journal(session, _capture_key(), payload, utcnow())
        session.commit()
        return run
    if event_type != "media":
        raise InboxValidationError("event_type không được hỗ trợ")

    required = (
        "msg_id",
        "attachment_index",
        "media_object_key",
        "mime_type",
        "size_bytes",
        "sent_at",
    )
    if any(payload.get(field) is None for field in required):
        raise InboxValidationError("Webhook media thiếu field bắt buộc")
    digest = _canonical_digest(payload)
    conversation_id = str(payload.get("conversation_id") or "")
    msg_id = str(payload["msg_id"])
    attachment_index = int(payload["attachment_index"])
    existing = _dedupe_row(
        session, _media_key(account_id, conversation_id, msg_id, attachment_index)
    )
    if existing is not None:
        if _dedupe_digest(existing) != digest:
            raise InboxConflict("Webhook trùng khóa nhưng payload khác")
        asset_id = _dedupe_result_id(existing)
        asset = (
            session.get(MediaAsset, asset_id) if asset_id else None
        )
        _journal(session, _capture_key(), payload, utcnow())
        session.commit()
        return asset if asset is not None else {"attachment_id": asset_id}

    source = _source_from_payload(session, payload)
    if (
        account.intake_consented_at is None
        or not source_ready(source)
        or not source.enabled
    ):
        _journal(session, _capture_key(), payload, utcnow())
        session.commit()
        return {"ignored": True}
    path = resolve_media_object(
        _media_root(settings),
        account_id,
        str(payload["media_object_key"]),
        str(payload["mime_type"]),
        int(payload["size_bytes"]),
    )
    sent_at = _parse_timestamp(payload["sent_at"])
    asset_id = _register_media_asset(
        session,
        path,
        {
            "media_object_key": str(payload["media_object_key"]),
        },
        sent_at,
    )
    _journal_dedupe(
        session,
        _media_key(account_id, conversation_id, msg_id, attachment_index),
        payload,
        asset_id,
        sent_at,
    )
    _journal(session, _capture_key(), payload, sent_at)
    session.commit()
    return session.get(MediaAsset, asset_id)


# --- connector config projection ------------------------------------------------


def protected_media_object_keys(session: "Session") -> list[str]:
    """Connector-vocabulary object keys of every non-expired media asset.

    [MIN-97] parity note: the legacy fed this from active ZaloBatch items;
    the module protects ALL live media (state != 'expired') — simpler and
    correct under the "chưa xóa được" semantics. Narrowing to only un-ACKed
    packages is a MIN-97 decision.
    """
    rows = (
        session.execute(
            select(MediaAsset.rel_path).where(MediaAsset.state != "expired")
        )
        .scalars()
        .all()
    )
    keys = []
    for rel_path in rows:
        rel = str(rel_path)
        keys.append(rel[6:] if rel.startswith("media/") else rel)
    return keys

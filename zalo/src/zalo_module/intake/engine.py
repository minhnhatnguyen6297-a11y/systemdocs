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

from sqlalchemy import select, text, update
from sqlalchemy.exc import IntegrityError

from zalo_module.models import (
    ConnectorAccount,
    ConvSource,
    DataSyncRun,
    Job,
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
        if was_receiving and generation > previous_generation:
            # Refresh every episode: a stale marker from an already-closed
            # gap would otherwise suppress detection of a NEW coverage loss
            # (``_closed_gap_before`` only counts markers newer than the
            # last certain coverage).
            account.gap_started_at = observed_iso
        account.session_state = "usable"
        account.last_seen_at = observed_iso
        if qr_login_success:
            account.qr_image = None
            account.qr_expires_at = None
        _touch(account, observed_at)
        return True
    return False


# --- listener session log ------------------------------------------------------
# Durable listener_sessions rows: one row per *applied* state transition.
# A same-state report is a heartbeat and only refreshes ``last_heartbeat_at``
# on the newest row; a newer listener_generation always opens a new row —
# a reconnect after restart is a new session even when the state repeats
# (contract: mỗi lần kết nối = một session_id mới). Restart coverage gaps
# stay on ``connector_accounts.gap_started_at`` and surface via ``/state``.


def _latest_listener_session(
    session: "Session", account_id: str
) -> ListenerSession | None:
    """Newest session row for the account (insertion order = rowid)."""
    return session.execute(
        select(ListenerSession)
        .where(ListenerSession.account_id == account_id)
        .order_by(text("rowid DESC"))
        .limit(1)
    ).scalar_one_or_none()


def _record_listener_session(
    session: "Session",
    account: ConnectorAccount,
    reported: str,
    observed_at: datetime,
    received_at: datetime,
    *,
    generation_bumped: bool = False,
    reason: str | None = None,
) -> str:
    """Persist an applied state report as a transition row or heartbeat.

    ``observed_at`` comes from the connector payload; ``last_heartbeat_at``
    is the module-side receipt time (backend-authoritative clock).
    """
    latest = _latest_listener_session(
        session, account.connector_account_id
    )
    if reason is not None:
        reason = str(reason)[:200] or None
    heartbeat = _iso(received_at)
    if (
        latest is not None
        and latest.state == reported
        and not generation_bumped
    ):
        latest.last_heartbeat_at = heartbeat
        if reason:
            latest.reason = reason
        return latest.session_id
    closed_gap = (
        _closed_gap_before(account, latest, received_at)
        if reported == "connected"
        else None
    )
    row = ListenerSession(
        session_id=_uuid(),
        account_id=account.connector_account_id,
        state=reported,
        observed_at=_iso(observed_at),
        last_heartbeat_at=heartbeat,
        reason=reason,
    )
    session.add(row)
    session.flush()
    _listener_session_record(
        session,
        account,
        row,
        received_at,
        reason=reason,
        uncertain_gap=closed_gap,
    )
    return row.session_id


def _closed_gap_before(
    account: ConnectorAccount,
    latest: ListenerSession | None,
    received_at: datetime,
) -> dict[str, Any] | None:
    """``uncertain_gap`` payload for a ``connected`` row that resumes coverage.

    ``ended_at`` is the module-observed receipt of this connect — the same
    clock as the record's ``listener.observed_at``/``captured_at``, so the
    embedded interval always ends at the session start it precedes. The
    ``started_at`` bound comes from two sources, mirroring ``listener_gaps``:

    - the previous session row when it was non-connected (a reported
      disconnect/login_required);
    - ``connector_accounts.gap_started_at`` — the persistent marker stamped
      when the module itself detected coverage loss (connector process
      death, or a listener restart while ``usable``). A stale marker from
      an already-closed gap must NOT reopen one: it only counts when it
      post-dates the last session observation.
    """
    ended = _aware(received_at)
    if ended is None:
        return None
    start: datetime | None = None
    if latest is not None and latest.state != "connected":
        # A reported disconnect/login_required bounds the interval. The
        # marker can never tighten it — it is stamped no earlier than that
        # row's own report — and a stale marker from an already-closed
        # episode must not stretch this gap back across a proven-connected
        # session.
        start = _aware(latest.observed_at)
    else:
        marker = _aware(account.gap_started_at)
        # Detection compares connector-observed times only (the marker is
        # stamped from the reporting event's ``observed_at``): the marker
        # must post-date the last session observation, so a stale marker
        # from an already-closed episode cannot reopen a gap.
        last_obs = _aware(latest.observed_at) if latest is not None else None
        if marker is not None and (last_obs is None or marker > last_obs):
            # Crash-type gap: coverage loss detected with no session row —
            # the listener died silently before this connect reported.
            # Per contract the start is an *estimate* = last certain
            # coverage (last heartbeat), not the detection time.
            start = (
                _aware(latest.last_heartbeat_at or latest.observed_at)
                if latest is not None
                else marker
            )
    if start is None or not start < ended:
        return None
    return {
        "started_at": _iso(start),
        "ended_at": _iso(ended),
        "start_is_estimate": True,
    }


def _listener_session_record(
    session: "Session",
    account: ConnectorAccount,
    row: ListenerSession,
    received_at: datetime,
    *,
    reason: str | None,
    uncertain_gap: dict[str, Any] | None = None,
) -> str:
    """Emit the schema-valid ``listener_session`` record for a session row.

    ``logical_id`` is the ``session_id`` itself — every connect is a new
    session and a new logical chain (contract §5.3), so a reconnect after
    crash/disconnect never revises the previous chain. Only row-creating
    transitions reach this helper; same-state heartbeats update the durable
    row in place and can never churn record revisions.
    """
    received_iso = _iso(received_at)
    src = session.get(Source, row.session_id)
    if src is None:
        src = Source(
            logical_id=row.session_id,
            scope="session",
            account_id=account.connector_account_id,
            conversation_id=None,
            provider_message_id=None,
            captured_at=received_iso,
            current_revision=0,
            image_available=0,
            enabled=1,
        )
        session.add(src)
        session.flush()
    revision = int(src.current_revision or 0) + 1
    prior = session.execute(
        select(Record).where(
            Record.logical_id == src.logical_id,
            Record.revision == revision - 1,
        )
    ).scalar_one_or_none()
    listener: dict[str, Any] = {
        "session_id": row.session_id,
        "state": row.state,
        # Contract: ``listener.observed_at`` is the module's observation of
        # the transition (= ``captured_at``); the connector-reported
        # timestamp lives on the durable ``listener_sessions`` row.
        "observed_at": received_iso,
    }
    if row.last_heartbeat_at:
        listener["last_heartbeat_at"] = row.last_heartbeat_at
    if reason:
        listener["reason"] = str(reason)[:200]
    if uncertain_gap is not None and row.state == "connected":
        listener["uncertain_gap"] = uncertain_gap
    record_id = _uuid()
    payload: dict[str, Any] = {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "listener_session",
        "record_id": record_id,
        "logical_id": src.logical_id,
        "revision": revision,
        "captured_at": received_iso,
        "recorded_at": received_iso,
        "source": {
            "provider": "zalo_personal",
            "account_id": account.connector_account_id,
        },
        "listener": listener,
    }
    if revision >= 2:
        if prior is None:
            raise InboxConflict("Listener session revision chain bị đứt")
        payload["supersedes"] = {
            "record_id": prior.record_id,
            "revision": prior.revision,
        }
    src.current_revision = revision
    payload_json = _canonical_json(payload)
    session.add(
        Record(
            record_id=record_id,
            logical_id=src.logical_id,
            revision=revision,
            kind="listener_session",
            canonical_sha256=hashlib.sha256(
                payload_json.encode("utf-8")
            ).hexdigest(),
            payload_json=payload_json,
            captured_at=received_iso,
            recorded_at=received_iso,
        )
    )
    return record_id


# --- media object validation --------------------------------------------------


def _check_media_object_key(
    connector_account_id: str, media_object_key: str
) -> None:
    """Containment check for a media object key (no file access).

    Failed/missing attachments carry the *reserved* object key even though
    no bytes arrived, so the key shape is validated separately.
    """
    key = Path(media_object_key)
    if (
        key.is_absolute()
        or ".." in key.parts
        or not key.parts
        or key.parts[0] != connector_account_id
    ):
        raise InboxValidationError("media_object_key nằm ngoài storage cho phép")


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
    _check_media_object_key(connector_account_id, media_object_key)
    key = Path(media_object_key)
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


def _dedupe_component(row: JournalEntry) -> dict:
    try:
        stored = json.loads(row.event_json)
    except (ValueError, AttributeError):
        return {}
    component = stored.get("component", stored)
    return component if isinstance(component, dict) else {}


def _media_dedupe_lookup(
    row: JournalEntry | None, component: dict
) -> str:
    """Classify a media dedupe row vs an incoming component.

    - ``new``:      no dedupe row yet.
    - ``same``:     identical digest, or an equivalent downloaded component
                    (same slot/mime/size on a different digest basis — e.g.
                    an envelope replay after a ``media`` supplement wrote
                    the dedupe row).
    - ``upgrade``:  the stored component was a ``failed`` marker and the
                    incoming component is the completed download at the
                    same object key — the only payload change allowed.
    - ``conflict``: same dedupe key, irreconcilable payload.
    """
    if row is None:
        return "new"
    if _dedupe_digest(row) == _canonical_digest(component):
        return "same"
    stored_component = _dedupe_component(row)
    if (
        stored_component.get("status") == "failed"
        and component.get("status") != "failed"
        and "size_bytes" in component
        and stored_component.get("media_object_key")
        == component.get("media_object_key")
    ):
        return "upgrade"
    if (
        stored_component.get("status") != "failed"
        and all(
            key in stored_component
            and key in component
            and stored_component[key] == component[key]
            for key in ("media_object_key", "mime_type", "size_bytes")
        )
    ):
        return "same"
    return "conflict"


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
    *,
    client_message_id: str | None = None,
) -> str:
    """Insert the ``message_text`` record; returns ``record_id``.

    The payload validates against ``schemas/raw-record.schema.json`` —
    module-internal fields (``conv_source_id``, attachment descriptors)
    live on the dedupe ``journal_entries.event_json`` instead [MIN-97].
    ``client_message_id`` keeps Zalo ``cliMsgId`` in the record's source
    block: recall/reaction events link back to the original message via
    ``cliMsgId``/``cMsgID`` (contract §5.2).
    """
    record_id = _uuid()
    now_iso = _iso(utcnow())
    source_block: dict[str, Any] = {
        "provider": "zalo_personal",
        "account_id": component["connector_account_id"],
        "conversation_id": component["conversation_id"],
        "conversation_type": conv_source.conversation_type,
        "provider_message_id": component["msg_id"],
        "sender_id": component["sender_id"],
        "source_sent_at": component["sent_at"],
    }
    if client_message_id:
        source_block["client_message_id"] = client_message_id
    payload: dict[str, Any] = {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "message_text",
        "record_id": record_id,
        "logical_id": source.logical_id,
        "revision": 1,
        "captured_at": _iso(sent_at),
        "recorded_at": now_iso,
        "source": source_block,
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
            # Internal discovery rows are never package payloads: the
            # sentinel keeps them out of ``packaged_in IS NULL`` selection
            # (contract §5.3 — discovery is not a packageable kind).
            packaged_in="__internal__",
        )
    )
    return record_id


# --- contract source events (recall / reaction) --------------------------------
#
# zca-js emits ``undo`` (recall) and ``reaction`` listener events; the
# connector normalizes them into ``event_type: "source_event"`` webhooks.
# Every observation becomes an immutable ``source_event`` record on its own
# logical id — the record never mutates the target message, it only points at
# it via ``event.target_*`` (contract §5.3/§5.4).

SOURCE_EVENT_SUBTYPES = {"recall", "reaction"}
# ``reaction_icon`` length bound (contract §5.4): 1–64 chars — the contract
# was amended because real zca-js tokens like ":handclap" exceed the
# provisional 1–4 draft bound.
SOURCE_EVENT_ICON_MAX = 64


def _source_event_key(
    account_id: str,
    conversation_id: str,
    subtype: str,
    target_provider_id: str,
    target_client_id: str | None,
    reaction_icon: str | None,
    sender_id: str | None,
) -> str:
    """Dedupe anchor for recall/reaction observations — derived from the
    event content so connector replays hash identically while distinct
    observations (different target/icon/actor) stay distinct."""
    return _canonical_digest(
        {
            "kind": "source_event",
            "connector_account_id": account_id,
            "conversation_id": conversation_id,
            "event_subtype": subtype,
            "target_provider_message_id": target_provider_id,
            "target_client_message_id": target_client_id,
            "reaction_icon": reaction_icon,
            "sender_id": sender_id,
        }
    )


def _source_event_contract_record(
    session: "Session",
    *,
    account_id: str,
    conversation_id: str,
    conversation_type: str,
    subtype: str,
    target_provider_id: str,
    target_client_id: str | None,
    reaction_icon: str | None,
    sender_id: str | None,
    sender_name: str | None,
    observed_at: datetime,
) -> str:
    """Create the ``sources`` row + schema-valid ``source_event`` record."""
    observed_iso = _iso(observed_at)
    src = Source(
        logical_id=_uuid(),
        scope="source_event",
        account_id=account_id,
        conversation_id=conversation_id,
        provider_message_id=target_provider_id,
        captured_at=observed_iso,
        current_revision=1,
        image_available=0,
        enabled=1,
    )
    session.add(src)
    session.flush()
    source_block: dict[str, Any] = {
        "provider": "zalo_personal",
        "account_id": account_id,
        "conversation_id": conversation_id,
        "conversation_type": conversation_type,
        "provider_message_id": target_provider_id,
    }
    if target_client_id:
        source_block["client_message_id"] = target_client_id
    if sender_id:
        source_block["sender_id"] = sender_id
    if sender_name:
        source_block["sender_display_name"] = sender_name
    event: dict[str, Any] = {
        "event_type": subtype,
        "target_provider_message_id": target_provider_id,
        "observed_at": observed_iso,
    }
    if target_client_id:
        event["target_client_message_id"] = target_client_id
    if reaction_icon is not None:
        event["reaction_icon"] = reaction_icon
    record_id = _uuid()
    payload: dict[str, Any] = {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "source_event",
        "record_id": record_id,
        "logical_id": src.logical_id,
        "revision": 1,
        "captured_at": observed_iso,
        "recorded_at": observed_iso,
        "source": source_block,
        "event": event,
    }
    payload_json = _canonical_json(payload)
    session.add(
        Record(
            record_id=record_id,
            logical_id=src.logical_id,
            revision=1,
            kind="source_event",
            canonical_sha256=hashlib.sha256(
                payload_json.encode("utf-8")
            ).hexdigest(),
            payload_json=payload_json,
            captured_at=observed_iso,
            recorded_at=observed_iso,
        )
    )
    return record_id


def _ingest_source_event(
    session: "Session", payload: dict[str, Any]
) -> dict[str, Any]:
    """Ingest one connector ``source_event`` (recall/reaction observation).

    Validation mirrors the record contract — malformed events are rejected
    (400/409) so the connector's durable outbox quarantines them after the
    retry bound instead of ever producing a schema-broken record. An
    identical replay dedupes to the stored record.
    """
    account_id = str(payload.get("connector_account_id") or "")
    conversation_id = str(payload.get("conversation_id") or "").strip()
    conversation_type = str(payload.get("conversation_type") or "")
    subtype = str(payload.get("event_subtype") or "")
    target_provider = str(
        payload.get("target_provider_message_id") or ""
    ).strip()
    raw_client = payload.get("target_client_message_id")
    raw_icon = payload.get("reaction_icon")
    if not conversation_id or conversation_type not in {"user", "group"}:
        raise InboxValidationError("source_event không hợp lệ")
    if subtype not in SOURCE_EVENT_SUBTYPES:
        raise InboxValidationError("source_event subtype không hợp lệ")
    if not target_provider:
        raise InboxValidationError("source_event thiếu định danh tin đích")
    if raw_client is not None and (
        not isinstance(raw_client, str) or not raw_client.strip()
    ):
        raise InboxValidationError("source_event client id không hợp lệ")
    target_client = raw_client.strip() if isinstance(raw_client, str) else None
    if subtype == "reaction":
        if not isinstance(raw_icon, str) or not (
            1 <= len(raw_icon) <= SOURCE_EVENT_ICON_MAX
        ):
            raise InboxValidationError("source_event reaction thiếu icon")
    elif raw_icon is not None:
        raise InboxValidationError("source_event recall không mang icon")
    icon = raw_icon if subtype == "reaction" else None
    sender_id = str(payload.get("sender_id") or "").strip() or None
    raw_name = payload.get("sender_display_name")
    sender_name = (
        raw_name.strip()[:200]
        if isinstance(raw_name, str) and raw_name.strip()
        else None
    )
    observed_raw = payload.get("observed_at")
    if observed_raw is not None:
        _parse_timestamp(observed_raw)  # shape check; module clock is used

    component = {
        "connector_account_id": account_id,
        "conversation_id": conversation_id,
        "event_subtype": subtype,
        "target_provider_message_id": target_provider,
        "target_client_message_id": target_client,
        "reaction_icon": icon,
        "sender_id": sender_id,
    }
    key = _source_event_key(
        account_id,
        conversation_id,
        subtype,
        target_provider,
        target_client,
        icon,
        sender_id,
    )
    existing = _dedupe_row(session, key)
    if existing is not None:
        if _dedupe_digest(existing) != _canonical_digest(component):
            raise InboxConflict("source_event trùng khóa nhưng payload khác")
        return {
            "record_id": _dedupe_result_id(existing),
            "duplicate": True,
        }
    observed_at = utcnow()  # module observation (contract: == captured_at)
    record_id = _source_event_contract_record(
        session,
        account_id=account_id,
        conversation_id=conversation_id,
        conversation_type=conversation_type,
        subtype=subtype,
        target_provider_id=target_provider,
        target_client_id=target_client,
        reaction_icon=icon,
        sender_id=sender_id,
        sender_name=sender_name,
        observed_at=observed_at,
    )
    _journal_dedupe(session, key, component, record_id, observed_at)
    _journal(session, _capture_key(), payload, observed_at)
    session.commit()
    return {"record_id": record_id, "duplicate": False}


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


def _register_missing_media_asset(
    session: "Session",
    component: dict,
    sent_at: datetime,
) -> str:
    """Insert a ``state='missing'`` media_assets row for a failed attachment.

    The connector reports the *reserved* object key even when the download
    never produced bytes — the row pins that slot so ops and OCR requests
    can see the missing media; ``sha256`` stays empty (no bytes observed).
    """
    attachment_id = _uuid()
    rel_path = f"media/{component['media_object_key']}"
    register_media(
        attachment_id, "", rel_path, sent_at, session, state="missing"
    )
    return attachment_id


def _attachment_source(
    session: "Session",
    account_id: str,
    conversation_id: str,
    msg_id: str,
    attachment_id: str,
    sent_at: datetime,
    *,
    image_available: bool,
    conv_source: ConvSource,
) -> Source:
    """Upsert the per-attachment provenance row (scope='attachment').

    ``logical_id`` lets OCR requests and status records address one
    attachment (contract logical_id vocabulary).
    """
    source = session.execute(
        select(Source).where(
            Source.scope == "attachment",
            Source.attachment_id == attachment_id,
        )
    ).scalar_one_or_none()
    if source is not None:
        if image_available and not source.image_available:
            source.image_available = 1
            source.image_expires_at = _iso(sent_at + timedelta(hours=168))
        return source
    source = Source(
        logical_id=_uuid(),
        scope="attachment",
        account_id=account_id,
        conversation_id=conversation_id,
        provider_message_id=msg_id,
        attachment_id=attachment_id,
        captured_at=_iso(sent_at),
        current_revision=0,
        image_available=1 if image_available else 0,
        enabled=int(bool(conv_source.enabled)),
        image_expires_at=_iso(sent_at + timedelta(hours=168))
        if image_available
        else None,
    )
    session.add(source)
    session.flush()
    return source


def _record_source_block(
    *,
    account_id: str,
    conversation_id: str,
    conversation_type: str,
    msg_id: str,
    sender_id: str | None,
    sent_at: datetime | str,
    attachment_id: str | None = None,
    attachment_index: int | None = None,
) -> dict[str, Any]:
    """Contract ``source`` block shared by status records."""
    block: dict[str, Any] = {
        "provider": "zalo_personal",
        "account_id": account_id,
        "conversation_id": conversation_id,
        "conversation_type": conversation_type,
        "provider_message_id": msg_id,
        "sender_id": sender_id,
        "source_sent_at": _iso(sent_at),
    }
    if attachment_id is not None:
        block["attachment_id"] = attachment_id
    if attachment_index is not None:
        block["attachment_index"] = attachment_index
    return block


def _processing_status_record(
    session: "Session",
    source: Source,
    source_block: dict[str, Any],
    code: str,
    captured_at: datetime | str,
    *,
    note: str | None = None,
) -> str:
    """Append a ``processing_status`` record revision for ``source``.

    Revisions are monotonic per ``logical_id``; rev>=2 carries
    ``supersedes`` pointing at the previous record (contract §5).
    """
    prev = session.execute(
        select(Record)
        .where(Record.logical_id == source.logical_id)
        .order_by(Record.revision.desc())
        .limit(1)
    ).scalar_one_or_none()
    revision = (prev.revision + 1) if prev is not None else 1
    record_id = _uuid()
    now_iso = _iso(utcnow())
    payload: dict[str, Any] = {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "processing_status",
        "record_id": record_id,
        "logical_id": source.logical_id,
        "revision": revision,
        "captured_at": _iso(captured_at),
        "recorded_at": now_iso,
        "source": source_block,
        "status": {"code": code},
    }
    if prev is not None:
        payload["supersedes"] = {
            "record_id": prev.record_id,
            "revision": prev.revision,
        }
    if note:
        payload["status"]["note"] = str(note)[:500]
    payload_json = _canonical_json(payload)
    session.add(
        Record(
            record_id=record_id,
            logical_id=source.logical_id,
            revision=revision,
            kind="processing_status",
            canonical_sha256=hashlib.sha256(
                payload_json.encode("utf-8")
            ).hexdigest(),
            payload_json=payload_json,
            captured_at=payload["captured_at"],
            recorded_at=now_iso,
        )
    )
    source.current_revision = revision
    return record_id


def _upgrade_missing_media_asset(
    session: "Session",
    dedupe_row: JournalEntry,
    asset: MediaAsset,
    path: Path,
    component: dict,
    sent_at: datetime,
    *,
    conv_source: ConvSource | None = None,
) -> str:
    """Flip a ``missing`` media asset to ``captured`` with the real bytes.

    Keeps the attachment identity (``attachment_id``/``rel_path``/expiry),
    rewrites the dedupe component to the downloaded basis so later replays
    dedupe cleanly, and appends a ``captured`` processing-status revision.
    """
    asset.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    asset.state = "captured"
    dedupe_row.event_json = _canonical_json(
        {"component": component, "result_id": asset.attachment_id}
    )
    att_source = session.execute(
        select(Source).where(
            Source.scope == "attachment",
            Source.attachment_id == asset.attachment_id,
        )
    ).scalar_one_or_none()
    if att_source is not None:
        if not att_source.image_available:
            att_source.image_available = 1
            att_source.image_expires_at = _iso(sent_at + timedelta(hours=168))
        _processing_status_record(
            session,
            att_source,
            _record_source_block(
                account_id=str(att_source.account_id),
                conversation_id=str(att_source.conversation_id),
                conversation_type=(
                    conv_source.conversation_type if conv_source else "user"
                ),
                msg_id=str(att_source.provider_message_id),
                sender_id=component.get("sender_id"),
                sent_at=sent_at,
                attachment_id=asset.attachment_id,
                attachment_index=component.get("attachment_index"),
            ),
            "captured",
            sent_at,
        )
    return asset.attachment_id


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
    raw_client_id = payload.get("client_message_id")
    if raw_client_id is not None and (
        not isinstance(raw_client_id, str) or not raw_client_id.strip()
    ):
        raise InboxValidationError("client_message_id không hợp lệ")
    client_message_id = (
        raw_client_id.strip() if isinstance(raw_client_id, str) else None
    )
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
    failed: list[tuple[dict[str, Any], int, str]] = []
    indexes: set[int] = set()
    for attachment in attachments:
        if not isinstance(attachment, dict):
            raise InboxValidationError("Attachment thiếu field bắt buộc")
        # Additive wire (MIN-94): ``status: "downloaded"|"failed"`` —
        # absent means downloaded (legacy envelopes stay valid).
        att_status = attachment.get("status", "downloaded")
        if att_status not in ("downloaded", "failed"):
            raise InboxValidationError("Attachment status không hợp lệ")
        required_fields = ("attachment_index", "media_object_key", "mime_type")
        required_fields += (
            ("error_code",) if att_status == "failed" else ("size_bytes",)
        )
        if any(attachment.get(field) is None for field in required_fields):
            raise InboxValidationError("Attachment thiếu field bắt buộc")
        index = attachment["attachment_index"]
        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or index < 0
            or index in indexes
        ):
            raise InboxValidationError("attachment_index không hợp lệ")
        indexes.add(index)
        mime_type = str(attachment["mime_type"])
        if mime_type not in SUPPORTED_MIME:
            raise InboxValidationError("Loại media không được hỗ trợ")
        media_object_key = str(attachment["media_object_key"])
        _check_media_object_key(account_id, media_object_key)
        component: dict[str, Any] = {
            "connector_account_id": account_id,
            "conversation_id": conversation_id,
            "msg_id": msg_id,
            "attachment_index": index,
            "media_object_key": media_object_key,
            "mime_type": mime_type,
            "sent_at": _iso(sent_at),
        }
        if att_status == "failed":
            # No bytes arrived: keep the reserved slot visible instead of
            # dropping the attachment or rejecting the envelope.
            error_code = str(attachment["error_code"])
            if not re.fullmatch(r"[a-z0-9_]{1,64}", error_code):
                raise InboxValidationError("Attachment error_code không hợp lệ")
            size = attachment.get("size_bytes")
            if size is not None:
                if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                    raise InboxValidationError("size_bytes không hợp lệ")
                component["size_bytes"] = size
            component["status"] = "failed"
            component["error_code"] = error_code
            failed.append((component, index, _canonical_digest(component)))
            continue
        size = attachment["size_bytes"]
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise InboxValidationError("size_bytes không hợp lệ")
        component["size_bytes"] = size
        path = resolve_media_object(
            storage_root,
            account_id,
            media_object_key,
            mime_type,
            size,
        )
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
    upgrade_media: dict[int, JournalEntry] = {}
    for _component, index, _digest, _path in checked:
        row = _dedupe_row(
            session, _media_key(account_id, conversation_id, msg_id, index)
        )
        verdict = _media_dedupe_lookup(row, _component)
        if verdict == "conflict":
            raise InboxConflict("Message media trùng khóa nhưng payload khác")
        if row is not None:
            if verdict == "upgrade":
                upgrade_media[index] = row
            existing_media[index] = row
    for _component, index, _digest in failed:
        row = _dedupe_row(
            session, _media_key(account_id, conversation_id, msg_id, index)
        )
        verdict = _media_dedupe_lookup(row, _component)
        if verdict != "same" and verdict != "new":
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
            "attachment_index": attachment["attachment_index"],
            "status": (
                "duplicate"
                if attachment["attachment_index"] in existing_media
                and attachment["attachment_index"] not in upgrade_media
                else "ignored"
            ),
        }
        for attachment in attachments
    ]
    text_id = _dedupe_result_id(existing_text) if existing_text else None
    media_ids = [
        _dedupe_result_id(existing_media[attachment["attachment_index"]])
        for attachment in attachments
        if attachment["attachment_index"] in existing_media
        and attachment["attachment_index"] not in upgrade_media
    ]

    if eligible:
        imported_attachments: list[dict] = []
        if raw_text is not None or checked or failed:
            msg_source = _message_source(
                session,
                account_id,
                conversation_id,
                msg_id,
                sent_at,
                has_media=bool(checked or failed),
            )
        for component, index, digest, path in checked:
            if index in existing_media and index not in upgrade_media:
                continue
            if index in upgrade_media:
                # missing → captured: the same attachment slot completes.
                asset_id = _dedupe_result_id(upgrade_media[index])
                asset = (
                    session.get(MediaAsset, asset_id) if asset_id else None
                )
                if asset is not None and asset.state == "missing":
                    attachment_id = _upgrade_missing_media_asset(
                        session,
                        upgrade_media[index],
                        asset,
                        path,
                        component,
                        sent_at,
                        conv_source=source,
                    )
                else:
                    attachment_id = _register_media_asset(
                        session, path, component, sent_at
                    )
                    upgrade_media[index].event_json = _canonical_json(
                        {"component": component, "result_id": attachment_id}
                    )
            else:
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
        for component, index, digest in failed:
            if index in existing_media:
                continue
            attachment_id = _register_missing_media_asset(
                session, component, sent_at
            )
            _journal_dedupe(
                session,
                _media_key(account_id, conversation_id, msg_id, index),
                component,
                attachment_id,
                sent_at,
            )
            media_ids.append(attachment_id)
            att_source = _attachment_source(
                session,
                account_id,
                conversation_id,
                msg_id,
                attachment_id,
                sent_at,
                image_available=False,
                conv_source=source,
            )
            _processing_status_record(
                session,
                att_source,
                _record_source_block(
                    account_id=account_id,
                    conversation_id=conversation_id,
                    conversation_type=source.conversation_type,
                    msg_id=msg_id,
                    sender_id=sender_id,
                    sent_at=sent_at,
                    attachment_id=attachment_id,
                    attachment_index=index,
                ),
                "media_missing",
                sent_at,
                note=component["error_code"],
            )
            imported_attachments.append(
                {
                    "attachment_id": attachment_id,
                    "attachment_index": index,
                    "media_object_key": component["media_object_key"],
                    "mime_type": component["mime_type"],
                    "status": "failed",
                }
            )
            next(
                item
                for item in media_statuses
                if item["attachment_index"] == index
            )["status"] = "missing"
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
                client_message_id=client_message_id,
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
    if event_type == "source_event":
        return _ingest_source_event(session, payload)
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
        generation = int(payload.get("listener_generation", 0))
        previous_generation = int(account.listener_generation or 0)
        changed = apply_connector_report(
            account,
            reported,
            generation,
            received_at,
            qr_login_success=bool(payload.get("qr_login_success")),
            qr_image=payload.get("qr_image"),
            storage_full=payload.get("storage_full"),
            bound_zalo_id=payload.get("bound_zalo_id"),
        )
        if changed:
            # Session log reflects accepted observations only (stale
            # generations / pre-login connects return False). Same-state
            # reports are heartbeats; a generation bump opens a new row.
            _record_listener_session(
                session,
                account,
                reported,
                observed_at,
                received_at,
                generation_bumped=generation > previous_generation,
                reason=payload.get("reason") or payload.get("error_code"),
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

    # Additive wire (MIN-94): ``status: "failed"`` + ``error_code`` marks a
    # media slot whose download failed; absent ``status`` means downloaded.
    media_status = payload.get("status", "downloaded")
    if media_status not in ("downloaded", "failed"):
        raise InboxValidationError("Webhook media status không hợp lệ")
    required = ["msg_id", "attachment_index", "media_object_key", "mime_type", "sent_at"]
    required.append("size_bytes" if media_status != "failed" else "error_code")
    if any(payload.get(field) is None for field in required):
        raise InboxValidationError("Webhook media thiếu field bắt buộc")
    conversation_id = str(payload.get("conversation_id") or "")
    msg_id = str(payload["msg_id"])
    attachment_index = int(payload["attachment_index"])
    source_key = _media_key(
        account_id, conversation_id, msg_id, attachment_index
    )
    existing = _dedupe_row(session, source_key)
    if existing is not None:
        verdict = _media_dedupe_lookup(existing, payload)
        if verdict == "conflict" or (
            verdict == "upgrade" and media_status == "failed"
        ):
            raise InboxConflict("Webhook trùng khóa nhưng payload khác")
        if verdict == "upgrade":
            # missing → captured: a late media supplement completes a slot
            # that the envelope reported as a failed download.
            asset_id = _dedupe_result_id(existing)
            asset = (
                session.get(MediaAsset, asset_id) if asset_id else None
            )
            if asset is None or asset.state != "missing":
                raise InboxConflict(
                    "Webhook trùng khóa nhưng payload khác"
                )
            path = resolve_media_object(
                _media_root(settings),
                account_id,
                str(payload["media_object_key"]),
                str(payload["mime_type"]),
                int(payload["size_bytes"]),
            )
            sent_at = _parse_timestamp(payload["sent_at"])
            source = _source_from_payload(session, payload)
            _upgrade_missing_media_asset(
                session, existing, asset, path, payload, sent_at,
                conv_source=source,
            )
            _journal(session, _capture_key(), payload, utcnow())
            session.commit()
            return session.get(MediaAsset, asset.attachment_id)
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
    sent_at = _parse_timestamp(payload["sent_at"])
    if media_status == "failed":
        error_code = str(payload["error_code"])
        if not re.fullmatch(r"[a-z0-9_]{1,64}", error_code):
            raise InboxValidationError("media error_code không hợp lệ")
        if str(payload["mime_type"]) not in SUPPORTED_MIME:
            raise InboxValidationError("Loại media không được hỗ trợ")
        _check_media_object_key(account_id, str(payload["media_object_key"]))
        asset_id = _register_missing_media_asset(session, payload, sent_at)
        att_source = _attachment_source(
            session,
            account_id,
            conversation_id,
            msg_id,
            asset_id,
            sent_at,
            image_available=False,
            conv_source=source,
        )
        _processing_status_record(
            session,
            att_source,
            _record_source_block(
                account_id=account_id,
                conversation_id=conversation_id,
                conversation_type=source.conversation_type,
                msg_id=msg_id,
                sender_id=payload.get("sender_id"),
                sent_at=sent_at,
                attachment_id=asset_id,
                attachment_index=attachment_index,
            ),
            "media_missing",
            sent_at,
            note=error_code,
        )
    else:
        path = resolve_media_object(
            _media_root(settings),
            account_id,
            str(payload["media_object_key"]),
            str(payload["mime_type"]),
            int(payload["size_bytes"]),
        )
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
        source_key,
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


# --- ops snapshot helpers (GET /connector/v1/state) ----------------------------


def listener_gaps(
    session: "Session",
    account: ConnectorAccount,
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Open/closed coverage gaps derived from ``listener_sessions``.

    A non-connected observation opens a gap; the next ``connected`` row
    closes it. ``connector_accounts.gap_started_at`` — set when the module
    detects a gap without a session row (connector process death or a
    listener restart while still receiving) — extends the open segment back
    or becomes its own interval when the log has no covering rows.
    """
    rows = (
        session.execute(
            select(ListenerSession)
            .where(
                ListenerSession.account_id == account.connector_account_id
            )
            .order_by(text("rowid"))
        )
        .scalars()
        .all()
    )
    gaps: list[dict[str, Any]] = []
    open_start: str | None = None
    last_connected_at: str | None = None
    for row in rows:
        if row.state == "connected":
            last_connected_at = row.observed_at
            if open_start is not None:
                gaps.append(
                    {
                        "started_at": open_start,
                        "ended_at": _iso(row.observed_at),
                        "ongoing": False,
                    }
                )
                open_start = None
        elif open_start is None:
            open_start = _iso(row.observed_at)
    marker = _aware(account.gap_started_at)
    if open_start is not None:
        if marker is not None and marker < (_aware(open_start) or marker):
            open_start = _iso(marker)
        gaps.append({"started_at": open_start, "ended_at": None, "ongoing": True})
    elif marker is not None:
        covered = any(
            (_aware(gap["started_at"]) or marker) <= marker
            and (
                gap["ended_at"] is None
                or marker <= (_aware(gap["ended_at"]) or marker)
            )
            for gap in gaps
        )
        if not covered:
            last_connected = _aware(last_connected_at)
            if last_connected is not None and last_connected >= marker:
                gaps.append(
                    {
                        "started_at": _iso(marker),
                        "ended_at": _iso(last_connected),
                        "ongoing": False,
                    }
                )
            elif connector_state(account, now=now) != "connected":
                gaps.append(
                    {
                        "started_at": _iso(marker),
                        "ended_at": None,
                        "ongoing": True,
                    }
                )
    return gaps


def job_queue_state(
    session: "Session", *, now: datetime | None = None
) -> dict[str, Any]:
    """Backlog metrics for the internal ``jobs`` queue (``queue`` block)."""
    created = (
        session.execute(
            select(Job.created_at).where(
                Job.state.in_(("queued", "retry_wait"))
            )
        )
        .scalars()
        .all()
    )
    current = _aware(now) or utcnow()
    oldest_age_s: int | None = None
    if created:
        oldest = min((_aware(value) or current) for value in created)
        oldest_age_s = max(0, int((current - oldest).total_seconds()))
    return {"pending_jobs": len(created), "oldest_age_s": oldest_age_s}


def media_usage_bytes(settings: "Settings") -> int:
    """Total bytes under ``runtime_root/media`` (originals + derived)."""
    root = _media_root(settings)
    if not root.is_dir():
        return 0
    total = 0
    for path in root.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
        except OSError:
            continue
    return total


def ops_warnings(
    account: ConnectorAccount,
    gaps: list[dict[str, Any]],
    media: dict[str, Any],
    *,
    now: datetime | None = None,
) -> list[dict[str, str]]:
    """Advisory warnings for the ops surface (``warnings[]``).

    Codes: ``listener_heartbeat_stale`` (heartbeat older than 45s while the
    session is marked usable — the connector is treated as disconnected),
    ``gap_open`` (an open listener gap means events may have been missed),
    ``storage_full`` / ``disk_pressure`` (media quota pressure).
    """
    warnings: list[dict[str, str]] = []
    state = connector_state(account, now=now)
    if account.session_state == "usable" and state != "connected":
        warnings.append(
            {
                "code": "listener_heartbeat_stale",
                "message": "listener heartbeat is stale (>45s) — treated as disconnected",
            }
        )
    if any(gap.get("ongoing") for gap in gaps):
        warnings.append(
            {
                "code": "gap_open",
                "message": "listener gap is open — events may have been missed",
            }
        )
    quota = media.get("quota_bytes") or 0
    usage = media.get("usage_bytes") or 0
    if media.get("storage_full"):
        warnings.append(
            {"code": "storage_full", "message": "media storage quota reached"}
        )
    elif quota and usage >= int(quota * 0.9):
        warnings.append(
            {
                "code": "disk_pressure",
                "message": "media storage usage is above 90% of quota",
            }
        )
    return warnings

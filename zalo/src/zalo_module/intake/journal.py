"""Event journal: idempotent capture of raw listener events.

MIN-93 scaffold grade. ``source_key`` hashes the *source identity* only, so
replays of the same provider message return the existing ``capture_id``
without writing anything. Real Zalo event-shape hardening is MIN-94.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from zalo_module.models import JournalEntry, Record, Source

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from zalo_module.settings import Settings

_SCHEMA_VERSION = "intake.raw-record.v1"
_PROVIDER = "zalo_personal"

# event["type"] -> sources.scope (DDL: msg|attachment|page|source_event|session)
_SCOPE_BY_EVENT_TYPE = {
    "message": "msg",
    "attachment": "attachment",
}


def _data(event: dict) -> dict:
    data = event.get("data")
    return data if isinstance(data, dict) else {}


def _event_kind(event: dict) -> str:
    etype = event.get("type")
    if etype == "message":
        return "message"
    if etype == "attachment":
        return "attachment"
    return "event"


def source_key(event: dict) -> str:
    """Canonical sha256 over the source-identity dict of *event*.

    Identity fields only (sheet section 5): account_id, conversation_id,
    provider_message_id (msgId | cliMsgId), kind; attachment events add their
    index. Non-identity fields (text, ts, ...) never change the key.
    """
    data = _data(event)
    kind = _event_kind(event)
    identity: dict[str, Any] = {
        "account_id": data.get("idTo"),
        "conversation_id": data.get("threadId"),
        "provider_message_id": data.get("msgId") or data.get("cliMsgId"),
        "kind": kind,
    }
    if kind == "attachment":
        index = data.get("attachment_index", data.get("index"))
        if index is not None:
            identity["attachment_index"] = index
    blob = json.dumps(
        identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def capture_event(event: dict, session: "Session", settings: "Settings") -> str:
    """Journal *event* idempotently and return its ``capture_id``.

    Replay path: ``source_key`` already present in ``journal_entries`` ->
    return the stored ``capture_id`` without inserting anything.

    New event: insert ``journal_entries`` row, upsert ``sources`` (scope from
    event type; existing source rows are never overwritten), then insert a
    ``records`` row - ``message_text`` when the event carries text content,
    ``processing_status`` {code: "captured"} otherwise.
    """
    skey = source_key(event)
    existing = session.execute(
        select(JournalEntry).where(JournalEntry.source_key == skey)
    ).scalar_one_or_none()
    if existing is not None:
        return existing.capture_id

    now_iso = datetime.now(timezone.utc).isoformat()
    capture_id = str(uuid.uuid4())
    session.add(
        JournalEntry(
            capture_id=capture_id,
            source_key=skey,
            event_json=json.dumps(event, ensure_ascii=False),
            captured_at=now_iso,
            recorded_at=now_iso,
        )
    )

    data = _data(event)
    source = _upsert_source(event, data, session, settings, now_iso)
    session.add(_build_record(data, source, now_iso))
    return capture_id


def _upsert_source(
    event: dict,
    data: dict,
    session: "Session",
    settings: "Settings",
    now_iso: str,
) -> Source:
    scope = _SCOPE_BY_EVENT_TYPE.get(event.get("type"), "source_event")
    account_id = settings.account_id or data.get("idTo")
    conversation_id = data.get("threadId")
    provider_message_id = data.get("msgId") or data.get("cliMsgId")
    attachment_id = data.get("attachmentId") or data.get("attachment_id")

    conditions = [
        Source.scope == scope,
        Source.account_id == account_id,
        Source.conversation_id == conversation_id,
        Source.provider_message_id == provider_message_id,
    ]
    if scope == "attachment":
        conditions.append(Source.attachment_id == attachment_id)

    existing = session.execute(
        select(Source).where(*conditions)
    ).scalar_one_or_none()
    if existing is not None:
        return existing  # never overwrite existing source fields on replay

    source = Source(
        logical_id=str(uuid.uuid4()),
        scope=scope,
        account_id=account_id,
        conversation_id=conversation_id,
        provider_message_id=provider_message_id,
        attachment_id=attachment_id if scope == "attachment" else None,
        captured_at=now_iso,
        current_revision=1,
        image_available=0,
        enabled=1,
    )
    session.add(source)
    return source


def _message_text(data: dict) -> str | None:
    content = data.get("content")
    if isinstance(content, dict):
        text = content.get("text")
        return text if isinstance(text, str) else None
    if isinstance(content, str):
        return content
    return None


def _source_sent_at(data: dict) -> str | None:
    """event data.ts (epoch ms) -> ISO 8601; omit when missing/non-numeric."""
    try:
        ms = int(data.get("ts"))
    except (TypeError, ValueError):
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _record_source(data: dict, source: Source) -> dict:
    out: dict[str, Any] = {"provider": _PROVIDER}
    if source.account_id is not None:
        out["account_id"] = source.account_id
    if source.conversation_id is not None:
        out["conversation_id"] = source.conversation_id
        out["conversation_type"] = "user"  # scaffold: zalo_personal 1:1
    if source.provider_message_id is not None:
        out["provider_message_id"] = source.provider_message_id
    client_message_id = data.get("cliMsgId")
    if client_message_id is not None:
        out["client_message_id"] = client_message_id
    sender_id = data.get("uidFrom")
    if sender_id is not None:
        out["sender_id"] = sender_id
    sent_at = _source_sent_at(data)
    if sent_at is not None:
        out["source_sent_at"] = sent_at
    if source.attachment_id is not None:
        out["attachment_id"] = source.attachment_id
    return out


def _build_record(data: dict, source: Source, now_iso: str) -> Record:
    record_id = str(uuid.uuid4())
    text = _message_text(data)
    kind = "message_text" if text is not None else "processing_status"
    payload: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "record_kind": kind,
        "record_id": record_id,
        "logical_id": source.logical_id,
        "revision": 1,
        "captured_at": now_iso,
        "recorded_at": now_iso,
        "source": _record_source(data, source),
    }
    if kind == "message_text":
        payload["message"] = {"text": text}
    else:
        payload["status"] = {"code": "captured"}
    payload_json = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return Record(
        record_id=record_id,
        logical_id=source.logical_id,
        revision=1,
        kind=kind,
        canonical_sha256=hashlib.sha256(payload_json.encode("utf-8")).hexdigest(),
        payload_json=payload_json,
        captured_at=now_iso,
        recorded_at=now_iso,
    )

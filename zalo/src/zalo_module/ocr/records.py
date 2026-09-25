"""Raw-record + source-row builders for the OCR pipeline (MIN-95).

Produces ``intake.raw-record.v1`` payloads for ``ocr_page`` and
``processing_status`` kinds and keeps the companion ``sources`` rows in
lock-step (one logical_id per attachment-page; one per attachment for
status-only outcomes).

Design notes:

- ``logical_id`` for an OCR page = Source row with ``scope="page"`` +
  ``attachment_id`` + 1-based ``page_index``; the whole-attachment status
  channel is ``scope="attachment"`` + ``page_index NULL`` (contract §5.3).
- Provenance (``source.*`` block) is recovered from the media dedupe
  journal entry — ``journal_entries.event_json`` carries
  ``{"component": {...}, "result_id": attachment_id}``.
- Records are immutable: a supplementary pass writes a new revision with
  ``supersedes`` pointing at the previous record, preserved ``captured_at``
  and ``source`` block (contract §9.5). ``sources.current_revision`` is
  bumped so the request API's ``stale_revision`` check stays honest.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select

from zalo_module.models import ConvSource, JournalEntry, Record, Source

RETENTION_HOURS = 168

SCHEMA_VERSION = "intake.raw-record.v1"
PROVIDER = "zalo_personal"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = aware(value)
        if value is None:
            return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def aware(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


def canonical_json(value: Any) -> str:
    """Stable canonical JSON for CAS compare — same convention as intake."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def image_expires_iso(captured_iso: str) -> str:
    captured = aware(captured_iso) or utcnow()
    return iso(captured + timedelta(hours=RETENTION_HOURS)) or captured_iso


# Forbidden-content guard for free-text fields (error.message / status.note):
# contract §11.3 scans record strings for data URIs, image/doc refs and
# base64 blobs — exception text can smuggle file paths or provider URLs, so
# stored messages pass through this sanitizer (drop offending tokens).
_CLEAN_DROP_TOKEN = re.compile(
    r"(?:data:|https?://|[\\/]|\.(?:jpe?g|png|webp|pdf)\b|[A-Za-z0-9+/]{48,}={0,2}$)",
    re.IGNORECASE,
)


def clean_message(text: object, fallback: str = "provider error") -> str:
    """Sanitize a free-text message for storage inside a record payload."""
    raw = str(text or "").strip() or fallback
    tokens = [t for t in raw.split() if not _CLEAN_DROP_TOKEN.search(t)]
    cleaned = " ".join(tokens).strip() or fallback
    return cleaned[:480]


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


@dataclass
class Provenance:
    """Source-context recovered from the media dedupe journal entry."""

    account_id: str | None = None
    conversation_id: str | None = None
    conversation_type: str | None = None
    provider_message_id: str | None = None
    attachment_index: int | None = None
    sender_id: str | None = None
    sent_at: str | None = None


def find_provenance(session, attachment_id: str) -> Provenance | None:
    """Resolve attachment_id → journal component → conversation context.

    The media dedupe row carries the digest ``component`` (account/
    conversation/msg/attachment_index/sent_at) plus ``result_id`` =
    attachment_id. ``conversation_type`` comes from ``conv_sources``;
    ``sender_id`` is best-effort (component may lack it — then the
    message_text record on the msg-scope source is consulted).
    """
    rows = (
        session.execute(
            select(JournalEntry).where(
                JournalEntry.event_json.like(f'%"{attachment_id}"%')
            )
        )
        .scalars()
        .all()
    )
    component: dict | None = None
    for row in rows:
        try:
            event = json.loads(row.event_json)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("result_id") == attachment_id and isinstance(
            event.get("component"), dict
        ):
            component = event["component"]
            break
        # Fallback: a message journal row embedding the attachment descriptor.
        for attachment in event.get("attachments") or []:
            if (
                isinstance(attachment, dict)
                and attachment.get("attachment_id") == attachment_id
            ):
                comp = event.get("component")
                if isinstance(comp, dict):
                    component = dict(comp)
                    component.setdefault(
                        "attachment_index", attachment.get("attachment_index")
                    )
                    break
        if component is not None:
            break
    if component is None:
        return None

    account_id = component.get("connector_account_id") or component.get(
        "account_id"
    )
    conversation_id = component.get("conversation_id")
    msg_id = component.get("msg_id")
    prov = Provenance(
        account_id=str(account_id) if account_id else None,
        conversation_id=str(conversation_id) if conversation_id else None,
        provider_message_id=str(msg_id) if msg_id else None,
        attachment_index=component.get("attachment_index"),
        sender_id=component.get("sender_id"),
        sent_at=component.get("sent_at"),
    )
    if account_id and conversation_id:
        conv = session.execute(
            select(ConvSource).where(
                ConvSource.connector_account_id == str(account_id),
                ConvSource.conversation_id == str(conversation_id),
            )
        ).scalar_one_or_none()
        if conv is not None:
            prov.conversation_type = conv.conversation_type
    if prov.sender_id is None and account_id and conversation_id and msg_id:
        # Best-effort: pull sender_id from the message_text record source.
        msg_source = session.execute(
            select(Source).where(
                Source.scope == "msg",
                Source.account_id == str(account_id),
                Source.conversation_id == str(conversation_id),
                Source.provider_message_id == str(msg_id),
            )
        ).scalar_one_or_none()
        if msg_source is not None:
            rec = session.execute(
                select(Record)
                .where(Record.logical_id == msg_source.logical_id)
                .order_by(Record.revision)
                .limit(1)
            ).scalar_one_or_none()
            if rec is not None:
                try:
                    sender = json.loads(rec.payload_json)["source"].get(
                        "sender_id"
                    )
                    if isinstance(sender, str) and sender:
                        prov.sender_id = sender
                except (ValueError, KeyError, AttributeError):
                    pass
    return prov


def source_block(
    prov: Provenance | None,
    attachment_id: str | None,
    page_index: int | None,
) -> dict:
    """The contract ``source`` object for an OCR/status record."""
    prov = prov or Provenance()
    block: dict[str, Any] = {"provider": PROVIDER}
    if prov.account_id:
        block["account_id"] = prov.account_id
    if prov.conversation_id:
        block["conversation_id"] = prov.conversation_id
    if prov.conversation_type:
        block["conversation_type"] = prov.conversation_type
    if prov.provider_message_id:
        block["provider_message_id"] = prov.provider_message_id
    if prov.sender_id:
        block["sender_id"] = prov.sender_id
    if prov.sent_at:
        sent = iso(prov.sent_at)
        if sent:
            block["source_sent_at"] = sent
    if attachment_id:
        block["attachment_id"] = attachment_id
    if prov.attachment_index is not None:
        block["attachment_index"] = int(prov.attachment_index)
    if page_index is not None:
        block["page_index"] = int(page_index)
    return block


# ---------------------------------------------------------------------------
# Source rows
# ---------------------------------------------------------------------------


def ensure_page_source(session, asset, prov: Provenance | None, page_index: int) -> Source:
    """Find-or-create the page-scope provenance row (contract §5.3)."""
    source = session.execute(
        select(Source).where(
            Source.scope == "page",
            Source.attachment_id == asset.attachment_id,
            Source.page_index == int(page_index),
        )
    ).scalar_one_or_none()
    if source is not None:
        return source
    prov = prov or Provenance()
    source = Source(
        logical_id=new_id(),
        scope="page",
        account_id=prov.account_id,
        conversation_id=prov.conversation_id,
        provider_message_id=prov.provider_message_id,
        attachment_id=asset.attachment_id,
        page_index=int(page_index),
        captured_at=iso(asset.captured_at),
        current_revision=1,
        image_available=1,
        enabled=1,
        image_expires_at=iso(asset.expires_at),
    )
    session.add(source)
    session.flush()
    return source


def ensure_attachment_source(session, asset, prov: Provenance | None) -> Source:
    """Find-or-create the attachment-scope status channel row."""
    source = session.execute(
        select(Source).where(
            Source.scope == "attachment",
            Source.attachment_id == asset.attachment_id,
            Source.page_index.is_(None),
        )
    ).scalar_one_or_none()
    if source is not None:
        return source
    prov = prov or Provenance()
    source = Source(
        logical_id=new_id(),
        scope="attachment",
        account_id=prov.account_id,
        conversation_id=prov.conversation_id,
        provider_message_id=prov.provider_message_id,
        attachment_id=asset.attachment_id,
        page_index=None,
        captured_at=iso(asset.captured_at),
        current_revision=1,
        image_available=1,
        enabled=1,
        image_expires_at=iso(asset.expires_at),
    )
    session.add(source)
    session.flush()
    return source


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


def insert_record(session, payload: dict) -> Record:
    """Insert a ``records`` row from a contract payload; bumps
    ``sources.current_revision`` when a matching source row exists."""
    record = Record(
        record_id=payload["record_id"],
        logical_id=payload["logical_id"],
        revision=payload["revision"],
        kind=payload["record_kind"],
        canonical_sha256=canonical_sha256(payload),
        payload_json=canonical_json(payload),
        captured_at=payload["captured_at"],
        recorded_at=payload["recorded_at"],
    )
    session.add(record)
    source = session.get(Source, payload["logical_id"])
    if source is not None and (source.current_revision or 0) < payload["revision"]:
        source.current_revision = payload["revision"]
    session.flush()
    return record


def has_record(session, logical_id: str) -> bool:
    return (
        session.execute(
            select(func.count(Record.record_id)).where(
                Record.logical_id == logical_id
            )
        ).scalar()
        or 0
    ) > 0


def records_for(session, logical_id: str) -> list[Record]:
    return (
        session.execute(
            select(Record)
            .where(Record.logical_id == logical_id)
            .order_by(Record.revision)
        )
        .scalars()
        .all()
    )


def latest_record(session, logical_id: str) -> Record | None:
    return session.execute(
        select(Record)
        .where(Record.logical_id == logical_id)
        .order_by(Record.revision.desc())
        .limit(1)
    ).scalar_one_or_none()


def latest_attachment_status(session, logical_id: str) -> dict | None:
    """Latest processing_status payload for an attachment-scope logical."""
    rec = session.execute(
        select(Record)
        .where(
            Record.logical_id == logical_id,
            Record.kind == "processing_status",
        )
        .order_by(Record.revision.desc())
        .limit(1)
    ).scalar_one_or_none()
    if rec is None:
        return None
    try:
        return json.loads(rec.payload_json)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------


def attempt_dict(
    *,
    ocr_pass_id: str,
    model: str,
    task: str,
    image_operation: str,
    region: dict,
    transform_chain: list[dict],
    geometry_status: str,
    status: str,
    config_version: str,
    submitted_frame: dict | None = None,
    provider_lines: list[dict] | None = None,
    error: dict | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
    request_id: str | None = None,
) -> dict:
    """One ``ocr.attempts[]`` element (schema-conformant keys only)."""
    attempt: dict[str, Any] = {
        "ocr_pass_id": ocr_pass_id,
        "provider": "qwen",
        "model": model,
        "task": task,
        "image_operation": image_operation,
        "region": region,
        "transform_chain": transform_chain,
        "geometry_status": geometry_status,
        "status": status,
        "config_version": config_version,
    }
    if submitted_frame is not None:
        attempt["submitted_frame"] = submitted_frame
    if provider_lines:
        attempt["provider_lines"] = provider_lines
    if error is not None:
        attempt["error"] = error
        if error.get("retryable") is None:
            error.pop("retryable", None)
    if started_at:
        attempt["started_at"] = started_at
    if completed_at:
        attempt["completed_at"] = completed_at
    if request_id:
        attempt["request_id"] = request_id
    return attempt


def text_line_dicts(
    lines: list[str],
    *,
    captured_at: str,
    page_index: int,
    ocr_pass_id: str,
) -> list[dict]:
    return [
        {
            "line_id": new_id(),
            "text": line[:4096],
            "captured_at": captured_at,
            "page_index": int(page_index),
            "ocr_pass_id": ocr_pass_id,
        }
        for line in lines
    ]


def ocr_status(attempts: list[dict], text_lines: list[dict]) -> str:
    """Aggregate record-level ``ocr.status`` honoring consistency rules."""
    if text_lines:
        return "succeeded"
    if any(a.get("status") == "source_image_expired" for a in attempts):
        return "source_image_expired"
    return "failed"


def build_ocr_page_payload(
    *,
    logical_id: str,
    revision: int,
    supersedes: dict | None,
    captured_at: str,
    recorded_at: str,
    source: dict,
    image_sha256: str,
    image_expires_at: str,
    image_state: str,
    attempts: list[dict],
    text_lines: list[dict],
    selected_pass_ids: list[str],
    status: str | None = None,
) -> dict:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_kind": "ocr_page",
        "record_id": new_id(),
        "logical_id": logical_id,
        "revision": revision,
        "captured_at": captured_at,
        "recorded_at": recorded_at,
        "source": source,
        "image_sha256": image_sha256,
        "image_expires_at": image_expires_at,
        "image_state": image_state,
        "ocr": {
            "status": status or ocr_status(attempts, text_lines),
            "attempts": attempts,
            "text_lines": text_lines,
            "selected_pass_ids": selected_pass_ids,
        },
    }
    if supersedes is not None:
        payload["supersedes"] = supersedes
    return payload


def build_processing_status_payload(
    *,
    logical_id: str,
    revision: int,
    supersedes: dict | None,
    captured_at: str,
    recorded_at: str,
    source: dict,
    code: str,
    note: str | None = None,
) -> dict:
    status: dict[str, Any] = {"code": code}
    if note:
        status["note"] = note[:500]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_kind": "processing_status",
        "record_id": new_id(),
        "logical_id": logical_id,
        "revision": revision,
        "captured_at": captured_at,
        "recorded_at": recorded_at,
        "source": source,
        "status": status,
    }
    if supersedes is not None:
        payload["supersedes"] = supersedes
    return payload

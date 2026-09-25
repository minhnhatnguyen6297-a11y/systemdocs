"""Declarative models — column-for-column match with decision-sheet §4 DDL.

All timestamps are stored as TEXT ISO-8601 (per DDL). The authoritative
schema is created by ``zalo_module.migrations.m0001_initial``; these models
exist for ORM access and must stay in lock-step with that DDL.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Index, Integer, Text, UniqueConstraint
from sqlalchemy import text as sa_text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class Base(DeclarativeBase):
    """Shared declarative base — imported by other slices as ``Base``."""


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"

    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    applied_at: Mapped[str] = mapped_column(Text, nullable=False)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    capture_id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    event_json: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[str] = mapped_column(Text, nullable=False)


class Source(Base):
    __tablename__ = "sources"

    logical_id: Mapped[str] = mapped_column(Text, primary_key=True)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    account_id: Mapped[str | None] = mapped_column(Text)
    conversation_id: Mapped[str | None] = mapped_column(Text)
    provider_message_id: Mapped[str | None] = mapped_column(Text)
    attachment_id: Mapped[str | None] = mapped_column(Text)
    page_index: Mapped[int | None] = mapped_column(Integer)
    captured_at: Mapped[str] = mapped_column(Text, nullable=False)
    current_revision: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    image_available: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    enabled: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    image_expires_at: Mapped[str | None] = mapped_column(Text)


class Record(Base):
    __tablename__ = "records"
    __table_args__ = (
        UniqueConstraint("logical_id", "revision", name="uq_records_logical_rev"),
    )

    record_id: Mapped[str] = mapped_column(Text, primary_key=True)
    logical_id: Mapped[str] = mapped_column(Text, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[str] = mapped_column(Text, nullable=False)
    packaged_in: Mapped[str | None] = mapped_column(Text)


class MediaAsset(Base):
    __tablename__ = "media_assets"

    attachment_id: Mapped[str] = mapped_column(Text, primary_key=True)
    sha256: Mapped[str] = mapped_column(Text, nullable=False)
    rel_path: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[str] = mapped_column(Text, nullable=False)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("idx_jobs_claim", "state", "run_after"),)

    job_id: Mapped[str] = mapped_column(Text, primary_key=True)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    logical_id: Mapped[str | None] = mapped_column(Text)
    request_id: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, server_default="3"
    )
    lease_owner: Mapped[str | None] = mapped_column(Text)
    lease_expires_at: Mapped[str | None] = mapped_column(Text)
    run_after: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    result_json: Mapped[str | None] = mapped_column(Text)


class OcrRequest(Base):
    __tablename__ = "ocr_requests"

    request_id: Mapped[str] = mapped_column(Text, primary_key=True)
    consumer_id: Mapped[str] = mapped_column(Text, nullable=False)
    logical_id: Mapped[str] = mapped_column(Text, nullable=False)
    variant: Mapped[str] = mapped_column(Text, nullable=False)
    preset: Mapped[str | None] = mapped_column(Text)
    reason_code: Mapped[str] = mapped_column(Text, nullable=False)
    observed_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[str] = mapped_column(Text, nullable=False)
    body_canonical_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    job_id: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    deduped_from: Mapped[str | None] = mapped_column(Text)


class Package(Base):
    __tablename__ = "packages"
    __table_args__ = (
        UniqueConstraint(
            "consumer_id", "sequence", name="uq_packages_consumer_seq"
        ),
    )

    package_id: Mapped[str] = mapped_column(Text, primary_key=True)
    consumer_id: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    manifest_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    dir_rel_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    sealed_at: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="pending", server_default="'pending'"
    )
    receipt_json: Mapped[str | None] = mapped_column(Text)


class ListenerSession(Base):
    __tablename__ = "listener_sessions"

    session_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    observed_at: Mapped[str] = mapped_column(Text, nullable=False)
    last_heartbeat_at: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)


# --- m0002 engine tables (MIN-103 slice B, decision sheet §3) ---------------
# Mirror the legacy zalo_* tables column-for-column (renamed tables, same
# column names). All timestamps are TEXT ISO-8601; booleans are INTEGER 0/1
# (nullable where the legacy column was nullable).


class ConnectorAccount(Base):
    __tablename__ = "connector_accounts"

    connector_account_id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    bound_zalo_id: Mapped[str | None] = mapped_column(Text)
    session_state: Mapped[str] = mapped_column(
        Text, nullable=False, default="login_required",
        server_default="'login_required'",
    )
    listener_generation: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    last_seen_at: Mapped[str | None] = mapped_column(Text)
    qr_image: Mapped[str | None] = mapped_column(Text)
    qr_expires_at: Mapped[str | None] = mapped_column(Text)
    storage_full: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    intake_consented_at: Mapped[str | None] = mapped_column(Text)
    policy_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    policy_acked_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    source_sync_request_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    source_sync_acked_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    gap_started_at: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(
        Text, nullable=False, default=_now_iso
    )
    updated_at: Mapped[str] = mapped_column(
        Text, nullable=False, default=_now_iso
    )


class ConvSource(Base):
    __tablename__ = "conv_sources"
    __table_args__ = (
        UniqueConstraint(
            "connector_account_id",
            "conversation_id",
            name="uq_conv_sources_conversation",
        ),
    )

    conv_source_id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    connector_account_id: Mapped[str] = mapped_column(Text, nullable=False)
    conversation_id: Mapped[str] = mapped_column(Text, nullable=False)
    conversation_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str | None] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    enabled_explicit: Mapped[int | None] = mapped_column(Integer)
    acked_enabled: Mapped[int | None] = mapped_column(Integer)
    policy_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    policy_acked_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    last_activity_at: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(
        Text, nullable=False, default=_now_iso
    )
    updated_at: Mapped[str] = mapped_column(
        Text, nullable=False, default=_now_iso
    )


class DataSyncRun(Base):
    __tablename__ = "data_sync_runs"
    __table_args__ = (
        Index(
            "uq_data_sync_runs_running_account",
            "connector_account_id",
            unique=True,
            sqlite_where=sa_text("status = 'running'"),
        ),
    )

    run_id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    connector_account_id: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    cutoff_at: Mapped[str] = mapped_column(Text, nullable=False)
    deadline_at: Mapped[str] = mapped_column(Text, nullable=False)
    source_ids_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]", server_default="'[]'"
    )
    counters_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}", server_default="'{}'"
    )
    error_code: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[str] = mapped_column(Text, nullable=False)
    completed_at: Mapped[str | None] = mapped_column(Text)

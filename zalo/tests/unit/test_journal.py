"""Slice C - journal capture tests (MIN-93 decision sheet section 8).

Production code imports ``zalo_module.{settings,models,database,audit}`` which
are owned by slices A/B. While those slices are in flight this file installs
minimal stand-ins into ``sys.modules`` *before* importing slice-C modules, so
the logic is still exercised against the pinned section-4 DDL shape. When the
real modules exist they are imported instead and every shim is skipped.
"""
from __future__ import annotations

import json
import os
import sys
import types
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session


def _install_slice_ab_shims() -> None:
    """Register minimal slice A/B module stand-ins in sys.modules."""
    from sqlalchemy import Column, Integer, Text
    from sqlalchemy.orm import DeclarativeBase

    try:
        import zalo_module.settings  # noqa: F401
    except ImportError:
        mod = types.ModuleType("zalo_module.settings")

        @dataclass(frozen=True)
        class Settings:  # fields per sheet section 2
            runtime_root: Path
            db_url: str
            consumer_id: str | None = None
            bind: str = "127.0.0.1"
            port: int = 8790
            qwen_api_base: str = "https://dashscope-intl.aliyuncs.com"
            qwen_model: str = "qwen-vl-ocr-2025-11-20"
            qwen_api_key: str | None = None
            account_id: str | None = None
            ocr_config_version: str = "ocr-config-v1"
            access_log_path: Path | None = None

        def get_settings(env: dict[str, str] | None = None) -> Settings:
            env = os.environ if env is None else env
            root = Path(env.get("ZALO_INTAKE_RUNTIME_DIR", "./runtime"))
            db_url = env.get(
                "ZALO_INTAKE_DB_URL",
                f"sqlite:///{(root / 'zalo_intake.db').as_posix()}",
            )
            return Settings(
                runtime_root=root,
                db_url=db_url,
                consumer_id=env.get("ZALO_INTAKE_CONSUMER_ID") or None,
                account_id=env.get("ZALO_ACCOUNT_ID") or None,
                access_log_path=root / "access.jsonl",
            )

        mod.Settings = Settings
        mod.get_settings = get_settings
        sys.modules["zalo_module.settings"] = mod

    try:
        import zalo_module.models  # noqa: F401
    except ImportError:
        mod = types.ModuleType("zalo_module.models")

        class Base(DeclarativeBase):
            pass

        class JournalEntry(Base):
            __tablename__ = "journal_entries"
            capture_id = Column(Text, primary_key=True)
            source_key = Column(Text, nullable=False, unique=True)
            event_json = Column(Text, nullable=False)
            captured_at = Column(Text, nullable=False)
            recorded_at = Column(Text, nullable=False)

        class Source(Base):
            __tablename__ = "sources"
            logical_id = Column(Text, primary_key=True)
            scope = Column(Text, nullable=False)
            account_id = Column(Text)
            conversation_id = Column(Text)
            provider_message_id = Column(Text)
            attachment_id = Column(Text)
            page_index = Column(Integer)
            captured_at = Column(Text, nullable=False)
            current_revision = Column(Integer, nullable=False, default=1)
            image_available = Column(Integer, nullable=False, default=0)
            enabled = Column(Integer, nullable=False, default=1)
            image_expires_at = Column(Text)

        class Record(Base):
            __tablename__ = "records"
            record_id = Column(Text, primary_key=True)
            logical_id = Column(Text, nullable=False)
            revision = Column(Integer, nullable=False)
            kind = Column(Text, nullable=False)
            canonical_sha256 = Column(Text, nullable=False)
            payload_json = Column(Text, nullable=False)
            captured_at = Column(Text, nullable=False)
            recorded_at = Column(Text, nullable=False)

        class MediaAsset(Base):
            __tablename__ = "media_assets"
            attachment_id = Column(Text, primary_key=True)
            sha256 = Column(Text, nullable=False)
            rel_path = Column(Text, nullable=False)
            state = Column(Text, nullable=False)
            captured_at = Column(Text, nullable=False)
            expires_at = Column(Text, nullable=False)

        class Job(Base):
            __tablename__ = "jobs"
            job_id = Column(Text, primary_key=True)
            kind = Column(Text, nullable=False)
            state = Column(Text, nullable=False)
            logical_id = Column(Text)
            request_id = Column(Text)
            payload_json = Column(Text, nullable=False)
            attempts = Column(Integer, nullable=False, default=0)
            max_attempts = Column(Integer, nullable=False, default=3)
            lease_owner = Column(Text)
            lease_expires_at = Column(Text)
            run_after = Column(Text)
            created_at = Column(Text, nullable=False)
            updated_at = Column(Text, nullable=False)
            result_json = Column(Text)

        mod.Base = Base
        for cls in (JournalEntry, Source, Record, MediaAsset, Job):
            setattr(mod, cls.__name__, cls)
        sys.modules["zalo_module.models"] = mod

    try:
        import zalo_module.audit  # noqa: F401
    except ImportError:
        mod = types.ModuleType("zalo_module.audit")
        mod.configure = lambda path: None
        mod.record_access = lambda path, kind: None
        sys.modules["zalo_module.audit"] = mod

    try:
        import zalo_module.database  # noqa: F401
    except ImportError:
        mod = types.ModuleType("zalo_module.database")
        from zalo_module.models import Base  # shim or real, whichever is live

        mod.SCHEMA_VERSION = 1
        mod.get_engine = lambda settings: create_engine(settings.db_url)
        mod.init_db = lambda engine: Base.metadata.create_all(engine)
        mod.run_migrations = lambda engine: 0

        @contextmanager
        def session_scope(engine):
            session = Session(engine)
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

        mod.session_scope = session_scope
        sys.modules["zalo_module.database"] = mod


_install_slice_ab_shims()

from zalo_module.database import get_engine, init_db, session_scope  # noqa: E402
from zalo_module.intake.journal import capture_event, source_key  # noqa: E402
from zalo_module.models import JournalEntry, Record, Source  # noqa: E402
from zalo_module.settings import Settings  # noqa: E402

EVENT = {
    "type": "message",
    "data": {
        "msgId": "t-msg-1",
        "cliMsgId": "t-cli-1",
        "uidFrom": "u1",
        "idTo": "acc1",
        "threadId": "th1",
        "msgType": "text",
        "ts": 1774425600000,
        "content": {"text": "hello"},
    },
}


def _settings(runtime: Path, **overrides) -> Settings:
    kwargs = dict(
        runtime_root=runtime,
        db_url=f"sqlite:///{(runtime / 'zalo_intake.db').as_posix()}",
        consumer_id=None,
        bind="127.0.0.1",
        port=8790,
        qwen_api_base="https://dashscope-intl.aliyuncs.com",
        qwen_model="qwen-vl-ocr-2025-11-20",
        qwen_api_key=None,
        account_id=None,
        ocr_config_version="ocr-config-v1",
        access_log_path=runtime / "access.jsonl",
    )
    kwargs.update(overrides)
    return Settings(**kwargs)


@pytest.fixture()
def env(tmp_path):
    runtime = tmp_path / "runtime"
    (runtime / "media").mkdir(parents=True)
    settings = _settings(runtime)
    engine = get_engine(settings)
    init_db(engine)
    yield settings, engine
    engine.dispose()


def _event(**data_overrides) -> dict:
    ev = json.loads(json.dumps(EVENT))  # deep copy
    ev["data"].update(data_overrides)
    return ev


def _count(session, model) -> int:
    return session.execute(select(func.count()).select_from(model)).scalar_one()


def test_replay_same_event_is_idempotent(env):
    settings, engine = env
    with session_scope(engine) as s:
        cid1 = capture_event(EVENT, s, settings)
    with session_scope(engine) as s:
        cid2 = capture_event(EVENT, s, settings)
        assert cid1 == cid2
        uuid.UUID(cid1)  # capture_id is a uuid4 str
        assert _count(s, JournalEntry) == 1
        assert _count(s, Source) == 1


def test_different_msgid_yields_different_capture_id(env):
    settings, engine = env
    other = _event(msgId="t-msg-2")
    assert source_key(other) != source_key(EVENT)
    with session_scope(engine) as s:
        cid1 = capture_event(EVENT, s, settings)
        cid2 = capture_event(other, s, settings)
        assert cid1 != cid2
        assert _count(s, JournalEntry) == 2
        assert _count(s, Source) == 2


def test_same_identity_different_text_keeps_first_event(env):
    """source_key covers identity only: same msgId/thread/account + different
    text must replay to the existing capture_id and keep the first payload."""
    settings, engine = env
    changed = _event(content={"text": "world - changed"})
    assert source_key(changed) == source_key(EVENT)
    with session_scope(engine) as s:
        cid1 = capture_event(EVENT, s, settings)
        cid2 = capture_event(changed, s, settings)
        assert cid1 == cid2
        assert _count(s, JournalEntry) == 1
        assert _count(s, Record) == 1
        rec = s.execute(select(Record)).scalar_one()
        assert json.loads(rec.payload_json)["message"]["text"] == "hello"


def test_changed_ts_does_not_change_source_key(env):
    settings, engine = env
    later = _event(ts=1774425600000 + 60_000)
    assert source_key(later) == source_key(EVENT)
    with session_scope(engine) as s:
        cid1 = capture_event(EVENT, s, settings)
        cid2 = capture_event(later, s, settings)
        assert cid1 == cid2
        assert _count(s, JournalEntry) == 1


def test_message_text_record_created_with_linkage(env):
    settings, engine = env
    with session_scope(engine) as s:
        capture_event(EVENT, s, settings)
        src = s.execute(select(Source)).scalar_one()
        assert src.scope == "msg"
        assert src.account_id == "acc1"  # settings.account_id None -> data.idTo
        assert src.conversation_id == "th1"
        assert src.provider_message_id == "t-msg-1"

        rec = s.execute(select(Record)).scalar_one()
        assert rec.kind == "message_text"
        assert rec.revision == 1
        assert rec.logical_id == src.logical_id
        payload = json.loads(rec.payload_json)
        assert payload["schema_version"] == "intake.raw-record.v1"
        assert payload["record_kind"] == "message_text"
        assert payload["record_id"] == rec.record_id
        assert payload["logical_id"] == src.logical_id
        assert payload["revision"] == 1
        assert payload["source"]["provider"] == "zalo_personal"
        assert payload["source"]["account_id"] == "acc1"
        assert payload["source"]["conversation_id"] == "th1"
        assert payload["source"]["conversation_type"] == "user"
        assert payload["source"]["provider_message_id"] == "t-msg-1"
        assert payload["source"]["client_message_id"] == "t-cli-1"
        assert payload["source"]["sender_id"] == "u1"
        assert payload["source"]["source_sent_at"] == datetime.fromtimestamp(
            1774425600000 / 1000, tz=timezone.utc
        ).isoformat()
        assert payload["message"] == {"text": "hello"}
        # canonical_sha256 matches the canonical serialization actually stored
        import hashlib

        assert rec.canonical_sha256 == hashlib.sha256(
            rec.payload_json.encode("utf-8")
        ).hexdigest()


def test_event_without_text_creates_processing_status(env):
    settings, engine = env
    ev = _event(content={"href": "https://example.invalid/x"})
    with session_scope(engine) as s:
        capture_event(ev, s, settings)
        rec = s.execute(select(Record)).scalar_one()
        assert rec.kind == "processing_status"
        payload = json.loads(rec.payload_json)
        assert payload["status"] == {"code": "captured"}
        assert "message" not in payload

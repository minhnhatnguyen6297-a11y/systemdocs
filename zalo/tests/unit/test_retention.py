"""Slice C - media path/register/retention tests (MIN-93 decision sheet 8).

Same slice A/B stand-in strategy as test_journal.py: real zalo_module modules
are used when present, otherwise minimal shims matching sheet sections 2/4.
"""
from __future__ import annotations

import os
import sys
import types
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
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
from zalo_module.models import MediaAsset  # noqa: E402
from zalo_module.settings import Settings  # noqa: E402
from zalo_module.storage.media import media_path, register_media  # noqa: E402
from zalo_module.storage.retention import (  # noqa: E402
    IMAGE_TTL_HOURS,
    expire_media,
    image_expires_at,
)


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


def test_image_expires_at_is_exactly_168h():
    captured = datetime(2026, 9, 25, 1, 2, 3, tzinfo=timezone.utc)
    expires = image_expires_at(captured)
    assert IMAGE_TTL_HOURS == 168
    assert expires == captured + timedelta(hours=168)
    assert (expires - captured).total_seconds() == 168 * 3600


def test_image_expires_at_honors_configured_hours():
    """M4: retention hours are a parameter — never hardcoded 168."""
    captured = datetime(2026, 9, 25, 1, 2, 3, tzinfo=timezone.utc)
    assert image_expires_at(captured, 48) == captured + timedelta(hours=48)
    assert image_expires_at(captured, 0.5) == captured + timedelta(minutes=30)


def test_image_expires_at_falls_back_on_invalid_hours():
    captured = datetime(2026, 9, 25, 1, 2, 3, tzinfo=timezone.utc)
    for bad in (None, 0, -12, "abc"):
        assert image_expires_at(captured, bad) == captured + timedelta(
            hours=IMAGE_TTL_HOURS
        )


def test_media_path_under_runtime_media(env):
    settings, _engine = env
    p = media_path("att-1", "jpg", settings)
    assert p == settings.runtime_root / "media" / "att-1.jpg"


def test_register_media_sets_expires_168h(env):
    settings, engine = env
    captured = datetime(2026, 9, 25, 0, 0, 0, tzinfo=timezone.utc)
    with session_scope(engine) as s:
        register_media("att-1", "ab" * 32, "media/att-1.jpg", captured, s)
        row = s.execute(select(MediaAsset)).scalar_one()
        assert row.attachment_id == "att-1"
        assert row.rel_path == "media/att-1.jpg"
        assert row.state == "captured"
        assert row.captured_at == captured.isoformat()
        assert row.expires_at == image_expires_at(captured).isoformat()


def test_register_media_uses_settings_retention_hours(env, tmp_path):
    """M4: ``expires_at`` comes from ``settings.connector_retention_hours``
    — the same window ``expire_media`` enforces — not a hardcoded 168."""
    _s, engine = env
    settings = _settings(tmp_path / "rt48", connector_retention_hours=48)
    captured = datetime(2026, 9, 25, 0, 0, 0, tzinfo=timezone.utc)
    with session_scope(engine) as s:
        register_media(
            "att-48", "ab" * 32, "media/att-48.jpg", captured, s,
            settings=settings,
        )
        row = s.execute(select(MediaAsset)).scalar_one()
        assert row.expires_at == (captured + timedelta(hours=48)).isoformat()


def test_register_media_env_fallback_when_no_settings(env, monkeypatch):
    """M4: callers that cannot pass a Settings still honor the env var —
    the same source ``settings.connector_retention_hours`` reads."""
    _s, engine = env
    monkeypatch.setenv("ZALO_CONNECTOR_RETENTION_HOURS", "24")
    captured = datetime(2026, 9, 25, 0, 0, 0, tzinfo=timezone.utc)
    with session_scope(engine) as s:
        register_media("att-e1", "ab" * 32, "media/e1.jpg", captured, s)
        row = s.execute(select(MediaAsset)).scalar_one()
        assert row.expires_at == (captured + timedelta(hours=24)).isoformat()


def test_register_media_invalid_env_falls_back_168(env, monkeypatch):
    _s, engine = env
    monkeypatch.setenv("ZALO_CONNECTOR_RETENTION_HOURS", "bogus")
    captured = datetime(2026, 9, 25, 0, 0, 0, tzinfo=timezone.utc)
    with session_scope(engine) as s:
        register_media("att-e2", "ab" * 32, "media/e2.jpg", captured, s)
        row = s.execute(select(MediaAsset)).scalar_one()
        assert row.expires_at == (captured + timedelta(hours=168)).isoformat()


def test_expire_media_flips_state_and_deletes_file(env):
    settings, engine = env
    old_capture = datetime.now(timezone.utc) - timedelta(hours=200)
    media_file = settings.runtime_root / "media" / "old.png"
    media_file.write_bytes(b"fake-image")
    assert media_file.exists()

    with session_scope(engine) as s:
        register_media("att-old", "cd" * 32, "media/old.png", old_capture, s)

    with session_scope(engine) as s:
        n = expire_media(datetime.now(timezone.utc), s, settings)
        assert n == 1
        row = s.execute(select(MediaAsset)).scalar_one()
        assert row.state == "expired"
    assert not media_file.exists()

    # second run must not recount already-expired rows
    with session_scope(engine) as s:
        assert expire_media(datetime.now(timezone.utc), s, settings) == 0


def test_expire_media_leaves_unexpired_file_alone(env):
    settings, engine = env
    fresh_capture = datetime.now(timezone.utc)
    media_file = settings.runtime_root / "media" / "fresh.png"
    media_file.write_bytes(b"fresh-image")

    with session_scope(engine) as s:
        register_media("att-fresh", "ef" * 32, "media/fresh.png", fresh_capture, s)

    with session_scope(engine) as s:
        n = expire_media(datetime.now(timezone.utc), s, settings)
        assert n == 0
        row = s.execute(select(MediaAsset)).scalar_one()
        assert row.state == "captured"
    assert media_file.exists()


def test_expire_media_ignores_missing_file(env):
    settings, engine = env
    old_capture = datetime.now(timezone.utc) - timedelta(hours=200)
    with session_scope(engine) as s:
        register_media("att-gone", "01" * 32, "media/gone.png", old_capture, s)
    # file was never created on disk - expire must still flip state, not crash
    with session_scope(engine) as s:
        n = expire_media(datetime.now(timezone.utc), s, settings)
        assert n == 1
        assert s.execute(select(MediaAsset)).scalar_one().state == "expired"

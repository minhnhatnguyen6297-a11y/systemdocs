"""Slice C - job queue / lease primitive tests (MIN-93 decision sheet 8).

Same slice A/B stand-in strategy as test_journal.py: real zalo_module modules
are used when present, otherwise minimal shims matching sheet sections 2/4.
"""
from __future__ import annotations

import os
import sys
import types
import uuid
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
from zalo_module.jobs.worker import (  # noqa: E402
    JOB_STATES,
    claim_jobs,
    enqueue_job,
    reclaim_expired_leases,
)
from zalo_module.models import Job  # noqa: E402
from zalo_module.settings import Settings  # noqa: E402

NOW = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)


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
    runtime.mkdir(parents=True)
    settings = _settings(runtime)
    engine = get_engine(settings)
    init_db(engine)
    yield settings, engine
    engine.dispose()


def _get(engine, job_id) -> Job:
    with session_scope(engine) as s:
        return s.execute(
            select(Job).where(Job.job_id == job_id)
        ).scalar_one()


def test_job_states_literal():
    assert JOB_STATES == {
        "queued",
        "running",
        "retry_wait",
        "succeeded",
        "failed",
        "expired",
    }


def test_enqueue_creates_queued_job(env):
    _settings_obj, engine = env
    with session_scope(engine) as s:
        job_id = enqueue_job("ocr", {"logical_id": "L1"}, s)
        uuid.UUID(job_id)
        job = s.execute(select(Job).where(Job.job_id == job_id)).scalar_one()
        assert job.state == "queued"
        assert job.attempts == 0
        assert job.max_attempts == 3
        assert job.lease_owner is None
        assert job.payload_json


def test_claim_moves_to_running_with_lease(env):
    _s, engine = env
    with session_scope(engine) as s:
        job_id = enqueue_job("ocr", {}, s)
        claimed = claim_jobs(NOW, "worker-1", s)
        assert [j.job_id for j in claimed] == [job_id]
        job = s.execute(select(Job).where(Job.job_id == job_id)).scalar_one()
        assert job.state == "running"
        assert job.lease_owner == "worker-1"
        assert job.attempts == 1
        assert job.lease_expires_at == (NOW + timedelta(seconds=300)).isoformat()


def test_reclaim_expired_lease_goes_to_retry_wait(env):
    _s, engine = env
    with session_scope(engine) as s:
        job_id = enqueue_job("ocr", {}, s)
        claim_jobs(NOW, "worker-1", s)
        after_lease = NOW + timedelta(seconds=301)
        n = reclaim_expired_leases(after_lease, s)
        assert n == 1
        job = s.execute(select(Job).where(Job.job_id == job_id)).scalar_one()
        assert job.state == "retry_wait"
        assert job.lease_owner is None
        assert job.attempts == 1  # attempts preserved

        # reclaimed job is claimable again
        claimed = claim_jobs(after_lease, "worker-2", s)
        assert [j.job_id for j in claimed] == [job_id]
        job = s.execute(select(Job).where(Job.job_id == job_id)).scalar_one()
        assert job.state == "running"
        assert job.lease_owner == "worker-2"
        assert job.attempts == 2


def test_reclaim_at_max_attempts_marks_failed(env):
    _s, engine = env
    with session_scope(engine) as s:
        job_id = enqueue_job("ocr", {}, s, max_attempts=1)
        claim_jobs(NOW, "worker-1", s)  # attempts -> 1 == max_attempts
        n = reclaim_expired_leases(NOW + timedelta(seconds=301), s)
        assert n == 1
        job = s.execute(select(Job).where(Job.job_id == job_id)).scalar_one()
        assert job.state == "failed"
        assert job.lease_owner is None


def test_unexpired_lease_not_reclaimed(env):
    _s, engine = env
    with session_scope(engine) as s:
        job_id = enqueue_job("ocr", {}, s)
        claim_jobs(NOW, "worker-1", s)
        n = reclaim_expired_leases(NOW + timedelta(seconds=299), s)
        assert n == 0
        job = s.execute(select(Job).where(Job.job_id == job_id)).scalar_one()
        assert job.state == "running"
        assert job.lease_owner == "worker-1"


def test_run_after_in_future_is_not_claimed(env):
    _s, engine = env
    with session_scope(engine) as s:
        job_id = enqueue_job(
            "package", {}, s, run_after=NOW + timedelta(hours=1)
        )
        assert claim_jobs(NOW, "worker-1", s) == []
        job = s.execute(select(Job).where(Job.job_id == job_id)).scalar_one()
        assert job.state == "queued"
        # once the time comes it is claimable
        claimed = claim_jobs(NOW + timedelta(hours=2), "worker-1", s)
        assert [j.job_id for j in claimed] == [job_id]


def test_claim_respects_limit(env):
    _s, engine = env
    with session_scope(engine) as s:
        for i in range(3):
            enqueue_job("ocr", {"i": i}, s)
        claimed = claim_jobs(NOW, "worker-1", s, limit=2)
        assert len(claimed) == 2

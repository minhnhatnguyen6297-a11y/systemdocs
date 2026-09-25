"""MIN-97 slice C — package build handler, sweepers and post-ACK retention.

Covers decision-sheet §4.3/§4.5/§4.7:

- ``scan_unpacked_records`` enqueues ``package_build`` only when packageable
  records wait and no build job is active; rows whose ``packaged_in`` is an
  internal sentinel (``__internal__`` — discovery rows written at ingest)
  are ignored, while ``listener_session`` IS packageable (``PACKAGE_KINDS``).
- ``handle_package_build`` seals all unpackaged records, sets
  ``records.packaged_in`` only on sealed publish, emits a ``processing_status``
  note for invalid payloads (never silent), and cleans orphan staging dirs
  left by a crashed previous build.
- ``expire_packages`` enforces the 30-day post-ACK TTL and the 1 GiB acked
  byte cap; pending/sealed packages are never deleted.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import func, select

from zalo_module.database import get_engine, init_db, session_scope
from zalo_module.delivery.package import build_package
from zalo_module.jobs import package_jobs
from zalo_module.jobs.package_jobs import (
    handle_package_build,
    scan_unpacked_records,
    expire_packages,
)
from zalo_module.jobs.worker import enqueue_job, run_once
from zalo_module.models import Job, Package, Record
from zalo_module.settings import get_settings

CONSUMER_ID = "c0000000-0000-4000-8000-000000000001"
ACCOUNT_ID = "a0000000-0000-4000-8000-000000000099"


@pytest.fixture()
def env(tmp_path):
    settings = get_settings(
        {
            "ZALO_INTAKE_RUNTIME_DIR": str(tmp_path),
            "ZALO_INTAKE_CONSUMER_ID": CONSUMER_ID,
        }
    )
    engine = get_engine(settings)
    init_db(engine)
    yield settings, engine
    engine.dispose()


def _source(**overrides) -> dict:
    src = {
        "provider": "zalo_personal",
        "account_id": ACCOUNT_ID,
        "conversation_id": "syn-thread-1",
        "conversation_type": "user",
        "provider_message_id": "syn-msg-1",
        "client_message_id": "syn-cli-1",
    }
    src.update(overrides)
    return src


def _record_payload(
    kind: str = "message_text",
    logical_id: str | None = None,
    captured_at: str = "2026-09-25T01:00:00+00:00",
    **overrides,
) -> dict:
    payload = {
        "schema_version": "intake.raw-record.v1",
        "record_kind": kind,
        "record_id": str(uuid.uuid4()),
        "logical_id": logical_id or str(uuid.uuid4()),
        "revision": 1,
        "captured_at": captured_at,
        "recorded_at": captured_at,
        "source": _source(),
        "message": {"text": "tin nhắn giả lập"},
    }
    if kind == "processing_status":
        payload.pop("message")
        payload["status"] = {"code": "captured"}
    if kind == "listener_session":
        payload.pop("message")
        payload["source"] = {"provider": "zalo_personal", "account_id": ACCOUNT_ID}
        payload["listener"] = {
            "session_id": str(uuid.uuid4()),
            "state": "connected",
            "observed_at": captured_at,
        }
    payload.update(overrides)
    return payload


def _insert_record(session, payload: dict, kind: str | None = None) -> Record:
    blob = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    row = Record(
        record_id=payload["record_id"],
        logical_id=payload["logical_id"],
        revision=payload["revision"],
        kind=kind or payload["record_kind"],
        canonical_sha256=hashlib.sha256(blob.encode()).hexdigest(),
        payload_json=blob,
        captured_at=payload["captured_at"],
        recorded_at=payload["recorded_at"],
    )
    session.add(row)
    return row


def _records_file(pkg_dir: Path) -> list[dict]:
    text = (pkg_dir / "records.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# sweeper
# ---------------------------------------------------------------------------


def test_sweeper_enqueues_build_for_unpackaged_records(env):
    settings, engine = env
    with session_scope(engine) as s:
        _insert_record(s, _record_payload())
        scan_unpacked_records(s, settings)
        job = s.execute(select(Job).where(Job.kind == "package_build")).scalar_one()
        assert job.state == "queued"

        # Second pass must not pile up a duplicate build job.
        scan_unpacked_records(s, settings)
        count = s.execute(
            select(func.count()).select_from(Job).where(Job.kind == "package_build")
        ).scalar_one()
        assert count == 1


def test_sweeper_enqueues_for_listener_session(env):
    """``listener_session`` is a package kind (contract body kinds) — the
    sweeper must treat waiting session records as packageable work."""
    settings, engine = env
    with session_scope(engine) as s:
        _insert_record(s, _record_payload(kind="listener_session"))
        scan_unpacked_records(s, settings)
        job = s.execute(
            select(Job).where(Job.kind == "package_build")
        ).scalar_one()
        assert job.state == "queued"


def test_sweeper_ignores_internal_sentinel_rows(env):
    """Discovery/internal rows carry ``packaged_in="__internal__"`` at ingest
    — a sentinel, not a package id — so ``IS NULL`` selection skips them."""
    settings, engine = env
    with session_scope(engine) as s:
        row = _insert_record(s, _record_payload())
        row.packaged_in = "__internal__"
        scan_unpacked_records(s, settings)
        assert s.execute(select(func.count()).select_from(Job)).scalar_one() == 0


def test_sweeper_no_consumer_no_enqueue(tmp_path):
    settings = get_settings({"ZALO_INTAKE_RUNTIME_DIR": str(tmp_path)})
    engine = get_engine(settings)
    init_db(engine)
    with session_scope(engine) as s:
        _insert_record(s, _record_payload())
        scan_unpacked_records(s, settings)
        assert s.execute(select(func.count()).select_from(Job)).scalar_one() == 0
    engine.dispose()


# ---------------------------------------------------------------------------
# build handler
# ---------------------------------------------------------------------------


def test_build_seals_records_and_marks_packaged_in(env):
    settings, engine = env
    lids = []
    with session_scope(engine) as s:
        for i in range(3):
            p = _record_payload(captured_at=f"2026-09-25T01:00:0{i}+00:00")
            lids.append(p["logical_id"])
            _insert_record(s, p)
        # listener_session IS a package kind — collected and sealed too
        # (later captured_at keeps the emitted order deterministic)
        sess = _record_payload(
            kind="listener_session", captured_at="2026-09-25T01:00:03+00:00"
        )
        lids.append(sess["logical_id"])
        _insert_record(s, sess)

        result = handle_package_build(s, None, settings)
        assert result["built"] is True
        assert result["record_count"] == 4

        pkg = s.execute(select(Package)).scalar_one()
        assert pkg.status == "sealed"
        assert pkg.sequence == 1
        assert pkg.record_count == 4
        assert pkg.consumer_id == CONSUMER_ID
        pkg_id = pkg.package_id

        for row in s.execute(select(Record)).scalars():
            assert row.packaged_in == pkg_id

    pkg_dir = settings.runtime_root / "packages" / pkg_id
    assert sorted(f.name for f in pkg_dir.iterdir()) == [
        "READY.json", "manifest.json", "records.jsonl",
    ]
    emitted = _records_file(pkg_dir)
    assert [r["logical_id"] for r in emitted] == lids  # captured_at order
    manifest = json.loads((pkg_dir / "manifest.json").read_bytes())
    assert manifest["record_count"] == 4
    ready = json.loads((pkg_dir / "READY.json").read_bytes())
    assert ready["manifest_sha256"] == hashlib.sha256(
        (pkg_dir / "manifest.json").read_bytes()
    ).hexdigest()


def test_build_second_package_gets_next_sequence(env):
    settings, engine = env
    with session_scope(engine) as s:
        _insert_record(s, _record_payload())
        handle_package_build(s, None, settings)
        _insert_record(s, _record_payload())
        handle_package_build(s, None, settings)
        seqs = [
            r.sequence
            for r in s.execute(
                select(Package).order_by(Package.sequence)
            ).scalars()
        ]
        assert seqs == [1, 2]


def test_invalid_record_gets_note_in_same_package(env):
    settings, engine = env
    bad_logical = None
    with session_scope(engine) as s:
        _insert_record(s, _record_payload())
        bad = _record_payload()
        bad_logical = bad["logical_id"]
        # schema_invalid: missing required `message` body for message_text
        del bad["message"]
        bad["status"] = {"code": "note"}  # kind_body_mismatch on top
        _insert_record(s, bad)

        result = handle_package_build(s, None, settings)
        assert result["built"] is True
        assert len(result["skipped_invalid"]) == 1
        assert result["skipped_invalid"][0]["record_id"] == bad["record_id"]

        bad_row = s.get(Record, bad["record_id"])
        pkg = s.execute(select(Package)).scalar_one()
        pkg_id = pkg.package_id
        assert bad_row.packaged_in == pkg_id

    pkg_dir = settings.runtime_root / "packages" / pkg_id
    emitted = _records_file(pkg_dir)
    notes = [r for r in emitted if r["record_kind"] == "processing_status"]
    assert len(notes) == 1
    note = notes[0]
    assert note["record_kind"] == "processing_status"
    assert note["status"]["code"] == "note"
    assert bad["record_id"] in note["status"]["note"]
    # The note is the next revision of the same logical_id and validates.
    assert note["logical_id"] == bad_logical
    assert note["revision"] == 2
    assert note["supersedes"]["record_id"] == bad["record_id"]


def test_invalid_record_without_source_is_marked_not_silent(env):
    settings, engine = env
    with session_scope(engine) as s:
        bad = _record_payload()
        del bad["source"]  # no usable source → note cannot be emitted
        del bad["message"]
        _insert_record(s, bad)

        result = handle_package_build(s, None, settings)
        assert result["skipped_invalid"][0]["record_id"] == bad["record_id"]
        row = s.get(Record, bad["record_id"])
        pkg = s.execute(select(Package)).scalar_one()
        # Marked so it can never stall the build queue; package still emitted.
        assert row.packaged_in == pkg.package_id
        emitted = _records_file(
            settings.runtime_root / "packages" / pkg.package_id
        )
        assert all(r["record_id"] != bad["record_id"] for r in emitted)
        assert len(emitted) == pkg.record_count


def test_crash_mid_build_staging_cleaned_and_rebuilt(env):
    settings, engine = env
    packages_root = settings.runtime_root / "packages"
    orphan = packages_root / ".staging-deadbeef"
    orphan.mkdir(parents=True)
    (orphan / "records.jsonl").write_bytes(b"partial")
    assert not (orphan / "READY.json").exists()  # crash before seal

    with session_scope(engine) as s:
        _insert_record(s, _record_payload())
        result = handle_package_build(s, None, settings)
        assert result["orphan_staging_removed"] == 1
        assert not orphan.exists()
        pkg = s.execute(select(Package)).scalar_one()
        pkg_id = pkg.package_id

    # Byte-exact package is still produced after the crash cleanup.
    emitted = _records_file(settings.runtime_root / "packages" / pkg_id)
    assert len(emitted) == 1


def test_build_respects_record_limit(env, monkeypatch):
    settings, engine = env
    monkeypatch.setattr(package_jobs, "PACKAGE_RECORD_LIMIT", 3)
    with session_scope(engine) as s:
        for i in range(5):
            _insert_record(
                s, _record_payload(captured_at=f"2026-09-25T01:00:0{i}+00:00")
            )
        result = handle_package_build(s, None, settings)
        assert result["record_count"] == 3
        left = s.execute(
            select(func.count())
            .select_from(Record)
            .where(Record.packaged_in.is_(None))
        ).scalar_one()
        assert left == 2
        result2 = handle_package_build(s, None, settings)
        assert result2["record_count"] == 2


def test_run_once_builds_package_end_to_end(env):
    settings, engine = env
    with session_scope(engine) as s:
        _insert_record(s, _record_payload())
    handlers = package_jobs.register({}) or {}
    from zalo_module.jobs.handlers import build_handlers, build_sweepers

    ran = run_once(
        engine,
        settings,
        build_handlers(),
        build_sweepers(),
        limit=2,
        now=datetime.now(timezone.utc),
    )
    assert ran >= 1
    with session_scope(engine) as s:
        job = s.execute(
            select(Job).where(Job.kind == "package_build")
        ).scalar_one()
        assert job.state == "succeeded"
        pkg = s.execute(select(Package)).scalar_one()
        assert pkg.status == "sealed"
        assert s.execute(
            select(func.count())
            .select_from(Record)
            .where(Record.packaged_in == pkg.package_id)
        ).scalar_one() == 1


# ---------------------------------------------------------------------------
# retention — contract §8.3
# ---------------------------------------------------------------------------


def _sealed_package(settings, engine, session, *, sealed_at: str) -> str:
    pid = build_package(
        [_record_payload()], CONSUMER_ID, settings, session
    )
    pkg = session.get(Package, pid)
    pkg.sealed_at = sealed_at
    return pid


def _ack(pkg, when="2026-09-25T02:00:00+00:00"):
    pkg.status = "acked"
    pkg.receipt_json = json.dumps(
        {
            "schema_version": "intake.receipt.v1",
            "receipt_id": str(uuid.uuid4()),
            "package_id": pkg.package_id,
            "consumer_id": CONSUMER_ID,
            "status": "accepted",
            "received_at": when,
            "manifest_sha256": pkg.manifest_sha256,
            "record_count": pkg.record_count,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def test_unacked_package_survives_past_30d(env):
    """Un-ACKed packages live forever — even sealed_at > 30d."""
    settings, engine = env
    old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    with session_scope(engine) as s:
        pid = _sealed_package(settings, engine, s, sealed_at=old)
        stats = expire_packages(s, settings)
        assert stats["expired_count"] == 0
        pkg = s.get(Package, pid)
        assert pkg.status == "sealed"
        assert (settings.runtime_root / pkg.dir_rel_path).is_dir()


def test_acked_package_expires_after_ttl(env):
    settings, engine = env
    old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    with session_scope(engine) as s:
        pid = _sealed_package(settings, engine, s, sealed_at=old)
        pkg = s.get(Package, pid)
        _ack(pkg, when=(datetime.now(timezone.utc) - timedelta(days=31)).isoformat())
        stats = expire_packages(s, settings)
        assert pid in stats["expired"]
        assert pkg.status == "expired"
        assert not (settings.runtime_root / pkg.dir_rel_path).exists()
        # Ledger row kept.
        assert s.get(Package, pid) is not None


def test_recently_acked_package_kept(env):
    settings, engine = env
    recent = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    with session_scope(engine) as s:
        pid = _sealed_package(settings, engine, s, sealed_at=recent)
        pkg = s.get(Package, pid)
        _ack(pkg, when=recent)
        stats = expire_packages(s, settings)
        assert stats["expired_count"] == 0
        assert pkg.status == "acked"
        assert (settings.runtime_root / pkg.dir_rel_path).is_dir()


def test_ack_cap_evicts_oldest_acked_only(env):
    settings, engine = env
    now = datetime.now(timezone.utc)
    with session_scope(engine) as s:
        ids = []
        for i in range(3):
            pid = _sealed_package(
                settings, engine, s,
                sealed_at=(now - timedelta(days=10 - i)).isoformat(),
            )
            pkg = s.get(Package, pid)
            _ack(pkg, when=(now - timedelta(days=10 - i)).isoformat())
            ids.append(pid)
        # tiny cap → everything above one package is evicted, oldest first
        one_dir_bytes = sum(
            f.stat().st_size
            for f in (settings.runtime_root / pkg.dir_rel_path).iterdir()
        )
        stats = expire_packages(
            s, settings, cap_bytes=one_dir_bytes * 2 - 1
        )
        assert ids[0] in stats["expired"]  # oldest evicted
        statuses = {p.package_id: p.status for p in s.execute(select(Package)).scalars()}
        assert statuses[ids[0]] == "expired"
        # at least the newest still fits under the cap accounting
        assert stats["acked_bytes_after"] <= one_dir_bytes * 2 - 1 or len(stats["expired"]) >= 2


def test_expire_packages_handles_missing_dir(env):
    settings, engine = env
    old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    with session_scope(engine) as s:
        pid = _sealed_package(settings, engine, s, sealed_at=old)
        pkg = s.get(Package, pid)
        _ack(pkg, when=old)
        import shutil

        shutil.rmtree(settings.runtime_root / pkg.dir_rel_path)
        stats = expire_packages(s, settings)
        assert pid in stats["expired"]
        assert pkg.status == "expired"


def test_package_sweep_job_handler(env):
    settings, engine = env
    old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    with session_scope(engine) as s:
        pid = _sealed_package(settings, engine, s, sealed_at=old)
        pkg = s.get(Package, pid)
        _ack(pkg, when=old)
        result = package_jobs.handle_package_sweep(s, None, settings)
        assert result["expired_count"] == 1
        assert pkg.status == "expired"


# ---------------------------------------------------------------------------
# M1 — orphan directory cleanup (crash between rename and ledger commit)
# ---------------------------------------------------------------------------


def _age_dir(path: Path, seconds: float) -> None:
    """Force every mtime under ``path`` (and the dir itself) into the past."""
    import os
    import time

    old = time.time() - seconds
    for child in path.rglob("*"):
        os.utime(child, (old, old))
    os.utime(path, (old, old))


def _fake_published_dir(settings, name: str) -> Path:
    d = settings.runtime_root / "packages" / name
    d.mkdir(parents=True)
    (d / "manifest.json").write_bytes(b"{}")
    return d


def test_clean_orphan_removes_stale_published_dir_without_ledger_row(env):
    """Crash after rename but before ledger commit → published-looking dir
    with no ``packages`` row; once provably stale it is swept."""
    settings, engine = env
    orphan = _fake_published_dir(settings, str(uuid.uuid4()))
    _age_dir(orphan, package_jobs.ORPHAN_PUBLISHED_MIN_AGE_SECONDS + 60)
    with session_scope(engine) as s:
        assert package_jobs._clean_orphan_staging(settings, s) == 1
    assert not orphan.exists()


def test_clean_orphan_keeps_fresh_published_dir_without_ledger_row(env):
    """A dir younger than the 10-minute grace window may belong to an
    in-flight build on another worker — never swept."""
    settings, engine = env
    fresh = _fake_published_dir(settings, str(uuid.uuid4()))
    with session_scope(engine) as s:
        assert package_jobs._clean_orphan_staging(settings, s) == 0
    assert fresh.is_dir()


def test_clean_orphan_keeps_ledger_backed_dir(env):
    """A published dir whose package_id exists in the ledger is live data."""
    settings, engine = env
    with session_scope(engine) as s:
        pid = build_package([_record_payload()], CONSUMER_ID, settings, s)
    live = settings.runtime_root / "packages" / pid
    assert live.is_dir()
    _age_dir(live, package_jobs.ORPHAN_PUBLISHED_MIN_AGE_SECONDS + 60)
    with session_scope(engine) as s:
        assert package_jobs._clean_orphan_staging(settings, s) == 0
    assert live.is_dir()


def test_clean_orphan_removes_staging_dirs_regardless_of_age(env):
    """``.staging-*`` dirs are always orphans — even fresh ones."""
    settings, engine = env
    staging = _fake_published_dir(settings, ".staging-abc123")
    with session_scope(engine) as s:
        assert package_jobs._clean_orphan_staging(settings, s) == 1
    assert not staging.exists()


def test_clean_orphan_ignores_loose_files_and_missing_root(env):
    settings, engine = env
    loose = settings.runtime_root / "packages" / "README.txt"
    loose.write_bytes(b"not a package dir")
    with session_scope(engine) as s:
        assert package_jobs._clean_orphan_staging(settings, s) == 0
    assert loose.is_file()

    # No packages/ root at all → nothing to do.
    import shutil

    shutil.rmtree(settings.runtime_root / "packages")
    with session_scope(engine) as s:
        assert package_jobs._clean_orphan_staging(settings, s) == 0

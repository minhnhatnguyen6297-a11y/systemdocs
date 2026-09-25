"""MIN-94 collector wave — missing media, listener sessions, retention,
and ops-state helpers.

Covers the wave's intake contract additions:
- failed attachment markers ingest as ``state='missing'`` media assets with
  a ``media_missing`` processing_status record — never a dropped slot and
  never a rejected envelope;
- a later ``media`` supplement upgrades ``missing`` -> ``captured`` on the
  same attachment identity and makes replays idempotent;
- durable ``listener_sessions`` rows: transitions append, same-state
  heartbeats update in place, generation bumps always open a new row, stale
  generations stay journal-only;
- retention expiry on a fake clock removes originals + derived files but
  keeps records and packages;
- ``listener_gaps`` / ``job_queue_state`` / ``media_usage_bytes`` /
  ``ops_warnings`` behind ``GET /connector/v1/state``.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from zalo_module.database import get_engine, init_db, session_scope
from zalo_module.intake.engine import (
    InboxConflict,
    InboxValidationError,
    _iso,
    ingest_message_envelope,
    ingest_webhook_event,
    job_queue_state,
    listener_gaps,
    media_usage_bytes,
    ops_warnings,
    utcnow,
)
from zalo_module.delivery.record_check import validate_record
from zalo_module.jobs.package_jobs import handle_package_build
from zalo_module.jobs.worker import enqueue_job
from zalo_module.models import (
    ConnectorAccount,
    JournalEntry,
    ListenerSession,
    MediaAsset,
    Package,
    Record,
    Source,
)
from zalo_module.storage.media import register_media
from zalo_module.storage.retention import expire_media

from test_engine_core import (
    _account,
    _conv_source,
    _consented_ready,
    _media_file,
    _message,
    _settings,
)

UTC = timezone.utc


@pytest.fixture()
def env(tmp_path):
    runtime = tmp_path / "runtime"
    (runtime / "media").mkdir(parents=True)
    settings = _settings(runtime)
    eng = get_engine(settings)
    init_db(eng)
    yield settings, eng
    eng.dispose()


def _session_rows(s: Session, account_id: str) -> list[ListenerSession]:
    return (
        s.execute(
            select(ListenerSession)
            .where(ListenerSession.account_id == account_id)
            .order_by(sa.text("rowid"))
        )
        .scalars()
        .all()
    )


def _state_event(account_id: str, state: str, generation: int,
                 observed_at=None, **kw) -> dict:
    payload = {
        "schema_version": 1,
        "event_type": "state",
        "connector_account_id": account_id,
        "state": state,
        "listener_generation": generation,
        "observed_at": _iso(observed_at or utcnow()),
    }
    payload.update(kw)
    return payload


def _media_event(account_id: str, key: str, **kw) -> dict:
    payload = {
        "schema_version": 1,
        "event_type": "media",
        "connector_account_id": account_id,
        "conversation_id": "c1",
        "conversation_type": "user",
        "source_type": "friend",
        "source_display_name": "Alice",
        "msg_id": "m1",
        "sender_id": "u1",
        "sent_at": _iso(utcnow()),
        "attachment_index": 0,
        "media_object_key": key,
        "mime_type": "image/jpeg",
    }
    payload.update(kw)
    return payload


def _status_records(s: Session, logical_id: str) -> list[Record]:
    return (
        s.execute(
            select(Record)
            .where(
                Record.logical_id == logical_id,
                Record.kind == "processing_status",
            )
            .order_by(Record.revision)
        )
        .scalars()
        .all()
    )


# --- missing media: envelope + media event -------------------------------------


def test_multi_attachment_mixed_download_and_failure(env):
    """A failed download keeps its slot: missing asset + media_missing record,
    siblings still import, envelope ACKs per-slot statuses."""
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        key, size = _media_file(settings, account.connector_account_id)
        failed_key = f"{account.connector_account_id}/d0c1badf00d.jpg"
        result = ingest_message_envelope(
            s, settings,
            _message(
                account.connector_account_id,
                attachments=[
                    {"attachment_index": 0, "media_object_key": key,
                     "mime_type": "image/jpeg", "size_bytes": size},
                    {"attachment_index": 1, "media_object_key": failed_key,
                     "mime_type": "image/jpeg", "status": "failed",
                     "error_code": "download_failed"},
                ],
            ),
        )
        media_statuses = {
            item["attachment_index"]: item["status"]
            for item in result["components"]["media"]
        }
        assert media_statuses == {0: "imported", 1: "missing"}
        assert len(result["media_ids"]) == 2

        assets = {
            a.attachment_id: a
            for a in s.execute(select(MediaAsset)).scalars().all()
        }
        ok_asset = next(
            a for a in assets.values() if a.rel_path == f"media/{key}"
        )
        missing_asset = next(
            a for a in assets.values() if a.rel_path == f"media/{failed_key}"
        )
        assert ok_asset.state == "captured"
        assert ok_asset.sha256 == hashlib.sha256(
            (Path(settings.runtime_root) / ok_asset.rel_path).read_bytes()
        ).hexdigest()
        assert missing_asset.state == "missing"
        assert missing_asset.sha256 == ""

        # media_missing processing_status record on the failed slot's source.
        src = s.execute(
            select(Source).where(
                Source.attachment_id == missing_asset.attachment_id
            )
        ).scalar_one()
        assert src.image_available == 0
        records = _status_records(s, src.logical_id)
        assert len(records) == 1
        payload = json.loads(records[0].payload_json)
        assert payload["status"]["code"] == "media_missing"
        assert "download_failed" in payload["status"]["note"]


def test_failed_attachment_replay_is_idempotent(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        failed_key = f"{account.connector_account_id}/m1.jpg"
        payload = _message(
            account.connector_account_id,
            raw_text=None,
            attachments=[{
                "attachment_index": 0, "media_object_key": failed_key,
                "mime_type": "image/jpeg", "status": "failed",
                "error_code": "download_aborted",
            }],
        )
        first = ingest_message_envelope(s, settings, payload)
        second = ingest_message_envelope(s, settings, payload)
        assert second["components"]["media"][0]["status"] == "duplicate"
        assert first["media_ids"] == second["media_ids"]
        assert s.execute(
            select(func.count()).select_from(MediaAsset)
        ).scalar_one() == 1


def test_storage_full_error_code_ingested_as_missing(env):
    """Storage-full is a visibility marker, not a rejection."""
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        result = ingest_message_envelope(
            s, settings,
            _message(
                account.connector_account_id,
                raw_text=None,
                attachments=[{
                    "attachment_index": 0,
                    "media_object_key": f"{account.connector_account_id}/q.jpg",
                    "mime_type": "image/jpeg", "status": "failed",
                    "error_code": "storage_full",
                }],
            ),
        )
        assert result["components"]["media"][0]["status"] == "missing"
        asset = s.get(MediaAsset, result["media_ids"][0])
        assert asset.state == "missing"


def test_missing_media_validation_errors(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        # Missing error_code rejected.
        bad = _message(
            account.connector_account_id, raw_text=None,
            attachments=[{
                "attachment_index": 0,
                "media_object_key": f"{account.connector_account_id}/v.jpg",
                "mime_type": "image/jpeg", "status": "failed",
            }],
        )
        with pytest.raises(InboxValidationError):
            ingest_message_envelope(s, settings, bad)
        # Invalid error_code rejected.
        bad2 = _message(
            account.connector_account_id, raw_text=None,
            attachments=[{
                "attachment_index": 0,
                "media_object_key": f"{account.connector_account_id}/v.jpg",
                "mime_type": "image/jpeg", "status": "failed",
                "error_code": "PRIVATE https://signed-url",
            }],
        )
        with pytest.raises(InboxValidationError):
            ingest_message_envelope(s, settings, bad2)
        # Containment still enforced without bytes on disk.
        bad3 = _message(
            account.connector_account_id, raw_text=None,
            attachments=[{
                "attachment_index": 0,
                "media_object_key": "../escape.jpg",
                "mime_type": "image/jpeg", "status": "failed",
                "error_code": "download_failed",
            }],
        )
        with pytest.raises(InboxValidationError, match="ngoài storage"):
            ingest_message_envelope(s, settings, bad3)
        assert s.execute(
            select(func.count()).select_from(MediaAsset)
        ).scalar_one() == 0


# --- missing -> captured upgrade ------------------------------------------------


def test_media_supplement_upgrades_missing_asset(env):
    """Failed marker first, downloaded supplement later: same attachment_id,
    real sha256, image_available flipped, captured status revision appended,
    and replays stay idempotent."""
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        key, size = _media_file(settings, account.connector_account_id)
        failed = ingest_webhook_event(
            s, settings,
            _media_event(
                account.connector_account_id, key,
                status="failed", error_code="download_failed",
            ),
        )
        asset_id = failed.attachment_id
        assert s.get(MediaAsset, asset_id).state == "missing"

        # Downloaded supplement on the same slot upgrades the row.
        upgraded = ingest_webhook_event(
            s, settings,
            _media_event(
                account.connector_account_id, key, size_bytes=size,
            ),
        )
        assert upgraded.attachment_id == asset_id
        asset = s.get(MediaAsset, asset_id)
        assert asset.state == "captured"
        content = (Path(settings.runtime_root) / asset.rel_path).read_bytes()
        assert asset.sha256 == hashlib.sha256(content).hexdigest()
        src = s.execute(
            select(Source).where(Source.attachment_id == asset_id)
        ).scalar_one()
        assert src.image_available == 1
        codes = [
            json.loads(r.payload_json)["status"]["code"]
            for r in _status_records(s, src.logical_id)
        ]
        assert codes == ["media_missing", "captured"]

        # The same supplement replayed dedupes to the upgraded asset.
        replay = ingest_webhook_event(
            s, settings,
            _media_event(
                account.connector_account_id, key, size_bytes=size,
            ),
        )
        assert replay.attachment_id == asset_id
        assert s.execute(
            select(func.count()).select_from(MediaAsset)
        ).scalar_one() == 1


def test_envelope_download_upgrades_missing_slot(env):
    """An envelope carrying real bytes for a previously-failed slot upgrades
    the missing asset in place (media ACK reports ``imported``)."""
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        key, size = _media_file(settings, account.connector_account_id)
        failed_payload = _message(
            account.connector_account_id, raw_text=None,
            attachments=[{
                "attachment_index": 0, "media_object_key": key,
                "mime_type": "image/jpeg", "status": "failed",
                "error_code": "download_failed",
            }],
        )
        first = ingest_message_envelope(s, settings, failed_payload)
        asset_id = first["media_ids"][0]
        downloaded = _message(
            account.connector_account_id, raw_text=None,
            attachments=[{
                "attachment_index": 0, "media_object_key": key,
                "mime_type": "image/jpeg", "size_bytes": size,
            }],
        )
        second = ingest_message_envelope(s, settings, downloaded)
        assert second["components"]["media"][0]["status"] == "imported"
        assert second["media_ids"][0] == asset_id
        asset = s.get(MediaAsset, asset_id)
        assert asset.state == "captured" and asset.sha256 != ""
        # A later replay of the downloaded form is a duplicate, not a conflict.
        third = ingest_message_envelope(s, settings, downloaded)
        assert third["components"]["media"][0]["status"] == "duplicate"


def test_conflicting_media_payload_still_rejected(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        key, size = _media_file(settings, account.connector_account_id)
        key2, size2 = _media_file(
            settings, account.connector_account_id, "other.jpg",
            b"\xff\xd8\xff\xe1" + b"\x02" * 40,
        )
        ingest_message_envelope(
            s, settings,
            _message(
                account.connector_account_id, raw_text=None,
                attachments=[{
                    "attachment_index": 0, "media_object_key": key,
                    "mime_type": "image/jpeg", "status": "failed",
                    "error_code": "download_failed",
                }],
            ),
        )
        # Same slot, different object key on a downloaded supplement.
        with pytest.raises(InboxConflict):
            ingest_webhook_event(
                s, settings,
                _media_event(
                    account.connector_account_id, key2, size_bytes=size2,
                ),
            )
        # A failed marker replayed with a different reserved key conflicts.
        with pytest.raises(InboxConflict):
            ingest_message_envelope(
                s, settings,
                _message(
                    account.connector_account_id, raw_text=None,
                    attachments=[{
                        "attachment_index": 0,
                        "media_object_key": key2,
                        "mime_type": "image/jpeg", "status": "failed",
                        "error_code": "download_failed",
                    }],
                ),
            )


# --- durable listener sessions ----------------------------------------------------


def test_listener_session_heartbeat_updates_in_place(env):
    """Same-state reports refresh last_heartbeat_at — no unbounded rows."""
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        aid = account.connector_account_id
        # Connect via QR login (accepted).
        r = ingest_webhook_event(
            s, settings,
            _state_event(aid, "connected", 1, qr_login_success=True,
                         bound_zalo_id="z1"),
        )
        assert r["changed"] is True
        rows = _session_rows(s, aid)
        assert len(rows) == 1
        first_beat = rows[0].last_heartbeat_at

        # Repeated same-state heartbeats update the same row.
        ingest_webhook_event(s, settings, _state_event(aid, "connected", 1))
        ingest_webhook_event(s, settings, _state_event(aid, "connected", 1))
        s.expire_all()
        rows = _session_rows(s, aid)
        assert len(rows) == 1
        assert rows[0].last_heartbeat_at >= first_beat


def test_listener_session_transitions_and_generation(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        aid = account.connector_account_id
        ingest_webhook_event(
            s, settings,
            _state_event(aid, "connected", 1, qr_login_success=True,
                         bound_zalo_id="z1"),
        )
        ingest_webhook_event(s, settings, _state_event(aid, "disconnected", 1))
        # Same-state reconnect at the same generation = a new row (transition).
        ingest_webhook_event(s, settings, _state_event(aid, "connected", 1))
        # A generation bump always opens a new row, even for a repeated state.
        ingest_webhook_event(s, settings, _state_event(aid, "connected", 2))
        s.expire_all()
        rows = _session_rows(s, aid)
        assert [r.state for r in rows] == [
            "connected", "disconnected", "connected", "connected",
        ]
        assert len({r.session_id for r in rows}) == 4
        # gap marker recorded by the disconnected report.
        assert s.get(ConnectorAccount, aid).gap_started_at is not None


def test_stale_generation_is_journal_only(env):
    """Revoked/stale listener generations never mutate durable sessions."""
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        aid = account.connector_account_id
        ingest_webhook_event(
            s, settings,
            _state_event(aid, "connected", 5, qr_login_success=True,
                         bound_zalo_id="z1"),
        )
        r = ingest_webhook_event(
            s, settings, _state_event(aid, "disconnected", 4)
        )
        assert r["changed"] is False
        s.expire_all()
        rows = _session_rows(s, aid)
        assert len(rows) == 1  # only the accepted connect
        assert s.get(ConnectorAccount, aid).session_state == "usable"
        # The stale report is still journaled (audit), just not applied.
        journal_count = s.execute(
            select(func.count())
            .select_from(JournalEntry)
        ).scalar_one()
        assert journal_count == 2


def test_listener_sessions_survive_restart(env):
    """Session rows are durable: a module restart keeps them readable."""
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        aid = account.connector_account_id
        ingest_webhook_event(
            s, settings,
            _state_event(aid, "connected", 1, qr_login_success=True,
                         bound_zalo_id="z1"),
        )
        ingest_webhook_event(s, settings, _state_event(aid, "disconnected", 1))
        expected = [
            (row.state, row.observed_at) for row in _session_rows(s, aid)
        ]
    eng.dispose()

    eng2 = get_engine(settings)
    init_db(eng2)
    try:
        with session_scope(eng2) as s:
            rows = _session_rows(s, aid)
            assert [(r.state, r.observed_at) for r in rows] == expected
            # Post-restart reconnect at a newer generation appends cleanly.
            ingest_webhook_event(
                s, settings, _state_event(aid, "connected", 2)
            )
            s.expire_all()
            rows = _session_rows(s, aid)
            assert [r.state for r in rows] == [
                "connected", "disconnected", "connected",
            ]
    finally:
        eng2.dispose()


# --- retention (fake clock) -------------------------------------------------------


def test_expire_media_fake_clock_removes_original_and_derived(env):
    settings, eng = env
    captured = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
    with session_scope(eng) as s:
        aid = str(uuid.uuid4())
        rel = f"media/{aid}-a.jpg"
        target = Path(settings.runtime_root) / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 8)
        derived_dir = (
            Path(settings.runtime_root) / "media" / "derived" / aid
        )
        derived_dir.mkdir(parents=True)
        (derived_dir / "page1.png").write_bytes(b"\x89PNG")
        sibling = (
            Path(settings.runtime_root) / "media" / "derived"
            / f"{aid}-thumb.png"
        )
        sibling.write_bytes(b"\x89PNG")
        register_media(
            aid, hashlib.sha256(b"x").hexdigest(), rel, captured, s
        )
        # A younger asset on the same clock must NOT expire yet.
        fresh_id = str(uuid.uuid4())
        register_media(
            fresh_id, hashlib.sha256(b"y").hexdigest(),
            f"media/{fresh_id}-b.jpg",
            captured + timedelta(hours=100), s,
        )
        s.commit()

        # One second before expiry: nothing happens.
        due = captured + timedelta(hours=168)
        assert expire_media(due - timedelta(seconds=1), s, settings) == 0
        assert target.is_file()
        s.commit()

        # At expiry: original + derived variants removed; row stays expired;
        # a not-yet-due asset is untouched.
        (Path(settings.runtime_root) / f"media/{fresh_id}-b.jpg").write_bytes(b"jpg")
        assert expire_media(due + timedelta(seconds=1), s, settings) == 1
        assert not target.exists()
        assert not derived_dir.exists()
        assert not sibling.exists()
        s.flush()
        s.expire_all()
        assert s.get(MediaAsset, aid).state == "expired"
        assert s.get(MediaAsset, fresh_id).state == "captured"


def test_expire_media_keeps_records_and_tolerates_missing_files(env):
    settings, eng = env
    captured = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        key, size = _media_file(settings, account.connector_account_id)
        result = ingest_message_envelope(
            s, settings,
            _message(
                account.connector_account_id, raw_text="hi",
                attachments=[{
                    "attachment_index": 0, "media_object_key": key,
                    "mime_type": "image/jpeg", "size_bytes": size,
                }],
            ),
        )
        asset = s.get(MediaAsset, result["media_ids"][0])
        asset.captured_at = _iso(captured)
        asset.expires_at = _iso(captured + timedelta(hours=168))
        record_count = s.execute(
            select(func.count()).select_from(Record)
        ).scalar_one()
        journal_count = s.execute(
            select(func.count()).select_from(JournalEntry)
        ).scalar_one()

        # The file is already gone on disk — expiry still flips the row.
        media_path = Path(settings.runtime_root) / asset.rel_path
        media_path.unlink()
        expired = expire_media(
            captured + timedelta(hours=169), s, settings
        )
        assert expired == 1
        s.flush()
        s.expire_all()
        assert s.get(MediaAsset, asset.attachment_id).state == "expired"
        # Records + journal survive untouched.
        assert s.execute(
            select(func.count()).select_from(Record)
        ).scalar_one() == record_count
        assert s.execute(
            select(func.count()).select_from(JournalEntry)
        ).scalar_one() == journal_count


def test_expire_media_missing_state_ages_out(env):
    """A ``state='missing'`` placeholder expires on the same 168h clock."""
    settings, eng = env
    captured = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
    with session_scope(eng) as s:
        register_media(
            str(uuid.uuid4()), "", "media/no-bytes.jpg",
            captured, s, state="missing",
        )
        s.commit()
        assert expire_media(
            captured + timedelta(hours=169), s, settings
        ) == 1


# --- ops-state helpers --------------------------------------------------------------


def test_listener_gaps_closed_and_open(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        aid = account.connector_account_id
        t0 = datetime(2026, 9, 25, 10, 0, tzinfo=UTC)
        ingest_webhook_event(
            s, settings,
            _state_event(aid, "connected", 1, t0, qr_login_success=True,
                         bound_zalo_id="z1"),
        )
        ingest_webhook_event(
            s, settings, _state_event(aid, "disconnected", 1, t0)
        )
        reconnect = t0 + timedelta(seconds=30)
        ingest_webhook_event(
            s, settings, _state_event(aid, "connected", 1, reconnect)
        )
        s.expire_all()
        account = s.get(ConnectorAccount, aid)
        gaps = listener_gaps(s, account, now=reconnect)
        closed = [g for g in gaps if not g["ongoing"]]
        assert any(
            g["ended_at"] is not None for g in closed
        )
        # Still connected afterwards: no open gap.
        assert not any(g["ongoing"] for g in gaps)

        # Disconnect again and leave it open.
        later = reconnect + timedelta(seconds=30)
        ingest_webhook_event(
            s, settings, _state_event(aid, "disconnected", 1, later)
        )
        s.expire_all()
        account = s.get(ConnectorAccount, aid)
        gaps = listener_gaps(s, account, now=later)
        assert any(g["ongoing"] for g in gaps)


def test_job_queue_state_counts_and_oldest(env):
    settings, eng = env
    with session_scope(eng) as s:
        assert job_queue_state(s) == {
            "pending_jobs": 0, "oldest_age_s": None,
        }
        enqueue_job("kind-a", {"x": 1}, s)
        jid = enqueue_job("kind-b", {"x": 2}, s)
        s.execute(
            sa.text("UPDATE jobs SET state='retry_wait' WHERE job_id=:j"),
            {"j": jid},
        )
        now = utcnow()
        state = job_queue_state(s, now=now)
        assert state["pending_jobs"] == 2
        assert 0 <= state["oldest_age_s"] <= 5


def test_ops_warnings_and_media_usage(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        assert ops_warnings(account, [], {"quota_bytes": 100, "usage_bytes": 10}) == []
        # Open gap -> gap_open warning.
        warnings = ops_warnings(
            account, [{"started_at": _iso(utcnow()), "ended_at": None,
                       "ongoing": True}],
            {"quota_bytes": 100, "usage_bytes": 10},
        )
        assert {w["code"] for w in warnings} == {"gap_open"}
        # Disk pressure over 90% -> disk_pressure; at quota -> storage_full.
        warnings = ops_warnings(
            account, [],
            {"quota_bytes": 100, "usage_bytes": 95, "storage_full": False},
        )
        assert {w["code"] for w in warnings} == {"disk_pressure"}
        warnings = ops_warnings(
            account, [],
            {"quota_bytes": 100, "usage_bytes": 100, "storage_full": True},
        )
        assert {w["code"] for w in warnings} == {"storage_full"}
        # Stale heartbeat while marked usable -> listener_heartbeat_stale.
        account.session_state = "usable"
        account.last_seen_at = _iso(utcnow() - timedelta(seconds=120))
        warnings = ops_warnings(
            account, [], {"quota_bytes": 100, "usage_bytes": 10},
            now=utcnow(),
        )
        assert {w["code"] for w in warnings} == {"listener_heartbeat_stale"}

    (Path(settings.runtime_root) / "media" / "x.jpg").write_bytes(b"123")
    (Path(settings.runtime_root) / "media" / "sub").mkdir()
    (Path(settings.runtime_root) / "media" / "sub" / "y.jpg").write_bytes(b"45")
    assert media_usage_bytes(settings) == 5


# --- contract source events (undo/reaction) + listener_session records --------


def _source_event(account_id: str, subtype: str = "recall", **kw) -> dict:
    payload = {
        "schema_version": 1,
        "event_type": "source_event",
        "connector_account_id": account_id,
        "conversation_id": "c1",
        "conversation_type": "user",
        "event_subtype": subtype,
        "target_provider_message_id": "gmsg-1",
        "target_client_message_id": "cmsg-1",
        "observed_at": _iso(utcnow()),
        "sender_id": "u1",
    }
    if subtype == "reaction":
        payload["reaction_icon"] = ":>"
    payload.update(kw)
    return payload


def _kind_records(s: Session, kind: str) -> list[Record]:
    return (
        s.execute(
            select(Record)
            .where(Record.kind == kind)
            .order_by(sa.text("rowid"))
        )
        .scalars()
        .all()
    )


def _payload_of(rec: Record) -> dict:
    return json.loads(rec.payload_json)


def test_source_event_recall_record(env):
    """A connector ``undo`` → schema-valid ``source_event`` record keeping
    both provider and client message ids (contract §5.2/§5.3)."""
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        aid = account.connector_account_id
        r = ingest_webhook_event(s, settings, _source_event(aid, "recall"))
        assert r["duplicate"] is False
        recs = _kind_records(s, "source_event")
        assert len(recs) == 1
        payload = _payload_of(recs[0])
        assert validate_record(payload) == []
        assert payload["record_kind"] == "source_event"
        assert payload["revision"] == 1
        assert "supersedes" not in payload
        event = payload["event"]
        assert event["event_type"] == "recall"
        assert event["target_provider_message_id"] == "gmsg-1"
        assert event["target_client_message_id"] == "cmsg-1"
        assert event["observed_at"] == payload["captured_at"]
        assert "reaction_icon" not in event
        src = payload["source"]
        assert src["provider"] == "zalo_personal"
        assert src["provider_message_id"] == "gmsg-1"
        assert src["client_message_id"] == "cmsg-1"
        assert src["conversation_id"] == "c1"
        # The record only observes the recall — the target message's own
        # logical chain is untouched.
        assert s.get(Source, recs[0].logical_id).scope == "source_event"


def test_source_event_reaction_record(env):
    """A connector ``reaction`` keeps its icon verbatim on the record."""
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        aid = account.connector_account_id
        r = ingest_webhook_event(
            s, settings, _source_event(aid, "reaction", reaction_icon=":handclap")
        )
        assert r["duplicate"] is False
        payload = _payload_of(_kind_records(s, "source_event")[0])
        assert validate_record(payload) == []
        event = payload["event"]
        assert event["event_type"] == "reaction"
        assert event["reaction_icon"] == ":handclap"
        assert event["target_provider_message_id"] == "gmsg-1"
        assert event["target_client_message_id"] == "cmsg-1"


def test_source_event_replay_dedupes(env):
    """Connector replays hash to the same dedupe row — one record, no churn."""
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        aid = account.connector_account_id
        event = _source_event(aid, "recall")
        r1 = ingest_webhook_event(s, settings, event)
        r2 = ingest_webhook_event(s, settings, dict(event))
        assert r2["duplicate"] is True
        assert r2["record_id"] == r1["record_id"]
        assert len(_kind_records(s, "source_event")) == 1
        # Distinct observations (different target) still record separately.
        r3 = ingest_webhook_event(
            s, settings,
            _source_event(aid, "recall", target_provider_message_id="gmsg-2"),
        )
        assert r3["duplicate"] is False
        assert len(_kind_records(s, "source_event")) == 2


@pytest.mark.parametrize(
    "mutate",
    [
        # reaction without an icon is unrecordable (contract requires it)
        {"event_subtype": "reaction"},
        # recall must never carry an icon
        {"reaction_icon": ":>"},
        # no resolvable target
        {"target_provider_message_id": ""},
        # unknown subtype
        {"event_subtype": "discovery"},
        # empty client id fails validation rather than silently dropping
        {"target_client_message_id": "   "},
    ],
)
def test_source_event_validation_rejects_malformed(env, mutate):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        event = _source_event(account.connector_account_id, "recall")
        event.update(mutate)
        with pytest.raises(InboxValidationError):
            ingest_webhook_event(s, settings, event)
        assert _kind_records(s, "source_event") == []


def test_message_record_keeps_client_message_id(env):
    """``cliMsgId`` rides the envelope into ``source.client_message_id`` so
    later recall/reaction events can link back to the message."""
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        result = ingest_message_envelope(
            s, settings,
            _message(account.connector_account_id, client_message_id="cli-9"),
        )
        assert result["components"]["text"] == "imported"
        recs = _kind_records(s, "message_text")
        assert len(recs) == 1
        payload = _payload_of(recs[0])
        assert validate_record(payload) == []
        assert payload["source"]["client_message_id"] == "cli-9"
        # Bad client ids are rejected, not silently dropped.
        with pytest.raises(InboxValidationError):
            ingest_message_envelope(
                s, settings,
                _message(
                    account.connector_account_id,
                    msg_id="m2",
                    client_message_id="  ",
                ),
            )


def _listener_records(s: Session, account_id: str) -> list[Record]:
    session_ids = [
        row.session_id for row in _session_rows(s, account_id)
    ]
    if not session_ids:
        return []
    return (
        s.execute(
            select(Record)
            .where(Record.logical_id.in_(session_ids))
            .order_by(sa.text("rowid"))
        )
        .scalars()
        .all()
    )


def test_listener_session_records_on_transitions_and_generation(env):
    """Each applied transition/generation bump emits a schema-valid
    ``listener_session`` record keyed by the new session_id; same-state
    heartbeats never do; a reconnect after a reported gap carries
    ``uncertain_gap``."""
    settings, eng = env
    t0 = datetime(2026, 3, 1, 10, 0, tzinfo=UTC)
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        aid = account.connector_account_id

        ingest_webhook_event(
            s, settings,
            _state_event(aid, "connected", 1, t0, qr_login_success=True,
                         bound_zalo_id="z1"),
        )
        # Heartbeat: same state + generation -> row refresh only.
        ingest_webhook_event(
            s, settings, _state_event(aid, "connected", 1,
                                      t0 + timedelta(minutes=1))
        )
        recs = _listener_records(s, aid)
        assert len(recs) == 1
        p1 = _payload_of(recs[0])
        assert validate_record(p1) == []
        assert p1["record_kind"] == "listener_session"
        assert p1["listener"]["state"] == "connected"
        assert p1["listener"]["session_id"] == recs[0].logical_id
        assert "uncertain_gap" not in p1["listener"]
        # module-observed clock: observed_at == captured_at == recorded_at
        assert p1["listener"]["observed_at"] == p1["captured_at"]
        assert p1["captured_at"] == p1["recorded_at"]

        # Disconnect -> new session row + new record (new logical chain).
        t_disc = t0 + timedelta(minutes=2)
        ingest_webhook_event(
            s, settings, _state_event(aid, "disconnected", 1, t_disc)
        )
        # Reconnect at a bumped generation closes the reported gap.
        t_re = t0 + timedelta(minutes=5)
        ingest_webhook_event(
            s, settings, _state_event(aid, "connected", 2, t_re)
        )
        recs = _listener_records(s, aid)
        assert len(recs) == 3
        states = [_payload_of(r)["listener"]["state"] for r in recs]
        assert states == ["connected", "disconnected", "connected"]
        for rec in recs:
            payload = _payload_of(rec)
            assert validate_record(payload) == []
            assert payload["revision"] == 1
            assert "supersedes" not in payload
        gap = _payload_of(recs[2])["listener"]["uncertain_gap"]
        assert gap["started_at"] == _iso(t_disc)
        assert gap["ended_at"] == (
            _payload_of(recs[2])["listener"]["observed_at"]
        )
        assert gap["start_is_estimate"] is True
        # Every session_id is a distinct logical chain — the reconnect never
        # revises the previous session's chain.
        assert len({r.logical_id for r in recs}) == 3


def test_listener_heartbeat_and_stale_generation_emit_no_record(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        aid = account.connector_account_id
        ingest_webhook_event(
            s, settings,
            _state_event(aid, "connected", 5, qr_login_success=True,
                         bound_zalo_id="z1"),
        )
        r = ingest_webhook_event(
            s, settings, _state_event(aid, "disconnected", 4)
        )
        assert r["changed"] is False
        assert len(_listener_records(s, aid)) == 1


def test_listener_session_crash_gap_and_repeat_episodes(env):
    """A generation bump while ``usable`` = silent coverage loss: the new
    session's record declares ``uncertain_gap`` starting at the last
    certain coverage (last heartbeat, per contract). A later restart must
    still detect a fresh episode — a consumed marker cannot suppress it."""
    settings, eng = env
    t0 = datetime(2026, 3, 1, 10, 0, tzinfo=UTC)
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        aid = account.connector_account_id
        ingest_webhook_event(
            s, settings,
            _state_event(aid, "connected", 1, t0, qr_login_success=True,
                         bound_zalo_id="z1"),
        )
        row1 = _session_rows(s, aid)[0]
        # Connector restart while usable — observed stamps bound the gap.
        ingest_webhook_event(
            s, settings,
            _state_event(aid, "connected", 2, t0 + timedelta(hours=1)),
        )
        rows = _session_rows(s, aid)
        assert [r.state for r in rows] == ["connected", "connected"]
        recs = _listener_records(s, aid)
        assert len(recs) == 2
        payload2 = _payload_of(recs[1])
        assert validate_record(payload2) == []
        gap = payload2["listener"]["uncertain_gap"]
        # estimate = last certain coverage, not the detection time
        assert gap["started_at"] == row1.last_heartbeat_at
        assert gap["ended_at"] == payload2["listener"]["observed_at"]
        assert gap["start_is_estimate"] is True

        # Second restart — the consumed marker must not suppress this gap.
        ingest_webhook_event(
            s, settings,
            _state_event(aid, "connected", 3, t0 + timedelta(hours=2)),
        )
        recs = _listener_records(s, aid)
        assert len(recs) == 3
        payload3 = _payload_of(recs[2])
        assert validate_record(payload3) == []
        gap2 = payload3["listener"]["uncertain_gap"]
        assert gap2["started_at"] == rows[1].last_heartbeat_at
        assert gap2["ended_at"] == payload3["listener"]["observed_at"]


def test_source_and_session_records_packageable_discovery_excluded(tmp_path):
    """``source_event`` + ``listener_session`` records land in consumer
    packages; internal discovery rows (``packaged_in='__internal__'``)
    never do."""
    runtime = tmp_path / "runtime"
    (runtime / "media").mkdir(parents=True)
    settings = _settings(runtime, consumer_id=str(uuid.uuid4()))
    eng = get_engine(settings)
    init_db(eng)
    try:
        with session_scope(eng) as s:
            account = _account(s)
            _consented_ready(s, account)
            aid = account.connector_account_id
            ingest_webhook_event(
                s, settings,
                _state_event(aid, "connected", 1, qr_login_success=True,
                             bound_zalo_id="z1"),
            )
            ingest_webhook_event(s, settings, _source_event(aid, "recall"))
            # Internal discovery row — lands with the sentinel at ingest.
            ingest_webhook_event(
                s, settings,
                {
                    "schema_version": 1,
                    "event_type": "discovery",
                    "connector_account_id": aid,
                    "conversation_id": "c2",
                    "conversation_type": "user",
                    "source_type": "friend",
                    "source_display_name": "Bob",
                    "last_activity_at": _iso(utcnow()),
                },
            )
            internal = [
                r for r in _kind_records(s, "source_event")
                if r.packaged_in == "__internal__"
            ]
            assert len(internal) == 1

            result = handle_package_build(s, None, settings)
            # session + recall records ship; discovery stays internal.
            assert result["record_count"] == 2
            pkg = s.execute(select(Package)).scalar_one()
            lines = (
                Path(settings.runtime_root)
                / pkg.dir_rel_path
                / "records.jsonl"
            ).read_text(encoding="utf-8").strip().splitlines()
            kinds = sorted(json.loads(line)["record_kind"] for line in lines)
            assert kinds == ["listener_session", "source_event"]
            assert _payload_of(internal[0])["event"]["event_type"] == (
                "discovery"
            )
            s.expire_all()
            assert s.get(Record, internal[0].record_id).packaged_in == (
                "__internal__"
            )
    finally:
        eng.dispose()


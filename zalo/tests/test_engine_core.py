"""MIN-103 slice B — engine tests ported from notary_v2 tests/test_zalo_inbox.py.

Covers: consent/policy two-phase, source-sync versions, connector state +
QR TTL + gap recording, data-sync lifecycle/CAS/timeout/terminal idempotency,
and ingest dedupe/conflict/eligibility on the module schema (journal_entries
dedupe, records, media_assets).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from zalo_module.database import get_engine, init_db, session_scope
from zalo_module.intake import engine
from zalo_module.intake.engine import (
    DATA_SYNC_COUNTERS,
    InboxConflict,
    InboxValidationError,
    _aware,
    _canonical_json,
    _iso,
    _source_from_payload,
    ack_policy,
    ack_source_sync,
    apply_connector_report,
    apply_data_sync_report,
    apply_intake_consent,
    connector_state,
    data_sync_command,
    ingest_message_envelope,
    public_qr,
    request_source_sync,
    resolve_media_object,
    set_source_policy,
    source_ready,
    start_data_sync,
    utcnow,
)
from zalo_module.models import (
    ConnectorAccount,
    ConvSource,
    DataSyncRun,
    JournalEntry,
    MediaAsset,
    Record,
    Source,
)
from zalo_module.settings import Settings

UTC = timezone.utc


# --- fixtures / builders -------------------------------------------------------


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
        webhook_secret="test-webhook-secret",
        bootstrap_secret="test-bootstrap-secret",
        data_sync_timeout_seconds=900,
    )
    kwargs.update(overrides)
    return Settings(**kwargs)


@pytest.fixture()
def env(tmp_path):
    runtime = tmp_path / "runtime"
    (runtime / "media").mkdir(parents=True)
    settings = _settings(runtime)
    eng = get_engine(settings)
    init_db(eng)
    yield settings, eng
    eng.dispose()


def _account(session: Session) -> ConnectorAccount:
    account = ConnectorAccount(connector_account_id=str(uuid.uuid4()))
    session.add(account)
    session.flush()
    return account


def _connected(account: ConnectorAccount, generation: int = 1) -> None:
    account.session_state = "usable"
    account.listener_generation = generation
    account.last_seen_at = _iso(utcnow())


def _consented_ready(session: Session, account: ConnectorAccount) -> None:
    """Consent + ack so ``source_ready`` gates pass."""
    account.intake_consented_at = _iso(utcnow())
    account.policy_version = 1
    account.policy_acked_version = 1


def _conv_source(
    session: Session,
    account: ConnectorAccount,
    *,
    conversation_id: str = "c1",
    conversation_type: str = "user",
    source_type: str = "friend",
    display_name: str = "Alice",
    enabled: int = 1,
    acked: int | None = 1,
) -> ConvSource:
    source = ConvSource(
        conv_source_id=str(uuid.uuid4()),
        connector_account_id=account.connector_account_id,
        conversation_id=conversation_id,
        conversation_type=conversation_type,
        source_type=source_type,
        display_name=display_name,
        enabled=enabled,
        enabled_explicit=1,
        acked_enabled=acked,
        policy_version=1,
        policy_acked_version=1,
        created_at=_iso(utcnow()),
        updated_at=_iso(utcnow()),
    )
    session.add(source)
    session.flush()
    return source


def _media_file(settings: Settings, account_id: str, name: str = "f1.jpg",
                content: bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 32) -> tuple[str, int]:
    """Create ``media/<account>/<name>``; return (media_object_key, size)."""
    key = f"{account_id}/{name}"
    path = Path(settings.runtime_root) / "media" / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return key, len(content)


def _message(account_id: str, **kw) -> dict:
    payload = {
        "schema_version": 1,
        "event_type": "message",
        "connector_account_id": account_id,
        "conversation_id": "c1",
        "conversation_type": "user",
        "source_type": "friend",
        "source_display_name": "Alice",
        "msg_id": "m1",
        "sender_id": "u1",
        "sent_at": _iso(utcnow()),
        "raw_text": "hello",
        "attachments": [],
    }
    payload.update(kw)
    return payload


def _counters(**kw) -> dict:
    counters = {key: 0 for key in DATA_SYNC_COUNTERS}
    counters.update(kw)
    return counters


def _report(account_id: str, run_id: str, event_type: str,
            counters: dict, error_code: str | None = None) -> dict:
    payload = {
        "schema_version": 1,
        "event_type": event_type,
        "connector_account_id": account_id,
        "run_id": run_id,
        "counters": counters,
    }
    if error_code is not None:
        payload["error_code"] = error_code
    return payload


# --- policy / consent / ack (ported: two-phase model) ---------------------------


def test_consent_applies_type_defaults_and_restages(env):
    _settings_obj, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        friend = _conv_source(s, account, source_type="friend",
                              enabled=0, acked=None)
        friend.enabled_explicit = None
        stranger = _conv_source(s, account, conversation_id="c2",
                                source_type="stranger", enabled=0, acked=None)
        stranger.enabled_explicit = None
        version = apply_intake_consent(s, account.connector_account_id)
        assert version == 1
        s.expire_all()
        friend = s.get(ConvSource, friend.conv_source_id)
        stranger = s.get(ConvSource, stranger.conv_source_id)
        assert friend.enabled == 1 and friend.enabled_explicit == 0
        assert stranger.enabled == 0
        assert friend.policy_version == 1 and stranger.policy_version == 1


def test_consent_preserves_explicit_choice(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        source = _conv_source(s, account, source_type="stranger",
                              enabled=1, acked=None)
        source.enabled_explicit = 1
        apply_intake_consent(s, account.connector_account_id)
        s.expire_all()
        assert s.get(ConvSource, source.conv_source_id).enabled == 1


def test_policy_ack_mirrors_desired(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        account.policy_acked_version = 0  # desired v1 not yet acked
        source = _conv_source(s, account, enabled=1, acked=None)
        ack_policy(s, account.connector_account_id, 1)
        s.expire_all()
        source = s.get(ConvSource, source.conv_source_id)
        assert source.acked_enabled == 1
        assert source.policy_acked_version == 1
        assert s.get(
            ConnectorAccount, account.connector_account_id
        ).policy_acked_version == 1


def test_policy_ack_wrong_version_rejected(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        with pytest.raises(InboxValidationError):
            ack_policy(s, account.connector_account_id, 99)


def test_policy_ack_idempotent(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        assert ack_policy(s, account.connector_account_id, 1) == 1
        assert ack_policy(s, account.connector_account_id, 1) == 1


def test_set_source_policy_bumps_version(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        source = _conv_source(s, account)
        version = set_source_policy(s, source.conv_source_id, False)
        assert version == 2
        s.expire_all()
        source = s.get(ConvSource, source.conv_source_id)
        assert source.enabled == 0 and source.enabled_explicit == 1
        assert source.policy_version == 2
        assert not source_ready(source)  # ack still at v1


def test_set_source_policy_unknown_source(env):
    _, eng = env
    with session_scope(eng) as s:
        with pytest.raises(InboxValidationError):
            set_source_policy(s, "missing", True)


def test_source_sync_request_and_ack(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        assert request_source_sync(s, account.connector_account_id) == 1
        assert request_source_sync(s, account.connector_account_id) == 2
        with pytest.raises(InboxValidationError):
            ack_source_sync(s, account.connector_account_id, 1)
        assert ack_source_sync(s, account.connector_account_id, 2) == 2
        assert ack_source_sync(s, account.connector_account_id, 2) == 2


def test_new_source_after_consent_restages(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        source = _source_from_payload(
            s,
            {
                "connector_account_id": account.connector_account_id,
                "conversation_id": "c9",
                "conversation_type": "group",
                "source_type": "group",
                "source_display_name": "Team",
            },
            require_source_type=True,
        )
        assert source.enabled == 1
        assert source.enabled_explicit == 0
        s.expire_all()
        assert s.get(
            ConnectorAccount, account.connector_account_id
        ).policy_version == 2
        assert source.policy_version == 2


# --- connector state / QR / gap (ported) ----------------------------------------


def test_connector_state_transitions(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        assert connector_state(account) == "login_required"
        account.session_state = "usable"
        assert connector_state(account) == "disconnected"  # never seen
        account.last_seen_at = _iso(utcnow())
        assert connector_state(account) == "connected"
        account.last_seen_at = _iso(utcnow() - timedelta(seconds=60))
        assert connector_state(account) == "disconnected"
        account.session_state = "disconnected"
        assert connector_state(account) == "disconnected"


def test_qr_public_until_ttl(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        account.qr_image = "data:image/png;base64,x"
        account.qr_expires_at = _iso(utcnow() + timedelta(seconds=30))
        assert public_qr(account) == "data:image/png;base64,x"
        account.qr_expires_at = _iso(utcnow() - timedelta(seconds=1))
        assert public_qr(account) is None
        account.qr_image = None
        assert public_qr(account) is None


def test_stale_generation_report_ignored(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _connected(account, generation=5)
        changed = apply_connector_report(
            account, "disconnected", 4, utcnow()
        )
        assert changed is False
        assert account.session_state == "usable"


def test_connected_after_receiving_records_gap(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _connected(account, generation=1)
        # New generation while still "usable" -> gap marker stamped.
        changed = apply_connector_report(
            account, "connected", 2, utcnow()
        )
        assert changed is True
        assert account.gap_started_at is not None
        # And not stamped twice.
        first_gap = account.gap_started_at
        apply_connector_report(account, "connected", 3, utcnow())
        assert account.gap_started_at == first_gap


def test_disconnect_records_gap_once(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _connected(account, generation=1)
        apply_connector_report(account, "disconnected", 1, utcnow())
        assert account.session_state == "disconnected"
        assert account.gap_started_at is not None


def test_bound_zalo_conflict(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        account.bound_zalo_id = "zalo-1"
        with pytest.raises(InboxConflict):
            apply_connector_report(
                account, "connected", 1, utcnow(), bound_zalo_id="zalo-2"
            )
        # Same id is fine (qr_login_success escapes login_required).
        assert apply_connector_report(
            account, "connected", 1, utcnow(), bound_zalo_id="zalo-1",
            qr_login_success=True,
        ) is True


def test_qr_login_success_requires_identity_and_clears_qr(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        account.session_state = "login_required"
        with pytest.raises(InboxValidationError):
            apply_connector_report(
                account, "connected", 1, utcnow(), qr_login_success=True
            )
        account.qr_image = "data:x"
        account.qr_expires_at = _iso(utcnow() + timedelta(seconds=30))
        apply_connector_report(
            account, "connected", 1, utcnow(),
            qr_login_success=True, bound_zalo_id="z1",
        )
        assert account.bound_zalo_id == "z1"
        assert account.qr_image is None
        assert account.session_state == "usable"


def test_login_required_connect_without_qr_login_ignored(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        changed = apply_connector_report(account, "connected", 1, utcnow())
        assert changed is False
        assert account.session_state == "login_required"


def test_qr_image_report_sets_expiry(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        now = utcnow()
        apply_connector_report(
            account, "login_required", 1, now, qr_image="data:qr"
        )
        assert account.qr_image == "data:qr"
        expires = _aware(account.qr_expires_at)
        assert expires is not None
        assert 95 <= (expires - now).total_seconds() <= 105
        # qr_image=None -> no QR field update (parity).
        apply_connector_report(
            account, "login_required", 1, now, qr_image=None
        )
        assert account.qr_image == "data:qr"
        apply_connector_report(
            account, "login_required", 1, now, qr_image=""
        )
        assert account.qr_expires_at is None


# --- data sync (ported: CAS, terminal idempotency, timeout, one-running) ---------


def _ready_for_sync(s: Session, account: ConnectorAccount) -> ConvSource:
    _consented_ready(s, account)
    _connected(account)
    return _conv_source(s, account)


def test_data_sync_requires_consent(env):
    _, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _connected(account)
        _conv_source(s, account)
        with pytest.raises(InboxValidationError):
            start_data_sync(s, env[0], account.connector_account_id)


def test_data_sync_requires_connected(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        with pytest.raises(InboxConflict):
            start_data_sync(s, settings, account.connector_account_id)


def test_data_sync_requires_policy_acked(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _connected(account)
        _conv_source(s, account)
        # Bump desired without acking -> pending sync gate.
        set_source_policy(
            s,
            s.execute(select(ConvSource)).scalar_one().conv_source_id,
            False,
        )
        with pytest.raises(InboxConflict, match="Chính sách"):
            start_data_sync(s, settings, account.connector_account_id)


def test_data_sync_start_freezes_sources_and_counters(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _connected(account)
        _conv_source(s, account, conversation_id="b")
        _conv_source(s, account, conversation_id="a")
        _conv_source(s, account, conversation_id="docs",
                     source_type="my_documents")  # excluded from sync
        run = start_data_sync(s, settings, account.connector_account_id)
        assert run.status == "running"
        assert json.loads(run.source_ids_json) == ["a", "b"]
        assert json.loads(run.counters_json) == _counters()
        deadline = _aware(run.deadline_at)
        assert (deadline - _aware(run.cutoff_at)).total_seconds() == 900


def test_data_sync_only_one_running(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _ready_for_sync(s, account)
        start_data_sync(s, settings, account.connector_account_id)
        with pytest.raises(InboxConflict, match="Data Sync"):
            start_data_sync(s, settings, account.connector_account_id)


def test_data_sync_command_shape(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _ready_for_sync(s, account)
        assert data_sync_command(s, account.connector_account_id) is None
        run = start_data_sync(s, settings, account.connector_account_id)
        command = data_sync_command(s, account.connector_account_id)
        assert command["command_type"] == "data_sync"
        assert command["run_id"] == run.run_id
        assert command["source_ids"] == ["c1"]
        assert command["cutoff_at"].endswith("Z")


def test_data_sync_progress_monotonic(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _ready_for_sync(s, account)
        run = start_data_sync(s, settings, account.connector_account_id)
        apply_data_sync_report(
            s, _report(account.connector_account_id, run.run_id,
                       "data_sync_progress", _counters(received=5))
        )
        s.expire_all()
        run = s.get(DataSyncRun, run.run_id)
        assert json.loads(run.counters_json)["received"] == 5
        # Regressing counters rejected.
        with pytest.raises(InboxConflict):
            apply_data_sync_report(
                s, _report(account.connector_account_id, run.run_id,
                           "data_sync_progress", _counters(received=4))
            )


def test_data_sync_complete_terminal_idempotent(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _ready_for_sync(s, account)
        run = start_data_sync(s, settings, account.connector_account_id)
        report = _report(account.connector_account_id, run.run_id,
                         "data_sync_complete", _counters(received=2))
        done = apply_data_sync_report(s, report)
        assert done.status == "completed_best_effort"
        # Identical replay is a no-op; divergent payload conflicts.
        again = apply_data_sync_report(s, report)
        assert again.run_id == run.run_id
        with pytest.raises(InboxConflict):
            apply_data_sync_report(
                s, _report(account.connector_account_id, run.run_id,
                           "data_sync_complete", _counters(received=3))
            )


def test_data_sync_failed_terminal(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _ready_for_sync(s, account)
        run = start_data_sync(s, settings, account.connector_account_id)
        done = apply_data_sync_report(
            s, _report(account.connector_account_id, run.run_id,
                       "data_sync_failed", _counters(),
                       error_code="listener_crashed")
        )
        assert done.status == "error"
        assert done.error_code == "listener_crashed"
        assert done.completed_at is not None


def test_data_sync_report_wrong_account_rejected(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        other = _account(s)
        _ready_for_sync(s, account)
        run = start_data_sync(s, settings, account.connector_account_id)
        with pytest.raises(InboxConflict):
            apply_data_sync_report(
                s, _report(other.connector_account_id, run.run_id,
                           "data_sync_progress", _counters())
            )


def test_data_sync_timeout_atomic(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _ready_for_sync(s, account)
        run = start_data_sync(s, settings, account.connector_account_id)
        # Expire the deadline, then poll the command -> auto-timeout.
        s.execute(
            sa.text(
                "UPDATE data_sync_runs SET deadline_at = :d WHERE run_id = :r"
            ),
            {"d": _iso(utcnow() - timedelta(seconds=1)), "r": run.run_id},
        )
        s.expire_all()
        assert data_sync_command(s, account.connector_account_id) is None
        s.expire_all()
        run = s.get(DataSyncRun, run.run_id)
        assert run.status == "error" and run.error_code == "timeout"
        # A stale report after timeout conflicts, never resurrects.
        with pytest.raises(InboxConflict):
            apply_data_sync_report(
                s, _report(account.connector_account_id, run.run_id,
                           "data_sync_complete", _counters())
            )


def test_data_sync_report_shape_validation(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _ready_for_sync(s, account)
        run = start_data_sync(s, settings, account.connector_account_id)
        bad = _report(account.connector_account_id, run.run_id,
                      "data_sync_progress", _counters())
        bad["extra"] = 1
        with pytest.raises(InboxValidationError):
            apply_data_sync_report(s, bad)
        bad2 = _report(account.connector_account_id, run.run_id,
                       "data_sync_failed", _counters())  # missing error_code
        with pytest.raises(InboxValidationError):
            apply_data_sync_report(s, bad2)
        bad3 = _report(account.connector_account_id, run.run_id,
                       "data_sync_failed", _counters(), error_code="BAD!")
        with pytest.raises(InboxValidationError):
            apply_data_sync_report(s, bad3)


# --- ingest (ported: dedupe, eligibility, media validation) ---------------------


def test_ingest_imports_text_record(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        result = ingest_message_envelope(s, settings, _message(
            account.connector_account_id))
        assert result["ignored"] is False
        assert result["components"]["text"] == "imported"
        record = s.get(Record, result["text_id"])
        assert record is not None and record.kind == "message_text"
        payload = json.loads(record.payload_json)
        assert payload["message"]["text"] == "hello"
        src = s.get(Source, record.logical_id)
        assert src.scope == "msg"
        assert src.provider_message_id == "m1"


def test_ingest_duplicate_same_payload_idempotent(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        payload = _message(account.connector_account_id)
        first = ingest_message_envelope(s, settings, payload)
        second = ingest_message_envelope(s, settings, payload)
        assert second["components"]["text"] == "duplicate"
        assert second["text_id"] == first["text_id"]
        assert s.execute(
            select(func.count()).select_from(Record)
        ).scalar_one() == 1


def test_ingest_conflict_same_key_different_payload(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        ingest_message_envelope(s, settings, _message(
            account.connector_account_id))
        with pytest.raises(InboxConflict):
            ingest_message_envelope(
                s, settings,
                _message(account.connector_account_id, raw_text="tampered"),
            )


def test_ingest_media_component_imports_asset(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        key, size = _media_file(settings, account.connector_account_id)
        payload = _message(
            account.connector_account_id,
            attachments=[{
                "attachment_index": 0,
                "media_object_key": key,
                "mime_type": "image/jpeg",
                "size_bytes": size,
            }],
        )
        result = ingest_message_envelope(s, settings, payload)
        assert result["components"]["media"][0]["status"] == "imported"
        asset = s.get(MediaAsset, result["media_ids"][0])
        assert asset is not None
        assert asset.rel_path == f"media/{key}"
        # Duplicate replay -> duplicate status, same id.
        replay = ingest_message_envelope(s, settings, payload)
        assert replay["components"]["media"][0]["status"] == "duplicate"
        assert result["media_ids"][0] in replay["media_ids"]


def test_ingest_media_conflict_on_different_payload(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        key, size = _media_file(settings, account.connector_account_id)
        _, size2 = _media_file(settings, account.connector_account_id,
                               "f2.jpg", b"\xff\xd8\xff\xe1" + b"\x01" * 40)
        ingest_message_envelope(s, settings, _message(
            account.connector_account_id,
            attachments=[{"attachment_index": 0, "media_object_key": key,
                          "mime_type": "image/jpeg", "size_bytes": size}]))
        with pytest.raises(InboxConflict):
            ingest_message_envelope(s, settings, _message(
                account.connector_account_id,
                attachments=[{"attachment_index": 0,
                              "media_object_key": f"{account.connector_account_id}/f2.jpg",
                              "mime_type": "image/jpeg",
                              "size_bytes": size2}]))


def test_ingest_ignored_without_consent(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _conv_source(s, account)
        result = ingest_message_envelope(s, settings, _message(
            account.connector_account_id))
        assert result["ignored"] is True
        assert result["components"]["text"] == "ignored"
        assert s.execute(
            select(func.count()).select_from(Record)
        ).scalar_one() == 0


def test_ingest_ignored_when_policy_unacked(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account, acked=None)  # desired set, never acked
        s.execute(
            sa.text(
                "UPDATE connector_accounts SET policy_acked_version = 0"
            )
        )
        result = ingest_message_envelope(s, settings, _message(
            account.connector_account_id))
        assert result["ignored"] is True


def test_ingest_ignored_when_source_disabled(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account, enabled=0, acked=0)
        result = ingest_message_envelope(s, settings, _message(
            account.connector_account_id))
        assert result["ignored"] is True


def test_ingest_stranger_blocked(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account, source_type="stranger")
        result = ingest_message_envelope(s, settings, _message(
            account.connector_account_id, source_type="stranger"))
        assert result["ignored"] is True


def test_ingest_my_documents_blocked_until_verified(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account, source_type="my_documents")
        result = ingest_message_envelope(s, settings, _message(
            account.connector_account_id, source_type="my_documents"))
        assert result["ignored"] is True
        assert engine.MY_DOCUMENTS_REALTIME_VERIFIED is False


def test_ingest_media_only_no_text(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        key, size = _media_file(settings, account.connector_account_id)
        result = ingest_message_envelope(s, settings, _message(
            account.connector_account_id,
            raw_text=None,
            attachments=[{"attachment_index": 0, "media_object_key": key,
                          "mime_type": "image/jpeg", "size_bytes": size}]))
        assert result["components"]["text"] == "absent"
        assert result["components"]["media"][0]["status"] == "imported"


def test_media_rejects_bad_magic(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        key, size = _media_file(settings, account.connector_account_id,
                                "evil.jpg", b"not-a-jpeg")
        with pytest.raises(InboxValidationError, match="MIME"):
            ingest_message_envelope(s, settings, _message(
                account.connector_account_id,
                attachments=[{"attachment_index": 0,
                              "media_object_key": key,
                              "mime_type": "image/jpeg",
                              "size_bytes": size}]))


def test_media_rejects_size_mismatch(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        key, size = _media_file(settings, account.connector_account_id)
        with pytest.raises(InboxValidationError, match="Kích thước"):
            ingest_message_envelope(s, settings, _message(
                account.connector_account_id,
                attachments=[{"attachment_index": 0,
                              "media_object_key": key,
                              "mime_type": "image/jpeg",
                              "size_bytes": size + 1}]))


def test_media_rejects_path_escape(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        with pytest.raises(InboxValidationError, match="ngoài storage"):
            resolve_media_object(
                Path(settings.runtime_root) / "media",
                account.connector_account_id,
                "../outside.jpg",
                "image/jpeg",
                10,
            )
        # Key under a different account's prefix is also rejected.
        with pytest.raises(InboxValidationError):
            resolve_media_object(
                Path(settings.runtime_root) / "media",
                account.connector_account_id,
                "other-account/f.jpg",
                "image/jpeg",
                10,
            )


def test_media_rejects_unsupported_mime(env):
    _, eng = env
    with pytest.raises(InboxValidationError, match="không được hỗ trợ"):
        resolve_media_object(Path("x"), "a", "a/f.gif", "image/gif", 1)


def test_message_envelope_validation(env):
    settings, eng = env
    with session_scope(eng) as s:
        account = _account(s)
        _consented_ready(s, account)
        _conv_source(s, account)
        with pytest.raises(InboxValidationError):
            ingest_message_envelope(
                s, settings, _message(account.connector_account_id,
                                      schema_version=2))
        with pytest.raises(InboxValidationError):
            ingest_message_envelope(
                s, settings, _message(account.connector_account_id,
                                      msg_id=None))
        with pytest.raises(InboxValidationError):
            ingest_message_envelope(
                s, settings, _message(account.connector_account_id,
                                      attachments="not-a-list"))


def test_unknown_account_rejected(env):
    settings, eng = env
    with session_scope(eng) as s:
        with pytest.raises(InboxValidationError, match="onboard"):
            ingest_message_envelope(s, settings, _message("nobody"))

"""MIN-103 slice B — connector API tests ported from
notary_v2 tests/test_zalo_inbox_api.py.

Covers: onboard bootstrap auth, webhook signature + replay window, signed
config, derived-key commands auth, error envelope shape, consent/policy/data-
sync endpoints, media content, ops state, and connector process lifecycle
(mocked Popen + gap recording).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import subprocess
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from zalo_module.app import create_app
from zalo_module.database import get_engine, init_db, session_scope
from zalo_module import connector_proc as proc
from zalo_module.intake.engine import _iso, utcnow
from zalo_module.intake.security import command_secret, sign_body
from zalo_module.models import ConnectorAccount, ConvSource
from zalo_module.settings import Settings

UTC = timezone.utc
WEBHOOK_SECRET = "api-test-webhook"
BOOTSTRAP_SECRET = "api-test-bootstrap"


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
        webhook_secret=WEBHOOK_SECRET,
        bootstrap_secret=BOOTSTRAP_SECRET,
    )
    kwargs.update(overrides)
    return Settings(**kwargs)


@pytest.fixture()
def env(tmp_path):
    runtime = tmp_path / "runtime"
    (runtime / "media").mkdir(parents=True)
    settings = _settings(runtime)
    app = create_app(settings)
    with TestClient(app) as client:
        yield settings, app.state.engine, client
    app.state.engine.dispose()


@pytest.fixture(autouse=True)
def _no_real_process():
    """Ensure the connector process globals are reset around each test."""
    proc.terminate_connector_process()
    yield
    proc.terminate_connector_process()


def _ts() -> str:
    return str(int(time.time()))


def _event_headers(body: bytes, secret: str = WEBHOOK_SECRET,
                   timestamp: str | None = None) -> dict:
    ts = timestamp or _ts()
    return {
        "x-zalo-timestamp": ts,
        "x-zalo-signature": sign_body(body, ts, secret),
    }


def _post_event(client: TestClient, payload: dict, **kw):
    body = json.dumps(payload).encode()
    return client.post(
        "/connector/v1/events", content=body, headers=_event_headers(body, **kw)
    )


def _account_id(client: TestClient) -> str:
    resp = client.post(
        "/connector/v1/connectors/onboard",
        headers={"x-zalo-bootstrap": BOOTSTRAP_SECRET},
    )
    assert resp.status_code == 200
    return resp.json()["connector_account_id"]


def _discovery(account_id: str, **kw) -> dict:
    payload = {
        "schema_version": 1,
        "event_type": "discovery",
        "connector_account_id": account_id,
        "conversation_id": "c1",
        "conversation_type": "user",
        "source_type": "friend",
        "source_display_name": "Alice",
    }
    payload.update(kw)
    return payload


def _ready_pair(client: TestClient, eng) -> str:
    """Onboard + discovery + consent + policy ack via the real wire flow."""
    account_id = _account_id(client)
    resp = _post_event(client, _discovery(account_id))
    assert resp.status_code == 200, resp.text
    resp = client.post(f"/connector/v1/connectors/{account_id}/consent")
    assert resp.status_code == 200, resp.text
    version = resp.json()["policy_version"]
    ack = {
        "schema_version": 1,
        "event_type": "policy_ack",
        "connector_account_id": account_id,
        "policy_version": version,
    }
    resp = _post_event(client, ack)
    assert resp.status_code == 200, resp.text
    # Connect the account (usable + fresh last_seen).
    state = {
        "schema_version": 1,
        "event_type": "state",
        "connector_account_id": account_id,
        "state": "connected",
        "listener_generation": 1,
        "observed_at": _iso(utcnow()),
        "bound_zalo_id": "z1",
        "qr_login_success": True,
    }
    resp = _post_event(client, state)
    assert resp.status_code == 200, resp.text
    return account_id


# --- onboard --------------------------------------------------------------------


def test_onboard_creates_and_reuses_single_account(env):
    _, eng, client = env
    account_id = _account_id(client)
    assert uuid.UUID(account_id)
    assert _account_id(client) == account_id
    with session_scope(eng) as s:
        assert len(s.execute(select(ConnectorAccount)).scalars().all()) == 1


def test_onboard_rejects_wrong_secret(env):
    _, _, client = env
    resp = client.post(
        "/connector/v1/connectors/onboard",
        headers={"x-zalo-bootstrap": "wrong"},
    )
    assert resp.status_code == 403  # parity: legacy HTTPException(403)
    body = resp.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}


def test_onboard_rejects_missing_secret(env):
    _, _, client = env
    resp = client.post("/connector/v1/connectors/onboard")
    assert resp.status_code == 403


def test_onboard_rejects_when_secret_unconfigured(tmp_path):
    runtime = tmp_path / "runtime"
    (runtime / "media").mkdir(parents=True)
    settings = _settings(runtime, bootstrap_secret=None)
    app = create_app(settings)
    with TestClient(app) as client:
        resp = client.post(
            "/connector/v1/connectors/onboard",
            headers={"x-zalo-bootstrap": "anything"},
        )
        assert resp.status_code == 403
    app.state.engine.dispose()


# --- webhook signature ------------------------------------------------------------


def test_events_reject_bad_signature(env):
    _, _, client = env
    account_id = _account_id(client)
    body = json.dumps(_discovery(account_id)).encode()
    resp = client.post(
        "/connector/v1/events",
        content=body,
        headers={"x-zalo-timestamp": _ts(), "x-zalo-signature": "0" * 64},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_failed"


def test_events_reject_stale_timestamp(env):
    _, _, client = env
    account_id = _account_id(client)
    body = json.dumps(_discovery(account_id)).encode()
    old = str(int(time.time()) - 400)
    resp = client.post(
        "/connector/v1/events",
        content=body,
        headers={
            "x-zalo-timestamp": old,
            "x-zalo-signature": sign_body(body, old, WEBHOOK_SECRET),
        },
    )
    assert resp.status_code == 400


def test_events_reject_invalid_timestamp(env):
    _, _, client = env
    account_id = _account_id(client)
    body = json.dumps(_discovery(account_id)).encode()
    resp = client.post(
        "/connector/v1/events",
        content=body,
        headers={
            "x-zalo-timestamp": "not-a-number",
            "x-zalo-signature": sign_body(body, "not-a-number", WEBHOOK_SECRET),
        },
    )
    assert resp.status_code == 400


def test_events_reject_malformed_json(env):
    _, _, client = env
    body = b'{"schema_version":1,"schema_version":1}'  # dup keys
    resp = client.post(
        "/connector/v1/events", content=body, headers=_event_headers(body)
    )
    assert resp.status_code == 400


def test_events_discovery_ack(env):
    _, _, client = env
    account_id = _account_id(client)
    resp = _post_event(client, _discovery(account_id))
    assert resp.status_code == 200
    assert resp.json()["ack"] is True
    # Legacy ACK shape: a single ``id`` key (routers/zalo_inbox.py:426).
    assert uuid.UUID(resp.json()["id"])


def test_events_message_ack_components(env):
    _, _, client = env
    account_id = _ready_pair(client, env[1])
    message = {
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
        "raw_text": "hi",
    }
    resp = _post_event(client, message)
    assert resp.status_code == 200
    body = resp.json()
    assert body == {
        "ack": True,
        "components": {"text": "imported", "media": []},
    }


def test_events_policy_ack(env):
    _, _, client = env
    account_id = _account_id(client)
    resp = client.post(f"/connector/v1/connectors/{account_id}/consent")
    version = resp.json()["policy_version"]
    resp = _post_event(
        client,
        {
            "schema_version": 1,
            "event_type": "policy_ack",
            "connector_account_id": account_id,
            "policy_version": version,
        },
    )
    assert resp.status_code == 200


def test_events_unknown_account_400(env):
    _, _, client = env
    _account_id(client)
    resp = _post_event(client, _discovery(str(uuid.uuid4())))
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_failed"


def test_events_source_event_ack_and_replay(env):
    """Connector ``source_event`` (undo/reaction) ACKs with the produced
    record id; identical replay ACKs the same id without a second record."""
    _, eng, client = env
    account_id = _account_id(client)
    event = {
        "schema_version": 1,
        "event_type": "source_event",
        "connector_account_id": account_id,
        "conversation_id": "c1",
        "conversation_type": "user",
        "event_subtype": "reaction",
        "target_provider_message_id": "g-1",
        "target_client_message_id": "c-1",
        "reaction_icon": ":>",
        "observed_at": _iso(utcnow()),
        "sender_id": "u1",
    }
    resp = _post_event(client, event)
    assert resp.status_code == 200, resp.text
    assert resp.json()["ack"] is True
    record_id = resp.json()["id"]
    assert uuid.UUID(record_id)

    replay = _post_event(client, event)
    assert replay.status_code == 200
    assert replay.json()["id"] == record_id

    # Malformed (reaction missing icon) is a 400 — the outbox quarantines it.
    bad = dict(event)
    bad.pop("reaction_icon")
    bad["target_provider_message_id"] = "g-2"
    resp = _post_event(client, bad)
    assert resp.status_code == 400


# --- config / commands auth --------------------------------------------------------


def test_config_requires_signed_empty_body(env):
    _, eng, client = env
    account_id = _account_id(client)
    ts = _ts()
    resp = client.get(
        f"/connector/v1/connectors/{account_id}/config",
        headers={
            "x-zalo-timestamp": ts,
            "x-zalo-signature": sign_body(b"", ts, WEBHOOK_SECRET),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["listener_generation"] == 0
    assert body["policy_version"] == 0
    assert body["sources"] == []
    assert body["protected_media_object_keys"] == []


def test_config_rejects_unsigned(env):
    _, _, client = env
    account_id = _account_id(client)
    resp = client.get(f"/connector/v1/connectors/{account_id}/config")
    assert resp.status_code == 400


def test_config_unknown_account(env):
    _, _, client = env
    _account_id(client)
    ts = _ts()
    resp = client.get(
        f"/connector/v1/connectors/{uuid.uuid4()}/config",
        headers={
            "x-zalo-timestamp": ts,
            "x-zalo-signature": sign_body(b"", ts, WEBHOOK_SECRET),
        },
    )
    assert resp.status_code == 404


def test_config_sources_emit_desired_acked_bools(env):
    """C1 regression: the connector filters ``acked_enabled === true`` —
    config ``sources[]`` must carry real JSON booleans, never 0/1."""
    _, eng, client = env
    account_id = _ready_pair(client, eng)  # enabled + acked source
    ts = _ts()
    resp = client.get(
        f"/connector/v1/connectors/{account_id}/config",
        headers={
            "x-zalo-timestamp": ts,
            "x-zalo-signature": sign_body(b"", ts, WEBHOOK_SECRET),
        },
    )
    assert resp.status_code == 200
    sources = resp.json()["sources"]
    assert len(sources) == 1
    source = sources[0]
    for key in ("enabled", "desired_enabled", "acked_enabled"):
        assert key in source
        assert isinstance(source[key], bool), key
    assert source["enabled"] is True
    assert source["desired_enabled"] is True
    assert source["acked_enabled"] is True


def test_commands_require_derived_key(env):
    _, eng, client = env
    account_id = _account_id(client)
    ts = _ts()
    # Raw webhook secret must NOT authenticate commands/next.
    resp = client.get(
        f"/connector/v1/connectors/{account_id}/commands/next",
        headers={
            "x-zalo-timestamp": ts,
            "x-zalo-signature": sign_body(b"", ts, WEBHOOK_SECRET),
        },
    )
    assert resp.status_code == 400
    # Derived key works and there is no command -> 204.
    derived = command_secret(WEBHOOK_SECRET, account_id)
    resp = client.get(
        f"/connector/v1/connectors/{account_id}/commands/next",
        headers={
            "x-zalo-timestamp": ts,
            "x-zalo-signature": sign_body(b"", ts, derived),
        },
    )
    assert resp.status_code == 204


def test_commands_next_unknown_account_404(env):
    """Unknown-but-validly-signed account → 404 (legacy :513-514), not 204."""
    _, _, client = env
    _account_id(client)
    ghost = str(uuid.uuid4())
    derived = command_secret(WEBHOOK_SECRET, ghost)
    ts = _ts()
    resp = client.get(
        f"/connector/v1/connectors/{ghost}/commands/next",
        headers={
            "x-zalo-timestamp": ts,
            "x-zalo-signature": sign_body(b"", ts, derived),
        },
    )
    assert resp.status_code == 404


def test_commands_returns_data_sync(env):
    _, eng, client = env
    account_id = _ready_pair(client, eng)
    resp = client.post(f"/connector/v1/connectors/{account_id}/data-sync")
    assert resp.status_code == 200, resp.text
    # Legacy data-sync response shape (routers/zalo_inbox.py:541).
    body = resp.json()
    assert set(body) == {"run_id", "status"}
    assert uuid.UUID(body["run_id"])
    assert body["status"] == "running"
    derived = command_secret(WEBHOOK_SECRET, account_id)
    ts = _ts()
    resp = client.get(
        f"/connector/v1/connectors/{account_id}/commands/next",
        headers={
            "x-zalo-timestamp": ts,
            "x-zalo-signature": sign_body(b"", ts, derived),
        },
    )
    assert resp.status_code == 200
    assert resp.json()["command_type"] == "data_sync"


# --- mutations / misc endpoints -----------------------------------------------------


def test_consent_and_patch_source(env):
    _, eng, client = env
    account_id = _account_id(client)
    _post_event(client, _discovery(account_id))
    resp = client.post(f"/connector/v1/connectors/{account_id}/consent")
    assert resp.status_code == 200
    assert resp.json()["policy_version"] == 1
    with session_scope(eng) as s:
        source = s.execute(select(ConvSource)).scalar_one()
        source_id = source.conv_source_id
    resp = client.patch(
        f"/connector/v1/sources/{source_id}",
        json={"enabled": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    # Legacy PATCH shape: the source snapshot (routers/zalo_inbox.py:702).
    assert body == {
        "id": source_id,
        "enabled": False,
        "desired_enabled": False,
        "acked_enabled": None,  # no policy_ack yet in this flow
        "pending": True,
    }


def test_patch_source_validation(env):
    _, _, client = env
    account_id = _account_id(client)
    _post_event(client, _discovery(account_id))
    resp = client.patch("/connector/v1/sources/missing", json={"enabled": True})
    assert resp.status_code == 400
    with session_scope(env[1]) as s:
        source = s.execute(select(ConvSource)).scalar_one()
        resp = client.patch(
            f"/connector/v1/sources/{source.conv_source_id}",
            json={"enabled": "yes"},
        )
        assert resp.status_code == 400


def test_data_sync_conflict_maps_409(env):
    _, eng, client = env
    account_id = _account_id(client)
    # No consent/connection -> 409 or 400, never a bare 500.
    resp = client.post(f"/connector/v1/connectors/{account_id}/data-sync")
    assert resp.status_code in (400, 409)
    assert resp.json()["error"]["code"] in (
        "validation_failed",
        "conflict",
    )


def test_sources_refresh(env):
    _, _, client = env
    account_id = _account_id(client)
    resp = client.post(
        f"/connector/v1/connectors/{account_id}/sources/refresh"
    )
    assert resp.status_code == 200
    assert resp.json()["source_sync_request_version"] == 1


def test_state_shape_excludes_batch_fields(env):
    _, eng, client = env
    account_id = _ready_pair(client, eng)
    resp = client.get("/connector/v1/state")
    assert resp.status_code == 200
    body = resp.json()
    assert {
        "connector", "policy", "sources", "data_sync", "connector_error",
    } <= set(body)
    # MIN-94 additive blocks: gaps, internal job-queue metrics, media usage
    # and advisory warnings.
    assert {
        "gaps", "queue", "media", "warnings",
    } <= set(body)
    assert body["connector"]["state"] == "connected"
    assert body["connector"]["bound_zalo_id"] == "z1"
    assert body["policy"]["intake_consented"] is True
    assert len(body["sources"]) == 1
    assert body["media"]["quota_bytes"] > 0
    assert body["media"]["usage_bytes"] >= 0
    assert isinstance(body["queue"]["pending_jobs"], int)
    # No batch/media-grid consumer vocabulary leaked into the ops snapshot.
    for forbidden in ("batches", "media_grid", "exports"):
        assert forbidden not in body


def test_state_reports_listener_gap_and_warnings(env):
    """MIN-94: a disconnect report opens a gap + gap_open warning on /state;
    a stale heartbeat while 'usable' surfaces listener_heartbeat_stale."""
    _, eng, client = env
    account_id = _ready_pair(client, eng)
    resp = _post_event(
        client,
        {
            "schema_version": 1,
            "event_type": "state",
            "connector_account_id": account_id,
            "state": "disconnected",
            "listener_generation": 1,
            "observed_at": _iso(utcnow()),
        },
    )
    assert resp.status_code == 200, resp.text
    body = client.get("/connector/v1/state").json()
    assert body["connector"]["state"] == "disconnected"
    open_gaps = [g for g in body["gaps"] if g["ongoing"]]
    assert len(open_gaps) == 1
    assert open_gaps[0]["ended_at"] is None
    assert {w["code"] for w in body["warnings"]} == {"gap_open"}

    # Reconnect closes the gap (still present as a closed interval).
    resp = _post_event(
        client,
        {
            "schema_version": 1,
            "event_type": "state",
            "connector_account_id": account_id,
            "state": "connected",
            "listener_generation": 1,
            "observed_at": _iso(utcnow()),
        },
    )
    assert resp.status_code == 200, resp.text
    body = client.get("/connector/v1/state").json()
    assert not any(g["ongoing"] for g in body["gaps"])
    assert "gap_open" not in {w["code"] for w in body["warnings"]}

    # Stale heartbeat while marked usable → heartbeat-stale warning.
    with session_scope(eng) as s:
        account = s.get(ConnectorAccount, account_id)
        account.last_seen_at = _iso(utcnow() - timedelta(seconds=120))
    body = client.get("/connector/v1/state").json()
    assert body["connector"]["state"] == "disconnected"
    assert "listener_heartbeat_stale" in {
        w["code"] for w in body["warnings"]
    }


# --- I7: consumer bearer on ops/mutation routes -----------------------------------


@pytest.fixture()
def env_token(tmp_path):
    """Same app but with ``api_token`` configured → ops/mutation routes
    require ``Authorization: Bearer`` (I7 defense-in-depth)."""
    runtime = tmp_path / "runtime"
    (runtime / "media").mkdir(parents=True)
    settings = _settings(runtime, api_token="ops-token-1")
    app = create_app(settings)
    with TestClient(app) as client:
        yield settings, app.state.engine, client
    app.state.engine.dispose()


def test_ops_routes_require_bearer_when_token_set(env_token):
    _, eng, client = env_token
    account_id = _account_id(client)  # onboard stays bootstrap-only, no Bearer
    _post_event(client, _discovery(account_id))
    with session_scope(eng) as s:
        source_id = s.execute(select(ConvSource)).scalar_one().conv_source_id

    guarded = [
        ("GET", "/connector/v1/state"),
        ("GET", f"/connector/v1/media/{uuid.uuid4()}/content"),
        ("POST", f"/connector/v1/connectors/{account_id}/consent"),
        ("POST", f"/connector/v1/connectors/{account_id}/sources/refresh"),
        ("POST", f"/connector/v1/connectors/{account_id}/data-sync"),
        ("PATCH", f"/connector/v1/sources/{source_id}"),
        ("POST", "/connector/v1/connectors/start"),
    ]
    for method, url in guarded:
        resp = client.request(method, url, json={"enabled": True})
        assert resp.status_code == 401, f"{method} {url} → {resp.status_code}"
        payload = resp.json()
        # IntakeRoute envelope — auth failures are intake.error.v1 401s.
        assert payload["schema_version"] == "intake.error.v1"
        assert payload["error"]["code"] == "unauthorized"
        resp = client.request(
            method, url, json={"enabled": True},
            headers={"Authorization": "Bearer wrong"},
        )
        assert resp.status_code == 401


def test_ops_routes_accept_correct_bearer(env_token):
    _, eng, client = env_token
    account_id = _account_id(client)
    auth = {"Authorization": "Bearer ops-token-1"}
    resp = client.get("/connector/v1/state", headers=auth)
    assert resp.status_code == 200
    resp = client.post(
        f"/connector/v1/connectors/{account_id}/consent", headers=auth
    )
    assert resp.status_code == 200
    assert resp.json()["policy_version"] == 1
    resp = client.post(
        f"/connector/v1/connectors/{account_id}/sources/refresh", headers=auth
    )
    assert resp.status_code == 200


def test_signed_and_bootstrap_routes_unaffected_by_token(env_token):
    """Events/config keep HMAC auth; onboard keeps the bootstrap secret —
    the consumer Bearer token does not apply to them."""
    _, _, client = env_token
    # onboard: no Bearer needed, bootstrap secret still checked
    account_id = _account_id(client)
    # events: HMAC signature, no Bearer
    resp = _post_event(client, _discovery(account_id))
    assert resp.status_code == 200
    ts = _ts()
    resp = client.get(
        f"/connector/v1/connectors/{account_id}/config",
        headers={
            "x-zalo-timestamp": ts,
            "x-zalo-signature": sign_body(b"", ts, WEBHOOK_SECRET),
        },
    )
    assert resp.status_code == 200


def test_events_malformed_int_fields_400_not_500(env):
    """M6: raw ``int()`` casts on payload fields raise TypeError/ValueError
    in the engine — the API must answer 400 ``validation_failed``, never 500."""
    _, eng, client = env
    account_id = _ready_pair(client, eng)
    resp = _post_event(
        client,
        {
            "schema_version": 1,
            "event_type": "state",
            "connector_account_id": account_id,
            "state": "connected",
            "listener_generation": "not-an-int",  # int() cast → ValueError
            "observed_at": _iso(utcnow()),
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_failed"


def test_media_content_serves_file(env):
    settings, eng, client = env
    account_id = _ready_pair(client, eng)
    # Drop a media file under media/<account>/ and register via ingest.
    key = f"{account_id}/pic.png"
    path = Path(settings.runtime_root) / "media" / key
    path.parent.mkdir(parents=True, exist_ok=True)
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
    path.write_bytes(content)
    message = {
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
        "attachments": [{
            "attachment_index": 0,
            "media_object_key": key,
            "mime_type": "image/png",
            "size_bytes": len(content),
        }],
    }
    resp = _post_event(client, message)
    assert resp.status_code == 200, resp.text
    with session_scope(eng) as s:
        from zalo_module.models import MediaAsset

        asset = s.execute(select(MediaAsset)).scalar_one()
        resp = client.get(f"/connector/v1/media/{asset.attachment_id}/content")
        assert resp.status_code == 200
        assert resp.content == content
        assert resp.headers["content-type"].startswith("image/png")


def test_media_content_not_found(env):
    _, _, client = env
    _account_id(client)
    resp = client.get(f"/connector/v1/media/{uuid.uuid4()}/content")
    assert resp.status_code == 404


# --- connector process lifecycle (mocked Popen) ---------------------------------------


class _FakeProc:
    """Minimal Popen double: running until ``exit_code`` is set."""

    def __init__(self):
        self.args = None
        self.kwargs = None
        self._exit = None
        self.terminated = False
        self.killed = False
        self._waiters: list[threading.Event] = []

    def poll(self):
        return self._exit

    def wait(self, timeout=None):
        deadline = None if timeout is None else time.monotonic() + timeout
        while self._exit is None:
            if deadline is not None and time.monotonic() > deadline:
                raise subprocess.TimeoutExpired("node", timeout)
            time.sleep(0.005)
        return self._exit

    def terminate(self):
        self.terminated = True
        self._exit = 0

    def kill(self):
        self.killed = True
        self._exit = -9

    def exit(self, code: int):
        self._exit = code


def test_connectors_start_spawns_with_whitelist_env(env):
    settings, eng, client = env
    account_id = _account_id(client)
    fake = _FakeProc()
    captured: dict = {}

    def _popen(args, **kw):
        captured["args"] = args
        captured.update(kw)
        return fake

    entrypoint = Path(settings.runtime_root) / "run.mjs"
    entrypoint.write_text("// stub", encoding="utf-8")
    with patch.object(proc, "_connector_entrypoint", return_value=entrypoint), \
         patch.object(proc.subprocess, "Popen", side_effect=_popen):
        resp = client.post("/connector/v1/connectors/start", json={})
        assert resp.status_code == 200
        assert resp.json() == {"status": "starting"}
        # Idempotent while running.
        resp = client.post("/connector/v1/connectors/start", json={})
        assert resp.json() == {"status": "running"}
        # force_restart spawns a new child.
        fake2 = _FakeProc()
        def _popen2(args, **kw):
            return fake2
        with patch.object(proc.subprocess, "Popen", side_effect=_popen2):
            resp = client.post(
                "/connector/v1/connectors/start",
                json={"force_restart": True},
            )
            assert resp.json() == {"status": "starting"}
            assert fake.terminated is True

    args = captured["args"]
    assert args[0] == "node" and args[1].endswith("run.mjs")
    child_env = captured["env"]
    assert child_env["ZALO_INBOX_BACKEND_URL"] == "http://127.0.0.1:8790"
    assert child_env["ZALO_INBOX_BOOTSTRAP_SECRET"] == BOOTSTRAP_SECRET
    assert child_env["ZALO_INBOX_WEBHOOK_SECRET"] == WEBHOOK_SECRET
    assert child_env["ZALO_CONNECTOR_STATE_ROOT"] == str(
        Path(settings.connector_state_root).resolve()
    )
    assert child_env["ZALO_INBOX_STORAGE_ROOT"] == str(
        (Path(settings.runtime_root) / "media").resolve()
    )
    assert child_env["ZALO_CONNECTOR_PARENT_PID"] == str(__import__("os").getpid())
    # Whitelist: no ambient secrets leak.
    for key in child_env:
        assert key in {
            "PATH", "Path", "SYSTEMROOT", "SystemRoot", "TEMP", "TMP",
            "ZALO_INBOX_BACKEND_URL", "ZALO_INBOX_BOOTSTRAP_SECRET",
            "ZALO_INBOX_WEBHOOK_SECRET", "ZALO_INBOX_STORAGE_ROOT",
            "ZALO_CONNECTOR_QUOTA_BYTES", "ZALO_CONNECTOR_RETENTION_HOURS",
            "ZALO_CONNECTOR_PARENT_PID", "ZALO_CONNECTOR_STATE_ROOT",
            "ZALO_CONNECTOR_FORCE_QR",
        }


def test_connectors_start_missing_entrypoint_503(env):
    settings, eng, client = env
    _account_id(client)
    missing = Path(settings.runtime_root) / "nope" / "run.mjs"
    with patch.object(proc, "_connector_entrypoint", return_value=missing):
        resp = client.post("/connector/v1/connectors/start", json={})
        assert resp.status_code == 503
        assert resp.json()["error"]["code"] == "service_unavailable"


def test_connectors_start_missing_secrets_503(tmp_path):
    runtime = tmp_path / "runtime"
    (runtime / "media").mkdir(parents=True)
    settings = _settings(runtime, webhook_secret=None)
    app = create_app(settings)
    with TestClient(app) as client:
        resp = client.post("/connector/v1/connectors/start", json={})
        assert resp.status_code == 503
    app.state.engine.dispose()


def test_watcher_records_gap_on_exit(env):
    settings, eng, client = env
    account_id = _ready_pair(client, eng)  # session_state = usable
    fake = _FakeProc()
    entrypoint = Path(settings.runtime_root) / "run.mjs"
    entrypoint.write_text("// stub", encoding="utf-8")
    with patch.object(proc, "_connector_entrypoint", return_value=entrypoint), \
         patch.object(proc.subprocess, "Popen", return_value=fake):
        resp = client.post("/connector/v1/connectors/start", json={})
        assert resp.status_code == 200
        fake.exit(1)  # child dies
        for _ in range(100):
            with session_scope(eng) as s:
                account = s.get(ConnectorAccount, account_id)
                if account.gap_started_at is not None:
                    break
            time.sleep(0.02)
        with session_scope(eng) as s:
            account = s.get(ConnectorAccount, account_id)
            assert account.gap_started_at is not None
        resp = client.get("/connector/v1/state")
        assert resp.json()["connector_error"] == proc.CONNECTOR_STOPPED_MESSAGE


def test_terminate_kills_on_timeout():
    fake = _FakeProc()
    fake.wait = MagicMock(side_effect=subprocess.TimeoutExpired("node", 3))
    proc._connector_process = fake
    proc.terminate_connector_process()
    assert fake.terminated and fake.killed
    assert proc._connector_process is None

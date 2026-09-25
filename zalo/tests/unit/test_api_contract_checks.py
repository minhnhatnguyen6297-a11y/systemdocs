"""Contract-check tests for slice-D API (fix round 1).

Covers:
- receipt_count_mismatch → HTTP 409 (finding 1)
- same receipt_id + different body → validation error, not replay (finding 1)
- strict JSON profile on POST bodies: BOM / NaN / duplicate keys → json_invalid
  (finding 2)
- unregistered consumer (settings.consumer_id None) → unauthorized on
  POST /ocr-requests (finding 3)

Uses the real FastAPI app wiring (``init_db`` schema) + TestClient — the same
path `cli serve` exposes over HTTP.
"""

import hashlib
import json
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from zalo_module.api.intake import router as intake_router
from zalo_module.api.ocr_requests import router as ocr_router
from zalo_module.database import get_engine, init_db, session_scope
from zalo_module.delivery.package import build_package
from zalo_module.settings import get_settings

CONSUMER_ID = "c0000000-0000-4000-8000-000000000001"


def _record() -> dict:
    return {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "message_text",
        "record_id": str(uuid.uuid4()),
        "logical_id": str(uuid.uuid4()),
        "revision": 1,
        "captured_at": "2026-09-25T01:00:00+00:00",
        "recorded_at": "2026-09-25T01:00:01+00:00",
        "source": {
            "provider": "zalo_personal",
            "account_id": "a0000000-0000-4000-8000-000000000099",
            "conversation_id": "syn-thread-1",
            "conversation_type": "user",
        },
        "message": {"text": "x"},
    }


def _app(tmp_path, consumer_id=CONSUMER_ID):
    env = {"ZALO_INTAKE_RUNTIME_DIR": str(tmp_path)}
    if consumer_id is not None:
        env["ZALO_INTAKE_CONSUMER_ID"] = consumer_id
    settings = get_settings(env)
    engine = get_engine(settings)
    init_db(engine)
    app = FastAPI()
    app.state.settings = settings
    app.state.engine = engine
    app.include_router(intake_router)
    app.include_router(ocr_router)
    return app, settings, engine


def _package(settings, engine, n_records=2):
    with session_scope(engine) as session:
        pid = build_package(
            [_record() for _ in range(n_records)],
            settings.consumer_id,
            settings,
            session,
        )
    manifest_bytes = (
        settings.runtime_root / "packages" / pid / "manifest.json"
    ).read_bytes()
    return pid, hashlib.sha256(manifest_bytes).hexdigest()


def _receipt(pid, sha, **overrides):
    r = {
        "schema_version": "intake.receipt.v1",
        "receipt_id": str(uuid.uuid4()),
        "package_id": pid,
        "consumer_id": CONSUMER_ID,
        "status": "accepted",
        "received_at": "2026-09-25T02:00:00+00:00",
        "manifest_sha256": sha,
        "record_count": 2,
    }
    r.update(overrides)
    return r


def test_receipt_count_mismatch(tmp_path):
    app, settings, engine = _app(tmp_path)
    pid, sha = _package(settings, engine)
    client = TestClient(app)
    resp = client.post(
        "/intake/v1/receipts",
        content=json.dumps(_receipt(pid, sha, record_count=99)),
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "receipt_count_mismatch"
    assert resp.json()["schema_version"] == "intake.error.v1"


def test_receipt_same_id_different_body_is_not_replay(tmp_path):
    app, settings, engine = _app(tmp_path)
    pid, sha = _package(settings, engine)
    client = TestClient(app)
    receipt_id = str(uuid.uuid4())

    ok = client.post(
        "/intake/v1/receipts",
        content=json.dumps(_receipt(pid, sha, receipt_id=receipt_id)),
    )
    assert ok.status_code == 200

    # Byte-identical replay → stored decision returned, still 200.
    replay = client.post(
        "/intake/v1/receipts",
        content=json.dumps(_receipt(pid, sha, receipt_id=receipt_id)),
    )
    assert replay.status_code == 200
    assert replay.json()["receipt_id"] == receipt_id

    # Same receipt_id but different manifest hash → package_conflict, not a
    # replay (I1: stored decisions are immutable; id reuse with different
    # contents is always a conflict, never a re-validation).
    bad = client.post(
        "/intake/v1/receipts",
        content=json.dumps(
            _receipt(pid, sha, receipt_id=receipt_id, manifest_sha256="0" * 64)
        ),
    )
    assert bad.status_code == 409
    assert bad.json()["error"]["code"] == "package_conflict"

    # Same receipt_id but different record count → package_conflict too.
    bad2 = client.post(
        "/intake/v1/receipts",
        content=json.dumps(
            _receipt(pid, sha, receipt_id=receipt_id, record_count=5)
        ),
    )
    assert bad2.status_code == 409
    assert bad2.json()["error"]["code"] == "package_conflict"


@pytest.mark.parametrize(
    "body",
    [
        b'\xef\xbb\xbf{"schema_version":"intake.receipt.v1"}',  # UTF-8 BOM
        b'{"schema_version":"intake.receipt.v1","x":NaN}',       # NaN literal
        b'{"a":1,"a":2}',                                        # duplicate key
        b'{"schema_version":"intake.receipt.v1","x":Infinity}',  # Infinity
    ],
    ids=["bom", "nan", "dup-key", "infinity"],
)
def test_strict_json_profile_receipts(tmp_path, body):
    app, settings, engine = _app(tmp_path)
    client = TestClient(app)
    resp = client.post("/intake/v1/receipts", content=body)
    assert resp.status_code == 400
    payload = resp.json()
    assert payload["schema_version"] == "intake.error.v1"
    assert payload["error"]["code"] == "json_invalid"


def test_strict_json_profile_ocr_requests(tmp_path):
    app, settings, engine = _app(tmp_path)
    client = TestClient(app)
    resp = client.post(
        "/intake/v1/ocr-requests", content=b'{"a":1,"a":2}'
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "json_invalid"


def test_ocr_request_rejected_when_no_consumer_registered(tmp_path):
    # settings.consumer_id is None → fail closed: unauthorized, not accept-all.
    app, settings, engine = _app(tmp_path, consumer_id=None)
    client = TestClient(app)
    body = {
        "schema_version": "intake.ocr-request.v1",
        "request_id": str(uuid.uuid4()),
        "consumer_id": CONSUMER_ID,
        "logical_id": "20000000-0000-4000-8000-000000000002",
        "variant": "full_res",
        "reason_code": "other",
        "observed_revision": 1,
        "submitted_at": "2026-09-25T02:01:00+00:00",
    }
    resp = client.post("/intake/v1/ocr-requests", content=json.dumps(body))
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


def test_ocr_request_wrong_consumer_unauthorized(tmp_path):
    app, settings, engine = _app(tmp_path)  # consumer_id = CONSUMER_ID
    client = TestClient(app)
    body = {
        "schema_version": "intake.ocr-request.v1",
        "request_id": str(uuid.uuid4()),
        "consumer_id": "d0000000-0000-4000-8000-000000000001",  # not registered
        "logical_id": "20000000-0000-4000-8000-000000000002",
        "variant": "full_res",
        "reason_code": "other",
        "observed_revision": 1,
        "submitted_at": "2026-09-25T02:01:00+00:00",
    }
    resp = client.post("/intake/v1/ocr-requests", content=json.dumps(body))
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"

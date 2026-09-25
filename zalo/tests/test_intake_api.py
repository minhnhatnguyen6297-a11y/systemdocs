"""MIN-97 slice C — authenticated intake delivery + OCR-request APIs.

Covers decision-sheet §4 deliverables 2/5/6:

- Bearer auth on every ``/intake/v1/*`` endpoint except ``/status`` (401
  ``unauthorized`` envelope when ``settings.api_token`` is configured;
  loopback-as-auth when it is not).
- ``GET /packages`` sealed-only feed with stable high-water pagination that
  survives interleaved ACKs; byte-exact file re-serves via both contract and
  file-name paths; ``package_unknown`` on misses.
- Receipt idempotency/replay semantics and rejected receipts never removing
  the package from the pending feed.
- OCR-request pipeline: schema codes, forbidden-field scan, source/revision/
  expiry checks, dedupe, idempotent replay, and all three quotas — with
  persisted rejections so restart-replays return the stored decision.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from zalo_module.api.intake import router as intake_router
from zalo_module.api.ocr_requests import router as ocr_router
from zalo_module.database import get_engine, init_db, session_scope
from zalo_module.delivery.package import build_package
from zalo_module.delivery.record_check import forbidden_codes
from zalo_module.models import Job, OcrRequest, Package, Source
from zalo_module.settings import get_settings

CONSUMER_ID = "c0000000-0000-4000-8000-000000000001"
ACCOUNT_ID = "a0000000-0000-4000-8000-000000000099"
TOKEN = "test-bearer-token-1"


def _app(tmp_path, *, consumer_id=CONSUMER_ID, token=None):
    env = {"ZALO_INTAKE_RUNTIME_DIR": str(tmp_path)}
    if consumer_id is not None:
        env["ZALO_INTAKE_CONSUMER_ID"] = consumer_id
    if token is not None:
        env["ZALO_INTAKE_API_TOKEN"] = token
    settings = get_settings(env)
    engine = get_engine(settings)
    init_db(engine)
    app = FastAPI()
    app.state.settings = settings
    app.state.engine = engine
    app.include_router(intake_router)
    app.include_router(ocr_router)
    return app, settings, engine


def _record(kind="message_text", **overrides):
    r = {
        "schema_version": "intake.raw-record.v1",
        "record_kind": kind,
        "record_id": str(uuid.uuid4()),
        "logical_id": str(uuid.uuid4()),
        "revision": 1,
        "captured_at": "2026-09-25T01:00:00+00:00",
        "recorded_at": "2026-09-25T01:00:01+00:00",
        "source": {
            "provider": "zalo_personal",
            "account_id": ACCOUNT_ID,
            "conversation_id": "syn-thread-1",
            "conversation_type": "user",
        },
        "message": {"text": "x"},
    }
    r.update(overrides)
    return r


def _package(settings, engine, n_records=2, records=None):
    with session_scope(engine) as session:
        pid = build_package(
            records or [_record() for _ in range(n_records)],
            CONSUMER_ID,
            settings,
            session,
        )
    return pid


def _pkg_dir(settings, engine, pid):
    with session_scope(engine) as session:
        pkg = session.get(Package, pid)
        rel = pkg.dir_rel_path
    return settings.runtime_root / rel


def _receipt(pid, sha, count=2, **overrides):
    r = {
        "schema_version": "intake.receipt.v1",
        "receipt_id": str(uuid.uuid4()),
        "package_id": pid,
        "consumer_id": CONSUMER_ID,
        "status": "accepted",
        "received_at": "2026-09-25T02:00:00+00:00",
        "manifest_sha256": sha,
        "record_count": count,
    }
    r.update(overrides)
    return r


def _manifest_sha(settings, pid):
    return hashlib.sha256(
        (settings.runtime_root / "packages" / pid / "manifest.json").read_bytes()
    ).hexdigest()


def _source_row(logical_id=None, *, captured_at=None, enabled=1, available=1):
    captured_at = captured_at or datetime.now(timezone.utc).isoformat()
    expires = (
        _parse(captured_at) + timedelta(hours=168)
    ).isoformat()
    return Source(
        logical_id=logical_id or str(uuid.uuid4()),
        scope="page",
        account_id=ACCOUNT_ID,
        conversation_id="syn-thread-1",
        provider_message_id="syn-msg-1",
        attachment_id="syn-att-1",
        page_index=1,
        captured_at=captured_at,
        current_revision=1,
        image_available=available,
        enabled=enabled,
        image_expires_at=expires,
    )


def _parse(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _ocr_body(logical_id, **overrides):
    body = {
        "schema_version": "intake.ocr-request.v1",
        "request_id": str(uuid.uuid4()),
        "consumer_id": CONSUMER_ID,
        "logical_id": logical_id,
        "variant": "full_res",
        "reason_code": "other",
        "observed_revision": 1,
        "submitted_at": "2026-09-25T02:01:00+00:00",
    }
    body.update(overrides)
    return body


# ---------------------------------------------------------------------------
# auth — decision-sheet §4.1
# ---------------------------------------------------------------------------


def test_auth_required_when_token_configured(tmp_path):
    app, settings, engine = _app(tmp_path, token=TOKEN)
    pid = _package(settings, engine)
    client = TestClient(app)
    for method, url in [
        ("GET", "/intake/v1/packages"),
        ("GET", f"/intake/v1/packages/{pid}/manifest"),
        ("GET", f"/intake/v1/packages/{pid}/records"),
        ("GET", f"/intake/v1/packages/{pid}/ready"),
        ("GET", f"/intake/v1/packages/{pid}/manifest.json"),
        ("POST", "/intake/v1/receipts"),
        ("POST", "/intake/v1/ocr-requests"),
        ("GET", f"/intake/v1/ocr-requests/{uuid.uuid4()}"),
    ]:
        resp = client.request(method, url)
        assert resp.status_code == 401, f"{method} {url} → {resp.status_code}"
        payload = resp.json()
        assert payload["schema_version"] == "intake.error.v1"
        assert payload["error"]["code"] == "unauthorized"

    # Wrong token → same 401.
    resp = client.get(
        "/intake/v1/packages", headers={"Authorization": "Bearer nope"}
    )
    assert resp.status_code == 401
    # Non-bearer scheme → 401.
    resp = client.get(
        "/intake/v1/packages", headers={"Authorization": f"Basic {TOKEN}"}
    )
    assert resp.status_code == 401
    # Correct token → 200.
    resp = client.get(
        "/intake/v1/packages", headers={"Authorization": f"Bearer {TOKEN}"}
    )
    assert resp.status_code == 200


def test_status_endpoint_open_even_with_token(tmp_path):
    app, settings, engine = _app(tmp_path, token=TOKEN)
    client = TestClient(app)
    resp = client.get("/intake/v1/status")
    assert resp.status_code == 200
    assert resp.json()["schema_version"] == "intake.service-status.v1"


def test_loopback_auth_when_no_token(tmp_path):
    app, settings, engine = _app(tmp_path, token=None)
    client = TestClient(app)
    resp = client.get("/intake/v1/packages")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# packages feed — §4.2: sealed only, high-water stability under ACKs
# ---------------------------------------------------------------------------


def test_packages_feed_lists_sealed_only_and_paginates(tmp_path):
    app, settings, engine = _app(tmp_path)
    pids = [_package(settings, engine) for _ in range(5)]
    client = TestClient(app)

    page1 = client.get("/intake/v1/packages", params={"limit": 2}).json()
    assert page1["schema_version"] == "intake.package-list.v1"
    until = page1["until_sequence"]
    assert until == 5
    assert [p["sequence"] for p in page1["packages"]] == [1, 2]
    assert page1["next_after"] == 2
    assert page1["has_more"] is True
    assert [p["package_id"] for p in page1["packages"]] == pids[:2]

    # ACK package 1 mid-sync — the feed window must not shift.
    sha = _manifest_sha(settings, pids[0])
    r = client.post(
        "/intake/v1/receipts",
        content=json.dumps(_receipt(pids[0], sha)),
    )
    assert r.status_code == 200

    page2 = client.get(
        "/intake/v1/packages",
        params={
            "after": page1["next_after"],
            "until_sequence": until,
            "limit": 2,
        },
    ).json()
    assert [p["sequence"] for p in page2["packages"]] == [3, 4]
    assert page2["next_after"] == 4
    assert page2["has_more"] is True

    # A NEW package sealed mid-run stays out of this sync's window.
    _package(settings, engine)
    page3 = client.get(
        "/intake/v1/packages",
        params={"after": 4, "until_sequence": until, "limit": 10},
    ).json()
    assert [p["sequence"] for p in page3["packages"]] == [5]
    assert page3["has_more"] is False

    # A fresh sync sees the remaining sealed ones (acked pkg 1 is gone).
    fresh = client.get("/intake/v1/packages").json()
    assert [p["sequence"] for p in fresh["packages"]] == [2, 3, 4, 5, 6]


def test_packages_feed_empty(tmp_path):
    app, settings, engine = _app(tmp_path)
    client = TestClient(app)
    doc = client.get("/intake/v1/packages").json()
    assert doc["packages"] == []
    assert doc["until_sequence"] == 0
    assert doc["has_more"] is False


# ---------------------------------------------------------------------------
# byte-exact file serves — §4.2
# ---------------------------------------------------------------------------


def test_package_files_served_byte_exact(tmp_path):
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    pkg_dir = _pkg_dir(settings, engine, pid)
    client = TestClient(app)
    for api_name, file_name in [
        ("manifest", "manifest.json"),
        ("manifest.json", "manifest.json"),
        ("records", "records.jsonl"),
        ("records.jsonl", "records.jsonl"),
        ("ready", "READY.json"),
        ("READY.json", "READY.json"),
    ]:
        resp = client.get(f"/intake/v1/packages/{pid}/{api_name}")
        assert resp.status_code == 200, api_name
        assert resp.content == (pkg_dir / file_name).read_bytes()


def test_package_files_remain_after_ack(tmp_path):
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    client = TestClient(app)
    sha = _manifest_sha(settings, pid)
    r = client.post(
        "/intake/v1/receipts", content=json.dumps(_receipt(pid, sha))
    )
    assert r.status_code == 200
    pkg_dir = _pkg_dir(settings, engine, pid)
    resp = client.get(f"/intake/v1/packages/{pid}/records.jsonl")
    assert resp.status_code == 200
    assert resp.content == (pkg_dir / "records.jsonl").read_bytes()


def test_package_file_unknown_package_404(tmp_path):
    app, settings, engine = _app(tmp_path)
    client = TestClient(app)
    resp = client.get(f"/intake/v1/packages/{uuid.uuid4()}/manifest")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "package_unknown"


def test_package_file_expired_404(tmp_path):
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    import shutil

    pkg_dir = _pkg_dir(settings, engine, pid)
    shutil.rmtree(pkg_dir)
    client = TestClient(app)
    resp = client.get(f"/intake/v1/packages/{pid}/manifest")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "package_unknown"


def test_package_files_no_forbidden_content(tmp_path):
    """The emitted package must carry no image refs / base64 / secrets —
    scanned with the validator's forbidden-field rules."""
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    pkg_dir = _pkg_dir(settings, engine, pid)
    for name in ("manifest.json", "READY.json"):
        doc = json.loads((pkg_dir / name).read_bytes())
        assert forbidden_codes(doc) == set()
    for line in (pkg_dir / "records.jsonl").read_text().splitlines():
        assert forbidden_codes(json.loads(line)) == set()


# ---------------------------------------------------------------------------
# receipts — §4.4
# ---------------------------------------------------------------------------


def test_receipt_ack_removes_package_from_feed(tmp_path):
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    client = TestClient(app)
    sha = _manifest_sha(settings, pid)
    r = client.post(
        "/intake/v1/receipts", content=json.dumps(_receipt(pid, sha))
    )
    assert r.status_code == 200
    assert r.json()["package_id"] == pid
    feed = client.get("/intake/v1/packages").json()
    assert feed["packages"] == []
    with session_scope(engine) as session:
        pkg = session.get(Package, pid)
        assert pkg.status == "acked"
        assert json.loads(pkg.receipt_json)["package_id"] == pid


def test_rejected_receipt_keeps_package_pending(tmp_path):
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    client = TestClient(app)
    sha = _manifest_sha(settings, pid)
    r = client.post(
        "/intake/v1/receipts",
        content=json.dumps(
            _receipt(
                pid, sha,
                status="rejected",
                error={"code": "record_count_mismatch",
                       "message": "consumer intake check failed"},
            )
        ),
    )
    assert r.status_code == 200
    with session_scope(engine) as session:
        pkg = session.get(Package, pid)
        assert pkg.status == "sealed"  # stays pending for the consumer
    feed = client.get("/intake/v1/packages").json()
    assert [p["package_id"] for p in feed["packages"]] == [pid]


def test_receipt_wrong_consumer(tmp_path):
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    client = TestClient(app)
    sha = _manifest_sha(settings, pid)
    r = client.post(
        "/intake/v1/receipts",
        content=json.dumps(
            _receipt(pid, sha, consumer_id=str(uuid.uuid4()))
        ),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "receipt_consumer_mismatch"


def test_receipt_unknown_package(tmp_path):
    app, settings, engine = _app(tmp_path)
    client = TestClient(app)
    r = client.post(
        "/intake/v1/receipts",
        content=json.dumps(_receipt(str(uuid.uuid4()), "0" * 64)),
    )
    # Contract §11: "404 unknown" — package_unknown maps to HTTP 404.
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "package_unknown"


def test_receipt_hash_mismatch_conflict(tmp_path):
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    client = TestClient(app)
    r = client.post(
        "/intake/v1/receipts",
        content=json.dumps(_receipt(pid, "f" * 64)),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "receipt_hash_mismatch"
    # Package stays sealed — a rejected receipt never ACKs.
    with session_scope(engine) as session:
        assert session.get(Package, pid).status == "sealed"


def test_receipt_replay_idempotent_and_conflict(tmp_path):
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    sha = _manifest_sha(settings, pid)
    client = TestClient(app)
    rid = str(uuid.uuid4())
    first = client.post(
        "/intake/v1/receipts",
        content=json.dumps(_receipt(pid, sha, receipt_id=rid)),
    )
    assert first.status_code == 200
    again = client.post(
        "/intake/v1/receipts",
        content=json.dumps(_receipt(pid, sha, receipt_id=rid)),
    )
    assert again.status_code == 200
    assert again.json() == first.json()
    # Same receipt_id + different package → validation conflict, not replay.
    other = client.post(
        "/intake/v1/receipts",
        content=json.dumps(
            _receipt(pid, sha, receipt_id=rid, package_id=str(uuid.uuid4()))
        ),
    )
    assert other.status_code == 404
    assert other.json()["error"]["code"] == "package_unknown"


# --- I1: receipt immutability + schema-validated timestamps ---------------------


def test_receipt_different_body_after_ack_conflicts(tmp_path):
    """A stored decision is immutable: a *different* receipt for an already
    ``acked`` package → 409 ``package_conflict``; nothing is overwritten and
    the package status never flips."""
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    sha = _manifest_sha(settings, pid)
    client = TestClient(app)
    first = client.post(
        "/intake/v1/receipts", content=json.dumps(_receipt(pid, sha))
    )
    assert first.status_code == 200
    with session_scope(engine) as session:
        stored = session.get(Package, pid).receipt_json

    different = client.post(
        "/intake/v1/receipts",
        content=json.dumps(
            _receipt(pid, sha, record_count=2,
                     received_at="2026-09-25T03:00:00+00:00")
        ),
    )
    assert different.status_code == 409
    assert different.json()["error"]["code"] == "package_conflict"
    with session_scope(engine) as session:
        pkg = session.get(Package, pid)
        assert pkg.status == "acked"
        assert pkg.receipt_json == stored  # untouched


def test_receipt_different_body_after_rejection_conflicts(tmp_path):
    """``rejected`` also records a decision — a second, different receipt is
    a conflict and the package stays pending in the feed."""
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    sha = _manifest_sha(settings, pid)
    client = TestClient(app)
    first = client.post(
        "/intake/v1/receipts",
        content=json.dumps(
            _receipt(
                pid, sha, status="rejected",
                error={"code": "record_count_mismatch", "message": "no"},
            )
        ),
    )
    assert first.status_code == 200

    second = client.post(
        "/intake/v1/receipts",
        content=json.dumps(_receipt(pid, sha)),
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "package_conflict"
    with session_scope(engine) as session:
        assert session.get(Package, pid).status == "sealed"
    feed = client.get("/intake/v1/packages").json()
    assert [p["package_id"] for p in feed["packages"]] == [pid]


def test_receipt_id_reuse_on_other_package_conflicts(tmp_path):
    """``receipt_id`` is the global idempotency key: reusing it with a
    different body against another *existing* package → 409
    ``package_conflict`` (never treated as a new decision or replay)."""
    app, settings, engine = _app(tmp_path)
    pid1 = _package(settings, engine)
    pid2 = _package(settings, engine)
    sha1 = _manifest_sha(settings, pid1)
    sha2 = _manifest_sha(settings, pid2)
    client = TestClient(app)
    rid = str(uuid.uuid4())
    first = client.post(
        "/intake/v1/receipts",
        content=json.dumps(_receipt(pid1, sha1, receipt_id=rid)),
    )
    assert first.status_code == 200
    reused = client.post(
        "/intake/v1/receipts",
        content=json.dumps(_receipt(pid2, sha2, receipt_id=rid)),
    )
    assert reused.status_code == 409
    assert reused.json()["error"]["code"] == "package_conflict"
    with session_scope(engine) as session:
        assert session.get(Package, pid2).receipt_json is None
        assert session.get(Package, pid2).status == "sealed"


def test_receipt_malformed_timestamps_schema_invalid(tmp_path):
    """Malformed ``received_at`` (and the out-of-schema ``sent_at``) must
    fail as ``schema_invalid`` — never silently becoming a retention
    anchor."""
    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    sha = _manifest_sha(settings, pid)
    client = TestClient(app)
    for bad in (
        _receipt(pid, sha, received_at="not-a-timestamp"),
        _receipt(pid, sha, received_at="2026-09-25 02:00:00"),  # not RFC3339
        _receipt(pid, sha, received_at="2026-09-25T02:00:00"),  # no offset
        _receipt(pid, sha, sent_at="2026-09-25T02:00:00Z"),  # closed key set
    ):
        r = client.post("/intake/v1/receipts", content=json.dumps(bad))
        assert r.status_code == 400, bad
        assert r.json()["error"]["code"] == "schema_invalid"
    # Nothing was stored — the package is still pending with no receipt.
    with session_scope(engine) as session:
        pkg = session.get(Package, pid)
        assert pkg.receipt_json is None
        assert pkg.status == "sealed"


def test_status_poll_writes_no_package_audit(tmp_path, monkeypatch):
    """M10: ``GET /status`` walks acked dirs for byte totals but must not
    emit ``record_access`` audit entries — audit only real byte serves."""
    import zalo_module.api.intake as intake_api

    app, settings, engine = _app(tmp_path)
    pid = _package(settings, engine)
    sha = _manifest_sha(settings, pid)
    client = TestClient(app)
    r = client.post(
        "/intake/v1/receipts", content=json.dumps(_receipt(pid, sha))
    )
    assert r.status_code == 200  # package now acked

    calls: list[tuple] = []
    monkeypatch.setattr(
        intake_api, "record_access", lambda p, k: calls.append((p, k))
    )
    resp = client.get("/intake/v1/status")
    assert resp.status_code == 200
    assert calls == []  # a stats poll is not a byte serve

    # Byte serves DO audit.
    resp = client.get(f"/intake/v1/packages/{pid}/manifest")
    assert resp.status_code == 200
    assert any(k == "package" for _p, k in calls)


# ---------------------------------------------------------------------------
# OCR requests — §4.5/§4.6
# ---------------------------------------------------------------------------


def test_ocr_request_accepted_enqueues_job(tmp_path):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        src = _source_row()
        s.add(src)
        logical_id = src.logical_id
    client = TestClient(app)
    body = _ocr_body(logical_id, note="góc bị mờ")
    resp = client.post("/intake/v1/ocr-requests", content=json.dumps(body))
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["schema_version"] == "intake.ocr-request-status.v1"
    assert doc["request_id"] == body["request_id"]
    assert doc["state"] == "queued"
    assert doc["attempt"] == 0
    assert doc["max_attempts"] == 3
    uuid.UUID(doc["job_id"])
    assert doc["accepted_at"]

    with session_scope(engine) as s:
        job = s.get(Job, doc["job_id"])
        assert job is not None and job.kind == "ocr_request"
        payload = json.loads(job.payload_json)
        assert payload["request_id"] == body["request_id"]
        assert payload["config_version"] == settings.ocr_config_version
        row = s.get(OcrRequest, body["request_id"])
        assert row is not None and row.state == "queued"
        assert row.job_id == job.job_id


def test_ocr_request_replay_returns_stored_decision(tmp_path):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        src = _source_row()
        s.add(src)
        logical_id = src.logical_id
    client = TestClient(app)
    body = _ocr_body(logical_id)
    r1 = client.post("/intake/v1/ocr-requests", content=json.dumps(body))
    r2 = client.post("/intake/v1/ocr-requests", content=json.dumps(body))
    assert r1.status_code == 200 and r2.status_code == 200
    assert r2.json()["deduplicated"] is True
    assert r1.json()["job_id"] == r2.json()["job_id"]

    # Same request_id, different body → request_conflict envelope.
    mutated = _ocr_body(logical_id, request_id=body["request_id"],
                        reason_code="insufficient_text")
    r3 = client.post("/intake/v1/ocr-requests", content=json.dumps(mutated))
    assert r3.status_code == 409
    assert r3.json()["error"]["code"] == "request_conflict"


def test_ocr_request_dedupe_same_key(tmp_path):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        src = _source_row()
        s.add(src)
        logical_id = src.logical_id
    client = TestClient(app)
    r1 = client.post(
        "/intake/v1/ocr-requests", content=json.dumps(_ocr_body(logical_id))
    )
    assert r1.status_code == 200
    # New request_id, identical dedupe key → deduplicated onto the same job.
    r2 = client.post(
        "/intake/v1/ocr-requests", content=json.dumps(_ocr_body(logical_id))
    )
    doc = r2.json()
    assert doc["deduplicated"] is True
    assert doc["job_id"] == r1.json()["job_id"]
    with session_scope(engine) as s:
        dup = s.get(OcrRequest, doc["request_id"])
        assert dup.deduped_from == r1.json()["request_id"]
        # Still only one job.
        assert s.execute(select(func.count()).select_from(Job)).scalar_one() == 1


def test_ocr_request_schema_codes(tmp_path):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        src = _source_row()
        s.add(src)
        logical_id = src.logical_id
    client = TestClient(app)

    cases = [
        # unsupported variant
        (_ocr_body(logical_id, variant="deep_zoom"), "unsupported_variant"),
        # crop preset outside the closed list
        (_ocr_body(logical_id, variant="crop_bottom", preset="bottom_half"),
         "unsupported_variant"),
        # rotate preset must be auto/null
        (_ocr_body(logical_id, variant="rotate", preset="90deg"),
         "unsupported_variant"),
        # crop_bottom without preset → missing_preset
        (_ocr_body(logical_id, variant="crop_bottom"), "missing_preset"),
        # full_res with a preset → the if/else branch is tagged
        # unsupported_variant by the schema's x-error-code
        (_ocr_body(logical_id, variant="full_res", preset="bottom_third"),
         "unsupported_variant"),
        # non-uuid request_id → schema_invalid
        (_ocr_body(logical_id, request_id="not-a-uuid"), "schema_invalid"),
        # extra top-level field → schema_invalid (additionalProperties)
        (_ocr_body(logical_id, bogus=1), "schema_invalid"),
    ]
    for body, code in cases:
        resp = client.post("/intake/v1/ocr-requests", content=json.dumps(body))
        assert resp.status_code == 400, (body["variant"], resp.status_code)
        assert resp.json()["error"]["code"] == code, (body, resp.json())


@pytest.mark.parametrize(
    "mutation",
    [
        {"image_url": "http://x/1.jpg"},          # banned key
        {"prompt": "please read better"},         # banned key
        {"note": "ảnh tại data:image/png;base64,AAAA"},  # data URI in value
        {"note": "xem file C:/tmp/scan.jpeg"},    # image file name in value
        {"image_sha256": "ab" * 32},              # banned key even if benign
    ],
)
def test_ocr_request_forbidden_field_scan(tmp_path, mutation):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        src = _source_row()
        s.add(src)
        logical_id = src.logical_id
    client = TestClient(app)
    body = _ocr_body(logical_id, **mutation)
    resp = client.post("/intake/v1/ocr-requests", content=json.dumps(body))
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "request_forbidden_field"


def test_ocr_request_unknown_source_persisted_rejection(tmp_path):
    app, settings, engine = _app(tmp_path)
    client = TestClient(app)
    body = _ocr_body(str(uuid.uuid4()))
    resp = client.post("/intake/v1/ocr-requests", content=json.dumps(body))
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["state"] == "rejected"
    assert doc["error"]["code"] == "unknown_source"
    assert doc["finished_at"]
    # Persisted — replay returns the stored rejection.
    replay = client.post("/intake/v1/ocr-requests", content=json.dumps(body))
    assert replay.json()["state"] == "rejected"
    assert replay.json()["deduplicated"] is True
    with session_scope(engine) as s:
        row = s.get(OcrRequest, body["request_id"])
        assert row.state == "rejected"
        assert s.get(Job, row.job_id) is not None


def test_ocr_request_disabled_source(tmp_path):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        src = _source_row(enabled=0)
        s.add(src)
        logical_id = src.logical_id
    client = TestClient(app)
    doc = client.post(
        "/intake/v1/ocr-requests",
        content=json.dumps(_ocr_body(logical_id)),
    ).json()
    assert doc["state"] == "rejected"
    assert doc["error"]["code"] == "source_not_enabled"


def test_ocr_request_stale_revision(tmp_path):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        src = _source_row()
        src.current_revision = 4
        s.add(src)
        logical_id = src.logical_id
    client = TestClient(app)
    doc = client.post(
        "/intake/v1/ocr-requests",
        content=json.dumps(_ocr_body(logical_id, observed_revision=2)),
    ).json()
    assert doc["state"] == "rejected"
    assert doc["error"]["code"] == "stale_revision"


def test_ocr_request_image_expired(tmp_path):
    app, settings, engine = _app(tmp_path)
    old = (datetime.now(timezone.utc) - timedelta(hours=200)).isoformat()
    with session_scope(engine) as s:
        src = _source_row(captured_at=old)
        s.add(src)
        logical_id = src.logical_id
    client = TestClient(app)
    doc = client.post(
        "/intake/v1/ocr-requests", content=json.dumps(_ocr_body(logical_id))
    ).json()
    assert doc["state"] == "rejected"
    assert doc["error"]["code"] == "source_image_expired"


def test_ocr_request_image_unavailable(tmp_path):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        src = _source_row(available=0)
        s.add(src)
        logical_id = src.logical_id
    client = TestClient(app)
    doc = client.post(
        "/intake/v1/ocr-requests", content=json.dumps(_ocr_body(logical_id))
    ).json()
    assert doc["state"] == "rejected"
    assert doc["error"]["code"] == "source_image_unavailable"


def test_ocr_request_key_quota(tmp_path):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        src = _source_row()
        s.add(src)
        logical_id = src.logical_id
    client = TestClient(app)
    # Two distinct variants → two accepted jobs on the same logical_id.
    for variant_kw in (
        {"variant": "full_res"},
        {"variant": "rotate", "preset": "auto"},
    ):
        doc = client.post(
            "/intake/v1/ocr-requests",
            content=json.dumps(_ocr_body(logical_id, **variant_kw)),
        ).json()
        assert doc["state"] == "queued"
    third = client.post(
        "/intake/v1/ocr-requests",
        content=json.dumps(
            _ocr_body(logical_id, variant="crop_bottom", preset="bottom_third")
        ),
    ).json()
    assert third["state"] == "rejected"
    assert third["error"]["code"] == "budget_exceeded"


def test_ocr_request_concurrent_quota(tmp_path):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        lids = []
        for _ in range(3):
            src = _source_row()
            s.add(src)
            lids.append(src.logical_id)
    client = TestClient(app)
    for lid in lids[:2]:
        doc = client.post(
            "/intake/v1/ocr-requests", content=json.dumps(_ocr_body(lid))
        ).json()
        assert doc["state"] == "queued"
    doc = client.post(
        "/intake/v1/ocr-requests", content=json.dumps(_ocr_body(lids[2]))
    ).json()
    assert doc["state"] == "rejected"
    assert doc["error"]["code"] == "rate_limited"
    assert doc["error"]["retryable"] is True


def test_ocr_request_day_quota(tmp_path):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        lids = []
        for _ in range(2):
            src = _source_row()
            s.add(src)
            lids.append(src.logical_id)
        # Pre-fill 100 provider-call jobs inside the window (historical rows).
        from zalo_module.jobs.worker import enqueue_job

        now_iso = datetime.now(timezone.utc).isoformat()
        for i in range(100):
            jid = enqueue_job(
                "ocr_request",
                {"request_id": str(uuid.uuid4()), "config_version": "cfg"},
                s,
                logical_id=lids[0],
                request_id=str(uuid.uuid4()),
            )
            job = s.get(Job, jid)
            job.state = "succeeded"  # historical — not concurrent
            s.add(
                OcrRequest(
                    request_id=str(uuid.uuid4()),
                    consumer_id=CONSUMER_ID,
                    logical_id=lids[0],
                    variant="full_res",
                    preset=None,
                    reason_code="other",
                    observed_revision=1,
                    submitted_at=now_iso,
                    body_canonical_sha256="0" * 64,
                    job_id=jid,
                    state="completed",
                    deduped_from=None,
                )
            )
    client = TestClient(app)
    doc = client.post(
        "/intake/v1/ocr-requests", content=json.dumps(_ocr_body(lids[1]))
    ).json()
    assert doc["state"] == "rejected"
    assert doc["error"]["code"] == "rate_limited"


def test_ocr_request_get_status_shape(tmp_path):
    app, settings, engine = _app(tmp_path)
    with session_scope(engine) as s:
        src = _source_row()
        s.add(src)
        logical_id = src.logical_id
    client = TestClient(app)
    body = _ocr_body(logical_id)
    posted = client.post("/intake/v1/ocr-requests", content=json.dumps(body))
    assert posted.status_code == 200
    got = client.get(f"/intake/v1/ocr-requests/{body['request_id']}")
    assert got.status_code == 200
    doc = got.json()
    for key in (
        "schema_version", "request_id", "job_id", "state",
        "attempt", "max_attempts", "accepted_at",
    ):
        assert key in doc
    assert doc["state"] == "queued"

    missing = client.get(f"/intake/v1/ocr-requests/{uuid.uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "unknown_source"

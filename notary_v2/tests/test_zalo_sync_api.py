"""Tests for routers/zalo_sync.py (MIN-99 slice B).

Slice A (services/zalo_exchange/{client,sync}.py) viet song song — tests nay
inject fake module qua sys.modules nen chay doc lap voi slice A da merge hay
chua.
"""

from __future__ import annotations

import dataclasses
import json
import sys
import types
import uuid
from datetime import datetime, timezone

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from models import ZaloImportLedger, ZaloIntakeResult, ZaloParseJob, ZaloRawRecord, ZaloSyncState
from routers import zalo_sync


PACKAGE_ID = "a0000000-0000-4000-8000-000000000001"
CONSUMER_ID = "c0000000-0000-4000-8000-000000000001"


@pytest.fixture()
def app_factory(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    monkeypatch.setenv("ZALO_MODULE_URL", "http://127.0.0.1:8765")
    monkeypatch.setenv("ZALO_INTAKE_API_TOKEN", "")
    monkeypatch.setenv("ZALO_CONSUMER_ID", CONSUMER_ID)
    monkeypatch.setenv("ZALO_EXCHANGE_ROOT", str(tmp_path / "exchange"))
    monkeypatch.setenv("ZALO_SYNC_INTERVAL_SECONDS", "0")

    app = FastAPI()
    app.include_router(zalo_sync.router)

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return app, factory


def _client(app_factory):
    app, _ = app_factory
    return TestClient(app)


def _install_fake_module(monkeypatch, dotted: str, module) -> None:
    """Inject fake vao sys.modules + attr tren package cha."""
    monkeypatch.setitem(sys.modules, dotted, module)
    parent_name, _, child = dotted.rpartition(".")
    try:
        parent = __import__(parent_name, fromlist=[child])
        monkeypatch.setattr(parent, child, module, raising=False)
    except ImportError:
        pass


def _make_fake_sync_module(report, recorder=None):
    fake = types.ModuleType("services.zalo_exchange.sync")

    @dataclasses.dataclass
    class SyncSettings:
        module_url: str = ""
        token: str | None = None
        consumer_id: str = ""
        exchange_root: str = ""
        timeout: float = 30.0

    def run_sync(db, settings):
        if recorder is not None:
            recorder.append(settings)
        return report

    fake.SyncSettings = SyncSettings
    fake.run_sync = run_sync
    return fake


def _make_fake_client_module(handler=None, error=None):
    fake = types.ModuleType("services.zalo_exchange.client")

    class IntakeClientError(Exception):
        def __init__(self, code, message):
            super().__init__(message)
            self.code = code
            self.message = message

    calls: list[dict] = []

    class IntakeClient:
        def __init__(self, base_url, token=None, timeout=30):
            self.base_url = base_url
            self.token = token
            self.timeout = timeout

        def create_ocr_request(self, body):
            calls.append({"method": "create", "body": body})
            if error is not None:
                raise error
            return handler(body) if handler else {"schema_version": "intake.ocr-request-status.v1", "request_id": body["request_id"], "job_id": str(uuid.uuid4()), "state": "queued", "attempt": 0, "max_attempts": 3}

        def get_ocr_request(self, request_id):
            calls.append({"method": "get", "request_id": request_id})
            if error is not None:
                raise error
            return handler(request_id) if handler else {"schema_version": "intake.ocr-request-status.v1", "request_id": request_id, "job_id": str(uuid.uuid4()), "state": "running", "attempt": 1, "max_attempts": 3}

        def close(self):
            calls.append({"method": "close"})

    fake.IntakeClientError = IntakeClientError
    fake.IntakeClient = IntakeClient
    fake.calls = calls
    return fake


# ---------------------------------------------------------------------------
# POST /api/zalo/sync
# ---------------------------------------------------------------------------


def test_post_sync_503_when_core_missing(app_factory, monkeypatch):
    # `from services.zalo_exchange import sync` resolves via the parent
    # package attribute once the submodule was imported elsewhere — mask
    # both the sys.modules entry AND the bound attribute so the lazy
    # import truly fails regardless of test order.
    import services.zalo_exchange as _zalo_exchange_pkg

    monkeypatch.delattr(_zalo_exchange_pkg, "sync", raising=False)
    monkeypatch.setitem(sys.modules, "services.zalo_exchange.sync", None)
    client = _client(app_factory)
    resp = client.post("/api/zalo/sync")
    assert resp.status_code == 503
    detail = resp.json()["detail"]
    assert detail["code"] == "sync_unavailable"


def test_post_sync_runs_core_builds_settings_and_drains_parse_jobs(app_factory, monkeypatch):
    app, factory = app_factory
    recorder: list = []
    report = {"imported": 1, "skipped": 0, "quarantined": 0, "receipts_sent": 1, "errors": []}
    _install_fake_module(monkeypatch, "services.zalo_exchange.sync", _make_fake_sync_module(report, recorder))

    # Mot pending parse job tren package da co raw record -> duoc drain sau sync
    db = factory()
    db.add(
        ZaloRawRecord(
            record_id="b0000000-0000-4000-8000-000000000001",
            logical_id="b0000000-0000-4000-8000-000000000002",
            revision=1,
            kind="message_text",
            package_id=PACKAGE_ID,
            package_sequence=1,
            captured_at=datetime(2026, 9, 24, 1, 0, tzinfo=timezone.utc),
            recorded_at=datetime(2026, 9, 24, 1, 5, tzinfo=timezone.utc),
            canonical_sha256="0" * 64,
            payload_json=json.dumps(
                {
                    "record_kind": "message_text",
                    "record_id": "b0000000-0000-4000-8000-000000000001",
                    "logical_id": "b0000000-0000-4000-8000-000000000002",
                    "message": {"text": "cam on anh"},
                },
                ensure_ascii=False,
            ),
        )
    )
    job_id = str(uuid.uuid4())
    db.add(ZaloParseJob(job_id=job_id, package_id=PACKAGE_ID, state="pending", attempts=0))
    db.commit()
    db.close()

    client = TestClient(app)
    resp = client.post("/api/zalo/sync")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["report"]["imported"] == 1
    assert payload["parse_jobs_processed"] == 1

    # SyncSettings nhan gia tri tu env
    assert len(recorder) == 1
    settings = recorder[0]
    assert settings.consumer_id == CONSUMER_ID
    assert settings.module_url == "http://127.0.0.1:8765"

    db = factory()
    refreshed = db.get(ZaloParseJob, job_id)
    assert refreshed.state == "succeeded"
    db.close()


def test_post_sync_single_flight_while_running(app_factory):
    """§7.2.5: chi mot luot sync active — luot thu hai bo qua, khong doi."""
    client = _client(app_factory)
    assert zalo_sync._sync_lock.acquire(blocking=False)
    try:
        resp = client.post("/api/zalo/sync")
    finally:
        zalo_sync._sync_lock.release()
    assert resp.status_code == 200
    assert resp.json() == {"already_running": True}


def test_post_sync_maps_transport_error_to_503(app_factory, monkeypatch):
    fake = _make_fake_sync_module(report=None)

    def broken_run_sync(db, settings):
        raise httpx.ConnectError("connection refused")

    fake.run_sync = broken_run_sync
    _install_fake_module(monkeypatch, "services.zalo_exchange.sync", fake)
    client = _client(app_factory)
    resp = client.post("/api/zalo/sync")
    assert resp.status_code == 503
    assert resp.json()["detail"]["code"] == "module_unreachable"


# ---------------------------------------------------------------------------
# GET /api/zalo/sync/state
# ---------------------------------------------------------------------------


def test_sync_state_returns_cursor_and_counts(app_factory):
    app, factory = app_factory
    db = factory()
    db.add(ZaloSyncState(key="last_sequence", value="7"))
    db.add(ZaloSyncState(key="last_run_at", value=json.dumps("2026-09-24T08:10:00+07:00")))
    db.add(ZaloSyncState(key="last_error", value=json.dumps(None)))
    for index, (package_id, decision, receipt) in enumerate(
        (
            ("d0000000-0000-4000-8000-000000000001", "imported", "accepted"),
            ("d0000000-0000-4000-8000-000000000002", "imported", None),
            ("d0000000-0000-4000-8000-000000000003", "quarantined", "rejected"),
        )
    ):
        db.add(
            ZaloImportLedger(
                package_id=package_id,
                consumer_id=CONSUMER_ID,
                sequence=index + 1,
                manifest_sha256="0" * 64,
                record_count=1,
                decision=decision,
                receipt_status=receipt,
            )
        )
    db.add(ZaloParseJob(job_id=str(uuid.uuid4()), package_id=PACKAGE_ID, state="pending", attempts=0))
    db.add(ZaloParseJob(job_id=str(uuid.uuid4()), package_id=PACKAGE_ID, state="failed", attempts=2))
    db.commit()
    db.close()

    client = TestClient(app)
    resp = client.get("/api/zalo/sync/state")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["module_url"] == "http://127.0.0.1:8765"
    assert payload["consumer_id"] == CONSUMER_ID
    assert payload["cursor"] == 7
    assert payload["last_run_at"] == "2026-09-24T08:10:00+07:00"
    assert payload["last_error"] is None
    assert payload["ledger"] == {
        "total": 3,
        "imported": 2,
        "quarantined": 1,
        "receipts_pending": 1,
    }
    assert payload["parse_jobs"]["pending"] == 1
    assert payload["parse_jobs"]["failed"] == 1
    assert payload["state"]["last_sequence"] == 7


# ---------------------------------------------------------------------------
# POST /api/zalo/ocr-requests
# ---------------------------------------------------------------------------


def test_ocr_request_valid_body_proxied(app_factory, monkeypatch):
    fake = _make_fake_client_module()
    _install_fake_module(monkeypatch, "services.zalo_exchange.client", fake)
    client = _client(app_factory)

    body = {
        "logical_id": "01000000-0000-4000-8000-000000000002",
        "variant": "crop_bottom",
        "preset": "bottom_42pct",
        "reason_code": "truncated_footer",
        "observed_revision": 2,
    }
    resp = client.post("/api/zalo/ocr-requests", json=body)
    assert resp.status_code == 200
    status_doc = resp.json()
    assert status_doc["schema_version"] == "intake.ocr-request-status.v1"
    assert status_doc["state"] == "queued"

    sent = fake.calls[0]["body"]
    assert sent["schema_version"] == "intake.ocr-request.v1"
    assert sent["consumer_id"] == CONSUMER_ID
    uuid.UUID(sent["request_id"])  # auto sinh uuid hop le
    assert sent["variant"] == "crop_bottom"
    assert sent["preset"] == "bottom_42pct"
    assert sent["submitted_at"]


@pytest.mark.parametrize(
    "body,needle",
    (
        ({"variant": "rotate"}, "logical_id"),
        (
            {
                "logical_id": "not-a-uuid",
                "variant": "rotate",
                "reason_code": "suspected_rotation",
                "observed_revision": 1,
            },
            "uuid",
        ),
        (
            {
                "logical_id": "01000000-0000-4000-8000-000000000002",
                "variant": "resize",
                "reason_code": "other",
                "observed_revision": 1,
            },
            "variant",
        ),
        (
            {
                "logical_id": "01000000-0000-4000-8000-000000000002",
                "variant": "crop_bottom",
                "reason_code": "other",
                "observed_revision": 1,
            },
            "preset",
        ),
        (
            {
                "logical_id": "01000000-0000-4000-8000-000000000002",
                "variant": "full_res",
                "preset": "hi",
                "reason_code": "other",
                "observed_revision": 1,
            },
            "preset",
        ),
        (
            {
                "logical_id": "01000000-0000-4000-8000-000000000002",
                "variant": "rotate",
                "reason_code": "other",
                "observed_revision": 0,
            },
            "observed_revision",
        ),
        (
            {
                "logical_id": "01000000-0000-4000-8000-000000000002",
                "variant": "rotate",
                "reason_code": "other",
                "observed_revision": 1,
                "image_url": "http://x/img.jpg",
            },
            "khong thuoc",
        ),
    ),
)
def test_ocr_request_validation_rejects_bad_body(app_factory, body, needle):
    client = _client(app_factory)
    resp = client.post("/api/zalo/ocr-requests", json=body)
    assert resp.status_code == 400
    assert needle in resp.json()["detail"]


def test_ocr_request_503_when_module_unreachable(app_factory, monkeypatch):
    fake = _make_fake_client_module(error=httpx.ConnectError("refused"))
    _install_fake_module(monkeypatch, "services.zalo_exchange.client", fake)
    client = _client(app_factory)
    resp = client.post(
        "/api/zalo/ocr-requests",
        json={
            "logical_id": "01000000-0000-4000-8000-000000000002",
            "variant": "rotate",
            "reason_code": "suspected_rotation",
            "observed_revision": 1,
        },
    )
    assert resp.status_code == 503
    assert resp.json()["detail"]["code"] == "module_unreachable"


def test_ocr_request_502_when_module_rejects(app_factory, monkeypatch):
    fake = _make_fake_client_module()
    _install_fake_module(monkeypatch, "services.zalo_exchange.client", fake)

    class RejectingClient(fake.IntakeClient):
        def create_ocr_request(self, body):
            raise fake.IntakeClientError("stale_revision", "observed_revision cu")

    fake.IntakeClient = RejectingClient
    client = _client(app_factory)
    resp = client.post(
        "/api/zalo/ocr-requests",
        json={
            "logical_id": "01000000-0000-4000-8000-000000000002",
            "variant": "rotate",
            "reason_code": "other",
            "observed_revision": 1,
        },
    )
    assert resp.status_code == 502
    assert resp.json()["detail"] == {"code": "stale_revision", "message": "observed_revision cu"}


def test_get_ocr_request_status_proxied(app_factory, monkeypatch):
    fake = _make_fake_client_module()
    _install_fake_module(monkeypatch, "services.zalo_exchange.client", fake)
    client = _client(app_factory)
    request_id = str(uuid.uuid4())
    resp = client.get(f"/api/zalo/ocr-requests/{request_id}")
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["request_id"] == request_id
    assert doc["state"] == "running"
    assert fake.calls[0] == {"method": "get", "request_id": request_id}


def test_get_ocr_request_status_bad_uuid(app_factory):
    client = _client(app_factory)
    resp = client.get("/api/zalo/ocr-requests/not-a-uuid")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/zalo/results
# ---------------------------------------------------------------------------


def _seed_result(db, *, package_id: str, revision: int, persons: int = 0):
    db.add(
        ZaloIntakeResult(
            result_id=str(uuid.uuid4()),
            package_id=package_id,
            revision=revision,
            parser_version="ocr_pipeline-2026-09-24",
            result_json=json.dumps(
                {"persons": [{}] * persons, "properties": [], "raw_results": [], "warnings": []},
                ensure_ascii=False,
            ),
            warnings_json="[]",
            created_at=datetime(2026, 9, 24, 2, 0, tzinfo=timezone.utc),
        )
    )


def test_results_latest_per_package_and_filter(app_factory):
    app, factory = app_factory
    other_package = "e0000000-0000-4000-8000-000000000009"
    db = factory()
    _seed_result(db, package_id=PACKAGE_ID, revision=1)
    _seed_result(db, package_id=PACKAGE_ID, revision=2, persons=1)
    _seed_result(db, package_id=other_package, revision=1)
    db.commit()
    db.close()

    client = TestClient(app)

    resp = client.get("/api/zalo/results")
    assert resp.status_code == 200
    rows = resp.json()["results"]
    assert len(rows) == 2  # latest revision moi package
    by_package = {row["package_id"]: row for row in rows}
    assert by_package[PACKAGE_ID]["revision"] == 2
    assert len(by_package[PACKAGE_ID]["result"]["persons"]) == 1

    resp = client.get(f"/api/zalo/results?package_id={PACKAGE_ID}")
    rows = resp.json()["results"]
    assert [row["revision"] for row in rows] == [2, 1]

    resp = client.get("/api/zalo/results?package_id=missing")
    assert resp.json()["results"] == []


# ---------------------------------------------------------------------------
# main.py wiring
# ---------------------------------------------------------------------------


def test_main_app_wires_zalo_router():
    import main

    paths = [getattr(route, "path", "") for route in main.app.routes]
    assert "/api/zalo/sync" in paths
    assert "/api/zalo/results" in paths


def test_main_lifespan_starts_and_cancels_periodic_sync(monkeypatch):
    import asyncio

    import main

    started: list[float] = []
    cancelled: list[bool] = []

    async def fake_loop(interval):
        started.append(interval)
        try:
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            cancelled.append(True)
            raise

    monkeypatch.setattr(main, "_periodic_zalo_sync", fake_loop)
    monkeypatch.setattr(main.zalo_inbox, "_terminate_connector_process", lambda: None)
    monkeypatch.setenv("ZALO_SYNC_INTERVAL_SECONDS", "10")

    async def exercise():
        async with main.lifespan(main.app):
            await asyncio.sleep(0)

    asyncio.run(exercise())
    assert started == [10.0]
    assert cancelled == [True]


def test_main_lifespan_no_sync_task_when_disabled(monkeypatch):
    import asyncio

    import main

    calls: list = []
    monkeypatch.setattr(main, "_periodic_zalo_sync", lambda interval: calls.append(interval))
    monkeypatch.setattr(main.zalo_inbox, "_terminate_connector_process", lambda: None)
    monkeypatch.setenv("ZALO_SYNC_INTERVAL_SECONDS", "-1")

    async def exercise():
        async with main.lifespan(main.app):
            await asyncio.sleep(0)

    asyncio.run(exercise())
    assert calls == []

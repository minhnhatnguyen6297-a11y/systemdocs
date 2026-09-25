"""MIN-95 slice B — ocr_request handler: variants, dedupe, expiry,
immutable revision-2 semantics."""
from __future__ import annotations

import hashlib
import io
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import sqlalchemy as sa
from PIL import Image
from sqlalchemy import select

from zalo_module.api import ocr_requests as ocr_api
from zalo_module.database import init_db, session_scope
from zalo_module.delivery.record_check import validate_record
from zalo_module.jobs import ocr_jobs
from zalo_module.jobs.worker import JobExpired, enqueue_job
from zalo_module.models import (
    ConvSource,
    Job,
    JournalEntry,
    MediaAsset,
    OcrRequest,
    Package,
    Record,
    Source,
)
from zalo_module.ocr.variants import normalize_preset
from zalo_module.settings import Settings
from zalo_module.storage.media import register_media

from test_ocr_jobs import (
    ACCOUNT,
    CONSUMER,
    CONVERSATION,
    MSG_ID,
    FakeClient,
    FakeResponse,
    _add_media,
    _attachment_records,
    _jpeg_bytes,
    _ok_payload,
    _payload,
    _records,
    _settings,
)


@pytest.fixture()
def env(tmp_path):
    settings = _settings(tmp_path)
    for sub in ("media", "packages", "outbox", "connector"):
        (settings.runtime_root / sub).mkdir(parents=True, exist_ok=True)
    engine = sa.create_engine(settings.db_url)
    init_db(engine)
    return settings, engine


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "test-key")
    yield


def _client(*items):
    """FakeClient whose first item is always the default-pass response."""
    return FakeClient(
        FakeResponse(200, _ok_payload("DEFAULT", "TEXT")), *items
    )


def _default_pass(session, settings, aid: str, client: FakeClient) -> Source:
    """Run a successful default pass on the *shared* client queue; return
    the page-1 Source row."""
    ocr_jobs.OCR_CLIENT = client
    job_id = enqueue_job(
        "ocr_default", {"attachment_id": aid}, session
    )
    job = session.get(Job, job_id)
    ocr_jobs.handle_ocr_default(session, job, settings)
    return session.execute(
        select(Source).where(
            Source.attachment_id == aid, Source.scope == "page"
        )
    ).scalar_one()


def _make_request(
    session,
    logical_id: str,
    variant: str,
    preset=None,
    *,
    request_id: str | None = None,
) -> tuple[OcrRequest, Job]:
    rid = request_id or str(uuid.uuid4())
    body = {
        "schema_version": "intake.ocr-request.v1",
        "request_id": rid,
        "consumer_id": CONSUMER,
        "logical_id": logical_id,
        "variant": variant,
        "preset": preset,
        "reason_code": "insufficient_text",
        "observed_revision": 1,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    row = OcrRequest(
        request_id=rid,
        consumer_id=CONSUMER,
        logical_id=logical_id,
        variant=variant,
        preset=preset,
        reason_code="insufficient_text",
        observed_revision=1,
        submitted_at=body["submitted_at"],
        body_canonical_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
        job_id=None,
        state="queued",
        deduped_from=None,
    )
    payload = {
        "request_id": rid,
        "logical_id": logical_id,
        "variant": variant,
        "preset": preset,
        "reason_code": "insufficient_text",
        "observed_revision": 1,
        "config_version": "ocr-config-test",
    }
    job_id = enqueue_job(
        "ocr_request", payload, session,
        logical_id=logical_id, request_id=rid, max_attempts=3,
    )
    row.job_id = job_id
    session.add(row)
    session.flush()
    return row, session.get(Job, job_id)


def _latest(session, logical_id: str) -> dict:
    rec = session.execute(
        select(Record)
        .where(Record.logical_id == logical_id)
        .order_by(Record.revision.desc())
        .limit(1)
    ).scalar_one()
    return _payload(rec)


# ---------------------------------------------------------------------------
# variants
# ---------------------------------------------------------------------------


def test_request_rotate_new_revision(env, monkeypatch):
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload("ROTATED")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        rev1 = _latest(session, src.logical_id)

        req, job = _make_request(session, src.logical_id, "rotate", None)
        result = ocr_jobs.handle_ocr_request(session, job, settings)
        assert result["deduplicated"] is False
        assert result["new_revision"] == 2
        assert session.get(OcrRequest, req.request_id).state == "completed"

        payload = _latest(session, src.logical_id)
        assert validate_record(payload) == []
        assert payload["revision"] == 2
        assert payload["supersedes"] == {
            "record_id": rev1["record_id"],
            "revision": 1,
        }
        # immutable envelope kept
        assert payload["captured_at"] == rev1["captured_at"]
        assert payload["source"] == rev1["source"]
        assert payload["image_sha256"] == rev1["image_sha256"]

        attempts = payload["ocr"]["attempts"]
        assert len(attempts) == 2
        new_attempt = attempts[1]
        assert new_attempt["image_operation"] == "rotate"
        assert new_attempt["request_id"] == req.request_id
        assert new_attempt["status"] == "succeeded"
        assert new_attempt["ocr_pass_id"] != attempts[0]["ocr_pass_id"]
        # rotate = provider-side flag, no client transform entry
        body = client.calls[-1]["body"]
        assert body["input"]["messages"][0]["content"][0]["enable_rotate"] is True
        # default transcript untouched (owner decision §6.3)
        assert payload["ocr"]["text_lines"] == rev1["ocr"]["text_lines"]
        assert payload["ocr"]["selected_pass_ids"] == rev1["ocr"]["selected_pass_ids"]
        assert session.get(Source, src.logical_id).current_revision == 2


@pytest.mark.parametrize(
    "preset,fraction",
    [
        ("bottom_quarter", 0.25),
        ("bottom_third", 1.0 / 3.0),
        ("bottom_42pct", 0.42),
    ],
)
def test_request_crop_bottom_variants(env, monkeypatch, preset, fraction):
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload("FOOTER")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(80, 60), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        req, job = _make_request(session, src.logical_id, "crop_bottom", preset)
        result = ocr_jobs.handle_ocr_request(session, job, settings)
        assert result["new_revision"] == 2
        payload = _latest(session, src.logical_id)
        assert validate_record(payload) == []
        attempt = payload["ocr"]["attempts"][1]
        assert attempt["image_operation"] == "crop_bottom"
        assert attempt["region"] == {
            "kind": "bottom_fraction",
            "fraction": pytest.approx(fraction),
        }
        ops = [s["op"] for s in attempt["transform_chain"]]
        assert "crop" in ops
        assert attempt["status"] == "succeeded"


def test_request_full_res(env, monkeypatch):
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload("HI-RES")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        req, job = _make_request(session, src.logical_id, "full_res", None)
        ocr_jobs.handle_ocr_request(session, job, settings)
        payload = _latest(session, src.logical_id)
        assert validate_record(payload) == []
        assert payload["ocr"]["attempts"][1]["image_operation"] == "full_res"


# ---------------------------------------------------------------------------
# dedupe
# ---------------------------------------------------------------------------


def test_request_dedupe_no_qwen_call(env, monkeypatch):
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload("ROTATED")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        req1, job1 = _make_request(session, src.logical_id, "rotate", None)
        ocr_jobs.handle_ocr_request(session, job1, settings)
        calls_before = len(client.calls)

        # a *different* request_id with the same (logical, variant, preset) key
        req2, job2 = _make_request(session, src.logical_id, "rotate", "auto")
        result = ocr_jobs.handle_ocr_request(session, job2, settings)
        assert result["deduplicated"] is True
        assert result["deduped_from"] == req1.request_id
        assert session.get(OcrRequest, req2.request_id).state == "completed"
        assert session.get(OcrRequest, req2.request_id).deduped_from == (
            req1.request_id
        )
        assert len(client.calls) == calls_before  # no provider call
        assert _records(session, src.logical_id)[-1].revision == 2  # no rev3


def test_request_dedupe_skips_failed_attempt(env, monkeypatch):
    """A failed earlier pass must NOT dedupe a new request (§9.4)."""
    settings, engine = env
    client = _client(
        FakeResponse(401, text="denied"),          # first rotate → fails
        FakeResponse(200, _ok_payload("ROTATED")),  # second rotate → ok
    )
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        req1, job1 = _make_request(session, src.logical_id, "rotate", None)
        with pytest.raises(RuntimeError):
            ocr_jobs.handle_ocr_request(session, job1, settings)
        assert session.get(OcrRequest, req1.request_id).state == "failed"

        req2, job2 = _make_request(session, src.logical_id, "rotate", None)
        result = ocr_jobs.handle_ocr_request(session, job2, settings)
        assert result["deduplicated"] is False
        assert result["new_revision"] == 3  # rev1 default + rev2 fail + rev3 ok


# ---------------------------------------------------------------------------
# expiry / failures
# ---------------------------------------------------------------------------


def test_request_expired_image(env, monkeypatch):
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload("x")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        asset = session.get(MediaAsset, aid)
        asset.expires_at = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).isoformat()
        asset.state = "expired"
        session.flush()

        req, job = _make_request(session, src.logical_id, "rotate", None)
        with pytest.raises(JobExpired):
            ocr_jobs.handle_ocr_request(session, job, settings)
        assert session.get(OcrRequest, req.request_id).state == "expired"
        assert len(client.calls) == 1  # only the default pass; no req call
        payload = _latest(session, src.logical_id)
        assert payload["revision"] == 2
        assert validate_record(payload) == []
        attempt = payload["ocr"]["attempts"][1]
        assert attempt["status"] == "source_image_expired"
        assert attempt["request_id"] == req.request_id


def test_request_missing_media(env, monkeypatch):
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload("x")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        Path.unlink(
            settings.runtime_root / session.get(MediaAsset, aid).rel_path
        )
        req, job = _make_request(session, src.logical_id, "rotate", None)
        with pytest.raises(RuntimeError):
            ocr_jobs.handle_ocr_request(session, job, settings)
        assert session.get(OcrRequest, req.request_id).state == "failed"
        assert len(client.calls) == 1  # only the default pass ran OCR
        payload = _latest(session, src.logical_id)
        assert payload["revision"] == 2
        attempt = payload["ocr"]["attempts"][1]
        assert attempt["status"] == "failed"
        assert attempt["error"]["code"] == "source_image_unavailable"


def test_request_provider_401_publishes_failed_revision(env, monkeypatch):
    settings, engine = env
    client = _client(FakeResponse(401, text="denied"))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        req, job = _make_request(session, src.logical_id, "rotate", None)
        with pytest.raises(RuntimeError):
            ocr_jobs.handle_ocr_request(session, job, settings)
        assert session.get(OcrRequest, req.request_id).state == "failed"
        assert job.attempts == job.max_attempts  # no retry on 401/403
        payload = _latest(session, src.logical_id)
        assert payload["revision"] == 2
        assert validate_record(payload) == []
        assert payload["ocr"]["attempts"][1]["error"]["code"] == (
            "provider_http_401"
        )


def test_request_retryable_error_retries(env, monkeypatch):
    settings, engine = env
    client = _client(FakeResponse(503, text="boom"))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        req, job = _make_request(session, src.logical_id, "rotate", None)
        job.attempts = 1
        with pytest.raises(Exception):
            ocr_jobs.handle_ocr_request(session, job, settings)
        # retryable path publishes no revision
        assert _records(session, src.logical_id)[-1].revision == 1


def test_request_empty_result_failed(env, monkeypatch):
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload()))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        req, job = _make_request(session, src.logical_id, "rotate", None)
        with pytest.raises(RuntimeError):
            ocr_jobs.handle_ocr_request(session, job, settings)
        payload = _latest(session, src.logical_id)
        attempt = payload["ocr"]["attempts"][1]
        assert attempt["status"] == "failed"
        assert attempt["error"]["code"] == "empty_result"
        # default transcript preserved
        assert payload["ocr"]["text_lines"]
        assert payload["ocr"]["status"] == "succeeded"


def test_request_invalid_variant_belt(env, monkeypatch):
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload("x")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        req, job = _make_request(
            session, src.logical_id, "warp_4d", None
        )
        with pytest.raises(RuntimeError):
            ocr_jobs.handle_ocr_request(session, job, settings)
        assert session.get(OcrRequest, req.request_id).state == "failed"
        assert len(client.calls) == 1  # only the default pass ran OCR


def test_request_unknown_logical(env, monkeypatch):
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload("x")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        req, job = _make_request(
            session, str(uuid.uuid4()), "rotate", None
        )
        with pytest.raises(RuntimeError):
            ocr_jobs.handle_ocr_request(session, job, settings)
        assert session.get(OcrRequest, req.request_id).state == "failed"


# ---------------------------------------------------------------------------
# preset matrix
# ---------------------------------------------------------------------------


def test_preset_matrix():
    assert normalize_preset("rotate", None) is None
    assert normalize_preset("rotate", "auto") == "auto"
    assert normalize_preset("crop_bottom", "bottom_42pct") == "bottom_42pct"
    assert normalize_preset("full_res", None) is None
    with pytest.raises(ValueError):
        normalize_preset("crop_bottom", None)        # missing_preset
    with pytest.raises(ValueError):
        normalize_preset("crop_bottom", "half")      # unsupported
    with pytest.raises(ValueError):
        normalize_preset("rotate", "90")             # unsupported
    with pytest.raises(ValueError):
        normalize_preset("full_res", "x")            # unsupported
    with pytest.raises(ValueError):
        normalize_preset("mirror", None)             # unsupported variant


# ---------------------------------------------------------------------------
# dedicated result package + terminal error persistence (F1 fix round)
# ---------------------------------------------------------------------------


def _package_records(settings, pkg: Package) -> list[dict]:
    path = (
        Path(settings.runtime_root) / pkg.dir_rel_path / "records.jsonl"
    )
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").strip().splitlines()
    ]


def test_request_publishes_dedicated_result_package(env, monkeypatch):
    """A completed request seals its own raw package and the status doc
    exposes ``{package_id, manifest_sha256, new_revision}`` (contract §9.5)."""
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload("ROTATED")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)

        req, job = _make_request(session, src.logical_id, "rotate", None)
        result = ocr_jobs.handle_ocr_request(session, job, settings)
        assert result["deduplicated"] is False
        assert result["new_revision"] == 2

        pkg = session.get(Package, result["package_id"])
        assert pkg is not None
        assert result["manifest_sha256"] == pkg.manifest_sha256
        rec = session.get(Record, result["record_id"])
        assert rec.packaged_in == pkg.package_id
        # The dedicated package carries exactly the produced revision.
        records = _package_records(settings, pkg)
        assert [r["record_id"] for r in records] == [rec.record_id]
        assert records[0]["revision"] == 2

        # Status doc resolves the pointer from the worker-written result.
        job.state = "succeeded"
        job.result_json = json.dumps({"result": result})
        doc = ocr_api._status_doc(
            session.get(OcrRequest, req.request_id), session
        )
        assert doc["state"] == "completed"
        assert doc["result"] == {
            "package_id": pkg.package_id,
            "manifest_sha256": pkg.manifest_sha256,
            "new_revision": 2,
        }


def test_request_dedupe_resolves_existing_package(env, monkeypatch):
    """A deduplicated request still resolves a real package pointer — via
    the existing record's ``packaged_in`` (contract §9.4/§9.5)."""
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload("ROTATED")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)

        req1, job1 = _make_request(session, src.logical_id, "rotate", None)
        r1 = ocr_jobs.handle_ocr_request(session, job1, settings)
        req2, job2 = _make_request(session, src.logical_id, "rotate", None)
        r2 = ocr_jobs.handle_ocr_request(session, job2, settings)

        assert r2["deduplicated"] is True
        assert r2["package_id"] == r1["package_id"]
        assert r2["manifest_sha256"] == r1["manifest_sha256"]
        assert r2["new_revision"] == r1["new_revision"]
        assert session.get(OcrRequest, req2.request_id).state == "completed"

        # Even a minimal worker result (record_id only) resolves the pointer
        # lazily through records.packaged_in.
        job2.state = "succeeded"
        job2.result_json = json.dumps({"record_id": r2["record_id"]})
        doc = ocr_api._status_doc(
            session.get(OcrRequest, req2.request_id), session
        )
        assert doc["result"]["package_id"] == r1["package_id"]
        assert doc["deduplicated"] is True


def test_request_terminal_error_survives_worker_result_overwrite(
    env, monkeypatch
):
    """Terminal request errors persist in ``job.payload_json`` before the
    exception escapes — the worker's ``result_json`` overwrite cannot lose
    the sanitized error code."""
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload()))  # no lines
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)

        req, job = _make_request(session, src.logical_id, "rotate", None)
        with pytest.raises(RuntimeError):
            ocr_jobs.handle_ocr_request(session, job, settings)
        req_row = session.get(OcrRequest, req.request_id)
        assert req_row.state == "failed"
        stored = json.loads(session.get(Job, job.job_id).payload_json)
        assert stored["terminal_error"]["code"] == "empty_result"

        # Simulate the worker's own failure write — code still recoverable.
        job.state = "failed"
        job.result_json = json.dumps(
            {"error": "RuntimeError: empty_result: provider returned no text"}
        )
        doc = ocr_api._status_doc(req_row, session)
        assert doc["state"] == "failed"
        assert doc["error"]["code"] == "empty_result"


# ---------------------------------------------------------------------------
# §9.4 single-flight
# ---------------------------------------------------------------------------


def test_single_flight_oldest_running_job_proceeds(env, monkeypatch):
    """Two same-logical_id jobs claimed by racing workers: the oldest
    (created_at, job_id) proceeds, the younger requeues retryable."""
    settings, engine = env
    client = _client(FakeResponse(200, _ok_payload()))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        src = _default_pass(session, settings, aid, client)
        _req1, job_a = _make_request(session, src.logical_id, "rotate", None)
        _req2, job_b = _make_request(session, src.logical_id, "crop_bottom",
                                     "half")

        # Both claimed (running); pin created_at so A is deterministically
        # the older job (uuid4 job_ids are not ordered).
        job_a.created_at = "2026-09-24T08:00:00+00:00"
        job_b.created_at = "2026-09-24T08:00:01+00:00"
        job_a.state = "running"
        job_b.state = "running"
        session.flush()

        # Younger sees the older running sibling -> retryable requeue.
        with pytest.raises(ocr_jobs.SameLogicalBusyError):
            ocr_jobs._check_single_flight(session, job_b, src.logical_id)
        # Older sees only a younger sibling -> proceeds.
        ocr_jobs._check_single_flight(session, job_a, src.logical_id)

        # Non-running siblings never block (queued/retry_wait wait their
        # turn; succeeded means the slot is free).
        job_a.state = "succeeded"
        session.flush()
        ocr_jobs._check_single_flight(session, job_b, src.logical_id)

        # Full handler path: busy error propagates as a retryable raise
        # before any request-state mutation.
        job_a.state = "running"
        session.flush()
        with pytest.raises(ocr_jobs.SameLogicalBusyError):
            ocr_jobs.handle_ocr_request(session, job_b, settings)
        assert session.get(OcrRequest, _req2.request_id).state == "queued"

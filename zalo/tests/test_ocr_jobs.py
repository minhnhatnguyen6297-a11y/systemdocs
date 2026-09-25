"""MIN-95 slice B — ocr_default handler + scan_media_for_ocr sweeper.

All offline: a fake httpx-like client drives the real
``call_qwen_ocr_detailed`` code path (body build → error taxonomy → payload
parse) without network. Emitted records are gated through slice C's real
contract validator ``delivery.record_check.validate_record``.
"""
from __future__ import annotations

import hashlib
import io
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import fitz
import pytest
import sqlalchemy as sa
from PIL import Image
from sqlalchemy import select

from zalo_module.database import init_db, session_scope
from zalo_module.delivery.record_check import validate_record
from zalo_module.jobs import ocr_jobs
from zalo_module.jobs.worker import JobExpired, enqueue_job, run_once
from zalo_module.models import (
    ConvSource,
    Job,
    JournalEntry,
    MediaAsset,
    Record,
    Source,
)
from zalo_module.settings import Settings
from zalo_module.storage.media import register_media
from zalo_module.storage.retention import image_expires_at

ACCOUNT = str(uuid.uuid4())
CONVERSATION = "conv-ocr-1"
MSG_ID = "msg-ocr-1"
CONSUMER = str(uuid.uuid4())


# ---------------------------------------------------------------------------
# infra
# ---------------------------------------------------------------------------


def _settings(tmp_path: Path) -> Settings:
    root = tmp_path / "runtime"
    return Settings(
        runtime_root=root,
        db_url=f"sqlite:///{tmp_path.as_posix()}/test.db",
        consumer_id=CONSUMER,
        bind="127.0.0.1",
        port=0,
        qwen_api_base="http://qwen.test",
        qwen_model="qwen-vl-ocr-2025-11-20",
        qwen_api_key="test-key",
        account_id=None,
        ocr_config_version="ocr-config-test",
        access_log_path=root / "access.jsonl",
        connector_state_root=root / "connector",
    )


@pytest.fixture()
def env(tmp_path):
    settings = _settings(tmp_path)
    for sub in ("media", "packages", "outbox", "connector"):
        (settings.runtime_root / sub).mkdir(parents=True, exist_ok=True)
    engine = sa.create_engine(settings.db_url)
    init_db(engine)
    return settings, engine


def _jpeg_bytes(width=60, height=40, color=(120, 160, 200)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()


def _pdf_bytes(pages=2, size=(300, 400)) -> bytes:
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=size[0], height=size[1])
    data = doc.tobytes()
    doc.close()
    return data


def _seed_provenance(session, attachment_id: str, *, sender=True) -> None:
    """ConvSource + media dedupe journal row the way ingest writes them."""
    if (
        session.execute(
            select(ConvSource).where(
                ConvSource.connector_account_id == ACCOUNT,
                ConvSource.conversation_id == CONVERSATION,
            )
        ).scalar_one_or_none()
        is None
    ):
        session.add(
            ConvSource(
                conv_source_id=str(uuid.uuid4()),
                connector_account_id=ACCOUNT,
                conversation_id=CONVERSATION,
                conversation_type="user",
                source_type="user",
                display_name="OCR conv",
                enabled=1,
            )
        )
    component = {
        "connector_account_id": ACCOUNT,
        "conversation_id": CONVERSATION,
        "msg_id": MSG_ID,
        "attachment_index": 0,
        "media_object_key": f"{attachment_id}.bin",
        "mime_type": "image/jpeg",
        "size_bytes": 10,
        "sent_at": "2026-03-01T10:00:00Z",
    }
    event = {"component": component, "result_id": attachment_id}
    session.add(
        JournalEntry(
            capture_id=str(uuid.uuid4()),
            source_key=hashlib.sha256(
                f"media:{attachment_id}".encode()
            ).hexdigest(),
            event_json=json.dumps(
                event, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
            captured_at=component["sent_at"],
            recorded_at=component["sent_at"],
        )
    )


def _add_media(
    session,
    settings: Settings,
    data: bytes,
    *,
    filename: str,
    state: str = "captured",
    captured_at: datetime | None = None,
    provenance: bool = True,
) -> str:
    """Write media file + media_assets row; return attachment_id."""
    aid = str(uuid.uuid4())
    captured = captured_at or datetime.now(timezone.utc)
    rel_path = f"media/{aid}-{filename}"
    target = settings.runtime_root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    register_media(aid, hashlib.sha256(data).hexdigest(), rel_path, captured, session)
    asset = session.get(MediaAsset, aid)
    asset.state = state
    if provenance:
        _seed_provenance(session, aid)
    session.flush()
    return aid


def _payload(rec: Record) -> dict:
    return json.loads(rec.payload_json)


def _records(session, logical_id: str) -> list[Record]:
    return (
        session.execute(
            select(Record)
            .where(Record.logical_id == logical_id)
            .order_by(Record.revision)
        )
        .scalars()
        .all()
    )


def _attachment_records(session, attachment_id: str) -> list[Record]:
    lids = [
        s.logical_id
        for s in session.execute(
            select(Source).where(Source.attachment_id == attachment_id)
        )
        .scalars()
        .all()
    ]
    if not lids:
        return []
    return (
        session.execute(select(Record).where(Record.logical_id.in_(lids)))
        .scalars()
        .all()
    )


def _enqueue_default(session, attachment_id: str) -> Job:
    job_id = enqueue_job("ocr_default", {"attachment_id": attachment_id}, session)
    return session.get(Job, job_id)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self.is_success = 200 <= status_code < 300
        self._payload = payload
        if text:
            self.text = text
        elif isinstance(payload, (dict, list)):
            self.text = json.dumps(payload)
        else:
            self.text = "not-json"

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeClient:
    """Queue of responses/exceptions; records request bodies for asserts."""

    def __init__(self, *items):
        self.items = list(items)
        self.calls: list[dict] = []

    async def post(self, url, *, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "body": json})
        if not self.items:
            raise AssertionError("FakeClient exhausted")
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _ok_payload(*lines: str, words_info=None):
    content = [
        {
            "text": "\n".join(lines),
            **(
                {"ocr_result": {"words_info": words_info}}
                if words_info is not None
                else {}
            ),
        }
    ]
    return {"output": {"choices": [{"message": {"content": content}}]}}


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "test-key")
    yield


# ---------------------------------------------------------------------------
# sweeper
# ---------------------------------------------------------------------------


def test_sweeper_enqueues_uncovered_asset(env):
    settings, engine = env
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        enqueued = ocr_jobs.scan_media_for_ocr(session, settings)
        assert enqueued == 1
        job = session.execute(
            select(Job).where(Job.kind == "ocr_default")
        ).scalar_one()
        assert json.loads(job.payload_json) == {"attachment_id": aid}


def test_sweeper_skips_active_and_covered(env):
    settings, engine = env
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        enqueue_job("ocr_default", {"attachment_id": aid}, session)  # active
        assert ocr_jobs.scan_media_for_ocr(session, settings) == 0


def test_sweeper_skips_expired(env):
    settings, engine = env
    with session_scope(engine) as session:
        aid = _add_media(
            session, settings, _jpeg_bytes(), filename="a.jpg",
            captured_at=datetime.now(timezone.utc) - timedelta(hours=200),
        )
        asset = session.get(MediaAsset, aid)
        asset.expires_at = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).isoformat()
        session.flush()
        assert ocr_jobs.scan_media_for_ocr(session, settings) == 0


def test_sweeper_bound_and_oldest_first(env, monkeypatch):
    settings, engine = env
    monkeypatch.setattr(ocr_jobs, "SCAN_LIMIT", 3)
    with session_scope(engine) as session:
        aids = [
            _add_media(
                session, settings, _jpeg_bytes(), filename=f"{i}.jpg",
                captured_at=datetime.now(timezone.utc) - timedelta(hours=10 - i),
            )
            for i in range(5)
        ]
        assert ocr_jobs.scan_media_for_ocr(session, settings) == 3
        jobs = session.execute(
            select(Job).where(Job.kind == "ocr_default").order_by(Job.created_at)
        ).scalars().all()
        got = [json.loads(j.payload_json)["attachment_id"] for j in jobs]
        assert got == aids[:3]  # oldest captured_at first


def test_sweeper_caps_permanent_failures(env, monkeypatch):
    settings, engine = env
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        for _ in range(ocr_jobs.JOB_CAP_PER_ASSET):
            jid = enqueue_job(
                "ocr_default", {"attachment_id": aid}, session
            )
            session.get(Job, jid).state = "failed"
        session.flush()
        assert ocr_jobs.scan_media_for_ocr(session, settings) == 0


# ---------------------------------------------------------------------------
# ocr_default — single image happy path
# ---------------------------------------------------------------------------


def test_default_single_image_writes_valid_record(env, monkeypatch):
    settings, engine = env
    client = FakeClient(FakeResponse(200, _ok_payload("DONG THUE", "123456")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(80, 40), filename="a.jpg")
        job = _enqueue_default(session, aid)
        result = ocr_jobs.handle_ocr_default(session, job, settings)
        assert result["status"] == "succeeded"
        assert len(client.calls) == 1

        src = session.execute(
            select(Source).where(
                Source.attachment_id == aid, Source.scope == "page"
            )
        ).scalar_one()
        assert src.page_index == 1
        rec = _records(session, src.logical_id)[0]
        payload = _payload(rec)
        assert validate_record(payload) == []

        assert payload["record_kind"] == "ocr_page"
        assert payload["revision"] == 1
        assert payload["logical_id"] == src.logical_id
        asset = session.get(MediaAsset, aid)
        assert payload["image_sha256"] == asset.sha256
        assert payload["image_state"] == "captured"
        expected_expires = image_expires_at(
            datetime.fromisoformat(asset.captured_at.replace("Z", "+00:00"))
        )
        got_expires = datetime.fromisoformat(
            payload["image_expires_at"].replace("Z", "+00:00")
        )
        assert got_expires == expected_expires

        src_block = payload["source"]
        assert src_block["provider"] == "zalo_personal"
        assert src_block["account_id"] == ACCOUNT
        assert src_block["conversation_id"] == CONVERSATION
        assert src_block["conversation_type"] == "user"
        assert src_block["attachment_id"] == aid
        assert src_block["page_index"] == 1

        ocr = payload["ocr"]
        assert ocr["status"] == "succeeded"
        assert len(ocr["attempts"]) == 1
        attempt = ocr["attempts"][0]
        assert attempt["image_operation"] == "original"
        assert attempt["task"] == "text_recognition"
        assert attempt["geometry_status"] == "not_applicable"
        assert "provider_lines" not in attempt
        assert attempt["provider"] == "qwen"
        assert attempt["config_version"] == "ocr-config-test"
        assert attempt["region"] == {"kind": "full_image"}
        assert attempt["transform_chain"][0]["op"] == "exif_transpose"
        assert attempt["submitted_frame"]["width"] > 0
        assert "request_id" not in attempt

        lines = ocr["text_lines"]
        assert [l["text"] for l in lines] == ["DONG THUE", "123456"]
        assert all(l["ocr_pass_id"] == attempt["ocr_pass_id"] for l in lines)
        assert all(l["page_index"] == 1 for l in lines)
        assert ocr["selected_pass_ids"] == [attempt["ocr_pass_id"]]

        # request body sent to provider is the OCR contract shape
        body = client.calls[0]["body"]
        assert body["parameters"]["ocr_options"]["task"] == "text_recognition"
        assert body["input"]["messages"][0]["content"][0]["enable_rotate"] is False


def test_default_job_via_run_once(env, monkeypatch):
    settings, engine = env
    client = FakeClient(FakeResponse(200, _ok_payload("X")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    handlers = {"ocr_default": ocr_jobs.handle_ocr_default}
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        n = ocr_jobs.scan_media_for_ocr(session, settings)
        assert n == 1
    run_once(
        engine, settings, handlers, [], worker_id="t", limit=1
    )
    with session_scope(engine) as session:
        job = session.execute(
            select(Job).where(Job.kind == "ocr_default")
        ).scalar_one()
        assert job.state == "succeeded"
        src = session.execute(
            select(Source).where(
                Source.attachment_id == aid, Source.scope == "page"
            )
        ).scalar_one()
        assert _records(session, src.logical_id)


# ---------------------------------------------------------------------------
# ocr_default — error taxonomy
# ---------------------------------------------------------------------------


def test_default_timeout_raises_for_retry(env, monkeypatch):
    import httpx

    settings, engine = env
    client = FakeClient(httpx.TimeoutException("boom"))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        job = _enqueue_default(session, aid)
        session.get(Job, job.job_id).attempts = 1
        with pytest.raises(Exception):
            ocr_jobs.handle_ocr_default(session, job, settings)


def test_default_429_raises_for_retry(env, monkeypatch):
    settings, engine = env
    client = FakeClient(FakeResponse(429, text="slow down"))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        job = _enqueue_default(session, aid)
        session.get(Job, job.job_id).attempts = 1
        with pytest.raises(Exception):
            ocr_jobs.handle_ocr_default(session, job, settings)


def test_default_429_last_attempt_writes_failed_record(env, monkeypatch):
    settings, engine = env
    client = FakeClient(FakeResponse(429, text="slow down"))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        job = _enqueue_default(session, aid)
        job.attempts = job.max_attempts  # last try
        result = ocr_jobs.handle_ocr_default(session, job, settings)
        assert result["status"] == "failed"
        recs = _attachment_records(session, aid)
        ocr_pages = [r for r in recs if r.kind == "ocr_page"]
        assert len(ocr_pages) == 1
        payload = _payload(ocr_pages[0])
        assert validate_record(payload) == []
        assert payload["ocr"]["status"] == "failed"
        assert payload["ocr"]["attempts"][0]["status"] == "failed"
        assert payload["ocr"]["attempts"][0]["error"]["code"] == (
            "provider_rate_limited"
        )


def test_default_401_fails_without_retry(env, monkeypatch):
    settings, engine = env
    client = FakeClient(FakeResponse(401, text="denied"))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        job = _enqueue_default(session, aid)
        result = ocr_jobs.handle_ocr_default(session, job, settings)
        assert result["status"] == "failed"
        assert len(client.calls) == 1  # no extra attempts for remaining pages
        rec = [
            r for r in _attachment_records(session, aid) if r.kind == "ocr_page"
        ][0]
        attempt = _payload(rec)["ocr"]["attempts"][0]
        assert attempt["status"] == "failed"
        assert attempt["error"]["code"] == "provider_http_401"


def test_default_malformed_json_raises_for_retry(env, monkeypatch):
    settings, engine = env
    bad = FakeResponse(200, payload=ValueError("no json"))
    client = FakeClient(bad)
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        job = _enqueue_default(session, aid)
        session.get(Job, job.job_id).attempts = 1
        with pytest.raises(Exception):
            ocr_jobs.handle_ocr_default(session, job, settings)


def test_default_missing_media_writes_status(env, monkeypatch):
    settings, engine = env
    client = FakeClient(FakeResponse(200, _ok_payload("x")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        Path.unlink(settings.runtime_root / session.get(MediaAsset, aid).rel_path)
        job = _enqueue_default(session, aid)
        result = ocr_jobs.handle_ocr_default(session, job, settings)
        assert result["status"] == "media_missing"
        assert client.calls == []  # provider never called
        recs = _attachment_records(session, aid)
        status_recs = [r for r in recs if r.kind == "processing_status"]
        assert status_recs, "expected media_missing status record"
        payload = _payload(status_recs[0])
        assert validate_record(payload) == []
        assert payload["status"]["code"] == "media_missing"


def test_default_expired_media_publishes_status(env, monkeypatch):
    settings, engine = env
    client = FakeClient(FakeResponse(200, _ok_payload("x")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        asset = session.get(MediaAsset, aid)
        asset.expires_at = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).isoformat()
        asset.state = "expired"
        session.flush()
        job = _enqueue_default(session, aid)
        result = ocr_jobs.handle_ocr_default(session, job, settings)
        assert result["status"] == "source_image_expired"
        assert client.calls == []
        recs = _attachment_records(session, aid)
        payload = _payload(
            [r for r in recs if r.kind == "processing_status"][0]
        )
        assert validate_record(payload) == []
        assert payload["status"]["code"] == "image_expired"


def test_default_empty_ocr_not_succeeded(env, monkeypatch):
    settings, engine = env
    client = FakeClient(FakeResponse(200, _ok_payload()))  # zero lines
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        job = _enqueue_default(session, aid)
        result = ocr_jobs.handle_ocr_default(session, job, settings)
        assert result["status"] == "failed"
        rec = [
            r for r in _attachment_records(session, aid) if r.kind == "ocr_page"
        ][0]
        payload = _payload(rec)
        assert validate_record(payload) == []
        assert payload["ocr"]["status"] == "failed"
        assert payload["ocr"]["attempts"][0]["error"]["code"] == "empty_result"
        assert payload["ocr"]["text_lines"] == []


# ---------------------------------------------------------------------------
# ocr_default — multi-page PDF
# ---------------------------------------------------------------------------


def test_default_two_page_pdf(env, monkeypatch):
    settings, engine = env
    client = FakeClient(
        FakeResponse(200, _ok_payload("TRANG 1")),
        FakeResponse(200, _ok_payload("TRANG 2")),
    )
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _pdf_bytes(2), filename="doc.pdf")
        job = _enqueue_default(session, aid)
        result = ocr_jobs.handle_ocr_default(session, job, settings)
        assert result["status"] == "succeeded"
        assert result["pages"] == 2
        assert len(client.calls) == 2
        page_sources = (
            session.execute(
                select(Source).where(
                    Source.attachment_id == aid, Source.scope == "page"
                )
            )
            .scalars()
            .all()
        )
        assert {s.page_index for s in page_sources} == {1, 2}
        for src in page_sources:
            payload = _payload(_records(session, src.logical_id)[0])
            assert validate_record(payload) == []
            assert payload["ocr"]["status"] == "succeeded"
            assert payload["ocr"]["text_lines"][0]["page_index"] == (
                src.page_index
            )


def test_default_partial_pdf_keeps_successes(env, monkeypatch):
    settings, engine = env
    client = FakeClient(
        FakeResponse(200, _ok_payload("TRANG 1")),
        FakeResponse(500, text="server boom"),
    )
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _pdf_bytes(2), filename="doc.pdf")
        job = _enqueue_default(session, aid)
        job.attempts = job.max_attempts  # last try → failure is terminal
        result = ocr_jobs.handle_ocr_default(session, job, settings)
        assert result["status"] == "partial"
        recs = _attachment_records(session, aid)
        by_page = {}
        status_recs = []
        for r in recs:
            payload = _payload(r)
            if r.kind == "ocr_page":
                by_page[payload["source"]["page_index"]] = payload
            else:
                status_recs.append(payload)
        assert by_page[1]["ocr"]["status"] == "succeeded"
        assert by_page[1]["ocr"]["text_lines"][0]["text"] == "TRANG 1"
        assert by_page[2]["ocr"]["status"] == "failed"
        assert validate_record(by_page[1]) == []
        assert validate_record(by_page[2]) == []
        assert status_recs and status_recs[0]["status"]["code"] == "ocr_partial"
        assert validate_record(status_recs[0]) == []


def test_default_retryable_pdf_retry_keeps_page1(env, monkeypatch):
    """Page 1 succeeds, page 2 hits a retryable error → raise; on the re-run
    page 1 is skipped (record exists) and only page 2 is retried."""
    settings, engine = env
    client = FakeClient(
        FakeResponse(200, _ok_payload("TRANG 1")),
        FakeResponse(503, text="boom"),
    )
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _pdf_bytes(2), filename="doc.pdf")
        job = _enqueue_default(session, aid)
        job.attempts = 1
        job_id = job.job_id
        with pytest.raises(Exception):
            ocr_jobs.handle_ocr_default(session, job, settings)
        # page-1 record survived (handler committed before raising)
        page1 = session.execute(
            select(Source).where(
                Source.attachment_id == aid,
                Source.scope == "page",
                Source.page_index == 1,
            )
        ).scalar_one()
        assert _records(session, page1.logical_id)
    # second run: page 1 not re-called
    client.items = [FakeResponse(200, _ok_payload("TRANG 2"))]
    with session_scope(engine) as session:
        job = session.get(Job, job_id)
        job.attempts = 2
        result = ocr_jobs.handle_ocr_default(session, job, settings)
        assert result["status"] == "succeeded"
        # first run used 2 calls (page1 ok + page2 503); only 1 new call now
        assert len(client.calls) == 3


def test_default_missing_provenance_fails_loudly(env):
    settings, engine = env
    with session_scope(engine) as session:
        aid = _add_media(
            session, settings, _jpeg_bytes(), filename="a.jpg",
            provenance=False,
        )
        job = _enqueue_default(session, aid)
        with pytest.raises(LookupError):
            ocr_jobs.handle_ocr_default(session, job, settings)


def test_sweeper_does_not_reenqueue_completed(env, monkeypatch):
    settings, engine = env
    client = FakeClient(FakeResponse(200, _ok_payload("x")))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        job = _enqueue_default(session, aid)
        session.get(Job, job.job_id).state = "succeeded"
        ocr_jobs.handle_ocr_default(session, job, settings)
        session.get(Job, job.job_id).state = "succeeded"
        assert ocr_jobs.scan_media_for_ocr(session, settings) == 0

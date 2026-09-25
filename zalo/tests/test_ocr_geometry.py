"""MIN-95 — advanced_recognition geometry handling (contract §6.4/§6.5).

Provider ``words_info`` is preserved verbatim as ``provider_lines``
(+ module ``element_index``); geometry_status stays UNVERIFIED — never
``present_mapping_verified``. Malformed/non-finite shapes →
``present_invalid``; none → ``absent``; text_recognition →
``not_applicable``.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import select

from zalo_module.database import init_db, session_scope
from zalo_module.delivery.record_check import validate_record
from zalo_module.jobs import ocr_jobs
from zalo_module.jobs.worker import enqueue_job
from zalo_module.models import Job, Record, Source
from zalo_module.ocr.pipeline import parse_provider_lines

from test_ocr_jobs import (
    FakeClient,
    FakeResponse,
    _add_media,
    _jpeg_bytes,
    _ok_payload,
    _payload,
    _records,
    _settings,
)

FIXTURE = Path(__file__).parent / "fixtures" / "ocr" / "words_info_ok.json"


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


def _run_default(env, monkeypatch, task_env, payload):
    settings, engine = env
    monkeypatch.setenv("ZALO_INTAKE_OCR_TASK", task_env)
    client = FakeClient(FakeResponse(200, payload))
    monkeypatch.setattr(ocr_jobs, "OCR_CLIENT", client)
    with session_scope(engine) as session:
        aid = _add_media(session, settings, _jpeg_bytes(), filename="a.jpg")
        job_id = enqueue_job("ocr_default", {"attachment_id": aid}, session)
        job = session.get(Job, job_id)
        ocr_jobs.handle_ocr_default(session, job, settings)
        src = session.execute(
            select(Source).where(
                Source.attachment_id == aid, Source.scope == "page"
            )
        ).scalar_one()
        return _payload(_records(session, src.logical_id)[0]), client


# ---------------------------------------------------------------------------
# unit-level geometry parsing
# ---------------------------------------------------------------------------


def test_parse_ok_geometry():
    status, lines = parse_provider_lines(
        [
            {"text": "A", "location": [0, 0, 1, 0, 1, 1, 0, 1],
             "rotate_rect": [0.5, 0.5, 1, 1, 30]},
            {"text": "B", "location": [2, 2, 3, 2, 3, 3, 2, 3]},
        ],
        "advanced_recognition",
    )
    assert status == "present_unverified"
    assert [l["element_index"] for l in lines] == [0, 1]
    assert lines[0]["text"] == "A"
    assert lines[0]["location"] == [0, 0, 1, 0, 1, 1, 0, 1]
    assert lines[0]["rotate_rect"] == [0.5, 0.5, 1, 1, 30]
    assert "rotate_rect" not in lines[1]  # absent → key omitted


@pytest.mark.parametrize(
    "element",
    [
        {"text": "A", "location": [0, 0, 1, 0, 1, 1, 0]},          # 7 elems
        {"text": "A", "location": [0, 0, 1, 0, 1, 1, 0, "x"]},     # non-num
        {"text": "A", "location": [0, 0, 1, 0, 1, 1, 0, float("nan")]},
        {"text": "A", "location": [0, 0, 1, 0, 1, 1, 0, float("inf")]},
        {"text": "A", "rotate_rect": [0, 0, 1, 1]},                # 4 elems
        {"text": "A", "rotate_rect": [0, 0, 1, 1, "deg"]},
        "not-a-dict",
    ],
)
def test_parse_invalid_geometry(element):
    status, lines = parse_provider_lines([element], "advanced_recognition")
    assert status == "present_invalid"
    assert lines and lines[0]["element_index"] == 0


def test_parse_absent_and_na():
    assert parse_provider_lines(None, "advanced_recognition") == ("absent", None)
    assert parse_provider_lines([], "advanced_recognition") == ("absent", None)
    assert parse_provider_lines(
        [{"text": "x"}], "text_recognition"
    ) == ("not_applicable", None)


# ---------------------------------------------------------------------------
# end-to-end through the handler
# ---------------------------------------------------------------------------


def test_geometry_present_unverified(env, monkeypatch):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload, client = _run_default(env, monkeypatch, "advanced_recognition", fixture)
    assert validate_record(payload) == []
    attempt = payload["ocr"]["attempts"][0]
    assert attempt["task"] == "advanced_recognition"
    assert attempt["geometry_status"] == "present_unverified"
    assert attempt["geometry_status"] != "present_mapping_verified"
    assert attempt["submitted_frame"]["width"] > 0
    provider_lines = attempt["provider_lines"]
    assert len(provider_lines) == 2
    assert provider_lines[0]["text"] == "CONG CHUNG"
    assert provider_lines[0]["location"] == [10, 20, 210, 20, 210, 60, 10, 60]
    assert provider_lines[1]["rotate_rect"] is None
    # provider task selector went out on the wire
    body = client.calls[0]["body"]
    assert body["parameters"]["ocr_options"]["task"] == "advanced_recognition"


def test_geometry_invalid_in_record(env, monkeypatch):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    words = fixture["output"]["choices"][0]["message"]["content"][0][
        "ocr_result"
    ]["words_info"]
    words[0]["location"] = [1, 2, 3]  # malformed → present_invalid
    payload, _ = _run_default(env, monkeypatch, "advanced_recognition", fixture)
    assert validate_record(payload) == []
    attempt = payload["ocr"]["attempts"][0]
    assert attempt["geometry_status"] == "present_invalid"
    # malformed location dropped; element text kept as evidence
    assert "location" not in attempt["provider_lines"][0]
    assert attempt["provider_lines"][0]["text"] == "CONG CHUNG"


def test_geometry_absent_in_record(env, monkeypatch):
    # advanced task but provider returns no words_info at all
    payload, _ = _run_default(
        env, monkeypatch, "advanced_recognition", _ok_payload("PLAIN")
    )
    assert validate_record(payload) == []
    attempt = payload["ocr"]["attempts"][0]
    assert attempt["geometry_status"] == "absent"
    assert "provider_lines" not in attempt


def test_geometry_not_applicable_under_text_task(env, monkeypatch):
    # provider still sends words_info but task=text_recognition → N/A
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload, _ = _run_default(env, monkeypatch, "text_recognition", fixture)
    assert validate_record(payload) == []
    attempt = payload["ocr"]["attempts"][0]
    assert attempt["task"] == "text_recognition"
    assert attempt["geometry_status"] == "not_applicable"
    assert "provider_lines" not in attempt


def test_invalid_task_env_falls_back(env, monkeypatch):
    payload, client = _run_default(
        env, monkeypatch, "bogus_task", _ok_payload("X")
    )
    attempt = payload["ocr"]["attempts"][0]
    assert attempt["task"] == "text_recognition"
    assert client.calls[0]["body"]["parameters"]["ocr_options"]["task"] == (
        "text_recognition"
    )

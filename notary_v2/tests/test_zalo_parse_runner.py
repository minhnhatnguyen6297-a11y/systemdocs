"""Tests for services.zalo_exchange.parse_runner (MIN-99 slice B).

Parse runner chay text-only tren raw records da import — khong network/Qwen,
khong cham business tables, parser loi chi lam job failed (retry duoc), raw
nguyen ven.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from models import Customer, ZaloIntakeResult, ZaloParseJob, ZaloRawRecord
from services.zalo_exchange import parse_runner


PACKAGE_ID = "a0000000-0000-4000-8000-000000000001"

CCCD_FRONT_LINES = [
    "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
    "CĂN CƯỚC CÔNG DÂN",
    "Họ và tên: NGUYỄN VĂN AN",
    "Số: 001234567890",
    "Ngày sinh: 20/03/1980",
    "Giới tính: Nam",
    "Quốc tịch: Việt Nam",
]

CCCD_BACK_LINES = [
    "CĂN CƯỚC CÔNG DÂN",
    "IDVNA001234567890<<<<<<<<<<<<<",
    "8003201M2503201VNA<<<<<<<<<<<4",
    "NGUYEN<<VAN<AN<<<<<<<<<<<<<<<<",
    "Nơi thường trú: Số 1 Đường ABC, Hà Nội",
    "Ngày cấp: 15/01/2021",
]

GCN_LINES = [
    "GIẤY CHỨNG NHẬN",
    "QUYỀN SỬ DỤNG ĐẤT",
    "Số phát hành (serial): DD 123456",
    "Số vào sổ: VP00166",
    "Thửa đất số: 10",
    "Tờ bản đồ số: 5",
    "Diện tích: 447,0 m2",
    "Địa chỉ: Thôn A, Xã B, Huyện C, Tỉnh D",
    "Ngày cấp: 20/05/2010",
]


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _seed_record(
    db,
    *,
    record_id: str,
    logical_id: str,
    revision: int = 1,
    kind: str = "ocr_page",
    payload: dict,
    package_id: str = PACKAGE_ID,
) -> ZaloRawRecord:
    record = ZaloRawRecord(
        record_id=record_id,
        logical_id=logical_id,
        revision=revision,
        kind=kind,
        package_id=package_id,
        package_sequence=1,
        captured_at=datetime(2026, 9, 24, 1, 0, tzinfo=timezone.utc),
        recorded_at=datetime(2026, 9, 24, 1, 5, tzinfo=timezone.utc),
        canonical_sha256="0" * 64,
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    db.add(record)
    return record


def _ocr_page_payload(
    *,
    record_id: str,
    logical_id: str,
    revision: int = 1,
    page_index: int = 1,
    lines: list[str],
    ocr_status: str = "succeeded",
    selected_pass_ids: list[str] | None = None,
    pass_id: str = "pass-orig",
) -> dict:
    text_lines = [
        {
            "line_id": f"{record_id[:8]}-l{index}",
            "text": line,
            "captured_at": "2026-09-24T08:00:00+07:00",
            "page_index": page_index,
            "ocr_pass_id": pass_id,
        }
        for index, line in enumerate(lines)
    ]
    ocr: dict = {"status": ocr_status, "text_lines": text_lines}
    if selected_pass_ids is not None:
        ocr["selected_pass_ids"] = selected_pass_ids
    else:
        ocr["selected_pass_ids"] = [pass_id]
    return {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "ocr_page",
        "record_id": record_id,
        "logical_id": logical_id,
        "revision": revision,
        "captured_at": "2026-09-24T08:00:00+07:00",
        "recorded_at": "2026-09-24T08:05:00+07:00",
        "source": {
            "provider": "zalo_personal",
            "conversation_id": "conv-1",
            "provider_message_id": f"msg-{record_id[:4]}",
            "sender_id": "uid-1",
            "attachment_id": "f0000000-0000-4000-8000-0000000000a1",
            "page_index": page_index,
        },
        "image_state": "captured",
        "ocr": ocr,
    }


def _message_payload(*, record_id: str, logical_id: str, text: str) -> dict:
    return {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "message_text",
        "record_id": record_id,
        "logical_id": logical_id,
        "revision": 1,
        "captured_at": "2026-09-24T08:00:00+07:00",
        "recorded_at": "2026-09-24T08:05:00+07:00",
        "source": {
            "provider": "zalo_personal",
            "conversation_id": "conv-1",
            "provider_message_id": f"msg-{record_id[:4]}",
            "sender_id": "uid-1",
        },
        "message": {"text": text},
    }


def _seed_job(db, package_id: str = PACKAGE_ID) -> ZaloParseJob:
    job = ZaloParseJob(
        job_id=str(uuid.uuid4()),
        package_id=package_id,
        state="pending",
        attempts=0,
    )
    db.add(job)
    db.commit()
    return job


def _result_row(db, package_id: str) -> ZaloIntakeResult | None:
    return (
        db.query(ZaloIntakeResult)
        .filter(ZaloIntakeResult.package_id == package_id)
        .order_by(ZaloIntakeResult.revision.desc())
        .first()
    )


def test_parse_job_pairs_cccd_pages_and_merges_property(db):
    _seed_record(
        db,
        record_id="01000000-0000-4000-8000-000000000001",
        logical_id="01000000-0000-4000-8000-000000000002",
        kind="ocr_page",
        payload=_ocr_page_payload(
            record_id="01000000-0000-4000-8000-000000000001",
            logical_id="01000000-0000-4000-8000-000000000002",
            page_index=1,
            lines=CCCD_FRONT_LINES,
        ),
    )
    _seed_record(
        db,
        record_id="02000000-0000-4000-8000-000000000001",
        logical_id="02000000-0000-4000-8000-000000000002",
        kind="ocr_page",
        payload=_ocr_page_payload(
            record_id="02000000-0000-4000-8000-000000000001",
            logical_id="02000000-0000-4000-8000-000000000002",
            page_index=2,
            lines=CCCD_BACK_LINES,
        ),
    )
    _seed_record(
        db,
        record_id="03000000-0000-4000-8000-000000000001",
        logical_id="03000000-0000-4000-8000-000000000002",
        kind="ocr_page",
        payload=_ocr_page_payload(
            record_id="03000000-0000-4000-8000-000000000001",
            logical_id="03000000-0000-4000-8000-000000000002",
            page_index=1,
            lines=GCN_LINES,
        ),
    )
    _seed_record(
        db,
        record_id="04000000-0000-4000-8000-000000000001",
        logical_id="04000000-0000-4000-8000-000000000002",
        kind="message_text",
        payload=_message_payload(
            record_id="04000000-0000-4000-8000-000000000001",
            logical_id="04000000-0000-4000-8000-000000000002",
            text="Da nhan duoc giay to anh gui, cam on anh.",
        ),
    )
    job = _seed_job(db)

    processed = parse_runner.run_pending_parse_jobs(db)

    assert processed == 1
    db.refresh(job)
    assert job.state == "succeeded"
    assert job.attempts == 1
    assert job.error is None

    row = _result_row(db, PACKAGE_ID)
    assert row is not None
    assert row.revision == 1
    assert row.parser_version == parse_runner.PARSER_VERSION

    result = json.loads(row.result_json)
    assert result["package_id"] == PACKAGE_ID
    assert result["record_count"] == 4

    assert len(result["persons"]) == 1
    person = result["persons"][0]
    assert person["paired"] is True
    assert person["side"] == "front_back"
    assert person["ho_ten"] == "NGUYỄN VĂN AN"
    assert person["so_giay_to"] == "001234567890"
    assert person["ngay_cap"] == "15/01/2021"
    assert person["_source"] == "zalo"

    assert len(result["properties"]) == 1
    prop = result["properties"][0]
    assert prop["source_type"] == "zalo"
    assert prop["so_serial"] or prop["so_vao_so"] or prop["dia_chi"]

    kinds = {entry["record_kind"] for entry in result["raw_results"]}
    assert kinds == {"ocr_page", "message_text"}
    message_entry = next(e for e in result["raw_results"] if e["record_kind"] == "message_text")
    assert message_entry["status"] == "message"

    # message_text khong aggregate len persons/properties
    assert len(result["persons"]) == 1

    # Khong ghi business tables
    assert db.query(Customer).count() == 0


def test_superseded_record_kept_out_of_aggregation(db):
    logical_id = "05000000-0000-4000-8000-000000000002"
    for revision, lines in ((1, CCCD_FRONT_LINES), (2, GCN_LINES)):
        record_id = f"05000000-0000-4000-8000-00000000000{revision}"
        _seed_record(
            db,
            record_id=record_id,
            logical_id=logical_id,
            revision=revision,
            kind="ocr_page",
            payload=_ocr_page_payload(
                record_id=record_id,
                logical_id=logical_id,
                revision=revision,
                page_index=1,
                lines=lines,
            ),
        )
    _seed_job(db)

    assert parse_runner.run_pending_parse_jobs(db) == 1

    row = _result_row(db, PACKAGE_ID)
    result = json.loads(row.result_json)
    assert result["superseded_count"] == 1
    superseded = [e for e in result["raw_results"] if e["status"] == "superseded"]
    assert len(superseded) == 1
    assert superseded[0]["revision"] == 1

    # Rev 2 la GCN — khong co person nao duoc tao tu rev 1 da bi supersede
    assert result["persons"] == []
    assert len(result["properties"]) == 1


def test_failed_ocr_record_marks_warning_not_job_failure(db):
    _seed_record(
        db,
        record_id="06000000-0000-4000-8000-000000000001",
        logical_id="06000000-0000-4000-8000-000000000002",
        kind="ocr_page",
        payload={
            "schema_version": "intake.raw-record.v1",
            "record_kind": "ocr_page",
            "record_id": "06000000-0000-4000-8000-000000000001",
            "logical_id": "06000000-0000-4000-8000-000000000002",
            "revision": 1,
            "captured_at": "2026-09-24T08:00:00+07:00",
            "recorded_at": "2026-09-24T08:05:00+07:00",
            "source": {"provider": "zalo_personal", "provider_message_id": "msg-f", "page_index": 1},
            "image_state": "captured",
            "ocr": {"status": "failed", "attempts": [{"ocr_pass_id": "p1", "status": "failed"}]},
        },
    )
    job = _seed_job(db)

    assert parse_runner.run_pending_parse_jobs(db) == 1

    db.refresh(job)
    assert job.state == "succeeded"
    row = _result_row(db, PACKAGE_ID)
    result = json.loads(row.result_json)
    entry = result["raw_results"][0]
    assert entry["status"] == "ocr_failed"
    assert any(w.startswith("ocr_failed") for w in result["warnings"])
    assert result["persons"] == []


def test_selected_pass_ids_filter_transcript(db):
    lines = _ocr_page_payload(
        record_id="07000000-0000-4000-8000-000000000001",
        logical_id="07000000-0000-4000-8000-000000000002",
        page_index=1,
        lines=[],
        selected_pass_ids=["pass-a"],
    )
    lines["ocr"]["text_lines"] = [
        {
            "line_id": "l-a",
            "text": "NGUYEN VAN AN",
            "captured_at": "2026-09-24T08:00:00+07:00",
            "page_index": 1,
            "ocr_pass_id": "pass-a",
        },
        {
            "line_id": "l-b",
            "text": "DONG NAY KHONG THUOC PASS CHON 999999999999",
            "captured_at": "2026-09-24T08:00:00+07:00",
            "page_index": 1,
            "ocr_pass_id": "pass-b",
        },
    ]
    _seed_record(
        db,
        record_id="07000000-0000-4000-8000-000000000001",
        logical_id="07000000-0000-4000-8000-000000000002",
        kind="ocr_page",
        payload=lines,
    )
    _seed_job(db)

    assert parse_runner.run_pending_parse_jobs(db) == 1
    row = _result_row(db, PACKAGE_ID)
    result = json.loads(row.result_json)
    entry = result["raw_results"][0]
    assert entry["text_lines"] == ["NGUYEN VAN AN"]


def test_parser_exception_fails_job_and_raw_stays_intact(db, monkeypatch):
    record = _seed_record(
        db,
        record_id="08000000-0000-4000-8000-000000000001",
        logical_id="08000000-0000-4000-8000-000000000002",
        kind="ocr_page",
        payload=_ocr_page_payload(
            record_id="08000000-0000-4000-8000-000000000001",
            logical_id="08000000-0000-4000-8000-000000000002",
            page_index=1,
            lines=CCCD_FRONT_LINES,
        ),
    )
    db.commit()
    raw_before = record.payload_json
    job = _seed_job(db)

    def boom(lines, filename):
        raise RuntimeError("parser exploded at C:\\secret\\path with token xyz")

    monkeypatch.setattr(parse_runner._ocr, "_normalize_native_ocr_doc", boom)
    assert parse_runner.run_pending_parse_jobs(db) == 1

    db.refresh(job)
    assert job.state == "failed"
    assert job.attempts == 1
    assert "parser exploded" in (job.error or "")
    assert db.query(ZaloIntakeResult).count() == 0

    # Raw nguyen ven — retry tu raw da luu, khong huy ACK
    db.refresh(record)
    assert record.payload_json == raw_before

    # Luot sau (loi da sua) job failed duoc retry va thanh cong
    monkeypatch.undo()
    assert parse_runner.run_pending_parse_jobs(db) == 1
    db.refresh(job)
    assert job.state == "succeeded"
    assert job.attempts == 2
    assert job.error is None

    row = _result_row(db, PACKAGE_ID)
    assert row is not None and row.revision == 1


def test_second_job_writes_next_revision(db):
    _seed_record(
        db,
        record_id="09000000-0000-4000-8000-000000000001",
        logical_id="09000000-0000-4000-8000-000000000002",
        kind="ocr_page",
        payload=_ocr_page_payload(
            record_id="09000000-0000-4000-8000-000000000001",
            logical_id="09000000-0000-4000-8000-000000000002",
            page_index=1,
            lines=GCN_LINES,
        ),
    )
    first = _seed_job(db)
    assert parse_runner.run_pending_parse_jobs(db) == 1
    db.refresh(first)
    assert first.state == "succeeded"

    second = _seed_job(db)
    assert parse_runner.run_pending_parse_jobs(db) == 1
    db.refresh(second)
    assert second.state == "succeeded"

    revisions = [
        row.revision
        for row in db.query(ZaloIntakeResult)
        .filter(ZaloIntakeResult.package_id == PACKAGE_ID)
        .order_by(ZaloIntakeResult.revision)
        .all()
    ]
    assert revisions == [1, 2]


def test_empty_package_succeeds(db):
    job = _seed_job(db)
    assert parse_runner.run_pending_parse_jobs(db) == 1
    db.refresh(job)
    assert job.state == "succeeded"
    row = _result_row(db, PACKAGE_ID)
    result = json.loads(row.result_json)
    assert result["record_count"] == 0
    assert result["persons"] == [] and result["properties"] == []


def test_running_job_reclaimed_after_crash(db):
    """Crash giua `state=running` -> job khong wedge: luot sau reclaim + parse."""
    _seed_record(
        db,
        record_id="0a000000-0000-4000-8000-000000000001",
        logical_id="0a000000-0000-4000-8000-000000000002",
        kind="ocr_page",
        payload=_ocr_page_payload(
            record_id="0a000000-0000-4000-8000-000000000001",
            logical_id="0a000000-0000-4000-8000-000000000002",
            page_index=1,
            lines=GCN_LINES,
        ),
    )
    job = _seed_job(db)
    job.state = "running"  # mo phong crash sau commit running, truoc khi xong
    job.attempts = 1
    db.commit()

    assert parse_runner.run_pending_parse_jobs(db) == 1
    db.refresh(job)
    assert job.state == "succeeded"
    assert job.attempts == 2
    assert _result_row(db, PACKAGE_ID) is not None


def test_failed_job_stops_retrying_after_attempt_cap(db):
    job = _seed_job(db)
    job.state = "failed"
    job.attempts = parse_runner._MAX_PARSE_ATTEMPTS
    job.error = "deterministic parser error"
    db.commit()

    assert parse_runner.run_pending_parse_jobs(db) == 0
    db.refresh(job)
    assert job.state == "failed"
    assert job.attempts == parse_runner._MAX_PARSE_ATTEMPTS

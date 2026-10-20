"""Controlled Case-only proof: no owner corpus, portal credentials or live DB."""
from __future__ import annotations

import copy
import hashlib
import html
import json
import os
from pathlib import Path

import pytest
from docx import Document

from extraction_adapter import core, extract
from batch_scan import connect_registry, finalize_manifest, run_batch_scan, upsert_registry_record
from playwright_uploader import NamDinhUploaderSession, UploaderSettings, build_upload_form_data, load_upload_queue


# Independent expected business values, declared before extraction.
EXPECTED = {
    "tenvanban": "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
    "nhomhopdong": "Chuyển nhượng - Mua bán",
    "loaivanbannhandien": "transfer_contract",
    "socongchung": "007/2026",
    "ngaycongchung": "2026-06-15",
    "congchungvien": "Nguyễn Công Chứng Mẫu",
    "thuky": None,
    "chudat": None,
}
SOURCE = "\n".join([
    EXPECTED["tenvanban"],
    "Hôm nay, chúng tôi gồm:",
    "BÊN CHUYỂN NHƯỢNG (BÊN A):",
    "Ông Nguyễn Văn Mẫu; Sinh năm 1980; Căn cước số: 001080000001;",
    "Thường trú tại: xã Mẫu A, tỉnh Mẫu;",
    "BÊN NHẬN CHUYỂN NHƯỢNG (BÊN B):",
    "Bà Trần Thị Mẫu; Sinh năm 1982; Căn cước số: 001082000002;",
    "Thường trú tại: xã Mẫu B, tỉnh Mẫu;",
    "ĐIỀU 1. QUYỀN SỬ DỤNG ĐẤT CHUYỂN NHƯỢNG",
    "Quyền sử dụng đất có địa chỉ tại: xã Mẫu, tỉnh Mẫu;",
    "Thửa đất số: 215; Tờ bản đồ số: 34; Diện tích: 120 m2;",
    "Mục đích sử dụng: Đất ở tại nông thôn; Thời hạn sử dụng: Lâu dài;",
    "Giấy chứng nhận quyền sử dụng đất số: AB 123456;",
    "ĐIỀU 2. GIÁ CHUYỂN NHƯỢNG",
    "Giá chuyển nhượng: 999999999 đồng; thời hạn vay: 12 tháng;",
    "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
    "Ngày 15 tháng 06 năm 2026",
    "ngày 15 tháng 06 năm 2026",
    "Tôi, Nguyễn Công Chứng Mẫu, Công chứng viên",
    "Số công chứng 007/2026/CCGD",
])


def _write_docx(path: Path):
    doc = Document()
    for line in SOURCE.splitlines():
        doc.add_paragraph(line)
    doc.save(path)


def _scanned(tmp_path):
    source = tmp_path / "controlled"
    source.mkdir()
    doc = source / "007.2026.CCGD.docx"
    _write_docx(doc)
    work = tmp_path / "isolated-upload"
    manifest = run_batch_scan(source, working_dir=work)
    manifest_path = finalize_manifest(manifest, work / "runs")
    _, records, total = load_upload_queue(manifest_path, working_dir=work)
    assert total == 1
    return work, manifest_path, records[0]


def test_docx_store_fresh_reader_case_and_unchanged_source(tmp_path):
    work, manifest, record = _scanned(tmp_path)
    assert record.payload["case"] == EXPECTED
    original = record.output_json_path.read_bytes()
    raw = copy.deepcopy(record.payload["raw"])
    assert "document_kind" not in raw
    assert set(record.payload["case"]) == set(EXPECTED)
    assert "999999999" not in json.dumps(record.payload["case"])
    assert any(row.get("thoi_han_su_dung") == "Lâu dài"
               for row in raw["danh_sach_thua_dat"])
    registry = connect_registry(work / "registry.sqlite3")
    stored = registry.execute("SELECT case_json FROM file_registry WHERE id=?", (record.record_id,)).fetchone()[0]
    registry.close()
    assert json.loads(stored) == EXPECTED
    _, records, _ = load_upload_queue(manifest, working_dir=work,
                                      cong_chung_vien="CCV được chọn", thu_ky="Thư ký Mẫu")
    selected = {**EXPECTED, "congchungvien": "CCV được chọn", "thuky": "Thư ký Mẫu"}
    assert records[0].payload["case"] == selected
    _, reopened, _ = load_upload_queue(manifest, working_dir=work)
    assert reopened[0].payload["case"] == EXPECTED  # queue overrides are read-only candidates
    assert reopened[0].payload["raw"] == raw
    assert record.output_json_path.read_bytes() == original
    assert reopened[0].upload_form["ngay_cong_chung"] == "15/06/2026"
    assert reopened[0].upload_form["so_cong_chung"] == "007/2026"
    assert reopened[0].upload_form["cong_chung_vien"] == EXPECTED["congchungvien"]
    # A stale/incorrect portal-shaped Case projection cannot override canonical truth.
    stale = copy.deepcopy(reopened[0].payload)
    stale["web_form"]["ngay_cong_chung"] = "01/01/1900"
    assert build_upload_form_data(stale)["ngay_cong_chung"] == "15/06/2026"


@pytest.mark.parametrize("bad", [None, False, [], {}, "broken"])
def test_invalid_canonical_case_never_falls_back(bad):
    with pytest.raises(ValueError):
        core.case_from_payload({"case": bad, "web_form": {"so_cong_chung": "1/2026"}, "raw": {}})


def test_legacy_default_name_is_ambiguous_but_source_untouched(tmp_path):
    work = tmp_path / "legacy"
    work.mkdir()
    source = work / "source.docx"
    source.write_bytes(b"historical evidence, must not be reread as DOCX")
    output = work / "legacy.json"
    legacy = {"web_form": {"ten_hop_dong": "Văn bản mẫu", "ngay_cong_chung": "15/06/2026",
                           "so_cong_chung": "7/2026/CCGD", "cong_chung_vien": core.DEFAULT_CCV},
              "raw": {"file_goc": str(source), "document_kind": "generic", "ben_a": {"nguoi": []}}}
    output.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
    before = hashlib.sha256(output.read_bytes()).hexdigest()
    conn = connect_registry(work / "registry.sqlite3")
    upsert_registry_record(conn, file_key="legacy", file_path=source, stat_result=source.stat(),
                           customer_folder="controlled", status="extracted", run_id="legacy",
                           contract_no="7/2026/CCGD", output_json_path=str(output))
    # Controlled old-schema DB: migration adds only the nullable Case column.
    conn.execute("ALTER TABLE file_registry DROP COLUMN case_json")
    conn.commit()
    conn.close()
    manifest = work / "manifest.json"
    manifest.write_text('{"run_id":"legacy"}', encoding="utf-8")
    _, records, _ = load_upload_queue(manifest, working_dir=work)
    assert records[0].payload["case"]["congchungvien"] is None
    assert records[0].payload["case"]["chudat"] is None
    assert records[0].upload_form["cong_chung_vien"] == core.DEFAULT_CCV  # policy only
    _, records, _ = load_upload_queue(manifest, working_dir=work, cong_chung_vien=core.DEFAULT_CCV)
    assert records[0].payload["case"]["congchungvien"] == core.DEFAULT_CCV
    _, reopened, _ = load_upload_queue(manifest, working_dir=work)
    assert reopened[0].payload["case"]["congchungvien"] is None
    assert hashlib.sha256(output.read_bytes()).hexdigest() == before
    assert core.case_from_payload({"web_form": {"cong_chung_vien": "Khác default"}, "raw": {}})["congchungvien"] == "Khác default"


def test_new_extract_missing_notary_is_not_default_fact():
    payload = core.extract_text(SOURCE.replace("Tôi, Nguyễn Công Chứng Mẫu, Công chứng viên", ""))
    assert payload["case"]["congchungvien"] is None
    assert build_upload_form_data(payload)["cong_chung_vien"] == core.DEFAULT_CCV


def test_corrupt_registry_case_errors_instead_of_json_fallback(tmp_path):
    work, manifest, record = _scanned(tmp_path)
    conn = connect_registry(work / "registry.sqlite3")
    conn.execute("UPDATE file_registry SET case_json='false' WHERE id=?", (record.record_id,))
    conn.commit()
    conn.close()
    with pytest.raises(ValueError):
        load_upload_queue(manifest, working_dir=work)


def test_real_local_browser_presave_consumer(tmp_path, monkeypatch):
    executable = os.environ.get("CASE_FIELDS_CHROMIUM")
    if not executable:
        pytest.skip("Set CASE_FIELDS_CHROMIUM to an existing installed browser for isolated smoke")
    from playwright.sync_api import sync_playwright
    work, manifest, _ = _scanned(tmp_path)
    _, records, _ = load_upload_queue(manifest, working_dir=work,
                                      cong_chung_vien="CCV được chọn", thu_ky="Thư ký Mẫu")
    record = records[0]
    # Four real queue rows: prepared, excluded duplicate, future chunk, unselected.
    # Their persisted staff values are deliberately different.
    original_payloads = {record.record_id: record.output_json_path.read_bytes()}
    before_cases = {record.record_id: EXPECTED}
    companion_ids = {}
    conn = connect_registry(work / "registry.sqlite3")
    try:
        for number, label in ((8, "duplicate"), (9, "future"), (10, "unselected")):
            payload = copy.deepcopy(record.payload)
            payload["case"] = {
                **EXPECTED, "socongchung": f"{number}/2026",
                "congchungvien": f"CCV {label}", "thuky": f"Thư ký {label}",
            }
            output = work / "output" / f"{label}.json"
            output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            upsert_registry_record(
                conn, file_key=label, file_path=record.source_file,
                stat_result=record.source_file.stat(), customer_folder="controlled",
                status="extracted", run_id=record.run_id, contract_no=f"{number}/2026/CCGD",
                output_json_path=str(output), case_fields=payload["case"])
            row_id = conn.execute("SELECT id FROM file_registry WHERE file_key=?", (label,)).fetchone()[0]
            companion_ids[label] = row_id
            before_cases[row_id] = payload["case"]
            original_payloads[row_id] = output.read_bytes()
    finally:
        conn.close()
    selected_ids = {record.record_id, companion_ids["duplicate"], companion_ids["future"]}
    _, candidate, _ = load_upload_queue(
        manifest, working_dir=work, selected_record_ids=selected_ids, limit=1,
        cong_chung_vien="CCV được chọn", thu_ky="Thư ký Mẫu")
    assert candidate[0].payload["case"]["congchungvien"] == "CCV được chọn"
    _, unchanged, _ = load_upload_queue(manifest, working_dir=work)
    assert {item.record_id: item.payload["case"] for item in unchanged} == before_cases
    ids = {"ten_hop_dong": "hopdong.tenhopdong", "nhom_hop_dong": "nhomhopdongId",
           "loai_tai_san": "loaiTaisan", "cong_chung_vien": "hopdong.congchungvien.id",
           "thu_ky": "hopdong.thuky", "tinh_trang": "hopdong.tinhtrang"}
    controls = []
    for field, element_id in ids.items():
        value = html.escape(record.upload_form[field], quote=True)
        controls.append(f'<select id="{element_id}"><option></option><option>{value}</option></select>')
    controls.extend(['<input id="hopdong.sohopdong">', '<input placeholder="dd/mm/yyyy">'])
    controls.append('<input type="file" id="hopdong.fileHopdong" accept=".doc,.docx,.pdf">')
    for label in ("Thông tin người yêu cầu công chứng", "Đương sự", "Tài sản", "Ghi chú"):
        controls.append(f'<div class="Field-container"><label>{label}</label><div contenteditable="true"></div></div>')
    controls.append('<button onclick="window.saved=true">Lưu hợp đồng</button>')
    page_html = '<!doctype html><meta charset="utf-8"><h1>Controlled local preSave only</h1>' + ''.join(controls)
    settings = UploaderSettings(base_url="http://case-fields.invalid", login_url="http://case-fields.invalid/login",
                                create_url="http://case-fields.invalid/create", storage_state_path=work / "profile.json",
                                post_prepare_delay_ms=0)
    session = NamDinhUploaderSession(settings, working_dir=work, log_callback=lambda message: None)
    # Only external authentication/requester sources are bypassed. Selection,
    # duplicate filtering, chunking, persistence and browser filling stay real.
    from threading import Event
    import playwright_uploader
    monkeypatch.setattr(playwright_uploader, "load_requester_contract_lookup", lambda **kwargs: ({}, ""))
    monkeypatch.setattr(session, "ensure_authenticated", lambda **kwargs: None)
    artifacts = Path(os.environ.get("CASE_FIELDS_EVIDENCE_DIR", str(tmp_path / "browser-proof")))
    artifacts.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as driver:
        browser = driver.chromium.launch(executable_path=executable, headless=True)
        try:
            session.context = browser.new_context()
            # Route every request locally. No DNS, portal, credentials or Save calls.
            session.context.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html", body=page_html))
            summary = session.prepare_manifest(
                manifest, Event(), selected_record_ids=selected_ids,
                exclude_contract_nos={"8/2026"}, chunk_size=1,
                cong_chung_vien="CCV được chọn", thu_ky="Thư ký Mẫu")
            assert summary["prepared_count"] == 1
            assert summary["excluded_duplicates"] == 1
            assert set(session.prepared_pages) == {record.record_id}
            _, reopened, _ = load_upload_queue(manifest, working_dir=work)
            after_cases = {item.record_id: item.payload["case"] for item in reopened}
            expected_after = {**before_cases, record.record_id: {
                **EXPECTED, "congchungvien": "CCV được chọn", "thuky": "Thư ký Mẫu"}}
            assert after_cases == expected_after
            for item in reopened:
                assert item.output_json_path.read_bytes() == original_payloads[item.record_id]
            artifacts_source = Path(summary["artifact_dir"])
            verify_path = next(artifacts_source.glob("debug_*.json"))
            debug = json.loads(verify_path.read_text(encoding="utf-8"))
            result = {"status": "prepared_dry_run", "verify_json": json.dumps(debug["verify"])}
            import shutil
            for proof_file in artifacts_source.iterdir():
                if proof_file.suffix in (".png", ".json"):
                    shutil.copyfile(proof_file, artifacts / proof_file.name)
            page = session.prepared_pages[record.record_id].page
            assert page.locator('[placeholder="dd/mm/yyyy"]').input_value() == "15/06/2026"
            assert page.locator('[id="hopdong.sohopdong"]').input_value() == "007/2026"
            assert page.locator('[id="hopdong.congchungvien.id"]').input_value() == "CCV được chọn"
            assert page.locator('[id="hopdong.thuky"]').input_value() == "Thư ký Mẫu"
            assert page.evaluate("window.saved === undefined")
            verify = json.loads(result["verify_json"])
            assert all(item["success"] for item in verify["fields"].values())
            (artifacts / "case-consumer-proof.json").write_text(json.dumps({
                "scope": "synthetic Case only; local controlled page, NOT real portal acceptance",
                "case": record.payload["case"], "status": result["status"], "verify": verify,
                "saved": False, "source_unchanged": record.output_json_path.exists(),
                "before_cases": before_cases, "after_cases": after_cases,
                "prepared_record_id": record.record_id, "excluded_record_id": companion_ids["duplicate"],
                "future_record_id": companion_ids["future"], "unselected_record_id": companion_ids["unselected"],
                "summary": summary,
            }, ensure_ascii=False, indent=2), encoding="utf-8")
        finally:
            browser.close()

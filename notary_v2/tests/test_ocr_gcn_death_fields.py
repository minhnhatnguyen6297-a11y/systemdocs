"""Synthetic native OCR regressions: ordered land triples and death-paper identity."""
import json

import pytest

from services.document_intake import ocr_pipeline as ocr
from tools.ocr_eval import field_accuracy as accuracy


@pytest.mark.parametrize("case", json.loads(accuracy.DEFAULT_CASES.read_text(encoding="utf-8")),
                         ids=lambda case: case["id"])
def test_synthetic_cases_are_exact(case):
    result, = accuracy.evaluate([case])
    assert [field for field in result["fields"] if not field["ok"]] == []
    assert accuracy.side_rows([result])[0]["side_ok"]
    assert result["doc_type"] == ("property" if case["kind"] == "gcn" else "person")


def test_land_table_does_not_use_row_number_as_area_or_term_digits_as_area():
    doc = ocr._normalize_native_ocr_doc([
        "GIẤY CHỨNG NHẬN QUYỀN SỬ DỤNG ĐẤT", "AA 000091",
        "Thửa đất số: 91", "Tờ bản đồ số: 9", "Diện tích: 350,5 m2",
        "Loại đất | Diện tích | Thời hạn sử dụng",
        "1 | ONT | 200 m2 | Lâu dài", "2 | CLN | 150,5 m2 | 15/10/2045",
        "Nguồn gốc: Công nhận quyền sử dụng đất",
    ], "synthetic-table.jpg")
    assert doc["data"]["land_rows"] == [
        {"loai_dat": "ONT", "dien_tich": "200", "thoi_han": "Lâu dài"},
        {"loai_dat": "CLN", "dien_tich": "150.5", "thoi_han": "15/10/2045"},
    ]


def test_opaque_asset_term_is_not_distributed_to_multiple_land_rows():
    rows = ocr._extract_property_land_rows([
        "Mục đích sử dụng: ONT: 200 m2; CLN: 150,5 m2",
        "Thời hạn sử dụng: Theo quyết định giao đất",
    ])
    assert rows == [
        {"loai_dat": "ONT", "dien_tich": "200", "thoi_han": ""},
        {"loai_dat": "CLN", "dien_tich": "150.5", "thoi_han": ""},
    ]


def test_death_paper_keeps_applicant_identity_out_of_deceased():
    doc = ocr._normalize_native_ocr_doc([
        "UBND xã Mây Giả", "TRÍCH LỤC KHAI TỬ", "Số: 123/TLKT-BS",
        "Họ và tên người chết: Lê Văn Giả", "Ngày sinh: 1940",
        "Ngày chết: 12/03/2020", "Nơi chết: Bệnh viện Mây Giả",
        "Nơi thường trú cuối cùng: Xã Sao Giả",
        "Người đi khai: Lê Thị Giả", "CCCD: 012000000099",
        "Ngày ký: 15/03/2020",
    ], "synthetic-death.jpg")
    data = doc["data"]
    assert data["so_giay_to"] == data["noi_cap"] == data["ngay_cap"] == ""
    assert data["dia_chi"] == ""
    assert data["so_trich_luc_khai_tu"] == "123/TLKT-BS"
    assert data["noi_cap_khai_tu"] == "UBND xã Mây Giả"
    assert data["ngay_ky"] == "15/03/2020"
    assert data["noi_chet"] == "Bệnh viện Mây Giả"
    assert data["noi_thuong_tru_cuoi"] == "Xã Sao Giả"


@pytest.mark.parametrize("actual", [[], [{"loai_dat": "", "dien_tich": "", "thoi_han": ""}],
    [{"loai_dat": "CLN", "dien_tich": "150.5", "thoi_han": "2045"},
     {"loai_dat": "ONT", "dien_tich": "200", "thoi_han": "Lâu dài"}]])
def test_evaluator_rejects_missing_extra_and_reordered_land_rows(monkeypatch, actual):
    expected = [{"loai_dat": "ONT", "dien_tich": "200", "thoi_han": "Lâu dài"},
                {"loai_dat": "CLN", "dien_tich": "150.5", "thoi_han": "2045"}]
    monkeypatch.setattr(accuracy, "_normalize_native_ocr_doc", lambda *_: {"data": {"land_rows": actual}})
    result, = accuracy.evaluate([{"id": "synthetic", "expected": {"land_rows": expected}}])
    assert any(not field["ok"] for field in result["fields"])


def test_evaluator_rejects_extra_blank_land_row(monkeypatch):
    monkeypatch.setattr(accuracy, "_normalize_native_ocr_doc", lambda *_: {
        "data": {"land_rows": [{"loai_dat": "", "dien_tich": "", "thoi_han": ""}]}})
    result, = accuracy.evaluate([{"id": "synthetic", "expected": {"land_rows": []}}])
    assert all(not field["ok"] for field in result["fields"])
    assert {field["field"] for field in result["fields"]} == {
        "land_rows.loai_dat", "land_rows.dien_tich", "land_rows.thoi_han"}


def test_named_land_finite_term_and_legacy_unitless_area():
    assert ocr._extract_property_land_rows([
        "Loại đất: Đất trồng cây lâu năm 150 m2",
        "Thời hạn sử dụng: Đất trồng cây lâu năm: 12/2043",
    ]) == [{"loai_dat": "CLN", "dien_tich": "150", "thoi_han": "12/2043"}]
    assert ocr._extract_property_land_rows(["CLN 150 Lâu dài"]) == [
        {"loai_dat": "CLN", "dien_tich": "150", "thoi_han": "Lâu dài"}]
    assert ocr._extract_property_area(["Diện tích 150,5 m2"]) == "150.5"


@pytest.mark.parametrize("identity_lines,want", [
    (["(Vợ: Trần Thị Mẫu, CCCD: 012000000099)"], ""),
    (["Chồng: Trần Văn Giả", "CCCD: 012000000099"], ""),
    (["CCCD: 012000000090 (Vợ: Trần Thị Mẫu, CCCD: 012000000099)"], "012000000090"),
])
def test_death_identity_does_not_take_spouse(identity_lines, want):
    doc = ocr._normalize_native_ocr_doc([
        "TRÍCH LỤC KHAI TỬ", "Họ và tên người chết: Lê Văn Mẫu", *identity_lines,
    ], "synthetic-spouse.jpg")
    assert doc["data"]["so_giay_to"] == want


@pytest.mark.parametrize("label", [
    "Ngày đăng ký:", "Ngày, tháng, năm đăng ký:", "Ngày, tháng, năm đăng ký khai tử:",
    "Ngày chết:", "Ngày, tháng, năm chết:", "Ngày, tháng, năm sinh:",
])
def test_death_signature_date_does_not_take_split_event_date(label):
    doc = ocr._normalize_native_ocr_doc([
        "TRÍCH LỤC KHAI TỬ", "Họ và tên người chết: Lê Văn Mẫu",
        label, "ngày 10 tháng 04 năm 2024",
    ], "synthetic-event.jpg")
    assert doc["data"]["ngay_ky"] == ""


def test_property_issue_date_accepts_labelled_column_not_land_expiry():
    assert ocr._extract_property_issue_date([
        "Ngày cấp | 20/10/2008", "CLN | 150 m2 | 20/10/2058",
        "Thời hạn sử dụng: Đến ngày 20/10/2058",
    ]) == "20/10/2008"


def test_death_number_label_does_not_take_embedded_identity_number():
    base = ["TRÍCH LỤC KHAI TỬ", "Họ và tên người chết: Lê Văn Mẫu",
            "Giấy tờ tùy thân số: 012000000090"]
    assert ocr._normalize_native_ocr_doc(base, "synthetic.jpg")["data"]["so_trich_luc_khai_tu"] == ""
    assert ocr._normalize_native_ocr_doc(
        base + ["Số : 12/TLKT-2024"], "synthetic.jpg")["data"]["so_trich_luc_khai_tu"] == "12/TLKT-2024"


def test_named_land_rows_exclude_transferred_land_in_notes():
    rows = ocr._extract_property_land_rows([
        "Loại đất: Đất ở tại nông thôn 200 m2",
        "Thời hạn sử dụng: Đất ở tại nông thôn: Lâu dài",
        "Ghi chú: Đất trồng cây lâu năm 50 m2 đã chuyển nhượng",
    ])
    assert rows == [{"loai_dat": "ONT", "dien_tich": "200", "thoi_han": "Lâu dài"}]

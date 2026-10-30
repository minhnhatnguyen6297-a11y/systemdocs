"""Field-level regressions using synthetic OCR text only."""

import pytest

from services.document_intake import ocr_pipeline as ocr


def front(*extra, title="CĂN CƯỚC CÔNG DÂN", birth="15/08/1995"):
    return [title, "BỘ CÔNG AN", "Số: 012000000001",
            "Họ và tên: Nguyễn Văn Mẫu", f"Ngày sinh: {birth}", *extra]


@pytest.mark.parametrize("printed,agency", [
    ("CỤC TRƯỞNG CỤC CẢNH SÁT QUẢN LÝ HÀNH CHÍNH VỀ TRẬT TỰ XÃ HỘI",
     "CỤC CẢNH SÁT QUẢN LÝ HÀNH CHÍNH VỀ TRẬT TỰ XÃ HỘI"),
    ("GIÁM ĐỐC CÔNG AN TỈNH MẪU", "CÔNG AN TỈNH MẪU"),
    ("Phó Giám đốc Công an tỉnh Mẫu", "Công an tỉnh Mẫu"),
    ("PHÓ CỤC TRƯỞNG CỤC CẢNH SÁT", "CỤC CẢNH SÁT"),
    ("BỘ CÔNG AN", "BỘ CÔNG AN"),
])
def test_back_issuer_is_agency_not_signer_title(printed, agency):
    doc = ocr._normalize_native_ocr_doc([
        "Đặc điểm nhân dạng: Sẹo nhỏ", "Ngày cấp: 15/06/2021", printed], "back.jpg")
    assert doc["side"] == "back"
    assert doc["data"]["noi_cap"] == agency
    assert doc["data"]["dia_chi"] == ""


def test_front_never_uses_ministry_header_as_issuer():
    doc = ocr._normalize_native_ocr_doc(front(), "front.jpg")
    assert doc["side"] == "front"
    assert doc["data"]["noi_cap"] == ""


@pytest.mark.parametrize("stop", [
    "Có giá trị đến: 15/08/2035", "Đặc điểm nhân dạng: Sẹo nhỏ",
    "Ngày, tháng, năm: 15/06/2021", "15/06/2021",
    "Quê quán: Xã Khác, tỉnh Khác", "Nơi đăng ký khai sinh: Xã Khác",
])
def test_inline_comma_address_continues_but_stops_at_other_fields(stop):
    doc = ocr._normalize_native_ocr_doc(front(
        "Nơi thường trú: Số 12, đường Mẫu", "phường Mẫu, thành phố Mẫu",
        stop, "Không phải địa chỉ"), "front.jpg")
    assert doc["data"]["dia_chi"] == "Số 12, đường Mẫu, phường Mẫu, thành phố Mẫu"
    short = ocr._normalize_native_ocr_doc(front(
        "Nơi thường trú: Số 12, đường Mẫu", stop, "Không phải địa chỉ"), "front.jpg")
    assert short["data"]["dia_chi"] == "Số 12, đường Mẫu"


def test_address_keeps_interleaved_skip_and_inline_stop_rules():
    doc = ocr._normalize_native_ocr_doc(front(
        "Nơi thường trú: Thôn Mẫu", "Không thời hạn",
        "xã Mẫu, tỉnh Mẫu, Cơ quan cấp / Date of expiry:"), "front.jpg")
    assert doc["data"]["dia_chi"] == "Thôn Mẫu, xã Mẫu, tỉnh Mẫu"


@pytest.mark.parametrize("title,want", [
    ("CĂN CƯỚC CÔNG DÂN", "Căn cước công dân"),
    ("CAN CUOC CONG DAN", "Căn cước công dân"),
    ("CĂN CƯỚC", "Căn cước"),
])
def test_card_type_follows_printed_title(title, want):
    assert ocr._normalize_native_ocr_doc(front(title=title), "front.jpg")["data"]["loai_giay_to"] == want


@pytest.mark.parametrize("mrz,want", [("IDVNM012000000001<<<<", "Căn cước công dân"),
                                      ("I<VNM012000000001<<<<", ""), ("", "")])
def test_back_type_requires_idvnm_without_title(mrz, want):
    doc = ocr._normalize_native_ocr_doc([
        "Đặc điểm nhân dạng: Sẹo nhỏ", "Ngày cấp: 15/06/2021", mrz], "back.jpg")
    assert doc["data"]["loai_giay_to"] == want


@pytest.mark.parametrize("birth,year_only", [("1935", True), ("02/03/1935", False), ("", False)])
@pytest.mark.parametrize("death", [False, True])
def test_birth_precision_is_boolean_for_cards_and_death_papers(birth, year_only, death):
    lines = (["GIẤY CHỨNG TỬ", "Họ và tên người chết: Nguyễn Văn Mẫu",
              *([f"Ngày, tháng, năm sinh: {birth}"] if birth else []), "Ngày chết: 12/03/2020"]
             if death else front(birth=birth))
    doc = ocr._normalize_native_ocr_doc(lines, "synthetic.jpg")
    assert doc["data"]["ngay_sinh"] == birth
    assert doc["data"]["chi_co_nam_sinh"] is year_only
    if death:
        assert doc["data"]["loai_giay_to"] == "Giấy chứng tử"




def test_address_continuation_keeps_text_before_inline_expiry_date():
    doc = ocr._normalize_native_ocr_doc(front(
        "Nơi thường trú: Số 12, đường Mẫu",
        "phường Mẫu, thành phố Mẫu, Có giá trị đến: 15/08/2035"), "front.jpg")
    assert doc["data"]["dia_chi"] == "Số 12, đường Mẫu, phường Mẫu, thành phố Mẫu"


def test_merged_person_recomputes_precision_from_selected_birth():
    people = [dict(ocr._normalize_person_data({"ngay_sinh": birth}), side=side)
              for birth, side in [("1935", "back"), ("02/03/1935", "front")]]
    assert ocr._merge_person_group(people)["chi_co_nam_sinh"] is False
    assert ocr._merge_person_group(people[:1])["chi_co_nam_sinh"] is True
    sources = ocr._field_sources(ocr._normalize_person_data({"ngay_sinh": "02/03/1935"}), "ai")
    assert sources["chi_co_nam_sinh"] == "ai"
    assert "chi_co_nam_sinh" not in ocr._field_sources(ocr._normalize_person_data({}), "ai")


@pytest.mark.parametrize("label", ["Quê quán", "Có giá trị đến", "Đặc điểm nhân dạng"])
def test_address_label_line_stop_prevents_followup_field_value(label):
    doc = ocr._normalize_native_ocr_doc(front(
        f"Nơi thường trú: Số 12, đường Mẫu, {label}:",
        "Xã Khác, tỉnh Khác"), "front.jpg")
    assert doc["data"]["dia_chi"] == "Số 12, đường Mẫu"


@pytest.mark.parametrize("reverse", [False, True])
def test_same_document_pair_preserves_printed_front_card_type(reverse):
    docs = [
        ocr._normalize_native_ocr_doc(front(title="CĂN CƯỚC"), "card.pdf#p1"),
        ocr._normalize_native_ocr_doc([
            "Đặc điểm nhân dạng: Sẹo nhỏ", "Ngày cấp: 15/06/2021",
            "IDVNM012000000001<<<<"], "card.pdf#p2"),
    ]
    persons, properties, raw = [], [], []
    for doc in reversed(docs) if reverse else docs:
        ocr._append_ai_doc(doc=doc, persons=persons, properties=properties, raw_results=raw)
    paired, = ocr._pair_persons(persons)
    assert paired["side"] == "front_back"
    assert paired["loai_giay_to"] == "Căn cước"

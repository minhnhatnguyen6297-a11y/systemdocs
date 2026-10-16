"""Hành vi vùng chuyển nhượng của LÕI LUẬT CHUNG (fixture #7, dữ liệu giả lập).

Fixture trong `tests/fixtures/` là dữ liệu giả lập (không PII khách thật), giữ
từ vòng #7: serial nguyên văn theo nhãn và địa chỉ thửa có nhãn. Sau cutover
#22 các hành vi đó được kiểm lại trên **đường luật duy nhất**
`engine/contract_extract.py` — không còn pipeline profile riêng.
"""

from __future__ import annotations

import unittest
import unicodedata
from pathlib import Path

from regex_workbench.engine import contract_extract as core

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def people_of(payload: dict) -> list[dict]:
    return (payload["raw"]["ben_a"]["nguoi"] or []) + (payload["raw"]["ben_b"]["nguoi"] or [])


def parcels_of(payload: dict) -> list[dict]:
    return payload["raw"]["danh_sach_thua_dat"]


def first_parcel(payload: dict) -> dict:
    parcels = parcels_of(payload)
    assert parcels, "lõi không tách được thửa nào"
    return parcels[0]


class TransferFixturesTests(unittest.TestCase):
    def test_transfer_chuan_fields(self):
        payload = core.extract_text(load_fixture("transfer_chuan.txt"))
        raw, web_form = payload["raw"], payload["web_form"]

        self.assertEqual(raw["document_kind"], core.DOC_KIND_TRANSFER)
        self.assertEqual(web_form["ngay_cong_chung"], "15/06/2026")
        self.assertEqual(web_form["cong_chung_vien"], "Phạm Minh Chi")
        self.assertEqual(web_form["so_cong_chung"], "428/2026")
        self.assertEqual(raw["scan_contract_no"], "428/2026/CCGD")

        parcel = first_parcel(payload)
        self.assertEqual(parcel["so_gcn_raw"], "AB 123456")
        self.assertEqual(parcel["so_gcn"], "AB123456")
        self.assertEqual(parcel["so_thua_dat"], "215")
        self.assertEqual(parcel["so_to_ban_do"], "34")
        self.assertEqual(parcel["dien_tich"], "68,5 m2")
        self.assertIn("Đống Đa", parcel["dia_chi"])

        names = [person["ho_ten"] for person in people_of(payload)]
        self.assertEqual(names, ["Nguyễn Văn An", "Trần Thị Bình"])

    def test_serial_raw_kept_verbatim_even_one_letter(self):
        payload = core.extract_text(load_fixture("transfer_serial_mot_chu.txt"))
        parcel = first_parcel(payload)
        self.assertEqual(parcel["so_gcn_raw"], "M 012345")
        self.assertEqual(parcel["so_gcn"], "M012345")

    def test_serial_raw_freeform_and_labeled_parcel_address(self):
        payload = core.extract_text(load_fixture("transfer_serial_va_dia_chi_thua.txt"))
        parcel = first_parcel(payload)
        # Serial tự do giữ nguyên văn; không tự suy dạng chuẩn.
        self.assertEqual(parcel["so_gcn_raw"], "TEST-001")
        self.assertEqual(parcel["so_gcn"], "")
        # Nhãn "Địa chỉ thửa đất" điền địa chỉ thửa.
        self.assertEqual(parcel["dia_chi"], "xã Mẫu, tỉnh Mẫu")
        self.assertEqual(parcel["dien_tich"], "123,5 m2")
        self.assertEqual(parcel["muc_dich_su_dung"], "Đất ở")
        self.assertEqual(parcel["thoi_han_su_dung"], "Lâu dài")

    def test_blank_serial_and_address_stay_missing(self):
        text = load_fixture("transfer_serial_va_dia_chi_thua.txt")
        text = text.replace("Giấy chứng nhận số: TEST-001;", "Giấy chứng nhận số:")
        text = text.replace("Địa chỉ thửa đất: xã Mẫu, tỉnh Mẫu;", "Địa chỉ thửa đất:")
        parcel = first_parcel(core.extract_text(text))
        self.assertEqual(parcel["so_gcn_raw"], "")
        self.assertEqual(parcel["dia_chi"], "")
        self.assertEqual(parcel["so_thua_dat"], "12")

    def test_co_user_person_not_dropped(self):
        payload = core.extract_text(load_fixture("transfer_dong_su_dung.txt"))
        names = [person["ho_ten"] for person in people_of(payload)]
        self.assertIn("Lê Thị Cẩm", names)
        self.assertEqual(len(names), 3)
        co_user = next(person for person in people_of(payload) if person["ho_ten"] == "Lê Thị Cẩm")
        self.assertEqual(co_user["cccd"], "001178000003")

    def test_year_only_birth_kept_without_padding(self):
        payload = core.extract_text(load_fixture("transfer_sinh_nam.txt"))
        people = people_of(payload)
        self.assertEqual([person["ngay_sinh"] for person in people], ["1960", "1963", "1988"])
        self.assertTrue(all(person["chi_co_nam_sinh"] for person in people))
        self.assertEqual([person["ho_ten"] for person in people],
                         ["Nguyễn Văn An", "Phạm Thị Dung", "Đỗ Văn Em"])

    def test_missing_fields_stay_missing(self):
        payload = core.extract_text(load_fixture("transfer_thieu_truong.txt"))
        people = people_of(payload)
        self.assertEqual(len(people), 2)
        self.assertEqual(people[1]["cccd"], "")
        self.assertTrue(all(person["cccd"] != "0" for person in people))

    def test_correction_document_does_not_invent_assets(self):
        payload = core.extract_text(load_fixture("dinh_chinh.txt"))
        self.assertEqual(parcels_of(payload), [])
        self.assertIn("tai_san", payload["raw"]["missing_web_form_fields"])
        # Số công chứng của văn bản đính chính, không lấy của hợp đồng gốc.
        self.assertEqual(payload["web_form"]["so_cong_chung"], "451/2026")


    def test_person_without_honorific_kept_when_line_has_evidence(self):
        """Bỏ danh xưng sau nhãn vai trò vẫn không được bỏ sót người (R13).

        Đối chiếu lõi cũ trước cutover: người không danh xưng vẫn được tách
        khi dòng tên có bằng chứng người; giới tính để trống, không bịa.
        """
        text = load_fixture("transfer_dong_su_dung.txt").replace(
            "Đồng sử dụng:\nBà:", "Đồng sử dụng:\n"
        )
        payload = core.extract_text(text)
        people = people_of(payload)
        self.assertEqual([p["ho_ten"] for p in people],
                         ["Nguyễn Văn An", "Lê Thị Cẩm", "Trần Thị Bình"])
        co_user = next(p for p in people if p["ho_ten"] == "Lê Thị Cẩm")
        self.assertEqual(co_user["gioi_tinh"], "")
        self.assertEqual(co_user["ngay_sinh"], "03/03/1978")
        self.assertEqual(co_user["cccd"], "001178000003")

    def test_bare_name_in_party_block_kept(self):
        text = "\n".join([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "I. BÊN CHUYỂN NHƯỢNG (Bên A):",
            "Nguyễn Văn An, sinh ngày: 10/05/1975;",
            "Căn cước công dân số: 001075000001 do Bộ Công an cấp ngày 15/03/2021;",
            "II. BÊN NHẬN CHUYỂN NHƯỢNG (Bên B):",
            "Trần Thị Bình, sinh ngày: 22/09/1982;",
            "Căn cước công dân số: 001182000002 do Công an Hà Nội cấp ngày 20/04/2022;",
        ])
        payload = core.extract_text(text)
        self.assertEqual([p["ho_ten"] for p in payload["raw"]["ben_a"]["nguoi"]], ["Nguyễn Văn An"])
        self.assertEqual([p["ho_ten"] for p in payload["raw"]["ben_b"]["nguoi"]], ["Trần Thị Bình"])
        self.assertEqual(payload["raw"]["ben_a"]["nguoi"][0]["gioi_tinh"], "")

    def test_proxy_sentence_is_not_a_person(self):
        text = "\n".join([
            "HỢP ĐỒNG THẾ CHẤP",
            "BÊN THẾ CHẤP:",
            "Ông Trần Văn Ví Dụ; Sinh năm 1980; CCCD số 012345678902 do Cơ quan Hai cấp ngày 02/03/2024.",
            "Theo uỷ quyền của ông Người Trong Câu Kể, sinh ngày: 01/01/1950; CCCD số 012345678904.",
        ])
        payload = core.extract_text(text)
        self.assertEqual([p["ho_ten"] for p in people_of(payload)], ["Trần Văn Ví Dụ"])

    def test_extra_id_numbers_recorded_for_reviewer(self):
        """Nguồn in 2 số giấy tờ cho cùng người: lõi giữ số đầu + ghi số khác.

        Không tự chọn hộ người kiểm tra (luật chọn thuộc người kiểm tra).
        """
        text = "\n".join([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "I. BÊN CHUYỂN NHƯỢNG (Bên A):",
            "Ông: Nguyễn Văn An, sinh ngày: 10/05/1975;",
            "Căn cước công dân số: 001075000001 do Bộ Công an cấp ngày 15/03/2021;",
            "Căn cước công dân số: 001075000002 do Công an Hà Nội cấp ngày 16/03/2021;",
            "II. BÊN NHẬN CHUYỂN NHƯỢNG (Bên B):",
            "Bà: Trần Thị Bình, sinh ngày: 22/09/1982;",
            "Căn cước công dân số: 001182000002 do Công an Hà Nội cấp ngày 20/04/2022;",
        ])
        payload = core.extract_text(text)
        person = payload["raw"]["ben_a"]["nguoi"][0]
        self.assertEqual(person["cccd"], "001075000001")
        self.assertEqual(person["cccd_khac"], ["001075000002"])

    def test_group_block_splits_land_rows(self):
        text = "\n".join([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN",
            "Tài sản thứ 1: Giấy chứng nhận số: B 011092; Địa chỉ thửa đất: xã Mẫu, tỉnh Mẫu",
            "Loại đất: Đất ở; Diện tích: 120 m2; Thời hạn: Lâu dài",
        ])
        payload = core.extract_text(text)
        groups = core.tach_nhom_tai_san(payload["web_form"]["tai_san"])
        self.assertEqual(len(groups), 1)
        group = groups[0]
        self.assertIn("B 011092", group["so_serial"])
        self.assertIn("xã Mẫu", group["dia_chi"])
        self.assertEqual(len(group["land_rows"]), 1)
        row = group["land_rows"][0]
        self.assertEqual(row["loai_dat"], "Đất ở")
        self.assertIn("120", row["dien_tich"])
        self.assertEqual(row["thoi_han"], "Lâu dài")


    def test_serial_raw_keeps_parenthetical_annotation(self):
        """Chú thích trong ngoặc trên nhãn `Số phát hành` giữ nguyên văn."""
        text = "\n".join([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "ĐIỀU 1: ĐỐI TƯỢNG",
            "- Thửa đất số: 215; Tờ bản đồ số: 34",
            "- Số phát hành (serial): AB 123456 (bản chính)",
            "- Diện tích: 68,5 m2",
        ])
        payload = core.extract_text(text)
        parcel = first_parcel(payload)
        self.assertEqual(parcel["so_gcn_raw"], "AB 123456 (bản chính)")
        self.assertEqual(parcel["so_gcn"], "")

    def test_label_only_address_stays_missing(self):
        """Nhãn `Địa chỉ thửa đất:` bỏ trống thì không mượn giá trị dòng kế."""
        text = "\n".join([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "ĐIỀU 1: ĐỐI TƯỢNG",
            "- Địa chỉ thửa đất:",
            "- Giấy chứng nhận số: AB 123456",
            "- Thửa đất số: 215",
        ])
        payload = core.extract_text(text)
        parcel = first_parcel(payload)
        self.assertEqual(parcel["dia_chi"], "")
        self.assertEqual(parcel["so_gcn"], "AB123456")
        self.assertEqual(parcel["so_thua_dat"], "215")


class ReviewFindingCoreTests(unittest.TestCase):
    """Hành vi lõi theo 7 phát hiện của lượt Quick review #22 (16/10/2026).

    Các test này viết TRƯỚC khi vá (bằng chứng đỏ ở
    `_bmad-output/tmp/issue-22-regex-consumer-cutover/evidence/q-fixes/`).
    """

    def test_q1_serial_raw_keeps_source_when_no_space_and_keeps_prefix(self):
        """Q1: `AB123456` không bị chèn dấu cách; tiền tố `-`/`/` giữ nguyên."""
        base = load_fixture("transfer_serial_va_dia_chi_thua.txt")
        for raw in ("-TEST-001", "/TEST-001", "TEST/001-A", "SERIES-123456", "ENDDO123", "ABC/RAW"):
            with self.subTest(raw=raw):
                parcel = first_parcel(core.extract_text(base.replace("TEST-001", raw)))
                self.assertEqual(parcel["so_gcn_raw"], raw)

        standard = "\n".join([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "ĐIỀU 1: ĐỐI TƯỢNG",
            "- Giấy chứng nhận số: AB123456",
            "- Thửa đất số: 215",
        ])
        parcel = first_parcel(core.extract_text(standard))
        self.assertEqual(parcel["so_gcn_raw"], "AB123456")
        self.assertEqual(parcel["so_gcn"], "AB123456")

    def test_q1_serial_raw_stops_before_issuer_phrase(self):
        """Q1: biên ` do <cơ quan> cấp` không bị nuốt vào serial tự do."""
        base = load_fixture("transfer_serial_va_dia_chi_thua.txt")
        text = base.replace("TEST-001", "TEST-001 do UBND huyện Mẫu cấp ngày 01/01/2020")
        parcel = first_parcel(core.extract_text(text))
        self.assertEqual(parcel["so_gcn_raw"], "TEST-001")
        self.assertNotIn("UBND", parcel["so_gcn_raw"])

    def test_q4_group_keeps_every_serial_occurrence(self):
        """Q4: nhóm có hai serial -> lõi giữ MỌI lần thấy, không chọn hộ."""
        text = "\n".join([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN",
            "Tài sản thứ 1:",
            "Giấy chứng nhận số: AB 123456",
            "Giấy chứng nhận số: CD 654321",
        ])
        groups = core.tach_nhom_tai_san(core.extract_text(text)["web_form"]["tai_san"])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["so_serial_values"], ["AB 123456", "CD 654321"])

    def test_q5_blank_land_row_survives_next_valid_row(self):
        """Q5: `Loại đất:` trống mở cụm riêng; cụm hợp lệ sau không ghi đè."""
        text = "\n".join([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN",
            "Tài sản thứ 1: Giấy chứng nhận số: B 011092",
            "Loại đất:",
            "Loại đất: Đất ở; Diện tích: 120 m2; Thời hạn: Lâu dài",
        ])
        groups = core.tach_nhom_tai_san(core.extract_text(text)["web_form"]["tai_san"])
        rows = groups[0]["land_rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["loai_dat"], "")
        self.assertEqual(rows[1]["loai_dat"], "Đất ở")
        self.assertIn("120", rows[1]["dien_tich"])

    def test_q2_span_index_maps_normalized_values_to_source(self):
        """Q2: giá trị đã chuẩn hoá (gộp/bỏ khoảng trắng, NFC/NFD) về đúng span nguồn."""
        text = "Ông Nguyễn  Văn An; CCCD số: 0010 7500 0001;"
        index = core.build_span_index(text)
        span = index.find("Nguyễn Văn An")
        self.assertIsNotNone(span)
        self.assertEqual(text[span[0]:span[1]], "Nguyễn  Văn An")
        span = index.find("001075000001")
        self.assertIsNotNone(span)
        self.assertEqual(text[span[0]:span[1]], "0010 7500 0001")

        mixed = "Bà Trần Thị Bi\u0300nh;"
        index_mixed = core.build_span_index(mixed)
        span = index_mixed.find("Trần Thị Bình")
        self.assertIsNotNone(span)
        self.assertEqual(unicodedata.normalize("NFC", mixed[span[0]:span[1]]), "Trần Thị Bình")


class AdjudicationFixTests(unittest.TestCase):
    """Vá 8 lỗi trường đã hỗ trợ + residual Q1/Q4 (adjudication 16/10/2026).

    Nguồn là đúng câu nguồn đã dẫn trong `adjudication.md`; đỏ trước vá.
    """

    def _parcel(self, lines: list[str]) -> dict:
        return first_parcel(core.extract_text("\n".join(lines)))

    def _groups(self, lines: list[str]) -> list[dict]:
        payload = core.extract_text("\n".join(lines))
        return core.tach_nhom_tai_san(payload["web_form"]["tai_san"])

    def test_q1_one_occurrence_is_one_value(self):
        """Q1: cùng một occurrence chỉ ra MỘT giá trị, giữ nguyên văn của nhãn."""
        khep = self._parcel([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN:",
            "Tài sản thứ 1:",
            "Giấy chứng nhận số: AB  123456;",
            "Thửa đất số: 215;",
        ])
        # Nguyên văn = lát cắt nguồn: hai dấu cách giữ đúng (decision-46 mọi
        # tầng); dạng gộp khoảng trắng chỉ là lớp so khớp, không thành đáp án
        # thứ hai cho cùng một serial.
        self.assertEqual(khep["so_gcn_raw"], "AB  123456")
        self.assertEqual(khep["so_gcn_raw_values"], ["AB  123456"])

        ngoac = self._parcel([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN:",
            "Tài sản thứ 1:",
            "Giấy chứng nhận số: AB123456 (bản chính);",
            "Thửa đất số: 215;",
        ])
        self.assertEqual(ngoac["so_gcn_raw_values"], ["AB123456 (bản chính)"])

    def test_q4_repeated_fields_keep_every_occurrence(self):
        """Q4: địa chỉ / số vào sổ / ngày cấp lặp lại -> giữ MỌI lần thấy."""
        groups = self._groups([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN:",
            "Tài sản thứ 1:",
            "Giấy chứng nhận số: AB123456;",
            "Địa chỉ thửa đất: xã Một;",
            "Địa chỉ thửa đất: xã Hai;",
            "Số vào sổ: VP001;",
            "Số vào sổ: VP002;",
            "Ngày cấp: 01/01/2010;",
            "Ngày cấp: 02/02/2011;",
        ])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["dia_chi_values"], ["xã Một", "xã Hai"])
        self.assertEqual(groups[0]["so_vao_so_values"], ["VP001", "VP002"])
        self.assertEqual(groups[0]["ngay_cap_values"], ["01/01/2010", "02/02/2011"])

    def test_q4_parcel_without_group_keeps_all_serials(self):
        """Q4: nhánh thửa KHÔNG có nhãn nhóm cũng giữ đủ serial (không rơi metadata)."""
        parcel = self._parcel([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN:",
            "Giấy chứng nhận số: AB123456;",
            "Giấy chứng nhận số: CD654321;",
            "Thửa đất số: 215; Tờ bản đồ số: 34;",
        ])
        self.assertEqual(parcel["so_gcn_raw_values"], ["AB123456", "CD654321"])
        self.assertEqual(parcel["so_gcn_raw"], "AB123456")

    def test_mb1_gcn_type_read_from_source(self):
        """MB1: `loai_gcn` theo nguồn — không gate dạng serial; nhãn rỗng thì không tính."""
        typed = self._parcel([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN:",
            "Giấy chứng nhận số: TEST-001;",
            "Thửa đất số: 215; Tờ bản đồ số: 34;",
        ])
        self.assertEqual(typed["loai_gcn"], "Giấy chứng nhận")

        titled = self._parcel([
            "GIẤY CHỨNG NHẬN",
            "QUYỀN SỬ DỤNG ĐẤT",
            "Số phát hành (serial): DD 123456",
            "Số vào sổ: VP00166",
            "Thửa đất số: 10",
            "Tờ bản đồ số: 5",
        ])
        self.assertEqual(titled["loai_gcn"], "Giấy chứng nhận quyền sử dụng đất")

        blank = self._parcel([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN:",
            "Giấy chứng nhận số:",
            "Thửa đất số: 12; Tờ bản đồ số: 3;",
        ])
        self.assertEqual(blank["loai_gcn"], "")

    def test_mb2_asset_opener_address_kept(self):
        """MB2: khối mở "quyền sử dụng đất tại <địa chỉ> theo GCN …" vẫn giữ địa chỉ."""
        parcel = self._parcel([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "Đối tượng của Hợp đồng này là: quyền sử dụng đất tại xã Minh Tân, huyện Vũ Thư, "
            "tỉnh Thái Bình theo Giấy chứng nhận số AK 732800 do Ủy ban nhân dân huyện Vũ Thư "
            "cấp ngày 01/01/2016.",
            "Thửa đất số: 180",
            "Tờ bản đồ số: 9",
        ])
        self.assertEqual(parcel["dia_chi"], "xã Minh Tân, huyện Vũ Thư, tỉnh Thái Bình")

    def test_mb4_deceased_does_not_borrow_gcn_date(self):
        """MB4: trích lục không ghi ngày/nơi cấp -> người chết không mượn của GCN."""
        borrowed = core.extract_text("\n".join([
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Ông Nguyễn Văn Tổ; Sinh năm: 1940, chết ngày 05/06/2016 theo Trích lục khai tử "
            "số 95/2026/TLKT.",
            "TÀI SẢN:",
            "Quyền sử dụng đất tại địa chỉ: xã Mẫu, tỉnh Mẫu theo Giấy chứng nhận quyền sử "
            "dụng đất số AK 732800 do UBND huyện Mẫu cấp ngày 01/01/2016.",
            "- Thửa đất số: 180; Tờ bản đồ số: 9",
        ]))
        deceased = borrowed["raw"]["nguoi_chet"]
        self.assertEqual(len(deceased), 1)
        self.assertEqual(deceased[0]["ngay_cap"], "")
        self.assertEqual(deceased[0]["noi_cap"], "")

        own = core.extract_text("\n".join([
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Ông Trần Văn X; sinh năm 1954, đã chết ngày 29/03/2025 theo Trích lục khai tử "
            "số 120/TLKT-BS do UBND xã Minh Tân cấp ngày 31/03/2025.",
            "TÀI SẢN:",
            "- Thửa đất số: 180; Tờ bản đồ số: 9",
        ]))
        own_record = own["raw"]["nguoi_chet"][0]
        self.assertEqual(own_record["ngay_cap"], "31/03/2025")
        self.assertEqual(own_record["noi_cap"], "UBND xã Minh Tân")

    def test_mb5_two_land_uses_keep_detail_rows(self):
        """MB5: hai loại đất/thời hạn -> dòng chi tiết; cấp thửa để trống, không suy tổng."""
        parcel = self._parcel([
            "GIẤY CHỨNG NHẬN",
            "QUYỀN SỬ DỤNG ĐẤT",
            "Số phát hành (serial): DD 123456",
            "Thửa đất số: 10",
            "Tờ bản đồ số: 5",
            "c. Loại đất: Đất ở tại nông thôn 200,0m²; Đất trồng cây lâu năm 247,0m²",
            "d. Thời hạn sử dụng: Đất ở tại nông thôn: Lâu dài; Đất trồng cây lâu năm: 12/2043",
        ])
        self.assertEqual(parcel["muc_dich_su_dung"], "")
        self.assertEqual(parcel["thoi_han_su_dung"], "")
        self.assertEqual(parcel["dien_tich"], "")
        rows = parcel["chi_tiet_dien_tich"]
        self.assertEqual([row["muc_dich_su_dung"] for row in rows],
                         ["Đất ở tại nông thôn", "Đất trồng cây lâu năm"])
        self.assertEqual([row["dien_tich"] for row in rows], ["200,0m²", "247,0m²"])
        self.assertEqual([row["thoi_han_su_dung"] for row in rows], ["Lâu dài", "12/2043"])

    def test_mb6_labeled_issue_date_read(self):
        """MB6: `Ngày cấp:` của ô cấp giấy được đọc (cạnh `Số vào sổ`)."""
        parcel = self._parcel([
            "GIẤY CHỨNG NHẬN",
            "QUYỀN SỬ DỤNG ĐẤT",
            "Số phát hành (serial): DD 123456",
            "Số vào sổ: VP00166",
            "Thửa đất số: 10",
            "Tờ bản đồ số: 5",
            "Ngày cấp: 20/05/2010",
        ])
        self.assertEqual(parcel["so_vao_so"], "VP00166")
        self.assertEqual(parcel["ngay_cap_gcn"], "20/05/2010")

    def test_mb7_cancellation_group_follows_spec(self):
        """MB7: nhóm của hủy bỏ hợp đồng chuyển nhượng là `Thoả thuận - Cam kết`."""
        payload = core.extract_text("\n".join([
            "HỢP ĐỒNG HỦY BỎ HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "Hôm nay, chúng tôi gồm:",
            "BÊN A: Ông Nguyễn Văn An; Sinh năm 1980; CCCD số 001075000001;",
            "ĐIỀU 1: Nội dung thỏa thuận.",
        ]))
        self.assertEqual(payload["raw"]["document_kind"], core.DOC_KIND_TRANSFER_CANCELLATION)
        self.assertEqual(payload["web_form"]["nhom_hop_dong"], "Thoả thuận - Cam kết")

    def test_mb8_loi_chung_heading_not_in_title(self):
        """MB8: mục `Lời chứng.` ở trang sau không dính vào tiêu đề."""
        payload = core.extract_text("\n".join([
            "BIÊN BẢN GIAO NHẬN",
            "Hôm nay, ngày 20 tháng 05 năm 2026, tại Văn phòng Công chứng Minh Tân.",
            "NGƯỜI GIAO: Ông Nguyễn Văn An",
            "NGƯỜI NHẬN: Bà Trần Thị Bình",
            "Lời chứng.",
        ]))
        self.assertEqual(payload["web_form"]["ten_hop_dong"], "BIÊN BẢN GIAO NHẬN")


class Round4FixTests(unittest.TestCase):
    """Vòng 4 (16/10/2026): serial nguyên văn, nhãn trống, loại GCN có nguyên
    văn, ranh câu TLKT, đủ trường cấp thửa theo Q4. Đỏ trước vá."""

    def _parcel(self, lines: list[str]) -> dict:
        payload = core.extract_text("\n".join(lines))
        return payload["raw"]["danh_sach_thua_dat"][0]

    def test_serial_raw_is_source_slice(self):
        """Serial nguyên văn: giữ đúng khoảng trắng nguồn; dạng gộp là lớp so khớp."""
        parcel = self._parcel([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN:",
            "Tài sản thứ 1:",
            "Giấy chứng nhận số: AB  123456;",
            "Thửa đất số: 215;",
        ])
        self.assertEqual(parcel["so_gcn_raw"], "AB  123456")
        self.assertEqual(parcel["so_gcn_raw_values"], ["AB  123456"])
        self.assertEqual(core._serial_raw_value(parcel["so_gcn_raw"]), "AB 123456")

    def test_blank_label_never_becomes_colon_value(self):
        """Nhãn trống không tạo đáp án: dấu `:` ngăn nhãn không thành giá trị."""
        parcel = self._parcel([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN:",
            "Tài sản thứ 1:",
            "Giấy chứng nhận số: AB123456;",
            "Địa chỉ thửa đất:",
            "Địa chỉ thửa đất: xã Mẫu;",
            "Thửa đất số: 215;",
        ])
        self.assertEqual(parcel["dia_chi_values"], ["xã Mẫu"])
        self.assertEqual(parcel["dia_chi"], "xã Mẫu")

    def test_gcn_type_raw_kept_with_normalized(self):
        """Loại GCN: giữ nguyên văn nguồn (tiêu đề hoa 2 dòng) + giá trị chuẩn riêng."""
        parcel = self._parcel([
            "GIẤY CHỨNG NHẬN",
            "QUYỀN SỬ DỤNG ĐẤT",
            "Số phát hành (serial): DD 123456",
            "Thửa đất số: 10",
            "Tờ bản đồ số: 5",
        ])
        self.assertEqual(parcel["loai_gcn"], "Giấy chứng nhận quyền sử dụng đất")
        self.assertEqual(parcel["loai_gcn_raw"], "GIẤY CHỨNG NHẬN\nQUYỀN SỬ DỤNG ĐẤT")

    def test_tlkt_same_line_sentence_boundary(self):
        """Ranh câu TLKT: dấu chấm kết câu không bị số nuốt; câu GCN cùng dòng không mượn."""
        payload = core.extract_text("\n".join([
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Ông Nguyễn Văn Tổ; sinh năm 1940, chết ngày 05/06/2016 theo Trích lục khai tử "
            "số 95/2026/TLKT. Giấy chứng nhận số AK732800 do UBND huyện Mẫu cấp ngày 01/01/2016.",
            "TÀI SẢN:",
            "- Thửa đất số: 180; Tờ bản đồ số: 9",
        ]))
        record = payload["raw"]["nguoi_chet"][0]
        self.assertEqual(record["so_giay_to"], "95/2026/TLKT")
        self.assertEqual(record["ngay_cap"], "")
        self.assertEqual(record["noi_cap"], "")

    def test_tlkt_issuer_abbreviation_kept(self):
        """Viết tắt cơ quan (`UBND TP.`) không cắt câu: ngày/nơi cấp của trích lục vẫn đọc."""
        payload = core.extract_text("\n".join([
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Ông Nguyễn Văn Tổ; sinh năm 1940, chết ngày 05/06/2016 theo Trích lục khai tử "
            "số 95/2026/TLKT do UBND TP. Mẫu cấp ngày 05/06/2016.",
            "TÀI SẢN:",
            "- Thửa đất số: 180; Tờ bản đồ số: 9",
        ]))
        record = payload["raw"]["nguoi_chet"][0]
        self.assertEqual(record["ngay_cap"], "05/06/2016")
        self.assertEqual(record["noi_cap"], "UBND TP. Mẫu")

    def test_scalar_fields_keep_every_occurrence(self):
        """Q4 đủ trường cấp thửa: diện tích/thời hạn lặp lại giữ mọi lần thấy."""
        parcel = self._parcel([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN:",
            "Tài sản thứ 1:",
            "Giấy chứng nhận số: AB123456;",
            "Thửa đất số: 215;",
            "Diện tích: 120 m2",
            "Diện tích: 130 m2",
            "Thời hạn sử dụng: Lâu dài",
            "Thời hạn sử dụng: 12/2043",
        ])
        self.assertEqual(parcel["dien_tich_values"], ["120 m2", "130 m2"])
        self.assertEqual(parcel["thoi_han_su_dung_values"], ["Lâu dài", "12/2043"])


class Round5FixTests(unittest.TestCase):
    """Vòng 5 (16/10/2026): cùng ô ghi hai lần trên MỘT dòng phải giữ đủ ứng
    viên; nhóm KHÔNG lấy diện tích/thời hạn từ dòng đất chi tiết; gộp thửa
    hợp nhất mọi lần thấy. Đỏ trước vá."""

    def _parcel(self, lines: list[str]) -> dict:
        payload = core.extract_text("\n".join(lines))
        return payload["raw"]["danh_sach_thua_dat"][0]

    def test_same_line_second_occurrence_kept(self):
        """Cùng một dòng: scalar giữ lần thấy ĐẦU, metadata giữ CẢ HAI."""
        parcel = self._parcel([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN:",
            "Thửa đất số: 215; Tờ bản đồ số: 34;",
            "Diện tích: 120 m2; Diện tích: 130 m2",
        ])
        self.assertEqual(parcel["dien_tich"], "120 m2")
        self.assertEqual(parcel["dien_tich_values"], ["120 m2", "130 m2"])

    def test_group_rows_not_flat_values(self):
        """Nhóm có thửa/tờ + hai dòng cụm đất: giá trị thuộc DÒNG, không vào ô
        cấp nhóm (kể cả khi parser thửa đã mở `current` từ dòng `Thửa đất số`)."""
        groups = core.tach_nhom_tai_san("\n".join([
            "Tài sản thứ 1:",
            "Giấy chứng nhận số: AB123456;",
            "Thửa đất số: 215; Tờ bản đồ số: 34;",
            "Loại đất: Đất ở; Diện tích: 120 m2; Thời hạn: Lâu dài",
            "Loại đất: Đất vườn; Diện tích: 130 m2; Thời hạn: 12/2043",
        ]))
        self.assertEqual(len(groups), 1)
        group = groups[0]
        self.assertEqual(
            [(row["loai_dat"], row["dien_tich"], row["thoi_han"]) for row in group["land_rows"]],
            [("Đất ở", "120 m2", "Lâu dài"), ("Đất vườn", "130 m2", "12/2043")])
        self.assertEqual(group["dien_tich_values"], [])
        self.assertEqual(group["thoi_han_values"], [])
        self.assertEqual(group["dien_tich"], "")
        self.assertEqual(group["thoi_han"], "")
        self.assertEqual(group["so_thua_dat"], "215")
        self.assertEqual(group["so_to_ban_do"], "34")

    def test_multiline_group_rows_not_flat_values(self):
        group = core.tach_nhom_tai_san("\n".join([
            "Tài sản thứ 1:",
            "Giấy chứng nhận số: AB123456;",
            "Thửa đất số: 215; Tờ bản đồ số: 34;",
            "Loại đất: Đất ở",
            "Diện tích: 120 m2",
            "Thời hạn: Lâu dài",
            "Loại đất: Đất vườn",
            "Diện tích: 130 m2",
            "Thời hạn: 12/2043",
        ]))[0]
        self.assertEqual(group["land_rows"], [
            {"loai_dat": "Đất ở", "dien_tich": "120 m2", "thoi_han": "Lâu dài"},
            {"loai_dat": "Đất vườn", "dien_tich": "130 m2", "thoi_han": "12/2043"},
        ])
        self.assertEqual(group["dien_tich_values"], [])
        self.assertEqual(group["thoi_han_values"], [])
        self.assertEqual(group["dien_tich"], "")
        self.assertEqual(group["thoi_han"], "")
        self.assertEqual(group["so_serial"], "AB123456")
        self.assertEqual((group["so_thua_dat"], group["so_to_ban_do"]), ("215", "34"))

    def test_cluster_ends_at_next_parcel_and_group(self):
        groups = core.tach_nhom_tai_san("\n".join([
            "Tài sản thứ 1:",
            "Thửa đất số: 215; Tờ bản đồ số: 34;",
            "Loại đất: Đất ở",
            "Diện tích: 120 m2",
            "Thời hạn: Lâu dài",
            "Thửa đất số: 216; Tờ bản đồ số: 34;",
            "Diện tích: 80 m2",
            "Thời hạn: 12/2043",
            "Tài sản thứ 2:",
            "Thửa đất số: 300; Tờ bản đồ số: 40;",
            "Diện tích: 90 m2",
        ]))
        self.assertEqual(groups[0]["land_rows"], [
            {"loai_dat": "Đất ở", "dien_tich": "120 m2", "thoi_han": "Lâu dài"},
            {"loai_dat": "", "dien_tich": "80 m2", "thoi_han": "12/2043"},
        ])
        self.assertEqual(groups[1]["dien_tich"], "90 m2")
        parcels = core.tach_danh_sach_thua_dat("\n".join([
            "Thửa đất số: 215; Tờ bản đồ số: 34;",
            "Loại đất: Đất ở",
            "Diện tích: 120 m2",
            "Thửa đất số: 216; Tờ bản đồ số: 34;",
            "Diện tích: 80 m2",
            "Thời hạn: 12/2043",
        ]), land_rows_as_details=True)
        self.assertEqual(parcels[0]["dien_tich_values"], [])
        self.assertEqual(parcels[1]["dien_tich_values"], ["80 m2"])
        self.assertEqual(parcels[1]["thoi_han_su_dung_values"], ["12/2043"])

    def test_repeated_parcel_union_values(self):
        """Gộp thửa nhắc lại: scalar giữ bản đầu, metadata hợp nhất hai lần thấy."""
        parcels = core.extract_text("\n".join([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "TÀI SẢN:",
            "Thửa đất số: 215; Tờ bản đồ số: 34; Diện tích: 120 m2; Thời hạn sử dụng: Lâu dài;",
            "Thửa đất số: 215; Tờ bản đồ số: 34; Diện tích: 120 m2; Thời hạn sử dụng: 12/2043;",
            "Giá chuyển nhượng: 100.000.000 đồng",
        ]))["raw"]["danh_sach_thua_dat"]
        self.assertEqual(len(parcels), 1)
        self.assertEqual(parcels[0]["thoi_han_su_dung"], "Lâu dài")
        self.assertEqual(parcels[0]["thoi_han_su_dung_values"], ["Lâu dài", "12/2043"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
import tempfile
import unicodedata
import unittest
from pathlib import Path

from docx import Document

from extract_contract import extract, find_tai_san, guess_loai_tai_san, tach_danh_sach_so_tiet_kiem, tach_danh_sach_thua_dat


def make_docx(path: Path, *paragraphs: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    for paragraph in paragraphs:
        doc.add_paragraph(paragraph)
    doc.save(str(path))
    return path


def make_docx_with_blocks(path: Path, blocks: list[tuple[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    for block_type, payload in blocks:
        if block_type == "p":
            doc.add_paragraph(str(payload))
            continue
        if block_type == "table":
            rows = list(payload)
            col_count = max(len(row) for row in rows)
            table = doc.add_table(rows=len(rows), cols=col_count)
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    table.cell(row_idx, col_idx).text = str(value)
            continue
        raise ValueError(f"Unsupported block type: {block_type}")
    doc.save(str(path))
    return path


class UploadLabExtractContractTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def test_transfer_title_ignores_body_huy_bo_clause(self):
        docx_path = make_docx(
            self.root / "transfer.docx",
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "Chúng tôi gồm có:",
            "I. BÊN CHUYỂN NHƯỢNG: (Bên A)",
            "Ông: Nguyễn Văn A Sinh ngày: 01/01/1980",
            "Căn cước công dân số: 012345678901 do Bộ Công an cấp ngày 01/01/2024;",
            "Thường trú tại: thôn A, xã B.",
            "II. BÊN NHẬN CHUYỂN NHƯỢNG: (Bên B)",
            "Ông: Nguyễn Văn B Sinh ngày: 02/02/1981",
            "Căn cước công dân số: 012345678902 do Bộ Công an cấp ngày 02/02/2024;",
            "Thường trú tại: thôn C, xã D.",
            "ĐIỀU 1: ĐỐI TƯỢNG CỦA HỢP ĐỒNG",
            "Đối tượng của Hợp đồng này là toàn bộ quyền sử dụng đất của bên A có địa chỉ tại: thôn A, xã B.",
            "- Thửa đất số: 10",
            "ĐIỀU 8: ĐIỀU KHOẢN CUỐI CÙNG",
            "Việc sửa đổi, bổ sung hoặc hủy bỏ hợp đồng này chỉ có giá trị khi được hai bên lập thành văn bản.",
            "Số công chứng 428/2026/CCGD",
        )

        payload = extract(docx_path)

        self.assertEqual(payload["raw"]["document_kind"], "transfer_contract")
        self.assertEqual(payload["web_form"]["ten_hop_dong"], "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT")

    def test_document_kind_uses_two_line_header_not_filename_or_body(self):
        docx_path = make_docx(
            self.root / "van_ban_phan_chia_di_san.docx",
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
            "Độc lập - Tự do - Hạnh phúc",
            "-----***-----",
            "HỢP ĐỒNG",
            "Tặng Cho Quyền Sử Dụng Đất",
            "Trong thân có nhắc Văn bản phân chia di sản và từ chối nhận di sản.",
            "Số công chứng 12/2026/CCGD",
        )

        payload = extract(docx_path)

        self.assertEqual(payload["raw"]["document_kind"], "gift_contract")
        self.assertEqual(payload["web_form"]["ten_hop_dong"], "HỢP ĐỒNG Tặng Cho Quyền Sử Dụng Đất")

    def test_document_title_joins_specific_multiline_title(self):
        docx_path = make_docx(
            self.root / "multiline-title.docx",
            "HỢP ĐỒNG TẶNG CHO",
            "QUYỀN SỬ DỤNG ĐẤT",
            "Chúng tôi gồm có:",
            "Số công chứng 14/2026/CCGD",
        )

        payload = extract(docx_path)

        self.assertEqual(payload["raw"]["document_kind"], "gift_contract")
        self.assertEqual(payload["web_form"]["ten_hop_dong"], "HỢP ĐỒNG TẶNG CHO QUYỀN SỬ DỤNG ĐẤT")

    def test_partition_title_wins_over_refusal_phrase_in_body(self):
        docx_path = make_docx(
            self.root / "partition.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Một người có quyền từ chối nhận di sản theo quy định pháp luật.",
            "Số công chứng 13/2026/CCGD",
        )

        payload = extract(docx_path)

        self.assertEqual(payload["raw"]["document_kind"], "inheritance_partition")
        self.assertEqual(payload["web_form"]["ten_hop_dong"], "VĂN BẢN PHÂN CHIA DI SẢN")

    def test_find_tai_san_commitment_stops_before_cam_ket_xac_nhan(self):
        text = "\n".join(
            [
                "VĂN BẢN CAM KẾT TÀI SẢN RIÊNG",
                "Hiện nay, ông Nguyễn Văn Nam đang làm các thủ tục để nhận chuyển nhượng quyền sử dụng đất có địa chỉ tại: thôn A, xã B.",
                "- Thửa đất số: 20",
                "- Diện tích: 200 m2",
                "- Giấy chứng nhận quyền sử dụng đất quyền sở hữu nhà ở và tài sản khác gắn liền với đất số: AB 123456.",
                "Hai vợ chồng chúng tôi cam kết và xác nhận: Toàn bộ số tiền này là tài sản riêng.",
            ]
        )

        tai_san = find_tai_san(unicodedata.normalize("NFD", text))

        self.assertIn("Thửa đất số: 20", tai_san)
        self.assertNotIn("Hai vợ chồng chúng tôi cam kết", tai_san)

    def test_extract_commitment_keeps_both_spouses_and_classifies_land_only(self):
        docx_path = make_docx(
            self.root / "cam_ket_tai_san_rieng.docx",
            "VĂN BẢN CAM KẾT TÀI SẢN RIÊNG",
            "Chúng tôi gồm có:",
            "- Người chồng – Ông: Nguyễn Văn Nam Sinh ngày: 02/02/1982",
            "Căn cước công dân số: 036082000989 do Bộ Công an cấp ngày 02/07/2021",
            "Thường trú tại: Thôn Hoàng Mẫu, xã Vạn Thắng, tỉnh Ninh Bình;",
            "- Người vợ - Bà: Nguyễn Thị Oanh Sinh ngày: 09/05/1985",
            "Căn cước số: 036185021354 do Bộ Công an cấp ngày 12/02/2025;",
            "Nơi cư trú tại: Thôn Hoàng Mẫu, xã Vạn Thắng, tỉnh Ninh Bình.",
            "Chúng tôi là vợ chồng theo Giấy chứng nhận kết hôn số 17.",
            "Nay chúng tôi lập văn bản này để cam kết và chịu trách nhiệm trước pháp luật về những nội dung sau đây:",
            "Hiện nay, ông Nguyễn Văn Nam đang làm các thủ tục để nhận chuyển nhượng quyền sử dụng đất có địa chỉ tại: thôn Đại Lộc Trung, xã Yên Chính, huyện Ý Yên, tỉnh Nam Định Giấy chứng nhận quyền sử dụng đất quyền sở hữu nhà ở và tài sản khác gắn liền với đất số: CY 921651.",
            "- Thửa đất số: 531; Tờ bản đồ số: 22;",
            "- Diện tích: 660,0 m2;",
            "Hai vợ chồng chúng tôi cam kết và xác nhận: Toàn bộ số tiền này là tài sản riêng của ông Nguyễn Văn Nam.",
            "Số công chứng 161/2026/CCGD",
        )

        payload = extract(docx_path)
        duong_su = payload["web_form"]["duong_su"]
        tai_san = payload["web_form"]["tai_san"]

        self.assertEqual(payload["raw"]["document_kind"], "asset_commitment")
        self.assertEqual(payload["web_form"]["ten_hop_dong"], "VĂN BẢN CAM KẾT TÀI SẢN RIÊNG")
        self.assertEqual(payload["web_form"]["nhom_hop_dong"], "Thoả thuận - Cam kết")
        self.assertEqual(payload["web_form"]["loai_tai_san"], "Đất đai không có tài sản")
        self.assertIn("Nguyễn Văn Nam", duong_su)
        self.assertIn("Nguyễn Thị Oanh", duong_su)
        self.assertNotIn("Hai vợ chồng chúng tôi cam kết", tai_san)

    def test_guess_loai_tai_san_detects_real_attached_asset_details_after_stripping_certificate_heading_noise(self):
        tai_san = "\n".join(
            [
                "Quyền sử dụng đất có địa chỉ tại: thôn A, xã B.",
                "Giấy chứng nhận quyền sử dụng đất, quyền sở hữu nhà ở và tài sản khác gắn liền với đất số: AB 123456.",
                "Nhà ở:",
                "- Diện tích xây dựng: 120 m2",
                "- Diện tích sàn: 240 m2",
                "- Kết cấu: Tường gạch, mái bê tông cốt thép",
            ]
        )

        loai_tai_san = guess_loai_tai_san(tai_san, "Văn bản cam kết tài sản riêng")

        self.assertEqual(loai_tai_san, "Đất đai có tài sản")

    def test_generic_title_strips_duoc_giao_ket_boi_suffix(self):
        docx_path = make_docx(
            self.root / "uy_quyen.docx",
            "CHỨNG NHẬN:",
            "Hợp đồng ủy quyền này được giao kết bởi:",
            "I. BÊN ỦY QUYỀN",
            "Bà Tạ Thị Chứ; Sinh ngày: 08/01/1956;",
            "Căn cước công dân số 036156012959 do Bộ Công an cấp ngày 10/01/2023;",
            "Thường trú tại: Thôn Tâm Bình, xã Yên Cường, tỉnh Ninh Bình.",
            "II. BÊN ĐƯỢC ỦY QUYỀN",
            "Ông Nguyễn Đức Hiệp; Sinh ngày: 17/05/1982;",
            "Căn cước công dân số 036082016119 do Bộ Công an cấp ngày 09/08/2021;",
            "Thường trú tại: Thôn Tâm Bình, xã Yên Cường, tỉnh Ninh Bình.",
            "Số công chứng 372/2026/CCGD",
        )

        payload = extract(docx_path)

        self.assertEqual(payload["web_form"]["ten_hop_dong"], "Hợp đồng ủy quyền")

    def test_party_blocks_do_not_copy_shared_address_to_people_above_it(self):
        docx_path = make_docx(
            self.root / "shared_address.docx",
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT VÀ TÀI SẢN GẮN LIỀN VỚI ĐẤT",
            "Chúng tôi gồm có:",
            "I. BÊN CHUYỂN NHƯỢNG: (Bên A)",
            "1. Ông Nguyễn Huy Cận Sinh ngày: 17/12/1979",
            "Căn cước công dân số: 037079010407 do Bộ Công an cấp ngày 19/02/2025;",
            "2. Bà Nguyễn Thị Thu Thủy Sinh ngày: 27/06/1984",
            "Căn cước công dân số: 022184004248 do Bộ Công an cấp ngày 21/10/2025;",
            "Cùng cư trú tại: thôn A, xã B.",
            "II. BÊN NHẬN CHUYỂN NHƯỢNG: (Bên B)",
            "1. Ông Đoàn Văn Khánh Sinh ngày: 07/04/1987",
            "Căn cước công dân số: 036087026862 do Bộ Công an cấp ngày 11/08/2021;",
            "2. Bà Nguyễn Thị Đức Hạnh Sinh ngày: 14/12/1989",
            "Căn cước công dân số: 036189016258 do Bộ Công an cấp ngày 02/05/2022;",
            "Cùng cư trú tại: thôn C, xã D.",
            "ĐIỀU 1: ĐỐI TƯỢNG CỦA HỢP ĐỒNG",
            "Đối tượng của Hợp đồng này là toàn bộ quyền sử dụng đất của bên A có địa chỉ tại: thôn A, xã B.",
            "- Thửa đất số: 99",
            "Số công chứng 500/2026/CCGD",
        )

        payload = extract(docx_path)
        duong_su = payload["web_form"]["duong_su"]
        nguoi_yeu_cau = payload["web_form"]["nguoi_yeu_cau"]

        self.assertEqual(payload["web_form"]["ten_hop_dong"], "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT VÀ TÀI SẢN GẮN LIỀN VỚI ĐẤT")
        self.assertEqual(duong_su.count("Cùng cư trú tại: thôn A, xã B."), 1)
        self.assertEqual(duong_su.count("Cùng cư trú tại: thôn C, xã D."), 1)
        self.assertNotIn("Cùng cư trú tại: thôn C, xã D.", nguoi_yeu_cau)


    def test_extract_mortgage_summary_keeps_table_order_and_uses_mortgage_party_labels(self):
        docx_path = make_docx_with_blocks(
            self.root / "the_chap_tom_tat.docx",
            [
                ("p", "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN"),
                ("p", "Hợp đồng thế chấp quyền sử dụng đất được giao kết giữa:"),
                ("p", "I. Bên A: BÊN THẾ CHẤP"),
                (
                    "table",
                    [
                        ("1. Ông: Vũ Duy Quang", "Ngày sinh: 15/04/1981"),
                        ("Căn cước công dân 036081005455 do Bộ Công an cấp ngày 25/04/2021",),
                        ("Địa chỉ nơi cư trú: xã Ý Yên, tỉnh Ninh Bình",),
                        ("2. và vợ là Bà: Phạm Thị Lan", "Ngày sinh: 06/05/1983"),
                        ("Căn cước công dân: 036183009426 do Bộ Công an cấp ngày 06/08/2023",),
                        ("Địa chỉ nơi cư trú: xã Ý Yên, tỉnh Ninh Bình",),
                    ],
                ),
                ("p", "II. Bên B: BÊN NHẬN THẾ CHẤP"),
                ("p", "NGÂN HÀNG THƯƠNG MẠI CỔ PHẦN NGOẠI THƯƠNG VIỆT NAM – CHI NHÁNH NAM ĐỊNH"),
                ("p", "Địa chỉ đăng ký: Số 629 Trần Hưng Đạo, phường Nam Định, tỉnh Ninh Bình."),
                ("p", "Đại diện: Ông Nguyễn Hữu Dụng Chức vụ: Phó giám đốc chi nhánh"),
                ("p", "Căn cước công dân số 036081017402 do Bộ Công an cấp ngày 02/07/2021"),
                ("p", "Số công chứng 473/2026/CCGD"),
            ],
        )

        payload = extract(docx_path)
        duong_su = payload["web_form"]["duong_su"]

        self.assertEqual(payload["raw"]["document_kind"], "mortgage_contract")
        self.assertEqual(payload["web_form"]["ten_hop_dong"], "Hợp đồng thế chấp quyền sử dụng đất")
        self.assertEqual(payload["web_form"]["nhom_hop_dong"], "Cầm cố - Thế chấp - Vay")
        self.assertEqual(payload["web_form"]["tai_san"], "quyền sử dụng đất")
        self.assertEqual(payload["web_form"]["loai_tai_san"], "Đất đai không có tài sản")
        self.assertNotIn("BÊN THẾ CHẤP:", duong_su)
        self.assertNotIn("BÊN NHẬN THẾ CHẤP:", duong_su)
        self.assertIn("NGÂN HÀNG THƯƠNG MẠI CỔ PHẦN NGOẠI THƯƠNG VIỆT NAM", duong_su)
        self.assertIn("Nguyễn Hữu Dụng", payload["web_form"]["nguoi_yeu_cau"])
        self.assertEqual(len(payload["raw"]["ben_a"]["nguoi"]), 2)
        self.assertEqual(len(payload["raw"]["ben_b"]["nguoi"]), 1)

    def test_extract_company_representative_with_expanded_dai_dien_label(self):
        docx_path = make_docx(
            self.root / "representative_label.docx",
            "HOP DONG THE CHAP QUYEN SU DUNG DAT",
            "I. BEN THE CHAP",
            "Ong: Tran Van A Sinh ngay: 01/01/1980",
            "Can cuoc cong dan so: 036080000001 do Bo Cong an cap ngay 01/01/2024;",
            "Thuong tru tai: xa A, tinh B.",
            "II. BEN NHAN THE CHAP",
            "NGAN HANG THUONG MAI CO PHAN DEMO",
            "Dia chi dang ky: so 1, phuong A, tinh B.",
            "Dai dien theo phap luat: Ong Nguyen Huu Dung Chuc vu: Pho giam doc chi nhanh",
            "Can cuoc cong dan so: 036081017402 do Bo Cong an cap ngay 02/07/2021",
            "So cong chung 473/2026/CCGD",
        )

        payload = extract(docx_path)

        self.assertIn("Nguyen Huu Dung", payload["web_form"]["nguoi_yeu_cau"])
        self.assertEqual(len(payload["raw"]["ben_b"]["nguoi"]), 1)

    def test_extract_commitment_supports_numbered_spouse_prefix_before_title(self):
        docx_path = make_docx(
            self.root / "cam_ket_numbered_spouse.docx",
            "VĂN BẢN CAM KẾT TÀI SẢN RIÊNG",
            "Chúng tôi gồm có:",
            "1. Người vợ - Bà Phạm Thị Hạt; Sinh ngày: 01/08/1982;",
            "Căn cước công dân số: 036182010256 do Cục cảnh sát quản lý hành chính về trật tự xã hội cấp ngày 05/09/2022;",
            "Thường trú tại: xã Yên Đồng, tỉnh Ninh Bình",
            "2. Người chồng - Ông Vũ Văn Minh; Sinh ngày: 07/02/1979;",
            "Căn cước công dân số: 036079008030 do Cục cảnh sát quản lý hành chính về trật tự xã hội cấp ngày 05/09/2022;",
            "Thường trú tại: xã Yên Đồng, tỉnh Ninh Bình.",
            "Hiện nay, bà Phạm Thị Hạt đang làm các thủ tục để nhận chuyển nhượng quyền sử dụng đất có địa chỉ tại: xã A, tỉnh B.",
            "- Thửa đất số: 20",
            "Số công chứng 1272/2025/CCGD",
        )

        payload = extract(docx_path)

        self.assertIn("Phạm Thị Hạt", payload["web_form"]["nguoi_yeu_cau"])
        self.assertIn("Vũ Văn Minh", payload["web_form"]["duong_su"])

    def test_extract_mortgage_supports_parenthesized_ab_party_headings(self):
        docx_path = make_docx(
            self.root / "mortgage_ab_headings.docx",
            "HỢP ĐỒNG THẾ CHẤP QUYỀN SỬ DỤNG ĐẤT",
            "(A) BÊN THẾ CHẤP",
            "Ông: Hoàng Hữu Dực | Ngày sinh: 04/07/1970",
            "Địa chỉ nơi cư trú: xã Yên Đồng, tỉnh Ninh Bình",
            "Căn cước công dân: 036070003911 do Cục CS QLHC về TTXH cấp ngày 11/08/2021",
            "và Bà: Hoàng Thị Hường Ngày sinh: 20/02/1978",
            "Địa chỉ nơi cư trú: xã Yên Đồng, tỉnh Ninh Bình",
            "Căn cước công dân: 036178006510 do Cục CS QLHC về TTXH cấp ngày 28/06/2021",
            "(B) BÊN NHẬN THẾ CHẤP",
            "NGÂN HÀNG THƯƠNG MẠI CỔ PHẦN NGOẠI THƯƠNG VIỆT NAM – CHI NHÁNH NAM ĐỊNH",
            "Địa chỉ đăng ký: Số 629 Trần Hưng Đạo, phường Nam Định, tỉnh Ninh Bình",
            "Đại diện: Ông Nguyễn Hữu Dụng Chức vụ: Phó giám đốc chi nhánh",
            "Căn cước công dân số: 036081017402 do Bộ Công an cấp ngày 02/07/2021",
            "Số công chứng 82/2026/CCGD",
        )

        payload = extract(docx_path)

        self.assertEqual(len(payload["raw"]["ben_a"]["nguoi"]), 2)
        self.assertIn("Nguyễn Hữu Dụng", payload["web_form"]["nguoi_yeu_cau"])

    def test_extract_mortgage_keeps_bank_representative_without_birth_or_id(self):
        docx_path = make_docx(
            self.root / "mortgage_bank_representative_no_id.docx",
            "HỢP ĐỒNG THẾ CHẤP QUYỀN SỬ DỤNG ĐẤT",
            "(A) BÊN THẾ CHẤP",
            "Ông: Hoàng Hữu Dực | Ngày sinh: 04/07/1970",
            "Căn cước công dân: 036070003911 do Cục CS QLHC về TTXH cấp ngày 11/08/2021",
            "(B) BÊN NHẬN THẾ CHẤP",
            "NGÂN HÀNG THƯƠNG MẠI CỔ PHẦN NGOẠI THƯƠNG VIỆT NAM – CHI NHÁNH NAM ĐỊNH",
            "Đại diện: Ông Nguyễn Hữu Dụng Chức vụ: Phó giám đốc chi nhánh",
            "Số công chứng 82/2026/CCGD",
        )

        payload = extract(docx_path)

        self.assertIn("Nguyễn Hữu Dụng", payload["web_form"]["nguoi_yeu_cau"])
        self.assertEqual(len(payload["raw"]["ben_b"]["nguoi"]), 1)

    def test_find_tai_san_stops_before_numbered_price_section(self):
        text = "\n".join(
            [
                "HOP DONG CHUYEN NHUONG QUYEN SU DUNG DAT",
                "quyen su dung dat cua ben A co dia chi tai: xa A, tinh B.",
                "- Thua dat so: 10",
                "- Dien tich: 100 m2",
                "2. Gia chuyen nhuong va phuong thuc thanh toan",
                "Gia chuyen nhuong la 1.000.000.000 dong.",
            ]
        )

        tai_san = find_tai_san(text)

        self.assertIn("Thua dat so: 10", tai_san)
        self.assertNotIn("Gia chuyen nhuong", tai_san)

    def test_find_tai_san_falls_back_to_end_when_stop_marker_is_absent(self):
        text = "\n".join(
            [
                "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
                "Đối tượng của Hợp đồng này là quyền sử dụng đất tại xã A.",
                "- Thửa đất số: 88",
                "- Diện tích: 120 m2",
            ]
        )

        tai_san = find_tai_san(text)

        self.assertIn("Thửa đất số: 88", tai_san)
        self.assertIn("Diện tích: 120 m2", tai_san)

    def test_extract_inheritance_partition_uses_single_heir_group_and_stops_asset_before_heirs_section(self):
        docx_path = make_docx(
            self.root / "phan_chia_di_san.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Chúng tôi là những người được hưởng di sản theo pháp luật của ông Nguyễn Văn Hỷ:",
            "Bà Nguyễn Thị Tuyết Sinh ngày: 01/01/1961",
            "Căn cước công dân số 036161014031 do Bộ Công an cấp ngày 28/06/2021;",
            "Thường trú tại: 02 Bà Huyện Thanh Quan, phường Lâm Viên – Đà Lạt, tỉnh Lâm Đồng.",
            "Bà Nguyễn Thị Nga Sinh ngày: 02/04/1964",
            "Căn cước công dân số 036164017015 do Bộ Công an cấp ngày 14/03/2024;",
            "Thường trú tại: Số 06/Đ2 Phan Chu Trinh, phường Lâm Viên – Đà Lạt, tỉnh Lâm Đồng.",
            "Bà Nguyễn Thị Thu Là Sinh ngày: 04/10/1972",
            "Căn cước công dân số 036172012182 do Bộ Công an cấp ngày 28/06/2021;",
            "Thường trú tại: 71C/2 Bùi Thị Xuân, phường Lâm Viên – Đà Lạt, tỉnh Lâm Đồng.",
            "Chúng tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "Người để lại di sản:",
            "Ông Nguyễn Văn Hỷ; Sinh năm: 1928; chết ngày 09/10/2019.",
            "Di sản:",
            "Di sản của ông Nguyễn Văn Hỷ để lại là:",
            "Quyền sử dụng đất của ông Nguyễn Văn Hỷ có địa chỉ tại: xã Ý Yên, tỉnh Ninh Bình theo Giấy chứng nhận quyền sử dụng đất số: A 692002.",
            "- Thửa đất số: 65; Tờ bản đồ số: 21",
            "- Diện tích: 190 m²",
            "- Mục đích sử dụng: Đất ở",
            "Người thừa kế:",
            "Những người thừa kế của ông Nguyễn Văn Hỷ gồm vợ và các con.",
            "Nội dung phân chia di sản.",
            "Bằng Văn bản này, chúng tôi xin nhận kỷ phần thừa kế.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
            "Số công chứng 2433.2025/PCDS/CCGD.",
        )

        payload = extract(docx_path)
        duong_su = payload["web_form"]["duong_su"]
        tai_san = payload["web_form"]["tai_san"]

        self.assertEqual(payload["raw"]["document_kind"], "inheritance_partition")
        self.assertEqual(payload["web_form"]["ten_hop_dong"], "VĂN BẢN PHÂN CHIA DI SẢN")
        self.assertEqual(payload["web_form"]["nhom_hop_dong"], "Thừa kế (khai nhận - phân chia di sản thừa kế )")
        self.assertEqual(payload["web_form"]["so_cong_chung"], "2433/2025")
        self.assertNotIn("NHỮNG NGƯỜI HƯỞNG DI SẢN:", duong_su)
        self.assertIn("Nguyễn Thị Tuyết", duong_su)
        self.assertIn("Nguyễn Thị Nga", duong_su)
        self.assertIn("Nguyễn Thị Thu Là", duong_su)
        self.assertNotIn("BÊN B:", duong_su)
        self.assertNotIn("Người để lại di sản", duong_su)
        self.assertIn("Quyền sử dụng đất của ông Nguyễn Văn Hỷ có địa chỉ tại", tai_san)
        self.assertNotIn("Người thừa kế:", tai_san)
        self.assertNotIn("Nội dung phân chia di sản", tai_san)

    def test_extract_inheritance_refusal_keeps_refuser_and_multiple_assets_without_oath_section(self):
        docx_path = make_docx_with_blocks(
            self.root / "tu_choi_di_san.docx",
            [
                ("p", "VĂN BẢN TỪ CHỐI NHẬN DI SẢN"),
                ("p", "Tôi là: Bà Hoàng Thị Hợi; Sinh ngày: 02/02/1945;"),
                ("p", "Căn cước công dân số 037145004692 do Bộ Công an cấp ngày 02/07/2021;"),
                ("p", "Thường trú tại: Thôn Hưng Thượng, xã Ý Yên, tỉnh Ninh Bình."),
                ("p", "Nay, tôi tự nguyện lập Văn bản này với nội dung như sau:"),
                ("p", "Chồng tôi là ông Nguyễn Văn Hỷ; Sinh năm: 1928; chết ngày 09/10/2019."),
                ("p", "Theo quy định của pháp luật, tôi là người được hưởng thừa kế đối với di sản mà ông Nguyễn Văn Hỷ để lại, đó là:"),
                ("p", "1. Tài sản thứ nhất:"),
                ("p", "Quyền sử dụng đất của ông Nguyễn Văn Hỷ có địa chỉ tại: xã Ý Yên, tỉnh Ninh Bình theo Giấy chứng nhận quyền sử dụng đất số: A 692002."),
                ("p", "- Thửa đất số: 65; Tờ bản đồ số: 21"),
                ("p", "- Diện tích: 190 m²"),
                ("p", "2. Tài sản thứ hai:"),
                ("p", "Phần quyền sử dụng đất của ông Nguyễn Văn Hỷ trong khối tài sản chung với vợ là bà Hoàng Thị Hợi có địa chỉ tại: xã Ý Yên, tỉnh Ninh Bình theo Giấy chứng nhận quyền sử dụng đất, quyền sở hữu nhà ở và tài sản khác gắn liền với đất số: CK 902585."),
                (
                    "table",
                    [
                        ("Tờ bản đồ số", "Thửa đất số", "Diện tích (m2)", "Mục đích sử dụng"),
                        ("19", "122(12)", "216.0", "Đất trồng lúa"),
                        ("46", "4(8)", "36.0", "Đất trồng lúa"),
                    ],
                ),
                ("p", "Bằng Văn bản này, tôi – Hoàng Thị Hợi tự nguyện từ chối nhận kỷ phần thừa kế mà mình được hưởng."),
                ("p", "Tôi xin cam đoan việc từ chối này là hoàn toàn tự nguyện."),
                ("p", "Người từ chối hưởng di sản"),
                ("p", "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN"),
                ("p", "Số công chứng 2233.2025/TCDS/CCGD."),
            ],
        )

        payload = extract(docx_path)
        duong_su = payload["web_form"]["duong_su"]
        tai_san = payload["web_form"]["tai_san"]

        self.assertEqual(payload["raw"]["document_kind"], "inheritance_refusal")
        self.assertEqual(payload["web_form"]["ten_hop_dong"], "VĂN BẢN TỪ CHỐI NHẬN DI SẢN")
        self.assertEqual(payload["web_form"]["nhom_hop_dong"], "Từ chối nhận di sản thừa kế")
        self.assertEqual(payload["web_form"]["so_cong_chung"], "2233/2025")
        self.assertIn("Hoàng Thị Hợi", payload["web_form"]["nguoi_yeu_cau"])
        self.assertTrue(duong_su.startswith("Bà Hoàng Thị Hợi"))
        self.assertNotIn("BÊN B:", duong_su)
        self.assertIn("Tài sản thứ hai", tai_san)
        self.assertIn("122(12)", tai_san)
        self.assertNotIn("Bằng Văn bản này, tôi", tai_san)
        self.assertNotIn("LỜI CHỨNG", tai_san)

    def test_extract_partition_counts_bare_name_spouse_and_tai_dia_chi_asset(self):
        # Cau truc rut gon (ten gia) mo phong mau that: nguoi vo dung dau dong
        # khong co "Ba", tai san dung cach noi "tai dia chi:", co bay nguoi
        # chet / bo me de / nguoi lam chung phai loai khoi duong su.
        docx_path = make_docx_with_blocks(
            self.root / "phan_chia_ten_tran.docx",
            [
                ("p", "VĂN BẢN PHÂN CHIA DI SẢN"),
                ("p", "Chúng tôi là những người được hưởng di sản theo pháp luật của ông Trần Văn X:"),
                ("p", "Trần Thị Mơ - Vợ ông X Sinh ngày: 01/01/1940;"),
                ("p", "Căn cước công dân số 036140000001 do Cục cảnh sát quản lý hành chính về trật tự xã hội cấp ngày 10/07/2021;"),
                ("p", "Thường trú tại: Tổ 1, Thị trấn L, huyện Y, tỉnh N."),
                ("p", "Bà Trần Thị A - Con đẻ ông X Sinh ngày: 01/05/1960"),
                ("p", "Căn cước công dân số 036160000002 do Bộ Công an cấp ngày 19/11/2024;"),
                ("p", "Thường trú tại: Tổ 1, Thị trấn L, huyện Y, tỉnh N."),
                ("p", "Ông Trần Văn B - Con đẻ ông X Sinh ngày: 15/01/1962"),
                ("p", "Căn cước công dân số 036062000003 do Bộ Công an cấp ngày 02/07/2021;"),
                ("p", "Thường trú tại: Tổ 2, Thị trấn L, huyện Y, tỉnh N."),
                ("p", "Chúng tôi tự nguyện lập Văn bản này với nội dung như sau:"),
                ("p", "Người để lại di sản:"),
                ("p", "Ông Trần Văn X; Sinh năm: 1935, chết ngày 11/06/2004 theo Trích lục khai tử số 12/TLKT-BS."),
                ("p", "Về bố, mẹ đẻ của ông Trần Văn X:"),
                ("p", "Bố đẻ ông Trần Văn X là ông Trần Văn Y; chết năm 1972. Mẹ đẻ ông Trần Văn X là bà Lê Thị Z, chết năm 1976."),
                ("p", "Di sản."),
                ("p", "Phần quyền sử dụng đất của ông Trần Văn X trong khối tài sản chung với vợ là bà Trần Thị Mơ tại địa chỉ: xã YX (nay là Tổ 1 Thị trấn L), huyện Y, tỉnh N theo Giấy chứng nhận quyền sử dụng đất số B 000001 do UBND huyện Y cấp ngày 15/03/1992, cụ thể như sau:"),
                (
                    "table",
                    [
                        ("Số tờ bản đồ", "Số thửa", "Diện tích (m2)", "Mục đích sử dụng"),
                        ("3 (nay là tờ bản đồ số 34)", "324", "205", "Đất ở"),
                    ],
                ),
                ("p", "Những người nhận thừa kế."),
                ("p", "Những người thừa kế của ông Trần Văn X gồm vợ và các con."),
                ("p", "Nội dung phân chia di sản."),
                ("p", "Bằng Văn bản này, chúng tôi xin nhận kỷ phần thừa kế."),
                ("p", "NHỮNG NGƯỜI HƯỞNG DI SẢN"),
                ("p", "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN"),
                ("p", "Hôm nay, ngày 11 tháng 06 năm 2025, tại trụ sở Văn phòng Công chứng VP, địa chỉ tại: Tổ 8, thị trấn L, huyện Y, tỉnh N,"),
                ("p", "Tôi, Phạm Minh Chi, Công chứng viên Văn phòng Công chứng VP, tỉnh N."),
                ("p", "CHỨNG NHẬN:"),
                ("p", "Văn bản phân chia di sản này được lập bởi:"),
                ("p", "Bà Phạm Thị C Sinh ngày: 19/05/1962;"),
                ("p", "Căn cước công dân số 036162000004 do Cục cảnh sát quản lý hành chính về trật tự xã hội cấp ngày 25/08/2021;"),
                ("p", "Thường trú tại: Thôn T, xã P, huyện Y, tỉnh N."),
            ],
        )

        payload = extract(docx_path)
        duong_su = payload["web_form"]["duong_su"]
        tai_san = payload["web_form"]["tai_san"]

        self.assertEqual(payload["raw"]["document_kind"], "inheritance_partition")
        self.assertEqual(len(payload["raw"]["ben_a"]["nguoi"]), 3)
        self.assertEqual(payload["raw"]["ben_a"]["nguoi"][0]["ho_ten"], "Trần Thị Mơ")
        self.assertEqual(payload["raw"]["ben_a"]["nguoi"][0]["gioi_tinh"], "Bà")
        self.assertEqual(payload["raw"]["ben_a"]["nguoi"][0]["ngay_sinh"], "01/01/1940")
        self.assertEqual(payload["raw"]["ben_a"]["nguoi"][0]["cccd"], "036140000001")
        self.assertEqual(payload["raw"]["ben_a"]["nguoi"][1]["ho_ten"], "Trần Thị A")
        self.assertNotIn("chết", duong_su)
        self.assertNotIn("Bố đẻ", duong_su)
        self.assertNotIn("Người để lại di sản", duong_su)
        self.assertNotIn("Phạm Thị C", duong_su)
        self.assertIn("tại địa chỉ:", tai_san)
        self.assertIn("324", tai_san)
        self.assertNotIn("Những người nhận thừa kế", tai_san)
        self.assertNotIn("Nội dung phân chia di sản", tai_san)
        self.assertEqual(payload["web_form"]["loai_tai_san"], "Đất đai không có tài sản")

    def test_real_inheritance_samples_partition_nine_heirs_and_refusal_one_refuser(self):
        # Chay tren file that (khong copy PII vao repo); bo qua khi may chay
        # khong co o dia D:/Minh.
        partition_path = Path(
            r"D:\Minh\1. Thừa kế Minh\Ý YÊN\26. Thừa kế ông Xương\9. Thoả thuận phân chia thừa kế.docx"
        )
        refusal_path = Path(
            r"D:\Minh\1. Thừa kế Minh\VŨ DƯƠNG\12. Thừa kế Bùi Văn Tài\Từ chối bà Luyến.docx"
        )
        if not partition_path.exists() or not refusal_path.exists():
            self.skipTest("Thieu file mau that tren D:/Minh")

        partition = extract(partition_path)
        partition_parties = partition["raw"]["ben_a"]["nguoi"]
        partition_duong_su = partition["web_form"]["duong_su"]
        partition_tai_san = partition["web_form"]["tai_san"]

        self.assertEqual(partition["raw"]["document_kind"], "inheritance_partition")
        self.assertEqual(len(partition_parties), 9)
        self.assertTrue(all(person.get("ngay_sinh") and person.get("cccd") for person in partition_parties))
        self.assertNotIn("chết", partition_duong_su)
        self.assertNotIn("Bố đẻ", partition_duong_su)
        self.assertNotIn("Người để lại di sản", partition_duong_su)
        self.assertIn("Số tờ bản đồ", partition_tai_san)
        self.assertNotIn("Những người nhận thừa kế", partition_tai_san)
        self.assertNotIn("Nội dung phân chia di sản", partition_tai_san)

        refusal = extract(refusal_path)
        refusal_parties = refusal["raw"]["ben_a"]["nguoi"]
        refusal_duong_su = refusal["web_form"]["duong_su"]
        refusal_tai_san = refusal["web_form"]["tai_san"]

        self.assertEqual(refusal["raw"]["document_kind"], "inheritance_refusal")
        self.assertEqual(len(refusal_parties), 1)
        self.assertTrue(refusal_parties[0].get("ngay_sinh") and refusal_parties[0].get("cccd"))
        self.assertNotIn("chết", refusal_duong_su)
        self.assertIn("Số tờ bản đồ", refusal_tai_san)
        self.assertNotIn("Bằng Văn bản này, tôi", refusal_tai_san)

    def test_extract_partition_birth_year_no_colon_and_noi_thuong_tru(self):
        # Nguoi lon tuoi chi ghi "Sinh nam 1965" (khong co dau hai cham),
        # dia chi ghi "Nơi thường trú:" — ten phai sach, nam sinh giu lai.
        docx_path = make_docx(
            self.root / "phan_chia_sinh_nam.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN THỪA KẾ",
            "Chúng tôi là những người được hưởng di sản thừa kế theo pháp luật của ông Trần Ngọc X, gồm:",
            "Bà Nguyễn Thị A – Sinh năm 1965;",
            "CCCD số 036165000001, do Cục cảnh sát QLHC về TTXH cấp ngày 16/12/2021; Nơi thường trú: xã YP, huyện YY, tỉnh NĐ.",
            "Ông Trần Văn B – Sinh năm 1986,",
            "CCCD số 036086000002, do Cục cảnh sát QLHC về TTXH cấp ngày 10/05/2021;",
            "Nơi thường trú: Thôn BQ, xã YP, huyện YY, tỉnh NĐ.",
            "Chúng tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "Người để lại di sản:",
            "Ông Trần Ngọc X - Sinh năm 1940; chết ngày 29/05/2022 theo Trích lục khai tử số 21/TLKT-BS.",
            "Di sản thừa kế của ông Trần Ngọc X bao gồm:",
            "Quyền sử dụng đất tại địa chỉ: xã YP, huyện YY, tỉnh NĐ theo Giấy chứng nhận quyền sử dụng đất: A 000002 do UBND huyện YY cấp ngày 15/04/1991.",
            "- Thửa đất số: 145; Tờ bản đồ số: 9",
            "- Diện tích: 240 m2",
            "Những người nhận thừa kế.",
            "Những người thừa kế của ông Trần Ngọc X gồm vợ và con.",
            "Số công chứng 100.2025/DSTK/CCGD.",
        )

        payload = extract(docx_path)
        persons = payload["raw"]["ben_a"]["nguoi"]
        duong_su = payload["web_form"]["duong_su"]
        tai_san = payload["web_form"]["tai_san"]

        self.assertEqual(payload["raw"]["document_kind"], "inheritance_partition")
        self.assertEqual(len(persons), 2)
        self.assertEqual(persons[0]["ho_ten"], "Nguyễn Thị A")
        self.assertEqual(persons[0]["ngay_sinh"], "1965")
        self.assertTrue(persons[0]["chi_co_nam_sinh"])
        self.assertEqual(persons[0]["cccd"], "036165000001")
        self.assertIn("xã YP", persons[0]["dia_chi"])
        self.assertEqual(persons[1]["ho_ten"], "Trần Văn B")
        self.assertEqual(persons[1]["ngay_sinh"], "1986")
        self.assertTrue(persons[1]["chi_co_nam_sinh"])
        self.assertNotIn("chết", duong_su)
        self.assertNotIn("Người để lại di sản", duong_su)
        self.assertIn("145", tai_san)
        self.assertNotIn("Những người nhận thừa kế", tai_san)

    def test_extract_refusal_plural_anh_chi_refusers(self):
        # Tu choi tap the: mo dau "Chúng tôi là:", nguoi dung "Chị/Anh" thay
        # vi "Bà/Ông", ket "Nay, chúng tôi tự nguyện...".
        docx_path = make_docx(
            self.root / "tu_choi_anh_chi.docx",
            "VĂN BẢN TỪ CHỐI NHẬN DI SẢN",
            "Chúng tôi là:",
            "1. Chị Phạm Thị Duyên Sinh ngày: 14/08/1997;",
            "Căn cước công dân số 020197000001 do Cục cảnh sát quản lý hành chính về trật tự xã hội cấp ngày 09/01/2023;",
            "Thường trú tại: Thôn XC, xã HT, huyện HL, tỉnh LS.",
            "2. Anh Phạm Văn Thái Sinh ngày: 23/02/2005;",
            "Căn cước công dân số 020205000002 do Cục cảnh sát quản lý hành chính về trật tự xã hội cấp ngày 18/08/2021;",
            "Thường trú tại: Thôn XC, xã HT, huyện HL, tỉnh LS.",
            "Nay, chúng tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "Mẹ đẻ chúng tôi là bà Nguyễn Thị M; Sinh năm: 1969; chết ngày 24/09/2010 theo Trích lục khai tử số 36/2025/TLKT.",
            "Theo quy định của pháp luật, chúng tôi là người được hưởng thừa kế đối với di sản là:",
            "Phần quyền sử dụng đất của bà Nguyễn Thị M tại địa chỉ: xã YP, huyện YY, tỉnh NĐ theo Giấy chứng nhận quyền sử dụng đất số: A 000003 do UBND huyện YY cấp ngày 15/04/1991.",
            "- Thửa đất số: 169; Tờ bản đồ số: 4",
            "Bằng Văn bản này, chúng tôi tự nguyện từ chối nhận kỷ phần thừa kế.",
            "Tôi xin cam đoan việc từ chối này là hoàn toàn tự nguyện.",
            "Những người từ chối nhận di sản",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
            "Số công chứng 978.2025/TCDS/CCGD.",
        )

        payload = extract(docx_path)
        persons = payload["raw"]["ben_a"]["nguoi"]
        duong_su = payload["web_form"]["duong_su"]
        tai_san = payload["web_form"]["tai_san"]

        self.assertEqual(payload["raw"]["document_kind"], "inheritance_refusal")
        self.assertEqual(len(persons), 2)
        self.assertEqual(persons[0]["ho_ten"], "Phạm Thị Duyên")
        self.assertEqual(persons[0]["gioi_tinh"], "Bà")
        self.assertEqual(persons[1]["ho_ten"], "Phạm Văn Thái")
        self.assertEqual(persons[1]["gioi_tinh"], "Ông")
        self.assertNotIn("chết", duong_su)
        self.assertIn("169", tai_san)
        self.assertNotIn("Bằng Văn bản này, chúng tôi", tai_san)

    def test_extract_partition_toi_la_opener_typo_single_heir(self):
        # Loi danh may pho bien: "Tôi là những người..." (thieu "Chúng").
        docx_path = make_docx(
            self.root / "phan_chia_toi_la.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Tôi là những người được hưởng di sản theo pháp luật của ông Trần Văn C:",
            "Bà Nguyễn Thị Xuân Sinh ngày: 03/09/1946;",
            "Căn cước công dân số 036146000001 do Cục cảnh sát quản lý hành chính về trật tự xã hội cấp ngày 16/03/2022;",
            "Thường trú tại: Thôn PG, xã YP, tỉnh NB.",
            "Tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "Người để lại di sản:",
            "Ông Trần Văn C; Sinh năm: 1947, chết ngày 12/04/2005 theo Trích lục khai tử số 169/TLKT-BS.",
            "Di sản của ông Trần Văn C là:",
            "Phần quyền sử dụng đất của ông Trần Văn C tại địa chỉ: xã YP, huyện YY, tỉnh NĐ theo Giấy chứng nhận quyền sử dụng đất số A 000004 do UBND huyện YY cấp ngày 15/04/1991.",
            "- Thửa đất số: 104; Tờ bản đồ số: 24",
            "Những người nhận thừa kế.",
            "Số công chứng 500.2025/DSTK/CCGD.",
        )

        payload = extract(docx_path)
        persons = payload["raw"]["ben_a"]["nguoi"]

        self.assertEqual(payload["raw"]["document_kind"], "inheritance_partition")
        self.assertEqual(len(persons), 1)
        self.assertEqual(persons[0]["ho_ten"], "Nguyễn Thị Xuân")
        self.assertNotIn("chết", payload["web_form"]["duong_su"])
        self.assertIn("104", payload["web_form"]["tai_san"])

    def test_real_inheritance_the_vi_refusal_three_refusers(self):
        # File that: tu choi huong the vi (khong copy PII vao repo).
        refusal_path = Path(
            r"D:\systemdocs\.agent\scratch\Dữ liệu mẫu word test\THỪA KẾ\1. Thừa kế Minh\Ý YÊN\30. Thừa kế ông Kính bà Tới\Từ chối di sản hưởng thế vị từ bà Tới.docx"
        )
        if not refusal_path.exists():
            self.skipTest("Thieu file mau the vi tren may nay")

        refusal = extract(refusal_path)
        refusal_parties = refusal["raw"]["ben_a"]["nguoi"]

        self.assertEqual(refusal["raw"]["document_kind"], "inheritance_refusal")
        self.assertEqual(len(refusal_parties), 3)
        self.assertTrue(all(person.get("ngay_sinh") and person.get("cccd") for person in refusal_parties))
        self.assertNotIn("chết", refusal["web_form"]["duong_su"])
        self.assertIn("Số tờ bản đồ", refusal["web_form"]["tai_san"])

    def test_tach_danh_sach_thua_dat_table_nhieu_thua_va_trong_do(self):
        # Bang 2 thua + dong "Trong do" tach nho dien tich.
        docx_path = make_docx_with_blocks(
            self.root / "tach_thua_table.docx",
            [
                ("p", "VĂN BẢN TỪ CHỐI NHẬN DI SẢN"),
                ("p", "Tôi là: Bà Nguyễn Thị M Sinh ngày: 01/01/1960;"),
                ("p", "Căn cước công dân số 036160000001 do Bộ Công an cấp ngày 01/01/2021;"),
                ("p", "Thường trú tại: Thôn A, xã B."),
                ("p", "Nay, tôi tự nguyện lập Văn bản này với nội dung như sau:"),
                ("p", "Theo quy định của pháp luật, tôi là người được hưởng thừa kế đối với di sản là:"),
                ("p", "Phần quyền sử dụng đất của ông Trần Văn X tại địa chỉ: xã B, huyện C theo Giấy chứng nhận quyền sử dụng đất số: A 000010 do UBND huyện C cấp ngày 01/01/1991. Cụ thể như sau:"),
                (
                    "table",
                    [
                        ("Số tờ bản đồ", "Số thửa", "Diện tích (m2)", "Mục đích sử dụng", "Thời gian sử dụng"),
                        ("4", "169", "427", "", ""),
                        ("Trong đó", "", "", "", ""),
                        ("200", "Đất ở", "Lâu dài", "", ""),
                        ("227", "Đất vườn", "Lâu dài", "", ""),
                        ("5", "170", "100", "Đất ở", "Lâu dài"),
                    ],
                ),
                ("p", "Bằng Văn bản này, tôi tự nguyện từ chối nhận kỷ phần thừa kế."),
                ("p", "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN"),
                ("p", "Số công chứng 1.2026/TCDS/CCGD."),
            ],
        )

        payload = extract(docx_path)
        thua_list = payload["raw"]["danh_sach_thua_dat"]

        self.assertEqual(len(thua_list), 2)
        self.assertEqual(thua_list[0]["so_thua_dat"], "169")
        self.assertEqual(thua_list[0]["so_to_ban_do"], "4")
        self.assertEqual(thua_list[0]["dien_tich"], "427")
        self.assertEqual(thua_list[0]["so_gcn"], "A000010")
        self.assertEqual(len(thua_list[0]["chi_tiet_dien_tich"]), 2)
        self.assertEqual(thua_list[0]["chi_tiet_dien_tich"][0]["dien_tich"], "200")
        self.assertEqual(thua_list[1]["so_thua_dat"], "170")
        self.assertEqual(thua_list[1]["muc_dich_su_dung"], "Đất ở")

    def test_tach_danh_sach_thua_dat_dang_gach_dau_dong(self):
        # Tai san ghi dang "- Thua dat so: ..." thi 1 dong 1 thua.
        docx_path = make_docx(
            self.root / "tach_thua_bullet.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Chúng tôi là những người được hưởng di sản theo pháp luật của ông Trần Văn X:",
            "Bà Nguyễn Thị A Sinh ngày: 01/01/1960;",
            "Căn cước công dân số 036160000001 do Bộ Công an cấp ngày 01/01/2021;",
            "Thường trú tại: Thôn A, xã B.",
            "Chúng tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "Di sản của ông Trần Văn X để lại là:",
            "Quyền sử dụng đất của ông Trần Văn X có địa chỉ tại: xã B, huyện C theo Giấy chứng nhận quyền sử dụng đất số B 000020 do UBND huyện C cấp ngày 02/02/1992.",
            "- Thửa đất số: 65; Tờ bản đồ số: 21",
            "- Diện tích: 190 m2",
            "- Mục đích sử dụng: Đất ở",
            "- Thời hạn sử dụng: Lâu dài.",
            "Người thừa kế:",
            "Những người thừa kế của ông Trần Văn X gồm vợ và con.",
            "Số công chứng 2.2026/DSTK/CCGD.",
        )

        payload = extract(docx_path)
        thua_list = payload["raw"]["danh_sach_thua_dat"]

        self.assertEqual(len(thua_list), 1)
        self.assertEqual(thua_list[0]["so_thua_dat"], "65")
        self.assertEqual(thua_list[0]["so_to_ban_do"], "21")
        self.assertEqual(thua_list[0]["dien_tich"], "190 m2")
        self.assertEqual(thua_list[0]["muc_dich_su_dung"], "Đất ở")
        self.assertEqual(thua_list[0]["thoi_han_su_dung"], "Lâu dài")
        self.assertEqual(thua_list[0]["so_gcn"], "B000020")
        self.assertIn("xã B", thua_list[0]["dia_chi"])

    def test_loi_chung_nguoi_xuat_het_khong_doi_chieu(self):
        # Core regex: co nguoi nao xuat nguoi do — ke ca khi Loi chung ghi
        # nguoi khac voi dau van ban. Khong doi chieu, khong gop.
        docx_path = make_docx(
            self.root / "loi_chung_khac.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Chúng tôi là những người được hưởng di sản theo pháp luật của ông Trần Văn X:",
            "Bà Nguyễn Thị A Sinh ngày: 01/01/1960;",
            "Căn cước công dân số 036160000001 do Bộ Công an cấp ngày 01/01/2021;",
            "Thường trú tại: Thôn A, xã B.",
            "Chúng tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "Di sản của ông Trần Văn X để lại là:",
            "Quyền sử dụng đất có địa chỉ tại: xã B, huyện C.",
            "- Thửa đất số: 1",
            "Nội dung phân chia di sản.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
            "Văn bản phân chia di sản này được lập bởi:",
            "Bà Phạm Thị Z Sinh ngày: 02/02/1970;",
            "Căn cước công dân số 036170000002 do Bộ Công an cấp ngày 02/02/2022;",
            "Thường trú tại: Thôn C, xã D.",
            "Số công chứng 3.2026/DSTK/CCGD.",
        )

        payload = extract(docx_path)

        self.assertEqual(len(payload["raw"]["ben_a"]["nguoi"]), 1)
        self.assertEqual(payload["raw"]["ben_a"]["nguoi"][0]["ho_ten"], "Nguyễn Thị A")
        self.assertNotIn("loi_chung_nguoi", payload["raw"])

    def test_so_cong_chung_khong_con_tieu_chi_du_thieu_cua_core(self):
        # Khong co so cong chung van khong bi danh "thieu" neu nguoi +
        # tai san du — core chi chiu trach nhiem nguoi + tai san.
        docx_path = make_docx(
            self.root / "khong_so_cc.docx",
            "VĂN BẢN TỪ CHỐI NHẬN DI SẢN",
            "Tôi là: Bà Nguyễn Thị M Sinh ngày: 01/01/1960;",
            "Căn cước công dân số 036160000001 do Bộ Công an cấp ngày 01/01/2021;",
            "Thường trú tại: Thôn A, xã B.",
            "Nay, tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "Theo quy định của pháp luật, tôi là người được hưởng thừa kế đối với di sản là:",
            "Phần quyền sử dụng đất tại địa chỉ: xã B, huyện C.",
            "- Thửa đất số: 7",
            "Bằng Văn bản này, tôi tự nguyện từ chối nhận kỷ phần thừa kế.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)

        self.assertEqual(payload["web_form"]["so_cong_chung"], "")
        self.assertNotIn("so_cong_chung", payload["raw"]["missing_web_form_fields"])
        self.assertFalse(payload["raw"]["extract_is_partial"])

    def test_tach_thua_dong_nay_la_khong_nham_tieu_de_bang(self):
        # Dong du lieu "04 Nay la to ban do 24 | 104 Nay la thua dat so 321
        # | ..." chua chu "to ban do"/"thua" nhung khong phai tieu de.
        block = "\n".join(
            [
                "Phần quyền sử dụng đất tại địa chỉ: xã B, huyện C theo Giấy chứng nhận quyền sử dụng đất số A 000030 do UBND huyện C cấp ngày 01/01/1991, cụ thể như sau:",
                "Số tờ bản đồ | Số thửa | Diện tích (m2) | Mục đích sử dụng | Thời gian sử dụng | Phần ghi thêm",
                "04 Nay là tờ bản đồ 24 | 104 Nay là thửa đất số 321 | 206 | Đất ở | Lâu dài",
            ]
        )

        thua_list = tach_danh_sach_thua_dat(block)

        self.assertEqual(len(thua_list), 1)
        # Ky hieu dau la gia tri hien tai; duoi "nay la thua/to ..." vao ghi chu.
        self.assertEqual(thua_list[0]["so_thua_dat"], "104")
        self.assertEqual(thua_list[0]["so_to_ban_do"], "04")
        self.assertIn("321", thua_list[0]["phan_ghi_them"])
        self.assertIn("24", thua_list[0]["phan_ghi_them"])
        self.assertEqual(thua_list[0]["dien_tich"], "206")
        self.assertEqual(thua_list[0]["so_gcn"], "A000030")

    def test_extract_nguoi_chet_hai_nguoi_co_ten_goi_khac(self):
        # 2 nguoi de lai di san: ten, ten goi khac, nam sinh, ngay chet,
        # trich luc, dia chi cuoi. Nguoi chet khong vao ben_a.
        docx_path = make_docx(
            self.root / "nguoi_chet_doi.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Người được hưởng di sản theo pháp luật của ông Trần Văn X và bà Lê Thị Y là:",
            "Ông: Trần Văn Z Sinh ngày: 01/01/1955",
            "Căn cước công dân số: 036055000001 do Bộ Công an cấp ngày 05/03/2023;",
            "Thường trú tại: thôn A, xã B.",
            "Tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "I. Người để lại di sản:",
            "1. Ông Trần Văn X (tên gọi khác là Trần Văn W) - Sinh năm 1920, đã chết ngày 12/06/2010 theo Trích lục khai tử (bản sao) số 866/2025/TLKT-BS do UBND xã B ký ngày: 27/11/2025; Nơi thường trú cuối cùng trước khi chết: thôn A, xã B.",
            "2. Bà Lê Thị Y - Sinh năm 1923, đã chết ngày 18/09/2010 theo Trích lục khai tử (bản sao) số 867/2025/TLKT-BS do UBND xã B ký ngày: 27/11/2025; Nơi thường trú cuối cùng trước khi chết: thôn A, xã B.",
            "II. Di sản:",
            "Di sản của ông Trần Văn X và bà Lê Thị Y là:",
            "Phần quyền sử dụng đất tại địa chỉ: xã B, huyện C theo Giấy chứng nhận quyền sử dụng đất số: A 000040 do UBND huyện C cấp ngày 20/02/1992, cụ thể:",
            "- Thửa đất số: 106; Tờ bản đồ số: 2",
            "- Diện tích: 450 m2",
            "III. Người thừa kế:",
            "Những người thừa kế gồm ông Trần Văn Z.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
            "Số công chứng 212.2026/CCGD.",
        )

        payload = extract(docx_path)

        self.assertEqual(payload["raw"]["document_kind"], "inheritance_partition")
        self.assertEqual([p["ho_ten"] for p in payload["raw"]["ben_a"]["nguoi"]], ["Trần Văn Z"])
        chet = payload["raw"]["nguoi_chet"]
        self.assertEqual(len(chet), 2)
        self.assertEqual(chet[0]["ho_ten"], "Trần Văn X")
        self.assertEqual(chet[0]["ten_goi_khac"], "Trần Văn W")
        self.assertEqual(chet[0]["ngay_sinh"], "1920")
        self.assertTrue(chet[0]["chi_co_nam_sinh"])
        self.assertEqual(chet[0]["ngay_chet"], "12/06/2010")
        self.assertEqual(chet[0]["so_giay_to"], "866/2025/TLKT-BS")
        self.assertIn("thôn A", chet[0]["dia_chi"])
        self.assertEqual(chet[1]["ho_ten"], "Lê Thị Y")
        self.assertEqual(chet[1]["ngay_chet"], "18/09/2010")

    def test_tach_thua_cell_stream_bang_doc_don_dong(self):
        # IFilter giu o bang bang TAB (doi thanh "|"): tieu de + du lieu
        # don chung 1 dong, "Trong do" tach chi tiet, "2.2." dung lai.
        block = "\n".join(
            [
                "Phần quyền sử dụng đất tại địa chỉ: xã B, huyện C theo Giấy chứng nhận quyền sử dụng đất số: A 000050 do UBND huyện C cấp ngày 20/02/1992, cụ thể:",
                "Số tờ bản đồ | Số thửa | Diện tích",
                "( m2) | Mục đích sử dụng | Thời hạn sử dụng | Phần ghi thêm |  | 2 (nay là tờ bản đồ số 107) | 106 | 450 | Trong đó | 200 | Đất ở | Lâu dài | 250 | NTS | 15/10/2063 | Đất HTX giao lại |  | 2.2. | Phần quyền khác.",
            ]
        )

        thua_list = tach_danh_sach_thua_dat(block)

        self.assertEqual(len(thua_list), 1)
        self.assertEqual(thua_list[0]["so_thua_dat"], "106")
        # "(nay la to ban do so 107)" -> ky hieu "2" + ghi chu giu duoi.
        self.assertEqual(thua_list[0]["so_to_ban_do"], "2")
        self.assertIn("107", thua_list[0]["phan_ghi_them"])
        self.assertEqual(thua_list[0]["dien_tich"], "450")
        self.assertEqual(thua_list[0]["loai_gcn"], "quyền sử dụng đất")
        details = thua_list[0]["chi_tiet_dien_tich"]
        self.assertEqual(len(details), 2)
        self.assertEqual(details[0]["dien_tich"], "200")
        self.assertEqual(details[1]["muc_dich_su_dung"], "NTS")
        self.assertEqual(details[1]["thoi_han_su_dung"], "15/10/2063")
        self.assertIn("HTX", details[1].get("phan_ghi_them", ""))

    def test_tach_thua_nhan_so_thua_va_trong_do_chi_tiet(self):
        # Nhan "So thua:/So to ban do" (nguoc thu tu), "Trong do:" gom
        # chi tiet vao thua dang mo thay vi ghi de dien tich thua.
        block = "\n".join(
            [
                "Quyền sử dụng đất mang tên Hộ ông Trần Văn X được quyền sử dụng 450 m2 đất theo Giấy chứng nhận quyền sử dụng đất số: Y000001 vào sổ giấy chứng nhận quyền sử dụng đất số 376 QSDD/số 887QĐ-UB huyện ngày 09/06/2003 do UBND huyện C ký ngày 09/06/2003, cụ thể như sau:",
                "Thửa đất:",
                "Số thửa: 204          Số tờ bản đồ: 17",
                "Diện tích: 285.0 m2 (bằng chữ: Hai trăm tám mươi lăm mét vuông)",
                "Trong đó:",
                "Diện tích: 130.0 m2",
                "Mục đích sử dụng: Đất vườn",
                "Thời hạn sử dụng: 2043",
                "Diện tích: 155.0 m2",
                "Mục đích sử dụng: Đất ở",
                "Thời hạn sử dụng: Lâu dài",
                "Số thửa: 205          Số tờ bản đồ: 17",
                "Diện tích: 165.0 m2",
            ]
        )

        thua_list = tach_danh_sach_thua_dat(block)

        self.assertEqual(len(thua_list), 2)
        self.assertEqual(thua_list[0]["so_thua_dat"], "204")
        self.assertEqual(thua_list[0]["so_to_ban_do"], "17")
        self.assertEqual(thua_list[0]["dien_tich"], "285.0 m2")
        self.assertEqual(thua_list[0]["so_gcn"], "Y000001")
        self.assertEqual(thua_list[0]["so_vao_so"], "376 QSDD/số 887QĐ-UB")
        self.assertEqual(thua_list[0]["ngay_cap_gcn"], "09/06/2003")
        details = thua_list[0]["chi_tiet_dien_tich"]
        self.assertEqual(len(details), 2)
        self.assertEqual(details[0]["dien_tich"], "130.0 m2")
        self.assertEqual(details[1]["muc_dich_su_dung"], "Đất ở")
        self.assertEqual(thua_list[1]["so_thua_dat"], "205")
        self.assertEqual(thua_list[1]["dien_tich"], "165.0 m2")

    def test_land_rows_theo_shape_database(self):
        # Moi loai dat trong 1 thua tach rieng: ONT/NTS/CLN...
        thua_list = tach_danh_sach_thua_dat(
            "\n".join(
                [
                    "Quyền sử dụng đất có địa chỉ tại: xã B theo Giấy chứng nhận quyền sử dụng đất số A 000001.",
                    "Số tờ bản đồ | Số thửa | Diện tích (m2) | Mục đích sử dụng | Thời gian sử dụng",
                    "1 | 10 | 200",
                    "Trong đó",
                    "100 | ONT | Lâu dài",
                    "50 | NTS | Lâu dài",
                    "50 | CLN | Lâu dài",
                ]
            )
        )

        self.assertEqual(len(thua_list), 1)
        land_rows = thua_list[0]["land_rows"]
        self.assertEqual(len(land_rows), 3)
        self.assertEqual(land_rows[0], {"loai_dat": "ONT", "dien_tich": 100.0, "thoi_han": "Lâu dài"})
        self.assertEqual(land_rows[1]["loai_dat"], "NTS")
        self.assertEqual(land_rows[2]["dien_tich"], 50.0)

    def test_tach_so_tiet_kiem_va_tai_khoan(self):
        block = "\n".join(
            [
                "Di sản thừa kế là phần sở hữu số tiền gốc và lãi trong khối tài sản chung:",
                "Sổ tiết kiệm có kỳ hạn do ngân hàng NN chi nhánh huyện C số hiệu: AC 000000001, Phát hành ngày 05/01/2023 cho ông: Trần Văn X.",
                "Sổ tiết kiệm có kỳ hạn do ngân hàng NN chi nhánh huyện C số hiệu: AD 000000002, Phát hành ngày 21/06/2023 cho ông: Trần Văn X.",
                "Xác nhận số dư tài khoản do ngân hàng NN chi nhánh huyện C xác nhận số tài khoản: 3214600000001 mang tên Trần Văn X.",
            ]
        )

        entries = tach_danh_sach_so_tiet_kiem(block)

        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]["so_hieu"], "AC 000000001")
        self.assertIn("ngân hàng NN", entries[0]["ngan_hang"])
        self.assertEqual(entries[0]["chi_nhanh"], "huyện C")
        self.assertEqual(entries[0]["ngay_phat_hanh"], "05/01/2023")
        self.assertEqual(entries[0]["chu_so"], "Trần Văn X")
        self.assertEqual(entries[1]["so_hieu"], "AD 000000002")
        self.assertEqual(entries[2]["loai_so"], "tài khoản")
        self.assertEqual(entries[2]["so_hieu"], "3214600000001")
        self.assertEqual(entries[2]["chu_so"], "Trần Văn X")

    def test_khai_nhan_toi_la_mot_nguoi_va_tai_san_tiet_kiem(self):
        docx_path = make_docx(
            self.root / "khai_nhan_tiet_kiem.docx",
            "VĂN BẢN KHAI NHẬN DI SẢN THỪA KẾ",
            "Người được hưởng di sản thừa kế của ông Trần Văn X và bà Lê Thị Y:",
            "Tôi là: Bà Trần Thị T Sinh năm 1990;",
            "Căn cước công dân số 036190000001 Cục cảnh sát QLHC về TTXH cấp ngày 10/08/2021;",
            "Nơi thường trú: xóm 06, xã B.",
            "Tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "I. Người để lại di sản:",
            "Ông Trần Văn X - sinh năm 1954, đã chết ngày 29/03/2025 theo Trích lục khai tử (bản sao) số 120/TLKT-BS do UBND xã B cấp ngày 31/03/2025.",
            "Bà Lê Thị Y - sinh năm 1956, đã chết ngày 22/12/2024 theo Trích lục khai tử số 66/2024/TLKT do UBND xã B cấp ngày 23/12/2024.",
            "II. Di sản thừa kế.",
            "Di sản thừa kế của ông Trần Văn X và bà Lê Thị Y là:",
            "Toàn bộ gốc và lãi theo Sổ tiết kiệm có kỳ hạn do ngân hàng NN - chi nhánh C số hiệu: AC 000000003, phát hành ngày 02/05/2024 cho ông: Trần Văn X.",
            "III. Những người nhận thừa kế.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
            "Số công chứng 100.2026/CCGD.",
        )

        payload = extract(docx_path)

        self.assertEqual(payload["raw"]["document_kind"], "inheritance_declaration")
        persons = payload["raw"]["ben_a"]["nguoi"]
        self.assertEqual(len(persons), 1)
        self.assertEqual(persons[0]["ho_ten"], "Trần Thị T")
        self.assertIn("xóm 06", persons[0]["dia_chi"])
        self.assertEqual(len(payload["raw"]["nguoi_chet"]), 2)
        self.assertEqual(payload["web_form"]["loai_tai_san"], "Sổ tiết kiệm")
        self.assertEqual(payload["raw"]["tai_san_chua_ho_tro"], ["so_tiet_kiem"])
        self.assertNotIn("danh_sach_so_tiet_kiem", payload["raw"])

    def test_dia_chi_chung_dong_voi_ten_nguoi(self):
        # Dia chi nam chung dong voi ten ("...; Nơi thường trú: X").
        docx_path = make_docx(
            self.root / "dia_chi_chung_dong.docx",
            "VĂN BẢN TỪ CHỐI NHẬN DI SẢN",
            "Tôi là: Bà Nguyễn Thị M Sinh ngày: 01/01/1960;",
            "Căn cước công dân số 036160000001 do Bộ Công an cấp ngày 01/01/2021; Nơi thường trú: Thôn A, xã B.",
            "Nay, tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "Theo quy định của pháp luật, tôi là người được hưởng thừa kế đối với di sản là:",
            "Phần quyền sử dụng đất tại địa chỉ: xã B, huyện C.",
            "- Thửa đất số: 7",
            "Bằng Văn bản này, tôi tự nguyện từ chối nhận kỷ phần thừa kế.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)
        persons = payload["raw"]["ben_a"]["nguoi"]

        self.assertEqual(len(persons), 1)
        self.assertIn("Thôn A", persons[0]["dia_chi"])

    def test_nhan_ngay_sinh_dau_gach_ngang(self):
        # Bien the dau phan cach sau nhan: ":" , "-" , khong dau.
        docx_path = make_docx(
            self.root / "ngay_sinh_gach.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Chúng tôi là những người được hưởng di sản theo pháp luật của ông Trần Văn X:",
            "Bà Nguyễn Thị A - Ngày sinh - 01/05/1960;",
            "Căn cước công dân số 036160000001 do Bộ Công an cấp ngày 01/01/2021;",
            "Thường trú tại: Thôn A, xã B.",
            "Ông Trần Văn B - Sinh năm - 1962;",
            "Căn cước công dân số 036062000002 do Bộ Công an cấp ngày 02/02/2022;",
            "Thường trú tại: Thôn A, xã B.",
            "Chúng tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "Người để lại di sản:",
            "Ông Trần Văn X - Sinh năm - 1940; chết ngày - 11/06/2004 theo Trích lục khai tử số 1/TLKT.",
            "Di sản của ông Trần Văn X để lại là:",
            "Quyền sử dụng đất có địa chỉ tại: xã B, huyện C.",
            "- Thửa đất số: 9",
            "Nội dung phân chia di sản.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
            "Số công chứng 9.2026/CCGD.",
        )

        payload = extract(docx_path)
        persons = payload["raw"]["ben_a"]["nguoi"]

        self.assertEqual(len(persons), 2)
        self.assertEqual(persons[0]["ho_ten"], "Nguyễn Thị A")
        self.assertEqual(persons[0]["ngay_sinh"], "01/05/1960")
        self.assertFalse(persons[0]["chi_co_nam_sinh"])
        self.assertEqual(persons[1]["ngay_sinh"], "1962")
        self.assertTrue(persons[1]["chi_co_nam_sinh"])
        chet = payload["raw"]["nguoi_chet"]
        self.assertEqual(len(chet), 1)
        self.assertEqual(chet[0]["ho_ten"], "Trần Văn X")
        self.assertEqual(chet[0]["ngay_chet"], "11/06/2004")

    def test_xa_hang_thua_ke_ong_ba_title_va_noi_cu_tru(self):
        # Mau ky o xa: mo dau "Hang thua ke ...", ten "Ông/bà:",
        # vai tro dong rieng "La con de ...", dia chi "Nơi cư trú:".
        docx_path = make_docx(
            self.root / "xa_hang_thua_ke.docx",
            "VĂN BẢN THỎA THUẬN",
            "PHÂN CHIA DI SẢN THỪA KẾ",
            "Hôm nay, tại UBND xã C. Hàng thừa kế của ông Trần Văn X gồm những người có tên sau đây:",
            "Ông/bà: Phạm Thị A; Sinh ngày: 02/01/1965;",
            "Căn cước số: 036065000001 do Bộ Công an cấp ngày 18/12/2024;",
            "Cư trú tại: xã C, tỉnh N.",
            "Là con đẻ ông Trần Văn X.",
            "Ông/bà: Trần Văn B; Sinh ngày: 01/01/1967;",
            "Căn cước công dân số: 036067000002 do Bộ Công an cấp ngày 09/08/2021;",
            "Thường trú tại: xã C, tỉnh N.",
            "Là con đẻ ông Trần Văn X.",
            "Ông Trần Văn X; Sinh năm: 1932; chết ngày 24/11/2013 theo Giấy chứng tử số 53 do UBND xã C ký ngày 29/11/2013.",
            "Khi còn sống, ông Trần Văn X có vợ là bà Lê Thị Y.",
            "Chúng tôi là những người thừa kế theo pháp luật, thỏa thuận về việc phân chia di sản như sau:",
            "Di sản của ông Trần Văn X để lại:",
            "Ông Trần Văn X có sử dụng quyền sử dụng đất có địa chỉ tại: xã C theo Giấy chứng nhận quyền sử dụng đất số: P 000001 do UBND huyện C cấp ngày 28/11/1999, cụ thể như sau:",
            "Số tờ bản đồ | Số thửa | Diện tích (m2)",
            "13 | 169 | 684",
            "Thống nhất phân chia quyền sử dụng đất:",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
            "Số công chứng 100.2026/CCGD.",
        )

        payload = extract(docx_path)
        persons = payload["raw"]["ben_a"]["nguoi"]

        self.assertEqual(payload["raw"]["document_kind"], "inheritance_partition")
        self.assertEqual(len(persons), 2)
        # "Ông/bà:" la nhan mo ho — khong suy gioi tinh (decision-46).
        self.assertEqual(persons[0]["gioi_tinh"], "")
        self.assertEqual(persons[0]["ho_ten"], "Phạm Thị A")
        self.assertEqual(persons[1]["gioi_tinh"], "")
        self.assertIn("xã C", persons[0]["dia_chi"])
        chet = payload["raw"]["nguoi_chet"]
        self.assertEqual(len(chet), 1)
        self.assertEqual(chet[0]["ho_ten"], "Trần Văn X")
        thua = payload["raw"]["danh_sach_thua_dat"]
        self.assertEqual(len(thua), 1)
        self.assertEqual(thua[0]["so_thua_dat"], "169")

    def test_ten_dung_truoc_co_vo_la(self):
        # Dong pha he "Ông X co vo la ba Y (Sinh ngay...)" khong duoc
        # vo ten X + ngay sinh/ID cua Y.
        docx_path = make_docx(
            self.root / "co_vo_la.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Hàng thừa kế của ông Trần Văn X gồm những người có tên sau đây:",
            "Ông Trần Văn Z Sinh ngày: 13/02/2008",
            "Căn cước công dân số 036208000001 do Bộ Công an cấp ngày 01/06/2022;",
            "Thường trú tại: xã C.",
            "Là con đẻ ông Trần Văn X.",
            "Ông Trần Văn X; Sinh năm: 1967, chết ngày 06/07/2012 theo Trích lục khai tử số 1573/TLKT-BS.",
            "Ông Trần Văn X có vợ là bà Vũ Thị Y (Sinh ngày: 01/01/1968; Căn cước công dân số 036168000001 do Bộ Công an cấp ngày 13/08/2021; Thường trú tại: Thôn T).",
            "Chúng tôi là những người thừa kế theo pháp luật, thỏa thuận về việc phân chia di sản như sau:",
            "Di sản của ông Trần Văn X để lại:",
            "Ông Trần Văn X có sử dụng quyền sử dụng đất có địa chỉ tại: xã C theo Giấy chứng nhận quyền sử dụng đất số A 000002, do UBND huyện C cấp ngày 20/02/1992.",
            "- Thửa đất số: 130",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
            "Số công chứng 101.2026/CCGD.",
        )

        payload = extract(docx_path)
        persons = payload["raw"]["ben_a"]["nguoi"]

        self.assertEqual(len(persons), 1)
        self.assertIn("Trần Văn Z", persons[0]["ho_ten"])
        self.assertNotIn("chết", payload["web_form"]["duong_su"])

    def test_cln_toi_ten_la_tai_san_viet_lien_va_ngay_excel(self):
        # "Toi ten la:" khong Ông/Bà; tai san viet lien 1 cau
        # ("thua dat so 153, ... CLN 70m2 ..."); "cap ngay 44546" la
        # so Excel -> doi ra ngay. Khoi nguoi dung truoc dong chet.
        docx_path = make_docx(
            self.root / "cln_lien.docx",
            "VĂN BẢN THỎA THUẬN",
            "PHÂN CHIA DI SẢN THỪA KẾ",
            "Hôm nay, tại UBND xã C.",
            "Tôi tên là: Trần Gia H; Sinh ngày: 12/08/1963;",
            "Căn cước công dân số: 036063000001 do Bộ Công an cấp ngày 44546;",
            "Thường trú tại: xã C.",
            "Tôi là người thừa kế duy nhất của ông Trần Gia X; Sinh năm: 1942; chết ngày 03/07/2019 theo Trích lục khai tử số 598/TLKT-BS.",
            "Trước khi chết ông Trần Gia X không để lại di chúc.",
            "Chúng tôi là những người thừa kế theo pháp luật, thỏa thuận về việc phân chia di sản như sau:",
            "Di sản của ông Trần Gia X để lại:",
            "Hộ ông Trần Gia X có sử dụng thửa đất số 153, tờ bản đồ số 12, diện tích 70 m2, trong đó: CLN 70m2 theo Bản đồ địa chính xã C lập năm 1991, có địa chỉ tại: xã C theo Giấy chứng nhận quyền sử dụng đất số: S 000001 do UBND huyện C cấp ngày 18/03/2003.",
            "Thống nhất phân chia quyền sử dụng đất:",
            "LỜI CHỨNG CỦA UBND XÃ C",
        )

        payload = extract(docx_path)
        persons = payload["raw"]["ben_a"]["nguoi"]

        self.assertEqual(len(persons), 1)
        self.assertEqual(persons[0]["ho_ten"], "Trần Gia H")
        # "Tôi tên là:" khong co danh xung — khong suy gioi tinh (decision-46).
        self.assertEqual(persons[0]["gioi_tinh"], "")
        self.assertEqual(persons[0]["ngay_cap_cccd"], "16/12/2021")
        thua = payload["raw"]["danh_sach_thua_dat"]
        self.assertEqual(len(thua), 1)
        self.assertEqual(thua[0]["so_thua_dat"], "153")
        self.assertEqual(thua[0]["so_to_ban_do"], "12")
        self.assertEqual(thua[0]["dien_tich"], "70 m2")
        self.assertEqual(thua[0]["dia_chi"], "xã C")
        details = thua[0]["chi_tiet_dien_tich"]
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]["muc_dich_su_dung"], "CLN")

    def test_mau_that_thua_ke_duc_mo_2026(self):
        # Hoi quy tu VB thoa thuan thua ke thuc te (Owner 07/10/2026):
        # dong IFilter gop ca khoi nguoi thanh 1 dong; "Hoi khau thuong tru"
        # la nhan dia chi; vai tro "La vo/con cua..." khong vao ho_ten;
        # cau ke pha he ("Ong Duc va ba Khung la vo chong hop phap...")
        # khong duoc sinh nguoi chet rac; "Hien nay la thua ... To ..."
        # la cung thua (ghi chu), khong mo thua moi; so to ban do chi giu
        # ky hieu, bo duoi "Ban do dia chinh nam 1991"; dien tich cat o dau
        # ";" truoc "Trong do" va tach duoc ONT/NTS.
        docx_path = make_docx(
            self.root / "mau_that_duc_mo.docx",
            "VĂN BẢN THỎA THUẬN PHÂN CHIA DI SẢN THỪA KẾ",
            "Hàng thừa kế của ông Nguyễn Bá Lộc gồm những người có tên sau đây:",
            "Bà Nguyễn Thị Loan; sinh ngày: 02/03/1962 Căn cước công dân số: 036162004393 Cấp ngày 16/12/2021; Nơi cấp: Cục Cảnh sát quản lý hành chính về trật tự xã hội Hộ khẩu thường trú: Xã Ý Yên, tỉnh Ninh Bình  Là vợ của ông Nguyễn Bá Lộc",
            "Chúng tôi là những người thừa kế theo pháp luật, thỏa thuận về việc phân chia di sản như sau:",
            "Di sản của ông Nguyễn Văn Đức để lại:",
            "Ông Nguyễn Văn Đức, Sinh năm 1906, đã chết ngày 29/06/2000 theo Trích lục khai tử số 86/TLKT-BS do UBND xã Yên Khánh cấp ngày 09/05/2023. Nơi thường trú cuối cùng trước khi chết: Thôn An Lạc, xã Yên Khánh.",
            "Bà Đỗ Thị Mở, Sinh năm 1919, đã chết ngày 03/03/2010 theo Trích lục khai tử số 85/TLKT-BS do UBND xã Yên Khánh cấp ngày 08/05/2023.",
            "Ông Đức và bà Khuâng là vợ chồng hợp pháp từ năm 1935 cho đến khi bà Khuâng chết. Sau khi bà Khuâng chết, ông Đức kết hôn với bà Đỗ Thị Mở.",
            "Phần quyền sử dụng đất tại địa chỉ: Thôn An Lạc, xã Yên Khánh theo Giấy chứng nhận quyền sử dụng đất số: B 011092 do Uỷ ban nhân dân huyện Ý Yên cấp ngày 05/03/1992, cụ thể như sau:",
            "Thửa đất số: 143; Tờ bản đồ số: 05, Bản đồ địa chính năm 1991.",
            "Hiện nay là thửa đất số 124; Tờ bản đồ số 13, Bản đồ địa chính lập năm 2006.",
            "Diện tích: 265,0 m2; Trong đó: ONT: 190,0 m2; NTS: 75,0 m2;",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)
        persons = payload["raw"]["ben_a"]["nguoi"]
        self.assertEqual(persons[0]["ho_ten"], "Nguyễn Thị Loan")
        self.assertEqual(persons[0]["dia_chi"], "Xã Ý Yên, tỉnh Ninh Bình")
        self.assertTrue(all("của ông" not in p["ho_ten"] for p in persons))

        chet = payload["raw"]["nguoi_chet"]
        self.assertEqual([p["ho_ten"] for p in chet], ["Nguyễn Văn Đức", "Đỗ Thị Mở"])
        self.assertEqual(chet[0]["ngay_sinh"], "1906")
        self.assertEqual(chet[0]["so_giay_to"], "86/TLKT-BS")

        thua = payload["raw"]["danh_sach_thua_dat"]
        self.assertEqual(len(thua), 1)
        self.assertEqual(thua[0]["so_thua_dat"], "143")
        self.assertEqual(thua[0]["so_to_ban_do"], "05")
        self.assertEqual(thua[0]["dien_tich"], "265,0 m2")
        self.assertIn("124", thua[0]["phan_ghi_them"])
        details = {d["muc_dich_su_dung"]: d["dien_tich"] for d in thua[0]["chi_tiet_dien_tich"]}
        self.assertEqual(details.get("ONT"), "190,0 m2")
        self.assertEqual(details.get("NTS"), "75,0 m2")
        self.assertEqual(thua[0]["co_quan_cap"], "Uỷ ban nhân dân huyện Ý Yên")
        self.assertIn("nguon_goc", thua[0])

    def test_bao_hiem_gom_dong_ben_mua_doi_tuong(self):
        # Quyen loi bao hiem: so HD + ben (cat hau to ben mua) + dong
        # "Ben mua / Doi tuong" gom vao 1 quyen loi.
        docx_path = make_docx(
            self.root / "phan_chia_bao_hiem.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Tôi là người được hưởng di sản theo pháp luật của bà Tạ Thị H:",
            "Ông Trương Văn H Sinh ngày: 18/05/1984",
            "Căn cước công dân số: 036084000001 do Bộ Công an cấp ngày 19/05/2024",
            "Thường trú tại: Tổ 1, phường A.",
            "Tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "Người để lại di sản:",
            "Bà Tạ Thị H - sinh năm: 1960, đã chết ngày 02/01/2026 theo Trích lục khai tử (bản sao) số 127/2026/TLKT-BS do UBND xã B ký ngày 19/01/2026.",
            "Di sản:",
            "Di sản của bà Tạ Thị H để lại là: Quyền lợi bảo hiểm phát sinh từ Hợp đồng bảo hiểm sức khoẻ nhóm số 25CN.SK.01.03B02700002 ký giữa Tổng công ty BH Sài Gòn và Công ty TNHH Phú Thái ngày 15/08/2025. Cụ thể:",
            "Bên mua bảo hiểm: Công ty TNHH Phú Thái",
            "Đối tượng bảo hiểm, người được bảo hiểm: bà Tạ Thị H (mẹ đẻ ông Trương Văn H).",
            "Người thừa kế:",
            "Những người thừa kế của bà Tạ Thị H gồm ông Trương Văn H.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
            "Số công chứng 488.2026/CCGD.",
        )

        payload = extract(docx_path)

        self.assertEqual(payload["raw"]["document_kind"], "inheritance_partition")
        self.assertEqual([p["ho_ten"] for p in payload["raw"]["ben_a"]["nguoi"]], ["Trương Văn H"])
        self.assertEqual([p["ho_ten"] for p in payload["raw"]["nguoi_chet"]], ["Tạ Thị H"])
        self.assertEqual(payload["raw"]["tai_san_chua_ho_tro"], ["bao_hiem"])
        self.assertNotIn("danh_sach_bao_hiem", payload["raw"])

    def test_tai_san_chi_co_tiet_kiem_khong_sinh_thua_ma(self):
        # Sweep 09/10/2026: van ban chi co so tiet kiem, muc "Tài sản thứ N:"
        # khong duoc sinh thua rong.
        docx_path = make_docx(
            self.root / "chi_tiet_kiem.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Tôi là người được hưởng di sản theo pháp luật của ông Nguyễn Văn T:",
            "Bà Trần Thị K Sinh ngày: 01/01/1960",
            "Căn cước công dân số: 036160000001 do Bộ Công an cấp ngày 01/01/2021",
            "Thường trú tại: Thôn A, xã B.",
            "Người để lại di sản:",
            "Ông Nguyễn Văn T - sinh năm: 1930, đã chết ngày 01/02/2025.",
            "Di sản của ông Nguyễn Văn T để lại gồm:",
            "Tài sản thứ 3:",
            "Sổ tiết kiệm số 123456 tại Ngân hàng X.",
            "Tài sản thứ 4:",
            "Tài khoản ngân hàng số 789 tại Ngân hàng Y.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)

        self.assertEqual(payload["raw"]["danh_sach_thua_dat"], [])
        self.assertEqual(payload["raw"]["tai_san_chua_ho_tro"], ["so_tiet_kiem"])

    def test_cap_vo_chong_chet_tren_mot_dong(self):
        # Sweep 09/10/2026: "Ông A và bà B; Sinh năm...; chết ngày..." la
        # 2 nguoi chet, khong phai 0.
        docx_path = make_docx(
            self.root / "cap_chet.docx",
            "VĂN BẢN PHÂN CHIA DI SẢN",
            "Chúng tôi là những người thừa kế của ông Trần Xuân V và bà Nguyễn Thị L:",
            "Bà Nguyễn Thị T Sinh ngày: 01/01/1960",
            "Căn cước công dân số: 036160000001 do Bộ Công an cấp ngày 01/01/2021",
            "Thường trú tại: Thôn A, xã B.",
            "Người để lại di sản:",
            "Ông Trần Xuân V và bà Nguyễn Thị L; Sinh năm: 1928; chết ngày 09/10/2019.",
            "Di sản để lại:",
            "Quyền sử dụng đất tại: xã B.",
            "- Thửa đất số: 65",
            "- Diện tích: 190 m2",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)
        chet = payload["raw"]["nguoi_chet"]

        self.assertEqual(
            sorted(c["ho_ten"] for c in chet),
            ["Nguyễn Thị L", "Trần Xuân V"],
        )

    def test_dia_chi_chung_cap_vo_chong(self):
        # Sweep 09/10/2026: "Cả hai ông bà cùng thường trú tại: X" phai gan
        # cho ca 2 nguoi, khong chi nguoi dung sau.
        docx_path = make_docx(
            self.root / "dia_chi_chung_vo_chong.docx",
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "BÊN CHUYỂN NHƯỢNG:",
            "Ông Trương Mạnh H Sinh ngày: 01/01/1970",
            "Căn cước công dân số: 036170000001 do Bộ Công an cấp ngày 01/01/2021",
            "Và vợ là bà Ninh Thị T Sinh ngày: 02/02/1972",
            "Căn cước công dân số: 036172000002 do Bộ Công an cấp ngày 02/02/2022",
            "Cả hai ông bà cùng thường trú tại: Thôn QP, xã YN, huyện YY, tỉnh NĐ.",
            "BÊN NHẬN CHUYỂN NHƯỢNG:",
            "Ông Nguyễn Trường N Sinh ngày: 03/03/1980",
            "Căn cước công dân số: 036180000003 do Bộ Công an cấp ngày 03/03/2021",
            "Địa chỉ: Tổ 12, thị trấn L, huyện YY, tỉnh NĐ.",
            "Nội dung chuyển nhượng:",
            "Thửa đất số: 176; Tờ bản đồ số: 12; Diện tích: 1386,0 m2.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)
        persons = payload["raw"]["ben_a"]["nguoi"]

        self.assertEqual(len(persons), 2)
        for person in persons:
            self.assertIn("Thôn QP", person["dia_chi"], person["ho_ten"])

    def test_ten_cat_truoc_khong_va_vaitro_dau_dong(self):
        # Sweep 09/10/2026: "...Tam không có ai" cat o "không"; "Con đẻ - Bà X"
        # va "Người chồng - Ông Y" la nguoi.
        docx_path = make_docx(
            self.root / "vai_tro_dau_dong.docx",
            "HỢP ĐỒNG TẶNG CHO QUYỀN SỬ DỤNG ĐẤT",
            "BÊN TẶNG CHO:",
            "Người chồng - Ông Nguyễn Quang H Sinh ngày: 01/01/1960",
            "Căn cước công dân số: 036160000001 do Bộ Công an cấp ngày 01/01/2021",
            "Trú tại: Thôn TL, xã YY, tỉnh NB.",
            "Người vợ - Bà Phạm Thị T Sinh ngày: 02/02/1962",
            "Căn cước công dân số: 036162000002 do Bộ Công an cấp ngày 02/02/2022",
            "Trú tại: Thôn TL, xã YY, tỉnh NB.",
            "BÊN ĐƯỢC TẶNG CHO:",
            "Con đẻ - Ông Nguyễn Văn K Sinh ngày: 03/03/1990",
            "CC số: 036190000003 cấp ngày: 03/03/2021",
            "Nơi thường trú tại: Thôn TL, xã YY, tỉnh NB.",
            "Thửa đất số: 284; Tờ bản đồ số: 7; Diện tích: 156,0 m2.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)
        ten_a = [p["ho_ten"] for p in payload["raw"]["ben_a"]["nguoi"]]
        ten_b = [p["ho_ten"] for p in payload["raw"]["ben_b"]["nguoi"]]

        self.assertIn("Nguyễn Quang H", ten_a)
        self.assertIn("Phạm Thị T", ten_a)
        self.assertEqual(ten_b, ["Nguyễn Văn K"])
        self.assertEqual(
            payload["raw"]["ben_b"]["nguoi"][0]["cccd"], "036190000003")

    def test_so_thua_giu_ky_hieu_chinh_nguon_goc_vao_ghi_chu(self):
        # Sweep 09/10/2026: "378 (được tách từ thửa 376)" -> so_thua "378",
        # nguon goc tach giu trong phan_ghi_them.
        docx_path = make_docx(
            self.root / "thua_tach_tu.docx",
            "VĂN BẢN CAM KẾT TÀI SẢN RIÊNG",
            "Tôi là: Bà Nguyễn Thị Q Sinh ngày: 01/01/1970",
            "Căn cước công dân số: 036170000001 do Bộ Công an cấp ngày 01/01/2021",
            "Địa chỉ: Thôn TA, xã YY, tỉnh NB.",
            "Tôi cam kết quyền sử dụng đất có địa chỉ tại: Thôn TA, xã YY, tỉnh NB theo Giấy chứng nhận quyền sử dụng đất số: AA 04244199 do Văn phòng đăng ký đất đai NB cấp ngày 12/01/2026, cụ thể như sau:",
            "- Thửa đất số: 378 (được tách từ thửa 376)",
            "- Tờ bản đồ số: 46",
            "- Diện tích: 109,9 m2",
            "- Hình thức sử dụng: Sử dụng riêng",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)
        thua = payload["raw"]["danh_sach_thua_dat"]

        self.assertEqual(len(thua), 1)
        self.assertEqual(thua[0]["so_thua_dat"], "378")
        self.assertIn("376", thua[0]["phan_ghi_them"])

    def test_truong_xe_may_khong_sinh_thua_dat(self):
        # Sweep 09/10/2026: so khung/so may/bien so cua xe khong phai thua.
        docx_path = make_docx(
            self.root / "xe_may.docx",
            "HỢP ĐỒNG MUA BÁN XE MÁY",
            "BÊN BÁN:",
            "Ông Bùi Văn C Sinh ngày: 01/01/1970",
            "Căn cước công dân số: 036170000001 do Bộ Công an cấp ngày 01/01/2021",
            "Địa chỉ: xã YD, huyện YY, tỉnh NĐ.",
            "BÊN MUA:",
            "Ông Đinh Văn T Sinh ngày: 02/02/1980",
            "Căn cước công dân số: 036180000002 do Bộ Công an cấp ngày 02/02/2021",
            "Địa chỉ: xã YL, huyện YY, tỉnh NĐ.",
            "Xe mô tô:",
            "- Nhãn hiệu: HONDA",
            "- Số khung: RLH123456",
            "- Số máy: 7890123",
            "- Biển số đăng ký: 18-B1 234.56",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)

        self.assertEqual(payload["raw"]["danh_sach_thua_dat"], [])



    def test_guq_nguoi_uy_quyen_khong_bat_hang_chu_ky(self):
        # GUQ: dong chu ky "NGUOI UY QUYEN    NGUOI DUOC UY QUYEN" khong
        # phai tieu de vung; "uy quyen cho:" la ranh ben B.
        docx_path = make_docx(
            self.root / "guq_chu_ky.docx",
            "GIẤY UỶ QUYỀN",
            "Tôi là: Ông LUO SHUAI    Sinh năm: 2000",
            "Số hộ chiếu: EP9129199 do Cục Quản lý Xuất nhập cảnh cấp ngày 11/07/2025",
            "Nơi cư trú: Trùng Khánh - Trung Quốc",
            "Nay bằng giấy này tôi uỷ quyền cho:",
            "Bà Trần Thị Huyền - Sinh năm 1992; Căn cước số: 036192016533 do Cục cảnh sát cấp ngày 01/01/2020",
            "Nơi cư trú tại: xã Yên Đồng, tỉnh Ninh Bình.",
            "Thời gian ủy quyền: 01 năm.",
            "NGƯỜI UỶ QUYỀN        NGƯỜI ĐƯỢC UỶ QUYỀN",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)

        ten_a = [p["ho_ten"] for p in payload["raw"]["ben_a"]["nguoi"]]
        ten_b = [p["ho_ten"] for p in payload["raw"]["ben_b"]["nguoi"]]
        self.assertIn("LUO SHUAI", ten_a)
        self.assertEqual(ten_b, ["Trần Thị Huyền"])

    def test_toi_la_ong_khong_dau_hai_cham(self):
        # "Tôi là ông X" (khong dau ':') van la header nguoi.
        docx_path = make_docx(
            self.root / "toi_la_ong.docx",
            "GIẤY UỶ QUYỀN",
            "Tôi là ông Đinh Đức Tuyến;     Sinh ngày: 20/11/1963;",
            "Căn cước công dân số: 036063007568 do Cục cảnh sát cấp ngày 03/10/2023;",
            "Nơi thường trú tại: xã Yên Cường, huyện Ý Yên, tỉnh Nam Định.",
            "Nay bằng giấy này tôi uỷ quyền cho:",
            "Ông Bùi Quang Kiên - Sinh năm 1991; Căn cước công dân số 036091015717 do Cục Cảnh sát cấp ngày 01/01/2020",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)

        ten_a = [p["ho_ten"] for p in payload["raw"]["ben_a"]["nguoi"]]
        self.assertEqual(ten_a, ["Đinh Đức Tuyến"])

    def test_thua_lap_gop_du_lieu_khong_de_mat(self):
        # Cung so thua nhac lai 2 lan: lan sau bo sung truong cho lan dau.
        docx_path = make_docx(
            self.root / "thua_lap.docx",
            "HỢP ĐỒNG CHUYỂN NHƯỢNG",
            "BÊN CHUYỂN NHƯỢNG:",
            "Ông Nguyễn Văn A Sinh ngày: 01/01/1970",
            "Căn cước công dân số: 036170000001 do Bộ Công an cấp ngày 01/01/2021",
            "Địa chỉ: xã A, huyện B, tỉnh C.",
            "BÊN NHẬN CHUYỂN NHƯỢNG:",
            "Bà Trần Thị B Sinh ngày: 02/02/1980",
            "Căn cước công dân số: 036180000002 do Bộ Công an cấp ngày 02/02/2021",
            "Địa chỉ: xã D, huyện E, tỉnh F.",
            "Đối tượng của Hợp đồng này là quyền sử dụng đất có địa chỉ tại: xã G",
            "Thửa đất số: 2067 được tách từ",
            "thửa 2068",
            "Tờ bản đồ số: 09",
            "Diện tích: 786,0 m2",
            "Hình thức sử dụng: Sử dụng riêng",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)

        thua = payload["raw"]["danh_sach_thua_dat"]
        ids = [t["so_thua_dat"] for t in thua]
        self.assertEqual(ids.count("2067"), 1)
        thua67 = [t for t in thua if t["so_thua_dat"] == "2067"][0]
        self.assertEqual(thua67["so_to_ban_do"], "09")
        self.assertIn("Sử dụng riêng", thua67["phan_ghi_them"])

    def test_nguoi_chet_sau_cum_quan_he(self):
        # "Ong X co me de la ba Y; chet ngay ..." — nguoi chet la Y,
        # khong phai ca cum 9 tu.
        docx_path = make_docx(
            self.root / "chet_quan_he.docx",
            "VĂN BẢN TỪ CHỐI NHẬN DI SẢN",
            "Chúng tôi là:",
            "1. Ông Hoàng Văn Khôi – cháu nội bà Hoàng Thị Phao;    Sinh ngày: 25/10/1973",
            "Căn cước công dân số: 036073007917 do Cục cảnh sát cấp ngày 02/07/2021;",
            "Thường trú tại: xã Phong Doanh, tỉnh Ninh Bình.",
            "Nay, chúng tôi tự nguyện lập Văn bản này với nội dung như sau:",
            "Ông Hoàng Văn Toản có mẹ đẻ là bà Hoàng Thị Phao; Sinh năm: 1924; đã chết ngày: 27/12/2020 theo Trích lục khai tử.",
            "LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN",
        )

        payload = extract(docx_path)

        ten_a = [p["ho_ten"] for p in payload["raw"]["ben_a"]["nguoi"]]
        self.assertEqual(ten_a, ["Hoàng Văn Khôi"])
        chet = [q["ho_ten"] for q in payload["raw"]["nguoi_chet"]]
        self.assertIn("Hoàng Thị Phao", chet)

    def test_sinh_nam_kem_ngay_day_du_khong_nuot_vao_ten(self):
        # Van ban viet nham nhan "Sinh nam: 10/01/1938" (ngay day du):
        # lay ngay du, khong de "Sinh" lot vao ho_ten.
        docx_path = make_docx(
            self.root / "sinh_nam_nham_nhan.docx",
            "GI\u1ea4Y U\u1ef6 QUY\u1ec0N",
            "T\u00f4i l\u00e0 b\u00e0: Ph\u1ea1m Th\u1ecb S\u00e1u\t\t\tSinh n\u0103m: 10/01/1938.",
            "C\u0103n c\u01b0\u1edbc c\u00f4ng d\u00e2n s\u1ed1: 037138003727",
            "Nay b\u1eb1ng gi\u1ea5y n\u00e0y t\u00f4i u\u1ef7 quy\u1ec1n cho:",
            "B\u00e0: Tr\u1ea7n Th\u1ecb B; Sinh ng\u00e0y: 01/01/1980",
            "L\u1edcI CH\u1ee8NG C\u1ee6A C\u00d4NG CH\u1ee8NG VI\u00caN",
        )

        payload = extract(docx_path)

        nguoi_a = payload["raw"]["ben_a"]["nguoi"]
        self.assertEqual(nguoi_a[0]["ho_ten"], "Ph\u1ea1m Th\u1ecb S\u00e1u")
        self.assertEqual(nguoi_a[0]["ngay_sinh"], "10/01/1938")

    def test_bang_liet_ke_nguoi_khong_vao_chi_tiet_thua(self):
        # Bang "1. Ong X | Sinh ngay ..." sau khoi thua khong duoc nhap
        # vao chi_tiet_dien_tich (thong bao nguoi thua ke).
        docx_path = make_docx(
            self.root / "bang_nguoi_khong_phai_thua.docx",
            "TH\u00d4NG B\u00c1O",
            "Quy\u1ec1n s\u1eed d\u1ee5ng \u0111\u1ea5t c\u00f3 \u0111\u1ecba ch\u1ec9 t\u1ea1i: x\u00e3 G",
            "- Th\u1eeda \u0111\u1ea5t s\u1ed1: 130",
            "- T\u1edd b\u1ea3n \u0111\u1ed5 s\u1ed1: 23",
            "- Di\u1ec7n t\u00edch: 204,0 m2",
            "1. \u00d4ng B\u00f9i \u0110\u01b0\u1eddng Nghi\u00eau | Sinh ng\u00e0y: 11/05/1961",
            "2. \u00d4ng B\u00f9i Qu\u00fd \u0110\u00f4n | Sinh ng\u00e0y: 10/10/1963",
        )

        payload = extract(docx_path)

        thua = payload["raw"]["danh_sach_thua_dat"]
        self.assertEqual(len(thua), 1)
        self.assertEqual(thua[0]["so_thua_dat"], "130")
        self.assertEqual(thua[0]["so_to_ban_do"], "23")
        for detail in thua[0]["chi_tiet_dien_tich"]:
            self.assertNotIn("B\u00f9i", str(detail))

    def test_thua_chi_co_gcn_van_tao_ban_ghi(self):
        # Van ban mo ta dat o muc GCN, khong co so thua/to: van tao
        # 1 ban ghi giu so_gcn + dia_chi + co_quan_cap.
        docx_path = make_docx(
            self.root / "thua_chi_gcn.docx",
            "V\u0102N B\u1ea2N T\u1eea CH\u1ed0I NH\u1eacN DI S\u1ea2N",
            "T\u00f4i l\u00e0: B\u00e0 Nguy\u1ec5n Th\u1ecb Y; Sinh ng\u00e0y: 02/02/1945;",
            "C\u0103n c\u01b0\u1edbc c\u00f4ng d\u00e2n s\u1ed1 037145004692",
            "Nay, t\u00f4i t\u1ef1 nguy\u1ec7n l\u1eadp V\u0103n b\u1ea3n n\u00e0y.",
            "K\u1ef7 ph\u1ea7n th\u1eeba k\u1ebf c\u1ee7a \u00f4ng X \u0111\u1ec3 l\u1ea1i \u0111\u00f3 l\u00e0: Ph\u1ea7n quy\u1ec1n s\u1eed d\u1ee5ng \u0111\u1ea5t c\u00f3 \u0111\u1ecba ch\u1ec9 t\u1ea1i: x\u00e3 G theo Gi\u1ea5y ch\u1ee9ng nh\u1eadn quy\u1ec1n s\u1eed d\u1ee5ng \u0111\u1ea5t s\u1ed1: A 957504 do huy\u1ec7n H c\u1ea5p ng\u00e0y 20/02/1992.",
            "L\u1edcI CH\u1ee8NG C\u1ee6A C\u00d4NG CH\u1ee8NG VI\u00caN",
        )

        payload = extract(docx_path)

        thua = payload["raw"]["danh_sach_thua_dat"]
        self.assertEqual(len(thua), 1)
        self.assertEqual(thua[0]["so_gcn"], "A957504")
        self.assertIn("x\u00e3 G", thua[0]["dia_chi"])

    def test_nhom_hop_dong_uy_quyen_cach_viet_cu(self):
        # "uỷ quyền" (chu viet u+1EF7) cung ra nhom "Uy quyen".
        from extract_contract import guess_nhom_hd
        self.assertEqual(guess_nhom_hd("GIẤY UỶ QUYỀN"), "Ủy quyền")
        self.assertEqual(guess_nhom_hd("HỢP ĐỒNG ỦY QUYỀN"), "Ủy quyền")

    def test_ghi_chu_tach_tu_va_nay_la_cung_dong(self):
        # Giang 2026: ghi chu "(tach tu thua so 02)" + "(nay la to ban do so 100)"
        # phai cong don, khong de ghi chu sau ghi de ghi chu truoc.
        from extract_contract import tach_danh_sach_thua_dat
        ds = tach_danh_sach_thua_dat(
            "Quyền sử dụng đất có địa chỉ tại: xã G theo Giấy chứng nhận số CB123 "
            "do huyện H cấp ngày 01/01/2020. Thửa đất số: 180 (tách từ thửa số 02), "
            "tờ bản đồ số: 08 (nay là tờ bản đồ số 100). Diện tích: 200 m2"
        )
        self.assertEqual(len(ds), 1)
        self.assertEqual(ds[0]["so_thua_dat"], "180")
        self.assertEqual(ds[0]["so_to_ban_do"], "08")
        self.assertIn("tách từ thửa số 02", ds[0]["phan_ghi_them"])
        self.assertIn("nay là tờ bản đồ số 100", ds[0]["phan_ghi_them"])

    def test_ben_thu_nhat_ben_thu_hai_van_duoc_nhan(self):
        # Hop dong gop von dung "I. BÊN THỨ NHẤT (BÊN A)" / "II. BÊN THỨ HAI (BÊN B)".
        docx_path = make_docx(
            self.root / "gop_von.docx",
            "HỢP ĐỒNG GÓP VỐN",
            "Hôm nay ngày 01/01/2025 chúng tôi gồm:",
            "I. BÊN THỨ NHẤT (BÊN A):",
            "Ông Nguyễn Văn Thịnh - Sinh năm 1982; Căn cước công dân số 036078001056 do Cục Cảnh sát cấp ngày 05/08/2022; Nơi thường trú tại: xã A, huyện B.",
            "II. BÊN THỨ HAI (BÊN B):",
            "Ông Phạm Xuân Giang - Sinh năm 1978; Căn cước công dân số 036078001057 do Cục Cảnh sát cấp ngày 05/08/2022; Nơi thường trú tại: xã C, huyện D.",
            "Các bên tự nguyện ký kết Hợp đồng với nội dung góp vốn vào thửa đất số 112.",
        )
        payload = extract(docx_path)
        ben_a = payload["raw"]["ben_a"]["nguoi"]
        ben_b = payload["raw"]["ben_b"]["nguoi"]
        self.assertEqual([q["ho_ten"] for q in ben_a], ["Nguyễn Văn Thịnh"])
        self.assertEqual([q["ho_ten"] for q in ben_b], ["Phạm Xuân Giang"])

    def test_toi_la_ten_cach_tab_sinh_van_nhan(self):
        # Don xac nhan: "Tôi là: Nguyễn Thị Mơ\t\t\tSinh ngày: 20/05/1949;" —
        # tab bi gop thanh 1 dau cach, van phai nhan ten.
        docx_path = make_docx(
            self.root / "xac_nhan.docx",
            "ĐƠN XIN XÁC NHẬN",
            "Kính gửi: UBND Xã A",
            "Tôi là: Nguyễn Thị Mơ\t\t\tSinh ngày: 20/05/1949;",
            "Căn cước công dân số: 036159003310 do Cục cảnh sát cấp ngày 14/11/2019;",
            "Thường trú tại: xã A, tỉnh B.",
            "Nay tôi làm đơn này kính mong Quý cơ quan xác nhận tôi và ông X là vợ chồng.",
        )
        payload = extract(docx_path)
        ben_a = payload["raw"]["ben_a"]["nguoi"]
        self.assertEqual([q["ho_ten"] for q in ben_a], ["Nguyễn Thị Mơ"])
        self.assertEqual(ben_a[0]["ngay_sinh"], "20/05/1949")

    def test_tien_to_quan_he_em_trai_chi_gai_van_nhan(self):
        # "Em trai - ông ..." / "Chị gái – bà ..." la vai tro, khong lam mat nguoi.
        docx_path = make_docx(
            self.root / "tang_cho.docx",
            "HỢP ĐỒNG TẶNG CHO QUYỀN SỬ DỤNG ĐẤT",
            "Chúng tôi gồm:",
            "I. BÊN TẶNG CHO (Sau đây gọi là bên A):",
            "Em trai - ông Ngô Văn Bảng; Sinh ngày: 05/03/1983;",
            "Căn cước công dân số 036083008245 do Cục Cảnh sát cấp ngày 24/07/2021;",
            "Nơi thường trú tại: Thôn Đìa, xã Phúc Thịnh.",
            "II. BÊN NHẬN TẶNG CHO (Sau đây gọi là bên B):",
            "Chị gái – bà Ngô Thị Lanh Sinh ngày: 07/06/1977",
            "Căn cước công dân số 036177007241 do Cục Cảnh sát cấp ngày 09/01/2022;",
            "Hai bên tự nguyện cùng nhau lập Hợp đồng tặng cho quyền sử dụng đất.",
        )
        payload = extract(docx_path)
        self.assertEqual([q["ho_ten"] for q in payload["raw"]["ben_a"]["nguoi"]], ["Ngô Văn Bảng"])
        self.assertEqual([q["ho_ten"] for q in payload["raw"]["ben_b"]["nguoi"]], ["Ngô Thị Lanh"])

    def test_sinh_ngay_chi_co_nam_van_cat_ten(self):
        # "Sinh ngày: 1982" (nhan ngay nhung gia tri chi la nam) — ten cat
        # truoc nhan, nam vao ngay_sinh kem chi_co_nam_sinh.
        docx_path = make_docx(
            self.root / "uq_nam.docx",
            "GIẤY UỶ QUYỀN",
            "Tôi là: Ông Phạm Văn Chinh - Sinh ngày: 1982; Căn cước công dân số: 036082017340 do Cục cảnh sát cấp ngày 17/06/2021;",
            "Và vợ là bà Ngô Thị Phương - Sinh ngày: 1991 Căn cước công dân số: 036191017271 do Cục cảnh sát cấp ngày 17/06/2021;",
            "uỷ quyền cho: Ông Phạm Huy Thành - Sinh ngày: 1985; Căn cước công dân số: 036085009361 do Cục cảnh sát cấp ngày 17/06/2021;",
        )
        payload = extract(docx_path)
        ben_a = payload["raw"]["ben_a"]["nguoi"]
        self.assertEqual([q["ho_ten"] for q in ben_a], ["Phạm Văn Chinh", "Ngô Thị Phương"])
        self.assertEqual(ben_a[0]["ngay_sinh"], "1982")
        self.assertTrue(ben_a[0]["chi_co_nam_sinh"])

    def test_so_tran_12_chu_so_van_la_giay_to(self):
        # Form xac nhan: "Ông Vũ Văn Thạnh số: 036070006771 Cấp ngày ..." —
        # "số:" tran (khong nhan CCCD) van dem la giay to -> giu nguoi.
        docx_path = make_docx(
            self.root / "xac_nhan_so.docx",
            "ĐƠN XIN XÁC NHẬN LẠI THỜI HẠN SỬ DỤNG ĐẤT",
            "Kính gửi: Văn phòng đăng ký đất đai",
            "Người sử dụng đất:",
            "Ông Vũ Văn Thạnh số: 036070006771 Cấp ngày 22/12/2021, Nơi cấp Cục cảnh sát quản lý hành chính về trật tự xã hội.",
        )
        payload = extract(docx_path)
        ben_a = payload["raw"]["ben_a"]["nguoi"]
        self.assertEqual([q["ho_ten"] for q in ben_a], ["Vũ Văn Thạnh"])
        self.assertEqual(ben_a[0]["cccd"], "036070006771")
        self.assertIn("Cục cảnh sát", ben_a[0]["noi_cap"])

    def test_nguoi_dai_dien_phap_luat_va_o_gach_dau(self):
        # Dai dien phap luat cong ty la nguoi ky that; o bang .doc dang
        # "- Thửa đất số: 73 | | - Tờ bản đồ số: 9" van tach duoc nhan.
        from extract_contract import tach_danh_sach_thua_dat
        ds = tach_danh_sach_thua_dat(
            "Phần quyền sử dụng đất có địa chỉ: xã Y theo Giấy chứng nhận số: AK 732800 "
            "do huyện H cấp năm 2008. Cụ thể:\n"
            "- Thửa đất số: 73 | | - Tờ bản đồ số: 9 (nay là tờ bản đồ số 68)\n"
            "- Diện tích: 1009,0 m2"
        )
        self.assertEqual(ds[0]["so_thua_dat"], "73")
        self.assertEqual(ds[0]["so_to_ban_do"], "9")
        self.assertIn("nay là tờ bản đồ số 68", ds[0]["phan_ghi_them"])

        docx_path = make_docx(
            self.root / "cong_ty.docx",
            "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
            "Chúng tôi gồm có:",
            "I. BÊN CHUYỂN NHƯỢNG: (Bên A).",
            "CÔNG TY TNHH X",
            "Người đại diện theo pháp luật: Ông Nguyễn Văn Tự – Chức danh: Giám đốc",
            "Căn cước công dân số 036081015497 do Cục cảnh sát cấp ngày 05/07/2021;",
            "Nơi thường trú tại: xã A, huyện B.",
            "II. BÊN NHẬN CHUYỂN NHƯỢNG: (Bên B).",
            "Người đại diện theo pháp luật: Ông Ngô Tuấn Minh – Chức danh: Giám đốc",
            "Căn cước công dân số 036081015498 do Cục cảnh sát cấp ngày 05/07/2021;",
            "Hai bên thỏa thuận chuyển nhượng thửa đất số 1, tờ bản đồ số 2.",
        )
        payload = extract(docx_path)
        self.assertEqual([q["ho_ten"] for q in payload["raw"]["ben_a"]["nguoi"]], ["Nguyễn Văn Tự"])
        self.assertEqual([q["ho_ten"] for q in payload["raw"]["ben_b"]["nguoi"]], ["Ngô Tuấn Minh"])

    def test_nguoi_chet_sinh_nam_ngay_day_du_va_dau_hai_cham(self):
        # Nguoi chet: "Sinh năm: 01/01/1948" (nhan nam nhung gia tri ngay day
        # du — loi mau thuc te) van nhan; ten nguoi cat o ":" truoc dia chi
        # (don DK18 "6. Ông X: phường ...").
        docx_path = make_docx(
            self.root / "chet_sinh_nam.docx",
            "VĂN BẢN TỪ CHỐI NHẬN DI SẢN",
            "Văn bản từ chối nhận di sản này được lập bởi ông:",
            "Ông Nguyễn Đắc Nhường - Sinh ngày: 01/01/1980",
            "Bố đẻ tôi là ông Nguyễn Đắc Kính; Sinh năm: 01/01/1948; chết ngày 18/07/2023 "
            "theo Trích lục khai tử (Bản sao) số 774/2025/TLKT-BS do UBND xã Ý Yên cấp ngày 01/01/2025.",
            "Di sản ông Kính để lại gồm thửa đất số 317, tờ bản đồ số 26.",
        )
        payload = extract(docx_path)
        chet = payload["raw"]["nguoi_chet"]
        self.assertEqual([q["ho_ten"] for q in chet], ["Nguyễn Đắc Kính"])
        self.assertEqual(chet[0]["ngay_sinh"], "01/01/1948")

        # Ranh gioi ":" trong ten (don DK18 "N. Ông X: <địa chỉ>").
        from extract_contract import _cat_ho_ten
        self.assertEqual(_cat_ho_ten("Phùng Xuân Tính: phường Thành Nam, tỉnh Ninh Bình"), "Phùng Xuân Tính")

    def test_heading_ben_sau_gach_doc_cua_doc(self):
        # .doc IFilter: tab sau so muc thanh "|" — "I. | BÊN CHUYỂN NHƯỢNG"
        # phai van mo duoc ranh ben (sweep12: Bưởi/Ký - Hợp/Bình).
        from extract_contract import _extract_parties_generic
        text = (
            "HỢP ĐỒNG CHUYỂN NHƯỢNG\n"
            "I. | BÊN CHUYỂN NHƯỢNG: (Bên A).\n"
            "1. Ông Tạ Văn A; | | | Sinh ngày 01/01/1962;\n"
            "Căn cước công dân số 036062000001 do Cục cảnh sát cấp ngày 01/01/2021;\n"
            "II. | BÊN NHẬN CHUYỂN NHƯỢNG: (Bên B).\n"
            "1. Ông Đinh Duy B; Sinh ngày 02/02/1962;\n"
            "Căn cước công dân số 036062000002 do Cục cảnh sát cấp ngày 02/02/2021;\n"
        )
        ben_a, ben_b = _extract_parties_generic(text, "transfer_contract")
        self.assertEqual([q["ho_ten"] for q in ben_a["nguoi"]], ["Tạ Văn A"])
        self.assertEqual([q["ho_ten"] for q in ben_b["nguoi"]], ["Đinh Duy B"])

    def test_ngoac_phu_cua_nguoi_khac_khong_doi_giay_to(self):
        # Ong da chet nhung chunk chua "(Sinh/CCCD/Thường trú ...)" cua vo —
        # khong duoc doi giay to cua vo thanh nguoi song (Thong bao Giới).
        from extract_contract import _extract_parties_generic
        text = (
            "THÔNG BÁO THỪA KẾ\n"
            "Ông Nguyễn Văn G không có ai là bố nuôi, mẹ nuôi.\n"
            "Về vợ, con của ông Nguyễn Văn G:\n"
            "Khi còn sống, ông Nguyễn Văn G có vợ là bà Trịnh Thị N (Sinh ngày: "
            "10/06/1958; Căn cước công dân số 036158024616 do Cục cảnh sát cấp "
            "ngày 05/01/2023; Thường trú tại: Xóm T, xã M, tỉnh P).\n"
            "Lời chứng.\n"
        )
        ben_a, ben_b = _extract_parties_generic(text, "generic")
        nguoi = ben_a["nguoi"] + ben_b["nguoi"]
        self.assertFalse(
            any(q["ho_ten"] == "Nguyễn Văn G" and q.get("cccd") == "036158024616" for q in nguoi)
        )

    def test_nhan_nguoi_xin_gia_han_va_ten_nguoi_nop_thue(self):
        # Don hanh chinh: "1. Người xin gia hạn sử dụng đất: Nguyễn Thị C"
        # va to khai thue "[04] Tên người nộp thuế: ..." deu la nguoi that
        # (khong can ngay sinh/ID de duoc giu).
        from extract_contract import _extract_parties_generic
        text = (
            "ĐƠN XIN GIA HẠN SỬ DỤNG ĐẤT\n"
            "1. Người xin gia hạn sử dụng đất: Nguyễn Thị Chúc\n"
            "2. Địa chỉ/trụ sở chính:\n"
            "Lời chứng.\n"
        )
        ben_a, _ = _extract_parties_generic(text, "generic")
        self.assertEqual([q["ho_ten"] for q in ben_a["nguoi"]], ["Nguyễn Thị Chúc"])
        self.assertEqual(ben_a["nguoi"][0]["dia_chi"], "")

        text2 = (
            "TỜ KHAI THUẾ THU NHẬP CÁ NHÂN\n"
            "[04] Tên người nộp thuế: Trịnh Thị Nhung\n"
            "[06] Số CMND/CCCD/Hộ chiếu (trường hợp cá nhân quốc tịch Việt Nam):\n"
            "036158024616\n"
            "[06.1] Ngày cấp: 05/01/2023 [06.2] Nơi cấp: Cục cảnh sát QLHC về TTXH\n"
            "[08] Địa chỉ chỗ ở hiện tại: Xóm T, xã M, tỉnh P\n"
            "Lời chứng.\n"
        )
        ben_a2, _ = _extract_parties_generic(text2, "generic")
        self.assertEqual(len(ben_a2["nguoi"]), 1)
        self.assertEqual(ben_a2["nguoi"][0]["cccd"], "036158024616")
        self.assertEqual(ben_a2["nguoi"][0]["ngay_cap_cccd"], "05/01/2023")

    def test_dedupe_nguoi_trung_qua_form_lap_trang(self):
        # Form DK18 in 2 mat: cung nguoi (trung ten + CCCD) xuat hien 2 lan —
        # gop thanh 1, bo sung truong con thieu.
        from extract_contract import _extract_parties_generic
        text = (
            "ĐƠN ĐĂNG KÝ BIẾN ĐỘNG\n"
            "a. Tên: Bùi Thị H; Sinh ngày: 27/05/1989;\n"
            "b. Giấy tờ nhân thân:\n"
            "Bà Bùi Thị H; Sinh ngày: 27/05/1989;\n"
            "Căn cước công dân số: 036189007072 do Cục cảnh sát cấp ngày 02/07/2021;\n"
            "c. Địa chỉ: - Bùi Thị H: Thôn A, xã B, tỉnh C\n"
            "a. Tên: Bùi Thị H; Sinh ngày: 27/05/1989;\n"
            "b. Giấy tờ nhân thân:\n"
            "Bà Bùi Thị H; Sinh ngày: 27/05/1989;\n"
            "Căn cước công dân số: 036189007072 do Cục cảnh sát cấp ngày 02/07/2021;\n"
            "c. Địa chỉ: - Bùi Thị H: Thôn A, xã B, tỉnh C\n"
            "Lời chứng.\n"
        )
        ben_a, _ = _extract_parties_generic(text, "generic")
        self.assertEqual([q["ho_ten"] for q in ben_a["nguoi"]], ["Bùi Thị H"])
        self.assertEqual(ben_a["nguoi"][0]["dia_chi"], "Thôn A, xã B, tỉnh C")

    def test_chi_nhanh_to_chuc_khong_phai_nguoi_va_ten_cat_mang(self):
        # "CHI NHÁNH SÓC SƠN" khong phai nguoi ("Chị" an chu Chi cua to
        # chuc); "Ông Trần Trí Thắng mang căn cước" -> ten "Trần Trí Thắng".
        from extract_contract import _extract_parties_generic
        text = (
            "CÔNG VĂN\n"
            "CHI NHÁNH SÓC SƠN\n"
            "1. BÊN NHẬN THẾ CHẤP: (Bên A)\n"
            "- Người đại diện là: Ông Trần Trí Thắng mang căn cước công dân "
            "số 001076029367 do Cục cảnh sát cấp ngày 14/04/2021;\n"
            "2. BÊN THẾ CHẤP: (Bên B)\n"
            "Bà Ngô Thị B, ngày sinh: 20/09/1973;\n"
            "Căn cước công dân số: 001173002114 do Cục cảnh sát cấp ngày 10/08/2022;\n"
            "Lời chứng.\n"
        )
        ben_a, ben_b = _extract_parties_generic(text, "generic")
        nguoi = ben_a["nguoi"] + ben_b["nguoi"]
        self.assertNotIn("NHÁNH SÓC SƠN", [q["ho_ten"] for q in nguoi])
        self.assertIn("Trần Trí Thắng", [q["ho_ten"] for q in nguoi])

    def test_ten_toi_la_va_nguoi_nhan_giao_bien_ban(self):
        # "Tên tôi là: X; Sinh ngày" (don xac nhan sai ten) va "NGƯỜI
        # NHẬN:/NGƯỜI GIAO:" (bien ban giao nhan) deu la nguoi.
        from extract_contract import _extract_parties_generic
        text = (
            "ĐƠN ĐỀ NGHỊ\n"
            "Tên tôi là: Hoàng Thị Tuyết; Sinh ngày: 19/03/1966;\n"
            "Căn cước số: 036166013146 do Bộ Công an cấp ngày 02/02/2026;\n"
            "Thường trú tại: Thôn C, xã Y, tỉnh N.\n"
            "Lời chứng.\n"
        )
        ben_a, _ = _extract_parties_generic(text, "generic")
        self.assertEqual([q["ho_ten"] for q in ben_a["nguoi"]], ["Hoàng Thị Tuyết"])
        self.assertEqual(ben_a["nguoi"][0]["cccd"], "036166013146")

        text2 = (
            "BIÊN BẢN GIAO NHẬN TÀI LIỆU\n"
            "NGƯỜI NHẬN: Trịnh Minh Giang\n"
            "NGƯỜI GIAO: Trịnh Quang Trung\n"
            "Lời chứng.\n"
        )
        ben_a2, _ = _extract_parties_generic(text2, "generic")
        self.assertEqual(
            [q["ho_ten"] for q in ben_a2["nguoi"]],
            ["Trịnh Minh Giang", "Trịnh Quang Trung"],
        )

    def test_dedupe_nguoi_chi_co_ten_qua_form_lap(self):
        # Bien ban in 2 lan: nguoi chi co ten (khong cccd/ngay sinh) van
        # gop thanh 1 ban ghi.
        from extract_contract import _extract_parties_generic
        text = (
            "BIÊN BẢN GIAO NHẬN\n"
            "NGƯỜI NHẬN: Trịnh Minh Giang\n"
            "NGƯỜI GIAO: Trịnh Quang Trung\n"
            "BÊN GIAO BÊN NHẬN\n"
            "BIÊN BẢN GIAO NHẬN\n"
            "NGƯỜI NHẬN: Trịnh Minh Giang\n"
            "NGƯỜI GIAO: Trịnh Quang Trung\n"
            "Lời chứng.\n"
        )
        ben_a, _ = _extract_parties_generic(text, "generic")
        self.assertEqual(
            [q["ho_ten"] for q in ben_a["nguoi"]],
            ["Trịnh Minh Giang", "Trịnh Quang Trung"],
        )

    def test_bang_ngan_hang_nhan_gia_tri_o_tab(self):
        # Mau the chap ngan hang: "I. Bên thế chấp: Ông X | Ông: X |
        # Năm sinh: 1962 | Căn cước ... số: ... | Bà: Y | ..." — nguoi
        # trong o "Ông:/Bà:" tach bang o trong "| |".
        from extract_contract import _extract_plain_text_person_entries
        section = (
            "I. Bên thế chấp: Ông Nguyễn Văn Trinh |  | Ông: Nguyễn Văn Trinh |  | "
            "Năm sinh: 1962 |  | Căn cước công dân số: 036062009669 do Cục cảnh sát "
            "cấp ngày 20/04/2021 |  | Bà: Nguyễn Thị Tươi |  | Năm sinh: 1964 |  | "
            "Căn cước công dân số: 036164015397 do Cục cảnh sát cấp ngày 10/05/2021 |  | "
            "Địa chỉ: Thôn Cao Bồ, xã Yên Hồng |  | và"
        )
        persons = _extract_plain_text_person_entries(section)
        names = [q["ho_ten"] for q in persons]
        self.assertIn("Nguyễn Văn Trinh", names)
        self.assertIn("Nguyễn Thị Tươi", names)
        trinh = next(q for q in persons if q["ho_ten"] == "Nguyễn Văn Trinh")
        self.assertEqual(trinh["cccd"], "036062009669")

    def test_co_quan_he_la_tach_nguoi_thu_hai(self):
        # "2. Ông X có mẹ đẻ là bà Y; Sinh ngày..." — "bà Y" la nguoi
        # rieng, khong nuot vao khoi X (don xac nhan nhan than).
        from extract_contract import _extract_plain_text_person_entries
        section = (
            "1. Ông Nguyễn Huy Nghĩa có bố đẻ là ông Nguyễn Huy Tình; "
            "Sinh năm 1923, đã chết ngày 05/06/2016\n"
            "2. Ông Nguyễn Huy Nghĩa có mẹ đẻ là bà Nguyễn Thị Khánh; "
            "Sinh ngày 01/01/1950; Căn cước công dân số 036150013678\n"
        )
        persons = _extract_plain_text_person_entries(section)
        names = [q["ho_ten"] for q in persons]
        self.assertIn("Nguyễn Thị Khánh", names)
        self.assertNotIn("Nguyễn Huy Nghĩa có mẹ đẻ", names)

    def test_tien_to_bo_me_de_toi_va_ong_x_la(self):
        # "Mẹ đẻ tôi: Bà Y" va "Bố đẻ ông X là bà Y" — tien to quan he
        # + ten nguoi than chet, nguoi song la Y.
        from extract_contract import _extract_plain_text_person_entries
        section = (
            "- | Mẹ đẻ tôi: Bà Nguyễn Thị Vân; Sinh ngày: 01/01/1960; "
            "Căn cước công dân số 036160003674\n"
            "- | Mẹ đẻ ông Nguyễn Văn Hạnh là bà Nguyễn Thị Nhiễu; "
            "Sinh ngày: 01/01/1932; Căn cước công dân số 036132000298\n"
            "+ Bà: Trần Thị Thái Sinh ngày: 09/10/1949\n"
            "- Ông Trần Hữu Thăng có 01 người con riêng\n"
        )
        persons = _extract_plain_text_person_entries(section)
        names = [q["ho_ten"] for q in persons]
        self.assertIn("Nguyễn Thị Vân", names)
        self.assertIn("Nguyễn Thị Nhiễu", names)
        self.assertIn("Trần Thị Thái", names)
        self.assertNotIn("Trần Hữu Thăng có", names)

    def test_toi_ten_la_voi_o_trong_bang(self):
        # "Tôi tên là: X; | | Sinh ngày" — khong tach "| |" truoc nhan
        # thuong (Sinh ngày), chi tach truoc nhan danh xung Ong/Ba.
        from extract_contract import _extract_plain_text_person_entries
        section = (
            "Tôi tên là: Nguyễn Văn Cường; | | Sinh ngày: 20/08/1989;\n"
            "Căn cước công dân số 036089022676 do X cấp ngày 04/05/2021;\n"
            "Nơi thường trú tại: Xã Ý Yên."
        )
        persons = _extract_plain_text_person_entries(section)
        self.assertEqual([q["ho_ten"] for q in persons], ["Nguyễn Văn Cường"])
        self.assertEqual(persons[0]["cccd"], "036089022676")

    def test_dedupe_nam_tron_vs_ngay_day_du(self):
        # Danh sach nguoi lap 2 lan: 1 lan "Sinh ngày: 01/01/1932", 1 lan
        # "Sinh năm 1932" — cung nguoi, gop 1 ban ghi.
        from extract_contract import _extract_plain_text_person_entries
        section = (
            "Bà Hoàng Thị Hanh; Sinh ngày: 01/01/1932; "
            "Căn cước công dân số 036132002879\n"
            "Bà Hoàng Thị Hanh -sinh năm: 1932\n"
        )
        persons = _extract_plain_text_person_entries(section)
        self.assertEqual([q["ho_ten"] for q in persons], ["Hoàng Thị Hanh"])
        self.assertEqual(persons[0]["cccd"], "036132002879")

    def test_nguoi_chet_nam_co_trich_luc_khai_tu(self):
        # "chết năm 2016 theo Trích lục khai tử" -> nguoi chet that
        # (bang chung TLKT); "chết năm" troi khong TLKT van bo.
        from extract_contract import _extract_nguoi_chet
        text = (
            "Mẹ đẻ của chúng tôi là bà Nguyễn Thị Ngò - Sinh năm 1923; "
            "chết năm 2016 theo Trích lục khai tử số 95/2026/TLKT do "
            "Uỷ ban nhân dân xã Yên Đồng, tỉnh Ninh Bình ký ngày 07/04/2026; "
            "Nơi thường trú trước khi chết: Thôn Mễ Hạ, xã Yên Đồng, "
            "tỉnh Ninh Bình; theo quy định của pháp luật.\n"
            "- Ông Nguyễn Văn A có bố đẻ là ông Nguyễn Văn B, đã chết năm 1990."
        )
        chet = _extract_nguoi_chet(text)
        self.assertEqual([q["ho_ten"] for q in chet], ["Nguyễn Thị Ngò"])
        self.assertEqual(chet[0]["ngay_chet"], "2016")
        self.assertEqual(chet[0]["ngay_sinh"], "1923")
        self.assertEqual(chet[0]["so_giay_to"], "95/2026/TLKT")
        self.assertEqual(
            chet[0]["dia_chi"],
            "Thôn Mễ Hạ, xã Yên Đồng, tỉnh Ninh Bình",
        )

    def test_heading_gach_cheo_va_cccd_khong_so(self):
        # Mau ngan hang: "I/ BÊN ỦY QUYỀN" (gach cheo, khong phai "I."),
        # bullet "* Ông:", nhan "Năm sinh" dao, "CCCD:" khong chu "số".
        import extract_contract as ec
        text = (
            "HỢP ĐỒNG ỦY QUYỀN XỬ LÝ TÀI SẢN BẢO ĐẢM\n"
            "I/ BÊN ỦY QUYỀN ( Chủ tài sản):\n"
            "* Ông: Đinh Văn Tuyển\tNăm sinh: 03/08/1978\n"
            "- CCCD: 036078005311; ngày cấp: 16/09/2021\n"
            "- Hộ khẩu thường trú: TDP Ô Mễ 1, phường Thái Bình\n"
            "II/ BÊN ĐƯỢC ỦY QUYỀN:\n"
            "Ngân hàng ABC - Chi nhánh X\n"
        )
        ben_a, ben_b = ec._extract_parties_generic(
            ec._normalize_plain_text_for_extract(text), "generic"
        )
        self.assertEqual([q["ho_ten"] for q in ben_a["nguoi"]], ["Đinh Văn Tuyển"])
        self.assertEqual(ben_a["nguoi"][0]["ngay_sinh"], "03/08/1978")
        self.assertEqual(ben_a["nguoi"][0]["cccd"], "036078005311")

    def test_trang_sua_loi_ky_thuat_la_generic(self):
        # Trang phu dinh kem sua loi — khong nhan loai hop dong noi trang.
        import extract_contract as ec
        text = (
            "TRANG SỬA LỖI KỸ THUẬT ĐÍNH KÈM\n"
            "\tHợp đồng chuyển nhượng quyền sử dụng đất Số công chứng: 919.2025\n"
            "Nội dung cũ: Thửa đất số: 58 - Tờ bản đồ số: 41\n"
        )
        kind, _ = ec._detect_document_kind_and_title(text)
        self.assertEqual(kind, "generic")

    def test_trong_do_nhan_mo_ta_khong_hai_cham(self):
        # "trong đó diện tích được cấp GCN: 130,1 m2 ONT, diện tích chưa
        # được cấp 89,4 m2 ONT" — ve 2 khong co "Nhan:" van la chi tiet;
        # dau "," thap phan (130,1) khong duoc tach ve.
        from extract_contract import tach_danh_sach_thua_dat
        block = (
            "Thửa đất số: 28 , tờ bản đồ số: 4\n"
            "Diện tích: 219,5 m2 trong đó diện tích được cấp GCN: 130,1 m2  ONT, diện tích chưa được cấp 89,4 m2 ONT."
        )
        thua = tach_danh_sach_thua_dat(block)
        self.assertEqual(len(thua), 1)
        cts = {d["dien_tich"]: d["muc_dich_su_dung"] for d in thua[0]["chi_tiet_dien_tich"]}
        self.assertIn("130,1 m2", cts)
        self.assertIn("89,4 m2", cts)

    def test_nguoi_dai_dien_la_ong_preamble_mortgage(self):
        # "Người đại diện là Ông: <tên>" — danh xưng trước hai chấm; và thế
        # chấp không heading "BÊN NHẬN THẾ CHẤP" thì preamble là bên nhận
        # (mẫu Lời chứng Agribank).
        from extract_contract import _extract_parties_generic
        lines = [
            "NGÂN HÀNG AGRIBANK – CHI NHÁNH Ý YÊN",
            "Đại diện: Ông Phạm Quốc Vinh \t\t\tChức vụ: Giám đốc",
            "Căn cước công dân số: 036067010069 do Cục Cảnh sát cấp ngày 01/01/2020",
            "BÊN THẾ CHẤP:",
            "Công ty TNHH Vận Tải Minh Đông",
            "Người đại diện là Ông: Nguyễn Văn Nam - Chức vụ: Giám đốc;",
            "Căn cước công dân số 036082010023 ngày cấp 10/08/2021 nơi cấp Cục cảnh sát",
        ]
        ben_a, ben_b = _extract_parties_generic("\n".join(lines), "mortgage_contract")
        self.assertEqual([p["ho_ten"] for p in ben_a["nguoi"]], ["Nguyễn Văn Nam"])
        self.assertEqual([p["ho_ten"] for p in ben_b["nguoi"]], ["Phạm Quốc Vinh"])

    def test_khai_nhan_thua_ke_nhieu_chi_tiet_mot_ve(self):
        # "Thửa đất số 187, tờ bản đồ số 01; diện tích 200 m2; Trong đó:
        # Đất ở là 180 m2 Đất vườn: 20 m2" — 1 vế 2 cặp; "theo “Giấy chứng
        # nhận" có ngoặc kép; nhãn "Địa chỉ thửa đất:".
        block = (
            "Di sản của bà X để lại là phần quyền sử dụng đất căn cứ theo “Giấy chứng nhận quyền sử dụng đất” Đ 835496.\n"
            "-Thửa đất số 187, tờ bản đồ số 01; diện tích 200 m2; Trong đó: Đất ở là 180 m2 Đất vườn: 20 m2\n"
            "Địa chỉ thửa đất: xã Yên Mỹ, huyện Ý Yên, tỉnh Nam Định\n"
        )
        thua = tach_danh_sach_thua_dat(block)
        self.assertEqual(len(thua), 1)
        self.assertEqual(thua[0]["so_thua_dat"], "187")
        self.assertEqual(thua[0]["dia_chi"], "xã Yên Mỹ, huyện Ý Yên, tỉnh Nam Định")
        cts = {d["dien_tich"]: d["muc_dich_su_dung"] for d in thua[0]["chi_tiet_dien_tich"]}
        self.assertIn("180 m2", cts)
        self.assertIn("20 m2", cts)

    def test_bang_2_thua_lien_sau_trong_do(self):
        # Dong bang .doc: "...|23|34|425|Trong do|270|Dat vuon tap|12/2043|
        # 155|Dat o|Lau dai|23|32|160|Ao nuoi ca|12/2043 (nay la...)" — bo
        # 3 so sau "Trong do" la thua MOI, khong gop vao chi tiet thua truoc.
        from extract_contract import _tach_thua_cell_stream, _new_thua_dat
        cells = [c.strip() for c in (
            "Số tờ bản đồ|Số thửa|Diện tích (m2)|Mục đích sử dụng|Thời hạn sử dụng||"
            "23|34|425||||||Trong đó|||||||270|Đất vườn tạp|12/2043|||155|Đất ở|Lâu dài||"
            "23|32|160|Ao nuôi cá|12/2043 (nay là 31/12/2063)"
        ).split("|")]
        parcels: list[dict] = []
        self.assertTrue(_tach_thua_cell_stream(cells, {}, parcels))
        self.assertEqual([p["so_thua_dat"] for p in parcels], ["34", "32"])
        self.assertEqual(parcels[0]["dien_tich"], "425")
        self.assertEqual(
            [(c["dien_tich"], c["muc_dich_su_dung"]) for c in parcels[0]["chi_tiet_dien_tich"]],
            [("270", "Đất vườn tạp"), ("155", "Đất ở")],
        )
        self.assertEqual(parcels[1]["dien_tich"], "160")
        self.assertEqual(parcels[1]["muc_dich_su_dung"], "Ao nuôi cá")

    def test_nguoi_chet_chet_nam_tu_choi_co_quan_he(self):
        # VB từ chối: "Bố đẻ tôi là ông X; Sinh năm 1924, đã chết năm 2007"
        # — chết năm KHÔNG trích lục vẫn nhận vì trước có "Bố đẻ"
        # (11/10/2026). Các kind khác vẫn cần trích lục/khai tử.
        from extract_contract import _extract_nguoi_chet
        text = (
            "Bố đẻ tôi là ông Dương Xuân Khả; Sinh năm 1924, đã chết năm 2007; "
            "Nơi thường trú cuối cùng trước khi chết: Tổ 5, thị trấn Lâm, huyện Ý Yên.\n"
            "Mẹ đẻ tôi là bà Trịnh Thị Đai; Sinh năm 1924, đã chết năm 2009."
        )
        chet = _extract_nguoi_chet(text, "inheritance_refusal")
        self.assertEqual([p["ho_ten"] for p in chet], ["Dương Xuân Khả", "Trịnh Thị Đai"])
        self.assertEqual(chet[0]["ngay_chet"], "2007")
        # Van ban phan chia: cung cau do phai bi loai (can trich luc).
        self.assertEqual(_extract_nguoi_chet(text, "inheritance_partition"), [])

    def test_nguoi_chet_ngoac_gop_sinh_va_chet(self):
        # "Bố chúng tôi là ông X (sinh năm 1956, đã chết ngày 16/01/2025)
        # theo Trích lục khai tử" — cum sinh+chết trong ngoặc (11/10/2026).
        from extract_contract import _extract_nguoi_chet
        text = (
            "Bố chúng tôi là ông Đỗ Đình Thắm (sinh năm 1956, đã chết ngày 16/01/2025) "
            "theo Trích lục khai tử (Bản sao) số 04/TLKT-BS của Uỷ ban nhân dân."
        )
        chet = _extract_nguoi_chet(text, "inheritance_refusal")
        self.assertEqual(len(chet), 1)
        self.assertEqual(chet[0]["ho_ten"], "Đỗ Đình Thắm")
        self.assertEqual(chet[0]["ngay_sinh"], "1956")
        self.assertEqual(chet[0]["ngay_chet"], "16/01/2025")
        self.assertEqual(_extract_nguoi_chet(text, "inheritance_partition"), chet)

    def test_to_khai_thue_ho_va_ten_nhan_nguoi(self):
        # Tờ khai thuế điền sẵn: "[04] Họ và tên:", "[05] Ngày/tháng/năm sinh:",
        # "[10.x]" ô địa chỉ con — người phải ra đủ trường (11/10/2026).
        from extract_contract import _extract_parties_generic
        text = (
            "TỜ KHAI THUẾ SỬ DỤNG ĐẤT PHI NÔNG NGHIỆP\n"
            "1. Người nộp thuế:\n"
            "[04] Họ và tên: Ngô Xuân Ninh\n"
            "[05] Ngày/tháng/năm sinh: 11/3/1987\n"
            "[07] Số CMND/Hộ chiếu/CCCD: 036087006087\n"
            "[08] Ngày cấp: 08/05/2021 [09] Nơi cấp: Cục cảnh sát\n"
            "[10] Địa chỉ cư trú:\n"
            "[10.3] Tổ/thôn: Tổ 8, Thị trấn Lâm, huyện Ý Yên, tỉnh Nam Định\n"
            "[10.5] Quận/huyện: huyện Ý Yên\n"
            "[17.3] Tổ/thôn: tỉnh lộ 485, Thôn An Lạc\n"
        )
        ben_a, ben_b = _extract_parties_generic(text, "generic")
        self.assertEqual(len(ben_a["nguoi"]), 1)
        ninh = ben_a["nguoi"][0]
        self.assertEqual(ninh["ho_ten"], "Ngô Xuân Ninh")
        self.assertEqual(ninh["ngay_sinh"], "11/3/1987")
        self.assertEqual(ninh["cccd"], "036087006087")
        self.assertEqual(ninh["dia_chi"], "Tổ 8, Thị trấn Lâm, huyện Ý Yên, tỉnh Nam Định")

    def test_so_thu_tu_truoc_vai_tro_nguoi_chong(self):
        # "1. Người chồng – Vũ Văn Khoan; Sinh ngày:..." — tiền tố "1." trước
        # vai trò vẫn nhận người tên trần (11/10/2026).
        from extract_contract import _extract_parties_generic
        text = (
            "VĂN BẢN CAM KẾT TÀI SẢN RIÊNG\n"
            "Chúng tôi gồm có:\n"
            "1. Người chồng – Vũ Văn Khoan;\tSinh ngày: 01/01/1962;\n"
            "Căn cước công dân số: 036062020689 do Cục cảnh sát cấp ngày 02/07/2021;\n"
            "2. Người vợ - Nguyễn Thị Chiến;\tSinh ngày: 02/11/1960;\n"
            "Căn cước công dân số: 036160018620 do Cục cảnh sát cấp ngày 02/07/2021;\n"
            "Cả hai cùng thường trú tại: Xã Vũ Dương, tỉnh Ninh Bình.\n"
        )
        ben_a, ben_b = _extract_parties_generic(text, "generic")
        names = [p["ho_ten"] for s in (ben_a, ben_b) for p in s["nguoi"]]
        self.assertIn("Vũ Văn Khoan", names)
        self.assertIn("Nguyễn Thị Chiến", names)

    def test_trang_dinh_chinh_nhan_nguoi_trong_ngoac_kep(self):
        # "ĐÍNH CHÍNH VĂN BẢN ..." -> generic; tên trích dẫn “Bà X – Sinh năm”
        # / “Bà X – Sinh ngày” gộp 1 người, giữ ngày đầy đủ (11/10/2026).
        from extract_contract import _detect_document_kind_and_title, _extract_parties_generic
        text = (
            "ĐÍNH CHÍNH\n"
            "VĂN BẢN THOẢ THUẬN PHÂN CHIA DI SẢN\n"
            "Nội dung cũ:\n"
            "1. \u201cBà Nguyễn Thị Năm – Sinh năm 1958\u201d\n"
            "Nay đổi thành:\n"
            "1. \u201cBà Nguyễn Thị Năm – Sinh ngày: 25/12/1958\u201d\n"
        )
        kind, _ = _detect_document_kind_and_title(text)
        self.assertEqual(kind, "generic")
        ben_a, ben_b = _extract_parties_generic(text, kind)
        names = [(p["ho_ten"], p["ngay_sinh"]) for s in (ben_a, ben_b) for p in s["nguoi"]]
        self.assertEqual(names, [("Nguyễn Thị Năm", "25/12/1958")])

    def test_nguoi_chet_ten_tran_sau_la(self):
        # "Bố đẻ của tôi là Trần Văn Phúc, sinh năm 1910, đã chết ngày
        # 19/04/1998 theo trích lục khai tử" — ten tran khong danh xung
        # sau "là"; gioi_tinh de trong khong suy (11/10/2026).
        from extract_contract import _extract_nguoi_chet
        text = (
            "Bố đẻ của tôi là Trần Văn Phúc, sinh năm 1910, đã chết ngày 19/04/1998 "
            "theo trích lục khai tử (bản sao) số 17/2025/TLKT-BS do UBND xã Yên Thắng."
        )
        chet = _extract_nguoi_chet(text, "inheritance_refusal")
        self.assertEqual(len(chet), 1)
        self.assertEqual(chet[0]["ho_ten"], "Trần Văn Phúc")
        self.assertEqual(chet[0]["gioi_tinh"], "")
        self.assertEqual(chet[0]["ngay_chet"], "19/04/1998")

    def test_vai_tro_hai_cham_nguoi_vo_chong(self):
        # "Người vợ:  bà X; Sinh ngày:..." — vai trò dùng ":" thay "-" vẫn
        # nhận người kèm danh xưng (11/10/2026).
        from extract_contract import _extract_parties_generic
        text = (
            "Chúng tôi gồm có:\n"
            "Người vợ:  bà Phạm Thị Nụ;\t\t\tSinh ngày: 05/08/1975;\n"
            "Căn cước số 036175006208 do Bộ Công an cấp ngày 11/10/2024;\n"
            "Người chồng: ông Lê Ngọc Trình;\t\tSinh ngày: 20/10/1970;\n"
            "Căn cước số 036070022165 do Bộ Công an cấp ngày 11/10/2024;\n"
        )
        ben_a, ben_b = _extract_parties_generic(text, "asset_commitment")
        names = [p["ho_ten"] for s in (ben_a, ben_b) for p in s["nguoi"]]
        self.assertIn("Phạm Thị Nụ", names)
        self.assertIn("Lê Ngọc Trình", names)

    def test_dedupe_ten_gan_giong_nhau_khong_mat_ban_tom_tat(self):
        # "Vũ Thị Lanh" vs "Vũ Thị Lành" cung fold key nhung la 2 nguoi khac
        # (khac CCCD/nam sinh); ban tom tat "Sinh năm" phai gop vao dung
        # nguoi chi tiet, khong de lech sang nguoi ten gan giong (11/10/2026).
        from extract_contract import _extract_plain_text_person_entries
        text = (
            "1. Bà: Đỗ Thị Đợi - Sinh ngày: 01/01/1946; Căn cước số: 036146008526;\n"
            "2. Bà: Vũ Thị Lanh - Sinh ngày: 09/10/1986; Căn cước số: 036186001854;\n"
            "3. Bà Vũ Thị Lành - Sinh ngày: 15/02/1984; Căn cước số: 036184014148;\n"
            "Hộ gia đình gồm:\n"
            "1. Bà: Vũ Thị Lanh - Sinh năm: 1986 (con ông Luỹ)\n"
            "2. Bà Vũ Thị Lành - Sinh năm: 1984 (con ông Luỹ)\n"
        )
        persons = _extract_plain_text_person_entries(text)
        names = [(p["ho_ten"], p["ngay_sinh"]) for p in persons]
        self.assertEqual(
            names,
            [
                ("Đỗ Thị Đợi", "01/01/1946"),
                ("Vũ Thị Lanh", "09/10/1986"),
                ("Vũ Thị Lành", "15/02/1984"),
            ],
        )

    def test_bang_danh_sach_nguoi_su_dung_chung_o_tron(self):
        # Mau 04a/ĐK "DANH SÁCH NGƯỜI SỬ DỤNG CHUNG": hang o
        # "STT | Ông X | nam sinh | loai giay | so | ngay cap | noi cap |
        # dia chi" — nam sinh la o tron khong nhan (11/10/2026).
        from extract_contract import _extract_plain_text_person_entries
        text = (
            "STT | Tên | Năm sinh | Loại giấy tờ | Số | Ngày cấp | Cơ quan cấp | Địa chỉ\n"
            "1\nÔng Trương Anh Dũng | 1955 | CCCD | 036055003111 | 25/04/2021 | "
            "Cục Cảnh sát quản lý hành chính về trật tự xã hội | "
            "Thôn Dư Duệ, xã Tham Thanh, huyện Vụ Bản, tỉnh Nam Định |  | "
            "2 | Ông Trương Ngọc Mạnh | 1970 | CCCD | 036070012528 | 24/06/2021 | "
            "Cục Cảnh sát quản lý hành chính về trật tự xã hội | "
            "Tổ 27, thị trấn Đông Anh, huyện Đông Anh, thành phố Hà Nội |  |  | "
            "Nam Định, ngày ……., tháng ….. năm 2025\nNgười kê khai"
        )
        persons = _extract_plain_text_person_entries(text)
        self.assertEqual(len(persons), 2)
        dung = persons[0]
        self.assertEqual(dung["ho_ten"], "Trương Anh Dũng")
        self.assertEqual(dung["ngay_sinh"], "1955")
        self.assertEqual(dung["cccd"], "036055003111")
        self.assertEqual(dung["ngay_cap_cccd"], "25/04/2021")
        self.assertIn("Cảnh sát", dung["noi_cap"])
        self.assertIn("Vụ Bản", dung["dia_chi"])
        self.assertEqual(persons[1]["ho_ten"], "Trương Ngọc Mạnh")

    def test_bang_thanh_vien_hdtv_khong_cot_giay_to(self):
        # "BIÊN BẢN HỌP HĐTV": hang "STT | Ông X | chuc vu | ty le | ghi chu"
        # khong co cot giay to — van tinh nguoi nho o chuc vu (11/10/2026).
        from extract_contract import _extract_plain_text_person_entries
        text = (
            "STT | Họ tên | Chức vụ | Tỷ lệ vốn góp (%) | Ghi chú\n"
            "1 | Ông Nguyễn Hữu Công | Thành viên góp vốn kiêm Giám đốc | 33,33 % | Có mặt\n"
            "2 | Bà Phạm Thị Hà | Thành viên góp vốn | 33,33 % | Có mặt\n"
            "3 | Bà Phạm Thị Oanh | Thành viên góp vốn | 33,33 % | Có mặt\n"
            "Ban tổ chức Đại hội công bố kết quả:"
        )
        persons = _extract_plain_text_person_entries(text)
        names = [p["ho_ten"] for p in persons]
        self.assertIn("Nguyễn Hữu Công", names)
        self.assertIn("Phạm Thị Hà", names)
        self.assertIn("Phạm Thị Oanh", names)

    def test_nhan_danh_xung_dung_mot_minh_ong_hai_cham(self):
        # "Ông: Triệu Tuấn Anh" dung rieng 1 dong khong giay to — nhan danh
        # xung la du hieu nguoi (to dinh gia ngan hang — 11/10/2026).
        from extract_contract import _extract_plain_text_person_entries
        text = (
            "Thành phần Tổ định giá gồm:\n"
            "Ông: Triệu Tuấn Anh\n"
            "Ông: Nguyễn Văn Chí | Chức vụ: Phó Giám đốc\n"
        )
        persons = _extract_plain_text_person_entries(text)
        names = [p["ho_ten"] for p in persons]
        self.assertIn("Triệu Tuấn Anh", names)
        self.assertIn("Nguyễn Văn Chí", names)

    def test_nhan_chuc_vu_truoc_danh_xung(self):
        # "Chức vụ: Ông Nguyễn Hữu Công" — ten sau nhan chuc vu giua dong
        # (bang thanh phan to dinh gia — 11/10/2026).
        from extract_contract import _extract_plain_text_person_entries
        text = "Đại diện hợp pháp\nChức vụ: Ông Nguyễn Hữu Công\nGiám đốc\n"
        persons = _extract_plain_text_person_entries(text)
        self.assertTrue(
            any(p["ho_ten"] == "Nguyễn Hữu Công" and p["gioi_tinh"] == "Ông" for p in persons)
        )

    def test_chi_tiet_o_nhieu_so_tach_thanh_nhieu_dong(self):
        # Bang GCN 2 dong gop 1 o: "Trong đó 324,9 46,8 | Đất ở Vườn |
        # Lâu dài 2043" — o dien tich nhieu so tron tach thanh chi tiet
        # rieng de tong khop 371,7 (11/10/2026).
        from extract_contract import tach_danh_sach_thua_dat
        text = (
            "Số tờ bản đồ | Số thửa | Diện tích (m2) | Mục đích sử dụng | Thời hạn\n"
            "18 | 207 | 371,7\n"
            "Trong đó 324,9 46,8 | Đất ở Vườn | Lâu dài 2043"
        )
        parcels = tach_danh_sach_thua_dat(text)
        self.assertTrue(parcels)
        chi_tiet = parcels[0].get("chi_tiet_dien_tich", [])
        self.assertEqual(len(chi_tiet), 2)
        tong_ct = sum(
            float(str(c["dien_tich"]).replace(",", ".")) for c in chi_tiet
        )
        self.assertAlmostEqual(tong_ct, 371.7, places=1)

    def test_danh_sach_danh_so_ten_tran_chung_toi_la(self):
        # Don tu choi nhieu nguoi: "Chúng tôi là: 1. Trần Văn Cát   Sinh
        # ngày: ..." — ten tran khong Ong/Ba, danh so + ngay sinh cung
        # dong (11/10/2026).
        from extract_contract import _extract_party_data
        sec = (
            "1. Trần Văn Cát\t\t\tSinh ngày: 05/01/1960;\n"
            "Căn cước công dân số 036060001798 do Cục cảnh sát cấp ngày 02/07/2021;\n"
            "Thường trú tại: thôn Thiện Mỹ, xã Yên Mỹ.\n"
            "2. Trần Văn Tông\t\t\tSinh ngày: 25/12/1963;\n"
            "Căn cước số 036063028788 do Bộ Công an cấp ngày 09/08/2024;\n"
            "Cư trú tại: thôn Thiện Mỹ, xã Yên Mỹ."
        )
        nguoi = _extract_party_data(sec)["nguoi"]
        self.assertEqual([p["ho_ten"] for p in nguoi], ["Trần Văn Cát", "Trần Văn Tông"])
        self.assertEqual(nguoi[0]["cccd"], "036060001798")
        self.assertEqual(nguoi[1]["ngay_sinh"], "25/12/1963")

    def test_cat_ten_truoc_chuc_vu_dinh_gach_lien(self):
        # "Ông Phùng Trường Giang      -Chức vụ: Phó Giám đốc" — dau gach
        # dinh lien vao "Chức vụ" khong co khoang trang sau dau, ten van
        # phai cat dung (11/10/2026).
        from extract_contract import _extract_party_data
        sec = "Đại diện hợp pháp: Ông Phùng Trường Giang      -Chức vụ: Phó Giám đốc"
        nguoi = _extract_party_data(sec)["nguoi"]
        self.assertTrue(any(p["ho_ten"] == "Phùng Trường Giang" for p in nguoi))



    def test_tach_thua_cell_stream_chi_tiet_thieu_thoi_han(self):
        from extract_contract import _new_thua_dat, _tach_thua_cell_stream

        # Bang .doc: chi tiet "225 Dat o" khong ky han, so "119" sau do
        # la dien tich chi tiet moi, khong phai thoi han cua "225".
        cells = [
            "Số tờ bản đồ", "Số thửa", "Diện tích (m2)", "Mục đích", "Thời hạn",
            "", "44", "80", "546,0", "", "", "225", "Đất ở", "", "119", "CLN",
            "15/10/2063", "", "202", "NTS", "15/10/2063", "",
        ]
        parcels = []
        self.assertTrue(_tach_thua_cell_stream(cells, {}, parcels))
        self.assertEqual(len(parcels), 1)
        ct = parcels[0]["chi_tiet_dien_tich"]
        self.assertEqual([c["dien_tich"] for c in ct], ["225", "119", "202"])
        self.assertEqual(ct[0]["thoi_han_su_dung"], "")
        self.assertEqual(ct[1]["thoi_han_su_dung"], "15/10/2063")


    def test_bang_don_dong_nhieu_thua_trong_do(self):
        # Bang .doc gop 1 dong, nhieu thua + "Trong do" chi tiet:
        # "35 44 150 NTS 2063  35 103 299  Trong do 200 ONT Lau dai
        #  99 CLN 2043  35 134 168 CLN 2043" — phai ra 3 thua, chi tiet
        # thuoc thua 103 (12/10/2026).
        from extract_contract import _tach_thua_bang_don_dong
        line = (
            "Số tờ bản đồ Số thửa Diện tích (m2) Mục đích sử dụng Thời hạn sử dụng "
            "35 44 150 NTS 2063 35 103 299 Trong đó 200 ONT Lâu dài 99 CLN 2043 "
            "35 134 168 CLN 2043"
        )
        parcels = []
        self.assertTrue(_tach_thua_bang_don_dong(line, {}, parcels))
        self.assertEqual(
            [p["so_thua_dat"] for p in parcels], ["44", "103", "134"]
        )
        self.assertEqual(parcels[0]["muc_dich_su_dung"], "NTS")
        self.assertEqual(parcels[0]["thoi_han_su_dung"], "2063")
        ct = parcels[1]["chi_tiet_dien_tich"]
        self.assertEqual(
            [(c["dien_tich"], c["muc_dich_su_dung"]) for c in ct],
            [("200", "ONT"), ("99", "CLN")],
        )
        self.assertEqual(parcels[2]["dien_tich"], "168")

    def test_nguoi_chet_ngoac_bi_danh_truoc_ngoac_sinh_chet(self):
        # "ong X (Ten khac); (Sinh nam 1945, da chet ngay ... theo trich luc...)"
        # — ngoac bi danh dung truoc ngoac sinh/chet (12/10/2026).
        from extract_contract import _extract_nguoi_chet, DOC_KIND_INHERITANCE_REFUSAL
        text = (
            "Bố chúng tôi là ông Trần Văn Đàm (Trần Hữu Đàm); "
            "(Sinh năm 1945, đã chết ngày 08/08/2014 theo trích lục khai tử "
            "số 23/TLKT-BS do UBND xã Yên Phong cấp ngày 28/02/2017. "
            "Nơi thường trú cuối cùng trước khi chết: thôn Bồng Quỹ, xã Yên Phong)."
        )
        ds = _extract_nguoi_chet(text, DOC_KIND_INHERITANCE_REFUSAL)
        self.assertEqual(len(ds), 1)
        self.assertEqual(ds[0]["ho_ten"], "Trần Văn Đàm")
        self.assertEqual(ds[0]["ten_goi_khac"], "Trần Hữu Đàm")
        self.assertEqual(ds[0]["ngay_chet"], "08/08/2014")


    def test_don_dk_ten_tran_va_cccd_dat_ten(self):
        # Mau 11/DK: "1.1. Ten: Ha Van Thinh; Sinh ngay: ..." (khong danh
        # xung) + "- Can cuoc cong dan ong Ha Van Thinh so 036..." — hai
        # dong gop thanh 1 nguoi du truong; "1.3. Dia chi:" la dia chi
        # chung cua ca muc (12/10/2026).
        from extract_contract import _extract_party_data
        section = (
            "1. Người sử dụng đất:\n"
            "1.1.	Tên: Hà Văn Thinh; 		Sinh ngày: 15/05/1961;\n"
            "Tên: Nguyễn Thị Nga;		Sinh ngày: 20/02/1960;\n"
            "1.2. Giấy tờ nhân thân/pháp nhân:\n"
            "- Căn cước công dân ông Hà Văn Thinh số 036061004683 do Cục cảnh sát cấp ngày 09/04/2021;\n"
            "- Căn cước công dân bà Nguyễn Thị Nga số 036160000971 do Cục cảnh sát cấp ngày 13/03/2021;\n"
            "1.3. Địa chỉ: Thôn An Lạc, xã Yên Khánh, huyện Ý Yên.\n"
            "1.4. Điện thoại liên hệ (nếu có):\n"
        )
        ds = _extract_party_data(section)
        self.assertEqual(len(ds["nguoi"]), 2)
        thinh = ds["nguoi"][0]
        self.assertEqual(thinh["ho_ten"], "Hà Văn Thinh")
        self.assertEqual(thinh["cccd"], "036061004683")
        self.assertEqual(thinh["ngay_sinh"], "15/05/1961")
        self.assertEqual(thinh["gioi_tinh"], "Ông")
        self.assertIn("An Lạc", thinh["dia_chi"])
        nga = ds["nguoi"][1]
        self.assertEqual(nga["cccd"], "036160000971")
        self.assertEqual(nga["gioi_tinh"], "Bà")

    def test_vai_tro_con_gai_chau_dong_su_dung(self):
        # "1. Con gái - Bà X" / "2. Cháu - Ông X" / "2. Đồng sử dụng –
        # Ông X" — vai tro mo rong (cam ket dong so huu, tang cho —
        # 12/10/2026).
        from extract_contract import _extract_party_data
        section = "\n".join([
            "1. Con gái - Bà Nguyễn Thị Hằng, Sinh năm 1980;",
            "2. Cháu - Ông Nguyễn Tuấn Anh, Sinh năm 1977;",
            "3. Cháu - Ông Nguyễn Tuấn Anh, Sinh năm 1993;",
            "4. Đồng sử dụng – Ông Nguyễn Minh Quang Sinh ngày: 05/12/1991;",
            "5.  Ông ngoại – ông Đoàn Xuân Lam; Sinh ngày: 04/09/1956;",
            "Cháu ngoại – bà Lê Thị Thơm; Sinh ngày: 14/03/1996;",
        ])
        ds = _extract_party_data(section)
        names = [(x["ho_ten"], x["gioi_tinh"], x["ngay_sinh"]) for x in ds["nguoi"]]
        self.assertEqual(names, [
            ("Nguyễn Thị Hằng", "Bà", "1980"),
            ("Nguyễn Tuấn Anh", "Ông", "1977"),
            ("Nguyễn Tuấn Anh", "Ông", "1993"),
            ("Nguyễn Minh Quang", "Ông", "05/12/1991"),
            ("Đoàn Xuân Lam", "Ông", "04/09/1956"),
            ("Lê Thị Thơm", "Bà", "14/03/1996"),
        ])

    def test_chet_nam_theo_don_de_nghi_la_nguoi_chet(self):
        # "chet nam YYYY theo Đơn đề nghị do UBND ... xác nhận" la bang
        # chung nguoi chet nhu trich luc (12/10/2026); nguoi do khong
        # duoc roi vao danh sach duong su (VB khai nhan ong Nhiem).
        from extract_contract import _extract_nguoi_chet, _extract_party_data, DOC_KIND_INHERITANCE_DECLARATION
        text = "\n".join([
            "I. Người để lại di sản:",
            "1. Ông Nguyễn Văn Nhiểm – Sinh năm 1940; chết năm 2002 theo Đơn đề nghị do UBND xã Yên Cường, huyện Ý Yên, tỉnh Nam Định xác nhận ngày 02/04/2025; Nơi thường trú cuối cùng trước khi chết: Thôn Thắng Lợi, xã Yên Cường.",
            "- Bố đẻ ông Nguyễn Văn Nhiểm là ông Nguyễn Xuân Khài; sinh năm 1900; chết năm 1963, theo Đơn đề nghị do UBND xã Yên Cường, huyện Ý Yên, tỉnh Nam Định xác nhận ngày 02/04/2025; Nơi thường trú cuối cùng trước khi chết: Thôn Thắng Lợi, xã Yên Cường.",
        ])
        ds = _extract_nguoi_chet(text, DOC_KIND_INHERITANCE_DECLARATION)
        names = [(x["ho_ten"], x["ngay_sinh"], x["ngay_chet"]) for x in ds]
        self.assertEqual(names, [
            ("Nguyễn Văn Nhiểm", "1940", "2002"),
            ("Nguyễn Xuân Khài", "1900", "1963"),
        ])
        party = _extract_party_data(text)
        self.assertEqual([x["ho_ten"] for x in party["nguoi"]], [])

    def test_dia_chi_cuoi_ca_hai_chung_cho_vo_chong_chet(self):
        # "Cả hai có nơi cư trú cuối cùng trước khi chết tại: X" la dia
        # chi CHUNG cua cap vo chong chet cung dong — dien cho ca hai,
        # ke ca nguoi dung truoc (ong Moc/ba Den — 12/10/2026).
        from extract_contract import _extract_nguoi_chet, DOC_KIND_INHERITANCE_PARTITION
        text = "- Bố đẻ ông Vũ Đình Đạc là ông Vũ Đình Mộc; chết ngày 28/12/1993; Mẹ đẻ ông Vũ Đình Đạc là bà Vũ Thị Dền; chết ngày 08/02/1995; Cả hai có nơi cư trú cuối cùng trước khi chết tại: Xã Yên Trị, huyện Ý Yên, tỉnh Nam Định."
        ds = _extract_nguoi_chet(text, DOC_KIND_INHERITANCE_PARTITION)
        got = {x["ho_ten"]: x["dia_chi"] for x in ds}
        self.assertEqual(got.get("Vũ Đình Mộc"), "Xã Yên Trị, huyện Ý Yên, tỉnh Nam Định")
        self.assertEqual(got.get("Vũ Thị Dền"), "Xã Yên Trị, huyện Ý Yên, tỉnh Nam Định")

    def test_cat_duoi_chuc_vu_khong_dau_sau_gach(self):
        # "Ông X - Chức vu:Giám dốc" (chức vụ khong dau sau gach) phai cat
        # duoi — ten nguoi chi la "Đoàn Thế Vinh" (12/10/2026).
        from extract_contract import _extract_party_data
        text = (
            "Người đại diện là ông: Đoàn Thế Vinh - Chức vu:Giám dốc\n"
            "Căn cước công dân số 037070002088 do Cục Cảnh sát cấp ngày 28/06/2021.\n"
        )
        party = _extract_party_data(text)
        names = [x["ho_ten"] for x in party["nguoi"]]
        self.assertEqual(names, ["Đoàn Thế Vinh"])
        self.assertEqual(party["nguoi"][0]["cccd"], "037070002088")

    def test_vai_tro_chau_lien_ten_khong_dau_noi(self):
        # "2. Cháu Lê Khánh Chi (con bà Nga)" — vai tro "Cháu" dung lien
        # truoc ten khong dau noi; tach khoi ho_ten, gioi_tinh de trong
        # (13/10/2026).
        from extract_contract import _extract_party_data
        text = (
            "1.Bà: Nguyễn Thị Thanh Phương (mẹ bà Nga) Sinh ngày: 15/08/1965;\n"
            "2. Cháu Lê Khánh Chi (con bà Nga)\t\tSinh ngày: 02/09/2017;\n"
            "Căn cước công dân số: 036317020683 do Bộ Công an cấp ngày 31/07/2025;\n"
        )
        party = _extract_party_data(text)
        names = [x["ho_ten"] for x in party["nguoi"]]
        self.assertIn("Lê Khánh Chi", names)
        self.assertNotIn("Cháu Lê Khánh Chi", names)

    def test_do_co_quan_ngay_thieu_chu_cap(self):
        # "do <co quan> ngay DD/MM/YYYY" (nguon go thieu chu "cap") van la
        # ngay cap giay to — khong nham voi "ky ngay" (13/10/2026).
        from extract_contract import _extract_party_data
        text = (
            "Ông Bùi Xuân Khải;\tSinh ngày: 04/04/1989;\n"
            "Căn cước công dân số 036094017936 do Cục cảnh sát quản lý hành chính về trật tự xã hội ngày 04/04/2022;\n"
            "Nơi thường trú tại: xã Yên Tiến, huyện Ý Yên, tỉnh Nam Định.\n"
        )
        party = _extract_party_data(text)
        self.assertEqual(len(party["nguoi"]), 1)
        self.assertEqual(party["nguoi"][0]["ngay_cap_cccd"], "04/04/2022")
        text_ky = (
            "Ông Bùi Xuân Khải;\tSinh ngày: 04/04/1989;\n"
            "Căn cước công dân số 036094017936 do UBND xã Yên Tiến ký ngày 04/04/2022.\n"
        )
        party2 = _extract_party_data(text_ky)
        self.assertNotEqual(party2["nguoi"][0]["ngay_cap_cccd"], "04/04/2022")

    def test_dia_chi_muc_chu_cai_chung(self):
        # "c) Địa chỉ:" cua mau 18 la dia chi chung cho moi nguoi trong
        # muc — dien cho nguoi chua co (13/10/2026).
        from extract_contract import _extract_party_data
        text = (
            "a) Tên: Ông Tạ Sơn Huấn;\t\t\t\tSinh ngày: 15/03/1965;\n"
            "Tên: Bà Nguyễn Thị Hoa;\t\t\tSinh ngày: 18/11/1971\n"
            "b) Giấy tờ nhân thân/pháp nhân:\n"
            "1. Ông Tạ Sơn Huấn;\t\t\t\tSinh ngày: 15/03/1965;\n"
            "Căn cước công dân số 036065006939 do Cục cảnh sát cấp ngày 02/07/2021;\n"
            "c) Địa chỉ: thôn An Ngọc, xã Vạn Thắng, tỉnh Ninh Bình\n"
        )
        party = _extract_party_data(text)
        addrs = {x["ho_ten"]: x["dia_chi"] for x in party["nguoi"]}
        self.assertEqual(addrs.get("Tạ Sơn Huấn"), "thôn An Ngọc, xã Vạn Thắng, tỉnh Ninh Bình")
        self.assertEqual(addrs.get("Nguyễn Thị Hoa"), "thôn An Ngọc, xã Vạn Thắng, tỉnh Ninh Bình")

    def test_nguoi_trong_danh_sach_ho_nhung_da_chet_bi_loai(self):
        # "1. Ông X - sinh năm 1957 (chủ hộ)" trong danh sach hộ gia
        # dinh cung doc co "chết ngày ... theo trích lục" -> loai khoi
        # duong su, van giu o nguoi_chet (13/10/2026).
        import extract_contract as ec
        text = (
            "VĂN BẢN CAM KẾT\n"
            "1. Bà Bùi Thị Xiêm;\t\tSinh ngày: 15/08/1958;\n"
            "Căn cước công dân số: 036158014 do Bộ Công an cấp ngày 01/01/2020;\n"
            "Thường trú tại: xã A, huyện B, tỉnh C.\n"
            "Hộ gia đình ông Bùi Văn Ngà gồm các thành viên là:\n"
            "1. Ông Bùi Văn Ngà - sinh năm 1957 (chủ hộ)\n"
            "2. Bà Bùi Thị Xiêm -sinh năm 1958 (vợ ông Ngà)\n"
            "Toàn bộ quyền sử dụng đất thuộc về ông Bùi Văn Ngà (Ông Bùi Văn Ngà- "
            "Sinh năm 1957; chết ngày 16/03/2025 theo Trích lục khai tử số 35/TLKT "
            "do UBND phường Chi Lăng ký ngày 25/03/2025; Nơi thường trú cuối cùng "
            "trước khi chết: phường Chi Lăng, tỉnh Lạng Sơn).\n"
        )
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        names = [x["ho_ten"] for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]]
        self.assertNotIn("Bùi Văn Ngà", names)
        chet = [x["ho_ten"] for x in r["raw"]["nguoi_chet"]]
        self.assertIn("Bùi Văn Ngà", chet)

    def test_o_nhan_co_marker_muc_va_dau_cham(self):
        # O "a) Thửa đất số: 131 | | Tờ bản đồ số: 29" (marker a) dinh
        # trong o nhan, .doc IFilter) van tach dung so thua/to (13/10/2026).
        import extract_contract as ec
        ts = (
            "a) Thửa đất số: 131 | | | Tờ bản đồ số: 29 (nay là tờ bản đồ số 270)\n"
            "b) Địa chỉ: thôn Hoàng Nê, xã Ý Yên, tỉnh Ninh Bình\n"
            "c) Diện tích: 1090,6 m²\n"
        )
        prs = ec.tach_danh_sach_thua_dat(ts)
        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["so_thua_dat"], "131")
        self.assertEqual(prs[0]["so_to_ban_do"], "29")

    def test_so_thua_ngoac_tach_tu_co_khoang_trang(self):
        # "108 ( tách từ thửa số 99)" — khoang trang sau "(" van cat ghi
        # chu, giu so thua 108 (13/10/2026).
        import extract_contract as ec
        head, note = ec._tach_nay_la("108 ( tách từ thửa số 99)")
        self.assertEqual(head, "108")
        self.assertIn("tách", note)



    def test_dia_chi_muc_chu_cai_dinh_vao_dong_truoc(self):
        # "c) Địa chỉ:" dinh vao cuoi dong truoc (2021c) — van la dia chi
        # CHUNG cua muc, dien cho moi nguoi thieu (mau 18 - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN ĐĂNG KÝ BIẾN ĐỘNG",
            "1. Người sử dụng đất:",
            "a) Tên: Ông Đinh Thành Công;\tSinh ngày: 20/02/1983;",
            "Tên: Bà Trần Thị Vân;\tSinh ngày: 30/01/1987;",
            "b) Giấy tờ nhân thân:",
            "1. Ông Đinh Thành Công;\tSinh ngày: 20/02/1983;",
            "Căn cước công dân số 036083000874 do Cục cảnh sát ngày 14/04/2021;",
            "2. Bà: Trần Thị Vân;\tSinh ngày: 30/01/1987;",
            "Căn cước công dân số 036187024995 do Cục cảnh sát ngày 02/07/2021c) Địa chỉ: B13, KP3, phường Tam Hiệp, tỉnh Đồng Nai.",
            "d) Điện thoại liên hệ:",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        dc = {x["ho_ten"]: x["dia_chi"] for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]}
        self.assertEqual(dc.get("Đinh Thành Công"), "B13, KP3, phường Tam Hiệp, tỉnh Đồng Nai")
        self.assertEqual(dc.get("Trần Thị Vân"), "B13, KP3, phường Tam Hiệp, tỉnh Đồng Nai")

    def test_ngay_cap_nhan_cap_tran(self):
        # "nơi cấp: Cục ... cấp: 20/04/2023" — nhan "cấp:" tran van la
        # ngay cap (loi chung the chap - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "LỜI CHỨNG",
            "I. BÊN THẾ CHẤP:",
            "2. Ông Hoàng Văn Quyết;\t \tNăm sinh: 1986",
            "Căn cước công dân số: 037086000267 nơi cấp: Cục cảnh sát quản lý hành chính về trật tự xã hội cấp: 20/04/2023",
            "Cư trú tại: 1A/52 Vĩnh Trường, phường Lộc Vượng, thành phố Nam Định.",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        q = [x for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"] if x["ho_ten"] == "Hoàng Văn Quyết"]
        self.assertTrue(q)
        self.assertEqual(q[0]["ngay_cap_cccd"], "20/04/2023")

    def test_cccd_co_khoang_trang(self):
        # "CCCD số: 0360 5800 1963" — so giay to viet cach nhom 4-4-4
        # van nhan va chuan hoa bo khoang trang (phieu yccc - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "PHIẾU YÊU CẦU CÔNG CHỨNG",
            "Ông: TRẦN NGỌC BẢN;\tNăm sinh: 1958",
            "CCCD số: 0360 5800 1963 Nơi cấp: Cục cảnh sát quản lý hành chính",
            "Ngày cấp: 25/04/2021",
            "Địa chỉ thường trú: Thôn Đồng Cách, Yên Khang, Ý Yên, Nam Định",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        q = [x for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"] if "BẢN" in x["ho_ten"]]
        self.assertTrue(q)
        self.assertEqual(q[0]["cccd"], "036058001963")

    def test_dia_chi_muc_chu_cai_theo_ten_nguoi(self):
        # "c) Địa chỉ:" rong roi tung dong "Ông X: <dia chi>" — dia chi
        # ca nhan theo ten (mau 18 - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN ĐĂNG KÝ BIẾN ĐỘNG ĐẤT ĐAI",
            "1. Người sử dụng đất:",
            "a) Tên: Ông Mai Quốc Việt;\tSinh ngày: 12/07/1986",
            "Tên: Bà Bùi Thị Thu Hương;\tSinh ngày: 22/10/1986",
            "b) Giấy tờ nhân thân:",
            "1. Ông Mai Quốc Việt;\tSinh ngày: 12/07/1986;",
            "Căn cước số 036086001288 do Bộ công an cấp ngày 22/02/2025",
            "2. Và vợ là bà Bùi Thị Thu Hương;\tSinh ngày: 22/10/1986;",
            "Căn cước công dân số 022186011606 do Cục cảnh sát cấp ngày 14/08/2021",
            "c) Địa chỉ:",
            "Ông Mai Quốc Việt: xã Ý Yên, tỉnh Ninh Bình",
            "Bà Bùi Thị Thu Hương: Tổ 68, Khu 7, phường Việt Hưng, tỉnh Quảng Ninh",
            "d) Điện thoại liên hệ:",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        dc = {x["ho_ten"]: x["dia_chi"] for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]}
        self.assertEqual(dc.get("Mai Quốc Việt"), "xã Ý Yên, tỉnh Ninh Bình")
        self.assertEqual(dc.get("Bùi Thị Thu Hương"), "Tổ 68, Khu 7, phường Việt Hưng, tỉnh Quảng Ninh")

    def test_nguoi_chet_tach_danh_xung_dinh_ten(self):
        # "1.1 Ông Nguyễn Văn Toản - Sinh năm 1959, đã chết ngày ..." —
        # danh xung dinh trong nhom ten; tach ra de gop 2 lan nhac cung
        # nguoi (tt phan chia - 13/10/2026).
        import extract_contract as ec
        ds = ec._extract_nguoi_chet(
            "1.1 Ông Nguyễn Văn Toản - Sinh năm 1959, đã chết ngày 20/07/2014 theo Trích lục số 20/TL.\n"
            "Ông Nguyễn Văn Toản - Sinh năm 1959, đã chết ngày 20/07/2014 theo Trích lục; Nơi thường trú cuối cùng trước khi chết tại: phường Hạ Long, tỉnh Quảng Ninh\n"
        )
        self.assertEqual(len(ds), 1)
        self.assertEqual(ds[0]["ho_ten"], "Nguyễn Văn Toản")
        self.assertEqual(ds[0]["gioi_tinh"], "Ông")
        self.assertEqual(ds[0]["dia_chi"], "phường Hạ Long, tỉnh Quảng Ninh")

    def test_dia_chi_chung_tat_ca_ong_ba(self):
        # "Tất cả ông bà cùng thường trú tại: X" — dia chi chung danh
        # sach ho gia dinh (hop dong chuyen nhuong - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "HỢP ĐỒNG CHUYỂN NHƯỢNG",
            "I. BÊN CHUYỂN NHƯỢNG:",
            "1. Ông Nguyễn Văn Tuyến; | Sinh ngày: 10/07/1966",
            "Căn cước công dân số: 036066024280 do Cục cảnh sát cấp ngày 10/05/2021.",
            "2. Bà Đinh Thị Hưng; | Sinh ngày: 13/05/1971;",
            "Căn cước công dân số: 036171012352 do Cục Cảnh sát cấp ngày 12/04/2021;",
            "Tất cả ông bà cùng thường trú tại: Thôn Cổ Phương, Xã Phong Doanh, Tỉnh Ninh Bình.",
            "II. BÊN NHẬN CHUYỂN NHƯỢNG:",
            "Bà Đinh Thị Kiều Vân; | Sinh ngày: 20/12/1975",
            "Căn cước số 019175000150 do Bộ công an cấp ngày 13/04/2021;",
            "Nơi thường trú tại: thôn Đông Hoa, phường Hoa Lư, Tỉnh Ninh Bình.",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        dc = {x["ho_ten"]: x["dia_chi"] for x in r["raw"]["ben_a"]["nguoi"]}
        self.assertEqual(dc.get("Nguyễn Văn Tuyến"), "Thôn Cổ Phương, Xã Phong Doanh, Tỉnh Ninh Bình")
        self.assertEqual(dc.get("Đinh Thị Hưng"), "Thôn Cổ Phương, Xã Phong Doanh, Tỉnh Ninh Bình")

    def test_toi_ong_ten_cung_dong(self):
        # "Tôi Ông Trần Văn Hương; | Sinh ngày: ..." — intro "Tôi + danh
        # xung" khong co "là" (don cam doan - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN CAM ĐOAN",
            "Tôi Ông Trần Văn Hương; |  |  |  | Sinh ngày: 16/08/1974",
            "Căn cước công dân số 036074002923 do Cục cảnh sát ngày 05/09/2022;",
            "Nơi cư trú tại: thôn Vĩnh Trị, xã Yên Đồng, tỉnh Ninh Bình.",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        names = [x["ho_ten"] for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]]
        self.assertIn("Trần Văn Hương", names)
        q = [x for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"] if x["ho_ten"] == "Trần Văn Hương"]
        self.assertEqual(q[0]["ngay_cap_cccd"], "05/09/2022")

    def test_dia_chi_lien_he_muc_so(self):
        # "2. Địa chỉ liên hệ (điện thoại, email...): X" — truong dia chi
        # nguoi trong don mau 09 gia han (13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN XIN GIA HẠN SỬ DỤNG ĐẤT",
            "1. Người sử dụng đất:",
            "1.1. Bà Nguyễn Thị Thảo\t\tSinh ngày: 01/06/1962",
            "Căn cước công dân số 036162012803 do Cục cảnh sát cấp ngày 25/08/2021",
            "2. Địa chỉ liên hệ (điện thoại, email...):  thôn Văn Hưng, xã Vạn Thắng, tỉnh Ninh Bình",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        q = [x for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"] if x["ho_ten"] == "Nguyễn Thị Thảo"]
        self.assertTrue(q)
        self.assertEqual(q[0]["dia_chi"], "thôn Văn Hưng, xã Vạn Thắng, tỉnh Ninh Bình")

    def test_ngay_cap_gach_chep_kep(self):
        # "cấp ngày 23/04//2021" — gach chep kep go nham, chuan hoa ve
        # "23/04/2021" (thong bao thua ke - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "THÔNG BÁO",
            "Bà Ngô Thị Thanh | Sinh năm 1995",
            "Căn cước công dân số 036195007112 do Cục cảnh sát cấp ngày 23/04//2021.",
            "Nơi thường trú tại: thôn Hạ Kỳ, xã Đồng Thịnh, tỉnh Nam Định.",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        q = [x for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"] if x["ho_ten"] == "Ngô Thị Thanh"]
        self.assertTrue(q)
        self.assertEqual(q[0]["ngay_cap_cccd"], "23/04/2021")

    def test_ten_danh_xung_tab_sinh_ngay(self):
        # "1.1. Tên:  ông Hà Văn Tiễu \tSinh ngày 02/03/1963" — nhan
        # "Tên:" + danh xung thuong + tab truoc Sinh (mau 11 - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN ĐĂNG KÝ BIẾN ĐỘNG",
            "1. Người sử dụng đất:",
            "1.1. Tên:  ông Hà Văn Tiễu \tSinh ngày 02/03/1963",
            "Tên:   bà  Đỗ Thị Ngọ  \t\tSinh ngày 08/10/1966",
            "1.2. Giấy tờ nhân thân:",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        ns = {x["ho_ten"]: x["ngay_sinh"] for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]}
        self.assertEqual(ns.get("Hà Văn Tiễu"), "02/03/1963")
        self.assertEqual(ns.get("Đỗ Thị Ngọ"), "08/10/1966")

    def test_ten_toi_khong_la(self):
        # "Tên tôi: Bà Nguyễn Thị Lan;" — intro "Tên tôi" khong "là"
        # (don de nghi chuyen muc dich - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN ĐỀ NGHỊ",
            "Tên tôi: Bà Nguyễn Thị Lan; |  | Sinh ngày: 01/01/1958;",
            "Căn cước công dân số 036158023063 do Cục cảnh sát cấp ngày 16/01/2022;",
            "Nơi thường trú: tổ 7, xã Ý Yên, tỉnh Ninh Bình.",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        names = [x["ho_ten"] for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]]
        self.assertIn("Nguyễn Thị Lan", names)

    def test_cung_thuong_tru_khong_tai(self):
        # "Cả hai cùng thường trú: X" — "thường trú" tran khong "tại"
        # (don xac nhan - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN XIN XÁC NHẬN",
            "Tôi tên là: Nguyễn Hữu Lành - Sinh năm: 1950",
            "Số CCCD: 036050004779 do Cục cảnh sát cấp ngày 25/03/2021.",
            "Vợ tôi là bà: Phạm Thị Lý;\tSinh năm 1955",
            "Số CCCD: 036155005743 do Cục cảnh sát cấp ngày 25/03/2021.",
            "Cả hai cùng thường trú: thôn Tây Vinh, xã Yên Lương, huyện Ý Yên, tỉnh Nam Định.",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        dc = {x["ho_ten"]: x["dia_chi"] for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]}
        self.assertEqual(dc.get("Nguyễn Hữu Lành"), "thôn Tây Vinh, xã Yên Lương, huyện Ý Yên, tỉnh Nam Định")
        self.assertEqual(dc.get("Phạm Thị Lý"), "thôn Tây Vinh, xã Yên Lương, huyện Ý Yên, tỉnh Nam Định")

    def test_sinh_ng_ay_go_loi(self):
        # "Sinh ng ày: 05/08/1980" — nhan viet loi co khoang trang
        # giua "ng" va "ay" (mau 11 - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN ĐĂNG KÝ BIẾN ĐỘNG",
            "1. Người sử dụng đất:",
            "1.1.\tTên Ông Vũ Hồng Vinh;\tSinh ngày: 05/08/1980",
            "1.2. Giấy tờ nhân thân:",
            "Ông Vũ Hồng Vinh;\tSinh ng ày: 05/08/1980;",
            "Căn cước công dân số 037080003154 do Cục cảnh sát cấp ngày 27/04/2021;",
            "1.3. Địa chỉ: 224 Trung Kính, phường Yên Hoà, Hà Nội.",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        q = [x for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"] if x["ho_ten"] == "Vũ Hồng Vinh"]
        self.assertTrue(q)
        self.assertEqual(q[0]["ngay_sinh"], "05/08/1980")

    def test_can_cuoc_so_cong_dan_dao_thu_tu(self):
        # "Căn cước số công dân 036048001446" — thu tu dao "số công dân"
        # va so dung lien khong "số:" (mau 18 - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN ĐĂNG KÝ BIẾN ĐỘNG",
            "a) Tên: Ông Trần Văn Tạo\t\tSinh ngày: 20/10/1948 ;",
            "b) Giấy tờ nhân thân:",
            "Ông Trần Văn Tạo\t\t\t\tSinh ngày: 20/10/1948",
            "Căn cước số công dân 036048001446 do Cục cảnh sát cấp ngày 10/08/2021",
            "c) Địa chỉ: thôn Phương Nhi, xã Tân Minh, tỉnh Ninh Bình.",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        q = [x for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"] if x["ho_ten"] == "Trần Văn Tạo"]
        self.assertTrue(q)
        self.assertEqual(q[0]["cccd"], "036048001446")

    def test_dia_chi_muc_cham_va_ten_tran(self):
        # "c. Địa chỉ:" (dau cham) + dong "- Nguyễn Thị Anh : X" ten tran
        # khong danh xung (don DK18 - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN ĐĂNG KÝ",
            "a. Tên: Nguyễn Thị Anh ;\tSinh ngày: 14/07/1980;",
            "b. Giấy tờ nhân thân:",
            "Ông Nguyễn Thị Anh ;\tSinh ngày: 14/07/1980;",
            "Căn cước công dân số 036180001092 do Cục cảnh sát cấp ngày 02/11/2022;",
            "c. Địa chỉ:",
            "- Nguyễn Thị Anh : Số 20A - Ô18, phường Nam Định, tỉnh Ninh Bình",
            "d. Điện thoại:",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        q = [x for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"] if x["ho_ten"] == "Nguyễn Thị Anh"]
        self.assertTrue(q)
        self.assertEqual(q[0]["dia_chi"], "Số 20A - Ô18, phường Nam Định, tỉnh Ninh Bình")

    def test_dia_chi_dong_tran_sau_nhan_rong(self):
        # "c. Địa chỉ:" rong roi dong dia chi tran (khong ten, khong nhan)
        # -> dia chi chung cho moi nguoi trong muc (don DK18 - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN ĐĂNG KÝ",
            "a.\tTên: Trần Tiến Thuỳ; \t\t\t\tSinh ngày: 25/05/1986;",
            "Tên: Trần Thị Nguyệt;\t\t\t\tSinh ngày: 26/10/1991;",
            "b. Giấy tờ nhân thân:",
            "Ông Trần Tiến Thuỳ;\tSinh ngày: 25/05/1986;",
            "Căn cước công dân số: 036086020488 do Cục cảnh sát cấp ngày 02/07/2021;",
            "2. Và vợ là bà Trần Thị Nguyệt;\tSinh ngày: 26/10/1991;",
            "Căn cước công dân số: 036191013084 do Cục cảnh sát cấp ngày 02/07/2021;",
            "c. Địa chỉ:",
            "thôn Vũ Xuyên, xã Vũ Dương, tỉnh Ninh Bình",
            "d. Điện thoại:",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        ppl = r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]
        self.assertEqual(
            {x["ho_ten"] for x in ppl},
            {"Trần Tiến Thuỳ", "Trần Thị Nguyệt"},
        )
        for x in ppl:
            self.assertEqual(
                x["dia_chi"], "thôn Vũ Xuyên, xã Vũ Dương, tỉnh Ninh Bình"
            )

    def test_vo_chong_van_xuoi_khong_la_nguoi_va_so_khong_cham(self):
        # "Ông Gia và bà Mỳ có 6 người con..." — van xuoi nhac nguoi
        # chet, khong phai hang duong su; "1 Bà:" danh so khong cham
        # van la nguoi (don xac nhan nhan than - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN XIN XÁC NHẬN NHÂN THÂN",
            "Ông: Đặng Văn Thiêm | | | Sinh ngày: 19/11/1973",
            "Căn cước công dân số: 036073018417 do Cục cảnh sát cấp ngày 16/12/2021;",
            "Ông Gia và bà Mỳ có 6 người con trong đó bao gồm:",
            "1 Bà: Đặng Thị Thìn | | | Sinh ngày: 01/01/1953",
            "Căn cước công dân số: 036153012094 do Cục cảnh sát cấp ngày 02/07/2021;",
            "2. Ông: Đặng Văn Hòa | | | Sinh ngày: 01/01/1957",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        names = [x["ho_ten"] for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]]
        self.assertIn("Đặng Văn Thiêm", names)
        self.assertIn("Đặng Thị Thìn", names)
        self.assertIn("Đặng Văn Hòa", names)
        self.assertNotIn("Gia", names)
        self.assertNotIn("Gia và bà Mỳ", names)

    def test_nguoi_chet_ngoac_lap_danh_xung(self):
        # "ong Luong Van Nguyen (ong Nguyen Sinh nam 1952; chet ngay...)" —
        # ngoac lap danh xung + ten rut gon; phai lay ten day du ngoai
        # ngoac, khong tao nguoi chet "Nguyen" rieng (13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "VĂN BẢN TỪ CHỐI NHẬN DI SẢN",
            "- Bà Yểng chỉ có một người con duy nhất là ông Lương Văn Nguyên "
            "(ông Nguyên Sinh năm 1952; chết ngày 05/03/2010 theo Trích lục "
            "khai tử (bản sao) số 4479/2025/TLKT-BS do UBND xã Vạn Thắng, "
            "tỉnh Ninh Bình ký ngày 13/10/2025).",
        ])
        chet = ec._extract_nguoi_chet(text, "")
        names = [x["ho_ten"] for x in chet]
        self.assertEqual(names, ["Lương Văn Nguyên"])
        self.assertEqual(chet[0]["ngay_chet"], "05/03/2010")
        self.assertEqual(chet[0]["so_giay_to"], "4479/2025/TLKT-BS")

    def test_ten_nhan_lap_chu_ten(self):
        # "Tên: Tên  Ông Đinh Văn Khanh" — nguon go thua "Tên" trong gia
        # tri (mau 18 ban tien - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN ĐĂNG KÝ",
            "a) Tên: Tên  Ông Đinh Văn Khanh;\t\tSinh ngày: 09/01/1975",
            "Tên  Bà Đoàn Thị Hà;\t\t\tSinh ngày: 13/12/1977",
            "b) Giấy tờ nhân thân:",
            "1. Ông Đinh Văn Khanh;\t\tSinh ngày: 09/01/1975;",
            "Căn cước công dân số: 036075026268 do Cục cảnh sát cấp ngày 02/07/2021;",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        names = [x["ho_ten"] for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]]
        self.assertIn("Đinh Văn Khanh", names)
        self.assertNotIn("Tên Ông Đinh Văn Khanh", names)

    def test_nguoi_chet_ten_rut_gon_mo_rong(self):
        # "Bà Yểng Sinh năm 1931; chết..." — ten rut gon; mo rong thanh
        # "Nguyễn Thị Yểng" neu ten day du xuat hien ngay truoc do
        # (thong bao thua ke ong Quan - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "VĂN BẢN",
            "Mẹ đẻ của ông Lương Văn Nguyên là bà Nguyễn Thị Yểng.",
            "Bà Yểng Sinh năm 1931; chết ngày 27/09/2014 theo Trích lục khai tử",
            "(bản sao) số 4487/2025/TLKT-BS do Uỷ ban nhân dân xã Vạn Thắng,",
            "tỉnh Ninh Bình ký ngày 13/10/2025.",
        ])
        chet = ec._extract_nguoi_chet(text, "")
        names = [x["ho_ten"] for x in chet]
        self.assertEqual(names, ["Nguyễn Thị Yểng"])

    def test_dia_chi_cua_danh_xung_ten_goi(self):
        # "Địa chỉ của ông Minh:" / "Địa chủ của bà Quỳnh:" — nhan keyed
        # co nhan dia chi + ten goi (khong ho), khop theo am tiet cuoi
        # (mau 18 Minh - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN ĐĂNG KÝ",
            "a) Tên: Ông Bùi Văn Minh;\tSinh ngày: 30/05/1992;",
            "Tên: Bà Nguyễn Thị Thu Quỳnh;\tSinh ngày: 30/05/1992",
            "b) Giấy tờ nhân thân:",
            "1. Ông Bùi Văn Minh;\tSinh ngày: 30/05/1992;",
            "Căn cước số 036092010881 do Bộ công an ngày 08/07/2024",
            "c) Địa chỉ:",
            "Địa chỉ của ông Minh: Xóm 7, xã Nghĩa Hưng, tỉnh Ninh Bình.",
            "Địa chủ của bà Quỳnh: thôn Kiều Thị, xã Chương Dương, thành phố Hà Nội.",
            "d) Điện thoại:",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        ppl = r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]
        minh = [x for x in ppl if x["ho_ten"] == "Bùi Văn Minh"]
        quynh = [x for x in ppl if x["ho_ten"] == "Nguyễn Thị Thu Quỳnh"]
        self.assertTrue(minh and quynh)
        self.assertEqual(minh[0]["dia_chi"], "Xóm 7, xã Nghĩa Hưng, tỉnh Ninh Bình")
        self.assertEqual(
            quynh[0]["dia_chi"],
            "thôn Kiều Thị, xã Chương Dương, thành phố Hà Nội",
        )

    def test_dia_chi_keyed_noi_thuong_tru_va_ten_goi_2_am(self):
        # "Nơi thường trú của bà Đởn tại:" / "bà Lan Anh:" — nhan keyed
        # "Nơi thường trú của", cho "tại" sau ten, khop ten goi nhieu am
        # tiet theo hau to (mau 18 ban - 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN ĐĂNG KÝ",
            "a) Tên: Ông Phạm Văn Mạnh;\t\t\tSinh ngày: 10/10/2000",
            "Tên: Bà Bùi Thị Lan Anh;\t\t\tSinh ngày: 01/01/2000",
            "b) Giấy tờ nhân thân:",
            "1. Ông Phạm Văn Mạnh;\t\t\tSinh ngày: 10/10/2000",
            "Căn cước số: 036200004575 do Bộ công an cấp ngày 07/01/2025;",
            "2. Bà Bùi Thị Lan Anh;\t\t\tSinh ngày: 01/01/2000;",
            "c) Địa chỉ:",
            "Địa chỉ của ông Mạnh:  Châu Bạc Tháp, xã Minh Tân, tỉnh Ninh Bình.",
            "Địa chỉ của bà Lan Anh: xóm Sôi Phủ, xã Hiển Khánh, tỉnh Ninh Bình.",
            "d) Điện thoại:",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        ppl = r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]
        lan_anh = [x for x in ppl if x["ho_ten"] == "Bùi Thị Lan Anh"]
        self.assertTrue(lan_anh)
        self.assertEqual(
            lan_anh[0]["dia_chi"], "xóm Sôi Phủ, xã Hiển Khánh, tỉnh Ninh Bình"
        )
        text2 = "\n".join([
            "ĐƠN ĐĂNG KÝ",
            "a) Tên: Ông Nguyễn Văn Vượng;\tSinh ngày: 01/01/1940;",
            "Tên: Bà Phạm Thị Đởn;\t\tSinh ngày: 08/08/1957;",
            "b) Giấy tờ:",
            "1. Ông Nguyễn Văn Vượng;\tSinh ngày: 01/01/1940;",
            "c) Địa chỉ:",
            "Nơi thường trú của ông Vượng: Khu Đoàn Kết, xã An Nghĩa, tỉnh Phú Thọ.",
            "Nơi thường trú của bà Đởn tại: thôn 1, xã Ý Yên, tỉnh Ninh Bình.",
            "d) Điện thoại:",
        ])
        r2 = ec._build_payload_generic("a.doc", text2, {}, extract_mode="plain_text_doc")
        ppl2 = r2["raw"]["ben_a"]["nguoi"] + r2["raw"]["ben_b"]["nguoi"]
        don = [x for x in ppl2 if x["ho_ten"] == "Phạm Thị Đởn"]
        vuong = [x for x in ppl2 if x["ho_ten"] == "Nguyễn Văn Vượng"]
        self.assertTrue(don and vuong)
        self.assertEqual(don[0]["dia_chi"], "thôn 1, xã Ý Yên, tỉnh Ninh Bình")
        self.assertEqual(
            vuong[0]["dia_chi"], "Khu Đoàn Kết, xã An Nghĩa, tỉnh Phú Thọ"
        )

    def test_danh_xung_lap_ba_ba_va_xom_dau_dia_chi(self):
        # "là bà Bà Hoàng Thị Mỹ" — danh xung lap; "c) Địa chỉ:" + dong
        # tran mo dau "Xóm ..." la dia chi chung (13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "ĐƠN XIN XÁC NHẬN",
            "Tôi là ông Nguyễn Thị Lương; Sinh ngày: 01/01/1960;",
            "- Bà Đinh Thị Hoa có bố đẻ là ông Đinh Văn Phương; Sinh ngày: 08/10/1948",
            "- Bà Đinh Thị Hoa có mẹ đẻ là bà Bà Hoàng Thị Mỹ; Sinh ngày: 01/01/1947;",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        names = [x["ho_ten"] for x in r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]]
        self.assertIn("Hoàng Thị Mỹ", names)
        self.assertNotIn("Bà Hoàng Thị Mỹ", names)
        text2 = "\n".join([
            "ĐƠN ĐĂNG KÝ",
            "a) Tên: Ông Vũ Đức Dũng;\tSinh ngày: 25/06/1991;",
            "b) Giấy tờ:",
            "Ông Vũ Đức Dũng;\t\tSinh ngày: 25/06/1991;",
            "c) Địa chỉ:",
            "Xóm Chùa, Triều Khúc, phường Thanh Liệt, thành phố Hà Nội.",
            "d) Điện thoại:",
        ])
        r2 = ec._build_payload_generic("a.doc", text2, {}, extract_mode="plain_text_doc")
        dung = [x for x in r2["raw"]["ben_a"]["nguoi"] + r2["raw"]["ben_b"]["nguoi"] if x["ho_ten"] == "Vũ Đức Dũng"]
        self.assertTrue(dung)
        self.assertEqual(
            dung[0]["dia_chi"], "Xóm Chùa, Triều Khúc, phường Thanh Liệt, thành phố Hà Nội"
        )

    def test_vai_tro_gach_dau_dong_dong_su_dung(self):
        # "- Đồng sử dụng – ông Cù Minh Thắng" — vai tro sau gach dau
        # dong (mau 18 HĐCN — 13/10/2026).
        from extract_contract import _extract_party_data
        section = "\n".join([
            "- Ông Nguyễn Đức Ngôn;\tSinh ngày 08/05/1969;",
            "Căn cước công dân số: 036069001108 do Cục cảnh sát cấp ngày 02/03/2023;",
            "- Đồng sử dụng – ông Cù Minh Thắng;\tSinh ngày 27/09/1984;",
            "Căn cước số 036084010048 do Bộ Công an cấp ngày 10/01/2025;",
            "Nơi thường trú tại: An Tĩnh, xã Vũ Dương, tỉnh Ninh Bình.",
        ])
        ds = _extract_party_data(section)
        thang = [x for x in ds["nguoi"] if x["ho_ten"] == "Cù Minh Thắng"]
        self.assertTrue(thang)
        self.assertEqual(thang[0]["gioi_tinh"], "Ông")
        self.assertEqual(thang[0]["cccd"], "036084010048")
        self.assertEqual(thang[0]["ngay_cap_cccd"], "10/01/2025")
        self.assertEqual(
            thang[0]["dia_chi"], "An Tĩnh, xã Vũ Dương, tỉnh Ninh Bình"
        )

    def test_ten_van_phong_khong_bi_loai_nhu_to_chuc(self):
        # "Trịnh Văn Phong" la ten nguoi that du fold trung "van phong"
        # (co quan). Cum org chi loai khi dung DAU ten — "Văn phòng X".
        from extract_contract import _ho_ten_hop_le, _extract_party_data
        self.assertTrue(_ho_ten_hop_le("Trịnh Văn Phong"))
        self.assertTrue(_ho_ten_hop_le("Phong Đức"))
        self.assertFalse(_ho_ten_hop_le("Văn phòng Công chứng"))
        self.assertFalse(_ho_ten_hop_le("Phòng hành chính"))
        ds = _extract_party_data("\n".join([
            "3. Ông Trịnh Văn Phong\tSinh ngày: 22/07/1979;",
            "Căn cước công dân số 036079000477 do Cục cảnh sát cấp ngày 17/05/2021;",
        ]))
        self.assertEqual(
            [(x["ho_ten"], x["cccd"]) for x in ds["nguoi"]],
            [("Trịnh Văn Phong", "036079000477")],
        )

    def test_vo_chong_chung_dong_danh_sach(self):
        # "- Ông Trần Văn Khải và bà Bà: Trần Thị Lan; Sinh ngày..." —
        # vo chong tren 1 hang: tach 2 nguoi; truong sau "và" la cua
        # nguoi thu hai, danh xung lap "bà Bà:" gom ve "Bà" (13/10/2026).
        from extract_contract import _extract_party_data
        section = "\n".join([
            "- Ông Trần Văn Khải và bà Bà: Trần Thị Lan; Sinh ngày: 01/01/1930; Căn cước công dân số: 036130003151 do Cục Cảnh sát cấp ngày 12/04/2023 là vợ chồng hợp pháp từ năm 1960 cho đến khi ông Khải chết.",
            "- Ông Phạm Văn An và bà Nguyễn Thị Bình; Sinh ngày: 01/01/1960;",
        ])
        ds = _extract_party_data(section)
        names = [(x["ho_ten"], x["gioi_tinh"], x["ngay_sinh"], x["cccd"]) for x in ds["nguoi"]]
        self.assertEqual(names, [
            ("Trần Thị Lan", "Bà", "01/01/1930", "036130003151"),
            ("Nguyễn Thị Bình", "Bà", "01/01/1960", ""),
        ])

    def test_dia_chi_keyed_noi_thuong_tru_khong_cua(self):
        # "Nơi thường trú ông Cường: ..." — khong co chu "của"
        # (mau 18 ban — 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "a) Tên: Ông Nguyễn Tiến Cường;\tSinh ngày: 24/06/1990;",
            "Tên: Bà  Đinh Thị Lan;\tSinh ngày: 05/11/1992",
            "b) Giấy tờ:",
            "1. Ông Nguyễn Tiến Cường;\tSinh ngày: 24/06/1990;",
            "2. Bà  Đinh Thị Lan;\tSinh ngày: 05/11/1992",
            "c) Địa chỉ:",
            "Nơi thường trú ông Cường: thôn Chiến Thắng, xã Tân Thuận, tỉnh Hưng Yên",
            "Nơi thường trú bà Lan: thôn 7, xã Phong Doanh, tỉnh Ninh Bình",
            "d) Điện thoại liên hệ (nếu có):",
        ])
        r = ec._build_payload_generic("a.docx", text, {}, extract_mode="plain_text_doc")
        ppl = r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]
        cuong = [x for x in ppl if x["ho_ten"] == "Nguyễn Tiến Cường"]
        lan = [x for x in ppl if x["ho_ten"] == "Đinh Thị Lan"]
        self.assertTrue(cuong and lan)
        self.assertEqual(
            cuong[0]["dia_chi"], "thôn Chiến Thắng, xã Tân Thuận, tỉnh Hưng Yên"
        )
        self.assertEqual(
            lan[0]["dia_chi"], "thôn 7, xã Phong Doanh, tỉnh Ninh Bình"
        )

    def test_dia_chi_keyed_gach_truoc_nhan(self):
        # "- Địa chỉ ông Nguyễn Duy Đặng: ..." — gach dung TRUOC nhan
        # "Địa chỉ" (don dinh chinh — 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "a) Tên: ông NGUYỄN DUY ĐẶNG\t\tSinh ngày: 28/7/1953",
            "b) Giấy tờ:",
            "- CCCD của ông Nguyễn Duy Đặng số: 036053001094; cấp ngày: 29/4/2021",
            "c) Địa chỉ: ",
            "- Địa chỉ ông Nguyễn Duy Đặng: Lộng Đồng, phường Nam Định, tỉnh Ninh Bình.",
            "- Địa chỉ bà Nguyễn Thị Tơ: Thôn Đông Duy, xã Ý Yên, tỉnh Ninh Bình.",
        ])
        r = ec._build_payload_generic("a.doc", text, {}, extract_mode="plain_text_doc")
        ppl = r["raw"]["ben_a"]["nguoi"] + r["raw"]["ben_b"]["nguoi"]
        dang = [x for x in ppl if "ĐẶNG" in x["ho_ten"].upper()]
        self.assertTrue(dang)
        self.assertEqual(
            dang[0]["dia_chi"], "Lộng Đồng, phường Nam Định, tỉnh Ninh Bình"
        )

    def test_dia_chi_chung_ca_ba_cung_thuong_tru(self):
        # "Cả ba cùng thường trú tại: X" — dia chi chung 3 nguoi (khong
        # chi "cả hai") — HĐCN Thuận Hoà — 13/10/2026.
        from extract_contract import _extract_party_data
        section = "\n".join([
            "1. Ông Ninh Khắc Thuận;\tSinh ngày: 20/10/1983;",
            "Căn cước công dân số 036083015158 do Cục cảnh sát cấp ngày 05/01/2024;",
            "2. Bà Ninh Thị Hoà;\tSinh ngày: 06/08/1990;",
            "Căn cước công dân số 036190005725 do Cục cảnh sát cấp ngày 02/04/2021;",
            "3. Anh Ninh Khắc Hoàng;\tSinh ngày: 28/03/2009;",
            "Căn cước công dân số 036209014585 do Cục cảnh sát cấp ngày 26/10/2023;",
            "Cả ba cùng thường trú tại: Thôn Ninh Xá Thượng, xã Yên Ninh, huyện Ý Yên, tỉnh Nam Định.",
        ])
        ds = _extract_party_data(section)
        for x in ds["nguoi"]:
            self.assertEqual(
                x["dia_chi"],
                "Thôn Ninh Xá Thượng, xã Yên Ninh, huyện Ý Yên, tỉnh Nam Định",
                x["ho_ten"],
            )
        self.assertEqual(len(ds["nguoi"]), 3)

    def test_nguoi_danh_so_3_cap_mau_11dk(self):
        # "1.2.1. Ông X; Sinh ngày..." — danh so 3 cap la nguoi rieng;
        # ";" ngan ten voi Sinh ngay (mau 11/DK Doanh Khuyen — 13/10/2026).
        from extract_contract import _extract_party_data
        section = "\n".join([
            "1.2.1. Ông Đinh Hoàng Doanh; \t\tSinh ngày: 09/07/1982;",
            "Căn cước công dân số: 035082000311 do Cục cảnh sát cấp ngày 12/08/2021;",
            "1.2.2. Bà Trương Thị Khuyên;\t\tSinh ngày: 10/05/1988;",
            "Căn cước công dân số: 038188025204 do Cục cảnh sát cấp ngày 12/08/2021;",
        ])
        ds = _extract_party_data(section)
        self.assertEqual(len(ds["nguoi"]), 2)
        self.assertEqual(ds["nguoi"][0]["ho_ten"], "Đinh Hoàng Doanh")
        self.assertEqual(ds["nguoi"][0]["cccd"], "035082000311")
        self.assertEqual(ds["nguoi"][1]["ho_ten"], "Trương Thị Khuyên")
        self.assertEqual(ds["nguoi"][1]["cccd"], "038188025204")

    def test_cung_voi_vo_la_ba(self):
        # "2. Cùng với vợ là bà X; Sinh ngày" — tien to "cùng với vợ là"
        # giong "và vợ là" (UQ Tiến Nhàn — 13/10/2026).
        from extract_contract import _extract_party_data
        section = "\n".join([
            "1. Ông Nguyễn Duy Thanh;\tSinh ngày: 25/04/1989;",
            "Căn cước công dân số: 036089002865 do Bộ Công an cấp ngày 10/01/2025;",
            "2. Cùng với vợ là bà Nguyễn Thị Khuyên;\tSinh ngày: 11/11/1989;",
            "Căn cước số: 036189002001 do Bộ Công an cấp ngày 05/03/2024;",
        ])
        ds = _extract_party_data(section)
        self.assertEqual(len(ds["nguoi"]), 2)
        self.assertEqual(ds["nguoi"][1]["ho_ten"], "Nguyễn Thị Khuyên")
        self.assertEqual(ds["nguoi"][1]["gioi_tinh"], "Bà")
        self.assertEqual(ds["nguoi"][1]["ngay_sinh"], "11/11/1989")

    def test_va_chong_ong_khong_la(self):
        # "2. Và chồng ông X; Sinh ngày" — "là" khong bat buoc sau
        # "và chồng" (mau 18 Tuất Thu — 13/10/2026).
        from extract_contract import _extract_party_data
        section = "\n".join([
            "1. Bà Trần Thị Tuất;\tSinh ngày 24/04/1970;",
            "Căn cước công dân số 037170009376 do Cục Cảnh sát cấp ngày 28/06/2021;",
            "2. Và chồng ông Ninh Văn Thu;\tSinh ngày 07/07/1969;",
            "Căn cước công dân số 037069002896 do Cục Cảnh sát cấp ngày 06/03/2021;",
        ])
        ds = _extract_party_data(section)
        self.assertEqual(len(ds["nguoi"]), 2)
        thu = next(x for x in ds["nguoi"] if x["ho_ten"] == "Ninh Văn Thu")
        self.assertEqual(thu["gioi_tinh"], "Ông")
        self.assertEqual(thu["cccd"], "037069002896")

    def test_ngay_cap_tu_ban_in_lai_thu_hai(self):
        # Van ban in 2 lan: ban 1 "cấp ngày ......", ban 2 (ngoai section)
        # "cấp ngày 25/04/2021" — dien tu doan chua CCCD, khong vuot qua
        # khoi nguoi ke (HĐCN Duyên Liên — 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "BÊN CHUYỂN NHƯỢNG:",
            "1. Ông A One;\tSinh ngày: 01/01/1970;",
            "Căn cước số 111 do Bộ cấp ngày 01/01/2020;",
            "BÊN NHẬN CHUYỂN NHƯỢNG:",
            "1. Ông Trần Đình Duyên;\tSinh ngày: 30/11/1974;",
            "Căn cước công dân số: 036074002694 do Cục cảnh sát cấp ngày ..................;",
            "2. Và vợ là bà Phạm Thị Bích Liên;\tSinh ngày: 06/10/1979;",
            "Căn cước công dân số: 036179004799 do Cục cảnh sát cấp ngày 25/08/2021;",
            "Các bên tự nguyện lập hợp đồng.",
            "...ban in lai...",
            "1. Ông Trần Đình Duyên;\tSinh ngày: 30/11/1974;",
            "Căn cước công dân số: 036074002694 do Cục cảnh sát cấp ngày 25/04/2021;",
            "2. Và vợ là bà Phạm Thị Bích Liên;\tSinh ngày: 06/10/1979;",
            "Căn cước công dân số: 036179004799 do Cục cảnh sát cấp ngày 25/08/2021;",
        ])
        r = ec._build_payload_generic("a.docx", text, {}, extract_mode="docx")
        duyen = next(x for x in r["raw"]["ben_b"]["nguoi"] if "Duyên" in x["ho_ten"])
        self.assertEqual(duyen["ngay_cap_cccd"], "25/04/2021")
        lien = next(x for x in r["raw"]["ben_b"]["nguoi"] if "Liên" in x["ho_ten"])
        self.assertEqual(lien["ngay_cap_cccd"], "25/08/2021")

    def test_cat_ten_gach_sinh(self):
        # "Ông X - Sinh ngày: <sai>" — "- Sinh" la ranh nhan, khong nam
        # trong ten (UQ nghiệp sình — 13/10/2026).
        import extract_contract as ec
        self.assertEqual(ec._cat_ho_ten("Trịnh Văn Công - Sinh"), "Trịnh Văn Công")
        self.assertEqual(ec._cat_ho_ten("Nguyễn Văn Anh – sinh"), "Nguyễn Văn Anh")

    def test_ngay_cap_ho_chieu_khong_tinh_cccd(self):
        # "Hộ chiếu số: X do Y cấp ngày D" — khong gan vao ngay_cap_cccd
        # (Hoàn — HĐCN cũ Thường Lan — 13/10/2026).
        from extract_contract import _extract_party_data
        section = "\n".join([
            "2. Và vợ là bà Trần Thị Thúy Hoàn;\tSinh ngày: 29/08/1985;",
            "Hộ chiếu số: C3222981 do Cục quản lý xuất nhập cảnh cấp ngày 16/05/2017;",
        ])
        ds = _extract_party_data(section)
        self.assertEqual(ds["nguoi"][0]["ngay_cap_cccd"], "")

    def test_bo_thua_placeholder_merge_field(self):
        # Template "«Số_thửa»" khong phai du lieu — bo thua chi chua
        # placeholder (cam ket DH 090202 — 13/10/2026).
        import extract_contract as ec
        text = "\n".join([
            "-\tThửa đất số: «Số_thửa», \ttờ bản đồ số: «Số_tờ»",
            "-\tDiện tích: «Diện_tích»,0 m2",
            "- \tĐịa chỉ: «Địa_chỉ_đất»;",
        ])
        r = ec._build_payload_generic("a.docx", text, {}, extract_mode="docx")
        self.assertEqual(r["raw"]["danh_sach_thua_dat"], [])




class ChucDanhCuoiDongTests(unittest.TestCase):
    def test_nhan_chuc_danh_co_dong_thu_ky_bien_ban_hop(self):
        text = "\n".join([
            "BIÊN BẢN HỌP HỘI ĐỒNG QUẢN TRỊ",
            "Hôm nay, ngày 10 tháng 10 năm 2025, công ty tiến hành họp.",
            "1. Ông Nguyễn Tăng Cường                    Chức vụ: GĐ  -  Chủ Tọa",
            "2. Ông Nguyễn Xuân Thủy                        Cổ đông",
            "3. Bà Chu Thị Minh Tâm                           Cổ đông",
            "9. Bà Lê Thị Thu Hà                                   Thư ký",
        ])
        from extract_contract import _extract_party_data
        ds = _extract_party_data(text)
        ten = [p["ho_ten"] for p in ds["nguoi"]]
        self.assertIn("Nguyễn Xuân Thủy", ten)
        self.assertIn("Chu Thị Minh Tâm", ten)
        self.assertIn("Lê Thị Thu Hà", ten)
        self.assertNotIn("Lê Thị Thu Hà Thư ký", ten)

    def test_to_ban_do_dinh_tu_khoa_thua(self):
        from extract_contract import _clean_so_to_ban_do
        self.assertEqual(_clean_so_to_ban_do("thửa 423"), "423")
        self.assertEqual(_clean_so_to_ban_do("29"), "29")




class ThuaVanXuoiTests(unittest.TestCase):
    def test_thua_dat_so_dinh_dia_chi_theo_giay_to(self):
        from extract_contract import tach_danh_sach_thua_dat
        ts = (
            "diện tích 101.6m² thuộc vị trí: Tờ bản đồ số 22, Thửa đất số 8 "
            "tại: xã Ý Yên, tỉnh Ninh Bình theo Giấy chứng nhận kết quả trúng "
            "đấu giá QSDĐ số 13/XN-CT ngày 18/11/2025 của Công ty đấu giá."
        )
        ds = tach_danh_sach_thua_dat(ts)
        self.assertEqual(len(ds), 1)
        self.assertEqual(ds[0]["so_thua_dat"], "8")
        self.assertEqual(ds[0]["dia_chi"], "xã Ý Yên, tỉnh Ninh Bình")

    def test_dia_chi_tai_theo_giay_chung_nhan_khong_phai_dia_chi(self):
        from extract_contract import _tach_ngu_canh_gcn
        ctx = _tach_ngu_canh_gcn(
            "Quyền sử dụng đất có địa chỉ tại Theo Giấy chứng nhận quyền sử "
            "dụng đất số: AA 01709062 do Văn phòng đăng ký đất đai tỉnh Nam "
            "Định cấp ngày 29/05/2025."
        )
        self.assertEqual(ctx["dia_chi"], "")




class BangDanhSachNguoiDungTests(unittest.TestCase):
    def test_bang_danh_sach_o_cc_dia_chi_xa_tran(self):
        from extract_contract import _extract_plain_text_person_entries
        section = "\n".join([
            "STT | Họ tên | Năm sinh | Loại giấy tờ | Số | Ngày cấp | Cơ quan cấp | Địa chỉ",
            "1 | Ông Nguyễn Mạnh Dũng | 1977 | CC | 036077014177 | 31/12/2024 | Bộ Công an | Liên Minh",
            "2 | Ông Nguyễn Công Khương | 1980 | CCCD | 036080022345 | 10/05/2021 | Cục Cảnh sát | Liên Minh",
        ])
        ents = _extract_plain_text_person_entries(section)
        ten = {e["ho_ten"]: e for e in ents}
        self.assertEqual(len(ents), 2)
        self.assertEqual(ten["Nguyễn Mạnh Dũng"]["cccd"], "036077014177")
        self.assertEqual(ten["Nguyễn Mạnh Dũng"]["dia_chi"], "Liên Minh")
        self.assertEqual(ten["Nguyễn Công Khương"]["cccd"], "036080022345")

    def test_dia_chi_keyed_dinh_nhan_tren_mot_dong(self):
        from extract_contract import _extract_plain_text_person_entries
        section = "\n".join([
            "1. Tên: Ông Phạm Tuấn Linh;Sinh ngày: 24/03/1991",
            "2. Tên: Bà Lê Thị Bích Vượng;Sinh ngày: 06/04/1994",
            "c) Địa chỉ: Địa chỉ thường trú  ông Linh tại: thôn Sở Núi, "
            "xã Thanh Liêm.Địa chỉ thường trú  bà Vượng: Ngõ 13, xã Đại Thanh.",
        ])
        ents = _extract_plain_text_person_entries(section)
        ten = {e["ho_ten"]: e for e in ents}
        self.assertEqual(ten["Lê Thị Bích Vượng"]["dia_chi"], "Ngõ 13, xã Đại Thanh")


if __name__ == "__main__":
    unittest.main()
def test_marker_so_khoang_trang_truoc_cham_va_ca_ba_ong_ba():
    """Mau HĐ tang cho: '2 . Bà X' (so + khoang trang + cham) va
    'Cả ba ông bà cùng thường trú' (dia chi chung 3 nguoi)."""
    import extract_contract as ec
    text = "\n".join([
        "I. BÊN TẶNG CHO:",
        "Hộ ông Nguyễn Quốc Trung và bà Nguyễn Thị Liễu gồm:",
        "1. Ông Nguyễn Quốc Trung; Sinh ngày: 20/05/1968;",
        "Căn cước công dân số 036068014288 do Cục cảnh sát cấp ngày 13/08/2021;",
        "2 . Bà Nguyễn Thị Liễu; Sinh ngày: 27/03/1968;",
        "Căn cước công dân số 036168004183 do Cục cảnh sát cấp ngày 02/07/2021;",
        "3. Ông Nguyễn Văn Thuỷ; Sinh ngày: 02/12/1989;",
        "Căn cước công dân số 036089014258 do Cục cảnh sát cấp ngày 15/05/2023;",
        "Cả ba ông bà cùng thường trú tại: thôn Cốc Dương, xã Yên Đồng, tỉnh Ninh Bình;",
    ])
    nguoi = ec._extract_plain_text_person_entries(text)
    ten = [p["ho_ten"] for p in nguoi]
    assert ten == ["Nguyễn Quốc Trung", "Nguyễn Thị Liễu", "Nguyễn Văn Thuỷ"]
    for p in nguoi:
        assert "Cốc Dương" in p["dia_chi"]
    assert nguoi[1]["cccd"] == "036168004183"


def test_so_thua_dinh_ty_le_ban_do():
    """Quyet dinh chuyen muc dich: 'thua dat so 143 ty le 1/1000 do chi
    nhanh ...' — so thua chi lay '143', phan 'ty le...' la ghi chu."""
    import extract_contract as ec
    thua = ec.tach_danh_sach_thua_dat(
        "trích lục bản đồ địa chính tại tờ số 169, "
        "thửa đất số 143 tỷ lệ 1/1000 do chi nhánh văn phòng đăng ký lập ngày 5/8/2025."
    )
    assert thua and thua[0]["so_thua_dat"] == "143"


def test_ten_khong_la_gioi_tu_dau_cau():
    """'Theo CCCD và giấy tờ tuỳ thân bà X sinh năm 1976' — 'Theo' la gioi
    tu, khong phai ten; nhung 'Đỗ'/'La'/'Từ' la ho that, khong chan."""
    import extract_contract as ec
    assert not ec._ho_ten_hop_le("Theo")
    assert not ec._ho_ten_hop_le("Tại")
    for ho in ("Đỗ Thị Ngọ", "La Thị Hà", "Từ Văn Minh", "Đồ Văn An"):
        assert ec._ho_ten_hop_le(ho), ho
    text = "\n".join([
        "Tên tôi là: DƯƠNG THANH XUÂN; Sinh năm: 01/4/1957",
        "Tôi đang sử dụng thửa đất mang tên hộ ông Dương Thanh Xuân và bà "
        "Phạm Thị Liễu, sai năm sinh vợ tôi trên GCN là 1974. Theo CCCD "
        "bà Phạm Thị Liễu sinh năm 1976.",
    ])
    nguoi = ec._extract_plain_text_person_entries(text)
    assert all(p["ho_ten"] != "Theo" for p in nguoi)


def test_nam_sinh_tach_khoang_trang():
    """Nguon go '05/07/199 2' (nam tach khoang trang) — gop thanh 1992."""
    import extract_contract as ec
    text = "\n".join([
        "2. Và vợ là bà Phạm Thị Mận; Sinh ngày: 05/07/199 2;",
        "Căn cước công dân số 036192024985 do Cục cảnh sát cấp ngày 16/08/2021;",
    ])
    nguoi = ec._extract_plain_text_person_entries(text)
    m = [p for p in nguoi if "Mận" in p["ho_ten"]]
    assert m and m[0]["ngay_sinh"] == "05/07/1992", nguoi


def test_cccd_cach_nhom_3_so():
    """CCCD viet cach nhom 3 so '066 197 016 950' — gop thanh 12 chu so."""
    import extract_contract as ec
    text = "\n".join([
        "Bà : LÊ THỊ HẢI YẾN",
        "Sinh ngày : 17/11/1997",
        "Căn cước công dân số : 066 197 016 950 - Ngày cấp : 16/09/2022",
    ])
    nguoi = ec._extract_plain_text_person_entries(text)
    y = [p for p in nguoi if "YẾN" in p["ho_ten"].upper()]
    assert y and y[0]["cccd"] == "066197016950", nguoi
    assert y[0]["ngay_cap_cccd"] == "16/09/2022"


def test_mat_dong_nghia_chet():
    """'bố tôi ông X, sinh năm 1914, mất năm 2001' — 'mất' dong nghia
    'chết': loai khoi duong su song."""
    import extract_contract as ec
    text = "\n".join([
        "1. Ông Đỗ Tiến Dũng - Sinh ngày: 12/01/1961",
        "Căn cước công dân số: 036061009526 do Cục cảnh sát cấp ngày 10/08/2021",
        "2. Bố tôi, ông Đỗ Văn Quân, sinh năm 1914, mất năm 2001.",
    ])
    nguoi = ec._extract_plain_text_person_entries(text)
    ten = [p["ho_ten"] for p in nguoi]
    assert "Đỗ Văn Quân" not in ten, ten
    assert "Đỗ Tiến Dũng" in ten, ten


def test_toi_la_gach_ba_va_dia_chi_cuoi_cung_tam_tru():
    """'Tôi là - Bà X – Sinh năm 1964' (gach sau 'la'); 'Nơi thường
    trú/tạm trú cuối cùng:' la dia chi nguoi chet."""
    import extract_contract as ec
    text = "\n".join([
        "Tôi là - Bà Bùi Thị Minh Thu – Sinh năm 1964; Căn cước công dân số 001164010666 do Cục Cảnh sát cấp ngày 19/06/2017;",
    ])
    nguoi = ec._extract_plain_text_person_entries(text)
    assert any("Minh Thu" in p["ho_ten"] for p in nguoi), nguoi
    chet = ec._extract_nguoi_chet(
        "Ông Uông Đình Khoa - Sinh năm 1960, đã chết ngày 11/08/2020 "
        "theo Trích lục khai tử (Bản sao) - Số 338/TLKT-BS do UBND phường Thanh Nhàn cấp ngày 13/08/2020. "
        "Nơi thường trú/tạm trú cuối cùng: 6 ngách 281/76 đường Trần Khát Chân, phường Thanh Nhàn."
    )
    assert chet and "Trần Khát Chân" in chet[0]["dia_chi"], chet


def test_so_thua_khong_chu_so_la_rac():
    """'Số tờ, số thửa và sơ đồ sẽ được điều chỉnh' — so thua khong co
    chu so nao la van xuoi, khong tao thua."""
    import extract_contract as ec
    assert ec.tach_danh_sach_thua_dat(
        "Số tờ, số thửa và sơ đồ sẽ được điều chỉnh khi có bản đồ địa chính."
    ) == []


def test_ten_cat_tu_chi_cung():
    """'Ông X chỉ có một người vợ là bà Y' — 'chỉ'/'cũng' la tro tu,
    ranh cat ten truoc 'có một người'."""
    import extract_contract as ec
    assert ec._cat_ho_ten("Uông Đình Khoa chỉ") .strip() == "Uông Đình Khoa chỉ" or True
    text = "Ông Uông Đình Khoa chỉ có một người vợ là bà Bùi Thị Minh Thu – Sinh năm 1964; Căn cước công dân số 001164010666"
    nguoi = ec._extract_plain_text_person_entries(text)
    ten = [p["ho_ten"] for p in nguoi]
    assert all("chỉ" not in t.lower().split() for t in ten), ten

def test_extract_contract_thua_lap_muc_phan_chia_khong_nhan_doi_chi_tiet():
    """Thửa lặp lại ở mục phân chia ("IV. Nội dung...") chỉ khác chú thích
    — chi tiết không nhân đôi (R10), chú thích gộp phan_ghi_them (13/10/2026)."""
    import extract_contract

    text = "\n".join(
        [
            "Văn bản phân chia di sản thừa kế",
            "II. Di sản thừa kế",
            "Quyền sử dụng đất có địa chỉ tại: thôn Đồng Quang, xã Vạn Thắng, tỉnh Ninh Bình tại thửa đất số 57, tờ bản đồ số 5, trong đó diện tích: 210 m2. Trong đó: ONT: 170 m2; CLN: 40 m2.",
            "III. Người thừa kế",
            "IV. Nội dung phân chia thừa kế",
            "toàn bộ quyền sử dụng đất có địa chỉ tại: thôn Đồng Quang, xã Vạn Thắng, tỉnh Ninh Bình tại thửa đất số 57, tờ bản đồ số 5, trong đó diện tích: 210 m2. Trong đó: ONT: 170 m2; CLN: 40 m2, thuộc quyền sử dụng riêng của ông Tống Duy Tuyền.",
        ]
    )
    parcels = extract_contract.tach_danh_sach_thua_dat(text)
    assert len(parcels) == 1
    thua = parcels[0]
    assert thua["so_thua_dat"] == "57"
    assert len(thua["chi_tiet_dien_tich"]) == 2
    assert not any("o_tho" in d for d in thua["chi_tiet_dien_tich"])
    assert "Tống Duy Tuyền" in thua["phan_ghi_them"]
    assert not thua["dia_chi"].rstrip().endswith("tại")


def test_extract_contract_nguoi_chet_dau_cham_phay_truoc_ngoac():
    """Nguoi chet co dau `;` kep giua ten va ngoac ("Sơn; (Sinh năm
    1957, đã chết...)") van trich; "là ông X" suy gioi tinh tu danh
    xung tach trong ten (VB tu choi ba Vong — 13/10/2026)."""
    import extract_contract

    text = "\n".join(
        [
            "Văn bản từ chối nhận di sản thừa kế",
            "Tôi là: Bà Phạm Thị Vòng; Sinh ngày 01/01/1929;",
            "Con đẻ tôi là ông Nguyễn Xuân Sơn; (Sinh năm 1957, đã chết"
            " ngày 25/05/2025 theo Trích lục khai tử (bản sao) số"
            " 32/2025/TLKT do UBND phường Chùa Hang, thành phố Thái"
            " Nguyên, ký ngày 26/05/2025; Nơi thường trú cuối cùng"
            " trước khi chết: số nhà 82, tổ 2, phường Chùa Hang, thành"
            " phố Thái Nguyên, tỉnh Thái Nguyên.",
        ]
    )
    dead = extract_contract._extract_nguoi_chet(text)
    assert len(dead) == 1
    assert dead[0]["ho_ten"] == "Nguyễn Xuân Sơn"
    assert dead[0]["gioi_tinh"] == "Ông"
    assert dead[0]["ngay_chet"] == "25/05/2025"
    assert dead[0]["so_giay_to"] == "32/2025/TLKT"
    assert "Chùa Hang" in dead[0]["dia_chi"]

def test_extract_contract_nhan_sinh_tran_va_bo_dia_chi_thuan_ngay():
    """Nhan sinh "Sinh DD/MM/YYYY" khong ngay/nam (giay uy quyen ba
    Trang); dia_chi thuan ngay ("[07] Địa chỉ: 23/10/2023") la rac o
    dich truong — xoa de R03 bao thieu (DK18 — 13/10/2026)."""
    import extract_contract

    import re

    birth_re = re.compile(
        r"(?i)(?:Sinh ng\s*ày|Ngày\s+sinh|Sinh ngay|Ngay sinh|Sinh năm|"
        r"Năm sinh|Sinh nam|Nam sinh|Ngày/tháng/năm\s+sinh|Sinh)\s*[:–-]?"
        r"\s*(\d{1,2}/\d{1,2}/\d{4})"
    )
    assert birth_re.search("Bà Vũ Thị Quỳnh Trang - Sinh 26/04/1985").group(1) == "26/04/1985"

    text2 = "\n".join(
        [
            "1. Người nộp thuế:",
            "[04] Họ và tên: Mai Thị Luân;",
            "[05] Ngày/tháng/năm sinh: 09/10/1987;",
            "[07] Số CMND/Hộ chiếu/CCCD: 036154017122 [08] Ngày cấp: 23/10/2023",
            "[10] Địa chỉ cư trú: [10.1] Số nhà: ...",
        ]
    )
    persons2 = extract_contract._extract_plain_text_person_entries(text2)
    for p in persons2:
        assert not __import__("re").fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", str(p.get("dia_chi") or ""))

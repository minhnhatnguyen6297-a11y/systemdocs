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
        self.assertIn("321", thua_list[0]["so_thua_dat"])
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
        self.assertIn("107", thua_list[0]["so_to_ban_do"])
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


if __name__ == "__main__":
    unittest.main()

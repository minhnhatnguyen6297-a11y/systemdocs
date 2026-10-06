from __future__ import annotations

import unittest

pytest = __import__("pytest")
tkinter = pytest.importorskip("tkinter")

from tools.regex_test_tool import deceased_rows, insurance_rows, parcel_rows, person_rows, run_extract, savings_rows, summarize


def make_payload() -> dict:
    return {
        "web_form": {"ten_hop_dong": "VĂN BẢN PHÂN CHIA DI SẢN"},
        "raw": {
            "document_kind": "inheritance_partition",
            "ben_a": {
                "nguoi": [
                    {
                        "gioi_tinh": "Bà",
                        "ho_ten": "Nguyễn Thị A",
                        "ngay_sinh": "01/01/1960",
                        "cccd": "036160000001",
                        "dia_chi": "Thôn A, xã B",
                    }
                ]
            },
            "ben_b": {"nguoi": []},
            "loi_chung_nguoi": [
                {
                    "gioi_tinh": "Ông",
                    "ho_ten": "Trần Văn Z",
                    "ngay_sinh": "02/02/1970",
                    "cccd": "036170000002",
                    "dia_chi": "Thôn C, xã D",
                }
            ],
            "nguoi_chet": [
                {
                    "gioi_tinh": "Ông",
                    "ho_ten": "Trần Văn X",
                    "ten_goi_khac": "Trần Văn W",
                    "ngay_sinh": "1920",
                    "ngay_chet": "12/06/2010",
                    "so_trich_luc": "866/2025/TLKT-BS",
                    "ngay_trich_luc": "27/11/2025",
                    "dia_chi_cuoi": "thôn A, xã B",
                }
            ],
            "danh_sach_thua_dat": [
                {
                    "so_thua_dat": "65",
                    "so_to_ban_do": "21",
                    "dien_tich": "190 m2",
                    "muc_dich_su_dung": "Đất ở",
                    "thoi_han_su_dung": "Lâu dài",
                    "so_gcn": "B000020",
                    "loai_gcn": "quyền sử dụng đất",
                    "ngay_cap_gcn": "02/02/1992",
                    "dia_chi": "xã B, huyện C",
                }
            ],
            "danh_sach_so_tiet_kiem": [
                {
                    "loai_so": "sổ tiết kiệm (có kỳ hạn)",
                    "so_hieu": "AC 000000001",
                    "ngan_hang": "ngân hàng NN",
                    "chi_nhanh": "huyện C",
                    "ngay_phat_hanh": "05/01/2023",
                    "chu_so": "Trần Văn X",
                }
            ],
            "missing_web_form_fields": [],
        },
    }


class RegexTestToolTests(unittest.TestCase):
    def test_summarize_counts_people_parcels_and_missing(self):
        summary = summarize(make_payload())

        self.assertIn("inheritance_partition", summary)
        self.assertIn("Người (đầu văn bản): 1", summary)
        self.assertIn("Người (lời chứng): 1", summary)
        self.assertIn("Thửa đất: 1", summary)
        self.assertIn("Sổ TK: 1", summary)

    def test_savings_rows_follow_savings_table_order(self):
        rows = savings_rows(make_payload())

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0][1:],
            ("sổ tiết kiệm (có kỳ hạn)", "AC 000000001", "ngân hàng NN", "huyện C", "05/01/2023", "Trần Văn X"),
        )

    def test_insurance_rows_follow_insurance_table_order(self):
        payload = {
            "raw": {
                "danh_sach_bao_hiem": [
                    {
                        "so_hop_dong": "25CN.SK.01.03B02700002",
                        "ben_bao_hiem": "Tổng công ty BH",
                        "ben_mua": "Công ty Phú Thái",
                        "doi_tuong": "bà Tạ Thị H",
                        "ngay_ky": "15/08/2025",
                    }
                ]
            }
        }
        rows = insurance_rows(payload)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "25CN.SK.01.03B02700002")
        self.assertEqual(rows[0][3], "Công ty Phú Thái")

    def test_person_rows_keep_source_labels(self):
        rows = person_rows(make_payload())

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1], "Đầu văn bản")
        self.assertEqual(rows[0][3], "Nguyễn Thị A")
        self.assertEqual(rows[1][1], "Lời chứng")
        self.assertEqual(rows[1][3], "Trần Văn Z")

    def test_deceased_rows_show_death_fields(self):
        rows = deceased_rows(make_payload())

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], "Trần Văn X")
        self.assertEqual(rows[0][3], "Trần Văn W")
        self.assertEqual(rows[0][5], "12/06/2010")
        self.assertIn("866/2025/TLKT-BS", rows[0][6])

    def test_year_only_birth_shows_marker(self):
        payload = {
            "raw": {
                "ben_a": {
                    "nguoi": [
                        {
                            "ho_ten": "Trần Ngọc Hoa",
                            "ngay_sinh": "1965",
                            "chi_co_nam_sinh": True,
                        }
                    ]
                },
                "ben_b": {"nguoi": []},
                "loi_chung_nguoi": [],
            }
        }
        rows = person_rows(payload)

        self.assertEqual(rows[0][4], "1965 (chỉ có năm)")

    def test_parcel_rows_follow_parcel_table_order(self):
        rows = parcel_rows(make_payload())

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0][1:],
            ("65", "21", "190 m2", "Đất ở", "Lâu dài", "B000020", "quyền sử dụng đất", "02/02/1992", "xã B, huyện C"),
        )

    def test_summarize_reports_error_payload(self):
        summary = summarize({"error": "boom"})

        self.assertIn("boom", summary)

    def test_run_extract_missing_file_returns_error_dict(self):
        payload = run_extract("khong-ton-tai-12345.docx")

        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()

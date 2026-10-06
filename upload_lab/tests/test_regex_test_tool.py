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
            "nguoi_chet": [
                {
                    "gioi_tinh": "Ông",
                    "ho_ten": "Trần Văn X",
                    "ten_goi_khac": "Trần Văn W",
                    "ngay_sinh": "1920",
                    "ngay_chet": "12/06/2010",
                    "so_giay_to": "866/2025/TLKT-BS",
                    "ngay_cap": "27/11/2025",
                    "dia_chi": "thôn A, xã B",
                }
            ],
            "danh_sach_thua_dat": [
                {
                    "so_thua_dat": "65",
                    "so_to_ban_do": "21",
                    "dien_tich": "190 m2",
                    "muc_dich_su_dung": "Đất ở",
                    "thoi_han_su_dung": "Lâu dài",
                    "nguon_goc": "Thừa kế",
                    "so_gcn": "B000020",
                    "loai_gcn": "quyền sử dụng đất",
                    "ngay_cap_gcn": "02/02/1992",
                    "co_quan_cap": "UBND huyện C",
                    "dia_chi": "xã B, huyện C",
                }
            ],
            "tai_san_chua_ho_tro": ["so_tiet_kiem"],
            "missing_web_form_fields": [],
        },
    }


class RegexTestToolTests(unittest.TestCase):
    def test_summarize_counts_people_parcels_and_missing(self):
        summary = summarize(make_payload())

        self.assertIn("inheritance_partition", summary)
        self.assertIn("Người (đầu văn bản): 1", summary)
        self.assertIn("Thửa đất: 1", summary)
        self.assertIn("Chưa hỗ trợ: so_tiet_kiem", summary)

    def test_savings_rows_chi_la_placeholder_chua_ho_tro(self):
        rows = savings_rows(make_payload())

        self.assertEqual(len(rows), 1)
        self.assertIn("chưa bóc dòng", rows[0][2])

    def test_insurance_rows_chi_la_placeholder_chua_ho_tro(self):
        payload = {"raw": {"tai_san_chua_ho_tro": ["bao_hiem"]}}
        rows = insurance_rows(payload)

        self.assertEqual(len(rows), 1)
        self.assertIn("bảo hiểm", rows[0][1])

    def test_person_rows_khong_gom_loi_chung(self):
        payload = make_payload()
        payload["raw"]["loi_chung_nguoi"] = [{"ho_ten": "Trần Văn Z"}]
        rows = person_rows(payload)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "Đầu văn bản")
        self.assertEqual(rows[0][3], "Nguyễn Thị A")

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
            }
        }
        rows = person_rows(payload)

        # Quy uoc noi bo: giu nguyen "1965", khong gan chu thich vao ket qua.
        self.assertEqual(rows[0][4], "1965")

    def test_parcel_rows_follow_parcel_table_order(self):
        rows = parcel_rows(make_payload())

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0][1:],
            ("65", "21", "190 m2", "Đất ở", "Lâu dài", "Thừa kế", "B000020", "quyền sử dụng đất", "02/02/1992", "UBND huyện C", "xã B, huyện C"),
        )

    def test_summarize_reports_error_payload(self):
        summary = summarize({"error": "boom"})

        self.assertIn("boom", summary)

    def test_run_extract_missing_file_returns_error_dict(self):
        payload = run_extract("khong-ton-tai-12345.docx")

        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()

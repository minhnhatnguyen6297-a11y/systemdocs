from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from ket_qua_log import (
    doc_ban_ghi,
    ghi_ban_ghi,
    mo_thu_muc_log,
    payload_thanh_ban_ghi,
    tom_tat_ban_ghi,
)


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
                        "ngay_cap_cccd": "01/01/2021",
                        "dia_chi": "",
                    }
                ]
            },
            "ben_b": {"nguoi": []},
            "nguoi_chet": [],
            "danh_sach_thua_dat": [
                {
                    "so_thua_dat": "65",
                    "so_to_ban_do": "21",
                    "dien_tich": "",
                }
            ],
            "missing_web_form_fields": [],
        },
    }


class KetQuaLogTests(unittest.TestCase):
    def test_ghi_roi_doc_lai_du_ban_ghi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "ket-qua-test.jsonl"
            record = payload_thanh_ban_ghi(make_payload(), r"D:\hop-dong\mau.docx", "test-v1")
            ghi_ban_ghi(record, log_path)
            ghi_ban_ghi(record, log_path)

            records = doc_ban_ghi(log_path)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["engine_version"], "test-v1")
        self.assertEqual(records[0]["ten_file"], "mau.docx")
        self.assertEqual(len(records[0]["nguoi"]), 1)
        self.assertEqual(len(records[0]["thua"]), 1)

    def test_tom_tat_bao_thieu_truong(self):
        summary = tom_tat_ban_ghi(payload_thanh_ban_ghi(make_payload(), "mau.docx", "v1"))

        self.assertIn("Người: 1", summary)
        self.assertIn("THIẾU", summary)

    def test_tom_tat_uu_tien_ma_kiem_tra(self):
        record = payload_thanh_ban_ghi(make_payload(), "mau.docx", "v1")
        record["kiem_tra"] = [{"id": "R03", "muc": "canh-bao", "noi_dung": "thiếu dia_chi: X"}]
        summary = tom_tat_ban_ghi(record)

        self.assertIn("R03", summary)

    def test_tom_tat_bo_qua_file_ngoai_le(self):
        record = payload_thanh_ban_ghi(make_payload(), "mau.docx", "v1")
        record["kiem_tra"] = [{"id": "R00", "muc": "bo-qua", "noi_dung": "bỏ qua"}]

        self.assertIn("BỎ QUA", tom_tat_ban_ghi(record))

    def test_doc_log_thieu_file_ve_rong(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(doc_ban_ghi(Path(tmp) / "khong-co.jsonl"), [])

    def test_mo_thu_muc_log_khong_no_neu_loi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "ket-qua-test.jsonl"
            with patch("os.startfile", side_effect=OSError("no gui")):
                folder = mo_thu_muc_log(log_path)

        self.assertEqual(folder, Path(tmp))

    def test_error_payload_ghi_loi(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "ket-qua-test.jsonl"
            record = payload_thanh_ban_ghi({"error": "hong file"}, "x.docx", "v1")
            ghi_ban_ghi(record, log_path)
            records = doc_ban_ghi(log_path)

        self.assertEqual(records[0]["loi"], "hong file")
        self.assertIn("LỖI", tom_tat_ban_ghi(records[0]))


if __name__ == "__main__":
    unittest.main()

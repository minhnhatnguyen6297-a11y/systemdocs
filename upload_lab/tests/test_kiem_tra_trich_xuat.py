from __future__ import annotations

import unittest

from kiem_tra_trich_xuat import (
    MUC_BO_QUA,
    MUC_CANH_BAO,
    MUC_LOI,
    co_loi,
    kiem_tra_payload,
)


def make_payload(**over) -> dict:
    payload = {
        "raw": {
            "file_goc": r"D:\hop-dong\9. Thoả thuận phân chia thừa kế.docx",
            "document_kind": "inheritance_partition",
            "engine_version": "test",
            "ben_a": {
                "nguoi": [
                    {
                        "gioi_tinh": "Bà",
                        "ho_ten": "Nguyễn Thị A",
                        "ngay_sinh": "01/01/1960",
                        "cccd": "036160000001",
                        "ngay_cap_cccd": "01/01/2021",
                        "dia_chi": "Thôn A, xã B",
                    }
                ],
                "dia_chi": "",
                "entity_lines": [],
            },
            "ben_b": {"nguoi": [], "dia_chi": "", "entity_lines": []},
            "nguoi_chet": [
                {
                    "ho_ten": "Trần Văn X",
                    "ngay_sinh": "1920",
                    "ngay_chet": "11/06/2004",
                    "dia_chi": "Thôn A",
                }
            ],
            "danh_sach_thua_dat": [
                {
                    "so_thua_dat": "65",
                    "dien_tich": "450",
                    "chi_tiet_dien_tich": [
                        {"dien_tich": "200"},
                        {"dien_tich": "250"},
                    ],
                }
            ],
            "missing_web_form_fields": [],
        },
        "web_form": {
            "ten_hop_dong": "VĂN BẢN PHÂN CHIA DI SẢN",
            "tai_san": "Quyền sử dụng đất...",
        },
    }
    payload["raw"].update(over.get("raw", {}))
    payload["web_form"].update(over.get("web_form", {}))
    return payload


class KiemTraTrichXuatTests(unittest.TestCase):
    def test_ban_sach_khong_co_phat_hien(self):
        self.assertEqual(kiem_tra_payload(make_payload()), [])

    def test_file_ngoai_le_thi_bo_qua(self):
        payload = make_payload(raw={"file_goc": r"D:\3. DK18, thuế.docx"})
        findings = kiem_tra_payload(payload)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["muc"], MUC_BO_QUA)

    def test_0_nguoi_la_loi(self):
        payload = make_payload(raw={"ben_a": {"nguoi": []}, "ben_b": {"nguoi": []}})
        findings = kiem_tra_payload(payload)

        self.assertTrue(any(f["id"] == "R02" and f["muc"] == MUC_LOI for f in findings))

    def test_thieu_truong_nguoi_bao_tung_truong(self):
        payload = make_payload()
        payload["raw"]["ben_a"]["nguoi"][0]["dia_chi"] = ""
        findings = kiem_tra_payload(payload)

        self.assertTrue(any(f["id"] == "R03" and "dia_chi" in f["noi_dung"] for f in findings))
        self.assertFalse(co_loi(findings))

    def test_ten_ban_va_trung_ten(self):
        payload = make_payload()
        payload["raw"]["ben_a"]["nguoi"].append(dict(payload["raw"]["ben_a"]["nguoi"][0]))
        payload["raw"]["ben_a"]["nguoi"][0]["ho_ten"] = "Nguyễn Thị A | Sinh ngày"
        findings = kiem_tra_payload(payload)

        self.assertTrue(any(f["id"] == "R04" for f in findings))

    def test_thieu_nguoi_chet_va_mat_tai_san(self):
        payload = make_payload(raw={"nguoi_chet": []}, web_form={"tai_san": ""})
        findings = kiem_tra_payload(payload)
        ids = {f["id"] for f in findings}

        self.assertIn("R06", ids)
        self.assertIn("R08", ids)

    def test_lech_dien_tich_bao_chinh_xac_tuyet_doi(self):
        payload = make_payload()
        payload["raw"]["danh_sach_thua_dat"][0]["chi_tiet_dien_tich"] = [
            {"dien_tich": "200"},
            {"dien_tich": "250,02"},
        ]
        r10 = [f for f in kiem_tra_payload(payload) if f["id"] == "R10"]
        self.assertEqual(len(r10), 1)
        self.assertEqual(r10[0]["muc"], MUC_CANH_BAO)

        payload["raw"]["danh_sach_thua_dat"][0]["chi_tiet_dien_tich"] = [
            {"dien_tich": "200"},
            {"dien_tich": "250"},
        ]
        self.assertFalse([f for f in kiem_tra_payload(payload) if f["id"] == "R10"])

    def test_tai_san_chua_ho_tro_bao_canh_bao(self):
        payload = make_payload()
        payload["raw"]["tai_san_chua_ho_tro"] = ["so_tiet_kiem", "bao_hiem"]
        findings = kiem_tra_payload(payload)

        r12 = [f for f in findings if f["id"] == "R12"]
        self.assertEqual(len(r12), 1)
        self.assertEqual(r12[0]["muc"], MUC_CANH_BAO)


if __name__ == "__main__":
    unittest.main()

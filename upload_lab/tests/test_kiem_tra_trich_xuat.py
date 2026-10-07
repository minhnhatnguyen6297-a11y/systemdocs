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
        payload = make_payload(raw={
            "file_goc": r"D:\3. DK18, thuế.docx",
            "document_kind": "generic",
            "ben_a": {"nguoi": [], "dia_chi": "", "entity_lines": []},
            "ben_b": {"nguoi": [], "dia_chi": "", "entity_lines": []},
            "nguoi_chet": [],
            "danh_sach_thua_dat": [],
        })
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

    def test_lech_dien_tich_bang_gcn_hai_dong_khong_bao(self):
        # sweep33: thua 143 tong 200 "Dat o" lau dai + dong phu "160 Dat vuon"
        # -> phan dat o 40 ngam, chi tiet < tong la hop le (decision-63).
        payload = make_payload()
        thua = payload["raw"]["danh_sach_thua_dat"][0]
        thua["dien_tich"] = "200"
        thua["muc_dich_su_dung"] = "Đất ở"
        thua["chi_tiet_dien_tich"] = [{"dien_tich": "160", "muc_dich_su_dung": "Đất vườn"}]
        self.assertFalse([f for f in kiem_tra_payload(payload) if f["id"] == "R10"])

        thua["chi_tiet_dien_tich"] = [{"dien_tich": "250", "muc_dich_su_dung": "Đất vườn"}]
        self.assertTrue([f for f in kiem_tra_payload(payload) if f["id"] == "R10"])

        thua["muc_dich_su_dung"] = ""
        thua["chi_tiet_dien_tich"] = [{"dien_tich": "160", "muc_dich_su_dung": "Đất vườn"}]
        self.assertTrue([f for f in kiem_tra_payload(payload) if f["id"] == "R10"])

    def test_tai_san_chua_ho_tro_bao_canh_bao(self):
        payload = make_payload()
        payload["raw"]["tai_san_chua_ho_tro"] = ["so_tiet_kiem", "bao_hiem"]
        findings = kiem_tra_payload(payload)

        r12 = [f for f in findings if f["id"] == "R12"]
        self.assertEqual(len(r12), 1)
        self.assertEqual(r12[0]["muc"], MUC_CANH_BAO)

    def test_gioi_tinh_trong_co_canh_bao_r13(self):
        payload = make_payload()
        payload["raw"]["ben_a"]["nguoi"][0]["gioi_tinh"] = ""
        findings = kiem_tra_payload(payload)

        r13 = [f for f in findings if f["id"] == "R13" and "giới tính" in f["noi_dung"]]
        self.assertEqual(len(r13), 1)
        self.assertEqual(r13[0]["muc"], MUC_CANH_BAO)

    def test_dien_tich_mo_ho_co_canh_bao_r13(self):
        payload = make_payload()
        payload["raw"]["danh_sach_thua_dat"][0]["dien_tich"] = "1.234"
        payload["raw"]["danh_sach_thua_dat"][0]["chi_tiet_dien_tich"] = []
        findings = kiem_tra_payload(payload)

        r13 = [f for f in findings if f["id"] == "R13" and "diện tích" in f["noi_dung"]]
        self.assertEqual(len(r13), 1)

    def test_dien_tich_chuan_khong_co_r13(self):
        payload = make_payload()
        findings = kiem_tra_payload(payload)

        self.assertFalse([f for f in findings if f["id"] == "R13"])

    def test_dien_tich_van_xuoi_lot_vao_co_r13(self):
        # Mau that 07/10/2026: "dien tich thua dat neu tren" (khong chu so)
        # cung la du lieu rac, phai co co.
        payload = make_payload()
        payload["raw"]["danh_sach_thua_dat"][0]["dien_tich"] = "thửa đất nêu trên"
        payload["raw"]["danh_sach_thua_dat"][0]["chi_tiet_dien_tich"] = []
        findings = kiem_tra_payload(payload)

        r13 = [f for f in findings if f["id"] == "R13" and "diện tích" in f["noi_dung"]]
        self.assertEqual(len(r13), 1)

    def test_thue_nha_khong_bi_nham_la_thue_thue(self):
        # Sweep 09/10/2026: file "HD THUÊ QSDĐ" (thuê đất) dung "thue" fold
        # giong "thuế" (tax). Co noi dung hop dong -> khong duoc bo qua.
        payload = make_payload(raw={
            "file_goc": r"D:\thue\HD THUÊ QSDĐ.doc",
            "document_kind": "generic",
        })
        findings = kiem_tra_payload(payload)
        self.assertFalse([f for f in findings if f["muc"] == MUC_BO_QUA])

    def test_file_thue_that_van_bo_qua(self):
        # File thue (tax) thuan tuy: khong co nguoi/thua -> van R00.
        payload = make_payload(raw={
            "file_goc": r"D:\soan\4. Thuế ĐẤT PNN.doc",
            "document_kind": "generic",
            "ben_a": {"nguoi": [], "dia_chi": "", "entity_lines": []},
            "ben_b": {"nguoi": [], "dia_chi": "", "entity_lines": []},
            "nguoi_chet": [],
            "danh_sach_thua_dat": [],
        })
        findings = kiem_tra_payload(payload)
        self.assertTrue(any(f["muc"] == MUC_BO_QUA for f in findings))

    def test_0_nguoi_o_loai_da_nhan_dien_la_canh_bao(self):
        # Sweep 09/10/2026: R02 mo rong sang non-generic (chuyen nhuong 0
        # nguoi = warning, khong phai "sach").
        payload = make_payload(raw={
            "document_kind": "transfer_contract",
            "ben_a": {"nguoi": [], "dia_chi": "", "entity_lines": []},
            "ben_b": {"nguoi": [], "dia_chi": "", "entity_lines": []},
        })
        findings = kiem_tra_payload(payload)
        r02 = [f for f in findings if f["id"] == "R02"]
        self.assertEqual(len(r02), 1)
        self.assertEqual(r02[0]["muc"], MUC_CANH_BAO)

    def test_generic_co_tieu_de_0_nguoi_van_co_r02(self):
        # Sweep 09/10/2026 (dot 2): van ban co ten hop dong nhung boc
        # trang nguoi -> canh bao, khong con "sach gia".
        payload = make_payload(raw={
            "document_kind": "generic",
            "ben_a": {"nguoi": [], "dia_chi": "", "entity_lines": []},
            "ben_b": {"nguoi": [], "dia_chi": "", "entity_lines": []},
        })
        findings = kiem_tra_payload(payload)
        r02 = [f for f in findings if f["id"] == "R02"]
        self.assertEqual(len(r02), 1)
        self.assertEqual(r02[0]["muc"], MUC_CANH_BAO)

    def test_generic_khong_tieu_de_0_nguoi_van_sach(self):
        payload = make_payload(web_form={"ten_hop_dong": ""}, raw={
            "document_kind": "generic",
            "ben_a": {"nguoi": [], "dia_chi": "", "entity_lines": []},
            "ben_b": {"nguoi": [], "dia_chi": "", "entity_lines": []},
        })
        findings = kiem_tra_payload(payload)
        self.assertFalse(any(f["id"] == "R02" for f in findings))

    def test_ten_ben_ban_la_cau_co_r04(self):
        # Sweep 09/10/2026: ten ben A/B nuot "CCCD so..." cung la R04.
        payload = make_payload()
        payload["raw"]["ben_a"]["nguoi"][0]["ho_ten"] = "Nguyễn Trường Nam CCCD số 036"
        findings = kiem_tra_payload(payload)
        self.assertTrue(any(f["id"] == "R04" for f in findings))

    def test_so_thua_chua_van_ban_co_r13(self):
        # Sweep 09/10/2026: loi tach thua de "Dien tich:" hoac cau dai
        # lot vao so_thua_dat.
        payload = make_payload()
        payload["raw"]["danh_sach_thua_dat"] = [{
            "so_thua_dat": "Diện tích:",
            "dien_tich": "450",
            "chi_tiet_dien_tich": [],
        }]
        findings = kiem_tra_payload(payload)
        r13 = [f for f in findings if f["id"] == "R13" and "thửa" in f["noi_dung"]]
        self.assertEqual(len(r13), 1)
        self.assertEqual(r13[0]["muc"], MUC_LOI)

    def test_ten_nguoi_chet_la_cau_co_r04(self):
        # Mau that 07/10/2026: cau pha he lot vao ho_ten nguoi chet.
        payload = make_payload()
        payload["raw"]["nguoi_chet"] = [{
            "ho_ten": "Đức và bà Khuâng là vợ chồng hợp pháp từ năm 1935",
            "ngay_chet": "03/03/2010",
        }]
        findings = kiem_tra_payload(payload)

        r04 = [f for f in findings if f["id"] == "R04"]
        self.assertEqual(len(r04), 1)




class OThoR10Tests(unittest.TestCase):
    def test_r10_dem_ca_o_tho(self):
        payload = {
            "raw": {
                "danh_sach_thua_dat": [{
                    "so_thua_dat": "33",
                    "dien_tich": "117,0",
                    "muc_dich_su_dung": "",
                    "chi_tiet_dien_tich": [
                        {"o_tho": ["80", "ONT"]},
                        {"dien_tich": "12", "muc_dich_su_dung": "CLN"},
                        {"dien_tich": "25", "muc_dich_su_dung": "CLN"},
                    ],
                }],
            },
        }
        self.assertFalse([f for f in kiem_tra_payload(payload) if f["id"] == "R10"])


if __name__ == "__main__":
    unittest.main()

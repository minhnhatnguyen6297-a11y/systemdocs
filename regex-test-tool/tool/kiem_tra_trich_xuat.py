"""Luat kiem tra ket qua trich xuat: MA LA CHUAN, khong suy luan.

Moi khi can biet "ban nay co loi gi", chay cac luat duoi day len payload
cua extract_contract.extract(). Ket qua deterministic: cung file luon
ra cung ma loi. LLM/agent chi doc ma loi, khong tu dat ten loi.

Muc do:
- "loi": bat buoc sua code hoac sua van ban; chua xong khong qua.
- "canh-bao": may lam dung theo van ban nhung nguoi can xem lai
  (vi du tong dien tich vênh, loi chung thieu nguoi ky).
- "bo-qua": khong phai van ban dich (mau trang, phieu thue...).

Truong hop acceptable (ghi nhan, khong sua code):
- Loi chung it nguoi hon dau van ban: chap nhan neu chi nguoi dai
  dien ky (owner xac nhan tung dot).
- Dien tich: KHONG lam tron, so sanh tuyet doi chinh xac. So lieu
  trong van ban vech bao nhieu bao bay nhieu (muc canh-bao, nguoi
  kiem tra); epsilon 1e-9 chi tru sai so float cua may.
"""
from __future__ import annotations

import re
from typing import Any

MUC_LOI = "loi"
MUC_CANH_BAO = "canh-bao"
MUC_BO_QUA = "bo-qua"

# Dien tich so sanh TUYET DOI chinh xac (quyet dinh owner 06/10/2026:
# khong lam tron). Epsilon chi de tru sai so float cua may, khong phai
# nguong chap nhan lech.
TOLERANCE_DIEN_TICH_M2 = 1e-9

TEN_FILE_NGOAI_LE = (
    ("mau loi chung", "mẫu lời chứng trắng"),
    ("mau so", "mẫu số"),
    ("dk18", "tờ khai thuế"),
    ("yccc", "phiếu yêu cầu"),
    ("phieu ", "phiếu"),
    ("thue", "thuế"),
    ("to khai", "tờ khai"),
    ("danh muc", "danh mục hồ sơ"),
    ("danh sach", "danh sách"),
)

KIND_THUA_KE = (
    "inheritance_partition",
    "inheritance_refusal",
    "inheritance_declaration",
)

TRUONG_NGUOI_BAT_BUOC = ("ho_ten", "ngay_sinh", "cccd", "ngay_cap_cccd", "dia_chi")
TRUONG_CHET_BAT_BUOC = ("ho_ten", "ngay_sinh", "ngay_chet", "dia_chi_cuoi")
TRUONG_THUA_BAT_BUOC = ("so_thua_dat", "dien_tich")


def _so_thuc(text: Any) -> float | None:
    match = re.match(r"\s*(\d+(?:[.,]\d+)*)", str(text or ""))
    if not match:
        return None
    cleaned = match.group(1)
    if cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")
    try:
        return float(cleaned.replace(",", "."))
    except ValueError:
        return None


def _ten_file_folded(payload: dict) -> str:
    raw = payload.get("raw", {})
    name = str(raw.get("file_goc") or "")
    name = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].lower()
    return name


def _ly_do_ngoai_le(payload: dict) -> str:
    name = _ten_file_folded(payload)
    for key, label in TEN_FILE_NGOAI_LE:
        if key in name:
            return label
    return ""


def _nguoi_1_ben(payload: dict) -> list[dict]:
    raw = payload.get("raw", {})
    return list(raw.get("ben_a", {}).get("nguoi", [])) + list(raw.get("ben_b", {}).get("nguoi", []))


def luat_ngoai_le(payload: dict) -> list[dict]:
    """R00: file khong phai van ban dich thi bo qua, khong cham diem."""
    ly_do = _ly_do_ngoai_le(payload)
    if ly_do:
        return [{"id": "R00", "muc": MUC_BO_QUA, "noi_dung": f"bỏ qua (giống {ly_do})"}]
    return []


def luat_loai_van_ban(payload: dict) -> list[dict]:
    """R01: ten file goi y phan chia nhung engine nhan loai khac."""
    name = _ten_file_folded(payload)
    goi_y = "phan chia" in name or "vbpc" in name or "pc" in name.replace(" ", "")
    kind = str(payload.get("raw", {}).get("document_kind", ""))
    if goi_y and kind not in (*KIND_THUA_KE,):
        return [{"id": "R01", "muc": MUC_CANH_BAO, "noi_dung": f"tên file gợi ý phân chia nhưng nhận diện: {kind}"}]
    return []


def luat_0_nguoi(payload: dict) -> list[dict]:
    """R02: van ban thua ke khong co nguoi nao."""
    kind = str(payload.get("raw", {}).get("document_kind", ""))
    if kind in KIND_THUA_KE and not _nguoi_1_ben(payload):
        return [{"id": "R02", "muc": MUC_LOI, "noi_dung": "0 người tham gia"}]
    return []


def luat_thieu_truong_nguoi(payload: dict) -> list[dict]:
    """R03: nguoi thieu truong bat buoc (ten/ngay sinh/cccd/ngay cap/dia chi)."""
    findings = []
    for field in ("ngay_sinh", "cccd", "ngay_cap_cccd", "dia_chi"):
        thieu = [p.get("ho_ten", "?") for p in _nguoi_1_ben(payload) if not str(p.get(field) or "").strip()]
        if thieu:
            findings.append({
                "id": "R03",
                "muc": MUC_CANH_BAO,
                "noi_dung": f"thiếu {field}: {', '.join(thieu[:3])}" + ("..." if len(thieu) > 3 else ""),
            })
    return findings


def luat_ten_ban(payload: dict) -> list[dict]:
    """R04: ten con rac can le (|, cum ngay sinh lot vao ten)."""
    ban = [
        p.get("ho_ten", "")
        for p in _nguoi_1_ben(payload)
        if "|" in str(p.get("ho_ten", "")) or "Sinh n" in str(p.get("ho_ten", ""))
    ]
    if ban:
        return [{"id": "R04", "muc": MUC_LOI, "noi_dung": f"tên bẩn: {', '.join(ban[:3])}"}]
    return []


def luat_trung_ten(payload: dict) -> list[dict]:
    """R05: 2 nguoi trung ten nhau trong cung van ban."""
    ten = [str(p.get("ho_ten", "")) for p in _nguoi_1_ben(payload)]
    trung = sorted({t for t in ten if t and ten.count(t) > 1})
    if trung:
        return [{"id": "R05", "muc": MUC_CANH_BAO, "noi_dung": f"trùng tên: {', '.join(trung[:3])}"}]
    return []


def luat_thieu_nguoi_chet(payload: dict) -> list[dict]:
    """R06: van ban thua ke khong thay nguoi chet."""
    kind = str(payload.get("raw", {}).get("document_kind", ""))
    if kind in KIND_THUA_KE and not payload.get("raw", {}).get("nguoi_chet"):
        return [{"id": "R06", "muc": MUC_CANH_BAO, "noi_dung": "không thấy người chết"}]
    return []


def luat_thieu_truong_chet(payload: dict) -> list[dict]:
    """R07: nguoi chet thieu truong (ten/ngay sinh/ngay chet/dia chi cuoi)."""
    findings = []
    for field in ("ngay_sinh", "ngay_chet", "dia_chi_cuoi"):
        thieu = [p.get("ho_ten", "?") for p in payload.get("raw", {}).get("nguoi_chet", []) if not str(p.get(field) or "").strip()]
        if thieu:
            findings.append({
                "id": "R07",
                "muc": MUC_CANH_BAO,
                "noi_dung": f"người chết thiếu {field}: {', '.join(thieu[:3])}",
            })
    return findings


def luat_mat_khoi_tai_san(payload: dict) -> list[dict]:
    """R08: van ban thua ke khong co khoi text tai san."""
    kind = str(payload.get("raw", {}).get("document_kind", ""))
    if kind in KIND_THUA_KE and not str(payload.get("web_form", {}).get("tai_san", "")).strip():
        return [{"id": "R08", "muc": MUC_LOI, "noi_dung": "không có khối tài sản"}]
    return []


def luat_khong_tach_tai_san(payload: dict) -> list[dict]:
    """R09: co khoi tai san nhung khong tach duoc thua/so/bh nao."""
    kind = str(payload.get("raw", {}).get("document_kind", ""))
    raw = payload.get("raw", {})
    if kind in KIND_THUA_KE and str(payload.get("web_form", {}).get("tai_san", "")).strip():
        if not raw.get("danh_sach_thua_dat") and not raw.get("danh_sach_so_tiet_kiem") and not raw.get("danh_sach_bao_hiem"):
            return [{"id": "R09", "muc": MUC_LOI, "noi_dung": "không tách được tài sản"}]
    return []


def luat_lech_dien_tich(payload: dict) -> list[dict]:
    """R10: tong chi tiet lech tong thua vuot nguong (mac dinh 1m2)."""
    findings = []
    for thua in payload.get("raw", {}).get("danh_sach_thua_dat", []):
        tong = _so_thuc(thua.get("dien_tich", ""))
        chi_tiet = [_so_thuc(c.get("dien_tich", "")) for c in thua.get("chi_tiet_dien_tich", [])]
        chi_tiet = [v for v in chi_tiet if v is not None]
        if tong is not None and chi_tiet and abs(sum(chi_tiet) - tong) > TOLERANCE_DIEN_TICH_M2:
            findings.append({
                "id": "R10",
                "muc": MUC_CANH_BAO,
                "noi_dung": (
                    f"tổng chi tiết khác tổng thửa {thua.get('so_thua_dat', '?')}: "
                    f"{sum(chi_tiet):g} != {tong:g}"
                ),
            })
    return findings


def luat_loi_chung_khac(payload: dict) -> list[dict]:
    """R11: loi chung it/dong nguoi hon dau van ban (de nguoi kiem tra)."""
    raw = payload.get("raw", {})
    n_dau = len(_nguoi_1_ben(payload))
    n_chung = len(raw.get("loi_chung_nguoi", []))
    if n_chung and n_chung != n_dau:
        return [{
            "id": "R11",
            "muc": MUC_CANH_BAO,
            "noi_dung": f"lời chứng khác đầu văn bản ({n_chung} so với {n_dau})",
        }]
    return []


LUAT = (
    luat_ngoai_le,
    luat_loai_van_ban,
    luat_0_nguoi,
    luat_thieu_truong_nguoi,
    luat_ten_ban,
    luat_trung_ten,
    luat_thieu_nguoi_chet,
    luat_thieu_truong_chet,
    luat_mat_khoi_tai_san,
    luat_khong_tach_tai_san,
    luat_lech_dien_tich,
    luat_loi_chung_khac,
)


def kiem_tra_payload(payload: dict) -> list[dict]:
    """Chay toan bo luat, tra list {id, muc, noi_dung} (bo qua thi dung)."""
    findings: list[dict] = []
    ngoai_le = luat_ngoai_le(payload)
    if ngoai_le:
        return ngoai_le
    for luat in LUAT:
        if luat is luat_ngoai_le:
            continue
        findings.extend(luat(payload))
    return findings


def co_loi(findings: list[dict]) -> bool:
    return any(item.get("muc") == MUC_LOI for item in findings)

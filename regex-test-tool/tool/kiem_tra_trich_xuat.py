"""Luat kiem tra ket qua trich xuat: MA LA CHUAN, khong suy luan.

Moi khi can biet "ban nay co loi gi", chay cac luat duoi day len payload
cua extract_contract.extract(). Ket qua deterministic: cung file luon
ra cung ma loi. LLM/agent chi doc ma loi, khong tu dat ten loi.

Muc do:
- "loi": bat buoc sua code hoac sua van ban; chua xong khong qua.
- "canh-bao": may lam dung theo van ban nhung nguoi can xem lai
  (vi du tong dien tich vênh, co tai san chua ho tro).
- "bo-qua": khong phai van ban dich (mau trang, phieu thue...).

Truong hop acceptable (ghi nhan, khong sua code):
- Dien tich: KHONG lam tron, so sanh tuyet doi chinh xac. So lieu
  trong van ban vech bao nhieu bao bay nhieu (muc canh-bao, nguoi
  kiem tra); epsilon 1e-9 chi tru sai so float cua may.

Quyet dinh Owner 06/10/2026 (decision-46): khong trich/doi chieu loi chung
(bo R11); nguoi chet mang truong person_row (so_giay_to/ngay_cap/noi_cap/
dia_chi); so TK/bao hiem chi gan co "chua ho tro" (R12); khong suy doan
gioi tinh / dien tich mo ho — de trong, giu nguyen van, co canh bao (R13).

Bo sung 07/10/2026 (mau thua ke that ong Thuong): R04 bat ca ten nguoi
chet la cau van (qua 6 tu / co tu viet thuong); R13 bat moi dien tich
co gia tri nhung khong parse duoc thanh so (ke ca van xuoi lot vao).
"""
from __future__ import annotations

import re
import unicodedata
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
    ("ho so luu", "danh mục hồ sơ lưu"),
    ("danh sach", "danh sách"),
    ("11dk", "mẫu đăng ký biến động"),
    ("dk11", "mẫu đăng ký biến động"),
    ("dk 11", "mẫu đăng ký biến động"),
    ("truoc ba", "lệ phí trước bạ"),
    ("tncn", "thuế TNCN"),
    ("thu nhap", "thu nhập cá nhân"),
)

KIND_THUA_KE = (
    "inheritance_partition",
    "inheritance_refusal",
    "inheritance_declaration",
)

TRUONG_NGUOI_BAT_BUOC = ("ho_ten", "ngay_sinh", "cccd", "ngay_cap_cccd", "dia_chi")
TRUONG_CHET_BAT_BUOC = ("ho_ten", "ngay_sinh", "ngay_chet", "dia_chi")
TRUONG_THUA_BAT_BUOC = ("so_thua_dat", "dien_tich")


def _so_thuc(text: Any) -> float | None:
    """Cung quy tac dien tich voi engine: "1.234,5"/"1234,5"/"1234.0" doc
    duoc; chi dau cham voi 3 so le ("1.234") la mo ho -> None."""
    match = re.match(r"\s*(\d+(?:[.,]\d+)*)", str(text or ""))
    if not match:
        return None
    cleaned = match.group(1)
    if "." in cleaned and "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    elif "." in cleaned and len(cleaned.rsplit(".", 1)[1]) == 3:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _fold_name(text: str) -> str:
    """Bo dau + thuong hoa ten file de match key khong dau."""
    folded = unicodedata.normalize("NFD", str(text or ""))
    folded = folded.replace("đ", "d").replace("Đ", "d")
    return "".join(c for c in folded if unicodedata.category(c) != "Mn").lower()


def _ten_file_folded(payload: dict) -> str:
    raw = payload.get("raw", {})
    name = str(raw.get("file_goc") or "")
    name = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return _fold_name(name)


def _ly_do_ngoai_le(payload: dict) -> str:
    # File khong doc duoc chu nao (docx chi chua anh scan, giay to dinh
    # kem chup) — bo qua, khong phai loi engine.
    if payload.get("raw", {}).get("text_rong"):
        return "file kh\u00f4ng c\u00f3 n\u1ed9i dung text"
    name = _ten_file_folded(payload)
    raw_name = str(payload.get("raw", {}).get("file_goc") or "").lower()
    # Tieu de noi dung cung la dau hieu danh muc ("DANH MỤC HỒ SƠ LƯU") —
    # ten file "HS thế chấp.docx" khong bat duoc key ten file.
    title_fold = _fold_name(payload.get("web_form", {}).get("ten_hop_dong") or "")
    if (
        title_fold.startswith(("danh muc", "ho so luu"))
        and not _co_noi_dung_hop_dong(payload)
    ):
        return "danh mục hồ sơ lưu"
    for key, label in TEN_FILE_NGOAI_LE:
        if key not in name:
            continue
        if key == "thue" and "thuê" in raw_name:
            # "thue" bo dau trung "thuê" (thue dat/nha) va ten nguoi "Thuế".
            continue
        if _co_noi_dung_hop_dong(payload):
            # Van ban co noi dung hop dong that thi khong bo qua — ten
            # file co the dat nham (09/10/2026: ap cho moi key, khong
            # chi "thue").
            continue
        return label
    return ""


def _co_noi_dung_hop_dong(payload: dict) -> bool:
    """Van ban co noi dung hop dong that (nguoi/thua) thi khong bo qua —
    ten file co the dung ten nguoi hoac bi dat nham."""
    raw = payload.get("raw", {})
    if str(raw.get("document_kind") or "generic") != "generic":
        return True
    if _nguoi_1_ben(payload) or raw.get("danh_sach_thua_dat"):
        return True
    return False


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
    goi_y = (
        "phan chia" in name
        or "vbpc" in name
        or re.search(r"(?:^|[^a-z0-9])pc(?:[^a-z0-9]|$)", name) is not None
    )
    kind = str(payload.get("raw", {}).get("document_kind", ""))
    if goi_y and kind not in (*KIND_THUA_KE,):
        return [{"id": "R01", "muc": MUC_CANH_BAO, "noi_dung": f"tên file gợi ý phân chia nhưng nhận diện: {kind}"}]
    return []


def luat_0_nguoi(payload: dict) -> list[dict]:
    """R02: van ban da nhan loai nhung khong co nguoi nao — thua ke la loi,
    cac loai hop dong khac (CN/TC/the chap/cam ket) la canh bao; generic
    khong ap (thong bao, don tu co the khong co chu the)."""
    kind = str(payload.get("raw", {}).get("document_kind", ""))
    if _nguoi_1_ben(payload):
        return []
    if kind in KIND_THUA_KE:
        return [{"id": "R02", "muc": MUC_LOI, "noi_dung": "0 người tham gia"}]
    if kind and kind != "generic":
        return [{"id": "R02", "muc": MUC_CANH_BAO, "noi_dung": f"0 người tham gia ({kind})"}]
    if str(payload.get("web_form", {}).get("ten_hop_dong") or "").strip():
        return [{"id": "R02", "muc": MUC_CANH_BAO, "noi_dung": "0 người tham gia (generic có tiêu đề)"}]
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


_TU_DEM_TEN = {"văn", "thị", "đẻ"}


def _ten_la_cau(ten: str) -> bool:
    """Ten la cau van (rac lot vao): qua 6 tu hoac co tu viet thuong —
    ten nguoi Viet moi tu deu viet hoa chu cai dau (tru tu dem
    "văn"/"thị"/"đẻ" doi khi viet thuong trong mau go tat)."""
    tokens = ten.split()
    return (
        not tokens
        or len(tokens) > 6
        or any(not t[0].isupper() and t.lower() not in _TU_DEM_TEN for t in tokens)
    )


_TU_KHOA_TEN_RAC = re.compile(
    r"(?i)(?:\d|cccd|cmnd|c\u0103n c\u01b0\u1edbc|\u0111\u1ecba ch\u1ec9|th\u01b0\u1eddng tr\u00fa|h\u1ed9 kh\u1ea9u"
    r"|chi nh\u00e1nh|v\u0103n ph\u00f2ng|c\u00f4ng ty|ng\u00e2n h\u00e0ng|chi c\u1ee5c|\bubnd\b|b\u1ec7nh vi\u1ec7n"
    # Cum nhan bi ro ("Sinh ngay", "cap ngay") — "Sinh/Nam/Cap" dung mot
    # minh la am tiet ten that ("Phạm Văn Sinh", 10/10/2026).
    r"|sinh\s+ng[\u00e0a]y|sinh\s+n[\u0103a]m|ng\u00e0y\s+sinh|n\u0103m\s+sinh|c\u1ea5p\s+ng[\u00e0a]y)"
)


def _ten_ben_ban(ten: str) -> bool:
    """Ten ben A/B co dau hieu rac: cau van, dung keyword giay to,
    hoac ten to chuc ("Chi nhánh văn phòng...") lot vao."""
    s = str(ten or "")
    return _ten_la_cau(s) or bool(_TU_KHOA_TEN_RAC.search(s))


def luat_ten_ban(payload: dict) -> list[dict]:
    """R04: ten con rac can le (|, cum ngay sinh, cau van, ten to chuc)."""
    ban = [
        p.get("ho_ten", "")
        for p in _nguoi_1_ben(payload)
        if _ten_ben_ban(str(p.get("ho_ten", "")))
    ]
    ban += [
        p.get("ho_ten", "")
        for p in payload.get("raw", {}).get("nguoi_chet", [])
        if _ten_la_cau(str(p.get("ho_ten", "")))
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
    for field in ("ngay_sinh", "ngay_chet", "dia_chi"):
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
        if not raw.get("danh_sach_thua_dat") and not raw.get("tai_san_chua_ho_tro"):
            return [{"id": "R09", "muc": MUC_LOI, "noi_dung": "không tách được tài sản"}]
    return []


def _dien_tich_mo_ho(text: Any) -> bool:
    """Dien tich khong rong nhung khong parse duoc thanh so — gom ca text van
    xuoi lot vao ("thua dat neu tren") lan so mo ho ("1.234")."""
    s = str(text or "").strip()
    return bool(s) and _so_thuc(s) is None


def luat_du_lieu_mo_ho(payload: dict) -> list[dict]:
    """R13: truong de trong/nhiem rac vi thieu can cu phai co co de nguoi kiem.

    - gioi_tinh trong: danh xung mo ho ("Ong/ba:") hoac khong suy duoc.
    - dien_tich co gia tri nhung khong parse duoc: giu nguyen van, khong doan so
      ("1.234" chi co dau cham; "dien tich thua dat neu tren" la van xuoi).
    """
    findings = []
    trong_gt = [p.get("ho_ten", "?") for p in _nguoi_1_ben(payload) if not str(p.get("gioi_tinh") or "").strip()]
    if trong_gt:
        findings.append({
            "id": "R13",
            "muc": MUC_CANH_BAO,
            "noi_dung": f"giới tính để trống (không suy đoán): {', '.join(trong_gt[:3])}" + ("..." if len(trong_gt) > 3 else ""),
        })
    mo_ho = []
    thua_rac = []
    for thua in payload.get("raw", {}).get("danh_sach_thua_dat", []):
        label = f"thửa {thua.get('so_thua_dat') or '?'}"
        if _dien_tich_mo_ho(thua.get("dien_tich")):
            mo_ho.append(label)
        elif any(_dien_tich_mo_ho(c.get("dien_tich")) for c in thua.get("chi_tiet_dien_tich", [])):
            mo_ho.append(label)
        # So thua phai la ky hieu ngan ("143", "68/T1") — chuoi dai co
        # ":" hoac khong co chu so la text van xuoi lot vao (loi tach).
        so_thua = str(thua.get("so_thua_dat") or "").strip()
        if so_thua and (":" in so_thua or len(so_thua) > 15 or not re.search(r"\d", so_thua)):
            thua_rac.append(so_thua[:30])
    if mo_ho:
        findings.append({
            "id": "R13",
            "muc": MUC_CANH_BAO,
            "noi_dung": f"diện tích mơ hồ (giữ nguyên văn): {', '.join(mo_ho[:3])}" + ("..." if len(mo_ho) > 3 else ""),
        })
    if thua_rac:
        findings.append({
            "id": "R13",
            "muc": MUC_LOI,
            "noi_dung": f"số thửa đất nghi rác (text văn xuôi): {', '.join(thua_rac[:3])}" + ("..." if len(thua_rac) > 3 else ""),
        })
    return findings


def luat_tai_san_chua_ho_tro(payload: dict) -> list[dict]:
    """R12: co so tiet kiem/bao hiem nhung tam dung boc dong (decision-46)."""
    kinds = payload.get("raw", {}).get("tai_san_chua_ho_tro") or []
    if kinds:
        ten = {"so_tiet_kiem": "sổ tiết kiệm", "bao_hiem": "bảo hiểm"}
        return [{
            "id": "R12",
            "muc": MUC_CANH_BAO,
            "noi_dung": "tài sản chưa hỗ trợ (không bóc dòng): "
                        + ", ".join(ten.get(k, k) for k in kinds),
        }]
    return []


def luat_lech_dien_tich(payload: dict) -> list[dict]:
    """R10: tong chi tiet khac tong thua (so sanh tuyet doi, epsilon float)."""
    findings = []
    for thua in payload.get("raw", {}).get("danh_sach_thua_dat", []):
        tong = _so_thuc(thua.get("dien_tich", ""))
        chi_tiet = [_so_thuc(c.get("dien_tich", "")) for c in thua.get("chi_tiet_dien_tich", [])]
        chi_tiet = [v for v in chi_tiet if v is not None]
        tong_chi_tiet = sum(chi_tiet)
        # bang GCN 2 dong: dong chinh ghi muc dich chinh (VD "Dat o"), dong phu
        # chi ghi phan dien tich con lai (VD "160 Dat vuon") -> chi tiet < tong
        # la hop le, phan du ngam la muc dich chinh (decision-63, 11/10/2026).
        lech_du = tong_chi_tiet - tong if tong is not None else 0
        muc_dich_chinh = (thua.get("muc_dich_su_dung") or "").strip()
        if (
            tong is not None
            and chi_tiet
            and abs(tong_chi_tiet - tong) > TOLERANCE_DIEN_TICH_M2
            and (lech_du > 0 or not muc_dich_chinh)
        ):
            findings.append({
                "id": "R10",
                "muc": MUC_CANH_BAO,
                "noi_dung": (
                    f"tổng chi tiết khác tổng thửa {thua.get('so_thua_dat', '?')}: "
                    f"{sum(chi_tiet):g} != {tong:g}"
                ),
            })
    return findings


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
    luat_du_lieu_mo_ho,
    luat_tai_san_chua_ho_tro,
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

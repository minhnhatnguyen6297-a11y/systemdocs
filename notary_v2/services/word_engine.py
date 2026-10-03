from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any


HIDDEN_BUILTIN_TEMPLATE_NAMES = {
    "system_placeholder_reference.docx",
    "system_template_chuan_v1.docx",
}


ROLE_LABELS = {
    "chu_dat": "chủ đất",
    "vo_chong": "vợ/chồng",
    "cha": "cha",
    "me": "mẹ",
    "cha_vo_chong": "cha vợ/chồng",
    "me_vo_chong": "mẹ vợ/chồng",
    "con": "con",
    "anh_chi_em": "anh/chị/em",
    "chau": "cháu",
    "vo_chong_nhanh": "vợ/chồng nhánh",
}

MAX_WORD_ASSETS = 5
MAX_WORD_LAND_ROWS = 20


class WordExportValidationError(Exception):
    """Lỗi nghiệp vụ khi dữ liệu không đủ để xuất Word đúng."""


@dataclass
class WordPerson:
    id: Any = None
    ho_ten: str = ""
    gioi_tinh: str = ""
    ngay_sinh: Any = None
    ngay_chet: Any = None
    so_giay_to: str = ""
    loai_giay_to: str = ""
    ngay_cap: Any = None
    noi_cap: str = ""
    dia_chi: str = ""
    loai_dia_chi: str = ""
    role: str = ""
    relation: str = ""
    share: str = ""
    will_receive: bool = False
    is_land_owner: bool = False
    is_in_diagram: bool = True
    is_hidden: bool = False
    is_deleted: bool = False

    @property
    def is_deceased(self) -> bool:
        return bool(self.ngay_chet)

    @property
    def is_alive(self) -> bool:
        return not self.is_deceased

    @property
    def gender_normalized(self) -> str:
        raw = _normalize_token(self.gioi_tinh)
        if raw in {"nam", "nam"}:
            return "nam"
        if raw in {"nu", "nữ", "nu"}:
            return "nữ"
        return ""

    @property
    def address_label(self) -> str:
        return _safe_text(self.loai_dia_chi) or "Địa chỉ"


@dataclass
class WordExportContext:
    case: Any
    today: date
    persons: list[WordPerson]
    assets: list[Any]
    all_people: list[WordPerson]
    landowners: list[WordPerson]
    living_landowners: list[WordPerson]
    deceased_landowners: list[WordPerson]
    receivers: list[WordPerson]
    legal_refusal_people: list[WordPerson]


def _fmt_date(d: Any) -> str:
    if not d:
        return ""
    if isinstance(d, str):
        return d
    return d.strftime("%d/%m/%Y")


def _fmt_snapshot_date(value: Any) -> str:
    """Ngày trong snapshot payload.case (ISO 'YYYY-MM-DD' hoặc năm
    'YYYY' — `_emit_date_or_year`) → dd/mm/YYYY cho placeholder Word."""
    text = _safe_text(value)
    if not text:
        return ""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
    return text


def _fmt_birth_or_year(d: Any) -> str:
    if not d:
        return ""
    if isinstance(d, str):
        return d
    if getattr(d, "day", None) == 1 and getattr(d, "month", None) == 1:
        return str(d.year)
    return _fmt_date(d)


def _safe_text(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return value != 0
    normalized = _normalize_token(str(value))
    if normalized in {"1", "true", "yes", "co"}:
        return True
    if normalized in {"0", "false", "no", "khong", ""}:
        return False
    return default


def _so_thanh_chu(so: float) -> str:
    try:
        so = float(so)
    except (TypeError, ValueError):
        return ""

    don_vi = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def _doc_ba_chu_so(n: int) -> str:
        tram = n // 100
        chuc = (n % 100) // 10
        dv = n % 10
        result = ""
        if tram:
            result += don_vi[tram] + " trăm"
            if chuc == 0 and dv:
                result += " linh " + don_vi[dv]
            elif chuc:
                result += " " + (don_vi[chuc] + " mươi" if chuc > 1 else "mườ")
                if dv == 1 and chuc > 1:
                    result += " mốt"
                elif dv == 5 and chuc > 0:
                    result += " lăm"
                elif dv:
                    result += " " + don_vi[dv]
        elif chuc:
            result += don_vi[chuc] + " mươi" if chuc > 1 else "mườ"
            if dv == 1 and chuc > 1:
                result += " mốt"
            elif dv == 5 and chuc > 0:
                result += " lăm"
            elif dv:
                result += " " + don_vi[dv]
        elif dv:
            result += don_vi[dv]
        return result.strip()

    phan_nguyen = int(so)
    phan_le_str = ""
    if so != phan_nguyen:
        le = round(so - phan_nguyen, 6)
        dec_s = f"{le:.6f}".split(".")[1].rstrip("0")
        if dec_s:
            phan_le_str = " phẩy " + " ".join(don_vi[int(d)] for d in dec_s)

    if phan_nguyen == 0:
        return ("không" + phan_le_str).strip()

    parts = []
    n = phan_nguyen
    ty = n // 1_000_000_000
    n %= 1_000_000_000
    tr = n // 1_000_000
    n %= 1_000_000
    ng = n // 1_000
    n %= 1_000

    if ty:
        parts.append(_doc_ba_chu_so(ty) + " tỷ")
    if tr:
        parts.append(_doc_ba_chu_so(tr) + " triệu")
    if ng:
        parts.append(_doc_ba_chu_so(ng) + " nghìn")
    if n:
        parts.append(_doc_ba_chu_so(n))

    return (" ".join(parts) + phan_le_str).strip()


def _normalize_token(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("đ", "d")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s


def _role_key(role: str) -> str:
    normalized = _normalize_token(role)
    normalized = normalized.replace("/", " ").replace("_", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if normalized in {"owner", "chu dat"}:
        return "chu_dat"
    if normalized in {"vo chong"}:
        return "vo_chong"
    if normalized == "cha":
        return "cha"
    if normalized in {"me", "me"}:
        return "me"
    if normalized in {"cha vc", "cha vo chong"}:
        return "cha_vo_chong"
    if normalized in {"me vc", "me vo chong"}:
        return "me_vo_chong"
    if normalized == "con":
        return "con"
    if normalized in {"anh chi em"}:
        return "anh_chi_em"
    if normalized in {"chau"}:
        return "chau"
    if normalized in {"con dau re", "vo chong nhanh"}:
        return "vo_chong_nhanh"
    return normalized.replace(" ", "_")


def _display_document_type(raw: str) -> str:
    raw = _safe_text(raw)
    if raw == "thoa_thuan":
        return "Thỏa thuận phân chia di sản"
    if raw == "khai_nhan":
        return "Văn bản khai nhận di sản thừa kế"
    return raw


def _format_share(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return ""
    if number.is_integer():
        return str(int(number))
    return f"{number:g}"


def _pick_core_people(case: Any) -> tuple[Any, Any, Any, list[Any]]:
    owner = getattr(case, "nguoi_chet", None)
    spouse = None
    for p in getattr(case, "participants", []) or []:
        if _role_key(getattr(p, "vai_tro", "")) == "vo_chong":
            spouse = getattr(p, "customer", None)
            break

    pair = [c for c in [owner, spouse] if c is not None]
    nam = [c for c in pair if _normalize_token(getattr(c, "gioi_tinh", "")) == "nam"]
    nu = [c for c in pair if _normalize_token(getattr(c, "gioi_tinh", "")) in {"nu", "nữ"}]

    if len(nam) == 1 and len(nu) == 1:
        person1 = nam[0]
        person2 = nu[0]
    elif len(pair) == 2:
        person1 = pair[0]
        person2 = pair[1]
    elif len(pair) == 1:
        person1 = pair[0]
        person2 = None
    else:
        person1 = None
        person2 = None

    excluded_ids = {getattr(c, "id", None) for c in [person1, person2] if c is not None}
    receivers = [
        p for p in getattr(case, "participants", []) or []
        if getattr(p, "co_nhan_tai_san", False) and getattr(p, "customer_id", None) not in excluded_ids
    ]
    receivers = sorted(receivers, key=lambda p: (-(getattr(p, "ty_le", 0) or 0), getattr(p, "customer_id", 0) or 0))
    non_receivers = [
        p for p in getattr(case, "participants", []) or []
        if not getattr(p, "co_nhan_tai_san", False) and getattr(p, "customer_id", None) not in excluded_ids
    ]
    non_receivers = sorted(non_receivers, key=lambda p: getattr(p, "customer_id", 0) or 0)

    person3 = getattr(receivers[0], "customer", None) if receivers else None
    people_4_plus = [p.customer for p in receivers[1:]] + [p.customer for p in non_receivers]
    return person1, person2, person3, people_4_plus


def _parse_land_rows(raw: str) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        rows = json.loads(raw)
    except Exception:
        return []
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _fmt_area(v: Any) -> str:
    """Diện tích → text; số nguyên bỏ phần thập phân thừa (80.0 → '80')."""
    if v is None or v == "" or isinstance(v, bool):
        return ""
    if isinstance(v, (int, float)):
        return f"{v:g}"
    return _safe_text(v)


def _land_row_values(row: Any) -> tuple[str, str, str]:
    """Một cụm đất → (loai_dat, dien_tich, thoi_han) dạng text.

    Đọc được dict snapshot/JSON — key canonical loaidat/dientich/thoihan
    hoặc key wire legacy loai_dat/dien_tich/thoi_han (kể cả lỗi chính tả
    'dien_tích' của data cũ) — và object bảng con PropertyLandRow."""
    if not row:
        return "", "", ""
    if isinstance(row, dict):
        loai = row.get("loaidat")
        if loai is None:
            loai = row.get("loai_dat")
        area = row.get("dientich")
        if area is None:
            area = row.get("dien_tích", row.get("dien_tich"))
        term = row.get("thoihan")
        if term is None:
            term = row.get("thoi_han")
    else:
        loai = getattr(row, "loaidat", getattr(row, "loai_dat", ""))
        area = getattr(row, "dientich", getattr(row, "dien_tich", ""))
        term = getattr(row, "thoihan", getattr(row, "thoi_han", ""))
    return _safe_text(loai), _fmt_area(area), _safe_text(term)


def _norm_land_dict(row: Any) -> dict[str, str]:
    loai, area, term = _land_row_values(row)
    return {"loai_dat": loai, "dien_tich": area, "thoi_han": term}


def _committed_land_rows(prop: Any) -> list[dict[str, str]]:
    """Cụm đất đã commit của một asset view → list dict đã normalize
    {loai_dat, dien_tich, thoi_han}. Nguồn theo thứ tự: `.land_rows`
    (bảng con ORM / snapshot view) → `land_rows_json` legacy → [].
    KHÔNG fallback trường lẻ — dùng _land_rows_for khi cần pseudo-row."""
    if prop is None:
        return []
    rows = getattr(prop, "land_rows", None)
    if rows:
        return [_norm_land_dict(r) for r in rows]
    parsed = _parse_land_rows(_safe_text(getattr(prop, "land_rows_json", "")))
    return [_norm_land_dict(r) for r in parsed]


def _land_rows_for(prop: Any) -> list[dict[str, str]]:
    """Cụm đất để render: committed rows, hoặc pseudo-row từ trường tổng
    hợp loai_dat/dien_tich khi chưa có cụm nào.

    Thời hạn lẻ (properties.thoi_han) KHÔNG được đắp vào cụm — thời hạn
    thuộc từng cụm (MIN-141 đợt 2); dữ liệu cũ chỉ có thời hạn lẻ được
    workspace_get báo orphan_thoi_han để đối chiếu, không tự đoán."""
    rows = _committed_land_rows(prop)
    if rows:
        return rows
    return [{
        "loai_dat": _safe_text(getattr(prop, "loai_dat", "")),
        "dien_tich": _fmt_area(getattr(prop, "dien_tich", "")),
        "thoi_han": "",
    }]


# ---------------------------------------------------------------------------
# Word export V2: case_state_json-aware helpers
# ---------------------------------------------------------------------------


def _load_case_state(case: Any) -> dict[str, Any]:
    raw = _safe_text(getattr(case, "case_state_json", ""))
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _word_person_from_stage(stage_person: dict[str, Any]) -> WordPerson:
    return WordPerson(
        id=_safe_text(stage_person.get("id")),
        ho_ten=_safe_text(stage_person.get("ho_ten")),
        gioi_tinh=_safe_text(stage_person.get("gioi_tinh")),
        ngay_sinh=stage_person.get("ngay_sinh") or None,
        ngay_chet=stage_person.get("ngay_chet") or None,
        so_giay_to=_safe_text(stage_person.get("so_giay_to")),
        loai_giay_to=_safe_text(stage_person.get("loai_giay_to")),
        ngay_cap=stage_person.get("ngay_cap") or None,
        noi_cap=_safe_text(stage_person.get("noi_cap")),
        dia_chi=_safe_text(stage_person.get("dia_chi")),
        loai_dia_chi=_safe_text(stage_person.get("loai_dia_chi", stage_person.get("place_of_origin"))),
    )


def _word_person_from_customer(customer: Any) -> WordPerson:
    return WordPerson(
        id=getattr(customer, "id", None),
        ho_ten=_safe_text(getattr(customer, "ho_ten", "")),
        gioi_tinh=_safe_text(getattr(customer, "gioi_tinh", "")),
        ngay_sinh=getattr(customer, "ngay_sinh", None),
        ngay_chet=getattr(customer, "ngay_chet", None),
        so_giay_to=_safe_text(getattr(customer, "so_giay_to", "")),
        loai_giay_to=_safe_text(getattr(customer, "loai_giay_to", "")),
        ngay_cap=getattr(customer, "ngay_cap", None),
        noi_cap=_safe_text(getattr(customer, "noi_cap", "")),
        dia_chi=_safe_text(getattr(customer, "dia_chi", "")),
        loai_dia_chi=_safe_text(getattr(customer, "loai_dia_chi", "")),
    )


def _apply_diagram_nodes(
    persons: list[WordPerson],
    nodes: list[dict[str, Any]],
    allocations: dict[str, Any] | None = None,
) -> list[WordPerson]:
    if not nodes:
        return persons
    for person in persons:
        person.is_in_diagram = False
    by_id = {str(p.id): p for p in persons if p.id is not None}
    ordered: list[WordPerson] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        person_id = _safe_text(node.get("personId") or (node.get("person") or {}).get("id"))
        if not person_id or person_id not in by_id:
            continue
        p = by_id[person_id]
        allocation = (allocations or {}).get(person_id, {})
        if not isinstance(allocation, dict):
            allocation = {}
        p.is_in_diagram = True
        p.role = _safe_text(node.get("role")) or p.role
        p.relation = _safe_text(node.get("relationLabel")) or p.relation
        p.share = _safe_text(
            allocation.get("finalShare")
            or node.get("finalShare")
            or node.get("share")
            or node.get("sharePercent")
        )
        legacy_decision = _safe_text(node.get("inheritanceDecision"))
        p.will_receive = _coerce_bool(node.get("willReceive"), legacy_decision == "accept")
        p.is_land_owner = _coerce_bool(node.get("isLandOwner"), False)
        p.is_hidden = _coerce_bool(node.get("hidden"), False)
        p.is_deleted = _coerce_bool(node.get("deleted"), False)
        if p not in ordered:
            ordered.append(p)
    ordered.extend(person for person in persons if person not in ordered)
    return ordered


def _build_word_persons(case: Any) -> list[WordPerson]:
    state = _load_case_state(case)
    has_state = bool(state)
    stage = state.get("stage", []) if has_state else []
    diagram = state.get("diagram", {}) if has_state and isinstance(state.get("diagram"), dict) else {}
    engine_input = diagram.get("engineInput", {}) if isinstance(diagram.get("engineInput"), dict) else {}
    legacy_engine_state = diagram.get("engineState", {}) if isinstance(diagram.get("engineState"), dict) else {}
    engine_result = diagram.get("engineResult", {}) if isinstance(diagram.get("engineResult"), dict) else {}
    node_source = engine_input if isinstance(engine_input.get("nodes"), list) else legacy_engine_state
    nodes = node_source.get("nodes", []) if isinstance(node_source.get("nodes"), list) else []
    allocations = engine_result.get("allocations", {})
    if not isinstance(allocations, dict):
        allocations = {}

    persons: list[WordPerson] = []
    owner = getattr(case, "nguoi_chet", None)

    if has_state and isinstance(stage, list):
        for item in stage:
            if isinstance(item, dict):
                persons.append(_word_person_from_stage(item))

    # Đảm bảo ngườ chết của hồ sơ luôn có mặt trong danh sách để xử lý chủ đất.
    if owner is not None:
        owner_id = str(getattr(owner, "id", ""))
        existing = next((p for p in persons if str(p.id) == owner_id), None)
        if existing is None:
            owner_wp = _word_person_from_customer(owner)
            owner_wp.is_land_owner = True
            persons.append(owner_wp)
        else:
            existing.is_land_owner = True

    if has_state:
        persons = _apply_diagram_nodes(persons, nodes, allocations)

    # Fallback về participants cũ khi không có case_state_json hợp lệ.
    if not has_state:
        for participant in getattr(case, "participants", []) or []:
            customer = getattr(participant, "customer", None)
            if customer is None:
                continue
            wp = _word_person_from_customer(customer)
            wp.role = _safe_text(getattr(participant, "vai_tro", ""))
            wp.will_receive = bool(getattr(participant, "co_nhan_tai_san", False))
            wp.share = _format_share(getattr(participant, "ty_le", ""))
            persons.append(wp)

    deduped: list[WordPerson] = []
    seen_ids: set[str] = set()
    for person in persons:
        person_id = str(person.id)
        if person_id in seen_ids:
            continue
        seen_ids.add(person_id)
        deduped.append(person)
    return deduped


def _active_persons(persons: list[WordPerson]) -> list[WordPerson]:
    return [p for p in persons if p.is_in_diagram and not p.is_hidden and not p.is_deleted]


def _children(persons: list[WordPerson]) -> list[WordPerson]:
    return [p for p in _active_persons(persons) if _role_key(p.role) == "con"]


def build_word_context(case: Any, today: date | None = None) -> WordExportContext:
    persons = _build_word_persons(case)
    all_people = _active_persons(persons)
    landowners = [person for person in all_people if person.is_land_owner]
    receivers = [person for person in all_people if person.will_receive]
    return WordExportContext(
        case=case,
        today=today or date.today(),
        persons=persons,
        assets=_get_property_list(case),
        all_people=all_people,
        landowners=landowners,
        living_landowners=[person for person in landowners if person.is_alive],
        deceased_landowners=[person for person in landowners if person.is_deceased],
        receivers=receivers,
        # Diagram has no legally confirmed refusal input. Compatibility
        # placeholders therefore stay empty instead of inferring a refusal.
        legal_refusal_people=[],
    )


def _spouses_of(persons: list[WordPerson], target: WordPerson) -> list[WordPerson]:
    return [p for p in _active_persons(persons) if _role_key(p.role) == "vo_chong" and p.id != target.id]


def _title_for_person(person: WordPerson) -> str:
    if person.gender_normalized == "nam":
        return "ông"
    if person.gender_normalized == "nữ":
        return "bà"
    return "ông/bà"


def _format_name_list(people: list[WordPerson]) -> str:
    if not people:
        return ""
    parts = [f"{_title_for_person(p)} {p.ho_ten}".strip() for p in people if p.ho_ten]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} và {parts[1]}"
    return ", ".join(parts[:-1]) + f" và {parts[-1]}"


def _format_simple_name_list(people: list[WordPerson]) -> str:
    if not people:
        return ""
    names = [p.ho_ten for p in people if p.ho_ten]
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} và {names[1]}"
    return ", ".join(names[:-1]) + f" và {names[-1]}"


def _relation_for_person(person: WordPerson) -> str:
    if person.relation:
        return person.relation
    role_key = _role_key(person.role)
    return ROLE_LABELS.get(role_key, _safe_text(person.role))


def _status_for_person(context: WordExportContext, person: WordPerson) -> str:
    person_id = str(person.id)
    if any(str(item.id) == person_id for item in context.receivers):
        return "Người nhận"
    if any(str(item.id) == person_id for item in context.deceased_landowners):
        return "Chủ đất chết"
    if any(str(item.id) == person_id for item in context.living_landowners):
        return "Chủ đất sống"
    return "Người không nhận"


def _person_placeholder_values(context: WordExportContext, person: WordPerson | None) -> dict[str, str]:
    if person is None:
        return {
            "Xưng hô": "",
            "Họ tên": "",
            "Giới tính": "",
            "Ngày sinh": "",
            "Năm sinh": "",
            "Ngày chết": "",
            "Năm chết": "",
            "Loại giấy tờ": "",
            "Số giấy tờ": "",
            "Ngày cấp": "",
            "Nơi cấp": "",
            "Nhãn địa chỉ": "",
            "Địa chỉ": "",
            "Quan hệ": "",
            "Vai trò": "",
            "Trạng thái": "",
            "Tỷ lệ": "",
        }
    return {
        "Xưng hô": _title_for_person(person),
        "Họ tên": person.ho_ten,
        "Giới tính": person.gioi_tinh,
        "Ngày sinh": _fmt_date(person.ngay_sinh),
        "Năm sinh": _fmt_birth_or_year(person.ngay_sinh),
        "Ngày chết": _fmt_date(person.ngay_chet),
        "Năm chết": _fmt_birth_or_year(person.ngay_chet),
        "Loại giấy tờ": person.loai_giay_to,
        "Số giấy tờ": person.so_giay_to,
        "Ngày cấp": _fmt_date(person.ngay_cap),
        "Nơi cấp": person.noi_cap,
        "Nhãn địa chỉ": person.address_label,
        "Địa chỉ": person.dia_chi,
        "Quan hệ": _relation_for_person(person),
        "Vai trò": person.role,
        "Trạng thái": _status_for_person(context, person),
        "Tỷ lệ": person.share,
    }


def _person_detail_block(index: int, person: WordPerson, *, refused: bool = False) -> str:
    lines = [f"{index}. {_title_for_person(person)} {person.ho_ten}".strip()]
    if person.ngay_sinh:
        lines[0] += f"; Sinh ngày: {_fmt_birth_or_year(person.ngay_sinh)}"
    lines[0] += "."

    document_parts = []
    if person.loai_giay_to:
        document_parts.append(person.loai_giay_to)
    if person.so_giay_to:
        document_parts.append(f"số: {person.so_giay_to}")
    document_line = " ".join(document_parts)
    if person.noi_cap:
        document_line += f" do {person.noi_cap} cấp"
    if person.ngay_cap:
        document_line += f" ngày {_fmt_date(person.ngay_cap)}"
    if document_line:
        lines.append(document_line + ".")

    if person.dia_chi:
        lines.append(f"{person.address_label}: {person.dia_chi}.")
    relation = _relation_for_person(person)
    if relation:
        lines.append(f"Là {relation}.")
    if refused:
        lines.append(
            f"{_title_for_person(person).capitalize()} {person.ho_ten} đã từ chối di sản theo Văn bản "
            "từ chối nhận di sản số ......................... ."
        )
    return "\n".join(lines)


def _add_word_person_group(
    mapping: dict[str, str],
    context: WordExportContext,
    group_name: str,
    people: list[WordPerson],
    *,
    limit: int = 20,
) -> None:
    group_alias = group_name.lower()
    for index in range(1, limit + 1):
        person = people[index - 1] if index <= len(people) else None
        values = _person_placeholder_values(context, person)
        for field, value in values.items():
            mapping[f"[{group_name} {index} - {field}]"] = value
            mapping[f"[{field} {group_alias} {index}]"] = value
        if group_name == "Hàng thừa kế":
            note = _combined_heir_note(context, person) if person else ""
            mapping[f"[Hàng thừa kế {index} - Ghi chú]"] = note
            mapping[f"[Ghi chú hàng thừa kế {index}]"] = note

        block = ""
        inline = ""
        if person is not None:
            block = _person_detail_block(index, person, refused=group_name == "Người từ chối")
            inline_name = f"{_title_for_person(person)} {person.ho_ten}".strip()
            if index == 1:
                inline = inline_name
            elif index == len(people):
                inline = f" và {inline_name}"
            else:
                inline = f", {inline_name}"
        mapping[f"[Dòng {group_alias} {index}]"] = block
        mapping[f"[{group_name} inline {index}]"] = inline

    mapping[f"[Danh sách {group_alias} inline]"] = _format_name_list(people)
    mapping[f"[Danh sách {group_alias}]"] = _format_simple_name_list(people)


def _deceased_landowner_clauses(people: list[WordPerson]) -> str:
    """Dòng khai tử chủ đất chết — ghép từ field đã commit của người
    (MIN-141 đợt 3): loại giấy tờ/nơi cấp lấy bằng chứng xác nhận trong
    snapshot; phần nào chưa có thì lược bỏ, KHÔNG gán cứng "Trích lục
    khai tử (Bản sao)" hay suy tên UBND xã."""
    lines = []
    for p in people:
        title = _title_for_person(p)
        born = _fmt_birth_or_year(p.ngay_sinh)
        died = _fmt_date(p.ngay_chet)
        doc_no = _safe_text(p.so_giay_to)
        doc_type = _safe_text(p.loai_giay_to)
        issuer = _safe_text(p.noi_cap)
        issued = _fmt_date(p.ngay_cap)
        address = _safe_text(p.dia_chi)
        line = f"{title} {p.ho_ten}"
        if born:
            line += f"; Sinh năm: {born}"
        line += f"; chết ngày {died}"
        if doc_type or doc_no or issuer or issued:
            tail = " theo"
            tail += f" {doc_type}" if doc_type else " giấy tờ khai tử"
            if doc_no:
                tail += f" số {doc_no}"
            if issuer:
                tail += f" do {issuer}"
            if issued:
                tail += f" ký ngày {issued}"
            line += tail
        line += "."
        if address:
            line += f" Nơi chết: {address}."
        lines.append(line)
    return "\n".join(lines)


def _family_relation_clauses(
    deceased_landowners: list[WordPerson],
    persons: list[WordPerson],
    legal_refusal_people: list[WordPerson],
) -> str:
    paragraphs = []
    refused_ids = {str(person.id) for person in legal_refusal_people}
    for owner in deceased_landowners:
        title = _title_for_person(owner)
        spouses = _spouses_of(persons, owner)
        if spouses:
            spouse = spouses[0]
            spouse_title = _title_for_person(spouse)
            paragraphs.append(f"{title} {owner.ho_ten} có vợ/chồng là {spouse_title} {spouse.ho_ten}.")
        children = _children(persons)
        if children:
            child_lines = []
            for child in children:
                if str(child.id) in refused_ids:
                    child_lines.append(
                        f"{child.ho_ten} đã từ chối di sản theo Văn bản từ chối nhận di sản số ......................... ."
                    )
                else:
                    child_lines.append(child.ho_ten)
            child_text = "; ".join(child_lines)
            paragraphs.append(f"{title} {owner.ho_ten} có {len(children)} ngườ con là: {child_text}.")
    return "\n".join(paragraphs)


_SNAPSHOT_ASSET_META_KEYS = {"id", "entity_id", "row_id", "is_primary"}


def _safe_int(v: Any) -> int | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _snapshot_asset_fields(item: Any) -> bool:
    """Snapshot asset đợt 2 trở đi mang full field + land_rows canonical;
    snapshot cũ chỉ có {id, entity_id, row_id, is_primary} → fieldless."""
    return isinstance(item, dict) and any(
        key not in _SNAPSHOT_ASSET_META_KEYS for key in item)


def _snapshot_asset_view(item: dict[str, Any]) -> Any:
    """Asset snapshot trong case_state_json → view giống ORM Property cho
    các hàm placeholder (MIN-141 đợt 2 — Word đọc đúng bản đã commit của
    hồ sơ, không đổi theo master properties của hồ sơ khác).

    `land_rows` giữ nguyên dict canonical (loaidat/dientich/thoihan) —
    _land_row_values đọc được cả hai spelling; `land_rows_json` = None vì
    snapshot đã là nguồn committed."""
    ngay_cap = item.get("ngay_cap")
    if isinstance(ngay_cap, str) and ngay_cap:
        try:
            ngay_cap = date.fromisoformat(ngay_cap[:10])
        except ValueError:
            pass  # giữ chuỗi gốc — _fmt_date pass-through chuỗi
    entity_id = item.get("entity_id")
    return SimpleNamespace(
        id=entity_id if isinstance(entity_id, int)
            else _safe_int(item.get("id")),
        entity_id=entity_id,
        so_serial=item.get("so_serial"),
        so_vao_so=item.get("so_vao_so"),
        so_thua_dat=item.get("so_thua_dat"),
        so_to_ban_do=item.get("so_to_ban_do"),
        dia_chi=item.get("dia_chi"),
        loai_so=item.get("loai_so"),
        hinh_thuc_su_dung=item.get("hinh_thuc_su_dung"),
        thoi_han=item.get("thoi_han"),
        nguon_goc=item.get("nguon_goc"),
        ngay_cap=ngay_cap,
        co_quan_cap=item.get("co_quan_cap"),
        loai_dat=item.get("loai_dat"),
        dien_tich=item.get("dien_tich"),
        land_rows=(item.get("land_rows")
                   if isinstance(item.get("land_rows"), list) else []),
        land_rows_json=None,
    )


def _snap_date_value(value: Any) -> Any:
    """Ngày trong snapshot person (ISO 'YYYY-MM-DD' hoặc năm 'YYYY') →
    `date` để _fmt_date/_fmt_birth_or_year render đồng nhất với đường
    master. Không parse được → giữ chuỗi gốc (pass-through)."""
    if not isinstance(value, str) or not value:
        return value
    text = value.strip()
    try:
        if re.fullmatch(r"\d{4}", text):
            return date(int(text), 1, 1)
        return date.fromisoformat(text[:10])
    except ValueError:
        return value


def _snapshot_person_view(customer: Any, row: dict) -> Any:
    """View Người cho slot `[Tên N]`…`[noicapN]` — đọc bằng chứng đã
    commit trong snapshot `stage[]` của chính hồ sơ thay vì master
    `customers` live (MIN-141 review: master dùng chung có thể bị hồ sơ
    khác đổi sau commit; vd loai_giay_to/ngay_cap của người chết model
    trả None nên đường live làm mất 'Giấy chứng tử' đã xác nhận).

    Per-key presence như `_snap_meta`: key có trong snapshot → dùng giá
    trị snapshot (kể cả null chủ ý → rỗng); key vắng (snapshot cũ) →
    fallback master live."""

    def pick(key: str) -> Any:
        return row[key] if key in row else getattr(customer, key, None)

    return SimpleNamespace(
        id=getattr(customer, "id", None),
        ho_ten=_safe_text(pick("ho_ten")),
        gioi_tinh=_safe_text(pick("gioi_tinh")),
        ngay_sinh=_snap_date_value(pick("ngay_sinh")),
        ngay_chet=_snap_date_value(pick("ngay_chet")),
        so_giay_to=_safe_text(pick("so_giay_to")),
        ngay_cap=_snap_date_value(pick("ngay_cap")),
        noi_cap=_safe_text(pick("noi_cap")),
        dia_chi=_safe_text(pick("dia_chi")),
        loai_giay_to=_safe_text(pick("loai_giay_to")),
        loai_dia_chi=_safe_text(pick("loai_dia_chi")),
    )


def _snapshot_people_by_id(state: dict[str, Any]) -> dict[str, dict]:
    """{entity_id str → row} từ snapshot `stage[]` — đối chiếu slot
    Người legacy (Customer live) với bản đã commit của hồ sơ."""
    out: dict[str, dict] = {}
    stage = state.get("stage") if isinstance(state, dict) else None
    for item in stage or []:
        if isinstance(item, dict) and item.get("id") is not None:
            out[str(item.get("id"))] = item
    return out


def _live_props_by_id(case: Any) -> dict[int, Any]:
    """{property_id: Property live} — fallback cho snapshot item chỉ có
    pointer (payload trước đợt 2)."""
    out: dict[int, Any] = {}
    for link in getattr(case, "property_links", None) or []:
        prop = getattr(link, "property", None)
        pid = getattr(link, "property_id", None)
        if prop is not None and isinstance(pid, int):
            out[pid] = prop
    ts = getattr(case, "tai_san", None)
    ts_id = getattr(ts, "id", None)
    if ts is not None and isinstance(ts_id, int):
        out.setdefault(ts_id, ts)
    return out


def _get_property_list(case: Any) -> list[Any]:
    """Tài sản để render — snapshot đã commit trong case_state_json trước
    (MIN-141 đợt 2): mỗi hồ sơ xuất đúng bản commit của mình, kể cả khi
    master properties bị hồ sơ khác dùng chung sửa. Item snapshot chỉ có
    pointer (payload cũ) → tra master live theo entity_id; không có
    snapshot assets → đường live cũ (links/tai_san)."""
    snap_assets = _load_case_state(case).get("assets")
    if isinstance(snap_assets, list) and snap_assets:
        live = _live_props_by_id(case)
        views = []
        for item in snap_assets:
            if _snapshot_asset_fields(item):
                views.append(_snapshot_asset_view(item))
                continue
            pid = None
            if isinstance(item, dict):
                pid = item.get("entity_id")
                if not isinstance(pid, int) or isinstance(pid, bool):
                    pid = _safe_int(item.get("id"))
            prop = live.get(pid) if isinstance(pid, int) else None
            if prop is not None:
                views.append(prop)
        if views:
            return views
    links = getattr(case, "property_links", None)
    if links:
        ordered = sorted(links, key=lambda x: (not bool(getattr(x, "is_primary", False)), getattr(x, "id", 0)))
        props = [getattr(link, "property", None) for link in ordered]
        props = [p for p in props if p is not None]
        if props:
            return props
    ts = getattr(case, "tai_san", None)
    if ts is not None:
        return [ts]
    return []


def _property_description(properties: list[Any]) -> str:
    if not properties:
        return ""
    paragraphs = ["Các quyền sử dụng đất như sau:"] if len(properties) > 1 else []
    for idx, prop in enumerate(properties, start=1):
        loai_so = _safe_text(getattr(prop, "loai_so", "")) or "Giấy chứng nhận quyền sử dụng đất"
        serial = _safe_text(getattr(prop, "so_serial", ""))
        so_vao_so = _safe_text(getattr(prop, "so_vao_so", ""))
        so_thua = _safe_text(getattr(prop, "so_thua_dat", ""))
        so_to = _safe_text(getattr(prop, "so_to_ban_do", ""))
        dia_chi = _safe_text(getattr(prop, "dia_chi", ""))
        co_quan_cap = _safe_text(getattr(prop, "co_quan_cap", ""))
        ngay_cap = _fmt_date(getattr(prop, "ngay_cap", None))

        header = f"{idx}. Quyền sử dụng đất tại: {dia_chi} theo {loai_so} số: {serial}; Số vào sổ cấp GCN: {so_vao_so} do {co_quan_cap} cấp ngày {ngay_cap}."
        paragraphs.append(header)

        detail = f"Thửa đất số: {so_thua}, tờ bản đồ số: {so_to}."
        paragraphs.append(detail)

        land_rows = _land_rows_for(prop)

        total_area = 0.0
        for row in land_rows:
            try:
                total_area += float(row.get("dien_tich") or 0)
            except (TypeError, ValueError):
                pass
        area_str = f"{total_area:g}" if total_area else _safe_text(getattr(prop, "dien_tich", ""))
        paragraphs.append(f"Diện tích: {area_str} m2")
        paragraphs.append(f"Hình thức sử dụng: {_safe_text(getattr(prop, 'hinh_thuc_su_dung', ''))}")

        land_type_lines = []
        for m_idx, row in enumerate(land_rows, start=1):
            loai_dat = _safe_text(row.get("loai_dat", ""))
            dien_tich = _safe_text(row.get("dien_tich", ""))
            thoi_han = _safe_text(row.get("thoi_han", ""))
            if not loai_dat and not dien_tich:
                continue
            land_type_lines.append(f"{idx}.{m_idx}. {loai_dat}: {dien_tich} m2 ({thoi_han})")
        if land_type_lines:
            paragraphs.append("\n".join(land_type_lines))

        paragraphs.append(f"Thời hạn sử dụng: {_safe_text(getattr(prop, 'thoi_han', ''))}")
        paragraphs.append(f"Nguồn gốc sử dụng đất: {_safe_text(getattr(prop, 'nguon_goc', ''))}.")
    return "\n".join(paragraphs)


def _division_clause(context: WordExportContext) -> str:
    if not context.receivers:
        raise WordExportValidationError("Không có người nhận để xuất văn bản phân chia.")

    deceased_names = _format_name_list(context.deceased_landowners)
    receiver_names = _format_name_list(context.receivers)
    simple_receiver_names = _format_simple_name_list(context.receivers)
    paragraphs = [
        f"Chúng tôi gồm: {receiver_names} thống nhất phân chia di sản của "
        f"{deceased_names} như sau:"
    ]
    paragraphs.append(
        f"{simple_receiver_names} đồng ý nhận phần di sản theo nội dung thỏa thuận "
        "phân chia di sản thừa kế ở trên."
    )
    return "\n".join(paragraphs)


def _heir_note(context: WordExportContext, person: WordPerson) -> str:
    return _status_for_person(context, person)


def _role_note(person: WordPerson) -> str:
    role = _role_key(person.role)
    if role == "vo_chong":
        if person.gender_normalized == "nam":
            return "Là chồng"
        return "Là vợ"
    if role == "con":
        return "Là con"
    return ""


def _combined_heir_note(context: WordExportContext, person: WordPerson) -> str:
    parts = [p for p in [_role_note(person), _heir_note(context, person)] if p]
    return "; ".join(parts)


def word_block_reason(context: WordExportContext) -> str | None:
    """Contract `word.*` block_reason đầu tiên cho một context đã build.

    Cùng thứ tự kiểm tra với `_add_block_placeholders` bên dưới (contract
    notary.case-drafting.v2 §13.10 mapping). Trả None khi dữ liệu đủ để xuất.
    Dùng bởi `services.word_batch_export` cho word_export_options +
    per-document failure của word_export_batch (MIN-110)."""
    if not context.assets:
        return "word.no_assets"
    if len(context.assets) > MAX_WORD_ASSETS:
        return "word.too_many_assets"
    if not context.landowners:
        return "word.no_landowner"
    if not context.deceased_landowners:
        return "word.no_deceased_landowner"
    if not context.receivers:
        return "word.no_receiver"
    if len(context.all_people) > 20:
        return "word.too_many_people"
    signers: list[WordPerson] = []
    signer_ids: set[str] = set()
    for person in [*context.living_landowners, *context.receivers]:
        if str(person.id) not in signer_ids:
            signers.append(person)
            signer_ids.add(str(person.id))
    if len(signers) > 20:
        return "word.too_many_signers"
    return None


def _add_block_placeholders(mapping: dict[str, str], context: WordExportContext) -> None:
    if not context.assets:
        raise WordExportValidationError("Không có tài sản để xuất Word.")
    if len(context.assets) > MAX_WORD_ASSETS:
        raise WordExportValidationError(
            f"Vượt quá {MAX_WORD_ASSETS} tài sản (hiện có {len(context.assets)}). "
            "Vui lòng giảm số lượng tài sản trước khi xuất Word."
        )
    if not context.landowners:
        raise WordExportValidationError("Không xác định được chủ đất trên Diagram.")
    if not context.deceased_landowners:
        raise WordExportValidationError("Không xác định được chủ đất đã chết để xuất văn bản.")
    if not context.receivers:
        raise WordExportValidationError("Không có người nhận để xuất văn bản phân chia.")
    if len(context.all_people) > 20:
        raise WordExportValidationError(
            f"Danh sách trên Diagram vượt quá 20 người (hiện có {len(context.all_people)})."
        )

    heir_rows = [person for person in context.all_people if not person.is_land_owner]
    groups = {
        "Người": context.all_people,
        "Chủ đất sống": context.living_landowners,
        "Chủ đất chết": context.deceased_landowners,
        "Người nhận": context.receivers,
        "Người từ chối": context.legal_refusal_people,
        "Hàng thừa kế": heir_rows,
    }
    for group_name, people in groups.items():
        _add_word_person_group(mapping, context, group_name, people)

    deceased_cluster = _format_name_list(context.deceased_landowners)
    mapping["[Cụm chủ đất chết]"] = deceased_cluster
    mapping["[Cụm người để lại di sản]"] = deceased_cluster
    mapping["[Cụm ngườ để lại di sản]"] = deceased_cluster
    for index in range(1, 3):
        person = context.deceased_landowners[index - 1] if index <= len(context.deceased_landowners) else None
        opening = f"{_title_for_person(person)} {person.ho_ten}".strip() if person else ""
        mapping[f"[Chủ đất chết mở đầu {index}]"] = opening
        mapping[f"[Dòng khai tử chủ đất chết {index}]"] = (
            _deceased_landowner_clauses([person]) if person else ""
        )
        mapping[f"[Cụm ngày chết chủ đất chết {index}]"] = (
            f"; Chết ngày: {_fmt_date(person.ngay_chet)}" if person and person.ngay_chet else ""
        )
    mapping["[Nối chủ đất chết 2]"] = " và " if len(context.deceased_landowners) >= 2 else ""
    mapping["[Cụm UBND niêm yết]"] = f"UBND xã {mapping.get('[Niêm Yết]', '')}".strip()

    for index in range(1, 21):
        mapping[f"[Dòng chủ đất sống tặng cho {index}]"] = ""

    # Alias cũ: không còn nhóm "chưa chọn", giá trị chỉ còn người nhận.
    mapping["[Danh sách người nhận và chưa chọn]"] = _format_name_list(context.receivers)
    mapping["[Danh sách ngườ nhận và chưa chọn]"] = mapping["[Danh sách người nhận và chưa chọn]"]

    mapping["[Đoạn người chết là chủ đất]"] = _deceased_landowner_clauses(context.deceased_landowners)
    mapping["[Đoạn ngườ chết là chủ đất]"] = mapping["[Đoạn người chết là chủ đất]"]

    mapping["[Đoạn quan hệ gia đình]"] = _family_relation_clauses(
        context.deceased_landowners,
        context.all_people,
        context.legal_refusal_people,
    )

    mapping["[Đoạn mô tả di sản]"] = _property_description(context.assets)
    mapping["[Đoạn phân chia di sản]"] = _division_clause(context)

    signers: list[WordPerson] = []
    signer_ids: set[str] = set()
    for person in [*context.living_landowners, *context.receivers]:
        if str(person.id) not in signer_ids:
            signers.append(person)
            signer_ids.add(str(person.id))
    mapping["[Danh sách người ký]"] = _format_simple_name_list(signers)
    mapping["[Danh sách ngườ ký]"] = mapping["[Danh sách người ký]"]
    mapping["[Danh sách hàng thừa kế]"] = _format_simple_name_list(heir_rows)

    for idx in range(1, 21):
        if idx <= len(heir_rows):
            p = heir_rows[idx - 1]
            mapping[f"[STT hàng thừa kế {idx}]"] = str(idx)
            mapping[f"[Họ tên hàng thừa kế {idx}]"] = p.ho_ten
            mapping[f"[Ngày sinh hàng thừa kế {idx}]"] = _fmt_birth_or_year(p.ngay_sinh)
            mapping[f"[Năm sinh hàng thừa kế {idx}]"] = _fmt_birth_or_year(p.ngay_sinh)
            mapping[f"[Địa chỉ hàng thừa kế {idx}]"] = p.dia_chi
            mapping[f"[Ghi chú hàng thừa kế {idx}]"] = _combined_heir_note(context, p)
            mapping[f"[Dòng hàng thừa kế {idx}]"] = (
                f"{idx}. {p.ho_ten} - {_fmt_birth_or_year(p.ngay_sinh)} - {p.dia_chi} - "
                f"{_combined_heir_note(context, p)}"
            ).strip(" -")
        else:
            mapping[f"[STT hàng thừa kế {idx}]"] = ""
            mapping[f"[Họ tên hàng thừa kế {idx}]"] = ""
            mapping[f"[Ngày sinh hàng thừa kế {idx}]"] = ""
            mapping[f"[Năm sinh hàng thừa kế {idx}]"] = ""
            mapping[f"[Địa chỉ hàng thừa kế {idx}]"] = ""
            mapping[f"[Ghi chú hàng thừa kế {idx}]"] = ""
            mapping[f"[Dòng hàng thừa kế {idx}]"] = ""

    if len(signers) > 20:
        raise WordExportValidationError(
            f"Danh sách người ký vượt quá 20 người (hiện có {len(signers)})."
        )
    for idx in range(1, 21):
        if idx <= len(signers):
            mapping[f"[Họ tên người ký {idx}]"] = signers[idx - 1].ho_ten
        else:
            mapping[f"[Họ tên người ký {idx}]"] = ""
        mapping[f"[Họ tên ngườ ký {idx}]"] = mapping[f"[Họ tên người ký {idx}]"]


def _add_property_placeholders(mapping: dict[str, str], properties: list[Any]) -> None:
    asset_fields = {
        "Địa chỉ": "Địa chỉ đất",
        "Loại sổ": "Loại sổ",
        "Serial": "Serial",
        "Số vào sổ": "Số vào sổ",
        "Số thửa": "Số thửa",
        "Số tờ": "Số tờ",
        "Diện tích": "Diện tích",
        "Hình thức sử dụng": "Hình thức sử dụng",
        "Mục đích sử dụng": "Mục đích sử dụng",
        "Thời hạn": "Thời hạn",
        "Nguồn gốc": "Nguồn gốc",
        "Ngày cấp sổ": "Ngày cấp sổ",
        "Cơ quan cấp sổ": "Cơ quan cấp sổ",
    }

    for idx in range(1, MAX_WORD_ASSETS + 1):
        prop = properties[idx - 1] if idx <= len(properties) else None
        land_rows: list[dict[str, Any]] = []
        values = {field: "" for field in asset_fields}
        if prop is not None:
            land_rows = _land_rows_for(prop)
            total_area = 0.0
            for row in land_rows:
                try:
                    total_area += float(row.get("dien_tich") or 0)
                except (TypeError, ValueError):
                    pass
            area_str = f"{total_area:g}" if total_area else _safe_text(getattr(prop, "dien_tich", ""))
            purpose = "; ".join(
                f"{_safe_text(row.get('loai_dat'))}: {_safe_text(row.get('dien_tich'))} m2"
                for row in land_rows
                if _safe_text(row.get("loai_dat")) or _safe_text(row.get("dien_tich"))
            )
            values = {
                "Địa chỉ": _safe_text(getattr(prop, "dia_chi", "")),
                "Loại sổ": _safe_text(getattr(prop, "loai_so", "")) or "Giấy chứng nhận quyền sử dụng đất",
                "Serial": _safe_text(getattr(prop, "so_serial", "")),
                "Số vào sổ": _safe_text(getattr(prop, "so_vao_so", "")),
                "Số thửa": _safe_text(getattr(prop, "so_thua_dat", "")),
                "Số tờ": _safe_text(getattr(prop, "so_to_ban_do", "")),
                "Diện tích": area_str,
                "Hình thức sử dụng": _safe_text(getattr(prop, "hinh_thuc_su_dung", "")),
                "Mục đích sử dụng": purpose,
                "Thời hạn": _safe_text(getattr(prop, "thoi_han", "")),
                "Nguồn gốc": _safe_text(getattr(prop, "nguon_goc", "")),
                "Ngày cấp sổ": _fmt_date(getattr(prop, "ngay_cap", None)),
                "Cơ quan cấp sổ": _safe_text(getattr(prop, "co_quan_cap", "")),
            }

        for field, legacy_name in asset_fields.items():
            value = values[field]
            mapping[f"[Tài sản {idx} - {field}]"] = value
            mapping[f"[{legacy_name} {idx}]"] = value
            mapping[f"[{legacy_name} tài sản {idx}]"] = value
            if idx == 1:
                mapping[f"[Tài sản - {field}]"] = value

        if prop is None:
            mapping[f"[Dòng tài sản {idx}]"] = ""
            mapping[f"[Dòng thửa đất {idx}]"] = ""
            mapping[f"[Dòng diện tích {idx}]"] = ""
            mapping[f"[Dòng hình thức sử dụng {idx}]"] = ""
            mapping[f"[Dòng mục đích sử dụng {idx}]"] = ""
            mapping[f"[Dòng thời hạn {idx}]"] = ""
            mapping[f"[Dòng nguồn gốc {idx}]"] = ""
        else:
            mapping[f"[Dòng tài sản {idx}]"] = (
                f"{idx}. Quyền sử dụng đất tại: {values['Địa chỉ']} theo {values['Loại sổ']} số: "
                f"{values['Serial']}; Số vào sổ cấp GCN: {values['Số vào sổ']} do "
                f"{values['Cơ quan cấp sổ']} cấp ngày {values['Ngày cấp sổ']}."
            )
            mapping[f"[Dòng thửa đất {idx}]"] = (
                f"Thửa đất số: {values['Số thửa']}, tờ bản đồ số: {values['Số tờ']}."
            )
            mapping[f"[Dòng diện tích {idx}]"] = f"Diện tích: {values['Diện tích']} m2."
            mapping[f"[Dòng hình thức sử dụng {idx}]"] = (
                f"Hình thức sử dụng: {values['Hình thức sử dụng']}."
            )
            mapping[f"[Dòng mục đích sử dụng {idx}]"] = (
                f"Mục đích sử dụng: {values['Mục đích sử dụng']}."
            )
            mapping[f"[Dòng thời hạn {idx}]"] = f"Thời hạn sử dụng: {values['Thời hạn']}."
            mapping[f"[Dòng nguồn gốc {idx}]"] = (
                f"Nguồn gốc sử dụng đất: {values['Nguồn gốc']}."
            )

        for line_name in ("thửa đất", "diện tích", "hình thức sử dụng", "mục đích sử dụng", "thời hạn", "nguồn gốc"):
            canonical = f"[Dòng {line_name} {idx}]"
            mapping[f"[Dòng {line_name} tài sản {idx}]"] = mapping[canonical]

        for m_idx in range(1, 11):
            row = land_rows[m_idx - 1] if m_idx <= len(land_rows) else None
            land_type, area, term = _land_row_values(row)
            mapping[f"[Loại đất {idx}.{m_idx} - Loại đất]"] = land_type
            mapping[f"[Loại đất {idx}.{m_idx} - Diện tích]"] = area
            mapping[f"[Loại đất {idx}.{m_idx} - Thời hạn]"] = term
            mapping[f"[Loại đất tài sản {idx}.{m_idx}]"] = land_type
            mapping[f"[Diện tích loại đất tài sản {idx}.{m_idx}]"] = area
            mapping[f"[Thời hạn loại đất tài sản {idx}.{m_idx}]"] = term
            mapping[f"[Thờ hạn loại đất tài sản {idx}.{m_idx}]"] = term
            mapping[f"[Dòng loại đất {idx}.{m_idx}]"] = (
                f"{idx}.{m_idx}. {land_type}: {area} m2; Thời hạn: {term}." if row else ""
            )
            mapping[f"[Dòng loại đất tài sản {idx}.{m_idx}]"] = mapping[f"[Dòng loại đất {idx}.{m_idx}]"]

        # Tên chuẩn (contracts/entities.md §9.2): [trường][loại đất M][tài sản N],
        # viết liền không dấu, không "_". Không sinh alias rút gọn [loaidatM].
        for m_idx in range(1, MAX_WORD_LAND_ROWS + 1):
            row = land_rows[m_idx - 1] if m_idx <= len(land_rows) else None
            land_type, area, term = _land_row_values(row)
            mapping[f"[loaidat{m_idx}{idx}]"] = land_type
            mapping[f"[dientich{m_idx}{idx}]"] = area
            mapping[f"[thoihan{m_idx}{idx}]"] = term


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_template_mapping(case: Any, today: date | None = None) -> dict[str, str]:
    context = build_word_context(case, today=today)
    # Tài sản vị trí 1 (primary) — snapshot đã commit nếu có, không thì
    # master live case.tai_san (đường cũ, hồ sơ chưa qua commit_stage).
    ts = context.assets[0] if context.assets else getattr(case, "tai_san", None)
    today = context.today
    person1, person2, person3, people_4_plus = _pick_core_people(case)

    people_slots = [None] * 21
    people_slots[1] = person1
    people_slots[2] = person2
    people_slots[3] = person3
    for idx, c in enumerate(people_4_plus[:17], start=4):
        people_slots[idx] = c

    # Metadata hồ sơ (MIN-141 đợt 3): snapshot `payload.case` đã commit
    # là nguồn đọc chính — cột live chỉ fallback khi snapshot KHÔNG có
    # key (hồ sơ legacy chưa qua commit_stage sau khi nâng cấp). Key đã
    # commit mà null/rỗng là giá trị chủ ý → xuất rỗng, không đọc master.
    # `[Nơi niêm yết]` KHÔNG còn đắp từ địa chỉ đất: chưa tra cứu được →
    # để trống, không tự khẳng định.
    _state_doc = _load_case_state(case)
    snap_case = _state_doc.get("case")
    if not isinstance(snap_case, dict):
        # Phòng snapshot lồng `payload.case` (một số doc legacy/wire).
        _inner = _state_doc.get("payload")
        snap_case = (_inner.get("case") if isinstance(_inner, dict)
                     else None)
    snap_case = snap_case if isinstance(snap_case, dict) else {}

    def _snap_meta(key: str, live_attr: str) -> str:
        if key in snap_case:
            return _safe_text(snap_case.get(key))
        return _safe_text(getattr(case, live_attr, ""))

    noi_niem_yet = _snap_meta("noiniemyet", "noi_niem_yet")
    noi_dung_viec = _snap_meta("noidungviec", "noi_dung_viec")
    ghi_chu = _snap_meta("ghichu", "ghi_chu")
    if "nguoinhanuyquyen" in snap_case:
        _uq_snap = snap_case.get("nguoinhanuyquyen")
        nguoi_nhan_uy_quyen = (
            _safe_text(_uq_snap.get("ten"))
            if isinstance(_uq_snap, dict) else _safe_text(_uq_snap))
    else:
        nguoi_nhan_uy_quyen = _safe_text(
            getattr(case, "nguoi_nhan_uy_quyen", ""))
    ngay_lap_ho_so = (
        _fmt_snapshot_date(snap_case.get("ngaylaphoso"))
        if "ngaylaphoso" in snap_case
        else _fmt_date(getattr(case, "ngay_lap_ho_so", None)))
    land_rows = _committed_land_rows(ts)
    if land_rows:
        total = 0.0
        for row in land_rows:
            try:
                total += float(row.get("dien_tich") or 0)
            except (TypeError, ValueError):
                pass
        dien_tich_so = total if total > 0 else getattr(ts, "dien_tich", None)
    else:
        dien_tich_so = getattr(ts, "dien_tich", None)
    dien_tich_str = f"{dien_tich_so:g}" if dien_tich_so else ""
    dien_tich_chu = _so_thanh_chu(dien_tich_so).capitalize() if dien_tich_so else ""
    loai_so_val = _safe_text(getattr(ts, "loai_so", "")) or "Giấy chứng nhận quyền sử dụng đất"
    loai_van_ban = _display_document_type(getattr(case, "loai_van_ban", ""))

    mapping: dict[str, str] = {
        "[Tên file]": f"ho_so_thua_ke_{getattr(case, 'id', '')}",
        "[Loại văn bản]": loai_van_ban,
        "[documenttype]": loai_van_ban,
        "[Ngày lập hồ sơ]": ngay_lap_ho_so,
        "[ngaylaphoso]": ngay_lap_ho_so,
        "[Nơi niêm yết]": noi_niem_yet,
        "[noiniemyet]": noi_niem_yet,
        "[Ghi chú]": ghi_chu,
        "[ghichu]": ghi_chu,
        "[Niêm Yết]": noi_niem_yet,
        "[NIÊM YẾT]": noi_niem_yet.upper() if noi_niem_yet else "",
        "[Loại sổ]": loai_so_val,
        "[Địa chỉ đất]": _safe_text(getattr(ts, "dia_chi", "")),
        "[Số serial]": _safe_text(getattr(ts, "so_serial", "")),
        "[Serial]": _safe_text(getattr(ts, "so_serial", "")),
        "[Số vào sổ]": _safe_text(getattr(ts, "so_vao_so", "")),
        "[Số thửa]": _safe_text(getattr(ts, "so_thua_dat", "")),
        "[Số tờ]": _safe_text(getattr(ts, "so_to_ban_do", "")),
        "[Số tờ bản đồ]": _safe_text(getattr(ts, "so_to_ban_do", "")),
        "[Diện tích]": dien_tich_str,
        "[Diện tích chữ]": dien_tich_chu,
        "[Hình thức sử dụng]": _safe_text(getattr(ts, "hinh_thuc_su_dung", "")),
        "[Loại đất]": _safe_text(getattr(ts, "loai_dat", "")),
        "[Thờ hạn]": _safe_text(getattr(ts, "thoi_han", "")),
        "[Nguồn gốc]": _safe_text(getattr(ts, "nguon_goc", "")),
        "[Ngày cấp sổ]": _fmt_date(getattr(ts, "ngay_cap", None)),
        "[Cơ quan cấp sổ]": _safe_text(getattr(ts, "co_quan_cap", "")),
        "[Ngày]": str(today.day),
        "[Tháng]": f"{today.month:02d}",
        "[Ngày chữ]": _so_thanh_chu(today.day),
        "[Tháng chữ]": _so_thanh_chu(today.month),
        "[Ngườ ủy quyền]": nguoi_nhan_uy_quyen,
        "[Ngườ ủy quyền2]": nguoi_nhan_uy_quyen,
        "[nguoinhanuyquyen]": nguoi_nhan_uy_quyen,
        "[Nội dung việc]": noi_dung_viec,
        "[noidungviec]": noi_dung_viec,
        "[Số công chứng]": "",
        "[ONT]": "",
        "[CLN]": "",
        "[NTS]": "",
        "[LUC]": "",
        "[Giá chuyển nhượng]": "",
        "[SĐT]": "",
    }

    # Slot Người: thứ tự giữ nguyên legacy (_pick_core_people trên
    # participants live), nhưng FIELD đọc bằng chứng đã commit trong
    # snapshot stage[] — đối chiếu theo entity id (MIN-141 review:
    # master customers dùng chung đổi sau commit không được kéo giá trị
    # slot đi; người chết có bằng chứng 'Giấy chứng tử' không bị model
    # trả None xóa mất). Snapshot cũ thiếu key → fallback master.
    _snap_people = _snapshot_people_by_id(_state_doc)

    def _slot_person(c):
        if c is None:
            return None
        row = _snap_people.get(str(getattr(c, "id", "")))
        return _snapshot_person_view(c, row) if row is not None else c

    for i in range(1, 21):
        c = _slot_person(people_slots[i])
        mapping[f"[Tên {i}]"] = _safe_text(getattr(c, "ho_ten", "") if c else "")
        mapping[f"[Năm sinh {i}]"] = _fmt_birth_or_year(getattr(c, "ngay_sinh", None) if c else None)
        mapping[f"[CCCD {i}]"] = _safe_text(getattr(c, "so_giay_to", "") if c else "")
        mapping[f"[Ngày cấp {i}]"] = _fmt_date(getattr(c, "ngay_cap", None) if c else None)
        mapping[f"[Địa chỉ {i}]"] = _safe_text(getattr(c, "dia_chi", "") if c else "")
        mapping[f"[Loại CC {i}]"] = _safe_text(getattr(c, "loai_giay_to", "") if c else "")
        mapping[f"[Nơi cấp CC {i}]"] = _safe_text(getattr(c, "noi_cap", "") if c else "")
        mapping[f"[Thường trú {i}]"] = _safe_text(getattr(c, "loai_dia_chi", "") if c else "")
        mapping[f"[Năm chết {i}]"] = _fmt_date(getattr(c, "ngay_chet", None) if c else None)
        # Tên chuẩn Người — viết liền không dấu không "_" (entities.md
        # §9.1): mirror đúng giá trị alias tiếng Việt cũ ở trên.
        mapping[f"[ten{i}]"] = mapping[f"[Tên {i}]"]
        mapping[f"[gioitinh{i}]"] = _safe_text(getattr(c, "gioi_tinh", "") if c else "")
        mapping[f"[ngaysinh{i}]"] = mapping[f"[Năm sinh {i}]"]
        mapping[f"[ngaychet{i}]"] = mapping[f"[Năm chết {i}]"]
        mapping[f"[sogiayto{i}]"] = mapping[f"[CCCD {i}]"]
        mapping[f"[ngaycap{i}]"] = mapping[f"[Ngày cấp {i}]"]
        mapping[f"[diachi{i}]"] = mapping[f"[Địa chỉ {i}]"]
        mapping[f"[loaigiayto{i}]"] = mapping[f"[Loại CC {i}]"]
        mapping[f"[noicap{i}]"] = mapping[f"[Nơi cấp CC {i}]"]
        mapping[f"[loaicutru{i}]"] = mapping[f"[Thường trú {i}]"]
        mapping[f"[loaidiachi{i}]"] = mapping[f"[Thường trú {i}]"]
    mapping["[Năm chết]"] = mapping.get("[Năm chết 1]", "")

    for i, row in enumerate(land_rows[:10], start=1):
        mapping[f"[Loại đất {i}]"] = _safe_text(row.get("loai_dat", ""))
        mapping[f"[Diện tích {i}]"] = _safe_text(row.get("dien_tich", ""))
        mapping[f"[Thờ hạn {i}]"] = _safe_text(row.get("thoi_han", ""))
    for i in range(len(land_rows) + 1, 11):
        mapping[f"[Loại đất {i}]"] = ""
        mapping[f"[Diện tích {i}]"] = ""
        mapping[f"[Thờ hạn {i}]"] = ""
    # Không còn đắp thời hạn lẻ (properties.thoi_han) vào [Thờ hạn 1] —
    # thời hạn thuộc từng cụm (MIN-141 đợt 2); thời hạn lẻ không gắn được
    # cụm được workspace_get báo orphan_thoi_han để đối chiếu.

    role_groups: dict[str, list[WordPerson]] = {key: [] for key in ROLE_LABELS}
    for person in context.all_people:
        role_key = "chu_dat" if person.is_land_owner else _role_key(person.role)
        if role_key in role_groups:
            role_groups[role_key].append(person)
    for role_key, label in ROLE_LABELS.items():
        role_people = role_groups[role_key]
        _add_word_person_group(mapping, context, label.capitalize(), role_people)
        first = role_people[0] if role_people else None
        for field, value in _person_placeholder_values(context, first).items():
            mapping[f"[{field} {label}]"] = value

    # -----------------------------------------------------------------------
    # Word export V2 placeholders based on case_state_json
    # -----------------------------------------------------------------------
    _add_block_placeholders(mapping, context)
    _add_property_placeholders(mapping, context.assets)
    mapping["[Danh sách người thừa kế]"] = mapping["[Danh sách hàng thừa kế]"]
    mapping["[Đoạn mô tả quan hệ]"] = mapping["[Đoạn quan hệ gia đình]"]

    return mapping


def _build_normalized_mapping(mapping: dict[str, str]) -> dict[str, str]:
    normalized = {}
    for k, v in mapping.items():
        if not (k.startswith("[") and k.endswith("]")):
            continue
        normalized[_normalize_token(k[1:-1])] = v
    return normalized


def _replace_text_placeholders(text: str, mapping: dict[str, str], normalized_mapping: dict[str, str]) -> str:
    new_text = text
    for k, v in mapping.items():
        if k in new_text:
            new_text = new_text.replace(k, v)

    def _token_repl(match):
        token = match.group(1)
        direct = mapping.get(f"[{token}]")
        if direct is not None:
            return direct
        norm = _normalize_token(token)
        if norm in normalized_mapping:
            return normalized_mapping[norm]
        return match.group(0)

    new_text = re.sub(r"\[([^\[\]]+)\]", _token_repl, new_text)
    new_text = re.sub(r"[ \t]{2,}", " ", new_text)
    new_text = re.sub(r"[ \t]+([,.;:])", r"\1", new_text)
    return new_text


def _replace_in_paragraph(paragraph: Any, mapping: dict[str, str], normalized_mapping: dict[str, str]) -> None:
    if not paragraph.runs:
        return
    text = "".join(r.text for r in paragraph.runs)
    if "[" not in text or "]" not in text:
        return

    for run in paragraph.runs:
        if "[" in run.text and "]" in run.text:
            new_text = _replace_text_placeholders(run.text, mapping, normalized_mapping)
            if new_text != run.text:
                run.text = new_text

    text = "".join(r.text for r in paragraph.runs)
    if "[" not in text or "]" not in text:
        return

    new_text = _replace_text_placeholders(text, mapping, normalized_mapping)
    if new_text != text:
        paragraph.runs[0].text = new_text
        for run in paragraph.runs[1:]:
            run.clear()


def replace_in_doc(doc: Any, mapping: dict[str, str]) -> None:
    normalized_mapping = _build_normalized_mapping(mapping)
    for paragraph in doc.paragraphs:
        _replace_in_paragraph(paragraph, mapping, normalized_mapping)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _replace_in_paragraph(paragraph, mapping, normalized_mapping)
    for section in doc.sections:
        for paragraph in section.header.paragraphs:
            _replace_in_paragraph(paragraph, mapping, normalized_mapping)
        for paragraph in section.footer.paragraphs:
            _replace_in_paragraph(paragraph, mapping, normalized_mapping)


def find_unresolved_placeholders(doc: Any) -> list[str]:
    texts: list[str] = []
    texts.extend(paragraph.text for paragraph in doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                texts.extend(paragraph.text for paragraph in cell.paragraphs)
    for section in doc.sections:
        texts.extend(paragraph.text for paragraph in section.header.paragraphs)
        texts.extend(paragraph.text for paragraph in section.footer.paragraphs)
    found = {
        match.group(0)
        for text in texts
        for match in re.finditer(r"\[[^\[\]]+\]", text)
    }
    return sorted(found)


def list_public_builtin_templates(root: str | Path = "word_templates") -> list[dict[str, Any]]:
    root_path = Path(root)
    items = []
    for path in sorted(root_path.glob("*.docx"), key=lambda p: p.name.lower()):
        if path.name in HIDDEN_BUILTIN_TEMPLATE_NAMES:
            continue
        if path.name.startswith("~$"):
            continue
        items.append({"id": f"builtin:{path.name}", "ten_mau": path.stem, "is_active": False, "builtin": True})
    return items

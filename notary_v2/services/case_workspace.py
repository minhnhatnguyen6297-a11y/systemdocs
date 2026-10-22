"""Case workspace service — backend thật cho contract notary.case-drafting.v2.

Sở hữu business rule của `notary.workspace_get`,
`notary.workspace_commit_stage` và `notary.workspace_create`; sidecar
handlers chỉ dịch payload ↔ service, không chứa nghiệp vụ (MIN-107,
nâng cấp v2 ở MIN-128; cutover Storage B ở issue 13).

Storage B (contract §13.19) — dữ kiện Stage là dòng case-owned:

- `CasePersonRow`/`CaseAssetRow` (ordered `vitri`) là SOT; `customer_id`/
  `property_id` chỉ là identity dùng chung, resolve ngay transaction ghi.
- `CaseAssetLandRow` thuộc dòng tài sản; không mirror/lấy PropertyLandRow.
- `case_state_json` schemaVersion 4 chỉ còn owner_row_id (inheritance),
  bảy scalar `case`, Diagram (state v3 + render_model + warnings) và
  docx_import. Không Stage/assets/engine projections.
- `inheritance_participants`/`inheritance_case_properties` là projection
  theo row_id; `nguoi_chet_id`/`tai_san_id` là identity projection (nullable).
- Trạng thái chỉ `draft`/`done`; không khóa soạn, không `locked` trên wire.

`case_type` derive từ `loai_van_ban` (không thêm column): inheritance doc
(`khai_nhan`/`thoa_thuan`) → "inheritance"; two-party doc (§13.5 Q11) →
"two_party"; giá trị khác → loại việc chưa hỗ trợ (capabilities tắt,
write bị chặn — giữ semantics "Chưa hỗ trợ" §7 drafting-tab).
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import uuid
from collections.abc import Mapping
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import text as sa_text
from sqlalchemy.exc import IntegrityError, OperationalError

from database import MAX_LAND_ROWS, _land_row_field
from models import (
    CaseAssetLandRow,
    CaseAssetRow,
    CasePersonRow,
    Customer,
    InheritanceCase,
    InheritanceCaseProperty,
    InheritanceParticipant,
    Property,
    derive_person_fields,
)
from services import case_rows

SCHEMA_VERSION = "notary.case-drafting.v2"
PAYLOAD_SCHEMA_VERSION = case_rows.PAYLOAD_SCHEMA_VERSION
DIAGRAM_STATE_VERSION = 3

CASE_TYPE_INHERITANCE = case_rows.CASE_TYPE_INHERITANCE
CASE_TYPE_TWO_PARTY = case_rows.CASE_TYPE_TWO_PARTY
CASE_TYPES = (CASE_TYPE_INHERITANCE, CASE_TYPE_TWO_PARTY)

DOCUMENT_TYPES = case_rows.DOCUMENT_TYPES
DOCUMENT_TYPES_TWO_PARTY = case_rows.DOCUMENT_TYPES_TWO_PARTY
INTAKE_KINDS = ["image", "pdf", "docx", "xlsx", "text"]

MAX_ASSETS = 3                        # §13.3
MAX_PEOPLE_TWO_PARTY = 30             # §13.5
POSITION_VALUES = (1, 2, 3)           # §13.4 — own/receive ⊆ {1,2,3}
TWO_PARTY_NODE_IDS = tuple(f"p{i}" for i in range(1, 31))

_UUID4_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}"
    r"-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
_DATE_OR_YEAR_RE = re.compile(r"^\d{4}(-\d{2}-\d{2})?$")
_DATE_FULL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_GENDER_VALUES = ("Nam", "Nữ")
_BIRTH_PARENT_IDS = ("father", "mother")
_SPOUSE_PARENT_IDS = ("spouse_father", "spouse_mother")
_BIRTH_PARENT_ROLES = ("Cha", "Mẹ")
_SPOUSE_PARENT_ROLES = ("Cha_vc", "Me_vc")
_SPOUSE_RELATIONS = ("spouse", "branchSpouse")
_GHOST_KINDS = ("ghost", "pendingspouse")
_PLACEHOLDER_ROW_ID = "00000000-0000-4000-8000-000000000000"


class WorkspaceError(Exception):
    """Lỗi nghiệp vụ có `code`/`details` theo contract §9 + §13.9."""

    def __init__(self, code: str, message: str,
                 details: Optional[Mapping[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details) if details else {}


# ------------------------------------------------------------------ helpers


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _nn(value: Any) -> Optional[str]:
    text = _clean(value)
    return text or None


def _to_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 1 else None
    text = _clean(value)
    if text.isdigit():
        parsed = int(text)
        return parsed if parsed >= 1 else None
    return None


def _is_uuid4(value: Any) -> bool:
    return isinstance(value, str) and bool(_UUID4_RE.match(value))


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _norm_gender(value: Any) -> Optional[str]:
    text = _clean(value)
    if not text:
        return None
    if text.lower() == "nam":
        return "Nam"
    if text.lower() in ("nữ", "nu"):
        return "Nữ"
    return None


def _valid_date_or_year(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or not _DATE_OR_YEAR_RE.match(value):
        return False
    if len(value) == 4:
        return int(value) >= 1
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _valid_date_full(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or not _DATE_FULL_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _parse_date_or_year(value: Any) -> Optional[date]:
    if value is None:
        return None
    text = _clean(value)
    if not text:
        return None
    if len(text) == 4 and text.isdigit():
        return date(int(text), 1, 1)
    try:
        return date.fromisoformat(text[:10])
    except (ValueError, TypeError):
        return None


def _emit_date_or_year(value: Any) -> Optional[str]:
    """DB date hoặc chuỗi legacy (dd/mm/YYYY, ISO, YYYY) → YYYY-MM-DD|YYYY|null."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{4}", text):
        return text
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if match:
        try:
            return date(
                int(match.group(3)), int(match.group(2)),
                int(match.group(1))).isoformat()
        except ValueError:
            return None
    if _DATE_FULL_RE.match(text[:10]):
        try:
            return date.fromisoformat(text[:10]).isoformat()
        except ValueError:
            return None
    return None


def _case_meta(case: InheritanceCase) -> tuple[str, str]:
    """(case_type, document_type) — `loai_van_ban` là discriminator."""
    return case_rows.case_types(case)


def _field_error(row_id: Any, field: str, code: str, message: str,
                 index: Optional[int] = None) -> dict:
    valid = _is_uuid4(row_id)
    if not valid and index is not None:
        message = f"{message} (row index {index})"
    return {
        "row_id": row_id if valid else _PLACEHOLDER_ROW_ID,
        "field": field,
        "code": code,
        "message": message,
    }


def _check_extra_keys(mapping: Any, allowed: set, where: str) -> None:
    if not isinstance(mapping, Mapping):
        return
    extra = sorted(set(mapping) - allowed)
    if extra:
        raise WorkspaceError(
            "validation_error",
            f"{where} có field không hỗ trợ: {extra}")


def _person_contract_keys() -> tuple[str, ...]:
    return case_rows.PERSON_CONTRACT_KEYS


def _asset_contract_keys() -> tuple[str, ...]:
    return case_rows.ASSET_CONTRACT_KEYS


_STAGE_KEYS = {"owner_row_id", "people", "assets"}
_PERSON_FIELD_SET = set(_person_contract_keys())
_ASSET_FIELD_SET = set(_asset_contract_keys())
CASE_SCALAR_FIELDS = case_rows.CASE_SCALAR_FIELDS

_CASE_META_UPDATE_KEYS = {"ngay_lap_ho_so", "noi_niem_yet", "ghi_chu"}

_LAND_ROW_KEY_SET = {"loaidat", "dientich", "thoihan",
                     "loai_dat", "dien_tich", "thoi_han"}
_LAND_ROW_STR_KEYS = ("loai_dat", "loaidat", "thoi_han", "thoihan")
_LAND_ROW_NUM_KEYS = ("dien_tich", "dientich")

_PERSON_KEY_ALIASES = {
    "ten": "ho_ten", "gioitinh": "gioi_tinh", "ngaysinh": "ngay_sinh",
    "ngaychet": "ngay_chet", "sogiayto": "so_giay_to",
    "ngaycap": "ngay_cap", "noicap": "noi_cap", "diachi": "dia_chi",
    "loaigiayto": "loai_giay_to", "loaidiachi": "loai_dia_chi",
}
_CASE_META_KEY_ALIASES = {
    "casetype": "case_type", "documenttype": "document_type",
    "ngaylaphoso": "ngay_lap_ho_so", "noiniemyet": "noi_niem_yet",
    "nguoinhanuyquyen": "nguoi_nhan_uy_quyen",
    "nguoinhanuyquyenid": "nguoi_nhan_uy_quyen_id",
    "noidungviec": "noi_dung_viec", "ghichu": "ghi_chu",
}


def _fold_key_aliases(row: Any, aliases: Mapping[str, str],
                      where: str) -> Any:
    """Gộp key canonical về key wire legacy.

    Cả hai spelling cùng mang giá trị khác nhau → validation_error
    (không âm thầm chọn một).
    """
    if not isinstance(row, Mapping):
        return row
    folded = dict(row)
    for canon, legacy in aliases.items():
        if canon not in folded:
            continue
        canon_v, legacy_v = folded.pop(canon), folded.get(legacy)
        if (legacy_v is not None and canon_v is not None
                and canon_v != legacy_v):
            raise WorkspaceError(
                "validation_error",
                f"{where}: {canon} và {legacy} mang giá trị khác nhau")
        folded[legacy] = canon_v if canon_v is not None else legacy_v
    return folded


def _resolve_derived_field(incoming: Any, stored: Any,
                           prev_derived: Any, new_derived: Any):
    """Trường suy ra của Người (`loai_giay_to`/`noi_cap`/`loai_dia_chi`).

    - `incoming` khác `stored` → người dùng vừa sửa → giữ `incoming`.
    - `stored` khác `prev_derived` → bằng chứng đã xác nhận → giữ.
    - Còn lại (echo/trống) → tính lại `new_derived`.
    """
    inc, sto = _nn(incoming), _nn(stored)
    if inc != sto:
        return inc
    if sto is not None and sto != prev_derived:
        return inc
    return new_derived


# ------------------------------------------------------- diagram sanitizing


def _scrub_v2_links(nodes: list[dict]) -> list[dict]:
    ids = {n["id"] for n in nodes}
    for node in nodes:
        node["parentSlotIds"] = [p for p in node["parentSlotIds"] if p in ids]
        if node["spouseSlotId"] and node["spouseSlotId"] not in ids:
            node["spouseSlotId"] = None
    return nodes


def _sanitize_positions(value: Any) -> list[int]:
    """ownPositions/receivePositions đã persist → list unique ⊆ {1,2,3}."""
    if not isinstance(value, list):
        return []
    out: list[int] = []
    for x in value:
        if isinstance(x, bool) or not isinstance(x, int):
            continue
        if x in POSITION_VALUES and x not in out:
            out.append(x)
    return out


def _sanitize_v3_nodes(raw_nodes: Any, valid_row_ids: set) -> list[dict]:
    """Normalize node V3 inheritance đã persist; bỏ node trỏ personId
    ngoài Stage."""
    out: list[dict] = []
    seen: set = set()
    for raw in raw_nodes or []:
        if not isinstance(raw, Mapping):
            continue
        nid = _clean(raw.get("id"))
        if not nid or nid in seen:
            continue
        person = raw.get("personId")
        person_id = _clean(person) if person is not None else None
        if person_id:
            if person_id not in valid_row_ids:
                continue
        else:
            person_id = None
        seen.add(nid)
        parents = raw.get("parentSlotIds")
        out.append({
            "id": nid,
            "personId": person_id,
            "parentSlotIds": [
                _clean(p) for p in parents if _clean(p)
            ][:2] if isinstance(parents, list) else [],
            "spouseSlotId": _nn(raw.get("spouseSlotId")),
            "ownPositions": _sanitize_positions(raw.get("ownPositions")),
            "receivePositions": _sanitize_positions(
                raw.get("receivePositions")),
            "hidden": _coerce_bool(raw.get("hidden"), False),
            "deleted": _coerce_bool(raw.get("deleted"), False),
        })
    return _scrub_v2_links(out)


def _sanitize_two_party_nodes(raw_nodes: Any, valid_row_ids: set) -> list[dict]:
    """Normalize node two_party đã persist: chỉ giữ id canonical p1..p30
    (unique, đúng thứ tự); personId ngoài Stage → null."""
    out: list[dict] = []
    seen: set = set()
    for raw in raw_nodes or []:
        if not isinstance(raw, Mapping):
            continue
        nid = _clean(raw.get("id"))
        if nid not in TWO_PARTY_NODE_IDS or nid in seen:
            continue
        seen.add(nid)
        person = raw.get("personId")
        person_id = _clean(person) if person is not None else None
        if person_id and person_id not in valid_row_ids:
            person_id = None
        out.append({
            "id": nid,
            "personId": person_id,
            "hidden": _coerce_bool(raw.get("hidden"), False),
            "deleted": _coerce_bool(raw.get("deleted"), False),
        })
    out.sort(key=lambda n: int(n["id"][1:]))
    return out


def _canonical_two_party_nodes(nodes: list[dict]) -> list[dict]:
    """Đủ đúng 30 slot p1..p30 theo thứ tự — ô thiếu được seed trống."""
    by_id = {n.get("id"): n for n in nodes if isinstance(n, dict)}
    out: list[dict] = []
    for pid in TWO_PARTY_NODE_IDS:
        n = by_id.get(pid)
        out.append({
            "id": pid,
            "personId": (n or {}).get("personId"),
            "hidden": bool((n or {}).get("hidden")),
            "deleted": bool((n or {}).get("deleted")),
        })
    return out


def _v3_to_v2_nodes(nodes: list[dict]) -> list[dict]:
    """V3 → V2 engine projection (§13.4 A4): isLandOwner := ownPositions ≠ [],
    willReceive := receivePositions ≠ []."""
    out: list[dict] = []
    for n in nodes or []:
        out.append({
            "id": n["id"],
            "personId": n.get("personId"),
            "parentSlotIds": list(n.get("parentSlotIds") or []),
            "spouseSlotId": n.get("spouseSlotId"),
            "isLandOwner": bool(n.get("ownPositions")),
            "willReceive": bool(n.get("receivePositions")),
            "hidden": _coerce_bool(n.get("hidden"), False),
            "deleted": _coerce_bool(n.get("deleted"), False),
        })
    return out


def _seed_inheritance_state(owner_row_id: Optional[str],
                            asset_count: int) -> dict:
    """Seed `diagram.state` v3 khi create không kèm diagram (§13.6)."""
    own = list(range(1, max(0, min(MAX_ASSETS, asset_count)) + 1))
    nodes = [
        {"id": "father", "personId": None, "parentSlotIds": [],
         "spouseSlotId": "mother", "ownPositions": [],
         "receivePositions": [], "hidden": False, "deleted": False},
        {"id": "mother", "personId": None, "parentSlotIds": [],
         "spouseSlotId": "father", "ownPositions": [],
         "receivePositions": [], "hidden": False, "deleted": False},
        {"id": "spouse_father", "personId": None, "parentSlotIds": [],
         "spouseSlotId": "spouse_mother", "ownPositions": [],
         "receivePositions": [], "hidden": False, "deleted": False},
        {"id": "spouse_mother", "personId": None, "parentSlotIds": [],
         "spouseSlotId": "spouse_father", "ownPositions": [],
         "receivePositions": [], "hidden": False, "deleted": False},
        {"id": "owner", "personId": owner_row_id,
         "parentSlotIds": ["father", "mother"], "spouseSlotId": "spouse",
         "ownPositions": own, "receivePositions": [],
         "hidden": False, "deleted": False},
        {"id": "spouse", "personId": None,
         "parentSlotIds": ["spouse_father", "spouse_mother"],
         "spouseSlotId": "owner", "ownPositions": [],
         "receivePositions": [], "hidden": False, "deleted": False},
        {"id": "child_1", "personId": None,
         "parentSlotIds": ["owner", "spouse"], "spouseSlotId": None,
         "ownPositions": [], "receivePositions": [],
         "hidden": False, "deleted": False},
    ]
    return {"version": DIAGRAM_STATE_VERSION,
            "domain": CASE_TYPE_INHERITANCE, "nodes": nodes}


def _seed_two_party_state() -> dict:
    """30 slot canonical trống p1..p30 (§13.5)."""
    return {"version": DIAGRAM_STATE_VERSION,
            "domain": CASE_TYPE_TWO_PARTY,
            "nodes": _canonical_two_party_nodes([])}


def unsupported_render_model() -> dict:
    """Render model của domain two_party — KHÔNG bao giờ vào engine thừa
    kế (§13.5). Shape giữ nguyên §7.2 (engineVersion 2)."""
    return {
        "engineVersion": 2,
        "status": "unsupported",
        "allocations": {},
        "breakdowns": [],
        "requiredSlots": [],
        "warnings": [{
            "code": "diagram.two_party_unsupported",
            "message": "Sơ đồ hai bên không chạy engine thừa kế"}],
        "errors": [],
        "unresolvedEstates": [],
        "conservation": {"allocated": "0", "unresolved": "0", "total": "0"},
    }


def _parent_role(node_id: str, info: Mapping[str, Any],
                 male_role: str, female_role: str) -> str:
    """Role cho slot cha/mẹ (và bên vợ/chồng) — id cố định trước, gender sau."""
    if node_id in ("father", "spouse_father"):
        return male_role
    if node_id in ("mother", "spouse_mother"):
        return female_role
    return female_role if _clean(info.get("gioi_tinh")) == "Nữ" else male_role


def _project_role_nodes(nodes: list[dict],
                        people: list[dict]) -> list[dict]:
    """Projection vai trò/quan hệ TRONG RAM, keyed `row_id`.

    `personId`/`parentPersonId` là row_id (không cast entity id), nên hai
    dòng chung identity vẫn giữ hai bộ độc lập. Chỉ dùng cho participant
    projection, không persist.
    """
    nodes = [n for n in (nodes or []) if isinstance(n, Mapping)]
    by_id = {n["id"]: n for n in nodes}
    people_map = {p["row_id"]: p for p in people
                  if isinstance(p, Mapping) and p.get("row_id")}

    def info_of(node: Mapping[str, Any]) -> Mapping[str, Any]:
        return people_map.get(node.get("personId")) or {}

    owner = by_id.get("owner")
    owner_spouse = _clean(owner.get("spouseSlotId")) if owner else ""
    if owner_spouse not in by_id:
        owner_spouse = next(
            (n["id"] for n in nodes
             if n["id"] != "owner" and n.get("spouseSlotId") == "owner"),
            "")
    owner_pair = {x for x in ("owner", owner_spouse) if x}
    owner_parents = set(owner.get("parentSlotIds") or []) if owner else set()
    spouse_node = by_id.get(owner_spouse) if owner_spouse else None
    spouse_parents = (
        set(spouse_node.get("parentSlotIds") or []) if spouse_node else set())
    child_slots = {
        n["id"] for n in nodes
        if n.get("parentSlotIds") and set(n["parentSlotIds"]) <= owner_pair
    }

    out: list[dict] = []
    for node in nodes:
        nid = node["id"]
        parents = [p for p in (node.get("parentSlotIds") or []) if p in by_id]
        spouse = node.get("spouseSlotId")
        spouse = spouse if spouse in by_id else None
        person_id = _nn(node.get("personId"))
        info = info_of(node)
        relation = role = family = anchor = ""
        if nid == "owner":
            relation, role = "owner", "Owner"
        elif spouse == "owner":
            relation, role, anchor = "spouse", "Vợ/Chồng", "owner"
        elif nid in owner_parents:
            relation = "parent"
            role = _parent_role(nid, info, "Cha", "Mẹ")
        elif nid in spouse_parents:
            relation = "spouseParent"
            role = _parent_role(nid, info, "Cha_vc", "Me_vc")
        elif spouse and spouse in child_slots:
            relation, role, anchor = "branchSpouse", "Con_dau_re", spouse
        elif parents and set(parents) <= owner_pair:
            relation, role, family = "child", "Con", "ownerSpouse"
        elif parents and set(parents) <= owner_parents:
            relation, role, family = "sibling", "Anh/Chị/Em", "birthParents"
        elif parents and set(parents) <= spouse_parents:
            relation, role, family = "sibling", "Anh/Chị/Em", "spouseParents"
        elif any(p in child_slots for p in parents):
            parent = next(p for p in parents if p in child_slots)
            relation, role = "grandchild", "Cháu"
            family = f"descendant:{parent}"
        parent_slot = anchor or (parents[0] if parents else "")
        parent_row_id = (
            _nn(by_id[parent_slot].get("personId"))
            if parent_slot in by_id
            and relation not in ("spouse", "branchSpouse")
            else None)
        out.append({
            "id": nid,
            "kind": "person",
            "label": _clean(info.get("ho_ten")),
            "role": role,
            "relationType": relation,
            "personId": person_id,
            "parentSlotId": parent_slot,
            "parentPersonId": parent_row_id or "",
            "familyGroupId": family,
            "sourceId": anchor or None,
            "spouseOf": anchor or None,
            "isLandOwner": bool(node.get("ownPositions")),
            "willReceive": bool(node.get("receivePositions")),
            "hidden": bool(node.get("hidden")),
            "deleted": bool(node.get("deleted")),
        })
    return out


# -------------------------------------------------------------------- service


class CaseWorkspaceService:
    """Compose/commit workspace cho một InheritanceCase trên session ORM."""

    def __init__(self, db, docx_store=None):
        self.db = db
        self.docx_store = docx_store

    def _docx_context(self, context, stage):
        from .word_original import validate_context
        try:
            store = self.docx_store() if callable(self.docx_store) else self.docx_store
            return validate_context(context, stage, store)
        except (ValueError, OSError, TypeError, KeyError) as exc:
            raise WorkspaceError("validation_error", str(exc)) from exc

    def _validate_docx_bindings(self, case, context, previous=None):
        from .word_original import validate_new_bindings
        try:
            store = self.docx_store() if callable(self.docx_store) else self.docx_store
            validate_new_bindings(case, context, previous, store)
        except (ValueError, OSError, TypeError, KeyError) as exc:
            raise WorkspaceError('validation_error', str(exc)) from exc

    # ------------------------------------------------------------- public

    def get(self, case_id: int) -> dict:
        """Đọc rows + JSON v4; không ghi/migrate, không key `locked`."""
        case = self._load_case(case_id)
        case_type, document_type = _case_meta(case)
        supported = case_type in CASE_TYPES
        domain = (case_type if supported else CASE_TYPE_INHERITANCE)

        composed = self._compose_stage(case)
        valid_rows = {p["row_id"] for p in composed.people}
        state = self._state_v3(
            composed.payload, domain=domain, valid_row_ids=valid_rows,
            asset_count=len(composed.assets))
        owner_row_id = None
        if domain == CASE_TYPE_INHERITANCE:
            owner_row_id = self._resolve_owner_row_id(
                composed.payload, state, valid_rows)
        render_model = self._render_model(composed.payload)

        stage_out = {"people": composed.people,
                     "assets": composed.assets}
        if domain == CASE_TYPE_INHERITANCE:
            stage_out = {"owner_row_id": owner_row_id, **stage_out}
        diagram_out: dict = {
            "domain": domain,
            "state": state,
            "render_model": render_model,
        }
        payload_diagram = composed.payload.get("diagram")
        if (isinstance(payload_diagram, Mapping)
                and payload_diagram.get("warnings")):
            diagram_out["warnings"] = list(payload_diagram["warnings"])

        payload_case = composed.payload.get("case")
        payload_case = payload_case if isinstance(payload_case, Mapping) else {}
        data = {
            "schema_version": SCHEMA_VERSION,
            "backend_mode": "real",
            "case": {
                "id": case.id,
                "case_type": case_type,
                "document_type": document_type,
                "status": case.trang_thai,
                "revision": self._revision(case),
                "ngay_lap_ho_so": _emit_date_or_year(case.ngay_lap_ho_so),
                "noi_niem_yet": _nn(case.noi_niem_yet),
                "nguoi_nhan_uy_quyen": _nn(case.nguoi_nhan_uy_quyen),
                "nguoi_nhan_uy_quyen_id": case.nguoi_nhan_uy_quyen_id,
                "noi_dung_viec": _nn(case.noi_dung_viec),
                **{key: payload_case.get(key) for key in CASE_SCALAR_FIELDS},
                "chudat": self._landowner_names({
                    "stage": composed.people,
                    "assets": composed.assets,
                    "diagram": {"state": state}}),
                "ghi_chu": _nn(case.ghi_chu),
            },
        }
        data["stage"] = stage_out
        data["diagram"] = diagram_out
        if "docx_import" in composed.payload:
            data["docx_import"] = composed.payload["docx_import"]
        data["capabilities"] = {
            "intake": list(INTAKE_KINDS) if supported else [],
            "diagram": supported,
            "word_export": case_type in CASE_TYPES,
        }
        return data

    def commit_stage(self, case_id: int, base_revision: int,
                     stage: Any, case_meta: Any = None,
                     docx_import: Any = None) -> dict:
        """`notary.workspace_commit_stage` — ghi rows + projection + Diagram
        đã lưu trong một transaction; giữ trạng thái; revision+1."""
        case = self._load_case(case_id)
        meta_edit: Optional[dict] = None
        if case_meta is not None:
            meta_edit = self._validate_case_meta(
                case_meta, require_type=False)
            stored_type, stored_doc = _case_meta(case)
            sent = _fold_key_aliases(
                case_meta, _CASE_META_KEY_ALIASES, "payload.case")
            if ("case_type" in sent and sent["case_type"] is not None
                    and sent["case_type"] != stored_type):
                raise WorkspaceError(
                    "validation_error",
                    "case_type không đổi qua commit")
            if ("document_type" in sent
                    and sent["document_type"] is not None
                    and sent["document_type"] != stored_doc):
                raise WorkspaceError(
                    "validation_error",
                    "document_type không đổi qua commit")
        case_type, _doc_type = _case_meta(case)
        if case_type not in CASE_TYPES:
            raise WorkspaceError(
                "case_type_unsupported",
                f"Loại việc chưa hỗ trợ: {case_type}",
                details={"case_type": case_type})
        if (not isinstance(base_revision, int)
                or isinstance(base_revision, bool) or base_revision < 1):
            raise WorkspaceError(
                "validation_error", "base_revision phải là số nguyên ≥ 1")
        server_revision = self._revision(case)
        if base_revision != server_revision:
            raise WorkspaceError(
                "workspace_conflict",
                f"Revision server hiện là {server_revision}, "
                f"base_revision={base_revision}",
                details={"server_revision": server_revision})
        if not isinstance(stage, Mapping):
            raise WorkspaceError("validation_error",
                                 "payload.stage phải là object")
        _check_extra_keys(stage, _STAGE_KEYS, "stage")
        people = stage.get("people")
        assets = stage.get("assets")
        if not isinstance(people, list) or not isinstance(assets, list):
            raise WorkspaceError(
                "validation_error",
                "stage.people/stage.assets phải là danh sách")
        people = [_fold_key_aliases(r, _PERSON_KEY_ALIASES,
                                    "person_row") for r in people]
        owner_row_id = self._validate_owner_pointer(
            stage, people, case_type)
        field_errors = self._validate_stage(people, assets, case_type)
        if field_errors:
            raise WorkspaceError(
                "stage_validation_error",
                f"Stage có {len(field_errors)} lỗi field",
                details={"field_errors": field_errors})

        try:
            if meta_edit is not None:
                case.ngay_lap_ho_so = meta_edit["ngay_lap_ho_so"]
                case.noi_niem_yet = meta_edit["noi_niem_yet"]
                case.nguoi_nhan_uy_quyen = meta_edit["nguoi_nhan_uy_quyen"]
                case.nguoi_nhan_uy_quyen_id = \
                    meta_edit["nguoi_nhan_uy_quyen_id"]
                case.noi_dung_viec = meta_edit["noi_dung_viec"]
                case.ghi_chu = meta_edit["ghi_chu"]
            payload = self._load_payload(case) or {}
            if meta_edit is not None:
                payload["case"] = {
                    **(payload.get("case") or {}),
                    **{key: meta_edit[key] for key in CASE_SCALAR_FIELDS
                       if key in meta_edit},
                }
            previous_import = payload.get('docx_import')
            resolved_people, resolved_assets = self._write_stage_rows(
                case, {"people": people, "assets": assets})
            self._sync_links(case, resolved_assets)

            stage_view = {
                "people": [wire for _r, _e, wire in resolved_people],
                "assets": [wire for _r, _e, wire in resolved_assets],
            }
            if docx_import is not None:
                payload["docx_import"] = self._docx_context(
                    docx_import, stage_view)
            elif payload.get("docx_import") is not None:
                payload["docx_import"] = self._docx_context(
                    payload["docx_import"], stage_view)
            self.db.flush()

            valid_rows = {rid for rid, _e, _w in resolved_people}
            state = self._state_v3(
                payload, domain=case_type, valid_row_ids=valid_rows,
                asset_count=len(resolved_assets))
            diagram_warnings: list = []
            if case_type == CASE_TYPE_INHERITANCE:
                pruned = _prune_positions(state["nodes"],
                                          len(resolved_assets))
                if pruned:
                    diagram_warnings.append({
                        "code": "diagram.selection_pruned",
                        "message": "Dấu chọn tài sản ngoài vị trí hiện có "
                                   "đã được gỡ"})
                _sync_owner_node(state["nodes"], owner_row_id)
                from services.inheritance_workspace import (
                    InheritanceWorkspaceService)
                render_model = InheritanceWorkspaceService(
                    self.db)._evaluate_inheritance(
                        state, valid_row_ids=valid_rows,
                        people=[{"row_id": rid,
                                 "ngay_chet": wire.get("ngay_chet")}
                                for rid, _entity, wire in resolved_people])
            else:
                state["nodes"] = _canonical_two_party_nodes(state["nodes"])
                render_model = unsupported_render_model()

            if case_type == CASE_TYPE_INHERITANCE:
                role_nodes = _project_role_nodes(
                    state["nodes"], stage_view["people"])
                self._sync_participants_and_owner(
                    case, role_nodes, stage_view["people"], owner_row_id)
            else:
                case.nguoi_chet_id = None

            now = _utc_now_iso()
            case.case_state_json = json.dumps(
                self._build_payload(
                    payload, state, render_model, now, domain=case_type,
                    owner_row_id=owner_row_id,
                    warnings=diagram_warnings),
                ensure_ascii=False)
            case.engine_state_json = None
            self.db.flush()

            if 'docx_import' in payload:
                self._validate_docx_bindings(
                    case, payload['docx_import'], previous_import)
            new_revision = server_revision + 1
            updated = self.db.execute(sa_text(
                "UPDATE inheritance_cases "
                "SET workspace_revision = :rev, updated_at = :now "
                "WHERE id = :cid AND workspace_revision = :base"),
                {"rev": new_revision,
                 "now": datetime.now(timezone.utc).replace(tzinfo=None),
                 "cid": case.id, "base": server_revision})
            if updated.rowcount != 1:
                self.db.rollback()
                fresh = self._fresh_revision(case.id, server_revision)
                raise WorkspaceError(
                    "workspace_conflict",
                    f"Revision server hiện là {fresh}",
                    details={"server_revision": fresh})
            self.db.commit()
        except WorkspaceError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise WorkspaceError(
                "stage_validation_error",
                "Dữ liệu vi phạm ràng buộc integrity",
                details={"field_errors": [_field_error(
                    None, "entity_id", "invalid_format",
                    "giá trị trùng/vi phạm ràng buộc duy nhất")]}) from exc
        except Exception:
            self.db.rollback()
            raise

        stage_out = {"people": [w for _r, _e, w in resolved_people],
                     "assets": [w for _r, _e, w in resolved_assets]}
        if case_type == CASE_TYPE_INHERITANCE:
            stage_out = {"owner_row_id": owner_row_id, **stage_out}
        diagram_out = {"state": state, "render_model": render_model}
        if diagram_warnings:
            diagram_out["warnings"] = diagram_warnings
        return {
            "schema_version": SCHEMA_VERSION,
            "revision": new_revision,
            "stage": stage_out,
            "diagram": diagram_out,
            **({"docx_import": payload["docx_import"]}
               if "docx_import" in payload else {}),
        }

    def convert_type(self, case_id: int, base_revision: int,
                     conversion: Any) -> dict:
        """Convert domain; Stage rows giữ nguyên, chỉ reset Diagram."""
        case = self._load_case(case_id)
        source_type, _ = _case_meta(case)
        if source_type not in CASE_TYPES:
            raise WorkspaceError("case_type_unsupported",
                                 "Loại việc chưa hỗ trợ")
        if (not isinstance(base_revision, int)
                or isinstance(base_revision, bool) or base_revision < 1):
            raise WorkspaceError("validation_error",
                                 "base_revision phải là số nguyên ≥ 1")
        revision = self._revision(case)
        if base_revision != revision:
            raise WorkspaceError("workspace_conflict", "Hồ sơ đã thay đổi",
                                 details={"server_revision": revision})
        if not isinstance(conversion, Mapping):
            raise WorkspaceError("validation_error",
                                 "conversion phải là object")
        _check_extra_keys(conversion, {
            "case_type", "document_type", "confirm_diagram_reset",
            "owner_row_id",
        }, "conversion")
        target = conversion.get("case_type")
        if target not in CASE_TYPES or target == source_type:
            raise WorkspaceError("validation_error",
                                 "Phải chọn loại hồ sơ khác")
        docs = (DOCUMENT_TYPES if target == CASE_TYPE_INHERITANCE
                else DOCUMENT_TYPES_TWO_PARTY)
        if conversion.get("document_type") not in docs:
            raise WorkspaceError("validation_error",
                                 "Phải chọn văn bản hợp lệ của loại mới")
        if conversion.get("confirm_diagram_reset") is not True:
            raise WorkspaceError("validation_error",
                                 "Phải xác nhận xóa Diagram cũ")
        composed = self._compose_stage(case)
        owner = self._validate_owner_pointer(
            conversion, composed.people, target)
        if target == CASE_TYPE_INHERITANCE:
            state = {
                "version": DIAGRAM_STATE_VERSION, "domain": target,
                "nodes": [{"id": "owner", "personId": owner,
                           "parentSlotIds": [], "spouseSlotId": None,
                           "ownPositions": [], "receivePositions": [],
                           "hidden": False, "deleted": False}],
            }
        else:
            state = _seed_two_party_state()
        payload = dict(composed.payload)
        try:
            case.loai_van_ban = conversion["document_type"]
            if target == CASE_TYPE_INHERITANCE:
                role_nodes = _project_role_nodes(
                    state["nodes"], composed.people)
                self._sync_participants_and_owner(
                    case, role_nodes, composed.people, owner)
            else:
                case.nguoi_chet_id = None
                self.db.query(InheritanceParticipant).filter(
                    InheritanceParticipant.ho_so_id == case.id).delete()
            now = _utc_now_iso()
            case.case_state_json = json.dumps(
                self._build_payload(
                    payload, state, None, now, domain=target,
                    owner_row_id=owner),
                ensure_ascii=False)
            case.engine_state_json = None
            self.db.flush()
            updated = self.db.execute(sa_text(
                "UPDATE inheritance_cases "
                "SET workspace_revision = :rev, updated_at = :now "
                "WHERE id = :cid AND workspace_revision = :base"),
                {"rev": revision + 1,
                 "now": datetime.now(timezone.utc).replace(tzinfo=None),
                 "cid": case.id, "base": revision})
            if updated.rowcount != 1:
                self.db.rollback()
                fresh = self._load_case(case_id)
                raise WorkspaceError(
                    "workspace_conflict", "Hồ sơ đã thay đổi",
                    details={"server_revision": self._revision(fresh)})
            self.db.expire(case, ["workspace_revision"])
            result = self.get(case_id)
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise

    def update_meta(self, case_id: int, base_revision: int,
                    meta: Any) -> dict:
        """`notary.workspace_update` — chỉ cột metadata; revision+1."""
        case = self._load_case(case_id)
        if (not isinstance(base_revision, int)
                or isinstance(base_revision, bool) or base_revision < 1):
            raise WorkspaceError(
                "validation_error", "base_revision phải là số nguyên ≥ 1")
        server_revision = self._revision(case)
        if base_revision != server_revision:
            raise WorkspaceError(
                "workspace_conflict",
                f"Revision server hiện là {server_revision}, "
                f"base_revision={base_revision}",
                details={"server_revision": server_revision})
        if not isinstance(meta, Mapping) or not meta:
            raise WorkspaceError(
                "validation_error", "payload.case phải là object non-empty")
        _check_extra_keys(meta, _CASE_META_UPDATE_KEYS, "payload.case")
        updates: dict = {}
        if "ngay_lap_ho_so" in meta:
            ngay = meta.get("ngay_lap_ho_so")
            if not _valid_date_full(ngay):
                raise WorkspaceError(
                    "validation_error",
                    "ngay_lap_ho_so phải là YYYY-MM-DD hoặc null")
            updates["ngay_lap_ho_so"] = _parse_date_or_year(ngay)
        for field in ("noi_niem_yet", "ghi_chu"):
            if field not in meta:
                continue
            value = meta.get(field)
            if value is not None and (
                    not isinstance(value, str) or not value.strip()):
                raise WorkspaceError(
                    "validation_error",
                    f"{field} phải là chuỗi non-empty hoặc null")
            updates[field] = _nn(value)
        try:
            for field, value in updates.items():
                setattr(case, field, value)
            self.db.flush()
            new_revision = server_revision + 1
            updated = self.db.execute(sa_text(
                "UPDATE inheritance_cases "
                "SET workspace_revision = :rev, updated_at = :now "
                "WHERE id = :cid AND workspace_revision = :base"),
                {"rev": new_revision,
                 "now": datetime.now(timezone.utc).replace(tzinfo=None),
                 "cid": case.id, "base": server_revision})
            if updated.rowcount != 1:
                self.db.rollback()
                fresh = self._fresh_revision(case.id, server_revision)
                raise WorkspaceError(
                    "workspace_conflict",
                    f"Revision server hiện là {fresh}",
                    details={"server_revision": fresh})
            self.db.commit()
        except WorkspaceError:
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(case)
        case_type, document_type = _case_meta(case)
        return {
            "schema_version": SCHEMA_VERSION,
            "revision": new_revision,
            "case": {
                "id": case.id,
                "case_type": case_type,
                "document_type": document_type,
                "status": case.trang_thai,
                "revision": new_revision,
                "ngay_lap_ho_so": _emit_date_or_year(case.ngay_lap_ho_so),
                "noi_niem_yet": _nn(case.noi_niem_yet),
                "ghi_chu": _nn(case.ghi_chu),
                "nguoi_nhan_uy_quyen": _nn(case.nguoi_nhan_uy_quyen),
                "nguoi_nhan_uy_quyen_id": case.nguoi_nhan_uy_quyen_id,
                "noi_dung_viec": _nn(case.noi_dung_viec),
            },
        }

    def create(self, idempotency_key: Any, case_meta: Any,
               stage: Any, state: Any, docx_import: Any = None) -> dict:
        """`notary.workspace_create` — tạo hồ sơ draft/revision 1.

        Một transaction: validate → hash/idempotency → tạo case trước →
        resolve/diff rows → projection → Diagram seed/persist → commit.
        """
        if not _is_uuid4(idempotency_key):
            raise WorkspaceError(
                "validation_error", "idempotency_key phải là UUID v4")

        meta = self._validate_case_meta(case_meta)
        case_type = meta["case_type"]
        if not isinstance(stage, Mapping):
            raise WorkspaceError("validation_error",
                                 "payload.stage phải là object")
        _check_extra_keys(stage, _STAGE_KEYS, "stage")
        people = stage.get("people")
        assets = stage.get("assets")
        if not isinstance(people, list) or not isinstance(assets, list):
            raise WorkspaceError(
                "validation_error",
                "stage.people/stage.assets phải là danh sách")
        people = [_fold_key_aliases(r, _PERSON_KEY_ALIASES,
                                    "person_row") for r in people]
        owner_row_id = self._validate_owner_pointer(
            stage, people, case_type)
        field_errors = self._validate_stage(people, assets, case_type)
        field_errors += self._validate_create_stage(people, assets)
        if field_errors:
            raise WorkspaceError(
                "stage_validation_error",
                f"Stage có {len(field_errors)} lỗi field",
                details={"field_errors": field_errors})

        creation_hash = _creation_hash(
            case_meta, stage, state, docx_import)
        existing = self.db.query(InheritanceCase).filter(
            InheritanceCase.workspace_idempotency_key
            == str(idempotency_key)).first()
        if existing is not None:
            if existing.workspace_creation_hash == creation_hash:
                data = self.get(existing.id)
                data["created"] = False
                return data
            raise WorkspaceError(
                "idempotency_conflict",
                "idempotency_key đã dùng với nội dung khác")

        from services.inheritance_workspace import (
            InheritanceWorkspaceService,
            _persisted_state,
            _validate_diagram_wire,
        )
        render_model: Optional[dict] = None
        if state is not None:
            errors = _validate_diagram_wire(state)
            if errors:
                raise WorkspaceError(
                    "diagram_invalid_state",
                    f"diagram state có {len(errors)} lỗi",
                    details={"errors": errors})
            if state["domain"] != case_type:
                raise WorkspaceError(
                    "diagram_domain_mismatch",
                    "state.domain không khớp case.case_type",
                    details={"expected": case_type,
                             "got": state["domain"]})
            row_ids = {r["row_id"] for r in people}
            for node in state["nodes"]:
                pid = node.get("personId")
                if pid is not None and pid not in row_ids:
                    raise WorkspaceError(
                        "diagram_reference_outside_stage",
                        "personId không thuộc Stage của payload",
                        details={"personId": pid})
            if case_type == CASE_TYPE_INHERITANCE:
                for node in state["nodes"]:
                    if (node.get("id") == "owner"
                            and node.get("deleted") is not True
                            and node.get("personId") is not None
                            and node["personId"] != owner_row_id):
                        raise WorkspaceError(
                            "diagram_owner_mismatch",
                            "node owner.personId phải khớp "
                            "stage.owner_row_id",
                            details={"owner_row_id": owner_row_id,
                                     "node_personId": node["personId"]})
                render_model = InheritanceWorkspaceService(
                    self.db)._evaluate_inheritance(
                        state, valid_row_ids=row_ids, people=people)
            else:
                render_model = unsupported_render_model()
            clean_state = _persisted_state(state)
        else:
            clean_state = (
                _seed_inheritance_state(owner_row_id, len(assets))
                if case_type == CASE_TYPE_INHERITANCE
                else _seed_two_party_state())
            render_model = None

        try:
            case = InheritanceCase(
                nguoi_chet_id=None,
                tai_san_id=None,
                ngay_lap_ho_so=meta["ngay_lap_ho_so"],
                loai_van_ban=meta["document_type"],
                trang_thai="draft",
                noi_niem_yet=meta["noi_niem_yet"],
                nguoi_nhan_uy_quyen=meta["nguoi_nhan_uy_quyen"],
                nguoi_nhan_uy_quyen_id=meta["nguoi_nhan_uy_quyen_id"],
                noi_dung_viec=meta["noi_dung_viec"],
                ghi_chu=meta["ghi_chu"],
                workspace_revision=1,
                workspace_idempotency_key=str(idempotency_key),
                workspace_creation_hash=creation_hash)
            self.db.add(case)
            self.db.flush()
            resolved_people, resolved_assets = self._write_stage_rows(
                case, {"people": people, "assets": assets})
            self._sync_links(case, resolved_assets)
            stage_view = {
                "people": [wire for _r, _e, wire in resolved_people],
                "assets": [wire for _r, _e, wire in resolved_assets],
            }
            if case_type == CASE_TYPE_INHERITANCE:
                role_nodes = _project_role_nodes(
                    clean_state["nodes"], stage_view["people"])
                self._sync_participants_and_owner(
                    case, role_nodes, stage_view["people"], owner_row_id)
            else:
                case.nguoi_chet_id = None

            initial_payload = {
                "case": {key: meta.get(key)
                         for key in CASE_SCALAR_FIELDS}}
            if docx_import is not None:
                initial_payload["docx_import"] = self._docx_context(
                    docx_import, stage_view)
            now = _utc_now_iso()
            case.case_state_json = json.dumps(
                self._build_payload(
                    initial_payload, clean_state, render_model, now,
                    domain=case_type, owner_row_id=owner_row_id),
                ensure_ascii=False)
            case.engine_state_json = None
            self.db.flush()
            if docx_import is not None:
                self._validate_docx_bindings(
                    case, initial_payload['docx_import'])
            self.db.commit()
        except WorkspaceError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise WorkspaceError(
                "stage_validation_error",
                "Dữ liệu vi phạm ràng buộc integrity",
                details={"field_errors": [_field_error(
                    None, "entity_id", "invalid_format",
                    "giá trị trùng/vi phạm ràng buộc duy nhất")]}) from exc
        except Exception:
            self.db.rollback()
            raise

        data = self.get(case.id)
        data["created"] = True
        return data

    def save_case(self, *, case_id: Optional[int] = None,
                  base_revision: Optional[int] = None,
                  idempotency_key: Optional[str] = None,
                  case_meta: Any, stage: Any, state: Any,
                  docx_import: Any = None) -> dict:
        """`notary.workspace_save_case` — Lưu hồ sơ nguyên tử (§13.19).

        Case mới (`case_id` absent): bắt buộc key, cấm base_revision, tạo
        case + rows + Diagram trong một transaction, revision=1, replay
        cùng key/hash trả workspace hiện tại created=false. Case cũ:
        bắt buộc base_revision, cấm key, CAS revision+1. Mọi nhánh thành
        công gán `trang_thai='done'`; lỗi sau flush rollback cả identity/
        meta/rows/đất/Diagram/status/revision.
        """
        new_case = case_id is None
        if new_case:
            if not _is_uuid4(idempotency_key):
                raise WorkspaceError(
                    "validation_error",
                    "idempotency_key phải là UUID v4 khi tạo mới")
            if base_revision is not None:
                raise WorkspaceError(
                    "validation_error",
                    "base_revision cấm khi tạo mới")
        else:
            if (isinstance(case_id, bool)
                    or not isinstance(case_id, int) or case_id < 1):
                raise WorkspaceError(
                    "validation_error", "case_id phải là số nguyên ≥ 1")
            if (isinstance(base_revision, bool)
                    or not isinstance(base_revision, int)
                    or base_revision < 1):
                raise WorkspaceError(
                    "validation_error",
                    "base_revision phải là số nguyên ≥ 1")
            if idempotency_key is not None:
                raise WorkspaceError(
                    "validation_error",
                    "idempotency_key cấm với hồ sơ đã có")
        if not isinstance(case_meta, Mapping):
            raise WorkspaceError(
                "validation_error", "payload.case phải là object")
        if not isinstance(stage, Mapping):
            raise WorkspaceError(
                "validation_error", "payload.stage phải là object")
        _check_extra_keys(stage, _STAGE_KEYS, "stage")
        people = stage.get("people")
        assets = stage.get("assets")
        if not isinstance(people, list) or not isinstance(assets, list):
            raise WorkspaceError(
                "validation_error",
                "stage.people/stage.assets phải là danh sách")
        people = [_fold_key_aliases(r, _PERSON_KEY_ALIASES,
                                    "person_row") for r in people]
        folded_meta = _fold_key_aliases(
            case_meta, _CASE_META_KEY_ALIASES, "payload.case")

        from services.inheritance_workspace import (
            InheritanceWorkspaceService,
            _validate_diagram_wire,
        )
        if not isinstance(state, Mapping):
            raise WorkspaceError(
                "diagram_invalid_state",
                "diagram.state phải là object")
        wire_errors = _validate_diagram_wire(state)
        if wire_errors:
            raise WorkspaceError(
                "diagram_invalid_state",
                f"diagram state có {len(wire_errors)} lỗi",
                details={"errors": wire_errors})

        if new_case:
            meta = self._validate_case_meta(case_meta)
            case_type = meta["case_type"]
        else:
            preloaded = self._load_case(case_id)
            case_type, stored_doc = _case_meta(preloaded)
            if case_type not in CASE_TYPES:
                raise WorkspaceError(
                    "case_type_unsupported",
                    f"Loại việc chưa hỗ trợ: {case_type}",
                    details={"case_type": case_type})
            sent_type = folded_meta.get("case_type")
            if sent_type is not None and sent_type != case_type:
                raise WorkspaceError(
                    "validation_error", "case_type không đổi qua Lưu hồ sơ")
            sent_doc = folded_meta.get("document_type")
            if sent_doc is not None and sent_doc != stored_doc:
                raise WorkspaceError(
                    "validation_error",
                    "document_type không đổi qua Lưu hồ sơ")
            meta = self._validate_case_meta(
                {**folded_meta, "case_type": case_type},
                require_type=False)
        owner_row_id = self._validate_owner_pointer(
            stage, people, case_type)
        field_errors = self._validate_stage(people, assets, case_type)
        if new_case:
            field_errors += self._validate_create_stage(people, assets)
        if field_errors:
            raise WorkspaceError(
                "stage_validation_error",
                f"Stage có {len(field_errors)} lỗi field",
                details={"field_errors": field_errors})

        creation_hash = None
        if new_case:
            creation_hash = _save_case_creation_hash(
                folded_meta,
                {"owner_row_id": owner_row_id, "people": people,
                 "assets": assets},
                state, docx_import)

        self._acquire_write_lock()
        try:
            if new_case:
                existing = self.db.query(InheritanceCase).filter(
                    InheritanceCase.workspace_idempotency_key
                    == str(idempotency_key)).first()
                if existing is not None:
                    if existing.workspace_creation_hash != creation_hash:
                        raise WorkspaceError(
                            "idempotency_conflict",
                            "idempotency_key đã dùng với nội dung khác")
                    data = self.get(existing.id)
                    data["created"] = False
                    self.db.commit()
                    return data
                case = InheritanceCase(
                    nguoi_chet_id=None,
                    tai_san_id=None,
                    ngay_lap_ho_so=meta["ngay_lap_ho_so"],
                    loai_van_ban=meta["document_type"],
                    trang_thai="draft",
                    noi_niem_yet=meta["noi_niem_yet"],
                    nguoi_nhan_uy_quyen=meta["nguoi_nhan_uy_quyen"],
                    nguoi_nhan_uy_quyen_id=meta["nguoi_nhan_uy_quyen_id"],
                    noi_dung_viec=meta["noi_dung_viec"],
                    ghi_chu=meta["ghi_chu"],
                    workspace_revision=1,
                    workspace_idempotency_key=str(idempotency_key),
                    workspace_creation_hash=creation_hash)
                self.db.add(case)
                self.db.flush()
                previous_people: list = []
                payload: dict = {"case": {
                    key: meta.get(key) for key in CASE_SCALAR_FIELDS}}
            else:
                case = self._load_case(case_id)
                fresh_type, _fresh_doc = _case_meta(case)
                if fresh_type != case_type:
                    raise WorkspaceError(
                        "workspace_conflict", "Hồ sơ đã đổi loại",
                        details={"server_revision": self._revision(case)})
                server_revision = self._revision(case)
                if base_revision != server_revision:
                    raise WorkspaceError(
                        "workspace_conflict",
                        f"Revision server hiện là {server_revision}, "
                        f"base_revision={base_revision}",
                        details={"server_revision": server_revision})
                previous = self._compose_stage(case)
                previous_people = previous.people
                payload = dict(previous.payload)
                present_scalars = {
                    key for key in CASE_SCALAR_FIELDS if key in folded_meta}
                payload["case"] = {
                    **(payload.get("case") or {}),
                    **{key: meta.get(key) for key in present_scalars},
                }
                case.ngay_lap_ho_so = meta["ngay_lap_ho_so"]
                case.noi_niem_yet = meta["noi_niem_yet"]
                case.nguoi_nhan_uy_quyen = meta["nguoi_nhan_uy_quyen"]
                case.nguoi_nhan_uy_quyen_id = \
                    meta["nguoi_nhan_uy_quyen_id"]
                case.noi_dung_viec = meta["noi_dung_viec"]
                case.ghi_chu = meta["ghi_chu"]

            previous_import = payload.get("docx_import")
            resolved_people, resolved_assets = self._write_stage_rows(
                case, {"people": people, "assets": assets})
            self._sync_links(case, resolved_assets)

            stage_view = {
                "people": [wire for _r, _e, wire in resolved_people],
                "assets": [wire for _r, _e, wire in resolved_assets],
            }
            if docx_import is not None:
                payload["docx_import"] = self._docx_context(
                    docx_import, stage_view)
            elif payload.get("docx_import") is not None:
                payload["docx_import"] = self._docx_context(
                    payload["docx_import"], stage_view)
            self.db.flush()

            valid_rows = {rid for rid, _e, _w in resolved_people}
            prepare_stage = dict(stage_view)
            if case_type == CASE_TYPE_INHERITANCE:
                prepare_stage["owner_row_id"] = owner_row_id
            previous_stage = (
                None if new_case else {"people": previous_people})
            clean_state, render_model, warnings = \
                InheritanceWorkspaceService(self.db).prepare_diagram(
                    case_type=case_type, stage=prepare_stage, state=state,
                    previous_stage=previous_stage)

            if case_type == CASE_TYPE_INHERITANCE:
                role_nodes = _project_role_nodes(
                    clean_state["nodes"], stage_view["people"])
                self._sync_participants_and_owner(
                    case, role_nodes, stage_view["people"], owner_row_id)
            else:
                case.nguoi_chet_id = None

            now = _utc_now_iso()
            case.case_state_json = json.dumps(
                self._build_payload(
                    payload, clean_state, render_model, now,
                    domain=case_type, owner_row_id=owner_row_id,
                    warnings=warnings),
                ensure_ascii=False)
            case.engine_state_json = None
            self.db.flush()

            if "docx_import" in payload:
                self._validate_docx_bindings(
                    case, payload["docx_import"], previous_import)

            case.trang_thai = "done"
            if new_case:
                new_revision = 1
            else:
                new_revision = server_revision + 1
                updated = self.db.execute(sa_text(
                    "UPDATE inheritance_cases "
                    "SET workspace_revision = :rev, updated_at = :now "
                    "WHERE id = :cid AND workspace_revision = :base"),
                    {"rev": new_revision,
                     "now": datetime.now(timezone.utc).replace(tzinfo=None),
                     "cid": case.id, "base": server_revision})
                if updated.rowcount != 1:
                    self.db.rollback()
                    fresh = self._fresh_revision(case.id, server_revision)
                    raise WorkspaceError(
                        "workspace_conflict",
                        f"Revision server hiện là {fresh}",
                        details={"server_revision": fresh})
            self.db.flush()
            self.db.commit()
        except WorkspaceError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise WorkspaceError(
                "stage_validation_error",
                "Dữ liệu vi phạm ràng buộc integrity",
                details={"field_errors": [_field_error(
                    None, "entity_id", "invalid_format",
                    "giá trị trùng/vi phạm ràng buộc duy nhất")]}) from exc
        except Exception:
            self.db.rollback()
            raise

        data = self.get(case.id)
        data["created"] = new_case
        return data

    def _acquire_write_lock(self) -> None:
        """Chiếm write reservation SQLite khi session chưa mở transaction.

        Session đã có DB transaction (caller vi phạm contract sạch) thì giữ
        CAS guarded UPDATE làm bảo vệ; busy/locked là lỗi hạ tầng retryable.
        """
        try:
            dbapi = self.db.connection().connection.dbapi_connection
            if getattr(dbapi, "in_transaction", False):
                return
            self.db.execute(sa_text("BEGIN IMMEDIATE"))
        except OperationalError as exc:
            self.db.rollback()
            raise WorkspaceError(
                "engine_unavailable",
                "Cơ sở dữ liệu đang bận; vui lòng thử lại",
                details={"retryable": True}) from exc

    # ------------------------------------------------------------- internals

    @staticmethod
    def _revision(case: InheritanceCase) -> int:
        try:
            return max(1, int(case.workspace_revision or 1))
        except (TypeError, ValueError):
            return 1

    def _fresh_revision(self, case_id: int, fallback: int) -> int:
        """Revision đọc lại sau rollback (race commit) — details cho conflict."""
        try:
            fresh = self.db.get(InheritanceCase, case_id)
            if fresh is not None:
                return max(1, int(fresh.workspace_revision or 1))
        except (TypeError, ValueError):
            pass
        return fallback

    def _load_case(self, case_id: Any) -> InheritanceCase:
        cid = _to_int(case_id)
        case = self.db.get(InheritanceCase, cid) if cid else None
        if case is None:
            raise WorkspaceError(
                "case_not_found", f"Không tìm thấy hồ sơ #{case_id}",
                details={"case_id": case_id})
        # Session có thể đang giữ bản cũ sau commit của session khác. GET
        # phải đọc bản mới nhất; expire không ghi DB và cũng buộc reload
        # person_rows/asset_rows trước khi compose.
        self.db.expire(case)
        return case

    def _load_payload(self, case: InheritanceCase) -> Optional[dict]:
        raw = _clean(case.case_state_json)
        if not raw:
            return None
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError):
            return None
        return payload if isinstance(payload, dict) else None

    # ----- compose stage from rows

    def _compose_stage(self, case: InheritanceCase) -> "_StageCompose":
        """Stage wire đọc thẳng từ rows — không fallback master/legacy JSON."""
        payload = self._load_payload(case) or {}
        stage = case_rows.read_stage(case)
        entity_to_row = {
            p["entity_id"]: p["row_id"] for p in stage["people"]
            if p["entity_id"] is not None}
        return _StageCompose(
            payload=payload, owner_row_id=stage.get("owner_row_id"),
            people=stage["people"], assets=stage["assets"],
            entity_to_row=entity_to_row)

    # ----- identity resolve + row diff

    @staticmethod
    def _person_anchor(name: Any, number: Any) -> Optional[tuple[str, str]]:
        name_key = _normalize_name_key(_clean(name))
        document_key = _normalize_document_key(_clean(number))
        if not name_key or not document_key:
            return None
        return name_key, document_key

    @staticmethod
    def _serial_anchor(serial: Any) -> Optional[str]:
        text = "" if serial is None else str(serial)
        return text if text.strip() else None

    def _resolve_person_identity(self, row: Mapping[str, Any],
                                 previous: Optional[CasePersonRow],
                                 cache: dict) -> Optional[int]:
        anchor = self._person_anchor(row.get("ho_ten"),
                                     row.get("so_giay_to"))
        if anchor is None:
            return None
        if previous is not None and previous.customer_id is not None:
            identity = self.db.get(Customer, previous.customer_id)
            if (identity is not None
                    and (identity.name_anchor, identity.document_anchor)
                    == anchor):
                return identity.id
        if anchor in cache:
            return cache[anchor]
        identity = self.db.query(Customer).filter(
            Customer.name_anchor == anchor[0],
            Customer.document_anchor == anchor[1],
        ).order_by(Customer.id.asc()).first()
        if identity is None:
            identity = Customer(
                ho_ten=_clean(row.get("ho_ten")),
                so_giay_to=_nn(row.get("so_giay_to")),
                name_anchor=anchor[0],
                document_anchor=anchor[1])
            self.db.add(identity)
            self.db.flush()
        cache[anchor] = identity.id
        return identity.id

    def _resolve_asset_identity(self, row: Mapping[str, Any],
                                previous: Optional[CaseAssetRow],
                                cache: dict) -> Optional[int]:
        anchor = self._serial_anchor(row.get("so_serial"))
        if anchor is None:
            return None
        if previous is not None and previous.property_id is not None:
            identity = self.db.get(Property, previous.property_id)
            if identity is not None and identity.so_serial == anchor:
                return identity.id
        if anchor in cache:
            return cache[anchor]
        identity = self.db.query(Property).filter(
            Property.so_serial == anchor,
        ).order_by(Property.id.asc()).first()
        if identity is None:
            identity = Property(so_serial=anchor)
            self.db.add(identity)
            self.db.flush()
        cache[anchor] = identity.id
        return identity.id

    def _write_stage_rows(self, case: InheritanceCase,
                          stage: Mapping[str, Any]) -> tuple[list, list]:
        """Diff Stage payload theo row_id → (people wires, asset wires)."""
        people_in = list(stage.get("people") or [])
        assets_in = list(stage.get("assets") or [])
        existing_people = {r.row_id: r for r in case.person_rows}
        existing_assets = {r.row_id: r for r in case.asset_rows}

        errors: list[dict] = []
        for row in people_in:
            rid = row.get("row_id")
            prev = existing_people.get(rid)
            if prev is None and self.db.get(CasePersonRow, rid) is not None:
                errors.append(_field_error(
                    rid, "row_id", "invalid_format",
                    "row_id đang thuộc hồ sơ khác"))
                continue
            allowed = prev.customer_id if prev is not None else None
            if row.get("entity_id") not in (None, allowed):
                errors.append(_field_error(
                    rid, "entity_id", "invalid_format",
                    "entity_id không phải identity đang gắn dòng này"))
        for row in assets_in:
            rid = row.get("row_id")
            prev = existing_assets.get(rid)
            if prev is None and self.db.get(CaseAssetRow, rid) is not None:
                errors.append(_field_error(
                    rid, "row_id", "invalid_format",
                    "row_id đang thuộc hồ sơ khác"))
                continue
            allowed = prev.property_id if prev is not None else None
            if row.get("entity_id") not in (None, allowed):
                errors.append(_field_error(
                    rid, "entity_id", "invalid_format",
                    "entity_id không phải identity đang gắn dòng này"))
        if errors:
            raise WorkspaceError(
                "stage_validation_error",
                f"Stage có {len(errors)} lỗi field",
                details={"field_errors": errors})

        person_cache: dict = {}
        asset_cache: dict = {}
        person_wires: list = []
        keep_people: set = set()
        for index, row in enumerate(people_in):
            rid = row["row_id"]
            keep_people.add(rid)
            previous = existing_people.get(rid)
            # Snapshot trước khi mutate: `previous` là cùng ORM object với
            # `target` khi dòng đã tồn tại. Đọc sau khi gán sẽ lấy input mới
            # làm "prev_derived" và giữ lại giá trị suy ra cũ sai.
            stored_died = previous.ngay_chet if previous is not None else None
            stored_issue = previous.ngay_cap if previous is not None else None
            stored_document = (previous.loai_giay_to
                               if previous is not None else None)
            stored_address = (previous.loai_dia_chi
                              if previous is not None else None)
            prev_derived = derive_person_fields(
                _parse_date_or_year(stored_died),
                _parse_date_or_year(stored_issue),
                stored_document, stored_address)
            entity = self._resolve_person_identity(
                row, previous, person_cache)
            target = previous
            if target is None:
                target = CasePersonRow(row_id=rid, case_id=case.id)
                self.db.add(target)
            target.customer_id = entity
            target.vitri = index + 1
            target.ho_ten = _clean(row.get("ho_ten"))
            target.gioi_tinh = _norm_gender(row.get("gioi_tinh"))
            target.ngay_sinh = _nn(row.get("ngay_sinh"))
            target.ngay_chet = _nn(row.get("ngay_chet"))
            target.so_giay_to = _nn(row.get("so_giay_to"))
            target.ngay_cap = _nn(row.get("ngay_cap"))
            target.dia_chi = _nn(row.get("dia_chi"))
            target.place_of_origin = _nn(row.get("place_of_origin"))

            current = derive_person_fields(
                _parse_date_or_year(row.get("ngay_chet")),
                _parse_date_or_year(row.get("ngay_cap")),
                row.get("loai_giay_to"), row.get("loai_dia_chi"))
            target.loai_giay_to = _resolve_derived_field(
                row.get("loai_giay_to"), stored_document,
                prev_derived[0], current[0])
            target.noi_cap = _resolve_derived_field(
                row.get("noi_cap"),
                previous.noi_cap if previous is not None else None,
                prev_derived[1], current[1])
            target.loai_dia_chi = _resolve_derived_field(
                row.get("loai_dia_chi"), stored_address,
                prev_derived[3], current[3])
            self.db.flush()
            person_wires.append((rid, entity, _row_person_wire(target)))

        asset_wires: list = []
        keep_assets: set = set()
        for index, row in enumerate(assets_in):
            rid = row["row_id"]
            keep_assets.add(rid)
            previous = existing_assets.get(rid)
            entity = self._resolve_asset_identity(row, previous, asset_cache)
            target = previous
            if target is None:
                target = CaseAssetRow(row_id=rid, case_id=case.id)
                self.db.add(target)
            target.property_id = entity
            target.vitri = index + 1
            target.so_serial = ("" if row.get("so_serial") is None
                                else str(row.get("so_serial")))
            target.so_vao_so = _nn(row.get("so_vao_so"))
            target.so_thua_dat = _nn(row.get("so_thua_dat"))
            target.so_to_ban_do = _nn(row.get("so_to_ban_do"))
            target.dia_chi = _nn(row.get("dia_chi"))
            target.loai_so = _nn(row.get("loai_so"))
            target.hinh_thuc_su_dung = _nn(row.get("hinh_thuc_su_dung"))
            target.thoi_han = _nn(row.get("thoi_han"))
            target.nguon_goc = _nn(row.get("nguon_goc"))
            target.ngay_cap = _parse_date_or_year(row.get("ngay_cap"))
            target.co_quan_cap = _nn(row.get("co_quan_cap"))
            raw_land = row.get("land_rows")
            normalized = (
                [_normalize_land_row(lr) for lr in raw_land
                 if isinstance(lr, Mapping)]
                if isinstance(raw_land, list) else None)
            target.land_rows_present = normalized is not None
            existing_land = {lr.vitri: lr for lr in target.land_rows}
            for land_index, land in enumerate(normalized or [], start=1):
                child = existing_land.get(land_index)
                if child is None:
                    child = CaseAssetLandRow(
                        case_asset_row_id=rid, vitri=land_index)
                    self.db.add(child)
                child.loaidat = land["loaidat"]
                child.dientich = land["dientich"]
                child.thoihan = land["thoihan"]
            for vitri, child in existing_land.items():
                if vitri > len(normalized or []):
                    self.db.delete(child)
            self.db.flush()
            # Collection đã cache trước khi thêm/xóa con; expire để wire
            # phản ánh đúng các vị trí vừa ghi trong cùng transaction.
            self.db.expire(target, ["land_rows"])
            asset_wires.append((rid, entity, _row_asset_wire(target)))

        for rid, row in existing_people.items():
            if rid in keep_people:
                continue
            self.db.query(InheritanceParticipant).filter(
                InheritanceParticipant.case_person_row_id == rid,
            ).delete(synchronize_session=False)
            self.db.query(InheritanceParticipant).filter(
                InheritanceParticipant.parent_case_person_row_id == rid,
            ).update({
                InheritanceParticipant.parent_case_person_row_id: None,
                InheritanceParticipant.parent_customer_id: None,
            }, synchronize_session=False)
            self.db.delete(row)

        for rid, row in existing_assets.items():
            if rid in keep_assets:
                continue
            self.db.query(InheritanceCaseProperty).filter(
                InheritanceCaseProperty.case_asset_row_id == rid,
            ).delete(synchronize_session=False)
            self.db.delete(row)

        self.db.flush()
        # Collection rows đã cache trước khi thêm dòng mới; expire để
        # consumer đọc rows trong CÙNG transaction (validate docx/Word)
        # thấy đủ dòng vừa ghi, không cần commit.
        self.db.expire(case, ["person_rows", "asset_rows"])
        return person_wires, asset_wires

    def _sync_links(self, case: InheritanceCase,
                    resolved_assets: list) -> None:
        """Link projection theo `case_asset_row_id`; `property_id` nullable,
        `is_primary` = vị trí 1."""
        links = {link.case_asset_row_id: link
                 for link in case.property_links}
        keep: set = set()
        for index, (row_id, property_id, _wire) in enumerate(resolved_assets):
            link = links.get(row_id)
            if link is None:
                link = InheritanceCaseProperty(
                    case_id=case.id, case_asset_row_id=row_id)
                self.db.add(link)
            link.property_id = property_id
            link.is_primary = index == 0
            keep.add(row_id)
        for row_id, link in links.items():
            if row_id not in keep:
                self.db.delete(link)
        case.tai_san_id = resolved_assets[0][1] if resolved_assets else None

    def _sync_participants_and_owner(self, case: InheritanceCase,
                                     role_nodes: list,
                                     people: list,
                                     owner_row_id: Optional[str]) -> None:
        """Diff participant theo `case_person_row_id`; owner projection =
        identity của owner row (có thể null)."""
        people_by_row = {p["row_id"]: p for p in people
                         if isinstance(p, Mapping) and p.get("row_id")}
        if owner_row_id is not None:
            owner = people_by_row.get(owner_row_id) or {}
            case.nguoi_chet_id = owner.get("entity_id")
        else:
            case.nguoi_chet_id = None

        active_ids = {
            _clean(n.get("personId")) for n in role_nodes
            if _clean(n.get("personId"))
            and not n.get("hidden") and not n.get("deleted")
        }
        existing = {
            p.case_person_row_id: p for p in case.participants
            if p.case_person_row_id
        }
        keep: set = set()
        for node in role_nodes:
            person_id = _clean(node.get("personId"))
            if (not person_id or node.get("hidden")
                    or node.get("deleted") or person_id == owner_row_id
                    or person_id not in active_ids or person_id in keep):
                continue
            keep.add(person_id)
            role = _clean(node.get("role")) or "Khac"
            parent_row_id = _clean(node.get("parentPersonId"))
            parent = people_by_row.get(parent_row_id) or {}
            parent_id = (parent.get("entity_id")
                         if parent_row_id in active_ids else None)
            row = existing.get(person_id)
            if row is None:
                row = InheritanceParticipant(
                    ho_so_id=case.id,
                    case_person_row_id=person_id,
                    vai_tro=role,
                    hang_thua_ke=_hang_for_role(role),
                    ty_le=0.0)
                self.db.add(row)
            else:
                role = row.vai_tro or role
                row.hang_thua_ke = _hang_for_role(role)
            row.customer_id = (people_by_row.get(person_id) or {}).get(
                "entity_id")
            row.co_nhan_tai_san = bool(node.get("willReceive", True))
            row.parent_case_person_row_id = (
                parent_row_id if parent_row_id in active_ids else None)
            row.parent_customer_id = parent_id
        for row_id, row in existing.items():
            if row_id not in keep:
                self.db.delete(row)

    # ----- diagram state

    def _state_v3(self, payload: Mapping[str, Any], *, domain: str,
                  valid_row_ids: Optional[set] = None,
                  asset_count: int = 0) -> dict:
        """Đọc `diagram.state` v4 (v3 wire) — không đọc legacy/column."""
        valid = valid_row_ids if valid_row_ids is not None else set()
        diagram = payload.get("diagram") if isinstance(
            payload.get("diagram"), Mapping) else {}
        raw_state = diagram.get("state")

        if domain == CASE_TYPE_TWO_PARTY:
            if (isinstance(raw_state, Mapping)
                    and raw_state.get("version") == DIAGRAM_STATE_VERSION
                    and raw_state.get("domain") == CASE_TYPE_TWO_PARTY
                    and isinstance(raw_state.get("nodes"), list)):
                nodes = _canonical_two_party_nodes(
                    _sanitize_two_party_nodes(raw_state["nodes"], valid))
                return {"version": DIAGRAM_STATE_VERSION,
                        "domain": CASE_TYPE_TWO_PARTY, "nodes": nodes}
            return _seed_two_party_state()

        if (isinstance(raw_state, Mapping)
                and raw_state.get("version") == DIAGRAM_STATE_VERSION
                and isinstance(raw_state.get("nodes"), list)):
            nodes = _sanitize_v3_nodes(raw_state["nodes"], valid)
            return {"version": DIAGRAM_STATE_VERSION,
                    "domain": CASE_TYPE_INHERITANCE, "nodes": nodes}

        return {"version": DIAGRAM_STATE_VERSION,
                "domain": CASE_TYPE_INHERITANCE, "nodes": []}

    @staticmethod
    def _render_model(payload: Mapping[str, Any]) -> Optional[dict]:
        diagram = payload.get("diagram") if isinstance(
            payload.get("diagram"), Mapping) else {}
        model = diagram.get("render_model")
        return dict(model) if isinstance(model, Mapping) else None

    # ----- owner_row_id (§13.6)

    @staticmethod
    def _resolve_owner_row_id(payload: Mapping[str, Any],
                              state: Mapping[str, Any],
                              valid_rows: set) -> Optional[str]:
        """owner_row_id đã committed → fallback personId node owner → null."""
        oid = payload.get("owner_row_id")
        if _is_uuid4(oid) and oid in valid_rows:
            return oid
        for n in (state or {}).get("nodes") or []:
            if (n.get("id") == "owner" and n.get("deleted") is not True
                    and n.get("personId") in valid_rows):
                return n["personId"]
        return None

    @staticmethod
    def _validate_owner_pointer(stage: Mapping[str, Any],
                                people: list,
                                case_type: str) -> Optional[str]:
        """owner_row_id: bắt buộc + trỏ row có thật với inheritance; CẤM
        (kể cả null) với two_party (§13.5/§13.6)."""
        if case_type == CASE_TYPE_TWO_PARTY:
            if "owner_row_id" in stage:
                raise WorkspaceError(
                    "validation_error",
                    "stage.owner_row_id cấm với case_type two_party")
            return None
        oid = stage.get("owner_row_id")
        people_ids = {r.get("row_id") for r in people
                      if isinstance(r, Mapping)}
        if not (_is_uuid4(oid) and oid in people_ids):
            raise WorkspaceError(
                "workspace_owner_required",
                "stage.owner_row_id phải là row_id của một dòng Người "
                "trong stage (inheritance)")
        return oid

    # ----- validation

    def _resolve_auth_recipient(self, case_meta: Mapping[str, Any]) -> dict:
        """`nguoi_nhan_uy_quyen` + `nguoi_nhan_uy_quyen_id` → (id, ten)."""
        uq_id = case_meta.get("nguoi_nhan_uy_quyen_id")
        uq_name = _nn(case_meta.get("nguoi_nhan_uy_quyen"))
        customer = None
        if uq_id is not None:
            if (not isinstance(uq_id, int) or isinstance(uq_id, bool)
                    or uq_id < 1):
                raise WorkspaceError(
                    "validation_error",
                    "nguoi_nhan_uy_quyen_id phải là số nguyên ≥ 1 hoặc null")
            customer = self.db.get(Customer, uq_id)
            if customer is None:
                raise WorkspaceError(
                    "validation_error",
                    f"nguoi_nhan_uy_quyen_id {uq_id} không tồn tại "
                    "trong danh bạ")
        if customer is not None:
            if uq_name is not None and uq_name != customer.ho_ten:
                raise WorkspaceError(
                    "validation_error",
                    "nguoi_nhan_uy_quyen và nguoi_nhan_uy_quyen_id "
                    "mâu thuẫn nhau")
            uq_name = customer.ho_ten
        return {"id": customer.id if customer is not None else None,
                "ten": uq_name}

    def _validate_case_meta(self, case_meta: Any, *,
                            require_type: bool = True) -> dict:
        if not isinstance(case_meta, Mapping):
            raise WorkspaceError(
                "validation_error", "payload.case phải là object")
        case_meta = _fold_key_aliases(
            case_meta, _CASE_META_KEY_ALIASES, "payload.case")
        _check_extra_keys(case_meta, {
            "case_type", "document_type", "ngay_lap_ho_so",
            "noi_niem_yet", "nguoi_nhan_uy_quyen", "nguoi_nhan_uy_quyen_id",
            "noi_dung_viec", "ghi_chu", *CASE_SCALAR_FIELDS}, "payload.case")
        case_type = case_meta.get("case_type", CASE_TYPE_INHERITANCE)
        if case_type not in CASE_TYPES:
            raise WorkspaceError(
                "validation_error",
                f"case_type phải ∈ {list(CASE_TYPES)}")
        document_type = case_meta.get("document_type")
        allowed = (DOCUMENT_TYPES_TWO_PARTY
                   if case_type == CASE_TYPE_TWO_PARTY else DOCUMENT_TYPES)
        if document_type is None and not require_type:
            pass
        elif document_type not in allowed:
            raise WorkspaceError(
                "validation_error",
                f"document_type phải ∈ {list(allowed)}")
        ngay = case_meta.get("ngay_lap_ho_so")
        if not _valid_date_full(ngay):
            raise WorkspaceError(
                "validation_error",
                "ngay_lap_ho_so phải là YYYY-MM-DD hoặc null")
        for field in ("noi_niem_yet", "nguoi_nhan_uy_quyen",
                      "noi_dung_viec", "ghi_chu"):
            value = case_meta.get(field)
            if value is not None and (
                    not isinstance(value, str) or not value.strip()):
                raise WorkspaceError(
                    "validation_error",
                    f"{field} phải là chuỗi non-empty hoặc null")
        auth = self._resolve_auth_recipient(case_meta)
        canonical_meta = {}
        for field in CASE_SCALAR_FIELDS:
            if field not in case_meta:
                continue
            value = case_meta[field]
            if value is not None and (
                    not isinstance(value, str) or not value.strip()):
                raise WorkspaceError(
                    "validation_error",
                    f"{field}: chuỗi không rỗng hoặc null")
            if field == "ngaycongchung" and not _valid_date_full(value):
                raise WorkspaceError(
                    "validation_error",
                    "ngaycongchung: YYYY-MM-DD hoặc null")
            if (field == "socongchung" and value is not None
                    and not re.fullmatch(r"\d+/\d{4}", value)):
                raise WorkspaceError(
                    "validation_error", "socongchung: xxx/yyyy hoặc null")
            canonical_meta[field] = value
        return {
            "case_type": case_type,
            "document_type": document_type,
            "ngay_lap_ho_so": _parse_date_or_year(ngay),
            "noi_niem_yet": _nn(case_meta.get("noi_niem_yet")),
            "nguoi_nhan_uy_quyen": auth["ten"],
            "nguoi_nhan_uy_quyen_id": auth["id"],
            "noi_dung_viec": _nn(case_meta.get("noi_dung_viec")),
            "ghi_chu": _nn(case_meta.get("ghi_chu")),
            **canonical_meta,
        }

    @staticmethod
    def _validate_create_stage(people: list, assets: list) -> list[dict]:
        """Rule riêng của `workspace_create` vòng 1 (§13.6): stage non-empty
        và mọi `entity_id` phải null — backend tự resolve identity."""
        errors: list[dict] = []
        if not people:
            errors.append(_field_error(
                None, "people", "required",
                "stage.people phải có ít nhất một dòng"))
        if not assets:
            errors.append(_field_error(
                None, "assets", "required",
                "stage.assets phải có ít nhất một dòng"))
        for index, row in enumerate(people):
            if isinstance(row, Mapping) and row.get("entity_id") is not None:
                errors.append(_field_error(
                    row.get("row_id"), "entity_id", "invalid_format",
                    "entity_id phải null — workspace_create tạo entity mới",
                    index))
        for index, row in enumerate(assets):
            if isinstance(row, Mapping) and row.get("entity_id") is not None:
                errors.append(_field_error(
                    row.get("row_id"), "entity_id", "invalid_format",
                    "entity_id phải null — workspace_create tạo entity mới",
                    index))
        return errors

    def _validate_stage(self, people: list, assets: list,
                        case_type: str = CASE_TYPE_INHERITANCE) -> list[dict]:
        """Field-level rules của stage_v2 (validation vòng 1 giữ nguyên).

        Duplicate entity không còn là lỗi: hai dòng row_id khác nhau có
        thể cùng identity (§4.2 step 6).
        """
        errors: list[dict] = []

        def err(row_id, field, code, message, index=None):
            errors.append(_field_error(row_id, field, code, message, index))

        for row in people:
            if isinstance(row, Mapping):
                _check_extra_keys(row, _PERSON_FIELD_SET, "person_row")
        for row in assets:
            if isinstance(row, Mapping):
                _check_extra_keys(row, _ASSET_FIELD_SET, "asset_row")

        seen_row_ids: set = set()

        for index, row in enumerate(people):
            if not isinstance(row, Mapping):
                err(None, "row", "invalid_type",
                    f"people[{index}] phải là object", index)
                continue
            row_id = row.get("row_id")
            emit = lambda f, c, m, _i=index: err(row_id, f, c, m, _i)
            self._check_row_id(row_id, seen_row_ids, emit)
            entity = row.get("entity_id")
            if entity is not None and (
                    not isinstance(entity, int) or isinstance(entity, bool)
                    or entity < 1):
                emit("entity_id", "invalid_type",
                     "entity_id phải là số nguyên ≥ 1 hoặc null")
            ho_ten = row.get("ho_ten")
            if not isinstance(ho_ten, str) or not ho_ten.strip():
                emit("ho_ten", "required", "ho_ten bắt buộc")
            if row.get("gioi_tinh") not in (None, *_GENDER_VALUES):
                emit("gioi_tinh", "invalid_enum",
                     "gioi_tinh ∈ {Nam, Nữ, null}")
            for field in ("ngay_sinh", "ngay_chet", "ngay_cap"):
                if not _valid_date_or_year(row.get(field)):
                    emit(field, "invalid_date",
                         f"{field} phải là YYYY-MM-DD | YYYY | null")
            for field in ("so_giay_to", "noi_cap", "dia_chi",
                          "place_of_origin", "loai_giay_to",
                          "loai_dia_chi"):
                self._check_nullable_str(row, field, emit)

        for index, row in enumerate(assets):
            if not isinstance(row, Mapping):
                err(None, "row", "invalid_type",
                    f"assets[{index}] phải là object", index)
                continue
            row_id = row.get("row_id")
            emit = lambda f, c, m, _i=index: err(row_id, f, c, m, _i)
            self._check_row_id(row_id, seen_row_ids, emit)
            entity = row.get("entity_id")
            if entity is not None and (
                    not isinstance(entity, int) or isinstance(entity, bool)
                    or entity < 1):
                emit("entity_id", "invalid_type",
                     "entity_id phải là số nguyên ≥ 1 hoặc null")
            serial = row.get("so_serial")
            if not isinstance(serial, str):
                emit("so_serial", "invalid_type",
                     "so_serial phải là chuỗi")
            # §3.3 design vòng 1: địa chỉ tài sản nullable — dòng thiếu dữ
            # kiện vẫn lưu được; chuỗi rỗng chuẩn hóa thành null khi ghi.
            self._check_nullable_str(row, "dia_chi", emit)
            if not _valid_date_full(row.get("ngay_cap")):
                emit("ngay_cap", "invalid_date",
                     "ngay_cap phải là YYYY-MM-DD hoặc null")
            for field in ("so_vao_so", "so_thua_dat", "so_to_ban_do",
                          "loai_so", "hinh_thuc_su_dung", "thoi_han",
                          "nguon_goc", "co_quan_cap"):
                self._check_nullable_str(row, field, emit)
            land_rows = row.get("land_rows")
            if land_rows is not None:
                if not isinstance(land_rows, list):
                    emit("land_rows", "invalid_type",
                         "land_rows phải là danh sách hoặc null")
                else:
                    for lr_index, lr in enumerate(land_rows):
                        if not isinstance(lr, Mapping):
                            emit("land_rows", "invalid_type",
                                 f"land_rows[{lr_index}] phải là object")
                            continue
                        _check_extra_keys(lr, _LAND_ROW_KEY_SET,
                                          f"land_rows[{lr_index}]")
                        for lf in _LAND_ROW_STR_KEYS:
                            value = lr.get(lf)
                            if value is not None and not isinstance(value, str):
                                emit("land_rows", "invalid_type",
                                     f"land_rows[{lr_index}].{lf} phải là chuỗi hoặc null")
                        for lf in _LAND_ROW_NUM_KEYS:
                            dt = lr.get(lf)
                            if dt is not None and (
                                    not isinstance(dt, (int, float))
                                    or isinstance(dt, bool)):
                                emit("land_rows", "invalid_type",
                                     f"land_rows[{lr_index}].{lf} phải là số hoặc null")
                        for new_key, old_key in (
                                ("loaidat", "loai_dat"),
                                ("dientich", "dien_tich"),
                                ("thoihan", "thoi_han")):
                            _lv, conflict = _land_row_field(
                                lr, new_key, old_key)
                            if conflict:
                                emit("land_rows", "conflict",
                                     f"land_rows[{lr_index}] '{new_key}' "
                                     f"và '{old_key}' có giá trị mâu thuẫn")
                    for lr_index in range(MAX_LAND_ROWS, len(land_rows)):
                        emit("land_rows", "land_row_limit",
                             f"land_rows[{lr_index}] vượt giới hạn "
                             f"{MAX_LAND_ROWS} cụm đất mỗi tài sản")

        for index, row in enumerate(assets[MAX_ASSETS:], start=MAX_ASSETS):
            err(row.get("row_id") if isinstance(row, Mapping) else None,
                "assets", "asset_limit",
                f"stage.assets tối đa {MAX_ASSETS} (v2)", index)
        if case_type == CASE_TYPE_TWO_PARTY:
            for index, row in enumerate(
                    people[MAX_PEOPLE_TWO_PARTY:],
                    start=MAX_PEOPLE_TWO_PARTY):
                err(row.get("row_id") if isinstance(row, Mapping) else None,
                    "people", "people_limit",
                    f"stage.people tối đa {MAX_PEOPLE_TWO_PARTY} "
                    "với two_party", index)
        return errors

    @staticmethod
    def _check_row_id(row_id: Any, seen: set, emit) -> None:
        if not isinstance(row_id, str) or not row_id.strip():
            emit("row_id", "required", "row_id bắt buộc")
        elif not _is_uuid4(row_id):
            emit("row_id", "invalid_format", "row_id phải là UUID v4")
        elif row_id in seen:
            emit("row_id", "duplicate_row_id",
                 "row_id trùng trong payload")
        else:
            seen.add(row_id)

    @staticmethod
    def _check_nullable_str(row: Mapping[str, Any], field: str, emit) -> None:
        value = row.get(field)
        if value is not None and not isinstance(value, str):
            emit(field, "invalid_type", f"{field} phải là chuỗi hoặc null")
        elif isinstance(value, str) and not value.strip():
            emit(field, "invalid_format",
                 f"{field} rỗng — dùng null thay chuỗi rỗng")

    # ----- persist committed payload

    @staticmethod
    def _landowner_names(payload: dict) -> Optional[str]:
        from services.word_engine import committed_landowner_names
        return committed_landowner_names(payload)

    def _build_payload(self, payload: Mapping[str, Any],
                       state: dict, render_model: Optional[dict],
                       now: str, *, domain: str,
                       owner_row_id: Optional[str],
                       warnings: Optional[list] = None) -> dict:
        """JSON v4: chỉ owner_row_id/case scalar/Diagram/docx_import."""
        scalars = payload.get("case")
        scalars = scalars if isinstance(scalars, Mapping) else {}
        out: dict = {
            "schemaVersion": PAYLOAD_SCHEMA_VERSION,
            "case": {key: scalars.get(key) for key in CASE_SCALAR_FIELDS},
            "diagram": {
                "state": state,
                "render_model": render_model,
                "updatedAt": now,
            },
        }
        if warnings:
            out["diagram"]["warnings"] = list(warnings)
        if domain == CASE_TYPE_INHERITANCE:
            out["owner_row_id"] = owner_row_id
        if "docx_import" in payload:
            out["docx_import"] = payload["docx_import"]
        return out


class _StageCompose:
    """Stage wire đọc từ rows — không giữ cờ migrate/persist legacy."""

    __slots__ = ("payload", "owner_row_id", "people", "assets",
                 "entity_to_row")

    def __init__(self, payload, owner_row_id, people, assets,
                 entity_to_row):
        self.payload = payload
        self.owner_row_id = owner_row_id
        self.people = people
        self.assets = assets
        self.entity_to_row = entity_to_row


# ------------------------------------------------------------- identity keys


def _normalize_name_key(value: str) -> Optional[str]:
    """Unicode NFD → bỏ Mn → đ/Đ → d/D → lower → gộp whitespace."""
    if not value:
        return None
    text = unicodedata.normalize("NFD", value)
    text = "".join(ch for ch in text
                   if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "D")
    return " ".join(text.lower().split()) or None


def _normalize_document_key(value: str) -> Optional[str]:
    """Số giấy đúng 12 chữ số (bỏ dấu chấm/space) → 12 số; còn lại trim."""
    if not value:
        return None
    if re.fullmatch(r"[\d.\s]+", value):
        digits = re.sub(r"[.\s]", "", value)
        if len(digits) == 12 and digits.isdigit():
            return digits
    return value


# ------------------------------------------------------------- land helpers


def _normalize_land_row(row: Mapping[str, Any]) -> dict:
    """land_row wire → canonical {loaidat, dientich, thoihan}."""
    loaidat, _ = _land_row_field(row, "loaidat", "loai_dat")
    dientich, _ = _land_row_field(row, "dientich", "dien_tich")
    thoihan, _ = _land_row_field(row, "thoihan", "thoi_han")
    return {
        "loaidat": _nn(loaidat),
        "dientich": (float(dientich)
                     if isinstance(dientich, (int, float))
                     and not isinstance(dientich, bool) else None),
        "thoihan": _nn(thoihan),
    }


def _land_rows_wire(rows: Optional[list]) -> Optional[list]:
    """Canonical {loaidat,dientich,thoihan} → key wire legacy §4.2."""
    if rows is None:
        return None
    return [{"loai_dat": r["loaidat"], "dien_tich": r["dientich"],
             "thoi_han": r["thoihan"]} for r in rows]


def _row_person_wire(row: CasePersonRow) -> dict:
    return {
        "row_id": row.row_id,
        "entity_id": row.customer_id,
        "ho_ten": row.ho_ten,
        "gioi_tinh": row.gioi_tinh,
        "ngay_sinh": row.ngay_sinh,
        "ngay_chet": row.ngay_chet,
        "so_giay_to": row.so_giay_to,
        "ngay_cap": row.ngay_cap,
        "noi_cap": row.noi_cap,
        "dia_chi": row.dia_chi,
        "place_of_origin": row.place_of_origin,
        "loai_giay_to": row.loai_giay_to,
        "loai_dia_chi": row.loai_dia_chi,
    }


def _row_asset_wire(row: CaseAssetRow) -> dict:
    land_rows = None
    if row.land_rows_present:
        land_rows = _land_rows_wire([
            {"loaidat": lr.loaidat, "dientich": lr.dientich,
             "thoihan": lr.thoihan}
            for lr in sorted(row.land_rows, key=lambda x: x.vitri)])
    return {
        "row_id": row.row_id,
        "entity_id": row.property_id,
        "so_serial": row.so_serial if row.so_serial is not None else "",
        "so_vao_so": row.so_vao_so,
        "so_thua_dat": row.so_thua_dat,
        "so_to_ban_do": row.so_to_ban_do,
        "dia_chi": row.dia_chi,
        "loai_so": row.loai_so,
        "hinh_thuc_su_dung": row.hinh_thuc_su_dung,
        "thoi_han": row.thoi_han,
        "nguon_goc": row.nguon_goc,
        "ngay_cap": _emit_date_or_year(row.ngay_cap),
        "co_quan_cap": row.co_quan_cap,
        "land_rows": land_rows,
    }


def _prune_positions(nodes: list[dict], asset_count: int) -> int:
    """Bỏ dấu chọn tới vị trí > len(assets) trong same transaction."""
    pruned = 0
    for node in nodes or []:
        for key in ("ownPositions", "receivePositions"):
            arr = node.get(key)
            if not isinstance(arr, list):
                continue
            kept = [x for x in arr
                    if isinstance(x, int) and not isinstance(x, bool)
                    and 1 <= x <= max(asset_count, 0)]
            if len(kept) != len(arr):
                pruned += len(arr) - len(kept)
                node[key] = kept
    return pruned


def _sync_owner_node(nodes: list[dict], owner_row_id: Optional[str]) -> None:
    """§13.6: commit stage đồng bộ node `owner` (không deleted)."""
    for node in nodes or []:
        if node.get("id") == "owner" and node.get("deleted") is not True:
            node["personId"] = owner_row_id
            return


def _hang_for_role(role: str) -> int:
    if role in ("Cha", "Mẹ", "Cha_vc", "Me_vc", "Vợ/Chồng", "Con",
                "Cháu", "Con_dau_re"):
        return 1
    if role in ("Ông/Bà", "Anh/Chị/Em"):
        return 2
    return 1


def _creation_hash(case_meta: Any, stage: Any, state: Any,
                   docx_import: Any) -> str:
    """SHA-256 canonical JSON của payload tạo (gồm command/ý định)."""
    canonical = {
        "command": "workspace_create",
        "intent": "draft",
        "case": case_meta,
        "stage": stage,
        "diagram": state,
        "docx_import": docx_import,
    }
    raw = json.dumps(canonical, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _save_case_creation_hash(case_meta: Any, stage: Any, state: Any,
                             docx_import: Any) -> str:
    """SHA-256 canonical payload Lưu hồ sơ — khác hash create draft cùng
    nội dung nhờ command/intent (§13.11/§13.19)."""
    canonical = {
        "command": "workspace_save_case",
        "intent": "done",
        "case": case_meta,
        "stage": stage,
        "diagram": state,
        "docx_import": docx_import,
    }
    raw = json.dumps(canonical, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z")

"""Case workspace service — backend thật cho contract notary.case-drafting.v1.

Sở hữu business rule của `notary.workspace_get` và
`notary.workspace_commit_stage`; sidecar handlers chỉ dịch payload ↔ service,
không chứa nghiệp vụ (MIN-107).

Persisted state — `inheritance_cases.case_state_json`::

    {"schemaVersion": 2,
     "stage":  [{"id": "<entity_id>", "row_id": "<uuid4>", ...field snapshot}],
     "assets": [{"id": "<entity_id>", "row_id": "<uuid4>", "is_primary": bool}],
     "diagram": {"state": {"version": 2, "nodes": [<diagram_node>]},
                "render_model": <engine output | null>,
                "engineState"/"engineInput"/"engineResult"/"assignments":
                    projection legacy cho web cũ}}

Migrate-on-read: payload cũ (không `row_id`, legacy `engineState`/`assignments`,
hoặc thiếu `case_state_json`) được normalize + ghi lại ngay trong `get()` để
`row_id` UUIDv4 ổn định qua reload. `diagram.state` trên wire luôn là V2
(`parentSlotIds`/`spouseSlotId`); `personId` trỏ `row_id` của Stage đã commit.
"""
from __future__ import annotations

import json
import re
import uuid
from collections.abc import Mapping
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import text as sa_text
from sqlalchemy.exc import IntegrityError, OperationalError

from models import (
    Customer,
    InheritanceCase,
    InheritanceCaseProperty,
    InheritanceParticipant,
    Property,
)
from services.inheritance_engine import run_inheritance_case


SCHEMA_VERSION = "notary.case-drafting.v1"
CASE_TYPE_INHERITANCE = "inheritance"
DOCUMENT_TYPES = ("khai_nhan", "thoa_thuan")
INTAKE_KINDS = ["image", "pdf", "docx", "xlsx", "text"]

_UUID4_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}"
    r"-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
_DATE_OR_YEAR_RE = re.compile(r"^\d{4}(-\d{2}-\d{2})?$")
_DATE_FULL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SERIAL_RE = re.compile(r"^[A-Z]{2}\d{6,8}$")
_GENDER_VALUES = ("Nam", "Nữ")
_BIRTH_PARENT_IDS = ("father", "mother")
_SPOUSE_PARENT_IDS = ("spouse_father", "spouse_mother")
_BIRTH_PARENT_ROLES = ("Cha", "Mẹ")
_SPOUSE_PARENT_ROLES = ("Cha_vc", "Me_vc")
_SPOUSE_RELATIONS = ("spouse", "branchSpouse")
_GHOST_KINDS = ("ghost", "pendingspouse")
_PLACEHOLDER_ROW_ID = "00000000-0000-4000-8000-000000000000"


class WorkspaceError(Exception):
    """Lỗi nghiệp vụ có `code`/`details` theo contract §9."""

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


def _canonical_serial(value: Any) -> Optional[str]:
    text = _clean(value)
    if not text:
        return None
    candidate = re.sub(r"[^0-9A-Za-z]", "", text).upper()
    return candidate if _SERIAL_RE.match(candidate) else None


def _case_meta(case: InheritanceCase) -> tuple[str, str]:
    """(case_type, document_type) — loai_van_ban là discriminator hiện có.

    `document_type` enum contract: khai_nhan|thoa_thuan. Giá trị khác →
    case_type != "inheritance" (capabilities tắt / write bị chặn).
    """
    loai = _clean(case.loai_van_ban)
    document_type = loai if loai in DOCUMENT_TYPES else "khai_nhan"
    case_type = CASE_TYPE_INHERITANCE if loai in DOCUMENT_TYPES else (
        loai or "unknown")
    return case_type, document_type


def _field_error(row_id: Any, field: str, code: str, message: str,
                 index: Optional[int] = None) -> dict:
    """Field error theo contract §9; row_id không hợp lệ → placeholder uuid4
    + `row index` trong message để correlate về dòng payload."""
    valid = _is_uuid4(row_id)
    if not valid and index is not None:
        message = f"{message} (row index {index})"
    return {
        "row_id": row_id if valid else _PLACEHOLDER_ROW_ID,
        "field": field,
        "code": code,
        "message": message,
    }


def _person_contract_keys() -> tuple[str, ...]:
    return ("row_id", "entity_id", "ho_ten", "gioi_tinh", "ngay_sinh",
            "ngay_chet", "so_giay_to", "ngay_cap", "noi_cap", "dia_chi",
            "place_of_origin")


def _asset_contract_keys() -> tuple[str, ...]:
    return ("row_id", "entity_id", "is_primary", "so_serial", "so_vao_so",
            "so_thua_dat", "so_to_ban_do", "dia_chi", "loai_so",
            "hinh_thuc_su_dung", "thoi_han", "nguon_goc", "ngay_cap",
            "co_quan_cap", "land_rows")


# ------------------------------------------------------- legacy → V2 diagram


def _legacy_person_entity(node: Mapping[str, Any]) -> Optional[int]:
    pid = node.get("personId")
    if pid is None:
        person = node.get("person")
        pid = person.get("id") if isinstance(person, Mapping) else None
    return _to_int(pid)


def _legacy_to_v2(raw_nodes: Any,
                  entity_to_row: Mapping[int, str]) -> list[dict]:
    """Chuyển node legacy (engineState/engineInput/engine_state_json) → V2.

    Node person trỏ entity_id ngoài Stage → bỏ node; quan hệ suy ra từ
    relationType/role/familyGroupId theo semantics diagram_edges.js.
    """
    raw_by_id: dict[str, dict] = {}
    order: list[str] = []
    for raw in raw_nodes or []:
        if not isinstance(raw, Mapping):
            continue
        node_id = _clean(raw.get("id"))
        if not node_id or node_id in raw_by_id:
            continue
        kind = _clean(raw.get("kind")).lower() or "person"
        if kind in _GHOST_KINDS:
            continue
        raw_by_id[node_id] = dict(raw)
        order.append(node_id)

    def is_birth_parent(node: Mapping[str, Any]) -> bool:
        return (
            node.get("id") in _BIRTH_PARENT_IDS
            or _clean(node.get("relationType")) == "parent"
            or _clean(node.get("role")) in _BIRTH_PARENT_ROLES
        )

    def is_spouse_parent(node: Mapping[str, Any]) -> bool:
        return (
            node.get("id") in _SPOUSE_PARENT_IDS
            or _clean(node.get("relationType")) == "spouseParent"
            or _clean(node.get("role")) in _SPOUSE_PARENT_ROLES
        )

    person_to_node: dict[int, str] = {}
    for nid in order:
        entity = _legacy_person_entity(raw_by_id[nid])
        if entity is not None and entity not in person_to_node:
            person_to_node[entity] = nid

    # anchor node id → node vợ/chồng gắn vào nó (relationType spouse/branchSpouse)
    spouse_of: dict[str, str] = {}
    for nid in order:
        node = raw_by_id[nid]
        if _clean(node.get("relationType")) not in _SPOUSE_RELATIONS:
            continue
        anchor = _clean(node.get("spouseOf"))
        if not anchor:
            anchor = "owner" if nid == "spouse" else _clean(
                node.get("parentSlotId") or node.get("sourceId"))
        if anchor in raw_by_id and anchor not in spouse_of:
            spouse_of[anchor] = nid

    birth_parents = [
        nid for nid in _BIRTH_PARENT_IDS if nid in raw_by_id
    ] + [
        nid for nid in order
        if nid not in _BIRTH_PARENT_IDS and is_birth_parent(raw_by_id[nid])
    ]
    spouse_parents = [
        nid for nid in _SPOUSE_PARENT_IDS if nid in raw_by_id
    ] + [
        nid for nid in order
        if nid not in _SPOUSE_PARENT_IDS and is_spouse_parent(raw_by_id[nid])
    ]
    owner_spouse_id = spouse_of.get("owner")
    owner_pair = [x for x in ("owner", owner_spouse_id)
                  if x and x in raw_by_id]

    def sibling_family(node: Mapping[str, Any]) -> str:
        explicit = _clean(node.get("familyGroupId"))
        if explicit:
            return explicit
        anchor = _clean(node.get("parentSlotId") or node.get("sourceId"))
        target = raw_by_id.get(anchor)
        if target is None:
            parent_entity = _to_int(node.get("parentPersonId"))
            target = raw_by_id.get(person_to_node.get(parent_entity or -1))
        if target is not None:
            if is_birth_parent(target):
                return "birthParents"
            if is_spouse_parent(target):
                return "spouseParents"
        return "ambiguousSibling"

    def paired(nid: str, first: str, second: str) -> Optional[str]:
        if nid == first and second in raw_by_id:
            return second
        if nid == second and first in raw_by_id:
            return first
        return None

    out: list[dict] = []
    for nid in order:
        node = raw_by_id[nid]
        entity = _legacy_person_entity(node)
        if entity is not None and entity not in entity_to_row:
            continue  # person ngoài Stage đã commit → bỏ node
        rel = _clean(node.get("relationType"))
        parents: list[str] = []
        spouse: Optional[str] = None
        if rel == "owner" or nid == "owner":
            parents = [x for x in birth_parents if x != nid]
            spouse = spouse_of.get(nid)
        elif rel == "spouse":
            parents = spouse_parents
            anchor = _clean(node.get("spouseOf"))
            if not anchor:
                anchor = "owner" if nid == "spouse" else _clean(
                    node.get("parentSlotId") or node.get("sourceId"))
            spouse = anchor if anchor in raw_by_id else None
        elif rel == "branchSpouse":
            anchor = _clean(node.get("spouseOf")) or _clean(
                node.get("parentSlotId") or node.get("sourceId"))
            spouse = anchor if anchor in raw_by_id else None
        elif rel == "child":
            parents = owner_pair
        elif rel == "sibling":
            family = sibling_family(node)
            if family == "birthParents":
                parents = birth_parents
            elif family == "spouseParents":
                parents = spouse_parents
        elif rel == "grandchild":
            parent_slot = _clean(node.get("parentSlotId"))
            if parent_slot in raw_by_id:
                parents = [parent_slot]
                branch_spouse = spouse_of.get(parent_slot)
                if branch_spouse:
                    parents.append(branch_spouse)
        elif is_birth_parent(node):
            spouse = paired(nid, *_BIRTH_PARENT_IDS)
        elif is_spouse_parent(node):
            spouse = paired(nid, *_SPOUSE_PARENT_IDS)
        else:
            spouse = spouse_of.get(nid)
        out.append({
            "id": nid,
            "personId": entity_to_row.get(entity) if entity is not None else None,
            "parentSlotIds": [p for p in parents if p in raw_by_id][:2],
            "spouseSlotId": spouse if spouse in raw_by_id else None,
            "isLandOwner": _coerce_bool(node.get("isLandOwner"), False),
            "willReceive": _coerce_bool(node.get("willReceive"), True),
            "hidden": _coerce_bool(node.get("hidden"), False),
            "deleted": _coerce_bool(node.get("deleted"), False),
        })
    return _scrub_v2_links(out)


def _assignments_to_v2(assignments: Mapping[str, Any],
                       entity_to_row: Mapping[int, str]) -> list[dict]:
    """Fallback: {slot_id: entity_id} → V2 nodes (kinship theo slot cố định)."""
    out: list[dict] = []
    for slot, raw_entity in (assignments or {}).items():
        nid = _clean(slot)
        if not nid:
            continue
        entity = _to_int(raw_entity)
        if entity is not None and entity not in entity_to_row:
            continue
        out.append({
            "id": nid,
            "personId": entity_to_row.get(entity) if entity else None,
            "parentSlotIds": [],
            "spouseSlotId": None,
            "isLandOwner": False,
            "willReceive": True,
            "hidden": False,
            "deleted": False,
        })
    by_id = {n["id"]: n for n in out}
    if "owner" in by_id:
        by_id["owner"]["parentSlotIds"] = [
            x for x in _BIRTH_PARENT_IDS if x in by_id]
    if "spouse" in by_id:
        by_id["spouse"]["parentSlotIds"] = [
            x for x in _SPOUSE_PARENT_IDS if x in by_id]
        if "owner" in by_id:
            by_id["spouse"]["spouseSlotId"] = "owner"
            by_id["owner"]["spouseSlotId"] = "spouse"
    for first, second in (_BIRTH_PARENT_IDS, _SPOUSE_PARENT_IDS):
        if first in by_id and second in by_id:
            by_id[first]["spouseSlotId"] = second
            by_id[second]["spouseSlotId"] = first
    return _scrub_v2_links(out)


def _scrub_v2_links(nodes: list[dict]) -> list[dict]:
    ids = {n["id"] for n in nodes}
    for node in nodes:
        node["parentSlotIds"] = [p for p in node["parentSlotIds"] if p in ids]
        if node["spouseSlotId"] and node["spouseSlotId"] not in ids:
            node["spouseSlotId"] = None
    return nodes


def _sanitize_v2_nodes(raw_nodes: Any, valid_row_ids: set) -> list[dict]:
    """Normalize node V2 đã persist; bỏ node trỏ personId ngoài Stage."""
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
            "isLandOwner": _coerce_bool(raw.get("isLandOwner"), False),
            "willReceive": _coerce_bool(raw.get("willReceive"), True),
            "hidden": _coerce_bool(raw.get("hidden"), False),
            "deleted": _coerce_bool(raw.get("deleted"), False),
        })
    return _scrub_v2_links(out)


def _parent_role(node_id: str, info: Mapping[str, Any],
                 male_role: str, female_role: str) -> str:
    """Role cho slot cha/mẹ (và bên vợ/chồng) — id cố định trước, gender sau."""
    if node_id in ("father", "spouse_father"):
        return male_role
    if node_id in ("mother", "spouse_mother"):
        return female_role
    return female_role if _clean(info.get("gioi_tinh")) == "Nữ" else male_role


def _v2_to_legacy_nodes(nodes: list[dict],
                        people_map: Mapping[str, Mapping[str, Any]]) -> list[dict]:
    """Projection ngược V2 → legacy cho web cũ (engineState/engineInput/
    engine_state_json column/assignments) — inverse của `_legacy_to_v2`.

    `people_map`: {row_id: {"entity": int|None, "ho_ten": str,
    "gioi_tinh": str|None}}. Derive đủ `role`/`relationType`/`parentSlotId`/
    `spouseOf`/`familyGroupId`/`label` để `diagram_edges.js`,
    `_extract_diagram_participants` và `word_engine` đọc đúng semantics —
    node rỗng semantics vẫn emit (kind person, role "") → normalize về "Khac".
    """
    nodes = [n for n in (nodes or []) if isinstance(n, Mapping)]
    by_id = {n["id"]: n for n in nodes}

    def entity_of(node: Mapping[str, Any]) -> Optional[int]:
        info = people_map.get(node.get("personId"))
        return info.get("entity") if info else None

    def info_of(node: Mapping[str, Any]) -> Mapping[str, Any]:
        return people_map.get(node.get("personId")) or {}

    owner = by_id.get("owner")
    owner_spouse = _clean(owner.get("spouseSlotId")) if owner else ""
    if owner_spouse not in by_id:
        # asymmetric link: chỉ phía spouse trỏ về owner
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
        entity = entity_of(node)
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
        # parentPersonId chỉ cho liên kết cha-con — anchor của spouse/
        # branchSpouse là liên kết hôn nhân, không phải cha/mẹ.
        parent_entity = (
            entity_of(by_id[parent_slot])
            if (parent_slot in by_id
                and relation not in ("spouse", "branchSpouse"))
            else None)
        out.append({
            "id": nid,
            "kind": "person",
            "label": _clean(info.get("ho_ten")),
            "role": role,
            "relationType": relation,
            "personId": str(entity) if entity is not None else None,
            "parentSlotId": parent_slot,
            "parentPersonId": str(parent_entity) if parent_entity else "",
            "familyGroupId": family,
            "sourceId": anchor or None,
            "spouseOf": anchor or None,
            "isLandOwner": bool(node.get("isLandOwner")),
            "willReceive": bool(node.get("willReceive", True)),
            "hidden": bool(node.get("hidden")),
            "deleted": bool(node.get("deleted")),
        })
    return out


# -------------------------------------------------------------------- service


class CaseWorkspaceService:
    """Compose/commit workspace cho một InheritanceCase trên session ORM."""

    def __init__(self, db):
        self.db = db

    # ------------------------------------------------------------- public

    def get(self, case_id: int) -> dict:
        case = self._load_case(case_id)
        case_type, document_type = _case_meta(case)
        supported = case_type == CASE_TYPE_INHERITANCE

        (payload, people, assets, entity_to_row, persisted_people,
         persisted_assets, warnings, dirty) = self._compose_stage(case)
        state, state_dirty = self._state_v2(
            case, payload, entity_to_row,
            valid_row_ids={p["row_id"] for p in people})
        render_model = self._render_model(payload)
        if state_dirty:
            dirty = True
        if dirty:
            status = self._persist_migrated(
                case, payload, persisted_people, persisted_assets,
                state, render_model)
            if status == "moved":
                # Commit chạy song song đã ghi state mới — đọc lại, không ghi đè.
                self.db.refresh(case)
                (payload, people, assets, entity_to_row, persisted_people,
                 persisted_assets, warnings, _dirty2) = self._compose_stage(case)
                state, _sd2 = self._state_v2(
                    case, payload, entity_to_row,
                    valid_row_ids={p["row_id"] for p in people})
                render_model = self._render_model(payload)
            # "locked" → trả snapshot đã compose, không persist lần này.

        return {
            "schema_version": SCHEMA_VERSION,
            "backend_mode": "real",
            "case": {
                "id": case.id,
                "case_type": case_type,
                "document_type": document_type,
                "status": "locked" if case.is_locked else "draft",
                "locked": bool(case.is_locked),
                "revision": self._revision(case),
            },
            "stage": {"people": people, "assets": assets},
            "diagram": {
                "domain": "inheritance",
                "state": state,
                "render_model": render_model,
                "warnings": warnings,
            },
            "capabilities": {
                "intake": list(INTAKE_KINDS) if supported else [],
                "diagram": supported,
                "word_export": supported,
            },
        }

    def commit_stage(self, case_id: int, base_revision: int,
                     people: Any, assets: Any) -> dict:
        case = self._load_case(case_id)
        if case.is_locked:
            raise WorkspaceError(
                "workspace_locked", f"Hồ sơ #{case_id} đang bị khóa")
        case_type, _doc_type = _case_meta(case)
        if case_type != CASE_TYPE_INHERITANCE:
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
        if not isinstance(people, list) or not isinstance(assets, list):
            raise WorkspaceError(
                "validation_error",
                "stage.people/stage.assets phải là danh sách")
        field_errors = self._validate_stage(people, assets)
        if field_errors:
            raise WorkspaceError(
                "stage_validation_error",
                f"Stage có {len(field_errors)} lỗi field",
                details={"field_errors": field_errors})

        try:
            resolved_people = self._upsert_people(people)
            resolved_assets = self._upsert_assets(assets)
            self._sync_links(case, resolved_assets)
            self.db.flush()

            payload = self._load_payload(case) or {}
            entity_to_row = {entity: rid
                             for rid, entity, _w in resolved_people}
            valid_rows = {rid for rid, _e, _w in resolved_people}
            state, _ = self._state_v2(case, payload, entity_to_row, valid_rows)
            people_by_id = {
                rid: {"ngay_chet": wire.get("ngay_chet")}
                for rid, _entity, wire in resolved_people
            }
            render_model = run_inheritance_case(
                {"version": 2, "nodes": state["nodes"]}, people_by_id)
            people_map = _people_map(resolved_people)
            legacy_nodes = _v2_to_legacy_nodes(state["nodes"], people_map)
            now = _utc_now_iso()
            self._sync_participants_and_owner(case, legacy_nodes)
            case.case_state_json = json.dumps(
                self._build_payload(payload, resolved_people, resolved_assets,
                                    state, render_model, legacy_nodes, now),
                ensure_ascii=False)
            case.engine_state_json = json.dumps(
                {"version": 2, "updatedAt": now, "nodes": legacy_nodes},
                ensure_ascii=False)
            self.db.flush()

            # Guarded atomic revision bump — 2 commit cùng base chỉ 1 cái thắng.
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

        return {
            "schema_version": SCHEMA_VERSION,
            "revision": server_revision + 1,
            "stage": {
                "people": [wire for _r, _e, wire in resolved_people],
                "assets": [wire for _r, _e, wire in resolved_assets],
            },
            "diagram": {"state": state, "render_model": render_model},
        }

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

    def _customer(self, entity_id: Optional[int]) -> Optional[Customer]:
        return self.db.get(Customer, entity_id) if entity_id else None

    def _property(self, entity_id: Optional[int]) -> Optional[Property]:
        return self.db.get(Property, entity_id) if entity_id else None

    # ----- compose stage (get)

    def _derive_people(self, case: InheritanceCase) -> list[dict]:
        rows: list[dict] = []
        seen: set = set()
        customers = [case.nguoi_chet]
        customers.extend(p.customer for p in case.participants)
        for customer in customers:
            if customer is None or customer.id in seen:
                continue
            seen.add(customer.id)
            rows.append({"id": str(customer.id)})
        return rows

    def _derive_assets(self, case: InheritanceCase) -> list[dict]:
        links = sorted(case.property_links,
                       key=lambda link: (not link.is_primary, link.id))
        if links:
            return [{"id": str(link.property_id),
                     "is_primary": bool(link.is_primary)} for link in links]
        if case.tai_san_id:
            return [{"id": str(case.tai_san_id), "is_primary": True}]
        return []

    def _compose_stage(self, case: InheritanceCase):
        """→ (payload, people_wire, assets_wire, entity_to_row,
        people_persisted, assets_persisted, warnings, dirty)."""
        payload = self._load_payload(case) or {}
        warnings: list[str] = []
        dirty = payload == {} or "stage" not in payload

        raw_people = payload.get("stage")
        if not isinstance(raw_people, list):
            raw_people = self._derive_people(case)
            dirty = True
        people: list[dict] = []
        entity_to_row: dict[int, str] = {}
        persisted_people: list[dict] = []
        for raw in raw_people:
            snap = dict(raw) if isinstance(raw, Mapping) else {}
            entity = _to_int(snap.get("id")) or _to_int(snap.get("entity_id"))
            row_id = snap.get("row_id")
            if not _is_uuid4(row_id):
                row_id = str(uuid.uuid4())
                snap["row_id"] = row_id
                dirty = True
            customer = self._customer(entity)
            wire = self._person_wire(row_id, entity, customer, snap)
            people.append(wire)
            if entity is not None:
                entity_to_row.setdefault(entity, row_id)
            persisted_people.append({
                "id": (str(entity) if entity is not None
                       else _clean(snap.get("id"))),
                "row_id": row_id,
                "ho_ten": wire["ho_ten"], "gioi_tinh": wire["gioi_tinh"],
                "ngay_sinh": wire["ngay_sinh"], "ngay_chet": wire["ngay_chet"],
                "so_giay_to": wire["so_giay_to"], "ngay_cap": wire["ngay_cap"],
                "noi_cap": wire["noi_cap"], "dia_chi": wire["dia_chi"],
                "place_of_origin": wire["place_of_origin"],
            })

        raw_assets = payload.get("assets")
        if not isinstance(raw_assets, list):
            raw_assets = self._derive_assets(case)
            dirty = True
        assets: list[dict] = []
        persisted_assets: list[dict] = []
        for index, raw in enumerate(raw_assets):
            snap = dict(raw) if isinstance(raw, Mapping) else {}
            entity = _to_int(snap.get("id")) or _to_int(snap.get("entity_id"))
            row_id = snap.get("row_id")
            if not _is_uuid4(row_id):
                row_id = str(uuid.uuid4())
                snap["row_id"] = row_id
                dirty = True
            primary = _coerce_bool(snap.get("is_primary"), False)
            assets.append(self._asset_wire(
                row_id, entity, self._property(entity), primary,
                index=index, warnings=warnings))
            persisted_assets.append({
                "id": (str(entity) if entity is not None
                       else _clean(snap.get("id"))),
                "row_id": row_id,
                "is_primary": primary,
            })

        return (payload, people, assets, entity_to_row,
                persisted_people, persisted_assets, warnings, dirty)

    def _person_wire(self, row_id: str, entity: Optional[int],
                     customer: Optional[Customer],
                     snap: Mapping[str, Any]) -> dict:
        noi_cap = _nn(snap.get("noi_cap"))
        if noi_cap is None and customer is not None and customer.ngay_cap:
            noi_cap = customer.noi_cap
        return {
            "row_id": row_id,
            "entity_id": entity,
            "ho_ten": _nn(customer.ho_ten if customer else snap.get("ho_ten")) or "(Chưa rõ)",
            "gioi_tinh": _norm_gender(
                customer.gioi_tinh if customer else snap.get("gioi_tinh")),
            "ngay_sinh": _emit_date_or_year(
                customer.ngay_sinh if customer else snap.get("ngay_sinh")),
            "ngay_chet": _emit_date_or_year(
                customer.ngay_chet if customer else snap.get("ngay_chet")),
            "so_giay_to": _nn(
                customer.so_giay_to if customer else snap.get("so_giay_to")),
            "ngay_cap": _emit_date_or_year(
                customer.ngay_cap if customer else snap.get("ngay_cap")),
            "noi_cap": noi_cap,
            "dia_chi": _nn(
                customer.dia_chi if customer else snap.get("dia_chi")),
            "place_of_origin": _nn(snap.get("place_of_origin")),
        }

    def _asset_wire(self, row_id: str, entity: Optional[int],
                    prop: Optional[Property], primary: bool,
                    index: int = 0,
                    warnings: Optional[list] = None) -> dict:
        land_rows = _parse_land_rows(
            prop.land_rows_json if prop is not None else None)
        raw_serial = prop.so_serial if prop is not None else None
        serial = _canonical_serial(raw_serial)
        if serial is None:
            # DB cũ có serial lạ → surrogate deterministic, giữ truy vết
            # qua warnings (không sửa Property — serial là SOT của sổ đỏ).
            serial = (f"XX{entity:06d}"[:8] if entity
                      else f"XX{index + 1:06d}")
            if raw_serial and warnings is not None:
                warnings.append(
                    f"asset {row_id}: so_serial '{raw_serial}' không "
                    f"canonical — emit '{serial}'")
        return {
            "row_id": row_id,
            "entity_id": entity,
            "is_primary": bool(primary),
            "so_serial": serial,
            "so_vao_so": _nn(prop.so_vao_so if prop else None),
            "so_thua_dat": _nn(prop.so_thua_dat if prop else None),
            "so_to_ban_do": _nn(prop.so_to_ban_do if prop else None),
            "dia_chi": _nn(prop.dia_chi if prop else None),
            "loai_so": _nn(prop.loai_so if prop else None),
            "hinh_thuc_su_dung": _nn(prop.hinh_thuc_su_dung if prop else None),
            "thoi_han": _nn(prop.thoi_han if prop else None),
            "nguon_goc": _nn(prop.nguon_goc if prop else None),
            "ngay_cap": _emit_date_or_year(prop.ngay_cap if prop else None),
            "co_quan_cap": _nn(prop.co_quan_cap if prop else None),
            "land_rows": land_rows,
        }

    # ----- diagram state

    def _state_v2(self, case: InheritanceCase, payload: Mapping[str, Any],
                  entity_to_row: Mapping[int, str],
                  valid_row_ids: Optional[set] = None) -> tuple:
        """→ ({"version":2,"nodes":[...]}, dirty). valid_row_ids=None → dùng
        mọi row_id đang có trong entity_to_row (get()); commit truyền tập row
        đã commit để prune."""
        valid = valid_row_ids if valid_row_ids is not None else set(
            entity_to_row.values())
        diagram = payload.get("diagram") if isinstance(
            payload.get("diagram"), Mapping) else {}
        raw_state = diagram.get("state")
        if (isinstance(raw_state, Mapping) and raw_state.get("version") == 2
                and isinstance(raw_state.get("nodes"), list)):
            nodes = _sanitize_v2_nodes(raw_state["nodes"], valid)
            return {"version": 2, "nodes": nodes}, nodes != raw_state["nodes"]

        for key in ("engineInput", "engineState"):
            src = diagram.get(key)
            if isinstance(src, Mapping) and isinstance(src.get("nodes"), list):
                return ({"version": 2,
                         "nodes": _legacy_to_v2(src["nodes"], entity_to_row)},
                        True)

        column_state = self._column_engine_state(case)
        if column_state is not None:
            return ({"version": 2, "nodes": _legacy_to_v2(
                column_state, entity_to_row)}, True)

        assignments = diagram.get("assignments")
        if isinstance(assignments, Mapping):
            return ({"version": 2, "nodes": _assignments_to_v2(
                assignments, entity_to_row)}, True)

        return {"version": 2, "nodes": []}, bool(raw_state)

    def _column_engine_state(self, case: InheritanceCase) -> Optional[list]:
        raw = _clean(getattr(case, "engine_state_json", None))
        if not raw:
            return None
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(payload, dict):
            return None
        inner = payload.get("engineState")
        if isinstance(inner, dict):
            payload = inner
        nodes = payload.get("nodes")
        return nodes if isinstance(nodes, list) else None

    @staticmethod
    def _render_model(payload: Mapping[str, Any]) -> Optional[dict]:
        diagram = payload.get("diagram") if isinstance(
            payload.get("diagram"), Mapping) else {}
        model = diagram.get("render_model")
        return dict(model) if isinstance(model, Mapping) else None

    # ----- migrate-on-read persist

    def _persist_migrated(self, case: InheritanceCase,
                          payload: Mapping[str, Any],
                          people: list[dict], assets: list[dict],
                          state: dict,
                          render_model: Optional[dict]) -> None:
        """Ghi lại payload đã migrate (row_id + diagram.state V2).

        Không đụng legacy keys (engineState/assignments/…) — web cũ vẫn đọc.
        """
        merged = dict(payload or {})
        diagram = dict(merged.get("diagram")
                       if isinstance(merged.get("diagram"), Mapping) else {})
        diagram["state"] = state
        diagram["render_model"] = render_model
        merged["schemaVersion"] = 2
        merged["stage"] = people
        merged["assets"] = assets
        merged["diagram"] = diagram
        merged_json = json.dumps(merged, ensure_ascii=False)
        seen_revision = self._revision(case)
        try:
            result = self.db.execute(sa_text(
                "UPDATE inheritance_cases SET case_state_json = :js "
                "WHERE id = :cid AND workspace_revision = :rev"),
                {"js": merged_json, "cid": case.id, "rev": seen_revision})
            self.db.commit()
        except OperationalError:
            # "database is locked" — read không được fail; bỏ persist lần này.
            self.db.rollback()
            return "locked"
        return "persisted" if result.rowcount == 1 else "moved"

    # ----- validation

    def _validate_stage(self, people: list, assets: list) -> list[dict]:
        errors: list[dict] = []

        def err(row_id, field, code, message, index=None):
            errors.append(_field_error(row_id, field, code, message, index))

        seen_row_ids: set = set()
        seen_person_keys: dict[str, Any] = {}
        seen_person_entities: dict[int, Any] = {}
        seen_serials: dict[str, Any] = {}
        seen_asset_entities: dict[int, Any] = {}

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
            elif entity is not None:
                if entity in seen_person_entities:
                    emit("entity_id", "invalid_format",
                         "entity_id trùng với dòng khác trong payload")
                else:
                    seen_person_entities[entity] = row_id
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
                          "place_of_origin"):
                self._check_nullable_str(row, field, emit)
            so_giay_to = row.get("so_giay_to")
            if isinstance(so_giay_to, str) and so_giay_to.strip():
                sgt = so_giay_to.strip()
                if sgt in seen_person_keys:
                    emit("so_giay_to", "invalid_format",
                         "so_giay_to trùng với dòng khác trong payload")
                else:
                    seen_person_keys[sgt] = row_id
                    owner = self.db.query(Customer).filter(
                        Customer.so_giay_to == sgt).first()
                    if (owner is not None and isinstance(entity, int)
                            and not isinstance(entity, bool)
                            and entity != owner.id):
                        emit("so_giay_to", "invalid_format",
                             "so_giay_to đã thuộc về người khác")

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
            elif entity is not None:
                if entity in seen_asset_entities:
                    emit("entity_id", "invalid_format",
                         "entity_id trùng với dòng khác trong payload")
                else:
                    seen_asset_entities[entity] = row_id
            if not isinstance(row.get("is_primary"), bool):
                emit("is_primary", "invalid_type",
                     "is_primary phải là boolean")
            serial = row.get("so_serial")
            if not isinstance(serial, str) or not serial.strip():
                emit("so_serial", "required", "so_serial bắt buộc")
            elif not _SERIAL_RE.match(serial.strip()):
                emit("so_serial", "invalid_format",
                     "so_serial phải canonical [A-Z]{2} + 6-8 chữ số")
            else:
                canon = serial.strip()
                if canon in seen_serials:
                    emit("so_serial", "invalid_format",
                         "so_serial trùng với dòng khác trong payload")
                else:
                    seen_serials[canon] = row_id
                    owner = self.db.query(Property).filter(
                        Property.so_serial == canon).first()
                    if (owner is not None and isinstance(entity, int)
                            and not isinstance(entity, bool)
                            and entity != owner.id):
                        emit("so_serial", "invalid_format",
                             "so_serial đã thuộc về tài sản khác")
            dia_chi = row.get("dia_chi")
            if not isinstance(dia_chi, str) or not dia_chi.strip():
                emit("dia_chi", "required", "dia_chi bắt buộc")
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
                        for lf in ("loai_dat", "thoi_han"):
                            value = lr.get(lf)
                            if value is not None and not isinstance(value, str):
                                emit("land_rows", "invalid_type",
                                     f"land_rows[{lr_index}].{lf} phải là chuỗi hoặc null")
                        dt = lr.get("dien_tich")
                        if dt is not None and (
                                not isinstance(dt, (int, float))
                                or isinstance(dt, bool)):
                            emit("land_rows", "invalid_type",
                                 f"land_rows[{lr_index}].dien_tich phải là số hoặc null")

        if assets:
            primaries = [r for r in assets
                         if isinstance(r, Mapping) and r.get("is_primary") is True]
            if len(primaries) != 1:
                targets = primaries if primaries else [
                    r for r in assets if isinstance(r, Mapping)][:1]
                for target in targets:
                    errors.append(_field_error(
                        target.get("row_id"), "is_primary", "primary_count",
                        "assets phải có đúng một dòng is_primary=true"))
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

    # ----- upsert + link

    def _upsert_people(self, rows: list) -> list:
        """→ [(row_id, entity_id, wire_row)]; upsert theo entity_id rồi
        khóa giấy tờ — không merge theo tên. Dedupe entity đã resolve —
        hai rows resolve về cùng customer là lỗi (tránh silent merge)."""
        resolved = []
        resolved_entities: dict[int, str] = {}
        for row in rows:
            entity = row.get("entity_id")
            customer = self._customer(entity) if isinstance(entity, int) else None
            if customer is None:
                sgt = _nn(row.get("so_giay_to"))
                if sgt:
                    customer = self.db.query(Customer).filter(
                        Customer.so_giay_to == sgt).first()
            if customer is None:
                customer = Customer()
                self.db.add(customer)
            customer.ho_ten = row["ho_ten"].strip()
            customer.gioi_tinh = row.get("gioi_tinh")
            customer.ngay_sinh = _parse_date_or_year(row.get("ngay_sinh"))
            customer.ngay_chet = _parse_date_or_year(row.get("ngay_chet"))
            customer.so_giay_to = _nn(row.get("so_giay_to"))
            customer.ngay_cap = _parse_date_or_year(row.get("ngay_cap"))
            customer.dia_chi = _nn(row.get("dia_chi"))
            self.db.flush()
            if customer.id in resolved_entities:
                raise WorkspaceError(
                    "stage_validation_error",
                    "Hai dòng resolve về cùng một người",
                    details={"field_errors": [_field_error(
                        row["row_id"], "entity_id", "invalid_format",
                        f"resolve trùng với dòng "
                        f"{resolved_entities[customer.id]}")]})
            resolved_entities[customer.id] = row["row_id"]
            wire = {key: row.get(key) for key in _person_contract_keys()}
            wire["row_id"] = row["row_id"]
            wire["entity_id"] = customer.id
            wire["ho_ten"] = customer.ho_ten
            resolved.append((row["row_id"], customer.id, wire))
        return resolved

    def _upsert_assets(self, rows: list) -> list:
        resolved = []
        resolved_entities: dict[int, str] = {}
        for row in rows:
            entity = row.get("entity_id")
            prop = self._property(entity) if isinstance(entity, int) else None
            if prop is None:
                serial = _clean(row.get("so_serial"))
                if serial:
                    prop = self.db.query(Property).filter(
                        Property.so_serial == serial).first()
            if prop is None:
                prop = Property(so_serial=row["so_serial"].strip(),
                                dia_chi=row["dia_chi"].strip())
                self.db.add(prop)
            prop.so_serial = row["so_serial"].strip()
            prop.so_vao_so = _nn(row.get("so_vao_so"))
            prop.so_thua_dat = _nn(row.get("so_thua_dat"))
            prop.so_to_ban_do = _nn(row.get("so_to_ban_do"))
            prop.dia_chi = row["dia_chi"].strip()
            prop.loai_so = _nn(row.get("loai_so"))
            land_rows = row.get("land_rows")
            prop.land_rows_json = (
                json.dumps([
                    {"loai_dat": _nn(lr.get("loai_dat")),
                     "dien_tich": lr.get("dien_tich"),
                     "thoi_han": _nn(lr.get("thoi_han"))}
                    for lr in land_rows if isinstance(lr, Mapping)
                ], ensure_ascii=False)
                if isinstance(land_rows, list) else None)
            prop.hinh_thuc_su_dung = _nn(row.get("hinh_thuc_su_dung"))
            prop.thoi_han = _nn(row.get("thoi_han"))
            prop.nguon_goc = _nn(row.get("nguon_goc"))
            prop.ngay_cap = _parse_date_or_year(row.get("ngay_cap"))
            prop.co_quan_cap = _nn(row.get("co_quan_cap"))
            self.db.flush()
            if prop.id in resolved_entities:
                raise WorkspaceError(
                    "stage_validation_error",
                    "Hai dòng resolve về cùng một tài sản",
                    details={"field_errors": [_field_error(
                        row["row_id"], "entity_id", "invalid_format",
                        f"resolve trùng với dòng "
                        f"{resolved_entities[prop.id]}")]})
            resolved_entities[prop.id] = row["row_id"]
            wire = {key: row.get(key) for key in _asset_contract_keys()}
            wire["row_id"] = row["row_id"]
            wire["entity_id"] = prop.id
            wire["land_rows"] = _parse_land_rows(prop.land_rows_json)
            resolved.append((row["row_id"], prop.id, wire))
        return resolved

    def _sync_links(self, case: InheritanceCase,
                    resolved_assets: list) -> None:
        self.db.query(InheritanceCaseProperty).filter(
            InheritanceCaseProperty.case_id == case.id).delete()
        primary_id = None
        for _rid, prop_id, wire in resolved_assets:
            self.db.add(InheritanceCaseProperty(
                case_id=case.id, property_id=prop_id,
                is_primary=bool(wire["is_primary"])))
            if wire["is_primary"]:
                primary_id = prop_id
        if primary_id is not None:
            case.tai_san_id = primary_id

    def _sync_participants_and_owner(self, case: InheritanceCase,
                                     legacy_nodes: list) -> None:
        """Rebuild `participants` + `nguoi_chet_id` từ legacy projection đã
        commit — tương đương `_extract_diagram_participants` +
        `_replace_case_participants` (routers/cases.py:202-257,456-470).

        Re-implement tại service thay vì import router: routers.cases kéo
        fastapi/jinja2 vào sidecar process. Dung sai service-side: node trỏ
        person ngoài Stage đã bị prune ở `_state_v2`; person trùng / deceased
        trùng / parentPersonId không active → bỏ qua thay vì raise (commit
        đã qua validation, contract không có error tương ứng).
        """
        active_ids = {
            _clean(n.get("personId")) for n in legacy_nodes
            if _clean(n.get("personId"))
            and not n.get("hidden") and not n.get("deleted")
        }
        owner_entity: Optional[int] = None
        for node in legacy_nodes:
            if node.get("role") == "Owner" and _clean(node.get("personId")):
                owner_entity = _to_int(node.get("personId"))
                break
        if owner_entity is not None:
            case.nguoi_chet_id = owner_entity
        deceased_id = (str(owner_entity) if owner_entity is not None
                       else str(case.nguoi_chet_id))

        self.db.query(InheritanceParticipant).filter(
            InheritanceParticipant.ho_so_id == case.id).delete()
        seen: set = set()
        for node in legacy_nodes:
            person_id = _clean(node.get("personId"))
            if (not person_id or node.get("hidden") or node.get("deleted")
                    or person_id in seen):
                continue
            role = _clean(node.get("role")) or "Khac"
            if role == "Owner" or person_id == deceased_id:
                continue
            seen.add(person_id)
            parent_raw = _clean(node.get("parentPersonId"))
            parent_id = (
                int(parent_raw)
                if parent_raw.isdigit() and parent_raw in active_ids
                else None)
            self.db.add(InheritanceParticipant(
                ho_so_id=case.id,
                customer_id=int(person_id),
                vai_tro=role,
                hang_thua_ke=_hang_for_role(role),
                ty_le=0.0,
                co_nhan_tai_san=bool(node.get("willReceive", True)),
                parent_customer_id=parent_id,
            ))

    # ----- persist committed payload

    def _build_payload(self, payload: Mapping[str, Any],
                       resolved_people: list, resolved_assets: list,
                       state: dict, render_model: dict,
                       legacy_nodes: list, now: str) -> dict:
        row_to_entity = {rid: entity
                         for rid, entity, _w in resolved_people}
        entity_allocations = {
            str(row_to_entity[pid]): alloc
            for pid, alloc in (render_model.get("allocations") or {}).items()
            if pid in row_to_entity
        }
        merged = dict(payload or {})
        diagram = dict(merged.get("diagram")
                       if isinstance(merged.get("diagram"), Mapping) else {})
        diagram.update({
            "state": state,
            "render_model": render_model,
            "engineInput": {"version": 2, "nodes": legacy_nodes},
            "engineResult": {**render_model,
                             "allocations": entity_allocations},
            "engineState": {"version": 2, "updatedAt": now,
                            "nodes": legacy_nodes},
            "assignments": {
                n["id"]: str(row_to_entity[n["personId"]])
                for n in state["nodes"]
                if n.get("personId") and n["personId"] in row_to_entity
            },
            "updatedAt": now,
        })
        merged["schemaVersion"] = 2
        merged["stage"] = [
            {"id": str(entity), "row_id": rid,
             "ho_ten": wire.get("ho_ten"), "gioi_tinh": wire.get("gioi_tinh"),
             "ngay_sinh": wire.get("ngay_sinh"),
             "ngay_chet": wire.get("ngay_chet"),
             "so_giay_to": wire.get("so_giay_to"),
             "ngay_cap": wire.get("ngay_cap"),
             "noi_cap": wire.get("noi_cap"), "dia_chi": wire.get("dia_chi"),
             "place_of_origin": wire.get("place_of_origin")}
            for rid, entity, wire in resolved_people
        ]
        merged["assets"] = [
            {"id": str(entity), "row_id": rid,
             "is_primary": bool(wire.get("is_primary"))}
            for rid, entity, wire in resolved_assets
        ]
        merged["diagram"] = diagram
        return merged


def _hang_for_role(role: str) -> int:
    """Bản sao routers/cases.py:_hang_for_role — giữ parity web cũ."""
    if role in ("Cha", "Mẹ", "Cha_vc", "Me_vc", "Vợ/Chồng", "Con",
                "Cháu", "Con_dau_re"):
        return 1
    if role in ("Ông/Bà", "Anh/Chị/Em"):
        return 2
    return 1


def _people_map(resolved_people: list) -> dict:
    """{row_id: {entity, ho_ten, gioi_tinh}} cho legacy projection."""
    return {
        rid: {"entity": entity, "ho_ten": wire.get("ho_ten"),
              "gioi_tinh": wire.get("gioi_tinh")}
        for rid, entity, wire in resolved_people
    }


def _parse_land_rows(raw: Any) -> Optional[list]:
    if raw is None:
        return None
    try:
        rows = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return None
    if not isinstance(rows, list):
        return None
    out = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        dien_tich = row.get("dien_tich")
        out.append({
            "loai_dat": _nn(row.get("loai_dat")),
            "dien_tich": dien_tich if isinstance(dien_tich, (int, float))
                         and not isinstance(dien_tich, bool) else None,
            "thoi_han": _nn(row.get("thoi_han")),
        })
    return out


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z")

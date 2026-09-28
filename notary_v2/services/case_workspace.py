"""Case workspace service — backend thật cho contract notary.case-drafting.v2.

Sở hữu business rule của `notary.workspace_get`,
`notary.workspace_commit_stage` và `notary.workspace_create`; sidecar
handlers chỉ dịch payload ↔ service, không chứa nghiệp vụ (MIN-107,
nâng cấp v2 ở MIN-128 — contract `contracts/notary-case-drafting.md` §13).

Persisted state — `inheritance_cases.case_state_json` (schemaVersion 3)::

    {"schemaVersion": 3,
     "case_type": "inheritance" | "two_party",
     "owner_row_id": "<uuid4>",                  # chỉ inheritance
     "stage":  [{"id": "<entity_id>", "row_id": "<uuid4>", ...field snapshot}],
     "assets": [{"id": "<entity_id>", "row_id": "<uuid4>",
                 "is_primary": bool}],          # projection legacy (index 0)
     "diagram": {"state": {"version": 3, "domain": ..., "nodes": [...]},
                "render_model": <engine output | unsupported | null>,
                "engineState"/"engineInput"/"engineResult"/"assignments":
                    projection legacy cho web cũ — chỉ inheritance}}

Migrate-on-read: payload cũ (schemaVersion 1/2, không `row_id`, legacy
`engineState`/`assignments`, hoặc thiếu `case_state_json`) được normalize +
ghi lại ngay trong `get()` để `row_id` UUIDv4 ổn định qua reload; node
flag `isLandOwner`/`willReceive` → `ownPositions`/`receivePositions`
= [1..min(3, len(assets))] (§13.7 Q6). `diagram.state` trên wire luôn là
V3 (`domain` + node shape theo domain); `personId` trỏ `row_id` của Stage
đã commit.

`case_type` derive từ `loai_van_ban` (không thêm column): inheritance doc
(`khai_nhan`/`thoa_thuan`) → "inheritance"; two-party doc (§13.5 Q11) →
"two_party"; giá trị khác → loại việc chưa hỗ trợ (capabilities tắt,
write bị chặn — giữ semantics "Chưa hỗ trợ" §7 drafting-tab).
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


SCHEMA_VERSION = "notary.case-drafting.v2"
PAYLOAD_SCHEMA_VERSION = 3            # case_state_json.schemaVersion
DIAGRAM_STATE_VERSION = 3

CASE_TYPE_INHERITANCE = "inheritance"
CASE_TYPE_TWO_PARTY = "two_party"
CASE_TYPES = (CASE_TYPE_INHERITANCE, CASE_TYPE_TWO_PARTY)

DOCUMENT_TYPES = ("khai_nhan", "thoa_thuan")
# §13.5/Q11 — doc types của domain hai bên (đã chốt owner 27/09/2026).
DOCUMENT_TYPES_TWO_PARTY = ("chuyen_nhuong", "tang_cho",
                            "cho_thue", "dat_coc")
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


def _canonical_serial(value: Any) -> Optional[str]:
    text = _clean(value)
    if not text:
        return None
    candidate = re.sub(r"[^0-9A-Za-z]", "", text).upper()
    return candidate if _SERIAL_RE.match(candidate) else None


def _case_meta(case: InheritanceCase) -> tuple[str, str]:
    """(case_type, document_type) — `loai_van_ban` là discriminator.

    - `khai_nhan`/`thoa_thuan` → inheritance.
    - `DOCUMENT_TYPES_TWO_PARTY` → two_party (§13.5/Q11).
    - Giá trị khác → case_type = giá trị thô (không thuộc CASE_TYPES —
      capabilities tắt, write bị chặn `case_type_unsupported`).
    """
    loai = _clean(case.loai_van_ban)
    if loai in DOCUMENT_TYPES:
        return CASE_TYPE_INHERITANCE, loai
    if loai in DOCUMENT_TYPES_TWO_PARTY:
        return CASE_TYPE_TWO_PARTY, loai
    return (loai or "unknown"), "khai_nhan"


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


def _check_extra_keys(mapping: Any, allowed: set, where: str) -> None:
    """Field lạ trên wire → `validation_error` (strip-field rule §2.2;
    `is_primary`/`isLandOwner` cũ cũng rơi vào rule này ở v2)."""
    if not isinstance(mapping, Mapping):
        return
    extra = sorted(set(mapping) - allowed)
    if extra:
        raise WorkspaceError(
            "validation_error",
            f"{where} có field không hỗ trợ: {extra}")


def _person_contract_keys() -> tuple[str, ...]:
    return ("row_id", "entity_id", "ho_ten", "gioi_tinh", "ngay_sinh",
            "ngay_chet", "so_giay_to", "ngay_cap", "noi_cap", "dia_chi",
            "place_of_origin")


def _asset_contract_keys() -> tuple[str, ...]:
    """asset_row_v2 — giống v1 TRỪ `is_primary` (§13.3)."""
    return ("row_id", "entity_id", "so_serial", "so_vao_so",
            "so_thua_dat", "so_to_ban_do", "dia_chi", "loai_so",
            "hinh_thuc_su_dung", "thoi_han", "nguon_goc", "ngay_cap",
            "co_quan_cap", "land_rows")


_STAGE_KEYS = {"owner_row_id", "people", "assets"}
_PERSON_FIELD_SET = set(_person_contract_keys())
_ASSET_FIELD_SET = set(_asset_contract_keys())


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
    ngoài Stage (giữ semantics `_sanitize_v2_nodes`)."""
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
    (unique, đúng thứ tự); personId ngoài Stage → null (ô giữ chỗ — §13.5,
    không bao giờ compact)."""
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


def _v2_nodes_to_v3(nodes: list[dict], asset_count: int) -> list[dict]:
    """V2 node (isLandOwner/willReceive) → V3 (§13.7 Q6):
    flag true → [1..min(3, len(assets))]; false → []."""
    top = max(0, min(MAX_ASSETS, asset_count))
    out: list[dict] = []
    for n in nodes or []:
        out.append({
            "id": n["id"],
            "personId": n.get("personId"),
            "parentSlotIds": list(n.get("parentSlotIds") or []),
            "spouseSlotId": n.get("spouseSlotId"),
            "ownPositions": list(range(1, top + 1))
            if _coerce_bool(n.get("isLandOwner"), False) else [],
            "receivePositions": list(range(1, top + 1))
            if _coerce_bool(n.get("willReceive"), True) else [],
            "hidden": _coerce_bool(n.get("hidden"), False),
            "deleted": _coerce_bool(n.get("deleted"), False),
        })
    return out


def _v3_to_v2_nodes(nodes: list[dict]) -> list[dict]:
    """V3 → V2 engine/projection (§13.4 A4): isLandOwner := ownPositions ≠ [],
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
    """Seed `diagram.state` v3 khi create không kèm diagram (§13.6):
    node `owner` gán owner_row_id + ownPositions đủ vị trí hiện có (Q5);
    bộ slot rỗng chuẩn như client seed hiện trạng."""
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
        supported = case_type in CASE_TYPES
        domain = (case_type if supported else CASE_TYPE_INHERITANCE)

        composed = self._compose_stage(case)
        valid_rows = {p["row_id"] for p in composed.people}
        state, state_dirty = self._state_v3(
            case, composed.payload, composed.entity_to_row,
            domain=domain, valid_row_ids=valid_rows,
            asset_count=len(composed.assets))
        if state_dirty:
            composed.dirty = True
        owner_row_id = None
        if domain == CASE_TYPE_INHERITANCE:
            owner_row_id = self._resolve_owner_row_id(
                composed.payload, state, valid_rows)
        render_model = self._render_model(composed.payload)
        if composed.dirty:
            status = self._persist_migrated(
                case, composed.payload, composed.persisted_people,
                composed.persisted_assets, state, render_model,
                domain=domain, owner_row_id=owner_row_id)
            if status == "moved":
                # Commit chạy song song đã ghi state mới — đọc lại, không ghi đè.
                self.db.refresh(case)
                composed = self._compose_stage(case)
                valid_rows = {p["row_id"] for p in composed.people}
                state, _sd2 = self._state_v3(
                    case, composed.payload, composed.entity_to_row,
                    domain=domain, valid_row_ids=valid_rows,
                    asset_count=len(composed.assets))
                if domain == CASE_TYPE_INHERITANCE:
                    owner_row_id = self._resolve_owner_row_id(
                        composed.payload, state, valid_rows)
                render_model = self._render_model(composed.payload)
            # "locked" → trả snapshot đã compose, không persist lần này.

        stage_out: dict = {"people": composed.people,
                           "assets": composed.assets}
        if domain == CASE_TYPE_INHERITANCE:
            stage_out = {"owner_row_id": owner_row_id, **stage_out}
        diagram_out: dict = {
            "domain": domain,
            "state": state,
            "render_model": render_model,
        }
        if composed.legacy_notes:
            diagram_out["warnings"] = list(composed.legacy_notes)

        data = {
            "schema_version": SCHEMA_VERSION,
            "backend_mode": "real",
            "case": {
                "id": case.id,
                "case_type": case_type,
                "document_type": document_type,
                "status": "locked" if case.is_locked else "draft",
                "locked": bool(case.is_locked),
                "revision": self._revision(case),
                "ngay_lap_ho_so": _emit_date_or_year(case.ngay_lap_ho_so),
                "noi_niem_yet": _nn(case.noi_niem_yet),
                "ghi_chu": _nn(case.ghi_chu),
            },
        }
        if composed.data_warnings:
            data["warnings"] = list(composed.data_warnings)
        data["stage"] = stage_out
        data["diagram"] = diagram_out
        data["capabilities"] = {
            "intake": list(INTAKE_KINDS) if supported else [],
            "diagram": supported,
            # §13.5: word_export chỉ mở cho inheritance.
            "word_export": case_type == CASE_TYPE_INHERITANCE,
        }
        return data

    def commit_stage(self, case_id: int, base_revision: int,
                     stage: Any) -> dict:
        """`notary.workspace_commit_stage` — atomic: validate → upsert →
        prune Diagram → re-evaluate → persist → revision+1 (§6.1, §13).

        `stage` = stage_v2 trên wire: `{owner_row_id?, people[], assets[]}`
        — owner_row_id bắt buộc với inheritance, cấm với two_party.
        """
        case = self._load_case(case_id)
        if case.is_locked:
            raise WorkspaceError(
                "workspace_locked", f"Hồ sơ #{case_id} đang bị khóa")
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
        owner_row_id = self._validate_owner_pointer(
            stage, people, case_type)
        field_errors = self._validate_stage(people, assets, case_type)
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
            state, _ = self._state_v3(
                case, payload, entity_to_row, domain=case_type,
                valid_row_ids=valid_rows, asset_count=len(assets))
            diagram_warnings: list = []
            legacy_nodes: Optional[list] = None
            people_map = _people_map(resolved_people)
            if case_type == CASE_TYPE_INHERITANCE:
                pruned = _prune_positions(state["nodes"], len(assets))
                if pruned:
                    diagram_warnings.append({
                        "code": "diagram.selection_pruned",
                        "message": "Dấu chọn tài sản ngoài vị trí hiện có "
                                   "đã được gỡ"})
                # §13.6: owner là con trỏ stage — sync node owner.
                _sync_owner_node(state["nodes"], owner_row_id)
                people_by_id = {
                    rid: {"ngay_chet": wire.get("ngay_chet")}
                    for rid, _entity, wire in resolved_people}
                render_model = run_inheritance_case(
                    {"version": 2,
                     "nodes": _v3_to_v2_nodes(state["nodes"])},
                    people_by_id)
                legacy_nodes = _v2_to_legacy_nodes(
                    _v3_to_v2_nodes(state["nodes"]), people_map)
            else:
                state["nodes"] = _canonical_two_party_nodes(state["nodes"])
                render_model = unsupported_render_model()
            now = _utc_now_iso()
            if case_type == CASE_TYPE_INHERITANCE:
                self._sync_participants_and_owner(
                    case, legacy_nodes,
                    owner_entity=next(
                        (entity for rid, entity, _w in resolved_people
                         if rid == owner_row_id), None))
            elif resolved_people:
                # two_party: neo people[0] vào nguoi_chet_id (cột NOT NULL;
                # không ý nghĩa "người để lại" — chỉ anchor danh sách).
                case.nguoi_chet_id = resolved_people[0][1]
            case.case_state_json = json.dumps(
                self._build_payload(
                    payload, resolved_people, resolved_assets,
                    state, render_model, legacy_nodes, now,
                    domain=case_type, owner_row_id=owner_row_id),
                ensure_ascii=False)
            if case_type == CASE_TYPE_INHERITANCE:
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
        }

    def create(self, idempotency_key: Any, case_meta: Any,
               stage: Any, state: Any) -> dict:
        """`notary.workspace_create` — tạo hồ sơ từ nháp (§13.6).

        Một transaction: validate → tạo case + person + asset + link +
        persist stage/diagram + revision=1 → commit; lỗi bất kỳ →
        rollback trọn vẹn. Idempotent trên `idempotency_key` đã persist:
        replay trả cùng case với `created:false`. `diagram` optional —
        absent → server seed (inheritance: owner + slot chuẩn; two_party:
        30 ô trống).
        """
        if not _is_uuid4(idempotency_key):
            raise WorkspaceError(
                "validation_error", "idempotency_key phải là UUID v4")

        existing = self.db.query(InheritanceCase).filter(
            InheritanceCase.workspace_idempotency_key
            == str(idempotency_key)).first()
        if existing is not None:
            data = self.get(existing.id)
            data["created"] = False
            return data

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
        owner_row_id = self._validate_owner_pointer(
            stage, people, case_type)
        field_errors = self._validate_stage(people, assets, case_type)
        field_errors += self._validate_create_stage(people, assets)
        if field_errors:
            raise WorkspaceError(
                "stage_validation_error",
                f"Stage có {len(field_errors)} lỗi field",
                details={"field_errors": field_errors})

        # Lazy import — inheritance_workspace đã import module này ở
        # module level; import ngược ở đây sẽ circular.
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
            # §13.6: render_model null khi chưa evaluate được (giữ §4.3).
            render_model = None

        try:
            resolved_people = self._upsert_people(people)
            resolved_assets = self._upsert_assets(assets)
            row_to_entity = {
                rid: entity for rid, entity, _w in resolved_people}
            if case_type == CASE_TYPE_INHERITANCE:
                nguoi_chet = row_to_entity[owner_row_id]
            else:
                nguoi_chet = resolved_people[0][1]  # anchor bên A đầu
            case = InheritanceCase(
                nguoi_chet_id=nguoi_chet,
                tai_san_id=resolved_assets[0][1],  # vị trí 1 = primary
                ngay_lap_ho_so=meta["ngay_lap_ho_so"] or date.today(),
                loai_van_ban=meta["document_type"],
                trang_thai="draft",
                noi_niem_yet=meta["noi_niem_yet"],
                ghi_chu=meta["ghi_chu"],
                workspace_revision=1,
                workspace_idempotency_key=str(idempotency_key))
            self.db.add(case)
            self.db.flush()
            self._sync_links(case, resolved_assets)

            now = _utc_now_iso()
            legacy_nodes = None
            if case_type == CASE_TYPE_INHERITANCE:
                legacy_nodes = _v2_to_legacy_nodes(
                    _v3_to_v2_nodes(clean_state["nodes"]),
                    _people_map(resolved_people))
                self._sync_participants_and_owner(
                    case, legacy_nodes, owner_entity=nguoi_chet)
            case.case_state_json = json.dumps(
                self._build_payload(
                    {}, resolved_people, resolved_assets,
                    clean_state, render_model, legacy_nodes, now,
                    domain=case_type, owner_row_id=owner_row_id),
                ensure_ascii=False)
            if case_type == CASE_TYPE_INHERITANCE:
                case.engine_state_json = json.dumps(
                    {"version": 2, "updatedAt": now, "nodes": legacy_nodes},
                    ensure_ascii=False)
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
        return {
            "schema_version": SCHEMA_VERSION,
            "backend_mode": "real",
            "created": True,
            "case": {
                "id": case.id,
                "case_type": case_type,
                "document_type": meta["document_type"],
                "status": "draft",
                "locked": False,
                "revision": 1,
                "ngay_lap_ho_so": _emit_date_or_year(case.ngay_lap_ho_so),
                "noi_niem_yet": meta["noi_niem_yet"],
                "ghi_chu": meta["ghi_chu"],
            },
            "stage": stage_out,
            "diagram": {
                "domain": case_type,
                "state": clean_state,
                "render_model": render_model,
            },
            "capabilities": {
                "intake": list(INTAKE_KINDS),
                "diagram": True,
                "word_export": case_type == CASE_TYPE_INHERITANCE,
            },
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

    def _compose_stage(self, case: InheritanceCase) -> "_StageCompose":
        """Compose people/assets wires từ payload (hoặc derive legacy).

        Thứ tự asset = vị trí (§13.3): reorder ưu tiên dòng is_primary:true
        đầu tiên lên vị trí 1 khi đọc payload cũ; is_primary bất thường
        (0 hoặc ≥2 true) → data warning `stage.legacy_primary_ambiguous`;
        >3 asset → `stage.legacy_asset_overflow` (emit đủ, không cắt)."""
        payload = self._load_payload(case) or {}
        data_warnings: list[dict] = []
        legacy_notes: list[str] = []
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
        snaps: list[dict] = []
        for raw in raw_assets:
            snap = dict(raw) if isinstance(raw, Mapping) else {}
            entity = _to_int(snap.get("id")) or _to_int(snap.get("entity_id"))
            row_id = snap.get("row_id")
            if not _is_uuid4(row_id):
                row_id = str(uuid.uuid4())
                snap["row_id"] = row_id
                dirty = True
            snap["_entity"] = entity
            snaps.append(snap)

        # Vị trí 1 = primary (§13.7): reorder mảng đọc — is_primary:true
        # đầu tiên lên đầu; bất thường (0/≥2 true) → warning legacy.
        primaries = [i for i, s in enumerate(snaps)
                     if _coerce_bool(s.get("is_primary"), False)]
        if len(primaries) != 1:
            if primaries or snaps:
                data_warnings.append({
                    "code": "stage.legacy_primary_ambiguous",
                    "message": "Hồ sơ cũ có cờ is_primary bất thường — "
                               "đã căn vị trí 1 theo dòng đầu"})
                dirty = True
        if primaries and primaries[0] != 0:
            snaps.insert(0, snaps.pop(primaries[0]))

        if len(snaps) > MAX_ASSETS:
            data_warnings.append({
                "code": "stage.legacy_asset_overflow",
                "message": f"Hồ sơ cũ có {len(snaps)} tài sản — contract "
                           f"v2 tối đa {MAX_ASSETS}; phải giảm trước khi "
                           "Cập nhật"})

        assets: list[dict] = []
        persisted_assets: list[dict] = []
        for index, snap in enumerate(snaps):
            entity = snap.get("_entity")
            assets.append(self._asset_wire(
                snap["row_id"], entity, self._property(entity),
                index=index, warnings=legacy_notes))
            persisted_assets.append({
                "id": (str(entity) if entity is not None
                       else _clean(snap.get("id"))),
                "row_id": snap["row_id"],
                # Vị trí 1 = primary theo nghĩa đã normalize.
                "is_primary": index == 0,
            })

        return _StageCompose(
            payload=payload, people=people, assets=assets,
            entity_to_row=entity_to_row, persisted_people=persisted_people,
            persisted_assets=persisted_assets,
            data_warnings=data_warnings, legacy_notes=legacy_notes,
            dirty=dirty)

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
                    prop: Optional[Property],
                    index: int = 0,
                    warnings: Optional[list] = None) -> dict:
        """asset_row_v2 — KHÔNG emit `is_primary` (§13.3)."""
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

    # ----- owner_row_id (§13.6)

    @staticmethod
    def _resolve_owner_row_id(payload: Mapping[str, Any],
                              state: Mapping[str, Any],
                              valid_rows: set) -> Optional[str]:
        """owner_row_id đã committed (SOT) → fallback personId của node
        owner persist (hồ sơ legacy chưa có pointer) → null."""
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
        """owner_row_id trên payload: bắt buộc + trỏ row có thật với
        inheritance; CẤM (kể cả null) với two_party (§13.5/§13.6)."""
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

    # ----- diagram state

    def _state_v3(self, case: InheritanceCase, payload: Mapping[str, Any],
                  entity_to_row: Mapping[int, str], *, domain: str,
                  valid_row_ids: Optional[set] = None,
                  asset_count: int = 0) -> tuple:
        """→ ({"version":3,"domain":...,"nodes":[...]}, dirty).

        valid_row_ids=None → mọi row_id đang có (get()); commit truyền tập
        row đã commit để prune. Domain `two_party`: state canonical 30 ô —
        personId ngoài stage → null, không compact. Domain inheritance:
        nguồn ưu tiên v3 → v2 → legacy (engineInput/engineState/column/
        assignments); node personId ngoài stage → bỏ node.
        """
        valid = valid_row_ids if valid_row_ids is not None else set(
            entity_to_row.values())
        diagram = payload.get("diagram") if isinstance(
            payload.get("diagram"), Mapping) else {}
        raw_state = diagram.get("state")

        if domain == CASE_TYPE_TWO_PARTY:
            if (isinstance(raw_state, Mapping)
                    and raw_state.get("version") == DIAGRAM_STATE_VERSION
                    and raw_state.get("domain") == CASE_TYPE_TWO_PARTY
                    and isinstance(raw_state.get("nodes"), list)):
                sanitized = _sanitize_two_party_nodes(
                    raw_state["nodes"], valid)
                nodes = _canonical_two_party_nodes(sanitized)
                return ({"version": DIAGRAM_STATE_VERSION,
                         "domain": CASE_TYPE_TWO_PARTY,
                         "nodes": nodes},
                        nodes != raw_state["nodes"])
            # Không có persisted state hợp lệ → seed 30 ô canonical (§13.5)
            # và persist lại luôn (get-side migration).
            return _seed_two_party_state(), True

        if (isinstance(raw_state, Mapping)
                and raw_state.get("version") == DIAGRAM_STATE_VERSION
                and isinstance(raw_state.get("nodes"), list)):
            nodes = _sanitize_v3_nodes(raw_state["nodes"], valid)
            return ({"version": DIAGRAM_STATE_VERSION,
                     "domain": CASE_TYPE_INHERITANCE,
                     "nodes": nodes},
                    nodes != raw_state["nodes"])

        if (isinstance(raw_state, Mapping)
                and raw_state.get("version") == 2
                and isinstance(raw_state.get("nodes"), list)):
            v2 = _sanitize_v2_nodes(raw_state["nodes"], valid)
            return ({"version": DIAGRAM_STATE_VERSION,
                     "domain": CASE_TYPE_INHERITANCE,
                     "nodes": _v2_nodes_to_v3(v2, asset_count)}, True)

        for key in ("engineInput", "engineState"):
            src = diagram.get(key)
            if isinstance(src, Mapping) and isinstance(src.get("nodes"), list):
                v2 = _legacy_to_v2(src["nodes"], entity_to_row)
                return ({"version": DIAGRAM_STATE_VERSION,
                         "domain": CASE_TYPE_INHERITANCE,
                         "nodes": _v2_nodes_to_v3(v2, asset_count)}, True)

        column_state = self._column_engine_state(case)
        if column_state is not None:
            v2 = _legacy_to_v2(column_state, entity_to_row)
            return ({"version": DIAGRAM_STATE_VERSION,
                     "domain": CASE_TYPE_INHERITANCE,
                     "nodes": _v2_nodes_to_v3(v2, asset_count)}, True)

        assignments = diagram.get("assignments")
        if isinstance(assignments, Mapping):
            v2 = _assignments_to_v2(assignments, entity_to_row)
            return ({"version": DIAGRAM_STATE_VERSION,
                     "domain": CASE_TYPE_INHERITANCE,
                     "nodes": _v2_nodes_to_v3(v2, asset_count)}, True)

        return ({"version": DIAGRAM_STATE_VERSION,
                 "domain": CASE_TYPE_INHERITANCE, "nodes": []},
                bool(raw_state))

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
                          render_model: Optional[dict], *,
                          domain: str,
                          owner_row_id: Optional[str]) -> None:
        """Ghi lại payload đã migrate (row_id + diagram.state V3 +
        owner_row_id + is_primary projection theo vị trí).

        Không đụng legacy keys (engineState/assignments/…) của inheritance —
        web cũ vẫn đọc; two_party strip chúng nếu lỡ có.
        """
        merged = dict(payload or {})
        diagram = dict(merged.get("diagram")
                       if isinstance(merged.get("diagram"), Mapping) else {})
        diagram["state"] = state
        diagram["render_model"] = render_model
        if domain == CASE_TYPE_TWO_PARTY:
            for key in ("engineInput", "engineState", "engineResult",
                        "assignments"):
                diagram.pop(key, None)
            merged.pop("owner_row_id", None)
        else:
            merged["owner_row_id"] = owner_row_id
        merged["schemaVersion"] = PAYLOAD_SCHEMA_VERSION
        merged["case_type"] = domain
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

    @staticmethod
    def _validate_case_meta(case_meta: Any) -> dict:
        """Payload `case` của workspace_create (§13.6) → meta đã chuẩn hóa;
        `case_type` optional default "inheritance"; document_type theo
        enum của từng case_type."""
        if not isinstance(case_meta, Mapping):
            raise WorkspaceError(
                "validation_error", "payload.case phải là object")
        _check_extra_keys(case_meta, {
            "case_type", "document_type", "ngay_lap_ho_so",
            "noi_niem_yet", "ghi_chu"}, "payload.case")
        case_type = case_meta.get("case_type", CASE_TYPE_INHERITANCE)
        if case_type not in CASE_TYPES:
            raise WorkspaceError(
                "validation_error",
                f"case_type phải ∈ {list(CASE_TYPES)}")
        document_type = case_meta.get("document_type")
        allowed = (DOCUMENT_TYPES_TWO_PARTY
                   if case_type == CASE_TYPE_TWO_PARTY else DOCUMENT_TYPES)
        if document_type not in allowed:
            raise WorkspaceError(
                "validation_error",
                f"document_type phải ∈ {list(allowed)}")
        ngay = case_meta.get("ngay_lap_ho_so")
        if not _valid_date_full(ngay):
            raise WorkspaceError(
                "validation_error",
                "ngay_lap_ho_so phải là YYYY-MM-DD hoặc null")
        for field in ("noi_niem_yet", "ghi_chu"):
            value = case_meta.get(field)
            if value is not None and (
                    not isinstance(value, str) or not value.strip()):
                raise WorkspaceError(
                    "validation_error",
                    f"{field} phải là chuỗi non-empty hoặc null")
        return {
            "case_type": case_type,
            "document_type": document_type,
            "ngay_lap_ho_so": _parse_date_or_year(ngay),
            "noi_niem_yet": _nn(case_meta.get("noi_niem_yet")),
            "ghi_chu": _nn(case_meta.get("ghi_chu")),
        }

    @staticmethod
    def _validate_create_stage(people: list, assets: list) -> list[dict]:
        """Rule riêng của `workspace_create` (§13.6): stage non-empty và
        mọi `entity_id` phải null — nháp chưa từng lưu tạo entity mới."""
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
        """Field-level rules của stage_v2: `is_primary` KHÔNG còn trên wire
        (field lạ → validation_error ở caller), assets ≤ 3 (`asset_limit`),
        two_party people ≤ 30 (`people_limit`)."""
        errors: list[dict] = []

        def err(row_id, field, code, message, index=None):
            errors.append(_field_error(row_id, field, code, message, index))

        # Trường lạ → validation_error (§13.3: producer v2 không emit
        # is_primary; consumer thấy key này = lỗi client).
        for row in people:
            if isinstance(row, Mapping):
                _check_extra_keys(row, _PERSON_FIELD_SET, "person_row")
        for row in assets:
            if isinstance(row, Mapping):
                _check_extra_keys(row, _ASSET_FIELD_SET, "asset_row")

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

        # Giới hạn §13.3/§13.5 — gắn row_id của dòng thừa.
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
        """Link table + tai_san_id theo VỊ TRÍ (§13.3): index 0 = primary
        (projection legacy cho web/Word cũ — wire v2 không còn is_primary)."""
        self.db.query(InheritanceCaseProperty).filter(
            InheritanceCaseProperty.case_id == case.id).delete()
        for index, (_rid, prop_id, _wire) in enumerate(resolved_assets):
            self.db.add(InheritanceCaseProperty(
                case_id=case.id, property_id=prop_id,
                is_primary=index == 0))
        if resolved_assets:
            case.tai_san_id = resolved_assets[0][1]

    def _sync_participants_and_owner(self, case: InheritanceCase,
                                     legacy_nodes: list,
                                     owner_entity: Optional[int] = None) -> None:
        """Rebuild `participants` + `nguoi_chet_id` từ legacy projection đã
        commit — tương đương `_extract_diagram_participants` +
        `_replace_case_participants` (routers/cases.py:202-257,456-470).

        `owner_entity` (row owner_row_id đã resolve) là nguồn chính xác ở
        v2; khi absent (save path) rơi về scan role=="Owner" như trước.
        Re-implement tại service thay vì import router: routers.cases kéo
        fastapi/jinja2 vào sidecar process. Dung sai service-side: node trỏ
        person ngoài Stage đã bị prune ở `_state_v3`; person trùng /
        deceased trùng / parentPersonId không active → bỏ qua thay vì raise
        (commit đã qua validation, contract không có error tương ứng).
        """
        active_ids = {
            _clean(n.get("personId")) for n in legacy_nodes
            if _clean(n.get("personId"))
            and not n.get("hidden") and not n.get("deleted")
        }
        if owner_entity is None:
            for node in legacy_nodes:
                if node.get("role") == "Owner" and _clean(
                        node.get("personId")):
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
                       state: dict, render_model: Optional[dict],
                       legacy_nodes: Optional[list], now: str, *,
                       domain: str,
                       owner_row_id: Optional[str]) -> dict:
        """case_state_json schemaVersion 3 (§13). inheritance → đầy đủ
        legacy projections cho web cũ; two_party → chỉ state + render_model
        (không engine → không projections)."""
        merged = dict(payload or {})
        diagram = dict(merged.get("diagram")
                       if isinstance(merged.get("diagram"), Mapping) else {})
        if domain == CASE_TYPE_INHERITANCE:
            row_to_entity = {rid: entity
                             for rid, entity, _w in resolved_people}
            entity_allocations = {
                str(row_to_entity[pid]): alloc
                for pid, alloc in (render_model or {}).get(
                    "allocations", {}).items()
                if pid in row_to_entity
            }
            rm = render_model or {}
            diagram.update({
                "state": state,
                "render_model": render_model,
                "engineInput": {"version": 2, "nodes": legacy_nodes},
                "engineResult": {**rm,
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
            merged["owner_row_id"] = owner_row_id
        else:
            for key in ("engineInput", "engineState", "engineResult",
                        "assignments"):
                diagram.pop(key, None)
            diagram.update({
                "state": state,
                "render_model": render_model,
                "updatedAt": now,
            })
            merged.pop("owner_row_id", None)
        merged["schemaVersion"] = PAYLOAD_SCHEMA_VERSION
        merged["case_type"] = domain
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
             # vị trí = index; is_primary giữ projection cho web cũ.
             "is_primary": index == 0}
            for index, (rid, entity, wire) in enumerate(resolved_assets)
        ]
        merged["diagram"] = diagram
        return merged


class _StageCompose:
    """Kết quả `_compose_stage` — people/assets là wire v2 (không cờ nội
    bộ); persisted_* giữ `is_primary` theo vị trí cho repersist."""

    __slots__ = ("payload", "people", "assets", "entity_to_row",
                 "persisted_people", "persisted_assets", "data_warnings",
                 "legacy_notes", "dirty")

    def __init__(self, payload, people, assets, entity_to_row,
                 persisted_people, persisted_assets, data_warnings,
                 legacy_notes, dirty):
        self.payload = payload
        self.people = people
        self.assets = assets
        self.entity_to_row = entity_to_row
        self.persisted_people = persisted_people
        self.persisted_assets = persisted_assets
        self.data_warnings = data_warnings      # [{code,message}] §13.3
        self.legacy_notes = legacy_notes        # [str] → diagram.warnings
        self.dirty = dirty


def _prune_positions(nodes: list[dict], asset_count: int) -> int:
    """Bỏ dấu chọn tới vị trí > len(assets) (§13.3/§13.4 — prune tại
    commit/save trong cùng transaction, không reject). → số chọn đã gỡ."""
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
    """§13.6: commit stage đồng bộ node `owner` (không deleted) →
    personId := stage.owner_row_id. Không node owner → bỏ qua (owner là
    con trỏ stage, không bắt buộc node trên sơ đồ)."""
    for node in nodes or []:
        if node.get("id") == "owner" and node.get("deleted") is not True:
            node["personId"] = owner_row_id
            return


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

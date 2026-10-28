"""Inheritance workspace service — backend thật cho notary.diagram_evaluate
và notary.diagram_save (contract notary.case-drafting.v2 §13.4–§13.5).

`Diagram` hiển thị trên canvas, `Pool` là projection: Stage committed
trừ đi personId đã được gán trên các node — không có storage riêng.
Sidecar handlers (`shell/sidecar/notary_adapter.py`) chỉ định tuyến;
mọi rule nghiệp vụ nằm ở đây hoặc `case_workspace.py` (MIN-109, nâng cấp
v2 ở MIN-128).

Wire diagram state V3 (§13.4):
    {"version": 3, "domain": "inheritance" | "two_party",
     "nodes": [node_v3_inheritance | node_v3_two_party]}
- inheritance node: {id, personId, parentSlotIds, spouseSlotIds,
  spouseSlotId mirror, spouseSuggestionId,
  ownPositions ⊆ {1,2,3}, receivePositions ⊆ {1,2,3}, hidden, deleted}
- two_party node: đúng 30 phần tử theo thứ tự canonical {id ∈ p1..p30,
  personId, hidden, deleted} — ô trống giữ chỗ, KHÔNG compact; domain
  này không chạy engine thừa kế (render_model status "unsupported").

Persist path nào cũng normalize state về đúng shape trước khi ghi
(`_persisted_state`); evaluate KHÔNG persist và KHÔNG tăng revision.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Optional

from models import InheritanceCase, case_saved_at
from services.inheritance_engine import run_inheritance_case
from services.case_workspace import (
    CASE_TYPE_INHERITANCE,
    CASE_TYPE_TWO_PARTY,
    CASE_TYPES,
    DIAGRAM_STATE_VERSION,
    POSITION_VALUES,
    SCHEMA_VERSION,
    WorkspaceError,
    _case_meta,
    _check_extra_keys,
    _is_uuid4,
    _project_role_nodes,
    _prune_positions,
    _STAGE_KEYS,
    _to_int,
    _utc_now_iso,
    _v3_to_v2_nodes,
    unsupported_render_model,
)


_INHERITANCE_NODE_FIELDS = {
    "id", "personId", "parentSlotIds", "spouseSlotId", "spouseSlotIds",
    "spouseSuggestionId", "ownPositions",
    "receivePositions", "hidden", "deleted", "noSpouseChildren"}
_TWO_PARTY_NODE_FIELDS = {"id", "personId", "hidden", "deleted"}
_TWO_PARTY_IDS = tuple(f"p{i}" for i in range(1, 31))
_TWO_PARTY_ID_SET = set(_TWO_PARTY_IDS)
_POSITIONS = POSITION_VALUES
# --------------------------------------------------------------- wire check


def _validate_diagram_wire(state: Any) -> list:
    """diagram_state_v3 (§13.4/§13.5) → [errors] cho `diagram_invalid_state`.

    `personId` không phải uuid4 KHÔNG thuộc nhóm này — caller map sang
    `diagram_reference_outside_stage` (nhất quán validator: personId sai
    định dạng hoặc ngoài stage đều là reference error). Domain khác
    `case_type` được caller trả `diagram_domain_mismatch` TRƯỚC khi gọi.
    """
    if not isinstance(state, Mapping):
        return [{"code": "invalid_input",
                 "message": "diagram.state phải là object"}]
    errors = []
    if state.get("version") != DIAGRAM_STATE_VERSION:
        errors.append({
            "code": "invalid_version",
            "message": f"diagram.state.version phải = {DIAGRAM_STATE_VERSION}"})
    domain = state.get("domain")
    if domain not in CASE_TYPES:
        errors.append({
            "code": "invalid_domain",
            "message": "diagram.state.domain phải ∈ "
                       f"{list(CASE_TYPES)}"})
    raw_nodes = state.get("nodes")
    if not isinstance(raw_nodes, list):
        errors.append({
            "code": "invalid_type",
            "message": "diagram.state.nodes phải là danh sách"})
        return errors

    two_party = domain == CASE_TYPE_TWO_PARTY
    ids = set()
    node_by_id: dict = {}
    persons: set = set()
    for i, node in enumerate(raw_nodes):
        if not isinstance(node, Mapping):
            errors.append({"code": "invalid_type",
                           "message": f"nodes[{i}] phải là object"})
            continue
        nid = node.get("id")
        allowed = (_TWO_PARTY_NODE_FIELDS if two_party
                   else _INHERITANCE_NODE_FIELDS)
        extra_keys = set(node) - allowed
        if extra_keys:
            errors.append({
                "code": "invalid_node",
                "message": f"nodes[{i}] có field lạ {sorted(extra_keys)}"})
        if two_party:
            # Canonical: đúng slot tại đúng thứ tự — id ngoài p1..p30 hoặc
            # sai thứ tự → invalid_position; thiếu slot → missing_position.
            if not isinstance(nid, str):
                errors.append({"code": "invalid_node_id",
                               "message": f"nodes[{i}].id phải là chuỗi"})
            elif nid not in _TWO_PARTY_ID_SET or i >= 30 \
                    or nid != f"p{i + 1}":
                errors.append({
                    "code": "invalid_position",
                    "message": f"nodes[{i}].id={nid!r} — kỳ vọng 'p{i + 1}'"
                               " theo canonical p1..p30"})
            elif nid in ids:
                errors.append({"code": "duplicate_node",
                               "message": f"nodes[{i}].id trùng '{nid}'"})
            else:
                ids.add(nid)
                node_by_id[nid] = node
        else:
            if not isinstance(nid, str) or not nid.strip():
                errors.append({"code": "invalid_node_id",
                               "message": f"nodes[{i}].id phải là chuỗi "
                                          "non-empty"})
                continue
            if nid in ids:
                errors.append({"code": "duplicate_node",
                               "message": f"nodes[{i}].id trùng '{nid}'"})
                continue
            ids.add(nid)
            node_by_id[nid] = node
        # strict booleans (contract: không coerce "false"/1/…)
        for field in ("hidden", "deleted"):
            if not isinstance(node.get(field), bool):
                errors.append({
                    "code": "invalid_boolean",
                    "message": f"nodes[{i}].{field} phải là boolean"})
        pid = node.get("personId")
        if pid is not None and node.get("deleted") is not True:
            if pid in persons:
                errors.append({
                    "code": "duplicate_person",
                    "message": f"nodes[{i}] personId trùng node khác"})
            persons.add(pid)
        if two_party:
            continue
        if domain != CASE_TYPE_INHERITANCE:
            # domain không xác định — đã flag invalid_domain, bỏ kiểm
            # shape sâu để tránh noise.
            continue
        ps = node.get("parentSlotIds")
        if not isinstance(ps, list) or len(ps) > 2 or any(
                not isinstance(p, str) or not p for p in ps):
            errors.append({
                "code": "invalid_parent",
                "message": f"nodes[{i}].parentSlotIds phải là "
                           "mảng ≤2 chuỗi node-id"})
        elif len(set(ps)) != len(ps):
            errors.append({
                "code": "duplicate_parent",
                "message": f"nodes[{i}].parentSlotIds có trùng"})
        elif nid in ps:
            errors.append({
                "code": "self_parent",
                "message": f"nodes[{i}] tự trỏ làm cha/mẹ"})
        spouse_ids = node.get("spouseSlotIds")
        if not isinstance(spouse_ids, list) or any(
                not isinstance(spouse_id, str) or not spouse_id
                for spouse_id in spouse_ids):
            errors.append({
                "code": "invalid_spouse_slots",
                "message": f"nodes[{i}].spouseSlotIds phải là mảng chuỗi"})
            spouse_ids = []
        elif len(set(spouse_ids)) != len(spouse_ids):
            errors.append({
                "code": "duplicate_spouse",
                "message": f"nodes[{i}].spouseSlotIds không được trùng"})
        elif nid in spouse_ids:
            errors.append({
                "code": "self_spouse",
                "message": f"nodes[{i}] tự trỏ làm vợ/chồng"})
        suggestion = node.get("spouseSuggestionId")
        if suggestion is not None and (
                not isinstance(suggestion, str) or not suggestion):
            errors.append({
                "code": "invalid_spouse_suggestion",
                "message": f"nodes[{i}].spouseSuggestionId phải là chuỗi hoặc null"})
        for pf in ("ownPositions", "receivePositions"):
            arr = node.get(pf)
            if not isinstance(arr, list):
                errors.append({
                    "code": "invalid_position",
                    "message": f"nodes[{i}].{pf} phải là mảng ⊆ {{1,2,3}}"})
            elif (any(isinstance(x, bool) or not isinstance(x, int)
                      or x not in _POSITIONS for x in arr)
                    or len(set(arr)) != len(arr)):
                errors.append({
                    "code": "invalid_position",
                    "message": f"nodes[{i}].{pf} phải là mảng ⊆ {{1,2,3}} "
                               "không trùng"})

    if two_party and ids != _TWO_PARTY_ID_SET:
        missing = sorted(_TWO_PARTY_ID_SET - ids, key=lambda s: int(s[1:]))
        errors.append({
            "code": "missing_position",
            "message": f"state two_party thiếu slot canonical {missing}"})

    if domain == CASE_TYPE_INHERITANCE:
        for i, node in enumerate(raw_nodes):
            if not isinstance(node, Mapping):
                continue
            for p in node.get("parentSlotIds") or []:
                if isinstance(p, str) and p not in ids:
                    errors.append({
                        "code": "dangling_parent",
                        "message": f"nodes[{i}] parentSlotIds '{p}' "
                                   "không tồn tại"})
            for spouse_id in node.get("spouseSlotIds") or []:
                if spouse_id not in ids:
                    errors.append({
                        "code": "dangling_spouse",
                        "message": f"nodes[{i}] spouseSlotIds '{spouse_id}' không tồn tại"})
        # Cycle trên cạnh cha-con.
        children = {}
        for node in node_by_id.values():
            for p in node.get("parentSlotIds") or []:
                if p in node_by_id:
                    children.setdefault(p, set()).add(node["id"])
        for start in node_by_id:
            stack, seen, path = [start], set(), set()
            while stack:
                cur = stack.pop()
                if cur in path:
                    errors.append({
                        "code": "ancestry_cycle",
                        "message": f"vòng tổ tiên qua node '{cur}'"})
                    stack = []
                    break
                if cur in seen:
                    continue
                seen.add(cur)
                path.add(cur)
                stack.extend(children.get(cur) or ())
    return errors


# Lỗi engine thuộc nhóm "thiếu dữ kiện để tính" (S3, owner 23/10/2026):
# hồ sơ còn điền dần nên đường Lưu ghi được ở trạng thái incomplete.
# Mọi lỗi cấu trúc khác (wire/reference/domain/quan hệ) vẫn raise.
_INCOMPLETE_ENGINE_CODES = frozenset({"missing_land_owner",
                                      "invalid_death_date"})


def _softened_incomplete(render_model: Mapping[str, Any]) -> Optional[dict]:
    """render_model `invalid` chỉ vì thiếu dữ kiện → bản `incomplete`.

    Trả None khi còn lỗi cấu trúc/không xác định — caller phải raise.
    """
    errors = render_model.get("errors")
    if not isinstance(errors, list) or not errors:
        return None
    if not all(isinstance(e, Mapping)
               and e.get("code") in _INCOMPLETE_ENGINE_CODES
               for e in errors):
        return None
    return {**render_model, "status": "incomplete"}


def _persisted_state(state: Mapping[str, Any]) -> dict:
    """State đã validate → canonical persist shape (§13.4).

    inheritance: đúng 8 field, mảng vị trí unique ⊆ {1,2,3} giữ thứ tự.
    two_party: đúng 30 slot p1..p30 theo thứ tự canonical.
    """
    domain = state["domain"]
    if domain == CASE_TYPE_TWO_PARTY:
        raw = {n["id"]: n for n in state.get("nodes") or []
               if isinstance(n, Mapping)}
        nodes = [{
            "id": pid,
            "personId": (raw.get(pid) or {}).get("personId"),
            "hidden": bool((raw.get(pid) or {}).get("hidden")),
            "deleted": bool((raw.get(pid) or {}).get("deleted")),
        } for pid in _TWO_PARTY_IDS]
    else:
        nodes = [{
            "id": n["id"],
            "personId": n.get("personId"),
            "parentSlotIds": list(n.get("parentSlotIds") or []),
            "spouseSlotIds": list(n.get("spouseSlotIds") or []),
            "spouseSlotId": (n.get("spouseSlotIds") or [None])[-1],
            "spouseSuggestionId": n.get("spouseSuggestionId"),
            "ownPositions": _positions(n.get("ownPositions")),
            "receivePositions": _positions(n.get("receivePositions")),
            "hidden": n["hidden"],
            "deleted": n["deleted"],
        } for n in state["nodes"]]
    return {"version": DIAGRAM_STATE_VERSION, "domain": domain,
            "nodes": nodes}


def _positions(value: Any) -> list:
    if not isinstance(value, list):
        return []
    out = []
    for x in value:
        if (isinstance(x, int) and not isinstance(x, bool)
                and x in _POSITIONS and x not in out):
            out.append(x)
    return out


def _check_person_refs(state: Mapping[str, Any], valid_row_ids: set) -> None:
    """personId: phải uuid4 + thuộc stage (committed hoặc payload stage —
    tuỳ caller truyền) → sai → `diagram_reference_outside_stage`."""
    for node in state["nodes"]:
        pid = node.get("personId")
        if pid is None:
            continue
        if not _is_uuid4(pid) or pid not in valid_row_ids:
            raise WorkspaceError(
                "diagram_reference_outside_stage",
                "personId không thuộc Stage đã commit",
                details={"personId": pid})


# ------------------------------------------------------------------- service


class InheritanceWorkspaceService:
    def __init__(self, db):
        self.db = db

    # ----------------------------------------------------- diagram_evaluate

    def evaluate_diagram(self, case_id: int, state: Any) -> dict:
        """`notary.diagram_evaluate` trên case đã commit — READ-ONLY."""
        case = self._load_case(case_id)
        case_type, _ = _case_meta(case)
        if case_type not in CASE_TYPES:
            raise WorkspaceError(
                "case_type_unsupported",
                f"Loại việc chưa hỗ trợ: {case_type}",
                details={"case_type": case_type})
        self._check_domain(state, case_type)
        errors = _validate_diagram_wire(state)
        if errors:
            raise WorkspaceError(
                "diagram_invalid_state",
                f"diagram state có {len(errors)} lỗi",
                details={"errors": errors})
        composed = self._compose(case)
        valid_rows = {p["row_id"] for p in composed.people}
        _check_person_refs(state, valid_rows)
        if case_type == CASE_TYPE_TWO_PARTY:
            render_model = unsupported_render_model()
        else:
            render_model = self._evaluate_inheritance(
                state, valid_row_ids=valid_rows, people=composed.people)
        return {
            "schema_version": SCHEMA_VERSION,
            "evaluated_revision": case.workspace_revision,
            "render_model": render_model,
        }

    def evaluate_draft(self, payload_case: Any, stage: Any,
                       state: Any) -> dict:
        """`notary.diagram_evaluate` chế độ nháp — không persist."""
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
        ct = (payload_case.get("case_type")
              if isinstance(payload_case, Mapping) else None)
        if not isinstance(ct, str):
            ct = CASE_TYPE_INHERITANCE

        self._check_domain(state, ct)
        errors = _validate_diagram_wire(state)
        if errors:
            raise WorkspaceError(
                "diagram_invalid_state",
                f"diagram state có {len(errors)} lỗi",
                details={"errors": errors})
        from services.case_workspace import CaseWorkspaceService
        # S2/S19 (owner 23/10/2026): chưa chọn Chủ đất hoặc Stage còn lỗi
        # field tùy chọn không chặn "Xem cách tính"; pointer non-null sai
        # vẫn là mâu thuẫn dữ liệu và vẫn raise.
        CaseWorkspaceService._validate_owner_pointer(
            stage, people, ct, allow_unassigned=True)
        field_errors = CaseWorkspaceService(self.db)._validate_stage(
            people, assets, ct)
        row_ids = {p.get("row_id") for p in people
                   if isinstance(p, Mapping)}
        _check_person_refs(state, row_ids)
        if state["domain"] == CASE_TYPE_TWO_PARTY:
            render_model = unsupported_render_model()
        else:
            render_model = self._evaluate_inheritance(
                state, valid_row_ids=row_ids, people=people)
        if field_errors:
            if render_model.get("status") == "complete":
                render_model["status"] = "incomplete"
            render_model["warnings"] = list(
                render_model.get("warnings") or []) + [{
                    "code": "stage.incomplete_fields",
                    "message": f"Stage còn {len(field_errors)} lỗi field"}]
        return {
            "schema_version": SCHEMA_VERSION,
            "evaluated_revision": None,
            "render_model": render_model,
        }

    # ------------------------------------------------- shared diagram prepare

    def prepare_diagram(self, *, case_type: str, stage: Mapping[str, Any],
                        state: Any,
                        previous_stage: Optional[Mapping[str, Any]] = None
                        ) -> tuple[dict, dict, list]:
        """Validate/prune/evaluate Diagram thuần — không ghi, không commit.

        Trả `(clean_state, render_model, warnings)`. Ref tới row đã bị xóa
        khỏi chính case (có trong `previous_stage`) được gỡ; UUID chưa
        từng thuộc bản trước/payload là `diagram_reference_outside_stage`.

        Ranh giới lỗi (S3, owner 23/10/2026): lỗi CẤU TRÚC — wire v3,
        reference ngoài Stage, owner mismatch, quan hệ/chu kỳ engine —
        vẫn raise `diagram_invalid_state`/mã riêng. Lỗi chỉ vì THIẾU DỮ
        KIỆN để tính (`missing_land_owner`, `invalid_death_date`) trả
        render_model `incomplete` để đường Lưu ghi được; đường evaluate
        vẫn báo nguyên trạng thái chưa tính được của engine.
        """
        self._check_domain(state, case_type)
        errors = _validate_diagram_wire(state)
        if errors:
            raise WorkspaceError(
                "diagram_invalid_state",
                f"diagram state có {len(errors)} lỗi",
                details={"errors": errors})
        people = stage.get("people")
        assets = stage.get("assets")
        if not isinstance(people, list) or not isinstance(assets, list):
            raise WorkspaceError(
                "validation_error",
                "stage.people/stage.assets phải là danh sách")
        valid_rows = {p["row_id"] for p in people if isinstance(p, Mapping)}
        previous_rows = {
            p.get("row_id") for p in (previous_stage or {}).get("people", [])
            if isinstance(p, Mapping)}
        nodes = []
        for node in state["nodes"]:
            pid = node.get("personId")
            if pid is not None and pid not in valid_rows:
                if pid in previous_rows:
                    node = {**node, "personId": None}
                else:
                    raise WorkspaceError(
                        "diagram_reference_outside_stage",
                        "personId không thuộc Stage của payload",
                        details={"personId": pid})
            nodes.append(node)
        checked = {**state, "nodes": nodes}
        _check_person_refs(checked, valid_rows)

        owner_row_id = stage.get("owner_row_id")
        warnings: list = []
        if case_type == CASE_TYPE_INHERITANCE:
            for node in nodes:
                if (node.get("id") == "owner"
                        and node.get("deleted") is not True
                        and node.get("personId") is not None
                        and node["personId"] != owner_row_id):
                    raise WorkspaceError(
                        "diagram_owner_mismatch",
                        "node owner.personId phải khớp stage.owner_row_id",
                        details={"owner_row_id": owner_row_id,
                                 "node_personId": node["personId"]})
        clean_state = _persisted_state(checked)
        if case_type == CASE_TYPE_INHERITANCE:
            pruned = _prune_positions(clean_state["nodes"], len(assets))
            if pruned:
                warnings.append({
                    "code": "diagram.selection_pruned",
                    "message": "Dấu chọn tài sản ngoài vị trí hiện có "
                               "đã được gỡ"})
            render_model = self._evaluate_inheritance(
                clean_state, valid_row_ids=valid_rows, people=people)
            if render_model.get("status") == "invalid":
                softened = _softened_incomplete(render_model)
                if softened is None:
                    raise WorkspaceError(
                        "diagram_invalid_state",
                        "diagram state bị engine từ chối",
                        details={"errors": render_model.get("errors") or []})
                render_model = softened
        else:
            render_model = unsupported_render_model()
        return clean_state, render_model, warnings

    # -------------------------------------------------------- diagram_save

    def save_diagram(self, case_id: int, base_revision: int,
                     state: Any) -> dict:
        """`notary.diagram_save` — persist Diagram JSON v4, giữ status;
        revision+1 (§13.4). Không rewrite Stage/master."""
        case = self._load_case(case_id)
        case_type, _ = _case_meta(case)
        if case_type not in CASE_TYPES:
            raise WorkspaceError(
                "case_type_unsupported",
                f"Loại việc chưa hỗ trợ: {case_type}",
                details={"case_type": case_type})
        if (not isinstance(base_revision, int)
                or isinstance(base_revision, bool) or base_revision < 1):
            raise WorkspaceError(
                "validation_error", "base_revision phải là số nguyên ≥ 1")
        server_revision = case.workspace_revision
        if base_revision != server_revision:
            raise WorkspaceError(
                "workspace_conflict",
                f"Revision server hiện là {server_revision}, "
                f"base_revision={base_revision}",
                details={"server_revision": server_revision})

        try:
            from services.case_workspace import CaseWorkspaceService
            case_ws = CaseWorkspaceService(self.db)
            composed = self._compose(case)
            valid_rows = {p["row_id"] for p in composed.people}
            committed_state = case_ws._state_v3(
                composed.payload, domain=case_type,
                valid_row_ids=valid_rows,
                asset_count=len(composed.assets),
                person_rows={p["row_id"]: p for p in composed.people})
            owner_row_id = None
            if case_type == CASE_TYPE_INHERITANCE:
                owner_row_id = case_ws._resolve_owner_row_id(
                    composed.payload, committed_state, valid_rows)
            stage_view = {
                "people": composed.people,
                "assets": composed.assets,
                "owner_row_id": owner_row_id,
            }
            clean_state, render_model, diagram_warnings =                 self.prepare_diagram(case_type=case_type,
                                     stage=stage_view, state=state)

            now = _utc_now_iso()
            case.case_state_json = json.dumps(
                case_ws._build_payload(
                    composed.payload, clean_state, render_model, now,
                    domain=case_type, owner_row_id=owner_row_id,
                    warnings=diagram_warnings),
                ensure_ascii=False)
            case.engine_state_json = None
            if case_type == CASE_TYPE_INHERITANCE:
                role_nodes = _project_role_nodes(
                    clean_state["nodes"], composed.people)
                case_ws._sync_participants_and_owner(
                    case, role_nodes, composed.people, owner_row_id)
            self.db.flush()

            new_revision = server_revision + 1
            from sqlalchemy import text as sa_text
            saved_at = case_saved_at()
            updated = self.db.execute(sa_text(
                "UPDATE inheritance_cases "
                "SET workspace_revision = :rev, updated_at = :now "
                "WHERE id = :cid AND workspace_revision = :base"),
                {"rev": new_revision, "now": saved_at, "cid": case.id,
                 "base": server_revision})
            if updated.rowcount != 1:
                self.db.rollback()
                fresh = case_ws._fresh_revision(case.id, server_revision)
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

        diagram_out = {"state": clean_state, "render_model": render_model}
        if diagram_warnings:
            diagram_out["warnings"] = diagram_warnings
        return {
            "schema_version": SCHEMA_VERSION,
            "revision": new_revision,
            "diagram": diagram_out,
        }

    # ------------------------------------------------------------- internals

    @staticmethod
    def _check_domain(state: Any, case_type: str) -> None:
        """state.domain hợp lệ nhưng khác case_type hiệu lực →
        `diagram_domain_mismatch` — kiểm TRƯỚC wire validation."""
        if isinstance(state, Mapping):
            domain = state.get("domain")
            if domain in CASE_TYPES and domain != case_type:
                raise WorkspaceError(
                    "diagram_domain_mismatch",
                    "state.domain không khớp case.case_type",
                    details={"expected": case_type, "got": domain})

    def _evaluate_inheritance(self, state: Mapping[str, Any], *,
                              valid_row_ids: set,
                              people: list) -> dict:
        """Bọc engine thừa kế + Pool warning — CHỈ cho domain inheritance."""
        v3_nodes = [n for n in state["nodes"]
                    if n.get("personId") in valid_row_ids
                    or n.get("personId") is None]
        people_by_id = {
            p["row_id"]: {"ngay_chet": p.get("ngay_chet"),
                          "loai_giay_to": p.get("loai_giay_to")}
            for p in people}
        render_model = run_inheritance_case(
            {"version": 2, "nodes": _v3_to_v2_nodes(v3_nodes)},
            people_by_id)
        assigned = {
            n.get("personId") for n in v3_nodes if n.get("personId")}
        unassigned = valid_row_ids - assigned
        warnings = list(render_model.get("warnings") or [])
        warned = {w.get("code") for w in warnings}
        for row_id in sorted(unassigned):
            if "diagram.unassigned_pool_person" not in warned:
                warnings.append({
                    "code": "diagram.unassigned_pool_person",
                    "message": "Người trong Stage chưa được gán trên sơ đồ"})
                warned.add("diagram.unassigned_pool_person")
            if (people_by_id.get(row_id, {}).get("ngay_chet") is None
                    and "diagram.missing_death_date" not in warned):
                warnings.append({
                    "code": "diagram.missing_death_date",
                    "message": "Người trong Stage chưa có ngày chết"})
                warned.add("diagram.missing_death_date")
        render_model["warnings"] = warnings
        if unassigned and render_model.get("status") == "complete":
            render_model["status"] = "incomplete"
        return render_model

    def _compose(self, case: InheritanceCase):
        """Stage wire đọc từ rows Storage B (không persist khi đọc)."""
        from services.case_workspace import CaseWorkspaceService
        return CaseWorkspaceService(self.db)._compose_stage(case)

    def _load_case(self, case_id: int) -> InheritanceCase:
        cid = _to_int(case_id)
        case = self.db.get(InheritanceCase, cid) if cid else None
        if case is None:
            raise WorkspaceError(
                "case_not_found", f"Không tìm thấy hồ sơ #{case_id}",
                details={"case_id": case_id})
        return case

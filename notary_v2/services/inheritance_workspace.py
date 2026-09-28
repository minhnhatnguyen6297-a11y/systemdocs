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

- inheritance node: {id, personId, parentSlotIds, spouseSlotId,
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

from models import InheritanceCase
from services.inheritance_engine import run_inheritance_case
from services.case_workspace import (
    CASE_TYPE_INHERITANCE,
    CASE_TYPE_TWO_PARTY,
    CASE_TYPES,
    DIAGRAM_STATE_VERSION,
    SCHEMA_VERSION,
    WorkspaceError,
    _case_meta,
    _check_extra_keys,
    _is_uuid4,
    _people_map,
    _prune_positions,
    _STAGE_KEYS,
    _to_int,
    _utc_now_iso,
    _v2_to_legacy_nodes,
    _v3_to_v2_nodes,
    unsupported_render_model,
)


_INHERITANCE_NODE_FIELDS = {
    "id", "personId", "parentSlotIds", "spouseSlotId",
    "ownPositions", "receivePositions", "hidden", "deleted"}
_TWO_PARTY_NODE_FIELDS = {"id", "personId", "hidden", "deleted"}
_TWO_PARTY_IDS = tuple(f"p{i}" for i in range(1, 31))
_TWO_PARTY_ID_SET = set(_TWO_PARTY_IDS)
_POSITIONS = (1, 2, 3)


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
        sl = node.get("spouseSlotId")
        if sl is not None and (not isinstance(sl, str) or not sl):
            errors.append({
                "code": "invalid_spouse",
                "message": f"nodes[{i}].spouseSlotId phải là chuỗi node-id "
                           "hoặc null"})
        elif sl == nid:
            errors.append({
                "code": "self_spouse",
                "message": f"nodes[{i}] tự trỏ làm vợ/chồng"})
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
            sl = node.get("spouseSlotId")
            if isinstance(sl, str) and sl not in ids:
                errors.append({
                    "code": "dangling_spouse",
                    "message": f"nodes[{i}] spouseSlotId '{sl}' không tồn tại"})
            elif (isinstance(sl, str) and sl in node_by_id
                    and node_by_id[sl].get("spouseSlotId")
                    != node.get("id")):
                errors.append({
                    "code": "spouse_conflict",
                    "message": f"nodes[{i}] và '{sl}' không link vợ-chồng "
                               "hai chiều"})
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
            "spouseSlotId": n.get("spouseSlotId"),
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
        """`notary.diagram_evaluate` trên case đã commit — READ-ONLY:
        không persist, không tăng revision (§13.4 A5). Cho phép trên case
        locked (đọc)."""
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
        """`notary.diagram_evaluate` chế độ nháp (case_id absent, §13.4):
        stage/diagram từ payload; không persist, evaluated_revision=null.

        `payload_case` (optional): `{case_type}` — domain hiệu lực của
        nháp; absent → "inheritance" (nhất quán `_payload_case_type` của
        validator: payload.case.case_type > default inheritance)."""
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
        owner_row_id = CaseWorkspaceService._validate_owner_pointer(
            stage, people, ct)
        field_errors = CaseWorkspaceService(self.db)._validate_stage(
            people, assets, ct)
        if field_errors:
            raise WorkspaceError(
                "stage_validation_error",
                f"Stage có {len(field_errors)} lỗi field",
                details={"field_errors": field_errors})
        row_ids = {p["row_id"] for p in people}
        _check_person_refs(state, row_ids)
        if state["domain"] == CASE_TYPE_TWO_PARTY:
            render_model = unsupported_render_model()
        else:
            render_model = self._evaluate_inheritance(
                state, valid_row_ids=row_ids, people=people)
        return {
            "schema_version": SCHEMA_VERSION,
            "evaluated_revision": None,
            "render_model": render_model,
        }

    # -------------------------------------------------------- diagram_save

    def save_diagram(self, case_id: int, base_revision: int,
                     state: Any) -> dict:
        """`notary.diagram_save` — atomic: persist state + render_model +
        revision+1 (§13.4). Prune dấu chọn ngoài vị trí asset trong cùng
        transaction + warning `diagram.selection_pruned` trên result."""
        case = self._load_case(case_id)
        if case.is_locked:
            raise WorkspaceError(
                "workspace_locked", f"Hồ sơ #{case_id} đang bị khóa")
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
        self._check_domain(state, case_type)
        errors = _validate_diagram_wire(state)
        if errors:
            raise WorkspaceError(
                "diagram_invalid_state",
                f"diagram state có {len(errors)} lỗi",
                details={"errors": errors})

        try:
            from services.case_workspace import CaseWorkspaceService
            case_ws = CaseWorkspaceService(self.db)
            composed = self._compose(case)
            valid_rows = {p["row_id"] for p in composed.people}
            committed_state, _ = case_ws._state_v3(
                case, composed.payload, composed.entity_to_row,
                domain=case_type, valid_row_ids=valid_rows,
                asset_count=len(composed.assets))
            owner_row_id = None
            if case_type == CASE_TYPE_INHERITANCE:
                owner_row_id = case_ws._resolve_owner_row_id(
                    composed.payload, committed_state, valid_rows)
                owner_pid = next(
                    (n.get("personId") for n in state["nodes"]
                     if n.get("id") == "owner" and n.get("deleted") is not True
                     and n.get("personId") is not None), None)
                if owner_pid is not None and owner_pid != owner_row_id:
                    raise WorkspaceError(
                        "diagram_owner_mismatch",
                        "node owner.personId phải khớp stage.owner_row_id "
                        "đã commit",
                        details={"owner_row_id": owner_row_id,
                                 "node_personId": owner_pid})
            _check_person_refs(state, valid_rows)

            clean_state = _persisted_state(state)
            diagram_warnings = []
            resolved_people = [
                (p["row_id"], _to_int(p.get("id")) or p.get("id"), p)
                for p in composed.persisted_people]
            resolved_assets = [
                (a["row_id"], _to_int(a.get("id")) or a.get("id"), a)
                for a in composed.persisted_assets]
            if case_type == CASE_TYPE_INHERITANCE:
                if _prune_positions(
                        clean_state["nodes"], len(composed.assets)):
                    diagram_warnings.append({
                        "code": "diagram.selection_pruned",
                        "message": "Dấu chọn tài sản ngoài vị trí hiện có "
                                   "đã được gỡ"})
                people_map = _people_map(resolved_people)
                people_by_id = {p["row_id"]: {"ngay_chet": p["ngay_chet"]}
                                for p in composed.people}
                render_model = run_inheritance_case(
                    {"version": 2,
                     "nodes": _v3_to_v2_nodes(clean_state["nodes"])},
                    people_by_id)
                legacy_nodes = _v2_to_legacy_nodes(
                    _v3_to_v2_nodes(clean_state["nodes"]), people_map)
            else:
                render_model = unsupported_render_model()
                legacy_nodes = None

            now = _utc_now_iso()
            case.case_state_json = json.dumps(
                case_ws._build_payload(
                    composed.payload, resolved_people,
                    resolved_assets, clean_state, render_model,
                    legacy_nodes, now, domain=case_type,
                    owner_row_id=owner_row_id),
                ensure_ascii=False)
            if case_type == CASE_TYPE_INHERITANCE:
                case.engine_state_json = json.dumps(
                    {"version": 2, "updatedAt": now, "nodes": legacy_nodes},
                    ensure_ascii=False)
                case_ws._sync_participants_and_owner(case, legacy_nodes)
            self.db.flush()

            new_revision = server_revision + 1
            from sqlalchemy import text as sa_text
            updated = self.db.execute(sa_text(
                "UPDATE inheritance_cases SET workspace_revision = :rev "
                "WHERE id = :cid AND workspace_revision = :base"),
                {"rev": new_revision, "cid": case.id,
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
        `diagram_domain_mismatch` — kiểm TRƯỚC wire validation (§13.5;
        domain invalid → `diagram_invalid_state` ở wire check sau đó)."""
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
        """Bọc engine thừa kế + Pool warning — CHỈ cho domain inheritance.

        Pool = Stage committed − personId đã assign trên node → warning
        `diagram.unassigned_pool_person` (+ `diagram.missing_death_date`
        nếu engine chưa báo)."""
        v3_nodes = [n for n in state["nodes"]
                    if n.get("personId") in valid_row_ids
                    or n.get("personId") is None]
        people_by_id = {
            p["row_id"]: {"ngay_chet": p.get("ngay_chet")}
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
        # Pool còn người chưa gán → draft chưa hoàn chỉnh (giữ semantics
        # v1 + mock: chỉ hạ status khi engine tính xong trọn vẹn).
        if unassigned and render_model.get("status") == "complete":
            render_model["status"] = "incomplete"
        return render_model

    def _compose(self, case: InheritanceCase):
        """Reuse seam compose của case_workspace — đọc stage committed theo
        đúng normalize (row_id/entity_id) mà không persist migrate-on-read
        (evaluate/save tự persist riêng qua _build_payload)."""
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

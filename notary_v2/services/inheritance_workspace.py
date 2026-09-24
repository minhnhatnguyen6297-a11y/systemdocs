"""Inheritance diagram workspace — backend thật cho `notary.diagram_evaluate`
và `notary.diagram_save` (MIN-109, contract `notary.case-drafting.v1` §7).

Sở hữu business rule của hai command Diagram; sidecar handlers chỉ dịch
payload ↔ service, không chứa nghiệp vụ. Tái dùng seam của
`services.case_workspace` (MIN-107): stage đã commit, revision guard,
legacy projection (`_v2_to_legacy_nodes`), participant/owner sync,
`_build_payload`. Engine `services.inheritance_engine` là nơi duy nhất
tính tỷ lệ — service không tự tính.

Semantics contract §7 + drafting-tab §2/§6:

- `diagram_evaluate` read-only theo DB — được phép trên case `locked`;
  không persist draft state, không đổi Stage, không đổi revision.
- `diagram_save` atomic write: validate state → evaluate → persist →
  `revision+1` → commit. Save không đổi `stage.people`/`stage.assets`.
- `personId` trên mọi node (kể cả `hidden`/`deleted`) phải là `row_id`
  của một dòng Người trong Stage đã commit →
  `diagram_reference_outside_stage`.
- Wire state là ENGINE V2 (`parentSlotIds[]`, `spouseSlotId`, boolean
  strict). Legacy JS fields (`parentSlotId`, `parentPersonId`,
  `familyGroupId`, `sourceId`, `role`, `relationType`, `person`, `kind`)
  không thuộc wire → `diagram_invalid_state`.
- Pool = Stage đã commit − người đang được gán trên Diagram (projection,
  không persist): còn người chưa gán → warning
  `diagram.unassigned_pool_person` + status downgrade `incomplete`.
- Chỉ hai quyết định trên card: `Chủ đất` (isLandOwner) và `Nhận`
  (willReceive); không suy "Từ chối" từ "không nhận".
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text as sa_text

from models import InheritanceCase
from services.case_workspace import (
    CASE_TYPE_INHERITANCE,
    SCHEMA_VERSION,
    CaseWorkspaceService,
    WorkspaceError,
    _case_meta,
    _is_uuid4,
    _people_map,
    _utc_now_iso,
    _v2_to_legacy_nodes,
)
from services.inheritance_engine import run_inheritance_case


_NODE_BOOL_FIELDS = ("isLandOwner", "willReceive", "hidden", "deleted")
_NODE_FIELDS = {"id", "personId", "parentSlotIds", "spouseSlotId",
                *_NODE_BOOL_FIELDS}

# Engine error codes là outcome nghiệp vụ — ở lại trong
# `render_model.errors[]` (status=invalid/unsupported), KHÔNG phải job
# error. Mọi code cấu trúc khác (§7.3) → `diagram_invalid_state`.
_OUTCOME_ERROR_CODES = {
    "missing_land_owner", "invalid_death_date", "conservation_failed",
    # reserved cho status=unsupported (contract §7.3) — nếu engine sau
    # này emit, chúng thuộc render_model, không phải job error.
    "second_order_required", "representation_depth_exceeded",
}


def _err(code: str, message: str, **details: Any) -> dict:
    return {"code": code, "message": message, **details}


def _validate_diagram_wire(state: Any) -> list[dict]:
    """Validate shape wire `diagram_state` (contract §7.1 + schema
    `common.schema.json#/definitions/diagram_state`).

    Tra danh sách error dict mang engine code §7.3 — caller raise
    `diagram_invalid_state` khi list non-empty. Phạm vi kiểm: mọi node
    (kể cả `hidden`/`deleted` — slot lỗi cấu trúc vẫn là lỗi wire).
    """
    errors: list[dict] = []
    if not isinstance(state, Mapping):
        return [_err("invalid_input", "diagram state phải là object")]
    if state.get("version") != 2:
        errors.append(_err(
            "invalid_version",
            f"version={state.get('version')!r} — wire chỉ nhận literal 2"))
    nodes = state.get("nodes")
    if not isinstance(nodes, list):
        errors.append(_err("invalid_nodes", "nodes phải là danh sách"))
        return errors

    ids: set[str] = set()
    persons: dict[str, list[str]] = {}
    for index, node in enumerate(nodes):
        where = f"nodes[{index}]"
        if not isinstance(node, Mapping):
            errors.append(_err("invalid_node",
                               f"{where} không phải object", nodeId=where))
            continue
        nid = node.get("id")
        if not (isinstance(nid, str) and nid.strip()):
            errors.append(_err("missing_node_id",
                               f"{where} thiếu id", nodeId=where))
            nid = None
        elif nid in ids:
            errors.append(_err("duplicate_node_id",
                               f"trùng node id {nid!r}", nodeId=nid))
        else:
            ids.add(nid)
        for field in _NODE_BOOL_FIELDS:
            if not isinstance(node.get(field), bool):
                errors.append(_err(
                    "invalid_boolean",
                    f"{where}.{field} phải là boolean strict",
                    nodeId=nid or where, field=field))
        pid = node.get("personId")
        if pid is not None:
            if not _is_uuid4(pid):
                errors.append(_err(
                    "invalid_node",
                    f"{where}.personId phải là uuid4 hoặc null",
                    nodeId=nid or where))
            else:
                persons.setdefault(pid, []).append(nid or where)
        for key in set(node) - _NODE_FIELDS:
            # Legacy JS fields không thuộc wire V2 (contract §7.1)
            errors.append(_err(
                "invalid_node", f"{where} field lạ {key!r}",
                nodeId=nid or where))
        parents = node.get("parentSlotIds")
        if not (isinstance(parents, list) and all(
                isinstance(p, str) and p.strip() for p in parents)):
            errors.append(_err(
                "invalid_parent_slots",
                f"{where}.parentSlotIds phải là list[string non-empty]",
                nodeId=nid or where))
            parents = []
        if len(parents) > 2:
            errors.append(_err("too_many_parents",
                               f"{where} quá 2 parent slots",
                               nodeId=nid or where))
        if nid and nid in parents:
            errors.append(_err("self_parent",
                               f"{nid} tự làm cha/mẹ", nodeId=nid))
        spouse = node.get("spouseSlotId")
        if spouse is not None and not (
                isinstance(spouse, str) and spouse.strip()):
            errors.append(_err(
                "invalid_node",
                f"{where}.spouseSlotId phải là string non-empty hoặc null",
                nodeId=nid or where))
        if nid and spouse == nid:
            errors.append(_err("self_spouse",
                               f"{nid} tự làm vợ/chồng", nodeId=nid))

    node_by_id = {n.get("id"): n for n in nodes
                  if isinstance(n, Mapping) and n.get("id")}
    for pid, slots in persons.items():
        # `deleted` không chiếm slot; `hidden` vẫn tính là đang gán —
        # một người trên ≥2 node chưa-xóa là state mơ hồ.
        active = [s for s in slots
                  if not (node_by_id.get(s) or {}).get("deleted")]
        if len(active) > 1:
            errors.append(_err(
                "duplicate_person",
                "một người không được gán trên nhiều node",
                personId=pid))
    for node in nodes:
        if not isinstance(node, Mapping):
            continue
        nid = node.get("id")
        parents = node.get("parentSlotIds")
        for parent in parents if isinstance(parents, list) else []:
            if isinstance(parent, str) and parent not in ids:
                errors.append(_err(
                    "dangling_parent",
                    f"{nid} tham chiếu parent {parent!r} không tồn tại",
                    nodeId=nid))
        spouse = node.get("spouseSlotId")
        if isinstance(spouse, str):
            if spouse not in ids:
                errors.append(_err(
                    "dangling_spouse",
                    f"{nid} tham chiếu spouse {spouse!r} không tồn tại",
                    nodeId=nid))
            else:
                other = node_by_id.get(spouse) or {}
                other_spouse = other.get("spouseSlotId")
                # Engine semantics: link một chiều (other=None) được heal
                # thành đối xứng; chỉ trỏ sang node THỨ BA mới là conflict.
                if other_spouse not in (None, nid):
                    errors.append(_err(
                        "spouse_conflict",
                        f"{nid}↔{spouse} quan hệ vợ/chồng bị lệch",
                        nodeId=nid))
    # Chu kỳ tổ tiên theo slot graph (mọi node, kể cả chưa gán person)
    for nid in ids:
        seen: set[str] = set()
        frontier = list(
            (node_by_id.get(nid) or {}).get("parentSlotIds") or [])
        while frontier:
            cur = frontier.pop()
            if cur == nid:
                errors.append(_err(
                    "ancestry_cycle",
                    f"quan hệ huyết thống tạo chu kỳ qua {nid}",
                    nodeId=nid))
                break
            if cur in seen:
                continue
            seen.add(cur)
            frontier.extend(
                (node_by_id.get(cur) or {}).get("parentSlotIds") or [])
    return errors


def _persisted_state(state: Mapping[str, Any]) -> dict:
    """State đã validate → canonical V2 để persist (đủ 8 field/node)."""
    return {"version": 2, "nodes": [
        {"id": n["id"], "personId": n.get("personId"),
         "parentSlotIds": list(n.get("parentSlotIds") or []),
         "spouseSlotId": n.get("spouseSlotId"),
         "isLandOwner": n.get("isLandOwner", False),
         "willReceive": n.get("willReceive", True),
         "hidden": n.get("hidden", False),
         "deleted": n.get("deleted", False)}
        for n in state["nodes"]]}


class InheritanceWorkspaceService:
    """Compose/evaluate/save Diagram cho một InheritanceCase.

    Giữ một `CaseWorkspaceService` trên cùng session để tái dùng seam
    (compose stage, revision, payload build, participant sync) — không
    re-implement.
    """

    def __init__(self, db):
        self.db = db
        self._ws = CaseWorkspaceService(db)

    # ------------------------------------------------------------- public

    def evaluate_diagram(self, case_id: Any, state: Any) -> dict:
        """`notary.diagram_evaluate` — read-only theo DB (contract §7.4).

        Được phép trên case `locked`; không persist state, không đổi
        Stage, không đổi revision.
        """
        case = self._ws._load_case(case_id)
        case_type, _doc_type = _case_meta(case)
        # case_type: DB hiện chỉ có InheritanceCase — loai_van_ban là
        # discriminator; guard sẵn cho case_type column tương lai (§2.4).
        if case_type != CASE_TYPE_INHERITANCE:
            raise WorkspaceError(
                "case_type_unsupported",
                f"Loại việc chưa hỗ trợ: {case_type}",
                details={"case_type": case_type})
        (_payload, people, _assets, _e2r, _pp, _pa, _w, _dirty) = \
            self._ws._compose_stage(case)
        render_model = self._evaluate_state(
            state, valid_row_ids={p["row_id"] for p in people},
            people=people)
        return {
            "schema_version": SCHEMA_VERSION,
            "evaluated_revision": self._ws._revision(case),
            "render_model": render_model,
        }

    def save_diagram(self, case_id: Any, base_revision: Any,
                     state: Any) -> dict:
        """`notary.diagram_save` — atomic write (contract §7.5).

        Validate lại bằng DB mới nhất trong transaction → evaluate →
        persist state + render_model (+ legacy projection cho web cũ) →
        `revision+1` → commit. Save không đổi Stage.
        """
        case = self._ws._load_case(case_id)
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
        server_revision = self._ws._revision(case)
        if base_revision != server_revision:
            raise WorkspaceError(
                "workspace_conflict",
                f"Revision server hiện là {server_revision}, "
                f"base_revision={base_revision}",
                details={"server_revision": server_revision})

        (payload, people, assets, _e2r, _pp, _pa, _w, _dirty) = \
            self._ws._compose_stage(case)
        render_model = self._evaluate_state(
            state, valid_row_ids={p["row_id"] for p in people},
            people=people)
        clean_state = _persisted_state(state)

        # resolved_* theo đúng tuple shape mà _build_payload/_people_map
        # của commit_stage dùng — stage không đổi, chỉ snapshot lại.
        resolved_people = [
            (p["row_id"], p["entity_id"], p) for p in people]
        resolved_assets = [
            (a["row_id"], a["entity_id"], a) for a in assets]
        people_map = _people_map(resolved_people)
        legacy_nodes = _v2_to_legacy_nodes(
            clean_state["nodes"], people_map)
        now = _utc_now_iso()
        try:
            self._ws._sync_participants_and_owner(case, legacy_nodes)
            case.case_state_json = json.dumps(
                self._ws._build_payload(
                    payload, resolved_people, resolved_assets,
                    clean_state, render_model, legacy_nodes, now),
                ensure_ascii=False)
            case.engine_state_json = json.dumps(
                {"version": 2, "updatedAt": now, "nodes": legacy_nodes},
                ensure_ascii=False)
            self.db.flush()

            # Guarded atomic revision bump — giống commit_stage: 2 save
            # cùng base chỉ 1 cái thắng.
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
                fresh = self._ws._fresh_revision(case.id, server_revision)
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

        return {
            "schema_version": SCHEMA_VERSION,
            "revision": new_revision,
            "diagram": {"state": clean_state,
                        "render_model": render_model},
        }

    # ------------------------------------------------------------- internals

    def _evaluate_state(self, state: Any, valid_row_ids: set,
                        people: list[dict]) -> dict:
        """Validate wire state → check personId ∈ Stage → chạy engine →
        gắn Pool warning. Tra render_model (contract §7.2)."""
        errors = _validate_diagram_wire(state)
        if errors:
            raise WorkspaceError(
                "diagram_invalid_state",
                f"diagram state có {len(errors)} lỗi",
                details={"errors": errors})
        for node in state["nodes"]:
            pid = node.get("personId")
            if pid is not None and pid not in valid_row_ids:
                raise WorkspaceError(
                    "diagram_reference_outside_stage",
                    "personId không thuộc Stage đã commit",
                    details={"personId": pid})

        people_by_id = {
            p["row_id"]: {"ngay_chet": p.get("ngay_chet")}
            for p in people}
        render_model = run_inheritance_case(
            {"version": 2, "nodes": state["nodes"]}, people_by_id)

        # Defense-in-depth: engine reject cấu trúc → job error. Outcome
        # codes (missing_land_owner, invalid_death_date, ...) ở lại
        # trong render_model.errors theo §7.2/§7.3.
        engine_errors = render_model.get("errors") or []
        structural = [e for e in engine_errors
                      if e.get("code") not in _OUTCOME_ERROR_CODES]
        if structural:
            raise WorkspaceError(
                "diagram_invalid_state",
                "diagram state bị engine từ chối",
                details={"errors": engine_errors})

        # Pool invariant (drafting-tab §2): Pool = Stage committed −
        # assigned. `hidden` vẫn tính assigned; `deleted` không.
        if render_model.get("status") != "invalid":
            assigned = {
                n.get("personId") for n in state["nodes"]
                if n.get("personId") and not n.get("deleted")}
            if valid_row_ids - assigned:
                render_model["warnings"].append({
                    "code": "diagram.unassigned_pool_person",
                    "message": "Còn người trong Pool chưa được gán "
                               "trên sơ đồ"})
                if render_model["status"] == "complete":
                    render_model["status"] = "incomplete"
        return render_model

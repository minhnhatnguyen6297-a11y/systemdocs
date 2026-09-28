"""Tests for services.inheritance_workspace — real backend of
notary.diagram_evaluate / notary.diagram_save (MIN-109,
contract notary.case-drafting.v2 §13.4/§13.7).

Uses a temporary SQLite DB per test (tmp_path) — never touches notary.db.
Engine = services.inheritance_engine (ENGINE_VERSION=2); Pool is a derived
projection: committed Stage − personId assigned on Diagram nodes.

v2 wire: diagram_state `{version:3, domain, nodes[]}` — node chủ đất có
`ownPositions` ≠ [], người nhận có `receivePositions` ≠ [] (flags v1
isLandOwner/willReceive đã gỡ khỏi wire; engine vẫn nhận projection v2
qua `_v3_to_v2_nodes` ở service).
"""
import json
import uuid
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database
from models import (
    Customer,
    InheritanceCase,
    InheritanceCaseProperty,
    Property,
)
from services.case_workspace import SCHEMA_VERSION, WorkspaceError
from services.inheritance_workspace import InheritanceWorkspaceService


TP_IDS = [f"p{i}" for i in range(1, 31)]


# ---------------------------------------------------------------- fixtures


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'diagram.db'}")
    database.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


def _seed_case(db, *, trang_thai="draft", loai_van_ban="khai_nhan"):
    """Case với Stage đã commit (4 người) trong case_state_json v3.

    Gia đình: chủ đất đã chết (2011) + vợ sống + con chết trước chủ đất
    (2010) + cháu nội sống — đủ để kiểm chứng nhánh thế vị (representation).
    Trả (case, people{key:Customer}, rows{key:row_id}, prop).
    """
    prop = Property(so_serial="DD123456", dia_chi="Thửa 123, tờ 45")
    people = {
        "owner": Customer(ho_ten="Nguyễn Văn An", gioi_tinh="Nam",
                          ngay_sinh=date(1950, 1, 1),
                          ngay_chet=date(2011, 5, 15)),
        "spouse": Customer(ho_ten="Nguyễn Thị Bình", gioi_tinh="Nữ",
                           ngay_sinh=date(1955, 3, 2)),
        "child": Customer(ho_ten="Nguyễn Văn Con", gioi_tinh="Nam",
                          ngay_sinh=date(1978, 7, 20),
                          ngay_chet=date(2010, 1, 1)),
        "gc": Customer(ho_ten="Nguyễn Văn Cháu", gioi_tinh="Nam",
                       ngay_sinh=date(2000, 6, 6)),
    }
    db.add(prop)
    db.add_all(people.values())
    db.flush()
    case = InheritanceCase(
        nguoi_chet_id=people["owner"].id, tai_san_id=prop.id,
        ngay_lap_ho_so=date(2026, 9, 1), loai_van_ban=loai_van_ban,
        trang_thai=trang_thai)
    db.add(case)
    db.flush()
    db.add(InheritanceCaseProperty(
        case_id=case.id, property_id=prop.id, is_primary=True))
    rows = {key: str(uuid.uuid4()) for key in people}
    case.case_state_json = json.dumps({
        "schemaVersion": 3,
        "owner_row_id": rows["owner"],
        "stage": [{"id": str(c.id), "row_id": rows[k],
                   "ho_ten": c.ho_ten,
                   "ngay_chet": c.ngay_chet.isoformat() if c.ngay_chet
                    else None}
                  for k, c in people.items()],
        "assets": [{"id": str(prop.id), "row_id": str(uuid.uuid4()),
                    "is_primary": True}],
        "diagram": {"state": {"version": 3, "domain": "inheritance",
                              "nodes": []},
                    "render_model": None},
    }, ensure_ascii=False)
    db.commit()
    return case, people, rows, prop


def _node(nid, person_id=None, parents=(), spouse=None, own=(),
          receive=(), hidden=False, deleted=False):
    """diagram node v3 (§13.4)."""
    return {"id": nid, "personId": person_id,
            "parentSlotIds": list(parents), "spouseSlotId": spouse,
            "ownPositions": list(own), "receivePositions": list(receive),
            "hidden": hidden, "deleted": deleted}


def _v3_state(nodes, domain="inheritance"):
    return {"version": 3, "domain": domain, "nodes": nodes}


def _tp_state(**kw):
    nodes = [{"id": f"p{i}", "personId": None,
              "hidden": False, "deleted": False}
             for i in range(1, 31)]
    for pid, person in (kw.get("assign") or {}).items():
        for n in nodes:
            if n["id"] == pid:
                n["personId"] = person
    return {"version": 3, "domain": "two_party", "nodes": nodes}


def _draft_state(rows):
    """Draft hợp lệ (engine V2): chủ đất đã chết + vợ nhận + con đã chết
    trước → cháu thế vị theo nhánh. v3: own/receive positions."""
    return _v3_state([
        _node("owner", rows["owner"], spouse="spouse", own=[1]),
        _node("spouse", rows["spouse"], spouse="owner", receive=[1]),
        _node("child", rows["child"], parents=("owner", "spouse"),
              receive=[1]),
        _node("gc", rows["gc"], parents=("child",), receive=[1]),
    ])


def _svc(db):
    return InheritanceWorkspaceService(db)


def _warning_codes(render_model):
    return [w["code"] for w in render_model["warnings"]]


# --------------------------------------------------------- diagram_evaluate


def test_evaluate_returns_engine_render_model_with_representation(db):
    """Engine output thật: con chết trước chủ đất → cháu thế vị nhận phần
    nhánh của con (kind=representation, viaBranchPersonIds)."""
    case, _people, rows, _prop = _seed_case(db)

    data = _svc(db).evaluate_diagram(case.id, _draft_state(rows))

    assert data["schema_version"] == SCHEMA_VERSION
    assert data["evaluated_revision"] == 1
    rm = data["render_model"]
    assert rm["engineVersion"] == 2
    assert rm["status"] == "complete"
    # owner mất → phân phối 1; vợ + cháu (thế vị con) mỗi người 1/2
    assert rm["allocations"][rows["owner"]] == {
        "baseShare": "1", "inheritedShare": "0",
        "distributedShare": "1", "finalShare": "0",
        "displayPercent": "0.00"}
    assert rm["allocations"][rows["spouse"]]["finalShare"] == "1/2"
    assert rm["allocations"][rows["child"]]["finalShare"] == "0"
    assert rm["allocations"][rows["gc"]]["finalShare"] == "1/2"
    gc_bd = next(b for b in rm["breakdowns"] if b["personId"] == rows["gc"])
    term = gc_bd["terms"][0]
    assert term["kind"] == "representation"
    assert term["fraction"] == "1/2"
    assert term["sourcePersonId"] == rows["owner"]
    assert term["viaBranchPersonIds"] == [rows["child"]]
    assert rm["conservation"] == {
        "allocated": "1", "unresolved": "0", "total": "1"}
    assert rm["warnings"] == []          # Pool rỗng — mọi người đã gán
    assert rm["errors"] == []


def test_evaluate_pool_invariant_warns_when_person_unassigned(db):
    """Pool = Stage committed − assigned: bỏ node cháu khỏi draft → cháu
    về Pool → warning diagram.unassigned_pool_person + status incomplete."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    state["nodes"] = [n for n in state["nodes"] if n["id"] != "gc"]

    data = _svc(db).evaluate_diagram(case.id, state)

    rm = data["render_model"]
    assert rows["gc"] not in rm["allocations"]
    assert "diagram.unassigned_pool_person" in _warning_codes(rm)
    assert rm["status"] == "incomplete"


def test_evaluate_remove_assignment_returns_person_to_pool(db):
    """Xóa assignment (personId → null) → thẻ về Pool (§6 drafting-tab)."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    for n in state["nodes"]:
        if n["id"] == "gc":
            n["personId"] = None

    data = _svc(db).evaluate_diagram(case.id, state)

    assert "diagram.unassigned_pool_person" in _warning_codes(
        data["render_model"])
    assert data["render_model"]["status"] == "incomplete"


def test_evaluate_personid_outside_stage(db):
    """personId không thuộc Stage đã commit → diagram_reference_outside_stage
    kèm details.personId (contract §13.4)."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    outside = str(uuid.uuid4())
    state["nodes"][2]["personId"] = outside

    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_diagram(case.id, state)

    assert exc.value.code == "diagram_reference_outside_stage"
    assert exc.value.details["personId"] == outside


def test_evaluate_rejects_invalid_wire_state(db):
    case, _people, _rows, _prop = _seed_case(db)

    for bad in ({"version": 1, "nodes": []},
                {"version": 2, "nodes": []},          # v1 state → invalid
                {"version": 3, "nodes": "x"},
                {"version": 3, "domain": "sai", "nodes": []},
                "not-a-dict"):
        with pytest.raises(WorkspaceError) as exc:
            _svc(db).evaluate_diagram(case.id, bad)
        assert exc.value.code == "diagram_invalid_state", bad
        assert exc.value.details["errors"]


def test_evaluate_rejects_string_boolean_and_dangling_ref(db):
    case, _people, rows, _prop = _seed_case(db)

    state = _draft_state(rows)
    state["nodes"][0]["hidden"] = "false"     # chuỗi, không phải bool
    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_diagram(case.id, state)
    assert exc.value.code == "diagram_invalid_state"
    assert any(e["code"] == "invalid_boolean"
               for e in exc.value.details["errors"])

    state = _draft_state(rows)
    state["nodes"][2]["parentSlotIds"] = ["no_such_slot"]
    with pytest.raises(WorkspaceError) as exc2:
        _svc(db).evaluate_diagram(case.id, state)
    assert exc2.value.code == "diagram_invalid_state"
    assert any(e["code"] == "dangling_parent"
               for e in exc2.value.details["errors"])


def test_evaluate_rejects_legacy_v1_node_fields(db):
    """v1 flags (isLandOwner/willReceive) + legacy js fields (role, kind,
    parentSlotId) không thuộc wire v3 → invalid_node."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    state["nodes"][0]["isLandOwner"] = True      # v1 flag
    state["nodes"][0]["willReceive"] = False     # v1 flag
    state["nodes"][0]["kind"] = "person"         # legacy field
    state["nodes"][0]["parentSlotId"] = "father"  # legacy field

    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_diagram(case.id, state)
    assert exc.value.code == "diagram_invalid_state"
    codes = {e["code"] for e in exc.value.details["errors"]}
    assert "invalid_node" in codes


def test_evaluate_position_out_of_range_or_dup(db):
    """Positions phải ⊆ {1,2,3} không trùng (§13.4)."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    state["nodes"][0]["ownPositions"] = [1, 4]
    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_diagram(case.id, state)
    assert exc.value.code == "diagram_invalid_state"
    assert any(e["code"] == "invalid_position"
               for e in exc.value.details["errors"])

    state = _draft_state(rows)
    state["nodes"][0]["ownPositions"] = [1, 1]
    with pytest.raises(WorkspaceError) as exc2:
        _svc(db).evaluate_diagram(case.id, state)
    assert exc2.value.code == "diagram_invalid_state"


def test_evaluate_domain_mismatch(db):
    """state.domain hợp lệ nhưng khác case_type → diagram_domain_mismatch
    TRƯỚC wire validation (§13.5)."""
    case, _people, _rows, _prop = _seed_case(db)

    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_diagram(case.id, _tp_state())
    assert exc.value.code == "diagram_domain_mismatch"
    assert exc.value.details["expected"] == "inheritance"
    assert exc.value.details["got"] == "two_party"


def test_evaluate_two_party_unsupported_render(db):
    """two_party committed: state canonical hợp lệ → render_model
    unsupported, không chạy engine thừa kế (§13.5)."""
    case, _people, rows, _prop = _seed_case(
        db, loai_van_ban="chuyen_nhuong")
    state = _tp_state(assign={"p1": rows["owner"]})

    data = _svc(db).evaluate_diagram(case.id, state)

    assert data["evaluated_revision"] == 1
    rm = data["render_model"]
    assert rm["status"] == "unsupported"
    assert rm["allocations"] == {}
    codes = _warning_codes(rm)
    assert "diagram.two_party_unsupported" in codes


def test_evaluate_two_party_bad_canonical(db):
    """Thiếu slot canonical → invalid_state ngay trên committed path."""
    case, _people, _rows, _prop = _seed_case(
        db, loai_van_ban="dat_coc")
    state = _tp_state()
    state["nodes"] = state["nodes"][:29]
    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_diagram(case.id, state)
    assert exc.value.code == "diagram_invalid_state"


def test_evaluate_allowed_on_locked_case(db):
    """Read-only theo DB — được phép trên case locked (contract §7.4)."""
    case, _people, rows, _prop = _seed_case(db, trang_thai="locked")

    data = _svc(db).evaluate_diagram(case.id, _draft_state(rows))

    assert data["render_model"]["status"] == "complete"


def test_evaluate_does_not_persist(db):
    """Evaluate không ghi state, không đổi revision (contract §7.4)."""
    case, _people, rows, _prop = _seed_case(db)
    before = case.case_state_json

    _svc(db).evaluate_diagram(case.id, _draft_state(rows))

    db.refresh(case)
    assert case.case_state_json == before
    assert case.workspace_revision == 1


def test_evaluate_unsupported_case_type(db):
    """case_type ngoài {inheritance,two_party} → case_type_unsupported."""
    case, _people, rows, _prop = _seed_case(db, loai_van_ban="khac")

    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_diagram(case.id, _draft_state(rows))
    assert exc.value.code == "case_type_unsupported"
    assert exc.value.details["case_type"] == "khac"


def test_evaluate_missing_case(db):
    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_diagram(9999, _v3_state([]))
    assert exc.value.code == "case_not_found"


def test_evaluate_missing_land_owner_is_render_model_not_job_error(db):
    """Không có Chủ đất (mọi ownPositions rỗng → engine thấy không
    isLandOwner) → render_model status invalid + errors[missing_land_owner],
    KHÔNG phải job error."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    for n in state["nodes"]:
        n["ownPositions"] = []

    data = _svc(db).evaluate_diagram(case.id, state)

    rm = data["render_model"]
    assert rm["status"] == "invalid"
    assert any(e["code"] == "missing_land_owner" for e in rm["errors"])


def test_evaluate_no_receive_is_not_refusal(db):
    """v3: tắt receivePositions (rỗng) = không nhận phần — không suy 'Từ
    chối'; finalShare 0, phần đi cho người còn lại."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    for n in state["nodes"]:
        if n["id"] == "spouse":
            n["receivePositions"] = []

    data = _svc(db).evaluate_diagram(case.id, state)

    rm = data["render_model"]
    assert rm["status"] == "complete"
    assert rm["allocations"][rows["spouse"]]["finalShare"] == "0"
    # vợ không nhận → chỉ còn nhánh cháu (thế vị) → cháu nhận toàn bộ
    assert rm["allocations"][rows["gc"]]["finalShare"] == "1"


# ------------------------------------------------------------- diagram_save


def test_save_persists_state_render_model_and_bumps_revision(
        db, session_factory):
    case, people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)

    data = _svc(db).save_diagram(case.id, 1, state)

    assert data["schema_version"] == SCHEMA_VERSION
    assert data["revision"] == 2
    assert data["diagram"]["state"] == state
    assert data["diagram"]["state"]["domain"] == "inheritance"
    assert data["diagram"]["render_model"]["status"] == "complete"

    db2 = session_factory()
    try:
        fresh = db2.get(InheritanceCase, case.id)
        assert fresh.workspace_revision == 2
        persisted = json.loads(fresh.case_state_json)
        assert persisted["schemaVersion"] == 3
        assert persisted["diagram"]["state"] == state
        assert persisted["diagram"]["render_model"]["engineVersion"] == 2
        # legacy projection cho web cũ (parity commit_stage)
        engine_state = persisted["diagram"]["engineState"]
        legacy_ids = {n["id"]: n for n in engine_state["nodes"]}
        assert legacy_ids["owner"]["personId"] == str(people["owner"].id)
        assert persisted["diagram"]["assignments"]["owner"] == \
            str(people["owner"].id)
        col = json.loads(fresh.engine_state_json)
        assert col["nodes"][0]["personId"] == str(people["owner"].id)
        # participants + nguoi_chet_id sync theo diagram mới
        assert fresh.nguoi_chet_id == people["owner"].id
        parts = {p.customer_id: p for p in fresh.participants}
        assert people["owner"].id not in parts
        assert parts[people["spouse"].id].vai_tro == "Vợ/Chồng"
        assert parts[people["gc"].id].vai_tro == "Cháu"
        assert parts[people["gc"].id].parent_customer_id == \
            people["child"].id
    finally:
        db2.close()


def test_save_owner_mismatch(db):
    """§13.6: node 'owner' personId ≠ stage.owner_row_id đã commit →
    diagram_owner_mismatch (server không tự sửa)."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    # owner node trỏ sang person khác trong stage (spouse vẫn hợp lệ nhưng
    # node khác giữ person riêng để tránh duplicate_person).
    state["nodes"][0]["personId"] = rows["child"]
    for n in state["nodes"]:
        if n["id"] == "child":
            n["personId"] = None

    with pytest.raises(WorkspaceError) as exc:
        _svc(db).save_diagram(case.id, 1, state)
    assert exc.value.code == "diagram_owner_mismatch"
    assert exc.value.details["owner_row_id"] == rows["owner"]


def test_save_prunes_out_of_range_positions(db):
    """Chọn vị trí > len(assets) → prune + warning diagram.selection_pruned
    trong cùng transaction (§13.3)."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    state["nodes"][0]["ownPositions"] = [1, 3]      # chỉ 1 asset

    data = _svc(db).save_diagram(case.id, 1, state)

    dg = data["diagram"]
    owner = next(n for n in dg["state"]["nodes"] if n["id"] == "owner")
    assert owner["ownPositions"] == [1]
    codes = [w["code"] for w in dg.get("warnings") or []]
    assert "diagram.selection_pruned" in codes


def test_save_does_not_change_stage(db):
    """diagram_save không đổi stage.people/stage.assets (contract §13.7)."""
    case, _people, rows, _prop = _seed_case(db)

    _svc(db).save_diagram(case.id, 1, _draft_state(rows))

    persisted = json.loads(db.get(InheritanceCase, case.id).case_state_json)
    assert {r["row_id"] for r in persisted["stage"]} == set(rows.values())
    assert len(persisted["assets"]) == 1
    assert persisted["owner_row_id"] == rows["owner"]


def test_save_stale_and_ahead_base_revision_conflict(db):
    case, _people, rows, _prop = _seed_case(db)

    # revision 1: base_revision 99 (ahead) → workspace_conflict
    with pytest.raises(WorkspaceError) as ahead:
        _svc(db).save_diagram(case.id, 99, _draft_state(rows))
    assert ahead.value.code == "workspace_conflict"
    assert ahead.value.details["server_revision"] == 1

    _svc(db).save_diagram(case.id, 1, _draft_state(rows))

    # revision 2: base_revision 1 (stale) → workspace_conflict
    with pytest.raises(WorkspaceError) as stale:
        _svc(db).save_diagram(case.id, 1, _draft_state(rows))
    assert stale.value.code == "workspace_conflict"
    assert stale.value.details["server_revision"] == 2


def test_save_locked_case(db):
    case, _people, rows, _prop = _seed_case(db, trang_thai="locked")

    with pytest.raises(WorkspaceError) as exc:
        _svc(db).save_diagram(case.id, 1, _draft_state(rows))
    assert exc.value.code == "workspace_locked"


def test_save_unsupported_case_type(db):
    case, _people, rows, _prop = _seed_case(db, loai_van_ban="khac")

    with pytest.raises(WorkspaceError) as exc:
        _svc(db).save_diagram(case.id, 1, _draft_state(rows))
    assert exc.value.code == "case_type_unsupported"


def test_save_two_party_canonical(db):
    """two_party save: canonical 30 ô + unsupported render + rev bump;
    không engineState/participants inheritance sync (§13.5)."""
    case, _people, rows, _prop = _seed_case(
        db, loai_van_ban="chuyen_nhuong")
    state = _tp_state(assign={"p1": rows["owner"], "p2": rows["spouse"]})

    data = _svc(db).save_diagram(case.id, 1, state)

    assert data["revision"] == 2
    st = data["diagram"]["state"]
    assert st["domain"] == "two_party"
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    assert st["nodes"][0]["personId"] == rows["owner"]
    assert st["nodes"][1]["personId"] == rows["spouse"]
    assert data["diagram"]["render_model"]["status"] == "unsupported"
    persisted = json.loads(
        db.get(InheritanceCase, case.id).case_state_json)
    assert persisted["case_type"] == "two_party"
    assert "owner_row_id" not in persisted
    # projections engine legacy phải bị gỡ trên two_party
    for key in ("engineInput", "engineState", "engineResult", "assignments"):
        assert key not in persisted["diagram"]


def test_save_missing_case(db):
    with pytest.raises(WorkspaceError) as exc:
        _svc(db).save_diagram(9999, 1, _v3_state([]))
    assert exc.value.code == "case_not_found"


def test_save_invalid_state_not_persisted(db):
    """Atomic: state invalid → không persist, revision không đổi (§13.7)."""
    case, _people, _rows, _prop = _seed_case(db)
    before = case.case_state_json

    with pytest.raises(WorkspaceError) as exc:
        _svc(db).save_diagram(case.id, 1, {"version": 1, "nodes": []})
    assert exc.value.code == "diagram_invalid_state"

    db.refresh(case)
    assert case.case_state_json == before
    assert case.workspace_revision == 1


def test_save_personid_outside_stage_not_persisted(db):
    case, _people, rows, _prop = _seed_case(db)
    before = case.case_state_json
    state = _draft_state(rows)
    # Node KHÔNG phải 'owner' — mirror check owner đi trước refs check.
    state["nodes"][1]["personId"] = str(uuid.uuid4())

    with pytest.raises(WorkspaceError) as exc:
        _svc(db).save_diagram(case.id, 1, state)
    assert exc.value.code == "diagram_reference_outside_stage"

    db.refresh(case)
    assert case.case_state_json == before
    assert case.workspace_revision == 1


def test_save_concurrent_same_base_conflicts(db, session_factory):
    """2 save cùng base_revision trên 2 session — chỉ 1 cái thắng (guarded
    UPDATE), cái thua workspace_conflict với server_revision mới."""
    case, _people, rows, _prop = _seed_case(db)
    s1 = session_factory()
    s2 = session_factory()
    try:
        _svc(s1).save_diagram(case.id, 1, _draft_state(rows))
        with pytest.raises(WorkspaceError) as exc:
            _svc(s2).save_diagram(case.id, 1, _draft_state(rows))
        assert exc.value.code == "workspace_conflict"
        assert exc.value.details["server_revision"] == 2
    finally:
        s1.close()
        s2.close()


def test_saved_state_reloads_identically_via_workspace_get(
        db, session_factory):
    """State + render_model đã save phải đọc lại nguyên vẹn qua
    workspace_get (render_model khớp state hiện tại — contract §4)."""
    from services.case_workspace import CaseWorkspaceService

    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    saved = _svc(db).save_diagram(case.id, 1, state)

    db2 = session_factory()
    try:
        data = CaseWorkspaceService(db2).get(case.id)
    finally:
        db2.close()

    assert data["case"]["revision"] == 2
    assert data["diagram"]["state"] == saved["diagram"]["state"]
    assert data["diagram"]["render_model"] == \
        saved["diagram"]["render_model"]
    assert data["stage"]["owner_row_id"] == rows["owner"]


# ----------------------------------------------------------- evaluate_draft


def _draft_stage(rows, owner_row_id="__owner__"):
    """Stage payload (chưa commit) cho chế độ nháp — person_row wire shape
    với row_id của `rows` map; owner_row_id mặc định = rows['owner']."""
    return {
        "owner_row_id": (rows["owner"]
                         if owner_row_id == "__owner__" else owner_row_id),
        "people": [
            {"row_id": rows["owner"], "entity_id": None,
             "ho_ten": "Nguyễn Văn An", "gioi_tinh": "Nam",
             "ngay_sinh": "1950-01-01", "ngay_chet": "2011-05-15",
             "so_giay_to": None, "ngay_cap": None, "noi_cap": None,
             "dia_chi": "xã A", "place_of_origin": None},
            {"row_id": rows["spouse"], "entity_id": None,
             "ho_ten": "Nguyễn Thị Bình", "gioi_tinh": "Nữ",
             "ngay_sinh": "1955-03-02", "ngay_chet": None,
             "so_giay_to": None, "ngay_cap": None, "noi_cap": None,
             "dia_chi": "xã A", "place_of_origin": None},
            {"row_id": rows["child"], "entity_id": None,
             "ho_ten": "Nguyễn Văn Con", "gioi_tinh": "Nam",
             "ngay_sinh": "1978-07-20", "ngay_chet": "2010-01-01",
             "so_giay_to": None, "ngay_cap": None, "noi_cap": None,
             "dia_chi": "xã A", "place_of_origin": None},
            {"row_id": rows["gc"], "entity_id": None,
             "ho_ten": "Nguyễn Văn Cháu", "gioi_tinh": "Nam",
             "ngay_sinh": "2000-06-06", "ngay_chet": None,
             "so_giay_to": None, "ngay_cap": None, "noi_cap": None,
             "dia_chi": "xã A", "place_of_origin": None},
        ],
        "assets": [
            {"row_id": str(uuid.uuid4()), "entity_id": None,
             "so_serial": "DD123456",
             "so_vao_so": None, "so_thua_dat": None, "so_to_ban_do": None,
             "dia_chi": "Thửa 123", "loai_so": None,
             "hinh_thuc_su_dung": None, "thoi_han": None,
             "nguon_goc": None, "ngay_cap": None, "co_quan_cap": None,
             "land_rows": None},
        ],
    }


def _draft_rows():
    return {k: str(uuid.uuid4())
            for k in ("owner", "spouse", "child", "gc")}


def test_evaluate_draft_evaluates_without_case(db):
    """Chế độ nháp (case_id absent): stage từ payload, không persist,
    evaluated_revision=null (contract §13.4 draft mode)."""
    rows = _draft_rows()

    data = _svc(db).evaluate_draft(
        None, _draft_stage(rows), _draft_state(rows))

    assert data["schema_version"] == SCHEMA_VERSION
    assert data["evaluated_revision"] is None        # không có case -> null
    rm = data["render_model"]
    assert rm["engineVersion"] == 2
    assert rm["status"] == "complete"
    assert rm["allocations"][rows["spouse"]]["finalShare"] == "1/2"
    assert rm["allocations"][rows["gc"]]["finalShare"] == "1/2"
    # không ghi gì vào DB — workspace nháp không tồn tại trên server
    assert db.query(InheritanceCase).count() == 0
    assert db.query(Customer).count() == 0


def test_evaluate_draft_two_party_hint(db):
    """§2.1a/§13.7: payload_case.case_type=two_party → stage không cần
    owner_row_id; state canonical → unsupported render_model."""
    rows = _draft_rows()
    stage = {"people": _draft_stage(rows)["people"],
             "assets": _draft_stage(rows)["assets"]}
    data = _svc(db).evaluate_draft(
        {"case_type": "two_party"}, stage,
        _tp_state(assign={"p1": rows["owner"], "p2": rows["spouse"]}))
    assert data["evaluated_revision"] is None
    assert data["render_model"]["status"] == "unsupported"


def test_evaluate_draft_owner_required(db):
    """Draft inheritance thiếu/dangling owner_row_id →
    workspace_owner_required (§13.6 — pointer là SOT)."""
    rows = _draft_rows()
    for bad in (None, str(uuid.uuid4()), "not-uuid"):
        stage = _draft_stage(rows, owner_row_id=bad)
        with pytest.raises(WorkspaceError) as exc:
            _svc(db).evaluate_draft(None, stage, _draft_state(rows))
        assert exc.value.code == "workspace_owner_required", bad


def test_evaluate_draft_domain_mismatch(db):
    """payload_case.case_type hint sai domain → diagram_domain_mismatch."""
    rows = _draft_rows()
    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_draft(
            {"case_type": "two_party"}, _draft_stage(rows),
            _draft_state(rows))
    assert exc.value.code == "diagram_domain_mismatch"
    assert exc.value.details["expected"] == "two_party"


def test_evaluate_draft_does_not_touch_existing_case(db):
    """Draft evaluate trên session có case sẵn: không đụng revision,
    không đổi stage/diagram đã persist của case."""
    case, _people, rows, _prop = _seed_case(db)
    before_json = case.case_state_json
    before_rev = case.workspace_revision

    draft_rows = _draft_rows()
    _svc(db).evaluate_draft(
        None, _draft_stage(draft_rows), _draft_state(draft_rows))

    db.refresh(case)
    assert case.workspace_revision == before_rev
    assert case.case_state_json == before_json


def test_evaluate_draft_stage_invalid_maps_stage_error(db):
    stage = {
        "owner_row_id": None,   # trỏ xuống dòng hợp lệ sau khi set
        "people": [
            {"row_id": str(uuid.uuid4()), "entity_id": None,
             "ho_ten": "  ",                        # sai: tên rỗng
             "gioi_tinh": "Nam", "ngay_sinh": None, "ngay_chet": None,
             "so_giay_to": None, "ngay_cap": None, "noi_cap": None,
             "dia_chi": None, "place_of_origin": None},
        ],
        "assets": [],
    }
    stage["owner_row_id"] = stage["people"][0]["row_id"]
    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_draft(None, stage, _v3_state([]))
    assert exc.value.code == "stage_validation_error"
    assert exc.value.details["field_errors"]


def test_evaluate_draft_requires_stage_object(db):
    for bad in (None, [], "x"):
        with pytest.raises(WorkspaceError) as exc:
            _svc(db).evaluate_draft(None, bad, _v3_state([]))
        assert exc.value.code == "validation_error", bad


def test_evaluate_draft_outside_stage_and_invalid_wire(db):
    rows = _draft_rows()
    stage = _draft_stage(rows)

    state = _draft_state(rows)
    state["nodes"][0]["personId"] = str(uuid.uuid4())
    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_draft(None, stage, state)
    assert exc.value.code == "diagram_reference_outside_stage"

    bad = _draft_state(rows)
    bad["nodes"][0]["hidden"] = "false"           # string bool
    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_draft(None, stage, bad)
    assert exc.value.code == "diagram_invalid_state"

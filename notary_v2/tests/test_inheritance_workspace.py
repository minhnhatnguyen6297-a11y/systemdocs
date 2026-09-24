"""Tests for services.inheritance_workspace — real backend of
notary.diagram_evaluate / notary.diagram_save (MIN-109,
contract notary.case-drafting.v1 §7).

Uses a temporary SQLite DB per test (tmp_path) — never touches notary.db.
Engine = services.inheritance_engine (ENGINE_VERSION=2); Pool is a derived
projection: committed Stage − personId assigned on Diagram nodes.
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
    """Case với Stage đã commit (4 người) trong case_state_json.

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
        "schemaVersion": 2,
        "stage": [{"id": str(c.id), "row_id": rows[k],
                   "ho_ten": c.ho_ten} for k, c in people.items()],
        "assets": [{"id": str(prop.id), "row_id": str(uuid.uuid4()),
                    "is_primary": True}],
        "diagram": {"state": {"version": 2, "nodes": []},
                    "render_model": None},
    }, ensure_ascii=False)
    db.commit()
    return case, people, rows, prop


def _node(nid, person_id=None, parents=(), spouse=None,
          owner=False, receive=True, hidden=False, deleted=False):
    return {"id": nid, "personId": person_id,
            "parentSlotIds": list(parents), "spouseSlotId": spouse,
            "isLandOwner": owner, "willReceive": receive,
            "hidden": hidden, "deleted": deleted}


def _draft_state(rows):
    """Draft hợp lệ (engine V2): chủ đất đã chết + vợ nhận + con đã chết
    trước → cháu thế vị theo nhánh."""
    return {"version": 2, "nodes": [
        _node("owner", rows["owner"], spouse="spouse",
              owner=True, receive=False),
        _node("spouse", rows["spouse"], spouse="owner"),
        _node("child", rows["child"], parents=("owner", "spouse")),
        _node("gc", rows["gc"], parents=("child",)),
    ]}


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
    kèm details.personId (contract §7.1/§9)."""
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
                {"version": 2, "nodes": "x"},
                "not-a-dict"):
        with pytest.raises(WorkspaceError) as exc:
            _svc(db).evaluate_diagram(case.id, bad)
        assert exc.value.code == "diagram_invalid_state", bad
        assert exc.value.details["errors"]


def test_evaluate_rejects_string_boolean_and_dangling_ref(db):
    case, _people, rows, _prop = _seed_case(db)

    state = _draft_state(rows)
    state["nodes"][0]["willReceive"] = "false"     # chuỗi, không phải bool
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


def test_evaluate_rejects_legacy_js_fields(db):
    """Wire = engine V2: legacy fields (parentSlotId, role, kind, ...) không
    thuộc wire shape → diagram_invalid_state."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    state["nodes"][0]["parentSlotId"] = "father"   # legacy field
    state["nodes"][0]["kind"] = "person"           # legacy field

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
    """case_type khác inheritance → case_type_unsupported (§2.4; DB hiện
    chỉ có InheritanceCase — loai_van_ban là discriminator, guard sẵn)."""
    case, _people, rows, _prop = _seed_case(db, loai_van_ban="khac")

    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_diagram(case.id, _draft_state(rows))
    assert exc.value.code == "case_type_unsupported"
    assert exc.value.details["case_type"] == "khac"


def test_evaluate_missing_case(db):
    with pytest.raises(WorkspaceError) as exc:
        _svc(db).evaluate_diagram(9999, {"version": 2, "nodes": []})
    assert exc.value.code == "case_not_found"


def test_evaluate_missing_land_owner_is_render_model_not_job_error(db):
    """Không có Chủ đất → draft vẫn hợp lệ shape: render_model status
    invalid + errors[missing_land_owner], KHÔNG phải job error."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    for n in state["nodes"]:
        n["isLandOwner"] = False

    data = _svc(db).evaluate_diagram(case.id, state)

    rm = data["render_model"]
    assert rm["status"] == "invalid"
    assert any(e["code"] == "missing_land_owner" for e in rm["errors"])


def test_evaluate_willreceive_false_is_not_refusal(db):
    """Chỉ 2 quyết định Chủ đất/Nhận — không suy 'Từ chối': tắt Nhận chỉ
    làm người đó không nhận phần (finalShare 0), phần đi cho người còn lại."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    for n in state["nodes"]:
        if n["id"] == "spouse":
            n["willReceive"] = False

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
    assert data["diagram"]["render_model"]["status"] == "complete"

    db2 = session_factory()
    try:
        fresh = db2.get(InheritanceCase, case.id)
        assert fresh.workspace_revision == 2
        persisted = json.loads(fresh.case_state_json)
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


def test_save_does_not_change_stage(db):
    """diagram_save không đổi stage.people/stage.assets (contract §7.5)."""
    case, _people, rows, _prop = _seed_case(db)

    _svc(db).save_diagram(case.id, 1, _draft_state(rows))

    persisted = json.loads(db.get(InheritanceCase, case.id).case_state_json)
    assert {r["row_id"] for r in persisted["stage"]} == set(rows.values())
    assert len(persisted["assets"]) == 1


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


def test_save_missing_case(db):
    with pytest.raises(WorkspaceError) as exc:
        _svc(db).save_diagram(9999, 1, {"version": 2, "nodes": []})
    assert exc.value.code == "case_not_found"


def test_save_invalid_state_not_persisted(db):
    """Atomic: state invalid → không persist, revision không đổi (§7.5)."""
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
    state["nodes"][0]["personId"] = str(uuid.uuid4())

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

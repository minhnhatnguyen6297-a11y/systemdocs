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
    CaseAssetRow,
    CasePersonRow,
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
    """Case với Stage đã commit (4 người) bằng dòng case-owned B.

    Gia đình: chủ đất đã chết (2011) + vợ sống + con chết trước chủ đất
    (2010) + cháu nội sống — đủ để kiểm chứng nhánh thế vị (representation).
    Trả (case, people{key:Customer}, rows{key:row_id}, prop).
    """
    prop = Property(so_serial="DD123456", dia_chi="Thửa 123, tờ 45")
    identities = {
        "owner": ("Nguyễn Văn An", "Nam", date(1950, 1, 1),
                  date(2011, 5, 15), "001111111111", "nguyen van an"),
        "spouse": ("Nguyễn Thị Bình", "Nữ", date(1955, 3, 2),
                   None, "002222222222", "nguyen thi binh"),
        "child": ("Nguyễn Văn Con", "Nam", date(1978, 7, 20),
                  date(2010, 1, 1), "003333333333", "nguyen van con"),
        "gc": ("Nguyễn Văn Cháu", "Nam", date(2000, 6, 6),
               None, "004444444444", "nguyen van chau"),
    }
    people = {}
    for key, (name, gender, born, died, number, anchor) in identities.items():
        people[key] = Customer(
            ho_ten=name, gioi_tinh=gender, ngay_sinh=born, ngay_chet=died,
            so_giay_to=number, name_anchor=anchor,
            document_anchor=number)
    db.add(prop)
    db.add_all(people.values())
    db.flush()
    case = InheritanceCase(
        nguoi_chet_id=people["owner"].id, tai_san_id=prop.id,
        ngay_lap_ho_so=date(2026, 9, 1), loai_van_ban=loai_van_ban,
        trang_thai=trang_thai)
    db.add(case)
    db.flush()
    rows = {key: str(uuid.uuid4()) for key in people}
    for index, (key, customer) in enumerate(people.items(), start=1):
        db.add(CasePersonRow(
            row_id=rows[key], case_id=case.id, customer_id=customer.id,
            vitri=index, ho_ten=customer.ho_ten,
            gioi_tinh=customer.gioi_tinh,
            ngay_sinh=(customer.ngay_sinh.isoformat()
                       if customer.ngay_sinh else None),
            ngay_chet=(customer.ngay_chet.isoformat()
                       if customer.ngay_chet else None),
            so_giay_to=customer.so_giay_to,
            dia_chi="xã A"))
    asset_row_id = str(uuid.uuid4())
    db.add(CaseAssetRow(
        row_id=asset_row_id, case_id=case.id, property_id=prop.id,
        vitri=1, so_serial=prop.so_serial, dia_chi=prop.dia_chi,
        land_rows_present=False))
    db.add(InheritanceCaseProperty(
        case_id=case.id, case_asset_row_id=asset_row_id,
        property_id=prop.id, is_primary=True))
    payload = {
        "schemaVersion": 4,
        "case": {},
        "diagram": {"state": {"version": 3, "domain": "inheritance",
                              "nodes": []},
                    "render_model": None},
    }
    if loai_van_ban not in ("chuyen_nhuong", "tang_cho", "cho_thue",
                            "dat_coc"):
        payload["owner_row_id"] = rows["owner"]
    case.case_state_json = json.dumps(payload, ensure_ascii=False)
    db.commit()
    return case, people, rows, prop


def _node(nid, person_id=None, parents=(), spouse=None, own=(),
          receive=(), hidden=False, deleted=False):
    """diagram node v3 (§13.4)."""
    return {"id": nid, "personId": person_id,
            "parentSlotIds": list(parents),
            "spouseSlotIds": [spouse] if spouse else [],
            "spouseSlotId": spouse,
            "spouseSuggestionId": None,
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
    """Positions phải ⊆ {1..5} không trùng (§13.4, S7 23/10/2026)."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    state["nodes"][0]["ownPositions"] = [1, 6]
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


def test_evaluate_position_five_allowed(db):
    """S7: vị trí 5 là hợp lệ trên wire v3 sau khi trần tài sản lên 5."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    state["nodes"][0]["ownPositions"] = [5]
    data = _svc(db).evaluate_diagram(case.id, state)
    assert data["render_model"]["status"] in ("complete", "incomplete")


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


def test_evaluate_allowed_on_done_case(db):
    """Read-only theo DB — evaluate được trên case done (Done sửa được)."""
    case, _people, rows, _prop = _seed_case(db, trang_thai="done")

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
        assert persisted["schemaVersion"] == 4
        assert persisted["diagram"]["state"] == state
        assert persisted["diagram"]["render_model"]["engineVersion"] == 2
        # Stage là rows case-owned — không còn bản sao trong JSON.
        assert "stage" not in persisted and "assets" not in persisted
        # engine_state_json không còn được đọc/ghi trên case B.
        assert fresh.engine_state_json is None
        # participants + nguoi_chet_id sync theo diagram mới, keyed row_id.
        assert fresh.nguoi_chet_id == people["owner"].id
        parts = {p.case_person_row_id: p for p in fresh.participants}
        assert rows["owner"] not in parts
        assert parts[rows["spouse"]].vai_tro == "Vợ/Chồng"
        assert parts[rows["gc"]].vai_tro == "Cháu"
        assert parts[rows["gc"]].parent_case_person_row_id == rows["child"]
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
    """diagram_save không đổi stage.people/stage.assets (rows B)."""
    from services.case_workspace import CaseWorkspaceService

    case, _people, rows, _prop = _seed_case(db)
    before = CaseWorkspaceService(db).get(case.id)["stage"]

    _svc(db).save_diagram(case.id, 1, _draft_state(rows))

    after = CaseWorkspaceService(db).get(case.id)["stage"]
    assert after == before
    assert {r["row_id"] for r in after["people"]} == set(rows.values())
    assert len(after["assets"]) == 1
    assert after["owner_row_id"] == rows["owner"]
    persisted = json.loads(db.get(InheritanceCase, case.id).case_state_json)
    assert "stage" not in persisted and "assets" not in persisted


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


def test_save_done_case_keeps_done_and_bumps_revision(db):
    """Done sửa được: diagram_save giữ status done, revision +1."""
    case, _people, rows, _prop = _seed_case(db, trang_thai="done")

    data = _svc(db).save_diagram(case.id, 1, _draft_state(rows))

    assert data["revision"] == 2
    db.expire_all()
    assert db.get(InheritanceCase, case.id).trang_thai == "done"


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
    from services.case_workspace import CaseWorkspaceService
    view = CaseWorkspaceService(db).get(case.id)
    assert view["case"]["case_type"] == "two_party"
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


def test_save_unassigned_pool_person_keeps_warning_and_incomplete(
        db, session_factory):
    """Save dùng đúng một đường đánh giá với evaluate (§6): người Stage
    chưa gán → render_model đã lưu có warning Pool + status incomplete;
    đọc lại bằng session mới trả nguyên trạng."""
    from services.case_workspace import CaseWorkspaceService

    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    # Bỏ node của 'gc' → người này còn trong Pool.
    state["nodes"] = [n for n in state["nodes"] if n["id"] != "gc"]

    data = _svc(db).save_diagram(case.id, 1, state)

    rm = data["diagram"]["render_model"]
    assert rm["status"] == "incomplete"
    assert any(w["code"] == "diagram.unassigned_pool_person"
               for w in rm["warnings"])
    assert rm["requiredSlots"]

    db2 = session_factory()
    try:
        reloaded = CaseWorkspaceService(db2).get(case.id)
    finally:
        db2.close()
    assert reloaded["diagram"]["render_model"] == rm
    assert reloaded["diagram"]["state"] == data["diagram"]["state"]


def test_save_missing_land_owner_persists_incomplete(db, session_factory):
    """S3 owner 23/10/2026: wire hợp lệ nhưng thiếu Chủ đất (mọi
    ownPositions rỗng) chỉ là THIẾU DỮ KIỆN → lưu được với render_model
    incomplete + lỗi engine giữ nguyên; revision tăng bình thường."""
    case, _people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    for n in state["nodes"]:
        n["ownPositions"] = []

    data = _svc(db).save_diagram(case.id, 1, state)
    assert data["revision"] == 2
    rm = data["diagram"]["render_model"]
    assert rm["status"] == "incomplete"
    assert any(e["code"] == "missing_land_owner" for e in rm["errors"])

    from services.case_workspace import CaseWorkspaceService
    db2 = session_factory()
    try:
        reopened = CaseWorkspaceService(db2).get(case.id)
    finally:
        db2.close()
    assert reopened["diagram"]["render_model"]["status"] == "incomplete"
    assert reopened["diagram"]["render_model"]["errors"] == rm["errors"]


# ----------------------------------------------------------- evaluate_draft


def _draft_stage(rows, owner_row_id="__owner__"):
    """Stage payload (chưa commit) cho chế độ nháp — person_row wire shape
    với row_id của `rows` map; owner_row_id mặc định = rows['owner']."""
    return {
        "owner_row_id": (rows["owner"]
                         if owner_row_id == "__owner__" else owner_row_id),
        # MIN-140: Người phải điền đủ trường có ô nhập; Tài sản cần
        # số tờ/số thửa/địa chỉ + ≥1 land_row — fixture bắt buộc hợp lệ.
        "people": [
            {"row_id": rows["owner"], "entity_id": None,
             "ho_ten": "Nguyễn Văn An", "gioi_tinh": "Nam",
             "ngay_sinh": "1950-01-01", "ngay_chet": "2011-05-15",
             "so_giay_to": "001111111111", "ngay_cap": "2009-01-01",
             "noi_cap": None, "dia_chi": "xã A", "place_of_origin": None},
            {"row_id": rows["spouse"], "entity_id": None,
             "ho_ten": "Nguyễn Thị Bình", "gioi_tinh": "Nữ",
             "ngay_sinh": "1955-03-02", "ngay_chet": None,
             "so_giay_to": "002222222222", "ngay_cap": "2009-01-01",
             "noi_cap": None, "dia_chi": "xã A", "place_of_origin": None},
            {"row_id": rows["child"], "entity_id": None,
             "ho_ten": "Nguyễn Văn Con", "gioi_tinh": "Nam",
             "ngay_sinh": "1978-07-20", "ngay_chet": "2010-01-01",
             "so_giay_to": "003333333333", "ngay_cap": "2009-01-01",
             "noi_cap": None, "dia_chi": "xã A", "place_of_origin": None},
            {"row_id": rows["gc"], "entity_id": None,
             "ho_ten": "Nguyễn Văn Cháu", "gioi_tinh": "Nam",
             "ngay_sinh": "2000-06-06", "ngay_chet": None,
             "so_giay_to": "004444444444", "ngay_cap": "2018-01-01",
             "noi_cap": None, "dia_chi": "xã A", "place_of_origin": None},
        ],
        "assets": [
            {"row_id": str(uuid.uuid4()), "entity_id": None,
             "so_serial": "DD123456",
             "so_vao_so": None, "so_thua_dat": "123", "so_to_ban_do": "45",
             "dia_chi": "Thửa 123", "loai_so": None,
             "hinh_thuc_su_dung": None, "thoi_han": None,
             "nguon_goc": None, "ngay_cap": None, "co_quan_cap": None,
             "land_rows": [{"loai_dat": "ODT", "dien_tich": 60.0}]},
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


def test_evaluate_draft_owner_unassigned_allowed(db):
    """S2 owner 23/10/2026: chưa chọn Chủ đất không chặn "Xem cách tính";
    pointer non-null sai/ngoài Stage vẫn workspace_owner_required."""
    rows = _draft_rows()
    stage = _draft_stage(rows, owner_row_id=None)
    data = _svc(db).evaluate_draft(None, stage, _draft_state(rows))
    assert data["render_model"]["status"] in ("complete", "incomplete")
    for bad in (str(uuid.uuid4()), "not-uuid"):
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


def test_evaluate_draft_field_error_returns_incomplete_outcome(db):
    """S19 owner 23/10/2026: lỗi field tùy chọn không chặn evaluate —
    vẫn chạy theo cấu trúc sơ đồ, trả outcome chưa-tính-được kèm cảnh
    báo ngắn; không còn stage_validation_error."""
    rows = _draft_rows()
    stage = _draft_stage(rows)
    stage["people"][1]["gioi_tinh"] = "Khác"      # lỗi enum trên field phụ

    data = _svc(db).evaluate_draft(None, stage, _draft_state(rows))

    rm = data["render_model"]
    assert rm["status"] == "incomplete"
    assert any(w["code"] == "stage.incomplete_fields"
               for w in rm["warnings"])
    # Cấu trúc sơ đồ vẫn được tính: kết quả engine còn đủ allocation.
    assert rm["allocations"][rows["spouse"]]["finalShare"] == "1/2"


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


def test_save_diagram_keeps_year_only_date_precision(db):
    """Lưu sơ đồ không đụng dòng Người — năm riêng đã lưu giữ nguyên."""
    from services.case_workspace import CaseWorkspaceService

    case, _people, rows, _prop = _seed_case(db)
    owner_row = db.get(CasePersonRow, rows["owner"])
    owner_row.ngay_sinh = "1950"      # năm riêng đã lưu
    db.commit()

    _svc(db).save_diagram(case.id, 1, _draft_state(rows))

    owner = next(r for r in CaseWorkspaceService(db).get(case.id)[
        "stage"]["people"] if r["row_id"] == rows["owner"])
    assert owner["ngay_sinh"] == "1950"


def test_branch_tombstones_coparent_save_reopen_and_reject_preserve(
        db, session_factory):
    from copy import deepcopy
    from services.case_workspace import CaseWorkspaceService

    case, _people, rows, _prop = _seed_case(db)
    spouse = Customer(ho_ten="Spouse S", gioi_tinh="Nữ")
    db.add(spouse)
    db.flush()
    rows["S"] = str(uuid.uuid4())
    db.add(CasePersonRow(
        row_id=rows["S"], case_id=case.id, customer_id=spouse.id,
        vitri=5, ho_ten=spouse.ho_ten, gioi_tinh="Nữ"))
    db.commit()
    before_stage = CaseWorkspaceService(db).get(case.id)["stage"]
    original = _draft_state(rows)
    original["nodes"][2].update(spouseSlotIds=["S"], spouseSlotId="S")
    original["nodes"][3]["parentSlotIds"] = ["child", "S"]
    original["nodes"].extend([
        _node("S", rows["S"], spouse="child"),
        _node("empty", parents=("gc",), hidden=True),
        _node("old", parents=("gc",), deleted=True),
    ])
    first = _svc(db).save_diagram(case.id, case.workspace_revision, original)
    removed = deepcopy(original)
    for node in removed["nodes"]:
        if node["id"] in {"child", "gc", "empty"}:
            node.update(deleted=True, parentSlotIds=[], spouseSlotIds=[],
                        spouseSlotId=None, spouseSuggestionId=None)
        if node["id"] == "S":
            node.update(spouseSlotIds=[], spouseSlotId=None,
                        spouseSuggestionId=None)
        if node["id"] == "old":
            node["parentSlotIds"] = []
    data = _svc(db).save_diagram(case.id, first["revision"], removed)
    assert data["diagram"]["state"] == removed
    assert data["revision"] == first["revision"] + 1
    assert data["diagram"]["render_model"]["status"] != "invalid"
    with session_factory() as fresh:
        reopened = CaseWorkspaceService(fresh).get(case.id)
        assert reopened["diagram"]["state"] == removed
        assert reopened["stage"] == before_stage
        assert reopened["case"]["revision"] == data["revision"]
        bad = deepcopy(removed)
        bad["nodes"][2].update(spouseSlotIds=["child"], spouseSlotId="child")
        for revision, state, code in [
            (data["revision"], bad, "diagram_invalid_state"),
            (first["revision"], removed, "workspace_conflict"),
        ]:
            with pytest.raises(WorkspaceError) as exc:
                _svc(fresh).save_diagram(case.id, revision, state)
            assert exc.value.code == code
            assert CaseWorkspaceService(fresh).get(case.id) == reopened


def test_case_landowner_text_transitions_saved_diagram_and_fresh_reopen(
        db, session_factory):
    import os
    from pathlib import Path
    from services.case_workspace import CaseWorkspaceService
    case, people, rows, _prop = _seed_case(db)
    state = _draft_state(rows)
    spouse = next(node for node in state["nodes"] if node["id"] == "spouse")
    spouse["ownPositions"] = [1]
    _svc(db).save_diagram(case.id, 1, state)
    fresh = session_factory()
    try:
        first = CaseWorkspaceService(fresh).get(case.id)
        assert first["case"]["chudat"] == "Nguyễn Văn An\nNguyễn Thị Bình"
        spouse["ownPositions"] = []
        _svc(fresh).save_diagram(case.id, 2, state)
    finally:
        fresh.close()
    reopened_session = session_factory()
    try:
        reopened = CaseWorkspaceService(reopened_session).get(case.id)
        assert reopened["case"]["chudat"] == "Nguyễn Văn An"
        persisted = json.loads(reopened_session.get(InheritanceCase, case.id).case_state_json)
        assert "chudat" not in persisted.get("case", {})
        evidence = os.environ.get("CASE_FIELDS_EVIDENCE_DIR")
        if evidence:
            target = Path(evidence)
            target.mkdir(parents=True, exist_ok=True)
            (target / "diagram-case-proof.json").write_text(json.dumps({
                "scope": "controlled synthetic DB; real save_diagram and fresh sessions",
                "first_case": first["case"], "reopened_case": reopened["case"],
                "saved_nodes": persisted["diagram"]["state"]["nodes"],
                "stage_snapshot": reopened["stage"],
            }, ensure_ascii=False, indent=2), encoding="utf-8")
    finally:
        reopened_session.close()

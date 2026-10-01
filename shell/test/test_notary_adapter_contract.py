"""Contract test cho adapter handlers MIN-107 → MIN-128
(notary.case-drafting.v2 §13).

Hermetic: `_db_session` → session SQLite temp, `_svc` → module
`services.*` that import tu `notary_v2/` trong repo. Khong cham
`notary_v2/notary.db` that, khong can engine-roots.json.

v2 wire (§13): stage `{owner_row_id?, people[], assets[]}` — owner_row_id
bat buoc voi inheritance, cam voi two_party; diagram_state v3 {version:3,
domain, nodes}; node inheritance {id, personId, parentSlotIds, spouseSlotId,
ownPositions, receivePositions, hidden, deleted}; two_party canonical
30 slot p1..p30. is_primary/isLandOwner/willReceive bi cam tren wire.
"""
import sys
import uuid
from datetime import date
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SHELL = _HERE.parent
_REPO = _SHELL.parent
sys.path.insert(0, str(_SHELL / "sidecar"))
sys.path.insert(0, str(_REPO / "notary_v2"))

import command_registry as reg  # noqa: E402
import notary_adapter  # noqa: E402
from errors import CommandError  # noqa: E402

from database import Base  # noqa: E402
from models import (Customer, InheritanceCase, InheritanceParticipant,  # noqa: E402
                    Property)
import services.case_workspace as case_workspace  # noqa: E402
import services.inheritance_workspace as inheritance_workspace  # noqa: E402
import services.word_batch_export as word_batch_export  # noqa: E402

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

SCHEMA = "notary.case-drafting.v2"
TP_IDS = [f"p{i}" for i in range(1, 31)]


class _Job:
    """Stub Job — check_cancel (co the mang result) + report_progress."""

    def check_cancel(self, result=None):
        return None

    def report_progress(self, done, total, label=""):
        self.progress = {"done": done, "total": total,
                         "current_label": label}


@pytest.fixture()
def adapter_db(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'adapter.db'}",
        connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(notary_adapter, "_db_session", lambda: Session())
    svc_modules = {"case_workspace": case_workspace,
                   "inheritance_workspace": inheritance_workspace,
                   "word_batch_export": word_batch_export}
    monkeypatch.setattr(
        notary_adapter, "_svc",
        lambda name: svc_modules.get(name)
        or pytest.fail(f"unexpected _svc({name!r})"))
    sess = Session()
    yield sess
    sess.close()


def _seed_case(sess, locked=False, loai_van_ban="khai_nhan"):
    deceased = Customer(ho_ten="Nguyen Van Xuat", ngay_chet=date(2020, 1, 1))
    prop = Property(so_serial="AA123456", dia_chi="1 duong test")
    sess.add_all([deceased, prop])
    sess.flush()
    case = InheritanceCase(
        nguoi_chet_id=deceased.id, tai_san_id=prop.id,
        ngay_lap_ho_so=date(2026, 9, 1), loai_van_ban=loai_van_ban,
        trang_thai="locked" if locked else "draft")
    sess.add(case)
    sess.commit()
    return case, deceased, prop


def _uuid4():
    return str(uuid.uuid4())


def _person_row(entity_id=None, **kw):
    row = {
        "row_id": _uuid4(), "entity_id": entity_id,
        "ho_ten": "Nguyen Van Xuat", "gioi_tinh": "Nam",
        "ngay_sinh": "1950-01-01", "ngay_chet": "2020-01-01",
        "so_giay_to": None, "ngay_cap": None, "noi_cap": None,
        "dia_chi": None, "place_of_origin": None,
    }
    row.update(kw)
    return row


def _asset_row(entity_id=None, **kw):
    row = {
        "row_id": _uuid4(), "entity_id": entity_id,
        "so_serial": "AA123456", "so_vao_so": None, "so_thua_dat": None,
        "so_to_ban_do": None, "dia_chi": "1 duong test", "loai_so": None,
        "hinh_thuc_su_dung": None, "thoi_han": None, "nguon_goc": None,
        "ngay_cap": None, "co_quan_cap": None, "land_rows": None,
    }
    row.update(kw)
    return row


def _commit_payload(case_id, base_revision, people, assets,
                    owner_row_id="__omit__"):
    """stage_v2 — owner_row_id chi co tren inheritance (§13.1).
    "__omit__" = khong emit key; None/string khac = emit gia tri."""
    stage = {"people": people, "assets": assets}
    if owner_row_id != "__omit__":
        stage["owner_row_id"] = owner_row_id
    return {"case_id": case_id, "base_revision": base_revision,
            "stage": stage}


def _commit_inheritance(case_id, base_revision, people, assets):
    """Commit payload inheritance: owner_row_id = people[0].row_id."""
    return _commit_payload(case_id, base_revision, people, assets,
                           owner_row_id=people[0]["row_id"])


def _diagram_node(nid, person_id=None, parents=(), spouse=None,
                  own=(), receive=(), hidden=False, deleted=False):
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


# ---------------------------------------------------------------- registry


def test_registry_wires_workspace_commands():
    assert "notary.workspace_get" in reg.COMMANDS
    assert "notary.workspace_commit_stage" in reg.COMMANDS
    assert callable(reg.COMMANDS["notary.workspace_get"])
    assert callable(reg.COMMANDS["notary.workspace_commit_stage"])


# ----------------------------------------------------------- workspace_get


def test_workspace_get_contract_shape(adapter_db):
    case, deceased, prop = _seed_case(adapter_db)
    res = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    assert res["kind"] == "workspace_get"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["backend_mode"] == "real"
    case_info = data["case"]
    assert case_info["id"] == case.id
    assert case_info["case_type"] == "inheritance"
    assert case_info["document_type"] == "khai_nhan"
    assert case_info["status"] == "draft"
    assert case_info["locked"] is False
    assert case_info["revision"] == 1
    assert len(data["stage"]["people"]) == 1
    assert len(data["stage"]["assets"]) == 1
    # v2: stage inheritance emit owner_row_id; asset khong is_primary.
    assert "owner_row_id" in data["stage"]
    assert "is_primary" not in data["stage"]["assets"][0]
    st = data["diagram"]["state"]
    assert st["version"] == 3
    assert st["domain"] == "inheritance"
    assert isinstance(st["nodes"], list)
    for n in st["nodes"]:
        assert "isLandOwner" not in n and "willReceive" not in n
    assert data["capabilities"]["diagram"] is True
    assert data["capabilities"]["word_export"] is True


def test_workspace_get_two_party(adapter_db):
    """two_party: stage khong owner_row_id; diagram canonical 30 slot;
    render_model unsupported sau commit (§13.5); word_export false."""
    case, deceased, prop = _seed_case(
        adapter_db, loai_van_ban="chuyen_nhuong")
    res = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    data = res["data"]
    assert data["case"]["case_type"] == "two_party"
    assert data["case"]["document_type"] == "chuyen_nhuong"
    assert "owner_row_id" not in data["stage"]
    st = data["diagram"]["state"]
    assert st["domain"] == "two_party"
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    # Chua commit → chua co render (giong inheritance).
    assert data["diagram"]["render_model"] is None
    assert data["capabilities"]["word_export"] is False
    assert data["capabilities"]["diagram"] is True
    # Commit xong → render_model unsupported (engine khong tinh).
    notary_adapter.workspace_commit_stage(
        _Job(), _commit_payload(
            case.id, 1, [_person_row(entity_id=deceased.id)],
            [_asset_row(entity_id=prop.id)]))
    res2 = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    rm = res2["data"]["diagram"]["render_model"]
    assert rm["status"] == "unsupported"
    assert rm["allocations"] == {}


def test_workspace_get_missing_case_is_structured(adapter_db):
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_get(_Job(), {"case_id": 9999})
    assert exc.value.code == "case_not_found"
    assert exc.value.retryable is False


def test_workspace_get_requires_case_id(adapter_db):
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_get(_Job(), {})
    assert exc.value.code == "validation_error"


# -------------------------------------------------- workspace_commit_stage


def test_workspace_commit_stage_contract_shape(adapter_db):
    case, deceased, prop = _seed_case(adapter_db)
    res = notary_adapter.workspace_commit_stage(
        _Job(), _commit_inheritance(
            case.id, 1,
            [_person_row(entity_id=deceased.id)],
            [_asset_row(entity_id=prop.id)]))
    assert res["kind"] == "workspace_commit_stage"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["revision"] == 2
    assert data["stage"]["people"][0]["entity_id"] == deceased.id
    assert data["stage"]["assets"][0]["entity_id"] == prop.id
    assert data["stage"]["owner_row_id"] == \
        data["stage"]["people"][0]["row_id"]
    assert data["diagram"]["render_model"] is not None
    adapter_db.refresh(case)
    assert case.workspace_revision == 2


def test_workspace_commit_stage_owner_required(adapter_db):
    """inheritance: owner_row_id null/missing/khong thuoc people ->
    workspace_owner_required (§13.6)."""
    case, deceased, prop = _seed_case(adapter_db)
    for bad_owner in (None, _uuid4()):
        p = _commit_payload(
            case.id, 1, [_person_row(entity_id=deceased.id)],
            [_asset_row(entity_id=prop.id)])
        p["stage"]["owner_row_id"] = bad_owner
        with pytest.raises(CommandError) as exc:
            notary_adapter.workspace_commit_stage(_Job(), p)
        assert exc.value.code == "workspace_owner_required", bad_owner
    # key hoan toan thieu -> cung owner_required
    p = _commit_payload(
        case.id, 1, [_person_row(entity_id=deceased.id)],
        [_asset_row(entity_id=prop.id)])
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), p)
    assert exc.value.code == "workspace_owner_required"


def test_workspace_commit_stage_owner_syncs_node(adapter_db):
    """§13.6: commit sync node 'owner' (neu co, chua deleted) :=
    owner_row_id — SOT la pointer stage; node khong ton tai thi khong
    tu tao."""
    case, deceased, prop = _seed_case(adapter_db)
    people = [_person_row(entity_id=deceased.id),
              _person_row(ho_ten="Tran Thi Binh", ngay_chet=None)]
    # Commit owner=p1 → rev 2.
    p = _commit_payload(case.id, 1, people,
                        [_asset_row(entity_id=prop.id)])
    p["stage"]["owner_row_id"] = people[0]["row_id"]
    notary_adapter.workspace_commit_stage(_Job(), p)
    # Persist diagram co node 'owner' (mirror khop pointer) → rev 3.
    notary_adapter.diagram_save(_Job(), _save_payload(
        case.id, 2, _v3_state([
            _diagram_node("owner", people[0]["row_id"], own=[1])])))
    # Commit doi pointer sang p2 → node owner persisted phai theo pointer.
    p2 = _commit_payload(case.id, 3, people,
                         [_asset_row(entity_id=prop.id)])
    p2["stage"]["owner_row_id"] = people[1]["row_id"]
    res = notary_adapter.workspace_commit_stage(_Job(), p2)
    nodes = res["data"]["diagram"]["state"]["nodes"]
    owner = next((n for n in nodes if n["id"] == "owner"), None)
    assert owner is not None and owner["personId"] == people[1]["row_id"]


def test_workspace_commit_stage_is_primary_rejected(adapter_db):
    """is_primary bi cam tren wire v2 — field la -> validation_error."""
    case, deceased, prop = _seed_case(adapter_db)
    asset = _asset_row(entity_id=prop.id)
    asset["is_primary"] = True
    p = _commit_inheritance(case.id, 1,
                            [_person_row(entity_id=deceased.id)], [asset])
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), p)
    assert exc.value.code == "validation_error"


def test_workspace_commit_stage_asset_limit(adapter_db):
    case, deceased, prop = _seed_case(adapter_db)
    assets = [_asset_row(entity_id=prop.id)] + [
        _asset_row(so_serial=f"AA{i:06d}") for i in range(3)]
    p = _commit_inheritance(
        case.id, 1, [_person_row(entity_id=deceased.id)], assets)
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), p)
    assert exc.value.code == "stage_validation_error"
    fe = exc.value.details["field_errors"]
    assert any(e["code"] == "asset_limit" for e in fe)


def test_workspace_commit_stage_two_party(adapter_db):
    """two_party commit: khong owner_row_id; canonical 30 slot giu
    personId hop le da assign; render_model unsupported; revision tang."""
    case, deceased, prop = _seed_case(
        adapter_db, loai_van_ban="chuyen_nhuong")
    people = [_person_row(entity_id=deceased.id)]
    res = notary_adapter.workspace_commit_stage(
        _Job(), _commit_payload(
            case.id, 1, people, [_asset_row(entity_id=prop.id)]))
    data = res["data"]
    assert data["revision"] == 2
    assert "owner_row_id" not in data["stage"]
    st = data["diagram"]["state"]
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    # Chua assign qua diagram_save → slot trong.
    assert all(n["personId"] is None for n in st["nodes"])
    assert data["diagram"]["render_model"]["status"] == "unsupported"
    # Assign p1 qua save → commit stage giu nguyen assignment.
    notary_adapter.diagram_save(_Job(), _save_payload(
        case.id, 2, _tp_state(assign={"p1": people[0]["row_id"]})))
    res2 = notary_adapter.workspace_commit_stage(
        _Job(), _commit_payload(
            case.id, 3, people, [_asset_row(entity_id=prop.id)]))
    st2 = res2["data"]["diagram"]["state"]
    assert st2["nodes"][0]["personId"] == people[0]["row_id"]


def test_workspace_commit_stage_two_party_owner_row_id_rejected(adapter_db):
    case, deceased, prop = _seed_case(
        adapter_db, loai_van_ban="chuyen_nhuong")
    p = _commit_payload(
        case.id, 1, [_person_row(entity_id=deceased.id)],
        [_asset_row(entity_id=prop.id)])
    p["stage"]["owner_row_id"] = None          # key cam voi two_party
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), p)
    assert exc.value.code == "validation_error"


def test_workspace_commit_stage_two_party_people_limit(adapter_db):
    case, _deceased, _prop = _seed_case(
        adapter_db, loai_van_ban="cho_thue")
    people = [_person_row() for _ in range(31)]
    p = _commit_payload(case.id, 1, people, [])
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), p)
    assert exc.value.code == "stage_validation_error"
    fe = exc.value.details["field_errors"]
    assert any(e["code"] == "people_limit" for e in fe)


def test_workspace_commit_stage_stale_revision_maps_conflict(adapter_db):
    case, deceased, prop = _seed_case(adapter_db)
    payload = _commit_inheritance(
        case.id, 1, [_person_row(entity_id=deceased.id)],
        [_asset_row(entity_id=prop.id)])
    notary_adapter.workspace_commit_stage(_Job(), payload)  # rev 1 → 2
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), payload)  # rev 1 stale
    err = exc.value
    assert err.code == "workspace_conflict"
    assert err.retryable is True
    assert err.next_action == "retry"  # envelope enum, khong phai command name
    assert err.details["server_revision"] == 2


def test_workspace_commit_stage_ahead_revision_maps_conflict(adapter_db):
    case, _deceased, _prop = _seed_case(adapter_db)
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(
            _Job(), _commit_payload(case.id, 99, [], []))
    assert exc.value.code == "workspace_conflict"
    assert exc.value.details["server_revision"] == 1


def test_workspace_commit_stage_locked_maps_error(adapter_db):
    case, deceased, prop = _seed_case(adapter_db, locked=True)
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(
            _Job(), _commit_inheritance(
                case.id, 1, [_person_row(entity_id=deceased.id)],
                [_asset_row(entity_id=prop.id)]))
    err = exc.value
    assert err.code == "workspace_locked"
    assert err.retryable is False


def test_workspace_commit_stage_invalid_row_maps_error(adapter_db):
    case, _deceased, _prop = _seed_case(adapter_db)
    bad = _person_row(ho_ten="   ")
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(
            _Job(), _commit_inheritance(case.id, 1, [bad], []))
    err = exc.value
    assert err.code == "stage_validation_error"
    assert err.retryable is False  # payload sai — retry mu van sai
    assert err.next_action is None
    assert err.details["field_errors"]


def test_workspace_commit_stage_bad_payload_shape(adapter_db):
    case, _d, _p = _seed_case(adapter_db)
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(
            _Job(), {"case_id": case.id, "base_revision": 1})
    assert exc.value.code == "validation_error"
    # Stage shape sai → validation_error truoc stage field validation.
    for bad_stage in ({"people": "x", "assets": []},
                      "khong-dict", 42):
        with pytest.raises(CommandError) as exc2:
            notary_adapter.workspace_commit_stage(
                _Job(), {"case_id": case.id, "base_revision": 1,
                         "stage": bad_stage})
        assert exc2.value.code == "validation_error", bad_stage


# ------------------------------------- payload.case qua commit (MIN-141 đợt 3)


def test_workspace_commit_stage_case_meta_passes_through(adapter_db):
    """payload.case di tu adapter → service → commit cung transaction:
    ghi cot hồ so + snapshot payload.case canonical; get() emit lai."""
    case, deceased, prop = _seed_case(adapter_db)
    uq = Customer(ho_ten="Nguoi Uy Quyen", gioi_tinh="Nu")
    adapter_db.add(uq)
    adapter_db.commit()  # adapter mo session rieng — phai commit
    stage = {"people": [_person_row(entity_id=deceased.id)],
             "assets": [_asset_row(entity_id=prop.id)],
             "owner_row_id": None}
    stage["owner_row_id"] = stage["people"][0]["row_id"]
    res = notary_adapter.workspace_commit_stage(_Job(), {
        "case_id": case.id, "base_revision": 1, "stage": stage,
        # canonical key — adapter khong doi ten, service fold ve snake.
        "case": {"noiniemyet": "UBND xa Test",
                 "nguoinhanuyquyenid": uq.id,
                 "noidungviec": "Dinh chinh nam sinh",
                 "ghichu": "ghi chu"}})
    assert res["data"]["revision"] == 2
    adapter_db.refresh(case)
    assert case.noi_niem_yet == "UBND xa Test"
    assert case.nguoi_nhan_uy_quyen == "Nguoi Uy Quyen"
    assert case.nguoi_nhan_uy_quyen_id == uq.id
    assert case.noi_dung_viec == "Dinh chinh nam sinh"

    got = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    c = got["data"]["case"]
    assert c["noi_niem_yet"] == "UBND xa Test"
    assert c["nguoi_nhan_uy_quyen_id"] == uq.id
    assert c["noi_dung_viec"] == "Dinh chinh nam sinh"


def test_workspace_commit_stage_case_meta_invalid_maps_error(adapter_db):
    """payload.case sai shape/id → CommandError validation_error, khong
    ghi Stage."""
    case, deceased, prop = _seed_case(adapter_db)
    stage = {"people": [_person_row(entity_id=deceased.id)],
             "assets": [_asset_row(entity_id=prop.id)]}
    stage["owner_row_id"] = stage["people"][0]["row_id"]
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), {
            "case_id": case.id, "base_revision": 1, "stage": stage,
            "case": "khong-phai-object"})
    assert exc.value.code == "validation_error"
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), {
            "case_id": case.id, "base_revision": 1, "stage": stage,
            "case": {"nguoinhanuyquyenid": 999999}})
    assert exc.value.code == "validation_error"
    adapter_db.refresh(case)
    assert case.workspace_revision == 1  # rollback tron ven


# ------------------------------------------------- diagram_evaluate / save


def _committed_case(adapter_db, loai_van_ban="khai_nhan"):
    """Seed case + commit Stage qua service that → (case, owner_row_id).

    Revision sau commit = 2. Person duy nhat la nguoi chet → draft hop le
    nhat = owner slot (engine: estate unresolved, status incomplete —
    du de kiem wire shape)."""
    case, deceased, prop = _seed_case(adapter_db, loai_van_ban=loai_van_ban)
    stage = {"people": [_person_row(entity_id=deceased.id)],
             "assets": [_asset_row(entity_id=prop.id)]}
    if loai_van_ban in ("khai_nhan", "thoa_thuan"):
        stage["owner_row_id"] = stage["people"][0]["row_id"]
    res = case_workspace.CaseWorkspaceService(adapter_db).commit_stage(
        case.id, 1, stage)
    row_id = res["stage"]["people"][0]["row_id"]
    return case, row_id


def _eval_payload(case_id, state):
    return {"case_id": case_id, "diagram": {"state": state}}


def _save_payload(case_id, base_revision, state):
    return {"case_id": case_id, "base_revision": base_revision,
            "diagram": {"state": state}}


def test_diagram_evaluate_contract_shape(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[1])])
    res = notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert res["kind"] == "diagram_evaluate"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["evaluated_revision"] == 2
    rm = data["render_model"]
    assert rm["engineVersion"] == 2
    assert rm["status"] in ("incomplete", "complete", "invalid")
    assert rm["allocations"][owner_row]["baseShare"] == "1"


def test_diagram_evaluate_outside_stage_maps_error(adapter_db):
    case, _owner_row = _committed_case(adapter_db)
    outside = str(uuid.uuid4())
    state = _v3_state([_diagram_node("owner", outside, own=[1])])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    err = exc.value
    assert err.code == "diagram_reference_outside_stage"
    assert err.retryable is False
    assert err.details["personId"] == outside


def test_diagram_evaluate_invalid_state_maps_error(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[1]),
        _diagram_node("child", None, parents=("ghost_slot",))])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    err = exc.value
    assert err.code == "diagram_invalid_state"
    assert any(e["code"] == "dangling_parent"
           for e in err.details["errors"])


def test_diagram_evaluate_legacy_node_flags_invalid(adapter_db):
    """isLandOwner/willReceive tren node v3 -> invalid_node (field la)."""
    case, owner_row = _committed_case(adapter_db)
    node = _diagram_node("owner", owner_row, own=[1])
    node["isLandOwner"] = True
    state = _v3_state([node])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert exc.value.code == "diagram_invalid_state"
    codes = {e["code"] for e in exc.value.details["errors"]}
    assert "invalid_node" in codes


def test_diagram_evaluate_position_out_of_range(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[4])])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert exc.value.code == "diagram_invalid_state"
    codes = {e["code"] for e in exc.value.details["errors"]}
    assert "invalid_position" in codes


def test_diagram_evaluate_domain_mismatch(adapter_db):
    """state.domain hop le nhung khac case_type -> diagram_domain_mismatch
    (§13.5) truoc moi wire check khac."""
    case, _owner_row = _committed_case(adapter_db)
    state = _tp_state()
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert exc.value.code == "diagram_domain_mismatch"
    assert exc.value.details["got"] == "two_party"
    assert exc.value.details["expected"] == "inheritance"


def test_diagram_evaluate_two_party_unsupported(adapter_db):
    """two_party committed: unsupported render, khong engine thua ke."""
    case, p1 = _committed_case(adapter_db, loai_van_ban="tang_cho")
    res = notary_adapter.diagram_evaluate(
        _Job(), _eval_payload(case.id, _tp_state(assign={"p1": p1})))
    data = res["data"]
    assert data["evaluated_revision"] == 2
    rm = data["render_model"]
    assert rm["status"] == "unsupported"
    assert rm["allocations"] == {}
    codes = [w["code"] for w in rm["warnings"]]
    assert "diagram.two_party_unsupported" in codes


def test_diagram_evaluate_missing_diagram_is_validation_error(adapter_db):
    case, _ = _committed_case(adapter_db)
    for bad in ({}, {"diagram": None}, {"diagram": {}},
                {"diagram": {"stae": {}}}):
        p = {"case_id": case.id}
        p.update(bad)
        with pytest.raises(CommandError) as exc:
            notary_adapter.diagram_evaluate(_Job(), p)
        assert exc.value.code == "validation_error", bad


def test_diagram_evaluate_allowed_on_locked_case(adapter_db):
    case, _deceased, _prop = _seed_case(adapter_db, locked=True)
    state = _v3_state([])
    res = notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert res["kind"] == "diagram_evaluate"
    assert res["data"]["evaluated_revision"] == 1


def test_diagram_save_persists_and_bumps_revision(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[1])])
    res = notary_adapter.diagram_save(
        _Job(), _save_payload(case.id, 2, state))
    assert res["kind"] == "diagram_save"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["revision"] == 3
    assert data["diagram"]["state"] == state
    assert data["diagram"]["state"]["domain"] == "inheritance"
    assert data["diagram"]["render_model"]["engineVersion"] == 2
    adapter_db.refresh(case)
    assert case.workspace_revision == 3


def test_diagram_save_owner_mismatch(adapter_db):
    """Node 'owner' personId != owner_row_id da commit ->
    diagram_owner_mismatch (§13.4)."""
    case, owner_row = _committed_case(adapter_db)
    # Them nguoi thu 2 vao stage de co row hop le khac owner.
    res = case_workspace.CaseWorkspaceService(adapter_db).commit_stage(
        case.id, 2, {
            "owner_row_id": owner_row,
            "people": [_person_row(entity_id=None, row_id=owner_row,
                                   ho_ten="Nguyen Van Xuat",
                                   ngay_chet="2020-01-01"),
                       _person_row(ho_ten="Tran Thi Binh",
                                   ngay_chet=None)],
            "assets": [_asset_row()]})
    other = res["stage"]["people"][1]["row_id"]
    state = _v3_state([
        _diagram_node("owner", other, spouse="spouse", own=[1]),
        _diagram_node("spouse", None, spouse="owner")])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(_Job(), _save_payload(case.id, 3, state))
    assert exc.value.code == "diagram_owner_mismatch"
    assert exc.value.details["owner_row_id"] == owner_row


def test_diagram_save_prunes_positions(adapter_db):
    """Vi tri > len(assets) bi prune + warning diagram.selection_pruned."""
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[1, 3])])  # chi 1 asset
    res = notary_adapter.diagram_save(
        _Job(), _save_payload(case.id, 2, state))
    dg = res["data"]["diagram"]
    codes = [w["code"] for w in dg.get("warnings") or []]
    assert "diagram.selection_pruned" in codes
    node = next(n for n in dg["state"]["nodes"] if n["id"] == "owner")
    assert node["ownPositions"] == [1]


def test_diagram_save_conflict_maps_retryable(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[1])])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(_Job(), _save_payload(case.id, 1, state))
    err = exc.value
    assert err.code == "workspace_conflict"
    assert err.retryable is True
    assert err.next_action == "retry"
    assert err.details["server_revision"] == 2


def test_diagram_save_locked_maps_error(adapter_db):
    case, _deceased, _prop = _seed_case(adapter_db, locked=True)
    state = _v3_state([])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(_Job(), _save_payload(case.id, 1, state))
    assert exc.value.code == "workspace_locked"


def test_diagram_save_two_party(adapter_db):
    """two_party save: canonical 30 slot + unsupported render + rev bump."""
    case, p1 = _committed_case(adapter_db, loai_van_ban="dat_coc")
    res = notary_adapter.diagram_save(
        _Job(), _save_payload(case.id, 2, _tp_state(assign={"p1": p1})))
    data = res["data"]
    assert data["revision"] == 3
    st = data["diagram"]["state"]
    assert st["domain"] == "two_party"
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    assert st["nodes"][0]["personId"] == p1
    assert data["diagram"]["render_model"]["status"] == "unsupported"


def test_diagram_save_two_party_missing_slot_invalid(adapter_db):
    """29 slot -> diagram_invalid_state — canonical 30 bat buoc (§13.5)."""
    case, _p1 = _committed_case(adapter_db, loai_van_ban="dat_coc")
    state = _tp_state()
    state["nodes"] = state["nodes"][:29]
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(
            _Job(), _save_payload(case.id, 2, state))
    assert exc.value.code == "diagram_invalid_state"


def test_diagram_save_missing_diagram_is_validation_error(adapter_db):
    case, _ = _committed_case(adapter_db)
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(
            _Job(), {"case_id": case.id, "base_revision": 2})
    assert exc.value.code == "validation_error"


# ------------------------------------- word_export_options/batch (MIN-110)


def _seed_word_ready_case(sess, locked=False):
    """Case du dieu kien xuat Word: chu dat da chet + tai san + nguoi nhan
    (participants fallback path — khong can case_state_json)."""
    case, _deceased, _prop = _seed_case(sess, locked=locked)
    heir = Customer(ho_ten="Nguyen Thi Con")
    sess.add(heir)
    sess.flush()
    sess.add(InheritanceParticipant(
        ho_so_id=case.id, customer_id=heir.id,
        vai_tro="Con", co_nhan_tai_san=True, ty_le=100.0))
    sess.commit()
    return case


def _dest(tmp_path):
    return {"path": str(tmp_path), "scope": "machine_local", "is_dir": True}


def test_registry_wires_word_commands():
    assert "notary.word_export_options" in reg.COMMANDS
    assert "notary.word_export_batch" in reg.COMMANDS
    assert callable(reg.COMMANDS["notary.word_export_options"])
    assert callable(reg.COMMANDS["notary.word_export_batch"])


def test_word_export_options_ready_case(adapter_db):
    case = _seed_word_ready_case(adapter_db)
    res = notary_adapter.word_export_options(_Job(), {"case_id": case.id})
    assert res["kind"] == "word_export_options"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    docs = {d["document_key"]: d for d in data["documents"]}
    assert set(docs) == {"khai_nhan_di_san", "thoa_thuan_phan_chia",
                       "niem_yet"}
    assert docs["khai_nhan_di_san"]["ready"] is True
    assert docs["khai_nhan_di_san"]["block_reason"] is None
    assert docs["niem_yet"]["ready"] is False
    assert docs["niem_yet"]["block_reason"] == "word.template_missing"


def test_word_export_options_locked_case_still_readonly(adapter_db):
    # options la read-only — locked case khong bi workspace_locked (§5.3).
    case = _seed_word_ready_case(adapter_db, locked=True)
    res = notary_adapter.word_export_options(_Job(), {"case_id": case.id})
    assert res["data"]["documents"][0]["document_key"]


def test_word_export_options_missing_case(adapter_db):
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_options(_Job(), {"case_id": 9999})
    assert exc.value.code == "case_not_found"


def test_word_export_two_party_rejected(adapter_db):
    """§13.10: word_export_* tren two_party -> case_type_unsupported."""
    case, _d, _p = _seed_case(adapter_db, loai_van_ban="tang_cho")
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_options(_Job(), {"case_id": case.id})
    assert exc.value.code == "case_type_unsupported"
    assert exc.value.details["case_type"] == "two_party"
    with pytest.raises(CommandError) as exc2:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id,
            "document_keys": ["khai_nhan_di_san"],
            "destination": {"path": "x", "scope": "machine_local",
                            "is_dir": True}})
    assert exc2.value.code == "case_type_unsupported"


def test_word_export_batch_writes_docx(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    res = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id,
        "document_keys": ["khai_nhan_di_san", "thoa_thuan_phan_chia"],
        "destination": _dest(tmp_path)})
    assert res["kind"] == "word_export_batch"
    assert res.get("partial") is not True
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["destination"]["is_dir"] is True
    assert data["breakdown"] == {
        "succeeded": ["khai_nhan_di_san", "thoa_thuan_phan_chia"],
        "failed": [], "skipped": []}
    import docx
    for d in data["documents"]:
        assert d["status"] == "saved"
        assert d["error"] is None
        assert ".." not in d["actual_filename"]
        out = Path(d["output_file"]["path"])
        assert out.parent == tmp_path       # ghi thang vao destination
        assert out.is_file()
        docx.Document(str(out))             # DOCX that, mo duoc


def test_word_export_batch_collision_suffix(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    old = tmp_path / f"Van_ban_khai_nhan_di_san_HS-{case.id}.docx"
    old.write_bytes(b"cu")
    res = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id,
        "document_keys": ["khai_nhan_di_san"],
        "destination": _dest(tmp_path)})
    d = res["data"]["documents"][0]
    assert d["actual_filename"] == (
        f"Van_ban_khai_nhan_di_san_HS-{case.id}_2.docx")
    assert old.read_bytes() == b"cu"        # khong bao gio ghi de


def test_word_export_batch_partial(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    res = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id,
        "document_keys": ["khai_nhan_di_san", "niem_yet"],
        "destination": _dest(tmp_path)})
    assert res["partial"] is True           # marker jobstore -> partial
    docs = {d["document_key"]: d for d in res["data"]["documents"]}
    assert docs["khai_nhan_di_san"]["status"] == "saved"
    assert docs["niem_yet"]["status"] == "failed"
    assert docs["niem_yet"]["error"]["code"] == "word.template_missing"
    assert res["data"]["breakdown"]["failed"] == ["niem_yet"]


def test_word_export_batch_all_failed_keeps_result(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id,
            "document_keys": ["niem_yet"],
            "destination": _dest(tmp_path)})
    err = exc.value
    assert err.code == "word_batch_failed"
    assert err.retryable is True
    assert err.next_action == "retry"
    assert err.details["documents"][0]["code"] == "word.template_missing"
    # Result giu lai tren wire — breakdown + per-file errors (§8.4).
    assert err.result["kind"] == "word_export_batch"
    assert err.result["data"]["breakdown"]["failed"] == ["niem_yet"]
    assert list(tmp_path.glob("*.docx")) == []


def test_word_export_batch_validates_before_writing(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    # document_keys rong -> word_no_documents_selected
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id, "document_keys": [],
            "destination": _dest(tmp_path)})
    assert exc.value.code == "word_no_documents_selected"
    # key trung / ngoai catalog
    for keys, code in (
            (["khai_nhan_di_san", "khai_nhan_di_san"],
             "word_duplicate_document_key"),
            (["khong_co"], "word_unknown_document_key"),
            ("khai_nhan_di_san", "validation_error")):
        with pytest.raises(CommandError) as exc:
            notary_adapter.word_export_batch(_Job(), {
                "case_id": case.id, "document_keys": keys,
                "destination": _dest(tmp_path)})
        assert exc.value.code == code, (keys, exc.value.code)
    assert list(tmp_path.glob("*.docx")) == []  # chua file nao duoc tao


def test_word_export_batch_destination_rules(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    # is_dir thieu/false -> validation_error
    for bad in ({"path": str(tmp_path), "scope": "machine_local"},
                {"path": str(tmp_path), "scope": "machine_local",
                 "is_dir": False}):
        with pytest.raises(CommandError) as exc:
            notary_adapter.word_export_batch(_Job(), {
                "case_id": case.id, "document_keys": ["khai_nhan_di_san"],
                "destination": bad})
        assert exc.value.code == "validation_error"
    # folder khong ton tai -> file_not_found
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id, "document_keys": ["khai_nhan_di_san"],
            "destination": _dest(tmp_path / "khong-co")})
    assert exc.value.code == "file_not_found"
    # destination tro toi FILE -> file_not_found
    f = tmp_path / "file.txt"
    f.write_text("x")
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id, "document_keys": ["khai_nhan_di_san"],
            "destination": {"path": str(f), "scope": "machine_local",
                            "is_dir": True}})
    assert exc.value.code == "file_not_found"


def test_word_export_batch_locked_case(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db, locked=True)
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id, "document_keys": ["khai_nhan_di_san"],
            "destination": _dest(tmp_path)})
    assert exc.value.code == "workspace_locked"


# ------------------------------------------------------- workspace_create


_UNSET = object()


def _create_payload(people, assets, state=_UNSET, key=_UNSET,
                    case_meta=_UNSET):
    p = {
        "idempotency_key": key if key is not _UNSET else _uuid4(),
        "case": (case_meta if case_meta is not _UNSET
                 else {"document_type": "khai_nhan"}),
        "stage": {"people": people, "assets": assets},
    }
    if state is not _UNSET:
        p["diagram"] = {"state": state}
    return p


def _create_args(with_diagram=True):
    """(people, assets, state, stage_owner_row_id) v2 — owner = people[0]."""
    owner = _person_row(
        ho_ten="Nguyen Van An", ngay_sinh="1950", ngay_chet="2011-05-15",
        so_giay_to="001234567890")
    spouse = _person_row(
        ho_ten="Tran Thi Binh", gioi_tinh="Nữ", ngay_sinh="1955-03-02",
        ngay_chet=None, so_giay_to="009876543210")
    state = _v3_state([
        _diagram_node("owner", owner["row_id"], spouse="spouse", own=[1]),
        _diagram_node("spouse", spouse["row_id"], spouse="owner",
                      receive=[1]),
    ]) if with_diagram else _UNSET
    return [owner, spouse], [_asset_row()], state


def _inheritance_create(people, assets, state=_UNSET, **kw):
    """_create_payload + stage.owner_row_id = people[0].row_id."""
    p = _create_payload(people, assets, state, **kw)
    p["stage"]["owner_row_id"] = people[0]["row_id"]
    return p


def test_registry_wires_workspace_create():
    assert "notary.workspace_create" in reg.COMMANDS
    assert callable(reg.COMMANDS["notary.workspace_create"])


def test_workspace_create_contract_shape(adapter_db):
    people, assets, state = _create_args()
    res = notary_adapter.workspace_create(
        _Job(), _inheritance_create(people, assets, state, case_meta={
            "document_type": "khai_nhan", "ngay_lap_ho_so": "2026-09-26",
            "noi_niem_yet": "xa Yen So", "ghi_chu": "Nhap"}))
    assert res["kind"] == "workspace_create"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["backend_mode"] == "real"
    assert data["created"] is True
    c = data["case"]
    assert c["case_type"] == "inheritance"
    assert c["status"] == "draft" and c["locked"] is False
    assert c["revision"] == 1
    assert c["ngay_lap_ho_so"] == "2026-09-26"
    assert c["noi_niem_yet"] == "xa Yen So"
    assert c["ghi_chu"] == "Nhap"
    assert all(p["entity_id"] for p in data["stage"]["people"])
    assert data["stage"]["owner_row_id"] == people[0]["row_id"]
    st = data["diagram"]["state"]
    assert st["version"] == 3 and st["domain"] == "inheritance"
    assert data["diagram"]["render_model"]["engineVersion"] == 2
    assert data["capabilities"]["word_export"] is True
    for n in st["nodes"]:
        assert "isLandOwner" not in n and "willReceive" not in n
    # doc lai bang workspace_get — case ton tai that
    got = notary_adapter.workspace_get(_Job(), {"case_id": c["id"]})
    assert got["data"]["case"]["revision"] == 1


def test_workspace_create_without_diagram_seeds_owner(adapter_db):
    """diagram absent -> server seed node 'owner' = owner_row_id +
    ownPositions moi vi tri (§13.6); render_model null."""
    people, assets, _ = _create_args(with_diagram=False)
    res = notary_adapter.workspace_create(
        _Job(), _inheritance_create(people, assets))
    data = res["data"]
    st = data["diagram"]["state"]
    owner = next((n for n in st["nodes"] if n["id"] == "owner"), None)
    assert owner is not None
    assert owner["personId"] == people[0]["row_id"]
    assert owner["ownPositions"] == [1]
    assert data["diagram"]["render_model"] is None


def test_workspace_create_two_party(adapter_db):
    """two_party create: case_type + doc enum moi; stage khong
    owner_row_id; diagram absent → seed canonical 30 slot."""
    people = [_person_row(ho_ten="Ben A", ngay_chet=None),
              _person_row(ho_ten="Ben B", gioi_tinh="Nữ",
                          ngay_chet=None)]
    p = _create_payload(people, [_asset_row()], case_meta={
        "case_type": "two_party", "document_type": "chuyen_nhuong"})
    res = notary_adapter.workspace_create(_Job(), p)
    data = res["data"]
    assert data["case"]["case_type"] == "two_party"
    assert data["case"]["document_type"] == "chuyen_nhuong"
    assert "owner_row_id" not in data["stage"]
    st = data["diagram"]["state"]
    assert st["domain"] == "two_party"
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    assert data["capabilities"]["word_export"] is False


def test_workspace_create_idempotent_replay(adapter_db):
    people, assets, state = _create_args()
    key = _uuid4()
    first = notary_adapter.workspace_create(
        _Job(), _inheritance_create(people, assets, state, key=key))
    second = notary_adapter.workspace_create(
        _Job(), _inheritance_create(people, assets, state, key=key))
    assert first["data"]["created"] is True
    assert second["data"]["created"] is False
    assert second["data"]["case"]["id"] == first["data"]["case"]["id"]
    assert adapter_db.query(InheritanceCase).count() == 1
    # key khac = case moi
    third = notary_adapter.workspace_create(
        _Job(), _inheritance_create(people, assets, state, key=_uuid4()))
    assert third["data"]["created"] is True
    assert third["data"]["case"]["id"] != first["data"]["case"]["id"]


def test_workspace_create_bad_key_and_meta(adapter_db):
    people, assets, state = _create_args()
    for bad_key in (None, "nope", 42, str(uuid.uuid1())):
        with pytest.raises(CommandError) as exc:
            notary_adapter.workspace_create(
                _Job(), _inheritance_create(
                    people, assets, state, key=bad_key))
        assert exc.value.code == "validation_error", bad_key
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(
            _Job(), _inheritance_create(
                people, assets, state, case_meta={"document_type": "khac"}))
    assert exc.value.code == "validation_error"
    assert adapter_db.query(InheritanceCase).count() == 0


def test_workspace_create_owner_pointer_required(adapter_db):
    """inheritance: owner_row_id null/missing/dangling ->
    workspace_owner_required (§13.6)."""
    people, assets, state = _create_args()
    for bad in (None, _uuid4(), "khong-uuid"):
        p = _create_payload(people, assets, state)
        p["stage"]["owner_row_id"] = bad
        with pytest.raises(CommandError) as exc:
            notary_adapter.workspace_create(_Job(), p)
        assert exc.value.code == "workspace_owner_required", bad
    p = _create_payload(people, assets, state)   # key hoan toan thieu
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(_Job(), p)
    assert exc.value.code == "workspace_owner_required"
    assert adapter_db.query(InheritanceCase).count() == 0


def test_workspace_create_owner_mismatch(adapter_db):
    """Node owner personId != stage.owner_row_id ->
    diagram_owner_mismatch — server KHONG tu sua (§13.6)."""
    people, assets, _ = _create_args()
    state = _v3_state([
        _diagram_node("owner", people[1]["row_id"], spouse="spouse",
                      own=[1]),
        _diagram_node("spouse", None, spouse="owner", receive=[1]),
    ])
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(
            _Job(), _inheritance_create(people, assets, state))
    assert exc.value.code == "diagram_owner_mismatch"
    assert exc.value.details["owner_row_id"] == people[0]["row_id"]
    assert adapter_db.query(InheritanceCase).count() == 0


def test_workspace_create_domain_mismatch(adapter_db):
    """state.domain hop le nhung khac case.case_type ->
    diagram_domain_mismatch (§13.5)."""
    people, assets, _ = _create_args()
    p = _inheritance_create(people, assets, _tp_state())
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(_Job(), p)
    assert exc.value.code == "diagram_domain_mismatch"
    assert exc.value.details["expected"] == "inheritance"


def test_workspace_create_is_primary_rejected(adapter_db):
    people, assets, state = _create_args()
    assets[0]["is_primary"] = True              # field la tren v2
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(
            _Job(), _inheritance_create(people, assets, state))
    assert exc.value.code == "validation_error"


def test_workspace_create_entity_id_and_stage_errors(adapter_db):
    people, assets, state = _create_args()
    # entity_id non-null tren nhap -> stage_validation_error
    bad_people = [dict(people[0], entity_id=5), people[1]]
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(
            _Job(), _inheritance_create(bad_people, assets, state))
    assert exc.value.code == "stage_validation_error"
    # stage rong assets -> required field error
    p = _inheritance_create(people, [], state)
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(_Job(), p)
    assert exc.value.code == "stage_validation_error"
    assert adapter_db.query(InheritanceCase).count() == 0


def test_workspace_create_two_party_owner_row_id_rejected(adapter_db):
    people = [_person_row(ho_ten="Ben A", ngay_chet=None)]
    p = _create_payload(people, [_asset_row()], case_meta={
        "case_type": "two_party", "document_type": "tang_cho"})
    p["stage"]["owner_row_id"] = None           # key cam voi two_party
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(_Job(), p)
    assert exc.value.code == "validation_error"


def test_workspace_create_missing_stage(adapter_db):
    people, assets, state = _create_args()
    payload = _inheritance_create(people, assets, state)
    del payload["stage"]
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(_Job(), payload)
    assert exc.value.code == "validation_error"


def test_workspace_create_diagram_absent_allowed(adapter_db):
    """diagram absent -> OK (§13.6 — server seed); stage thieu -> loi."""
    people, assets, _state = _create_args()
    p = _inheritance_create(people, assets)      # khong kem diagram
    res = notary_adapter.workspace_create(_Job(), p)
    assert res["data"]["created"] is True


# --------------------------------------------- diagram_evaluate draft mode


def _draft_stage():
    """stage draft inheritance — owner_row_id = people[0].row_id."""
    people = [
        _person_row(ho_ten="Nguyen Van An", ngay_sinh="1950",
                    ngay_chet="2011-05-15"),
        _person_row(ho_ten="Tran Thi Binh", gioi_tinh="Nữ",
                    ngay_chet=None),
    ]
    return {"owner_row_id": people[0]["row_id"],
            "people": people, "assets": []}


def test_diagram_evaluate_draft_mode(adapter_db):
    stage = _draft_stage()
    rows = [p["row_id"] for p in stage["people"]]
    state = _v3_state([
        _diagram_node("owner", rows[0], spouse="spouse", own=[1]),
        _diagram_node("spouse", rows[1], spouse="owner", receive=[1])])
    res = notary_adapter.diagram_evaluate(_Job(), {
        "stage": stage, "diagram": {"state": state}})
    assert res["kind"] == "diagram_evaluate"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["evaluated_revision"] is None
    assert data["render_model"]["engineVersion"] == 2
    # read-only tuyet doi — khong ghi DB
    assert adapter_db.query(InheritanceCase).count() == 0


def test_diagram_evaluate_draft_case_hint_two_party(adapter_db):
    """§2.1a/§13.7: case.case_type hint -> two_party draft tra
    unsupported render_model (khong can owner_row_id)."""
    stage = {"people": [_person_row(ngay_chet=None),
                        _person_row(ho_ten="Ben B", ngay_chet=None)],
             "assets": [_asset_row()]}
    res = notary_adapter.diagram_evaluate(_Job(), {
        "case": {"case_type": "two_party"},
        "stage": stage,
        "diagram": {"state": _tp_state(
            assign={"p1": stage["people"][0]["row_id"]})}})
    data = res["data"]
    assert data["evaluated_revision"] is None
    assert data["render_model"]["status"] == "unsupported"


def test_diagram_evaluate_draft_domain_mismatch(adapter_db):
    stage = _draft_stage()
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "stage": stage, "diagram": {"state": _tp_state()}})
    assert exc.value.code == "diagram_domain_mismatch"
    assert exc.value.details["expected"] == "inheritance"


def test_diagram_evaluate_draft_owner_required(adapter_db):
    """Draft inheritance thieu owner_row_id -> workspace_owner_required."""
    stage = {"people": [_person_row()], "assets": [_asset_row()]}
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "stage": stage, "diagram": {"state": _v3_state([])}})
    assert exc.value.code == "workspace_owner_required"


def test_diagram_evaluate_null_case_id_is_validation_error(adapter_db):
    stage = _draft_stage()
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "case_id": None, "stage": stage,
            "diagram": {"state": _v3_state([])}})
    assert exc.value.code == "validation_error"


def test_diagram_evaluate_draft_requires_stage(adapter_db):
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "diagram": {"state": _v3_state([])}})
    assert exc.value.code == "validation_error"


def test_diagram_evaluate_draft_stage_errors(adapter_db):
    stage = _draft_stage()
    stage["people"][0]["ho_ten"] = "   "
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "stage": stage,
            "diagram": {"state": _v3_state([])}})
    assert exc.value.code == "stage_validation_error"
    assert exc.value.details["field_errors"]


def test_diagram_evaluate_draft_outside_stage(adapter_db):
    stage = _draft_stage()
    state = _v3_state([
        _diagram_node("owner", stage["people"][0]["row_id"], own=[1]),
        _diagram_node("child", str(uuid.uuid4()), parents=("owner",),
                      receive=[1])])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "stage": stage, "diagram": {"state": state}})
    assert exc.value.code == "diagram_reference_outside_stage"

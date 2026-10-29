"""Test `notary.workspace_save_case` — Lưu hồ sơ nguyên tử (issue 13).

Design: `_bmad-output/tmp/issue13-b-phase2-design-20261022.md` Phần 5 + 8
(A1–A3/B1/B3/B4). Dữ kiện Enter lấy từ fixture tổng hợp
`fixtures/issue13_storage_b.json` (F1/F3 prototypes); ID integer DB không
hardcode — assert theo alias/quan hệ.
"""
import json
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
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
from services.case_workspace import CaseWorkspaceService, WorkspaceError

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "issue13_storage_b.json"
INHERITANCE_META = {"case_type": "inheritance",
                    "document_type": "khai_nhan",
                    "ngay_lap_ho_so": "2026-10-22"}


@pytest.fixture(scope="module")
def dataset():
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'save_case.db'}")
    database.enable_sqlite_foreign_keys(engine)
    database.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


# ------------------------------------------------------------------ helpers


def _proto(dataset, section, alias, **override):
    row = dict(dataset[section][alias])
    row.pop("alias", None)
    row.update(override)
    return row


def _f1_stage(dataset):
    return {
        "owner_row_id": "00000000-0000-4000-8000-000000000101",
        "people": [_proto(dataset, "people_prototypes", alias)
                   for alias in ("P101", "P102", "P103")],
        "assets": [_proto(dataset, "asset_prototypes", "T101")],
    }


def _node(nid, person_id=None, parents=(), spouses=(),
          own=(), receive=()):
    return {"id": nid, "personId": person_id,
            "parentSlotIds": list(parents), "spouseSlotIds": list(spouses),
            "spouseSuggestionId": None,
            "ownPositions": list(own), "receivePositions": list(receive),
            "hidden": False, "deleted": False}


def _f1_state():
    return {"version": 3, "domain": "inheritance", "nodes": [
        _node("owner", "00000000-0000-4000-8000-000000000101",
              parents=("father", "mother"), spouses=("spouse",), own=[1]),
        _node("spouse", "00000000-0000-4000-8000-000000000102",
              parents=("spouse_father", "spouse_mother"),
              spouses=("owner",), own=[1], receive=[1]),
        _node("child_1", "00000000-0000-4000-8000-000000000103",
              parents=("owner", "spouse"), receive=[1]),
        _node("father"), _node("mother"),
        _node("spouse_father"), _node("spouse_mother"),
    ]}


def _meta(**override):
    meta = dict(INHERITANCE_META)
    meta.update(override)
    return meta


def _key():
    return str(uuid.uuid4())


def _create_draft(db, dataset, *, stage=None, meta=None, key=None):
    return CaseWorkspaceService(db).create(
        key or _key(), meta or _meta(), stage or _f1_stage(dataset), None)


def _counts(db):
    return (db.query(Customer).count(), db.query(Property).count(),
            db.query(CasePersonRow).count(), db.query(CaseAssetRow).count())


def _snapshot(db, case_id):
    case = db.get(InheritanceCase, case_id)
    db.refresh(case)
    return {
        "revision": case.workspace_revision,
        "status": case.trang_thai,
        "meta": (case.ghi_chu, case.noi_niem_yet, case.ngay_lap_ho_so),
        "people": [(r.row_id, r.ho_ten, r.vitri) for r in case.person_rows],
        "assets": [(r.row_id, r.so_serial, r.vitri) for r in case.asset_rows],
        "json": case.case_state_json,
    }


# ---------------------------------------------------------------- A1/A2


def test_save_case_moves_existing_draft_to_done_revision_plus_one(
        db, dataset):
    created = _create_draft(db, dataset)
    case_id = created["case"]["id"]
    assert created["case"]["status"] == "draft"
    assert created["case"]["revision"] == 1

    # Renderer gửi snapshot Stage hiện tại (đã có trường suy ra từ create).
    result = CaseWorkspaceService(db).save_case(
        case_id=case_id, base_revision=1, idempotency_key=None,
        case_meta=_meta(), stage=created["stage"], state=_f1_state())

    assert result["created"] is False
    assert result["case"]["status"] == "done"
    assert result["case"]["revision"] == 2
    assert result["diagram"]["render_model"] is not None
    assert [p["ho_ten"] for p in result["stage"]["people"]] == [
        "Nguyễn Đăng An", "Trần Thị Bình", "Nguyễn Văn Con"]
    asset = result["stage"]["assets"][0]
    assert asset["entity_id"] is not None
    assert len(asset["land_rows"]) == 3
    assert asset["land_rows"][1] == {
        "loai_dat": None, "dien_tich": None, "thoi_han": None}
    people = {p["ho_ten"]: p for p in result["stage"]["people"]}
    assert people["Nguyễn Đăng An"]["ngay_sinh"] == "1950"
    assert people["Nguyễn Đăng An"]["loai_dia_chi"] == "Nơi chết"
    assert people["Trần Thị Bình"]["loai_giay_to"] == "Căn cước"
    assert people["Trần Thị Bình"]["noi_cap"] == "Bộ Công an"
    assert people["Nguyễn Văn Con"]["loai_giay_to"] is None
    assert result["case"]["chudat"] == "Nguyễn Đăng An\nTrần Thị Bình"

    case = db.get(InheritanceCase, case_id)
    db.refresh(case)
    assert case.trang_thai == "done"
    assert case.workspace_revision == 2
    assert [(r.vitri, r.ho_ten) for r in case.person_rows] == [
        (1, "Nguyễn Đăng An"), (2, "Trần Thị Bình"),
        (3, "Nguyễn Văn Con")]

    reopened = CaseWorkspaceService(db).get(case_id)
    assert reopened["case"]["status"] == "done"
    assert reopened["case"]["revision"] == 2
    assert len(reopened["stage"]["people"]) == 3


def test_save_case_creates_new_case_done_revision_one(db, dataset):
    result = CaseWorkspaceService(db).save_case(
        case_id=None, base_revision=None, idempotency_key=_key(),
        case_meta=_meta(), stage=_f1_stage(dataset), state=_f1_state())

    assert result["created"] is True
    assert result["case"]["status"] == "done"
    assert result["case"]["revision"] == 1
    assert result["case"]["id"] >= 1
    case = db.get(InheritanceCase, result["case"]["id"])
    assert case.trang_thai == "done"
    assert case.workspace_revision == 1
    assert case.workspace_creation_hash
    assert case.workspace_idempotency_key
    assert len(case.person_rows) == 3
    assert len(case.asset_rows) == 1
    assert len(case.asset_rows[0].land_rows) == 3

    links = db.query(InheritanceCaseProperty).filter(
        InheritanceCaseProperty.case_id == case.id).all()
    assert len(links) == 1
    assert links[0].case_asset_row_id == case.asset_rows[0].row_id
    assert links[0].property_id == case.asset_rows[0].property_id


def test_save_case_five_assets_ok_six_rejected(db):
    """S7: trần 5 tài sản áp cả nhánh tạo mới của Lưu hồ sơ."""
    def stage(count):
        return {"owner_row_id": None, "people": [_minimal_person()],
                "assets": [_minimal_asset(so_serial=f"SR{i}")
                           for i in range(count)]}

    saved = CaseWorkspaceService(db).save_case(
        case_id=None, base_revision=None, idempotency_key=_key(),
        case_meta=_meta(), stage=stage(5), state=EMPTY_STATE)
    assert len(saved["stage"]["assets"]) == 5

    with pytest.raises(WorkspaceError) as exc:
        CaseWorkspaceService(db).save_case(
            case_id=None, base_revision=None, idempotency_key=_key(),
            case_meta=_meta(), stage=stage(6), state=EMPTY_STATE)
    assert any(e["code"] == "asset_limit"
               for e in exc.value.details["field_errors"])
    assert db.query(InheritanceCase).count() == 1


def test_save_case_done_stays_done_when_commit_and_resave(db, dataset):
    create = _create_draft(db, dataset)
    case_id = create["case"]["id"]
    svc = CaseWorkspaceService(db)
    svc.save_case(case_id=case_id, base_revision=1, idempotency_key=None,
                  case_meta=_meta(), stage=_f1_stage(dataset),
                  state=_f1_state())

    stage = _f1_stage(dataset)
    stage["people"][1] = dict(stage["people"][1],
                              dia_chi="Khu Giả Lập B2")
    updated = svc.commit_stage(case_id, 2, stage, None)
    assert updated["revision"] == 3
    case = db.get(InheritanceCase, case_id)
    db.refresh(case)
    assert case.trang_thai == "done"
    assert case.person_rows[1].dia_chi == "Khu Giả Lập B2"

    resaved = svc.save_case(case_id=case_id, base_revision=3,
                            idempotency_key=None, case_meta=_meta(),
                            stage=stage, state=_f1_state())
    assert resaved["case"]["status"] == "done"
    assert resaved["case"]["revision"] == 4
    db.refresh(case)
    assert case.trang_thai == "done"
    assert case.workspace_revision == 4


# ---------------------------------------------------------------- A3


def test_save_case_keeps_valid_unsupported_diagram_done(db, dataset):
    create = _create_draft(db, dataset)
    case_id = create["case"]["id"]
    state = {"version": 3, "domain": "inheritance",
             "nodes": [_node(
                 "owner", "00000000-0000-4000-8000-000000000101",
                 own=[1])]}
    result = CaseWorkspaceService(db).save_case(
        case_id=case_id, base_revision=1, idempotency_key=None,
        case_meta=_meta(), stage=_f1_stage(dataset), state=state)
    assert result["case"]["status"] == "done"
    assert result["diagram"]["render_model"]["status"] == "unsupported"
    codes = {w["code"]
             for w in result["diagram"]["render_model"]["warnings"]}
    assert "diagram.unassigned_pool_person" in codes

    reopened = CaseWorkspaceService(db).get(case_id)
    assert reopened["case"]["status"] == "done"
    assert reopened["diagram"]["render_model"]["status"] == "unsupported"
    assert {w["code"]
            for w in reopened["diagram"]["render_model"]["warnings"]} >= codes


@pytest.mark.parametrize(("state_factory", "expected_error"), [
    (lambda: {"version": 2, "domain": "inheritance", "nodes": []},
     "invalid_version"),
    (lambda: {"version": 3, "domain": "inheritance", "nodes": "bad"},
     "invalid_input"),
    (lambda: {"version": 3, "domain": "inheritance", "nodes": [
        dict(_node("owner"), hidden="false")]}, "invalid_input"),
])
def test_save_case_invalid_diagram_rolls_back_everything(
        db, dataset, state_factory, expected_error):
    create = _create_draft(db, dataset)
    case_id = create["case"]["id"]
    before = _snapshot(db, case_id)
    counts = _counts(db)
    stage = _f1_stage(dataset)
    stage["people"].append(_proto(dataset, "people_prototypes", "P103",
                                  row_id=str(uuid.uuid4()),
                                  ho_ten="Người Mới Chưa Tồn Tại",
                                  so_giay_to="000000000999"))
    stage["people"][1] = dict(stage["people"][1], dia_chi="Sửa Nhưng Rollback")
    meta = _meta(ghi_chu="không được lưu")
    with pytest.raises(WorkspaceError) as exc:
        CaseWorkspaceService(db).save_case(
            case_id=case_id, base_revision=1, idempotency_key=None,
            case_meta=meta, stage=stage, state=state_factory())
    assert exc.value.code == "diagram_invalid_state"
    assert {error["code"] for error in exc.value.details["errors"]} == {
        expected_error}
    db.expire_all()
    assert _snapshot(db, case_id) == before
    assert _counts(db) == counts


def test_save_case_self_spouse_persists_invalid_with_stage_and_revision(db, dataset):
    create = _create_draft(db, dataset)
    case_id = create["case"]["id"]
    stage = _f1_stage(dataset)
    stage["people"][1]["dia_chi"] = "Địa chỉ đã sửa"
    state = _f1_state()
    state["nodes"][0]["spouseSlotIds"] = ["owner"]
    saved = CaseWorkspaceService(db).save_case(
        case_id=case_id, base_revision=1, idempotency_key=None,
        case_meta=_meta(ghi_chu="Lưu cả sơ đồ chưa hợp lệ"),
        stage=stage, state=state)
    assert saved["case"]["revision"] == 2
    assert saved["diagram"]["state"] == state
    rm = saved["diagram"]["render_model"]
    assert rm["status"] == "invalid"
    assert any(e["code"] == "self_spouse" for e in rm["errors"])
    reopened = CaseWorkspaceService(db).get(case_id)
    assert reopened["case"]["revision"] == 2
    assert reopened["diagram"]["state"] == state
    assert reopened["diagram"]["render_model"] == rm
    assert reopened["stage"]["people"][1]["dia_chi"] == "Địa chỉ đã sửa"
    assert reopened["case"]["ghi_chu"] == "Lưu cả sơ đồ chưa hợp lệ"


# ---------------------------------------------------------------- B1


def test_save_case_missing_land_owner_saves_incomplete(db, dataset):
    """S3 owner 23/10/2026: thiếu Chủ đất = thiếu dữ kiện, không chặn Lưu.
    State được ghi, render_model incomplete và giữ lỗi missing_land_owner."""
    create = _create_draft(db, dataset)
    case_id = create["case"]["id"]
    state = {"version": 3, "domain": "inheritance",
             "nodes": [_node(
                 "owner", "00000000-0000-4000-8000-000000000101",
                 own=[])]}

    result = CaseWorkspaceService(db).save_case(
        case_id=case_id, base_revision=1, idempotency_key=None,
        case_meta=_meta(), stage=_f1_stage(dataset), state=state)

    assert result["case"]["status"] == "done"
    assert result["case"]["revision"] == 2
    rm = result["diagram"]["render_model"]
    assert rm["status"] == "incomplete"
    assert any(e["code"] == "missing_land_owner" for e in rm["errors"])
    reopened = CaseWorkspaceService(db).get(case_id)
    assert reopened["diagram"]["state"] == result["diagram"]["state"]
    assert reopened["diagram"]["render_model"]["status"] == "incomplete"


def test_save_case_writes_new_rows_meta_and_diagram_in_one_revision(
        db, dataset):
    stage = {
        "owner_row_id": "00000000-0000-4000-8000-000000000101",
        "people": [_proto(dataset, "people_prototypes", "P101")],
        "assets": [_proto(dataset, "asset_prototypes", "T101")],
    }
    create = _create_draft(db, dataset, stage=stage,
                           meta=_meta(ghi_chu="bản cũ"))
    case_id = create["case"]["id"]
    assert create["case"]["revision"] == 1

    full = _f1_stage(dataset)
    result = CaseWorkspaceService(db).save_case(
        case_id=case_id, base_revision=1, idempotency_key=None,
        case_meta=_meta(ghi_chu=None), stage=full, state=_f1_state())

    assert result["case"]["revision"] == 2
    assert result["case"]["ghi_chu"] is None
    assert len(result["stage"]["people"]) == 3
    other = next(p for p in result["stage"]["people"]
                 if p["row_id"] == "00000000-0000-4000-8000-000000000102")
    assert other["entity_id"] is not None

    reopened = CaseWorkspaceService(db).get(case_id)
    assert reopened["case"]["revision"] == 2
    assert reopened["case"]["ghi_chu"] is None
    assert [p["row_id"] for p in reopened["stage"]["people"]] == [
        "00000000-0000-4000-8000-000000000101",
        "00000000-0000-4000-8000-000000000102",
        "00000000-0000-4000-8000-000000000103"]
    assigned = {n.get("personId") for n in reopened["diagram"]["state"]["nodes"]}
    assert "00000000-0000-4000-8000-000000000102" in assigned
    assert reopened["diagram"]["render_model"] is not None


# ---------------------------------------------------------------- B3


def test_save_case_unknown_diagram_uuid_rolls_back_new_identity(
        db, dataset):
    create = _create_draft(db, dataset, stage={
        "owner_row_id": "00000000-0000-4000-8000-000000000101",
        "people": [_proto(dataset, "people_prototypes", "P101")],
        "assets": [_proto(dataset, "asset_prototypes", "T101")],
    })
    case_id = create["case"]["id"]
    before = _snapshot(db, case_id)
    counts = _counts(db)
    stage = _f1_stage(dataset)
    stage["people"][1] = dict(stage["people"][1],
                              so_giay_to="000000000777")
    state = _f1_state()
    state["nodes"].append(_node("ghost", str(uuid.uuid4())))
    with pytest.raises(WorkspaceError) as exc:
        CaseWorkspaceService(db).save_case(
            case_id=case_id, base_revision=1, idempotency_key=None,
            case_meta=_meta(), stage=stage, state=state)
    assert exc.value.code == "diagram_reference_outside_stage"
    db.expire_all()
    assert _snapshot(db, case_id) == before
    assert _counts(db) == counts


def test_save_case_new_case_failure_leaves_no_case_or_key(db, dataset):
    counts = _counts(db)
    key = _key()
    state = _f1_state()
    state["nodes"].append(_node("ghost", str(uuid.uuid4())))
    with pytest.raises(WorkspaceError) as exc:
        CaseWorkspaceService(db).save_case(
            case_id=None, base_revision=None, idempotency_key=key,
            case_meta=_meta(), stage=_f1_stage(dataset), state=state)
    assert exc.value.code == "diagram_reference_outside_stage"
    assert _counts(db) == counts
    assert db.query(InheritanceCase).filter(
        InheritanceCase.workspace_idempotency_key == key).first() is None


def test_save_case_bad_meta_type_does_not_write(db, dataset):
    create = _create_draft(db, dataset)
    case_id = create["case"]["id"]
    before = _snapshot(db, case_id)
    counts = _counts(db)
    with pytest.raises(WorkspaceError) as exc:
        CaseWorkspaceService(db).save_case(
            case_id=case_id, base_revision=1, idempotency_key=None,
            case_meta=_meta(ghi_chu=123), stage=_f1_stage(dataset),
            state=_f1_state())
    assert exc.value.code == "validation_error"
    db.expire_all()
    assert _snapshot(db, case_id) == before
    assert _counts(db) == counts


# ---------------------------------------------------------------- B4


def test_save_case_two_sessions_same_base_one_conflict(
        session_factory, dataset):
    seed = session_factory()
    created = _create_draft(seed, dataset)
    case_id = created["case"]["id"]
    seed.close()

    first = session_factory()
    second = session_factory()
    try:
        res = CaseWorkspaceService(first).save_case(
            case_id=case_id, base_revision=1, idempotency_key=None,
            case_meta=_meta(), stage=_f1_stage(dataset),
            state=_f1_state())
        assert res["case"]["revision"] == 2

        stage = _f1_stage(dataset)
        stage["people"][1] = dict(stage["people"][1],
                                  dia_chi="Người thua cuộc")
        with pytest.raises(WorkspaceError) as exc:
            CaseWorkspaceService(second).save_case(
                case_id=case_id, base_revision=1, idempotency_key=None,
                case_meta=_meta(), stage=stage, state=_f1_state())
        assert exc.value.code == "workspace_conflict"
        assert exc.value.details["server_revision"] == 2
    finally:
        first.close()
        second.close()

    check = session_factory()
    try:
        case = check.get(InheritanceCase, case_id)
        check.refresh(case)
        assert case.workspace_revision == 2
        assert case.person_rows[1].dia_chi == "Khu Giả Lập B"
    finally:
        check.close()


def test_save_case_new_replay_same_key_hash_does_not_increment(
        session_factory, dataset):
    key = _key()
    payload = dict(case_meta=_meta(), stage=_f1_stage(dataset),
                   state=_f1_state())
    first = session_factory()
    try:
        one = CaseWorkspaceService(first).save_case(
            case_id=None, base_revision=None, idempotency_key=key, **payload)
        counts = _counts(first)
    finally:
        first.close()

    second = session_factory()
    try:
        two = CaseWorkspaceService(second).save_case(
            case_id=None, base_revision=None, idempotency_key=key, **payload)
        assert two["created"] is False
        assert two["case"]["id"] == one["case"]["id"]
        assert two["case"]["revision"] == 1
        assert two["case"]["status"] == "done"
        assert _counts(second) == counts
    finally:
        second.close()


def test_save_case_same_key_different_payload_conflicts(db, dataset):
    key = _key()
    CaseWorkspaceService(db).save_case(
        case_id=None, base_revision=None, idempotency_key=key,
        case_meta=_meta(), stage=_f1_stage(dataset), state=_f1_state())
    with pytest.raises(WorkspaceError) as exc:
        CaseWorkspaceService(db).save_case(
            case_id=None, base_revision=None, idempotency_key=key,
            case_meta=_meta(ghi_chu="khác payload"),
            stage=_f1_stage(dataset), state=_f1_state())
    assert exc.value.code == "idempotency_conflict"


def test_save_case_retry_old_base_does_not_write_twice(db, dataset):
    create = _create_draft(db, dataset)
    case_id = create["case"]["id"]
    svc = CaseWorkspaceService(db)
    svc.save_case(case_id=case_id, base_revision=1, idempotency_key=None,
                  case_meta=_meta(), stage=_f1_stage(dataset),
                  state=_f1_state())
    before = _snapshot(db, case_id)
    with pytest.raises(WorkspaceError) as exc:
        svc.save_case(case_id=case_id, base_revision=1,
                      idempotency_key=None, case_meta=_meta(),
                      stage=_f1_stage(dataset), state=_f1_state())
    assert exc.value.code == "workspace_conflict"
    assert exc.value.details["server_revision"] == 2
    db.expire_all()
    assert _snapshot(db, case_id) == before


# ------------------------------------------------------------ envelope


def test_save_case_envelope_rules(db, dataset):
    svc = CaseWorkspaceService(db)
    cases = [
        dict(case_id=None, base_revision=1, idempotency_key=_key(),
             case_meta=_meta(), stage=_f1_stage(dataset),
             state=_f1_state()),
        dict(case_id=None, base_revision=None, idempotency_key=None,
             case_meta=_meta(), stage=_f1_stage(dataset),
             state=_f1_state()),
        dict(case_id=1, base_revision=None, idempotency_key=_key(),
             case_meta=_meta(), stage=_f1_stage(dataset),
             state=_f1_state()),
        dict(case_id=True, base_revision=1, idempotency_key=None,
             case_meta=_meta(), stage=_f1_stage(dataset),
             state=_f1_state()),
    ]
    for kwargs in cases:
        with pytest.raises(WorkspaceError) as exc:
            svc.save_case(**kwargs)
        assert exc.value.code == "validation_error", kwargs
    assert db.query(InheritanceCase).count() == 0


# ------------------------------------------------- mức tối thiểu owner 23/10


def _minimal_person(**overrides):
    row = {
        "row_id": str(uuid.uuid4()), "entity_id": None,
        "ho_ten": "Người Chỉ Tên", "gioi_tinh": None,
        "ngay_sinh": None, "ngay_chet": None,
        "so_giay_to": None, "ngay_cap": None, "noi_cap": None,
        "dia_chi": None, "place_of_origin": None,
        "loai_giay_to": None, "loai_dia_chi": None,
    }
    row.update(overrides)
    return row


def _minimal_asset(**overrides):
    row = {
        "row_id": str(uuid.uuid4()), "entity_id": None,
        "so_serial": "", "so_vao_so": None, "so_thua_dat": "7",
        "so_to_ban_do": "8", "dia_chi": None, "loai_so": None,
        "hinh_thuc_su_dung": None, "thoi_han": None, "nguon_goc": None,
        "ngay_cap": None, "co_quan_cap": None, "land_rows": None,
    }
    row.update(overrides)
    return row


EMPTY_STATE = {"version": 3, "domain": "inheritance", "nodes": []}


def test_save_case_minimum_fields_and_blank_strings_normalized(db):
    """S4d/S5b owner 23/10/2026: Người chỉ cần họ tên, Tài sản chỉ cần
    số thửa + số tờ; chuỗi rỗng/toàn khoảng trắng ghi null, không lỗi."""
    person = _minimal_person(
        so_giay_to="  ", noi_cap=" ", dia_chi="   ",
        place_of_origin="", loai_giay_to="", loai_dia_chi="  ")
    asset = _minimal_asset(
        so_vao_so=" ", loai_so="", hinh_thuc_su_dung=" ",
        thoi_han="", nguon_goc=" ", co_quan_cap="  ",
        dia_chi=" ", land_rows=None)

    saved = CaseWorkspaceService(db).save_case(
        case_id=None, base_revision=None, idempotency_key=_key(),
        case_meta=_meta(),
        stage={"owner_row_id": None, "people": [person],
               "assets": [asset]},
        state=EMPTY_STATE)

    assert saved["case"]["status"] == "done"
    out_person = saved["stage"]["people"][0]
    for field in ("so_giay_to", "noi_cap", "dia_chi",
                  "place_of_origin", "loai_giay_to", "loai_dia_chi"):
        assert out_person[field] is None, field
    out_asset = saved["stage"]["assets"][0]
    assert out_asset["so_thua_dat"] == "7"
    assert out_asset["so_to_ban_do"] == "8"
    for field in ("so_vao_so", "loai_so", "hinh_thuc_su_dung",
                  "thoi_han", "nguon_goc", "co_quan_cap", "dia_chi"):
        assert out_asset[field] is None, field


def test_save_case_asset_requires_thua_and_to(db):
    """S5b: dòng Tài sản thiếu số thửa hoặc số tờ vẫn bị chặn đúng ô."""
    for field in ("so_thua_dat", "so_to_ban_do"):
        person = _minimal_person()
        asset = _minimal_asset(**{field: "  "})
        with pytest.raises(WorkspaceError) as exc:
            CaseWorkspaceService(db).save_case(
                case_id=None, base_revision=None, idempotency_key=_key(),
                case_meta=_meta(),
                stage={"owner_row_id": None, "people": [person],
                       "assets": [asset]},
                state=EMPTY_STATE)
        assert exc.value.code == "stage_validation_error"
        errors = exc.value.details["field_errors"]
        assert any(e["field"] == field and e["code"] == "required"
                   for e in errors), field
    assert db.query(InheritanceCase).count() == 0


@pytest.mark.parametrize("field", ["so_thua_dat", "so_to_ban_do"])
def test_save_case_blank_parcel_or_sheet_preserves_existing_workspace(
        db, dataset, field):
    created = _create_draft(db, dataset)
    case_id = created["case"]["id"]
    svc = CaseWorkspaceService(db)
    before = svc.get(case_id)
    before_snapshot = _snapshot(db, case_id)
    stage = _f1_stage(dataset)
    stage["assets"][0][field] = "  "
    with pytest.raises(WorkspaceError) as exc:
        svc.save_case(
            case_id=case_id, base_revision=1, idempotency_key=None,
            case_meta=_meta(ghi_chu="không được lưu"), stage=stage,
            state=_f1_state())
    assert exc.value.code == "stage_validation_error"
    assert any(e["field"] == field and e["code"] == "required"
               for e in exc.value.details["field_errors"])
    db.expire_all()
    assert svc.get(case_id) == before
    assert _snapshot(db, case_id) == before_snapshot


def test_save_case_asset_ngay_cap_year_only(db):
    """S5c: ngày cấp Tài sản chấp nhận chỉ-năm như trường ngày của Người."""
    saved = CaseWorkspaceService(db).save_case(
        case_id=None, base_revision=None, idempotency_key=_key(),
        case_meta=_meta(),
        stage={"owner_row_id": None,
               "people": [_minimal_person()],
               "assets": [_minimal_asset(ngay_cap="2005")]},
        state=EMPTY_STATE)
    assert saved["stage"]["assets"][0]["ngay_cap"] == "2005"

    reopen = CaseWorkspaceService(db).get(saved["case"]["id"])
    assert reopen["stage"]["assets"][0]["ngay_cap"] == "2005"


# ------------------------ entity_id là hint nội bộ, không chặn user (23/10)


def test_save_case_new_ignores_unknown_entity_hints(db, dataset):
    """Hint entity_id không tồn tại → bỏ hint, resolve theo neo, Lưu được."""
    stage = _f1_stage(dataset)
    for row in stage["people"] + stage["assets"]:
        row["entity_id"] = 999999

    saved = CaseWorkspaceService(db).save_case(
        case_id=None, base_revision=None, idempotency_key=_key(),
        case_meta=_meta(), stage=stage, state=_f1_state())

    assert saved["created"] is True
    people = {p["row_id"]: p for p in saved["stage"]["people"]}
    for alias in ("P101", "P102", "P103"):
        row = people[dataset["people_prototypes"][alias]["row_id"]]
        assert row["entity_id"] is not None, alias
        assert row["entity_id"] != 999999, alias
    asset = saved["stage"]["assets"][0]
    assert asset["entity_id"] is not None
    assert asset["entity_id"] != 999999
    assert db.query(Customer).count() == 3
    assert db.query(Property).count() == 1


def test_save_case_existing_row_hint_mismatch_resolves_by_anchor(db, dataset):
    """Dòng đã có: hint lệch identity đang gắn (kể cả ID khác có thật) bị
    bỏ; identity giữ theo neo của chính dòng, không hijack dòng khác."""
    created = _create_draft(db, dataset)
    case_id = created["case"]["id"]
    stage = created["stage"]
    original = {p["row_id"]: p["entity_id"] for p in stage["people"]}
    original_asset = stage["assets"][0]["entity_id"]
    other_identity = stage["people"][1]["entity_id"]
    assert other_identity is not None
    stage["people"][0]["entity_id"] = other_identity
    stage["people"][1]["entity_id"] = 999999
    stage["assets"][0]["entity_id"] = 999999

    saved = CaseWorkspaceService(db).save_case(
        case_id=case_id, base_revision=1, idempotency_key=None,
        case_meta=_meta(), stage=stage, state=_f1_state())

    out = {p["row_id"]: p["entity_id"] for p in saved["stage"]["people"]}
    assert out[stage["people"][0]["row_id"]] == original[
        stage["people"][0]["row_id"]]
    assert out[stage["people"][1]["row_id"]] == original[
        stage["people"][1]["row_id"]]
    assert saved["stage"]["assets"][0]["entity_id"] == original_asset
    assert db.query(Customer).count() == 3
    assert db.query(Property).count() == 1


def test_save_case_new_row_garbage_hint_resolves_or_null(db, dataset):
    """Dòng mới mang hint rác: có neo → resolve theo neo; thiếu neo →
    entity_id null. Không raise vì entity_id."""
    created = _create_draft(db, dataset)
    case_id = created["case"]["id"]
    stage = created["stage"]
    with_doc = _minimal_person(
        ho_ten="Người Mới Có Neo", so_giay_to="000000000999",
        entity_id="hint-rác")
    without_doc = _minimal_person(
        ho_ten="Người Mới Không Neo", entity_id=999999)
    stage["people"] = stage["people"] + [with_doc, without_doc]

    saved = CaseWorkspaceService(db).save_case(
        case_id=case_id, base_revision=1, idempotency_key=None,
        case_meta=_meta(), stage=stage, state=_f1_state())

    rows = {p["row_id"]: p for p in saved["stage"]["people"]}
    assert rows[with_doc["row_id"]]["entity_id"] is not None
    assert rows[without_doc["row_id"]]["entity_id"] is None


def test_save_case_integrity_error_is_infra_not_fake_field(
        db, dataset, monkeypatch):
    """IntegrityError không còn giả danh `entity_id`: trả lỗi hạ tầng có mã
    riêng, không field_errors, không row giả (owner 23/10/2026)."""
    def boom(self, case, stage):
        raise IntegrityError(
            "INSERT INTO case_person_rows", {},
            Exception("UNIQUE constraint failed: case_person_rows.case_id, "
                      "case_person_rows.row_id"))

    monkeypatch.setattr(CaseWorkspaceService, "_write_stage_rows", boom)
    with pytest.raises(WorkspaceError) as exc:
        CaseWorkspaceService(db).save_case(
            case_id=None, base_revision=None, idempotency_key=_key(),
            case_meta=_meta(), stage=_f1_stage(dataset),
            state=_f1_state())

    assert exc.value.code == "workspace_storage_error"
    assert "field_errors" not in exc.value.details
    assert exc.value.details["constraint"] == "case_person_rows"
    assert exc.value.details["retryable"] is False

"""D1–D4 — Nháp ít dữ liệu + nhãn nháp (issue 13 vòng 2, lát (d)).

Đáp án đọc từ `fixtures/issue13_storage_b.json` (F3/F3B/F3C/F3D — thiết kế
vòng 2 §5) và literal DB, không lấy output service làm oracle:

- D1: `workspace_create` nhận 0 Người/0 Tài sản, `ho_ten=null`, owner
  inheritance null; non-null sai/ngoài Stage vẫn `workspace_owner_required`;
  sai kiểu tên/ngày vẫn lỗi + rollback; hai_bên vẫn cấm owner key.
- D2: `commit_stage` (Cập nhật) trên nháp đã đủ strict giữ `draft`;
  `save_case` chuyển `done`; adapter `case_list` trả `trang_thai` raw +
  `status_label`.
- D3: vòng đời neo identity trên dòng nháp — row_id ổn định, entity echo
  thật từ GET, đổi/xóa neo không merge, case khác độc lập.
- D4: lỗi giữa transaction create không để nửa case/key/identity; lỗi
  cập nhật draft giữ snapshot/revision cũ.
"""
import json
import uuid
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database
from models import (
    CasePersonRow,
    Customer,
    InheritanceCase,
    Property,
)
from routers import cases as cases_router
from services.case_workspace import CaseWorkspaceService, WorkspaceError

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "issue13_storage_b.json"


# ---------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def dataset():
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'partial_draft.db'}")
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


def _case_spec(dataset, alias):
    matches = [case for case in dataset["cases"] if case["alias"] == alias]
    assert len(matches) == 1, f"fixture phải có đúng một ca {alias}"
    return matches[0]


def _proto(dataset, section, alias, override=None):
    data = dict(dataset[section][alias])
    data.pop("alias", None)
    data.update(override or {})
    return data


def _meta(spec):
    metadata = spec["metadata"]
    return {
        "case_type": spec["case_type"],
        "document_type": metadata["loai_van_ban"],
        "ngay_lap_ho_so": metadata.get("ngay_lap_ho_so"),
    }


def _stage(spec, dataset, *, owner_row_id=None):
    people = [_proto(dataset, "people_prototypes", entry["prototype"],
                     entry.get("override"))
              for entry in spec["people"]]
    assets = [_proto(dataset, "asset_prototypes", entry["prototype"],
                     entry.get("override"))
              for entry in spec["assets"]]
    stage = {"people": people, "assets": assets}
    if spec["case_type"] == "inheritance":
        stage = {"owner_row_id": owner_row_id, **stage}
    return stage


def _create(db, spec, dataset, *, key=None, state=None,
            owner_row_id=None, stage=None):
    return CaseWorkspaceService(db).create(
        str(uuid.uuid4()) if key is None else key,
        _meta(spec),
        stage if stage is not None else _stage(
            spec, dataset, owner_row_id=owner_row_id),
        state)


def _service(db):
    return CaseWorkspaceService(db)


def _counts(db):
    return {
        "cases": db.query(InheritanceCase).count(),
        "customers": db.query(Customer).count(),
        "properties": db.query(Property).count(),
    }


# --------------------------------------------------------------------- D1


def test_create_empty_draft_reopens_empty_stage(db, dataset):
    spec = _case_spec(dataset, "F3D")
    data = _create(db, spec, dataset)

    assert data["created"] is True
    assert data["case"]["status"] == "draft"
    assert data["case"]["revision"] == 1
    assert data["stage"] == {"owner_row_id": None, "people": [], "assets": []}
    assert data["diagram"]["state"]["nodes"] == []
    assert data["diagram"]["render_model"] is None

    again = _service(db).get(data["case"]["id"])
    assert again["stage"] == {"owner_row_id": None, "people": [], "assets": []}
    assert again["diagram"]["state"]["nodes"] == []
    assert _counts(db) == {"cases": 1, "customers": 0, "properties": 0}
    assert db.query(CasePersonRow).count() == 0


def test_create_name_only_reopens_null_identity(db, dataset):
    spec = _case_spec(dataset, "F3")
    data = _create(db, spec, dataset)

    expected = spec["expected"]
    people = data["stage"]["people"]
    assert [p["ho_ten"] for p in people] == ["Người thử chưa đủ neo"]
    assert [p["entity_id"] for p in people] == [None]
    assert data["stage"]["assets"] == []
    assert data["stage"]["owner_row_id"] is None
    assert data["diagram"]["state"]["nodes"] == []
    assert _counts(db) == {"cases": 1, "customers": 0, "properties": 0}
    assert len(people) == expected["so_person_rows"]


def test_create_document_number_without_name_stores_null_name(db, dataset):
    spec = _case_spec(dataset, "F3B")
    data = _create(db, spec, dataset)

    row = db.query(CasePersonRow).one()
    assert row.ho_ten is None, "tên null phải lưu NULL, không phải chuỗi rỗng"
    assert row.so_giay_to == "SYN-P302-01"
    assert row.customer_id is None, "thiếu tên => chưa đủ neo, không identity"
    wire = data["stage"]["people"][0]
    assert wire["ho_ten"] is None
    assert wire["entity_id"] is None
    assert _counts(db) == {"cases": 1, "customers": 0, "properties": 0}


def test_create_assets_only_has_no_fake_person(db, dataset):
    spec = _case_spec(dataset, "F3C")
    data = _create(db, spec, dataset)

    assert data["stage"]["people"] == []
    assert data["stage"]["owner_row_id"] is None
    assert len(data["stage"]["assets"]) == 1
    assert data["stage"]["assets"][0]["entity_id"] is None
    assert db.query(InheritanceCase).one().nguoi_chet_id is None
    assert _counts(db) == {"cases": 1, "customers": 0, "properties": 0}


def test_create_owner_null_is_unassigned_not_an_error(db, dataset):
    spec = _case_spec(dataset, "F3")
    data = _create(db, spec, dataset, owner_row_id=None)

    assert data["stage"]["owner_row_id"] is None
    state = data["diagram"]["state"]
    assert state["nodes"] == [], "owner null không được seed node Chủ giả"


def test_create_owner_non_null_invalid_still_owner_required(db, dataset):
    spec = _case_spec(dataset, "F3")
    for bad_owner in (str(uuid.uuid4()), "not-a-uuid"):
        with pytest.raises(WorkspaceError) as exc:
            _create(db, spec, dataset, owner_row_id=bad_owner)
        assert exc.value.code == "workspace_owner_required", bad_owner
    assert _counts(db) == {"cases": 0, "customers": 0, "properties": 0}


def test_create_two_party_still_forbids_owner_key(db, dataset):
    spec = _case_spec(dataset, "F3D")
    meta = {"case_type": "two_party", "document_type": "chuyen_nhuong"}
    stage = {"owner_row_id": None, "people": [], "assets": []}
    with pytest.raises(WorkspaceError) as exc:
        _service(db).create(str(uuid.uuid4()), meta, stage, None)
    assert exc.value.code == "validation_error"
    assert db.query(InheritanceCase).count() == 0


@pytest.mark.parametrize("patch, field", [
    ({"ho_ten": 5}, "ho_ten"),
    ({"ho_ten": ["Nguyễn"]}, "ho_ten"),
    ({"ho_ten": {"ten": "Nguyễn"}}, "ho_ten"),
    ({"ngay_sinh": "2026-13-40"}, "ngay_sinh"),
    ({"ngay_sinh": "31/12/2020"}, "ngay_sinh"),
])
def test_create_wrong_type_or_date_rolls_back(db, dataset, patch, field):
    spec = _case_spec(dataset, "F3")
    before = _counts(db)
    with pytest.raises(WorkspaceError) as exc:
        _service(db).create(
            str(uuid.uuid4()), _meta(spec),
            _stage(spec, dataset, owner_row_id=None)
            | {"people": [{**_stage(spec, dataset)["people"][0], **patch}]},
            None)
    assert exc.value.code == "stage_validation_error"
    assert any(item["field"] == field
               for item in exc.value.details["field_errors"])
    assert _counts(db) == before


# --------------------------------------------------------------------- D2


def test_commit_keeps_draft_then_save_case_turns_done(db, dataset):
    spec = _case_spec(dataset, "F3")
    data = _create(db, spec, dataset)
    case_id = data["case"]["id"]
    row_id = data["stage"]["people"][0]["row_id"]

    # Cập nhật trên nháp: owner được gán, tên đã có, 0 Tài sản vẫn hợp lệ.
    stage = {"owner_row_id": row_id,
             "people": data["stage"]["people"], "assets": []}
    committed = _service(db).commit_stage(case_id, 1, stage)
    assert committed["revision"] == 2
    assert _service(db).get(case_id)["case"]["status"] == "draft"
    assert committed["stage"]["owner_row_id"] == row_id
    assert committed["stage"]["people"][0]["row_id"] == row_id

    # save_case case cũ: Lưu hồ sơ → done. Diagram inheritance cần Chủ đất
    # và 1 vị trí Tài sản (engine từ chối missing_land_owner) nên lượt Lưu
    # hồ sơ mang asset prototype + slot owner đã gán.
    save_state = {"version": 3, "domain": "inheritance", "nodes": [{
        "id": "owner", "personId": row_id, "parentSlotIds": [],
        "spouseSlotId": None, "ownPositions": [1], "receivePositions": [],
        "hidden": False, "deleted": False}]}
    saved = _service(db).save_case(
        case_id=case_id, base_revision=2,
        case_meta={}, stage={"owner_row_id": row_id,
                             "people": committed["stage"]["people"],
                             "assets": [_proto(dataset, "asset_prototypes",
                                               "T203")]},
        state=save_state)
    assert saved["case"]["status"] == "done"
    assert saved["case"]["revision"] == 3
    assert saved["stage"]["owner_row_id"] == row_id
    assert len(saved["stage"]["assets"]) == 1


def test_save_case_new_accepts_empty_stage_and_unassigned_owner(db, dataset):
    """S1+S2 owner 23/10/2026: Lưu hồ sơ mới không bắt ≥1 Người/≥1 Tài
    sản và không bắt Chủ đất; Diagram thiếu Chủ đất vẫn ghi được ở trạng
    thái incomplete (S3)."""
    spec = _case_spec(dataset, "F3")
    empty_state = {"version": 3, "domain": "inheritance", "nodes": []}
    saved = _service(db).save_case(
        case_id=None, base_revision=None,
        idempotency_key=str(uuid.uuid4()), case_meta=_meta(spec),
        stage={"owner_row_id": None, "people": [], "assets": []},
        state=empty_state)

    assert saved["created"] is True
    assert saved["case"]["status"] == "done"
    assert saved["case"]["revision"] == 1
    assert saved["stage"] == {"owner_row_id": None,
                              "people": [], "assets": []}
    assert saved["diagram"]["render_model"]["status"] == "incomplete"
    assert any(e["code"] == "missing_land_owner"
               for e in saved["diagram"]["render_model"]["errors"])
    assert _counts(db) == {"cases": 1, "customers": 0, "properties": 0}

    # Pointer owner non-null sai vẫn là mâu thuẫn dữ liệu (S11).
    with pytest.raises(WorkspaceError) as exc:
        _service(db).save_case(
            case_id=None, base_revision=None,
            idempotency_key=str(uuid.uuid4()), case_meta=_meta(spec),
            stage={"owner_row_id": str(uuid.uuid4()),
                   "people": [], "assets": []},
            state=empty_state)
    assert exc.value.code == "workspace_owner_required"

    assert _counts(db) == {"cases": 1, "customers": 0, "properties": 0}


# --------------------------------------------------------------------- D3


def test_identity_anchor_lifecycle_on_draft_row(db, session_factory, dataset):
    spec = _case_spec(dataset, "F3")
    created = _create(db, spec, dataset)
    case_id = created["case"]["id"]
    row_id = created["stage"]["people"][0]["row_id"]
    revision = created["case"]["revision"]

    def commit(stage):
        nonlocal revision
        data = _service(db).commit_stage(case_id, revision, stage)
        revision = data["revision"]
        return data

    # Thiếu neo (chỉ tên) → chưa có identity.
    assert created["stage"]["people"][0]["entity_id"] is None

    # Đủ neo: echo wire thật từ GET, thêm số giấy tờ → identity mới.
    current = _service(db).get(case_id)["stage"]
    current["people"][0]["so_giay_to"] = "D3-ANCHOR-01"
    data = commit({"owner_row_id": row_id, "people": current["people"],
                   "assets": []})
    first_entity = data["stage"]["people"][0]["entity_id"]
    assert isinstance(first_entity, int)
    assert data["stage"]["people"][0]["row_id"] == row_id
    first_customer = db.get(Customer, first_entity)
    assert first_customer.so_giay_to == "D3-ANCHOR-01"

    # Đổi neo → identity mới, row_id giữ nguyên, identity cũ không bị merge.
    current = _service(db).get(case_id)["stage"]
    current["people"][0]["so_giay_to"] = "D3-ANCHOR-02"
    data = commit({"owner_row_id": row_id, "people": current["people"],
                   "assets": []})
    second_entity = data["stage"]["people"][0]["entity_id"]
    assert isinstance(second_entity, int) and second_entity != first_entity
    assert data["stage"]["people"][0]["row_id"] == row_id
    assert db.get(Customer, first_entity) is not None, "identity cũ bị xóa/merge"
    assert db.query(Customer).count() == 2

    # Xóa neo → null; customer cũ vẫn còn nguyên (không merge).
    current = _service(db).get(case_id)["stage"]
    current["people"][0]["so_giay_to"] = None
    data = commit({"owner_row_id": row_id, "people": current["people"],
                   "assets": []})
    assert data["stage"]["people"][0]["entity_id"] is None
    assert data["stage"]["people"][0]["row_id"] == row_id
    assert db.query(Customer).count() == 2

    # Case khác dùng neo gốc không bị đổi theo.
    other = _create(db, _case_spec(dataset, "F3D"), dataset)
    assert other["case"]["id"] != case_id

    fresh = session_factory()
    try:
        rows = fresh.query(CasePersonRow).filter_by(case_id=case_id).all()
        assert [(r.row_id, r.customer_id) for r in rows] == [(row_id, None)]
    finally:
        fresh.close()


def test_other_case_identity_untouched_by_anchor_change(db, dataset):
    spec = _case_spec(dataset, "F3")
    first = _create(db, spec, dataset)
    base_person = dict(_stage(spec, dataset)["people"][0])
    second_stage = {
        "owner_row_id": None,
        "people": [{**base_person, "row_id": str(uuid.uuid4())}],
        "assets": [],
    }
    second = _create(db, spec, dataset, stage=second_stage)
    row_a = first["stage"]["people"][0]["row_id"]
    row_b = second["stage"]["people"][0]["row_id"]

    stage_a = _service(db).get(first["case"]["id"])["stage"]
    stage_a["people"][0]["so_giay_to"] = "D3-SHARED-01"
    _service(db).commit_stage(first["case"]["id"], 1,
                              {"owner_row_id": row_a,
                               "people": stage_a["people"], "assets": []})
    stage_b = _service(db).get(second["case"]["id"])["stage"]
    stage_b["people"][0]["so_giay_to"] = "D3-SHARED-01"
    _service(db).commit_stage(second["case"]["id"], 1,
                              {"owner_row_id": row_b,
                               "people": stage_b["people"], "assets": []})
    assert (db.query(Customer).count()) == 1
    db_row_a = db.query(CasePersonRow).filter_by(row_id=row_a).one()
    db_row_b = db.query(CasePersonRow).filter_by(row_id=row_b).one()
    assert db_row_a.customer_id == db_row_b.customer_id

    # Đổi neo ở case A không đổi case B.
    stage_a = _service(db).get(first["case"]["id"])["stage"]
    stage_a["people"][0]["so_giay_to"] = "D3-SHARED-02"
    _service(db).commit_stage(first["case"]["id"], 2,
                              {"owner_row_id": row_a,
                               "people": stage_a["people"], "assets": []})
    db.expire_all()
    assert db.query(CasePersonRow).filter_by(row_id=row_b).one().customer_id \
        == db_row_b.customer_id
    assert db.query(Customer).count() == 2


# --------------------------------------------------------------------- D4


def test_create_fault_after_rows_leaves_no_half_case(db, monkeypatch, dataset):
    spec = _case_spec(dataset, "F3")
    key = str(uuid.uuid4())

    def boom(*_args, **_kwargs):
        raise RuntimeError("injected after rows")

    monkeypatch.setattr(CaseWorkspaceService, "_build_payload", boom)
    with pytest.raises(RuntimeError):
        _create(db, spec, dataset, key=key)
    monkeypatch.undo()

    assert _counts(db) == {"cases": 0, "customers": 0, "properties": 0}
    assert db.query(InheritanceCase).filter(
        InheritanceCase.workspace_idempotency_key == key).count() == 0
    assert db.query(CasePersonRow).count() == 0

    # Cùng key sau rollback tạo được case sạch (không bị key mồ côi).
    data = _create(db, spec, dataset, key=key)
    assert data["created"] is True
    assert _counts(db)["cases"] == 1


def test_draft_update_fault_keeps_snapshot_and_revision(
        db, session_factory, monkeypatch, dataset):
    spec = _case_spec(dataset, "F3")
    data = _create(db, spec, dataset)
    case_id = data["case"]["id"]
    row_id = data["stage"]["people"][0]["row_id"]
    before_case = db.get(InheritanceCase, case_id)
    before_state = before_case.case_state_json
    before_revision = before_case.workspace_revision

    stage = _service(db).get(case_id)["stage"]
    stage["people"][0]["ho_ten"] = "Tên sẽ không được ghi"

    def boom(*_args, **_kwargs):
        raise RuntimeError("injected before commit")

    monkeypatch.setattr(CaseWorkspaceService, "_build_payload", boom)
    with pytest.raises(RuntimeError):
        _service(db).commit_stage(case_id, before_revision,
                                  {"owner_row_id": row_id,
                                   "people": stage["people"],
                                   "assets": []})
    monkeypatch.undo()

    fresh = session_factory()
    try:
        case = fresh.get(InheritanceCase, case_id)
        assert case.workspace_revision == before_revision
        assert case.case_state_json == before_state
        row = fresh.query(CasePersonRow).filter_by(case_id=case_id).one()
        assert row.ho_ten == "Người thử chưa đủ neo"
    finally:
        fresh.close()


# ------------------------------------------------------- D1 router form


@pytest.fixture()
def client(session_factory):
    app = FastAPI()
    app.include_router(cases_router.router, prefix="/cases")

    def get_test_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[cases_router.get_db] = get_test_db
    with TestClient(app) as test_client:
        yield test_client


def test_router_create_empty_form_makes_empty_draft(client, session_factory):
    response = client.post("/cases/create", data={}, follow_redirects=False)
    assert response.status_code == 302

    with session_factory() as session:
        case = session.query(InheritanceCase).one()
        assert case.trang_thai == "draft"
        assert case.person_rows == []
        assert case.asset_rows == []
        assert case.nguoi_chet_id is None
        assert case.tai_san_id is None


def test_router_create_explicit_empty_stage_skips_master_fallback(
        client, session_factory):
    with session_factory() as session:
        owner = Customer(ho_ten="Owner", so_giay_to="001",
                         name_anchor="owner", document_anchor="001")
        prop = Property(so_serial="WEB-D1", dia_chi="Đất giả lập")
        session.add_all([owner, prop])
        session.commit()
        owner_id, property_id = owner.id, prop.id

    response = client.post("/cases/create", data={
        "nguoi_chet_id": str(owner_id),
        "tai_san_id": str(property_id),
        "case_state_json": json.dumps(
            {"schemaVersion": 1, "stage": [], "diagram": {}}),
    }, follow_redirects=False)
    assert response.status_code == 302

    with session_factory() as session:
        case = session.query(InheritanceCase).one()
        assert case.person_rows == [], "explicit [] bị thay bằng master"
        assert len(case.asset_rows) == 1
        payload = json.loads(case.case_state_json)
        assert payload["owner_row_id"] is None


def test_router_create_hydrates_master_only_without_posted_stage(
        client, session_factory):
    with session_factory() as session:
        owner = Customer(ho_ten="Owner", so_giay_to="001",
                         name_anchor="owner", document_anchor="001")
        session.add(owner)
        session.commit()
        owner_id = owner.id

    response = client.post("/cases/create", data={
        "nguoi_chet_id": str(owner_id),
    }, follow_redirects=False)
    assert response.status_code == 302

    with session_factory() as session:
        case = session.query(InheritanceCase).one()
        assert len(case.person_rows) == 1
        payload = json.loads(case.case_state_json)
        assert payload["owner_row_id"] == case.person_rows[0].row_id

"""Tests for services.case_workspace — real backend of notary.case-drafting.v1.

Uses a temporary SQLite DB per test (tmp_path) — never touches notary.db.
Wire shapes follow contracts/notary-case-drafting/*.schema.json.
"""
import json
import re
import sqlite3
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database
from models import (
    Customer,
    InheritanceCase,
    InheritanceCaseProperty,
    InheritanceParticipant,
    Property,
)
from services.case_workspace import (
    SCHEMA_VERSION,
    CaseWorkspaceService,
    WorkspaceError,
)


UUID4_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}"
    r"-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)


# ---------------------------------------------------------------- fixtures


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'workspace.db'}")
    database.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


def _make_case(db, *, loai_van_ban="khai_nhan", trang_thai="draft",
               case_state_json=None, with_participant=False):
    deceased = Customer(
        ho_ten="Nguyễn Văn An", gioi_tinh="Nam",
        ngay_sinh=date(1950, 1, 1), ngay_chet=date(2011, 5, 15),
        so_giay_to="001234567890", dia_chi="Số 1 phố Huế, Hà Nội",
    )
    prop = Property(
        so_serial="DD123456", dia_chi="Thửa 123, tờ 45, phường Bạch Mai",
        so_vao_so="CS 12345", so_thua_dat="123", so_to_ban_do="45",
    )
    db.add_all([deceased, prop])
    db.flush()
    case = InheritanceCase(
        nguoi_chet_id=deceased.id, tai_san_id=prop.id,
        ngay_lap_ho_so=date(2026, 9, 1), loai_van_ban=loai_van_ban,
        trang_thai=trang_thai, case_state_json=case_state_json,
    )
    db.add(case)
    db.flush()
    db.add(InheritanceCaseProperty(
        case_id=case.id, property_id=prop.id, is_primary=True))
    heirs = []
    if with_participant:
        heir = Customer(
            ho_ten="Nguyễn Thị Bình", gioi_tinh="Nữ",
            ngay_sinh=date(1980, 3, 2), dia_chi="Số 1 phố Huế, Hà Nội",
        )
        db.add(heir)
        db.flush()
        db.add(InheritanceParticipant(
            ho_so_id=case.id, customer_id=heir.id, vai_tro="Con"))
        heirs.append(heir)
    db.commit()
    return case, deceased, prop, heirs


def _person_row(**overrides):
    row = {
        "row_id": str(uuid.uuid4()),
        "entity_id": None,
        "ho_ten": "Người Mới",
        "gioi_tinh": "Nam",
        "ngay_sinh": "1980-01-01",
        "ngay_chet": None,
        "so_giay_to": None,
        "ngay_cap": None,
        "noi_cap": None,
        "dia_chi": "xã test",
        "place_of_origin": None,
    }
    row.update(overrides)
    return row


def _asset_row(**overrides):
    row = {
        "row_id": str(uuid.uuid4()),
        "entity_id": None,
        "is_primary": True,
        "so_serial": "EE123456",
        "so_vao_so": "CS 99999",
        "so_thua_dat": "99",
        "so_to_ban_do": "12",
        "dia_chi": "Thửa 99, xã Yên Sở",
        "loai_so": "GCN QSDĐ",
        "hinh_thuc_su_dung": "Sử dụng riêng",
        "thoi_han": "Lâu dài",
        "nguon_goc": "Cấp đổi",
        "ngay_cap": "2005-09-30",
        "co_quan_cap": "UBND quận Hai Bà Trưng",
        "land_rows": [{"loai_dat": "ODT", "dien_tich": 85.5,
                       "thoi_han": "Lâu dài"}],
    }
    row.update(overrides)
    return row


def _service(db):
    return CaseWorkspaceService(db)


def _workspace_people(result):
    return result["stage"]["people"]


# ------------------------------------------------------------------- get()


def test_get_derives_stage_for_legacy_case_without_case_state(db):
    case, deceased, prop, heirs = _make_case(db, with_participant=True)

    data = _service(db).get(case.id)

    assert data["schema_version"] == SCHEMA_VERSION
    assert data["backend_mode"] == "real"
    assert data["case"] == {
        "id": case.id,
        "case_type": "inheritance",
        "document_type": "khai_nhan",
        "status": "draft",
        "locked": False,
        "revision": 1,
    }
    people = _workspace_people(data)
    assert [p["entity_id"] for p in people] == [deceased.id, heirs[0].id]
    assert people[0]["ho_ten"] == "Nguyễn Văn An"
    assert people[0]["ngay_chet"] == "2011-05-15"
    assert people[0]["gioi_tinh"] == "Nam"
    assert people[1]["ho_ten"] == "Nguyễn Thị Bình"
    for row in people:
        assert UUID4_RE.match(row["row_id"])
    assets = data["stage"]["assets"]
    assert len(assets) == 1
    assert assets[0]["entity_id"] == prop.id
    assert assets[0]["is_primary"] is True
    assert assets[0]["so_serial"] == "DD123456"
    assert data["diagram"]["domain"] == "inheritance"
    assert data["diagram"]["state"] == {"version": 2, "nodes": []}
    assert data["diagram"]["render_model"] is None
    assert data["capabilities"] == {
        "intake": ["image", "pdf", "docx", "xlsx", "text"],
        "diagram": True,
        "word_export": True,
    }


def test_get_generates_stable_row_ids_across_reloads(db, session_factory):
    case, _deceased, _prop, _heirs = _make_case(db, with_participant=True)

    first = _service(db).get(case.id)
    first_ids = [p["row_id"] for p in first["stage"]["people"]]
    first_asset_ids = [a["row_id"] for a in first["stage"]["assets"]]

    db2 = session_factory()
    try:
        second = _service(db2).get(case.id)
    finally:
        db2.close()

    assert [p["row_id"] for p in second["stage"]["people"]] == first_ids
    assert [a["row_id"] for a in second["stage"]["assets"]] == first_asset_ids


def test_get_multiple_people_and_assets(db):
    case, deceased, prop, _h = _make_case(db)
    other_prop = Property(so_serial="EE654321", dia_chi="Thửa 77, tờ 12")
    extra = Customer(ho_ten="Trần Thị Cẩm", gioi_tinh="Nữ")
    db.add_all([other_prop, extra])
    db.flush()
    db.add(InheritanceCaseProperty(
        case_id=case.id, property_id=other_prop.id, is_primary=False))
    db.commit()

    data = _service(db).get(case.id)

    assets = {a["so_serial"]: a for a in data["stage"]["assets"]}
    assert set(assets) == {"DD123456", "EE654321"}
    assert assets["DD123456"]["is_primary"] is True
    assert assets["EE654321"]["is_primary"] is False


def test_get_migrates_legacy_engine_state_to_v2(db):
    case, deceased, prop, heirs = _make_case(db, with_participant=True)
    heir = heirs[0]
    owner_row_id = str(uuid.uuid4())
    heir_row_id = str(uuid.uuid4())
    legacy_state = {
        "schemaVersion": 1,
        "stage": [
            {"id": str(deceased.id), "row_id": owner_row_id,
             "ho_ten": deceased.ho_ten},
            {"id": str(heir.id), "row_id": heir_row_id,
             "ho_ten": heir.ho_ten},
        ],
        "diagram": {
            "engineState": {
                "version": 2,
                "updatedAt": "2026-05-11T10:00:00.000Z",
                "nodes": [
                    {"id": "owner", "kind": "person", "relationType": "owner",
                     "personId": str(deceased.id), "isLandOwner": True},
                    {"id": "spouse", "kind": "person",
                     "relationType": "spouse", "personId": str(heir.id),
                     "sourceId": "owner", "willReceive": True},
                ],
            },
            "assignments": {"owner": str(deceased.id),
                            "spouse": str(heir.id)},
        },
    }
    case.case_state_json = json.dumps(legacy_state, ensure_ascii=False)
    db.commit()

    data = _service(db).get(case.id)
    nodes = {n["id"]: n for n in data["diagram"]["state"]["nodes"]}

    assert set(nodes) == {"owner", "spouse"}
    assert nodes["owner"]["personId"] == owner_row_id
    assert nodes["owner"]["spouseSlotId"] == "spouse"
    assert nodes["owner"]["isLandOwner"] is True
    assert nodes["spouse"]["personId"] == heir_row_id
    assert nodes["spouse"]["spouseSlotId"] == "owner"
    assert nodes["spouse"]["parentSlotIds"] == []
    # migrated state must persist — reload shows the same V2 nodes
    db2 = db
    data2 = _service(db2).get(case.id)
    assert data2["diagram"]["state"] == data["diagram"]["state"]


def test_get_unsupported_case_type_disables_capabilities(db):
    case, _d, _p, _h = _make_case(db, loai_van_ban="khac")

    data = _service(db).get(case.id)

    assert data["case"]["case_type"] != "inheritance"
    assert data["capabilities"]["intake"] == []
    assert data["capabilities"]["diagram"] is False
    assert data["capabilities"]["word_export"] is False


def test_get_supports_thoa_thuan_document_type(db):
    case, _d, _p, _h = _make_case(db, loai_van_ban="thoa_thuan")

    data = _service(db).get(case.id)

    assert data["case"]["case_type"] == "inheritance"
    assert data["case"]["document_type"] == "thoa_thuan"


def test_get_missing_case_raises_case_not_found(db):
    with pytest.raises(WorkspaceError) as exc:
        _service(db).get(9999)
    assert exc.value.code == "case_not_found"


def test_get_on_locked_case_still_readable(db):
    case, _d, _p, _h = _make_case(db, trang_thai="locked")

    data = _service(db).get(case.id)

    assert data["case"]["locked"] is True
    assert data["case"]["status"] == "locked"


# ------------------------------------------------------------- commit_stage


def test_commit_stage_increments_revision_and_returns_render_model(db):
    case, deceased, prop, _h = _make_case(db)
    people = [
        _person_row(entity_id=deceased.id, ho_ten="Nguyễn Văn An",
                    ngay_sinh="1950", ngay_chet="2011-05-15",
                    so_giay_to="001234567890",
                    dia_chi="Số 1 phố Huế, Hà Nội"),
        _person_row(ho_ten="Nguyễn Văn Cường", gioi_tinh="Nam",
                    ngay_sinh="1980-07-20", so_giay_to="001080012345"),
    ]
    assets = [_asset_row(entity_id=prop.id, so_serial="DD123456",
                         dia_chi="Thửa 123, tờ 45, phường Bạch Mai")]

    data = _service(db).commit_stage(case.id, 1, people, assets)

    assert data["schema_version"] == SCHEMA_VERSION
    assert data["revision"] == 2
    assert db.get(InheritanceCase, case.id).workspace_revision == 2
    assert data["diagram"]["render_model"] is not None
    assert data["diagram"]["render_model"]["engineVersion"] == 2
    committed_people = data["stage"]["people"]
    assert committed_people[0]["entity_id"] == deceased.id
    assert committed_people[0]["row_id"] == people[0]["row_id"]
    assert committed_people[1]["entity_id"] is not None  # backend-assigned
    assert committed_people[1]["row_id"] == people[1]["row_id"]
    assert db.query(Customer).filter_by(
        so_giay_to="001080012345").one().ho_ten == "Nguyễn Văn Cường"


def test_commit_stage_new_rows_persist_then_reload(db, session_factory):
    case, deceased, prop, _h = _make_case(db)
    people = [_person_row(entity_id=deceased.id, ho_ten="Nguyễn Văn An"),
              _person_row(ho_ten="Người Hoàn Toàn Mới")]
    assets = [_asset_row(entity_id=prop.id, so_serial="DD123456")]

    committed = _service(db).commit_stage(case.id, 1, people, assets)

    db2 = session_factory()
    try:
        reloaded = _service(db2).get(case.id)
    finally:
        db2.close()

    assert reloaded["case"]["revision"] == 2
    assert [p["row_id"] for p in reloaded["stage"]["people"]] == [
        p["row_id"] for p in committed["stage"]["people"]]
    assert reloaded["stage"]["people"][1]["ho_ten"] == "Người Hoàn Toàn Mới"
    assert reloaded["diagram"]["render_model"] == \
        committed["diagram"]["render_model"]


def test_commit_stage_invalid_row_rolls_back_everything(db, session_factory):
    case, deceased, prop, heirs = _make_case(db, with_participant=True)
    before_state = case.case_state_json
    customers_before = db.query(Customer).count()

    people = [
        _person_row(entity_id=deceased.id, ho_ten="Nguyễn Văn An"),
        _person_row(ho_ten="Dòng Hợp Lệ", so_giay_to="009999999999"),
        _person_row(ho_ten="Dòng Sai Giới Tính", gioi_tinh="Khác"),
    ]
    bad_row_id = people[2]["row_id"]
    assets = [_asset_row(entity_id=prop.id, so_serial="DD123456")]

    with pytest.raises(WorkspaceError) as exc:
        _service(db).commit_stage(case.id, 1, people, assets)

    assert exc.value.code == "stage_validation_error"
    field_errors = exc.value.details["field_errors"]
    assert any(
        e["row_id"] == bad_row_id and e["field"] == "gioi_tinh"
        and e["code"] == "invalid_enum"
        for e in field_errors
    )

    db2 = session_factory()
    try:
        assert db2.query(Customer).count() == customers_before
        reloaded = db2.get(InheritanceCase, case.id)
        assert reloaded.workspace_revision == 1
        assert reloaded.case_state_json == before_state
    finally:
        db2.close()


def test_commit_stage_collects_multiple_field_errors(db):
    case, deceased, prop, _h = _make_case(db)
    bad = _person_row(entity_id=deceased.id, ho_ten="",
                      ngay_sinh="15/05/2011")

    with pytest.raises(WorkspaceError) as exc:
        _service(db).commit_stage(case.id, 1, [bad], [])

    errors = exc.value.details["field_errors"]
    by_field = {e["field"]: e for e in errors}
    assert by_field["ho_ten"]["code"] == "required"
    assert by_field["ngay_sinh"]["code"] == "invalid_date"
    assert all(e["row_id"] == bad["row_id"] for e in errors)


def test_commit_stage_rejects_duplicate_row_id(db):
    case, deceased, prop, _h = _make_case(db)
    shared = str(uuid.uuid4())
    people = [_person_row(row_id=shared, ho_ten="A"),
              _person_row(row_id=shared, ho_ten="B")]

    with pytest.raises(WorkspaceError) as exc:
        _service(db).commit_stage(case.id, 1, people, [])

    assert exc.value.code == "stage_validation_error"
    assert any(e["code"] == "duplicate_row_id" and e["row_id"] == shared
               for e in exc.value.details["field_errors"])


def test_commit_stage_enforces_single_primary_asset(db):
    case, _d, prop, _h = _make_case(db)
    assets = [
        _asset_row(entity_id=prop.id, so_serial="DD123456", is_primary=True),
        _asset_row(so_serial="GG123456", is_primary=True),
    ]

    with pytest.raises(WorkspaceError) as exc:
        _service(db).commit_stage(case.id, 1, [], assets)
    assert any(e["code"] == "primary_count"
               for e in exc.value.details["field_errors"])

    assets[1]["is_primary"] = False
    assets[0]["is_primary"] = False
    with pytest.raises(WorkspaceError) as exc2:
        _service(db).commit_stage(case.id, 1, [], assets)
    assert any(e["code"] == "primary_count"
               for e in exc2.value.details["field_errors"])


def test_commit_stage_rejects_noncanonical_so_serial(db):
    case, _d, _p, _h = _make_case(db)
    asset = _asset_row(so_serial="dd 12-34")

    with pytest.raises(WorkspaceError) as exc:
        _service(db).commit_stage(case.id, 1, [], [asset])

    assert any(e["field"] == "so_serial" and e["code"] == "invalid_format"
               for e in exc.value.details["field_errors"])


def test_commit_stage_locked_case(db):
    case, deceased, prop, _h = _make_case(db, trang_thai="locked")

    with pytest.raises(WorkspaceError) as exc:
        _service(db).commit_stage(
            case.id, 1,
            [_person_row(entity_id=deceased.id)],
            [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    assert exc.value.code == "workspace_locked"


def test_commit_stage_stale_and_ahead_base_revision(db):
    case, deceased, prop, _h = _make_case(db)

    # revision 1: base_revision 99 (ahead) → workspace_conflict
    with pytest.raises(WorkspaceError) as ahead:
        _service(db).commit_stage(case.id, 99, [], [])
    assert ahead.value.code == "workspace_conflict"
    assert ahead.value.details["server_revision"] == 1

    _service(db).commit_stage(
        case.id, 1, [_person_row(entity_id=deceased.id)],
        [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    # revision now 2: base_revision 1 (stale) → workspace_conflict
    with pytest.raises(WorkspaceError) as stale:
        _service(db).commit_stage(case.id, 1, [], [])
    assert stale.value.code == "workspace_conflict"
    assert stale.value.details["server_revision"] == 2


def test_commit_stage_unsupported_case_type(db):
    case, deceased, prop, _h = _make_case(db, loai_van_ban="khac")

    with pytest.raises(WorkspaceError) as exc:
        _service(db).commit_stage(
            case.id, 1, [_person_row(entity_id=deceased.id)],
            [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    assert exc.value.code == "case_type_unsupported"
    assert exc.value.details["case_type"] != "inheritance"


def test_commit_stage_missing_case(db):
    with pytest.raises(WorkspaceError) as exc:
        _service(db).commit_stage(9999, 1, [], [])
    assert exc.value.code == "case_not_found"


def test_commit_stage_prunes_diagram_and_reevaluates(db):
    case, deceased, prop, heirs = _make_case(db, with_participant=True)
    heir = heirs[0]
    owner_row = str(uuid.uuid4())
    heir_row = str(uuid.uuid4())
    state = {
        "version": 2,
        "nodes": [
            {"id": "owner", "personId": owner_row, "parentSlotIds": [],
             "spouseSlotId": "spouse", "isLandOwner": True,
             "willReceive": False, "hidden": False, "deleted": False},
            {"id": "spouse", "personId": heir_row, "parentSlotIds": [],
             "spouseSlotId": "owner", "isLandOwner": False,
             "willReceive": True, "hidden": False, "deleted": False},
        ],
    }
    case.case_state_json = json.dumps({
        "schemaVersion": 2,
        "stage": [
            {"id": str(deceased.id), "row_id": owner_row,
             "ho_ten": deceased.ho_ten},
            {"id": str(heir.id), "row_id": heir_row,
             "ho_ten": heir.ho_ten},
        ],
        "assets": [{"id": str(prop.id), "row_id": str(uuid.uuid4()),
                    "is_primary": True}],
        "diagram": {"state": state, "render_model": None},
    }, ensure_ascii=False)
    db.commit()

    people = [
        _person_row(row_id=owner_row, entity_id=deceased.id,
                    ho_ten="Nguyễn Văn An", ngay_chet="2011-05-15"),
    ]
    data = _service(db).commit_stage(
        case.id, 1, people,
        [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    nodes = data["diagram"]["state"]["nodes"]
    assert [n["id"] for n in nodes] == ["owner"]
    assert nodes[0]["spouseSlotId"] is None
    assert data["diagram"]["render_model"] is not None
    # spouse was removed — new render model must not allocate to it
    assert heir_row not in data["diagram"]["render_model"]["allocations"]

    # legacy projections keep entity ids (row_id → entity map)
    persisted = json.loads(
        db.get(InheritanceCase, case.id).case_state_json)
    assert persisted["diagram"]["assignments"] == {
        "owner": str(deceased.id)}
    assert persisted["diagram"]["engineState"]["nodes"][0][
        "personId"] == str(deceased.id)
    column_state = json.loads(
        db.get(InheritanceCase, case.id).engine_state_json)
    assert column_state["nodes"][0]["personId"] == str(deceased.id)


def test_commit_stage_does_not_merge_duplicate_names(db):
    case, _d, prop, _h = _make_case(db)
    people = [
        _person_row(ho_ten="Trùng Tên"),
        _person_row(ho_ten="Trùng Tên"),
    ]

    data = _service(db).commit_stage(
        case.id, 1, people, [_asset_row(entity_id=prop.id,
                                       so_serial="DD123456")])

    ids = {p["entity_id"] for p in data["stage"]["people"]}
    assert len(ids) == 2
    assert db.query(Customer).filter_by(ho_ten="Trùng Tên").count() == 2


def test_commit_stage_upserts_by_document_key(db):
    case, _d, prop, _h = _make_case(db)
    existing = Customer(ho_ten="Người Có Sẵn", so_giay_to="007777777777")
    db.add(existing)
    db.commit()

    data = _service(db).commit_stage(
        case.id, 1,
        [_person_row(ho_ten="Người Có Sẵn Đổi Tên",
                     so_giay_to="007777777777")],
        [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    assert data["stage"]["people"][0]["entity_id"] == existing.id
    assert db.get(Customer, existing.id).ho_ten == "Người Có Sẵn Đổi Tên"
    assert db.query(Customer).filter_by(
        so_giay_to="007777777777").count() == 1


def test_commit_stage_updates_links_and_is_primary(db, session_factory):
    case, _d, prop, _h = _make_case(db)
    other = Property(so_serial="HH654321", dia_chi="Thửa khác")
    db.add(other)
    db.commit()

    data = _service(db).commit_stage(
        case.id, 1, [],
        [_asset_row(entity_id=prop.id, so_serial="DD123456",
                    is_primary=False),
         _asset_row(entity_id=other.id, so_serial="HH654321",
                    is_primary=True)])

    assert {a["so_serial"]: a["is_primary"]
            for a in data["stage"]["assets"]} == {
                "DD123456": False, "HH654321": True}
    db2 = session_factory()
    try:
        links = {l.property_id: l.is_primary for l in db2.query(
            InheritanceCaseProperty).filter_by(case_id=case.id)}
        assert links == {prop.id: False, other.id: True}
        assert db2.get(InheritanceCase, case.id).tai_san_id == other.id
    finally:
        db2.close()


def test_committed_case_state_still_normalizes_for_web(db):
    """case_state_json ghi bởi service phải parse được bằng helper web cũ."""
    from routers.cases import _normalize_case_state_json

    case, deceased, prop, _h = _make_case(db)
    _service(db).commit_stage(
        case.id, 1, [_person_row(entity_id=deceased.id)],
        [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    raw = db.get(InheritanceCase, case.id).case_state_json
    normalized = json.loads(_normalize_case_state_json(raw))
    assert normalized["stage"][0]["id"] == str(deceased.id)
    assert normalized["stage"][0]["row_id"]
    assert normalized["diagram"]["state"]["version"] == 2


# -------------------------------------------------------------- migration


def test_migration_adds_workspace_columns_to_legacy_db(tmp_path):
    db_path = Path(tmp_path) / "legacy.db"
    con = sqlite3.connect(db_path)
    con.execute(
        """CREATE TABLE inheritance_cases (
               id INTEGER PRIMARY KEY,
               nguoi_chet_id INTEGER NOT NULL,
               tai_san_id INTEGER NOT NULL,
               ngay_lap_ho_so DATE NOT NULL)""")
    con.commit()
    con.close()

    original = database.DB_PATH
    try:
        database.DB_PATH = db_path
        database.migrate_inheritance_cases_schema()
        database.migrate_inheritance_cases_schema()  # idempotent
    finally:
        database.DB_PATH = original

    con = sqlite3.connect(db_path)
    info = {row[1]: row for row in con.execute(
        "PRAGMA table_info(inheritance_cases)")}
    con.close()

    assert "workspace_revision" in info
    assert info["workspace_revision"][4] == "1"  # dflt_value
    assert "updated_at" in info


def test_model_declares_workspace_columns():
    cols = InheritanceCase.__table__.columns
    assert "workspace_revision" in cols
    assert "updated_at" in cols
    assert cols["workspace_revision"].nullable is False

"""Tests for services.case_workspace — real backend of notary.case-drafting.v2.

Uses a temporary SQLite DB per test (tmp_path) — never touches notary.db.
Wire shapes follow contracts/notary-case-drafting/*.schema.json §13:
stage `{owner_row_id?, people[], assets[]}`, diagram_state v3
`{version:3, domain, nodes[]}` — is_primary/isLandOwner/willReceive bị cấm
trên wire v2 (vị trí = index mảng; owner = stage.owner_row_id).
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
TP_IDS = [f"p{i}" for i in range(1, 31)]


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
    """asset_row v2 — KHÔNG is_primary (vị trí = index mảng)."""
    row = {
        "row_id": str(uuid.uuid4()),
        "entity_id": None,
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


def _stage(people, assets, owner_row_id="__omit__"):
    """stage_v2 — inheritance cần owner_row_id; "__omit__" = không emit."""
    st = {"people": people, "assets": assets}
    if owner_row_id != "__omit__":
        st["owner_row_id"] = owner_row_id
    return st


def _inheritance_stage(people, assets):
    """Stage hợp lệ tối thiểu: owner = people[0]."""
    return _stage(people, assets, owner_row_id=people[0]["row_id"])


def _commit(db, case_id, base_revision, people, assets):
    """Commit stage inheritance chuẩn — owner = people[0].row_id."""
    return _service(db).commit_stage(
        case_id, base_revision, _inheritance_stage(people, assets))


def _node(nid, person_id=None, parents=(), spouse=None, own=(),
          receive=(), hidden=False, deleted=False):
    """diagram node v3 (§13.4) — ownPositions/receivePositions ⊆ {1,2,3}."""
    return {"id": nid, "personId": person_id,
            "parentSlotIds": list(parents), "spouseSlotId": spouse,
            "ownPositions": list(own), "receivePositions": list(receive),
            "hidden": hidden, "deleted": deleted}


def _v3_state(nodes, domain="inheritance"):
    return {"version": 3, "domain": domain, "nodes": nodes}


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
        "ngay_lap_ho_so": "2026-09-01",
        "noi_niem_yet": None,
        "nguoi_nhan_uy_quyen": None,
        "nguoi_nhan_uy_quyen_id": None,
        "noi_dung_viec": None,
        "ghi_chu": None,
        **{key: None for key in (
            "tenvanban", "nhomhopdong", "loaivanbannhandien", "socongchung",
            "ngaycongchung", "congchungvien", "thuky", "chudat")},
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
    assert "is_primary" not in assets[0]           # v2: không emit
    assert assets[0]["so_serial"] == "DD123456"
    # v2: stage inheritance emit owner_row_id (null — legacy chưa có
    # pointer lẫn node owner để derive).
    assert "owner_row_id" in data["stage"]
    assert data["stage"]["owner_row_id"] is None
    assert data["diagram"]["domain"] == "inheritance"
    assert data["diagram"]["state"] == {
        "version": 3, "domain": "inheritance", "nodes": []}
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
    for a in assets.values():
        assert "is_primary" not in a


def test_get_migrates_legacy_engine_state_to_v3(db):
    """Legacy engineState (relationType/isLandOwner/willReceive) → node v3:
    isLandOwner → ownPositions=1..asset_count; willReceive →
    receivePositions; node owner persist → stage.owner_row_id."""
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
    state = data["diagram"]["state"]
    assert state["version"] == 3 and state["domain"] == "inheritance"
    nodes = {n["id"]: n for n in state["nodes"]}

    assert set(nodes) == {"owner", "spouse"}
    for n in nodes.values():          # v3: không còn flag v1 trên wire
        assert "isLandOwner" not in n and "willReceive" not in n
    assert nodes["owner"]["personId"] == owner_row_id
    assert nodes["owner"]["spouseSlotId"] == "spouse"
    assert nodes["owner"]["ownPositions"] == [1]     # isLandOwner → own
    assert nodes["spouse"]["personId"] == heir_row_id
    assert nodes["spouse"]["spouseSlotId"] == "owner"
    assert nodes["spouse"]["parentSlotIds"] == []
    assert nodes["spouse"]["receivePositions"] == [1]
    # node owner persist → pointer stage derive được
    assert data["stage"]["owner_row_id"] == owner_row_id
    # migrated state must persist — reload shows the same V3 nodes
    data2 = _service(db).get(case.id)
    assert data2["diagram"]["state"] == data["diagram"]["state"]


def test_get_two_party_case_state_and_capabilities(db):
    """two_party: stage không owner_row_id; state canonical 30 slot;
    word_export=true (NAIA-8); render_model null khi chưa commit."""
    case, _d, _p, _h = _make_case(db, loai_van_ban="chuyen_nhuong")

    data = _service(db).get(case.id)

    assert data["case"]["case_type"] == "two_party"
    assert data["case"]["document_type"] == "chuyen_nhuong"
    assert "owner_row_id" not in data["stage"]
    st = data["diagram"]["state"]
    assert st["version"] == 3 and st["domain"] == "two_party"
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    assert all(set(n) == {"id", "personId", "hidden", "deleted"}
               for n in st["nodes"])
    assert data["capabilities"]["word_export"] is True
    assert data["capabilities"]["diagram"] is True


def test_get_unsupported_case_type_disables_capabilities(db):
    case, _d, _p, _h = _make_case(db, loai_van_ban="khac")

    data = _service(db).get(case.id)

    assert data["case"]["case_type"] not in ("inheritance", "two_party")
    assert data["capabilities"]["intake"] == []
    assert data["capabilities"]["diagram"] is False
    assert data["capabilities"]["word_export"] is False
    # fallback domain inheritance → stage emit owner_row_id (§13.5)
    assert "owner_row_id" in data["stage"]


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

    data = _commit(db, case.id, 1, people, assets)

    assert data["schema_version"] == SCHEMA_VERSION
    assert data["revision"] == 2
    assert db.get(InheritanceCase, case.id).workspace_revision == 2
    assert data["stage"]["owner_row_id"] == people[0]["row_id"]
    assert data["diagram"]["render_model"] is not None
    assert data["diagram"]["render_model"]["engineVersion"] == 2
    committed_people = data["stage"]["people"]
    assert committed_people[0]["entity_id"] == deceased.id
    assert committed_people[0]["row_id"] == people[0]["row_id"]
    assert committed_people[1]["entity_id"] is not None  # backend-assigned
    assert committed_people[1]["row_id"] == people[1]["row_id"]
    assert "is_primary" not in data["stage"]["assets"][0]
    assert db.query(Customer).filter_by(
        so_giay_to="001080012345").one().ho_ten == "Nguyễn Văn Cường"


def test_commit_stage_owner_pointer_required(db):
    """§13.6: owner_row_id null/missing/dangling → workspace_owner_required
    (check trước stage field errors)."""
    case, deceased, prop, _h = _make_case(db)
    people = [_person_row(entity_id=deceased.id)]
    assets = [_asset_row(entity_id=prop.id, so_serial="DD123456")]

    for bad in (None, str(uuid.uuid4()), "not-uuid"):
        with pytest.raises(WorkspaceError) as exc:
            _service(db).commit_stage(
                case.id, 1, _stage(people, assets, owner_row_id=bad))
        assert exc.value.code == "workspace_owner_required", bad
    # thiếu key hoàn toàn
    with pytest.raises(WorkspaceError) as exc:
        _service(db).commit_stage(case.id, 1, _stage(people, assets))
    assert exc.value.code == "workspace_owner_required"


def test_commit_stage_owner_syncs_node(db):
    """§13.6: node 'owner' đã persist được sync personId := owner_row_id
    khi pointer stage đổi; node không tồn tại → không tự tạo."""
    case, deceased, prop, heirs = _make_case(db, with_participant=True)
    heir = heirs[0]
    owner_row = str(uuid.uuid4())
    heir_row = str(uuid.uuid4())
    case.case_state_json = json.dumps({
        "schemaVersion": 3,
        "owner_row_id": owner_row,
        "stage": [
            {"id": str(deceased.id), "row_id": owner_row,
             "ho_ten": deceased.ho_ten},
            {"id": str(heir.id), "row_id": heir_row,
             "ho_ten": heir.ho_ten},
        ],
        "assets": [{"id": str(prop.id), "row_id": str(uuid.uuid4()),
                    "is_primary": True}],
        "diagram": {"state": _v3_state([
            _node("owner", owner_row, own=[1]),
            _node("spouse", heir_row, receive=[1])]),
                    "render_model": None},
    }, ensure_ascii=False)
    db.commit()

    people = [
        _person_row(row_id=owner_row, entity_id=deceased.id,
                    ho_ten="Nguyễn Văn An", ngay_chet="2011-05-15"),
        _person_row(row_id=heir_row, entity_id=heir.id,
                    ho_ten="Nguyễn Thị Bình", gioi_tinh="Nữ",
                    ngay_sinh="1980-03-02"),
    ]
    # pointer đổi sang heir → node owner.personId theo pointer mới
    data = _service(db).commit_stage(
        case.id, 1, _stage(
            people, [_asset_row(entity_id=prop.id, so_serial="DD123456")],
            owner_row_id=heir_row))
    owner = next(n for n in data["diagram"]["state"]["nodes"]
                 if n["id"] == "owner")
    assert owner["personId"] == heir_row
    assert data["stage"]["owner_row_id"] == heir_row


def test_commit_stage_new_rows_persist_then_reload(db, session_factory):
    case, deceased, prop, _h = _make_case(db)
    people = [_person_row(entity_id=deceased.id, ho_ten="Nguyễn Văn An"),
              _person_row(ho_ten="Người Hoàn Toàn Mới")]
    assets = [_asset_row(entity_id=prop.id, so_serial="DD123456")]

    committed = _commit(db, case.id, 1, people, assets)

    db2 = session_factory()
    try:
        reloaded = _service(db2).get(case.id)
    finally:
        db2.close()

    assert reloaded["case"]["revision"] == 2
    assert reloaded["stage"]["owner_row_id"] == \
        committed["stage"]["owner_row_id"]
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
        _commit(db, case.id, 1, people, assets)

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
        _commit(db, case.id, 1, [bad], [])

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
        _commit(db, case.id, 1, people, [])

    assert exc.value.code == "stage_validation_error"
    assert any(e["code"] == "duplicate_row_id" and e["row_id"] == shared
               for e in exc.value.details["field_errors"])


def test_commit_stage_rejects_is_primary_and_asset_limit(db):
    """v2: is_primary trên wire = trường lạ → validation_error;
    assets > 3 → field_error asset_limit (§13.3)."""
    case, deceased, prop, _h = _make_case(db)
    people = [_person_row(entity_id=deceased.id)]

    bad_asset = _asset_row(entity_id=prop.id, so_serial="DD123456")
    bad_asset["is_primary"] = True
    with pytest.raises(WorkspaceError) as exc:
        _commit(db, case.id, 1, people, [bad_asset])
    assert exc.value.code == "validation_error"

    assets = [_asset_row(entity_id=prop.id, so_serial="DD123456")] + [
        _asset_row(so_serial=f"GG{i:06d}") for i in range(3)]
    with pytest.raises(WorkspaceError) as exc2:
        _commit(db, case.id, 1, people, assets)
    assert any(e["code"] == "asset_limit"
               for e in exc2.value.details["field_errors"])


@pytest.mark.parametrize("serial", ["TEST-RAW/001", "", "  RAW  "])
def test_commit_stage_accepts_verbatim_so_serial(db, session_factory, serial):
    """Serial là chuỗi nguyên văn, có thể rỗng/ngoài mẫu (entities.md §2)."""
    case, deceased, _p, _h = _make_case(db)
    data = _commit(db, case.id, 1, [_person_row(entity_id=deceased.id)],
                   [_asset_row(so_serial=serial)])

    assert data["stage"]["assets"][0]["so_serial"] == serial
    fresh = session_factory()
    try:
        reopened = CaseWorkspaceService(fresh).get(case.id)
    finally:
        fresh.close()
    assert reopened["stage"]["assets"][0]["so_serial"] == serial


def test_commit_stage_allows_duplicate_serial_on_distinct_parcels(
        db, session_factory):
    """Hai thửa/tờ khác nhau cùng serial → hai Property riêng, không gộp."""
    case, deceased, prop, _h = _make_case(db)
    first = _asset_row(entity_id=prop.id, so_serial="DD123456",
                       so_thua_dat="123", so_to_ban_do="45",
                       dia_chi="Thửa 123, tờ 45")
    second = _asset_row(so_serial="DD123456", so_thua_dat="456",
                        so_to_ban_do="78", dia_chi="Thửa 456, tờ 78")

    data = _commit(db, case.id, 1, [_person_row(entity_id=deceased.id)],
                   [first, second])

    assets = data["stage"]["assets"]
    assert [a["so_serial"] for a in assets] == ["DD123456", "DD123456"]
    assert assets[0]["entity_id"] != assets[1]["entity_id"]
    assert db.query(Property).filter_by(so_serial="DD123456").count() == 2

    fresh = session_factory()
    try:
        reopened = CaseWorkspaceService(fresh).get(case.id)
    finally:
        fresh.close()
    saved = reopened["stage"]["assets"]
    assert [a["so_serial"] for a in saved] == ["DD123456", "DD123456"]
    assert [a["so_thua_dat"] for a in saved] == ["123", "456"]
    assert saved[0]["entity_id"] != saved[1]["entity_id"]


def test_commit_stage_rejects_non_string_so_serial(db):
    case, deceased, _p, _h = _make_case(db)
    asset = _asset_row(so_serial=None)

    with pytest.raises(WorkspaceError) as exc:
        _commit(db, case.id, 1, [_person_row(entity_id=deceased.id)],
                [asset])

    assert any(e["field"] == "so_serial" and e["code"] == "invalid_type"
               for e in exc.value.details["field_errors"])


def test_commit_stage_locked_case(db):
    case, deceased, prop, _h = _make_case(db, trang_thai="locked")

    with pytest.raises(WorkspaceError) as exc:
        _commit(db, case.id, 1, [_person_row(entity_id=deceased.id)],
                [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    assert exc.value.code == "workspace_locked"


def test_commit_stage_stale_and_ahead_base_revision(db):
    case, deceased, prop, _h = _make_case(db)

    # revision 1: base_revision 99 (ahead) → workspace_conflict
    with pytest.raises(WorkspaceError) as ahead:
        _service(db).commit_stage(case.id, 99, {})
    assert ahead.value.code == "workspace_conflict"
    assert ahead.value.details["server_revision"] == 1

    _commit(db, case.id, 1, [_person_row(entity_id=deceased.id)],
            [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    # revision now 2: base_revision 1 (stale) → workspace_conflict
    with pytest.raises(WorkspaceError) as stale:
        _service(db).commit_stage(case.id, 1, {})
    assert stale.value.code == "workspace_conflict"
    assert stale.value.details["server_revision"] == 2


def test_commit_stage_unsupported_case_type(db):
    case, deceased, prop, _h = _make_case(db, loai_van_ban="khac")

    with pytest.raises(WorkspaceError) as exc:
        _commit(db, case.id, 1, [_person_row(entity_id=deceased.id)],
                [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    assert exc.value.code == "case_type_unsupported"
    assert exc.value.details["case_type"] not in ("inheritance", "two_party")


def test_commit_stage_two_party_canonical_and_unsupported(db):
    """two_party commit: stage không owner_row_id; state canonical 30 ô;
    render_model.status='unsupported' (§13.5); nguoi_chet neo people[0]."""
    case, deceased, prop, _h = _make_case(db, loai_van_ban="chuyen_nhuong")
    people = [_person_row(entity_id=deceased.id, ho_ten="Bên A",
                          ngay_chet=None)]
    data = _service(db).commit_stage(
        case.id, 1, _stage(people, [_asset_row(entity_id=prop.id,
                                              so_serial="DD123456")]))

    assert data["revision"] == 2
    assert "owner_row_id" not in data["stage"]
    st = data["diagram"]["state"]
    assert st["domain"] == "two_party"
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    assert data["diagram"]["render_model"]["status"] == "unsupported"
    assert data["diagram"]["render_model"]["allocations"] == {}
    db.refresh(case)
    assert case.nguoi_chet_id == deceased.id


def test_commit_stage_two_party_owner_row_id_forbidden(db):
    case, deceased, prop, _h = _make_case(db, loai_van_ban="tang_cho")
    people = [_person_row(entity_id=deceased.id)]
    stage = _stage(people, [_asset_row(entity_id=prop.id)],
                   owner_row_id=None)          # key cấm với two_party

    with pytest.raises(WorkspaceError) as exc:
        _service(db).commit_stage(case.id, 1, stage)
    assert exc.value.code == "validation_error"


def test_commit_stage_missing_case(db):
    with pytest.raises(WorkspaceError) as exc:
        _service(db).commit_stage(9999, 1, _stage([], []))
    assert exc.value.code == "case_not_found"


def test_commit_stage_prunes_diagram_and_reevaluates(db):
    """personId ngoài stage commit → node bị bỏ + link dangling scrub;
    render_model re-evaluate không còn allocation cho node đã gỡ."""
    case, deceased, prop, heirs = _make_case(db, with_participant=True)
    heir = heirs[0]
    owner_row = str(uuid.uuid4())
    heir_row = str(uuid.uuid4())
    case.case_state_json = json.dumps({
        "schemaVersion": 3,
        "owner_row_id": owner_row,
        "stage": [
            {"id": str(deceased.id), "row_id": owner_row,
             "ho_ten": deceased.ho_ten},
            {"id": str(heir.id), "row_id": heir_row,
             "ho_ten": heir.ho_ten},
        ],
        "assets": [{"id": str(prop.id), "row_id": str(uuid.uuid4()),
                    "is_primary": True}],
        "diagram": {"state": _v3_state([
            _node("owner", owner_row, spouse="spouse", own=[1]),
            _node("spouse", heir_row, spouse="owner", receive=[1])]),
                    "render_model": None},
    }, ensure_ascii=False)
    db.commit()

    people = [
        _person_row(row_id=owner_row, entity_id=deceased.id,
                    ho_ten="Nguyễn Văn An", ngay_chet="2011-05-15"),
    ]
    data = _commit(db, case.id, 1, people,
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
    assert persisted["schemaVersion"] == 3
    assert persisted["diagram"]["assignments"] == {
        "owner": str(deceased.id)}
    assert persisted["diagram"]["engineState"]["nodes"][0][
        "personId"] == str(deceased.id)
    column_state = json.loads(
        db.get(InheritanceCase, case.id).engine_state_json)
    assert column_state["nodes"][0]["personId"] == str(deceased.id)


def test_commit_stage_prunes_out_of_range_positions(db):
    """§13.3: chọn vị trí > len(assets) → prune + warning
    diagram.selection_pruned (không reject)."""
    case, deceased, prop, _h = _make_case(db)
    owner_row = str(uuid.uuid4())
    case.case_state_json = json.dumps({
        "schemaVersion": 3,
        "owner_row_id": owner_row,
        "stage": [{"id": str(deceased.id), "row_id": owner_row,
                   "ho_ten": deceased.ho_ten}],
        "assets": [{"id": str(prop.id), "row_id": str(uuid.uuid4()),
                    "is_primary": True}],
        "diagram": {"state": _v3_state([
            _node("owner", owner_row, own=[1, 2, 3])]),
                    "render_model": None},
    }, ensure_ascii=False)
    db.commit()

    people = [_person_row(row_id=owner_row, entity_id=deceased.id,
                          ho_ten="Nguyễn Văn An", ngay_chet="2011-05-15")]
    data = _commit(db, case.id, 1, people,
                   [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    owner = next(n for n in data["diagram"]["state"]["nodes"]
                 if n["id"] == "owner")
    assert owner["ownPositions"] == [1]
    codes = [w["code"] for w in data["diagram"].get("warnings") or []]
    assert "diagram.selection_pruned" in codes


def _diagram_nodes_v3(owner_row, spouse_row, child_row, father_row,
                      sib_row, gc_row):
    """state v3 cho case gia đình đầy đủ: owner + cha + vợ + con + anh em
    + cháu — dùng kiểm chứng legacy projection (H1) và participant sync."""
    return [
        _node("owner", owner_row, parents=("father",), spouse="spouse",
              own=[1]),
        _node("father", father_row, receive=[1]),
        _node("spouse", spouse_row, spouse="owner", receive=[1]),
        _node("child1", child_row, parents=("owner", "spouse"),
              receive=[1]),
        _node("sib1", sib_row, parents=("father",), receive=[1]),
        _node("gc1", gc_row, parents=("child1",), receive=[1]),
    ]


def _seed_diagram_case(db):
    """Case với stage 6 người + persisted diagram v3 (chưa commit lại)."""
    case, deceased, prop, heirs = _make_case(db, with_participant=True)
    spouse = heirs[0]
    extras = {}
    for key, name, gender, died in (
            ("father", "Nguyễn Văn Cha", "Nam", date(1990, 1, 1)),
            ("child", "Nguyễn Văn Con", "Nam", None),
            ("sib", "Nguyễn Thị Em", "Nữ", None),
            ("gc", "Nguyễn Văn Cháu", "Nam", None)):
        cust = Customer(ho_ten=name, gioi_tinh=gender, ngay_chet=died)
        db.add(cust)
        db.flush()
        extras[key] = cust
    db.commit()
    people = {
        "owner": deceased, "spouse": spouse, "father": extras["father"],
        "child": extras["child"], "sib": extras["sib"], "gc": extras["gc"],
    }
    rows = {k: str(uuid.uuid4()) for k in people}
    state = _v3_state(_diagram_nodes_v3(
        rows["owner"], rows["spouse"], rows["child"],
        rows["father"], rows["sib"], rows["gc"]))
    case.case_state_json = json.dumps({
        "schemaVersion": 3,
        "owner_row_id": rows["owner"],
        "stage": [{"id": str(c.id), "row_id": rows[k],
                   "ho_ten": c.ho_ten} for k, c in people.items()],
        "assets": [{"id": str(prop.id), "row_id": str(uuid.uuid4()),
                    "is_primary": True}],
        "diagram": {"state": state, "render_model": None},
    }, ensure_ascii=False)
    db.commit()
    return case, prop, people, rows


def _commit_diagram_people(people, rows):
    """Stage people rows cho toàn bộ entities theo row_id đã seed."""
    wire = {
        "owner": {"gioi_tinh": "Nam", "ngay_sinh": "1950",
                  "ngay_chet": "2011-05-15"},
        "spouse": {"gioi_tinh": "Nữ", "ngay_sinh": "1980-03-02"},
        "father": {"gioi_tinh": "Nam", "ngay_chet": "1990-01-01"},
        "child": {"gioi_tinh": "Nam", "ngay_sinh": "1978-01-01"},
        "sib": {"gioi_tinh": "Nữ", "ngay_sinh": "1975-06-06"},
        "gc": {"gioi_tinh": "Nam", "ngay_sinh": "2000-01-01"},
    }
    return [
        _person_row(row_id=rows[k], entity_id=c.id, ho_ten=c.ho_ten,
                    **wire[k])
        for k, c in people.items()
    ]


def test_committed_legacy_projection_consumable_by_web(db):
    """H1: engineState projection sau commit phải đọc được bởi web cũ —
    `_extract_diagram_participants` 0 lỗi, vai_tro đúng, owner không là
    participant; fields diagram_edges.js tiêu thụ đầy đủ."""
    from routers.cases import _extract_diagram_participants

    case, prop, people, rows = _seed_diagram_case(db)
    _commit(db, case.id, 1, _commit_diagram_people(people, rows),
            [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    persisted = json.loads(db.get(InheritanceCase, case.id).case_state_json)
    engine_state = persisted["diagram"]["engineState"]
    nodes = {n["id"]: n for n in engine_state["nodes"]}

    # vocabulary mà diagram_edges.js + word_engine tiêu thụ
    assert nodes["owner"]["relationType"] == "owner"
    assert nodes["owner"]["role"] == "Owner"
    assert nodes["father"]["relationType"] == "parent"
    assert nodes["father"]["role"] == "Cha"
    assert nodes["spouse"]["relationType"] == "spouse"
    assert nodes["spouse"]["role"] == "Vợ/Chồng"
    assert nodes["spouse"]["spouseOf"] == "owner"
    assert nodes["child1"]["relationType"] == "child"
    assert nodes["child1"]["role"] == "Con"
    assert nodes["child1"]["familyGroupId"] == "ownerSpouse"
    assert nodes["child1"]["parentPersonId"] == str(people["owner"].id)
    assert nodes["sib1"]["relationType"] == "sibling"
    assert nodes["sib1"]["role"] == "Anh/Chị/Em"
    assert nodes["sib1"]["familyGroupId"] == "birthParents"
    assert nodes["sib1"]["parentSlotId"] == "father"
    assert nodes["gc1"]["relationType"] == "grandchild"
    assert nodes["gc1"]["role"] == "Cháu"
    assert nodes["gc1"]["parentSlotId"] == "child1"
    assert nodes["gc1"]["parentPersonId"] == str(people["child"].id)
    assert nodes["father"]["label"] == "Nguyễn Văn Cha"

    # consumer thật của web: 0 lỗi, vai_tro đúng, owner không phải participant
    customers = {str(c.id): c for c in db.query(Customer).all()}
    participants, participant_ids = _extract_diagram_participants(
        engine_state, customers, str(people["owner"].id))
    roles = {p.customer_id: p.vai_tro for p in participants}
    assert people["owner"].id not in participant_ids
    assert roles[people["spouse"].id] == "Vợ/Chồng"
    assert roles[people["father"].id] == "Cha"
    assert roles[people["child"].id] == "Con"
    assert roles[people["sib"].id] == "Anh/Chị/Em"
    assert roles[people["gc"].id] == "Cháu"


def test_commit_stage_rebuilds_participants_and_owner(db):
    """M2: commit sync `case.participants` + `nguoi_chet_id` theo diagram."""
    case, prop, people, rows = _seed_diagram_case(db)
    _commit(db, case.id, 1, _commit_diagram_people(people, rows),
            [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    db.refresh(case)
    assert case.nguoi_chet_id == people["owner"].id
    parts = {p.customer_id: p for p in case.participants}
    assert people["owner"].id not in parts  # người chết không là participant
    assert parts[people["spouse"].id].vai_tro == "Vợ/Chồng"
    assert parts[people["spouse"].id].hang_thua_ke == 1
    assert parts[people["spouse"].id].parent_customer_id is None
    assert parts[people["father"].id].vai_tro == "Cha"
    assert parts[people["child"].id].vai_tro == "Con"
    assert parts[people["child"].id].parent_customer_id == people["owner"].id
    assert parts[people["sib"].id].vai_tro == "Anh/Chị/Em"
    assert parts[people["sib"].id].hang_thua_ke == 2
    assert parts[people["gc"].id].vai_tro == "Cháu"
    assert parts[people["gc"].id].parent_customer_id == people["child"].id
    assert parts[people["father"].id].co_nhan_tai_san is True
    assert case.tong_ty_le == 0.0


def test_commit_stage_concurrent_same_base_conflicts(db, session_factory):
    """M1: 2 commit cùng base_revision trên 2 session — chỉ 1 cái thắng,
    cái thua nhận workspace_conflict với server_revision mới."""
    case, deceased, prop, _h = _make_case(db)
    s1 = session_factory()
    s2 = session_factory()
    try:
        # hai session đều giữ snapshot revision=1
        assert s1.get(InheritanceCase, case.id).workspace_revision == 1
        assert s2.get(InheritanceCase, case.id).workspace_revision == 1
        _commit(s1, case.id, 1, [_person_row(entity_id=deceased.id)],
                [_asset_row(entity_id=prop.id, so_serial="DD123456")])
        with pytest.raises(WorkspaceError) as exc:
            _commit(s2, case.id, 1, [_person_row(entity_id=deceased.id)],
                    [_asset_row(entity_id=prop.id, so_serial="DD123456")])
        assert exc.value.code == "workspace_conflict"
        assert exc.value.details["server_revision"] == 2
    finally:
        s1.close()
        s2.close()
    s3 = session_factory()
    try:
        assert s3.get(InheritanceCase, case.id).workspace_revision == 2
    finally:
        s3.close()


def test_get_migrate_on_read_does_not_overwrite_newer_commit(
        db, session_factory):
    """M1: get() trên snapshot cũ (stale ORM) không được ghi đè commit mới —
    guarded UPDATE miss → đọc lại trạng thái mới."""
    case, deceased, prop, _h = _make_case(db)
    # cache attributes trong session `db` trước khi session khác commit —
    # sau đó ORM object giữ snapshot cũ (rev 1, case_state_json=None).
    assert case.workspace_revision == 1
    assert case.case_state_json is None
    s2 = session_factory()
    try:
        committed = _commit(
            s2, case.id, 1, [_person_row(entity_id=deceased.id)],
            [_asset_row(entity_id=prop.id, so_serial="DD123456")])
    finally:
        s2.close()

    data = _service(db).get(case.id)

    assert data["case"]["revision"] == 2
    assert [p["row_id"] for p in data["stage"]["people"]] == [
        p["row_id"] for p in committed["stage"]["people"]]


def test_get_keeps_legacy_raw_serial_without_surrogate(db):
    """Serial cũ ngoài mẫu được đọc nguyên văn; không sinh XX/không cảnh báo
    thay mã. dia_chi rỗng vẫn → null; ho_ten rỗng → '(Chưa rõ)'."""
    case, _d, prop, _h = _make_case(db)
    prop.so_serial = "dd-12 34"
    prop.dia_chi = ""
    db.commit()

    data = _service(db).get(case.id)

    asset = data["stage"]["assets"][0]
    assert asset["so_serial"] == "dd-12 34"
    assert asset["dia_chi"] is None
    assert not any("so_serial" in str(w)
                   for w in data["diagram"].get("warnings", []))

    case.case_state_json = json.dumps({
        "schemaVersion": 3,
        "stage": [{"id": "9999", "row_id": str(uuid.uuid4()),
                   "ho_ten": ""}],
        "assets": [], "diagram": {}}, ensure_ascii=False)
    db.commit()
    data2 = _service(db).get(case.id)
    assert data2["stage"]["people"][0]["ho_ten"] == "(Chưa rõ)"


def test_commit_stage_does_not_merge_duplicate_names(db):
    case, _d, prop, _h = _make_case(db)
    people = [
        _person_row(ho_ten="Trùng Tên"),
        _person_row(ho_ten="Trùng Tên"),
    ]

    data = _commit(db, case.id, 1, people,
                   [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    ids = {p["entity_id"] for p in data["stage"]["people"]}
    assert len(ids) == 2
    assert db.query(Customer).filter_by(ho_ten="Trùng Tên").count() == 2


def test_commit_stage_upserts_by_document_key(db):
    case, _d, prop, _h = _make_case(db)
    existing = Customer(ho_ten="Người Có Sẵn", so_giay_to="007777777777")
    db.add(existing)
    db.commit()

    data = _commit(
        db, case.id, 1,
        [_person_row(ho_ten="Người Có Sẵn Đổi Tên",
                     so_giay_to="007777777777")],
        [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    assert data["stage"]["people"][0]["entity_id"] == existing.id
    assert db.get(Customer, existing.id).ho_ten == "Người Có Sẵn Đổi Tên"
    assert db.query(Customer).filter_by(
        so_giay_to="007777777777").count() == 1


def test_commit_stage_updates_links_and_primary_position(db, session_factory):
    """v2: vị trí 1 (index 0) = primary trong link projection + tai_san_id
    (§13.3 — wire không còn is_primary; thứ tự mảng là SOT)."""
    case, deceased, prop, _h = _make_case(db)
    other = Property(so_serial="HH654321", dia_chi="Thửa khác")
    db.add(other)
    db.commit()

    people = [_person_row(entity_id=deceased.id)]
    data = _commit(
        db, case.id, 1, people,
        [_asset_row(entity_id=other.id, so_serial="HH654321"),
         _asset_row(entity_id=prop.id, so_serial="DD123456")])

    assert [a["so_serial"] for a in data["stage"]["assets"]] == [
        "HH654321", "DD123456"]
    db2 = session_factory()
    try:
        links = {l.property_id: l.is_primary for l in db2.query(
            InheritanceCaseProperty).filter_by(case_id=case.id)}
        assert links == {other.id: True, prop.id: False}
        assert db2.get(InheritanceCase, case.id).tai_san_id == other.id
    finally:
        db2.close()


def test_committed_case_state_still_normalizes_for_web(db):
    """case_state_json ghi bởi service phải parse được bằng helper web cũ."""
    from routers.cases import _normalize_case_state_json

    case, deceased, prop, _h = _make_case(db)
    _commit(db, case.id, 1, [_person_row(entity_id=deceased.id)],
            [_asset_row(entity_id=prop.id, so_serial="DD123456")])

    raw = db.get(InheritanceCase, case.id).case_state_json
    normalized = json.loads(_normalize_case_state_json(raw))
    assert normalized["stage"][0]["id"] == str(deceased.id)
    assert normalized["stage"][0]["row_id"]
    assert normalized["diagram"]["state"]["version"] == 3


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
    assert "workspace_idempotency_key" in cols
    assert cols["workspace_revision"].nullable is False


# ------------------------------------------------------------------ create()


def _create_args():
    """(people, assets, state) hợp lệ tối thiểu — owner đã chết + vợ nhận."""
    owner = _person_row(
        ho_ten="Nguyễn Văn An", ngay_sinh="1950", ngay_chet="2011-05-15",
        so_giay_to="001234567890")
    spouse = _person_row(
        ho_ten="Trần Thị Bình", gioi_tinh="Nữ", ngay_sinh="1955-03-02",
        so_giay_to="009876543210")
    state = _v3_state([
        _node("owner", owner["row_id"], spouse="spouse", own=[1]),
        _node("spouse", spouse["row_id"], spouse="owner", receive=[1]),
    ])
    return [owner, spouse], [_asset_row()], state


_UNSET = object()


def _create(db, people, assets, state, key=_UNSET, meta=_UNSET,
            owner_row_id=_UNSET):
    """create(key, meta, stage, state) — stage = {owner_row_id?, people,
    assets}; owner_row_id mặc định = people[0].row_id (inheritance)."""
    if owner_row_id is _UNSET:
        owner_row_id = people[0]["row_id"] if people else None
    stage = _stage(people, assets, owner_row_id=owner_row_id)
    return _service(db).create(
        str(uuid.uuid4()) if key is _UNSET else key,
        {"document_type": "khai_nhan"} if meta is _UNSET else meta,
        stage, state)


def test_create_persists_case_stage_diagram_one_transaction(db):
    people, assets, state = _create_args()
    meta = {"document_type": "khai_nhan", "ngay_lap_ho_so": "2026-09-26",
            "noi_niem_yet": "xã Yên Sở", "ghi_chu": "Hồ sơ nháp"}

    data = _create(db, people, assets, state, meta=meta)

    assert data["schema_version"] == SCHEMA_VERSION
    assert data["backend_mode"] == "real"
    assert data["created"] is True
    case = data["case"]
    assert case["case_type"] == "inheritance"
    assert case["document_type"] == "khai_nhan"
    assert case["status"] == "draft"
    assert case["locked"] is False
    assert case["revision"] == 1
    assert case["ngay_lap_ho_so"] == "2026-09-26"
    assert case["noi_niem_yet"] == "xã Yên Sở"
    assert case["ghi_chu"] == "Hồ sơ nháp"

    wire_people = data["stage"]["people"]
    assert [p["ho_ten"] for p in wire_people] == [
        "Nguyễn Văn An", "Trần Thị Bình"]
    assert all(isinstance(p["entity_id"], int) for p in wire_people)
    owner_entity = wire_people[0]["entity_id"]
    spouse_entity = wire_people[1]["entity_id"]
    assert data["stage"]["owner_row_id"] == people[0]["row_id"]

    db_case = db.get(InheritanceCase, case["id"])
    assert db_case is not None
    assert db_case.nguoi_chet_id == owner_entity     # owner -> người chết
    assert db_case.tai_san_id == \
        data["stage"]["assets"][0]["entity_id"]      # vị trí 1 = primary
    assert db_case.ngay_lap_ho_so == date(2026, 9, 26)
    assert db_case.loai_van_ban == "khai_nhan"
    assert db_case.noi_niem_yet == "xã Yên Sở"
    assert db_case.ghi_chu == "Hồ sơ nháp"
    assert db_case.workspace_idempotency_key

    # Diagram persist + render_model + participant sync
    assert data["diagram"]["state"]["version"] == 3
    assert data["diagram"]["state"]["domain"] == "inheritance"
    assert data["diagram"]["domain"] == "inheritance"
    assert data["diagram"]["render_model"] is not None
    assert data["diagram"]["render_model"]["status"] in (
        "incomplete", "complete")
    parts = db.query(InheritanceParticipant).filter_by(
        ho_so_id=case["id"]).all()
    assert [p.customer_id for p in parts] == [spouse_entity]
    assert parts[0].vai_tro == "Vợ/Chồng"

    # workspace_get đọc lại đúng snapshot vừa tạo (row_id/entity_id giữ
    # nguyên; field date emit dạng canonical YYYY-MM-DD)
    again = _service(db).get(case["id"])
    assert again["case"]["revision"] == 1
    assert again["stage"]["owner_row_id"] == people[0]["row_id"]
    assert [(p["row_id"], p["entity_id"], p["ho_ten"])
            for p in again["stage"]["people"]] == [
        (p["row_id"], p["entity_id"], p["ho_ten"]) for p in wire_people]


def test_noi_niem_yet_saved_value_flows_into_word_export(db, session_factory,
                                                       tmp_path):
    """Chuỗi đầy đủ theo yêu cầu Owner (NAIA-12): người dùng NHẬP nơi niêm yết
    -> LƯU xuống InheritanceCase.noi_niem_yet -> TẢI LẠI hồ sơ từ DB -> XUẤT
    Word phải in đúng giá trị đó; không mượn địa chỉ tài sản làm fallback.
    """
    from docx import Document

    from services import word_engine

    people, assets, state = _create_args()
    typed = "Trụ sở UBND xã Đại An, huyện Vụ Bản"
    data = _create(db, people, assets, state, meta={
        "document_type": "khai_nhan",
        "noi_niem_yet": typed,
    })

    # Tải lại bằng session MỚI — chứng minh giá trị đã ghi DB, không chỉ RAM.
    fresh = session_factory()
    try:
        db_case = fresh.get(InheritanceCase, data["case"]["id"])
        assert db_case is not None
        assert db_case.noi_niem_yet == typed

        template = tmp_path / "mau_niem_yet.docx"
        doc = Document()
        doc.add_paragraph("Niêm yết tại: [Nơi niêm yết]")
        doc.save(str(template))

        out = Document(str(template))
        mapping = word_engine.build_template_mapping(db_case)
        word_engine.replace_in_doc(out, mapping)
        assert word_engine.find_unresolved_placeholders(
            out, template_ref=template) == []
        out_path = tmp_path / "out.docx"
        out.save(str(out_path))

        exported = Document(str(out_path))
        assert exported.paragraphs[0].text == \
            f"Niêm yết tại: {typed}"
        # Phản chứng: địa chỉ tài sản khác hẳn, không bị lẫn vào.
        assert "Thửa 99" not in exported.paragraphs[0].text
    finally:
        fresh.close()


def test_noi_niem_yet_missing_stays_empty_no_property_fallback(db,
                                                             session_factory):
    """Hồ sơ chưa nhập nơi niêm yết -> token rỗng (dữ liệu thiếu), KHÔNG được
    đổ địa chỉ tài sản vào để vụ việc "thiếu" trông như "đủ"."""
    from services import word_engine

    people, assets, state = _create_args()
    data = _create(db, people, assets, state, meta={
        "document_type": "khai_nhan"})  # không truyền noi_niem_yet

    fresh = session_factory()
    try:
        db_case = fresh.get(InheritanceCase, data["case"]["id"])
        assert db_case is not None
        assert db_case.noi_niem_yet is None

        mapping = word_engine.build_template_mapping(db_case)
        assert mapping["[Nơi niêm yết]"] == ""
        assert mapping["[Niêm Yết]"] == ""
        assert mapping["[Địa chỉ đất]"] == "Thửa 99, xã Yên Sở"  # nguồn riêng, không fallback
    finally:
        fresh.close()


def test_create_without_diagram_seeds_owner(db):
    """§13.6: diagram absent → server seed node 'owner' personId =
    owner_row_id + ownPositions đủ vị trí; render_model null."""
    people, assets, _state = _create_args()
    data = _create(db, people, assets, None)

    assert data["created"] is True
    st = data["diagram"]["state"]
    owner = next((n for n in st["nodes"] if n["id"] == "owner"), None)
    assert owner is not None
    assert owner["personId"] == people[0]["row_id"]
    assert owner["ownPositions"] == [1]
    assert data["diagram"]["render_model"] is None


def test_create_two_party_seeds_canonical_slots(db):
    """two_party create: stage cấm owner_row_id; diagram absent → seed
    canonical p1..p30; case_type/document_type đúng."""
    people = [_person_row(ho_ten="Bên A", ngay_chet=None),
              _person_row(ho_ten="Bên B", gioi_tinh="Nữ",
                          ngay_chet=None)]
    meta = {"case_type": "two_party", "document_type": "chuyen_nhuong"}
    data = _service(db).create(
        str(uuid.uuid4()), meta, _stage(people, [_asset_row()]), None)

    assert data["created"] is True
    assert data["case"]["case_type"] == "two_party"
    assert data["case"]["document_type"] == "chuyen_nhuong"
    assert "owner_row_id" not in data["stage"]
    st = data["diagram"]["state"]
    assert st["domain"] == "two_party"
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    assert data["capabilities"]["word_export"] is True


def test_create_idempotent_replay_same_key(db):
    people, assets, state = _create_args()
    key = str(uuid.uuid4())

    first = _create(db, people, assets, state, key=key)
    second = _create(db, people, assets, state, key=key)

    assert first["created"] is True
    assert second["created"] is False
    assert second["case"]["id"] == first["case"]["id"]
    assert db.query(InheritanceCase).count() == 1

    # key khác = nháp khác → case mới (không suy giống-nhau-nội-dung)
    third = _create(db, people, assets, state, key=str(uuid.uuid4()))
    assert third["created"] is True
    assert third["case"]["id"] != first["case"]["id"]
    assert db.query(InheritanceCase).count() == 2


def test_create_requires_uuid4_idempotency_key(db):
    people, assets, state = _create_args()
    for bad in (None, "not-a-uuid", 42, str(uuid.uuid1())):
        with pytest.raises(WorkspaceError) as exc:
            _create(db, people, assets, state, key=bad)
        assert exc.value.code == "validation_error", bad
    assert db.query(InheritanceCase).count() == 0


def test_create_case_meta_validation(db):
    people, assets, state = _create_args()
    for bad_meta in (None, [], {"document_type": "khac"},
                     {"document_type": None}, {"bogus": 1},
                     {"document_type": "khai_nhan",
                      "ngay_lap_ho_so": "2026"},
                     {"document_type": "khai_nhan", "ghi_chu": "  "},
                     {"document_type": "khai_nhan", "noi_niem_yet": 5}):
        with pytest.raises(WorkspaceError) as exc:
            _create(db, people, assets, state, meta=bad_meta)
        assert exc.value.code == "validation_error", bad_meta
    assert db.query(InheritanceCase).count() == 0


def test_create_missing_owner_maps_workspace_owner_required(db):
    """§13.6: pointer thiếu/null/không thuộc stage → owner_required.
    (v2: owner KHÔNG suy từ node — stage.owner_row_id là SOT.)"""
    people, assets, state = _create_args()
    for bad_owner in (None, str(uuid.uuid4()), "not-uuid"):
        with pytest.raises(WorkspaceError) as exc:
            _create(db, people, assets, state, owner_row_id=bad_owner)
        assert exc.value.code == "workspace_owner_required", bad_owner
    assert db.query(InheritanceCase).count() == 0


def test_create_owner_node_mismatch_rejected(db):
    """§13.6: node 'owner' personId khác stage.owner_row_id →
    diagram_owner_mismatch — server không tự sửa nháp client."""
    people, assets, _state = _create_args()
    state = _v3_state([
        _node("owner", people[1]["row_id"], spouse="spouse", own=[1]),
        _node("spouse", None, spouse="owner", receive=[1]),
    ])
    with pytest.raises(WorkspaceError) as exc:
        _create(db, people, assets, state)
    assert exc.value.code == "diagram_owner_mismatch"
    assert exc.value.details["owner_row_id"] == people[0]["row_id"]
    assert db.query(InheritanceCase).count() == 0


def test_create_stage_rules_apply(db):
    people, assets, state = _create_args()

    # entity_id phải null — hồ sơ mới tạo entity mới
    bad_people = [dict(p) for p in people]
    bad_people[0]["entity_id"] = 5
    with pytest.raises(WorkspaceError) as exc:
        _create(db, bad_people, assets, state)
    assert exc.value.code == "stage_validation_error"
    assert any(e["field"] == "entity_id"
               for e in exc.value.details["field_errors"])

    # assets rỗng → required; people rỗng → owner_required trước (owner
    # pointer validation đi trước field errors §13.6)
    with pytest.raises(WorkspaceError) as exc:
        _create(db, people, [], state)
    assert exc.value.code == "stage_validation_error"
    with pytest.raises(WorkspaceError) as exc:
        _create(db, [], assets, state)
    assert exc.value.code == "workspace_owner_required"

    # field sai → rollback trọn vẹn, không ghi nửa vời
    bad_name = [dict(people[0], ho_ten="  "), people[1]]
    with pytest.raises(WorkspaceError) as exc:
        _create(db, bad_name, assets, state)
    assert exc.value.code == "stage_validation_error"
    assert db.query(InheritanceCase).count() == 0
    assert db.query(Customer).count() == 0
    assert db.query(Property).count() == 0


def test_create_is_primary_rejected(db):
    """is_primary trên asset row = trường lạ → validation_error (§13.3)."""
    people, assets, state = _create_args()
    assets[0]["is_primary"] = True
    with pytest.raises(WorkspaceError) as exc:
        _create(db, people, assets, state)
    assert exc.value.code == "validation_error"
    assert db.query(InheritanceCase).count() == 0


def test_create_domain_mismatch_rejected(db):
    """state.domain hợp lệ nhưng khác case.case_type →
    diagram_domain_mismatch (§13.5)."""
    people, assets, _state = _create_args()
    tp_state = {"version": 3, "domain": "two_party",
                "nodes": [{"id": f"p{i}", "personId": None,
                           "hidden": False, "deleted": False}
                          for i in range(1, 31)]}
    with pytest.raises(WorkspaceError) as exc:
        _create(db, people, assets, tp_state)
    assert exc.value.code == "diagram_domain_mismatch"
    assert exc.value.details["expected"] == "inheritance"


def test_create_diagram_invalid_and_outside_stage(db):
    people, assets, _state = _create_args()

    dangling = _v3_state([
        _node("owner", people[0]["row_id"], parents=("ghost",),
              own=[1])])
    with pytest.raises(WorkspaceError) as exc:
        _create(db, people, assets, dangling)
    assert exc.value.code == "diagram_invalid_state"

    outside = _v3_state([
        _node("owner", people[0]["row_id"], own=[1]),
        _node("child_1", str(uuid.uuid4()), parents=("owner",),
              receive=[1])])
    with pytest.raises(WorkspaceError) as exc:
        _create(db, people, assets, outside)
    assert exc.value.code == "diagram_reference_outside_stage"
    assert db.query(InheritanceCase).count() == 0


def test_update_meta_keeps_committed_stage_and_word_snapshot(db):
    from services.word_engine import build_template_mapping
    people, assets, state = _create_args()
    created = _create(db, people, assets, state)
    service = _service(db)
    case = db.get(InheritanceCase, created["case"]["id"])
    original = json.loads(case.case_state_json)
    result = service.update_meta(case.id, created["case"]["revision"],
                                 {"noi_niem_yet": "xã Snapshot Mới"})
    fresh = json.loads(case.case_state_json)
    assert fresh["stage"] == original["stage"]
    assert fresh["assets"] == original["assets"]
    assert fresh["diagram"] == original["diagram"]
    assert fresh["case"]["noiniemyet"] == "xã Snapshot Mới"
    assert build_template_mapping(case)["[Nơi niêm yết]"] == "xã Snapshot Mới"
    service.update_meta(case.id, result["revision"], {"noi_niem_yet": None})
    assert build_template_mapping(case)["[Nơi niêm yết]"] == ""
    with pytest.raises(WorkspaceError) as exc:
        service.update_meta(case.id, result["revision"],
                            {"noi_niem_yet": "stale"})
    assert exc.value.code == "workspace_conflict"
    assert build_template_mapping(case)["[Nơi niêm yết]"] == ""


# ------------------------------------------- độ đầy đủ ngày (Owner 15/10/2026)


def test_year_only_dates_survive_save_reopen_edit_unrelated_and_recommit(db):
    """`2010` chỉ năm phải phân biệt được với `01/01/2010` qua lưu → mở lại
    → sửa trường khác → Cập nhật; snapshot không bị đệm thành `01/01`."""
    case, deceased, prop, _heirs = _make_case(db)
    people = [
        _person_row(entity_id=deceased.id, ho_ten="Nguyễn Văn Năm",
                    ngay_sinh="2010", ngay_chet="2015", ngay_cap="2018",
                    so_giay_to="001234567890", dia_chi="Số 1 phố Huế"),
        _person_row(ho_ten="Trần Thị Đầy Đủ", gioi_tinh="Nữ",
                    ngay_sinh="2010-01-01", so_giay_to="001080012345"),
    ]
    assets = [_asset_row(entity_id=prop.id, so_serial="DD123456")]
    committed = _commit(db, case.id, 1, people, assets)
    assert [p["ngay_sinh"] for p in _workspace_people(committed)] == [
        "2010", "2010-01-01"]

    got = _service(db).get(case.id)
    people_out = _workspace_people(got)
    assert [p["ngay_sinh"] for p in people_out] == ["2010", "2010-01-01"]
    assert people_out[0]["ngay_chet"] == "2015"
    assert people_out[0]["ngay_cap"] == "2018"

    # Mở lại → sửa trường KHÁC → Cập nhật (đường người dùng).
    stage = got["stage"]
    stage["people"][0]["dia_chi"] = "Số 2 phố Huế"
    again = _commit(db, case.id, got["case"]["revision"],
                    stage["people"], stage["assets"])
    assert [p["ngay_sinh"] for p in _workspace_people(again)] == [
        "2010", "2010-01-01"]

    snapshot = json.loads(db.get(InheritanceCase, case.id).case_state_json)
    assert [row["ngay_sinh"] for row in snapshot["stage"]] == [
        "2010", "2010-01-01"]
    assert [row["ngay_chet"] for row in snapshot["stage"]] == ["2015", None]
    assert [row["ngay_cap"] for row in snapshot["stage"]] == ["2018", None]
    reopened = _service(db).get(case.id)
    assert [p["ngay_sinh"] for p in _workspace_people(reopened)] == [
        "2010", "2010-01-01"]


def test_date_key_presence_blocks_master_fallback_but_missing_key_uses_master(db):
    """Key ngày có mặt (kể cả `null`) → chặn fallback master; key vắng
    (snapshot cũ) → master, ghi nhận dạng đầy đủ (không đoán năm riêng)."""
    case, deceased, prop, _heirs = _make_case(db)
    people = [
        _person_row(entity_id=deceased.id, ho_ten="Nguyễn Văn Null",
                    ngay_sinh="1980-02-03", so_giay_to="001234567890"),
    ]
    assets = [_asset_row(entity_id=prop.id, so_serial="DD123456")]
    _commit(db, case.id, 1, people, assets)

    # Master Jan-1 — giới hạn biểu diễn của cột Date; dùng để thử fallback.
    master = db.get(Customer, deceased.id)
    master.ngay_sinh = date(1980, 1, 1)
    master.ngay_chet = date(1990, 1, 1)
    db.commit()

    payload = json.loads(db.get(InheritanceCase, case.id).case_state_json)
    row = payload["stage"][0]
    row["ngay_sinh"] = None       # key có mặt, giá trị null → chặn master
    row.pop("ngay_chet")          # key vắng → fallback master
    stored = db.get(InheritanceCase, case.id)
    stored.case_state_json = json.dumps(payload, ensure_ascii=False)
    db.commit()

    person = _workspace_people(_service(db).get(case.id))[0]
    assert person["ngay_sinh"] is None
    assert person["ngay_chet"] == "1990-01-01"   # đầy đủ, không hạ thành "1990"
    # Word dùng cùng quyền key-presence: null → rỗng, không đọc master.
    from services.word_engine import build_template_mapping
    word_map = build_template_mapping(
        db.get(InheritanceCase, case.id), static=True)
    assert word_map["[Người 1 - Ngày sinh]"] == ""
    assert word_map["[ngaysinh1]"] == ""
    assert word_map["[ngaychet1]"] == "01/01/1990"


def test_migrate_on_read_keeps_year_only_snapshot_value(db):
    """Migrate-on-read ghi lại stage từ wire — giá trị năm riêng không bị
    phình thành `01/01` (đường `_persist_migrated`)."""
    case, deceased, prop, _heirs = _make_case(db)
    people = [
        _person_row(entity_id=deceased.id, ho_ten="Nguyễn Văn Năm",
                    ngay_sinh="2010", so_giay_to="001234567890",
                    dia_chi="Số 1 phố Huế"),
    ]
    assets = [_asset_row(entity_id=prop.id, so_serial="DD123456")]
    _commit(db, case.id, 1, people, assets)

    payload = json.loads(db.get(InheritanceCase, case.id).case_state_json)
    del payload["stage"][0]["row_id"]     # row_id thiếu → compose đánh dấu dirty
    stored = db.get(InheritanceCase, case.id)
    stored.case_state_json = json.dumps(payload, ensure_ascii=False)
    db.commit()

    _service(db).get(case.id)

    snapshot = json.loads(db.get(InheritanceCase, case.id).case_state_json)
    assert snapshot["stage"][0]["ngay_sinh"] == "2010"
    assert UUID4_RE.match(snapshot["stage"][0]["row_id"])


def test_saved_type_conversion_roundtrip_keeps_stage_and_resets_domain(db):
    case, *_ = _make_case(db, with_participant=True)
    before = _service(db).get(case.id)
    snapshot = json.loads(case.case_state_json)
    converted = _service(db).convert_type(case.id, before["case"]["revision"], {
        "case_type": "two_party", "document_type": "tang_cho",
        "confirm_diagram_reset": True})
    assert converted["case"]["document_type"] == "tang_cho"
    assert converted["stage"]["people"] == before["stage"]["people"]
    assert converted["stage"]["assets"] == before["stage"]["assets"]
    assert "owner_row_id" not in converted["stage"]
    assert len(converted["diagram"]["state"]["nodes"]) == 30
    assert all(n["personId"] is None for n in converted["diagram"]["state"]["nodes"])
    assert case.engine_state_json is None
    assert db.query(InheritanceParticipant).filter_by(ho_so_id=case.id).count() == 0
    saved = json.loads(case.case_state_json)
    assert saved["stage"] == snapshot["stage"]
    assert saved["assets"] == snapshot["assets"]
    owner = before["stage"]["people"][-1]["row_id"]
    restored = _service(db).convert_type(case.id, converted["case"]["revision"], {
        "case_type": "inheritance", "document_type": "thoa_thuan",
        "confirm_diagram_reset": True, "owner_row_id": owner})
    assert restored["stage"]["owner_row_id"] == owner
    assert restored["diagram"]["state"]["nodes"] == [{
        "id": "owner", "personId": owner, "parentSlotIds": [],
        "spouseSlotId": None, "ownPositions": [], "receivePositions": [],
        "hidden": False, "deleted": False}]
    db.expire_all()
    assert _service(db).get(case.id) == restored


@pytest.mark.parametrize("patch", [
    {"document_type": "khai_nhan"}, {"document_type": None},
    {"confirm_diagram_reset": False}, {"case_type": "inheritance"},
    {"owner_row_id": None}, {"unexpected": True},
])
def test_saved_type_conversion_invalid_leaves_snapshot_unchanged(db, patch):
    case, *_ = _make_case(db, with_participant=True)
    before = _service(db).get(case.id)
    raw = case.case_state_json
    request = {"case_type": "two_party", "document_type": "dat_coc",
               "confirm_diagram_reset": True, **patch}
    with pytest.raises(WorkspaceError):
        _service(db).convert_type(case.id, before["case"]["revision"], request)
    db.expire_all()
    assert case.case_state_json == raw
    assert _service(db).get(case.id) == before


def test_saved_type_conversion_failure_rolls_back_all_projections(db, monkeypatch):
    case, *_ = _make_case(db, with_participant=True)
    service = _service(db)
    before = service.get(case.id)
    raw = case.case_state_json
    def fail(*args, **kwargs):
        raise RuntimeError("injected response construction failure")
    monkeypatch.setattr(service, "get", fail)
    with pytest.raises(RuntimeError):
        service.convert_type(case.id, before["case"]["revision"], {
            "case_type": "two_party", "document_type": "cho_thue",
            "confirm_diagram_reset": True})
    db.expire_all()
    assert case.case_state_json == raw
    assert _service(db).get(case.id) == before


def test_saved_type_conversion_stale_and_locked_leave_case_usable(db):
    case, *_ = _make_case(db)
    before = _service(db).get(case.id)
    request = {"case_type": "two_party", "document_type": "cho_thue",
               "confirm_diagram_reset": True}
    with pytest.raises(WorkspaceError) as conflict:
        _service(db).convert_type(case.id, before["case"]["revision"] + 1, request)
    assert conflict.value.code == "workspace_conflict"
    case.trang_thai = "locked"
    db.commit()
    raw = case.case_state_json
    with pytest.raises(WorkspaceError) as locked:
        _service(db).convert_type(case.id, before["case"]["revision"], request)
    assert locked.value.code == "workspace_locked"
    assert case.case_state_json == raw

"""Tests for MIN-141 đợt 2 — cụm đất thành bản ghi DB (property_land_rows).

Phạm vi phủ sóng:
- migrate_property_land_rows: tạo bảng + backfill JSON, idempotent, bảo toàn
  thứ tự/vị trí trống, báo anomaly không cắt cụt, giữ nguyên bản gốc.
- commit_stage/create: ghi master + cụm đất + snapshot + revision trong một
  transaction; edit/xóa/reorder; key canonical + legacy; conflict → lỗi.
- workspace_get: bảng con là SOT khi đã có dòng, JSON là fallback; data
  warnings cho JSON lỗi/overflow/thời hạn lẻ mồ côi.
- word_engine: đọc snapshot đã commit của hồ sơ — hai hồ sơ dùng chung tài
  sản không ảnh hưởng nhau; thời hạn lẻ không được đắp vào cụm.

Dùng SQLite file tạm (tmp_path) — không bao giờ chạm notary.db thật.
"""
import json
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
    Property,
    PropertyLandRow,
)
from services import word_engine
from services.case_workspace import (
    CaseWorkspaceService,
    WorkspaceError,
)


# ---------------------------------------------------------------- fixtures


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'ws.db'}")
    database.Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine)
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def legacy_db(tmp_path):
    """File SQLite giả lập DB trước đợt 2: full schema ORM trừ bảng con
    property_land_rows (DROP sau create_all)."""
    db_path = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{db_path}")
    database.Base.metadata.create_all(engine)
    engine.dispose()
    con = sqlite3.connect(db_path)
    con.execute("DROP TABLE property_land_rows")
    con.commit()
    yield db_path, con
    con.close()


def _insert_property(con, land_rows_json=None, thoi_han=None,
                     serial="DD123456", dia_chi="addr"):
    cur = con.execute(
        "INSERT INTO properties (so_serial, dia_chi, land_rows_json, "
        "thoi_han) VALUES (?,?,?,?)",
        (serial, dia_chi, land_rows_json, thoi_han))
    con.commit()
    return cur.lastrowid


def _table_rows(con, property_id):
    return con.execute(
        "SELECT vitri, loaidat, dientich, thoihan FROM property_land_rows"
        " WHERE property_id=? ORDER BY vitri",
        (property_id,)).fetchall()


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
        "so_serial": "EE123456",
        "so_vao_so": "CS 99999",
        "so_thua_dat": "99",
        "so_to_ban_do": "12",
        "dia_chi": "Thửa 99, xã Yên Sở",
        "loai_so": "GCN QSDĐ",
        "hinh_thuc_su_dung": "Sử dụng riêng",
        "thoi_han": None,
        "nguon_goc": "Cấp đổi",
        "ngay_cap": "2005-09-30",
        "co_quan_cap": "UBND quận Hai Bà Trưng",
        "land_rows": [{"loai_dat": "ODT", "dien_tich": 85.5,
                       "thoi_han": "Lâu dài"}],
    }
    row.update(overrides)
    return row


def _node(nid, person_id=None, own=(), receive=()):
    return {"id": nid, "personId": person_id, "parentSlotIds": [],
            "spouseSlotId": None, "ownPositions": list(own),
            "receivePositions": list(receive), "hidden": False,
            "deleted": False}


def _v3_state(nodes, domain="inheritance"):
    return {"version": 3, "domain": domain, "nodes": nodes}


def _create_args():
    owner = _person_row(ho_ten="Nguyễn Văn An", ngay_sinh="1950",
                        ngay_chet="2011-05-15", so_giay_to="001234567890")
    spouse = _person_row(ho_ten="Trần Thị Bình", gioi_tinh="Nữ",
                         ngay_sinh="1955-03-02", so_giay_to="009876543210")
    state = _v3_state([
        _node("owner", owner["row_id"], own=[1]),
        _node("spouse", spouse["row_id"], receive=[1]),
    ])
    return [owner, spouse], [_asset_row()], state


def _create(db, people, assets, state, key=None):
    stage = {"owner_row_id": people[0]["row_id"],
             "people": people, "assets": assets}
    return CaseWorkspaceService(db).create(
        key or str(uuid.uuid4()), {"document_type": "khai_nhan"},
        stage, state)


def _commit(db, case_id, base_revision, people, assets):
    stage = {"owner_row_id": people[0]["row_id"],
             "people": people, "assets": assets}
    return CaseWorkspaceService(db).commit_stage(case_id, base_revision, stage)


def _payload_assets(db, case_id):
    payload = json.loads(
        db.get(InheritanceCase, case_id).case_state_json)
    return payload["assets"]


def _land_warning_codes(result):
    return {w["code"] for w in result.get("warnings", [])}


# --------------------------------------------------------- migration tests


def test_migration_creates_table_and_backfills_order_and_gaps(legacy_db):
    _, con = legacy_db
    pid = _insert_property(con, json.dumps([
        {"loai_dat": "ODT", "dien_tich": 80, "thoi_han": "Lâu dài"},
        {},                                            # vị trí trống giữa
        {"loai_dat": "CLN", "dien_tich": 120.5,
         "thoi_han": "Đến 2043-12-31"},
    ], ensure_ascii=False))
    report = database.migrate_property_land_rows(con)
    assert _table_rows(con, pid) == [
        (1, "ODT", 80.0, "Lâu dài"),
        (2, None, None, None),                          # vị trí trống giữ nguyên
        (3, "CLN", 120.5, "Đến 2043-12-31"),
    ]
    assert report["table_created"] is True
    assert report["backfilled"] == 1 and report["rows_inserted"] == 3
    assert report["anomalies"] == []
    # JSON gốc giữ nguyên — không DROP/ghi đè trong bước chuyển đổi
    assert con.execute(
        "SELECT land_rows_json FROM properties WHERE id=?",
        (pid,)).fetchone()[0] is not None


def test_migration_idempotent_no_duplicate_rows(legacy_db):
    _, con = legacy_db
    pid = _insert_property(con, json.dumps([
        {"loai_dat": "ODT", "dien_tich": 80, "thoi_han": "Lâu dài"},
        {"loai_dat": "CLN", "dien_tich": 90, "thoi_han": "50 năm"},
    ]))
    database.migrate_property_land_rows(con)
    report2 = database.migrate_property_land_rows(con)
    assert len(_table_rows(con, pid)) == 2
    assert report2["skipped_existing"] == 1
    assert report2["rows_inserted"] == 0
    assert report2["table_created"] is False


def test_migration_does_not_overwrite_rows_written_by_commit(legacy_db):
    """Backfill xong, commit ghi đè bảng con (JSON mirror giữ nguyên) →
    migration lần sau KHÔNG lấy JSON cũ đè lại — bảng con là SOT."""
    _, con = legacy_db
    pid = _insert_property(
        con, json.dumps([{"loai_dat": "STALE", "dien_tich": 1,
                          "thoi_han": "cũ"}]))
    database.migrate_property_land_rows(con)          # lần 1: tạo + backfill
    # commit workspace thay cụm bằng giá trị mới trên bảng con
    con.execute("DELETE FROM property_land_rows WHERE property_id=?",
                (pid,))
    con.execute(
        "INSERT INTO property_land_rows "
        "(property_id, vitri, loaidat, dientich, thoihan) "
        "VALUES (?,?,?,?,?)", (pid, 1, "ONT", 10.0, "Lâu dài"))
    con.commit()
    report = database.migrate_property_land_rows(con)  # lần 2: phải skip
    assert _table_rows(con, pid) == [(1, "ONT", 10.0, "Lâu dài")]
    assert report["skipped_existing"] == 1
    assert report["rows_inserted"] == 0


@pytest.mark.parametrize("json_text,code", [
    ("not-json{{{", "invalid_json"),
    ('"chuỗi không phải mảng"', "invalid_shape"),
    ('[{"loai_dat": "ODT"}, "không phải object"]', "invalid_row"),
    ('[{"loai_dat": "ODT", "dien_tich": "abc"}]', "invalid_dientich"),
    # MIN-141 đợt 2 fix: kiểu object/list/bool phải thành anomaly —
    # không để SQLite crash, không ép về NULL; số/chuỗi không hữu hạn
    # cũng bị chặn.
    ('[{"loai_dat": {"bad": "type"}, "dien_tich": 5}]', "invalid_field"),
    ('[{"loai_dat": ["ODT"]}]', "invalid_field"),
    ('[{"loaidat": "ODT", "thoihan": true}]', "invalid_field"),
    ('[{"dientich": true}]', "invalid_dientich"),
    ('[{"dientich": {"a": 1}}]', "invalid_dientich"),
    ('[{"dien_tich": 1e999}]', "invalid_dientich"),  # inf — không hữu hạn
])
def test_migration_bad_json_reported_and_preserved(legacy_db,
                                                   json_text, code):
    """JSON lỗi → báo anomaly + giữ nguyên bản gốc, không ghi/cắt cụt."""
    _, con = legacy_db
    pid = _insert_property(con, json_text)
    report = database.migrate_property_land_rows(con)
    assert _table_rows(con, pid) == []
    assert [a["code"] for a in report["anomalies"]] == [code]
    assert report["anomalies"][0]["property_id"] == pid
    # Bản gốc giữ nguyên để đối chiếu
    assert con.execute(
        "SELECT land_rows_json FROM properties WHERE id=?",
        (pid,)).fetchone()[0] == json_text


def test_migration_conflicting_keys_reported(legacy_db):
    """Key cũ + mới cùng mang giá trị mâu thuẫn → anomaly, không chọn ngầm."""
    _, con = legacy_db
    pid = _insert_property(con, json.dumps([
        {"loai_dat": "ODT", "loaidat": "CLN", "dien_tich": 80},
    ]))
    report = database.migrate_property_land_rows(con)
    assert _table_rows(con, pid) == []
    assert [a["code"] for a in report["anomalies"]] == ["conflict"]


def test_migration_accepts_canonical_keys_in_json(legacy_db):
    _, con = legacy_db
    pid = _insert_property(con, json.dumps([
        {"loaidat": "ONT", "dientich": 50, "thoihan": "Lâu dài"},
    ]))
    report = database.migrate_property_land_rows(con)
    assert _table_rows(con, pid) == [(1, "ONT", 50.0, "Lâu dài")]
    assert report["anomalies"] == []


def test_migration_over_limit_inserts_all_and_reports(legacy_db):
    """JSON >20 cụm: ghi đủ để không mất dữ liệu + báo over_limit."""
    _, con = legacy_db
    pid = _insert_property(con, json.dumps([
        {"loai_dat": f"Đất {i}", "dien_tich": i, "thoi_han": None}
        for i in range(1, 26)]))
    report = database.migrate_property_land_rows(con)
    assert len(_table_rows(con, pid)) == 25
    assert [a["code"] for a in report["anomalies"]] == ["over_limit"]


def test_migration_orphan_thoi_han_reported(legacy_db):
    """Thời hạn lẻ không trùng thoihan cụm nào → anomaly orphan_thoi_han;
    trùng một cụm → không báo. Giữ nguyên bản gốc cả hai trường hợp."""
    _, con = legacy_db
    orphan = _insert_property(
        con, land_rows_json=None, thoi_han="Lâu dài", serial="DD000001")
    matched = _insert_property(
        con, json.dumps([{"loai_dat": "ODT", "dien_tich": 80,
                          "thoi_han": "Lâu dài"}]),
        thoi_han="Lâu dài", serial="DD000002")
    report = database.migrate_property_land_rows(con)
    orphan_anomalies = [
        a for a in report["anomalies"]
        if a["code"] == "orphan_thoi_han"]
    assert [a["property_id"] for a in orphan_anomalies] == [orphan]
    assert not any(
        a["property_id"] == matched for a in report["anomalies"])


# ------------------------------------------------------- commit/persist


def test_create_persists_land_rows_to_child_table(db):
    people, assets, state = _create_args()
    data = _create(db, people, assets, state)
    prop_id = data["stage"]["assets"][0]["entity_id"]
    rows = db.query(PropertyLandRow).filter_by(
        property_id=prop_id).order_by(PropertyLandRow.vitri).all()
    assert [(r.vitri, r.loaidat, r.dientich, r.thoihan)
            for r in rows] == [(1, "ODT", 85.5, "Lâu dài")]
    # Mirror JSON vẫn được ghi theo key legacy cho đường đọc cũ
    prop = db.get(Property, prop_id)
    assert json.loads(prop.land_rows_json) == [
        {"loai_dat": "ODT", "dien_tich": 85.5, "thoi_han": "Lâu dài"}]


def test_commit_writes_land_rows_and_snapshot_in_one_tx(db):
    people, assets, state = _create_args()
    data = _create(db, people, assets, state)
    case_id = data["case"]["id"]
    prop_id = data["stage"]["assets"][0]["entity_id"]

    new_assets = [_asset_row(
        entity_id=prop_id,
        land_rows=[
            {"loai_dat": "CLN", "dien_tich": 90, "thoi_han": "50 năm"},
            {"loai_dat": None, "dien_tich": None, "thoi_han": None},
            {"loai_dat": "ODT", "dien_tich": 15.5, "thoi_han": "Lâu dài"},
        ])]
    out = _commit(db, case_id, 1, people, new_assets)

    rows = db.query(PropertyLandRow).filter_by(
        property_id=prop_id).order_by(PropertyLandRow.vitri).all()
    assert [(r.vitri, r.loaidat, r.dientich, r.thoihan) for r in rows] == [
        (1, "CLN", 90.0, "50 năm"),
        (2, None, None, None),                       # vị trí trống giữ nguyên
        (3, "ODT", 15.5, "Lâu dài"),
    ]
    # wire echo giữ key legacy để UI không hỏng
    assert out["stage"]["assets"][0]["land_rows"] == [
        {"loai_dat": "CLN", "dien_tich": 90.0, "thoi_han": "50 năm"},
        {"loai_dat": None, "dien_tich": None, "thoi_han": None},
        {"loai_dat": "ODT", "dien_tich": 15.5, "thoi_han": "Lâu dài"},
    ]
    # snapshot assets trong case_state_json mang cụm đất key canonical
    snap = _payload_assets(db, case_id)[0]
    assert snap["entity_id"] == prop_id
    assert snap["land_rows"] == [
        {"loaidat": "CLN", "dientich": 90.0, "thoihan": "50 năm"},
        {"loaidat": None, "dientich": None, "thoihan": None},
        {"loaidat": "ODT", "dientich": 15.5, "thoihan": "Lâu dài"},
    ]


def test_get_reloads_land_rows_from_child_table(db):
    """Mở lại bằng session mới: wire land_rows đọc từ bảng con."""
    people, assets, state = _create_args()
    data = _create(db, people, assets, state)
    prop_id = data["stage"]["assets"][0]["entity_id"]
    # JSON mirror giả lập lệch — bảng con phải thắng (SOT)
    db.get(Property, prop_id).land_rows_json = json.dumps(
        [{"loai_dat": "STALE", "dien_tich": 1, "thoi_han": "x"}])
    db.commit()
    result = CaseWorkspaceService(db).get(data["case"]["id"])
    assert result["stage"]["assets"][0]["land_rows"] == [
        {"loai_dat": "ODT", "dien_tich": 85.5, "thoi_han": "Lâu dài"}]


def test_get_falls_back_to_json_when_table_empty(db):
    """Tài sản chưa migrate (bảng trống, còn JSON) → wire đọc fallback."""
    prop = Property(
        so_serial="DD123456", dia_chi="addr",
        land_rows_json=json.dumps([
            {"loai_dat": "LUC", "dien_tich": 70, "thoi_han": "20 năm"}]))
    deceased = Customer(ho_ten="Người Chết", ngay_chet=date(2020, 1, 1))
    db.add_all([prop, deceased])
    db.flush()
    case = InheritanceCase(
        nguoi_chet_id=deceased.id, tai_san_id=prop.id,
        ngay_lap_ho_so=date(2026, 9, 1), loai_van_ban="khai_nhan",
        trang_thai="draft")
    db.add(case)
    db.flush()
    db.add(InheritanceCaseProperty(
        case_id=case.id, property_id=prop.id, is_primary=True))
    db.commit()
    result = CaseWorkspaceService(db).get(case.id)
    assert result["stage"]["assets"][0]["land_rows"] == [
        {"loai_dat": "LUC", "dien_tich": 70, "thoi_han": "20 năm"}]


def test_commit_land_rows_edit_delete_reorder(db):
    people, assets, state = _create_args()
    data = _create(db, people, assets, state)
    case_id = data["case"]["id"]
    prop_id = data["stage"]["assets"][0]["entity_id"]

    # reorder + sửa + xóa: [CLN-30] lên vị trí 1, ODT đổi 85.5→90, bỏ dòng 3
    new_assets = [_asset_row(
        entity_id=prop_id,
        land_rows=[
            {"loai_dat": "CLN", "dien_tich": 30, "thoi_han": "50 năm"},
            {"loai_dat": "ODT", "dien_tich": 90, "thoi_han": "Lâu dài"},
        ])]
    _commit(db, case_id, 1, people, new_assets)
    assert [(r.vitri, r.loaidat, r.dientich, r.thoihan) for r in
            db.query(PropertyLandRow).filter_by(property_id=prop_id)
            .order_by(PropertyLandRow.vitri)] == [
        (1, "CLN", 30.0, "50 năm"),
        (2, "ODT", 90.0, "Lâu dài"),
    ]

    # xóa hết cụm — bảng trống, mirror None
    _commit(db, case_id, 2, people,
            [_asset_row(entity_id=prop_id, land_rows=None)])
    assert db.query(PropertyLandRow).filter_by(property_id=prop_id).count() == 0
    assert db.get(Property, prop_id).land_rows_json is None


def test_commit_land_rows_canonical_keys_accepted(db):
    """Payload key mới loaidat/dientich/thoihan commit được, emit wire
    vẫn bộ legacy."""
    people, assets, state = _create_args()
    data = _create(db, people, assets, state)
    prop_id = data["stage"]["assets"][0]["entity_id"]
    out = _commit(db, data["case"]["id"], 1, people, [_asset_row(
        entity_id=prop_id,
        land_rows=[{"loaidat": "ONT", "dientich": 120,
                    "thoihan": "Đến 2043"}])])
    row = db.query(PropertyLandRow).filter_by(property_id=prop_id).one()
    assert (row.loaidat, row.dientich, row.thoihan) == ("ONT", 120.0, "Đến 2043")
    assert out["stage"]["assets"][0]["land_rows"] == [
        {"loai_dat": "ONT", "dien_tich": 120.0, "thoi_han": "Đến 2043"}]


def test_commit_land_rows_conflicting_keys_rejected(db):
    """Key cũ + mới mâu thuẫn → stage_validation_error 'conflict', không
    âm thầm chọn một."""
    people, assets, state = _create_args()
    data = _create(db, people, assets, state)
    prop_id = data["stage"]["assets"][0]["entity_id"]
    with pytest.raises(WorkspaceError) as exc:
        _commit(db, data["case"]["id"], 1, people, [_asset_row(
            entity_id=prop_id,
            land_rows=[{"loai_dat": "ODT", "loaidat": "CLN",
                        "dien_tich": 80}])])
    assert exc.value.code == "stage_validation_error"
    assert any(e["code"] == "conflict" and e["field"] == "land_rows"
               for e in exc.value.details["field_errors"])


def test_commit_land_row_limit(db):
    people, assets, state = _create_args()
    data = _create(db, people, assets, state)
    prop_id = data["stage"]["assets"][0]["entity_id"]
    with pytest.raises(WorkspaceError) as exc:
        _commit(db, data["case"]["id"], 1, people, [_asset_row(
            entity_id=prop_id,
            land_rows=[{"loai_dat": f"Đất {i}", "dien_tich": i,
                        "thoi_han": None} for i in range(21)])])
    assert exc.value.code == "stage_validation_error"
    assert any(e["code"] == "land_row_limit"
               for e in exc.value.details["field_errors"])


def test_invalid_land_row_rolls_back_everything(db):
    """Commit sai ở dòng thứ 2 → master + cụm đất + snapshot + revision
    của dòng 1 cũng không được ghi (một transaction)."""
    people, assets, state = _create_args()
    assets.append(_asset_row(so_serial="FF123456", land_rows=[
        {"loai_dat": "BHK", "dien_tich": 40, "thoi_han": "Lâu dài"}]))
    data = _create(db, people, assets, state)
    case_id = data["case"]["id"]
    prop1 = data["stage"]["assets"][0]["entity_id"]
    prop2 = data["stage"]["assets"][1]["entity_id"]
    before_payload = db.get(InheritanceCase, case_id).case_state_json

    bad_assets = [
        _asset_row(entity_id=prop1, land_rows=[
            {"loai_dat": "LUC", "dien_tich": 999, "thoi_han": "20 năm"}]),
        _asset_row(entity_id=prop2, land_rows=[
            {"loai_dat": "ODT", "dien_tich": "không-phải-số",
             "thoi_han": None}]),
    ]
    with pytest.raises(WorkspaceError) as exc:
        _commit(db, case_id, 1, people, bad_assets)
    assert exc.value.code == "stage_validation_error"

    case = db.get(InheritanceCase, case_id)
    assert case.workspace_revision == 1
    assert case.case_state_json == before_payload
    # Cụm đất cả hai tài sản giữ nguyên như lúc create — không nửa ghi
    assert [(r.vitri, r.loaidat) for r in db.query(PropertyLandRow)
            .filter_by(property_id=prop1)
            .order_by(PropertyLandRow.vitri)] == [(1, "ODT")]
    assert [(r.vitri, r.loaidat) for r in db.query(PropertyLandRow)
            .filter_by(property_id=prop2)
            .order_by(PropertyLandRow.vitri)] == [(1, "BHK")]
    assert db.get(Property, prop1).so_serial == "EE123456"


def test_commit_land_rows_3x20_roundtrip(db):
    """Lưu rồi mở lại đủ 3 tài sản × 20 cụm (AC2)."""
    people, _assets, state = _create_args()
    assets = [_asset_row(so_serial=f"EE00000{n}") for n in range(1, 4)]
    data = _create(db, people, assets, state)
    case_id = data["case"]["id"]
    prop_ids = [a["entity_id"] for a in data["stage"]["assets"]]
    new_assets = []
    for n, prop_id in enumerate(prop_ids, start=1):
        new_assets.append(_asset_row(
            entity_id=prop_id, so_serial=f"EE00000{n}",
            land_rows=[{"loai_dat": f"Đất {n}.{m}",
                        "dien_tich": n * 100 + m,
                        "thoi_han": f"TH{n}.{m}"} for m in range(1, 21)]))
    _commit(db, case_id, 1, people, new_assets)
    db.expire_all()
    result = CaseWorkspaceService(db).get(case_id)
    assert len(result["stage"]["assets"]) == 3
    for n, prop_id in enumerate(prop_ids, start=1):
        rows = db.query(PropertyLandRow).filter_by(
            property_id=prop_id).order_by(PropertyLandRow.vitri).all()
        assert len(rows) == 20
        assert (rows[0].vitri, rows[0].loaidat, rows[0].dientich,
                rows[0].thoihan) == (1, f"Đất {n}.1",
                                     float(n * 100 + 1), f"TH{n}.1")
        assert rows[-1].vitri == 20
    wire0 = result["stage"]["assets"][0]["land_rows"]
    assert len(wire0) == 20 and wire0[0]["loai_dat"] == "Đất 1.1"
    assert len(_payload_assets(db, case_id)[0]["land_rows"]) == 20


def test_two_cases_sharing_property_word_uses_own_snapshot(db):
    """AC5: hai hồ sơ dùng chung một master property — Word của mỗi hồ sơ
    đọc đúng snapshot đã commit của mình, không bị commit hồ sơ kia kéo."""
    people, assets, state = _create_args()
    data_a = _create(db, people, assets, state)
    case_a, prop_id = data_a["case"]["id"], \
        data_a["stage"]["assets"][0]["entity_id"]

    # Hồ sơ B tạo với tài sản khác, rồi commit trỏ sang cùng master prop
    people_b = [_person_row(ho_ten="Lê Văn C", ngay_chet="2020-01-01",
                            so_giay_to="111222333444"),
                _person_row(ho_ten="Phạm Thị D", gioi_tinh="Nữ",
                            so_giay_to="555666777888")]
    state_b = _v3_state([
        _node("owner", people_b[0]["row_id"], own=[1]),
        _node("spouse", people_b[1]["row_id"], receive=[1])])
    data_b = _create(db, people_b,
                     [_asset_row(so_serial="FF123456",
                                 land_rows=[{"loai_dat": "BHK",
                                             "dien_tich": 10,
                                             "thoi_han": "x"}])],
                     state_b)
    case_b = data_b["case"]["id"]
    _commit(db, case_b, 1, people_b, [_asset_row(
        entity_id=prop_id,
        land_rows=[{"loai_dat": "CLN", "dien_tich": 90,
                    "thoi_han": "Đến 2043"}])])

    # Master bị commit của B ghi đè — đúng semantics master dùng chung
    row = db.query(PropertyLandRow).filter_by(property_id=prop_id).one()
    assert row.loaidat == "CLN"

    # Nhưng Word của A đọc snapshot A, Word của B đọc snapshot B
    map_a = word_engine.build_template_mapping(db.get(InheritanceCase, case_a))
    map_b = word_engine.build_template_mapping(db.get(InheritanceCase, case_b))
    assert map_a["[loaidat11]"] == "ODT"
    assert map_a["[dientich11]"] == "85.5"
    assert map_a["[thoihan11]"] == "Lâu dài"
    assert map_b["[loaidat11]"] == "CLN"
    assert map_b["[dientich11]"] == "90"
    assert map_b["[thoihan11]"] == "Đến 2043"


def test_standalone_thoi_han_not_grafted_into_word_cluster(db):
    """AC4: thời hạn lẻ không tự đắp vào cụm khi xuất Word."""
    people, assets, state = _create_args()
    assets[0]["thoi_han"] = "Lâu dài lẻ"          # field lẻ của asset_row
    assets[0]["land_rows"] = [{"loai_dat": "ODT", "dien_tich": 80,
                               "thoi_han": None}]  # cụm không thời hạn
    data = _create(db, people, assets, state)
    mapping = word_engine.build_template_mapping(
        db.get(InheritanceCase, data["case"]["id"]))
    assert mapping["[thoihan11]"] == ""           # không đắp lẻ vào cụm 1
    # trường lẻ vẫn render ở placeholder của chính nó
    assert mapping["[Tài sản 1 - Thời hạn]"] == "Lâu dài lẻ"


def test_get_warns_orphan_and_invalid_and_overflow(db):
    """workspace_get báo data warning cho 3 loại legacy land data."""
    deceased = Customer(ho_ten="Người Chết", ngay_chet=date(2020, 1, 1))
    orphan = Property(so_serial="DD000001", dia_chi="a",
                      thoi_han="Lâu dài")
    broken = Property(so_serial="DD000002", dia_chi="b",
                      land_rows_json="not-json{{{")
    overflow = Property(so_serial="DD000003", dia_chi="c",
                        land_rows_json=json.dumps([
                            {"loai_dat": "X"} for _ in range(25)]))
    ok = Property(so_serial="DD000004", dia_chi="d",
                  land_rows_json=json.dumps([{"loai_dat": "ODT",
                                              "dien_tich": 10,
                                              "thoi_han": "Lâu dài"}]),
                  thoi_han="Lâu dài")
    db.add_all([deceased, orphan, broken, overflow, ok])
    db.flush()
    case = InheritanceCase(
        nguoi_chet_id=deceased.id, tai_san_id=orphan.id,
        ngay_lap_ho_so=date(2026, 9, 1), loai_van_ban="khai_nhan",
        trang_thai="draft")
    db.add(case)
    db.flush()
    for prop in (orphan, broken, overflow, ok):
        db.add(InheritanceCaseProperty(
            case_id=case.id, property_id=prop.id,
            is_primary=prop is orphan))
    db.commit()
    # >3 asset → cần payload thủ công (commit_stage chặn asset_limit)
    payload = {"schemaVersion": 3, "case_type": "inheritance",
               "stage": [{"id": str(deceased.id), "row_id": str(uuid.uuid4()),
                          "ho_ten": deceased.ho_ten}],
               "assets": [{"id": str(p.id), "row_id": str(uuid.uuid4()),
                           "is_primary": i == 0}
                          for i, p in enumerate((orphan, broken, overflow, ok))],
               "diagram": {}}
    case.case_state_json = json.dumps(payload)
    db.commit()

    codes = _land_warning_codes(CaseWorkspaceService(db).get(case.id))
    assert "stage.orphan_thoi_han" in codes          # orphan: thoi_han lẻ
    assert "stage.legacy_land_rows_invalid" in codes  # broken JSON
    assert "stage.legacy_land_rows_overflow" in codes # 25 cụm
    assert "stage.legacy_asset_overflow" in codes     # 4 asset > 3
    # tài sản khớp thoihan với thời hạn lẻ → không báo orphan cho nó
    orphan_msgs = [w["message"] for w in
                   CaseWorkspaceService(db).get(case.id)["warnings"]
                   if w["code"] == "stage.orphan_thoi_han"]
    assert len(orphan_msgs) == 1


def test_reopen_commit_noop_preserves_own_snapshot(db):
    """MIN-141 đợt 2 fix: mở lại Stage hồ sơ A (đọc snapshot A, không kéo
    master mà hồ sơ B vừa đổi) rồi commit nguyên trạng → snapshot A giữ
    nguyên giá trị, Word vẫn đúng."""
    people, assets, state = _create_args()
    data_a = _create(db, people, assets, state)
    case_a = data_a["case"]["id"]
    prop_id = data_a["stage"]["assets"][0]["entity_id"]

    # Hồ sơ B trỏ cùng master property và đổi cụm đất thành CLN
    people_b = [_person_row(ho_ten="Lê Văn C", ngay_chet="2020-01-01",
                            so_giay_to="111222333444")]
    state_b = _v3_state([_node("owner", people_b[0]["row_id"], own=[1])])
    data_b = _create(db, people_b,
                     [_asset_row(so_serial="FF123456")], state_b)
    _commit(db, data_b["case"]["id"], 1, people_b, [_asset_row(
        entity_id=prop_id, so_serial="EE123456",
        land_rows=[{"loai_dat": "CLN", "dien_tich": 90,
                    "thoi_han": "Đến 2043"}])])
    assert db.query(PropertyLandRow).filter_by(
        property_id=prop_id).one().loaidat == "CLN"

    service = CaseWorkspaceService(db)
    reopened = service.get(case_a)
    # Stage A đọc snapshot A — ODT, không phải CLN của master
    assert reopened["stage"]["assets"][0]["land_rows"][0][
        "loai_dat"] == "ODT"
    # Commit nguyên trạng payload vừa mở → snapshot A không đổi
    result = service.commit_stage(
        case_a, reopened["case"]["revision"],
        reopened["stage"])
    assert result["revision"] == 2
    snap = _payload_assets(db, case_a)[0]
    assert snap["land_rows"][0]["loaidat"] == "ODT"
    assert word_engine.build_template_mapping(
        db.get(InheritanceCase, case_a))["[loaidat11]"] == "ODT"


def test_pointer_snapshot_falls_back_to_master_rows(db):
    """Snapshot legacy chỉ có con trỏ {id,row_id,is_primary} → vẫn đọc
    master (bảng con), không đọc nhầm snapshot rỗng."""
    people, _assets, state = _create_args()
    prop = Property(so_serial="DD777777", dia_chi="Thửa cũ")
    prop.land_rows = [PropertyLandRow(
        vitri=1, loaidat="BHK", dientich=33.0, thoihan="50 năm")]
    db.add(prop)
    db.flush()
    data_a = _create(db, people, [_asset_row()], state)
    case = db.get(InheritanceCase, data_a["case"]["id"])
    payload = json.loads(case.case_state_json)
    payload["assets"] = [{"id": str(prop.id),
                          "row_id": str(uuid.uuid4()),
                          "is_primary": True}]
    case.case_state_json = json.dumps(payload)
    db.commit()
    result = CaseWorkspaceService(db).get(case.id)
    assert result["stage"]["assets"][0]["land_rows"] == [
        {"loai_dat": "BHK", "dien_tich": 33.0, "thoi_han": "50 năm"}]


def test_inline_create_writes_land_rows_and_mirror_atomically(db):
    """Route tạo nhanh ghi master + bảng con + mirror trong một commit —
    query property_land_rows ngay sau route thấy đủ cụm, không chờ
    migration (MIN-141 đợt 2 fix)."""
    from routers.properties import inline_create
    rows = [{"loai_dat": "ODT", "dien_tich": 80, "thoi_han": "Lâu dài"},
            {"loai_dat": "CLN", "dien_tich": 50.5, "thoi_han": None}]
    resp = inline_create(
        so_serial="RT000001", so_vao_so=None, so_thua_dat=None,
        so_to_ban_do=None, dia_chi="Thửa 1, xã A", loai_so=None,
        hinh_thuc_su_dung=None, nguon_goc=None, ngay_cap=None,
        co_quan_cap=None,
        land_rows=json.dumps(rows, ensure_ascii=False), db=db)
    payload = json.loads(resp.body)
    assert payload["ok"] is True
    prop = db.get(Property, payload["property"]["id"])
    assert [(r.vitri, r.loaidat, r.dientich, r.thoihan)
            for r in prop.land_rows] == [
        (1, "ODT", 80.0, "Lâu dài"), (2, "CLN", 50.5, None)]
    # Mirror cùng một transaction, shape legacy như migration ghi
    assert json.loads(prop.land_rows_json) == [
        {"loai_dat": "ODT", "dien_tich": 80, "thoi_han": "Lâu dài"},
        {"loai_dat": "CLN", "dien_tich": 50.5, "thoi_han": None}]
    assert prop.dien_tich == 130.5            # tổng diện tích các cụm
    assert prop.thoi_han is None             # MIN-141: không còn ghi
                                             # giá trị lẻ — chỉ cụm
    # Key canonical cũng nhận được (dual-key như Stage)
    resp2 = inline_create(
        so_serial="RT000002", so_vao_so=None, so_thua_dat=None,
        so_to_ban_do=None, dia_chi="Thửa 2", loai_so=None,
        hinh_thuc_su_dung=None, nguon_goc=None, ngay_cap=None,
        co_quan_cap=None,
        land_rows=json.dumps([{"loaidat": "ONT", "dientich": 10,
                               "thoihan": "x"}]), db=db)
    assert json.loads(resp2.body)["ok"] is True
    prop2 = db.get(Property, json.loads(resp2.body)["property"]["id"])
    assert [(r.vitri, r.loaidat) for r in prop2.land_rows] == [(1, "ONT")]


@pytest.mark.parametrize("rows_json", [
    json.dumps([{"loai_dat": {"bad": 1}}]),        # object — sai kiểu
    json.dumps([{"thoi_han": True}]),              # bool — sai kiểu
    json.dumps([{"dien_tich": "abc"}]),            # không phải số
    json.dumps({"loai_dat": "ODT"}),               # không phải mảng
    "not-json{{{",                                  # JSON hỏng
    json.dumps([{"loai_dat": "ODT", "loaidat": "CLN"}]),  # mâu thuẫn
    json.dumps([{"loai_dat": "X"}] * 21),          # > MAX_LAND_ROWS
])
def test_inline_create_rejects_malformed_land_rows(db, rows_json):
    """Land_rows sai → 400 + errors['land_rows'], không ghi master/bảng
    con nửa chừng — route không đưa giá trị thô/sai kiểu vào DB."""
    from routers.properties import inline_create
    resp = inline_create(
        so_serial="RT000009", so_vao_so=None, so_thua_dat=None,
        so_to_ban_do=None, dia_chi="Thửa bad", loai_so=None,
        hinh_thuc_su_dung=None, nguon_goc=None, ngay_cap=None,
        co_quan_cap=None, land_rows=rows_json, db=db)
    assert resp.status_code == 400
    assert "land_rows" in json.loads(resp.body)["errors"]
    assert db.query(Property).filter_by(
        so_serial="RT000009").first() is None


def test_main_and_sidecar_wire_land_row_migration():
    """Wiring guard: web main.py và sidecar _ensure_db đều gọi đủ
    migrate_property_land_rows + migrate_zalo_exchange_schema (AC6)."""
    root = Path(__file__).resolve().parent.parent
    main_src = (root / "main.py").read_text(encoding="utf-8")
    assert "migrate_property_land_rows()" in main_src
    assert "migrate_zalo_exchange_schema()" in main_src
    adapter = root.parent / "shell" / "sidecar" / "notary_adapter.py"
    if adapter.exists():
        src = adapter.read_text(encoding="utf-8")
        assert "migrate_property_land_rows()" in src
        assert "migrate_zalo_exchange_schema()" in src

"""Nen Storage B (issue 13, phase 2 vong 1 — commit 2).

Chi kiem DDL/model (bang case-owned, identity nullable, FK cascade/restrict)
va doc/ghi ORM truc tiep theo fixture tong hop. Service/router/Word thuoc
commit sau, khong gia lap o day.

Dap an trong `fixtures/issue13_storage_b.json` lay tu thiet ke
`_bmad-output/tmp/issue13-b-phase2-design-20261022.md` Phan 7 — viet doc lap
voi code, khong lay output service/parser lam dap an.
"""
import json
import re
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import Date as SADate
from sqlalchemy import create_engine, delete, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import database
from models import (
    CaseAssetLandRow,
    CaseAssetRow,
    CasePersonRow,
    Customer,
    InheritanceCase,
    Property,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "issue13_storage_b.json"
UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


# ---------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def dataset():
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture()
def engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'storage_b.db'}")
    database.enable_sqlite_foreign_keys(eng)
    database.Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


# ---------------------------------------------------------------- helpers


def _case_spec(dataset, alias):
    matches = [case for case in dataset["cases"] if case["alias"] == alias]
    assert len(matches) == 1, f"fixture phai co dung mot ca {alias}"
    return matches[0]


def _prototype(dataset, section, alias, override=None):
    data = dict(dataset[section][alias])
    data.pop("alias", None)
    data.update(override or {})
    return data


def _column_kwargs(model, data):
    columns = set(model.__table__.columns.keys())
    unknown = set(data) - columns
    assert not unknown, f"field la trong prototype {model.__name__}: {sorted(unknown)}"
    return {key: value for key, value in data.items() if key in columns}


def _identity_customer(db, data):
    """Identity toi thieu (chi ten + so); thieu mot neo thi khong tao."""
    name, number = data.get("ho_ten"), data.get("so_giay_to")
    if not name or not number:
        return None
    customer = Customer(ho_ten=name, so_giay_to=number)
    db.add(customer)
    return customer


def _identity_property(db, data, cache):
    """Identity theo serial NGUYEN VAN; serial rong/whitespace = thieu neo."""
    serial = data.get("so_serial") or ""
    if not serial.strip():
        return None
    if serial not in cache:
        prop = Property(so_serial=serial)
        db.add(prop)
        cache[serial] = prop
    return cache[serial]


def _build_person_row(db, dataset, alias, case_id, vitri, override=None):
    data = _prototype(dataset, "people_prototypes", alias, override)
    row = CasePersonRow(
        case_id=case_id, vitri=vitri,
        **_column_kwargs(CasePersonRow, data))
    row.identity = _identity_customer(db, data)
    return row


def _build_asset_row(db, dataset, alias, case_id, vitri, override=None, cache=None):
    data = _prototype(dataset, "asset_prototypes", alias, override)
    land_rows = data.pop("land_rows", None)
    data.pop("land_rows_present", None)
    row = CaseAssetRow(
        case_id=case_id, vitri=vitri,
        land_rows_present=land_rows is not None,
        **_column_kwargs(CaseAssetRow, data))
    row.identity = _identity_property(db, data, {} if cache is None else cache)
    for land_vitri, land in enumerate(land_rows or [], start=1):
        row.land_rows.append(CaseAssetLandRow(
            vitri=land_vitri,
            loaidat=land.get("loaidat"),
            dientich=land.get("dientich"),
            thoihan=land.get("thoihan"),
        ))
    return row


def _seed_stage(db, dataset, alias, *, reverse_insert=True):
    """Seed dong case-owned theo fixture; chen nguoc de chung minh order_by."""
    spec = _case_spec(dataset, alias)
    meta = spec.get("metadata") or {}
    case = InheritanceCase(
        trang_thai=spec["status_mong_doi"],
        loai_van_ban=meta.get("loai_van_ban") or "khai_nhan",
        ngay_lap_ho_so=(
            date.fromisoformat(meta["ngay_lap_ho_so"])
            if meta.get("ngay_lap_ho_so") else None),
    )
    db.add(case)
    db.flush()

    rows = []
    for vitri, entry in enumerate(spec["people"], start=1):
        rows.append(_build_person_row(
            db, dataset, entry["prototype"], case.id, vitri,
            entry.get("override")))
    cache = {}
    for vitri, entry in enumerate(spec["assets"], start=1):
        rows.append(_build_asset_row(
            db, dataset, entry["prototype"], case.id, vitri,
            entry.get("override"), cache))

    db.add_all(list(reversed(rows)) if reverse_insert else rows)
    db.commit()
    return case


def _land_view(row):
    return [
        {"vitri": land.vitri, "loaidat": land.loaidat,
         "dientich": land.dientich, "thoihan": land.thoihan}
        for land in row.land_rows
    ]


# ---------------------------------------------------------------- schema


def test_fresh_schema_has_storage_b_tables_and_columns(engine):
    insp = inspect(engine)
    assert {"case_person_rows", "case_asset_rows", "case_asset_land_rows"} <= set(
        insp.get_table_names())

    person = {col["name"]: col for col in insp.get_columns("case_person_rows")}
    assert set(person) == {
        "row_id", "case_id", "customer_id", "vitri", "ho_ten", "gioi_tinh",
        "ngay_sinh", "ngay_chet", "so_giay_to", "ngay_cap", "noi_cap",
        "dia_chi", "place_of_origin", "loai_giay_to", "loai_dia_chi"}
    assert person["row_id"]["primary_key"]
    assert person["case_id"]["nullable"] is False
    assert person["customer_id"]["nullable"] is True
    assert person["vitri"]["nullable"] is False
    assert person["ho_ten"]["nullable"] is True
    assert str(person["ngay_sinh"]["type"]).upper().startswith("VARCHAR")

    asset = {col["name"]: col for col in insp.get_columns("case_asset_rows")}
    assert set(asset) == {
        "row_id", "case_id", "property_id", "vitri", "so_serial", "so_vao_so",
        "so_thua_dat", "so_to_ban_do", "dia_chi", "loai_so",
        "hinh_thuc_su_dung", "thoi_han", "nguon_goc", "ngay_cap",
        "co_quan_cap", "land_rows_present"}
    assert asset["property_id"]["nullable"] is True
    assert asset["so_serial"]["nullable"] is False
    assert asset["land_rows_present"]["nullable"] is False
    assert isinstance(asset["ngay_cap"]["type"], SADate)

    land = {col["name"]: col for col in insp.get_columns("case_asset_land_rows")}
    assert set(land) == {
        "id", "case_asset_row_id", "vitri", "loaidat", "dientich", "thoihan"}
    assert land["case_asset_row_id"]["nullable"] is False
    assert land["vitri"]["nullable"] is False

    person_fks = {
        tuple(fk["constrained_columns"]): fk
        for fk in insp.get_foreign_keys("case_person_rows")}
    assert person_fks[("case_id",)]["referred_table"] == "inheritance_cases"
    assert person_fks[("case_id",)]["options"]["ondelete"] == "CASCADE"
    assert person_fks[("customer_id",)]["referred_table"] == "customers"
    assert person_fks[("customer_id",)]["options"]["ondelete"] == "RESTRICT"

    asset_fks = {
        tuple(fk["constrained_columns"]): fk
        for fk in insp.get_foreign_keys("case_asset_rows")}
    assert asset_fks[("case_id",)]["options"]["ondelete"] == "CASCADE"
    assert asset_fks[("property_id",)]["options"]["ondelete"] == "RESTRICT"

    land_fks = {
        tuple(fk["constrained_columns"]): fk
        for fk in insp.get_foreign_keys("case_asset_land_rows")}
    assert land_fks[("case_asset_row_id",)]["referred_table"] == "case_asset_rows"
    assert land_fks[("case_asset_row_id",)]["options"]["ondelete"] == "CASCADE"

    person_indexes = {tuple(ix["column_names"]): ix
                      for ix in insp.get_indexes("case_person_rows")}
    assert ("case_id", "vitri") in person_indexes
    assert ("customer_id",) in person_indexes
    person_uniques = {tuple(uq["column_names"])
                      for uq in insp.get_unique_constraints("case_person_rows")}
    assert ("case_id", "row_id") in person_uniques

    asset_indexes = {tuple(ix["column_names"]): ix
                     for ix in insp.get_indexes("case_asset_rows")}
    assert ("case_id", "vitri") in asset_indexes
    assert ("property_id",) in asset_indexes
    assert asset_indexes[("property_id",)]["unique"] == 0
    asset_uniques = {tuple(uq["column_names"])
                     for uq in insp.get_unique_constraints("case_asset_rows")}
    assert ("case_id", "row_id") in asset_uniques

    land_uniques = {tuple(uq["column_names"])
                    for uq in insp.get_unique_constraints("case_asset_land_rows")}
    assert ("case_asset_row_id", "vitri") in land_uniques

    checks = {
        table: {ck["name"] for ck in insp.get_check_constraints(table)}
        for table in ("case_person_rows", "case_asset_rows",
                      "case_asset_land_rows")}
    assert "ck_case_person_row_vitri" in checks["case_person_rows"]
    assert "ck_case_asset_row_vitri" in checks["case_asset_rows"]
    assert "ck_case_asset_land_row_vitri" in checks["case_asset_land_rows"]

    case_cols = {col["name"]: col for col in insp.get_columns("inheritance_cases")}
    assert case_cols["nguoi_chet_id"]["nullable"] is True
    assert case_cols["tai_san_id"]["nullable"] is True
    assert case_cols["ngay_lap_ho_so"]["nullable"] is True
    assert "workspace_creation_hash" in case_cols
    assert str(case_cols["workspace_creation_hash"]["type"]).upper().startswith(
        "VARCHAR(64)")
    case_indexes = {tuple(ix["column_names"]): ix
                    for ix in insp.get_indexes("inheritance_cases")}
    assert case_indexes[("workspace_idempotency_key",)]["unique"] == 1

    link_cols = {col["name"]: col
                 for col in insp.get_columns("inheritance_case_properties")}
    assert link_cols["property_id"]["nullable"] is True
    assert link_cols["case_asset_row_id"]["nullable"] is True

    participant_cols = {col["name"]: col
                        for col in insp.get_columns("inheritance_participants")}
    assert participant_cols["customer_id"]["nullable"] is True
    assert participant_cols["parent_customer_id"]["nullable"] is True
    assert participant_cols["case_person_row_id"]["nullable"] is True
    assert participant_cols["parent_case_person_row_id"]["nullable"] is True

    customer_cols = {col["name"]: col for col in insp.get_columns("customers")}
    assert customer_cols["name_anchor"]["nullable"] is True
    assert customer_cols["document_anchor"]["nullable"] is True
    customer_indexes = {tuple(ix["column_names"]): ix
                        for ix in insp.get_indexes("customers")}
    assert customer_indexes[("name_anchor", "document_anchor")]["unique"] == 0

    property_cols = {col["name"]: col for col in insp.get_columns("properties")}
    assert property_cols["dia_chi"]["nullable"] is True
    property_indexes = {tuple(ix["column_names"]): ix
                        for ix in insp.get_indexes("properties")}
    assert property_indexes[("so_serial",)]["unique"] == 0


# ---------------------------------------------------------------- F1 rows


def test_f1_rows_roundtrip_keep_vitri_order_and_blank_land_row(db, dataset):
    case = _seed_stage(db, dataset, "F1")
    db.expire_all()
    loaded = db.get(InheritanceCase, case.id)
    expected = _case_spec(dataset, "F1")["expected"]

    assert [row.vitri for row in loaded.person_rows] == list(
        range(1, expected["so_person_rows"] + 1))
    assert [row.ho_ten for row in loaded.person_rows] == [
        "Nguyễn Đăng An", "Trần Thị Bình", "Nguyễn Văn Con"]
    assert loaded.person_rows[0].ngay_sinh == "1950"
    assert loaded.person_rows[1].dia_chi == "Khu Giả Lập B"
    assert len({row.customer_id for row in loaded.person_rows}) == 3
    assert None not in {row.customer_id for row in loaded.person_rows}

    assert [row.vitri for row in loaded.asset_rows] == [1]
    assert len(loaded.asset_rows) == expected["so_asset_rows"]
    asset_row = loaded.asset_rows[0]
    assert asset_row.land_rows_present is True
    assert asset_row.property_id is not None
    assert _land_view(asset_row) == expected["land_rows_theo_asset"]["F1:T101"]
    assert _land_view(asset_row)[1] == {
        "vitri": 2, "loaidat": None, "dientich": None, "thoihan": None}

    # Cung fixture F1 nhung thao tac lai tren DB da co: khong insert trung UUID.
    assert db.query(CasePersonRow).count() == 3
    assert db.query(CaseAssetLandRow).count() == 3


def test_land_rows_present_distinguishes_null_from_empty_list(db, dataset):
    case = InheritanceCase(trang_thai="draft")
    db.add(case)
    db.flush()
    null_row = _build_asset_row(db, dataset, "T203", case.id, 1)
    empty_row = _build_asset_row(db, dataset, "T204", case.id, 2)
    db.add_all([null_row, empty_row])
    db.commit()
    db.expire_all()

    loaded = db.get(InheritanceCase, case.id)
    by_id = {row.row_id: row for row in loaded.asset_rows}
    null_loaded = by_id[dataset["asset_prototypes"]["T203"]["row_id"]]
    empty_loaded = by_id[dataset["asset_prototypes"]["T204"]["row_id"]]

    assert null_loaded.land_rows_present is False
    assert null_loaded.land_rows == []
    assert empty_loaded.land_rows_present is True
    assert empty_loaded.land_rows == []
    assert [row.vitri for row in loaded.asset_rows] == [1, 2]


# ---------------------------------------------------------------- FK


def test_deleting_case_cascades_rows_and_land_rows(db, dataset):
    case = _seed_stage(db, dataset, "F1")
    db.expire_all()
    loaded = db.get(InheritanceCase, case.id)
    asset_ids = [row.row_id for row in loaded.asset_rows]
    assert asset_ids

    db.execute(delete(InheritanceCase).where(InheritanceCase.id == case.id))
    db.commit()

    assert db.query(CasePersonRow).filter(
        CasePersonRow.case_id == case.id).count() == 0
    assert db.query(CaseAssetRow).filter(
        CaseAssetRow.case_id == case.id).count() == 0
    assert db.query(CaseAssetLandRow).filter(
        CaseAssetLandRow.case_asset_row_id.in_(asset_ids)).count() == 0


def test_identity_delete_is_restricted_while_case_rows_reference(db, dataset):
    case = _seed_stage(db, dataset, "F1")
    db.expire_all()
    loaded = db.get(InheritanceCase, case.id)
    customer_id = loaded.person_rows[0].customer_id
    property_id = loaded.asset_rows[0].property_id
    assert customer_id is not None and property_id is not None

    with pytest.raises(IntegrityError):
        db.execute(delete(Customer).where(Customer.id == customer_id))
    db.rollback()

    with pytest.raises(IntegrityError):
        db.execute(delete(Property).where(Property.id == property_id))
    db.rollback()

    assert db.get(Customer, customer_id) is not None
    assert db.get(Property, property_id) is not None


# ---------------------------------------------------------------- F5


def test_same_serial_asset_rows_keep_independent_land_groups(db, dataset):
    case = _seed_stage(db, dataset, "F5")
    db.expire_all()
    loaded = db.get(InheritanceCase, case.id)
    expected = _case_spec(dataset, "F5")["expected"]

    assert [row.vitri for row in loaded.asset_rows] == [1, 2]
    first, second = loaded.asset_rows
    assert first.property_id is not None
    assert first.property_id == second.property_id
    assert first.row_id != second.row_id
    assert (first.so_thua_dat, second.so_thua_dat) == ("11", "22")
    assert _land_view(first) == expected["land_rows_theo_asset"]["F5:T101"]
    assert _land_view(second) == expected["land_rows_theo_asset"]["F5:T202"]

    second.land_rows[0].dientich = 251
    db.commit()
    db.expire_all()
    loaded = db.get(InheritanceCase, case.id)
    first, second = loaded.asset_rows
    assert _land_view(first) == expected["land_rows_theo_asset"]["F5:T101"]
    assert _land_view(second) == [
        {"vitri": 1, "loaidat": "LUC", "dientich": 251.0, "thoihan": "2060"}]
    assert [row.vitri for row in loaded.asset_rows] == [1, 2]


# ---------------------------------------------------------------- fixture


def test_fixture_uuids_are_canonical_v4(dataset):
    row_ids = [
        proto["row_id"]
        for section in ("people_prototypes", "asset_prototypes")
        for proto in dataset[section].values()
    ]
    assert len(row_ids) == 10  # P101-103/111/301 + T101-205
    for row_id in row_ids:
        assert UUID4_RE.match(row_id), row_id
        assert str(uuid.UUID(row_id)) == row_id
        assert uuid.UUID(row_id).version == 4

    found = list(_iter_uuid_strings(dataset))
    assert len(found) == len(set(found))
    assert set(row_ids) <= set(found)
    assert all(uuid.UUID(value).version == 4 for value in found)


def _iter_uuid_strings(node):
    if isinstance(node, dict):
        for value in node.values():
            yield from _iter_uuid_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _iter_uuid_strings(value)
    elif isinstance(node, str) and UUID4_RE.match(node):
        yield node

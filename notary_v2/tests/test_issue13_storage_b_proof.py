"""Proof hành vi Storage B bằng fixture tổng hợp (issue 13, vòng 1).

Dựng dữ kiện bằng `CaseWorkspaceService` (create/commit_stage/save_case/get)
từ `fixtures/issue13_storage_b.json`; không chép dữ kiện vào test và không
lấy output service làm đáp án. Đáp án đọc từ `expected` của fixture.

Mapping ca fixture ↔ hành vi:
- P1 (hai Hồ sơ chung một Tài sản): F6A/F6B — cùng property identity,
  nhưng đất/dữ kiện đọc theo dòng của từng Hồ sơ; sửa A không đổi B;
  `materialize_case_state(B)` không lẫn dữ kiện A.
- P2 (hai Hồ sơ chung một Người): F6A/F6B — cùng customer identity,
  khác dữ kiện dòng; reopen giữ nguyên; sửa A không đổi B.
- Cùng serial nguyên văn, khác thửa: F5 (hai asset row, cùng property id,
  đất độc lập theo parent+vitri).
- Serial khác -> identity khác: F7 bước 5 (`serial_variants`).
- Hồ sơ done mở/sửa giữ done: F1 (Save mới) + F4 (Cập nhật rồi Save lại).

F2 (hai bên), F3 và các bước nháp khác của F7 không nằm trong phạm vi
P1/P2/F4/F5 của lượt proof này; đã có test nền ở
`test_issue13_storage_foundation.py` và `test_workspace_save_case.py`.
"""
import json
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database
from models import Customer, InheritanceCase
from services import case_rows
from services.case_workspace import CaseWorkspaceService

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "issue13_storage_b.json"


# ---------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def dataset():
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'storage_b_proof.db'}")
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


def _stage(spec, dataset):
    """Stage wire từ danh sách prototype/override của fixture."""
    people = [_proto(dataset, "people_prototypes", entry["prototype"],
                     entry.get("override"))
              for entry in spec["people"]]
    assets = [_proto(dataset, "asset_prototypes", entry["prototype"],
                     entry.get("override"))
              for entry in spec["assets"]]
    stage = {"people": people, "assets": assets}
    if spec["case_type"] == "inheritance":
        owner_alias = spec["diagram"].get("owner_row_id")
        owner_row_id = None
        if owner_alias:
            owner_row_id = next(
                row["row_id"] for entry, row in zip(spec["people"], people)
                if entry["prototype"] == owner_alias)
        stage = {"owner_row_id": owner_row_id, **stage}
    return stage


def _state(spec, dataset):
    """Diagram v3 từ `diagram` của fixture (domain Thừa kế)."""
    assert spec["case_type"] == "inheritance"
    diagram = spec["diagram"]
    nodes = []
    by_alias = {}
    for entry in spec["people"]:
        alias = entry["prototype"]
        node = {
            "id": alias,
            "personId": dataset["people_prototypes"][alias]["row_id"],
            "parentSlotIds": [],
            "spouseSlotId": None,
            "ownPositions": list(diagram.get("ownPositions", {}).get(alias, [])),
            "receivePositions": list(
                diagram.get("receivePositions", {}).get(alias, [])),
            "hidden": False,
            "deleted": False,
        }
        nodes.append(node)
        by_alias[alias] = node
    for relation in diagram.get("relations", []):
        source = by_alias[relation["from"]]
        target = by_alias[relation["to"]]
        if relation["kind"] == "spouse":
            source["spouseSlotId"] = target["id"]
            target["spouseSlotId"] = source["id"]
        elif relation["kind"] == "parent_child":
            target["parentSlotIds"].append(source["id"])
    return {"version": 3, "domain": "inheritance", "nodes": nodes}


def _save_new(db, dataset, spec):
    return CaseWorkspaceService(db).save_case(
        case_id=None, base_revision=None,
        idempotency_key=str(uuid.uuid4()),
        case_meta=_meta(spec), stage=_stage(spec, dataset),
        state=_state(spec, dataset))


def _land_wire(asset):
    return [{"loaidat": row["loai_dat"], "dientich": row["dien_tich"],
             "thoihan": row["thoi_han"]}
            for row in asset["land_rows"]]


def _expected_land(dataset, case_alias, asset_alias):
    expected = _case_spec(dataset, case_alias)["expected"]["land_rows_theo_asset"]
    return [{key: item[key] for key in ("loaidat", "dientich", "thoihan")}
            for item in expected[asset_alias]]


def _person(stage, dataset, prototype):
    row_id = dataset["people_prototypes"][prototype]["row_id"]
    return next(row for row in stage["people"] if row["row_id"] == row_id)


def _asset(stage, dataset, prototype):
    row_id = dataset["asset_prototypes"][prototype]["row_id"]
    return next(row for row in stage["assets"] if row["row_id"] == row_id)


def _reopen(factory, case_id):
    session = factory()
    try:
        return CaseWorkspaceService(session).get(case_id), session
    except Exception:
        session.close()
        raise


# ---------------------------------------------------------------- P1


def test_p1_shared_asset_rows_keep_own_land_data_and_word_view(
        dataset, db, session_factory):
    """F6A/F6B: cùng serial -> cùng property identity, đất theo Hồ sơ."""
    a = _save_new(db, dataset, _case_spec(dataset, "F6A"))
    b = _save_new(db, dataset, _case_spec(dataset, "F6B"))
    a_asset = _asset(a["stage"], dataset, "T101")
    b_asset = _asset(b["stage"], dataset, "T205")

    serial = dataset["asset_prototypes"]["T101"]["so_serial"]
    assert a_asset["entity_id"] is not None
    assert a_asset["entity_id"] == b_asset["entity_id"]
    assert a_asset["so_serial"] == b_asset["so_serial"] == serial

    expected_t101 = _expected_land(dataset, "F5", "F5:T101")
    assert _land_wire(a_asset) == expected_t101
    assert b_asset["land_rows"] == []

    # Sửa đất của A qua commit_stage: B phải giữ nguyên.
    stage = CaseWorkspaceService(db).get(a["case"]["id"])["stage"]
    stage["assets"][0]["land_rows"][0]["dien_tich"] = 150
    changed = CaseWorkspaceService(db).commit_stage(
        a["case"]["id"], a["case"]["revision"], stage)
    assert changed["revision"] == 2
    assert CaseWorkspaceService(db).get(a["case"]["id"])["case"]["status"] \
        == "done"

    expected_changed = [dict(expected_t101[0], dientich=150.0)] + expected_t101[1:]
    reopened_a, session_a = _reopen(session_factory, a["case"]["id"])
    try:
        assert _land_wire(reopened_a["stage"]["assets"][0]) == expected_changed
        assert reopened_a["stage"]["assets"][0]["entity_id"] == \
            a_asset["entity_id"]
    finally:
        session_a.close()

    reopened_b, session_b = _reopen(session_factory, b["case"]["id"])
    try:
        assert reopened_b["stage"]["assets"][0]["land_rows"] == []
        assert reopened_b["stage"]["assets"][0]["entity_id"] == \
            a_asset["entity_id"]
    finally:
        session_b.close()

    # Word materialize của B chỉ thấy dòng B; không lẫn đất/địa chỉ A.
    session_b = session_factory()
    try:
        case_b = session_b.get(InheritanceCase, b["case"]["id"])
        view = case_rows.materialize_case_state(case_b)
        assert view["assets"][0]["land_rows"] == []
        assert view["assets"][0]["so_serial"] == serial
        leaked = [dataset["asset_prototypes"]["T101"]["dia_chi"],
                  dataset["people_prototypes"]["P101"]["dia_chi"]] + [
            land["loaidat"] for land in
            dataset["asset_prototypes"]["T101"]["land_rows"]
            if land["loaidat"]]
        payload = json.dumps(view, ensure_ascii=False)
        for token in leaked:
            assert token not in payload
    finally:
        session_b.close()


# ---------------------------------------------------------------- P2


def test_p2_shared_person_identity_keeps_per_case_rows_after_reopen(
        dataset, db, session_factory):
    """F6A/F6B: cùng neo tên+số -> cùng customer_id, dữ kiện dòng riêng."""
    a = _save_new(db, dataset, _case_spec(dataset, "F6A"))
    b = _save_new(db, dataset, _case_spec(dataset, "F6B"))
    a_person = _person(a["stage"], dataset, "P101")
    b_person = _person(b["stage"], dataset, "P111")
    proto_a = dataset["people_prototypes"]["P101"]
    proto_b = dataset["people_prototypes"]["P111"]

    assert a_person["entity_id"] is not None
    assert a_person["entity_id"] == b_person["entity_id"]
    assert a_person["row_id"] != b_person["row_id"]

    assert a_person["ho_ten"] == proto_a["ho_ten"]
    assert a_person["dia_chi"] == proto_a["dia_chi"]
    assert a_person["ngay_cap"] == proto_a["ngay_cap"]
    assert b_person["ho_ten"] == proto_b["ho_ten"]
    assert b_person["dia_chi"] == proto_b["dia_chi"] is None
    assert b_person["ngay_cap"] == proto_b["ngay_cap"]

    # Reopen phiên mới: dữ kiện dòng giữ nguyên theo từng Hồ sơ.
    reopened_a, session_a = _reopen(session_factory, a["case"]["id"])
    try:
        row = _person(reopened_a["stage"], dataset, "P101")
        assert row["entity_id"] == a_person["entity_id"]
        assert (row["dia_chi"], row["ngay_cap"]) == (
            proto_a["dia_chi"], proto_a["ngay_cap"])
    finally:
        session_a.close()

    reopened_b, session_b = _reopen(session_factory, b["case"]["id"])
    try:
        row = _person(reopened_b["stage"], dataset, "P111")
        assert row["entity_id"] == b_person["entity_id"]
        assert (row["dia_chi"], row["ngay_cap"]) == (
            proto_b["dia_chi"], proto_b["ngay_cap"])
    finally:
        session_b.close()

    # Sửa địa chỉ ở A không đổi B và không update Customer master.
    stage = CaseWorkspaceService(db).get(a["case"]["id"])["stage"]
    _person(stage, dataset, "P101")["dia_chi"] = "Khu Giả Lập A2"
    CaseWorkspaceService(db).commit_stage(
        a["case"]["id"], a["case"]["revision"], stage)

    reopened_b, session_b = _reopen(session_factory, b["case"]["id"])
    try:
        row = _person(reopened_b["stage"], dataset, "P111")
        assert row["dia_chi"] == proto_b["dia_chi"]
        assert row["ngay_cap"] == proto_b["ngay_cap"]
        customer = session_b.get(Customer, row["entity_id"])
        assert customer.dia_chi is None
        assert customer.ngay_cap is None
    finally:
        session_b.close()


# ----------------------------------------- cùng serial khác thửa (F5)


def test_same_serial_different_parcel_share_property_identity(
        dataset, db):
    """F5 (= nhãn 'F4' trong yêu cầu): hai dòng, một property id."""
    saved = _save_new(db, dataset, _case_spec(dataset, "F5"))
    first = _asset(saved["stage"], dataset, "T101")
    second = _asset(saved["stage"], dataset, "T202")

    assert first["row_id"] != second["row_id"]
    assert first["entity_id"] is not None
    assert first["entity_id"] == second["entity_id"]
    assert (first["so_thua_dat"], second["so_thua_dat"]) == (
        dataset["asset_prototypes"]["T101"]["so_thua_dat"],
        dataset["asset_prototypes"]["T202"]["so_thua_dat"])
    assert _land_wire(first) == _expected_land(dataset, "F5", "F5:T101")
    assert _land_wire(second) == _expected_land(dataset, "F5", "F5:T202")

    stage = CaseWorkspaceService(db).get(saved["case"]["id"])["stage"]
    step = _case_spec(dataset, "F5")["expected"]["steps"][0]
    assert step["asset"] == "T202" and step["vitri"] == 1
    target = next(row for row in stage["assets"]
                  if row["row_id"] == second["row_id"])
    target["land_rows"][0]["dien_tich"] = step["dientich_moi"]
    result = CaseWorkspaceService(db).commit_stage(
        saved["case"]["id"], saved["case"]["revision"], stage)
    assert result["revision"] == 2
    assert CaseWorkspaceService(db).get(saved["case"]["id"])["case"]["status"] \
        == "done"

    reopened = CaseWorkspaceService(db).get(saved["case"]["id"])
    new_first = _asset(reopened["stage"], dataset, "T101")
    new_second = _asset(reopened["stage"], dataset, "T202")
    assert _land_wire(new_first) == _expected_land(dataset, "F5", "F5:T101")
    expected_second = _expected_land(dataset, "F5", "F5:T202")
    assert _land_wire(new_second) == [
        dict(expected_second[0], dientich=float(step["dientich_moi"]))]
    assert new_first["entity_id"] == new_second["entity_id"] == \
        first["entity_id"]
    assert [row["row_id"] for row in reopened["stage"]["assets"]] == [
        first["row_id"], second["row_id"]]


# ------------------------------- serial khác -> identity khác (F7 bước 5)


def test_serial_variants_do_not_share_identity(dataset, db):
    """F7 bước 5: serial khác nguyên văn không match, giữ nguyên văn."""
    variants = next(
        step for step in _case_spec(dataset, "F7")["expected"]["steps"]
        if step["action"] == "serial_bien_the")["serial_variants"]
    assert len(variants) >= 2

    identities = []
    for variant in variants:
        person = _proto(dataset, "people_prototypes", "P101")
        person["row_id"] = str(uuid.uuid4())
        asset = _proto(dataset, "asset_prototypes", "T203")
        asset["row_id"] = str(uuid.uuid4())
        asset["so_serial"] = variant
        stage = {"owner_row_id": person["row_id"],
                 "people": [person], "assets": [asset]}
        created = CaseWorkspaceService(db).create(
            str(uuid.uuid4()),
            {"case_type": "inheritance", "document_type": "khai_nhan",
             "ngay_lap_ho_so": None},
            stage, None)
        row = CaseWorkspaceService(db).get(
            created["case"]["id"])["stage"]["assets"][0]
        assert row["so_serial"] == variant
        assert row["entity_id"] is not None
        identities.append(row["entity_id"])

    assert len(set(identities)) == len(variants)


# --------------------------------------- done mở/sửa giữ done (F1 + F4)


def test_done_case_edit_and_resave_stay_done(dataset, db):
    """F4 trên nền F1: Cập nhật rev2 giữ done, Save lại sạch rev3 done."""
    f1 = _case_spec(dataset, "F1")
    saved = _save_new(db, dataset, f1)
    case_id = saved["case"]["id"]
    f1_expected = f1["expected"]
    assert saved["case"]["status"] == f1_expected["status"] == "done"
    assert saved["case"]["revision"] == f1_expected["revision"] == 1
    assert len(saved["stage"]["people"]) == f1_expected["so_person_rows"]
    assert len(saved["stage"]["assets"]) == f1_expected["so_asset_rows"]
    assert len(_asset(saved["stage"], dataset, "T101")["land_rows"]) == \
        f1_expected["so_land_rows"]
    assert _land_wire(_asset(saved["stage"], dataset, "T101")) == \
        _expected_land(dataset, "F1", "F1:T101")
    assert saved["case"]["chudat"] == f1_expected["chudat"]
    identity_before = _person(saved["stage"], dataset, "P102")["entity_id"]

    f4 = _case_spec(dataset, "F4")
    step_update = f4["expected"]["steps"][0]
    assert step_update["action"] == "cap_nhat"
    assert step_update["expected"]["status"] == "done"
    assert step_update["expected"]["revision"] == 2

    updated = CaseWorkspaceService(db).commit_stage(
        case_id, 1, _stage(f4, dataset))
    assert updated["revision"] == 2
    assert CaseWorkspaceService(db).get(case_id)["case"]["status"] == "done"
    address_b2 = step_update["override"]["P102"]["dia_chi"]
    assert _person(updated["stage"], dataset, "P102")["dia_chi"] == address_b2
    assert _person(updated["stage"], dataset, "P102")["entity_id"] == identity_before

    # Word đọc bản vừa Cập nhật, trước lần Save lại.
    case = db.get(InheritanceCase, case_id)
    db.refresh(case)
    view = case_rows.materialize_case_state(case)
    person_b = next(row for row in view["stage"]
                    if row["row_id"] == dataset["people_prototypes"]["P102"]["row_id"])
    assert person_b["dia_chi"] == address_b2

    step_resave = f4["expected"]["steps"][1]
    assert step_resave["action"] == "luu_lai_sach"
    resaved = CaseWorkspaceService(db).save_case(
        case_id=case_id, base_revision=2, idempotency_key=None,
        case_meta=_meta(f4), stage=_stage(f4, dataset), state=_state(f4, dataset))
    assert resaved["case"]["status"] == step_resave["expected"]["status"] == "done"
    assert resaved["case"]["revision"] == step_resave["expected"]["revision"] == 3
    assert _person(resaved["stage"], dataset, "P102")["entity_id"] == identity_before
    assert _person(resaved["stage"], dataset, "P102")["dia_chi"] == address_b2
    case = db.get(InheritanceCase, case_id)
    db.refresh(case)
    assert case.trang_thai == "done"

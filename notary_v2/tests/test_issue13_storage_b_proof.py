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
- C1: F1 → F4-sửa Người/Tài sản/đất qua commit (chưa Save lại); session
  mới xuất DOCX tổng hợp đọc XML thấy giá trị mới, không còn giá trị cũ.
- C2: Done update_meta rồi convert hai chiều giữ Stage/status; DOCX theo
  domain mới; lỗi thiếu xác nhận/owner không ghi gì.
- C4: F6A/F6B + hai Customer trùng neo (ID thấp/cao); sửa A không đổi B;
  resolver `source_latest` giữ đúng identity của case Done mới nhất.

F2 (hai bên), F3 và các bước nháp khác của F7 không nằm trong phạm vi
P1/P2/F4/F5 của lượt proof này; đã có test nền ở
`test_issue13_storage_foundation.py` và `test_workspace_save_case.py`.
"""
import json
import uuid
from pathlib import Path

import pytest
from docx import Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database
from models import CaseAssetRow, CasePersonRow, Customer, InheritanceCase
from services import case_rows
from services import word_batch_export as wbe
from services.case_workspace import CaseWorkspaceService, WorkspaceError

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
            "spouseSlotIds": [],
            "spouseSlotId": None,
            "spouseSuggestionId": None,
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
            source["spouseSlotIds"].append(target["id"])
            source["spouseSlotId"] = source["spouseSlotIds"][-1]
            target["spouseSlotIds"].append(source["id"])
            target["spouseSlotId"] = target["spouseSlotIds"][-1]
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


def _export_paragraphs(factory, case_id, tokens, tmp_path, *, key):
    """Xuất DOCX thật bằng mẫu tổng hợp tự tạo; trả text từng paragraph.

    Session riêng cho lần xuất (mở lại case từ DB), engine + python-docx
    thật — không assert file tồn tại hay mapping RAM.
    """
    template_dir = tmp_path / f"templates_{key}"
    dest = tmp_path / f"out_{key}"
    template_dir.mkdir(parents=True)
    dest.mkdir(parents=True)
    template = template_dir / f"{key}.docx"
    doc = Document()
    for token in tokens:
        doc.add_paragraph(token)
    doc.save(template)
    session = factory()
    try:
        case = session.get(InheritanceCase, case_id)
        spec = wbe.WordDocumentSpec(document_key=key, display_name=key,
                                    filename_stem=key)
        batch = wbe.export_batch(
            case, case_id=case_id, document_keys=[key], dest_dir=dest,
            resolve_template=lambda _k: template, doc_specs=[spec])
        entry = batch["documents"][0]
        assert entry["status"] == "saved", entry
        output = Document(entry["output_file"]["path"])
        return [p.text for p in output.paragraphs]
    finally:
        session.close()


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


# ------------------- C1: Done sửa qua commit → Word thấy bản mới (F1/F4)


def test_c1_done_commit_new_values_reach_word_before_resave(
        dataset, db, session_factory, tmp_path):
    """C1: commit rev2 giữ done; xuất DOCX thật ở session mới đọc XML
    thấy giá trị mới (Người/Tài sản/đất) và không còn giá trị cũ —
    trước khi Save lại (không gọi `save_case` lần nữa)."""
    f1 = _case_spec(dataset, "F1")
    saved = _save_new(db, dataset, f1)
    case_id = saved["case"]["id"]

    stage = CaseWorkspaceService(db).get(case_id)["stage"]
    _person(stage, dataset, "P101")["ngay_sinh"] = "1951"
    _person(stage, dataset, "P102")["dia_chi"] = "Ngõ Thử Nghiệm 77"
    asset = _asset(stage, dataset, "T101")
    asset["so_thua_dat"] = "77"
    asset["dia_chi"] = "Thửa Thử Nghiệm 88"
    asset["land_rows"][0].update(
        {"loai_dat": "NTS", "dien_tich": 123.5, "thoi_han": "2055"})

    changed = CaseWorkspaceService(db).commit_stage(
        case_id, saved["case"]["revision"], stage)
    assert changed["revision"] == 2
    assert CaseWorkspaceService(db).get(case_id)["case"]["status"] == "done"

    tokens = [
        "[Tên 1]", "[Người 2 - Họ tên]", "[Người 2 - Địa chỉ]",
        "[Năm sinh 1]",
        "[Tài sản 1 - Số thửa]", "[Tài sản 1 - Địa chỉ]",
        "[Loại đất 1.1 - Loại đất]", "[Diện tích loại đất tài sản 1.1]",
        "[Thời hạn loại đất tài sản 1.1]",
        "[Loại đất 1.2 - Loại đất]", "[Diện tích loại đất tài sản 1.2]",
        "[Loại đất 1.3 - Loại đất]", "[Diện tích loại đất tài sản 1.3]",
        "[Thời hạn loại đất tài sản 1.3]",
    ]
    paragraphs = _export_paragraphs(
        session_factory, case_id, tokens, tmp_path, key="c1")
    assert paragraphs == [
        "Nguyễn Đăng An", "Trần Thị Bình", "Ngõ Thử Nghiệm 77",
        "1951",
        "77", "Thửa Thử Nghiệm 88",
        "NTS", "123.5", "2055",
        "", "",
        "CLN", "50", "2063",
    ]
    exported = "\n".join(paragraphs)
    for old in ("Khu Giả Lập B", "1950", "Thửa giả lập A", "ONT",
                "Lâu dài"):
        assert old not in exported

    # Xuất Word là read-only: vẫn rev2 done, chưa Save lại.
    reopened = CaseWorkspaceService(db).get(case_id)
    assert reopened["case"]["revision"] == 2
    assert reopened["case"]["status"] == "done"


# ------------- C2: Done update_meta + convert hai chiều giữ Stage/status


def test_c2_done_meta_and_convert_type_keep_stage_and_docx(
        dataset, db, session_factory, tmp_path):
    """C2: update_meta trên Done → rev+1 giữ done; convert hai chiều có
    xác nhận giữ nguyên row_id/entity_id/giá trị, reset Diagram domain
    mới; DOCX thật theo từng domain thấy meta/Người/Tài sản."""
    f1 = _case_spec(dataset, "F1")
    saved = _save_new(db, dataset, f1)
    case_id = saved["case"]["id"]

    updated = CaseWorkspaceService(db).update_meta(
        case_id, saved["case"]["revision"],
        {"ngay_lap_ho_so": "2026-11-05", "noi_niem_yet": "Xã Thử Nghiệm",
         "ghi_chu": "Ghi chú Thử Nghiệm"})
    assert updated["revision"] == 2
    assert updated["case"]["status"] == "done"
    assert updated["case"]["noi_niem_yet"] == "Xã Thử Nghiệm"
    assert updated["case"]["ghi_chu"] == "Ghi chú Thử Nghiệm"

    before = CaseWorkspaceService(db).get(case_id)
    stage_before = before["stage"]
    owner_row_id = stage_before["owner_row_id"]

    # Thiếu xác nhận xóa Diagram → không ghi gì.
    with pytest.raises(WorkspaceError) as exc:
        CaseWorkspaceService(db).convert_type(
            case_id, 2, {"case_type": "two_party",
                         "document_type": "chuyen_nhuong"})
    assert exc.value.code == "validation_error"
    unchanged = CaseWorkspaceService(db).get(case_id)
    assert unchanged["case"]["revision"] == 2
    assert unchanged["case"]["case_type"] == "inheritance"

    converted = CaseWorkspaceService(db).convert_type(
        case_id, 2, {"case_type": "two_party",
                     "document_type": "chuyen_nhuong",
                     "confirm_diagram_reset": True})
    assert converted["case"]["status"] == "done"
    assert converted["case"]["revision"] == 3
    assert converted["case"]["case_type"] == "two_party"
    assert converted["case"]["document_type"] == "chuyen_nhuong"
    assert converted["stage"]["people"] == stage_before["people"]
    assert converted["stage"]["assets"] == stage_before["assets"]
    assert "owner_row_id" not in converted["stage"]
    assert converted["diagram"]["domain"] == "two_party"
    assert converted["diagram"]["state"]["nodes"]
    assert all(node["personId"] is None
               for node in converted["diagram"]["state"]["nodes"])
    assert converted["case"]["noi_niem_yet"] == "Xã Thử Nghiệm"
    assert converted["case"]["ghi_chu"] == "Ghi chú Thử Nghiệm"
    assert converted["case"]["ngay_lap_ho_so"] == "2026-11-05"

    paragraphs = _export_paragraphs(
        session_factory, case_id,
        ["[Ngày lập hồ sơ]", "[Nơi niêm yết]", "[Ghi chú]",
         "[Người 1 - Họ tên]", "[Người 1 - Địa chỉ]",
         "[Tài sản 1 - Số thửa]"],
        tmp_path, key="c2_two_party")
    assert paragraphs == [
        "05/11/2026", "Xã Thử Nghiệm", "Ghi chú Thử Nghiệm",
        "Nguyễn Đăng An", "Khu Giả Lập A", "11"]

    # two_party → inheritance: thiếu owner phải bị chặn, không ghi.
    with pytest.raises(WorkspaceError) as exc:
        CaseWorkspaceService(db).convert_type(
            case_id, 3, {"case_type": "inheritance",
                         "document_type": "khai_nhan",
                         "confirm_diagram_reset": True})
    assert exc.value.code == "workspace_owner_required"
    unchanged = CaseWorkspaceService(db).get(case_id)
    assert unchanged["case"]["revision"] == 3
    assert unchanged["case"]["case_type"] == "two_party"
    assert unchanged["stage"]["people"] == stage_before["people"]

    with pytest.raises(WorkspaceError) as exc:
        CaseWorkspaceService(db).convert_type(
            case_id, 3, {"case_type": "inheritance",
                         "document_type": "khai_nhan",
                         "owner_row_id": owner_row_id})
    assert exc.value.code == "validation_error"

    back = CaseWorkspaceService(db).convert_type(
        case_id, 3, {"case_type": "inheritance",
                     "document_type": "khai_nhan",
                     "confirm_diagram_reset": True,
                     "owner_row_id": owner_row_id})
    assert back["case"]["status"] == "done"
    assert back["case"]["revision"] == 4
    assert back["case"]["case_type"] == "inheritance"
    assert back["stage"]["owner_row_id"] == owner_row_id
    assert back["stage"]["people"] == stage_before["people"]
    assert back["stage"]["assets"] == stage_before["assets"]
    assert back["diagram"]["domain"] == "inheritance"
    nodes = back["diagram"]["state"]["nodes"]
    assert [(node["id"], node["personId"]) for node in nodes] == [
        ("owner", owner_row_id)]

    paragraphs = _export_paragraphs(
        session_factory, case_id,
        ["[Ngày lập hồ sơ]", "[Nơi niêm yết]", "[Ghi chú]",
         "[Tên 1]", "[Địa chỉ 1]", "[Tài sản 1 - Số thửa]"],
        tmp_path, key="c2_inheritance")
    assert paragraphs == [
        "05/11/2026", "Xã Thử Nghiệm", "Ghi chú Thử Nghiệm",
        "Nguyễn Đăng An", "Khu Giả Lập A", "11"]

    reopened, session = _reopen(session_factory, case_id)
    try:
        assert reopened["case"]["status"] == "done"
        assert reopened["case"]["revision"] == 4
        assert reopened["case"]["ngay_lap_ho_so"] == "2026-11-05"
        assert reopened["case"]["noi_niem_yet"] == "Xã Thử Nghiệm"
        assert reopened["case"]["ghi_chu"] == "Ghi chú Thử Nghiệm"
        assert reopened["stage"]["people"] == stage_before["people"]
        assert reopened["stage"]["assets"] == stage_before["assets"]
    finally:
        session.close()


# ---------- C4: chung neo + hai Customer trùng ID thấp/cao, resolver


def test_c4_shared_anchor_high_id_stays_with_its_case(
        dataset, db, session_factory, tmp_path):
    """C4: F6A/F6B chung neo; seed hai Customer trùng neo (ID thấp/cao)
    và gắn case B vào ID cao bằng ORM có chủ đích. Sửa A → Word A mới,
    Word B giữ dữ kiện B; resolver lấy case Done mới nhất và giữ đúng
    identity nguồn (ID cao), không merge/xóa/rebind case còn lại."""
    proto = dataset["people_prototypes"]["P101"]
    anchor = CaseWorkspaceService._person_anchor(
        proto["ho_ten"], proto["so_giay_to"])
    assert anchor is not None
    low = Customer(ho_ten=proto["ho_ten"], so_giay_to=proto["so_giay_to"],
                   name_anchor=anchor[0], document_anchor=anchor[1])
    high = Customer(ho_ten=proto["ho_ten"], so_giay_to=proto["so_giay_to"],
                    name_anchor=anchor[0], document_anchor=anchor[1])
    db.add_all([low, high])
    db.commit()
    assert low.id < high.id

    a = _save_new(db, dataset, _case_spec(dataset, "F6A"))
    b = _save_new(db, dataset, _case_spec(dataset, "F6B"))
    a_row_id = a["stage"]["people"][0]["row_id"]
    b_row_id = b["stage"]["people"][0]["row_id"]
    a_asset_row_id = a["stage"]["assets"][0]["row_id"]
    b_asset_row_id = b["stage"]["assets"][0]["row_id"]
    a_customer_id = a["stage"]["people"][0]["entity_id"]
    property_id = a["stage"]["assets"][0]["entity_id"]
    assert a_customer_id == low.id
    assert b["stage"]["people"][0]["entity_id"] == low.id
    assert property_id is not None
    assert b["stage"]["assets"][0]["entity_id"] == property_id

    # Gắn case B vào identity ID cao bằng ORM (ý định của test).
    row_b = db.query(CasePersonRow).filter_by(case_id=b["case"]["id"]).one()
    row_b.customer_id = high.id
    db.commit()

    # Sửa A qua commit: Word A thấy dữ kiện A mới.
    stage_a = CaseWorkspaceService(db).get(a["case"]["id"])["stage"]
    stage_a["people"][0]["dia_chi"] = "Ngõ Chỉ Của A"
    changed_a = CaseWorkspaceService(db).commit_stage(
        a["case"]["id"], a["case"]["revision"], stage_a)
    assert changed_a["revision"] == 2

    tokens = ["[Tên 1]", "[Địa chỉ 1]", "[Ngày cấp 1]",
              "[Tài sản 1 - Số thửa]", "[Loại đất 1.1 - Loại đất]",
              "[Diện tích loại đất tài sản 1.1]"]
    a_paragraphs = _export_paragraphs(
        session_factory, a["case"]["id"], tokens, tmp_path, key="c4_a")
    assert a_paragraphs == [
        "Nguyễn Đăng An", "Ngõ Chỉ Của A", "20/05/2011", "11", "ONT",
        "100"]
    b_paragraphs = _export_paragraphs(
        session_factory, b["case"]["id"], tokens, tmp_path, key="c4_b")
    assert b_paragraphs == [
        "NGUYEN DANG AN", "", "01/06/2020", "31", "", ""]

    # B là case Done được lưu gần nhất (commit sạch, dữ kiện B giữ nguyên).
    stage_b = CaseWorkspaceService(db).get(b["case"]["id"])["stage"]
    touched_b = CaseWorkspaceService(db).commit_stage(
        b["case"]["id"], b["case"]["revision"], stage_b)
    assert touched_b["revision"] == 2
    assert touched_b["stage"]["people"][0]["entity_id"] == high.id

    session = session_factory()
    try:
        source = CaseWorkspaceService(session).source_latest()
    finally:
        session.close()
    assert source["source_case_id"] == b["case"]["id"]
    assert source["source_status"] == "done"
    source_person = source["stage"]["people"][0]
    assert source_person["entity_id"] == high.id
    assert source_person["row_id"] != b_row_id
    assert source_person["ho_ten"] == "NGUYEN DANG AN"
    assert source_person["dia_chi"] is None
    assert source_person["ngay_cap"] == "2020-06-01"
    source_asset = source["stage"]["assets"][0]
    assert source_asset["so_thua_dat"] == "31"
    assert source_asset["land_rows"] == []

    # Reopen session mới: toàn bộ ID/FK còn nguyên, không merge/xóa/rebind.
    session = session_factory()
    try:
        case_a = session.get(InheritanceCase, a["case"]["id"])
        case_b = session.get(InheritanceCase, b["case"]["id"])
        row_a = session.query(CasePersonRow).filter_by(
            case_id=a["case"]["id"]).one()
        row_b = session.query(CasePersonRow).filter_by(
            case_id=b["case"]["id"]).one()
        assert (row_a.row_id, row_a.customer_id) == (a_row_id, low.id)
        assert (row_b.row_id, row_b.customer_id) == (b_row_id, high.id)
        asset_a = session.query(CaseAssetRow).filter_by(
            case_id=a["case"]["id"]).one()
        asset_b = session.query(CaseAssetRow).filter_by(
            case_id=b["case"]["id"]).one()
        assert (asset_a.row_id, asset_a.property_id) == (
            a_asset_row_id, property_id)
        assert (asset_b.row_id, asset_b.property_id) == (
            b_asset_row_id, property_id)
        assert case_a.nguoi_chet_id == low.id
        assert case_b.nguoi_chet_id == high.id
        assert case_a.trang_thai == case_b.trang_thai == "done"
        assert session.query(Customer).count() == 2
        assert session.get(Customer, low.id) is not None
        assert session.get(Customer, high.id) is not None
    finally:
        session.close()

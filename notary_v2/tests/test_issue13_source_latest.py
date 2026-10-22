"""C3 — resolver nguồn Done (`notary.workspace_source_latest`, issue 13 vòng 2).

Đáp án lấy từ `fixtures/issue13_storage_b.json` scenario F8 (design vòng 2
§5) và literals của fixture — không lấy output resolver làm oracle.

Phạm vi file này:
- chọn nguồn theo mốc lưu kỹ thuật (microsecond, null-last, tie id DESC);
- remap row_id mới/owner/giữ entity_id, không meta/Diagram, không ghi DB;
- mốc lưu: mọi đường ghi case tiến microsecond; replay/conflict/lỗi/get/
  evaluate không tiến;
- E1 tối thiểu: nguồn → create giữ đúng identity kể cả khi có ID cũ trùng
  neo thấp hơn (không bị min-ID kéo lại).

F8C là nháp: public partial-create thuộc lát sau, nên test seed ORM trực
tiếp (status draft + updated_at theo action). Các action còn lại đi qua
public service với clock `case_saved_at` được monkeypatch.
"""
import json
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, update
from sqlalchemy.orm import sessionmaker

import database
import models
from models import (
    CaseAssetRow,
    CasePersonRow,
    Customer,
    InheritanceCase,
    InheritanceParticipant,
)
from routers import participants as participants_router
from services import case_workspace
from services import inheritance_workspace
from services.case_workspace import CaseWorkspaceService, WorkspaceError
from services.inheritance_workspace import InheritanceWorkspaceService

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "issue13_storage_b.json"
UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
INHERITANCE_META = {"case_type": "inheritance",
                    "document_type": "khai_nhan",
                    "ngay_lap_ho_so": "2026-10-22"}


# ---------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def dataset():
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'source_latest.db'}")
    database.enable_sqlite_foreign_keys(engine)
    database.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory, engine
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    factory, _engine = session_factory
    session = factory()
    yield session
    session.close()


# ------------------------------------------------------------------ helpers


def _spec(dataset, alias):
    matches = [case for case in dataset["cases"] if case["alias"] == alias]
    assert len(matches) == 1, f"fixture phải có đúng một ca {alias}"
    return matches[0]


def _parse_stamp(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")


def _suffix(row_id, suffix):
    return f"{row_id[:-3]}{suffix:03d}"


def _stage_for(dataset, alias):
    """Stage wire của F8 alias từ `case_template` + suffix/override."""
    scenario = _spec(dataset, "F8")["scenario"]
    entry = scenario["aliases"][alias]
    template = _spec(dataset, entry["case_template"])
    overrides = scenario["overrides"].get(alias) or {}
    people_overrides = overrides.get("people") or {}
    asset_overrides = overrides.get("assets") or {}
    people = []
    owner_row_id = None
    owner_proto = template["diagram"].get("owner_row_id")
    for source, suffix in zip(template["people"],
                              entry["person_suffixes"]):
        data = dict(dataset["people_prototypes"][source["prototype"]])
        data["row_id"] = _suffix(data["row_id"], suffix)
        data.update(people_overrides.get(source["prototype"]) or {})
        people.append(data)
        if source["prototype"] == owner_proto:
            owner_row_id = data["row_id"]
    assets = []
    if not isinstance(asset_overrides, list):
        for source, suffix in zip(template["assets"],
                                  entry["asset_suffixes"]):
            data = dict(dataset["asset_prototypes"][source["prototype"]])
            data["row_id"] = _suffix(data["row_id"], suffix)
            data.update(asset_overrides.get(source["prototype"]) or {})
            assets.append(data)
    if "owner_row_id" in overrides:
        owner_row_id = overrides["owner_row_id"]
    stage = {"people": people, "assets": assets}
    if template["case_type"] == "inheritance":
        stage = {"owner_row_id": owner_row_id, **stage}
    return stage


def _meta_for(dataset, alias):
    scenario = _spec(dataset, "F8")["scenario"]
    template = _spec(dataset, scenario["aliases"][alias]["case_template"])
    return {
        "case_type": template["case_type"],
        "document_type": template["metadata"]["loai_van_ban"],
        "ngay_lap_ho_so": template["metadata"].get("ngay_lap_ho_so"),
    }


def _state_for(stage):
    """Diagram v3 tối thiểu: node owner đã gán + vị trí tài sản 1."""
    if "owner_row_id" not in stage:
        return {"version": 3, "domain": "two_party",
                "nodes": []}
    return {"version": 3, "domain": "inheritance", "nodes": [{
        "id": "owner", "personId": stage.get("owner_row_id"),
        "parentSlotIds": [], "spouseSlotId": None,
        "ownPositions": [1] if stage.get("assets") else [],
        "receivePositions": [], "hidden": False, "deleted": False,
    }]}


def _clock(monkeypatch, value):
    """Clock điều khiển cho `case_saved_at` của mọi writer dùng chung.

    ORM `onupdate` được patch sang một mốc KHÁC (+1s): nếu code để ORM
    flush sau CAS cuối, mốc DB sẽ lệch và test đóng dấu bắt được.
    """
    holder = {"value": value}

    def fake():
        return holder["value"]

    monkeypatch.setattr(case_workspace, "case_saved_at", fake)
    monkeypatch.setattr(inheritance_workspace, "case_saved_at", fake)
    monkeypatch.setattr(participants_router, "case_saved_at", fake)
    monkeypatch.setattr(models, "case_saved_at",
                        lambda: holder["value"] + timedelta(seconds=1))
    return holder


def _stamp_of(factory, case_id):
    session = factory()
    try:
        case = session.get(InheritanceCase, case_id)
        session.refresh(case)
        return case.updated_at, case.workspace_revision
    finally:
        session.close()


def _seed_draft(db, *, people=(), assets=(), updated_at=None,
                owner_row_id=None, document_type="khai_nhan",
                status="draft"):
    case = InheritanceCase(
        loai_van_ban=document_type, trang_thai=status,
        workspace_revision=1,
        updated_at=updated_at or models.case_saved_at())
    db.add(case)
    db.flush()
    for index, row in enumerate(people, start=1):
        db.add(CasePersonRow(
            row_id=row["row_id"], case_id=case.id, vitri=index,
            ho_ten=row.get("ho_ten"), customer_id=row.get("entity_id")))
    for index, row in enumerate(assets, start=1):
        db.add(CaseAssetRow(
            row_id=row["row_id"], case_id=case.id, vitri=index,
            so_serial=row.get("so_serial") or "",
            land_rows_present=row.get("land_rows") is not None))
    if owner_row_id is not None:
        case.case_state_json = json.dumps({
            "schemaVersion": 4, "case": {},
            "owner_row_id": owner_row_id,
            "diagram": {"state": {
                "version": 3, "domain": "inheritance", "nodes": []},
                "render_model": None}})
    db.commit()
    return case


def _sql_writes(engine):
    """Listener ghi lại mọi câu INSERT/UPDATE/DELETE/REPLACE."""
    statements = []

    def before_cursor_execute(conn, cursor, statement, parameters,
                              context, executemany):
        head = statement.lstrip().split(None, 1)[0].upper()
        if head in ("INSERT", "UPDATE", "DELETE", "REPLACE"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    return statements, lambda: event.remove(
        engine, "before_cursor_execute", before_cursor_execute)


# ------------------------------------------------------- F8: chọn nguồn


def test_f8_source_selection_by_saved_at_microsecond_and_tie_id(
        dataset, session_factory, db, monkeypatch):
    factory, _engine = session_factory
    scenario = _spec(dataset, "F8")["scenario"]
    expected = _spec(dataset, "F8")["expected"]
    steps = {step["checkpoint"]: step for step in expected["steps"]}
    clock = _clock(monkeypatch, _parse_stamp(
        "2026-10-22T08:00:00.000000Z"))
    svc = CaseWorkspaceService(db)

    ids = {}
    recorded = {}
    checkpoints = {}
    for action in scenario["actions"]:
        if action["action"] == "source_latest":
            checkpoints[action["checkpoint"]] = svc.source_latest()
            continue
        if action["action"] == "save_case_new":
            clock["value"] = _parse_stamp(action["saved_at"])
            alias = action["case"]
            stage = _stage_for(dataset, alias)
            data = svc.save_case(
                case_id=None, base_revision=None,
                idempotency_key=str(uuid.uuid4()),
                case_meta=_meta_for(dataset, alias), stage=stage,
                state=_state_for(stage))
            ids[alias] = data["case"]["id"]
            recorded[alias] = _stamp_of(factory, ids[alias])[0]
        elif action["action"] == "create_draft":
            alias = action["case"]
            stage = _stage_for(dataset, alias)
            case = _seed_draft(
                db, people=stage["people"], assets=stage["assets"],
                updated_at=_parse_stamp(action["saved_at"]),
                owner_row_id=None)
            ids[alias] = case.id
        elif action["action"] == "force_equal_saved_at":
            value = _parse_stamp(action["saved_at"])
            db.execute(update(InheritanceCase)
                       .where(InheritanceCase.id.in_(
                           [ids[alias] for alias in action["cases"]]))
                       .values(updated_at=value))
            db.commit()
        elif action["action"] == "commit_stage":
            clock["value"] = _parse_stamp(action["saved_at"])
            alias = action["case"]
            workspace = svc.get(ids[alias])
            stage = workspace["stage"]
            template_people = [
                entry["prototype"] for entry in
                _spec(dataset, scenario["aliases"][alias]
                      ["case_template"])["people"]]
            for prototype, override in action["override"].items():
                suffix = scenario["aliases"][alias]["person_suffixes"][
                    template_people.index(prototype)]
                row_id = _suffix(
                    dataset["people_prototypes"][prototype]["row_id"],
                    suffix)
                row = next(r for r in stage["people"]
                           if r["row_id"] == row_id)
                row.update(override)
            svc.commit_stage(
                ids[alias], workspace["case"]["revision"], stage)
        else:                                # pragma: no cover
            pytest.fail(f"action lạ {action['action']}")

    # Thứ tự ID theo fixture: A ghi trước B, C sau — đáp án tie độc lập.
    assert [ids[a] for a in expected["case_id_order"]] == sorted(ids.values())
    assert ids["F8A"] < ids["F8B"]

    # Cùng một giây, khác microsecond: B (.100002) > A (.100001); C draft
    # không được chọn dù mốc mới hơn.
    assert recorded["F8B"] == _parse_stamp("2026-10-22T08:00:00.100002Z")
    assert recorded["F8A"] == _parse_stamp("2026-10-22T08:00:00.100001Z")
    assert recorded["F8B"].second == recorded["F8A"].second
    assert checkpoints["empty"] == {
        "schema_version": "notary.case-drafting.v2",
        "backend_mode": "real",
        "source_case_id": None,
        "source_status": None,
        "stage": {"people": [], "assets": []},
    }

    after_b = checkpoints["after_b_and_c"]
    assert after_b["source_case_id"] == ids["F8B"]
    assert after_b["source_status"] == "done"
    assert after_b["stage"]["people"][0]["dia_chi"] is None
    assert after_b["stage"]["people"][0]["ngay_cap"] == "2020-06-01"
    assert after_b["stage"]["assets"][0]["land_rows"] == []
    assert [p["ho_ten"] for p in after_b["stage"]["people"]] == [
        dataset["people_prototypes"]["P111"]["ho_ten"]]

    # Tie tuyệt đối: id cao thắng.
    tie = checkpoints["absolute_tie"]
    assert _stamp_of(factory, ids["F8B"])[0] == _parse_stamp(
        "2026-10-22T08:00:01.000000Z")
    assert tie["source_case_id"] == ids["F8B"]
    assert tie["source_case_id"] > ids["F8A"]

    # Cập nhật Done A → nguồn chuyển A; giấy mới/đầy đủ không phải khóa.
    assert _stamp_of(factory, ids["F8A"])[0] == _parse_stamp(
        "2026-10-22T08:00:01.000001Z")
    source = checkpoints["after_update_a"]
    assert source["source_case_id"] == ids["F8A"]
    assert source["source_status"] == "done"
    people = source["stage"]["people"]
    assert [p["ho_ten"] for p in people] == [
        dataset["people_prototypes"][alias]["ho_ten"]
        for alias in ("P101", "P102", "P103")]
    saved_a = svc.get(ids["F8A"])["stage"]
    source_row_ids = [p["row_id"] for p in saved_a["people"]]
    assert [p["row_id"] for p in people] != source_row_ids
    assert all(p["row_id"] not in source_row_ids for p in people)
    assert source["stage"]["owner_row_id"] == people[0]["row_id"]
    p102 = people[1]
    assert p102["dia_chi"] == steps["after_update_a"]["P102_dia_chi"]
    assert people[0]["ngay_sinh"] == "1950"
    assert [row["dien_tich"] for row in
            source["stage"]["assets"][0]["land_rows"]] == [100, None, 50]

    # Đọc lặp: row_id mới hoàn toàn, owner trỏ đúng person đã remap,
    # entity_id giữ, không meta/Diagram trên data.
    again = svc.source_latest()
    first_ids = {row["row_id"] for row in
                 source["stage"]["people"] + source["stage"]["assets"]}
    second_ids = {row["row_id"] for row in
                  again["stage"]["people"] + again["stage"]["assets"]}
    assert first_ids.isdisjoint(second_ids)
    assert all(UUID4_RE.match(rid) for rid in first_ids | second_ids)
    assert again["stage"]["owner_row_id"] in {
        row["row_id"] for row in again["stage"]["people"]}
    assert set(again) == {"schema_version", "backend_mode",
                          "source_case_id", "source_status", "stage"}
    assert set(again["stage"]) == {"owner_row_id", "people", "assets"}
    assert [row["entity_id"] for row in again["stage"]["people"]] == [
        row["entity_id"] for row in saved_a["people"]]
    assert [row["entity_id"] for row in again["stage"]["assets"]] == [
        row["entity_id"] for row in saved_a["assets"]]


def test_source_latest_empty_is_success(session_factory):
    factory, _engine = session_factory
    session = factory()
    try:
        data = CaseWorkspaceService(session).source_latest()
    finally:
        session.close()
    assert data == {
        "schema_version": "notary.case-drafting.v2",
        "backend_mode": "real",
        "source_case_id": None,
        "source_status": None,
        "stage": {"people": [], "assets": []},
    }


def test_source_latest_null_timestamp_is_last(session_factory, db):
    """updated_at null (seed/ngoài luồng) xếp sau timestamp có giá trị."""
    valued = _seed_draft(db, status="done",
                         updated_at=datetime(2026, 10, 22, 8, 0, 0, 5))
    null_case = _seed_draft(db, status="done",
                            updated_at=datetime(2026, 10, 22, 8, 0, 0, 6))
    db.execute(update(InheritanceCase)
               .where(InheritanceCase.id == null_case.id)
               .values(updated_at=None))
    db.commit()
    assert CaseWorkspaceService(db).source_latest()["source_case_id"] == \
        valued.id
    # Toàn bộ null → vẫn id DESC, không lỗi.
    db.execute(update(InheritanceCase)
               .where(InheritanceCase.id == valued.id)
               .values(updated_at=None))
    db.commit()
    assert CaseWorkspaceService(db).source_latest()["source_case_id"] == \
        max(valued.id, null_case.id)


def test_source_latest_unsupported_type_is_error(dataset, session_factory, db):
    factory, _engine = session_factory
    case = _seed_draft(db, document_type="gift", status="done",
                       updated_at=datetime(2026, 10, 22, 8, 0, 0, 5))
    with pytest.raises(WorkspaceError) as exc:
        CaseWorkspaceService(db).source_latest()
    assert exc.value.code == "case_type_unsupported"
    assert exc.value.details["case_type"] == "gift"
    assert case.id


def test_source_latest_does_not_write_and_reads_fresh_timestamp(
        dataset, session_factory, db, monkeypatch):
    factory, engine = session_factory
    clock = _clock(monkeypatch, datetime(2026, 10, 22, 8, 0, 0, 123456))
    stage = _stage_for(dataset, "F8A")
    data = CaseWorkspaceService(db).save_case(
        case_id=None, base_revision=None,
        idempotency_key=str(uuid.uuid4()),
        case_meta=_meta_for(dataset, "F8A"), stage=stage,
        state=_state_for(stage))
    case_id = data["case"]["id"]

    # Timestamp roundtrip từ session MỚI: kiểu datetime + microsecond.
    stamp, revision = _stamp_of(factory, case_id)
    assert isinstance(stamp, datetime)
    assert stamp == datetime(2026, 10, 22, 8, 0, 0, 123456)
    assert stamp.microsecond == 123456
    assert revision == 1

    session = factory()
    try:
        statements, stop = _sql_writes(engine)
        try:
            result = CaseWorkspaceService(session).source_latest()
        finally:
            stop()
        assert result["source_case_id"] == case_id
        assert statements == [], statements
    finally:
        session.close()
    assert _stamp_of(factory, case_id) == (stamp, revision)


# ------------------------------------------------ mốc lưu theo mọi writer


def _two_person_stage():
    return {
        "owner_row_id": str(uuid.uuid4()),
        "people": [
            {"row_id": str(uuid.uuid4()), "entity_id": None,
             "ho_ten": "Người A", "gioi_tinh": None, "ngay_sinh": None,
             "ngay_chet": None, "so_giay_to": None, "ngay_cap": None,
             "noi_cap": None, "dia_chi": None, "place_of_origin": None,
             "loai_giay_to": None, "loai_dia_chi": None},
        ],
        "assets": [
            {"row_id": str(uuid.uuid4()), "entity_id": None,
             "so_serial": "STAMP 001", "so_vao_so": None,
             "so_thua_dat": None, "so_to_ban_do": None, "dia_chi": None,
             "loai_so": None, "hinh_thuc_su_dung": None, "thoi_han": None,
             "nguon_goc": None, "ngay_cap": None, "co_quan_cap": None,
             "land_rows": None},
        ],
    }


def _stage_with_owner(stage):
    stage["owner_row_id"] = stage["people"][0]["row_id"]
    return stage


def _diagram_for(stage, domain="inheritance"):
    return {"version": 3, "domain": domain, "nodes": [{
        "id": "owner", "personId": stage.get("owner_row_id"),
        "parentSlotIds": [], "spouseSlotId": None,
        "ownPositions": [1] if stage.get("assets") else [],
        "receivePositions": [], "hidden": False, "deleted": False,
    }]}


def _create_case(db, stage, meta=None, state=None):
    return CaseWorkspaceService(db).create(
        str(uuid.uuid4()), meta or dict(INHERITANCE_META), stage,
        state if state is not None else _diagram_for(stage))


@pytest.mark.parametrize("writer", [
    "create", "save_case_new", "save_case_existing", "commit_stage",
    "update_meta", "convert_type", "save_diagram",
])
def test_writer_advances_updated_at_microseconds(
        writer, session_factory, db, monkeypatch):
    factory, _engine = session_factory
    start = datetime(2026, 10, 22, 9, 0, 0, 100000)
    clock = _clock(monkeypatch, start)
    svc = CaseWorkspaceService(db)
    stage = _stage_with_owner(_two_person_stage())
    state = _diagram_for(stage)
    case_id = None
    revision = None

    if writer in ("save_case_new",):
        data = svc.save_case(
            case_id=None, base_revision=None,
            idempotency_key=str(uuid.uuid4()),
            case_meta=dict(INHERITANCE_META), stage=stage, state=state)
        case_id, revision = data["case"]["id"], data["case"]["revision"]
    else:
        created = _create_case(db, stage, state=state)
        case_id = created["case"]["id"]
        revision = created["case"]["revision"]

    if writer == "create":
        # `_create_case` ở trên đã là writer create; đo chính nó.
        stamp, rev = _stamp_of(factory, case_id)
        assert stamp == start
        assert rev == 1
        return

    clock["value"] = start + timedelta(microseconds=7)
    if writer == "save_case_new":
        # Case mới thứ hai với stamp riêng.
        second_stage = _stage_with_owner(_two_person_stage())
        data = svc.save_case(
            case_id=None, base_revision=None,
            idempotency_key=str(uuid.uuid4()),
            case_meta=dict(INHERITANCE_META), stage=second_stage,
            state=_diagram_for(second_stage))
        case_id = data["case"]["id"]
    elif writer == "save_case_existing":
        svc.save_case(
            case_id=case_id, base_revision=revision,
            case_meta=dict(INHERITANCE_META), stage=stage, state=state)
    elif writer == "commit_stage":
        svc.commit_stage(case_id, revision, stage)
    elif writer == "update_meta":
        svc.update_meta(case_id, revision, {"ghi_chu": "mốc mới"})
    elif writer == "convert_type":
        svc.convert_type(case_id, revision, {
            "case_type": "two_party",
            "document_type": "chuyen_nhuong",
            "confirm_diagram_reset": True})
    elif writer == "save_diagram":
        InheritanceWorkspaceService(db).save_diagram(
            case_id, revision, state)
    stamp, _rev = _stamp_of(factory, case_id)
    assert stamp == start + timedelta(microseconds=7), writer
    assert stamp.microsecond == 100007


def test_participant_writes_stamp_parent_case(session_factory, db, monkeypatch):
    factory, _engine = session_factory
    start = datetime(2026, 10, 22, 9, 30, 0, 200000)
    clock = _clock(monkeypatch, start)
    stage = _stage_with_owner(_two_person_stage())
    case_id = _create_case(db, stage, state=_diagram_for(stage))["case"]["id"]
    customer = Customer(ho_ten="Người Tham Gia")
    db.add(customer)
    db.commit()

    clock["value"] = start + timedelta(microseconds=11)
    participants_router.add(
        ho_so_id=case_id, customer_id=customer.id, vai_tro="Con",
        hang_thua_ke=1, co_nhan_tai_san=None, ty_le=0.0, ghi_chu=None,
        db=db)
    assert _stamp_of(factory, case_id)[0] == start + timedelta(microseconds=11)

    participant = db.query(InheritanceParticipant).filter(
        InheritanceParticipant.ho_so_id == case_id).one()
    clock["value"] = start + timedelta(microseconds=12)
    participants_router.edit(
        pid=participant.id, vai_tro="Cháu", hang_thua_ke=2,
        co_nhan_tai_san="on", ty_le=0.5, ghi_chu="ghi chú", db=db)
    assert _stamp_of(factory, case_id)[0] == start + timedelta(microseconds=12)

    clock["value"] = start + timedelta(microseconds=13)
    participants_router.delete(pid=participant.id, db=db)
    assert _stamp_of(factory, case_id)[0] == start + timedelta(microseconds=13)

    # Nhánh exists-không-ghi: thêm lại cùng customer không stamp.
    clock["value"] = start + timedelta(microseconds=14)
    participants_router.add(
        ho_so_id=case_id, customer_id=customer.id, vai_tro="Con",
        hang_thua_ke=1, co_nhan_tai_san=None, ty_le=0.0, ghi_chu=None,
        db=db)
    first = _stamp_of(factory, case_id)[0]
    assert first == start + timedelta(microseconds=14)
    participants_router.add(
        ho_so_id=case_id, customer_id=customer.id, vai_tro="Con",
        hang_thua_ke=1, co_nhan_tai_san=None, ty_le=0.0, ghi_chu=None,
        db=db)
    assert _stamp_of(factory, case_id)[0] == first


def test_replay_conflict_and_error_do_not_advance_stamp(
        session_factory, db, monkeypatch):
    factory, _engine = session_factory
    start = datetime(2026, 10, 22, 10, 0, 0, 300000)
    clock = _clock(monkeypatch, start)
    svc = CaseWorkspaceService(db)
    stage = _stage_with_owner(_two_person_stage())
    state = _diagram_for(stage)
    key = str(uuid.uuid4())
    data = svc.save_case(
        case_id=None, base_revision=None, idempotency_key=key,
        case_meta=dict(INHERITANCE_META), stage=stage, state=state)
    case_id = data["case"]["id"]
    baseline = _stamp_of(factory, case_id)

    clock["value"] = start + timedelta(seconds=5)

    # Replay save_case mới cùng key/hash: trả workspace, không ghi mốc.
    replay = svc.save_case(
        case_id=None, base_revision=None, idempotency_key=key,
        case_meta=dict(INHERITANCE_META), stage=stage, state=state)
    assert replay["created"] is False
    assert _stamp_of(factory, case_id) == baseline

    # Replay create cùng key/hash: trả case đã tạo, không ghi mốc.
    create_stage = _stage_with_owner(_two_person_stage())
    create_key = str(uuid.uuid4())
    created = svc.create(create_key, dict(INHERITANCE_META), create_stage,
                         _diagram_for(create_stage))
    created_baseline = _stamp_of(factory, created["case"]["id"])
    replay_create = svc.create(create_key, dict(INHERITANCE_META),
                               create_stage, _diagram_for(create_stage))
    assert replay_create["created"] is False
    assert _stamp_of(factory, created["case"]["id"]) == created_baseline

    # Conflict base_revision (save cũ + commit) không ghi.
    with pytest.raises(WorkspaceError) as exc:
        svc.save_case(
            case_id=case_id, base_revision=99,
            case_meta=dict(INHERITANCE_META), stage=stage, state=state)
    assert exc.value.code == "workspace_conflict"
    assert _stamp_of(factory, case_id) == baseline
    with pytest.raises(WorkspaceError) as exc:
        svc.commit_stage(case_id, 99, stage)
    assert exc.value.code == "workspace_conflict"
    assert _stamp_of(factory, case_id) == baseline
    with pytest.raises(WorkspaceError) as exc:
        InheritanceWorkspaceService(db).save_diagram(case_id, 99, state)
    assert exc.value.code == "workspace_conflict"
    assert _stamp_of(factory, case_id) == baseline

    # Lỗi validation không ghi.
    with pytest.raises(WorkspaceError) as exc:
        svc.update_meta(case_id, baseline[1], {"ghi_chu": ""})
    assert exc.value.code == "validation_error"
    assert _stamp_of(factory, case_id) == baseline

    # GET / evaluate / export-options style read không ghi.
    svc.get(case_id)
    InheritanceWorkspaceService(db).evaluate_diagram(case_id, state)
    assert _stamp_of(factory, case_id) == baseline

    # Create lỗi không tạo case và không để lại mốc.
    bad_stage = _stage_with_owner(_two_person_stage())
    bad_stage["people"][0]["ho_ten"] = "   "
    with pytest.raises(WorkspaceError) as exc:
        _create_case(db, bad_stage, state=_diagram_for(bad_stage))
    assert exc.value.code == "stage_validation_error"
    assert db.query(InheritanceCase).count() == 2


# --------------------------------------------- E1 tối thiểu: nguồn → create


def test_source_stage_create_keeps_source_identity_over_min_id(
        dataset, session_factory, db, monkeypatch):
    factory, _engine = session_factory
    _clock(monkeypatch, datetime(2026, 10, 22, 11, 0, 0, 400000))
    svc = CaseWorkspaceService(db)
    prototype = dataset["people_prototypes"]["P101"]
    anchor = (
        case_workspace._normalize_name_key(prototype["ho_ten"]),
        case_workspace._normalize_document_key(prototype["so_giay_to"]))
    # ID cũ trùng neo thấp hơn nguồn.
    low = Customer(ho_ten=prototype["ho_ten"],
                   so_giay_to=prototype["so_giay_to"],
                   name_anchor=anchor[0], document_anchor=anchor[1])
    db.add(low)
    db.commit()
    high = Customer(ho_ten=prototype["ho_ten"],
                    so_giay_to=prototype["so_giay_to"],
                    name_anchor=anchor[0], document_anchor=anchor[1])
    db.add(high)
    db.commit()
    assert low.id < high.id

    source_stage = _stage_for(dataset, "F8A")
    source_stage["people"][0]["entity_id"] = high.id
    # Nguồn lưu bằng public save_case với gợi ý identity cao (neo khớp).
    source = svc.save_case(
        case_id=None, base_revision=None,
        idempotency_key=str(uuid.uuid4()),
        case_meta=_meta_for(dataset, "F8A"), stage=source_stage,
        state=_state_for(source_stage))
    assert source["stage"]["people"][0]["entity_id"] == high.id

    latest = svc.source_latest()
    assert latest["source_case_id"] == source["case"]["id"]
    assert latest["stage"]["people"][0]["entity_id"] == high.id

    # Dùng đúng Stage nguồn tạo case mới: giữ ID cao, không bị min-ID kéo.
    stage = latest["stage"]
    created = _create_case(db, stage, meta=_meta_for(dataset, "F8A"),
                           state=_state_for(stage))
    assert created["stage"]["people"][0]["entity_id"] == high.id
    assert created["stage"]["people"][0]["entity_id"] != low.id

    # Đổi neo → resolve theo neo mới (không sửa master, không giữ hint cũ).
    # Đọc nguồn lại để có row_id mới (row_id lần đọc trước đã thuộc case
    # vừa tạo).
    fresh = svc.source_latest()["stage"]
    changed = {**fresh, "people": [
        {**fresh["people"][0], "so_giay_to": "07, quyển 9"}] +
        fresh["people"][1:]}
    created2 = _create_case(db, changed, meta=_meta_for(dataset, "F8A"),
                            state=_state_for(changed))
    new_entity = created2["stage"]["people"][0]["entity_id"]
    assert new_entity is not None
    assert new_entity not in (low.id, high.id)
    session = factory()
    try:
        assert session.get(Customer, high.id).document_anchor == anchor[1]
    finally:
        session.close()

    # Hint không tồn tại → stage_validation_error gắn row/field.
    bad_base = svc.source_latest()["stage"]
    bad = {**bad_base, "people": [
        {**bad_base["people"][0], "entity_id": 987654}] +
        bad_base["people"][1:]}
    with pytest.raises(WorkspaceError) as exc:
        _create_case(db, bad, meta=_meta_for(dataset, "F8A"),
                     state=_state_for(bad))
    assert exc.value.code == "stage_validation_error"
    assert exc.value.details["field_errors"][0]["field"] == "entity_id"

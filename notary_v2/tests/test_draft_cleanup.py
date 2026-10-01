"""Tests MIN-141 đợt 4 — xóa hồ sơ nháp reference-safe + thống kê.

AC:
- Xóa draft → xóa hồ sơ + chỉ dọn master "thuộc hồ sơ" không còn tham
  chiếu (case khác, participant kể cả parent_customer_id, link tài sản,
  snapshot hồ sơ còn tồn tại, danh mục ủy quyền của case khác).
- Người nhận ủy quyền của chính hồ sơ bị xóa = danh bạ tái dùng → GIỮ.
- Không quét xóa danh bạ mồ côi ngoài phạm vi hồ sơ.
- Hồ sơ khóa → từ chối xóa.
- /api/stats đếm người/tài sản gắn hồ sơ, DISTINCT primary/link —
  danh bạ trơ không tính.
"""
import asyncio
import json
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database
import routers.cases as cases_router
from models import (
    Customer,
    InheritanceCase,
    InheritanceCaseProperty,
    InheritanceParticipant,
    Property,
    PropertyLandRow,
)


# ---------------------------------------------------------------- fixtures


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'cleanup.db'}")
    database.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


def _customer(db, name, **kw):
    c = Customer(ho_ten=name, **kw)
    db.add(c)
    db.flush()
    return c


def _property(db, serial, **kw):
    p = Property(so_serial=serial, dia_chi=f"Thửa {serial}", **kw)
    db.add(p)
    db.flush()
    return p


def _case(db, deceased, prop, *, trang_thai="draft", snapshot=None,
          uq_id=None, extra_props=(), participants=()):
    case = InheritanceCase(
        nguoi_chet_id=deceased.id, tai_san_id=prop.id,
        ngay_lap_ho_so=date(2026, 10, 1), loai_van_ban="khai_nhan",
        trang_thai=trang_thai,
        nguoi_nhan_uy_quyen_id=uq_id,
        case_state_json=snapshot)
    db.add(case)
    db.flush()
    for p in extra_props:
        db.add(InheritanceCaseProperty(case_id=case.id, property_id=p.id))
    for idx, (cust, parent) in enumerate(participants):
        db.add(InheritanceParticipant(
            ho_so_id=case.id, customer_id=cust.id,
            vai_tro="Con", hang_thua_ke=1, ty_le=0.0,
            co_nhan_tai_san=True,
            parent_customer_id=parent.id if parent else None))
    db.flush()
    db.commit()  # commit setup → test rollback không cuốn dữ liệu nền
    return case


def _snapshot(people_ids=(), asset_ids=(), uq_id=None):
    return json.dumps({
        "schemaVersion": 3,
        "case_type": "inheritance",
        "stage": [{"id": str(i), "row_id": f"r{i}"} for i in people_ids],
        "assets": [{"id": str(i), "row_id": f"a{i}"} for i in asset_ids],
        "case": {"nguoinhanuyquyen": {"id": uq_id, "ten": "X"}} if uq_id
                else {"nguoinhanuyquyen": {"id": None, "ten": None}},
    }, ensure_ascii=False)


# --------------------------------------------------------------- xóa hồ sơ


def test_delete_draft_removes_case_and_unreferenced_masters(db):
    dead = _customer(db, "Người chết", ngay_chet=date(2020, 1, 1))
    heir = _customer(db, "Người thừa kế")
    prop = _property(db, "AA0001")
    case = _case(db, dead, prop, participants=[(heir, None)])

    cases_router.delete(case.id, db=db)

    assert db.get(InheritanceCase, case.id) is None
    assert db.get(Customer, dead.id) is None
    assert db.get(Customer, heir.id) is None
    assert db.get(Property, prop.id) is None
    assert db.query(InheritanceParticipant).count() == 0


def test_delete_locked_case_refused(db):
    dead = _customer(db, "Người chết", ngay_chet=date(2020, 1, 1))
    prop = _property(db, "AA0002")
    case = _case(db, dead, prop, trang_thai="locked")

    cases_router.delete(case.id, db=db)

    assert db.get(InheritanceCase, case.id) is not None
    assert db.get(Customer, dead.id) is not None
    assert db.get(Property, prop.id) is not None


def test_delete_keeps_shared_deceased_and_property(db):
    """Người chết + tài sản còn được hồ sơ khác dùng → giữ nguyên."""
    dead = _customer(db, "Người chết", ngay_chet=date(2020, 1, 1))
    prop = _property(db, "AA0003")
    case_a = _case(db, dead, prop)
    keep = _case(db, dead, prop)   # hồ sơ B dùng chung cả hai master

    cases_router.delete(case_a.id, db=db)

    assert db.get(InheritanceCase, case_a.id) is None
    assert db.get(Customer, dead.id) is not None
    assert db.get(Property, prop.id) is not None
    assert db.get(InheritanceCase, keep.id) is not None


def test_delete_removes_only_case_local_participants(db):
    """Participant chỉ thuộc hồ sơ bị xóa → dọn; participant còn gắn
    hồ sơ khác (vai trò phụ) → giữ."""
    dead_a = _customer(db, "Dead A", ngay_chet=date(2020, 1, 1))
    dead_b = _customer(db, "Dead B", ngay_chet=date(2020, 1, 1))
    shared = _customer(db, "Heir chung")
    only_a = _customer(db, "Heir riêng A")
    pa = _property(db, "AA0004")
    pb = _property(db, "AA0005")
    case_a = _case(db, dead_a, pa,
                   participants=[(shared, None), (only_a, None)])
    _case(db, dead_b, pb, participants=[(shared, None)])

    cases_router.delete(case_a.id, db=db)

    assert db.get(Customer, only_a.id) is None        # chỉ của case A
    assert db.get(Customer, shared.id) is not None    # còn gắn case B
    assert db.get(Customer, dead_b.id) is not None


def test_delete_considers_parent_customer_id(db):
    """parent_customer_id của participant thuộc hồ sơ còn lại chặn dọn."""
    dead_a = _customer(db, "Dead A", ngay_chet=date(2020, 1, 1))
    dead_b = _customer(db, "Dead B", ngay_chet=date(2020, 1, 1))
    child_a = _customer(db, "Con A")
    child_b = _customer(db, "Con B")
    parent = _customer(db, "Cha/mẹ chung")   # chỉ làm vai trò phụ
    pa = _property(db, "AA0006")
    pb = _property(db, "AA0007")
    case_a = _case(db, dead_a, pa,
                   participants=[(child_a, parent)])
    _case(db, dead_b, pb, participants=[(child_b, parent)])

    cases_router.delete(case_a.id, db=db)

    assert db.get(Customer, parent.id) is not None  # còn là parent ở case B
    assert db.get(Customer, child_a.id) is None


def test_delete_keeps_uq_catalog_customer(db):
    """Người nhận ủy quyền = danh bạ tái dùng → KHÔNG bị xóa theo hồ sơ."""
    dead = _customer(db, "Người chết", ngay_chet=date(2020, 1, 1))
    uq = _customer(db, "Người nhận UQ")
    prop = _property(db, "AA0008")
    case = _case(db, dead, prop, uq_id=uq.id)

    cases_router.delete(case.id, db=db)

    assert db.get(InheritanceCase, case.id) is None
    assert db.get(Customer, uq.id) is not None   # danh bạ còn nguyên


def test_delete_uq_reference_of_other_case_blocks_cleanup(db):
    """Customer của hồ sơ bị xóa nhưng là người nhận UQ của hồ sơ khác
    → vẫn giữ (tham chiếu từ danh mục ủy quyền)."""
    dead_a = _customer(db, "Dead A", ngay_chet=date(2020, 1, 1))
    dead_b = _customer(db, "Dead B", ngay_chet=date(2020, 1, 1))
    pa = _property(db, "AA0009")
    pb = _property(db, "AA0010")
    case_a = _case(db, dead_a, pa)
    _case(db, dead_b, pb, uq_id=dead_a.id)   # dead_a là UQ của case B

    cases_router.delete(case_a.id, db=db)

    assert db.get(Customer, dead_a.id) is not None


def test_delete_respects_surviving_case_snapshot_refs(db):
    """Snapshot case_state_json của hồ sơ còn tồn tại trỏ entity_id →
    chặn dọn master dù bảng quan hệ không còn."""
    dead_a = _customer(db, "Dead A", ngay_chet=date(2020, 1, 1))
    dead_b = _customer(db, "Dead B", ngay_chet=date(2020, 1, 1))
    snap_person = _customer(db, "Người chỉ trong snapshot")
    snap_prop = _property(db, "SNAP01")
    pa = _property(db, "AA0011")
    pb = _property(db, "AA0012")
    case_a = _case(db, dead_a, pa,
                   participants=[(snap_person, None)],
                   extra_props=[snap_prop])
    _case(db, dead_b, pb,
          snapshot=_snapshot(people_ids=[snap_person.id],
                             asset_ids=[snap_prop.id]))

    cases_router.delete(case_a.id, db=db)

    assert db.get(Customer, snap_person.id) is not None
    assert db.get(Property, snap_prop.id) is not None
    assert db.get(Customer, dead_a.id) is None
    assert db.get(Property, pa.id) is None


def test_delete_cascades_land_rows_with_property(db):
    dead = _customer(db, "Người chết", ngay_chet=date(2020, 1, 1))
    prop = _property(db, "AA0013")
    db.add(PropertyLandRow(
        property_id=prop.id, vitri=1,
        loaidat="Đất ở", dientich=100.0, thoihan="Lâu dài"))
    case = _case(db, dead, prop)
    db.flush()

    cases_router.delete(case.id, db=db)

    assert db.get(Property, prop.id) is None
    assert db.query(PropertyLandRow).count() == 0


def test_delete_rollback_keeps_everything_on_error(db, monkeypatch):
    """Lỗi giữa transaction → rollback: hồ sơ + master + participant
    vẫn nguyên vẹn."""
    dead = _customer(db, "Người chết", ngay_chet=date(2020, 1, 1))
    heir = _customer(db, "Người thừa kế")
    prop = _property(db, "AA0021")
    case = _case(db, dead, prop, participants=[(heir, None)])

    def _boom(_db):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(cases_router, "_live_master_refs", _boom)
    with pytest.raises(RuntimeError):
        cases_router.delete(case.id, db=db)

    assert db.get(InheritanceCase, case.id) is not None
    assert db.get(Customer, dead.id) is not None
    assert db.get(Customer, heir.id) is not None
    assert db.get(Property, prop.id) is not None
    assert db.query(InheritanceParticipant).count() == 1


def test_delete_preserves_unrelated_orphan_catalog(db):
    """Danh bạ trơ không gắn hồ sơ nào — không bị quét xóa."""
    dead = _customer(db, "Người chết", ngay_chet=date(2020, 1, 1))
    stray = _customer(db, "Danh bạ trơ")
    stray_prop = _property(db, "AA0015")
    prop = _property(db, "AA0014")
    case = _case(db, dead, prop)

    cases_router.delete(case.id, db=db)

    assert db.get(Customer, stray.id) is not None
    assert db.get(Property, stray_prop.id) is not None


# --------------------------------------------------------------- thống kê


def test_stats_count_case_linked_entities_only(db):
    dead = _customer(db, "Người chết", ngay_chet=date(2020, 1, 1))
    heir = _customer(db, "Người thừa kế")
    parent = _customer(db, "Cha/mẹ")
    uq = _customer(db, "Người nhận UQ")
    prop = _property(db, "AA0016")
    extra = _property(db, "AA0017")
    _customer(db, "Danh bạ trơ 1")
    _customer(db, "Danh bạ trơ 2")
    _property(db, "TRƠ01")
    _case(db, dead, prop, uq_id=uq.id, extra_props=[extra],
          participants=[(heir, parent)])

    cust_ids, prop_ids = cases_router._live_master_refs(db)
    assert cust_ids == {dead.id, heir.id, parent.id, uq.id}
    assert prop_ids == {prop.id, extra.id}


def test_stats_distinct_primary_and_link(db):
    """Tài sản vừa là primary của case A vừa link phụ của case B →
    đếm một lần."""
    dead_a = _customer(db, "Dead A", ngay_chet=date(2020, 1, 1))
    dead_b = _customer(db, "Dead B", ngay_chet=date(2020, 1, 1))
    prop = _property(db, "AA0018")
    other = _property(db, "AA0019")
    _case(db, dead_a, prop)
    _case(db, dead_b, other, extra_props=[prop])

    cust_ids, prop_ids = cases_router._live_master_refs(db)
    assert cust_ids == {dead_a.id, dead_b.id}
    assert prop_ids == {prop.id, other.id}


def test_stats_endpoint_response_shape(db, session_factory, monkeypatch):
    """Endpoint /api/stats trả cùng key, đếm theo tham chiếu sống."""
    import main as main_mod

    dead = _customer(db, "Người chết", ngay_chet=date(2020, 1, 1))
    prop = _property(db, "AA0020")
    _customer(db, "Danh bạ trơ")
    _case(db, dead, prop, trang_thai="locked")

    monkeypatch.setattr(database, "SessionLocal", session_factory)
    out = asyncio.run(main_mod.stats())
    assert out == {"customers": 1, "properties": 1, "cases": 1, "locked": 1}

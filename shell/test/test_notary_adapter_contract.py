"""Contract test cho adapter handlers MIN-107 (notary.case-drafting.v1).

Hermetic: `_db_session` → session SQLite temp, `_svc` → module
`services.case_workspace` that import tu `notary_v2/` trong repo.
Khong cham `notary_v2/notary.db` that, khong can engine-roots.json.
"""
import sys
import uuid
from datetime import date
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SHELL = _HERE.parent
_REPO = _SHELL.parent
sys.path.insert(0, str(_SHELL / "sidecar"))
sys.path.insert(0, str(_REPO / "notary_v2"))

import command_registry as reg  # noqa: E402
import notary_adapter  # noqa: E402
from errors import CommandError  # noqa: E402

from database import Base  # noqa: E402
from models import Customer, InheritanceCase, Property  # noqa: E402
import services.case_workspace as case_workspace  # noqa: E402

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402


class _Job:
    """Stub Job — chi can check_cancel()."""

    def check_cancel(self):
        return None


@pytest.fixture()
def adapter_db(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'adapter.db'}",
        connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(notary_adapter, "_db_session", lambda: Session())
    monkeypatch.setattr(
        notary_adapter, "_svc",
        lambda name: case_workspace if name == "case_workspace"
        else pytest.fail(f"unexpected _svc({name!r})"))
    sess = Session()
    yield sess
    sess.close()


def _seed_case(sess, locked=False, loai_van_ban="khai_nhan"):
    deceased = Customer(ho_ten="Nguyen Van Xuat", ngay_chet=date(2020, 1, 1))
    prop = Property(so_serial="AA123456", dia_chi="1 duong test")
    sess.add_all([deceased, prop])
    sess.flush()
    case = InheritanceCase(
        nguoi_chet_id=deceased.id, tai_san_id=prop.id,
        ngay_lap_ho_so=date(2026, 9, 1), loai_van_ban=loai_van_ban,
        trang_thai="locked" if locked else "draft")
    sess.add(case)
    sess.commit()
    return case, deceased, prop


def _uuid4():
    return str(uuid.uuid4())


def _person_row(entity_id=None, **kw):
    row = {
        "row_id": _uuid4(), "entity_id": entity_id,
        "ho_ten": "Nguyen Van Xuat", "gioi_tinh": "Nam",
        "ngay_sinh": "1950-01-01", "ngay_chet": "2020-01-01",
        "so_giay_to": None, "ngay_cap": None, "noi_cap": None,
        "dia_chi": None, "place_of_origin": None,
    }
    row.update(kw)
    return row


def _asset_row(entity_id=None, **kw):
    row = {
        "row_id": _uuid4(), "entity_id": entity_id, "is_primary": True,
        "so_serial": "AA123456", "so_vao_so": None, "so_thua_dat": None,
        "so_to_ban_do": None, "dia_chi": "1 duong test", "loai_so": None,
        "hinh_thuc_su_dung": None, "thoi_han": None, "nguon_goc": None,
        "ngay_cap": None, "co_quan_cap": None, "land_rows": None,
    }
    row.update(kw)
    return row


def _commit_payload(case_id, base_revision, people, assets):
    return {"case_id": case_id, "base_revision": base_revision,
            "stage": {"people": people, "assets": assets}}


# ---------------------------------------------------------------- registry


def test_registry_wires_workspace_commands():
    assert "notary.workspace_get" in reg.COMMANDS
    assert "notary.workspace_commit_stage" in reg.COMMANDS
    assert callable(reg.COMMANDS["notary.workspace_get"])
    assert callable(reg.COMMANDS["notary.workspace_commit_stage"])


# ----------------------------------------------------------- workspace_get


def test_workspace_get_contract_shape(adapter_db):
    case, deceased, prop = _seed_case(adapter_db)
    res = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    assert res["kind"] == "workspace_get"
    data = res["data"]
    assert data["schema_version"] == "notary.case-drafting.v1"
    assert data["backend_mode"] == "real"
    case_info = data["case"]
    assert case_info["id"] == case.id
    assert case_info["case_type"] == "inheritance"
    assert case_info["document_type"] == "khai_nhan"
    assert case_info["status"] == "draft"
    assert case_info["locked"] is False
    assert case_info["revision"] == 1
    assert len(data["stage"]["people"]) == 1
    assert len(data["stage"]["assets"]) == 1
    assert data["stage"]["assets"][0]["is_primary"] is True
    assert data["diagram"]["state"]["version"] == 2
    assert isinstance(data["diagram"]["state"]["nodes"], list)
    assert data["capabilities"]["diagram"] is True


def test_workspace_get_missing_case_is_structured(adapter_db):
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_get(_Job(), {"case_id": 9999})
    assert exc.value.code == "case_not_found"
    assert exc.value.retryable is False


def test_workspace_get_requires_case_id(adapter_db):
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_get(_Job(), {})
    assert exc.value.code == "validation_error"


# -------------------------------------------------- workspace_commit_stage


def test_workspace_commit_stage_contract_shape(adapter_db):
    case, deceased, prop = _seed_case(adapter_db)
    res = notary_adapter.workspace_commit_stage(
        _Job(), _commit_payload(
            case.id, 1,
            [_person_row(entity_id=deceased.id)],
            [_asset_row(entity_id=prop.id)]))
    assert res["kind"] == "workspace_commit_stage"
    data = res["data"]
    assert data["schema_version"] == "notary.case-drafting.v1"
    assert data["revision"] == 2
    assert data["stage"]["people"][0]["entity_id"] == deceased.id
    assert data["stage"]["assets"][0]["entity_id"] == prop.id
    assert data["diagram"]["render_model"] is not None
    adapter_db.refresh(case)
    assert case.workspace_revision == 2


def test_workspace_commit_stage_stale_revision_maps_conflict(adapter_db):
    case, deceased, prop = _seed_case(adapter_db)
    payload = _commit_payload(
        case.id, 1, [_person_row(entity_id=deceased.id)],
        [_asset_row(entity_id=prop.id)])
    notary_adapter.workspace_commit_stage(_Job(), payload)  # rev 1 → 2
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), payload)  # rev 1 stale
    err = exc.value
    assert err.code == "workspace_conflict"
    assert err.retryable is True
    assert err.next_action == "call notary.workspace_get"
    assert err.details["server_revision"] == 2


def test_workspace_commit_stage_ahead_revision_maps_conflict(adapter_db):
    case, _deceased, _prop = _seed_case(adapter_db)
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(
            _Job(), _commit_payload(case.id, 99, [], []))
    assert exc.value.code == "workspace_conflict"
    assert exc.value.details["server_revision"] == 1


def test_workspace_commit_stage_locked_maps_error(adapter_db):
    case, deceased, prop = _seed_case(adapter_db, locked=True)
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(
            _Job(), _commit_payload(
                case.id, 1, [_person_row(entity_id=deceased.id)],
                [_asset_row(entity_id=prop.id)]))
    err = exc.value
    assert err.code == "workspace_locked"
    assert err.retryable is False


def test_workspace_commit_stage_invalid_row_maps_error(adapter_db):
    case, _deceased, _prop = _seed_case(adapter_db)
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(
            _Job(), _commit_payload(
                case.id, 1, [_person_row(ho_ten="   ")], []))
    err = exc.value
    assert err.code == "stage_validation_error"
    assert err.retryable is True
    assert err.details["field_errors"]


def test_workspace_commit_stage_bad_payload_shape(adapter_db):
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(
            _Job(), {"case_id": 1, "base_revision": 1})
    assert exc.value.code == "validation_error"
    with pytest.raises(CommandError) as exc2:
        notary_adapter.workspace_commit_stage(
            _Job(), {"case_id": 1, "base_revision": 1,
                     "stage": {"people": "x", "assets": []}})
    assert exc2.value.code == "validation_error"

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
from models import (Customer, InheritanceCase, InheritanceParticipant,  # noqa: E402
                    Property)
import services.case_workspace as case_workspace  # noqa: E402
import services.inheritance_workspace as inheritance_workspace  # noqa: E402
import services.word_batch_export as word_batch_export  # noqa: E402

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402


class _Job:
    """Stub Job — check_cancel (co the mang result) + report_progress."""

    def check_cancel(self, result=None):
        return None

    def report_progress(self, done, total, label=""):
        self.progress = {"done": done, "total": total,
                         "current_label": label}


@pytest.fixture()
def adapter_db(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'adapter.db'}",
        connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(notary_adapter, "_db_session", lambda: Session())
    svc_modules = {"case_workspace": case_workspace,
                   "inheritance_workspace": inheritance_workspace,
                   "word_batch_export": word_batch_export}
    monkeypatch.setattr(
        notary_adapter, "_svc",
        lambda name: svc_modules.get(name)
        or pytest.fail(f"unexpected _svc({name!r})"))
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
    assert err.next_action == "retry"  # envelope enum, khong phai command name
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
    assert err.retryable is False  # payload sai — retry mu van sai
    assert err.next_action is None
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


# ------------------------------------------------- diagram_evaluate / save


def _diagram_node(nid, person_id=None, parents=(), spouse=None,
                  owner=False, receive=True):
    return {"id": nid, "personId": person_id,
            "parentSlotIds": list(parents), "spouseSlotId": spouse,
            "isLandOwner": owner, "willReceive": receive,
            "hidden": False, "deleted": False}


def _committed_case(adapter_db):
    """Seed case + commit Stage qua service that → (case, owner_row_id).

    Revision sau commit = 2. Person duy nhat la nguoi chet → draft hop le
    nhat = owner slot isLandOwner (engine: estate unresolved, status
    incomplete — du de kiem wire shape)."""
    case, deceased, prop = _seed_case(adapter_db)
    res = case_workspace.CaseWorkspaceService(adapter_db).commit_stage(
        case.id, 1, [_person_row(entity_id=deceased.id)],
        [_asset_row(entity_id=prop.id)])
    row_id = res["stage"]["people"][0]["row_id"]
    return case, row_id


def _eval_payload(case_id, state):
    return {"case_id": case_id, "diagram": {"state": state}}


def _save_payload(case_id, base_revision, state):
    return {"case_id": case_id, "base_revision": base_revision,
            "diagram": {"state": state}}


def test_diagram_evaluate_contract_shape(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = {"version": 2, "nodes": [
        _diagram_node("owner", owner_row, owner=True, receive=False)]}
    res = notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert res["kind"] == "diagram_evaluate"
    data = res["data"]
    assert data["schema_version"] == "notary.case-drafting.v1"
    assert data["evaluated_revision"] == 2
    rm = data["render_model"]
    assert rm["engineVersion"] == 2
    assert rm["status"] in ("incomplete", "complete", "invalid")
    assert rm["allocations"][owner_row]["baseShare"] == "1"


def test_diagram_evaluate_outside_stage_maps_error(adapter_db):
    case, _owner_row = _committed_case(adapter_db)
    outside = str(uuid.uuid4())
    state = {"version": 2, "nodes": [
        _diagram_node("owner", outside, owner=True)]}
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    err = exc.value
    assert err.code == "diagram_reference_outside_stage"
    assert err.retryable is False
    assert err.details["personId"] == outside


def test_diagram_evaluate_invalid_state_maps_error(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = {"version": 2, "nodes": [
        _diagram_node("owner", owner_row, owner=True, receive=False),
        _diagram_node("child", None, parents=("ghost_slot",))]}
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    err = exc.value
    assert err.code == "diagram_invalid_state"
    assert any(e["code"] == "dangling_parent"
           for e in err.details["errors"])


def test_diagram_evaluate_missing_diagram_is_validation_error(adapter_db):
    case, _ = _committed_case(adapter_db)
    for bad in ({}, {"diagram": None}, {"diagram": {}},
                {"diagram": {"stae": {}}}):
        p = {"case_id": case.id}
        p.update(bad)
        with pytest.raises(CommandError) as exc:
            notary_adapter.diagram_evaluate(_Job(), p)
        assert exc.value.code == "validation_error", bad


def test_diagram_evaluate_allowed_on_locked_case(adapter_db):
    case, _deceased, _prop = _seed_case(adapter_db, locked=True)
    state = {"version": 2, "nodes": []}
    res = notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert res["kind"] == "diagram_evaluate"
    assert res["data"]["evaluated_revision"] == 1


def test_diagram_save_persists_and_bumps_revision(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = {"version": 2, "nodes": [
        _diagram_node("owner", owner_row, owner=True, receive=False)]}
    res = notary_adapter.diagram_save(
        _Job(), _save_payload(case.id, 2, state))
    assert res["kind"] == "diagram_save"
    data = res["data"]
    assert data["schema_version"] == "notary.case-drafting.v1"
    assert data["revision"] == 3
    assert data["diagram"]["state"] == state
    assert data["diagram"]["render_model"]["engineVersion"] == 2
    adapter_db.refresh(case)
    assert case.workspace_revision == 3


def test_diagram_save_conflict_maps_retryable(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = {"version": 2, "nodes": [
        _diagram_node("owner", owner_row, owner=True)]}
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(_Job(), _save_payload(case.id, 1, state))
    err = exc.value
    assert err.code == "workspace_conflict"
    assert err.retryable is True
    assert err.next_action == "retry"
    assert err.details["server_revision"] == 2


def test_diagram_save_locked_maps_error(adapter_db):
    case, _deceased, _prop = _seed_case(adapter_db, locked=True)
    state = {"version": 2, "nodes": []}
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(_Job(), _save_payload(case.id, 1, state))
    assert exc.value.code == "workspace_locked"


def test_diagram_save_missing_diagram_is_validation_error(adapter_db):
    case, _ = _committed_case(adapter_db)
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(
            _Job(), {"case_id": case.id, "base_revision": 2})
    assert exc.value.code == "validation_error"


# ------------------------------------- word_export_options/batch (MIN-110)


def _seed_word_ready_case(sess, locked=False):
    """Case du dieu kien xuat Word: chu dat da chet + tai san + nguoi nhan
    (participants fallback path — khong can case_state_json)."""
    case, _deceased, _prop = _seed_case(sess, locked=locked)
    heir = Customer(ho_ten="Nguyen Thi Con")
    sess.add(heir)
    sess.flush()
    sess.add(InheritanceParticipant(
        ho_so_id=case.id, customer_id=heir.id,
        vai_tro="Con", co_nhan_tai_san=True, ty_le=100.0))
    sess.commit()
    return case


def _dest(tmp_path):
    return {"path": str(tmp_path), "scope": "machine_local", "is_dir": True}


def test_registry_wires_word_commands():
    assert "notary.word_export_options" in reg.COMMANDS
    assert "notary.word_export_batch" in reg.COMMANDS
    assert callable(reg.COMMANDS["notary.word_export_options"])
    assert callable(reg.COMMANDS["notary.word_export_batch"])


def test_word_export_options_ready_case(adapter_db):
    case = _seed_word_ready_case(adapter_db)
    res = notary_adapter.word_export_options(_Job(), {"case_id": case.id})
    assert res["kind"] == "word_export_options"
    data = res["data"]
    assert data["schema_version"] == "notary.case-drafting.v1"
    docs = {d["document_key"]: d for d in data["documents"]}
    assert set(docs) == {"khai_nhan_di_san", "thoa_thuan_phan_chia",
                       "niem_yet"}
    assert docs["khai_nhan_di_san"]["ready"] is True
    assert docs["khai_nhan_di_san"]["block_reason"] is None
    assert docs["niem_yet"]["ready"] is False
    assert docs["niem_yet"]["block_reason"] == "word.template_missing"


def test_word_export_options_locked_case_still_readonly(adapter_db):
    # options la read-only — locked case khong bi workspace_locked (§5.3).
    case = _seed_word_ready_case(adapter_db, locked=True)
    res = notary_adapter.word_export_options(_Job(), {"case_id": case.id})
    assert res["data"]["documents"][0]["document_key"]


def test_word_export_options_missing_case(adapter_db):
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_options(_Job(), {"case_id": 9999})
    assert exc.value.code == "case_not_found"


def test_word_export_batch_writes_docx(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    res = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id,
        "document_keys": ["khai_nhan_di_san", "thoa_thuan_phan_chia"],
        "destination": _dest(tmp_path)})
    assert res["kind"] == "word_export_batch"
    assert res.get("partial") is not True
    data = res["data"]
    assert data["schema_version"] == "notary.case-drafting.v1"
    assert data["destination"]["is_dir"] is True
    assert data["breakdown"] == {
        "succeeded": ["khai_nhan_di_san", "thoa_thuan_phan_chia"],
        "failed": [], "skipped": []}
    import docx
    for d in data["documents"]:
        assert d["status"] == "saved"
        assert d["error"] is None
        assert ".." not in d["actual_filename"]
        out = Path(d["output_file"]["path"])
        assert out.parent == tmp_path       # ghi thang vao destination
        assert out.is_file()
        docx.Document(str(out))             # DOCX that, mo duoc


def test_word_export_batch_collision_suffix(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    old = tmp_path / f"Van_ban_khai_nhan_di_san_HS-{case.id}.docx"
    old.write_bytes(b"cu")
    res = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id,
        "document_keys": ["khai_nhan_di_san"],
        "destination": _dest(tmp_path)})
    d = res["data"]["documents"][0]
    assert d["actual_filename"] == (
        f"Van_ban_khai_nhan_di_san_HS-{case.id}_2.docx")
    assert old.read_bytes() == b"cu"        # khong bao gio ghi de


def test_word_export_batch_partial(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    res = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id,
        "document_keys": ["khai_nhan_di_san", "niem_yet"],
        "destination": _dest(tmp_path)})
    assert res["partial"] is True           # marker jobstore -> partial
    docs = {d["document_key"]: d for d in res["data"]["documents"]}
    assert docs["khai_nhan_di_san"]["status"] == "saved"
    assert docs["niem_yet"]["status"] == "failed"
    assert docs["niem_yet"]["error"]["code"] == "word.template_missing"
    assert res["data"]["breakdown"]["failed"] == ["niem_yet"]


def test_word_export_batch_all_failed_keeps_result(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id,
            "document_keys": ["niem_yet"],
            "destination": _dest(tmp_path)})
    err = exc.value
    assert err.code == "word_batch_failed"
    assert err.retryable is True
    assert err.next_action == "retry"
    assert err.details["documents"][0]["code"] == "word.template_missing"
    # Result giu lai tren wire — breakdown + per-file errors (§8.4).
    assert err.result["kind"] == "word_export_batch"
    assert err.result["data"]["breakdown"]["failed"] == ["niem_yet"]
    assert list(tmp_path.glob("*.docx")) == []


def test_word_export_batch_validates_before_writing(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    # document_keys rong -> word_no_documents_selected
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id, "document_keys": [],
            "destination": _dest(tmp_path)})
    assert exc.value.code == "word_no_documents_selected"
    # key trung / ngoai catalog
    for keys, code in (
            (["khai_nhan_di_san", "khai_nhan_di_san"],
             "word_duplicate_document_key"),
            (["khong_co"], "word_unknown_document_key"),
            ("khai_nhan_di_san", "validation_error")):
        with pytest.raises(CommandError) as exc:
            notary_adapter.word_export_batch(_Job(), {
                "case_id": case.id, "document_keys": keys,
                "destination": _dest(tmp_path)})
        assert exc.value.code == code, (keys, exc.value.code)
    assert list(tmp_path.glob("*.docx")) == []  # chua file nao duoc tao


def test_word_export_batch_destination_rules(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    # is_dir thieu/false -> validation_error
    for bad in ({"path": str(tmp_path), "scope": "machine_local"},
                {"path": str(tmp_path), "scope": "machine_local",
                 "is_dir": False}):
        with pytest.raises(CommandError) as exc:
            notary_adapter.word_export_batch(_Job(), {
                "case_id": case.id, "document_keys": ["khai_nhan_di_san"],
                "destination": bad})
        assert exc.value.code == "validation_error"
    # folder khong ton tai -> file_not_found
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id, "document_keys": ["khai_nhan_di_san"],
            "destination": _dest(tmp_path / "khong-co")})
    assert exc.value.code == "file_not_found"
    # destination tro toi FILE -> file_not_found
    f = tmp_path / "file.txt"
    f.write_text("x")
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id, "document_keys": ["khai_nhan_di_san"],
            "destination": {"path": str(f), "scope": "machine_local",
                            "is_dir": True}})
    assert exc.value.code == "file_not_found"


def test_word_export_batch_locked_case(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db, locked=True)
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id, "document_keys": ["khai_nhan_di_san"],
            "destination": _dest(tmp_path)})
    assert exc.value.code == "workspace_locked"

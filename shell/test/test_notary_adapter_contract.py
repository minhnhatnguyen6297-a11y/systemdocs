"""Contract test cho adapter handlers MIN-107 → MIN-128
(notary.case-drafting.v2 §13).

Hermetic: `_db_session` → session SQLite temp, `_svc` → module
`services.*` that import tu `notary_v2/` trong repo. Khong cham
`notary_v2/notary.db` that, khong can engine-roots.json.

v2 wire (§13): stage `{owner_row_id?, people[], assets[]}` — owner_row_id
bat buoc voi inheritance, cam voi two_party; diagram_state v3 {version:3,
domain, nodes}; node inheritance {id, personId, parentSlotIds, spouseSlotId,
ownPositions, receivePositions, hidden, deleted}; two_party canonical
30 slot p1..p30. is_primary/isLandOwner/willReceive bi cam tren wire.
"""
import os
import subprocess
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event

_HERE = Path(__file__).resolve().parent
_SHELL = _HERE.parent
_REPO = _SHELL.parent
sys.path.insert(0, str(_SHELL / "sidecar"))
sys.path.insert(0, str(_REPO / "notary_v2"))

import command_registry as reg  # noqa: E402
import notary_adapter  # noqa: E402
from errors import CommandError  # noqa: E402

from database import Base  # noqa: E402
import models as engine_models  # noqa: E402
from models import (CaseAssetRow, CasePersonRow, Customer,  # noqa: E402
                    InheritanceCase, InheritanceCaseProperty,
                    InheritanceParticipant, Property)
import services.case_workspace as case_workspace  # noqa: E402
import services.inheritance_workspace as inheritance_workspace  # noqa: E402
import services.word_batch_export as word_batch_export  # noqa: E402

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

SCHEMA = "notary.case-drafting.v2"
TP_IDS = [f"p{i}" for i in range(1, 31)]
# file_ref chỉ nhận path Windows tuyệt đối (C:\...) — trên POSIX tmp_path
# không qua validate_file_ref, nên các ca destination/template_dir được skip.
WINDOWS_ONLY = pytest.mark.skipif(
    os.name != "nt", reason="file_ref yêu cầu path tuyệt đối Windows")


@WINDOWS_ONLY
def test_original_docx_two_party_adapter_lifecycle_stale_guard_and_subfolder(adapter_db, tmp_path, monkeypatch):
    """Real intake → saved two-party rows/seats → exact original export, with stale no-write."""
    import json
    import hashlib
    from docx import Document
    from services.document_intake import service as intake_service
    from services.document_intake.docx_store import DocxStore
    from services.document_intake.docx_source import read_docx
    from services import word_original
    store = DocxStore(tmp_path / 'sources')
    modules = {'document_intake.service':intake_service, 'word_original':word_original,
               'word_batch_export':word_batch_export, 'case_workspace':case_workspace}
    monkeypatch.setattr(notary_adapter, '_svc', lambda name: modules[name])
    monkeypatch.setattr(notary_adapter, '_docx_store', lambda: store)
    document = Document()
    for line in ['HỢP ĐỒNG CHUYỂN NHƯỢNG', 'Bên A:',
        'Ông: Nguyễn Văn Mẫu, sinh ngày 1/2/1980; CCCD: 001234567890; thường trú: Nhà A',
        'Bên B:', 'Bà: Trần Thị Mẫu, sinh ngày 3/4/1985; CCCD: 001234567891; thường trú: Nhà B',
        'Tài sản 1:', 'Serial: ZZ123456; có địa chỉ tại: Nhà đất A',
        'Loại đất: ONT; Diện tích: 50; Thời hạn: Lâu dài',
        'Tài sản 2:', 'Serial: YY123456; có địa chỉ tại: Nhà đất B',
        'Loại đất: CLN; Diện tích: 90; Thời hạn: 2050', 'Điều 2: Nội dung tĩnh giữ nguyên']:
        document.add_paragraph(line)
    path = tmp_path / 'Hợp đồng mẫu.docx'; document.save(path)
    original = path.read_bytes()
    analyzed = notary_adapter.intake_analyze(_Job(), {'sources':[{'source_id':_uuid4(),'kind':'docx',
        'file_ref':{'path':str(path),'scope':'machine_local','size_bytes':len(original)}}]})['data']
    assert len(analyzed['suggestions']) == 4
    people, assets, records = [], [], []
    ref = analyzed['suggestions'][0]['fields']['ho_ten']['source_refs'][0]
    for candidate in analyzed['suggestions']:
        values = {k:f['normalized_value'] for k,f in candidate['fields'].items()}
        if 'land_rows' in values: values['land_rows'] = json.loads(values['land_rows'])
        row = _person_row(ngay_chet=None, **values) if candidate['target']=='person' else _asset_row(**values)
        (people if candidate['target']=='person' else assets).append(row)
        records.append({'candidate_id':candidate['suggestion_id'],'row_id':row['row_id']})
    context = {'version':1,'sources':[{'source_id':ref['source_id'],'sha256':ref['source_sha256'],'records':records,'bindings':[]}]}
    created = notary_adapter.workspace_create(_Job(), {'idempotency_key':_uuid4(),
        'case':{'case_type':'two_party','document_type':'chuyen_nhuong'},'stage':{'people':people,'assets':assets},
        'diagram':{'state':_tp_state(assign={'p17':people[0]['row_id'],'p2':people[1]['row_id']})},'docx_import':context})['data']
    cid = created['case']['id']; source_id = ref['source_id']
    options = notary_adapter.word_export_options(_Job(),{'case_id':cid,'original_source_id':source_id})['data']
    names = [p for p in options['binding_proposals'] if p['field_key']=='ho_ten']
    assert [p['slot'] for p in names] == ['[Bên B 2 - Họ tên]','[Bên A 2 - Họ tên]']
    assert created['docx_import']['sources'][0]['label'] == path.name
    created['stage']['people'][0]['ho_ten'] = 'Tên B đã kiểm tra'
    context = created['docx_import']; context['sources'][0]['bindings'] = [
        {k:p[k] for k in ('candidate_id','occurrence_id','field_key','slot')} for p in options['binding_proposals'] if p['supported']]
    committed = notary_adapter.workspace_commit_stage(_Job(),{'case_id':cid,'base_revision':1,
        'stage':created['stage'],'docx_import':context})['data']
    loaded = notary_adapter.workspace_get(_Job(),{'case_id':cid})['data']
    assert loaded['docx_import'] == committed['docx_import']
    dest = tmp_path / 'exports'; dest.mkdir()
    payload = {'case_id':cid,'document_keys':['original.docx'],'original_source_id':source_id,
        'base_revision':1,'destination':_dest(dest),'create_case_subdir':True}
    with pytest.raises(CommandError) as err:
        notary_adapter.word_export_batch(_Job(),payload)
    assert err.value.code == 'workspace_conflict'
    assert list(dest.iterdir()) == []
    payload['base_revision'] = committed['revision']
    exported = notary_adapter.word_export_batch(_Job(),payload)['data']
    assert exported['destination'] == _dest(dest)
    output = Path(exported['documents'][0]['output_file']['path'])
    assert output.parent == dest / f'HS-{cid}' and output.is_file()
    text = read_docx(output.read_bytes()).text
    assert 'Tên B đã kiểm tra' in text and 'Trần Thị Mẫu' in text and 'Nội dung tĩnh giữ nguyên' in text
    assert hashlib.sha256(path.read_bytes()).hexdigest() == hashlib.sha256(original).hexdigest()
    # A file occupying the child-folder name must produce a Word error, not a raw OS exception.
    blocked_dest = tmp_path / 'blocked-exports'; blocked_dest.mkdir()
    (blocked_dest / f'HS-{cid}').write_text('existing file', encoding='utf-8')
    payload['destination'] = _dest(blocked_dest)
    with pytest.raises(CommandError) as err:
        notary_adapter.word_export_batch(_Job(), payload)
    assert err.value.code == 'word.render_failed'
    assert (blocked_dest / f'HS-{cid}').read_text(encoding='utf-8') == 'existing file'
    mkdir = Path.mkdir
    def locked_child(folder, *args, **kwargs):
        if folder.name == f'HS-{cid}': raise PermissionError('locked folder')
        return mkdir(folder, *args, **kwargs)
    payload['destination'] = _dest(dest)
    with monkeypatch.context() as patch:
        patch.setattr(Path, 'mkdir', locked_child)
        with pytest.raises(CommandError) as err:
            notary_adapter.word_export_batch(_Job(), payload)
        assert err.value.code == 'file_locked'
    assert list(output.parent.iterdir()) == [output]


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


def _seed_case(sess, loai_van_ban="khai_nhan"):
    """Case + rows Storage B: một chủ đất (identity anchor khớp
    `_person_row`) và một tài sản (serial khớp `_asset_row`)."""
    import json
    deceased = Customer(
        ho_ten="Nguyen Van Xuat", gioi_tinh="Nam",
        ngay_chet=date(2020, 1, 1), so_giay_to="001122334455",
        name_anchor="nguyen van xuat", document_anchor="001122334455")
    prop = Property(so_serial="AA123456", dia_chi="1 duong test")
    sess.add_all([deceased, prop])
    sess.flush()
    case = InheritanceCase(
        nguoi_chet_id=deceased.id, tai_san_id=prop.id,
        ngay_lap_ho_so=date(2026, 9, 1), loai_van_ban=loai_van_ban,
        trang_thai="draft")
    sess.add(case)
    sess.flush()
    person_row_id = str(uuid.uuid4())
    asset_row_id = str(uuid.uuid4())
    sess.add(CasePersonRow(
        row_id=person_row_id, case_id=case.id, customer_id=deceased.id,
        vitri=1, ho_ten=deceased.ho_ten, gioi_tinh="Nam",
        ngay_sinh="1950-01-01", ngay_chet="2020-01-01",
        so_giay_to=deceased.so_giay_to))
    sess.add(CaseAssetRow(
        row_id=asset_row_id, case_id=case.id, property_id=prop.id,
        vitri=1, so_serial=prop.so_serial, dia_chi=prop.dia_chi,
        land_rows_present=False))
    sess.add(InheritanceCaseProperty(
        case_id=case.id, case_asset_row_id=asset_row_id,
        property_id=prop.id, is_primary=True))
    case_type = ("two_party" if loai_van_ban in
                 ("chuyen_nhuong", "tang_cho", "cho_thue", "dat_coc")
                 else "inheritance")
    if case_type == "inheritance":
        payload = {
            "schemaVersion": 4, "case": {}, "owner_row_id": person_row_id,
            "diagram": {"state": {
                "version": 3, "domain": "inheritance",
                "nodes": [{"id": "owner", "personId": person_row_id,
                           "parentSlotIds": [], "spouseSlotId": None,
                           "ownPositions": [1], "receivePositions": [],
                           "hidden": False, "deleted": False}]},
                "render_model": None}}
    else:
        payload = {
            "schemaVersion": 4, "case": {},
            "diagram": {"state": {
                "version": 3, "domain": "two_party", "nodes": []},
                "render_model": None}}
    case.case_state_json = json.dumps(payload)
    sess.commit()
    return case, deceased, prop


def _uuid4():
    return str(uuid.uuid4())


def _person_row(entity_id=None, **kw):
    row = {
        "row_id": _uuid4(), "entity_id": entity_id,
        "ho_ten": "Nguyen Van Xuat", "gioi_tinh": "Nam",
        "ngay_sinh": "1950-01-01", "ngay_chet": "2020-01-01",
        "so_giay_to": "001122334455", "ngay_cap": None, "noi_cap": None,
        "dia_chi": None, "place_of_origin": None,
    }
    row.update(kw)
    return row


def _asset_row(entity_id=None, **kw):
    row = {
        "row_id": _uuid4(), "entity_id": entity_id,
        "so_serial": "AA123456", "so_vao_so": None, "so_thua_dat": None,
        "so_to_ban_do": None, "dia_chi": "1 duong test", "loai_so": None,
        "hinh_thuc_su_dung": None, "thoi_han": None, "nguon_goc": None,
        "ngay_cap": None, "co_quan_cap": None, "land_rows": None,
    }
    row.update(kw)
    return row


def _commit_payload(case_id, base_revision, people, assets,
                    owner_row_id="__omit__"):
    """stage_v2 — owner_row_id chi co tren inheritance (§13.1).
    "__omit__" = khong emit key; None/string khac = emit gia tri."""
    stage = {"people": people, "assets": assets}
    if owner_row_id != "__omit__":
        stage["owner_row_id"] = owner_row_id
    return {"case_id": case_id, "base_revision": base_revision,
            "stage": stage}


def _commit_inheritance(case_id, base_revision, people, assets):
    """Commit payload inheritance: owner_row_id = people[0].row_id."""
    return _commit_payload(case_id, base_revision, people, assets,
                           owner_row_id=people[0]["row_id"])


def _diagram_node(nid, person_id=None, parents=(), spouse=None,
                  own=(), receive=(), hidden=False, deleted=False):
    """diagram node v3 (§13.4)."""
    return {"id": nid, "personId": person_id,
            "parentSlotIds": list(parents), "spouseSlotId": spouse,
            "ownPositions": list(own), "receivePositions": list(receive),
            "hidden": hidden, "deleted": deleted}


def _v3_state(nodes, domain="inheritance"):
    return {"version": 3, "domain": domain, "nodes": nodes}


def _tp_state(**kw):
    nodes = [{"id": f"p{i}", "personId": None,
              "hidden": False, "deleted": False}
             for i in range(1, 31)]
    for pid, person in (kw.get("assign") or {}).items():
        for n in nodes:
            if n["id"] == pid:
                n["personId"] = person
    return {"version": 3, "domain": "two_party", "nodes": nodes}


# ---------------------------------------------------------------- registry


def test_registry_wires_workspace_commands():
    assert "notary.workspace_get" in reg.COMMANDS
    assert "notary.workspace_source_latest" in reg.COMMANDS
    assert "notary.workspace_commit_stage" in reg.COMMANDS
    assert "notary.workspace_save_case" in reg.COMMANDS
    assert callable(reg.COMMANDS["notary.workspace_get"])
    assert callable(reg.COMMANDS["notary.workspace_source_latest"])
    assert callable(reg.COMMANDS["notary.workspace_commit_stage"])
    assert callable(reg.COMMANDS["notary.workspace_save_case"])


def test_workspace_save_case_new_done_and_idempotent_replay(adapter_db):
    people, assets, state = _create_args()
    payload = _inheritance_create(people, assets, state)
    first = notary_adapter.workspace_save_case(_Job(), payload)
    assert first["kind"] == "workspace_save_case"
    assert first["data"]["created"] is True
    assert first["data"]["case"]["status"] == "done"
    assert first["data"]["case"]["revision"] == 1
    assert len(first["data"]["stage"]["people"]) == 2

    replay = notary_adapter.workspace_save_case(_Job(), payload)
    assert replay["data"]["created"] is False
    assert replay["data"]["case"]["id"] == first["data"]["case"]["id"]
    assert replay["data"]["case"]["revision"] == 1
    assert adapter_db.query(InheritanceCase).count() == 1

    other = _inheritance_create(people, assets, state)
    other["idempotency_key"] = payload["idempotency_key"]
    other["case"] = {"document_type": "khai_nhan", "ghi_chu": "khac"}
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_save_case(_Job(), other)
    assert exc.value.code == "idempotency_conflict"


def test_workspace_save_case_existing_revision_guard(adapter_db):
    case, _deceased, _prop = _seed_case(adapter_db)
    people, assets, state = _create_args()
    payload = _inheritance_create(people, assets, state)
    payload.pop("idempotency_key")
    payload["case_id"] = case.id
    payload["base_revision"] = case.workspace_revision
    saved = notary_adapter.workspace_save_case(_Job(), payload)
    assert saved["data"]["created"] is False
    assert saved["data"]["case"]["status"] == "done"
    assert saved["data"]["case"]["revision"] == 2

    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_save_case(_Job(), payload)
    err = exc.value
    assert err.code == "workspace_conflict"
    assert err.retryable is True
    assert err.next_action == "retry"
    assert err.details["server_revision"] == 2



# ----------------------------------------------------------- workspace_get


def test_workspace_get_contract_shape(adapter_db):
    case, deceased, prop = _seed_case(adapter_db)
    res = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    assert res["kind"] == "workspace_get"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["backend_mode"] == "real"
    case_info = data["case"]
    assert case_info["id"] == case.id
    assert case_info["case_type"] == "inheritance"
    assert case_info["document_type"] == "khai_nhan"
    assert case_info["status"] == "draft"
    assert "locked" not in case_info
    assert case_info["revision"] == 1
    assert len(data["stage"]["people"]) == 1
    assert len(data["stage"]["assets"]) == 1
    # v2: stage inheritance emit owner_row_id; asset khong is_primary.
    assert "owner_row_id" in data["stage"]
    assert "is_primary" not in data["stage"]["assets"][0]
    st = data["diagram"]["state"]
    assert st["version"] == 3
    assert st["domain"] == "inheritance"
    assert isinstance(st["nodes"], list)
    for n in st["nodes"]:
        assert "isLandOwner" not in n and "willReceive" not in n
    assert data["capabilities"]["diagram"] is True
    assert data["capabilities"]["word_export"] is True


def test_workspace_get_two_party(adapter_db):
    """two_party: stage khong owner_row_id; diagram canonical 30 slot;
    render_model unsupported sau commit (§13.5); word_export mo
    (NAIA-8) — readiness chi tiet qua word_export_options."""
    case, deceased, prop = _seed_case(
        adapter_db, loai_van_ban="chuyen_nhuong")
    res = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    data = res["data"]
    assert data["case"]["case_type"] == "two_party"
    assert data["case"]["document_type"] == "chuyen_nhuong"
    assert "owner_row_id" not in data["stage"]
    st = data["diagram"]["state"]
    assert st["domain"] == "two_party"
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    # Chua commit → chua co render (giong inheritance).
    assert data["diagram"]["render_model"] is None
    assert data["capabilities"]["word_export"] is True
    assert data["capabilities"]["diagram"] is True
    # Commit xong → render_model unsupported (engine khong tinh).
    notary_adapter.workspace_commit_stage(
        _Job(), _commit_payload(
            case.id, 1, [_person_row()],
            [_asset_row()]))
    res2 = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    rm = res2["data"]["diagram"]["render_model"]
    assert rm["status"] == "unsupported"
    assert rm["allocations"] == {}


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
        _Job(), _commit_inheritance(
            case.id, 1,
            [_person_row()],
            [_asset_row()]))
    assert res["kind"] == "workspace_commit_stage"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["revision"] == 2
    assert data["stage"]["people"][0]["entity_id"] == deceased.id
    assert data["stage"]["assets"][0]["entity_id"] == prop.id
    assert data["stage"]["owner_row_id"] == \
        data["stage"]["people"][0]["row_id"]
    assert data["diagram"]["render_model"] is not None
    adapter_db.refresh(case)
    assert case.workspace_revision == 2


def test_workspace_commit_stage_owner_required(adapter_db):
    """inheritance: owner_row_id null/missing/khong thuoc people ->
    workspace_owner_required (§13.6)."""
    case, deceased, prop = _seed_case(adapter_db)
    for bad_owner in (None, _uuid4()):
        p = _commit_payload(
            case.id, 1, [_person_row()],
            [_asset_row()])
        p["stage"]["owner_row_id"] = bad_owner
        with pytest.raises(CommandError) as exc:
            notary_adapter.workspace_commit_stage(_Job(), p)
        assert exc.value.code == "workspace_owner_required", bad_owner
    # key hoan toan thieu -> cung owner_required
    p = _commit_payload(
        case.id, 1, [_person_row()],
        [_asset_row()])
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), p)
    assert exc.value.code == "workspace_owner_required"


def test_workspace_commit_stage_owner_syncs_node(adapter_db):
    """§13.6: commit sync node 'owner' (neu co, chua deleted) :=
    owner_row_id — SOT la pointer stage; node khong ton tai thi khong
    tu tao."""
    case, deceased, prop = _seed_case(adapter_db)
    people = [_person_row(),
              _person_row(ho_ten="Tran Thi Binh", ngay_chet=None)]
    # Commit owner=p1 → rev 2.
    p = _commit_payload(case.id, 1, people,
                        [_asset_row()])
    p["stage"]["owner_row_id"] = people[0]["row_id"]
    notary_adapter.workspace_commit_stage(_Job(), p)
    # Persist diagram co node 'owner' (mirror khop pointer) → rev 3.
    notary_adapter.diagram_save(_Job(), _save_payload(
        case.id, 2, _v3_state([
            _diagram_node("owner", people[0]["row_id"], own=[1])])))
    # Commit doi pointer sang p2 → node owner persisted phai theo pointer.
    p2 = _commit_payload(case.id, 3, people,
                         [_asset_row()])
    p2["stage"]["owner_row_id"] = people[1]["row_id"]
    res = notary_adapter.workspace_commit_stage(_Job(), p2)
    nodes = res["data"]["diagram"]["state"]["nodes"]
    owner = next((n for n in nodes if n["id"] == "owner"), None)
    assert owner is not None and owner["personId"] == people[1]["row_id"]


def test_workspace_commit_stage_is_primary_rejected(adapter_db):
    """is_primary bi cam tren wire v2 — field la -> validation_error."""
    case, deceased, prop = _seed_case(adapter_db)
    asset = _asset_row()
    asset["is_primary"] = True
    p = _commit_inheritance(case.id, 1,
                            [_person_row()], [asset])
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), p)
    assert exc.value.code == "validation_error"


def test_workspace_commit_stage_asset_limit(adapter_db):
    case, deceased, prop = _seed_case(adapter_db)
    assets = [_asset_row()] + [
        _asset_row(so_serial=f"AA{i:06d}") for i in range(3)]
    p = _commit_inheritance(
        case.id, 1, [_person_row()], assets)
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), p)
    assert exc.value.code == "stage_validation_error"
    fe = exc.value.details["field_errors"]
    assert any(e["code"] == "asset_limit" for e in fe)


def test_workspace_commit_stage_two_party(adapter_db):
    """two_party commit: khong owner_row_id; canonical 30 slot giu
    personId hop le da assign; render_model unsupported; revision tang."""
    case, deceased, prop = _seed_case(
        adapter_db, loai_van_ban="chuyen_nhuong")
    people = [_person_row()]
    res = notary_adapter.workspace_commit_stage(
        _Job(), _commit_payload(
            case.id, 1, people, [_asset_row()]))
    data = res["data"]
    assert data["revision"] == 2
    assert "owner_row_id" not in data["stage"]
    st = data["diagram"]["state"]
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    # Chua assign qua diagram_save → slot trong.
    assert all(n["personId"] is None for n in st["nodes"])
    assert data["diagram"]["render_model"]["status"] == "unsupported"
    # Assign p1 qua save → commit stage giu nguyen assignment.
    notary_adapter.diagram_save(_Job(), _save_payload(
        case.id, 2, _tp_state(assign={"p1": people[0]["row_id"]})))
    res2 = notary_adapter.workspace_commit_stage(
        _Job(), _commit_payload(
            case.id, 3, people, [_asset_row()]))
    st2 = res2["data"]["diagram"]["state"]
    assert st2["nodes"][0]["personId"] == people[0]["row_id"]


def test_workspace_commit_stage_two_party_owner_row_id_rejected(adapter_db):
    case, deceased, prop = _seed_case(
        adapter_db, loai_van_ban="chuyen_nhuong")
    p = _commit_payload(
        case.id, 1, [_person_row()],
        [_asset_row()])
    p["stage"]["owner_row_id"] = None          # key cam voi two_party
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), p)
    assert exc.value.code == "validation_error"


def test_workspace_commit_stage_two_party_people_limit(adapter_db):
    case, _deceased, _prop = _seed_case(
        adapter_db, loai_van_ban="cho_thue")
    people = [_person_row() for _ in range(31)]
    p = _commit_payload(case.id, 1, people, [])
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), p)
    assert exc.value.code == "stage_validation_error"
    fe = exc.value.details["field_errors"]
    assert any(e["code"] == "people_limit" for e in fe)


def test_workspace_commit_stage_stale_revision_maps_conflict(adapter_db):
    case, deceased, prop = _seed_case(adapter_db)
    payload = _commit_inheritance(
        case.id, 1, [_person_row()],
        [_asset_row()])
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


def test_workspace_commit_stage_invalid_row_maps_error(adapter_db):
    case, _deceased, _prop = _seed_case(adapter_db)
    bad = _person_row(ho_ten="   ")
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(
            _Job(), _commit_inheritance(case.id, 1, [bad], []))
    err = exc.value
    assert err.code == "stage_validation_error"
    assert err.retryable is False  # payload sai — retry mu van sai
    assert err.next_action is None
    assert err.details["field_errors"]


def test_workspace_commit_stage_bad_payload_shape(adapter_db):
    case, _d, _p = _seed_case(adapter_db)
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(
            _Job(), {"case_id": case.id, "base_revision": 1})
    assert exc.value.code == "validation_error"
    # Stage shape sai → validation_error truoc stage field validation.
    for bad_stage in ({"people": "x", "assets": []},
                      "khong-dict", 42):
        with pytest.raises(CommandError) as exc2:
            notary_adapter.workspace_commit_stage(
                _Job(), {"case_id": case.id, "base_revision": 1,
                         "stage": bad_stage})
        assert exc2.value.code == "validation_error", bad_stage


# ------------------------------------- payload.case qua commit (MIN-141 đợt 3)


def test_workspace_commit_stage_case_meta_passes_through(adapter_db):
    """payload.case di tu adapter → service → commit cung transaction:
    ghi cot hồ so + snapshot payload.case canonical; get() emit lai."""
    case, deceased, prop = _seed_case(adapter_db)
    uq = Customer(ho_ten="Nguoi Uy Quyen", gioi_tinh="Nu")
    adapter_db.add(uq)
    adapter_db.commit()  # adapter mo session rieng — phai commit
    stage = {"people": [_person_row()],
             "assets": [_asset_row()],
             "owner_row_id": None}
    stage["owner_row_id"] = stage["people"][0]["row_id"]
    res = notary_adapter.workspace_commit_stage(_Job(), {
        "case_id": case.id, "base_revision": 1, "stage": stage,
        # canonical key — adapter khong doi ten, service fold ve snake.
        "case": {"noiniemyet": "UBND xa Test",
                 "nguoinhanuyquyenid": uq.id,
                 "noidungviec": "Dinh chinh nam sinh",
                 "ghichu": "ghi chu"}})
    assert res["data"]["revision"] == 2
    adapter_db.refresh(case)
    assert case.noi_niem_yet == "UBND xa Test"
    assert case.nguoi_nhan_uy_quyen == "Nguoi Uy Quyen"
    assert case.nguoi_nhan_uy_quyen_id == uq.id
    assert case.noi_dung_viec == "Dinh chinh nam sinh"

    got = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    c = got["data"]["case"]
    assert c["noi_niem_yet"] == "UBND xa Test"
    assert c["nguoi_nhan_uy_quyen_id"] == uq.id
    assert c["noi_dung_viec"] == "Dinh chinh nam sinh"


def test_workspace_commit_stage_case_meta_invalid_maps_error(adapter_db):
    """payload.case sai shape/id → CommandError validation_error, khong
    ghi Stage."""
    case, deceased, prop = _seed_case(adapter_db)
    stage = {"people": [_person_row()],
             "assets": [_asset_row()]}
    stage["owner_row_id"] = stage["people"][0]["row_id"]
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), {
            "case_id": case.id, "base_revision": 1, "stage": stage,
            "case": "khong-phai-object"})
    assert exc.value.code == "validation_error"
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_commit_stage(_Job(), {
            "case_id": case.id, "base_revision": 1, "stage": stage,
            "case": {"nguoinhanuyquyenid": 999999}})
    assert exc.value.code == "validation_error"
    adapter_db.refresh(case)
    assert case.workspace_revision == 1  # rollback tron ven


# ------------------------------------------------- diagram_evaluate / save


def _committed_case(adapter_db, loai_van_ban="khai_nhan"):
    """Seed case + commit Stage qua service that → (case, owner_row_id).

    Revision sau commit = 2. Person duy nhat la nguoi chet → draft hop le
    nhat = owner slot (engine: estate unresolved, status incomplete —
    du de kiem wire shape)."""
    case, deceased, prop = _seed_case(adapter_db, loai_van_ban=loai_van_ban)
    stage = {"people": [_person_row()],
             "assets": [_asset_row()]}
    if loai_van_ban in ("khai_nhan", "thoa_thuan"):
        stage["owner_row_id"] = stage["people"][0]["row_id"]
    res = case_workspace.CaseWorkspaceService(adapter_db).commit_stage(
        case.id, 1, stage)
    row_id = res["stage"]["people"][0]["row_id"]
    return case, row_id


def _eval_payload(case_id, state):
    return {"case_id": case_id, "diagram": {"state": state}}


def _save_payload(case_id, base_revision, state):
    return {"case_id": case_id, "base_revision": base_revision,
            "diagram": {"state": state}}


def test_diagram_evaluate_contract_shape(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[1])])
    res = notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert res["kind"] == "diagram_evaluate"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["evaluated_revision"] == 2
    rm = data["render_model"]
    assert rm["engineVersion"] == 2
    assert rm["status"] in ("incomplete", "complete", "invalid")
    assert rm["allocations"][owner_row]["baseShare"] == "1"


def test_diagram_evaluate_outside_stage_maps_error(adapter_db):
    case, _owner_row = _committed_case(adapter_db)
    outside = str(uuid.uuid4())
    state = _v3_state([_diagram_node("owner", outside, own=[1])])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    err = exc.value
    assert err.code == "diagram_reference_outside_stage"
    assert err.retryable is False
    assert err.details["personId"] == outside


def test_diagram_evaluate_invalid_state_maps_error(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[1]),
        _diagram_node("child", None, parents=("ghost_slot",))])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    err = exc.value
    assert err.code == "diagram_invalid_state"
    assert any(e["code"] == "dangling_parent"
           for e in err.details["errors"])


def test_diagram_evaluate_legacy_node_flags_invalid(adapter_db):
    """isLandOwner/willReceive tren node v3 -> invalid_node (field la)."""
    case, owner_row = _committed_case(adapter_db)
    node = _diagram_node("owner", owner_row, own=[1])
    node["isLandOwner"] = True
    state = _v3_state([node])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert exc.value.code == "diagram_invalid_state"
    codes = {e["code"] for e in exc.value.details["errors"]}
    assert "invalid_node" in codes


def test_diagram_evaluate_position_out_of_range(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[4])])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert exc.value.code == "diagram_invalid_state"
    codes = {e["code"] for e in exc.value.details["errors"]}
    assert "invalid_position" in codes


def test_diagram_evaluate_domain_mismatch(adapter_db):
    """state.domain hop le nhung khac case_type -> diagram_domain_mismatch
    (§13.5) truoc moi wire check khac."""
    case, _owner_row = _committed_case(adapter_db)
    state = _tp_state()
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert exc.value.code == "diagram_domain_mismatch"
    assert exc.value.details["got"] == "two_party"
    assert exc.value.details["expected"] == "inheritance"


def test_diagram_evaluate_two_party_unsupported(adapter_db):
    """two_party committed: unsupported render, khong engine thua ke."""
    case, p1 = _committed_case(adapter_db, loai_van_ban="tang_cho")
    res = notary_adapter.diagram_evaluate(
        _Job(), _eval_payload(case.id, _tp_state(assign={"p1": p1})))
    data = res["data"]
    assert data["evaluated_revision"] == 2
    rm = data["render_model"]
    assert rm["status"] == "unsupported"
    assert rm["allocations"] == {}
    codes = [w["code"] for w in rm["warnings"]]
    assert "diagram.two_party_unsupported" in codes


def test_diagram_evaluate_missing_diagram_is_validation_error(adapter_db):
    case, _ = _committed_case(adapter_db)
    for bad in ({}, {"diagram": None}, {"diagram": {}},
                {"diagram": {"stae": {}}}):
        p = {"case_id": case.id}
        p.update(bad)
        with pytest.raises(CommandError) as exc:
            notary_adapter.diagram_evaluate(_Job(), p)
        assert exc.value.code == "validation_error", bad


def test_diagram_evaluate_allowed_on_draft_case(adapter_db):
    case, _deceased, _prop = _seed_case(adapter_db)
    state = _v3_state([])
    res = notary_adapter.diagram_evaluate(_Job(), _eval_payload(case.id, state))
    assert res["kind"] == "diagram_evaluate"
    assert res["data"]["evaluated_revision"] == 1


def test_diagram_save_persists_and_bumps_revision(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[1])])
    res = notary_adapter.diagram_save(
        _Job(), _save_payload(case.id, 2, state))
    assert res["kind"] == "diagram_save"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["revision"] == 3
    assert data["diagram"]["state"] == state
    assert data["diagram"]["state"]["domain"] == "inheritance"
    assert data["diagram"]["render_model"]["engineVersion"] == 2
    adapter_db.refresh(case)
    assert case.workspace_revision == 3


def test_diagram_save_owner_mismatch(adapter_db):
    """Node 'owner' personId != owner_row_id da commit ->
    diagram_owner_mismatch (§13.4)."""
    case, owner_row = _committed_case(adapter_db)
    # Them nguoi thu 2 vao stage de co row hop le khac owner.
    res = case_workspace.CaseWorkspaceService(adapter_db).commit_stage(
        case.id, 2, {
            "owner_row_id": owner_row,
            "people": [_person_row(entity_id=None, row_id=owner_row,
                                   ho_ten="Nguyen Van Xuat",
                                   ngay_chet="2020-01-01"),
                       _person_row(ho_ten="Tran Thi Binh",
                                   ngay_chet=None)],
            "assets": [_asset_row()]})
    other = res["stage"]["people"][1]["row_id"]
    state = _v3_state([
        _diagram_node("owner", other, spouse="spouse", own=[1]),
        _diagram_node("spouse", None, spouse="owner")])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(_Job(), _save_payload(case.id, 3, state))
    assert exc.value.code == "diagram_owner_mismatch"
    assert exc.value.details["owner_row_id"] == owner_row


def test_diagram_save_prunes_positions(adapter_db):
    """Vi tri > len(assets) bi prune + warning diagram.selection_pruned."""
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[1, 3])])  # chi 1 asset
    res = notary_adapter.diagram_save(
        _Job(), _save_payload(case.id, 2, state))
    dg = res["data"]["diagram"]
    codes = [w["code"] for w in dg.get("warnings") or []]
    assert "diagram.selection_pruned" in codes
    node = next(n for n in dg["state"]["nodes"] if n["id"] == "owner")
    assert node["ownPositions"] == [1]


def test_diagram_save_conflict_maps_retryable(adapter_db):
    case, owner_row = _committed_case(adapter_db)
    state = _v3_state([
        _diagram_node("owner", owner_row, own=[1])])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(_Job(), _save_payload(case.id, 1, state))
    err = exc.value
    assert err.code == "workspace_conflict"
    assert err.retryable is True
    assert err.next_action == "retry"
    assert err.details["server_revision"] == 2


def test_diagram_save_two_party(adapter_db):
    """two_party save: canonical 30 slot + unsupported render + rev bump."""
    case, p1 = _committed_case(adapter_db, loai_van_ban="dat_coc")
    res = notary_adapter.diagram_save(
        _Job(), _save_payload(case.id, 2, _tp_state(assign={"p1": p1})))
    data = res["data"]
    assert data["revision"] == 3
    st = data["diagram"]["state"]
    assert st["domain"] == "two_party"
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    assert st["nodes"][0]["personId"] == p1
    assert data["diagram"]["render_model"]["status"] == "unsupported"


def test_diagram_save_two_party_missing_slot_invalid(adapter_db):
    """29 slot -> diagram_invalid_state — canonical 30 bat buoc (§13.5)."""
    case, _p1 = _committed_case(adapter_db, loai_van_ban="dat_coc")
    state = _tp_state()
    state["nodes"] = state["nodes"][:29]
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(
            _Job(), _save_payload(case.id, 2, state))
    assert exc.value.code == "diagram_invalid_state"


def test_diagram_save_missing_diagram_is_validation_error(adapter_db):
    case, _ = _committed_case(adapter_db)
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(
            _Job(), {"case_id": case.id, "base_revision": 2})
    assert exc.value.code == "validation_error"


def _commit_second_person(adapter_db, case, owner_row):
    """Thêm người Stage thứ hai (chưa gán diagram) qua commit thật."""
    adapter_db.refresh(case)
    res = case_workspace.CaseWorkspaceService(adapter_db).commit_stage(
        case.id, case.workspace_revision, {
            "owner_row_id": owner_row,
            "people": [_person_row(entity_id=None, row_id=owner_row,
                                   ho_ten="Nguyen Van Xuat",
                                   ngay_chet="2020-01-01"),
                       _person_row(ho_ten="Tran Thi Binh",
                                   ngay_chet=None)],
            "assets": [_asset_row()]})
    return res


def test_diagram_save_incomplete_reopen_keeps_warning(adapter_db):
    """Save → workspace_get (session mới, service thật): render_model đã
    lưu giữ warning Pool + incomplete + requiredSlots (§6 — mở lại)."""
    case, owner_row = _committed_case(adapter_db)
    commit = _commit_second_person(adapter_db, case, owner_row)
    assert commit["revision"] == 3
    state = _v3_state([_diagram_node("owner", owner_row, own=[1])])

    saved = notary_adapter.diagram_save(
        _Job(), _save_payload(case.id, 3, state))
    rm = saved["data"]["diagram"]["render_model"]
    codes = [w["code"] for w in rm["warnings"]]
    assert "diagram.unassigned_pool_person" in codes
    assert rm["status"] == "incomplete"
    assert rm["requiredSlots"]

    reopened = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    assert reopened["data"]["diagram"]["render_model"] == rm
    assert reopened["data"]["diagram"]["state"] == saved["data"]["diagram"]["state"]
    assert reopened["data"]["case"]["revision"] == 4


def test_diagram_save_engine_invalid_rejected_state_preserved(adapter_db):
    """Wire hợp lệ nhưng không ai giữ vị trí tài sản → engine từ chối
    `diagram_invalid_state`; bản cũ + revision giữ nguyên (§6/§9.7)."""
    case, owner_row = _committed_case(adapter_db)
    before = notary_adapter.workspace_get(_Job(), {"case_id": case.id})["data"]
    state = _v3_state([_diagram_node("owner", owner_row, own=[])])

    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_save(
            _Job(), _save_payload(case.id, 2, state))
    err = exc.value
    assert err.code == "diagram_invalid_state"
    assert any(e["code"] == "missing_land_owner"
               for e in err.details["errors"])

    after = notary_adapter.workspace_get(_Job(), {"case_id": case.id})["data"]
    assert after["case"]["revision"] == before["case"]["revision"]
    assert after["diagram"]["state"] == before["diagram"]["state"]
    assert after["diagram"]["render_model"] == \
        before["diagram"]["render_model"]


def test_workspace_commit_stage_keeps_unassigned_pool_warning(adapter_db):
    """Cập nhật Stage (không phải diagram_save) cũng lưu render_model
    khớp evaluate: người chưa gán → warning Pool + incomplete."""
    case, owner_row = _committed_case(adapter_db)
    # Chủ đất giữ vị trí 1 đã lưu (state hợp lệ) → rev 3.
    notary_adapter.diagram_save(
        _Job(), _save_payload(case.id, 2, _v3_state([
            _diagram_node("owner", owner_row, own=[1])])))
    commit = _commit_second_person(adapter_db, case, owner_row)
    rm = commit["diagram"]["render_model"]
    codes = [w["code"] for w in rm["warnings"]]
    assert "diagram.unassigned_pool_person" in codes
    assert rm["status"] == "incomplete"

    reopened = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    stored = reopened["data"]["diagram"]["render_model"]
    assert stored == rm


# ------------------------------------- word_export_options/batch (MIN-110)


def _seed_word_ready_case(sess):
    """Case du dieu kien xuat Word: chu dat da chet + tai san + nguoi nhan
    là dòng Người Storage B + participant join theo case_person_row_id."""
    case, _deceased, _prop = _seed_case(sess)
    heir = Customer(ho_ten="Nguyen Thi Con", gioi_tinh="Nữ")
    sess.add(heir)
    sess.flush()
    row_id = str(uuid.uuid4())
    sess.add(CasePersonRow(
        row_id=row_id, case_id=case.id, customer_id=heir.id, vitri=2,
        ho_ten=heir.ho_ten, gioi_tinh="Nữ"))
    sess.add(InheritanceParticipant(
        ho_so_id=case.id, customer_id=heir.id,
        case_person_row_id=row_id,
        vai_tro="Con", co_nhan_tai_san=True, ty_le=100.0))
    sess.commit()
    return case


def _dest(tmp_path):
    return {"path": str(tmp_path), "scope": "machine_local", "is_dir": True}


def _dir_link(link, target):
    """Directory link `link` → `target`: os.symlink trước, fallback
    junction `mklink /J` trên Windows (không cần quyền admin)."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except OSError:
        pass
    if os.name == "nt":
        r = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True)
        if r.returncode == 0:
            return
    pytest.skip("không tạo được directory link (thiếu quyền)")


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
    assert data["schema_version"] == SCHEMA
    docs = {d["document_key"]: d for d in data["documents"]}
    assert set(docs) == {"khai_nhan_di_san", "thoa_thuan_phan_chia",
                       "niem_yet"}
    assert docs["khai_nhan_di_san"]["ready"] is True
    assert docs["khai_nhan_di_san"]["block_reason"] is None
    assert docs["niem_yet"]["ready"] is False
    assert docs["niem_yet"]["block_reason"] == "word.template_missing"


def test_word_export_options_missing_case(adapter_db):
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_options(_Job(), {"case_id": 9999})
    assert exc.value.code == "case_not_found"


def test_word_export_two_party_allowed(adapter_db, tmp_path):
    """NAIA-8: word_export_* tren two_party khong con
    case_type_unsupported — readiness per-file qua block_reason."""
    case, _d, _p = _seed_case(adapter_db, loai_van_ban="tang_cho")
    res = notary_adapter.word_export_options(_Job(), {"case_id": case.id})
    docs = {d["document_key"]: d for d in res["data"]["documents"]}
    assert docs["khai_nhan_di_san"]["ready"] is True
    assert docs["khai_nhan_di_san"]["block_reason"] is None
    assert docs["niem_yet"]["block_reason"] == "word.template_missing"
    if os.name != "nt":
        return      # destination FileRef chỉ hợp lệ trên Windows
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id,
            "document_keys": ["khai_nhan_di_san"],
            "destination": _dest(tmp_path)})
    err = exc.value
    assert err.result["data"]["documents"][0]["error"] is None


@WINDOWS_ONLY
def test_word_export_batch_writes_docx(adapter_db, tmp_path):
    case = _seed_word_ready_case(adapter_db)
    res = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id,
        "document_keys": ["khai_nhan_di_san", "thoa_thuan_phan_chia"],
        "destination": _dest(tmp_path)})
    assert res["kind"] == "word_export_batch"
    assert res.get("partial") is not True
    data = res["data"]
    assert data["schema_version"] == SCHEMA
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


@WINDOWS_ONLY
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


@WINDOWS_ONLY
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


@WINDOWS_ONLY
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


@WINDOWS_ONLY
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


@WINDOWS_ONLY
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


@WINDOWS_ONLY
def test_word_export_batch_subdir_link_escape(adapter_db, tmp_path):
    """Review NAIA-8: destination/HS-<case_id> là junction/symlink trỏ
    ra ngoài — mkdir(exist_ok=True) chấp nhận; phải từ chối
    word_path_traversal TRƯỚC khi probe/ghi, không file nào bên ngoài."""
    case = _seed_word_ready_case(adapter_db)
    dest = tmp_path / "selected"
    dest.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    _dir_link(dest / f"HS-{case.id}", outside)
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_batch(_Job(), {
            "case_id": case.id, "document_keys": ["khai_nhan_di_san"],
            "destination": _dest(dest),
            "create_case_subdir": True})
    assert exc.value.code == "word_path_traversal"
    assert list(outside.iterdir()) == []
    assert [p.name for p in dest.iterdir()] == [f"HS-{case.id}"]


@WINDOWS_ONLY
def test_word_export_batch_subdir_destination_is_granted_dir(
        adapter_db, tmp_path):
    """Contract §8.2: create_case_subdir → ghi vào <dest>/HS-<id>/ nhưng
    data.destination trong result vẫn là thư mục người dùng chọn."""
    case = _seed_word_ready_case(adapter_db)
    res = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id, "document_keys": ["khai_nhan_di_san"],
        "destination": _dest(tmp_path),
        "create_case_subdir": True})
    data = res["data"]
    assert data["destination"]["path"] == str(tmp_path)
    out = Path(data["documents"][0]["output_file"]["path"])
    assert out.parent == tmp_path / f"HS-{case.id}"
    assert out.is_file()


# --------------------------------------- folder mode + workspace_update (NAIA-8)


def _write_docx(path, *lines):
    import docx
    d = docx.Document()
    for line in lines:
        d.add_paragraph(line)
    d.save(str(path))
    return path


def _tpl_dir(tmp_path, name="mau"):
    d = tmp_path / name
    d.mkdir()
    return d


def test_registry_wires_workspace_update():
    assert "notary.workspace_update" in reg.COMMANDS
    assert callable(reg.COMMANDS["notary.workspace_update"])


def test_workspace_update_meta_persists_and_reloads(adapter_db):
    """NAIA-8: Noi niem yet luu qua workspace_update → revision+1 →
    workspace_get doc lai DUNG gia tri (mot nguon du lieu = case DB)."""
    case = _seed_word_ready_case(adapter_db)
    res = notary_adapter.workspace_update(_Job(), {
        "case_id": case.id, "base_revision": case.workspace_revision,
        "case": {"noi_niem_yet": "xã Yên Sở"}})
    assert res["kind"] == "workspace_update"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["revision"] == case.workspace_revision + 1
    assert data["case"]["noi_niem_yet"] == "xã Yên Sở"
    # Reload qua workspace_get — du lieu da persist vao case record.
    got = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    assert got["data"]["case"]["noi_niem_yet"] == "xã Yên Sở"
    assert got["data"]["case"]["revision"] == case.workspace_revision + 1


def test_workspace_update_conflict_and_shape(adapter_db):
    case = _seed_word_ready_case(adapter_db)
    rev = case.workspace_revision
    # base_revision cu → workspace_conflict
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_update(_Job(), {
            "case_id": case.id, "base_revision": rev + 3,
            "case": {"noi_niem_yet": "xã X"}})
    assert exc.value.code == "workspace_conflict"
    # case.id khong ton tai
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_update(_Job(), {
            "case_id": 9999, "base_revision": 1,
            "case": {"noi_niem_yet": "x"}})
    assert exc.value.code == "case_not_found"
    # key la (ke ca dinh danh case_type) + case rong → validation_error
    for bad in ({"case_type": "gift"}, {}, "chuoi"):
        with pytest.raises(CommandError) as exc:
            notary_adapter.workspace_update(_Job(), {
                "case_id": case.id, "base_revision": rev, "case": bad})
        assert exc.value.code == "validation_error", bad
    # Done sửa được — không còn nhánh workspace_locked.
    case.trang_thai = "done"
    adapter_db.commit()
    done = notary_adapter.workspace_update(_Job(), {
        "case_id": case.id, "base_revision": case.workspace_revision,
        "case": {"noi_niem_yet": "xã Y"}})
    assert done["data"]["case"]["status"] == "done"


@WINDOWS_ONLY
def test_word_export_options_folder_mode(adapter_db, tmp_path):
    """template_dir (FileRef da resolve) → documents = .docx quet duoc,
    document_key = basename; lock file ~$ + non-docx + subdir bi loai."""
    case = _seed_word_ready_case(adapter_db)
    tpl = _tpl_dir(tmp_path)
    _write_docx(tpl / "B mau.docx", "SENTINEL_B")
    _write_docx(tpl / "a mau.docx", "SENTINEL_A")
    (tpl / "~$khoa.docx").write_bytes(b"lock")
    (tpl / "ghi_chu.txt").write_text("x")
    (tpl / "sub").mkdir()
    res = notary_adapter.word_export_options(_Job(), {
        "case_id": case.id,
        "template_dir": {"path": str(tpl), "scope": "machine_local",
                         "is_dir": True}})
    docs = res["data"]["documents"]
    # Sort case-insensitive: 'a mau.docx' truoc 'B mau.docx'.
    assert [d["document_key"] for d in docs] == [
        "a mau.docx", "B mau.docx"]
    assert [d["display_name"] for d in docs] == ["a mau", "B mau"]
    assert all(d["ready"] for d in docs)


@WINDOWS_ONLY
def test_word_export_options_template_dir_missing(adapter_db, tmp_path):
    """Review B3: loi doc folder mau phai la contract file_not_found,
    khong roi engine_internal_error."""
    case = _seed_word_ready_case(adapter_db)
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_options(_Job(), {
            "case_id": case.id,
            "template_dir": {"path": str(tmp_path / "khong-co"),
                             "scope": "machine_local", "is_dir": True}})
    assert exc.value.code == "file_not_found"
    f = tmp_path / "la-file"
    f.write_text("x")
    with pytest.raises(CommandError) as exc:
        notary_adapter.word_export_options(_Job(), {
            "case_id": case.id,
            "template_dir": {"path": str(f),
                             "scope": "machine_local", "is_dir": True}})
    assert exc.value.code == "file_not_found"


@WINDOWS_ONLY
def test_word_export_batch_folder_mode_real_docx(adapter_db, tmp_path):
    """Integration that: folder mau that → options → batch chi xuat
    mau duoc CHON; output la DOCX that chua noi dung mau do (khong phai
    mau khac), [Nơi niêm yết] thay bang gia tri da luu qua
    workspace_update; chay lai → suffix _2, khong ghi de."""
    case = _seed_word_ready_case(adapter_db)
    # Luu meta qua duong contract (khong set thuoc tinh truc tiep).
    notary_adapter.workspace_update(_Job(), {
        "case_id": case.id, "base_revision": case.workspace_revision,
        "case": {"noi_niem_yet": "xã Yên Sở"}})
    tpl = _tpl_dir(tmp_path, "mau")
    _write_docx(tpl / "mau_a.docx",
                "SENTINEL_MAU_A niem yet tai [Nơi niêm yết].")
    _write_docx(tpl / "mau_b.docx", "SENTINEL_MAU_B doc lap")
    dest = tmp_path / "dich"
    dest.mkdir()
    tpl_ref = {"path": str(tpl), "scope": "machine_local", "is_dir": True}

    opts = notary_adapter.word_export_options(_Job(), {
        "case_id": case.id, "template_dir": tpl_ref})
    keys = [d["document_key"] for d in opts["data"]["documents"]]
    assert keys == ["mau_a.docx", "mau_b.docx"]

    # Chi xuat mau_b — file phai chua noi dung MAU B, khong lan A.
    res = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id, "document_keys": ["mau_b.docx"],
        "template_dir": tpl_ref, "destination": _dest(dest)})
    data = res["data"]
    assert data["breakdown"]["succeeded"] == ["mau_b.docx"]
    out = Path(data["documents"][0]["output_file"]["path"])
    assert out.parent == dest
    import docx
    text = "\n".join(p.text for p in docx.Document(str(out)).paragraphs)
    assert "SENTINEL_MAU_B" in text
    assert "SENTINEL_MAU_A" not in text

    # Mau A: placeholder [Nơi niêm yết] → gia tri DA LUU trong case.
    res_a = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id, "document_keys": ["mau_a.docx"],
        "template_dir": tpl_ref, "destination": _dest(dest)})
    out_a = Path(res_a["data"]["documents"][0]["output_file"]["path"])
    text_a = "\n".join(p.text for p in docx.Document(str(out_a)).paragraphs)
    assert "SENTINEL_MAU_A" in text_a
    assert "xã Yên Sở" in text_a
    assert "[Nơi niêm yết]" not in text_a
    # Chay lai mau A → collision suffix, file cu giu nguyen.
    res_a2 = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id, "document_keys": ["mau_a.docx"],
        "template_dir": tpl_ref, "destination": _dest(dest)})
    d2 = res_a2["data"]["documents"][0]
    assert d2["actual_filename"].endswith("_2.docx")
    assert Path(out_a).is_file()
    assert len(list(dest.glob("*.docx"))) == 3


# ------------------------------------------------------- workspace_create


_UNSET = object()


def _create_payload(people, assets, state=_UNSET, key=_UNSET,
                    case_meta=_UNSET):
    p = {
        "idempotency_key": key if key is not _UNSET else _uuid4(),
        "case": (case_meta if case_meta is not _UNSET
                 else {"document_type": "khai_nhan"}),
        "stage": {"people": people, "assets": assets},
    }
    if state is not _UNSET:
        p["diagram"] = {"state": state}
    return p


def _create_args(with_diagram=True):
    """(people, assets, state, stage_owner_row_id) v2 — owner = people[0]."""
    owner = _person_row(
        ho_ten="Nguyen Van An", ngay_sinh="1950", ngay_chet="2011-05-15",
        so_giay_to="001234567890")
    spouse = _person_row(
        ho_ten="Tran Thi Binh", gioi_tinh="Nữ", ngay_sinh="1955-03-02",
        ngay_chet=None, so_giay_to="009876543210")
    state = _v3_state([
        _diagram_node("owner", owner["row_id"], spouse="spouse", own=[1]),
        _diagram_node("spouse", spouse["row_id"], spouse="owner",
                      receive=[1]),
    ]) if with_diagram else _UNSET
    return [owner, spouse], [_asset_row()], state


def _inheritance_create(people, assets, state=_UNSET, **kw):
    """_create_payload + stage.owner_row_id = people[0].row_id."""
    p = _create_payload(people, assets, state, **kw)
    p["stage"]["owner_row_id"] = people[0]["row_id"]
    return p


def test_registry_wires_workspace_create():
    assert "notary.workspace_create" in reg.COMMANDS
    assert callable(reg.COMMANDS["notary.workspace_create"])


def test_workspace_create_contract_shape(adapter_db):
    people, assets, state = _create_args()
    res = notary_adapter.workspace_create(
        _Job(), _inheritance_create(people, assets, state, case_meta={
            "document_type": "khai_nhan", "ngay_lap_ho_so": "2026-09-26",
            "noi_niem_yet": "xa Yen So", "ghi_chu": "Nhap"}))
    assert res["kind"] == "workspace_create"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["backend_mode"] == "real"
    assert data["created"] is True
    c = data["case"]
    assert c["case_type"] == "inheritance"
    assert c["status"] == "draft"
    assert "locked" not in c
    assert c["revision"] == 1
    assert c["ngay_lap_ho_so"] == "2026-09-26"
    assert c["noi_niem_yet"] == "xa Yen So"
    assert c["ghi_chu"] == "Nhap"
    assert all(p["entity_id"] for p in data["stage"]["people"])
    assert data["stage"]["owner_row_id"] == people[0]["row_id"]
    st = data["diagram"]["state"]
    assert st["version"] == 3 and st["domain"] == "inheritance"
    assert data["diagram"]["render_model"]["engineVersion"] == 2
    assert data["capabilities"]["word_export"] is True
    for n in st["nodes"]:
        assert "isLandOwner" not in n and "willReceive" not in n
    # doc lai bang workspace_get — case ton tai that
    got = notary_adapter.workspace_get(_Job(), {"case_id": c["id"]})
    assert got["data"]["case"]["revision"] == 1


def test_workspace_create_without_diagram_seeds_owner(adapter_db):
    """diagram absent -> server seed node 'owner' = owner_row_id +
    ownPositions moi vi tri (§13.6); render_model null."""
    people, assets, _ = _create_args(with_diagram=False)
    res = notary_adapter.workspace_create(
        _Job(), _inheritance_create(people, assets))
    data = res["data"]
    st = data["diagram"]["state"]
    owner = next((n for n in st["nodes"] if n["id"] == "owner"), None)
    assert owner is not None
    assert owner["personId"] == people[0]["row_id"]
    assert owner["ownPositions"] == [1]
    assert data["diagram"]["render_model"] is None


def test_workspace_create_two_party(adapter_db):
    """two_party create: case_type + doc enum moi; stage khong
    owner_row_id; diagram absent → seed canonical 30 slot."""
    people = [_person_row(ho_ten="Ben A", ngay_chet=None),
              _person_row(ho_ten="Ben B", gioi_tinh="Nữ",
                          ngay_chet=None)]
    p = _create_payload(people, [_asset_row()], case_meta={
        "case_type": "two_party", "document_type": "chuyen_nhuong"})
    res = notary_adapter.workspace_create(_Job(), p)
    data = res["data"]
    assert data["case"]["case_type"] == "two_party"
    assert data["case"]["document_type"] == "chuyen_nhuong"
    assert "owner_row_id" not in data["stage"]
    st = data["diagram"]["state"]
    assert st["domain"] == "two_party"
    assert [n["id"] for n in st["nodes"]] == TP_IDS
    assert data["capabilities"]["word_export"] is True   # NAIA-8


def test_workspace_create_idempotent_replay(adapter_db):
    people, assets, state = _create_args()
    key = _uuid4()
    first = notary_adapter.workspace_create(
        _Job(), _inheritance_create(people, assets, state, key=key))
    second = notary_adapter.workspace_create(
        _Job(), _inheritance_create(people, assets, state, key=key))
    assert first["data"]["created"] is True
    assert second["data"]["created"] is False
    assert second["data"]["case"]["id"] == first["data"]["case"]["id"]
    assert adapter_db.query(InheritanceCase).count() == 1
    # key khac = case moi; row_id thuộc case cũ nên payload phải mới.
    people2, assets2, state2 = _create_args()
    third = notary_adapter.workspace_create(
        _Job(), _inheritance_create(people2, assets2, state2, key=_uuid4()))
    assert third["data"]["created"] is True
    assert third["data"]["case"]["id"] != first["data"]["case"]["id"]


def test_workspace_create_bad_key_and_meta(adapter_db):
    people, assets, state = _create_args()
    for bad_key in (None, "nope", 42, str(uuid.uuid1())):
        with pytest.raises(CommandError) as exc:
            notary_adapter.workspace_create(
                _Job(), _inheritance_create(
                    people, assets, state, key=bad_key))
        assert exc.value.code == "validation_error", bad_key
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(
            _Job(), _inheritance_create(
                people, assets, state, case_meta={"document_type": "khac"}))
    assert exc.value.code == "validation_error"
    assert adapter_db.query(InheritanceCase).count() == 0


def test_workspace_create_owner_pointer_required(adapter_db):
    """inheritance: owner_row_id null/missing/dangling ->
    workspace_owner_required (§13.6)."""
    people, assets, state = _create_args()
    for bad in (None, _uuid4(), "khong-uuid"):
        p = _create_payload(people, assets, state)
        p["stage"]["owner_row_id"] = bad
        with pytest.raises(CommandError) as exc:
            notary_adapter.workspace_create(_Job(), p)
        assert exc.value.code == "workspace_owner_required", bad
    p = _create_payload(people, assets, state)   # key hoan toan thieu
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(_Job(), p)
    assert exc.value.code == "workspace_owner_required"
    assert adapter_db.query(InheritanceCase).count() == 0


def test_workspace_create_owner_mismatch(adapter_db):
    """Node owner personId != stage.owner_row_id ->
    diagram_owner_mismatch — server KHONG tu sua (§13.6)."""
    people, assets, _ = _create_args()
    state = _v3_state([
        _diagram_node("owner", people[1]["row_id"], spouse="spouse",
                      own=[1]),
        _diagram_node("spouse", None, spouse="owner", receive=[1]),
    ])
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(
            _Job(), _inheritance_create(people, assets, state))
    assert exc.value.code == "diagram_owner_mismatch"
    assert exc.value.details["owner_row_id"] == people[0]["row_id"]
    assert adapter_db.query(InheritanceCase).count() == 0


def test_workspace_create_domain_mismatch(adapter_db):
    """state.domain hop le nhung khac case.case_type ->
    diagram_domain_mismatch (§13.5)."""
    people, assets, _ = _create_args()
    p = _inheritance_create(people, assets, _tp_state())
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(_Job(), p)
    assert exc.value.code == "diagram_domain_mismatch"
    assert exc.value.details["expected"] == "inheritance"


def test_workspace_create_is_primary_rejected(adapter_db):
    people, assets, state = _create_args()
    assets[0]["is_primary"] = True              # field la tren v2
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(
            _Job(), _inheritance_create(people, assets, state))
    assert exc.value.code == "validation_error"


def test_workspace_create_entity_id_and_stage_errors(adapter_db):
    people, assets, state = _create_args()
    # entity_id non-null tren nhap -> stage_validation_error
    bad_people = [dict(people[0], entity_id=5), people[1]]
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(
            _Job(), _inheritance_create(bad_people, assets, state))
    assert exc.value.code == "stage_validation_error"
    # stage rong assets -> required field error
    p = _inheritance_create(people, [], state)
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(_Job(), p)
    assert exc.value.code == "stage_validation_error"
    assert adapter_db.query(InheritanceCase).count() == 0


def test_workspace_create_two_party_owner_row_id_rejected(adapter_db):
    people = [_person_row(ho_ten="Ben A", ngay_chet=None)]
    p = _create_payload(people, [_asset_row()], case_meta={
        "case_type": "two_party", "document_type": "tang_cho"})
    p["stage"]["owner_row_id"] = None           # key cam voi two_party
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(_Job(), p)
    assert exc.value.code == "validation_error"


def test_workspace_create_missing_stage(adapter_db):
    people, assets, state = _create_args()
    payload = _inheritance_create(people, assets, state)
    del payload["stage"]
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_create(_Job(), payload)
    assert exc.value.code == "validation_error"


def test_workspace_create_diagram_absent_allowed(adapter_db):
    """diagram absent -> OK (§13.6 — server seed); stage thieu -> loi."""
    people, assets, _state = _create_args()
    p = _inheritance_create(people, assets)      # khong kem diagram
    res = notary_adapter.workspace_create(_Job(), p)
    assert res["data"]["created"] is True


# --------------------------------------------- diagram_evaluate draft mode


def _draft_stage():
    """stage draft inheritance — owner_row_id = people[0].row_id."""
    people = [
        _person_row(ho_ten="Nguyen Van An", ngay_sinh="1950",
                    ngay_chet="2011-05-15"),
        _person_row(ho_ten="Tran Thi Binh", gioi_tinh="Nữ",
                    ngay_chet=None),
    ]
    return {"owner_row_id": people[0]["row_id"],
            "people": people, "assets": []}


def test_diagram_evaluate_draft_mode(adapter_db):
    stage = _draft_stage()
    rows = [p["row_id"] for p in stage["people"]]
    state = _v3_state([
        _diagram_node("owner", rows[0], spouse="spouse", own=[1]),
        _diagram_node("spouse", rows[1], spouse="owner", receive=[1])])
    res = notary_adapter.diagram_evaluate(_Job(), {
        "stage": stage, "diagram": {"state": state}})
    assert res["kind"] == "diagram_evaluate"
    data = res["data"]
    assert data["schema_version"] == SCHEMA
    assert data["evaluated_revision"] is None
    assert data["render_model"]["engineVersion"] == 2
    # read-only tuyet doi — khong ghi DB
    assert adapter_db.query(InheritanceCase).count() == 0


def test_diagram_evaluate_draft_case_hint_two_party(adapter_db):
    """§2.1a/§13.7: case.case_type hint -> two_party draft tra
    unsupported render_model (khong can owner_row_id)."""
    stage = {"people": [_person_row(ngay_chet=None),
                        _person_row(ho_ten="Ben B", ngay_chet=None)],
             "assets": [_asset_row()]}
    res = notary_adapter.diagram_evaluate(_Job(), {
        "case": {"case_type": "two_party"},
        "stage": stage,
        "diagram": {"state": _tp_state(
            assign={"p1": stage["people"][0]["row_id"]})}})
    data = res["data"]
    assert data["evaluated_revision"] is None
    assert data["render_model"]["status"] == "unsupported"


def test_diagram_evaluate_draft_domain_mismatch(adapter_db):
    stage = _draft_stage()
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "stage": stage, "diagram": {"state": _tp_state()}})
    assert exc.value.code == "diagram_domain_mismatch"
    assert exc.value.details["expected"] == "inheritance"


def test_diagram_evaluate_draft_owner_required(adapter_db):
    """Draft inheritance thieu owner_row_id -> workspace_owner_required."""
    stage = {"people": [_person_row()], "assets": [_asset_row()]}
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "stage": stage, "diagram": {"state": _v3_state([])}})
    assert exc.value.code == "workspace_owner_required"


def test_diagram_evaluate_null_case_id_is_validation_error(adapter_db):
    stage = _draft_stage()
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "case_id": None, "stage": stage,
            "diagram": {"state": _v3_state([])}})
    assert exc.value.code == "validation_error"


def test_diagram_evaluate_draft_requires_stage(adapter_db):
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "diagram": {"state": _v3_state([])}})
    assert exc.value.code == "validation_error"


def test_diagram_evaluate_draft_stage_errors(adapter_db):
    stage = _draft_stage()
    stage["people"][0]["ho_ten"] = "   "
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "stage": stage,
            "diagram": {"state": _v3_state([])}})
    assert exc.value.code == "stage_validation_error"
    assert exc.value.details["field_errors"]


def test_diagram_evaluate_draft_outside_stage(adapter_db):
    stage = _draft_stage()
    state = _v3_state([
        _diagram_node("owner", stage["people"][0]["row_id"], own=[1]),
        _diagram_node("child", str(uuid.uuid4()), parents=("owner",),
                      receive=[1])])
    with pytest.raises(CommandError) as exc:
        notary_adapter.diagram_evaluate(_Job(), {
            "stage": stage, "diagram": {"state": state}})
    assert exc.value.code == "diagram_reference_outside_stage"


def test_conversion_real_adapter_persists_and_publishes_terminal_success(adapter_db):
    from jobstore import Job
    case = _seed_word_ready_case(adapter_db)
    before = notary_adapter.workspace_get(_Job(), {"case_id": case.id})["data"]
    job = Job("conversion-adapter", "notary.workspace_convert_type")
    result = notary_adapter.workspace_convert_type(job, {
        "case_id": case.id, "base_revision": before["case"]["revision"],
        "case_type": "two_party", "document_type": "tang_cho",
        "confirm_diagram_reset": True})
    assert result["data"]["stage"]["people"] == before["stage"]["people"]
    assert result["data"]["stage"]["assets"] == before["stage"]["assets"]
    assert result["data"]["case"]["case_type"] == "two_party"
    assert job.snapshot()["status"] == "succeeded"
    assert job.request_cancel() is False
    reopened = notary_adapter.workspace_get(_Job(), {"case_id": case.id})["data"]
    assert reopened == result["data"]


def test_conversion_real_adapter_accepted_cancel_never_writes(adapter_db):
    from jobstore import Job, CancelledByUser
    case = _seed_word_ready_case(adapter_db)
    before = notary_adapter.workspace_get(_Job(), {"case_id": case.id})["data"]
    job = Job("conversion-canceled", "notary.workspace_convert_type")
    assert job.request_cancel()
    with pytest.raises(CancelledByUser):
        notary_adapter.workspace_convert_type(job, {
            "case_id": case.id, "base_revision": before["case"]["revision"],
            "case_type": "two_party", "document_type": "tang_cho",
            "confirm_diagram_reset": True})
    assert notary_adapter.workspace_get(_Job(), {"case_id": case.id})["data"] == before


@WINDOWS_ONLY
def test_stage_raw_serial_commit_reopen_and_word_batch(adapter_db, tmp_path):
    """#40: serial nguyên văn/rỗng/trùng qua commit thật, mở lại phiên mới
    và xuất Word batch thật — không sinh XX, không gộp tài sản."""
    case, deceased, prop = _seed_case(adapter_db)
    people = [_person_row()]
    assets = [
        _asset_row(so_serial="TEST-RAW/001",
                   so_thua_dat="123", so_to_ban_do="45",
                   dia_chi="Thửa 123, tờ 45"),
        _asset_row(so_serial="", so_thua_dat="456", so_to_ban_do="78",
                   dia_chi="Thửa 456, tờ 78"),
        _asset_row(so_serial="TEST-RAW/001", so_thua_dat="789",
                   so_to_ban_do="90", dia_chi="Thửa 789, tờ 90"),
    ]
    assert assets[1]["entity_id"] is None
    assert assets[1]["so_serial"] == ""
    committed = notary_adapter.workspace_commit_stage(_Job(), {
        "case_id": case.id, "base_revision": case.workspace_revision,
        "stage": {"owner_row_id": people[0]["row_id"],
                  "people": people, "assets": assets},
    })
    assert [a["so_serial"] for a in committed["data"]["stage"]["assets"]] == [
        "TEST-RAW/001", "", "TEST-RAW/001"]

    reopened = notary_adapter.workspace_get(_Job(), {"case_id": case.id})
    saved = reopened["data"]["stage"]["assets"]
    assert [a["so_serial"] for a in saved] == [
        "TEST-RAW/001", "", "TEST-RAW/001"]
    assert [a["so_thua_dat"] for a in saved] == ["123", "456", "789"]
    # Cùng serial nguyên văn → cùng identity; serial rỗng = thiếu neo → null.
    assert saved[0]["entity_id"] == saved[2]["entity_id"] is not None
    assert saved[1]["entity_id"] is None
    assert adapter_db.query(Property).filter_by(
        so_serial="TEST-RAW/001").count() == 1
    assert adapter_db.query(Property).filter_by(so_serial="").count() == 0

    tpl = _tpl_dir(tmp_path, "mau-serial")
    _write_docx(tpl / "serial.docx",
                "S1=[Serial 1]",
                "S2=[Serial 2]",
                "S3=[Serial 3]",
                "T1=[Số thửa 1]",
                "T2=[Số thửa 2]",
                "T3=[Số thửa 3]")
    dest = tmp_path / "dich"
    dest.mkdir()
    res = notary_adapter.word_export_batch(_Job(), {
        "case_id": case.id,
        "document_keys": ["serial.docx"],
        "template_dir": {"path": str(tpl), "scope": "machine_local",
                          "is_dir": True},
        "destination": _dest(dest),
    })
    assert res["data"]["breakdown"]["succeeded"] == ["serial.docx"]
    out = Path(res["data"]["documents"][0]["output_file"]["path"])
    import docx
    text = "\n".join(p.text for p in docx.Document(str(out)).paragraphs)
    lines = text.splitlines()
    assert "S1=TEST-RAW/001" in lines
    assert "S2=" in lines
    assert "S3=TEST-RAW/001" in lines
    assert "S2=[Serial 2]" not in text
    assert "T1=123" in lines and "T2=456" in lines and "T3=789" in lines
    assert "XX" not in text


def test_property_create_allows_empty_and_verbatim_serial(adapter_db):
    """#40: adapter property_create không còn _require serial; giữ raw."""
    empty = notary_adapter.property_create(_Job(), {
        "so_serial": "", "dia_chi": "Thửa 0"})
    assert empty["data"]["property"]["so_serial"] == ""

    raw = notary_adapter.property_create(_Job(), {
        "so_serial": "  RAW  ", "dia_chi": "Thửa 1"})
    assert raw["data"]["property"]["so_serial"] == "  RAW  "

    absent = notary_adapter.property_create(_Job(), {
        "dia_chi": "Thửa 2"})
    assert absent["data"]["property"]["so_serial"] == ""


# ------------------------------------------------ workspace_source_latest


def _done_case(sess, *, loai_van_ban="khai_nhan", stamp=None):
    case, deceased, prop = _seed_case(sess, loai_van_ban=loai_van_ban)
    case.trang_thai = "done"
    if stamp is not None:
        case.updated_at = stamp
    sess.commit()
    return case, deceased, prop


def test_workspace_source_latest_real_db_read_only(adapter_db):
    sess = adapter_db
    stamp = datetime(2026, 10, 22, 8, 0, 0, 123456)
    case, deceased, prop = _done_case(sess, stamp=stamp)
    engine = sess.get_bind()
    statements = []

    def before(conn, cursor, statement, parameters, context, many):
        head = statement.lstrip().split(None, 1)[0].upper()
        if head in ("INSERT", "UPDATE", "DELETE", "REPLACE"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", before)
    try:
        res = notary_adapter.workspace_source_latest(_Job(), {})
    finally:
        event.remove(engine, "before_cursor_execute", before)

    assert res["kind"] == "workspace_source_latest"
    data = res["data"]
    assert data["backend_mode"] == "real"
    assert data["source_case_id"] == case.id
    assert data["source_status"] == "done"
    assert statements == [], statements
    stage = data["stage"]
    assert stage["owner_row_id"] == stage["people"][0]["row_id"]
    original = [r.row_id for r in sess.query(CasePersonRow).all()] + [
        r.row_id for r in sess.query(CaseAssetRow).all()]
    returned = [r["row_id"] for r in stage["people"] + stage["assets"]]
    assert all(rid not in original for rid in returned)
    assert all(uuid.UUID(rid).version == 4 for rid in returned)
    assert stage["people"][0]["entity_id"] == deceased.id
    assert stage["assets"][0]["entity_id"] == prop.id
    assert set(data) == {"schema_version", "backend_mode",
                         "source_case_id", "source_status", "stage"}
    assert set(stage) == {"owner_row_id", "people", "assets"}

    # Đọc lại mốc bằng session mới — handler không tiến mốc/revision.
    other = sessionmaker(bind=engine)()
    try:
        fresh = other.get(InheritanceCase, case.id)
        other.refresh(fresh)
        assert fresh.updated_at == stamp
        assert fresh.workspace_revision == case.workspace_revision
    finally:
        other.close()


def test_workspace_source_latest_empty_and_payload_errors(adapter_db):
    res = notary_adapter.workspace_source_latest(_Job(), {})
    assert res["data"]["source_case_id"] is None
    assert res["data"]["source_status"] is None
    assert res["data"]["stage"] == {"people": [], "assets": []}

    for payload in (None, {"case_id": 1}, {"filter": "x"}):
        with pytest.raises(CommandError) as exc:
            notary_adapter.workspace_source_latest(_Job(), payload)
        assert exc.value.code == "validation_error"


def test_workspace_source_latest_unsupported_case_type(adapter_db):
    sess = adapter_db
    _done_case(sess, loai_van_ban="gift")
    with pytest.raises(CommandError) as exc:
        notary_adapter.workspace_source_latest(_Job(), {})
    assert exc.value.code == "case_type_unsupported"
    assert exc.value.details["case_type"] == "gift"


def test_legacy_case_create_stamps_microsecond(adapter_db, monkeypatch):
    """NA `case_create` legacy đóng mốc lưu microsecond như mọi writer."""
    sess = adapter_db
    customer = Customer(ho_ten="Khách Legacy")
    prop = Property(so_serial="LEGACY 001")
    sess.add_all([customer, prop])
    sess.commit()
    stamp = datetime(2026, 10, 22, 9, 0, 0, 654321)
    monkeypatch.setattr(engine_models, "case_saved_at", lambda: stamp)
    res = notary_adapter.case_create(_Job(), {
        "nguoi_chet_id": customer.id, "tai_san_id": prop.id,
        "loai_van_ban": "khai_nhan"})
    case_id = res["data"]["case"]["id"]
    sess.expire_all()
    case = sess.get(InheritanceCase, case_id)
    assert case.updated_at == stamp
    assert case.updated_at.microsecond == 654321

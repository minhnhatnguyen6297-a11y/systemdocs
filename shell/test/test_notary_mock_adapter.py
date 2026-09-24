"""MIN-106 — mock backend notary case-drafting (contract-faithful).

Chay:  python -m pytest shell/test/test_notary_mock_adapter.py -q

Gateway (`notary_gateway`) chon mock khi G1_DEV_NOTARY_MOCK=1 VA sidecar
khong packaged (sys.frozen); mac dinh real. Scenario fixtures o
`fixtures/notary-case-drafting/*.json` — ten/dia chi deu la mau gia.

Contract SOT: contracts/notary-case-drafting.md — test reuse chinh validator
cua contract (`validate_examples.violations`) de kiem chung wire shape.
"""
import copy
import importlib.util
import json
import sys
import threading
import time
import uuid
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SHELL = _HERE.parent
_REPO = _SHELL.parent
sys.path.insert(0, str(_SHELL / "sidecar"))

from errors import CommandError            # noqa: E402
from jobstore import Job, JobStore          # noqa: E402
import command_registry as reg              # noqa: E402
import notary_gateway as gw                 # noqa: E402
import notary_mock_adapter as mock          # noqa: E402

FIXTURES = _HERE / "fixtures" / "notary-case-drafting"
VALIDATOR = (_REPO / "contracts" / "notary-case-drafting"
             / "validate_examples.py")

_spec = importlib.util.spec_from_file_location("ncd_validate", VALIDATOR)
ncd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ncd)

DRAFTING_COMMANDS = [
    "notary.workspace_get",
    "notary.intake_analyze",
    "notary.workspace_commit_stage",
    "notary.diagram_evaluate",
    "notary.diagram_save",
    "notary.word_export_options",
    "notary.word_export_batch",
]

P_OWNER = "11111111-1111-4111-8111-111111111111"
P_SPOUSE = "22222222-2222-4222-8222-222222222222"
P_CHILD1 = "33333333-3333-4333-8333-333333333333"
P_CHILD2 = "44444444-4444-4444-8444-444444444444"
P_POOL = "77777777-7777-4777-8777-777777777777"


# ---------- helpers ----------

def _load_fixture(name):
    """Doc scenario fixture; resolve '$ref_scenario' bang file cung ten."""
    doc = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    cases = {}
    for cid, c in (doc.get("cases") or {}).items():
        if isinstance(c, dict) and "$ref_scenario" in c:
            ref = _load_fixture(c["$ref_scenario"] + ".json")
            cases[cid] = copy.deepcopy(ref["cases"][cid])
        else:
            cases[cid] = c
    doc["cases"] = cases
    return doc


def _job(command="notary.workspace_get"):
    j = Job(str(uuid.uuid4()), command)
    j.status = "running"
    return j


def _call(fn_name, payload):
    """Di qua gateway dispatch (mock da bat qua autouse fixture)."""
    return gw.dispatch(fn_name, _job(f"notary.{fn_name}"), payload)


def _node(nid, person_id=None, parents=(), spouse=None,
          owner=False, receive=True):
    return {
        "id": nid, "personId": person_id,
        "parentSlotIds": list(parents), "spouseSlotId": spouse,
        "isLandOwner": owner, "willReceive": receive,
        "hidden": False, "deleted": False,
    }


def _ready_state():
    return {
        "version": 2,
        "nodes": [
            _node("owner", P_OWNER, spouse="spouse", owner=True,
                  receive=False),
            _node("spouse", P_SPOUSE, spouse="owner"),
            _node("child_1", P_CHILD1, parents=("owner", "spouse")),
            _node("child_2", P_CHILD2, parents=("owner", "spouse")),
        ],
    }


def _job_doc(command, payload, result=None, error=None,
             status="succeeded", fixture_context=None):
    doc = {
        "contract_version": "desktopcommand.v1",
        "job_id": "j_mock_test",
        "command_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        "command": command,
        "payload": payload,
        "status": status,
        "waiting_on": None,
        "progress": None,
        "result": result,
        "error": error,
        "updated_at": "2026-09-24T00:00:00Z",
    }
    if fixture_context:
        doc["fixture_context"] = fixture_context
    return doc


def _assert_contract(doc):
    """Chay chinh validator cua contract len job snapshot cua mock."""
    viols = ncd.violations(doc)
    assert viols == [], f"contract violations: {viols}"


def _no_confirmed_key(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert str(k).lower() != "confirmed", "co key 'confirmed' bi cam"
            _no_confirmed_key(v)
    elif isinstance(obj, list):
        for v in obj:
            _no_confirmed_key(v)


def _wait_terminal(store, job_id, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = store.get(job_id)
        if job.status in ("succeeded", "failed", "canceled", "partial"):
            return job
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} khong terminal trong {timeout}s")


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch):
    """Moi test chay voi mock ON va state seed mac dinh sach."""
    monkeypatch.setenv("G1_DEV_NOTARY_MOCK", "1")
    monkeypatch.delattr(sys, "frozen", raising=False)
    gw._warned_packaged = False          # doc lap thu tu test
    mock.reset_backend()
    yield
    mock.reset_backend()


# ---------- fixtures / registration ----------

class TestScaffolding:
    def test_commands_registered(self):
        for cmd in DRAFTING_COMMANDS:
            assert cmd in reg.COMMANDS, f"thieu {cmd} trong COMMANDS"

    def test_fixtures_loadable_and_no_real_pii(self):
        names = ["empty", "ready", "locked", "conflict", "intake-partial",
                 "diagram-warning", "word-collision", "word-partial",
                 "word-all-failed", "word-canceled", "unsupported"]
        for n in names:
            doc = _load_fixture(f"{n}.json")
            assert doc["scenario"] == n
            assert doc.get("cases"), n
            raw = json.dumps(doc, ensure_ascii=False)
            assert "Người Mẫu" in raw or n in (
                "empty", "unsupported", "intake-partial",
                "word-all-failed"), n   # word-all-failed ref -> empty

    def test_default_backend_covers_scenarios(self):
        # Default seed (fixture files) phai co du case cho moi scenario.
        for cid in (42, 43, 44, 45, 46):
            res = _call("workspace_get", {"case_id": cid})
            assert res["data"]["case"]["id"] == cid


# ---------- gateway ----------

class TestGateway:
    def test_mock_selected_when_env_and_not_packaged(self, monkeypatch):
        monkeypatch.setenv("G1_DEV_NOTARY_MOCK", "1")
        monkeypatch.delattr(sys, "frozen", raising=False)
        assert gw.use_mock() is True

    def test_real_by_default(self, monkeypatch):
        monkeypatch.delenv("G1_DEV_NOTARY_MOCK", raising=False)
        assert gw.use_mock() is False

    def test_flag_value_other_than_1_ignored(self, monkeypatch):
        monkeypatch.setenv("G1_DEV_NOTARY_MOCK", "yes")
        assert gw.use_mock() is False

    def test_packaged_ignores_flag_with_warning(self, monkeypatch, capsys):
        monkeypatch.setenv("G1_DEV_NOTARY_MOCK", "1")
        # PyInstaller packaged — sys.frozen chi ton tai tren ban dong goi
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        assert gw.use_mock() is False
        err = capsys.readouterr().err
        assert "G1_DEV_NOTARY_MOCK" in err

    def test_packaged_dispatch_goes_real(self, monkeypatch):
        monkeypatch.setenv("G1_DEV_NOTARY_MOCK", "1")
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        # Real backend cho 7 command chua implement (MIN-107+) -> structured
        with pytest.raises(CommandError) as exc:
            gw.dispatch("workspace_get", _job(), {"case_id": 42})
        assert exc.value.code == "engine_not_installed"
        assert exc.value.retryable is False

    def test_dispatch_mock(self):
        res = gw.dispatch("workspace_get", _job(), {"case_id": 42})
        assert res["data"]["backend_mode"] == "mock"


# ---------- workspace_get ----------

class TestWorkspaceGet:
    def test_empty(self):
        mock.reset_backend(_load_fixture("empty.json"))
        payload = {"case_id": 43}
        res = _call("workspace_get", payload)
        assert res["kind"] == "workspace_get"
        data = res["data"]
        assert data["schema_version"] == "notary.case-drafting.v1"
        assert data["backend_mode"] == "mock"
        assert data["case"]["revision"] == 1
        assert data["case"]["locked"] is False
        assert data["stage"] == {"people": [], "assets": []}
        assert data["diagram"]["render_model"] is None
        assert data["capabilities"]["diagram"] is True
        _assert_contract(_job_doc("notary.workspace_get", payload, result=res))

    def test_ready_stage_full(self):
        mock.reset_backend(_load_fixture("ready.json"))
        res = _call("workspace_get", {"case_id": 42})
        data = res["data"]
        assert len(data["stage"]["people"]) == 4
        assert len(data["stage"]["assets"]) == 2
        rm = data["diagram"]["render_model"]
        assert rm is not None and rm["status"] == "complete"
        assert data["case"]["revision"] == 7
        # personId trong diagram deu thuoc stage da commit
        stage_ids = {p["row_id"] for p in data["stage"]["people"]}
        for n in data["diagram"]["state"]["nodes"]:
            if n["personId"] is not None:
                assert n["personId"] in stage_ids
        _assert_contract(_job_doc(
            "notary.workspace_get", {"case_id": 42}, result=res,
            fixture_context={"stage_row_ids": sorted(stage_ids)}))

    def test_locked_case(self):
        mock.reset_backend(_load_fixture("locked.json"))
        res = _call("workspace_get", {"case_id": 44})
        assert res["data"]["case"]["locked"] is True
        assert res["data"]["case"]["status"] == "locked"

    def test_unsupported_case_type(self):
        mock.reset_backend(_load_fixture("unsupported.json"))
        res = _call("workspace_get", {"case_id": 45})
        data = res["data"]
        assert data["case"]["case_type"] == "gift"
        assert data["capabilities"]["word_export"] is False
        assert data["capabilities"]["diagram"] is False
        assert data["capabilities"]["intake"] == []

    def test_case_not_found(self):
        with pytest.raises(CommandError) as exc:
            _call("workspace_get", {"case_id": 9999})
        assert exc.value.code == "case_not_found"


# ---------- workspace_commit_stage ----------

class TestCommitStage:
    def _payload(self, base_revision=1, people=None, assets=None):
        return {"case_id": 43, "base_revision": base_revision,
                "stage": {"people": people or [], "assets": assets or []}}

    def _person(self, row_id, name="Người Mẫu X", entity_id=None):
        return {
            "row_id": row_id, "entity_id": entity_id,
            "ho_ten": name, "gioi_tinh": "Nam",
            "ngay_sinh": "1990-01-01", "ngay_chet": None,
            "so_giay_to": None, "ngay_cap": None, "noi_cap": None,
            "dia_chi": "Địa chỉ mẫu", "place_of_origin": None,
        }

    def _asset(self, row_id, primary=True, serial="MM000010"):
        return {
            "row_id": row_id, "entity_id": None, "is_primary": primary,
            "so_serial": serial, "so_vao_so": None, "so_thua_dat": "9",
            "so_to_ban_do": "1", "dia_chi": "Địa chỉ mẫu tài sản",
            "loai_so": None, "hinh_thuc_su_dung": None, "thoi_han": None,
            "nguon_goc": None, "ngay_cap": None, "co_quan_cap": None,
            "land_rows": [],
        }

    def test_commit_success_assigns_entity_and_bumps_revision(self):
        mock.reset_backend(_load_fixture("empty.json"))
        rid = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
        payload = self._payload(people=[self._person(rid)])
        res = _call("workspace_commit_stage", payload)
        data = res["data"]
        assert data["revision"] == 2                     # 1 -> 2
        row = data["stage"]["people"][0]
        assert row["row_id"] == rid
        assert isinstance(row["entity_id"], int)         # backend gan
        assert data["diagram"]["render_model"] is not None  # re-evaluate §6.1
        _assert_contract(_job_doc(
            "notary.workspace_commit_stage", payload, result=res))
        # get lai thay stage da persist
        res2 = _call("workspace_get", {"case_id": 43})
        assert res2["data"]["case"]["revision"] == 2
        assert len(res2["data"]["stage"]["people"]) == 1

    def test_revision_monotonic_two_commits(self):
        mock.reset_backend(_load_fixture("empty.json"))
        p = self._payload()
        assert _call("workspace_commit_stage", p)["data"]["revision"] == 2
        p["base_revision"] = 2
        assert _call("workspace_commit_stage", p)["data"]["revision"] == 3

    def test_stale_revision_conflict(self):
        mock.reset_backend(_load_fixture("conflict.json"))
        payload = _load_fixture("conflict.json")["request"][
            "workspace_commit_stage"]
        with pytest.raises(CommandError) as exc:
            _call("workspace_commit_stage", payload)
        assert exc.value.code == "workspace_conflict"
        assert exc.value.details["server_revision"] == 7

    def test_future_revision_also_conflict(self):
        mock.reset_backend(_load_fixture("empty.json"))
        p = self._payload(base_revision=99)
        with pytest.raises(CommandError) as exc:
            _call("workspace_commit_stage", p)
        assert exc.value.code == "workspace_conflict"

    def test_atomic_bad_row_rolls_back(self):
        mock.reset_backend(_load_fixture("empty.json"))
        bad = self._person("ffffffff-ffff-4fff-8fff-ffffffffffff")
        bad["ho_ten"] = ""                                # vi pham required
        good = self._person("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
        payload = self._payload(people=[good, bad])
        with pytest.raises(CommandError) as exc:
            _call("workspace_commit_stage", payload)
        assert exc.value.code == "stage_validation_error"
        fe = exc.value.details["field_errors"]
        assert any(e["row_id"] == bad["row_id"] and e["field"] == "ho_ten"
                   and e["code"] == "required" for e in fe)
        # Stage khong doi (atomic) — dong good cung khong duoc ghi
        res = _call("workspace_get", {"case_id": 43})
        assert res["data"]["stage"]["people"] == []
        assert res["data"]["case"]["revision"] == 1

    def test_duplicate_row_id(self):
        mock.reset_backend(_load_fixture("empty.json"))
        row = self._person("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
        payload = self._payload(people=[row, dict(row)])
        with pytest.raises(CommandError) as exc:
            _call("workspace_commit_stage", payload)
        assert exc.value.code == "stage_validation_error"
        assert any(e["code"] == "duplicate_row_id"
                   for e in exc.value.details["field_errors"])

    def test_primary_count_rule(self):
        mock.reset_backend(_load_fixture("empty.json"))
        a1 = self._asset("aaaaaaa1-1111-4111-8111-111111111111", primary=True)
        a2 = self._asset("aaaaaaa2-2222-4222-8222-222222222222", primary=True)
        with pytest.raises(CommandError) as exc:
            _call("workspace_commit_stage", self._payload(assets=[a1, a2]))
        assert any(e["code"] == "primary_count"
                   for e in exc.value.details["field_errors"])

    def test_serial_must_be_canonical(self):
        mock.reset_backend(_load_fixture("empty.json"))
        a = self._asset("aaaaaaa1-1111-4111-8111-111111111111",
                        serial="khong-canonical")
        with pytest.raises(CommandError) as exc:
            _call("workspace_commit_stage", self._payload(assets=[a]))
        assert any(e["field"] == "so_serial" and e["code"] == "invalid_format"
                   for e in exc.value.details["field_errors"])

    def test_commit_prunes_diagram_refs(self):
        """Xoa nguoi khoi stage -> node tham chieu bi prune trong cung
        transaction, render_model khop state moi (§6.1)."""
        mock.reset_backend(_load_fixture("ready.json"))
        # commit stage bo het nguoi tru owner (nguoi da chet)
        keep = _load_fixture("ready.json")["cases"]["42"]["stage"]["people"][0]
        payload = {"case_id": 42, "base_revision": 7,
                   "stage": {"people": [keep],
                             "assets": _load_fixture("ready.json")
                             ["cases"]["42"]["stage"]["assets"]}}
        res = _call("workspace_commit_stage", payload)
        nodes = res["data"]["diagram"]["state"]["nodes"]
        ids = {n["personId"] for n in nodes if n["personId"]}
        assert ids <= {keep["row_id"], None} - {None} or ids == {
            keep["row_id"]}
        for n in nodes:
            if n["personId"] is not None:
                assert n["personId"] == keep["row_id"]

    def test_container_shape_is_validation_error(self):
        """Oracle parity: stage khong dict / people|assets thieu hoac
        khong list -> validation_error (KHONG stage_validation_error;
        code do chi cho loi row-level)."""
        mock.reset_backend(_load_fixture("empty.json"))
        for bad_stage in (
                "khong-phai-object",
                {"people": "x", "assets": []},
                {"people": []},                       # thieu assets
                {"assets": []},                       # thieu people
                {"people": [], "assets": "y"},
                {"people": None, "assets": []}):
            p = {"case_id": 43, "base_revision": 1, "stage": bad_stage}
            with pytest.raises(CommandError) as exc:
                _call("workspace_commit_stage", p)
            assert exc.value.code == "validation_error", bad_stage

    def test_locked_case_rejected(self):
        mock.reset_backend(_load_fixture("locked.json"))
        p = {"case_id": 44, "base_revision": 3,
             "stage": {"people": [], "assets": []}}
        with pytest.raises(CommandError) as exc:
            _call("workspace_commit_stage", p)
        assert exc.value.code == "workspace_locked"

    def test_unsupported_case_type(self):
        mock.reset_backend(_load_fixture("unsupported.json"))
        p = {"case_id": 45, "base_revision": 1,
             "stage": {"people": [], "assets": []}}
        with pytest.raises(CommandError) as exc:
            _call("workspace_commit_stage", p)
        assert exc.value.code == "case_type_unsupported"
        assert exc.value.details["case_type"] == "gift"


# ---------- intake_analyze ----------

class TestIntakeAnalyze:
    def _text_src(self, sid, text):
        return {"source_id": sid, "kind": "text", "text": text}

    def test_succeeded(self):
        mock.reset_backend(_load_fixture("empty.json"))
        sid = "aaaaaaaa-0000-4000-8000-000000000009"
        payload = {"case_id": 43,
                   "sources": [self._text_src(sid, "Người Mẫu I, sinh 1950")]}
        res = _call("intake_analyze", payload)
        assert res["kind"] == "intake_analyze"
        assert res["data"]["schema_version"] == "notary.case-drafting.v1"
        sug = res["data"]["suggestions"][0]
        assert sug["source_id"] == sid
        assert sug["target"] in ("person", "asset")
        for fv in sug["fields"].values():
            assert fv["observation_state"] in (
                "observed", "normalized", "inferred")
        _no_confirmed_key(res)
        _assert_contract(_job_doc("notary.intake_analyze", payload, result=res))

    def test_partial_with_breakdown(self):
        doc = _load_fixture("intake-partial.json")
        mock.reset_backend(doc)
        payload = doc["request"]["intake_analyze"]
        res = _call("intake_analyze", payload)
        assert res.get("partial") is True            # marker cho jobstore
        bd = res["data"]["breakdown"]
        assert len(bd["succeeded"]) == 2
        assert bd["failed"] == ["aaaaaaaa-0000-4000-8000-000000000003"]
        assert res["data"]["errors"][0]["code"] == "intake.parse_failed"
        _assert_contract(_job_doc(
            "notary.intake_analyze", payload, result=res, status="partial"))

    def test_progress_reported(self):
        mock.reset_backend(_load_fixture("empty.json"))
        job = _job("notary.intake_analyze")
        payload = {"case_id": 43, "sources": [
            self._text_src("aaaaaaaa-0000-4000-8000-000000000001", "x")]}
        gw.dispatch("intake_analyze", job, payload)
        assert job.progress == {"done": 1, "total": 1,
                                "current_label": job.progress["current_label"]}
        assert job.progress["done"] == 1

    def test_too_many_sources(self):
        mock.reset_backend(_load_fixture("empty.json"))
        sources = [self._text_src(
            f"aaaaaaaa-0000-4000-8000-00000000000{i}", "x")
            for i in range(9)]
        with pytest.raises(CommandError) as exc:
            _call("intake_analyze", {"case_id": 43, "sources": sources})
        assert exc.value.code == "intake_too_many_sources"
        assert exc.value.details["limit"] == 8

    def test_unsupported_kind(self):
        mock.reset_backend(_load_fixture("empty.json"))
        s = {"source_id": "aaaaaaaa-0000-4000-8000-000000000001",
             "kind": "zalo_media", "text": "x"}
        with pytest.raises(CommandError) as exc:
            _call("intake_analyze", {"case_id": 43, "sources": [s]})
        assert exc.value.code == "intake_unsupported_source"
        assert exc.value.details["kind"] == "zalo_media"

    def test_text_too_long(self):
        mock.reset_backend(_load_fixture("empty.json"))
        s = self._text_src("aaaaaaaa-0000-4000-8000-000000000001",
                           "x" * 100_001)
        with pytest.raises(CommandError) as exc:
            _call("intake_analyze", {"case_id": 43, "sources": [s]})
        assert exc.value.code == "intake_text_too_long"

    def test_source_too_large(self):
        mock.reset_backend(_load_fixture("empty.json"))
        s = {"source_id": "aaaaaaaa-0000-4000-8000-000000000001",
             "kind": "image",
             "file_ref": {"path": "D:/mock-intake/big.jpg",
                          "scope": "machine_local",
                          "size_bytes": 21 * 1024 * 1024}}
        with pytest.raises(CommandError) as exc:
            _call("intake_analyze", {"case_id": 43, "sources": [s]})
        assert exc.value.code == "intake_source_too_large"

    def test_duplicate_source_id(self):
        mock.reset_backend(_load_fixture("empty.json"))
        s = self._text_src("aaaaaaaa-0000-4000-8000-000000000001", "x")
        with pytest.raises(CommandError) as exc:
            _call("intake_analyze", {"case_id": 43, "sources": [s, dict(s)]})
        assert exc.value.code == "validation_error"

    def test_file_ref_required_for_nontext(self):
        mock.reset_backend(_load_fixture("empty.json"))
        s = {"source_id": "aaaaaaaa-0000-4000-8000-000000000001",
             "kind": "pdf"}
        with pytest.raises(CommandError) as exc:
            _call("intake_analyze", {"case_id": 43, "sources": [s]})
        assert exc.value.code == "validation_error"

    def test_locked_case_rejected(self):
        mock.reset_backend(_load_fixture("locked.json"))
        s = self._text_src("aaaaaaaa-0000-4000-8000-000000000001", "x")
        with pytest.raises(CommandError) as exc:
            _call("intake_analyze", {"case_id": 44, "sources": [s]})
        assert exc.value.code == "workspace_locked"


# ---------- diagram_evaluate / diagram_save ----------

class TestDiagram:
    def test_evaluate_complete(self):
        mock.reset_backend(_load_fixture("ready.json"))
        payload = {"case_id": 42, "diagram": {"state": _ready_state()}}
        res = _call("diagram_evaluate", payload)
        assert res["kind"] == "diagram_evaluate"
        data = res["data"]
        assert data["evaluated_revision"] == 7
        rm = data["render_model"]
        assert rm["engineVersion"] == 2
        assert rm["status"] == "complete"
        # 3 nguoi nhan, moi nguoi 1/3
        assert rm["allocations"][P_SPOUSE]["finalShare"] == "1/3"
        _assert_contract(_job_doc(
            "notary.diagram_evaluate", payload, result=res,
            fixture_context={"stage_row_ids": [
                P_OWNER, P_SPOUSE, P_CHILD1, P_CHILD2]}))

    def test_evaluate_unassigned_pool_warning(self):
        doc = _load_fixture("diagram-warning.json")
        mock.reset_backend(doc)
        payload = doc["request"]["diagram_evaluate"]
        res = _call("diagram_evaluate", payload)
        rm = res["data"]["render_model"]
        codes = [w["code"] for w in rm["warnings"]]
        assert "diagram.unassigned_pool_person" in codes
        assert rm["status"] == "incomplete"

    def test_evaluate_personid_outside_stage(self):
        mock.reset_backend(_load_fixture("ready.json"))
        state = _ready_state()
        state["nodes"][0]["personId"] = (
            "99999999-9999-4999-8999-999999999999")
        with pytest.raises(CommandError) as exc:
            _call("diagram_evaluate",
                  {"case_id": 42, "diagram": {"state": state}})
        assert exc.value.code == "diagram_reference_outside_stage"

    def test_evaluate_invalid_state(self):
        mock.reset_backend(_load_fixture("ready.json"))
        state = _ready_state()
        state["version"] = 1
        with pytest.raises(CommandError) as exc:
            _call("diagram_evaluate",
                  {"case_id": 42, "diagram": {"state": state}})
        assert exc.value.code == "diagram_invalid_state"
        assert exc.value.details["errors"]

    def test_evaluate_missing_diagram_is_validation_error(self):
        """diagram/diagram.state thieu -> validation_error; state co mat
        ma sai -> diagram_invalid_state (oracle parity)."""
        mock.reset_backend(_load_fixture("ready.json"))
        for bad in (
                {},                                    # thieu diagram
                {"diagram": None},
                {"diagram": "x"},                      # khong phai object
                {"diagram": {}},                       # thieu state
                {"diagram": {"stae": {}}},             # key sai chinh ta
        ):
            p = {"case_id": 42}
            p.update(bad)
            with pytest.raises(CommandError) as exc:
                _call("diagram_evaluate", p)
            assert exc.value.code == "validation_error", bad
        # state co mat nhung khong phai object -> diagram_invalid_state
        with pytest.raises(CommandError) as exc:
            _call("diagram_evaluate",
                  {"case_id": 42, "diagram": {"state": None}})
        assert exc.value.code == "diagram_invalid_state"

    def test_save_missing_diagram_is_validation_error(self):
        mock.reset_backend(_load_fixture("ready.json"))
        with pytest.raises(CommandError) as exc:
            _call("diagram_save",
                  {"case_id": 42, "base_revision": 7})
        assert exc.value.code == "validation_error"

    def test_evaluate_string_bool_is_invalid(self):
        mock.reset_backend(_load_fixture("ready.json"))
        state = _ready_state()
        state["nodes"][0]["willReceive"] = "false"     # chuoi, khong phai bool
        with pytest.raises(CommandError) as exc:
            _call("diagram_evaluate",
                  {"case_id": 42, "diagram": {"state": state}})
        assert exc.value.code == "diagram_invalid_state"

    def test_evaluate_allowed_on_locked_case(self):
        """Read-only — evaluate duoc phep tren case locked (§7.4)."""
        mock.reset_backend(_load_fixture("locked.json"))
        res = _call("diagram_evaluate", {
            "case_id": 44,
            "diagram": {"state": _load_fixture("locked.json")
                        ["cases"]["44"]["diagram"]["state"]}})
        assert res["data"]["evaluated_revision"] == 3

    def test_evaluate_does_not_persist(self):
        mock.reset_backend(_load_fixture("ready.json"))
        state = _ready_state()
        state["nodes"].append(_node("extra_slot"))   # slot trong, hop le
        _call("diagram_evaluate", {
            "case_id": 42, "diagram": {"state": state}})
        res = _call("workspace_get", {"case_id": 42})
        assert res["data"]["case"]["revision"] == 7      # khong doi
        assert len(res["data"]["diagram"]["state"]["nodes"]) == 4

    def test_save_persists_and_bumps_revision(self):
        mock.reset_backend(_load_fixture("ready.json"))
        state = _ready_state()
        payload = {"case_id": 42, "base_revision": 7,
                   "diagram": {"state": state}}
        res = _call("diagram_save", payload)
        data = res["data"]
        assert data["revision"] == 8
        assert data["diagram"]["render_model"]["status"] == "complete"
        _assert_contract(_job_doc(
            "notary.diagram_save", payload, result=res,
            fixture_context={"stage_row_ids": [
                P_OWNER, P_SPOUSE, P_CHILD1, P_CHILD2]}))
        got = _call("workspace_get", {"case_id": 42})
        assert got["data"]["case"]["revision"] == 8

    def test_save_conflict(self):
        mock.reset_backend(_load_fixture("ready.json"))
        with pytest.raises(CommandError) as exc:
            _call("diagram_save", {
                "case_id": 42, "base_revision": 3,
                "diagram": {"state": _ready_state()}})
        assert exc.value.code == "workspace_conflict"
        assert exc.value.details["server_revision"] == 7

    def test_save_locked(self):
        mock.reset_backend(_load_fixture("locked.json"))
        with pytest.raises(CommandError) as exc:
            _call("diagram_save", {
                "case_id": 44, "base_revision": 3,
                "diagram": {"state": {"version": 2, "nodes": []}}})
        assert exc.value.code == "workspace_locked"

    def test_save_invalid_state_not_persisted(self):
        mock.reset_backend(_load_fixture("ready.json"))
        with pytest.raises(CommandError):
            _call("diagram_save", {
                "case_id": 42, "base_revision": 7,
                "diagram": {"state": {"version": 1, "nodes": []}}})
        res = _call("workspace_get", {"case_id": 42})
        assert res["data"]["case"]["revision"] == 7


# ---------- word_export_options / word_export_batch ----------

class TestWordExport:
    def _dest(self, tmp_path):
        return {"path": str(tmp_path), "scope": "machine_local",
                "is_dir": True}

    def test_options_ready_case(self):
        mock.reset_backend(_load_fixture("ready.json"))
        res = _call("word_export_options", {"case_id": 42})
        docs = {d["document_key"]: d for d in res["data"]["documents"]}
        assert docs["khai_nhan_di_san"]["ready"] is True
        assert docs["khai_nhan_di_san"]["block_reason"] is None
        assert docs["niem_yet"]["ready"] is False
        assert docs["niem_yet"]["block_reason"] == "word.template_missing"
        _assert_contract(_job_doc(
            "notary.word_export_options", {"case_id": 42}, result=res))

    def test_options_empty_case_blocked(self):
        mock.reset_backend(_load_fixture("empty.json"))
        res = _call("word_export_options", {"case_id": 43})
        docs = {d["document_key"]: d for d in res["data"]["documents"]}
        assert docs["khai_nhan_di_san"]["ready"] is False
        assert docs["khai_nhan_di_san"]["block_reason"] == "word.no_assets"
        assert docs["niem_yet"]["block_reason"] == "word.template_missing"

    def test_batch_writes_real_docx(self, tmp_path):
        mock.reset_backend(_load_fixture("ready.json"))
        payload = {"case_id": 42,
                   "document_keys": ["khai_nhan_di_san",
                                     "thoa_thuan_phan_chia"],
                   "destination": self._dest(tmp_path)}
        res = _call("word_export_batch", payload)
        assert res.get("partial") is not True
        data = res["data"]
        assert data["breakdown"] == {
            "succeeded": ["khai_nhan_di_san", "thoa_thuan_phan_chia"],
            "failed": [], "skipped": []}
        import docx
        for d in data["documents"]:
            assert d["status"] == "saved"
            out = Path(d["output_file"]["path"])
            assert out.parent == tmp_path         # trong destination
            assert out.is_file()
            docx.Document(str(out))               # DOCX hop le mo duoc
            assert ".." not in d["actual_filename"]
        _assert_contract(_job_doc(
            "notary.word_export_batch", payload, result=res))

    def test_batch_collision_suffix(self, tmp_path):
        doc = _load_fixture("word-collision.json")
        mock.reset_backend(doc)
        # pre-existing files: base + _2 -> file moi phai la _3
        for name in doc["preexisting_files"]:
            (tmp_path / name).write_bytes(b"cu")
        payload = dict(doc["request"]["word_export_batch"])
        payload["destination"] = self._dest(tmp_path)
        res = _call("word_export_batch", payload)
        d = res["data"]["documents"][0]
        assert d["actual_filename"] == (
            "Van_ban_khai_nhan_di_san_HS-42_3.docx")
        # file cu khong bi ghi de
        assert (tmp_path / doc["preexisting_files"][0]).read_bytes() == b"cu"

    def test_batch_partial(self, tmp_path):
        doc = _load_fixture("word-partial.json")
        mock.reset_backend(doc)
        payload = dict(doc["request"]["word_export_batch"])
        payload["destination"] = self._dest(tmp_path)
        res = _call("word_export_batch", payload)
        assert res.get("partial") is True
        docs = {d["document_key"]: d for d in res["data"]["documents"]}
        assert docs["khai_nhan_di_san"]["status"] == "saved"
        assert docs["niem_yet"]["status"] == "failed"
        assert docs["niem_yet"]["error"]["code"] == "word.template_missing"
        assert res["data"]["breakdown"]["failed"] == ["niem_yet"]

    def test_batch_all_failed(self, tmp_path):
        doc = _load_fixture("word-all-failed.json")
        mock.reset_backend(doc)
        payload = dict(doc["request"]["word_export_batch"])
        payload["destination"] = self._dest(tmp_path)
        with pytest.raises(CommandError) as exc:
            _call("word_export_batch", payload)
        assert exc.value.code == "word_batch_failed"
        assert len(exc.value.details["documents"]) == 2
        assert list(tmp_path.iterdir()) == []      # khong file nao duoc tao

    def test_batch_validates_before_writing(self, tmp_path):
        mock.reset_backend(_load_fixture("ready.json"))
        # document_keys thieu/null/khong list -> validation_error
        # (word_no_documents_selected CHI cho list rong)
        for bad_keys in (None, "khai_nhan_di_san", 3, {"a": 1}):
            with pytest.raises(CommandError) as exc:
                _call("word_export_batch", {
                    "case_id": 42, "document_keys": bad_keys,
                    "destination": self._dest(tmp_path)})
            assert exc.value.code == "validation_error", bad_keys
        p_no_keys = {"case_id": 42, "destination": self._dest(tmp_path)}
        with pytest.raises(CommandError) as exc:
            _call("word_export_batch", p_no_keys)
        assert exc.value.code == "validation_error"
        # document_keys rong [] -> word_no_documents_selected
        with pytest.raises(CommandError) as exc:
            _call("word_export_batch", {
                "case_id": 42, "document_keys": [],
                "destination": self._dest(tmp_path)})
        assert exc.value.code == "word_no_documents_selected"
        # key trung
        with pytest.raises(CommandError) as exc:
            _call("word_export_batch", {
                "case_id": 42,
                "document_keys": ["khai_nhan_di_san", "khai_nhan_di_san"],
                "destination": self._dest(tmp_path)})
        assert exc.value.code == "word_duplicate_document_key"
        # key ngoai catalog
        with pytest.raises(CommandError) as exc:
            _call("word_export_batch", {
                "case_id": 42, "document_keys": ["khong_co_trong_catalog"],
                "destination": self._dest(tmp_path)})
        assert exc.value.code == "word_unknown_document_key"
        # key sai pattern
        with pytest.raises(CommandError) as exc:
            _call("word_export_batch", {
                "case_id": 42, "document_keys": ["BAD-KEY"],
                "destination": self._dest(tmp_path)})
        assert exc.value.code == "word_unknown_document_key"
        assert list(tmp_path.iterdir()) == []

    def test_batch_destination_rules(self, tmp_path):
        mock.reset_backend(_load_fixture("ready.json"))
        # is_dir false -> validation_error
        with pytest.raises(CommandError) as exc:
            _call("word_export_batch", {
                "case_id": 42, "document_keys": ["khai_nhan_di_san"],
                "destination": {"path": str(tmp_path),
                                "scope": "machine_local", "is_dir": False}})
        assert exc.value.code == "validation_error"
        # thieu is_dir -> validation_error
        with pytest.raises(CommandError) as exc:
            _call("word_export_batch", {
                "case_id": 42, "document_keys": ["khai_nhan_di_san"],
                "destination": {"path": str(tmp_path),
                                "scope": "machine_local"}})
        assert exc.value.code == "validation_error"
        # folder khong ton tai -> file_not_found
        with pytest.raises(CommandError) as exc:
            _call("word_export_batch", {
                "case_id": 42, "document_keys": ["khai_nhan_di_san"],
                "destination": {"path": str(tmp_path / "khong-co"),
                                "scope": "machine_local", "is_dir": True}})
        assert exc.value.code == "file_not_found"

    def test_batch_locked_case(self, tmp_path):
        mock.reset_backend(_load_fixture("locked.json"))
        with pytest.raises(CommandError) as exc:
            _call("word_export_batch", {
                "case_id": 44, "document_keys": ["khai_nhan_di_san"],
                "destination": self._dest(tmp_path)})
        assert exc.value.code == "workspace_locked"

    def test_batch_unsupported_case_type(self, tmp_path):
        mock.reset_backend(_load_fixture("unsupported.json"))
        with pytest.raises(CommandError) as exc:
            _call("word_export_batch", {
                "case_id": 45, "document_keys": ["khai_nhan_di_san"],
                "destination": self._dest(tmp_path)})
        assert exc.value.code == "case_type_unsupported"

    def test_batch_progress(self, tmp_path):
        mock.reset_backend(_load_fixture("ready.json"))
        job = _job("notary.word_export_batch")
        gw.dispatch("word_export_batch", job, {
            "case_id": 42, "document_keys": ["khai_nhan_di_san"],
            "destination": self._dest(tmp_path)})
        assert job.progress["done"] == 1
        assert job.progress["total"] == 1


# ---------- job lifecycle qua JobStore that ----------

class TestJobLifecycle:
    def _store(self):
        return JobStore(max_workers=2)

    def test_succeeded_status(self):
        store = self._store()
        try:
            job = store.submit(str(uuid.uuid4()), "notary.workspace_get",
                               reg.COMMANDS["notary.workspace_get"],
                               {"case_id": 42})
            final = _wait_terminal(store, job.job_id)
            assert final.status == "succeeded"
            assert final.result["data"]["backend_mode"] == "mock"
        finally:
            store.drain(2)

    def test_partial_status_and_breakdown(self):
        mock.reset_backend(_load_fixture("intake-partial.json"))
        store = self._store()
        try:
            payload = _load_fixture("intake-partial.json")[
                "request"]["intake_analyze"]
            job = store.submit(str(uuid.uuid4()), "notary.intake_analyze",
                               reg.COMMANDS["notary.intake_analyze"], payload)
            final = _wait_terminal(store, job.job_id)
            assert final.status == "partial"
            assert set(final.result["data"]["breakdown"]) >= {
                "succeeded", "failed"}
        finally:
            store.drain(2)

    def test_failed_error_shape(self):
        store = self._store()
        try:
            job = store.submit(str(uuid.uuid4()), "notary.workspace_get",
                               reg.COMMANDS["notary.workspace_get"],
                               {"case_id": 9999})
            final = _wait_terminal(store, job.job_id)
            assert final.status == "failed"
            err = final.error
            assert err["code"] == "case_not_found"
            for k in ("code", "message", "retryable", "next_action",
                      "job_id", "details"):
                assert k in err
        finally:
            store.drain(2)

    def test_idempotent_command_id_no_duplicate_files(self, tmp_path):
        """Retry cung command_id -> cung job -> khong tao them file."""
        mock.reset_backend(_load_fixture("ready.json"))
        store = self._store()
        try:
            cid = str(uuid.uuid4())
            payload = {"case_id": 42,
                       "document_keys": ["khai_nhan_di_san"],
                       "destination": {"path": str(tmp_path),
                                       "scope": "machine_local",
                                       "is_dir": True}}
            handler = reg.COMMANDS["notary.word_export_batch"]
            j1 = store.submit(cid, "notary.word_export_batch", handler,
                              payload)
            _wait_terminal(store, j1.job_id)
            j2 = store.submit(cid, "notary.word_export_batch", handler,
                              payload)
            assert j2.job_id == j1.job_id
            files = list(tmp_path.glob("*.docx"))
            assert len(files) == 1            # khong _2
        finally:
            store.drain(2)

    def test_word_export_canceled_mid_batch(self, tmp_path, monkeypatch):
        """Cancel giua batch: file da ghi giu nguyen, file chua bat dau
        khong duoc tao; job canceled{user_canceled}.

        LUU Y platform: jobstore huy job voi result=null — per-file
        skipped chi ton tai tren dia, khong di vao result cua job
        (gioi han jobstore hien tai, giong real backend MIN-110)."""
        monkeypatch.setattr(mock, "WORD_DOC_DELAY", 0.4)
        doc = _load_fixture("word-canceled.json")
        mock.reset_backend(doc)
        store = self._store()
        try:
            payload = dict(doc["request"]["word_export_batch"])
            payload["destination"] = {"path": str(tmp_path),
                                      "scope": "machine_local",
                                      "is_dir": True}
            job = store.submit(str(uuid.uuid4()),
                               "notary.word_export_batch",
                               reg.COMMANDS["notary.word_export_batch"],
                               payload)
            # cho van ban dau duoc ghi roi cancel
            deadline = time.time() + 8
            while time.time() < deadline:
                cur = store.get(job.job_id)
                if cur.progress and cur.progress["done"] >= 1:
                    break
                time.sleep(0.02)
            assert store.cancel(job.job_id) == "ok"
            final = _wait_terminal(store, job.job_id)
            assert final.status == "canceled"
            assert final.error["code"] == "user_canceled"
            files = sorted(p.name for p in tmp_path.glob("*.docx"))
            # file dau giu lai; hai file sau khong bao gio duoc tao
            assert files == ["Van_ban_khai_nhan_di_san_HS-42.docx"]
        finally:
            store.drain(2)


# ---------- cross-cutting contract rules ----------

class TestContractInvariants:
    def test_schema_version_on_all_kinds(self, tmp_path):
        mock.reset_backend(_load_fixture("ready.json"))
        ready_stage = _load_fixture("ready.json")["cases"]["42"]["stage"]
        calls = {
            "workspace_get": {"case_id": 42},
            "intake_analyze": {"case_id": 42, "sources": [
                {"source_id": "aaaaaaaa-0000-4000-8000-000000000001",
                 "kind": "text", "text": "mau"}]},
            "workspace_commit_stage": {
                "case_id": 42, "base_revision": 7,
                "stage": copy.deepcopy(ready_stage)},   # giu stage de
                                                       # personId hop le
            "diagram_evaluate": {
                "case_id": 42, "diagram": {"state": _ready_state()}},
            "diagram_save": {
                "case_id": 42, "base_revision": 8,
                "diagram": {"state": _ready_state()}},
            "word_export_options": {"case_id": 42},
            "word_export_batch": {
                "case_id": 42, "document_keys": ["khai_nhan_di_san"],
                "destination": {"path": str(tmp_path),
                                "scope": "machine_local", "is_dir": True}},
        }
        for name, payload in calls.items():
            res = _call(name, payload)
            assert res["kind"] == name
            assert res["data"]["schema_version"] == (
                "notary.case-drafting.v1"), name

    def test_no_confirmed_anywhere(self):
        mock.reset_backend(_load_fixture("intake-partial.json"))
        res = _call("intake_analyze", _load_fixture("intake-partial.json")
                    ["request"]["intake_analyze"])
        _no_confirmed_key(res)

    def test_deterministic_suggestion_ids(self):
        mock.reset_backend(_load_fixture("empty.json"))
        payload = {"case_id": 43, "sources": [
            {"source_id": "aaaaaaaa-0000-4000-8000-000000000001",
             "kind": "text", "text": "Người Mẫu I"}]}
        r1 = _call("intake_analyze", payload)
        r2 = _call("intake_analyze", payload)
        assert (r1["data"]["suggestions"][0]["suggestion_id"]
                == r2["data"]["suggestions"][0]["suggestion_id"])

"""Unit test upload workspace + session scoping (MIN-69 task 2).

Chay: python test/test_upload_workspace.py
Can engine upload_lab resolvable (env G1_UPLOAD_LAB_ROOT / engine-roots.json /
<repo>/upload_lab bundled) — module `providers` that duoc import de validate
website_id. Khong mo Playwright: NamDinhUploaderSession lazy trong __init__,
cac test conflict dung sentinel session hoac _BrowserWorker() rieng.

Cover: select_website busy-block (job/tab rows), resolve_run binding +
scope_violation + website_mismatch + manifest hash, preferences save/load +
chunk_size bounds, legacy<->v1 workflow_conflict qua _ensure_session.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve().parent
_SHELL = _HERE.parent
sys.path.insert(0, str(_SHELL / "sidecar"))

from errors import CommandError  # noqa: E402
import engine_roots  # noqa: E402
import upload_workspace  # noqa: E402
import upload_adapter  # noqa: E402
import upload_session  # noqa: E402
from upload_workspace_store import UploadWorkspaceStore  # noqa: E402


def _engines_available():
    try:
        engine_roots.engine_root("upload_lab")
        return True
    except CommandError:
        return False


class _JobStub:
    """Job toi thieu cho handler khong can progress/cancel."""
    def report_progress(self, *a, **k):
        pass

    def check_cancel(self):
        pass


def _providers_mod():
    return engine_roots.import_engine_module("upload_lab", "providers")


@unittest.skipUnless(_engines_available(),
                     "chua resolve duoc upload_lab engine root")
class WorkspaceCase(unittest.TestCase):
    """Base: G1_UPLOAD_DATA_DIR tro vao temp dir + store rieng moi test."""

    FAKE_ID = "fake_b"

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.data_root = Path(self.tempdir.name) / "data"
        self._old_env = os.environ.get("G1_UPLOAD_DATA_DIR")
        os.environ["G1_UPLOAD_DATA_DIR"] = str(self.data_root)
        upload_workspace.reset_store_for_tests()
        self.addCleanup(upload_workspace.reset_store_for_tests)
        self.addCleanup(self._restore_env)
        # Website gia chi song trong test — inject vao registry engine roi
        # go ra khi xong (production catalog khong bao gio co no).
        self.providers = _providers_mod()
        class _Fake(self.providers.WebsiteProvider):
            def __init__(self, wid):
                super().__init__(
                    website_id=wid, label=wid.upper(),
                    display_url="https://fake.example",
                    capabilities=())
        self.providers.DEFAULT_REGISTRY.register(_Fake(self.FAKE_ID))
        self.addCleanup(self._unregister_fake)

    def _restore_env(self):
        if self._old_env is None:
            os.environ.pop("G1_UPLOAD_DATA_DIR", None)
        else:
            os.environ["G1_UPLOAD_DATA_DIR"] = self._old_env

    def _unregister_fake(self):
        self.providers.DEFAULT_REGISTRY._providers.pop(self.FAKE_ID, None)

    # ---------- helpers ----------

    def _manifest(self, run_id="run-1", name="m1.json") -> Path:
        runs = upload_workspace.website_data_dir("nam_dinh") / "runs"
        runs.mkdir(parents=True, exist_ok=True)
        path = runs / name
        path.write_text(json.dumps(
            {"run_id": run_id, "stats": {"processed_files": 1}}),
            encoding="utf-8")
        return path


class WebsiteScopeTests(WorkspaceCase):
    def test_website_data_dir_layout_under_data_root(self):
        d = upload_workspace.website_data_dir("nam_dinh")
        self.assertEqual(d.parent.name, "websites")
        self.assertEqual(d.parent.parent, self.data_root.resolve())
        for sub in ("output", "runs", "downloads", "upload_runs", "logs"):
            self.assertTrue((d / sub).is_dir(), sub)

    def test_unknown_and_bad_slug_rejected(self):
        with self.assertRaises(CommandError) as ctx:
            upload_workspace.website_data_dir("ha_noi")
        self.assertEqual(ctx.exception.code, "unknown_website")
        with self.assertRaises(CommandError) as ctx:
            upload_workspace.website_data_dir("../escape")
        self.assertEqual(ctx.exception.code, "unknown_website")


class SelectWebsiteTests(WorkspaceCase):
    def test_select_first_website_bumps_revision(self):
        store = upload_workspace.open_store()
        self.assertIsNone(store.selected_website_id())
        snap = upload_workspace.select_website("nam_dinh", 0)
        self.assertEqual(snap["website_id"], "nam_dinh")
        self.assertEqual(snap["revision"], 1)

    def test_stale_revision_rejected_retryable(self):
        upload_workspace.select_website("nam_dinh", 0)
        with self.assertRaises(CommandError) as ctx:
            upload_workspace.select_website(self.FAKE_ID, 0)
        self.assertEqual(ctx.exception.code, "stale_revision")
        self.assertTrue(ctx.exception.retryable)

    def test_select_same_website_idempotent(self):
        upload_workspace.select_website("nam_dinh", 0)
        snap = upload_workspace.select_website("nam_dinh", 1)
        self.assertEqual(snap["website_id"], "nam_dinh")
        self.assertEqual(snap["revision"], 1)  # khong bump lan hai

    def test_busy_blocked_by_active_job(self):
        store = upload_workspace.open_store()
        upload_workspace.select_website("nam_dinh", 0)
        store.upsert_job("j1", command="upload.prepare",
                         website_id="nam_dinh", status="running")
        with self.assertRaises(CommandError) as ctx:
            upload_workspace.select_website(self.FAKE_ID, 1)
        self.assertEqual(ctx.exception.code, "workflow_busy")
        self.assertIn("j1", ctx.exception.details["active_job_ids"])
        # job sang trang thai terminal -> doi duoc
        store.set_job_status("j1", "succeeded")
        snap = upload_workspace.select_website(self.FAKE_ID, 1)
        self.assertEqual(snap["website_id"], self.FAKE_ID)

    def test_busy_blocked_by_open_tabs(self):
        store = upload_workspace.open_store()
        upload_workspace.select_website("nam_dinh", 0)
        store.add_open_tabs("nam_dinh", [10, 11], run_id="run-1")
        with self.assertRaises(CommandError) as ctx:
            upload_workspace.select_website(self.FAKE_ID, 1)
        self.assertEqual(ctx.exception.code, "workflow_busy")
        self.assertEqual(ctx.exception.details["open_tab_record_ids"], [10, 11])
        store.remove_open_tabs("nam_dinh", [10, 11])
        snap = upload_workspace.select_website(self.FAKE_ID, 1)
        self.assertEqual(snap["website_id"], self.FAKE_ID)


class ResolveRunTests(WorkspaceCase):
    def test_resolve_run_via_store_binding(self):
        path = self._manifest("run-1")
        upload_workspace.register_run("nam_dinh", path)
        resolved = upload_workspace.resolve_run("nam_dinh", "run-1")
        self.assertEqual(resolved.resolve(), path.resolve())

    def test_resolve_run_fallback_by_manifest_content(self):
        """Manifest trong runs/ chua co row store (du lieu migrate) -> resolve
        theo noi dung run_id va tu ghi binding."""
        path = self._manifest("run-migrated")
        resolved = upload_workspace.resolve_run("nam_dinh", "run-migrated")
        self.assertEqual(resolved.resolve(), path.resolve())
        rec = upload_workspace.open_store().run_for("run-migrated")
        self.assertEqual(rec["website_id"], "nam_dinh")

    def test_scope_violation_unknown_run(self):
        upload_workspace.website_data_dir("nam_dinh")
        with self.assertRaises(CommandError) as ctx:
            upload_workspace.resolve_run("nam_dinh", "khong-co")
        self.assertEqual(ctx.exception.code, "scope_violation")

    def test_website_mismatch_run_of_other_website(self):
        path = self._manifest("run-1")
        upload_workspace.register_run("nam_dinh", path)
        with self.assertRaises(CommandError) as ctx:
            upload_workspace.resolve_run(self.FAKE_ID, "run-1")
        self.assertEqual(ctx.exception.code, "website_mismatch")

    def test_manifest_mismatch_on_changed_file(self):
        path = self._manifest("run-1")
        upload_workspace.register_run("nam_dinh", path)
        path.write_text(json.dumps(
            {"run_id": "run-1", "stats": {"processed_files": 999}}),
            encoding="utf-8")
        with self.assertRaises(CommandError) as ctx:
            upload_workspace.resolve_run("nam_dinh", "run-1")
        self.assertEqual(ctx.exception.code, "manifest_mismatch")

    def test_file_not_found_retryable(self):
        path = self._manifest("run-1")
        upload_workspace.register_run("nam_dinh", path)
        path.unlink()
        with self.assertRaises(CommandError) as ctx:
            upload_workspace.resolve_run("nam_dinh", "run-1")
        self.assertEqual(ctx.exception.code, "file_not_found")
        self.assertTrue(ctx.exception.retryable)
        self.assertEqual(ctx.exception.next_action, "retry")

    def test_run_id_validation(self):
        with self.assertRaises(CommandError) as ctx:
            upload_workspace.resolve_run("nam_dinh", "   ")
        self.assertEqual(ctx.exception.code, "validation_error")


class PreferencesTests(WorkspaceCase):
    def test_store_defaults_and_save(self):
        store = upload_workspace.open_store()
        prefs = store.get_preferences("nam_dinh")
        self.assertEqual(prefs, {"website_id": "nam_dinh", "chunk_size": 10,
                                 "cong_chung_vien": None, "thu_ky": None})
        store.save_preferences(
            "nam_dinh", {"chunk_size": 7, "cong_chung_vien": "A"})
        prefs = store.get_preferences("nam_dinh")
        self.assertEqual(prefs["chunk_size"], 7)
        self.assertEqual(prefs["cong_chung_vien"], "A")
        self.assertIsNone(prefs["thu_ky"])

    def test_store_clamps_chunk_size_and_rejects_unknown_key(self):
        store = upload_workspace.open_store()
        self.assertEqual(
            store.save_preferences("nam_dinh", {"chunk_size": 0})
            ["chunk_size"], 1)
        self.assertEqual(
            store.save_preferences("nam_dinh", {"chunk_size": 99})
            ["chunk_size"], 30)
        with self.assertRaises(ValueError):
            store.save_preferences("nam_dinh", {"base_url": "x"})

    def test_preferences_are_per_website(self):
        store = upload_workspace.open_store()
        store.save_preferences("nam_dinh", {"chunk_size": 7})
        self.assertEqual(
            store.get_preferences(self.FAKE_ID)["chunk_size"], 10)

    def test_adapter_validation_errors(self):
        job = _JobStub()
        base = {"workflow_version": "upload.workflow.v1",
                "website_id": "nam_dinh"}
        for bad_values, note in (
                ({"chunk_size": 0}, "duoi 1"),
                ({"chunk_size": 31}, "tren 30"),
                ({"chunk_size": True}, "bool khong phai int"),
                ({"chunk_size": "5"}, "string"),
                ({"cong_chung_vien": ""}, "chuoi rong phai null"),
                ({"thu_ky": ""}, "chuoi rong phai null"),
                ({"thu_ky": 5}, "sai kieu"),
                ({"base_url": "https://x"}, "key ngoai schema")):
            with self.assertRaises(CommandError, msg=note) as ctx:
                upload_adapter.upload_preferences(
                    job, base | {"values": bad_values})
            self.assertEqual(ctx.exception.code, "validation_error", note)

    def test_adapter_write_syncs_env_per_website(self):
        job = _JobStub()
        res = upload_adapter.upload_preferences(job, {
            "workflow_version": "upload.workflow.v1",
            "website_id": "nam_dinh",
            "values": {"chunk_size": 7, "cong_chung_vien": "Nguyen A"}})
        self.assertEqual(res["kind"], "preferences")
        self.assertEqual(res["data"]["chunk_size"], 7)
        env = (upload_workspace.website_data_dir("nam_dinh")
               / ".env").read_text(encoding="utf-8")
        self.assertIn("ND_MAX_PREPARED_TABS=7", env)
        # doc lai khong co values
        res2 = upload_adapter.upload_preferences(job, {
            "workflow_version": "upload.workflow.v1",
            "website_id": "nam_dinh"})
        self.assertEqual(res2["data"]["cong_chung_vien"], "Nguyen A")


class WorkflowGateTests(WorkspaceCase):
    def test_non_dict_payload_is_validation_error(self):
        job = _JobStub()
        for bad in (["a", "b"], "chuoi", 42):
            with self.assertRaises(CommandError) as ctx:
                upload_adapter.upload_websites(job, bad)
            self.assertEqual(ctx.exception.code, "validation_error")

    def test_missing_and_wrong_version(self):
        job = _JobStub()
        for payload in (None, {}, {"workflow_version": "v0"},
                        {"workflow_version": "upload.workflow.v2"}):
            with self.assertRaises(CommandError) as ctx:
                upload_adapter.upload_websites(job, payload)
            self.assertEqual(ctx.exception.code,
                             "unsupported_workflow_version")

    def test_catalog_shape(self):
        job = _JobStub()
        res = upload_adapter.upload_websites(
            job, {"workflow_version": "upload.workflow.v1"})
        self.assertEqual(res["kind"], "website_catalog")
        entries = res["data"]["websites"]
        # nam_dinh la website dau tien (production); fake inject sau do chi
        # ton tai trong test — production-only check nam o
        # upload_lab/tests/test_website_providers.py
        self.assertEqual(entries[0]["website_id"], "nam_dinh")
        for e in entries:
            self.assertEqual(
                set(e), {"website_id", "label", "display_url",
                         "capabilities", "status"})


class SessionConflictTests(WorkspaceCase):
    """_BrowserWorker._ensure_session — logic conflict thuan, khong can
    browser that (NamDinhUploaderSession lazy trong __init__)."""

    def test_versioned_session_records_browser_and_blocks_others(self):
        w = upload_session._BrowserWorker()
        session = w._ensure_session("nam_dinh")
        self.assertEqual(session.working_dir,
                         upload_workspace.website_data_dir("nam_dinh"))
        store = upload_workspace.open_store()
        brow = store.current_browser("nam_dinh")
        self.assertIsNotNone(brow)
        self.assertEqual(brow["browser_id"], w.browser_id)
        self.assertEqual(brow["status"], "open")

        # website khac -> website_mismatch; legacy -> workflow_conflict
        with self.assertRaises(CommandError) as ctx:
            w._ensure_session(self.FAKE_ID)
        self.assertEqual(ctx.exception.code, "website_mismatch")
        with self.assertRaises(CommandError) as ctx:
            w._ensure_session(None)
        self.assertEqual(ctx.exception.code, "workflow_conflict")

        w._close_session()
        self.assertIsNone(store.current_browser("nam_dinh"))
        self.assertIsNone(w.browser_id)

    def test_legacy_session_blocks_versioned(self):
        """Session legacy (website_id=None) dang mo -> op versioned bi
        workflow_conflict chu khong website_mismatch."""
        w = upload_session._BrowserWorker()
        w._session = object()       # sentinel — khong can session that
        w._website_id = None        # legacy
        with self.assertRaises(CommandError) as ctx:
            w._ensure_session("nam_dinh")
        self.assertEqual(ctx.exception.code, "workflow_conflict")

    def test_versioned_session_blocks_legacy(self):
        w = upload_session._BrowserWorker()
        w._session = object()
        w._website_id = "nam_dinh"
        with self.assertRaises(CommandError) as ctx:
            w._ensure_session(None)
        self.assertEqual(ctx.exception.code, "workflow_conflict")

    def test_close_cleans_browser_row_even_if_session_close_raises(self):
        store = upload_workspace.open_store()
        store.open_browser("nam_dinh", "brw_dead")

        class _BadClose:
            def close(self):
                raise RuntimeError("boom")

        w = upload_session._BrowserWorker()
        w._session = _BadClose()
        w._website_id = "nam_dinh"
        w.browser_id = "brw_dead"
        with self.assertRaises(RuntimeError):
            w._close_session()
        # browsers row da closed + state da reset du session.close raise
        self.assertIsNone(store.current_browser("nam_dinh"))
        self.assertIsNone(w._website_id)
        self.assertIsNone(w.browser_id)

    def test_open_browser_store_failure_fails_session(self):
        """Store loi khi ghi browser -> session bi dong + engine_unavailable,
        khong chay session 'vo chu' nhu truoc."""
        w = upload_session._BrowserWorker()
        with mock.patch.object(upload_workspace, "open_store",
                               side_effect=RuntimeError("db locked")):
            with self.assertRaises(CommandError) as ctx:
                w._ensure_session("nam_dinh")
        self.assertEqual(ctx.exception.code, "engine_unavailable")
        self.assertIsNone(w._session)
        self.assertIsNone(w.browser_id)


if __name__ == "__main__":
    unittest.main()

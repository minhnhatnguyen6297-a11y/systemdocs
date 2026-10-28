"""MIN-69 — Task 5: huy/ket qua mot phan/khoi phuc sau gian doan.

Lop 1 (khong can engine): JobRepository + JobStore tren workspace.sqlite3
tam — "restart" = store instance moi tren cung file: job do →
failed{engine_restarted}, terminal giu nguyen, command_id cu khong chay
lai handler, command_id cu + payload khac → command_id_conflict.

Lop 2 (FakePortal — tai dung BrowserWorkflowCase): crash giua review →
job failed + mat quyen so huu tab (khong suy ket qua Luu); shutdown dong
browser sach; restart khong replay handler prepare; toan bo muc loi →
failed (khong phai partial).

Chay: python test/test_upload_recovery.py
"""

import json
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SHELL = _HERE.parent
sys.path.insert(0, str(_SHELL / "sidecar"))
sys.path.insert(0, str(_HERE / "fixtures"))
sys.path.insert(0, str(_HERE))

from errors import CommandError                              # noqa: E402
from job_repository import JobRepository                    # noqa: E402
from jobstore import JobStore                               # noqa: E402
from upload_workspace_store import UploadWorkspaceStore     # noqa: E402

import test_upload_browser_workflow as tbw                  # noqa: E402


# =====================================================================
# Lop 1 — JobRepository + JobStore tren file tam (khong can engine)
# =====================================================================

def _quick(job, payload):
    return {"kind": "ok", "data": {"echo": payload},
            "evidence": [], "warnings": []}


def _wait_terminal(store, job_id, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        snap = store.get(job_id).snapshot()
        if snap["status"] in ("succeeded", "failed", "canceled",
                              "partial"):
            return snap
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} khong terminal")


class JobRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.db = Path(self.tempdir.name) / "workspace.sqlite3"
        self._stores = []

    def _new_store(self):
        repo = JobRepository(self.db)
        store = JobStore(max_workers=4, repository=repo)
        self._stores.append(store)
        return store

    def tearDown(self):
        for store in self._stores:
            try:
                store.drain(timeout=2)
            except Exception:
                pass

    def test_unfinished_job_marked_engine_restarted_on_reopen(self):
        """Job 'running' cua process cu → store moi danh dau
        failed{engine_restarted, retryable} va KHONG chay lai handler."""
        gate = threading.Event()
        calls = []

        def blocked(job, payload):
            calls.append(1)
            gate.wait(30)
            job.check_cancel()
            return {"kind": "ok", "data": {}}

        store1 = self._new_store()
        job = store1.submit("c-restart", "diag.slow_task", blocked,
                            {"a": 1})
        deadline = time.time() + 5
        while job.snapshot()["status"] != "running":
            self.assertLess(time.time(), deadline)
            time.sleep(0.02)

        # "Process moi": JobStore moi tren cung file — job cu chet theo
        # process, khong duoc chay lai.
        store2 = self._new_store()
        zombie = store2.get(job.job_id)
        self.assertIsNotNone(zombie)
        snap = zombie.snapshot()
        self.assertEqual(snap["status"], "failed")
        self.assertEqual(snap["error"]["code"], "engine_restarted")
        self.assertTrue(snap["error"]["retryable"])
        self.assertEqual(snap["error"]["next_action"], "retry")

        # Resubmit cung command_id + cung noi dung → lai dung job cu,
        # handler KHONG chay lai (khong phat lai upload mu — §7.4).
        z2 = store2.submit("c-restart", "diag.slow_task", blocked,
                           {"a": 1})
        self.assertEqual(z2.job_id, job.job_id)
        self.assertEqual(len(calls), 1, "handler bi chay lai sau restart")

        # Cung command_id + noi dung khac → command_id_conflict.
        with self.assertRaises(CommandError) as ctx:
            store2.submit("c-restart", "diag.slow_task", blocked,
                          {"a": 2})
        self.assertEqual(ctx.exception.code, "command_id_conflict")

        # Don dep: nha gate de handler cu thoat roi drain.
        gate.set()
        store1.drain(timeout=3)

    def test_terminal_job_preserved_and_idempotent_across_restart(self):
        """Job da terminal giu nguyen snapshot (result/error) sau restart;
        resubmit cung command_id tra lai job cu ma khong chay lai."""
        calls = []

        def counted(job, payload):
            calls.append(1)
            return _quick(job, payload)

        store1 = self._new_store()
        job = store1.submit("c-done", "diag.x", counted, {"n": 1})
        snap = _wait_terminal(store1, job.job_id)
        self.assertEqual(snap["status"], "succeeded")
        store1.drain(timeout=2)

        store2 = self._new_store()
        got = store2.get(job.job_id)
        self.assertIsNotNone(got, "job terminal phai materialize duoc")
        snap2 = got.snapshot()
        self.assertEqual(snap2["status"], "succeeded")
        self.assertEqual(snap2["result"]["data"]["echo"], {"n": 1})
        # Resubmit → cung job, khong re-execute.
        again = store2.submit("c-done", "diag.x", counted, {"n": 1})
        self.assertEqual(again.job_id, job.job_id)
        self.assertEqual(len(calls), 1)

    def test_drain_persists_engine_shutdown_terminal(self):
        """Shutdown nhan nhanh: job dang chay → canceled{engine_shutdown}
        va da persist — process sau thay terminal, khong phuc hoi."""
        gate = threading.Event()

        def blocked(job, payload):
            while not gate.is_set():
                job.check_cancel()
                time.sleep(0.01)

        store1 = self._new_store()
        job = store1.submit("c-drain", "diag.x", blocked, {})
        deadline = time.time() + 5
        while job.snapshot()["status"] != "running":
            self.assertLess(time.time(), deadline)
            time.sleep(0.02)
        store1.drain(timeout=3)
        snap = job.snapshot()
        self.assertEqual(snap["status"], "canceled")
        self.assertEqual(snap["error"]["code"], "engine_shutdown")

        # Process moi: canceled la terminal → giu nguyen, khong
        # engine_restarted.
        store2 = self._new_store()
        got = store2.get(job.job_id)
        self.assertEqual(got.snapshot()["status"], "canceled")
        self.assertEqual(got.snapshot()["error"]["code"],
                         "engine_shutdown")
        gate.set()

    def test_zombie_not_reexecutable_but_retry_is_new_command(self):
        """Job engine_restarted la snapshot doc-only: cancel →
        job_already_terminal; retry co chu y la COMMAND MOI (command_id
        moi) → job moi chay handler binh thuong."""
        gate = threading.Event()

        def blocked(job, payload):
            gate.wait(30)

        store1 = self._new_store()
        job = store1.submit("c-z1", "diag.x", blocked, {})
        deadline = time.time() + 5
        while job.snapshot()["status"] != "running":
            self.assertLess(time.time(), deadline)
            time.sleep(0.02)
        store2 = self._new_store()
        self.assertEqual(store2.cancel(job.job_id), "terminal")

        done = threading.Event()

        def quick2(j, p):
            done.set()
            return _quick(j, p)

        retry = store2.submit("c-z1-retry", "diag.x", quick2, {})
        self.assertNotEqual(retry.job_id, job.job_id)
        snap = _wait_terminal(store2, retry.job_id)
        self.assertEqual(snap["status"], "succeeded")
        self.assertTrue(done.is_set())
        gate.set()
        store1.drain(timeout=3)

    def test_record_snapshot_cannot_regress_terminal_row(self):
        """Terminal guard cua journal (T5 fix1): record_snapshot goi truc
        tiep voi snapshot non-terminal 'tre' (listener cham/race) KHONG
        duoc ghi de row da terminal — mirror terminal guard cua
        workflow_jobs.upsert_job; terminal dau tien luon thang."""
        repo = JobRepository(self.db)
        self.addCleanup(repo.close)
        store = JobStore(max_workers=2, repository=repo)
        self._stores.append(store)
        job = store.submit("c-term-guard", "diag.x", _quick, {"n": 1})
        snap = _wait_terminal(store, job.job_id)
        self.assertEqual(snap["status"], "succeeded")

        # Snapshot 'running' den tre → status + snapshot_json giu
        # nguyen terminal da persist.
        repo.record_snapshot(
            dict(snap, status="running", result=None, error=None))
        row = repo.find_by_job_id(job.job_id)
        self.assertEqual(row["status"], "succeeded")
        self.assertEqual(row["snapshot"]["status"], "succeeded")
        self.assertEqual(row["snapshot"]["result"]["data"]["echo"],
                         {"n": 1})

        # Terminal khac cung khong ghi de — cancel/finish dau tien thang.
        repo.record_snapshot(
            dict(snap, status="failed",
                 error={"code": "engine_internal_error"}))
        row = repo.find_by_job_id(job.job_id)
        self.assertEqual(row["status"], "succeeded")
        self.assertEqual(row["snapshot"]["status"], "succeeded")


class WorkspaceSweepTest(unittest.TestCase):
    """_recover_interrupted: store instance moi = 'process moi' — don
    trang thai do tien trinh truoc de lai."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.db = Path(self.tempdir.name) / "workspace.sqlite3"

    def test_sweep_marks_zombie_state(self):
        store = UploadWorkspaceStore(self.db)
        store.open_browser("w1", "brw_1")
        store.upsert_job("j_live", command="upload.prepare",
                         website_id="w1", status="waiting_user",
                         waiting_on="review")
        store.upsert_job("j_done", website_id="w1", status="succeeded")
        store.add_open_tabs("w1", [5, 6], run_id="run_1")
        store.close()

        store2 = UploadWorkspaceStore(self.db)
        self.addCleanup(store2.close)
        # Job non-terminal → failed; terminal giu nguyen.
        self.assertEqual(store2.job_for("j_live")["status"], "failed")
        self.assertIsNone(store2.job_for("j_live")["waiting_on"])
        self.assertEqual(store2.job_for("j_done")["status"], "succeeded")
        # Browser 'open' cua process cu → closed.
        self.assertIsNone(store2.current_browser("w1"))
        self.assertEqual(store2.browser_for("brw_1")["status"], "closed")
        # open_tabs mat chu so huu → xoa (chi la tai nguyen; khong suy ket
        # qua Luu nao duoc ghi lai).
        self.assertEqual(store2.open_tab_record_ids("w1"), [])

    def test_legacy_save_column_is_hidden_and_data_preserved(self):
        """DB cu truoc cutover con cot Save (`verified_record_ids`): store
        moi van doc/ghi job binh thuong, serializer khong lo cot do ra, va
        du lieu vat ly giu nguyen (khong migrate/xoa)."""
        legacy_value = json.dumps([9, 11])
        store = UploadWorkspaceStore(self.db)
        store.upsert_job("j_legacy", command="upload.prepare",
                         website_id="w1", record_ids=[1, 2],
                         status="waiting_user", waiting_on="review")
        store.close()

        # Mo phong DB cu: cot Save con nguyen, co du lieu lich su.
        conn = sqlite3.connect(str(self.db))
        try:
            conn.execute("ALTER TABLE workflow_jobs ADD COLUMN"
                         " verified_record_ids TEXT")
            conn.execute("UPDATE workflow_jobs SET verified_record_ids=?"
                         " WHERE job_id='j_legacy'", (legacy_value,))
            conn.commit()
        finally:
            conn.close()

        store2 = UploadWorkspaceStore(self.db)
        self.addCleanup(store2.close)
        row = store2.job_for("j_legacy")
        self.assertNotIn("verified_record_ids", row)
        self.assertEqual(row["record_ids"], [1, 2])
        self.assertEqual(row["command"], "upload.prepare")
        # Sweep cua process moi van chay: job non-terminal → failed.
        self.assertEqual(row["status"], "failed")
        self.assertIsNone(row["waiting_on"])
        # Ghi tiep tren cung row van hoat dong.
        store2.set_job_status("j_legacy", "succeeded")
        self.assertEqual(store2.job_for("j_legacy")["status"], "succeeded")

        conn = sqlite3.connect(str(self.db))
        try:
            kept = conn.execute(
                "SELECT verified_record_ids FROM workflow_jobs"
                " WHERE job_id='j_legacy'").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(kept, legacy_value)


# =====================================================================
# Lop 2 — FakePortal: crash/shutdown/reconcile khong replay upload
# =====================================================================

@unittest.skipUnless(tbw._engines_available(),
                     "upload_lab engine/openpyxl missing")
class UploadRecoveryTest(tbw.BrowserWorkflowCase):
    """Crash/restart o muc workflow — reuse bo fixture FakePortal."""

    def setUp(self):
        super().setUp()
        import upload_workspace
        # JobStore co repository that (cung workspace.sqlite3 voi
        # open_store) — test o muc wiring nhu production. super().setUp
        # da dang ky cleanup drain cho store cu — store do khong chay
        # job nao nen drain la no-op; store moi co cleanup rieng.
        self.repo = JobRepository(upload_workspace.workspace_db_path())
        self.jobs = JobStore(max_workers=6, repository=self.repo)
        self.addCleanup(lambda: self.jobs.drain(timeout=3))

    def _restart_jobstore(self):
        """'Process moi' o lop job: JobStore + repository moi tren cung
        file; giu lai de cleanup."""
        repo = JobRepository(tbw.upload_workspace.workspace_db_path())
        store = JobStore(max_workers=2, repository=repo)
        self.addCleanup(lambda: store.drain(timeout=2))
        return store

    # ------------------------------------------------------------ crash
    def test_crash_mid_review_row_failed_and_tabs_released(self):
        """Process chet giua review: workflow_jobs row → failed, browser
        row → closed, quyen so huu tab bi xa; khong ghi ket qua Luu."""
        run_id, ids = self.run_scan(tbw.CONTRACT_NOS[:2])
        bid = self.login()
        job = self.prepare(bid, run_id, ids)
        self.wait_status(job, "waiting_user")

        # "Chet process" o lop browser: giet thread khong qua shutdown —
        # loop finally dong session + nha wait, open_tabs con treo trong
        # store (khong ai so huu duoc nua).
        self.browser._stop.set()
        self.browser._thread.join(timeout=5)
        snap = self.wait_terminal(job)
        self.assertEqual(snap["status"], "failed")
        self.assertEqual(snap["error"]["code"], "engine_unavailable")

        # Store instance moi = process moi → sweep don di trang thai.
        tbw.upload_workspace.reset_store_for_tests()
        self.store = tbw.upload_workspace.open_store()

        self.assertEqual(
            self.store.open_tab_record_ids(tbw.WEBSITE), [])
        self.assertIsNone(self.store.current_browser(tbw.WEBSITE))
        # Ho so van la da chuan bi trong luot — khong suy ket qua Luu.
        for rid in ids:
            self.assertEqual(self.registry_status(rid), "prepared_dry_run")

    def test_crash_after_portal_save_keeps_local_progress_only(self):
        """Nguoi dung da bam Luu tren portal nhung process chet TRUOC khi
        dong tab: app khong ghi 'da Luu'; su that nam o so chinh thuc."""
        run_id, ids = self.run_scan(tbw.CONTRACT_NOS[:1])
        bid = self.login()
        job = self.prepare(bid, run_id, ids)
        self.wait_status(job, "waiting_user")
        # Chan idle poll: interval dai + cho nhip dang cho het → trang thai
        # tab chua duoc browser thread tieu thu.
        self.browser._poll_interval = 600
        time.sleep(0.25)
        self.session.user_save(ids[0])
        self.assertEqual(len(self.portal.saved_contract_nos), 1)

        # "Chet" khong graceful: mo store moi trong khi zombie thread con
        # block trong queue.get(600); zombie duoc don o cleanup qua
        # browser.shutdown → _poll_then_close.
        tbw.upload_workspace.reset_store_for_tests()
        self.store = tbw.upload_workspace.open_store()
        self.assertEqual(self.store.open_tab_record_ids(tbw.WEBSITE), [])
        self.assertEqual(self.registry_status(ids[0]), "prepared_dry_run")

        # Doi chieu lai bang so chinh thuc (tai/nap Excel): ho so da co
        # trong so → queue khong con chon mac dinh no nua.
        audit_id = self.run_audit(["101/2026"])
        queue = self.queue_get(run_id, audit_id=audit_id)
        row = next(r for r in queue["folder_rows"]
                   if r["record_id"] == ids[0])
        self.assertFalse(row["selected"])
        self.assertIn("da co trong Excel", row["ghi_chu"])

    def test_restart_materializes_engine_restarted_and_no_replay(self):
        """Restart giua luc prepare chay: JobStore moi materialize job cu
        thanh failed{engine_restarted}; resubmit cung command_id+payload
        tra zombie — handler prepare KHONG chay lai lan hai."""
        run_id, ids = self.run_scan(tbw.CONTRACT_NOS[:2])
        bid = self.login()
        gate = threading.Event()
        self.session.prepare_gate = gate          # chan trong engine op
        payload = self.v1(
            browser_id=bid, run_id=run_id, audit_id=None,
            queue_revision=self.store.queue_revision(run_id),
            record_ids=list(ids[:1]), chunk_size=5,
            cong_chung_vien=None, thu_ky=None)
        cid = str(uuid.uuid4())
        import command_registry as reg
        job = self.jobs.submit(cid, "upload.prepare",
                               reg.COMMANDS["upload.prepare"], payload)
        self.wait_until(
            lambda: "prepare_manifest" in self.session.calls,
            what="prepare da vao browser thread")
        self.assertEqual(job.snapshot()["status"], "running")

        jobs2 = self._restart_jobstore()
        zombie = jobs2.get(job.job_id)
        self.assertIsNotNone(zombie)
        zsnap = zombie.snapshot()
        self.assertEqual(zsnap["status"], "failed")
        self.assertEqual(zsnap["error"]["code"], "engine_restarted")
        self.assertTrue(zsnap["error"]["retryable"])
        self.assertEqual(zsnap["error"]["next_action"], "retry")

        before = self.session.prepare_calls
        same = jobs2.submit(cid, "upload.prepare",
                            reg.COMMANDS["upload.prepare"], payload)
        self.assertEqual(same.job_id, job.job_id)
        self.assertEqual(self.session.prepare_calls, before,
                         "handler prepare bi phat lai sau restart")

        with self.assertRaises(CommandError) as ctx:
            jobs2.submit(cid, "upload.prepare",
                         reg.COMMANDS["upload.prepare"],
                         dict(payload, record_ids=list(ids)))
        self.assertEqual(ctx.exception.code, "command_id_conflict")

        # Thu lai co chu y = command moi → duoc chay binh thuong.
        retry = jobs2.submit(str(uuid.uuid4()), "upload.prepare",
                             reg.COMMANDS["upload.prepare"], payload)
        self.assertNotEqual(retry.job_id, job.job_id)

        # Don dep: nha gate de handler cu thoat roi cancel job cu.
        gate.set()
        self.jobs.cancel(job.job_id)
        self.wait_terminal(job)
        # Retry job co the dang chay tren browser op — huy luon de
        # cleanup khong treo.
        jobs2.cancel(retry.job_id)

    # ------------------------------------------------------------ shutdown
    def test_graceful_shutdown_closes_browser_and_releases_tabs(self):
        """worker.shutdown: poll lan cuoi + dong phien; quyen so huu tab
        duoc xa; khong ghi ket qua Luu nao."""
        run_id, ids = self.run_scan(tbw.CONTRACT_NOS[:2])
        bid = self.login()
        job = self.prepare(bid, run_id, ids)
        self.wait_status(job, "waiting_user")
        self.session.user_save(ids[0])

        self.browser.shutdown(timeout=5)
        self.assertFalse(self.browser._thread.is_alive(),
                         "browser thread con song sau shutdown")
        # Tat ca tab da mat quyen so huu (phien da dong).
        self.assertEqual(self.store.open_tab_record_ids(tbw.WEBSITE), [])
        for rid in ids:
            self.assertEqual(self.registry_status(rid), "prepared_dry_run")
        # Job dang cho duoc nha → failed (browser chet), khong treo.
        snap = self.wait_terminal(job)
        self.assertEqual(snap["status"], "failed")
        self.assertEqual(snap["error"]["code"], "engine_unavailable")

    def test_call_after_shutdown_is_rejected_no_respawn(self):
        """Op den sau shutdown → engine_unavailable, worker KHONG spawn
        lai thread moi sau lenh tat."""
        bid = self.login()
        self.browser.shutdown(timeout=5)
        with self.assertRaises(CommandError) as ctx:
            self.browser.call("poll_manual_login",
                              website_id=tbw.WEBSITE)
        self.assertEqual(ctx.exception.code, "engine_unavailable")
        self.assertIsNone(self.browser._session)

    def test_shutdown_timeout_is_total_budget_not_per_phase(self):
        """Regression T5 fix1: shutdown(timeout) CHIA budget giua
        reconcile (_poll_then_close) va join — poll/close hang khong
        lam shutdown chan qua ~timeout. Truoc day reconcile nhan
        timeout-1 roi join nhan them timeout → ~2*timeout, vuot
        SHUTDOWN_GRACE_MS cua Electron → SIGKILL giua reconcile."""
        run_id, ids = self.run_scan(tbw.CONTRACT_NOS[:1])
        bid = self.login()
        job = self.prepare(bid, run_id, ids)
        self.wait_status(job, "waiting_user")

        # Lam browser hang ngay trong poll (giu 30s neu khong duoc nha)
        # — _poll_then_close khong co stop_event nen khong bi ngat.
        hang = threading.Event()
        orig_poll = self.session.poll_prepared_pages

        def blocked_poll():
            hang.wait(timeout=30)
            return orig_poll()

        self.session.poll_prepared_pages = blocked_poll
        try:
            t0 = time.monotonic()
            self.browser.shutdown(timeout=1.0)
            elapsed = time.monotonic() - t0
            # Code cu: reconcile 1.0s + join 1.0s ≈ 2.0s. Code moi:
            # tong <= ~timeout + overhead → phai duoi 1.75s.
            self.assertLess(
                elapsed, 1.75,
                f"shutdown chan {elapsed:.2f}s — budget khong duoc "
                "chia giua reconcile va join")
            # Sweep van chay sau join timeout: quyen so huu tab bi xa.
            self.assertEqual(
                self.store.open_tab_record_ids(tbw.WEBSITE), [])
        finally:
            # Nha gate de zombie thread (daemon) thoat — cleanup
            # browser.shutdown tiep theo khong phai cho 30s.
            hang.set()

        snap = self.wait_terminal(job)
        self.assertEqual(snap["status"], "failed")
        self.assertEqual(snap["error"]["code"], "engine_unavailable")

    # ------------------------------------------------- cancel/finish race
    def test_cancel_while_waiting_then_finish_review_keeps_canceled(self):
        """Cancel trong waiting_user → finish_review tre toi → wrong_job;
        job van canceled, tab khong bi coi la da Luu."""
        run_id, ids = self.run_scan(tbw.CONTRACT_NOS[:1])
        bid = self.login()
        job = self.prepare(bid, run_id, ids)
        self.wait_status(job, "waiting_user")
        self.jobs.cancel(job.job_id)
        snap = self.wait_terminal(job)
        self.assertEqual(snap["status"], "canceled")
        self.assertEqual(snap["error"]["code"], "user_canceled")
        self.assertFalse(snap["error"]["retryable"])

        # Cho handler don xong wait rec (finally: unregister_wait) — neu
        # finish_review toi TRUOC unregister thi confirm_wait van tra True
        # (release mot wait khong con ai cho la no-op). Diem dong bo dung
        # la "wait rec da go" — khong dua vao sleep.
        self.wait_until(
            lambda: job.job_id not in self.browser._waits,
            what="wait rec da duoc unregister sau cancel")

        fj = self.finish_review(bid, job.job_id)
        fsnap = self.wait_terminal(fj)
        self.assertEqual(fsnap["status"], "failed")
        self.assertEqual(fsnap["error"]["code"], "wrong_job")
        self.assertEqual(job.snapshot()["status"], "canceled")
        # 'finish_review' khong phai bang chung Luu — registry giu
        # prepared_dry_run, tab dang mo khong bien thanh saved.
        self.assertEqual(
            self.registry_status(ids[0]), "prepared_dry_run")
        # workflow_jobs row cung phai la canceled (khong de 'succeeded'
        # gia hay bi handler viet de lai).
        self.assertEqual(
            self.store.job_for(job.job_id)["status"], "canceled")

    # ------------------------------------------------------ partial/failed
    def test_all_records_failed_is_failed_not_partial(self):
        """Toan bo muc chuan bi loi → job failed + breakdown failed day
        du; khong con ho so chua ro nen retryable=True (retry an toan —
        record upload_failed van trong queue)."""
        run_id, ids = self.run_scan(tbw.CONTRACT_NOS[:2])
        bid = self.login()
        self.session.fail_record_ids = set(ids)
        job = self.prepare(bid, run_id, ids)
        snap = self.wait_terminal(job)
        self.assertEqual(snap["status"], "failed")
        self.assertEqual(snap["error"]["code"], "upload.partial_failure")
        self.assertTrue(snap["error"]["retryable"])
        self.assertEqual(snap["error"]["next_action"], "retry")
        bd = snap["result"]["data"]["breakdown"]
        self.assertEqual(bd["succeeded"], [])
        self.assertEqual(
            sorted(f["record_id"] for f in bd["failed"]), sorted(ids))
        for rid in ids:
            self.assertEqual(self.registry_status(rid), "upload_failed")

    def test_mixed_partial_keeps_breakdown_and_retryable(self):
        """Mot muc loi, con lai mo duoc → partial + breakdown per-record;
        khong co ho so chua ro → retryable=True."""
        run_id, ids = self.run_scan(tbw.CONTRACT_NOS[:3])
        bid = self.login()
        self.session.fail_record_ids = {ids[0]}
        job = self.prepare(bid, run_id, ids)
        self.wait_status(job, "waiting_user")
        fj = self.finish_review(bid, job.job_id)
        self.wait_terminal(fj)
        snap = self.wait_terminal(job)
        self.assertEqual(snap["status"], "partial")
        self.assertEqual(snap["error"]["code"], "upload.partial_failure")
        self.assertTrue(snap["error"]["retryable"])
        bd = snap["result"]["data"]["breakdown"]
        self.assertEqual(
            sorted(b["record_id"] for b in bd["succeeded"]),
            sorted(ids[1:]))
        self.assertEqual(
            [b["record_id"] for b in bd["failed"]], [ids[0]])
        self.assertEqual(bd["failed"][0]["stage"], "prepared")

    def test_failure_when_browser_lost_is_plain_retryable(self):
        """Browser chet giua review → job failed{engine_unavailable} va
        retryable=True (loi ha tang thuong); khong khoa vi ket qua Luu."""
        run_id, ids = self.run_scan(tbw.CONTRACT_NOS[:2])
        bid = self.login()
        job = self.prepare(bid, run_id, ids)
        self.wait_status(job, "waiting_user")
        self.session.crash()
        snap = self.wait_terminal(job)
        self.assertEqual(snap["status"], "failed")
        self.assertEqual(snap["error"]["code"], "engine_unavailable")
        self.assertTrue(snap["error"]["retryable"])
        self.assertEqual(snap["error"]["next_action"], "retry")
        details = snap["error"].get("details") or {}
        self.assertNotIn("needs_reconcile_record_ids", details)


if __name__ == "__main__":
    unittest.main(verbosity=2)

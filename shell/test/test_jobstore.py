"""Unit test JobStore — cancel semantics + drain + partial breakdown.

Chay: python test/test_jobstore.py  (chi can stdlib)
"""
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sidecar"))

from errors import CommandError  # noqa: E402
from jobstore import JobStore  # noqa: E402


def quick(job, payload):
    return {"kind": "ok", "data": {}, "evidence": [], "warnings": []}


def slow(job, payload):
    for _ in range(200):
        job.check_cancel()
        time.sleep(0.01)
    return {"kind": "ok", "data": {}}


def waiting(job, payload):
    job.set_waiting("finalize")
    while True:
        job.check_cancel()
        time.sleep(0.01)


def partial_bad(job, payload):
    return {"partial": True, "kind": "x", "data": {}}


def partial_ok(job, payload):
    return {"partial": True, "kind": "x",
            "data": {"breakdown": {"succeeded": ["a"], "failed": ["b"]}}}


def slow_with_result(job, payload):
    """Handler mang theo partial result khi bi cancel giua batch."""
    result = {"kind": "word_export_batch",
              "data": {"breakdown": {"succeeded": ["a.docx"],
                                     "failed": [],
                                     "skipped": ["b.docx"]}}}
    for _ in range(200):
        job.check_cancel(result)
        time.sleep(0.01)
    return {"kind": "ok", "data": {}}


def failed_with_result(job, payload):
    raise CommandError(
        "word_batch_failed", "tat ca file deu loi",
        result={"kind": "word_export_batch",
                "data": {"breakdown": {"succeeded": [],
                                       "failed": ["a.docx"],
                                       "skipped": []}}})


def waiting_then_resume(job, payload):
    job.set_waiting("confirm")
    while job.snapshot()["status"] == "waiting_user":
        job.check_cancel()
        time.sleep(0.01)
    return {"kind": "ok", "data": {}}


def resumer(store, job_id, delay=0.15):
    """Goi job.resume() tu thread khac sau delay — nhu engine nhan xong
    buoc nguoi dung."""
    def _go():
        time.sleep(delay)
        store.get(job_id).resume()
    threading.Thread(target=_go, daemon=True).start()


def wait_terminal(store, job_id, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        snap = store.get(job_id).snapshot()
        if snap["status"] in ("succeeded", "failed", "canceled", "partial"):
            return snap
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} khong terminal")


class JobStoreTest(unittest.TestCase):
    def setUp(self):
        self.store = JobStore(max_workers=4)

    def tearDown(self):
        self.store.drain(timeout=2)

    def test_user_cancel_running(self):
        job = self.store.submit("c-1", "diag.slow_task", slow, {})
        self.store.cancel(job.job_id)
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "canceled")
        self.assertEqual(snap["error"]["code"], "user_canceled")
        self.assertFalse(snap["error"]["retryable"])

    def test_cancel_waiting_user_applies_immediately(self):
        job = self.store.submit("c-2", "diag.slow_task", waiting, {})
        deadline = time.time() + 5
        while job.snapshot()["status"] != "waiting_user":
            self.assertLess(time.time(), deadline)
            time.sleep(0.02)
        self.store.cancel(job.job_id)
        snap = job.snapshot()
        self.assertEqual(snap["status"], "canceled")
        self.assertEqual(snap["error"]["code"], "user_canceled")

    def test_cancel_terminal_409(self):
        job = self.store.submit("c-3", "diag.slow_task", quick, {})
        wait_terminal(self.store, job.job_id)
        self.assertEqual(self.store.cancel(job.job_id), "terminal")

    def test_drain_marks_engine_shutdown(self):
        job = self.store.submit("c-4", "diag.slow_task", slow, {})
        self.store.drain(timeout=3)
        snap = job.snapshot()
        self.assertEqual(snap["status"], "canceled")
        self.assertEqual(snap["error"]["code"], "engine_shutdown")
        self.assertTrue(snap["error"]["retryable"])
        with self.assertRaises(CommandError) as ctx:
            self.store.submit("c-5", "diag.slow_task", quick, {})
        self.assertEqual(ctx.exception.code, "engine_shutdown")

    def test_partial_requires_breakdown(self):
        job = self.store.submit("c-6", "diag.slow_task", partial_bad, {})
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "failed")
        self.assertEqual(snap["error"]["code"], "validation_error")

    def test_partial_with_breakdown_ok(self):
        job = self.store.submit("c-7", "diag.slow_task", partial_ok, {})
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "partial")
        self.assertEqual(
            snap["result"]["data"]["breakdown"]["succeeded"], ["a"])

    def test_idempotent_command_id(self):
        j1 = self.store.submit("dup-1", "diag.slow_task", slow, {})
        j2 = self.store.submit("dup-1", "diag.slow_task", slow, {})
        self.assertEqual(j1.job_id, j2.job_id)
        self.store.cancel(j1.job_id)
        wait_terminal(self.store, j1.job_id)

    def test_resume_waiting_to_running(self):
        # contract §2: waiting_user -> running khi buoc nguoi dung xong
        job = self.store.submit("c-9", "diag.waiting_task",
                                waiting_then_resume, {})
        deadline = time.time() + 5
        while job.snapshot()["status"] != "waiting_user":
            self.assertLess(time.time(), deadline)
            time.sleep(0.02)
        resumer(self.store, job.job_id)
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "succeeded")
        self.assertIsNone(snap["waiting_on"])

    def test_resume_tren_job_khong_waiting_la_loi(self):
        job = self.store.submit("c-10", "diag.slow_task", quick, {})
        wait_terminal(self.store, job.job_id)
        with self.assertRaises(CommandError) as ctx:
            job.resume()
        self.assertEqual(ctx.exception.code, "validation_error")

    def test_set_waiting_validates_enum(self):
        def bad_waiting(job, payload):
            job.set_waiting("bogus")
        job = self.store.submit("c-8", "diag.slow_task", bad_waiting, {})
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "failed")

    def test_cancel_giu_partial_result(self):
        # contract word_export_batch: canceled job van can result.data.
        # breakdown.skipped len wire (MIN-115).
        job = self.store.submit("c-11", "diag.slow_task",
                                slow_with_result, {})
        self.assertEqual(self.store.cancel(job.job_id), "ok")
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "canceled")
        self.assertEqual(snap["error"]["code"], "user_canceled")
        self.assertEqual(
            snap["result"]["data"]["breakdown"]["skipped"], ["b.docx"])

    def test_failed_giu_result_payload(self):
        job = self.store.submit("c-12", "diag.slow_task",
                                failed_with_result, {})
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "failed")
        self.assertEqual(snap["error"]["code"], "word_batch_failed")
        self.assertEqual(
            snap["result"]["data"]["breakdown"]["failed"], ["a.docx"])

    # ---------- MIN-69 T5: terminal-state integrity + command identity

    def _wait_waiting(self, job, timeout=5):
        deadline = time.time() + timeout
        while job.snapshot()["status"] != "waiting_user":
            self.assertLess(time.time(), deadline)
            time.sleep(0.02)

    def test_cancel_in_waiting_beats_late_handler_failure(self):
        """Race huy/hoan tat (T5): huy trong waiting_user → handler ngu
        tinh nem loi sau do — terminal cuoi van canceled, khong bi ghi de
        thanh failed. Gate Event kiem soat, khong sleep timing."""
        gate = threading.Event()

        def late_fail(job, payload):
            job.set_waiting("review")
            gate.wait(5)
            raise CommandError("engine_unavailable", "boom",
                               retryable=True)

        job = self.store.submit("c-race1", "diag.x", late_fail, {})
        self._wait_waiting(job)
        self.store.cancel(job.job_id)
        self.assertEqual(job.snapshot()["status"], "canceled")
        gate.set()  # handler tiep tuc → nem CommandError muon
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "canceled")
        self.assertEqual(snap["error"]["code"], "user_canceled")

    def test_cancel_in_waiting_beats_late_success(self):
        """Huy trong waiting → handler thu resume + tra ket qua — van
        canceled (resume tren job da huy phai abort, khong duoc tro lai
        running roi succeeded)."""
        gate = threading.Event()

        def late_ok(job, payload):
            job.set_waiting("review")
            gate.wait(5)
            job.resume()
            return {"kind": "ok", "data": {}}

        job = self.store.submit("c-race2", "diag.x", late_ok, {})
        self._wait_waiting(job)
        self.store.cancel(job.job_id)
        gate.set()
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "canceled")
        self.assertEqual(snap["error"]["code"], "user_canceled")

    def test_cancel_in_waiting_beats_late_progress_write(self):
        """report_progress sau cancel phai abort handler (CancelledByUser)
        thay vi ghi progress len job da terminal."""
        gate = threading.Event()

        def late_progress(job, payload):
            job.set_waiting("review")
            gate.wait(5)
            job.report_progress(1, 2, "sau huy")   # phai raise
            return {"kind": "ok", "data": {}}

        job = self.store.submit("c-race3", "diag.x", late_progress, {})
        self._wait_waiting(job)
        self.store.cancel(job.job_id)
        gate.set()
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "canceled")
        self.assertIsNone(snap["progress"],
                          "progress khong duoc ghi len job da huy")

    def test_finish_before_cancel_is_terminal(self):
        """Cancel-after-finish: job da succeeded → cancel tra 'terminal'
        (409 o API) va snapshot khong doi."""
        job = self.store.submit("c-f1", "diag.x", quick, {})
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "succeeded")
        self.assertEqual(self.store.cancel(job.job_id), "terminal")
        snap2 = job.snapshot()
        self.assertEqual(snap2["status"], "succeeded")
        self.assertIsNotNone(snap2["result"])
        self.assertIsNone(snap2["error"])

    def test_finish_never_overwrites_terminal(self):
        """_finish vao job da terminal bi tu choi cho moi huong —
        succeeded/failed/partial/canceled deu bat bien."""
        job = self.store.submit("c-f2", "diag.x", quick, {})
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "succeeded")
        self.assertFalse(job._finish("failed"))
        self.assertFalse(job._finish("partial", result={"k": 1}))
        self.assertFalse(job._finish("canceled"))
        self.assertFalse(job.request_cancel(code="engine_shutdown"))
        snap2 = job.snapshot()
        self.assertEqual(snap2["status"], "succeeded")
        self.assertIsNone(snap2["error"])

    def test_command_id_conflict_on_different_payload(self):
        """Cung command_id + noi dung khac → command_id_conflict (khong
        tra job cu, khong ghi de identity); cung noi dung → idempotent."""
        j1 = self.store.submit("dup-x", "diag.slow_task", quick,
                               {"steps": 1})
        wait_terminal(self.store, j1.job_id)
        with self.assertRaises(CommandError) as ctx:
            self.store.submit("dup-x", "diag.slow_task", quick,
                              {"steps": 2})
        self.assertEqual(ctx.exception.code, "command_id_conflict")
        self.assertFalse(ctx.exception.retryable)
        j2 = self.store.submit("dup-x", "diag.slow_task", quick,
                               {"steps": 1})
        self.assertEqual(j2.job_id, j1.job_id)

    def test_partial_all_failed_maps_to_failed(self):
        """Toan bo muc loi → job failed (khong phai partial); breakdown
        giu nguyen de khach doc chi tiet tung muc."""
        def all_failed(job, payload):
            return {"partial": True, "kind": "x",
                    "data": {"breakdown": {
                        "succeeded": [],
                        "failed": [{"record_id": 7, "stage": "prepared",
                                    "code": "upload_failed",
                                    "message": "fake"}]}}}

        job = self.store.submit("c-af", "diag.x", all_failed, {})
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "failed")
        self.assertEqual(
            snap["result"]["data"]["breakdown"]["failed"][0]
            ["record_id"], 7)

    def test_next_action_trong_enum(self):
        """Error next_action chi nam trong enum contract §8."""
        allowed = {"login_required", "pick_files", "retry",
                   "contact_admin", None}

        def fail_with_bad_next(job, payload):
            raise CommandError("engine_unavailable", "x", retryable=True,
                               next_action="retry")

        job = self.store.submit("c-na", "diag.x", fail_with_bad_next, {})
        snap = wait_terminal(self.store, job.job_id)
        self.assertIn(snap["error"]["next_action"], allowed)


if __name__ == "__main__":
    unittest.main(verbosity=2)

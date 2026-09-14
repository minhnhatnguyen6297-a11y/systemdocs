"""Unit test JobStore — cancel semantics + drain + partial breakdown.

Chay: python test/test_jobstore.py  (chi can stdlib)
"""
import sys
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

    def test_set_waiting_validates_enum(self):
        def bad_waiting(job, payload):
            job.set_waiting("bogus")
        job = self.store.submit("c-8", "diag.slow_task", bad_waiting, {})
        snap = wait_terminal(self.store, job.job_id)
        self.assertEqual(snap["status"], "failed")


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Job registry in-memory theo desktopcommand.v1 §4-5.

Idempotency: command_id → job_id. Terminal: succeeded/failed/canceled/partial.
Cancel user → error.code=user_canceled; cancel do engine shutdown →
error.code=engine_shutdown (contract §5). Handler dang chay PHAI goi
job.check_cancel() dinh ky — khi job o waiting_user thi cancel ap dung ngay.
"""
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from errors import CommandError, error_object

TERMINAL = {"succeeded", "failed", "canceled", "partial"}
WAITING_ON_ENUM = {"login", "review", "finalize", "confirm"}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z")


class CancelledByUser(Exception):
    pass


class Job:
    def __init__(self, command_id, command):
        self.job_id = "j_" + uuid.uuid4().hex[:12]
        self.command_id = command_id
        self.command = command
        self.status = "accepted"
        self.waiting_on = None
        self.progress = None
        self.result = None
        self.error = None
        self.updated_at = _now()
        self._cancel = threading.Event()
        self._cancel_code = "user_canceled"
        self._cancel_message = "nguoi dung huy job"
        self._lock = threading.Lock()

    def check_cancel(self):
        if self._cancel.is_set():
            raise CancelledByUser()

    def request_cancel(self, code="user_canceled",
                       message="nguoi dung huy job"):
        """→ False neu job da terminal (tranh TOCTOU giua check va cancel)."""
        with self._lock:
            if self.status in TERMINAL:
                return False
            self._cancel_code = code
            self._cancel_message = message
            self._cancel.set()
            # waiting_user: khong co gi dang chay — ket thuc ngay
            if self.status == "waiting_user":
                self._finish_locked("canceled", error=error_object(
                    code, message, retryable=(code != "user_canceled"),
                    job_id=self.job_id))
            return True

    def report_progress(self, done, total, label=""):
        with self._lock:
            self.progress = {"done": done, "total": total,
                             "current_label": label}
            self.updated_at = _now()

    def set_waiting(self, waiting_on):
        if waiting_on not in WAITING_ON_ENUM:
            raise CommandError("validation_error",
                               f"waiting_on khong hop le: {waiting_on!r}")
        with self._lock:
            self.status = "waiting_user"
            self.waiting_on = waiting_on
            self.updated_at = _now()

    def resume(self):
        """waiting_user -> running khi buoc can nguoi da xong (contract §2)."""
        with self._lock:
            if self.status != "waiting_user":
                raise CommandError(
                    "validation_error",
                    f"resume khi status={self.status}, khong phai waiting_user")
            self.status = "running"
            self.waiting_on = None
            self.updated_at = _now()

    def snapshot(self):
        with self._lock:
            return {
                "contract_version": "desktopcommand.v1",
                "job_id": self.job_id,
                "command_id": self.command_id,
                "command": self.command,
                "status": self.status,
                "waiting_on": self.waiting_on,
                "progress": self.progress,
                "result": self.result,
                "error": self.error,
                "updated_at": self.updated_at,
            }

    def _finish_locked(self, status, result=None, error=None):
        self.status = status
        self.waiting_on = None
        self.result = result
        self.error = error
        self.updated_at = _now()

    def _finish(self, status, result=None, error=None):
        with self._lock:
            self._finish_locked(status, result, error)


class JobStore:
    def __init__(self, max_workers=4):
        self._by_id = {}
        self._by_command = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._accepting = True

    def submit(self, command_id, command, handler, payload):
        """Idempotent: command_id da thay → tra job cu."""
        with self._lock:
            if not self._accepting:
                raise CommandError("engine_shutdown", "sidecar dang tat",
                                   retryable=True)
            if command_id in self._by_command:
                return self._by_id[self._by_command[command_id]]
            job = Job(command_id, command)
            self._by_id[job.job_id] = job
            self._by_command[command_id] = job.job_id
            self._executor.submit(self._run, job, handler, payload or {})
            return job

    def get(self, job_id):
        return self._by_id.get(job_id)

    def cancel(self, job_id):
        """→ 'ok' | 'terminal' | 'missing'."""
        job = self._by_id.get(job_id)
        if job is None:
            return "missing"
        return "ok" if job.request_cancel() else "terminal"

    def _run(self, job, handler, payload):
        with job._lock:
            if job._cancel.is_set():
                job._finish_locked("canceled", error=error_object(
                    job._cancel_code, job._cancel_message,
                    retryable=(job._cancel_code != "user_canceled"),
                    job_id=job.job_id))
                return
            job.status = "running"
            job.updated_at = _now()
        try:
            result = handler(job, payload)
            job.check_cancel()
            status = "succeeded"
            # "partial" la marker noi bo handler->jobstore — pop khoi dict
            # de khong len wire (result chi mang kind/data/evidence/
            # warnings/source_files).
            partial = bool(isinstance(result, dict)
                           and result.pop("partial", None))
            if partial:
                bd = (result.get("data") or {}).get("breakdown") or {}
                if not isinstance(bd.get("succeeded"), list) \
                        or not isinstance(bd.get("failed"), list):
                    raise CommandError(
                        "validation_error",
                        "partial bat buoc data.breakdown={succeeded,failed}")
                status = "partial"
            job._finish(status, result=result)
        except CancelledByUser:
            with job._lock:
                job._finish_locked("canceled", error=error_object(
                    job._cancel_code, job._cancel_message,
                    retryable=(job._cancel_code != "user_canceled"),
                    job_id=job.job_id))
        except CommandError as exc:
            job._finish("failed", error=error_object(
                exc.code, exc.message, exc.retryable, exc.next_action,
                job.job_id, exc.details))
        except Exception as exc:  # noqa: BLE001 — boundary cuoi cung
            job._finish("failed", error=error_object(
                "engine_internal_error", f"{type(exc).__name__}: {exc}",
                retryable=True, job_id=job.job_id))

    def drain(self, timeout=8):
        """Ngung nhan job moi; cancel non-terminal voi engine_shutdown;
        cho toi da `timeout` giay roi bo (main se kill sau grace)."""
        with self._lock:
            self._accepting = False
            for job in self._by_id.values():
                job.request_cancel(
                    code="engine_shutdown",
                    message="engine dang tat; job co the chay lai")
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if all(j.status in TERMINAL for j in self._by_id.values()):
                    break
            time.sleep(0.05)
        self._executor.shutdown(wait=False, cancel_futures=True)

    @property
    def accepting(self):
        return self._accepting

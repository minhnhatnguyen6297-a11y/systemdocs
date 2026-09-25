"""Job registry + command journal theo desktopcommand.v1 §4-5.

Idempotency: command_id + request hash → job_id. Cung command_id nhung
noi dung request khac → command_id_conflict (contract §5 /
upload.workflow.v1 §8).

Terminal-state integrity (MIN-69 T5): succeeded/failed/canceled/partial
la BAT BIEN — moi transition vao terminal sau do bi tu choi, va cancel
da chap nhan LUON thang cuoc dua finish: handler tra result hay nem loi
sau khi bi huy van ket luan `canceled` (khong ghi de thanh succeeded/
failed/partial).

Recovery: khi co JobRepository (workspace.sqlite3), moi transition ghi
snapshot xuong dia; process moi materialize lai job cu lam snapshot
read-only — job non-terminal cua tien trinh truoc →
failed{engine_restarted} va handler KHONG bao gio chay lai (khong auto
replay upload khi ket qua chua ro, contract §7.4/§5).
"""
import hashlib
import json
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


def hash_request(command, payload):
    """Identity cua mot submit = hash(command + payload canonical).

    On dinh xuyen restart (khong chua handler object/transient state);
    dung de phan biet "retry cung noi dung" (tra job cu) vs
    "command_id cu, noi dung moi" (command_id_conflict).
    """
    return hashlib.sha256(json.dumps(
        {"command": command, "payload": payload if payload is not None else {}},
        sort_keys=True, default=str).encode("utf-8")).hexdigest()


class CancelledByUser(Exception):
    """Huy giua chung — co the mang partial result len wire (MIN-115)."""

    def __init__(self, result=None):
        super().__init__("job bi huy")
        self.result = result


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
        self.request_hash = None
        self._cancel = threading.Event()
        self._cancel_code = "user_canceled"
        self._cancel_message = "nguoi dung huy job"
        self._lock = threading.Lock()
        # Listeners (JobStore persist, adapter mirror workflow_jobs) —
        # goi NGOAI _lock sau moi transition; exception bi nuot.
        self._listeners = []

    def _notify(self):
        """Bao listeners sau transition — goi ngoai lock de listener doc
        snapshot() khong deadlock. Listener loi khong duoc che job."""
        for listener in list(self._listeners):
            try:
                listener(self)
            except Exception:
                pass

    def check_cancel(self, result=None):
        """Cancel checkpoint; `result` (neu co) di len wire khi job canceled —
        vd word batch tra breakdown.skipped (contract, MIN-115)."""
        if self._cancel.is_set():
            raise CancelledByUser(result)

    def request_cancel(self, code="user_canceled",
                       message="nguoi dung huy job"):
        """→ False neu job da terminal (tranh TOCTOU giua check va cancel).

        accepted/waiting_user: khong co engine work dang chay (task chua
        bat dau hoac dang cho nguoi) — ket thuc ngay o canceled; khong de
        job accepted bi cancel_futures bo sot roi treo non-terminal.
        running: dat flag; _run/handler ket thuc qua
        check_cancel/set_waiting/resume/report_progress."""
        with self._lock:
            if self.status in TERMINAL:
                return False
            self._cancel_code = code
            self._cancel_message = message
            self._cancel.set()
            if self.status in ("accepted", "waiting_user"):
                self._finish_locked("canceled", error=error_object(
                    code, message, retryable=(code != "user_canceled"),
                    next_action="retry" if code != "user_canceled" else None,
                    job_id=self.job_id))
        self._notify()
        return True

    def report_progress(self, done, total, label=""):
        with self._lock:
            if self.status in TERMINAL or self._cancel.is_set():
                # Cancel da chap nhan → handler phai dung thay vi ghi
                # progress len job da chet (post-cancel writes).
                raise CancelledByUser()
            self.progress = {"done": done, "total": total,
                             "current_label": label}
            self.updated_at = _now()
        # progress khong persist — recovery chi can identity + terminal.

    def set_waiting(self, waiting_on):
        if waiting_on not in WAITING_ON_ENUM:
            raise CommandError("validation_error",
                               f"waiting_on khong hop le: {waiting_on!r}")
        aborted = False
        with self._lock:
            if self._cancel.is_set() and self.status not in TERMINAL:
                # Cancel toi trong luc handler chuan bi vao waiting —
                # ket thuc canceled ngay, khong cho quay lai waiting_user.
                self._finish_locked("canceled", error=error_object(
                    self._cancel_code, self._cancel_message,
                    retryable=(self._cancel_code != "user_canceled"),
                    next_action="retry"
                    if self._cancel_code != "user_canceled" else None,
                    job_id=self.job_id))
            if self.status in TERMINAL:
                aborted = True
            else:
                self.status = "waiting_user"
                self.waiting_on = waiting_on
                self.updated_at = _now()
        self._notify()
        if aborted:
            raise CancelledByUser()

    def resume(self):
        """waiting_user -> running khi buoc can nguoi da xong (contract §2).

        Cancel da chap nhan → CancelledByUser (uu tien huy cua nguoi dung);
        terminal khac (khong do cancel) → validation_error."""
        with self._lock:
            if self._cancel.is_set():
                raise CancelledByUser()
            if self.status != "waiting_user":
                raise CommandError(
                    "validation_error",
                    f"resume khi status={self.status}, khong phai "
                    "waiting_user")
            self.status = "running"
            self.waiting_on = None
            self.updated_at = _now()
        self._notify()

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
        """DUOI _lock. Tra True neu da ghi terminal; False neu da terminal —
        terminal la bat bien (contract §5), khong ghi de.

        Cancel-wins: _cancel da set nhung status muon ghi khong phai
        canceled → ep ve canceled voi cancel error da luu."""
        if self.status in TERMINAL:
            return False
        if self._cancel.is_set() and status != "canceled":
            status = "canceled"
            result = None
            error = error_object(
                self._cancel_code, self._cancel_message,
                retryable=(self._cancel_code != "user_canceled"),
                next_action="retry"
                if self._cancel_code != "user_canceled" else None,
                job_id=self.job_id)
        self.status = status
        self.waiting_on = None
        self.result = result
        self.error = error
        self.updated_at = _now()
        return True

    def _finish(self, status, result=None, error=None):
        """Tra True neu transition duoc ap dung (False = da terminal)."""
        with self._lock:
            applied = self._finish_locked(status, result, error)
        if applied:
            self._notify()
        return applied


class JobStore:
    """Registry in-memory + (tuy chon) JobRepository ben.

    repository: khi co, moi transition persist vao workspace.sqlite3 va
    job cua process truoc duoc materialize lai — non-terminal →
    failed{engine_restarted} (snapshot doc-only, handler khong chay lai);
    command_id duoc doi chieu theo request hash xuyen restart.
    """

    def __init__(self, max_workers=4, repository=None):
        self._by_id = {}
        self._by_command = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._accepting = True
        self._repository = repository
        if repository is not None:
            for row in repository.load_unfinished():
                with self._lock:
                    self._register(self._materialize(row))

    # ------------------------------------------------------------ registry
    def _register(self, job):
        """DUOI self._lock."""
        self._by_id[job.job_id] = job
        self._by_command[job.command_id] = job.job_id

    def _persist_job(self, job):
        """Listener ghi snapshot xuong repository — best-effort, khong bao
        gio de loi ghi dia chet job."""
        repo = self._repository
        if repo is None:
            return
        try:
            repo.record_snapshot(job.snapshot())
        except Exception:
            pass

    def _materialize(self, row):
        """Tai mot job tu repository row thanh snapshot read-only.

        Row non-terminal (process truoc chet giua chung) →
        failed{engine_restarted, retryable} theo contract §5/§7.4 — va ghi
        nguoc lai marker terminal de row khong con non-terminal."""
        snap = row["snapshot"]
        job = Job(row["command_id"], row["command"])
        job.job_id = row["job_id"]
        job.request_hash = row["request_hash"]
        status = snap.get("status") or "failed"
        with job._lock:
            if status in TERMINAL:
                job.status = status
                job.waiting_on = snap.get("waiting_on")
                job.progress = snap.get("progress")
                job.result = snap.get("result")
                job.error = snap.get("error")
                job.updated_at = snap.get("updated_at") or job.updated_at
            else:
                job._finish_locked("failed", error=error_object(
                    "engine_restarted",
                    "engine khoi dong lai giua chung; job co the chay lai",
                    retryable=True, next_action="retry", job_id=job.job_id))
        if self._repository is not None:
            job._listeners.append(self._persist_job)
            if status not in TERMINAL:
                # Persist marker terminal ngay — crash tiep theo van thay
                # job da ket thuc dung nghia.
                self._persist_job(job)
        return job

    def _restore_by_command_locked(self, command_id):
        """DUOI self._lock — materialize job cu theo command_id (restart)."""
        if self._repository is None:
            return None
        try:
            row = self._repository.find_by_command_id(command_id)
        except Exception:
            return None
        if row is None:
            return None
        job = self._materialize(row)
        self._register(job)
        return job

    # ------------------------------------------------------------ API
    def submit(self, command_id, command, handler, payload):
        """Idempotent: command_id + cung noi dung → job cu (ke ca job da
        terminal hoac job duoc phuc hoi sau restart — handler khong chay
        lai). command_id + noi dung khac → command_id_conflict."""
        request_hash = hash_request(command, payload)
        with self._lock:
            if not self._accepting:
                raise CommandError("engine_shutdown", "sidecar dang tat",
                                   retryable=True)
            job_id = self._by_command.get(command_id)
            job = self._by_id.get(job_id) if job_id else None
            if job is None:
                job = self._restore_by_command_locked(command_id)
            if job is not None:
                if job.request_hash and job.request_hash != request_hash:
                    raise CommandError(
                        "command_id_conflict",
                        "command_id da duoc dung cho mot request khac — "
                        "retry co chu y phai dung command_id moi",
                        retryable=False)
                return job
            job = Job(command_id, command)
            job.request_hash = request_hash
            if self._repository is not None:
                job._listeners.append(self._persist_job)
                self._repository.record_submit(job)  # raise → chua register
            self._register(job)
            self._executor.submit(self._run, job, handler, payload or {})
            return job

    def get(self, job_id):
        """Job theo id — ke ca job cua process truoc (reconnect theo
        job_id sau restart, contract §5): materialize lazy tu repository."""
        job = self._by_id.get(job_id)
        if job is None and self._repository is not None:
            try:
                row = self._repository.find_by_job_id(job_id)
            except Exception:
                row = None
            if row is not None:
                with self._lock:
                    job = self._by_id.get(job_id)
                    if job is None:
                        job = self._materialize(row)
                        self._register(job)
        return job

    def cancel(self, job_id):
        """→ 'ok' | 'terminal' | 'missing'."""
        job = self.get(job_id)
        if job is None:
            return "missing"
        return "ok" if job.request_cancel() else "terminal"

    def _run(self, job, handler, payload):
        with job._lock:
            if job._cancel.is_set():
                job._finish_locked("canceled", error=error_object(
                    job._cancel_code, job._cancel_message,
                    retryable=(job._cancel_code != "user_canceled"),
                    next_action="retry"
                    if job._cancel_code != "user_canceled" else None,
                    job_id=job.job_id))
                finished_early = True
            else:
                job.status = "running"
                job.updated_at = _now()
                finished_early = False
        job._notify()
        if finished_early:
            return
        try:
            result = handler(job, payload)
            status = "succeeded"
            error = None
            # "partial" la marker noi bo handler->jobstore — pop khoi dict
            # de khong len wire (result chi mang kind/data/evidence/
            # warnings/source_files).
            partial = bool(isinstance(result, dict)
                           and result.pop("partial", None))
            if partial:
                bd = (result.get("data") or {}).get("breakdown") or {}
                ok_list = bd.get("succeeded")
                fail_list = bd.get("failed")
                if not isinstance(ok_list, list) \
                        or not isinstance(fail_list, list):
                    raise CommandError(
                        "validation_error",
                        "partial bat buoc data.breakdown={succeeded,failed}")
                if fail_list and not ok_list:
                    # Toan bo muc deu loi → job failed, KHONG phai partial
                    # (contract §5/§6.14: partial nghia la co ca thanh cong
                    # lan that bai). Result (breakdown) van giu de khach
                    # doc chi tiet tung muc.
                    status = "failed"
                else:
                    status = "partial"
                # §6.14: partial/failed do batch kem error.code
                # upload.partial_failure len job.error — client doc
                # next_action/retryable tu day, khong phai dao result.
                error = result.get("error")
                if not isinstance(error, dict):
                    error = error_object(
                        "upload.partial_failure",
                        "mot phan hoac toan bo muc trong batch deu loi",
                        retryable=True, next_action="retry")
                if error.get("job_id") is None:
                    error = dict(error, job_id=job.job_id)
            # Cancel roi vao khe giua handler-return va finish van giu
            # result len wire (MIN-115 + MIN-110 review finding).
            job.check_cancel(result)
            job._finish(status, result=result, error=error)
        except CancelledByUser as exc:
            with job._lock:
                job._finish_locked("canceled", result=exc.result,
                                   error=error_object(
                    job._cancel_code, job._cancel_message,
                    retryable=(job._cancel_code != "user_canceled"),
                    next_action="retry"
                    if job._cancel_code != "user_canceled" else None,
                    job_id=job.job_id))
            # _finish_locked khong tu notify — bat buoc phai notify de
            # listener persist snapshot terminal va danh thuc waiters;
            # thieu thi repository giu non-terminal → process sau resync
            # nham thanh failed{engine_restarted}.
            job._notify()
        except CommandError as exc:
            job._finish("failed", result=exc.result,
                        error=error_object(
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
        all_done = False
        while time.time() < deadline:
            with self._lock:
                all_done = all(j.status in TERMINAL
                               for j in self._by_id.values())
            if all_done:
                break
            time.sleep(0.05)
        # Moi job terminal → moi handler da return (_finish chay trong
        # _run SAU handler) — phan con lai tren executor chi la
        # notify+persist (ms). wait=True de snapshot terminal ghi xuong
        # journal TRUOC khi dong repo — neu khong, dong repo som lam mat
        # 'canceled' va process sau doc nham 'running' → engine_restarted.
        # Neu van con job non-terminal (handler treo) → khong cho.
        self._executor.shutdown(wait=all_done, cancel_futures=True)
        if self._repository is not None:
            try:
                self._repository.close()
            except Exception:
                pass

    @property
    def accepting(self):
        return self._accepting

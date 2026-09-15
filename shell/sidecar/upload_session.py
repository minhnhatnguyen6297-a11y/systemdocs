"""Upload session bridge — Playwright sync API tren MOT thread chuyen biet.

Mirror ui_qt/workers.py:UploadWorker — engine (NamDinhUploaderSession) bat
buoc sync Playwright tren mot thread duy nhat. Sidecar giu mot worker thread
`g1-upload-browser` nhan operation qua queue; command handler submit op va
doi Future.

waiting_user: session_start dat job vao waiting_user('login') va doi event
`confirm_login` (command upload.confirm_login) hoac cancel. Khong bao gio
tu finalize — prepare chi mo tab da dien (dry-run), nguoi dung save trong
Chromium (spec MIN-69).
"""
import queue
import threading

from errors import CommandError
from engine_roots import engine_root, import_engine_module

LOGIN_WAIT_TIMEOUT_S = 15 * 60
REVIEW_WAIT_TIMEOUT_S = 60 * 60


class _BrowserWorker:
    """Mot thread so huu NamDinhUploaderSession — nhan (name, args) → Future."""

    def __init__(self):
        self._queue = queue.Queue()
        self._thread = None
        self._session = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        # Event ma command confirm_login set de giai phong job dang waiting.
        self.login_confirmed = threading.Event()
        self.review_finished = threading.Event()

    def _ensure_thread(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._loop, name="g1-upload-browser", daemon=True)
            self._thread.start()

    def call(self, op, *args, **kwargs):
        """Chay fn session tren browser thread, tra ket qua/raise loi."""
        self._ensure_thread()
        fut = _Future()
        self._queue.put((op, args, kwargs, fut))
        return fut.result()

    def _loop(self):
        while not self._stop.is_set():
            try:
                op, args, kwargs, fut = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                fut.set_result(self._dispatch(op, *args, **kwargs))
            except Exception as exc:  # noqa: BLE001 — boundary
                fut.set_error(exc)
        self._close_session()

    def _dispatch(self, op, *args, **kwargs):
        uploader = import_engine_module("upload_lab", "playwright_uploader")
        if op == "_close":
            self._close_session()
            return {"closed": True}
        session = self._ensure_session()
        return getattr(session, op)(*args, **kwargs)

    def _ensure_session(self):
        """Chi goi tren browser thread."""
        if self._session is None:
            uploader = import_engine_module(
                "upload_lab", "playwright_uploader")
            root = engine_root("upload_lab")
            self._session = uploader.NamDinhUploaderSession(
                uploader.load_uploader_settings(root),
                working_dir=root)
        return self._session

    def _close_session(self):
        if self._session is not None:
            try:
                self._session.close()
            finally:
                self._session = None
        self.login_confirmed.clear()
        self.review_finished.clear()


class _Future:
    def __init__(self):
        self._done = threading.Event()
        self._result = None
        self._error = None

    def set_result(self, value):
        self._result = value
        self._done.set()

    def set_error(self, exc):
        self._error = exc
        self._done.set()

    def result(self, timeout=None):
        if not self._done.wait(timeout):
            raise TimeoutError("browser op timeout")
        if self._error is not None:
            raise self._error
        return self._result


_worker = _BrowserWorker()


def worker():
    return _worker

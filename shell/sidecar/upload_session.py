"""Upload session bridge — Playwright sync API tren MOT thread chuyen biet.

Mirror ui_qt/workers.py:UploadWorker — engine (NamDinhUploaderSession) bat
buoc sync Playwright tren mot thread duy nhat. Sidecar giu mot worker thread
`g1-upload-browser` nhan operation qua queue; command handler submit op va
doi Future.

Engine root vs data root (MIN-69 T2): `import_engine_module` chi de IMPORT
code that tu engine root. Session co the gan vao vung du lieu theo website:
`call(op, ..., website_id="nam_dinh")` → working_dir =
`website_data_dir(website_id)` (duoi G1_UPLOAD_DATA_DIR). `website_id=None`
giu legacy path nguyen trang (working_dir = engine root, contract §9.2).

Mot thoi diem worker giu toi da mot session; session da bind website A ma
nhan op cua website B → `website_mismatch` (caller dong session A truoc).
`browser_id` la ma tham chieu KHONG bi mat phat ra khi session mo — khong
mang quyen portal.

waiting_user: session_start dat job vao waiting_user('login') va doi event
`confirm_login` (command upload.confirm_login) hoac cancel. Khong bao gio
tu finalize — prepare chi mo tab da dien (dry-run), nguoi dung save trong
Chromium (spec MIN-69).
"""
import queue
import threading
import uuid

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
        # Scope cua session hien tai: None = chua mo / legacy (engine root).
        self._website_id = None
        self.browser_id = None

    def _ensure_thread(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._loop, name="g1-upload-browser", daemon=True)
            self._thread.start()

    def call(self, op, *args, website_id=None, **kwargs):
        """Chay fn session tren browser thread, tra ket qua/raise loi.

        `website_id`: None → session legacy (working_dir = engine root);
        "<id>" → session scoped vao website data dir cua id do.
        """
        self._ensure_thread()
        fut = _Future()
        self._queue.put((op, args, kwargs, website_id, fut))
        return fut.result()

    @property
    def website_id(self):
        """website ma session hien tai bind; None khi chua mo/legacy."""
        return self._website_id

    def _loop(self):
        while not self._stop.is_set():
            try:
                op, args, kwargs, website_id, fut = self._queue.get(
                    timeout=0.5)
            except queue.Empty:
                continue
            try:
                fut.set_result(
                    self._dispatch(op, args, kwargs, website_id))
            except Exception as exc:  # noqa: BLE001 — boundary
                fut.set_error(exc)
        self._close_session()

    def _dispatch(self, op, args, kwargs, website_id):
        import_engine_module("upload_lab", "playwright_uploader")
        if op == "_close":
            self._close_session()
            return {"closed": True}
        session = self._ensure_session(website_id)
        return getattr(session, op)(*args, **kwargs)

    def _ensure_session(self, website_id=None):
        """Chi goi tren browser thread.

        Session dang mo ma op den voi website khac → website_mismatch —
        khong tu dong browser hay ghi cheo du lieu website khac.
        """
        if self._session is not None and self._website_id != website_id:
            # legacy (None) <-> versioned: contract §9.4 workflow_conflict;
            # hai website khac nhau: contract §3 website_mismatch.
            if self._website_id is None or website_id is None:
                raise CommandError(
                    "workflow_conflict",
                    "luong legacy va versioned khong dung chung browser — "
                    "dong session hien tai truoc")
            raise CommandError(
                "website_mismatch",
                f"browser dang phuc vu website {self._website_id!r}; "
                f"dong session truoc khi dung website {website_id!r}")
        if self._session is None:
            uploader = import_engine_module(
                "upload_lab", "playwright_uploader")
            if website_id:
                # Versioned flow: working_dir = vung du lieu rieng cua
                # website duoi data root — session/staff cache/runs/
                # registry khong dung lai cua website khac hay engine root.
                from upload_workspace import website_data_dir, open_store
                data_dir = website_data_dir(website_id)
                settings = uploader.load_uploader_settings(data_dir)
                self._session = uploader.NamDinhUploaderSession(
                    settings, working_dir=data_dir)
                self._website_id = website_id
                self.browser_id = "brw_" + uuid.uuid4().hex[:8]
                try:
                    open_store().open_browser(website_id, self.browser_id)
                except Exception:
                    pass  # store loi khong chan session — browser van dung
            else:
                # Legacy path nguyen trang (contract §9.2).
                root = engine_root("upload_lab")
                self._session = uploader.NamDinhUploaderSession(
                    uploader.load_uploader_settings(root),
                    working_dir=root)
        return self._session

    def _close_session(self):
        browser_id = self.browser_id
        website_id = self._website_id
        if self._session is not None:
            try:
                self._session.close()
            finally:
                self._session = None
        if browser_id:
            try:
                from upload_workspace import open_store
                open_store().close_browser(browser_id)
            except Exception:
                pass
        self._website_id = None
        self.browser_id = None
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

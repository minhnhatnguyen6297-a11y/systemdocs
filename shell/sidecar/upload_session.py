"""Upload session bridge — Playwright sync API tren MOT thread chuyen biet.

Mirror ui_qt/workers.py:UploadWorker — engine (NamDinhUploaderSession) bat
buoc sync Playwright tren mot thread duy nhat. Sidecar giu mot worker thread
`g1-upload-browser` nhan operation qua queue; command handler submit op va
doi Future.

Engine root vs data root (MIN-69 T2): `import_engine_module` chi de IMPORT
code that tu engine root. Session versioned gan vao vung du lieu theo website:
`call(op, ..., website_id="nam_dinh")` → browser do provider tao voi
`working_dir = website_data_dir(website_id)` (duoi G1_UPLOAD_DATA_DIR).
`website_id=None` giu legacy path nguyen trang (working_dir = engine root,
contract §9.2).

Mot thoi diem worker giu toi da mot session; session da bind website A ma
nhan op cua website B → `website_mismatch` (caller dong session A truoc).
`browser_id` la ma tham chieu KHONG bi mat phat ra khi session mo — khong
mang quyen portal.

waiting_user (MIN-69 T4): thay event global bang wait-state THEO JOB —
`register_wait` gan job_id → (waiting_on, website_id, browser_id, event);
`upload.confirm_login`/`upload.finish_review` chi giai phong job dang cho
dung buoc + dung scope (`wrong_job` cho moi truong hop khac — xac nhan cho
job A khong bao gio danh thuc job B).

Mot tac vu browser "mutating" (open/prepare/download/staff fetch) chiem op
slot — tac vu mutating khac den trong luc do bi tu choi `browser_busy` thay
vi xep hang. Op quan sat (poll) van xep hang thuong — thread don da serialize
san. Phan idle cua loop poll login + prepared pages (dung Qt worker lam mau)
va cap nhat snapshot/store; `session_status` chi doc snapshot, khong bao gio
spawn browser hay enqueue op.

Browser chet/mat ket noi (poll nem loi, vi du target closed) → session bi
dong, tab dang mo chuyen sang needs_reconcile (khong bao gio danh 'da luu'),
moi job dang cho tren browser do duoc danh thuc va that bai
`engine_unavailable`.
"""
import queue
import threading
import uuid
from datetime import datetime, timezone

from errors import CommandError
from engine_roots import engine_root, import_engine_module

LOGIN_WAIT_TIMEOUT_S = 15 * 60
REVIEW_WAIT_TIMEOUT_S = 60 * 60

_LOGIN_STATUS_MAP = {
    "authenticated": "authenticated",
    "waiting": "awaiting_login",
    "idle": "unknown",
    "closed": "closed",
    "timeout": "awaiting_login",
    "navigation_error": "unknown",
}

# Engine tra "authenticated" MOT LAN duy nhat (poll_manual_login dat
# login_page=None khi nhan dien xong → cac poll sau chi tra "idle").
# Snapshot latch trang thai do cho live session: idle/navigation_error/
# timeout sau mot lan authenticated KHONG duoc ha status xuong. Chi reset
# khi _close_session/_session_lost/open_manual_login moi.
_LATCH_SUPPRESS = frozenset({"idle", "navigation_error", "timeout"})


def _engine_auth_expired(exc) -> bool:
    """Engine bao phien dang nhap het han (RuntimeError 'Session da het
    han' o prepare/download/staff) → can dang nhap lai, khong phai loi
    engine thuong."""
    msg = str(exc).lower()
    return "het han" in msg or "hết hạn" in msg


def _now_z() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z")


def _new_snapshot() -> dict:
    return {
        "login": {"status": "unknown", "checked_at": None},
        "tabs": {
            "open_record_ids": [],
            "saved_record_ids": [],
            "closed_record_ids": [],
            "unknown_record_ids": [],
        },
    }


class _WaitRec:
    __slots__ = ("event", "waiting_on", "website_id", "browser_id")

    def __init__(self, waiting_on, website_id, browser_id):
        self.event = threading.Event()
        self.waiting_on = waiting_on
        self.website_id = website_id
        self.browser_id = browser_id


class _BrowserWorker:
    """Mot thread so huu session browser — nhan (op, args) → Future.

    `mutating=True` tren `call` chiem op slot suot thoi gian op chay: mot op
    mutating khac den sau → `browser_busy` ngay (contract §8) thay vi xep
    hang sau mot batch dai. Op quan sat khong chiem slot.
    """

    def __init__(self):
        self._queue = queue.Queue()
        self._thread = None
        self._session = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        # Wait-state THEO JOB (thay event global T3): job_id → _WaitRec.
        self._waits = {}
        # Op slot: toi da mot tac vu mutating tren browser tai mot thoi diem.
        self._op_slot = threading.Lock()
        # Stop event cua op mutating dang chay (prepare) — session_close/
        # request_stop dat no de engine dung sau don vi dang xu ly.
        self._active_stop = None
        # Snapshot moi nhat do browser thread cap nhat — doc boi
        # session_status ma khong enqueue op.
        self._snapshot = _new_snapshot()
        # record_id → run_id cho tab dang mo (bo nho; needs_reconcile lo
        # truong hop restart).
        self._tab_runs = {}
        # Khoang idle giua hai poll (test dat 0.05; production 0.5 nhu Qt).
        self._poll_interval = 0.5
        # Scope cua session hien tai: None = chua mo / legacy (engine root).
        self._website_id = None
        self.browser_id = None
        # Latch authenticated (chi browser thread ghi): engine tra one-shot
        # "authenticated" roi "idle" — snapshot phai giu authenticated.
        self._login_latched = False
        # Future cua op dang dispatch — loop exit phai fail no + moi op con
        # xep hang, khong de caller treo vo han (thread chet giua op).
        self._inflight = None

    # ------------------------------------------------------------ thread
    def _ensure_thread(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._loop, name="g1-upload-browser", daemon=True)
            self._thread.start()

    def shutdown(self):
        """Dung browser thread + dong session (test teardown / drain)."""
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=5)

    def call(self, op, *args, website_id=None, mutating=False,
             stop_event=None, stop_current=False, **kwargs):
        """Chay fn session tren browser thread, tra ket qua/raise loi.

        `website_id`: None → session legacy (working_dir = engine root);
        "<id>" → session scoped vao website data dir cua id do.
        `mutating`: op thay doi browser → chiem op slot; slot ban →
        `browser_busy` (retryable). `stop_event`: stop event cua chinh op
        nay — duoc dang ky de `request_stop()`/`_close` dat tu ben ngoai.
        `stop_current`: dat stop event cua op dang chay TRUOC khi xep hang
        (dung cho `_close` — engine dung som thay vi het batch).
        """
        if stop_current:
            self.request_stop()
        acquired = False
        if mutating:
            acquired = self._op_slot.acquire(blocking=False)
            if not acquired:
                raise CommandError(
                    "browser_busy",
                    "browser dang phuc vu thao tac khac — thu lai sau",
                    retryable=True, next_action="retry")
        try:
            self._ensure_thread()
            if stop_event is not None:
                self._register_active_stop(stop_event)
            fut = _Future()
            try:
                self._queue.put((op, args, kwargs, website_id, fut))
                return fut.result()
            finally:
                if stop_event is not None:
                    self._register_active_stop(None)
        finally:
            if acquired:
                self._op_slot.release()

    @property
    def website_id(self):
        """website ma session hien tai bind; None khi chua mo/legacy."""
        return self._website_id

    # ------------------------------------------------------------ snapshot
    def snapshot(self):
        """Ban sao trang thai login/tabs moi nhat — doc-only, khong spawn
        thread, khong cham Playwright."""
        with self._lock:
            return {
                "login": dict(self._snapshot["login"]),
                "tabs": {key: list(value)
                         for key, value in self._snapshot["tabs"].items()},
            }

    def browser_alive(self) -> bool:
        """Session engine con song (doc-only — khong spawn thread)."""
        with self._lock:
            return self._session is not None

    def note_open_tabs(self, run_id, record_ids):
        """Ghi run_id cua cac tab vua mo (browser thread doc khi poll)."""
        with self._lock:
            for rid in record_ids:
                self._tab_runs[int(rid)] = run_id

    def tab_run_map(self):
        """Ban sao {record_id: run_id} cua tab dang duoc theo doi."""
        with self._lock:
            return dict(self._tab_runs)

    # ------------------------------------------------------------ waits
    def register_wait(self, job_id, *, waiting_on, website_id, browser_id):
        """Job dang ky cho — tra Event duoc set khi confirm dung scope."""
        rec = _WaitRec(waiting_on, website_id, browser_id)
        with self._lock:
            self._waits[job_id] = rec
        return rec.event

    def confirm_wait(self, job_id, *, waiting_on, website_id,
                     browser_id) -> bool:
        """Giai phong wait cua `job_id` khi dung buoc + dung scope.

        False cho moi truong hop khac — confirm cho job A khong bao gio
        danh thuc job B (`wrong_job` phia command)."""
        with self._lock:
            rec = self._waits.get(job_id)
            if rec is None:
                return False
            if rec.waiting_on != waiting_on \
                    or rec.website_id != website_id \
                    or rec.browser_id != browser_id:
                return False
            rec.event.set()
            return True

    def unregister_wait(self, job_id):
        with self._lock:
            self._waits.pop(job_id, None)

    def release_any_wait(self, waiting_on):
        """Legacy global-confirm: danh thuc moi wait LEGACY dang
        `waiting_on` nay.

        Chi giai phong wait khong scope (website_id=None va browser_id=None
        — duong legacy). Wait versioned co scope day du: confirm legacy
        khong bao gio danh thuc job versioned — di qua `confirm_wait` co
        kiem scope tung job + wrong_job phia command."""
        with self._lock:
            recs = [rec for rec in self._waits.values()
                    if rec.waiting_on == waiting_on
                    and rec.website_id is None
                    and rec.browser_id is None]
        for rec in recs:
            rec.event.set()

    def _release_waits_for_browser(self, browser_id):
        """Browser dong/mat → danh thuc moi job dang cho tren browser do;
        job tu kiem `browser_alive()` va that bai `engine_unavailable`.
        Session legacy (browser_id=None) giai phong wait co browser_id=None."""
        with self._lock:
            recs = [rec for rec in self._waits.values()
                    if rec.browser_id == browser_id]
        for rec in recs:
            rec.event.set()

    # ------------------------------------------------------------ loop
    def _loop(self):
        try:
            while not self._stop.is_set():
                try:
                    op, args, kwargs, website_id, fut = self._queue.get(
                        timeout=self._poll_interval)
                except queue.Empty:
                    self._poll_browser()
                    continue
                with self._lock:
                    self._inflight = fut
                try:
                    fut.set_result(
                        self._dispatch(op, args, kwargs, website_id))
                except Exception as exc:  # noqa: BLE001 — boundary
                    fut.set_error(exc)
                finally:
                    with self._lock:
                        self._inflight = None
                # Sau moi op poll lai trang thai — engine op thuong thay
                # doi login/tab (mau ui_qt/workers.py:_browser_loop).
                self._poll_browser()
        finally:
            try:
                self._close_session()
            finally:
                # Thread dung (shutdown/crash): moi Future chua resolve —
                # dang dispatch hoac con xep hang — phai that bai ro rang
                # thay vi de caller cho vo han.
                self._fail_pending()

    def _fail_pending(self):
        """Fail moi op dang dispatch/xep hang khi browser thread thoat."""
        with self._lock:
            inflight = self._inflight
            self._inflight = None
        exc = CommandError(
            "engine_unavailable",
            "browser thread da dung giua chung — thu lai",
            retryable=True, next_action="retry")
        if inflight is not None:
            inflight.set_error(exc)
        while True:
            try:
                _op, _a, _k, _w, queued = self._queue.get_nowait()
            except queue.Empty:
                return
            try:
                queued.set_error(exc)
            except Exception:
                pass

    def _dispatch(self, op, args, kwargs, website_id):
        import_engine_module("upload_lab", "playwright_uploader")
        if op in ("_poll_now", "_close", "_poll_then_close"):
            # Op noi bo van kiem scope — khong cho command cua website
            # khac poll/dong nham session dang phuc vu (loai tru legacy
            # None↔None). _poll_then_close la MOT op: poll reconcile roi
            # dong ngay tren cung luot dispatch — khong op nao xen giua.
            if self._session is not None \
                    and self._website_id != website_id:
                if self._website_id is None or website_id is None:
                    raise CommandError(
                        "workflow_conflict",
                        "luong legacy va versioned khong dung chung "
                        "browser")
                raise CommandError(
                    "website_mismatch",
                    f"browser dang phuc vu website {self._website_id!r}")
            if op == "_poll_now":
                # Reconcile dong bo: chay _poll_browser ngay trong dispatch
                # de snapshot/store moi nhat khi call() tra ve
                # (finish_review doc saved ngay sau do — khong dua vao
                # nhip idle poll).
                self._poll_browser()
                return {"polled": True}
            if op == "_poll_then_close":
                self._poll_browser()
            self._close_session()
            return {"closed": True}
        session = self._ensure_session(website_id)
        if op == "open_manual_login":
            # Login flow moi: one-shot authenticated cu het gia tri —
            # latch phai reset de idle sau do khong bao authenticated gia.
            self._login_latched = False
            with self._lock:
                self._snapshot["login"] = {
                    "status": "unknown", "checked_at": _now_z()}
        try:
            return getattr(session, op)(*args, **kwargs)
        except RuntimeError as exc:
            if _engine_auth_expired(exc):
                # Session portal het han: latch authenticated khong con
                # dung — snapshot phai bao can dang nhap lai (UI dua
                # login_required thay vi retry mu).
                self._expire_login()
            raise

    def _expire_login(self):
        """Bo latch khi engine bao session het han (chi browser thread)."""
        self._login_latched = False
        with self._lock:
            self._snapshot["login"] = {
                "status": "unknown", "checked_at": _now_z()}

    # ------------------------------------------------------------ polling
    def _poll_browser(self):
        """Chi chay tren browser thread. Poll login + prepared pages roi
        cap nhat snapshot + store (mau _poll_browser_in_browser_thread)."""
        session = self._session
        if session is None:
            return
        try:
            login_result = session.poll_manual_login()
            pages = session.poll_prepared_pages()
        except Exception:
            # Poll nem loi = browser/target mat — dong session, danh dau
            # tab con mo la can doi chieu va danh thuc cac job dang cho.
            try:
                self._session_lost()
            except Exception:
                pass
            return
        try:
            self._update_snapshot(login_result, pages)
        except Exception:
            pass  # store/snapshot loi khong duoc giet browser loop

    def _update_snapshot(self, login_result, pages):
        """Gop ket qua poll vao snapshot + mirror vao workspace store.

        Luat ghi store (chi browser thread goi):
        - saved (POST /api/hoso 2xx da xac minh boi engine) → bo khoi
          open_tabs + needs_reconcile, bump queue_revision cua run.
        - closed truoc khi Luu → bo khoi open_tabs + needs_reconcile.
        - open trong store nhung engine khong con thay → unknown +
          needs_reconcile (mat dau truoc khi xac dinh).
        """
        status = str((login_result or {}).get("status") or "unknown")
        if status == "authenticated":
            self._login_latched = True
        elif self._login_latched and status in _LATCH_SUPPRESS:
            # One-shot authenticated da bi mot poll truoc tieu thu — giu
            # nguyen authenticated cho live session (engine tra "idle"
            # mai sau do cho toi khi session/login page thay doi).
            status = "authenticated"
        login = {"status": _LOGIN_STATUS_MAP.get(status, "unknown"),
                 "checked_at": _now_z()}
        saved = sorted({int(i) for i in
                        (pages or {}).get("saved_record_ids") or []})
        closed = sorted({int(i) for i in
                         (pages or {}).get("closed_record_ids") or []})
        open_ids = sorted({int(i) for i in
                           (pages or {}).get("open_record_ids") or []})
        wid = self._website_id
        bid = self.browser_id
        unknown = []
        runs_bumped = set()
        if wid:
            try:
                from upload_workspace import open_store
                store = open_store()
                with self._lock:
                    tab_runs = dict(self._tab_runs)
                    for rid in saved + closed:
                        self._tab_runs.pop(rid, None)
                if saved or closed:
                    store.remove_open_tabs(wid, saved + closed)
                if saved:
                    store.clear_needs_reconcile(wid, saved)
                # needs_reconcile giu run_id de upload.reconcile doi chieu
                # theo dung run (contract §6.15).
                for rid in closed:
                    store.add_needs_reconcile(
                        wid, [rid], run_id=tab_runs.get(rid),
                        reason="tab dong truoc khi xac minh Luu")
                tracked = set(store.open_tab_record_ids(wid))
                vanished = sorted(tracked - set(open_ids))
                if vanished:
                    unknown = vanished
                    store.remove_open_tabs(wid, vanished)
                    with self._lock:
                        for rid in vanished:
                            tab_runs[rid] = self._tab_runs.pop(rid, None)
                    for rid in vanished:
                        store.add_needs_reconcile(
                            wid, [rid], run_id=tab_runs.get(rid),
                            reason="mat dau truoc khi xac dinh Luu")
                # Save/close/vanish lam queue cua run doi → bump
                # queue_revision de prepare cu phai doc lai queue.
                for rid in saved + closed + vanished:
                    run_id = tab_runs.get(rid)
                    if run_id and run_id not in runs_bumped:
                        store.bump_queue_revision(run_id)
                        runs_bumped.add(run_id)
            except Exception:
                unknown = []
        with self._lock:
            tabs = self._snapshot["tabs"]
            tabs["open_record_ids"] = open_ids
            for rid in saved:
                if rid not in tabs["saved_record_ids"]:
                    tabs["saved_record_ids"].append(rid)
            for rid in closed:
                if rid not in tabs["closed_record_ids"]:
                    tabs["closed_record_ids"].append(rid)
            for rid in unknown:
                if rid not in tabs["unknown_record_ids"]:
                    tabs["unknown_record_ids"].append(rid)
            tabs["saved_record_ids"].sort()
            tabs["closed_record_ids"].sort()
            tabs["unknown_record_ids"].sort()
            self._snapshot["login"] = login

    def _session_lost(self):
        """Browser khong con doc duoc (crash/target closed).

        Tab dang mo → needs_reconcile (KHONG 'da luu'); browser row dong;
        job dang cho duoc danh thuc de that bai engine_unavailable."""
        wid = self._website_id
        bid = self.browser_id
        if wid:
            try:
                from upload_workspace import open_store
                store = open_store()
                open_ids = store.open_tab_record_ids(wid)
                with self._lock:
                    run_map = dict(self._tab_runs)
                for rid in open_ids:
                    store.add_needs_reconcile(
                        wid, [rid], run_id=run_map.get(rid),
                        reason="browser mat ket noi truoc khi xac dinh")
                if open_ids:
                    store.remove_open_tabs(wid, open_ids)
                with self._lock:
                    tabs = self._snapshot["tabs"]
                    for rid in open_ids:
                        if rid not in tabs["unknown_record_ids"]:
                            tabs["unknown_record_ids"].append(rid)
                    tabs["open_record_ids"] = []
                    self._tab_runs.clear()
            except Exception:
                pass
        with self._lock:
            self._snapshot["login"] = {
                "status": "unknown", "checked_at": _now_z()}
        self._login_latched = False
        try:
            self._close_session()
        except Exception:
            pass
        self._release_waits_for_browser(bid)

    # ------------------------------------------------------------ session
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
                # Versioned flow: provider tao browser voi working_dir =
                # vung du lieu rieng cua website — session/staff cache/runs/
                # registry khong dung lai cua website khac hay engine root.
                from upload_workspace import (
                    get_provider, open_store, website_data_dir)
                data_dir = website_data_dir(website_id)
                provider = get_provider(website_id)
                session = provider.create_browser(data_dir)
                browser_id = "brw_" + uuid.uuid4().hex[:8]
                try:
                    # Ghi so huu browser TRUOC khi session di vao dung —
                    # fail thi dong session, khong cho chay "vo chu".
                    open_store().open_browser(website_id, browser_id)
                except Exception as exc:
                    try:
                        session.close()
                    except Exception:
                        pass
                    raise CommandError(
                        "engine_unavailable",
                        f"khong ghi duoc browser vao workspace store: "
                        f"{exc}") from exc
                self._session = session
                self._website_id = website_id
                self.browser_id = browser_id
                self._login_latched = False
                with self._lock:
                    self._snapshot = _new_snapshot()
                    self._tab_runs.clear()
            else:
                # Legacy path nguyen trang (contract §9.2).
                root = engine_root("upload_lab")
                self._session = uploader.NamDinhUploaderSession(
                    uploader.load_uploader_settings(root),
                    working_dir=root)
                self._login_latched = False
        return self._session

    def request_stop(self):
        """Dat stop event cua op dang chay (an toan goi tu moi thread)."""
        with self._lock:
            stop = self._active_stop
        if stop is not None:
            stop.set()

    def _register_active_stop(self, stop_event):
        with self._lock:
            self._active_stop = stop_event

    def _close_session(self):
        """Dong session + danh dau browser closed trong store.

        finally bao dam: du session.close() raise thi browsers row van
        duoc dong va state reset — khong de browser 'open' treo. Job dang
        cho tren browser nay duoc danh thuc (se thay browser_alive=False).
        """
        browser_id = self.browser_id
        try:
            if self._session is not None:
                try:
                    self._session.close()
                finally:
                    self._session = None
        finally:
            if browser_id:
                try:
                    from upload_workspace import open_store
                    open_store().close_browser(browser_id)
                except Exception:
                    pass
            self._website_id = None
            self.browser_id = None
            self._login_latched = False
            self._register_active_stop(None)
            self._release_waits_for_browser(browser_id)


class _Future:
    def __init__(self):
        self._done = threading.Event()
        self._result = None
        self._error = None

    def set_result(self, value):
        self._result = value
        self._done.set()

    def set_error(self, exc):
        if self._done.is_set():
            return  # da resolve — khong ghi de ket qua thanh loi
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

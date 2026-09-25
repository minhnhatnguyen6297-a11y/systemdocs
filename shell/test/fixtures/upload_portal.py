"""Fake upload portal + browser session for sidecar workflow tests.

Provides three pieces so browser-workflow tests never touch the real portal or
real Chromium:

* ``FakePortal`` — a stdlib ``http.server`` on 127.0.0.1 serving a login page,
  a create-record page with a fake ``Lưu`` button (``POST /api/hoso``), a
  contract-book export endpoint and a staff-options endpoint. A real Playwright
  browser could drive these pages, but tests normally use
  ``PortalBrowserSession``.
* ``PortalBrowserSession`` — a drop-in fake for
  ``NamDinhUploaderSession``. It implements the same public methods, records
  the thread id of every engine call (so tests can prove the one-browser-thread
  invariant), talks to ``FakePortal`` over real loopback HTTP for
  login/save/export/staff paths, and keeps an in-memory prepared-tab map that
  mirrors the engine (Save only counts after a 2xx ``POST /api/hoso``).
* ``FakePortalProvider`` — a ``WebsiteProvider`` whose ``create_browser``
  returns the fake session and whose ``run_scan`` fabricates a real registry +
  manifest + output json files inside the per-website data dir.
"""

from __future__ import annotations

import io
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


# ---------------------------------------------------------------------------
# FakePortal — HTTP fixture server
# ---------------------------------------------------------------------------

_LOGIN_HTML = """<!doctype html><html><head><title>Dang nhap</title></head>
<body>
<h1>Dang nhap</h1>
<form id="login">
<input name="username"/><input name="password"/>
<button type="submit">Dang nhap</button>
</form>
<script>
document.getElementById('login').addEventListener('submit', async (e) => {
  e.preventDefault();
  await fetch('/api/login', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: 'u', password: 'p'})});
  location.href = '/ho-so-cong-chung';
});
</script>
</body></html>"""

_LISTING_HTML = """<!doctype html><html><head><title>Ho so cong chung</title></head>
<body>
<h1>So cong chung</h1>
<button id="export-btn">Xuất Sổ công chứng</button>
<div id="export-dialog" hidden>
<input id="export-from" placeholder="dd/mm/yyyy"/>
<input id="export-to" placeholder="dd/mm/yyyy"/>
<button id="export-confirm">Tải xuống</button>
</div>
<a href="/ho-so-cong-chung/tao-moi-nhanh">Tao moi nhanh</a>
</body></html>"""

_CREATE_HTML = """<!doctype html><html><head><title>Tao ho so</title></head>
<body>
<h1>Tao moi ho so</h1>
<input id="so-cong-chung"/>
<button id="save-btn">Lưu</button>
<script>
document.getElementById('save-btn').addEventListener('click', async () => {
  const res = await fetch('/api/hoso', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({so_cong_chung:
      document.getElementById('so-cong-chung').value})});
  if (res.ok) location.href = '/ho-so-cong-chung';
});
</script>
</body></html>"""


def _json_response(payload: dict, status: int = 200) -> tuple[int, dict, bytes]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return status, {"Content-Type": "application/json; charset=utf-8"}, body


def _html_response(html: str, status: int = 200) -> tuple[int, dict, bytes]:
    return status, {"Content-Type": "text/html; charset=utf-8"}, html.encode("utf-8")


def build_export_xlsx(rows: list[tuple[str, str]]) -> bytes:
    """Build a minimal .xlsx (col A contract_no, col B date) for export."""
    try:
        from openpyxl import Workbook
    except ImportError as exc:  # pragma: no cover - tests require openpyxl
        raise RuntimeError("openpyxl required for fake portal export") from exc
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class FakePortal:
    """In-process fake upload portal served on 127.0.0.1:<random port>."""

    def __init__(self, *, staff_ccv=None, staff_tk=None):
        self._lock = threading.Lock()
        self.authenticated = False
        self.fail_next_export = False
        self.saved_contract_nos: list[str] = []
        self.export_requests: list[tuple[str, str]] = []
        self.login_attempts = 0
        self.request_log: list[tuple[str, str]] = []
        self.staff = {
            "cong_chung_vien": list(staff_ccv or ["Nguyen Van A", "Tran Thi B"]),
            "thu_ky": list(staff_tk or ["Le Van C"]),
        }
        self.export_rows: list[tuple[str, str]] = [
            ("Số công chứng", "Ngày công chứng"),
            ("999/2099/FIXTURE", "01/01/2099"),
        ]
        # Live test control — set via ``POST /__fixture__/control`` so an
        # out-of-process E2E driver can steer the fake portal/session:
        #   fail_record_ids: list[int]  — record ids that raise in prepare
        #   record_delay_s: float       — per-record delay in prepare
        #   fail_next_export: bool      — next /api/export returns 500
        #   block/release: [name,...]   — gate names: "scan","prepare","open"
        # Gates live here (not on the session) so a control call mid-run can
        # block or release the CURRENT session, and ``scan`` works before any
        # browser exists.
        self.control: dict = {}
        self.provider = None  # wired by register_fake_portal_website

        portal = self

        class _Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # keep test output quiet
                return

            def _handle(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                status, headers, payload = portal.handle(
                    self.command, self.path, body
                )
                self.send_response(status)
                for key, value in headers.items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = _handle
            do_POST = _handle

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True, name="fake-portal"
        )
        self._thread.start()

    # -- URLs ---------------------------------------------------------------
    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def login_url(self) -> str:
        return f"{self.base_url}/dang-nhap"

    @property
    def listing_url(self) -> str:
        return f"{self.base_url}/ho-so-cong-chung"

    @property
    def create_url(self) -> str:
        return f"{self.base_url}/ho-so-cong-chung/tao-moi-nhanh"

    @property
    def save_url(self) -> str:
        return f"{self.base_url}/api/hoso"

    def export_url(self, from_date: str, to_date: str) -> str:
        return f"{self.base_url}/api/export?from={from_date}&to={to_date}"

    @property
    def staff_url(self) -> str:
        return f"{self.base_url}/api/staff"

    # -- test helpers ---------------------------------------------------------
    def user_login(self) -> None:
        with self._lock:
            self.authenticated = True

    def expire(self) -> None:
        with self._lock:
            self.authenticated = False

    def is_authenticated(self) -> bool:
        with self._lock:
            return self.authenticated

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    # -- routing --------------------------------------------------------------
    def handle(
        self, method: str, path: str, body: bytes
    ) -> tuple[int, dict, bytes]:
        route = path.split("?", 1)[0]
        with self._lock:
            self.request_log.append((method, route))
            authed = self.authenticated

        if route == "/dang-nhap" and method == "GET":
            return _html_response(_LOGIN_HTML)
        if route == "/api/login" and method == "POST":
            with self._lock:
                self.login_attempts += 1
                self.authenticated = True
            return _json_response({"ok": True, "access_token": "fixture-token"})
        if route in ("/", "/ho-so-cong-chung") and method == "GET":
            if not authed:
                return _html_response(_LOGIN_HTML)
            return _html_response(_LISTING_HTML)
        if route == "/ho-so-cong-chung/tao-moi-nhanh" and method == "GET":
            if not authed:
                return _html_response(_LOGIN_HTML)
            return _html_response(_CREATE_HTML)
        if route == "/api/hoso" and method == "POST":
            if not authed:
                return _json_response({"ok": False, "error": "unauthenticated"}, 401)
            try:
                payload = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                payload = {}
            contract_no = str(payload.get("so_cong_chung") or payload.get("contract_no") or "")
            with self._lock:
                self.saved_contract_nos.append(contract_no)
            return _json_response({"ok": True, "id": len(self.saved_contract_nos)})
        if route == "/api/export" and method == "GET":
            if not authed:
                return _json_response({"ok": False, "error": "unauthenticated"}, 401)
            query = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
            from_date = (query.get("from") or [""])[0]
            to_date = (query.get("to") or [""])[0]
            with self._lock:
                self.export_requests.append((from_date, to_date))
                fail = self.fail_next_export or bool(
                    self.control.get("fail_next_export"))
                self.fail_next_export = False
                self.control["fail_next_export"] = False
                saved = list(self.saved_contract_nos)
            if fail:
                return _json_response({"ok": False, "error": "interrupted"}, 500)
            # So da Lưu tren portal hien trong export moi nhat — giong so
            # that, de audit/reconcile doi chieu duoc sau Save.
            existing = {r[0] for r in self.export_rows}
            rows = list(self.export_rows) + [
                (cn, datetime.now().strftime("%d/%m/%Y"))
                for cn in saved if cn not in existing]
            data = build_export_xlsx(rows)
            return 200, {
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "Content-Disposition": 'attachment; filename="so_cong_chung.xlsx"',
            }, data
        # -- E2E control channel (khong phai API portal that) ---------------
        if route == "/__fixture__/control" and method == "POST":
            try:
                ctl = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                ctl = {}
            with self._lock:
                for key in ("fail_record_ids", "record_delay_s",
                            "fail_next_export"):
                    if key in ctl:
                        self.control[key] = ctl[key]
                for name in ctl.get("block") or []:
                    ev = self.control.get(f"{name}_gate")
                    if ev is None:
                        ev = threading.Event()
                        self.control[f"{name}_gate"] = ev
                    ev.clear()
                for name in ctl.get("release") or []:
                    ev = self.control.get(f"{name}_gate")
                    if ev is not None:
                        ev.set()
            return _json_response({"ok": True})
        if route == "/__fixture__/user" and method == "POST":
            # Mo phong nguoi dung bam trong Chromium: khong ghi thread_log.
            try:
                req = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                req = {}
            action = str(req.get("action") or "")
            rid = req.get("record_id")
            try:
                if action == "login":
                    self.user_login()
                elif action == "logout":
                    self.expire()
                elif action in ("save", "close_tab"):
                    sess = self.provider and self.provider.last_session
                    if sess is None:
                        return _json_response(
                            {"ok": False, "error": "no_session"}, 409)
                    if action == "save":
                        sess.user_save(int(rid))
                    else:
                        sess.user_close_tab(int(rid))
                elif action == "close_browser":
                    sess = self.provider and self.provider.last_session
                    if sess is not None:
                        sess.user_close_browser()
                else:
                    return _json_response(
                        {"ok": False, "error": f"unknown action {action}"},
                        400)
            except Exception as exc:
                return _json_response(
                    {"ok": False, "error": str(exc)}, 409)
            return _json_response({"ok": True})
        if route == "/__fixture__/state" and method == "GET":
            with self._lock:
                saved = list(self.saved_contract_nos)
                exports = list(self.export_requests)
            sess = self.provider and self.provider.last_session
            tabs = {}
            open_ids: list[int] = []
            if sess is not None:
                with sess._state:
                    tabs = {
                        str(rid): {
                            "closed": t["closed"],
                            "save_evidence": t["save_evidence"],
                            "contract_no": t["contract_no"],
                        }
                        for rid, t in sess.tabs.items()
                    }
                    open_ids = sorted(sess._prepared_record_ids)
            kwargs = dict(sess.last_prepare_kwargs or {}) if sess else {}
            if isinstance(kwargs.get("selected_record_ids"), set):
                kwargs["selected_record_ids"] = sorted(
                    kwargs["selected_record_ids"])
            if isinstance(kwargs.get("exclude_contract_nos"), set):
                kwargs["exclude_contract_nos"] = sorted(
                    kwargs["exclude_contract_nos"])
            return _json_response({
                "ok": True,
                "authenticated": self.is_authenticated(),
                "saved_contract_nos": saved,
                "export_requests": exports,
                "session": {
                    "exists": sess is not None,
                    "closed": bool(sess and sess.closed),
                    "login_page_open": bool(sess and sess.login_page_open),
                    "prepare_calls": int(sess.prepare_calls if sess else 0),
                    "open_record_ids": open_ids,
                    "tabs": tabs,
                    "last_prepare_kwargs": kwargs,
                    "calls": list(sess.calls) if sess else [],
                },
            })
        if route == "/api/staff" and method == "GET":
            if not authed:
                return _json_response({"ok": False, "error": "unauthenticated"}, 401)
            with self._lock:
                staff = dict(self.staff)
            return _json_response(staff)
        return _json_response({"ok": False, "error": "not_found"}, 404)


# ---------------------------------------------------------------------------
# PortalBrowserSession — fake engine session
# ---------------------------------------------------------------------------


class PortalBrowserSession:
    """Fake for ``NamDinhUploaderSession`` driving ``FakePortal``.

    Every engine-facing method records ``(method_name, thread_ident)`` in
    ``thread_log`` so tests can assert every Playwright-equivalent call ran on
    the single browser thread. ``user_*`` helpers simulate the human clicking
    inside Chromium — they do NOT record a thread entry.
    """

    def __init__(self, portal: FakePortal, working_dir):
        self.portal = portal
        self.working_dir = Path(working_dir)
        self._state = threading.Lock()
        self.thread_log: list[tuple[str, int]] = []
        self.calls: list[str] = []
        self.focus_events: list[str] = []

        self.login_page_open = False
        self.login_page_closed = False
        self.authed_seen = False
        self.crashed = False
        self.closed = False

        # prepared tabs: record_id -> {closed, save_evidence, contract_no}
        self.tabs: dict[int, dict] = {}
        self._prepared_record_ids: set[int] = set()

        # test controls
        self.fail_record_ids: set[int] = set()
        self.record_delay_s = 0.0
        self.open_gate: threading.Event | None = None
        self.prepare_gate: threading.Event | None = None
        self.last_prepare_kwargs: dict | None = None
        self.last_download_dates: tuple[str, str] | None = None
        self.last_poll_strict: bool | None = None
        self.prepare_calls = 0

    # -- helpers ---------------------------------------------------------------
    def _mark(self, name: str) -> None:
        self.calls.append(name)
        self.thread_log.append((name, threading.get_ident()))
        with self._state:
            if self.crashed:
                raise RuntimeError("Target closed (fake browser crash)")

    def _http_get(self, url: str) -> bytes:
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"portal HTTP {exc.code} for {url}") from exc

    def _http_post_json(self, url: str, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"portal HTTP {exc.code} for {url}") from exc

    # -- engine-facing API ------------------------------------------------------
    def _ctl(self) -> dict:
        """Live control dict on the portal — settable mid-run via the
        ``/__fixture__/control`` endpoint (works even for a session that was
        already created, unlike the armed next_session_* gates)."""
        return getattr(self.portal, "control", {}) or {}

    def open_manual_login(self) -> dict:
        self._mark("open_manual_login")
        gate = self._ctl().get("open_gate") or self.open_gate
        if gate is not None:
            gate.wait(timeout=30)
        with self._state:
            self.login_page_open = True
            self.login_page_closed = False
        return {"status": "waiting", "url": self.portal.login_url}

    def poll_manual_login(self, force: bool = False) -> dict:
        self._mark("poll_manual_login")
        with self._state:
            if self.closed or self.login_page_closed:
                return {"status": "closed"}
            if not self.login_page_open:
                # Real engine: login_page=None sau khi nhan dien → one-shot
                # "authenticated" da bi tieu thu, cac poll sau tra "idle"
                # mai (KHONG lap lai authenticated nhu ban cu).
                return {"status": "idle"}
        if self.portal.is_authenticated():
            with self._state:
                self.login_page_open = False
                self.authed_seen = True
            return {"status": "authenticated"}
        return {"status": "waiting", "url": self.portal.login_url}

    def ensure_authenticated(self, stop_event=None) -> None:
        self._mark("ensure_authenticated")
        if not self.portal.is_authenticated():
            raise RuntimeError("Session da het han — can dang nhap lai (fake portal)")

    def fetch_staff_options(self) -> dict:
        self._mark("fetch_staff_options")
        self.ensure_authenticated()
        data = self._http_get(self.portal.staff_url)
        options = json.loads(data.decode("utf-8") or "{}")
        cache = self.working_dir / "uploader_staff_options.json"
        cache.write_text(json.dumps(options, ensure_ascii=False), encoding="utf-8")
        return {
            "cong_chung_vien": list(options.get("cong_chung_vien") or []),
            "thu_ky": list(options.get("thu_ky") or []),
        }

    def download_contract_book_export(self, from_date: str, to_date: str):
        self._mark("download_contract_book_export")
        self.ensure_authenticated()
        self.last_download_dates = (from_date, to_date)
        data = self._http_get(self.portal.export_url(from_date, to_date))
        downloads = self.working_dir / "downloads"
        downloads.mkdir(parents=True, exist_ok=True)
        path = downloads / f"so_cong_chung_{from_date.replace('/', '')}_{to_date.replace('/', '')}.xlsx"
        path.write_bytes(data)
        return path

    def prepare_manifest(
        self,
        manifest_path,
        stop_event,
        *,
        selected_record_ids=None,
        exclude_contract_nos=None,
        requester_sheet_url: str = "",
        progress_callback=None,
        cong_chung_vien=None,
        thu_ky=None,
        chunk_size=None,
        prime_save_validation: bool = True,
    ) -> dict:
        self._mark("prepare_manifest")
        self.last_prepare_kwargs = {
            "selected_record_ids": set(selected_record_ids) if selected_record_ids is not None else None,
            "exclude_contract_nos": set(exclude_contract_nos or []),
            "requester_sheet_url": requester_sheet_url,
            "cong_chung_vien": cong_chung_vien,
            "thu_ky": thu_ky,
            "chunk_size": chunk_size,
            # v1 adapter truyen False: dry-run khong click nut Luu (F1).
            # Fixture ghi lai de test assert kwarg di toi engine seam.
            "prime_save_validation": prime_save_validation,
        }
        self.prepare_calls += 1

        # Engine modules are imported lazily so the fixture works once the
        # sidecar dir (engine_roots) is on sys.path.
        from engine_roots import import_engine_module

        uploader = import_engine_module("upload_lab", "playwright_uploader")
        batch_scan = import_engine_module("upload_lab", "batch_scan")

        def emit(event: dict) -> None:
            if progress_callback is None:
                return
            try:
                progress_callback(dict(event))
            except Exception:
                pass

        self.ensure_authenticated(stop_event)
        gate = self._ctl().get("prepare_gate") or self.prepare_gate
        if gate is not None:
            gate.wait(timeout=30)

        manifest, records, total_pending = uploader.load_upload_queue(
            manifest_path,
            working_dir=self.working_dir,
            selected_record_ids=selected_record_ids,
            cong_chung_vien=cong_chung_vien,
            thu_ky=thu_ky,
            statuses=uploader.QUEUE_STATUSES,
        )
        records = [
            record
            for record in records
            if record.status in uploader.PREPARE_QUEUE_STATUSES
            or (
                record.status in uploader.PREPARED_QUEUE_STATUSES
                and record.record_id not in self._prepared_record_ids
            )
        ]
        excluded_duplicates: list = []
        if exclude_contract_nos:
            records, excluded_duplicates = uploader.split_records_by_existing_contract_nos(
                records, exclude_contract_nos
            )
        filtered_pending = len(records)
        if chunk_size is not None:
            records = records[: int(chunk_size)]

        emit(
            {
                "event": "queue_loaded",
                "run_id": manifest.get("run_id"),
                "total_pending": total_pending,
                "filtered_pending": filtered_pending,
                "chunk_size": len(records),
                "excluded_duplicates": len(excluded_duplicates),
            }
        )
        if not records:
            summary = {
                "run_id": manifest.get("run_id"),
                "prepared_count": 0,
                "total_pending": total_pending,
                "remaining": 0,
                "artifact_dir": "",
                "excluded_duplicates": len(excluded_duplicates),
                "open_record_ids": sorted(self._prepared_record_ids),
                "errors": [],
                "message": "Khong con ho so nao can chuan bi (da xu ly het hoac da co trong Excel).",
            }
            emit({"event": "finished", **summary})
            return summary

        conn = batch_scan.connect_registry(self.working_dir / "registry.sqlite3")
        prepared_count = 0
        errors: list[dict] = []
        stopped = False
        for record in records:
            if stop_event is not None and stop_event.is_set():
                stopped = True
                emit(
                    {
                        "event": "stopped",
                        "run_id": manifest.get("run_id"),
                        "prepared_count": prepared_count,
                        "total_pending": filtered_pending,
                        "remaining": max(filtered_pending - prepared_count, 0),
                    }
                )
                break
            emit(
                {
                    "event": "record_started",
                    "run_id": manifest.get("run_id"),
                    "record_id": record.record_id,
                    "contract_no": record.contract_no,
                    "prepared_count": prepared_count,
                    "total_pending": filtered_pending,
                    "remaining": max(filtered_pending - prepared_count, 0),
                }
            )
            try:
                # Mirror the real engine: the window is kept minimized instead
                # of stealing focus while the dry-run fills the form.
                self.focus_events.append("keep_minimized")
                # Live control co the them fail_record_ids/delay giua chung
                # dot — merge voi hook armed tren session.
                ctl = self._ctl()
                fail_ids = set(self.fail_record_ids) | set(
                    ctl.get("fail_record_ids") or [])
                delay_s = ctl.get("record_delay_s", self.record_delay_s)
                if record.record_id in fail_ids:
                    raise RuntimeError(f"fake portal rejected record {record.record_id}")
                if delay_s:
                    import time as _time

                    _time.sleep(float(delay_s))
                self._prepared_record_ids.add(record.record_id)
                with self._state:
                    self.tabs[record.record_id] = {
                        "closed": False,
                        "save_evidence": False,
                        "contract_no": record.contract_no,
                    }
                batch_scan.update_registry_record_by_id(
                    conn, record.record_id, status="prepared_dry_run"
                )
                prepared_count += 1
                emit(
                    {
                        "event": "record_prepared",
                        "run_id": manifest.get("run_id"),
                        "record_id": record.record_id,
                        "prepared_count": prepared_count,
                        "total_pending": filtered_pending,
                        "remaining": max(filtered_pending - prepared_count, 0),
                    }
                )
            except Exception as exc:
                batch_scan.update_registry_record_by_id(
                    conn,
                    record.record_id,
                    status="upload_failed",
                    last_error=str(exc),
                )
                errors.append(
                    {
                        "record_id": record.record_id,
                        "contract_no": record.contract_no,
                        "error": str(exc),
                    }
                )
                emit(
                    {
                        "event": "record_failed",
                        "run_id": manifest.get("run_id"),
                        "record_id": record.record_id,
                        "contract_no": record.contract_no,
                        "error": str(exc),
                        "prepared_count": prepared_count,
                        "total_pending": filtered_pending,
                        "remaining": max(filtered_pending - prepared_count, 0),
                    }
                )
        conn.close()

        artifact_dir = self.working_dir / "upload_runs" / str(manifest.get("run_id"))
        artifact_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "run_id": manifest.get("run_id"),
            "prepared_count": prepared_count,
            "total_pending": filtered_pending,
            "remaining": max(filtered_pending - prepared_count, 0),
            "artifact_dir": str(artifact_dir),
            "excluded_duplicates": len(excluded_duplicates),
            "open_record_ids": sorted(self._prepared_record_ids),
            "errors": errors,
            "message": (
                "Da dung theo yeu cau."
                if stopped
                else "Da dien thu xong — kiem tra tren Chromium roi bam Luu."
            ),
        }
        (artifact_dir / "upload_manifest.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        emit({"event": "finished", **summary})
        return summary

    def poll_prepared_pages(self, strict_save_evidence: bool = False) -> dict:
        self._mark("poll_prepared_pages")
        # v1 (_poll_browser truyen website_id != None): chi POST 2xx tinh
        # la Luu — fake da strict san (chi save_evidence=POST 2xx moi
        # finalize; 'navigated away' khong co trong model cua fixture).
        self.last_poll_strict = strict_save_evidence
        from engine_roots import import_engine_module

        batch_scan = import_engine_module("upload_lab", "batch_scan")
        saved_ids: list[int] = []
        closed_ids: list[int] = []
        with self._state:
            items = list(self.tabs.items())
        for record_id, tab in items:
            if tab["closed"]:
                with self._state:
                    self.tabs.pop(record_id, None)
                    self._prepared_record_ids.discard(record_id)
                closed_ids.append(record_id)
            elif tab["save_evidence"]:
                conn = batch_scan.connect_registry(self.working_dir / "registry.sqlite3")
                batch_scan.mark_records_uploaded_success(
                    conn, [record_id], reason="Luu tren fake portal (da xac minh POST)"
                )
                conn.close()
                with self._state:
                    self.tabs.pop(record_id, None)
                    self._prepared_record_ids.discard(record_id)
                saved_ids.append(record_id)
        with self._state:
            open_ids = sorted(self._prepared_record_ids)
        return {
            "saved_record_ids": saved_ids,
            "closed_record_ids": closed_ids,
            "open_record_ids": open_ids,
        }

    def open_prepared_record_ids(self) -> set[int]:
        self._mark("open_prepared_record_ids")
        with self._state:
            return set(self._prepared_record_ids)

    def close(self) -> None:
        self._mark("close")
        with self._state:
            self.closed = True
            self.login_page_open = False
            self.tabs.clear()
            self._prepared_record_ids.clear()

    # -- user actions (NOT engine calls; simulate the human in Chromium) --------
    def user_login(self) -> None:
        self.portal.user_login()

    def user_save(self, record_id: int) -> None:
        """Simulate clicking the portal's Save button for a prepared tab."""
        with self._state:
            tab = self.tabs.get(record_id)
        if tab is None:
            raise RuntimeError(f"record {record_id} khong co tab dang mo")
        self._http_post_json(self.portal.save_url, {"so_cong_chung": tab["contract_no"]})
        with self._state:
            tab["save_evidence"] = True

    def user_close_tab(self, record_id: int) -> None:
        with self._state:
            tab = self.tabs.get(record_id)
            if tab is not None:
                tab["closed"] = True

    def user_close_login_page(self) -> None:
        with self._state:
            self.login_page_open = False
            self.login_page_closed = True

    def user_close_browser(self) -> None:
        with self._state:
            self.closed = True
            self.login_page_open = False
            for tab in self.tabs.values():
                tab["closed"] = True

    def crash(self) -> None:
        with self._state:
            self.crashed = True


# ---------------------------------------------------------------------------
# FakePortalProvider — WebsiteProvider driving the fake portal
# ---------------------------------------------------------------------------

_PROVIDER_CLASS = None


def make_fake_provider(portal: FakePortal, *, website_id: str = "fake_portal"):
    """Build (once) a ``WebsiteProvider`` subclass bound to ``portal``.

    The engine's ``providers.registry.WebsiteProvider`` is imported lazily —
    the engine root only lands on ``sys.path`` after the sidecar's
    ``engine_roots`` resolves it, so the class cannot be defined at fixture
    import time.
    """
    global _PROVIDER_CLASS
    from engine_roots import import_engine_module

    registry = import_engine_module("upload_lab", "providers.registry")

    if _PROVIDER_CLASS is None:

        class FakePortalProvider(registry.WebsiteProvider):
            """Provider for a fake website backed by ``FakePortal``."""

            def __init__(self, fake_portal, *, website_id):
                super().__init__(
                    website_id=website_id,
                    label="Cong chung gia lap",
                    display_url=fake_portal.base_url,
                    capabilities=(
                        "login",
                        "download_export",
                        "audit_excel",
                        "scan",
                        "prepare",
                        "staff_options",
                        "reconcile",
                    ),
                )
                self.portal = fake_portal
                self.scan_contract_nos: list[str] = []
                self.last_session: PortalBrowserSession | None = None
                self.chunk_size = 10
                # Test hooks: armed BEFORE create_browser so the fresh session
                # blocks inside open_manual_login/prepare until released.
                self.next_session_open_gate: threading.Event | None = None
                self.next_session_prepare_gate: threading.Event | None = None

            # -- scan / audit ---------------------------------------------------
            def run_scan(
                self,
                folder: Path,
                data_dir: Path,
                *,
                modified_since=None,
                full_rescan: bool = False,
                progress_callback=None,
            ):
                return _fake_run_scan(
                    self, folder, data_dir,
                    progress_callback=progress_callback)

            def audit_excel(self, path, *, from_date, to_date):
                """Delegate to the real contract-book audit service."""
                from engine_roots import import_engine_module as _imp

                audit_module = _imp(
                    "upload_lab", "ui.services.contract_book_audit")
                return audit_module.analyze_contract_book(
                    Path(path), from_date=from_date, to_date=to_date)

            # -- browser ---------------------------------------------------------
            def create_browser(self, data_dir):
                resolved = self.ensure_data_layout(data_dir)
                session = PortalBrowserSession(self.portal, resolved)
                session.open_gate = self.next_session_open_gate
                session.prepare_gate = self.next_session_prepare_gate
                self.next_session_open_gate = None
                self.next_session_prepare_gate = None
                self.last_session = session
                return session

            def connect_registry(self, data_dir):
                from engine_roots import import_engine_module as _imp

                batch_scan = _imp("upload_lab", "batch_scan")
                return batch_scan.connect_registry(
                    self.assert_data_dir(data_dir) / "registry.sqlite3")

            # -- env / prefs -------------------------------------------------------
            def env_check(self, data_dir):
                return {
                    "overall": "passed",
                    "python_version": "fake",
                    "platform": "fake",
                    "playwright_installed": True,
                    "chromium_installed": True,
                    "chromium_version": "fake",
                    "env_file": None,
                    "env_writable": True,
                    "missing": [],
                }

            def public_config(self, data_dir) -> dict:
                return {
                    "website_id": self.website_id,
                    "base_url": self.portal.base_url,
                    "browser_channel": "fake",
                    "max_prepared_tabs": self.chunk_size,
                    "storage_state_exists": False,
                    "env_exists": False,
                }

            def load_staff_options_cache(self, data_dir) -> dict:
                cache = Path(data_dir) / "uploader_staff_options.json"
                if not cache.exists():
                    return {"cong_chung_vien": [], "thu_ky": []}
                try:
                    data = json.loads(
                        cache.read_text(encoding="utf-8") or "{}")
                except (OSError, json.JSONDecodeError):
                    return {"cong_chung_vien": [], "thu_ky": []}
                return {
                    "cong_chung_vien": list(
                        data.get("cong_chung_vien") or []),
                    "thu_ky": list(data.get("thu_ky") or []),
                }

            def save_chunk_size(self, data_dir, chunk_size: int) -> Path:
                self.chunk_size = max(1, min(int(chunk_size), 30))
                marker = self.assert_data_dir(data_dir) / ".env"
                marker.write_text(
                    f"ND_MAX_PREPARED_TABS={self.chunk_size}\n",
                    encoding="utf-8")
                return marker

        _PROVIDER_CLASS = FakePortalProvider

    return _PROVIDER_CLASS(portal, website_id=website_id)


def register_fake_portal_website(
    portal: FakePortal, *, website_id: str = "fake_portal"
):
    """Register the fake provider into the engine ``DEFAULT_REGISTRY``.

    Returns the provider instance. Caller must pop
    ``DEFAULT_REGISTRY._providers[website_id]`` in test teardown so the fake
    never leaks into the production catalog.
    """
    from engine_roots import import_engine_module

    providers = import_engine_module("upload_lab", "providers")
    provider = make_fake_provider(portal, website_id=website_id)
    providers.DEFAULT_REGISTRY.register(provider)
    portal.provider = provider
    return provider


def _fake_run_scan(
    provider,
    folder: Path,
    data_dir: Path,
    *,
    progress_callback=None,
):
    """Fabricate a real registry + manifest + output json for a fake run."""
    from engine_roots import import_engine_module

    # Live scan gate — E2E blocks scan mid-run to assert tab switching
    # preserves progress (``POST /__fixture__/control`` block/release).
    ctl = getattr(getattr(provider, "portal", None), "control", {}) or {}
    gate = ctl.get("scan_gate")
    if gate is not None:
        gate.wait(timeout=60)

    batch_scan = import_engine_module("upload_lab", "batch_scan")

    resolved = provider.ensure_data_layout(data_dir)
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    run_id = f"run_{uuid.uuid4().hex[:10]}"
    conn = batch_scan.connect_registry(resolved / "registry.sqlite3")
    try:
        for index, contract_no in enumerate(
                provider.scan_contract_nos, start=1):
            docx = folder / f"HD-{index:03d}.docx"
            if not docx.exists():
                docx.write_bytes(b"fake docx bytes")
            output_dir = resolved / "output" / f"HD-{index:03d}"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_json = output_dir / "output.json"
            output_json.write_text(
                json.dumps(
                    {
                        "web_form": {
                            "ten_hop_dong": f"Hop dong {contract_no}",
                            "ngay_cong_chung": "15/04/2026",
                            "so_cong_chung": contract_no,
                            "nhom_hop_dong": "Chuyen nhuong quyen su dung dat",
                            "loai_tai_san": "Quyen su dung dat",
                            "tai_san": f"Thua dat so {index}",
                        },
                        "raw": {"file_goc": str(docx)},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            batch_scan.upsert_registry_record(
                conn,
                file_key=f"fake-{run_id}-{index}",
                file_path=docx,
                stat_result=docx.stat(),
                customer_folder="",
                status="extracted",
                run_id=run_id,
                contract_no=contract_no,
                extracted_at=batch_scan.now_iso(),
                output_json_path=str(output_json),
            )
    finally:
        conn.close()
    manifest = {
        "run_id": run_id,
        "folder": str(folder.resolve()),
        "stats": {
            "candidates_found": len(provider.scan_contract_nos),
            "processed_files": len(provider.scan_contract_nos),
            "preexisting_output_reused": 0,
            "extract_failed_files": 0,
            "files_without_contract": 0,
            "skipped_by_modified_since": 0,
        },
    }
    manifest_path = resolved / "runs" / f"{run_id}.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if progress_callback is not None:
        try:
            progress_callback(
                {"event": "finished",
                 "processed_files": len(provider.scan_contract_nos),
                 "total_files": len(provider.scan_contract_nos)})
        except Exception:
            pass
    return manifest, manifest_path

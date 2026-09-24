"""Adapter upload_lab — engine that: batch_scan / contract_book_audit /
environment_check / NamDinhUploaderSession.

Boundary (MIN-69):
  - Dry-run mac dinh: prepare mo tab da dien, KHONG tu save/Finalize —
    nguoi dung bam luu trong Chromium (poll_prepared_pages phat hien).
  - Retry/cancel khong tao upload trung: command_id idempotent o jobstore;
    registry.sqlite3 dedup theo file_identity_key trong engine.
  - Playwright sync API song tren upload_session worker thread.
  - Credential/session state (nd_storage_state.json) khong qua contract.
  - Engine root vs data root (T2): `engine_root("upload_lab")` chi de IMPORT
    code + giu data root legacy; luong `upload.workflow.v1` doc/ghi qua
    `upload_workspace.website_data_dir(website_id)` duoi G1_UPLOAD_DATA_DIR.
"""
import functools
import hashlib
import json
import re
import sqlite3
import threading
import time
from dataclasses import asdict, is_dataclass
from datetime import date as _date, datetime as _datetime
from pathlib import Path

from errors import CommandError, error_object
from engine_roots import engine_root, import_engine_module
from fileref import existing_file, validate_file_ref
from jobstore import CancelledByUser
from upload_session import (
    worker, _engine_auth_expired,
    LOGIN_WAIT_TIMEOUT_S, REVIEW_WAIT_TIMEOUT_S)
import upload_workspace

WORKFLOW_VERSION = "upload.workflow.v1"


def _result(kind, data, warnings=None, source_files=None, evidence=None):
    return {
        "kind": kind, "data": data,
        "evidence": evidence or [],
        "warnings": warnings or [],
        "source_files": source_files or [],
    }


def _ddmmyyyy(value):
    """Contract dung ISO yyyy-mm-dd; engine upload_lab dung dd/mm/yyyy.
    Normalize o boundary adapter — khong doi contract."""
    import datetime as _dt
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return _dt.datetime.strptime(s, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    raise CommandError("validation_error",
                       f"ngay khong hop le (yyyy-mm-dd): {s}")


def _existing_dir(ref):
    p = validate_file_ref(ref)
    if not p.is_dir():
        raise CommandError("file_not_found", f"khong phai thu muc: {p}")
    return p


def _dc(obj):
    """dataclass → dict (nested) cho contract result."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: _dc(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: _dc(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_dc(v) for v in obj]
    if isinstance(obj, (Path,)):
        return str(obj)
    import datetime as _dt
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    return obj


# ---------- scan ----------

def scan_folder(job, payload):
    """run_batch_scan that tren thu muc nguoi dung chon. Output/registry
    ghi vao workspace engine (upload_lab root) — engine so huu."""
    p = payload or {}
    folder = _existing_dir(p.get("folder"))
    root = engine_root("upload_lab")
    batch_scan = import_engine_module("upload_lab", "batch_scan")

    def on_progress(snap):
        total = snap.get("total_files") or 0
        done = snap.get("processed_files") or 0
        label = snap.get("current_file") or snap.get("step") or ""
        job.report_progress(done, total or 1, label)
        job.check_cancel()

    job.report_progress(0, 1, "indexing")
    manifest = batch_scan.run_batch_scan(
        folder,
        full_rescan=bool(p.get("full_rescan")),
        modified_since=p.get("modified_since") or None,
        working_dir=root,
        progress_callback=on_progress)
    job.check_cancel()

    # Doc lai registry theo run de tra danh sach per-file co trang thai.
    conn = batch_scan.connect_registry(root / "registry.sqlite3")
    try:
        rows = batch_scan.fetch_registry_records_for_run(
            conn, manifest["run_id"]) if manifest.get("run_id") else []
    except Exception:
        rows = []
    finally:
        conn.close()
    items = []
    for r in rows:
        rd = dict(r)
        items.append({
            "record_id": rd.get("id"),
            "file_path": rd.get("file_path"),
            "contract_no": rd.get("contract_no"),
            "status": rd.get("status"),
            "reason": rd.get("reason"),
            "last_error": rd.get("last_error"),
        })
    stats = manifest.get("stats") or {}
    return _result(
        "scan_report",
        {"run_id": manifest.get("run_id"), "folder": str(folder),
         "stats": stats, "records": items,
         "manifest_path": str(root / "runs"),
         "prepared_ids": []},
        source_files=[{"path": str(folder), "scope": "machine_local"}])


# ---------- audit excel ----------

def audit_excel(job, payload):
    """analyze_contract_book that. Cot output chuan MIN-77:
    STT | Ngay | So cong chung | Ghi chu (ca missing va issues)."""
    p = payload or {}
    path = p.get("file")
    from fileref import existing_file
    excel = existing_file(path)
    from_date = p.get("from_date")
    to_date = p.get("to_date")
    if not from_date or not to_date:
        raise CommandError("validation_error",
                           "can from_date + to_date (yyyy-mm-dd)")
    svc = import_engine_module(
        "upload_lab", "ui.services.contract_book_audit")
    job.report_progress(0, 1, "doc so excel")
    analysis = svc.analyze_contract_book(
        excel, from_date=_ddmmyyyy(from_date), to_date=_ddmmyyyy(to_date))
    job.check_cancel()

    def _row(stt, d, contract_no, note):
        # Schema MIN-77: STT | Ngay | So cong chung | Ghi chu
        return {"stt": stt, "ngay": d, "so_cong_chung": contract_no,
                "ghi_chu": note}

    missing = [
        _row(i + 1, None, m.contract_no,
             getattr(m, "note", None) or "")
        for i, m in enumerate(analysis.missing_numbers)]

    def _kind(r):
        k = getattr(r, "kind", "")
        return getattr(k, "value", k)

    issues = [
        _row(i + 1,
             getattr(r, "contract_date", None),
             getattr(r, "contract_no", None) or getattr(r, "raw_contract_no", ""),
             f"{_kind(r)}: {getattr(r, 'message', '')}")
        for i, r in enumerate(analysis.issue_rows)]
    summary = getattr(analysis, "summary", None)
    job.report_progress(1, 1, "xong")
    return _result(
        "audit_report",
        {"from_date": str(from_date), "to_date": str(to_date),
         "summary": _dc(summary) if summary else {},
         "missing": _dc(missing), "issues": _dc(issues)},
        source_files=[{"path": str(excel), "scope": "machine_local"}])


# ---------- env check ----------

def env_check(job, payload):
    """run_environment_checks that cua upload_lab (OS/quyen ghi/dia/deps/
    mang/DNS/HTTPS/proxy) — khong phai ban rut gon cua sidecar."""
    svc = import_engine_module(
        "upload_lab", "ui.services.environment_check_service")
    uploader = import_engine_module("upload_lab", "playwright_uploader")
    root = engine_root("upload_lab")
    job.report_progress(0, 1, "kiem tra moi truong")
    settings = uploader.load_uploader_settings(root)
    report = svc.run_environment_checks(root, settings.base_url)
    job.check_cancel()
    data = _dc(report)
    return _result("env_check", data)


def env_check_dispatch(job, payload):
    """Route `upload.env_check`: co workflow_version → luong v1 scoped
    website; khong co → legacy engine-root nguyen trang (contract §9.2)."""
    if isinstance(payload, dict) and "workflow_version" in payload:
        return upload_env_check_v1(job, payload)
    return env_check(job, payload)


def scan_dispatch(job, payload):
    """Route `upload.scan`: co workflow_version → v1 scoped (data_dir cua
    website + binding run→manifest); khong co → legacy engine-root."""
    if isinstance(payload, dict) and "workflow_version" in payload:
        return upload_scan_v1(job, payload)
    return scan_folder(job, payload)


def audit_excel_dispatch(job, payload):
    """Route `upload.audit_excel`: co workflow_version → v1 scoped
    (file_ref + binding audit); khong co → legacy `file` payload."""
    if isinstance(payload, dict) and "workflow_version" in payload:
        return upload_audit_excel_v1(job, payload)
    return audit_excel(job, payload)


# ---------- browser session (upload_lab/playwright_uploader) ----------

def session_status(job, payload):
    try:
        result = worker().call("poll_manual_login")
    except CommandError:
        raise
    except Exception as exc:
        raise CommandError("engine_unavailable",
                           f"chua co phien browser: {exc}") from exc
    return _result("session_state", {"login": result})


def session_start(job, payload):
    """Mo Chromium → trang login that; job vao waiting_user('login') toi
    khi nguoi dung xac nhan (upload.confirm_login) hoac huy."""
    job.report_progress(0, 3, "mo Chromium")
    try:
        worker().call("open_manual_login")
    except CommandError:
        raise
    except Exception as exc:
        raise CommandError(
            "engine_unavailable",
            f"khong mo duoc trinh duyet: {exc}", retryable=True) from exc
    job.report_progress(1, 3, "cho dang nhap")
    ev = worker().register_wait(
        job.job_id, waiting_on="login", website_id=None, browser_id=None)
    job.set_waiting("login")
    deadline = time.time() + LOGIN_WAIT_TIMEOUT_S
    try:
        while not ev.wait(0.3):
            job.check_cancel()
            if not worker().browser_alive():
                raise CommandError(
                    "engine_unavailable",
                    "trinh duyet da dong giua cho dang nhap",
                    retryable=True)
            if time.time() > deadline:
                raise CommandError(
                    "ocr.login_timeout",
                    "het thoi gian cho dang nhap", retryable=True,
                    next_action="upload.session_start lai")
    finally:
        worker().unregister_wait(job.job_id)
    job.check_cancel()
    job.resume()
    job.report_progress(2, 3, "xac nhan dang nhap")
    # Engine tra "authenticated" MOT LAN (one-shot) roi "idle" mai — kiem
    # snapshot da latch thay vi raw poll: idle poll co the da tieu thu
    # one-shot tu truoc. _poll_now buoc mot nhip poll dong bo de snapshot
    # moi nhat ngay tai thoi diem xac nhan.
    worker().call("_poll_now")
    login = dict(worker().snapshot()["login"])
    status = str(login.get("status") or "")
    if status != "authenticated":
        raise CommandError(
            "upload.login_not_confirmed",
            f"trang thai dang nhap: {status or 'khong ro'}", retryable=True,
            next_action="dang nhap tren Chromium roi bam Xac nhan lai")
    options = worker().call("fetch_staff_options")
    job.report_progress(3, 3, "da dang nhap")
    return _result("session_state",
                   {"login": login, "staff_options": _dc(options)})


def confirm_login(job, payload):
    """Nguoi dung xac nhan da dang nhap → giai phong job session_start."""
    worker().release_any_wait("login")
    return _result("session_state", {"login_confirmed": True})


def session_close(job, payload):
    try:
        worker().call("_close")
    except CommandError:
        raise
    except Exception:
        worker().release_any_wait("login")
        worker().release_any_wait("review")
    return _result("session_state", {"closed": True})


def download_export(job, payload):
    """Tai so cong chung Excel tu web tinh qua session that."""
    p = payload or {}
    try:
        path = worker().call(
            "download_contract_book_export",
            from_date=str(p.get("from_date") or ""),
            to_date=str(p.get("to_date") or ""))
    except CommandError:
        raise
    except Exception as exc:
        raise CommandError("engine_unavailable",
                           f"tai export that bai: {exc}", retryable=True) from exc
    return _result(
        "export_download",
        {"file": {"path": str(path), "scope": "machine_local"}},
        source_files=[])


def prepare_upload(job, payload):
    """Mo tab da dien (dry-run — khong save). Nguoi dung kiem tra + bam
    luu trong Chromium; job waiting_user('review') toi khi finish_review
    hoac cancel. Cancel KHONG dong tab da mo — nguoi quyet tren browser."""
    p = payload or {}
    root = engine_root("upload_lab")
    ids = p.get("record_ids")
    if not isinstance(ids, list) or not ids:
        raise CommandError("validation_error", "can record_ids: [int]")
    manifest_path = p.get("manifest_path")
    if manifest_path:
        manifest = validate_file_ref(manifest_path)
        if not manifest.is_file():
            raise CommandError("file_not_found", "manifest khong ton tai")
    else:
        runs = sorted((root / "runs").glob("*.json"))
        if not runs:
            raise CommandError("file_not_found",
                               "chua co run nao — chay upload.scan truoc")
        manifest = runs[-1]
    stop = threading.Event()

    def _watch_cancel():
        job._cancel.wait()
        stop.set()

    threading.Thread(target=_watch_cancel, daemon=True).start()

    def on_progress(ev):
        job.check_cancel()
        job.report_progress(
            int(ev.get("prepared") or 0), int(ev.get("total") or 0),
            str(ev.get("event") or "prepare"))

    summary = worker().call(
        "prepare_manifest", manifest, stop,
        selected_record_ids={int(i) for i in ids},
        exclude_contract_nos=set(p.get("exclude_contract_nos") or []),
        cong_chung_vien=p.get("cong_chung_vien") or None,
        thu_ky=p.get("thu_ky") or None,
        progress_callback=on_progress)
    job.check_cancel()
    ev = worker().register_wait(
        job.job_id, waiting_on="review", website_id=None, browser_id=None)
    job.set_waiting("review")
    deadline = time.time() + REVIEW_WAIT_TIMEOUT_S
    try:
        while not ev.wait(0.5):
            job.check_cancel()
            if not worker().browser_alive():
                raise CommandError(
                    "engine_unavailable",
                    "trinh duyet da dong giua cho kiem tra",
                    retryable=True)
            if time.time() > deadline:
                raise CommandError(
                    "upload.review_timeout",
                    "het thoi gian cho review", retryable=True)
    finally:
        worker().unregister_wait(job.job_id)
    job.check_cancel()
    job.resume()
    pages = worker().call("poll_prepared_pages")
    return _result(
        "upload_prepare",
        {"summary": _dc(summary), "pages": _dc(pages),
         "note": "dry-run — nguoi dung da tu kiem tra/luu trong Chromium"})


def finish_review(job, payload):
    """Nguoi dung xac nhan da kiem tra xong cac tab → job prepare ket thuc."""
    worker().release_any_wait("review")
    return _result("session_state", {"review_finished": True})


# =====================================================================
# upload.workflow.v1 — luong versioned (contract upload-workflow.md).
# Cac handler duoi chi chay khi payload.workflow_version dung literal;
# command khong co version giu nguyen legacy path o tren.
# =====================================================================

_PREFERENCE_KEYS = ("chunk_size", "cong_chung_vien", "thu_ky")


def _require_workflow(payload) -> dict:
    """Gate version: thieu/sai workflow_version → unsupported_workflow_version
    (contract §2 — command chi-co-o-v1 khong duoc chay nhu legacy).

    Payload khong phai dict/null → validation_error (handler goi truc tiep
    khong qua app.py cung khong AttributeError)."""
    if payload is not None and not isinstance(payload, dict):
        raise CommandError("validation_error",
                           "payload phai la object/null")
    p = payload or {}
    version = p.get("workflow_version")
    if version != WORKFLOW_VERSION:
        raise CommandError(
            "unsupported_workflow_version",
            f"can workflow_version={WORKFLOW_VERSION!r}")
    return p


def _require_website(payload) -> str:
    """website_id bat buoc + da dang ky → unknown_website/validation_error."""
    wid = payload.get("website_id")
    if wid is None:
        raise CommandError("validation_error", "thieu website_id")
    return upload_workspace.validate_website_id(wid)


def _optional_website(payload):
    """website_id cho phep null (workspace_get doc selection da luu)."""
    wid = payload.get("website_id")
    if wid is None:
        return None
    return upload_workspace.validate_website_id(wid)


def _require_revision(payload, key="expected_revision") -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CommandError("validation_error",
                           f"{key} phai la int >= 0")
    return value


_V1_NEXT_ACTIONS = frozenset(
    {"login_required", "pick_files", "retry", "contact_admin"})


def _v1_boundary(fn):
    """Guard wire-shape contract §8 o ranh gioi upload.workflow.v1.

    Helper dung chung co the nem CommandError thieu/sai next_action —
    `import_engine_module` (engine_roots) tra `engine_unavailable`
    retryable nhung next_action=None, `engine_not_installed` mang
    next_action la huong dan tieng Viet (ngoai enum §8), `fileref` tra
    `file_scope_not_supported` khong next_action. Cac file do la infra
    chia se voi legacy (wire shape legacy khong doi), nen normalize tai
    boundary v1 thay vi sua chung: moi duong loi thoat ra command v1 deu
    co next_action dung bang §8 — gia tri ngoai enum bi chan, khong lo
    ra wire."""
    @functools.wraps(fn)
    def wrapper(job, payload):
        try:
            return fn(job, payload)
        except CommandError as exc:
            if exc.code in ("engine_not_installed",
                            "engine_version_mismatch"):
                exc.retryable = False
                exc.next_action = "contact_admin"
            elif exc.code == "engine_unavailable":
                exc.retryable = True
                exc.next_action = "retry"
            elif exc.code == "file_scope_not_supported":
                exc.next_action = "pick_files"
            elif exc.next_action is not None \
                    and exc.next_action not in _V1_NEXT_ACTIONS:
                exc.next_action = None
            raise
    return wrapper


@_v1_boundary
def upload_websites(job, payload):
    """`upload.websites` → kind website_catalog (contract §6.1)."""
    _require_workflow(payload)
    store = upload_workspace.open_store()
    return _result("website_catalog", {
        "workflow_version": WORKFLOW_VERSION,
        "websites": upload_workspace.list_websites(),
        "selected_website_id": store.selected_website_id(),
    })


@_v1_boundary
def upload_workspace_get(job, payload):
    """`upload.workspace_get` → kind upload_workspace (§6.2).

    website_id null → doc lua chon da luu; website chua chon lan nao →
    workspace rong (website_id null, revision 0)."""
    _require_workflow(payload)
    wid = _optional_website(payload)
    snap = upload_workspace.workspace_snapshot(wid)
    return _result("upload_workspace", snap)


@_v1_boundary
def upload_website_select(job, payload):
    """`upload.website_select` → kind upload_workspace (§6.2).

    Backend kiem lai dieu kien doi (khong chi UI): website cu con job/
    tab cho kiem tra → workflow_busy; revision lech → stale_revision."""
    _require_workflow(payload)
    wid = _require_website(payload)
    expected = _require_revision(payload, "expected_revision")
    snap = upload_workspace.select_website(wid, expected)
    return _result("upload_workspace", snap)


@_v1_boundary
def upload_preferences(job, payload):
    """`upload.preferences` → kind preferences (§6.13).

    `values` thieu → doc; co → validate + luu theo website. Khong nhan
    URL/token/gia tri tu do: key ngoai schema → validation_error."""
    _require_workflow(payload)
    wid = _require_website(payload)
    values = payload.get("values")
    store = upload_workspace.open_store()
    if values is not None:
        if not isinstance(values, dict):
            raise CommandError("validation_error",
                               "values phai la object")
        unknown = set(values) - set(_PREFERENCE_KEYS)
        if unknown:
            raise CommandError(
                "validation_error",
                f"preferences key khong ho tro: {sorted(unknown)}")
        if "chunk_size" in values:
            cs = values["chunk_size"]
            if not isinstance(cs, int) or isinstance(cs, bool) \
                    or not 1 <= cs <= 30:
                raise CommandError("validation_error",
                                   "chunk_size phai la int 1..30")
        for key in ("cong_chung_vien", "thu_ky"):
            if values.get(key) == "":
                raise CommandError("validation_error",
                                   f"{key}: dung null thay chuoi rong")
            if values.get(key) is not None \
                    and not isinstance(values[key], str):
                raise CommandError("validation_error",
                                   f"{key} phai la string/null")
        # Thu tu ghi: .env (engine-native, de that bai) TRUOC store. Neu
        # store fail sau do → revert .env ve gia tri cu de khong phan ky.
        old_prefs = store.get_preferences(wid)
        if "chunk_size" in values:
            provider = upload_workspace.get_provider(wid)
            data_dir = upload_workspace.website_data_dir(wid)
            provider.save_chunk_size(data_dir, values["chunk_size"])
            try:
                store.save_preferences(wid, values)
            except Exception:
                try:
                    provider.save_chunk_size(
                        data_dir, old_prefs["chunk_size"])
                except Exception:
                    pass  # best-effort revert — loi goc van raise len
                raise
        else:
            store.save_preferences(wid, values)
    prefs = store.get_preferences(wid)
    return _result("preferences", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "chunk_size": prefs["chunk_size"],
        "cong_chung_vien": prefs["cong_chung_vien"],
        "thu_ky": prefs["thu_ky"],
    })


@_v1_boundary
def upload_env_check_v1(job, payload):
    """`upload.env_check` versioned → kind env_check (§6.3).

    Engine run_environment_checks that nhung scoped vao data_dir cua
    website; tra {website_id, status, steps[]} — khong le base_url thu
    cong tu payload (base_url do provider quyet dinh)."""
    _require_workflow(payload)
    wid = _require_website(payload)
    provider = upload_workspace.get_provider(wid)
    data_dir = upload_workspace.website_data_dir(wid)
    job.report_progress(0, 1, "kiem tra moi truong")
    report = provider.env_check(data_dir)
    job.check_cancel()
    steps = report.get("steps") or []
    return _result("env_check", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "status": report.get("overall") or report.get("status") or "blocked",
        "steps": _dc(steps),
    })


# =====================================================================
# upload.workflow.v1 — scan / audit_excel / queue_get (MIN-69 task 3).
#
# Khac biet then chot so voi legacy:
#   - Moi ghi/doc di qua `website_data_dir(website_id)` — KHONG engine root.
#   - manifest_ref la file cua CHINH run vua scan; binding run→manifest luu
#     trong workspace store; khong fallback "file moi nhat" o bat cu dau.
#   - Loi doc registry/Excel/output JSON la LOI (engine_unavailable /
#     file_not_found / stale_revision) — khong bao gio tra danh sach rong
#     gia thanh cong.
#   - queue_get khong cham Playwright/browser: sai binding/run/audit fail
#     truoc moi thao tac engine nang.
# =====================================================================

_SCAN_V1_KEYS = frozenset({
    "workflow_version", "website_id", "folder", "expected_revision",
    "full_rescan", "modified_since"})
_AUDIT_V1_KEYS = frozenset({
    "workflow_version", "website_id", "file_ref", "from_date", "to_date"})
_QUEUE_V1_KEYS = frozenset({
    "workflow_version", "website_id", "run_id", "audit_id"})
# .xls (BIFF) chua co duong doc da kiem chung trong engine → tu choi.
_AUDIT_EXCEL_SUFFIXES = (".xlsx", ".xlsm")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CANON_CONTRACT_NO_RE = re.compile(r"^\d+/\d{4}$")


def _require_payload_keys(payload, allowed):
    """Contract khong nhan key la: key ngoai schema → validation_error."""
    extra = set(payload) - set(allowed)
    if extra:
        raise CommandError("validation_error",
                           f"payload key khong ho tro: {sorted(extra)}")


def _require_iso_date(value, field):
    """Wire format ISO yyyy-mm-dd nghiem ngat — dd/mm/yyyy bi tu choi."""
    if not isinstance(value, str) or not _ISO_DATE_RE.match(value):
        raise CommandError("validation_error",
                           f"{field} phai la ISO yyyy-mm-dd: {value!r}")
    try:
        return _datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise CommandError("validation_error",
                           f"{field} khong phai ngay that: {value!r}") from exc


def _ddmmyyyy_from_iso(value, field):
    """Boundary ISO → engine dd/mm/yyyy (engine audit dung dd/mm/yyyy)."""
    return _require_iso_date(value, field).strftime("%d/%m/%Y")


def _ngay_iso(value):
    """Engine date (date/datetime hoac 'dd/mm/yyyy') → ISO hoac None."""
    if isinstance(value, _datetime):
        return value.date().isoformat()
    if isinstance(value, _date):
        return value.isoformat()
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return _datetime.strptime(text, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def _request_hash(payload) -> str:
    return hashlib.sha256(json.dumps(
        payload or {}, sort_keys=True, default=str
    ).encode("utf-8")).hexdigest()


def _begin_workflow_job(store, job, *, command, website_id, payload,
                        **job_fields):
    """Ghi dong workflow_jobs truoc khi engine chay (plan §3.2): recovery
    toi thieu + job non-terminal chan doi website (workflow_busy)."""
    store.upsert_job(
        job.job_id, command_id=job.command_id,
        request_hash=_request_hash(payload), command=command,
        website_id=website_id, status="running", **job_fields)


def _finish_workflow_job(store, job_id, status, **fields):
    """Terminal status cho dong workflow_jobs — best-effort, khong che loi
    nghiep vu khi store hu."""
    try:
        store.upsert_job(job_id, status=status, **fields)
    except Exception:
        pass


def _engine_error(exc, *, generic):
    """Engine exception → (code, message, retryable, next_action) strings.

    Tra text thay vi giu object exc: traceback cua engine exception giu
    frame dang mo sqlite connection/file handle — neu CommandError giu
    __cause__/__context__ toi no thi handle bi pin mo tren Windows cho
    toi khi cyclic GC chay (exception↔traceback↔frame tao cycle).

    engine_unavailable LUON di kem next_action="retry" theo contract §8 —
    normalize o day de moi duong loi engine ra cung mot wire shape."""
    if isinstance(exc, FileNotFoundError):
        err = ("file_not_found", str(exc), True, "pick_files")
    elif isinstance(exc, PermissionError):
        err = ("file_locked", str(exc), True, "retry")
    elif isinstance(exc, RuntimeError) and _engine_auth_expired(exc):
        # Session portal het han (engine RuntimeError 'Session da het
        # han') → can dang nhap lai: UI phai dua login_required thay vi
        # retry mu (contract §8 upload.login_not_confirmed).
        err = ("upload.login_not_confirmed", str(exc), True,
               "login_required")
    elif isinstance(exc, RuntimeError):
        err = ("engine_unavailable", str(exc), True, None)
    elif isinstance(exc, ValueError):
        err = ("validation_error", str(exc), False, None)
    else:
        code, retryable, next_action, label = generic
        err = (code, f"{label}: {type(exc).__name__}: {exc}",
               retryable, next_action)
    if err[0] == "engine_unavailable" and not err[3]:
        err = (err[0], err[1], True, "retry")
    return err


def _run_engine(fn, *, generic):
    """Chay callable engine; exception → CommandError theo _engine_error.

    CommandError (structured tu tang duoi) va CancelledByUser (nguoi huy)
    di qua nguyen — cancel khong bao gio bi map thanh loi engine. Loi duoc
    raise SAU khi except block ket thuc de context exception engine duoc
    giai phong ngay — khong de lai handle mo tren Windows."""
    err = None
    try:
        return fn()
    except CommandError:
        raise
    except CancelledByUser:
        raise
    except Exception as exc:
        err = _engine_error(exc, generic=generic)
    code, message, retryable, next_action = err
    raise CommandError(code, message,
                       retryable=retryable, next_action=next_action)


def _analyze_excel(provider, excel, from_date, to_date):
    """analyze_contract_book qua provider; exception → contract error.

    from_date/to_date la ISO wire (da validate) — doi sang dd/mm/yyyy
    cho engine o boundary nay."""
    return _run_engine(
        lambda: provider.audit_excel(
            excel,
            from_date=_ddmmyyyy_from_iso(from_date, "from_date"),
            to_date=_ddmmyyyy_from_iso(to_date, "to_date")),
        generic=("validation_error", False, "pick_files",
                 f"khong doc duoc file Excel {excel.name}"))


def _audit_rows(analysis):
    """ContractBookAnalysis → hai bang MIN-77 (stt/ngay/so_cong_chung/ghi_chu)."""
    missing = [
        {"stt": i + 1, "ngay": None,
         "so_cong_chung": str(m.contract_no),
         "ghi_chu": str(getattr(m, "note", "") or "")}
        for i, m in enumerate(analysis.missing_numbers)]

    def _kind(r):
        k = getattr(r, "kind", "")
        return str(getattr(k, "value", k))

    issues = [
        {"stt": i + 1,
         "ngay": _ngay_iso(getattr(r, "contract_date", None)),
         "so_cong_chung": str(
             getattr(r, "contract_no", "")
             or getattr(r, "raw_contract_no", "")),
         "ghi_chu": f"{_kind(r)}: {getattr(r, 'message', '')}"}
        for i, r in enumerate(analysis.issue_rows)]
    return missing, issues


def _canonical_contract_no(value) -> str:
    """Canonical HOA HAI PHIA theo dung engine
    (`scan_classification_service._canonical_contract_no`): normalize roi
    cat so 0 dau — "0101/2026" ≡ "101/2026".

    queue_get danh dau "da co trong Excel" bang canonical nay; prepare/
    reconcile PHAI dung cung mot dang, khong dung
    `normalize_contract_no_for_compare` tho (giu so 0 → lech hai phia →
    upload trung)."""
    mod = import_engine_module(
        "upload_lab", "ui.services.scan_classification_service")
    return mod._canonical_contract_no(value)


def _record_row(rd):
    """Row registry cua run → records[] cua scan_report (§6.10)."""
    return {
        "record_id": int(rd.get("id") or 0),
        "contract_no": str(rd.get("contract_no") or ""),
        "status": str(rd.get("status") or ""),
        "reason": str(rd.get("reason") or ""),
        "last_error": str(rd.get("last_error") or ""),
        "file_path": str(rd.get("file_path") or ""),
    }


def _queue_row(row):
    """FolderScanRow cua engine → folder_rows[] cua upload_queue (§6.11)."""
    ncn = str(row.normalized_contract_no or "").strip()
    return {
        "record_id": int(row.record_id),
        "contract_no": str(row.contract_no or ""),
        "normalized_contract_no": (
            ncn if _CANON_CONTRACT_NO_RE.match(ncn) else None),
        "ngay": _ngay_iso(row.contract_date),
        "ghi_chu": str(row.note or ""),
        "file_path": str(row.source_file or ""),
        "status": str(row.status or ""),
        "selected": bool(row.selected),
        "has_issue": bool(row.has_issue),
        "missing_fields": [str(f) for f in (row.missing_fields or [])],
    }


@_v1_boundary
def upload_scan_v1(job, payload):
    """`upload.scan` versioned → kind scan_report (contract §6.10).

    Goi `provider.run_scan` (= run_folder_scan that) voi working_dir la
    data_dir cua website; manifest cua chinh luot nay duoc gan vao store;
    records doc lai tu registry cua website — loi doc la LOI."""
    p = _require_workflow(payload)
    _require_payload_keys(p, _SCAN_V1_KEYS)
    wid = _require_website(p)
    expected = _require_revision(p, "expected_revision")
    folder = validate_file_ref(p.get("folder"))
    if not folder.is_dir():
        raise CommandError(
            "file_not_found",
            f"khong phai thu muc/khong ton tai: {folder}",
            retryable=True, next_action="pick_files")
    full_rescan = p.get("full_rescan", False)
    if not isinstance(full_rescan, bool):
        raise CommandError("validation_error", "full_rescan phai la bool")
    modified_since = p.get("modified_since")
    if modified_since == "":
        raise CommandError("validation_error",
                           "modified_since: dung null thay chuoi rong")
    if modified_since is not None:
        _require_iso_date(modified_since, "modified_since")

    store = upload_workspace.open_store()
    current = store.revision()
    if expected != current:
        raise CommandError(
            "stale_revision",
            f"expected_revision {expected} != hien tai {current} — "
            "doc lai workspace_get",
            retryable=True, next_action="retry")
    data_dir = upload_workspace.website_data_dir(wid)
    provider = upload_workspace.get_provider(wid)

    _begin_workflow_job(store, job, command="upload.scan",
                        website_id=wid, payload=p)
    try:
        def on_progress(snap):
            total = snap.get("total_files") or 0
            done = snap.get("processed_files") or 0
            label = snap.get("current_file") or snap.get("step") or ""
            job.report_progress(done, total or 1, label)
            # Giong legacy scan_folder: cancel giua chung cat ngay, khong
            # cho engine chay het folder moi thoat.
            job.check_cancel()

        job.report_progress(0, 1, "indexing")
        manifest, manifest_path = _run_engine(
            lambda: provider.run_scan(
                folder, data_dir,
                modified_since=modified_since,
                full_rescan=full_rescan,
                progress_callback=on_progress),
            generic=("engine_unavailable", True, "retry", "scan that bai"))
        job.check_cancel()
        # Binding run→manifest cua chinh luot nay — manifest da duoc
        # finalize boi engine trong working_dir/runs.
        run = upload_workspace.register_run(wid, manifest_path, store=store)
        run_id = run["run_id"]
        batch_scan = import_engine_module("upload_lab", "batch_scan")

        def _read_run_records():
            # sqlite3.connect truc tiep + close trong finally: registry
            # cua run vua scan da ton tai. Khong qua connect_registry cua
            # engine — neu ensure_registry_schema nem loi thi conn mo bi
            # bo lai trong frame (statement-cache tao self-cycle, file
            # bi khoa tren Windows toi khi cyclic GC chay).
            conn = sqlite3.connect(str(data_dir / "registry.sqlite3"))
            try:
                conn.row_factory = sqlite3.Row
                return batch_scan.fetch_registry_records_for_run(
                    conn, run_id)
            finally:
                conn.close()

        rows = _run_engine(
            _read_run_records,
            generic=("engine_unavailable", True, "retry",
                     f"khong doc duoc registry cua run {run_id}"))
        job.check_cancel()
        revision = store.bump_revision()
        _finish_workflow_job(store, job.job_id, "succeeded", run_id=run_id)
    except CancelledByUser:
        _finish_workflow_job(store, job.job_id, "canceled")
        raise
    except Exception:
        _finish_workflow_job(store, job.job_id, "failed")
        raise
    return _result("scan_report", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "run_id": run_id,
        "manifest_ref": {
            "path": str(manifest_path),
            "scope": "machine_local",
            "sha256": run["manifest_sha256"],
            "size_bytes": run["manifest_size"],
        },
        "folder": {"path": str(folder), "scope": "machine_local"},
        "stats": _dc(manifest.get("stats") or {}),
        "records": [_record_row(dict(r)) for r in rows],
        "revision": revision,
    }, source_files=[{"path": str(folder), "scope": "machine_local"}])


@_v1_boundary
def upload_audit_excel_v1(job, payload):
    """`upload.audit_excel` versioned → kind audit_report (contract §6.9).

    file_ref → .xlsx/.xlsm that; ngay wire ISO → engine dd/mm/yyyy o
    boundary; binding audit_id → website + file + hash + khoang ngay duoc
    giu de queue_get/prepare loai tru sau."""
    p = _require_workflow(payload)
    _require_payload_keys(p, _AUDIT_V1_KEYS)
    wid = _require_website(p)
    try:
        excel = existing_file(p.get("file_ref"))
    except CommandError as exc:
        # file_ref do nguoi dung chon: contract §8 bat retryable +
        # next_action — fileref.py tra bare CommandError (legacy giu
        # nguyen wire shape do), nang cap o boundary v1 nay.
        if exc.code == "file_not_found":
            raise CommandError("file_not_found", exc.message,
                               retryable=True, next_action="pick_files")
        if exc.code == "file_locked":
            raise CommandError("file_locked", exc.message,
                               retryable=True, next_action="retry")
        raise
    if excel.suffix.lower() not in _AUDIT_EXCEL_SUFFIXES:
        raise CommandError(
            "validation_error",
            "chi ho tro .xlsx/.xlsm (.xls chua co duong doc da kiem chung)")
    from_date = p.get("from_date")
    to_date = p.get("to_date")
    _require_iso_date(from_date, "from_date")
    _require_iso_date(to_date, "to_date")

    store = upload_workspace.open_store()
    provider = upload_workspace.get_provider(wid)
    _begin_workflow_job(store, job, command="upload.audit_excel",
                        website_id=wid, payload=p)
    try:
        job.report_progress(0, 1, "doc so excel")
        analysis = _analyze_excel(provider, excel, from_date, to_date)
        job.check_cancel()
        audit = upload_workspace.register_audit(
            wid, excel, from_date=from_date, to_date=to_date, store=store)
        revision = store.bump_revision()
        _finish_workflow_job(store, job.job_id, "succeeded",
                             audit_id=audit["audit_id"])
    except CancelledByUser:
        _finish_workflow_job(store, job.job_id, "canceled")
        raise
    except Exception:
        _finish_workflow_job(store, job.job_id, "failed")
        raise
    missing, issues = _audit_rows(analysis)
    job.report_progress(1, 1, "xong")
    return _result("audit_report", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "audit_id": audit["audit_id"],
        "from_date": from_date,
        "to_date": to_date,
        "summary": _dc(getattr(analysis, "summary", None) or {}),
        "missing": missing,
        "issues": issues,
        "revision": revision,
    }, source_files=[{"path": str(excel), "scope": "machine_local"}])


@_v1_boundary
def upload_queue_get(job, payload):
    """`upload.queue_get` → kind upload_queue (contract §6.11).

    Manifest chi giai quyet qua binding da luu (`resolve_run` kiem website
    + file + sha256); audit phai thuoc website va file Excel khong doi ke
    tu luc audit. Khong fallback, khong browser, khong bump revision —
    chi `queue_revision` tang khi gan audit moi cho run."""
    p = _require_workflow(payload)
    _require_payload_keys(p, _QUEUE_V1_KEYS)
    wid = _require_website(p)
    run_id = _require_run_id(p)
    audit_id = _optional_audit_id(p)
    store = upload_workspace.open_store()
    manifest_path = upload_workspace.resolve_run(wid, run_id, store=store)
    audit_rec = upload_workspace.resolve_audit(wid, audit_id, store=store)
    data_dir = upload_workspace.website_data_dir(wid, create=False)
    provider = upload_workspace.get_provider(wid)
    batch_scan = import_engine_module("upload_lab", "batch_scan")
    uploader = import_engine_module("upload_lab", "playwright_uploader")

    # Registry cua website phai con + doc duoc; thieu/hu = LOI, khong
    # bao gio tra queue rong gia thanh cong.
    registry_path = data_dir / "registry.sqlite3"
    if not registry_path.is_file():
        raise CommandError(
            "engine_unavailable",
            f"registry cua website {wid} khong con tren dia — quet lai",
            retryable=True, next_action="retry")

    def _read_queueable():
        # sqlite3.connect truc tiep + close trong finally — registry hu
        # thi SELECT that bai ngay (engine_unavailable), khong de lai
        # conn mo trong frame nhu connect_registry cua engine.
        conn = sqlite3.connect(str(registry_path))
        try:
            conn.row_factory = sqlite3.Row
            return batch_scan.fetch_registry_records_for_run(
                conn, run_id, statuses=uploader.QUEUE_STATUSES)
        finally:
            conn.close()

    queueable = _run_engine(
        _read_queueable,
        generic=("engine_unavailable", True, "retry",
                 "khong doc duoc registry"))
    _manifest, records, _total = _run_engine(
        lambda: uploader.load_upload_queue(
            manifest_path, working_dir=data_dir),
        generic=("engine_unavailable", True, "retry",
                 f"khong doc duoc queue cua run {run_id}"))
    if len(records) < len(queueable):
        raise CommandError(
            "engine_unavailable",
            f"{len(queueable) - len(records)} ho so cua run {run_id} "
            "thieu output JSON — quet lai folder",
            retryable=True, next_action="retry")

    analysis = None
    if audit_rec is not None:
        audit_file = Path(audit_rec["file_path"])
        if not audit_file.is_file():
            raise CommandError(
                "file_not_found",
                f"file Excel cua audit {audit_rec['audit_id']} khong con "
                "tren dia — audit lai",
                retryable=True, next_action="pick_files")
        bound_hash = audit_rec.get("file_sha256")
        if bound_hash and \
                upload_workspace.sha256_file(audit_file) != bound_hash:
            raise CommandError(
                "stale_revision",
                f"file Excel cua audit {audit_rec['audit_id']} da thay "
                "doi — audit lai",
                retryable=True, next_action="retry")
        if not audit_rec.get("from_date") or not audit_rec.get("to_date"):
            raise CommandError(
                "validation_error",
                "audit thieu khoang ngay — audit lai")
        analysis = _analyze_excel(
            provider, audit_file,
            audit_rec["from_date"], audit_rec["to_date"])
        # Ghi nhan audit dung voi run de prepare loai tru sau; gan audit
        # moi khac audit da gan → queue thay doi → bump queue_revision.
        bound = store.audit_for_run(run_id)
        if bound is None or bound["audit_id"] != audit_rec["audit_id"]:
            store.bind_run_audit(run_id, audit_rec["audit_id"])
            store.bump_queue_revision(run_id)

    classify_mod = import_engine_module(
        "upload_lab", "ui.services.scan_classification_service")
    classification = classify_mod.classify_scan_records(records, analysis)
    job.check_cancel()
    return _result("upload_queue", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "run_id": run_id,
        "audit_id": audit_rec["audit_id"] if audit_rec else None,
        "queue_revision": store.queue_revision(run_id),
        "has_excel": bool(classification.has_excel),
        "folder_rows": [_queue_row(r) for r in classification.folder_rows],
        "missing_in_excel_record_ids": sorted(
            int(i) for i in classification.missing_in_excel_record_ids),
    }, source_files=[{"path": str(manifest_path),
                      "scope": "machine_local"}])


# =====================================================================
# upload.workflow.v1 — phien browser, tai so, tung dot chuan bi
# (MIN-69 task 4 — contract §6.4-§6.8/§6.12/§6.14/§6.15, §7, §8).
#
# Nguyen tac:
# - Moi Playwright call tren upload_session worker thread duy nhat; op
#   mutating (open/prepare/download/staff/close) chiem op slot — op mutating
#   thu hai trong luc do bi `browser_busy` thay vi xep hang.
# - Wait-state THEO JOB: confirm_login/finish_review chi giai phong job
#   dang cho dung buoc + dung (website_id, browser_id) — wrong_job cho moi
#   truong hop khac, khong bao gio danh thuc nham.
# - Status/snapshot doc bo nho do browser thread cap nhat — khong spawn
#   thread, khong enqueue op, khong tao browser ngam.
# - Save chi duoc ghi nhan qua POST /api/hoso 2xx (engine xac minh);
#   tab dong thieu bang chung → needs_reconcile, khong bao gio 'da luu'.
# =====================================================================

_SESSION_START_V1_KEYS = frozenset({
    "workflow_version", "website_id", "expected_revision"})
_CONFIRM_V1_KEYS = frozenset({
    "workflow_version", "website_id", "browser_id", "target_job_id"})
_BROWSER_V1_KEYS = frozenset({
    "workflow_version", "website_id", "browser_id"})
_DOWNLOAD_V1_KEYS = frozenset({
    "workflow_version", "website_id", "browser_id",
    "from_date", "to_date"})
_STAFF_V1_KEYS = frozenset({
    "workflow_version", "website_id", "browser_id", "refresh"})
_PREPARE_V1_KEYS = frozenset({
    "workflow_version", "website_id", "browser_id", "run_id", "audit_id",
    "queue_revision", "record_ids", "chunk_size",
    "cong_chung_vien", "thu_ky"})
_RECONCILE_V1_KEYS = frozenset({
    "workflow_version", "website_id", "run_id", "audit_id"})

_STAFF_CACHE_NAME = "uploader_staff_options.json"


def _require_browser_id(payload) -> str:
    bid = payload.get("browser_id")
    if bid is None:
        raise CommandError("validation_error", "thieu browser_id")
    if not isinstance(bid, str) or not bid.strip() or bid != bid.strip():
        raise CommandError("validation_error",
                           "browser_id phai la chuoi khong rong")
    return bid


def _require_target_job_id(payload) -> str:
    target = payload.get("target_job_id")
    if target is None:
        raise CommandError("validation_error", "thieu target_job_id")
    if not isinstance(target, str) or not target.strip() \
            or target != target.strip():
        raise CommandError("validation_error",
                           "target_job_id phai la chuoi khong rong")
    return target


def _require_run_id(payload) -> str:
    run_id = payload.get("run_id")
    if run_id is None:
        raise CommandError("validation_error", "thieu run_id")
    if not isinstance(run_id, str) or not run_id.strip() \
            or run_id != run_id.strip():
        raise CommandError("validation_error",
                           "run_id phai la chuoi khong rong")
    return run_id


def _optional_audit_id(payload):
    """audit_id null duoc phep (prepare); ''/chuoi dem/padded →
    validation_error — cung luat strict voi _require_run_id (§3)."""
    audit_id = payload.get("audit_id")
    if audit_id is None:
        return None
    if not isinstance(audit_id, str) or not audit_id.strip() \
            or audit_id != audit_id.strip():
        raise CommandError("validation_error",
                           "audit_id phai la chuoi khong rong hoac null")
    return audit_id


def _optional_browser_id(payload):
    """browser_id null duoc phep (staff_options refresh=false);
    ''/padded → validation_error — cung luat strict _require_browser_id."""
    bid = payload.get("browser_id")
    if bid is None:
        return None
    if not isinstance(bid, str) or not bid.strip() \
            or bid != bid.strip():
        raise CommandError("validation_error",
                           "browser_id phai la chuoi khong rong hoac null")
    return bid


def _browser_scope(store, website_id, browser_id):
    """Kiem browser_id ton tai, dang mo, thuoc website va LA phien song
    hien tai cua worker — truoc moi thao tac browser (contract §3 rule 1)."""
    rec = store.browser_for(browser_id)
    if rec is None or rec.get("status") != "open":
        raise CommandError(
            "scope_violation",
            f"browser_id {browser_id!r} khong ton tai hoac da dong")
    upload_workspace.require_same_website(website_id, rec["website_id"])
    if worker().browser_id != browser_id:
        raise CommandError(
            "scope_violation",
            f"browser_id {browser_id!r} khong phai phien browser hien tai")
    return rec


def _require_login_confirmed():
    """Snapshot login phai la authenticated truoc op can phien that."""
    snap = worker().snapshot()
    if snap["login"].get("status") != "authenticated":
        raise CommandError(
            "upload.login_not_confirmed",
            "chua xac minh duoc dang nhap tren browser",
            retryable=True, next_action="login_required")


def _wait_for_release(job, ev, *, timeout_s, timeout_code, timeout_msg):
    """Vong cho chung cua waiting_user: release / cancel / browser chet /
    timeout — khong mot duong nao khac ket thuc job dang cho."""
    deadline = time.time() + timeout_s
    while True:
        job.check_cancel()
        released = ev.wait(0.3)
        if not worker().browser_alive():
            raise CommandError(
                "engine_unavailable",
                "browser da dong hoac mat ket noi trong luc cho",
                retryable=True, next_action="retry")
        if released:
            break
        if time.time() > deadline:
            raise CommandError(timeout_code, timeout_msg,
                               retryable=True, next_action="retry")
    job.check_cancel()
    try:
        job.resume()
    except CommandError:
        # Cancel co the dat job vao terminal giua check_cancel va resume —
        # uu tien huy cua nguoi dung thay vi loi resume.
        job.check_cancel()
        raise


def _utc_now_z() -> str:
    from datetime import timezone as _tz
    return _datetime.now(_tz.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z")


def _cache_fetched_at(data_dir) -> str | None:
    """mtime cua uploader_staff_options.json → fetched_at cho cache read."""
    path = Path(data_dir) / _STAFF_CACHE_NAME
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    from datetime import timezone as _tz
    return _datetime.fromtimestamp(mtime, _tz.utc).isoformat(
        timespec="seconds").replace("+00:00", "Z")


def _run_record_rows(data_dir, run_id):
    """Rows registry cua run (sqlite truc tiep + close trong finally —
    cung mau upload_queue_get: registry hu = LOI, khong tra rong)."""
    batch_scan = import_engine_module("upload_lab", "batch_scan")

    def _read():
        conn = sqlite3.connect(str(data_dir / "registry.sqlite3"))
        try:
            conn.row_factory = sqlite3.Row
            return batch_scan.fetch_registry_records_for_run(conn, run_id)
        finally:
            conn.close()

    return _run_engine(
        _read,
        generic=("engine_unavailable", True, "retry",
                 f"khong doc duoc registry cua run {run_id}"))


# ---------- dispatchers (legacy giu nguyen khi khong co workflow_version) --

def session_start_dispatch(job, payload):
    if isinstance(payload, dict) and "workflow_version" in payload:
        return upload_session_start_v1(job, payload)
    return session_start(job, payload)


def confirm_login_dispatch(job, payload):
    if isinstance(payload, dict) and "workflow_version" in payload:
        return upload_confirm_login_v1(job, payload)
    return confirm_login(job, payload)


def session_status_dispatch(job, payload):
    if isinstance(payload, dict) and "workflow_version" in payload:
        return upload_session_status_v1(job, payload)
    return session_status(job, payload)


def session_close_dispatch(job, payload):
    if isinstance(payload, dict) and "workflow_version" in payload:
        return upload_session_close_v1(job, payload)
    return session_close(job, payload)


def download_export_dispatch(job, payload):
    if isinstance(payload, dict) and "workflow_version" in payload:
        return upload_download_export_v1(job, payload)
    return download_export(job, payload)


def prepare_dispatch(job, payload):
    if isinstance(payload, dict) and "workflow_version" in payload:
        return upload_prepare_v1(job, payload)
    return prepare_upload(job, payload)


def finish_review_dispatch(job, payload):
    if isinstance(payload, dict) and "workflow_version" in payload:
        return upload_finish_review_v1(job, payload)
    return finish_review(job, payload)


# ---------- upload.session_start (§6.4) ----------

@_v1_boundary
def upload_session_start_v1(job, payload):
    """`upload.session_start` versioned → kind session_state.

    Mo Chromium tren website data dir → job waiting_user(login); confirm
    dung (website, browser, job) moi giai phong; job van kiem trang thai
    portal that truoc khi succeeded (login_not_confirmed neu chua that).
    """
    p = _require_workflow(payload)
    _require_payload_keys(p, _SESSION_START_V1_KEYS)
    wid = _require_website(p)
    expected = _require_revision(p, "expected_revision")
    store = upload_workspace.open_store()
    current = store.revision()
    if expected != current:
        raise CommandError(
            "stale_revision",
            f"expected_revision {expected} != hien tai {current} — "
            "doc lai workspace_get",
            retryable=True, next_action="retry")
    _begin_workflow_job(store, job, command="upload.session_start",
                        website_id=wid, payload=p)
    bid = None
    try:
        job.report_progress(0, 3, "mo Chromium")
        _run_engine(
            lambda: worker().call("open_manual_login",
                                  website_id=wid, mutating=True),
            generic=("engine_unavailable", True, "retry",
                     "khong mo duoc trinh duyet"))
        bid = worker().browser_id
        if not bid:
            raise CommandError(
                "engine_unavailable",
                "browser mo len nhung khong co browser_id",
                retryable=True, next_action="retry")
        # Browser moi = binding workspace moi → revision tang de client
        # doc lai (contract §3 rule 2).
        revision = store.bump_revision()
        store.upsert_job(job.job_id, browser_id=bid)
        job.report_progress(1, 3, "cho dang nhap")
        ev = worker().register_wait(
            job.job_id, waiting_on="login",
            website_id=wid, browser_id=bid)
        try:
            store.upsert_job(job.job_id, status="waiting_user",
                             waiting_on="login")
            job.set_waiting("login")
            _wait_for_release(
                job, ev,
                timeout_s=LOGIN_WAIT_TIMEOUT_S,
                timeout_code="upload.login_timeout",
                timeout_msg="het 15 phut cho dang nhap")
        finally:
            worker().unregister_wait(job.job_id)
        job.report_progress(2, 3, "xac nhan dang nhap")
        # Engine tra "authenticated" MOT LAN (one-shot) roi "idle" mai —
        # kiem snapshot da latch thay vi raw poll: idle poll co the da
        # tieu thu one-shot tu truoc. _poll_now buoc mot nhip poll dong
        # bo de snapshot moi nhat ngay tai thoi diem xac nhan.
        _run_engine(
            lambda: worker().call("_poll_now", website_id=wid),
            generic=("engine_unavailable", True, "retry",
                     "khong doc duoc trang thai dang nhap"))
        status = str(worker().snapshot()["login"].get("status") or "")
        if status != "authenticated":
            raise CommandError(
                "upload.login_not_confirmed",
                f"trang thai dang nhap: {status or 'khong ro'}",
                retryable=True, next_action="login_required")
        options = _run_engine(
            lambda: worker().call("fetch_staff_options",
                                  website_id=wid, mutating=True),
            generic=("engine_unavailable", True, "retry",
                     "khong doc duoc danh sach nhan su"))
        _finish_workflow_job(store, job.job_id, "succeeded")
    except CancelledByUser:
        _finish_workflow_job(store, job.job_id, "canceled")
        raise
    except Exception:
        _finish_workflow_job(store, job.job_id, "failed")
        raise
    job.report_progress(3, 3, "da dang nhap")
    return _result("session_state", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "browser_id": bid,
        "login": {"status": "authenticated",
                  "checked_at": _utc_now_z()},
        "staff_options": {
            "cong_chung_vien": [
                str(v) for v in (options or {}).get("cong_chung_vien") or []],
            "thu_ky": [
                str(v) for v in (options or {}).get("thu_ky") or []],
            "source": "portal",
        },
        "revision": revision,
    })


# ---------- upload.confirm_login / upload.finish_review (§6.5) ----------

def _confirm_or_finish(job, payload, *, waiting_on, result_flag):
    p = _require_workflow(payload)
    _require_payload_keys(p, _CONFIRM_V1_KEYS)
    wid = _require_website(p)
    bid = _require_browser_id(p)
    target = _require_target_job_id(p)
    store = upload_workspace.open_store()
    _browser_scope(store, wid, bid)
    released = worker().confirm_wait(
        target, waiting_on=waiting_on,
        website_id=wid, browser_id=bid)
    if not released:
        raise CommandError(
            "wrong_job",
            f"target_job_id khong phai job dang cho "
            f"'{waiting_on}' tren browser/website nay")
    return _result("session_state", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "browser_id": bid,
        "target_job_id": target,
        result_flag: True,
    })


@_v1_boundary
def upload_confirm_login_v1(job, payload):
    """`upload.confirm_login` versioned — xin xac nhan dang nhap.

    Chi dat event cua dung job dang waiting_on=login; job session_start
    van phai tu kiem portal that (§6.5)."""
    return _confirm_or_finish(
        job, payload, waiting_on="login", result_flag="login_confirmed")


@_v1_boundary
def upload_finish_review_v1(job, payload):
    """`upload.finish_review` versioned — xong buoc kiem tra tab.

    Giai phong dung job prepare waiting_on=review; KHONG danh dau
    uploaded_success — saves doc qua session_status (§6.5/§7.7)."""
    return _confirm_or_finish(
        job, payload, waiting_on="review", result_flag="review_finished")


# ---------- upload.session_status (§6.6) ----------

@_v1_boundary
def upload_session_status_v1(job, payload):
    """`upload.session_status` versioned → kind session_state.

    Doc snapshot do browser thread cap nhat lien tuc — KHONG enqueue op,
    KHONG spawn thread, KHONG tao browser ngam (§7.1/§7.2)."""
    p = _require_workflow(payload)
    _require_payload_keys(p, _BROWSER_V1_KEYS)
    wid = _require_website(p)
    bid = _require_browser_id(p)
    store = upload_workspace.open_store()
    _browser_scope(store, wid, bid)
    snap = worker().snapshot()
    return _result("session_state", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "browser_id": bid,
        "login": snap["login"],
        "tabs": snap["tabs"],
    })


# ---------- upload.session_close (§6.7) ----------

@_v1_boundary
def upload_session_close_v1(job, payload):
    """`upload.session_close` versioned → kind session_state.

    Poll/reconcile lan cuoi tren browser thread truoc khi dong; tab con
    mo ma khong xac dinh → needs_reconcile. Khong bao gio tu bam Luu va
    khong hoan tac save da xac minh (§7.3)."""
    p = _require_workflow(payload)
    _require_payload_keys(p, _BROWSER_V1_KEYS)
    wid = _require_website(p)
    bid = _require_browser_id(p)
    store = upload_workspace.open_store()
    _browser_scope(store, wid, bid)
    _begin_workflow_job(store, job, command="upload.session_close",
                        website_id=wid, browser_id=bid, payload=p)
    try:
        # _poll_then_close la MOT op tren browser thread: poll/reconcile
        # lan cuoi roi dong ngay — khong op mutating nao xen giua nhip
        # poll va close (§7.3). Xep hang sau op dang chay (cho no nha
        # browser) va dat stop event truoc de engine dung som.
        _run_engine(
            lambda: worker().call("_poll_then_close", website_id=wid,
                                  stop_current=True),
            generic=("engine_unavailable", True, "retry",
                     "khong doi chieu/dong duoc browser"))
        # Tab van con mo sau poll cuoi → khong xac dinh → needs_reconcile
        # (giu run_id de upload.reconcile doi chieu theo dung run).
        open_ids = store.open_tab_record_ids(wid)
        if open_ids:
            run_map = worker().tab_run_map()
            store.remove_open_tabs(wid, open_ids)
            for rid in open_ids:
                store.add_needs_reconcile(
                    wid, [rid], run_id=run_map.get(rid),
                    reason="browser dong khi tab chua xac minh Luu")
        snap = worker().snapshot()
        _finish_workflow_job(store, job.job_id, "succeeded")
    except CancelledByUser:
        _finish_workflow_job(store, job.job_id, "canceled")
        raise
    except Exception:
        _finish_workflow_job(store, job.job_id, "failed")
        raise
    return _result("session_state", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "browser_id": bid,
        "closed": True,
        "verified_record_ids": snap["tabs"]["saved_record_ids"],
        "needs_reconcile_record_ids": store.needs_reconcile_ids(wid),
    })


# ---------- upload.download_export (§6.8) ----------

@_v1_boundary
def upload_download_export_v1(job, payload):
    """`upload.download_export` versioned → kind export_download.

    Cung browser cua website; ngay wire ISO → dd/mm/yyyy cho engine o
    boundary. Chi tra file HOAN TAT (file_ref + sha256 + size) — download
    gian doan nem loi truoc khi file_ref duoc tra (§6.8/§7.5/§7.6)."""
    p = _require_workflow(payload)
    _require_payload_keys(p, _DOWNLOAD_V1_KEYS)
    wid = _require_website(p)
    bid = _require_browser_id(p)
    from_iso = p.get("from_date")
    to_iso = p.get("to_date")
    _require_iso_date(from_iso, "from_date")
    _require_iso_date(to_iso, "to_date")
    store = upload_workspace.open_store()
    _browser_scope(store, wid, bid)
    _require_login_confirmed()
    _begin_workflow_job(store, job, command="upload.download_export",
                        website_id=wid, browser_id=bid, payload=p)
    try:
        job.report_progress(0, 2, "tai so cong chung")
        path = _run_engine(
            lambda: worker().call(
                "download_contract_book_export",
                website_id=wid, mutating=True,
                from_date=_ddmmyyyy_from_iso(from_iso, "from_date"),
                to_date=_ddmmyyyy_from_iso(to_iso, "to_date")),
            generic=("engine_unavailable", True, "retry",
                     "tai export that bai"))
        job.check_cancel()
        path = Path(path)
        if not path.is_file():
            raise CommandError(
                "engine_unavailable",
                "export ket thuc nhung khong thay file tren dia",
                retryable=True, next_action="retry")
        job.report_progress(1, 2, "xong")
        _finish_workflow_job(store, job.job_id, "succeeded")
    except CancelledByUser:
        _finish_workflow_job(store, job.job_id, "canceled")
        raise
    except Exception:
        _finish_workflow_job(store, job.job_id, "failed")
        raise
    return _result("export_download", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "file_ref": {
            "path": str(path),
            "scope": "machine_local",
            "sha256": upload_workspace.sha256_file(path),
            "size_bytes": path.stat().st_size,
        },
        "from_date": from_iso,
        "to_date": to_iso,
    }, source_files=[{"path": str(path), "scope": "machine_local"}])


# ---------- upload.staff_options (§6.12) ----------

@_v1_boundary
def upload_staff_options_v1(job, payload):
    """`upload.staff_options` → kind staff_options.

    refresh=false doc cache theo website (co the khong can browser);
    refresh=true can browser_id da dang nhap, chay tren browser thread.
    Khong lo credential/cookie/storage state (§7.4)."""
    p = _require_workflow(payload)
    _require_payload_keys(p, _STAFF_V1_KEYS)
    wid = _require_website(p)
    refresh = p.get("refresh")
    if not isinstance(refresh, bool):
        raise CommandError("validation_error", "refresh phai la bool")
    bid = _optional_browser_id(p)
    store = upload_workspace.open_store()
    data_dir = upload_workspace.website_data_dir(wid)
    provider = upload_workspace.get_provider(wid)
    if refresh:
        if bid is None:
            raise CommandError(
                "validation_error",
                "refresh=true can browser_id cua phien da dang nhap")
        _browser_scope(store, wid, bid)
        _require_login_confirmed()
        _begin_workflow_job(store, job, command="upload.staff_options",
                            website_id=wid, browser_id=bid, payload=p)
        try:
            options = _run_engine(
                lambda: worker().call("fetch_staff_options",
                                      website_id=wid, mutating=True),
                generic=("engine_unavailable", True, "retry",
                         "khong doc duoc danh sach nhan su"))
            _finish_workflow_job(store, job.job_id, "succeeded")
        except CancelledByUser:
            _finish_workflow_job(store, job.job_id, "canceled")
            raise
        except Exception:
            _finish_workflow_job(store, job.job_id, "failed")
            raise
        source = "portal"
        fetched_at = _utc_now_z()
    else:
        options = _run_engine(
            lambda: provider.load_staff_options_cache(data_dir),
            generic=("engine_unavailable", True, "retry",
                     "khong doc duoc cache nhan su"))
        source = "cache"
        fetched_at = _cache_fetched_at(data_dir)
    return _result("staff_options", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "cong_chung_vien": [
            str(v) for v in (options or {}).get("cong_chung_vien") or []],
        "thu_ky": [str(v) for v in (options or {}).get("thu_ky") or []],
        "source": source,
        "fetched_at": fetched_at,
    })


# ---------- upload.prepare (§6.14) ----------

@_v1_boundary
def upload_prepare_v1(job, payload):
    """`upload.prepare` versioned → kind upload_prepare.

    Manifest giai quyet qua binding run→manifest (resolve_run kiem website
    + file + hash). Backend tinh loai tru tu audit that + needs_reconcile
    — khong tin danh sach renderer. Dry-run: mo toi da chunk_size tab da
    dien roi waiting_user(review); Save chi dem khi engine xac minh POST
    /api/hoso 2xx (poll ghi registry uploaded_success + bo khoi queue).
    """
    p = _require_workflow(payload)
    _require_payload_keys(p, _PREPARE_V1_KEYS)
    wid = _require_website(p)
    bid = _require_browser_id(p)
    run_id = _require_run_id(p)
    audit_id = _optional_audit_id(p)
    queue_rev = _require_revision(p, "queue_revision")
    ids = p.get("record_ids")
    if not isinstance(ids, list) or not ids:
        raise CommandError("validation_error",
                           "record_ids phai la list khong rong")
    record_ids = []
    for item in ids:
        if not isinstance(item, int) or isinstance(item, bool) or item < 1:
            raise CommandError("validation_error",
                               "record_ids phai la list int >= 1")
        if item in record_ids:
            raise CommandError("validation_error",
                               "record_ids trung lap")
        record_ids.append(item)
    chunk_size = p.get("chunk_size")
    if not isinstance(chunk_size, int) or isinstance(chunk_size, bool) \
            or not 1 <= chunk_size <= 30:
        raise CommandError("validation_error",
                           "chunk_size phai la int 1..30")
    for key in ("cong_chung_vien", "thu_ky"):
        if p.get(key) == "":
            raise CommandError("validation_error",
                               f"{key}: dung null thay chuoi rong")
        if p.get(key) is not None and not isinstance(p[key], str):
            raise CommandError("validation_error",
                               f"{key} phai la string/null")
    cong_chung_vien = p.get("cong_chung_vien")
    thu_ky = p.get("thu_ky")

    store = upload_workspace.open_store()
    _browser_scope(store, wid, bid)
    manifest_path = upload_workspace.resolve_run(wid, run_id, store=store)
    audit_rec = upload_workspace.resolve_audit(wid, audit_id, store=store)
    current_qrev = store.queue_revision(run_id)
    if queue_rev != current_qrev:
        raise CommandError(
            "stale_revision",
            f"queue_revision {queue_rev} != hien tai {current_qrev} — "
            "doc lai queue_get",
            retryable=True, next_action="retry")
    data_dir = upload_workspace.website_data_dir(wid)
    provider = upload_workspace.get_provider(wid)
    uploader = import_engine_module("upload_lab", "playwright_uploader")
    registry_path = data_dir / "registry.sqlite3"
    if not registry_path.is_file():
        raise CommandError(
            "engine_unavailable",
            f"registry cua website {wid} khong con tren dia — quet lai",
            retryable=True, next_action="retry")
    run_rows = _run_record_rows(data_dir, run_id)
    run_record_ids = {int(r["id"]) for r in run_rows}
    contract_no_by_id = {
        int(r["id"]): str(r["contract_no"] or "") for r in run_rows}
    outside = sorted(set(record_ids) - run_record_ids)
    if outside:
        raise CommandError(
            "scope_violation",
            f"record_ids khong thuoc run {run_id}: {outside}")

    # --- Backend tinh loai tru (contract §3 rule 4) ---------------------
    # a) so cong chung da co tren web theo audit that — CANONICAL hai
    #    phia (cat so 0 dau) giong queue_get: "0101/2026" trong folder
    #    khop Excel "101/2026". normalize tho cua engine giu so 0 → neu
    #    chi dua set do cho split_records_by_existing_contract_nos thi
    #    record dem so 0 khong bao gio khop → upload trung.
    exclude = set()
    canon_existing = set()
    if audit_rec is not None:
        audit_file = Path(audit_rec["file_path"])
        if not audit_file.is_file():
            raise CommandError(
                "file_not_found",
                f"file Excel cua audit {audit_rec['audit_id']} khong con "
                "tren dia — audit lai",
                retryable=True, next_action="pick_files")
        bound_hash = audit_rec.get("file_sha256")
        if bound_hash and \
                upload_workspace.sha256_file(audit_file) != bound_hash:
            raise CommandError(
                "stale_revision",
                f"file Excel cua audit {audit_rec['audit_id']} da thay "
                "doi — audit lai",
                retryable=True, next_action="retry")
        if not audit_rec.get("from_date") or not audit_rec.get("to_date"):
            raise CommandError(
                "validation_error",
                "audit thieu khoang ngay — audit lai")
        analysis = _analyze_excel(
            provider, audit_file,
            audit_rec["from_date"], audit_rec["to_date"])
        for row in analysis.display_rows:
            cn = _canonical_contract_no(getattr(row, "contract_no", ""))
            if cn:
                canon_existing.add(cn)
    # b) ho so can doi chieu giu chan khoi dot chuan bi (§6.15)
    needs = set(store.needs_reconcile_ids(wid))
    dropped_needs = sorted(set(record_ids) & needs)
    for rid in dropped_needs:
        cn = uploader.normalize_contract_no_for_compare(
            contract_no_by_id.get(rid, ""))
        if cn:
            exclude.add(cn)
    # a2) Pre-filter adapter-side: record co canonical ∈ Excel bi loai
    # khoi dot — khong phu thuoc engine normalize (giu so 0). exclude
    # van mang dang ENGINE se tinh cho tung record (zero-keeping) de
    # split_records_by_existing_contract_nos khop duoc that — lop ve
    # phong thu hai neu contract_no record khac registry.
    dropped_excel = sorted(
        rid for rid in record_ids
        if rid not in needs
        and _canonical_contract_no(contract_no_by_id.get(rid, ""))
        in canon_existing)
    for rid in dropped_excel:
        cn = uploader.normalize_contract_no_for_compare(
            contract_no_by_id.get(rid, ""))
        if cn:
            exclude.add(cn)
    dropped_set = needs | set(dropped_excel)
    selected = [rid for rid in record_ids if rid not in dropped_set]

    _require_login_confirmed()
    _begin_workflow_job(
        store, job, command="upload.prepare", website_id=wid,
        browser_id=bid, run_id=run_id, audit_id=audit_id,
        record_ids=record_ids, payload=p)

    stop = threading.Event()
    done = threading.Event()

    def _watch_cancel():
        while not done.is_set():
            if job._cancel.wait(0.05):
                stop.set()
                return

    threading.Thread(target=_watch_cancel, daemon=True).start()
    try:
        def on_progress(ev2):
            job.check_cancel()
            prepared = int(
                ev2.get("prepared_count") or ev2.get("prepared") or 0)
            total = int(ev2.get("filtered_pending")
                        or ev2.get("total_pending") or 0)
            job.report_progress(prepared, total or 1,
                                str(ev2.get("event") or "prepare"))

        job.report_progress(0, 1, "mo tab da dien (dry-run)")
        summary = _run_engine(
            lambda: worker().call(
                "prepare_manifest", manifest_path, stop,
                website_id=wid, mutating=True, stop_event=stop,
                selected_record_ids=set(selected),
                exclude_contract_nos=exclude,
                cong_chung_vien=cong_chung_vien,
                thu_ky=thu_ky,
                chunk_size=chunk_size,
                progress_callback=on_progress),
            generic=("engine_unavailable", True, "retry",
                     "chuan bi ho so that bai"))
        job.check_cancel()
        errors = list((summary or {}).get("errors") or [])
        open_ids = {int(i) for i in
                    (summary or {}).get("open_record_ids") or []}
        batch_open = sorted(open_ids & set(selected))
        if batch_open:
            store.add_open_tabs(wid, batch_open, run_id=run_id,
                                browser_id=bid)
            worker().note_open_tabs(run_id, batch_open)
        if not batch_open:
            # Khong con gi de kiem tra (excluded het hoac fail toan bo)
            # → terminal ngay, KHONG waiting_user.
            data = _prepare_result_data(
                wid, bid, run_id, audit_id, record_ids, summary,
                errors, store, adapter_excluded=len(dropped_excel))
            _finish_workflow_job(
                store, job.job_id, "partial" if errors else "succeeded")
            return _prepare_result(data, errors)
        store.upsert_job(job.job_id, status="waiting_user",
                         waiting_on="review")
        ev = worker().register_wait(
            job.job_id, waiting_on="review",
            website_id=wid, browser_id=bid)
        try:
            job.set_waiting("review")
            _wait_for_release(
                job, ev,
                timeout_s=REVIEW_WAIT_TIMEOUT_S,
                timeout_code="upload.review_timeout",
                timeout_msg="het 60 phut cho kiem tra tab")
        finally:
            worker().unregister_wait(job.job_id)
        # Reconcile lan cuoi TRUOC khi doc ket qua: save via POST /api/hoso
        # vua bam co the chua kip mot nhip idle poll — _poll_now bao dam
        # snapshot/store cap nhat dong bo tren browser thread.
        _run_engine(
            lambda: worker().call("_poll_now", website_id=wid),
            generic=("engine_unavailable", True, "retry",
                     "khong doi chieu duoc tab sau kiem tra"))
        data = _prepare_result_data(
            wid, bid, run_id, audit_id, record_ids, summary,
            errors, store, adapter_excluded=len(dropped_excel))
        _finish_workflow_job(
            store, job.job_id, "partial" if errors else "succeeded",
            verified_record_ids=data["saved_record_ids"])
        return _prepare_result(data, errors)
    except CancelledByUser:
        _finish_workflow_job(store, job.job_id, "canceled")
        raise
    except Exception:
        _finish_workflow_job(store, job.job_id, "failed")
        raise
    finally:
        done.set()


def _prepare_result_data(wid, bid, run_id, audit_id, record_ids,
                         summary, errors, store, adapter_excluded=0):
    """Data §6.14 — breakdown tach 'da dien' (prepared) khoi 'da Luu'
    (saved); saved chi tu snapshot da xac minh cua browser thread.
    `adapter_excluded`: so record bi adapter loai truoc khi goi engine
    (canonical Excel match) — cong vao excluded_duplicates cua engine."""
    snap = worker().snapshot()
    tabs = snap["tabs"]
    requested = set(record_ids)
    saved = sorted(set(tabs["saved_record_ids"]) & requested)
    closed = sorted(set(tabs["closed_record_ids"]) & requested)
    unknown = sorted(set(tabs["unknown_record_ids"]) & requested)
    still_open = sorted(set(tabs["open_record_ids"]) & requested)
    failed_ids = {int(e.get("record_id") or 0) for e in errors}
    prepared_ids = set(still_open) | set(saved) | set(closed) | set(unknown)
    succeeded = []
    for rid in record_ids:
        if rid in failed_ids or rid not in prepared_ids:
            continue
        succeeded.append({
            "record_id": rid,
            "stage": "saved" if rid in saved else "prepared",
        })
    failed = [{
        "record_id": int(e.get("record_id") or 0),
        "stage": "prepared",
        "code": "upload_failed",
        "message": str(e.get("error") or ""),
    } for e in errors]
    needs_reconcile = sorted(
        (set(closed) | set(unknown)
         | (set(store.needs_reconcile_ids(wid, run_id=run_id))
            & requested)))
    return {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "browser_id": bid,
        "run_id": run_id,
        "audit_id": audit_id,
        "summary": {
            "total_requested": len(record_ids),
            "prepared_count": int((summary or {}).get("prepared_count") or 0),
            "remaining": int((summary or {}).get("remaining") or 0),
            "open_record_ids": still_open,
            "excluded_duplicates": int(
                (summary or {}).get("excluded_duplicates") or 0)
            + int(adapter_excluded),
        },
        "breakdown": {"succeeded": succeeded, "failed": failed},
        "saved_record_ids": saved,
        "needs_reconcile_record_ids": needs_reconcile,
    }


def _prepare_result(data, errors):
    """upload_prepare result; co loi tung muc → partial + error code
    upload.partial_failure (contract §6.14/§8)."""
    result = _result("upload_prepare", data)
    if errors:
        result["partial"] = True
        result["error"] = error_object(
            "upload.partial_failure",
            f"{len(errors)} ho so chuan bi that bai",
            retryable=True, next_action="retry")
    return result


# ---------- upload.reconcile (§6.15) ----------

@_v1_boundary
def upload_reconcile_v1(job, payload):
    """`upload.reconcile` → kind reconcile_report.

    Doi chieu ho so needs_reconcile cua run voi audit MOI (bat buoc):
    so da thay tren web → verified (registry uploaded_success + mo khoa
    needs_reconcile); con lai giu cho doi chieu sau. Khong tu gui lai."""
    p = _require_workflow(payload)
    _require_payload_keys(p, _RECONCILE_V1_KEYS)
    wid = _require_website(p)
    run_id = _require_run_id(p)
    audit_id = _optional_audit_id(p)
    if audit_id is None:
        raise CommandError("validation_error",
                           "reconcile can audit_id (audit moi da nap)")
    store = upload_workspace.open_store()
    upload_workspace.resolve_run(wid, run_id, store=store)
    audit_rec = upload_workspace.resolve_audit(wid, audit_id, store=store)
    data_dir = upload_workspace.website_data_dir(wid)
    provider = upload_workspace.get_provider(wid)
    uploader = import_engine_module("upload_lab", "playwright_uploader")

    audit_file = Path(audit_rec["file_path"])
    if not audit_file.is_file():
        raise CommandError(
            "file_not_found",
            f"file Excel cua audit {audit_rec['audit_id']} khong con "
            "tren dia — audit lai",
            retryable=True, next_action="pick_files")
    bound_hash = audit_rec.get("file_sha256")
    if bound_hash and \
            upload_workspace.sha256_file(audit_file) != bound_hash:
        raise CommandError(
            "stale_revision",
            f"file Excel cua audit {audit_rec['audit_id']} da thay doi — "
            "audit lai",
            retryable=True, next_action="retry")
    if not audit_rec.get("from_date") or not audit_rec.get("to_date"):
        raise CommandError("validation_error",
                           "audit thieu khoang ngay — audit lai")
    analysis = _analyze_excel(
        provider, audit_file, audit_rec["from_date"], audit_rec["to_date"])
    # Canonical HAI PHIA (cat so 0 dau — cung dang queue_get/prepare):
    # record "0101/2026" khop audit "101/2026"; dung normalize tho
    # (giu so 0) o mot phia se bo sot ho so da len web that.
    existing = {
        _canonical_contract_no(getattr(row, "contract_no", ""))
        for row in analysis.display_rows}
    existing.discard("")

    needs = store.needs_reconcile_ids(wid, run_id=run_id)
    _begin_workflow_job(store, job, command="upload.reconcile",
                        website_id=wid, run_id=run_id,
                        audit_id=audit_id, record_ids=needs, payload=p)
    try:
        verified = []
        if needs:
            rows = _run_record_rows(data_dir, run_id)
            cn_by_id = {int(r["id"]): str(r["contract_no"] or "")
                        for r in rows}
            for rid in needs:
                cn = _canonical_contract_no(cn_by_id.get(rid, ""))
                if cn and cn in existing:
                    verified.append(rid)
        if verified:
            _run_engine(
                lambda: uploader.finalize_uploaded_records(
                    verified, working_dir=data_dir),
                generic=("engine_unavailable", True, "retry",
                         "khong ghi duoc uploaded_success"))
            store.clear_needs_reconcile(wid, verified)
            store.remove_open_tabs(wid, verified)
            store.bump_queue_revision(run_id)
        # Audit moi gan vao run (nhu queue_get) de dot sau dung so nay.
        bound = store.audit_for_run(run_id)
        if bound is None or bound["audit_id"] != audit_rec["audit_id"]:
            store.bind_run_audit(run_id, audit_rec["audit_id"])
            store.bump_queue_revision(run_id)
        remaining = store.needs_reconcile_ids(wid, run_id=run_id)
        _finish_workflow_job(store, job.job_id, "succeeded",
                             verified_record_ids=verified)
    except CancelledByUser:
        _finish_workflow_job(store, job.job_id, "canceled")
        raise
    except Exception:
        _finish_workflow_job(store, job.job_id, "failed")
        raise
    return _result("reconcile_report", {
        "workflow_version": WORKFLOW_VERSION,
        "website_id": wid,
        "run_id": run_id,
        "audit_id": audit_id,
        "verified_record_ids": verified,
        "needs_reconcile_record_ids": remaining,
    })

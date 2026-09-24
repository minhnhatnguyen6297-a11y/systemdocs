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
import threading
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path

from errors import CommandError
from engine_roots import engine_root, import_engine_module
from fileref import validate_file_ref
from upload_session import worker, LOGIN_WAIT_TIMEOUT_S, REVIEW_WAIT_TIMEOUT_S
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
    job.set_waiting("login")
    worker().login_confirmed.clear()
    deadline = time.time() + LOGIN_WAIT_TIMEOUT_S
    while not worker().login_confirmed.is_set():
        job.check_cancel()
        if time.time() > deadline:
            raise CommandError(
                "ocr.login_timeout",
                "het thoi gian cho dang nhap", retryable=True,
                next_action="upload.session_start lai")
        time.sleep(0.3)
    job.resume()
    job.report_progress(2, 3, "xac nhan dang nhap")
    result = worker().call("poll_manual_login", force=True)
    status = str((result or {}).get("status") or "")
    if status != "authenticated":
        raise CommandError(
            "upload.login_not_confirmed",
            f"trang thai dang nhap: {status or 'khong ro'}", retryable=True,
            next_action="dang nhap tren Chromium roi bam Xac nhan lai")
    options = worker().call("fetch_staff_options")
    job.report_progress(3, 3, "da dang nhap")
    return _result("session_state",
                   {"login": result, "staff_options": _dc(options)})


def confirm_login(job, payload):
    """Nguoi dung xac nhan da dang nhap → giai phong job session_start."""
    worker().login_confirmed.set()
    return _result("session_state", {"login_confirmed": True})


def session_close(job, payload):
    try:
        worker().call("_close")
    except CommandError:
        raise
    except Exception:
        worker().login_confirmed.set()
        worker().review_finished.set()
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
    worker().review_finished.clear()
    job.set_waiting("review")
    deadline = time.time() + REVIEW_WAIT_TIMEOUT_S
    while not worker().review_finished.is_set():
        job.check_cancel()
        if time.time() > deadline:
            raise CommandError("upload.review_timeout",
                               "het thoi gian cho review", retryable=True)
        time.sleep(0.5)
    job.resume()
    pages = worker().call("poll_prepared_pages")
    return _result(
        "upload_prepare",
        {"summary": _dc(summary), "pages": _dc(pages),
         "note": "dry-run — nguoi dung da tu kiem tra/luu trong Chromium"})


def finish_review(job, payload):
    """Nguoi dung xac nhan da kiem tra xong cac tab → job prepare ket thuc."""
    worker().review_finished.set()
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


def upload_websites(job, payload):
    """`upload.websites` → kind website_catalog (contract §6.1)."""
    _require_workflow(payload)
    store = upload_workspace.open_store()
    return _result("website_catalog", {
        "workflow_version": WORKFLOW_VERSION,
        "websites": upload_workspace.list_websites(),
        "selected_website_id": store.selected_website_id(),
    })


def upload_workspace_get(job, payload):
    """`upload.workspace_get` → kind upload_workspace (§6.2).

    website_id null → doc lua chon da luu; website chua chon lan nao →
    workspace rong (website_id null, revision 0)."""
    _require_workflow(payload)
    wid = _optional_website(payload)
    snap = upload_workspace.workspace_snapshot(wid)
    return _result("upload_workspace", snap)


def upload_website_select(job, payload):
    """`upload.website_select` → kind upload_workspace (§6.2).

    Backend kiem lai dieu kien doi (khong chi UI): website cu con job/
    tab cho kiem tra → workflow_busy; revision lech → stale_revision."""
    _require_workflow(payload)
    wid = _require_website(payload)
    expected = _require_revision(payload, "expected_revision")
    snap = upload_workspace.select_website(wid, expected)
    return _result("upload_workspace", snap)


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

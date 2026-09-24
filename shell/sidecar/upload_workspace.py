"""Upload workflow data root + scope helpers (MIN-69 task 2).

Tach **vi tri code** (engine root — chi de import module that) khoi
**vi tri du lieu** (data root do Electron main inject qua env
`G1_UPLOAD_DATA_DIR`, mac dinh `<G1_OUTPUT_DIR>/upload_lab`).

Layout theo plan §3.2:

    <data_root>/workspace.sqlite3           # UploadWorkspaceStore
    <data_root>/websites/<website_id>/      # working_dir engine cua website
        registry.sqlite3 output/ runs/ downloads/ upload_runs/
        nd_storage_state.json uploader_staff_options.json logs/

Moi lenh nghiep vu versioned ghi doc qua `website_data_dir(website_id)` —
khong bao gio default vao thu muc cai dat/engine root.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from pathlib import Path

from engine_roots import import_engine_module, output_dir
from errors import CommandError
from upload_workspace_store import UploadWorkspaceStore

DATA_ROOT_ENV = "G1_UPLOAD_DATA_DIR"
WEBSITES_DIR_NAME = "websites"
WORKSPACE_DB_NAME = "workspace.sqlite3"
WEBSITE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}$")

_store = None
_store_lock_path = None


# ---------- data root ----------

def upload_data_root(*, create=True) -> Path:
    """Data root do Electron main inject (userData/upload_lab).

    `G1_UPLOAD_DATA_DIR` > `<G1_OUTPUT_DIR>/upload_lab` (output_dir da
    fallback ve <shell>/output o dev). Khong bao gio mac dinh vao engine
    root hay thu muc cai dat.
    """
    raw = os.environ.get(DATA_ROOT_ENV)
    base = Path(raw).expanduser() if raw else (output_dir() / "upload_lab")
    base = base.resolve()
    if create:
        base.mkdir(parents=True, exist_ok=True)
    return base


def workspace_db_path() -> Path:
    return upload_data_root() / WORKSPACE_DB_NAME


def open_store() -> UploadWorkspaceStore:
    """Store dung chung trong process (reopen neu data root doi — test)."""
    global _store, _store_lock_path
    db = workspace_db_path()
    if _store is None or _store_lock_path != db:
        if _store is not None:
            try:
                _store.close()
            except Exception:
                pass
        _store = UploadWorkspaceStore(db)
        _store_lock_path = db
    return _store


def reset_store_for_tests():
    """Dong store cache — test goi sau khi doi G1_UPLOAD_DATA_DIR."""
    global _store, _store_lock_path
    if _store is not None:
        try:
            _store.close()
        except Exception:
            pass
    _store = None
    _store_lock_path = None


# ---------- website scope ----------

def _providers_module():
    """providers package trong engine root (code that, khong copy)."""
    return import_engine_module("upload_lab", "providers")


def list_websites() -> list:
    return _providers_module().list_websites()


def get_provider(website_id):
    """Provider engine cho website_id; unknown → CommandError(unknown_website)."""
    providers = _providers_module()
    try:
        return providers.get_provider(website_id)
    except providers.UnknownWebsiteError as exc:
        raise CommandError("unknown_website", str(exc)) from exc
    except Exception as exc:
        # provider.registry co the raise UnknownWebsiteError qua module khac
        if getattr(exc, "code", None) == "unknown_website":
            raise CommandError("unknown_website", str(exc)) from exc
        raise


def validate_website_id(website_id) -> str:
    """Slug + da dang ky. Tra website_id chuan hoac CommandError."""
    if not isinstance(website_id, str) or not WEBSITE_ID_RE.match(website_id):
        raise CommandError(
            "unknown_website" if isinstance(website_id, str)
            else "validation_error",
            f"website_id khong hop le/chua dang ky: {website_id!r}")
    return get_provider(website_id).website_id


def website_data_dir(website_id, *, create=True) -> Path:
    """`<data_root>/websites/<website_id>` da kiem chung + layout chuan."""
    wid = validate_website_id(website_id)
    provider = get_provider(wid)
    data_dir = provider.website_data_dir(upload_data_root())
    if create:
        return provider.ensure_data_layout(data_dir)
    return provider.assert_data_dir(data_dir)


def require_same_website(website_id, actual_website_id):
    """Reject khi tham chieu thuoc website khac (contract §3 rule 1)."""
    if actual_website_id != website_id:
        raise CommandError(
            "website_mismatch",
            f"tham chieu thuoc website {actual_website_id!r}, "
            f"khong phai {website_id!r}")


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- run/audit/browser bindings ----------

def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register_run(website_id, manifest_path, *, run_id=None, store=None) -> dict:
    """Ghi binding run→manifest sau khi scan xong (doc run_id tu manifest
    neu khong truyen). Tra record runs."""
    manifest = Path(manifest_path)
    if run_id is None:
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CommandError("validation_error",
                               f"manifest khong doc duoc: {exc}") from exc
        run_id = str(data.get("run_id") or "").strip()
        if not run_id:
            raise CommandError("validation_error",
                               "manifest khong co run_id")
    digest = sha256_file(manifest) if manifest.is_file() else None
    st = store or open_store()
    return st.add_run(
        website_id, run_id, str(manifest),
        manifest_sha256=digest,
        manifest_size=manifest.stat().st_size if manifest.is_file() else None)


def resolve_run(website_id, run_id, *, store=None) -> Path:
    """Manifest path cua run thuoc website — kiem binding + ton tai + hash.

    - run_id khong biet → scope_violation
    - run thuoc website khac → website_mismatch
    - manifest mat file → file_not_found (retryable — quet lai)
    - hash/binding sai → manifest_mismatch
    Fallback doc file trong `websites/<id>/runs/*.json` theo noi dung
    run_id (du lieu da migrate khi chua co row trong store); KHONG bao gio
    fallback "file moi nhat".
    """
    wid = validate_website_id(website_id)
    if not isinstance(run_id, str) or not run_id.strip():
        raise CommandError("validation_error", "run_id phai la chuoi khong rong")
    run_id = run_id.strip()
    st = store or open_store()
    rec = st.run_for(run_id)
    if rec is not None:
        require_same_website(wid, rec["website_id"])
        path = Path(rec["manifest_path"])
        if not path.is_file():
            raise CommandError(
                "file_not_found",
                f"manifest cua run {run_id} khong con tren dia — quet lai",
                retryable=True)
        expected = rec.get("manifest_sha256")
        if expected and sha256_file(path) != expected:
            raise CommandError(
                "manifest_mismatch",
                f"manifest cua run {run_id} bi thay doi so voi binding")
        return path

    # Fallback: tim file manifest trong runs/ cua website theo noi dung.
    runs_dir = website_data_dir(wid, create=False) / "runs"
    found = None
    if runs_dir.is_dir():
        for candidate in sorted(runs_dir.glob("*.json")):
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if str(data.get("run_id") or "").strip() == run_id:
                found = candidate
                break
    if found is None:
        raise CommandError(
            "scope_violation",
            f"run_id {run_id!r} khong ton tai trong website {wid!r}")
    # Tu bo sung binding de lan sau kiem hash nhat quan.
    st.add_run(wid, run_id, str(found), manifest_sha256=sha256_file(found),
               manifest_size=found.stat().st_size)
    return found


def register_audit(website_id, file_path, *, from_date=None, to_date=None,
                   audit_id=None, store=None) -> dict:
    st = store or open_store()
    audit_id = audit_id or new_id("aud")
    path = Path(file_path)
    return st.add_audit(
        website_id, audit_id, str(path),
        file_sha256=sha256_file(path) if path.is_file() else None,
        from_date=from_date, to_date=to_date)


def resolve_audit(website_id, audit_id, *, store=None) -> dict:
    """Audit record thuoc website; null → None (audit la tuy chon o mot so
    lenh). Sai scope → website_mismatch/scope_violation."""
    wid = validate_website_id(website_id)
    if audit_id is None:
        return None
    if not isinstance(audit_id, str) or not audit_id.strip():
        raise CommandError("validation_error",
                           "audit_id phai la chuoi khong rong hoac null")
    st = store or open_store()
    rec = st.audit_for(audit_id.strip())
    if rec is None:
        raise CommandError(
            "scope_violation",
            f"audit_id {audit_id!r} khong ton tai trong website {wid!r}")
    require_same_website(wid, rec["website_id"])
    return rec


# ---------- workspace read/select (contract §6.2) ----------

def workspace_snapshot(website_id=None, *, store=None) -> dict:
    """Tra shape `upload_workspace` §6.2. website_id None → doc selection."""
    st = store or open_store()
    wid = website_id if website_id is not None else st.selected_website_id()
    if wid is not None:
        wid = validate_website_id(wid)
    snap = st.workspace_snapshot(wid)
    snap["workflow_version"] = "upload.workflow.v1"
    return snap


def select_website(website_id, expected_revision, *, store=None) -> dict:
    """Doi website dang chon (contract §6.2 website_select).

    - expected_revision != revision hien tai → stale_revision
    - website cu con job non-terminal hoac tab cho kiem tra → workflow_busy
    - chon lai dung website dang dung → idempotent, tra snapshot hien tai
    """
    wid = validate_website_id(website_id)
    st = store or open_store()
    current_revision = st.revision()
    if int(expected_revision) != current_revision:
        raise CommandError(
            "stale_revision",
            f"expected_revision {expected_revision} != hien tai "
            f"{current_revision} — doc lai workspace_get",
            retryable=True, next_action="retry")
    current = st.selected_website_id()
    if current == wid:
        return st.workspace_snapshot(wid) | {
            "workflow_version": "upload.workflow.v1"}
    if current:
        busy_jobs = st.active_job_ids(current)
        busy_tabs = st.open_tab_record_ids(current)
        if busy_jobs or busy_tabs:
            raise CommandError(
                "workflow_busy",
                f"website {current} con {len(busy_jobs)} job va "
                f"{len(busy_tabs)} tab cho kiem tra — hoan tat truoc khi doi",
                retryable=True, next_action="retry",
                details={"active_job_ids": busy_jobs,
                         "open_tab_record_ids": busy_tabs})
    st.select_website(wid)
    return st.workspace_snapshot(wid) | {
        "workflow_version": "upload.workflow.v1"}

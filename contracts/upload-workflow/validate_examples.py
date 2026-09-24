"""Validator cho contracts/upload-workflow/examples — stdlib-only, không dep ngoài.

Chạy:  python contracts/upload-workflow/validate_examples.py
Quy tắc: mọi *.valid.json phải pass hết rule; mọi *.invalid.json phải vi phạm
ít nhất một rule VÀ khai báo expected_error khớp code trong contract.

Phạm vi: chỉ ví dụ của luồng `upload.workflow.v1`. Payload không mang
workflow_version literal là legacy — nằm ngoài validator này (xem
contracts/upload-workflow.md §2, §9). Validator **không** nhận diện legacy
path: đưa ví dụ legacy vào đây sẽ bị báo `unsupported_workflow_version` —
đó là hành vi đúng của check v1, không phải lỗi validator.

`fixture` là metadata test (không đi trên wire) mô phỏng binding phía
backend: websites / workspace / browsers / runs / audits / queues /
waiting_jobs / legacy_holds_browser.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
EX = HERE / "examples"

CONTRACT_VERSION = "desktopcommand.v1"
WORKFLOW_VERSION = "upload.workflow.v1"

STATUSES = {"accepted", "running", "waiting_user", "partial",
            "succeeded", "failed", "canceled"}
WAITING_ON = {"login", "review", "finalize", "confirm", None}
NEXT_ACTIONS = {"login_required", "pick_files", "retry", "contact_admin", None}
STAGES = {"prepared", "saved"}
ENV_STATUSES = {"passed", "warning", "blocked"}
LOGIN_STATUSES = {"authenticated", "awaiting_login", "closed", "unknown"}
CAPABILITIES = {"login", "download_export", "audit_excel", "scan",
                "prepare", "staff_options", "reconcile"}

SENSITIVE_KEY = re.compile(
    r"password|passwd|secret|token|credential|cookie|auth|session|"
    r"storage_state|api_key|bearer", re.I)

WEBSITE_ID = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")

ERRORS = {
    "unsupported_contract_version", "unsupported_workflow_version",
    "payload_rejected_sensitive_key", "validation_error",
    "unknown_website", "website_mismatch", "scope_violation",
    "stale_revision", "workflow_busy", "browser_busy", "workflow_conflict",
    "wrong_job", "command_id_conflict", "manifest_mismatch",
    "file_not_found", "file_scope_not_supported", "file_locked",
    "upload.login_not_confirmed", "upload.login_timeout",
    "upload.review_timeout", "upload.partial_failure",
    "engine_unavailable", "engine_restarted", "engine_shutdown",
    "engine_not_installed", "engine_version_mismatch",
    "user_canceled", "job_already_terminal",
}

# Command schema: req = key bắt buộc có mặt; opt = key được phép thêm.
# Nullable riêng từng command bên dưới. workflow_version kiểm riêng.
COMMANDS = {
    "upload.websites": {"req": [], "opt": []},
    "upload.workspace_get": {"req": ["website_id"], "opt": []},
    "upload.website_select": {"req": ["website_id", "expected_revision"],
                              "opt": []},
    "upload.env_check": {"req": ["website_id"], "opt": []},
    "upload.session_start": {"req": ["website_id", "expected_revision"],
                             "opt": []},
    "upload.confirm_login": {"req": ["website_id", "browser_id",
                                     "target_job_id"], "opt": []},
    "upload.session_status": {"req": ["website_id", "browser_id"], "opt": []},
    "upload.session_close": {"req": ["website_id", "browser_id"], "opt": []},
    "upload.download_export": {"req": ["website_id", "browser_id",
                                       "from_date", "to_date"], "opt": []},
    "upload.audit_excel": {"req": ["website_id", "file_ref", "from_date",
                                   "to_date"], "opt": []},
    "upload.scan": {"req": ["website_id", "folder", "expected_revision"],
                    "opt": ["full_rescan", "modified_since"]},
    "upload.queue_get": {"req": ["website_id", "run_id", "audit_id"],
                         "opt": []},
    "upload.staff_options": {"req": ["website_id", "browser_id", "refresh"],
                             "opt": []},
    "upload.preferences": {"req": ["website_id"], "opt": ["values"]},
    "upload.prepare": {"req": ["website_id", "browser_id", "run_id",
                               "audit_id", "queue_revision", "record_ids",
                               "chunk_size", "cong_chung_vien", "thu_ky"],
                       "opt": []},
    "upload.finish_review": {"req": ["website_id", "browser_id",
                                     "target_job_id"], "opt": []},
    "upload.reconcile": {"req": ["website_id", "run_id", "audit_id"],
                         "opt": []},
}

NULLABLE = {
    "upload.workspace_get": {"website_id"},
    "upload.queue_get": {"audit_id"},
    "upload.staff_options": {"browser_id"},
    "upload.prepare": {"audit_id", "cong_chung_vien", "thu_ky"},
    "upload.scan": {"modified_since"},
}

# Command enqueue việc lên browser thread (bị browser_busy / workflow_conflict).
BROWSER_OPS = {"upload.session_start", "upload.download_export",
               "upload.prepare", "upload.staff_options",
               "upload.session_close"}

PREF_KEYS = {"chunk_size", "cong_chung_vien", "thu_ky"}

# Khóa mà "" không được thay null (ID/tham chiếu/datetime/staff).
NO_EMPTY_STRING = {
    "website_id", "browser_id", "run_id", "audit_id", "target_job_id",
    "selected_website_id", "normalized_contract_no", "cong_chung_vien",
    "thu_ky", "modified_since", "fetched_at", "checked_at",
}


def walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path + "/" + str(k), k, v
            yield from walk_keys(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]")


def _is_fileref_dict(d):
    return isinstance(d, dict) and "path" in d and "scope" in d


def _check_fileref(v, path, viols):
    """FileRef theo desktop-command §6; viols += (code, detail)."""
    scope = v.get("scope")
    p = v.get("path")
    if scope != "machine_local":
        viols.append(("file_scope_not_supported", f"{path} scope={scope!r}"))
    if isinstance(p, str):
        if p.startswith("\\\\") and not p.startswith("\\\\?\\"):
            viols.append(("file_scope_not_supported", f"UNC path {path}"))
        elif p.startswith("\\\\?\\"):
            rest = p[len("\\\\?\\"):].lower()
            if rest.startswith(("unc\\", "unc/", "\\\\", "//")):
                viols.append(("file_scope_not_supported", f"UNC ext {path}"))
        elif not re.match(r"^[A-Za-z]:[\\/]", p):
            viols.append(("file_scope_not_supported",
                          f"non-absolute path {path}"))
    else:
        viols.append(("validation_error", f"{path}.path empty/not str"))


def _check_iso_date(val, path, viols, nullable=False):
    if val is None and nullable:
        return
    if not (isinstance(val, str) and ISO_DATE.match(val)):
        viols.append(("validation_error", f"{path} not ISO date: {val!r}"))
        return
    try:
        datetime.strptime(val, "%Y-%m-%d")
    except ValueError:
        viols.append(("validation_error", f"{path} bad date: {val!r}"))


def _check_iso_datetime(val, path, viols, nullable=False):
    if val is None and nullable:
        return
    if not (isinstance(val, str) and ISO_DATETIME.match(val)):
        viols.append(("validation_error",
                      f"{path} not ISO datetime: {val!r}"))


def _nonempty_str(val, path, viols, code="validation_error"):
    if not (isinstance(val, str) and val.strip()):
        viols.append((code, f"{path} empty/not str: {val!r}"))


def _check_rows(data, viols):
    """Kiểm dòng audit (MIN-77) và queue row theo kind đã biết."""
    for sect in ("missing", "issues"):
        for i, row in enumerate(data.get(sect) or []):
            p = f"data.{sect}[{i}]"
            if not isinstance(row, dict):
                viols.append(("validation_error", f"{p} not object"))
                continue
            if not isinstance(row.get("stt"), int):
                viols.append(("validation_error", f"{p}.stt not int"))
            _check_iso_date(row.get("ngay"), f"{p}.ngay", viols,
                            nullable=True)
            if not isinstance(row.get("so_cong_chung"), str):
                viols.append(("validation_error",
                              f"{p}.so_cong_chung not str"))
            if not isinstance(row.get("ghi_chu"), str):
                viols.append(("validation_error", f"{p}.ghi_chu not str"))
    for i, row in enumerate(data.get("folder_rows") or []):
        p = f"data.folder_rows[{i}]"
        if not isinstance(row, dict):
            viols.append(("validation_error", f"{p} not object"))
            continue
        rid = row.get("record_id")
        if not (isinstance(rid, int) and rid >= 1):
            viols.append(("validation_error", f"{p}.record_id bad: {rid!r}"))
        if not isinstance(row.get("contract_no"), str):
            viols.append(("validation_error", f"{p}.contract_no not str"))
        ncn = row.get("normalized_contract_no")
        if ncn is not None:
            _nonempty_str(ncn, f"{p}.normalized_contract_no", viols)
        _check_iso_date(row.get("ngay"), f"{p}.ngay", viols, nullable=True)
        if not isinstance(row.get("ghi_chu"), str):
            viols.append(("validation_error", f"{p}.ghi_chu not str"))
        _nonempty_str(row.get("file_path"), f"{p}.file_path", viols)
        _nonempty_str(row.get("status"), f"{p}.status", viols)
        if not isinstance(row.get("selected"), bool):
            viols.append(("validation_error", f"{p}.selected not bool"))
        if not isinstance(row.get("has_issue"), bool):
            viols.append(("validation_error", f"{p}.has_issue not bool"))
        mf = row.get("missing_fields")
        if not (isinstance(mf, list)
                and all(isinstance(x, str) for x in mf)):
            viols.append(("validation_error", f"{p}.missing_fields bad"))
    for i, row in enumerate(data.get("records") or []):
        p = f"data.records[{i}]"
        if not isinstance(row, dict):
            viols.append(("validation_error", f"{p} not object"))
            continue
        rid = row.get("record_id")
        if not (isinstance(rid, int) and rid >= 1):
            viols.append(("validation_error", f"{p}.record_id bad: {rid!r}"))
        if not isinstance(row.get("contract_no"), str):
            viols.append(("validation_error", f"{p}.contract_no not str"))
        _nonempty_str(row.get("status"), f"{p}.status", viols)
        _nonempty_str(row.get("file_path"), f"{p}.file_path", viols)


def _id_list(v, path, viols, nullable=False):
    if v is None and nullable:
        return
    if not (isinstance(v, list) and all(
            isinstance(x, int) and not isinstance(x, bool) and x >= 1
            for x in v)):
        viols.append(("validation_error", f"{path} not [int>=1]"))


def _str_list(v, path, viols, nullable=False):
    if v is None and nullable:
        return
    if not (isinstance(v, list)
            and all(isinstance(x, str) for x in v)):
        viols.append(("validation_error", f"{path} not [str]"))


def _int_nonneg(v, path, viols, nullable=False):
    if v is None and nullable:
        return
    if not (isinstance(v, int) and not isinstance(v, bool) and v >= 0):
        viols.append(("validation_error", f"{path} not int>=0: {v!r}"))


def _opt_id(v, path, viols):
    if v is not None:
        _nonempty_str(v, path, viols)


def _check_data(kind, data, viols):
    """Kiểm field đặc thù theo result.kind (unknown kind → bỏ qua)."""
    if kind == "website_catalog":
        ws = data.get("websites")
        if not isinstance(ws, list):
            viols.append(("validation_error", "data.websites not list"))
            return
        for i, w in enumerate(ws):
            p = f"data.websites[{i}]"
            if not isinstance(w, dict):
                viols.append(("validation_error", f"{p} not object"))
                continue
            wid = w.get("website_id")
            if not (isinstance(wid, str) and WEBSITE_ID.match(wid)):
                viols.append(("validation_error",
                              f"{p}.website_id bad: {wid!r}"))
            _nonempty_str(w.get("label"), f"{p}.label", viols)
            _nonempty_str(w.get("display_url"), f"{p}.display_url", viols)
            caps = w.get("capabilities")
            if not (isinstance(caps, list)
                    and all(c in CAPABILITIES for c in caps)):
                viols.append(("validation_error",
                              f"{p}.capabilities bad: {caps!r}"))
            if w.get("status") not in {"available", "unavailable"}:
                viols.append(("validation_error",
                              f"{p}.status bad: {w.get('status')!r}"))
        _opt_id(data.get("selected_website_id"),
                "data.selected_website_id", viols)
    elif kind == "upload_workspace":
        wid = data.get("website_id")
        if wid is not None and not (
                isinstance(wid, str) and WEBSITE_ID.match(wid)):
            viols.append(("validation_error",
                          f"data.website_id bad: {wid!r}"))
        _int_nonneg(data.get("revision"), "data.revision", viols)
        for k in ("run_id", "audit_id", "browser_id"):
            _opt_id(data.get(k), f"data.{k}", viols)
        _str_list(data.get("active_job_ids"), "data.active_job_ids", viols)
        _id_list(data.get("needs_reconcile_record_ids"),
                 "data.needs_reconcile_record_ids", viols)
        if "has_excel" in data and not isinstance(
                data["has_excel"], bool):
            viols.append(("validation_error", "data.has_excel not bool"))
        _int_nonneg(data.get("queue_revision"), "data.queue_revision",
                    viols, nullable=True)
    elif kind == "env_check":
        if data.get("status") not in ENV_STATUSES:
            viols.append(("validation_error",
                          f"data.status bad: {data.get('status')!r}"))
        for i, s in enumerate(data.get("steps") or []):
            p = f"data.steps[{i}]"
            if not isinstance(s, dict):
                viols.append(("validation_error", f"{p} not object"))
                continue
            _nonempty_str(s.get("key"), f"{p}.key", viols)
            _nonempty_str(s.get("label"), f"{p}.label", viols)
            if s.get("status") not in ENV_STATUSES:
                viols.append(("validation_error",
                              f"{p}.status bad: {s.get('status')!r}"))
            if not isinstance(s.get("message"), str):
                viols.append(("validation_error", f"{p}.message not str"))
            if "guidance" in s and not isinstance(s["guidance"], str):
                viols.append(("validation_error",
                              f"{p}.guidance not str"))
    elif kind == "session_state":
        _opt_id(data.get("browser_id"), "data.browser_id", viols)
        login = data.get("login")
        if isinstance(login, dict):
            if login.get("status") not in LOGIN_STATUSES:
                viols.append(("validation_error",
                              f"login.status bad: {login.get('status')!r}"))
            _check_iso_datetime(login.get("checked_at"),
                                "login.checked_at", viols, nullable=True)
        tabs = data.get("tabs")
        if isinstance(tabs, dict):
            for k in ("open_record_ids", "saved_record_ids",
                      "closed_record_ids", "unknown_record_ids"):
                if k in tabs:
                    _id_list(tabs[k], f"tabs.{k}", viols)
        for k in ("verified_record_ids", "needs_reconcile_record_ids"):
            if k in data:
                _id_list(data[k], f"data.{k}", viols)
    elif kind == "export_download":
        for k in ("from_date", "to_date"):
            if k in data:
                _check_iso_date(data[k], f"data.{k}", viols)
    elif kind == "audit_report":
        _opt_id(data.get("audit_id"), "data.audit_id", viols)
        for k in ("from_date", "to_date"):
            if k in data:
                _check_iso_date(data[k], f"data.{k}", viols)
        summ = data.get("summary")
        if isinstance(summ, dict):
            for k in ("excel_total", "valid_count", "missing_count",
                      "issue_count", "duplicate_count"):
                if k in summ:
                    _int_nonneg(summ[k], f"summary.{k}", viols)
    elif kind == "scan_report":
        _nonempty_str(data.get("run_id"), "data.run_id", viols)
        _int_nonneg(data.get("revision"), "data.revision", viols,
                    nullable=True)
    elif kind == "upload_queue":
        _nonempty_str(data.get("run_id"), "data.run_id", viols)
        _opt_id(data.get("audit_id"), "data.audit_id", viols)
        _int_nonneg(data.get("queue_revision"), "data.queue_revision",
                    viols)
        if "has_excel" in data and not isinstance(
                data["has_excel"], bool):
            viols.append(("validation_error", "data.has_excel not bool"))
        _id_list(data.get("missing_in_excel_record_ids"),
                 "data.missing_in_excel_record_ids", viols)
    elif kind == "staff_options":
        _str_list(data.get("cong_chung_vien"), "data.cong_chung_vien",
                  viols)
        if data.get("source") not in {"portal", "cache", None}:
            viols.append(("validation_error",
                          f"data.source bad: {data.get('source')!r}"))
        _check_iso_datetime(data.get("fetched_at"), "data.fetched_at",
                            viols, nullable=True)
    elif kind == "preferences":
        cs = data.get("chunk_size")
        if not (isinstance(cs, int) and not isinstance(cs, bool)
                and 1 <= cs <= 30):
            viols.append(("validation_error",
                          f"data.chunk_size out of 1-30: {cs!r}"))
        for k in ("cong_chung_vien", "thu_ky"):
            _opt_id(data.get(k), f"data.{k}", viols)
    elif kind == "upload_prepare":
        _opt_id(data.get("browser_id"), "data.browser_id", viols)
        _opt_id(data.get("run_id"), "data.run_id", viols)
        _opt_id(data.get("audit_id"), "data.audit_id", viols)
        summ = data.get("summary")
        if isinstance(summ, dict):
            for k in ("total_requested", "prepared_count", "remaining"):
                if k in summ:
                    _int_nonneg(summ[k], f"summary.{k}", viols)
            _id_list(summ.get("open_record_ids"),
                     "summary.open_record_ids", viols, nullable=True)
        for k in ("saved_record_ids", "needs_reconcile_record_ids"):
            if k in data:
                _id_list(data[k], f"data.{k}", viols)
    elif kind == "reconcile_report":
        _nonempty_str(data.get("run_id"), "data.run_id", viols)
        _opt_id(data.get("audit_id"), "data.audit_id", viols)
        for k in ("verified_record_ids", "needs_reconcile_record_ids"):
            if k in data:
                _id_list(data[k], f"data.{k}", viols)


def _check_breakdown(bd, viols):
    if not isinstance(bd, dict) or "succeeded" not in bd or "failed" not in bd:
        viols.append(("validation_error", "partial without breakdown"))
        return
    for sect in ("succeeded", "failed"):
        items = bd.get(sect)
        if not isinstance(items, list):
            viols.append(("validation_error", f"breakdown.{sect} not list"))
            continue
        for i, it in enumerate(items):
            p = f"breakdown.{sect}[{i}]"
            if not isinstance(it, dict):
                viols.append(("validation_error", f"{p} not object"))
                continue
            rid = it.get("record_id")
            if not (isinstance(rid, int) and rid >= 1):
                viols.append(("validation_error",
                              f"{p}.record_id bad: {rid!r}"))
            if it.get("stage") not in STAGES:
                viols.append(("validation_error",
                              f"{p}.stage bad: {it.get('stage')!r}"))
            if sect == "failed":
                _nonempty_str(it.get("code"), f"{p}.code", viols)
                if "message" in it and not isinstance(it["message"], str):
                    viols.append(("validation_error",
                                  f"{p}.message not str"))


def _check_error(err, viols):
    for k in ("code", "message", "retryable", "next_action", "job_id"):
        if k not in err:
            viols.append(("validation_error", f"error.{k} missing"))
    code = err.get("code")
    if code is not None and code not in ERRORS:
        viols.append(("validation_error", f"error.code unknown: {code!r}"))
    if err.get("next_action") not in NEXT_ACTIONS:
        viols.append(("validation_error",
                      f"next_action bad: {err.get('next_action')!r}"))


def _check_command(doc, viols):
    """Kiểm request envelope + payload schema + fixture scope."""
    if doc.get("contract_version") != CONTRACT_VERSION:
        viols.append(("unsupported_contract_version",
                      f"contract_version={doc.get('contract_version')!r}"))
    _nonempty_str(doc.get("command_id"), "command_id", viols)
    cmd = doc.get("command")
    spec = COMMANDS.get(cmd)
    if spec is None:
        viols.append(("validation_error", f"unknown command: {cmd!r}"))
        return
    payload = doc.get("payload")
    if not isinstance(payload, dict):
        viols.append(("validation_error", "payload not object"))
        return
    meta = doc.get("client_meta")
    if not isinstance(meta, dict) or not meta.get("module"):
        viols.append(("validation_error", "client_meta missing/module"))

    if payload.get("workflow_version") != WORKFLOW_VERSION:
        viols.append(("unsupported_workflow_version",
                      f"workflow_version={payload.get('workflow_version')!r}"))

    allowed = set(spec["req"]) | set(spec["opt"]) | {"workflow_version"}
    nullable = NULLABLE.get(cmd, set())
    for k in spec["req"]:
        if k not in payload:
            viols.append(("validation_error", f"payload.{k} missing"))
    for k in payload:
        if k not in allowed:
            viols.append(("validation_error", f"payload.{k} unexpected"))

    # Kiểu từng trường
    wid = payload.get("website_id")
    if "website_id" in payload:
        if wid is None:
            if "website_id" not in nullable:
                viols.append(("validation_error", "website_id null"))
        elif not (isinstance(wid, str) and WEBSITE_ID.match(wid)):
            viols.append(("validation_error", f"website_id bad: {wid!r}"))
    for k in ("browser_id", "run_id", "audit_id", "target_job_id"):
        if k in payload:
            v = payload[k]
            if v is None:
                if k not in nullable:
                    viols.append(("validation_error", f"{k} null"))
            else:
                _nonempty_str(v, f"payload.{k}", viols)
    for k in ("expected_revision", "queue_revision"):
        if k in payload:
            v = payload[k]
            if not (isinstance(v, int) and not isinstance(v, bool) and v >= 0):
                viols.append(("validation_error",
                              f"{k} not int>=0: {v!r}"))
    if "record_ids" in payload:
        v = payload["record_ids"]
        ok = (isinstance(v, list) and v
              and all(isinstance(x, int) and not isinstance(x, bool)
                      and x >= 1 for x in v)
              and len(set(v)) == len(v))
        if not ok:
            viols.append(("validation_error", f"record_ids bad: {v!r}"))
    if "chunk_size" in payload:
        v = payload["chunk_size"]
        if not (isinstance(v, int) and not isinstance(v, bool)
                and 1 <= v <= 30):
            viols.append(("validation_error",
                          f"chunk_size out of 1-30: {v!r}"))
    for k in ("from_date", "to_date"):
        if k in payload:
            _check_iso_date(payload[k], f"payload.{k}", viols)
    if "modified_since" in payload and payload["modified_since"] is not None:
        _check_iso_date(payload["modified_since"],
                        "payload.modified_since", viols)
    for k in ("refresh", "full_rescan"):
        if k in payload and not isinstance(payload[k], bool):
            viols.append(("validation_error", f"{k} not bool"))
    for k in ("cong_chung_vien", "thu_ky"):
        if k in payload:
            v = payload[k]
            if v is not None:
                _nonempty_str(v, f"payload.{k}", viols)
    if "values" in payload:
        v = payload["values"]
        if not isinstance(v, dict):
            viols.append(("validation_error", "values not object"))
        else:
            for kk in v:
                if kk not in PREF_KEYS:
                    viols.append(("validation_error",
                                  f"values.{kk} unexpected"))
            cs = v.get("chunk_size")
            if cs is not None and not (
                    isinstance(cs, int) and not isinstance(cs, bool)
                    and 1 <= cs <= 30):
                viols.append(("validation_error",
                              f"values.chunk_size out of 1-30: {cs!r}"))
            for kk in ("cong_chung_vien", "thu_ky"):
                vv = v.get(kk)
                if vv is not None and not (
                        isinstance(vv, str) and vv.strip()):
                    viols.append(("validation_error",
                                  f"values.{kk} bad: {vv!r}"))
    if cmd == "upload.staff_options" and payload.get("refresh") is True \
            and not payload.get("browser_id"):
        viols.append(("validation_error",
                      "refresh=true requires browser_id"))
    if cmd == "upload.audit_excel":
        fr = payload.get("file_ref")
        if isinstance(fr, dict) and isinstance(fr.get("path"), str):
            if not fr["path"].lower().endswith((".xlsx", ".xlsm")):
                viols.append(("validation_error",
                              "file_ref phai la file .xlsx/.xlsm"))

    # ---- fixture scope simulation ----
    fx = doc.get("fixture") or {}
    websites = fx.get("websites") or ["nam_dinh"]
    ws = fx.get("workspace") or {}
    browsers = fx.get("browsers") or {}
    runs = fx.get("runs") or {}
    audits = fx.get("audits") or {}
    queues = fx.get("queues") or {}
    waiting_jobs = fx.get("waiting_jobs") or {}

    if wid is not None and wid not in websites:
        viols.append(("unknown_website", f"website_id {wid!r}"))

    bid = payload.get("browser_id")
    if bid is not None:
        b = browsers.get(bid)
        if b is None:
            viols.append(("scope_violation", f"browser {bid!r} not in scope"))
        else:
            if wid is not None and b.get("website_id") != wid:
                viols.append(("website_mismatch",
                              f"browser {bid!r} belongs to "
                              f"{b.get('website_id')!r}"))
            elif b.get("busy_with") and cmd in BROWSER_OPS:
                viols.append(("browser_busy",
                              f"browser {bid!r} busy_with "
                              f"{b['busy_with']!r}"))

    rid = payload.get("run_id")
    if rid is not None:
        r = runs.get(rid)
        if r is None:
            viols.append(("scope_violation", f"run {rid!r} not in scope"))
        else:
            if wid is not None and r.get("website_id") != wid:
                viols.append(("website_mismatch",
                              f"run {rid!r} belongs to "
                              f"{r.get('website_id')!r}"))
            else:
                if r.get("manifest_exists") is False:
                    viols.append(("file_not_found",
                                  f"manifest of {rid!r} missing"))
                elif r.get("manifest_ok") is False:
                    viols.append(("manifest_mismatch",
                                  f"manifest of {rid!r} bad hash/binding"))
                known = r.get("record_ids") or []
                for rec in payload.get("record_ids") or []:
                    if rec not in known:
                        viols.append(("scope_violation",
                                      f"record_id {rec} not in {rid!r}"))
                        break
                if "queue_revision" in payload:
                    qr = (queues.get(rid) or {}).get("queue_revision")
                    if qr is not None and payload["queue_revision"] != qr:
                        viols.append(("stale_revision",
                                      f"queue_revision "
                                      f"{payload['queue_revision']} != {qr}"))

    aid = payload.get("audit_id")
    if aid is not None:
        a = audits.get(aid)
        if a is None:
            viols.append(("scope_violation", f"audit {aid!r} not in scope"))
        elif wid is not None and a.get("website_id") != wid:
            viols.append(("website_mismatch",
                          f"audit {aid!r} belongs to "
                          f"{a.get('website_id')!r}"))

    if "expected_revision" in payload:
        cur = ws.get("revision", 0)
        if payload["expected_revision"] != cur:
            viols.append(("stale_revision",
                          f"expected_revision "
                          f"{payload['expected_revision']} != {cur}"))

    if cmd == "upload.website_select" and wid is not None:
        busy = (ws.get("active_job_ids") or ws.get("open_tab_record_ids"))
        if wid != ws.get("website_id") and busy:
            viols.append(("workflow_busy",
                          "website cu con job/tab dang cho"))

    tj = payload.get("target_job_id")
    if tj is not None:
        j = waiting_jobs.get(tj)
        need = ("login" if cmd == "upload.confirm_login"
                else "review" if cmd == "upload.finish_review" else None)
        if j is None:
            viols.append(("wrong_job", f"target_job {tj!r} not waiting"))
        elif need and (j.get("waiting_on") != need
                       or (wid is not None and j.get("website_id") != wid)
                       or (bid is not None and j.get("browser_id") != bid)):
            viols.append(("wrong_job",
                          f"target_job {tj!r} wrong step/scope"))

    if cmd in BROWSER_OPS and fx.get("legacy_holds_browser"):
        viols.append(("workflow_conflict", "legacy flow holds browser"))


def _check_job(doc, viols):
    """Kiểm job document theo desktop-command §4 + workflow rules."""
    if doc.get("contract_version") != CONTRACT_VERSION:
        viols.append(("unsupported_contract_version",
                      f"contract_version={doc.get('contract_version')!r}"))
    for k in ("job_id", "command_id", "status", "waiting_on", "progress",
              "result", "error", "updated_at"):
        if k not in doc:
            viols.append(("validation_error", f"job.{k} missing"))
    _nonempty_str(doc.get("job_id"), "job_id", viols)
    _nonempty_str(doc.get("command_id"), "command_id", viols)
    _check_iso_datetime(doc.get("updated_at"), "updated_at", viols)

    status = doc.get("status")
    if status not in STATUSES:
        viols.append(("validation_error", f"status={status!r}"))
    if doc.get("waiting_on") not in WAITING_ON:
        viols.append(("validation_error",
                      f"waiting_on={doc.get('waiting_on')!r}"))
    if status == "waiting_user" and not doc.get("waiting_on"):
        viols.append(("validation_error", "waiting_user without waiting_on"))
    if status in ("failed", "canceled") and not doc.get("error"):
        viols.append(("validation_error", "failed/canceled without error"))

    prog = doc.get("progress")
    if prog is not None:
        if not isinstance(prog, dict) or not isinstance(
                prog.get("done"), int) or not isinstance(
                prog.get("total"), int):
            viols.append(("validation_error", "progress bad shape"))

    err = doc.get("error")
    if err is not None:
        if not isinstance(err, dict):
            viols.append(("validation_error", "error not object"))
        else:
            _check_error(err, viols)

    res = doc.get("result")
    if res is not None:
        if not isinstance(res, dict):
            viols.append(("validation_error", "result not object"))
        else:
            _nonempty_str(res.get("kind"), "result.kind", viols)
            data = res.get("data")
            if not isinstance(data, dict):
                viols.append(("validation_error", "result.data not object"))
                data = None
            if data is not None:
                if data.get("workflow_version") != WORKFLOW_VERSION:
                    viols.append((
                        "unsupported_workflow_version",
                        f"data.workflow_version="
                        f"{data.get('workflow_version')!r}"))
                _check_rows(data, viols)
                _check_data(res.get("kind"), data, viols)
                if "breakdown" in data:
                    _check_breakdown(data["breakdown"], viols)
            warns = res.get("warnings")
            if warns is not None:
                if not isinstance(warns, list):
                    viols.append(("validation_error",
                                  "warnings not list"))
                else:
                    for i, w in enumerate(warns):
                        if not isinstance(w, dict) or not w.get("code") \
                                or not isinstance(w.get("message"), str):
                            viols.append(("validation_error",
                                          f"warnings[{i}] bad"))
    if status == "partial":
        bd = (res or {}).get("data", {}).get("breakdown") \
            if isinstance(res, dict) else None
        _check_breakdown(bd, viols)
        # Contract §6.14: job partial bat buoc kem
        # error.code == "upload.partial_failure".
        err2 = doc.get("error")
        if not isinstance(err2, dict) or \
                err2.get("code") != "upload.partial_failure":
            viols.append(("validation_error",
                          "partial requires error.code "
                          "upload.partial_failure"))


def violations(doc):
    v = []
    # Sensitive-key scan + FileRef trên TOÀN tài liệu (kể cả fixture —
    # ví dụ cũng không được chứa credential).
    for path, k, val in walk_keys(doc):
        if SENSITIVE_KEY.search(str(k)):
            v.append(("payload_rejected_sensitive_key", f"key {path}"))
    for path, k, val in walk_keys(doc):
        named = k in ("file_ref", "manifest_ref", "folder")
        if named or _is_fileref_dict(val):
            if not isinstance(val, dict):
                v.append(("validation_error", f"{path} not object"))
                continue
            missing = [f for f in ("path", "scope") if f not in val]
            if missing:
                v.append(("validation_error",
                          f"{path} missing {missing}"))
            else:
                _check_fileref(val, path, v)
    for path, k, val in walk_keys(doc):
        if k in NO_EMPTY_STRING and val == "":
            v.append(("validation_error", f"{path} empty-string-as-null"))

    if "command" in doc and "payload" in doc:
        _check_command(doc, v)
    elif "job_id" in doc or "status" in doc:
        _check_job(doc, v)
    else:
        v.append(("validation_error", "not a command or job document"))
    return v


def main():
    files = sorted(EX.glob("*.json"))
    if not files:
        print("no examples found")
        return 1
    bad = 0
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        viols = violations(doc)
        name = f.name
        if ".invalid." in name:
            exp = doc.get("expected_error")
            ok = bool(viols) and exp in ERRORS and any(
                c == exp for c, _ in viols)
            status = "REJECTED-CORRECTLY" if ok \
                else "!! NOT REJECTED AS EXPECTED"
            print(f"[invalid] {name}: expected={exp} "
                  f"got={[c for c, _ in viols]} -> {status}")
        else:
            ok = not viols
            print(f"[valid]   {name}: violations={viols} -> "
                  f"{'PASS' if ok else '!! FAIL'}")
        bad += 0 if ok else 1
    print(f"\n{len(files)} files, {bad} unexpected outcomes")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

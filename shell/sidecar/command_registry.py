"""Command registry — handler nghiep vu cho desktopcommand.v1.

P4 co read-only command goi engine that (file.inspect). P5 them diagnostic
command de kiem chung waiting_user/resume/env-check end-to-end tu shell.
Business commands cua upload_lab/notary_v2 duoc them o P6 theo dung
namespace da duyet.
"""
import hashlib
import importlib.util
import mimetypes
import platform
import time

from errors import CommandError
from fileref import existing_file

PREVIEW_LIMIT = 2000

_MEDIA_BY_SUFFIX = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".pdf": "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _preview(path):
    """Tra (text, warnings). Engine that: python-docx / PyMuPDF / plain read."""
    ext = path.suffix.lower()
    warnings = []
    try:
        if ext == ".docx":
            import docx
            doc = docx.Document(str(path))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return text, warnings
        if ext == ".pdf":
            import pymupdf
            with pymupdf.open(str(path)) as pdf:
                text = "\n".join(page.get_text() for page in pdf[:3])
            if not text.strip():
                warnings.append({"code": "ocr_required",
                                 "message": "PDF khong co text — can OCR gate"})
            return text, warnings
        if ext in (".txt", ".md"):
            return path.read_text(encoding="utf-8", errors="replace"), warnings
        warnings.append({"code": "preview_unsupported",
                         "message": f"chua co preview cho {ext or 'unknown'}"})
        return "", warnings
    except PermissionError as exc:
        raise CommandError("file_locked", f"file dang bi khoa: {path.name}",
                           retryable=True) from exc
    except CommandError:
        raise
    except Exception as exc:  # doc loi dinh dang — bao structured, khong crash
        raise CommandError("extraction_failed",
                           f"{type(exc).__name__}: {exc}",
                           retryable=False) from exc


def inspect_file(job, payload):
    ref = payload.get("file") if isinstance(payload, dict) else None
    path = existing_file(ref)
    job.check_cancel()
    job.report_progress(0, 2, "doc file")
    stat = path.stat()
    digest = _sha256(path)
    job.report_progress(1, 2, "trich preview")
    text, warnings = _preview(path)
    truncated = len(text) > PREVIEW_LIMIT
    return {
        "kind": "file_inspect",
        "data": {
            "size_bytes": stat.st_size,
            "sha256": digest,
            "media_type": _MEDIA_BY_SUFFIX.get(
                path.suffix.lower(),
                mimetypes.guess_type(path.name)[0] or "application/octet-stream"),
            "text_preview": text[:PREVIEW_LIMIT],
            "preview_truncated": truncated,
        },
        "evidence": [],
        "warnings": warnings,
        "source_files": [{"path": str(path), "scope": "machine_local"}],
    }


def slow_task(job, payload):
    """Diagnostic command: progress + cancel + waiting semantics end-to-end."""
    steps = 10
    if isinstance(payload, dict) and payload.get("steps") is not None:
        steps = max(1, min(int(payload["steps"]), 100))
    for i in range(steps):
        job.check_cancel()
        job.report_progress(i, steps, f"buoc {i + 1}/{steps}")
        time.sleep(0.15)
    return {"kind": "diag_result", "data": {"steps": steps},
            "evidence": [], "warnings": []}


def waiting_task(job, payload):
    """Diagnostic: vao waiting_user(review) roi tu resume sau wait_seconds.

    Kiem chung banner waiting_user + cancel-khi-waiting + resume tu shell ma
    khong can luong nghiep vu that (P5). Cancel ap dung ngay luc waiting.
    """
    wait = 20.0
    if isinstance(payload, dict) and payload.get("wait_seconds") is not None:
        try:
            wait = max(1.0, min(float(payload["wait_seconds"]), 120.0))
        except (TypeError, ValueError) as exc:
            raise CommandError("validation_error",
                               "wait_seconds phai la so") from exc
    job.set_waiting("review")
    deadline = time.time() + wait
    while time.time() < deadline:
        job.check_cancel()
        time.sleep(0.1)
    job.resume()
    job.report_progress(1, 1, "buoc nguoi dung da xong")
    return {"kind": "diag_result", "data": {"waited_seconds": wait},
            "evidence": [], "warnings": []}


def env_check(job, payload):
    """Diagnostic: checklist moi truong engine (MIN-32 §6 — env service)."""
    job.report_progress(0, 1, "doc moi truong")
    checks = [{"name": "python", "ok": True,
               "detail": platform.python_version()}]
    for mod in ("fastapi", "uvicorn", "docx", "pymupdf"):
        found = importlib.util.find_spec(mod) is not None
        checks.append({"name": mod, "ok": found,
                       "detail": "co san" if found else "thieu"})
    # playwright optional trong G1-SM (finding F5 chua do) — thieu la warning,
    # khong lam env fail.
    pw = importlib.util.find_spec("playwright") is not None
    checks.append({"name": "playwright", "ok": pw,
                   "detail": "co san" if pw else "chua cai (optional G1-SM)"})
    job.check_cancel()
    job.report_progress(1, 1, "xong")
    required_ok = all(c["ok"] for c in checks if c["name"] != "playwright")
    return {
        "kind": "env_check",
        "data": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "checks": checks,
            "required_ok": required_ok,
        },
        "evidence": [],
        "warnings": ([] if pw else [{
            "code": "playwright_missing",
            "message": "playwright chua cai — upload login/finalize se can"}]),
    }


# Business commands (P6 — MIN-68 notary_v2, MIN-69 upload_lab). Adapter import
# lazy trong handler → thieu engine root chi lam command do loi
# engine_not_installed, khong gay sap sidecar.
def _notary(fn_name):
    def call(job, payload):
        import notary_adapter
        return getattr(notary_adapter, fn_name)(job, payload)
    return call


def _upload(fn_name):
    def call(job, payload):
        import upload_adapter
        return getattr(upload_adapter, fn_name)(job, payload)
    return call


COMMANDS = {
    "file.inspect": inspect_file,
    "diag.slow_task": slow_task,
    "diag.waiting_task": waiting_task,
    "diag.env_check": env_check,
    # notary_v2 (document-review module) — MIN-68
    "notary.case_list": _notary("case_list"),
    "notary.case_get": _notary("case_get"),
    "notary.case_create": _notary("case_create"),
    "notary.customer_list": _notary("customer_list"),
    "notary.customer_create": _notary("customer_create"),
    "notary.property_list": _notary("property_list"),
    "notary.property_create": _notary("property_create"),
    "notary.participant_add": _notary("participant_add"),
    "notary.word_templates": _notary("word_templates"),
    "notary.export_word": _notary("export_word"),
    "ocr.analyze": _notary("ocr_analyze"),
    "zalo.status": _notary("zalo_status"),
    # upload_lab — MIN-69
    "upload.scan": _upload("scan_folder"),
    "upload.audit_excel": _upload("audit_excel"),
    "upload.env_check": _upload("env_check"),
    "upload.session_start": _upload("session_start"),
    "upload.session_status": _upload("session_status"),
    "upload.confirm_login": _upload("confirm_login"),
    "upload.session_close": _upload("session_close"),
    "upload.download_export": _upload("download_export"),
    "upload.prepare": _upload("prepare_upload"),
    "upload.finish_review": _upload("finish_review"),
    # notary_v2 case workspace — MIN-107 (notary.case-drafting.v1)
    "notary.workspace_get": _notary("workspace_get"),
    "notary.workspace_commit_stage": _notary("workspace_commit_stage"),
}

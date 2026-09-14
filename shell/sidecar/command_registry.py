"""Command registry — handler nghiep vu cho desktopcommand.v1.

P4 chi co read-only command goi engine that (file.inspect) + mot diagnostic
command de kiem chung progress/cancel end-to-end. Business commands cua
upload_lab/notary_v2 duoc them o P6 theo dung namespace da duyet.
"""
import hashlib
import mimetypes
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


COMMANDS = {
    "file.inspect": inspect_file,
    "diag.slow_task": slow_task,
}

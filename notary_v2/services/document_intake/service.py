"""Multi-source document intake orchestration (notary.case-drafting.v1).

Luồng: validate sources (shape + limits §5.2) → dispatch adapter theo kind →
gom suggestions + per-source errors → status succeeded|partial|failed.

Contract invariants giữ ở đây:
- Một source fail không hủy kết quả source khác (SourceFailed → errors[]).
- Job-level violations (limits, malformed) → IntakeError với code §9.
- Telemetry chỉ chứa source_id/kind/status/ms/code — không filename, không
  raw text, không PII.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Optional

import httpx

from . import ocr_pipeline
from .adapters import docx, excel, image_ocr, pdf, text
from .models import (
    AdapterContext,
    IntakeCancelled,
    IntakeError,
    IntakeOutcome,
    MAX_FILE_BYTES,
    MAX_SOURCES,
    MAX_TEXT_CHARS,
    SOURCE_KINDS,
    SourceFailed,
    SourceSpec,
    make_source_error,
)

_logger = logging.getLogger("document_intake")

_ABS_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")
_LONG_PREFIX = "\\\\?\\"
_UUID4_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
_SOURCE_KEYS = {"source_id", "kind", "file_ref", "text"}
_FILEREF_KEYS = {"path", "scope", "is_dir", "sha256", "media_type", "size_bytes"}


def _log(event: str, **fields: Any) -> None:
    """Telemetry không PII: chỉ source_id/kind/status/ms/code."""
    payload = {"event": event, **fields}
    try:
        _logger.info("document_intake %s", json.dumps(payload, ensure_ascii=False, default=str))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Source validation (job-level → IntakeError)
# ---------------------------------------------------------------------------


def _is_unc(path: str) -> bool:
    if path.startswith(_LONG_PREFIX):
        rest = path[len(_LONG_PREFIX):]
        low = rest.lower()
        return (
            low.startswith("unc\\")
            or low.startswith("unc/")
            or rest.startswith("\\\\")
            or rest.startswith("//")
        )
    return path.startswith("\\\\") or path.startswith("//")


def _is_abs(path: str) -> bool:
    return path.startswith(_LONG_PREFIX) or bool(_ABS_DRIVE.match(path))


def _validate_sources(sources: Any) -> list[SourceSpec]:
    if not isinstance(sources, list) or not sources:
        raise IntakeError("validation_error", "cần sources: [..]")
    if len(sources) > MAX_SOURCES:
        raise IntakeError(
            "intake_too_many_sources",
            f"tối đa {MAX_SOURCES} nguồn/lần",
            details={"count": len(sources), "limit": MAX_SOURCES},
        )
    specs: list[SourceSpec] = []
    seen_ids: set[str] = set()
    for raw in sources:
        if not isinstance(raw, dict):
            raise IntakeError("validation_error", "source phải là object")
        extra = set(raw) - _SOURCE_KEYS
        if extra:
            raise IntakeError(
                "validation_error",
                f"source có key ngoài schema: {sorted(extra)}")
        sid = str(raw.get("source_id") or "").strip()
        if not sid:
            raise IntakeError("validation_error", "source thiếu source_id")
        if not _UUID4_RE.match(sid):
            raise IntakeError(
                "validation_error", f"source_id phải là uuid4: {sid!r}")
        if sid in seen_ids:
            raise IntakeError("validation_error", f"source_id trùng: {sid}")
        seen_ids.add(sid)
        kind = str(raw.get("kind") or "").strip()
        if kind not in SOURCE_KINDS:
            raise IntakeError(
                "intake_unsupported_source",
                f"kind không hỗ trợ: {kind or '<empty>'}",
                details={"source_id": sid, "kind": kind},
            )
        if kind == "text":
            specs.append(_validate_text_source(raw, sid))
        else:
            specs.append(_validate_file_source(raw, sid, kind))
    return specs


def _validate_text_source(raw: dict, sid: str) -> SourceSpec:
    # Schema: kind=text → bắt buộc key `text`, cấm key `file_ref` (kể cả null).
    if "file_ref" in raw:
        raise IntakeError(
            "validation_error", f"source {sid}: kind=text không nhận file_ref")
    if "text" not in raw:
        raise IntakeError("validation_error", f"source {sid}: thiếu text")
    content = raw.get("text")
    if not isinstance(content, str) or not content.strip():
        raise IntakeError("validation_error", f"source {sid}: text rỗng")
    if len(content) > MAX_TEXT_CHARS:
        raise IntakeError(
            "intake_text_too_long",
            f"text vượt {MAX_TEXT_CHARS} ký tự",
            details={"source_id": sid, "length": len(content), "limit": MAX_TEXT_CHARS},
        )
    return SourceSpec(source_id=sid, kind="text", text=content, filename="<text>")


def _validate_file_source(raw: dict, sid: str, kind: str) -> SourceSpec:
    # Schema: kind=file → bắt buộc key `file_ref`, cấm key `text` (kể cả null).
    if "text" in raw:
        raise IntakeError(
            "validation_error", f"source {sid}: kind={kind} không nhận text")
    ref = raw.get("file_ref")
    if not isinstance(ref, dict):
        raise IntakeError("validation_error", f"source {sid}: thiếu file_ref")
    extra = set(ref) - _FILEREF_KEYS
    if extra:
        raise IntakeError(
            "validation_error",
            f"source {sid}: file_ref có key ngoài schema: {sorted(extra)}")
    if "is_dir" in ref and ref["is_dir"] is not False:
        raise IntakeError(
            "validation_error", f"source {sid}: file_ref.is_dir phải absent/false")
    scope = ref.get("scope")
    if scope != "machine_local":
        raise IntakeError(
            "file_scope_not_supported",
            f"scope={scope!r}: chỉ chấp nhận machine_local")
    path = ref.get("path")
    if not isinstance(path, str) or not path.strip():
        raise IntakeError("validation_error", f"source {sid}: file_ref.path rỗng")
    if _is_unc(path):
        raise IntakeError("file_scope_not_supported", "UNC path bị từ chối (một máy)")
    if not _is_abs(path):
        raise IntakeError("file_scope_not_supported", "path không tuyệt đối")
    size = ref.get("size_bytes")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise IntakeError(
            "validation_error",
            f"source {sid}: file_ref.size_bytes bắt buộc (int ≥ 0)")
    if size > MAX_FILE_BYTES:
        raise IntakeError(
            "intake_source_too_large",
            f"file vượt {MAX_FILE_BYTES} bytes",
            details={"source_id": sid, "size_bytes": size, "limit": MAX_FILE_BYTES},
        )
    filename = Path(path[len(_LONG_PREFIX):] if path.startswith(_LONG_PREFIX) else path).name or path
    return SourceSpec(
        source_id=sid, kind=kind, path=path, filename=filename, declared_size=size)


# ---------------------------------------------------------------------------
# File reading (mọi lỗi phát hiện lúc đọc → per-source SourceFailed)
# ---------------------------------------------------------------------------


def _default_read_file(spec: SourceSpec) -> bytes:
    p = Path(str(spec.path))
    try:
        if not p.exists():
            raise SourceFailed("file_not_found", f"không tìm thấy: {p.name}")
        if not p.is_file():
            raise SourceFailed("file_not_found", f"không phải file: {p.name}")
        size = p.stat().st_size
        if size > MAX_FILE_BYTES:
            # Khai báo size_bytes nhỏ nhưng file thật lớn → lỗi per-source,
            # không hủy cả batch (stat trước read nên không đọc file > limit).
            raise SourceFailed(
                "intake_source_too_large",
                f"file thực tế vượt {MAX_FILE_BYTES} bytes")
        return p.read_bytes()
    except PermissionError as exc:
        raise SourceFailed("file_locked", f"file đang bị khóa: {p.name}") from exc


_ADAPTERS = {
    "image": image_ocr.extract,
    "pdf": pdf.extract,
    "docx": docx.extract,
    "xlsx": excel.extract,
    "text": text.extract,
}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


async def analyze_async(
    sources: Any,
    *,
    check_cancel: Optional[Callable[[], None]] = None,
    report_progress: Optional[Callable[[int, int, str], None]] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    ocr_call: Optional[Callable] = None,
    read_file: Optional[Callable[[SourceSpec], bytes]] = None,
) -> IntakeOutcome:
    """Analyze một batch intake sources → IntakeOutcome (contract data).

    - api_key=None → resolve từ env/.env; truyền "" để ép thiếu key (tests).
    - ocr_call injectable cho tests (async fn → list[str] lines).
    - check_cancel gọi giữa các source và (trong adapter) giữa các trang.
    """
    specs = _validate_sources(sources)
    resolved_key = ocr_pipeline._get_api_key() if api_key is None else api_key
    resolved_model = model or ocr_pipeline._get_model()
    reader = read_file or _default_read_file
    outcome = IntakeOutcome(status="succeeded")

    def _cancel():
        if check_cancel is not None:
            try:
                check_cancel()
            except IntakeCancelled:
                raise
            except Exception as exc:
                raise IntakeCancelled(exc) from exc

    async with httpx.AsyncClient(timeout=ocr_pipeline.AI_TIMEOUT_SECONDS) as client:
        ctx = AdapterContext(
            api_key=resolved_key,
            model=resolved_model,
            client=client,
            semaphore=asyncio.Semaphore(ocr_pipeline.OCR_AI_CONCURRENCY),
            ocr_call=ocr_call,
            check_cancel=check_cancel,
            read_file=reader,
        )
        total = len(specs)
        try:
            for idx, spec in enumerate(specs):
                _cancel()
                t0 = perf_counter()
                try:
                    suggestions = await _ADAPTERS[spec.kind](spec, ctx)
                    outcome.suggestions.extend(suggestions)
                    outcome.succeeded.append(spec.source_id)
                    _log(
                        "intake_source",
                        source_id=spec.source_id,
                        kind=spec.kind,
                        status="ok",
                        ms=round((perf_counter() - t0) * 1000, 2),
                        suggestions=len(suggestions),
                    )
                except IntakeCancelled:
                    raise
                except IntakeError:
                    raise
                except SourceFailed as exc:
                    outcome.errors.append(
                        make_source_error(
                            source_id=spec.source_id,
                            code=exc.code,
                            message=exc.message,
                        )
                    )
                    outcome.failed.append(spec.source_id)
                    _log(
                        "intake_source",
                        source_id=spec.source_id,
                        kind=spec.kind,
                        status="error",
                        ms=round((perf_counter() - t0) * 1000, 2),
                        code=exc.code,
                    )
                except Exception as exc:
                    outcome.errors.append(
                        make_source_error(
                            source_id=spec.source_id,
                            code="intake.parse_failed",
                            message=str(exc)[:240],
                        )
                    )
                    outcome.failed.append(spec.source_id)
                    _log(
                        "intake_source",
                        source_id=spec.source_id,
                        kind=spec.kind,
                        status="error",
                        ms=round((perf_counter() - t0) * 1000, 2),
                        code="intake.parse_failed",
                    )
                if report_progress is not None:
                    report_progress(idx + 1, total, spec.kind)
        except IntakeCancelled as exc:
            if exc.original is not None:
                raise exc.original
            raise

    # Contract §5.3: lifecycle succeeded | partial — một phần (hoặc toàn bộ)
    # nguồn lỗi vẫn là partial với breakdown đầy đủ.
    if outcome.failed:
        outcome.status = "partial"
    return outcome


def analyze(sources: Any, **kwargs) -> IntakeOutcome:
    """Sync wrapper — dùng trong sidecar thread (không có event loop)."""
    return asyncio.run(analyze_async(sources, **kwargs))

"""Batch Word export theo contract notary.case-drafting.v1 §8 (MIN-110).

Sở hữu phần nghiệp vụ lớp catalog/orchestration cho
`notary.word_export_options` + `notary.word_export_batch`:

- document catalog: `document_key` → display_name / filename_stem ASCII
  do backend sở hữu (KHÔNG derive từ display_name — §8.3);
- readiness `word.*` block_reason qua `word_engine.word_block_reason`
  (cùng thứ tự check với `_add_block_placeholders`);
- render từng DOCX độc lập vào destination người dùng chọn — không ZIP,
  không output mặc định, KHÔNG BAO GIỜ ghi đè (open "xb" exclusive +
  reservation nội batch); file lỗi dở chỉ xóa đúng item đó;
- per-document status saved|failed|skipped + breakdown đủ ba list;
- cancel giữa batch: `check_cancel(pending_data)` — caller (sidecar)
  bọc thành `job.check_cancel(result)` của MIN-115; doc chưa bắt đầu
  đi vào breakdown.skipped, file đã lưu giữ nguyên;
- MIN-116: probe writability destination MỘT lần đầu batch bằng file
  tạo/xóa thật (`os.access` trên Windows misreport ACL deny-write) và
  KHÔNG dùng `tempfile.mkstemp` — stdlib retry PermissionError
  `TMP_MAX` = 2**31-1 lần trên nt → job hang vô hạn. Destination deny
  → mọi doc per-file `file_locked`, job failed trong giây.

Module này không import DB/FastAPI — `case` là ORM object duck-typed
giống `word_engine.build_word_context`. Sidecar `notary_adapter` chịu
trách session, FileRef/destination validation và map CommandError.
"""
from __future__ import annotations

import logging
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from services import word_engine

_logger = logging.getLogger("word_batch_export")

SCHEMA_VERSION = "notary.case-drafting.v1"

_DOC_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class WordBatchError(Exception):
    """Lỗi job-level → CommandError(code) ở sidecar.

    `result_data` (khi có) là `result.data` của batch — dùng cho
    `word_batch_failed` để breakdown/per-file errors lên wire (§8.4)."""

    def __init__(self, code: str, message: str, *,
                 details: Optional[dict] = None,
                 result_data: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.result_data = result_data


class _DocFailed(Exception):
    """Lỗi một văn bản — các văn bản khác tiếp tục (§8.4)."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------- catalog


@dataclass(frozen=True)
class WordDocumentSpec:
    """Một loại văn bản xuất được — registry mở (contract §8.1).

    `has_template=False` = v1 chưa có template cho loại này → luôn
    `word.template_missing` (như NO_TEMPLATE_KEYS của mock)."""

    document_key: str
    display_name: str
    filename_stem: str
    has_template: bool = True


DOC_CATALOG: tuple[WordDocumentSpec, ...] = (
    WordDocumentSpec(
        document_key="khai_nhan_di_san",
        display_name="Văn bản khai nhận di sản",
        filename_stem="Van_ban_khai_nhan_di_san"),
    WordDocumentSpec(
        document_key="thoa_thuan_phan_chia",
        display_name="Thỏa thuận phân chia di sản",
        filename_stem="Thoa_thuan_phan_chia_di_san"),
    WordDocumentSpec(
        document_key="niem_yet",
        display_name="Thông báo niêm yết",
        filename_stem="Thong_bao_niem_yet",
        has_template=False),
)
DOC_CATALOG_BY_KEY: dict[str, WordDocumentSpec] = {
    spec.document_key: spec for spec in DOC_CATALOG}

_BLOCK_MESSAGES = {
    "word.no_assets": "Hồ sơ chưa có tài sản",
    "word.no_landowner": "Chưa có chủ đất trên Diagram",
    "word.no_deceased_landowner": "Không có chủ đất đã chết",
    "word.no_receiver": "Chưa có người nhận",
    "word.too_many_assets": "Quá 5 tài sản",
    "word.too_many_people": "Quá 20 người trên Diagram",
    "word.too_many_signers": "Quá 20 người ký",
    "word.template_missing": "Văn bản chưa có template",
}

# ------------------------------------------------------------- validation


def validate_document_keys(document_keys: Any) -> list[str]:
    """Contract §8.2 — validate TRƯỚC khi tạo file đầu tiên.

    Thiếu/null/không list → validation_error (word_no_documents_selected
    CHỈ cho list rỗng — parity với mock oracle)."""
    if not isinstance(document_keys, list):
        raise WordBatchError(
            "validation_error", "document_keys phải là danh sách")
    if not document_keys:
        raise WordBatchError(
            "word_no_documents_selected", "document_keys rỗng")
    seen: list = []                     # list: dict/list keys unhashable
    for key in document_keys:
        if key in seen:
            raise WordBatchError(
                "word_duplicate_document_key",
                f"document_key lặp: {key!r}",
                details={"document_key": key})
        seen.append(key)
    for key in document_keys:
        if not (isinstance(key, str) and _DOC_KEY_RE.match(key)
                and key in DOC_CATALOG_BY_KEY):
            raise WordBatchError(
                "word_unknown_document_key",
                f"document_key ngoài catalog: {key!r}",
                details={"document_key": key})
    return list(document_keys)


# ------------------------------------------------------- filename safety

_WIN_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
_WIN_FORBIDDEN_CHARS = frozenset('<>:"/\\|?*')


def is_safe_windows_filename(name: Any) -> bool:
    """Tên file Windows hợp lệ cho output — defense-in-depth trên
    `actual_filename` (stem catalog đã sạch, nhưng không bao giờ tin
    dữ liệu đi ra ổ đĩa)."""
    if not isinstance(name, str) or not name:
        return False
    if ".." in name:                              # traversal
        return False
    if name != name.strip() or name.startswith("."):
        return False
    if name.endswith("."):
        return False
    if any(ch in _WIN_FORBIDDEN_CHARS or ord(ch) < 32 for ch in name):
        return False
    if name.split(".")[0].upper() in _WIN_RESERVED_NAMES:
        return False
    return True


def _assert_safe_filename(name: str) -> None:
    # `..`/separator dùng data-code đã register của contract (§8.3);
    # các dạng unsafe khác → word.invalid_filename.
    if isinstance(name, str) and (
            ".." in name or "/" in name or "\\" in name):
        raise _DocFailed(
            "word_path_traversal",
            f"tên file sinh ra thoát khỏi destination: {name!r}")
    if not is_safe_windows_filename(name):
        raise _DocFailed(
            "word.invalid_filename",
            f"tên file sinh ra không hợp lệ: {name!r}")


# ---------------------------------------------------------------- helpers


def _block_message(code: str) -> str:
    return _BLOCK_MESSAGES.get(code, code)


def _skipped_entry(spec: WordDocumentSpec) -> dict:
    return {
        "document_key": spec.document_key,
        "display_name": spec.display_name,
        "status": "skipped",
        "actual_filename": None,
        "output_file": None,
        "error": None,
    }


def _failed_entry(spec: WordDocumentSpec, code: str, message: str) -> dict:
    return {
        "document_key": spec.document_key,
        "display_name": spec.display_name,
        "status": "failed",
        "actual_filename": None,
        "output_file": None,
        "error": {"code": code, "message": message},
    }


def _batch_data(dest_dir: Path, documents: list[dict], *,
                succeeded: list[str], failed: list[str],
                skipped: list[str]) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "destination": {
            "path": str(dest_dir),
            "scope": "machine_local",
            "is_dir": True,
        },
        "documents": documents,
        "breakdown": {
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped,
        },
    }


def _doc_error_from(exc: BaseException,
                    context: word_engine.WordExportContext) -> tuple[str, str]:
    """Exception → (code, message) cho per-file error — data-code §2.5."""
    if isinstance(exc, _DocFailed):
        return exc.code, exc.message
    if isinstance(exc, word_engine.WordExportValidationError):
        # Mapping render raise cùng check với word_block_reason — reason
        # luôn non-None khi đây là một trong các lỗi §8.1.
        reason = word_engine.word_block_reason(context)
        return (reason or "word.render_failed"), str(exc)
    if isinstance(exc, FileNotFoundError):
        return "file_not_found", f"không tìm thấy file/thư mục: {exc}"
    if isinstance(exc, PermissionError):
        return "file_locked", f"không ghi được file: {exc}"
    return "word.render_failed", f"{type(exc).__name__}: {exc}"


_TEMP_CREATE_ATTEMPTS = 8


def _temp_file_in(dest_dir: Path, *, prefix: str, suffix: str) -> Path:
    """Tạo file rỗng exclusive trong `dest_dir` (uuid name + open "xb"),
    trả path đã tạo.

    MIN-116: KHÔNG dùng tempfile.mkstemp — `_mkstemp_inner` của stdlib
    retry PermissionError trên Windows khi `os.access(dir, W_OK)` trả
    True (ACL deny-write bị misreport), và TMP_MAX = 2**31-1 → vòng
    lặp thực tế vô hạn, job hang không cancel được. open("xb") raise
    PermissionError NGAY ở lần đầu — chỉ retry trên FileExistsError
    (va chạm uuid, gần như không thể)."""
    for _ in range(_TEMP_CREATE_ATTEMPTS):
        candidate = dest_dir / f"{prefix}{uuid.uuid4().hex}{suffix}"
        try:
            with open(candidate, "xb"):
                pass
        except FileExistsError:
            continue
        return candidate
    raise FileExistsError(
        f"không tạo được file tạm trong destination {dest_dir}")


def _probe_dest_writable(dest_dir: Path) -> None:
    """MIN-116: verify destination THỰC SỰ ghi được bằng một lần tạo/xóa
    file ở đầu batch — `os.access()` trên Windows không đáng tin với
    ACL (chỉ đọc attribute read-only bit, không eval ACL thật)."""
    probe = _temp_file_in(
        dest_dir, prefix=".word_export_probe_", suffix=".tmp")
    try:
        probe.unlink()
    except OSError:
        pass


def _render_temp(doc: Any, dest_dir: Path) -> Path:
    """Render docx ra file tạm NGAY TRONG destination (cùng filesystem —
    publish sau chỉ là copy nội bộ). Lỗi → xóa file tạm.

    MIN-116: `_temp_file_in` thay tempfile.mkstemp — PermissionError
    propagate ngay thành per-doc `file_locked` thay vì hang trong
    stdlib retry loop."""
    tmp_path = _temp_file_in(
        dest_dir, prefix=".word_export_", suffix=".docx")
    try:
        doc.save(str(tmp_path))
    except BaseException:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise
    return tmp_path


def _publish(tmp_path: Path, dest_dir: Path, spec: WordDocumentSpec,
             case_id: int, taken: set[str]) -> str:
    """Đặt tên `<stem>_HS-<case_id>[_n].docx` (n ≥ 2) và ghi exclusive.

    `taken` = reservation nội batch (hai document cùng stem không va);
    `open("xb")` chống cả file đã tồn tại lẫn race — KHÔNG BAO GIỜ ghi đè.
    Copy lỗi → xóa đúng file dở của item này. Trả actual_filename."""
    n = 1
    while True:
        suffix = "" if n == 1 else f"_{n}"
        name = f"{spec.filename_stem}_HS-{case_id}{suffix}.docx"
        n += 1
        _assert_safe_filename(name)
        if name in taken:
            continue
        target = dest_dir / name
        if target.is_dir():
            continue                       # directory cùng tên → _n kế
        try:
            fh = open(target, "xb")          # exclusive create — atomic
        except FileExistsError:
            continue
        taken.add(name)
        try:
            with open(tmp_path, "rb") as src:
                shutil.copyfileobj(src, fh)
            fh.close()
        except BaseException:
            taken.discard(name)            # trả reservation khi fail
            try:
                fh.close()
            finally:
                try:
                    target.unlink()          # không để file nửa vời lại
                except OSError:
                    pass
            raise
        return name


def _export_one_document(*, spec: WordDocumentSpec, case: Any,
                         context: word_engine.WordExportContext,
                         data_reason: Optional[str],
                         resolve_template: Callable[[str], Any],
                         mapping_holder: dict, dest_dir: Path,
                         taken: set[str], case_id: int, today: Any,
                         check: Callable[[], None]) -> dict:
    """Xuất một văn bản — trả word_document_result entry.

    Mọi exception trong try → status:failed với data-code; exception
    cancel (do `check()` raise) vẫn thoát qua — `check()` trong except
    re-raise khi flag đang set, nên cancel không bao giờ nuốt thành failed.
    """
    try:
        # Thứ tự check như mock: template → data validation → render.
        if not spec.has_template:
            raise _DocFailed("word.template_missing",
                             _block_message("word.template_missing"))
        template_path = resolve_template(spec.document_key)
        if template_path is None:
            raise _DocFailed("word.template_missing",
                             _block_message("word.template_missing"))
        if data_reason is not None:
            raise _DocFailed(data_reason, _block_message(data_reason))

        import docx  # lazy — giữ module import được khi thiếu python-docx
        doc = docx.Document(str(template_path))
        mapping = mapping_holder.get("mapping")
        if mapping is None:
            mapping = word_engine.build_template_mapping(case, today=today)
            mapping_holder["mapping"] = mapping
        word_engine.replace_in_doc(doc, mapping)
        unresolved = word_engine.find_unresolved_placeholders(doc)
        if unresolved:
            raise _DocFailed(
                "word.unresolved_placeholders",
                f"Mẫu còn {len(unresolved)} trường chưa hỗ trợ: "
                + ", ".join(unresolved))

        check()                        # cancel trước khi render
        tmp_path = _render_temp(doc, dest_dir)
        try:
            check()                        # cancel trước khi publish
            name = _publish(tmp_path, dest_dir, spec, case_id, taken)
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass
        return {
            "document_key": spec.document_key,
            "display_name": spec.display_name,
            "status": "saved",
            "actual_filename": name,
            "output_file": {
                "path": str(dest_dir / name),
                "scope": "machine_local",
            },
            "error": None,
        }
    except ImportError as exc:
        # Thiếu python-docx = lỗi hạ tầng, không phải lỗi của 1 văn bản —
        # thoát khỏi per-doc boundary thành job-level engine_unavailable.
        raise WordBatchError(
            "engine_unavailable",
            f"thiếu dependency python-docx: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 — per-document boundary
        check()   # cancel pending → raise tại đây (doc tính skipped)
        code, message = _doc_error_from(exc, context)
        _logger.info("word_doc_failed %s",
                     {"document_key": spec.document_key, "code": code})
        return _failed_entry(spec, code, message)


# ---------------------------------------------------------------- public


def export_options(case: Any, *, resolve_template: Callable[[str], Any],
                   today: Any = None) -> dict:
    """`result.data` của notary.word_export_options — read-only.

    Liệt kê TOÀN BỘ catalog (không chỉ template active); block_reason
    theo `word_engine.word_block_reason` — cùng semantics với render.
    """
    context = word_engine.build_word_context(case, today=today)
    data_reason = word_engine.word_block_reason(context)
    documents = []
    for spec in DOC_CATALOG:
        block = None
        if not spec.has_template:
            block = "word.template_missing"
        elif resolve_template(spec.document_key) is None:
            block = "word.template_missing"
        else:
            block = data_reason
        documents.append({
            "document_key": spec.document_key,
            "display_name": spec.display_name,
            "ready": block is None,
            "block_reason": block,
        })
    return {"schema_version": SCHEMA_VERSION, "documents": documents}


def export_batch(case: Any, *, case_id: int, document_keys: Any,
                 dest_dir: Any, resolve_template: Callable[[str], Any],
                 check_cancel: Optional[Callable[[dict], None]] = None,
                 report_progress: Optional[Callable] = None,
                 today: Any = None) -> dict:
    """`result.data` của notary.word_export_batch — read snapshot + ghi file.

    `check_cancel(data)` được gọi GIỮA các văn bản với result.data hiện
    tại (doc chưa bắt đầu → skipped) — caller bọc job.check_cancel(result)
    của jobstore để canceled job vẫn mang breakdown (MIN-115).

    Tất cả failed → WordBatchError("word_batch_failed", result_data=...).
    """
    keys = validate_document_keys(document_keys)
    dest_dir = Path(dest_dir)
    if not dest_dir.is_dir():
        raise WordBatchError(
            "file_not_found",
            "destination không phải thư mục đang tồn tại")

    taken: set[str] = set()
    docs: list[dict] = []
    saved: list[str] = []
    failed: list[str] = []
    total = len(keys)

    def _pending_data() -> dict:
        """Snapshot result.data: đã xong giữ status; chưa bắt đầu → skipped."""
        entries = list(docs)
        remaining = keys[len(entries):]
        for key in remaining:
            entries.append(_skipped_entry(DOC_CATALOG_BY_KEY[key]))
        return _batch_data(
            dest_dir, entries, succeeded=list(saved),
            failed=list(failed), skipped=list(remaining))

    def _check() -> None:
        if check_cancel is not None:
            check_cancel(_pending_data())

    # MIN-116: probe writability destination MỘT lần đầu batch, trước khi
    # build context/render — destination deny-write (ACL) thì mọi doc
    # nhận per-file error chung, job kết thúc trong giây, KHÔNG hang.
    _check()                                       # cancel trước khi probe
    dest_error: Optional[tuple[str, str]] = None
    try:
        _probe_dest_writable(dest_dir)
    except FileNotFoundError as exc:
        dest_error = ("file_not_found",
                      f"destination không còn tồn tại: {exc}")
    except PermissionError as exc:
        dest_error = ("file_locked",
                      f"destination không ghi được: {exc}")
    except OSError as exc:
        dest_error = ("word.render_failed",
                      f"destination không tạo được file: {exc}")

    # Chỉ build context khi dest ghi được — dest_error set thì mọi doc
    # nhận per-file error chung, context build vừa thừa vừa có thể ném
    # raw exception ngoài shape per-doc (review MIN-116 minor).
    context = None
    data_reason = None
    if dest_error is None:
        context = word_engine.build_word_context(case, today=today)
        data_reason = word_engine.word_block_reason(context)
    mapping_holder: dict = {}

    for key in keys:
        _check()                                   # cancel giữa batch
        spec = DOC_CATALOG_BY_KEY[key]
        if dest_error is not None:
            code, message = dest_error
            entry = _failed_entry(spec, code, message)
        else:
            entry = _export_one_document(
                spec=spec, case=case, context=context,
                data_reason=data_reason, resolve_template=resolve_template,
                mapping_holder=mapping_holder, dest_dir=dest_dir,
                taken=taken, case_id=case_id, today=today, check=_check)
        docs.append(entry)
        (saved if entry["status"] == "saved" else failed).append(key)
        if report_progress is not None:
            report_progress(len(docs), total,
                            f"văn bản {len(docs)}/{total}")

    data = _batch_data(dest_dir, docs, succeeded=saved, failed=failed,
                       skipped=[])
    if len(failed) == total:
        raise WordBatchError(                      # §8.4 — job failed
            "word_batch_failed",
            "Toàn bộ văn bản trong lượt xuất đều lỗi",
            details={"documents": [
                {"document_key": d["document_key"],
                 "code": d["error"]["code"],
                 "message": d["error"]["message"]} for d in docs]},
            result_data=data)
    return data


__all__ = [
    "DOC_CATALOG",
    "DOC_CATALOG_BY_KEY",
    "WordBatchError",
    "WordDocumentSpec",
    "export_batch",
    "export_options",
    "is_safe_windows_filename",
    "validate_document_keys",
]

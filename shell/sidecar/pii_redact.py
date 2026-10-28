"""Che PII/bi mat trong log va text exception cua Python (sidecar + notary_v2).

Ban sao Y HET o `notary_v2/pii_redact.py` (hai process khac sys.path);
test `test_pii_redact.py::test_copies_identical` giu hai file dong bo.

Che: CCCD/CMND, ngay sinh, ho ten (heuristic ho Viet + nhan "ho ten"),
dia chi (nhan "dia chi"/"thuong tru" + don vi hanh chinh), duong dan
Windows/UNC/posix, token (token=/token xyz/Bearer/gh*_/chuoi dai ngau
nhien). Heuristic co chu dich che THUA hon thieu — log la de debug luong,
khong de doc du lieu cong dan.
"""
from __future__ import annotations

import io
import logging
import re
import sys
import threading

R = {
    "path": "<path>", "token": "<token>", "cccd": "<cccd>",
    "dob": "<date>", "name": "<name>", "address": "<address>",
}

_VN_UPPER = "A-ZĐÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ"
_VN_WORD = rf"[{_VN_UPPER}][^\W\d_]*"
_SURNAMES = (
    "Nguyễn|Nguyen|Trần|Tran|Lê|Le|Phạm|Pham|Hoàng|Hoang|Huỳnh|Huynh|Phan|"
    "Vũ|Vu|Võ|Vo|Đặng|Dang|Bùi|Bui|Đỗ|Do|Hồ|Ho|Ngô|Ngo|Dương|Duong|Lý|Ly|"
    "Đinh|Dinh|Trịnh|Trinh|Đào|Dao|Mai|Tô|Cao|Lưu|Luu|Tạ|Ta|Lâm|Lam|Chu")
_ADMIN = (r"(?:phường|phuong|xã|thị trấn|thi tran|quận|quan|huyện|huyen|"
          r"tỉnh|tinh|thành phố|thanh pho|thôn|thon|xóm|xom|ấp|tổ dân phố|khu phố)")

_RULES: list[tuple[re.Pattern, str]] = [
    # --- token / secret ---
    (re.compile(r"\b(gh[pousr]_|github_pat_)[A-Za-z0-9_]+"), R["token"]),
    (re.compile(r"(?i)\bbearer\s+\S+"), "Bearer " + R["token"]),
    (re.compile(
        r"(?i)\b((?:access_|refresh_|api_|id_)?token|secret|password|passwd|"
        r"api_key|cookie|session|authorization|credential)"
        r"(\"?'?\s*(?:[:=]\s*|\s+)[\"']?)(?!<)([^\s\"',;&}\]]+)"),
     r"\1\2" + R["token"]),
    (re.compile(r"\b(?=[A-Za-z0-9_\-]*\d)(?=[A-Za-z0-9_\-]*[A-Za-z])"
                r"[A-Za-z0-9_\-]{32,}\b"), R["token"]),
    # --- duong dan ---
    (re.compile(r"\\\\[?.]\\[^\s\"'<>|]+"), R["path"]),            # \\?\C:\...
    (re.compile(r"\\\\[^\s\\\"'<>|]+\\[^\s\"'<>|]+"), R["path"]),  # UNC
    (re.compile(r"\b[A-Za-z]:[\\/][^\s\"'<>|,;]*"), R["path"]),    # C:\...
    (re.compile(r"(?<![\w:/.<])/(?:[^\s/\"'<>,;:]+/)+[^\s\"'<>,;:]*"),
     R["path"]),                                                    # /a/b
    # --- dinh danh ---
    (re.compile(r"(?<!\d)\d{12}(?!\d)"), R["cccd"]),
    (re.compile(r"(?i)\b(cmnd|cccd|căn cước|can cuoc|cmt|hộ chiếu|ho chieu|"
                r"passport)(\s*(?:số|so|no\.?)?\s*[:=]?\s*)[A-Z]?\d{6,12}\b"),
     r"\1\2" + R["cccd"]),
    # --- ngay sinh / ngay ---
    (re.compile(r"(?<!\d)(?:0?[1-9]|[12]\d|3[01])[/.\-](?:0?[1-9]|1[0-2])"
                r"[/.\-](?:19|20)\d{2}(?!\d)"), R["dob"]),
    (re.compile(r"(?<![\d\-])(?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])"
                r"(?![\dT:])"), R["dob"]),
    # --- dia chi ---
    (re.compile(r"(?i)\b(địa chỉ|dia chi|address|thường trú|thuong tru|"
                r"tạm trú|tam tru|nơi cư trú|noi cu tru|quê quán|que quan)"
                r"(\s*[:=]\s*|\s+)[^\n;|]+"), r"\1\2" + R["address"]),
    (re.compile(rf"(?i)\b{_ADMIN}\s+[^\s,;\n][^,;\n]*"), R["address"]),
    # --- ho ten ---
    (re.compile(r"(?i)\b(họ và tên|ho va ten|họ tên|ho ten|full_?name|"
                r"ho_ten|người được cấp|chủ sử dụng|chu su dung)"
                r"(\s*[:=]\s*|\s+)[^\n,;|]+"), r"\1\2" + R["name"]),
    (re.compile(rf"\b(?:{_SURNAMES})(?:\s+{_VN_WORD}){{1,4}}"), R["name"]),
]

_extra: list[str] = []
_lock = threading.Lock()


def add_secret(value: str | None) -> None:
    """Dang ky gia tri bi mat cu the (vd SIDECAR_TOKEN) de che nguyen van."""
    if value and len(value) >= 6:
        with _lock:
            if value not in _extra:
                _extra.append(value)


def redact_text(text: object) -> str:
    s = text if isinstance(text, str) else str(text)
    for secret in list(_extra):
        s = s.replace(secret, R["token"])
    for pat, repl in _RULES:
        s = pat.sub(repl, s)
    return s


def redact_exception(exc: BaseException) -> str:
    """`Type: message` da che — dung thay cho f"{exc}" khi ghi log/luu loi."""
    return redact_text(f"{type(exc).__name__}: {exc}")


class RedactingFilter(logging.Filter):
    """Filter gan vao HANDLER: che msg+args va traceback truoc khi format."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:  # noqa: BLE001 — format loi thi giu msg goc
            msg = str(record.msg)
        record.msg = redact_text(msg)
        record.args = None
        if record.exc_info and record.exc_info[0] is not None:
            record.exc_text = redact_text(
                logging.Formatter().formatException(record.exc_info))
            record.exc_info = None
        if record.stack_info:
            record.stack_info = redact_text(record.stack_info)
        return True


class RedactingStream(io.TextIOBase):
    """Boc stdout/stderr: che theo dong (traceback/print cung di qua)."""

    def __init__(self, inner):
        self._inner = inner
        self._buf = ""

    def writable(self) -> bool:
        return True

    def write(self, s: str) -> int:
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self._inner.write(redact_text(line) + "\n")
        return len(s)

    def flush(self) -> None:
        if self._buf:
            self._inner.write(redact_text(self._buf))
            self._buf = ""
        self._inner.flush()

    def __getattr__(self, name):
        return getattr(self._inner, name)


_FILTER = RedactingFilter()


def attach_filter(logger: logging.Logger | None = None) -> None:
    lg = logger or logging.getLogger()
    for h in lg.handlers:
        if _FILTER not in h.filters:
            h.addFilter(_FILTER)


def install(*, wrap_std: bool = True, secrets: tuple = ()) -> None:
    """Goi 1 lan khi process khoi dong (sau khi cau hinh logging)."""
    for s in secrets:
        add_secret(s)
    for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        attach_filter(logging.getLogger(name))
    if wrap_std:
        if not isinstance(sys.stdout, RedactingStream):
            sys.stdout = RedactingStream(sys.stdout)
        if not isinstance(sys.stderr, RedactingStream):
            sys.stderr = RedactingStream(sys.stderr)

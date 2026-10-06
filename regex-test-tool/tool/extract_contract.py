"""
TRICH XUAT HOP DONG CONG CHUNG -> JSON CHO WEB FORM
===================================================
CORE REGEX DUNG CHUNG (nguoi + tai san) — agent moi doc them:
- Catalog quy tac: docs/spec/upload_lab/regex-rules.md (dau file co muc
  "Core nam o dau" chi dung file engine/test/bao cao).
- Test: upload_lab/tests/test_upload_lab_extract_contract.py
- Bao cao tung loai van ban: .agent/scratch/regex-core/bao-cao-NN-*.md
Pham vi core: chi trich XUAT (regex) nguoi + tai san; KHONG so sanh,
KHONG doi chieu, KHONG gop — co nguoi nao xuat du lieu nguoi do.
So cong chung van duoc doc (phuc vu upload/audit) nhung khong con la
tieu chi "du/thieu" cua core.

Cach dung:
    python extract_contract.py "hop_dong.docx"
    python extract_contract.py "hop_dong.doc"

Ket qua:
    - In JSON ra man hinh
    - Luu file .json cung thu muc

Cai dat:
    pip install python-docx
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Iterable


ENGINE_VERSION = "2026-10-10-sweep3"
"""Ban engine snapshot cho repo test cua nhan vien ghi vao log."""

# ============================================================
# CAU HINH MAC DINH — sua tai day cho phu hop van phong
# ============================================================
DEFAULT_CCV = "Phạm Minh Chi"
CONTRACT_YEAR = "2026"
CONTRACT_NO_REGEX = re.compile(r"\b(\d+[./]\d{4}(?:/[A-Z0-9]+)*/CCGD)\b", re.IGNORECASE)
CONTRACT_KEYWORDS = ("hợp đồng", "hop dong", "hđ", "hd")

NHOM_HD_MAP = {
    "chuyển nhượng": "Chuyển nhượng - Mua bán",
    "mua bán": "Chuyển nhượng - Mua bán",
    "tặng cho": "Tặng, cho tài sản",
    "tặng, cho": "Tặng, cho tài sản",
    "thế chấp": "Cầm cố - Thế chấp - Vay",
    "cầm cố": "Cầm cố - Thế chấp - Vay",
    "vay": "Cầm cố - Thế chấp - Vay",
    "ủy quyền": "Ủy quyền",
    "ủy quền": "Ủy quyền",
    "di chúc": "Di chúc",
    "đặt cọc": "Đặt cọc",
    "thỏa thuận": "Thoả thuận - Cam kết",
    "cam kết": "Thoả thuận - Cam kết",
    "góp vốn": "Góp vốn - Hợp tác",
    "hợp tác": "Góp vốn - Hợp tác",
    "thừa kế": "Thừa kế (khai nhận - phân chia di sản thừa kế )",
    "khai nhận": "Thừa kế (khai nhận - phân chia di sản thừa kế )",
    "phân chia": "Thừa kế (khai nhận - phân chia di sản thừa kế )",
    "từ chối nhận di sản": "Từ chối nhận di sản thừa kế",
    "phụ lục": "Phụ lục hợp đồng - văn bản sửa đổi",
    "thuê": "Thuê - Mượn tài sản",
    "mượn": "Thuê - Mượn tài sản",
}


CRITICAL_WEB_FORM_FIELDS = (
    "ten_hop_dong",
    "nhom_hop_dong",
    "loai_tai_san",
    "tai_san",
)
# Core regex chi chiu trach nhiem NGUOI + TAI SAN.
# "so_cong_chung" van duoc trich (find_so_cong_chung, scan) de phuc vu
# upload/audit portal, nhung khong con la tieu chi du/thieu cua core.

DOC_KIND_TRANSFER = "transfer_contract"
DOC_KIND_GIFT = "gift_contract"
DOC_KIND_ASSET_COMMITMENT = "asset_commitment"
DOC_KIND_TRANSFER_CANCELLATION = "transfer_cancellation"
DOC_KIND_MORTGAGE = "mortgage_contract"
DOC_KIND_INHERITANCE_PARTITION = "inheritance_partition"
DOC_KIND_INHERITANCE_REFUSAL = "inheritance_refusal"
DOC_KIND_INHERITANCE_DECLARATION = "inheritance_declaration"
DOC_KIND_GENERIC = "generic"


def _append_text_lines(lines: list[str], values: Iterable[str]) -> None:
    for raw in values:
        text = str(raw or "").strip()
        if text:
            lines.append(text)


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = str(raw or "").strip()
        if not value or value in seen:
            continue
        items.append(value)
        seen.add(value)
    return items


def _append_table_lines(lines: list[str], tables) -> None:
    for table in tables:
        for row in table.rows:
            row_values = []
            for cell in row.cells:
                cell_text = " ".join(
                    p.text.strip()
                    for p in cell.paragraphs
                    if p.text and p.text.strip()
                ).strip()
                if cell_text:
                    row_values.append(cell_text)
            row_values = _dedupe_preserve_order(row_values)
            if row_values:
                lines.append(" | ".join(row_values))


def _append_docx_body_lines(lines: list[str], doc) -> None:
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            _append_text_lines(lines, [Paragraph(child, doc).text])
            continue
        if isinstance(child, CT_Tbl):
            _append_table_lines(lines, [Table(child, doc)])


# ============================================================
# DOCX / DOC HELPERS
# ============================================================
def read_doc_via_ifilter(filepath) -> str:
    """Trich xuat text tu .doc bang Windows IFilter (cung co che voi Agent Ransack).
    WHY: Doc .doc tren Windows ma khong can Word/Office.
         Dung cho scan (tim so hop dong) — chi can plain text, khong can table structure.
    RISK: IFilter tra plain text thuan — mat cau truc bang va header/footer.
          Flow extract() cho .doc se chay theo plain text nay.
    REQUIRE: query.dll (co san tren Windows 7+, khong can cai them).
    """
    import ctypes

    abs_path = str(Path(filepath).resolve())
    ole32 = ctypes.windll.ole32
    ole32.CoInitialize(None)
    try:
        query = ctypes.windll.query
        # c_long (signed) de compare HRESULT am — WINFUNCTYPE(HRESULT) tu raise exception
        query.LoadIFilter.restype = ctypes.c_long
        query.LoadIFilter.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        p_filter = ctypes.c_void_p()
        hr = query.LoadIFilter(abs_path, None, ctypes.byref(p_filter))
        if hr != 0 or not p_filter.value:
            raise OSError(f"LoadIFilter that bai (hr=0x{hr & 0xFFFFFFFF:08X})")

        # IFilter VTBL layout (IUnknown 0-2, IFilter 3-7):
        #   3=Init, 4=GetChunk, 5=GetText, 6=GetValue, 7=BindRegion
        VTBL_INIT = 3
        VTBL_GET_CHUNK = 4
        VTBL_GET_TEXT = 5
        VTBL_RELEASE = 2

        vtbl_ptr = ctypes.cast(p_filter, ctypes.POINTER(ctypes.c_void_p))
        vtbl = ctypes.cast(vtbl_ptr[0], ctypes.POINTER(ctypes.c_void_p))

        # Init(grfFlags, cAttributes, aAttributes, pFlags) — c_long tranh auto-raise
        InitFunc = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p,
            ctypes.c_uint, ctypes.c_ulong, ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint),
        )
        out_flags = ctypes.c_uint(0)
        InitFunc(vtbl[VTBL_INIT])(p_filter, 0, 0, None, ctypes.byref(out_flags))

        # STAT_CHUNK tren x64 Windows:
        #   offset  0: idChunk   (ULONG 4B)
        #   offset  4: breakType (enum  4B)
        #   offset  8: flags     (CHUNKSTATE 4B) — CHUNK_TEXT=0x1, CHUNK_VALUE=0x2
        #   offset 12: locale    (LCID  4B)
        #   offset 16: attribute (FULLPROPSPEC = GUID(16B) + PROPSPEC(4+4pad+8B) = 32B)
        #   offset 48: idChunkSource (4B), cwcStartSource (4B), cwcLenSource (4B)
        #   total: 60B — dung 64B buffer cho an toan tren moi alignment
        CHUNK_BUF_SIZE = 64
        CHUNK_FLAGS_OFFSET = 8
        CHUNK_TEXT = 0x1  # CHUNKSTATE: CHUNK_TEXT=1 (khong phai 2)

        GetChunkFunc = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, ctypes.c_char_p,
        )
        get_chunk_fn = GetChunkFunc(vtbl[VTBL_GET_CHUNK])

        BUF_SIZE = 4096
        GetTextFunc = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ulong), ctypes.c_wchar_p,
        )
        get_text_fn = GetTextFunc(vtbl[VTBL_GET_TEXT])

        ReleaseFunc = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)
        release_fn = ReleaseFunc(vtbl[VTBL_RELEASE])

        # HRESULT codes (signed 32-bit)
        FILTER_E_END_OF_CHUNKS = ctypes.c_long(0x80041700).value  # negative
        FILTER_E_NO_MORE_TEXT  = ctypes.c_long(0x80041701).value  # negative
        # FILTER_S_LAST_TEXT = 0x00041709 — SUCCESS: text duoc ghi VA day la phan cuoi cung
        # Phai capture text TRUOC khi check status nay, roi break
        FILTER_S_LAST_TEXT = 0x00041709  # positive (success with info)

        parts: list[str] = []
        chunk_buf = ctypes.create_string_buffer(CHUNK_BUF_SIZE)

        while True:
            hr_chunk = get_chunk_fn(p_filter, chunk_buf)
            if hr_chunk == FILTER_E_END_OF_CHUNKS:
                break
            if hr_chunk != 0:
                break

            flags = ctypes.c_uint.from_buffer_copy(chunk_buf, CHUNK_FLAGS_OFFSET).value
            if not (flags & CHUNK_TEXT):
                continue

            while True:
                buf_len = ctypes.c_ulong(BUF_SIZE)
                text_buf = ctypes.create_unicode_buffer(BUF_SIZE)
                hr_text = get_text_fn(p_filter, ctypes.byref(buf_len), text_buf)
                # Capture text TRUOC khi check status — FILTER_S_LAST_TEXT tra text hop le
                if buf_len.value > 0:
                    parts.append(text_buf.value[: buf_len.value])
                if hr_text == FILTER_E_NO_MORE_TEXT:
                    break
                if hr_text == FILTER_S_LAST_TEXT:
                    break  # text da duoc lay, day la phan cuoi cua chunk nay
                if hr_text != 0:
                    break

        release_fn(p_filter)
        return "".join(parts)
    finally:
        ole32.CoUninitialize()


def read_docx(filepath, *, use_ifilter_for_doc: bool = False):
    """Doc .docx hoac .doc -> text thuan.
    - .docx: dung python-docx truc tiep (nhanh).
    - .doc: dung IFilter/plain text tren Windows, khong can Word.
    """
    path = Path(filepath)
    if path.suffix.lower() == ".doc":
        return read_doc_via_ifilter(filepath)

    from docx import Document
    doc = Document(str(filepath))
    lines: list[str] = []
    _append_docx_body_lines(lines, doc)
    for section in doc.sections:
        _append_text_lines(lines, (p.text for p in section.header.paragraphs))
        _append_text_lines(lines, (p.text for p in section.footer.paragraphs))
    return "\n".join(lines)


def _normalize_scan_contract_no(contract_no: str) -> str:
    text = re.sub(r"\s+", "", str(contract_no or "").strip().upper())
    match = re.match(r"^(\d+)[./](\d{4})(.*)$", text)
    if match:
        return f"{match.group(1)}/{match.group(2)}{match.group(3)}"
    return text


def _normalize_web_contract_no(contract_no: str) -> str:
    normalized = _normalize_scan_contract_no(contract_no)
    match = re.match(r"^(\d+)/(\d{4})(?:/[A-Z0-9]+)*(?:/CCGD)?$", normalized, re.IGNORECASE)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    if normalized.endswith("/CCGD"):
        normalized = normalized[:-5]
    match = re.match(r"^(\d+)[./](\d{4})$", normalized)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return normalized


def find_contract_numbers(text: str) -> list[str]:
    return [_normalize_scan_contract_no(match.group(1)) for match in CONTRACT_NO_REGEX.finditer(text or "")]


def has_contract_keyword(text: str, file_name: str = "") -> bool:
    haystack = f"{file_name}\n{text}".lower()
    return any(keyword in haystack for keyword in CONTRACT_KEYWORDS)


def _normalize_plain_text_for_extract(text: str) -> str:
    normalized = str(text or "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    # IFilter giu o bang bang TAB — doi thanh " | " (cung quy uoc voi
    # _append_table_lines cua .docx) de parser bang dung chung duoc.
    # Nguoi doc ten khong bao gio co "|" nen khong so nham.
    normalized = normalized.replace("\x0b", "\n").replace("\t", " | ").replace("\xa0", " ")
    normalized = unicodedata.normalize("NFC", normalized)
    lines = []
    for raw in normalized.split("\n"):
        line = re.sub(r"[ \xa0]+", " ", raw).strip()
        line = re.sub(r"\s*\|\s*", " | ", line)
        # Dau/cuoi dong con "| " la do TAB thu dau dong cua .doc —
        # cat de pattern ^...$ khong bi lech (o trong bang van giu).
        line = re.sub(r"^(?:\s*\|\s*)+", "", line)
        line = re.sub(r"(?:\s*\|\s*)+$", "", line)
        if line:
            lines.append(line)
    return "\n".join(lines)


def _scan_contract_text(text: str, *, file_name: str = "") -> dict:
    matches = find_contract_numbers(text)
    if matches:
        contract_no = matches[-1]
        return {
            "is_contract": True,
            "contract_no": contract_no,
            "reason": f"Tim thay so CC: {contract_no}",
        }

    if has_contract_keyword(text, file_name):
        return {
            "is_contract": False,
            "contract_no": "",
            "reason": "Co keyword hop dong nhung khong thay so cong chung",
        }

    return {
        "is_contract": False,
        "contract_no": "",
        "reason": "Khong thay so cong chung",
    }


def scan_docx_for_contract_no(filepath, *, include_text: bool = False):
    """Tim so cong chung trong noi dung file .docx hoac .doc.
    .doc dung IFilter (nhanh) — chi can plain text de tim regex so cong chung.
    """
    path = Path(filepath)
    use_ifilter_for_doc = path.suffix.lower() == ".doc"
    try:
        text = read_docx(path, use_ifilter_for_doc=use_ifilter_for_doc)
        if use_ifilter_for_doc:
            text = _normalize_plain_text_for_extract(text)
    except Exception as exc:
        result = {
            "is_contract": False,
            "contract_no": "",
            "reason": f"Khong doc duoc file: {exc}",
        }
        if include_text:
            result["text"] = ""
        return result

    result = _scan_contract_text(text, file_name=path.name)
    if include_text:
        result["text"] = text
    return result


# ============================================================
# TRICH XUAT TUNG TRUONG
# ============================================================
def find_ten_hop_dong(text):
    _, title = _detect_document_kind_and_title(text)
    return title


def find_so_cong_chung(text):
    m = re.search(r"Số công chứng\s*(\d+)\s*[./]\s*(\d{4})(?:\s*/\s*[A-Z0-9]+)*\s*/\s*CCGD\b", text, re.IGNORECASE)
    if m:
        return _normalize_web_contract_no(f"{m.group(1)}/{m.group(2)}/CCGD")

    matches = find_contract_numbers(text)
    if matches:
        return _normalize_web_contract_no(matches[-1])
    return ""


def find_ngay_cong_chung(text):
    idx = text.find("LỜI CHỨNG")
    sub = text[idx:] if idx >= 0 else text
    m = re.search(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", sub)
    if m:
        return f"{m.group(1).zfill(2)}/{m.group(2).zfill(2)}/{m.group(3)}"
    return ""


def find_ccv(text):
    m = re.search(r"Tôi,\s+([^,]+),\s+Công chứng viên", text)
    return m.group(1).strip() if m else DEFAULT_CCV


def find_persons(section):
    """Tim tat ca nguoi trong 1 doan (Ben A hoac Ben B)."""
    persons = []
    names = list(re.finditer(r"(Ông|[Bb]à)\s+([^;]+?)\s*;", section))

    for idx, nm in enumerate(names):
        start = nm.start()
        end = names[idx + 1].start() if idx + 1 < len(names) else len(section)
        chunk = section[start:end]

        person = {
            "gioi_tinh": nm.group(1).capitalize(),
            "ho_ten": nm.group(2).strip(),
        }

        m = re.search(r"Sinh ngày:?\s*(\d{2}/\d{2}/\d{4})", chunk)
        person["ngay_sinh"] = m.group(1) if m else ""

        m = re.search(r"(?:Căn cước|CCCD|CMND)(?:\s+công dân)?\s*(?:số:?\s*)(\d+)", chunk)
        person["cccd"] = m.group(1) if m else ""

        m = re.search(r"do\s+([^\n]+?)\s+cấp ngày", chunk)
        person["noi_cap"] = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

        m = re.search(r"cấp ngày\s*(\d{2}/\d{2}/\d{4})", chunk)
        person["ngay_cap_cccd"] = m.group(1) if m else ""

        persons.append(person)

    return persons


def find_dia_chi(section):
    m = re.search(r"cùng (?:cư trú|thường trú) tại:?\s*([^\n.]+)\.", section)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def find_tai_san(text):
    doc_kind, _ = _detect_document_kind_and_title(text)
    return _find_tai_san_by_kind(text, doc_kind)


def _fold_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", str(text or ""))
    normalized = normalized.replace("\u0111", "d").replace("\u0110", "D")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()


def _fold_text_with_index_map(text: str) -> tuple[str, list[int]]:
    source = str(text or "")
    folded_chars: list[str] = []
    index_map: list[int] = []
    for idx, char in enumerate(source):
        normalized = unicodedata.normalize("NFD", char)
        normalized = normalized.replace("\u0111", "d").replace("\u0110", "D")
        for part in normalized:
            if unicodedata.category(part) == "Mn":
                continue
            folded_chars.append(part.lower())
            index_map.append(idx)
    return "".join(folded_chars), index_map


def _clean_title_line(text: str) -> str:
    cleaned = unicodedata.normalize("NFC", str(text or ""))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return ""
    cleaned = re.sub(
        r"\s+(?:này\s+)?được\s+giao\s+kết\s+(?:bởi|giữa)\s*:?\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\s+(?:nay\s+)?duoc\s+giao\s+ket\s+boi\s*:?\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\s+(?:nÃ y\s+)?Ä‘Æ°á»£c\s+giao\s+káº¿t\s+giá»¯a\s*:?\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\s+(?:nay\s+)?duoc\s+giao\s+ket\s+giua\s*:?\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def _find_title_line(text: str) -> str:
    lines = str(text or "").split("\n")[:20]
    for idx, raw in enumerate(lines):
        line = _clean_title_line(raw)
        if not line:
            continue
        folded = _fold_text(line)
        if folded.startswith(("chung toi", "toi la", "dieu ", "ben ", "ong ", "ba ")):
            break
        if folded in ("van ban", "hop dong") and idx + 1 < len(lines):
            subtitle = _clean_title_line(lines[idx + 1])
            if subtitle:
                return f"{line} {subtitle}"
        if folded.startswith(("hop dong ", "van ban ")) and idx + 1 < len(lines):
            subtitle = _clean_title_line(lines[idx + 1])
            subtitle_folded = _fold_text(subtitle)
            if subtitle_folded.startswith(
                ("quyen ", "nha o ", "tai san ", "ve viec ", "phan chia ", "tu choi ", "tang cho ")
            ):
                return f"{line} {subtitle}"
        if folded.startswith(
            (
                "hop dong ",
                "van ban ",
                "thoa thuan ",
                "giay ",
                "don ",
                "to khai ",
                "di chuc",
                "phu luc ",
                "danh sach ",
                "bien ban ",
                "thong bao ",
                "giao dich ",
            )
        ):
            return line
    return ""


def _detect_document_kind_and_title(text: str) -> tuple[str, str]:
    title_line = _clean_title_line(_find_title_line(text))
    title_fold = _fold_text(title_line)

    # Trang phu "Lời chứng chứng thực văn bản ..." chi xac nhan chu ky —
    # khong mang nguoi chet/tai san, ap luat generic thay vi loai noi trang.
    if title_fold.startswith("loi chung"):
        return DOC_KIND_GENERIC, title_line

    if "cam ket tai san rieng" in title_fold:
        return DOC_KIND_ASSET_COMMITMENT, title_line

    if any(
        marker in title_fold
        for marker in (
            "van ban tu choi nhan di san",
            "tu choi nhan di san",
            "tu choi quyen huong di san",
            "tu choi di san",
        )
    ):
        return DOC_KIND_INHERITANCE_REFUSAL, title_line

    if any(
        marker in title_fold
        for marker in (
            "van ban khai nhan di san",
            "khai nhan di san thua ke",
            "bien ban khai nhan di san",
        )
    ):
        return DOC_KIND_INHERITANCE_DECLARATION, title_line

    if any(
        marker in title_fold
        for marker in (
            "van ban phan chia di san",
            "thoa thuan phan chia di san",
            "phan chia thua ke",
            "phan chia di san thua ke",
        )
    ):
        return DOC_KIND_INHERITANCE_PARTITION, title_line

    is_transfer_cancellation = (
        ("huy bo" in title_fold or "huy hop dong" in title_fold)
        and (
            "hop dong chuyen nhuong" in title_fold
            or "chuyen nhuong quyen su dung dat" in title_fold
        )
    )
    if is_transfer_cancellation:
        return DOC_KIND_TRANSFER_CANCELLATION, title_line

    if "hop dong chuyen nhuong" in title_fold:
        return DOC_KIND_TRANSFER, title_line

    if "hop dong tang cho" in title_fold or "giao dich tang cho" in title_fold:
        return DOC_KIND_GIFT, title_line

    if "hop dong the chap" in title_fold:
        return DOC_KIND_MORTGAGE, title_line

    if title_line:
        return DOC_KIND_GENERIC, title_line
    return DOC_KIND_GENERIC, ""


def _extract_block_by_patterns(text: str, start_patterns: Iterable[str], end_patterns: Iterable[str]) -> str:
    match = _find_first_pattern_match_generic(text, start_patterns)
    if not match:
        return ""

    start_idx = int(match[0])
    end_idx = len(text)
    for pattern in (*end_patterns, *_UNIVERSAL_ASSET_END_PATTERNS):
        end_match = re.search(pattern, text[start_idx:], re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if not end_match:
            continue
        candidate_end = start_idx + end_match.start()
        if candidate_end > start_idx and candidate_end < end_idx:
            end_idx = candidate_end

    raw = text[start_idx:end_idx].strip()
    if not raw:
        return ""
    raw = unicodedata.normalize("NFC", raw)
    lines = [re.sub(r"\s+", " ", line).strip(" ;,") for line in raw.split("\n") if line.strip()]
    return "\n".join(lines).strip()


def _extract_block_by_folded_patterns(text: str, start_patterns: Iterable[str], end_patterns: Iterable[str]) -> str:
    source = str(text or "")
    if not source:
        return ""

    folded_text, index_map = _fold_text_with_index_map(source)
    if not folded_text or not index_map:
        return ""

    best_match = None
    for pattern in start_patterns:
        match = re.search(pattern, folded_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if not match:
            continue
        if best_match is None or match.start() < best_match.start():
            best_match = match

    if not best_match:
        return ""

    start_fold_idx = best_match.start()
    start_idx = index_map[start_fold_idx]
    end_idx = len(source)

    for pattern in (*end_patterns, *_UNIVERSAL_ASSET_END_PATTERNS_FOLDED):
        end_match = re.search(pattern, folded_text[best_match.end():], re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if not end_match:
            continue
        candidate_fold_idx = best_match.end() + end_match.start()
        if candidate_fold_idx <= start_fold_idx:
            continue
        candidate_end = index_map[candidate_fold_idx]
        if candidate_end > start_idx and candidate_end < end_idx:
            end_idx = candidate_end

    raw = source[start_idx:end_idx].strip()
    if not raw:
        return ""
    raw = unicodedata.normalize("NFC", raw)
    lines = [re.sub(r"\s+", " ", line).strip(" ;,") for line in raw.split("\n") if line.strip()]
    return "\n".join(lines).strip()


_UNIVERSAL_ASSET_END_PATTERNS = (
    r"(?m)^\s*LỜI CHỨNG\b",
    r"(?m)^\s*Số công chứng\b",
    r"(?m)^\s*(?:NGƯỜI|CÁC BÊN|BÊN)\s+(?:KÝ|ĐIỂM CHỈ|LẬP|YÊU CẦU)\b",
)

_UNIVERSAL_ASSET_END_PATTERNS_FOLDED = (
    r"(?m)^\s*loi chung\b",
    r"(?m)^\s*so cong chung\b",
    r"(?m)^\s*(?:nguoi|cac ben|ben)\s+(?:ky|diem chi|lap|yeu cau)\b",
)


def _find_tai_san_generic(text: str) -> str:
    return _extract_block_by_patterns(
        text,
        (
            r"(?m)^\s*(?:1\.1\s*)?\u0110\u1ed1i t\u01b0\u1ee3ng c\u1ee7a H\u1ee3p \u0111\u1ed3ng n\u00e0y l\u00e0\b",
            r"(?m)^\s*\u0110I\u1ec0U\s*1\b",
        ),
        (
            r"(?m)^\s*1\.2\b",
            r"(?m)^\s*B\u1eb1ng H\u1ee3p \u0111\u1ed3ng n\u00e0y\b",
            r"(?m)^\s*\u0110I\u1ec0U\s*2\b",
            r"(?m)^\s*Gi\u00e1 chuy\u1ec3n nh\u01b0\u1ee3ng\b",
            r"(?m)^\s*Ph\u01b0\u01a1ng th\u1ee9c thanh to\u00e1n\b",
        ),
    )


def _find_tai_san_qsdd_common(text: str) -> str:
    return _extract_block_by_folded_patterns(
        text,
        (
            r"quyen su dung dat(?: va tai san gan lien voi dat)?[^\n]{0,250}?co dia chi tai\s*:?",
            r"nha o va quyen su dung dat o[^\n]{0,250}?co dia chi tai\s*:?",
            r"chu so huu nha o va quyen su dung dat o[^\n]{0,250}?co dia chi tai\s*:?",
        ),
        (
            r"(?m)^\s*1\.2\b",
            r"(?m)^\s*dieu\s*2\b",
            r"(?m)^\s*\d+\.\s*gia chuyen nhuong\b",
            r"(?m)^\s*bang hop dong nay\b",
            r"(?m)^\s*bang van ban nay chung toi xac dinh\b",
            r"(?m)^\s*hai vo chong chung toi cam ket\b",
            r"(?m)^\s*hai vo chong chung toi cam doan\b",
            r"(?m)^\s*chung toi cong nhan\b",
            r"(?m)^\s*gia chuyen nhuong\b",
            r"(?m)^\s*phuong thuc thanh toan\b",
            r"\bva duoc cong chung vien\b",
            r"\bva duoc[\s\S]{0,120}?chung nhan\b",
            r"\bso cong chung\b",
        ),
    )


def _find_tai_san_from_mortgage_title(text: str) -> str:
    title = _find_title_line(text)
    folded, index_map = _fold_text_with_index_map(title)
    match = re.match(r"^\s*hop\s+dong\s+the\s+chap\s+(.+)$", folded)
    if not match or not index_map:
        return ""
    return title[index_map[match.start(1)]:].strip()


def _find_tai_san_inheritance_partition(text: str) -> str:
    return _extract_block_by_folded_patterns(
        text,
        (
            r"quyen su dung dat(?: cua[^\n]{0,120})?[^\n]{0,250}?(?:co dia chi(?: tai)?|tai dia chi)\s*:?",
            r"nha o va quyen su dung dat o(?: cua[^\n]{0,120})?[^\n]{0,250}?(?:co dia chi(?: tai)?|tai dia chi)\s*:?",
            r"phan quyen su dung dat(?: cua[^\n]{0,200})?[^\n]{0,300}?(?:co dia chi(?: tai)?|tai dia chi)\s*:?",
            r"quyen su dung dat[^\n]{0,300}?theo giay chung nhan",
            r"thua dat so[^\n]{0,200}?(?:co dia chi tai|tai dia chi|theo giay chung nhan|theo ban do)",
        ),
        (
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?(?:\|\s*)?nguoi thua ke\s*:",
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?(?:\|\s*)?nhung nguoi thua ke\b",
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?(?:\|\s*)?nhung nguoi nhan thua ke\b",
            r"(?m)^\s*noi dung phan chia di san\b",
            r"(?m)^\s*thong nhat phan chia\b",
            r"(?m)^\s*bang van ban nay\b",
            r"(?m)^\s*nhung nguoi huong di san\b",
            r"(?m)^\s*loi chung\b",
        ),
    )


def _find_tai_san_inheritance_refusal(text: str) -> str:
    return _extract_block_by_folded_patterns(
        text,
        (
            r"(?m)^\s*(?:1\.\s*)?tai san(?: thu nhat)?\s*:",
            r"quyen su dung dat(?: cua[^\n]{0,120})?[^\n]{0,250}?(?:co dia chi(?: tai)?|tai dia chi)\s*:?",
            r"phan quyen su dung dat(?: cua[^\n]{0,200})?[^\n]{0,300}?(?:co dia chi(?: tai)?|tai dia chi)\s*:?",
        ),
        (
            r"(?m)^\s*bang van ban nay\b",
            r"(?m)^\s*toi xin cam doan\b",
            r"(?m)^\s*nguoi tu choi huong di san\b",
            r"(?m)^\s*loi chung\b",
        ),
    )


def _find_tai_san_insurance(text: str) -> str:
    """Khoi QUYEN LOI BAO HIEM trong van ban thua ke."""
    return _extract_block_by_folded_patterns(
        text,
        (
            r"quyen loi bao hiem",
        ),
        (
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?(?:\|\s*)?nguoi thua ke\s*:",
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?(?:\|\s*)?nhung nguoi (?:thua ke|nhan thua ke)\b",
            r"(?m)^\s*noi dung (?:phan chia|thoa thuan phan chia|khai nhan) di san\b",
            r"(?m)^\s*bang van ban nay\b",
            r"(?m)^\s*(?:chung toi|toi) xin cam doan\b",
            r"(?m)^\s*nguoi (?:tu choi huong|huong) di san\b",
            r"(?m)^\s*loi chung\b",
        ),
    )


def tach_danh_sach_bao_hiem(tai_san: str) -> list[dict]:
    """Moi quyen loi bao hiem 1 dong: so hop dong, ben bao hiem,
    ben mua, doi tuong, ngay ky."""
    block = unicodedata.normalize("NFC", str(tai_san or ""))
    if not block.strip():
        return []
    entries: list[dict] = []
    current: dict | None = None

    for raw_line in block.split("\n"):
        line = raw_line.strip()
        if not line or "bảo hiểm" not in line and "Bảo hiểm" not in line:
            if current is not None and line:
                extra = current.get("mo_ta", "")
                if line not in extra:
                    current["mo_ta"] = f"{extra} {line}".strip()
            continue
        # Dong "Ben mua / Doi tuong" bo sung cho quyen loi dang mo (khong
        # mo dong moi khi chua co so hop dong).
        has_so = bool(re.search(r"(?i)\bs\u1ed1\s*[0-9]", line))
        if current is not None and not has_so and current["so_hop_dong"]:
            current["mo_ta"] = f"{current['mo_ta']} {line}".strip()
        else:
            current = {
                "loai_quyen_loi": "",
                "so_hop_dong": "",
                "ben_bao_hiem": "",
                "ben_mua": "",
                "doi_tuong": "",
                "ngay_ky": "",
                "mo_ta": line,
            }
            entries.append(current)
        loai_match = re.search(r"(?i)(Quy\u1ec1n l\u1ee3i b\u1ea3o hi\u1ec3m[^\n:]*|H\u1ee3p \u0111\u1ed3ng b\u1ea3o hi\u1ec3m[^\n]*?)(?:\s+s\u1ed1\b|$)", line)
        if loai_match:
            current["loai_quyen_loi"] = _clean_asset_cell(loai_match.group(1))
        so_match = re.search(r"(?i)\bs\u1ed1\s*([0-9][A-Z0-9.\-]{5,40})", line)
        if so_match:
            current["so_hop_dong"] = so_match.group(1).strip()
        mua_match = re.search(r"(?i)B\u00ean mua b\u1ea3o hi\u1ec3m:\s*([^\n]+)", line)
        if mua_match and not current["ben_mua"]:
            current["ben_mua"] = _clean_asset_cell(mua_match.group(1))
        dt_match = re.search(
            r"(?i)\u0110\u1ed1i t\u01b0\u1ee3ng b\u1ea3o hi\u1ec3m[^\n:]*:\s*([^\n]+)", line
        )
        if dt_match and not current["doi_tuong"]:
            current["doi_tuong"] = _clean_asset_cell(dt_match.group(1))
        ngay_match = re.search(r"ng\u00e0y\s*(\d{1,2}/\d{1,2}/\d{4})", line)
        if ngay_match and not current["ngay_ky"]:
            current["ngay_ky"] = ngay_match.group(1)
        ky_match = re.search(r"(?i)k\u00fd gi\u1eefa\s+(.+?)\s+ng\u00e0y\s*\d{1,2}/\d{1,2}/\d{4}", line)
        if ky_match:
            ben = _clean_asset_cell(ky_match.group(1))
            mua = current["ben_mua"]
            if mua and ben.endswith(mua):
                ben = ben[: -len(mua)].strip()
                ben = re.sub(r"(?i)\s*v\u00e0\s*$", "", ben).strip()
            current["ben_bao_hiem"] = ben
    known_mua = [entry["ben_mua"] for entry in entries if entry["ben_mua"]]
    for entry in entries:
        if not entry["ben_mua"] and known_mua:
            entry["ben_mua"] = known_mua[0]
        mua = entry["ben_mua"]
        ben = entry["ben_bao_hiem"]
        if mua and ben.endswith(mua):
            ben = ben[: -len(mua)].strip()
            entry["ben_bao_hiem"] = re.sub(r"(?i)\s*và\s*$", "", ben).strip()
    return [entry for entry in entries if entry["so_hop_dong"] or entry["ben_mua"] or entry["doi_tuong"]]


def _find_tai_san_savings(text: str) -> str:
    """Khoi tai san SO TIET KIEM / TAI KHOAN trong van ban thua ke."""
    return _extract_block_by_folded_patterns(
        text,
        (
            r"so tiet kiem",
            r"so du tai khoan",
            r"so tien goc va lai",
        ),
        (
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?(?:\|\s*)?nhung nguoi (?:thua ke|nhan thua ke)\b",
            r"(?m)^\s*noi dung (?:phan chia|thoa thuan phan chia|khai nhan) di san\b",
            r"(?m)^\s*bang van ban nay\b",
            r"(?m)^\s*(?:chung toi|toi) xin cam doan\b",
            r"(?m)^\s*nguoi (?:tu choi huong|huong) di san\b",
            r"(?m)^\s*loi chung\b",
        ),
    )


def tach_danh_sach_so_tiet_kiem(tai_san: str) -> list[dict]:
    """Moi so tiet kiem / tai khoan 1 dong: số hiệu, ngan hang, chi nhánh,
    ngay phát hành, chu so."""
    block = unicodedata.normalize("NFC", str(tai_san or ""))
    if not block.strip():
        return []
    entries: list[dict] = []
    current: dict | None = None

    def new_entry(loai: str) -> dict:
        return {
            "loai_so": loai,
            "so_hieu": "",
            "ngan_hang": "",
            "chi_nhanh": "",
            "ngay_phat_hanh": "",
            "chu_so": "",
            "mo_ta": "",
        }

    for raw_line in block.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        folded = _fold_text(line)
        la_tai_khoan = "tai khoan" in folded and (
            "so tai khoan" in folded
            or "so hieu tai khoan" in folded
            or "chu tai khoan" in folded
            or "ngay mo tai khoan" in folded
            or "xac nhan" in folded
        )
        if la_tai_khoan:
            stk_match = re.search(r"(?i)(?:s\u1ed1 t\u00e0i kho\u1ea3n|s\u1ed1 hi\u1ec7u t\u00e0i kho\u1ea3n):?\s*(\d{6,20})", line)
            if current is None or (stk_match and current["so_hieu"]):
                current = new_entry("tài khoản")
                entries.append(current)
                current["mo_ta"] = line
            elif line not in current["mo_ta"]:
                current["mo_ta"] = f"{current['mo_ta']} {line}".strip()
            if stk_match and not current["so_hieu"]:
                current["so_hieu"] = stk_match.group(1)
            chu_tk = re.search(r"(?i)(?:mang t\u00ean|ch\u1ee7 t\u00e0i kho\u1ea3n)\s*:?\s*([^\n,.]+)", line)
            if chu_tk and not current["chu_so"]:
                current["chu_so"] = _clean_asset_cell(chu_tk.group(1))
            mo_tk = re.search(r"(?i)ng\u00e0y m\u1edf t\u00e0i kho\u1ea3n\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})", line)
            if mo_tk and not current["ngay_phat_hanh"]:
                current["ngay_phat_hanh"] = mo_tk.group(1)
            ten_match = re.search(r"(?i)mang t\u00ean\s+([^\n,.]+)", line)
            if ten_match and not current["chu_so"]:
                current["chu_so"] = _clean_asset_cell(ten_match.group(1))
            bank_match = re.search(
                r"(?i)\bdo\s+(.+?)(?=\s+(?:chi nhánh|số hiệu|số tài khoản|phát hành|xác nhận|như sau)|$)",
                line,
            )
            if not bank_match:
                bank_match = re.search(
                    r"(?i)\bc\u1ee7a\s+(Ng\u00e2n h\u00e0ng[^\n]+?)(?=\s*[–-]\s*|\s+ng\u00e0y\s+\d|$)",
                    line,
                )
            if bank_match and not current["ngan_hang"]:
                current["ngan_hang"] = re.sub(r"\s*[-\u2013\u2014]\s*$", "", _clean_asset_cell(bank_match.group(1)))
            branch_match = re.search(
                r"(?i)chi nh\u00e1nh\s+(.+?)(?=\s+(?:số hiệu|số tài khoản|phát hành|xác nhận|như sau)|$)",
                line,
            )
            if branch_match and not current["chi_nhanh"]:
                current["chi_nhanh"] = re.sub(r"\s*[-\u2013\u2014]\s*$", "", _clean_asset_cell(branch_match.group(1)))
            continue
        if "so tiet kiem" not in folded and "the tiet kiem" not in folded:
            if current is not None:
                extra_hieu = re.search(r"(?i)(?:s\u1ed1 hi\u1ec7u|s\u1ed1(?!\s*(?:t\u00e0i kho\u1ea3n|ti\u1ec1n)))\s*:?\s*([A-Za-z]{1,3}\s*\d{6,14}|\d{7,20})", line)
                if extra_hieu and not current["so_hieu"]:
                    current["so_hieu"] = _clean_asset_cell(extra_hieu.group(1))
                extra_ngay = re.search(
                    r"(?i)ph\u00e1t h\u00e0nh ng\u00e0y\s*(\d{1,2}/\d{1,2}/\d{4})", line
                )
                if extra_ngay and not current["ngay_phat_hanh"]:
                    current["ngay_phat_hanh"] = extra_ngay.group(1)
            continue
        current = new_entry("sổ tiết kiệm")
        entries.append(current)
        current["mo_ta"] = line
        ky_han = re.search(r"(?i)S\u1ed5 ti\u1ebft ki\u1ec7m\s+(c\u00f3 k\u1ef3 h\u1ea1n|kh\u00f4ng k\u1ef3 h\u1ea1n)", line)
        if ky_han:
            current["loai_so"] = f"sổ tiết kiệm ({ky_han.group(1).lower()})"
        bank_match = re.search(
            r"(?i)\bdo\s+(.+?)(?=\s+(?:chi nhánh|số hiệu|phát hành|như sau)|$)",
            line,
        )
        if bank_match:
            current["ngan_hang"] = re.sub(r"\s*[-\u2013\u2014]\s*$", "", _clean_asset_cell(bank_match.group(1)))
        branch_match = re.search(
            r"(?i)chi nh\u00e1nh\s+(.+?)(?=\s+(?:số hiệu|phát hành|như sau)|$)",
            line,
        )
        if branch_match:
            current["chi_nhanh"] = re.sub(r"\s*[-\u2013\u2014]\s*$", "", _clean_asset_cell(branch_match.group(1)))
        hieu_match = re.search(r"(?i)(?:s\u1ed1 hi\u1ec7u|s\u1ed1(?!\s*(?:t\u00e0i kho\u1ea3n|ti\u1ec1n)))\s*:?\s*([A-Za-z]{1,3}\s*\d{6,14}|\d{7,20})", line)
        if hieu_match:
            current["so_hieu"] = _clean_asset_cell(hieu_match.group(1))
        ngay_match = re.search(
            r"(?i)ph\u00e1t h\u00e0nh ng\u00e0y\s*(\d{1,2}/\d{1,2}/\d{4})", line
        )
        if ngay_match:
            current["ngay_phat_hanh"] = ngay_match.group(1)
        chu_match = re.search(r"(?i)\b(?:cho|mang t\u00ean)\s+(?:\u00f4ng|b\u00e0|anh|ch\u1ecb)?\s*:?\s*([^\n,;.]+)", line)
        if chu_match:
            current["chu_so"] = _clean_asset_cell(chu_match.group(1))
    return entries


def _find_tai_san_by_kind(text: str, doc_kind: str) -> str:
    if doc_kind in (DOC_KIND_INHERITANCE_PARTITION, DOC_KIND_INHERITANCE_DECLARATION):
        tai_san = _find_tai_san_inheritance_partition(text)
        if tai_san:
            return tai_san
        savings = _find_tai_san_savings(text)
        if savings:
            return savings
        return _find_tai_san_insurance(text)

    if doc_kind == DOC_KIND_INHERITANCE_REFUSAL:
        tai_san = _find_tai_san_inheritance_refusal(text)
        if tai_san:
            return tai_san
        savings = _find_tai_san_savings(text)
        if savings:
            return savings
        return _find_tai_san_insurance(text)

    if doc_kind in (DOC_KIND_TRANSFER, DOC_KIND_GIFT):
        common_qsdd_block = _find_tai_san_qsdd_common(text)
        if common_qsdd_block:
            return common_qsdd_block
        tai_san = _extract_block_by_patterns(
            text,
            (r"(?m)^\s*(?:1\.1\s*)?\u0110\u1ed1i t\u01b0\u1ee3ng c\u1ee7a H\u1ee3p \u0111\u1ed3ng n\u00e0y l\u00e0\b",),
            (
                r"(?m)^\s*1\.2\b",
                r"(?m)^\s*B\u1eb1ng H\u1ee3p \u0111\u1ed3ng n\u00e0y\b",
                r"(?m)^\s*\u0110I\u1ec0U\s*2\b",
                r"(?m)^\s*Gi\u00e1 chuy\u1ec3n nh\u01b0\u1ee3ng\b",
                r"(?m)^\s*Ph\u01b0\u01a1ng th\u1ee9c thanh to\u00e1n\b",
            ),
        )
        if tai_san:
            return tai_san

    if doc_kind == DOC_KIND_ASSET_COMMITMENT:
        tai_san = _extract_block_by_patterns(
            text,
            (
                r"(?m)^\s*(?:\u00d4ng|B\u00e0)[^\n]{0,200}?hi\u1ec7n \u0111ang s\u1edf h\u1eefu\s+T\u00e0i\s*S\u1ea3n\s+l\u00e0\b",
                r"(?m)^\s*T\u00e0i\s*S\u1ea3n\s+l\u00e0\b",
            ),
            (
                r"(?m)^\s*B\u1eb1ng v\u0103n b\u1ea3n n\u00e0y ch\u00fang t\u00f4i x\u00e1c \u0111\u1ecbnh\b",
                r"(?m)^\s*Hai v\u1ee3 ch\u1ed3ng ch\u00fang t\u00f4i cam \u0111oan\b",
                r"(?m)^\s*Ch\u00fang t\u00f4i c\u00f4ng nh\u1eadn\b",
            ),
        )
        if tai_san:
            return tai_san

    if doc_kind == DOC_KIND_TRANSFER_CANCELLATION:
        tai_san = _extract_block_by_patterns(
            text,
            (
                r"(?:mua b\u00e1n nh\u00e0 \u1edf v\u00e0\s+)?chuy\u1ec3n nh\u01b0\u1ee3ng quy\u1ec1n s\u1eed d\u1ee5ng \u0111\u1ea5t(?:\s+v\u00e0\s+t\u00e0i\s+s\u1ea3n\s+g\u1eafn\s+li\u1ec1n\s+v\u1edbi\s+\u0111\u1ea5t)?[^.\n]{0,200}?c\u00f3 \u0111\u1ecba ch\u1ec9 t\u1ea1i:\s*",
            ),
            (
                r"\bv\u00e0 \u0111\u01b0\u1ee3c C\u00f4ng ch\u1ee9ng vi\u00ean\b",
                r"\bv\u00e0 \u0111\u01b0\u1ee3c[^.\n]{0,120}?ch\u1ee9ng nh\u1eadn\b",
                r"\bs\u1ed1 c\u00f4ng ch\u1ee9ng\b",
            ),
        )
        if tai_san:
            return tai_san

    if doc_kind == DOC_KIND_MORTGAGE:
        tai_san = _find_tai_san_qsdd_common(text)
        if tai_san:
            return tai_san
        return _find_tai_san_from_mortgage_title(text)

    common_qsdd_block = _find_tai_san_qsdd_common(text)
    if common_qsdd_block:
        return common_qsdd_block

    return _find_tai_san_generic(text)


def guess_nhom_hd(ten_hd):
    lower = _fold_text(ten_hd)
    for kw, nhom in NHOM_HD_MAP.items():
        if _fold_text(kw) in lower:
            return nhom
    return "Khác"


LAND_CERTIFICATE_HEADING_NOISE_PATTERNS = (
    r"giay chung nhan quyen su dung dat\s*,?\s*quyen so huu nha o va tai san khac gan lien voi dat",
    r"giay chung nhan quyen su dung dat\s*,?\s*quyen so huu tai san gan lien voi dat",
    r"giay chung nhan quyen su dung dat\s*,?\s*quyen so huu nha o",
)

LAND_WITH_ASSET_TITLE_MARKERS = (
    "quyen su dung dat va tai san gan lien voi dat",
    "nha o va quyen su dung dat o",
    "mua ban nha o",
)

LAND_ATTACHED_ASSET_DETAIL_PATTERNS = (
    r"\bnha o\b\s*:",
    r"\bquyen so huu nha o\b",
    r"\bnha o va quyen su dung dat o\b",
    r"\bcong trinh xay dung\b\s*:",
    r"\btai san gan lien voi dat\b\s*:",
    r"\btai san khac gan lien voi dat\b\s*:",
    r"\bdien tich xay dung\b",
    r"\bdien tich san\b",
    r"\bket cau\b",
    r"\bso tang\b",
    r"\bhinh thuc so huu\b",
    r"\bcap \(hang\)\b",
    r"\bcap cong trinh\b",
)


def _strip_land_certificate_heading_noise(text_folded: str) -> str:
    cleaned = str(text_folded or "")
    for pattern in LAND_CERTIFICATE_HEADING_NOISE_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def _has_attached_land_asset_details(text_folded: str) -> bool:
    cleaned = _strip_land_certificate_heading_noise(text_folded)
    return any(
        re.search(pattern, cleaned, re.IGNORECASE)
        for pattern in LAND_ATTACHED_ASSET_DETAIL_PATTERNS
    )


def guess_loai_tai_san(tai_san, ten_hd):
    tai_san_fold = _fold_text(tai_san)
    title_fold = _fold_text(ten_hd)
    combined = f"{tai_san_fold} {title_fold}".strip()

    if "quyen su dung dat" in combined:
        if any(marker in title_fold for marker in LAND_WITH_ASSET_TITLE_MARKERS):
            return "Đất đai có tài sản"
        if _has_attached_land_asset_details(tai_san_fold):
            return "Đất đai có tài sản"
        return "Đất đai không có tài sản"

    keywords = [
        ("o to", "Ô tô"),
        ("xe may", "Xe máy"),
        ("tau", "Tàu, thuyền"),
        ("thuyen", "Tàu, thuyền"),
        ("so tiet kiem", "Sổ tiết kiệm"),
        ("co phan", "Cổ phần"),
        ("co phieu", "Cổ phiếu"),
        ("chung khoan", "Chứng khoán"),
        ("the atm", "Thẻ ATM"),
    ]
    for kw, loai in keywords:
        if kw in combined:
            return loai
    return "Tài sản khác"


# ============================================================
# TACH MOI THUA DAT THANH 1 DONG TAI SAN RIENG
# Quyet dinh cua owner 05/10/2026: tai san nhieu thua thi tach rieng.
# Nguyen tac: dong nao co so thua (khac "_" , khac rong) thi mo thua moi;
# dong "Trong do" / dong khong co so thua thi gan vao thua dang mo
# (chi_tiet_dien_tich) — giu du lieu, khong tu bia danh tinh thua.
# ============================================================
_THUA_TABLE_DEFAULT_ORDER = ("to", "thua", "dien_tich", "muc_dich", "thoi_han", "ghi_them")


def _clean_asset_cell(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ;,.\u2013-")


def _map_asset_table_columns(header_line: str) -> tuple:
    order: list = []
    for cell in header_line.split("|"):
        folded = _fold_text(cell)
        if "to ban do" in folded or "to so" in folded:
            order.append("to")
        elif "thua" in folded:
            order.append("thua")
        elif "dien tich" in folded:
            order.append("dien_tich")
        elif "muc dich" in folded:
            order.append("muc_dich")
        elif "thoi gian" in folded or "thoi han" in folded:
            order.append("thoi_han")
        elif "ghi them" in folded or "phan ghi" in folded:
            order.append("ghi_them")
        else:
            order.append("")
    return tuple(order)


def _tach_ngu_canh_gcn(tai_san: str) -> dict:
    block = unicodedata.normalize("NFC", str(tai_san or ""))
    context = {
        "so_gcn": "",
        "so_gcn_raw": "",
        "loai_gcn": "",
        "so_vao_so": "",
        "dia_chi": "",
        "ngay_cap_gcn": "",
        "co_quan_cap": "",
    }
    gcn_match = re.search(
        r"(?i)(?:ch\u1ee9ng nh\u1eadn|GCN)[^\n]{0,100}?(?:s\u1ed1\s*:?\s*|\u0111\u1ea5t\s*:?\s*)([A-Za-z\u0110\u0111]{1,3})\s*(\d{6,8})",
        block,
    )
    if gcn_match:
        context["so_gcn_raw"] = f"{gcn_match.group(1)} {gcn_match.group(2)}"
        context["so_gcn"] = (gcn_match.group(1) + gcn_match.group(2)).upper()
    loai_match = re.search(
        r"(?i)Gi\u1ea5y ch\u1ee9ng nh\u1eadn\s+(.+?)\s+s\u1ed1\s*:?\s*[A-Za-z]{1,3}\s*\d{6,8}",
        block,
    )
    if loai_match:
        context["loai_gcn"] = _clean_asset_cell(loai_match.group(1))
    vao_so_match = re.search(
        r"(?i)(?:v\u00e0o s\u1ed5|v\u00e0o s\u1ed1)[^\n:]{0,60}?s\u1ed1\s+([A-Z0-9][^\n,;]*?)(?=\s+ng\u00e0y\s+\d|\s+do\s+|\s*$)",
        block,
    )
    if vao_so_match:
        so_vao_so = _clean_asset_cell(vao_so_match.group(1))
        # Cat tu thua rot ("...887QD-UB huyen" -> "...887QD-UB"): token cuoi
        # khong chua so thi cat, lap den khi token cuoi co so.
        while " " in so_vao_so and not re.search(r"\d", so_vao_so.rsplit(" ", 1)[-1]):
            so_vao_so = so_vao_so.rsplit(" ", 1)[0].strip()
        context["so_vao_so"] = so_vao_so
    dia_chi_match = re.search(
        r"(?i)(?:c\u00f3 \u0111\u1ecba ch\u1ec9 t\u1ea1i|t\u1ea1i \u0111\u1ecba ch\u1ec9)\s*:?\s*(.+?)(?=\s+theo\s+[A-Z]|\s+theo\s+Gi\u1ea5y|$)",
        block,
    )
    if dia_chi_match:
        context["dia_chi"] = _clean_asset_cell(dia_chi_match.group(1))
    cap_match = re.search(
        r"(?i)do\s+([^\n]+?)\s+(?:c\u1ea5p|k\u00fd)\s+ng\u00e0y\s*(\d{1,2}/\d{1,2}/\d{4})",
        block,
    )
    if cap_match:
        context["co_quan_cap"] = _clean_asset_cell(cap_match.group(1))
        context["ngay_cap_gcn"] = cap_match.group(2)
    return context


def _new_thua_dat(context: dict) -> dict:
    return {
        "so_thua_dat": "",
        "so_to_ban_do": "",
        "dien_tich": "",
        "muc_dich_su_dung": "",
        "thoi_han_su_dung": "",
        "phan_ghi_them": "",
        "nguon_goc": "",
        "dia_chi": context.get("dia_chi", ""),
        "loai_gcn": context.get("loai_gcn", ""),
        "so_gcn": context.get("so_gcn", ""),
        "so_gcn_raw": context.get("so_gcn_raw", ""),
        "so_vao_so": context.get("so_vao_so", ""),
        "ngay_cap_gcn": context.get("ngay_cap_gcn", ""),
        "co_quan_cap": context.get("co_quan_cap", ""),
        "chi_tiet_dien_tich": [],
    }


def _is_pure_number_cell(value: str) -> bool:
    return bool(re.match(r"^\d+(?:[.,]\d+)*$", (value or "").strip()))


def _clean_so_to_ban_do(value: str) -> str:
    """So to ban do chi giu so/ky hieu — cat phan mo ta theo sau
    ("05, Bản đồ địa chính năm 1991" -> "05"). Chi cat khi "bản đồ"
    di kem mo ta (địa chính/lập/năm) — khong cat cum hop le
    "tờ bản đồ số 107" trong "(nay là tờ bản đồ số 107)"."""
    cut = re.split(
        r",|\s+(?i:b\u1ea3n \u0111\u1ed3)\s+(?:\u0111\u1ecba ch\u00ednh|l\u1eadp|n\u0103m)\b|\s*\(?\s*(?:hi\u1ec7n nay|nay)\s+l\u00e0\b",
        str(value or ""), maxsplit=1,
    )[0]
    return cut.strip(" ;,.")


def _cell_has_letters(value: str) -> bool:
    return bool(re.search(r"[A-Za-zÀ-ỹ]", value or ""))


def _tach_nay_la(value: str) -> tuple[str, str]:
    """Cat duoi "(nay la to ban do so N)"/"nay la thua dat so N" ra ghi chu
    — tra (ky hieu dau, ghi chu). Vi du "104 Nay la thua dat so 321" ->
    ("104", "Nay la thua dat so 321")."""
    text = str(value or "")
    match = re.search(
        r"(?i)\s*(\((?:(?:\u0111\u01b0\u1ee3c|\u0111\u00e3)\s+)?(?:t\u00e1ch|g\u1ed9p|s\u00e1p|nh\u1eadp|chia|h\u1ee3p|t\u0103ng|gi\u1ea3m)[^)]*\)?"
        r"|(?:\u0111\u01b0\u1ee3c|\u0111\u00e3)\s+(?:t\u00e1ch|g\u1ed9p|s\u00e1p|nh\u1eadp|chia|h\u1ee3p)\s+t\u1eeb\b.*"
        r"|\(?\s*(?:hi\u1ec7n nay|nay)\s+l\u00e0\b[^)]*\)?)\s*$",
        text,
    )
    if not match:
        return text.strip(" ;,.-"), ""
    head = text[: match.start()].strip(" ;,.-(")
    return head, match.group(1).strip(" ;,.-")


def _tach_thua_cell_stream(cells: list[str], context: dict, parcels: list[dict]) -> bool:
    """Tach dong bang don (nhieu o, co ca tieu de + du lieu, gap o .doc
    doc bang IFilter). Tra True neu an duoc it nhat 1 thua.
    Quy tac: bo thu tuc tieu de sau o "Phan ghi them"/"Muc dich";
    bo 3 o so dau (to, thua, tong DT) la thua moi; cum (DT, loai dat,
    thoi han) sau "Trong do" la chi tiet; gap "2.2."/chu thuong thi dung.
    """
    anchor = None
    for idx, cell in enumerate(cells):
        if "so thua" in _fold_text(cell):
            anchor = idx
            break
    if anchor is None:
        return False
    # Tieu de co the thua o trong ("( m2)", "Thoi han su dung", ...) —
    # di qua het cac o tieu de moi toi du lieu.
    header_words = ("so thua", "so to", "dien tich", "muc dich", "thoi han", "phan ghi", "ghi them", "( m2)", "m2)")
    last_header = anchor
    for idx in range(anchor + 1, len(cells)):
        folded = _fold_text(cells[idx])
        if not folded.strip():
            last_header = idx
            continue
        if any(word in folded for word in header_words):
            last_header = idx
            continue
        break
    start = last_header + 1
    data = [cell for cell in cells[start:] if cell.strip()]
    pos = 0
    current: dict | None = None
    if (
        pos + 2 < len(data)
        and re.search(r"\d", data[pos])
        and _is_pure_number_cell(data[pos + 1])
        and _is_pure_number_cell(data[pos + 2])
    ):
        current = _new_thua_dat(context)
        to_head, to_note = _tach_nay_la(data[pos])
        thua_head, thua_note = _tach_nay_la(data[pos + 1])
        current["so_to_ban_do"] = _clean_so_to_ban_do(to_head)
        current["so_thua_dat"] = thua_head
        current["dien_tich"] = data[pos + 2]
        _ghi_nay = "; ".join(n for n in (to_note, thua_note) if n)
        if _ghi_nay:
            current["phan_ghi_them"] = _ghi_nay
        parcels.append(current)
        pos += 3
    else:
        return False
    while pos < len(data):
        folded = _fold_text(data[pos])
        if folded in ("trong do", "trong do:") or folded.startswith("trong do"):
            pos += 1
            continue
        if re.match(r"^\d+\.\d+", data[pos].strip()):
            break
        if (
            pos + 2 < len(data)
            and _is_pure_number_cell(data[pos])
            and _cell_has_letters(data[pos + 1])
        ):
            detail = {
                "dien_tich": data[pos],
                "muc_dich_su_dung": data[pos + 1],
                "thoi_han_su_dung": data[pos + 2],
            }
            pos += 3
            extras: list[str] = []
            while pos < len(data):
                peek = data[pos]
                peek_fold = _fold_text(peek)
                if peek_fold in ("trong do", "trong do:") or peek_fold.startswith("trong do"):
                    break
                if re.match(r"^\d+\.\d+", peek.strip()):
                    break
                if _is_pure_number_cell(peek) and pos + 1 < len(data) and _cell_has_letters(data[pos + 1]):
                    break
                extras.append(peek)
                pos += 1
                if len(extras) >= 2:
                    break
            if extras:
                detail["phan_ghi_them"] = " ".join(extras)
            current["chi_tiet_dien_tich"].append(detail)
            continue
        break
    return True


def _tach_thua_bang_don_dong(text: str, context: dict, parcels: list[dict]) -> bool:
    """Bang .doc bi don thanh 1 dong chu (mat dau |): tim tieu de
    "So to ban do ... Dien tich ... Muc dich" roi tach dong du lieu
    theo sau. Tra True neu an duoc it nhat 1 thua.
    Vi du: "So thua ... 2 (nay la to ban do so 107) 106 450 Trong do
    200 Dat o Lau dai 250 NTS 15/10/2063 ...".
    """
    folded = _fold_text(text)
    if not (("so thua" in folded or "so to" in folded) and ("dien tich" in folded or "muc dich" in folded)):
        return False
    head_end = re.search(
        r"(?i)(?:Ph\u1ea7n ghi th\u00eam|M\u1ee5c \u0111\u00edch s\u1eed d\u1ee5ng|Di\u1ec7n t\u00edch[^\n]*?m2\))\s*",
        text,
    )
    if not head_end:
        return False
    data = text[head_end.end():]
    # Cat phan chu thich dieu khoan ke tiep ("2.2. Phan quyen...").
    data = re.split(r"\s(?=\d+\.\d+\.\s)", data, maxsplit=1)[0]
    parcel_match = re.search(
        r"(\d+(?:\s*\(nay l\u00e0 t\u1edd b\u1ea3n \u0111\u1ed3 s\u1ed1\s*\d+\))?)\s+(\d+)\s+([\d.,]+)\s*(?=Trong |$)",
        data,
        flags=re.IGNORECASE,
    )
    if not parcel_match:
        return False
    current = _new_thua_dat(context)
    _to_head, _to_note = _tach_nay_la(_clean_asset_cell(parcel_match.group(1)))
    current["so_to_ban_do"] = _clean_so_to_ban_do(_to_head)
    current["so_thua_dat"] = _clean_asset_cell(parcel_match.group(2))
    current["dien_tich"] = _clean_asset_cell(parcel_match.group(3))
    if _to_note:
        current["phan_ghi_them"] = _to_note
    parcels.append(current)
    rest = data[parcel_match.end():]
    detail_re = re.compile(
        r"Trong\s+([\d.,]+)\s+(.+?)\s+(L\u00e2u d\u00e0i|\d{1,2}/\d{1,2}/\d{4})\b\s*",
        flags=re.IGNORECASE,
    )
    pos = 0
    while True:
        seg_match = re.search(r"(?i)Trong", rest[pos:])
        if not seg_match:
            break
        detail = detail_re.match(rest, pos + seg_match.start())
        if not detail:
            break
        ghi_them = rest[detail.end():]
        next_seg = re.search(r"(?i)Trong", ghi_them)
        if next_seg:
            ghi_them = ghi_them[:next_seg.start()]
        current["chi_tiet_dien_tich"].append({
            "dien_tich": _clean_asset_cell(detail.group(1)),
            "muc_dich_su_dung": _clean_asset_cell(detail.group(2)),
            "thoi_han_su_dung": _clean_asset_cell(detail.group(3)),
            "phan_ghi_them": _clean_asset_cell(ghi_them),
        })
        pos = detail.end() + len(ghi_them)
    return True


def _so_thuc_dien_tich(value: str) -> float | None:
    """So dau tien trong o dien tich -> float (phuc vu land_rows).
    Quy tac Owner 06/10/2026: "1.234,5"/"1234,5"/"1234.0" doc duoc; chi dau
    cham ("1.234") la mo ho -> None, giu nguyen van + co o tang khac.
    Khong parse duoc thi None (giu text goc o muc_dich/dien_tich raw).
    """
    match = re.match(r"\s*(\d+(?:[.,]\d+)*)", str(value or ""))
    if not match:
        return None
    cleaned = match.group(1)
    if "." in cleaned and "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    elif "." in cleaned:
        frac = cleaned.rsplit(".", 1)[1]
        if len(frac) == 3:
            # "1.234" mo ho: hang nghin (1234) hay thap phan (1,234)?
            # -> giu nguyen van, tang khac gan co; khong doan.
            return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def thua_dat_sang_land_rows(parcel: dict) -> list[dict]:
    """Doi chi_tiet_dien_tich sang shape DB land_rows (contracts/
    notary-case-drafting.md asset_row): [{loai_dat, dien_tich, thoi_han}].
    loai_dat giu text goc (ma nhu ONT/CLN hoac ten nhu "Dat o") —
    khong tu suy ma khi thieu can cu.
    """
    rows: list[dict] = []
    for detail in (parcel or {}).get("chi_tiet_dien_tich", []):
        if not isinstance(detail, dict):
            continue
        loai_dat = _clean_asset_cell(detail.get("muc_dich_su_dung", ""))
        thoi_han = _clean_asset_cell(detail.get("thoi_han_su_dung", ""))
        dien_tich = _so_thuc_dien_tich(detail.get("dien_tich", ""))
        if not loai_dat and dien_tich is None and not thoi_han:
            continue
        rows.append({
            "loai_dat": loai_dat or None,
            "dien_tich": dien_tich,
            "thoi_han": thoi_han or None,
        })
    return rows


def tach_danh_sach_thua_dat(tai_san: str) -> list[dict]:
    """Tach khoi text tai san thanh list moi thua 1 dong (gop context GCN)."""
    block = unicodedata.normalize("NFC", str(tai_san or ""))
    if not block.strip():
        return []
    context = _tach_ngu_canh_gcn(block)
    parcels: list[dict] = []
    current: dict | None = None
    pending: dict | None = None
    trong_do_seen = False
    col_order: tuple = ()

    bullet_labels = (
        ("so_thua_dat", r"Th\u1eeda \u0111\u1ea5t s\u1ed1|S\u1ed1 th\u1eeda"),
        ("so_to_ban_do", r"T\u1edd b\u1ea3n \u0111[\u1ed3\u0111\u1ed5](?: \u0111\u1ecba ch\u00ednh)? s\u1ed1|S\u1ed1 t\u1edd(?: b\u1ea3n \u0111[\u1ed3\u0111\u1ed5])?"),
        ("dien_tich", r"Di\u1ec7n t\u00edch"),
        ("muc_dich_su_dung", r"M\u1ee5c \u0111\u00edch s\u1eed d\u1ee5ng"),
        ("thoi_han_su_dung", r"Th\u1eddi h\u1ea1n s\u1eed d\u1ee5ng"),
        ("nguon_goc", r"Ngu\u1ed3n g\u1ed1c(?:\s+s\u1eed d\u1ee5ng(?:\s+\u0111\u1ea5t)?)?"),
        ("dia_chi", r"\u0110\u1ecba ch\u1ec9"),
        ("phan_ghi_them", r"Ghi ch\u00fa|H\u00ecnh th\u1ee9c s\u1eed d\u1ee5ng"),
        ("muc_dich_su_dung", r"Lo\u1ea1i \u0111\u1ea5t"),
    )

    # IFilter cat tieu de bang lam 2 dong ("Dien tich" / "( m2) muc dich...")
    # — noi lai truoc khi tach de du tieu de + du lieu chung 1 dong.
    raw_lines = block.split("\n")
    merged_lines: list[str] = []
    skip_next = False
    for idx, raw_line in enumerate(raw_lines):
        if skip_next:
            skip_next = False
            continue
        folded_line = _fold_text(raw_line)
        next_line = raw_lines[idx + 1] if idx + 1 < len(raw_lines) else ""
        if (
            "|" in raw_line
            and "so to ban do" in folded_line
            and "muc dich" not in folded_line
            and "muc dich" in _fold_text(next_line)
        ):
            merged_lines.append(raw_line.strip() + " | " + next_line.strip())
            skip_next = True
            continue
        merged_lines.append(raw_line)

    for raw_line in merged_lines:
        line = raw_line.strip()
        if not line:
            continue
        folded = _fold_text(line)
        # "Trong do: | 300 | Dat o | ..." — cat moc, giu lai o du lieu.
        if "|" in line and "trong do" in folded:
            line = re.sub(r"(?i)trong\s+đ[oó]:?", "", line)
            folded = _fold_text(line)
            if not line.strip(" |"):
                trong_do_seen = True
                continue
        if folded in ("trong do", "trong do:") or folded.startswith("trong do"):
            trong_do_seen = True
            continue
        # Dong tieu de bang that co chu "So thua"/"So to" + "Dien tich"/
        # "Muc dich" — dong du lieu kieu "04 Nay la to ban do 24 | 104 Nay
        # la thua dat so 321 | ..." khong duoc nhan nham lam tieu de.
        # Bang .doc bi don thanh 1 dong (mat dau |): tach rieng, khong de
        # roi vao nhan bullet gay thua rac.
        if ("so thua" in folded or "so to" in folded) and ("dien tich" in folded or "muc dich" in folded):
            if "|" not in line:
                _tach_thua_bang_don_dong(line, context, parcels)
                continue
            pipe_cells = [_clean_asset_cell(cell) for cell in line.split("|")]
            if not _tach_thua_cell_stream(pipe_cells, context, parcels):
                col_order = _map_asset_table_columns(line)
            continue
        # Dong gach dau dong .doc qua IFilter ("-\tDien tich: x" -> "-|Dien tich: x")
        # — o la cap "nhan: gia tri", khong phai dong bang: doi thanh dong nhan
        # "- L: v; L: v" de bullet path xu ly, tranh tach thanh thua rac.
        if "|" in line and line.lstrip().startswith(("-", "*")):
            _label_alt = "|".join(lbl for _f, lbl in bullet_labels)
            _o_co_nhan = [c.strip() for c in line.split("|") if c.strip("-*_ ")]
            if _o_co_nhan and any(
                re.match(r"(?i)(?:" + _label_alt + r")\s*:", c.lstrip("-*_ ")) for c in _o_co_nhan
            ):
                line = "- " + "; ".join(c.lstrip("-*_ ").rstrip(" ;") for c in _o_co_nhan)
                folded = _fold_text(line)
        elif "|" in line:
            # Bullet chu cai/so cua .doc ("a)\tThua dat so: 378" -> "a|Thua...") —
            # moi o khong trong la "nhan: gia tri" hoac danh dau bullet.
            _label_alt = "|".join(lbl for _f, lbl in bullet_labels)
            _o = [c.strip() for c in line.split("|")]
            _o_ko_trong = [c for c in _o if c]
            def _la_marker(c: str) -> bool:
                return bool(re.match(r"^(?:[a-z\u0110]{1,2}|\d{1,3})[.)-]?$", c, re.IGNORECASE))
            if _o_ko_trong and all(
                re.match(r"(?i)(?:" + _label_alt + r")\s*:", c.lstrip("-*_ ")) or _la_marker(c)
                for c in _o_ko_trong
            ) and any(re.match(r"(?i)(?:" + _label_alt + r")\s*:", c.lstrip("-*_ ")) for c in _o_ko_trong):
                line = "- " + "; ".join(
                    c.rstrip(" ;") for c in _o_ko_trong if not _la_marker(c)
                )
                folded = _fold_text(line)
        if "|" in line:
            order = col_order or _THUA_TABLE_DEFAULT_ORDER
            cells = [_clean_asset_cell(cell) for cell in line.split("|")]
            # Dong van xuoi rat dai (lap lai GCN/QSDD trong doan tom tat
            # phan chia) khong phai dong du lieu bang — o that luon ngan.
            if any(len(cell) > 100 for cell in cells):
                continue
            if col_order and len(cells) >= len(order):
                # Dong van xuoi troi vao bang ("15/10/2063 | | | 2. Thống nhất
                # phân chia...") — o tieu de muc "2. ..." khong phai du lieu.
                if any(re.match(r"^\s*\d{1,2}\.\s+\S", c) for c in cells if c):
                    continue
                row = {
                    "so_to_ban_do": "",
                    "so_thua_dat": "",
                    "dien_tich": "",
                    "muc_dich_su_dung": "",
                    "thoi_han_su_dung": "",
                    "phan_ghi_them": "",
                }
                key_map = {
                    "to": "so_to_ban_do",
                    "thua": "so_thua_dat",
                    "dien_tich": "dien_tich",
                    "muc_dich": "muc_dich_su_dung",
                    "thoi_han": "thoi_han_su_dung",
                    "ghi_them": "phan_ghi_them",
                }
                for pos, cell in enumerate(cells):
                    if pos >= len(order) or not order[pos]:
                        continue
                    target = key_map.get(order[pos], "")
                    if target and not row[target]:
                        if target in ("so_to_ban_do", "so_thua_dat"):
                            _head, _note = _tach_nay_la(cell)
                            if _note:
                                row["phan_ghi_them"] = (row["phan_ghi_them"] + "; " + _note).lstrip("; ")
                            cell = _head
                        row[target] = _clean_so_to_ban_do(cell) if target == "so_to_ban_do" else cell
                if row["so_thua_dat"] == "_":
                    row["so_thua_dat"] = ""
                if row["so_to_ban_do"] == "_":
                    row["so_to_ban_do"] = ""
                if re.search(r"\d", row["so_thua_dat"]):
                    current = _new_thua_dat(context)
                    for key, value in row.items():
                        if value:
                            current[key] = value
                    parcels.append(current)
                elif current is not None:
                    detail = {key: value for key, value in row.items() if value}
                    if detail:
                        current["chi_tiet_dien_tich"].append(detail)
                else:
                    current = _new_thua_dat(context)
                    detail = {key: value for key, value in row.items() if value}
                    if detail:
                        current["chi_tiet_dien_tich"].append(detail)
                    parcels.append(current)
                continue
            # Dong ngan khong du o: o giua co chu so la thua moi
            # ("4|169|427", "_|201|622"); khong co thi la chi tiet
            # ("200|Dat o|Lau dai" = dien tich|muc dich|thoi han).
            mid = cells[1] if len(cells) > 1 else ""
            cells_fold = " ".join(_fold_text(c) for c in cells)
            if re.search(r"so khung|so may|so dang ky|nhan hieu|bien (so|kiem)|loai (xe|tau)|dung tich|ma so|mau son|so cho|nam san xuat|nam sx|kieu dang|trong tai", cells_fold):
                continue
            if re.search(r"tai san (thu|rieng)\b", cells_fold):
                continue
            # Bang liet ke nguoi (ten + sinh ngay/cccd) khong phai bang chi
            # tiet thua — bo qua de khong bi nhat ten nguoi vao dien_tich.
            if re.search(r"sinh (ngay|nam)|ngay sinh|nam sinh|can cuoc|cccd|cmnd|ho chieu|ho khau", cells_fold):
                continue
            # Bang liet ke nguoi thua ke khong cot ngay sinh ("STT|HỌ VÀ TÊN|
            # QUAN HỆ|THUỘC HÀNG THỪA KẾ", "1|Hoàng Thị X|Vợ|Thứ nhất").
            if re.search(r"\bstt\b|ho va ten|quan he|thuoc hang thua ke|hang thua ke|nguoi thua ke", cells_fold):
                continue
            if re.match(r"^\s*\d{1,2}\s*$", cells[0].strip()) and re.search(
                r"\b(?:vo|chong|con(?:\s+de|\s+ruot)?|chau|dau|re|me|bo|cha)\b|thu (nhat|hai|ba|tu)", cells_fold
            ):
                continue
            if re.match(r"^\s*\d+[.)]?\s*(?:\u00d4ng|\u00f4ng|\u00f4ng/b\u00e0|B\u00e0|Anh|Ch\u1ecb|C\u00f4|Ch\u00e1u)\b", cells[0]):
                continue
            # Dong van xuoi co o la tieu de muc "2. Thống nhất ..." khong phai
            # du lieu bang — bo truoc khi vao chi tiet/thua "ma".
            if any(re.match(r"^\s*\d{1,2}\.\s+\S", c) for c in cells if c):
                continue
            mid_head, _mid_note = _tach_nay_la(mid)
            if (
                mid_head.strip() not in ("", "_")
                and re.search(r"\d", mid_head)
                and ":" not in mid_head
                and len(mid_head.strip()) <= 15
            ):
                current = _new_thua_dat(context)
                shorts = cells + ["", "", "", "", ""]
                _to_head, _to_note = _tach_nay_la(shorts[0])
                current["so_to_ban_do"] = (
                    "" if shorts[0].strip() == "_" else _clean_so_to_ban_do(_to_head)
                )
                current["so_thua_dat"] = mid_head
                _ghi_nay = "; ".join(n for n in (_to_note, _mid_note) if n)
                if _ghi_nay:
                    current["phan_ghi_them"] = _ghi_nay
                current["dien_tich"] = shorts[2]
                current["muc_dich_su_dung"] = shorts[3]
                current["thoi_han_su_dung"] = shorts[4]
                parcels.append(current)
            elif current is not None:
                if len(cells) == 3:
                    current["chi_tiet_dien_tich"].append(
                        {
                            "dien_tich": cells[0],
                            "muc_dich_su_dung": cells[1],
                            "thoi_han_su_dung": cells[2],
                        }
                    )
                elif len(cells) == 4:
                    current["chi_tiet_dien_tich"].append(
                        {
                            "dien_tich": cells[0],
                            "muc_dich_su_dung": cells[1],
                            "thoi_han_su_dung": cells[2],
                            "phan_ghi_them": cells[3],
                        }
                    )
                elif any(cells):
                    current["chi_tiet_dien_tich"].append({"o_tho": cells})
            else:
                current = _new_thua_dat(context)
                parcels.append(current)
                if len(cells) == 3:
                    current["chi_tiet_dien_tich"].append(
                        {
                            "dien_tich": cells[0],
                            "muc_dich_su_dung": cells[1],
                            "thoi_han_su_dung": cells[2],
                        }
                    )
                elif len(cells) == 4:
                    current["chi_tiet_dien_tich"].append(
                        {
                            "dien_tich": cells[0],
                            "muc_dich_su_dung": cells[1],
                            "thoi_han_su_dung": cells[2],
                            "phan_ghi_them": cells[3],
                        }
                    )
                elif any(cells):
                    current["chi_tiet_dien_tich"].append({"o_tho": cells})
            continue
        # Chi nhan dong co nhan: gach dau dong, nhan thua/to, hoac nhan
        # chi tiet (dien tich/muc dich/thoi han/dia chi) khi da mo thua —
        # tranh nhan nham dong mo ta chung ("... tai dia chi: ...").
        line_fold = _fold_text(line)
        has_thua_to = (
            "thua dat so" in line_fold
            or "to ban do so" in line_fold
            or "so thua" in line_fold
            or "so to" in line_fold
        )
        hits: list[tuple[int, int, str]] = []
        for field, label in bullet_labels:
            for label_match in re.finditer(f"(?i)({label})\\s*:?", line):
                # Nhan nam trong ngoac ("(nay la to ban do so 100)") la
                # ghi chu nguon goc/danh so lai, khong phai nhan du lieu.
                if line.count("(", 0, label_match.start()) > line.count(")", 0, label_match.start()):
                    continue
                hits.append((label_match.start(), label_match.end(), field))
        if not hits:
            continue
        if (
            not re.match(r"\s*[-*]", line)
            and not has_thua_to
            and current is None
        ):
            continue
        hits.sort()
        values: dict[str, str] = {}
        thua_hit_pos = -1
        for pos, (start, end, field) in enumerate(hits):
            next_start = hits[pos + 1][0] if pos + 1 < len(hits) else len(line)
            value = _clean_asset_cell(line[end:next_start])
            if not value or field in values:
                continue
            if field == "so_thua_dat" and thua_hit_pos < 0:
                thua_hit_pos = start
            if field in ("so_to_ban_do", "so_thua_dat"):
                _head, _note = _tach_nay_la(value)
                if _note:
                    _cu = values.get("_nay_la", "")
                    values["_nay_la"] = (_cu + "; " + _note).lstrip("; ")
                value = _head
            if field == "so_to_ban_do":
                value = _clean_so_to_ban_do(value)
            if field == "dien_tich":
                value = re.sub(r"(?i)\s*\(b\u1eb1ng ch\u1eef:[^)]*\)", "", value).strip()
                # Cat phan thua ("70 m2, trong do: ...", "265,0 m2; Trong do: ...").
                value = re.split(
                    r"[,;]\s*(?=[A-Za-z\u00c0-\u1ef9])|\s+(?i:trong|theo)\b",
                    value, maxsplit=1,
                )[0].strip()
                # Dien tich khong co so nao la text van xuoi
                # ("dien tich thua dat neu tren") — bo, khong gan vao thua.
                if not re.search(r"\d", value):
                    continue
            if field == "dia_chi":
                value = re.sub(r"(?i)^t\u1ea1i:\s*", "", value).strip()
                value = re.split(r"\s+theo\b|;", value, maxsplit=1)[0].strip()
            values[field] = value
        if not values:
            continue
        if (
            "so_thua_dat" in values
            and current is not None
            and thua_hit_pos > 0
            and _fold_text(line[:thua_hit_pos]).rstrip().endswith("hien nay la")
        ):
            # Dong danh so lai ("Hien nay la thua dat so 124; To ban do so 13")
            # van la CUNG thua — ghi vao phan ghi them, khong mo thua moi.
            ghi = f"Hiện nay là thửa đất số {values['so_thua_dat']}"
            if values.get("so_to_ban_do"):
                ghi += f", tờ bản đồ số {values['so_to_ban_do']}"
            current["phan_ghi_them"] = (
                current["phan_ghi_them"] + "; " + ghi
            ).lstrip("; ")
            continue
        _nay_la = values.pop("_nay_la", "")
        if "so_thua_dat" in values:
            if current is not None and pending:
                current["chi_tiet_dien_tich"].append(pending)
            pending = None
            trong_do_seen = False
            current = _new_thua_dat(context)
            for field, value in values.items():
                if value:
                    current[field] = value
            if _nay_la:
                current["phan_ghi_them"] = (current["phan_ghi_them"] + "; " + _nay_la).lstrip("; ")
            parcels.append(current)
            # Chi tiet viet lien ("trong do: CLN 70m2").
            inline = re.search(
                r"(?i)trong đ[oó]:\s*([A-Za-z\u00c0-\u1ef9./]+)\s*([\d.,]+\s*m2?)",
                line,
            )
            if inline:
                current["chi_tiet_dien_tich"].append({
                    "dien_tich": _clean_asset_cell(inline.group(2)),
                    "muc_dich_su_dung": _clean_asset_cell(inline.group(1)),
                    "thoi_han_su_dung": "",
                })
        elif current is not None:
            if _nay_la:
                current["phan_ghi_them"] = (current["phan_ghi_them"] + "; " + _nay_la).lstrip("; ")
            if trong_do_seen and "so_thua_dat" not in values:
                if "dien_tich" in values:
                    if pending and pending.get("dien_tich"):
                        current["chi_tiet_dien_tich"].append(pending)
                    pending = {}
                if pending is None:
                    pending = {}
                for field, value in values.items():
                    if value:
                        pending[field] = value
            else:
                for field, value in values.items():
                    if not value:
                        continue
                    if field == "phan_ghi_them":
                        current[field] = (current[field] + "; " + value).lstrip("; ")
                    else:
                        current[field] = value
                # Chi tiet viet lien ngay tren dong dien tich:
                # "Dien tich: 265,0 m2; Trong do: ONT: 190,0 m2; NTS: 75,0 m2".
                if "dien_tich" in values and "trong do" in folded:
                    detail_tail = re.split(r"(?i)trong\s+đ[oó]\s*:?", line)[-1]
                    for dm in re.finditer(
                        r"([A-Z\u00c0-\u1ef9\u0110][\w\u00c0-\u1ef9]{1,10}"
                        r"(?:\s+[a-z\u00e0-\u1ef9]{1,10})?)"
                        r"\s*:\s*([\d.,]+\s*m2)",
                        detail_tail,
                    ):
                        current["chi_tiet_dien_tich"].append({
                            "dien_tich": _clean_asset_cell(dm.group(2)),
                            "muc_dich_su_dung": _clean_asset_cell(dm.group(1)),
                            "thoi_han_su_dung": "",
                        })
        else:
            current = _new_thua_dat(context)
            for field, value in values.items():
                if value:
                    current[field] = value
            parcels.append(current)
        continue

    if current is not None and pending:
        current["chi_tiet_dien_tich"].append(pending)

    # Bo thua "ma" — khong co bat ky du lieu thua nao (vi du van ban chi
    # co so tiet kiem nhung bullet khac lot vao).
    parcels = [
        th for th in parcels
        if any(
            str(th.get(k) or "").strip()
            for k in (
                "so_thua_dat", "so_to_ban_do", "dien_tich", "muc_dich_su_dung",
                "thoi_han_su_dung", "nguon_goc", "phan_ghi_them",
            )
        )
        or (str(th.get("dia_chi") or "").strip()
            and str(th.get("dia_chi") or "").strip() != context.get("dia_chi", ""))
        or any(re.search(r"\d", str(c.get("dien_tich") or "")) for c in th.get("chi_tiet_dien_tich", []))
    ]

    # Cung thua duoc nhac lai nhieu lan trong bai viet (khoi "di san de lai"
    # roi khoi "thong nhat phan chia") — gop vao ban ghi dau tien: do truong
    # trong, cong don phan_ghi_them va chi_tiet (09/10/2026: truoc day chi bo
    # ban sau -> mat du lieu neu lan nhac sau giau hon; IFilter cung cat
    # "2067 duoc tach tu thua X" thanh 2 thua cung so).
    dedup: list[dict] = []
    for parcel in parcels:
        key = _fold_text(parcel.get("so_thua_dat", ""))
        key_to = _fold_text(parcel.get("so_to_ban_do", ""))
        giu = None
        if key:
            for cu in dedup:
                if _fold_text(cu.get("so_thua_dat", "")) != key:
                    continue
                to_cu = _fold_text(cu.get("so_to_ban_do", ""))
                if to_cu == key_to or not to_cu or not key_to:
                    giu = cu
                    break
        if giu is not None:
            for field in (
                "so_to_ban_do", "dien_tich", "muc_dich_su_dung",
                "thoi_han_su_dung", "nguon_goc", "dia_chi", "loai_gcn",
                "so_gcn", "so_gcn_raw", "so_vao_so", "ngay_cap_gcn",
                "co_quan_cap",
            ):
                if not giu.get(field) and parcel.get(field):
                    giu[field] = parcel[field]
            for detail in parcel.get("chi_tiet_dien_tich", []):
                if detail and detail not in giu["chi_tiet_dien_tich"]:
                    giu["chi_tiet_dien_tich"].append(detail)
            ghi = str(parcel.get("phan_ghi_them") or "").strip(" ;")
            if ghi and ghi not in giu["phan_ghi_them"]:
                giu["phan_ghi_them"] = (giu["phan_ghi_them"] + "; " + ghi).lstrip("; ")
            continue
        dedup.append(parcel)
    # Note nguon goc bi cat doan o IFilter ("duoc tach tu" khong co so) —
    # khong mang thong tin, bo.
    for parcel in dedup:
        parcel["phan_ghi_them"] = "; ".join(
            part for part in str(parcel.get("phan_ghi_them") or "").split("; ")
            if not re.fullmatch(
                r"(?i)(?:\u0111\u01b0\u1ee3c|\u0111\u00e3)?\s*(?:t\u00e1ch|g\u1ed9p|s\u00e1p|nh\u1eadp)\s+t\u1eeb",
                part.strip(" (),;"),
            )
        ).strip(" ;")

    # Van ban chi mo ta dat o muc GCN (so + dia chi), khong co so thua/to —
    # van tao 1 ban ghi de giu so_gcn/dia_chi/co_quan_cap thay vi tra ve
    # rong (truoc day R09 bao "khong tach duoc tai san" du da biet GCN).
    if not dedup and (context.get("so_gcn") or context.get("dia_chi")):
        if re.search(
            r"(?i)quy\u1ec1n s\u1eed d\u1ee5ng \u0111\u1ea5t|th\u1eeda \u0111\u1ea5t|nh\u00e0 \u1edf|nh\u00e0 v\u00e0 \u0111\u1ea5t",
            block,
        ):
            dedup.append(_new_thua_dat(context))

    for parcel in dedup:
        parcel["land_rows"] = thua_dat_sang_land_rows(parcel)

    return dedup


# ============================================================
# FORMAT CHO 3 O CKEDITOR TREN WEB
# ============================================================
def _normalize_person_block_lines(person: dict) -> list[str]:
    raw_text = unicodedata.normalize("NFC", str(person.get("raw_text") or "")).strip()
    return [re.sub(r"\s+", " ", line).strip() for line in raw_text.split("\n") if line.strip()]


def _format_person_block(person: dict, *, index: int | None = None) -> str:
    lines = _normalize_person_block_lines(person)
    if not lines:
        return ""
    return "\n".join(lines).strip()


def fmt_nguoi_yeu_cau(ben_b):
    """Nguoi yeu cau CC = nguoi dau tien ben B."""
    if not ben_b.get("nguoi"):
        entity_lines = [line for line in ben_b.get("entity_lines", []) if line]
        return "\n".join(entity_lines[:3]).strip()
    return _format_person_block(ben_b["nguoi"][0])


def fmt_duong_su(ben_a, ben_b):
    """Duong su = toan bo ben A + ben B."""
    lines: list[str] = []
    _append_party_display(lines, ben_a)
    _append_party_display(lines, ben_b)
    return "\n".join(lines).strip()


def _append_party_display(lines: list[str], party: dict) -> None:
    for line in party.get("entity_lines", []):
        cleaned = str(line or "").strip()
        if cleaned:
            lines.append(cleaned)
    if party.get("entity_lines") and party.get("nguoi"):
        lines.append("")
    for person in party.get("nguoi", []):
        block = _format_person_block(person)
        if block:
            lines.append(block)
            lines.append("")


def _fmt_single_party_with_label(party: dict, *, label: str) -> str:
    lines: list[str] = []
    _append_party_display(lines, party)
    return "\n".join(lines).strip()


def _fmt_duong_su_with_labels(ben_a, ben_b, *, label_a: str, label_b: str) -> str:
    lines: list[str] = []
    _append_party_display(lines, ben_a)
    _append_party_display(lines, ben_b)
    return "\n".join(lines).strip()


def get_missing_web_form_fields(web_form: dict, *, file_hop_dong: str = "") -> list[str]:
    values = dict(web_form or {})
    values["file_hop_dong"] = file_hop_dong
    return [field for field in CRITICAL_WEB_FORM_FIELDS if not str(values.get(field) or "").strip()]


def _find_first_pattern_index(text: str, patterns: Iterable[str], *, start: int = 0) -> int:
    haystack = text[start:]
    best_idx = -1
    for pattern in patterns:
        match = re.search(pattern, haystack, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if not match:
            continue
        idx = start + match.start()
        if best_idx < 0 or idx < best_idx:
            best_idx = idx
    return best_idx


def _split_section_lines(section: str) -> list[str]:
    normalized = unicodedata.normalize("NFC", str(section or ""))
    lines: list[str] = []
    last_line = ""
    for raw in normalized.split("\n"):
        line = re.sub(r"\s+", " ", raw).strip()
        if not line or not re.search(r"\w", line) or line == last_line:
            continue
        lines.append(line)
        last_line = line
    return lines


def _extract_plain_text_persons(section: str) -> list[dict]:
    return [dict(entry) for entry in _extract_plain_text_person_entries(section)]


# Nhan dia chi nguoi song (dung chung cho tung nguoi + dia chi ca ben).
# "Hộ khẩu" bat buoc co ":" de khong bat nham cau ke "theo hộ khẩu của ông X".
_DIA_CHI_LABEL = (
    r"(?:N\u01a1i\s+)?(?:th\u01b0\u1eddng tr\u00fa|c\u01b0 tr\u00fa)\s+t\u1ea1i"
    r"|N\u01a1i\s+th\u01b0\u1eddng\s+tr\u00fa|N\u01a1i\s+c\u01b0\s+tr\u00fa"
    r"|H\u1ed9\s+kh\u1ea9u\s*(?:th\u01b0\u1eddng\s+tr\u00fa)?\s*:"
    r"|\u0110\u1ecba ch\u1ec9\s+n\u01a1i\s+c\u01b0\s+tr\u00fa|\u0110\u1ecba ch\u1ec9\s+\u0111\u0103ng\s+k\u00fd"
    r"|\u0110\u1ecba ch\u1ec9\s+th\u01b0\u1eddng\s+tr\u00fa|Tr\u00fa\s+t\u1ea1i"
    r"|\u0110\u0103ng\s+k\u00fd\s+(?:th\u01b0\u1eddng\s+tr\u00fa|h\u1ed9\s+kh\u1ea5u)|HKTT"
    r"|\u0110\u1ecba ch\u1ec9(?!\s+(?:th\u1eeda|nh\u00e0|\u0111\u1ea5t|li\u00ean h\u1ec7|giao d\u1ecbch))"
)


def _cat_duoi_dia_chi(value: str) -> str:
    """Dong IFilter gop nhieu dong thanh 1 — cat phan duoi khong phai dia
    chi: cum quan he "Là vợ/con của..." hoac dau nguoi tiep theo
    ("... Xã Y  Ông: Nguyễn Bá Văn", "... Ninh Bình  2. Ông ...")."""
    addr_val = re.sub(r"\s+", " ", str(value or "")).strip(" .;")
    addr_val = re.split(
        r"(?i)\s+(?:l\u00e0|la)\s+(?:v\u1ee3|ch\u1ed3ng|con|cha|m\u1eb9|ch\u00e1u|anh|ch\u1ecb)\b"
        r"|\s+\d+[.)]\s+(?=\u00d4ng|B\u00e0|Anh|Ch\u1ecb|[A-Z\u00c0-\u1ef9][a-z\u00e0-\u1ef9]*\s+[A-Z\u00c0-\u1ef9])"
        r"|\s+(?:\u00d4ng|B\u00e0|Anh|Ch\u1ecb)\s*:",
        addr_val, maxsplit=1,
    )[0].strip(" .;,")
    return addr_val


# Moc cat duoi trong ho_ten: dau cau/cum khoi dau truong ("CCCD so...",
# "Sinh ngay...", "Dia chi...", "cap ngay...", vai tro "la vo/chong...").
_NAME_BOUNDARY_RE = re.compile(
    r"[,;(|]"
    r"|\s+\d"
    r"|\s+(?i:cccd|cmnd|cc\b|c\u0103n c\u01b0\u1edbc|c\u0103n c\u1ee9|gi\u1ea5y\b|\u0111\u1ecba ch\u1ec9|th\u01b0\u1eddng tr\u00fa|c\u01b0 tr\u00fa"
    r"|h\u1ed9 kh\u1ea9u|qu\u00ea qu\u00e1n|ch\u1ee9c v\u1ee5|hi\u1ec7n\b|l\u00e0\b|thu\u1ed9c\b|theo\b|\u0111\u01b0\u1ee3c\b|n\u01a1i\b|v\u1ee3\b|ch\u1ed3ng\b|kh\u00f4ng\b|con\s+(?:\u0111\u1ebb|ru\u1ed9t))"
    r"|\s+(?:sinh\b|ng\u00e0y\b|n\u0103m\s*[:\d]|s\u1ed1\s*[:\d]|c\u1ea5p\s*(?:ng\u00e0y|t\u1ea1i|:))"
)


_TEN_TO_CHUC_RE = re.compile(
    r"chi nhanh|van phong|cong ty|ngan hang|chi cuc|\bubnd\b|benh vien|\bso\s|ban giam|\bphong\s",
    re.IGNORECASE,
)


def _cat_ho_ten(name: str) -> str:
    """Cat phan duoi khong phai ten: keyword truong, dau cau, so."""
    return _NAME_BOUNDARY_RE.split(str(name or ""), maxsplit=1)[0].strip(" ;,.-\u2013\u2014")


def _ho_ten_hop_le(name: str) -> bool:
    """Tu dau phai viet hoa (chan "nhánh văn phòng...", cau van) va khong
    chua tu khoa to chuc. Ten Viet 1-6 tu."""
    tokens = str(name or "").split()
    if not tokens or len(tokens) > 6:
        return False
    if not tokens[0][0].isupper():
        return False
    return not _TEN_TO_CHUC_RE.search(_fold_text(name))


def _extract_plain_text_person_entries(section: str) -> list[dict]:
    section = unicodedata.normalize("NFC", str(section or ""))
    header_re = re.compile(
        r"(?i)^\s*(?:[-*]\s*)?(?:(?:ng\u01b0\u1eddi\s+)?(?:v\u1ee3|ch\u1ed3ng)\s*[–-]\s*)?"
        r"(?:\d+\.\s*)?(?:v\u00e0\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\s+)?"
        r"(?:ng\u01b0\u1eddi\s+(?:v\u1ee3|ch\u1ed3ng)\s+)?(?P<title>\u00f4ng|b\u00e0)\s*:?\s*"
        r"(?P<name>.+?)(?=\s+Sinh ng\u00e0y:|[;]|$)"
    )
    header_re = re.compile(
        r"(?i)^\s*(?:[-*]\s*)?(?:\u0110\u1ea1i di\u1ec7n:\s*)?(?:(?:ng\u01b0\u1eddi\s+)?(?:v\u1ee3|ch\u1ed3ng)\s*[â€“-]\s*)?"
        r"(?:\d+\.\s*)?(?:v\u00e0\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\s+)?"
        r"(?:ng\u01b0\u1eddi\s+(?:v\u1ee3|ch\u1ed3ng)\s+)?(?P<title>\u00f4ng|b\u00e0)\s*:?\s*"
        r"(?P<name>.+?)(?=\s+(?:Sinh ng\u00e0y|Ng\u00e0y\s+sinh):|\s+Ch\u1ee9c v\u1ee5\s*:|[;]|$)"
    )
    header_re = re.compile(
        r"(?i)^\s*(?:[-*]\s*)?(?:\u0110\u1ea1i di\u1ec7n:\s*)?(?:(?:ng\u01b0\u1eddi\s+)?(?:v\u1ee3|ch\u1ed3ng)\s*[\-\u2013]\s*)?"
        r"(?:\d+\.\s*)?(?:v\u00e0\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\s+)?"
        r"(?:ng\u01b0\u1eddi\s+(?:v\u1ee3|ch\u1ed3ng)\s+)?(?P<title>\u00f4ng|b\u00e0)\s*:?\s*"
        r"(?P<name>.+?)(?=\s+(?:Sinh ng\u00e0y|Ng\u00e0y\s+sinh):|\s+Ch\u1ee9c v\u1ee5\s*:|[;]|$)"
    )
    birth_re = re.compile(r"(?i)(?:Sinh ng\u00e0y|Ng\u00e0y\s+sinh):?\s*(\d{1,2}/\d{1,2}/\d{4})")
    id_re = re.compile(r"(?i)(?:C\u0103n c\u01b0\u1edbc(?:\s+c\u00f4ng d\u00e2n)?|CCCD|CMND)\s*(?:s\u1ed1)?\s*:?\s*(\d+)")
    issue_place_re = re.compile(r"(?i)\bdo\s+([^\n]+?)\s+c\u1ea5p ng\u00e0y")
    issue_date_re = re.compile(r"(?i)c\u1ea5p ng\u00e0y\s*(\d{1,2}/\d{1,2}/\d{4})")
    header_re = re.compile(
        r"(?i)^\s*(?:[-*]\s*)?(?:(?:\u0110\u1ea1i di\u1ec7n|Dai dien|Ng\u01b0\u1eddi \u0111\u1ea1i di\u1ec7n|Nguoi dai dien)(?:\s+[^:]{0,80})?:\s*)?"
        r"(?:\d+\.\s*)?"
        r"(?:T\u00f4i (?:t\u00ean )?l\u00e0\s*:?|Ch\u00fang t\u00f4i l\u00e0\s*:?)?\s*"
        r"(?:(?:ng\u01b0\u1eddi\s+)?(?:v\u1ee3|ch\u1ed3ng)\s*[\-\u2013]\s*)?"
        r"(?:(?:em|anh|ch\u1ecb|c\u00f4|ch\u00fa|b\u00e1c|d\u00ec|c\u1eadu|m\u1ee3)\s+(?:trai|g\u00e1i|d\u00e2u|r\u1ec3|\u0111\u1ebb|ru\u1ed9t)\s*[-\u2013:]\s*)?"
        r"(?:v\u00e0\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\s+)?"
        r"(?:(?:b\u00ean|ben)\s+[A-Za-z\u00c0-\u1ef9]\s*[:.,]?\s*)?"
        r"(?:(?:con|m\u1eb9|b\u1ed1|cha|v\u1ee3|ch\u1ed3ng)\s+(?:\u0111\u1ebb|ru\u1ed9t|nu\u00f4i)\s*[-\u2013\u2014:]\s*)?"
        r"(?:ng\u01b0\u1eddi\s+(?:v\u1ee3|ch\u1ed3ng)\s+)?(?:v\u00e0\s+)?(?P<title>\u00f4ng/b\u00e0|ong/ba|\u00f4ng|ong|b\u00e0|ba|anh|ch\u1ecb|chi)\s*:?\s*"
        r"(?P<name>.+?)(?=\s+(?:[\-\u2013]\s+)?(?:Sinh ng\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh|Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh)\s*[:\u2013-]?\s*(?:(?:19|20)\d{2}|\d{1,2}/\d{1,2}/\d{4})|\s+(?:[\-\u2013]\s+)?(?:Ch\u1ee9c v\u1ee5|Chuc vu|Ch\u1ee9c danh|Chuc danh)\s*:|\s+c\u00f3\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\b|\s*\(\s*(?:Sinh|Ng\u00e0y)|[;]|$)"
    )
    birth_re = re.compile(r"(?i)(?:Sinh ng\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh|Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh)\s*[:\u2013-]?\s*(\d{1,2}/\d{1,2}/\d{4})")
    # Nguoi lon tuoi thuong chi ghi "Sinh nam 1965" — database chap nhan YYYY
    # (docs/spec/notary_v2/stage.md muc 5) nen giu nam lam ngay_sinh.
    # Gia tri chi co nam van nhan du nhan viet "Sinh ngay: 1982" (loi mau thuc te).
    birth_year_re = re.compile(r"(?i)(?:Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh|Sinh ng\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh)\s*[:\u2013-]?\s*((?:19|20)\d{2})(?!\d)")
    id_re = re.compile(r"(?i)(?:C\u0103n c\u01b0\u1edbc(?:\s+c\u00f4ng(?:\s+d\u00e2n)?)?(?:\s+m\u1edbi)?|Can cuoc(?:\s+cong(?:\s+dan)?)?|CCCD|CMND|\bCC)\s*(?:[A-Z\u00c0-\u1ef9\u0110][^\d:;\n]{0,40}?)?\s*(?:s\u1ed1|so)\s*:?\s*(\d{6,12})")
    issue_place_re = re.compile(r"(?i)\bdo\s+([^\n]+?)\s+(?:c\u1ea5p ng\u00e0y|cap ngay)")
    issue_date_re = re.compile(r"(?i)(?:c\u1ea5p ng\u00e0y|cap ngay|c\u1ea5p v\u00e0o ng\u00e0y)\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})")
    # Nguoi tham gia thua ke ghi ten tran khong kem "Ong/Ba", vi du:
    # "Nguyen Van A - Vo ong X Sinh ngay: 01/01/1933;" — chi nhan khi cung
    # dong co ngay sinh (han che nhan nham cau van mo ta nhu "Di san").
    bare_header_re = re.compile(
        r"(?i)^\s*(?P<name>[^\d;:\n]{2,60}?)\s*[\-\u2013]\s*"
        r"(?P<role>(?:v\u1ee3|vo|ch\u1ed3ng|chong|con(?:\s+\u0111\u1ebb|\s+de)?)\b[^\n;]*?)"
        r"\s+(?:(?:Sinh ng\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh)\s*[:\u2013-]?\s*\d{1,2}/\d{1,2}/\d{4}|(?:Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh)\s*[:\u2013-]?\s*(?:19|20)\d{2})"
    )
    # "Người chồng – Vũ Văn X, Sinh ngày ..." / "Con đẻ – Nguyễn Thị Y" —
    # vai tro dung dau dong, khong co danh xung Ong/Ba; chi nhan khi dong
    # co dau hieu nguoi (ngay sinh/giay to/dia chi).
    lead_role_re = re.compile(
        r"(?i)^\s*(?:Ng\u01b0\u1eddi\s+)?(?P<role>v\u1ee3|ch\u1ed3ng|con|m\u1eb9|b\u1ed1|cha)\b"
        r"(?:\s+(?:\u0111\u1ebb|ru\u1ed9t|nu\u00f4i))?\s*[-\u2013\u2014:]\s*"
        r"(?P<name>[A-Z\u00c0-\u1ef9\u0110][^\d;:\n]{1,60}?)"
        r"(?=\s+(?:sinh|ng\u00e0y|n\u0103m|cccd|c\u0103n c\u01b0\u1edbc|c\u1ea5p|\u0111\u1ecba ch\u1ec9|th\u01b0\u1eddng tr\u00fa|c\u01b0 tr\u00fa|n\u01a1i|h\u1ed9 kh\u1ea9u)\b|[;]|$)"
    )
    bare_name_noise_re = re.compile(
        r"chung toi|nguoi de lai|di san|van ban|loi chung|cong chung|thua ke|tai san",
        re.IGNORECASE,
    )
    # "Toi ten la: Tran Gia Huy; Sinh ngay: ..." — ten tran khong
    # Ông/Bà, nhan ngay sinh cung dong de chac la nguoi.
    intro_bare_re = re.compile(
        r"(?i)^\s*Tôi (?:tên )?là\s*:?\s*(?P<name>[^;|\-\u2013\n]+?)(?:\s*[;|\-\u2013]|\s+)[\s|]*"
        r"(?:Sinh ngày|Ngày sinh|Sinh ngay|Ngay sinh|Sinh năm|Năm sinh|Sinh nam|Nam sinh)"
    )
    _ADDR_LABEL = _DIA_CHI_LABEL
    address_re = re.compile(
        r"(?im)^\s*(?:\d+(?:\.\d+)*[.)]?\s*)?(?:C\u1ea3 hai(?:\s+\u00f4ng b\u00e0|\s+v\u1ee3 ch\u1ed3ng)?|C\u00f9ng|Hai v\u1ee3 ch\u1ed3ng)?\s*(?:"
        + _ADDR_LABEL + r")\s*:?\s*(.+)$"
    )
    shared_addr_re = re.compile(
        r"(?i)^\s*(?:c\u1ea3 hai|hai\s+v\u1ee3 ch\u1ed3ng|hai\s+\u00f4ng b\u00e0|c\u00f9ng)\b"
    )
    # Dia chi nam giua dong (vi du "...; Nơi thường trú: X") — chi dung khi
    # nhan dau dong khong khop; loai "Nơi thường trú cuối cùng..." cua nguoi
    # da chet de khong vo tinh gan dia chi nguoi chet cho nguoi song.
    address_fallback_re = re.compile(
        r"(?i)(?:" + _ADDR_LABEL + r")\s*:?\s*(?!\s*cu\u1ed1i c\u00f9ng\b)(.+)$"
    )

    lines = _split_section_lines(section)
    headers: list[tuple[int, re.Match[str]]] = []
    address_lines: list[tuple[int, str, str]] = []
    prev_intro_bare = False
    for idx, line in enumerate(lines):
        # "Toi la:" dung rieng 1 dong -> ten tran o dong ke tiep
        # ("Nguyen Thi Yen\t\tSinh ngay: ...").
        if (
            prev_intro_bare
            and re.search(r"\d", line)
            and header_re.search(line) is None
        ):
            next_match = re.match(
                r"\s*(?P<name>[A-Z\u00c0-\u1ef9\u0110][^\d;:\n]{2,60}?)"
                r"\s+(?:[-\u2013]\s*)?(?:Sinh ng\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh|Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh)",
                line,
            )
            if next_match:
                headers.append((idx, next_match))
        prev_intro_bare = bool(
            re.match(r"(?i)^\s*(?:T\u00f4i|Ch\u00fang t\u00f4i)\s+l\u00e0\s*:?\s*$", line)
        ) or (prev_intro_bare and not line.strip())
        match = header_re.search(line)
        if match:
            # Dong pha he ("Ông X co vo la ba Y (Sinh ngay...)") — ngay
            # sinh/ID tren dong la cua nguoi khac, bo ca dong.
            line_fold = _fold_text(line)
            la_pha_he = re.search(r"\bco\s+(vo|chong)\s+la\b", line_fold) is not None
            ngoac_nguoi_khac = bool(
                re.search(r"\(\s*(?:Sinh|Ng\u00e0y|CCCD|CMND|C\u0103n c\u01b0\u1edbc)", line)
            )
            if not la_pha_he and not ngoac_nguoi_khac:
                headers.append((idx, match))
        else:
            bare_match = bare_header_re.search(line)
            if bare_match:
                bare_name = re.sub(r"\s+", " ", bare_match.group("name")).strip(" ;,.")
                if len(bare_name.split()) >= 2 and not re.search(r"\d", bare_name):
                    bare_fold = _fold_text(bare_name)
                    if bare_fold and not bare_name_noise_re.search(bare_fold):
                        headers.append((idx, bare_match))
            else:
                intro_match = intro_bare_re.search(line)
                if intro_match:
                    intro_name = re.sub(r"\s+", " ", intro_match.group("name")).strip(" ;,.")
                    if len(intro_name.split()) >= 2 and not re.search(r"\d", intro_name):
                        intro_fold = _fold_text(intro_name)
                        if intro_fold and not bare_name_noise_re.search(intro_fold):
                            headers.append((idx, intro_match))
                elif re.search(r"\d", line):
                    lead_match = lead_role_re.search(line)
                    if lead_match:
                        lead_name = _cat_ho_ten(lead_match.group("name"))
                        if len(lead_name.split()) >= 2 and not re.search(r"\d", lead_name):
                            lead_fold = _fold_text(lead_name)
                            if lead_fold and not bare_name_noise_re.search(lead_fold):
                                headers.append((idx, lead_match))
        # Khong "continue" sau header: dia chi co the nam chung dong
        # voi ten ("...; Nơi thường trú: X").
        address_match = address_re.search(line)
        if not address_match:
            address_match = address_fallback_re.search(line)
        if address_match:
            addr_val = _cat_duoi_dia_chi(address_match.group(1))
            address_lines.append(
                (idx, line.strip(" ;"), addr_val, bool(shared_addr_re.match(line)))
            )

    persons = []
    death_line_re = re.compile(r"chet\s+ngay\s*\d", re.IGNORECASE)
    for header_idx, (line_idx, match) in enumerate(headers):
        next_idx = headers[header_idx + 1][0] if header_idx + 1 < len(headers) else len(lines)
        # Khoi cua 1 nguoi dung truoc dong "chet ngay ..." (dong mo ta
        # nguoi chet) — khong de chum lan sang nguoi song.
        for stop_idx in range(line_idx + 1, next_idx):
            if death_line_re.search(_fold_text(lines[stop_idx])):
                next_idx = stop_idx
                break
        chunk_lines = [line.strip() for line in lines[line_idx:next_idx] if line.strip()]
        if chunk_lines:
            # Nhan mo dau "Toi la:/Chung toi la:" khong phai ten — bo khoi
            # raw_text hien thi (use_match_end=False giu ca dong nhan de
            # parser bat duoc ten nam cung dong).
            chunk_lines[0] = re.sub(
                r"(?i)^\s*(?:T\u00f4i (?:t\u00ean )?l\u00e0|Ch\u00fang t\u00f4i l\u00e0)\s*:?\s*",
                "",
                chunk_lines[0],
            )
        chunk_lines = [line for line in chunk_lines if line]
        chunk = "\n".join(chunk_lines)
        groups = match.groupdict()
        if groups.get("title"):
            title = str(groups.get("title") or "").strip().lower()
            title_fold = _fold_text(title)
            if title_fold in ("ong", "anh"):
                gioi_tinh = "\u00d4ng"
            elif title_fold in ("ong/ba", "ong / ba", ""):
                # Khong suy gioi tinh (Owner 06/10/2026): nhan "Ông/bà"
                # hoac thieu chuc danh -> de trong, nguoi dung chon o Stage.
                gioi_tinh = ""
            else:
                gioi_tinh = "B\u00e0"
            ho_ten = re.sub(r"\s+", " ", match.group("name")).split("|")[0].strip(" ;,.-\u2013\u2014")
            ho_ten = re.split(r"(?i)\s*[-\u2013\u2014]\s+(?:con\b|ch\u00e1u\b|chau\b|v\u1ee3\b|ch\u1ed3ng\b|l\u00e0\b|b\u1ed1\b|m\u1eb9\b|cha\b|b\u00ean\b|ch\u1ecb\b|chi\b|anh\b|em\b|c\u00f4\b|co\b|ch\u00fa\b|chu\b|b\u00e1c\b|bac\b|d\u00ec\b|di\b|c\u1eadu\b|cau\b|m\u1ee3\b|mo\b|\u00f4ng\b|b\u00e0\b)", ho_ten, maxsplit=1)[0].strip(" ;,.-\u2013\u2014")
            ho_ten = _cat_ho_ten(ho_ten)
            person = {
                "gioi_tinh": gioi_tinh,
                "ho_ten": ho_ten,
                "_line_idx": line_idx,
                "raw_text": chunk,
            }
            # Vai tro ("La con de/vo cua ong X") la dong rieng — KHONG gop vao
            # ho_ten (Owner 07/10/2026: ten chi giu ho ten).
        else:
            base_name = re.sub(r"\s+", " ", groups.get("name") or "").split("|")[0].strip(" ;,.")
            base_name = re.split(r"(?i)\s*[-\u2013\u2014]\s+(?:con\b|ch\u00e1u\b|chau\b|v\u1ee3\b|ch\u1ed3ng\b|l\u00e0\b|b\u1ed1\b|m\u1eb9\b|cha\b|b\u00ean\b|ch\u1ecb\b|chi\b|anh\b|em\b|c\u00f4\b|co\b|ch\u00fa\b|chu\b|b\u00e1c\b|bac\b|d\u00ec\b|di\b|c\u1eadu\b|cau\b|m\u1ee3\b|mo\b|\u00f4ng\b|b\u00e0\b)", base_name, maxsplit=1)[0].strip(" ;,.-\u2013\u2014")
            base_name = _cat_ho_ten(base_name)
            role_phrase = re.sub(r"\s+", " ", groups.get("role") or "").strip(" ;,.")
            role_fold = _fold_text(role_phrase)
            if re.search(r"\b(?:vo|me)\b", role_fold):
                gioi_tinh = "B\u00e0"
            elif re.search(r"\b(?:chong|bo|cha)\b", role_fold):
                gioi_tinh = "\u00d4ng"
            else:
                # Khong suy tu chu "Thi" trong ten (Owner 06/10/2026).
                gioi_tinh = ""
            person = {
                "gioi_tinh": gioi_tinh,
                "ho_ten": base_name,
                "_line_idx": line_idx,
                "raw_text": chunk,
            }
        birth_match = birth_re.search(chunk)
        birth_year_match = birth_year_re.search(chunk) if not birth_match else None
        has_birth = bool(birth_match or birth_year_match)
        ngay_sinh, chi_co_nam = _chuan_hoa_ngay_sinh(
            birth_match.group(1) if birth_match else "",
            birth_year_match.group(1) if birth_year_match else "",
        )
        person["ngay_sinh"] = ngay_sinh
        person["chi_co_nam_sinh"] = chi_co_nam
        id_match = id_re.search(chunk)
        if not id_match:
            # Form viet tat "Ông Vũ Văn Thạnh số: 036070006771 Cấp ngày ..."
            # — "số:" tran khong nhan CCCD; so 9-12 chu so van la giay to.
            id_match = re.search(r"\bs\u1ed1\s*:\s*(\d{9,12})(?!\d)", chunk)
        person["cccd"] = id_match.group(1) if id_match else ""
        issue_place_match = issue_place_re.search(chunk)
        if not issue_place_match:
            cap_tai = re.search(
                r"(?i)c\u1ea5p\s+t\u1ea1i\s+([^\n,;.]{2,80}?)\s+ng\u00e0y\s*(\d{1,2}/\d{1,2}/\d{4})",
                chunk,
            )
            if cap_tai:
                issue_place_match = cap_tai
                if not person.get("ngay_cap_cccd"):
                    person["ngay_cap_cccd"] = cap_tai.group(2)
        if not issue_place_match:
            # Bien the thieu "do": "CCCD so 036... Cuc canh sat ... cap ngay..."
            # — chi nhan cum dung sau so giay to, tranh vo nham ca menh de.
            issue_place_match = re.search(
                r"(?i)(?:\d{9,12}\s+|\bCCCD\s+|\bCMND\s+)([^\n,;]{2,60}?)\s+(?:c\u1ea5p ng\u00e0y|cap ngay)",
                chunk,
            )
        if not issue_place_match:
            # Form "Nơi cấp Cục cảnh sát ..." (don xac nhan thoi han dat).
            issue_place_match = re.search(
                r"(?i)\bN\u01a1i\s+c\u1ea5p\s*[:;,]?\s*([^\n,;.]+?)(?=\s*[,;.]|\s*$)",
                chunk,
            )
        person["noi_cap"] = re.sub(r"\s+", " ", issue_place_match.group(1)).strip(" ;,.") if issue_place_match else ""
        issue_date_match = issue_date_re.search(chunk)
        if issue_date_match:
            person["ngay_cap_cccd"] = issue_date_match.group(1)
        else:
            # So Excel ("cap ngay 44546") — doi sang ngay that.
            person["ngay_cap_cccd"] = _doi_ngay_excel(chunk)
        address_match = next((item for item in address_lines if line_idx <= item[0] < next_idx), None)
        person["dia_chi"] = address_match[2] if address_match else ""
        dia_chi_line = address_match[1] if address_match else ""
        if dia_chi_line and re.search(
            r"(?i)sinh\s+ng|c\u0103n\s+c\u01b0\u1edbc|l\u00e0\s+(?:v\u1ee3|con|ch\u1ed3ng)",
            dia_chi_line,
        ):
            # Dong IFilter gop ca khoi nguoi thanh 1 dong — khong dung dong
            # tho lam dia_chi_line (uploader se paste ca cum rac).
            dia_chi_line = f"Thuong tru tai: {person['dia_chi']}"
        person["dia_chi_line"] = dia_chi_line
        name_fold = _fold_text(person["ho_ten"])
        if "hien dang so huu" in name_fold or "tai san la" in name_fold:
            continue
        # Loai nguoi da chet: chi khi co "chet ngay + ngay thang" cu the
        # (dong mo ta thua ke luon co; chu "chet" dung mot minh nhu
        # "ngay chet" trong checklist khong du de loai).
        if re.search(r"\bchet\s+ngay\s*[:.-]?\s*\d", _fold_text(chunk)):
            continue
        role_match = re.search(r"(?i)(?:Ch\u1ee9c v\u1ee5|Chuc vu|Ch\u1ee9c danh|Chuc danh)\s*:", chunk)
        if not has_birth and not id_match and not role_match:
            continue
        if not _ho_ten_hop_le(person["ho_ten"]):
            continue
        persons.append(person)

    # Dia chi dung chung ca khoi ("Cả hai ông bà cùng thường trú tại: X")
    # — gan cho moi nguoi con thieu, khong chi nguoi dung truoc dong do.
    shared_addrs = [a[2] for a in address_lines if len(a) > 3 and a[3] and a[2]]
    for person in persons:
        if not person["dia_chi"] and shared_addrs:
            person["dia_chi"] = shared_addrs[0]

    for person in persons:
        person["source_start_line_idx"] = person["_line_idx"]
        person.pop("_line_idx", None)
    return persons


def _extract_plain_text_address(section: str) -> str:
    address_re = re.compile(
        r"(?im)^(?:C\u1ea3 hai \u00f4ng b\u00e0\s+)?(?:C\u00f9ng\s+)?"
        r"(?:" + _DIA_CHI_LABEL + r")\s*:?\s*(.+)$"
    )
    for line in _split_section_lines(section):
        match = address_re.search(line)
        if not match:
            match = re.search(
                r"(?i)(?:" + _DIA_CHI_LABEL + r")\s*:?\s*(?!\s*cu\u1ed1i c\u00f9ng\b)(.+)$",
                line,
            )
        if match:
            return _cat_duoi_dia_chi(match.group(1))
    return ""


def _extract_party_data(section: str) -> dict:
    persons = _extract_plain_text_person_entries(section)
    lines = _split_section_lines(section)
    header_line_re = re.compile(
        r"(?i)^\s*(?:[-*]\s*)?(?:\u0110\u1ea1i di\u1ec7n:\s*)?(?:(?:ng\u01b0\u1eddi\s+)?(?:v\u1ee3|ch\u1ed3ng)\s*[â€“-]\s*)?"
        r"(?:\d+\.\s*)?(?:v\u00e0\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\s+)?"
        r"(?:ng\u01b0\u1eddi\s+(?:v\u1ee3|ch\u1ed3ng)\s+)?(?:\u00f4ng|b\u00e0)\s*:?"
    )
    header_line_re = re.compile(
        r"(?i)^\s*(?:[-*]\s*)?(?:\u0110\u1ea1i di\u1ec7n:\s*)?(?:(?:ng\u01b0\u1eddi\s+)?(?:v\u1ee3|ch\u1ed3ng)\s*[\-\u2013]\s*)?"
        r"(?:\d+\.\s*)?(?:v\u00e0\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\s+)?"
        r"(?:ng\u01b0\u1eddi\s+(?:v\u1ee3|ch\u1ed3ng)\s+)?(?:\u00f4ng|b\u00e0|anh|ch\u1ecb)\s*:?"
        r"|^[^\d;:\n]{2,60}?[\-\u2013]\s*(?:v\u1ee3|vo|ch\u1ed3ng|chong|con(?:\s+\u0111\u1ebb|\s+de)?)\b"
    )
    party_heading_re = re.compile(r"(?i)^(?:[IVX]+\.\s*)?B\u00caN\b")
    entity_lines: list[str] = []
    if persons:
        first_person_idx = min(int(person.get("source_start_line_idx", 0)) for person in persons)
        entity_lines = [
            line.strip(" ;")
            for idx, line in enumerate(lines)
            if idx < first_person_idx and line.strip() and not header_line_re.search(line) and not party_heading_re.search(line)
        ]
    for person in persons:
        person.pop("source_start_line_idx", None)
    return {
        "nguoi": [dict(person) for person in persons],
        "dia_chi": _extract_plain_text_address(section),
        "entity_lines": _dedupe_preserve_order(entity_lines),
    }


def _extract_section_between_patterns(
    text: str,
    start_patterns: Iterable[str],
    end_patterns: Iterable[str],
    *,
    use_match_end: bool = False,
) -> str:
    match = _find_first_pattern_match_generic(text, start_patterns)
    if not match:
        return ""

    start_idx = int(match[1] if use_match_end else match[0])
    end_idx = _find_first_pattern_index(text, end_patterns, start=start_idx)
    if end_idx <= start_idx:
        end_idx = len(text)
    return str(text[start_idx:end_idx]).strip()



def _find_first_pattern_match_generic(text: str, patterns: Iterable[str], *, start: int = 0):
    haystack = text[start:]
    best_match = None
    for pattern in patterns:
        match = re.search(pattern, haystack, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if not match:
            continue
        idx = start + match.start()
        end = start + match.end()
        if best_match is None or idx < best_match[0]:
            best_match = (idx, end)
    return best_match


def _extract_commitment_parties(text: str) -> tuple[dict, dict]:
    source = unicodedata.normalize("NFC", str(text or ""))
    lines = [re.sub(r"\s+", " ", line).strip() for line in source.split("\n") if line.strip()]
    if not lines:
        return {"nguoi": [], "dia_chi": ""}, {"nguoi": [], "dia_chi": ""}

    start_idx = 0
    for idx, line in enumerate(lines):
        if "chung toi gom" in _fold_text(line):
            start_idx = idx + 1
            break

    stop_prefixes = (
        "chung toi la vo chong",
        "nay chung toi lap van ban nay",
        "hien nay",
        "bang van ban nay",
        "loi chung",
    )

    preamble_lines: list[str] = []
    for line in lines[start_idx:]:
        folded = _fold_text(line)
        if any(folded.startswith(prefix) for prefix in stop_prefixes):
            break
        preamble_lines.append(line)

    entries = _extract_plain_text_person_entries("\n".join(preamble_lines))
    ben_a = {"nguoi": [], "dia_chi": ""}
    ben_b = {"nguoi": [], "dia_chi": ""}

    if entries:
        first = dict(entries[0])
        ben_a["dia_chi"] = first.get("dia_chi", "")
        ben_a["nguoi"] = [first]
    if len(entries) > 1:
        second = dict(entries[1])
        ben_b["dia_chi"] = second.get("dia_chi", "")
        ben_b["nguoi"] = [second]
    return ben_a, ben_b


def _extract_inheritance_partition_parties(text: str) -> tuple[dict, dict]:
    section = _extract_section_between_patterns(
        text,
        (
            r"(?im)^\s*Chúng tôi là những người được hưởng di sản\b",
            r"(?im)^\s*Tôi là những người được hưởng di sản\b",
            r"(?im)^\s*(?:Tôi là|Chúng tôi là)\s+người được hưởng di sản\b",
            r"(?im)^\s*Người được hưởng di sản theo pháp luật\b",
            r"(?im)^\s*Người được hưởng di sản thừa kế của\b",
            r"(?im)^\s*Tôi tên là:",
            r"(?im)Hàng thừa kế\b.{0,120}?gồm những người có tên sau đây\b",
            r"(?im)^\s*Văn bản phân chia di sản này được lập bởi\b",
        ),
        (
            r"(?im)^\s*Chúng tôi tự nguyện lập Văn bản này\b",
            r"(?im)^\s*Tôi tự nguyện lập Văn bản này\b",
            r"(?im)^\s*Người để lại di sản\s*:",
            r"(?im)^\s*Di sản\s*:",
            r"(?im)^\s*Khi còn sống\b",
            r"(?im)^\s*Trước khi chết\b",
            r"(?im)^\s*(?:Về\s+)?bố(?:,?\s*mẹ)?\s+đẻ\b",
            r"(?im)^\s*Chúng tôi là những người thừa kế\b",
            r"(?im)^\s*LỜI CHỨNG\b",
        ),
    )
    ben_a = _extract_party_data(section) if section else {"nguoi": [], "dia_chi": "", "entity_lines": []}
    ben_b = {"nguoi": [], "dia_chi": "", "entity_lines": []}
    return ben_a, ben_b


def _extract_inheritance_refusal_parties(text: str) -> tuple[dict, dict]:
    section = _extract_section_between_patterns(
        text,
        (
            r"(?im)^\s*Tôi là\s*:?",
            r"(?im)^\s*Chúng tôi là\s*:?",
            r"(?im)^\s*Văn bản từ chối nhận di sản này được lập bởi\s*:?",
        ),
        (
            r"(?im)^\s*Nay,\s*(?:tôi|chúng tôi)\s+tự nguyện lập Văn bản này\b",
            r"(?im)^\s*Theo quy định của pháp luật\b",
            r"(?im)^\s*LỜI CHỨNG\b",
        ),
        use_match_end=False,
    )
    ben_a = _extract_party_data(section) if section else {"nguoi": [], "dia_chi": "", "entity_lines": []}
    ben_b = {"nguoi": [], "dia_chi": "", "entity_lines": []}
    return ben_a, ben_b


def _chuan_hoa_ngay_sinh(ngay_du: str = "", nam: str = "") -> tuple[str, bool]:
    """Ngay sinh giu dung dang van ban viet.
    Quy uoc owner (sua 06/10/2026): chi co nam thi xuat dung YYYY
    (khong tu them 01/01), kem co chi_co_nam_sinh=True de tang duoi
    biet phan biet voi ngay du khi dien portal.
    """
    if (ngay_du or "").strip():
        return (ngay_du or "").strip(), False
    if re.fullmatch(r"(?:19|20)\d{2}", (nam or "").strip()):
        return (nam or "").strip(), True
    return "", False


def _doi_ngay_excel(chunk: str) -> str:
    """So Excel sau "cap ngay" (vi du 44546) -> DD/MM/YYYY.
    Chi nhan so 5 chu so trong khoang nam 1995-2040 de tranh so CCCD.
    """
    match = re.search(r"(?i)(?:c\u1ea5p ng\u00e0y|cap ngay)\s*:?\s*(\d{5})(?!\d)", chunk or "")
    if not match:
        return ""
    try:
        serial = int(match.group(1))
    except ValueError:
        return ""
    if serial < 34000 or serial > 60000:
        return ""
    try:
        from datetime import date, timedelta

        day = date(1899, 12, 30) + timedelta(days=serial)
        return day.strftime("%d/%m/%Y")
    except (OverflowError, ValueError):
        return ""


def _extract_nguoi_chet(text: str) -> list[dict]:
    """Trich NGUOI DA CHET (nguoi de lai di san) theo shape person_row
    (decision-46 06/10/2026): trich luc khai tu la giay to cua nguoi chet,
    dien vao so_giay_to/ngay_cap/noi_cap/loai_giay_to; dia chi cuoi -> dia_chi.
    Dau hieu bat buoc: co "chet ngay DD/MM/YYYY". Khong co ngay chet
    thi khong nhan (tranh vo nhan bo/me de chi ghi "chet nam...").
    """
    source = unicodedata.normalize("NFC", str(text or ""))
    found: list[dict] = []
    seen: set[str] = set()
    death_re = re.compile(
        r"(?i)(?P<title>\u00d4ng|B\u00e0|Anh|Ch\u1ecb)\s*:?\s*(?P<name>[^;(\n.,]+?)"
        r"(?:\s+v\u00e0\s+(?P<title2>\u00f4ng|b\u00e0|anh|ch\u1ecb)\s*:?\s*(?P<name2>[^;(\n.,]+?))?"
        r"\s*(?:\((?P<alias>[^)]+)\))?"
        r"\s*[-\u2013;,]?\s*"
        r"(?:Sinh n\u0103m\s*[:\u2013-]?\s*(?P<birth_year>(?:19|20)\d{2})"
        r"|Sinh ng\u00e0y\s*[:\u2013-]?\s*(?P<birth_full>\d{1,2}/\d{1,2}/\d{4}))?"
        r"\s*[;,]?\s*(?:\u0111\u00e3\s+)?ch\u1ebft ng\u00e0y\s*[:\u2013-]?\s*(?P<death>\d{1,2}/\d{1,2}/\d{4})"
    )
    matches = list(death_re.finditer(source))
    for match_idx, match in enumerate(matches):
        raw_name = re.sub(r"\s+", " ", match.group("name")).strip(" ;,.-")
        raw_name = re.sub(r"(?i)^\d+\.\s*", "", raw_name)
        raw_name = re.sub(r"(?i)^(?:l\u00e0|bao g\u1ed3m)\s+", "", raw_name)
        # Ten chi gom toi da 6 tu va moi tu phai viet hoa — cau van ke
        # ("va ba Khung la vo chong hop phap...", "duoc cap ngay...") bi loai.
        name_tokens = raw_name.split()
        if (
            not name_tokens
            or len(name_tokens) > 6
            or not all(tok[0].isupper() for tok in name_tokens)
        ):
            # Nguoi chet nam sau cum quan he ("ong X co me de la ba Y;
            # chet ngay ...") — regex nuot ca cum lam ten; thu lay danh
            # xung + ten CUOI trong cum truoc khi bo (09/10/2026).
            inner = re.search(
                r"(?i)\b(ông|bà|anh|chị)\s+([A-ZÀ-ỹĐ][^\d;:.,()\n]{2,60}?)\s*$",
                raw_name,
            )
            if not inner:
                continue
            inner_name = re.sub(r"\s+", " ", inner.group(2)).strip(" ;,.-")
            inner_tokens = inner_name.split()
            if (
                not inner_tokens
                or len(inner_tokens) > 6
                or not all(tok[0].isupper() for tok in inner_tokens)
            ):
                continue
            raw_name = inner_name
            match_title = inner.group(1)
        else:
            match_title = match.group("title")
        title_fold = _fold_text(match_title)
        # Nguoi thu 2 cung dong ("... và bà B; chết ngày ...") — tach thanh
        # ban ghi rieng, dung chung truong ngay/giay to cua cap.
        name2 = re.sub(r"\s+", " ", match.group("name2") or "").strip(" ;,.-")
        if name2:
            t2 = name2.split()
            key2 = f"{_fold_text(name2)}|{match.group('death')}"
            if t2 and len(t2) <= 6 and all(tok[0].isupper() for tok in t2) and key2 not in seen:
                seen.add(key2)
                found.append({
                    "gioi_tinh": "\u00d4ng" if _fold_text(match.group("title2") or "") in ("ong", "anh") else "B\u00e0",
                    "ho_ten": name2,
                    "ten_goi_khac": "",
                    "ngay_sinh": "",
                    "chi_co_nam_sinh": False,
                    "ngay_chet": match.group("death"),
                    "so_giay_to": "",
                    "ngay_cap": "",
                    "noi_cap": "",
                    "loai_giay_to": "",
                    "dia_chi": "",
                })
        alias = re.sub(r"\s+", " ", match.group("alias") or "").strip()
        alias = re.sub(r"(?i)^t\u00ean g\u1ecdi kh\u00e1c l\u00e0\s+", "", alias)
        tail_end = min(match.end() + 400, len(source))
        if match_idx + 1 < len(matches):
            tail_end = min(tail_end, matches[match_idx + 1].start())
        tail = source[match.end():tail_end]
        tlkt_no = ""
        tlkt_match = re.search(
            r"(?i)Tr\u00edch l\u1ee5c khai t\u1eed[^\n]{0,60}?s\u1ed1:?\s*([A-Za-z0-9/.-]+)",
            tail,
        )
        if tlkt_match:
            tlkt_no = tlkt_match.group(1).strip(" ;,.")
        tlkt_by = ""
        tlkt_date = ""
        tlkt_by_match = re.search(
            r"(?i)\bdo\s+([^\n]+?)\s+(?:k\u00fd|c\u1ea5p)\s+ng\u00e0y:?\s*(\d{1,2}/\d{1,2}/\d{4})",
            tail,
        )
        if tlkt_by_match:
            tlkt_by = re.sub(r"\s+", " ", tlkt_by_match.group(1)).strip(" ;,.")
            tlkt_date = tlkt_by_match.group(2)
        last_addr = ""
        addr_match = re.search(
            r"(?i)N\u01a1i th\u01b0\u1eddng tr\u00fa cu\u1ed1i c\u00f9ng tr\u01b0\u1edbc khi ch\u1ebft:\s*([^.\n]+)",
            tail,
        )
        if addr_match:
            last_addr = re.sub(r"\s+", " ", addr_match.group(1)).strip(" ;,.")
        key = f"{_fold_text(raw_name)}|{match.group('death')}"
        if not raw_name or key in seen:
            continue
        seen.add(key)
        ngay_sinh, chi_co_nam = _chuan_hoa_ngay_sinh(
            match.group("birth_full") or "", match.group("birth_year") or ""
        )
        found.append({
            "gioi_tinh": "\u00d4ng" if title_fold in ("ong", "anh") else "B\u00e0",
            "ho_ten": raw_name,
            "ten_goi_khac": alias,
            "ngay_sinh": ngay_sinh,
            "chi_co_nam_sinh": chi_co_nam,
            "ngay_chet": match.group("death"),
            "so_giay_to": tlkt_no,
            "ngay_cap": tlkt_date,
            "noi_cap": tlkt_by,
            "loai_giay_to": "Trích lục khai tử" if tlkt_no else "",
            "dia_chi": last_addr,
        })
    return found


def _extract_parties_generic(text: str, doc_kind: str) -> tuple[dict, dict]:
    if doc_kind == DOC_KIND_ASSET_COMMITMENT:
        ben_a, ben_b = _extract_commitment_parties(text)
        if ben_a.get("nguoi") or ben_b.get("nguoi"):
            return ben_a, ben_b
    if doc_kind in (DOC_KIND_INHERITANCE_PARTITION, DOC_KIND_INHERITANCE_DECLARATION):
        ben_a, ben_b = _extract_inheritance_partition_parties(text)
        if ben_a.get("nguoi") or ben_b.get("nguoi"):
            return ben_a, ben_b
    if doc_kind == DOC_KIND_INHERITANCE_REFUSAL:
        ben_a, ben_b = _extract_inheritance_refusal_parties(text)
        if ben_a.get("nguoi") or ben_b.get("nguoi"):
            return ben_a, ben_b

    ben_a_patterns = (
        r"(?m)^\s*(?:I\.\s*)?B\u00caN CHUY\u1ec2N NH\u01af\u1ee2NG\b",
        r"(?m)^\s*(?:I\.\s*)?B\u00caN TH\u1ebe CH\u1ea4P\b",
        r"(?m)^\s*\(?A\)?\s*B\u00caN TH\u1ebe CH\u1ea4P\b",
        r"(?m)^\s*(?:I\.\s*)?BEN THE CHAP\b",
        r"(?m)^\s*(?:I\.\s*)?B\u00caN CHO VAY\b",
        r"(?m)^\s*(?:I\.\s*)?B\u00caN CHO THU\u00ca\b",
        r"(?m)^\s*(?:I\.\s*)?B\u00caN (?:UY|U\u1ef6|\u1ee6Y) QUY\u1ec0N\b",
        r"(?m)^\s*(?:I\.\s*)?NG\u01af\u1edcI (?:UY|U\u1ef6|\u1ee6Y) QUY\u1ec0N\b(?=\s*[:(])(?![^\n]*\bNG\u01af\u1edcI\b)",
        r"(?m)^\s*(?:I\.\s*)?B\u00caN \u0110\u1eb6T C\u1eccC\b",
        r"(?m)^\s*(?:I\.\s*)?NG\u01af\u1edcI DI CH\u00daC\b(?=\s*[:(])(?![^\n]*\bNG\u01af\u1edcI\b)",
        r"(?m)^\s*(?:I\.\s*)?NG\u01af\u1edcI CAM K\u1ebeT\b(?=\s*[:(])(?![^\n]*\bNG\u01af\u1edcI\b)",
        r"(?m)^\s*(?:I\.\s*)?B\u00caN G\u00d3P V\u1ed0N\b",
        r"(?m)^\s*(?:I\.\s*)?B\u00caN T\u1eb6NG CHO\b",
        r"(?m)^\s*(?:I\.\s*)?B\u00caN B\u00c1N\b",
        r"(?m)^\s*(?:I\.\s*)?B\u00caN TH\u1ee8 NH\u1ea4T\b",
        r"(?m)^\s*(?:I\.\s*)?B\u00caN A\b",
    )
    ben_b_patterns = (
        r"(?m)^\s*(?:II\.\s*)?B\u00caN NH\u1eacN CHUY\u1ec2N NH\u01af\u1ee2NG\b",
        r"(?m)^\s*(?:II\.\s*)?B\u00caN NH\u1eacN TH\u1ebe CH\u1ea4P\b",
        r"(?m)^\s*\(?B\)?\s*B\u00caN NH\u1eacN TH\u1ebe CH\u1ea4P\b",
        r"(?m)^\s*(?:II\.\s*)?BEN NHAN THE CHAP\b",
        r"(?m)^\s*(?:II\.\s*)?B\u00caN VAY\b",
        r"(?m)^\s*(?:II\.\s*)?B\u00caN THU\u00ca\b",
        r"(?m)^\s*(?:II\.\s*)?B\u00caN \u0110\u01af\u1ee2C (?:UY|U\u1ef6|\u1ee6Y) QUY\u1ec0N\b",
        r"(?m)^\s*(?:II\.\s*)?NG\u01af\u1edcI \u0110\u01af\u1ee2C (?:UY|U\u1ef6|\u1ee6Y) QUY\u1ec0N\b(?=\s*[:(])(?![^\n]*\bNG\u01af\u1edcI\b)",
        r"(?i)uỷ\s+quyền\s+cho\s*:",
        r"(?m)^\s*(?:II\.\s*)?B\u00caN NH\u1eacN \u0110\u1eb6T C\u1eccC\b",
        r"(?m)^\s*(?:II\.\s*)?B\u00caN NH\u1eacN T\u1eb6NG CHO\b",
        r"(?m)^\s*(?:II\.\s*)?B\u00caN \u0110\u01af\u1ee2C T\u1eb6NG CHO\b",
        r"(?m)^\s*(?:II\.\s*)?B\u00caN MUA\b",
        r"(?m)^\s*(?:II\.\s*)?B\u00caN TH\u1ee8 HAI\b",
        r"(?m)^\s*(?:II\.\s*)?B\u00caN B\b",
    )
    preamble_patterns = (
        r"\bCh\u00fang t\u00f4i g\u1ed3m c\u00f3\s*:\s*",
        r"\bCh\u00fang t\u00f4i g\u1ed3m\s*:\s*",
    )
    end_patterns = (
        r"\bC\u00e1c b\u00ean t\u1ef1 nguy\u1ec7n\b",
        r"\bC\u00e1c b\u00ean \u0111\u00e3 t\u1ef1 nguy\u1ec7n\b",
        r"\bHai b\u00ean t\u1ef1 nguy\u1ec7n\b",
        r"\bB\u1eb1ng H\u1ee3p \u0111\u1ed3ng n\u00e0y\b",
        r"\b\u0110I\u1ec0U\s*1\b",
        r"\bL\u1edcI CH\u1ee8NG\b",
    )

    match_a = _find_first_pattern_match_generic(text, ben_a_patterns)
    match_b = _find_first_pattern_match_generic(text, ben_b_patterns)
    preamble_match = _find_first_pattern_match_generic(text, preamble_patterns)

    if match_a and match_b and match_a[0] > match_b[0]:
        match_a = None

    if match_a:
        idx_a_start = int(match_a[0])
    elif preamble_match and match_b:
        idx_a_start = int(preamble_match[1])
    else:
        idx_a_start = 0

    idx_b_start = int(match_b[0]) if match_b else -1
    idx_end = _find_first_pattern_index(text, end_patterns, start=max(idx_b_start, idx_a_start))

    if idx_b_start >= 0:
        ben_a_section = text[idx_a_start:idx_b_start]
        ben_b_section = text[idx_b_start:idx_end] if idx_end > idx_b_start else text[idx_b_start:]
    else:
        ben_a_section = text[idx_a_start:idx_end] if idx_end > idx_a_start else text[idx_a_start:]
        ben_b_section = ""

    return _extract_party_data(ben_a_section), _extract_party_data(ben_b_section)


def _fmt_duong_su_generic(ben_a, ben_b):
    lines: list[str] = []
    _append_party_display(lines, ben_a)
    _append_party_display(lines, ben_b)
    return "\n".join(lines).strip()


def _fmt_duong_su_by_kind(doc_kind: str, ben_a: dict, ben_b: dict) -> str:
    if doc_kind == DOC_KIND_TRANSFER:
        return fmt_duong_su(ben_a, ben_b)
    if doc_kind == DOC_KIND_MORTGAGE:
        return _fmt_duong_su_with_labels(
            ben_a,
            ben_b,
            label_a="BÊN THẾ CHẤP",
            label_b="BÊN NHẬN THẾ CHẤP",
        )
    if doc_kind == DOC_KIND_INHERITANCE_PARTITION:
        return _fmt_single_party_with_label(ben_a, label="NHỮNG NGƯỜI HƯỞNG DI SẢN")
    if doc_kind == DOC_KIND_INHERITANCE_DECLARATION:
        return _fmt_single_party_with_label(ben_a, label="NGƯỜI KHAI NHẬN DI SẢN")
    if doc_kind == DOC_KIND_INHERITANCE_REFUSAL:
        return _fmt_single_party_with_label(ben_a, label="NGƯỜI TỪ CHỐI NHẬN DI SẢN")
    return _fmt_duong_su_with_labels(ben_a, ben_b, label_a="BÊN A", label_b="BÊN B")


def _phat_hien_tai_san_chua_ho_tro(text: str) -> list[str]:
    """Nhan dien so tiet kiem / bao hiem co mat trong van ban nhung khong
    boc dong (decision-46 06/10/2026: tam dung). Tra ve ma loai de log/canh
    bao — thong tin van nam nguyen trong web_form.tai_san.
    """
    found = []
    if _find_tai_san_savings(text):
        found.append("so_tiet_kiem")
    if _find_tai_san_insurance(text):
        found.append("bao_hiem")
    return found


def _build_payload_generic(filepath, text: str, scan_result: dict, *, extract_mode: str) -> dict:
    doc_kind, ten_hd = _detect_document_kind_and_title(text)
    ben_a, ben_b = _extract_parties_generic(text, doc_kind)
    tai_san = _find_tai_san_by_kind(text, doc_kind)
    so_cong_chung = _normalize_web_contract_no(find_so_cong_chung(text) or scan_result.get("contract_no", ""))
    if doc_kind == DOC_KIND_ASSET_COMMITMENT and ben_a.get("nguoi"):
        nguoi_yeu_cau_party = ben_a
    else:
        nguoi_yeu_cau_party = ben_b if ben_b.get("nguoi") else ben_a
    web_form = {
        "ten_hop_dong": ten_hd,
        "ngay_cong_chung": find_ngay_cong_chung(text),
        "so_cong_chung": so_cong_chung,
        "nhom_hop_dong": guess_nhom_hd(ten_hd),
        "loai_tai_san": guess_loai_tai_san(tai_san, ten_hd),
        "cong_chung_vien": find_ccv(text),
        "thu_ky": "",
        "nguoi_yeu_cau": fmt_nguoi_yeu_cau(nguoi_yeu_cau_party),
        "duong_su": _fmt_duong_su_by_kind(doc_kind, ben_a, ben_b),
        "tai_san": tai_san,
    }
    file_goc = os.path.abspath(filepath)
    missing_fields = get_missing_web_form_fields(web_form, file_hop_dong=file_goc)
    return {
        "web_form": web_form,
        "raw": {
            "ben_a": ben_a,
            "ben_b": ben_b,
            # decision-46 (06/10/2026): khong trich loi chung; so TK/bao hiem
            # tam dung — chi nhan dien va gan co "chua ho tro".
            "tai_san_chua_ho_tro": _phat_hien_tai_san_chua_ho_tro(text),
            "nguoi_chet": _extract_nguoi_chet(text),
            "danh_sach_thua_dat": tach_danh_sach_thua_dat(tai_san),
            "file_goc": file_goc,
            "scan_contract_no": scan_result.get("contract_no", ""),
            "scan_reason": scan_result.get("reason", ""),
            "document_kind": doc_kind,
            "engine_version": ENGINE_VERSION,
            "extract_mode": extract_mode,
            "extract_is_partial": bool(missing_fields),
            "text_rong": not str(text or "").strip(),
            "missing_web_form_fields": missing_fields,
        },
    }

# ============================================================
# HAM CHINH
# ============================================================
def extract(filepath, *, scan_result: dict | None = None, preloaded_text: str | None = None):
    path = Path(filepath)
    use_ifilter_for_doc = path.suffix.lower() == ".doc"

    text = preloaded_text
    if text is None:
        text = read_docx(path, use_ifilter_for_doc=use_ifilter_for_doc)
        if use_ifilter_for_doc:
            text = _normalize_plain_text_for_extract(text)

    if scan_result is None:
        scan_result = _scan_contract_text(text, file_name=path.name)

    if use_ifilter_for_doc:
        return _build_payload_generic(path, text, scan_result, extract_mode="plain_text_doc")
    return _build_payload_generic(path, text, scan_result, extract_mode="structured_docx")


def main():
    if len(sys.argv) < 2:
        print("Cách dùng:")
        print('  python extract_contract.py "hop_dong.docx"')
        print('  python extract_contract.py "hop_dong.doc"')
        sys.exit(1)

    fp = sys.argv[1]
    if not os.path.exists(fp):
        print(f"Không tìm thấy file: {fp}")
        sys.exit(1)

    result = extract(fp)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)

    json_path = fp.rsplit(".", 1)[0] + "_extracted.json"
    with open(json_path, "w", encoding="utf-8") as file_obj:
        file_obj.write(output)
    print(f"\n→ Đã lưu: {json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

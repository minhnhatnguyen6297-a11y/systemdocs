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
        # O bang kieu "nhan<TAB>:<TAB>gia tri" (mau the chap ngan hang)
        # -> "nhan: gia tri" de parser truong doc duoc.
        line = re.sub(r"\s*\|\s*:\s*(?:\|\s*)?", ": ", line)
        # Dau/cuoi dong con "| " la do TAB thu dau dong cua .doc —
        # cat de pattern ^...$ khong bi lech (o trong bang van giu).
        line = re.sub(r"^(?:\s*\|)+\s*", "", line)
        line = re.sub(r"(?:\s*\|)+\s*$", "", line)
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

        m = re.search(r"(?:Sinh ngày|Sinh)\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})", chunk)
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
        if folded in ("van ban", "hop dong", "dinh chinh") and idx + 1 < len(lines):
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
                "danh muc ",
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
    # Trang phu "Trang sửa lỗi kỹ thuật đính kèm" cung vay — chi chep lai
    # dieu khoan sua, khong co khoi duong su rieng. Dung dau file, khong
    # nam trong tien to _find_title_line nen quet vai dong dau.
    head_raw = str(text or "").split("\n")[:6]
    head_lines = [_fold_text(l) for l in head_raw]

    def _trang_phu_title(marker: str) -> str:
        # Tieu de tra ve phai bat dau bang dong trang phu ("Trang sửa
        # lỗi kỹ thuật đính kèm ...") de R02 nhan dien — neu
        # _find_title_line bo qua dong marker thi ghep lai (12/10/2026).
        if title_fold.startswith(marker):
            return title_line
        for raw, folded in zip(head_raw, head_lines):
            if folded.strip().startswith(marker):
                head = _clean_title_line(raw)
                return f"{head} {title_line}".strip() if title_line else head
        return title_line

    if title_fold.startswith("trang sua loi ky thuat") or any(
        l.strip().startswith("trang sua loi ky thuat") for l in head_lines
    ):
        return DOC_KIND_GENERIC, _trang_phu_title("trang sua loi ky thuat")
    # File .doc/IFilter chi trich duoc trang "LỜI CHỨNG" (than van ban
    # khong co trong file) — route generic nhu trang phu, khong ap luat
    # thua ke (R08 se bao oan vi khoi tai san khong ton tai trong text).
    # Van giu loai hop dong neu loi chung dung truoc than van ban co
    # heading ben ("I. Bên A: ..." — tom tat kem loi chung trong 1 file).
    if any(l.strip().startswith("loi chung") for l in head_lines) and not re.search(
        r"(?im)^\s*(?:[IVX]+\s*[./]?\s*)?b\u00ean\b[^:\n]{0,60}:",
        text,
    ):
        return DOC_KIND_GENERIC, _trang_phu_title("loi chung")
    # Trang "ĐÍNH CHÍNH <văn bản gốc>" chi sua loi van ban da cong chung —
    # khong co khoi duong su/nguoi chet/tai san rieng (11/10/2026).
    if title_fold.startswith("dinh chinh") or any(
        l.strip().startswith("dinh chinh") for l in head_lines
    ):
        return DOC_KIND_GENERIC, _trang_phu_title("dinh chinh")

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
            r"quyen su dung dat(?: cua[^\n]{0,120})?[^\n]{0,250}?(?:(?:co dia chi(?: tai)?|tai dia chi)\s*:?|tai\s*:)",
            r"nha o va quyen su dung dat o(?: cua[^\n]{0,120})?[^\n]{0,250}?(?:(?:co dia chi(?: tai)?|tai dia chi)\s*:?|tai\s*:)",
            r"phan quyen su dung dat(?: cua[^\n]{0,200})?[^\n]{0,400}?(?:(?:co dia chi(?: tai)?|tai dia chi)\s*:?|tai\s*:|la\s*:|(?:cu the\s+)?nhu sau\s*:)",
            r"quyen su dung dat[^\n]{0,300}?theo\s*[\"'“”‘’]?\s*giay chung nhan",
            r"thua dat so[^\n]{0,200}?(?:co dia chi tai|tai dia chi|theo\s*[\"'“”‘’]?\s*giay chung nhan|theo ban do)",
            # "Phần Quyền tài sản của ông X ... đối với một phần thửa đất số 62"
            # — di san ke trong van xuoi, khong co bang/dia chi ranh ro.
            r"phan quyen tai san[^\n]{0,300}?thua dat\b",
            r"(?m)^\s*[-–—•]?\s*thua dat so\s*[:.]?\s*\d",
        ),
        (
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?(?:\|\s*)?nguoi thua ke\s*:",
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?(?:\|\s*)?nhung nguoi thua ke\b",
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?(?:\|\s*)?nhung nguoi nhan thua ke\b",
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?(?:\|\s*)?nhung nguoi thuoc hang thua ke\b",
            r"(?m)^\s*noi dung phan chia di san\b",
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?(?:\|\s*)?noi dung khai nhan\b",
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
            r"quyen su dung dat(?: cua[^\n]{0,120})?[^\n]{0,250}?(?:(?:co dia chi(?: tai)?|tai dia chi)\s*:?|tai\s*:)",
            r"phan quyen su dung dat(?: cua[^\n]{0,200})?[^\n]{0,400}?(?:(?:co dia chi(?: tai)?|tai dia chi)\s*:?|tai\s*:|la\s*:|(?:cu the\s+)?nhu sau\s*:)",
            # "Di san cua ong X de lai la ky phan thua ke ... tai dia chi:"
            # — don tu choi ke lai di san khong qua cum "quyen su dung dat".
            r"di san\s+(?:cua\s+)?[^\n]{0,250}?\bde\s+lai\b[^\n]{0,250}?(?:(?:co dia chi(?: tai)?|tai dia chi)\s*:?|tai\s*:|la\s*:|(?:cu the\s+)?nhu sau\s*:)",
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


def _find_tai_san_vehicle(text: str) -> str:
    """Khoi tai san XE O TO / XE MAY trong van ban thua ke — giu nguyen
    van text (bien so, so khung), chua boc dong theo decision-46."""
    return _extract_block_by_folded_patterns(
        text,
        (
            r"quyen so huu\s+xe\b",
            r"toan bo\s+quyen so huu[^\n]{0,60}?\b(?:xe|o to|xe may)\b",
            r"(?m)^\s*(?:[IVX]+\.[\s|]*)?di san[^\n]{0,120}?(?:xe\s+o to|xe\s+may|o to)\b",
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
        insurance = _find_tai_san_insurance(text)
        if insurance:
            return insurance
        return _find_tai_san_vehicle(text)

    if doc_kind == DOC_KIND_INHERITANCE_REFUSAL:
        tai_san = _find_tai_san_inheritance_refusal(text)
        if tai_san:
            return tai_san
        savings = _find_tai_san_savings(text)
        if savings:
            return savings
        insurance = _find_tai_san_insurance(text)
        if insurance:
            return insurance
        return _find_tai_san_vehicle(text)

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
        _dc = _clean_asset_cell(dia_chi_match.group(1))
        if re.match(
            r"(?i)theo\s+(?:Gi\u1ea5y|Quy\u1ebft|H\u1ee3p|\u0110\u01a1n|Bi\u00ean|GCN)\b",
            _dc,
        ):
            # "địa chỉ tại Theo Giấy chứng nhận ..." — nguon viet nham:
            # gia tri la mo ta giay to, khong phai dia chi (13/10/2026).
            context["nguon_goc"] = context.get("nguon_goc") or _dc
        else:
            context["dia_chi"] = _dc
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
    # Duoi marker muc ke ("20 b." dung truoc "Diện tích") — bo.
    cut = re.sub(r"\s+[a-zĐ]{1,2}[.)]?\s*$", "", cut)
    # O to ban do ghi kem tu khoa "thửa/tờ" ("thửa 423" thay vi "423" —
    # bang GCN 5 cot mau so 18, 13/10/2026).
    cut = re.sub(r"^\s*(?i:th\u1eeda|thua|t\u1edd|to)\s+(?=\d)", "", cut)
    return cut.strip(" ;,.")


def _cell_has_letters(value: str) -> bool:
    return bool(re.search(r"[A-Za-zÀ-ỹ]", value or ""))


def _la_o_thoi_han(value: str) -> bool:
    """O ky han su dung: nam 4 so ("2043"), ngay co "/" ("15/10/2063"),
    hoac chu ("Lau dai"). So nho 3 chu so ("119") la dien tich, tra False."""
    text = (value or "").strip()
    if not text:
        return False
    if re.match(r"^\d{4}\s*$", text) or "/" in text:
        return True
    return _cell_has_letters(text)


def _tach_nay_la(value: str) -> tuple[str, str]:
    """Cat duoi "(nay la to ban do so N)"/"nay la thua dat so N" ra ghi chu
    — tra (ky hieu dau, ghi chu). Vi du "104 Nay la thua dat so 321" ->
    ("104", "Nay la thua dat so 321")."""
    text = str(value or "")
    match = re.search(
        r"(?i)\s*(\(\s*(?:(?:\u0111\u01b0\u1ee3c|\u0111\u00e3)\s+)?(?:t\u00e1ch|g\u1ed9p|s\u00e1p|nh\u1eadp|chia|h\u1ee3p|t\u0103ng|gi\u1ea3m)[^)]*\)?"
        r"|(?:\u0111\u01b0\u1ee3c|\u0111\u00e3)\s+(?:t\u00e1ch|g\u1ed9p|s\u00e1p|nh\u1eadp|chia|h\u1ee3p)\s+t\u1eeb\b.*"
        r"|\(?\s*(?:hi\u1ec7n nay|nay)\s+l\u00e0\b[^)]*\)?)\s*$",
        text,
    )
    if not match:
        return text.strip(" ;,.-"), ""
    head = text[: match.start()].strip(" ;,.-(")
    return head, match.group(1).strip(" ;,.-")


def _nuot_o_chu_thua(data: list[str], pos: int, current: dict) -> int:
    """Nuot cac o chu ngay sau thua vua mo: muc dich -> thoi han.
    Dung khi gap o so (thua/chi tiet ke) hoac 'trong do'."""
    while pos < len(data):
        cell = data[pos]
        fold = _fold_text(cell)
        if fold.startswith("trong do") or len(cell) > 100:
            break
        if not _cell_has_letters(cell):
            # O so: chi nhan khi giong ky han ("2063", "15/10/2063") —
            # so dien tich nho ("119", "299") la thua/chi tiet tiep theo.
            if not current["thoi_han_su_dung"] and _la_o_thoi_han(cell):
                current["thoi_han_su_dung"] = cell
                pos += 1
            break
        head_txt, note_txt = _tach_nay_la(cell)
        if note_txt:
            current["phan_ghi_them"] = (current["phan_ghi_them"] + "; " + note_txt).lstrip("; ")
        if not current["muc_dich_su_dung"]:
            current["muc_dich_su_dung"] = head_txt
        elif not current["thoi_han_su_dung"]:
            current["thoi_han_su_dung"] = head_txt
        else:
            break
        pos += 1
    return pos


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
        # O chu sau bo 3 so dau (muc dich/thoi han cua thua dau
        # "150 NTS 2063") — giong nhanh thua moi ben duoi.
        pos = _nuot_o_chu_thua(data, pos, current)
    else:
        return False
    while pos < len(data):
        folded = _fold_text(data[pos])
        if folded in ("trong do", "trong do:") or folded.startswith("trong do"):
            pos += 1
            continue
        if re.match(r"^\d+\.\d+", data[pos].strip()):
            break
        # Bo 3 so lien tiep (to, thua, tong DT) sau "Trong do" = thua moi
        # ("...155|Dat o|Lau dai|23|32|160|Ao nuoi ca|12/2043...").
        if (
            pos + 2 < len(data)
            and _is_pure_number_cell(data[pos])
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
            # O chu tiep theo thuoc thua moi ("Ao nuoi ca", "12/2043
            # (nay la 31/12/2063)") — dung khi gap so (thua/chi tiet ke).
            pos = _nuot_o_chu_thua(data, pos, current)
            continue
        if (
            pos + 1 < len(data)
            and _is_pure_number_cell(data[pos])
            and _cell_has_letters(data[pos + 1])
        ):
            detail = {
                "dien_tich": data[pos],
                "muc_dich_su_dung": data[pos + 1],
                "thoi_han_su_dung": "",
            }
            pos += 2
            # O thoi han chi nhan khi giong ky han that (nam 4 so,
            # ngay co "/", hoac chu "Lau dai") — so 3 chu so nhu "119"
            # la dien tich cua chi tiet tiep theo, khong duoc nuot.
            if pos < len(data) and _la_o_thoi_han(data[pos]):
                detail["thoi_han_su_dung"] = data[pos]
                pos += 1
            extras: list[str] = []
            while pos < len(data):
                peek = data[pos]
                peek_fold = _fold_text(peek)
                if peek_fold in ("trong do", "trong do:") or peek_fold.startswith("trong do"):
                    break
                if re.match(r"^\d+\.\d+", peek.strip()):
                    break
                if re.search(r"bang van ban nay|xin cam doan|cam doan\s*:", peek_fold):
                    break
                if _is_pure_number_cell(peek) and pos + 1 < len(data) and (
                    _cell_has_letters(data[pos + 1])
                    or _is_pure_number_cell(data[pos + 1])
                ):
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
    # Bang don dong co the chua NHIEU thua + cum chi tiet "Trong do"
    # ("35 44 150 NTS 2063  35 103 299  Trong do 200 ONT Lau dai
    # 99 CLN 2043  35 134 168 CLN 2043"). Xay "o gia" — so rieng, cum
    # chu gop lai — roi dung chung bo tach stream voi bang co "|".
    cells = [text[: head_end.end()].strip()]
    buf: list[str] = []
    toks = data.split()
    idx = 0
    while idx < len(toks):
        tok = toks[idx]
        tok_fold = _fold_text(tok)
        if _is_pure_number_cell(tok) or re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", tok):
            if buf:
                cells.append(" ".join(buf))
                buf = []
            cells.append(tok)
        elif (
            tok_fold == "trong"
            and idx + 1 < len(toks)
            and _fold_text(toks[idx + 1]) == "do"
        ):
            if buf:
                cells.append(" ".join(buf))
                buf = []
            cells.append("trong do")
            idx += 1
        elif (
            tok_fold == "lau"
            and idx + 1 < len(toks)
            and _fold_text(toks[idx + 1]) == "dai"
        ):
            if buf:
                cells.append(" ".join(buf))
                buf = []
            cells.append("Lâu dài")
            idx += 1
        else:
            buf.append(tok)
        idx += 1
    if buf:
        cells.append(" ".join(buf))
    return _tach_thua_cell_stream(cells, context, parcels)


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


def _append_trong_do_details(current: dict, line: str) -> None:
    """Them cac chi tiet dien tich sau 'trong do' tren cung dong vao thua.

    Ho tro ca "Trong do: ONT: 190,0 m2; NTS: 75,0 m2" lan ve khong nhan
    ("dien tich chua duoc cap 89,4 m2 ONT") va ve nhieu cap
    ("Dat o la 180 m2 Dat vuon: 20 m2"). Dau "," kep giua 2 chu so la
    phan thap phan — khong tach ve.
    """
    if not re.search(r"(?i)trong\s+đ[oó]", line):
        return
    detail_tail = re.split(r"(?i)trong\s+đ[oó]\s*:?", line)[-1]
    for seg in re.split(r";|(?<!\d),(?!\d)", detail_tail):
        matches = list(re.finditer(r"(\d[\d.,]*)\s*m2", seg))
        for j, dm in enumerate(matches):
            start = matches[j - 1].end() if j else 0
            tail_txt = seg[dm.end():] if j == len(matches) - 1 else ""
            tail_txt = re.split(
                r"(?i)\s+(?:theo|tại|có|bản|giấy|năm)\b", tail_txt, maxsplit=1,
            )[0]
            label = (seg[start: dm.start()] + " " + tail_txt).strip(" :.,-")
            if not label:
                continue
            current["chi_tiet_dien_tich"].append({
                "dien_tich": _clean_asset_cell(dm.group(0)),
                "muc_dich_su_dung": _clean_asset_cell(label),
                "thoi_han_su_dung": "",
            })


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
        ("so_to_ban_do", r"T\u1edd b[\u1ea3\u00e0]n \u0111[\u1ed3\u0111\u1ed5](?: \u0111\u1ecba ch\u00ednh)?(?: s\u1ed1)?|S\u1ed1 t\u1edd(?: b[\u1ea3\u00e0]n \u0111[\u1ed3\u0111\u1ed5])?"),
        ("dien_tich", r"Di\u1ec7n t\u00edch"),
        ("muc_dich_su_dung", r"M\u1ee5c \u0111\u00edch s\u1eed d\u1ee5ng"),
        ("thoi_han_su_dung", r"Th\u1eddi h\u1ea1n s\u1eed d\u1ee5ng"),
        ("nguon_goc", r"Ngu\u1ed3n g\u1ed1c(?:\s+s\u1eed d\u1ee5ng(?:\s+\u0111\u1ea5t)?)?"),
        ("dia_chi", r"\u0110\u1ecba ch\u1ec9(?:\s+th\u1eeda \u0111\u1ea5t)?"),
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
            def _co_nhan(c: str) -> bool:
                # O "a) Thua dat so: 131" — marker danh so dung truoc
                # nhan cung tinh la o nhan (13/10/2026).
                c2 = re.sub(r"^[-*_ ;]*(?:[a-z\u0110]{1,2}|\d{1,3})[.)]\s*", "", c.lstrip("-*_ "))
                return bool(re.match(r"(?i)(?:" + _label_alt + r")\s*:", c2.lstrip("; ")))
            if _o_ko_trong and all(
                _co_nhan(c) or _la_marker(c)
                for c in _o_ko_trong
            ) and any(_co_nhan(c) for c in _o_ko_trong):
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
            # Dong marker muc ("IV | Nội dung phân chia thừa kế") — khong phai
            # chi tiet dien tich; dong thoi ngat thua hien tai de chi tiet
            # muc sau khong dinh vao thua truoc (13/10/2026).
            if (
                re.match(r"^\s*(?:[IVXLCDM]{1,5}|[A-Za-z])[.)]?\s*$", cells[0])
                and not any(re.search(r"\d", c) for c in cells)
            ):
                current = None
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
            if (
                field == "so_thua_dat"
                and value
                and not re.search(r"\d", value)
                and "«" not in value
                and "[" not in value
            ):
                # Gia tri so thua khong co chu so nao la van xuoi
                # ("số thửa và sơ đồ sẽ được điều chỉnh...") — bo.
                continue
            if field in ("so_to_ban_do", "so_thua_dat"):
                _head, _note = _tach_nay_la(value)
                if _note:
                    _cu = values.get("_nay_la", "")
                    values["_nay_la"] = (_cu + "; " + _note).lstrip("; ")
                value = _head.rstrip(" :;").strip()
            if field == "so_to_ban_do":
                value = _clean_so_to_ban_do(value)
            if field == "dien_tich":
                value = re.sub(r"(?i)\s*\(b\u1eb1ng ch\u1eef:[^)]*\)", "", value).strip()
                # Cat phan thua ("70 m2, trong do: ...", "265,0 m2; Trong do: ...").
                value = re.split(
                    r"[,;]\s*(?=[A-Za-z\u00c0-\u1ef9])|\s+(?i:trong|theo)\b",
                    value, maxsplit=1,
                )[0].strip()
                # Gia tri van xuoi kem so ("duoc cap de lam nha o 288 m2")
                # — chi lay cum so, khong giu ca cau.
                if re.search(r"[A-Za-z\u00c0-\u1ef9]", re.sub(r"(?i)m2|m\u00b2|ha", "", value)):
                    _num = re.search(r"\d[\d.,]*", value)
                    value = _num.group(0) if _num else ""
                # Dien tich khong co so nao la text van xuoi
                # ("dien tich thua dat neu tren") — bo, khong gan vao thua.
                if not re.search(r"\d", value):
                    continue
            if field == "dia_chi":
                value = re.sub(r"(?i)^t\u1ea1i:\s*", "", value).strip()
                value = re.split(r"\s+theo\b|;", value, maxsplit=1)[0].strip()
                if re.match(
                    r"(?i)theo\s+(?:Gi\u1ea5y|Quy\u1ebft|H\u1ee3p|\u0110\u01a1n|Bi\u00ean|GCN)\b",
                    value,
                ):
                    # "địa chỉ tại Theo Giấy chứng nhận ..." — nguon viet
                    # nham: gia tri la mo ta giay to, khong phai dia chi
                    # (cam ket tai san rieng, 13/10/2026).
                    values.setdefault("nguon_goc", value)
                    value = ""
            values[field] = value
        if not values:
            # Tieu de muc ("III. Người thừa kế", "IV. Nội dung phân
            # chia") — ngat trang thai de dong nhan muc sau khong dinh
            # vao thua truoc (thua 57 dinh "40 CLN" cua muc phan chia,
            # 13/10/2026).
            if re.match(
                r"(?i)^\s*(?:[IVXLCDM]{1,5}|\d{1,2})[.)]\s+(?:Nội dung|Điều|Người thừa|Di sản|Phần|Mục|Quyền|Nghĩa vụ|Cam kết|Thỏa thuận|Tài sản|Người nhận)\b",
                line,
            ):
                current = None
                pending = None
                trong_do_seen = False
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
            # Gia tri van xuoi keo theo mo ta ("thua dat so 8 tai: xa A,
            # tinh B theo Giay chung nhan ...") — tach head la so thua,
            # "tai: ..." thanh dia chi, "theo ..." thanh nguon goc
            # (HD uy quyen dau gia, 13/10/2026). Khong tach khi head
            # khong phai so thuan.
            _th = re.match(
                r"^\s*(\d[\d/.,]*)\s*[:,]?\s*"
                r"(t\u1ea1i\s*:|theo\b|t\u1ef7 l\u1ec7\b|,\s*)(.*)$",
                values["so_thua_dat"], re.I | re.S,
            )
            if _th and _th.group(3):
                _head = _th.group(1).rstrip("., ")
                _rest = _th.group(3).strip(" ,;")
                if _rest:
                    _dia_m = re.match(
                        r"(?i)(.*?)\s+theo\s+(Gi\u1ea5y|Quy\u1ebft|H\u1ee3p|\u0110\u01a1n|Bi\u00ean)\b(.*)$",
                        _rest, re.S,
                    )
                    if _dia_m:
                        values.setdefault("dia_chi", _dia_m.group(1).strip(" ,;"))
                        values.setdefault("nguon_goc", ("theo " + _dia_m.group(2) + _dia_m.group(3)).strip(" ,;"))
                    elif _fold_text(_th.group(2)).startswith("tai"):
                        values.setdefault("dia_chi", _rest)
                    else:
                        values.setdefault("phan_ghi_them", _rest)
                    values["so_thua_dat"] = _head
            # Liet ke nhieu thua trong van xuoi ("cac thua dat so 112, 115,
            # to ban do so 80") — moi so la mot thua cung truong con lai;
            # dedupe se gop vao ban chi tiet cung so o duoi (12/10/2026).
            # Chi tach khi moi phan deu la so thuan ("112, 115"), tranh tach
            # dia chi co dau phay ("8 tai: xa A, tinh B").
            _raw_parts = [p.strip() for p in re.split(r"[,;]", values["so_thua_dat"]) if p.strip()]
            if all(re.fullmatch(r"\d[\d/.,]*[a-zA-Z]?", p) for p in _raw_parts):
                thua_parts = _raw_parts
            else:
                thua_parts = [values["so_thua_dat"]]
            for part_idx, thua_part in enumerate(thua_parts):
                current = _new_thua_dat(context)
                for field, value in values.items():
                    if not value:
                        continue
                    current[field] = thua_part if field == "so_thua_dat" else value
                if _nay_la:
                    current["phan_ghi_them"] = (current["phan_ghi_them"] + "; " + _nay_la).lstrip("; ")
                parcels.append(current)
                if part_idx == 0:
                    _append_trong_do_details(current, line)
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
                    _append_trong_do_details(current, line)
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
                if not detail:
                    continue
                # Ban lap cung thua o muc khac ("Trong đó: ONT 170; CLN 40"
                # roi lai "CLN: 40 m2, thuộc ... ông X") — chi tiet trung
                # (dien_tich + loai dat dau) thi gop chu thich, khong nhan
                # doi dong keo R10 (13/10/2026).
                _d_dup = None
                if "dien_tich" in detail:
                    _d_dt = re.findall(r"\d[\d.,]*", str(detail.get("dien_tich") or ""))
                    _d_md = _fold_text(str(detail.get("muc_dich_su_dung") or "")).split(":")[0].strip()
                    for cu_d in giu["chi_tiet_dien_tich"]:
                        if "dien_tich" not in cu_d:
                            continue
                        _c_dt = re.findall(r"\d[\d.,]*", str(cu_d.get("dien_tich") or ""))
                        _c_md = _fold_text(str(cu_d.get("muc_dich_su_dung") or "")).split(":")[0].strip()
                        if _d_dt == _c_dt and _d_md == _c_md:
                            _d_dup = cu_d
                            break
                if _d_dup is not None:
                    _extra = str(detail.get("muc_dich_su_dung") or "").split(":", 1)[-1].strip(" ,;")
                    if _extra and _extra not in giu["phan_ghi_them"]:
                        giu["phan_ghi_them"] = (giu["phan_ghi_them"] + "; " + _extra).lstrip("; ")
                    continue
                if detail not in giu["chi_tiet_dien_tich"]:
                    giu["chi_tiet_dien_tich"].append(detail)
            ghi = str(parcel.get("phan_ghi_them") or "").strip(" ;")
            if ghi and ghi not in giu["phan_ghi_them"]:
                giu["phan_ghi_them"] = (giu["phan_ghi_them"] + "; " + ghi).lstrip("; ")
            continue
        dedup.append(parcel)
    # Note nguon goc bi cat doan o IFilter ("duoc tach tu" khong co so) —
    # khong mang thong tin, bo.
    for parcel in dedup:
        # Dia chi bat theo prose "tai <dia chi> tai thua dat so N" — cat
        # duoi gioi tu "tại/là" con treo (13/10/2026).
        if parcel.get("dia_chi"):
            parcel["dia_chi"] = re.sub(
                r"(?i)\s+(?:tại|là|tại:|ở)\s*$", "", str(parcel["dia_chi"])
            ).strip(" ,;")
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
        # Bang GCN gop 2 dong chi tiet vao 1 o ("Trong đó 324,9 46,8 |
        # Đất ở Vườn | Lâu dài 2043") — o dien tich chua nhieu so tron:
        # tach so dau giu muc dich goc, so sau thanh chi tiet rieng de
        # R10 cong dung tong (11/10/2026).
        if parcel.get("chi_tiet_dien_tich"):
            mo_rong: list[dict] = []
            for detail in parcel["chi_tiet_dien_tich"]:
                dt = str(detail.get("dien_tich") or "")
                so_list = re.findall(r"\d[\d.,]*", dt)
                if len(so_list) > 1 and not re.search(r"[A-Za-z\u00c0-\u1ef9\u0110]", dt):
                    mo_rong.append({**detail, "dien_tich": so_list[0]})
                    for so in so_list[1:]:
                        mo_rong.append(
                            {"dien_tich": so, "muc_dich_su_dung": "", "thoi_han_su_dung": ""}
                        )
                else:
                    mo_rong.append(detail)
            parcel["chi_tiet_dien_tich"] = mo_rong
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
    r"|\u0110\u1ecba ch\u1ec9\s+n\u01a1i\s+c\u01b0\s+tr\u00fa|\u0110\u1ecba ch\u1ec9\s+c\u01b0\s+tr\u00fa|\u0110\u1ecba ch\u1ec9\s+\u0111\u0103ng\s+k\u00fd"
    r"|\u0110\u1ecba ch\u1ec9\s+th\u01b0\u1eddng\s+tr\u00fa|Tr\u00fa\s+t\u1ea1i"
    r"|\u0110\u0103ng\s+k\u00fd\s+(?:th\u01b0\u1eddng\s+tr\u00fa|h\u1ed9\s+kh\u1ea5u)|HKTT"
    r"|\u0110\u1ecba ch\u1ec9\s+ch\u1ed7 \u1edf(?:\s+hi\u1ec7n t\u1ea1i)?|\u0110\u1ecba ch\u1ec9\s+n\u01a1i \u1edf(?:\s+hi\u1ec7n t\u1ea1i)?"
    r"|\u0110\u1ecba ch\u1ec9(?:\s*/\s*(?:tr\u1ee5 s\u1edf ch\u00ednh|li\u00ean h\u1ec7))?(?!\s*(?:/\s*tr\u1ee5|th\u1eeda|nh\u00e0|\u0111\u1ea5t|li\u00ean h\u1ec7|giao d\u1ecbch|ch\u1ed7|n\u01a1i))"
    r"|(?:th\u01b0\u1eddng tr\u00fa|c\u01b0 tr\u00fa)(?!\s+cu\u1ed1i c\u00f9ng)"
)


def _cat_duoi_dia_chi(value: str) -> str:
    """Dong IFilter gop nhieu dong thanh 1 — cat phan duoi khong phai dia
    chi: cum quan he "Là vợ/con của..." hoac dau nguoi tiep theo
    ("... Xã Y  Ông: Nguyễn Bá Văn", "... Ninh Bình  2. Ông ...")."""
    addr_val = re.sub(r"\s+", " ", str(value or "")).strip(" .;")
    # Danh sach dia chi theo nguoi: "Địa chỉ: - Bùi Thị Hường: Thôn X ..."
    # — cat nhan "- <Tên>:" o dau (toi da 5 tu viet hoa, khong chua tu khoa
    # dia gioi nhu xa/phuong/thon).
    head_name = re.match(
        r"^-\s*([A-Z\u00c0-\u1ef9\u0110][^\d;:\n]{2,40}?)\s*:\s*",
        addr_val,
    )
    if head_name and not re.search(
        r"(?i)\b(x\u00e3|xa|ph\u01b0\u1eddng|phuong|th\u00f4n|thon|huy\u1ec7n|huyen|t\u1ec9nh|tinh|ng\u00f5|ngo|s\u1ed1|so|th\u1eeda|thua)\b",
        head_name.group(1),
    ):
        addr_val = addr_val[head_name.end():]
    addr_val = re.split(
        r"(?i)\s+(?:l\u00e0|la)\s+(?:v\u1ee3|ch\u1ed3ng|con|cha|m\u1eb9|ch\u00e1u|anh|ch\u1ecb)\b"
        r"|\s+\d+[.)]\s+(?=\u00d4ng|B\u00e0|Anh|Ch\u1ecb|[A-Z\u00c0-\u1ef9][a-z\u00e0-\u1ef9]*\s+[A-Z\u00c0-\u1ef9])"
        r"|\s+(?:\u00d4ng|B\u00e0|Anh|Ch\u1ecb)\s*:",
        addr_val, maxsplit=1,
    )[0].strip(" .;,")
    # Nhan trong ("2. Địa chỉ/trụ sở chính:") de lai dau ":" — khong phai
    # dia chi, tra rong thay vi day rac len form.
    if not re.search(r"[0-9A-Za-z\u00c0-\u1ef9]", addr_val):
        return ""
    return addr_val


# Moc cat duoi trong ho_ten: dau cau/cum khoi dau truong ("CCCD so...",
# "Sinh ngay...", "Dia chi...", "cap ngay...", vai tro "la vo/chong...").
_NAME_BOUNDARY_RE = re.compile(
    r"[,;(|:]"
    r"|\s+\d"
    r"|\s*[-\u2013\u2014]\s+(?i:sinh)\b"
    r"|\s+(?i:cccd|cmnd|cc\b|c\u0103n c\u01b0\u1edbc|c\u0103n c\u1ee9|gi\u1ea5y\b|\u0111\u1ecba ch\u1ec9|th\u01b0\u1eddng tr\u00fa|c\u01b0 tr\u00fa"
    r"|h\u1ed9 kh\u1ea9u|qu\u00ea qu\u00e1n|ch\u1ee9c v\u1ee5|hi\u1ec7n\b|l\u00e0\b|thu\u1ed9c\b|theo\b|\u0111\u01b0\u1ee3c\b|n\u01a1i\b|v\u1ee3\b|ch\u1ed3ng\b|kh\u00f4ng\b|ch\u1ec9\b|c\u0169ng\b|con\s+(?:\u0111\u1ebb|ru\u1ed9t)"
    r"|th\u01b0\s+k\u00fd|thu\s+ky|c\u1ed5\s+\u0111\u00f4ng|co\s+dong|ch\u1ee7\s+t\u1ecda|chu\s+toa|th\u00e0nh\s+vi\u00ean|thanh\s+vien)"
    r"|\s+mang\s+(?=c\u0103n|cccd|cmnd|gi\u1ea5y|h\u1ed9 chi\u1ebfu|s\u1ed5|theo)"
    r"|\s+v\u00e0\s+(?=\u00f4ng|b\u00e0|anh|ch\u1ecb)\b"
    r"|\s+(?:c\u00f3|cho)\s+(?=\d|\(|(?:m\u1ed9t|hai|ba|b\u1ed1n|n\u0103m|s\u00e1u|b\u1ea3y|t\u00e1m|ch\u00edn|m\u01b0\u1eddi)\s+ng\u01b0\u1eddi)"
    r"|\s+(?:sinh\b|ng\u00e0y\b|n\u0103m\s*[:\d]|s\u1ed1\s*[:\d]|c\u1ea5p\s*(?:ng\u00e0y|t\u1ea1i|:))"
)


_TEN_TO_CHUC_RE = re.compile(
    r"chi nhanh|cong ty|ngan hang|chi cuc|\bubnd\b|benh vien|\bso\s|ban giam",
    re.IGNORECASE,
)
# "Văn phòng"/"Phòng <đơn vị>" la co quan — nhung "Văn Phong" cung la
# ten nguoi that ("Trịnh Văn Phong"). Chi loai khi cum dung DAU ten
# (org mo dau bang "Văn phòng ..."); nguoi thi "Văn Phong" dung sau ho.
_TEN_TO_CHUC_DAU_RE = re.compile(
    r"^(?:van phong\b|phong\s+(?:ban|giam|thi|ke|to|hop|nhan|quan|kinh|ky|nghe|dao|hanh|cong|tuyen|phap|tu|xay|ly|tn|y|cntt|kd)\b)",
    re.IGNORECASE,
)


def _cat_ho_ten(name: str) -> str:
    """Cat phan duoi khong phai ten: keyword truong, dau cau, so."""
    return _NAME_BOUNDARY_RE.split(str(name or ""), maxsplit=1)[0].strip(" ;,.-\u2013\u2014`")


# "la" khong dua vao: "La Thị Hà" la ten that (ho La); tuong tu
# "Đỗ" (fold "do"), "Đồ" (ho Do) — chi giu tu chac chan khong phai
# ho/ten (13/10/2026).
_TU_GIOI_TU_DAU_TEN = {
    "theo", "tai", "cua", "va", "voi", "ve", "tren", "trong",
    "khi", "neu", "vay", "den", "giao", "cho", "boi", "nhu",
    "cung", "hoac", "hay", "ma", "thi",
}


def _ho_ten_hop_le(name: str) -> bool:
    """Tu dau phai viet hoa (chan "nhánh văn phòng...", cau van), khong
    chua tu khoa to chuc, va tu dau khong phai gioi tu/lien tu ("Theo
    CCCD..." bi bat lam ten "Theo" — 13/10/2026). Ten Viet 1-6 tu."""
    tokens = str(name or "").split()
    if not tokens or len(tokens) > 6:
        return False
    if not tokens[0][0].isupper():
        return False
    if _fold_text(tokens[0]) in _TU_GIOI_TU_DAU_TEN:
        return False
    folded = _fold_text(name)
    if _TEN_TO_CHUC_RE.search(folded) or _TEN_TO_CHUC_DAU_RE.search(folded):
        return False
    return True


def _ngay_sinh_conflict(a: str, b: str) -> bool:
    """Mau thuan ngay sinh: khac nam -> khac nguoi; hai ngay day du
    khac nhau -> khac nguoi; chi-nam trung nam voi ngay-du la cung
    nguoi (form tom tat). Mot ben trong -> khong ket luan."""
    if not (a and b) or a == b:
        return False
    a_year = re.search(r"(\d{4})\s*$", a)
    b_year = re.search(r"(\d{4})\s*$", b)
    a_full = "/" in a
    b_full = "/" in b
    if a_year and b_year and a_year.group(1) != b_year.group(1):
        return True
    return a_full and b_full


def _extract_plain_text_person_entries(section: str) -> list[dict]:
    section = unicodedata.normalize("NFC", str(section or ""))
    header_re = re.compile(
        r"(?i)^\s*(?:[-*]\s*)?(?:(?:ng\u01b0\u1eddi\s+)?(?:v\u1ee3|ch\u1ed3ng)\s*[–-]\s*)?"
        r"(?:\d+\s*\.\s*)?(?:v\u00e0\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\s+)?"
        r"(?:ng\u01b0\u1eddi\s+(?:v\u1ee3|ch\u1ed3ng)\s+)?(?P<title>\u00f4ng|b\u00e0)\s*:?\s*"
        r"(?P<name>.+?)(?=\s+Sinh ng\s*\u00e0y:|[;]|$)"
    )
    header_re = re.compile(
        r"(?i)^\s*(?:[-*]\s*)?(?:\u0110\u1ea1i di\u1ec7n:\s*)?(?:(?:ng\u01b0\u1eddi\s+)?(?:v\u1ee3|ch\u1ed3ng)\s*[â€“-]\s*)?"
        r"(?:\d+\s*\.\s*)?(?:v\u00e0\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\s+)?"
        r"(?:ng\u01b0\u1eddi\s+(?:v\u1ee3|ch\u1ed3ng)\s+)?(?P<title>\u00f4ng|b\u00e0)\s*:?\s*"
        r"(?P<name>.+?)(?=\s+(?:Sinh ng\s*\u00e0y|Ng\u00e0y\s+sinh):|\s+Ch\u1ee9c v\u1ee5\s*:|[;]|$)"
    )
    header_re = re.compile(
        r"(?i)^\s*(?:[-*]\s*)?(?:\u0110\u1ea1i di\u1ec7n:\s*)?(?:(?:ng\u01b0\u1eddi\s+)?(?:v\u1ee3|ch\u1ed3ng)\s*[\-\u2013:]\s*)?"
        r"(?:\d+\s*\.\s*)?(?:v\u00e0\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\s+)?"
        r"(?:ng\u01b0\u1eddi\s+(?:v\u1ee3|ch\u1ed3ng)\s+)?(?P<title>\u00f4ng|b\u00e0)\s*:?\s*"
        r"(?P<name>.+?)(?=\s+(?:Sinh ng\s*\u00e0y|Ng\u00e0y\s+sinh):|\s+Ch\u1ee9c v\u1ee5\s*:|[;]|$)"
    )
    birth_re = re.compile(r"(?i)(?:Sinh ng\s*\u00e0y|Ng\u00e0y\s+sinh|Sinh):?\s*(\d{1,2}/\d{1,2}/\d{4})")
    id_re = re.compile(r"(?i)(?:C\u0103n c\u01b0\u1edbc(?:\s+c\u00f4ng d\u00e2n)?|CCCD|CMND)\s*(?:s\u1ed1)?\s*:?\s*(\d+)")
    issue_place_re = re.compile(r"(?i)\bdo\s+([^\n]+?)\s+c\u1ea5p ng\u00e0y")
    issue_date_re = re.compile(r"(?i)c\u1ea5p ng\u00e0y\s*(\d{1,2}/\d{1,2}/\d{4})")
    header_re = re.compile(
        r"(?i)^\s*(?:(?:[-*:|\u201c\u201d\"]|\+|\|)\s*)*(?:(?:\u0110\u1ea1i di\u1ec7n|Dai dien|Ng\u01b0\u1eddi \u0111\u1ea1i di\u1ec7n|Nguoi dai dien)(?:\s+[^:]{0,80})?:|(?:Người|Nguoi)\s+đại\s+diện\s+(?:là|la)\s*)?"
        r"(?:\d+\s*\.\s*|\d+\s+(?=[\u00d4O]ng|[Bb]\u00e0\s*:))?(?:[|\-\u2013\u2014]\s*)?[\u201c\u201d\"']?\s*"
        r"(?:T\u00f4i (?:t\u00ean )?l\u00e0\s*:?|Ch\u00fang t\u00f4i l\u00e0\s*:?)?\s*"
        r"(?:(?:ng\u01b0\u1eddi\s+)?(?:v\u1ee3|ch\u1ed3ng)\s*[\-\u2013:]\s*)?"
        r"(?:(?:em|anh|ch\u1ecb|c\u00f4|ch\u00fa|b\u00e1c|d\u00ec|c\u1eadu|m\u1ee3)\s+(?:trai|g\u00e1i|d\u00e2u|r\u1ec3|\u0111\u1ebb|ru\u1ed9t)\s*[-\u2013:]\s*)?"
        r"(?:(?:v\u00e0|c\u00f9ng(?:\s+v\u1edbi)?)\s+(?:v\u1ee3|ch\u1ed3ng)(?:\s+l\u00e0)?\s+)?"
        r"(?:(?:b\u00ean|ben)\s+[A-Za-z\u00c0-\u1ef9]\s*[:.,]?\s*)?"
        r"(?:(?:con|m\u1eb9|b\u1ed1|cha|v\u1ee3|ch\u1ed3ng)\s+(?:(?:\u0111\u1ebb|ru\u1ed9t|nu\u00f4i)(?:\s+(?:t\u00f4i|c\u1ee7a\s+t\u00f4i))?|t\u00f4i)(?:\s+\u00f4ng\s+[^\d;:]{2,50}?)?\s*(?:[-\u2013\u2014:,]|l\u00e0)\s*)?"
        r"(?:ng\u01b0\u1eddi\s+(?:v\u1ee3|ch\u1ed3ng)\s+)?(?:v\u00e0\s+)?(?P<title>\u00f4ng/b\u00e0|ong/ba|\u00f4ng\s*\(b\u00e0\)|b\u00e0\s*\(\u00f4ng\)|\u00f4ng|ong|b\u00e0|ba|anh|ch\u1ecb|chi)\s*:?\s*"
        r"(?P<name>.+?)(?=[\s|]+\s*(?:[\-\u2013]\s*)?(?:Sinh ng\s*\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh|Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh|sinh n\u0103m|sinh ng\u00e0y)\s*[:\u2013-]?\s*(?:(?:19|20)\d{2}|\d{1,2}/\d{1,2}/\d{4})|\s+(?:[\-\u2013]\s*)?(?:Ch\u1ee9c v\u1ee5|Chuc vu|Ch\u1ee9c danh|Chuc danh)\s*:|\s+c\u00f3\s+(?:(?:m\u1eb9|b\u1ed1|cha|con|v\u1ee3|ch\u1ed3ng)(?:\s+(?:\u0111\u1ebb|ru\u1ed9t|nu\u00f4i))?|\d)\b|\s*\(\s*(?:Sinh|Ng\u00e0y)|[;]|$)"
    )
    birth_re = re.compile(r"(?i)(?:Sinh ng\s*\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh|Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh|Ng\u00e0y/th\u00e1ng/n\u0103m\s+sinh|Sinh)\s*[:\u2013-]?\s*(\d{1,2}/\d{1,2}/\d{4})")
    # Nguoi lon tuoi thuong chi ghi "Sinh nam 1965" — database chap nhan YYYY
    # (docs/spec/notary_v2/stage.md muc 5) nen giu nam lam ngay_sinh.
    # Gia tri chi co nam van nhan du nhan viet "Sinh ngay: 1982" (loi mau thuc te).
    birth_year_re = re.compile(r"(?i)(?:Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh|Sinh ng\s*\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh|Sinh)\s*[:–-]?\s*((?:19|20)\d{2})(?!\d)")
    id_re = re.compile(r"(?i)(?:C\u0103n c\u01b0\u1edbc(?:\s+(?:s\u1ed1\s+)?c\u00f4ng(?:\s+d\u00e2n)?)?(?:\s+m\u1edbi)?|Can cuoc(?:\s+cong(?:\s+dan)?)?|CCCD|CMND|\bCC)\s*(?:[A-Z\u00c0-\u1ef9\u0110][^\d:;\n]{0,40}?)?[\s|]*(?:(?:s\u1ed1|so)\s*:?|:)?[\s|]*(\d{3,4}(?:\s\d{3,4})+|\d{6,12})")
    issue_place_re = re.compile(
        r"(?i)\bdo\s+((?:(?!k[ýí]\s+ng\u00e0y)[^\n])+?)\s+(?:c\u1ea5p\s+ng\u00e0y|cap ngay|ng\u00e0y\s*\d)"
    )
    issue_date_re = re.compile(r"(?i)(?:c\u1ea5p ng\u00e0y|cap ngay|c\u1ea5p v\u00e0o ng\u00e0y|ng\u00e0y c\u1ea5p|ngay cap|c\u1ea5p|cap)\s*:?\s*(\d{1,2}/+\d{1,2}/+\d{4})")
    # "do <co quan> ngay DD/MM/YYYY" (nguon go thieu chu "cap") — "ngay"
    # tran chi tinh khi dung sau "do <co quan>", khong phai "ky ngay".
    issue_date_do_re = re.compile(
        r"(?i)\bdo\s+(?:(?!k[ýí]\s+ng\u00e0y)[^\n])+?\s+ng\u00e0y\s*(\d{1,2}/\d{1,2}/\d{4})"
    )
    # Nguoi tham gia thua ke ghi ten tran khong kem "Ong/Ba", vi du:
    # "Nguyen Van A - Vo ong X Sinh ngay: 01/01/1933;" — chi nhan khi cung
    # dong co ngay sinh (han che nhan nham cau van mo ta nhu "Di san").
    bare_header_re = re.compile(
        r"(?i)^\s*(?P<name>[^\d;:\n]{2,60}?)\s*[\-\u2013]\s*"
        r"(?P<role>(?:v\u1ee3|vo|ch\u1ed3ng|chong|con(?:\s+\u0111\u1ebb|\s+de)?)\b[^\n;]*?)"
        r"\s+(?:(?:Sinh ng\s*\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh)\s*[:\u2013-]?\s*\d{1,2}/\d{1,2}/\d{4}|(?:Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh)\s*[:\u2013-]?\s*(?:19|20)\d{2})"
    )
    # "Người chồng – Vũ Văn X, Sinh ngày ..." / "Con đẻ – Nguyễn Thị Y" —
    # vai tro dung dau dong, khong co danh xung Ong/Ba; chi nhan khi dong
    # co dau hieu nguoi (ngay sinh/giay to/dia chi).
    lead_role_re = re.compile(
        r"(?i)^\s*(?:[-\u2013\u2014\u2022]\s*)?(?:\[\d+\]\s*|\d+\.\s*)?(?:Ng\u01b0\u1eddi\s+)?(?P<role>v\u1ee3|ch\u1ed3ng|con\s+(?:g\u00e1i|trai)|con|ch\u00e1u|m\u1eb9|b\u1ed1|cha|anh|ch\u1ecb|em|\u0111\u1ed3ng\s+(?:s\u1eed\s+d\u1ee5ng|s\u1edf\s+h\u1eefu)|(?:\u00f4ng|b\u00e0)\s+(?:ngo\u1ea1i|n\u1ed9i))\b"
        r"(?:\s+(?:\u0111\u1ebb|ru\u1ed9t|nu\u00f4i|d\u00e2u|r\u1ec3|ngo\u1ea1i|n\u1ed9i))?(?:\s*(?:[-\u2013\u2014:]|l\u00e0)\s*|\s+)"
        r"(?P<name>(?:(?:\u00f4ng|\u00d4ng|b\u00e0|B\u00e0|anh|Anh|ch\u1ecb|Ch\u1ecb|c\u00f4|C\u00f4|ch\u00fa|Chú|em|Em)\s+)?[A-Z\u00c0-\u1ef9\u0110][^\d;:\n]{1,60}?)"
        r"(?=\s+(?:sinh|ng\u00e0y|n\u0103m|cccd|c\u0103n c\u01b0\u1edbc|c\u1ea5p|\u0111\u1ecba ch\u1ec9|th\u01b0\u1eddng tr\u00fa|c\u01b0 tr\u00fa|n\u01a1i|h\u1ed9 kh\u1ea9u)\b|[;]|$)"
    )
    bare_name_noise_re = re.compile(
        r"chung toi|nguoi de lai|di san|van ban|loi chung|cong chung|thua ke|tai san",
        re.IGNORECASE,
    )
    # "Toi ten la: Tran Gia Huy; Sinh ngay: ..." — ten tran khong
    # Ông/Bà, nhan ngay sinh cung dong de chac la nguoi.
    intro_bare_re = re.compile(
        r"(?i)^\s*(?:Tôi (?:tên )?là|Tên tôi(?:\s+là)?|Tôi\s+(?:Ông|Bà))\s*[:–\-]?\s*(?P<name>[^;|\-\u2013\n]+?)"
        r"(?:\s*[-\u2013]\s*[^\n;|]{0,60}?)?(?:\s*[;|]|\s+)[\s|]*"
        r"(?:Sinh ngày|Ngày sinh|Sinh ngay|Ngay sinh|Sinh năm|Năm sinh|Sinh nam|Nam sinh)"
    )
    # Don hanh chinh co nhan nguoi danh so: "1. Người xin gia hạn sử dụng
    # đất: Nguyễn Thị Chúc" — ten khong kem danh xung Ong/Ba va thuong khong
    # co giay to, nen danh dau de vuot cong loc "phai co ngay sinh/ID".
    labeled_name_re = re.compile(
        r"(?i)^\s*(?:\[\d+\]\s*|\d+\s*(?:\.\d+)*[.)]?\s*)?"
        r"(?:(?:t\u00ean\s+)?(?:ng\u01b0\u1eddi|nguoi)\s+"
        r"(?:xin|n\u1ed9p|nop|l\u1eadp|lap|\u0111\u1ec1 ngh\u1ecb|de nghi|y\u00eau c\u1ea7u|yeu cau|\u0111\u0103ng k\u00fd|dang ky|k\u00fd|ky|nh\u1eadn|nhan|giao)"
        r"|H\u1ecd\s+v\u00e0\s+t\u00ean)"
        r"[^:\n]{0,60}:\s*(?P<name>[A-Z\u00c0-\u1ef9\u0110][^\d;:\n]{2,60}?)\s*$"
    )
    _ADDR_LABEL = _DIA_CHI_LABEL
    address_re = re.compile(
        r"(?im)^\s*(?:\[\d+\]\s*|[a-zA-Z][.)]\s*|\d+(?:\.\d+)*[.)]?\s*)?(?:C\u1ea3 hai(?:\s+\u00f4ng b\u00e0|\s+v\u1ee3 ch\u1ed3ng)?|C\u00f9ng|Hai v\u1ee3 ch\u1ed3ng|T\u1ea5t c\u1ea3(?:\s+\u00f4ng b\u00e0)?)?\s*(?:"
        + _ADDR_LABEL + r")\s*:?\s*(.+)$"
    )
    shared_addr_re = re.compile(
        r"(?i)^\s*(?:c\u1ea3 hai|hai\s+v\u1ee3 ch\u1ed3ng|hai\s+\u00f4ng b\u00e0|c\u1ea3\s+\S+(?:\s+\S+){0,2}\s+c\u00f9ng|c\u00f9ng|t\u1ea5t c\u1ea3)\b"
    )
    # Dia chi nam giua dong (vi du "...; Nơi thường trú: X") — chi dung khi
    # nhan dau dong khong khop; loai "Nơi thường trú cuối cùng..." cua nguoi
    # da chet de khong vo tinh gan dia chi nguoi chet cho nguoi song.
    address_fallback_re = re.compile(
        r"(?i)(?:" + _ADDR_LABEL + r")\s*:?\s*(?!\s*cu\u1ed1i c\u00f9ng\b)(.+)$"
    )

    lines = _split_section_lines(section)
    # Nguoi liet ke danh so khong danh xung trong don nhieu nguoi
    # ("Chúng tôi là: 1. Trần Văn Cát   Sinh ngày: ...") — chi nhan khi
    # cung dong co ngay sinh de chac la nguoi (11/10/2026).
    numbered_bare_re = re.compile(
        r"(?i)\s*\d{1,2}(?:\.\d{1,2})*\.\s*(?P<name>[A-Z\u00c0-\u1ef9\u0110][^\d;:\n]{2,60}?);?\s+"
        r"(?=Sinh ng\s*\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh|Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh|sinh ng\u00e0y|sinh n\u0103m)"
    )
    # Dong "2. Ông X có mẹ đẻ là bà Y; Sinh ngày..." — "bà Y" la nguoi
    # rieng bi nuot vao khoi X; tach "là bà/ông <tên>" thanh dong ao de
    # parser chuan nhan ca hai (10/10/2026 — don xac nhan nhan than).
    _kinship_la_re = re.compile(
        r"(?i)\s+(?:c\u00f3\s+(?:m\u1eb9|b\u1ed1|cha|con|v\u1ee3|ch\u1ed3ng)(?:\s+(?:\u0111\u1ebb|ru\u1ed9t|nu\u00f4i))?|(?:m\u1eb9|b\u1ed1|cha|con|v\u1ee3|ch\u1ed3ng)\s+c\u1ee7a\s+(?:\u00f4ng|b\u00e0)\s+[^\n]{2,50}?)\s+l\u00e0\s+"
        r"(?=(?:\u00f4ng|b\u00e0)\s+[A-Z\u00c0-\u1ef9\u0110])"
    )
    # Hang vo chong chung mot dong danh sach:
    # "- Ông Trần Văn Khải và bà Bà: Trần Thị Lan; Sinh ngày: ..." —
    # tach thanh 2 dong ao; danh xung lap "bà Bà:" gom ve "Bà:".
    _va_couple_re = re.compile(
        r"(?i)^(?P<lead>\s*[-–—•]?\s*(?:\d+[.)]?\s*)?)"
        r"(?P<t1>ông|bà)\s+(?P<n1>[A-ZÀ-ỹĐ][^\d;:()\n]{1,50}?)\s+"
        r"và\s+(?P<t2>ông|bà)\s+(?:(?:ông|bà)\s*:\s*)?(?P<rest>[A-ZÀ-ỹĐ][^\n]*)$"
    )
    _split_lines: list[str] = []
    for ln in lines:
        couple = _va_couple_re.match(ln)
        if couple:
            parts = [
                couple.group("lead") + couple.group("t1") + " " + couple.group("n1"),
                couple.group("t2") + " " + couple.group("rest"),
            ]
        else:
            kinship_match = _kinship_la_re.search(ln)
            parts = (
                [ln[: kinship_match.start()], ln[kinship_match.end():]]
                if kinship_match
                else [ln]
            )
        for part in parts:
            # O trong "| |" truoc nhan danh xung ("| | Bà: Y") la ranh
            # nguoi moi trong bang ngan hang — tach dong ao. Chi tach
            # truoc "Ông:/Bà:..." de khong be "Tên ...; | | Sinh ngày"
            # (truong van doc tren cung dong ao).
            _split_lines.extend(
                re.split(
                    r" \| +\| (?=(?:\u00d4ng|B\u00e0|Anh|Ch\u1ecb|C\u00f4|Ch\u00fa|B\u00e1c|D\u00ec|C\u1eadu|M\u1ee3)\s*:)",
                    part,
                )
            )
    lines = _split_lines
    # Dong dau section thuong la "I. Bên thế chấp: Ông X | Năm sinh: ..."
    # (mau ngan hang viet lien tieu de voi nguoi) — bo tieu de bên de ten
    # nguoi thanh dau dong.
    if lines:
        lines[0] = re.sub(
            r"(?i)^\s*(?:(?:I{1,3}|IV|V|VI{0,3})\.\s*(?:\|\s*)?)?B\u00caN\b[^:\n]{0,60}:\s*",
            "",
            lines[0],
        )
    headers: list[tuple[int, re.Match[str]]] = []
    address_lines: list[tuple[int, str, str]] = []
    labeled_person_idx: set[int] = set()
    keyed_addrs: dict[str, str] = {}
    keyed_addr_mode = False
    prev_intro_bare = False
    gom_list = False
    for idx, line in enumerate(lines):
        # "c) Địa chỉ:" rong roi den "Ông X: <dia chi>" tung dong — dia
        # chi ca nhan theo ten (mau 18 - 13/10/2026).
        if keyed_addr_mode:
            km = re.match(
                r"^\s*[-–—]?\s*(?:(?:Địa\s+ch[ỉủ]|Nơi\s+thường\s+trú)(?:\s+của)?\s+|Dia\s+chi\s+cua\s+|Noi\s+thuong\s+tru(?:\s+cua)?\s+)?(?:(?:Ông|ông|Bà|bà)\s+)?([A-ZÀ-ỹĐ][^\d;:]{2,60}?)\s*(?:tại)?\s*:\s*(\S.{3,}?)\s*$",
                line,
            )
            if km:
                keyed_addrs[_fold_text(km.group(1))] = _cat_duoi_dia_chi(km.group(2))
                continue
            if re.match(r"\s*(?:[a-zA-Z][.)]|\d+\.)", line):
                keyed_addr_mode = False
            elif re.match(r"^\s*(?:th\u00f4n|x\u00e3|ph\u01b0\u1eddng|s\u1ed1|t\u1ed5|khu|qu\u1eadn|th\u00e0nh|huy\u1ec7n|x\u00f3m|\u1ea5p|b\u1ea3n|\u0111\u1ed9i)", line, re.I):
                # Dong dia chi tran ngay sau "c) Dia chi:" rong — dia chi
                # CHUNG cho moi nguoi trong muc (don DK18 - 13/10/2026).
                address_lines.append(
                    (idx, line.strip(" ;"), _cat_duoi_dia_chi(line), True)
                )
                keyed_addr_mode = False
                continue
        # "Toi la:" dung rieng 1 dong -> ten tran o dong ke tiep
        # ("Nguyen Thi Yen\t\tSinh ngay: ...").
        if (
            prev_intro_bare
            and re.search(r"\d", line)
            and header_re.search(line) is None
        ):
            next_match = re.match(
                r"\s*(?P<name>[A-Z\u00c0-\u1ef9\u0110][^\d;:\n]{2,60}?)"
                r"\s+(?:[-\u2013]\s*)?(?:Sinh ng\s*\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh|Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh)",
                line,
            )
            if next_match:
                headers.append((idx, next_match))
        prev_intro_bare = bool(
            re.match(r"(?i)^\s*(?:T\u00f4i|Ch\u00fang t\u00f4i)\s+l\u00e0\s*:?\s*$", line)
        ) or (prev_intro_bare and not line.strip())
        # "Chúng tôi gồm:" / "Chúng tôi là:" mo danh sach TEN TRAN (VB cua
        # nguoi dai dien — ong Nghinh 12/10/2026): cac dong ten khong danh
        # xung/so van la nguoi khi di kem "Sinh ngay" tren cung dong.
        if re.match(
            r"(?i)^\s*Ch\u00fang t\u00f4i\s*(?:g\u1ed3m|l\u00e0\s*:|:)",
            line,
        ):
            gom_list = True
        elif gom_list and re.match(
            r"(?i)^\s*(?:Nay\b|\u0110I\u1ec0U|\u0110i\u1ec1u\s+\d|N\u1ed9i\s+dung|Khi\s|c\u00f2n\s+s\u1ed1ng)",
            line,
        ):
            gom_list = False
        match = header_re.search(line)
        if match is None:
            match = numbered_bare_re.search(line)
        if match is None and gom_list and re.search(r"\d", line):
            match = re.match(
                r"\s*(?P<name>[A-Z\u00c0-\u1ef9\u0110][^\d;:\n]{2,60}?)"
                r"\s+(?:[-\u2013]\s*)?(?:Sinh ng\s*\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh|Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh)",
                line,
            )
        if match:
            # "2. Con dâu - bà X" — header nam bat ca cum vai tro; neu
            # "ten" mo dau bang tu quan he thi thu lai bang lead_role_re.
            _hm = (
                (match.groupdict().get("title") or "") + " " + (match.groupdict().get("name") or "")
            ).strip()
            if re.match(
                r"(?i)^\s*(?:người\s+)?(?:vợ|chồng|con\s+(?:gái|trai)|con|cháu|mẹ|bố|cha|anh|chị|em|đồng\s+(?:sử\s+dụng|sở\s+hữu)|(?:ông|bà)\s+(?:ngoại|nội))"
                r"(?:\s+(?:đẻ|ruột|nuôi|dâu|rể|ngoại|nội))?(?:\s*(?:[-–—:]|là)\s*|\s+)",
                _hm,
            ):
                _lead = lead_role_re.search(line)
                if _lead:
                    match = _lead
        if match:
            # Dong pha he ("Ông X co vo la ba Y (Sinh ngay...)") — ngay
            # sinh/ID tren dong la cua nguoi khac, bo ca dong.
            line_fold = _fold_text(line)
            la_pha_he = re.search(r"\bco\s+(vo|chong)\s+la\b", line_fold) is not None
            ngoac_nguoi_khac = bool(
                re.search(r"\(\s*(?:Sinh|Ng\u00e0y|CCCD|CMND|C\u0103n c\u01b0\u1edbc)", line)
            )
            # "CHI NHÁNH SÓC SƠN" — danh xung "Chị" an chu "Chi" cua to
            # chuc, khong phai nguoi (cong van ngan hang).
            title_fold = _fold_text((match.groupdict().get("title") or ""))
            name_fold = _fold_text(match.groupdict().get("name") or "")
            la_chi_nhanh = title_fold == "chi" and name_fold.startswith("nhanh")
            # "Ông Gia và bà Mỳ có 6 người con..." — nhac lai vo chong
            # nguoi chet trong van xuoi, khong phai hang duong su (13/10/2026).
            la_vo_chong_van_xuoi = bool(
                re.search(
                    r"(?i)^\s*[\u00d4O]ng\s+\S.*?\bv\u00e0\s+(?:\u00f4ng|b\u00e0)\s+\S+\s+(?:c\u00f3|l\u00e0)\b",
                    line,
                )
            )
            if not la_pha_he and not ngoac_nguoi_khac and not la_chi_nhanh and not la_vo_chong_van_xuoi:
                headers.append((idx, match))
                # O nhan "Ông: <ten>" / "Bà: <ten>" dung mot minh (danh
                # sach thanh vien to dinh gia) — nhan danh xung la du
                # hieu nguoi, vuot cong "phai co sinh/ID/chuc vu".
                if re.match(r"^\s*(?:[ÔO]ng|[Bb]\u00e0)\s*:", line):
                    labeled_person_idx.add(idx)
        else:
            bare_match = bare_header_re.search(line)
            if bare_match:
                bare_name = re.sub(r"\s+", " ", bare_match.groupdict().get("name") or "").strip(" ;,.")
                if len(bare_name.split()) >= 2 and not re.search(r"\d", bare_name):
                    bare_fold = _fold_text(bare_name)
                    if bare_fold and not bare_name_noise_re.search(bare_fold):
                        headers.append((idx, bare_match))
            else:
                intro_match = intro_bare_re.search(line)
                if intro_match:
                    intro_name = re.sub(r"\s+", " ", intro_match.groupdict().get("name") or "").strip(" ;,.")
                    if len(intro_name.split()) >= 2 and not re.search(r"\d", intro_name):
                        intro_fold = _fold_text(intro_name)
                        if intro_fold and not bare_name_noise_re.search(intro_fold):
                            headers.append((idx, intro_match))
                elif re.search(r"\d", line):
                    lead_match = lead_role_re.search(line)
                    if lead_match:
                        lead_name = _cat_ho_ten(lead_match.groupdict().get("name") or "")
                        if len(lead_name.split()) >= 2 and not re.search(r"\d", lead_name):
                            lead_fold = _fold_text(lead_name)
                            if lead_fold and not bare_name_noise_re.search(lead_fold):
                                headers.append((idx, lead_match))
        # "Chức vụ: Ông Nguyễn Hữu Công" — nhan chuc vu di truoc danh
        # xung giua dong (bang thanh phan to dinh gia ngan hang).
        labeled_match = (
            labeled_name_re.search(line)
            or re.search(
                r"(?i)^\s*(?:Ch\u1ee9c v\u1ee5|Chuc vu|Ch\u1ee9c danh|Chuc danh)\s*:?\s*"
                r"(?P<title>\u00f4ng|b\u00e0)\s+"
                r"(?P<name>[A-Z\u00c0-\u1ef9\u0110][^\d;:\n]{2,60}?)\s*$",
                line,
            )
            or re.search(
                # "1.1. Tên: Ha Van Thinh; Sinh ngay:" — nhan "Tên:" tran
                # khong danh xung (mau 11/DK don bien dong — 12/10/2026).
                r"(?i)^\s*(?:[a-zA-Z][.)]|\d+(?:\.\d+)*[.)]?)?\s*T\u00ean\s*:\s*"
                # Gia tri go thua chu "Tên" lan nua: "Tên: Tên  Ông X" (mau 18).
                r"(?:T\u00ean\s+)?"
                r"(?:(?P<title>\u00f4ng|b\u00e0)\s+)?"
                r"(?P<name>[A-Z\u00c0-\u1ef9\u0110][^\d;:\n]{2,60}?)\s*(?=[;|]|$|[\s|]+\s*(?:Sinh|Ng\u00e0y))",
                line,
            )
            or re.search(
                # "- Căn cước công dân ông X số 036..." — nguoi nam
                # trong dong giay to (mau 11/DK — 12/10/2026).
                r"(?i)^\s*[-\u2013*]?\s*(?:C\u0103n c\u01b0\u1edbc(?:\s+c\u00f4ng d\u00e2n)?|CCCD|CMND)\s+"
                r"(?P<title>\u00f4ng|b\u00e0)\s+"
                r"(?P<name>[A-Z\u00c0-\u1ef9\u0110][^\d;:\n]{2,60}?)\s+s\u1ed1",
                line,
            )
        )
        if labeled_match:
            labeled_name = _cat_ho_ten(labeled_match.groupdict().get("name") or "")
            if len(labeled_name.split()) >= 2 and not bare_name_noise_re.search(_fold_text(labeled_name)):
                headers.append((idx, labeled_match))
                labeled_person_idx.add(idx)
        # Khong "continue" sau header: dia chi co the nam chung dong
        # voi ten ("...; Nơi thường trú: X").
        address_match = address_re.search(line)
        if not address_match and re.match(r"\s*\d+(?:\.\d+)*\.\s*\u0110\u1ecba ch\u1ec9\s+li\u00ean h\u1ec7", line, re.I):
            # "2. Địa chỉ liên hệ (điện thoại, email...): X" — truong
            # dia chi nguoi trong don mau 09 gia han; nhan "Địa chỉ liên
            # hệ" binh thuong thuoc co quan/van phong nen chi tinh khi
            # dong mo dau bang so muc.
            address_match = re.search(
                r"(?i)\u0110\u1ecba ch\u1ec9\s+li\u00ean h\u1ec7[^:\n]*:\s*(.+)$", line
            )
        if not address_match:
            address_match = address_fallback_re.search(line)
            if address_match:
                # Nhan dia chi nam TRONG ngoac "(...Thuong tru tai: X)" thuoc
                # ve nguoi khac (vo/chong ghi kem) — bo qua.
                before = line[: address_match.start(1)]
                if before.count("(") > before.count(")"):
                    address_match = None
        if address_match:
            addr_val = _cat_duoi_dia_chi(address_match.group(1))
            # "c) Địa chỉ: Địa chỉ thường trú ông X tại: A.Địa chỉ thường
            # trú bà Y: B." — nhieu nhan keyed tren 1 dong (IFilter gop
            # dong): boc tung doan "nhan + danh xung + ten + :|tại:" thanh
            # keyed_addrs, khong de ca blob lam dia chi chung
            # (mau 18 - 13/10/2026).
            _keyed_inline = list(
                re.finditer(
                    r"(?i)(?:\u0110\u1ecba\s+ch[\u1ec9\u1ee7]\s+th\u01b0\u1eddng\s+tr\u00fa|N\u01a1i\s+th\u01b0\u1eddng\s+tr\u00fa|\u0110\u1ecba\s+ch[\u1ec9\u1ee7])"
                    r"\s+(?i:[\u00d4O]ng|[Bb]\u00e0)\s+([A-Z\u00c0-\u1ef9\u0110][^\d;:]{1,40}?)\s*(?:t\u1ea1i)?\s*:",
                    addr_val,
                )
            )
            if _keyed_inline:
                for _ki, _km in enumerate(_keyed_inline):
                    _seg_end = (
                        _keyed_inline[_ki + 1].start()
                        if _ki + 1 < len(_keyed_inline)
                        else len(addr_val)
                    )
                    _v = _cat_duoi_dia_chi(addr_val[_km.end():_seg_end])
                    if _v:
                        keyed_addrs[_fold_text(_km.group(1))] = _v
                addr_val = ""
            addr_val = re.sub(r"(?i)^t\u1ea1i:?\s*", "", addr_val).strip(" ;,.")
            # Muc con "X.Y. Địa chỉ:" / "c) Địa chỉ:" trong don mau (1.3
            # cua mau 11/DK, c) cua mau 18) la truong CHUNG cho moi nguoi
            # khai trong muc X — danh dau shared de dien cho nguoi chua
            # co dia chi (12/10/2026).
            _sub_item = bool(re.match(r"\s*(?:\d+\.\d+\.|[a-z][.)])", line)) or bool(
                re.search(r"[a-zđ][.)]\s*(?:" + _ADDR_LABEL + r")", line, re.I)
            )
            address_lines.append(
                (idx, line.strip(" ;"), addr_val, _sub_item or bool(shared_addr_re.match(line)))
            )
            if _sub_item and not addr_val:
                keyed_addr_mode = True

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
        # Ngoac "(Sinh ngay/CCCD/Thuong tru...)" trong chunk thuoc ve NGUOI
        # KHAC (vo/chong ghi kem trong ngoac) — header line chua ngoac da bi
        # loc tu truoc, nen moi ngoac con lai trong chunk deu khong phai
        # du lieu cua nguoi nay. Cat khoi vung soi truong de tranh "doi"
        # giay to cua vo/chong (ong da chet lay CCCD cua vo).
        chunk_scan = re.sub(
            r"\([^)]*(?:Sinh|Ng\u00e0y|CCCD|CMND|C\u0103n c\u01b0\u1edbc|Th\u01b0\u1eddng tr\u00fa|N\u01a1i)[^)]*\)",
            " ",
            chunk,
        )
        # Nam bi tach khoang trang trong nguon ("05/07/199 2") — gop lai
        # truoc khi soi ngay (13/10/2026).
        chunk_scan = re.sub(r"(\d{1,2}/\d{1,2}/\d{3})\s+(\d)\b", r"\1\2", chunk_scan)
        groups = match.groupdict()
        if groups.get("title"):
            title = str(groups.get("title") or "").strip().lower()
            title_fold = _fold_text(title)
            if title_fold in ("ong", "anh"):
                gioi_tinh = "\u00d4ng"
            elif title_fold in ("ong/ba", "ong / ba", "ong(ba)", "ba(ong)", ""):
                # Khong suy gioi tinh (Owner 06/10/2026): nhan "Ông/bà"
                # hoac thieu chuc danh -> de trong, nguoi dung chon o Stage.
                gioi_tinh = ""
            else:
                gioi_tinh = "B\u00e0"
            ho_ten = re.sub(r"\s+", " ", match.groupdict().get("name") or "").split("|")[0].strip(" ;,.-\u2013\u2014`")
            ho_ten = re.split(r"(?i)\s*[-\u2013\u2014]\s+(?:con\b|ch\u00e1u\b|chau\b|v\u1ee3\b|ch\u1ed3ng\b|l\u00e0\b|b\u1ed1\b|m\u1eb9\b|cha\b|b\u00ean\b|ch\u1ecb\b|chi\b|anh\b|em\b|c\u00f4\b|co\b|ch\u00fa\b|chu\b|b\u00e1c\b|bac\b|d\u00ec\b|di\b|c\u1eadu\b|cau\b|m\u1ee3\b|mo\b|\u00f4ng\b|b\u00e0\b|(?:ch\u1ee9c|chuc)\s*(?:v\u1ee5|vu|danh)\b)", ho_ten, maxsplit=1)[0].strip(" ;,.-\u2013\u2014`")
            ho_ten = _cat_ho_ten(ho_ten)
            # Danh xung lap/dinh trong ten ("là bà Bà Hoàng Thị Mỹ" —
            # nguon go thua "bà Bà") — gioi tinh da chot tu title.
            ho_ten = re.sub(r"(?i)^(?:[ôo]ng|bà)\s+", "", ho_ten).strip(" ;,.-\u2013\u2014`")
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
            base_name = re.split(r"(?i)\s*[-\u2013\u2014]\s+(?:con\b|ch\u00e1u\b|chau\b|v\u1ee3\b|ch\u1ed3ng\b|l\u00e0\b|b\u1ed1\b|m\u1eb9\b|cha\b|b\u00ean\b|ch\u1ecb\b|chi\b|anh\b|em\b|c\u00f4\b|co\b|ch\u00fa\b|chu\b|b\u00e1c\b|bac\b|d\u00ec\b|di\b|c\u1eadu\b|cau\b|m\u1ee3\b|mo\b|\u00f4ng\b|b\u00e0\b|(?:ch\u1ee9c|chuc)\s*(?:v\u1ee5|vu|danh)\b)", base_name, maxsplit=1)[0].strip(" ;,.-\u2013\u2014`")
            base_name = _cat_ho_ten(base_name)
            role_phrase = re.sub(r"\s+", " ", groups.get("role") or "").strip(" ;,.")
            role_fold = _fold_text(role_phrase)
            # Danh xung di kem ten ("Con dau - ba Nguyen Thi Trang") — tach
            # khoi ten, dung de xac dinh gioi tinh.
            _dx = re.match(
                r"(?i)^(ông|bà|anh|chị|cô|chú|bác|dì|cậu|mợ|em)\s+", base_name
            )
            _dx_gender = ""
            if _dx:
                _dx_gender = (
                    "Ông"
                    if _fold_text(_dx.group(1)) in ("ong", "anh", "chu", "cau", "bac")
                    else "Bà"
                )
                base_name = base_name[_dx.end() :].strip()
            if re.search(r"\b(?:vo|me|dau|con gai|chi)\b", role_fold):
                gioi_tinh = "Bà"
            elif re.search(r"\b(?:chong|bo|cha|re|con trai|anh)\b", role_fold):
                gioi_tinh = "Ông"
            elif _dx_gender:
                gioi_tinh = _dx_gender
            else:
                # Khong suy tu chu "Thi" trong ten (Owner 06/10/2026).
                gioi_tinh = ""
            person = {
                "gioi_tinh": gioi_tinh,
                "ho_ten": base_name,
                "_line_idx": line_idx,
                "raw_text": chunk,
            }
        birth_match = birth_re.search(chunk_scan)
        birth_year_match = birth_year_re.search(chunk_scan) if not birth_match else None
        has_birth = bool(birth_match or birth_year_match)
        ngay_sinh, chi_co_nam = _chuan_hoa_ngay_sinh(
            birth_match.group(1) if birth_match else "",
            birth_year_match.group(1) if birth_year_match else "",
        )
        person["ngay_sinh"] = ngay_sinh
        person["chi_co_nam_sinh"] = chi_co_nam
        id_match = id_re.search(chunk_scan)
        if not id_match:
            # Form viet tat "Ông Vũ Văn Thạnh số: 036070006771 Cấp ngày ..."
            # — "số:" tran khong nhan CCCD; so 9-12 chu so van la giay to.
            id_match = re.search(r"\bs\u1ed1\s*:\s*(\d{3,4}(?:\s\d{3,4})+|\d{9,12})(?!\d)", chunk_scan)
        if not id_match:
            # To khai thue "[06] Số CMND/CCCD/Hộ chiếu ...:\n 036158024616"
            # — nhan bat dau bang "Số <loai giay to>", so o dong sau.
            id_match = re.search(
                r"(?i)\bS\u1ed1\s+(?:CMND|CCCD|C\u0103n c\u01b0\u1edbc|H\u1ed9 chi\u1ebfu)[^\n:]{0,60}:\s*(\d{9,12})",
                chunk_scan,
            )
        person["cccd"] = re.sub(r"\s+", "", id_match.group(1)) if id_match else ""
        issue_place_match = issue_place_re.search(chunk_scan)
        if not issue_place_match:
            cap_tai = re.search(
                r"(?i)c\u1ea5p\s+t\u1ea1i\s+([^\n,;.]{2,80}?)\s+ng\u00e0y\s*(\d{1,2}/\d{1,2}/\d{4})",
                chunk_scan,
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
                chunk_scan,
            )
        if not issue_place_match:
            # Form "Nơi cấp Cục cảnh sát ..." (don xac nhan thoi han dat).
            issue_place_match = re.search(
                r"(?i)\bN\u01a1i\s+c\u1ea5p\s*[:;,]?\s*([^\n,;.]+?)(?=\s*[,;.]|\s*$)",
                chunk_scan,
            )
        person["noi_cap"] = re.sub(r"\s+", " ", issue_place_match.group(1)).strip(" ;,.") if issue_place_match else ""
        # Bo ngay cap HO CHIEU ("Hộ chiếu số: X do Y cấp ngày D") — khong
        # phai ngay cap CCCD (Hoàn — HĐCN cũ Thường Lan — 13/10/2026).
        def _issue_date_first(rx):
            for m in rx.finditer(chunk_scan):
                if re.search(
                    r"(?i)h\u1ed9\s+chi\u1ebfu|ho chieu|passport",
                    chunk_scan[max(0, m.start() - 140):m.start()],
                ) and not re.search(
                    r"(?i)c\u0103n c\u01b0\u1edbc|cccd|cmnd",
                    chunk_scan[max(0, m.start() - 140):m.start()],
                ):
                    continue
                return m
            return None
        issue_date_match = min(
            (m for m in (_issue_date_first(issue_date_re), _issue_date_first(issue_date_do_re)) if m),
            key=lambda m: m.start(),
            default=None,
        )
        if issue_date_match:
            # Chuan hoa "//" kep go nham ("23/04//2021" -> "23/04/2021").
            person["ngay_cap_cccd"] = re.sub(r"/+", "/", issue_date_match.group(1))
        else:
            # So Excel ("cap ngay 44546") — doi sang ngay that.
            person["ngay_cap_cccd"] = _doi_ngay_excel(chunk_scan)
        address_match = next((item for item in address_lines if line_idx <= item[0] < next_idx), None)
        person["dia_chi"] = address_match[2] if address_match else ""
        if not person["dia_chi"]:
            # To khai thue: "[10] Dia chi cu tru:" chia o con "[10.3] To/thon:",
            # "[10.5] Quan/huyen:"... — chi gop o con cung so voi nhan cha
            # (tranh [17.x] dia chi thua dat) va bo phan da chua san (11/10/2026).
            parent = re.search(
                r"\[(\d+)\]\s*(?:\u0110\u1ecba ch\u1ec9|\u0110\u1ecba ch\u1edd)[^\n:]{0,40}:",
                chunk_scan,
            )
            if parent:
                sub_re = re.compile(
                    r"\[" + re.escape(parent.group(1)) + r"\.\d+\]\s*"
                    r"(?:S\u1ed1\s+nh\u00e0|\u0110\u01b0\u1eddng/ph\u1ed1|T\u1ed5/th\u00f4n|Ph\u01b0\u1eddng/x\u00e3/th\u1ecb tr\u1ea5n|Qu\u1eadn/huy\u1ec7n|T\u1ec9nh/Th\u00e0nh ph\u1ed1)"
                    r"\s*:\s*([^\[\n]+?)(?=\s*\[\d|\s*$)"
                )
                sub_parts: list[str] = []
                for sm in sub_re.finditer(chunk_scan):
                    val = sm.group(1).strip(" ;,.|\t")
                    val = re.sub(r"^[.\u2026\s]+|[.\u2026\s]+$", "", val)
                    if val and all(val not in p for p in sub_parts):
                        sub_parts.append(val)
                if sub_parts:
                    person["dia_chi"] = ", ".join(sub_parts)
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
        # "ngay chet" trong checklist khong du de loai). "chet nam YYYY"
        # chi loai khi nam ngay tren dong ten — "chet nam" trong khoi co
        # the la ke bo/me chet ("Me de toi - ba X (sinh nam 1958, chet
        # nam 2016)" — don xac nhan quan he 12/10/2026).
        if re.search(r"\b(?:chet|mat)\s+ngay\s*[:.-]?\s*\d", _fold_text(chunk_scan)):
            continue
        if re.search(
            r"\b(?:chet|mat)\s+nam\s*[:.-]?\s*(?:19|20)\d{2}",
            _fold_text(lines[line_idx]),
        ):
            continue
        role_match = re.search(r"(?i)(?:Ch\u1ee9c v\u1ee5|Chuc vu|Ch\u1ee9c danh|Chuc danh)\s*:", chunk_scan)
        if not role_match:
            # Nhan chuc danh tran cuoi dong danh so ("3. Bà X   Cổ đông",
            # "9. Bà Y   Thư ký") — bien ban hop co dong khong co giay to
            # (BB hop Quang Trung — 13/10/2026).
            role_match = re.search(
                r"(?i)(?:c\u1ed5\s+\u0111\u00f4ng|co\s+dong|th\u01b0\s+k\u00fd|thu\s+ky|ch\u1ee7\s+t\u1ecda|chu\s+toa|th\u00e0nh\s+vi\u00ean|thanh\s+vien|tr\u01b0\u1edfng\s+ph\u00f2ng|k\u1ebf\s+to\u00e1n)\s*$",
                lines[line_idx],
            )
        if (
            not has_birth
            and not id_match
            and not role_match
            and line_idx not in labeled_person_idx
        ):
            continue
        if not _ho_ten_hop_le(person["ho_ten"]):
            continue
        persons.append(person)

    # Dia chi dung chung ca khoi ("Cả hai ông bà cùng thường trú tại: X")
    # — gan cho moi nguoi con thieu, khong chi nguoi dung truoc dong do.
    shared_addrs = [a[2] for a in address_lines if len(a) > 3 and a[3] and a[2]]
    _KEYED_PREFIX = re.compile(
        r"^(?:dia chi|noi thuong tru|noi cu tru|thuong tru|cu tru|ho khau|ong|ba|cua|tai)\s+"
    )

    def _keyed_name(key: str) -> str:
        # Khoa keyed doi khi dinh ca nhan/danh xung ("dia chi thuong tru
        # ong linh") — cat phan dau de con ten goi (mau 18, 13/10/2026).
        prev = None
        while prev != key:
            prev = key
            key = _KEYED_PREFIX.sub("", key)
        return key

    for person in persons:
        # Gia tri dia_chi thuan ngay thang ("[07] Địa chỉ: 23/10/2023" —
        # nguon dich o sai truong) khong phai dia chi — xoa de R03 bao
        # thieu trung thuc (DK18 Mai Thị Luân, 13/10/2026).
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", str(person.get("dia_chi") or "").strip()):
            person["dia_chi"] = ""
        if not person["dia_chi"]:
            keyed = keyed_addrs.get(_fold_text(person["ho_ten"]))
            if not keyed:
                # "Địa chỉ của ông Minh:" / "bà Quỳnh:" / "bà Lan Anh:" —
                # nhan theo ten goi; khoa keyed co the la hau to cua ho
                # ten (am tiet cuoi hoac cum ten goi — 13/10/2026).
                _fold = _fold_text(person["ho_ten"])
                for _k, _v in keyed_addrs.items():
                    _k2 = _keyed_name(_k)
                    if _k2 and (_fold == _k2 or _fold.endswith(" " + _k2)):
                        keyed = _v
                        break
            if keyed:
                person["dia_chi"] = keyed
            elif shared_addrs:
                person["dia_chi"] = shared_addrs[0]

    # Cap vo chong viet "1. Ong X ... 2. Va vo la ba Y ... Nơi thường trú: Z"
    # — chi co 1 dong dia chi cuoi khoi, ap cho ca hai (khong co tu khoa
    # "cả hai/cùng"). Nguoi lien truoc con thieu dia chi nhan dia chi cua
    # nguoi ke duoc mo bang "Và vợ/chồng là".
    for idx, person in enumerate(persons[:-1]):
        if person["dia_chi"]:
            continue
        nxt = persons[idx + 1]
        nxt_head = _fold_text(lines[nxt["_line_idx"]]) if nxt.get("_line_idx") is not None else ""
        if nxt["dia_chi"] and re.search(r"\bva\s+(vo|chong)\s+la\b", nxt_head):
            person["dia_chi"] = nxt["dia_chi"]

    # Bang hanh chinh dang o ("DANH SÁCH NGƯỜI SỬ DỤNG CHUNG" mau 04a/DK,
    # "BIÊN BẢN HỌP HĐTV"): hang "STT | Ông/Bà X | <cac o> | so giay to |
    # ..." — nam sinh co the la o tron khong nhan (1955) hoac vang mat,
    # truong lay theo vi tri o (11/10/2026). Chi tinh hang co o so giay
    # to 6-12 so de tranh nhan nham muc van xuoi danh so.
    table_row_re = re.compile(
        r"(?im)(?:^|\|)\s*\d{1,3}[\s|]*"
        r"(?P<title>\u00f4ng|b\u00e0)\s+(?P<name>[^|\d;]{2,60}?)\s*"
        r"(?P<tail>(?:\|[^|\n]*){0,20}?)"
        r"(?=\|\s*\d{1,3}[\s|]*(?:\u00f4ng|b\u00e0)|\n|$)"
    )
    for tr in table_row_re.finditer(section):
        name = re.sub(r"\s+", " ", tr.group("name")).strip(" ;,.")
        if not _ho_ten_hop_le(name):
            continue
        tail_cells = [
            re.sub(r"\s+", " ", c).strip(" ;,.")
            for c in tr.group("tail").split("|")
            if re.search(r"\w", c)
        ]
        ngay_sinh = cccd = noi_cap = ngay_cap = dia_chi = ""
        expect_noi_cap = False
        has_role_cell = False
        for cell in tail_cells:
            # O ky ket "Nam Định, ngày … năm 2025 | Người kê khai (Ký...)"
            # — cat phan chu ky, chi giu phan truoc.
            cell = re.sub(r"(?i)\s*ng\u01b0\u1eddi\s+k\u00ea\s+khai.*$", "", cell).strip(" ;,.")
            # O ngay-thang-noi-chot "Nam Định, ngày … năm 2025" khong phai
            # truong nguoi.
            if not cell or re.search(r"(?i)ng\u00e0y\b[^\n]{0,30}\bn\u0103m\b", cell):
                continue
            if not ngay_sinh and re.fullmatch(r"(?:19|20)\d{2}", cell):
                ngay_sinh = cell
                continue
            m_id = re.search(r"\b(\d{9,12})\b", cell)
            if m_id:
                if not cccd:
                    cccd = m_id.group(1)
                    cap = re.search(
                        r"(?i)\bdo\s+([^|]{2,80}?)\s+(?:c\u1ea5p ng\u00e0y|cap ngay)\s*(\d{1,2}/\d{1,2}/\d{4})",
                        cell,
                    )
                    if cap:
                        noi_cap = cap.group(1).strip(" ;,.")
                        ngay_cap = cap.group(2)
                continue
            # O nhan loai giay to / nhan cot bo qua — khong phai du lieu.
            if re.fullmatch(
                r"(?i)(?:CCCD|CMND|CC|H\u1ed9 chi\u1ebfu|C\u0103n c\u01b0\u1edbc(?:\s+c\u00f4ng d\u00e2n)?"
                r"|Lo\u1ea1i gi\u1ea5y t\u1edd|S\u1ed1|Ch\u1ee9c v\u1ee5|Ghi ch\u00fa|C\u00f3 m\u1eb7t"
                r"|[\d.,\s%]+)",
                cell,
            ):
                continue
            if expect_noi_cap and not noi_cap:
                noi_cap = cell
                expect_noi_cap = False
                continue
            if not ngay_cap and re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", cell):
                ngay_cap = cell
                # Cot ngay cap: o sau ngay cap la noi cap, sau nua la
                # dia chi (mau 04a/DK "so | ngay cap | noi cap | dia chi").
                expect_noi_cap = True
                continue
            fold = _fold_text(cell)
            # "xa hoi" trong "Cục cảnh sát ... trật tự xã hội" khong phai
            # don vi hanh chinh — bo tu "hoi" dung sau "xa".
            if re.search(r"xa\b(?! hoi)|phuong|huyen|tinh|thi tran|thanh pho|thon|to\b", fold):
                dia_chi = cell
            elif re.search(
                r"thanh vien|chu tich|chu toa|giam doc|thu ky|pho chu|truong phong",
                fold,
            ):
                has_role_cell = True
            elif not noi_cap:
                noi_cap = cell
            elif (
                not dia_chi
                and len(cell.split()) <= 5
                and not re.search(r"[\d;:]", cell)
                and re.match(r"[A-Z\u00c0-\u1ef9\u0110]", cell)
            ):
                # O dia chi ten xa tran ("Liên Minh") dung sau co quan
                # cap — danh sach nguoi su dung chung mau 04a/DK
                # (13/10/2026).
                dia_chi = cell
        if not cccd and not (has_role_cell and len(tail_cells) >= 3):
            continue
        persons.append(
            {
                "gioi_tinh": tr.group("title").capitalize(),
                "ho_ten": name,
                "ngay_sinh": ngay_sinh,
                "chi_co_nam_sinh": bool(ngay_sinh),
                "cccd": cccd,
                "noi_cap": noi_cap,
                "ngay_cap_cccd": ngay_cap,
                "dia_chi": dia_chi,
                "dia_chi_line": "",
                "_line_idx": len(lines),
            }
        )

    for person in persons:
        person["source_start_line_idx"] = person["_line_idx"]
        person.pop("_line_idx", None)
    # Form lap lai nguyen trang (DK18 in 2 mat): cung nguoi xuat hien 2 lan.
    # Dedupe khi trung ho_ten + cccd (uu tien), hoac ho_ten + ngay_sinh.
    # Gop khi trung ten va (a) co it nhat 1 truong phan biet khop
    # khong-rong (cung cccd/ngay sinh), hoac (b) ca 2 deu trong het
    # truong phan biet (nguoi chi co ten, form lap trang). Hai nguoi
    # khac nhau cung ten thuong co du giay to mau thuan -> giu rieng.
    # Fold ten bo dau — "Vũ Thị Lanh"/"Vũ Thị Lành" cung key, nen moi key
    # giu DANH SACH base va gop vao base dau tien khong mau thuan
    # (11/10/2026).
    def _ns_conflict(a: str, b: str) -> bool:
        return _ngay_sinh_conflict(a, b)

    def _can_merge(base: dict, person: dict) -> bool:
        a_vals = {f: str(base.get(f) or "").strip() for f in ("cccd", "ngay_sinh")}
        b_vals = {f: str(person.get(f) or "").strip() for f in ("cccd", "ngay_sinh")}
        conflict = bool(
            a_vals["cccd"] and b_vals["cccd"] and a_vals["cccd"] != b_vals["cccd"]
        ) or _ns_conflict(a_vals["ngay_sinh"], b_vals["ngay_sinh"])
        shared = (a_vals["cccd"] and a_vals["cccd"] == b_vals["cccd"]) or (
            a_vals["ngay_sinh"]
            and not _ns_conflict(a_vals["ngay_sinh"], b_vals["ngay_sinh"])
            and b_vals["ngay_sinh"]
        )
        both_empty = not any((*a_vals.values(), *b_vals.values()))
        complementary = False
        if not shared and not conflict and not both_empty:
            # Dong giay to dat ten nguoi giua nhan ("- Căn cước công dân
            # ông X số ...") la bang chung danh tinh cua "Tên: X" khai
            # cung don (mau 11/DK — 12/10/2026) — gop 2 ban bo sung.
            # Phia trong het truong phan biet van giu rieng (cung nguoi
            # 2 vai tro trong to khai -> R05 trung thuc).
            for id_side, other_vals in ((base, b_vals), (person, a_vals)):
                complementary = complementary or (
                    bool(str(id_side.get("cccd") or "").strip())
                    and re.search(
                        r"(?i)c\u0103n c\u01b0\u1edbc|cccd|cmnd",
                        str(id_side.get("raw_text") or ""),
                    )
                    is not None
                    and bool(other_vals["ngay_sinh"] or other_vals["cccd"])
                )
        return not conflict and (shared or both_empty or complementary)

    seen_person: dict[str, list[dict]] = {}
    deduped: list[dict] = []
    for person in persons:
        name_key = _fold_text(person.get("ho_ten") or "")
        bases = (seen_person.get(name_key) or []) if name_key else []
        base = next((b for b in bases if _can_merge(b, person)), None)
        if base is not None:
            for field in ("ngay_sinh", "cccd", "noi_cap", "ngay_cap_cccd", "dia_chi", "gioi_tinh"):
                if not str(base.get(field) or "").strip() and str(person.get(field) or "").strip():
                    base[field] = person[field]
            # Nguon go thuong 1 am tiet ("Khiếu Minh hải" vs "Khiếu Minh
            # Hải" o muc sau) — giu ban viet hoa dung (13/10/2026).
            _b_name = str(base.get("ho_ten") or "")
            _n_name = str(person.get("ho_ten") or "")
            if _n_name and _b_name != _n_name:
                _sc = lambda nm: sum(1 for w in nm.split() if w[:1].isupper())
                if _sc(_n_name) > _sc(_b_name):
                    base["ho_ten"] = _n_name
            # Nang "ngay_sinh" chi-co-nam len ngay day du cung nam — ban
            # "Sinh ngay: 25/12/1958" day du hon "Sinh nam 1958" (11/10/2026).
            base_ns = str(base.get("ngay_sinh") or "").strip()
            new_ns = str(person.get("ngay_sinh") or "").strip()
            if (
                base_ns
                and "/" not in base_ns
                and "/" in new_ns
                and new_ns.endswith(base_ns)
            ):
                base["ngay_sinh"] = new_ns
                base["chi_co_nam_sinh"] = False
            continue
        if name_key:
            seen_person.setdefault(name_key, []).append(person)
        deduped.append(person)
    return deduped


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
        r"(?:\d+\s*\.\s*)?(?:v\u00e0\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\s+)?"
        r"(?:ng\u01b0\u1eddi\s+(?:v\u1ee3|ch\u1ed3ng)\s+)?(?:\u00f4ng|b\u00e0)\s*:?"
    )
    header_line_re = re.compile(
        r"(?i)^\s*(?:[-*]\s*)?(?:\u0110\u1ea1i di\u1ec7n:\s*)?(?:(?:ng\u01b0\u1eddi\s+)?(?:v\u1ee3|ch\u1ed3ng)\s*[\-\u2013:]\s*)?"
        r"(?:\d+\s*\.\s*)?(?:v\u00e0\s+(?:v\u1ee3|ch\u1ed3ng)\s+l\u00e0\s+)?"
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


def _extract_nguoi_chet(text: str, doc_kind: str = "") -> list[dict]:
    """Trich NGUOI DA CHET (nguoi de lai di san) theo shape person_row
    (decision-46 06/10/2026): trich luc khai tu la giay to cua nguoi chet,
    dien vao so_giay_to/ngay_cap/noi_cap/loai_giay_to; dia chi cuoi -> dia_chi.
    Dau hieu bat buoc: "chet ngay DD/MM/YYYY", hoac "chet nam YYYY"
    chi khi ngay sau co "trich luc/khai tu" (bang chung nguoi de lai
    di san; tranh vo nhan bo/me de chi ghi "chet nam...").
    Rieng van ban TU CHOI nhan di san: "chet nam YYYY" duoc nhan them
    khi phia truoc co tu quan he (bo/me de, vo/chong...) — cha/me cua
    nguoi tu choi mac dinh la nguoi de lai di san (11/10/2026).
    """
    source = unicodedata.normalize("NFC", str(text or ""))
    found: list[dict] = []
    seen: dict[str, dict] = {}
    is_refusal = doc_kind == DOC_KIND_INHERITANCE_REFUSAL
    death_y_evidence = (
        r""
        if is_refusal
        else r"(?=\s*(?:theo\s+)?tr\u00edch\s+l\u1ee5c|[^.\n]{0,60}?(?:khai\s+t\u1eed|\u0111\u01a1n\s+(?:xin\s+x\u00e1c\s+nh\u1eadn|\u0111\u1ec1\s+ngh\u1ecb)|gi\u1ea5y\s+x\u00e1c\s+nh\u1eadn))"
    )
    death_re = re.compile(
        r"(?i)(?P<title>\u00d4ng|B\u00e0|Anh|Ch\u1ecb|l\u00e0)\s*:?\s*(?P<name>[^;(\n.,]+?)"
        r"(?:\s+v\u00e0\s+(?P<title2>\u00f4ng|b\u00e0|anh|ch\u1ecb)\s*:?\s*(?P<name2>[^;(\n.,]+?))?"
        r"\s*(?:\((?P<alias>[^)]+)\))?"
        r"\s*[-\u2013;,]?\s*"
        r"(?:(?:Sinh n\u0103m|N\u0103m sinh|Sinh nam|Nam sinh|Sinh ng\s*\u00e0y|Ng\u00e0y\s+sinh|Sinh ngay|Ngay sinh)"
        r"\s*[:\u2013-]?\s*(?P<birth>(?:19|20)\d{2}|\d{1,2}/\d{1,2}/\d{4}))?"
        r"\s*[;,]?\s*(?:\u0111\u00e3\s+)?(?:ch\u1ebft|m\u1ea5t)\s+(?:ng\u00e0y\s*(?:ng\u00e0y\s*)?[:\u2013-]?\s*(?P<death>\d{1,2}/\d{1,2}/\d{4})"
        r"|n\u0103m\s*[:\u2013-]?\s*(?P<death_y>(?:19|20)\d{2})"
        + death_y_evidence + r")"
    )
    # Dang ngoac gop: "ong X (sinh nam 1956, da chet ngay 16/01/2025)" —
    # cum sinh+chet nam trong ngoac bi nhom alias nuot o death_re (11/10/2026).
    death_paren_re = re.compile(
        r"(?i)(?P<title>Ông|Bà|Anh|Chị|là)\s*:?\s*(?P<name>[^;(\n.,]+?)"
        # Ngoac bi danh co the dung TRUOC ngoac sinh/chet:
        # "ong X (Tran Huu Dam); (Sinh nam 1945, da chet ngay ...)".
        r"(?:\s*\((?P<alias>[^)]+)\)\s*[-–;,]?)?"
        # Ngoac co the lap lai danh xung + ten rut gon truoc ngay sinh:
        # "ong Luong Van Nguyen (ong Nguyen Sinh nam 1952; chet ngay ...)".
        # Dau cau kep giua ten va ngoac ("Sơn; (Sinh năm...)") van nhan
        # (VB tu choi ba Vong — 13/10/2026).
        r"\s*[-–;,]?\s*\(\s*(?:(?:ông|bà)\s+[^;()\n]{2,40}?\s+)?(?:Sinh\s+năm|Năm\s+sinh|Sinh\s+ngày|Ngày\s+sinh)"
        r"\s*[:–-]?\s*(?P<birth>(?:19|20)\d{2}|\d{1,2}/\d{1,2}/\d{4})"
        r"\s*[,;]?\s*(?:đã\s+)?(?:chết|mất)\s+"
        r"(?:ngày\s*(?:ngày\s*)?[:–-]?\s*(?P<death>\d{1,2}/\d{1,2}/\d{4})"
        r"|năm\s*[:–-]?\s*(?P<death_y>(?:19|20)\d{2})"
        + death_y_evidence + r")[^)]*\)"
    )
    matches = sorted(
        list(death_re.finditer(source)) + list(death_paren_re.finditer(source)),
        key=lambda m: m.start(),
    )
    _accepted_end = -1
    for match_idx, match in enumerate(matches):
        # Match nam gon trong mot match da nhan (vd "ong Nguyen" ben trong
        # ngoac cua "ong Luong Van Nguyen (ong Nguyen Sinh nam...)") — bo.
        if match.start() < _accepted_end:
            continue
        raw_name = re.sub(r"\s+", " ", match.groupdict().get("name") or "").strip(" ;,.-")
        raw_name = re.sub(r"(?i)^\d+\.\s*", "", raw_name)
        raw_name = re.sub(r"(?i)^(?:l\u00e0|bao g\u1ed3m)\s+", "", raw_name)
        # Danh xung dinh trong nhom ten ("1.1 Ông Nguyễn Văn Toản - Sinh
        # năm ...") — tach ra, dung lam gioi tinh neu title trong.
        _lead_salut = re.match(r"(?i)^(ông|bà|anh|chị)\s+(.{2,})$", raw_name)
        _salut_title = None
        if _lead_salut:
            _salut_title = _lead_salut.group(1)
            raw_name = _lead_salut.group(2)
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
            match_title = match.groupdict().get("title") or _salut_title
        # "là ông X" — title regex bat "là", danh xung that nam trong ten
        # da tach (_salut_title) — dung danh xung de suy gioi tinh.
        if _fold_text(str(match_title or "")) in ("la", "lam") and _salut_title:
            match_title = _salut_title
        if len(raw_name.split()) == 1:
            # Ten rut gon 1 am tiet ("Bà Yểng Sinh năm 1931; chết...") —
            # tim ten day du ket thuc bang am tiet do ngay truoc trong
            # nguyen doan ("là bà Nguyễn Thị Yểng. Bà Yểng Sinh năm...").
            _tok = raw_name
            _before = source[max(0, match.start() - 250):match.start()]
            _full = re.findall(
                r"(?:\u00f4ng|b\u00e0)\s+([A-Z\u00c0-\u1ef9\u0110](?:(?!\b(?:\u00f4ng|b\u00e0|l\u00e0)\b)[^\d;:.,()\n]){1,58}?"
                + re.escape(_tok)
                + r")\b",
                _before,
                re.I,
            )
            _full = [
                re.sub(r"\s+", " ", c).strip(" ;,.-") for c in _full
            ]
            _full = [
                c for c in _full
                if 1 < len(c.split()) <= 6
                and all(t[0].isupper() for t in c.split())
            ]
            if _full:
                raw_name = max(_full, key=len)
        title_fold = _fold_text(match_title)
        death_val = match.groupdict().get("death") or match.groupdict().get("death_y") or ""
        # Tu choi: "chet nam" khong trich luc chi nhan khi truoc ten co
        # tu quan he (bo/me/vo/chong...) — tranh nhan ten ghep thoang.
        if is_refusal and match.groupdict().get("death_y") and not match.groupdict().get("death"):
            tail_after = source[match.end():match.end() + 80]
            if not re.search(r"(?i)tr\u00edch\s+l\u1ee5c|khai\s+t\u1eed|\u0111\u01a1n\s+xin\s+x\u00e1c\s+nh\u1eadn", tail_after):
                head_before = source[max(0, match.start() - 100):match.start()]
                if not re.search(
                    r"(?i)b\u1ed1|m\u1eb9|cha|ba|v\u1ee3|ch\u1ed3ng|anh|ch\u1ecb|em\b|con\b|ch\u00e1u",
                    head_before,
                ):
                    continue
        # Nguoi thu 2 cung dong ("... và bà B; chết ngày ...") — tach thanh
        # ban ghi rieng, dung chung truong ngay/giay to cua cap.
        name2 = re.sub(r"\s+", " ", match.groupdict().get("name2") or "").strip(" ;,.-")
        if name2:
            t2 = name2.split()
            key2 = f"{_fold_text(name2)}|{death_val}"
            if t2 and len(t2) <= 6 and all(tok[0].isupper() for tok in t2) and key2 not in seen:
                seen[key2] = {
                    "gioi_tinh": "\u00d4ng" if _fold_text(match.groupdict().get("title2") or "") in ("ong", "anh") else "B\u00e0",
                    "ho_ten": name2,
                    "ten_goi_khac": "",
                    "ngay_sinh": "",
                    "chi_co_nam_sinh": False,
                    "ngay_chet": death_val,
                    "so_giay_to": "",
                    "ngay_cap": "",
                    "noi_cap": "",
                    "loai_giay_to": "",
                    "dia_chi": "",
                }
                found.append(seen[key2])
        alias = re.sub(r"\s+", " ", match.groupdict().get("alias") or "").strip()
        alias = re.sub(r"(?i)^t\u00ean g\u1ecdi kh\u00e1c l\u00e0\s+", "", alias)
        tail_end = min(match.end() + 400, len(source))
        if match_idx + 1 < len(matches):
            _next_starts = [m.start() for m in matches[match_idx + 1:] if m.start() > match.end()]
            if _next_starts:
                tail_end = min(tail_end, _next_starts[0])
        # Quet tu dau match: TLKT co the nam TRONG ngoac
        # "(ong Nguyen Sinh nam 1952; chet ngay ... theo Trich luc ...)".
        tail = source[match.start():tail_end]
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
            r"(?i)(?P<ca_hai>c\u1ea3 hai\s+c\u00f3\s+)?N\u01a1i\s+(?:th\u01b0\u1eddng tr\u00fa|c\u01b0 tr\u00fa|t\u1ea1m tr\u00fa)(?:\s*/\s*t\u1ea1m tr\u00fa)?\s+(?:(?:cu\u1ed1i c\u00f9ng\s+)?tr\u01b0\u1edbc khi ch\u1ebft|cu\u1ed1i c\u00f9ng)\s*(?:t\u1ea1i)?\s*:\s*(?P<addr>[^.\n;)]+)",
            tail,
        )
        if addr_match:
            last_addr = re.sub(r"\s+", " ", addr_match.group("addr")).strip(" ;,.")
            # "Cả hai có nơi cư trú cuối cùng..." — dia chi chung cua cap
            # vo chong chet cung dong; dien nguoc cho nguoi ngay truoc
            # con trong (ong Moc/ba Den — tho a thuan phan chia 12/10/2026).
            if addr_match.group("ca_hai") and found and not found[-1]["dia_chi"]:
                found[-1]["dia_chi"] = last_addr
        key = f"{_fold_text(raw_name)}|{death_val}"
        if not raw_name:
            continue
        _birth = match.groupdict().get("birth") or ""
        ngay_sinh, chi_co_nam = _chuan_hoa_ngay_sinh(
            _birth if "/" in _birth else "", _birth if "/" not in _birth else ""
        )
        record = {
            "gioi_tinh": "\u00d4ng" if title_fold in ("ong", "anh") else ("B\u00e0" if title_fold in ("ba", "chi") else ""),
            "ho_ten": raw_name,
            "ten_goi_khac": alias,
            "ngay_sinh": ngay_sinh,
            "chi_co_nam_sinh": chi_co_nam,
            "ngay_chet": death_val,
            "so_giay_to": tlkt_no,
            "ngay_cap": tlkt_date,
            "noi_cap": tlkt_by,
            "loai_giay_to": "Trích lục khai tử" if tlkt_no else "",
            "dia_chi": last_addr,
        }
        if key in seen:
            # Lan nhac sau cung nguoi — dien truong trong (dia chi, TLKT)
            # thay vi bo; ban sau thuong giau hon (12/10/2026 — ba Hien
            # nhac 2 lan, lan sau co "Noi thuong tru cuoi cung").
            base = seen[key]
            for field, value in record.items():
                if not str(base.get(field) or "").strip() and str(value or "").strip():
                    base[field] = value
            _accepted_end = match.end()
            continue
        seen[key] = record
        found.append(record)
        _accepted_end = match.end()
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
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?B\u00caN CHUY\u1ec2N NH\u01af\u1ee2NG\b",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?B\u00caN TH\u1ebe CH\u1ea4P\b",
        r"(?im)^\s*\(?A\)?\s*B\u00caN TH\u1ebe CH\u1ea4P\b",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?BEN THE CHAP\b",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?B\u00caN CHO VAY\b",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?B\u00caN CHO THU\u00ca\b",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?B\u00caN (?:UY|U\u1ef6|\u1ee6Y) QUY\u1ec0N\b",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?NG\u01af\u1edcI (?:UY|U\u1ef6|\u1ee6Y) QUY\u1ec0N\b(?=\s*[:(])(?![^\n]*\bNG\u01af\u1edcI\b)",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?B\u00caN \u0110\u1eb6T C\u1eccC\b",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?NG\u01af\u1edcI DI CH\u00daC\b(?=\s*[:(])(?![^\n]*\bNG\u01af\u1edcI\b)",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?NG\u01af\u1edcI CAM K\u1ebeT\b(?=\s*[:(])(?![^\n]*\bNG\u01af\u1edcI\b)",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?B\u00caN G\u00d3P V\u1ed0N\b",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?B\u00caN T\u1eb6NG CHO\b",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?B\u00caN B\u00c1N\b",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?B\u00caN TH\u1ee8 NH\u1ea4T\b",
        r"(?im)^\s*(?:I[./]\s*(?:\|\s*)?)?B\u00caN A\b",
    )
    ben_b_patterns = (
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?B\u00caN NH\u1eacN CHUY\u1ec2N NH\u01af\u1ee2NG\b",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?B\u00caN NH\u1eacN TH\u1ebe CH\u1ea4P\b",
        r"(?im)^\s*\(?B\)?\s*B\u00caN NH\u1eacN TH\u1ebe CH\u1ea4P\b",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?BEN NHAN THE CHAP\b",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?B\u00caN VAY\b",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?B\u00caN THU\u00ca\b",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?B\u00caN \u0110\u01af\u1ee2C (?:UY|U\u1ef6|\u1ee6Y) QUY\u1ec0N\b",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?NG\u01af\u1edcI \u0110\u01af\u1ee2C (?:UY|U\u1ef6|\u1ee6Y) QUY\u1ec0N\b(?=\s*[:(])(?![^\n]*\bNG\u01af\u1edcI\b)",
        r"(?i)uỷ\s+quyền\s+cho\s*:",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?B\u00caN NH\u1eacN \u0110\u1eb6T C\u1eccC\b",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?B\u00caN NH\u1eacN T\u1eb6NG CHO\b",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?B\u00caN \u0110\u01af\u1ee2C T\u1eb6NG CHO\b",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?B\u00caN MUA\b",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?B\u00caN TH\u1ee8 HAI\b",
        r"(?im)^\s*(?:II[./]\s*(?:\|\s*)?)?B\u00caN B\b",
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
        # Chu ky/chung thuc sau than van: danh sach nguoi ky lai duoi
        # "CHUNG THUC"/"NGUOI UY QUYEN" khong phai duong su ben B
        # (mau giay uy quyen UBND xa — 12/10/2026).
        r"(?im)^\s*CH\u1ee8NG TH\u1ef0C\b",
        r"(?im)^\s*NG\u01af\u1edcI (?:U\u1ef6|\u1ee6Y|UY) QUY\u1ec0N\b",
        r"(?im)^\s*NG\u01af\u1edcI \u0110\u01af\u1ee2C (?:U\u1ef6|\u1ee6Y|UY) QUY\u1ec0N\b",
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
        # The chap khong heading "BÊN NHẬN THẾ CHẤP": ngan hang + dai dien
        # thuong nam trong phan mo dau truoc "BÊN THẾ CHẤP" (mau Agribank
        # trong Loi chung) — preamble chinh la ben nhan the chap.
        ben_b_section = (
            text[:idx_a_start]
            if doc_kind == DOC_KIND_MORTGAGE and idx_a_start > 0
            else ""
        )

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
    if _find_tai_san_vehicle(text):
        found.append("xe")
    return found


def _build_payload_generic(filepath, text: str, scan_result: dict, *, extract_mode: str) -> dict:
    doc_kind, ten_hd = _detect_document_kind_and_title(text)
    ben_a, ben_b = _extract_parties_generic(text, doc_kind)
    nguoi_chet = _extract_nguoi_chet(text, doc_kind)
    # Nguoi da chet (ten + nam sinh khop voi nguoi_chet) van bi danh sach
    # thanh vien ho gia dinh ho vao duong su — loai khoi ben (13/10/2026,
    # van ban cam ket: "1. Ông X - sinh nam 1957 (chu ho)" trong khi phan
    # sau ghi "chet ngay ... theo trich luc").
    for ben in (ben_a, ben_b):
        if not ben.get("nguoi"):
            continue
        giu = []
        for person in ben["nguoi"]:
            key = _fold_text(person.get("ho_ten") or "")
            cung_nguoi_chet = any(
                _fold_text(c.get("ho_ten") or "") == key
                and not _ngay_sinh_conflict(
                    str(person.get("ngay_sinh") or "").strip(),
                    str(c.get("ngay_sinh") or "").strip(),
                )
                and bool(str(person.get("ngay_sinh") or "").strip())
                for c in nguoi_chet
            )
            if not cung_nguoi_chet:
                giu.append(person)
        ben["nguoi"] = giu
    # Van ban in lap 2 mat: ban sao sau section da cat van co the chua
    # ngay cap CCCD (VD "cấp ngày .................." o ban 1 nhung
    # "cấp ngày 25/04/2021" o ban 2) — dien tu doan chua so CCCD
    # (HĐCN Duyên Liên — 13/10/2026).
    for ben in (ben_a, ben_b):
        for person in ben.get("nguoi") or []:
            name = str(person.get("ho_ten") or "").strip()
            # Dien cccd tu ban in lai: tim ten nguoi roi lay "Căn cước
            # ... số" truoc khoi nguoi ke (Hoàn — hộ chiếu o ban 1,
            # CCCD o ban 2 — 13/10/2026).
            if name and not str(person.get("cccd") or "").strip():
                for m in re.finditer(re.escape(name), text, re.IGNORECASE):
                    window = text[m.end():m.end() + 300]
                    end = re.search(
                        r"(?im)^\s*(?:[\u00d4O]ng|[Bb]\u00e0|[Aa]nh|[Cc]h\u1ecb|[Cc]\u00f4)|\b(?:v\u00e0|c\u00f9ng)\s+(?:v\u1ee3|ch\u1ed3ng)\b",
                        window,
                    )
                    seg = window[: end.start() if end else 300]
                    cap = re.search(
                        r"(?i)c\u0103n c\u01b0\u1edbc(?:\s+c\u00f4ng\s*d\u00e2n)?\s*(?:s\u1ed1)?\s*:?\s*(\d{6,12})",
                        seg,
                    )
                    if cap:
                        person["cccd"] = cap.group(1)
                        break
            cccd = str(person.get("cccd") or "").strip()
            if not cccd or str(person.get("ngay_cap_cccd") or "").strip():
                continue
            for m in re.finditer(re.escape(cccd), text):
                window = text[m.end():m.end() + 250]
                end = re.search(
                    r"(?i)c\u0103n c\u01b0\u1edbc|cccd|cmnd|sinh ng\u00e0y",
                    window,
                )
                cap = re.search(
                    r"(?i)c\u1ea5p\s+ng\u00e0y\s*(\d{1,2}/\d{1,2}/\d{4})",
                    window[: end.start() if end else 250],
                )
                if cap:
                    person["ngay_cap_cccd"] = cap.group(1)
                    break
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
            "nguoi_chet": nguoi_chet,
            # Mau template: gia tri «merge_field» khong phai du lieu —
            # bo thua chi chua placeholder (cam ket DH 090202 — 13/10/2026).
            "danh_sach_thua_dat": [
                p for p in tach_danh_sach_thua_dat(tai_san)
                if not all(
                    not str(p.get(f) or "").strip()
                    or "«" in str(p.get(f) or "")
                    or str(p.get(f) or "").strip().startswith("[")
                    for f in ("so_thua_dat", "so_to_ban_do", "dia_chi")
                )
            ],
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

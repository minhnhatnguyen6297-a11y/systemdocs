"""Field normalization for intake suggestions (notary.case-drafting.v1).

Rules (contract §2.2, §4):
- raw_value giữ nguyên giá trị quan sát được; normalized_value là dạng chuẩn.
- observation_state ∈ {observed, normalized, inferred}; không có `confirmed`.
- confidence chỉ có nghĩa khi state == "inferred", còn lại phải là null.
- Chuỗi rỗng không bao giờ được emit như null — field rỗng bị bỏ qua, còn
  normalized_value không chuẩn hóa được thì là null.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from datetime import datetime
from typing import Any, Optional

from .models import make_suggestion

# ---------------------------------------------------------------------------
# Primitive normalizers → (normalized_value, observation_state, confidence)
# ---------------------------------------------------------------------------


def clean_ws(value: Any) -> str:
    """Collapse whitespace; strip."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    without_marks = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return without_marks.replace("đ", "d").replace("Đ", "D").lower()


def _norm_result(raw: str, normalized: Optional[str], confidence: Optional[float] = None):
    """Decide observed vs normalized by comparing raw to normalized."""
    if normalized is None or normalized == "":
        return None, "observed", None
    if normalized == raw:
        return normalized, "observed", None
    if confidence is not None:
        return normalized, "inferred", confidence
    return normalized, "normalized", None


def norm_text(raw: str):
    """Generic text field: collapse whitespace only."""
    cleaned = clean_ws(raw)
    return (cleaned or None), "observed" if cleaned == raw else "normalized", None


def norm_name(raw: str):
    """Tên người: ALL-CAPS → Title Case (normalized); giữ nguyên nếu đã hỗn hợp."""
    cleaned = clean_ws(raw)
    if not cleaned:
        return None, "observed", None
    letters = [ch for ch in cleaned if ch.isalpha()]
    if letters and all(ch.isupper() for ch in letters):
        return cleaned.title(), "normalized", None
    return cleaned, "observed" if cleaned == raw else "normalized", None


_DATE_PATTERNS = (
    re.compile(r"^(\d{4})-(\d{2})-(\d{2})$"),           # YYYY-MM-DD
    re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$"),  # dd/mm/YYYY | dd-mm-YYYY
    re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$"),      # dd.mm.YYYY
    re.compile(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$"),  # YYYY/m/d
    re.compile(r"^(\d{4})$"),                            # YYYY
)


def norm_date(raw: str, *, allow_year: bool = True):
    """Ngày → "YYYY-MM-DD" hoặc "YYYY" — canonical field: normalized khi ra."""
    cleaned = clean_ws(raw)
    if not cleaned:
        return None, "observed", None

    m = _DATE_PATTERNS[0].match(cleaned)
    if m:
        return cleaned, "normalized", None
    for pat in _DATE_PATTERNS[1:4]:
        m = pat.match(cleaned)
        if m:
            a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if pat is _DATE_PATTERNS[3]:  # YYYY/m/d
                y, mo, d = a, b, c
            else:
                d, mo, y = a, b, c
            try:
                datetime(y, mo, d)
            except ValueError:
                return None, "observed", None
            return f"{y:04d}-{mo:02d}-{d:02d}", "normalized", None
    m = _DATE_PATTERNS[4].match(cleaned)
    if m and allow_year:
        y = int(m.group(1))
        if 1900 <= y <= 2099:
            return m.group(1), "normalized", None
    return None, "observed", None


def norm_gender(raw: str):
    """Giới tính → "Nam" | "Nữ" | null (compare-rule như contract examples)."""
    cleaned = clean_ws(raw)
    if not cleaned:
        return None, "observed", None
    folded = _fold(cleaned)
    if folded in ("nam", "male", "m"):
        return "Nam", "observed" if cleaned == "Nam" else "normalized", None
    if folded in ("nu", "female", "f"):
        return "Nữ", "observed" if cleaned == "Nữ" else "normalized", None
    return None, "observed", None


def norm_doc_no(raw: str):
    """Số giấy tờ/CCCD: bỏ ký tự không phải chữ-số — canonical → normalized."""
    cleaned = clean_ws(raw)
    if not cleaned:
        return None, "observed", None
    compact = re.sub(r"[^0-9A-Za-z]", "", cleaned)
    if not compact:
        return None, "observed", None
    return compact, "normalized", None


_SERIAL_PATTERN = re.compile(r"^[A-Z]{2}\d{6,8}$")


def norm_serial(raw: str):
    """Serial sổ đỏ: 2 chữ + 6-8 số. Suy ra dạng chuẩn → inferred + confidence."""
    cleaned = clean_ws(raw)
    if not cleaned:
        return None, "observed", None
    upper = cleaned.upper()
    if _SERIAL_PATTERN.match(upper):
        return upper, "normalized", None
    compact = re.sub(r"[^A-Z0-9]", "", upper)
    if _SERIAL_PATTERN.match(compact):
        return compact, "inferred", 0.62
    return None, "observed", None


def norm_number(raw: str):
    """Diện tích / số: '447,0' → 447.0 ; '1.234,5' → 1234.5 — canonical."""
    cleaned = clean_ws(raw)
    if not cleaned:
        return None, "observed", None
    candidate = cleaned
    if "," in candidate and "." in candidate:
        candidate = candidate.replace(".", "").replace(",", ".")
    elif "," in candidate:
        candidate = candidate.replace(",", ".")
    if re.fullmatch(r"\d+(\.\d+)?", candidate):
        num = float(candidate)
        normalized: Any = int(num) if num.is_integer() else num
        return normalized, "normalized", None
    return None, "observed", None


def norm_code(raw: str):
    """Mã nội bộ (so_vao_so, so_thua_dat...): canonical → normalized."""
    cleaned = clean_ws(raw)
    return (cleaned or None), ("normalized" if cleaned else "observed"), None


# ---------------------------------------------------------------------------
# Field-value builders (contract field_value shape)
# ---------------------------------------------------------------------------


def field_value(raw, normalized, state, confidence, refs) -> dict:
    """Build one contract field_value. Invariants: no `confirmed`, no "" as null,
    confidence null unless inferred, source_refs non-empty."""
    if state not in ("observed", "normalized", "inferred"):
        raise ValueError(f"invalid observation_state: {state}")
    if state != "inferred":
        confidence = None
    if normalized == "":
        normalized = None
    refs = list(refs or [])
    if not refs:
        raise ValueError("field_value requires non-empty source_refs")
    return {
        "raw_value": raw,
        "normalized_value": normalized,
        "observation_state": state,
        "confidence": confidence,
        "source_refs": refs,
    }


def _emit(fields: dict, name: str, raw: Any, normalizer, refs, **kw):
    """Normalize + append one field; skip when raw rỗng (không emit "" as null)."""
    raw_clean = clean_ws(raw)
    if not raw_clean:
        return
    normalized, state, confidence = normalizer(raw_clean, **kw) if kw else normalizer(raw_clean)
    fields[name] = field_value(raw_clean, normalized, state, confidence, refs)


# ---------------------------------------------------------------------------
# Doc → suggestion mapping
# ---------------------------------------------------------------------------

_PERSON_FIELD_NORMALIZERS = {
    "ho_ten": norm_name,
    "so_giay_to": norm_doc_no,
    "ngay_sinh": norm_date,
    "gioi_tinh": norm_gender,
    "dia_chi": norm_text,
    "ngay_cap": norm_date,
    "ngay_het_han": norm_date,
    "ngay_chet": norm_date,
}

_PROPERTY_FIELD_NORMALIZERS = {
    "loai_so": norm_text,
    "so_serial": norm_serial,
    "so_vao_so": norm_code,
    "so_thua_dat": norm_code,
    "so_to_ban_do": norm_code,
    "dien_tich": norm_number,
    "dia_chi": norm_text,
    "chu_su_dung": norm_name,
    "ngay_cap": norm_date,
    "co_quan_cap": norm_text,
    "loai_dat": norm_text,
    "thoi_han": norm_text,
    "hinh_thuc_su_dung": norm_text,
    "nguon_goc": norm_text,
}

_EXCEL_FIELD_NORMALIZERS = {
    "ho_ten": norm_name,
    "gioi_tinh": norm_gender,
    "ngay_sinh": norm_date,
    "ngay_chet": norm_date,
    "so_giay_to": norm_doc_no,
    "ngay_cap": norm_date,
    "dia_chi": norm_text,
}

_DOC_WARNING_CODES = {
    "missing_front": ("intake.missing_front", "Thiếu ảnh mặt trước CCCD"),
    "missing_back": ("intake.missing_back", "Thiếu ảnh mặt sau CCCD"),
    "missing_name": ("intake.missing_name", "Không đọc được họ tên"),
    "missing_death_date": ("intake.missing_death_date", "Không đọc được ngày chết"),
}


def map_warning_tokens(tokens) -> list[dict]:
    """Map pipeline warning tokens → contract warning dicts."""
    warnings: list[dict] = []
    seen: set[str] = set()
    for w in tokens or []:
        token = str(w)
        code, message = _DOC_WARNING_CODES.get(
            token,
            ("intake.missing_field", f"Thiếu trường: {token}"),
        )
        key = f"{code}:{token}"
        if key in seen:
            continue
        seen.add(key)
        warnings.append({"code": code, "message": message})
    return warnings


def map_doc_warnings(doc: dict) -> list[dict]:
    tokens = doc.get("warnings") if isinstance(doc.get("warnings"), list) else []
    return map_warning_tokens(tokens)


def _low_confidence_warnings(fields: dict) -> list[dict]:
    """Warning `intake.low_confidence` cho field inferred dưới ngưỡng 0.7
    (khớp valid example job.intake-analyze-partial)."""
    warnings: list[dict] = []
    for name, fv in fields.items():
        if (
            fv.get("observation_state") == "inferred"
            and isinstance(fv.get("confidence"), (int, float))
            and fv["confidence"] < 0.7
        ):
            warnings.append({
                "code": "intake.low_confidence",
                "message": f"Độ tin cậy {name} dưới ngưỡng đề xuất",
            })
    return warnings


def person_data_to_suggestion(data: dict, warning_tokens, source_id: str, refs: list) -> Optional[dict]:
    """Map một person dict đã merge (hoặc QR parse) → contract suggestion."""
    fields: dict[str, dict] = {}
    for name, normalizer in _PERSON_FIELD_NORMALIZERS.items():
        _emit(fields, name, data.get(name), normalizer, refs)
    if not fields:
        return None
    return make_suggestion(
        source_id=source_id,
        target="person",
        fields=fields,
        warnings=map_warning_tokens(warning_tokens) + _low_confidence_warnings(fields),
    )


def doc_to_suggestion(doc: dict, source_id: str, source_ref: dict) -> Optional[dict]:
    """Map một parsed pipeline doc → contract suggestion (person|asset).

    Trả None khi doc không phải person/property hoặc không có field nào —
    caller quyết định có phải intake.parse_failed hay không.
    """
    doc_type = doc.get("doc_type")
    data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
    refs = [source_ref]
    fields: dict[str, dict] = {}

    if doc_type == "person":
        for name, normalizer in _PERSON_FIELD_NORMALIZERS.items():
            _emit(fields, name, data.get(name), normalizer, refs)
        target = "person"
    elif doc_type == "property":
        for name, normalizer in _PROPERTY_FIELD_NORMALIZERS.items():
            if name == "ngay_cap":
                # asset_row.ngay_cap chỉ nhận YYYY-MM-DD đầy đủ
                _emit(fields, name, data.get(name), norm_date, refs, allow_year=False)
            else:
                _emit(fields, name, data.get(name), normalizer, refs)
        target = "asset"
    else:
        return None

    if not fields:
        return None
    return make_suggestion(
        source_id=source_id,
        target=target,
        fields=fields,
        warnings=map_doc_warnings(doc) + _low_confidence_warnings(fields),
    )


def person_row_to_suggestion(form: dict, cells: dict, source_id: str, sheet: str, row_num: int) -> Optional[dict]:
    """Map một Excel person row → contract suggestion với sheet/cell refs."""
    fields: dict[str, dict] = {}
    for name, normalizer in _EXCEL_FIELD_NORMALIZERS.items():
        cell = cells.get(name)
        refs = [{"sheet": sheet, "cell": cell, "row": row_num}] if cell else [{"sheet": sheet, "row": row_num}]
        _emit(fields, name, form.get(name), normalizer, refs)
    if not fields:
        return None
    warnings: list[dict] = _low_confidence_warnings(fields)
    if not clean_ws(form.get("so_giay_to")):
        warnings.append({"code": "intake.missing_field", "message": "Thiếu trường: so_giay_to"})
    return make_suggestion(source_id=source_id, target="person", fields=fields, warnings=warnings)


def make_source_ref(*, filename: Optional[str] = None, page: Optional[int] = None,
                    sheet: Optional[str] = None, row: Optional[int] = None,
                    cell: Optional[str] = None, span: Optional[list] = None) -> dict:
    ref: dict[str, Any] = {}
    if filename is not None:
        ref["file"] = filename
    if page is not None:
        ref["page"] = page
    if sheet is not None:
        ref["sheet"] = sheet
    if row is not None:
        ref["row"] = row
    if cell is not None:
        ref["cell"] = cell
    if span is not None:
        ref["span"] = span
    return ref

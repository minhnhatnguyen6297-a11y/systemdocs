"""Ordered DOCX → lõi luật chung → review candidates with exact field evidence.

Đường luật duy nhất: `tools/regex_workbench/engine/contract_extract.py`
(`extract_text` + các hàm nhóm/thửa). Adapter này chỉ giữ phần biên của
Document Intake:

- đọc DOCX theo thứ tự XML (`..docx_source`) và giữ span gốc;
- ánh xạ payload lõi -> `suggestion`/`field_value` của contract intake
  (normalizer + shape ở `..normalization`);
- dựng `source_refs` (span + `raw_snippet` + `rule_id` + identity lõi) bằng
  cách định vị giá trị đã bóc trong text nguồn — không tự bóc lại giá trị.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
import uuid
from pathlib import Path

# Shared source ships beside the engine; avoid colliding with notary_v2.tools.
_SHARED_TOOLS = str(Path(__file__).resolve().parents[4] / "tools")
if _SHARED_TOOLS not in sys.path:
    sys.path.insert(0, _SHARED_TOOLS)

from regex_workbench.engine.contract_extract import (  # noqa: E402
    ENGINE_ID,
    ENGINE_VERSION,
    SourceSpanIndex,
    build_span_index,
    dien_tich_thanh_so,
    document_asset_context,
    extract_text,
    tach_nhom_tai_san,
    thua_dat_sang_land_rows,
)
from ..docx_source import read_docx  # noqa: E402
from ..models import SourceFailed, make_suggestion, MAX_TEXT_CHARS  # noqa: E402
from ..normalization import (  # noqa: E402
    _PERSON_FIELD_NORMALIZERS,
    _PROPERTY_FIELD_NORMALIZERS,
    field_value,
    norm_number,
    norm_text,
)

# Notary key -> khoá trường của lõi (payload `web_form`/`raw`).
PERSON_FIELD_SOURCES = {
    "ho_ten": "ho_ten",
    "ngay_sinh": "ngay_sinh",
    "so_giay_to": "cccd",
    "noi_cap": "noi_cap",
    "dia_chi": "dia_chi",
    "ngay_cap": "ngay_cap_cccd",
}
ASSET_FIELD_SOURCES = {
    "so_serial": "so_gcn_raw",
    "dia_chi": "dia_chi",
    "so_thua_dat": "so_thua_dat",
    "so_to_ban_do": "so_to_ban_do",
    "dien_tich": "dien_tich",
    "thoi_han": "thoi_han_su_dung",
    "nguon_goc": "nguon_goc",
    "so_vao_so": "so_vao_so",
    "ngay_cap": "ngay_cap_gcn",
    "co_quan_cap": "co_quan_cap",
    "loai_so": "loai_gcn",
}
GROUP_FIELD_SOURCES = {
    "so_serial": "so_serial",
    "dia_chi": "dia_chi",
    "so_thua_dat": "so_thua_dat",
    "so_to_ban_do": "so_to_ban_do",
    "dien_tich": "dien_tich",
    "thoi_han": "thoi_han",
    "nguon_goc": "nguon_goc",
    "so_vao_so": "so_vao_so",
    "ngay_cap": "ngay_cap",
    "co_quan_cap": "co_quan_cap",
    "loai_so": "loai_so",
}
REQUIRED_PERSON_FIELDS = ("ho_ten", "so_giay_to")
REQUIRED_ASSET_FIELDS = ("so_serial", "dia_chi")
# Trường tài sản có thể bị nguồn ghi nhiều lần -> khoá MỌI lần thấy của lõi.
# Hai shape KHÁC tên khoá serial: nhánh thửa/văn bản giữ tên lõi
# (`so_gcn_raw_values`, `loai_gcn_raw_values`), nhánh nhóm do `tach_nhom_tai_san`
# đổi tên (`so_serial_values`, `loai_so_values`). Lớp gọi truyền bảng theo
# shape tường minh — không alias ngầm một khoá cho cả hai shape.
_PARCEL_MULTI_VALUE_SOURCES = {
    "so_serial": "so_gcn_raw_values",
    "loai_so": "loai_gcn_raw_values",
    "so_thua_dat": "so_thua_dat_values",
    "so_to_ban_do": "so_to_ban_do_values",
    "dia_chi": "dia_chi_values",
    "dien_tich": "dien_tich_values",
    "nguon_goc": "nguon_goc_values",
    "thoi_han": "thoi_han_su_dung_values",
    "so_vao_so": "so_vao_so_values",
    "ngay_cap": "ngay_cap_values",
    "co_quan_cap": "co_quan_cap_values",
}
_GROUP_MULTI_VALUE_SOURCES = {
    **_PARCEL_MULTI_VALUE_SOURCES,
    "so_serial": "so_serial_values",
    "loai_so": "loai_so_values",
    "thoi_han": "thoi_han_values",
    "nguon_goc": "nguon_goc_values",
}


def _multi_values_from(values: dict, sources: dict) -> dict[str, list[str]]:
    """MỌI lần thấy của từng trường tài sản theo shape của ứng viên (lõi trả kèm).

    `sources` do lớp gọi truyền tường minh theo shape (`_PARCEL_MULTI_VALUE_SOURCES`
    cho thửa/văn bản, `_GROUP_MULTI_VALUE_SOURCES` cho nhóm). Mọi trường tài sản
    đang hỗ trợ đều giữ đủ lần thấy (Q4: kể cả loại giấy, diện tích/thời hạn
    cấp thửa) — consumer tự chọn/sửa khi có nhiều giá trị khác nhau.
    """
    return {
        key: [str(item).strip() for item in (values.get(source) or []) if str(item).strip()]
        for key, source in sources.items()
    }
UNSUPPORTED_LABELS = {
    "so_tiet_kiem": "sổ tiết kiệm / tài khoản",
    "bao_hiem": "quyền lợi bảo hiểm",
    "xe": "xe / phương tiện",
}


def _variants(value: str) -> tuple[str, ...]:
    """Biến thể chuẩn hoá của giá trị đã bóc.

    Nguồn Word có thể ở dạng NFD (hoặc NFC) trong khi giá trị đã được lõi
    chuẩn hoá về NFC — tìm đúng biến thể để span vẫn cắt đúng nguồn.
    """
    return tuple(dict.fromkeys((value, unicodedata.normalize("NFD", value), unicodedata.normalize("NFC", value))))


def _locate(text: str, value: str) -> list[int] | None:
    """Định vị giá trị đã bóc trong text nguồn (span code-point)."""
    if not value:
        return None
    for variant in _variants(value):
        index = text.find(variant)
        if index >= 0:
            return [index, index + len(variant)]
    return None


def _locate_in(text: str, value: str, window: tuple[int, int],
               index: "SourceSpanIndex | None" = None) -> list[int] | None:
    """Định vị trong vùng của CHÍNH ứng viên, thiếu thì chỉ nhận lần xuất hiện
    duy nhất toàn văn bản.

    Thứ tự (Q2/Q3): MỌI dạng chuẩn hoá TRONG vùng ứng viên trước — khớp nguyên
    văn rồi bản đồ span của lõi (cũng quét mọi dạng) — sau đó mới tới toàn văn
    bản, và chỉ nhận khi duy nhất. Giá trị lặp ở nhiều người/thửa mà không
    thấy trong vùng ứng viên thì KHÔNG mượn provenance của người khác: ví dụ
    hai người cùng số giấy tờ, một người ghi có khoảng trắng (Q2).
    """
    if not value:
        return None
    for variant in _variants(value):
        index_ = text.find(variant, window[0])
        if index_ >= 0 and index_ + len(variant) <= window[1]:
            return [index_, index_ + len(variant)]
    if index is not None:
        inside = [span for span in index.find_all(value, window)
                  if span[0] >= window[0] and span[1] <= window[1]]
        if len(inside) == 1:
            return [inside[0][0], inside[0][1]]
        if len(inside) > 1:
            return None  # nhiều lần thấy trong vùng ứng viên — không chọn hộ
    for variant in _variants(value):
        first = text.find(variant)
        if first < 0:
            continue
        if text.find(variant, first + 1) >= 0:
            return None  # giá trị lặp ngoài vùng ứng viên — không chọn hộ
        return [first, first + len(variant)]
    if index is not None:
        span = index.find(value, window)
        if span:
            return [span[0], span[1]]
    return None


LABELS = {
    "so_serial": (r"Số serial", r"Số phát hành(?:\s*\(\s*serial\s*\))?", r"Số GCN",
                  r"Giấy chứng nhận(?:\s+quyền\s+sử\s+dụng\s+đất)?(?:\s*\([^)\n]*\))?\s*số"),
    "dia_chi": (r"Địa chỉ thửa đất", r"Địa chỉ", r"có địa chỉ tại", r"tại địa chỉ"),
    "so_thua_dat": (r"Thửa đất số", r"Số thửa"),
    "so_to_ban_do": (r"Tờ bản đồ số", r"Số tờ(?: bản đồ)?"),
    "dien_tich": (r"Diện tích",),
    "loai_dat": (r"Loại đất", r"Mục đích sử dụng"),
    "thoi_han": (r"Thời hạn(?:\s+sử dụng)?",),
    "nguon_goc": (r"Nguồn gốc(?:\s+sử dụng(?:\s+đất)?)?",),
    "so_vao_so": (r"Số vào sổ", r"Vào sổ số"),
    "ngay_cap": (r"Ngày cấp",),
    "loai_so": (r"Giấy chứng nhận",),
    "ho_ten": (r"Ông", r"Bà", r"Tên", r"Họ và tên", r"Họ, chữ đệm, tên"),
    "so_giay_to": (r"Căn cước công dân(?:\s+số)?", r"Căn cước(?:\s+số)?", r"CCCD", r"CMND",
                   r"Chứng minh nhân dân(?:\s+số)?", r"Hộ chiếu(?:\s+số)?"),
    "ngay_sinh": (r"Sinh ngày", r"Ngày sinh"),
    "ngay_cap_cccd": (r"Ngày cấp",),
    "dia_chi_nguoi": (r"Thường trú tại", r"Nơi thường trú", r"Nơi cư trú", r"Trú tại", r"Địa chỉ"),
}


def _locate_labeled(text: str, value: str, labels: tuple[str, ...],
                    window: tuple[int, int],
                    index: "SourceSpanIndex | None" = None) -> list[int] | None:
    """Định vị giá trị NGAY SAU nhãn của nó (bằng chứng đúng ô) trong vùng ứng viên.

    Không có nhãn trong vùng thì rơi về `_locate_in` (cục bộ trước, chỉ nhận
    lần xuất hiện duy nhất toàn văn bản) — không mượn lần khớp đầu tiên ở
    ngoài vùng ứng viên.
    """
    if not value:
        return None
    for label in labels:
        pattern = re.compile(rf"(?im){label}\s*:?[ \t]*{re.escape(value)}")
        for match in pattern.finditer(text, window[0], window[1]):
            start = match.end() - len(value)
            return [start, match.end()]
    return _locate_in(text, value, window, index)


PERSON_LABELS = {
    "ho_ten": LABELS["ho_ten"],
    "so_giay_to": LABELS["so_giay_to"],
    "ngay_sinh": LABELS["ngay_sinh"],
    "ngay_cap": LABELS["ngay_cap_cccd"],
    "dia_chi": LABELS["dia_chi_nguoi"],
}
ASSET_LABELS = {
    "so_serial": LABELS["so_serial"],
    "dia_chi": LABELS["dia_chi"],
    "so_thua_dat": LABELS["so_thua_dat"],
    "so_to_ban_do": LABELS["so_to_ban_do"],
    "dien_tich": LABELS["dien_tich"],
    "thoi_han": LABELS["thoi_han"],
    "nguon_goc": LABELS["nguon_goc"],
    "so_vao_so": LABELS["so_vao_so"],
    "ngay_cap": LABELS["ngay_cap"],
    "loai_so": LABELS["loai_so"],
}


def _person_window(text: str, person: dict) -> tuple[int, int]:
    """Vùng text của một người (theo `raw_text` của lõi) để ưu tiên span đúng."""
    raw = str(person.get("raw_text") or "")
    span = _locate(text, raw) if raw else None
    return (span[0], span[1]) if span else (0, len(text))


async def extract(spec, ctx):
    content = ctx.read_file(spec)
    try:
        source = read_docx(content)
    except Exception as exc:
        raise SourceFailed("intake.parse_failed", "Không đọc được gói DOCX") from exc
    if not source.text.strip():
        raise SourceFailed("intake.parse_failed", "DOCX không có nội dung text")
    if len(source.text) > MAX_TEXT_CHARS:
        raise SourceFailed("intake.parse_failed", "DOCX vượt giới hạn 100.000 ký tự")
    payload = extract_text(source.text, file_name=str(spec.filename or ""))
    raw = payload["raw"]
    span_index = build_span_index(source.text)
    suggestions: list[dict] = []

    def make_refs(candidate_id, span, rule_id, *, extra: dict | None = None):
        ref = {
            "kind": "docx", "source_id": spec.source_id, "source_sha256": source.sha256,
            "text_map_version": 1, "candidate_id": candidate_id, "candidate_state": "matched",
            "occurrence_id": str(uuid.uuid4()), "span": list(span),
            "raw_snippet": source.text[span[0]:span[1]],
            "rule_id": rule_id, "profile_id": ENGINE_ID, "profile_version": ENGINE_VERSION,
            "core_state": "matched", "docx_refs": source.refs(list(span)),
        }
        if extra:
            ref.update(extra)
        return ref

    def add_field(fields, warnings, candidate_id, normalizers, *,
                  key, raw_value, span, rule_id):
        ref = make_refs(candidate_id, span, rule_id)
        normalizer = normalizers.get(key, norm_text)
        normalized, state, confidence = normalizer(raw_value)
        if key == "dien_tich" and normalized is None:
            ref["core_state"] = "error"
            warnings.append({"code": "intake.invalid_number",
                             "message": "Diện tích cần là số hữu hạn từ 0 trở lên; hãy sửa giá trị"})
        if key in ("ngay_sinh", "ngay_cap", "ngay_het_han", "ngay_chet") and normalized is None:
            ref["core_state"] = "error"
            warnings.append({"code": "intake.invalid_date",
                             "message": f"{key}: ngày không hợp lệ; hãy sửa trước khi đưa vào Stage"})
        fields[key] = field_value(raw_value, normalized, state, confidence, [ref])
        return normalized

    def map_fields(fields, warnings, candidate_id, normalizers, sources: dict, values: dict,
                   window: tuple[int, int], rule_prefix: str, labels: dict,
                   skip: frozenset = frozenset()):
        for key, source_key in sources.items():
            if key in skip:
                continue  # Trường mơ hồ do lớp gọi tự emit (giữ mọi lần thấy).
            raw_value = str(values.get(source_key) or "").strip()
            if not raw_value:
                continue  # Không emit "" như null (contract §2.2).
            span = _locate_labeled(source.text, raw_value, labels.get(key, ()), window, span_index)
            if not span:
                continue
            normalized = add_field(fields, warnings, candidate_id, normalizers,
                                   key=key, raw_value=raw_value, span=span,
                                   rule_id=f"{rule_prefix}.{key}")
            if key == "so_serial" and normalized is None:
                warnings.append({"code": "intake.warning_nonstandard",
                                 "message": "so_serial: giữ nguyên văn theo nguồn; cần kiểm tra lại"})

    # ----- người: hai bên của lõi, theo thứ tự trong văn bản -----
    people: list[dict] = []
    for side in ("ben_a", "ben_b"):
        people.extend((raw.get(side) or {}).get("nguoi") or [])
    for person in people:
        candidate_id = str(uuid.uuid4())
        fields: dict = {}
        warnings = [{"code": "intake.docx_coverage", "message": w} for w in source.warnings]
        map_fields(fields, warnings, candidate_id, _PERSON_FIELD_NORMALIZERS,
                   PERSON_FIELD_SOURCES, person, _person_window(source.text, person),
                   "person", PERSON_LABELS)
        if not fields:
            continue
        extra_ids = [str(value).strip() for value in (person.get("cccd_khac") or []) if str(value).strip()]
        if extra_ids and "so_giay_to" in fields:
            refs = list(fields["so_giay_to"]["source_refs"])
            window = _person_window(source.text, person)
            for value in extra_ids:
                span = _locate_labeled(source.text, value, LABELS["so_giay_to"], window, span_index)
                if span:
                    refs.append(make_refs(candidate_id, span, "person.so_giay_to"))
            if len(refs) > 1:
                # Nguồn có nhiều giấy tờ cho cùng người: giữ đủ bằng chứng,
                # không tự chọn giá trị (cần người kiểm tra).
                fields["so_giay_to"] = field_value(fields["so_giay_to"]["raw_value"], None,
                                                   "observed", None, refs)
                warnings.append({"code": "intake.ambiguous",
                                 "message": "so_giay_to: nhiều giá trị; cần chọn hoặc sửa"})
        if any(key not in fields for key in REQUIRED_PERSON_FIELDS):
            warnings.append({"code": "intake.fragment",
                             "message": "Bản ghi thiếu trường; hãy bổ sung trước khi lưu hồ sơ"})
        suggestion = make_suggestion(source_id=spec.source_id, target="person",
                                     fields=fields, warnings=warnings)
        suggestion["suggestion_id"] = candidate_id
        suggestions.append(suggestion)

    # ----- tài sản -----
    tai_san_block = str(payload["web_form"].get("tai_san") or "")
    groups = tach_nhom_tai_san(tai_san_block)
    parcels = [row for row in (raw.get("danh_sach_thua_dat") or [])
               if any(str(row.get(key) or "").strip() for key in (
                   "so_thua_dat", "so_to_ban_do", "so_gcn_raw", "dia_chi"))]
    multi_parcel = len(parcels) > 1 and not groups
    unsupported = [UNSUPPORTED_LABELS[code] for code in (raw.get("tai_san_chua_ho_tro") or [])
                   if code in UNSUPPORTED_LABELS]

    def _window_after(text: str, marker: str, start: int) -> int:
        """Vị trí bắt đầu của mốc kế tiếp (dùng để chặn vùng tìm span)."""
        index = text.find(marker, start) if marker else -1
        return index if index >= 0 else len(text)

    def group_window(index: int) -> tuple[int, int]:
        """Vùng nguồn của một nhóm 'Tài sản N:' (đến nhóm kế tiếp)."""
        title = str(groups[index].get("tieu_de") or "")
        span = _locate(source.text, title) if title else None
        start = span[0] if span else 0
        end = len(source.text)
        for other in groups[index + 1:]:
            other_title = str(other.get("tieu_de") or "")
            if other_title:
                end = _window_after(source.text, other_title, start + 1)
                break
        return (start, end)

    def parcel_window(index: int) -> tuple[int, int]:
        """Vùng nguồn của một thửa (từ đầu khối thửa đến nhãn thửa kế tiếp).

        Đầu khối lùi qua các dòng mở thửa NGAY TRƯỚC nhãn thửa — câu mở
        "quyền sử dụng đất tại địa chỉ: … theo Giấy chứng nhận …" (F4/F5) nằm
        trước nhãn thửa; dừng ở dòng có nhãn thửa của thửa khác (không mượn
        vùng của thửa khác), dòng trống, hoặc quá 5 dòng/500 ký tự.
        """
        thua = str(parcels[index].get("so_thua_dat") or "").strip()
        span = _locate_labeled(source.text, thua, LABELS["so_thua_dat"], (0, len(source.text))) if thua else None
        start = span[0] if span else 0
        end = len(source.text)
        for other in parcels[index + 1:]:
            other_thua = str(other.get("so_thua_dat") or "").strip()
            if other_thua:
                next_span = _locate_labeled(source.text, other_thua, LABELS["so_thua_dat"],
                                            (start + 1, len(source.text)))
                if next_span:
                    end = next_span[0]
                    break
        floor = start
        for _ in range(5):
            newline = source.text.rfind("\n", 0, floor)
            if newline < 0 or start - newline > 500:
                break
            prev_newline = source.text.rfind("\n", 0, newline)
            prev_line = source.text[prev_newline + 1:newline]
            if not prev_line.strip():
                break
            if any(
                str(other.get("so_thua_dat") or "").strip()
                and str(other.get("so_thua_dat") or "").strip() in prev_line
                for other in parcels[:index]
            ):
                break
            floor = prev_newline + 1
        return (floor, end)

    def emit_asset(values: dict, sources: dict, window: tuple[int, int],
                   land_rows_raw: list[dict] | None = None,
                   multi_values: dict[str, list[str]] | None = None):
        candidate_id = str(uuid.uuid4())
        fields: dict = {}
        warnings = [{"code": "intake.docx_coverage", "message": w} for w in source.warnings]
        if multi_parcel:
            warnings.append({"code": "intake.multi_parcel",
                             "message": "Văn bản có nhiều thửa; mỗi dòng tài sản là một thửa"})
        for label in unsupported:
            warnings.append({"code": "intake.unsupported_asset",
                             "message": f"{label}: chưa hỗ trợ bóc chi tiết; kiểm tra thủ công"})
        # "Nhiều giá trị" = nhiều giá trị KHÁC NHAU; cùng một giá trị lặp ở hai
        # lần thấy không phải mơ hồ (Q1: khác biệt do chuẩn hoá/tiền tố không
        # được tạo đáp án thứ hai cho cùng một serial). So khớp trên dạng gộp
        # khoảng trắng: "AB  123456" và "AB 123456" là MỘT giá trị (nguyên văn
        # vẫn là lát cắt nguồn, xem `_labeled_occurrences`).
        ambiguous = {
            key: list(occurrences)
            for key, occurrences in (multi_values or {}).items()
            if len({re.sub(r"\s+", " ", str(value)).strip()
                    for value in occurrences if str(value).strip()}) > 1
        }
        skip_keys = set(ambiguous)
        # Loại giấy: lõi trả giá trị CHUẨN + NGUYÊN VĂN nguồn (có thể là tiêu đề
        # hoa 2 dòng). Bằng chứng phải cắt đúng nguyên văn; giá trị chuẩn giữ
        # riêng — tìm bằng giá trị chuẩn sẽ trượt span vì lệch hoa–thường.
        loai_so_raw = next(iter((multi_values or {}).get("loai_so") or []), "")
        loai_so_canonical = str(values.get(sources.get("loai_so") or "") or "").strip()
        if loai_so_raw and loai_so_canonical:
            span = _locate_labeled(source.text, loai_so_raw, ASSET_LABELS.get("loai_so", ()),
                                   window, span_index)
            if span:
                ref = make_refs(candidate_id, span, "asset.loai_so")
                fields["loai_so"] = field_value(loai_so_raw, loai_so_canonical, "normalized", None, [ref])
                skip_keys.add("loai_so")
        map_fields(fields, warnings, candidate_id, _PROPERTY_FIELD_NORMALIZERS,
                   sources, values, window, "asset", ASSET_LABELS, frozenset(skip_keys))
        # Nhiều giá trị trong cùng nhóm: giữ MỌI lần thấy, normalized null cho
        # tới khi người kiểm tra chọn/sửa (spec `word-templates.md`), và giữ
        # `ambiguous_group` thay vì mặc định matched.
        for key, occurrences in ambiguous.items():
            refs = []
            for occurrence in occurrences:
                span = _locate_labeled(source.text, str(occurrence).strip(),
                                       ASSET_LABELS.get(key, ()), window, span_index)
                if not span:
                    continue
                ref = make_refs(candidate_id, span, f"asset.{key}")
                ref["candidate_state"] = "ambiguous_group"
                ref["core_state"] = "ambiguous_group"
                refs.append(ref)
            if len(refs) < 2:
                continue
            fields[key] = field_value(str(occurrences[0]).strip(), None, "observed", None, refs)
            warnings.append({"code": "intake.ambiguous",
                             "message": f"{key}: nhiều giá trị; cần chọn hoặc sửa"})
        rows_raw = list(land_rows_raw or [])
        for index, row in enumerate(rows_raw, 1):
            if not any(str(row.get(key) or "").strip() for key in ("loai_dat", "dien_tich", "thoi_han")):
                warnings.append({
                    "code": "intake.fragment",
                    "message": f"Cụm đất {index} thiếu dữ liệu; hãy bổ sung trước khi lưu hồ sơ"})
        if any(str(row.get("loai_dat") or "").strip() for row in rows_raw):
            rows, refs = [], []
            cursor = window[0]
            for index, row in enumerate(rows_raw, 1):
                entry = {"loai_dat": None, "dien_tich": None, "thoi_han": None}
                row_start = cursor
                for key in ("loai_dat", "dien_tich", "thoi_han"):
                    raw_value = str(row.get(key) or "").strip()
                    if not raw_value:
                        continue
                    # Bằng chứng cục bộ theo dòng: tìm từ vị trí dòng trước đã
                    # dùng tới, không mượn lần khớp đầu của cụm khác (hai cụm
                    # cùng `Diện tích: 120 m2` phải trỏ về đúng cụm).
                    span = _locate_labeled(source.text, raw_value, LABELS[key],
                                           (row_start, window[1]), span_index)
                    if not span:
                        continue
                    core_state = "matched"
                    if key == "dien_tich":
                        # Luật lõi (Owner 06/10/2026) đọc ô diện tích CÓ ĐƠN VỊ
                        # ("200,0m²" -> 200.0) — adapter không chép lại luật,
                        # chỉ chuẩn hoá đích trên giá trị không đơn vị như cũ.
                        # Ô mơ hồ ("1.234") vẫn None + cảnh báo, giữ nguyên văn
                        # trong bằng chứng.
                        number = dien_tich_thanh_so(raw_value)
                        normalized, _, _ = norm_number("" if number is None else str(number))
                        entry["dien_tich"] = normalized
                        if normalized is None:
                            core_state = "error"
                            warnings.append({
                                "code": "intake.invalid_number",
                                "message": f"Cụm đất {index}: diện tích cần là số hữu hạn từ 0 trở lên; hãy sửa"})
                    else:
                        normalized, _, _ = norm_text(raw_value)
                        entry[key] = normalized
                    ref = make_refs(candidate_id, span, f"asset.{key}",
                                    extra={"land_row": index, "land_field": key})
                    ref["core_state"] = core_state
                    refs.append(ref)
                    cursor = max(cursor, span[1])
                rows.append(entry)
            if refs:
                value = json.dumps(rows, ensure_ascii=False, allow_nan=False)
                fields["land_rows"] = field_value(value, value, "normalized", None, refs)
                # Cụm đất đã mang dòng đất: bỏ bản phẳng trùng span để binding
                # không chồng vị trí.
                fields.pop("dien_tich", None)
                fields.pop("thoi_han", None)
        if not fields:
            return
        if any(key not in fields for key in REQUIRED_ASSET_FIELDS):
            warnings.append({"code": "intake.fragment",
                             "message": "Bản ghi thiếu trường; hãy bổ sung trước khi lưu hồ sơ"})
        suggestion = make_suggestion(source_id=spec.source_id, target="asset",
                                     fields=fields, warnings=warnings)
        suggestion["suggestion_id"] = candidate_id
        suggestions.append(suggestion)

    if groups:
        # Văn bản liệt kê nhóm "Tài sản thứ N": mỗi nhóm là một gợi ý tài sản
        # (kèm các dòng đất của nhóm — nguồn thật liệt kê nhiều dòng).
        for index, group in enumerate(groups):
            if not any(str(group.get(key) or "").strip() for key in (
                    "so_serial", "dia_chi", "so_thua_dat", "so_to_ban_do")) and not any(
                    any(str(row.get(key) or "").strip() for key in ("loai_dat", "dien_tich", "thoi_han"))
                    for row in group.get("land_rows") or []):
                continue  # Nhóm chỉ có nhãn trống: không tạo gợi ý rỗng.
            emit_asset(group, GROUP_FIELD_SOURCES, group_window(index),
                       land_rows_raw=group.get("land_rows"),
                       multi_values=_multi_values_from(group, _GROUP_MULTI_VALUE_SOURCES))
    else:
        for index, parcel in enumerate(parcels):
            land_rows_raw = [
                {"loai_dat": detail.get("muc_dich_su_dung"),
                 "dien_tich": detail.get("dien_tich"),
                 "thoi_han": detail.get("thoi_han_su_dung")}
                for detail in parcel.get("chi_tiet_dien_tich") or []
            ]
            emit_asset(parcel, ASSET_FIELD_SOURCES, parcel_window(index),
                       land_rows_raw=land_rows_raw,
                       multi_values=_multi_values_from(parcel, _PARCEL_MULTI_VALUE_SOURCES))
        if not parcels:
            # GCN ở mức văn bản (không có dòng thửa): giữ hành vi cũ — vẫn ra
            # gợi ý tài sản khi có serial/địa chỉ.
            context = document_asset_context(tai_san_block)
            if any(str(context.get(key) or "").strip() for key in ("so_gcn_raw", "dia_chi")):
                emit_asset(context, ASSET_FIELD_SOURCES, (0, len(source.text)),
                           multi_values=_multi_values_from(context, _PARCEL_MULTI_VALUE_SOURCES))

    for key in ("so_giay_to", "so_serial"):
        buckets: dict = {}
        for suggestion in suggestions:
            value = suggestion["fields"].get(key, {}).get("normalized_value")
            if value:
                buckets.setdefault(value, []).append(suggestion)
        for group in buckets.values():
            if len(group) > 1:
                for suggestion in group:
                    suggestion["warnings"].append({"code": "intake.suspected_duplicate",
                                                   "message": "Giấy tờ trùng ứng viên khác; không tự gộp"})

    if not suggestions:
        raise SourceFailed("intake.parse_failed",
                           "Lõi trích xuất chưa nhận được người hoặc tài sản; hãy kiểm tra mẫu")
    if ctx.store_docx:
        ctx.store_docx(content, suggestions, spec.filename or 'Hợp đồng Word')
    return suggestions

"""Ordered DOCX → shared regex core → review candidates with exact field evidence."""
from __future__ import annotations
import uuid
import json
import sys
from pathlib import Path
# Shared source ships beside the engine; avoid colliding with notary_v2.tools.
_SHARED_TOOLS = str(Path(__file__).resolve().parents[4] / "tools")
if _SHARED_TOOLS not in sys.path:
    sys.path.insert(0, _SHARED_TOOLS)
from regex_workbench.engine.runner import load_profile, run
from ..docx_source import read_docx
from ..models import SourceFailed, make_suggestion, MAX_TEXT_CHARS
from ..normalization import _PERSON_FIELD_NORMALIZERS, _PROPERTY_FIELD_NORMALIZERS, field_value, norm_text, norm_number

ALIASES = {"cccd": "so_giay_to", "dia_chi_thua": "dia_chi", "thua_dat": "so_thua_dat",
           "to_ban_do": "so_to_ban_do", "dien_tich_m2": "dien_tich", "ngay_cap_gcn": "ngay_cap"}


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
    result = run(source.text, load_profile("transfer"))
    source.warnings.extend("Một quy tắc trích xuất lỗi; cần kiểm tra lại dữ liệu" for _ in result["errors"])
    suggestions = []

    def candidate(target, matches, group_state="matched", allow_empty=False):
        fields, warnings = {}, [{"code": "intake.docx_coverage", "message": w} for w in source.warnings]
        candidate_id = str(uuid.uuid4())
        normalizers = _PERSON_FIELD_NORMALIZERS if target == "person" else _PROPERTY_FIELD_NORMALIZERS
        for match in matches:
            key = ALIASES.get(match["name"], match["name"])
            if key == "gioi_tinh":
                continue  # A title is wording evidence, not confirmed gender.
            hits = match.get("candidates") or ([{"span": match["span"], "value": match.get("value")}]
                                                  if match.get("span") else [])
            if not hits:
                continue
            refs = []
            for hit in hits:
                span = hit["span"]
                refs.append({"kind": "docx", "source_id": spec.source_id,
                             "source_sha256": source.sha256, "text_map_version": 1,
                             "candidate_id": candidate_id, "candidate_state": group_state,
                             "occurrence_id": str(uuid.uuid4()), "span": span,
                             "raw_snippet": source.text[span[0]:span[1]],
                             "rule_id": match["rule_id"], "profile_id": result["profile_id"],
                             "profile_version": result["profile_version"], "core_state": match["state"],
                             "docx_refs": source.refs(span)})
            raw = refs[0]["raw_snippet"]
            normalized, state, confidence = normalizers.get(key, norm_text)(raw)
            if key == "dien_tich" and normalized is None:
                for ref in refs:
                    ref["core_state"] = "error"
                warnings.append({"code": "intake.invalid_number", "message": "Diện tích cần là số hữu hạn từ 0 trở lên; hãy sửa giá trị"})
            if match["state"] in ("ambiguous", "error", "warning_nonstandard"):
                normalized, state, confidence = None, "observed", None
                warnings.append({"code": "intake." + match["state"], "message": f"{key}: cần chọn hoặc sửa giá trị"})
            fields[key] = field_value(raw, normalized, state, confidence, refs)
        if not fields and not allow_empty:
            return
        if group_state == "ambiguous_group":
            warnings.append({"code": "intake.ambiguous_group", "message": "Chưa có nhãn phân chia tài sản; kiểm tra các trường thuộc cùng tài sản"})
        required = ("ho_ten", "so_giay_to") if target == "person" else ("so_serial", "dia_chi")
        if any(key not in fields for key in required):
            warnings.append({"code": "intake.fragment", "message": "Bản ghi thiếu trường; hãy bổ sung trước khi lưu hồ sơ"})
        suggestion = make_suggestion(source_id=spec.source_id, target=target, fields=fields, warnings=warnings)
        suggestion["suggestion_id"] = candidate_id
        suggestions.append(suggestion)
        return suggestion

    for block in result["parties"].get("blocks", []):
        for person in block.get("persons", []):
            candidate("person", person["fields"].values())
    for group in result.get("asset_groups", []):
        has_identifier = any(match.get("span") and match["name"] in ("so_serial", "thua_dat", "so_vao_so") for match in group["fields"])
        has_address = any(match.get("span") and match["name"] == "dia_chi_thua" for match in group["fields"])
        has_land = any(match.get("span") for row in group.get("land_rows", []) for match in row)
        if not has_identifier and not (group["state"] == "matched" and (has_address or has_land)):
            continue
        suggestion = candidate("asset", group["fields"], group["state"], allow_empty=has_land)
        if suggestion and group.get("land_rows"):
            rows, refs = [], []
            for index, row_matches in enumerate(group["land_rows"], 1):
                row = {"loai_dat": None, "dien_tich": None, "thoi_han": None}
                refs_before = len(refs)
                for match in row_matches:
                    if not match.get("span"):
                        continue
                    hits = match.get("candidates") or [{"span": match["span"]}]
                    if match["state"] == "ambiguous":
                        suggestion["warnings"].append({"code": "intake.ambiguous", "message": f"Cụm đất {index}: {match['name']} có nhiều giá trị; hãy chọn hoặc sửa"})
                    for hit in hits:
                        span = hit["span"]
                        raw = source.text[span[0]:span[1]]
                        core_state = match["state"]
                        if match["state"] == "matched":
                            row[match["name"]] = norm_number(raw)[0] if match["name"] == "dien_tich" else raw.strip()
                            if match["name"] == "dien_tich" and row[match["name"]] is None:
                                core_state = "error"
                                suggestion["warnings"].append({"code": "intake.invalid_number", "message": f"Cụm đất {index}: diện tích cần là số hữu hạn từ 0 trở lên; hãy sửa"})
                        refs.append({"kind": "docx", "source_id": spec.source_id, "source_sha256": source.sha256,
                                     "text_map_version": 1, "candidate_id": suggestion["suggestion_id"],
                                     "candidate_state": group["state"], "profile_id": result["profile_id"],
                                     "profile_version": result["profile_version"],
                                     "occurrence_id": str(uuid.uuid4()), "span": span, "raw_snippet": raw,
                                     "land_row": index, "land_field": match["name"], "core_state": core_state,
                                     "docx_refs": source.refs(span), "rule_id": match["rule_id"]})
                if len(refs) == refs_before:
                    suggestion["warnings"].append({"code": "intake.fragment", "message": f"Cụm đất {index} thiếu dữ liệu; hãy bổ sung trước khi lưu hồ sơ"})
                rows.append(row)
            value = json.dumps(rows, ensure_ascii=False, allow_nan=False)
            if not refs:
                suggestion["warnings"].append({"code": "intake.fragment", "message": "Cụm đất thiếu dữ liệu; hãy bổ sung trước khi lưu hồ sơ"})
                continue
            suggestion["fields"]["land_rows"] = field_value(value, value, "normalized", None, refs)
            # Total area is derived from confirmed rows; repeated row areas are not ambiguity of ownership.
            suggestion["fields"].pop("dien_tich", None)
            suggestion["warnings"] = [w for w in suggestion["warnings"] if not w["message"].startswith("dien_tich:")]
    for key in ("so_giay_to", "so_serial"):
        buckets = {}
        for suggestion in suggestions:
            value = suggestion["fields"].get(key, {}).get("normalized_value")
            if value:
                buckets.setdefault(value, []).append(suggestion)
        for group in buckets.values():
            if len(group) > 1:
                for suggestion in group:
                    suggestion["warnings"].append({"code": "intake.suspected_duplicate", "message": "Giấy tờ trùng ứng viên khác; không tự gộp"})
    if not suggestions:
        raise SourceFailed("intake.parse_failed", "Lõi trích xuất chưa nhận được người hoặc tài sản; hãy kiểm tra mẫu")
    if ctx.store_docx:
        ctx.store_docx(content, suggestions, spec.filename or 'Hợp đồng Word')
    return suggestions

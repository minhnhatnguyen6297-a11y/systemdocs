"""XLSX source adapter — shared person-sheet parser (excel_parse.py).

Mỗi dòng dữ liệu → 1 person suggestion với source_refs {sheet, cell, row}.
Không ghi DB — intake chỉ emit suggestion chờ user commit (khác upload_excel
legacy vốn ghi thẳng customers).
"""

from __future__ import annotations

from .. import excel_parse
from ..models import AdapterContext, SourceFailed, SourceSpec
from ..normalization import person_row_to_suggestion


async def extract(spec: SourceSpec, ctx: AdapterContext) -> list[dict]:
    content = ctx.read_file(spec)
    try:
        sheet = excel_parse.parse_people_workbook(content)
    except excel_parse.ExcelParseError as exc:
        raise SourceFailed("intake.parse_failed", str(exc)) from exc

    suggestions: list[dict] = []
    for row in sheet["rows"]:
        form = row["form"]
        if not form.get("ho_ten") and not form.get("so_giay_to"):
            continue
        sug = person_row_to_suggestion(
            form, row["cells"], spec.source_id, sheet["sheet"], row["row_num"])
        if sug:
            suggestions.append(sug)

    if not suggestions:
        raise SourceFailed(
            "intake.parse_failed",
            "không có dòng dữ liệu người hợp lệ trong Excel")
    return suggestions

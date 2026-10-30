#!/usr/bin/env python3
"""Đo độ chính xác từng trường của bộ chuẩn hóa OCR gốc trên bộ ca tổng hợp.

Chạy từ gốc repo:

    python tools/ocr_eval/field_accuracy.py [--cases path] [--json out]

Script chỉ đọc cases, gọi ``_normalize_native_ocr_doc(lines, "<id>.jpg")`` và so
nhãn ``expected`` viết tay với ``doc["data"]``. Không thư viện ngoài, không log
hay telemetry khác. Exit code 1 khi có ít nhất một field lệch.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from notary_v2.services.document_intake.ocr_pipeline import (  # noqa: E402
    _normalize_native_ocr_doc,
)

DEFAULT_CASES = REPO_ROOT / "testdata" / "ocr-field-accuracy" / "v1" / "cases.json"

FIELD_ORDER = [
    "ho_ten",
    "so_giay_to",
    "ngay_sinh",
    "chi_co_nam_sinh",
    "loai_giay_to",
    "gioi_tinh",
    "dia_chi",
    "ngay_cap",
    "noi_cap",
    "ngay_chet",
    "so_trich_luc_khai_tu",
    "noi_cap_khai_tu",
    "ngay_ky",
    "noi_chet",
    "noi_thuong_tru_cuoi",
    "so_serial",
    "so_vao_so",
    "co_quan_cap",
    "so_thua_dat",
    "so_to_ban_do",
    "dien_tich",
    "loai_dat",
    "hinh_thuc_su_dung",
    "thoi_han",
    "nguon_goc",
    "land_rows.loai_dat",
    "land_rows.dien_tich",
    "land_rows.thoi_han",
]

EXPECTED_SIDE = {
    "cccd_front": "front",
    "cccd_back": "back",
    "death_certificate": "single",
    "gcn": "unknown",
}

_TRAILING_PUNCT = " ,.;:"


def normalize_value(value: object) -> str:
    """Chuẩn hóa để so khớp: NFC, gộp khoảng trắng, casefold, bỏ dấu câu cuối."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value))
    text = " ".join(text.split())
    return text.casefold().rstrip(_TRAILING_PUNCT)


def _matches_value(want: object, got: object) -> bool:
    if type(want) is bool:
        return type(got) is bool and got == want
    return normalize_value(want) == normalize_value(got)


def _land_row_fields(want: object, got: object) -> list[dict]:
    """So từng ô theo vị trí; thiếu dòng/khóa không tương đương ô rỗng."""
    expected_rows = want if isinstance(want, list) else []
    actual_rows = got if isinstance(got, list) else []
    valid_lists = isinstance(want, list) and isinstance(got, list)
    row_count = max(len(expected_rows), len(actual_rows), 0 if valid_lists else 1)
    fields = []
    for row_index in range(row_count):
        expected_row = expected_rows[row_index] if row_index < len(expected_rows) else None
        actual_row = actual_rows[row_index] if row_index < len(actual_rows) else None
        for child in ("loai_dat", "dien_tich", "thoi_han"):
            expected_present = isinstance(expected_row, dict) and child in expected_row
            got_present = isinstance(actual_row, dict) and child in actual_row
            expected_value = expected_row[child] if expected_present else None
            actual_value = actual_row[child] if got_present else None
            fields.append(
                {
                    "field": f"land_rows.{child}",
                    "row_index": row_index,
                    "expected": expected_value,
                    "got": actual_value,
                    "expected_present": expected_present,
                    "got_present": got_present,
                    "ok": (
                        valid_lists
                        and expected_present
                        and got_present
                        and _matches_value(expected_value, actual_value)
                    ),
                }
            )
    return fields


def evaluate(cases: list[dict]) -> list[dict]:
    results: list[dict] = []
    for case in cases:
        case_id = str(case.get("id") or "")
        kind = str(case.get("kind") or "")
        lines = [str(line) for line in case.get("lines") or []]
        expected = case.get("expected") or {}
        doc = _normalize_native_ocr_doc(lines, f"{case_id}.jpg")
        data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
        fields = []
        for field, want in expected.items():
            got = data.get(field, "")
            if field == "land_rows":
                fields.extend(_land_row_fields(want, got))
                continue
            fields.append(
                {
                    "field": field,
                    "expected": want,
                    "got": got,
                    "ok": _matches_value(want, got),
                }
            )
        results.append(
            {
                "id": case_id,
                "kind": kind,
                "doc_type": doc.get("doc_type"),
                "side": doc.get("side"),
                "fields": fields,
            }
        )
    return results


def _ordered_fields(results: list[dict]) -> list[str]:
    seen: list[str] = []
    for result in results:
        for item in result["fields"]:
            if item["field"] not in seen:
                seen.append(item["field"])
    head = [field for field in FIELD_ORDER if field in seen]
    tail = sorted(field for field in seen if field not in FIELD_ORDER)
    return head + tail


def _pct(ok: int, total: int) -> str:
    if total == 0:
        return "-"
    return f"{100.0 * ok / total:.1f}%"


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    out = ["  ".join(header.ljust(widths[i]) for i, header in enumerate(headers)).rstrip()]
    out.append("  ".join("-" * width for width in widths))
    for row in rows:
        out.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip())
    return out


def field_rows(results: list[dict], *, non_empty_only: bool) -> list[dict]:
    rows: list[dict] = []
    for field in _ordered_fields(results):
        total = 0
        ok = 0
        for result in results:
            for item in result["fields"]:
                if item["field"] != field:
                    continue
                if non_empty_only and normalize_value(item["expected"]) == "":
                    continue
                total += 1
                ok += 1 if item["ok"] else 0
        rows.append({"field": field, "cases": total, "ok": ok, "accuracy": _pct(ok, total)})
    return rows


def kind_rows(results: list[dict]) -> list[dict]:
    order: list[str] = []
    buckets: dict[str, dict[str, int]] = {}
    for result in results:
        kind = result["kind"]
        if kind not in buckets:
            order.append(kind)
            buckets[kind] = {"cases": 0, "checks": 0, "ok": 0, "exact": 0}
        bucket = buckets[kind]
        bucket["cases"] += 1
        case_ok = True
        for item in result["fields"]:
            bucket["checks"] += 1
            if item["ok"]:
                bucket["ok"] += 1
            else:
                case_ok = False
        bucket["exact"] += 1 if case_ok else 0
    return [
        {
            "kind": kind,
            "cases": buckets[kind]["cases"],
            "checks": buckets[kind]["checks"],
            "ok": buckets[kind]["ok"],
            "accuracy": _pct(buckets[kind]["ok"], buckets[kind]["checks"]),
            "exact_cases": buckets[kind]["exact"],
        }
        for kind in order
    ]


def side_rows(results: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for result in results:
        expected_side = EXPECTED_SIDE.get(result["kind"])
        rows.append(
            {
                "id": result["id"],
                "kind": result["kind"],
                "doc_type": str(result["doc_type"]),
                "side": str(result["side"]),
                "expected_side": expected_side or "",
                "side_ok": expected_side is None or result["side"] == expected_side,
            }
        )
    return rows


def summarize(results: list[dict]) -> dict:
    checks = sum(len(result["fields"]) for result in results)
    ok = sum(1 for result in results for item in result["fields"] if item["ok"])
    exact = sum(1 for result in results if all(item["ok"] for item in result["fields"]))
    return {
        "cases": len(results),
        "field_checks": checks,
        "field_ok": ok,
        "field_accuracy": _pct(ok, checks),
        "exact_cases": exact,
    }


def render(results: list[dict], cases_path: Path) -> list[str]:
    lines: list[str] = []
    summary = summarize(results)
    lines.append(f"cases file: {cases_path}")
    lines.append(
        "cases={cases} field_checks={field_checks} ok={field_ok} "
        "accuracy={field_accuracy} exact_cases={exact_cases}/{cases}".format(**summary)
    )

    lines.append("")
    lines.append("== Field accuracy (mọi ca có field trong expected) ==")
    rows = field_rows(results, non_empty_only=False)
    lines.extend(
        _table(
            ["field", "cases", "ok", "accuracy"],
            [[row["field"], str(row["cases"]), str(row["ok"]), row["accuracy"]] for row in rows],
        )
    )

    lines.append("")
    lines.append("== Field accuracy (chỉ ca expected khác rỗng) ==")
    rows = field_rows(results, non_empty_only=True)
    lines.extend(
        _table(
            ["field", "cases", "ok", "accuracy"],
            [[row["field"], str(row["cases"]), str(row["ok"]), row["accuracy"]] for row in rows],
        )
    )

    lines.append("")
    lines.append("== Accuracy theo kind ==")
    rows = kind_rows(results)
    lines.extend(
        _table(
            ["kind", "cases", "checks", "ok", "accuracy", "exact_cases"],
            [
                [
                    row["kind"],
                    str(row["cases"]),
                    str(row["checks"]),
                    str(row["ok"]),
                    row["accuracy"],
                    str(row["exact_cases"]),
                ]
                for row in rows
            ],
        )
    )

    lines.append("")
    lines.append("== doc_type / side nhận diện ==")
    rows = side_rows(results)
    lines.extend(
        _table(
            ["id", "kind", "doc_type", "side", "expected_side", "ok"],
            [
                [
                    row["id"],
                    row["kind"],
                    row["doc_type"],
                    row["side"],
                    row["expected_side"],
                    "yes" if row["side_ok"] else "NO",
                ]
                for row in rows
            ],
        )
    )
    mismatched = [row["id"] for row in rows if not row["side_ok"]]
    lines.append(f"side lệch: {', '.join(mismatched) if mismatched else 'không'}")

    failures = [
        (
            result["id"],
            f'{item["field"]}[{item["row_index"]}]' if "row_index" in item else item["field"],
            item["expected"],
            item["got"],
        )
        for result in results
        for item in result["fields"]
        if not item["ok"]
    ]
    lines.append("")
    lines.append(f"== Ca sai ({len(failures)}) ==")
    if failures:
        for case_id, field, expected, got in failures:
            lines.append(f'{case_id} {field} expected="{expected}" got="{got}"')
    else:
        lines.append("không")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Đo độ chính xác field của _normalize_native_ocr_doc trên bộ ca tổng hợp."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="file cases.json")
    parser.add_argument("--json", type=Path, default=None, help="ghi kết quả chi tiết ra file JSON")
    args = parser.parse_args(argv)

    cases_path = args.cases if args.cases.is_absolute() else Path.cwd() / args.cases
    if not cases_path.exists():
        parser.error(f"không thấy file cases: {cases_path}")
    with cases_path.open(encoding="utf-8") as handle:
        cases = json.load(handle)
    if not isinstance(cases, list) or not cases:
        parser.error(f"file cases phải là danh sách ca không rỗng: {cases_path}")

    results = evaluate(cases)
    print("\n".join(render(results, cases_path)))

    if args.json is not None:
        payload = {
            "cases_file": str(cases_path),
            "summary": summarize(results),
            "by_kind": kind_rows(results),
            "fields_all": field_rows(results, non_empty_only=False),
            "fields_non_empty": field_rows(results, non_empty_only=True),
            "cases": results,
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    return 1 if any(not item["ok"] for result in results for item in result["fields"]) else 0


if __name__ == "__main__":
    sys.exit(main())

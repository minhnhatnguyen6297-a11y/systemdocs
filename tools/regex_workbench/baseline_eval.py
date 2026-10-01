"""Đối chiếu engine trên đúng tập baseline 20 thư mục.

    python tools/regex_workbench/baseline_eval.py --results <results.json>

`--results` trỏ tới `results.json` của artifacts baseline
(`artifacts/g1-transfer-20-2026-09-28-direct/`): script đọc text đã trích
sẵn trong baseline, chạy lại bằng engine hiện tại và chỉ xuất TỔNG HỢP.

NGUYÊN TẮC PII: output chỉ gồm số đếm/tỉ lệ và rule_id — không raw text,
không tên đường dẫn, không giá trị trường, không tên người. Không ghi file.

Ground-truth limit: baseline chỉ có trạng thái đọc file + kết quả extractor
cũ, không có nhãn đúng tay cho từng trường — đối chiếu ở mức phân bố
(state/kind/errors) và coverage, không phải độ chính xác tuyệt đối.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import load_profile, run  # noqa: E402


def aggregate(rows: list[dict], profile: dict) -> dict:
    summary = {
        "files_total": len(rows),
        "readable": 0,
        "skipped": {},
        "doc_kind": collections.Counter(),
        "title_state": collections.Counter(),
        "zone_states": collections.defaultdict(collections.Counter),
        "field_states": collections.defaultdict(collections.Counter),
        "parties_state": collections.Counter(),
        "persons_per_doc": {"min": None, "max": None, "sum": 0},
        "files_with_errors": 0,
        "error_rules": collections.Counter(),
        "runtime_ms": {"sum": 0.0, "max": 0.0},
    }
    import time

    for row in rows:
        if row.get("status") != "ok":
            summary["skipped"][row.get("status", "?")] = (
                summary["skipped"].get(row.get("status", "?"), 0) + 1
            )
            continue
        summary["readable"] += 1
        t0 = time.monotonic()
        result = run(row.get("text", ""), profile)
        dt = (time.monotonic() - t0) * 1000.0
        summary["runtime_ms"]["sum"] += dt
        summary["runtime_ms"]["max"] = max(summary["runtime_ms"]["max"], round(dt, 1))

        summary["doc_kind"][result["doc_kind"]] += 1
        summary["title_state"][result["title"]["state"]] += 1
        for zone in result["zones"]:
            summary["zone_states"][zone["name"]][zone["state"]] += 1
        for field in result["fields"]:
            summary["field_states"][field["name"]][field["state"]] += 1
        parties = result["parties"]
        summary["parties_state"][parties["state"]] += 1
        n_persons = sum(len(b.get("persons", [])) for b in parties.get("blocks", []))
        p = summary["persons_per_doc"]
        p["sum"] += n_persons
        p["min"] = n_persons if p["min"] is None else min(p["min"], n_persons)
        p["max"] = n_persons if p["max"] is None else max(p["max"], n_persons)
        if result["errors"]:
            summary["files_with_errors"] += 1
            for err in result["errors"]:
                rule = err.split(":", 1)[0]
                summary["error_rules"][rule] += 1

    summary["skipped"] = dict(summary["skipped"])
    summary["doc_kind"] = dict(summary["doc_kind"])
    summary["title_state"] = dict(summary["title_state"])
    summary["zone_states"] = {k: dict(v) for k, v in summary["zone_states"].items()}
    summary["field_states"] = {k: dict(v) for k, v in summary["field_states"].items()}
    summary["parties_state"] = dict(summary["parties_state"])
    summary["error_rules"] = dict(summary["error_rules"])
    p = summary["persons_per_doc"]
    p["avg"] = round(p["sum"] / summary["readable"], 2) if summary["readable"] else 0
    del p["sum"]
    summary["runtime_ms"]["avg"] = (
        round(summary["runtime_ms"]["sum"] / summary["readable"], 1)
        if summary["readable"]
        else 0
    )
    del summary["runtime_ms"]["sum"]
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Baseline eval — aggregate only, no PII")
    parser.add_argument("--results", required=True, help="đường dẫn results.json của baseline")
    parser.add_argument("--profile", default="transfer")
    args = parser.parse_args()

    rows = json.loads(Path(args.results).read_text(encoding="utf-8"))
    profile = load_profile(args.profile)
    out = aggregate(rows, profile)
    out["profile"] = f"{profile.get('profile_id')} v{profile.get('version')}"
    out["note"] = (
        "aggregate only — no raw text/paths/values; ground truth chưa có nhãn đúng tay"
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

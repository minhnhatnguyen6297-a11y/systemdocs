"""Probe chạy engine trong TIẾN TRÌNH RIÊNG cho các test timeout.

Test suite gọi file này qua `subprocess.run(..., timeout=N)` — giới hạn ngoài
tiến trình bảo đảm suite không bao giờ treo ngay cả khi cơ chế timeout của
engine hỏng. Kết quả in ra stdout dạng JSON (ensure_ascii để tránh vấn đề
encoding console Windows).

    python _timeout_probe.py <mode> [fixture_path]

Modes:
    field_redos  -- field rule `(a|a)*b` (lọt lint tĩnh) trên fixture + trigger
    party_redos  -- side_markers chỉ còn pattern ReDoS, trigger nằm trong vùng parties
    zone_redos   -- start_markers của zone parties chỉ còn pattern ReDoS

Mỗi mode chạy 2 lượt: profile ReDoS rồi profile sạch — chứng minh engine hồi
phục và lần chạy hợp lệ tiếp theo vẫn thành công.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from engine import load_profile, run  # noqa: E402

REDOS_PATTERN = "(a|a)*b"  # nested qua alternation — _NESTED_QUANTIFIER không bắt được
TRIGGER = "a" * 60 + "cb"
TIMEOUT_MS = 200

PARTIES_DOC = (
    "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT\n"
    "BÊN A (BÊN CHUYỂN NHƯỢNG)\n"
    f"Ông Nguyễn Văn A; {TRIGGER}\n"
    "ĐIỀU 1. ĐỐI TƯỢNG CỦA HỢP ĐỒNG\n"
)


def _redos_profile() -> dict:
    profile = load_profile("transfer")
    profile["regex_timeout_ms"] = TIMEOUT_MS
    return profile


def main() -> None:
    mode = sys.argv[1]
    out: dict = {"mode": mode}

    if mode == "field_redos":
        fixture = Path(sys.argv[2]).read_text(encoding="utf-8")
        text = fixture + "\n" + TRIGGER + "\n"
        profile = _redos_profile()
        profile["fields"].append(
            {
                "rule_id": "test.redos_field",
                "name": "redos_probe",
                "zone": "any",
                "pattern": REDOS_PATTERN,
            }
        )
        out["first"] = run(text, profile)
        out["second"] = run(Path(sys.argv[2]).read_text(encoding="utf-8"), load_profile("transfer"))

    elif mode == "party_redos":
        profile = _redos_profile()
        profile["parties"]["side_markers"] = [
            {
                "rule_id": "test.redos_party",
                "side": "A",
                "role": "probe",
                "pattern": REDOS_PATTERN,
            }
        ]
        out["first"] = run(PARTIES_DOC, profile)
        out["second"] = run(PARTIES_DOC, load_profile("transfer"))

    elif mode == "zone_redos":
        profile = _redos_profile()
        for z in profile["zones"]:
            if z.get("zone_id") == "parties":
                z["start_markers"] = [REDOS_PATTERN]
        text = "HỢP ĐỒNG CHUYỂN NHƯỢNG\n" + TRIGGER + "\nĐIỀU 1.\n"
        out["first"] = run(text, profile)
        out["second"] = run(PARTIES_DOC, load_profile("transfer"))

    else:
        raise SystemExit(f"unknown mode {mode}")

    print(json.dumps(out, ensure_ascii=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""So sánh lỗi test thực tế với danh sách lỗi đã biết (quarantine).

- Lỗi MỚI (không có trong danh sách)  -> exit 1 (chặn CI).
- Lỗi đã biết                        -> chỉ cảnh báo, kèm issue ref.
- Lỗi đã biết nay PASS               -> cảnh báo "hãy xoá khỏi danh sách" (không chặn).

Không skip test nào: test vẫn chạy, chỉ đổi cách đánh giá kết quả.

Dùng:
  known_failures.py tap    <tap-output.txt>  <known-file>
  known_failures.py pytest <pytest -rA output>      <known-file>
Định dạng known-file: mỗi dòng `<test id>  # <issue ref> <lý do>`; dòng '#' là chú thích.
"""
import re
import sys


def load_known(path):
    known = {}
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        tid, _, note = line.partition("  #")
        known[tid.strip()] = note.strip()
    return known


def norm_js(name):
    # File-level failure: absolute path -> 'file:test/x.test.mjs'
    m = re.search(r"(?:^|/)shell/(test/[^/]+\.mjs)$", name)
    return f"file:{m.group(1)}" if m else name.strip()


def tap_failures(path):
    fails, passes = set(), set()
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"^\s*(not ok|ok) \d+ - (.*?)(\s+# (SKIP|TODO).*)?$", line)
        if not m:
            continue
        (fails if m.group(1) == "not ok" else passes).add(norm_js(m.group(2)))
    return fails, passes


def pytest_failures(path):
    """Đọc short summary của `pytest -rA` (PASSED/FAILED/ERROR <nodeid>)."""
    fails, passes = set(), set()
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"^(PASSED|FAILED|ERROR) (\S+)", line)
        if m:
            (passes if m.group(1) == "PASSED" else fails).add(m.group(2))
    return fails, passes


def main():
    kind, result, known_file = sys.argv[1:4]
    fails, passes = (tap_failures if kind == "tap" else pytest_failures)(result)
    known = load_known(known_file)
    new = sorted(fails - known.keys())
    still = sorted(fails & known.keys())
    fixed = sorted(passes & known.keys() - fails)
    gh = "::warning::"
    for t in still:
        print(f"{gh}KNOWN-FAIL {t}  ({known[t]})")
    for t in fixed:
        print(f"{gh}NOW-PASSING (xoá khỏi {known_file}): {t}")
    for t in new:
        print(f"::error::NEW-FAIL {t}")
    print(f"summary: fail={len(fails)} known={len(still)} new={len(new)} "
          f"fixed={len(fixed)} known_listed={len(known)}")
    if not fails and not passes:
        print("::error::không đọc được kết quả test nào (output rỗng?)")
        return 1
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())

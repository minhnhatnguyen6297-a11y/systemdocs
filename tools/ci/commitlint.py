"""Kiểm tra commit message theo docs/COMMIT.md (Conventional Commits rút gọn).

Dùng: python tools/ci/commitlint.py <base_sha> <head_sha>
      python tools/ci/commitlint.py --title "<PR title>"
Bỏ qua merge commit. Exit 1 nếu có commit sai chuẩn.
"""
import re
import subprocess
import sys

TYPES = "feat|fix|docs|test|refactor|perf|build|ci|chore|revert"
HEADER = re.compile(rf"^({TYPES})(\([a-z0-9._/-]+\))!?: \S.{{0,70}}$")
REF = re.compile(r"(#\d+|\bD-\d{3}\b|\bRefs?:)", re.I)


def check(msg: str) -> list[str]:
    lines = msg.strip().splitlines()
    head = lines[0] if lines else ""
    errs = []
    if not HEADER.match(head):
        errs.append(f"tiêu đề sai dạng '<type>(<scope>): <tóm tắt>' (≤72 ký tự): {head!r}")
    body = "\n".join(lines[1:]).strip()
    if not body:
        errs.append("thiếu body (cái gì / vì sao / tính năng)")
    elif not REF.search(msg):
        errs.append("thiếu tham chiếu issue (#123), D-xxx hoặc dòng 'Refs:'")
    return errs


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "--title":
        bad = [e for e in check(argv[1] + "\n\nRefs: -") if "tiêu đề" in e]
        for e in bad:
            print(f"PR title: {e}")
        return 1 if bad else 0
    base, head = argv
    shas = subprocess.run(["git", "rev-list", "--no-merges", f"{base}..{head}"],
                          capture_output=True, text=True, check=True).stdout.split()
    failed = 0
    for sha in shas:
        msg = subprocess.run(["git", "log", "-1", "--format=%B", sha],
                             capture_output=True, text=True, check=True).stdout
        errs = check(msg)
        if errs:
            failed += 1
            for e in errs:
                print(f"{sha[:8]}: {e}")
    print(f"commitlint: {len(shas)} commit, {failed} sai chuẩn")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

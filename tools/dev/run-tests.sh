#!/usr/bin/env bash
# Chạy đúng bộ test CI (js-unit + pytest) rồi so với tools/ci/known-failures-*.txt.
# Cần chạy tools/dev/setup-worktree.sh trước. Exit != 0 nếu có lỗi MỚI.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV="${SYSTEMDOCS_VENV:-$HOME/.cache/systemdocs/venv-py312}"
BASETEMP="${PYTEST_BASETEMP:-$HOME/workspace/tmp-pytest}"
OUT="${TEST_OUT:-$(mktemp -d)}"
mkdir -p "$OUT"
export PATH="$VENV/bin:$PATH"   # test JS gọi `python`/`python3`
cd "$ROOT"
(cd shell && node --test --test-reporter=tap test/*.test.mjs > "$OUT/js-test.tap" 2>&1)
python -m pytest shell/test notary_v2/tests -q -p no:cacheprovider -rA --basetemp "$BASETEMP" > "$OUT/pytest.txt" 2>&1
echo "== JS:";     grep -E '^# (tests|pass|fail|skipped)' "$OUT/js-test.tap"
echo "== pytest:"; tail -1 "$OUT/pytest.txt"
rc=0
python tools/ci/known_failures.py tap "$OUT/js-test.tap" tools/ci/known-failures-js.txt || rc=1
python tools/ci/known_failures.py pytest "$OUT/pytest.txt" tools/ci/known-failures-py-linux.txt || rc=1
echo "logs: $OUT"; exit $rc

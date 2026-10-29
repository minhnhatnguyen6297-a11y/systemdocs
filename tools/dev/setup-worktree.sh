#!/usr/bin/env bash
# Chuẩn bị môi trường test giống CI (.github/workflows/ci.yml) cho một worktree.
# - Python 3.12 venv dùng chung (mặc định ~/.cache/systemdocs/venv-py312), cài lại khi requirements đổi.
# - shell/node_modules qua `npm ci` (mỗi worktree một bản).
# Dùng: tools/dev/setup-worktree.sh [--no-npm]
# Sau đó: tools/dev/run-tests.sh   (pytest + node --test + so known-failures như CI)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV="${SYSTEMDOCS_VENV:-$HOME/.cache/systemdocs/venv-py312}"
PYVER="${SYSTEMDOCS_PYTHON:-3.12}"
REQS=("$ROOT/shell/sidecar/requirements.txt" "$ROOT/notary_v2/requirements.txt")

if [ ! -x "$VENV/bin/python" ]; then
  mkdir -p "$(dirname "$VENV")"
  if command -v uv >/dev/null; then uv venv -q --python "$PYVER" "$VENV"
  else "python$PYVER" -m venv "$VENV"; fi
fi
STAMP="$VENV/.reqs-sha"
SHA="$(cat "${REQS[@]}" | sha256sum | cut -d' ' -f1)"
if [ "$(cat "$STAMP" 2>/dev/null)" != "$SHA" ]; then
  if command -v uv >/dev/null; then
    uv pip install -q --python "$VENV/bin/python" -r "${REQS[0]}" -r "${REQS[1]}" pytest
  else
    "$VENV/bin/python" -m pip install -q -U pip
    "$VENV/bin/python" -m pip install -q -r "${REQS[0]}" -r "${REQS[1]}" pytest
  fi
  echo "$SHA" > "$STAMP"
fi
echo "python: $("$VENV/bin/python" --version) ($VENV)"

if [ "${1:-}" != "--no-npm" ]; then
  (cd "$ROOT/shell" && npm ci --no-audit --no-fund --loglevel=error)
  echo "node: $(node --version); shell/node_modules ready"
fi

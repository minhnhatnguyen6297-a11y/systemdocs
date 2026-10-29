#!/usr/bin/env bash
# Commit bằng vai trò commit của omp (`omp commit`), theo docs/COMMIT.md.
# Dùng: git add <files>; tools/dev/omp-commit.sh "<ngữ cảnh: vì sao, issue/D-xxx>" [--push]
# Model: `omp commit` dùng role `default` cho phân tích, role `smol` cho bước nhẹ
# (~/.omp/agent/config.yml modelRoles). Ghi đè: OMP_COMMIT_MODEL=<model>.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
CTX="${1:?cần ngữ cảnh: vì sao + issue/D-xxx}"; shift || true
ARGS=(--no-changelog -c "Tuân thủ chuẩn sau. Ngữ cảnh: $CTX

$(sed -n '/^## Dạng/,/^## Dùng mẫu/p' "$ROOT/docs/COMMIT.md")")
[ -n "${OMP_COMMIT_MODEL:-}" ] && ARGS+=(-m "$OMP_COMMIT_MODEL")
BEFORE="$(git rev-parse HEAD)"
omp commit "${ARGS[@]}" "$@" </dev/null
python3 "$ROOT/tools/ci/commitlint.py" "$BEFORE" HEAD

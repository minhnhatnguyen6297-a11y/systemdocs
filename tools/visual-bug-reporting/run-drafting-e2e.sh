#!/usr/bin/env bash
# One-command drafting E2E (Linux box): real sidecar, fresh temp DB per test.
# Usage: tools/visual-bug-reporting/run-drafting-e2e.sh [T1,T3,...]
set -u
cd "$(dirname "$0")/../.."
export G1_PYTHON="${G1_PYTHON:-/workspace/venv/bin/python}"
[ -n "${1:-}" ] && export E2E_ONLY="$1"
export E2E_OUT="${E2E_OUT:-/workspace/e2e-run/$(date +%Y%m%d-%H%M%S)}"
exec xvfb-run -a -s "-screen 0 1600x1000x24" node tools/visual-bug-reporting/drafting-e2e.cjs

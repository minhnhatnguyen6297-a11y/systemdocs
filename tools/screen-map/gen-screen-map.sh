#!/usr/bin/env bash
# Launch app (CDP, Xvfb, profile tạm) -> sinh docs/screen-map.yaml -> tắt app.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; UX_DIR="${UX_DIR:-/workspace/usability}"
export CDP_PORT="${CDP_PORT:-9566}"
export UX_PW="${UX_PW:-/workspace/venv2/lib/python3.13/site-packages/playwright/driver/package}"
REPO="$ROOT" CDP=1 "$UX_DIR/launch-app-cdp.sh"
trap '"$UX_DIR/stop-app-cdp.sh" >/dev/null 2>&1 || true' EXIT
sleep "${SETTLE_S:-5}"
node "$ROOT/tools/screen-map/gen-screen-map.cjs" > "$ROOT/docs/screen-map.yaml.tmp"
mv "$ROOT/docs/screen-map.yaml.tmp" "$ROOT/docs/screen-map.yaml"
echo "wrote docs/screen-map.yaml"

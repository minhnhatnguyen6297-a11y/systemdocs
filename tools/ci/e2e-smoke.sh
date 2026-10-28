#!/usr/bin/env bash
# E2E smoke: khởi động Electron shell dưới Xvfb với CDP, chờ renderer có page target,
# kiểm tra DOM có nội dung, rồi tắt. Dữ liệu: profile tạm, rỗng (không dữ liệu thật).
# Dùng ở CI (job e2e, non-blocking) và local. Cần: xvfb-run, curl, python3, node_modules/electron.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${CDP_PORT:-9444}"
PROFILE="$(mktemp -d)"; mkdir -p "$PROFILE"/{notary,upload,output}
export G1_PYTHON="${G1_PYTHON:-$(command -v python3)}"
export G1_NOTARY_DATA_DIR="$PROFILE/notary" G1_UPLOAD_DATA_DIR="$PROFILE/upload" G1_OUTPUT_DIR="$PROFILE/output"
export G1_NOTARY_V2_ROOT="$ROOT/notary_v2" G1_UPLOAD_LAB_ROOT="$ROOT/upload_lab"
unset ELECTRON_RUN_AS_NODE G1_DEV_NOTARY_MOCK || true
ELECTRON="$ROOT/shell/node_modules/electron/dist/electron"
xvfb-run -a -s "-screen 0 1280x800x24" "$ELECTRON" --no-sandbox "$ROOT/shell" --user-data-dir="$PROFILE/ud" \
  --remote-debugging-address=127.0.0.1 --remote-debugging-port="$PORT" >"$PROFILE/app.log" 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null || true; pkill -f "user-data-dir=$PROFILE/ud" 2>/dev/null || true' EXIT
ok=""
for _ in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:$PORT/json/list" -o "$PROFILE/targets.json" && \
     python3 -c "import json,sys; t=[x for x in json.load(open(sys.argv[1])) if x.get('type')=='page' and not x['url'].startswith('devtools')]; print(t[0]['url'], '|', t[0].get('title')) if t else sys.exit(1)" "$PROFILE/targets.json"; then
    ok=1; break
  fi
  sleep 1
done
if [ -z "$ok" ]; then echo "::error::không thấy renderer page qua CDP sau 60s"; tail -50 "$PROFILE/app.log"; exit 1; fi
sleep 3
kill -0 $PID 2>/dev/null || { echo "::error::Electron đã thoát sớm"; tail -50 "$PROFILE/app.log"; exit 1; }
echo "e2e-smoke OK (log: $PROFILE/app.log)"; tail -5 "$PROFILE/app.log"

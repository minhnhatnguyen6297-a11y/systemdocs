# g1-shell — Electron foundation + navigation (MIN-65 P4 / MIN-67 P5)

Runtime Electron + Python sidecar theo contract `desktopcommand.v1`
(`systemdocs/contracts/desktop-command.md`, branch `g1-single-machine-roadmap`).

## Layout

```text
shell/
  src/main/       Electron main: sidecar lifecycle, IPC allowlist, registry,
                command client (giu token), job tracker, diagnostics redaction
  src/preload/    contextBridge — chi expose desktop.v1.* da allowlist
  src/renderer/   UI thuan; sandbox + contextIsolation; CSP connect-src 'none'
                lib.js = display logic thuan (nav spec, status vocabulary,
                4 state faces) — node-test duoc; renderer.js = DOM app
  sidecar/        FastAPI desktopcommand.v1 producer (python app.py | exe)
  test/           node --test (main-side) + unittest (sidecar contract)
```

## Navigation (MIN-67 / spec MIN-32)

- Nav trai 7 muc: Tong quan, Upload/Audit, Ho so, Excel/Word, Van phong
  (placeholder "Chua trien khai"), Tim kiem, Trang thai/Cai dat.
- Moi module view la DOM subtree persistent: chuyen module khong mat
  file da chon/job/scroll (SM-07); job tiep tuc o sidecar + tracker.
- 4 mat trang thai dung chung: loading / empty / error / unavailable;
  `waiting_user` hien banner + CTA trong module (khong phai loi).
- Cancel co confirm dialog, chi o accepted/running/waiting_user, khong
  trigger Finalize. Retry tao command_id moi (khong duplicate).
- Tong quan: connection, version, module health, job that. Trang thai/Cai
  dat: diagnostics (env check qua `diag.env_check`, version, log da redact).
- Dong app khi con job chay → confirm (engine_shutdown se cancel job).
- Renderer reload khong mat job: `desktop.v1.listJobs` noi lai snapshot.

## Dev

```powershell
# python can fastapi/uvicorn/python-docx/PyMuPDF (xem sidecar/requirements.txt)
$env:G1_PYTHON = "<venv>/Scripts/python.exe"   # neu python PATH thieu deps
npm install          # mang cham: $env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
npm start
```

## Test

```powershell
npm test                                # redact, ipc allowlist, command client
& $env:G1_PYTHON test/test_sidecar_contract.py   # contract conformance (uvicorn that)
```

## Package

```powershell
$env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
$env:ELECTRON_BUILDER_BINARIES_MIRROR="https://npmmirror.com/mirrors/electron-builder-binaries/"
npm run build:sidecar   # -> sidecar/dist/g1-shell-sidecar/
npm run dist            # -> dist-app/win-unpacked/g1-shell.exe
```

Packaged smoke (khong can terminal tuong tac):

```powershell
$env:G1_SMOKE="1"; $env:G1_SMOKE_LOG="$PWD/smoke.json"
./dist-app/win-unpacked/g1-shell.exe   # tu thoat; xem smoke.json
```

## Boundary

- Renderer khong Node/fetch sidecar — moi call qua `window.desktop.v1`.
- Token + port sidecar chi trong Electron main (env, memory).
- File vao engine chi qua `desktop.v1.pickFiles` → file_ref `machine_local`.
- Sidecar bind `127.0.0.1`, Bearer auth moi endpoint tru `/healthz`, khong CORS.
- `diag.*` la command chan doan (progress/cancel/waiting/env), khong phai
  nghiep vu. Navigation ngoai `NAV_SPEC` bi tu choi; shell khong mo app
  legacy ben ngoai.

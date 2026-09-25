# g1-shell — Electron + nghiep vu that (MIN-65/67/68/69)

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

## Business modules (MIN-68 notary_v2 / MIN-69 upload_lab)

Sidecar import engine that tu repo con qua `sys.path` theo engine root —
khong port nghiep vu sang sidecar. Root resolve: env
`G1_NOTARY_V2_ROOT`/`G1_UPLOAD_LAB_ROOT` hoac `shell/engine-roots.json`
(gitignored, xem `engine-roots.example.json`).

- `notary_adapter.py` — case/customer/property/participant qua models +
  router handlers that (inline-create giu upsert/dedup/locked-case rule);
  `export_word` qua `services.word_engine` (template resolve, mapping,
  unresolved-placeholder check) ghi vao `G1_OUTPUT_DIR` (sidecar so huu,
  mac dinh `<shell>/output`, Electron dat ve `%APPDATA%/g1-shell/output`);
  `ocr.analyze` goi `routers/ocr_ai.analyze_images` that (cloud Qwen,
  ket qua luon `observed` — chua confirm khong thanh truth); `zalo.status`
  doc trang thai connector tu models (Zalo van server-side).
- `upload_adapter.py` + `upload_session.py` — `upload.scan` qua
  `batch_scan.run_batch_scan` (registry.sqlite3 dedup theo file_identity_key),
  `upload.audit_excel` qua `contract_book_audit` (cot MIN-77: STT | Ngay |
  So cong chung | Ghi chu), `upload.env_check` qua `environment_check_service`,
  va phien browser: `NamDinhUploaderSession` song tren thread chuyen biet
  `g1-upload-browser` (sync Playwright) — `session_start` → `waiting_user(login)`
  cho nguoi dung xac nhan, `prepare` chi mo tab da dien (dry-run, khong tu
  Finalize) → `waiting_user(review)` toi `finish_review`; `download_export`
  tai so Excel tu web tinh. Credential/storage state khong qua contract.
- IPC moi: `desktop.v1.openPath` (mo file san pham .docx bang app mac dinh,
  path validate tuyet doi + file ton tai + khong UNC) va `pickFiles` ho tro
  `directory: true` cho upload.scan.

## Dev

```powershell
# python can fastapi/uvicorn/python-docx/PyMuPDF (xem sidecar/requirements.txt)
$env:G1_PYTHON = "<venv>/Scripts/python.exe"   # neu python PATH thieu deps
npm install          # mang cham: $env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
npm start
```

## Test

```powershell
npm test                                # redact, ipc allowlist, command client, job tracker
& $env:G1_PYTHON test/test_sidecar_contract.py   # contract conformance (uvicorn that)
python test/test_jobstore.py            # jobstore cancel/drain
python test/test_upload_workflow.py     # v1 handlers scan/audit/queue
python test/test_upload_browser_workflow.py    # browser session + fake portal
python test/test_upload_recovery.py     # restart/reconcile/recovery
python test/test_engine_adapters.py     # engine that: case→Word, scan, audit
                                        #   (G1_NOTARY_DATA_DIR/G1_UPLOAD_DATA_DIR/G1_OUTPUT_DIR → tempdir)
```

## Package (MIN-69 T9)

```powershell
$env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
$env:ELECTRON_BUILDER_BINARIES_MIRROR="https://npmmirror.com/mirrors/electron-builder-binaries/"
$env:G1_PYTHON = "<venv>/Scripts/python.exe"   # venv can PyInstaller + deps engine
npm run build:sidecar   # PyInstaller onedir + stage engine/browsers
                      #   -> sidecar/dist/g1-shell-sidecar/
                      #   -> build/engine/{upload_lab,notary_v2}
                      #   -> build/playwright-browsers/chromium-*
npm run dist            # electron-builder dir -> dist-app/win-unpacked/g1-shell.exe
```

Deps dong goi vao exe duoc PIN trong `sidecar/requirements-package.txt`
(version theo build venv da kiem chung). `build_sidecar.ps1`/
`test/build-upload-test.ps1` chay `sidecar/check_package_deps.py` truoc
PyInstaller — venv sai version thi fail som (`pip install -r
sidecar/requirements-package.txt` de tao venv dung pin).

Layout trong goi:

```text
resources/sidecar/g1-shell-sidecar/     frozen Python sidecar (khong Qt)
resources/engine/{upload_lab,notary_v2} source engine (read-only)
resources/playwright-browsers/          Chromium pin revision
```

Runtime env do main.js dat: `G1_ENGINE_DIR=<resources>/engine`,
`PLAYWRIGHT_BROWSERS_PATH=<resources>/playwright-browsers`,
`G1_UPLOAD_DATA_DIR=<userData>/upload_lab`,
`G1_NOTARY_DATA_DIR=<userData>/engine-data/notary_v2`,
`G1_OUTPUT_DIR=<userData>/output`. Bundled engine root la read-only —
data/output luon ghi duoi userData, khong bao gio ghi vao thu muc cai dat.

Test build (fixture-only, tach userData):

```powershell
npm run dist:test   # -> dist-test/win-unpacked/g1-shell-test.exe
                    #    appId dev.g1.shell.test, marker
                    #    resources/test-pkg/test-build.json
```

Marker `test-pkg/test-build.json` → `G1_BUILD_LABEL=test`, app/userData
ten rieng, seam E2E (`G1_E2E_PICK_FILES`, `G1_E2E_OPEN_LOG`,
`G1_E2E_FIXTURE` → fixture portals) duoc phep. Production khong ship
marker + `e2e_fixture_hook.py` → seam la no-op, chi `nam_dinh` trong
catalog, `diag.fixture_browser_launch` = `command_unknown`.

Verify goi (khong can portal that):

```powershell
# probe frozen sidecar truc tiep (healthz + engine command + prod guard)
& $env:G1_PYTHON test/probe_frozen_sidecar.py `
    dist-app/win-unpacked/resources/sidecar/g1-shell-sidecar/g1-shell-sidecar.exe

# production offline: catalog that, khong fixture, ghi userData, ACL deny-write
& $env:G1_PYTHON test/test_upload_e2e.py --app dist-app/win-unpacked/g1-shell.exe --case offline

# test package full: audit + Chromium bundle + upload + recovery
& $env:G1_PYTHON test/test_upload_e2e.py --app dist-test/win-unpacked/g1-shell-test.exe --case all
```

`--case offline` bat buoc goi production (tu choi test marker);
`audit`/`upload`/`all` bat buoc build test (tu choi production).

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

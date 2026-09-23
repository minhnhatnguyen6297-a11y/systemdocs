# G1-SM Compatibility Matrix — Windows một máy (MIN-75 local / SM-02 / P1)

**Ngày:** 14/09/2026 · **Goal:** MIN-56 (scope G1-SM) · **Issue:** MIN-75 (phần local)
**Máy kiểm chứng:** Windows 11 (10.0.26200), Node v25.9.0, Python 3.12.10/3.10,
Word 16.0, Playwright 1.62 + chromium-1208/1234 đã cache sẵn.

Mọi probe nằm ngoài các repo tại
`C:/Users/MINH/orca/workspaces/_scratch/g1-p1/` (probes/, sidecar/,
electron-smoke/, logs/, golden/). Golden fixtures trích từ
`upload_lab@ce05b52:poc/conversion_benchmark/golden/` (read-only, không checkout).
Không dữ liệu khách hàng, không gọi cloud OCR/Zalo/portal thật.

---

## 1. Ma trận capability

### C1 — Electron dev + package

```text
CAPABILITY: electron.dev_package
REAL OR MOCK: REAL
INPUT FIXTURE: electron-smoke app (main/preload/renderer sandboxed)
COMMAND: node_modules/.bin/electron . ; electron-builder --dir
EXPECTED: dev run + packaged win-unpacked
ACTUAL: electron v31.7.7 dev run OK; electron-builder 24.13.3 →
  dist-app/win-unpacked/g1-p1-smoke.exe (~85MB dir). Electron dist phải tải qua
  npmmirror (GitHub release ~32KB/s, timeout) — xem F1.
PASS/FAIL/BLOCKED: PASS
OWNER: systemdocs/electron-system-shell
FOLLOW-UP ISSUE: MIN-65 (foundation), NSIS installer test hoãn P7
```

### C2 — Python sidecar runtime + native deps đóng gói

```text
CAPABILITY: python.sidecar_packaged
REAL OR MOCK: REAL
INPUT FIXTURE: sidecar_app.py (FastAPI /healthz /engine/* /shutdown)
COMMAND: PyInstaller --onedir; run dist/g1p1-sidecar/g1p1-sidecar.exe
EXPECTED: exe chạy không cần Python cài sẵn
ACTUAL: 40MB onedir; healthz 200; engine/read IFilter+docx thật (xem C3);
  shutdown sạch. Build nặng hơn: notary-deps.exe 92MB chứa sqlalchemy 2.0.52,
  jinja2, celery, PyMuPDF, zxing-cpp, python-docx, openpyxl — healthz thực thi
  fitz tạo PDF (790B) + zxingcpp.read_barcodes + sqlite select 1 → OK.
PASS/FAIL/BLOCKED: PASS
OWNER: upload_lab + notary_v2 (sidecar)
FOLLOW-UP ISSUE: MIN-65; stack local OCR parked (torch/vietocr/cv2 ~GB) CHƯA
  đo — quyết định D0-3
```

### C3 — File formats: .doc IFilter / .docx / PDF / ảnh / Excel

```text
CAPABILITY: file.formats
REAL OR MOCK: REAL (engine thật extract_contract.py của upload_lab)
INPUT FIXTURE: GD-03.docx (35KB), GD-04.xlsx, GD-06.png, GD-01/02/07.pdf,
  GD-05.doc stub 13B, P1-real.doc (Word COM author, 25KB)
COMMAND: venv python probes/probe_formats.py → logs/formats.json
EXPECTED: đọc được; lỗi fixture hỏng phải catchable
ACTUAL:
  docx.read.engine        PASS  text 'Synthetic DOCX paragraph\nField | Value'
  docx.extract.pipeline   PASS  web_form{} với cong_chung_vien/thu_ky bóc được
  doc.ifilter.stub        PASS  OSError hr=0x8004170C — catchable, đúng kỳ vọng
  doc.ifilter.real        PASS  'HOP DONG CONG CHUNG THU NGHIEM SO 123/2026...'
                                (query.dll, KHÔNG cần Word lúc runtime)
  pdf.text.read           PASS  1 trang 19 ký tự (PyMuPDF)
  pdf.scan.read           PASS  1 trang 0 ký tự (scan — cần OCR, đúng kỳ vọng)
  pdf.broken.error        PASS  FileDataError catchable
  xlsx.read               PASS  sheets=['Synthetic']
  png.read                PASS  magic bytes đúng
PASS/FAIL/BLOCKED: PASS
OWNER: upload_lab (extract), notary_v2 (fitz)
FOLLOW-UP ISSUE: MIN-69; GD-05.doc là stub — cần fixture .doc thật lâu dài
  (tạo qua Word COM như P1-real.doc hoặc sample tổng hợp)
```

### C4 — Word export / open / download

```text
CAPABILITY: word.export_open_download
REAL OR MOCK: REAL (generate) / API-LEVEL (open, download)
INPUT FIXTURE: docx sinh bởi python-docx trong unicode probe + frozen exe
COMMAND: python-docx Document().save() trong PyInstaller exe;
  Electron shell.openPath / session.downloadItem (API chuẩn E31)
EXPECTED: tạo .docx hợp lệ; mở/tải qua Electron API
ACTUAL: python-docx tạo+đọc docx trong frozen exe (unicode probe C5 + C2).
  shell.openPath/downloadItem là API chuẩn — chưa gắn UI, test UX ở P5.
PASS/FAIL/BLOCKED: PASS (generate REAL; open/download = API chuẩn, verify UX ở P5)
OWNER: notary_v2 (word_engine), shell (dialog/download)
FOLLOW-UP ISSUE: MIN-68 export-word qua word_engine; P5 wiring save-dialog
```

### C5 — Unicode đường dẫn / tên file / nội dung

```text
CAPABILITY: fs.unicode
REAL OR MOCK: REAL
INPUT FIXTURE: thư mục 'Hồ Sơ Unicode Đường Dẫn Tiếng Việt' + file
  'tài liệu thử nghiệm 日本語.docx' + nội dung tiếng Việt đậm
COMMAND: docx.save() → ec.read_docx() qua đường dẫn unicode
EXPECTED: ghi+đọc không lỗi, nội dung nguyên vẹn
ACTUAL: PASS — 47 ký tự đọc lại nguyên vẹn qua path unicode (logs/formats.json)
PASS/FAIL/BLOCKED: PASS
OWNER: cả hai engine
FOLLOW-UP ISSUE: —
```

### C6 — Quyền đọc/ghi, file đang mở, path dài

```text
CAPABILITY: fs.perms_locked_longpath
REAL OR MOCK: REAL (ctypes CreateFileW)
INPUT FIXTURE: locked_test.txt giữ share=0; path 321 ký tự
COMMAND: CreateFileW share=0 → open() lần 2; mkdir >260 plain vs \\?\ prefix
EXPECTED: file khóa → PermissionError bắt được; path dài plain fail + prefix OK
ACTUAL: share=0 → open() thứ hai PermissionError (catchable) — khớp hành vi
  "file đang mở trong Word". LongPathsEnabled=0 trên máy này: plain >260 ký tự
  FileNotFoundError; \\?\ prefix OK (pathlen=321). F2.
PASS/FAIL/BLOCKED: PASS (kèm finding F2 — app phải dùng \\?\ hoặc manifest
  longPathAware)
OWNER: shell + engine
FOLLOW-UP ISSUE: MIN-64 (file reference machine scope) + manifest P4
```

### C7 — Chromium/Playwright + storage state

```text
CAPABILITY: playwright.chromium_headed_state
REAL OR MOCK: REAL (upload_lab venv playwright 1.62, chromium-1234 bundled)
INPUT FIXTURE: trang HTML local phục vụ http://127.0.0.1 (không portal thật)
COMMAND: .venv python probes/probe_playwright.py → logs/playwright.json
EXPECTED: launch headed; storage_state save→restore localStorage
ACTUAL: headed_launch PASS; storage_state file tạo; restore PASS
  ('p1_probe'='ok-123' trên context mới). Lưu ý: data: URL và file:// KHÔNG
  round-trip localStorage qua storage_state — phải dùng origin http/https
  (portal thật là https, không ảnh hưởng; F3 ghi nhận cho test tương lai).
PASS/FAIL/BLOCKED: PASS
OWNER: upload_lab (Playwright thread ownership giữ nguyên)
FOLLOW-UP ISSUE: MIN-69 + P4/P7: provisioning ms-playwright trên máy sạch —
  %LOCALAPPDATA%/ms-playwright hiện có sẵn trên máy này; máy mới cần
  'playwright install chromium' lần đầu hoặc bundle thư mục browser
  (~400MB) + PLAYWRIGHT_BROWSERS_PATH. CHƯA ĐO — follow-up bắt buộc.
```

### C8 — Helper lifecycle: start/health/restart/shutdown

```text
CAPABILITY: helper.lifecycle
REAL OR MOCK: REAL (node spawn dist/g1p1-sidecar.exe)
INPUT FIXTURE: probe_lifecycle.mjs
COMMAND: node probes/probe_lifecycle.mjs → logs/lifecycle.json
EXPECTED: cold start health; kill→restart pid mới; /shutdown exit 0;
  instance thứ 2 cùng port tự thoát (detectable)
ACTUAL: 4/4 PASS — cold_start_health; kill_and_restart (pid 13796→20340);
  graceful_shutdown exitCode=0; port_conflict exitCode=3
PASS/FAIL/BLOCKED: PASS
OWNER: shell (Electron main) sở hữu lifecycle helper
FOLLOW-UP ISSUE: MIN-65
```

### C9 — Packaged smoke gọi engine thật (gate bắt buộc)

```text
CAPABILITY: packaged.smoke_real_engine
REAL OR MOCK: REAL end-to-end
INPUT FIXTURE: dist-app/win-unpacked + extraResources sidecar/ + golden/
COMMAND: G1_SMOKE_AUTOQUIT=1 g1-p1-smoke.exe
EXPECTED: packaged exe spawn sidecar exe, /healthz, engine/read file thật,
  shutdown sạch
ACTUAL: spawn resources/sidecar/g1p1-sidecar.exe (pid 7532) → healthz 200 →
  engine/read resources/golden/GD-03.docx → 'Synthetic DOCX paragraph' →
  sidecar exit 0 → app quit. Log: dist-app/win-unpacked/resources/g1-p1-electron.log
PASS/FAIL/BLOCKED: PASS
OWNER: systemdocs/electron-system-shell
FOLLOW-UP ISSUE: MIN-65
```

### C10 — Node runtime cho zalo_connector (D0-2)

```text
CAPABILITY: helper.node_embedded
REAL OR MOCK: REAL
INPUT FIXTURE: ELECTRON_RUN_AS_NODE=1 trên electron.exe dev + packaged
COMMAND: electron.exe -e "process.version"
EXPECTED: Node chạy được bên trong packaged app → zalo_connector (zca-js)
  không cần cài Node riêng
ACTUAL: v20.18.0 cả dev lẫn win-unpacked exe
PASS/FAIL/BLOCKED: PASS
OWNER: notary_v2 zalo_connector (helper process)
FOLLOW-UP ISSUE: MIN-68; quyết ai spawn connector (main vs python sidecar) ở P4
```

## 2. Phân loại client / helper / server (một máy)

| Lớp | Process | Chứa | Không chứa |
|---|---|---|---|
| **Electron main** (client host) | electron.exe | window/nav, file dialog, download, IPC allowlist, spawn/kill helper, token sidecar | business logic, Playwright, OCR |
| **Renderer** (client UI) | sandboxed, no nodeIntegration | UI thuần, gọi qua preload IPC | Node API, token, business |
| **Python sidecar** (helper+server nội bộ, 127.0.0.1) | PyInstaller exe | engine: extract/scan/audit/word_engine/inheritance_engine/OCR/DB SQLite; sở hữu Playwright thread + Celery nếu cần | UI, dialog |
| **zalo_connector** (helper) | Node qua ELECTRON_RUN_AS_NODE | zca-js session, webhook nội bộ | UI |
| **Playwright Chromium** (helper con của sidecar) | chromium-1234 headed | automation web tỉnh; Python sở hữu lifecycle | — |

Không có server tách máy trong G1-SM. LAN/đa máy = G1-LAN deferred (MIN-76).

## 3. Findings & blocker

| # | Finding | Mức | Ảnh hưởng / hành động |
|---|---|---|---|
| F1 | GitHub release ~32KB/s (timeout 5 phút/9.7MB); npmmirror 3.2MB/s | Infra | Build cần `ELECTRON_MIRROR` + `ELECTRON_BUILDER_BINARIES_MIRROR` hoặc vendor binary — ghi vào hướng dẫn build P4/P7 |
| F2 | `LongPathsEnabled=0` (mặc định OS): path >260 fail trừ khi `\\?\` | App | Manifest `longPathAware` (Electron hỗ trợ) + engine dùng prefix khi cần — spec vào MIN-64/P2 |
| F3 | `data:`/`file://` không persist localStorage qua storage_state | Test | Chỉ test storage trên origin http(s) — đúng thực tế portal https |
| F4 | Renderer thiếu CSP → Electron cảnh báo security | App | Thêm CSP meta ở P4; không chặn |
| F5 | ms-playwright browsers chỉ có sẵn ở %LOCALAPPDATA% máy này | Package | Máy sạch cần provision browser (~400MB) hoặc bundle + PLAYWRIGHT_BROWSERS_PATH — **chưa đo, follow-up bắt buộc P4/P7** |
| F6 | Stack local OCR parked (torch/vietocr/cv2 ~GB) chưa đo đóng gói | Quyết định | D0-3: P1 không chứng minh được kích thước — nếu owner muốn kèm local OCR, cần spike đóng gói riêng |
| F7 | GD-05.doc là stub 13B — không phải .doc thật | Fixture | Fixture .doc thật phải tự tạo (Word COM đã chứng minh đường này) |
| F8 | Zalo connector = Node service → dùng ELECTRON_RUN_AS_NODE embedded | Thiết kế | Ai spawn connector: Electron main hay Python sidecar — chốt ở P4 |

**Không có hard blocker cho P2-P6.** Cả hai engine đọc được định dạng nghiệp vụ,
Python sidecar đóng gói được, Electron đóng gói + gọi engine thật được, helper
lifecycle đầy đủ, Playwright + storage state hoạt động.

## 4. Log & artifact

- `logs/formats.json`, `logs/playwright.json`, `logs/lifecycle.json` — kết quả máy
- `dist/g1p1-sidecar/` (40MB), `dist/notary-deps/` (92MB) — exe sidecar đóng gói
- `electron-smoke/dist-app/win-unpacked/` + `resources/g1-p1-electron.log` — packaged app + log smoke
- `golden/` — fixture trích từ `upload_lab@ce05b52` + `P1-real.doc` tạo bằng Word COM
- Tất cả ở `C:/Users/MINH/orca/workspaces/_scratch/g1-p1/` — ngoài repo, throwaway

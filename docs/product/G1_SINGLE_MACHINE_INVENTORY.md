# G1-SM Inventory — Baseline khóa cho Electron một máy (MIN-74 / SM-01)

**Ngày:** 14/09/2026 · **Goal:** MIN-56 (scope G1-SM một máy) · **Issue:** MIN-74
**Trạng thái:** D0 đã duyệt một phần (owner 14/09/2026) — xem mục 8. Còn các mục
mở nhỏ không chặn P1.

**Quyết định owner đã chốt:**

- **D0-1 → B:** nguồn migrate `notary_v2` = **`codex/zalo-document-inbox-v2` @
  `d350048`** (không phải main `9a9bf9a`). Đã kiểm chứng `d350048` là superset
  code của `inheritance-diagram-v2` cho mọi file lõi (`services/word_engine.py`,
  `services/inheritance_engine.py`, `routers/cases.py`, `form.html`,
  `diagram_*.js`, `routers/ocr_local.py` — `git diff` identical). `d350048`
  thêm Zalo Inbox mở rộng + gỡ `parse_cccd_qr` phía server (khớp test
  `no_document_qr`). `inheritance-diagram-v2` @`14fb368` giữ spec docs phong
  phú hơn (`docs/domains/inheritance/spec.md` +625 dòng, spec/plan markitdown) —
  dùng làm normative reference cho P6-B; POC markitdown vẫn nằm trên `664edb4`.
- **D0-2 → Có:** Zalo Inbox nằm trong G1-SM (6 bảng DB Zalo + `zalo_connector`
  Node `zca-js`; connector lifecycle thuộc helper boundary; credential qua
  secrets, không hardcode).
- **D0-6 → tự động theo D0-1:** trên `d350048` các route `export-word-legacy`,
  `live-preview`, `export-draft`, `preview`, `export-preview` đã bị xóa (0 match
  trong `routers/cases.py`); chỉ còn `/{cid}/export-word` qua `word_engine` —
  không cần migrate luồng preview cũ.

Bản inventory này là read-only audit. Mọi claim về repo con có nguồn
`repo@sha:path:line`. Không chức năng nào bị bỏ ngầm: mục mơ hồ được ghi vào
mục 8 ("Cần owner quyết") thay vì tự gắn `NGOÀI PHẠM VI`.

Tag quyết định: `CHUYỂN UI` = chuyển sang shell Electron · `GIỮ PYTHON ENGINE` =
giữ engine/helper Python · `NGOÀI PHẠM VI` = ngoài G1-SM · `⚠ CẦN OWNER` = không
tự quyết.

---

## 1. Revision đã khóa (đối chiếu với bảng bàn giao)

Fetch remote ngày 14/09/2026, **không merge**. Tất cả SHA khớp bảng bàn giao.

| Repo | Branch/ref | SHA bàn giao | SHA hiện tại | Merge-base với main | Vai trò |
|---|---|---:|---:|---|---|
| `systemdocs` | `origin/electron-system-shell` | `aea764a` | `aea764a` ✓ | — | Nhánh tích hợp shell; worktree này (`g1-single-machine-roadmap` @ `965bb73`) dựng trên nó |
| `notary_v2` | `origin/main` | `9a9bf9a` | `9a9bf9a` ✓ | — | Baseline production hiện hành |
| `notary_v2` | `origin/codex/inheritance-diagram-v2` | `14fb368` | `14fb368` ✓ | `1192154` | Nhánh dev chính: Case Workspace v2 + word_engine/inheritance_engine/zalo_inbox (bản sớm) |
| `notary_v2` | `origin/codex/ocr-stage-pool-diagram-v1` | `a800406` | `a800406` ✓ | `42c88b3` | Snapshot bảo toàn workspace Stage/Pool cũ; **xóa stack local OCR** so với base |
| `notary_v2` | `origin/codex/zalo-document-inbox-v2` | `d350048` | `d350048` ✓ | `1192154` | = inheritance-diagram-v2 + Zalo Inbox mở rộng mạnh (+6.9k dòng, 6 bảng DB Zalo, connector Node đầy đủ) |
| `notary_v2` | `origin/codex/markitdown-qwen-poc` | `664edb4` | `664edb4` ✓ | `1192154` | = inheritance-diagram-v2 + `tools/document_conversion_poc/` |
| `upload_lab` | `origin/main` | `a4349a2` | `a4349a2` ✓ | — | Baseline production hiện hành |
| `upload_lab` | `origin/codex/desktop-command-poc` | `f18a42f` | `f18a42f` ✓ | `a4349a2` | POC Electron 31 + FastAPI sidecar + UploadWorker bridge |
| `upload_lab` | `origin/min-52-conversion-benchmark` | `ce05b52` | `ce05b52` ✓ | `a4349a2` | POC conversion benchmark + golden dataset GD-01..GD-07 |
| `notaryoffice` | `origin/main` / `origin/min-54-evidence-spec` | `1c1b160` / `c744975` | khớp ✓ | — | Chỉ tài liệu; local `D:/notaryoffice` main chưa có commit, toàn untracked docs |

Remote refs khác tồn tại nhưng **không cần cho G1-SM** (đã kiểm tra diff):
`systemdocs`: `min-56-architecture-convergence`, `min-61-conversion-decision`,
`min-62-data-contract-draft`, `min-63-database-spec-draft`, `min-64-ui-spec-draft`,
`min-66-merge-readiness-draft` (draft spec branches). `upload_lab`:
`feat/fluent-ui-redesign` (`f4fe560`, diff rỗng — đã merge), `codex/qt-workflow-redesign`
(`3339b27`, đã chứa trong main), `codex/ui-regex-rebuild` (`0318393`, đã chứa trong main),
`legacy/old-main` (`0a9ca02`, chỉ +35 dòng docs cũ).

Trạng thái checkout hiện có: `D:/notary_v2` (main, `M memory-bank/CURRENT.md` chưa
commit — **không phải thay đổi của task này**); `D:/upload_lab_repo` (main, sạch);
worktree audit riêng ở `C:/Users/MINH/orca/workspaces/{notary_v2/g1-notary-audit-devin,
upload_lab_repo/g1-upload-audit-devin, systemdocs/g1-single-machine-roadmap}`.

Thư mục cũ trên máy (bảo toàn, không phải nguồn migrate): `D:/notary_app`
(app notary đời cũ), `D:/upload_lab` (bản copy thứ hai của upload_lab),
`D:/notary_v2_old_20260914-1`, `D:/systemdocs_old_20260914-1`.

---

## 2. `notary_v2` @ `9a9bf9a` (main) — inventory

App FastAPI + Jinja server-rendered (`main.py:55-111`). Không có SPA; diagram
dùng ReactFlow UMD vendor (`frontend/static/vendor/`, xóa trên các nhánh codex).

### 2.1 Màn hình (Jinja template → route)

| Màn hình | Route / file | Tag | Owner | Source | Baseline test | Issue nhận |
|---|---|---|---|---|---|---|
| Trang chủ (stat cards + nav) | `GET /` → `home.html` | CHUYỂN UI | notary_v2 | `notary_v2@9a9bf9a:main.py:109-111; frontend/templates/home.html` | `tests/test_docs_structure.py` (docs only) | MIN-68 |
| Danh sách/tạo/sửa/xóa Khách hàng | `GET/POST /customers*` → `customers/{list,form,detail,upload_result}.html` | CHUYỂN UI | notary_v2 | `routers/customers.py:196,418,550,586,594,613,657` | `tests/test_customers_excel.py` | MIN-68 |
| Tìm khách hàng (API) | `GET /customers/api/search` | GIỮ PYTHON ENGINE (HTTP API) | notary_v2 | `routers/customers.py:205` | — | MIN-68 |
| Import khách hàng từ Excel (+ save từng dòng) | `GET download-template`, `POST upload-excel`, `POST upload-excel/save-row` | CHUYỂN UI + GIỮ ENGINE | notary_v2 | `routers/customers.py:221,255,387` | `tests/test_customers_excel.py` (371 dòng) | MIN-68 |
| Tạo nhanh khách hàng inline | `POST /customers/inline-create`; `POST /{cid}/quick-update` | GIỮ PYTHON ENGINE | notary_v2 | `routers/customers.py:426,498` | `test_customers_excel.py` | MIN-68 |
| Danh sách/tạo/sửa/xóa Tài sản (GCN) | `GET/POST /properties*` → `properties/{list,form,detail}.html` | CHUYỂN UI | notary_v2 | `routers/properties.py:25,37,144,215,222,246,313` | — | MIN-68 |
| Tạo nhanh tài sản inline | `POST /properties/inline-create` | GIỮ PYTHON ENGINE | notary_v2 | `routers/properties.py:49` | — | MIN-68 |
| Danh sách/tạo/sửa/khóa/xóa Hồ sơ thừa kế | `GET/POST /cases*` → `cases/{list,form,detail}.html`; lock/unlock/delete | CHUYỂN UI | notary_v2 | `routers/cases.py:422,431,457,573,587,628,740,749,758` | `tests/test_diagram_payload_parser.py`, `cases_ui_dataflow_static.test.mjs` | MIN-68 |
| **Case form = Case Workspace** (Stage/Pool/Diagram + OCR modal + nháp inline) — file 13.837 dòng | `cases/form.html` + `case_state_json`/`engine_state_json` qua form POST | CHUYỂN UI (lớn nhất của repo) | notary_v2 | `routers/cases.py:469-518,640-686`; `frontend/templates/cases/form.html` (~200 hàm JS); `frontend/static/{diagram_state,diagram_edges,inheritance_engine}.js`, `ReactFlowApp.jsx` | `diagram_state.test.mjs`, `diagram_inheritance_engine.test.mjs`, `cases_ui_dataflow_static.test.mjs` | MIN-68 |
| Quản lý mẫu Word (upload/kích hoạt/xóa) | `cases/templates*` → `cases/templates.html`; API `/templates/*` | CHUYỂN UI | notary_v2 | `routers/cases.py:789,806,817,853,864,892,929,940` | — | MIN-68 |
| Xuất Word hồ sơ | `GET /cases/{cid}/export-word-legacy`, `GET /cases/{cid}/export-word` (python-docx inline) | GIỮ PYTHON ENGINE (gọi qua helper), UI = nút/điểm tải | notary_v2 | `routers/cases.py:1304,1398` | — | MIN-68 |
| Live preview + export nháp/preview (htmldocx) | `POST /cases/live-preview`, `POST /cases/export-draft`, `GET /{cid}/preview`, `POST /{cid}/export-preview` | CHUYỂN UI + GIỮ ENGINE | notary_v2 | `routers/cases.py:1454,1574,1600,1635` | — | MIN-68 |
| Thêm/sửa/xóa đương sự | `POST /participants/*` | GIỮ PYTHON ENGINE | notary_v2 | `routers/participants.py:12,43,64` | — | MIN-68 |
| Stats | `GET /api/stats` | GIỮ PYTHON ENGINE | notary_v2 | `main.py:114-128` | — | MIN-68 |
| Xem trước văn bản cũ | `cases/preview.html`, `_document_template.html` | ⚠ CẦN OWNER (xóa trên nhánh codex — luồng cũ) | notary_v2 | `frontend/templates/cases/preview.html`, `_document_template.html` | — | MIN-68 |

### 2.2 OCR & intake (cloud Qwen)

| Chức năng | Route | Tag | Owner | Source | Baseline test | Issue nhận |
|---|---|---|---|---|---|---|
| OCR ảnh giấy tờ (CCCD, khai tử) qua DashScope native | `POST /api/ocr/analyze` | GIỮ PYTHON ENGINE | notary_v2 | `routers/ocr_ai.py:2471`; native call `:381-414` | `tests/test_ocr_ai.py` (44 tests, mock cloud) | MIN-68 |
| OCR sổ đỏ / pair trang | `POST /api/ocr/analyze-property`, `/analyze-property-pair` | GIỮ PYTHON ENGINE | notary_v2 | `routers/ocr_ai.py:2580,2689` | `test_ocr_ai.py` | MIN-68 |
| Cấu hình OCR cho client | `GET /api/ocr/config` | GIỮ PYTHON ENGINE | notary_v2 | `routers/ocr_ai.py:2814` | `test_ocr_ai.py` | MIN-68 |
| QR trên giấy tờ (web worker jsQR qua **CDN**) | `frontend/static/ocr_qr_worker.js` (+ `zxing-cpp` phía server trong `ocr_local.py:50-52,150-156`) | ⚠ CẦN OWNER — worker tải script từ `cdn.jsdelivr.net`, xem mục 7 | notary_v2 | `frontend/static/ocr_qr_worker.js:2`; `routers/ocr_local.py:150` | — | MIN-68/MIN-75 |
| **Local OCR (parked)**: submit/batch/status/confirm-save + warmup lúc boot | `POST /api/ocr/local/*`; `main.py:43-51` | ⚠ CẦN OWNER — giữ hiển thị "không khả dụng" hay ẩn; stack đang parked | notary_v2 | `routers/ocr_local.py:2567,2578,2620,2677,2694` | `tests/test_ocr_local_v4.py` (đỏ nếu thiếu stack) | MIN-68 |
| OCR job nền Celery | `tasks.py` + `celery_app.py` | GIỮ PYTHON ENGINE | notary_v2 | `celery_app.py:5-11`; `tasks.py` | — | MIN-68 |

### 2.3 Job / DB / quyền hệ thống

| Hạng mục | Chi tiết | Source |
|---|---|---|
| DB nghiệp vụ | SQLite `notary.db`: `customers`, `properties`, `inheritance_cases`, `inheritance_case_properties`, `inheritance_participants`, `word_templates`, `ocr_jobs`, `extracted_documents` | `models.py:8-183`; `database.py:8-9` |
| Broker/result Celery | `ocr_jobs.db` (hạ tầng, không phải DB nghiệp vụ) | `celery_app.py:5-6` |
| Schema migration lúc boot | 4 hàm migrate chạy trước `create_all` | `main.py:29-34`; `database.py:16-115` |
| Template Word đóng gói + upload | `word_templates/*.docx` (tracked) + `word_templates/custom/` | `routers/cases.py:22,780-806` |
| **UNC path hardcode** | `\\maychu\D\Minh\HỒ SƠ UBND CÁC XÃ\2. Mẫu thừa kế\xã_PCDS -.docx` trong template fallback — giả định share mạng/LAN | `routers/cases.py:780` |
| Quyền hệ thống cần | ghi `notary.db`, `ocr_jobs.db`, `tmp/ocr`, `logs/`, `word_templates/custom/`; đọc ảnh/PDF người dùng chọn | `run.bat` §6-7; `.gitignore` |
| Process | uvicorn `:8000` + Celery worker solo + (run.bat cài stack local OCR) | `run.bat` |
| Fixture nhạy cảm trong git | `ID template/{1,2,5,6}.jpg` **được track trên main** (~150KB/file); xóa trên nhánh zalo | `git ls-tree origin/main` |

### 2.4 Công cụ độc lập & test trên main

| Mục | Tag | Source | Baseline |
|---|---|---|---|
| Fast text audit (CLI, soát Word vs scan OCR) | ⚠ CẦN OWNER — CLI hay surface Electron? | `services/fast_audit/*`; `tools/run_fast_audit.py` | `test_fast_audit_*.py` (4 file, 36 tests theo memory-bank) |
| `tools/codex_relay.py`, `fix_mojibake_utf8.py` | NGOÀI PHẠM VI (dev tooling) | `tools/` | — |
| `test_ocr_local.py` ở root | NGOÀI PHẠM VI — script chẩn đoán thủ công, cần `ocr test/` (gitignored) | `test_ocr_local.py` | không chạy trong suite |
| `.bat` VPS/deploy (`connect_vps.bat`, `install_vps.sh`, `launch_vps_app.bat`, `view_vps_logs.bat`) | ⚠ CẦN OWNER — deploy VPS ngoài goal một máy, giữ nguyên không xóa | repo root | — |
| `ID template/` (4 ảnh tracked) | ⚠ CẦN OWNER — dữ liệu định danh thật? xem mục 7 | `git ls-tree` | — |

### 2.5 Code/test/fixture CHỈ có trên nhánh chưa merge

Ba nhánh base `1192154` (`inheritance-diagram-v2`, `zalo-document-inbox-v2`,
`markitdown-qwen-poc`) chứa "thế giới v2" **không có trên main**:

| Hạng mục | Nhánh | Source |
|---|---|---|
| `services/word_engine.py`, `services/inheritance_engine.py` (Word/engine Python tách khỏi router) | cả 3 | `git diff main...branch` |
| `services/zalo_inbox.py`, `routers/zalo_inbox.py` (`/zalo-inbox/*`: connector onboard/start, webhook, batches, outputs, confirm, download) + `frontend/templates/zalo_inbox.html` + `frontend/static/js/zalo_inbox.js` | cả 3; zalo branch lớn nhất | `routers/zalo_inbox.py:351-843` trên `d350048` |
| `zalo_connector/` (Node `zca-js` service: `src/connector.mjs` 949 dòng bản zalo / 344 bản diagram; `bin/run.mjs`; tests) | cả 3 | `zalo_connector/` trên `d350048`/`14fb368` |
| 6 bảng Zalo: `zalo_connector_accounts`, `zalo_sources`, `zalo_media`, `zalo_message_texts`, `zalo_data_sync_runs`, `zalo_batches` | cả 3 | `models.py:186-300` trên `d350048` |
| `scripts/ensure_zalo_env.py` | zalo | `d350048` |
| `tools/document_conversion_poc/` + `requirements-poc-markitdown.txt` + golden manifest | markitdown | `664edb4` |
| Test mới: `test_word_engine.py`, `test_inheritance_engine.py`, `test_inheritance_research_catalog.py`, `test_zalo_env_setup.py`, `test_zalo_inbox.py`, `test_zalo_inbox_api.py`, `cases_word_export_static.test.mjs`, `diagram_edges.test.mjs`, `zalo_inbox_ui_static.test.mjs`, `test_document_conversion_poc.py`; fixture `tests/fixtures/inheritance_research_cases.json` | theo nhánh | `git diff --name-status main...branch -- tests/` |
| Xóa so với main: `preview.html`, `macros.html`, `_document_template.html`, `inheritance_engine.js`, vendor ReactFlow/dagre | cả 3 (luồng case cũ bị thay bởi v2) | `git diff main...branch` |

Nhánh `codex/ocr-stage-pool-diagram-v1` (base `42c88b3`): **xóa toàn bộ stack
local OCR** (`routers/ocr_local.py`, `celery_app.py`, `tasks.py`,
`ocr_qr_worker.js`, `requirements-local-ocr.txt`, `test_ocr_local*.py`) và sửa
`form.html`/diagram — đây là snapshot workspace bảo toàn, không phải tính năng
mới cho migrate.

---

## 3. `upload_lab` @ `a4349a2` (main) — inventory

App desktop PySide6/Fluent (`ui_qt/`). **Không có HTTP server nào trên main** —
đã kiểm chứng bằng grep (`fastapi|uvicorn|flask|aiohttp|HTTPServer` → 0 hit
ngoài `.venv`/`tests`). UI↔engine đi in-process qua Qt signals + command queue.

### 3.1 Màn hình (4 mục navigation, `ui_qt/main_window.py`)

| Màn hình | Vai trò | Tag | Owner | Source | Baseline test | Issue nhận |
|---|---|---|---|---|---|---|
| "Audit Sổ Công Chứng" (excelTab) | Tải/nạp sổ Excel từ web tỉnh, đối chiếu, phát hiện số hở | CHUYỂN UI | upload_lab | `main_window.py:142-144,164-339`; `ui/services/contract_book_audit.py`, `web_list_service.py` | `test_contract_book_audit.py` (8), `test_web_list_service.py` (4) | MIN-69 |
| "Quét & Upload Hồ Sơ" (folderTab) | Chọn folder → scan/extract → bảng kết quả → chọn → prefill | CHUYỂN UI | upload_lab | `main_window.py:148-150,340-520`; `ui/services/folder_workflow_service.py`, `scan_classification_service.py`, `upload_selection_service.py` | `test_upload_batch_scan.py` (14), `test_scan_classification_service.py` (6), `test_upload_selection_service.py` (6), `test_upload_lab_extract_contract.py` (18) | MIN-69 |
| "Cấu Hình & Hệ Thống" (regexTab) | Cấu hình URL/session, kiểm tra môi trường, mở đăng nhập | CHUYỂN UI | upload_lab | `main_window.py:154-156,521-577`; `ui/services/environment_check_service.py` | `test_environment_check_service.py` (11) | MIN-69 |
| "Nhật Ký Hệ Thống" (logsPage) | Log viewer | CHUYỂN UI | upload_lab | `main_window.py:160-162,578-606` | `test_qt_ui_structure.py` (19) | MIN-69 |

### 3.2 Engine / thao tác

| Chức năng | Tag | Source | Baseline test |
|---|---|---|---|
| Đọc `.docx` giữ thứ tự đoạn+bảng; đọc `.doc` qua Windows IFilter `query.dll` | GIỮ PYTHON ENGINE | `extract_contract.py:99-131,133-160,247-266` | `test_upload_lab_extract_contract.py` |
| Phân loại văn bản + bóc trường (6 doc_kind, regex label-anchor) | GIỮ PYTHON ENGINE | `extract_contract.py:526-780+`; `docs/regex-rules.md` | `test_upload_lab_extract_contract.py`, `test_regex_lab.py` (7), `test_regex_review_samples.py` (3) |
| Quét folder → manifest `runs/`, JSON `output/`, ghi `registry.sqlite3` | GIỮ PYTHON ENGINE | `batch_scan.py:106-282,353-371,432+`; `ui/services/folder_workflow_service.py` | `test_upload_batch_scan.py` |
| Trạng thái registry: `matched`, `extracted`, `prepared_dry_run`, `prepared_partial`, `uploaded_success`, `extract_failed`, `upload_failed`, `skipped_*` | GIỮ PYTHON ENGINE | `batch_scan.py:353-365,575,627,687,713,744,786`; `playwright_uploader.py:81-83` | `test_upload_batch_scan.py`, `test_playwright_uploader.py` (24) |
| Audit sổ Excel, chuẩn hóa `xxx/yyyy`, phát hiện số hở | GIỮ PYTHON ENGINE | `ui/services/contract_book_audit.py` | `test_contract_book_audit.py` |
| Playwright session: preflight → login tay → storage state → mở N tab → dry-run → detect `POST /api/hoso` → `uploaded_success` | GIỮ PYTHON ENGINE | `playwright_uploader.py:816+` (`NamDinhUploaderSession`); handshake: `docs/handoff-login-handshake.md` | `test_playwright_uploader.py` |
| Selectors web tỉnh | GIỮ PYTHON ENGINE | `uploader_selectors.py` (180 dòng) | — |
| Command queue `UploadWorker` (một Python thread sở hữu Playwright sync) | GIỮ PYTHON ENGINE — **điểm bám DesktopCommand** | `ui_qt/workers.py:57-238` (slots: prepare/start_login/preflight/confirm_login/download/refresh_options/reload_options/close) | `test_qt_ui_structure.py` |
| Env check (OS, quyền ghi, đĩa, deps, mạng/DNS, HTTPS, proxy) + redaction | GIỮ PYTHON ENGINE | `ui/services/environment_check_service.py:389-478` | `test_environment_check_service.py` |
| Regex lab CLI + review samples | ⚠ CẦN OWNER — công cụ dev, giữ CLI hay bỏ khỏi shell? | `regex_lab.py`, `review_regex_samples.py`, `regex_review_samples/` (input/reports rỗng trong repo) | `test_regex_lab.py`, `test_regex_review_samples.py` |
| Bootstrap/packaging: `run.bat`, `run_ui.bat`, `bootstrap_ui.py`, `ui_runner.py`, `build_standalone_release.ps1` → `_release/` | NGOÀI PHẠM VI (thay bằng Electron packaging; giữ làm entrypoint rollback) | repo root | — |

### 3.3 Job / DB / quyền hệ thống / config

| Hạng mục | Chi tiết | Source |
|---|---|---|
| DB | SQLite `registry.sqlite3` (bảng `file_registry` + cột `prepared_at`…) — gitignored | `batch_scan.py:106-143`; `.gitignore` |
| Output | `output/*.json`, `runs/<ts>.json`, `downloads/`, `upload_runs/`, `logs/` — gitignored | `.gitignore`; `README.md:27-31` |
| Session web tỉnh | `nd_storage_state.json` (token local storage — **secret-like**, gitignored) | `playwright_uploader.py:200-212`; `.gitignore` |
| Config | `.env`: `ND_BASE_URL` mặc định `https://congchungnamdinh.ninhbinh.gov.vn`, `ND_*` | `.env.example`; `playwright_uploader.py:200-212` |
| Quyền hệ thống | ghi workspace, Chromium Playwright bundled, mạng HTTPS tới web tỉnh; đọc file Word người chọn | `environment_check_service.py:389-405` |
| Threading | Playwright sync API **chỉ trên một Python thread** (`upload-lab-playwright`), không dùng QThread cho browser | `ui_qt/workers.py:57-75,146-207` |

### 3.4 Code/test/fixture CHỈ có trên nhánh chưa merge

| Hạng mục | Nhánh | Source |
|---|---|---|
| `poc/desktop_command/`: Electron app (`electron/{main,preload,renderer*,*.test.mjs}`, `package.json` Electron `^31.0.2`) + sidecar FastAPI (`server.py`: `/healthz`, `POST /v0/commands`, `GET /v0/jobs/{id}`, Bearer token, no CORS) + `models.py` (contract `v0.experimental`, commands `start_upload/cancel_upload/scan_document/get_status`, status `accepted/waiting_user/running/failed/completed/canceled`) + `registry.py` (idempotent, chặn payload key nhạy cảm) + `bridge.py`/`runtime.py` (queue-only quanh `UploadWorker`; `scan_document` cố tình unavailable) | `codex/desktop-command-poc` | `f18a42f`; spec: `docs/superpowers/specs/2026-09-11-desktop-command-poc.md`; test: `tests/test_desktop_command_poc.py` + 2 `.test.mjs` |
| `poc/conversion_benchmark/`: golden dataset `GD-01..GD-07` (file thật: pdf/docx/xlsx/doc/png/broken) + `golden_manifest.json` + `harness.py` + `router.py` | `min-52-conversion-benchmark` | `ce05b52`; test: `tests/test_markitdown_conversion_poc.py` |
| Plan doc POC | **main** (đã merge) | `docs/superpowers/plans/2026-09-11-desktop-command-poc.md` |

Lưu ý doc: `upload_lab/AGENTS.md` dẫn `docs/spec_UI.md` nhưng file không tồn tại
trên main — stale ref nhỏ, báo owner repo sửa sau.

---

## 4. `notaryoffice` — NGOÀI PHẠM VI G1-SM

Chưa có code (chỉ docs). Remote `origin/main@1c1b160`, `origin/min-54-evidence-spec@c744975`.
Local `D:/notaryoffice` main chưa commit, toàn untracked (`intent*.md`, `docs/`,
`architecture_sources/`). Trong shell Electron: chỉ mục "Chưa triển khai" (MIN-67).

`excelTK`: dự án riêng, NGOÀI PHẠM VI.

---

## 5. Baseline test (chạy mới ngày 14/09/2026 trên máy này)

| Suite | Ref | Lệnh | Kết quả | Ghi chú |
|---|---|---|---|---|
| notary_v2 Python | `9a9bf9a` (worktree `g1-notary-audit-devin`, venv mới, `requirements.txt` + pytest + numpy) | `venv/Scripts/python.exe -m pytest tests -q` | **118 pass / 2 fail** | 2 fail = `test_ocr_local_v4.py::DetectorAndCropTests::{test_crop_box_image_upscales_small_text_line, test_rapidocr_detect_boxes_handles_numpy_array_output}` — `np=None` vì `cv2`/stack local OCR (parked, `requirements-local-ocr.txt`) vắng |
| notary_v2 Node | `9a9bf9a` | `node --test tests/*.test.mjs` | **22 pass / 0 fail** | `cases_ui_dataflow_static`, `diagram_inheritance_engine`, `diagram_state` |
| notary_v2 pytest (env tối thiểu, không numpy) | `9a9bf9a` | `pytest tests -q` | **collection error** trên `test_ocr_local_v4.py` (`import numpy`) | Suite main giả định local-OCR deps cho file test này dù tính năng parked |
| upload_lab unittest | `a4349a2` (worktree, venv `D:/upload_lab_repo/.venv`) | `python -m unittest discover -s tests` | **120 pass / 0 fail** (26.3s) | README ghi "109 tests" — stale |
| zalo branch | `d350048` | artifact `HANDOFF_2026-09-14.md` (đã dọn khỏi root, xem git history) + **xác minh source lần này** | **1 fail**: `tests/test_ocr_ai.py::test_active_cloud_path_has_no_document_qr` | Nguyên nhân xác minh tại source: `form.html` ~dòng 8338-8366 chứa code QR legacy **sau `return;`** (dead code) trong khoảng `ocrExtractAll`→`ocrExtractLocal`; test quét cả khoảng nên fail. `routers/ocr_ai.py` trên nhánh sạch symbol QR. KHÔNG sửa trong task này |
| ocr-stage-pool-diagram-v1 | `a800406` | artifact `HANDOFF_2026-09-14.md` (đã dọn khỏi root, xem git history) | 75 pytest + 14 Node pass | Chưa rerun (không venv sẵn) |

Chưa chạy: suite trên `inheritance-diagram-v2`/`markitdown-qwen-poc` (cần venv
riêng từng nhánh — làm khi P0 duyệt và task cụ thể cần); Electron POC tests
(`poc/desktop_command` chạy `node --test` + pytest riêng, branch `f18a42f`).

## 6. Fixture & dữ liệu test

- `upload_lab`: test tự sinh `.docx`/`.xlsx` bằng python-docx/openpyxl trong temp
  dir — **không cần dữ liệu thật**. `regex_review_samples/{input,reports}` rỗng
  trong repo.
- Golden dataset chuẩn GD-01..GD-07 chỉ có trên `min-52-conversion-benchmark`
  (`poc/conversion_benchmark/golden/`) — fixture tổng hợp theo
  `SYSTEM_ARCHITECTURE.md` §6.8.
- `notary_v2`: test dùng string/mẫu inline + mock cloud; fixture JSON
  `tests/fixtures/inheritance_research_cases.json` chỉ trên nhánh codex.
  `ocr test/`, `tests/QR test/`, `tests/bad QR test/` là thư mục local gitignored.
- **`ID template/{1,2,5,6}.jpg` được track trong git trên main** (~150KB/ảnh,
  nghi là ảnh giấy tờ định danh dùng dev QR/OCR) — rủi ro dữ liệu nhạy cảm, xem
  mục 7.

## 7. Rủi ro / phát hiện cần chú ý

1. **Hai thế hệ Case Workspace tồn tại song song**: main giữ engine JS
   (`inheritance_engine.js`, ReactFlow vendor, `preview.html`/`macros.html`);
   các nhánh codex đã chuyển sang `services/inheritance_engine.py` +
   `word_engine.py` và xóa các file trên. Migrate phải chọn một nguồn (mục 8).
2. `routers/cases.py:780` hardcode UNC `\\maychu\...` cho template fallback —
   xung đột "file reference có machine scope" của DesktopCommand (MIN-62/MIN-64).
3. `ocr_qr_worker.js` tải jsQR từ CDN `cdn.jsdelivr.net` — phụ thuộc mạng ngoài
   cho app đóng gói; cần vendor lại hoặc loại.
4. `htmldocx` được import ở `routers/cases.py:1578,1643` nhưng **không có trong
   `requirements.txt`** — route export-draft/preview lỗi nếu thiếu gói (xử lý
   bằng nhánh fallback `Document()`).
5. `requirements.txt` notary_v2 chứa `playwright` nhưng không file `.py` nào
   import — dependency thừa hoặc từng dùng.
6. `run.bat` notary_v2 vẫn tự cài stack local OCR (torch/vietocr/rapidocr) dù
   tính năng parked — bootstrap nặng cho packaged app.
7. `ID template/*.jpg` tracked trong git — kiểm tra độ nhạy cảm trước khi mang
   vào fixture/test G1-SM.
8. `memory-bank/CURRENT.md` trên `D:/notary_v2` đang dirty (không phải của task
   này); nội dung memory-bank lạc hậu (main `8e0b5ab` vs thật `9a9bf9a`).
9. Linear issues MIN-75/MIN-68/MIN-69 còn ghi "qua LAN" trong khi scope G1-SM là
   một máy — cần SM-00 đồng bộ Linear sau khi owner duyệt design spec.
10. `docs/spec_UI.md` trong `upload_lab/AGENTS.md` không tồn tại trên main.

## 8. CẦN OWNER QUYẾT (D0) — không tự quyết

| # | Quyết định | Trạng thái |
|---|---|---|
| D0-1 | Nguồn migrate notary_v2 | **CHỐT 14/09: `codex/zalo-document-inbox-v2` @ `d350048`** (xem block trên đầu file) |
| D0-2 | Zalo Inbox trong G1-SM | **CHỐT 14/09: CÓ** |
| D0-3 | **Local OCR (parked)** trong shell: hiển thị "không khả dụng", ẩn, hay kèm stack nặng? | Mở — chặn P6-B packaging; P1 sẽ đo khả năng đóng gói stack OCR để hỗ trợ quyết định |
| D0-4 | **fast_audit CLI** + **regex_lab/review tools**: giữ CLI ngoài Electron hay có surface? | Mở — chặn phạm vi UI P6-A/B |
| D0-5 | `ID template/*.jpg` tracked trong git: có phải giấy tờ thật? có được dùng/giữ làm fixture không? | Mở — P1/P6 không dùng file này làm fixture cho tới khi có quyết định |
| D0-6 | Luồng preview/export-draft/preview-legacy | **CHỐT tự động theo D0-1** — đã xóa trên `d350048` (verified) |
| D0-7 | UNC `\\maychu\...` và mọi đường dẫn tuyệt đối: chính sách file reference máy-client vs server cho contract MIN-62 | Mở — **chặn P2** (contract) nếu chưa chốt |
| D0-8 | `codex/ocr-stage-pool-diagram-v1` (`a800406`) còn vai trò gì? Có chứa state duy nhất cần giữ? | Mở — housekeeping, không chặn |
| D0-9 | Thư mục legacy `D:/notary_app`, `D:/upload_lab`, `*_old_20260914-1`: chỉ archival? | Mở — housekeeping, không chặn |
| D0-10 | SM-00: đồng bộ Linear theo scope một máy (MIN-75/76/66 + issue nghiệm thu một máy mới) | Mở — không chặn P1; cần trước P7 nghiệm thu |

## 9. Không có / chưa chứng minh (ghi ngang mục có)

- Không có API giữa các repo; không DB chung; không luồng dữ liệu tự động.
- `upload_lab` main không có HTTP server/desktop API — DesktopCommand production
  phải dựng mới (POC chỉ là bằng chứng).
- `notary_v2` main không có Zalo Inbox, `word_engine.py`, `inheritance_engine.py`
  — tất cả nằm trên nhánh chưa merge.
- Không có Electron app production nào — chỉ POC `poc/desktop_command/`.
- Chưa đo: IFilter khi Word giữ file (A1), sự kiện ổ mạng (A3), tài khoản máy
  trạm (A4) — các quyết định 🔴 vẫn mở, G1-SM một máy không tự đóng.
- LAN/nhiều máy/SMB/cutover toàn văn phòng: chưa kiểm tra, thuộc G1-LAN.

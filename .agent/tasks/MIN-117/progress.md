# Progress — MIN-117

## Trạng thái: xong — 2026-09-25 (verify end-to-end packaged PASS)

Base `29cf2a0`. Fix defect MIN-113 D3: packaged sidecar thiếu third-party deps
của engine thật → mọi `notary.*` real trả `engine_not_installed`/
`engine_unavailable`.

## 1. Enumerate deps (grep `^import|^from` trên các module adapter chạm tới)

Module engine load runtime qua `engine_roots` (không bundle source):

- `notary_adapter` → `database`, `models`, `services.{word_engine,
  zalo_inbox, case_workspace, document_intake.*, inheritance_workspace,
  word_batch_export, fast_audit.* (qua zalo_inbox)}`,
  `routers.{customers, properties, participants, ocr_ai}`.
- `upload_adapter`/`upload_session` → `batch_scan`, `extract_contract`,
  `ui.services.{contract_book_audit, environment_check_service}`,
  `playwright_uploader`, `uploader_selectors`.
- `command_registry` → `docx`, `pymupdf` (lazy, trong `_preview`).

Third-party cần bundle (đã kiểm chứng bằng grep thật):

| Package | Người dùng | Ghi chú |
|---|---|---|
| `sqlalchemy` | database/models/mọi service | dialects + ext load động → collect_all |
| `docx` (python-docx) | word_engine, word_batch_export, document_intake, extract_contract, command_registry | kéo `lxml` (C ext) |
| `pymupdf` + `fitz` | pdf adapter, pdf_splitter, zalo_inbox, command_registry | PyMuPDF 1.24.5 cả hai tên; `_mupdf.pyd`+`mupdfcpp64.dll` |
| `openpyxl` | excel_parse, contract_book_audit, report_writer, batch_scan | |
| `PIL` (Pillow) | ocr_pipeline | plugin load động |
| `dotenv` (python-dotenv) | ocr_ai, playwright_uploader | |
| `httpx` | ocr_ai, fast_audit ocr_runner | |
| `rapidfuzz` | fast_audit compare/rules | C ext |
| `jinja2` | routers.customers/properties (Jinja2Templates) | markupsafe auto |
| `multipart` (python-multipart) | **bắt buộc lúc import routers** — fastapi raise "Form data requires python-multipart" khi đăng ký route Form/File | lazy import → bắt buộc hiddenimport |
| `pydantic` + `pydantic_core` | fastapi dep + routers.zalo_inbox | `.pyd` binary |
| `tzdata` | services.zalo_inbox `ZoneInfo("Asia/Ho_Chi_Minh")` — Windows không có system tz db | collect_all lấy data files |
| `playwright` | upload.session_*/prepare/env_check | lazy trong playwright_uploader nhưng runtime cần; collect_all lấy cả `driver/node.exe` |
| `sqlite3` | stdlib — `sqlalchemy.dialects.sqlite` kéo `_sqlite3.pyd`+`sqlite3.dll` tự động | đã verify có trong `_internal/` |

Không có `yaml`, `requests`, `aiofiles`, `numpy`, `pandas` trong các module
reachable — không bundle. PySide6 (upload_lab ui_qt) không reachable từ
sidecar — không bundle.

Word templates **không** bundle: `notary_adapter._resolve_template` đọc
`<engine_root>/word_templates/*.docx` từ filesystem (datas=[] cho engine).

## 2. Diff

`shell/sidecar/g1-shell-sidecar.spec`: thêm vòng `collect_all()` cho 16
package trên → `datas`/`binaries`/`hiddenimports` của Analysis. Không đổi
runtime_hooks/excludes/entry. Dev-mode không đổi (spec chỉ ảnh hưởng build).

## 3. Build

```text
G1_PYTHON=D:\systemdocs\notary_v2\venv\Scripts\python.exe
powershell -ExecutionPolicy Bypass -File shell/sidecar/build_sidecar.ps1
→ PyInstaller 6.22.3, Python 3.12.10, contrib hooks 2026.7
→ OK: dist/g1-shell-sidecar/g1-shell-sidecar.exe (234MB onedir)
```

Cảnh báo duy nhất có ý nghĩa: `pysqlite2`, `MySQLdb` not found — dialect
optional của sqlalchemy, dự kiến. Warn log còn lại là noise posix/Unix
chuẩn của PyInstaller trên Windows.

Đã kiểm chứng trong `_internal/`: `sqlite3.dll`, `_sqlite3.pyd`,
`sqlalchemy/dialects/sqlite/*`, `pymupdf/` (+ PyMuPDFb), `pydantic_core/`,
`tzdata/zoneinfo/Asia/Ho_Chi_Minh`, `playwright/driver/node.exe`.

## 4. Verify end-to-end trên exe packaged — PASS

DB worktree-local: `notary_v2/notary.db` chưa tồn tại trong worktree (gitignore
`*.db`) → copy DB đã seed từ `D:\systemdocs-min-113\notary_v2\notary.db`
(case 1 draft, 6+1 participants, 2 properties — fixture MIN-113 §3 real).
KHÔNG đụng `D:\systemdocs`.

Launch (mock flag cố tình bật để kiểm strip):

```text
SIDECAR_TOKEN=min117test SIDECAR_PORT=8765
G1_NOTARY_V2_ROOT=D:\systemdocs-min-117\notary_v2
G1_UPLOAD_LAB_ROOT=D:\systemdocs-min-117\upload_lab
G1_DEV_NOTARY_MOCK=1
./dist/g1-shell-sidecar/g1-shell-sidecar.exe
```

Kết quả qua HTTP loopback `http://127.0.0.1:8765`:

| Check | Kết quả |
|---|---|
| `GET /healthz` | `{"ok":true,"accepting":true,...}` |
| `notary.workspace_get` `{case_id:1}` | `succeeded`, `backend_mode:"real"`, stage 7 people / 2 assets, capabilities đầy đủ — KHÔNG `engine_not_installed` |
| `notary.word_export_options` | `succeeded`: khai_nhan ready, thoa_thuan ready, niem_yet `word.template_missing` |
| `notary.word_export_batch` 1 doc → `.tmp/min117/dest` | `succeeded`, `Van_ban_khai_nhan_di_san_HS-1.docx` 22224 bytes trên đĩa; mở bằng python-docx đọc được 140 paragraphs |
| `notary.case_list` | `succeeded`, cases `[2,1]` (query sqlalchemy thật) |
| `notary.diagram_evaluate` (state từ workspace) | `succeeded`, warnings=0 |
| `file.inspect` trên .docx vừa xuất | `succeeded`, preview 2587 chars (docx reader trong bundle) |
| `upload.env_check` | `succeeded` — engine upload_lab import OK (playwright_uploader, environment_check_service) |
| Mock flag `G1_DEV_NOTARY_MOCK=1` trên exe | stderr: `WARN: G1_DEV_NOTARY_MOCK bi bo qua tren ban packaged (backend real)` — strip đúng `sys.frozen` |
| `POST /shutdown` | `{"stopping":true}` → `tasklist` không còn `g1-shell-sidecar.exe` — không orphan |

Một lần submit thất bại do test payload thiếu `is_dir:true` trong
destination file_ref → `validation_error` "file_ref destination phai co
is_dir:true" — contract đúng, gửi lại pass.

## 5. Phần chưa được / giới hạn

- `upload.session_*`/prepare (Playwright browser thật) chưa chạy — cần
  `playwright install chromium` trên máy + tương tác người dùng; driver đã
  bundle, verify chỉ tới mức import/env_check.
- `ocr.analyze`/`intake_analyze` nguồn ảnh cần `QWEN_API_KEY` thật — không
  test (ngoài acceptance; lỗi thiếu key đã verify controlled ở MIN-113).
- Defect `word_export_batch` + dest read-only hang (MIN-113 §4b) vẫn còn —
  ngoài scope, chưa sửa.
- Kích thước bundle 234MB (playwright driver + pymupdf chiếm phần lớn).
  Nếu owner muốn gọn hơn có thể tách playwright thành optional follow-up.

## Check đã chạy
- Build log đầy đủ + warn file: `shell/sidecar/build/g1-shell-sidecar/`
  (gitignored).
- Evidence verify: `.tmp/min117/` (gitignored) — ws.json, diag_req.json,
  sidecar.log, dest/*.docx.

# Decisions — MIN-117

## 2026-09-25 — `collect_all` cho 16 package thay vì hiddenimports rời
- **Chọn:** Vòng `collect_all()` trên `_ENGINE_DEP_PACKAGES` trong
  `g1-shell-sidecar.spec` (sqlalchemy, docx, lxml, pymupdf, fitz, openpyxl,
  PIL, httpx, rapidfuzz, jinja2, multipart, pydantic, pydantic_core, dotenv,
  tzdata, playwright).
- **Lý do:** Các package này load submodule/data/binary động
  (`sqlalchemy.dialects.*`, `docx.oxml.*`, PIL plugins, pymupdf C ext +
  `mupdfcpp64.dll`, pydantic_core `.pyd`, tzdata zoneinfo db, playwright
  `driver/node.exe`) — `hiddenimports` đơn thuần không đủ datas/binaries.
- **Loại bỏ:** (a) Ship engine kèm venv/embedded Python ngoài exe — nặng,
  trùng venv dev, khó maintain; (b) liệt kê từng submodule tay — dễ rớt
  khi engine đổi deps.
- **Nguồn:** defect MIN-113 D3 + brief MIN-117; verify thực tế §4
  progress.md.

## 2026-09-25 — Bundle `playwright` kể cả lazy
- **Chọn:** `collect_all('playwright')` — gồm cả driver `node.exe`.
- **Lý do:** `upload.session_*`/`upload.prepare`/`upload.env_check` là
  command surface đã duyệt của sidecar; thiếu playwright trong bundle thì
  packaged exe lặp lại đúng defect của notary (command trả
  engine_unavailable). Browser binaries (ms-playwright cache) vẫn ngoài
  bundle — `playwright install chromium` trên máy đích.
- **Loại bỏ:** Bỏ playwright để exe nhẹ — phá `upload.*` trên bản packaged.
- **Nguồn:** `upload_lab/playwright_uploader.py:886-887` (lazy import),
  `probe_playwright_runtime()` (:350-355).

## 2026-09-25 — `multipart` (python-multipart) là hiddenimport bắt buộc
- **Chọn:** Thêm `multipart` dù không có `import multipart` trực tiếp nào
  trong engine code.
- **Lý do:** FastAPI 0.111 kiểm `import multipart` khi router đăng ký
  route có `Form(...)`/`File(...)` — `routers.customers`, `properties`,
  `participants`, `ocr_ai` đều dùng. Import runtime qua
  `engine_roots.import_engine_module` không qua modulegraph → PyInstaller
  không tự thấy → thiếu sẽ fail lúc import router trên exe.
- **Nguồn:** grep Form/File tại routers/*; fastapi deps-utils.

## 2026-09-25 — DB test worktree-local copy từ MIN-113
- **Chọn:** Copy `D:\systemdocs-min-113\notary_v2\notary.db` (đã seed
  case 1: draft, participants, properties) sang `D:\systemdocs-min-117\
  notary_v2\notary.db` cho verify.
- **Lý do:** `*.db` gitignored nên worktree không có DB sẵn; canonical
  `D:\systemdocs\notary_v2\notary.db` có case 1 nhưng 0 participants và
  bị cấm đụng. Adapter `_ensure_db()` chạy migrate + create_all nên schema
  được chuẩn hóa theo code hiện tại.
- **Loại bỏ:** Seed tay từ đầu — chậm, trùng lại fixture MIN-113 đã kiểm.

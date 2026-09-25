# Handoff — MIN-117

## Trạng thái khi bàn giao — 2026-09-25
Xong. Packaged `g1-shell-sidecar.exe` giờ chạy được engine thật:
`notary.*` real trả `backend_mode:real` + dữ liệu DB thật, export Word ra
.docx thật; `upload.env_check` pass; mock flag bị strip trên packaged.
Defect MIN-113 D3 đã đóng.

## File đã đổi
- `shell/sidecar/g1-shell-sidecar.spec` — thêm `datas`/`binaries` +
  vòng `collect_all()` cho 16 third-party deps của engine (sqlalchemy,
  docx, lxml, pymupdf, fitz, openpyxl, PIL, httpx, rapidfuzz, jinja2,
  multipart, pydantic, pydantic_core, dotenv, tzdata, playwright).
  Không đổi entry/runtime_hooks/excludes; dev-mode không ảnh hưởng.
- `.agent/tasks/MIN-117/{progress,decisions,handoff}.md` — record task.

## Cách verify
1. Build: `G1_PYTHON=D:\systemdocs\notary_v2\venv\Scripts\python.exe
   powershell -ExecutionPolicy Bypass -File shell/sidecar/build_sidecar.ps1`
   → `dist/g1-shell-sidecar/g1-shell-sidecar.exe`.
2. Chạy exe với `SIDECAR_TOKEN`, `SIDECAR_PORT`, `G1_NOTARY_V2_ROOT`
   trỏ tới `notary_v2/` có `notary.db` → `GET /healthz` ok.
3. `POST /v1/commands` `notary.workspace_get {case_id:1}` → job
   `succeeded`, `result.data.backend_mode=="real"`.
4. `notary.word_export_batch` 1 doc → dest dir có `.docx` thật.
5. `G1_DEV_NOTARY_MOCK=1` khi launch exe → stderr WARN strip, backend real.
6. `POST /shutdown` → process thoát, không orphan.

## Việc còn lại / rủi ro
- `upload.session_*` browser thật chưa verify end-to-end (cần
  `playwright install chromium` + người thao tác login).
- `ocr.analyze`/intake ảnh cần API key thật — chưa test.
- Bundle 234MB — nếu cần nhỏ hơn, cân nhắc tách playwright optional.
- Defect dest-read-only hang của `word_export_batch` (MIN-113 §4b) vẫn
  mở — repo `notary_v2`, cần issue riêng.
- Khi thêm dep mới vào engine reachable path: thêm vào
  `_ENGINE_DEP_PACKAGES` trong spec + rebuild + smoke `notary.workspace_get`.

## File tạm đã dọn
- `.tmp/min117/` giữ evidence verify (gitignored — ws.json, diag_req.json,
  sidecar.log, dest/*.docx). Có thể xóa khi owner xong review.
- `notary_v2/notary.db` trong worktree là bản copy test (gitignored),
  KHÔNG phải DB user — an toàn xóa.
- `shell/sidecar/{dist,build}/` gitignored, không commit.

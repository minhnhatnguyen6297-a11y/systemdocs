# MIN-117 — PACKAGING: sidecar PyInstaller thiếu deps của engine thật

Linear: MIN-117 (parent MIN-68). Phát hiện bởi MIN-113 packaged smoke
(`.agent/tasks/MIN-113/decisions.md` D3 — đọc trước).

## Defect
`shell/sidecar/g1-shell-sidecar.spec` chỉ bundle `uvicorn`+`fastapi`.
Sidecar exe packaged chạy + healthy nhưng `notary_adapter`/`upload_lab`
import engine từ filesystem qua `engine_roots.py` → engine source có, nhưng
third-party deps (`sqlalchemy`, `sqlite3`?, `docx`, `fitz`/PyMuPDF, `openpyxl`,
`requests`/`httpx`...) không có trong bundle → mọi `notary.*` real command
trả `engine_not_installed`.

## Việc
1. Enumerate deps: grep imports trong `notary_v2/` (services, models, database,
   document_intake, word_engine, inheritance_engine) + `upload_lab/` + adapter
   files trong `shell/sidecar/` → danh sách third-party modules cần.
2. Sửa `g1-shell-sidecar.spec`: `collect_submodules`/`collect_all` cho từng
   dep cần; `sqlite3` là stdlib — nếu thật sự thiếu trong exe thì cần
   investigate PyInstaller env (thiếu DLL?). datas nếu engine cần file kèm
   (templates word — check `notary_v2` template dirs có được load từ
   filesystem qua engine_roots hay cần bundle).
3. Rebuild: `powershell -ExecutionPolicy Bypass -File shell/sidecar/build_sidecar.ps1`
   (venv `D:\systemdocs\notary_v2\venv\Scripts\python.exe` có sẵn pyinstaller).
4. **Verify end-to-end thật** — đây là acceptance:
   - Chạy `dist/g1-shell-sidecar/g1-shell-sidecar.exe` trực tiếp (không cần
     Electron): sidecar up → POST command `notary.workspace_get` case_id=1
     qua HTTP loopback → phải trả `backend_mode:real` + workspace thật,
     KHÔNG `engine_not_installed`.
   - `notary.word_export_options` + `word_export_batch` 1 doc ra temp dir →
     file .docx thật.
   - `upload_lab` command smoke nếu có.
   - Mock flag `G1_DEV_NOTARY_MOCK=1` trên exe → phải bị strip (sys.frozen).
   - DB: engine_roots resolve `notary_v2` — dùng DB worktree-local
     (`D:\systemdocs-min-117\notary_v2\notary.db`), KHÔNG đụng `D:\systemdocs`.
5. Nếu cần data files (word templates) → thêm datas + verify export thật.

## Ràng buộc
- Worktree `D:\systemdocs-min-117`, branch `minhnhatnguyen6297/min-117-pyinstaller-engine-deps`.
- Không sửa contracts/, Zalo, renderer; không đổi default behavior dev-mode.
- Build artifacts (`dist/`, `build/`) KHÔNG commit (gitignore).
- Có thể cần `pip install` vào venv — chỉ package đã dùng trong repo
  (check `notary_v2/requirements*.txt`, `shell/sidecar/requirements*`).
- Commit `fix(shell): bundle engine deps into packaged sidecar` + MIN-117.
- `.agent/tasks/MIN-117/progress.md` + `decisions.md` — paste output verify thật.

# Progress — MIN-69

## Trạng thái: triển khai theo kế hoạch — 25/09/2026 (cập nhật)

Triển khai tại worktree riêng `D:/systemdocs-min-69`, nhánh `minhnhatnguyen6297/min-69-migrate-uploadaudit-vao-electron` (base `consolidate/monorepo` @ 1abbb20). Quy trình: subagent-driven development — mỗi task có implementer + reviewer + fix loop riêng. Owner duyệt contract khi review nhánh trước merge (user đã chọn "code hết T1–T9").

## Tiến độ task (theo kế hoạch)

- **T1 (xong, review sạch):** spec_UI.md + README viết lại theo 2 tab; `contracts/upload-workflow.md` (DRAFT — chờ owner duyệt) + 53 examples + `validate_examples.py` (37 valid pass / 16 invalid reject đúng mã); 17 commands, `workflow_version`, scope/revision guards.
- **T2 (xong, review sạch):** `upload_lab/providers/` (nam_dinh duy nhất, unknown → `unknown_website`); `shell/sidecar/upload_workspace{,_store}.py` (data root qua `G1_UPLOAD_DATA_DIR`, per-website `websites/<id>/`, SQLite store); `upload_lab/tools/migrate_shell_data.py` (inspect/apply, snapshot+hash verify); `shell/test/test_upload_workspace.py` 27 tests.
- **T6 (xong, review sạch):** `shell/src/renderer/upload/` 2 tab (Audit Sổ Công Chứng + Quét & Upload Hồ Sơ), state chung `createUploadState/selectTab/acceptScopedResult`, CSS scoped `.upload-lab` full-width, 31 tests mjs mới (70/70 npm test).
- **T3 (xong, review sạch):** `upload.scan/audit_excel/queue_get` v1 — manifest file của đúng run (binding+sha256, không fallback file mới nhất), audit_id gắn website+khoảng ngày, `classify_scan_records` thật, `_v1_boundary` chuẩn hóa next_action; `test_upload_workflow.py` 21 tests.
- **T4 (xong):** `_BrowserWorker` wait-state theo job + op-slot `browser_busy` + idle poll snapshot + `_session_lost` reconcile; v1 handlers session_start/confirm_login/session_status/session_close/download_export/staff_options/prepare/finish_review/reconcile; `upload.staff_options` + `upload.reconcile` đăng ký mới; `/health` quảng bá `upload.workflow.v1`; `test_upload_browser_workflow.py` 28 tests qua localhost fake portal (27F+1E RED → GREEN).
- **T5 (xong):** Job terminal bất biến (transition dưới lock, cancel thắng race late-success/failure/progress); `job_repository.py` mới — bảng `sidecar_jobs` trong workspace.sqlite3 (command_id UNIQUE + request_hash → `command_id_conflict` 409, không lưu payload); restart materialize non-terminal → `failed{engine_restarted}`, không replay handler, `get(job_id)` resync lazy; `_recover_interrupted` sweep lúc mở store (workflow_jobs→failed, browsers→closed, open_tabs→needs_reconcile giữ run_id); `worker.shutdown(timeout)` + `_poll_then_close` nguyên tử, tab chưa verify → needs_reconcile không bao giờ 'đã Lưu'; adapter mirror `Job.snapshot()` qua `set_job_status` (duy nhất ghi terminal), prepare tách prepared/saved, `needs_reconcile_record_ids` → engine_unavailable non-retryable; `drain(timeout)` cancel engine_shutdown + persist trước khi đóng repo; tracker.js: instance change → engine_restarted cục bộ + `getJob` resync terminal thật, terminal cục bộ bất biến với snapshot trễ. Tests: test_jobstore +18, test_upload_recovery.py mới 14, test_sidecar_contract +409, job-tracker.test.mjs mới 4 — Python 145 ok + npm 74 ok. **Fix1 (review):** `worker.shutdown(timeout)` chia budget reconcile+join theo deadline (không còn ~2·timeout), `SHUTDOWN_GRACE_MS` 3s→6s (bound _stop ~4.5s + headroom), `record_snapshot` terminal guard CASE WHEN (status+snapshot_json); +2 test Python +1 mjs — Python 146 ok + npm 75 ok.
- **T7 (xong, commit cdedafd):** tab Audit nối trọn — catalog-driven selector + env/login/download/pick → auto audit → 4 KPI + 2 bảng MIN-77; once-per-job adopt (audit/download/ws_get/website_select/session_start), revision forward-only (vá stale_revision), session_status checked_at guard, catalog/ws retry qua derive khi sidecar chưa ready; main.js openPath FileRef scope + ext allowlist + seam G1_E2E_PICK_FILES; test_upload_e2e.py --case audit (Electron thật + CDP + fake_portal hook) PASS; npm test 84/84. Bugs vá trong bring-up: latestJob tie ≥, catalog bootstrap một-lần kẹt khi submit sớm, session_start re-adopt kéo revision lui.
- **T8, T9:** chưa bắt đầu — theo thứ tự plan.

## Đã làm (phiên kế hoạch trước)

- Lập [kế hoạch chuyển đổi](D:/systemdocs/docs/product/plans/2026-09-24-upload-lab-shell-migration-plan.md).
- Đọc chuỗi launcher: bản Fluent UI/Qt hiện tại là giao diện được run.bat mở.
- Đối chiếu source với hai manifest codegraph Upload Lab: bản Fluent có 9/38 tệp khác dấu kiểm tra; bản thử nghiệm Electron có 10/53.
- Tạo brief và [handoff](D:/systemdocs/.agent/tasks/MIN-69/handoff.md).

## Kiểm chứng và giới hạn

- Python test env: `D:/systemdocs/notary_v2/venv/Scripts/python.exe` (shell/sidecar), `D:/systemdocs/upload_lab/.venv/Scripts/python.exe` (upload_lab, có PySide6). Baseline xanh trước khi code.
- Chưa chạy portal thật, chưa đóng gói, chưa chuyển dữ liệu thật — T9/T10 còn lại. Contract vẫn DRAFT chờ owner duyệt.
- Venv không nằm trong worktree (machine-local ở checkout chính) — implementers dùng đường dẫn tuyệt đối ở trên.

---
title: 'Bỏ theo dõi kết quả Lưu; giữ tiến độ chuẩn bị theo lượt'
type: 'refactor'
ticket: '28'
created: '2026-10-15'
status: 'draft'
baseline_revision: '8a128227d707da02275d865b0ebb5a394df10990'
route: 'full'
route_source: 'auto'
risk: 'high'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context: ['{project-root}/_bmad-output/decisions/decision-upload-web-sot-without-save-tracking.md', '{project-root}/_bmad-output/specs/upload_lab/README.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** App vẫn suy kết quả Lưu từ POST `/api/hoso`, điều hướng/đóng tab, `finish_review` — tạo khóa/requeue trái quyết định owner 15/10/2026: dữ liệu website chính thức là SOT.

**Approach:** Bỏ suy luận Lưu và `upload.reconcile` khỏi engine, sidecar, store, renderer, Qt legacy, test echo; tiến độ chuẩn bị theo lượt bám trạng thái registry trong `run_id` hiện tại.

## Boundaries & Constraints

**Always:** Điền sẵn rồi dừng trước nút Lưu; wire chỉ mang tiến độ chuẩn bị + tài nguyên tab; lô kế do người dùng bấm, chỉ gồm hồ sơ đã chọn chưa chuẩn bị; giữ cổng đăng nhập/revision/job/tài nguyên browser; không xóa/migrate dữ liệu production (`uploaded_success*`, bảng `needs_reconcile` cũ); quét lại chuyển row sang run mới nên "Tiếp tục" trên run cũ phải bị binding run/scope từ chối, không tự chuẩn bị lại.

**Never:** Không fetch/reconciliation engine, `needs_reconcile`, khóa UI, auto-retry/requeue do chưa rõ Lưu, lô tự chạy, blacklist, shim, telemetry; không đổi version contract; không dựng lại probe race Save.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Lưu, tab vẫn mở | 10 chuẩn bị, 3 POST 2xx | không khóa Lưu; 3 tab `open` | — |
| Tab đóng chưa Lưu | 2 tab đóng | chỉ `closed_record_ids`; không ghi `needs_reconcile` | không lỗi |
| Tiếp tục lô sau | 10 đã chuẩn bị (5 chưa Lưu) | chỉ hồ sơ chưa chuẩn bị; ID cũ không mở lại | `stale_revision` khi queue cũ |
| `finish_review`/`session_close` | bước chờ kết thúc | đóng tài nguyên; không kết luận Lưu | `wrong_job`, lỗi scope |
| `upload.reconcile` | command/capability đã bỏ | `command_unknown` | không nhánh phục hồi |
| Restart giữa review | `failed{engine_restarted}` | tiến độ sống theo registry | retryable §8 |

</frozen-after-approval>

## Code Map

- `upload_lab/playwright_uploader.py` — bỏ suy luận Lưu (finalize, listener POST, route heuristic); poll chỉ tài nguyên tab; prepare lọc theo trạng thái run.
- `upload_lab/batch_scan.py` + `providers/nam_dinh.py` — bỏ skip theo `uploaded_success` và capability `reconcile`; cột `uploaded_success_at` giữ.
- `shell/sidecar/` — `upload_workspace_store.py`, `upload_session.py`, `upload_adapter.py`, `command_registry.py`: bỏ surface Save (`needs_reconcile`, `verified_record_ids`, `upload_reconcile_v1`), schema cũ giữ.
- `shell/src/renderer/upload/` — `client.js`, `state.js`, `scan-upload.js`, `index.js`, `upload.css`: bỏ cờ/banner/action đối chiếu.
- `upload_lab/ui_qt/` + `upload_services/folder_workflow_service.py` — đồng bộ legacy.
- `shell/test/fixtures/upload_portal.py`, test hai phía, `upload_lab/README.md` — fixture/echo/mô tả.

## Tasks & Acceptance

**Execution:**
- [ ] engine (`playwright_uploader.py`) — bỏ suy luận Lưu; loại trừ theo trạng thái registry trong run.
- [ ] scan (+`nam_dinh.py`) — bỏ ghi/đọc `uploaded_success`.
- [ ] sidecar (4 file trên) — bỏ surface Save; wire khớp §6.7/§6.14.
- [ ] renderer — UI chỉ mô tả chuẩn bị/tài nguyên.
- [ ] Qt legacy + `folder_workflow_service.py` — đồng bộ.
- [ ] fixture + test hai phía + README — xóa echo, test policy.

**Acceptance Criteria:**
- Given luồng v1 với sổ Excel chính thức, when chạy trọn flow (scan → audit → prepare → Lưu/đóng tab → Tiếp tục → `session_close`, kể cả restart), then wire/store/UI không còn kết luận hay số đếm Lưu, lô kế chỉ gồm hồ sơ chưa chuẩn bị, các luồng thường giữ hành vi §6–§8.

## Implementation Notes

## Plan Change Log

## Review Triage Log

## Design Notes

`prepare` chỉ nhận trạng thái tiền-chuẩn bị trong `run_id` hiện tại nên ID đã chuẩn bị không quay lại lô sau; quét lại B trên cùng file chuyển row sang run mới — "Tiếp tục" trên A bị binding run/scope từ chối (không tự chuẩn bị lại), chọn lại ở B là đường hợp lệ. `open_tabs` vẫn là tài nguyên cho `workflow_busy`/`session_close`; `queue_get` vẫn hiển thị row đã chuẩn bị, chỉ `prepare` lọc.

## Verification

**Commands:**
- `& $env:G1_PYTHON test/test_upload_e2e.py --case upload` (cwd `shell/`) -- bắt buộc: prepare 10, Lưu 3, đóng 2 tab chưa Lưu, Tiếp tục chỉ mở hồ sơ chưa chuẩn bị.
- `& $env:G1_PYTHON test/test_upload_browser_workflow.py`; `npm test` (cwd `shell/`) -- pass, shape tài nguyên.
- `.\.venv\Scripts\python.exe -B -X utf8 -m pytest tests/ -q -p no:cacheprovider` (cwd `upload_lab/`) -- pass.

**Manual checks (if no CLI):**
- Nếu e2e không chạy được: smoke bắt buộc trên app/engine thật + browser cô lập; kèm edge prepare A → scan B → Tiếp tục A phải là `scope_violation`, không mở tab mới.

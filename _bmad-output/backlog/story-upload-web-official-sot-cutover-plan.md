---
title: 'Bỏ theo dõi kết quả Lưu; giữ tiến độ chuẩn bị theo lượt'
type: 'refactor'
ticket: '28'
created: '2026-10-15'
status: 'built'
baseline_revision: '8a128227d707da02275d865b0ebb5a394df10990'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 2
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
- [x] engine (`playwright_uploader.py`) — bỏ suy luận Lưu; loại trừ theo trạng thái registry trong run.
- [x] scan (+`nam_dinh.py`) — bỏ ghi/đọc `uploaded_success`.
- [x] sidecar (4 file trên) — bỏ surface Save; wire khớp §6.7/§6.14.
- [x] renderer — UI chỉ mô tả chuẩn bị/tài nguyên.
- [x] Qt legacy + `folder_workflow_service.py` — đồng bộ.
- [x] fixture + test hai phía + README — xóa echo, test policy.

**Acceptance Criteria:**
- Given luồng v1 với sổ Excel chính thức, when chạy trọn flow (scan → audit → prepare → Lưu/đóng tab → Tiếp tục → `session_close`, kể cả restart), then wire/store/UI không còn kết luận hay số đếm Lưu, lô kế chỉ gồm hồ sơ chưa chuẩn bị, các luồng thường giữ hành vi §6–§8.

## Implementation Notes

Chốt nghĩa chuẩn tắc cho implementer (đọc kèm I/O Matrix; theo contract đích, không thêm quyết định kinh doanh):

- **`finish_review` vs `session_close` (§6.5/§6.7):** `upload.finish_review` chỉ giải phóng job prepare đang `waiting_user(review)` và trả `review_finished`; tab người dùng vẫn mở, không đóng tài nguyên. Chỉ `upload.session_close` đóng phiên/browser và trả `closed: true` + `closed_record_ids`/`unknown_record_ids` (chỉ mô tả tài nguyên). Dòng matrix tương ứng đọc theo đúng hai nghĩa này.
- **Tab đóng/mất dấu (§6.6, A2):** là sự kiện tài nguyên — bỏ hẳn `needs_reconcile`/`verified` và bỏ `bump_queue_revision` chỉ sinh ra để phục vụ chúng (`upload_session.py` 466–533, `upload_adapter.py` 1634–1643). Poll `session_status` không tự tăng revision nguồn (§3 rule 2); renderer giữ cơ chế refetch-một-lần-mỗi-job khi queue đổi thật (scan/audit/prepare status), không thêm luật mới.
- **`uploaded_success` cũ (A3):** chỉ là lịch sử dữ liệu. Không backfill/DELETE/migrate; row cũ nằm ngoài `QUEUE_STATUSES` nên không tự vào queue; quét lại upsert status theo file (đường người dùng chủ động chọn lại). Không có nhánh "coi là đã Lưu", không auto-requeue.
- **Run A chờ review + scan B (A4):** prepare giữ `waiting_user(review)` tới `finish_review`/cancel/`upload.review_timeout` 60' (§6.14); scan B là job riêng, không có khóa xuyên run; prepare mới trên A bị `scope_violation` khi `record_ids` không còn thuộc run A (binding run→manifest + `record_ids ⊆ run`); `website_select` vẫn chặn bằng `workflow_busy` hiện có. Không thêm "latest-run rule" hay khóa toàn cục.
- **Field delta (A6):** theo từng command — `upload.session_status` §6.6: `login` + `tabs.open_record_ids`/`closed_record_ids`/`unknown_record_ids`; `upload.session_close` §6.7: `closed: true` + `closed_record_ids`/`unknown_record_ids`; `upload.prepare` §6.14: `summary` (prepared/`remaining`/`open_record_ids`) + `breakdown` theo `record_id`+`stage`. Không trường Save nào; schema store hiện hữu (bảng/cột cũ) giữ nguyên, không DROP.
- **Bằng chứng (E2/A5):** smoke bắt buộc chạy engine thật + Playwright browser thật (chỉ fixture portal localhost, không session giả như `PortalBrowserSession`); e2e `--case upload` chỉ là lớp bổ sung. `npm test` chỉ chạy Node (`node --test test/*.test.mjs`) — suite Python gọi riêng, gồm `shell/test/test_upload_recovery.py`.
- **Anchors đã đọc:** `upload_lab/playwright_uploader.py` 765–773, 1912–2025, 2137–2145; `upload_lab/batch_scan.py` 179–189, 353–368, 679–703; `shell/sidecar/upload_workspace_store.py` 102–109, 140–177, 348–392, 464–514; `shell/sidecar/upload_session.py` 89–98, 439–533, 552–612; `shell/sidecar/upload_adapter.py` 489–495, 1609–1659, 1861–1920, 2094–2170, 2137–2250; `command_registry.py` 226; `providers/nam_dinh.py` 31–33; renderer `client.js` 24, 77–96, 373–425, 633–637, 688+; `state.js` 87–88, 262–265, 316–344; `scan-upload.js` 182–194, 269–284, 356–360, 413–427, 487–497; `index.js` 607–649.

## Plan Change Log

- 2026-10-15 (plan review trước checkpoint): A1–A6/E1–E2 cho thấy dòng matrix `finish_review`/`session_close` mơ hồ và thiếu ranh giới tài nguyên/`queue_revision`, `uploaded_success` cũ, ngữ nghĩa run A + scan B, suite recovery và bằng chứng smoke. Đã bổ sung Implementation Notes + Verification ngoài `<frozen-after-approval>` (giữ nguyên intent và các bất biến: không xóa/migrate dữ liệu, tiến độ theo run, wire không suy Lưu); tránh implementer đóng tab ở `finish_review`, thêm khóa xuyên run, coi status cũ là bằng chứng Lưu, hoặc tưởng session giả của e2e là bằng chứng thật.

- 2026-10-16 (completion): all six execution items are built within the approved #28 scope; final test/smoke evidence and the renderer-only UI proof are recorded below and in `../tmp/issue-28-implementation/runtime-verification.md`. The separate pre-existing `file_token` UI E2E blocker remains explicitly deferred; no gate was bypassed.

## Review Triage Log

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| A1 `finish_review` vs `session_close` | accepted | patch (giải nghĩa ngoài frozen block) | §6.5 chỉ release `waiting_on=review` + `review_finished`; §6.7 mới `closed: true` + id tài nguyên. |
| A2 tab đóng/unknown + queue_revision/refetch | covered | — | §6.6 tabs chỉ `open/closed/unknown`; §3 rule 2 poll không tăng revision; refetch giữ cơ chế hiện có. |
| A3 legacy `uploaded_success` | covered | — | `QUEUE_STATUSES` (`playwright_uploader.py` 81–83) không chứa `uploaded_success`; upsert theo file khi quét lại; không migrate. |
| A4 run A chờ review + scan B | covered | — | §6.14 timeout 60'; `upload_prepare_v1` kiểm `record_ids ⊆ run` → `scope_violation`; `workflow_busy` theo active jobs/open tabs. |
| A5 thiếu `test_upload_recovery.py`; `npm test` chỉ Node | accepted | patch (Verification) | `shell/package.json` `node --test test/*.test.mjs`; suite Python gọi riêng theo `shell/README.md`. |
| A6 field delta Save | accepted | patch (Implementation Notes) | §6.6/§6.7/§6.14 chỉ tài nguyên + tiến độ; schema cũ giữ nguyên. |
| E1 finish_review không đóng tab | accepted | trùng A1 | Cùng evidence §6.5/§6.7. |
| E2 smoke phải là engine thật, không phải fallback | accepted | patch (Verification) | e2e dùng `PortalBrowserSession` (fake) trong `shell/test/fixtures/upload_portal.py`. |
| Code hiện trái predicate của plan | covered | — | Đã ghi trong Approach/Code Map; không phải finding mới. |
| `upload.reconcile` trả `validation_error` hay `command_unknown`; "latest-run" binding | out-of-scope | — | Contract §10 chỉ yêu cầu command/capability đã bỏ bị từ chối; không thêm cơ chế mới. |
| Q1 `test_upload_browser_workflow.py:609` uses run B with old A ids, not a real-file move | medium | patch | Fixed with same-file upsert and an explicit A-command check; the 40-test `test_upload_browser_workflow.py` run passed, including the same-file rescan regression. |
| Q2 `store_job_dict(dict(row))` exposes legacy `verified_record_ids` from existing DB rows | low | patch | Fixed with an explicit job projection; all 17 recovery tests passed, including `test_legacy_save_column_is_hidden_and_data_preserved`, confirming the legacy DB value remains stored but is hidden from output. |
| Q3 Removing shell-chrome source CSS/HTML/token-regex and bare-not-throw assertions loses coverage | false | rejected | The engineering cleanup rule requires deleting incidental-behavior tests and forbids repinning them; tooltip behavior remains and no runtime code changed. Do not restore the forbidden checks. |
| Post-patch Quick review (2026-10-16) | clean | — | Parent confirmed Q1/Q2 patches and Q3 disposition; no remaining finding. |

**Separate pre-existing blocker (deferred, not a quick-review finding):** `shell/src/renderer/upload/index.js:488-492,548` drops `file_token`; `shell/src/main/ipc.js:68-109` `resolveFileTokens` rejects raw paths without a valid token. It is recorded at `_bmad-output/implementation-artifacts/deferred-work.md:70-72`, with copied UI blocker logs in `_bmad-output/tmp/issue-28-implementation/`.


## Design Notes

`prepare` chỉ nhận trạng thái tiền-chuẩn bị trong `run_id` hiện tại nên ID đã chuẩn bị không quay lại lô sau; quét lại B trên cùng file chuyển row sang run mới — "Tiếp tục" trên A bị binding run/scope từ chối (không tự chuẩn bị lại), chọn lại ở B là đường hợp lệ. `open_tabs` vẫn là tài nguyên cho `workflow_busy`/`session_close`; `queue_get` vẫn hiển thị row đã chuẩn bị, chỉ `prepare` lọc.

## Verification

**Commands:**
- Smoke chính (bắt buộc trước review/complete): engine thật + Playwright browser thật; được dùng một portal fixture chạy localhost với selectors thật, nhưng **không** dùng session/engine giả như `PortalBrowserSession`; không cần portal thật/production hay dữ liệu thật -- prepare 10, Lưu 3, đóng 2 tab chưa Lưu, bấm Tiếp tục chỉ mở hồ sơ chưa chuẩn bị; edge prepare A → scan B → Tiếp tục A = `scope_violation`, không mở tab mới.
- `& $env:G1_PYTHON test/test_upload_e2e.py --case upload` (cwd `shell/`) -- lớp bổ sung (fixture `PortalBrowserSession` là fake): cùng kịch bản.
- `& $env:G1_PYTHON test/test_upload_browser_workflow.py`; `& $env:G1_PYTHON test/test_upload_recovery.py`; `npm test` (cwd `shell/`, chỉ chạy Node `test/*.test.mjs`) -- pass, shape tài nguyên.
- `.\.venv\Scripts\python.exe -B -X utf8 -m pytest tests/ -q -p no:cacheprovider` (cwd `upload_lab/`) -- pass.

**Execution evidence and current blocker (2026-10-15):**
- Good worker reports the mandatory prepare 10 / Save 3 / close 2 / continue 2 / restart 0 smoke passed with the actual `NamDinhUploaderSession` and no overrides. Its observed JSON output is copied to `../tmp/issue-28-implementation/real-engine-upload-sot-smoke.json`; this worker did not run the smoke.
- **UI E2E remains blocked; the gate is not bypassed.** `pickExcel` omits `file_token` while constructing `state.excelFile` (`shell/src/renderer/upload/index.js:488-492`), and `pickFolder` stores only path/scope, also dropping the token (`:548`). The downloaded references reportedly expose raw paths without `file_token`, so this real UI flow cannot pass until the pre-existing renderer/reference mismatch is addressed.
- **UI E2E: BLOCKED, not passed; not rerun.** The known `file_token` picker/download mismatch is recorded above and in deferred work; no gate was bypassed.

**Manual checks (if no CLI):**
- Không có CLI: chạy đúng smoke chính ở trên bằng tay trên máy, cùng kịch bản và cùng edge A/B.

## Completion record — 2026-10-16

- `status: built` (not `done` or published); `created` remains `2026-10-15`. All six Execution items are complete.
- **Post-patch Quick review:** clean; source remains pinned and `lenses_ran` remains `['quick']`. Q1/Q2 patches are retained; Q3 remains rejected under the cleanup rule.
- **Final verification, before this docs-only closeout:** actual `NamDinhUploaderSession` smoke, prepare 10 / manual Save 3 / close 2 / continue 2 / restart 0; shell Python suites 40/17/22/27/27/20; `npm test` 397/397; Upload Lab pytest 424 passed, 2 skipped, 68 subtests; upload workflow validator 53 files with 0 unexpected outcomes. Full recorded commands/results are in `../tmp/issue-28-implementation/runtime-verification.md`. No tests were rerun for this documentation-only finalization.
- **Renderer-only UI proof:** real Chromium rendered the current `G1_UPLOAD.buildView` with production renderer scripts/styles and in-memory test snapshots. The portal line changed from 10 open to 8 open / 2 closed; rows 101–103 remained visible; review-wait appeared until Finish, which left the 8/2 resource counts unchanged. No save/reconcile outcome banner appeared. This is not Electron IPC, sidecar, engine-smoke, or E2E proof. Screenshots and scenario log are in `../tmp/issue-28-implementation/upload-ui-proof-scenario.json` and adjacent PNGs.
- **UI E2E remains BLOCKED, not passed:** `pickExcel` (`index.js:488-492`) and `pickFolder` (`:548`) omit `file_token`; `resolveFileTokens` rejects raw paths. The pre-existing mismatch remains deferred at `_bmad-output/implementation-artifacts/deferred-work.md:70-72`; it is not claimed fixed and no gate was bypassed.

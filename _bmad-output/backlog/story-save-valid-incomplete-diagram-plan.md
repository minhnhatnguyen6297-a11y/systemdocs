---
title: 'Lưu và mở lại sơ đồ hợp lệ còn thiếu dữ liệu'
type: 'feature'
ticket: 5
created: '2026-10-16'
status: 'built'
baseline_revision: 'e4f97ce5ec0d19cc50516b2cf86497ac830a38be'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/notary_v2/diagram-rules.md'
  - '{project-root}/contracts/notary-case-drafting.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Owner đã chốt 15/10/2026: sơ đồ cấu trúc hợp lệ nhưng `incomplete` được lưu làm nháp kèm cảnh báo và hiển thị rõ phần thiếu; sơ đồ `invalid` không được persist. Backend `save_diagram` hiện gọi engine thô nên bỏ mất wrapper thêm cảnh báo Pool/hạ `status: incomplete`, persist cả khi engine trả `invalid` (ví dụ mọi `ownPositions` rỗng → `missing_land_owner`), và UI chỉ thấy phần thiếu sau khi bấm `Xem cách tính` — bản lưu/mở lại mất cảnh báo và phần thiếu không hiện ngay.

**Approach:** `save_diagram` dùng đúng một đường đánh giá với `evaluate` (wrapper `_evaluate_inheritance`) và từ chối `invalid` trước khi ghi (rollback giữ nguyên state/revision). Mock adapter giữ parity. UI thêm cue chỉ-đọc (trạng thái + `requiredSlots` + lỗi engine) trong vùng cảnh báo sẵn có khi panel `Xem cách tính` đóng — không tự sinh slot, không mutate graph, không dirty. `commit_stage` dùng cùng wrapper để giữ bất biến "render_model đã lưu = kết quả evaluate".

## Boundaries & Constraints

**Always:** Giữ state canonical, ID field/slot, `row_id`/`personId`, revision, nguồn và metadata; save atomic; `invalid` không persist (rollback; lỗi `diagram_invalid_state` + `details.errors`); `incomplete` vẫn lưu kèm `requiredSlots`/warning; `two_party` unsupported vẫn lưu canonical 30 slot không cổng mới; chỉ `Xem cách tính` (`runEvaluate`) sinh slot như cũ; cue UI chỉ-đọc trong container cảnh báo hiện có, dùng catalog lỗi hiện có.

**Never:** Không đổi schema/wire/contract/engine rule; không thêm mã lỗi mới; không auto-evaluate hay tự sinh slot khi mở/lưu; không thêm export/hook mới giữa view; không đổi điều kiện Word (không chặn chỉ vì `incomplete`); không đụng `.agent/`, `docs/` hay file người dùng; không commit trước Quick review của parent.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Save incomplete | Đồ thị tính được, còn người Stage chưa gán | OK, `revision+1`; `render_model.status="incomplete"` + `diagram.unassigned_pool_person`; mở lại giữ requiredSlots/warning | — |
| Save engine-invalid | Wire hợp lệ, mọi `ownPositions` rỗng (`missing_land_owner`) | Từ chối trước khi ghi; `case_state_json` + `workspace_revision` không đổi | `diagram_invalid_state`, `details.errors` là lỗi engine |
| Save two_party | 30 slot canonical | OK, `render_model.status="unsupported"`, `revision+1`, không cổng | — |
| Mở lại case incomplete (panel đóng) | `render_model` đã lưu có `requiredSlots` | Graph giữ nguyên từng node/id/personId, `diagramDirty=false`; cue chỉ-đọc hiện trạng thái + phần thiếu | — |
| Bấm `Xem cách tính` | Như cũ | Evaluate + sinh slot `requiredSlots` như hành vi hiện hành | — |
| `commit_stage` có người chưa gán | Stage đổi, diagram không dirty | `render_model` đã lưu có warning Pool + incomplete (khớp evaluate) | — |

</frozen-after-approval>

## Code Map

- `notary_v2/services/inheritance_workspace.py` — `save_diagram` (:402; raw call :480-483; persist :499-529) phải dùng `_evaluate_inheritance` (:551-590) như `evaluate_diagram` (:339) và `evaluate_draft` (:392); rollback `WorkspaceError` (:532-537).
- `notary_v2/services/case_workspace.py` — `commit_stage` raw engine call (:1169-1172) cùng lớp lỗi; `create` đã dùng wrapper (:1444-1446) làm tiền lệ; `get`/`_render_model` đọc payload đã lưu (:955, :1000-1003, :2025-2029).
- `notary_v2/services/inheritance_engine.py` — `status invalid` khi `missing_land_owner` (:70-81, :232-249); `isLandOwner := ownPositions ≠ []` (`_v3_to_v2_nodes`, `case_workspace.py:740-753`).
- `shell/sidecar/notary_mock_adapter.py` — `_render` (:567-658) đã có warning Pool/incomplete và `missing_land_owner`; `diagram_save` (:1858-1905) thêm cổng parity.
- `shell/src/renderer/notary/relationship-diagram.js` — vùng cảnh báo `diagramRegionEl` (:1243-1284, block `extra`); map nhãn trạng thái trong `calcPanelEl` (:992-995); `slotTag` (:355-361); `runEvaluate` (:308-316) / `applyRequiredSlots` (:542-612) giữ nguyên.
- `shell/src/renderer/notary/error-catalog.js` — entry `diagram_invalid_state` (:~118) + mã engine (`missing_land_owner` :~170) tái dùng qua `relErrText`.
- Tests: `notary_v2/tests/test_inheritance_workspace.py` (save :409+; invalid :564; reload :611), `shell/test/test_notary_adapter_contract.py` (:603 `_committed_case`, :738 save), `shell/test/test_notary_mock_adapter.py`, `shell/test/notary-diagram.test.mjs` (:400, :572), `shell/test/notary-diagram-errors.test.mjs` (:170 evaluate, save-side thiếu).

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/specs/notary_v2/diagram-rules.md` — ghi hành vi hiện hành: save dùng cùng kết quả evaluate, từ chối `invalid`, UI hiển thị trạng thái/requiredSlots chỉ-đọc khi panel đóng — spec trước code.
- [x] `notary_v2/services/inheritance_workspace.py` — `save_diagram` gọi `_evaluate_inheritance(clean_state, valid_row_ids=valid_rows, people=composed.people)`; cổng `status == "invalid"` → `WorkspaceError("diagram_invalid_state", details={"errors": render_model.get("errors") or []})` trước mọi ghi.
- [x] `notary_v2/services/case_workspace.py` — `commit_stage` gọi wrapper với `people=[{"row_id": rid, "ngay_chet": wire.get("ngay_chet")} ...]`; không thêm cổng.
- [x] `shell/sidecar/notary_mock_adapter.py` — `diagram_save` trả `diagram_invalid_state` khi `_render` cho `status == "invalid"` (parity, cùng shape details.errors).
- [x] `shell/src/renderer/notary/relationship-diagram.js` — cue chỉ-đọc trong `diagramRegionEl` (guard `!isTp() && !calcOpen`): dòng trạng thái tái dùng nhãn của `calcPanelEl`, mỗi `requiredSlots` một dòng "cần bổ sung", lỗi engine qua `relErrText`; không mutate model, không gọi evaluate.
- [x] Tests: `notary_v2/tests/test_inheritance_workspace.py`, `shell/test/test_notary_adapter_contract.py`, `shell/test/test_notary_mock_adapter.py`, `shell/test/notary-diagram.test.mjs`, `shell/test/notary-diagram-errors.test.mjs` — các ca matrix trên, fail-first ở service/adapter.
- [x] Real Electron smoke (service thật + SQLite tạm riêng): save/reopen incomplete, invalid reject, two_party; giữ log/ảnh dưới `_bmad-output/tmp/`.
- [x] Sau proof: cập nhật handbook/`docs` hiện có liên quan (product-overview, backlog tracking) — chỉ khi hành vi đã chứng minh.

**Acceptance Criteria:**
- Given sơ đồ inheritance tính được nhưng còn người Stage chưa gán, when lưu rồi đọc lại bằng session mới, then `render_model` đã lưu có `diagram.unassigned_pool_person`, `status="incomplete"`, `requiredSlots`; UI hiện cue khi panel cách tính đóng.
- Given wire hợp lệ nhưng mọi `ownPositions` rỗng, when lưu, then bị từ chối `diagram_invalid_state` với `details.errors` có `missing_land_owner`; state cũ + revision giữ nguyên, mở lại thấy bản cũ.
- Given mở lại case có `requiredSlots` đã lưu mà không bấm `Xem cách tính`, when xem sơ đồ, then từng node/id/personId giữ nguyên, không slot mới, `diagramDirty=false`; cue hiện phần thiếu.
- Given `two_party`, when lưu, then thành công 30 slot canonical, `status="unsupported"`, `revision+1`, không cổng mới.
- Given Stage được Cập nhật với người chưa gán, when mở lại, then `render_model` đã lưu khớp kết quả evaluate (warning Pool + incomplete).
- Given save lỗi invalid, when UI xử lý, then giữ formatter #4: lỗi dưới sơ đồ qua `relErrText`, không toast riêng, draft/revision giữ nguyên.

## Implementation Notes

- 2026-10-16: Owner waiver áp dụng (continuous; không cần duyệt plan riêng), plan vào `ready-for-dev` và triển khai ngay. Parent-led independent Quick review được phép và hoàn tất trước commit; ghi chú cũ “no spawn review/agent” là giới hạn ownership của child task, không phải lệnh cấm từ owner.
- Baseline ghi trước code: `e4f97ce5ec0d19cc50516b2cf86497ac830a38be` (HEAD, nhánh `autoresearch/session-20261015`; untracked `.agent/`, `docs/` là của người dùng — không đụng).
- 2026-10-16 (implement): `save_diagram` dùng `_evaluate_inheritance` + cổng `invalid` (`diagram_invalid_state.details.errors`, rollback giữ state/revision); `commit_stage` cùng wrapper (counterexample `test_workspace_commit_stage_keeps_unassigned_pool_warning`); mock adapter thêm cổng parity; UI cue chỉ-đọc trong `diagramRegionEl` (tách `CALC_STATUS_LABEL`; không mutate draft, không gọi evaluate).
- Phát hiện + sửa lỗi có sẵn cùng vùng: `applyRequiredSlots` khai báo vợ/chồng một chiều → wire `spouse_conflict` chặn evaluate/save sau khi engine sinh slot (tái hiện qua service: state sau sinh slot → `diagram_invalid_state ['spouse_conflict']`). Sửa: mirror cả hai phía; thêm assert 2 chiều trong test `requiredSlots` (fail-first trước sửa).
- Smoke Electron thật (service thật, không mock, `G1_NOTARY_DATA_DIR` tạm): 21/21 check PASS, node exit 0. S3 dùng "bỏ dấu Chủ đất" (bỏ gán owner làm `stageDirty` → nút Lưu bị gate đúng thiết kế, không phải lỗi #5). Toast `engine_unavailable` khi mở danh sách là transient (case_list tự retry) — ghi trong `evidence.startupToasts`, không che.
- Harness (temporary, gitignored): watchdog 8 phút, exec/taskkill/close có timeout, ghi evidence trước cleanup, force-kill chỉ PID do harness spawn; ảnh `*-cue.png` chụp vùng cảnh báo sau khi cuộn. Owner đã xóa cả bốn script tạm sau khi proof; không script throwaway nào được commit.
- Bằng chứng: `_bmad-output/tmp/story-save-valid-incomplete-diagram/evidence/{result.json,shots/,main.log,run2-stale-hang.log}`.
- Môi trường: `word_templates/` tồn tại dưới `notary_v2/`; các test dùng path tương đối theo CWD. Lần chạy từ repository root `D:/systemdocs` báo 3 lỗi thiếu `word_templates` do CWD sai, không phải bằng chứng lỗi có sẵn. Full Notary chạy từ `D:/systemdocs/notary_v2` đạt 1115 passed, 2 skipped.

## Plan Change Log

## Review Triage Log


- 2026-10-16 (independent Quick t3, Q1 low/patch): renderer bỏ sót dòng trạng thái `Hoàn chỉnh` khi render model đã lưu chuyển sang `complete`. Đây là omission trong thay đổi hiện tại, không phải stale-cue bug có sẵn. Guard JS tối thiểu và transition UI test đã sửa; review cuối **CLEAN (no findings)**. Renderer fixture probe: 4 pass; smoke Electron/service thật: 21/21 pass; parent đã xem ảnh fixture complete.

## Design Notes

Cue chỉ-đọc đặt trong `extra` của `diagramRegionEl` (cùng chỗ hint ngày mất/warnings/errors) nên tự hiện lại sau save (model emit) và sau mở case (`applyWorkspace` set `renderModel`) — không cần wiring mới, không có vòng auto-evaluate, mở lại giữ nguyên graph (khác phương án tự `applyRequiredSlots` khi mở: mutate canonical mới lưu và bật dirty trái yêu cầu).

`commit_stage` được đổi cùng wrapper vì counterexample thật: thêm người vào Stage → `Cập nhật` → `render_model` lưu từ engine thô (mất `diagram.unassigned_pool_person`), diagram không dirty nên `Lưu sơ đồ` không chạy bù; mở lại/evaluate lệch bất biến. Không thêm cổng invalid ở đường này (tránh chặn Stage mới).

Cổng invalid dùng mã sẵn có `diagram_invalid_state` (contract §9: "state sai cấu trúc/engine reject", `details.errors`) nên UI #4 giữ nguyên: lỗi hiện dưới sơ đồ, không toast riêng, draft giữ.

Ngoại lệ `two_party` unsupported là hành vi cố ý, không bị cổng mới — bằng chứng nguồn: nhánh `else` của `save_diagram` trả `unsupported_render_model()` (`notary_v2/services/inheritance_workspace.py:515-518`; shape `case_workspace.py:801-813` gồm warning `diagram.two_party_unsupported`), contract §13.5 "diagram_save/workspace_commit_stage persist + structural validate như thường" (`contracts/notary-case-drafting.md:1301-1305`), test thật `test_diagram_save_two_party` (`shell/test/test_notary_adapter_contract.py:814+`) và `test_save_two_party_canonical` (`notary_v2/tests/test_inheritance_workspace.py:535+`), mock `_unsupported_render` (`shell/sidecar/notary_mock_adapter.py:1881-1882`). Cổng chỉ khớp `status == "invalid"`, không đụng `unsupported`; Word readiness giữ nguyên.

## Verification

**Commands and results:**
- Full Notary, from `D:/systemdocs/notary_v2`: `cmd.exe /c "set PYTHONPATH=D:/systemdocs&& D:\systemdocs\notary_v2\venv\Scripts\python.exe -m pytest tests -q --basetemp D:\systemdocs\.tmp\p5fullfinal"` — **1115 passed, 2 skipped, 115 warnings, 2 subtests passed** (241.76s). This preceded the renderer-only Q1 patch; Python production/tests stayed unchanged and the full suite was not rerun after it.
- Targeted Notary workspace, from `D:/systemdocs/notary_v2`: `cmd.exe /c "set PYTHONPATH=D:/systemdocs&& D:\systemdocs\notary_v2\venv\Scripts\python.exe -m pytest tests/test_inheritance_workspace.py -q --basetemp D:\systemdocs\.tmp\p5-inheritance-final-20261016"` — **41 passed** (23.59s).
- Shell adapter contract + mock adapter, combined from `D:/systemdocs`: `cmd.exe /c "set PYTHONPATH=D:/systemdocs&& D:\systemdocs\notary_v2\venv\Scripts\python.exe -m pytest shell/test/test_notary_adapter_contract.py shell/test/test_notary_mock_adapter.py -q --basetemp D:\systemdocs\.tmp\p5-shell-final-20261016"` — **239 passed, 2 skipped, 32 warnings** (47.04s).
- Diagram UI, from `D:/systemdocs`: `cmd.exe /c "node --test shell/test/notary-diagram.test.mjs shell/test/notary-diagram-errors.test.mjs"` — **30 passed, 0 failed, 0 skipped** (989.4227ms).
- Real Electron/service smoke — **21/21 checks passed**; independent Quick final `t3` **CLEAN (no findings)**.

**Manual checks (if no CLI):**
- Mở lại case incomplete: graph giữ nguyên node/personId, cue hiện trạng thái + phần thiếu khi panel đóng; bấm `Xem cách tính` mới sinh slot.

# Handoff — MIN-112

## Trạng thái khi bàn giao — 2026-10

Xong toàn bộ phạm vi MIN-112 (nối Intake/Stage/Diagram/Word + opaque
file token + dirty guard + mock case_list parity). Branch
`minhnhatnguyen6297/min-112-frontend-noi-intake-stage-diagram-va-word-export`,
base MIN-111 `6aa74bf`. Chưa tạo PR — chờ review.

## File đã đổi

**Mới:**
- `shell/src/main/file-tokens.js` — token store `issue/resolve/clear` +
  `pickedEntry` (shape renderer không path/scope).
- `shell/src/renderer/notary/intake-dialog.js` — dialog Nhập dữ liệu
  (picker filters, drop-zone qua webUtils, paste text, per-source
  status, progress+cancel, review cards).
- `shell/src/renderer/notary/relationship-diagram.js` — Pool + sơ đồ
  (search, drag/drop + menu "Gán vị trí", SVG edges, alloc badge,
  debounce evaluate 500ms, "Xem cách tính" verbatim engine).
- `shell/src/renderer/notary/word-export-dialog.js` — options checkbox,
  dir token pick, progress+cancel, per-doc result rows.

**Sửa:**
- `shell/src/main/ipc.js` — `resolveFileTokens` đệ quy, handler
  `registerDroppedFile` (`data:{file}`) + `setDirtyState`, export
  `resolveFileTokens` cho test.
- `shell/src/main/main.js` — pickFiles trả token; drop register; token
  clear closed/navigation/quit; close-guard active-jobs OR
  rendererDirty; reset dirty khi reload.
- `shell/src/preload/preload.js` — `registerDroppedFile` qua
  `webUtils.getPathForFile`, `setDirtyState`.
- `shell/src/renderer/renderer.js` — engine/upload view đổi sang
  `file_token`; `runner.run(cmd,payload,opts)` → `opts.onJob` sau submit
  + mỗi poll + terminal; notary view ctx (`registerDroppedFile`,
  `cancelJob`, `onUnsavedChange`→`setDirtyState`); `canLeave` guard.
- `shell/src/renderer/notary/case-drafting-model.js` —
  `onUnsavedChange` từ emit; `intakeAnalyze`/`exportWord` nhận `opts`
  (onJob); suggestion PREPEND; `intakeErrors` tích lũy;
  `user_canceled`→notice; `normalizeWordResult` (full/compact/skipped
  synthesis).
- `shell/src/renderer/notary/case-drafting-view.js` — mount 3 pane qua
  `G1_NOTARY_*`; field_errors per-field; openModal focus-trap; tray
  suggestion.
- `shell/src/renderer/notary/case-drafting.css` — `.cd-field-err`,
  dropzone/badge/calc/word/edge styles (edge-row padding, không
  min-height <40px).
- `shell/src/renderer/index.html` — load 3 file notary mới trước
  renderer.js.
- `shell/sidecar/command_registry.py` — `notary.case_list` route qua
  `_notary_drafting` gateway.
- `shell/sidecar/notary_gateway.py` — docstring.
- `shell/sidecar/notary_mock_adapter.py` — `case_list` +
  `_mock_case_row` parity `_case_row` real adapter.
- Tests: `test/ipc.test.mjs` (token store, resolve đệ quy, reject, 2
  handler mới), `test/notary-case-drafting-model.test.mjs` (opts
  passthrough, prepend, canceled notice, normalize word result),
  `test/notary-case-drafting-static.test.mjs` (invariants file_token,
  dialog files, debounce, close guard), `test/test_notary_mock_adapter.py`
  (case_list shape + query filter).
- `.agent/tasks/MIN-112/{progress,decisions,handoff}.md`.

## Cách verify

```powershell
cd D:\systemdocs-min-112\shell
npm test                                        # 100/100
node --test test/ipc.test.mjs                   # 15/15
D:\systemdocs\notary_v2\venv\Scripts\python.exe -m pytest `
  test/test_notary_mock_adapter.py test/test_notary_adapter_contract.py -q
                                                # 100 passed
cd D:\systemdocs-min-112
D:\systemdocs\notary_v2\venv\Scripts\python.exe `
  contracts\notary-case-drafting\validate_examples.py
                                                # 34 files, 0 unexpected
```

Smoke tay (chưa chạy trong phiên): `cd shell; $env:G1_DEV_NOTARY_MOCK=1;
npm start` → Tổng quan mở case 42 → Nhập dữ liệu (dán text) → Đưa vào
Stage → Cập nhật → gán Pool lên sơ đồ → Đánh giá thử → Lưu sơ đồ →
Xuất Word chọn thư mục → xem per-doc result.

## Việc còn lại / rủi ro

- Smoke Electron thật chưa chạy (không có desktop trong phiên) — nên
  chạy trước merge; các đường token/drop chỉ kiểm chứng unit+static.
- Tab "Word" trong local nav vẫn placeholder có hướng dẫn (spec §1 —
  surface văn bản lát cắt sau); entry xuất Word ở Soạn hồ sơ → Xuất
  Word.
- Intake re-run bỏ qua nguồn đang 'lỗi' (user xóa/thêm lại để retry) —
  chủ động, không phải bug.
- `did-start-navigation` reset dirty: reload dev mất draft KHÔNG cảnh
  báo — draft vốn in-memory (spec), không phải regression.

## File tạm đã dọn

- Không tạo file scratch; output test chỉ đọc, không ghi repo.

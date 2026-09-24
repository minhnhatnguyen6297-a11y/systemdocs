# Progress — MIN-111

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: xong — 2026-09-26 (đã commit)

## Đã làm
- TDD đỏ: viết `shell/test/notary-case-drafting-model.test.mjs` trước —
  fail đúng vì module chưa tồn tại.
- `shell/src/renderer/notary/case-drafting-model.js` — pure state machine
  UMD/CommonJS, inject `client.run(command, payload)`, không DOM:
  load workspace, stageDirty/diagramDirty tách, commit/save giữ draft khi lỗi,
  fieldErrors theo row_id, conflict → status conflict + server_revision,
  Pool = Stage committed − assignment Diagram, locked chặn write nhưng cho
  evaluate, mock banner "Dữ liệu mô phỏng", unsupported → "Chưa hỗ trợ",
  intake suggestion chỉ vào draft (không auto-commit), word options/export
  dạng data — không JSON thô.
- `shell/src/renderer/notary/case-drafting-view.js` — view classic-script
  `window.G1_NOTARY_VIEW.createNotaryModuleView(deps)`; local nav 3 tab
  (Tổng quan hồ sơ / Soạn hồ sơ / Word); layout Stage trên (Tài sản/Người
  ~36/64), Pool/Diagram dưới (~22/78); faces loading/empty/error/locked/
  conflict/unavailable + mock banner; menu "Gán vị trí…" là thay thế bàn
  phím cho kéo-thả; devQuickOpen chỉ hiện khi `window.G1_DEV` (không input
  ID trong production); không Zalo, không JSON thô.
- `shell/src/renderer/notary/case-drafting.css` — tokens + layout; mọi
  control ≥44px (`--cd-tap`), `:focus-visible` rõ.
- `shell/src/renderer/index.html` — link CSS + 2 script notary trước
  renderer.js.
- `shell/src/renderer/lib.js` — `NAV_SPEC` mới 5 mục theo taxonomy
  (notary_v2/upload_lab/notaryoffice + Tra cứu + Trạng thái/Cài đặt);
  `navEntry` hỗ trợ `aliases` — `document-review` route sang `notary_v2`.
- `shell/src/renderer/renderer.js` — `buildNotaryView` (model + view +
  `canLeave` dirty guard); `makeCommandRunner` seam (submit → awaitJob →
  {ok,data}|{ok,error}); bỏ `buildDocReviewView`/`buildExcelWord`/
  `buildOverview`; health+jobs gộp vào `buildStatus`; default module
  `notary_v2`; `showModule` async + canLeave.
- `shell/src/renderer/styles.css` — button/input/select/textarea min-height
  44px, `:focus-visible` toàn cục, `#view section.cd-root-outer` bỏ
  max-width 860px.
- `shell/src/main/registry.js` — bỏ namespace `zalo` khỏi document-review;
  giữ `document-review` + `excel-word` cho compat.
- Tests: `notary-case-drafting-static.test.mjs` mới; `navigation.test.mjs`
  + `state-faces.test.mjs` cập nhật taxonomy (zalo.status giờ bị
  command_unknown — đúng MIN-103 tách Zalo).

## Đang làm dở
- Không còn — chỉ commit.

## Bước tiếp theo
- Commit `feat(shell): build notary case drafting workspace layout`.
- MIN-112: nối backend thật (seam `makeCommandRunner` đã sẵn — mock qua
  `G1_DEV_NOTARY_MOCK=1`).

## Vá review findings — 2026-09-26 (commit tiếp theo)

Đã vá:
- **#1 locked/unsupported vẫn ghi được (Important)**: view disable hết nút
  write khi `!canWrite()` — `Nhập dữ liệu`/`+ Tài sản` (card Tài sản),
  `Nhập Excel`/`OCR giấy tờ`/`+ Người` (card Người), nút `Xuất` trong
  word dialog (`word_export_batch` là write theo §5.3). Model thêm guard
  `canWrite()` vào mọi draft mutation (defense-in-depth): `addPerson`,
  `addAsset`, `updatePersonField`, `updateAssetField`, `removeStageRow`,
  `addSlot`, `assignPerson`, `setNodeFlag`, `setNodeRelation`,
  `removeNode`, `acceptSuggestion` → no-op / trả null|false.
  `discardSuggestion` cố tình KHÔNG chặn — tray session-local, cần dọn
  được cả khi case vừa bị khóa giữa chừng.
- **#2 openCase phá draft không hỏi (Important)**: `openCaseInDrafting`
  check `model.hasUnsaved()` → `confirm()` (dep đã inject) trước khi
  `model.openCase(id)`; nút `Thử lại` ở face unavailable đi qua cùng
  đường guard. `resolveConflict('reload')` giữ nguyên — user đã chọn
  "Tải bản mới" trong dialog.
- **#3 full rebuild mất focus + expanded row (Important)**: view giữ
  `openRowIds` (Set row_id, cập nhật trong head onclick, prune khi row
  không còn trong draft), re-apply `.cd-row.open` + `aria-expanded` sau
  mỗi rebuild. `rerender()` skip hoàn toàn phần rebuild `panels.drafting`
  khi `document.activeElement` nằm trong `.cd-row-detail` — emit nền
  (jobUpdate/status poll → `view.refresh()`) không đè input đang gõ;
  tab/panel hidden-state vẫn cập nhật.
- **#4 applyWorkspace leak aux state giữa case (Important)**: reset thêm
  `suggestions`, `intakeErrors`, `intakePartial`, `intakeBusy`,
  `wordOptions`, `wordResult`, `wordBusy`, `evaluatedRevision`, `notice`,
  `busy` (đã có: `conflict`, `error`, `fieldErrors`, `diagramErrors`,
  `stale`, dirty flags).

Fix nhanh:
- **#5** `state` literal thêm `diagramDirty: false` (trước chỉ có qua
  applyWorkspace/touchDiagram → shape không nhất quán).
- **#6** `commitStage`/`saveDiagram` success path clear `state.error`
  trước khi set `notice` — lỗi cũ không đọng lại cạnh notice thành công.
- **#7** dead code: bỏ `const s` unused trong `personRowEl`/`assetRowEl`/
  `diagramNodeEl`; bỏ onclick thừa bị ghi đè ở row heads (giờ 1 handler
  duy nhất, gộp tracking `openRowIds`); `confirm` dep giữ — giờ đã dùng
  cho #2.
- **#8** handoff.md sửa claim sai: `notary.case_list` route **real
  adapter** (`command_registry.py:193` `_notary` → `notary_adapter.
  case_list`), KHÔNG qua mock gateway; mock chỉ phủ drafting commands cho
  fixture 42–46 qua devQuickOpen/workspace_get.

Defer → MIN-112 (chi tiết trong handoff.md §Deferred):
- M-5 `notary.case_list` mock parity; M-6 app-close dirty guard
  (main.js close handler); M-7 word dialog per-doc progress + cancel.
- Modal focus-trap đầy đủ: defer; đã thêm Escape-dismiss cho mọi
  `openModal` (<10 dòng — đủ điều kiện "fix nhanh nếu <10 dòng").

## Check đã chạy
- `cd D:\systemdocs-min-111\shell && npm test` (node --test test/*.test.mjs)
  → lượt đầu (feature): **75 tests, 75 pass, 0 fail, ~20.7s** (exit 0).
- Sau vá findings: **79 tests, 79 pass, 0 fail, ~20.9s** (exit 0).
  +4 test model mới (TDD đỏ → xanh): locked mutations no-op, unsupported
  mutations no-op, applyWorkspace reset aux state, acceptSuggestion trên
  case locked. Output cuối:

```
ℹ tests 79
ℹ suites 0
ℹ pass 79
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 20868.1709
```

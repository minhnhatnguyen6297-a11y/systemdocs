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

## Check đã chạy
- `cd D:\systemdocs-min-111\shell && npm test` (node --test test/*.test.mjs)
  → **75 tests, 75 pass, 0 fail, duration ~20.7s** (exit 0). Output cuối:

```
ℹ tests 75
ℹ suites 0
ℹ pass 75
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 20683.0368
```

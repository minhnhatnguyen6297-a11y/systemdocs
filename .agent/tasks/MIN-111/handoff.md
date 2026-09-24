# Handoff — MIN-111

## Trạng thái khi bàn giao — 2026-09-26
MIN-111 (frontend khung UI tab Soạn hồ sơ) hoàn thành code + test: 75/75
pass. Chưa nối backend thật — seam `makeCommandRunner` sẵn cho MIN-112;
demo qua mock `G1_DEV_NOTARY_MOCK=1`.

## File đã đổi
- `shell/src/renderer/notary/case-drafting-model.js` (mới) — pure state
  machine UMD; inject client; đủ faces/dirty/conflict/locked/pool-derive.
- `shell/src/renderer/notary/case-drafting-view.js` (mới) — 3 tab local +
  workspace Stage/Pool/Diagram; keyboard alternative cho gán; ARIA đầy đủ.
- `shell/src/renderer/notary/case-drafting.css` (mới) — tokens, ≥44px,
  focus-visible.
- `shell/src/renderer/index.html` — load css + 2 script notary.
- `shell/src/renderer/lib.js` — NAV_SPEC 5 mục + aliases; navEntry resolve
  alias.
- `shell/src/renderer/renderer.js` — buildNotaryView + makeCommandRunner +
  canLeave guard; bỏ buildDocReviewView/buildExcelWord/buildOverview;
  health+jobs → buildStatus; default notary_v2.
- `shell/src/renderer/styles.css` — 44px + focus-visible toàn cục; widen
  cd-root-outer.
- `shell/src/main/registry.js` — bỏ namespace zalo; giữ document-review +
  excel-word compat.
- `shell/test/notary-case-drafting-model.test.mjs` (mới, 23 test),
  `notary-case-drafting-static.test.mjs` (mới, 12 test),
  `navigation.test.mjs` + `state-faces.test.mjs` cập nhật taxonomy.

## Cách verify
- `cd D:\systemdocs-min-111\shell && npm test` → 75 pass / 0 fail (đã chạy).
- Manual: `G1_DEV_NOTARY_MOCK=1` chạy app, nav `notary_v2` → tab
  `Tổng quan hồ sơ` → Tải danh sách (mock case 42-46) hoặc bật
  `window.G1_DEV` trong DevTools để có nút mở nhanh.

## Việc còn lại / rủi ro
- MIN-112: nối backend thật — thay/bổ sung runner; `devQuickOpen` chỉ dev.
- `zalo.*` nay trả `command_unknown` (namespace đã bỏ khỏi registry theo
  MIN-103) — nếu cần zalo trước khi migration xong phải mở lại namespace.
- Conflict dialog mở khi status chuyển conflict; refresh tay là "Tải lại
  bản mới nhất" — UX auto-refresh (nếu muốn) để lát sau.
- Hai tab `Tổng quan hồ sơ`/`Word` mới có khung + danh sách/options cơ bản;
  hoàn thiện nội dung ở MIN-112.

## File tạm đã dọn
- Không có file tạm nào được tạo ngoài `.agent/tasks/MIN-111/`.

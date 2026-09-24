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
- `cd D:\systemdocs-min-111\shell && npm test` → 79 pass / 0 fail (đã chạy
  sau đợt vá review findings).
- Manual: `G1_DEV_NOTARY_MOCK=1` chạy app, nav `notary_v2`, bật
  `window.G1_DEV` trong DevTools → devQuickOpen mở fixture mock 42–46.
- Lưu ý route: mock CHỈ phủ các command drafting (`workspace_get`,
  `commit_stage`, `diagram_*`, `intake_analyze`, `word_export_*`) qua
  `notary_gateway` (`command_registry.py:230-238`). `notary.case_list`
  route vào **real adapter** `notary_adapter.case_list`
  (`command_registry.py:193` — `_notary`, KHÔNG qua gateway) → cần engine
  notary_v2 thật; trên máy thiếu engine, "Tải danh sách" trả lỗi
  `engine_not_installed` và devQuickOpen (G1_DEV) là đường mở mock.
  Mock parity cho `case_list` là việc của MIN-112 (M-5).

## Việc còn lại / rủi ro
- MIN-112: nối backend thật — thay/bổ sung runner; `devQuickOpen` chỉ dev.
- `zalo.*` nay trả `command_unknown` (namespace đã bỏ khỏi registry theo
  MIN-103) — nếu cần zalo trước khi migration xong phải mở lại namespace.
- Conflict dialog mở khi status chuyển conflict; refresh tay là "Tải lại
  bản mới nhất" — UX auto-refresh (nếu muốn) để lát sau.
- Hai tab `Tổng quan hồ sơ`/`Word` mới có khung + danh sách/options cơ bản;
  hoàn thiện nội dung ở MIN-112.

## Deferred → MIN-112 (ghi nhận từ review findings)
- **M-5 — `notary.case_list` mock parity**: case_list đi thẳng real
  adapter; mock gateway không implement. MIN-112 quyết định: thêm
  `case_list` vào mock/gateway hay để real-only.
- **M-6 — app-close dirty guard**: `canLeave` chỉ chặn đổi module trong
  shell; đóng cửa sổ/thoát app (main.js `close`/`before-quit`) chưa hỏi
  khi `hasUnsaved()`. Cần IPC hỏi renderer hoặc `beforeunload`.
- **M-7 — Word dialog: progress per-doc + cancel**: `word_export_batch`
  chạy một job cho cả batch; dialog hiện chỉ show kết quả cuối, không
  cancel giữa chừng, không progress từng văn bản — nằm trong scope
  workflows MIN-112.
- **Modal a11y**: đã có Escape-dismiss cho mọi `openModal` (conflict,
  assign menu, intake, word); focus-trap đầy đủ vẫn defer.
- **Rerender skip khi focus trong `.cd-row-detail`**: emit bị nuốt một
  nhịp khi đang gõ — chấp nhận được (minimum viable); nếu cần render tức
  thì mà giữ focus, làm diff/patch DOM ở lát cắt sau.

## File tạm đã dọn
- Không có file tạm nào được tạo ngoài `.agent/tasks/MIN-111/`.

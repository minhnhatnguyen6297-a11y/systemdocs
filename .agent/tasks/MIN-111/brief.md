# MIN-111 — FRONTEND: Khung UI tab Soạn hồ sơ

Linear: MIN-111 (parent MIN-68). Plan §12 (Task 8).
SOT thiết kế: `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md`
(bố cục §1.2, visual tokens, trạng thái) + `notary_v2/docs/platform/case-workspace/drafting-tab.md`.
Contract: `contracts/notary-case-drafting.md` (KHÔNG sửa — chỉ dùng command đã publish).

## Mục tiêu
Khung Electron cho tab Soạn hồ sơ — dùng Mock Backend (`G1_DEV_NOTARY_MOCK=1`)
để nhìn/thử toàn bộ trạng thái. CHƯA nối backend thật ở issue này.

## Files
- Create `shell/src/renderer/notary/case-drafting-model.js` (pure state, UMD/CommonJS-compatible — chạy được `node --test`, KHÔNG bundler)
- Create `shell/src/renderer/notary/case-drafting-view.js`
- Create `shell/src/renderer/notary/case-drafting.css`
- Create `shell/test/notary-case-drafting-model.test.mjs`
- Create `shell/test/notary-case-drafting-static.test.mjs`
- Modify `shell/src/renderer/index.html`, `renderer.js`, `styles.css`, `lib.js`
- Modify `shell/src/main/registry.js`, `shell/test/navigation.test.mjs`

## Nghiệm thu (Linear + plan)
- Nav chính: 3 module nghiệp vụ `notary_v2`, `upload_lab`, `notaryoffice` (+ Search/Status tiện ích). Bỏ `Excel → Word` khỏi nav chính; giữ `document-review` ID tương thích; chưa xóa command cũ.
- Local nav notary_v2: `Tổng quan hồ sơ` / `Soạn hồ sơ` / `Word` — task này chỉ hoàn thiện `Soạn hồ sơ`.
- Bố cục §1.2: Stage Tài sản/Người trên (ưu tiên 36/64); Pool/Diagram dưới (22/78).
- States đủ: loading, empty, error, locked (read-only), conflict, unavailable, mock banner (`backend_mode=mock` → "Dữ liệu mô phỏng").
- KHÔNG: Zalo, JSON kỹ thuật, nhập ID tay trong production view (debug view sau dev flag OK).
- JS/CSS thuần; không framework/bundler; không chép Bootstrap/ReactFlow web cũ.
- Nút 44px, focus visible, label/aria; kéo thả có nút/menu bàn phím thay thế.

## TDD bắt buộc
Pure-state tests TRƯỚC (fail vì module chưa có): load, dirty Stage,
commit success/fail, derived Pool (Stage committed − Diagram assignment),
draft Diagram, revision conflict, locked read-only, mock banner.
Static tests: nav không chứa `Zalo`/`zalo.status`/input ID kỹ thuật;
không import ReactFlow/Bootstrap; view không render JSON thô.

## Seams đã có
- `shell/src/renderer/` — renderer.js/lib.js/styles.css hiện có (đọc convention trước).
- `shell/src/main/registry.js` — nav registry hiện có.
- `shell/test/*.test.mjs` — node:test pattern hiện có.
- `shell/test/fixtures/notary-case-drafting/` — fixture mock (empty/ready/locked/conflict/...).
- Mock backend commands đã merge — model gọi qua command client hiện có (`command-client.test.mjs` cho pattern).

## Ràng buộc
- Không thêm dependency; không đụng Zalo; không sửa contracts/; không sửa backend Python.
- Không tạo contract/command mới — chỉ dùng 7 command `notary.*` đã publish.
- Không log PII.

## Verify
- `cd D:\systemdocs-min-111\shell && npm test` (node --test test/*.test.mjs)
- Static test chứng minh nav/state đúng nghiệm thu.
- `.agent/tasks/MIN-111/progress.md` + `decisions.md` đầy đủ.

# Progress — MIN-126

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: xong — 2026-09-28 (chờ owner duyệt trên Linear)

## Đã làm

- Đọc SOT: `AGENTS.md`, `docs/product/ui/{DESIGN,EXPERIENCE}.md`,
  `tokens.json`, `references/README.md` + 2 ảnh approved,
  `notary_v2/docs/platform/case-workspace/{visual-design,drafting-tab}.md`,
  `upload_lab/docs/{spec_UI,visual-design}.md`,
  `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md`,
  `contracts/notary-case-drafting.md`, `contracts/upload-workflow.md`,
  renderer tham chiếu `shell/src/renderer/notary/*`, `ReactFlowApp.jsx`.
- Xây bản mẫu độc lập tại `docs/product/ui/prototypes/`:
  `index.html` (shell + thanh demo), `prototype.css` (token ánh xạ tay,
  status proposed), `data.js` (dữ liệu giả deterministic), `app.js` (modal
  focus-trap/trả focus, toast, viewport, dispatch), `notary.js` (Stage
  chuyển vị + Người + Pool + sơ đồ thừa kế/hai bên + dialog loại đất/intake/
  conflict/Word-stub/Mở rộng), `upload.js` (Audit + Quét-upload giữ state).
- `README.md` trong thư mục prototype: cách mở, bản đồ trạng thái, kích
  thước đã kiểm, giới hạn, 11 quyết định chờ chốt.
- Sửa 3 lỗi phát hiện khi duyệt ảnh:
  1. `assignedIds()` đếm cả slot hai bên khi đang ở thừa kế → Pool sai (đã sửa:
     chỉ trừ theo sơ đồ đang hiển thị).
  2. `.audit-pane`/`.ul-panel` không giới hạn chiều cao → bảng 2 audit nằm
     dưới fold (đã sửa: hai pane chia chiều cao, cuộn trong).
  3. `sidesCanvas` (hai bên) `.canvas-scale` absolute → không cuộn được 30 chỗ
     (đã sửa: set height theo nội dung). `openExpanded` bổ sung trả focus +
     zoom đồng bộ trong overlay. `.node-flags` thêm wrap.

## Đang làm dở

- Không còn — chờ owner duyệt + chốt các quyết định mở (decisions.md).

## Bước tiếp theo (cho P4+)

- P4/MIN-127 dùng bản mẫu làm baseline layout/token khi implement Electron UI.
- Owner chốt 11 mục ở `decisions.md` trước khi P4 harden semantics.

## Check đã chạy

- `node --check` 4 file JS — pass.
- Script tương tác `.agent/scratch/p3_test.py` (Playwright, Chromium headless):
  **18/18 PASS** — kéo Pool→node/slot, swap, Gán vị trí keyboard, reorder
  Ctrl+arrow cả hai bảng, splitter chuột+phím, zoom, Esc/trả focus dialog &
  overlay, tab giữ state, 2 pane audit, 60 người, focus-visible 2px.
  Console/page error = 0.
- Chụp 26 ảnh (`.agent/scratch/p3_shot.py`) vào `screenshots/`:
  1366×768, 1280×800, 1920×1080, 1536×864(≈125%), 1280×720(≈150%) + mọi
  trạng thái/dialog — `errors=[]` toàn bộ.
- DPI Windows 125%/150% thật: chưa chạy trên máy Windows scale thật — hai
  viewport trên mô phỏng không gian CSS tương đương; đã ghi hạn chế trong
  README (cần owner xác nhận crispness nếu muốn).

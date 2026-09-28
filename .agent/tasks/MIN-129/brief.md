# Brief — MIN-129

**Linear:** MIN-129 (P6 của MIN-123) · **Ngày bắt đầu:** 2026-09-27 · **Nhánh:** `consolidate/monorepo`

## Mục tiêu
Dựng vùng nhập tài sản/người (Stage) theo bản mẫu đã duyệt, popup loại đất,
và Pool; đồng nhất thanh action (Nhập file / Zalo disabled / Hủy / Cập nhật).
Chi tiết yêu cầu ở Linear — không chép lại vào đây.

## Phạm vi
- Repo/module ảnh hưởng: `shell/src/renderer/notary/`
- File sở hữu:
  - `shell/src/renderer/notary/case-drafting-view.js`
  - `shell/src/renderer/notary/case-drafting.css`
  - `shell/src/renderer/notary/intake-dialog.js`
  - `shell/src/renderer/notary/relationship-diagram.js` — **chỉ phần Pool
    (render/behavior) + nút Lưu sơ đồ/Xuất Word footer**
  - `shell/test/` — mở rộng static test + test view mới
  - `.agent/tasks/MIN-129/*`
- KHÔNG sửa: `case-drafting-model.js`, `styles.css`, `lib.js`, `renderer.js`,
  `index.html`, `word-export-dialog.js`, upload/*, backend, `notary_v2/`,
  `contracts/*`.
- Ranh giới giữ: vùng/diagram canvas trong `relationship-diagram.js` là đất
  của P7/MIN-130 — không đụng node/edges/calc/seed. Pool payload
  `text/plain` `{kind:'person', row_id}` giữ nguyên. Zalo chỉ là nút
  disabled, không kéo engine vào.

## Bằng chứng nghiệm thu
- `cd shell && node --test test/*.test.mjs` — baseline 222 pass + test mới.
- `git diff --check` sạch.
- Bố cục theo `docs/product/ui/references/approved-drafting.png` +
  `approved-land-types.png` ở 1280×800 / 1366×768 / 1920×1080.

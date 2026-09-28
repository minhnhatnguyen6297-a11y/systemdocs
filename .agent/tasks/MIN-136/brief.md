# Brief — MIN-136

**Linear:** MIN-136 · **Ngày bắt đầu:** 2026-09-28 · **Nhánh/worktree:** consolidate/monorepo

## Mục tiêu
UI P11 — Sửa các lỗi nghiệm thu owner báo sau MIN-133: luồng sơ đồ đơn node,
Pool chỉ người, bỏ cột Để lại, danh mục lỗi liệt kê rule ẩn, và các sửa UX
đi kèm (Nhập file trên nháp, +Hồ sơ mới, Hình thức SD, dd/mm/yyyy, canvas
căn giữa). Chi tiết yêu cầu ở Linear — không chép lại vào đây.

## Phạm vi
- Repo/module ảnh hưởng: `shell/` (renderer Notary — model/view/diagram/css/html + tests)
- File dự kiến sửa:
  - `shell/src/renderer/notary/error-catalog.js` (mới)
  - `shell/src/renderer/notary/case-drafting-model.js`
  - `shell/src/renderer/notary/relationship-diagram.js`
  - `shell/src/renderer/notary/case-drafting-view.js`
  - `shell/src/renderer/notary/case-drafting.css`
  - `shell/src/renderer/index.html`
  - `shell/test/notary-*.{test,static,diagram,view,model}.mjs`
- Ranh giới giữ nguyên: contract, backend, Word export, 30 slot two_party,
  legacy 7-slot case cũ vẫn render, Lưu hồ sơ/Cập nhật sync.

## Bằng chứng nghiệm thu
- `node --test test/*.test.mjs` trong `shell/` — toàn bộ xanh.
- Harness Electron `.agent/scratch/w2-harness/render.js` — metrics + PNG.
- Ảnh bằng chứng: `.agent/tasks/MIN-136/shots/`.

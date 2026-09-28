# Brief — MIN-130

**Linear:** MIN-130 (P7 của MIN-123) · **Ngày bắt đầu:** 2026-09-28 · **Nhánh:** `consolidate/monorepo`

## Mục tiêu
Dựng sơ đồ thừa kế (canvas card + edges) và sơ đồ hai bên (30 chỗ
canonical) theo bản thiết kế đã duyệt, trên nền Pool/P6 và model v2 P5.
Chi tiết yêu cầu ở Linear — không chép lại vào đây.

## Phạm vi
- Repo/module ảnh hưởng: `shell/src/renderer/notary/`
- File sở hữu:
  - `shell/src/renderer/notary/relationship-diagram.js` — vùng diagram
    (canvas, node card, edges, two-party slots, zoom/pan/Mở rộng).
    **Pool + khung card + footer giữ nguyên contract P6.**
  - `shell/src/renderer/notary/case-drafting.css` — chỉ phần `cd-*`
    liên quan sơ đồ, scope dưới `.cd-root`.
  - `shell/src/renderer/notary/case-drafting-view.js` — chỉ điểm nối nếu
    bắt buộc (mục tiêu: không sửa).
  - `shell/test/notary-diagram.test.mjs` (mới) + mở rộng static test nếu cần.
  - `.agent/tasks/MIN-130/*`
- KHÔNG sửa: `case-drafting-model.js`, `styles.css`, `lib.js`,
  `renderer.js`, `index.html`, upload/*, backend `notary_v2/`,
  `contracts/*`, word-export.

## Ranh giới giữ
- Drag payload `{kind:'person', row_id}` trong `text/plain` — giữ nguyên.
- `isLandOwner`/`willReceive`/`is_primary` cấm trên wire v2 — không thêm.
- Edges từ `parentSlotIds`/`spouseSlotId` + slot từ `requiredSlots` của
  engine (Python = SOT); JS không tính phần/%, không port rule legacy.
- Pool = committed-only; stageDirty gate cho evaluate/save giữ nguyên.
- Stage trực tiếp sửa nguồn gốc/sinh-mất giữ nguyên (không đụng Stage).

## Bằng chứng nghiệm thu
- `cd shell && node --test test/*.test.mjs` — toàn bộ pass.
- Test mới: 30 slot hai bên, p16 đầu Bên B, swap, về Pool, chip độc lập,
  round-trip save/open qua mock adapter, 60 node vẫn render/thao tác.
- `git diff --check` sạch; `git show --stat` chỉ file sở hữu.

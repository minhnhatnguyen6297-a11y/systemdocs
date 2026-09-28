# Progress — MIN-129

## Trạng thái: đang làm

## Đã làm
- Recon xong: model v2 (`case-drafting-model.js`), view cũ (accordion
  rows + land rows inline), P4 shared styles (`styles.css` + class guide
  trong handoff MIN-127), approved refs (drafting + land-types PNG),
  contract §13.
- Phát hiện API gaps (ghi lại để làm việc xung quanh + đưa vào handoff):
  - `cancelDraft()` **không có** — view sẽ restore `state.stage`/
    `state.diagram` từ `committed`/`committedDiagram` + emit qua
    `model.dismissNotice()`.
  - Reorder people stage **không có** hàm model (`moveAsset` chỉ cho
    asset) — view splice `state.stage.people` + set `stageDirty` + emit.
  - `setNodePositions(nodeId, kind, positions)` không có — chỉ
    `toggleNodePosition` (không cần cho P6, ghi vào handoff).
  - `setOwner` thực tế là `setOwnerRow(rowId)`.
- Mở task record (commit đầu).

## Đang làm dở
- Rewrite `case-drafting.css` theo tokens P4 (xóa dark rail/lime).

## Bước tiếp theo
1. CSS mới (cd-* scoped `.cd-root`).
2. View: actionbar + openModal canonical + cancelDraft + focus-restore
   rerender + syncDirtyUI.
3. Asset transposed table + land dialog.
4. People table + reorder.
5. Diagram: Pool restyle + footer Lưu sơ đồ/Xuất Word + stageDirty gate.
6. Intake dialog canonical modal.
7. Test: cập nhật static + file test view mới (DOM stub).
8. Chạy full suite + `git diff --check` + handoff.

## Check đã chạy
- `node --test test/*.test.mjs` baseline: **222/222 pass**.

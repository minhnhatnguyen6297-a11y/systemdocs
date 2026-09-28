# Progress — MIN-136

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: xong implement + verify — 2026-09-28

## Đã làm

- `error-catalog.js` (mới): danh mục mã lỗi → thông điệp thân thiện + rule ẩn;
  `describeError`/`errText`; load trước model trong `index.html`.
- `case-drafting-model.js`: draft thừa kế seed đúng 1 node `owner`; bỏ export
  `seedDiagramSlots`/`ensureEmptyChildSlot`; `capabilities.intake` đủ 5 loại
  trên nháp; `INTAKE_KINDS` const.
- `relationship-diagram.js`: bỏ `+ Slot`/`Đánh giá thử`/"Tạo sơ đồ mẫu"/menu
  "Con của X"/"Vợ-chồng của X"/thẻ tài sản Pool/`seedBase`; Pool nháp lấy
  `stage.people`; hint chủ đất sống; header còn `Xem cách tính`·zoom·
  `Mở rộng`·`Lưu sơ đồ`·`Xuất Word`; fix `diagramRegionEl` dùng `tp` ngoài
  scope → `isTp()`; đổi `errText`→`relErrText` (xung global với catalog).
- `case-drafting-view.js`: bỏ cột Để lại + radio owner; `Hình thức SD`; ô
  ngày text mask `dd/mm/yyyy` ↔ wire ISO (helper `fmtDisplayDate`/
  `parseDisplayDate`/`dateCellInput`); `+ Hồ sơ mới` ở empty-state;
  `case_list` retry 5×1.5s khi infra error; wire catalog vào field/intake/
  diagram/save errors; fix F-1 (conflict render ngay khi đang gõ).
- `case-drafting.css`: `.cd-canvas-world { margin: 0 auto }` căn giữa;
  `.cd-hint`; sửa comment `*/` giữa dòng (MIN-129) nuốt rule `.cd-diagram`
  → canvas flex-fill đúng.
- Tests: cập nhật model/view/diagram/static theo flow mới; thêm test MIN-136
  (pool nháp, empty-state, date mask, error catalog, hint, F-1, no-export
  seedDiagramSlots) + 3 regression guard (top-level identifier trùng, thứ tự
  load error-catalog, cân bằng comment CSS).

## Đang làm dở

- (không còn)

## Bước tiếp theo

- Commit; sao chép ảnh harness vào `shots/`; viết `handoff.md`; cập nhật
  Linear (đang Backlog — kết nối Linear tạm lỗi lúc tạo issue).

## Check đã chạy

- `node --check` 3 file sửa — OK.
- `node --test test/*.test.mjs` trong `shell/` — **292/292 pass**.
- Harness Electron `render.js` 6 ca (1440/1366/1920 × inheritance-7,
  two_party-30, alive-owner, empty):
  - `wrapStyle: block|flex` — `.cd-diagram` đúng flex sau sửa comment.
  - `wrapW = diagramW = 1123/1049/1620` — canvas lấp vùng còn lại.
  - `worldLeft ≈ (wrapW−worldW)/2` — world căn giữa mọi ca.
  - `poolCards` 6/7/30 đúng nguồn; `hasAssetInPool: false`.
  - `nodeCount: 1` (owner node); hint chủ đất sống hiện đúng.
  - `wide: []` — không tràn ngang ở mọi viewport.
  - two_party-30: `page.h:1343` — trang cuộn đúng D8, không scrollbar lồng.
- PNG: `.agent/scratch/w2-harness/w2-*.png`.

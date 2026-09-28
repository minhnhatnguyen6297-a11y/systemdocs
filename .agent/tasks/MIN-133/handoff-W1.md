# Handoff — MIN-133 / W1 (nền chung)

## Trạng thái khi bàn giao — 2026-09-28
W1 xong toàn bộ phạm vi ở plan §3. Có 2 commit trên `consolidate/monorepo`, chưa push:
- `c780ddf` docs(MIN-133): tokens v1.1.0 + DESIGN mật độ cao + ảnh approved-drafting-v2
- `2c7ce84` style(MIN-133): nền chung mật độ cao — token mới, bỏ statusbar, sửa cap 860px

Không đụng file của W2/W3 (`case-drafting-view.js`, `case-drafting.css`, `relationship-diagram.js`, `case-drafting-model.js`), upload/*, backend, contracts.

## File đã đổi
- `docs/product/ui/tokens.json` → v1.1.0. Các giá trị bị đổi: `color.bg.app` #e9edf2, `color.bg.canvas` #f5f7fa. Token mới `color.border.card` #dde3ea (1px), `font.size.data` 14px, `font.size.chip` 12px, `size.buttonHeightSm` 28px, `size.cardHeadHeight` 34px, `space.viewPadding` 8px. Các giá trị khác: `font.size.cardTitle` 15px/700, `size.buttonHeight` 32px, `size.tableRow` 25px, `space.cardPadding` "0 10px 8px" (x = 10px), `space.cardGap`/`sectionGap` 8px, `layout.stage` 35:65 (38:62 khi ≥1920), `layout.relation.pool` 176px, `layout.contentMaxWidth` null, viewport chuẩn 1440x775. Ngày duyệt 28/09/2026 ghi ở `meta`.
- `docs/product/ui/DESIGN.md`: thêm ghi chú MIN-133 ở đầu file. Sửa V4 (ngoại lệ viền card cấp ngoài cùng), §2, §3, §4, §5 (bỏ statusbar, cap chỉ áp cho `#view > section`), §6 Card. Thêm §9.1 và sửa §10 (bỏ `#statusbar`, cap mới, danh sách biến `:root`).
- `docs/product/ui/references/approved-drafting-v2.png`: bản copy của `mockup/mockup-1440x775.png`. `references/README.md` thêm dòng cho ảnh này (nguồn, ngày duyệt 28/09/2026), ghi rõ dữ liệu trong ảnh chỉ là ví dụ, và khi v1 khác v2 thì theo v2.
- `shell/src/renderer/styles.css`:
  - `:root` có thêm `--border-card`, `--fs-data`, `--fs-chip`, `--btn-h-sm`, `--card-head-h`, `--gap`, `--view-pad`, `--card-pad-x`; các biến sau đổi giá trị: `--bg-app`, `--bg-canvas`, `--btn-h` 32, `--row-h` 25, `--fs-card` 15.
  - Rail: viền phải dùng `--border-card`, padding 8px.
  - `#view` có `padding: var(--view-pad)` và `min-height: 0`.
  - **Sửa lỗi không giãn ngang:** đổi `#view section{max-width:860px}` thành `#view > section`, và `#view > section.cd-root-outer{max-width:none}`. Upload vẫn thoát cap nhờ `#view section.upload-lab` (specificity cao hơn).
  - `.card` thêm viền 1px; `.card-head` min-height 34px, padding `0 10px`; `.card-title` 15px/700, nowrap; `.card-body` padding `0 10px 8px`. Rule mới `.card > .card-body:first-child { padding-top: 8px }` để các card chỉ có body của Upload không bị chạm viền.
  - `.actionbar`, `.job-card`, `.conn-card`, `.health-table` cũng có viền 1px.
  - `table.grid`: chữ 14px, header 13px, padding `0 4px`, hàng cao `--row-h` (25px). `.tbl` giữ chữ 13px, padding `2px 8px`.
  - Nút: `min-height: var(--btn-h)` (32px), padding ngang 12px; `.sm` dùng `var(--btn-h-sm)`. `.pill`/`.badge` dùng `--fs-chip`.
  - Bỏ rule `#statusbar` và media query 800px (rule đó chỉ còn padding `#view` và `#statusbar`).
- `shell/src/renderer/index.html`: bỏ `header#statusbar` gồm 3 pill. Logo thành `<div id="rail-logo" class="rail-logo" role="img" aria-label title>`.
- `shell/src/renderer/renderer.js` `setStatus()`: gộp engine, version, contract vào `title` và `aria-label` của `#rail-logo`, gắn thêm `data-engine-state`. Không có logo thì return, không crash. Giữ nguyên `sidecarStatus`, polling 3s, `engineSlotEl`, `engineInstanceId` và `buildStatus`.
- `shell/test/upload-routing.test.mjs`: test cap đổi regex từ `#view section {` sang `#view > section {` và thêm assert rằng không còn `#view section {`. **Lý do:** test cũ giữ cap 860px để trang shell không bị giãn. Mục đích đó vẫn đúng, nhưng selector cũ cap cả `section.cd-root` lồng bên trong, trái quyết định owner (nội dung module giãn hết ngang).
- `shell/test/shell-chrome.test.mjs` (mới, 7 test): kiểm statusbar đã bỏ khỏi html/css; `setStatus` không crash khi không có element; tooltip logo có engine/version/contract; polling và `engineSlotEl`/`engineInstanceId`/`buildStatus` còn nguyên; giá trị `:root` khớp `tokens.json`; card có viền, `#view` padding token, `.sm` token; `.rail-btn` vẫn 44px.
- Test `styles.css: focus-visible + control 44px toan cuc` (notary-case-drafting-static) **không sửa**. Test vẫn đạt nhờ `.rail-btn` min-height 44px, đúng mục đích tapMin.

## Token/class mới cho W2/W3
- CSS var: `--gap` (8px, khoảng giữa vùng), `--view-pad`, `--card-pad-x` (10px), `--card-head-h` (34px), `--btn-h` (32), `--btn-h-sm` (28), `--row-h` (25), `--fs-data` (14), `--fs-small` (13), `--fs-chip` (12), `--fs-card` (15), `--bg-canvas` (#f5f7fa), `--border-card` (#dde3ea).
- Class chung đã có sẵn kiểu mới: `.card` (có viền), `.card-head/.card-title/.card-tools/.card-body`, `table.grid`, `button.sm`. Chưa thêm class mới không tiền tố. Ô nhập tại chỗ (`.cell-in` trong mockup), topbar, colgroup và lưới chấm canvas thuộc module nên W2/W3 tự scope bằng `cd-*`.
- `#view` hiện có `overflow: auto` và `min-height: 0`, không phải flex container. Nếu W2 muốn `.cd-root` lấp đủ chiều cao (sơ đồ lấp phần còn lại, D8 cuộn cả trang), module cần tự đặt chiều cao hoặc min-height cho `.cd-root-outer`/`.cd-root` (ví dụ `min-height: 100%`), vì W1 không đổi `#view` thành flex. Lưu ý thêm: `section.cd-root-outer` còn chứa `div.slot` engine phía trên `.cd-root`.

## Cách verify
- `cd shell && node --test test/*.test.mjs`:
  - **Trên checkout hiện tại: 261 test, 232 đạt, 29 fail.** Cả 29 fail nằm ở `notary-case-drafting-view.test.mjs` (ví dụ "thiếu nút Zalo") vì W2 đang sửa dở `case-drafting-view.js`/`case-drafting.css`/`notary-case-drafting-view.test.mjs` (chưa commit).
  - **Bằng chứng không phải do W1:** copy `shell/` sang `.tmp/w1check/`, thay `case-drafting-view.js` bằng bản HEAD rồi chạy toàn bộ: **261/261 đạt** (254 cũ + 7 mới).
- `python -m pytest test/test_upload_workflow.py test/test_upload_workspace.py test/test_upload_recovery.py test/test_upload_browser_workflow.py -q`: 109 đạt.
- `git diff --check` sạch; `git show --stat` của 2 commit chỉ có file W1.

## Việc còn lại / rủi ro
- **Chưa nhìn tận mắt trong Electron** (Upload Audit/Quét-upload, trang Trạng thái, Soạn hồ sơ) vì W2 đang sửa dở view. Việc này để W4 làm. Chỗ cần xem kỹ:
  - hàng `ul-grid` dùng `--row-h` 25 kèm padding 4px 10px, thực tế cao khoảng 26px;
  - card Upload chỉ có body, lấy padding-top 8px từ rule mới;
  - trang Trạng thái với padding `#view` 8px.
- `size.inputHeight` giữ 38px vì plan không nói đổi. Ô nhập form rời (Upload, form-row) cao hơn nút 32px. Nếu W4 thấy lệch thì cần owner quyết.
- `prototypes/prototype.css` giữ v1.0.0 làm bản ghi MIN-126, không đồng bộ. Điều này đã ghi trong `tokens.json` meta và DESIGN §10.
- `size.chipPosition` (24px) chưa đổi. Mockup có chip 22×19, thuộc phạm vi W3 nếu cần.
- DESIGN §7 vẫn ghi "bảng có cuộn riêng" ở 1280/1366. Câu này trái D8 với bảng Người của Stage. Đoạn đó thuộc visual-design Notary nên W1 không sửa; điều phối cân nhắc khi W2 xong.
- Chưa commit `progress.md`: cả thư mục `.agent/tasks/MIN-133/` đang untracked (plan/brief/mockup của điều phối) và W2 cũng ghi vào file này. W1 chỉ nối thêm mục ở cuối file. Điều phối commit cùng các file task.

## File tạm đã dọn
- `.tmp/w1check/` (bản copy để kiểm) và `.tmp/min133-w1-node.log` đã xóa sau khi ghi kết quả vào đây.

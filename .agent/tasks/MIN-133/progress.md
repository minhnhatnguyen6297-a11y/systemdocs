# Progress — MIN-133

## Trạng thái: mockup đã duyệt, plan lập xong (`plan.md`) — chờ lệnh giao W1+W2

## Đã làm
- Điều tra (worker chỉ đọc):
  - Trường Người: DB `Customer` chỉ có 7 cột (ho_ten, gioi_tinh, ngay_sinh, ngay_chet, so_giay_to, ngay_cap, dia_chi — models.py:8-20).
    `noi_cap` là @property suy từ ngay_cap (models.py:47-49), Word dùng. `place_of_origin` chỉ nằm trong case_state_json,
    không cột DB, không intake sinh, form cũ chưa từng có ô nhập (chỉ dữ liệu record Zalo); vào contract từ MIN-105 (`1507301`).
  - Tài sản: 11 trường + land_rows khớp DB `Property` 1-1 — giữ nguyên.
  - Card Thông tin hồ sơ: `document_type` bắt buộc trên wire (case_workspace.py:1703-1709); `ngay_lap_ho_so` DB NOT NULL nhưng backend tự điền today (case_workspace.py:1190);
    Word dùng [Loại văn bản]/[Ngày lập hồ sơ]/[Nơi niêm yết]/[Ghi chú] (word_engine.py:1098-1107).
  - Statusbar: client-only, cùng dữ liệu đã có ở module Trạng thái (renderer.js:656+).
  - Không giãn full screen: `styles.css:158` `#view section{max-width:860px}` cap cả `section.cd-root` bên trong.
  - Thanh cuộn Stage: `.cd-stage-body{max-height:290px;overflow:auto}` + min-width cột (case-drafting.css:126-177).
- Mockup render bằng Electron có sẵn: `mockup/`.

## Chờ owner
Xem handoff câu hỏi trong phản hồi phiên 28/09 (node 144px, gộp tab+action bar, Lưu sơ đồ lên header, nơi đặt 4 trường Thông tin hồ sơ, noi_cap/place_of_origin, bảng Người >12 người, thông tin engine).

## W1 — nền chung (2026-09-28) — XONG
- Commit `c780ddf` (docs: tokens v1.1.0, DESIGN §9.1, ảnh `references/approved-drafting-v2.png`) + `2c7ce84` (style: styles.css/index.html/renderer.js, bỏ `#statusbar`, cap chỉ `#view > section`, test).
- Test shell: 261/261 đạt khi dùng bản HEAD của `case-drafting-view.js`; trên checkout hiện tại có 29 fail ở `notary-case-drafting-view.test.mjs`, do W2 đang sửa dở. pytest upload: 109 đạt.
- Chi tiết, token/class mới cho W2/W3, rủi ro: `handoff-W1.md`.

## W2 — Stage + thanh trên (2026-09-28) — XONG
- Commit `feat(MIN-133): W2 …` gồm case-drafting-view.js, case-drafting.css, 2 file test view/static và handoff-W2.md.
- D5 thanh trên 42px (tab + hành động), D4 bỏ back/tiêu đề/pill Nháp/nhãn lưu, D2 bỏ card meta (dùng mặc định model), D1 bảng Người 7 cột (noi_cap/place_of_origin vẫn giữ trên wire), D8 Stage không cuộn, layout flex dọc.
- Test shell: 278/278 đạt. Harness Electron đo Stage 371px, hàng 25px, cột đúng mockup, Stage tràn = 0; Hai bên 30 người thì cả trang cuộn.
- Việc cho W3 (canvas còn cao cố định; tràn ngang ở .cd-diagram có sẵn từ trước): xem `handoff-W2.md`.

## W3 — sơ đồ (2026-09-28) — XONG
- Worker `7fdc44fa` viết xong phần JS (hằng layout, layout căn giữa, node trống, chip Chủ/Nhận, edges không mũi tên, Pool gọn) rồi chết do hết quota — coordinator hoàn thành: D6 nút lên head (bỏ `.cd-rel-foot`), toàn bộ CSS relation/canvas/node, sửa bug edge trùng từ midpoint cặp vợ/chồng, test + docs.
- Đo Electron (harness W2): page overflow 0×0 ở cả 1440×775 / 1366×768 / 1920×1080; tràn ngang hết; two_party 30 người → trang cuộn 648px, Stage không cuộn lồng.
- Test: 280/280 đạt (+2 test D6/D7).
- Chi tiết + hằng layout + hạn mức W4: `handoff-W3.md`. Ảnh: `w3-shots/`.

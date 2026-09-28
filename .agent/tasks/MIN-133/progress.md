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

## W4 — kiểm chứng cuối (2026-09-28) — XONG
- Kiểm chứng trên **Electron thật + sidecar Python thật** (CDP 9666, DB/output scratch `.agent/scratch/w4/`, không đụng DB dev): 23/23 mục checklist ĐẠT — xem `handoff-W4.md` §3.
- Test giữ xanh: node 280/280; validate_examples 68/0; pytest adapter 194, upload 109, workspace 87.
- Đo app thật HS-11 (3 TS, 7 người): page/stage/h-overflow = 0/0/0 ở cả 1440×775, 1366×768, 1920×1080; stage 371px, topbar 42, row 25, pool 176, diag head 34, diag card flex 330/323/635.
- Flow thật đã qua: nhập mới + lưu `HS-11`/`HS-12`, mở hồ sơ cũ, Cập nhật/Hủy, validation inline, **conflict→"Tải bản mới" reload** (revision 3→4), dialog Loại đất "Áp dụng" chỉ đổi draft, two_party 30 chỗ (p16 đầu B, không dồn, swap + bỏ gán về Pool), 33 người → trang cuộn không cuộn lồng, node trống nhận drop, chip Chủ/Nhận, ellipsis+tooltip, drag-drop 3 hướng (synthetic), gán bàn phím, zoom 90/110%, Mở rộng+Esc, dirty-dot, gate Stage, Word dialog chỉ mở không export, focus-within lộ nút hover-only, Upload Audit + Quét & Upload.
- Phát hiện: **F-1** (khuyến nghị mở issue follow-up, không sửa trong W4) — defer rerender khi focus còn trong ô Stage có thể nuốt render `status='conflict'` cho tới emit kế; dùng chuột thật hầu như không gặp. Chi tiết `handoff-W4.md` §4.
- Hạn chế môi trường: kéo native không có (`Input.startDragging` thiếu trên Electron 31); `Page.captureScreenshot` stall khi cửa sổ OS bị che → bắt bằng `Page.startScreencast`; **true Windows DPI 125/150% không kiểm được** (chỉ CSS-pixel emulation: DSF 1.25 → cuộn dọc +131px, không tràn ngang).
- **Không sửa code** → không có `fix(MIN-133)`. Ảnh: `w4-shots/` (3 viewport + 2 tab Upload + flow).

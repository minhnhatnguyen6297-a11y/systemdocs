# EXPERIENCE — Cách thao tác chung cho shell Electron (MIN-124)

> **Trạng thái: APPROVED — owner duyệt qua bản mẫu MIN-126, 27/09/2026.**
> File này gom cách người dùng
> tương tác **dùng chung cho mọi module** trong shell (Notary, Upload Lab,
> các mặt shell). Nó không thay thế spec UX cấp sản phẩm hay SOT hành vi:
>
> - Vocabulary trạng thái shell + bốn mặt màn hình → SOT:
>   `docs/product/specs/2026-09-14-module-transition-ux-spec.md` (DRAFT,
>   MIN-32 slice). File này **dẫn lại**, không nhân bản.
> - Hành vi/dữ liệu Notary → `notary_v2/docs/platform/case-workspace/drafting-tab.md`.
> - Hành vi Upload → `upload_lab/docs/spec_UI.md`.
> - Thị giác → [`DESIGN.md`](./DESIGN.md) + `tokens.json`.

## 1. Navigation và giữ trạng thái

- Đổi module/tab **không được mất** form đang nhập, lựa chọn, vị trí cuộn,
  job đang chạy (hiện trạng đã có: panel DOM persistent +
  `upload/state.js` giữ scroll per-tab + model Notary giữ draft). Đây là
  yêu cầu **cứng** của hướng đích, không phải tiện ích.
- Vị trí quay lại dùng đúng một nút/quan hệ cha (tab cục bộ / nav shell);
  không breadcrumb dài.
- Tab/module có dữ liệu chưa lưu hiển thị dấu hiệu dirty (§5) thay vì
  chặn rời ngầm.

## 2. Bàn phím & focus

- Tab order theo thứ tự nhìn thấy (trên → dưới, trái → phải); không nhảy
  ngược khiến người dùng mất ngữ cảnh.
- Mọi phần tử tương tác đạt được bằng bàn phím: `Enter`/`Space` kích hoạt,
  `Esc` đóng popup/menu.
- **Kéo-thả luôn có đường bàn phím tương đương**: thẻ Pool → Diagram có
  menu `Gán vị trí` (hiện trạng `openAssignMenu`); không có thao tác nào
  chỉ làm được bằng chuột.
- Focus ring hiển thị rõ (`color.focus.ring`, 2 px); focus phải vào phần
  tử đầu của dialog/panel vừa mở và **trả về** phần tử mở nó khi đóng.
- `selected ≠ focused`: dòng đang chọn (bảng, chip số) và điểm focus bàn
  phím là hai khái niệm riêng, có hai dấu hiệu thị giác riêng.

## 3. Bốn mặt trạng thái màn hình (faces)

Tên trạng thái giữ đúng vocabulary shell (`face*` trong `lib.js`); file này
chỉ quy định cách dùng:

| Mặt | Quy tắc thao tác |
|---|---|
| Loading | Skeleton/spinner + nhãn việc đang làm; không giả progress; không hiện "đang tải" vô thời hạn cho job có progress thật |
| Empty | Nói rõ vùng này trống + **hành động đầu tiên** ngay trong vùng; không để màn trắng |
| Error | `error.code` + message tiếng Việt + `retryable`; nút Thử lại chỉ khi `retryable: true`; link diagnostics nếu có; **không in JSON/stack trace/tên command** |
| Unavailable | Nêu capability thiếu + lý do; disable hành động liên quan thay vì cho bấm rồi lỗi |

Phạm vi áp: từng card/vùng dùng face riêng khi chỉ vùng đó lỗi; face
toàn-màn chỉ khi cả workspace không tải được.

## 4. Busy, waiting_user, cancel

- `busy` cục bộ (đang commit/lưu/xuất) disable nút kích hoạt + hiển thị
  trạng thái trong nút/hàng đó; **không** khóa toàn màn trừ khi thao tác
  thật sự toàn cục.
- `waiting_user` = chờ người (login portal, review tab đã điền) — **không
  phải lỗi**: banner tông warn, nêu đúng việc cần làm + CTA. Không giật
  focus cửa sổ Chromium lặp lại (spec_UI §5).
- Cancel chỉ hiện khi job đang `accepted/running/waiting_user`; luôn có
  confirm; hủy **không** hoàn tác một hành động đã xảy ra và không tự đóng
  tab người đang kiểm tra.
- `partial` hiển thị breakdown thành công/thất bại ngay chỗ kết quả, không
  phải toast thoáng qua.

## 5. Dirty / chưa lưu

- Mỗi tầng dữ liệu có cờ dirty riêng (hiện trạng Notary: `stageDirty`,
  `diagramDirty`, `metaDirty` → `hasUnsaved`). Dirty hiển thị chấm/nhãn
  tại đúng nút commit của tầng đó; không gom một banner chung mơ hồ.
- Rời module/đóng cửa sổ khi dirty → confirm qua `confirmModal` chung;
  không auto-save, không im lặng mất dữ liệu.
- `Hủy thay đổi` (discard) — ngữ nghĩa đã chốt §13.2 Q2 (client-only,
  restore cả Stage lẫn Diagram về committed): nút hiển thị trên action
  bar, có confirm khi dirty; đã triển khai P6.

## 6. Conflict (revision)

- `workspace_conflict` → dialog riêng, không toast: cho **tải bản mới** hoặc
  **giữ bản nháp để sao chép**; không có nút ghi đè cưỡng bức
  (`drafting-tab.md` §3).
- Dữ liệu stale (đọc cũ hơn revision server) hiển thị nhãn `đã cũ` tại chỗ
  bị ảnh hưởng thay vì khóa màn.

## 7. Dialog / popup

- Một modal tại một thời điểm trong một module; overlay mờ nhẹ; `×` góc
  phải trên + `Esc` đóng; focus trap trong modal; trả focus đúng nơi gọi.
- Footer: primary bên phải, secondary/ghost bên trái nó; nút hủy đóng
  **không** tự lưu hay tự xóa kết quả đang có.
- Dialog có hành động phá hủy (xóa dòng/xóa parcel) dùng icon `✕` trong
  dòng/cột đó, không mở thêm popup xác nhận cho thao tác draft UI; hành
  động **không phải draft** (đã commit, xóa vật lý) mới confirm.
- Không dùng dialog cho thông báo thường ngày: thành công → toast/banner
  inline; hướng dẫn cách dùng → nhãn nhỏ trong vùng, **không** popup "dạy".

## 8. Thông báo / toast

- Toast chỉ cho kết quả job hoàn tất hoặc lỗi cần chú ý tức thì; banner
  inline cho trạng thái còn tồn tại (waiting, conflict, mock mode).
- Không popup báo thành công thường ngày (`đã lưu` chỉ cần trạng thái lưu
  trên thanh ngữ cảnh hoặc toast nhẹ tự tắt).
- Không hiển thị ID kỹ thuật thô trong thông báo người đọc (`row_id`,
  `job_id`, tên command); dùng nhãn tiếng Việt có dấu.

## 9. Trường hợp đặc biệt dùng chung

- **Mock/dev mode**: banner hiển thị liên tục khi backend là mock
  (`mockBanner`) — không cho trông như dữ liệu thật.
- **Locked/unsupported**: `locked` → toàn workspace chỉ đọc (xem/sao chép
  vẫn được); `case_type` không hỗ trợ → mặt Unavailable của vùng đó.
- **Response trễ**: kết quả job của phiên/scope cũ bị loại bỏ
  (`session` counter Notary, `acceptScopedResult` Upload) — UI không hiện
  lỗi "không liên quan" khi user đã chuyển ngữ cảnh.
- **Đường dẫn/tên dài**: cắt ellipsis + tooltip + mở file gốc; không kéo
  vỡ layout.

## 10. Quyết định thao tác — ĐÃ CHỐT (cập nhật MIN-132)

Các mục dưới đã được chốt qua duyệt bản mẫu MIN-126 (27/09/2026),
`notary.case-drafting.v2` §13 và triển khai P4–P8:

1. `Hủy thay đổi` ở action bar — chốt §13.2 Q2: revert **cả** draft Stage
   lẫn Diagram về committed (client-only); đã triển khai P6.
2. `Mở rộng` — chốt DESIGN §9.6: overlay gần toàn màn trong app (Esc/×
   đóng, trả focus); đã triển khai P7.
3. Trình tự focus khi dialog mở — chốt: focus vào control đầu trong
   dialog, Esc/× trả focus về element mở; đã triển khai P4 (confirmModal/
   modal focus-trap + return focus).
4. Phím tắt thao tác sơ đồ — chốt theo P7: gán node bằng menu/phím qua
   position chips (không bắt buộc drag); đã triển khai P7.
5. Ngưỡng cuộn ngang bảng khi hẹp — chốt theo triển khai: bảng data-heavy
   (Người, audit, queue) giữ `table-wrap` cuộn ngang nội bộ, không ép co
   cột; breakpoint trang 1000/800 px theo `DESIGN.md` §7.
6. Toast lỗi — chốt: toast lỗi retryable tự tắt ~4 s + banner/inline state
   còn lại tại vùng liên quan, không modal; đã triển khai P4.

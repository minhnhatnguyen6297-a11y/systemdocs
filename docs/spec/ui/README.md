# UI chung của Electron shell

**Trạng thái:** Approved · owner duyệt qua prototype 27–28/09/2026

UI chung là một feature cấp hệ thống, nên spec nằm tại đây. Hành vi riêng của
Stage, Diagram hoặc Upload vẫn nằm trong spec feature tương ứng.

## 1. Mục tiêu

Giao diện Windows sáng, gọn, nhiều dữ liệu nhưng dễ quét. Một bộ token và
component dùng chung cho Notary, Upload Lab và các mặt shell.

## 2. Nguyên tắc

- Nền xám-xanh nhạt, card trắng, điểm nhấn xanh.
- Data-first, khoảng cách 8 px, ít bóng và ít viền trang trí.
- Card cấp ngoài có viền 1 px; bảng giữ đường lưới vì mang nghĩa dữ liệu.
- Focus luôn nhìn thấy; selected khác focus.
- Không biến dữ liệu mẫu trong ảnh thành mặc định nghiệp vụ.
- Không thu nhỏ font khi viewport hẹp; dùng cuộn, truncate và tooltip.

## 3. Token chính

Nguồn máy đọc: [`tokens.json`](./tokens.json).

| Nhóm | Giá trị đã chốt |
|---|---|
| Nền app | `#e9edf2` |
| Card | `#ffffff`, viền `#dde3ea` |
| Accent | `#2563eb` |
| Font | Segoe UI; base 15 px; data 14 px |
| Nút | 32 px; nhỏ 28 px |
| Hàng bảng | 25 px |
| Card | radius 10 px; header 34 px |
| Navigation | rail icon sáng 60 px |

## 4. Component và thao tác

- Một primary action cho một phạm vi hiển thị.
- Lỗi field nằm cạnh field; lỗi nguồn nằm cạnh nguồn.
- Dialog có focus trap, Esc/× đóng và trả focus.
- Toast chỉ cho kết quả ngắn; trạng thái dài nằm trong vùng nội dung.
- `waiting_user` dùng tông cảnh báo, không dùng đỏ như lỗi.
- Drag có keyboard fallback hoặc menu gán vị trí.
- Dữ liệu chưa lưu phải có dấu rõ; Hủy khôi phục snapshot committed.

### Navigation và giữ trạng thái

- Đổi module/tab không được mất form, lựa chọn, vị trí cuộn hoặc job đang chạy.
- Dữ liệu dirty (đã sửa nhưng chưa lưu) hiển thị tại đúng nút commit.
- Rời module hoặc đóng cửa sổ khi dirty phải hỏi xác nhận; không auto-save và
  không âm thầm bỏ dữ liệu.

### Bốn mặt trạng thái

| Mặt | Cách hiển thị |
|---|---|
| Loading | Nêu việc đang làm; job có progress thật không dùng spinner vô hạn |
| Empty | Nói vùng đang trống và đưa hành động đầu tiên ngay tại đó |
| Error | Message tiếng Việt + retry khi `retryable:true`; không lộ JSON/stack |
| Unavailable | Nêu capability thiếu và khóa đúng hành động liên quan |

Lỗi chỉ ở một card thì card đó đổi mặt; không che toàn màn hình.

### Busy, chờ người, hủy và partial

- Busy chỉ khóa nút/vùng đang chạy, không khóa toàn màn nếu không cần.
- `waiting_user` là chờ người, dùng banner cảnh báo và CTA, không tô như lỗi.
- Cancel chỉ hiện khi job đang chạy/chờ, phải xác nhận; không hoàn tác việc đã
  xảy ra và không tự đóng tab người dùng đang kiểm tra.
- `partial` hiển thị danh sách phần thành công/thất bại tại vùng kết quả.

### Conflict, dialog và thông báo

- `workspace_conflict` mở dialog cho `Tải bản mới` hoặc `Giữ bản nháp để sao
  chép`; không có nút ghi đè cưỡng bức.
- Một modal mỗi module; Esc/× đóng, focus trap và trả focus về nút mở.
- Toast chỉ cho kết quả ngắn. Trạng thái còn tồn tại nằm inline/banner.
- Không popup “thành công” thường ngày và không hiển thị ID kỹ thuật cho người
  dùng.

## 5. Responsive

- Kiểm ở 1280×800, 1366×768, 1920×1080 và DPI 125%/150%.
- ≤1000 px: các vùng lớn xếp dọc.
- ≤800 px: giảm padding, không giảm font.
- Bảng rộng cuộn ngang; đường dẫn dài truncate và có tooltip.
- Diagram hỗ trợ pan/zoom và mở rộng trong app.

## 6. Kiến trúc CSS

- `shell/src/renderer/styles.css` sở hữu token, shell chrome và component chung.
- CSS Notary dùng prefix `cd-*`, scope trong `.cd-root`.
- CSS Upload dùng prefix `ul-*`, scope trong `.upload-lab`.
- Module không ghi đè biến `:root` và không dùng selector element trần làm ảnh
  hưởng module khác.

## 7. Tài sản tham chiếu

- [`prototypes/`](./prototypes/README.md): prototype HTML có dữ liệu giả.
- [`references/`](./references/README.md): ảnh owner đã duyệt.
- `tokens.json`: giá trị chuẩn; CSS runtime phải ánh xạ từ đây.

## 8. Lịch sử và câu hỏi

- MIN-126 duyệt prototype và hướng trắng/xanh ngày 27/09/2026.
- MIN-133 duyệt mật độ cao hơn ngày 28/09/2026.
- Không còn câu hỏi về accent, rail, radius hoặc breakpoint trong phạm vi này.
- Thay đổi hành vi sản phẩm không được quyết bằng file UI chung.

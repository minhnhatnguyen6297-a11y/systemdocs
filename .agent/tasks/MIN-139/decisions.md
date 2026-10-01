# Decisions — MIN-139

## 2026-09-29 — Định hình sản phẩm
- **Chọn:** Đặt giao diện sản phẩm thành tab thứ ba trong Upload Lab; đầu ra
  chính là bản ghi người/tài sản đã nhóm và có bằng chứng nguồn.
- **Lý do:** User cần một nơi thử regex phục vụ Upload và các chức năng khác;
  các trường rời không đủ để đưa vào nghiệp vụ.
- **Loại bỏ:** Giữ MIN-137 chỉ là công cụ dev độc lập và chỉ trả danh sách
  trường, vì không đáp ứng nhu cầu nhóm người/tài sản.
- **Nguồn:** Owner chốt trong yêu cầu ngày 2026-09-29; Linear MIN-139.

## 2026-09-29 — Đề xuất xử lý nhiễu và hướng Word (chưa chốt)
- **Đề xuất:** Giữ mảnh dữ liệu thiếu cùng bằng chứng; chỉ đánh dấu nghi nhiễu/
  nghi trùng. Word assistant chỉ gợi ý placeholder có sẵn để user xác nhận.
- **Lý do:** Lời chứng thường lặp hoặc chưa hoàn chỉnh, nhưng “thiếu trường”
  không tự động có nghĩa là dữ liệu sai. Vai trò placeholder là nghĩa nghiệp vụ.
- **Loại bỏ:** Tự xóa bản ghi thiếu và tự suy đoán placeholder từ giá trị tìm
  thấy, vì cả hai có thể làm mất hoặc gắn sai dữ liệu.
- **Nguồn:** Agent đề xuất từ yêu cầu ngày 2026-09-29 và contract Word hiện
  hành. Owner đã yêu cầu xử lý nhiễu/trùng và hướng tạo mẫu tự động; chưa chốt
  cách nhận diện, khóa gộp hoặc mức tự động của phiên bản đầu.

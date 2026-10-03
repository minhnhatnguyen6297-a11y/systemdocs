# Decisions — MIN-139

## 2026-10-04 — Triển khai Word-first đã được Owner yêu cầu

- **Nguồn Owner:** NAIA-4 comments `01a0fd96-dc6d-77f5-a301-053b7eb6a651`,
  `01a0fd9b-ff2e-7e8c-be10-bbf2bfe91391` (02/10),
  `01a0ff5c-5cf6-7e55-a2e8-597143bfb0d3` (03/10), yêu cầu triển khai trong chat
  04/10. Chọn Word trước, regex NAIA-3 chung, không tự suy quan hệ/sở hữu.
- **Lựa chọn kỹ thuật của executor:** giữ parser/bản đồ DOCX trong Document
  Intake, source/extraction và derivative tại engine-data, context ID/hash
  trong workspace snapshot; Word service dùng catalog tích hợp. Ghi cùng
  Stage transaction/revision, không thêm DB công nghệ khác.
- **Thay cho hướng UI 29/09 trong đợt này:** giữ dialog Intake/Word và hai Upload
  tabs; không tạo tab thứ ba. Không nối địa chỉ lịch sử từ ledger pending.
- **Bằng chứng giới hạn:** fixture giả lập có nhãn; chưa có corpus văn phòng
  hoặc kiểm trang Word thật. Tách/gộp tùy ý ứng viên chưa có UI riêng.

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

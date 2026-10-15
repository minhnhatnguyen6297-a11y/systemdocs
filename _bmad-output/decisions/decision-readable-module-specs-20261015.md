# Spec module liền mạch, ít file

**Trạng thái:** Accepted · **Ngày:** 15/10/2026 · **Nguồn:** Owner trong hội thoại này, yêu cầu “viết liền mạch… Spec vẫn ghi lại quyết định là gì”, rồi “triển khai”.

## Đã chọn

- Mỗi module một hoặc vài spec quan trọng. Soạn thảo có README, quy tắc sơ đồ và Word; Upload/NotaryOffice mỗi module một README. Quy tắc bóc tách, OCR, dữ liệu và địa chỉ dùng chung tập trung theo chủ đề.
- Spec tự đủ nghĩa: mục đích → luồng → hành vi → giới hạn/ngoại lệ → phần chưa chốt. Quyết định có hiệu lực được viết trực tiếp trong spec, dù trùng decision.
- Decision ghi điều đã chọn, lý do và phương án đã loại/chốt bỏ qua. Đổi quyết định phải cập nhật spec; không để người đọc tự ghép lịch sử để suy quy tắc.
- Bản nền sản phẩm đọc đầu phiên; sổ tay theo màn hình/công việc tiếp theo; chỉ mở spec module và phần chuyên sâu có liên quan. Issue/task bền vững ở `_bmad-output/backlog/`; sổ tay chỉ dẫn đường.
- Lưu bản cũ vào archive có nhãn lịch sử. Thiết kế chưa duyệt vẫn chưa duyệt, không tự thành yêu cầu triển khai.

## Lý do

Nhiều spec nhỏ và dẫn chiếu liên tục khiến owner không đọc hết, không phát hiện lệch ý; coordinator cũng dễ thiếu ngữ cảnh. Ưu tiên đường đọc trọn vẹn, rút gọn câu thừa thay vì cắt mất quy tắc.

## Phương án bỏ

- Bỏ cách mỗi thành phần nhỏ/mỗi lần bàn tạo một spec riêng.
- Bỏ nguyên tắc tránh lặp tuyệt đối giữa spec và decision.
- Bỏ cách chỉ ghi “xem file khác” thay cho hành vi cốt lõi.
- Không gom bằng cách nối toàn bộ lịch sử, báo cáo và Draft thành một spec được coi là đã duyệt.

## Ý định sản phẩm được nhắc rõ trong lần biên soạn

Owner mô tả soạn hồ sơ là điền dần dữ liệu: trường nào có thì xuất, thiếu để trống; không bắt hoàn tất Diagram khi mẫu chỉ cần Stage. Chỉ chặn/hỏi khi có nguy cơ cụ thể làm lệch dữ liệu. Các điều kiện readiness cũ được ghi là khoảng lệch cần xử lý, không tuyên bố đã thay runtime.

Zalo hiện nghiên cứu riêng; tab Word tự tạo mẫu chưa đặc tả. Bản này không duyệt công thức thừa kế Draft, schema Office, bảng đơn dòng decision-72 hoặc thuật toán gộp dữ liệu mâu thuẫn.

## Kiểm chứng và giới hạn

Đợt này chỉ đổi tài liệu, đường đọc và link. Không sửa code, schema hoặc đáp án đã duyệt. Bản gốc và bảng chuyển nơi lưu nằm trong `_bmad-output/archive/specs-before-consolidation-20261015/`; checkpoint Git `68e6196` giữ mốc trước khi gom. Thay đổi sổ tay có trước phiên được bảo toàn, không tự khôi phục đoạn owner đã bỏ.

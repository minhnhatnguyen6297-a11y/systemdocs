# Cập nhật đúng file khi nghiệp vụ thay đổi

## 1. Cửa vào và file sở hữu

Đọc [AGENTS.md](../../AGENTS.md) và [bảng định tuyến SPEC](../SPEC.md#1-sửa-yêu-cầu-ở-đúng-một-nơi).
Chọn chủ đề, mở đúng chương được chỉ định. Không đoán theo tên file có chữ
spec, ngày mới nhất, tiêu đề APPROVED hoặc kết quả tìm kiếm đầu tiên.

Bộ SPEC là một nguồn có thẩm quyền, chia chương để dễ đọc. Một quy tắc có đúng
một file sở hữu; file tiêu thụ dẫn liên kết. Trạng thái DRAFT vẫn là chưa duyệt.

## 2. Khi chủ dự án đổi một yêu cầu

1. Ghi lại yêu cầu, phạm vi, nguồn/ngày quyết định; phân biệt đã duyệt với đề xuất.
2. Tìm chương sở hữu trong SPEC §1 rồi sửa nội dung tại chỗ. Không tạo bản ngày
   mới cạnh tranh với bản hiện hành. Đề xuất chưa duyệt ở mục câu hỏi/draft rõ ràng.
3. Nếu trải qua nhiều chương, mỗi chương chỉ viết phần của mình:
   OCR nhận/đọc; Stage sửa/duyệt; Zalo quản lý nguồn/lô; Diagram quan hệ; Word xuất.
4. Dùng mã quy tắc hoặc tiêu đề ổn định để dẫn chiếu, không chép lại các điều kiện.
5. Đọc source hiện tại khi mô tả hiện trạng. Thêm/cập nhật gap ở SPEC §7 khi code
   chưa đáp ứng; viết SPEC không phải thực hiện migration hoặc sửa lỗi.
6. Kiểm tra consumer của quy tắc: Word, Zalo, Diagram, shell adapter khi liên quan.
   Nếu cần đổi runtime/contract/module ngoài phạm vi, xin mở scope riêng.
7. Thay đổi file sở hữu/đường dẫn thì cập nhật SPEC §1, README và AGENTS; giữ
   redirect cần thiết để các đường đọc cũ dẫn tới đúng nơi.
8. Kiểm tra diff, link và các cụm “SOT/Source of truth/APPROVED” còn sót;
   qua review độc lập trước commit/việc phụ thuộc.

## 3. Tài liệu cũ

- Workflow cũ đã chuyển thành redirect: chỉ sửa link, không thêm lại nghiệp vụ.
- Stage draft 18/08 lưu nguồn D8/D9/D12 và các phương án kỹ thuật cũ; hành vi
  đã tiếp nhận nằm ở chương Stage hiện hành.
- Hai bản tính thừa kế 22/08 và 24/08 còn nháp. Không chọn bản mới hơn làm luật.
- Bản Zalo 08/2026 là reference-only; việc từng được duyệt không cho khôi phục
  sửa/xác nhận OCR ngoài Stage.
- Technical/parser/catalog ghi chi tiết cách làm; không tự đổi nghiệp vụ hoặc
  danh mục công nghệ. Nhãn trong bản lịch sử không ghi đè nhãn lịch sử đầu file.
- Memory Bank và plan là ngữ cảnh làm việc, không là SOT; không phục hồi các nhánh
  trước monorepo như hướng phát triển hiện tại.

## 4. Thêm loại hồ sơ hoặc chức năng

Chỉ thêm một chương khi có chủ đề đủ độc lập và phạm vi được duyệt; đăng ký tại
SPEC §1. Loại hồ sơ mới dùng lại chương input/Stage/Word, không chép thành bộ riêng.
Không tạo sẵn folder/spec cho mọi loại hồ sơ tương lai, không trích framework
chung hoặc thêm contract tích hợp chỉ vì đang tổ chức lại tài liệu.

## 5. Kiểm tra thay đổi chỉ ở Markdown

- `git diff --check`.
- Kiểm tra mọi link Markdown nội bộ được thêm/sửa, kể cả anchor tiêu đề.
- Kiểm tra các đường dẫn trong bảng routing AGENTS và SPEC tồn tại.
- Tìm các tuyên bố thẩm quyền cũ; chỉ còn chương do SPEC chỉ định, draft rõ
  trạng thái hoặc reference/redirect không có quyền đặt lại nghiệp vụ.
- Báo rõ không chạy runtime suite nếu không đổi code; không gọi kiểm docs là test toàn bộ.

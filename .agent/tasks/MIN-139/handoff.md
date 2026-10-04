# Handoff — MIN-139, 2026-10-04

Luồng Word-first đã triển khai cục bộ, chờ root review và commit đúng phạm vi.
Spec hiện hành: [Nhập DOCX](../../../docs/spec/notary_v2/input/docx-import.md).
Các phép thử và giới hạn được ghi trong [progress](progress.md).
Đã sửa các nhóm lỗi được xác minh ở review iteration 1: danh tính dòng đất,
duyệt từng ô, ngày evidence, slot/định dạng không dùng được, lựa chọn đã lưu/
xóa hết, giới hạn/gỡ/tên nguồn, kiểm slot trong transaction và đích thư mục con.
Kiểm chứng gồm luồng DOCX hai bên qua adapter thật và stale export không ghi file.

Đọc file gốc → review/sửa → nhận từng bản ghi → lưu Stage → chọn từng vị trí
Word → xác nhận/lưu → xuất vào thư mục đã cấp quyền. Mọi lần xuất dùng dữ liệu
đã lưu và kiểm tra nguồn, thứ tự, mã băm. File gốc không bị sửa.

Root cần review ranh giới chung với workspace/Word, kiểm tra UI và bản đóng gói
trước khi gọi là sẵn sàng dùng tại văn phòng. Không upload tài liệu khách, không
push/PR/merge. Phạm vi ảnh/OCR/Excel và tab thứ ba vẫn nằm ngoài lần này.

## Handoff kiến trúc cũ — 29/09/2026

Nên đặt bộ máy nhận diện trường ở đâu để nhiều chức năng cùng sử dụng mà vẫn có một nơi chịu trách nhiệm quản lý quy tắc và phiên bản? Đầu vào chung nên là văn bản đã chuyển đổi, hay phải giữ thêm cấu trúc riêng của ảnh, Word và bảng tính cùng vị trí trong file gốc? Kết quả nên biểu diễn trường tìm thấy, bản ghi người/tài sản, bằng chứng nguồn, phần thiếu, mâu thuẫn và các lần xuất hiện lặp như thế nào? Nên tách bước tìm trường khỏi bước ghép bản ghi và xử lý nhiễu/trùng ra sao; khi nào được tự gộp, khi nào cần người kiểm tra? Khả năng nhận diện để tạo mẫu Word nên dùng chung phần nào với bộ máy nhập dữ liệu, và ranh giới nào bảo đảm sửa đúng vị trí mà không gán sai vai trò? Cần phép thử và tiêu chí nào trên các loại đầu vào để chọn kiến trúc trước khi triển khai?

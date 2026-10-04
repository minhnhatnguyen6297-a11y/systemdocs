# Handoff — MIN-139, 2026-10-04

Luồng Word-first đã triển khai cục bộ, chờ root review và commit đúng phạm vi.
Spec hiện hành: [Nhập DOCX](../../../docs/spec/notary_v2/input/docx-import.md).
Các phép thử và giới hạn được ghi trong [progress](progress.md).
Iteration 4 sửa số âm/không hữu hạn ngay trong bằng chứng nguồn; giữ bản ghi
tài sản thiếu mã nhưng có nhãn/địa chỉ/đất; gỡ nguồn lỗi khôi phục để thử lại;
JSON tải xuống giữ kết quả chuẩn ban đầu. 35 DOCX Python, 20 Node DOCX đạt;
bộ regression 386 backend pass/2 COM skip, 115 sidecar/Intake/lõi regex,
229 Node và 78 ví dụ contract đạt. Root Electron HS-7 đạt 4 bản ghi/25 binding,
lưu/mở lại/xuất và kiểm nguồn/ZIP/DB không đổi; native picker vẫn giả lập.
Iteration 3 đã sửa 8 nhóm xác minh: retry/khóa chọn vị trí, ranh giới tài sản,
diện tích sai, giữ review cũ, công bố nguồn/mẫu bằng file tạm và hủy xuất,
đất thiếu bằng chứng, lỗi thư mục đích, response xuất cũ. 24 DOCX, 353 backend
regression (2 ca COM skip), 109 sidecar/lõi regex, 6 sidecar Intake, 226 Node
và 78 ví dụ contract đều qua. Root chạy lại Electron iteration 3 `ok: true`
với 4 bản ghi/25 vị trí; picker dùng bộ giả lập. Chưa kiểm native picker,
trang Word/corpus văn phòng/bản cài sạch hay phục hồi chung database+nguồn.
Đã sửa các nhóm lỗi được xác minh ở review iteration 1: danh tính dòng đất,
duyệt từng ô, ngày evidence, slot/định dạng không dùng được, lựa chọn đã lưu/
xóa hết, giới hạn/gỡ/tên nguồn, kiểm slot trong transaction và đích thư mục con.
Kiểm chứng gồm luồng DOCX hai bên qua adapter thật và stale export không ghi file.
Iteration 2 đã sửa đủ nhóm được xác minh: diện tích đầy đủ, ngày sai bị chặn,
khóa gỡ nguồn, giữ bảng chọn vị trí, số dòng nguồn/schema, rule đất sai kiểu,
trường Word lồng nhiều đoạn, dấu kiểm bằng chứng và thông tin nguồn từng ô đất.
Kiểm lưu/mở lại bằng model thật giữ dòng nguồn số 21, không đổi thành dòng 1.
Nguồn/mẫu chưa dùng vẫn giữ local; không tự xóa hoặc đặt thời hạn lưu.
Kiểm thử: 19 DOCX + 280 backend regression, 86 sidecar, 221 Node, 38 lõi regex,
78 ví dụ contract đều qua. Root chạy lại Electron iteration 2 thành công;
native picker dùng bộ trả đường dẫn giả, chưa kiểm trang Word/bản cài/corpus thật.

Đọc file gốc → review/sửa → nhận từng bản ghi → lưu Stage → chọn từng vị trí
Word → xác nhận/lưu → xuất vào thư mục đã cấp quyền. Mọi lần xuất dùng dữ liệu
đã lưu và kiểm tra nguồn, thứ tự, mã băm. File gốc không bị sửa.

Root cần review ranh giới chung với workspace/Word, kiểm tra UI và bản đóng gói
trước khi gọi là sẵn sàng dùng tại văn phòng. Không upload tài liệu khách, không
push/PR/merge. Phạm vi ảnh/OCR/Excel và tab thứ ba vẫn nằm ngoài lần này.

## Handoff kiến trúc cũ — 29/09/2026

Nên đặt bộ máy nhận diện trường ở đâu để nhiều chức năng cùng sử dụng mà vẫn có một nơi chịu trách nhiệm quản lý quy tắc và phiên bản? Đầu vào chung nên là văn bản đã chuyển đổi, hay phải giữ thêm cấu trúc riêng của ảnh, Word và bảng tính cùng vị trí trong file gốc? Kết quả nên biểu diễn trường tìm thấy, bản ghi người/tài sản, bằng chứng nguồn, phần thiếu, mâu thuẫn và các lần xuất hiện lặp như thế nào? Nên tách bước tìm trường khỏi bước ghép bản ghi và xử lý nhiễu/trùng ra sao; khi nào được tự gộp, khi nào cần người kiểm tra? Khả năng nhận diện để tạo mẫu Word nên dùng chung phần nào với bộ máy nhập dữ liệu, và ranh giới nào bảo đảm sửa đúng vị trí mà không gán sai vai trò? Cần phép thử và tiêu chí nào trên các loại đầu vào để chọn kiến trúc trước khi triển khai?

---
title: "Product Brief: Document Field Studio"
status: proposed
created: 2026-09-29
updated: 2026-09-29
---

# Product Brief: Document Field Studio

> Tên làm việc tiếng Việt: **Nhận diện dữ liệu**.

## Tóm tắt đề xuất

Document Field Studio là tab thứ ba được đề xuất cho Upload Lab. Đây là nơi
người phụ trách rule đưa tài liệu mẫu vào, xem hệ thống nhận diện trường nào,
ghép các trường thành bản ghi người hoặc tài sản ra sao và sửa rule dựa trên
kết quả thử.

Phần xử lý phía sau là một engine dùng chung cho Upload và Soạn hồ sơ. Engine
này cũng nhận văn bản thô do công cụ MarkItDown tạo ra. Phiên bản đầu tập trung
vào DOCX và văn bản thô, luôn để người dùng duyệt trước khi dữ liệu đi vào
nghiệp vụ. Tạo mẫu Word tự động là hướng giá trị quan trọng thứ hai: nhận diện
đúng trường và vị trí để thay dữ liệu mẫu bằng placeholder. Đề xuất bắt đầu
bằng gợi ý có người kiểm tra, rồi mới tăng mức tự động qua kết quả thử nghiệm.

**Từ cần biết:** regex là mẫu tìm chữ; rule là một quy tắc nhận diện; engine là
phần chạy các quy tắc; OCR là bước đọc chữ từ ảnh; placeholder là chỗ giữ chỗ
trong mẫu Word, ví dụ `[Họ tên bên chuyển nhượng]`; API là cách các phần mềm gọi
nhau theo một cấu trúc đã thống nhất.

## Vì sao sản phẩm này tồn tại

Các luồng hiện nay đều cần hiểu dữ liệu bên trong tài liệu, nhưng đang xử lý
theo từng chỗ riêng: Upload Lab bóc dữ liệu từ Word, Soạn hồ sơ nhận ảnh/PDF/
Word/Excel/text, còn công cụ MIN-137 chỉ giúp thử regex độc lập. Kết quả dễ
lệch nhau và thường mới dừng ở việc tìm thấy từng trường rời rạc.

Sản phẩm này tạo **một bộ phận nhận diện dữ liệu mà nhiều chức năng có thể dùng
chung**. Nó tìm trường, ghép đúng các trường của cùng một người hoặc tài sản,
giữ nguyên đoạn dữ liệu và vị trí trong file gốc làm bằng chứng, rồi đưa ra kết
quả để người dùng kiểm tra. Các chức năng có thể dùng cùng kết quả thay vì tự
viết lại regex.

## Vấn đề cần giải quyết

1. **Tìm đúng trường chưa đủ.** Mười ngày sinh tìm được không có ích nếu không
   biết ngày nào thuộc người nào. Đơn vị kết quả chính phải là một bản ghi
   người hoặc tài sản, không phải một túi trường rời.
2. **Mỗi đầu vào có cấu trúc khác nhau.** Ảnh OCR có thể có vị trí trên ảnh;
   Word có đoạn, bảng và thứ tự; Excel có sheet, hàng và ô; raw text từ
   MarkItDown chủ yếu còn dòng và cụm nội dung. Engine phải tận dụng phần cấu
   trúc còn lại của từng loại đầu vào.
3. **Tài liệu thật luôn có dữ liệu nhiễu và nội dung lặp lại.** Phần lời chứng
   của công chứng viên ở cuối văn bản thường nhắc lại tên, giấy tờ hoặc địa chỉ.
   Lời chứng chưa soạn xong cũng có thể tạo các mảnh dữ liệu thiếu. Nếu chỉ chạy
   regex, hệ thống dễ tạo thêm người hoặc tài sản giả.

## Người dùng chính

- **Người xây và kiểm thử rule:** cần thử nhanh trên nhiều tài liệu, xem sai ở
  đâu và biết một thay đổi làm kết quả tốt lên hay xấu đi.
- **Nhân viên nghiệp vụ:** cần duyệt các bản ghi người/tài sản trước khi đưa
  vào Upload hoặc Soạn hồ sơ.
- **Lập trình viên làm Word:** cần gợi ý vị trí placeholder thay cho việc dò và sửa tay
  toàn bộ mẫu.

## Sản phẩm hoạt động như thế nào

| Phần | Trách nhiệm |
|---|---|
| Tab trong Upload Lab | Nhập mẫu, sửa và thử rule, xem trường/bản ghi, cảnh báo nhiễu/trùng, so sánh phiên bản |
| Engine dùng chung | Giữ cấu trúc nguồn, tìm trường, ghép bản ghi và trả bằng chứng |
| Upload/Soạn hồ sơ | Cho người dùng duyệt và quyết định dữ liệu nào được ghi vào nghiệp vụ |

`Nguồn vào → Giữ cấu trúc nguồn → Tìm trường → Ghép bản ghi → Lọc nhiễu và trùng → Người dùng kiểm tra → Chuyển cho chức năng sử dụng`

Mỗi kết quả phải trả lời được ba câu hỏi:

- Hệ thống tìm thấy giá trị gì?
- Giá trị đó thuộc người/tài sản nào?
- Giá trị đến từ đâu trong file gốc?

Ba nguyên tắc bảo vệ dữ liệu:

- Luôn giữ text gốc và vị trí nguồn bên cạnh giá trị đã chuẩn hóa.
- Không tự ghép khi các thông tin dùng để nhận biết chắc chắn một người, như số
  CCCD, mâu thuẫn nhau.
- Không tự xóa bản ghi thiếu hoặc phần nghi là lời chứng; chỉ đánh dấu
  `mảnh chưa đủ`, `nghi là nhiễu` hoặc `nghi trùng` để người dùng xem.

## Phạm vi phiên bản đầu

**[ASSUMPTION — đề xuất để thử, chưa phải phạm vi đã chốt]:** ưu tiên DOCX và
văn bản thô khi triển khai đầu tiên. Tập mẫu nghiên cứu phải có cả ảnh OCR,
Word, Excel và văn bản thô ngay từ đầu để không thiết kế lệch về một loại nguồn.

- Tab Nhận diện dữ liệu trong Upload Lab, dùng tập tài liệu mẫu đã được người
  kiểm tra và ghi kết quả đúng.
- DOCX và văn bản thô là hai đầu vào của phiên bản đầu; XLSX được bổ sung ở
  bước tiếp theo vì đã có cấu trúc hàng và ô rõ.
- Kết quả nhóm thành người/tài sản, có giá trị gốc, giá trị chuẩn hóa, vị trí
  nguồn, mức tin cậy, cảnh báo và trạng thái trùng/nhiễu.
- Cho phép sửa rule, chạy lại và so sánh với kết quả đúng đã ghi trước.
- Thử nghiệm quét Word, gợi ý placeholder đã có trong danh mục và cho người dùng xem
  trước khi tạo bản sao mẫu. Engine không tự bịa vai trò pháp lý của một giá trị.

Chưa thuộc phiên bản đầu: tự ghi thẳng vào hồ sơ không qua review; tự suy luận
vai trò pháp lý; tự xóa dữ liệu nghi nhiễu; tự tạo placeholder mới; dùng tọa
độ tuyệt đối cố định cho mọi ảnh; và thay toàn bộ Document Intake trong một lần.

Nếu phiên bản đầu chứng minh được giá trị, engine sẽ trở thành lớp đọc cấu trúc
tài liệu dùng chung. Mỗi chức năng vẫn tự quyết định cách người dùng duyệt và cách dữ
liệu được ghi vào nghiệp vụ.

## Điều chưa chốt

Regex là một công cụ tìm trường; cách dùng cấu trúc nguồn để nhận diện và nhóm
vẫn phải thử trên nhiều đầu vào. Các nguyên tắc trên là hướng thiết kế đề xuất,
chưa phải thuật toán đã được chứng minh.

- Engine sẽ nằm trong một mô-đun dùng chung hay tạm đặt ở Upload Lab và cung
  cấp API riêng để các phần khác gọi?
- Upload Lab chỉ quản lý quy tắc hay cũng trực tiếp chạy bộ phân tích tài liệu?
  Theo thiết kế hiện tại, Document Intake đang phụ trách việc phân tích.
- Cấu trúc kết quả dùng chung, tiêu chí một bản ghi là “đủ”, khóa tự gộp và
  chuẩn vị trí OCR.
- Tên chính thức của tab và phạm vi tạo mẫu Word sau giai đoạn thử nghiệm.

Các điểm này phải được chốt trong thiết kế tổng thể và đặc tả giao tiếp trước
khi kết nối vào hệ thống đang chạy.

## Đo thành công bằng gì

**Đo ngay từ phiên bản đầu:** số người/tài sản được tạo đúng; số trường được
ghép đúng bản ghi; vị trí nguồn còn chính xác; bản ghi lặp từ lời chứng được
chặn mà không mất dữ liệu thật; và kết quả trên cùng một file tốt lên hay xấu
đi khi đổi quy tắc. Với Word, đo thời gian làm mẫu và số lần hệ thống chặn được
gợi ý placeholder gắn sai vai trò trước khi tạo file.

**Mục tiêu số:** chỉ chốt sau khi có tập mẫu được người kiểm tra gắn nhãn. Kết
quả MIN-137 hiện chứng minh công cụ chạy và giữ được vị trí nguồn; nó chưa chứng
minh độ chính xác.

Đọc chi tiết mô hình dữ liệu, cách xử lý từng loại file, lời chứng và lộ trình
trong [addendum.md](addendum.md).

# Phụ lục — Document Field Studio

**Trạng thái:** mục 1 là hiện trạng đã đối chiếu với mã nguồn. Các mục còn lại là
đề xuất để thử nghiệm, chưa phải đặc tả giao tiếp được duyệt. Đọc mục 7 trước
khi dùng mô hình dữ liệu để thiết kế kỹ thuật.

**Từ cần biết:** schema là cấu trúc dữ liệu; contract là đặc tả giao tiếp;
adapter là bộ đọc riêng cho từng nguồn; span là khoảng ký tự trong văn bản;
bounding box là khung tọa độ bao quanh chữ trên ảnh; profile là bộ quy tắc;
corpus là tập tài liệu thử; regression là lỗi mới xuất hiện sau một thay đổi.

## 1. Hiện trạng đã kiểm chứng

- Upload Lab hiện được mô tả là có đúng hai tab nghiệp vụ, nên việc thêm tab
  thứ ba phải cập nhật lại SOT giao diện: `upload_lab/README.md:119-127` và
  `upload_lab/docs/spec_UI.md:16-17`.
- Upload Lab đã có `regex_lab.py` và catalog regex cho Word, nhưng catalog hiện
  tập trung vào tiêu đề, đương sự và tài sản sau khi đọc text:
  `upload_lab/docs/regex-rules.md:10-16`.
- Kiến trúc hiện tại giao regex, bóc trường và ghép người/tài sản cho Document
  Intake: `docs/architecture/TECH_STACK.md:51-52` và
  `docs/architecture/OPEN_DECISIONS.md:97-99`.
- Document Intake hiện nhận năm loại nguồn `image`, `pdf`, `docx`, `xlsx`,
  `text`, và đầu ra là suggestion cho `person` hoặc `asset`:
  `notary_v2/services/document_intake/models.py:16-19`.
- Adapter Excel đang coi mỗi hàng dữ liệu là một person suggestion và giữ
  sheet/cell/row; adapter Word đang đọc đoạn và bảng; adapter text hiện chỉ giữ
  span của toàn bộ text: `notary_v2/services/document_intake/adapters/excel.py:1-4`,
  `notary_v2/services/document_intake/adapters/docx.py:26-42`,
  `notary_v2/services/document_intake/adapters/text.py:21-40`.
- Contract Word hiện yêu cầu mọi placeholder có mapping rõ và cấm resolver đoán
  từ tên placeholder: `notary_v2/docs/platform/document-generation/technical.md:25-32`.
- Công cụ MIN-137 đã giữ được span gốc và tạo ứng viên người/tài sản theo vùng,
  nhưng file engine vẫn tuyên bố là công cụ độc lập, không nhập code sản phẩm:
  `tools/regex_workbench/engine.py:1-1`, `tools/regex_workbench/README.md:59-67`.

Kết luận: hướng mới có nền kỹ thuật để tiếp tục, nhưng thay đổi ranh giới sản
phẩm. Cần sửa quyết định kiến trúc và spec giao diện trước khi nối runtime.

## 2. Mô hình kết quả đề xuất

Đây là phác thảo thảo luận, phụ thuộc quyết định schema ở mục 7. Một bản ghi
có thể đồng thời thiếu trường và nghi trùng; các nhãn dưới đây không loại trừ
nhau. Cần lưu riêng độ đầy đủ, nghi nhiễu, quan hệ trùng và xung đột.

### FieldObservation — một trường được nhìn thấy

| Thuộc tính | Ý nghĩa |
|---|---|
| `field_type` | Loại trường, ví dụ `person.name`, `person.dob`, `asset.serial` |
| `raw_value` | Giá trị đúng như nguồn |
| `normalized_value` | Giá trị đã chuẩn hóa, không ghi đè giá trị gốc |
| `source_ref` | File, trang/sheet, hàng/ô, đoạn, span hoặc khối OCR |
| `rule_id` / `rule_version` | Rule nào tạo ra kết quả |
| `confidence` | Mức chắc chắn của riêng trường |
| `warnings` | Lỗi định dạng, mâu thuẫn hoặc thiếu bằng chứng |

### EntityCandidate — bản ghi được ghép

| Thuộc tính | Ý nghĩa |
|---|---|
| `entity_type` | `person` hoặc `asset` |
| `fields` | Các FieldObservation được ghép vào bản ghi |
| `region_refs` | Các vùng nguồn tạo nên bản ghi |
| `completeness` | Có đủ các trường cần thiết cho loại tài liệu này hay chưa |
| `state` | `candidate`, `fragment`, `noise_candidate`, `duplicate_candidate` |
| `duplicate_of` | Mã của bản ghi mà ứng viên này có thể trùng với |
| `conflicts` | Các trường mâu thuẫn khiến hệ thống không được tự gộp |

“Đủ” không có một công thức chung cho mọi loại tài liệu. Ví dụ CCCD có thể cần
họ tên + số CCCD; danh sách Excel có thể chỉ có họ tên + ngày sinh; tài sản có
thể cần số giấy chứng nhận hoặc thửa/tờ bản đồ. Mỗi profile phải khai báo bộ
trường tối thiểu và các khóa nhận dạng mạnh.

Các ví dụ trên chưa đủ để tự gộp: một giấy chứng nhận có thể chứa nhiều thửa;
số thửa/tờ phải kèm địa bàn; hai người có thể trùng tên và ngày sinh. Cần tách
việc một thực thể xuất hiện nhiều lần khỏi việc có nhiều thực thể khác nhau.

## 3. Cách xử lý theo nguồn

Thử trên cả bốn loại nguồn trước khi chốt cách nhóm. Thứ tự triển khai DOCX/
văn bản thô trước chỉ là giả định tiến độ, không loại ảnh và Excel khỏi nghiên cứu.

| Nguồn | Cấu trúc nên giữ | Cách nhóm ban đầu |
|---|---|---|
| Ảnh/OCR | text, trang, khối/dòng, bounding box nếu OCR trả về | Nhãn gần giá trị, cùng hàng/cột/khối; dùng text fallback khi không có tọa độ |
| DOCX | đoạn, bảng, hàng/ô, thứ tự, style, section, header/footer | Bảng/hàng là ranh giới mạnh; đoạn liên tiếp và tiêu đề là ranh giới mềm |
| XLSX | workbook, sheet, hàng, cột, ô, merged cell | Một hàng thường là một bản ghi; header ánh xạ sang loại trường |
| Raw text | dòng, đoạn, khoảng trống, span ký tự, heading | Cụm dòng liên tiếp quanh trường nhận dạng mạnh; ngắt khi gặp heading hoặc bản ghi mới |

Tọa độ OCR chỉ có nghĩa trong đúng ảnh và đúng lần OCR. Không dùng số tọa độ
cố định như “x > 400 luôn là ngày sinh”. Dùng quan hệ tương đối như “giá trị ở
bên phải nhãn Ngày sinh trong cùng dòng” sẽ bền hơn.

## 4. Xử lý lời chứng, dữ liệu thiếu và trùng lặp

Quy trình đề xuất gồm bốn bước:

1. **Chia vùng:** nhận diện phần nội dung chính, lời chứng, chữ ký, phụ lục và
   các vùng chưa rõ.
2. **Tạo ứng viên:** tìm trường và ghép trong từng vùng trước. Không kéo một
   ngày sinh ở lời chứng lên ghép với một tên ở phần đầu chỉ vì đang thiếu.
3. **Chấm độ đầy đủ:** profile xác định trường nào là khóa mạnh và trường nào
   chỉ bổ sung. Bản ghi thiếu được giữ thành `fragment`.
4. **So trùng:** so khóa mạnh, các trường trùng khớp, khoảng cách vùng và vai
   trò của vùng. Lời chứng là tín hiệu giảm ưu tiên, không phải lý do tự xóa.

Ví dụ: phần đầu có Nguyễn Văn A + CCCD 0123 + ngày sinh; lời chứng chỉ lặp
Nguyễn Văn A + CCCD 0123. Hệ thống có thể đánh dấu bản ghi lời chứng là trùng
với bản chính. Nếu lời chứng ghi CCCD 9999, phải báo xung đột và giữ cả hai để
user xem.

Lời chứng cũng có thể lặp một bản ghi đầy đủ, hoặc chứa thông tin duy nhất còn
thiếu ở phần chính. Vì vậy độ đầy đủ và vị trí lời chứng chỉ là hai tín hiệu,
không đủ để quyết định loại bỏ. Khi nhiều lần xuất hiện được liên kết với cùng
một người, phải giữ mọi vị trí để chức năng làm mẫu Word vẫn tìm được từng chỗ.

## 5. Chế độ tạo mẫu Word có hỗ trợ

1. Kiểm kê vùng text của Word: đoạn, bảng, đầu/chân trang, hộp văn bản và các
   đoạn định dạng nhỏ (run). Vùng chưa hỗ trợ phải được báo rõ.
2. Nhận diện giá trị và giữ đúng vị trí trong cấu trúc Word.
3. So với danh mục placeholder đã duyệt rồi đưa ra gợi ý.
4. User xác nhận từng gợi ý hoặc một nhóm gợi ý.
5. Tạo bản sao Word mới, thay giá trị bằng placeholder và chạy kiểm tra
   placeholder chưa map hoặc vị trí làm hỏng định dạng.

Phiên bản đầu nên chỉ hỗ trợ gợi ý và xem trước. Tự động thay toàn bộ chỉ được
mở khi corpus mẫu Word chứng minh rằng thao tác giữ đúng định dạng và vai trò.

Vị trí trong văn bản do MarkItDown xuất ra không mặc nhiên là vị trí có thể
sửa trong file Word gốc. Cần giữ liên kết tới phần tử Word và phiên bản file;
nếu mất liên kết, chỉ trả gợi ý, không thay bằng cách tìm toàn bộ chuỗi giống
nhau. Cùng một giá trị có thể xuất hiện ở nhiều người hoặc nhiều vai trò.

## 6. Ma trận thử nghiệm cần có

Mỗi hàng dữ liệu thử phải có nguồn, loại tài liệu, text/cấu trúc đã đọc, bản
ghi đúng do người gắn nhãn, vùng nhiễu và kết quả mong đợi.

| Nhóm thử | Tối thiểu cần phủ |
|---|---|
| Nhiều người | 1, 2, 10 người; trường giống nhau; thiếu một vài trường |
| Nhiều tài sản | nhiều thửa/một giấy; nhiều giấy/một người; trường dùng chung |
| Lời chứng | lặp đủ; lặp thiếu; chưa soạn xong; có giá trị mâu thuẫn |
| Dữ liệu thiếu thật | chỉ có tên/ngày sinh; thông tin duy nhất ở lời chứng; không có khóa mạnh |
| DOCX | paragraph, table, header/footer, text chia run |
| XLSX | header khác tên, merged cell, dòng trống, nhiều sheet |
| Raw text | có heading, không heading, lỗi xuống dòng, nhiều cụm liên tiếp |
| OCR | có/không bounding box, xoay ảnh, hai cột, OCR sai một ký tự khóa |

Chỉ số phải có cả mức trường và mức bản ghi. Nếu 10 trường đúng nhưng ghép sai
người, phép thử mức bản ghi phải tính là sai.

## 7. Các quyết định còn mở

1. **Vị trí code engine:** module dùng chung dưới hệ thống, package riêng, hay
   tạm nằm trong Upload Lab nhưng có API sạch. Khuyến nghị tách lõi khỏi UI.
2. **Ai sở hữu nghiệp vụ:** hướng mới chuyển nơi xây/quản lý rule về Upload
   Lab, trong khi kiến trúc hiện giao parser cho Document Intake. Owner cần sửa
   quyết định cũ hoặc ghi rõ Upload Lab chỉ là UI quản trị, Document Intake vẫn
   chạy engine dùng chung.
3. **Schema kết quả:** mở rộng contract intake hiện tại hay tạo contract dùng
   chung mới. Theo quy tắc kho mã nguồn, đặc tả giao tiếp phải được duyệt trước
   khi triển khai.
4. **Định nghĩa bản ghi đủ:** cần theo từng profile và loại giấy tờ.
5. **Khóa chống trùng:** trường nào đủ mạnh để tự gộp; trường nào chỉ báo user.
6. **Bounding box:** chuẩn tọa độ, đơn vị, trang và cách giữ liên kết với text.
7. **Phạm vi Word:** chỉ gợi ý placeholder hay cho phép tạo file mẫu hoàn chỉnh.

## 8. Lộ trình đề xuất

- **Giai đoạn 0 — Ranh giới:** chốt nơi quản lý/chạy engine và kế hoạch tái sử
  dụng Document Intake, sau đó duyệt đặc tả giao tiếp trước task triển khai.

- **Giai đoạn A — Định nghĩa và corpus:** chốt schema, gắn nhãn mẫu nhiều nguồn,
  định nghĩa “bản ghi đúng”, noise và duplicate.
- **Giai đoạn B — Lõi chung:** chuyển khả năng giữ span/region từ MIN-137 thành
  engine có bộ đọc cho từng nguồn, khả năng ghép bản ghi và báo cáo lỗi phát
  sinh sau thay đổi.
- **Giai đoạn C — Tab Upload Lab:** xây màn thử rule, review bản ghi và so sánh
  phiên bản. Chưa ghi dữ liệu nghiệp vụ.
- **Giai đoạn D — Chức năng sử dụng đầu tiên:** nối một luồng có giới hạn, khuyến nghị
  trường của tab Upload, sau khi contract được duyệt; Soạn hồ sơ dùng lại tiếp theo.
- **Giai đoạn E — Word assistant:** nhận diện vị trí và gợi ý placeholder trên
  bản sao tài liệu.

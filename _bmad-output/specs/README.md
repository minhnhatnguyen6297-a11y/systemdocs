# Nền sản phẩm

**Cập nhật:** 15/10/2026. Đọc đầu phiên để hiểu sản phẩm; sau đó đọc sổ tay và spec module đang làm. Quy tắc dưới đây mô tả điều cần có, không chứng minh code đã hoàn thành.

## 1. Người dùng và công việc

Sản phẩm dành cho nhân viên, chuyên viên văn phòng công chứng. Công việc xoay quanh soạn văn bản, số hóa văn bản đã soạn và theo dõi công việc tiếp tục phát sinh quanh Người, Tài sản và Hồ sơ.

Máy giảm việc đánh máy lại: lấy tối đa thông tin có căn cứ từ nguồn, đặt vào đúng trường chuẩn để người dùng kiểm tra, sửa và sử dụng. Không đoán dữ liệu cho đủ ô. Ba module hỗ trợ ba nhóm việc, không mặc định tự chuyển hồ sơ hoặc dùng chung một mã hồ sơ.

## 2. Soạn thảo — notary_v2

Soạn hồ sơ là chức năng trung tâm. Người dùng nhận giấy tờ/file/chữ → kiểm tra thông tin Người/Tài sản → bổ sung vai trò, quan hệ khi cần → xuất Word theo mẫu.

| Thành phần | Vai trò |
|---|---|
| Danh sách hồ sơ | Tìm và mở hồ sơ đang/đã soạn. Đây là tên mong muốn thay Tổng quan; nhãn, tìm kiếm và bộ lọc còn cần chốt chi tiết. |
| Input | Đọc ảnh, PDF, Word, Excel hoặc chữ thành gợi ý có nguồn. Phạm vi từng định dạng theo spec module, không hứa đọc mọi file. |
| Stage | Kiểm tra/sửa thông tin Người và Tài sản. Bấm Cập nhật mới lưu và áp dụng cho các phần sử dụng. |
| Pool | Những người đã lưu trong Stage nhưng chưa được gán lên Diagram đang xem; không phải kho riêng. |
| Diagram | Gán vai trò và quan hệ bằng kéo thả/chọn trong thẻ; có Hai bên và Thừa kế. Không sửa thông tin Người/Tài sản thay Stage. |
| Xuất Word | Điền dữ liệu đã lưu vào placeholder — vị trí đánh dấu trong mẫu. |

**Triết lý: điền dần, không ép hoàn tất mọi bước.** Có dữ liệu nào thì điền trường đó; trường hợp lệ chưa có dữ liệu để trống. Một văn bản chỉ cần Stage không phải dựng sơ đồ không cần thiết. Chỉ chặn hoặc hỏi xác nhận khi có nguy cơ cụ thể như dùng dữ liệu chưa cập nhật, làm gãy quan hệ hoặc không thể tạo file đúng. Điều kiện chặn hiện hành còn phải đồng bộ theo định hướng này; không coi việc sửa docs là đã sửa chương trình.

Tab Word riêng dự kiến giúp nhập văn bản, đề xuất placeholder, tải về sửa rồi nhập lại để lưu mẫu lâu dài. Tab này chưa có spec chi tiết/chưa triển khai; khác nút Xuất Word đang nằm trong Soạn hồ sơ.

## 3. Upload — upload_lab

Đọc kho Word trên máy, đối chiếu sổ của website nghiệp vụ, chọn hồ sơ còn thiếu, bóc trường và điền sẵn biểu mẫu trên trình duyệt. Người dùng tự kiểm tra và bấm Lưu. Điền form không đồng nghĩa lưu thành công.

Số công chứng được đối chiếu theo năm và nguồn website; phải báo số thiếu, lỗi và trùng. Mỗi website có bộ xử lý riêng cho đăng nhập, lấy sổ, đối chiếu và điền form.

Owner đánh giá module tương đối hoàn thiện; hướng tiếp theo chủ yếu là chất lượng regex và website mới. Đánh giá này không thay bằng chứng kiểm chức năng.

## 4. NotaryOffice — theo dõi công việc

Ngoài soạn văn bản còn có chuỗi việc dài như nộp hồ sơ chuyển nhượng, chỉnh lý giấy chứng nhận, đo đạc, cập nhật địa chỉ. Module giúp trả lời “Hồ sơ đang ở đâu, chờ việc gì?” bằng dấu vết công việc thay vì chỉ dựa vào trí nhớ.

Hướng chính: thay đổi nội dung Word trong phạm vi được phép → bóc Người/Tài sản/Hồ sơ liên quan → thẻ đề xuất ngắn → nhân viên xác nhận/sửa → dòng thời gian. Dấu vết sửa Word chưa chứng minh một thủ tục đã hoàn tất. Đây là công cụ hỗ trợ, không áp quy trình quản lý doanh nghiệp cứng nhắc. Thiết kế chi tiết còn Draft, chưa có runtime đã nghiệm thu.

## 5. Zalo và công nghệ chung

Zalo ban đầu được định hướng làm nguồn Input. Hiện nghiên cứu riêng do vấn đề pháp lý cần làm rõ; không tự nối vào hệ thống. Các đề xuất tích hợp cũ không phải quyền triển khai.

OCR chuyển ảnh thành chữ: hiện dùng Qwen-VL-OCR qua đường cloud đã duyệt; OCR local là hướng dài hạn. Regex bóc chữ thành trường. Đọc Word tùy luồng: IFilter cho DOC; python-docx cho Upload DOCX; Document Intake đọc XML bằng lxml để giữ vị trí. Playwright hỗ trợ điền trình duyệt. SQLite theo module là hiện trạng tài liệu; database nghiệp vụ chung là đích, engine chung và cách chuyển dữ liệu chưa chốt.

Electron là vỏ ứng dụng; Python/FastAPI xử lý nghiệp vụ. Module giữ quyền ghi dữ liệu của mình; dùng chung ứng dụng không cho phép tự nối hoặc gộp dữ liệu.

## 6. Khái niệm và nguyên tắc

- Hồ sơ là đơn vị công việc trong từng module. CCCD, GCN, cặp thửa/tờ, số công chứng là bằng chứng đối chiếu, không tự trở thành mã hồ sơ chung.
- Bản nháp Stage/Diagram là sửa chưa lưu. Draft Case của Office là ứng viên chưa xác nhận. Trạng thái hồ sơ `draft` phục vụ quy tắc quản lý hồ sơ. Ba nghĩa không thay thế nhau.
- Nguồn gốc → chữ đọc được → dữ liệu chuẩn hóa → gợi ý suy ra nếu cần → người có thẩm quyền xác nhận. Không phải dữ liệu nào cũng cần suy luận.
- Giữ nguồn và giá trị gốc; không sửa raw để che lỗi. Máy không tự nâng OCR/AI thành dữ liệu đã xác nhận.
- Đầu ra nghiệp vụ phải theo trường, kiểu, định dạng, cách nhóm và đích lưu đã chốt trong DB/contract. Raw không bắt buộc mang schema DB. Không sinh trường mồ côi hoặc nhét sai nghĩa vào ghi chú. Trường mới phải được chốt trước.
- Ngày nhập/hiển thị giữ đúng độ đầy đủ: năm riêng vẫn là năm. Ngày quy ước chỉ dùng trong tính toán, không ghi đè thành dữ kiện đã biết.
- Máy hỗ trợ thao tác; người dùng kiểm tra và chịu trách nhiệm xác nhận. Không tự động hóa phán quyết pháp lý.
- Thiết kế gọn, tối ưu xử lý; không tự thêm chức năng, cơ chế dự phòng hoặc bộ công cụ kiểm thử ngoài phạm vi được phép.
- Không ép chuyên viên đổi thói quen cần cho nghiệp vụ. Không quay màn hình, ghi phím hoặc chấm công bằng dấu vết hồ sơ.
- Dữ liệu ở lại văn phòng; chỉ gọi dịch vụ ngoài tại điểm đã duyệt. Không ghi giấy tờ, raw OCR, cookie hoặc secret vào log rộng.
- Quy ước sản phẩm phục vụ phần mềm không phải kết luận về pháp luật.

## 7. Đọc và cập nhật

Đầu phiên: AGENTS → bản nền này → sổ tay → spec module liên quan. Chỉ đọc quy tắc chuyên sâu khi làm đúng phần đó; không nạp lịch sử mặc định.

Spec viết liền mạch hành vi đang áp dụng, kể cả trùng quyết định. Decision lưu điều đã chọn, lý do và phương án đã loại/chốt bỏ qua. Backlog giữ issue/task và trạng thái; sổ tay tóm tắt việc hiện tại, không là bản sao backlog. Khi quyết định đổi, cập nhật cả spec và decision.

| Đọc tiếp khi cần | Nội dung |
|---|---|
| [Sổ tay](product-overview.md) | Việc hiện tại, màn hình và điểm vào code |
| [Soạn thảo](notary_v2/README.md) | Luồng sử dụng đầy đủ |
| [Upload](upload_lab/README.md) | Đối chiếu và điền website |
| [NotaryOffice](notaryoffice/README.md) | Theo dõi công việc dự kiến |
| [Dữ liệu chung](shared/data-rules.md) | Đầu ra, quyền ghi và ranh giới hệ thống |
| [Bóc tách](shared/extraction-rules.md) | Quy tắc trường và nguồn Word |
| [Backlog](../backlog) | Ghi nhận việc chưa làm; ghi nhận không phải duyệt triển khai |

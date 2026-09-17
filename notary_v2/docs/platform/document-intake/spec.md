# Tiếp nhận dữ liệu và cửa sổ OCR

Chương của [SPEC notary_v2](../../SPEC.md); cập nhật 17/09/2026.
Trạng thái: yêu cầu đích đã chốt; chưa tuyên bố code đạt.
Chỉnh quy tắc input/OCR tại file này. Quy tắc sửa, duyệt và lưu dữ liệu chỉ ở
[Stage / Cập nhật](../case-workspace/contract.md).

## 1. Các nguồn đầu vào

- Ảnh/PDF từ máy.
- Excel, nhập tay, tìm và chọn Người/Tài sản đã có.
- [Zalo](../zalo-document-inbox/spec.md) là nguồn tài liệu, không phải một quy trình duyệt riêng.
- QR giấy tờ: dự phòng, chưa triển khai theo định hướng mới; không ghép lại vào OCR.

Mỗi nguồn cần giữ đủ thông tin để người dùng đối chiếu dữ liệu với ảnh/tài liệu
đã nhập. Các nguồn khác nhau không được tạo các bản dữ liệu có cách sửa/lưu khác nhau.

## 2. Loại giấy tờ và mức hỗ trợ

| Loại | Phạm vi |
|---|---|
| CCCD/căn cước | Đã có OCR; quy trình sửa/duyệt còn phải đưa về Stage |
| Sổ đỏ/giấy chứng nhận | Đã có OCR, xử lý mặt khác CCCD; hỗ trợ bài toán nhiều sổ/nhiều tài sản |
| Khai tử | Đã có đường nhận diện/parse trong source; Stage và luồng duyệt chung chưa hoàn chỉnh. Phần giao diện/triển khai giấy tờ khác làm sau |
| Khai sinh, đăng ký kết hôn và biểu mẫu khác | Dự phòng, triển khai sau; không thiết kế sâu trong lần này |
| Giấy tờ không nhận diện chắc chắn | Không đoán để đẩy sai dữ liệu vào Stage |

Khai tử đã có nhánh parser trong [ocr_ai.py:2121](../../../routers/ocr_ai.py#L2121),
nhưng như vậy chưa chứng minh đã có cửa sổ, Stage và duyệt hoàn chỉnh. Giữ
quy ước nhập đã được chốt trước đây ở [R-014/015 của bản Zalo cũ](../zalo-document-inbox/reference-2026-08.md):
khai tử trả dữ liệu Người với ngày chết; số trích lục là số giấy tờ, ngày
ký là ngày cấp (không lấy ngày đăng ký), cơ quan cấp là nơi cấp và nơi chết là
địa chỉ theo bản mapping cũ. Đây là quy tắc giữ lại cho khi triển khai giấy
tờ khác, không phải khẳng định schema/Stage hiện hỗ trợ lưu đủ các trường.

## 3. Một cửa sổ OCR chung — triển khai có điều kiện

Chủ dự án đã chọn hướng **một cửa sổ OCR**, tự phân loại giấy tờ rồi xử lý riêng
từng loại. **Chỉ thực hiện khi engine đủ tốt để tự động phân loại giấy tờ.**

- Gộp giao diện không gộp quy tắc ghép mặt CCCD với quy tắc sổ đỏ.
- Stage từng loại dữ liệu vẫn riêng; một tài sản một cột theo SPEC tổng.
- Chưa qua gate thì giữ các cửa sổ hiện có; không hứa đã có cửa sổ chung.
- Cần bộ mẫu có CCCD, nhiều sổ, thứ tự lẫn lộn, thiếu mặt, giấy tờ ngoài phạm vi,
  ảnh mờ và trường hợp dễ nhầm. Chủ dự án duyệt mức đạt trước khi chuyển UI.
- Ngưỡng số liệu, tập mẫu và cách xử lý trường hợp không chắc còn mở.
  Không tự chốt một tỷ lệ đúng hoặc dùng vài ảnh chạy được làm bằng chứng đủ tốt.
- Quy tắc chỉ xem, đóng không xóa và sửa tại Stage không phụ thuộc gate này;
  các cửa sổ hiện có cũng phải tiến tới đáp ứng chúng.

## 4. Cửa sổ OCR chỉ để xem và đưa dữ liệu vào Stage

- Giữ tạm ảnh cùng kết quả OCR gốc; cho xem lại nguồn của từng kết quả.
- Kết quả tại cửa sổ OCR **không cho sửa**; dữ liệu đọc sai được sửa tại Stage.
- Đưa kết quả vào Stage là tạo nháp, không phải xác nhận hay ghi dữ liệu nghiệp vụ.
  Tên nút phải thể hiện đúng việc đưa vào Stage, không khiến user tưởng đã lưu hồ sơ.
- Bấm `×` chỉ ẩn/đóng; không xóa ảnh, không xóa kết quả tạm, không reset hoặc tự lưu.
- Mở lại cửa sổ trong phiên làm việc dùng dữ liệu tạm đã có, không OCR lại chỉ
  vì mở lại. Yêu cầu OCR lại phải là thao tác chủ động.
- Thêm OCR không được tự xóa kết quả chưa xử lý hoặc tự gộp người do trùng CCCD.
- Với CCCD, chủ động đưa cùng kết quả OCR vào Stage lần nữa tạo một hàng nháp
  khác, không âm thầm cập nhật hàng trước; người dùng xử lý trùng trước khi
  Cập nhật toàn cục. Kết quả OCR mới hiển thị trước nhưng giữ kết quả cũ để so.
- Dọn cache sau cập nhật thành công theo chương Stage. Đây không phải quyền
  xóa file gốc trên máy, media nguồn Zalo hay dữ liệu của lô khác.
- Bền vững qua reload/đóng app và thời hạn cache toàn module còn mở; không
  đồng nhất yêu cầu này với chính sách 72 giờ của lô Zalo.

## 5. CCCD và sổ đỏ xử lý khác nhau

CCCD:

- Có thể nhận nhiều ảnh; cần gắn đúng ảnh nguồn với người được đọc.
- Nếu kết quả từ hai mặt, xem nguồn phải thấy cả hai.
- Thiếu mặt không tự ngăn đưa nháp vào Stage; dữ liệu nào không biết thì để rõ
  thiếu. Kiểm tra khi cập nhật theo chương Stage, không tự bịa dữ liệu bổ sung.
- Trùng người không tự gộp hoặc xóa.

Sổ đỏ:

- Phân biệt loại sổ, ảnh/mặt, phần thông tin chung của sổ và từng tài sản.
- Một hoặc nhiều sổ có thể cung cấp nhiều tài sản. Không dùng serial làm bằng
  chứng “chỉ được có một tài sản”.
- Không áp logic ghép trước/sau CCCD cho sổ; kết quả phải truy lại được các ảnh nguồn.
- Thửa/tờ, diện tích, loại đất, số vào sổ, ngày/cơ quan cấp và thông tin chủ sử
  dụng chỉ là kết quả đọc chờ soát, không tự tạo quan hệ sở hữu đã xác nhận.
- [property-rules.md](property-rules.md) giữ chi tiết parser/heuristic cũ để
  kiểm chứng với code; không có quyền tự đặt nghiệp vụ hoặc khóa định danh.

## 6. Không làm và kiểm tra đạt

Không khôi phục local OCR, QR rescue hoặc thêm nhà cung cấp OCR.
Công nghệ đọc [TECH_STACK.md](../../../../TECH_STACK.md), không chọn lại ở đây.
Định danh dùng chung đọc [contracts/entities.md](../../../../contracts/entities.md).
API hiện có chỉ là bằng chứng triển khai; task tài liệu không đổi contract.

Tiêu chí đích: OCR chỉ xem; đóng/mở không mất ảnh/kết quả; sửa tại Stage; nhiều
tài sản cùng sổ không bị ép thành một tài sản; phân loại không chắc không đẩy
nhầm loại; chưa đạt engine thì chưa gộp cửa sổ.

Đối chiếu gap/source tại [SPEC §7](../../SPEC.md#7-yêu-cầu-đích-so-với-code-và-câu-hỏi-còn-mở).

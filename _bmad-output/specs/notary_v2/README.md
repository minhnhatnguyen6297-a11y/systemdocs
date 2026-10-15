# Soạn thảo hồ sơ

**Cập nhật:** 15/10/2026. Spec chính của module. Định hướng mới được ghi rõ; lần gom docs không sửa code hay nghiệm thu runtime.

## 1. Mục đích và luồng

Giảm đánh máy lại: nhận giấy tờ/chữ, kiểm tra Người/Tài sản, gán quan hệ khi văn bản cần rồi xuất Word. Luồng Input → Stage → Pool/Diagram → Word cho phép làm dở; không bắt hoàn thiện quan hệ không phục vụ văn bản đang soạn.

Stage giữ thông tin Người/Tài sản; Diagram giữ vai trò/quan hệ; Word dùng dữ liệu đã lưu. Một phần chưa đủ thông tin phải được chỉ rõ, không tự điền cho đủ.

## 2. Danh sách hồ sơ

Tên mong muốn là Danh sách hồ sơ. Người dùng xem danh sách, tìm/lọc, tạo nháp và mở hồ sơ. Nhãn trạng thái, người tạo, tên/ngày tạo là hướng mô tả; danh sách nhãn, nguồn tìm kiếm và trường lọc chưa chốt đầy đủ.

Chọn Thừa kế hoặc Hai bên khi tạo nháp. Loại không hỗ trợ hiện lý do và khóa thao tác không có khả năng, không tự chuyển sang Thừa kế. Tạo hồ sơ lần đầu chưa cần Diagram; intake/evaluate nháp không ghi database. Quy tắc đổi loại của hồ sơ đã lưu còn chờ quyết định, không suy việc chọn loại lúc tạo thành quyền tự đổi domain.

Chỉ hồ sơ `draft` được xóa. Xóa trong một lần ghi trọn vẹn: dọn dữ liệu thuộc hồ sơ nếu không còn được hồ sơ khác, participant, liên kết tài sản hoặc snapshot tham chiếu. Danh bạ người nhận ủy quyền tái dùng không bị xóa theo hồ sơ; không quét danh bạ mồ côi ngoài phạm vi. Lỗi phải khôi phục toàn bộ.

Thống kê Người/Tài sản đếm mỗi bản ghi thực sự gắn hồ sơ một lần, không đếm danh bạ rời; tài sản vừa chính vừa liên kết không đếm hai lần.

<a id="input"></a>
## 3. Input — đọc và kiểm tra nguồn

Nhận ảnh/PDF, DOCX, XLSX và chữ dán; tạo gợi ý có nguồn, không tự ghi hồ sơ, gán quan hệ hoặc chọn người nhận. Zalo đang tách riêng, không phải đầu vào đã tích hợp.

Giới hạn intake: tối đa 8 nguồn/lượt, 20 MB/file, PDF 50 trang, chữ 100.000 ký tự. Backend có thể siết chặt hơn, không tự nới. DOCX giữ vị trí đoạn/bảng theo XML; XLSX đọc bảng; ảnh qua OCR Qwen đã duyệt, không tự dùng QR/local OCR cứu lỗi.

Người dùng thấy nguồn, giá trị đọc được/chuẩn hóa, cảnh báo và lỗi từng nguồn. Sửa gợi ý rồi Đưa vào Stage chỉ tạo bản nháp. Phân tích thêm không làm mất gợi ý đang sửa; lỗi một nguồn vẫn giữ kết quả nguồn khác và báo kết quả một phần. Phản hồi đến muộn của hồ sơ cũ bị bỏ.

Không chắc ranh người/tài sản thì giữ nguồn và báo mơ hồ; nhiều giá trị phải chọn/sửa trước khi nhận. Trùng giấy tờ/serial chỉ cảnh báo, không tự gộp. Không suy giới tính từ tên, vai trò/quan hệ/sở hữu từ lời văn. Một file nhiều người/tài sản không mặc định là một hồ sơ.

Nhập Word giữ chữ lấy được ở đúng ô để sửa, kể cả lỗi gõ/dính chữ; không thêm ô nguyên văn hoặc tự sửa tên cơ quan. Ngày sai lịch, diện tích âm/không hữu hạn phải sửa; không lấy riêng năm để che ngày sai. Diện tích `1.234,5` đọc được; chỉ `1.234` thì giữ nguyên + báo mơ hồ. Thiếu trường vẫn cho kiểm tra/bổ sung; không vượt giới hạn khi nhận vào Stage.

Ảnh nhập tay được xem lại đúng nguồn. Không lưu bản nháp giấy tờ vào localStorage/log. Chỉ Cập nhật thành công mới ghi dữ liệu nghiệp vụ.

<a id="stage"></a>
## 4. Stage — sửa thông tin và Cập nhật

Người sửa theo dòng; tài sản theo cột. Thêm/sửa/xóa/sắp xếp chỉ đổi bản nháp. Mỗi dòng có `row_id` ổn định; ID database có thể chưa có trước lần lưu đầu. Sửa Người/Tài sản tại Stage, không sửa từ Pool hoặc Diagram.

| Nhóm | Quy tắc |
|---|---|
| Người | Sáu trường nghiệp vụ chính: tên, sinh, chết, số giấy tờ, ngày cấp, địa chỉ; có giới tính và trường kỹ thuật. Chỉ họ tên bắt buộc. Giới tính Nam/Nữ/trống; ngày đúng lịch hoặc năm riêng. Giấy tờ/địa chỉ có thể trống. |
| Giấy tờ | Người sống suy loại/nơi cấp/nhãn cư trú theo ngày cấp và mốc 01/10/2024; thiếu ngày để trống. Người chết dùng bằng chứng giấy tờ đã xác nhận, không mặc định nơi cấp. Nhãn nơi cấp phải phân biệt CCCD và giấy khai tử; địa chỉ người chết mang nhãn Nơi chết theo quy tắc đã có. |
| Tài sản | Tối đa 3; thứ tự 1..3 có ý nghĩa với dấu Chủ/Nhận. Serial nguyên văn, có thể trống/trùng, không ép mẫu hoặc thay mã XX. Địa chỉ không rỗng khi commit; thửa/tờ tùy chọn. |
| Loại đất | Mỗi tài sản tối đa 20 cụm loại đất–diện tích–thời hạn. Có thể để danh sách trống. Giữ vị trí trống; bỏ thời hạn lẻ cấp tài sản, không tự đắp vào cụm. |
| Hồ sơ | Nơi niêm yết nhập tay; người nhận ủy quyền từ danh mục/tạo mới; nội dung việc nhập tay. Ba dòng đặt dưới tài sản. |

Tên và định dạng trường giữ chuẩn DB; alias cũ cần ánh xạ. Hai alias của cùng trường trái nhau phải báo lỗi, không chọn ngầm. Cụm đất lưu `property_land_rows`, duy nhất theo tài sản và vị trí; JSON cũ chỉ tương thích. Tên token cụm viết đủ `loaidat<M><N>`, `dientich<M><N>`, `thoihan<M><N>`: M là cụm, N là tài sản; không thêm dạng rút gọn gây lẫn cụm 12 với tài sản 2.

Thừa kế cần `owner_row_id` theo contract lưu hiện hành; Hai bên không nhận trường đó, tối đa 30 người. Hồ sơ cũ hơn 3 tài sản vẫn đọc đủ và cảnh báo; commit hiện chặn đến khi còn tối đa 3. Đây là giới hạn hiện hành cần xem xét riêng nếu thay đổi, không tự bỏ vì triết lý điền dần.

**Cập nhật:** kiểm toàn bộ Stage → ghi Người/Tài sản → dọn tham chiếu Diagram của đối tượng đã xóa → tính lại → tăng phiên bản → lưu trọn vẹn. Một dòng lỗi thì không lưu nửa chừng; báo đúng ô và giữ bản nháp. Lần đầu tạo hồ sơ dùng cùng `idempotency_key` khi thử lại sau timeout để tránh tạo trùng.

Mọi ghi gửi phiên bản đã đọc (`base_revision`); nếu server có bản khác, báo xung đột và cho tải bản mới hoặc giữ nháp để sao chép, không ghi đè cưỡng bức. Hồ sơ khóa chỉ đọc, vẫn xem/sao chép và dùng thao tác đọc được cho phép.

Không chặn chuyển tab chỉ vì đang nhập. Chuyển module phải giữ nháp; rời/đóng khi có thay đổi chưa lưu phải cảnh báo. Cập nhật nền không ghi đè ô đang sửa. Yêu cầu bỏ nút Hủy thay đổi đã có trong backlog; bảo vệ bản nháp vẫn phải giữ. Cơ chế cũ của nút khôi phục cả Stage/Diagram từ bản lưu, không tăng phiên bản; không coi đó là yêu cầu phải giữ nút.

<a id="pool"></a>
## 5. Pool và Diagram — gán quan hệ

Pool = người trong Stage đã cập nhật − người đã gán trên Diagram đang xem. Khi kéo thả, Pool phản ánh bản nháp Diagram; tải lại dùng bản đã lưu. Pool không có bảng dữ liệu hoặc nút lưu riêng.

Kéo người vào vị trí để gán; gỡ thẻ trả người về Pool nhưng không xóa Stage. Một người không xuất hiện ở nhiều vị trí xung đột. Xóa ở Stage chỉ ảnh hưởng sơ đồ khi Cập nhật thành công.

Hai bên có 30 vị trí cố định: p1..p15 Bên A, p16..p30 Bên B. Giữ ghế trống; thả lên ghế có người thì hoán đổi, không dồn danh sách. Thừa kế biểu diễn cha/mẹ, vợ/chồng, con và nhánh thế vị. Dấu Chủ/Nhận chọn theo vị trí tài sản 1..3; đổi thứ tự/xóa tài sản phải cảnh báo đổi nghĩa.

Diagram có nháp riêng và nút Lưu sơ đồ. Xem cách tính chỉ đọc kết quả Python, không lưu và không tính lại bằng JavaScript. Quan hệ sai/vòng lặp/người ngoài Stage bị chặn; cấu trúc hợp lệ nhưng thiếu dữ liệu vẫn cho lưu, hiện rõ phần còn thiếu. Lỗi không xóa sơ đồ cũ. Xóa nút giữa có nguy cơ ảnh hưởng nhánh phải thông báo; cách xử lý nhánh cụ thể còn cần chốt.

<a id="word"></a>
## 6. Xuất Word và quản lý mẫu

Chọn thư mục mẫu, các văn bản và thư mục đích; mỗi văn bản tạo một DOCX riêng. Không chọn lại Người/Tài sản ở màn xuất. Dữ liệu Người/Tài sản lấy Stage đã lưu; vai trò/quan hệ từ Diagram, kết quả tính từ Python.

Định hướng owner: trường có dữ liệu thì điền; trường hợp lệ chưa có dữ liệu để trống, không bắt hoàn thành sơ đồ nếu mẫu không cần. Lỗi mẫu, token không hỗ trợ, nguồn hỏng hoặc nguy cơ dùng dữ liệu khác với phần đang sửa phải báo rõ.

**Khoảng lệch cần xử lý:** luồng thư mục mẫu hiện đã cho xuất thông tin tĩnh khi thiếu Chủ/Nhận trong thừa kế; catalog cũ còn chặn theo nghiệp vụ, một số kiểm tra về Stage/tài sản/slot đại diện còn tồn tại. Định hướng mới không chứng minh các kiểm tra này đã được bỏ. Chi tiết các giới hạn hiện hành được ghi trong file mẫu Word để triển khai đúng phạm vi.

Ô Nơi niêm yết phải lưu trước khi xuất nếu đang khác bản đã lưu; không hiển thị chữ mới rồi xuất chữ cũ. Một file lỗi không làm mất file khác; báo Đã lưu/Lỗi/Bỏ qua theo từng file. Không ghi đè file có sẵn, tên trùng thêm số. Hủy giữ file đã tạo, dọn file đang ghi dở khi có thể.

Nhập DOCX có thể xuất theo bản gốc: người dùng chọn đúng từng vị trí cần thay, gắn với dòng và trường đã lưu, xác nhận rồi xuất. Không thay mọi chuỗi giống nhau; không sửa file nguồn. Tab Word tự tạo/quản lý mẫu lâu dài còn là hướng chưa đặc tả.

<a id="address"></a>
## 7. Tra địa chỉ ngay khi nhập

Tra địa chỉ Người/Tài sản hoặc chính ô Nơi niêm yết; nơi cấp khai tử dùng địa chỉ của chính người chết. Dùng chữ đang nhập, không cần ngày giấy. Tra kho cục bộ, không gửi địa chỉ khách hàng lên website.

Máy chỉ trả kết quả để Copy; không tự sửa, nối “nay là” hoặc lưu Stage. Hơn 10 kết quả thì hỏi mở danh sách đầy đủ. Cửa sổ đầy đủ cho sửa câu tìm, bấm Tra và Copy từng dòng; đóng về đúng ô/con trỏ/vùng chọn/cuộn, không mất nháp. Đổi hồ sơ/ô/chuỗi tìm thì bỏ phản hồi cũ. Copy lỗi phải báo lỗi.

<a id="layout"></a>
## 8. Bố cục và thao tác

Tài sản bên trái, Người bên phải; phía dưới là Pool và Diagram. Tài sản dùng bảng cột, Người dùng bảng dòng; danh sách dài cuộn trang. Dialog Loại đất sửa cụm, Áp dụng chỉ về nháp, Cập nhật mới lưu. Có đường bàn phím thay kéo thả; lỗi đặt ngay ô/thẻ liên quan.

Mốc bố cục đã duyệt: Stage 35:65 (38:62 ở màn ≥1920), Pool khoảng 176 px, node có người 144 px, node trống 88×24. Màn ≤900 px xếp các vùng dọc; không thu chữ/node đến khó đọc. Canvas pan/zoom; Mở rộng là lớp phủ trong ứng dụng. Dấu chưa lưu của Stage và Diagram tách riêng.

Các yêu cầu mới về tăng kích thước Pool/Diagram/ô thả còn trong backlog, chưa tự áp tỷ lệ. Mốc ảnh cũ bỏ ô Nơi cấp nhưng yêu cầu mới cần thể hiện đúng nghĩa nơi cấp giấy tờ/khai tử: phải xử lý trong task giao diện, không âm thầm coi ảnh cũ là quyết định mới.

## 9. Tiêu chí kiểm và phần chưa chốt

- Lưu/mở lại giữ đúng Người/Tài sản/quan hệ; lỗi hoặc xung đột không mất nháp, không lưu nửa chừng.
- Gỡ thẻ không xóa người; xóa Stage dọn tham chiếu đúng; reorder giữ ID và báo đổi nghĩa vị trí.
- Nhập nhiều nguồn giữ phần đã sửa, lỗi từng nguồn rõ ràng; dữ liệu mơ hồ không tự được xác nhận.
- Xuất dùng đúng bản đã lưu, không sửa nguồn hoặc ghi đè đầu ra; kiểm văn bản có trường trống và văn bản chỉ cần Stage khi triển khai định hướng mới.
- Chưa chốt: tìm/lọc/nhãn Danh sách hồ sơ; đổi loại hồ sơ đã lưu; chi tiết xử lý nhánh khi xóa nút giữa; tab Word tạo mẫu; phạm vi thay các điều kiện chặn hiện hành. Quy tắc tính thừa kế Draft không tự được duyệt.

## 10. Tra cứu chuyên sâu

[Quy tắc sơ đồ](diagram-rules.md), [Word và nguồn DOCX](word-templates.md), [bóc tách dùng chung](../shared/extraction-rules.md), [tra địa chỉ](../shared/administrative-lookup.md#lookup). Các file này bổ sung chi tiết; luồng thường dùng đã được mô tả đầy đủ ở trên.

Hai bên không chạy engine chia di sản; evaluate trả unsupported, còn xuất Word có đường hỗ trợ riêng. Không thêm nghiệp vụ mới vào web cũ; nếu cần tương thích thì gọi dịch vụ chung.

Code bắt đầu tại `shell/src/renderer/notary/` và `notary_v2/routers/cases.py`; contract giao tiếp tại `contracts/notary-case-drafting.md`. Spec quyết định hành vi, code/test chứng minh hiện trạng, không tự đổi quy tắc theo code.

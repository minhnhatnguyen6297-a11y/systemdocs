# Dàn ý bộ trích xuất từ mẫu Word — bản để duyệt

**Phạm vi:** chi tiết hóa yêu cầu và lọc quy tắc từ mẫu thật. Chưa phải spec hoặc kế hoạch giao agent sửa code. Brainstorming hỏi–đáp đang tạm dừng. Các quy tắc dự kiến cần phân biệt với quyết định Owner đã chốt.

## Dàn ý hoàn thiện từ yêu cầu ban đầu

| Mã | Hạng mục cần triển khai | Nội dung cần làm rõ | Sản phẩm cần có |
|---|---|---|---|
| A01 | **Đọc đúng tài liệu và giữ vị trí nguồn** | Đọc đoạn và ô bảng theo thứ tự; giữ dòng/ô có nhãn và giá trị. Phân biệt xuống dòng trình bày với kết thúc dữ liệu; không đọc lặp hai cách hiển thị của cùng nội dung Word. | Văn bản nguồn có vị trí tra lại; có trạng thái lỗi đọc/không đọc được. Đây là tiền đề của regex. |
| A02 | **Nhận diện từng văn bản trong file** | Một file có thể chứa một hợp đồng, chỉ lời chứng hoặc nhiều đơn/tờ khai. Tìm phần bắt đầu/kết thúc từng văn bản bằng tiêu đề kết hợp cấu trúc mở đầu; không dựa tên file hoặc mọi câu nhắc tên hợp đồng. | Danh mục loại/cấu trúc đã thấy, mẫu chứng minh và phần chưa hỗ trợ. |
| A03 | **Nhận diện vùng dữ liệu chính theo từng loại** | Vùng các bên, người để lại di sản, người thừa kế, người có nghĩa vụ được bảo đảm, tài sản, ngân hàng. Mỗi vùng có dấu hiệu mở/kết thúc và vai trò rõ; không mặc định chỉ phần mở đầu có Người. | Bảng vùng theo loại văn bản, gồm mốc đầu/cuối thật trong mẫu. |
| A04 | **Nhận diện vùng của một Người** | Dấu hiệu bắt đầu một khối Người, các trường tiếp theo thuộc khối đó, dấu hiệu người kế tiếp và kết thúc khối. Có mẫu danh xưng, mẫu ghi tên trong ô/hàng biểu mẫu và mẫu chỉ ghi tên. | Quy tắc ranh giới từng Người và phạm vi địa chỉ dùng chung. |
| A05 | **Nhận diện vùng của một tài sản** | Tách vùng tài sản chung khỏi khối mô tả mỗi thửa; phân biệt thửa giao dịch với thửa gốc/thửa cũ được dẫn chiếu. Giấy chứng nhận có thể chung cho nhiều thửa. Nhà/công trình ghi đúng nhóm thông tin đã liệt kê, không trộn diện tích vào đất. | Quy tắc mỗi thửa một tài sản, đầu/cuối từng khối và phạm vi thông tin dùng chung. |
| A06 | **Nhận diện từng bộ giấy tờ và ngân hàng** | Một Người có nhiều bộ số/ngày/nơi cấp; khai tử tách khỏi căn cước. Một GCN giữ bộ thông tin riêng; các căn cứ ủy quyền ngân hàng có thể nhiều giấy. Tên ngân hàng nguyên cụm. | Ranh giới mỗi bộ giấy và cách giữ các trường cùng bộ; tránh gán giấy của tổ chức sang cá nhân. |
| A07 | **Nhận diện và lấy từng trường** | Mỗi trường có nhãn/biến thể, vùng được áp dụng, vị trí giá trị (sau nhãn/cùng ô/ô kế), dấu hiệu dừng và ví dụ đúng. Nhãn giống nhau như “Ngày cấp” hoặc “Địa chỉ” phải được hiểu theo vùng. | Bảng dấu hiệu đã lọc theo bằng chứng mẫu, liên hệ với bảng 56 mục trước. |
| A08 | **Thành phần dùng chung và quy tắc riêng từng cấu trúc** | Dùng chung cách nhận Ông/Bà, ngày, bộ giấy…; từng cấu trúc chọn đúng vùng và cách gom. Ưu tiên dấu hiệu cụ thể trước dấu hiệu rộng; giải quyết rule chồng nhau bằng ví dụ kiểm chứng. | Danh mục thành phần có thể dùng chung, phần riêng cho đoạn/bảng/biểu mẫu; tránh nhân bản 30 bộ regex. |
| A09 | **Giữ dữ liệu nguồn khi thiếu hoặc mơ hồ** | Record đã nhận diện vẫn trả dù thiếu. Giữ nhãn/giá trị nguyên văn để tra lại; không tự điền thông tin từ chữ ký, lời chứng lặp hoặc văn bản khác. Giữ rõ phần nguồn không ghi và phần chưa trích được. | Kết quả có bản ghi, dữ liệu lấy được, nguồn và ghi nhận thiếu/mơ hồ; các điểm chưa được Owner chốt được đánh dấu. |
| A10 | **Lớp đánh giá cuối** | Chỉ báo kết quả của lượt trích và tình trạng loại văn bản chưa hỗ trợ khi có căn cứ. Owner đã giải thích “sai format” là loại văn bản chưa hỗ trợ, không phải định dạng giá trị trường. Không chạy lại, tự học hoặc tự đổi rule. Số ô điền được chưa đủ chứng minh đúng/loại chưa hỗ trợ. | Kết quả đánh giá có căn cứ; thuật toán và ngưỡng chưa chốt trong bản này. |
| A11 | **Bộ mẫu và đáp án kiểm chứng** | Với từng mẫu: loại/vùng mong đợi, số bản ghi, từng giá trị có trong nguồn, ô nguồn không ghi, ví dụ không được nhận. Cần kiểm cả đủ/sai/thiếu/lặp/gán nhầm. | Đáp án được duyệt rồi mới dùng chấm; đọc thành công và số test xanh không thay đáp án. |
| A12 | **Đưa từng bản ghi vào Stage và phát triển rule** | Kết quả gốc chỉ đọc; nhập từng dòng theo lựa chọn, sửa ở Stage. Bản sửa không ghi đè kết quả gốc. Rule mới đi qua log thất bại → phát triển/kiểm thử → phát hành. | Giữ giấy tờ/loại đất đi cùng bản ghi được chọn. Chỗ lưu ngân hàng và các UX chưa chốt vẫn để mở. |
| A13 | **Đối chiếu trường trích với trường hệ thống** | Với từng trường đã trích: trường đích là gì, có kiểu dữ liệu tương ứng chưa, cách giữ nhãn gốc và giá trị chưa đủ mức chi tiết. Xác định quan hệ Người–giấy, thửa–GCN chung, thửa–loại đất; không đoán tên khóa database từ bảng dấu hiệu. | Bảng ánh xạ được duyệt trước khi triển khai, đặc biệt diện tích tổng, nhiều giấy tờ và ngân hàng. Phần chưa có chỗ lưu được ghi rõ. |

## Nội dung một quy tắc đầy đủ

| Thành phần | Ví dụ dễ hiểu |
|---|---|
| Mã và công dụng | “Lấy tên một Người”, “Tìm khối của một thửa đất”. |
| Phạm vi áp dụng | Vùng các bên trong chuyển nhượng; vùng người vay trong thế chấp; ô thông tin người nộp đơn. |
| Dấu hiệu bắt đầu | `Ông:`, `Họ và tên:`, `Thửa đất số:`… |
| Dấu hiệu kết thúc | Người/thửa kế tiếp; mốc đóng vùng; nhãn trường kế tiếp đúng ngữ cảnh. |
| Cách lấy giá trị | Bỏ toàn bộ danh xưng/nhãn; lấy chữ/số đến đúng ranh giới, kể cả có xuống dòng trong giá trị. |
| Cách giữ quan hệ | Ngày/nơi cấp thuộc số giấy nào; câu “cả hai cùng” thuộc hai người trong nhóm nào; GCN chung thuộc những thửa nào. |
| Biến thể và ưu tiên | Nhận đầy đủ `Ông/bà:` trước trường hợp rộng `Ông`; dấu hai chấm/khoảng trắng có thể dùng thành phần chung. |
| Ví dụ đúng và ví dụ loại | `Địa chỉ` trong khối đất không ghi vào Người; số công chứng không ghi vào số GCN. |
| Bằng chứng | Mã file mẫu, vị trí đoạn/ô, chữ nguồn; trạng thái đã thấy/chưa thấy/chờ chốt. |

**Mốc kết thúc không đồng nghĩa trường bắt buộc:** văn bản không có chữ ký/lời chứng hoặc record thiếu trường vẫn có thể kết thúc tại ranh giới vùng đã xác định/cuối văn bản. Dấu chấm trong `P.`/`TP.` và xuống dòng trong địa chỉ không được dùng làm mốc dừng chung cho mọi trường.

## Các giới hạn nghiệp vụ đã giữ

- Mỗi file xử lý riêng; các văn bản bên trong file có vùng riêng, không điền chéo. File lời chứng độc lập có thể có vùng Người chính ngay trong lời chứng.
- Bỏ người làm chứng/công chứng viên; Người ủy quyền và người ký thay đều thuộc phạm vi đã chốt. Tên dẫn chiếu và khối lặp chưa có quyết định tổng quát, không tự giải quyết bằng gộp theo tên/số giấy.
- Một Người nhiều bản ghi giấy tờ; căn cước cùng số khác ngày/cơ quan cấp là bộ giấy khác. Liên kết CMND 9 số/căn cước 12 số chỉ khi nguồn thể hiện rõ cùng Người; giữ giấy mới làm giấy chính.
- Mỗi thửa một tài sản; serial tùy chữ nguồn, không bắt buộc và có thể trùng. Diện tích tổng độc lập với diện tích từng loại đất. Năm trường đất bắt buộc đã chốt là yêu cầu hoàn thiện ở Stage, không được dùng loại bỏ tài sản chưa đủ khi trích.
- Ngân hàng có quy tắc riêng; tên giữ nguyên cụm trong JSON. Ghi nhận nhóm thông tin nhà đã liệt kê; xe/tàu chưa hỗ trợ.
- Chưa nhận ra loại thì trả tốt nhất engine lấy được từ dữ liệu chính; chưa có chiến lược mới được duyệt để tự suy từ vùng ký/xác nhận hoặc chạy lại sau đánh giá.

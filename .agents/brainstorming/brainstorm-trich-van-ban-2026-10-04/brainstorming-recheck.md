# Rà lại brainstorming trích xuất — 05/10/2026

**Ghi chép lịch sử trước khi Owner tạm dừng brainstorming hỏi–đáp. Đây không phải spec, plan hoặc kết luận nghiệm thu.** Phạm vi là trích Người/tài sản/ngân hàng từ từng file Word; không thay báo cáo review code ban đầu về xuất Word, địa chỉ và danh bạ. Trạng thái tiếp tục và bộ quy tắc từ mẫu tại [bàn giao 05/10](../../handoff/notary-20261005/README.md).

Cách dùng BMad: **Affinity Clustering — gom các quyết định cùng chủ đề**, rồi kiểm tra chúng có khớp nhau. Nguồn: [lịch sử trao đổi](.memlog.md), [20 mẫu và đáp án dự kiến](sample-answers/answers-draft.md), [khảo sát kho mẫu](corpus-survey/survey.md). Quyết định của Owner, nhận xét của agent và điểm chưa chốt được phân biệt dưới đây.

## Những quyết định đã rõ

| Nhóm | Quyết định của Owner | Ý nghĩa khi đọc mẫu |
|---|---|---|
| Đầu vào | Coi từng file riêng lẻ. Nhận diện cấu trúc, chia vùng, dùng chung thành phần quy tắc; có mẫu và đáp án cụ thể. | Không lấy dữ liệu file khác để hoàn thiện file đang đọc. Khoảng 10 nhóm cấu trúc là nhận định ban đầu, chưa phải con số bắt buộc. |
| Vùng dữ liệu | Trích trực tiếp từ vùng chính của từng loại; không dùng phần ký/xác nhận để tìm bù hoặc xác nhận chéo. Lời chứng đứng riêng vẫn được trích trực tiếp. | Vùng chính có thể nằm trong bảng, phần người thừa kế, điều khoản người vay hoặc các bên trong lời chứng độc lập; không giới hạn ở mở đầu. |
| Người | Bỏ người làm chứng và công chứng viên; trích cả người ủy quyền và người ký thay. Một record đã nhận diện là Người dù thiếu vẫn trả. | Việc thiếu ngày sinh/giấy tờ không tự loại một dòng. Người dùng giữ, xóa hoặc bổ sung ở Stage. |
| Giấy tờ | Một Người có nhiều bản ghi giấy tờ. Cùng số nhưng khác ngày/cơ quan cấp lưu riêng; giấy chính giữ giấy mới. Chỉ liên kết CMND 9 số với căn cước 12 số khi nguồn ghi rõ cùng người. | S20: một Người có hai bản căn cước; không tạo hai Người. Không nối phiên bản giấy chỉ vì trùng số. |
| Đất | Mỗi thửa một tài sản, cùng sổ có thể trùng serial. Năm trường bắt buộc: địa chỉ, số thửa, số tờ, diện tích tổng, loại đất. Serial không bắt buộc, không áp một định dạng chuẩn. | S17 có hai tài sản cùng serial. Diện tích tổng khác diện tích từng loại đất. Trích xuất thiếu vẫn phải trả phần có được. |
| Nhà và tài sản khác | Ghi nhận danh mục nhà/đất đã liệt kê; dừng bàn thêm nhà ở. Xe/tàu chưa hỗ trợ hiện tại. | Không tự biến toàn bộ danh mục nhà ở thành trường bắt buộc hoặc mở thêm thiết kế căn hộ. |
| Ngân hàng | Có quy tắc trích riêng. **Tên giữ nguyên cả cụm trong một giá trị JSON**, gồm chi nhánh/PGD khi có trong nguồn, không phân tách tên. | Giữ nguyên tên ở S18–S20; tránh đưa mã/địa chỉ/ngày giấy ngân hàng vào thông tin cá nhân đại diện. |
| Kết quả và Stage | Cửa sổ trích xuất chỉ đọc; nhập từng dòng theo lựa chọn, sửa ở Stage. | Không sửa kết quả gốc theo những chỉnh sửa sau đó ở Stage. |
| Đánh giá cuối | Trả kết quả tốt nhất kể cả chưa nhận ra loại. Lớp cuối chỉ báo kết quả; không chạy lại, tự học hoặc đổi quy tắc. Quy tắc mới qua quá trình phát triển sản phẩm. | “Sai format” trong trao đổi nghĩa là loại văn bản chưa hỗ trợ, không phải ô ngày/số sai định dạng. |

## Những cách hiểu cần sửa trong ghi chép của agent

1. **Giấy tờ và Người:** “không cần liên kết phiên bản” không có nghĩa giấy mất quan hệ với Người sở hữu. Owner đã chốt nhiều bản ghi giấy tờ dưới cùng một Người. Ghi chép trước về không mở rộng popup CMND cũ đã vượt quyết định; giao diện phiên bản căn cước chưa được chốt.
2. **Lời chứng:** quy tắc bỏ vùng xác nhận để tìm bù không loại file lời chứng độc lập. Khi file chỉ có lời chứng, vùng các bên của chính file đó được trích trực tiếp. S13 thực tế là lời chứng ủy quyền; không gán mọi lời chứng thành thế chấp.
3. **Ngân hàng:** tên nguyên cụm đã chốt; nhóm Ngân hàng riêng trong Stage vẫn là đề xuất. Không suy quyết định lưu/hiển thị từ quyết định giữ tên.
4. **Thiếu dữ liệu và đánh giá:** trả một dòng thiếu là hành vi đã chốt. Vì vậy số ô trống không đủ để kết luận văn bản chưa hỗ trợ. S18 có đại diện thiếu ngày sinh/địa chỉ; S08/S15/S20 có đất thiếu nhiều trường ngay trong nguồn. Cần phân biệt điều này khi bàn cách đánh giá; thuật toán chưa chốt.
5. **Chưa nhận ra loại và cấm tìm bù:** chưa thấy hai yêu cầu mâu thuẫn trực tiếp. Nhận xét của agent: có thể trả các khối dữ liệu chính nhận diện được mà không sang vùng ký/xác nhận hoặc chạy thêm lượt. Đây là khả năng để trao đổi, chưa phải chiến lược nhận diện đã được Owner duyệt.
6. **Bằng chứng:** 473 Word đọc được chỉ chứng minh đường đọc khảo sát đã chạy; 20 đáp án đọc tay còn chờ kiểm tra nghiệp vụ. Không gọi đó là độ chính xác engine hay bộ đáp án đã duyệt. Nhóm từ khóa trong khảo sát có chồng lấp, chưa phải nhóm cấu trúc cuối cùng.

## Các điểm nghiệp vụ còn mở, có ví dụ thật

| Điểm | Mẫu | Điều còn cần Owner quyết định |
|---|---|---|
| Tên trong vùng chính nhưng chỉ là dẫn chiếu | S04/S06 có đồng sử dụng đất chỉ ghi tên; S05/S17 có thân nhân/cán bộ cơ quan | Khi nào các tên này thuộc một dòng Người cần trả? Quyết định “record thiếu vẫn trả” chưa xác định mọi tên nhắc đến là một record. Người làm chứng/công chứng viên đã loại; không hỏi lại. |
| Record lặp và file ghép | S05/S09 lặp khối Người; S12 có 5 văn bản, S17 có 3 | Cách trình bày các dòng độc lập và xử lý khối lặp trong vùng chính. Không dùng đối chiếu chéo để điền thiếu. |
| Nhiều giá trị khác nghĩa cho một ô Stage | S09 thường trú/tạm trú/hiện tại; S14/S16 tờ cũ–mới; S05/S06 loại đất cũ–mới | Chọn giá trị nào hoặc giữ chúng như thế nào khi đưa vào Stage? Đáp án hiện giữ chữ và nhãn nguồn, không chọn ngầm. |
| Ngân hàng sau trích xuất | S18–S20 đã có tên nguyên cụm và thông tin riêng | Đưa vào Stage/chỗ lưu nào, hay giữ ở kết quả JSON? Việc giữ tên nguyên cụm không giải quyết điểm này. |

Những việc như cú pháp khóa JSON, tổ chức quy tắc, ghi vị trí nguồn và hỗ trợ định dạng DOC/DOCX/DOCM là phần thiết kế sau này; không coi khả năng đọc kho mẫu là quyết định sản phẩm đã hỗ trợ tất cả định dạng. Không mở thêm câu hỏi nghiệp vụ chỉ để chọn tên file hoặc cách tổ chức code.

## Căn cứ kiểm chứng còn thiếu

- **Số dòng mong đợi đã duyệt:** các mẫu có tên dẫn chiếu, record lặp hoặc nhiều văn bản chưa có đáp án cuối; chưa thể dùng chúng để chấm đủ/thiếu Người.
- **Trường nguồn có ghi và trường nguồn không ghi:** cần phân biệt để không phạt engine vì văn bản thiếu và không thưởng cho ô điền nhầm. Đây là nhận xét của agent, chưa chốt công thức chấm hay ngưỡng phần trăm.
- **Đối chiếu kết quả engine với đáp án:** chưa làm trong lượt brainstorming này; không có kết luận engine mới thành công. Các lỗi sẵn trong nguồn như tên Trường/Kính và #REF! vẫn phải được ghi đúng nguồn, không sửa bằng file khác.

**Kết quả lượt rà:** đã cập nhật cách giữ tên ngân hàng, sửa diễn giải quá mức về popup giấy tờ và cập nhật trạng thái khảo sát trong ghi chép. Những điểm mở vẫn để mở. Chưa kết thúc brainstorming hoặc chuyển sang spec/plan/code.

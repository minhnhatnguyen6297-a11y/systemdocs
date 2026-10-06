# Bộ trích xuất Word: dàn ý và quy tắc từ mẫu — chờ duyệt

Ngày 05/10/2026. Đã hoàn thiện dàn ý thành **13 hạng mục**, đọc lại **20 file mẫu S01–S20** bằng ba nhóm Luna và tổng hợp bằng parent. Kết quả gồm quy tắc nhận vùng, ranh giới từng bản ghi và bảng 56 nhóm trường được lọc theo bằng chứng mẫu.

**Chưa sửa engine, spec hoặc plan triển khai.** Các file ở đây là ghi chú để người dùng duyệt. Cách gom mới là đề xuất trừ các quyết định đã chốt trong trao đổi; đọc được mẫu không chứng minh engine trích đúng.

Bàn giao để tiếp tục sau merge: [task, plan, spec và các tham chiếu](../../handoff/notary-20261005/README.md). Task đang hoạt động cho bước duyệt là TASK-5; TASK-11 trích xuất cũ đã được lưu trữ và không có hiệu lực triển khai.

## Thứ tự đọc

| Tài liệu | Nội dung cần duyệt |
|---|---|
| [00 — Dàn ý 13 hạng mục](00-outline.md) | Hoàn thiện yêu cầu ban đầu: từ đọc tài liệu đến đưa từng dòng vào Stage và ánh xạ trường hệ thống |
| [01 — Văn bản, vùng và ranh giới bản ghi](01-boundaries.md) | 16 cấu trúc đã thấy; 3 quy tắc file ghép/lời chứng; 17 quy tắc Người/thửa/giấy/ngân hàng; 8 thành phần dùng chung |
| [02 — Dấu hiệu 56 nhóm trường](02-fields.md) | Từ/nhãn đã thấy, cách lấy giá trị, điểm dừng và mã mẫu chứng minh; phần chưa có mẫu ghi riêng |
| [03 — Mở 20 file mẫu](03-samples.md) | Liên kết trực tiếp đến từng file Word gốc để đối chiếu khi duyệt |

Bằng chứng đọc mẫu: [Người](people-evidence.md), [tài sản trong nhóm mẫu Người](people-assets-evidence.md), [ngân hàng/thế chấp](bank-evidence.md), [biểu mẫu](forms-evidence.md).

Tra file gốc và mã băm tại [manifest 20 mẫu](../../brainstorming/brainstorm-trich-van-ban-2026-10-04/sample-answers/selected-samples.json). [Đáp án đọc tay trước đó](../../brainstorming/brainstorm-trich-van-ban-2026-10-04/sample-answers/answers-draft.md) còn là bản nháp: các trường hợp tên dẫn chiếu, khối lặp, cán bộ và file ghép chưa dùng làm đáp án chấm tổng dòng.

## Dàn ý được bổ sung như thế nào

Giữ hướng người dùng đã nêu: nhận cấu trúc trước, chia vùng, dùng dấu hiệu từng trường và ghép các thành phần dùng chung. Bổ sung những phần mẫu cho thấy cần có:

- Phân biệt **mở một trường**, **mở một Người/thửa**, **mở một vùng** và **mở một văn bản mới**. Bốn việc này không dùng chung một dấu kết thúc.
- Một Người có nhiều giấy; một GCN có thể chung nhiều thửa; địa chỉ chung có phạm vi cặp người. Cần giữ những quan hệ này khi gom các trường.
- Nhãn và giá trị có thể ở đoạn/ô khác nhau. Cấu trúc bảng cần được giữ, kể cả ô trống, ô gộp và nhiều người trong một bảng.
- Phân biệt thửa giao dịch với thửa gốc/cũ, tổng diện tích với diện tích loại đất/nhà và ngày cấp giấy với ngày hợp đồng/quyết định.
- Có đáp án theo **từng vùng/từng trường** và ví dụ không được nhận. Đếm ô điền được chỉ báo mức đầy đủ, chưa chứng minh chính xác.
- Đối chiếu với các trường hệ thống trước triển khai; không biến tên trao đổi trong bảng này thành khóa database tự đặt.

## Các trường hợp thực tế phải có trong bộ kiểm tra

| Mẫu | Cấu trúc đọc thấy | Điều phải kiểm khi triển khai | Tình trạng số bản ghi |
|---|---|---|---|
| S01 | Chuyển nhượng | Hai khối Người; một thửa đủ dữ liệu; lời chứng lặp không là nguồn tìm bù | Đáp án nháp 2 Người/1 thửa |
| S02 | Tặng cho phần đất tách | Địa chỉ chung cho từng cặp; thửa giao dịch khác thửa nguồn/cũ; ngày tách khác ngày GCN | 4 Người/1 thửa giao dịch |
| S03 | Giấy ủy quyền | Người nhận nằm trong một đoạn; `P.`/`TP.` không làm cắt địa chỉ; địa chỉ kinh doanh không tự tạo đất | 2 Người/0 thửa |
| S04 | Hợp đồng ủy quyền | Hai khối nhân thân; tên đồng sử dụng chỉ nêu trong đoạn đất | Hai khối rõ/1 thửa; tổng dòng tên dẫn chiếu chờ duyệt |
| S05 | Phân chia di sản | Người chết, bố mẹ, vợ con ở nhiều tiểu vùng; khai tử khác căn cước; nguồn có tên không nhất quán | Chưa chấm tổng dòng khi còn khối lặp/tên dẫn chiếu |
| S06 | Từ chối di sản | Không có lời chứng vẫn đọc được; khai tử; loại/địa chỉ cũ–mới; ngày QĐ khác mẫu S05 phải giữ theo chính nguồn | Hai khối rõ/1 thửa; tên đồng sở hữu chờ duyệt |
| S07 | Di chúc `.doc` | Trang bìa trước nội dung; bảng đất; người hưởng riêng; loại người làm chứng/CCV | 2 Người/1 thửa |
| S08 | Cam kết tài sản riêng | Một lô được chỉ định; tên giấy đấu giá nói 22 thửa; nguồn thiếu nhiều thuộc tính | 2 Người/1 tài sản thiếu |
| S09 | Thế chấp dạng đoạn | Đại diện ngân hàng chỉ có tên/chức vụ; người vay ở điều khoản khác; nhiều loại địa chỉ; ba mô tả công trình khác diện tích đất | Có khối Người lặp trong vùng chính; tổng dòng chờ duyệt |
| S10 | Đơn Mẫu 18 | Đính chính địa chỉ; nhãn tên không đòi Ông/Bà; checklist giấy không đủ tạo tài sản | 1 Người/0 thửa |
| S11 | Phiếu đăng ký dạng bảng | Các bên/tài sản nằm trong hàng/ô; mục giấy kèm khác mô tả GCN | 1 khối tài sản; cách nhóm Người lặp vai trò chờ duyệt |
| S12 | Năm đơn/tờ khai trong file | Tách năm văn bản; nhãn số giấy ở p51, giá trị p52; tờ khai thu nhập có diện tích theo loại nhưng không ghi tổng riêng; `#REF!` là lỗi nguồn | Theo từng văn bản; chưa chốt tổng dòng nhập |
| S13 | Lời chứng ủy quyền độc lập | Lấy hai bên từ chính lời chứng; filename không quyết định tên/loại; không có ngân hàng trong mẫu này | 2 Người/0 thửa |
| S14 | Biên bản họp gia đình | `Ông/bà` không chỉ giới tính; Người đại diện lặp; một thửa hai loại đất/thời hạn; tờ cũ–mới | Bốn khối danh sách; tên người chết/khối lặp chờ duyệt |
| S15 | Giấy ủy quyền | CMND cũ có số/ngày/nơi cấp riêng; địa chỉ chung; đất chỉ ghi địa chỉ/GCN | 3 Người/1 tài sản thiếu; một Người có giấy cũ riêng |
| S16 | Thế chấp có bảng và đoạn dài | Bên A là thế chấp, khác S09; đại diện thiếu giấy tờ tùy thân nhưng có hai căn cứ ủy quyền; hai thửa; mục `(iii)/(iv)` không tạo thửa mới | Hai khối thửa rõ; Người lặp ở nghĩa vụ chưa chấm tổng dòng |
| S17 | Ba đơn/biên bản trong file | Hai thửa trong một đoạn dùng chung GCN; dữ liệu bản đồ mới để chấm; biên bản có cán bộ | Hai thửa trong đơn; tổng dòng cả file/vai trò cán bộ chờ duyệt |
| S18 | Lời chứng thế chấp độc lập | Giấy đăng ký ngân hàng khác giấy đại diện; đại diện thiếu sinh/địa chỉ; không mô tả đất | 2 Người/0 thửa |
| S19 | Lời chứng sửa đổi thế chấp độc lập | Đại diện và hai người thế chấp; địa chỉ chung; MST ngân hàng; hai quyết định có ngày riêng | 3 Người/0 thửa |
| S20 | Hủy thế chấp `.doc` | Một Người có hai giấy cùng số khác ngày/nơi cấp; hai giấy ủy quyền ngân hàng; tài sản thiếu được dẫn trong phần chính | 3 Người/1 tài sản thiếu; hai bản giấy của cùng Người |

Các con số là đáp án đọc tay dự kiến, **không phải kết quả chạy engine**. Việc phát hiện khối lặp chưa đồng nghĩa có quy tắc tự gộp được duyệt.

## Phạm vi và bằng chứng

- Đã đọc lại 20 mẫu trong manifest. Kiểm tra SHA-256 trước/sau đọc để xác nhận nguồn không đổi; OfficeCLI cho DOCX, Word chỉ đọc/tắt macro/đóng không lưu cho hai file DOC.
- Kho đầy đủ đã được khảo sát khả năng đọc ở lượt trước; **bộ quy tắc lần này chi tiết trên 20 mẫu, chưa tuyên bố bao phủ toàn bộ 473 file Word thường hoặc đủ mọi loại văn bản**.
- Parent đối chiếu và sửa ghi chú của nhóm đọc mẫu: S12 tờ khai thứ năm mở ở p216/p218, p270 là phần bên trong; S12 p95 không có tổng diện tích; S20 đoạn đất P26 vẫn thuộc phần chính. Vị trí được kiểm bằng đường dẫn đoạn/ô thật, không đếm dòng hiển thị.
- Chưa chạy chấm engine hoặc đưa ra phần trăm thành công. Biến thể chưa có mẫu và nghiệp vụ chưa chốt được ghi rõ trong hai bảng quy tắc.
- Đính chính khi đóng gói: “sai format” ở lớp đánh giá là **loại văn bản chưa hỗ trợ**, theo lời giải thích đã ghi trong `.memlog.md`; không phải yêu cầu mới kiểm sai định dạng giá trị trường. Đã sửa A10.

## Giới hạn đã giữ từ quyết định người dùng

Kết quả trích chỉ đọc, đưa từng dòng theo lựa chọn, sửa ở Stage. Record đã nhận ra nhưng thiếu trường vẫn trả. Không tìm bù/xác nhận bằng chữ ký, lời chứng kèm hoặc file khác; lời chứng độc lập có vùng các bên chính riêng. Bỏ công chứng viên/người làm chứng.

Một Người có nhiều bản giấy; chỉ liên kết CMND 9 số ↔ căn cước 12 số khi nguồn nói rõ. Mỗi thửa một tài sản, serial tùy chữ nguồn/có thể trùng/không bắt buộc; tổng diện tích không suy từ loại đất. Ngân hàng dùng quy tắc riêng, tên nguyên cụm. Nhà chỉ giữ danh mục đã nêu; xe/tàu chưa hỗ trợ. Lớp cuối báo kết quả, không tự học hoặc tự đổi quy tắc.

Các mục chờ duyệt vẫn được giữ ở dạng ghi chú. Chỉ sau khi duyệt mới dùng chúng để sửa spec và lập plan giao agent triển khai.

---
id: decision-owner-sample-first-iteration-20261019
title: "Quy tắc test bền vững: LLM đọc mẫu trước, lặp đến đủ đúng; văn bản lạ ghi issue và tiếp tục"
date: '2026-10-19'
status: accepted
---

## Nguồn

Owner chỉ dẫn trong hội thoại 19/10/2026, nguyên văn:

> tạo issue riêng cho những loại văn bản chưa chốt cấu trúc. Nhắc lại: thông tin luôn xoay quanh 3 loại. CÁch làm việc theo thứ tự: gọi llm đọc hàng loạt file mẫu, nhận diện trước cấu trúc -> so sánh với code -> điều chỉnh code -> test lại -> nếu sai thì lặp lại. Mục tiêu: xuất đủ, đúng thông tin của hợp đồng, nếu có văn bản lạ, không tự quyết được -> tạo issue tổng hợp để tôi xem sau, không dừng vòng lặp.

Owner nhấn mạnh tiếp, nguyên văn:

> ghi lại rule test này lại, tôi không muốn nhắc lại lần sau.

Đây là **quy tắc test bắt buộc, bền vững cho các phiên sau**, không phải đề xuất tạm. Ngày ghi theo đồng hồ máy 19/10/2026. Context loại văn bản và lệnh dừng triển khai vẫn theo [quyết định cùng ngày](decision-owner-case-context-standard-data-20261019.md).

## Quyết định

1. Khi được giao bắt đầu vòng thực thi, **LLM đọc hàng loạt file mẫu thực trước → nhận diện cấu trúc → đối chiếu spec/code → điều chỉnh code có căn cứ → test lại → sai thì lặp cho tới khi xuất đủ, đúng thông tin hợp đồng**. Không bắt đầu từ fixture tự tưởng tượng hoặc đóng băng output parser thành đáp án. Nhãn/giá trị/cách nhóm đối chiếu phải có nguồn độc lập trước khi xem kết quả code.
2. Thông tin nghiệp vụ chuẩn hóa chỉ thuộc **Người, Tài sản, Hồ sơ**, dùng bộ trường canonical đã duyệt; chức năng và đầu ra dùng chính dữ liệu này. Không thêm field/DTO ghi DB riêng, entity thuế/xe tưởng tượng, hoặc nhét dữ kiện sai nghĩa vào ghi chú để né mapping. Raw/bằng chứng/vị trí nguồn vẫn được giữ riêng làm provenance kỹ thuật.
3. Loại văn bản đã biết nhưng cấu trúc/mapping chưa chốt có **issue riêng theo loại**. Đầu tiên LLM phải đọc mẫu thực, xác định vùng/nhãn/biến thể và mapping; sau đó mới so code. Thiếu enum runtime **không tự chứng minh** có lỗi regex hoặc cấu trúc chưa biết. Các issue mới là công việc nghiên cứu cấu trúc/mapping UNSELECTED, chưa phải lỗi đã xác nhận, kết luận pháp lý hoặc quyền triển khai.
4. Văn bản lạ, thông tin không tự quyết được hoặc gap mapping được thêm theo từng file/ứng viên vào **issue tổng hợp xem sau #39**. Giữ nguồn/hash/vị trí và phần thông tin chắc/chưa chắc, mapping vào ba đối tượng, tham chiếu issue đúng loại nếu có và tác động tới thông tin còn thiếu. Đây là metadata workflow, không phải schema DB nghiệp vụ mới.
5. Phần chưa giải quyết giữ **pending/chưa kiểm, không tính pass**, không bị xóa/âm thầm loại để tuyên bố cả lô đủ đúng. Tiếp tục các file/phần đã rõ, **không dừng cả vòng chờ owner trả lời văn bản lạ**. Không đoán cấu trúc, field hoặc quyết định nghiệp vụ thay owner. Quy tắc này thay mọi cách hiểu trước đó rằng một gap cục bộ phải chặn toàn bộ batch.
6. Mục tiêu đủ đúng thông tin hợp đồng không đồng nghĩa chỉ tạo được DOCX hoặc đạt phép so byte. So cấu trúc/định dạng, byte và native Word trang/pixel là các lớp kiểm riêng; tiêu chuẩn binary/pixel còn chưa chọn, không coi owner đã đồng ý nới hoặc đã đạt các lớp đó.
7. LLM có thể là agent đọc file cục bộ; không cấp thêm quyền gửi hồ sơ tới cloud/provider chưa duyệt, không yêu cầu tích hợp LLM runtime/fallback mới. Raw/bằng chứng không được đưa vào log rộng.
8. Trước khi tạo fixture hoặc chạy vòng ở phiên sau, agents đọc **`D:\testcase\README.md`**, AGENTS và [spec vòng theo mẫu thực](../specs/shared/extraction-rules.md#sample-iteration). Không yêu cầu owner nhắc lại quy tắc, không tự tiếp tục kế hoạch mười ca cũ.

## Phân tuyến issue

- #29 mua bán ô tô/xe máy vẫn **DEFERRED**, duy nhất; không tạo field hoặc ca xe.
- #30 Di chúc; #31 vay tiền; #32 ủy quyền; #33 văn bản cam kết; #34 lời chứng thế chấp; #35 đơn đăng ký thường dùng Mẫu 18; #36 nhận diện ba loại khai thuế khi đổi chủ sử dụng; #37 cử đại diện thừa kế; #38 thông báo niêm yết thừa kế. Mỗi leaf giữ phần đã biết và câu hỏi chưa chọn riêng.
- #36 là **một việc nhận diện trước** vì tên ba loại thuế chưa được cung cấp; chưa thể tách đúng tên mà không đọc mẫu. Không tự đặt ba tên, field, mức thuế hoặc loại thuế. Điều kiện là **đổi chủ sử dụng**, không giới hạn theo tên “chuyển nhượng” hay tự loại tặng cho/thừa kế.
- #32 phân biệt hợp đồng ủy quyền độc lập và văn bản phụ ủy quyền cho người của văn phòng đi làm cho khách; nguồn, vai trò, mapping riêng, không lấy một template thay cả hai.
- #39 là queue xem sau cho văn bản lạ/gap cụ thể, **hiện rỗng, chưa ghi nhận file lỗi hoặc finding thực tế**. Không đọc file để lấp queue trong lượt tài liệu.
- Không tạo issue mới cho từ chối nhận di sản chỉ vì chưa có enum runtime; quy tắc nhận diện đã tồn tại không bị biến thành câu hỏi pháp lý mới. Không mở lại #14/#19/#20/#27 hoặc dùng lại #18.

## Làm rõ “vị trí” Di chúc

Nguyên văn owner: **“Người nhận tài sản theo di chúc có vị trí khác so với các văn bản khác”**. Đây là context **cấu trúc văn bản**: agent đọc mẫu để tìm vùng/vị trí người nhận và mapping. Không có chỉ dẫn chọn ghế Diagram khác hay p16; cách suy đó là diễn giải của trợ lý, không phải quyết định owner. Chỉ xét gán downstream nếu nguồn/spec thực sự quy định; nếu chưa tự quyết được, ghi issue rồi tiếp tục các mẫu đã rõ.

## Quyền hiện tại

Lượt hiện tại **chỉ ghi tài liệu/quy tắc/issue**, chưa được giao bắt đầu đọc nội dung mẫu khách hàng, chạy batch, chỉnh code, tạo Word/corpus hoặc test/E2E. Chỉ công bố tài liệu repo sau review; không đưa file khách hàng hoặc tài liệu ngoài repo lên Git. Các bản nháp corpus trước lệnh dừng giữ nguyên, không xóa/move/sửa. Quy tắc bắt buộc được lưu ngay để dùng khi owner giao thực thi, không tự coi lời “ghi lại” là quyền bắt đầu chạy.

## Bổ sung gate hoàn thành và báo cáo ổn định — cùng ngày

Owner yêu cầu tiếp, nguyên văn:

> kiểm tra kỹ tiêu chí hoàn thành: các trường chuẩn đã được xác định rõ chưa, khi llm đọc khảo sát hàng loạt -> phải ghi lại file báo cáo dùng ổn định lần sau.

- Báo cáo ổn định là **`D:\testcase\BAO_CAO_KHAO_SAT.md`**. Agents đọc trước
  mỗi lô, cập nhật sau mỗi lô, bảo lưu kết quả có ngày/lịch sử và next resume;
  không chỉ để kết quả trong tmp, không khảo sát lại vô ích hoặc ghi đè mất cũ.
- Chuẩn trường phải được audit thật: tên/kiểu/format/độ đầy đủ ngày,
  nhóm/thứ tự, đích DB/wire, ràng buộc và nguồn canonical của Người/Tài sản/Hồ sơ.
  Defined, Draft và ambiguous/unmapped tách riêng. Danh sách key đã duyệt không
  chứng minh mọi cấu trúc/biến thể hợp đồng đã có mapping đủ; không gọi tất cả
  “đã rõ” nếu chưa có đối chiếu. Báo cáo là **audit hiện tại**, không thay contract.
- Mỗi lô ghi nguồn/ref/version/ngày, đã/chưa đọc/phương pháp, vùng/bảng/vai trò
  và vị trí các bên, mapping/coverage có nguồn, code gap/issue, proposed/applied
  fix, retest quan sát đã/chưa chạy, pending và điểm tiếp tục. Chưa đọc body
  phải ghi coverage nội dung 0; báo cáo khởi tạo/metadata không là khảo sát mẫu.
- Gap chặn phần phụ thuộc chứ không dừng file đã rõ; chưa giải quyết không
  tính pass và không bị loại im lặng để claim toàn bộ đạt. Không tự sửa schema.
- Raw/chi tiết riêng tư giữ owner-local theo quyền hiện có; repo chỉ nhận ref
  an toàn/bằng chứng cấu trúc đã che giá trị cá nhân. Không chép raw Word, CCCD
  hoặc dữ liệu khách vào Git/log rộng, không tạo logging/telemetry mới.
- AC của #30–#38 và #39 ghi cả audit trường và báo cáo ổn định. #29 vẫn hoãn,
  không tự bắt đầu xe. Quyền hiện tại vẫn docs-only; chưa đọc nội dung mẫu,
  sinh Word, sửa code hoặc chạy test/E2E.

## Đối chiếu audit trường nền — 19/10/2026

Báo cáo owner-local đã có catalog Người/Tài sản/Hồ sơ: field names, kiểu,
đích DB/wire, giới hạn v2, nhóm/thứ tự và nguồn canonical. **Định nghĩa nền có
nguồn**, không đồng nghĩa mapping mọi biến thể hoặc tuân thủ implementation
đã hoàn tất. Chưa đọc body mẫu, coverage nội dung vẫn 0.

Parent đối chiếu source tĩnh xác nhận serial Stage/DB còn ràng buộc hẹp so
với chuẩn nguyên văn/rỗng/trùng đã chốt 06/10/2026. Ghi riêng
[#40](../backlog/bug-stage-raw-gcn-serial-contract.md), chưa chạy runtime hoặc sửa;
**không hỏi owner duyệt lại chuẩn đã có**, không gộp với structure leaf hay
queue #39 đang rỗng. #7/#22 là extraction, không được coi đã sửa constraint Stage.

Ngày lập hồ sơ wire optional và DB default không tự là vi phạm nếu chưa chứng
minh yêu cầu null persistence; ngày master quy ước nội bộ/snapshot giữ `YYYY`
theo #6 là semantics đã có; UNIQUE số giấy tờ không đồng nghĩa dùng làm Case key.
Không mở bug hoặc câu hỏi owner mới chỉ từ khác biệt tầng/biểu diễn này.
Thiết kế kỹ thuật bảo toàn/migration cho #40 chưa chọn, không triển khai trong
lượt docs-only này.

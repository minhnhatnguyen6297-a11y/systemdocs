---
id: decision-upload-web-sot-without-save-tracking
title: Bỏ theo dõi kết quả Lưu; dữ liệu website là nguồn sự thật
date: '2026-10-15'
status: accepted
---

## Quyết định

Bỏ theo dõi và phục hồi kết quả Lưu của app Upload. Người dùng có thể chủ ý không Lưu biểu mẫu vì lỗi, trùng hoặc lý do nghiệp vụ; owner chấp nhận rủi ro sự cố đó. Dữ liệu đã được website ghi nhận chính thức là nguồn sự thật (SOT).

App tiếp tục điền sẵn biểu mẫu rồi dừng trước nút Lưu để người dùng tự kiểm tra và quyết định. App không suy kết quả Lưu từ POST, route/điều hướng, đóng tab, `finish_review` hay tín hiệu cục bộ; không lưu trạng thái/số đếm Lưu suy từ browser, không khóa hoặc yêu cầu giải phóng vì chưa rõ Lưu, không retry/phục hồi Lưu và không tự đưa hồ sơ chưa Lưu vào đợt sau. Không tự mở đợt kế tiếp. Phân loại hiện diện trong sổ chính thức vẫn được dùng bình thường.

Trong lượt hiện tại chỉ nhớ tiến độ chuẩn bị và quyền sở hữu tài nguyên. `Tiếp tục` do người dùng bấm, chuyển qua hồ sơ đã chọn nhưng chưa chuẩn bị; tiến độ này không phải bằng chứng Lưu hay blacklist vĩnh viễn. Quét/chọn lại thủ công dùng đối chiếu thường lệ với ảnh chụp dữ liệu chính thức đang nạp theo website và phạm vi ngày/năm. Tải/nạp Excel hiện có được giữ; không thêm fetch tự động hoặc đối chiếu phục hồi bắt buộc.

Giữ các bước/nguồn lực hiện có không thuộc theo dõi kết quả Lưu: quét, audit đầu vào, đăng nhập, tiến độ/lỗi job thông thường, kết thúc chờ kiểm tra, đóng phiên browser và điều khiển website. Không dùng những bước này làm bằng chứng Lưu.

## Lý do

Theo dõi hậu Lưu và phục hồi kết quả suy từ browser có giá trị thấp so với chi phí duy trì trạng thái, cảnh báo và khóa dựa trên kết quả chưa chắc chắn. Người dùng cần quyền chủ ý không Lưu; trạng thái duy nhất có thẩm quyền về việc đã ghi nhận là dữ liệu chính thức trên website. Quyết định này không loại bỏ phân loại hiện diện từ audit chính thức hay các khóa thông thường cho đăng nhập, job, nguồn, revision và tài nguyên.

## Ranh giới

Đây là quyết định hành vi/spec, không phải xác nhận code đã đồng bộ hoặc phê duyệt implementation hàng loạt. Contract `upload-workflow` vẫn Draft. Code hiện còn theo dõi tín hiệu và trạng thái đối chiếu; cần xử lý cutover riêng. Quyết định này thay thế hướng theo dõi/phục hồi kết quả Lưu trước đây, nhưng không sửa hay xóa lịch sử các quyết định/ticket cũ.

## Nguồn quyết định

Owner, 15/10/2026: “Bỏ chức năng này, user chịu rủi ro về việc sự cố. SOT là dữ liệu đã được upload chính thức từ web”.

## Hệ quả theo dõi — 15/10/2026

Phạm vi cũ của #11 và nhu cầu kiểm chứng tín hiệu Save ở #26 được ghi nhận là dropped; lịch sử không bị xóa. C27/#28 là draft cho runtime cutover, chưa duyệt implementation. Câu hỏi A/B trong plan cũ #11 đã retired, không còn gate.

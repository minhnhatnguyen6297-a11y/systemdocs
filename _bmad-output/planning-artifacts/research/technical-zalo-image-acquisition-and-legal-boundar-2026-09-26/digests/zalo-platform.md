# Zalo platform, listener và OCR cloud

## Cập nhật quan trọng: Zalo Bot API chính thức

Kiểm tra 26/09/2026 từ trang của Công Ty TNHH Zalo Platforms. [Bot Platform](https://bot.zapps.me/) ghi Basic tối đa 3 bot, 50 người dùng/bot, 3.000 tin/tháng và **3 nhóm Chat (Beta)**; gói Pro hiện ghi sắp ra mắt. [Tài liệu tạo Bot](https://docs.zaloplatforms.com/docs/BOT/create_bot) hướng dẫn tạo từ OA “Zalo Bot Manager” và Bot Creator, nhận token, dùng polling hoặc webhook. Đây là **Zalo Bot API chính thức**, không đồng nhất OA GMF và không đồng nhất tài khoản cá nhân chạy zca-js.

[Webhook Bot](https://docs.zaloplatforms.com/docs/BOT/webhook) liệt kê “message.image.received”, trường ảnh “photo” (URL), caption, from, chat.id, message_id, date; chat_type “GROUP” đang beta. Webhook có header “X-Bot-Api-Secret-Token”; nhóm người gửi đặc biệt có thể chỉ tạo “message.unsupported.received”. [setWebhook](https://docs.zaloplatforms.com/docs/BOT/apis/setWebhook) yêu cầu HTTPS công khai. [getUpdates](https://docs.zaloplatforms.com/docs/BOT/apis/getUpdates) và webhook loại trừ nhau; tài liệu khuyên production dùng webhook để tránh bỏ lỡ event.

**Mâu thuẫn chưa giải:** [getMe](https://docs.zaloplatforms.com/docs/BOT/apis/getMe) có ví dụ bot BASIC với “can_join_groups: false”, trong khi bảng gói nói 3 nhóm beta. Ví dụ không chứng minh mọi bot không thể vào nhóm; bảng gói cũng không chứng minh bot thử nghiệm được mời vào nhóm cá nhân đang có. Tài liệu chính thức đã đọc không nêu bot thấy ảnh không @mention. Phải thử đúng tài khoản/nhóm, tag trên từng ảnh, ảnh không tag, reply, chat riêng. Đừng đưa lời khẳng định “Bot API nghe đủ mọi ảnh nhóm” vào spec trước phép thử.

**Khoảng trống về độ bền:** [getWebhookInfo](https://docs.zaloplatforms.com/docs/BOT/apis/getWebhookInfo) minh họa URL và thời điểm đổi cấu hình, không chỉ ra pending count/retry. [testWebhook](https://docs.zaloplatforms.com/docs/BOT/apis/testWebhook) chỉ kiểm tra trả lời 2xx, bị giới hạn số lần gọi mỗi ngày; không kiểm đếm ảnh thực. Chưa thấy tài liệu chính thức cam kết thời hạn giữ event, số lần retry, API history/backfill, chất lượng và hạn dùng photo URL.

**Phương án chính thức khác:** [Mini App openMediaPicker](https://docs.zaloplatforms.com/docs/MA/api/media/file/openMediaPicker) cho người dùng chọn nhiều ảnh và upload trực tiếp tới serverUploadUrl; compressLevel 0 mặc định không nén. Đây là người dùng nộp chủ động, không đọc ảnh trong chat. Cổng upload độc lập cũng đạt đặc tính server 24/7 và trả biên nhận số ảnh.

Ngày truy cập: 2026-09-26. Nguồn sơ cấp, chưa thử tài khoản thật.

## Kết quả đã kiểm chứng

- Zalo Terms, https://zaloapp.com/mobile/zalo/dieukhoan/ : bản được máy tìm kiếm lập chỉ mục ghi cập nhật 28/08/2026, hiệu lực 05/09/2026. Điều 4.4–4.7 liên quan đảo ngược, can thiệp trái phép, truy cập không được phép và dùng phần mềm/hệ thống bên thứ ba chưa được chấp thuận. Trang mở trực tiếp qua web reader trả rỗng; nội dung được xác nhận qua tìm kiếm chính trang nguồn. Không suy diễn mọi trình duyệt phổ thông đều bị cấm. Client Electron tùy biến và tự động hóa chưa có xác nhận được Zalo chấp thuận. Đây là rủi ro điều khoản riêng với việc có cấu thành vi phạm pháp luật hay không.
- zca-js maintainer README, https://github.com/RFS-ADRENO/zca-js : tự xác định là API không chính thức, mô phỏng trình duyệt giao tiếp với Zalo Web; cảnh báo khóa tài khoản. README nêu một web listener/tài khoản và mở Zalo trong browser làm listener dừng. Có message listener cho chat riêng/nhóm. Không có cơ sở tuyên bố nhận 100% hoặc replay toàn bộ lịch sử. MIT cho phép dùng mã thư viện, không thay thế quyền dùng dịch vụ Zalo. Pubdate không ghi; accessed 26/09/2026.
- OA GMF, https://oa.zalo.me/home/resources/news/_4601792943864106455 : bài ngày14/06/2023 còn truy cập được. Nêu không mời OA vào nhóm có sẵn; mục bảo mật hạn chế chia sẻ thông tin tương tác ra ngoài nhóm và không dùng nhóm chia sẻ/yêu cầu CMND, dữ liệu ngân hàng, thông tin bảo mật cá nhân. Đây là bằng chứng chính sách lịch sử còn công khai, chưa chứng minh toàn bộ còn áp dụng nguyên vẹn năm2026. Không lấy giá/gói2023 làm giá hiện tại. Cần Zalo xác nhận use case CCCD trước khi chọn OA.
- OA docs https://developers.zalo.me/docs/official-account/nhom-chat-gmf/quan-ly/group_conversation có tiêu đề API lấy tin nhắn nhóm nhưng reader trả0dòng. Chưa xác minh payload, quyền, webhook/replay/quota hiện tại; không dùng làm bằng chứng đảm bảo thu đủ ảnh.
- Alibaba Model Studio https://www.alibabacloud.com/help/en/model-studio/what-is-model-studio (22/09/2026) công bố API chính thức Qwen. Gọi Qwen API không cùng loại với tự mô phỏng API Zalo.
- Privacy https://www.alibabacloud.com/help/en/model-studio/privacy-notice (20/09/2026): công bố không dùng dữ liệu cho training, nhưng có lưu dữ liệu sinh từ lượt gọi model/application theo pháp luật và điều khoản. Không suy ra zero retention từ no-training.
- Regions https://www.alibabacloud.com/help/en/model-studio/regions (24/09/2026): vùng endpoint quyết định nơi lưu dữ liệu; phạm vi triển khai quyết định nơi chạy suy luận. Không coi tên model, quốc tịch nhà cung cấp hay địa chỉ endpoint là đủ chứng minh toàn bộ dữ liệu ở Việt Nam.

## Suy luận cho quyết định

1. Nút tải chính thức và watcher file giảm phụ thuộc giao thức nội bộ; tự click vẫn cần xem điều khoản, không tự trở thành integration được Zalo phê duyệt.
2. OA có thể là kênh mới, không được mặc định thay bot đang nằm trong nhóm cá nhân hiện hữu. Tính phù hợp nhận giấy tờ định danh là câu hỏi chính sách riêng.
3. Đổi OCR trong nước chỉ giải quyết nơi xử lý nếu cả lưu trữ, vận hành, nhà thầu phụ được kiểm chứng; dữ liệu chữ sau OCR vẫn có thể là dữ liệu cá nhân.
4. Một link tải tài liệu lên cổng của văn phòng là phương án thiết kế khác: Zalo chỉ chuyển link, người gửi chọn tài liệu, server của văn phòng nhận và đếm file. Không phải công cụ kéo lịch sử Zalo.

## Chưa xác minh

Quyền dùng client Electron và automation có giám sát; chính sách OA năm2026 cho CCCD/sổ đỏ; endpoint/quyền nhận ảnh OA thực tế; tỷ lệ lỗi, ảnh hết hạn, phiên đăng nhập đồng thời; hợp đồng và vùng xử lý của tài khoản OCR cụ thể. Không có tài khoản thật nào được truy cập trong nghiên cứu.

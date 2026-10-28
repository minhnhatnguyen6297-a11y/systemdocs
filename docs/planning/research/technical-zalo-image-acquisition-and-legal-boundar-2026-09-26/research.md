---
title: Lấy ảnh từ Zalo và ranh giới pháp lý
type: technical
topic: zalo-image-acquisition-and-legal-boundaries
decision: Chọn đường nhận tài liệu và điều kiện thử nghiệm
source: primary-source-web-research
status: completed-research-not-architecture-decision
preset: deep
validation: published-documents-checked-live-behavior-unverified
created: 2026-09-26
updated: 2026-09-26
---

# Lấy ảnh Zalo cho Soạn hồ sơ: kết quả nghiên cứu

**Khảo sát ngày 26/09/2026.** Đây là tài liệu hỗ trợ quyết định; chưa đổi spec, contract hoặc phần mềm đang chạy. Chưa đăng nhập Zalo thật, chưa đọc ảnh khách hàng, chưa đo 10 ảnh trong nhóm thực tế. Ký hiệu **[TL]**: tài liệu xác nhận; **[SL]**: suy luận kỹ thuật; **[CT]**: phải kiểm thử. Phần pháp lý là nhận diện rủi ro, chưa phải kết luận cho một hồ sơ cụ thể.

## Kết luận dùng để chọn hướng

1. **Thử Zalo Bot API chính thức trước.** Zalo công bố sự kiện nhận ảnh, địa chỉ ảnh, giờ gửi, mã tin, mã nhóm và webhook (Zalo báo tới máy chủ). Trang gói Basic ghi tối đa 3 nhóm ở trạng thái beta. Nhưng ví dụ API lại trả “can_join_groups: false” cho một bot Basic; tài liệu cũng không cam kết bot được thấy **mọi** ảnh không nhắc tên trong nhóm. Hai chỗ này quyết định ca “10 ảnh lúc nửa đêm”, nên chưa thể chốt nó đạt yêu cầu. [Webhook Bot](https://docs.zaloplatforms.com/docs/BOT/webhook), [gói Bot](https://bot.zapps.me/), [getMe](https://docs.zaloplatforms.com/docs/BOT/apis/getMe).
2. Nếu API chỉ báo ảnh có **@bot**, người gửi có thể tag bot trên từng ảnh hoặc gửi riêng cho bot. Đó là thay đổi thói quen gửi. Nếu bắt buộc nghe thụ động toàn bộ nhóm cá nhân hiện có, các đường còn lại đều cần dùng giao tiếp Zalo không công bố, quan sát Zalo Web hoặc tự bấm giao diện. Không nguồn nào đã kiểm tra chứng minh nhận 100%, khôi phục đầy đủ tin bỏ lỡ hay được Zalo chấp thuận. [zca-js](https://github.com/RFS-ADRENO/zca-js), [điều khoản Zalo](https://zaloapp.com/mobile/zalo/dieukhoan/).
3. **Hướng bền nhất khi người gửi hợp tác:** gửi link cổng nhận hồ sơ qua Zalo, hoặc mở Zalo Mini App để người gửi chọn 10 ảnh một lần. Máy chủ đếm và xác nhận “đã nhận 10/10”, hoạt động lúc máy công chứng tắt. Mini App có API chọn nhiều ảnh và tải trực tiếp lên máy chủ; nó không âm thầm đọc ảnh đã gửi vào chat. [openMediaPicker](https://docs.zaloplatforms.com/docs/MA/api/media/file/openMediaPicker), [chooseImage](https://docs.zaloplatforms.com/docs/MA/api/media/file/chooseImage).
4. **Zalo Web → tải ảnh → thư mục theo dõi** là đường nhập chủ động tốt cho buổi sáng. Nhúng Web trong Electron giảm việc đổi cửa sổ, nhưng khi Electron đóng thì bộ nhận đó cũng dừng. Sự kiện tải của Electron chỉ biết lượt tải đã bắt đầu, không biết nhóm vừa có ảnh. [Electron session](https://www.electronjs.org/docs/latest/api/session), [DownloadItem](https://www.electronjs.org/docs/latest/api/download-item).

## Tách ba bài toán vốn dễ bị lẫn

| Bài toán | Ví dụ 10 ảnh | Hệ quả |
|---|---|---|
| **Nguồn có báo sự kiện?** | Bot nhận 10 sự kiện hay chỉ các ảnh có @bot? | Nếu Zalo không phát một tin cho kênh đó, máy chủ không thể tự tạo lại tin ấy. |
| **Lấy được ảnh đủ nét?** | Có 10 URL nhưng chúng là ảnh gốc hay ảnh thu nhỏ? | Đếm sự kiện chưa chứng minh OCR đọc được 10 ảnh thật. |
| **Máy nhận có bền?** | Server mất mạng 5 phút; Zalo gửi lại hay không? | Webhook đang xanh không chứng minh không bỏ sót trong quá khứ. |

“Luôn sống” nghĩa là máy chủ nhận độc lập với app công chứng; ghi sự kiện xuống đĩa, lấy và kiểm tra ảnh, rồi mới OCR. Máy chủ chạy 24/7 vẫn có thể mất tin do quyền nguồn, phiên đăng nhập, hạn URL, mất mạng hoặc dịch vụ. Nếu nguồn không cho danh sách đầy đủ để so, phải hiển thị **“chưa chứng minh nhận đủ”**, không tự báo “đã đủ”. [SL]

## Bản đồ các đường lấy ảnh

“Ban đêm” giả định app và máy công chứng tắt, nhưng máy chủ riêng vẫn bật. “Chính thức” chỉ nói Zalo công bố cách tích hợp, chưa thay cho quyền xử lý giấy tờ cá nhân.

| Đường | Có thể tự nhận khi app tắt? | Điều kiện và giới hạn |
|---|---|---|
| **Zalo Bot API + webhook** | Có thể | Chính thức; nhóm beta. Phải chứng minh bot vào nhóm, thấy ảnh không tag, tải được bản đủ nét, có cách xử lý đứt mạng. |
| **OA + nhóm do OA quản lý (GMF)** | Có thể | Kênh chính thức nhưng không tự nhập nhóm cá nhân có sẵn; chính sách GMF công khai cũ hạn chế CMND. |
| **Mini App/cổng upload** | Có, sau khi người gửi chọn ảnh | Có thể đếm chính xác file đã nộp; không kéo ảnh cũ trong chat. |
| **zca-js/giao thức Web không công bố** | Có thể, nếu listener server còn sống | Tự động nhưng không chính thức; rủi ro khóa tài khoản, không có bảo đảm đủ sự kiện hoặc replay. |
| **Chrome mở liên tục + extension/DOM** | Có thể nếu tự tìm và tự tải được | Chỉ biết dữ liệu đã tải vào trang; thay đổi giao diện hoặc browser chết có thể bỏ sót. |
| **DevTools/CDP/Network/WebSocket** | Chỉ quan sát khi kết nối sống | Không phải Zalo API; URL hoặc thumbnail quan sát được chưa bằng ảnh gốc/lịch sử đầy đủ. |
| **Electron nhúng Zalo Web** | Không, nếu Electron đóng | Biết lượt tải sau khi người dùng bấm; không tự nghe qua đêm. |
| **Chrome riêng + nút tải + thư mục theo dõi** | Không | Nhập lô sáng hôm sau; thư mục chỉ thấy file đã tải. |
| **Zalo PC + tải thủ công** | Không | Có cài thư mục tải và chạy nền; hướng dẫn chính thức vẫn yêu cầu chọn/lưu ảnh. |
| **Zalo PC + tự bấm bằng RPA/UI Automation** | Có thể trên máy Windows còn chạy | Phụ thuộc màn hình, phiên desktop, hộp thoại và UI; chưa chứng minh độ đầy đủ. |
| **Điện thoại → Share sheet/app nhận** | Không tự động | Android/iOS hỗ trợ app nhận nhiều tệp; Zalo có hiện thao tác chia sẻ phù hợp hay không phải thử. |
| **Android đọc thông báo hoặc Accessibility** | Chỉ có thể quan sát phần hệ điều hành hiện ra | Thông báo có thể thiếu ảnh/ẩn nội dung; điều khiển màn hình phụ thuộc UI và mục đích cấp quyền, không phải quyền đọc kho Zalo. |
| **Clipboard/kéo thả/chụp màn hình** | Không | Mất ngữ cảnh người gửi/giờ; ảnh màn hình có thể kém nét. |
| **My Documents/Cloud/backup/cache/DB nội bộ** | Chưa có bằng chứng | Backup có loại trừ; cache có thể thiếu/được mã hóa. Không dùng làm nguồn sự kiện chính. |

Nguồn chính cho bảng: [Zalo Bot](https://docs.zaloplatforms.com/docs/BOT/webhook), [OA GMF](https://oa.zalo.me/home/resources/news/_4601792943864106455), [Mini App](https://docs.zaloplatforms.com/docs/MA/api/media/file/openMediaPicker), [zca-js](https://github.com/RFS-ADRENO/zca-js), [Electron](https://www.electronjs.org/docs/latest/api/session), [Zalo PC lưu ảnh](https://help.zalo.me/huong-dan/chuyen-muc/nhan-tin-va-goi/nhan-tin/tai-ve-may-luu-my-documents-cac-anh-video-file-quan-trong-tren-zalo/), [Zalo backup](https://help.zalo.me/huong-dan/chuyen-muc/quan-ly-tai-khoan-zalo/sao-luu-va-khoi-phuc/chi-tiet-ve-cac-du-lieu-duoc-zalo-sao-luu/). “Có thể” là [SL], không phải kết quả thử.

## Đi sâu vào những đường có triển vọng

### Bot API chính thức: phát hiện quan trọng nhưng chưa đạt điều kiện chốt

[TL] Zalo ghi loại hội thoại nhóm là “GROUP (Beta)”. Sự kiện “message.image.received” có đường dẫn ảnh, chú thích, mã tin, giờ gửi, người gửi và mã cuộc trò chuyện. Trang Basic ghi 3 nhóm, nhưng mẫu “getMe” của một bot Basic có “can_join_groups: false”. **Không được suy từ một mẫu rằng mọi bot đều không thể vào nhóm**, cũng không được suy từ bảng giá rằng bot của ta chắc chắn vào được nhóm sẵn có. [Webhook](https://docs.zaloplatforms.com/docs/BOT/webhook), [Basic](https://bot.zapps.me/), [getMe](https://docs.zaloplatforms.com/docs/BOT/apis/getMe).

[CT] Tài liệu chính thức đã xem không nói rõ bot nhận ảnh không @mention. Một số triển khai cộng đồng nói chỉ @mention/reply mới tới bot; đó là đầu mối cần thử, không phải quy tắc được Zalo xác nhận. Cần phân biệt tag ở **chính ảnh**, tag trong tin liền trước, caption, reply và gửi riêng. Chỉ một ảnh không tag bị mất đã khiến đường này không đáp ứng yêu cầu “nghe đầy đủ”.

[TL] Zalo yêu cầu webhook là địa chỉ HTTPS công khai và khuyên dùng webhook cho production thay cho polling. Polling và webhook loại trừ nhau. Tài liệu “getWebhookInfo” chỉ minh họa URL/thời điểm cấu hình; không có bằng chứng về số sự kiện đang chờ. “testWebhook” kiểm tra endpoint trả lời 2xx, bị giới hạn số lần gọi/ngày; nó **không kiểm tra 10 ảnh đã đến đủ**. Chưa tìm được cam kết về số lần gửi lại webhook, thời hạn giữ sự kiện, API đọc lịch sử hoặc hạn sử dụng URL ảnh. [getUpdates](https://docs.zaloplatforms.com/docs/BOT/apis/getUpdates), [setWebhook](https://docs.zaloplatforms.com/docs/BOT/apis/setWebhook), [getWebhookInfo](https://docs.zaloplatforms.com/docs/BOT/apis/getWebhookInfo), [testWebhook](https://docs.zaloplatforms.com/docs/BOT/apis/testWebhook).

[TL] Webhook gửi khóa xác thực trong header “X-Bot-Api-Secret-Token”. Một số tài khoản người gửi thuộc nhóm đối tượng đặc biệt khiến Zalo gửi “message.unsupported.received” thay vì nội dung; đây là một kiểu “có sự kiện nhưng không có ảnh”. Phải ghi nó thành trạng thái cần xử lý, không âm thầm bỏ qua. [Webhook](https://docs.zaloplatforms.com/docs/BOT/webhook).

### OA, Mini App và cổng nhận hồ sơ

**OA GMF khác Bot API.** Bài chính sách GMF ngày 14/06/2023 nói không mời OA vào nhóm có sẵn và không dùng nhóm OA để chia sẻ/yêu cầu CMND cùng dữ liệu bảo mật cá nhân. Bài còn công khai, song giá và điều kiện nhóm đã thay đổi ở những bản tin sau. Cần hỏi Zalo chính sách **hiện hành** cho công chứng; không tự áp chính sách OA lên Bot API hay ngược lại. [GMF 2023](https://oa.zalo.me/home/resources/news/_4601792943864106455), [cập nhật GMF](https://oa.zalo.me/home/resources/news/cap-nhat-tinh-nang-moi-thang-112024-_1276553607002998075), [gói OA từ 01/06/2026](https://oa.zalo.me/home/resources/news/162026-zalo-official-account-trien-khai-4-goi-dich-vu-moi-toi-uu-hieu-suat-theo-nhu-cau-doanh-nghiep-_109742821673880689).

[TL] Mini App “openMediaPicker” cho chọn nhiều ảnh và gửi tới “serverUploadUrl”; mức nén 0 được mô tả là không nén. Cần thử số lượng/kích thước 10 ảnh và khả năng mở từ cuộc trò chuyện đang dùng. Đây là API cho ảnh **người dùng chủ động chọn**, không phải quyền đọc ngầm các ảnh đã gửi trong chat. [openMediaPicker](https://docs.zaloplatforms.com/docs/MA/api/media/file/openMediaPicker).

### Trình duyệt, DevTools và Zalo PC

[TL] Electron “will-download” và Chrome “downloads” theo dõi lượt tải đã được khởi tạo. DOM (cấu trúc trang) chỉ chứa phần cuộc trò chuyện trang đã tải. DevTools/CDP (bộ công cụ đọc/điều khiển Chrome) quan sát mạng khi đang mở/kết nối. [SL] Có thể nghiên cứu gói WebSocket hoặc yêu cầu ảnh để đo thiếu/trùng, nhưng đó không phải API Zalo; URL có thể hết hạn, thumbnail hoặc bộ nhớ đệm không chứng minh đủ ảnh gốc, và lịch sử chưa tải không tự xuất hiện. Chrome từ bản 136 cần thư mục hồ sơ riêng khi dùng remote debugging. [Electron](https://www.electronjs.org/docs/latest/api/session), [Chrome downloads](https://developer.chrome.com/docs/extensions/reference/api/downloads), [CDP Network](https://chromedevtools.github.io/devtools-protocol/tot/Network/), [Chrome 136](https://developer.chrome.com/blog/remote-debugging-port).

[TL] Nếu nhúng Zalo Web, Electron có “WebContentsView”; “BrowserView” đã deprecated và tài liệu khuyên tránh thẻ “webview”. Trang mạng phải được cô lập khỏi quyền đọc/ghi của app. Repo khai báo “electron: ^31.0.2” (chưa kiểm tra phiên bản tiến trình đang chạy); Electron 31 đã hết hỗ trợ, nên không thiết kế dựa vào API chỉ có ở phiên bản mới. [WebContentsView](https://www.electronjs.org/docs/latest/api/web-contents-view), [BrowserView](https://www.electronjs.org/docs/latest/api/browser-view), [bảo mật Electron](https://www.electronjs.org/docs/latest/tutorial/security), [lịch hỗ trợ](https://releases.electronjs.org/schedule).

[TL] Zalo Help hướng dẫn người dùng chọn ảnh trong “Ảnh, link, file đã gửi” rồi lưu. Zalo PC có cài thư mục tải/khởi động cùng Windows; mục “Thoát” vẫn để app chạy nền. Đây là hỗ trợ cho nhập thủ công, **không phải bằng chứng tự lưu mọi ảnh**. Backup chính thức loại trừ một số dữ liệu/nhóm/tệp, không thể coi là đường nhập sự kiện đầy đủ. [Lưu ảnh](https://help.zalo.me/huong-dan/chuyen-muc/nhan-tin-va-goi/nhan-tin/tai-ve-may-luu-my-documents-cac-anh-video-file-quan-trong-tren-zalo/), [cài đặt PC](https://help.zalo.me/huong-dan/chuyen-muc/zalo-cong-viec/ca-nhan-hoa-zalo-tren-may-tinh/), [backup](https://help.zalo.me/huong-dan/chuyen-muc/quan-ly-tai-khoan-zalo/sao-luu-va-khoi-phuc/chi-tiet-ve-cac-du-lieu-duoc-zalo-sao-luu/).

**Điện thoại:** Android có API để app khác nhận nhiều file khi người dùng chia sẻ, và API nghe thông báo; nội dung thông báo do Zalo quyết định nên không thể suy ra có đủ bản ảnh. Accessibility đọc/tác động giao diện phục vụ hỗ trợ tiếp cận, không phải lối tắt cấp quyền đọc dữ liệu Zalo. Android 11+ hạn chế app đọc thư mục riêng của app khác; iOS cũng cách ly kho riêng từng app. Do đó không xem “quét thư mục Zalo”, đọc thông báo hay root/jailbreak là phương án nhập ảnh sản xuất. [Android nhận file](https://developer.android.com/develop/ui/compose/sharing/receive), [Android notification listener](https://developer.android.com/reference/android/service/notification/NotificationListenerService), [Android Accessibility](https://developer.android.com/guide/topics/ui/accessibility/views/service), [Android 11 storage](https://developer.android.com/about/versions/11/privacy/storage), [Apple sandbox](https://developer.apple.com/documentation/technologyoverviews/shared-data).

### Tencent BrowserSkill: học nguyên lý, chưa cài

[TL] BrowserSkill gồm lệnh, dịch vụ nền và tiện ích Chrome/Edge điều khiển các tab đang đăng nhập. Nó không cấp quyền Zalo mới. Đáng học: bộ nhận độc lập, phạm vi phiên điều khiển, ghi nhận thao tác, nhờ người dùng can thiệp khi cần. README ghi chế độ tác nhân chạy server nhưng browser giữ ở PC người dùng **chưa hỗ trợ upload/download file**. Không thể dùng bản hiện tại để trực tiếp chuyển ảnh từ Zalo Web trên PC về server. Quyền điều khiển tab đăng nhập cũng cần thẩm định trước khi cài. [README Tencent](https://github.com/Tencent/BrowserSkill), [kiến trúc tại commit a271764](https://github.com/Tencent/BrowserSkill/blob/a2717648e8a525b0d21d83d30f96360642b461b9/docs/architecture.md).

## Ranh giới pháp lý: bốn lớp khác nhau

| Lớp | Điều cần kiểm tra | Không được suy diễn |
|---|---|---|
| **Điều khoản Zalo** | Bản có hiệu lực 05/09/2026, mục 4.7 cấm đăng nhập/sử dụng dịch vụ bằng phần mềm tương thích của bên thứ ba hoặc hệ thống chưa được Zalo phát triển, cấp quyền hay chấp thuận. “zca-js” tự nhận là API không chính thức mô phỏng Zalo Web, cảnh báo khóa tài khoản. | Người tự bấm trên trình duyệt thông thường không tự động thuộc mục cấm; nhúng/click tự động cũng chưa có thư chấp thuận. Phải xin Zalo xác nhận trường hợp cụ thể. [Điều khoản](https://zaloapp.com/mobile/zalo/dieukhoan/), [zca-js](https://github.com/RFS-ADRENO/zca-js). |
| **Dữ liệu cá nhân** | Luật 91/2025/QH15 hiệu lực 01/01/2026 quy định căn cứ xử lý, mục đích, người kiểm soát và quyền chủ thể. Nếu dựa vào đồng ý, sự đồng ý phải rõ và kiểm chứng được. NĐ 356/2025/NĐ-CP xếp **hình ảnh thẻ căn cước/CCCD/CMND** vào dữ liệu nhạy cảm, yêu cầu phân quyền và biện pháp bảo vệ. | Người gửi ảnh của nhiều người trong nhóm không tự đại diện cho mọi chủ thể dữ liệu. Chữ OCR vẫn có thể là dữ liệu cá nhân. Giữ ảnh 7 ngày là quyết định sản phẩm, không phải miễn trách nhiệm. [Luật 91](https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/7/91qh.signed.pdf), [NĐ 356](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/356-nd.signed.pdf). |
| **Bí mật công chứng** | Luật Công chứng 46/2024/QH15 yêu cầu công chứng viên và tổ chức giữ bí mật nội dung công chứng, trừ khi người yêu cầu đồng ý bằng văn bản hoặc luật quy định khác. Chuyển ảnh hồ sơ tới nhà OCR ngoài cần được đánh giá riêng trong quy trình văn phòng. | Sự đồng ý của người yêu cầu đối với bí mật công chứng và căn cứ xử lý dữ liệu của mọi người có tên trên giấy là hai câu hỏi khác nhau. [Luật Công chứng](https://congbao.chinhphu.vn/van-ban/luat-so-46-2024-qh15-43574.htm). |
| **Truy cập trái phép** | Bộ luật Hình sự Điều 289 có những yếu tố cụ thể về vượt cảnh báo/biện pháp bảo vệ, xâm nhập trái phép, mục đích và hậu quả. Cần đánh giá hành vi thực tế. | Vi phạm điều khoản Zalo **không tự động** cấu thành tội phạm; có tài khoản trong nhóm cũng không cho phép vượt biện pháp bảo vệ. [Bộ luật Hình sự](https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/96122/VanBanGoc_100.2015.QH13.P3.pdf). |

**Qwen OCR là vấn đề pháp lý khác với cách nghe Zalo.** Alibaba nói vùng endpoint quyết định nơi lưu, phạm vi triển khai quyết định nơi máy chạy suy luận. Họ nói không dùng dữ liệu để huấn luyện, nhưng vẫn lưu dữ liệu phát sinh từ lời gọi theo chính sách. Nếu ảnh CCCD đi tới dịch vụ/máy chủ ngoài Việt Nam, phải đánh giá nghĩa vụ chuyển dữ liệu xuyên biên giới theo Luật 91 Điều 20 và NĐ 356 Điều 17–18; hồ sơ đánh giá, thời hạn và ngoại lệ cần đối chiếu cấu hình thực tế với người phụ trách pháp lý. Thay bằng “model nội địa” chỉ giải bài toán này nếu vị trí chạy, lưu, sao lưu và nhà thầu phụ thực sự phù hợp. [Vùng Alibaba](https://www.alibabacloud.com/help/en/model-studio/regions), [chính sách riêng tư](https://www.alibabacloud.com/help/en/model-studio/privacy-notice), [Luật 91](https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/7/91qh.signed.pdf), [NĐ 356](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/356-nd.signed.pdf).

NĐ 356 cho một số doanh nghiệp nhỏ/siêu nhỏ lựa chọn hoặc miễn vài nghĩa vụ hồ sơ trong điều kiện cụ thể, **nhưng loại trừ trường hợp trực tiếp xử lý dữ liệu nhạy cảm** cùng những trường hợp khác. Không mặc định văn phòng được miễn do quy mô nhỏ. Điều 42 của nghị định làm NĐ 13/2023 hết hiệu lực từ 01/01/2026; checklist chỉ dựa trên NĐ 13 đã cũ. [NĐ 356 Điều 41–42](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/356-nd.signed.pdf).

## Kiến trúc đề nghị nếu Bot API vượt phép thử

| Bước | Trên máy chủ Zalo | Trên máy công chứng |
|---|---|---|
| Nhận tin | Nhận webhook, kiểm tra khóa, ghi **sự kiện nguyên bản** xuống đĩa trước khi trả thành công. | Có thể đang tắt. |
| Lấy ảnh | Tải URL ảnh ngay, đếm, kiểm tra tệp/độ nét, ghi mã tin, nhóm, người gửi, giờ Zalo gửi và giờ server nhận. | Không có ảnh. |
| Bàn giao | OCR trên server; lưu ảnh tối đa theo hạn đã chọn; tạo gói raw có trạng thái và dấu kiểm, giữ gói để điều tra sai sót. | Nút Sync lấy gói raw. |
| Duyệt | Giữ nhật ký giao nhận, ACK và trạng thái lỗi. | Soạn hồ sơ bóc tách chữ, regex, ghép hai mặt/người/tài sản và cho nhân viên duyệt. |

Đây là [SL] triển khai, **không** phải cam kết webhook đã bảo đảm phát lại. Chỉ trả mã thành công sau khi sự kiện đã được lưu bền; OCR chạy sau. Mỗi ảnh có khóa chống trùng theo nguồn + nhóm + mã tin + vị trí ảnh; trạng thái tối thiểu: “đã thấy tin → đã lấy ảnh → đã OCR → đã bàn giao”. Lỗi ở bước nào phải hiện ở bước đó. Dùng giờ Zalo cấp làm giờ gửi, đồng thời ghi giờ server nhận và giờ máy công chứng Sync. “testWebhook”/heartbeat chỉ nói còn kết nối, không chứng minh một ảnh cụ thể đã tới. [Webhook](https://docs.zaloplatforms.com/docs/BOT/webhook), [testWebhook](https://docs.zaloplatforms.com/docs/BOT/apis/testWebhook).

Repo hiện có ranh giới [zalo/README.md](../../../../zalo/README.md) và [contracts/README.md](../../../../contracts/README.md): Zalo giữ ảnh 168 giờ, gói handoff chỉ gửi raw/OCR, máy chính không nhận ảnh; Soạn hồ sơ xử lý chữ/ghép thông tin. Báo cáo này **chưa đổi** ranh giới đó. Nếu chọn Chrome/Electron/folder watcher ngay trên máy công chứng, ảnh sẽ có mặt trên máy ấy; khi đó cần sửa contract và quy tắc lưu/xóa minh bạch trước khi triển khai.

**Để phát hiện “bắt trượt” cần có số đối chiếu từ nguồn hoặc người gửi.** Nếu Zalo không cấp danh sách đầy đủ các tin theo khoảng giờ, server không biết một ảnh chưa từng được phát cho bot. Biên nhận “server đã thấy 10 ảnh” cần được người gửi/nhân viên đối chiếu 10 ảnh trong Zalo. Với cổng upload/Mini App, server có thể xác nhận ngay số file được chọn và tải thành công. [SL]

## Phép thử quyết định

Dùng **ảnh mẫu không chứa dữ liệu cá nhân thật**, nhóm thử nghiệm do văn phòng kiểm soát. Không đọc kho/cookie nội bộ hoặc vượt xác thực Zalo. Mỗi vòng lưu bảng “số gửi / số sự kiện bot thấy / số URL tải xong / số ảnh OCR được / số gói Sync”, kèm mã tin và ba mốc giờ. [CT]

1. Tạo Bot theo hướng dẫn chính thức, gọi “getMe”, ghi “can_join_groups”, thử mời vào **nhóm có sẵn**. Nếu không được, dừng nhánh nghe nhóm đó. [Tạo Bot](https://docs.zaloplatforms.com/docs/BOT/create_bot), [getMe](https://docs.zaloplatforms.com/docs/BOT/apis/getMe).
2. Gửi 10 ảnh đơn, một album 10 ảnh, ảnh dưới dạng file, ảnh có/không @bot, reply, caption và chat riêng. So mã tin với webhook; tải từng ảnh, đo kích thước/độ phân giải, không chỉ đếm URL.
3. Tắt app công chứng và máy chính nhưng giữ server sống. Lặp với server mất mạng ngắn, restart, webhook trả 5xx rồi hồi phục, URL ảnh gần hết hạn. Đo Zalo có gửi lại, trong bao lâu. Nếu không có bằng chứng, ghi “không bảo đảm tải bù”.
4. Ghi mọi sự kiện “message.unsupported.received”, kiểm tra bot bị thoát nhóm, quota Basic, token thay đổi, ảnh nhận được nhưng OCR lỗi.
5. Nếu Bot chỉ nhận @mention, thử quy trình tag trên từng ảnh với người dùng, đếm thao tác. Nếu không chấp nhận, thử Mini App/cổng upload hoặc nhập thủ công buổi sáng. Chỉ nghiên cứu zca-js/tự động hóa Web trong môi trường nghiên cứu tách biệt.

**Không gọi một đường là “không bỏ sót” vì một lần đạt 10/10.** Cần nhiều phiên, lỗi được phân loại và một biên nhận để so. Nếu không thể phát hiện ảnh chưa từng tới bot, giao diện và spec phải nói rõ giới hạn đó. [SL]

## Câu hỏi còn phải nhờ Zalo hoặc phép thử trả lời

- Bot Basic vào được nhóm cá nhân đang có không? Điều kiện nào khiến “can_join_groups” thành true? Bot thấy ảnh không @mention không, hay phải @bot trên **chính ảnh**?
- Một lần gửi nhiều ảnh tạo mấy sự kiện? “photo” là bản nào, giữ được bao lâu? Khi webhook trả 5xx, Zalo gửi lại mấy lần/trong bao lâu? Có API lấy lịch sử hay kiểm toán tin bỏ lỡ không?
- Bot API và OA GMF có được dùng với CCCD/sổ đỏ trong quy trình công chứng không theo chính sách hiện hành? Muốn nhúng Zalo Web hoặc tự động tải qua giao diện thì xin chấp thuận ở đâu?
- Nhà OCR được chọn lưu ảnh/prompt/chữ ở đâu, bao lâu, ai là nhà thầu phụ? Văn phòng đã có căn cứ xử lý của các chủ thể dữ liệu và quy trình giữ bí mật tương ứng chưa?

## Nguồn và giới hạn

Nguồn chính: [Zalo Bot](https://docs.zaloplatforms.com/docs/BOT), [webhook](https://docs.zaloplatforms.com/docs/BOT/webhook), [Bot Platform](https://bot.zapps.me/), [Zalo OA](https://oa.zalo.me/home/resources/news/_4601792943864106455), [Mini App](https://docs.zaloplatforms.com/docs/MA/api/media/file/openMediaPicker), [Zalo Help](https://help.zalo.me/huong-dan/chuyen-muc/nhan-tin-va-goi/nhan-tin/tai-ve-may-luu-my-documents-cac-anh-video-file-quan-trong-tren-zalo/), [điều khoản Zalo](https://zaloapp.com/mobile/zalo/dieukhoan/), [zca-js](https://github.com/RFS-ADRENO/zca-js), [Tencent BrowserSkill](https://github.com/Tencent/BrowserSkill), [Electron](https://www.electronjs.org/docs/latest/api/session), [Chrome](https://developer.chrome.com/docs/extensions/reference/api/downloads), [Luật 91](https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/7/91qh.signed.pdf), [NĐ 356](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/356-nd.signed.pdf), [Luật Công chứng](https://congbao.chinhphu.vn/van-ban/luat-so-46-2024-qh15-43574.htm), [Alibaba Model Studio](https://www.alibabacloud.com/help/en/model-studio/regions). Bằng chứng kỹ thuật phụ nằm ở thư mục “digests” cùng cấp.

Một số trang Zalo chỉ hiện nội dung qua chỉ mục tìm kiếm và bản Luật 91 là PDF quét ảnh; đường dẫn văn bản chính thức đã được đối chiếu. Tài liệu API và điều khoản có thể thay đổi. Phạm vi Bot trong nhóm, bản gốc của ảnh và khả năng khôi phục sự kiện **chưa được kiểm thử thực tế**; không thể cam kết triển khai trước khi qua các phép thử trên.

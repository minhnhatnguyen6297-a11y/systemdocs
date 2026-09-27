# Lấy ảnh bằng trình duyệt: bằng chứng và lựa chọn

Truy cập nguồn: **26/09/2026**. Chỉ đọc tài liệu và `D:/systemdocs/shell/package.json`; chưa đăng nhập Zalo, chưa thử tải ảnh, chưa thay runtime. **[TL]** = tài liệu xác nhận; **[SL]** = suy luận thiết kế, cần thử trên Zalo. Các trang Electron, Node.js, CDP và Playwright là tài liệu cập nhật liên tục, không có ngày xuất bản cố định được xác nhận.

## Kết luận cho quyết định

**[SL]** Có thể làm nhập nhiều ảnh với ít thao tác theo cả hai hướng: Zalo Web nhúng Electron, hoặc Chrome riêng có tiện ích mở rộng. Trình duyệt bên ngoài thuận lợi khi app nghiệp vụ đóng: Chrome và bộ nhận tệp vẫn có thể chạy riêng. Nhúng Electron thuận lợi cho một màn hình làm việc, nhưng nếu toàn bộ Electron thoát thì bộ nhận nằm trong nó cũng dừng.

Không hướng nào tự chứng minh lấy đủ ảnh trong mọi nhóm, toàn bộ lịch sử hay đủ ảnh gốc. “Nhận 10 ảnh ban đêm” cần phân biệt: chỉ đóng cửa sổ nghiệp vụ; thoát toàn bộ bộ nhận; mất mạng; và máy ngủ/tắt. Trường hợp cuối không thể nhận trực tiếp trên chính máy đó; việc tải bù sáng hôm sau phụ thuộc dữ liệu còn được Zalo cung cấp và khả năng tìm lại.

## So sánh phương án

| Cách | Thao tác, tự động hóa dự kiến [SL] | Điểm mạnh | Giới hạn phải chứng minh |
|---|---|---|---|
| Tải bằng giao diện Zalo Web → thư mục nhập | Người dùng chọn/tải; app quét nhiều tệp | Ít phụ thuộc cấu trúc bên trong Zalo | Tính năng chọn hàng loạt thực tế, thông tin người gửi/nhóm/thời điểm |
| Electron `WebContentsView` + bắt tải xuống | Người dùng bấm tải; app tiếp nhận tự động | Gắn trải nghiệm với hồ sơ; biết tải thành công/thất bại | Bắt tải không tự phát hiện mọi ảnh mới; đăng nhập và tải trong Electron chưa thử |
| Chrome + extension + `downloads` | Có thể thêm lệnh nhập cả lô đang được phép xem | Dùng trình duyệt thông thường; hoạt động độc lập app nghiệp vụ | Phải tìm đúng ảnh, giữ ngữ cảnh và theo dõi từng lượt tải |
| Extension + native messaging | Chrome gửi thông tin sang chương trình Windows cục bộ | Chuyển lô sang hàng đợi bền vững trên đĩa | Cần cài bộ nhận; giới hạn quyền và xác minh nguồn thông điệp |
| Tự điều khiển Chrome/Electron qua DOM | Mở nhóm, cuộn lịch sử, bấm tải theo kịch bản | Có thể giảm nhiều thao tác lặp | Dễ hỏng khi giao diện đổi; không được suy từ một nhóm sang mọi nhóm |
| DevTools/CDP, Network/WebSocket | Quan sát dữ liệu mà trang đang nhận | Hữu ích để hiểu nguồn ảnh và kiểm tra thiếu/trùng | Không phải API sự kiện chính thức của Zalo; dữ liệu quan sát chưa chắc là ảnh gốc |

DOM là cấu trúc các thành phần trang. CDP là giao thức điều khiển/kiểm tra Chrome. Native messaging là cầu nối được Chrome hỗ trợ giữa tiện ích và chương trình cục bộ. Các hàng trên có thể kết hợp; chúng không phải sáu sản phẩm đã chạy thử.

## Những điểm kỹ thuật đã xác minh

**[TL] Electron:** `session.will-download` báo khi một lượt tải chuẩn bị diễn ra; `session.downloadURL()` mới chủ động khởi tạo lượt tải. Đó không phải đăng ký nhận mọi ảnh trong Zalo. `DownloadItem.done` có ba trạng thái `completed`, `cancelled`, `interrupted`; chỉ trạng thái đầu xác nhận hoàn tất. [Session](https://www.electronjs.org/docs/latest/api/session), [DownloadItem](https://www.electronjs.org/docs/latest/api/download-item).

**[TL] Phiên bản:** repo khai báo Electron `^31.0.2`; lịch chính thức ghi Electron 31 hết hỗ trợ ngày **14/01/2025**. Đây là khai báo phụ thuộc, chưa xác minh phiên bản tiến trình đang chạy. Tài liệu latest ghi `getInitiatorOrigin()` và tham số `frame` của `will-download` chỉ thêm ở **43.7/44.4**; không thiết kế dựa vào chúng cho Electron 31. [Lịch Electron](https://releases.electronjs.org/schedule).

**[TL] Nhúng trang:** tài liệu API đánh dấu `BrowserView` deprecated từ 29; Electron khuyên tránh thẻ `<webview>` và cân nhắc `WebContentsView`. Trang từ mạng phải tắt `nodeIntegration`, bật `contextIsolation` và sandbox. **[SL]** Nếu chọn nhúng, cần phiên làm việc riêng và một cầu nối nhỏ chỉ nhận yêu cầu nhập tệp hợp lệ. [BrowserView](https://www.electronjs.org/docs/latest/api/browser-view), [webview](https://www.electronjs.org/docs/latest/api/webview-tag), [bảo mật](https://www.electronjs.org/docs/latest/tutorial/security).

**[TL] Extension:** content script đọc DOM, mặc định chạy trong môi trường JavaScript tách biệt; không tự đọc được mọi biến nội bộ của trang. `chrome.downloads` khởi tạo, theo dõi và tìm lượt tải; đường dẫn chỉ định nằm tương đối dưới Downloads. **[SL]** Có thể tải cả lô khi đã xác định danh sách hợp lệ; một nút tải lô không bảo đảm tự tìm đủ ảnh. [Content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts) (trang ghi cập nhật 17/09/2012), [Downloads](https://developer.chrome.com/docs/extensions/reference/api/downloads) (11/09/2026).

**[TL] Cầu nối:** native messaging cần quyền và danh sách extension được phép kết nối; thông điệp từ chương trình cục bộ tối đa 1 MB, chiều ngược lại 64 MiB. **[SL]** Nên gửi mã công việc/thông tin tệp và giao nhận có xác nhận; tránh coi một thông điệp chứa ảnh là kho lưu trữ. Extension có thể bị Chrome dừng khi rảnh; hàng đợi cần lưu bền vững. [Native messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging) (16/09/2026), [vòng đời](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle) (trang ghi 02/05/2023).

**[TL] Chrome 136:** `--remote-debugging-port/pipe` không còn được tôn trọng với thư mục dữ liệu mặc định; cần `--user-data-dir` riêng. Playwright hỗ trợ kết nối CDP nhưng ghi rõ mức hỗ trợ thấp hơn kết nối Playwright đầy đủ. [Chrome, 17/03/2025](https://developer.chrome.com/blog/remote-debugging-port), [Playwright](https://playwright.dev/docs/api/class-browsertype#browser-type-connect-over-cdp).

## Độ đầy đủ và khôi phục

**[TL]** DevTools Network ghi yêu cầu trong khi công cụ mở; giao diện WebSocket chỉ hiển thị 100 thông điệp cuối. CDP có sự kiện nhận WebSocket và đọc nội dung phản hồi. [Network, 16/07/2024](https://developer.chrome.com/docs/devtools/network/reference), [CDP Network](https://chromedevtools.github.io/devtools-protocol/tot/Network/).

**[SL]** DOM chỉ cho thấy nội dung đã được đưa vào trang; lịch sử chưa tải không tự xuất hiện. Ảnh thu nhỏ, bộ nhớ đệm, địa chỉ `blob:` và gói WebSocket không chứng minh có đủ bản gốc. Cần kiểm tra kích thước, nội dung tệp và đối chiếu từng ảnh; không suy “DevTools thấy mạng” thành “lấy đủ 100%”.

**[SL]** Bộ theo dõi thư mục chỉ biết tệp đã đến ổ đĩa. Khi khởi động phải quét lại, đối chiếu sổ công việc và dấu vân tay tệp để phục hồi tệp bị bỏ qua. Quét lại không khôi phục ảnh chưa từng tải. Ngày tạo tệp/ngày tải không thay thế thời điểm gửi; trường thiếu phải để “không biết”. Node.js cũng ghi các hạn chế của `fs.watch`, đặc biệt trên ổ mạng. [Node.js](https://nodejs.org/api/fs.html#fswatchfilename-options-listener).

**[SL] Ranh giới:** tải trang Zalo chính thức trong trình duyệt tự làm không tự chứng minh việc nhúng/tự động hóa được Zalo cho phép. Đọc cùng phân tích điều 4.7 tại [điều khoản Zalo](https://zaloapp.com/mobile/zalo/dieukhoan/) trong báo cáo chính; bản này không kết luận pháp lý.

## Bảy phép thử nhỏ được đề xuất, chưa thực hiện

1. Gửi bộ ảnh mẫu được phép dùng: ảnh đơn, album 10 ảnh, ảnh gửi dạng tệp; đối chiếu đủ số lượng và chất lượng với thao tác tải chuẩn.
2. Thử nhóm đang mở, nhóm chưa mở và lịch sử chưa cuộn; đo phần bị bỏ sót của từng cách.
3. Gửi 10 ảnh khi chỉ đóng app nghiệp vụ, rồi lặp với bộ nhận thoát, mất mạng và máy ngủ; đo nhận ngay/tải bù/không phục hồi.
4. Ngắt mạng hoặc đóng Chrome giữa lượt tải; khởi động lại, kiểm tra hàng đợi tiếp tục và không nhập tệp dở dang.
5. Tải lặp cùng ảnh, ảnh trùng tên và bản nén khác nhau; kiểm tra chống trùng mà không gộp nhầm nguồn.
6. Đối chiếu nhóm, người gửi, mã tin, giờ gửi, giờ nhận và giờ tải; trường không thu được phải ghi thiếu.
7. Thử phiên đăng nhập hết hạn, giao diện Zalo đổi và Chrome/Electron cập nhật; hệ thống phải báo dừng cần xử lý, không âm thầm báo đã lấy đủ.

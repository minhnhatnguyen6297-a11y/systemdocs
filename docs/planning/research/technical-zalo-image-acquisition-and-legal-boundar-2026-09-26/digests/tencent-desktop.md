# Tencent BrowserSkill và các đường lấy ảnh Zalo Desktop

Trạng thái: đã đối chiếu nguồn công khai; chưa chạy thử với Zalo. Ngày khảo sát: 26/09/2026. Không cài đặt, không đăng nhập tài khoản, không chạy thử trên dữ liệu người dùng.

## Kết luận đã kiểm chứng

- Tencent BrowserSkill là công cụ nối một trợ lý AI với Chrome/Edge đang đăng nhập. Gồm CLI, dịch vụ nền và tiện ích trình duyệt; người dùng chọn trợ lý và mô hình riêng. Nó không tự tạo quyền truy cập Zalo.
- README chính thức công bố đọc trang, tương tác, chụp màn hình, upload/download ở chế độ cục bộ. Chế độ từ xa chưa hỗ trợ upload/download. README cũng nói bản trong kho có thể đi trước bản trên cửa hàng.
- BrowserSkill điều khiển trang web; khả năng hoạt động với Zalo Web, tải ảnh nguyên gốc, lấy đủ lịch sử và độ ổn định đều cần kiểm thử riêng. Không thể suy ra khả năng điều khiển Zalo PC chỉ từ hỗ trợ Chrome/Edge.

Nguồn đã đọc: [Tencent/BrowserSkill README](https://github.com/Tencent/BrowserSkill), truy cập 26/09/2026, không hiển thị ngày xuất bản; tin cậy cao cho mô tả sản phẩm, chưa có kiểm thử Zalo.

## Bằng chứng bổ sung

1. [Kiến trúc tại commit a2717648](https://github.com/Tencent/BrowserSkill/blob/a2717648e8a525b0d21d83d30f96360642b461b9/docs/architecture.md): lệnh CLI gửi qua dịch vụ nền; dịch vụ chuyển tác vụ tới tiện ích Chrome/Edge; tiện ích dùng CDP/WebExtension tác động lên tab. Đây là kiến trúc điều khiển browser có đăng nhập, không phải Zalo API. [README](https://github.com/Tencent/BrowserSkill) nói remote mode hiện không hỗ trợ upload/download. Browser giữ ở PC và agent chạy server chưa tạo kênh chuyển file như ca sử dụng.
2. [Zalo Help PC](https://help.zalo.me/huong-dan/chuyen-muc/zalo-cong-viec/ca-nhan-hoa-zalo-tren-may-tinh/) có thư mục tải, tự mở cùng máy và mô tả nút “Thoát” vẫn chạy nền. [Hướng dẫn lưu ảnh](https://help.zalo.me/huong-dan/chuyen-muc/nhan-tin-va-goi/nhan-tin/tai-ve-may-luu-my-documents-cac-anh-video-file-quan-trong-tren-zalo/) yêu cầu chọn ảnh/file rồi bấm lưu. Không tìm được tài liệu chính thức hứa tự lưu mọi ảnh nhóm vào thư mục.
3. [Zalo backup](https://help.zalo.me/huong-dan/chuyen-muc/quan-ly-tai-khoan-zalo/sao-luu-va-khoi-phuc/chi-tiet-ve-cac-du-lieu-duoc-zalo-sao-luu/) loại trừ một số dữ liệu/nhóm/tệp. Không nên coi Cloud/My Documents/backup là hàng đợi sự kiện đầy đủ.
4. [Power Automate unattended](https://learn.microsoft.com/en-us/power-automate/desktop-flows/run-unattended-desktop-flows) quản lý phiên desktop riêng và có các ràng buộc phiên/quyền; UI Automation Windows có thể điều khiển một số thành phần, nhưng với Zalo PC chưa kiểm chứng control cụ thể, ảnh gốc, khả năng phục hồi và số thao tác. RPA không biến Zalo PC thành API chính thức.
5. [Android nhận nhiều file](https://developer.android.com/develop/ui/compose/sharing/receive) và [iOS Share extension](https://developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/Share.html) là API hệ điều hành cho app của ta nhận ảnh do người dùng chia sẻ. Không chứng minh Zalo có menu chia sẻ đúng ảnh/hồ sơ trong ca này; phải thử trên từng phiên bản.

## Ranh giới kỹ thuật và sử dụng

Ảnh tải bằng nút chính thức khác ảnh chụp màn hình, ảnh trong cache/DB, thumbnail hoặc dữ liệu thông báo. Các nguồn phụ không tự cung cấp mã tin, giờ gửi hay bản đủ nét; không có bằng chứng về 100% lịch sử. Không nghiên cứu giải mã kho riêng hoặc né cơ chế bảo vệ. Nếu dùng BrowserSkill trong tương lai, phải thẩm định quyền truy cập các tab đang đăng nhập và bảo vệ kết quả debug/audit trước khi cài.

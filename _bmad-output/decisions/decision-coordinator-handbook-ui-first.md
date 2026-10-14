# Sổ tay coordinator theo góc nhìn sản phẩm

**Ngày:** 14/10/2026 · **Owner:** đã chốt qua yêu cầu trong phiên

## Quyết định

Coordinator là trợ lý cá nhân chia sẻ góc nhìn sản phẩm và UI với owner, không
được mặc định xem như một worker. Owner cần một file tổng hợp ngắn theo góc nhìn
đó. Phản hồi trực tiếp của owner: “Agent coordinator là 1 trợ lý cá nhân, tôi
cần đồng nhất góc nhìn của tôi và coordinator chứ không phải coi đó là 1 worker.
hiện thiếu 1 file tổng hợp ngắn theo kiểu như vậy.”

## Cách thực hiện trong phiên

Owner chấp thuận bắt đầu sửa sổ tay. Trong phiên này, chọn viết lại
`_bmad-output/specs/product-overview.md` tại chỗ thành bản đồ đầu phiên theo
menu và màn hình thực tế: mục tiêu sản phẩm, việc đang mở có nguồn, chức năng
nhỏ, tài liệu và điểm vào code. Phân biệt UI hiện có với Draft/chưa xác minh;
bước tiếp theo chỉ là đề xuất. Đồng bộ đường đọc từ README và AGENTS.

Đây là lựa chọn triển khai trong phiên, không phải owner chỉ định tên file hay
yêu cầu coordinator thay thế workflow của repo. Lý do chọn cách này: phần giới
thiệu cũ dài và thiên về developer; chưa giúp owner và coordinator cùng tìm
nhanh việc đang làm trong giao diện.

## Ranh giới

Đây là bản đồ tìm đường, không thay spec hành vi. Thay đổi này chỉ chạm sổ tay,
đường đọc và quyết định này; không đổi code, hành vi sản phẩm, contract hay
spec feature.

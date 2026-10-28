# NAIA-9 — quyết định tiếp nhận

Ngày 03/10/2026, Owner trả lời trong chat tiếp nhận:

> Theo ngày lập hồ sơ; ngày cấp giấy tờ chỉ giúp đọc địa chỉ cũ/mới.

Áp dụng cho nơi niêm yết: ngày đích là `ngay_lap_ho_so`. Ngày cấp của đúng
giấy nguồn chỉ giúp đọc địa chỉ theo cấu trúc cũ/mới. Không lấy ngày CCCD của
người thay ngày sổ đất, không lấy ngày giấy tờ thay ngày hồ sơ.

Nơi cấp giấy khai tử giữ riêng với nơi niêm yết. Địa chỉ cư trú cuối cùng không
tự chứng minh nơi cấp giấy khai tử. Giá trị đã xác nhận/sửa tay không tự bị ghi đè.

Nguồn cũ: comments NAIA-9 `01a0fd70-3664-7a6a-a564-9f198c3b62d3`,
`01a0fd8d-1bb9-7173-8454-17b0cf816919`, 02/10/2026. Trả lời mới giải quyết
câu hỏi ngày đích còn mở trong các task NAIA-15/18/21.

Owner bổ sung trong cùng chat: `https://sapnhap.bando.com.vn/` là SOT
tra cứu tên xã và tỉnh cũ–mới. Kiểm tra API hoặc file tổng hợp từ chính website.
Huyện không có trong cấu trúc hiện hành, không tự dựng huyện mới. NSO/nghị
quyết chỉ đối chiếu hoặc bổ sung lịch sử có nguồn; không đè tên chuẩn Bando.

Owner bổ sung04/10/2026: lấy Bando tạo SOT timeline thay đổi tên. Website chỉ
có lần gần nhất A→B; Owner sẽ cung cấp các lần trước sau. Cấu trúc cần thêm
được A→B→C→D cho xã, huyện, tỉnh; giữ cả sáp nhập/chia tách. Không thu lịch
sử thay Owner trong lượt này. Ngày chưa có căn cứ để trống/chưa xác nhận;
ngày tải website không phải ngày đổi tên. Huyện chưa có từ Bando vẫn được
cấu trúc hỗ trợ để Owner bổ sung sau.

Owner bổ sung 04/10/2026: docs phải giải thích cách phát triển dữ liệu sáp nhập
về sau để agent tiếp nhận hiểu cách mở rộng hệ thống. Spec feature cần có ví dụ
thêm nhiều mốc, gộp/tách, xử lý phần chưa biết và cập nhật nguồn mà không mất
lịch sử đã xác nhận. Phân biệt phần đang chạy với hướng mở rộng trong tương lai.

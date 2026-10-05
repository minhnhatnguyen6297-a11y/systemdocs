# Đáp án đọc tay — chỉ mục bàn giao

**Trạng thái:** Draft; chưa được Owner duyệt, chưa chạy chấm engine.

Bản đầy đủ chứa dữ liệu cá nhân của mẫu, được giữ cục bộ tại `.agents/local-only/notary-20261005/answers-draft.md`; không đưa vào Git. Nguồn gốc còn ở worktree 1aae và bộ Word bên ngoài repo. Dùng [manifest](selected-samples.json) và [bộ bảng quy tắc](../../../review/sample-rules-20261005/README.md) để tiếp tục duyệt.

## Bảng xem nhanh

| Mẫu | Nội dung đọc thấy | Người / tài sản dự kiến | Điểm kiểm tra chính |
|---|---|---|---|
| S01 | Chuyển nhượng | 2 / 1 | Mẫu cơ bản đủ dữ liệu |
| S02 | Tặng cho phần đất tách | 4 / 1 | Địa chỉ chung; thửa giao dịch khác thửa nguồn |
| S03 | Giấy ủy quyền xóa mã số thuế | 2 / 0 | Người nhận ủy quyền trong một đoạn; địa chỉ có P./TP. |
| S04 | Hợp đồng ủy quyền đất | 2 hồ sơ người đầy đủ + 1 tên đồng sử dụng / 1 | Người chỉ ghi tên trong vùng tài sản |
| S05 | Phân chia di sản | 7 danh tính có mô tả, có một hồ sơ lặp / 1 | Thân nhân chết, từ chối di sản; câu nguồn lẫn tên |
| S06 | Từ chối di sản | 2 hồ sơ + 1 tên đồng sở hữu / 1 | Giấy khai tử không thay CCCD |
| S07 | Di chúc | 2 / 1 | Loại bỏ người làm chứng và công chứng viên |
| S08 | Cam kết tài sản riêng | 2 / 1 thiếu trường | Không tạo 22 tài sản từ tên giấy đấu giá |
| S09 | Thế chấp | 3 danh tính, một mô tả lặp / 1 thửa | Đại diện ngân hàng; người vay ở điều khoản riêng |
| S10 | Đơn đăng ký biến động | 1 / 0 | Danh sách giấy kèm không đủ tạo tài sản |
| S11 | Phiếu đăng ký biện pháp bảo đảm | 1 cá nhân / 1 | Dữ liệu nằm trong bảng; tổ chức có mã số thuế |
| S12 | File ghép 5 đơn/tờ khai | Xem từng văn bản dưới đây | Không lấy dữ liệu văn bản trước để điền văn bản sau |
| S13 | Chỉ lời chứng | 2 / 0 | Đọc trực tiếp Người; không giả định tên từ filename |
| S14 | Biên bản họp gia đình | 4 hồ sơ + 1 tên người đã mất / 1 | Ông/bà; hai loại đất; số tờ cũ–mới |
| S15 | Giấy ủy quyền có CMND cũ | 3 / 1 thiếu trường | Giữ riêng hai bộ số/ngày/nơi cấp |
| S16 | Thế chấp dạng bảng và đoạn dài | 3 danh tính / 2 | Hai thửa, hai serial; đại diện chỉ có tên |
| S17 | Đơn và biên bản ghép | Xem từng văn bản dưới đây | Hai thửa cùng serial; bản đồ mới để trống |
| S18 | Lời chứng thế chấp độc lập | 2 / 0 | Đại diện có giấy chính; ngân hàng có ĐKDN và địa chỉ riêng |
| S19 | Lời chứng sửa đổi thế chấp | 3 / 0 | Ngân hàng có mã số thuế; hai người dùng chung địa chỉ |
| S20 | Hủy bỏ thế chấp | 3 Người; Hoa có 2 bản ghi giấy tờ / 1 tài sản thiếu trường | Hai phiên bản cùng số thuộc một Người; không cần liên kết các phiên bản |

“Hồ sơ + tên” và “danh tính” trong bảng là quan sát, chưa chốt tổng dòng ở các trường hợp dẫn chiếu/lặp. Không được dùng bảng này làm bộ chấm tự động trước khi Owner kiểm tra những điểm đó.

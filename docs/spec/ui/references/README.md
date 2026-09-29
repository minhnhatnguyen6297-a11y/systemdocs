# References — ảnh thiết kế đã duyệt (MIN-123 / MIN-124 / MIN-133)

Các ảnh dưới đây là **tham chiếu thị giác đã được owner duyệt** cho hướng
thiết kế lại UI Electron chung (Notary + Upload Lab). Chúng là nguồn chuẩn
về **tông trắng/xanh, bố cục và thành phần** mà `../README.md`,
`../tokens.json` và spec feature của
module diễn giải thành quy tắc.

## Danh mục

| File | Kích thước | Nội dung | Phiên bản/nguồn | Ngày duyệt |
|---|---|---|---|---|
| `approved-drafting.png` | 1496×1051 | Tab `Soạn hồ sơ`: thanh action trên cùng (Nhập file, Zalo*, Hủy thay đổi, Cập nhật), Stage hai card (Tài sản bảng chuyển vị / Người bảng dòng), tầng `Sơ đồ thừa kế` với Pool + canvas + cụm zoom + `Lưu sơ đồ`/`Xuất Word` | Gốc: `.agent/tasks/MIN-123/references/approved-drafting.png` (phiên MIN-123); id `approved-drafting` v1 | 27/09/2026 |
| `approved-land-types.png` | 1631×964 | Dialog `Loại đất · Tài sản 1`: nút `+ Loại đất`, bảng chuyển vị (dòng nhãn × cột thửa, `×` xóa trên header cột), footer `Hủy`/`Áp dụng` | Gốc: `.agent/tasks/MIN-123/references/approved-land-types.png` (phiên MIN-123); id `approved-land-types` v1 | 27/09/2026 |
| `approved-drafting-v2.png` | 1440×775 | Tab `Soạn hồ sơ` mật độ cao (MIN-133): không còn thanh trạng thái engine; một thanh trên cùng cao khoảng 42px gộp tab + hành động; Stage Tài sản : Người = 35 : 65, hàng bảng 25px, ô nhập nằm trong ô bảng; card viền 1px trên nền `#e9edf2`; tầng sơ đồ lấp phần chiều cao còn lại với Pool 176px, `Lưu sơ đồ`/`Xuất Word` trên header vùng sơ đồ, node trống viền đứt không nhãn. Không còn giới hạn chiều ngang 860px | Gốc: `.agent/tasks/MIN-133/mockup/mockup-1440x775.png` (mockup render bằng Electron; ảnh 1920×1080 và 1366×768 cùng thư mục dùng kiểm co giãn); id `approved-drafting` v2 — thay v1 về mật độ và tỷ lệ, giữ v1 làm lịch sử | 28/09/2026 |

\* Nút **Zalo** trong ảnh là hiện trạng chưa rõ — theo ràng buộc MIN-123, bản
thật phải **disable** và không tái giới thiệu UI/lệnh/trạng thái Zalo.

## Quy tắc dùng — đọc trước khi diễn giải

- **Chỉ tham chiếu thị giác.** Ảnh chốt tông màu, tỉ lệ vùng, kiểu thành
  phần và mật độ. Chúng **không** chốt: giá trị token hex chính xác (lấy
  `tokens.json` sau duyệt), ngữ nghĩa nghiệp vụ, thứ tự/giá trị mặc định.
- **Dữ liệu trong ảnh là mẫu.** Tên người, số tài sản (3 cột), ngày tháng,
  số địa chỉ, số lượng `3 loại`… tất cả là dữ liệu minh họa — **cấm** biến
  thành mặc định nghiệp vụ, fixture, hay hằng số trong code/test. Điều này
  áp dụng cả cho `approved-drafting-v2.png` (3 tài sản, 7 người, tên và số
  giấy tờ trong ảnh đều là ví dụ).
- **Khi v1 và v2 khác nhau** về mật độ, tỷ lệ vùng, chiều cao hàng/nút hay
  vị trí nút của màn `Soạn hồ sơ`: theo `approved-drafting-v2.png` và
  `../tokens.json` v1.1.0.
- **Bảng tài sản chuyển vị** (thuộc tính = dòng, tài sản = cột) là hướng
  đích thay cho form dọc hiện hữu — diễn giải chi tiết ở
  `docs/spec/notary_v2/visual-reference.md`.
- **Chip số `1/2/3` trên node sơ đồ** (`Chủ đất`/`Nhận đất`) chỉ xác nhận
  hình thức tương tác; **ngữ nghĩa** (ánh xạ tới tài sản/vị trí, mô hình
  hai bên) là quyết định nghiệp vụ thuộc P2 (MIN-125) — đừng suy ra contract
  từ ảnh.
- `Mở rộng` trong cụm zoom và `Hủy thay đổi` trên action bar là phần tử đã
  duyệt về **hiện diện**, nhưng ngữ nghĩa chờ chốt — xem
  `../README.md`.
- Thêm ảnh approved mới: commit file ảnh + thêm hàng vào bảng trên kèm
  nguồn/ngày duyệt; **không ghi đè** ảnh cũ (giữ lịch sử quyết định).

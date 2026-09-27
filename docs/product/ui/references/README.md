# References — ảnh thiết kế đã duyệt (MIN-123 / MIN-124)

Hai ảnh dưới đây là **tham chiếu thị giác đã được owner duyệt** cho hướng
thiết kế lại UI Electron chung (Notary + Upload Lab). Chúng là nguồn chuẩn
về **tông trắng/xanh, bố cục và thành phần** mà `../DESIGN.md`,
`../EXPERIENCE.md`, `../tokens.json` và hai file `visual-design.md` của
module diễn giải thành quy tắc.

## Danh mục

| File | Kích thước | Nội dung | Phiên bản/nguồn | Ngày duyệt |
|---|---|---|---|---|
| `approved-drafting.png` | 1496×1051 | Tab `Soạn hồ sơ`: thanh action trên cùng (Nhập file, Zalo*, Hủy thay đổi, Cập nhật), Stage hai card (Tài sản bảng chuyển vị / Người bảng dòng), tầng `Sơ đồ thừa kế` với Pool + canvas + cụm zoom + `Lưu sơ đồ`/`Xuất Word` | Gốc: `.agent/tasks/MIN-123/references/approved-drafting.png` (phiên MIN-123); id `approved-drafting` v1 | 27/09/2026 |
| `approved-land-types.png` | 1631×964 | Dialog `Loại đất · Tài sản 1`: nút `+ Loại đất`, bảng chuyển vị (dòng nhãn × cột thửa, `×` xóa trên header cột), footer `Hủy`/`Áp dụng` | Gốc: `.agent/tasks/MIN-123/references/approved-land-types.png` (phiên MIN-123); id `approved-land-types` v1 | 27/09/2026 |

\* Nút **Zalo** trong ảnh là hiện trạng chưa rõ — theo ràng buộc MIN-123, bản
thật phải **disable** và không tái giới thiệu UI/lệnh/trạng thái Zalo.

## Quy tắc dùng — đọc trước khi diễn giải

- **Chỉ tham chiếu thị giác.** Ảnh chốt tông màu, tỉ lệ vùng, kiểu thành
  phần và mật độ. Chúng **không** chốt: giá trị token hex chính xác (lấy
  `tokens.json` sau duyệt), ngữ nghĩa nghiệp vụ, thứ tự/giá trị mặc định.
- **Dữ liệu trong ảnh là mẫu.** Tên người, số tài sản (3 cột), ngày tháng,
  số địa chỉ, số lượng `3 loại`… tất cả là dữ liệu minh họa — **cấm** biến
  thành mặc định nghiệp vụ, fixture, hay hằng số trong code/test.
- **Bảng tài sản chuyển vị** (thuộc tính = dòng, tài sản = cột) là hướng
  đích thay cho form dọc hiện hữu — diễn giải chi tiết ở
  `notary_v2/docs/platform/case-workspace/visual-design.md`.
- **Chip số `1/2/3` trên node sơ đồ** (`Chủ đất`/`Nhận đất`) chỉ xác nhận
  hình thức tương tác; **ngữ nghĩa** (ánh xạ tới tài sản/vị trí, mô hình
  hai bên) là quyết định nghiệp vụ thuộc P2 (MIN-125) — đừng suy ra contract
  từ ảnh.
- `Mở rộng` trong cụm zoom và `Hủy thay đổi` trên action bar là phần tử đã
  duyệt về **hiện diện**, nhưng ngữ nghĩa chờ chốt — xem
  `../EXPERIENCE.md` §10.
- Thêm ảnh approved mới: commit file ảnh + thêm hàng vào bảng trên kèm
  nguồn/ngày duyệt; **không ghi đè** ảnh cũ (giữ lịch sử quyết định).

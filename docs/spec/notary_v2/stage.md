# Stage — Dữ liệu đã commit của hồ sơ

**Trạng thái:** Active · **Owner:** `notary_v2`

## 1. Công dụng

Stage là nguồn dữ liệu Người và Tài sản đã được người dùng xác nhận cho workspace.
Mọi Input chỉ trở thành Stage sau thao tác `Cập nhật` thành công.

## 2. Draft và committed

- **Draft:** bản người dùng đang thêm, sửa, xóa hoặc sắp xếp; chỉ sống trong
  phiên UI.
- **Committed:** snapshot server trả sau `workspace_create` hoặc
  `workspace_commit_stage`; Pool và Diagram dùng bản này.
- `Hủy` là thao tác client: khôi phục cả Stage và Diagram draft về snapshot
  committed gần nhất, không tăng revision.

## 3. Thao tác

- Người và Tài sản sửa trực tiếp trên Stage.
- Chỉ nút xóa của dòng được xóa dòng đó.
- Xóa/sửa draft chưa đổi server và chưa prune Diagram.
- `Cập nhật` gửi toàn bộ Stage cùng `base_revision`.
- Hồ sơ mới: lần `Cập nhật` đầu gọi `workspace_create`, tạo case và revision 1.
  Client sinh một `idempotency_key` UUID v4 cho nháp và dùng lại đúng key khi
  retry sau timeout; đổi key có thể tạo hồ sơ trùng.

## 4. Input và output

Input gồm Stage snapshot `{people, assets}`, case metadata và `base_revision`
khi cập nhật. Output gồm revision mới, Stage đã gán `entity_id`, Diagram sau
prune và render model do backend tính lại.

`row_id` do client sinh UUID v4 và giữ ổn định qua commit/reload. `entity_id`
là ID database, có thể null trước commit.

## 5. Quy tắc dữ liệu

- Người: 6 trường nhập liệu lưu DB (`ten`, `ngaysinh`, `ngaychet`, `sogiayto`,
  `ngaycap`, `diachi`). Bắt buộc `ten`/`ho_ten`; các trường ngày dùng
  `YYYY-MM-DD`, `YYYY` hoặc null. Các trường `loaigiayto`, `noicap`, `loaicutru`
  được backend suy ra theo mốc quy định (01/10/2024 và 01/07/2025).
- CCCD/giấy tờ là free text, không dùng làm Case key.
- Tài sản v2 tối đa 3; vị trí là thứ tự mảng, vị trí 1 là primary theo nghĩa
  engine. Không dùng `is_primary` trong wire v2.
  * Bỏ trường lẻ `thoi_han` ở cấp tài sản vì là trường mồ côi: không tự đắp
    vào cụm khi xuất; giữ nguyên bản gốc và báo cần đối chiếu.
  * Thông tin loại đất lưu cụm 3 trường: `loaidat` - `dientich` - `thoihan`
    (tối đa 20 cụm một tài sản). Mỗi cụm là một bản ghi trong bảng con
    `property_land_rows` (UNIQUE `(property_id, vitri)`, `vitri` = vị trí
    cụm 1..20, giữ nguyên vị trí trống); `properties.land_rows_json` chỉ
    còn vai trò tương thích/chuyển đổi, không còn là nguồn lưu chính.
  * Wire/snapshot chấp nhận cả key canonical (`loaidat`/`dientich`/`thoihan`)
    lẫn key legacy (`loai_dat`/`dien_tich`/`thoi_han`); cùng trường mà hai
    key mang giá trị mâu thuẫn → `stage_validation_error` code `conflict`,
    không chọn ngầm.
  * Định danh phân biệt Loại đất thứ mấy trong Tài sản thứ mấy:
    Cú pháp `[trường][loại đất M][tài sản N]` viết liền không dấu, **không có dấu gạch dưới `_`**.
    Ví dụ: `loaidat12` = loại đất 1 của tài sản 2; `dientich12` = diện tích loại đất 1 của tài sản 2; `thoihan12` = thời hạn loại đất 1 của tài sản 2.
    Review MIN-141 (29/09/2026) chốt: chỉ dùng dạng đầy đủ `loaidat<M><N>`,
    không thêm alias rút gọn `loaidatM` vì `loaidat12` trùng nghĩa giữa
    "cụm 1 tài sản 2" và "cụm 12 tài sản 1".
- Reorder đổi nghĩa vị trí nhưng không đổi `row_id`.
- Hồ sơ thừa kế bắt buộc `owner_row_id`; hồ sơ `two_party` cấm trường này.
- Hồ sơ có 3 trường quản lý: `noiniemyet` (suy từ địa chỉ đất + bảng xã),
  `nguoinhanuyquyen` (danh mục quen/tạo mới), `noidungviec` (nhập tay).
  Tất cả tuân thủ quy tắc viết liền không dấu, không có ký tự `_`.

## 6. Commit và lưu

Backend thực hiện trong một transaction:

```text
validate
→ upsert/link Người và Tài sản
→ prune tham chiếu Diagram không còn hợp lệ
→ chạy lại engine
→ tăng revision
→ commit
```

Một dòng sai làm toàn bộ commit thất bại. `base_revision` khác server revision
phải báo `workspace_conflict`; không ghi đè cưỡng bức.

## 7. Quan hệ với feature khác

- Input thêm/sửa Stage draft, không commit thay người dùng.
- Pool = người trong Stage committed chưa được gán Diagram.
- Diagram chỉ tham chiếu `row_id` của Stage committed.
- Word đọc snapshot Stage và Diagram đã lưu.

## 8. Lỗi và ngoại lệ

- Lỗi field gắn đúng `row_id`, field và code.
- Xóa phần tử Stage khi commit phải prune mọi tham chiếu Diagram trong cùng
  transaction.
- Hồ sơ legacy có hơn 3 tài sản vẫn được đọc đủ kèm warning; commit bị chặn
  đến khi còn tối đa 3.
- Commit lỗi không được xóa draft hoặc local UI state.

## 9. Giao diện

- Tài sản dùng bảng chuyển vị: mỗi cột là Tài sản 1..3; mỗi dòng là một
  thuộc tính. Cụm loại đất sửa các dòng `(Loại đất, Diện tích, Thời hạn)`.
- Bảng hồ sơ: Bố trí thêm 3 dòng ngay dưới các dòng tài sản (`Nơi niêm yết`,
  `Người nhận ủy quyền`, `Nội dung việc`), giảm 10% độ cao các ô để không
  chiếm nhiều diện tích màn hình.
- Người dùng bảng dòng có kéo sắp xếp, radio `Để lại`, các field chính và nút
  xóa. Danh sách dài cuộn cả trang, không tạo vùng cuộn riêng trong card.
- Lỗi field tô đúng ô/dòng theo `row_id`. `+ Người`, `+ Tài sản` và xóa chỉ
  thay draft cho tới khi commit.
- Toolbar dùng `Nhập file`, `Hủy thay đổi`, `Cập nhật`; chấm dirty cho biết
  Stage chưa commit. Quy tắc màu/kích thước chung thuộc `docs/spec/ui/`.

## 10. Kiến trúc, câu hỏi và lịch sử

Stage v2 thay mô hình flag phân tán bằng snapshot có revision. Owner chốt
27/09/2026: vòng đời draft/committed, `owner_row_id`, tài sản theo vị trí và
commit nguyên khối thuộc `notary.case-drafting.v2`.
Owner chốt 01/10/2026 (MIN-141): Từ điển dữ liệu Người đầy đủ, chuẩn hóa cụm
loại đất (1..20) bỏ `thoi_han` lẻ mồ côi, bổ sung 3 dòng hồ sơ dưới tài sản,
và quy tắc đặt tên trường tiếng Việt không dấu viết liền số.

## 11. Nguồn

- Contract: `contracts/notary-case-drafting.md` §13.
- Ảnh bố cục đã duyệt: `docs/spec/ui/references/approved-drafting-v2.png`.
- Source chính: `shell/src/renderer/notary/case-drafting-view.js` và
  `notary_v2/routers/cases.py`.

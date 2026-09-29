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

- Người bắt buộc `ho_ten`; các trường ngày dùng `YYYY-MM-DD`, `YYYY` hoặc null.
- CCCD/giấy tờ là free text, không dùng làm Case key.
- Tài sản v2 tối đa 3; vị trí là thứ tự mảng, vị trí 1 là primary theo nghĩa
  engine. Không dùng `is_primary` trong wire v2.
- Reorder đổi nghĩa vị trí nhưng không đổi `row_id`.
- Hồ sơ thừa kế bắt buộc `owner_row_id`; hồ sơ `two_party` cấm trường này.

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

## 9. Kiến trúc, câu hỏi và lịch sử

Stage v2 thay mô hình flag phân tán bằng snapshot có revision. Owner chốt
27/09/2026: vòng đời draft/committed, `owner_row_id`, tài sản theo vị trí và
commit nguyên khối thuộc `notary.case-drafting.v2`.

Còn mở: từ điển dữ liệu Người đầy đủ và quyền hiển thị/sửa của từng field.

## 10. Nguồn

- Contract: `contracts/notary-case-drafting.md` §13.
- Chi tiết hiện hành: `notary_v2/docs/platform/case-workspace/drafting-tab.md`.

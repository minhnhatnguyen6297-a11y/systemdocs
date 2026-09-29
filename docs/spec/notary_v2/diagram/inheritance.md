# Diagram thừa kế

**Trạng thái:** Quy tắc engine hiện hành có hiệu lực; tài liệu nghiệp vụ mở rộng
`notary_v2/docs/domains/inheritance/spec.md` vẫn có phần Draft cần duyệt riêng.

## 1. Công dụng

Biểu diễn người để lại di sản, vợ/chồng, cha mẹ, con và các nhánh thế vị. Từ
quan hệ đã lưu, backend xác định hàng thừa kế, người nhận, người không nhận và
phần di sản theo rule được duyệt.

## 2. Dữ liệu vào

- Người đã commit trong Stage.
- `owner_row_id` của người để lại di sản.
- Node, `parentSlotIds`, `spouseSlotId`.
- `ownPositions` và `receivePositions` theo vị trí tài sản 1..3.
- Ngày chết và các dữ kiện pháp lý đã được xác nhận.

## 3. Quy tắc chính

- Owner là một người Stage riêng, không suy từ cờ chủ đất cũ.
- Quan hệ vợ/chồng và cha-con phải nhất quán hai chiều theo engine.
- Không cho vòng quan hệ hoặc một người nằm ở nhiều slot xung đột.
- Người chết trước/sau owner ảnh hưởng nhánh thế vị; dữ liệu ngày thiếu phải tạo
  warning hoặc slot cần bổ sung, không tự đoán.
- Người từ chối nhận di sản là khái niệm pháp lý riêng, không đồng nghĩa người
  không được đánh dấu nhận trên UI.
- Frontend không tính phân số. Python tạo allocation, breakdown, warning và
  `requiredSlots`.

Công thức và ma trận ca chi tiết vẫn được kiểm chứng tại
`notary_v2/docs/domains/inheritance/technical/inheritance-engine.md` và tests.

## 4. Tài sản

- Tối đa 3 tài sản trong contract v2.
- Vị trí tài sản là index 1..3 của Stage assets.
- `ownPositions`: tài sản người đó sở hữu.
- `receivePositions`: tài sản người đó nhận.
- Reorder tài sản đổi vật đang ở vị trí; dấu chọn bám số vị trí, không bám
  `row_id`. UI phải cảnh báo khi reorder/xóa làm đổi nghĩa.

## 5. Kết quả và nơi lưu

`engineInput` lưu quan hệ và lựa chọn đã validate trong `case_state_json`.
`engineResult` do backend tạo cùng lần save để audit và Word dùng. Projection
participant có thể được thay trong transaction, nhưng không được quyết định
ngược Stage/Pool/Diagram.

## 6. Word

- Thông tin cá nhân lấy từ Stage.
- Quan hệ và người nhận lấy từ Diagram/engine result.
- Chủ tài sản lấy từ `ownPositions`.
- Người không nhận và người từ chối phải theo rule riêng; không suy một nhóm từ
  nhóm kia.

## 7. Lỗi và ngoại lệ

- Thiếu slot bắt buộc: trả `requiredSlots`, không bịa node.
- State `invalid`: save bị chặn. State hợp lệ nhưng `incomplete`: được save và
  trả `requiredSlots`/warning; chưa được coi là đủ điều kiện xuất văn bản.
- Engine lỗi: không xóa state cũ.
- Hồ sơ legacy: migrate khi đọc theo rule đã có; GET không âm thầm ghi DB.

## 8. Câu hỏi và lịch sử

- Các lựa chọn “Nhận 1/2/3”, contract A/B và quyền sở hữu per-asset cần data
  model được duyệt; không suy từ `willReceive`/`isLandOwner` cũ.
- Nghiệp vụ từ chối, không nhận, thừa kế thế vị và ngoại lệ phải được owner/legal
  xác nhận trước khi đổi engine. Authority chưa xác minh phải ghi `[CONFIRM]`.
- Spec nghiệp vụ v2 cũ là draft; workflow/code đang chạy không tự biến mọi đề
  xuất trong draft thành quy tắc hiện hành.

## 9. Nguồn

- `notary_v2/docs/domains/inheritance/workflow.md`.
- `notary_v2/docs/domains/inheritance/spec.md`.
- `notary_v2/docs/domains/inheritance/technical/inheritance-engine.md`.
- `contracts/notary-case-drafting.md` §13.

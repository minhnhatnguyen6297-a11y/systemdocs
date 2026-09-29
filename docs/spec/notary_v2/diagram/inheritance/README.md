# Diagram thừa kế

**Trạng thái:** Contract `notary.case-drafting.v2` đã Approved; runtime chỉ là
bằng chứng hiện trạng. [`engine.md`](./engine.md) là thiết kế đích chưa có
hiệu lực; nghiệp vụ mở rộng tại [`business-rules.md`](./business-rules.md)
vẫn Draft, chưa được tự áp dụng.

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
- `Người không nhận = tất cả người trên Diagram − Chủ đất − Người nhận` là
  công thức UI owner giữ ngày 24/09/2026. Đây không đồng nghĩa từ chối pháp lý.

Công thức kỹ thuật nằm tại [`engine.md`](./engine.md); ví dụ và nguồn tại
[`examples.md`](./examples.md) và [`provenance.md`](./provenance.md). Các file
này không nâng business rule Draft thành quy tắc đã duyệt.

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

## 7. Giao diện

- Tree theo thế hệ; cặp vợ/chồng thành một cụm, nhánh thế vị nằm dưới đúng
  người trung gian. Node đã có dữ liệu không tự biến mất sau evaluate.
- Card chỉ có quyết định `Chủ`/`Nhận` theo vị trí tài sản; không có nút `Từ
  chối`. Slot chỉ sinh khi backend trả là cần.
- `Xem cách tính` hiển thị một dòng cho mỗi người, gồm tổng và từng nguồn; UI
  không hiển thị JSON và không tự tính lại.
- Canvas rộng dùng cuộn ngang/pan/zoom, không bẻ nhánh hoặc thu node đến mức
  khó đọc. Cảnh báo gom thành vùng rõ ràng, không chồng popup.

## 8. Lỗi và ngoại lệ

- Thiếu slot bắt buộc: trả `requiredSlots`, không bịa node.
- State `invalid`: save bị chặn. State hợp lệ nhưng `incomplete`: contract hiện
  hành cho lưu và trả `requiredSlots`/warning. Việc xuất Word của state này
  chưa được contract hiện hành chặn theo `status`; xem câu hỏi mở bên dưới.
- Engine lỗi: không xóa state cũ.
- Hồ sơ legacy: migrate khi đọc theo rule đã có; GET không âm thầm ghi DB.

## 9. Câu hỏi và lịch sử

- Các lựa chọn “Nhận 1/2/3”, contract A/B và quyền sở hữu per-asset cần data
  model được duyệt; không suy từ `willReceive`/`isLandOwner` cũ.
- Nghiệp vụ từ chối, không nhận, thừa kế thế vị và ngoại lệ phải được owner/legal
  xác nhận trước khi đổi engine. Authority chưa xác minh phải ghi `[CONFIRM]`.
- Spec nghiệp vụ v2 cũ là draft; workflow/code đang chạy không tự biến mọi đề
  xuất trong draft thành quy tắc hiện hành.
- Quy tắc lưu/xuất khi `incomplete` còn mâu thuẫn: contract v2 cho lưu;
  [`engine.md`](./engine.md) đề xuất chặn lưu; Draft
  [`business-rules.md`](./business-rules.md) đề xuất cho lưu và xuất có nhãn.
  Chưa tự chọn một phương án để sửa runtime hay contract.
- Còn rủi ro migration giữa `case_state_json.diagram.*`, `engine_state_json`,
  `diagram_payload` và projection legacy. Save phải ưu tiên state canonical,
  prune ghost/orphan nhưng giữ metadata hợp lệ; không suy API mới từ tên field cũ.
- Việc nối cạnh/mũi tên mới cần fixture hoặc ảnh chấp nhận riêng; không rebuild
  toàn Graph/Diagram chỉ để sửa một connector.

## 10. Nguồn

- [`business-rules.md`](./business-rules.md) — Draft mới nhất.
- [`engine.md`](./engine.md) — contract kỹ thuật/đối chiếu implementation.
- [`examples.md`](./examples.md) và [`provenance.md`](./provenance.md) — phụ lục.
- [`case-state-parked.md`](./case-state-parked.md) — bản thiết kế lưu state cũ
  đang tạm gác, chỉ để hiểu nguyên nhân lỗi và lựa chọn từng cân nhắc.
- `contracts/notary-case-drafting.md` §13.

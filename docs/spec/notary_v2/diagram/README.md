# Diagram — Quan hệ và vai trò trong hồ sơ

**Trạng thái:** Active cho `inheritance`; contract v2 đã duyệt cho
`inheritance` và `two_party`

## 1. Công dụng

Diagram gán người từ Stage vào vị trí có ý nghĩa nghiệp vụ. Nó lưu quan hệ,
vai trò và lựa chọn liên quan tài sản; backend dùng state đó để validate, tính
kết quả và dựng render model.

Spec theo domain:

- Thừa kế: [`inheritance/`](./inheritance/README.md).
- Hai bên A/B: [`two-party.md`](./two-party.md).

[`stage-sync-draft.md`](./stage-sync-draft.md) là phụ lục đề xuất cũ về
đồng bộ Stage/Pool/Diagram, chưa được duyệt. Các phần đã chốt được viết trong
spec hiện hành ở trên; phần còn mở của phụ lục phải kiểm lại trước khi làm.

## 2. Input và output

Input chung là `diagram.state` draft và domain của Case. Cụ thể:

- `diagram_evaluate` có `case_id`; nếu chưa có Case thì bỏ `case_id` và gửi
  thêm Stage draft. Đây là read-only, không có `base_revision`.
- `diagram_save` có `case_id`, `base_revision` và Diagram; `case_type` lấy từ
  workspace server, không phải field tự do trong payload.

Output:

- `diagram.state` canonical đã validate;
- `render_model` do Python tạo;
- `requiredSlots`, warnings, errors và kết quả nghiệp vụ;
- revision mới sau `diagram_save`.

## 3. Thao tác

- Kéo người từ Pool vào slot: gán `personId` cho node.
- Di chuyển node: đổi slot/quan hệ trong Diagram draft.
- Gỡ node: xóa gán, không xóa người khỏi Stage.
- Chọn quan hệ/tài sản: sửa field Diagram draft theo domain.
- `Xem cách tính`: gọi evaluate read-only, chỉ hiển thị render model backend.
- `Lưu sơ đồ`: validate và ghi state trong một transaction.
- `Hủy`: khôi phục Stage/Diagram draft về snapshot committed gần nhất.

## 4. Cách biểu diễn và lưu

Diagram không tự ghi một bảng quan hệ chung. Với hồ sơ thừa kế hiện hành, state
được lưu trong `case_state_json.diagram.engineInput`; backend tạo
`engineResult` cùng lần save và có thể cập nhật projection participant theo
quy tắc module.

Ví dụ: kéo người A vào slot `child_1` của owner và spouse:

```json
{
  "id": "child_1",
  "personId": "<row_id-cua-A>",
  "parentSlotIds": ["owner", "spouse"],
  "spouseSlotId": null
}
```

Ý nghĩa: A là con của người tại slot `owner` và `spouse`. Backend kiểm các slot
tồn tại, `personId` thuộc Stage, không có vòng quan hệ và chạy engine. Không
được suy thành bảng cha-con khác nếu spec/schema chưa chốt.

## 5. Contract v2

- `diagram_state.version = 3` và `domain` bắt buộc.
- Domain `inheritance` dùng node quan hệ cha/mẹ/vợ-chồng/con.
- Domain `two_party` dùng 30 slot `p1..p30`; không mang field quan hệ thừa kế.
- Node v2 dùng `ownPositions` và `receivePositions` theo vị trí tài sản 1..3.
- `isLandOwner` và `willReceive` là field legacy, bị cấm trên wire v2.

Contract chuẩn và schema máy đọc:
[`contracts/notary-case-drafting.md`](../../../../contracts/notary-case-drafting.md)
và `contracts/notary-case-drafting/*.schema.json`.

## 6. Quy tắc lưu

- `personId` phải thuộc Stage committed.
- Save mang đúng `base_revision`; conflict không được ghi đè.
- Frontend không gửi kết quả tính như sự thật. Backend luôn tính lại từ input.
- State sai cấu trúc/nghiệp vụ (`invalid`) không được persist. State hợp lệ
  nhưng kết quả `incomplete` vẫn được lưu; backend trả `requiredSlots`/warning
  để người dùng bổ sung sau.
- Save lỗi giữ nguyên Stage, Diagram và projection cũ.
- Reload và Word phải dùng cùng snapshot đã lưu.

## 7. Giao diện

- Canvas hiển thị node, mũi tên và slot thiếu từ `render_model`.
- Drag payload phải chứa đủ `row_id/personId`; không suy người từ vị trí DOM.
- Slot trống cần thiết do backend trả trong `requiredSlots`.
- Cảnh báo nằm gần node/slot liên quan; không chỉ báo chung ở đầu trang.
- Pool rộng khoảng 176 px; node đã gán hiển thị tên, năm sinh–mất và chip vị
  trí tài sản `Chủ`/`Nhận`. Node trống là drop target viền đứt và vẫn có
  `aria-label`/đường thao tác bàn phím.
- Quan hệ cha–con dùng đường vuông góc, vợ/chồng dùng nét ngang đứt; không vẽ
  mũi tên tài sản vì một người có thể nhận từ nhiều nguồn.
- Header Diagram giữ `+ Slot`, `Xem cách tính`, `Đánh giá thử`, zoom/mở rộng,
  `Lưu sơ đồ`, `Xuất Word`; dirty Diagram tách khỏi dirty Stage.

## 8. Lỗi và ngoại lệ

- Node trỏ ra ngoài Stage: `diagram_reference_outside_stage`.
- Quan hệ sai, vòng lặp, slot/position không hợp lệ: `diagram_invalid_state`.
- Domain không khớp `case_type`: `diagram_domain_mismatch`.
- Field legacy trong state v2: reject, không âm thầm chuyển nghĩa.

## 9. Kiến trúc, câu hỏi và lịch sử

Python là authority cho validate và tính. `render_model` là output trình bày,
không phải input pháp lý. Contract v2 được owner duyệt 27/09/2026; runtime
triển khai theo issue P5/P6 tương ứng.

Còn mở: dữ liệu per-asset không được suy từ các flag v1; mỗi domain mới phải
chốt semantics trước khi thêm node/field. Domain hai bên xem
[`two-party.md`](./two-party.md).

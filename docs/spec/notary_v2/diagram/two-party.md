# Diagram hai bên

**Trạng thái:** Contract v2 Approved 27/09/2026; Word chưa hỗ trợ

## 1. Công dụng

Xếp người vào hai bên của hợp đồng song phương mà không dùng quan hệ thừa kế.
Domain này chỉ quản lý vị trí; không chạy engine chia di sản.

## 2. Vị trí và thao tác

- Có đúng 30 slot ổn định: `p1..p15` là Bên A, `p16..p30` là Bên B.
- Slot trống được giữ nguyên; không dồn người sang trái hoặc đổi số slot.
- Thả người vào slot trống: gán `personId`.
- Thả vào slot đã có người: hoán đổi hai `personId`.
- Gỡ người: slot trở lại rỗng và người quay về Pool.
- Mọi thao tác có đường bàn phím qua menu gán vị trí.

## 3. Dữ liệu và giới hạn

State dùng `version: 3`, `domain: two_party` và 30 node có `id` cố định.
Node chỉ giữ `id`, `personId`, `ownPositions`, `receivePositions`; cấm field
quan hệ thừa kế như `parentSlotIds`/`spouseSlotId`. Stage tối đa 30 người và
cấm `owner_row_id` cho Case hai bên.

## 4. Lưu, lỗi và contract

Save dùng `case_id`, `base_revision` và state canonical đủ 30 slot. Slot ngoài
`p1..p30`, người ngoài Stage, trùng người hoặc mang field thừa kế đều bị từ
chối. Không được tự đổi domain của Case.

Word export hiện trả `case_type_unsupported`; không nhân bản template thừa kế
để “chạy tạm”. Chi tiết wire và fixture:
[`contracts/notary-case-drafting.md`](../../../../contracts/notary-case-drafting.md)
mục 13.5 và `contracts/notary-case-drafting/examples/draft-v2/`.

## 5. Lịch sử và câu hỏi

Owner duyệt layout 30 vị trí, ranh giới hai bên, giữ slot trống và hành vi swap
trong MIN-125; runtime triển khai P7/MIN-130. Mapping vai trò hợp đồng chi tiết
và bộ văn bản Word cho domain này vẫn cần spec riêng trước khi mở rộng.

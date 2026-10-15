---
id: 25
type: story
title: "Đổi loại hồ sơ đã lưu theo quy tắc đã chốt"
parent: none
covers: []
after: [3]
assignee: ""
refined: false
hitl: false
risk: high
---

# Đổi loại hồ sơ đã lưu theo quy tắc đã chốt

## Description

Triển khai semantics đổi loại được chọn ở #3 để yêu cầu d9da640e không mất sau khi issue quyết định đóng. Giữ Stage và transaction/revision; chưa chọn tự reset sơ đồ.

## Acceptance Criteria

1. **Đổi theo quyết định**
   **Given** hồ sơ Hai bên/Thừa kế đã lưu đủ điều kiện quyết định
   **When** chuyên viên thực hiện tương tác đổi loại được #3 chọn
   **Then** loại và tác động Diagram/domain/Word đúng quyết định đó, Người/Tài sản giữ ID và giá trị theo invariant đã duyệt
2. **Thất bại nguyên tử**
   **Given** stale revision, hồ sơ khóa, lỗi hoặc thao tác không được quyết định #3 cho phép
   **When** thử đổi loại
   **Then** không tạo hồ sơ đổi dở hoặc mất nháp, hồ sơ cũ còn dùng được; nếu #3 chọn bước hủy/từ chối thì bước đó cũng giữ các invariant này
3. **Mở lại và xuất**
   **Given** hồ sơ đổi thành công theo cách giữ/chuyển gán và binding do #3 chọn
   **When** mở lại và xuất văn bản hỗ trợ
   **Then** trạng thái và đầu ra đúng lựa chọn đã lưu, không giữ tham chiếu domain cũ sai nghĩa

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C24
- source — _bmad-output/specs/notary_v2/README.md, §2, §4–6, §9

## Notes

- Tracking: C24; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Chuyển domain sai có thể mất Người/Tài sản hoặc giữ quan hệ/binding không còn đúng.
- Unknown: #3 phải ghi semantics được duyệt trước refinement implementation. Report d9da640e đã yêu cầu chức năng; không hỏi lại có muốn. Giữ loại bất biến tới khi contract chuyển đổi duyệt; bảo toàn revision/lock/rollback, không đoán reset hoặc mapping domain/Word.
- Boundary: không tự chọn preview, xác nhận, hủy, reset gán hoặc cách remap; chỉ thực hiện tương tác và quy tắc mà #3 đã ghi nhận được duyệt.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

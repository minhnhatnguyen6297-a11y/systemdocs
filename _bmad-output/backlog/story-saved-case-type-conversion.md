---
id: 25
type: story
title: "Đổi loại hồ sơ đã lưu theo quy tắc đã chốt"
parent: none
covers: []
after: [3]
assignee: ""
refined: true
hitl: false
risk: high
---

# Đổi loại hồ sơ đã lưu theo quy tắc đã chốt

## Description

Triển khai semantics đổi loại đã chốt ở #3 ([decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md), contract §13.18) cho yêu cầu d9da640e: giữ ID + giá trị Người/Tài sản của Stage; reset Diagram rỗng theo domain mới; buộc chọn `document_type` mới + xác nhận phần Diagram mất trước khi ghi; giữ guard transaction/revision/khóa/atomic.

## Acceptance Criteria

1. **Đổi theo quyết định**
   **Given** hồ sơ Hai bên/Thừa kế đã lưu đủ điều kiện quyết định
   **When** chuyên viên thực hiện tương tác đổi loại được #3 chọn
   **Then** loại và tác động Diagram/domain/Word đúng decision đã duyệt, Người/Tài sản giữ ID và giá trị, Diagram reset rỗng theo domain mới và `document_type` mới được người dùng chọn có xác nhận
2. **Thất bại nguyên tử**
   **Given** stale revision, hồ sơ khóa, lỗi hoặc thao tác ngoài đường chuyển loại đã duyệt
   **When** thử đổi loại
   **Then** không tạo hồ sơ đổi dở hoặc mất nháp, hồ sơ cũ còn dùng được; hủy/thất bại không đổi state/revision
3. **Mở lại và xuất**
   **Given** hồ sơ đổi thành công theo decision #3 (giữ Stage, reset Diagram, `document_type` mới, binding Word giữ nguyên)
   **When** mở lại và xuất văn bản hỗ trợ
   **Then** trạng thái và đầu ra đúng lựa chọn đã lưu, không giữ tham chiếu domain cũ sai nghĩa

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Refined từ decision #3; **chưa built**, không phải xác nhận đã chạy.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C24
- source — _bmad-output/specs/notary_v2/README.md, §2, §4–6, §9

## Notes

- Tracking: C24; **built 16/10/2026** — refined từ đáp án #3 ([decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md), contract §13.18); implementation + smoke xong, independent Quick **CLEAN** (parent đọc full diff + proof artifacts, no actionable findings). #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Chuyển domain sai có thể mất Người/Tài sản hoặc giữ quan hệ/binding không còn đúng.
- Semantics đã chốt (#3): giữ Stage (ID + giá trị); reset Diagram rỗng theo domain mới; buộc chọn `document_type` mới + xác nhận phần mất trước khi ghi; chuyển vào Thừa kế cần `owner_row_id` từ Stage, vào Hai bên cấm; giữ guard `base_revision`/khóa/atomic; binding Word không remap ngầm; không thêm chặn hồ sơ đã xuất/bound.
- Implementation 16/10/2026: dedicated `notary.workspace_convert_type`, saved-case dialog, revision/lock/rollback + opt-in atomic cancel completion; normal commit/update giữ bất biến loại. Schema/validator/mock/callers đã theo command riêng.
- Boundary: chỉ thực hiện tương tác và quy tắc #3 đã duyệt; không tự thêm reset/remap/capability ngoài Diagram/domain + guard `document_type`/owner.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.
- Bằng chứng tự kiểm: [summary JSON](../tmp/issue-25-saved-case-conversion/evidence/implementation-summary.json). Service/inheritance/DOCX/batch **252 passed, 2 skipped**; adapter/job/mock **263 passed, 2 skipped**, mock sau test bổ sung **157 passed, 2 skipped**; Node **177 passed**; contract **83 files / 0 unexpected**. Electron source thật + IPC/SQLite tạm: hai chiều, owner chọn rõ, cancel không tăng revision, Stage giữ nguyên; dirty Stage + stale Diagram draft giữ nháp. Real original export guard → reassign/reconfirm → DOCX đạt; existing `1. PCDS .docx` export đạt, hash nguồn không đổi.
- Closeout: dedicated `notary.workspace_convert_type` + dialog `Đổi loại`; Stage/meta nháp phải Cập nhật trước; lỗi/xung đột giữ nháp; binding cũ giữ guard `word.original_mapping_invalid`. Evidence: [summary](../tmp/issue-25-saved-case-conversion/evidence/implementation-summary.json), [full diff](../tmp/issue-25-saved-case-conversion/evidence/full-diff.patch), [runtime IPC proof](../tmp/issue-25-saved-case-conversion/evidence/ui-ipc-proof.json), [service export proof](../tmp/issue-25-saved-case-conversion/evidence/service-export/proof.json), test logs cùng thư mục. Giới hạn đã quan sát: không native picker/Word pagination review, không packaged artifact; một lần chụp CDP sau đó lỗi window visibility (ảnh dialog thật trước đó vẫn giữ). Commit/push chỉ các path explicit được parent cho phép.

---
id: TASK-8
title: Viet lai engine Word theo catalog moi va du lieu mau can
status: To Do
assignee: []
created_date: '2026-10-04 15:40'
updated_date: '2026-10-04 16:25'
labels:
  - notary
  - repair
dependencies: []
references:
  - .agents/review-plan-20261004/investigation-report.md
  - backlog/tasks/task-2 - Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md
  - docs/spec/notary_v2/word-output.md
  - docs/spec/notary_v2/stage.md
type: feature
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Viết lại phần xác định dữ liệu/điền token; giữ helper định dạng an toàn nếu phù hợp. Q5 đã chốt chỉ kiểm dữ liệu mẫu cần, mẫu Người không đòi tài sản/sơ đồ; xử lý cả đường lưu DB còn bắt tài sản. Q1/Q2 chờ Owner về nghĩa token cũ/UQ. Sửa W-05 schema response lỗi. Chi tiết gói F TASK-2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Q1/Q2 được ghi decision/spec trước phần phụ thuộc; catalog mới có một nghĩa rõ, đúng người/ghế/vai trò đã lưu.
- [ ] #2 Mẫu chỉ Người xuất được khi chưa tài sản/sơ đồ; đường lưu hỗ trợ hợp lệ, không tạo asset giả; mẫu cần nguồn nào kiểm nguồn đó.
- [ ] #3 Tổng diện tích xuất đúng trường tổng, ghế trống không dồn, trùng tên/reorder/xóa không đổi danh tính ngoài spec.
- [ ] #4 Response original mapping invalid và mọi block_reason thật phù hợp schema/validator/examples.
- [ ] #5 Batch/original giữ nguồn hash, binding/context, hủy/cleanup/publish; thiếu dữ liệu báo rõ, expected độc lập với resolver.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

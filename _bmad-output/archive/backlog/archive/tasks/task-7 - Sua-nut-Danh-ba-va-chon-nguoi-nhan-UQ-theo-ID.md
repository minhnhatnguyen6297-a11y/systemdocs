---
id: TASK-7
title: Sua nut Danh ba va chon nguoi nhan UQ theo ID
status: To Do
assignee: []
created_date: '2026-10-04 15:40'
labels:
  - notary
  - repair
dependencies: []
references:
  - .agents/review-plan-20261004/investigation-report.md
  - backlog/tasks/task-2 - Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md
  - docs/spec/notary_v2/stage.md
  - docs/spec/notary_v2/word-output.md
type: bug
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
DB-01/02: nút bị khóa sau input và tự gán ID đầu tiên khi trùng tên. Sửa chọn danh bạ theo ID, phân biệt người, tìm ngoài 200 đầu, tạo mới riêng. Q2 chờ xác nhận nguồn UQ trong Word; không cần chờ Q2 để sửa nút và ID. Chi tiết gói E TASK-2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Nút dùng được ngay sau input/change/blur hợp lệ, không cần thao tác khác để vẽ lại.
- [ ] #2 Chọn người ID 22 giữa hai người cùng tên lưu/reload đúng 22; gõ tên mơ hồ không tự gán ID 11.
- [ ] #3 Tìm được người ngoài danh sách 200 đầu; hủy picker không đổi draft; tạo mới không tạo tên rỗng.
- [ ] #4 Q2 ghi decision/spec trước đổi nguồn nhóm UQ; danh bạ và template không tự dùng hai nghĩa chưa được xác nhận.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

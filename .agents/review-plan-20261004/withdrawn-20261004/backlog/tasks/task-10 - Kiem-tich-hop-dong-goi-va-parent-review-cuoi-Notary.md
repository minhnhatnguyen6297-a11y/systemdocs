---
id: TASK-10
title: Kiem tich hop dong goi va parent review cuoi Notary
status: To Do
assignee: []
created_date: '2026-10-04 15:40'
labels:
  - notary
  - repair
dependencies:
  - TASK-5
  - TASK-6
  - TASK-7
  - TASK-8
  - TASK-9
references:
  - .agents/review-plan-20261004/investigation-report.md
  - backlog/tasks/task-2 - Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md
  - docs/spec/notary_v2/stage.md
  - docs/spec/notary_v2/administrative-address.md
  - docs/spec/notary_v2/input/docx-import.md
  - docs/spec/notary_v2/word-output.md
type: task
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Nghiệm thu chuỗi nhập-Stage-lưu-địa chỉ-danh bạ-Word qua Electron và bản đóng gói. Parent kiểm diff, bộ đáp án giữ lại, Word từng trang và ca hỏng. Chi tiết gói H/checklist TASK-2; agent implement bàn giao trước, parent quyết định chấp nhận.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Electron chạy chuỗi hợp đồng có đáp án, hai thửa cùng serial, đúng ID UQ, tra địa chỉ ba loại ô và xuất qua hộp thư mục Windows.
- [ ] #2 Ca thiếu trường/nguồn hỏng/truy vấn cũ/mapping sai/hủy/trùng file không đổi nguồn hoặc để file dở.
- [ ] #3 Bản đóng gói ở thư mục mới/app data riêng có đúng kho/catalog/engine và không lồng thư mục sai.
- [ ] #4 Có log test, skip/lỗi môi trường, fixture độc lập, DB migration, nguồn địa chỉ, manifest Word và ảnh trang; parent truy cập được.
- [ ] #5 Parent review phản ví dụ và bộ giữ lại; docs/contract không mâu thuẫn; tầng chưa chạy không được báo nghiệm thu.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

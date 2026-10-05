---
id: TASK-9
title: Chuyen va kiem tung vi tri placeholder trong toan bo mau Word
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
  - notary_v2/word_templates/placeholder_mapping.md
type: task
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
W-02/04: kiểm đủ inventory 22 mẫu được bàn giao, chuyển token cũ sang nghĩa catalog mới theo từng vị trí, không giữ alias rồi báo đã chuyển hết. Q1 phải được chốt. Giữ mẫu gốc, bản sao, manifest và kiểm Word trực quan; đưa bộ được duyệt vào nơi runtime dùng. Chi tiết gói G TASK-2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Có inventory nguồn/hash và mapping từng occurrence token cũ theo Q1; vị trí không rõ nghĩa còn mở, không báo hoàn tất.
- [ ] #2 Bộ mới không còn token legacy ngoài danh sách Owner chủ ý cho phép; phân biệt engine compatibility với mẫu đã chuyển.
- [ ] #3 Nguồn không đổi hash; run bị tách, bảng, header/footer và 5 mẫu .doc có bằng chứng chuyển/xem đúng.
- [ ] #4 Mỗi mẫu xuất đúng người/tài sản theo đáp án độc lập, kể cả đổi thứ tự Stage; định dạng được xem trực quan.
- [ ] #5 Bộ mẫu được duyệt nằm ở nơi runtime thực sự sử dụng, không chỉ artifact ignored.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

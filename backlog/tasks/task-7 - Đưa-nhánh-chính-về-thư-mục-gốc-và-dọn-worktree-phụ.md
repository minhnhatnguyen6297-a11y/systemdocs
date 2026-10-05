---
id: TASK-7
title: Đưa nhánh chính về thư mục gốc và dọn worktree phụ
status: In Progress
assignee:
  - '@codex'
created_date: '2026-10-05 03:26'
labels: []
dependencies: []
type: chore
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Owner yêu cầu D:/systemdocs là nơi làm việc duy nhất sau TASK-6. Cần chuyển dữ liệu local cần dùng, bảo toàn bản sao, đổi nhánh tại root rồi kiểm tra trước khi xóa các checkout phụ.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 D:/systemdocs chạy trên consolidate/monorepo và chứa toàn bộ tài liệu/task đã gom.
- [ ] #2 Dữ liệu local và thay đổi chưa commit ở các nguồn có bản sao kiểm được trước khi dọn.
- [ ] #3 Kiểm tra Git, Backlog, liên kết và các kiểm tra phù hợp tại root đạt; giới hạn kiểm tra được ghi rõ.
- [ ] #4 Các worktree phụ của systemdocs được dọn; Git chỉ còn checkout gốc, có bàn giao và commit.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Kiểm kê lại và sao lưu đủ dữ liệu local của các checkout. 2. Giữ trạng thái làm dở ở root, chuyển dữ liệu local và đưa root về nhánh chính. 3. Kiểm tra tài liệu, task và khả năng chạy kiểm tra ở root. 4. Sau khi đạt, dọn đúng các worktree phụ đã sao lưu. 5. Ghi quyết định, kết quả và commit.
<!-- SECTION:PLAN:END -->

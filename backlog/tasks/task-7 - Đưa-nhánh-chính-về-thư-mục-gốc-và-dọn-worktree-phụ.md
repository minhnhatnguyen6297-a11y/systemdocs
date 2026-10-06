---
id: TASK-7
title: Đưa nhánh chính về thư mục gốc và dọn worktree phụ
status: Done
assignee:
  - '@codex'
created_date: '2026-10-05 03:26'
updated_date: '2026-10-05 03:48'
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
- [x] #1 D:/systemdocs chạy trên consolidate/monorepo và chứa toàn bộ tài liệu/task đã gom.
- [x] #2 Dữ liệu local và thay đổi chưa commit ở các nguồn có bản sao kiểm được trước khi dọn.
- [x] #3 Kiểm tra Git, Backlog, liên kết và các kiểm tra phù hợp tại root đạt; giới hạn kiểm tra được ghi rõ.
- [x] #4 Các worktree phụ của systemdocs được dọn; Git chỉ còn checkout gốc, có bàn giao và commit.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [x] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [x] #3 Tests pass
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Kiểm kê lại và sao lưu đủ dữ liệu local của các checkout. 2. Giữ trạng thái làm dở ở root, chuyển dữ liệu local và đưa root về nhánh chính. 3. Kiểm tra tài liệu, task và khả năng chạy kiểm tra ở root. 4. Sau khi đạt, dọn đúng các worktree phụ đã sao lưu. 5. Ghi quyết định, kết quả và commit.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Root D:/systemdocs ở consolidate/monorepo. Có ZIP 33850 file, ZIP bổ sung 31 file, SHA-256 và CRC đạt; backup private copy khớp; 20 mẫu hash khớp. Git chỉ còn root; worktree trung gian và Orca đã xóa. Worktree 1aae hết file, vỏ thư mục rỗng còn bị phiên giữ (WinError 32), ghi cách xóa không đệ quy sau khi đóng phiên. Kiểm tra: Backlog doctor, links, 82 contract examples; shell 382 pass; Python 389 pass/2 skip. Runtime không đổi so với 8a7d8bf; chưa nghiệm thu chức năng mới. Quyết định decision-21, chỉ mục spec cập nhật nơi tiếp tục. TASK-3/4/5 giữ trạng thái. Xem .agents/handoff/worktree-consolidation-20261005/root-verification.md.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Gom về D:/systemdocs, consolidate/monorepo; sao lưu có kiểm chứng, chỉ còn một checkout Git. Dọn các worktree phụ và Orca; còn vỏ 1aae/systemdocs rỗng bị phiên khóa. Tài liệu và test tại root đạt trong phạm vi đã ghi; không triển khai runtime, chưa push.
<!-- SECTION:FINAL_SUMMARY:END -->

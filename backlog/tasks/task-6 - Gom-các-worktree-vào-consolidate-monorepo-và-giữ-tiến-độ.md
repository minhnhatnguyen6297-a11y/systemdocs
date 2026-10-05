---
id: TASK-6
title: Gom các worktree vào consolidate/monorepo và giữ tiến độ
status: Done
assignee:
  - '@codex'
created_date: '2026-10-05 02:55'
updated_date: '2026-10-05 03:13'
labels: []
dependencies: []
references:
  - .agents/handoff/worktree-consolidation-20261005/README.md
  - .agents/handoff/notary-20261005/README.md
type: chore
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Owner yêu cầu gom tài liệu regex và địa chỉ cùng phần làm dở trên máy vào nhánh chính. Worktree 1aae mất metadata; cần giữ bản sao và đối chiếu, không triển khai runtime.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Kiểm kê commit và file chưa commit, có bản sao phục hồi.
- [x] #2 Spec, task, plan và tham chiếu regex/địa chỉ cùng ở nhánh chính; phân biệt đã duyệt và còn chờ.
- [x] #3 Thay đổi ngoài hai luồng được đối chiếu và ghi rõ đã nhận hoặc giữ lại; nguồn cũ được giữ.
- [x] #4 Nhánh nhận có commit, kiểm liên kết và báo cáo trạng thái từng việc.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [x] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [x] #3 Tests pass
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Sao lưu và kiểm kê. 2. Tạo checkout sạch của nhánh chính. 3. Gom tài liệu theo từng nhóm và hoàn thiện bàn giao đang dở. 4. Kiểm liên kết, task và commit. 5. Ghi trạng thái cuối, giữ nguồn cũ.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Kiểm kê: tất cả nhánh local đã là tổ tiên main tại 8a7d8bf; phần cần nhận là tài liệu/task chưa commit. Backup zip + bundle đã giữ ở cả nguồn 1aae và checkout mới, bundle verify PASS. Đã kiểm toàn bộ Orca/workspaces và metadata phiên: bốn thư mục cũ không còn source; đường dẫn còn là D:/systemdocs. Nhận tài liệu regex, audit, task5, review/progress địa chỉ và docs tổng quan; giữ nguyên code runtime, trạng thái TASK-3/4/5, nguồn gốc và các xóa BMAD chưa rõ ý định ở root.

Kiểm cuối PASS: 34 Markdown/206 local links, 0 missing; 18 snapshot spec/plan đã rút được giữ nguyên ngữ cảnh lịch sử, không thuộc cây spec hoạt động. Backlog doctor PASS. Hai zip kiểm CRC PASS và bundle Git verify PASS. Đối chiếu 135 file nguồn theo SHA-256: không thay đổi; runtime diff so 8a7d8bf rỗng. Diff whitespace PASS với ngoại lệ dòng trống EOF của mẫu decision do CLI sinh. Commit riêng dcc2d06 (regex/audit), e1fded2 (review/progress địa chỉ); phần tổng quan/kiểm kê vào commit kết thúc TASK-6. Không chạy lại engine hoặc nghiệm thu chức năng trong task gom docs.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Đã gom tài liệu và tiến độ trên consolidate/monorepo, giữ nguồn/backup và trạng thái duyệt. Regex: bảng quy tắc 20 mẫu + TASK-5 chờ duyệt; địa chỉ: spec/contract đã duyệt, TASK-3 In Progress và TASK-4 To Do. Đã kiểm cây Orca và metadata phiên, không tìm thêm checkout còn source. Bàn giao: .agents/handoff/notary-20261005/README.md; kiểm kê/phục hồi: .agents/handoff/worktree-consolidation-20261005/README.md. Checks: links, Backlog doctor, zip CRC, bundle verify, SHA-256 nguồn và runtime diff đều PASS. Không triển khai runtime, không xóa worktree nguồn, không push.
<!-- SECTION:FINAL_SUMMARY:END -->

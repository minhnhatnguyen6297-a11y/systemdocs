---
id: TASK-10.1
title: Chuẩn hóa đáp án trích Word và nguồn quy tắc từng trường
status: Done
assignee:
  - '@codex'
created_date: '2026-10-07 03:45'
updated_date: '2026-10-07 14:31'
labels:
  - regex
  - spec
  - expected-results
dependencies: []
references:
  - .agents/review-sweep-20261007/report.md
  - .agents/review-viewpoint-20261007/assessment.md
  - docs/spec/upload_lab/regex-fields.md
  - docs/spec/upload_lab/regex-expected-results.md
parent_task_id: TASK-10
type: enhancement
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Owner giao triển khai sau review: kiểm từng trường; quy tắc rải và mâu thuẫn giữa catalog/spec loại. Bộ đáp án có nguồn, một nơi sở hữu quy tắc; F01/F04/F05 chờ quyết định. Sửa lỗi thực hiện sai luật đã rõ, không tự port lõi, không commit/push.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Mỗi lỗi có đầu vào, trường đích, cảnh báo và trạng thái đã chốt/chờ quyết định; F01/F04/F05 chưa được tính đạt
- [x] #2 Quy tắc trường có một nguồn trong docs/spec; catalog/spec loại dẫn tới đó, giữ ngoại lệ, nguồn và điểm mở
- [x] #3 Lỗi đã rõ có kiểm qua hàm thật cả hai engine; bỏ hỗ trợ làm test liên quan thất bại
- [x] #4 Mẫu Word thật có nguồn và kiểm từng trường; không dùng số cờ R để kết luận dữ liệu đúng
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [x] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [x] #3 Tests pass
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Bảng nguồn/đáp án và quyết định mở. 2. regex-fields.md và liên kết spec; giữ thay đổi owner. 3. Sửa nhánh đã rõ, test thật, mirror. 4. Hai suite, phép bỏ hỗ trợ trong bộ nhớ, Word và liên kết. 5. Decision, giới hạn, task.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Đã lập regex-fields.md và regex-expected-results.md trước code; catalog/spec loại dẫn tới một nguồn trường; F01/F04/F05 pending. Giữ nguyên 6 dòng owner trong regex-core. Đã tạo decision-73. Reader độc lập đọc Word s283, lập 4 người/7 trường trước output máy. Implementer đang sửa phần closed.

Review độc lập thấy test đất ghi đè payload; native .doc làm mất ô trống; các biến thể bảng thiếu/ngược cột còn chưa phủ; guard năm/birth và nhãn dài/prose cần bổ sung. Sửa trong phạm vi luật closed, giữ F01/F04/F05. Triage .agents/task-10.1/review-triage.md.

Kiểm cuối sau sửa review: Upload Lab full406 passed2 skipped51 subtests; tool full196 passed1 skipped17 subtests. 22 ca closed unittest mỗi engine;16/16 bỏ hỗ trợ bị bắt, không lỗi chạy. Word thật4 ngườix7 trường mỗi engine,28/28 khớp;giữ R13.65 links/anchors đạt;edit owner giữ nguyên;engine/validator/fixture byte-equal;F01/F04/F05 code giữ nguyên. Skipped:markitdown và mẫu thế vị;không gọi đạt. RESULT và final-verification.json trong .agents/task-10.1.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Đã tập trung luật từng trường và đáp án Closed/Pending; sửa nhánh đọc đã rõ, test native payload và mirror. Bằng chứng: .agents/task-10.1/RESULT.md, final-verification.json, XML suite và verification-fields.json. F01/F04/F05 vẫn chờ;không quét lại toàn corpus,approve Golden,commit hoặc push.
<!-- SECTION:FINAL_SUMMARY:END -->

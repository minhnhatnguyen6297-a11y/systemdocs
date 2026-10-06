---
id: TASK-6
title: Sua trich hop dong DOCX du Nguoi Tai san va bang chung
status: To Do
assignee: []
created_date: '2026-10-04 15:40'
updated_date: '2026-10-04 16:25'
labels:
  - notary
  - repair
dependencies:
  - TASK-11
references:
  - .agents/review-plan-20261004/investigation-report.md
  - backlog/tasks/task-2 - Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md
  - docs/spec/notary_v2/input/docx-import.md
  - docs/spec/notary_v2/stage.md
  - docs/spec/notary_v2/input/document-extraction.md
  - >-
    backlog/tasks/task-11 -
    Xay-lai-engine-trich-van-ban-theo-cau-truc-va-rule-dung-chung.md
type: bug
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Tích hợp engine trích mới TASK-11 vào DOCX và Stage. Phần nhận loại/chia vùng/rules/bộ chấm được tách sang task engine theo yêu cầu Owner; TASK-6 giữ reader ZIP/XML, bản đồ bằng chứng, adapter/normalizer, dialog và save/reload. Cần sửa RE-05 AlternateContent và TS-03 bỏ tổng diện tích, giữ số bản ghi/giá trị engine đã chấm khi đi vào Stage. Không tạo một bộ regex riêng trong adapter.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Reader DOCX giữ đúng chữ/thứ tự đoạn-bảng lồng/vị trí nguồn, chọn một biểu diễn AlternateContent; không thành hai người hoặc dedup người theo tên.
- [ ] #2 Adapter dùng bộ nhận diện/định tuyến engine mới của TASK-11, không luôn load transfer và không sao chép rules; trace nguồn/rule/profile/vùng được giữ trong gợi ý theo contract.
- [ ] #3 Mẫu có đáp án 3 người/1 tài sản giữ đúng 3/1 và giá trị qua adapter-dialog-Stage-commit-reload; mỗi thửa riêng, cùng sổ cùng serial.
- [ ] #4 Normalizer giữ serial free text và tổng diện tích độc lập khi có land_rows; thiếu giấy tờ không xóa người rõ tên, không bịa để vượt Stage.
- [ ] #5 Không nhận loại, lỗi rule hoặc vùng/bản ghi mơ hồ hiện đúng phạm vi; không ghi nhận trích đầy đủ thành công khi còn thiếu dữ liệu nguồn.
- [ ] #6 Source_refs/hash/context/binding đúng qua sửa/reorder/xóa và mở lại; kiểm bộ giữ lại độc lập của engine qua đường DOCX thật, tách lỗi reader/engine/adapter.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

---
id: TASK-3
title: Sua Stage tai san serial tu do va dien tich tong
status: To Do
assignee: []
created_date: '2026-10-04 15:40'
updated_date: '2026-10-04 16:19'
labels:
  - notary
  - repair
dependencies: []
references:
  - .agents/review-plan-20261004/investigation-report.md
  - backlog/tasks/task-2 - Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md
  - docs/spec/notary_v2/stage.md
type: bug
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TS-01/02/03; Owner đã chốt 5 trường bắt buộc, serial tự do/optional và mỗi thửa một tài sản, cùng sổ cùng serial. Sửa trọn UI-wire-snapshot-DB-save-reload; bỏ serial giả và liên kết chỉ theo serial. DB migration cho serial null/non-unique phải giữ dữ liệu. Chi tiết gói A trong TASK-2; chưa implement ở phiên review.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Chỉ địa chỉ, thửa, tờ, tổng diện tích và loại đất bắt buộc; thiếu từng mục báo đúng dòng/ô.
- [ ] #2 Serial null hoặc 1234/X-2020 không bị đổi/sinh giả qua đọc-lưu-mở lại; schema/client/server thống nhất.
- [ ] #3 Hai thửa cùng serial lưu thành hai entity riêng, reorder/reload giữ định danh; không tự .first() liên kết theo serial.
- [ ] #4 DB cũ chuyển serial nullable/non-unique không mất ID, giá trị, liên kết; kiểm trên bản sao.
- [ ] #5 Diện tích tổng 300 và dòng loại đất 100 giữ riêng xuyên Stage/save/reload; không ghi đè nguồn. Điền Word được kiểm tại TASK-8/TASK-10 để không tạo phụ thuộc vòng.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

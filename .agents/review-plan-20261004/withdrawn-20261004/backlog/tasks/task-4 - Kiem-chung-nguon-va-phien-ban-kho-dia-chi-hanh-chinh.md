---
id: TASK-4
title: Kiem chung nguon va phien ban kho dia chi hanh chinh
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
  - docs/spec/notary_v2/administrative-timeline.md
  - docs/spec/notary_v2/administrative-address.md
type: task
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
DC-06/08: phân biệt danh mục/câu nguồn Bando với lịch sử có ngày được xác nhận; bổ sung nguồn chính thức và báo phạm vi dữ liệu. Sửa A→B→A trả tên sai phiên bản. Giữ kho hiện có, không dựng hệ mới. Chi tiết gói B TASK-2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tên/cha/evidence trả về đúng dataset_version đang hoạt động; A→B→A không lấy tên B.
- [ ] #2 Quan hệ confirmed có nguồn chính thức, ngày hiệu lực, đơn vị trước/sau; quan hệ chưa đủ bằng chứng vẫn pending.
- [ ] #3 Có ca gộp/chia một phần với chứng cứ và kết quả truy vấn; không nâng toàn bộ câu nguồn thành confirmed.
- [ ] #4 Import sai/thiếu/hỏng không đổi kho; giữ lịch sử curator; baseline số lượng đổi phải có nguồn và kiểm đầy đủ.
- [ ] #5 Bàn giao bảng phạm vi toàn quốc/đợt thay đổi đã xác nhận và khoảng trống; không báo đạt khi còn thiếu nguồn.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

---
id: TASK-5
title: Tra dia chi theo cum ten tai Nguoi Dat va Niem yet
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
  - docs/spec/notary_v2/administrative-address.md
type: feature
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
DC-01…05: tra cứu nền bằng cụm tên không đòi tỉnh/ngày, giữ xã/phường/tỉnh, tìm chữ trong chính ô niêm yết. Sửa kết quả tự nay là và đoán cấp bằng ngày. Q3 đang chờ Owner về cách ghi địa chỉ sau Áp dụng; tìm/hiển thị có thể làm trước. Chi tiết gói C TASK-2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Gõ xã Yên Bình không có tỉnh/ngày trả danh sách đúng cấp, tên cũ/mới và tỉnh/nguồn phân biệt.
- [ ] #2 Địa chỉ hiện hành được nhận biết, không nối nay là chính nó; không suy cấp địa chỉ chỉ bằng ngày giấy tờ.
- [ ] #3 Người/Đất/Niêm yết tìm chữ đang nhập; Niêm yết không buộc có tài sản.
- [ ] #4 Response cũ khi sửa chữ/đổi hồ sơ bị bỏ; lookup không tự ghi/save và không khóa nhập khi lỗi.
- [ ] #5 Q3 phải được ghi decision/spec trước triển khai Áp dụng; giữ thôn/số nhà, không tự chọn quan hệ một phần.
- [ ] #6 Người sống có nơi cấp Bộ Công an không nhận nhãn/lời nhắc giấy khai tử; ngữ cảnh người chết giữ đúng bằng chứng và giá trị nơi cấp.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

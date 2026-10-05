---
id: TASK-11
title: Xay lai engine trich van ban theo cau truc va rule dung chung
status: To Do
assignee: []
created_date: '2026-10-04 16:19'
labels:
  - notary
  - regex
  - rebuild
dependencies: []
references:
  - docs/spec/notary_v2/input/document-extraction.md
  - tools/regex_workbench/README.md
  - .agents/review-plan-20261004/investigation-report.md
  - backlog/tasks/task-2 - Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md
type: feature
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Owner yêu cầu làm lại chiến lược trích thay vì vá từng mẫu: sẽ liệt kê khoảng 30 loại văn bản, dự kiến khoảng 10 nhóm cấu trúc. Engine phải nhận loại/cấu trúc trước, chia vùng và dùng các quy tắc vùng/trường có biến thể, định tuyến và dự phòng rõ. Mẫu thật/đáp án và tiêu chí thành công là điều kiện trước khi mở rộng. Code hiện có chia vùng nhưng adapter luôn chọn transfer, chưa chứng minh bao phủ. Task này sở hữu lõi/rules/bộ chấm; TASK-6 sở hữu reader DOCX/bằng chứng/adapter/Stage. Chưa implement trong phiên lập task; chờ Owner cung cấp danh mục và vị trí mẫu để chốt ma trận loại-nhóm-mẫu.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Danh mục Owner được đối chiếu mẫu: mỗi loại có nhóm cấu trúc, vùng/trường, mẫu/đáp án hoặc nhãn thiếu mẫu; khoảng 30 loại/10 nhóm không bị coi là số đã chốt.
- [ ] #2 Loại văn bản, nhóm cấu trúc và quy tắc vùng/trường tách rõ; ít nhất hai loại có mẫu chứng minh dùng chung một vùng/rule, không chép 30 engine.
- [ ] #3 Nhận diện dùng dấu hiệu/loại trừ/ranh giới cấu trúc; nhiều kết quả phù hợp hoặc không biết loại được báo rõ, không chọn cấu hình đầu tiên hay luôn transfer.
- [ ] #4 Các biến thể ông A, ông: A, ông/bà A, ông/bà: A, đánh số/bảng/xuống dòng và ca âm ngày chết/địa chỉ/lời chứng có đáp án đúng và test.
- [ ] #5 Dự phòng có phạm vi và thứ tự rõ, có trace rule/version/vùng/nguồn; không quét toàn file bằng mọi regex; lỗi/timeout không bị nuốt thành missing.
- [ ] #6 Bộ có đáp án chốt cho nghiệm thu trả đúng loại/vùng, số Người/Tài sản, giá trị và người/thửa chứa trường; không bản ghi giả; mỗi thửa riêng, cùng sổ cùng serial, tổng diện tích giữ riêng.
- [ ] #7 Bộ giữ lại độc lập và các ca biến thể có báo cáo theo loại/nhóm/trường: đúng, sai, bỏ sót, mơ hồ, đạt toàn bộ, thời gian/lỗi; partial không tính thành công đầy đủ.
- [ ] #8 Bàn giao hợp đồng đầu vào chữ/layout và đầu ra có bằng chứng cho TASK-6, cấu hình có phiên bản, fixture/đáp án và giới hạn đã hỗ trợ; chưa có đủ danh mục/mẫu thì không báo phủ đủ 30 loại.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

---
id: TASK-5
title: Duyệt bộ quy tắc trích Word từ mẫu và chốt spec triển khai
status: To Do
assignee: []
created_date: '2026-10-05 02:30'
updated_date: '2026-10-05 03:03'
labels:
  - word-intake
  - rules
  - owner-review
dependencies: []
references:
  - .agents/handoff/notary-20261005/README.md
  - .agents/review/sample-rules-20261005/README.md
  - .agents/review/field-recognition-20261005.md
  - .agents/review/external-rules/parent-summary.md
  - .agents/brainstorming/brainstorm-trich-van-ban-2026-10-04/.memlog.md
  - docs/spec/notary_v2/input/docx-import.md
  - docs/spec/notary_v2/stage.md
  - contracts/notary-case-drafting.md
type: spike
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Bộ regex hiện tại chưa chứng minh trích đủ, đúng Người và tài sản trên hồ sơ thật. Owner yêu cầu nhận cấu trúc, chia vùng, xác định đầu/cuối từng bản ghi và dùng chung quy tắc trường; đã có dàn ý 13 hạng mục và bảng dấu hiệu trên 20 mẫu S01–S20. Task này dành cho bước tiếp tục duyệt/chốt sau khi merge vào nhánh chính; chưa giao triển khai engine.

Nguồn bắt đầu: .agents/handoff/notary-20261005/README.md; .agents/review/sample-rules-20261005/README.md. Brainstorming hỏi–đáp đã tạm dừng; không hỏi lại những quyết định đã chốt. Bảng quy tắc/đáp án đọc tay vẫn chờ Owner duyệt, không dùng số test xanh hoặc số ô được điền để khẳng định chính xác.

Quyết định đã chốt: đọc từng file riêng; bỏ CCV/người làm chứng; không tìm bù/xác nhận từ vùng ký/lời chứng kèm hoặc file khác; lời chứng độc lập có vùng Người chính riêng; record thiếu vẫn trả; kết quả trích chỉ đọc, chọn từng dòng vào Stage và sửa ở Stage; một Người có nhiều bản giấy, chỉ liên kết CMND 9 số với căn cước 12 số khi nguồn ghi rõ; mỗi thửa một tài sản, serial tùy nguồn/optional/có thể trùng; tổng diện tích độc lập; tên ngân hàng nguyên cụm JSON; xe/tàu chưa hỗ trợ. Lớp đánh giá chỉ báo kết quả, không tự thử lại/học; Owner đã giải thích 'sai format' là loại văn bản chưa hỗ trợ, không phải lỗi định dạng giá trị trường.

Còn mở: tên dẫn chiếu/khối lặp trong vùng chính; cán bộ trong biên bản; nhiều văn bản/một file; nhiều giá trị nguồn/một ô Stage; chỗ lưu ngân hàng; UX nhiều phiên bản giấy; thuật toán đánh giá cuối. Không tự chốt các mục này.

Spec đang dùng là docs/spec/notary_v2/input/docx-import.md và stage.md; chưa có spec mới cho toàn bộ engine nhận nhiều cấu trúc. Plan/spec sửa cũ đã rút, nằm ở .agents/review-plan-20261004/withdrawn-20261004/ và backlog/archive/tasks; không sử dụng để triển khai. TASK-3/TASK-4 đang hoạt động là tra cứu hành chính, không phải task trích xuất.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Owner duyệt dấu hiệu loại/vùng và đầu-cuối từng Người/thửa/giấy trên mẫu cụ thể; biến thể chưa có mẫu và điểm chưa chốt được phân biệt rõ.
- [ ] #2 Bộ đáp án từng vùng/từng trường được duyệt, gồm dữ liệu thiếu, nhiều giấy, GCN chung, tên lặp và ví dụ không được nhận; chưa chấm tổng dòng ở các mục nghiệp vụ còn mở.
- [ ] #3 Các quyết định đã duyệt được ghi vào spec phù hợp và Backlog decisions, có QUYẾT ĐỊNH và TẠI SAO; giải quyết khác biệt với spec/contract Stage và DOCX hiện tại trước code.
- [ ] #4 Sau khi có spec đã duyệt, lập task/plan triển khai riêng cho engine và tích hợp Stage; nêu cách kiểm trên bộ mẫu, agent implement và parent review cuối. Task này không tự chuyển sang sửa runtime.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
05/10/2026: Đã gom bảng quy tắc 20 mẫu, dấu hiệu 56 nhóm, memlog, báo cáo tham khảo và bàn giao vào consolidate/monorepo. Xem .agents/handoff/notary-20261005/README.md. Spec triển khai engine mới còn chờ duyệt; task giữ To Do, không giao code. Bản đáp án chứa dữ liệu cá nhân giữ local-only; Git có chỉ mục/manifest và ghi chú quy tắc.
<!-- SECTION:NOTES:END -->

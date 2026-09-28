---
title: 'Giữ quyết định cùng lý do và nguồn gốc'
type: 'feature'
ticket: 'MIN-134'
created: '2026-09-28'
baseline_revision: 'cc37cd65c301b22e28d7c5e6f6f000c27565396c'
status: 'built'
route: 'oneshot'
route_source: 'auto'
review: 'quick'
review_source: 'auto'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="owner intent from conversation 2026-09-28">

## Intent

**Problem:** Quyết định nằm rải rác trong Linear, task, spec và tài liệu kiến trúc; lời giải thích nghiệp vụ của owner dễ mất hoặc bị tóm tắt thành một kết luận không còn lý do.

**Approach:** Đặt bản đồ nơi tra cứu và quy tắc ghi quyết định dài hạn trong `docs/architecture/`; mở rộng mẫu quyết định task để giữ lời giải thích gốc, nguồn và trạng thái. Dẫn từ README/AGENTS và minh họa bằng quyết định đã có nguồn.

</frozen-after-approval>

## Implementation Notes

Plan đặt trong `.agent/tasks/MIN-134/` theo AGENTS.md; BMad output mặc định không là nơi lưu task của repo. Baseline `cc37cd65c301b22e28d7c5e6f6f000c27565396c`.

- Thêm `docs/architecture/KNOWLEDGE.md`: bản đồ SOT, quy tắc giữ lời gốc và mẫu quyết định; ví dụ B1 chỉ dẫn nguồn cũ thay vì nhân bản nội dung.
- Thêm lối vào ở `README.md` và quy tắc ngắn ở `AGENTS.md`; mở rộng `.agent/templates/decisions.md`.
- Giữ kinh nghiệm chưa thành quyết định ở issue/comment với trạng thái `Chưa chốt` để không bị nâng thành quy tắc đã duyệt.
- Một task khác tạo `.agent/tasks/MIN-133/w4-shots/` trong lúc làm; không đưa vào MIN-134.

## Plan Change Log

## Review Triage Log

- Quick review: 1 phát hiện `medium` tại `.agent/tasks/MIN-134/` — thiếu `handoff.md` theo AGENTS.md. Đã thêm file bàn giao cùng trạng thái, cách verify và việc còn lại; không còn thiếu file task bắt buộc.

## Verification

- Kiểm tra mọi link tương đối trong tài liệu mới trỏ tới file thật.
- `git diff --check` không báo lỗi khoảng trắng.
- Đối chiếu ví dụ với nguồn gốc và trạng thái hiện có; không suy diễn lý do.

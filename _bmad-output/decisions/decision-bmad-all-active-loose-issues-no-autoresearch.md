---
id: decision-bmad-all-active-loose-issues-no-autoresearch
title: Triển khai mọi issue còn hiệu lực bằng BMAD, không dùng Autoresearch
date: '2026-10-15'
status: accepted
---

## Quyết định quy trình

Owner yêu cầu nguyên văn:

> Tiếp tục BMAD triển khai toàn bộ issues còn hiệu lực theo thứ tự trong backlog, bắt đầu #28. Không dùng Autoresearch. Thiếu quyết định nghiệp vụ thì dừng hỏi tôi.

Giữ ticket rời trong `_bmad-output/backlog/`, mỗi issue có plan riêng và triển khai tuần tự theo thứ tự đã có: bắt đầu #28, rồi #4, #6, #7, #5, #17 và các issue còn hiệu lực tiếp theo trong backlog. Không thực thi #1 (tracking-only) hoặc #11/#26 (dropped). Không tạo initiative, đổi config hay hỏi lại lựa chọn phạm vi/thứ tự đã chốt.

Autoresearch bị tắt theo yêu cầu này: không khởi tạo experiment, không gọi init/run/log/notes, không coi thiếu `init_experiment` là điều kiện chặn BMAD. Chỉ bỏ hai scaffold chưa commit do workstream tạo (`autoresearch.sh`, `autoresearch_benchmark.py`); giữ bằng chứng baseline lịch sử dưới `_bmad-output/tmp/issue-28-implementation/`.

## Ranh giới

Đây là quyền tiếp tục quy trình, không phải tuyên bố plan đã được duyệt tại checkpoint hoặc runtime đã implement/nghiệm thu. BMAD giữ route/checkpoint/review và kiểm chứng riêng cho từng issue; với #28, smoke app/engine thật trên fixture cục bộ, browser cô lập vẫn bắt buộc trước review/complete theo plan chuẩn. Nếu phát sinh quyết định nghiệp vụ thực sự còn thiếu, dừng và hỏi owner; không tự chọn thay.

Quyết định này cập nhật phần phạm vi/thứ tự hiện hành của [quyết định ticket rời trước](decision-p1-sequential-loose-tickets.md), không xóa lịch sử. [Quyết định SOT Upload](decision-upload-web-sot-without-save-tracking.md) tiếp tục là nguồn hành vi #28; [plan chuẩn #28](../backlog/story-upload-web-official-sot-cutover-plan.md) vẫn giữ trạng thái thực tế của nó.

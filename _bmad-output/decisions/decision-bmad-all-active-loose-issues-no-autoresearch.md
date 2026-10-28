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

Owner đã phê duyệt bản plan #28 hiện tại để triển khai; phạm vi phê duyệt không bao gồm quyết định nghiệp vụ chưa nêu hoặc các plan issue tiếp theo. Nếu gặp lựa chọn ảnh hưởng hành vi còn thiếu, dừng và hỏi owner.

Quyết định này cập nhật phần phạm vi/thứ tự hiện hành của [quyết định ticket rời trước](decision-p1-sequential-loose-tickets.md), không xóa lịch sử. [Quyết định SOT Upload](decision-upload-web-sot-without-save-tracking.md) tiếp tục là nguồn hành vi #28; [plan chuẩn #28](../backlog/story-upload-web-official-sot-cutover-plan.md) vẫn giữ trạng thái thực tế của nó.

## Phê duyệt plan #28

Owner, 2026-10-15:

> “duyệt, triển khai”

Áp dụng cho plan #28 hiện tại; không phê duyệt trước quyết định nghiệp vụ chưa nêu hay plan tương lai.

## Phê duyệt plan #4

Owner, 2026-10-16:

> “trien khai”

Áp dụng riêng cho plan #4 hiện tại đã được trình bày; không phê duyệt trước quyết định nghiệp vụ chưa nêu hoặc bất kỳ plan issue tương lai nào.
## Cập nhật chỉ đạo của owner — 2026-10-16

Chỉ đạo owner, nguyên văn:

> “trien khai lien tuc, khong can duyet plan, chi dung lai khi can hoi”

Với các issue còn hiệu lực theo thứ tự backlog đã duyệt, chỉ đạo này thay thế yêu cầu duyệt riêng từng plan: sau khi đã rà hết bằng chứng repository/spec và semantics nghiệp vụ đã chốt, tự động chuyển từ lập plan sang triển khai, không dừng chờ duyệt plan. Chỉ dừng khi vẫn còn một quyết định nghiệp vụ thực sự chưa được giải đáp sau khi đã khai thác bằng chứng sẵn có trong repo. Không thêm tính năng ngoài backlog hiện có, đổi thứ tự/loại trừ đã chốt, tạo initiative hoặc dùng spike để tự suy ra câu trả lời nghiệp vụ.

Tiếp tục duy trì plan và đánh giá rủi ro cho từng issue; triển khai tuần tự, mỗi thời điểm chỉ một người phụ trách implementation; chạy test/smoke hành vi phù hợp trước review; giữ review Quick độc lập và commit đúng phạm vi. Waiver chỉ bỏ checkpoint duyệt riêng từng plan; giữ nguyên quyền thực thi/handoff của adaptive-coding-flow, kiểm chứng và review. Không chạy luồng song song, Autoresearch, thay config hoặc skill override. #6 được triển khai trước, với một người phụ trách triển khai. Tracker #6 vẫn `refined: false`; chỉ đạo này không âm thầm nâng spec thành đã refined.

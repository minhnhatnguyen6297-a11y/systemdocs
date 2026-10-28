# BMAD sở hữu coding loop; orchestration chưa chốt

> **Bị thay bởi [decision-81](decision-81%20-%20Bo-BMAD-thu-Superpowers-docs-chuyen-sang-docs.md) (28/10/2026).** Giữ để tra lịch sử.

Ngày: 2026-10-12

## Quyết định của user

- Tập trung làm tốt phần BMAD: agent phải biết đang ở bước nào, làm gì tiếp và tự thực hiện đủ coding loop, không chờ user nhắc test/review.
- Chưa chốt orchestration do OMP phụ trách. Không coi OMP, Orca hoặc một topology worker cụ thể là quyết định cuối cùng của phiên này.
- Giữ cấu trúc HTML Plan Thariq đã chốt.

## Vì sao

Nhu cầu daily tối thiểu là workflow kỹ thuật ổn định cho solo-vibecoder. Chọn công cụ điều phối và chuyển agent là vấn đề riêng, không phải điều kiện để xác định trình tự và điều kiện hoàn tất của BMAD.

## Phạm vi áp dụng

- Bổ sung quyết định `decision-daily-coding-loop-auto-test-review.md` và `decision-clear-intent-no-plan-approval.md`.
- Các quyết định/override transport đã tồn tại là cấu hình hiện trạng, không phải orchestration mới được user xác nhận. Chưa xóa hoặc thay chúng trong bước khảo sát này.
- Dựa vào step files, state và customization được BMAD hiện tại hỗ trợ; không dựng bộ luật hoặc task-state engine song song.
- Đây là quyết định scope; chưa sửa spec/override/installed skills.

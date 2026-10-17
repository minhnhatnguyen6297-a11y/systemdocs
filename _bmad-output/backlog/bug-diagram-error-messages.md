---
id: 4
type: bug
title: "Sơ đồ không hiển thị đúng thông báo khi gặp lỗi"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: medium
severity: P2
---

# Sơ đồ không hiển thị đúng thông báo khi gặp lỗi

## Description

Lỗi binding formatter đã có bằng chứng làm hỏng hiển thị lỗi khi đánh giá, dựng danh sách lỗi và lưu sơ đồ. Chuyên viên cần đọc được lỗi thực và tiếp tục dùng hồ sơ/bản nháp.

## Reproduction

Probe lịch sử nạp catalog lỗi thật trước Diagram, gây lỗi evaluate, dựng diagramErrors và lưu thông thường. Cả ba ghi TypeError: relErrText is not a function thay thông báo. Xem plan/bằng chứng đã dẫn; không chạy lại chỉ để xác nhận lỗi đã báo.

## Cause Hypothesis

Binding formatter khi nạp browser có thể trỏ tên export không tồn tại trong catalog thật; nhánh fallback khi nạp riêng che mất sai khác.

## Acceptance Criteria

1. **Hiện lỗi thực**
   **Given** evaluate hoặc lưu thông thường trả lỗi
   **When** chuyên viên đánh giá, xem danh sách lỗi hoặc lưu
   **Then** thấy lỗi dễ đọc đúng ngữ cảnh, không exception formatter, state/nháp cũ còn dùng được
2. **Giữ ngoại lệ**
   **Given** xung đột, invalid state hoặc lưu thành công
   **When** chuyên viên thao tác
   **Then** xử lý xung đột/invalid hoặc kết quả lưu đúng như contract
3. **Bằng chứng regression hoặc hành vi hiện có đúng**
   **Given** điều kiện đã ghi và các ca hợp lệ liền kề
   **When** nghiệm thu kết quả cuối
   **Then** bằng chứng theo hành vi phủ điều kiện và các biên đã đổi; hoặc chứng minh phạm vi hành vi không đổi đã đúng với phản ánh chưa xác minh. Không dùng kết luận này để bỏ yêu cầu hành vi mới của owner.

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C03
- source — _bmad-output/specs/notary_v2/diagram-rules.md, §9.7
- source — _bmad-output/implementation-artifacts/plan-diagram-error-fix-20261009.md, Problem, boundaries, evidence

## Notes

- Tracking: C03; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: medium — Hỏng nhánh trình bày lỗi làm người dùng không hiểu thất bại; chưa có bằng chứng bản thân formatter làm hỏng dữ liệu.
- Điểm vào code: shell/src/renderer/notary/relationship-diagram.js:47-49,312,1278,1333; error-catalog.js. Bằng chứng defect và phạm vi nằm trong nguồn đã dẫn; không đóng 12 report mất ghi chú theo lỗi này (issue 12 report lịch sử đã bỏ theo quyết định owner 17/10/2026 — [decision](../decisions/decision-owner-remove-historical-report-issue-20261017.md)).

---
id: 7
type: bug
title: "Regex bỏ sót serial nguyên văn và địa chỉ thửa có nhãn"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: medium
severity: P2
---

# Regex bỏ sót serial nguyên văn và địa chỉ thửa có nhãn

## Description

Fixture qua core/intake đã ghi nhận hai Người và một Tài sản nhưng thiếu TEST-001 và địa chỉ thửa có nhãn. Giá trị nguồn thuộc phạm vi hỗ trợ phải vào đúng ô gợi ý cùng bằng chứng.

## Reproduction

Dùng fixture synthetic-transfer.docx sẵn có. Kết quả core trực tiếp và intake service thật đã ghi so_serial/dia_chi_thua là missing dù nguồn có TEST-001 và nhãn Địa chỉ thửa đất. Đây là quan sát service/core, chưa phải native UI.

## Cause Hypothesis

Profile có vẻ chỉ nhận format serial và câu nhãn địa chỉ hẹp hơn quy tắc field đã được chọn.

## Acceptance Criteria

1. **Hai field có nguồn**
   **Given** fixture chuyển nhượng tổng hợp đã ghi bằng chứng
   **When** phân tích qua consumer intake Notary thật
   **Then** gợi ý tài sản chứa TEST-001 nguyên văn và đúng địa chỉ thửa vào field tương ứng cùng nguồn
2. **Không mượn dữ liệu**
   **Given** nguồn thiếu field, giấy tờ người khác và Lời chứng
   **When** chạy phân tích
   **Then** field thiếu vẫn thiếu, không lấy dữ liệu lân cận/Lời chứng và giữ các nhóm đang hỗ trợ
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
- tracking — _bmad-output/backlog/README.md, C06
- source — _bmad-output/specs/shared/extraction-rules.md, §2.1, §2.6, §6
- source — _bmad-output/tmp/notary-flow-remediation/assessment-plan.md, §2, §6

## Notes

- Tracking: C06; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: medium — Bỏ sót hoặc lấy nhầm serial/địa chỉ làm gợi ý sai; người dùng vẫn có bước kiểm và sửa.
- Fixture/kết quả: _bmad-output/tmp/notary-flow-remediation/runtime-synthetic/. Core: tools/regex_workbench/engine/. Không chờ cutover #22; không mở luật parsing còn Pending.

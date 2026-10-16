---
id: 22
type: story
title: "Dùng lõi regex chung cho các consumer sau khi giữ đủ hành vi"
parent: none
covers: []
after: [7]
assignee: ""
refined: false
hitl: false
risk: high
---

# Dùng lõi regex chung cho các consumer sau khi giữ đủ hành vi

## Description

Hoàn tất hướng core chung đã duyệt cho consumer Notary, Upload và tool nhân viên thực tế. Chứng minh parity phạm vi hỗ trợ trước cutover, bỏ bản extraction/copy cũ sau chuyển, không giữ dual engine lâu dài.

## Acceptance Criteria

1. **Parity consumer**
   **Given** đáp án gán nhãn độc lập cho từng consumer/loại văn bản hỗ trợ
   **When** chạy qua entry point thực
   **Then** field/nhóm/cảnh báo/unsupported/Pending đúng đáp án, gồm serial nguyên văn/năm riêng và không tạo người Lời chứng
2. **Một core có hiệu lực**
   **Given** consumer đã chuyển cùng ranh rule writable/package
   **When** chuyên viên nhập Word/text hoặc dùng tool
   **Then** cùng core/rule identity có hiệu lực, mapping adapter rõ, không chép engine tay hoặc giữ fallback lâu dài
3. **Không giảm coverage âm thầm**
   **Given** nguồn hỗ trợ, file lỗi và ca ngoài phạm vi/Pending
   **When** batch/intake/tool xử lý
   **Then** giữ kết quả nguồn hợp lệ, báo lỗi từng nguồn, Pending không thành Approved chỉ vì có output

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C21
- source — _bmad-output/specs/shared/extraction-rules.md, §1, §5–§8
- source — _bmad-output/specs/notary_v2/word-templates.md, §2.2
- source — _bmad-output/tmp/notary-flow-remediation/assessment-plan.md, §2

## Notes

- Tracking: C21; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Chuyển consumer thiếu parity có thể mất người/thửa/trường đã hỗ trợ trên nhiều luồng.
- Điểm vào code: tools/regex_workbench/engine, upload_lab/extract_contract.py, regex-test-tool/tool, adapter intake Notary và package staging. #7 có thể sửa trước. Issue này sở hữu parity/caller cutover, không sở hữu vòng đời editable rule #8/#23. Không thêm luật parsing/nhánh OCR.
- Sequencing: chờ #7 để tuần tự hóa hai lượt sửa cùng core, không thêm gate nghiệp vụ và không làm #7 chờ full cutover. #23 đã superseded 16/10/2026 theo [quyết định owner](../decisions/decision-owner-regex-rule-developer-only-20261016.md) (rule do developer quản lý; người dùng không dùng tính năng); parity/cutover của issue này không đổi.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

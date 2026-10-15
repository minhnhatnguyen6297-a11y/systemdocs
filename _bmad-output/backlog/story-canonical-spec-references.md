---
id: 16
type: story
title: "Sửa tham chiếu không còn đúng trong spec đang dùng"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: low
---

# Sửa tham chiếu không còn đúng trong spec đang dùng

## Description

Sửa hai tham chiếu canonical đã chỉ ra mà không mở lại yêu cầu archive hoặc đổi hành vi sản phẩm.

## Acceptance Criteria

1. **Đọc đúng nguồn**
   **Given** tham chiếu mapping nguồn Word và nguồn quy tắc extraction
   **When** người đọc lần theo canonical
   **Then** đến section hiện hành tự đủ nghĩa, không đến input/docx-import.md hoặc regex-thua-ke.md đã mất
2. **Giữ ý nghĩa**
   **Given** đoạn spec owner vừa viết
   **When** sửa tham chiếu
   **Then** hành vi/trạng thái duyệt giữ nguyên, nguồn lịch sử vẫn mang nhãn lịch sử

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C15
- source — _bmad-output/specs/notary_v2/word-templates.md, §3.2 source references
- source — _bmad-output/specs/shared/extraction-rules.md, §2.1

## Notes

- Tracking: C15; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: low — Link sai làm đọc nhầm nguồn hoặc không tìm được quy tắc hiện hành.
- Chỉ sửa docs: tìm section hiện hành gần nhất và đổi đúng tham chiếu. Không tuyên bố nghiệm thu runtime.

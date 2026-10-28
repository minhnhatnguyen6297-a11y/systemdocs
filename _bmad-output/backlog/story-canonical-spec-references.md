---
id: 16
type: story
title: "Sửa tham chiếu không còn đúng trong spec đang dùng"
parent: none
covers: []
after: []
assignee: ""
refined: true
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

- Tracking: C15; **built 17/10/2026 — independent Quick CLEAN, parent accepted**. DOC-only: structural resolver **5 PASS / 0 FAIL**; không tuyên bố nghiệm thu runtime. Parent giao DOC oneshot sau khi #15 xuất bản tại `63897daf59937c7aacc0240ab2736e347c77a7dc`. #1 chỉ tracking, không chạy cùng leaf.
- Risk: low — Link sai làm đọc nhầm nguồn hoặc không tìm được quy tắc hiện hành.
- Chỉ sửa docs: tìm section hiện hành gần nhất và đổi đúng tham chiếu. Không tuyên bố nghiệm thu runtime.

### DOC oneshot — todo và bàn giao (17/10/2026)

- [x] Đọc lại đúng hai tham chiếu, các anchor canonical và header lịch sử; không mở lại quy tắc hoặc quyết định.
- [x] Word §3.2 trỏ về §2 `#docx-import`; extraction §2.1 trỏ về §2 `#fields` và §4 `#inheritance`. Hai bản archive được ghi rõ lịch sử, không phải nguồn hiện hành.
- [x] Structural DOC smoke: **5 PASS / 0 FAIL**, resolver kiểm đúng năm link vừa sửa (ba anchor hiện hành, hai file lịch sử), ghi path/fragment/hash và kết quả thực ở `_bmad-output/tmp/issue-16-canonical-references/resolver-output.txt`.
- [x] Parent đã giao **một fresh independent Quick reviewer**: không có actionable findings, **CLEAN accepted**; parent đã đọc scoped diff và actual resolver output trước closeout.
- Bằng chứng/handoff: `_bmad-output/tmp/issue-16-canonical-references/evidence.md`; scoped diff: `_bmad-output/tmp/issue-16-canonical-references/scoped-doc.diff`.
- Giữ nguyên attribution `regex-decision-46`, TASK-5, TASK-9; không đổi literal quy tắc, Draft/Pending hoặc trạng thái duyệt. Không code/app smoke/test thường trực; không tuyên bố nghiệm thu runtime hoặc audit link toàn cục.

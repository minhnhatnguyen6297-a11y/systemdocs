---
id: 5
type: story
title: "Lưu và mở lại sơ đồ hợp lệ còn thiếu dữ liệu"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: high
---

# Lưu và mở lại sơ đồ hợp lệ còn thiếu dữ liệu

## Description

Áp dụng hành vi đã chọn: lưu sơ đồ có cấu trúc hợp lệ nhưng còn thiếu dữ liệu thành bản nháp, chỉ rõ phần thiếu. Không mở quyền lưu invalid hoặc unsupported.

## Acceptance Criteria

1. **Bản nháp incomplete**
   **Given** sơ đồ cấu trúc hợp lệ còn thiếu thông tin
   **When** chuyên viên lưu rồi mở lại
   **Then** quan hệ/metadata còn đủ và phần thiếu được chỉ rõ
2. **Từ chối lưu không an toàn**
   **Given** quan hệ sai, người ngoài Stage hoặc unsupported
   **When** chuyên viên lưu
   **Then** thay đổi bị từ chối, sơ đồ cũ và nháp không mất

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C04
- source — _bmad-output/specs/notary_v2/diagram-rules.md, §9.7–10
- source — _bmad-output/decisions/decision-owner-doc-clarifications-20261015.md, item 6

## Notes

- Tracking: C04; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Lưu hoặc migration sai có thể làm mất quan hệ và metadata sơ đồ đã lưu.
- Chú ý state canonical và projection khi migration; giữ metadata và revision. Không thêm điều kiện chặn Word chỉ vì incomplete.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

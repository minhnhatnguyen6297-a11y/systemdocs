---
id: 6
type: story
title: "Giữ nguyên độ đầy đủ của ngày qua lưu và xuất"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: high
---

# Giữ nguyên độ đầy đủ của ngày qua lưu và xuất

## Description

Khép khoảng lệch với yêu cầu giữ độ đầy đủ của ngày qua nhập, lưu, đọc lại và xuất. Đường chuyển đổi trong code cho thấy rủi ro mất độ chính xác; không gọi đây là hỏng dữ liệu production đã được chứng minh.

## Acceptance Criteria

1. **Ngày giữ độ đầy đủ**
   **Given** hai Người giả lập, một chỉ năm và một đúng ngày 01/01
   **When** chuyên viên lưu, mở lại, sửa trường khác rồi xuất trường ngày được hỗ trợ
   **Then** giá trị chỉ năm vẫn chỉ năm, phân biệt được với ngày 01/01 đầy đủ
2. **Nguồn còn nguyên**
   **Given** ngày chưa đầy đủ và ngày đầy đủ sai lịch từ intake
   **When** chuyên viên xem gợi ý
   **Then** raw còn nguyên, không đệm ngày cho năm riêng và không cắt ngày sai thành năm để che lỗi

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C05
- source — _bmad-output/specs/README.md, §6
- source — contracts/entities.md, §8.1
- source — _bmad-output/specs/notary_v2/README.md, §4

## Notes

- Tracking: C05; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Đổi năm riêng thành ngày đầy đủ có thể tạo dữ kiện sai trong hồ sơ và Word.
- Điểm vào code: notary_v2/services/case_workspace.py:184-210,1281-1306,1757-1764,2410-2413. Refinement chọn cách lưu/migration; việc giữ năm riêng đã được chốt, không hỏi duyệt lại.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

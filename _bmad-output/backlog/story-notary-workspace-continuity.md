---
id: 2
type: story
title: "Không gian Stage, Pool và Diagram liền mạch, dễ thao tác"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: medium
---

# Không gian Stage, Pool và Diagram liền mạch, dễ thao tác

## Description

Thực hiện sáu cải thiện workspace đã báo: phân biệt địa chỉ với nơi cấp giấy tờ, mở rộng vùng thao tác Pool/Sơ đồ và ô Hai bên, bỏ riêng Hủy thay đổi của Stage, không để thông báo đẩy Sơ đồ khỏi vị trí đang làm.

## Acceptance Criteria

1. **Đúng nghĩa trường**
   **Given** người sống/người chết có địa chỉ và nơi cấp
   **When** chuyên viên sửa, lưu rồi mở lại
   **Then** địa chỉ/Nơi chết và nơi cấp giấy tờ có nhãn riêng, giữ đủ hai giá trị
2. **Vùng thao tác dùng được**
   **Given** layout được duyệt ở viewport report/màn nhỏ và danh sách dài
   **When** gán/hoán đổi bằng kéo thả hoặc bàn phím và có thông báo
   **Then** target còn tiếp cận được, thông báo không đẩy Sơ đồ khỏi vị trí thao tác, kích thước/cuộn đúng thiết kế đã nhận
3. **Giữ nháp**
   **Given** Stage hoặc Diagram chưa lưu
   **When** chuyên viên chuyển màn hoặc đóng app
   **Then** không còn Hủy thay đổi của Stage nhưng dirty, giữ nháp và cảnh báo rời/đóng vẫn hoạt động

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C01
- source — _bmad-output/specs/notary_v2/README.md, §4, §5, §8
- source — _bmad-output/tmp/notary-flow-remediation/assessment-plan.md, §1 proposal, not approved design

## Notes

- Tracking: C01; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: medium — Bố cục hoặc nhãn sai làm khó thao tác và có thể khiến người dùng sửa nhầm trường; phải giữ bảo vệ nháp.
- Unknown: Chốt đo chiều rộng nội dung hay khung Pool, vùng tăng 50% chiều cao, kích thước ô thả và vị trí thông báo. Khi refinement, không để câu hỏi kích thước chặn phần nhãn/nút độc lập.
- Report: 18ae1083, e86a02bb, 802bd69e, 2c232a28, b54184b3, ac5e3ae3. Thiết kế ở assessment §1 mới là đề xuất, chưa duyệt tỷ lệ.

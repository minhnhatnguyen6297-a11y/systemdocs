---
id: 24
type: story
title: "Xuất Word theo dữ liệu mẫu thực sự cần, cho phép điền dần"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: high
---

# Xuất Word theo dữ liệu mẫu thực sự cần, cho phép điền dần

## Description

Đồng bộ readiness với hướng điền dần đã chọn: dữ liệu hợp lệ chưa có có thể trống, mẫu chỉ cần Stage không đòi Diagram hoàn chỉnh không liên quan. Giữ rõ lỗi mẫu/nguồn, bảo vệ nháp và giới hạn slot chưa giải quyết.

## Acceptance Criteria

1. **Mẫu chỉ cần Stage**
   **Given** mẫu hợp lệ dùng field Stage đã lưu, có vài giá trị hợp lệ chưa có
   **When** chuyên viên xuất khi Diagram chưa hoàn thiện không liên quan
   **Then** điền phần có và để trống phần được phép; không chặn vì chưa hoàn tất nghiệp vụ không phục vụ mẫu
2. **Giữ blocker cụ thể**
   **Given** token không hỗ trợ, nguồn/mẫu hỏng, nháp khác bản lưu, stale revision hoặc slot ngoài ranh giải quyết hiện hành
   **When** chuyên viên xuất
   **Then** báo đúng điều kiện không an toàn và giữ chặn theo contract, không coi là field trống
3. **Kết quả từng mode/file**
   **Given** folder/legacy trong phạm vi blocker được chọn rõ
   **When** xuất nhiều văn bản có một file lỗi
   **Then** mỗi file dùng bản đã lưu, báo đã lưu/lỗi/bỏ qua riêng và không ghi đè nguồn

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C23
- source — _bmad-output/specs/notary_v2/README.md, §6, §9
- source — _bmad-output/specs/notary_v2/word-templates.md, §1, §3.3

## Notes

- Tracking: C23; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Nới nhầm guard có thể xuất sai nguồn/slot hoặc dữ liệu chưa lưu thay vì chỉ để trống trường hợp lệ.
- Unknown: Cụ thể những blocker Stage/Người/Tài sản/slot đại diện và mode legacy nào được nới cho từng nhóm token/mẫu? Giữ ranh unresolved-slot và giới hạn kỹ thuật tới khi chọn đúng scope; không hỏi lại có muốn điền dần không.
- Unknown: ghi rõ phạm vi nới blocker khi refinement trước khi đổi guard tương ứng. #9 là bằng chứng nghiệm thu bổ sung, không hard prerequisite để bắt đầu phân tích implementation độc lập này.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

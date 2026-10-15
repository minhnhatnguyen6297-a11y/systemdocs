---
id: 17
type: story
title: "Chuyển desktop sang bản Electron còn được hỗ trợ"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: high
---

# Chuyển desktop sang bản Electron còn được hỗ trợ

## Description

Chọn bản Electron còn được hỗ trợ, phù hợp triển khai Windows và chuyển đường dependency/package desktop. Rủi ro hỗ trợ đã có, không là phát hiện CVE mới hay câu hỏi duyệt lại nghiệp vụ.

## Acceptance Criteria

1. **Triển khai được hỗ trợ**
   **Given** target kỹ thuật còn hỗ trợ và ràng buộc Windows
   **When** cài sạch package và khởi chạy
   **Then** app mở đường module/sidecar thật và dialog native hoạt động trên môi trường hỗ trợ
2. **Giữ hành vi**
   **Given** ma trận nghiệm thu Notary/Upload và debug isolation
   **When** chạy regression/E2E đóng gói và check.cjs sau implementation
   **Then** ghi kết quả/phiên bản/giới hạn, dữ liệu production còn nguyên và debug/mock không bật trong package

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C16
- source — _bmad-output/implementation-artifacts/deferred-work.md, Electron support record

## Notes

- Tracking: C16; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Nâng nền desktop sai có thể làm hỏng đóng gói, picker/sidecar hoặc đường xử lý dữ liệu nhạy cảm.
- Câu hỏi kỹ thuật khi refinement: chọn bản còn hỗ trợ, tương thích electron-builder/browser và Windows theo bằng chứng hiện tại. Điểm vào code: shell/package.json. Không bịa CVE, phiên bản đích hoặc bằng chứng package đã đạt.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

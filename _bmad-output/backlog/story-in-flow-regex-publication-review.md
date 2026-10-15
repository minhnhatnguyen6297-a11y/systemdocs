---
id: 23
type: story
title: "Thử và công bố rule regex rồi duyệt kết quả chạy lại trong flow"
parent: none
covers: []
after: [8, 22]
assignee: ""
refined: false
hitl: false
risk: high
---

# Thử và công bố rule regex rồi duyệt kết quả chạy lại trong flow

## Description

Đưa thử, công bố và chạy lại/duyệt vào flow theo đáp án lifecycle #8 và capability consumer chung #22. Đây là draft có gate; mô tả không tự duyệt lifecycle.

## Acceptance Criteria

1. **Thử chưa kích hoạt**
   **Given** nguồn và rule draft đã sửa
   **When** chuyên viên chạy thử trước công bố
   **Then** thấy kết quả/identity rule và nguồn, không đổi active rule hoặc Stage đã lưu
2. **Identity sau công bố**
   **Given** lần công bố có quyền theo lifecycle đã chọn
   **When** chạy lại qua consumer cần thiết
   **Then** version/hash kích hoạt nhất quán qua cache/package/runtime, phân biệt revision extraction/bằng chứng mới với cũ
3. **Duyệt trước đổi dữ liệu**
   **Given** kết quả mới khác gợi ý hoặc binding đã duyệt
   **When** chuyên viên xem và áp dụng phần chọn
   **Then** Stage chỉ đổi khi đồng ý rõ, không ghi đè bằng chứng đang dùng hoặc âm thầm rebind; lỗi/stale revision giữ state đã lưu

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C22
- source — _bmad-output/specs/shared/extraction-rules.md, §1, §5–§8
- source — _bmad-output/tmp/notary-flow-remediation/assessment-plan.md, §2 proposed lifecycle

## Notes

- Tracking: C22; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Công bố/cache/rerun sai có thể ghi đè dữ liệu đã xác nhận hoặc đổi binding sang bằng chứng khác.
- Unknown: cần đáp án lifecycle #8 được nhận và capability #22 đã giao trước refinement implementation. Điểm vào code: dialog/model intake, publication profile, package/cache identity. Không tự refresh Stage đã duyệt.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

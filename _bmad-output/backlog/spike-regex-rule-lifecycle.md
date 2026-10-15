---
id: 8
type: spike
title: "Chốt vòng đời thử, công bố và chạy lại rule regex"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Chốt vòng đời thử, công bố và chạy lại rule regex

## Description

Chốt vòng đời rule mà #23 cần để thử, công bố và chạy lại trong flow. Hướng core chung và các consumer Notary/Upload/tool đã chọn; không hỏi lại có nên dùng chung hay không.

## Approach

Đọc nguồn hiện hành và bằng chứng sẵn có trước. Chỉ so phương án trong ranh issue; không đoán phần nguồn thiếu. Người có vai trò ghi trong Notes cung cấp bằng chứng không thể lấy từ repo hoặc nhận đáp án cần lựa chọn. Không triển khai sản phẩm trong spike.

## Acceptance Criteria

1. **Trả lời đúng câu hỏi hoặc xác định bằng chứng thiếu**
   Verify: Notes ghi đối chiếu có ngày theo từng câu hỏi, nguồn/phương án/hệ quả và phần thông tin còn thật sự không lấy được.
2. **Đáp án dùng được cho đúng bên chờ**
   Verify: Notes chỉ rõ ai chờ, cần quyết định/capability gì, nơi ghi đáp án canonical và việc độc lập không phải chờ.
3. **Người chịu trách nhiệm nhận đáp án đúng phạm vi**
   Verify: owner nhận lựa chọn sản phẩm; người thao tác/reviewer nhận bằng chứng đo. Notes ghi vai trò/ngày; phần Draft/Pending chưa chọn vẫn giữ trạng thái.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C07
- source — _bmad-output/specs/shared/extraction-rules.md, §1, §5–§8
- source — _bmad-output/decisions/decision-75-regex-integration.md, §Decision

## Notes

- Tracking: C07; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Công bố hoặc chạy lại sai có thể đổi kết quả của nhiều consumer và làm lệch bằng chứng đã duyệt.
- Open question: Ai được công bố rule đã thử, nguồn rule có quyền ghi ở đâu, ghi nhận kích hoạt version/hash và rollback thế nào, duyệt khác biệt chạy lại ra sao mà không ghi đè Stage/binding đã xác nhận?
- Ai chờ: #23; sửa field #7 và parity #22 không chờ. Nơi ghi đáp án: Notes issue này, spec/contract bóc tách và decision có ngày.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

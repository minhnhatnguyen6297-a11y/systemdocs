---
id: 21
type: spike
title: "Chốt xử lý nhánh khi xóa nút giữa sơ đồ thừa kế"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Chốt xử lý nhánh khi xóa nút giữa sơ đồ thừa kế

## Description

Chốt xử lý con/nhánh khi xóa nút giữa thừa kế. Cảnh báo ảnh hưởng đã chọn; chưa chọn thuật toán cắt nhánh hoặc đổi cha.

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
- tracking — _bmad-output/backlog/README.md, C20
- source — _bmad-output/specs/notary_v2/README.md, §5, §9
- source — _bmad-output/specs/notary_v2/diagram-rules.md, §10

## Notes

- Tracking: C20; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Xóa hoặc nối lại nhánh sai có thể đổi quan hệ thừa kế đã lưu.
- Open question: Sau khi báo các con/quan hệ bị ảnh hưởng, nhánh nào giữ, tách hay xóa; xác nhận/hủy ra sao và lưu/mở lại state canonical thế nào?
- Ai chờ: thay semantics xóa dùng đáp án này. Nơi ghi: spec/decision Diagram và Notes. Không coi duyệt cảnh báo là duyệt xóa con.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

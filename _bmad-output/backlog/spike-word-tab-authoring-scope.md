---
id: 19
type: spike
title: "Đặc tả tab Word tạo và lưu mẫu"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Đặc tả tab Word tạo và lưu mẫu

## Description

Đặc tả flow tab Word riêng: nhập chữ, đề xuất placeholder, tải về sửa, nhập lại và xác nhận lưu mẫu lâu dài. Owner chọn UX/scope trước implementation; khác nút Xuất Word hiện có.

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
- tracking — _bmad-output/backlog/README.md, C18
- source — _bmad-output/specs/notary_v2/word-templates.md, §6
- source — _bmad-output/specs/notary_v2/README.md, §6, §9

## Notes

- Tracking: C18; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: medium — Scope chưa rõ có thể tạo luồng mẫu khác contract đang dùng; đây chỉ là đặc tả.
- Open question: Định dạng nguồn, đề xuất/duyệt, catalog/quyền lưu mẫu và tiêu chí phát hành nào xác định tab Word riêng?
- Ai chờ: implementation tab Word sau này. Nơi ghi: UX/spec Word canonical và Notes. Giữ token/core đã duyệt, không tự dựng tab hay quản lý mẫu tùy ý.

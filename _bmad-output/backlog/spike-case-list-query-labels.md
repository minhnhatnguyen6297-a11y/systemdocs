---
id: 20
type: spike
title: "Chốt tìm kiếm, bộ lọc và nhãn Danh sách hồ sơ"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: low
---

# Chốt tìm kiếm, bộ lọc và nhãn Danh sách hồ sơ

## Description

Chốt nhãn, nguồn tìm kiếm, bộ lọc và trình bày trạng thái của Danh sách hồ sơ. Danh sách/tạo/mở hiện có không bị coi là chưa tồn tại.

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
- tracking — _bmad-output/backlog/README.md, C19
- source — _bmad-output/specs/notary_v2/README.md, §2, §9

## Notes

- Tracking: C19; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: low — Nhãn/lọc chưa rõ làm khó tìm đúng hồ sơ; issue chưa đổi query/runtime.
- Open question: Chọn nhãn/trạng thái, trường nguồn và luật tìm/lọc nào, gồm người tạo/tên/ngày và trạng thái rỗng/lỗi?
- Ai chờ: thay UX/query Danh sách hồ sơ sau này. Nơi ghi: spec/design Notary và Notes. Không tự thêm quy trình doanh nghiệp hoặc tìm liên module.

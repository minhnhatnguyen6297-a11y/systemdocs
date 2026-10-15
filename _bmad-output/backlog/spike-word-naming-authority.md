---
id: 10
type: spike
title: "Đối chiếu phạm vi quy tắc tên entities với hướng dẫn mẫu Word"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: low
---

# Đối chiếu phạm vi quy tắc tên entities với hướng dẫn mẫu Word

## Description

Spec Word hiện đã quy định ngoặc vuông, tên nhóm dễ đọc cho mẫu mới, các tên viết liền được hỗ trợ và alias cũ. Chỉ còn đối chiếu phạm vi câu bắt buộc tên viết liền ở entities §9.1 với hướng dẫn mẫu mới ở Word §4.1. Không mở tính năng cú pháp hoặc phát hiện literal mới.

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
- tracking — _bmad-output/backlog/README.md, C09
- source — _bmad-output/specs/notary_v2/word-templates.md, §4
- source — contracts/entities.md, §9.1
- source — _bmad-output/tmp/notary-word-recheck/syntax-evidence.md, historical parser evidence
- source — _bmad-output/tmp/notary-word-recheck/smoke-proof.json, real_api, direct_real_engine

## Notes

- Tracking: C09; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: low — Hướng dẫn tên không rõ có thể khiến người viết mẫu dùng sai quy ước; không thay parser hay mapping.
- Open question: Quy định tên viết liền bắt buộc tại entities §9.1 chỉ áp cho tên trường nghiệp vụ hay cả placeholder và có lấn hướng dẫn Word §4.1 không? Đối chiếu nguồn đã có trước; chỉ hỏi owner nếu đúng điểm thẩm quyền này còn thiếu căn cứ.
- Đã rõ: ngoặc vuông và hỗ trợ tên dễ đọc/viết liền theo Word §4.1. Không mở câu hỏi hay implementation cho ngoặc nhọn, migration hoặc tự phát hiện literal. Ai chờ: chỉ sửa hướng dẫn đặt tên mâu thuẫn; #9 và dùng token hiện có không chờ. Nơi ghi: Notes và đúng đoạn Word/entities cần làm rõ nếu có.

---
id: 9
type: spike
title: "Kiểm chứng đường xuất Word thật và nguồn mẫu"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Kiểm chứng đường xuất Word thật và nguồn mẫu

## Description

Lập đường nhập thử an toàn qua backend thật, picker native và đúng byte mẫu; kiểm nội dung Word thực. Một người thao tác UI native và kiểm trang mẫu đại diện; mock không thay nghiệm thu engine.

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
- tracking — _bmad-output/backlog/README.md, C08
- source — _bmad-output/specs/notary_v2/word-templates.md, §2.3–2.4, §3, §5
- source — _bmad-output/tmp/notary-word-recheck/template-evidence.md, §Evidence, §Synthetic smoke
- source — _bmad-output/implementation-artifacts/deferred-work.md, Word/picker, clean-install/restore and filesystem records

## Notes

- Tracking: C08; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: medium — Chứng cứ thiếu phạm vi có thể khiến đóng nhầm lỗi xuất Word; issue này không sửa dữ liệu sản phẩm.
- Open question: Sau khi tận dụng nguồn đã tìm được, còn thiếu bản sao mẫu đại diện/đáp án nào để kiểm native, bản cài sạch và khôi phục? Không yêu cầu thử phá dữ liệu production.
- Ai chờ: kết luận nghiệm thu đường thật/nguồn mẫu, không phải bắt đầu #24. Nơi ghi: Notes và đường bằng chứng, launch/backend, fixture, mẫu/hash và kết quả. Kiểm sao lưu cùng DB+docx_sources, phục hồi/bản cài sạch, retention/dọn thủ công và filesystem được hỗ trợ. Chưa duyệt tự dọn. DOCX generic của run-dev không chứng minh engine thật hỏng hay đã đúng.

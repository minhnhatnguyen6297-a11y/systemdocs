---
id: 14
type: spike
title: "Chốt phạm vi và tiêu chí pilot NotaryOffice"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Chốt phạm vi và tiêu chí pilot NotaryOffice

## Description

Chốt có giao pilot Office và đo A1/A3/A4 trong môi trường cô lập được phép hay chưa. Owner/người tham gia chọn scope và nghiệm thu; issue này không cấp quyền schema/runtime production.

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
- tracking — _bmad-output/backlog/README.md, C13
- source — _bmad-output/specs/notaryoffice/README.md, §1–6
- source — _bmad-output/specs/shared/data-rules.md, §5–§7, Còn mở

## Notes

- Tracking: C13; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: medium — Pilot sai phạm vi có thể gây hiểu lầm về nhận diện người/việc hoặc thu nhận ngoài phạm vi cho phép; chưa triển khai production.
- Open question: Giao pilot lúc này hay giữ Draft? Những phép đo Word đang mở, sự kiện ổ mạng, tài khoản người dùng, ví dụ nhóm việc, quyền/retention và tiêu chí người dùng nào xác định pilot?
- Ai chờ: delivery Office sau khi được giao, không phải Notary/Upload độc lập. Nơi ghi: Notes và spec/decision Office. Không hard-after DB chung #13; chuyển liên module thật cần contract riêng. Loại theo dõi bản in/tài khoản riêng.

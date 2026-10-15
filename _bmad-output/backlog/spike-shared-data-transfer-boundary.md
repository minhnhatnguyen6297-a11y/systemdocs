---
id: 13
type: spike
title: "Chốt DB vật lý và contract chuyển dữ liệu liên module"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Chốt DB vật lý và contract chuyển dữ liệu liên module

## Description

Chốt DB vật lý/migration và chuyển dữ liệu xuyên ownership trước công việc thực sự ghi/chuyển liên module. Các phép đo Office cô lập không cần đợi DB vật lý chung.

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
- tracking — _bmad-output/backlog/README.md, C12
- source — _bmad-output/specs/shared/data-rules.md, §5–§7, Còn mở
- source — _bmad-output/decisions/decision-extraction-output-data-contract.md, §Decision

## Notes

- Tracking: C12; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Ownership hoặc migration sai có thể nối nhầm hồ sơ, mất dữ liệu và ghi ngoài quyền module.
- Open question: Với lần chuyển liên module cụ thể, ai sở hữu từng lần ghi, payload/xác nhận nào được duyệt, chọn DB vật lý/migration nào trước schema production?
- Ai chờ: implementation schema/chuyển liên module thật. Nơi ghi: contract dữ liệu/chuyển được duyệt và Notes. Không gộp Case từ CCCD/GCN/thửa-tờ; không chặn #14 đo A1/A3/A4.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

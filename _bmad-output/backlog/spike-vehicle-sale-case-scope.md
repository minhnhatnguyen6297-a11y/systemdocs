---
id: 29
type: spike
title: "Để sau: chốt phạm vi hồ sơ mua bán ô tô, xe máy"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Để sau: chốt phạm vi hồ sơ mua bán ô tô, xe máy

## Description

Owner xác định mua bán ô tô/xe máy là hồ sơ hai bên nhưng chưa chọn bộ trường Tài sản và các biến thể xe. Owner yêu cầu ghi issue để làm sau, **hiện không làm ca này**. Chỉ phần hồ sơ xe tương lai chờ đáp án; việc ghi context chung và các loại khác không phụ thuộc issue này.

## Approach

**DEFERRED — 19/10/2026.** Không bắt đầu nghiên cứu/thiết kế/triển khai, tạo field, mẫu Word, dữ liệu xe hoặc chạy thử khi owner chưa mở lại. Khi được mở lại, ghi rõ phạm vi xe, bộ trường/ánh xạ được duyệt và biến thể cần phục vụ trước khi chuyển sang implementation. Không đặt thời hạn hoặc tự chọn đáp án.

## Acceptance Criteria khi owner mở lại

1. **Phạm vi xe và biến thể được ghi rõ**
   Verify: Notes ghi loại giao dịch, ô tô/xe máy và biến thể owner thực sự chọn; không biến danh sách đề xuất thành phạm vi đã duyệt.
2. **Dữ liệu xe có đích canonical được duyệt**
   Verify: đáp án phân biệt trường đã có, mapping còn thiếu và phần cần duyệt mở rộng; không có field tự đặt hoặc thông tin xe nhét vào ghi chú khác nghĩa.
3. **Owner nhận đáp án trước implementation**
   Verify: Notes dẫn quyết định có ngày của owner và ảnh hưởng tới hồ sơ xe tương lai. Kết quả spike không được gọi là runtime, mẫu Word hoặc E2E đã xây dựng.

## References

- parent — none
- source — _bmad-output/decisions/decision-owner-case-context-standard-data-20261019.md, Context từng nhóm owner nêu / nhóm 5
- source — _bmad-output/specs/notary_v2/README.md, Context theo loại hồ sơ / nhóm 5
- source — _bmad-output/specs/shared/data-rules.md, §4.2
- source — contracts/entities.md, phạm vi chuẩn định danh và bộ trường hiện có

## Notes

- Decision: owner 19/10/2026 — chỉ ghi issue xe để sau; **DEFERRED, hiện không làm ca này**. Giữ `refined: false`; không phải giao việc bắt đầu hoặc phê duyệt schema.
- Risk: medium — tự chọn field hoặc biến thể có thể lưu sai tài sản và tạo văn bản sai nghĩa.
- Open question khi được mở lại: owner chọn phạm vi giao dịch và biến thể ô tô/xe máy nào?
- Open question khi được mở lại: bộ trường canonical/ánh xạ của Tài sản xe là gì; phần nào đã có và phần nào cần duyệt mở rộng?
- Open question khi được mở lại: văn bản chính/phụ và tiêu chí nghiệm thu nào áp dụng cho phạm vi đã chọn?
- Identity: `next_id: 29` từ `tickets.py status _bmad-output/backlog` ngày 19/10/2026; không dùng lại #18 đã REMOVED. Không tạo phụ thuộc hoặc mở lại #14/#19/#20/#27.

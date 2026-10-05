---
id: TASK-3
title: Triển khai lõi tra cứu hành chính theo spec + contract v2
status: In Progress
assignee:
  - '@devin'
created_date: '2026-10-05 01:07'
updated_date: '2026-10-05 01:13'
labels:
  - address-lookup
  - shared-core
dependencies: []
references:
  - docs/spec/shared/administrative-lookup.md
  - docs/spec/notary_v2/administrative-address.md
  - contracts/notary-case-drafting.md
  - contracts/notary-case-drafting/address-lookup.v2.schema.json
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Spec docs/spec/shared/administrative-lookup.md và contract notary.address-lookup.v2 đã Owner duyệt 05/10/2026 (TASK-2). Runtime hiện vẫn v1: bắt source_date/target_date, tách xã+tỉnh, trả coverage/partial, bỏ tiền tố khi so, đoán cấp theo mốc ngày — trái spec. Task này chuyển runtime sang v2 và xóa schema v1. Quyết định đã chốt ghi trong spec + backlog decision-8..18; KHÔNG suy diễn thêm luật, chỗ chưa chốt hỏi Owner.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Lệnh notary.address_lookup nhận payload query + presentation (drafting|full), trả schema_version notary.address-lookup.v2 với status found|not_found|too_many|invalid_input|reload_failed theo §14
- [ ] #2 Khớp đúng spec: giữ tiền tố, danh mục viết tắt cố định đổi ra tiền tố đầy đủ, không phân biệt hoa/thường, gõ không dấu khớp bỏ dấu, khớp liền cụm đúng thứ tự, không tự đổi số
- [ ] #3 Flow phải->trái: cụm cuối khớp tỉnh (tên hoặc đoạn chữ sáp nhập từ) thì giới hạn phạm vi trong mọi tỉnh khớp; không khớp thì tra toàn quốc; mọi cụm còn lại tra xã; cụm tiền tố huyện/quận/thị xã bỏ qua; tra huyện trả không có
- [ ] #4 Presentation drafting trả display dạng xã Ý Yên, tỉnh Ninh Bình (loại đơn vị thường, tên riêng hoa); full trả đầy đủ gồm đoạn chữ gốc sáp nhập từ
- [ ] #5 too_many chỉ khi drafting và total > 10, results rỗng; not_found/invalid_input/reload_failed có total 0, results rỗng
- [ ] #6 Test cover: viết tắt, tiền tố, hoa/thường, không dấu, liền cụm (Bình Yên/Yên Thịnh Bình không khớp Yên Bình), phạm vi tỉnh, nhiều cụm, bỏ cụm huyện, trùng tên, không có, too_many, reload_failed; validate_examples 0 lỗi
- [ ] #7 Xóa address-lookup.schema.json v1 cùng lúc runtime chuyển v2; không còn code/test tham chiếu v1
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

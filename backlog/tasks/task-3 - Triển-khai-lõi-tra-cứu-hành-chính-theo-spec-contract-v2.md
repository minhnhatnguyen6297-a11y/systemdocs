---
id: TASK-3
title: Triển khai lõi tra cứu hành chính theo spec + contract v2
status: In Progress
assignee:
  - '@devin'
created_date: '2026-10-05 01:07'
updated_date: '2026-10-05 02:19'
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
- [ ] #2 Khớp đúng spec: giữ tiền tố, danh mục viết tắt cố định đổi ra tiền tố đầy đủ, không phân biệt hoa/thường, NFC chuẩn hóa, input có dấu so có dấu, input hoàn toàn không dấu so bỏ dấu (đ→d phía DB), khớp liền cụm đúng thứ tự, không tự đổi số
- [ ] #3 Mọi cụm tra độc lập: so vào xã toàn quốc (tên + đoạn chữ gốc) và so vào tỉnh (tên + đoạn chữ gốc); tỉnh khớp luôn in dòng riêng kể cả khi đã là tỉnh cha của xã trong kết quả; không scope, không bỏ qua cụm theo tiền tố huyện; kết quả không chứa đơn vị cấp huyện
- [ ] #4 Presentation drafting trả display dạng xã Ý Yên, tỉnh Ninh Bình (loại đơn vị thường, tên riêng hoa) và tỉnh Ninh Bình cho level tỉnh; full trả đầy đủ gồm đoạn chữ gốc sáp nhập từ
- [ ] #5 too_many chỉ khi drafting và total > 10 (gồm cả dòng tỉnh), results rỗng; not_found/invalid_input/reload_failed có total 0, results rỗng; invalid_input có presentation null
- [ ] #6 Test cover: viết tắt đủ danh mục, tiền tố, hoa/thường, không dấu, NFD, d/đ, liền cụm (Bình Yên/Yên Thịnh Bình không khớp Yên Bình), nhiều cụm độc lập, cụm huyện/quận khớp raw_phrase xã, trùng tên, cụm khớp nhiều tỉnh, tên có gạch ngang (Bà Rịa - Vũng Tàu), khớp ghi chú trong ngoặc, độ dài query 1/4000/4001, không có, too_many, full >10 không bị chặn, reload_failed; validate_examples 0 lỗi
- [ ] #7 Renderer ngủ đông: gửi/nhận v2, gỡ mọi trigger tự động, bỏ nối (nay là ...); nút Tra/popup/overlay thuộc TASK-4
- [ ] #8 Xóa address-lookup.schema.json v1; không còn tham chiếu v1 trong code/test/spec còn dùng (spec §12 ghi chú lịch sử trỏ v2)
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Theo bmad-build (route full), plan chi tiet: _bmad-output/implementation-artifacts/plan-task-3-administrative-lookup-v2.md
1. Viet lai engine v2 trong notary_v2/services/administrative_address.py (tach cum ,/-, viet tat co dinh, giu tien to, khop lien cum tren ten+raw_phrase; MOI CUM tra doc lap vao xa toan quoc va tinh, tinh khop in dong rieng, khong scope/skip; 5 status; display drafting/full). Giu cache signature/lock, read_ledger/validate.
2. Viet lai test_administrative_address.py cho v2 (synthetic+real ledger+cache+staging+schema v2; bo test theo matrix moi).
3. Renderer ngu dong: case-drafting-model.js + view.js nhan/gui v2, go trigger tu dong, bo noi (nay la ...); UX nut Tra/popup = TASK-4.
4. Sua 3 file test shell sang stub/assert v2.
5. Xoa address-lookup.schema.json v1 + sua tham chieu; cap nhat spec §12 (ghi chu lich su tro v2) + contract §14/changelog.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
05/10/2026: Codex review plan = APPROVE_WITH_FIXES (9 findings, .agents/task3-plan-review-codex.md). Owner quyet: renderer ngu dong toi TASK-4; doi luat tim kiem — moi cum doc lap so xa+tinh, tinh luon in dong rieng, khong bo qua cum huyen (decision-19, spec §7, theo hanh vi Bando). Ledger that: 0 province raw_phrase chua tu huyen.
<!-- SECTION:NOTES:END -->

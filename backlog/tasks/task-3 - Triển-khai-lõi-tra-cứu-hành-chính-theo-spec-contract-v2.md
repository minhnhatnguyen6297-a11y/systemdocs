---
id: TASK-3
title: Triển khai lõi tra cứu hành chính theo spec + contract v2
status: Done
assignee:
  - '@codex'
created_date: '2026-10-05 01:07'
updated_date: '2026-10-06 01:13'
labels:
  - address-lookup
  - shared-core
dependencies: []
references:
  - docs/spec/shared/administrative-lookup.md
  - docs/spec/notary_v2/administrative-address.md
  - contracts/notary-case-drafting.md
  - contracts/notary-case-drafting/address-lookup.v2.schema.json
  - .agents/plans/task-3-administrative-lookup-v2.md
  - .agents/plans/task-3-4-handoff.md
  - .agents/audit-task3-4-20261005/REVIEW.md
  - .agents/handoffs/task3-4-opencode-rework-20261005.md
  - .agents/review-task3-4-resumed-20261005/REVIEW.md
  - .agents/fix-task3-4-20261005/RESULT.md
  - .agents/plans/task-3-4-fix-review-20261005.md
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Lõi v2 theo spec Owner duyệt đã sửa và nghiệm thu 06/10/2026: bỏ đơn vị lịch sử không còn trong catalog hiện hành, giữ tên-only hợp lệ; nguồn theo thứ tự kho; xã thiếu tỉnh trả lỗi kho thay vì found sai schema. P1/P2/P3/P10 có regression và mutation bắt lỗi cũ. Luật tra và contract Owner giữ nguyên. Kết quả: .agents/fix-task3-4-20261005/RESULT.md.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Lệnh notary.address_lookup nhận payload query + presentation (drafting|full), trả schema_version notary.address-lookup.v2 với status found|not_found|too_many|invalid_input|reload_failed theo §14
- [x] #2 Khớp đúng spec: giữ tiền tố, danh mục viết tắt cố định đổi ra tiền tố đầy đủ, không phân biệt hoa/thường, NFC chuẩn hóa, input có dấu so có dấu, input hoàn toàn không dấu so bỏ dấu (đ→d phía DB), khớp liền cụm đúng thứ tự, không tự đổi số
- [x] #3 Mọi cụm tra độc lập: so vào xã toàn quốc (tên + đoạn chữ gốc) và so vào tỉnh (tên + đoạn chữ gốc); tỉnh khớp luôn in dòng riêng kể cả khi đã là tỉnh cha của xã trong kết quả; không scope, không bỏ qua cụm theo tiền tố huyện; kết quả không chứa đơn vị cấp huyện
- [x] #4 Presentation drafting trả display dạng xã Ý Yên, tỉnh Ninh Bình (loại đơn vị thường, tên riêng hoa) và tỉnh Ninh Bình cho level tỉnh; full trả đầy đủ gồm đoạn chữ gốc sáp nhập từ
- [x] #5 too_many chỉ khi drafting và total > 10 (gồm cả dòng tỉnh), results rỗng; not_found/invalid_input/reload_failed có total 0, results rỗng; invalid_input có presentation null
- [x] #6 Test cover: viết tắt đủ danh mục, tiền tố, hoa/thường, không dấu, NFD, d/đ, liền cụm (Bình Yên/Yên Thịnh Bình không khớp Yên Bình), nhiều cụm độc lập, cụm huyện/quận khớp raw_phrase xã, trùng tên, cụm khớp nhiều tỉnh, tên có gạch ngang (Bà Rịa - Vũng Tàu), khớp ghi chú trong ngoặc, độ dài query 1/4000/4001, không có, too_many, full >10 không bị chặn, reload_failed; validate_examples 0 lỗi
- [x] #7 Renderer ngủ đông: gửi/nhận v2, gỡ mọi trigger tự động, bỏ nối (nay là ...); nút Tra/popup/overlay thuộc TASK-4
- [x] #8 Xóa address-lookup.schema.json v1; không còn tham chiếu v1 trong code/test/spec còn dùng (spec §12 ghi chú lịch sử trỏ v2)
- [x] #9 Cùng đơn vị có nhiều dòng nguồn khớp thì trả riêng nguyên văn từng dòng với observation_id/evidence; không chọn hộ/gộp/báo reload_failed vì nhiều nguồn. Chỉ bỏ cùng dòng khớp lặp qua nhiều cụm; total và ngưỡng 10 tính số dòng, không đếm unit_id khác nhau.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [x] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [x] #3 Tests pass
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Sẵn sàng giao worker. Plan chi tiết: .agents/plans/task-3-administrative-lookup-v2.md; bàn giao: .agents/plans/task-3-4-handoff.md. Owner đã chốt nhiều nguồn: in riêng mọi dòng khớp, người dùng chọn; không tự chọn/gộp/báo lỗi vì nhiều nguồn. total đếm dòng kết quả. Triển khai lõi v2, renderer ngủ đông, tests và chuyển schema; sau nghiệm thu bàn giao model/view cho TASK-4.

Sau kiểm tra độc lập 05/10: sửa R1/R2 theo .agents/audit-task3-4-20261005/REVIEW.md; thêm ca raw-only khớp nhiều observation (2 và 11 dòng), hai lần import đổi tên và tỉnh cha; nghiệm thu lại lõi trước khi TASK-4 Done.

Review tiếp 05/10 16:19 UTC: xử lý P1/P2/P3/P10 trong REVIEW mới; kiểm kho hot-cache và đơn vị biến mất, thứ tự observation qua query đảo cụm, xã thiếu tỉnh và assertion thứ tự thực sự có thể rớt. Không đổi luật khớp hoặc phạm vi Owner.

Owner yêu cầu tự sửa P1-P12. Kế hoạch hiện hành: .agents/plans/task-3-4-fix-review-20261005.md; sửa lõi trước, UI sau, review và kiểm Electron trước nghiệm thu; giữ TASK-1 và thay đổi dở, không commit/push.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
05/10/2026: Codex review plan = APPROVE_WITH_FIXES (9 findings, .agents/task3-plan-review-codex.md). Owner quyet: renderer ngu dong toi TASK-4; doi luat tim kiem — moi cum doc lap so xa+tinh, tinh luon in dong rieng, khong bo qua cum huyen (decision-19, spec §7, theo hanh vi Bando). Ledger that: 0 province raw_phrase chua tu huyen.

05/10/2026 Owner giao Codex: lam song song TASK-3 va TASK-4 o pha hoan thien spec, sau do lap plan chi tiet giao worker. Chua trien khai runtime; giu assignee hien co @devin. Plan moi du kien .agents/plans/task-3-administrative-lookup-v2.md; doi chieu plan cu va review truoc khi chot.

Ra soat spec/plan 05-10: sua contract con luat phai-trai, ro NFC/d-d va xac dinh co dau TRUOC mo rong viet tat (P. yen binh). Con cho Owner: nhieu observation cung unit trong dataset dang hoat dong, plan cu tu noi raw_phrase chua co quyet dinh. Kho hien tai 1 observation/unit. Khong tu chot chon/gop.

05/10/2026: plan chi tiet da ghi tai .agents/plans; reviewer doc lap da doi chieu spec/contract/plan, nhat quan o muc Draft. Chua giao trien khai: cho 3 cau tra loi Owner (Q3-SOURCE, Q4-BUTTON, Q4-FULL) tai task-3-4-handoff.md. git diff --check khong loi whitespace. Khong sua runtime, khong chay runtime tests, khong tick Done.

Owner chốt 05/10: in dữ liệu ra, user tự chọn; đây là tool truy vấn DB, không thêm quy tắc phức tạp. Bỏ gate Q3-SOURCE và đề xuất báo lỗi nguồn trùng. Spec mục 4,7,8 và contract §14 đã đồng bộ. Chưa triển khai runtime.

TASK-3 code xong: engine v2 + test Python 53 pass, renderer ngu dong, xoa schema v1, validator 0 loi. Chi tiet .agents/task3-handoff-to-task4.md

Nghiem thu TASK-3 (evidence): pytest notary_v2/tests/test_administrative_address.py + shell/test/test_notary_mock_adapter.py = 207 passed/3 skipped (skip: jsonschema/pwsh thieu, co san); node --test 2 file renderer = 62+ pass luc ban giao (sau TASK-4: 73 pass); validate_examples.py 82 files 0 unexpected; schema v1 da xoa, rg khong con tham chieu v1 trong code/test (chi dong changelog lich su); git diff --check sach. npm test full rot san tai notary-docx-intake.test.mjs (ngoai pham vi, ton tai truoc TASK-3). Handoff: .agents/task3-handoff-to-task4.md

05/10/2026 Codex kiểm tra độc lập: CHƯA ĐẠT, mở lại TASK-3. R1: raw_phrase cùng khớp nhiều observation chỉ trả dòng đầu; 11 dòng bị tính thành 1 nên found thay vì too_many. R2: import hai snapshot hợp lệ, response gắn version mới nhưng tên và tỉnh cha lấy rows[0] của kho cũ; tra tên mới not_found. Probe và dữ liệu giả lập: .agents/audit-task3-4-20261005/REVIEW.md, core-result.json. Bỏ tick AC4/5/9 và DoD3 vì kiểm chứng hành vi chưa đạt; test có sẵn vẫn 207 passed/3 skipped, renderer 73 passed, validator 82 files/0 unexpected. Không sửa luật Owner, không sửa runtime, không tạo task ngoài phạm vi. Final Summary cũ được bỏ vì chưa thể kết luận hoàn thành.

Owner 05/10/2026 yêu cầu handoff OpenCode làm lại sau audit chưa đạt. Bàn giao sửa trong phạm vi TASK-3/TASK-4: .agents/handoffs/task3-4-opencode-rework-20261005.md. OpenCode tiếp tục tại D:/systemdocs, terminal term_9aae2638-cb43-4a42-a88b-3f9daf8baa47. Sửa lõi R1/R2 trước, UI R3/R5/R6 sau; R4 là hành vi đúng theo plan. Không thay luật Owner, không reset/clean hay commit/push; chỉ Done khi có bằng chứng. Chế độ giao toàn quyền, Codex không giám sát chạy nền.

Rework R1/R2 xong + verified: raw khop tra rieng moi observation (2/11 dong), ten khop tra ca 11, 11 dong -> too_many total=11; importer that 2 snapshot doi ten+tinh cha tra dung version moi; pytest 211 passed/3 skipped (skip nhu cu: thieu jsonschema + symlink); validator 82/0; probe audit cu rot dung cho du kien (assert loi cu). Spec S12 + decision-45 da ghi.

Codex tiếp phiên, review độc lập hoàn tất: CHƯA ĐẠT, mở lại TASK-3. P1: importer thật ba snapshot, unit không còn trong catalog mới vẫn found với source_text null/evidence rỗng. P2: query đảo thứ tự cụm trả nguồn 1 trước 0. P3: ledger validate đạt nhưng xã thiếu tỉnh trả province:null trái schema. P10: test thứ tự tại dòng 577 so danh sách với chính nó. Bỏ tick AC4/9 và DoD3; giữ bằng chứng sửa R1/R2 trước. Python 211 đạt/3 bỏ qua, renderer 79 đạt, examples 82/0; số xanh chưa chứng minh các ca này. Báo cáo/probe: .agents/review-task3-4-resumed-20261005/REVIEW.md. Không sửa runtime, không commit/push.

Owner yêu cầu tự sửa. Đã sửa P1/P2/P3/P10; root kiểm importer hot-cache và ba snapshot, thử bỏ sửa trong bộ nhớ đều rớt đúng regression. Producer frozen thật từ .agents/package với kho public: found/not_found/too_many/full/invalid_input/reload_failed đều đúng schema, full 3001 dòng, mất snapshot không trả cũ, khôi phục đọc được, mock flag bị bỏ qua; không tạo DB văn phòng trong engine. Python address+timeline+adapter 294 đạt/2 skip symlink do quyền Windows; jsonschema đã chạy. npm 403 đạt; renderer 90 đạt; examples 82/0; diff check sạch. Spec đã ghi kết quả và lý do, decision-47 ghi nghiệm thu. Evidence: .agents/fix-task3-4-20261005/RESULT.md. Không commit/push, giữ TASK-1 và dữ liệu/đổi dở khác.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Sửa lõi P1/P2/P3/P10 đúng spec; regression và mutation bắt đủ lỗi cũ. Kiểm độc lập 294 Python/2 skip symlink, 403 npm, examples 82/0; frozen producer và kho public đạt cả các trạng thái/full 3001 dòng. Nghiệm thu 06/10/2026, evidence tại .agents/fix-task3-4-20261005/RESULT.md.
<!-- SECTION:FINAL_SUMMARY:END -->

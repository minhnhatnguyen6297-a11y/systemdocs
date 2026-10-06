---
id: TASK-2
title: Brainstorm Muc 5 - Loi tra cuu thay doi ten don vi hanh chinh dung chung
status: Done
assignee:
  - '@devin'
created_date: '2026-10-04 16:32'
updated_date: '2026-10-05 01:05'
labels:
  - brainstorming
  - address-lookup
  - shared-core
dependencies: []
references:
  - .agents/review-plan-20261004/investigation-report.md
  - >-
    _bmad-output/brainstorming/brainstorm-tra-cuu-don-vi-hanh-chinh-2026-10-05/.memlog.md
modified_files:
  - docs/spec/shared/administrative-lookup.md
  - docs/spec/notary_v2/administrative-address.md
  - docs/spec/notary_v2/word-output.md
  - docs/spec/notary_v2/stage.md
  - docs/spec/notary_v2/input/README.md
  - docs/spec/notary_v2/administrative-timeline.md
  - docs/spec/notary_v2/README.md
  - docs/spec/README.md
  - README.md
  - contracts/notary-case-drafting.md
  - contracts/notary-case-drafting/address-lookup.v2.schema.json
  - contracts/notary-case-drafting/validate_examples.py
  - >-
    contracts/notary-case-drafting/examples/valid/command.address-lookup.valid.json
  - contracts/notary-case-drafting/examples/valid/job.address-lookup.valid.json
  - >-
    contracts/notary-case-drafting/examples/valid/job.address-lookup-too-many.valid.json
  - >-
    contracts/notary-case-drafting/examples/invalid/command.address-lookup-year.invalid.json
type: spike
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Chỉ ghi nhận chủ đề brainstorming theo yêu cầu Owner ngày 04/10/2026. Chờ Owner gọi task tại session khác; không triển khai hoặc brainstorming chi tiết trong session tạo task này. Chưa chốt thuật toán, cấu trúc lưu trữ, giao diện hay plan; chưa sửa code/spec.

Định vị: một bộ dữ liệu về thay đổi tên gọi đơn vị hành chính và lõi truy vấn dùng chung cho các chức năng khác. Tra bằng một cấp xã/huyện/tỉnh hoặc kết hợp nhiều cấp. Ví dụ xã Yên Bình phải tra được mà không bắt nhập thêm huyện Ý Yên, tỉnh Nam Định. Chỉ cấp thông tin đã có; không bắt người dùng hoàn thiện toàn bộ địa chỉ để được tìm.

Trọng tâm buổi trao đổi sau: người dùng đưa những dạng đầu vào khác nhau thì bộ xử lý hiểu và phản hồi thế nào; nhận diện thôn, xã, huyện, tỉnh; xử lý tên không có nhãn cấp, viết tắt, chữ hoa/thường, thiếu dấu, nhiều thành phần hoặc thứ tự khác nhau. Thôn cần được xem xét như thành phần đầu vào; chưa mặc định kho dữ liệu có lịch sử thôn. Nhãn như xã/tỉnh là dấu hiệu cần bàn cách sử dụng, không tự suy diễn cấp khi chưa đủ thông tin. Nhiều nơi cùng tên, không tìm thấy hoặc chưa hiểu đầu vào là các tình huống cần làm rõ; chưa chọn quy tắc xử lý.

Không truy vấn database theo từng ký tự người dùng gõ. Cần thảo luận lúc nào gửi truy vấn và cách tránh truy vấn thừa; chưa quyết định chờ bao lâu, nhấn nút tìm hay phương án cụ thể. Ưu tiên làm rõ hành vi truy vấn và phần lõi dùng chung trước các chi tiết tích hợp vào chức năng khác.

Ví dụ làm chất liệu trao đổi: xã YÊn Bình; Yên Bình; huyện Ý Yên; tỉnh Nam Định; xã Yên Bình, tỉnh Nam Định; một chuỗi có thôn/xóm cùng xã và tỉnh. Các ví dụ này chưa là đáp án đã chốt hoặc kết luận về lịch sử thay đổi hành chính.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Buổi brainstorming làm rõ kết quả mong đợi khi tra một cấp và nhiều cấp, gồm tên trùng nhiều nơi, không tìm thấy và đầu vào chưa rõ nghĩa.
- [x] #2 Có ví dụ đầu vào và cách hiểu dự kiến cho thôn/xã/huyện/tỉnh, tên thiếu nhãn cấp, viết tắt và biến thể trình bày; giữ rõ phần chưa thể xác định.
- [x] #3 Đã trao đổi thời điểm gửi truy vấn và cách tránh truy vấn theo mỗi ký tự; các lựa chọn chưa được Owner chốt được ghi là còn mở.
- [x] #4 Owner xác nhận phạm vi lõi dùng chung và các vấn đề còn mở; task chỉ kết thúc brainstorming, không tự chuyển sang viết spec, plan hoặc code.
- [x] #5 Theo yêu cầu Owner 05/10/2026: sau brainstorming, cập nhật spec tra cứu (docs/spec/shared/administrative-lookup.md, notary_v2/administrative-address.md và link liên quan) và contract notary.address_lookup (doc, schema, examples, validator) theo quyết định đã chốt; ghi QUYẾT ĐỊNH và TẠI SAO; không sửa runtime/test.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Brainstorm (Creative Partner: Job to Be Done, Morphological Analysis, Worst Possible Idea) + hội tụ MoSCoW; ghi memlog.
2. Owner chọn đặt lõi ở cấp hệ thống: tạo docs/spec/shared/administrative-lookup.md; viết lại notary_v2/administrative-address.md thành cách hồ sơ gọi lõi.
3. Sửa câu trái quyết định ở word-output.md, stage.md, input/README.md, administrative-timeline.md, notary_v2/README.md; ngoại lệ shared core ở docs/spec/README.md; thêm shared/ vào cây README gốc.
4. Owner yêu cầu đổi contract: notary.address-lookup.v2 (doc §14 + changelog, schema v2, examples, validator); giữ schema v1 cho runtime hiện tại tới task triển khai.
5. Ghi backlog decision 8-18.
6. Kiểm: validate_examples, examples khớp schema v2, link tương đối, git diff --check; Owner duyệt.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
05/10/2026: Brainstorm xong (Creative Partner, 4 kỹ thuật + MoSCoW). Memlog: _bmad-output/brainstorming/brainstorm-tra-cuu-don-vi-hanh-chinh-2026-10-05/.memlog.md. Owner xác nhận phạm vi MoSCoW, bỏ 2 trường ngày; mở 1 (xác minh NĐ30) bỏ qua; mở 2 (bỏ bước hỏi 'xem toàn bộ?') đúng. Owner mở rộng scope: lập spec, chưa đóng task.

05/10/2026 spec: Owner chọn đặt lõi ở cấp hệ thống. Tạo docs/spec/shared/administrative-lookup.md (Draft); viết lại notary_v2/administrative-address.md thành cách hồ sơ gọi lõi; sửa câu trái quyết định ở word-output.md, stage.md, input/README.md, administrative-timeline.md, notary_v2/README.md; thêm ngoại lệ shared core + link ở docs/spec/README.md; thêm shared/ vào cây README gốc. Kiểm link tương đối: 0 lỗi. Không sửa code/contract/schema. Decision 8-13 đã tạo. Chờ Owner duyệt spec trước khi finalize.

05/10/2026 vòng 2 (Owner): (2) nơi cấp giấy khai tử = tra xã mới từ địa chỉ người chết, bỏ ngày; (3) tool tra cứu full lên Must; (4) đổi contract. Đã thêm notary.address-lookup.v2: contracts/notary-case-drafting.md §14 + changelog, address-lookup.v2.schema.json, examples (command, job found, job too_many mới, invalid gửi trường ngày), validate_examples.py. Giữ schema v1 cho runtime hiện tại; không sửa runtime/test. Kiểm: validate_examples 82 file 0 lỗi; examples khớp schema v2 (jsonschema), 2 ca âm bị bắt; test_administrative_address.py 30 pass (lỗi cleanup temp pytest do quyền máy). Câu (1) cụm cuối khớp nhiều tỉnh: còn mở, đã giải thích lại cho Owner. Decision 14-15.

05/10/2026 vòng 3: Owner chốt cụm cuối khớp nhiều tỉnh = tra như thường trong mọi tỉnh khớp, nhiều kết quả thì luật >10 chuyển tool; nhắc agent không tự suy diễn rule. Đã sửa spec §7 bước 1, bỏ mục còn mở tương ứng. Decision 16.

05/10/2026 vòng 4: Owner đổi luật >10 ở drafting: popup 'Nhiều kết quả khớp. Xem đầy đủ?', bấm đồng ý mới mở tool (thay 'chuyển thẳng'). Đã sửa spec lõi §7/§8/§10, administrative-address.md, contract §14.2. Decision 17.

05/10/2026 vòng 5: Owner chốt tool tra cứu full mở dạng popup đè lên màn hình hiện tại, không chuyển màn hình; đóng popup giữ nguyên nháp/con trỏ. Đã sửa spec lõi §8, administrative-address.md, contract §14.2. Decision 18.

05/10/2026: Owner duyệt spec + contract v2. Kiểm cuối: validate_examples 82 file 0 lỗi; link tương đối 10 file 0 hỏng; git diff --check sạch.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Brainstorm xong lõi tra cứu tên xã/tỉnh dùng chung và chốt thành spec + contract, Owner duyệt 05/10/2026.

- Spec mới docs/spec/shared/administrative-lookup.md: chỉ phản ánh DB, đúng/sai, bỏ ngày, xã+tỉnh (bỏ huyện/thôn), tách cụm phải->trái, giữ tiền tố + danh mục viết tắt, khớp liền cụm, tra trên đoạn chữ gốc Bando, nút Tra + copy không tự ghi, 2 kiểu trình bày drafting/full, >10 kết quả -> popup hỏi rồi mở tool dạng popup không mất nháp; ví dụ đầu vào, MoSCoW, còn mở, hiện trạng runtime lệch.
- notary_v2/administrative-address.md viết lại thành cách hồ sơ gọi lõi (nơi cấp giấy khai tử tra từ địa chỉ người chết); sửa link/câu cũ ở 5 spec notary_v2, docs/spec/README.md (ngoại lệ shared core), README gốc.
- Contract notary.address-lookup.v2 DRAFT->Owner duyệt: §14, schema v2, examples, validate_examples.py. Runtime/test chưa đổi, schema v1 giữ tới task triển khai.
- Kiểm: validate_examples 82 file 0 lỗi; examples khớp schema v2 (jsonschema) + ca âm bị bắt; link 0 hỏng; test_administrative_address.py 30 pass.
- Việc sau (chưa tạo task): triển khai runtime theo spec/contract v2 và xóa schema v1.
<!-- SECTION:FINAL_SUMMARY:END -->

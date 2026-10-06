---
id: TASK-4
title: >-
  Tích hợp tra cứu vào trình soạn thảo: nút Tra, popup xác nhận, tool full dạng
  overlay
status: Done
assignee:
  - '@codex'
created_date: '2026-10-05 01:08'
updated_date: '2026-10-06 01:13'
labels:
  - address-lookup
  - shared-core
  - ui
dependencies: []
references:
  - docs/spec/shared/administrative-lookup.md
  - docs/spec/notary_v2/administrative-address.md
  - contracts/notary-case-drafting.md
  - .agents/plans/task-4-address-lookup-ui.md
  - .agents/plans/task-3-4-handoff.md
  - .agents/audit-task3-4-20261005/REVIEW.md
  - .agents/handoffs/task3-4-opencode-rework-20261005.md
  - .agents/review-task3-4-resumed-20261005/REVIEW.md
  - .agents/fix-task3-4-20261005/RESULT.md
  - .agents/plans/task-3-4-fix-review-20261005.md
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Tích hợp lõi v2 sau TASK-3: chỉ bấm Tra mới tra, kết quả copy được và không tự sửa ô. Nút Tra bên phải ô, kết quả dưới ô. too_many hỏi Nhiều kết quả khớp. Xem đầy đủ? Đồng ý mở overlay full cùng query. Overlay có query sửa được, Tra, danh sách cuộn, Copy từng dòng và Đóng; giữ nháp/con trỏ. Nhiều nguồn trả riêng từng dòng để user chọn, không tự chọn/gộp/ẩn dòng.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Mỗi ô trong bảng Nơi gọi của spec có nút Tra; chỉ bấm mới gọi presentation=drafting. Query là chữ đang nhập chưa lưu trong ô nguồn; riêng nơi cấp khai tử lấy địa chỉ của chính người chết.
- [x] #2 Không tự tra khi gõ, dán, rời ô, hover hay mở hồ sơ; kết quả copy được, không tự sửa ô hay Stage; cho bấm Tra lại cùng chuỗi.
- [x] #3 too_many: không hiện dòng nào, hỏi đúng câu: Nhiều kết quả khớp. Xem đầy đủ? Đồng ý mới mở overlay full và gửi đúng query đã tra; hủy không gọi full.
- [x] #4 Đóng overlay giữ nguyên màn hình, nháp chưa lưu, chữ đang nhập, vị trí cuộn và con trỏ/vùng chọn. Một dialog; Esc, nút đóng trả focus đúng chỗ.
- [x] #5 Nơi cấp giấy khai tử tra từ địa chỉ người chết không phụ thuộc ngày; không tự điền kết quả. Nơi niêm yết tra nội dung chính ô, không lấy địa chỉ tài sản.
- [x] #6 Bỏ phản hồi cũ nếu đổi hồ sơ, người/tài sản/ô, chuỗi nguồn, hoặc đã có lần Tra mới hơn; kể cả A sang B rồi về A. Đóng overlay không cho phản hồi muộn mở lại.
- [x] #7 Có trạng thái đang tra, found, not_found, invalid_input, reload_failed và lỗi giao tiếp; copy thất bại không báo thành công. Tra bên phải ô, kết quả dưới ô; overlay có query sửa được, Tra, danh sách cuộn, Copy từng dòng, Đóng. Giữ riêng mọi dòng nguồn, không gộp theo unit_id/display.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [x] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [x] #3 Tests pass
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Tiếp tục TASK-4 sau khi lõi TASK-3 được nghiệm thu lại. Plan gốc: .agents/plans/task-4-address-lookup-ui.md; bàn giao: .agents/plans/task-3-4-handoff.md. Giữ quyết định Owner: Tra bên phải ô, kết quả dưới ô; full sửa query và bấm Tra mới gửi, danh sách cuộn, Copy từng dòng, Đóng; user chọn nguồn, không gộp. Sau audit 05/10, sửa R3/R5/R6 theo .agents/audit-task3-4-20261005/REVIEW.md: cập nhật vùng kết quả khi người dùng đang sửa, dọn loading hết hiệu lực, kiểm A-B-A trước xác nhận, Hủy/đóng full trả đúng ô và vùng chọn. Bổ sung kiểm thử, xác nhận bằng Electron và luồng khai tử/niêm yết/clipboard thật. R4 không là lỗi: query full đang gõ chưa có hiệu lực cho đến lần Tra mới. Không thêm quy tắc ngoài spec.

Review tiếp 05/10 16:19 UTC: xử lý P4/P5/P6/P7/P8/P9/P11/P12 trong REVIEW mới. Giữ luật R4. Nối Tra trong ô Nơi niêm yết của Word theo word-output.md:34; handler giữ đúng mã lần Tra; vô hiệu kết quả nguồn đã đổi; giữ focus/node/feedback Copy khi emit nền; bảo vệ phản hồi v2 và thêm kiểm trạng thái/bàn phím. Copy OS đã kiểm đạt; frozen sidecar chưa kiểm do thiếu dependency.

Owner yêu cầu tự sửa. Theo .agents/plans/task-3-4-fix-review-20261005.md: P4-P9/P11/P12 sau lõi; giữ R4, modal đơn và lưu/xuất Word; bổ sung kiểm hồi quy và Electron trước Done.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
05/10/2026 Owner giao Codex: hoan thien spec va plan chi tiet song song TASK-3; chi pha tai lieu, runtime van phu thuoc TASK-3. Dang hoi Owner vi tri nut Tra va bo cuc tool full; chua chot thay Owner. Plan du kien .agents/plans/task-4-address-lookup-ui.md.

Dependency --depends-on 3 bi CLI tu choi vi trung TASK-3 active/archive; backlog doctor chi doc lai bao khong trung. Chua sua lich su hay renumber. Phu thuoc TASK-3 duoc ghi ro trong description/spec/plan; worker phai doi chieu task active theo title va duong dan.

05/10/2026: plan chi tiet da ghi tai .agents/plans; reviewer doc lap da doi chieu spec/contract/plan, nhat quan o muc Draft. Chua giao trien khai: cho 3 cau tra loi Owner (Q3-SOURCE, Q4-BUTTON, Q4-FULL) tai task-3-4-handoff.md. git diff --check khong loi whitespace. Khong sua runtime, khong chay runtime tests, khong tick Done.

Owner đã chốt Q4-BUTTON: bên phải; Q4-FULL: đồng ý bố cục đề xuất. Q3-SOURCE: in riêng dữ liệu, user chọn. Các câu hỏi đã đóng; chưa triển khai runtime, không tick Done.

TASK-4 code xong tren model/view TASK-3 (evidence): node --test 2 file = 73 pass (10 model + 63 view, gom 7 test TASK-4 moi); pytest + validator khong doi (207 passed/3 skipped, 0 loi). AC1-7 da co test chung minh (nut Tra tung o, nguon query dung, stale/A-B-A, too_many hoi dung cau + full dung query chup, overlay sua query/Tra/Copy/Dong, giu nhap-caret-scroll). CON LAI: kiem tay GUI Electron (1280x800/1366x768, bam Tra/dong/mo/copy, luong khai tu) chua lam duoc o may nay + review doc lap. Chua tick Done theo plan. Handoff: .agents/task4-handoff.md

05/10/2026 Codex kiểm tra độc lập: TASK-4 chưa đạt, giữ In Progress; sửa assignee sai @--plan thành @opencode. Component Electron/Chromium thật, click chuột, 1280x800 và 1366x768: model ready nhưng UI vẫn Đang tra khi focus ở ô khác; Hủy mất vùng chọn; đóng full trả nhầm ô nếu trước Tra đang sửa Họ tên. Query full đổi A sang B khi chờ vẫn hiện kết quả A dưới B. Model: A-B-A sau too_many trước xác nhận vẫn mở full; response bị bỏ sau sửa nguồn nhưng slot loading còn treo. Bỏ tick AC4/6/7. Ca tốt: đóng full giữ nháp/vùng chọn khi lưu đúng ô, không mở lại sau late response, sửa query không tự gọi. Report/probe: .agents/audit-task3-4-20261005/REVIEW.md; electron-result.json/model-result.json. Chưa nghiệm thu app nối sidecar, clipboard và bản đóng gói. Core TASK-3 đã mở lại do R1/R2; không tick Done.

Đối chiếu lại plan TASK-4 dòng 48: R4 (gõ B trong full nhưng chưa bấm Tra B, vẫn thấy kết quả lần Tra A) PHÙ HỢP với quy định chữ sửa chỉ có hiệu lực sau khi bấm Tra. Không dùng R4 để chặn nghiệm thu hoặc thêm luật mới. Report đã phân loại lại; lỗi cần sửa của UI là R3/R5/R6. AC4/6/7 vẫn chưa đạt bởi các lỗi đã tái hiện đó.

Owner 05/10/2026 yêu cầu handoff OpenCode làm lại sau audit chưa đạt. Bàn giao sửa trong phạm vi TASK-3/TASK-4: .agents/handoffs/task3-4-opencode-rework-20261005.md. OpenCode tiếp tục tại D:/systemdocs, terminal term_9aae2638-cb43-4a42-a88b-3f9daf8baa47. Sửa lõi R1/R2 trước, UI R3/R5/R6 sau; R4 là hành vi đúng theo plan. Không thay luật Owner, không reset/clean hay commit/push; chỉ Done khi có bằng chứng. Chế độ giao toàn quyền, Codex không giám sát chạy nền.

Rework R3/R5/R6 xong + verified: renderer 79 pass (10 test moi); Electron that 1280x800+1366x768: ket qua hien khi sua o khac + giu focus, Huy/dong full tra dung o+vung chon+scroll, issuer/posting dung nguon, sua query khong tu tra; probe model cu dao chieu dung. R4 giu nguyen. CON THIEU (giu chua Done): Copy ra clipboard OS (cua so an khong ghi duoc) + ban dong goi + review doc lap. Spec + decision-45 + handoff .agents/handoffs/task3-4-opencode-rework-result.md da ghi.

Codex tiếp phiên, review bốn lượt đã hoàn tất: CHƯA ĐẠT. Electron thật hai cỡ màn hình xác nhận Copy clipboard đúng, R3/R5/R6 cũ vẫn đạt. Ca mới: phản hồi đảo thứ tự mở hai confirm; sửa A thành B còn Copy A; emit từ lookup cũ ở ô khác tháo Copy full đang focus; Copy chờ rồi bấm Tra lại và clipboard reject không báo lỗi. Word dialog có ô Nơi niêm yết/vùng kết quả nhưng thiếu Tra theo spec Word. Model nhận v2 sai presentation/total âm/dòng null. Thiếu test thông báo các trạng thái và focusin/bàn phím. Bỏ tick AC1/4/6/7; giữ In Progress. Report/probe: .agents/review-task3-4-resumed-20261005/REVIEW.md. Targeted 79 đạt; npm full 391 đạt/1 lỗi có sẵn vì Python thiếu jsonschema. Tài nguyên kho đã staging/test riêng; chưa có frozen exe, kiểm dependency venv thất bại vì thiếu regex==2026.9.29. Hai nhánh full khi context đổi chỉ kiểm qua API model, chưa coi là lỗi UI đã chứng minh. Không sửa runtime, không commit/push.

Owner yêu cầu tự sửa. Đã sửa P4-P9/P11/P12 và lỗi Word tìm thêm: định danh riêng, origin đã đóng không mở lại, Copy lỗi đúng vùng hoặc notify, subscription theo slot identity, kiểm malformed ở drafting/cả hai đường full; test bàn phím đầy đủ. P4 test đầu không bắt view cũ, root phát hiện qua mutation và đã sửa giữ confirm pending. Root kiểm hình/geometry sửa Tra bên phải ô Word và kết quả dưới. Electron thật hai cỡ màn hình: một dialog, đúng nguồn và nháp, Copy OS đúng, focus/cuộn/vùng chọn giữ, phản hồi muộn bị bỏ. Word lookup nối producer frozen/kho public qua IPC harness: found 8, full 3001, Tab/ShiftTab/Esc và đóng/reopen origin đạt, không gửi lệnh lưu. npm 403/0, renderer 90/0; 7 nhóm mutation bắt đủ các sửa; Python 294/2 skip symlink; examples 82/0. D1/D2 và confirm reject chỉ là nhánh API/dependency chưa có đường UI production chứng minh, ghi deferred, không thêm luật. Đã cập nhật spec và decision-47. Hạn kiểm: chưa build installer Electron toàn bộ hoặc kiểm mọi nghiệp vụ văn phòng; đã kiểm component thật và producer frozen. Evidence .agents/fix-task3-4-20261005/RESULT.md. Không commit/push.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Nút Tra/Copy và full đúng spec, gồm ô Nơi niêm yết trong Word; hết các lỗi có bằng chứng P4-P9/P11/P12 và lỗi phát sinh trong review. 403 npm/90 renderer đạt; native Electron hai cỡ màn hình, clipboard, keyboard, nháp và producer frozen/kho thật đạt. Mutation bắt lỗi cũ; giới hạn/deferred ghi riêng trong RESULT.md. Nghiệm thu 06/10/2026.
<!-- SECTION:FINAL_SUMMARY:END -->

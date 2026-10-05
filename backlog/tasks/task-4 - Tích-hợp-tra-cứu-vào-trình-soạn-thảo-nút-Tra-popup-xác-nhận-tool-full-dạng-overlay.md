---
id: TASK-4
title: >-
  Tích hợp tra cứu vào trình soạn thảo: nút Tra, popup xác nhận, tool full dạng
  overlay
status: To Do
assignee: []
created_date: '2026-10-05 01:08'
labels:
  - address-lookup
  - shared-core
  - ui
dependencies: []
references:
  - docs/spec/shared/administrative-lookup.md
  - docs/spec/notary_v2/administrative-address.md
  - contracts/notary-case-drafting.md
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Phụ thuộc TASK-3 (lõi + contract v2): làm sau khi lõi chạy. Phần giao diện của lõi tra cứu (spec docs/spec/shared/administrative-lookup.md, Owner duyệt 05/10/2026, TASK-2). Chỉ tra khi bấm nút Tra — không tự tra khi gõ/dán/rời ô. Kết quả copy được, máy KHÔNG tự ghi đè hay nối vào ô. Khi lõi trả too_many (>10, chỉ drafting): hiện popup "Nhiều kết quả khớp. Xem đầy đủ?"; đồng ý mới mở tool tra cứu full dạng popup overlay đè lên màn hình — không chuyển màn hình, không mất nháp/con trỏ/chữ đang nhập; hủy thì ở lại. Vị trí nút Tra và bố cục popup còn mở ở spec — hỏi Owner trước khi chốt.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Mỗi ô địa chỉ trong hồ sơ có nút Tra; chỉ bấm mới gọi notary.address_lookup với presentation=drafting và đúng chữ trong ô
- [ ] #2 Không tự tra khi gõ, dán, rời ô, hover; kết quả hiển thị copy được và không tự sửa nội dung ô
- [ ] #3 too_many: không hiện dòng kết quả nào, hiện popup "Nhiều kết quả khớp. Xem đầy đủ?"; đồng ý mở tool full bằng popup overlay với cùng query (presentation=full); hủy ở lại
- [ ] #4 Đóng popup overlay trả về đúng màn hình: giữ nguyên chữ đang nhập, nháp chưa lưu, vị trí con trỏ
- [ ] #5 Ô nơi cấp giấy khai tử tra xã mới từ địa chỉ người chết (không phụ thuộc ngày) theo spec notary_v2/administrative-address.md
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->

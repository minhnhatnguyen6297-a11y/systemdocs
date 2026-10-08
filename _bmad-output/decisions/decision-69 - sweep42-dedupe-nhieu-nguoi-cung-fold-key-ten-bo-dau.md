---
id: decision-69
title: "sweep42: dedupe nhieu nguoi cung fold-key ten bo dau"
status: Accepted
date: '2026-10-11'
---

## Context

`4. Văn bản cam kết về tài.doc` (THỪA KẾ 2026): 2 chị em `Vũ Thị Lanh`
(1986, CCCD ...1854) và `Vũ Thị Lành` (1984, CCCD ...4148) — tên bỏ dấu
(fold) rơi cùng một khoá dedupe. Mỗi người xuất hiện 2 lần trong văn bản
(khối chi tiết đủ giấy tờ + danh sách tóm tắt `Hộ gia đình` chỉ có
`Sinh năm`). `seen_person` chỉ giữ 1 base/khoá: bản `Lành` (mâu thuẫn)
ghi đè `Lanh`, khiến bản tóm tắt `Lanh 1986` so sánh nhầm với `Lành`
→ 4 bản ghi thay vì 2 → R05 báo oan.

## Decision

Mỗi khoá fold giữ **danh sách** bản ghi riêng biệt; bản mới gộp vào bản
đầu tiên không mâu thuẫn (cùng CCCD hoặc ngày sinh tương thích), chỉ thêm
bản mới khi không có base nào hợp — luật mâu thuẫn giữ nguyên.

## Evidence

- `ben_a` còn đúng 6 người (không trùng): `Đỗ Thị Đợi`, `Vũ Thị Lanh`
  `09/10/1986`, `Vũ Thị Lành` `15/02/1984`, `Vũ Thị Hợi`,
  `Vũ Thị Thu Hiền`, `Vũ Văn Luỹ` — R05 hết.
- Test: `test_dedupe_ten_gan_giong_nhau_khong_mat_ban_tom_tat` (90 pass).
- Mirror `regex-test-tool/tool/extract_contract.py` đồng bộ (diff rỗng).

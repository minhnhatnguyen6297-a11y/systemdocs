---
id: decision-65
title: "sweep36: tien to so thu tu truoc vai tro 'Nguoi chong/vo -'"
status: Accepted
date: '2026-10-11'
---

## Context

`cam kết ts riêng.docx` (HỢP ĐỒNG 2026/CHUYỂN NHƯỢNG) — R02 `0 người`: nguồn
ghi `1. Người chồng – Vũ Văn Khoan; Sinh ngày:...` và `2. Người vợ - Nguyễn
Thị Chiến; Sinh ngày:...`. `lead_role_re` nhận vai trò đứng đầu dòng nhưng
thiếu tiền tố số thứ tự `1.` nên cả 2 người bị sót.

## Decision

`lead_role_re` chấp nhận tiền tố `[\d+]`/`N.` trước `(Người) (vợ|chồng|con|mẹ|
bố|cha) - <tên trần>` — vẫn yêu cầu dòng có dấu hiệu người (ngày sinh/giấy tờ/
địa chỉ) như trước.

R05 `trùng tên` trên tờ khai thuế TNCN giữ nguyên: cùng người đứng 2 vai
(`[04] Tên người nộp thuế` + `[33] Họ và tên đại diện` phần NGƯỜI NHẬN), khối
sau không có giấy tờ để gộp chắc — cảnh báo trung thực cho người kiểm tra.

## Evidence

- `Vũ Văn Khoan` (Ông, 01/01/1962, CCCD `036062020689`) + `Nguyễn Thị Chiến`
  (Bà, 02/11/1960, CCCD `036160018620`), địa chỉ chung `Xã Vũ Dương, tỉnh Ninh
  Bình` áp cho cả hai.
- Test: `test_so_thu_tu_truoc_vai_tro_nguoi_chong` (86 pass).

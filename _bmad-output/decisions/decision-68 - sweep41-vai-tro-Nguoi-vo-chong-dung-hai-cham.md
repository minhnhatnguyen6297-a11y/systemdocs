---
id: decision-68
title: "sweep41: vai tro 'Nguoi vo/chong:' dung hai cham"
status: Accepted
date: '2026-10-11'
---

## Context

`Cam kết tài sản riêng Hùng Mai.doc` và `phiếu yccc cam kết ts riêng.docx`
(Hưng 2025): R02 `0 người` — nguồn ghi `Người vợ:  bà Phạm Thị Nụ` /
`Người chồng: ông Lê Ngọc Trình` — vai trò đứng đầu dùng **hai chấm** thay
gạch ngang, header_re chỉ nhận `[-–]`.

## Decision

Tiền tố vai trò `(người )?(vợ|chồng)` trong header_re chấp nhận `:` bên cạnh
`-`/`–`.

## Evidence

- `Phạm Thị Nụ` + `Lê Ngọc Trình` ra đủ ngày sinh/CCCCD/địa chỉ trên cả 2 file.
- Test: `test_vai_tro_hai_cham_nguoi_vo_chong` (89 pass).

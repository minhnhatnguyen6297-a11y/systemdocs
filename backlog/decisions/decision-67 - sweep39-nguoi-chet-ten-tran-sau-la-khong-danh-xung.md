---
id: decision-67
title: "sweep39: nguoi chet ten tran sau 'la' khong danh xung"
status: Accepted
date: '2026-10-11'
---

## Context

`Văn bản từ chối Trích lại.doc` (THỪA KẾ 2026): R06 báo oan — nguồn ghi
`Bố đẻ của tôi là Trần Văn Phúc, sinh năm 1910, đã chết ngày 19/04/1998 theo
trích lục khai tử số 17/2025/TLKT-BS`. Tên trần sau `là`, không có `Ông/Bà`
nên `death_re` trật.

## Decision

Nhóm danh xưng trong `death_re`/`death_paren_re` chấp nhận thêm `là` như
tiền tố giả — `là <Tên>, sinh năm..., đã chết ...` vẫn là người chết. Khi
tiền tố là `là`, `gioi_tinh` để trống (không suy Bà như trước).

## Evidence

- `Trần Văn Phúc`: sinh 1910, chết 19/04/1998, TLKT `17/2025/TLKT-BS`.
- Test: `test_nguoi_chet_ten_tran_sau_la` (88 pass).

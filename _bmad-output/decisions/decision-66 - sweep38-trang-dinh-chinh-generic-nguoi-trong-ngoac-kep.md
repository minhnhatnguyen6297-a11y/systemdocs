---
id: decision-66
title: "sweep38: trang DINH CHINH -> generic; boc ten trong ngoac kep; merge ngay day du"
status: Accepted
date: '2026-10-11'
---

## Context

`Đính chính.doc` (THỪA KẾ 2025): trang `ĐÍNH CHÍNH VĂN BẢN THOẢ THUẬN PHÂN
CHIA DI SẢN` — chỉ liệt kê nội dung cũ/đổi thành (`“Bà Nguyễn Thị Năm – Sinh
năm 1958”` → `“Bà Nguyễn Thị Năm – Sinh ngày: 25/12/1958”`), không có khối
đương sự/người chết/tài sản riêng. Bị nhầm `inheritance_partition` → R06+R08
báo oan; tên trong ngoặc kép không bóc được; khi gộp, `Sinh năm 1958` thắng
`Sinh ngày: 25/12/1958` mất dữ liệu.

## Decision

- `dinh chinh` ở đầu tiêu đề hoặc 6 dòng đầu → `generic` (cùng cơ chế
  `Lời chứng`/`Trang sửa lỗi kỹ thuật`).
- `header_re` chấp nhận `“ ” "` trong tiền tố rác đầu dòng và sau số thứ tự —
  `1. “Bà X – Sinh năm Y”` bóc được người.
- Dedupe cùng tên: `ngay_sinh` chỉ-năm được nâng lên ngày đầy đủ cùng năm
  (`1958` → `25/12/1958`), `chi_co_nam_sinh` tắt.
- R10 `469 != 496` trên `Chuyển nhượng Lượt.doc` giữ nguyên: dòng chính không
  mục đích, nguồn thật thiếu 27 m² chi tiết — cảnh báo trung thực.

## Evidence

- `generic`, 4 người ra đủ ngày đã đính chính; R06/R08 hết, còn R03 trung
  thực (trang đính chính không ghi CCCD/địa chỉ).
- Test: `test_trang_dinh_chinh_nhan_nguoi_trong_ngoac_kep` (87 pass).

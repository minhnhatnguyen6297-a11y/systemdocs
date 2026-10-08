---
id: decision-63
title: "sweep33: R10 - bang GCN 2 dong co chi tiet < tong la hop le"
status: Accepted
date: '2026-10-11'
---

## Context

`1. HĐ Tặng cho thanh tuấn.docx`: bảng GCN ghi thửa 143 = 200 m² (`Đất ở`, Lâu dài)
trên dòng chính; dòng phụ chỉ ghi `160 | Đất vườn | 12.2043`. Phần đất ở 40 m² là
hiệu số ngầm, không ghi thành số — parser gom `160 Đất vườn` vào `chi_tiet` và
luật R10 so `160 != 200` → báo oan.

## Decision

R10 (`luat_lech_dien_tich`) chỉ flag khi:
- tổng `chi_tiet_dien_tich` **lớn hơn** tổng thửa (dữ liệu thật sự mâu thuẫn), hoặc
- tổng chi tiết khác tổng **và** thửa không có `muc_dich_su_dung` ở dòng chính
  (không có phần dư ngầm để giải thích).

Khi `chi_tiet < tong` và dòng chính đã có mục đích sử dụng → phần dư hiểu là mục
đích chính, không flag. Ca đúng-thật `475 != 565` (Thoả thuận phân chia, thửa
không mục đích chính) vẫn báo.

## Evidence

- Nguồn: `HỢP ĐỒNG 2025/TẶNG CHO/1. HĐ Tặng cho thanh tuấn.docx` — ô bảng
  `9 | 143 | 200 | Đất ở | Lâu dài` + `160 | Đất vườn | 12.2043`.
- Test: `test_lech_dien_tich_bang_gcn_hai_dong_khong_bao` trong
  `tests/test_kiem_tra_trich_xuat.py` (cả 3 chiều: nhỏ+đủ mục đích → sạch;
  lớn hơn → flag; thiếu mục đích chính → flag).

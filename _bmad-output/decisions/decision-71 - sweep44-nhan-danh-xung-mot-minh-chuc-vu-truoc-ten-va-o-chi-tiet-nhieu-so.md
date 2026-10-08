---
id: decision-71
title: "sweep44: nhan danh xung mot minh + Chuc vu: Ong X + o chi tiet nhieu so"
status: Accepted
date: '2026-10-11'
---

## Context

- `MB 02 - BBĐG.doc` + `PHIEU KHAO SAT GIA TSBD1.doc` (THẾ CHẤP 2026):
  `Ông: Triệu Tuấn Anh` đứng một mình (không giấy tờ/chức vụ trên cùng
  khối) bị cổng lọc "phải có sinh/ID/chức vụ" loại → thiếu thành viên tổ
  định giá; `Chức vụ: Ông Nguyễn Hữu Công` có danh xưng giữa dòng sau
  nhãn chức vụ cũng sót.
- `thoả thuận phân chia di sản ông Độ.docx` (THỪA KẾ 2025): bảng GCN gộp
  2 dòng chi tiết vào 1 ô `Trong đó 324,9 46,8 | Đất ở Vườn | Lâu dài
  2043` — chi tiết đọc là 1 giá trị → R10 báo oan `324.9 != 371.7`.

## Decision

- Ô nhãn `Ông:`/`Bà:` đứng một mình đầu dòng được tính là người (labeled)
  dù không trường nào khác.
- `Chức vụ|Chức danh: (Ông|Bà) <tên>` nhận người, giới tính theo danh
  xưng.
- Ô `dien_tich` chi tiết chứa nhiều số trần (không chữ) thì tách: số đầu
  giữ mục đích gốc, số sau thành chi tiết riêng.

## Evidence

- BBĐG + khảo sát: đủ 4/3 thành viên (`Triệu Tuấn Anh`, `Nguyễn Văn Chí`,
  `Phạm Văn Quang`, `Nguyễn Hữu Công`).
- `ông Độ`: chi tiết `324,9 + 46,8 = 371,7` — R10 hết.
- Test: `test_nhan_danh_xung_dung_mot_minh_ong_hai_cham`,
  `test_nhan_chuc_vu_truoc_danh_xung`,
  `test_chi_tiet_o_nhieu_so_tach_thanh_nhieu_dong` (95 pass).
- Mirror đồng bộ (copy nguyên canonical, diff rỗng).

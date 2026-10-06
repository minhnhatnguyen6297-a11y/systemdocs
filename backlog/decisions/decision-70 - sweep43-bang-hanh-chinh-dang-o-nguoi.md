---
id: decision-70
title: "sweep43: bang hanh chinh dang o - nguoi theo hang STT | Ong/Ba"
status: Accepted
date: '2026-10-11'
---

## Context

`5. Danh sách người sử dụng chung thửa đất.doc` (TẶNG CHO 2025) bị R00 bỏ
qua dù bảng liệt kê 2 người đủ CCCD; 2 biên bản họp HĐTV (THẾ CHẤP 2026)
R02 0 người dù bảng thành viên rõ. Dạng ô `STT | Ông/Bà X | <ô>` chưa có
đường bóc — năm sinh là ô trần, số giấy tờ/ngày cấp/nơi cấp/địa chỉ theo
vị trí cột.

## Decision

Thêm đường bóc hàng-bảng: neo `STT | Ông/Bà`, ô năm trần -> ngay_sinh
chỉ-năm, ô 9-12 số -> cccd, `do X cấp ngày` -> noi_cap/ngay_cap, ô sau
ngày cấp trần -> noi_cap, ô từ hành chính (trừ `xã hội`) -> dia_chi; bỏ ô
nhãn cột, ô `ngày … năm` và đuôi `Người kê khai`; hàng không giấy tờ vẫn
tính khi có ô chức vụ (`thành viên/chủ tịch/...`); ô không vượt `\n` nên
hàng kết trước hàng kế.

## Evidence

- `Danh sách`: `Trương Anh Dũng` 1955 + `Trương Ngọc Mạnh` 1970 đủ CCCD/
  ngày cấp/nơi cấp/địa chỉ — R00 hết (file không còn bị bỏ qua).
- `BM01e` + `BB HOP HĐTV`: 3 thành viên mỗi file (Công/Hà/Oanh).
- Test: `test_bang_danh_sach_nguoi_su_dung_chung_o_tron`,
  `test_bang_thanh_vien_hdtv_khong_cot_giay_to` (92 pass).
- Mirror đồng bộ (diff rỗng).

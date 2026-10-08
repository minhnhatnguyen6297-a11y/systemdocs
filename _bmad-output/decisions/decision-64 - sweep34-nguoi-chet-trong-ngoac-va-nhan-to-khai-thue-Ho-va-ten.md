---
id: decision-64
title: "sweep34: nguoi chet trong ngoac gop + to khai thue [NN] Ho va ten"
status: Accepted
date: '2026-10-11'
---

## Context

2 lỗi thật ở đợt quét offset 330 (folder `HỢP ĐỒNG ĐÃ XONG 2025`):

1. `117.2025 từ chối Dung, Quế.doc` — R06 báo oan: nguồn ghi
   `Bố chúng tôi là ông Đỗ Đình Thắm (sinh năm 1956, đã chết ngày 16/01/2025)
   theo Trích lục khai tử`. Cụm `sinh năm + chết ngày` nằm **trong ngoặc** nên
   `death_re` nuốt vào nhóm `alias`, phần `chết` bắt buộc phía sau trật.
2. `phi nông nghiệp.docx` — R02 `0 người`: tờ khai thuế mẫu `[NN]` mới, dùng
   nhãn `[04] Họ và tên:`, `[05] Ngày/tháng/năm sinh:`, `[10.x]` ô địa chỉ con —
   các nhãn này chưa được nhận.

## Decision

- Thêm `death_paren_re` song song `death_re`: nhận
  `(Sinh năm N, đã chết ngày D)` gộp trong ngoặc; merge 2 danh sách match theo
  vị trí, truy cập nhóm qua `groupdict()` để 2 pattern khác nhóm không vỡ.
- `labeled_name_re` chấp nhận thêm nhãn `Họ và tên:`; `birth_re`/`birth_year_re`
  thêm biến thể `Ngày/tháng/năm sinh:`.
- Địa chỉ ô con tờ khai: chỉ gộp các `[P.x]` cùng số `P` với nhãn cha
  `[P] Địa chỉ ...` (tránh `[17.x]` địa chỉ thửa đất), bỏ giá trị là hậu tố đã
  có sẵn — `Tổ 8, Thị trấn Lâm, huyện Ý Yên, tỉnh Nam Định` không bị nối lặp
  `huyện Ý Yên`/`tỉnh Nam Định`.
- `_DIA_CHI_LABEL` thêm `Địa chỉ cư trú`.

## Evidence

- `Đỗ Đình Thắm` ra đúng: sinh 1956, chết 16/01/2025, TLKT `04/TLKT-BS`.
- `Ngô Xuân Ninh` ra đủ: 11/3/1987, CCCD `036087006087`, cấp 08/05/2021,
  địa chỉ `Tổ 8, Thị trấn Lâm, huyện Ý Yên, tỉnh Nam Định`.
- Test: `test_nguoi_chet_ngoac_gop_sinh_va_chet`,
  `test_to_khai_thue_ho_va_ten_nhan_nguoi` (85 pass).

---
id: decision-owner-gate-inventory-rulings-20261023
title: "Chốt từng mục bản thống kê chốt chặn Soạn hồ sơ: gần như bỏ chặn hết, lỗi đỏ tại ô lỗi"
date: '2026-10-23'
status: accepted
---

## Bối cảnh

Owner duyệt từng mục bản thống kê 60 quy tắc chốt chặn trong Soạn hồ sơ
(`_bmad-output/tmp/gate-inventory-soan-ho-so-20261023.md`) trong chat
23/10/2026 và chốt các mục dưới đây. Các mục chưa ghi ở đây (phần W và một số
mục R/S còn lại) giữ nguyên trạng cho tới khi owner chốt tiếp.

## Triết lý tổng (áp cho mọi mục)

- **Gần như bỏ chặn hết.** User tự chịu trách nhiệm nếu nhập sai hoặc thiếu
  thông tin. Kể cả trường trống cũng **không chặn xuất dữ liệu vào
  placeholder** — lỗi hiện ra trong văn bản Word là đủ.
- Chỉ giữ chặn tối thiểu khi rule đủ rõ và gọn.
- **Lỗi ở đâu báo đỏ ở đó:** mỗi lỗi phải trỏ đúng ô/thẻ chứa lỗi; không
  thông báo chung chung khiến user không xác định được lỗi ở đâu.
- **Vùng thông báo không được đẩy/xô lệch các phần UI khác** khi hiện lên.
- Giao diện luôn hướng **tối giản, thoáng nhất có thể** — một màn hình đã
  chứa rất nhiều chức năng (xem thêm R16).

## Các chốt theo mục

- **R12 — BỎ.** Bỏ công thức thông báo lỗi dài (tiêu đề + câu hướng dẫn +
  mã kỹ thuật) của catalog lỗi.
- **R14 — Bỏ text báo thành công, thay bằng tín hiệu trực quan.** Lược bỏ
  thông báo chữ sau thao tác thành công tới mức tối đa; thay vào đó các hành
  động như OCR, phân tích Word, engine tính thừa kế… phải có **UI loading
  trong lúc chạy và dấu tích xanh khi thành công** để user thấy trực quan.
- **R15 — Zalo là chức năng chưa ban hành.** Nút Zalo disable thường trực
  không được coi là tính năng đang có.
- **R16 — BỎ TOÀN BỘ chữ hướng dẫn tĩnh trên màn hình.** Ghi thành nguyên
  tắc thiết kế đứng: giao diện tối giản, thoáng nhất có thể vì một màn hình
  đã chứa sẵn rất nhiều chức năng.
- **S1 — Bỏ chặn.** Hồ sơ mới không còn bị bắt buộc ≥1 Người + ≥1 Tài sản
  mới Lưu được.
- **S2 — Bỏ chặn.** Chưa chọn người để lại vẫn Lưu được.
- **S3 — Bỏ chặn.** Thiếu Chủ đất không còn chặn Lưu.
- **S4 — Bỏ chặn + SỬA SPEC.** D quyết
...[truncated 2567 chars]
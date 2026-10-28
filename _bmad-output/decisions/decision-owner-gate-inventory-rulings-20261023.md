---
id: decision-owner-gate-inventory-rulings-20261023
title: "Chốt từng mục bản thống kê chốt chặn Soạn hồ sơ: gần như bỏ chặn hết, lỗi đỏ tại ô lỗi"
date: '2026-10-23'
status: accepted
---

## Bối cảnh

Owner duyệt từng mục bản thống kê 60 quy tắc chốt chặn trong Soạn hồ sơ
(`_bmad-output/tmp/gate-inventory-soan-ho-so-20261023.md`) trong chat
23/10/2026 và chốt các mục dưới đây. Phần W được owner chốt bổ sung cùng
ngày (xem mục W bên dưới). Một số mục R/S/N chưa nhắc tới đi theo khuyến
nghị trong bản thống kê khi triển khai.

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
- **S4 — Bỏ chặn + SỬA SPEC.** Dòng Người cho phép để trống tất cả các
  trường **trừ họ tên** — họ tên là mức tối thiểu để dòng có tên thẻ. Spec
  liên quan phải sửa theo quyết định này.
- **S5b — Gỡ chặn + SỬA SPEC.** Dòng Tài sản chỉ giữ mức tối thiểu 2
  trường: **số thửa đất** và **số tờ bản đồ**; các trường còn lại cho phép
  trống. Chuỗi rỗng ở các trường chữ tùy chọn được chuẩn hóa thành null khi
  ghi, không chặn Lưu. Spec liên quan phải sửa và hết tự mâu thuẫn.
- **S5c — Bỏ chặn.** Ngày cấp của Tài sản chấp nhận dạng chỉ-năm như các
  trường ngày của Người.
- **S6 — Bỏ chặn.** Các chặn ở cụm đất (land_rows) trong đường Lưu được
  gỡ theo triết lý tổng.
- **S7 — Trần 5 tài sản, thống nhất mọi tầng.** Owner chốt trần 5 tài
  sản (client, server và tầng Word dùng cùng một con số); phần diện tích
  giao diện cho 5 tài sản owner tự giải quyết sau.
- **R7 — Chuẩn hóa UI đổi loại; KHÔNG làm nhiều diagram trong một hồ
  sơ.** Kiểm chứng khả thi (biên bản
  `_bmad-output/tmp/feasibility-r7-s10-s17-r11-20261023.md`): nhiều
  diagram/tab trong một hồ sơ là thay đổi lớn (~200 điểm đọc `case_type`,
  loại hồ sơ là thuộc tính của cả hồ sơ, mỗi hồ sơ đúng một state sơ đồ)
  nên bỏ qua theo đúng điều kiện owner đặt. Chuẩn hóa tối thiểu thay thế:
  dời nút chọn loại diagram xuống header của vùng Sơ đồ, một kiểu UI cho
  cả hồ sơ mới và hồ sơ cũ; dialog đổi loại giữ đúng 3 hạng mục có lý do
  cơ chế (văn bản mới; người để lại khi sang thừa kế; xác nhận xóa sơ đồ
  cũ) và bỏ cửa "bắt Lưu trước".
- **S10 + S16 — Quan hệ sơ đồ phải thành trường chuẩn; đã kiểm chứng, có
  gap, mở issue #45.** Triết lý owner (product overview): sơ đồ là trải
  nghiệm kéo thả của user, hệ thống chuyển các mối quan hệ của sơ đồ thành
  trường chuẩn trong hồ sơ; quan hệ chỉ do engine diagram tự quản mà
  không lưu database là dữ liệu mồ côi. Kiểm chứng 23/10: quan hệ có
  chiếu xuống bảng `inheritance_participants` mỗi lần Lưu và Word điền
  placeholder vợ/chồng từ bảng đó, nhưng `vai_tro` của dòng đã tồn tại
  không được cập nhật theo sơ đồ mới ở các lần Lưu sau, và thiếu neo cặp
  vợ–chồng theo nhánh — đã mở issue #45
  (`bug-participant-role-projection-stale-spouse-anchor`).
- **Phần W — Xuất Word làm đến cùng triết lý: có gì xuất đó.** Owner chốt
  bổ sung 23/10: xuất Word kể cả khi hồ sơ không có đủ thông tin — thiếu
  dữ liệu không chặn xuất; phần thiếu/lỗi bộc lộ trong file Word và danh
  sách kết quả xuất, không chặn trước ở dialog. Hệ quả khi triển khai:
  gỡ các chặn readiness theo dữ kiện thiếu (W6/W8 dạng chặn), gộp chuỗi
  thao tác xuất gốc thành một hành động "Lưu & xuất" (W2), xuất theo nội
  dung hiện tại thay vì lặng lẽ xuất bản đã lưu cũ (W3), bỏ nút "Lưu nơi
  niêm yết" riêng trong dialog (W4), bỏ chữ hướng dẫn trong dialog nhưng
  giữ tiến trình và kết quả (W9).

## Trạng thái các mục còn lại

- Các mục owner chưa nhắc đích danh (R1–R5, R13, S8/S9/S11–S15, S19/S20,
  phần N) đi theo khuyến nghị trong bản thống kê khi triển khai; phát
  hiện lệch khuyến nghị thì báo lại owner trước khi làm khác.
- S17 đã kiểm chứng: danh bạ người nhận ủy quyền dùng chung bảng
  `customers` toàn app; chức năng thêm người vào danh bạ đã có (nút
  "+ Danh bạ" trong màn soạn, tạo dòng tối thiểu chỉ họ tên).
- R11 đã kiểm chứng: trần 8 nguồn Word là hằng số kỹ thuật tự đặt trong
  code, không có quyết định nghiệp vụ nào của owner làm căn cứ.

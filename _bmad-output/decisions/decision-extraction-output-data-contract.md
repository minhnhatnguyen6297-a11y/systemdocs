---
id: decision-extraction-output-data-contract
title: 'Owner: chốt nguyên tắc đầu ra bóc tách theo nhóm đích lưu'
date: '2026-10-14'
status: accepted
---

## Context

Owner yêu cầu “duyệt, kiểm tra lại toàn bộ docs, chú ý các khái niệm, định
nghĩa, lý giải có mâu thuẫn” và đã duyệt nguyên tắc chuẩn đầu ra bóc tách.

## Decision

- Trước khi triển khai, chốt bộ trường, kiểu dữ liệu, định dạng, cách nhóm và
  nơi lưu cho chức năng nhận dữ liệu; cùng một đối tượng dùng cùng chuẩn đích
  trong suốt luồng.
- Giữ riêng và nguyên vẹn giá trị gốc (raw) cùng vị trí nguồn. Chuẩn hóa giá trị
  đầu ra theo quy tắc của từng trường; trường nào yêu cầu nguyên văn thì giữ
  nguyên. Mục đích là tránh cùng thông tin cho kết quả khác nhau giữa các trường
  hoặc khiến trường cần thiết không điền/lưu được, mà không tự thêm quy tắc ngoài
  những gì đã chốt.
  Dữ liệu phải gắn đúng người, tài sản hoặc cụm đất; không ghép dữ liệu mồ côi,
  tạo field riêng hoặc nhét dữ liệu vào ghi chú.
- Giữ mapping đã chốt giữa tên nghiệp vụ và tên cột/API; ví dụ `ten` và
  `ho_ten` không phải lý do để đổi hàng loạt schema. Thời hạn đất thuộc đúng
  cụm và tài sản, không đổ vào `thoi_han` chung.
- Thiếu căn cứ thì để trống và gắn cờ theo quy ước. Field mới cần được đề xuất
  và chốt trước khi triển khai.
- Dữ liệu đúng cấu trúc chưa đồng nghĩa đã xác nhận hoặc được tự ghi DB. Không
  ép raw OCR vào schema DB, không tạo schema dùng chung hoặc Case liên module.

## Scope

Nguyên tắc này ghi tại [_bmad-output/specs/README.md](../specs/README.md) §§2,
4.2. Nó không phê duyệt các quy tắc đang Draft/chờ Owner, không đổi schema hay
mapping đã chốt, và không xác nhận hiện trạng runtime.

---
id: decision-gcn-serial-stage-persistence-20261020
title: >-
  Serial GCN Stage giữ nguyên văn; persistence nullable/non-unique, migration
  tại chỗ giữ ID/link
date: '2026-10-20'
status: accepted
---

## Context

Owner đã chốt 06/10/2026 (decision-46, entities.md §2, contract §6.1): serial GCN
là chuỗi nguyên văn ở mọi tầng, có thể rỗng/trùng, không chuẩn hóa, không thay
`XX`. Audit tĩnh #40 và repro runtime 20/10/2026 trên DB tổng hợp cô lập xác
nhận Stage vẫn chặn ba ca, DB mới tạo `NOT NULL/UNIQUE`, đường đọc thay `XX`,
và upsert ghép tài sản theo serial. Không có câu hỏi nghiệp vụ mới.

## Decision

1. Bỏ validator serial và `_canonical_serial`; Stage chỉ kiểm kiểu `str`.
2. `_asset_wire` trả nguyên văn; DB NULL đọc thành chuỗi rỗng trên wire.
3. `_upsert_assets` chỉ liên kết theo `entity_id`; không tìm master theo serial.
4. `properties.so_serial` nullable, bỏ unique. Migration SQLite rebuild bảng tại
   chỗ qua `properties_serial_new`, copy đủ cột/ID, giữ `inheritance_case_properties`
   và `property_land_rows`, một transaction, rollback khi lỗi, idempotent.
5. Các write path serial còn lại (properties router/form, mock adapter) theo cùng
   quy tắc để không hình thành chuẩn thứ hai.

## Alternatives rejected

- Giữ `UNIQUE` và thêm hậu tố/nhân bản mã: vi phạm serial nguyên văn, đổi dữ liệu.
- Chỉ xóa unique index: SQLite không bỏ được `NOT NULL`; DB mới vẫn sai.
- Thêm bảng/cột serial riêng: tạo trường mồ côi, trái contract canonical.
- Viết lại serial cũ sang dạng chuẩn: xóa bằng chứng nguồn.

## Consequences

DB cũ và DB mới cùng semantics; không đổi ID/khóa ngoại/giá trị cũ. AC5 không
áp dụng vì repro đã chứng minh consumer hiện hành sai. Plan và evidence:
`_bmad-output/backlog/bug-stage-raw-gcn-serial-contract-plan.md`,
`_bmad-output/tmp/issue-40-repro/`. Owner duyệt cùng CHECKPOINT 1 ngày 20/10/2026; implementation và verification
được ghi trong plan/backlog #40.

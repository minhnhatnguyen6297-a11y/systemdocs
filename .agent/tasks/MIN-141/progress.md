# Progress — MIN-141

## Trạng thái: In Review

## Việc đã hoàn thành (2026-10-01)

1. **Rà soát & kiểm tra hệ thống:**
   - Đối chiếu các trường Người, Tài sản, Hồ sơ trong `notary_v2/models.py`, `database.py`, `services/case_workspace.py`, `services/word_engine.py`.
   - Xác định lỗi docstring lệch mốc 01/07/2024 trong `Customer._moc_cccd_moi`.
   - Xác định thiếu sót trong `Customer.loai_giay_to` và `noi_cap` khi xử lý trường hợp người đã chết (`con_song == False`).

2. **Triển khai code backend:**
   - Cập nhật docstring `Customer._moc_cccd_moi` về chuẩn 01/10/2024.
   - Bổ sung logic phân biệt người sống vs người chết trong `Customer.loai_giay_to` và `Customer.noi_cap`.
   - Bổ sung property `Customer.loaicutru` ("Cư trú" / "Thường trú").
   - Bổ sung các trường `nguoi_nhan_uy_quyen` và `noi_dung_viec` vào `InheritanceCase` (`models.py`) và hàm `migrate_inheritance_cases_schema` (`database.py`).
   - Chạy kiểm chứng logic qua Python thành công.

3. **Tạo Issue trên nền tảng Multica:**
   - Tạo thành công issue `NAIA-9` (ID: `01a0f67d-45a0-7c32-8de4-f93d778d7f25`) với tiêu đề: *"Xây dựng bảng dữ liệu chuẩn hóa xã/phường cũ - mới sau sáp nhập 01/07/2025"*.

4. **Cập nhật tài liệu Spec & Contract dài hạn:**
   - `contracts/entities.md`: Bổ sung §8 (Từ điển dữ liệu Người & trường suy ra) và §9 (Chuẩn hóa Tài sản, Hồ sơ & Quy tắc đặt tên).
   - `docs/spec/notary_v2/README.md`: Di chuyển mục từ điển dữ liệu Người sang phần "Đã chốt", cập nhật các quyết định 01/10/2026.
   - `docs/spec/notary_v2/stage.md`: Cập nhật mục 5 (Quy tắc dữ liệu), mục 9 (Giao diện 3 dòng hồ sơ dưới tài sản), mục 10 (Lịch sử).
   - `docs/spec/notary_v2/input/property-rules.md`: Bổ sung ghi chú loại bỏ trường lẻ `thoi_han` mồ côi ở cấp tài sản.

## Đợt 2 — cụm đất thành bản ghi DB (đang thực hiện)

Phạm vi theo review comment 29/09/2026 (Leader): lưu mỗi cụm đất thành một
bản ghi con thay vì JSON blob.

1. **Model + Migration (`models.py`, `database.py`):**
   - Bảng `property_land_rows(property_id, vitri, loaidat, dientich, thoihan)`,
     UNIQUE `(property_id, vitri)`; `Property.land_rows` cascade delete-orphan.
   - `migrate_property_land_rows(con=None)`: tạo bảng nếu thiếu, backfill từ
     `land_rows_json`, idempotent (skip property đã có dòng), giữ thứ tự + vị
     trí trống, giữ nguyên JSON gốc. Dữ liệu lỗi/quá giới hạn/mâu thuẫn alias
     → report `anomalies`, không cắt cụt, không DROP.
   - `MAX_LAND_ROWS = 20`.

2. **Case workspace (`services/case_workspace.py`):**
   - Đọc ưu tiên bảng con, fallback `land_rows_json` cho tài sản chưa migrate.
   - Chấp nhận cả key canonical (`loaidat/dientich/thoihan`) lẫn legacy
     (`loai_dat/dien_tich/thoi_han`); hai key mâu thuẫn → `stage_validation_error`
     code `conflict`, không chọn ngầm.
   - Commit ghi master + thay cụm đất + mirror JSON + snapshot đầy đủ +
     revision trong một transaction (clear → flush → insert tránh xung đột
     UNIQUE khi upsert).
   - Data warnings: `stage.orphan_thoi_han`, `stage.legacy_land_rows_invalid`,
     `stage.legacy_land_rows_overflow`.

3. **Word engine (`services/word_engine.py`):**
   - `build_word_context` đọc snapshot `case_state_json` đã commit trước,
     fallback master property sống — hai hồ sơ dùng chung tài sản không
     ảnh hưởng nhau.
   - Mỗi cụm dùng `thoihan` riêng; bỏ hẳn việc đắp `properties.thoi_han`
     lẻ vào `[Thờ hạn 1]`/cụm.

4. **Khởi tạo (`main.py`, `shell/sidecar/notary_adapter.py`):**
   - Web `_run_migrations` và sidecar `_ensure_db` cùng gọi
     `migrate_property_land_rows()`; bổ sung `migrate_zalo_exchange_schema()`
     còn thiếu trong sidecar.

5. **Contract/Spec:**
   - `contracts/notary-case-drafting/common.schema.json`: `land_row` nhận cả
     hai bộ key.
   - `contracts/notary-case-drafting.md`: §4.2/§13.3 — canonical keys,
     conflict → validation, `vitri = index+1`, tối đa 20, mirror JSON,
     snapshot-isolation cho Word, 3 warning mới.
   - `contracts/entities.md` §9.2 + `docs/spec/notary_v2/stage.md` +
     `docs/spec/notary_v2/input/property-rules.md`: ghi bảng con, bỏ alias
     rút gọn `loaidatM` (quyết định review 29/09/2026: chỉ `loaidat<M><N>`
     vì rút gọn trùng nghĩa `loaidat12`).

6. **Test (`tests/test_property_land_rows.py`, 25 test):**
   - Migration: tạo bảng + backfill thứ tự/khe trống, idempotent, không đè
     dòng do commit ghi, báo lỗi JSON/shape/row/số/conflict, overflow vẫn
     ghi đủ + báo, orphan `thoi_han`.
   - Commit: ghi bảng + mirror + snapshot atomic, edit/xóa/reorder, key
     canonical/legacy, conflict → reject, giới hạn 20, rollback nguyên
     transaction khi 1 dòng sai, 3 tài sản × 20 cụm lưu→mở lại.
   - Word: 2 hồ sơ dùng chung tài sản xuất đúng snapshot riêng; không đắp
     `thoi_han` lẻ vào cụm.
   - Wiring: `main.py`/sidecar gọi đủ migration; test sidecar chạy
     `_ensure_db` trên sqlite file thật kiểm bảng + UNIQUE.

### Bằng chứng kiểm thử đợt 2

- Branch: `agent/worker-nh-n-vi-c/1127ad7579d2` (base `64f4544`)
- cwd: `<repo>/systemdocs/notary_v2`
- `python -m pytest tests/test_property_land_rows.py -x -q` → **25 passed**,
  6 warnings (9.33s).
- `python -m pytest tests/ -q` (đầy đủ) → **576 passed**, 1 skipped;
  **8 failed đều pre-existing tại `64f4544`** (đã chạy lại trên worktree
  HEAD để đối chiếu): jinja2/starlette unhashable dict ở
  `test_customers_excel`, sha256 fixture POC ở `test_document_conversion_poc`,
  thiếu tzdata `Asia/Ho_Chi_Minh` + router zalo chưa wire ở `test_zalo_*`.
- cwd: `<repo>/systemdocs/shell`
- `python test/test_engine_adapters.py` → **14 tests OK** (gồm test mới
  `_ensure_db` tạo `property_land_rows` + đủ bảng Zalo trên sqlite thật).
- cwd: `<repo>/systemdocs`
- `python contracts/notary-case-drafting/validate_examples.py` → **68 files,
  0 unexpected outcomes**.

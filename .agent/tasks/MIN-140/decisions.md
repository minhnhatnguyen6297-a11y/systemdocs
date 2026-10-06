# Decisions — MIN-140

## D1 — Serial: verbatim lưu, match key chỉ để so khớp

Quyết định (owner 29/09/2026): serial nhập tự do, KHÔNG ép dạng
`XX123456`. Lưu/emit nguyên văn (trim 2 đầu). Vẫn cần nhận diện "cùng
property" khi user gõ khác khoảng trắng/hoa thường → `_serial_match_key`:
`re.sub(r"[^0-9A-Za-z]", "", v).upper()`, `None` khi kết quả rỗng.

Hệ quả:
- `_asset_wire` emit `_nn(prop.so_serial)` — hồ sơ legacy serial lạ emit
  nguyên văn, không còn surrogate `XX{id:06d}`.
- `_upsert_assets`: `entity_id` → serial match key (bảng properties scan
  so_serial non-null) → nếu không khớp thì tạo Property mới; ghi
  `prop.so_serial = serial` (verbatim).
- Dedupe trong payload so trên match key → `'XX 123456'` vs `'xx123456'`
  = trùng.
- `validate_examples.py` giữ `SERIAL_RX` nhưng CHỈ còn áp cho contract v1
  (non-draft) — v2 bỏ.

## D2 — Required fields theo ô nhập thật trên UI

Owner: "mọi trường thuộc người trên UI đều bắt buộc". Áp lên payload v2
(commit/create/evaluate-draft); kết quả get() từ hồ sơ cũ giữ nullable
(result rows vẫn emit null hợp lệ).

- `noi_cap`, `place_of_origin` KHÔNG có ô nhập trên bảng Người → tùy chọn
  (nullable string).
- `ngay_chet` tùy chọn — null = còn sống (đúng semantics model).
- `ngay_sinh`/`ngay_cap` người: `YYYY-MM-DD` hoặc `YYYY` (giữ
  `_valid_date_or_year` — ô nhập UI cho phép chỉ năm).
- `ngay_cap` tài sản: vẫn full ISO hoặc null (`_valid_date_full`) — theo
  contract cũ, MIN-140 không đổi.

## D3 — Không chặn chuyển tab

Owner chốt lại: không cần block khi đang sửa mà chuyển tab — draft Stage
là client buffer (`case-drafting-model.js`), chuyển tab không mất dữ
liệu. Validation chỉ chạy khi bấm Cập nhật / create. → Không thêm guard
nào ở topbar; chỉ bổ sung hiển thị `field_errors` của `land_rows` trên ô
"Loại đất" (trước đây lỗi này không có ô nào hiển thị).

## D4 — DB migration `properties.so_serial NOT NULL → NULL`

SQLite không `ALTER` nullability → `migrate_properties_serial_nullable()`
rebuild bảng: đọc `PRAGMA table_info` lấy đúng tập cột hiện có, tạo
`properties_new` schema mới, copy, rename, tạo lại index `ix_properties_id`,
cuối cùng `PRAGMA foreign_key_check`. Idempotent (skip khi cột đã
nullable). UNIQUE giữ nguyên — nhiều NULL hợp lệ theo semantics SQLite.
Gọi trong `main.py` trước `Base.metadata.create_all`.

## D5 — Phân biệt payload vs result trong validator/schema

`check_person_row(..., strict_v2=)` và `check_asset_row(..., in_payload=)`
chỉ siết required khi validate PAYLOAD (command `workspace_commit_stage`,
`workspace_create`, `diagram_evaluate` chế độ nháp). Result/job fixtures
giữ nullable — hồ sơ cũ emit null hợp lệ.

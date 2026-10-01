# Progress — MIN-140

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: xong implement + verify — 2026-10-01

## Đã làm

### Backend (`notary_v2`)

- `services/case_workspace.py`:
  - Bỏ `_SERIAL_RE`/`_canonical_serial`; thêm `_serial_match_key`
    (bỏ non-alnum + uppercase) dùng riêng cho so khớp.
  - `_asset_wire` emit serial verbatim (`_nn`), bỏ surrogate `XX%06d`.
  - `_validate_stage`: person bắt buộc `ho_ten`/`gioi_tinh`/`ngay_sinh`/
    `so_giay_to`/`ngay_cap`/`dia_chi` (`noi_cap`,`place_of_origin`,
    `ngay_chet` tùy chọn); asset bắt buộc `so_to_ban_do`/`so_thua_dat`/
    `dia_chi` + `land_rows` ≥1 dòng hợp lệ (`loai_dat` nonempty,
    `dien_tich` number); serial tùy chọn — chỉ check kiểu/không-rỗng +
    dedupe match key + "đã thuộc tài sản khác".
  - `_find_property_by_serial` scan `Property.so_serial` non-null, so
    match key; `_upsert_assets` ghi verbatim.
  - `_upsert_assets` wire emit `so_serial`/`dia_chi` theo giá trị persist.
- `models.py`: `Property.so_serial` → `nullable=True, unique=True`.
- `database.py`: `migrate_properties_serial_nullable()` rebuild bảng
  SQLite cũ (giữ unique, nhiều NULL hợp lệ, FK check sau migrate).
- `main.py`: gọi migration trước `create_all`.

### Mock (`shell/sidecar/notary_mock_adapter.py`)

- Bỏ `SERIAL_RX`/canonical check; serial tùy chọn, verbatim (trim).
- Person: 6 field bắt buộc; asset: số tờ/số thửa/địa chỉ + land_rows.
- Dedupe serial qua `_serial_match_key` parity backend.

### Renderer

- `case-drafting-view.js`: `cellErrs(a.row_id, 'land_rows', td)` dưới chip
  "Loại đất" — lỗi required/invalid của land_rows giờ hiển thị.
- Không thêm chặn chuyển tab (owner đã chốt không chặn — draft giữ trong
  model).

### Contract + spec

- `contracts/notary-case-drafting.md`: §13.3 (asset row/payload), §13.16
  (rule MIN-140), changelog.
- `draft-v2.schema.json`: `so_serial` nullable string, mô tả không-canonical.
- `validate_examples.py`: `strict_v2` person (`gioi_tinh`/`ngay_sinh`/
  `ngay_cap`/`so_giay_to`/`dia_chi` bắt buộc), asset `in_payload` (số tờ/
  số thửa/địa chỉ + land_rows ≥1 `loai_dat`+`dien_tich`); `SERIAL_RX` chỉ
  còn cho contract v1.
- `contracts/entities.md` §2: canonical chỉ là dạng so khớp, không phải
  rule đầu vào; raw serial lưu/emit nguyên văn.
- `docs/spec/notary_v2/stage.md`: nguyên tắc permissive + bảng required
  + serial verbatim + không chặn chuyển tab + position-1 = primary.
- `workspace-detail.md`: không có wording serial/required cũ cần sửa.

### Tests + fixtures

- `test_case_workspace.py`: `_person_row` thêm `so_giay_to` unique +
  `ngay_cap`; rewrite test serial canonical → free-form/null/match-key/
  dup-normalized; thêm test required person/asset, land_rows, serial ''
  bị chặn (dùng null), emit verbatim không surrogate, migration
  `migrate_properties_serial_nullable` + `nullable` trong model.
- `test_inheritance_workspace.py`: `_draft_stage` đủ field bắt buộc.
- `test_notary_mock_adapter.py`: `_mk_person`/`_mk_asset`/`_person`/
  `_asset` đủ field; rewrite `test_serial_must_be_canonical` →
  free-form + dup match key.
- `test_notary_adapter_contract.py`: `_person_row`/`_asset_row` đủ field.
- Fixtures: `ready.json` (person B + D đủ sgt/ngay_cap); 4 command
  `*.valid.json` trong `contracts/.../examples/draft-v2/`.

## Verify

- `pytest notary_v2/tests/test_case_workspace.py + test_inheritance_workspace.py`:
  **93 passed**.
- `pytest shell/test`: **364 passed**.
- `node --test` 3 file case-drafting (model/view/static): **141 passed**.
- `validate_examples.py`: **68 files, 0 unexpected**.
- `pytest notary_v2/tests` full: 536 passed; **8 fail + 1 deselect nhóm
  lỗi môi trường**, không liên quan diff:
  - `test_customers_excel` — jinja2/starlette mới (`unhashable dict` trong
    template cache).
  - `test_zalo_sync_api::test_main_app_wires_zalo_router` — starlette 1.7
    dùng `_IncludedRouter` lazy proxy → `.path` rỗng (test introspect
    `app.routes`).
  - `test_zalo_inbox` ×3 + `test_zalo_inbox_api` — batch async còn
    `processing` (timing) + env zalo.
  - `test_ocr_ai` — env legacy openai.
  - `test_document_conversion_poc` — sha256 golden manifest (env/POC).
  - `tests/test_customers_excel.py` deselect cả file (cùng lỗi jinja2).
  - `rapidfuzz` thiếu → đã cài `rapidfuzz==3.9.0` theo requirements.txt.
- `git diff --check`: sạch.

## Đang làm dở

- (không còn)

## Còn lại / lưu ý

- File rác `nul` ở root repo (0 byte, artifact redirect Windows) — đã xóa.
- `.agent/tasks/MIN-141/` untracked từ phiên trước — không thuộc ticket
  này, để nguyên.

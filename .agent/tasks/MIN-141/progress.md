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

### Đợt 2 — sửa lỗi review Leader (commit `f464b59`)

Leader review `7c43bef` chưa PASS; bốn sửa trong commit riêng:

1. `_asset_wire` đọc snapshot `case_state_json` khi snapshot đủ field
   nghiệp vụ (`_snapshot_has_asset_fields`, ngưỡng khớp word_engine) —
   Stage mở lại khớp Word; snapshot con trỏ vẫn fallback master.
2. `migrate_property_land_rows`: loaidat/thoihan sai kiểu (object/list/
   bool) → anomaly `invalid_field`; `_land_area_to_float` strict (bool,
   dict, inf/nan, chuỗi hỏng → `invalid_dientich`); giữ nguyên bản gốc,
   tiếp tục property khác; lỗi bất ngờ → rollback + đóng connection.
3. `_land_data_warnings` kiểm overflow trên nguồn thực đọc — bảng con
   >20 dòng vẫn báo `stage.legacy_land_rows_overflow`, không truncate.
4. `routers/properties.py inline_create`: validate land_rows theo luật
   Stage (dual key, conflict/sai kiểu/quá 20 → 400), ghi master + bảng
   con + mirror trong một transaction.

Bằng chứng (cwd `notary_v2/`):
- `pytest tests/test_property_land_rows.py tests/test_leader_review_probes.py -x -q` → **44 passed**
  (probe Leader 3/3 green; +6 case sai kiểu, reopen-commit noop giữ
  snapshot, pointer fallback, route create atomic + reject malformed).
- `pytest tests/test_case_workspace.py tests/test_word_engine.py -q` → **77 passed**.
- `pytest tests/ -q` (full) → **595 passed, 1 skipped, 8 failed** — 8 fail
  giống hệt baseline `64f4544`/`7c43bef` (customers_excel jinja2,
  doc_conversion_poc, zalo_*), không liên quan diff.
- cwd `shell/`: `python test/test_engine_adapters.py` → **14 ran, 14 OK,
  0 skipped** (môi trường local; review env của Leader báo 11 skipped —
  khác nhau ở optional deps).
- `python contracts/notary-case-drafting/validate_examples.py` → **68 files,
  0 unexpected outcomes**.

## Đợt 3 — người + hồ sơ xuyên backend–UI–Word (commit `ae5dd7a`)

1. **Person derived fields:** `loai_giay_to`/`loai_dia_chi` vào PERSON_FIELDS,
   wire + snapshot giá trị hiệu lực; người chết giữ evidence-only (không gán
   cứng), người sống suy từ `ngay_cap` qua mốc 01/10/2024, thiếu ngày → null.
   Canonical alias không dấu fold vào snake_case; hai alias khác nhau →
   `validation_error`.
2. **Case meta (6 trường):** `ngay_lap_ho_so`, `noi_niem_yet`,
   `nguoi_nhan_uy_quyen`, `nguoi_nhan_uy_quyen_id`, `noi_dung_viec`, `ghi_chu`
   nhận qua `payload.case` ở cả `workspace_create` lẫn `workspace_commit_stage`
   (cùng transaction Stage); `case_type`/`document_type` immutable; `uq_id`
   phải tồn tại trong `customers` + tên khớp master.
3. **Cột `nguoi_nhan_uy_quyen_id` thật** (FK customers) để đối chiếu danh bạ
   và phục vụ dọn dữ liệu đợt 4.
4. **Word engine:** đọc meta từ snapshot trước, DB fallback cho hồ sơ cũ;
   deceased clause xây từ trường đã xác nhận thay vì gán cứng.
5. **Sidecar + mock parity:** adapter truyền `payload.case`; mock có
   `_apply_case_meta`, canonical alias, danh bạ giả cho
   `notary.customer_list`/`customer_create` (route qua gateway).
6. **UI:** 3 dòng meta (Nơi niêm yết / Người nhận ủy quyền / Nội dung việc)
   dưới bảng tài sản; catalog ủy quyền có tìm kiếm + `+ Danh bạ`; input meta
   90% chiều cao input thường; defer `loadUqCatalog` sang microtask tránh
   render lồng nhau.
7. **Contracts:** doc + 4 schema JSON + validator + 68 ví dụ đồng bộ.

Bằng chứng đợt 3:
- focused backend 136 passed; sidecar/mock 190 passed; contract validator
  68 files 0 unexpected; JS renderer 124 passed (1 fail baseline
  `shell-chrome` thiếu `docs/product/ui/tokens.json`); full Python
  610 passed, 8 failed = baseline (excel jinja2, poc, zalo_*).

## Đợt 4 — dọn hồ sơ nháp reference-safe + thống kê gắn hồ sơ

1. **Xóa draft (`routers/cases.py`):** `_delete_case_and_unreferenced_masters`
   trong một transaction — xóa case (cascade participants/property_links),
   flush, rồi chỉ xóa master "thuộc hồ sơ" (người chết, tài sản chính,
   participant kể cả `parent_customer_id`, tài sản link phụ) khi KHÔNG còn
   tham chiếu sống: case khác (`nguoi_chet_id`/`tai_san_id`/
   `nguoi_nhan_uy_quyen_id`), participant còn lại (`customer_id`/
   `parent_customer_id`), `InheritanceCaseProperty` còn lại, hoặc snapshot
   `case_state_json`/`engine_state_json` của hồ sơ còn tồn tại
   (`_snapshot_master_refs`, `_live_master_refs`). Người nhận ủy quyền của
   chính hồ sơ = danh bạ tái dùng → không nằm trong danh sách dọn; không
   quét xóa danh bạ mồ côi ngoài phạm vi. Hồ sơ khóa giữ nguyên từ chối;
   lỗi giữa chừng → rollback toàn bộ.
2. **`/api/stats` (`main.py`):** `customers`/`properties` = DISTINCT id qua
   `_live_master_refs` (case + participant + link + snapshot còn lại) —
   danh bạ trơ không tính, primary/link trùng đếm một lần; giữ nguyên
   `cases`/`locked` và response keys.
3. **Tests `tests/test_draft_cleanup.py`:** 14 case — xóa draft dọn master
   không tham chiếu; khóa từ chối; master dùng chung/vai trò phụ/ủy quyền/
   snapshot sống giữ lại; land_rows cascade theo property; danh bạ trơ
   không bị quét; rollback nguyên vẹn; stats chỉ đếm thực thể gắn hồ sơ +
   distinct primary/link + shape endpoint.

Bằng chứng đợt 4:
- `pytest tests/test_draft_cleanup.py -x -q` → **14 passed**.
- `pytest tests/test_draft_cleanup.py tests/test_case_workspace.py
  tests/test_case_metadata.py tests/test_property_land_rows.py -q` →
  **119 passed**.
- `pytest tests/ -q` (full) → **624 passed, 1 skipped, 8 failed** — 8 fail
  giống hệt baseline (customers_excel jinja2, doc_conversion_poc, zalo_*),
  không liên quan diff.

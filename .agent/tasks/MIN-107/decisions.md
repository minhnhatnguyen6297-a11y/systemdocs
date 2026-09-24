# Decisions — MIN-107

- Contract `notary.case-drafting.v1` là SOT wire (APPROVED 24/09/2026) — mọi
  shape/error code bám contract, không tự chế.

## Quyết định implementation

- **Persist SSoT trong `case_state_json`** (`schemaVersion: 2`): `stage[]`
  rows mang `id` (entity_id str, web cũ cần) + `row_id` UUIDv4 + field
  snapshot; `assets[]` = `{id, row_id, is_primary}`; `diagram.state` là V2
  (`parentSlotIds`/`spouseSlotId`, `personId` = `row_id`). Legacy projections
  (`engineState`/`engineInput`/`engineResult`/`assignments`) được giữ/ghi lại
  để web cũ đọc — wire mới chỉ emit `state` V2 + `render_model`.
- **Migrate-on-read**: `get()` ghi lại payload đã migrate (row_id + state V2)
  ngay trong session — cần thiết để row_id ổn định qua reload; revision chỉ
  tăng trong `commit_stage` (get là read-only về semantics).
- **`case_type` discriminator**: `loai_van_ban` — `khai_nhan`/`thoa_thuan` →
  `inheritance` (document_type tương ứng); giá trị khác → case_type khác,
  capabilities tắt, commit → `case_type_unsupported`. Không thêm cột loại
  việc mới (ngoài scope migration).
- **Upsert identity**: theo `entity_id` rồi khóa giấy tờ
  (`so_giay_to`/`so_serial`); entity_id trỏ nhầm entity khác với khóa giấy tờ
  → `invalid_format` error; trùng entity_id/khóa trong cùng payload → error;
  KHÔNG merge theo tên (rows trùng tên vẫn tạo Customer riêng).
- **`updated_at`/`workspace_revision`** trên `InheritanceCase`; migration
  cộng dồn qua `_ensure_table_columns` (ALTER TABLE ADD COLUMN, không
  recreate).
- **`tai_san_id` legacy pointer**: commit assets non-empty → cập nhật sang
  primary; assets rỗng → giữ nguyên (NOT NULL), links bị xóa hết — artifact
  hiển thị web cũ, chấp nhận (ghi ở đây).
- **`engine_state_json` cột** được ghi lại mỗi commit (nodes legacy
  entity-id) — web route `/cases/{id}/state` đọc cột này.
- **`engineResult.allocations`** re-key về entity_id cho word_engine;
  `allocations` trong `diagram.render_model` (persisted + wire) giữ row_id.
- **`render_model` trên get()** = persisted; chỉ commit mới chạy
  `run_inheritance_case` (tránh phí tính lại trên read path — khớp spec:
  commit là điểm re-evaluate).
- **Adapter**: handlers chỉ dịch payload → service → `_result`/`CommandError`;
  retryable = `{workspace_conflict, stage_validation_error}` +
  `next_action=call notary.workspace_get`; `job.check_cancel()` sau service
  call.
- **`so_serial` validation** theo canonical `[A-Z]{2}\d{6,8}` (đúng schema
  stage.schema.json) — non-canonical → `invalid_format`.
- **Deviation (documented)**: `field_errors[].row_id` khi row thiếu/không hợp
  lệ `row_id` dùng placeholder `00000000-0000-4000-8000-000000000000` (uuid4
  hợp lệ) vì contract bắt row_id uuid4 trong error object.

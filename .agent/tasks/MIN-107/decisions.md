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
  `job.check_cancel()` sau service call. Retry metadata (fix reviewer M3):
  `next_action` phải nằm trong envelope enum → `workspace_conflict` =
  retryable + `next_action="retry"`; `stage_validation_error` = **không**
  retryable (payload sai, retry mù vẫn sai); `details` giữ nguyên
  `server_revision`/`field_errors`.
- **`so_serial` validation** theo canonical `[A-Z]{2}\d{6,8}` (đúng schema
  stage.schema.json) — non-canonical → `invalid_format`.
- **Deviation (documented)**: `field_errors[].row_id` khi row thiếu/không hợp
  lệ `row_id` dùng placeholder `00000000-0000-4000-8000-000000000000` (uuid4
  hợp lệ) vì contract bắt row_id uuid4 trong error object; message kèm
  `(row index N)` để client correlate về dòng payload gốc (fix reviewer L6).

## Reviewer follow-up fixes (commit thứ 2)

- **Legacy projection có semantics đầy đủ (H1)**: `_v2_to_legacy_nodes` suy
  `relationType`/`role`/`familyGroupId`/`sourceId`/`spouseOf`/
  `parentSlotId`/`parentPersonId`/`label` từ cấu trúc V2
  (`parentSlotIds`/`spouseSlotId`/slot cố định), không còn emit chuỗi rỗng.
  Mapping: `owner`→owner/Owner; `father`/`mother`→parent/Cha·Mẹ;
  `spouse_father`/`spouse_mother`→spouseParent/Cha_vc·Me_vc; spouse→owner =
  spouse/Vợ/Chồng; spouse→con = branchSpouse/Con_dau_re; parents ⊆
  {owner,spouse} = child/Con + familyGroupId ownerSpouse; parents ⊆
  {father,mother} = sibling/Anh/Chị/Em + birthParents; parents ⊆
  {spouse_father,spouse_mother} = sibling + spouseParents; parent là child
  slot = grandchild/Cháu. `label` = tên Stage person. `parentPersonId` chỉ
  cho liên kết cha-con (spouse/branchSpouse anchor là liên kết hôn nhân,
  không phải cha/mẹ — participant của họ không có `parent_customer_id`).
  Kiểm chứng bằng `_extract_diagram_participants` thật trên engineState đã
  persist.
- **Race-safety (M1)**: cả migrate-on-read lẫn commit đều dùng guarded
  conditional UPDATE (`WHERE workspace_revision = :seen`). Commit miss →
  rollback + `workspace_conflict` + `server_revision` mới. Migrate miss →
  re-read state mới và re-compose (không ghi đè); `OperationalError`
  (SQLite locked) → rollback + trả response đã compose (read không fail).
- **Participant sync (M2)**: `commit_stage` rebuild `InheritanceParticipant`
  + `case.nguoi_chet_id` từ legacy projection đã commit — tái implement
  `_extract_diagram_participants`/`_replace_case_participants` trong service
  thay vì import router (routers.cases kéo fastapi/jinja2 vào sidecar).
  Dung sai: node trỏ person ngoài Stage đã bị prune ở `_state_v2` nên không
  còn case lỗi cần raise; trùng person/deceased/parentPersonId không active
  → bỏ qua.
- **Normalize-on-read (M4)**: `ho_ten` rỗng → `"(Chưa rõ)"`; `dia_chi`
  placeholder/rỗng → `null`; `so_serial` không canonical → surrogate
  deterministic `XX%06d` theo entity_id (hoặc index) + cảnh báo trong
  `diagram.warnings` kèm giá trị gốc — không emit serial sai schema.
- **Asset dedupe (L2)**: hai stage rows resolve cùng một `properties.id`
  → `stage_validation_error`; `IntegrityError` trong commit cũng map về
  `stage_validation_error` (không `engine_internal_error`).
- **`land_rows` echo (L3)**: commit response + persist dùng bản normalized
  qua `_parse_land_rows` (đủ key schema), không echo input verbatim.
- **`tai_san_id` stale (L4, documented — không sửa schema)**: cột NOT NULL
  nên commit assets rỗng không null được pointer; `tai_san_id` có thể giữ
  asset cũ đã bị unlink → một lần save web sau đó có thể "hồi sinh" asset
  đó trong diagram cũ. Chấp nhận trong task này; track cho task sau nếu
  cần (đổi sang nullable hoặc tombstone flag).

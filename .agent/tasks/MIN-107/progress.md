# Progress — MIN-107

## Trạng thái: reviewer fixes applied + tested — 24/09/2026

Worktree `D:\systemdocs-min-107`, branch
`minhnhatnguyen6297/min-107-backend-workspace-va-stage-transaction`,
base `consolidate/monorepo` @6da4eb0.

## Đã làm

- `notary_v2/services/case_workspace.py` — `CaseWorkspaceService(db)`:
  - `get(case_id)` → workspace theo `notary.case-drafting.v1`
    (case/stage/diagram/capabilities, `backend_mode: "real"`).
    Migrate-on-read: sinh `row_id` UUIDv4 cho stage rows thiếu, derive stage từ
    `nguoi_chet`/`participants`/`property_links`/`tai_san` khi không có
    `case_state_json`, chuyển `diagram.state` legacy → V2, ghi lại payload đã
    migrate trong cùng session (revision không đổi — read-only semantics).
  - `commit_stage(case_id, base_revision, people, assets)` — một transaction:
    locked check (`workspace_locked`) → case_type check
    (`case_type_unsupported`) → revision check (`workspace_conflict` +
    `details.server_revision`) → field validation (`stage_validation_error` +
    `details.field_errors[]`) → upsert Customer/Property (theo `entity_id` rồi
    khóa `so_giay_to`/`so_serial`; không merge theo tên) → rebuild
    `inheritance_case_properties` + `case.tai_san_id` theo `is_primary` → prune
    diagram refs ngoài Stage → `run_inheritance_case` re-evaluate → ghi
    `case_state_json` (V2 + projection legacy `engineState`/`engineInput`/
    `engineResult`/`assignments` cho web cũ) + `engine_state_json` cột →
    `workspace_revision += 1`, `updated_at`. Rollback toàn bộ khi lỗi.
  - `WorkspaceError(code, message, details)` — error codes đúng contract §9.
- `notary_v2/models.py` — `InheritanceCase.workspace_revision` (Integer NOT
  NULL default 1), `InheritanceCase.updated_at` (DateTime, server_default +
  onupdate).
- `notary_v2/database.py` — `migrate_inheritance_cases_schema()` thêm 2 cột
  trên, idempotent qua `_ensure_table_columns`.
- `shell/sidecar/notary_adapter.py` — append handlers `workspace_get` /
  `workspace_commit_stage`: `_db_session()` + `_svc("case_workspace")`,
  `WorkspaceError` → `CommandError` giữ `code`/`details`; retryable chỉ cho
  `workspace_conflict` (+ `next_action="retry"`).
- `shell/sidecar/command_registry.py` — append 2 entries
  `notary.workspace_get` / `notary.workspace_commit_stage`.
- `notary_v2/tests/test_case_workspace.py` — 31 tests (temp SQLite):
  legacy-no-state, stable row_ids qua reload, multi-asset, commit hợp lệ +
  render_model, rollback khi row invalid, field_errors gộp, dup row_id,
  primary_count, so_serial canonical, locked, stale+ahead revision,
  case_type_unsupported, prune+re-evaluate + legacy projection, no
  name-merge, upsert theo khóa giấy tờ, link+is_primary, payload parse được
  bằng `_normalize_case_state_json` web cũ, migration idempotent, model cols.
  + reviewer regression: H1 engineState projection đọc được bởi
  `_extract_diagram_participants` thật (0 lỗi, vai_tro đúng, owner không là
  participant, fields `diagram_edges.js` đầy đủ); M2 rebuild participants +
  `nguoi_chet_id`; M1 commit đua cùng base trên 2 session → 1 thắng
  1 `workspace_conflict`; M1 migrate-on-read trên snapshot cũ không ghi đè
  commit mới; M4 normalize serial/dia_chi/ho_ten.
- `shell/test/test_notary_adapter_contract.py` — 10 tests (hermetic: patch
  `_db_session` temp + `_svc` module thật): registry wiring, contract shape,
  case_not_found/validation_error, commit shape + revision persist,
  stale/ahead `workspace_conflict` + details + `next_action="retry"`,
  `workspace_locked`, `stage_validation_error` không retryable, bad payload.

## Reviewer follow-up (commit 2)

- H1: `_v2_to_legacy_nodes` emit đủ semantics (relationType/role/label/
  familyGroupId/sourceId/spouseOf/parentSlotId/parentPersonId).
- M1: guarded conditional UPDATE cho cả migrate-on-read lẫn revision bump;
  migrate miss → re-read + re-compose; OperationalError → trả response,
  không fail read.
- M2: `_sync_participants_and_owner` rebuild `inheritance_participants` +
  `nguoi_chet_id` trong commit (parity `_extract_diagram_participants`/
  `_replace_case_participants`, không import router — xem decisions.md).
- M3: `next_action="retry"`; chỉ `workspace_conflict` retryable.
- M4: normalize-on-read (serial surrogate + warnings, `"(Chưa rõ)"`,
  dia_chi null).
- L1 `_emit_date_or_year` validate date; L2 dedupe asset + IntegrityError →
  stage_validation_error; L3 `land_rows` echo normalized; L4 stale
  `tai_san_id` documented; L6 row index trong field error message.

## Kiểm chứng

- `pytest notary_v2/tests/test_case_workspace.py -q` → 31 passed
- `pytest shell/test/test_notary_adapter_contract.py -q` → 10 passed
- Regression: `pytest notary_v2/tests/test_inheritance_engine.py
  notary_v2/tests/test_diagram_payload_parser.py -q` → 45 passed
- `pytest notary_v2/tests -q` (cwd=notary_v2) → 7 failed đều pre-existing
  (test_docs_structure thiếu AGENTS.md/contracts path; test_zalo_inbox* /
  test_zalo_inbox_api batch async) — không liên quan diff này.
- `python -m compileall` trên các file sửa → OK.

## Trạng thái merge (post-review)

- Review: Needs fixes (HIGH) → vá `5c1073e`: legacy projection đầy đủ
  role/relationType/label/familyGroupId, guarded UPDATE chống race,
  sync InheritanceParticipant trong transaction, next_action=retry.
- Merged vào `consolidate/monorepo` (`059a9fe` + `b528b9e` drop literal
  registry entries — gateway là đăng ký duy nhất).

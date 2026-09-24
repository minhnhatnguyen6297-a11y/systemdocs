# Progress — MIN-107

## Trạng thái: implemented + tested — 24/09/2026

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
  `WorkspaceError` → `CommandError` giữ `code`/`details`; retryable cho
  `workspace_conflict`/`stage_validation_error` (+ `next_action` =
  `call notary.workspace_get`).
- `shell/sidecar/command_registry.py` — append 2 entries
  `notary.workspace_get` / `notary.workspace_commit_stage`.
- `notary_v2/tests/test_case_workspace.py` — 26 tests (temp SQLite):
  legacy-no-state, stable row_ids qua reload, multi-asset, commit hợp lệ +
  render_model, rollback khi row invalid, field_errors gộp, dup row_id,
  primary_count, so_serial canonical, locked, stale+ahead revision,
  case_type_unsupported, prune+re-evaluate + legacy projection, no
  name-merge, upsert theo khóa giấy tờ, link+is_primary, payload parse được
  bằng `_normalize_case_state_json` web cũ, migration idempotent, model cols.
- `shell/test/test_notary_adapter_contract.py` — 10 tests (hermetic: patch
  `_db_session` temp + `_svc` module thật): registry wiring, contract shape,
  case_not_found/validation_error, commit shape + revision persist,
  stale/ahead `workspace_conflict` + details, `workspace_locked`,
  `stage_validation_error`, bad payload.

## Kiểm chứng

- `pytest notary_v2/tests/test_case_workspace.py -q` → 26 passed
- `pytest shell/test/test_notary_adapter_contract.py -q -k workspace` →
  10 passed
- Regression: `pytest tests/test_inheritance_engine.py
  tests/test_diagram_payload_parser.py tests/test_case_workspace.py -q` →
  71 passed
- `pytest notary_v2/tests -q` → 311 passed / 7 failed — tất cả lỗi
  pre-existing trên checkout gốc `D:\systemdocs\notary_v2` (test_docs_structure
  thiếu AGENTS.md/contracts path; test_zalo_inbox*, test_zalo_inbox_api batch
  async) — không liên quan diff này.
- `verify.ps1` → py_compile OK; ruff chưa cài (skip); selective suites skip
  (đường dẫn diff là monorepo-relative).
- `python -m compileall` trên các file sửa → OK.

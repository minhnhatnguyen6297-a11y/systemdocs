# Progress — MIN-109

Backend thật cho `notary.diagram_evaluate` + `notary.diagram_save`
(contract `notary.case-drafting.v1` §7), theo brief `brief.md`.

## Trạng thái: xong — 2026-09-21

## Đã làm

- `notary_v2/tests/test_inheritance_workspace.py` (mới, 23 test) — viết
  trước code (TDD): Pool invariant, outside-Stage, owner/Nhận, thế vị,
  xóa assignment → về Pool, revision cũ/mới, locked, evaluate không
  persist, save persist + bump revision, invalid state không persist,
  strict boolean, V2 wire (legacy field bị reject), concurrent save.
  (spouse heal/conflict và ancestry cycle được cover ở engine level —
  `test_inheritance_engine.py` — không có case service-level riêng.)
- `notary_v2/services/inheritance_workspace.py` (mới) —
  `InheritanceWorkspaceService.evaluate_diagram`/`save_diagram`. Tái dùng
  seam `case_workspace` (compose Stage, revision, payload, participant
  sync, `_v2_to_legacy_nodes`); engine `run_inheritance_case` là authority
  duy nhất cho tỷ lệ. `evaluate` read-only (được phép trên case locked);
  `save` validate lại trong transaction, persist V2 state + render_model +
  legacy projection, bump revision bằng guarded UPDATE (atomic), rollback
  trên mọi lỗi.
- `shell/sidecar/notary_adapter.py` — append-only: thêm
  `diagram_evaluate(job, payload)` + `diagram_save(job, payload)` ở cuối
  file theo pattern `_db_session()`/`_svc()`/`_workspace_command_error()`/
  `_result()`/`job.check_cancel()`/`finally: sess.close()`. Không log PII.
- `shell/test/test_notary_adapter_contract.py` — thêm
  `inheritance_workspace` vào `_svc` map + 9 test contract cho 2 command
  (shape, outside-stage, invalid state, missing field, locked evaluate OK,
  save persist/bump, conflict retryable, locked save, missing diagram).
- Không đổi `contracts/`, `command_registry.py`, file Zalo, dependencies,
  `inheritance_engine.py`, `case_workspace.py`.

## Đang làm dở

- Không còn.

## Bước tiếp theo

- Commit `feat(notary): expose inheritance diagram evaluate and save`.

## Check đã chạy (output thật)

`cd D:\systemdocs-min-109\notary_v2 && D:\systemdocs\notary_v2\venv\Scripts\python.exe -m pytest tests/test_inheritance_workspace.py tests/test_inheritance_engine.py tests/test_diagram_payload_parser.py -q`

```
....................................................................     [100%]
============================== warnings summary ===============================
tests/test_inheritance_workspace.py::test_save_persists_state_render_model_and_bumps_revision
tests/test_inheritance_workspace.py::test_save_does_not_change_stage
tests/test_inheritance_workspace.py::test_save_stale_and_ahead_base_revision_conflict
tests/test_inheritance_workspace.py::test_save_concurrent_same_base_conflicts
tests/test_inheritance_workspace.py::test_saved_state_reloads_identically_via_workspace_get
  ... DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12 ...
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
68 passed, 6 warnings in 7.83s
```

`cd D:\systemdocs-min-109\shell\test && D:\systemdocs\notary_v2\venv\Scripts\python.exe -m pytest test_notary_adapter_contract.py -q`

```
...................                                                      [100%]
============================== warnings summary ===============================
test_notary_adapter_contract.py: 10 warnings
  ... DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12 ...
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
19 passed, 10 warnings in 5.03s
```

`cd D:\systemdocs-min-109 && D:\systemdocs\notary_v2\venv\Scripts\python.exe contracts\notary-case-drafting\validate_examples.py`

```
[invalid] command.commit-bad-gender.invalid.json: expected=stage_validation_error got=['stage_validation_error'] -> REJECTED-CORRECTLY
[invalid] command.commit-stale-revision.invalid.json: expected=workspace_conflict got=['workspace_conflict'] -> REJECTED-CORRECTLY
[invalid] command.diagram-outside-stage.invalid.json: expected=diagram_reference_outside_stage got=['diagram_reference_outside_stage'] -> REJECTED-CORRECTLY
[invalid] command.intake-source-too-large.invalid.json: expected=intake_source_too_large got=['intake_source_too_large'] -> REJECTED-CORRECTLY
[invalid] command.intake-too-many-sources.invalid.json: expected=intake_too_many_sources got=['intake_too_many_sources'] -> REJECTED-CORRECTLY
[invalid] command.intake-unsupported-kind.invalid.json: expected=intake_unsupported_source got=['intake_unsupported_source'] -> REJECTED-CORRECTLY
[invalid] command.word-batch-destination-file.invalid.json: expected=validation_error got=['validation_error'] -> REJECTED-CORRECTLY
[invalid] command.word-batch-destination-unc.invalid.json: expected=file_scope_not_supported got=['file_scope_not_supported'] -> REJECTED-CORRECTLY
[invalid] command.word-batch-duplicate-key.invalid.json: expected=word_duplicate_document_key got=['word_duplicate_document_key'] -> REJECTED-CORRECTLY
[invalid] command.word-batch-empty-keys.invalid.json: expected=word_no_documents_selected got=['word_no_documents_selected'] -> REJECTED-CORRECTLY
[invalid] job.intake-confirmed.invalid.json: expected=validation_error got=['validation_error'] -> REJECTED-CORRECTLY
[invalid] job.word-batch-traversal.invalid.json: expected=word_path_traversal got=['word_path_traversal', 'word_path_traversal'] -> REJECTED-CORRECTLY
[invalid] job.workspace-diagram-outside-stage.invalid.json: expected=diagram_reference_outside_stage got=['diagram_reference_outside_stage'] -> REJECTED-CORRECTLY
[valid]   command.diagram-evaluate.valid.json: violations=[] -> PASS
[valid]   command.diagram-save.valid.json: violations=[] -> PASS
[valid]   command.intake-analyze.valid.json: violations=[] -> PASS
[valid]   command.word-export-batch.valid.json: violations=[] -> PASS
[valid]   command.word-export-options.valid.json: violations=[] -> PASS
[valid]   command.workspace-commit-stage.valid.json: violations=[] -> PASS
[valid]   command.workspace-get.valid.json: violations=[] -> PASS
[valid]   job.diagram-evaluate.valid.json: violations=[] -> PASS
[valid]   job.diagram-save.valid.json: violations=[] -> PASS
[valid]   job.intake-analyze-partial.valid.json: violations=[] -> PASS
[valid]   job.intake-analyze-succeeded.valid.json: violations=[] -> PASS
[valid]   job.word-export-batch-all-failed.valid.json: violations=[] -> PASS
[valid]   job.word-export-batch-canceled.valid.json: violations=[] -> PASS
[valid]   job.word-export-batch-collision.valid.json: violations=[] -> PASS
[valid]   job.word-export-batch-collision3.valid.json: violations=[] -> PASS
[valid]   job.word-export-batch-partial.valid.json: violations=[] -> PASS
[valid]   job.word-export-options.valid.json: violations=[] -> PASS
[valid]   job.workspace-commit-stage.valid.json: violations=[] -> PASS
[valid]   job.workspace-get-empty.valid.json: violations=[] -> PASS
[valid]   job.workspace-get-not-found.valid.json: violations=[] -> PASS
[valid]   job.workspace-get-stage.valid.json: violations=[] -> PASS

34 files, 0 unexpected outcomes
EXIT_CODE=0
```

## Deviations

- Không có deviation chức năng. Ghi chú: lệnh validator trên Windows phải
  chạy bằng đường dẫn có quote (backslash bị Git Bash escape nếu không
  quote) — kết quả giống hệt spec.
- `case_type_unsupported`: guard đã thêm nhưng hiện unreachable vì
  `InheritanceCase` chưa có cột case_type (precedent MIN-108, đã comment
  trong code).

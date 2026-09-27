# Progress — MIN-121

## Trạng thái: contract xong — 2026-09-27

Rebuild từ contract v1 (7 command) + Linear comment chi tiết. **Validator:
44 files, 0 unexpected outcomes** — khớp target của lần implement trước
(44/0).

## Đã làm

- `contracts/notary-case-drafting.md` → doc rev 1.1: §4.3
  `workspace_create` (idempotency_key uuid4, một transaction, owner node
  `owner` bắt buộc gán person ∈ payload stage, đúng một is_primary),
  §2.1a case_id required/draftable/forbidden, `case` +3 field
  (`ngay_lap_ho_so`/`noi_niem_yet`/`ghi_chu`), field_error
  +`duplicate_entity`, §9 +`workspace_owner_required`, §10 conformance,
  §12 changelog.
- `workspace-create.schema.json` mới; `workspace.schema.json` case +3
  field; `intake.schema.json`/`diagram.schema.json` case_id optional +
  stage payload có điều kiện; `common.schema.json` field_error enum.
- `validate_examples.py`: `workspace_create` kind, case_id 3 nhóm,
  `check_case_object`/`check_create_payload`, `evaluated_revision`
  nullable.
- +10 fixture (6 valid + 4 invalid) → tổng 44 files.

## Chưa

- Runtime (MIN-122): service create/evaluate_draft, adapter, mock.


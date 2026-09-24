# MIN-109 — BACKEND: Diagram thừa kế evaluate/save

Linear: MIN-109 (parent MIN-68). Plan §10 (Task 6).
Contract SOT: `contracts/notary-case-drafting.md` + `diagram.schema.json` — KHÔNG ĐƯỢC SỬA.

## Mục tiêu
`diagram_evaluate` (read-only, được phép trên case locked) và `diagram_save`
(validate lại + persist + tăng revision trong transaction) — Python engine là nơi
duy nhất tính nghiệp vụ; renderer/JS không tự tính tỷ lệ pháp lý.

## Files
- Create `notary_v2/services/inheritance_workspace.py`
- Create `notary_v2/tests/test_inheritance_workspace.py`
- Modify `notary_v2/services/inheritance_engine.py` (chỉ nếu cần seam mới)
- Append-only `shell/sidecar/notary_adapter.py` (2 handler mới)
- KHÔNG sửa `command_registry.py` — gateway `COMMANDS.update` đã là đăng ký duy nhất.

## Nghiệm thu (Linear)
- Pool invariant: Pool = Stage committed − items assigned trên Diagram.
- Diagram personId chỉ tham chiếu Stage `row_id`; ngoài Stage → `diagram_reference_outside_stage`.
- Evaluate không persist; Save validate lại bằng DB mới nhất, persist + tăng revision.
- Chỉ 2 quyết định: `Chủ đất`, `Nhận`; không suy "Từ chối" từ "không nhận".
- Xóa assignment → thẻ về Pool.
- Case locked → chặn write (`workspace_locked`); revision cũ → `workspace_conflict`.
- `case_type` khác inheritance → capability false / `case_type_unsupported` (hiện DB
  chỉ có InheritanceCase — guard + comment, xem precedent MIN-108).
- Wire diagram shape = engine V2: `parentSlotIds[]`, `spouseSlotId`, strict booleans.
  Legacy JS fields (`parentSlotId`, `parentPersonId`, `familyGroupId`, `sourceId`)
  không phải wire shape — adapter phải map/validate theo V2.

## Seams đã có (merged, dùng lại)
- `notary_v2/services/case_workspace.py` — CaseWorkspaceService, workspace_revision,
  legacy projection `_v2_to_legacy_nodes`, participant sync. Đọc kỹ trước khi viết.
- `notary_v2/services/inheritance_engine.py` — `run_inheritance_case`, graph validate.
- `shell/sidecar/notary_adapter.py` — pattern handler workspace_get/commit_stage
  (session, envelope, CommandError mapping).
- Mock: `shell/sidecar/notary_mock_adapter.py` — expected wire shape diagram_evaluate/save.

## Ràng buộc
- TDD: viết failing test trước (Pool invariant, ref ngoài Stage, owner/receiver,
  nhánh thế vị, xóa assignment, revision cũ, locked).
- Không thêm dependency; không đụng Zalo; không sửa contracts/; không log PII.
- Venv dùng chung: `D:\systemdocs\notary_v2\venv\Scripts\python.exe`.
- CWD-sensitive: chạy pytest notary_v2 từ `D:\systemdocs-min-109\notary_v2`.
- DB test dùng temp DB, không ghi vào notary.db dev.

## Verify
- `pytest notary_v2/tests/test_inheritance_workspace.py test_inheritance_engine.py test_diagram_payload_parser.py -q`
- `pytest shell/test/test_notary_adapter_contract.py -q -k diagram` (thêm case nếu cần)
- `python contracts/notary-case-drafting/validate_examples.py` → exit 0.
- `.agent/tasks/MIN-109/progress.md` + `decisions.md` ghi đầy đủ.

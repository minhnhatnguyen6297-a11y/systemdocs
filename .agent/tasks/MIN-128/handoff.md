# Handoff — MIN-128

## Commit
- **CHƯA commit, CHƯA push** — worktree `D:\systemdocs`, nhánh
  `consolidate/monorepo`. Chờ owner duyệt; khi commit: path-restricted theo
  danh sách dưới, message dẫn `MIN-128`.

## Files changed (37 modified + 4 task records + 1 fixture mới)
- Backend: `notary_v2/services/case_workspace.py`,
  `inheritance_workspace.py`, `word_batch_export.py`, `word_engine.py`,
  `document_intake/{__init__,models,normalization,service}.py`,
  `notary_v2/models.py` (comment).
- Sidecar: `shell/sidecar/notary_adapter.py`, `notary_mock_adapter.py`,
  `notary_gateway.py`, `command_registry.py`.
- Renderer: `shell/src/renderer/notary/case-drafting-model.js`,
  `case-drafting-view.js`, `relationship-diagram.js`.
- Fixtures: `shell/test/fixtures/notary-case-drafting/*.json` (13 file) +
  **mới** `ready-two-party.json`.
- Tests: `notary_v2/tests/{test_case_workspace,test_inheritance_workspace,
  test_word_batch_export,test_document_intake}.py`,
  `shell/test/{test_notary_adapter_contract,test_notary_mock_adapter,
  test_notary_intake_adapter,test_sidecar_contract}.py`,
  `notary-case-drafting-{model,static}.test.mjs`.
- Task records: `.agent/tasks/MIN-128/{brief,progress,decisions,handoff}.md`.
- Đã xóa `.tmp/migrate_fixtures_v2.py` (script một lần, gitignored).

## Verification
- `python -m pytest shell/test -q` → **363 passed**.
- `cd notary_v2 && python -m pytest tests -q --ignore tests/test_fast_audit_*`
  → **507 passed, 9 failed** — 9 fail pre-existing ngoài scope
  (customers_excel asyncio, docs_structure, conversion POC hash, zalo×6 —
  zalo đã tách `D:\zalo-intake`; 4 file fast_audit thiếu dep `rapidfuzz`).
- `node --test` model → 71, static → 26.
- LƯU Ý cwd: pytest backend phải chạy từ `notary_v2/` (test dùng path tương
  đối `word_templates/`, `frontend/static`); chạy từ repo root sẽ thấy
  `word.render_failed`/`frontend/static does not exist` giả.

## Compatibility notes
- Wire v2 KHÔNG emit `is_primary`/`isLandOwner`/`willReceive`; diagram state
  `{version:3, domain}`; stage `{owner_row_id?, people, assets≤3}`.
- Internal projections GIỮ NGUYÊN (§13.4/A4): `engineInput`/`engineState`
  version 2, flags cho engine + `is_primary` DB column (`= index==0`).
- Legacy surfaces ngoài scope giữ v1: `notary.case_list`/`case_get`
  (adapter), web `routers/cases.py`.
- Real↔mock parity mới chốt: stage person chưa gán trên diagram →
  warning `diagram.unassigned_pool_person` **và** `status: complete →
  incomplete` (chỉ khi engine trả complete).
- `contracts/notary-case-drafting/` (JSON schema + examples) vẫn v1 —
  artifact P2, chưa migrate; docs `contracts/README.md`, `shell/README.md`,
  `notary_v2/docs/platform/case-workspace/drafting-tab.md` còn ghi v1.

## P6/P7 integration notes
- Model API đích đã có: `state.diagram = {version:3, domain, nodes}`;
  nodes inheritance `ownPositions`/`receivePositions` ⊆ {1,2,3}; two_party
  `{id:'p1'..'p30', personId, hidden, deleted}`.
- `case-drafting-view.js` + `relationship-diagram.js` ĐÃ chuyển sang
  positions/`owner_row_id` (không còn đọc flag v1) — P6/P7 chỉ nối flow UI
  (land table, intake apply, Pool, diagram interactions).
- `cancelDraft()` = Hủy thay đổi; `setNodePositions(nodeId, kind, positions)`;
  `moveAsset(from, to)`; `setOwner(rowId)`; `newDraft(caseType)`.
- two_party: assignments do `diagram_save` sở hữu (Stage commit KHÔNG suy ra);
  render_model `unsupported`; `word_export_*` → `case_type_unsupported`.

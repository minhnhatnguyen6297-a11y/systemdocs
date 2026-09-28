# Progress — MIN-128

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: hoàn thành — 2026-09-28 (chờ owner review; CHƯA commit/push)

## Đã làm
- Recon + brief/decisions/handoff stub.
- `case_workspace.py`: schema v2 end-to-end — `SCHEMA_VERSION =
  notary.case-drafting.v2`, `case_type` derive từ `loai_van_ban`
  (`DOC_TYPES_TWO_PARTY` → two_party), `stage.owner_row_id` (bắt buộc
  inheritance, cấm two_party kể cả null), assets ≤3 theo thứ tự mảng (không
  `is_primary`), people ≤30 cho two_party, stage validation
  `asset_limit`/`people_limit` (bỏ `primary_count`), diagram state v3
  `{version:3, domain, nodes}` + migration-on-read từ persist cũ, prune
  `diagram.selection_pruned`, legacy warnings `stage.legacy_asset_overflow` /
  `stage.legacy_primary_ambiguous`, `diagram_domain_mismatch` /
  `diagram_owner_mismatch`, 30 slot canonical p1..p30, revision guard
  `workspace_conflict`, `workspace_locked`, idempotent create theo
  `workspace_idempotency_key`, seed diagram khi create không kèm state.
- `inheritance_workspace.py`: validate v3 strict (own/receivePositions ⊆
  {1,2,3} unique, cấm field lạ → `invalid_node`), dispatch theo domain,
  two_party → render_model `unsupported` + warning
  `diagram.two_party_unsupported`, owner mirror check trước refs check,
  Pool-parity: người stage chưa gán → warning `diagram.unassigned_pool_person`
  + hạ `status: complete → incomplete` (không đụng status khác).
- `word_batch_export.py` + `document_intake/*`: `SCHEMA_VERSION` → v2, cập
  nhật docstring; `word_engine.py` comment; `models.py` comment
  workspace_revision.
- `notary_adapter.py`: pass-through `case_type`, reject `word_export_*` trên
  two_party (`case_type_unsupported`) trong `_word_case`; `command_registry`
  + `notary_gateway` comment → v2.
- `notary_mock_adapter.py`: rewrite theo v2 (state v3, domain, owner_row_id,
  p1..p30, unsupported RM two_party, parity warnings với real).
- Renderer `case-drafting-model.js`: state v2 — stage `{owner_row_id, people,
  assets}` (≤3, theo thứ tự), diagram v3, `setNodePositions`,
  `moveAsset`, `setOwner`, `newDraft(caseType)`, `cancelDraft()`; KHÔNG emit
  `is_primary`/`isLandOwner`/`willReceive`. `case-drafting-view.js` +
  `relationship-diagram.js`: đọc positions/`owner_row_id` thay flags v1.
- Fixtures `shell/test/fixtures/notary-case-drafting/*.json`: migrate sang v2;
  thêm `ready-two-party.json`.
- Tests: rewrite `test_case_workspace.py` (49), `test_inheritance_workspace.py`
  (38), `test_notary_adapter_contract.py` (69 — real adapter, temp SQLite,
  v2 helpers + two_party + optional diagram + owner sync + Word v2),
  `test_notary_mock_adapter.py` (119), `notary-case-drafting-model.test.mjs`
  (71), `notary-case-drafting-static.test.mjs` (26 — assert renderer không
  emit field v1), `test_notary_intake_adapter.py`, `test_sidecar_contract.py`
  (schema v2), `test_document_intake.py`, `test_word_batch_export.py`
  (schema v2).
- Sweep legacy keys (`is_primary`/`isLandOwner`/`willReceive`/`"version": 2`/
  `notary.case-drafting.v1`) trên `D:\systemdocs`: còn lại chỉ ở (a) test
  assert reject/không-emit; (b) internal engine/persist projections
  (`engineInput`/`engineState` version 2, flags cho engine, `is_primary` DB
  column) — cố ý theo §13.4/A4; (c) surface legacy ngoài scope v2
  (`notary.case_get` adapter, `routers/cases.py` web); (d) contract v1 doc +
  `contracts/notary-case-drafting/` schema/examples (artifact P2) + docs
  lịch sử.
- Dọn `.tmp/migrate_fixtures_v2.py` (script migrate fixtures một lần).

## Check đã chạy (cwd đúng: notary_v2 cho pytest backend)
- `python -m pytest shell/test -q` → **363 passed** (23 warnings).
- `cd notary_v2 && python -m pytest tests/test_case_workspace.py
  tests/test_inheritance_workspace.py tests/test_word_batch_export.py
  tests/test_document_intake.py tests/test_word_engine.py -q` → xanh.
- `cd notary_v2 && python -m pytest tests -q --ignore tests/test_fast_audit_*`
  (4 file) → **507 passed, 9 failed** — toàn bộ fail ngoài scope MIN-128
  (pre-existing): `test_customers_excel` (asyncio), `test_docs_structure`,
  `test_document_conversion_poc` (golden hash), `test_zalo_inbox*` ×6
  (zalo engine đã tách `D:\zalo-intake`). 4 file fast_audit không collect
  được do thiếu dep `rapidfuzz` (pre-existing).
- `node --test shell/test/notary-case-drafting-model.test.mjs` → 71 pass;
  `notary-case-drafting-static.test.mjs` → 26 pass (chạy lần trước, file JS
  không đổi kể từ đó).
- `git status`/`git diff --stat` đã inspect — chỉ file thuộc scope MIN-128;
  `.tmp/` gitignored; không commit/push.

## Bước tiếp theo (ngoài P5)
- P6/P7: Stage UI/land table/intake/Pool + sơ đồ đã có model API đích
  (`setNodePositions`/`moveAsset`/`setOwner`/`newDraft`/`cancelDraft`) —
  chỉ còn nối UI flows.
- Contract-level cleanup (không thuộc P5): `contracts/notary-case-drafting/`
  schema+examples vẫn stamp v1; `contracts/README.md`, `shell/README.md`,
  `notary_v2/docs/platform/case-workspace/drafting-tab.md` còn tham chiếu v1 —
  cân nhắc task docs khi owner duyệt.
- Cần owner duyệt trước khi commit (path-restricted, không push).

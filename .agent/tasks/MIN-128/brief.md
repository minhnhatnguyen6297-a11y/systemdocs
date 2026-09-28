# Brief — MIN-128

**Linear:** MIN-128 (child của MIN-123) · **Ngày bắt đầu:** 2026-09-28 · **Nhánh/worktree:** `consolidate/monorepo` @ `5f1de32` (shared checkout `D:\systemdocs`, không push, không branch mới)

## Mục tiêu
P5 — Thực thi model + lưu dữ liệu Notary theo contract `notary.case-drafting.v2` §13 đã owner duyệt (27/09/2026): backend workspace services, adapter thật, mock adapter + fixtures, renderer model `case-drafting-model.js`, và toàn bộ test tương ứng.

## Phạm vi
- Repo/module ảnh hưởng: `notary_v2` (backend), `shell/sidecar` (adapters), `shell/src/renderer/notary` (model), `shell/test` + `notary_v2/tests`, fixtures `shell/test/fixtures/notary-case-drafting/`.
- File/thư mục dự kiến sửa:
  - `notary_v2/services/case_workspace.py` — v2 schema, `case_type`, owner_row_id, ≤3 assets, ≤30 two-party people, diagram state v3 (ownPositions/receivePositions), legacy warnings (`stage.legacy_asset_overflow`, `stage.legacy_primary_ambiguous`, `diagram.selection_pruned`), two_party domain.
  - `notary_v2/services/inheritance_workspace.py` — validate v3, dispatch domain, two_party → `status:"unsupported"` không gọi engine.
  - `shell/sidecar/notary_adapter.py` — pass-through `case_type`/`owner_row_id`, two-party Word → `case_type_unsupported`.
  - `shell/sidecar/notary_mock_adapter.py` + `shell/test/fixtures/notary-case-drafting/*.json` (+ fixture `ready-two-party.json` mới).
  - `shell/src/renderer/notary/case-drafting-model.js` — v2 state shape, `cancelDraft()`, node positions API, two-party draft.
  - Tests: `notary_v2/tests/test_case_workspace.py`, `test_inheritance_workspace.py`, `shell/test/test_notary_adapter_contract.py`, `test_notary_mock_adapter.py`, `shell/test/notary-case-drafting-model.test.mjs`, `notary-case-drafting-static.test.mjs`.
- Ranh giới dùng chung cần giữ:
  - KHÔNG đụng file P4/MIN-127 (electron chrome/styles chung) và P6/P7 renderer (`case-drafting-view.js`, `relationship-diagram.js`, dialogs, css — chỉ note handoff).
  - `desktopcommand.v1` envelope giữ nguyên; `notary.case_list` legacy giữ nguyên.
  - `loai_van_ban`/`tai_san_id`/`InheritanceCaseProperty.is_primary`/`engine_state_json` vẫn sync legacy projections cho web/Word cũ.
  - `diagram_evaluate` read-only (không +revision); `diagram_save`/`commit_stage`/`create` atomic + `base_revision` guard; idempotent create theo `idempotency_key`.
  - Không `confirmed` field ở đâu; intake suggestion không auto-commit.

## Bằng chứng nghiệm thu
- `python contracts/notary-case-drafting/validate_examples.py` → sạch.
- `pytest notary_v2/tests/test_case_workspace.py notary_v2/tests/test_inheritance_workspace.py -q` → pass.
- `node --test shell/test/notary-case-drafting-model.test.mjs` + `notary-case-drafting-static.test.mjs` → pass.
- `pytest shell/test/test_notary_adapter_contract.py shell/test/test_notary_mock_adapter.py -q` → pass.
- `verify.ps1` (scope repo hỗ trợ).
- `git status` sạch ngoài file P5; commit gắn MIN-128; không push.

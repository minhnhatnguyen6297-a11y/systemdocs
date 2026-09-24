# Brief — MIN-105

## Mục tiêu
Publish contract dữ liệu `notary.case-drafting.v1` cho tab Soạn hồ sơ trên
envelope `desktopcommand.v1`. Chỉ contract + fixtures + validator — **không
sửa runtime** (`command_registry.py`, adapter, DB, renderer, UI cấm đụng).

## Nguồn
- Linear: MIN-105 (con MIN-68).
- Plan: `docs/product/plans/2026-09-24-notary-v2-case-drafting-tab-implementation-plan.md` §2 + Task 2 (§6).
- Spec đã duyệt: `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md`, `notary_v2/docs/platform/case-workspace/drafting-tab.md` (§8 map 7 command, §10 điểm mở dành cho MIN-105).
- Envelope: `contracts/desktop-command.md`, `contracts/g1-module-data.md`, `contracts/entities.md`; precedent `contracts/g1/` (examples + validator stdlib-only).
- Quyết định owner: `is_dir:true` + absolute local path + local folder + cấm UNC cho directory FileRef (2A).

## Deliverables
- `contracts/notary-case-drafting.md`
- `contracts/notary-case-drafting/*.schema.json`
- `contracts/notary-case-drafting/examples/valid/*.json`
- `contracts/notary-case-drafting/examples/invalid/*.json`
- `contracts/notary-case-drafting/validate_examples.py`
- `contracts/README.md` (modify)

## 7 command
`notary.workspace_get`, `notary.intake_analyze`, `notary.workspace_commit_stage`,
`notary.diagram_evaluate`, `notary.diagram_save`, `notary.word_export_options`,
`notary.word_export_batch`

## Nghiệm thu (từ issue)
- `row_id/entity_id/revision/base_revision` khóa rõ.
- OCR/import không trả `confirmed`.
- Stage commit atomic; lỗi gắn `row_id`/field.
- Diagram không tham chiếu phần tử ngoài Stage.
- Directory FileRef: local, `is_dir=true`, không UNC.
- Batch Word: `_2/_3`, partial, all-failed, cancel, per-file error.
- `python contracts/notary-case-drafting/validate_examples.py` exit 0.
- DỪNG chờ owner duyệt trước Mock/Real backend.

# Progress — MIN-125

## Trạng thái: hoàn thành — đã commit `contract(MIN-125)` trên `consolidate/monorepo` — 2026-09-28

## Đã làm
- Khảo sát đầy đủ nguồn: contract v1 + validator + 44 fixtures (baseline
  pass), `case-drafting-model.js`, `relationship-diagram.js`,
  `case_workspace.py`, `inheritance_workspace.py`, `models.py`,
  `database.py`, `word_engine.py`, `word_batch_export.py`, hai adapter
  sidecar, `drafting-tab.md`, `visual-design.md`, `DESIGN.md`,
  `EXPERIENCE.md`, `entities.md`, plan MIN-123, task record MIN-124.
- Viết **PHẦN II — DRAFT §13** trong `contracts/notary-case-drafting.md`
  (v1 §1–§12 giữ nguyên APPROVED): vòng đời draft/committed/Cập nhật/Hủy;
  tài sản ≤3 theo vị trí; node v3 `ownPositions`/`receivePositions`;
  domain `two_party` 30 vị trí `p1..p30`; `workspace_create` v2 với
  `stage.owner_row_id` + diagram optional; bảng chuyển trường + tương
  thích hồ sơ cũ; error codes; ranh giới Word; retry/late-response; ví dụ
  trước/sau 5 kịch bản.
- `draft-v2.schema.json` (JSON Schema draft-07 tham chiếu).
- `validate_examples.py` mở rộng additive: `fixture_context.draft_v2`,
  `case_type`, `stage_owner_row_id`, `stage_row_ids` (đã có);
  check stage_v2 / diagram_state_v3 / create_v2 / domain mismatch /
  owner mismatch / asset_limit / people_limit / word trên two_party.
- 24 fixtures draft-v2 (12 valid + 12 invalid) tại `examples/draft-v2/`.
- `drafting-tab.md` §10 + header: các điểm chờ P2 nay trỏ §13 DRAFT.
- `visual-design.md`: các marker PENDING (P2) trỏ §13, giữ trạng thái
  chờ owner.
- `decisions.md`: bảng A (giữ nguyên) / B (Q1–Q12 đề xuất) / C (C1–C4
  chưa đề xuất).

## Check đã chạy
- `rtk proxy python contracts/notary-case-drafting/validate_examples.py`
  → **68 files, 0 unexpected outcomes** (44 v1 giữ nguyên + 24 draft-v2).
- `git diff --check` → sạch.

## Ghi chú commit
- Commit `contract(MIN-125)` trên `consolidate/monorepo`, không push; chỉ
  gồm đường dẫn sở hữu (không chạm `.agent/tasks/MIN-126/`,
  `docs/product/ui/prototypes/` của worker P3).
- Sự cố race chung index: commit P3 đầu tiên (`422b8c8`, sau bị reset)
  đã cuốn theo file MIN-125 đang staged; đã khôi phục bằng cách rebase
  `--onto 78a557f` và commit lại sạch phạm vi.

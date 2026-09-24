# Progress — MIN-105

Ghi đến đâu khi làm đến đó.

## Trạng thái: contract draft hoàn chỉnh — 2026-09-24 (chờ owner duyệt)

## Đã làm
- Worktree `D:\systemdocs-min-105`, branch `minhnhatnguyen6297/min-105-contract-notarycase-draftingv1` (base `a79cce5` — đã có spec MIN-104).
- Linear MIN-105 → In Progress.
- Audit shape thật xong: `.agent/scratch/min-105-audit-stage-diagram.md` + `min-105-audit-engine-word.md`.
- Viết `contracts/notary-case-drafting.md` (DRAFT, 12 mục): 7 command, ID/ngày/null rules, FileRef `is_dir`, intake limits, diagram state engine v2, Word batch naming/reservation/cancel, bảng error code.
- `contracts/notary-case-drafting/`: `common.schema.json` + 5 schema command (draft-07).
- Examples: 21 valid + 13 invalid trong `examples/{valid,invalid}/`.
- `validate_examples.py` (stdlib-only): **34 files, 0 unexpected outcomes, exit 0**.
- `contracts/README.md`: thêm 2 dòng index (DRAFT chờ owner duyệt).
- Review round 1 (`5730915`): 18 findings I-*/M-* đã fix (schema + doc + fixtures + validator). Re-review residuals: `breakdown.skipped` trong schema, 2 chỗ `workspace_conflict` đồng bộ `!=` revision, fraction `"a/b"` hoặc integer string.

## Tự khóa cần reviewer kiểm
- `validation_error` = mã chung cho vi phạm shape không có mã riêng (`confirmed` cấm, `""`-as-null, `is_dir` sai ngữ cảnh) — ngoài list pin.
- `schema_version` bắt buộc trong `result.data` của cả 7 command (pin chỉ nói workspace).
- `personId` = `row_id` (không phải `entity_id`) cho tham chiếu Diagram→Stage.
- `diagram_save` cũng tăng `revision` (một counter workspace chung).
- `filename_stem` do catalog backend sở hữu, không phải transform cơ học của `display_name`.
- `breakdown` bắt buộc luôn trong `word_export_batch` result (kể cả khi succeeded toàn bộ).
- `backend_mode` optional trong workspace result (chuẩn bị cho mock MIN-106).
- `fixture_context` top-level trong fixtures — không nằm trên wire.

## Bước tiếp theo
- Reviewer đọc contract + chạy validator → fix → commit → Linear In Review → DỪNG chờ owner trước MIN-106+.

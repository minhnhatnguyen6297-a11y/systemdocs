# Decisions — MIN-105

Chỉ ghi quyết định **trong phạm vi task** đã được chốt (owner hoặc spec đã duyệt).

## 2026-09-24 — ràng buộc đã có từ MIN-104/owner
- `is_dir: true` + absolute local path + chỉ folder + cấm UNC cho directory FileRef (owner 2A).
- Công thức `Người không nhận` giữ hiện trạng (owner 1A) — contract chỉ mang dữ liệu, không khóa công thức nghiệp vụ (engine Python quyết).
- Không Zalo: contract không chứa command/field Zalo; `zalo.status` không liên quan.
- Schema version: `notary.case-drafting.v1` trên envelope `desktopcommand.v1`; `result.kind` theo command.

## 2026-09-24 — controller rulings trong quá trình review contract
- `workspace_commit_stage` re-evaluate Diagram đã prune trong cùng transaction → `render_model` luôn khớp state (result trả render_model non-null).
- `breakdown` word batch = `{succeeded[], failed[], skipped[]}`; `skipped` cho file chưa làm khi cancel.
- `base_revision != server_revision` (cả `<` lẫn `>`) → `workspace_conflict`.
- `diagram_evaluate` là read-only → cho phép trên case `locked`; chỉ write bị `workspace_locked`.
- `personId` trong Diagram node = `row_id` (UUIDv4) của Stage row — ổn định trước commit; `entity_id` chỉ là tham chiếu DB sau commit.
- Diagram node wire = engine V2 (`parentSlotIds[]`, `spouseSlotId`, bool strict) — renderer chịu trách nhiệm map từ legacy JS shape.
- Data-codes `<ns>.<snake>` (block_reason, per-file error, warnings) tách khỏi job-level `error.code` (underscore) — §2.5 contract.
- `word.no_deceased_landowner`, `word.too_many_signers` thêm vào block_reason để phủ hết validation thật của `word_engine.py`.

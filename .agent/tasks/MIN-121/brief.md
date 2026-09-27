# MIN-121 — CONTRACT: notary.workspace_create + draft mode intake/evaluate

Linear: MIN-121 (parent MIN-68, In Review). Làm lại từ đầu — implementation
trước đã mất cùng worktree (2026-09-27). Contract phải xong trước MIN-122
(`blockedBy`).

## Scope (Linear)

1. Command mới `notary.workspace_create`: nhận draft Stage + diagram, tạo
   case + person + asset + link + state trong **một transaction**, trả
   workspace revision 1. Owner bắt buộc: node `owner` có `personId` trỏ đúng
   một person Stage. Đúng một asset `is_primary=true`. `isLandOwner` KHÔNG
   thay owner. Giữ nguyên `notary.case_create` cũ.
2. Draft mode cho `notary.intake_analyze` + `notary.diagram_evaluate`:
   `case_id` absent = draft; `case_id: null` = lỗi. Evaluate draft kèm
   `stage` trong payload; result `evaluated_revision: null`.
3. `case` object thêm `ngay_lap_ho_so`/`noi_niem_yet`/`ghi_chu` trong
   workspace_get/create result.
4. `field_error` thêm code `duplicate_entity`; code job-level mới
   `workspace_owner_required`.
5. `notary.case_list` thêm tham số `q` (lọc trước limit).

## Chi tiết đã chốt từ comment implementation cũ (mất)

- `idempotency_key` bắt buộc (uuid4); 429/500 vẫn idempotent — same key trả
  cùng case `created:false`, không tạo trùng.
- Payload: `{idempotency_key, case:{...meta}, stage:{people,assets},
  diagram:{state}}`. Result = workspace_get result + `created:true|false`.
- 7 schema cũ chỉ lỏng `case_id` đúng chỗ draft-allowed (intake/evaluate);
  command còn lại vẫn bắt buộc int ≥1.
- Fixtures thêm ~10 (valid+invalid); validator target **44 valid /
  0 invalid problems**.

## Files

- `contracts/notary-case-drafting.md` → v1.1
- `contracts/notary-case-drafting/*.schema.json` (+ `workspace_create.schema.json`)
- `contracts/notary-case-drafting/examples/*.json` (+ ~10)
- `contracts/notary-case-drafting/validate_examples.py` (command list + rules)

## Nghiệm thu

Validator pass 44/0; spec UX phản ánh luồng nháp (phần spec thuộc P0,
tham chiếu chéo).

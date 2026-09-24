# Progress — MIN-105

Ghi đến đâu khi làm đến đó.

## Trạng thái: APPROVED — owner duyệt 24/09/2026; contract là SOT wire; merge về `consolidate/monorepo`; MIN-106+ được mở cổng

## Đã làm
- Worktree `D:\systemdocs-min-105`, branch `minhnhatnguyen6297/min-105-contract-notarycase-draftingv1` (base `a79cce5` — đã có spec MIN-104).
- Linear MIN-105 → In Progress.
- Audit shape thật xong: `.agent/scratch/min-105-audit-stage-diagram.md` + `min-105-audit-engine-word.md`.
- `1507301` — `contracts/notary-case-drafting.md` (DRAFT, 12 mục): 7 command, ID/ngày/null rules, FileRef `is_dir`, intake limits, diagram state engine v2, Word batch naming/reservation/cancel, bảng error code. `common.schema.json` + 5 schema command (draft-07). `contracts/README.md` +2 dòng index.
- Reviewer round 1: 8 Important + 13 Minor → fix `5730915` (fraction pattern, breakdown_term required, land_rows null-safe, intake if/then, NEVER_EMPTY mở rộng, data-code registry §2.5, `word.no_deceased_landowner`/`word.too_many_signers`, commit re-evaluate render_model, `breakdown.skipped`, fixture canceled/`_3`/outside-stage request-side...).
- Re-review: toàn bộ ADDRESSED; residuals → fix `1f7e04a` (`skipped` vào schema, `workspace_conflict` `!=` đồng bộ §9/§7.5, fraction integer form trong doc).
- **Validator: 34 files (21 valid PASS + 13 invalid REJECTED-CORRECTLY), 0 unexpected outcomes, exit 0** — verified sau mỗi round.
- Không runtime nào bị đụng (registry/adapter/DB/renderer không đổi — reviewer kiểm chứng anchor file).

## Tự khóa (đã được reviewer duyệt — giữ để owner đọc)
- `validation_error` = mã chung cho vi phạm shape không có mã riêng (`confirmed` cấm, `""`-as-null, `is_dir` sai ngữ cảnh) — ngoài list pin.
- `schema_version` bắt buộc trong `result.data` của cả 7 command (pin chỉ nói workspace).
- `personId` = `row_id` (không phải `entity_id`) cho tham chiếu Diagram→Stage.
- `diagram_save` cũng tăng `revision` (một counter workspace chung).
- `filename_stem` do catalog backend sở hữu, không phải transform cơ học của `display_name`.
- `breakdown` bắt buộc luôn trong `word_export_batch` result (kể cả khi succeeded toàn bộ).
- `backend_mode` optional trong workspace result (chuẩn bị cho mock MIN-106).
- `fixture_context` top-level trong fixtures — không nằm trên wire.
- `evaluated_revision` trong `diagram_evaluate` result; `size_bytes` bắt buộc ở intake file_ref; `so_serial` canonical `[A-Z]{2}\d{6,8}`.

## Điểm flag cho owner (không chặn)
- `word_batch_failed` (job-level underscore) khác literal plan §2 `word.batch_failed` — chủ đích theo convention envelope; contract làm SOT sau duyệt, plan nên sửa lại.
- Data-codes (`block_reason`, per-file `error.code`, warnings, intake errors) dùng dạng `<ns>.<snake>` có chấm — khác convention underscore của job-level `error.code`; hai tầng tách rõ ở §2.5.
- `document_key` catalog v1: `khai_nhan_di_san`, `thoa_thuan_phan_chia`, `niem_yet` (niem_yet chưa có template → blocked `word.template_missing` hợp lệ).
- Intake limits v1: ≤8 nguồn/call, ≤20MB/file, PDF ≤50 trang, text ≤100.000 ký tự — backend được siết chặt hơn.
- `word_export_batch` không mang `base_revision` (export là read-snapshot, không mutate workspace).
- Diagram wire = engine V2 (`parentSlotIds[]`/`spouseSlotId`), KHÔNG legacy JS (`parentSlotId`/`parentPersonId`/`familyGroupId`/`sourceId`) — renderer phải map.
- OCR `type:"marriage"` ngoài mapping V1 — quan hệ do người dùng gán trên Diagram (§5.4).

## Đã chốt sau duyệt
- Contract status → APPROVED; `contracts/README.md` → APPROVED v1 (MIN-105).
- Plan §2 đồng bộ `word.batch_failed` → `word_batch_failed` (contract là SOT).
- Scratch audit files đã dọn theo AGENTS.md.

## Bước tiếp theo
- MIN-106 (mock backend) + MIN-107..110 (real backend) theo plan §6 — được mở cổng, song song được.

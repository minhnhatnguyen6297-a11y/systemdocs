# MIN-110 — Decisions

## D1. Catalog trong service `word_batch_export`, không phải adapter

`DOC_CATALOG` (document_key → display_name + filename_stem ASCII +
`has_template`) đặt ở `notary_v2/services/word_batch_export.py` —
business registry mở theo contract §8.1. Adapter chỉ inject
`resolve_template(key)` vì template resolution cần DB session +
`engine_root`. `filename_stem` tách khỏi `display_name` (ASCII stem,
không derive từ tên có dấu — §8.3). `niem_yet` có spec nhưng
`has_template=False` → luôn `word.template_missing` (NO_TEMPLATE_KEYS
của mock).

## D2. Seam `word_engine.word_block_reason` thay vì duplícate checks

Readiness `word.*` reuse đúng semantics engine: một hàm trả code đầu
tiên theo CÙNG thứ tự `_add_block_placeholders` (assets →
too_many_assets → landowners → deceased_landowners → receivers →
too_many_people → too_many_signers). Per-doc failure khi
`WordExportValidationError` raise cũng map qua hàm này → code luôn
khớp message render thật. Không sửa gì khác trong word_engine.

## D3. Cancel mang result (vượt mock hiện tại)

Mock gọi `job.check_cancel()` không result → canceled job result=null
(test mock tự ghi "giới hạn platform"). Contract example
`job.word-export-batch-canceled.valid.json` yêu cầu result retained
với `skipped[]`. Real adapter bọc `job.check_cancel(_result(
"word_export_batch", pending_data))` — đúng contract, dùng đúng seam
MIN-115 (`check_cancel(result)` đã merge ở d740a80). Service tự build
pending_data: đã xong giữ status, chưa bắt đầu → `skipped` +
`breakdown.skipped`.

## D4. word_batch_failed: `CommandError.result` + `details`

Contract example all-failed giữ `result` (kind+data+breakdown) VÀ
`error.details.documents`. Service raise `WordBatchError` với
`result_data`; adapter map `CommandError(result=_result(...),
retryable=True, next_action="retry", details={documents:[...]})` —
superset của mock (mock chỉ có details). `retryable` chỉ bật cho
`word_batch_failed`.

## D5. `existing_dir` ở fileref — thứ tự + codes theo mock oracle

`is_dir is not True` → `validation_error` TRƯỚC `validate_file_ref`;
UNC/non-absolute/non-machine_local → `file_scope_not_supported`;
không tồn tại hoặc không phải dir → `file_not_found` (mock gộp cả
"destination trỏ tới file"). Service `export_batch` tự check
`dest_dir.is_dir()` → `file_not_found` làm defense-in-depth.

## D6. Per-document error code mapping

`WordExportValidationError` → `word_block_reason(context)` (đảm bảo
code `word.*` khớp điều kiện data thật); `PermissionError` →
`file_locked`; `_DocFailed` (template_missing, unresolved_placeholders,
invalid_filename) → code riêng; mọi lỗi khác → `word.render_failed`
với `TypeError: msg` — không log PII (chỉ document_key + code).

## D7. Session ORM mở suốt batch

`build_word_context` lazy-load `participants`/`property_links`/
`nguoi_chet`/`tai_san`/`case_state_json` → `sess` phải mở trong suốt
`export_batch` (read snapshot + ghi file). Không dùng `base_revision`
(read snapshot theo brief). `mapping` build 1 lần/case trong
`mapping_holder` — cùng mapping cho mọi templated doc (v1 một template
family); `resolve_template(key)` là seam nếu sau này per-key template.

## D8. Validation order (mock parity)

case → `workspace_locked` (writable) → `document_keys` (non-list →
validation_error; [] → word_no_documents_selected; dup →
word_duplicate_document_key kèm `details.document_key`; ngoài catalog
→ word_unknown_document_key) → destination FileRef → loop. Validate
xong mới tạo file đầu tiên — test `glob("*.docx") == []` sau mọi lỗi
payload.

## D9. Checkpoint cancel trong except

`except` của `_export_one_document` gọi `check()` lần nữa trước khi
ghi entry failed: nếu cancel flag đã bật (kể cả `check()` trong try
vừa raise) → `CancelledByUser` thoát ra, doc đang xử lý tính skipped
chứ không failed. `except Exception` (không `BaseException`) →
KeyboardInterrupt/SystemExit không bị nuốt.

## Lệch so với mock (có chủ đích)

- Mock `word_export_batch` raise `word_batch_failed` KHÔNG result;
  real giữ `result` trên wire (contract example bắt buộc).
- Mock `check_cancel()` không result; real mang pending result —
  `skipped[]` lên wire đúng contract.

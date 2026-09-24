# MIN-110 — Progress

## Trạng thái: HOÀN THÀNH — chờ commit

## Đã làm (theo brief)

1. **`notary_v2/services/word_batch_export.py`** (mới) — nghiệp vụ §8:
   - `DOC_CATALOG` / `DOC_CATALOG_BY_KEY`: 3 document_key, `filename_stem`
     ASCII do backend sở hữu; `niem_yet` `has_template=False`.
   - `export_options(case, resolve_template=...)` → `result.data`
     (`schema_version` + `documents[]` ready/block_reason `word.*`).
   - `export_batch(case, case_id, document_keys, dest_dir,
     resolve_template, check_cancel, report_progress)` → `result.data`
     (`destination` FileRef dir + `documents[]` saved|failed|skipped +
     `breakdown` đủ 3 list).
   - `validate_document_keys`: non-list → `validation_error`; `[]` →
     `word_no_documents_selected`; lặp → `word_duplicate_document_key`;
     ngoài catalog/sai pattern → `word_unknown_document_key` — validate
     TRƯỚC khi tạo file (§8.2).
   - Per-document `try/except`: `WordExportValidationError` →
     `word_block_reason(context)`; template/render/IO → `word.*` /
     `file_locked` / `word.render_failed`; file saved giữ nguyên.
   - Collision: `{stem}_HS-<id>[_n].docx` n≥2; `taken` set reservation
     nội batch; `open("xb")` exclusive (không TOCTOU, không ghi đè);
     copy lỗi → xóa đúng file dở; file tạm `mkstemp` trong destination.
   - `is_safe_windows_filename`: chặn `..`, ký tự `< > : " / \ | ? *`,
     control chars, reserved names (CON/NUL/COM1-9/LPT1-9), trailing
     space/dot, leading dot.
   - All-failed → `WordBatchError("word_batch_failed", result_data=...)`.
   - `check_cancel(pending_data)` gọi giữa các văn bản + trước publish +
     trong except; pending docs → `skipped` trong data đưa lên wire.

2. **`notary_v2/services/word_engine.py`** — thêm DUY NHẤT seam
   `word_block_reason(context)` (lines ~808-835): map cùng thứ tự check
   với `_add_block_placeholders` → `word.*` code đầu tiên hoặc None.
   Không sửa logic render.

3. **`shell/sidecar/fileref.py`** — thêm `existing_dir(ref)`:
   `is_dir is True` bắt buộc → `validation_error`; `validate_file_ref`
   (scope machine_local, cấm UNC, absolute) → `file_scope_not_supported`;
   không tồn tại/không phải dir → `file_not_found`; `PermissionError` →
   `file_locked`.

4. **`shell/sidecar/notary_adapter.py`** — append 2 handler +
   helpers `_word_case_id`, `_word_case`, `_word_batch_command_error`:
   - `word_export_options`: read-only — KHÔNG check locked (mock parity,
     §5.3); `case_not_found` khi thiếu case.
   - `word_export_batch`: case → `workspace_locked` khi locked →
     validate keys → `existing_dir` → `export_batch`. Session giữ mở
     suốt batch (lazy-load participants/property_links/nguoi_chet).
   - `resolve_template` = `_resolve_template(sess, None)` (active
     template → builtin fallback `word_templates/1. PCDS .docx`).
   - `check_cancel` bọc `job.check_cancel(_result(...))` → canceled job
     mang full result + breakdown.skipped (đúng contract example
     `job.word-export-batch-canceled` — hơn mock: mock hiện trả
     result=null, có note platform trong test).
   - `word_batch_failed` → `CommandError(..., retryable=True,
     next_action="retry", details=..., result=_result(...))` — result
     retained lên wire (§8.4).
   - partial → `result["partial"] = True` (jobstore pop → status partial).

5. **Tests**:
   - `notary_v2/tests/test_word_batch_export.py` (mới): 46 tests —
     options (ready/empty/no_template/no_receiver/no_deceased_landowner/
     no_landowner/too_many_assets/too_many_people), batch (2 docx độc lập
     + round-trip python-docx, collision `_3` giữ byte cũ, intra-batch
     cùng stem → `_2`, partial, all-failed+result, template_missing,
     unresolved placeholders, cancel giữa batch giữ file saved + skipped,
     unsafe filename, progress), payload validation, filename safety
     unit tests.
   - `shell/test/test_notary_adapter_contract.py`: `_Job` stub +
     `check_cancel(result)`, `report_progress`; `_svc` stub cho phép
     `word_batch_export`; 11 tests word mới (registry wiring, options
     ready/locked-readonly/missing, batch writes real docx, collision,
     partial, all-failed result retained, validation order, destination
     rules, locked).

## Verify — TẤT CẢ PASS

- `cd notary_v2 && pytest tests/test_word_batch_export.py
  tests/test_word_engine.py -q` → **68 passed**
- `pytest shell/test/test_notary_adapter_contract.py -q -k word` →
  **11 passed** (full file: 21 passed)
- `python contracts/notary-case-drafting/validate_examples.py` →
  **exit 0** (34 files, 0 unexpected outcomes)
- `pytest shell/test -q` → **140 passed, 1 skipped** (0 regression)
- `pytest notary_v2/tests -q` → 405 passed, 7 failed — **TẤT CẢ
  pre-existing trên base d740a80** (đã stash-verify): test_docs_structure
  (monorepo layout, AGENTS.md/repo con không tồn tại theo rule),
  test_zalo_inbox*/flaky async — không liên quan diff này.

## Commit

- Branch `minhnhatnguyen6297/min-110-backend-xuat-word-nhieu-van-ban`,
  message: `feat(notary): export independent Word documents as a batch`.

## Trạng thái merge (post-review)

- Review: LGTM (0 Critical/Important; 7 Minor — đã vá tất cả trong
  `9b63100`): word_path_traversal cho stem `..`/separator; directory
  cùng tên → `_n`; `taken` discard khi publish fail; strict case_id +
  reject extra payload keys; ImportError python-docx → job-level
  `engine_unavailable` retryable; jobstore check_cancel(result) vá race
  giữa handler-return và finish.
- Mock parity vá cùng round: `check_cancel(result)` + `word_batch_failed`
  mang result trên wire; `too_many_signers` = living_landowners +
  receivers dedupe (khớp word_engine.word_block_reason).
- Merged vào `consolidate/monorepo` (`1723f1d`) — resolve append-conflict
  notary_adapter.py + test_notary_adapter_contract.py giữ cả diagram
  (MIN-109) và word (MIN-110) blocks.

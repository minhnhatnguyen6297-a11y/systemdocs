# MIN-110 — BACKEND: Xuất Word nhiều văn bản

Linear: MIN-110 (parent MIN-68). Plan §11 (Task 7).
Contract SOT: `contracts/notary-case-drafting.md` + `word-export.schema.json` — KHÔNG ĐƯỢC SỬA.

## Mục tiêu
`word_export_options` + `word_export_batch`: nhiều DOCX độc lập trong một lần,
ghi thẳng vào folder người dùng chọn; không ZIP, không overwrite, không output mặc định.

## Files
- Create `notary_v2/services/word_batch_export.py`
- Create `notary_v2/tests/test_word_batch_export.py`
- Modify `notary_v2/services/word_engine.py` (chỉ seam cần thiết)
- Modify `shell/sidecar/fileref.py` (directory FileRef validation nếu thiếu)
- Append-only `shell/sidecar/notary_adapter.py` (2 handler mới)
- Modify `shell/test/test_notary_adapter_contract.py` (word cases)
- KHÔNG sửa `command_registry.py` — gateway `COMMANDS.update` đã là đăng ký duy nhất.

## Nghiệm thu (Linear + contract)
- Checkbox = nhiều văn bản riêng (không bật/tắt đoạn trong 1 file).
- Không overwrite: trùng tên → `{stem}_2`, `_3`...; hai document cùng batch trùng
  stem vẫn không va chạm (intra-batch reservation).
- Mỗi document độc lập: try/except từng cái; lỗi nêu đúng `document_key` + `word.*`
  code; file thành công giữ nguyên.
- breakdown: `succeeded[]`/`failed[]`/`skipped[]`. Partial → marker `partial: True`
  trên result (jobstore pop khỏi wire, status=partial — đã có mechanism).
- Cancel giữa batch: gọi `job.check_cancel(result)` với result mang
  `data.breakdown.skipped` — mechanism MIN-115 đã merge (`d740a80`), dùng ngay.
- All-failed → `CommandError("word_batch_failed", ..., result=<result dict>)`
  để breakdown.failed lên wire.
- Chặn: UNC path, `..`/path traversal, tên Windows không hợp lệ (CON, NUL,
  ký tự cấm...), `is_dir:false`/non-local/không phải folder → validation_error.
- `filename_stem` do document catalog sở hữu — KHÔNG derive từ display name có dấu.
- `word_export_options`: map mỗi văn bản → template; trả `ready`/`blocked_reasons`
  (gồm `word.no_deceased_landowner`, `word.too_many_signers` per contract).
- `word_export_batch` là read-snapshot + file write — KHÔNG dùng `base_revision`.

## Seams đã có (merged, dùng lại)
- `notary_v2/services/word_engine.py` — render DOCX + template + validation hiện có.
- `notary_v2/services/case_workspace.py` — Stage/diagram snapshot cho context.
- `shell/sidecar/jobstore.py` — `check_cancel(result)`, `CommandError(result=...)`.
- `shell/sidecar/notary_mock_adapter.py` — expected wire shape word_* + fixture behavior
  (collision `_2`, canceled skipped, all-failed).
- Directory FileRef rules (contract): `is_dir:true` + absolute local + folder + cấm UNC.

## Ràng buộc
- TDD trước: 0 lựa chọn (`word_no_documents_selected`), dir sai, 2 doc cùng tên,
  file đã tồn tại, 1 template lỗi, placeholder sót, hủy giữa batch, path traversal,
  tên Windows không hợp lệ.
- File tạm trong destination → create-exclusive (`open(path,"xb")` hoặc tương đương);
  copy lỗi → xóa file dở đúng item.
- Không thêm dependency; không đụng Zalo; không sửa contracts/; không log PII.
- Venv: `D:\systemdocs\notary_v2\venv\Scripts\python.exe`. CWD: `D:\systemdocs-min-110\notary_v2`.
- DOCX output phải mở được (python-docx round-trip trong test).

## Verify
- `pytest notary_v2/tests/test_word_batch_export.py test_word_engine.py -q`
- `pytest shell/test/test_notary_adapter_contract.py -q -k word`
- `python contracts/notary-case-drafting/validate_examples.py` → exit 0.
- `.agent/tasks/MIN-110/progress.md` + `decisions.md` ghi đầy đủ.

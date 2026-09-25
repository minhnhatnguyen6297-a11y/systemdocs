# Progress — MIN-116

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: xong — 2026-09-25 (commit 33932f8)

## Đã làm
- Reproduce defect trên Python 3.12.10 venv: `tempfile.TMP_MAX = 2147483647`
  trên nt → `_mkstemp_inner` retry PermissionError ~2.1 tỷ lần khi
  `os.access(dir, W_OK)` misreport ACL deny-write → hang thực sự vô hạn
  (repro: >1.18M denied `os.open` calls và vẫn chạy). Đây là nguồn gốc
  hang >60s của MIN-113 §4b.
- `notary_v2/services/word_batch_export.py`:
  - `_temp_file_in(dest_dir, prefix, suffix)` — tạo file rỗng exclusive
    bằng uuid name + `open("xb")` (8 attempt, chỉ retry FileExistsError);
    thay `tempfile.mkstemp` trong `_render_temp` → PermissionError raise
    ngay, không còn retry loop.
  - `_probe_dest_writable(dest_dir)` — tạo/xóa `.word_export_probe_<uuid>.tmp`
    một lần; gọi ở đầu `export_batch` sau `_check()` và trước
    `build_word_context`.
  - `export_batch`: `dest_error` tuple khi probe fail → mọi doc nhận cùng
    per-file error (`file_locked` / `file_not_found` / `word.render_failed`)
    qua `_failed_entry` mới; all-failed → `word_batch_failed` kèm
    `result_data` như cũ.
  - `_doc_error_from`: thêm nhánh FileNotFoundError → `file_not_found`
    (contract §8.4 cho reuse envelope codes làm per-file data-code).
  - `_export_one_document`: thêm `check()` trước `_render_temp` (đã có
    check trước publish và trong except); dùng `_failed_entry`.
  - Bỏ `import tempfile`, `import os`; thêm `import uuid`.
- `notary_v2/tests/test_word_batch_export.py`: +5 test
  `TestDestWriteDenied` — deny-all <5s toàn `file_locked` +
  `word_batch_failed`, cancel giữa batch deny → skipped giữ result,
  cancel trước probe → all skipped, TOCTOU publish deny → file_locked,
  TOCTOU `_render_temp` PermissionError → file_locked. Helper
  `_deny_writes_under` vá cả ba seam builtins.open/io.open/os.open.
- `shell/sidecar/notary_mock_adapter.py`: divergence thật → vá parity:
  probe writability một lần đầu batch (giống engine) → `dest_error` →
  mọi doc per-file error đồng nhất; thêm catch PermissionError quanh
  `_reserve_and_write` → per-doc `file_locked` (trước đó propagate raw,
  job chết không theo contract).
- `shell/test/test_notary_mock_adapter.py`: +1 test
  `test_batch_dest_write_denied_file_locked` — deny → word_batch_failed,
  mọi doc file_locked (kể cả niem_yet — uniform như engine thật).

## Đang làm dở
- Không còn.

## Bước tiếp theo
- Push branch `minhnhatnguyen6297/min-116-word-export-acl-hang` nếu cần.

## Check đã chạy
- `pytest tests/test_word_batch_export.py -q` từ `notary_v2/`: **53 passed**
  (48 baseline + 5 mới) trong ~3.4s.
- `pytest test/test_notary_adapter_contract.py test/test_notary_mock_adapter.py -q`
  từ `shell/`: **101 passed**.
- `python contracts/notary-case-drafting/validate_examples.py`: **34 files,
  0 unexpected outcomes**.
- `notary_v2/verify.bat`: py_compile pass; ruff/scoped test groups skipped
  (ruff không cài trong venv, không file OCR/fast-audit/Zalo đổi).
- `pytest tests/ -q` full notary_v2: **440 passed, 2 failed** — cả hai ở
  `test_docs_structure.py` và **pre-existing ở base 29cf2a0** (đòi
  `notary_v2/AGENTS.md` đã bị xóa khi import snapshot theo rule monorepo,
  và `contracts/` path nằm ở repo root) — không liên quan diff này.
- Repro tay: `tempfile.mkstemp(dir=denied)` dưới `os.open` deny spin qua
  >1.18M lần trước khi kill — xác nhận hang vô hạn (TMP_MAX=2**31-1).

## Post-merge review fix (reviewer `7aed2ab9` — LGTM + 2 Important mock-parity)

- `notary_mock_adapter`: `probe.unlink()` tách khỏi guarded try — unlink OSError
  nuốt (parity real `_probe_dest_writable`), trước đây create-ok/delete-deny ACL
  làm mock fail cả batch trong khi real tiếp tục.
- `notary_mock_adapter`: catch `_reserve_and_write` nới `PermissionError` →
  `OSError` + map `file_not_found`/`file_locked`/`word.render_failed` theo
  `_doc_error_from` — trước đây dest mất giữa batch → `engine_internal_error`
  không breakdown, lệch real.
- `word_batch_export`: `build_word_context`/`word_block_reason` chỉ chạy khi
  `dest_error is None` — tránh work thừa + raw exception ngoài per-doc shape.
- Re-verify merged tree: 53 word batch + 71 mock adapter pass.

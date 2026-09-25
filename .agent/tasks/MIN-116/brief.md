# MIN-116 — BUG: word_export_batch treo khi destination ACL deny-write

Linear: MIN-116 (parent MIN-68). Phát hiện bởi MIN-113 fault injection.

## Defect
`notary_v2/services/word_batch_export.py:242` `_render_temp` → `tempfile.mkstemp`
→ stdlib retry `PermissionError` trên Windows → job hang >60s, không terminal,
không cancel được.

## Fix direction (MIN-113 decisions D2 — chọn và justify trong decisions.md)
1. **Probe writability dest TRƯỚC khi render** — 1 lần/batch: tạo file tạm thử
   trong dest, xóa ngay; PermissionError → per-doc `file_locked`/`file_not_found`
   cho TẤT CẢ docs (không phải hang). `os.access` trên Windows không đáng tin
   với ACL → phải probe bằng write thật.
2. **Check `job.check_cancel()`/cancel_requested giữa các vòng** — batch loop
   đã có check_cancel giữa docs (MIN-110); đảm bảo retry/render path cũng
   thoát được khi cancel (render temp + publish).
3. Giữ nguyên semantics: render temp trong dest (same-volume), `open('xb')`
   exclusive publish, `_2/_3` collision, per-doc error không rollback.

## Contract guardrail
- Error code cho dest không ghi được: check `contracts/notary-case-drafting.md`
  §8 — dùng code đã publish (`file_locked`/`file_not_found`/`word.*` —
  KHÔNG tạo code mới nếu contract đã có). Đọc kỹ bảng error trước khi map.
- KHÔNG sửa contract files.

## TDD bắt buộc
- Test fail trước: giả lập dest read-only (chmod/ACL hoặc monkeypatch mkstemp
  raise PermissionError) → job terminal `partial`/`failed` trong <5s, mọi doc
  có per-doc error code, không hang, hủy được.
- Regression: `pytest notary_v2/tests/test_word_batch_export.py` (48 baseline)
  + `shell/test/test_notary_adapter_contract.py` word section.

## Ràng buộc
- Worktree `D:\systemdocs-min-116`, branch `minhnhatnguyen6297/min-116-word-export-acl-hang`.
- Không đụng contracts/, Zalo, shell renderer.
- Venv: `D:\systemdocs\notary_v2\venv\Scripts\python.exe`; test chạy từ `notary_v2/` (CWD-sensitive).
- Commit `fix(notary): fail fast khi word destination khong ghi duoc` + MIN-116.
- `.agent/tasks/MIN-116/progress.md` + `decisions.md`.

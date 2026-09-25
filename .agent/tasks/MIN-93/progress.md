# Progress — MIN-93

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: HOÀN TẤT — scaffold commit + verify PASS 2026-09-25

## Đã làm
- Đọc issue Linear MIN-93 (SOT scope/nghiệm thu), plan §MIN-93/§3 (cây file,
  types §3.1), TECH_STACK (FastAPI/SQLite/zca-js/Qwen), `notary_v2/requirements.txt`
  (pin dep baseline), `zalo_connector/package.json` (zca-js 2.1.2, node>=20).
- Kiểm `D:\zalo-intake` chưa tồn tại → tạo + `git init -b main` (repo nguồn
  chính, chưa commit).
- `plan.md`, `decisions.md` (D1–D6), `brief.md`.
- Interface khóa chung: `.agent/scratch/MIN-93/decision-sheet.md` (file
  ownership + env + DDL 9 bảng + API domain + CLI + test spec).

## Đang làm dở
- Không còn. Wave 1 (A/B/C/D song song) + wave 2 (E integration) xong;
  final reviewer PASS; fix round 1 (3 Important: receipt_count_mismatch,
  strict JSON profile, consumer_id fail-closed) → 40 test; commit `a2de16b`
  + `068ae58`; `.\verify.ps1` PASS end-to-end.

## Ruling đã ghi (ledger + decisions.md)
- Contract thắng khi dispatch text lệch shape (package-list `next_after`,
  manifest `bytes`, status pending/storage/capabilities, receipt codes
  `package_unknown`/`receipt_consumer_mismatch`/`receipt_hash_mismatch`/
  `receipt_count_mismatch`) — slice D ship đúng contract.
- `rel_path` = tương đối `runtime_root`; `.pytest_cache`/`.venv` gitignore;
  `pyproject` `pythonpath=["src"]`; `_deps` đọc `app.state.settings/engine`;
  conftest PYTHONPATH=src-only (thay, không append) + pop PYTHONHOME.

## Check đã chạy (cuối)
- `.\verify.ps1` → **PASS** (40 test + replay created→capture_id + status
  intake.service-status.v1 đầy đủ trường).
- Strict JSON spot: BOM/NaN/Infinity/dup-key → StrictJsonError; body sạch parse.
- Schemas vendored: Get-FileHash 10 schema + CONTRACT_REVISION → 0 khác biệt.
- Secret sweep: 0 hit; git tree 64 file sạch.

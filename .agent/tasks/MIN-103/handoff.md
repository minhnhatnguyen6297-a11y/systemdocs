# MIN-103 handoff

## Đọc trước khi làm việc tiếp

1. `D:\zalo-intake\docs\migration-notes.md` — **mọi khác biệt cố ý vs baseline**, tagged [MIN-94/95/97/101].
2. `D:\zalo-intake\docs\connector-protocol.md` — wire contract module↔connector.
3. `D:\zalo-intake\docs\rollback-runbook.md` — khôi phục + single-listener rule.
4. `scratch/MIN-103/inventory/i{1..4}.md` — source map đầy đủ (path/symbol/verdict).
5. `scratch/MIN-103/decision-sheet.md` — giao diện đã pin giữa các slice.

## Trạng thái repo

- `D:\zalo-intake` @ `13ea96c` — source of truth. Branch main, local-only.
- `D:\systemdocs\zalo\` — snapshot phẳng 82 file + `SNAPSHOT_MANIFEST.json` (commit 13ea96c). **Untracked trong systemdocs — chưa commit** (quyết định của owner; MIN-92 cũng để chưa commit).
- Sync quy trình: chỉnh `D:\zalo-intake` → chạy `tools/export_snapshot.ps1` → manifest mới. Không sửa trực tiếp `zalo/`.
- `notary_v2` legacy giữ nguyên — shell/sidecar `zalo.status` còn wire vào code legacy (sẽ gãy khi xóa — MIN-101 lo).

## Verify nhanh

```powershell
cd D:\zalo-intake; .\verify.ps1          # PASS: 161 pytest + npm check + replay + status
npm --prefix connector test              # 87-89/90 — baseline flake, documented
tools\export_snapshot.ps1                # re-export sau khi repo đổi + commit
```

## SOT

- Wire với notary: `contracts/zalo-intake/` (MIN-92 published — không sửa tự do).
- Producer behavior: `D:\zalo-intake\docs\spec-producer.md` (một nguồn duy nhất; spec.md notary chỉ còn consumer).
- Task state: `.agent/tasks/MIN-103/`; ledger: `.agent/scratch/sdd/zalo-v2/progress.md`.

## Next

MIN-94/95/97 (có thể song song một phần) → MIN-98 → MIN-99/100/101. Mở rà `docs/migration-notes.md` trước khi plan MIN-94 — nó chứa sẵn danh sách việc phải làm.

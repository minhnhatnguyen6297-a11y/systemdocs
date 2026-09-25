# Handoff — MIN-113

## Trạng thái khi bàn giao — 2026-09-25

Verify hoàn tất: baseline xanh (113 + 100 + 25 + 188 + 34/0), full flow
E2E pass cả mock **và** real (10/10 mỗi bên), fault injection phát hiện
**1 defect thật**, packaged smoke pass với 1 giới hạn môi trường.
**Chưa cutover** — default entry không đổi, chờ owner review theo
checklist progress.md §9.

## File đã đổi (trong phạm vi cho phép)

- `shell/test/fixtures/notary-case-drafting/full-flow.json` — MỚI:
  scenario `full-flow`, case 47, 6 người + 2 tài sản + diagram 6 node +
  3 Word docs, toàn dữ liệu giả.
- `.agent/tasks/MIN-113/{progress,decisions,handoff}.md` — evidence đầy
  đủ (output thật, đường dẫn artifact `.tmp/min113/`).
- `notary_v2/docs/platform/case-workspace/drafting-tab.md` — sửa drift:
  header "chưa triển khai runtime" + §8 "chưa có 7 command/gateway chưa
  tồn tại" (stale sau MIN-106…112).
- `shell/README.md` — sửa drift: nav 7→5 mục (MIN-104), thêm mục tab
  Soạn hồ sơ + gateway/mock rule.
- `docs/architecture/ELECTRON_G1_PLAN.md` — KHÔNG sửa (không có drift).

Không sửa: contract, runtime code, Zalo, DB user, default entry.

## Phát hiện cần owner/follow-up

1. **DEFECT (blocker tiềm năng)**: `word_export_batch` backend thật hang
   >60s (không terminal, không cancel) khi destination bị ACL deny
   write — `tempfile.mkstemp` retry loop tại
   `notary_v2/services/word_batch_export.py:242`. Chi tiết + hướng fix:
   `progress.md` §4b, `decisions.md` D2. Cần issue mới.
2. **Packaged real-engine chưa chạy được**: sidecar PyInstaller thiếu
   `sqlalchemy`/`sqlite3` → `engine_unavailable` kể cả khi có
   `G1_NOTARY_V2_ROOT`; không có root → `engine_not_installed`. Đường
   lỗi controlled đã verify; "export Word trên packaged" chưa verify
   được. Cần task packaging (`decisions.md` D3).
3. `verify.bat` FULL_VERIFY **FAIL ngoài scope**: sau khi junction
   `notary_v2/venv` + `pip install tzdata`, còn 3 test Zalo connector
   (`runDataSync …` ENOENT file tạm `%TEMP%`) fail deterministic —
   cũng fail trên worktree canonical `D:\systemdocs` → pre-existing,
   Zalo scope MIN-103, không do diff này. Log `.tmp/min113/verify-bat.log`;
   chi tiết `progress.md` §7.

## Verify matrix (tóm tắt — full output progress.md)

| Mục | Kết quả |
|---|---|
| npm test shell | 113/0 |
| pytest adapter (mock+contract) | 100 |
| sidecar contract | 25 |
| notary_v2 6 suite | 188 (+37 warn) |
| contract examples | 34/0 |
| E2E mock case 47 | 10/10 |
| E2E real (DB test) | 10/10 |
| Faults mock | 9/9 |
| Faults real | 8/9 (defect §4b) |
| Sidecar restart | 7/7 |
| Privacy grep | sạch |
| Packaged smoke | pass + WARN mock-ignore đúng; engine real unavailable (giới hạn) |

## Còn lại cho owner / task sau

- Owner review checklist `progress.md` §9 → quyết cutover (KHÔNG làm ở
  task này).
- Rollback plan `progress.md` §10 — web cũ giữ nguyên 1 chu kỳ.
- Follow-up issues: fix hang word_export_batch; packaged engine deps.
- `.tmp/min113/` + `.agent/scratch/min113_e2e.py` là tạm (gitignored) —
  có thể dọn sau khi owner xem xong.

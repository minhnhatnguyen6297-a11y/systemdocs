# Handoff — MIN-105

## Trạng thái
CONTRACT DRAFT HOÀN CHỈNH — chờ owner duyệt. KHÔNG merge, KHÔNG runtime trước duyệt.

## Deliverable
- `contracts/notary-case-drafting.md` — contract `notary.case-drafting.v1` (DRAFT, 12 mục) trên envelope `desktopcommand.v1`.
- `contracts/notary-case-drafting/` — `common.schema.json` + 5 schema command (`workspace`, `intake`, `stage`, `diagram`, `word-export`), draft-07.
- `contracts/notary-case-drafting/examples/` — 21 valid + 13 invalid fixtures (mọi invalid có `expected_error`).
- `contracts/notary-case-drafting/validate_examples.py` — validator stdlib-only.
- `contracts/README.md` — index đã thêm contract (DRAFT chờ owner duyệt).

## Commits (branch `minhnhatnguyen6297/min-105-contract-notarycase-draftingv1`, base `a79cce5`)
- `1507301` contract + schemas + examples + validator + README index.
- `5730915` fix review round 1 (18 findings).
- `1f7e04a` fix residuals round 2 (3 items).

## Verify
- `python contracts/notary-case-drafting/validate_examples.py` → **34 files, 0 unexpected outcomes, exit 0**.
- Mọi JSON parse qua `json.tool`. Runtime không bị sửa (registry/adapter/DB/renderer nguyên vẹn — reviewer kiểm chứng anchor).

## Đọc tiếp khi làm việc tiếp
- `.agent/tasks/MIN-105/progress.md` — list tự khóa + flag cho owner.
- `.agent/tasks/MIN-105/decisions.md` — rulings đã chốt.
- `.agent/scratch/min-105-audit-*.md` — bằng chứng shape code thật (xóa khi task done theo AGENTS.md).
- Plan: `docs/product/plans/2026-09-24-notary-v2-case-drafting-tab-implementation-plan.md` §2, §6.

## Sau khi owner duyệt
- Merge branch về `consolidate/monorepo` (pure docs/contracts — merge sạch, không đụng pending Zalo ở main checkout vì không file nào trùng).
- Mở MIN-106 (mock backend) + MIN-107..110 (real backend) theo plan §6 — song song được.
- Nhớ sửa plan §2: `word.batch_failed` → `word_batch_failed` (contract là SOT).

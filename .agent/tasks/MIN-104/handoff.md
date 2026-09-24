# Handoff — MIN-104

Viết khi kết thúc phiên hoặc chuyển giao cho agent/người khác.

## Trạng thái khi bàn giao — 2026-09-24
Đã xong toàn bộ phạm vi MIN-104 (SPEC) và **owner đã duyệt** (1A, 2A, 3, 4 —
xem `decisions.md`). Branch đã được rebuild để loại toàn bộ nội dung Zalo theo
quyết định owner (Zalo chuyển sang repo riêng, không commit Zalo-related vào
đây). Branch `minhnhatnguyen6297/min-104-spec-product-flow-va-electron-ux-tab-soan-ho-so`
ở worktree `D:\systemdocs-min-104` — chờ integrate về `consolidate/monorepo`
rồi mở MIN-105.

## File đã đổi
- `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md` — MỚI: SOT cấp sản phẩm (taxonomy 3 module/3 tab, layout 36/64+22/78, bảng 13 nút, 12 trạng thái UI, tokens, Word multi-doc, loại trừ Zalo)
- `notary_v2/docs/platform/case-workspace/drafting-tab.md` — MỚI: SOT hành vi tab (Stage/Pool/Diagram semantics, atomic commit + base_revision, suggestion không confirmed, map 7 command đích → MIN-105)
- `docs/product/specs/2026-09-14-module-transition-ux-spec.md` — nav taxonomy đích, hàng Word export multi-doc, Zalo ra khỏi flow tab
- `notary_v2/docs/platform/case-workspace/README.md` — SOT split hiện trạng/đích; contract.md = note provisional, không phải wire contract
- `notary_v2/docs/platform/document-intake/spec.md` — section "Intake thủ công đích": 5 nguồn, gợi ý không confirmed, không Zalo control trong tab
- `notary_v2/docs/domains/inheritance/workflow.md` — đánh dấu SOT hiện trạng web; công thức `Người không nhận` **đã chốt** theo quyết định owner 1A (giữ công thức hiện tại)
- `notary_v2/docs/domains/inheritance/word-export.md` — §5/§7 tách hiện trạng (1 template → 1 download) vs đích (multi-doc batch)
- `notary_v2/docs/README.md` — index thêm drafting-tab.md
- `AGENTS.md`, `contracts/README.md` — thay đổi chung được owner cho phép commit
- `.agent/tasks/MIN-104/` — task folder này

## Đã loại khỏi branch (theo quyết định owner)
- Toàn bộ pending state đợt Zalo: `notary_v2/docs/platform/zalo-document-inbox/` edits, `notary_v2/zalo_connector/`, `docs/product/specs/2026-09-24-zalo-independent-intake.md`, `zalo-file-exchange-v1-draft.md`, `docs/product/plans/2026-09-24-zalo-independent-implementation-plan.md`, `.agent/tasks/MIN-89|91|92/`
- Pending updates của đợt Zalo trong `README.md`, `docs/architecture/*.md`, `2026-09-14-electron-core-desktopcommand-production-spec.md` — giữ nguyên ở base; các thay đổi đó vẫn nằm uncommitted ở main checkout `D:\systemdocs` để owner/Zalo repo xử lý.

## Cách verify
- `rg -n "Zalo|Stage|Pool|Diagram|word_export_batch|_2|partial|Chưa hỗ trợ" docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md notary_v2/docs/platform/case-workspace/drafting-tab.md notary_v2/docs/domains/inheritance/word-export.md` — Zalo chỉ trong câu loại trừ
- `git diff consolidate/monorepo...HEAD -- notary_v2/docs/platform/zalo-document-inbox notary_v2/zalo_connector` — phải rỗng
- Review evidence: `.superpowers/sdd/2026-09-24-*/task-1-report.md` + `review-*.diff` (gitignored — chỉ trong worktree)

## Việc còn lại / rủi ro
- Merge về `consolidate/monorepo`. Nếu conflict (do pending state ở main checkout) → **tạo Linear issue** theo chỉ dẫn owner, không tự quyết.
- MIN-105 (CONTRACT `notary.case-drafting.v1`) là cổng duyệt bắt buộc tiếp theo — phải pin `is_dir:true` + absolute local path + cấm UNC cho directory FileRef (quyết định owner 2A). Không runtime trước khi MIN-105 duyệt.
- `notary_adapter.py` hiện có 12 command `notary.*` cũ (không có 7 command workspace) — Task MIN-106+ sẽ đụng; namespace `notary` đang thuộc module `document-review` trong registry.js.
- `Người không nhận` đã chốt giữ công thức hiện tại; nếu `inheritance/spec.md` §11.3 DRAFT được duyệt sau này phải sửa lại cho khớp.

## File tạm đã dọn
- Audit reports giữ ở `.agent/scratch/min-104-audit-*.md` (gitignored, là bằng chứng hiện trạng — có thể xóa khi owner không cần đối chiếu nữa)
- `.superpowers/sdd/` gitignored tự động

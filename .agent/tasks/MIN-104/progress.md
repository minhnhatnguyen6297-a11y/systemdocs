# Progress — MIN-104

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: OWNER ĐÃ DUYỆT — đang chuẩn bị integrate — 2026-09-24

## Đã làm
- Worktree `D:\systemdocs-min-104`, branch `minhnhatnguyen6297/min-104-spec-...`
- Tạo 2 spec: `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md` (SOT sản phẩm/UX) + `notary_v2/docs/platform/case-workspace/drafting-tab.md` (SOT hành vi tab)
- Align 6 file hiện có: `module-transition-ux-spec.md` (nav 3 module + Word export row + Zalo loại trừ), `case-workspace/README.md` (SOT split + contract.md non-wire), `document-intake/spec.md` (intake đích 5 nguồn), `workflow.md` (hiện trạng/đích), `word-export.md` (§5/§7 hiện trạng vs đích multi-doc), `notary_v2/docs/README.md` (index)
- Fix round 1 sau review: vocabulary trạng thái khớp module-transition §2–3 + mapping wire `succeeded`→display `completed`; sửa 3 citation stale; wording Zalo loại trừ
- Review: task reviewer Spec ✅; re-review round 1 — all findings ADDRESSED, no new breakage
- **Owner duyệt 24/09/2026** kèm quyết định (xem `decisions.md`):
  - 1A: giữ công thức `Người không nhận` hiện tại — spec đã cập nhật (`drafting-tab.md` §6, `workflow.md` §6)
  - 2A: MIN-105 phải pin `is_dir:true` + absolute local path + cấm UNC cho directory FileRef
  - 3: chỉ commit thay đổi chung; mọi nội dung Zalo không commit (Zalo chuyển repo riêng)
  - 4: duyệt spec
- **Rebuild branch theo quyết định 3:** bỏ sync commit `f966f74` chứa snapshot Zalo; loại toàn bộ file/hunk Zalo-only (zalo-document-inbox edits, zalo_connector, spec/plan/task Zalo, pending arch docs của đợt Zalo); giữ lại `AGENTS.md` + `contracts/README.md` (thay đổi chung). 3 file mixed (`module-transition`, `document-intake`, `notary_v2/docs/README.md`) được restore về base rồi tái áp dụng chỉ phần MIN-104.

## Đang làm dở
- Commit lại theo cấu trúc mới (common / spec / task records), rồi integrate về `consolidate/monorepo`.

## Bước tiếp theo
- Merge branch về `consolidate/monorepo`. Nếu conflict với pending state ở main checkout → tạo Linear issue theo chỉ dẫn owner, không tự quyết.
- Sau merge: mở MIN-105 (CONTRACT). TUYỆT ĐỐI không runtime trước khi MIN-105 được duyệt.

## Check đã chạy
- `rg -n "Zalo|Stage|Pool|Diagram|word_export_batch|_2|partial|Chưa hỗ trợ"` trên 3 file spec chính: PASS — Zalo chỉ loại trừ/bằng chứng loại trừ; mọi quyết định một nguồn chuẩn (chạy lại sau mỗi commit)
- Reviewer spot-check 10 citation file:line — đều đúng

# Brief — MIN-104

**Linear:** https://linear.app/minhnotary/issue/MIN-104 · **Ngày bắt đầu:** 2026-09-24 · **Nhánh/worktree:** `minhnhatnguyen6297/min-104-spec-product-flow-va-electron-ux-tab-soan-ho-so` @ `D:\systemdocs-min-104`

## Mục tiêu
Khóa spec Product Flow + Electron UX cho tab Soạn hồ sơ của notary_v2 (Task 1 của plan `docs/product/plans/2026-09-24-notary-v2-case-drafting-tab-implementation-plan.md`). Chi tiết yêu cầu ở Linear — không chép lại vào đây.

## Phạm vi
- Repo/module ảnh hưởng: `systemdocs/docs/product/specs/` + `notary_v2/docs/` (chỉ tài liệu)
- File/thư mục dự kiến sửa: 2 create (`docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md`, `notary_v2/docs/platform/case-workspace/drafting-tab.md`) + 5 modify (`2026-09-14-module-transition-ux-spec.md`, `case-workspace/README.md`, `inheritance/workflow.md`, `inheritance/word-export.md`, `document-intake/spec.md`)
- Ranh giới dùng chung cần giữ: không sửa runtime/DB/`contracts/`/Figma; không nút/flow Zalo trong tab (Zalo chỉ trong câu loại trừ); không giả backend đã có — ghi rõ hiện trạng/đích

## Bằng chứng nghiệm thu
- `rg -n "Zalo|Stage|Pool|Diagram|word_export_batch|_2|partial|Chưa hỗ trợ"` trên 3 file spec chính: Zalo chỉ trong câu loại trừ, không mâu thuẫn
- Reviewer subagent duyệt spec compliance; owner duyệt trước khi MIN-105 mở

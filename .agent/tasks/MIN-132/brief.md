# Brief — MIN-132

**Linear:** [MIN-132](https://linear.app/minhnotary/issue/MIN-132/ui-p9-gop-cac-phase-kiem-tra-toan-luong-va-ban-giao-ui) · **Ngày bắt đầu:** 2026-09-28 · **Nhánh/worktree:** `consolidate/monorepo` @ `D:\systemdocs`

## Mục tiêu
P9 (phase cuối của MIN-123): kiểm chứng tích hợp toàn luồng UI Electron Notary + Upload Lab sau P1–P8, sửa lỗi phát sinh trong phạm vi, đối chiếu docs và bàn giao. Chi tiết yêu cầu ở Linear + `.agent/tasks/MIN-123/plan.md` §4 P9/§6.

## Phạm vi
- Repo/module ảnh hưởng: toàn monorepo ở mức KIỂM CHỨNG; sửa chỉ khi lỗi tích hợp giữa các phase. Không push, không tạo nhánh — commit trực tiếp `consolidate/monorepo`.
- File/thư mục dự kiến sửa: `.agent/tasks/MIN-132/`; docs hiện trạng nếu còn ghi "mục tiêu/chờ duyệt" sai (`notary_v2/docs/platform/case-workspace/drafting-tab.md`, `contracts/README.md`, `shell/README.md`, `docs/product/ui/`, `upload_lab/docs/spec_UI.md`); code chỉ khi phát hiện lỗi tích hợp nhỏ.
- Ranh giới: KHÔNG đổi contract semantics, không implement Word mới, không upload/finalize thật trên cổng tỉnh, không "sửa" ~9 fail pre-existing của notary_v2 (customers_excel, docs_structure, document_conversion_poc, zalo_inbox ×6, fast_audit thiếu rapidfuzz). Kỷ luật git: add/commit theo path sở hữu, không `add -A`/`commit -a`/`--amend`.

## Bằng chứng nghiệm thu
- `python contracts/notary-case-drafting/validate_examples.py` (root)
- `cd shell && node --test test/*.test.mjs` → kỳ vọng 254
- `cd shell && python -m pytest test/test_notary_adapter_contract.py test/test_notary_intake_adapter.py test/test_notary_mock_adapter.py -q`
- `cd shell && python -m pytest test/test_upload_workspace.py test/test_upload_workflow.py test/test_upload_recovery.py -q` (ghi điều kiện chạy)
- `cd notary_v2 && python -m pytest tests/test_case_workspace.py tests/test_inheritance_workspace.py -q` (cwd=notary_v2 bắt buộc — relative path)
- `verify.ps1` nếu môi trường cho phép; `git diff --check`
- Thử `npm start`/`electron .` trong shell — ghi rõ nếu không chạy được.
- Checklist cửa sổ theo plan.md §6 (1280×800, 1366×768, 1920×1080, DPI 125/150%, Tab/focus/dialog, cuộn, dữ liệu lớn).

# Brief — MIN-92

**Linear:** https://linear.app/minhnotary/issue/MIN-92/contract-goi-file-raw-ocr-va-yeu-cau-ocr-bo-sung · **Ngày bắt đầu:** 2026-09-24 · **Nhánh/worktree:** consolidate/monorepo (chờ owner chọn nhánh)

## Mục tiêu
Chốt contract liên repo `zalo-intake v1` (gói raw OCR, ACK, OCR bổ sung, listener_session, retention raw bot sau ACK) để owner duyệt và publish vào `contracts/`, giải phóng MIN-93.

## Phạm vi
- Repo/module ảnh hưởng: `systemdocs/contracts/` (sau duyệt); bản nháp dựng tại `.agent/scratch/MIN-92/contracts/` trước duyệt.
- File dự kiến: `contracts/zalo-intake.md`, `contracts/zalo-intake/*.schema.json`, `contracts/zalo-intake/examples/{valid,invalid}/`, `contracts/zalo-intake/validate_examples.py` + `_validator/`, `contracts/README.md`, `.gitattributes`.
- Ranh giới: chỉ trao đổi hai repo; không schema kết quả Document Intake (MIN-102); không runtime.

## Bằng chứng nghiệm thu
`python contracts/zalo-intake/validate_examples.py` (0 unexpected outcomes, đếm valid/invalid, contract revision) + `python -m unittest discover -s contracts/zalo-intake/_validator/tests -t contracts/zalo-intake` + owner duyệt ghi trong `decisions.md`.

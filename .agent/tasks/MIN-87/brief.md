# Brief — MIN-87

**Linear:** https://linear.app/minhnotary/issue/MIN-87 · **Ngày bắt đầu:** 2026-09-22 · **Nhánh/worktree:** `consolidate/monorepo`

## Mục tiêu
Rà soát backlog cũ, chuyển phần còn giá trị sang một project/repo `systemdocs`, và bàn giao brief prototype UX để owner kiểm tra trước production.

## Phạm vi
- Repo/module ảnh hưởng: Linear project `systemdocs`, taxonomy component cho `system`, `shell`, `notary_v2`, `upload_lab`, `notaryoffice`.
- File/thư mục dự kiến sửa: `.agent/tasks/MIN-87/`, gồm record bàn giao, design brief HTML, UX Vòng 02 tham chiếu và snapshot Linear đã biên tập.
- Ranh giới dùng chung cần giữ: ba module nghiệp vụ dùng shared shell; database chỉ là hạ tầng; không sửa spec module/runtime trong task này; không loại issue hỗn hợp còn backend, contract, logic hoặc data-integrity.

## Bằng chứng nghiệm thu
- Read-back Linear cho project/label/parent/state; snapshot sau tại `.agent/tasks/MIN-87/linear-scope-after-summary.json`.
- Validator HTML: 21 stable screen IDs, 16 acceptance scenarios, không external reference.
- Browser: 1440×900, 1280×820, 760×520; không overflow ngang, control hiển thị tối thiểu 44px, copy/download/TOC/print hoạt động, không lỗi JavaScript.
- `git diff --check` pass; bản bàn giao nằm trong `.agent/tasks/MIN-87/`, bản làm việc ở `.agent/scratch/` được gitignore.

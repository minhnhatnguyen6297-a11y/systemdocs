# Brief — MIN-139

**Linear:** https://linear.app/minhnotary/issue/MIN-139/spec-document-field-studio-engine-nhan-dien-truong-dung-chung-trong · **Ngày bắt đầu:** 2026-09-29 · **Nhánh/worktree:** minhnhatnguyen6297-a11y/notaryoffice-bmad-brainstorm

## Mục tiêu
Định hình Document Field Studio thành tab Nhận diện dữ liệu trong Upload Lab và
làm rõ năng lực nhận diện/nhóm dữ liệu dùng chung trước khi thiết kế runtime.

## Phạm vi
- Repo/module ảnh hưởng: `upload_lab`, Document Intake của `notary_v2`, Word engine.
- File/thư mục dự kiến sửa: product brief dưới `_bmad-output/`; task record này.
- Ranh giới dùng chung cần giữ: chưa sửa SOT kiến trúc, UI hoặc contract khi
  quyền sở hữu engine và schema kết quả chưa được owner chốt.

## Bằng chứng nghiệm thu
- Product brief và addendum phản ánh đủ đầu vào, nhóm bản ghi, nhiễu/trùng và
  Word placeholder.
- Mỗi mô tả hiện trạng có đường dẫn + dòng source.
- `git diff --check` và kiểm tra link Markdown nội bộ đều qua.


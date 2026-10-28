# Dọn output generated của BMAD

Ngày: 2026-10-12

## LÀ GÌ

- User cho phép xóa `notary-diagram-errors.packed.html` và yêu cầu xử lý 368 file generated chưa commit trong phiên này.
- Xóa đúng 368 file untracked dưới `_bmad/render/` và packed HTML đã nêu; không gỡ 59 file render đã tracked hoặc hai tài liệu brainstorm/decision-76 còn untracked.
- Ignore `_bmad/render/` và `_bmad/custom/html-plan/examples/*.packed.html` để output được sinh lại không xuất hiện trong worktree status.
- Bảo lưu trước xóa tại `docs/tmp/generated-artifact-cleanup/before-cleanup.tar.gz`; phạm vi chính xác trong `manifest.json` cùng thư mục.

## TẠI SAO

- `render_skill.py` sinh snapshot bất biến từ skill đã cài và customization của project. Đây là output có thể tái tạo, không phải nguồn chuẩn để sửa workflow.
- Packer sinh `.packed.html` từ HTML nguồn và runtime. Giữ source, không đưa output build vào commit.
- Xóa theo danh sách untracked đã kiểm tra, không dùng clean toàn repo; giữ nguyên tài liệu chưa được user cho phép xóa.

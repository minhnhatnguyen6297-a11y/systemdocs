---
title: 'Sửa run.bat trong worktree thiếu Electron'
type: 'bugfix'
ticket: ''
created: '2026-10-08'
status: 'built'
route: 'oneshot'
route_source: 'auto'
baseline_revision: 'df28b2a823309468bc9696b6643b5968ad9870ac'
review: 'quick'
review_source: 'auto'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="User requests repair of run.bat">

## Intent

**Problem:** `run.bat` thoát mã 1 với lỗi không tìm thấy Electron; worktree không có node_modules và Python venv riêng.

**Approach:** Ưu tiên runtime tại chỗ, dùng runtime sẵn có ở kho Git chính nếu thiếu; luôn chạy mã tại worktree. Giữ biến Python do người dùng đặt, đối số và mã thoát; không tự bật spike, không đổi dữ liệu hay cài dependency.

</frozen-after-approval>

## Implementation Notes

Sửa nhỏ dưới 100 dòng. Spec: `../specs/shared/dev-launcher.md`.
Kho chính lấy từ `git rev-parse --path-format=absolute --git-common-dir`, không gắn cứng D:/systemdocs.
Phần spike có sẵn không nằm trong commit sửa launcher.

## Plan Change Log

## Review Triage Log

- Orca review `task_60acb0d2057a` / `ctx_8a0c9f628230`: không có phát hiện cần sửa; reviewer kiểm tra mã, không tự chạy app. Không chạy thêm các góc review chuyên sâu cho bản sửa nhỏ này.

## Verification

- Trước sửa: `rtk proxy cmd /c run.bat` → mã 1, electron không được nhận diện.
- Sau sửa: gọi chính run.bat, nối vào Electron thật; kiểm tra cửa sổ và sidecar ready bằng profile/dữ liệu thử riêng.
- Kiểm tra ưu tiên runtime, override Python, đối số/đường dẫn có khoảng trắng và thiếu runtime bằng bản sao launcher trong thư mục tạm.
- `rtk proxy node _bmad-output/tmp/launcher-fix/check-launcher.cjs`: PASS. Chính run.bat được gọi từ thư mục khác, Electron mở URL của worktree, sidecar ready, không bật spike; thoát mã 0. Dữ liệu/profile giả tách riêng. Biến ELECTRON_RUN_AS_NODE kế thừa đã được xóa; Python dùng kho chính.
- `rtk proxy python -X utf8 _bmad-output/tmp/launcher-fix/check_edges.py`: PASS. Runtime tại chỗ, đường dẫn/đối số có khoảng trắng, mã thoát 7, override Python và trường hợp thiếu Git/runtime trả mã 1. Dùng Node đóng vai executable để quan sát đối số/môi trường; không thay thế kiểm tra Electron thật ở trên.
- `rtk git diff --check`: PASS. Link báo cáo/ảnh tạm cũ đã được bỏ ngày 15/10/2026 vì file không còn trong repo; phần ghi kết quả ở trên là lịch sử, chưa đọc lại được bằng chứng gốc.

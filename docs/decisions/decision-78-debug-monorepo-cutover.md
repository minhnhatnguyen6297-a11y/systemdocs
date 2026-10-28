# Quyết định: merge đầy đủ luồng debug vào monorepo, bảo lưu dữ liệu riêng tư

Ngày: 2026-10-11. Người dùng đã duyệt mapping và backup trong phiên cutover.

## LÀ GÌ

- Code và bộ kiểm chứng được maintain ở `tools/visual-bug-reporting/`, tracked cùng hook main/preload và root `run-dev.bat`.
- `run-dev.bat` chỉ bật cờ rồi gọi `run.bat`: dùng chung resolver runtime Git/worktree, giữ đối số/mã thoát, không hardcode máy hoặc bắt buộc `rtk`.
- Đây vẫn là dev mock-only trong cùng app, bị khóa bởi unpackaged + cờ bật; không thêm sản phẩm hoặc đưa tool vào package globs.
- Báo cáo/runtime mới mặc định ở ignored `docs/tmp/visual-bug-reporting/`. Dữ liệu nguồn được archive riêng tư vào ignored target `debug-spike-source-backup/spike-visual-bug-reporting` trước khi cutover, không tự import vào profile/schema đang chạy.
- Sau commit nguồn và independent review mới merge vào `consolidate/monorepo`, kiểm chứng BAT thật và ahead=0. Không push, không tự xóa branch/worktree.

## TẠI SAO

- Merge tài liệu trước đó không mang executable/hooks chưa commit: launcher ở đích không tồn tại và luồng debug chưa chạy được.
- Code dưới tmp ignored không phải vị trí maintain. Dữ liệu người dùng, note, ảnh và SQLite cần bảo lưu nhưng không được commit vào Git hoặc ghi đè dữ liệu active.
- Dùng lại launcher chung tránh hai cách giải runtime lệch nhau; test BAT thật chứng minh đường đi người dùng, không chỉ harness bỏ qua launcher.

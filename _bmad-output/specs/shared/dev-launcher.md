# Mở ứng dụng trong Git worktree

Trạng thái: sửa lỗi theo yêu cầu người dùng, 2026-10-08.

- `run.bat` chạy mã của thư mục chứa nó, dù được gọi từ nơi khác.
- Ưu tiên Electron và Python đã cài tại thư mục hiện tại. Nếu thiếu, dùng bản đã cài tại kho Git chính; không tải/cài tự động.
- Giữ `G1_PYTHON` do người dùng đặt. Xóa `ELECTRON_RUN_AS_NODE` trong tiến trình mở app để Electron thực sự mở cửa sổ.
- Không tự bật chế độ báo lỗi thử nghiệm hoặc đổi dữ liệu ứng dụng.
- Thiếu Electron ở cả hai nơi: thông báo cách cài, trả mã lỗi và giữ cửa sổ để đọc được lỗi. Giữ nguyên đối số và mã thoát của Electron.

Lý do: worktree chia sẻ mã Git nhưng không tự có `node_modules` hoặc môi trường Python của kho chính.

## Launcher báo lỗi cục bộ

- `run-dev.bat` đặt riêng `G1_VISUAL_BUG_SPIKE=1` rồi gọi `run.bat` cùng đối số.
- Hook chỉ chạy trong Electron chưa đóng gói; không tạo sản phẩm/app thứ hai.
- Chế độ này dùng Notary mock và profile/dữ liệu thử tách riêng dưới
  `_bmad-output/tmp/visual-bug-reporting/`, không mở dữ liệu Notary production.
- JSON/PNG báo lỗi ở đó là dữ liệu riêng tư local, không commit. Xem
  [visual-bug-spike.md](visual-bug-spike.md) và
  [hướng dẫn tool](../../../tools/visual-bug-reporting/README.md).

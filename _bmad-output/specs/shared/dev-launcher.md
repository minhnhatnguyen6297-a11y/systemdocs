# Mở ứng dụng trong Git worktree

Trạng thái: sửa lỗi theo yêu cầu người dùng, 2026-10-08.

- `run.bat` chạy mã của thư mục chứa nó, dù được gọi từ nơi khác.
- Ưu tiên Electron và Python đã cài tại thư mục hiện tại. Nếu thiếu, dùng bản đã cài tại kho Git chính; không tải/cài tự động.
- Giữ `G1_PYTHON` do người dùng đặt. Xóa `ELECTRON_RUN_AS_NODE` trong tiến trình mở app để Electron thực sự mở cửa sổ.
- Không tự bật chế độ báo lỗi thử nghiệm hoặc đổi dữ liệu ứng dụng.
- Thiếu Electron ở cả hai nơi: thông báo cách cài, trả mã lỗi và giữ cửa sổ để đọc được lỗi. Giữ nguyên đối số và mã thoát của Electron.

Lý do: worktree chia sẻ mã Git nhưng không tự có `node_modules` hoặc môi trường Python của kho chính.

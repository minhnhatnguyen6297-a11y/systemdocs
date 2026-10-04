# NAIA-22 — kiểm tra lại đăng nhập sandbox

Ngày 03/10/2026, không sửa mật khẩu hay chính sách khóa tài khoản.

- Cả `CodexSandboxOnline` và `CodexSandboxOffline` vẫn enabled.
- Một sandbox CLI mới đăng nhập được `CodexSandboxOffline`; các lượt kiểm
  uv sau đó chạy được. Điều này chưa chứng minh cả hai đường ổn định.
- Đọc Security Event4625 gần nhất có `SubStatus 0xc000006a` (mật khẩu sai):
  Offline lúc23:50:25; Online lúc22:23:04,22:23:22,22:23:34 ngày03/10/2026.
  `svchost.exe` là tiến trình Windows xử lý đăng nhập, chưa xác định ứng dụng
  nào giữ mật khẩu cũ. Không kết luận lỗi đã hết từ báo cáo00:35 trước đó.
- Có hai bản Codex trên máy: npm CLI0.160.0 và desktop CLI0.159.0-alpha.12.1.
  Sự khác phiên bản là thông tin cần đối chiếu, chưa phải bằng chứng nguyên nhân.
- Multica daemon không có task active/running hay terminal report pending lúc
  kiểm tra. Các công việc sản phẩm được tiếp nhận tại Codex hiện tại.

Chưa hoàn tất: xác định nguồn dùng credential cũ và chứng minh online/offline
không tái xuất hiện4625. Không tự đổi mật khẩu để che nguyên nhân; không hạ
chính sách khóa tài khoản. Hạn mức model trước đó là nguyên nhân khác.

## Kiểm tra mới ngày 04/10/2026

- Chạy phiên sandbox mới riêng cho cả Online và Offline: đều đăng nhập đúng
  tài khoản, tìm được uv dùng chung, chạy Python trả `uv-run-ok`.
- Đọc Security4625 trong cửa sổ 8 giờ gần nhất sau các lượt trên: không thấy
  lần mật khẩu sai mới của hai tài khoản. Cả hai vẫn enabled.
- Đây là bằng chứng hai đường hiện chạy được; chưa xác định ứng dụng đã dùng
  mật khẩu cũ trong các sự kiện ngày03/10. Không sửa mật khẩu/chính sách và
  không coi một lượt chạy thành bằng chứng ổn định lâu dài.

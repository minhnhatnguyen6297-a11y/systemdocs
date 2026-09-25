# Handoff — MIN-69: chuyển Upload Lab sang shell

**Ngày:** 24/09/2026 · **Repo:** `D:/systemdocs` · **Nhánh đã kiểm tra:** `consolidate/monorepo`.

**Đọc trước:** [AGENTS.md](D:/systemdocs/AGENTS.md), [MIN-69 trên Linear](https://linear.app/minhnotary/issue/MIN-69/migrate-uploadaudit-vao-electron), rồi [kế hoạch triển khai](D:/systemdocs/docs/product/plans/2026-09-24-upload-lab-shell-migration-plan.md).

## Điểm bàn giao

- Đã lập kế hoạch và kiểm tra luồng khởi động; **chưa triển khai code, chạy kiểm thử ứng dụng hoặc chuyển dữ liệu thật**. MIN-69 đang In Review; không coi trạng thái này là đã nghiệm thu kế hoạch mới.
- Chuẩn đối chiếu là **Fluent UI hiện tại chạy bằng [run.bat](D:/systemdocs/upload_lab/run.bat:3)**. Launcher đi qua bootstrap tới [ui_runner.py](D:/systemdocs/upload_lab/ui_runner.py:3), mở [ui_qt/main_window.py](D:/systemdocs/upload_lab/ui_qt/main_window.py:75). Đây không phải giao diện đã bị bỏ; không lấy bản thử nghiệm Electron làm chuẩn trải nghiệm.
- [Codegraph](D:/systemdocs/code-graphs/README.md:13) là bản chụp ngày 14/09, đã lệch code hiện tại. Dùng để tìm đường đi rồi đọc source thật; không tự xây lại toàn bộ graph. Không có công cụ Graphify/context-mode trong phiên kiểm tra.

## Chỉ dẫn thực hiện

1. Kiểm tra nhánh và thay đổi chưa commit; giữ nguyên phần việc của người khác. Đọc kế hoạch với skill `executing-plans`; không tự bắt đầu lại vòng thiết kế.
2. **Bắt đầu Task 1:** cập nhật đặc tả, ghi rõ mốc Fluent UI/run.bat ở trên; đối chiếu issue hiện có. Quy ước trao đổi dữ liệu giữa giao diện và Python phải được duyệt trong task riêng **trước** phần code phụ thuộc.
3. Giữ quyết định ở §1 của kế hoạch: **hai tab toàn chiều rộng**; bỏ trang Nhật ký; cấu hình và dropdown website ở đầu Audit, dùng chung cho Upload. Chỉ bật website có bộ xử lý thật; website thứ hai chờ người dùng cung cấp.
4. Sau khi qua bước duyệt, làm lần lượt **T2–T5: website/dữ liệu và xử lý Python → T6–T8: giao diện và nối thao tác → T9: kiểm thử bản đóng gói → T10: chuyển mặc định**. Ưu tiên đúng lượt quét, nhận biết hồ sơ đã Lưu và không gửi trùng sau lỗi/khởi động lại.
5. Giữ nghiệp vụ Python; ứng dụng chỉ điền sẵn, **người dùng tự bấm Lưu**. Không tự đổi launcher, xóa bản đang dùng, ghi đè dữ liệu hoặc thử upload trên website thật khi chưa đủ điều kiện nghiệm thu/đồng ý tương ứng.
6. Kiểm chứng theo §7 của kế hoạch; ghi lệnh đã chạy, kết quả và việc còn thiếu vào [progress.md](D:/systemdocs/.agent/tasks/MIN-69/progress.md). Không dùng kết quả kiểm thử lịch sử hoặc chỉ thấy cửa sổ mở để báo hoàn thành.

## Hồ sơ và kiểm chứng

Handoff này bổ sung cách hiểu đúng về Qt/run.bat, không thay thế kế hoạch. Hồ sơ hiện chỉ thêm tài liệu kế hoạch, brief, progress và handoff; chưa sửa code. Kiểm tra bàn giao giới hạn ở nội dung/đường dẫn tài liệu; kiểm thử ứng dụng còn phải thực hiện theo từng task. Không tạo file tạm cần dọn.

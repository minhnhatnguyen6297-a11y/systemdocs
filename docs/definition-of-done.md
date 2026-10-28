# Definition of Done (DoD)

Một thay đổi chỉ "xong" khi đủ **tất cả** mục dưới đây. PR template
(`.github/pull_request_template.md`) có checklist tương ứng.

## 1. Đúng việc
- Gắn với issue hoặc mục tiêu ghi rõ; phạm vi không phình ra ngoài mục tiêu.
- Đổi hành vi ⇒ spec/decision liên quan được cập nhật **trước** khi sửa code.
- Đã tìm giải pháp có sẵn trên GitHub (thư viện, action, pattern) trước khi tự viết; ghi URL đã xem.

## 2. Có bằng chứng
- Có test cho hành vi mới/sửa (unit; e2e/CDP nếu là luồng UI).
- Báo cáo/PR có **lệnh đã chạy + output thật**, kể cả lỗi và bước bị bỏ qua.
- CI xanh. Lỗi đã biết chỉ được nằm trong `tools/ci/known-failures-*.txt` kèm issue ref
  và lý do; không thêm lỗi mới, không skip/xoá test để cho xanh.
- Thay đổi UI: có ảnh trước/sau (dữ liệu giả lập).

## 3. An toàn
- Chỉ dữ liệu giả lập. Không secret, không dữ liệu khách hàng (repo public).
- gitleaks sạch (`gitleaks git --redact -c .gitleaks.toml .`).
- Không `git stash`, không code trên `main`, không push khi chưa được duyệt.

## 4. Đã review
- Bắt buộc một bước review trước khi báo xong: Superpowers `requesting-code-review`
  hoặc agent Reviewer. Góp ý được xử lý hoặc ghi lý do không xử lý.

## 5. Quyết định đúng tầng
- Quyết định nhỏ (đặt tên, cấu trúc nội bộ một module, refactor cục bộ): tự quyết, ghi trong báo cáo.
- Kiến trúc, schema/contract, dependency mới: **dừng**, báo các phương án + đánh đổi, chờ owner.

## 6. Báo cáo
- Tách **đã kiểm chứng** và **chưa kiểm chứng**; nêu giả định; liệt kê commit.

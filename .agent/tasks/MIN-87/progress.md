# Progress — MIN-87

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: chờ owner review — 2026-09-22

## Đã làm
- Tạo issue điều phối `MIN-87`, issue prototype `MIN-88` và sáu label component/phase trong Linear.
- Đưa 55 issue đã giữ vào project `systemdocs`; read-back xác nhận: system 21, shell 9, notary_v2 10, upload_lab 14, notaryoffice 1.
- Audit bảy candidate UI: giữ `MIN-31`, `MIN-32`, `MIN-33`, `MIN-77`, `MIN-82`; chỉ `MIN-34`, `MIN-38` đủ điều kiện loại.
- Tạo và kiểm chứng `.agent/tasks/MIN-87/he-thong-cong-chung-ui-design-brief.html`; giữ bản làm việc tương ứng trong `.agent/scratch/`.
- Cập nhật `MIN-88` sang `In Review`, ghi comment kết quả và đọc lại xác minh.
- Xóa `docs/architecture/CHANGE_REVIEW.md` từng được tạo ngoài phạm vi ở giai đoạn brainstorming; không đụng các thay đổi staged có sẵn.

## Đang làm dở
- Chưa xóa/archive `MIN-34`, `MIN-38`: connector Linear không có thao tác delete/archive và phiên web chưa được đăng nhập.

## Bước tiếp theo
- Owner mở Linear web để xóa/archive hai issue trên, hoặc cấp capability delete/archive; không dùng `Cancelled` để giả xóa.
- Gửi brief cho Agent Design, nhận prototype click được và review UX.
- Chỉ sau khi backlog/prototype được duyệt mới mở task riêng cập nhật spec module.

## Check đã chạy
- Validator Python trên artifact: PASS; 21 ID duy nhất, 16 scenarios, 0 external refs.
- Browser QA: PASS tại 1440×900, 1280×820, 760×520; copy fallback, download, TOC mobile, print handler; 0 JS errors.
- `git diff --check`: PASS.
- Linear read-back `MIN-88`: state `In Review`, comment kiểm chứng tồn tại.
- Kết quả migration đã biên tập: `.agent/tasks/MIN-87/linear-scope-after-summary.json`; audit phân loại: `.agent/tasks/MIN-87/linear-delete-readiness-summary.json`.

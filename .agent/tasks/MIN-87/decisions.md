# Decisions — MIN-87

Chỉ ghi quyết định **trong phạm vi task** đã được chốt (bởi user/owner hoặc
theo spec đã duyệt). Quyết định xuyên sản phẩm hoặc câu hỏi mở: **không** tự
chốt ở đây — đưa lên `docs/architecture/OPEN_DECISIONS.md`.

## 2026-09-22 — Một project backlog cho monorepo
- **Chọn:** Project/repo `systemdocs`; phân loại ownership bằng label `component:*`.
- **Lý do:** Phù hợp cấu trúc monorepo và tránh tiếp tục gắn task vào repo/UI cũ.
- **Loại bỏ:** Duy trì các backlog độc lập theo snapshot repo con.
- **Nguồn:** Owner trong hội thoại; Linear `MIN-87`.

## 2026-09-22 — Chỉ loại issue frontend thuần túy đã lỗi thời
- **Chọn:** Giữ issue hệ thống, backend, contract, logic, queue/data-integrity và issue hỗn hợp; `MIN-34`, `MIN-38` là hai candidate đủ điều kiện loại.
- **Lý do:** Tiêu đề có “UI” không chứng minh nội dung chỉ là giao diện.
- **Loại bỏ:** Xóa hàng loạt theo title/status hoặc xóa issue hỗn hợp khi chưa bảo toàn yêu cầu.
- **Nguồn:** Chỉ đạo owner; `.agent/tasks/MIN-87/linear-delete-readiness-summary.json`.

## 2026-09-22 — Không giả xóa bằng trạng thái Cancelled
- **Chọn:** Để `MIN-34`, `MIN-38` chờ delete/archive thật khi có capability.
- **Lý do:** Connector hiện không có delete/archive; đổi trạng thái không cùng semantics.
- **Loại bỏ:** Sửa title hoặc đổi `Cancelled` để báo đã xóa.
- **Nguồn:** Kiểm tra schema Linear MCP và read-back issue.

## 2026-09-22 — Prototype trước, spec module cập nhật sau
- **Chọn:** Giữ UX Vòng 02 và design brief trong `.agent/scratch/`; giao Agent Design dựng một prototype offline, click được bằng fixture hư cấu.
- **Lý do:** Owner cần kiểm tra UX trước production; A1/A3/A4 và các gate khác chưa chốt.
- **Loại bỏ:** Sửa ngay spec/runtime module hoặc mô tả PoC như pipeline production.
- **Nguồn:** Owner trong hội thoại; Linear `MIN-88`.

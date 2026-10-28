# Giữ cấu trúc HTML Plan của Thariq

> **Bị thay bởi [decision-81](decision-81%20-%20Bo-BMAD-thu-Superpowers-docs-chuyen-sang-docs.md) (28/10/2026).** Giữ để tra lịch sử.

Ngày: 2026-10-12

## Quyết định của user

- Cấu trúc HTML đã chốt theo HTML Plan của Thariq trong Claude Code; giữ nguyên, không brainstorm hay thiết kế lại cấu trúc.
- Khi cần tham khảo implementation, phải đọc code nguồn thực tế. Nếu không có code để tham khảo thì dừng phần phụ thuộc và báo user; không tự suy diễn thay thế.
- Phiên brainstorm hiện tại tập trung nối workflow/công cụ hiện có, không mở lại thiết kế HTML.

## Vì sao

User đã chốt cấu trúc HTML trong phiên trước. Thiết kế lại hoặc suy diễn thiếu nguồn sẽ làm lệch yêu cầu và tạo thêm vòng sửa workflow daily.

## Nguồn hiện có

- Bản nguồn nghiên cứu: `docs/tmp/thariq-html-plan-source/` gồm `SKILL.md`, `references/blocks.md`, `runtime/` và `examples/`.
- Bản tích hợp: `_bmad/custom/html-plan/`; provenance và các patch cục bộ ghi trong `UPSTREAM.md`.
- Upstream pin được ghi trong provenance: `88003be1129c09381d27100b37a8fdc21b3214bf`.

Việc xác nhận các file tồn tại không thay cho đọc nội dung khi dùng chúng làm căn cứ; bản tích hợp có patch không được coi là nguyên bản upstream.

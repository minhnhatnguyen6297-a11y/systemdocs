# Decisions — MIN-138

## 2026-09-29 — Một cây spec theo phạm vi

- **Chọn:** Cây `docs/spec/` đi từ hệ thống → module → flow → feature. README của mỗi thư mục giữ phần chung cho các con.
- **Tại sao — lời giải thích gốc:** Khi vấn đề đã được chia nhỏ, tạo thêm file `architecture.md`, `decision.md` hoặc `design.md` làm tài liệu ngắn bị phân mảnh. Kiến trúc và lịch sử của feature phải nằm ngay trong spec feature; nội dung dùng chung đặt ở cấp cha tương ứng.
- **Diễn giải áp dụng:** Agent tìm cấp nhỏ nhất bao phủ toàn bộ ảnh hưởng. Chỉ tách file khi có chức năng độc lập hoặc phụ lục lớn, không tách theo loại thông tin.
- **Nguồn:** Owner, 29/09/2026, trao đổi MIN-138.
- **Phạm vi / trạng thái:** Đã chốt cho toàn bộ tài liệu dài hạn trong monorepo.
- **Nơi lưu lâu dài:** `README.md`, `AGENTS.md` và cây `docs/spec/`.

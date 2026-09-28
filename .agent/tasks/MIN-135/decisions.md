# Decisions — MIN-135

## 2026-09-28 — Chỉ mục không thay nguồn nghiệp vụ

- **Quyết định:** Bảng chỉ dẫn tới nguồn đã có; khi trạng thái nguồn thay đổi thì sửa chỉ mục, không chép quy tắc nghiệp vụ sang đây.
- **Tại sao — lời giải thích gốc:** “Giữ lại phần "Tại sao?" cho các quyết định, mỗi lần tôi giải thích - là 1 chi tiết tinh tế, kiến thức ngách của ngành mà không hệ thống hoặc tài liệu chung chung nào nhắc tới, không nên để những kinh nghiệm, đúc kết đó mất đi.” — owner, MIN-134, 28/09/2026.
- **Cách áp dụng:** Tách cột “Lý do đã viết” và “Lời gốc của owner”; thiếu link thì ghi `Chưa dẫn`, không viết lại lý do như thể đã có lời gốc.
- **Nguồn:** `docs/architecture/KNOWLEDGE.md`.

## 2026-09-28 — Thay chỉ mục theo quyết định bằng bản đồ bốn phần

- **Quyết định của owner:** “Chia chỉ mục như sau: 1. Tầm nhìn chung, định hướng sản phẩm 2. Soạn thảo tự động (notary_v2): Mục tiêu là hướng đến soạn thảo tự động 3. Upload_lab: Phục vụ số hóa tài liệu sẵn có. 4. Quản lý vận hành: notaryoffice”.
- **Tại sao — lời giải thích gốc:** “cách làm này sẽ liên tục tạo ra các docs khác nhau, vụn vặt, không tập trung, tranh chấp SOT” và “repo cũng không có bản đồ tri thức để biết file gì lưu gì, agent luôn tự tạo ra mà không có luật agents.md khống chế”.
- **Cách áp dụng:** xóa `DECISION_INDEX.md`; `KNOWLEDGE.md` chỉ dẫn file sở hữu theo bốn phần; `AGENTS.md` kiểm soát việc tạo file mới.
- **Nguồn:** phản hồi owner trong cuộc trao đổi MIN-135 ngày 28/09/2026.

# Decisions — MIN-134

## 2026-09-28 — Giữ lý do trong nguồn có chủ sở hữu, không tạo kho sự thật thứ hai

- **Chọn:** Bản đồ tra cứu ở `docs/architecture/KNOWLEDGE.md`; quy tắc lâu dài ở docs của module sở hữu, việc đang làm ở Linear, diễn biến ở `.agent/tasks/`.
- **Tại sao — lời giải thích gốc:** “Giữ lại phần "Tại sao?" cho các quyết định, mỗi lần tôi giải thích - là 1 chi tiết tinh tế, kiến thức ngách của ngành mà không hệ thống hoặc tài liệu chung chung nào nhắc tới, không nên để những kinh nghiệm, đúc kết đó mất đi.”
- **Diễn giải áp dụng:** Giữ nguyên lời giải thích và ví dụ của owner cạnh nguồn ổn định; phần agent diễn giải phải tách ra, ghi trạng thái và link. Quy tắc nơi lưu bám `AGENTS.md` và ADR-0001 của `notary_v2`.
- **Nguồn:** owner trong phiên 28/09/2026; Linear MIN-134; `AGENTS.md` phần SOT; `notary_v2/docs/architecture/decisions/0001-domain-module-documentation-architecture.md`.
- **Phạm vi / trạng thái:** cách ghi tri thức cấp hệ thống; đã chốt bởi yêu cầu trực tiếp của owner.
- **Nơi lưu lâu dài:** `docs/architecture/KNOWLEDGE.md`.

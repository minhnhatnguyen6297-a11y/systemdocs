# AGENTS.md — upload_lab

## Sources of truth
- `docs/SPEC.md` — **SOT duy nhất về nghiệp vụ** của module (pipeline, trạng thái, ràng buộc)
- `README.md` — sơ đồ codebase, lệnh chạy/test
- `docs/regex-rules.md` — quy chuẩn trích xuất theo từng loại văn bản
- `docs/spec_UI.md` — UI
- `agent.md` — quy trình agent, Linear issue và bảo mật

## Rules
- Không tự chuyển chế độ Finalize thành mặc định. Dry-run là mặc định.
- Đổi selector web tỉnh: sửa ở `uploader_selectors.py`, không rải trong code.
- Thêm loại văn bản mới: cập nhật `docs/regex-rules.md` cùng lúc với code.
- Chạy test trước khi báo xong.

## Cross-module context (read only when needed)
Module này nằm trong monorepo (MIN-83) — tài liệu cấp repo ở `../`.
Task thường ngày **không cần** đọc. Chỉ đọc khi task chạm ranh giới module,
khóa định danh dùng chung, hoặc tích hợp: `../SYSTEM_ARCHITECTURE.md`,
`../contracts/entities.md`, `../contracts/desktop-command.md` (kênh gọi qua
`shell/`), `../OPEN_DECISIONS.md`. Nghiệp vụ module khác:
`../<module>/docs/SPEC.md`. Module này thắng về hành vi nội bộ.

**Bắt buộc đọc `../TECH_STACK.md` trước khi** thêm/đổi công nghệ (thư viện đọc
file, OCR, DB, queue, framework UI) hoặc ra quyết định kiến trúc. Các module sẽ
gộp về một database dùng chung, chọn lệch nhau là viết lại sau.

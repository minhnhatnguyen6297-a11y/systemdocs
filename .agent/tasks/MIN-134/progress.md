# Progress — MIN-134

## Trạng thái: xong lát cắt đầu — 2026-09-28

## Đã làm

- Tạo issue Linear MIN-134 trước khi sửa repo.
- Đọc AGENTS.md, README.md, OPEN_DECISIONS.md, ADR của notary_v2 và mẫu quyết định task.
- Chọn lát cắt đầu: bản đồ tra cứu và cách giữ nguyên lời giải thích gốc; không xây RAG ở bước này.
- Tạo `docs/architecture/KNOWLEDGE.md`, mở đường dẫn từ `README.md` và `AGENTS.md`.
- Mở rộng `.agent/templates/decisions.md` và ghi lý do gốc ở `decisions.md` của task.
- Review nhanh phát hiện thiếu `handoff.md`; đã bổ sung trước khi bàn giao.

## Đang làm dở

- Không có trong phạm vi MIN-134.

## Bước tiếp theo

- Rà từng nhóm quyết định lịch sử có lý do chưa được giữ; tạo issue riêng cho tài liệu lệch hiện trạng.

## Check đã chạy

- `git status --short --branch`: sạch trước khi làm.
- Các đích link chính tồn tại; ví dụ B1 có nguồn ở `OPEN_DECISIONS.md`.
- `git diff --check`: đạt trước review.
- Review nhanh: một phát hiện thật (thiếu handoff), đã sửa.

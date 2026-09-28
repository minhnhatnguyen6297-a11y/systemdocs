# Handoff — MIN-134

## Trạng thái khi bàn giao — 2026-09-28

Đã hoàn thành lát cắt đầu của Tri thức dự án: bản đồ tra cứu và quy tắc giữ
quyết định cùng lời giải thích gốc. Linear MIN-134 là nguồn trạng thái task.

## File đã đổi

- `docs/architecture/KNOWLEDGE.md`: nơi tra cứu, cách giữ “tại sao”, mẫu ghi nhận, ví dụ có nguồn.
- `AGENTS.md`, `README.md`: dẫn tới quy tắc lâu dài.
- `.agent/templates/decisions.md`: yêu cầu ghi lời gốc, nguồn, phạm vi và nơi lưu lâu dài.
- `.agent/tasks/MIN-134/`: brief, plan, progress, decisions, handoff.

## Cách verify

- `git diff --cached --check` không báo lỗi.
- Kiểm tra link từ README/AGENTS/mẫu quyết định tới `KNOWLEDGE.md`.
- Ví dụ B1 đối chiếu `docs/architecture/OPEN_DECISIONS.md` mục B1.

## Việc còn lại / rủi ro

- Các quyết định lịch sử chưa được rà từng mục để bổ sung lý do gốc; không tự điền phần thiếu.
- Một số tài liệu tổng quan về Zalo còn mô tả trạng thái cũ; nên sửa trong issue rà soát tài liệu riêng, không coi ngày ghi trên tài liệu là bằng chứng duy nhất.
- `.agent/tasks/MIN-133/w4-shots/` xuất hiện trong lúc làm MIN-134 và không thuộc thay đổi này.

## File tạm đã dọn

Không tạo file tạm trong repo cho MIN-134.

---
id: decision-48
title: "SOT gom ve _bmad-output; chap nhan mat file tam .agents; BMAD doc spec tu noi moi"
date: '2026-10-07'
status: accepted
---
## Context

Code review đợt tái cấu trúc SOT (2026-10-07) nêu 2 điểm cần user quyết:
(1) 11 file trong `.agents/` (review, plan task-3, handoff) bị xóa vĩnh viễn vì
thư mục này chưa từng được commit vào git; (2) `_bmad/config.toml` vẫn trỏ
`project_knowledge` về `docs/`, nên BMAD chưa "tự động" đọc/ghi spec ở nơi mới —
trái với yêu cầu "tự động, tôi không cần quan tâm".

## Decision

- **Chấp nhận mất 11 file `.agents/`** — đó là file tạm theo luật cũ; nội dung
  quan trọng nhất (kế hoạch task-3) còn lại trong `removed-agents-files.md` dưới
  dạng tóm tắt vị trí. Không đi khôi phục từ Thùng rác/backup.
- **Sửa `_bmad/config.toml`: `project_knowledge` → `{project-root}/_bmad-output/specs`.**
  Kèm theo: `bmad-spec` vốn đã ghi spec vào `{output_folder}/specs` (cùng nơi),
  AGENTS.md §2 chỉ SOT cho mọi agent. Từ giờ BMAD đọc lẫn ghi đều ở
  `_bmad-output/specs` — không còn thư mục `docs/spec`.

## Consequences

- Spec sống duy nhất ở `_bmad-output/specs/`; `docs/` không còn là nguồn chuẩn.
- File tạm mất là chấp nhận được — quy trình mới không tạo file tạm ngoài git.
- Nếu sau này cần lại nội dung 11 file đã mất: chỉ còn cách dựng lại từ quyết
  định trong `_bmad-output/decisions/` và spec hiện hành.

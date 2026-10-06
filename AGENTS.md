# AGENTS.md — luật làm việc trong systemdocs
- Cách giao tiếp: Nói với người dùng như người dung nontech - vibecoder. Dùng từ dễ hiểu; thuật ngữ bắt buộc phải
giải thích hoặc có ví dụ.
- Agent tạo và ghi file theo sơ đồ cấu trúc thư mục tại file README. Các file sinh ra trong quá trình làm việc tạm: task, rác, handoff,... ghi vào .agents, KHÔNG lưu tùy tiện ở các folder code.
- `docs/spec là tài lieu SOT của toàn dự án, khi tôi chỉ dẫn, sửa lỗi, đưa quan điểm,... tức là quyết định từ tôi phải được agent chắt lọc và ghi vào file docs tương ứng: QUYẾT ĐỊNH LÀ GÌ? TẠI SAO?
- Spec quyết định hành vi phải có; code chỉ chứng minh hiện trạng, KHÔNG sửa code, code mới khi không có spec, yêu cầu tôi thêm spec trước.
- Luật cứng Backlog: mọi việc phải có task backlog trước khi code. Xong việc nào, agent tự chắt lọc quyết định vào backlog decision, tự cập nhật hoặc thêm mới spec trong docs/spec, rồi mới tick Done. File tạm (task, rác, handoff) ghi vào .agents, KHÔNG để lẫn vào folder code.
- Luôn áp dung khi có thể:
+ Ponytail: Code tối thiểu, đây là giai đoạn MVP, cần 1 bản chạy được trước khi phát triển 1 hệ thống lớn
+ Caveman: Nói ít - Luôn áp dụng khi handoff, viết spec, plan giao tiếp agent với agent. Không ap dụng khi nói chuyện, brainstorming với tôi.
+ bmad: tuân theo quy trình coding của bmad
+ graphify: code map, luôn đọc trước khi dò file thủ công, nếu chưa có hoặc file graphify behind nhiều ngày so với hiện tại -> chạy graphify trước.

<!-- BACKLOG.MD GUIDELINES START -->
<!-- backlog.md-instructions-version: 1.53.0 -->
<CRITICAL_INSTRUCTION>

## Backlog.md Workflow

This project uses Backlog.md for task and project management.

**At the beginning of each conversation in this project, run `backlog instructions overview` before answering or taking action. Re-read it only if you have not read it yet in the current conversation.**

Use the overview to decide whether to search, read, create, or update Backlog tasks.

Before task lifecycle actions, read the matching detailed guide:
- `backlog instructions task-creation` before creating or splitting tasks
- `backlog instructions task-execution` before planning, changing status or assignee, adding a plan or implementation notes, or implementing task work
- `backlog instructions task-finalization` before checking acceptance criteria, writing final summaries, or moving tasks to terminal statuses

Use `backlog <command> --help` before running unfamiliar commands. Help shows options, fields, and examples.

Do not edit Backlog task, draft, document, decision, or milestone markdown files directly. Use the `backlog` CLI so metadata, relationships, and history stay consistent.

</CRITICAL_INSTRUCTION>
<!-- BACKLOG.MD GUIDELINES END -->

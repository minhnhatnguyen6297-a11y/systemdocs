# Agent Workflow

## Source of truth

- Linear is the source of truth for requirements, plans, and issues in this repository.
- The Fluent UI redesign specification and its action plan are tracked in [MIN-31](https://linear.app/minhnotary/issue/MIN-31/upload-lab-fluent-ui-redesign-specification-windows-11).
- Each repository/product must have its own Linear project; never place its issues in another product's project.
- If the repository's dedicated Linear project does not exist, leave the issue unassigned to a project until it is created; do not use a shared or unrelated project as a substitute.
- Linear updates from a feature worktree must explicitly name the worktree branch and state that they do not represent `main`.
- Do not create or maintain local `spec`, `plan`, or `issue` files.
- Keep local documentation only when it is operational guidance, a user-facing reference, or a durable domain catalog that is not a work item.

## Cross-module context (read only when needed)

Module này nằm trong monorepo (MIN-83) cùng `notary_v2`, `shell`, `notaryoffice`
— tài liệu cấp repo ở `../`, repo GitHub cũ chỉ còn archive.
Task thường ngày **không cần** đọc. Chỉ đọc khi task chạm ranh giới module,
khóa định danh dùng chung, hoặc tích hợp: `../SYSTEM_ARCHITECTURE.md`,
`../contracts/entities.md`, `../contracts/desktop-command.md`,
`../OPEN_DECISIONS.md`. Module này thắng về hành vi nội bộ.

**Bắt buộc đọc `../TECH_STACK.md` trước khi** thêm/đổi công nghệ (thư viện đọc
file, OCR, DB, queue, framework UI) hoặc ra quyết định kiến trúc. Các module sẽ
gộp về một database dùng chung, chọn lệch nhau là viết lại sau.

## Required workflow

1. Search Linear before starting work to find an existing issue.
2. Create a Linear issue for new requirements, plans, or defects before implementing them.
3. Read the linked Linear issue before editing code and reference its identifier in handoffs, commits, or pull requests.
4. Update the Linear issue when scope or acceptance criteria change; do not duplicate the requirements in the repository.
5. Use the Orca Linear CLI (`orca linear ...`) for Linear reads and writes.

## Security

- Never put credentials, tokens, cookies, or sensitive user data in Linear descriptions, comments, logs, or repository documentation.
- Preserve the existing rule that browser and network diagnostics must redact authentication data and query strings.

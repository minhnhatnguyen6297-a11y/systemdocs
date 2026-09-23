# code-graphs — Graphify snapshots của các repo con

Graph cấu trúc code (AST) của các nhánh đang được gộp về app Electron thống
nhất. Snapshot tại **2026-09-14**, quét bằng
`D:\graphify\.venv\Scripts\graphify.exe extract <path> --code-only`
+ `cluster-only --no-label` — AST thuần, **không qua LLM**, nên:

- Edge có ~17% là INFERRED (suy luận), không phải 100% chứng cứ AST.
- Community chưa có tên (placeholder `Community N`) — chạy `graphify label`
  hoặc `cluster-only` không `--no-label` nếu muốn đặt tên bằng LLM.
- Graph chỉ để **điều hướng**; kết luận hành vi phải đọc source thật.

## Danh mục graph

| Repo | Nhánh | Commit tip | Nguồn đã quét | Nodes / Edges / Communities |
|---|---|---|---|---|
| notary_v2 | `main` | `9a9bf9a` | `systemdocs/.scan-src/notary_v2-main` (export `git archive`, frozen) | 843 / 2119 / 41 |
| notary_v2 | `codex/zalo-document-inbox-v2` | `12b8695` | `D:\notary_v2-worktrees\task-8-integration` | 1298 / 3935 / 53 |
| notary_v2 | `codex/inheritance-diagram-v2` (nhánh dev hiện tại — user gọi là "nhánh electron") | `2c59fae` | `D:\notary_v2` | 1410 / 3806 / 67 |
| upload_lab_repo | `feat/fluent-ui-redesign` | `f4fe560` | `D:\upload_lab_repo-worktrees\feat-fluent-ui-redesign` | 690 / 1711 / 19 |
| upload_lab_repo | `codex/desktop-command-poc` (Electron POC: `poc/desktop_command/electron/`) | `f18a42f` | `D:\upload_lab_repo\.worktrees\desktop-command-poc` | 792 / 1920 / 38 |
| notaryoffice | — | — | **Chưa có code** — chỉ có `intent.md` (đặc tả); không có gì để quét. | — |

Lưu ý: **không có code Electron nào trong notary_v2** ở mọi nhánh (đã kiểm
chứng bằng `git ls-tree` toàn bộ 20 nhánh). "Nhánh electron" của notary_v2 ở
đây là nhánh dev hiện tại do user chỉ định. Electron thật sự chỉ tồn tại ở
`upload_lab_repo@codex/desktop-command-poc`.

## Cách dùng

```bash
GRAPH="D:\systemdocs\code-graphs\<repo>\<nhánh>\graphify-out\graph.json"

D:\graphify\.venv\Scripts\graphify.exe query "câu hỏi" --graph "$GRAPH"
D:\graphify\.venv\Scripts\graphify.exe explain "symbol" --graph "$GRAPH"
D:\graphify\.venv\Scripts\graphify.exe affected "symbol" --graph "$GRAPH"
D:\graphify\.venv\Scripts\graphify.exe tree --graph "$GRAPH"   # D3 tree HTML
```

Mỗi graph kèm `GRAPH_REPORT.md` (community hubs, god nodes) cùng thư mục —
đọc report trước khi lặn vào node.

## Quét lại / cập nhật

- Worktree còn nguyên (4/5 target): sửa code xong chạy
  `graphify update <worktree>` rồi copy `graphify-out/` đè lên đây, hoặc
  `extract <worktree> --code-only --out <dir-tại-đây>` cho snapshot mới.
- `notary_v2@main`: snapshot nguồn giữ ở `.scan-src/notary_v2-main`. Muốn quét
  tip mới: `git -C D:/notary_v2 archive main | tar -x -C <dir>` rồi extract lại.
- Trước khi tin graph: đối chiếu commit ở bảng trên với `git rev-parse <nhánh>`
  — lệch nhau là graph đã cũ.

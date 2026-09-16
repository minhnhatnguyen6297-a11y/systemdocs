# code-graphs — Graphify snapshots của các module monorepo

Graph cấu trúc code (AST) của các module trong monorepo. Quét bằng
`D:\graphify\.venv\Scripts\graphify.exe extract <path> --code-only`
+ `cluster-only --no-label` — AST thuần, **không qua LLM**, nên:

- Edge có một phần là INFERRED (suy luận), không phải 100% chứng cứ AST.
- Community chưa có tên (placeholder `Community N`) — chạy `graphify label`
  hoặc `cluster-only` không `--no-label` nếu muốn đặt tên bằng LLM.
- Graph chỉ để **điều hướng**; kết luận hành vi phải đọc source thật.

## Danh mục graph — monorepo (bản mới nhất)

Snapshot sau khi gộp monorepo (MIN-83), nguồn = module trong repo này:

| Module | Snapshot | Nguồn đã quét | Nodes / Edges / Communities |
|---|---|---|---|
| `notary_v2` | `notary_v2/monorepo/` | `notary_v2/` trong repo | 1377 / 4008 / 58 |
| `upload_lab` | `upload_lab/monorepo/` | `upload_lab/` trong repo | 874 / 2070 / 39 |
| `shell` | `shell/monorepo/` | `shell/` trong repo | 451 / 847 / 19 |
| `notaryoffice` | — | **Chưa có code** — chỉ `AGENTS.md` + `docs/SPEC.md`; không có gì để quét | — |

Lưu ý khi đọc graph monorepo:

- `notary_v2` graph bao gồm cả `.agents/skills/` (tooling của agent, không phải
  kiến trúc sản phẩm).
- `shell` graph cho thấy rõ renderer → preload/IPC → main → sidecar.
- `notary_v2` ↔ `upload_lab` **không cross-import** nhau; `shell/sidecar` import
  cả hai engine qua `sys.path` (in-process, không HTTP).

## Snapshot cũ (trước khi gộp — chỉ tham chiếu lịch sử)

Các thư mục `code-graphs/<repo>/<nhánh-cũ>/` (vd `notary_v2/main`,
`upload_lab_repo/feat-fluent-ui-redesign`, `upload_lab_repo/codex/desktop-command-poc`,
`notary_v2/codex/*`) là snapshot quét từ các worktree ngoài (`D:\...`) trước
15/09/2026. Nguồn có thể không còn; dùng để so sánh lịch sử, **không** dùng làm
bằng chứng cho code hiện tại.

## Cách dùng

```bash
GRAPH="code-graphs/<module>/monorepo/graphify-out/graph.json"

D:\graphify\.venv\Scripts\graphify.exe query "câu hỏi" --graph "$GRAPH"
D:\graphify\.venv\Scripts\graphify.exe explain "symbol" --graph "$GRAPH"
D:\graphify\.venv\Scripts\graphify.exe affected "symbol" --graph "$GRAPH"
D:\graphify\.venv\Scripts\graphify.exe tree --graph "$GRAPH"   # D3 tree HTML
```

Mỗi graph kèm `GRAPH_REPORT.md` (community hubs, god nodes) cùng thư mục —
đọc report trước khi lặn vào node.

## Quét lại / cập nhật

- Sau khi sửa code module: `graphify update <module>` tại gốc repo rồi copy
  `graphify-out/` đè lên `code-graphs/<module>/monorepo/`, hoặc
  `extract <module> --code-only --out code-graphs/<module>/monorepo`.
- Trước khi tin graph: đối chiếu commit ghi trong snapshot với
  `git rev-parse HEAD` — lệch nhau là graph đã cũ.

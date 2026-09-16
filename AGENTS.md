# AGENTS.md — systemdocs (monorepo)

Repo gốc của hệ thống công chứng. Từ 15/09/2026 (MIN-83) đây là **monorepo**:
các repo con đã gộp vào làm module, phát triển trực tiếp tại đây trên nhánh
`consolidate/monorepo` — nhánh phát triển duy nhất. Repo cũ trên GitHub
(`notary_v2`, `upload_lab`, `notaryoffice`) chỉ còn vai trò archive đóng băng.

Nhánh `main` vẫn là bản tài liệu cũ trước gộp — **không merge runtime vào
`main`**.

## Cấu trúc

```text
├── notary_v2/      # module: soạn thảo hồ sơ mới (FastAPI + Jinja2 + SQLite)
├── upload_lab/     # module: số hóa Word cũ → upload web CSDL tỉnh (PySide6 + Playwright)
├── shell/          # module: vỏ Electron + Python sidecar (desktopcommand.v1)
├── notaryoffice/   # module: theo dõi hồ sơ đang chạy — CHƯA CÓ CODE, chỉ spec
├── contracts/      # contract đã duyệt giữa các module + vocabulary chung
├── docs/g1/        # tài liệu lộ trình G1/Electron + draft MIN-* (lịch sử/tham chiếu)
└── code-graphs/    # graphify snapshot: <module>/monorepo/graphify-out/ là bản mới nhất
```

## Nguồn sự thật (SOT) — ai quyết định cái gì

| Tầng | File | Phạm vi |
|---|---|---|
| Module | `<module>/docs/SPEC.md` | **SOT duy nhất về nghiệp vụ** của module đó |
| Module | `<module>/AGENTS.md` | quyền hạn, quy trình, review gate của module |
| Repo | `TECH_STACK.md` | công nghệ đã chọn + quy tắc thêm công nghệ mới |
| Repo | `SYSTEM_ARCHITECTURE.md` | ranh giới, ownership dữ liệu giữa các module |
| Repo | `contracts/` | contract đã duyệt + chuẩn hóa khóa định danh |
| Repo | `OPEN_DECISIONS.md` | câu hỏi chưa chốt + phương án đã loại |
| Repo | `VISION.md` | bài toán, nguyên tắc, điều cố tình không làm |

Khi docs root xung đột với docs/code của module: **module thắng về hành vi nội
bộ** — và mâu thuẫn phải được sửa lại ở root.

## Quy tắc khi sửa repo này

- Mọi mô tả module phải **kiểm chứng bằng file thật** trong repo (đường dẫn +
  số dòng), không viết theo suy luận hay tài liệu cũ của repo bên ngoài.
  Đường `D:\...` trong tài liệu cũ là từ trước khi gộp — giờ code ở ngay trong
  repo.
- Ghi rõ **cái gì KHÔNG có** ngang với cái gì có. Phần lớn lỗi cũ là giả định
  tồn tại một luồng dữ liệu không tồn tại.
- Phân biệt rõ **hiện trạng** và **dự định**. `notaryoffice/` chưa có code —
  `docs/SPEC.md` của nó là đặc tả, không phải hệ thống đang chạy.
- Không tự chốt mục nào đang mở (🔴) trong `OPEN_DECISIONS.md`.
- `excelTK` là dự án riêng, ngoài phạm vi hệ thống.
- Mọi lựa chọn công nghệ ghi ở `TECH_STACK.md`, không rải trong file khác.
  Thêm công nghệ mới cho một việc đã có công nghệ: phải qua 4 bước ở
  `TECH_STACK.md` §2.
- Đích đến là **một hệ thống dùng chung database**. Phân biệt *hiện trạng*
  (module độc lập về nghiệp vụ) với *đích đến*; `shell/` đã là kênh gọi thật
  vào hai engine — không viết lại mô tả "ba sản phẩm độc lập vĩnh viễn".
- Không tạo contract tích hợp mới rồi tự implement trong cùng một task.
- Task/issue được quản lý trên **Linear (team MIN, project systemdocs)** —
  không tạo file task/plan/todo mới trong repo gốc. Mỗi module giữ workflow
  riêng theo `AGENTS.md` của nó.

## Quy tắc chọn tool cho agent

- Biết rõ file, symbol hoặc chuỗi lỗi: tìm kiếm có giới hạn rồi đọc đúng đoạn
  source; dùng LSP nếu client đã cung cấp.
- Cần quan hệ qua nhiều file, caller/callee, dependency hoặc ownership: dùng
  graph Graphify trong `code-graphs/<module>/monorepo/graphify-out/graph.json`:
  `D:\graphify\.venv\Scripts\graphify.exe query "<câu hỏi>" --graph <path>`.
  Bắt đầu hẹp (depth 1–2); graph chỉ dẫn đường — kết luận hành vi phải đọc
  source thật. Graph cũ/thiếu thì chạy `graphify update <module>` hoặc
  `extract <module> --code-only` rồi copy `graphify-out/` vào `code-graphs/`.
- Các snapshot `code-graphs/<repo>/<nhánh-cũ>/` là **trước khi gộp** — chỉ để
  tham chiếu lịch sử, nguồn `D:\...` có thể không còn.
- Log, JSON/CSV, output build/test hoặc dữ liệu lớn: dùng context-mode khi
  capability đã được đăng ký (`ctx_execute`, `ctx_batch_execute`,
  `ctx_index`/`ctx_fetch_and_index`, `ctx_search`) để lọc trước khi đưa vào
  context. Kết quả tool đã nhỏ thì đọc trực tiếp, không bọc thêm.
- Không tự cài tool, bật daemon, tạo watcher, hay tạo contract mới tùy ý.
- Sau thay đổi code ở module, chạy check theo `AGENTS.md`/verify script của
  module đó (`notary_v2/verify.bat`, `upload_lab` unittest, `shell` npm test +
  contract test). Thay đổi chỉ ở Markdown thì kiểm tra diff và tính nhất quán.

# AGENTS.md — systemdocs

Folder tài liệu cấp cha, đồng thời là **file rule duy nhất của monorepo**.
`main` **không có code, không có runtime**.

Ngoại lệ owner chốt ngày 14/09/2026: nhánh `electron-system-shell` là nhánh
tích hợp cấp hệ thống và được phép chứa runtime Electron sau khi spec/contract
tương ứng được duyệt. Không merge runtime vào `main`; xem
`docs/architecture/ELECTRON_G1_PLAN.md`.

Nhánh `consolidate/monorepo` (base `electron-system-shell`) hiện chứa snapshot
của ba sản phẩm nghiệp vụ và shell. Đích mới dành `zalo/` cho module thứ tư:

| Thư mục | Nguồn | Nội dung |
|---|---|---|
| `shell/` | `electron-system-shell` | Vỏ Electron + Python sidecar FastAPI loopback |
| `notary_v2/` | `notary_v2` branch `consolidate/latest` | FastAPI nghiệp vụ công chứng (đã gộp 4 nhánh codex) |
| `upload_lab/` | `upload_lab` branch `consolidate/latest` | Số hóa + upload (đã gộp 2 nhánh POC) |
| `notaryoffice/` | `notaryoffice` `main` | Tài liệu intent, chưa có code |

zalo đã được tách thành repo riêng D:\zalo-intake
## Cấu trúc thư mục

```
├─ AGENTS.md            # File rule duy nhất (file này)
├─ README.md            # Chỉ mục cho người đọc
├─ docs/
│  ├─ architecture/     # SOT cấp hệ thống, giá trị dài hạn
│  └─ product/          # Spec theo feature/issue (MIN-*, G1-SM) + specs/
├─ contracts/           # Contract đã duyệt + entities.md
├─ code-graphs/         # Graphify snapshots — knowledge asset dùng chung, committed
├─ .agent/
│  ├─ tasks/<ID>/       # Trạng thái thực thi theo Linear issue — committed
│  ├─ templates/        # Template brief/progress/decisions/handoff
│  └─ scratch/          # Ghi tạm — gitignore
├─ .tmp/  .cache/  logs/  artifacts/   # Bãi rác chính thức — gitignore
└─ notary_v2/  upload_lab/  shell/  notaryoffice/   # Snapshot hiện có
   zalo/                                            # Dành cho module thứ tư, chưa migrate
```

## Quy tắc ghi file cho agent

### Nguồn sự thật (SOT)

- **Linear là SOT của task**: mô tả, acceptance criteria, trạng thái issue.
  Tìm issue trước khi làm; tạo issue trước khi implement yêu cầu mới; dẫn ID
  issue trong commit/handoff. Không viết lại mô tả issue vào file trong repo.
- `docs/` chỉ chứa tài liệu **dài hạn**: kiến trúc tổng ở `docs/architecture/`,
  spec theo feature ở `docs/product/`. File chỉ vào `docs/` khi nội dung còn
  đúng và còn được tra cứu sau khi task kết thúc. Không task-log, không note
  tạm, không draft một lần.
- `contracts/` giữ nguyên quy tắc contract-trước-code (`contracts/README.md`).

### Trạng thái thực thi → `.agent/tasks/<LINEAR-ID>/`

- Task gắn issue Linear thì tạo `.agent/tasks/<ID>/` gồm `brief.md`,
  `progress.md`, `decisions.md` (khi có quyết định cần ghi), `handoff.md` —
  template ở `.agent/templates/`.
- Agent làm đến đâu ghi vào `progress.md` đến đó. Khi ngắt kết nối/sự cố,
  agent khác đọc `brief.md` + `progress.md` (+ `handoff.md` nếu có) là làm
  tiếp được.
- Khi xong việc: cập nhật `progress.md`/`handoff.md` **và** SOT liên quan
  (`docs/`, spec repo con), rồi **xóa file tạm** trong scratch. Task folder
  giữ lại làm record.

### File tạm → bãi rác chính thức (đã gitignore)

`.agent/scratch/`, `.tmp/`, `.cache/`, `logs/`, `artifacts/`

- Note tạm, output thử nghiệm, log chạy, script một lần, dump, file trung
  gian: ghi vào các folder này — **không** ghi vào root hay `docs/`.
- Không commit nội dung các folder này. Dọn khi xong task.

### Cấm

- Không tạo `.md` mới ở root — root chỉ có `AGENTS.md` + `README.md`.
- Không tạo `AGENTS.md`/`agent.md`/`memory-bank/` trong repo con — rule của
  repo con ghi trong spec/SOT của repo đó (`README.md`, `docs/`, `intent.md`).
- Không tạo file task/handoff/spec/log rời rạc ngoài các nơi đã quy định ở
  trên. Skill, MCP, hook, sub-agent thuộc lớp tooling phía ngoài — không biến
  cấu trúc source repo phụ thuộc vào một agent cụ thể.
- Khi import snapshot mới từ repo gốc có kéo theo `AGENTS.md`/`agent.md`:
  loại bỏ ngay ở bước import, không để tồn tại song song với file này.

## Quyền hạn của folder này

Được mô tả: quan hệ giữa các sản phẩm, vocabulary/khóa định danh dùng chung,
quyết định kiến trúc xuyên sản phẩm, câu hỏi mở.

Không được mô tả: hành vi nội bộ của một sản phẩm. Đó là việc của docs trong
repo đó. Khi xung đột, **repo con thắng** — và mâu thuẫn phải được sửa ở đây.

## Bản đồ file

| File | Nội dung |
|---|---|
| `README.md` | Chỉ mục, bốn module đích và hiện trạng, đọc gì khi nào |
| `docs/architecture/VISION.md` | Bài toán, nguyên tắc chung, điều cố tình không làm |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | Ranh giới sản phẩm, sở hữu dữ liệu, kiến trúc dự kiến `notaryoffice` |
| `docs/architecture/PROJECTS.md` | Từng repo: giải bài toán gì — feature gì — công nghệ gì |
| `docs/architecture/TECH_STACK.md` | Công nghệ đã chọn + quy tắc thêm công nghệ mới + ràng buộc để gộp DB không xung đột |
| `docs/architecture/OPEN_DECISIONS.md` | Câu hỏi chưa chốt + phương án đã loại |
| `docs/architecture/COMPONENT_MAP.md` | Bản đồ component/ownership đề xuất — draft MIN-57 |
| `docs/architecture/ELECTRON_G1_PLAN.md` | Plan G1 chuyển nghiệp vụ sang Electron |
| `docs/product/` | Spec/draft theo issue (`MIN*`, `G1_SINGLE_MACHINE_*`); `specs/` chứa spec có ngày |
| `contracts/entities.md` | Chuẩn hóa khóa định danh hồ sơ |
| `contracts/README.md` | Quy tắc contract-trước-code |
| `code-graphs/` | Graphify snapshots các repo con + README cách dùng |
| `.agent/` | `tasks/` trạng thái thực thi, `templates/` mẫu, `scratch/` tạm |

## Quy tắc chọn tool cho agent

- Biết rõ file, symbol hoặc chuỗi lỗi: tìm kiếm có giới hạn rồi đọc đúng đoạn
  source; dùng LSP nếu client đã cung cấp.
- Cần quan hệ qua nhiều file, caller/callee, dependency hoặc ownership: dùng
  truy vấn Graphify hiện có nếu client/tool đã cung cấp. Bắt đầu hẹp (depth
  1–2); nếu graph thiếu, cũ hoặc bị cắt thì đối chiếu source hiện tại và chỉ
  refresh khi task cần. Không rebuild toàn bộ graph cho sửa nhỏ.

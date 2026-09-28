# AGENTS.md — systemdocs

Folder tài liệu cấp cha, đồng thời là **file rule duy nhất của monorepo**.
`main` **không có code, không có runtime**.

Ngoại lệ owner chốt ngày 14/09/2026: nhánh `electron-system-shell` là nhánh
tích hợp cấp hệ thống và được phép chứa runtime Electron sau khi spec/contract
tương ứng được duyệt. Không merge runtime vào `main`; xem
`docs/architecture/ELECTRON_G1_PLAN.md`.

Nhánh `consolidate/monorepo` (base `electron-system-shell`) hiện chứa snapshot
của ba sản phẩm nghiệp vụ, shell và module kỹ thuật Zalo:

| Thư mục | Nguồn | Nội dung |
|---|---|---|
| `shell/` | `electron-system-shell` | Vỏ Electron + Python sidecar FastAPI loopback |
| `notary_v2/` | `notary_v2` branch `consolidate/latest` | FastAPI nghiệp vụ công chứng (đã gộp 4 nhánh codex) |
| `upload_lab/` | `upload_lab` branch `consolidate/latest` | Số hóa + upload (đã gộp 2 nhánh POC) |
| `notaryoffice/` | `notaryoffice` `main` | Tài liệu intent, chưa có code |
| `zalo/` | `D:\zalo-intake` | Snapshot một chiều của engine Zalo; repo độc lập là nguồn gốc |

Zalo đã được tách thành repo riêng `D:\zalo-intake`; xem `zalo/README.md` để
phân biệt repo nguồn với snapshot ở đây. Bản đồ tri thức vẫn có bốn phần sản
phẩm/định hướng; Zalo là nguồn đầu vào kỹ thuật, không tạo phần thứ năm.
## Cấu trúc thư mục

```
├─ AGENTS.md            # File rule duy nhất (file này)
├─ README.md            # Chỉ mục cho người đọc
├─ docs/
│  ├─ architecture/     # Bản đồ tri thức + SOT xuyên sản phẩm
│  └─ product/          # Tài liệu UI chung và artifact liên sản phẩm đã có
├─ contracts/           # Contract đã duyệt + entities.md
├─ code-graphs/         # Graphify snapshots — knowledge asset dùng chung, committed
├─ .agent/
│  ├─ tasks/<ID>/       # Trạng thái thực thi theo Linear issue — committed
│  ├─ templates/        # Template brief/progress/decisions/handoff
│  └─ scratch/          # Ghi tạm — gitignore
├─ .tmp/  .cache/  logs/  artifacts/   # Bãi rác chính thức — gitignore
└─ notary_v2/  upload_lab/  shell/  notaryoffice/  zalo/  # Snapshot hiện có
```

## Quy tắc ghi file cho agent

### Nguồn sự thật (SOT)

- **Linear là SOT của task**: mô tả, acceptance criteria, trạng thái issue.
  Tìm issue trước khi làm; tạo issue trước khi implement yêu cầu mới; dẫn ID
  issue trong commit/handoff. Không viết lại mô tả issue vào file trong repo.
- **Một bản đồ tri thức:** `docs/architecture/KNOWLEDGE.md` chia đúng bốn phần:
  tầm nhìn chung, `notary_v2`, `upload_lab`, `notaryoffice`. Mở bản đồ trước khi
  thêm/sửa tài liệu; bảng này chỉ định file nào sở hữu hạng mục và flow nào.
- `docs/` chỉ chứa tài liệu **dài hạn**. Kiến trúc xuyên sản phẩm ở
  `docs/architecture/`; quy tắc/hành vi bên trong sản phẩm ở docs của module
  đó. `docs/product/` giữ tài liệu UI chung và artifact liên sản phẩm đã có,
  **không** là nơi mặc định tạo spec nghiệp vụ mới theo issue. Không task-log,
  note tạm hoặc draft một lần trong `docs/`.
- `contracts/` giữ nguyên quy tắc contract-trước-code (`contracts/README.md`).
- Khi owner giải thích **tại sao** chọn một quy tắc, giữ nguyên ý, ví dụ và ngoại
  lệ cùng nguồn/ngày; bản diễn giải của agent phải tách riêng. Ghi đúng nơi sở
  hữu lâu dài theo `docs/architecture/KNOWLEDGE.md`. Thiếu lý do thì đánh dấu
  thiếu, không suy đoán từ code hoặc bản nháp.

### Trước khi tạo hoặc sửa tài liệu dài hạn

1. Xác định một trong bốn phần ở `KNOWLEDGE.md`, rồi mở file sở hữu và README
   của module. Tìm trong file hiện có trước; **ưu tiên sửa đúng mục** thay vì
   tạo một file `spec`, `flow`, `ux`, `decisions` hay `index` mới cho cùng nội dung.
2. Chọn đúng một nơi sở hữu **mỗi quy tắc**. File tổng và file UI/contract chỉ
   dẫn tới nơi đó, không viết lại thành phiên bản thứ hai. Nếu phải tách nội
   dung lớn, ghi rõ phần chuyển quyền sở hữu trong file cũ và file mới.
3. File mới chỉ hợp lệ khi nó có phạm vi dài hạn riêng, không trùng file đã có.
   Trong **cùng thay đổi**, ghi đầu file mục đích, trạng thái (`Draft`/`Approved`/
   `Superseded`), phạm vi, nguồn quyết định; thêm link và vai trò của nó vào
   `KNOWLEDGE.md` và README của module nếu module có README. Thiếu một bước thì
   chưa tạo file mới; ghi việc cần làm vào Linear/task thay vì thả file rời.
4. Quyết định mới về nghiệp vụ vào mục quyết định/“Tại sao?” của spec sở hữu;
   quyết định kiến trúc lớn chỉ tách thành ADR khi có đánh đổi cần giữ riêng và
   README module đăng ký nó. `.agent/tasks/<ID>/decisions.md` là lịch sử thực
   thi, không được làm nguồn quy tắc vĩnh viễn.
5. Trước khi xong task, soát link hai chiều, trạng thái bản nháp/đã duyệt, và
   xóa hoặc đánh dấu `Superseded` tài liệu bị thay thế. Không để hai file đều
   tự nhận là SOT cho cùng hành vi.

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
- Không tạo chỉ mục quyết định, kho `secondbrain` hay cây tài liệu song song
  với `KNOWLEDGE.md` và docs của module. Tìm kiếm/RAG sau này chỉ đọc các nguồn
  này kèm trạng thái, không có quyền tự chốt quy tắc.
- Khi import snapshot mới từ repo gốc có kéo theo `AGENTS.md`/`agent.md`:
  loại bỏ ngay ở bước import, không để tồn tại song song với file này.

## Quyền hạn của folder này

Được mô tả: quan hệ giữa các sản phẩm, vocabulary/khóa định danh dùng chung,
quyết định kiến trúc xuyên sản phẩm, câu hỏi mở.

Không được mô tả: hành vi nội bộ của một sản phẩm. Đó là việc của docs trong
repo đó. Khi xung đột, **repo con thắng** — và mâu thuẫn phải được sửa ở đây.

## Bản đồ file

`README.md` là cửa vào ngắn. **`docs/architecture/KNOWLEDGE.md` là bản đồ tra cứu
duy nhất**: bốn phần, từng hạng mục, flow và file sở hữu. Không duy trì thêm
một bảng file tổng quát khác trong `AGENTS.md` hoặc một `DECISION_INDEX.md`.
`contracts/README.md` quản lý contract; `.agent/` chỉ quản lý trạng thái task;
`code-graphs/` là snapshot để tìm code, không phải spec nghiệp vụ.

## Quy tắc chọn tool cho agent

- Biết rõ file, symbol hoặc chuỗi lỗi: tìm kiếm có giới hạn rồi đọc đúng đoạn
  source; dùng LSP nếu client đã cung cấp.
- Cần quan hệ qua nhiều file, caller/callee, dependency hoặc ownership: dùng
  truy vấn Graphify hiện có nếu client/tool đã cung cấp. Bắt đầu hẹp (depth
  1–2); nếu graph thiếu, cũ hoặc bị cắt thì đối chiếu source hiện tại và chỉ
  refresh khi task cần. Không rebuild toàn bộ graph cho sửa nhỏ.

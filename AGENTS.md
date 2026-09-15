# AGENTS.md — systemdocs

Folder tài liệu cấp cha. `main` **không có code, không có runtime**.

Ngoại lệ owner chốt ngày 14/09/2026: nhánh `electron-system-shell` là nhánh
tích hợp cấp hệ thống và được phép chứa runtime Electron sau khi spec/contract
tương ứng được duyệt. Không merge runtime vào `main`; xem `ELECTRON_G1_PLAN.md`.

Nhánh `consolidate/monorepo` (base `electron-system-shell`) chứa toàn bộ code
của ba sản phẩm dưới dạng snapshot để phát triển thống nhất một nhánh:

| Thư mục | Nguồn | Nội dung |
|---|---|---|
| `shell/` | `electron-system-shell` | Vỏ Electron + Python sidecar FastAPI loopback |
| `notary_v2/` | `notary_v2` branch `consolidate/latest` | FastAPI nghiệp vụ công chứng (đã gộp 4 nhánh codex) |
| `upload_lab/` | `upload_lab` branch `consolidate/latest` | Số hóa + upload (đã gộp 2 nhánh POC) |
| `notaryoffice/` | `notaryoffice` `main` | Tài liệu intent, chưa có code |

Mỗi thư mục con giữ nguyên `AGENTS.md`/`README.md` của repo gốc — khi sửa code
trong `notary_v2/` hay `upload_lab/`, tuân theo quy tắc của thư mục đó. Đây là
snapshot một chiều: repo con vẫn tồn tại độc lập; quyết định repo nào là nguồn
chính thức chưa chốt.

## Quyền hạn của folder này

Được mô tả: quan hệ giữa các sản phẩm, vocabulary/khóa định danh dùng chung,
quyết định kiến trúc xuyên sản phẩm, câu hỏi mở.

Không được mô tả: hành vi nội bộ của một sản phẩm. Đó là việc của docs trong
repo đó. Khi xung đột, **repo con thắng** — và mâu thuẫn phải được sửa ở đây.

## Quy tắc khi sửa folder này

- Mọi mô tả repo con phải **kiểm chứng bằng file thật** (đường dẫn + số dòng),
  không viết theo suy luận. Tài liệu cũ ở đây từng sai nhiều vì lý do này.
- Ghi rõ **cái gì KHÔNG có** ngang với cái gì có. Phần lớn lỗi cũ là giả định
  tồn tại một luồng dữ liệu không tồn tại.
- Phân biệt rõ **hiện trạng** và **dự định**. `notaryoffice` chưa có code.
- Không tự chốt mục nào đang mở (🔴) trong `OPEN_DECISIONS.md`.
- `excelTK` là dự án riêng, ngoài phạm vi hệ thống công chứng và G1 Electron.
- Mọi lựa chọn công nghệ ghi ở `TECH_STACK.md`, không rải trong file khác. Thêm
  công nghệ mới cho một việc đã có công nghệ: phải qua 4 bước ở `TECH_STACK.md` §2.
- Đích đến là **một hệ thống dùng chung database**. Đừng viết lại các mô tả kiểu
  "ba sản phẩm độc lập vĩnh viễn" — phân biệt *hiện trạng* với *đích đến*.
- Không tạo contract tích hợp mới rồi tự implement trong cùng một task.

## Bản đồ file

| File | Nội dung |
|---|---|
| `README.md` | Chỉ mục, ba sản phẩm, đọc gì khi nào |
| `VISION.md` | Bài toán, nguyên tắc chung, điều cố tình không làm |
| `SYSTEM_ARCHITECTURE.md` | Ranh giới sản phẩm, sở hữu dữ liệu, kiến trúc dự kiến `notaryoffice` |
| `PROJECTS.md` | Từng repo: giải bài toán gì — feature gì — công nghệ gì |
| `TECH_STACK.md` | Công nghệ đã chọn + quy tắc thêm công nghệ mới + ràng buộc để gộp DB không xung đột |
| `contracts/entities.md` | Chuẩn hóa khóa định danh hồ sơ |
| `contracts/README.md` | Quy tắc contract-trước-code |
| `OPEN_DECISIONS.md` | Câu hỏi chưa chốt + phương án đã loại |

## Quy tắc chọn tool cho agent

Các quy tắc này chỉ hướng dẫn cách agent đọc và kiểm chứng tài liệu/code của
repo con; folder `systemdocs` vẫn là tài liệu, không có runtime và không chạy
Graphify/context-mode tại đây.

- Biết rõ file, symbol hoặc chuỗi lỗi: tìm kiếm có giới hạn rồi đọc đúng đoạn
  source; dùng LSP nếu client đã cung cấp.
- Cần quan hệ qua nhiều file, caller/callee, dependency hoặc ownership: dùng
  truy vấn Graphify hiện có nếu client/tool đã cung cấp. Bắt đầu hẹp (depth
  1–2); nếu graph thiếu, cũ hoặc bị cắt thì đối chiếu source hiện tại và chỉ
  refresh khi task cần. Không rebuild toàn bộ graph cho sửa nhỏ.
- Log, JSON/CSV, output build/test hoặc dữ liệu lớn: dùng context-mode khi
  capability đã được đăng ký (`ctx_execute`, `ctx_execute_file`,
  `ctx_batch_execute`, `ctx_index`/`ctx_fetch_and_index`, `ctx_search`) để lọc,
  đếm hoặc tổng hợp trước khi đưa vào context. `ctx_search` chỉ tìm trong nội
  dung đã index; giữ exit code, lỗi hữu ích và đường dẫn tới dữ liệu đầy đủ.
- Kết quả tool đã nhỏ, kể cả truy vấn graph có giới hạn: đọc trực tiếp, không
  bọc thêm qua context-mode.
- Không tự cài tool, bật daemon, tạo watcher, full-index hoặc tạo contract mới
  trong folder này. Nếu Graphify/context-mode không có trong client hiện tại,
  dùng source/tìm kiếm thông thường và ghi rõ trong bàn giao.
- Sau thay đổi code ở repo con, chạy check phù hợp với repo đó; thay đổi chỉ ở
  Markdown thì kiểm tra diff và tính nhất quán tài liệu.

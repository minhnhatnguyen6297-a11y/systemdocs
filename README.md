# Notary System — Hub tầm nhìn & kiến trúc

Nguồn tham chiếu cấp cha cho hệ sinh thái phần mềm công chứng.
Khi sửa code nội bộ, đọc tài liệu của module sở hữu. **Trước khi tạo hoặc sửa
tài liệu dài hạn**, mở [bản đồ tri thức](./docs/architecture/KNOWLEDGE.md);
khi task đụng ranh giới giữa các sản phẩm thì đọc thêm kiến trúc và contract
được bản đồ dẫn tới.

Một ngoại lệ bắt buộc: **trước khi chọn một công nghệ mới** (OCR provider khác,
ORM khác, queue khác, framework UI khác) thì phải đọc
[`TECH_STACK.md`](./docs/architecture/TECH_STACK.md). Ba module nghiệp vụ hướng
tới database chung; Zalo là module thứ tư có thể chạy riêng với DB/session riêng.

## Bốn module trong phạm vi đích

| Sản phẩm | Đường dẫn (trên nhánh `consolidate/monorepo`) | Làm gì | Trạng thái |
|---|---|---|---|
| `notary_v2` | `./notary_v2` (snapshot từ `D:\notary_v2`) | Soạn thảo hồ sơ tự động; nhận raw OCR Zalo rồi phân tích, cho người dùng duyệt | Đang phát triển; code Zalo legacy vẫn nằm ở đây |
| `upload_lab` | `./upload_lab` (snapshot từ `D:\upload_lab_repo`) | Số hóa hồ sơ giấy: Word cũ → trường có cấu trúc → upload web CSDL công chứng tỉnh | Đang phát triển; chưa triển khai production |
| `notaryoffice` | `./notaryoffice` (snapshot từ `D:\notaryoffice`) | Quản lý hồ sơ tại văn phòng: thu dấu vết từ máy con → tự dựng record hồ sơ | Tài liệu, chưa code |
| `zalo` | `./zalo` (snapshot từ repo nguồn `D:\zalo-intake`) | Thu nhận Zalo, giữ media tạm, gọi Qwen OCR và giao gói chữ raw | Repo độc lập là SOT engine; snapshot một chiều trong monorepo |
| `shell` | `./shell` | Vỏ Electron + Python sidecar FastAPI loopback | POC tích hợp; contract production chưa duyệt |

`shell` là hạ tầng giao diện của hệ thống, không tính là module nghiệp vụ thứ năm.
Zalo là module đầu vào kỹ thuật, không phải một phần sản phẩm thứ năm trong
[bản đồ tri thức](./docs/architecture/KNOWLEDGE.md). Chỉnh engine ở repo nguồn;
`zalo/` trong monorepo là snapshot một chiều theo `zalo/README.md`.

Ngoài phạm vi: `researchskill` (`D:\researchskill`) là skill hỗ trợ coding,
không phải phân hệ công chứng.

`excelTK` là dự án riêng, không thuộc phạm vi hệ thống này. Kế hoạch chuyển
nghiệp vụ thật sang Electron nằm ở
[`ELECTRON_G1_PLAN.md`](./docs/architecture/ELECTRON_G1_PLAN.md)
trên nhánh `electron-system-shell`; `main` tiếp tục chỉ chứa tài liệu.

## Bắt đầu đọc

Mở **[bản đồ tri thức](./docs/architecture/KNOWLEDGE.md)** để đi từ một trong
bốn phần — tầm nhìn chung, soạn thảo tự động, số hóa tài liệu cũ, quản lý vận
hành — tới đúng flow, spec và nơi giữ quyết định. Đây là chỉ mục tài liệu duy
nhất; không tạo thêm chỉ mục quyết định theo issue hoặc theo tên file.

Trước khi agent thêm/sửa tài liệu, đọc [quy tắc ghi file](./AGENTS.md). Task
và trạng thái nghiệm thu nằm trên Linear; tài liệu trong module sở hữu hành vi
nghiệp vụ của module đó.

## Cấu trúc folder

| Chỗ | Dùng cho |
|---|---|
| `docs/architecture/` | Bản đồ tri thức và tài liệu xuyên sản phẩm, giá trị dài hạn |
| `docs/product/` | UI chung và artifact liên sản phẩm đã có; spec nghiệp vụ mới thuộc module sở hữu |
| `contracts/` | Contract đã duyệt giữa các sản phẩm |
| `code-graphs/` | Graphify snapshots các repo con |
| `zalo/` | Snapshot một chiều từ repo Zalo độc lập; xem `zalo/README.md` |
| `.agent/tasks/` | Trạng thái thực thi theo Linear issue |
| `.agent/scratch/`, `.tmp/`, `.cache/`, `logs/`, `artifacts/` | File tạm — gitignore |

## Nguồn sự thật

Folder này mô tả **quan hệ giữa các sản phẩm**. Hành vi bên trong một sản phẩm
do docs của repo đó quyết định (`notary_v2/docs/`, `upload_lab/README.md` +
`upload_lab/docs/`, `notaryoffice/intent.md`). Khi folder này xung đột với repo
con, repo con thắng về hành vi nội bộ — và mâu thuẫn đó phải được báo lại để
sửa ở đây.

Linear là SOT của task/issue; `.agent/tasks/` chỉ lưu trạng thái thực thi.
Quy ước chi tiết ở [`AGENTS.md`](./AGENTS.md).

# Notary System — Hub tầm nhìn & kiến trúc

Nguồn tham chiếu cấp cha cho hệ sinh thái phần mềm công chứng.
Repo con **không** cần đọc folder này để làm việc hằng ngày — chỉ đọc khi task
đụng tới ranh giới giữa các sản phẩm, vocabulary dùng chung, hoặc quyết định
kiến trúc xuyên sản phẩm.

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
| `zalo` | `./zalo` (dành chỗ; repo độc lập chưa tạo, `D:\zalo-intake` là path dự kiến) | Thu nhận Zalo, giữ media tạm, gọi Qwen OCR và giao gói chữ raw | Chưa migrate code; chưa chạy độc lập |
| `shell` | `./shell` | Vỏ Electron + Python sidecar FastAPI loopback | POC tích hợp; contract production chưa duyệt |

`shell` là hạ tầng giao diện của hệ thống, không tính là module nghiệp vụ thứ năm.
Task chuyển Zalo sẽ chốt repo nguồn chính thức và cách đưa snapshot vào
monorepo; hiện không có hai nơi cùng được sửa tự do.

Ngoài phạm vi: `researchskill` (`D:\researchskill`) là skill hỗ trợ coding,
không phải phân hệ công chứng.

`excelTK` là dự án riêng, không thuộc phạm vi hệ thống này. Kế hoạch chuyển
nghiệp vụ thật sang Electron nằm ở
[`ELECTRON_G1_PLAN.md`](./docs/architecture/ELECTRON_G1_PLAN.md)
trên nhánh `electron-system-shell`; `main` tiếp tục chỉ chứa tài liệu.

## Đọc gì khi nào

| Cần gì | File |
|---|---|
| Tại sao có hệ thống này, các module ghép lại thành gì | [`VISION.md`](./docs/architecture/VISION.md) |
| Ranh giới sản phẩm, sản phẩm nào sở hữu dữ liệu nào | [`SYSTEM_ARCHITECTURE.md`](./docs/architecture/SYSTEM_ARCHITECTURE.md) |
| Sáu lớp thành phần chung, owner đề xuất và mức reuse — draft MIN-57 | [`COMPONENT_MAP.md`](./docs/architecture/COMPONENT_MAP.md) |
| Repo nào giải bài toán gì — feature gì — công nghệ gì | [`PROJECTS.md`](./docs/architecture/PROJECTS.md) |
| **Trước khi chọn công nghệ mới hoặc ra quyết định kiến trúc** | [`TECH_STACK.md`](./docs/architecture/TECH_STACK.md) |
| Vocabulary & schema dùng chung giữa các sản phẩm | [`contracts/README.md`](./contracts/README.md) |
| Cái gì đã chốt, cái gì chưa chốt — đừng tự quyết | [`OPEN_DECISIONS.md`](./docs/architecture/OPEN_DECISIONS.md) |
| Spec/draft theo từng issue (MIN-*, G1-SM) | [`docs/product/`](./docs/product/) |
| Zalo Inbox — nguồn chuẩn, bản nháp và thứ tự đọc | [`Zalo Intake — bắt đầu tại đây`](./notary_v2/docs/platform/zalo-document-inbox/README.md) |
| Review kết quả POC conversion/OCR của MIN-52 và MIN-59 | [`MIN61_CONVERSION_OCR_DECISION.md`](./docs/product/MIN61_CONVERSION_OCR_DECISION.md) |
| Quy tắc khi sửa chính folder này + nơi agent được ghi file | [`AGENTS.md`](./AGENTS.md) |

## Cấu trúc folder

| Chỗ | Dùng cho |
|---|---|
| `docs/architecture/` | Tài liệu SOT cấp hệ thống, giá trị dài hạn |
| `docs/product/` | Spec theo feature/issue (`specs/` chứa spec có ngày) |
| `contracts/` | Contract đã duyệt giữa các sản phẩm |
| `code-graphs/` | Graphify snapshots các repo con |
| `zalo/` | Dành cho snapshot module Zalo sau task migration; hiện chưa có code |
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

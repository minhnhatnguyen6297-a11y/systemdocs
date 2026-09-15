# Notary System — Hub tầm nhìn & kiến trúc

Nguồn tham chiếu cấp cha cho hệ sinh thái phần mềm công chứng.
Repo con **không** cần đọc folder này để làm việc hằng ngày — chỉ đọc khi task
đụng tới ranh giới giữa các sản phẩm, vocabulary dùng chung, hoặc quyết định
kiến trúc xuyên sản phẩm.

Một ngoại lệ bắt buộc: **trước khi chọn một công nghệ mới** (OCR provider khác,
ORM khác, queue khác, framework UI khác) thì phải đọc
[`TECH_STACK.md`](./TECH_STACK.md). Ba repo sẽ gộp về một database dùng chung;
chọn lệch nhau bây giờ là viết lại sau.

## Ba sản phẩm trong phạm vi

| Sản phẩm | Đường dẫn | Làm gì | Trạng thái |
|---|---|---|---|
| `notary_v2` | `D:\notary_v2` | Soạn thảo hồ sơ tự động (thừa kế, sinh Word, intake giấy tờ, Zalo inbox) | Đang chạy |
| `upload_lab` | `D:\upload_lab_repo` | Số hóa hồ sơ giấy: Word cũ → trường có cấu trúc → upload web CSDL công chứng tỉnh | Đang chạy |
| `notaryoffice` | `D:\notaryoffice` | Quản lý hồ sơ tại văn phòng: thu dấu vết từ máy con → tự dựng record hồ sơ | Tài liệu, chưa code |

Ngoài phạm vi: `researchskill` (`D:\researchskill`) là skill hỗ trợ coding,
không phải phân hệ công chứng.

## Đọc gì khi nào

| Cần gì | File |
|---|---|
| Tại sao có hệ thống này, ba sản phẩm ghép lại thành gì | [`VISION.md`](./VISION.md) |
| Ranh giới sản phẩm, sản phẩm nào sở hữu dữ liệu nào | [`SYSTEM_ARCHITECTURE.md`](./SYSTEM_ARCHITECTURE.md) |
| Sáu lớp thành phần chung, owner đề xuất và mức reuse — draft MIN-57 | [`COMPONENT_MAP.md`](./COMPONENT_MAP.md) |
| Repo nào giải bài toán gì — feature gì — công nghệ gì | [`PROJECTS.md`](./PROJECTS.md) |
| **Trước khi chọn công nghệ mới hoặc ra quyết định kiến trúc** | [`TECH_STACK.md`](./TECH_STACK.md) |
| Vocabulary & schema dùng chung giữa các sản phẩm | [`contracts/README.md`](./contracts/README.md) |
| Cái gì đã chốt, cái gì chưa chốt — đừng tự quyết | [`OPEN_DECISIONS.md`](./OPEN_DECISIONS.md) |
| Review kết quả POC conversion/OCR của MIN-52 và MIN-59 | [`MIN61_CONVERSION_OCR_DECISION.md`](./MIN61_CONVERSION_OCR_DECISION.md) |
| Quy tắc khi sửa chính folder này | [`AGENTS.md`](./AGENTS.md) |

## Nguồn sự thật

Folder này mô tả **quan hệ giữa các sản phẩm**. Hành vi bên trong một sản phẩm
do docs của repo đó quyết định (`notary_v2/AGENTS.md` → `docs/`,
`upload_lab_repo/README.md`, `notaryoffice/intent.md`). Khi folder này xung đột với repo con, repo con thắng về
hành vi nội bộ — và mâu thuẫn đó phải được báo lại để sửa ở đây.

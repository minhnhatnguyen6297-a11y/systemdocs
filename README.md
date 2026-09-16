# Notary System — monorepo

Monorepo của hệ thống phần mềm công chứng. Từ 15/09/2026 (Linear MIN-83) các
repo con đã gộp vào đây làm module; nhánh phát triển duy nhất là
`consolidate/monorepo`. Repo cũ trên GitHub chỉ còn archive.

## Các module

| Module | Làm gì | SOT nghiệp vụ | Trạng thái |
|---|---|---|---|
| `notary_v2/` | Soạn thảo hồ sơ mới: OCR giấy tờ, Case Workspace, engine thừa kế, sinh Word, Zalo inbox | [`notary_v2/docs/SPEC.md`](./notary_v2/docs/SPEC.md) | Đang phát triển; chưa production |
| `upload_lab/` | Số hóa kho Word cũ → trường có cấu trúc → upload web CSDL công chứng tỉnh | [`upload_lab/docs/SPEC.md`](./upload_lab/docs/SPEC.md) | Đang phát triển; chưa production |
| `shell/` | Vỏ desktop Electron + Python sidecar gọi hai engine qua `desktopcommand.v1` | [`shell/docs/SPEC.md`](./shell/docs/SPEC.md) | Đang phát triển (G1 một máy) |
| `notaryoffice/` | Theo dõi hồ sơ đang chạy: thu dấu vết máy trạm → tự dựng record | [`notaryoffice/docs/SPEC.md`](./notaryoffice/docs/SPEC.md) | **Chỉ có spec, chưa code** |

Ngoài phạm vi: `excelTK` (dự án riêng), `researchskill` (skill hỗ trợ coding).

## Đọc gì khi nào

| Cần gì | File |
|---|---|
| Tại sao có hệ thống này, các module ghép lại thành gì | [`VISION.md`](./VISION.md) |
| Nghiệp vụ của một module | `<module>/docs/SPEC.md` (bảng trên) |
| Ranh giới module, ai sở hữu dữ liệu nào | [`SYSTEM_ARCHITECTURE.md`](./SYSTEM_ARCHITECTURE.md) |
| **Trước khi chọn công nghệ mới hoặc ra quyết định kiến trúc** | [`TECH_STACK.md`](./TECH_STACK.md) |
| Contract đã duyệt + chuẩn hóa khóa định danh dùng chung | [`contracts/README.md`](./contracts/README.md) |
| Cái gì đã chốt, cái gì chưa chốt — đừng tự quyết | [`OPEN_DECISIONS.md`](./OPEN_DECISIONS.md) |
| Lộ trình Electron G1, draft spec MIN-*, handoff cũ | [`docs/g1/`](./docs/g1/) |
| Graph điều hướng code (graphify) | [`code-graphs/README.md`](./code-graphs/README.md) |
| Quy tắc khi sửa repo này | [`AGENTS.md`](./AGENTS.md) |

## Nguyên tắc nhanh

- Mỗi module có **một** `docs/SPEC.md` làm SOT nghiệp vụ duy nhất — đọc nó
  trước khi sửa nghiệp vụ của module đó.
- Task/issue quản lý trên **Linear** (team `MIN`, project `systemdocs`),
  không lưu task trong repo.
- Nối hai module = tích hợp = cần contract được duyệt trước
  ([`contracts/README.md`](./contracts/README.md)). `shell/` là kênh tích hợp
  đã duyệt duy nhất hiện nay.

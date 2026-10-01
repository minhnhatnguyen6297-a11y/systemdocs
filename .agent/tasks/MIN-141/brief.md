# MIN-141 — Chuẩn hóa dữ liệu Người/Tài sản

Linear: https://linear.app/minhnotary/issue/MIN-141

## Nguồn

Buổi rà soát DB/trường dữ liệu với owner ngày 29/09/2026 (session Devin).
Bắt đầu từ câu hỏi "thêm/bớt trường Người và Tài sản như thế nào".

## Đã chốt (owner)

- Mốc giấy tờ cũ/mới = **01/10/2024** (theo code; nói 01/07 là nhầm).
- Giữ upsert master tại `commit_stage`; xóa hồ sơ draft thì dọn
  `customers`/`properties` mồ côi **có kiểm tra tham chiếu**.
- Thống kê đếm qua hồ sơ, không đếm bảng `customers` trần.

## Còn mở

- `place_of_origin` chưa có cột `customers` — cố ý hay sót?
- Shared code giữa module: owner nghiêng về kéo ra code dùng chung;
  luật spec yêu cầu contract trước — cần chốt và cập nhật spec nếu đổi.
- Alembic cho `notary_v2` (migrate tay hiện lệch main.py vs sidecar).
- Bỏ `engine_state_json` (legacy) khi web cũ retire.

## Bằng chứng chính

`notary_v2/models.py`, `notary_v2/database.py`,
`notary_v2/services/case_workspace.py`, `shell/sidecar/notary_adapter.py`,
`contracts/notary-case-drafting/common.schema.json`.

# Brief — MIN-141

**Linear:** https://linear.app/minhnotary/issue/MIN-141 · **Ngày bắt đầu:** 2026-09-30 / Cập nhật: 2026-10-01 · **Nhánh:** `agent/mika/33d7e2146084`

## Mục tiêu

Chuẩn hóa dữ liệu Người (`customers`), Tài sản (`properties`), Hồ sơ (`inheritance_cases`) theo quyết định chốt ngày 29/09/2026 và chỉ đạo trực tiếp ngày 01/10/2026 từ Owner.

## Phạm vi

- Chuẩn hóa 6 trường lưu CSDL của Người (`ten`, `ngaysinh`, `ngaychet`, `sogiayto`, `ngaycap`, `diachi`).
- Chuẩn hóa các trường suy ra backend (@property): `loaigiayto` (mốc 01/10/2024; người chết), `noicap` (mốc 01/10/2024; người chết mốc sáp nhập 01/07/2025), `loaicutru` (mốc 01/10/2024).
- Sửa lỗi docstring lệch mốc "01/07/2024" -> "01/10/2024" trong `notary_v2/models.py`.
- Chuẩn hóa Bảng Tài sản: Loại bỏ trường `thoi_han` lẻ mồ côi; lưu theo cụm 3 trường `(loại đất, diện tích, thời hạn)` 1..20; quy ước định danh đa tài sản (`loaidat12`).
- Chuẩn hóa Bảng Hồ sơ: Thêm trường `noi_niem_yet`, `nguoi_nhan_uy_quyen`, `noi_dung_viec`; bố trí UI 3 dòng dưới tài sản, giảm 10% chiều cao ô nhập.
- Quy tắc chung về đặt tên trường: Tiếng Việt không dấu, viết liền số (`loaidat1`).
- Tạo issue NAIA-9 trên Multica để theo dõi triển khai Bảng dữ liệu xã cũ - mới sau sáp nhập 01/07/2025.
- Cập nhật tài liệu dài hạn: `contracts/entities.md`, `docs/spec/notary_v2/README.md`, `docs/spec/notary_v2/stage.md`, `docs/spec/notary_v2/input/property-rules.md`.

## Bằng chứng nghiệm thu

- Code `notary_v2/models.py` và `notary_v2/database.py` được cập nhật chính xác.
- Python tests cho `Customer` properties chạy thành công.
- Spec và contract được cập nhật đầy đủ, đồng bộ.
- Issue con cho bảng xã sáp nhập được tạo trên platform (`NAIA-9`).

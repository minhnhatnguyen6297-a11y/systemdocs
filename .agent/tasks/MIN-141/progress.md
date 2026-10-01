# Progress — MIN-141

## Trạng thái: In Review

## Việc đã hoàn thành (2026-10-01)

1. **Rà soát & kiểm tra hệ thống:**
   - Đối chiếu các trường Người, Tài sản, Hồ sơ trong `notary_v2/models.py`, `database.py`, `services/case_workspace.py`, `services/word_engine.py`.
   - Xác định lỗi docstring lệch mốc 01/07/2024 trong `Customer._moc_cccd_moi`.
   - Xác định thiếu sót trong `Customer.loai_giay_to` và `noi_cap` khi xử lý trường hợp người đã chết (`con_song == False`).

2. **Triển khai code backend:**
   - Cập nhật docstring `Customer._moc_cccd_moi` về chuẩn 01/10/2024.
   - Bổ sung logic phân biệt người sống vs người chết trong `Customer.loai_giay_to` và `Customer.noi_cap`.
   - Bổ sung property `Customer.loaicutru` ("Cư trú" / "Thường trú").
   - Bổ sung các trường `nguoi_nhan_uy_quyen` và `noi_dung_viec` vào `InheritanceCase` (`models.py`) và hàm `migrate_inheritance_cases_schema` (`database.py`).
   - Chạy kiểm chứng logic qua Python thành công.

3. **Tạo Issue trên nền tảng Multica:**
   - Tạo thành công issue `NAIA-9` (ID: `01a0f67d-45a0-7c32-8de4-f93d778d7f25`) với tiêu đề: *"Xây dựng bảng dữ liệu chuẩn hóa xã/phường cũ - mới sau sáp nhập 01/07/2025"*.

4. **Cập nhật tài liệu Spec & Contract dài hạn:**
   - `contracts/entities.md`: Bổ sung §8 (Từ điển dữ liệu Người & trường suy ra) và §9 (Chuẩn hóa Tài sản, Hồ sơ & Quy tắc đặt tên).
   - `docs/spec/notary_v2/README.md`: Di chuyển mục từ điển dữ liệu Người sang phần "Đã chốt", cập nhật các quyết định 01/10/2026.
   - `docs/spec/notary_v2/stage.md`: Cập nhật mục 5 (Quy tắc dữ liệu), mục 9 (Giao diện 3 dòng hồ sơ dưới tài sản), mục 10 (Lịch sử).
   - `docs/spec/notary_v2/input/property-rules.md`: Bổ sung ghi chú loại bỏ trường lẻ `thoi_han` mồ côi ở cấp tài sản.

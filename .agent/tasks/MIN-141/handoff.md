# Handoff — MIN-141

**Task:** MIN-141 / NAIA-6 — Chuẩn hóa dữ liệu Người/Tài sản  
**Người bàn giao:** Mika  
**Ngày bàn giao:** 2026-10-01  

## 1. Kết quả thực hiện

1. **Chuẩn hóa Người (`customers`):**
   - 6 trường lưu CSDL: `ten`, `ngaysinh`, `ngaychet`, `sogiayto`, `ngaycap`, `diachi`.
   - Các trường suy ra backend:
     * `loaigiayto`: Mốc 01/10/2024 (trước: Căn cước công dân; sau: Căn cước); Người chết: Trích lục khai tử (Bản sao)...
     * `noicap`: Mốc 01/10/2024 (trước: Cục CSQLHC về TTXH; sau: Bộ Công an); Người chết mốc 01/07/2025 (UBND xã cũ / UBND xã mới).
     * `loaicutru`: Mốc 01/10/2024 (trước: Thường trú; sau: Cư trú).
   - Code `notary_v2/models.py` đã được cập nhật logic đầy đủ.

2. **Chuẩn hóa Tài sản (`properties`):**
   - Loại bỏ trường lẻ `thoi_han` mồ côi.
   - Cụm Loại đất - Diện tích - Thời hạn đi liền nhau (`loaidat1..20`, `dientich1..20`, `thoihan1..20`). Khi có 3 tài sản, tài sản 2 đánh số kết hợp như `loaidat12`.

3. **Chuẩn hóa Hồ sơ (`inheritance_cases`):**
   - Thêm trường `noi_niem_yet`, `nguoi_nhan_uy_quyen`, `noi_dung_viec`.
   - Thêm migration trong `notary_v2/database.py`.
   - Đặc tả UI: 3 dòng hồ sơ dưới tài sản, giảm 10% chiều cao ô nhập.

4. **Tạo issue mới:**
   - Tạo issue `NAIA-9` (Xây dựng bảng dữ liệu chuẩn hóa xã/phường cũ - mới sau sáp nhập 01/07/2025) để phục vụ suy ra Nơi cấp giấy khai tử và Nơi niêm yết theo đất.

5. **Đồng bộ Spec & Contract:**
   - `contracts/entities.md` (§8, §9).
   - `docs/spec/notary_v2/README.md`.
   - `docs/spec/notary_v2/stage.md`.
   - `docs/spec/notary_v2/input/property-rules.md`.

## 2. Việc tiếp theo đề xuất

1. Triển khai issue `NAIA-9`: Xây dựng bảng tra cứu xã/phường sáp nhập và lookup service.
2. Cập nhật frontend Electron renderer (`shell/src/renderer/notary/case-drafting-view.js`):
   - Bổ sung 3 dòng của bảng hồ sơ dưới bảng tài sản (giảm 10% chiều cao ô).
   - Render và bind các cụm loại đất theo danh sách phẳng `loaidat1..20`.

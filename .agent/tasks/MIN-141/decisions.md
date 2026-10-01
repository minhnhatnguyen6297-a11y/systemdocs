# Decisions — MIN-141

## 2026-09-29 — Quyết định sơ bộ rà soát Người / Tài sản

- **Mốc phân biệt giấy tờ cũ/mới = 01/10/2024:** Theo code cũ `Customer._moc_cccd_moi` dùng `date(2024, 10, 1)`. Docstring ghi nhầm 01/07/2024 được sửa lại cho khớp.
- **Giữ hành vi upsert master tại `commit_stage`:** Không đổi sang cache thuần vì entity_id và dedup CCCD phụ thuộc master record ngay từ Stage.
- **Chính sách xóa hồ sơ draft:** Dọn `customers`/`properties` mồ côi kèm kiểm tra tham chiếu.
- **Quy ước thống kê:** Đếm qua `inheritance_cases` / `inheritance_participants`, không đếm `customers` trần.
- **Nguồn:** Owner, 29/09/2026, buổi rà soát dữ liệu MIN-141.

---

## 2026-10-01 — Chuẩn hóa từ điển dữ liệu, quy tắc suy ra & quy ước đặt tên

- **6 trường lưu DB của Người (`customers`):** `ten`, `ngaysinh`, `ngaychet`, `sogiayto`, `ngaycap`, `diachi`.
- **3 nhóm trường suy ra backend (@property):**
  * `loaigiayto`: Người sống dùng mốc 01/10/2024 (Căn cước công dân / Căn cước); Người chết là Trích lục khai tử (Bản sao)...
  * `noicap`: Người sống dùng mốc 01/10/2024 (Cục CSQLHC về TTXH / Bộ Công an); Người chết dùng mốc sáp nhập 01/07/2025 (UBND cấp xã cũ / mới).
  * `loaicutru`: Dùng mốc 01/10/2024 (Thường trú / Cư trú).
  * *Quê quán (`place_of_origin`):* Giữ nguyên nguyên tắc snapshot trong hồ sơ, không tạo cột trong danh bạ master `customers`.
- **Loại bỏ trường lẻ `thoi_han` ở bảng Tài sản (`properties`):** Thông tin thời hạn luôn gắn liền theo cụm 3 trường `(loại đất, diện tích, thời hạn)`, từ 1 đến tối đa 20 cụm (`loaidat1..20`).
- **Quy tắc phân biệt Loại đất thứ mấy trong Tài sản thứ mấy:** Cú pháp `loaidat<LoạiĐất><TàiSản>`, `dientich<LoạiĐất><TàiSản>`, `thoihan<LoạiĐất><TàiSản>`. Ví dụ: `loaidat12` = loại đất 1 của tài sản 2; `loaidat23` = loại đất 2 của tài sản 3.
- **Thêm 3 trường Bảng Hồ sơ (`inheritance_cases`) & Vị trí UI:**
  * `noiniemyet` (suy từ địa chỉ đất + bảng xã sáp nhập).
  * `nguoinhanuyquyen` (danh mục người quen thường UQ / tạo mới).
  * `noidungviec` (cụm nhập tay mô tả công việc).
  * UI: Bố trí thêm 3 dòng dưới các dòng tài sản, giảm 10% chiều cao các ô.
- **Rule chung về đặt tên trường:** Tiếng Việt không dấu, viết thường toàn bộ, **viết liền không dấu, tuyệt đối KHÔNG có dấu gạch dưới `_`** (ví dụ: `ten`, `ngaysinh`, `ngaychet`, `sogiayto`, `ngaycap`, `diachi`, `noicap`, `loaigiayto`, `loaicutru`, `noiniemyet`, `nguoinhanuyquyen`, `noidungviec`, `loaidat12`, `dientich12`, `thoihan12`).
- **Nguồn:** Owner chỉ đạo trực tiếp tại comment issue NAIA-6 ngày 01/10/2026.
- **Nơi lưu lâu dài:** `contracts/entities.md` §8–§9, `docs/spec/notary_v2/README.md`, `docs/spec/notary_v2/stage.md`, `docs/spec/notary_v2/input/property-rules.md`.

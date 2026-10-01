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

---

## 2026-10-0x — Đợt 2: cụm đất thành bản ghi DB

- **Bảng con `property_land_rows`:** `(property_id, vitri, loaidat, dientich,
  thoihan)`, UNIQUE `(property_id, vitri)`. `vitri` là vị trí cụm 1..20 trong
  tài sản và giữ nguyên khe trống; N (vị trí tài sản trong hồ sơ) chỉ tồn tại
  trong placeholder Word/snapshot, không ghi vào master dùng chung.
- **`land_rows_json` hạ vai trò:** từ nguồn lưu chính xuống mirror tương
  thích/đầu vào chuyển đổi. Đọc ưu tiên bảng con; JSON chỉ là fallback cho
  tài sản chưa migrate. Không DROP/không ghi đè bản gốc trong bước này.
- **Hai bộ key song song ở biên:** canonical `loaidat/dientich/thoihan`
  (nghiệp vụ mới + snapshot `case_state_json`) và legacy
  `loai_dat/dien_tich/thoi_han` (UI/wire hiện hành). Cùng trường mà hai key
  mâu thuẫn → `stage_validation_error` code `conflict`, không chọn ngầm.
- **`thoi_han` lẻ mồ côi:** không tự đắp vào cụm khi xuất Word; giữ nguyên
  bản gốc, báo `stage.orphan_thoi_han` để đối chiếu. Chưa xóa cột vật lý.
- **Word đọc snapshot đã commit:** `build_word_context`/`build_template_mapping`
  lấy assets từ `case_state_json` trước — hai hồ sơ dùng chung tài sản không
  cạnh tranh nguồn dữ liệu; master property chỉ là fallback cho hồ sơ cũ chưa
  có snapshot assets.
- **Commit nguyên khối:** master + cụm đất + mirror JSON + snapshot + revision
  trong một transaction; upsert thay bộ cụm bằng clear → flush → insert để
  không đâm UNIQUE khi reuse `(property_id, vitri)`.
- **Migration khởi động song hành:** web `main.py` và sidecar
  `notary_adapter._ensure_db` cùng gọi `migrate_property_land_rows()`; lời
  gọi `migrate_zalo_exchange_schema()` thiếu ở sidecar được bổ sung.
- **Tên placeholder:** giữ dạng đầy đủ `loaidat<M><N>` cho mọi hồ sơ (kể cả
  1 tài sản), không thêm alias rút gọn — `loaidat12` trùng nghĩa
  "cụm 1 tài sản 2" vs "cụm 12 tài sản 1".
- **Nguồn:** review comment của Leader trên NAIA-6, 29/09/2026 (AC đợt 2).

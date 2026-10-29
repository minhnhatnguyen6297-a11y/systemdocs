# Chế độ nhẹ (Bảng nhanh) — spec

**Trạng thái:** spec đề xuất, chưa triển khai, chưa owner duyệt. **Cập nhật:** 29/10/2026.
**Owner module:** bot Soạn thảo & Word. **Phụ thuộc:** bot Sơ đồ thừa kế (`inheritance_engine`).
**Quyết định đang chờ owner:** [#41](https://github.com/minhnhatnguyen6297-a11y/systemdocs/issues/41) điểm vào ·
[#42](https://github.com/minhnhatnguyen6297-a11y/systemdocs/issues/42) chuyển nhẹ↔sơ đồ ·
[#44](https://github.com/minhnhatnguyen6297-a11y/systemdocs/issues/44) không tích Nhận = từ chối? ·
[#45](https://github.com/minhnhatnguyen6297-a11y/systemdocs/issues/45) tích theo tài sản.
(Số GitHub issue, khác dải số backlog `#NN` trong `_bmad-output/backlog/`.)

Quy ước: **[KC]** = đã kiểm chứng tại nguồn trích; **[SUY]** = suy luận/đề xuất, chưa kiểm chứng.

## 1. Mục đích

Hồ sơ thừa kế đơn giản (ước ~70% — **[SUY]**, số liệu từ brief, chưa đo) không cần dựng Sơ đồ.
Chế độ nhẹ là **một view khác của cùng dữ liệu** (D-003, `docs/decisions/decision-80-so-quyet-dinh-nghiep-vu-thua-ke.md:39`):
một bảng phẳng mỗi dòng một Người — Hàng TK, cha nhánh, tích Chủ đất, tích Nhận — rồi
**Xuất Word khung cơ bản** bằng đúng engine Word hiện có. Ca phức tạp chuyển sang Sơ đồ
không nhập lại (#42). Phạm vi: chỉ loại thừa kế (D-049, `decision-80…md:349`).

Ngoài phạm vi: tính suất/phân chia, đoạn Word từ chối (Q3), thế vị/chuyển tiếp nhiều tầng,
nhiều đời vợ/chồng, con riêng — đều là tiêu chí "phức tạp" → Sơ đồ.

## 2. Tham chiếu excelTK

Repo `excelTK` commit `628d070` (2026-09-03 11:19 UTC+7). **[KC]**
- Sheet `NhapLieu`, cột hằng ở `src/vba/modCommon.bas:35-40`: `HangTK` (`COL_LEVEL`),
  `NhanDat` (`COL_RECEIVE`), `ParentNguoiID` (`COL_PARENT`), `LaChuDat` (`COL_OWNER`);
  ngoài ra NguoiID, HoTen, NgaySinh, NgayChet, SoGiayTo, NgayCap, DiaChi, TrangThai, NhomTuChoiID.
- Hàng TK tối đa cấu hình 0–4, mặc định 2 (`modCommon.bas:109-110`, `GetHangTKToiDa`).
- H0 = nhóm chủ đất (2 vị trí cố định, một gốc chung); H1 = nhánh trực tiếp của nhóm chủ đất,
  `ParentNguoiID` rỗng ở H0–H1; từ H2 cha nhánh là người ở dòng hàng trên
  (`docs/specs/inheritance-branch-architecture.md`, mã `PARENT_NOT_EMPTY/PARENT_MISSING/PARENT_LEVEL/PARENT_CYCLE`).
- Nhóm xuất (`src/vba/modExportData.bas:145-165`): ChuDat = LaChuDat; NguoiDaChet = có ngày chết;
  NguoiNhanDat = còn sống ∧ NhanDat; CacNhomTuChoi = còn sống ∧ ¬NhanDat
  (spec excelTK `inheritance-branch-architecture.md:349`, tự tính, không nhập tay — dòng 229).
- Người đã chết không nhận đất (`modNguoi.bas:241`, `ResolveDeathReceiveConflict`).
- Spec excelTK nói chẩn đoán không chặn (§12), nhưng code v0.2.x chặn xuất
  (`modWordExport.bas:22-23` "Dữ liệu còn lỗi chặn xuất."). systemdocs theo **không chặn** (R-28).

## 3. Contract dữ liệu chung với Sơ đồ

Nguyên tắc **[SUY, đề xuất]**: Bảng nhanh **không có storage riêng**. Người/Tài sản ở Stage
(`stage.people` / `stage.assets`, khóa `PERSON_CONTRACT_KEYS`, `ASSET_CONTRACT_KEYS` —
`notary_v2/services/case_rows.py:30`); quan hệ ghi vào `diagram.state` v3
(`DIAGRAM_STATE_VERSION = 3`, `notary_v2/services/case_workspace.py:57`; node fields
`inheritance_workspace.py:53-56`, persisted `:332-363`). Lưu qua điểm ghi duy nhất "Lưu hồ sơ".

| excelTK | systemdocs (đích) | Ghi chú |
|---|---|---|
| NguoiID | `stage.people[].row_id` = `node.personId` | [KC] ID ổn định, không mã 1.x.x (R-29) |
| HoTen, NgaySinh, SoGiayTo, NgayCap, DiaChi | `ho_ten, ngay_sinh, so_giay_to, ngay_cap, dia_chi` | [KC] cùng tên trong `PERSON_CONTRACT_KEYS` |
| NgayChet | `ngay_chet` | [KC] engine đọc `ngay_chet/death_date/deathDate/death` (`inheritance_engine.py:241-243`); `yyyy` → 01/01 chỉ để tính (R-08) |
| LaChuDat | `node.ownPositions` | [KC] mảng vị trí TS 1..5; bảng 1 ô → ghi mọi vị trí (#45) |
| NhanDat | `node.receivePositions` | như trên (#45) |
| ParentNguoiID (1 cha nhánh) | `node.parentSlotIds` (≤ 1 cha + 1 mẹ, R-10) | **GAP-1** xem dưới |
| HangTK | — (không lưu) | **GAP-2** suy từ cấu trúc |
| H0 hai chủ đất | 2 node chủ đất + `spouseSlotIds` giữa họ | **GAP-3** |
| TrangThai, NhomTuChoiID | — | **GAP-4** không mang sang (D-046, #44) |
| (không có) | `gioi_tinh, noi_cap, place_of_origin, loai_giay_to, loai_dia_chi` | dùng nguyên cột Stage |

Gap (chưa kiểm chứng engine chấp nhận — câu hỏi §10):
- **GAP-1 cha nhánh vs ô cha/mẹ.** excelTK có một `ParentNguoiID`; systemdocs có ô cha và ô mẹ do engine sinh
  (`diagram-rules.md` §9.6, user không tạo ô). Đề xuất: Bảng nhanh chỉ ghi "cha nhánh" = person; engine reconcile
  đặt vào ô cha/mẹ phù hợp; H1 tự gắn cả hai chủ đất H0 làm cha/mẹ (excelTK coi H1 là con của **nhóm** chủ đất).
- **GAP-2 Hàng TK.** Không có trường; hiển thị suy từ độ sâu cây. Không thêm trường mới (AGENTS.md).
- **GAP-3 vợ/chồng.** excelTK không có cột vợ/chồng ngoài cặp H0; vợ/chồng của người chết ở H1+ (chuyển tiếp)
  không biểu diễn được → tiêu chí "phức tạp".
- **GAP-4 "chết trước, không rõ ngày"** (D-032, R-07) chưa có trong code; Bảng nhanh không thêm.
- **GAP-5 engine v2/v3.** Engine tính trên node v2 (`isLandOwner/willReceive`, `inheritance_engine.py:96-140`)
  chuyển từ v3 (`_v3_to_v2_nodes`); Bảng nhanh chỉ ghi v3.

## 4. Placeholder Word điền được

Engine Word không đổi. [KC] `_apply_diagram_nodes` (`word_engine.py:563-611`) đọc node theo `entity_id/row_id`,
lấy `receivePositions`/`ownPositions`, `hidden/deleted`. Không có Diagram → người `owner_row_id` là Chủ đất
(`word_engine.py:712-718`). Nhóm (`word_engine.py:1544-1556`):

| Nhóm / dòng | Điền từ Bảng nhanh | Ghi chú |
|---|---|---|
| `[Người N - Trường]` | ✅ thứ tự Stage | |
| `[Chủ đất sống N - …]`, `[Chủ đất chết N - …]` | ✅ LaChuDat + ngày chết | D-050 người sống được làm Chủ đất |
| `[Người nhận N - …]` | ✅ NhanDat ∧ còn sống | |
| `[Dòng người không nhận N]` | ✅ trạng thái "Người không nhận" (`_status_for_person`, `:967-977`) | thay cho `CacNhomTuChoi` excelTK (#44) |
| `[Dòng khai tử chủ đất chết N]`, `[Dòng chủ đất sống tặng cho N]` | ✅ | |
| `[Dòng hàng thừa kế N]`, `[Hàng thừa kế N - …]` | ✅ người không phải chủ đất | |
| `[Dòng tài sản N]`, `[Tài sản N - …]` | ✅ Stage assets | |
| `[Người từ chối N - …]`, `[Dòng người từ chối N]` | ❌ rỗng | `legal_refusal_people=[]` (`:843`, `:867`), Q3 |
| Suất/phần chia, nhãn quan hệ chi tiết | ❌ / "chưa kiểm chứng" | cần engine result đầy đủ → Sơ đồ |

Placeholder thiếu dữ liệu vẫn xuất (`word-templates.md` §1 "có gì xuất đó"; `missing: []`).

## 5. Luật tối thiểu

1. **Chỉ thừa kế.** Bảng nhanh chỉ cho loại thừa kế — D-049 (`decision-80…md:349`).
2. **Một nguồn sự thật.** Bảng là view; không lưu song song — D-003 (`decision-80…md:39`).
3. **Tối đa 5 tài sản**, một thửa = một tài sản — R-06, D-036 (`business-rules.md:49`; `case_workspace.py:67`).
4. **Ngày chết trống = còn sống**; ngày thiếu giữ nguyên khi hiển thị, quy đổi chỉ để tính — R-07/R-08 (`business-rules.md:58-59`).
5. **Người đã chết không tích Nhận được** — excelTK `modNguoi.bas:241`; systemdocs: [SUY] tương đương engine, cần bot Sơ đồ xác nhận.
6. **Không tích Nhận ở người còn sống = nhắc, không phải từ chối** — D-046 (`decision-80…md:331`), R-19 (`business-rules.md:75`). Xung đột excelTK → #44.
7. **Người sống được làm Chủ đất** — D-050 (`decision-80…md:354`). Thiếu Chủ đất vẫn Lưu, có cảnh báo — D-051 (`decision-80…md:360`).
8. **Không chặn Lưu/Xuất vì dữ liệu nghiệp vụ**; chỉ chặn kỹ thuật (thiếu mẫu, quá giới hạn) — R-28 (`business-rules.md:92`), D-002; ngoại lệ D-048: trống số thửa/tờ chặn Lưu.
9. **Con tối đa 1 cha + 1 mẹ, chỉ thừa kế từ cha/mẹ đã gắn** — R-10 (`business-rules.md:61`). Cha nhánh ở Bảng nhanh phải là người hàng trên.
10. **Hàng TK 0..4, mặc định tối đa 2** — excelTK `modCommon.bas:109-110`. [SUY] áp nguyên cho Bảng nhanh; vượt → gợi ý Sơ đồ.

Chẩn đoán cấu trúc (mã excelTK `PARENT_*`) hiện cảnh báo tại dòng, không chặn (luật 8). [SUY]

## 6. Tiêu chí MVP (kiểm thử được)

1. Hồ sơ thừa kế 1 chủ đất chết + 3 con sống (dữ liệu giả lập) nhập xong chỉ trong Bảng nhanh, không mở Sơ đồ.
2. "Lưu hồ sơ" ghi `stage.people` và `diagram.state` v3 hợp lệ schema `contracts/notary-case-drafting/diagram.schema.json`.
3. Xuất Word: `[Chủ đất chết 1 - Họ tên]`, `[Người nhận 1..3 - Họ tên]`, `[Dòng tài sản 1]` điền đúng; `[Người từ chối …]` rỗng.
4. Người sống bỏ tích Nhận → hiện nhắc, xuất vẫn chạy, người đó vào `[Dòng người không nhận 1]`.
5. Tích Nhận cho người có ngày chết → không nhận / cảnh báo; không chặn Lưu.
6. Mở cùng hồ sơ bằng Sơ đồ (#42 phương án A) → không mất Người, không cần nhập lại; khác biệt vào Pool kèm cảnh báo.
7. Dữ liệu thiếu (vd. thiếu ngày cấp) → vẫn xuất, `missing` liệt kê trường.
8. Không thêm khóa nào ngoài `PERSON_CONTRACT_KEYS`/`ASSET_CONTRACT_KEYS`/node v3 (kiểm bằng schema test).

## 7. Câu hỏi mở

- #41 điểm vào (khuyến nghị: công tắc ở header vùng Sơ đồ).
- #42 chuyển nhẹ→sơ đồ (khuyến nghị: một chiều một bấm) và ngược lại (có điều kiện).
- #44 không tích Nhận: nhắc (D-046) hay từ chối (excelTK) — khuyến nghị giữ D-046.
- #45 tích theo tài sản hay một ô — khuyến nghị một ô cho MVP.
- Ước lượng "~70% ca đơn giản" chưa có số đo.

## 8. Câu hỏi contract cho bot Sơ đồ thừa kế

1. Engine reconcile có nhận node v3 chỉ có `personId` + `parentSlotIds` trỏ tới **node người** (không phải ô do engine sinh) không? Nếu không, Bảng nhanh phải gọi API nào để sinh ô (UUIDv5 theo §9.6)?
2. H1 là con của **cả hai** chủ đất H0: ghi hai `parentSlotIds` hay một và để engine suy?
3. Cặp chủ đất H0: dùng `spouseSlotIds` một chiều (D-041) — chiều nào?
4. Có chấp nhận không lưu Hàng TK (suy từ cây) không?
5. Kiểm tra "người chết không nhận" nằm ở engine hay UI?
6. Lộ trình bỏ engine v2 (`_v3_to_v2_nodes`) có đổi gì với node do Bảng nhanh ghi?
7. Trạng thái "chết trước, không rõ ngày" (D-032) có trường dự kiến chưa?

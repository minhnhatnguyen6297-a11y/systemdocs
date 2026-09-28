# Kế hoạch triển khai — MIN-133

Ngày: 2026-09-28. Nhánh: `consolidate/monorepo` tại `D:\systemdocs`, commit trực tiếp theo chỉ đạo owner.
Chuẩn thị giác: `mockup/mockup-1440x775.png`, owner duyệt tỷ lệ ngày 28/09/2026. Hai ảnh 1920×1080 và 1366×768 dùng để kiểm bố cục co giãn.
Yêu cầu gốc nằm ở Linear MIN-133. File này chỉ ghi ai sửa file nào, theo thứ tự nào, và bằng chứng cần có.

## 1. Quyết định

Owner chốt ngày 28/09/2026: duyệt tỷ lệ mockup; D1 bỏ cả hai ô; D2 dùng mặc định, chỗ nhập để task Word; D8 cuộn cả trang. Các điểm còn lại theo đề xuất trong mockup.

| # | Điểm | Đề xuất (mặc định nếu owner không đổi) | Ảnh hưởng backend |
|---|---|---|---|
| D1 | Trường Người | Stage hiện 7 cột theo đúng DB `Customer`. Bỏ ô `Nơi cấp` (backend tự suy từ ngày cấp, `models.py:47-49`) và ô `Nguyên quán` | Không đổi wire/contract. `noi_cap` và `place_of_origin` vẫn được giữ và truyền nguyên vẹn nếu đã có, để không mất dữ liệu cũ |
| D2 | Card Thông tin hồ sơ | Bỏ khỏi UI. `document_type` lấy mặc định của model theo loại sơ đồ (`model.js:396`). `ngay_lap_ho_so` để backend tự điền ngày hiện tại (`case_workspace.py:1190`). `noi_niem_yet` để trống thì Word dùng địa chỉ tài sản (`word_engine.py:1083`). `ghi_chu` để trống | Backend giữ nguyên vì Word đọc 4 trường này (`word_engine.py:1098-1107`). Cách nhập lại sẽ quyết trong task Word |
| D3 | Thanh trạng thái engine | Bỏ `#statusbar`. Thông tin engine vẫn có ở module Trạng thái (`renderer.js:656+`), thêm tooltip trên logo G1 | Chỉ ở client. Vẫn giữ polling `sidecarStatus` |
| D4 | Nút ‹, tiêu đề, pill Nháp, text trạng thái lưu | Bỏ hết. Chỉ còn chấm dirty trên nút Lưu | Chỉ ở client |
| D5 | Thanh trên cùng | Gộp tab (Tổng quan / Soạn / Word) với action bar thành một thanh cao khoảng 42px | — |
| D6 | Nút Lưu sơ đồ / Xuất Word | Chuyển lên header vùng sơ đồ, bỏ footer | — |
| D7 | Kích thước node | Node đã thả rộng 144px (vừa tên 3 chữ ở cỡ 14px). Node trống 88×24px viền đứt, không nhãn, không chip. Chip ghi "Chủ" / "Nhận" | — |
| D8 | Nhiều người hơn chiều cao màn | Bảng Người dài theo số dòng, không có thanh cuộn riêng. Vượt khoảng 12 dòng ở 1440×775 (ví dụ Hai bên 30 người) thì **cuộn cả trang**, sơ đồ bị đẩy xuống dưới và vẫn giữ chiều cao tối thiểu đọc được. Không co chữ | — |
| D9 | Cây sơ đồ sâu hơn 3 thế hệ | Canvas giữ pan/zoom và nút Mở rộng. Không tự thu nhỏ đến mức không đọc được | — |

## 2. Giá trị thiết kế (lấy theo mockup)

Worker W1 sửa `tokens.json` trước, sau đó mới áp vào CSS.
- Màu nền app `#e9edf2`. Card nền `#fff`, viền 1px `#dde3ea`, giữ shadow cũ, bo góc 10px. Canvas `#f5f7fa` với lưới chấm.
- Khoảng cách giữa vùng 8px, padding `#view` 8px. Card head cao 34px, padding 0 10px. Card body padding 0 10px 8px.
- Hàng bảng Stage cao 25px; ô nhập nằm ngay trong ô bảng, chỉ hiện viền khi hover hoặc focus. Nút trên thanh cao 32px, nút `sm` cao 28px.
- Cỡ chữ: dữ liệu 14px; nhãn và header 13px; chip 12px.
- Tỷ lệ Tài sản : Người là 35 : 65 (38 : 62 ở màn ≥1920). Bảng dùng `table-layout: fixed` với `colgroup`; chuỗi dài cắt "…" kèm tooltip.
- Pool rộng 176px. Khoảng cách trong sơ đồ: lề 6px, giữa thế hệ 12–16px, giữa node 14px, giữa cặp vợ chồng 28px.

## 3. Chia worker và phạm vi file

| Đợt | Worker | Sở hữu | Việc |
|---|---|---|---|
| 1 | **W1 — nền chung** | `docs/product/ui/tokens.json`, `DESIGN.md`, `references/` (thêm mockup đã duyệt), `shell/src/renderer/styles.css`, `index.html`, phần shell trong `renderer.js` | Token mới (§2). Sửa `#view section{max-width:860px}` ở `styles.css:158` thành chỉ áp cho section con trực tiếp, để nội dung giãn hết màn. Thêm viền card, giảm khoảng cách, chiều cao hàng `grid` và nút. Bỏ `#statusbar` nhưng giữ `setStatus` an toàn khi element không còn; thêm tooltip engine trên logo. Kiểm Upload Lab không vỡ vì dùng chung `styles.css` |
| 1 (song song) | **W2 — Stage + thanh trên** | `case-drafting-view.js` (phần actionbar, localnav, workspace, stage), phần Stage/actionbar trong `case-drafting.css` | D1, D2, D4, D5. Select loại sơ đồ rộng ≥128px. `PERSON_COLS` còn 7 cột. `colgroup` cố định cột. Bỏ `max-height`/`overflow` của `.cd-stage-body`, bỏ cuộn của `.cd-table-wrap` và các min-width. Theo D8, bảng Người không có thanh cuộn riêng. Layout flex dọc để vùng sơ đồ lấp phần chiều cao còn lại, có `min-height`; khi Stage cao hơn màn hình thì cả trang cuộn |
| 2 | **W3 — sơ đồ** | `relationship-diagram.js`, phần diagram/Pool trong `case-drafting.css` | D6, D7, D9. Sửa hằng `NODE_W`/`NODE_H`/`GAP_X`/`ROW_H`/`PAD` (dòng 43). Node trống không có role, hint hay chip (dòng 635, 670-675). Đổi nhãn chip (682). Đưa nút lên head (1293-1309). Canvas co giãn theo chiều cao còn lại, bỏ `height:min(52vh,620px)`. Giữ nguyên drag payload P6 |
| 3 | **W4 — kiểm chứng** | chỉ `.agent/tasks/MIN-133/` | Chạy toàn bộ test; mở Electron thật, chụp 3 kích thước và so với mockup; đi luồng hồ sơ mới/cũ, 30 người Hai bên, hơn 30 người thừa kế; kiểm Upload hai tab. Chỉ sửa lỗi nhỏ khi điều phối cho phép |

W1 và W2 sửa các file khác nhau nên chạy song song được. W3 phải chờ W2 xong vì hai worker cùng sửa `case-drafting.css`.
Kỷ luật git giống đợt trước: commit bằng `git commit --only -- <paths>`, không `-A`, không amend hay rebase commit người khác.

## 4. Điểm dừng

- Không sửa model, contract, backend hay Word. Nếu cần sửa ngoài vùng sở hữu, ghi rõ vào handoff và báo điều phối.
- Test cũ gắn với kích thước cũ (ví dụ control 44px, cap 860px) phải đối chiếu mục đích trước khi sửa. Không xóa test chỉ để có kết quả xanh.
- D1 không đụng tới fixture/test adapter có `noi_cap`/`place_of_origin` (`test_notary_adapter_contract.py:99-100`, `test_notary_mock_adapter.py:381-382`), vì wire vẫn giữ các trường này.

## 5. Bằng chứng

| Kiểm tra | Nơi chạy |
|---|---|
| `node --test test/*.test.mjs` (trước đợt này: 254 đạt) | shell |
| pytest cho adapter notary và upload | shell |
| `validate_examples.py` (68 file) | root |
| Ảnh Electron thật ở 1440×775, 1366×768, 1920×1080, đặt cạnh mockup | W4 |
| Đo độ tràn bằng JS: Stage = 0 ở mọi trường hợp; trang = 0 khi dữ liệu ≤ mockup (3 tài sản, 7 người); với 30 người thì cả trang cuộn, không có thanh cuộn lồng trong Stage (D8) | W4 |
| Upload Audit và Quét-upload vẫn đúng sau khi đổi token chung | W4 |

# Regex thừa kế v1 — phân chia / từ chối / khai nhận di sản

**Trạng thái:** Active · **Phiên bản:** v1.2 (07/10/2026) ·
**Engine:** `ENGINE_VERSION 2026-10-07-thuake6` ·
**Độ phủ:** 50 văn bản phân chia đầu tiên ở `D` (31 sạch, 11 loại
đúng vì không phải văn bản, 8 gắn cờ người kiểm) + file owner gửi
(`comment/Văn bản phân chia 1.doc`)

File này là SOT chi tiết loại thừa kế. Catalog tổng ở
[`regex-rules.md`](./regex-rules.md) §2.5–§2.9 chỉ tra nhanh;
khi lệch nhau thì file này đúng.

## 1. Ba loại con

| Loại | Dấu hiệu tiêu đề | Mở đầu đương sự | Nhãn hiển thị |
|---|---|---|---|
| Phân chia (`inheritance_partition`) | `phân chia di sản`, `thỏa thuận phân chia di sản` | `Chúng tôi/Tôi là [những người] được hưởng di sản...`, `Người được hưởng di sản theo pháp luật/thừa kế của...`, `Tôi/Chúng tôi là người được hưởng di sản...`, `Hàng thừa kế... gồm những người có tên sau đây`, `Tôi tên là:` | NHỮNG NGƯỜI HƯỞNG DI SẢN |
| Từ chối (`inheritance_refusal`) | `từ chối nhận di sản` | `Tôi là:` / `Chúng tôi là:` (kể cả hưởng thế vị Anh/Chị) | NGƯỜI TỪ CHỐI NHẬN DI SẢN |
| Khai nhận (`inheritance_declaration`) | `khai nhận di sản` | dùng chung luật mở đầu với phân chia | NGƯỜI KHAI NHẬN DI SẢN |

Kết khối đương sự trước: `tự nguyện lập Văn bản này`, `Người để
lại di sản:`, `Di sản:`, `Khi còn sống`, `Trước khi chết`,
`Bố/mẹ đẻ`, `Chúng tôi là những người thừa kế`, `LỜI CHỨNG`.

## 2. Người sống (mỗi người 1 bản ghi)

| Trường | Cách nhận |
|---|---|
| `gioi_tinh` | `Ông`/`Anh`/`Ngài` → Ông; `Bà`/`Chị`/`Bà mụ` → Bà; `Ông/bà:` hoặc mơ hồ → **để trống** + cờ R13 (không suy qua `Thị`, decision-46) |
| `ho_ten` | Sau danh xưng, cắt trước `\|`, nhãn ngày sinh (bắt buộc kèm giá trị vì `Năm` là âm tiết tên), `có vợ/chồng là`, ngoặc ngày sinh người khác; **vai trò không vào tên** — cắt cả đuôi ` - Con đẻ ông X` lẫn dòng riêng `Là vợ/con của...` (Owner 07/10/2026: `ho_ten` chỉ giữ họ tên) |
| `ngay_sinh` | `Sinh ngày[:/-] DD/MM/YYYY`, hoặc `Sinh năm[:/-] YYYY` → giữ đúng `YYYY` + cờ `chi_co_nam_sinh`; văn bản viết nhầm nhãn `Sinh năm: DD/MM/YYYY` (ngày đủ) vẫn lấy ngày đủ, không nuốt `Sinh` vào tên (10/10/2026) |
| `cccd` | Sau `Căn cước (công dân) số` / `CCCD số` / `CMND` (`số:` dính hai chấm cũng nhận) |
| `noi_cap` | Giữa `do` và `cấp/ký ngày`; thiếu `do` thì lấy cụm sau số giấy tờ |
| `ngay_cap_cccd` | Sau `cấp/ký ngày`; số Excel 5 chữ số (`cấp ngày 44546`) đổi ra ngày thật |
| `dia_chi` | `Thường trú/Cư trú tại:`, `Nơi thường trú[:]`, `Nơi cư trú:`, `Hộ khẩu (thường trú):`, `Địa chỉ...` — kể cả chung dòng tên; giá trị cắt trước `Là vợ/con của...`, `1.`/`2.`..., `Ông:`/`Bà:` đầu người kế (IFilter gộp dòng); trừ `Nơi thường trú cuối cùng...` của người chết |

Bỏ cả dòng phả hệ (`Ông X có vợ là bà Y (Sinh ngày...)`) và khối
dừng trước dòng `chết ngày`.

## 3. Người chết (`raw.nguoi_chet`, bắt buộc có `chết/đã chết ngày DD/MM/YYYY`)

| Trường | Cách nhận |
|---|---|
| `ho_ten`, `ten_goi_khac` | `Ông/Bà ... [(tên gọi khác là ...)]`; tên tối đa 6 từ, mọi từ phải viết hoa chữ cái đầu — câu kể phả hệ (`Ông Đức và bà Khuâng là vợ chồng...`) bị loại, không sinh bản ghi rác |
| `ngay_sinh` | `Sinh năm[:] YYYY` (giữ `YYYY` + cờ) hoặc đủ ngày |
| `ngay_chet` | Sau `chết/đã chết ngày[:/-]` |
| `so_giay_to`, `loai_giay_to`, `ngay_cap`, `noi_cap` | Trích lục khai tử là giấy tờ của người chết: sau `Trích lục khai tử... số`, `do... ký/cấp ngày` (decision-46) |
| `dia_chi` | Sau `Nơi thường trú cuối cùng trước khi chết:` |

## 4. Tài sản đất (mỗi thửa 1 dòng `danh_sach_thua_dat` + `land_rows` shape DB)

Khối đất mở bằng: `quyền sử dụng đất ... có/tại địa chỉ:`, `Phần
quyền sử dụng đất ... trong khối tài sản chung...`, `... theo
Giấy chứng nhận`, hoặc `thửa đất số ... (có địa chỉ tại/theo
GCN/theo bản đồ)`. Dừng trước: `Người/Những người thừa kế/nhận
thừa kế` (kể cả `III.`, `III. |`), `Nội dung/Thống nhất phân chia`,
`Bằng Văn bản này`, `Lời chứng`.

| Trường thửa | Cách nhận |
|---|---|
| `so_thua_dat`, `so_to_ban_do` | Nhãn `Thửa đất số`/`Số thửa`, `Tờ bản đồ số`/`Số tờ` (kể cả ngược thứ tự, chung dòng, cắt nhau bằng `;`, kể cả lỗi chính tả `Tờ bản đổ số` 10/10/2026); `so_to_ban_do` chỉ giữ số/ký hiệu — cắt đuôi mô tả `Bản đồ địa chính năm 1991` (Owner 07/10/2026) |
| `dien_tich` | Giữ chữ gốc (`285.0 m2`), bỏ `(bằng chữ:...)`, cắt phần thừa sau `,`/`;`/`trong`/`theo`; giá trị không chứa chữ số (`diện tích thửa đất nêu trên`) bị loại + R13 |
| `muc_dich_su_dung`, `thoi_han_su_dung`, `phan_ghi_them` | Ô bảng / nhãn dòng; `Trong đó` gộp vào thửa đang mở, không ghi đè; chi tiết viết liền `Trong đó: ONT: 190,0 m2; NTS: 75,0 m2` tách vào `chi_tiet_dien_tich`; dòng `Hiện nay là thửa đất số X; Tờ Y` là đánh số lại của **cùng thửa** → ghi vào `phan_ghi_them`, không mở thửa mới; thửa `(so_thua_dat, so_to_ban_do)` lặp lại trong văn bản chỉ giữ bản ghi đầu |
| `nguon_goc` | Nhãn `Nguồn gốc (sử dụng đất)` — có trường sẵn, trống khi văn bản không ghi |
| `dia_chi`, `loai_gcn`, `so_gcn`, `so_vao_so`, `ngay_cap_gcn`, `co_quan_cap` | Từ câu GCN chung, copy vào từng thửa; serial nhận cả `Đ` (`Đ 364866`); số vào sổ cắt từ thừa |
| `land_rows[]` | Đổi từng chi tiết sang `{loai_dat (giữ chữ gốc: ONT/CLN hay Đất ở), dien_tich (số), thoi_han}` đúng shape DB `asset_row.land_rows` |

Hai luật chống nhiễu (10/10/2026): **bảng liệt kê người** (ô chứa
`Sinh ngày/năm`, `CCCD`, `Hộ khẩu`, hoặc ô đầu dạng `1. Ông/Bà ...`)
không được nhập vào `chi_tiet_dien_tich`; **thửa chỉ có GCN** — văn bản
mô tả đất bằng `theo Giấy chứng nhận ... Số X do ... cấp ngày` nhưng
không có số thửa/tờ — vẫn tạo 1 bản ghi giữ `so_gcn`/`dia_chi`/
`co_quan_cap`/`ngay_cap_gcn` thay vì trả về rỗng (R09 hết báo sai).

Bảng `.doc` (IFilter giữ ô bằng TAB → code đổi thành `|`,
cắt `|` thừa đầu/cuối, tên cắt trước `|`): bảng dồn 1 dòng thì tách
theo dòng ô (ô `Số thửa` làm neo); tiêu đề tách 2 dòng thì nối lại;
dòng văn xuôi >100 ký tự trong vùng bảng thì bỏ; `Trong đó: | ...`
thì cắt mốc giữ ô.

## 5. Tài sản sổ tiết kiệm / tài khoản — TẠM DỪNG (decision-46)

Không bóc dòng. Khi văn bản có khối `sổ tiết kiệm` / `số dư tài khoản`,
engine chỉ ghi `"so_tiet_kiem"` vào `raw.tai_san_chua_ho_tro` và R12
cảnh báo để nhân viên biết file có phần này.

## 6. Quyền lợi bảo hiểm — TẠM DỪNG (decision-46)

Tương tự §5: nhận diện khối `quyền lợi bảo hiểm` → `"bao_hiem"` trong
`raw.tai_san_chua_ho_tro` + R12. Không trích `so_hop_dong`, `ben_bao_hiem`...

## 7. Lời chứng — KHÔNG TRÍCH (decision-46)

Không đối chiếu với người đầu văn bản nên không bóc người trong Lời chứng;
không còn `raw.loi_chung_nguoi` và luật R11.

## 8. Lịch sử phiên bản

| Bản | Ngày | Nội dung | Engine |
|---|---|---|---|
| v1.0 | 06/10/2026 | Vòng 1–5: mở đầu/kết 12+ biến thể, tên trần + vai trò, `Ông/bà`, Anh/Chị, `Tôi tên là:`, năm sinh + cờ, ngày Excel, người chết + trích lục, tách thửa + `land_rows`, sổ TK/tài khoản/thẻ, bảo hiểm, bảng `.doc`, luật R00–R11 | thuake5 |
| v1.1 | 06/10/2026 | decision-46: bỏ lời chứng + R11; người chết dùng trường Người (`so_giay_to`/`ngay_cap`/`noi_cap`/`dia_chi`); sổ TK/bảo hiểm chỉ gắn cờ `tai_san_chua_ho_tro` + R12; không suy giới tính từ `Thị`, giới tính trống → R13; diện tích mơ hồ (`1.234`) → R13 | thuake5 |
| v1.2 | 07/10/2026 | Mẫu thật ông Thưởng: `ho_ten` chỉ giữ họ tên (bỏ đuôi vai trò ` - Con đẻ...`, `Là vợ của...`); `dia_chi` nhận `Hộ khẩu thường trú` + cắt đuôi người kế trên dòng gộp; lọc tên người chết dạng câu; `so_to_ban_do` chỉ giữ ký hiệu; `dien_tich` phải có chữ số, cắt `; Trong đó`, tách ONT/NTS viết liền; `Hiện nay là thửa...` → `phan_ghi_them` không mở thửa; khử trùng thửa `(thửa,tờ)`; thêm trường `nguon_goc`; tool hiển thị `Nguồn gốc`/`Cơ quan cấp`, bỏ chú thích "(chỉ có năm)"; R13 cờ cả diện tích không parse được; R04 cờ tên người chết dạng câu | thuake6 |

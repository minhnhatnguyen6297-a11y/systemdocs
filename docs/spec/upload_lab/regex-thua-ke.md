# Regex thừa kế v1 — phân chia / từ chối / khai nhận di sản

**Trạng thái:** Active · **Phiên bản:** v1.0 (06/10/2026) ·
**Engine:** `ENGINE_VERSION 2026-10-06-thuake5` ·
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
| `gioi_tinh` | `Ông`/`Anh` → Ông; `Bà`/`Chị` → Bà; `Ông/bà:` suy qua `Thị` trong tên |
| `ho_ten` | Sau danh xưng, cắt trước `\|`, nhãn ngày sinh (bắt buộc kèm giá trị vì `Năm` là âm tiết tên), `có vợ/chồng là`, ngoặc ngày sinh người khác; vai trò dòng riêng (`Là con đẻ...`) giữ vào tên |
| `ngay_sinh` | `Sinh ngày[:/-] DD/MM/YYYY`, hoặc `Sinh năm[:/-] YYYY` → giữ đúng `YYYY` + cờ `chi_co_nam_sinh` |
| `cccd` | Sau `Căn cước (công dân) số` / `CCCD số` / `CMND` (`số:` dính hai chấm cũng nhận) |
| `noi_cap` | Giữa `do` và `cấp/ký ngày`; thiếu `do` thì lấy cụm sau số giấy tờ |
| `ngay_cap_cccd` | Sau `cấp/ký ngày`; số Excel 5 chữ số (`cấp ngày 44546`) đổi ra ngày thật |
| `dia_chi` | `Thường trú/Cư trú tại:`, `Nơi thường trú[:]`, `Nơi cư trú:`, `Địa chỉ...` — kể cả chung dòng tên; trừ `Nơi thường trú cuối cùng...` của người chết |

Bỏ cả dòng phả hệ (`Ông X có vợ là bà Y (Sinh ngày...)`) và khối
dừng trước dòng `chết ngày`.

## 3. Người chết (`raw.nguoi_chet`, bắt buộc có `chết/đã chết ngày DD/MM/YYYY`)

| Trường | Cách nhận |
|---|---|
| `ho_ten`, `ten_goi_khac` | `Ông/Bà ... [(tên gọi khác là ...)]` |
| `ngay_sinh` | `Sinh năm[:] YYYY` (giữ `YYYY` + cờ) hoặc đủ ngày |
| `ngay_chet` | Sau `chết/đã chết ngày[:/-]` |
| `so_trich_luc`, `co_quan_trich_luc`, `ngay_trich_luc` | Sau `Trích lục khai tử... số`, `do... ký/cấp ngày` |
| `dia_chi_cuoi` | Sau `Nơi thường trú cuối cùng trước khi chết:` |

## 4. Tài sản đất (mỗi thửa 1 dòng `danh_sach_thua_dat` + `land_rows` shape DB)

Khối đất mở bằng: `quyền sử dụng đất ... có/tại địa chỉ:`, `Phần
quyền sử dụng đất ... trong khối tài sản chung...`, `... theo
Giấy chứng nhận`, hoặc `thửa đất số ... (có địa chỉ tại/theo
GCN/theo bản đồ)`. Dừng trước: `Người/Những người thừa kế/nhận
thừa kế` (kể cả `III.`, `III. |`), `Nội dung/Thống nhất phân chia`,
`Bằng Văn bản này`, `Lời chứng`.

| Trường thửa | Cách nhận |
|---|---|
| `so_thua_dat`, `so_to_ban_do` | Nhãn `Thửa đất số`/`Số thửa`, `Tờ bản đồ số`/`Số tờ` (kể cả ngược thứ tự, chung dòng, cắt nhau bằng `;`) |
| `dien_tich` | Giữ chữ gốc (`285.0 m2`), bỏ `(bằng chữ:...)`, cắt phần thừa sau `,`/`trong`/`theo` |
| `muc_dich_su_dung`, `thoi_han_su_dung`, `phan_ghi_them` | Ô bảng / nhãn dòng; `Trong đó` gộp vào thửa đang mở, không ghi đè |
| `dia_chi`, `loai_gcn`, `so_gcn`, `so_vao_so`, `ngay_cap_gcn`, `co_quan_cap` | Từ câu GCN chung, copy vào từng thửa; serial nhận cả `Đ` (`Đ 364866`); số vào sổ cắt từ thừa |
| `land_rows[]` | Đổi từng chi tiết sang `{loai_dat (giữ chữ gốc: ONT/CLN hay Đất ở), dien_tich (số), thoi_han}` đúng shape DB `asset_row.land_rows` |

Bảng `.doc` (IFilter giữ ô bằng TAB → code đổi thành `|`,
cắt `|` thừa đầu/cuối, tên cắt trước `|`): bảng dồn 1 dòng thì tách
theo dòng ô (ô `Số thửa` làm neo); tiêu đề tách 2 dòng thì nối lại;
dòng văn xuôi >100 ký tự trong vùng bảng thì bỏ; `Trong đó: | ...`
thì cắt mốc giữ ô.

## 5. Tài sản sổ tiết kiệm / tài khoản (`danh_sach_so_tiet_kiem`)

Khối mở bằng `sổ tiết kiệm`, `số dư tài khoản`, `số tiền gốc và lãi`.
Mỗi sổ/tài khoản 1 dòng: `loai_so` (`có kỳ hạn`, `tài khoản`),
`so_hieu` (`AC 00033961022`, `IE4025426`, `STK: 3214...`;
`Thẻ tiết kiệm` tính như sổ), `ngan_hang` (sau `do`/`của Ngân
hàng..., cắt hậu tố), `chi_nhanh`, `ngay_phat_hanh` (+`Ngày mở tài
khoản`), `chu_so` (sau `cho/mang tên/chủ tài khoản:`).
`loai_tai_san` của văn bản: `Sổ tiết kiệm`.

## 6. Quyền lợi bảo hiểm (`danh_sach_bao_hiem`)

Khối mở bằng `quyền lợi bảo hiểm`. Mỗi quyền lợi 1 dòng:
`so_hop_dong` (sau `số`, mở đầu bằng chữ số), `ben_bao_hiem`
(sau `ký giữa`, cắt hậu tố bên mua), `ben_mua`, `doi_tuong`,
`ngay_ky`. Dòng không số thì gộp vào dòng đang mở.
`loai_tai_san`: `Tài sản khác` ([CONFIRM] portal chưa có enum).

## 7. Lời chứng (`raw.loi_chung_nguoi`)

Mọi khối CCCD trong Lời chứng đều xuất, không đối chiếu với đầu
văn bản (cờ R11 khi lệch số lượng).

## 8. Lịch sử phiên bản

| Bản | Ngày | Nội dung | Engine |
|---|---|---|---|
| v1.0 | 06/10/2026 | Vòng 1–5: mở đầu/kết 12+ biến thể, tên trần + vai trò, `Ông/bà`, Anh/Chị, `Tôi tên là:`, năm sinh + cờ, ngày Excel, người chết + trích lục, tách thửa + `land_rows`, sổ TK/tài khoản/thẻ, bảo hiểm, bảng `.doc`, luật R00–R11 | thuake5 |

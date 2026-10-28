# Regex thừa kế v1 — phân chia / từ chối / khai nhận di sản

**Trạng thái:** Active · **Phiên bản tài liệu:** v1.3 (TASK-10.1).
**Engine hiện hành:** [extract_contract.py](../../../upload_lab/extract_contract.py),
phiên bản lấy từ `ENGINE_VERSION`, không chép mã bản vào nhiều spec.
**Bằng chứng lịch sử:** 50 văn bản phân chia đầu tiên ở `D` (31 không có cờ,
11 được loại vì không phải văn bản, 8 gắn cờ) + file owner gửi
(`comment/Văn bản phân chia 1.doc`). Đây là kết quả quét cũ, không phải
độ chính xác được chấm bằng đáp án. Kiểm hiện tại theo [bộ đáp án](regex-expected-results.md).

File này sở hữu loại/vùng và đầu-cuối bản ghi thừa kế. Giá trị từng trường
chỉ do [regex-fields.md](regex-fields.md) sở hữu; [đáp án](regex-expected-results.md)
ghi cách kiểm. [Catalog](regex-rules.md) dẫn đường. Mâu thuẫn gộp/phục hồi tên
F01/F04/F05 được giữ chờ, không tự giải quyết bằng tuổi hoặc thứ tự file.

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

| Trường | Nguồn quy tắc duy nhất |
|---|---|
| `ho_ten, ten_goi_khac, gioi_tinh` | [Người](regex-fields.md#2-người): tên sạch, danh xưng trung tính để trống |
| `ngay_sinh, chi_co_nam_sinh` | Ngày/năm, không tự thêm 01/01; bảng phải giữ đúng cột |
| `cccd, noi_cap, ngay_cap_cccd` | Giấy tờ đúng người; không lấy ngày làm nơi cấp |
| `dia_chi` | Nhãn/vùng đúng người; ngày thuần không phải địa chỉ |

Bỏ cả dòng phả hệ (`Ông X có vợ là bà Y (Sinh ngày...)`) và khối
dừng trước dòng `chết ngày`.

## 3. Người chết (`raw.nguoi_chet`, bắt buộc có `chết/đã chết ngày DD/MM/YYYY`)

Trường người chết dùng [quy tắc trường §3](regex-fields.md#3-người-chết--theo-spec-hiện-hành-trừ-f01).
Dấu hiệu chết và vùng khai ở đây quyết định đây là người để lại di sản;
không đổi người chỉ để đầy đủ giấy tờ. Luật phục hồi gọi tắt F01 còn chờ.

Dạng ngoặc gộp (11–12/10/2026): `ông X (sinh năm 1956, đã chết ngày ...)` và
`ông X (Tên khác); (Sinh năm 1945, đã chết ngày ... theo trích lục...)` —
ngoặc bí danh có thể đứng trước ngoặc sinh/chết; phần trong ngoặc sau
ngày chết (`theo trích lục`, `Nơi thường trú`) vẫn được chấp nhận.

**Lần nhắc lặp:** luật “bản sau điền trường trống” của v1.2 là hiện trạng đã ghi,
không mở rộng luật phục hồi hoặc gộp tài sản trong TASK-10.1. Các lựa chọn đang
mâu thuẫn xem [F01/F04/F05](regex-fields.md#8-chờ-quyết-định--không-tính-đạt).
Danh sách số thửa 112,115 và ghi chú đánh số lại vẫn theo quy tắc định danh trường;
không tự chọn cách gộp các bản lặp.

## 4. Tài sản đất (mỗi thửa 1 dòng `danh_sach_thua_dat` + `land_rows` shape DB)

Khối đất mở bằng: `quyền sử dụng đất ... có/tại địa chỉ:`, `Phần
quyền sử dụng đất ... trong khối tài sản chung...`, `... theo
Giấy chứng nhận`, hoặc `thửa đất số ... (có địa chỉ tại/theo
GCN/theo bản đồ)`. Dừng trước: `Người/Những người thừa kế/nhận
thừa kế` (kể cả `III.`, `III. |`), `Nội dung/Thống nhất phân chia`,
`Bằng Văn bản này`, `Lời chứng`.

| Trường thửa | Nguồn quy tắc duy nhất |
|---|---|
| `so_thua_dat, so_to_ban_do` | [Định danh thửa](regex-fields.md#4-định-danh-thửa--theo-spec-hiện-hành), giữ nhãn/cột cả khi đảo thứ tự |
| `dien_tich, chi_tiet_dien_tich, land_rows` | [Diện tích/chi tiết](regex-fields.md#5-diện-tích-và-chi-tiết-đất--theo-spec-hiện-hành-trừ-cách-gộp), tổng độc lập |
| `muc_dich_su_dung, thoi_han_su_dung, phan_ghi_them, nguon_goc` | Giữ dữ liệu đúng ô; không cắt vì nhãn dài |
| `dia_chi, loai_gcn, so_gcn, so_vao_so, ngay_cap_gcn, co_quan_cap` | [Giấy chứng nhận](regex-fields.md#6-giấy-chứng-nhận--theo-spec-hiện-hành) |

Luật cũ “cùng thửa/tờ chỉ giữ bản đầu” mâu thuẫn catalog gộp/giữ khác tổng:
[F04/F05 chờ quyết định](regex-fields.md#8-chờ-quyết-định--không-tính-đạt).
Không dùng bảng ở đây để chốt một đáp án số bản ghi đang mở.

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

Bảng **đơn dòng** (không `|`, không xuống dòng — 12/10/2026): token hóa
thành "ô giả" — số đứng riêng, cụm chữ gộp, `Trong đó`/`Lâu dài` thành
ô riêng — rồi dùng chung bộ tách ô với bảng `|`; hỗ trợ **nhiều thửa**
liên tiếp (`35 44 150 NTS 2063  35 103 299  Trong đó ...  35 134 168`).
Ô số ngay sau thửa chỉ được nuốt làm `thoi_han_su_dung` khi giống kỳ
hạn (4 số, ngày `dd/mm/yyyy`, `Lâu dài`) — số diện tích nhỏ (`119`,
`299`) là thửa/chi tiết tiếp theo.

## 5. Tài sản sổ tiết kiệm / tài khoản — TẠM DỪNG (regex-decision-46)

Không bóc dòng. Khi văn bản có khối `sổ tiết kiệm` / `số dư tài khoản`,
engine chỉ ghi `"so_tiet_kiem"` vào `raw.tai_san_chua_ho_tro` và R12
cảnh báo để nhân viên biết file có phần này.

## 6. Quyền lợi bảo hiểm — TẠM DỪNG (regex-decision-46)

Tương tự §5: nhận diện khối `quyền lợi bảo hiểm` → `"bao_hiem"` trong
`raw.tai_san_chua_ho_tro` + R12. Không trích `so_hop_dong`, `ben_bao_hiem`...

## 7. Lời chứng — KHÔNG TRÍCH (regex-decision-46)

Không đối chiếu với người đầu văn bản nên không bóc người trong Lời chứng;
không còn `raw.loi_chung_nguoi` và luật R11.

## 8. Lịch sử phiên bản

| Bản | Ngày | Nội dung | Engine |
|---|---|---|---|
| v1.0 | 06/10/2026 | Vòng 1–5: mở đầu/kết 12+ biến thể, tên trần + vai trò, `Ông/bà`, Anh/Chị, `Tôi tên là:`, năm sinh + cờ, ngày Excel, người chết + trích lục, tách thửa + `land_rows`, sổ TK/tài khoản/thẻ, bảo hiểm, bảng `.doc`, luật R00–R11 | thuake5 |
| v1.1 | 06/10/2026 | regex-decision-46: bỏ lời chứng + R11; người chết dùng trường Người (`so_giay_to`/`ngay_cap`/`noi_cap`/`dia_chi`); sổ TK/bảo hiểm chỉ gắn cờ `tai_san_chua_ho_tro` + R12; không suy giới tính từ `Thị`, giới tính trống → R13; diện tích mơ hồ (`1.234`) → R13 | thuake5 |
| v1.2 | 07/10/2026 | Mẫu thật ông Thưởng: `ho_ten` chỉ giữ họ tên (bỏ đuôi vai trò ` - Con đẻ...`, `Là vợ của...`); `dia_chi` nhận `Hộ khẩu thường trú` + cắt đuôi người kế trên dòng gộp; lọc tên người chết dạng câu; `so_to_ban_do` chỉ giữ ký hiệu; `dien_tich` phải có chữ số, cắt `; Trong đó`, tách ONT/NTS viết liền; `Hiện nay là thửa...` → `phan_ghi_them` không mở thửa; khử trùng thửa `(thửa,tờ)`; thêm trường `nguon_goc`; tool hiển thị `Nguồn gốc`/`Cơ quan cấp`, bỏ chú thích "(chỉ có năm)"; R13 cờ cả diện tích không parse được; R04 cờ tên người chết dạng câu | thuake6 |
| v1.3 | TASK-10.1 | Loại/vùng ở đây, luật giá trị ở regex-fields, đáp án ở regex-expected-results; F01/F04/F05 chờ; không coi số cờ là tỷ lệ đúng | Xem ENGINE_VERSION trong engine |

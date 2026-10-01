# Word output — Xuất văn bản

**Trạng thái:** §1–§10 là **Draft phase "engine tĩnh"** — owner chốt hướng
29/09/2026, chờ duyệt chi tiết. Hành vi đang chạy thật ghi riêng ở §11
(Active cho tới khi phase này được triển khai).

## 1. Công dụng và phạm vi

Lấy dữ liệu hồ sơ **đã lưu** (Stage + sơ đồ), điền vào các file mẫu `.docx`,
ghi ra thư mục người dùng chọn. Mỗi mẫu được chọn tạo một file riêng.

Phase này chỉ làm **một việc**: bộ máy xuất Word chạy ổn định với
**placeholder tĩnh**. Placeholder tĩnh là chỗ đánh dấu trong mẫu Word, ví dụ
`[Người 2 - Họ tên]`, được thay bằng đúng một giá trị đã lưu. Nó không tự
quyết ai là chủ, ai nhận, câu nào xuất hiện.

Lời owner (29/09/2026): *"Tôi chỉ cần làm engine xuất word ổn định, danh sách
các trường, tên placeholder tĩnh để gắn vào word, chưa quan tâm đến logic
nghiệp vụ ở phase này, sau này khi ổn định, tôi sẽ phát triển placeholder
động — thay đổi theo dữ liệu. Nhưng hiện tại toàn bộ xuất theo placeholder
tĩnh."* và *"Tôi sẽ làm danh sách xuất sau, làm engine xuất ổn định vào
word."*

Trong phạm vi:

- Hồ sơ thừa kế (`inheritance`) **và** hồ sơ hai bên (`two_party`).
- Danh mục trường + tên placeholder tĩnh (§4).
- Mẫu lấy từ một thư mục mẫu (§5).
- Popup `Xuất Word` giữ ở thanh công cụ sơ đồ (§8).

Ngoài phạm vi (làm phase sau): placeholder động theo dữ liệu, phân chủ/người
nhận theo từng tài sản, danh sách văn bản chính thức cho từng loại việc, tab
Word riêng (MIN-118 — owner chọn giữ popup), in dấu Chủ/Nhận 1|2|3.

## 2. Người dùng và cách thao tác

Chuyên viên công chứng:

1. Soạn Stage, bấm `Cập nhật`; xếp sơ đồ, bấm `Lưu sơ đồ`.
2. Bấm `Xuất Word` trên thanh sơ đồ → popup hiện danh sách mẫu trong thư mục
   mẫu, mẫu nào dùng được/không dùng được và lý do.
3. Tích một hoặc nhiều mẫu, chọn thư mục đích, bấm `Xuất`.
4. Xem kết quả từng file: `Đã lưu` + tên file thật, hoặc `Lỗi` + lý do.

Muốn thêm văn bản mới: chép file `.docx` có placeholder vào thư mục mẫu. Không
cần sửa code.

## 3. Input, output và flow

```text
Bấm Xuất Word (Stage và sơ đồ không còn chỗ chưa lưu)
→ quét thư mục mẫu → danh sách mẫu + trạng thái dùng được
→ người dùng chọn mẫu + thư mục đích
→ backend đọc snapshot đã lưu: hồ sơ, Stage, sơ đồ
→ dựng bảng giá trị tĩnh (§4) một lần cho cả lượt
→ với từng mẫu: thay placeholder → kiểm tra còn sót → ghi file
→ kết quả saved/failed/skipped theo từng file
```

- Input: `case_id`, danh sách mẫu đã chọn, thư mục đích local đã tồn tại.
- Output: mỗi mẫu một `.docx`; kết quả gồm tên file thật, đường dẫn, trạng
  thái, lỗi; breakdown luôn có `succeeded`, `failed`, `skipped`.

## 4. Danh mục placeholder tĩnh

Quy tắc chung:

- Dạng `[Nhóm N - Trường]`. `N`, `M` là số nguyên từ 1.
- Placeholder đúng tên trong danh mục nhưng **không có dữ liệu** (người thứ
  N không tồn tại, ghế trống, trường `null`) → thay bằng **chuỗi rỗng**.
- Placeholder **không có trong danh mục** (gõ sai, trường chưa hỗ trợ) → file
  đó **lỗi**, liệt kê tên placeholder sai. Không ghi file còn sót `[...]`.
- Chỉ đổi dạng hiển thị (ngày `dd/mm/yyyy`, `Ông`/`Bà`); không suy luận
  nghiệp vụ.

**Tại sao:** rỗng khi thiếu dữ liệu cho phép một mẫu dùng chung cho hồ sơ ít
hay nhiều người. Lỗi khi sai tên để lỗi gõ mẫu không lọt vào văn bản ký.

### 4.1 Số `N` của người

| Loại hồ sơ | `N` là gì | Ví dụ |
|---|---|---|
| Thừa kế | Thứ tự dòng trong bảng Người của Stage **đã Cập nhật** (1 = dòng đầu) | `[Người 1 - Họ tên]` = dòng Người đầu tiên |
| Hai bên | Số ghế cố định trên sơ đồ: 1–15 Bên A, 16–30 Bên B | `[Người 16 - Họ tên]` = ghế đầu Bên B; ghế trống → rỗng |

Thừa kế: người có trong Stage nhưng chưa lên sơ đồ vẫn có số. Kéo đổi thứ tự
dòng Stage rồi `Cập nhật` thì số đổi theo. Nguồn: owner chọn 29/09/2026; hai
bên theo contract §13.10.

### 4.2 Hồ sơ và ngày xuất

| Placeholder | Giá trị |
|---|---|
| `[Hồ sơ - Số]` | `case_id` |
| `[Hồ sơ - Loại việc]` | `Thừa kế` / `Hai bên` |
| `[Hồ sơ - Loại văn bản]` | Tên hiển thị của `document_type` |
| `[Ngày lập hồ sơ]` | `ngay_lap_ho_so`, `dd/mm/yyyy` |
| `[Niêm Yết]` | `noi_niem_yet` |
| `[Ghi chú]` | `ghi_chu` |
| `[Ngày]`, `[Tháng]`, `[Năm]` | Ngày/tháng/năm lúc xuất |
| `[Ngày chữ]`, `[Tháng chữ]` | Ngày/tháng lúc xuất viết bằng chữ |
| `[Tên file]` | Tên file thật được ghi |

### 4.3 Người `N`

| Placeholder | Giá trị từ `person_row` |
|---|---|
| `[Người N - Họ tên]` | `ho_ten` |
| `[Người N - Giới tính]` | `gioi_tinh` |
| `[Người N - Xưng hô]` | `Ông` nếu Nam, `Bà` nếu Nữ, rỗng nếu không rõ |
| `[Người N - Ngày sinh]` | `ngay_sinh`: đủ ngày → `dd/mm/yyyy`; chỉ năm → `yyyy` |
| `[Người N - Năm sinh]` | Phần năm của `ngay_sinh` |
| `[Người N - Ngày chết]`, `[Người N - Năm chết]` | Như trên với `ngay_chet` |
| `[Người N - Số giấy tờ]` | `so_giay_to` |
| `[Người N - Ngày cấp]` | `ngay_cap` (cùng quy tắc ngày) |
| `[Người N - Nơi cấp]` | `noi_cap` |
| `[Người N - Địa chỉ]` | `dia_chi` |
| `[Người N - Quê quán]` | `place_of_origin` |

Ngày chỉ có năm hiển thị đúng năm; bỏ thủ thuật cũ đọc `01/01/yyyy` thành
`yyyy` (business-rules việc 1, 4–5).

### 4.4 Tài sản `N` và loại đất `N.M`

`N` = vị trí tài sản 1–3 trên Stage (contract §13.3). `M` = dòng loại đất thứ
M của tài sản đó.

| Placeholder | Giá trị từ `asset_row` |
|---|---|
| `[Tài sản N - Địa chỉ]` | `dia_chi` |
| `[Tài sản N - Loại sổ]` | `loai_so` |
| `[Tài sản N - Serial]` | `so_serial` |
| `[Tài sản N - Số vào sổ]` | `so_vao_so` |
| `[Tài sản N - Số thửa]` | `so_thua_dat` |
| `[Tài sản N - Số tờ]` | `so_to_ban_do` |
| `[Tài sản N - Hình thức sử dụng]` | `hinh_thuc_su_dung` |
| `[Tài sản N - Thời hạn]` | `thoi_han` |
| `[Tài sản N - Nguồn gốc]` | `nguon_goc` |
| `[Tài sản N - Ngày cấp sổ]` | `ngay_cap` |
| `[Tài sản N - Cơ quan cấp sổ]` | `co_quan_cap` |
| `[Tài sản N - Diện tích]` | Tổng `dien_tich` các dòng loại đất (asset không có field diện tích riêng) |
| `[Loại đất N.M - Loại đất]` | `land_rows[M-1].loai_dat` |
| `[Loại đất N.M - Diện tích]` | `land_rows[M-1].dien_tich` |
| `[Loại đất N.M - Thời hạn]` | `land_rows[M-1].thoi_han` |

Số thập phân hiển thị kiểu Việt Nam (`1.234,5`) — `[CONFIRM]` định dạng số.

### 4.5 Placeholder cũ — giữ chạy, không phát triển

Placeholder đang chạy ngoài danh mục trên (nhóm lọc `Chủ đất sống`,
`Chủ đất chết`, `Người nhận`, `Người từ chối`; `[Dòng …]`, `[Đoạn …]`,
inline, bảng hàng thừa kế; `[Người N - Quan hệ/Vai trò/Trạng thái/Tỷ lệ/Loại
giấy tờ/Nhãn địa chỉ]`; alias cũ như `[Tên N]`) vẫn chạy như hiện trạng để mẫu
PCDS không hỏng. Phase này không sửa, không cam kết đúng với dữ liệu 3 tài
sản/dấu theo vị trí, và không áp dụng cho hồ sơ hai bên (trên hồ sơ hai bên
chúng tính là placeholder không hỗ trợ). Owner chọn 29/09/2026.

Cảnh báo: `[Người N - …]` cũ đánh số theo thứ tự node sơ đồ; §4.1 đổi sang
thứ tự dòng Stage. Mẫu PCDS phải được kiểm lại bằng dữ liệu thật trước khi
bật phase này.

## 5. Thư mục mẫu và lưu trữ

- Mỗi file `.docx` ở **cấp đầu** thư mục mẫu = một văn bản chọn được. Bỏ qua
  file khóa `~$*`, file không phải `.docx`, thư mục con (kể cả `custom/` của
  web cũ). Owner chọn 29/09/2026.
- Đề xuất vị trí `[CONFIRM]`: bản dev `notary_v2/word_templates/`; bản đóng
  gói `<userData>/engine-data/notary_v2/word_templates/` (cùng chỗ DB,
  `shell/src/main/sidecar.js:63-69`), lần chạy đầu chép sẵn mẫu PCDS. **Tại
  sao:** thư mục trong gói cài đặt chỉ đọc và bị thay khi cập nhật app.
- `document_key` = tên file bỏ dấu, chữ thường, ký tự khác chữ/số thành `_`;
  bắt đầu bằng số thì thêm `mau_`. Tên hiển thị = tên file không đuôi. Hai
  file ra cùng key → cả hai `không dùng được`, lý do trùng tên.
- Tên file ra: `<document_key>_HS-<case_id>[_n].docx`. Không ghi đè; trùng
  tên thêm `_2`, `_3`, …
- Không lưu gì mới vào DB. Word chỉ đọc; file ra là thứ duy nhất được ghi.

## 6. Contract với phần khác

- Chỉ đọc dữ liệu đã commit: Stage sau `Cập nhật`, sơ đồ sau `Lưu sơ đồ`.
  Không đọc bản đang gõ, không dùng kết quả frontend tự tính.
- Hồ sơ thừa kế: placeholder tĩnh chỉ cần Stage; sơ đồ chỉ cần cho placeholder
  cũ §4.5. Hồ sơ hai bên: cần sơ đồ để biết ai ngồi ghế nào.
- Lệnh giữ tên `notary.word_export_options` + `notary.word_export_batch`.
  Phase này **đổi contract**, phải có revision được duyệt trước khi code
  (`contracts/README.md`):
  - §8.1: danh sách văn bản lấy từ thư mục mẫu thay catalog cố định;
    `document_key` theo quy tắc §5.
  - §13.5/§13.10: bật `word_export:true` cho `two_party`; bỏ
    `case_type_unsupported` cho Word.
  - Lý do chặn mới cho mẫu, ví dụ trùng key, file hỏng/không mở được.
  - Bỏ hay giữ các lý do chặn nghiệp vụ hiện có — xem §10.

## 7. Kiến trúc và công nghệ

Không thêm công nghệ: Python + `python-docx` trong sidecar như hiện tại.

- Backend Python sở hữu: quét thư mục mẫu, dựng bảng giá trị, thay
  placeholder, kiểm tra sót, đặt tên, ghi file.
- Electron chỉ: mở popup, chọn thư mục đích (native picker), gửi lệnh, hiện
  tiến trình/kết quả, mở file khi người dùng bấm.
- Bảng giá trị tĩnh dựng **một lần** mỗi lượt xuất; mọi mẫu trong lượt dùng
  cùng bảng.
- Thay placeholder và kiểm tra sót phải phủ: đoạn văn, bảng (cả bảng lồng
  bảng), header/footer (cả bảng trong header/footer), placeholder bị Word
  tách thành nhiều run.

"Ổn định" nghĩa là, và phải có test tự động cho từng ý:

1. Cùng dữ liệu + cùng mẫu → cùng nội dung file (trừ ngày xuất).
2. Mẫu khác nhau cho file khác nhau (hiện tại mọi key ra cùng một mẫu — §11).
3. Một file lỗi không làm hỏng/xóa file khác; file ghi dở được dọn.
4. Không bao giờ ghi đè; không ghi ra ngoài thư mục đích.
5. Không còn `[...]` của danh mục trong file đã lưu.
6. Thư mục đích không ghi được → lỗi trong vài giây, không treo (MIN-116).
7. Hủy giữa lượt: file đã lưu giữ nguyên, file chưa làm là `skipped`.

## 8. Giao diện

Giữ popup `Xuất Word` trên thanh công cụ sơ đồ (owner chọn 29/09/2026), chỉ
restyle theo [`../ui/`](../ui/README.md):

- Nút mờ khi Stage hoặc sơ đồ còn chỗ chưa lưu (chấm dirty), kèm gợi ý
  `Cập nhật`/`Lưu sơ đồ` trước. **Tại sao:** Word chỉ đọc bản đã lưu; xuất lúc
  đang sửa sẽ ra file khác với màn hình.
- Danh sách mẫu: checkbox + tên hiển thị; mẫu không dùng được bị mờ, ghi lý do.
- Chọn thư mục đích, nút `Xuất`, tiến trình, nút `Hủy`.
- Kết quả từng file; popup không tự đóng khi còn lỗi.
- Hồ sơ bị khóa: vẫn xem danh sách mẫu; nút `Xuất` mờ.

## 9. Lỗi, ngoại lệ và ví dụ

| Tình huống | Kết quả |
|---|---|
| Thư mục mẫu trống / không tồn tại | Popup báo chưa có mẫu; không xuất được |
| Mẫu có `[Người 3 - Hoten]` (gõ sai) | File đó lỗi, báo `[Người 3 - Hoten]` không hỗ trợ; file khác vẫn lưu |
| Hồ sơ 2 người, mẫu có `[Người 5 - Họ tên]` | Chỗ đó để trống; file lưu bình thường |
| Hai bên, ghế 16 trống | `[Người 16 - …]` rỗng |
| File mẫu hỏng / đang mở khóa | Mẫu đó lỗi, lý do không đọc được mẫu |
| Trùng tên file ở thư mục đích | Ghi `…_HS-12_2.docx` |
| Tất cả file lỗi | Job `failed` (`word_batch_failed`); trộn → `partial` |
| Hồ sơ cũ > 3 tài sản | `[Tài sản 4 - …]` vẫn đọc được theo thứ tự lưu `[CONFIRM]` |

Ví dụ: Stage thừa kế có 3 dòng Người: `Nguyễn Văn A` (Nam, 1950), `Trần Thị B`
(Nữ, 03/04/1955), `Nguyễn Văn C`. Mẫu `Ông/Bà [Người 2 - Xưng hô] [Người 2 -
Họ tên], sinh [Người 2 - Ngày sinh]` → `Bà Trần Thị B, sinh 03/04/1955`.
`[Người 1 - Ngày sinh]` → `1950`.

## 10. Câu hỏi mở, lịch sử và nguồn

### Câu hỏi mở (chưa chốt — không tự quyết)

1. **Chặn xuất theo nghiệp vụ.** Hiện có chặn khi thiếu chủ đất, thiếu người
   nhận, không có chủ đất đã chết, > 20 người (`word_batch_export.py:105-114`).
   Đề xuất: phase tĩnh **chỉ chặn lỗi kỹ thuật** (không có hồ sơ, chưa có dữ
   liệu Stage, mẫu hỏng/trùng key); thiếu dữ liệu thì placeholder rỗng. Đi
   cùng business-rules việc 13 (cho xuất hồ sơ `incomplete`).
2. Vị trí thư mục mẫu bản đóng gói (§5).
3. Định dạng số diện tích (§4.4) và ngày viết bằng chữ.
4. Hồ sơ cũ > 3 tài sản có cho `[Tài sản 4..5]` không (§9).
5. Tên hiển thị `document_type` cho hai bên (`chuyen_nhuong`, `tang_cho`,
   `cho_thue`, `dat_coc`).

### Lịch sử

- 22/07/2026: Word web, một mẫu → một file tải về (`word-output-detail.md`).
- 24/09/2026: Electron xuất nhiều file vào thư mục (MIN-104/105/110/112).
- 27/09/2026: MIN-123/125 hoãn Word; contract v2 giữ giới hạn Word cũ
  (§13.10).
- 29/09/2026: owner chốt hướng phase này — engine tĩnh, gồm cả hai bên, N
  thừa kế theo dòng Stage, mẫu từ thư mục, giữ popup, placeholder cũ giữ chạy,
  chưa in dấu Chủ/Nhận, danh sách văn bản làm sau.

### Nguồn

- Contract: [`contracts/notary-case-drafting.md`](../../../contracts/notary-case-drafting.md)
  §4.1–4.2, §8, §13.3, §13.5, §13.10.
- Catalog người dùng xem: `notary_v2/word_templates/placeholder_mapping.md` —
  phải cập nhật theo §4 cùng lúc triển khai.
- Chi tiết web cũ và tầng placeholder cũ: [`word-output-detail.md`](./word-output-detail.md).

## 11. Hiện trạng đang chạy (bằng chứng, 29/09/2026)

- Catalog văn bản cố định 3 key `khai_nhan_di_san`, `thoa_thuan_phan_chia`,
  `niem_yet` (chưa có mẫu) — `notary_v2/services/word_batch_export.py:87-101`.
- **Mọi key dùng cùng một mẫu**: sidecar gọi `_resolve_template(sess, None)`
  bỏ qua key (`shell/sidecar/notary_adapter.py:956`, `:991`), lấy mẫu active
  trong DB hoặc PCDS (`:385-423`).
- Word đọc cờ cũ `willReceive`/`isLandOwner` trên node
  (`word_engine.py:394-395`), trong khi workspace v2 lưu
  `ownPositions`/`receivePositions` (`case_workspace.py:22-25`, `:648-659`).
  Chưa kiểm chứng Word ra đúng chủ/người nhận trên hồ sơ lưu bằng v2.
- `[Người N]` đánh theo thứ tự node sơ đồ, người ngoài sơ đồ xếp sau
  (`word_engine.py:370-401`). Giới hạn 5 tài sản (`word_engine.py:31`).
- Kiểm tra sót placeholder chưa quét bảng lồng và bảng trong header/footer
  (`word_engine.py:1257-1272`).
- Hai bên: `word_export:false`, mọi lệnh Word trả `case_type_unsupported`
  (contract §13.5).
- Đã tốt, giữ: không ghi đè, `_2/_3`, per-file result, cancel, probe thư mục
  không ghi được (`word_batch_export.py:1-21`).

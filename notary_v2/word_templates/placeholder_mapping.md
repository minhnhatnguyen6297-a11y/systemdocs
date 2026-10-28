# Catalog Placeholder Word

Quy ước: `N` là số thứ tự người/tài sản; `M` là số thứ tự loại đất trong tài sản. Slot không có dữ liệu trả về rỗng toàn bộ.

**Vai trò:** catalog tham chiếu mẫu Word đang chạy; spec hiện hành ở
[`word-output.md`](../../_bmad-output/specs/notary_v2/word-templates.md#export).
Phase thư mục mẫu Active sau tích hợp NAIA-8/12 (04/10/2026).

### Token chuẩn bổ sung MIN-141 (03/10/2026)

| Nhóm | Token | Nguồn |
|---|---|---|
| Hồ sơ | `[noiniemyet]`, `[nguoinhanuyquyen]`, `[noidungviec]`, `[ngaylaphoso]`, `[ghichu]`, `[documenttype]` | Snapshot hồ sơ đã commit; key thiếu mới fallback master |
| Người | `[tenN]`, `[gioitinhN]`, `[ngaysinhN]`, `[ngaychetN]`, `[sogiaytoN]`, `[ngaycapN]`, `[diachiN]`, `[loaigiaytoN]`, `[noicapN]`, `[loaicutruN]`, `[loaidiachiN]` | Slot 1–20 legacy, tương ứng alias `[Tên N]` và các alias cũ; field ưu tiên snapshot Người |
| Cụm đất | `[loaidatMN]`, `[dientichMN]`, `[thoihanMN]` | M = cụm 1–20, N = vị trí tài sản; ví dụ `[loaidat12]` = cụm 1 tài sản 2 |

Không có alias rút gọn `[loaidatM]`. Null/rỗng đã commit được giữ nguyên;
không tự điền nơi niêm yết từ địa chỉ đất hoặc thời hạn lẻ vào cụm.
Token viết liền giữ slot legacy. Nhóm `[Người N - ...]` dùng thứ tự Stage đã lưu;
`[Bên A N - ...]` và `[Bên B N - ...]` giữ ghế cố định 1..15 mỗi bên.

## 1. Hồ sơ

| Placeholder | Chú thích | Hàm bên trong |
|---|---|---|
| `[Loại văn bản]` | Tên loại văn bản | - |
| `[Tên file]` | Tên file xuất | - |
| `[Ngày lập hồ sơ]` | Ngày lập hồ sơ | - |
| `[Nơi niêm yết]` | Nơi niêm yết người dùng nhập trên hồ sơ | Cột `InheritanceCase.noi_niem_yet`; KHÔNG fallback địa chỉ tài sản — thiếu dữ liệu thì rỗng |
| `[Niêm Yết]`, `[NIÊM YẾT]` | Alias cũ của nơi niêm yết | Cùng nguồn `noi_niem_yet` (bản HOA cho `[NIÊM YẾT]`) |
| `[Ghi chú]` | Ghi chú hồ sơ | - |
| `[Ngày]` | Ngày xuất Word | - |
| `[Tháng]` | Tháng xuất Word | - |
| `[Ngày chữ]` | Ngày xuất bằng chữ | Đổi số thành chữ |
| `[Tháng chữ]` | Tháng xuất bằng chữ | Đổi số thành chữ |

## 2. Người - tầng 1

Áp dụng cùng một bộ trường cho: `Người`, `Chủ đất sống`, `Chủ đất chết`, `Người nhận`, `Người từ chối`, `Hàng thừa kế`.

| Placeholder | Chú thích | Hàm bên trong |
|---|---|---|
| `[Người N - Xưng hô]` | Ông/Bà của dòng Stage N | Theo giới tính |
| `[Người N - Họ tên]` | Họ tên dòng Stage N đã lưu | - |
| `[Người N - Giới tính]` | Giới tính | - |
| `[Người N - Ngày sinh]` | Ngày sinh | - |
| `[Người N - Năm sinh]` | Năm của ngày sinh hoặc chỉ năm sinh | Chỉ năm `yyyy` |
| `[Người N - Ngày chết]` | Ngày chết | - |
| `[Người N - Năm chết]` | Năm của ngày chết hoặc chỉ năm chết | Chỉ năm `yyyy` |
| `[Người N - Loại giấy tờ]` | Loại giấy tờ | - |
| `[Người N - Số giấy tờ]` | Số giấy tờ | - |
| `[Người N - Ngày cấp]` | Ngày cấp giấy tờ | - |
| `[Người N - Nơi cấp]` | Nơi cấp giấy tờ | - |
| `[Người N - Nhãn địa chỉ]` | Thường trú tại/Cư trú tại/Nơi chết | - |
| `[Người N - Địa chỉ]` | Địa chỉ | - |
| `[Người N - Quan hệ]` | Quan hệ trên Diagram | Theo role/nhãn quan hệ Diagram |
| `[Người N - Vai trò]` | Role kỹ thuật trên Diagram | - |
| `[Người N - Trạng thái]` | Chủ đất sống/chủ đất chết/người nhận/người từ chối | Theo `WordExportContext` |
| `[Người N - Tỷ lệ]` | Tỷ lệ cuối cùng nếu có | Kết quả Diagram |
| `[Chủ đất sống N - Họ tên]` | Người N trong danh sách chủ đất còn sống | Lọc `Chủ đất` và chưa chết |
| `[Chủ đất chết N - Họ tên]` | Người N trong danh sách chủ đất đã chết | Lọc `Chủ đất` và đã chết |
| `[Người nhận N - Họ tên]` | Người N trong danh sách nhận | Lọc `Nhận` trên Diagram |
| `[Người từ chối N - Họ tên]` | Dành cho dữ liệu từ chối pháp lý được xác nhận | Hiện luôn rỗng vì Diagram chưa có đầu vào pháp lý này |

Các trường còn lại dùng cùng mẫu: `[Tên danh sách N - Tên trường]`.

## 3. Người - tầng 2

| Placeholder | Chú thích | Hàm bên trong |
|---|---|---|
| `[Cụm chủ đất chết]` | Tên một hoặc hai người để lại di sản | `[Chủ đất chết 1 - Xưng hô] [Chủ đất chết 1 - Họ tên]` + ` và ` + `[Chủ đất chết 2 - Xưng hô] [Chủ đất chết 2 - Họ tên]`; người thứ hai rỗng thì bỏ cả người và từ nối |
| `[Nối chủ đất chết 2]` | Từ nối tương thích cho template ghép trường | ` và ` nếu có chủ đất chết 2; ngược lại rỗng |
| `[Dòng người N]` | Một block thông tin dòng Stage N | `N. [Người N - Xưng hô] [Người N - Họ tên]; Sinh ngày: [Người N - Ngày sinh].`<br>`[Người N - Loại giấy tờ] số: [Người N - Số giấy tờ] do [Người N - Nơi cấp] cấp ngày [Người N - Ngày cấp].`<br>`[Người N - Nhãn địa chỉ]: [Người N - Địa chỉ].`<br>`Là [Người N - Quan hệ].` |
| `[Dòng người nhận N]` | Một block thông tin người nhận N | Cùng cấu trúc `[Dòng người N]`, dùng trường của danh sách `Người nhận` |
| `[Dòng người từ chối N]` | Một block thông tin người từ chối N | Cùng cấu trúc `[Dòng người N]`, cuối block thêm: `[Người từ chối N - Xưng hô] [Người từ chối N - Họ tên] đã từ chối di sản theo Văn bản từ chối nhận di sản số ......................... .` |
| `[Dòng khai tử chủ đất chết N]` | Một block thông tin chủ đất chết N | Xưng hô, họ tên, sinh, chết, giấy tờ khai tử, nơi chết |
| `[Dòng chủ đất sống tặng cho N]` | Placeholder tương thích cho input chuyển quyền riêng | Hiện luôn rỗng; không suy tặng cho từ nút `Nhận` |
| `[Người nhận inline N]` | Người nhận N trong câu ngang | Tự thêm `, ` hoặc ` và ` theo vị trí |
| `[Danh sách người nhận inline]` | Tất cả người nhận trong câu ngang | Ghép `[Người nhận inline 1]` đến `[Người nhận inline 20]` |
| `[Người từ chối inline N]` | Người từ chối N trong câu ngang | Tự thêm `, ` hoặc ` và ` theo vị trí |
| `[Danh sách người từ chối inline]` | Tất cả người từ chối trong câu ngang | Ghép `[Người từ chối inline 1]` đến `[Người từ chối inline 20]` |
| `[Đoạn người chết là chủ đất]` | Toàn bộ các dòng khai tử chủ đất chết | Ghép `[Dòng khai tử chủ đất chết N]` có dữ liệu |
| `[Đoạn quan hệ gia đình]` | Quan hệ vợ/chồng, con của chủ đất chết | Theo role Diagram; chỉ ghi từ chối khi có dữ liệu pháp lý riêng |
| `[Đoạn phân chia di sản]` | Nội dung phân chia | Chỉ gồm người nhận; không tự chuyển phần sở hữu của chủ đất sống |
| `[Danh sách người ký]` | Người ký văn bản phân chia | Chủ đất sống + người nhận, không lặp người |

## 4. Bảng hàng thừa kế

| Placeholder | Chú thích | Hàm bên trong |
|---|---|---|
| `[STT hàng thừa kế N]` | Số thứ tự dòng N | - |
| `[Họ tên hàng thừa kế N]` | Họ tên dòng N | - |
| `[Ngày sinh hàng thừa kế N]` | Ngày/năm sinh dòng N | - |
| `[Địa chỉ hàng thừa kế N]` | Địa chỉ dòng N | - |
| `[Ghi chú hàng thừa kế N]` | Quan hệ và trạng thái | Theo `WordExportContext` |
| `[Dòng hàng thừa kế N]` | Dòng text nếu không dùng bảng | `[STT] . [Họ tên] - [Ngày sinh] - [Địa chỉ] - [Ghi chú]` |
| `[Họ tên người ký N]` | Người ký dòng N | - |

## 5. Tài sản - tầng 1

| Placeholder | Chú thích | Hàm bên trong |
|---|---|---|
| `[Tài sản N - Địa chỉ]` | Địa chỉ tài sản N | - |
| `[Tài sản N - Loại sổ]` | Loại giấy chứng nhận | - |
| `[Tài sản N - Serial]` | Số serial | - |
| `[Tài sản N - Số vào sổ]` | Số vào sổ cấp GCN | - |
| `[Tài sản N - Số thửa]` | Số thửa đất | - |
| `[Tài sản N - Số tờ]` | Số tờ bản đồ | - |
| `[Tài sản N - Diện tích]` | Tổng diện tích | Cộng các dòng loại đất; fallback diện tích tài sản |
| `[Tài sản N - Hình thức sử dụng]` | Hình thức sử dụng | - |
| `[Tài sản N - Mục đích sử dụng]` | Các loại đất và diện tích | Ghép các dòng loại đất |
| `[Tài sản N - Thời hạn]` | Thời hạn chung | - |
| `[Tài sản N - Nguồn gốc]` | Nguồn gốc sử dụng | - |
| `[Tài sản N - Ngày cấp sổ]` | Ngày cấp giấy chứng nhận | - |
| `[Tài sản N - Cơ quan cấp sổ]` | Cơ quan cấp giấy chứng nhận | - |
| `[Tài sản N - Loại đất]` | Loại đất cấp tài sản (`prop.loai_dat`) | Giá trị đơn người dùng nhập cho cả thửa; KHÔNG phải dòng loại đất M |
| `[Loại đất tài sản N]` | Alias của `[Tài sản N - Loại đất]` | Cùng nguồn; thêm cho review NAIA-12 (nhãn động cấp tài sản) |
| `[Loại đất N.M - Loại đất]` | Loại đất M của tài sản N | - |
| `[Loại đất N.M - Diện tích]` | Diện tích loại đất M | - |
| `[Loại đất N.M - Thời hạn]` | Thời hạn loại đất M | - |
| `[Loại đất tài sản N.M]` | Loại đất THẬT của dòng M, tài sản N | Dùng cho nhãn động thay chữ ONT/CLN/NTS/LUC in cứng trong mẫu |

## 6. Tài sản - tầng 2

| Placeholder | Chú thích | Hàm bên trong |
|---|---|---|
| `[Dòng tài sản N]` | Dòng mở đầu tài sản N | `N. Quyền sử dụng đất tại: [Tài sản N - Địa chỉ] theo [Tài sản N - Loại sổ] số: [Tài sản N - Serial]; Số vào sổ cấp GCN: [Tài sản N - Số vào sổ] do [Tài sản N - Cơ quan cấp sổ] cấp ngày [Tài sản N - Ngày cấp sổ].` |
| `[Dòng thửa đất N]` | Số thửa, số tờ | `Thửa đất số: [Tài sản N - Số thửa], tờ bản đồ số: [Tài sản N - Số tờ].` |
| `[Dòng diện tích N]` | Tổng diện tích | `Diện tích: [Tài sản N - Diện tích] m2.` |
| `[Dòng hình thức sử dụng N]` | Hình thức sử dụng | `Hình thức sử dụng: [Tài sản N - Hình thức sử dụng].` |
| `[Dòng mục đích sử dụng N]` | Mục đích sử dụng | `Mục đích sử dụng: [Tài sản N - Mục đích sử dụng].` |
| `[Dòng thời hạn N]` | Thời hạn sử dụng | `Thời hạn sử dụng: [Tài sản N - Thời hạn].` |
| `[Dòng nguồn gốc N]` | Nguồn gốc sử dụng | `Nguồn gốc sử dụng đất: [Tài sản N - Nguồn gốc].` |
| `[Dòng loại đất N.M]` | Một dòng loại đất | `N.M. [Loại đất N.M - Loại đất]: [Loại đất N.M - Diện tích] m2; Thời hạn: [Loại đất N.M - Thời hạn].` |
| `[Đoạn mô tả di sản]` | Toàn bộ tài sản được xuất | Ghép các dòng tài sản và loại đất có dữ liệu |

## 7. Alias cũ

| Placeholder | Chú thích | Hàm bên trong |
|---|---|---|
| `[Tên N]`, `[Năm sinh N]`, `[CCCD N]` | Slot người của template cũ | Mapping tương thích cũ |
| `[Ngày cấp N]`, `[Nơi cấp CC N]`, `[Địa chỉ N]` | Giấy tờ, địa chỉ của slot cũ | Mapping tương thích cũ |
| `[Địa chỉ đất]`, `[Loại sổ]`, `[Serial]`, `[Số vào sổ]` | Tài sản chính của template cũ | Alias tài sản 1 |
| `[Số thửa]`, `[Số tờ]`, `[Diện tích]`, `[Nguồn gốc]` | Tài sản chính của template cũ | Alias tài sản 1 |
| `[ONT]`, `[CLN]`, `[NTS]`, `[LUC]` | Diện tích theo VỊ TRÍ dòng loại đất 1/2/3/4 của tài sản 1 (mẫu cũ in cứng nhãn "Loại đất 1: ONT" rồi `[ONT]` là diện tích dòng đó — KHÔNG tra theo mã loại đất; quyết định Owner 02/10/2026, NAIA-8 comment `01a0fd42-5cbe-7076-976e-ef907c8ca086`) | Dòng ở vị trí đó vắng → rỗng; tài sản không tồn tại → không map (export báo sót) |
| `[ONT N]`, `[CLN N]`, `[NTS N]`, `[LUC N]` | Như trên nhưng của tài sản N | `N` là chỉ số tài sản, không phải vị trí dòng |

## 8. Tầng 3

| Placeholder | Chú thích | Hàm bên trong |
|---|---|---|
| Chưa dùng | Cụm phải đối chiếu nhiều phần của văn bản | - |

## 9. Nhãn mục in cứng của biểu mẫu hành chính

Ba mẫu thuế `2. DK18, thuế 1..3` in cứng nhãn mục `[01]`..`[54]` và `[NN.M]`.
Đây là CHỮ của biểu mẫu, không phải placeholder — chỉ được miễn khỏi kiểm tra
placeholder sót khi thuộc danh sách đã xác minh của ĐÚNG mẫu đó
(`VERIFIED_FIXED_CODES` trong `services/word_engine.py`). Mẫu khác chứa token
dạng `[01]`/`[54.99]` vẫn bị báo thiếu và chặn export.

## 10. Sửa ngữ cảnh khi migrate (review NAIA-12)

Một số mẫu cũ in CỨNG dữ liệu hồ sơ thay vì placeholder — migrate đổi đúng
đoạn đó thành placeholder động, ghi `context_fix` trong manifest
(`_apply_context_fixes` trong `services/word_template_migration.py`):

- Ba mẫu `2. DK18, thuế 1..3`: nhãn `Loại đất <vị trí>: ONT/CLN/NTS/LUC` in
  cứng → `[Loại đất tài sản N.<vị trí>]` để in loại đất THẬT của từng dòng
  (trước đó nhãn cứng làm sai khi hồ sơ xếp dòng khác thứ tự mẫu). Token
  diện tích theo vị trí `[ONT N]`/`[CLN N]`/... giữ nguyên.
- `2. DK18, thuế 2` và `thuế 3` là tờ khai của TÀI SẢN 2/3: token đất không
  hậu tố `[Diện tích]`, `[Diện tích 2]`, `[Loại đất 2]`, `[Địa chỉ đất]`
  trong những mẫu này được đổi thành `... tài sản 2/3` cho đúng đối tượng
  (ngoài các mẫu đó token giữ alias tài sản 1 như cũ).
- `1. Khai nhận di sản Vũ Dương` và `1. PCDS`: liệt kê in cứng
  `Mục đích sử dụng: ONT: [ONT] m2; CLN: [CLN] m2; ...` →
  `[Mục đích sử dụng 1]` — chỉ in các dòng đất thật của hồ sơ, không còn
  nhãn cứng hay đuôi `: m2` thừa.

Mọi sửa ngữ cảnh chỉ áp trên đúng stem mẫu đã đối chiếu; mẫu khác có cùng
chuỗi vẫn giữ nguyên (kiểm thử `test_migrate_context_fix_leaves_other_-
files_untouched`).

## 11. Người được ủy quyền (slot)

| Placeholder | Chú thích | Hàm bên trong |
|---|---|---|
| `[Danh sách người được ủy quyền]` | Block nhiều dòng tất cả đại diện | Ghép `[Dòng người được ủy quyền 1]` đến hết danh sách |
| `[Danh sách người được ủy quyền inline]` | Tất cả đại diện trong câu ngang | Ghép `[Người được ủy quyền inline N]` |
| `[Dòng người được ủy quyền N]` | Block thông tin đại diện N | Cùng cấu trúc `[Dòng người N]` |
| `[Người được ủy quyền inline N]` | Đại diện N trong câu ngang | Tự thêm `, `/` và ` theo vị trí |
| `[Người được ủy quyền N - <trường>]` | Một trường của đại diện N | Ví dụ `[Người được ủy quyền 1 - Họ tên]` |
| `[<Trường> người được ủy quyền N]` | Dạng tiền tố | Ví dụ `[Họ tên người được ủy quyền 2]` |

Nguồn: participants đã LƯU vai trò `Người được ủy quyền` — không yêu cầu node
Diagram (NAIA-8). Engine đọc slot `N` từ mọi dạng token trên (kể cả
`inline N`); token không hậu tố tính slot 1. Mẫu yêu cầu slot N lớn hơn số
đại diện đã lưu → theo W6/W8 (23/10/2026) export vẫn tạo file, slot trống,
và ghi "người được ủy quyền N" vào `missing` của kết quả (trước đây: lỗi
`word.missing_authorized_person`, review NAIA-12: `[Người được ủy quyền inline 2]` từng bị nhận nhầm
slot 1 nên slot 2 trống vẫn xuất).

## 12. Quyết định Owner 02/10/2026 và tương thích MIN-141

- Tổng diện tích bằng chữ: `[Diện tích chữ tài sản N]`; alias `[Diện tích chữ]`
  dùng tài sản 1. Token chỉ chứa giá trị; mẫu tự ghi đơn vị `m²`.
- `[Năm chết]` dùng người 1 và chỉ xuất năm; `[ngaychetN]` giữ ngày đầy đủ
  như MIN-141. Ngày đầy đủ hiển thị `dd/mm/yyyy`, chỉ năm giữ `yyyy`.
- Bỏ `[Số công chứng]`, `[Giá chuyển nhượng]`, `[Người ủy quyền2]` và alias
  sai chính tả tương ứng. Mẫu chưa migrate còn các token này phải báo lỗi,
  không tự điền hay đăng ký alias rỗng. Manifest ghi tên/số lần bỏ; giữ nhãn
  biểu mẫu hành chính cần người dùng điền tay.
- `[Người ủy quyền]` cũ chuyển theo ngữ cảnh sang thông tin **người được ủy quyền**.
  Alias MIN-141 `[Ngườ ủy quyền]` đọc metadata `nguoinhanuyquyen` đã xác nhận
  nếu key có trong snapshot, kể cả null. Nhóm đại diện đầy đủ vẫn đọc vai trò
  đã lưu, không suy từ vị trí dòng.
- Nơi niêm yết nhập tay là đường chính. `workspace_update` cập nhật snapshot
  metadata cùng revision. Cơ quan niêm yết theo ngày lập hồ sơ; ngày cấp giấy
  tờ chỉ chọn dạng địa chỉ nguồn. Giấy chứng tử giữ nơi cấp xác nhận độc lập.
  Quy tắc chuyển địa chỉ thuộc feature địa chỉ, không tự suy trong Word.

Nguồn: owner comments NAIA-8/12 ngày 02/10/2026, yêu cầu tích hợp 03/10/2026;
snapshot MIN-141 theo [entities](../../contracts/entities.md) §8–§9.

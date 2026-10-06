# Regex Rule Catalog — Quy chuẩn Trích xuất Văn bản Công chứng

**Trạng thái:** Catalog quy tắc trích xuất; khi code và catalog lệch, đối chiếu
fixture rồi cập nhật cùng thay đổi. **Nguồn:** `upload_lab/docs/regex-rules.md`
trước đợt gom 29/09/2026. Flow và giới hạn ở [`README.md`](./README.md).

## 0. Core nằm ở đâu (đọc trước khi sửa)

**Owner 06/10/2026:** lõi regex dùng chung là
`tools/regex_workbench/engine` (zoning-first, provenance, trạng thái
matched/ambiguous/missing — Owner NAIA-4 02/10/2026 chọn). Lõi phục vụ cả
trích xuất và đề xuất placeholder cho mẫu Word chưa gắn template.
`upload_lab/extract_contract.py` là **engine thừa kế đang chạy**, giữ vai
trò nguồn kiến thức trường để port sang profile workbench — không còn
là bản gốc của core dùng chung.

| Thứ | File |
|---|---|
| Lõi regex dùng chung | `tools/regex_workbench/engine/` + profile JSON |
| Engine thừa kế đang chạy (nguồn port sang profile) | `upload_lab/extract_contract.py` (docstring đầu file dẫn tiếp) |
| Test giữ hành vi | `upload_lab/tests/test_upload_lab_extract_contract.py` |
| Tool test giao diện (chọn 1 file Word → xem Người/Thửa/JSON) | `upload_lab/tools/regex_test_tool.py` (chạy bằng `upload_lab/run_regex_test.bat`) |
| Luật kiểm tra kết quả (R00..R10, R12 tài sản chưa hỗ trợ, R13 dữ liệu mơ hồ/thiếu căn cứ; R11 lời chứng đã xóa theo decision-46) | `upload_lab/kiem_tra_trich_xuat.py` + test `tests/test_kiem_tra_trich_xuat.py` |
| Quét hàng loạt bằng luật trên | `upload_lab/tools/quet_kiem_tra.py` (`--loc`, `--offset/--limit`, `--ca-doc`) |
| Repo test cho nhân viên (Test 1 file + Test cả thư mục + Xem log, log cố định) | `regex-test-tool/tool/` tất cả trong 1 folder (chạy bằng `tool/run.bat`) |
| Catalog quy tắc này | `docs/spec/upload_lab/regex-rules.md` |
| Báo cáo từng loại văn bản (kết quả test + nguyên tắc bằng lời) | `.agents/` (file tạm, không commit) |

Phạm vi core (quyết định owner 05/10/2026): core chỉ trích **xuất**
người + tài sản bằng regex, **không** so sánh/đối chiếu/gộp —
có người nào xuất dữ liệu người đó (kể cả người trong Lời chứng).
`so_cong_chung` vẫn được đọc để phục vụ upload/audit portal nhưng
không còn là tiêu chí đủ/thiếu của core.

Catalog này tập hợp và chuẩn hóa toàn bộ quy tắc trích xuất dữ liệu từ file Word (`.doc`, `.docx`) sang JSON web form trong `extract_contract.py`.

---

## 1. Nguyên tắc chung

### 1.1. Đọc dữ liệu
- Nguồn dữ liệu là file Word `.doc` và `.docx`.
- `.docx` đọc có cấu trúc (bảo toàn thứ tự đoạn văn và bảng biểu table để tránh trộn lẫn Bên A / Bên B).
- `.doc` đọc qua Windows IFilter dạng plain text.
- Tầng regex tập trung nhận diện tiêu đề, phân tách đương sự, bóc tách tài sản và chuẩn hóa trường sau khi đã đọc text.

### 1.2. Chuẩn hóa Số công chứng
- Dạng raw thường gặp:
  - `428/2026/CCGD` hoặc `428.2026/CCGD` $\rightarrow$ Chuẩn hóa web: `428/2026`
  - `2433.2025/PCDS/CCGD` $\rightarrow$ Chuẩn hóa web: `2433/2025`
  - `2233.2025/TCDS/CCGD` $\rightarrow$ Chuẩn hóa web: `2233/2025`
- Nguyên tắc: Giữ số thứ tự và năm `xxx/yyyy`, loại bỏ hậu tố mã nghiệp vụ khi so khớp và điền web form.

### 1.3. Nhận diện Loại tài sản (`loai_tai_san`)
- Nếu có `quyền sử dụng đất`:
  - Có chi tiết nhà ở / công trình xây dựng (diện tích sàn, kết cấu, số tầng, cấp công trình...): **`Đất đai có tài sản`**
  - Chỉ có thông tin thửa đất / tờ bản đồ / diện tích đất: **`Đất đai không có tài sản`**
  - *Lưu ý*: Loại bỏ nhiễu tiêu đề chuẩn của phôi sổ ("Giấy chứng nhận quyền sử dụng đất, quyền sở hữu nhà ở và tài sản khác gắn liền với đất") trước khi kiểm tra chi tiết tài sản gắn liền.
- Ô tô / Xe máy: **`Ô tô - Xe máy`**
- Không có tài sản: **`Không có tài sản`**

---

## 2. Quy tắc chi tiết theo từng loại văn bản

Chi tiết đầy đủ từng loại nằm ở file riêng (`regex-<loại>.md`,
hiện có [`regex-thua-ke.md`](./regex-thua-ke.md) v1 cho thừa kế);
mục này chỉ tra nhanh. Khi lệch nhau, file riêng của loại đó đúng.

### 2.1. Hợp đồng chuyển nhượng (`DOC_KIND_TRANSFER`)
- **Nhóm HĐ**: `Chuyển nhượng - Mua bán`
- **Tiêu đề canonical**: `Hợp đồng chuyển nhượng quyền sử dụng đất` (hoặc kèm tài sản gắn liền với đất)
- **Đương sự**:
  - `Bên A`: Bên chuyển nhượng
  - `Bên B`: Bên nhận chuyển nhượng
  - Người yêu cầu công chứng: Ưu tiên Bên B (Bên nhận chuyển nhượng).
- **Tài sản**:
  - *Điểm bắt đầu*: `quyền sử dụng đất ... có địa chỉ tại:` hoặc `Đối tượng của Hợp đồng này là...`
  - *Điểm kết thúc*: Dừng trước `1.2`, `Điều 2`, `Giá chuyển nhượng`, `Phương thức thanh toán`, `Bằng Hợp đồng này`.

### 2.2. Văn bản cam kết tài sản riêng (`DOC_KIND_ASSET_COMMITMENT`)
- **Nhóm HĐ**: `Thoả thuận - Cam kết`
- **Tiêu đề canonical**: `Văn bản cam kết tài sản riêng`
- **Đương sự**:
  - Gồm cả 2 vợ chồng (Người chồng - Ông ... / Người vợ - Bà ...).
  - Người yêu cầu công chứng: Người đứng tên cam kết tài sản riêng.
- **Tài sản**:
  - *Điểm bắt đầu*: `quyền sử dụng đất ... có địa chỉ tại:` hoặc `hiện đang sở hữu Tài Sản là` / `Tài Sản là`.
  - *Điểm kết thúc*: Dừng trước `Bằng văn bản này chúng tôi xác định`, `Hai vợ chồng chúng tôi cam kết`, `Chúng tôi công nhận`.

### 2.3. Văn bản thỏa thuận hủy bỏ / sửa đổi / bổ sung (`DOC_KIND_TRANSFER_CANCELLATION`)
- **Nhóm HĐ**: `Thoả thuận - Cam kết` (hoặc `Phụ lục hợp đồng - văn bản sửa đổi`)
- **Tiêu đề canonical**: `Văn bản thỏa thuận về việc hủy bỏ hợp đồng chuyển nhượng quyền sử dụng đất`
- **Đương sự**: 2 bên tham gia thỏa thuận hủy bỏ.
- **Tài sản**: Đoạn trích tham chiếu thông tin thửa đất/GCN từ hợp đồng gốc, dừng trước `và được Công chứng viên chứng nhận`, `số công chứng`.

### 2.4. Hợp đồng thế chấp (`DOC_KIND_MORTGAGE`)
- **Nhóm HĐ**: `Cầm cố - Thế chấp - Vay`
- **Tiêu đề canonical**: `Hợp đồng thế chấp quyền sử dụng đất` (hoặc kèm tài sản gắn liền với đất)
- **Đương sự**:
  - `Bên A`: Bên thế chấp (cá nhân/hộ gia đình).
  - `Bên B`: Bên nhận thế chấp (thường là Ngân hàng / Pháp nhân / Chi nhánh + Người đại diện ký).
  - Người yêu cầu công chứng: Người đại diện ngân hàng (Bên B).
- **Tài sản**:
  - Trích xuất thông tin thửa đất / GCN từ phần mô tả tài sản hoặc trích xuất tối thiểu `Quyền sử dụng đất`.

### 2.5. Văn bản phân chia di sản (`DOC_KIND_INHERITANCE_PARTITION`)
- **Nhóm HĐ**: `Thừa kế (khai nhận - phân chia di sản thừa kế )`
- **Tiêu đề canonical**: `Văn bản phân chia di sản`
- **Đương sự**:
  - Nhóm người ký ở phần mở đầu: `NHỮNG NGƯỜI HƯỞNG DI SẢN` (bắt đầu từ `Chúng tôi là những người được hưởng di sản...`; chấp nhận biến thể `Tôi là những người...`, mở đầu đơn `Người được hưởng di sản theo pháp luật ... là:`, `Người được hưởng di sản thừa kế của ...:`, `(Tôi/Chúng tôi) là người được hưởng di sản ...` + kết `Tôi/Chúng tôi tự nguyện lập Văn bản này`).
  - Tên người đứng sau `Ông`/`Bà` (kể cả dạng `1. Bà ...`, `Bà: ...`, `Ông/bà:` (giới tính để trống + R13, không suy qua `Thị`), `Người vợ - Bà: ...`, `Tôi là:/Tôi tên là: Bà ...` cùng dòng); người vợ ghi tên trần `Tên - Vợ ông X` vẫn tính 1 người, giới tính suy từ `Vợ`/`Chồng`. `ho_ten` chỉ giữ họ tên (Owner 07/10/2026): cắt đuôi vai trò ` - Con đẻ ông X` lẫn dòng riêng `Là vợ/con của...`, không gộp vào tên. Tên cắt trước `|` (dấu căn dòng của `.doc`), trước nhãn ngày sinh (bắt buộc kèm giá trị ngày/năm, vì `Năm` là âm tiết tên hay gặp), trước `có vợ/chồng là`, trước `không` (câu "không có ai..."), trước nhãn giấy tờ (`CCCD`/`CMND`/`CC`/`Căn cước`/`Giấy`), trước nhãn địa chỉ/cư trú và ngoặc ngày sinh của người khác; bỏ cả dòng phả hệ (`Ông X có vợ là bà Y (Sinh ngày...)`); khối của 1 người dừng trước dòng `chết ngày`.
  - Vai trò đứng đầu dòng vẫn nhận người (09/10/2026): `Con đẻ - Bà X`, `Mẹ đẻ - Ông Y`, `Người chồng -`, `Người vợ -`, `Bên B: Bà X`, `Đại diện:`, `Tôi (tên) là:`; vai trò chỉ đi vào `gioi_tinh`/bỏ, không vào `ho_ten`.
  - Tổ chức không tính người: tên chứa `chi nhánh|văn phòng|công ty|ngân hàng|chi cục|UBND|bệnh viện` hoặc không viết hoa đầu từ → loại (09/10/2026).
  - Địa chỉ chung cặp vợ chồng (`Cả hai ông bà cùng thường trú tại: X`, `Cả hai cùng thường trú tại: X`) gán cho **cả hai** người trong khối (09/10/2026).
  - Nhãn địa chỉ bổ sung: `Địa chỉ:`, `Trú tại:`, `Địa chỉ thường trú:`, nhãn đánh số (`1.3. Địa chỉ:`). Nhãn giấy tờ bổ sung: `CC số:`, `Căn cước công dân mới số:`, `cấp ngày:` (có hai chấm), `cấp tại X ngày DD/MM/YYYY`.
  - Người một dòng (`Bà ... - Sinh năm ..., CCCD số ..., ...; Nơi thường trú: ...`): địa chỉ lấy ngay trên dòng tên.
  - Ngày sinh 2 dạng: `Sinh ngày: DD/MM/YYYY` và `Sinh năm YYYY` (không dấu hai chấm cũng nhận). Quy ước owner 06/10/2026 (phương án 1): chỉ có năm thì `ngay_sinh` giữ đúng `YYYY` (không tự thêm 01/01), kèm cờ `chi_co_nam_sinh: true` để phân biệt với ngày đủ (nhận diện chắc vì luôn có nhãn `Sinh năm` đi kèm, không đoán số năm trôi nổi).
  - CCCD sau `Căn cước công dân số` / `Căn cước số` / `CCCD số` (kể cả `số:` dính hai chấm); nơi cấp sau `do ... cấp ngày`, nếu thiếu `do` thì lấy cụm sau số giấy tờ; ngày cấp sau `cấp/ký ngày`; địa chỉ sau `Thường trú tại:` / `Cư trú tại:` / `Nơi thường trú:` / `Nơi thường trú tại:` / `Hộ khẩu (thường trú):` (kể cả giữa dòng sau `;`), cắt đuôi `Là vợ/con của...` và đầu người kế khi IFilter gộp dòng, trừ `Nơi thường trú cuối cùng trước khi chết` của người đã chết.
  - Dừng trước `Người để lại di sản:`, `Chúng tôi/Tôi tự nguyện lập Văn bản này`.
  - *Không đưa người để lại di sản, bố mẹ đẻ đã chết, phần kể phả hệ, người làm chứng trong Lời chứng vào danh sách đương sự. Người đã chết trích riêng ở `raw.nguoi_chet` (bắt buộc có `chết/đã chết ngày DD/MM/YYYY`), gồm tên gọi khác, năm sinh, trích lục khai tử, địa chỉ cuối. Điều kiện loại người chết trong khối đương sự là `chết ngày + ngày tháng` cụ thể (không loại khi chỉ có chữ `chết` chung chung). Cặp vợ chồng chết ghi chung 1 dòng (`Ông A và bà B; Sinh năm...; chết ngày...`) tách thành 2 bản ghi (09/10/2026); tên người chết là câu văn (từ thường, dấu câu, > 6 từ) bị loại và báo R04.*
- **Tài sản**:
  - *Điểm bắt đầu*: Sau heading `Di sản:` / `Di sản của ... để lại là:` hoặc dòng `quyền sử dụng đất ... có địa chỉ tại:` / `... tại địa chỉ:` / `Phần quyền sử dụng đất ... trong khối tài sản chung ...`.
  - *Điểm kết thúc*: Dừng trước `Người thừa kế:`, `Những người thừa kế`, `Những người nhận thừa kế` (kể cả `III. ...`, `III. | ...` của `.doc`), `Nội dung phân chia di sản`, `Bằng Văn bản này`, `Lời chứng`.
  - *Loại sổ (`loai_gcn`)*: cụm sau `Giấy chứng nhận` trước `số` (ví dụ `quyền sử dụng đất`).
  - *Tách thửa* (quyết định owner 05/10/2026, bổ sung 07/10/2026): mỗi thửa 1 dòng trong `raw.danh_sach_thua_dat` — dòng bảng/bullet nào có số thửa thì mở thửa mới (nhãn `Thửa đất số` hoặc `Số thửa`, `Tờ bản đồ số` hoặc `Số tờ`); dòng `Trong đó` hoặc dòng ngắn không số thửa thì gộp vào `chi_tiet_dien_tich` của thửa đang mở (không ghi đè diện tích thửa); `Diện tích` bỏ `(bằng chữ: ...)`, cắt phần thừa sau `,`/`;`/`trong`/`theo`, giá trị không có chữ số bị loại; `so_to_ban_do` chỉ giữ số/ký hiệu, cắt đuôi `Bản đồ địa chính năm ...`; `Nguồn gốc (sử dụng đất)` → `nguon_goc`; dòng `Hiện nay là thửa đất số X; Tờ Y` là đánh số lại của cùng thửa → `phan_ghi_them`, không mở thửa; đuôi `Nay là thửa/tờ...` hoặc ngoặc nguồn `(được tách từ thửa N)` trong ô số thửa/tờ cũng vào `phan_ghi_them`, giữ ký hiệu đầu (09/10/2026); thửa `(so_thua_dat, so_to_ban_do)` lặp lại chỉ giữ bản ghi đầu; số vào sổ cắt từ thừa; context GCN/địa chỉ/ngày cấp/cơ quan cấp copy vào từng thửa. `phan_ghi_them` cộng dồn (`; `), không ghi đè. Thửa "ma" — không có trường dữ liệu nào ngoài trường kế thừa context và không có chi tiết có `dien_tich` — bị loại (09/10/2026). Trường xe/tàu (`Số khung`, `Số máy`, `Số đăng ký`, `Nhãn hiệu`, `Biển số`, `Loại xe/tàu`, `Dung tích`, `Mã số`) và heading `Tài sản thứ N:` không tạo thửa (09/10/2026). Bullet `.doc` dạng `a|Thửa đất số: ...` (letter-prefixed) cũng là nhãn thửa. Dòng dữ liệu kiểu `04 Nay là tờ bản đồ 24 | 104 Nay là thửa đất số 321 | ...` không được nhận nhầm làm tiêu đề bảng. Khối đất mở được cả khi không có cụm địa chỉ mà chỉ có `... theo Giấy chứng nhận` (ví dụ `Quyền sử dụng đất mang tên Hộ ông ... 450 m2 đất theo GCN`). Serial chấp nhận `Đ` (`Đ 364866`).
  - *Bảng `.doc` đọc bằng IFilter*: IFilter giữ ô bảng bằng TAB (code đổi thành ` | `, cắt `|` thừa đầu/cuối dòng do TAB thụt đầu dòng); bảng dồn 1 dòng thì tách theo dòng ô (ô `Số thửa` làm neo, hết `Phần ghi thêm` thì vào dữ liệu, gặp `2.2.`/chữ thường thì dừng).

### 2.6. Văn bản từ chối nhận di sản (`DOC_KIND_INHERITANCE_REFUSAL`)
- **Nhóm HĐ**: `Từ chối nhận di sản thừa kế`
- **Tiêu đề canonical**: `Văn bản từ chối nhận di sản`
- **Đương sự**:
  - Đơn phương 1 người (`Tôi là:`) hoặc tập thể (`Chúng tôi là:`, kể cả từ chối hưởng thế vị): `NGƯỜI TỪ CHỐI NHẬN DI SẢN`.
  - Tên người đứng sau `Ông`/`Bà`/`Anh`/`Chị` (kể cả `1. Chị ...`, `3. Anh ...`).
  - Dừng trước `Nay, tôi/chúng tôi tự nguyện lập Văn bản này`, `Theo quy định của pháp luật`.
  - *Người đã chết (`chết ngày...`) không vào danh sách đương sự*.
- **Tài sản**:
  - Hỗ trợ đơn tài sản hoặc đa tài sản (`1. Tài sản thứ nhất:`, `2. Tài sản thứ hai:`...).
  - Tài sản đất: xem quy tắc tách thửa ở §2.5.
  - Tài sản sổ tiết kiệm / tài khoản: xem §2.8.
  - *Điểm kết thúc*: Dừng trước `Bằng Văn bản này, tôi ... từ chối nhận kỷ phần thừa kế`, `Tôi xin cam đoan`, `Người từ chối hưởng di sản`, `Lời chứng`.

### 2.7. Văn bản khai nhận di sản (`DOC_KIND_INHERITANCE_DECLARATION`)
- **Nhóm HĐ**: `Thừa kế (khai nhận - phân chia di sản thừa kế )`
- **Tiêu đề canonical**: chứa `khai nhận di sản` (ví dụ `Văn bản khai nhận di sản thừa kế`).
- **Đương sự**: cùng cấu trúc mở đầu với phân chia (`Chúng tôi là...`, `Tôi là: ...`, `Người được hưởng di sản ...`); nhãn hiển thị `NGƯỜI KHAI NHẬN DI SẢN`.
- **Tài sản**: đất (quy tắc §2.5) hoặc sổ tiết kiệm / tài khoản (quy tắc §2.8).

### 2.8. Tài sản sổ tiết kiệm / tài khoản (trong văn bản thừa kế)
- Khối tài sản bắt đầu ở `sổ tiết kiệm`, `số dư tài khoản`, `số tiền gốc và lãi`; dừng trước phần người thừa kế, `Bằng Văn bản này`, cam đoan, `Lời chứng`.
- Mỗi sổ 1 dòng trong `raw.danh_sach_so_tiet_kiem`: loại sổ (`có kỳ hạn`), số hiệu (`AC 00033961022`, `IE4025426`), ngân hàng (sau `do`, trước `chi nhánh`/`số hiệu`/`phát hành`), chi nhánh, ngày phát hành, chủ sổ (sau `cho ông/bà:`).
- Tài khoản: số tài khoản (`số tài khoản:`), chủ (sau `mang tên`).
- `loai_tai_san` của văn bản: `Sổ tiết kiệm`.

### 2.9. Quyền lợi bảo hiểm (trong văn bản thừa kế)
- Khối tài sản bắt đầu ở `quyền lợi bảo hiểm`; dừng trước phần người thừa kế, `Bằng Văn bản này`, cam đoan, `Lời chứng`.
- Mỗi quyền lợi 1 dòng trong `raw.danh_sach_bao_hiem`: số hợp đồng (sau `số`, mở đầu bằng chữ số), bên bảo hiểm (sau `ký giữa`, cắt hậu tố bên mua), bên mua (sau `Bên mua bảo hiểm:`), đối tượng (sau `Đối tượng bảo hiểm...:`), ngày ký. Dòng `Bên mua`/`Đối tượng` không có số hợp đồng thì gộp vào quyền lợi đang mở.
- `loai_tai_san` của văn bản: `Tài sản khác` (portal chưa có enum bảo hiểm — [CONFIRM]).

---

## 3. Quy trình thêm loại văn bản mới

Khi cần bổ sung thêm một loại văn bản mới vào hệ thống:
1. **Cập nhật catalog**: Thêm tên loại văn bản, marker tiêu đề, nhóm HĐ, quy tắc đương sự và tài sản vào file này.
2. **Khai báo `DOC_KIND_*`**: Khai báo hằng số trong `extract_contract.py`.
3. **Cập nhật hàm nhận diện**: Thêm rule vào `_detect_document_kind_and_title()`.
4. **Cập nhật hàm trích xuất**:
   - Nếu đương sự có cấu trúc mới $\rightarrow$ Bổ sung hàm parse đương sự và cập nhật `_fmt_duong_su_by_kind()`.
   - Nếu tài sản có marker đặc thù $\rightarrow$ Bổ sung `_find_tai_san_<kind>()` và tích hợp vào `_find_tai_san_by_kind()`.
5. **Thêm Unit Test**: Bổ sung test case vào `tests/test_upload_lab_extract_contract.py`.
6. **Chạy đối chiếu mẫu thực tế**: Đặt file vào `regex_review_samples/input/` và chạy `tools/review_regex_samples.py`.

## Future runtime LLM

Có thể nghiên cứu chế độ `regex` / `hybrid` / `llm` trả về span offsets có cấu trúc, không nhận free text. Mặc định phải tắt; khi timeout hoặc lỗi phải fallback về regex. Dữ liệu có PII nên chỉ được xử lý trong ranh giới bảo mật đã phê duyệt. Đây chỉ là ý tưởng, chưa triển khai runtime.

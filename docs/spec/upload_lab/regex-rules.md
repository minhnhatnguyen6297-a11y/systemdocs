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
- Trang phụ `Lời chứng chứng thực văn bản <loại>` (tiêu đề bắt đầu `Lời chứng`) chỉ chứng nhận chữ ký: nhận loại `generic` và áp luật `generic` — người ký vẫn được bóc, nhưng không đòi người chết/tài sản như loại trong tiêu đề (10/10/2026). Cùng cơ chế cho `Trang sửa lỗi kỹ thuật đính kèm` — trang phụ chỉ chép lại điều khoản sửa, quét trong 6 dòng đầu vì không thuộc tiền tố tiêu đề (11/10/2026) và `ĐÍNH CHÍNH <văn bản gốc>` — trang sửa lỗi nội dung đã công chứng, tên trích dẫn `“Bà X – Sinh năm/ngày”` vẫn bóc và gộp theo tên (ngày đầy đủ cùng năm thắng chỉ-năm — 11/10/2026); normalize `	 → \|`: regex cắt `|` đầu/cuối dòng viết deterministic `(?:\s*\|)+` — `\s*\|\s*` lặp trên chuỗi ~60 ô `|` gây backtracking mũ, treo engine (11/10/2026); `có N/một..mười người` là ranh giới tên (`Nguyễn Hữu Hoà có 03 người con` → `Hoà`).
- Dòng `|` có ô là tiêu đề mục văn xuôi `2. Thống nhất ...` (số + `.` + chữ) không phải dữ liệu bảng — bỏ trước khi vào `chi_tiet_dien_tich`/thửa "ma" (10/10/2026).

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
  - Không có heading `BÊN NHẬN THẾ CHẤP` thì phần mở đầu trước `BÊN THẾ CHẤP` (ngân hàng + đại diện, mẫu Lời chứng Agribank/VB sửa đổi) được coi là Bên B (11/10/2026).
  - Người yêu cầu công chứng: Người đại diện ngân hàng (Bên B).
- **Tài sản**:
  - Trích xuất thông tin thửa đất / GCN từ phần mô tả tài sản hoặc trích xuất tối thiểu `Quyền sử dụng đất`.

### 2.5. Văn bản phân chia di sản (`DOC_KIND_INHERITANCE_PARTITION`)
- **Nhóm HĐ**: `Thừa kế (khai nhận - phân chia di sản thừa kế )`
- **Tiêu đề canonical**: `Văn bản phân chia di sản`
- **Đương sự**:
  - Nhóm người ký ở phần mở đầu: `NHỮNG NGƯỜI HƯỞNG DI SẢN` (bắt đầu từ `Chúng tôi là những người được hưởng di sản...`; chấp nhận biến thể `Tôi là những người...`, mở đầu đơn `Người được hưởng di sản theo pháp luật ... là:`, `Người được hưởng di sản thừa kế của ...:`, `(Tôi/Chúng tôi) là người được hưởng di sản ...` + kết `Tôi/Chúng tôi tự nguyện lập Văn bản này`).
  - Tên người đứng sau `Ông`/`Bà` (kể cả dạng `1. Bà ...`, `Bà: ...`, `Ông/bà:` (giới tính để trống + R13, không suy qua `Thị`), `Người vợ - Bà: ...`, `Tôi là:/Tôi tên là: Bà ...` cùng dòng); người vợ ghi tên trần `Tên - Vợ ông X` vẫn tính 1 người, giới tính suy từ `Vợ`/`Chồng`. Vai trò số-hoá `N. <vai trò> - <danh xưng + tên>` mở rộng: `Con gái`/`Con trai`/`Cháu`/`Anh`/`Chị`/`Em`/`Đồng sử dụng`/`Đồng sở hữu` (cam kết đồng sở hữu, danh sách thừa kế tặng cho — 12/10/2026); `Ông ngoại`/`Bà ngoại`/`Ông nội`/`Bà nội`/`Cháu ngoại`/`Cháu nội` (hợp đồng tặng cho ông bà ngoại–cháu — 12/10/2026); giới tính suy từ `Con gái`/`Chị`→Bà, `Con trai`/`Anh`→Ông, `Cháu`/`Em`/đồng-sở-hữu để trống. Khi kiểm tra vai trò đầu tên phải ghép lại cả danh xưng bị tách riêng (`1. Ông ngoại – ông X` bị header bóc `Ông` làm danh xưng + `ngoại` làm tên nếu không ghép). `ho_ten` chỉ giữ họ tên (Owner 07/10/2026): cắt đuôi vai trò ` - Con đẻ ông X` lẫn dòng riêng `Là vợ/con của...`, không gộp vào tên. Tên cắt trước `|` (dấu căn dòng của `.doc`), trước nhãn ngày sinh (bắt buộc kèm giá trị ngày/năm, vì `Năm` là âm tiết tên hay gặp), trước `có vợ/chồng là`, trước `không` (câu "không có ai..."), trước nhãn giấy tờ (`CCCD`/`CMND`/`CC`/`Căn cước`/`Giấy`), trước nhãn địa chỉ/cư trú và ngoặc ngày sinh của người khác; bỏ cả dòng phả hệ (`Ông X có vợ là bà Y (Sinh ngày...)`); khối của 1 người dừng trước dòng `chết ngày`.
  - Vai trò đứng đầu dòng vẫn nhận người (09/10/2026): `Con đẻ - Bà X`, `Mẹ đẻ - Ông Y`, `Người chồng -`/`Người chồng:`, `Người vợ -`/`Người vợ:` (dấu `-`, `:` hoặc `là` — `2. Đồng sử dụng là ông X` — 12/10/2026; kể cả gạch `-` đầu dòng — `- Đồng sử dụng – ông X` (mẫu 18 HĐCN — 13/10/2026); kể cả tiền tố số `1. Người chồng –` — 11/10/2026; vai trò cũng có thể đứng liền tên chỉ cách khoảng trắng — `2. Cháu Lê Khánh Chi (con bà Nga)` → `Lê Khánh Chi`, `gioi_tinh` trống — 13/10/2026), danh sách tên trần sau `Chúng tôi gồm:`/`Chúng tôi là:` (văn bản cử người đại diện — 12/10/2026): mỗi dòng `<Tên> Sinh ngày:` không danh xưng vẫn là người, `gioi_tinh` để trống → R13; `Bên B: Bà X`, `Đại diện:`, `Người đại diện là Ông/Bà:` (danh xưng trước hai chấm — 11/10/2026), `Tôi (tên) là:` (dấu `:` không bắt buộc — `Tôi là ông X` cũng nhận), `Tôi Ông/Bà X` trực tiếp (`Tôi Ông Trần Văn Hương;` — 13/10/2026), `Tên tôi:` không `là` (`Tên tôi: Bà X;` — 13/10/2026); vai trò chỉ đi vào `gioi_tinh`/bỏ, không vào `ho_ten`; đuôi vai trò sau `-` cắt cả `cháu` (`Ông X – cháu nội bà Y` → `X`); tiền tố quan hệ 2 từ `Em trai/Chị gái/Anh rể/Cô dâu... - ông/bà X` cũng là vai trò (10/10/2026); nhãn `Sinh ngày:` (kể cả lỗi gõ `Sinh ng ày:` có khoảng trắng giữa — 13/10/2026)/`Sinh năm:` đều chấp nhận giá trị chỉ-có-năm (`Sinh ngày: 1982` → `ngay_sinh=1982` + `chi_co_nam_sinh`, tên cắt trước nhãn); `số:` trần (không nhãn CCCD) đi kèm 9–12 chữ số vẫn tính là giấy tờ của người (`Ông X số: 036070006771`, đơn xác nhận); số giấy tờ viết cách nhóm `0360 5800 1963` (3 nhóm 4 số) cũng nhận và chuẩn hóa bỏ khoảng trắng (13/10/2026); nhãn nơi cấp thêm `Nơi cấp <cơ quan>`; nhãn chức danh thêm `Chức danh:` (cạnh `Chức vụ:`); tiền tố `Người đại diện (theo pháp luật):` cũng mở dòng người (đại diện pháp luật công ty là người ký thật); R04 chỉ flag cụm nhãn rờ (`sinh ngày`, `sinh năm`, `ngày/năm sinh`, `cấp ngày`) — `Sinh/Năm/Cấp` đứng một mình là âm tiết tên hợp lệ (`Phạm Văn Sinh`, `Văn Năm`); dấu `:` cũng là ranh giới tên — `6. Ông Phùng Xuân Tính: phường Thành Nam` (đơn DK18) → tên `Phùng Xuân Tính`, phần sau `:` là địa chỉ (10/10/2026).
  - Ranh bên uỷ quyền (09/10/2026): heading `NGƯỜI UỶ QUYỀN:`/`NGƯỜI ĐƯỢC UỶ QUYỀN:` chỉ tính khi đi kèm `:`/`(` và dòng đó **không chứa người thứ 2** (hàng chữ ký `NGƯỜI UỶ QUYỀN    NGƯỜI ĐƯỢC UỶ QUYỀN` bị bỏ — nếu không sẽ cắt trắng toàn bộ người phía trên); `uỷ quyền cho:` inline đánh dấu bắt đầu bên được uỷ quyền. Heading thêm: `BÊN ĐẶT CỌC`/`BÊN NHẬN ĐẶT CỌC`, `NGƯỜI DI CHÚC:`, `NGƯỜI CAM KẾT:`, `BÊN GÓP VỐN`, `BÊN THỨ NHẤT`→A / `BÊN THỨ HAI`→B (10/10/2026 — góp vốn, thoả thuận); số La Mã cách heading bằng `|` do tab `.doc` (`I. | BÊN CHUYỂN NHƯỢNG`) vẫn nhận (10/10/2026); tiền tố La Mã chấp nhận cả gạch chéo `I/ BÊN ỦY QUYỀN`, `II/ BÊN ĐƯỢC ỦY QUYỀN` (mẫu ngân hàng — 11/10/2026).
  - Vùng đương sự **kết thúc tại khối ký/chứng thực** (12/10/2026): dòng `CHỨNG THỰC`, `NGƯỜI UỶ QUYỀN`, `NGƯỜI ĐƯỢC UỶ QUYỀN` đứng đầu dòng là ranh giới — danh sách người ký lại dưới `CHỨNG THỰC` (`1. Ông X; Căn cước...`) không nhập vào Bên B (mẫu giấy uỷ quyền UBND xã `uỷ quyền sổ.doc`).
  - Nhóm HĐ `guess_nhom_hd` so khớp trên text đã fold (09/10/2026): `GIẤY UỶ QUYỀN` (u+1EF7) và `ỦY QUYỀN` (u+1EE7) đều ra nhóm `Ủy quyền` — trước đây cách viết `uỷ` rơi về `Khác`.
  - Tổ chức không tính người: tên chứa `chi nhánh|công ty|ngân hàng|chi cục|UBND|bệnh viện` hoặc không viết hoa đầu từ → loại (09/10/2026); `văn phòng`/`phòng <đơn vị>` chỉ loại khi đứng **đầu** tên (`Văn phòng Công chứng`, `Phòng hành chính`) — `Trịnh Văn Phong` là tên người thật dù fold trùng `van phong` (13/10/2026). Dòng văn xuôi nhắc cặp vợ chồng (`Ông <tên> và bà <tên> có/là ...` — `Ông Gia và bà Mỳ có 6 người con`) cũng bị loại khỏi đương sự vì là lời kể, không phải hàng khai người (đơn xác nhận nhân thân — 13/10/2026). Hàng người đánh số **không** dấu chấm vẫn nhận khi số đứng ngay trước danh xưng có hai chấm (`1 Bà: Đặng Thị Thìn` — 13/10/2026). Cặp vợ chồng ghi chung một hàng danh sách `- Ông X và bà (Bà:)? Y` tách thành 2 dòng ảo — trường sau `và` thuộc người thứ hai, danh xưng lặp `bà Bà:` gộp về `Bà` (đơn xác nhận nhân thân ông Khải/bà Lan — 13/10/2026).
  - Địa chỉ chung cặp vợ chồng (`Cả hai ông bà cùng thường trú tại: X`, `Cả hai cùng thường trú tại: X`, `Tất cả ông bà cùng thường trú tại: X` — 13/10/2026) gán cho **cả hai** người trong khối (09/10/2026); khi chỉ có **một** dòng địa chỉ sau người mở bằng `Và vợ/chồng là` (không từ khoá `cả hai`), dòng đó cũng áp cho người liền trước còn thiếu (10/10/2026 — `Ông Thấu / Và vợ là bà Thanh / Nơi thường trú: Z`).
  - Dữ liệu người trong ngoặc `(Sinh ngày/CCCD/Thường trú...)` thuộc về vợ/chồng ghi kèm, **không** tính vào người đang xét — khối người được quét trên bản đã cắt ngoặc (10/10/2026, ca `Thông báo ông Giới`: ông đã chết đội CCCD của vợ); nhãn địa chỉ nằm trong ngoặc cũng bị bỏ.
  - Nhãn đánh số kiểu hành chính vẫn là người: `Người xin ...: <tên>`, `Tên người nộp thuế: <tên>` (đơn gia hạn, tờ khai thuế) — người chỉ có tên được giữ nguyên để R03 báo thiếu trường trung thực; đánh số `[04]` nhận như `4.`; nhãn giấy tờ `Số CMND/CCCD/Hộ chiếu ...:` (số ở dòng sau), `Ngày cấp:`, `Địa chỉ chỗ ở hiện tại:`, `Địa chỉ/trụ sở chính:` (10/10/2026). Thêm: `Tên tôi là:` (đơn xác nhận), `NGƯỜI NHẬN:`/`NGƯỜI GIAO:` (biên bản giao nhận — 10/10/2026); `Chị` + `Nhánh` bị loại vì là `Chi nhánh` tổ chức, và động từ `mang` trước từ giấy tờ cắt tên (`Ông X mang căn cước` → `X`). Nhãn `Họ và tên:` (tờ khai `[04]`) và `Ngày/tháng/năm sinh:` cũng nhận; địa chỉ ô con `[10.x] Tổ/thôn|Quận/huyện|...` gộp theo số nhãn cha `[10] Địa chỉ` — bỏ ô của nhóm khác như `[17.x]` địa chỉ thửa đất và phần đã chứa sẵn (11/10/2026).
  - Form lặp nguyên trang (DK18 in 2 mặt, biên bản in 2 lần): người trùng `ho_ten` gộp 1 bản ghi khi **không mâu thuẫn** CCCD/ngày sinh — cùng giá trị hoặc cả hai đều trống; hai người khác nhau cùng tên thường có giấy tờ khác nhau nên vẫn giữ riêng. Bản sau bổ sung trường thiếu (10/10/2026); địa chỉ dạng danh sách `- <Tên>: <địa chỉ>` cắt nhãn tên đầu dòng (10/10/2026). Đơn mẫu biến động đất đai (11/ĐK, 18) ghi người hai lớp: nhãn `Tên: <tên trần>; Sinh ngày:` không danh xưng + dòng giấy tờ đặt tên giữa nhãn `- Căn cước công dân ông <tên> số <id>`; `Tên:` cũng nhận khi sau nhãn là danh xưng thường + tab `Sinh ngày` (`Tên:  ông Hà Văn Tiễu 	Sinh ngày ...` — 13/10/2026); bỏ chữ `Tên` lặp thừa trong giá trị (`Tên: Tên  Ông X` → `Ông X` — 13/10/2026); danh xưng lặp dính trong tên (`là bà Bà Hoàng Thị Mỹ` → `Hoàng Thị Mỹ`, giới tính lấy từ danh xưng đầu — 13/10/2026) — hai bản cùng tên **gộp bổ sung** khi phía có CCCD đến từ dòng giấy tờ nêu tên người và bên kia có trường phân biệt riêng (ngày sinh); bản trống hết vẫn giữ riêng (cùng người 2 vai trò → R05 trung thực) (12/10/2026). Mục con `X.Y. Địa chỉ:` (`1.3.` của mẫu 11/ĐK) hoặc tiền tố chữ cái `c)`/`c.` Địa chỉ:` (mẫu 18) là địa chỉ **chung** của cả mục — điền cho mọi người chưa có `dia_chi`; kể cả khi marker `c)` bị dính vào cuối dòng trước (`...ngày 02/07/2021c) Địa chỉ:`) — nhận marker đứng ngay trước nhãn ở bất kỳ vị trí nào trong dòng (13/10/2026). Khi `c) Địa chỉ:` rỗng rồi đến từng dòng `Ông X: <địa chỉ>` / `Bà Y: <địa chỉ>` / `- <tên trần> : <địa chỉ>` / `Địa chỉ của ông/bà <tên gọi>:` (kể cả lỗi gõ `Địa chủ`, nhãn `Nơi thường trú của` hoặc `Nơi thường trú` trần không `của` (`Nơi thường trú ông Cường:` — 13/10/2026), `tại` đứng sau tên; khớp theo hậu tố của họ tên — âm tiết cuối hoặc cụm tên gọi nhiều âm như `bà Lan Anh` — mẫu 18, 13/10/2026) thì đây là địa chỉ **cá nhân theo tên**. Nếu dòng ngay sau nhãn rỗng là một địa chỉ trần (bắt đầu `thôn`/`xã`/`phường`/`số`/`tổ`/`khu`/`quận`/`thành`/`huyện`/`xóm`/`ấp`/`bản`/`đội`, không tên) thì nó là địa chỉ **chung** của mục (đơn DK18 — 13/10/2026) — gán đúng người trùng tên đã fold (mẫu 18 — 13/10/2026).
  - Ô nhãn danh xưng đứng một mình `Ông: <tên>`/`Bà: <tên>` (thành phần tổ định giá ngân hàng) vẫn là người dù không có trường nào khác; nhãn chức vụ trước danh xưng giữa dòng `Chức vụ: Ông X` cũng nhận (11/10/2026).
  - Danh sách đánh số tên trần sau `Chúng tôi là:` (đơn từ chối/cam kết nhiều người): `1. Trần Văn Cát   Sinh ngày: ...` nhận người khi cùng dòng có ngày sinh — không cần danh xưng; dòng `Căn cước/Thường trú` kế tiếp thuộc khối người đó (11/10/2026). Ranh giới tên trước `Chức vụ:` chấp nhận gạch dính liền `-Chức vụ` không khoảng trắng sau dấu (11/10/2026) và đuôi `- Chức vu`/`Chuc vu`/`Chuc danh` không dấu hoặc dấu lệch (`Đoàn Thế Vinh - Chức vu:Giám dốc` → `Đoàn Thế Vinh` — 12/10/2026). Ô trống chuẩn hoá `1. | Ông:` (`.doc` IFilter, ô STT trước ô danh xưng) vẫn nhận người — `|` sau số thứ tự được bỏ qua (11/10/2026).
  - Bảng hành chính dạng ô (`DANH SÁCH NGƯỜI SỬ DỤNG CHUNG` mẫu 04a/ĐK, `BIÊN BẢN HỌP HĐTV`): hàng `STT | Ông/Bà X | <các ô>` bóc theo ô — ô năm trần `(19|20)YY` → `ngay_sinh` chỉ-năm; ô 9–12 số → `cccd`; `do <X> cấp ngày` trong ô số → `noi_cap`/`ngay_cap_cccd`; ô ngay sau ô ngày cấp trần → `noi_cap`; ô có từ hành chính (`xã/huyện/tỉnh/thôn/tổ`, trừ `xã hội`) → `dia_chi`; bỏ ô nhãn cột (`CCCD`, `Chức vụ`, `Có mặt`, `Số`, `%`), ô `ngày … năm YYYY` chốt và đuôi `Người kê khai`; hàng không có ô số giấy tờ vẫn tính khi có ô chức vụ (`thành viên/chủ tịch/giám đốc/thư ký`) — người chỉ tên để R03 báo trung thực; ô không vượt `\n` nên hàng tự kết thúc trước hàng `N | Ông/Bà` kế (11/10/2026).
  - Mẫu bảng ngân hàng (`.doc` IFilter): ô `nhãn<TAB>:<TAB>giá trị` chuẩn hoá thành `nhãn: giá trị`; ô trống `| |` chỉ tách dòng ảo **trước** nhãn danh xưng `Ông:`/`Bà:`/... (người mới) — không tách trước nhãn thường như `Sinh ngày` để `Tôi tên là: X; | | Sinh ngày` vẫn đọc cùng dòng; tiêu đề bên viết liền `I. Bên thế chấp: Ông X` bị bỏ phần `BÊN ...:` đầu dòng; heading bên nhận cả viết hoa-thường (`(?i)`); `: | Ông X`, `+ Bà: X` nhận người; `có <quan hệ> là ông/bà Y` tách `Y` thành người riêng (đơn xác nhận nhân thân — 10/10/2026).
  - Tiền tố quan hệ + tham chiếu người chết: `Mẹ đẻ tôi: Bà Y`, `Bố đẻ ông X là bà Y`, `Con đẻ ông X là ông Y` — tiền tố gồm vai trò + `tôi`/`của tôi`/`ông <tên>` + `:`/`là` bị bỏ để lấy `Y` (10/10/2026). Ranh tên thêm `có` + số (`Thăng có 01 người con` → `Thăng`) và `-sinh` dính liền (`Hanh -sinh năm` → `Hanh`).
  - Dedupe theo tương thích `ngay_sinh`: `01/01/1932` vs `1932` (chỉ-năm trùng năm) là cùng người → gộp; hai ngày đầy đủ khác nhau hoặc khác năm → giữ riêng (danh sách lặp tóm tắt `Sinh năm` + chi tiết `Sinh ngày` — 10/10/2026). Khoá tên bỏ dấu (`fold`) nên hai người tên gần giống (`Vũ Thị Lanh`/`Vũ Thị Lành`) rơi cùng khoá — mỗi khoá giữ **danh sách** bản ghi và bản mới gộp vào bản đầu tiên không mâu thuẫn, nếu đụng nhầm sang bản của người khác-tên-nhưng-cùng-fold sẽ lọt bản tóm tắt thành trùng lặp giả (11/10/2026).
  - Nhãn địa chỉ bổ sung: `Địa chỉ:`, `Trú tại:`, `Địa chỉ thường trú:`, nhãn đánh số (`1.3. Địa chỉ:`), `N. Địa chỉ liên hệ (...):` (trường đơn mẫu 09 gia hạn — chỉ khi dòng mở đầu bằng số mục, vì `Địa chỉ liên hệ` trần thường là của cơ quan/văn phòng — 13/10/2026), `thường trú:`/`cư trú:` trần không `tại` (`Cả hai cùng thường trú:` — 13/10/2026; loại trừ `... cuối cùng` của người chết). Nhãn giấy tờ bổ sung: `CC số:`, `Căn cước công dân mới số:`, `Căn cước số công dân <id>` (thứ tự đảo, số liền sau không `số:` — 13/10/2026), `cấp ngày:` (có hai chấm), `cấp tại X ngày DD/MM/YYYY`, `do <cơ quan> ngày DD/MM/YYYY` (gõ thiếu `cấp` — `ký ngày` không tính) và `cấp:` trần ngay trước ngày (`nơi cấp: Cục ... cấp: 20/04/2023` — 13/10/2026); `//` kép gõ nhầm (`23/04//2021`) chuẩn hóa về `23/04/2021`; khi chunk có nhiều ứng viên ngày cấp thì lấy match **sớm nhất** để `do <cq> ngày` thắng `cấp ngày` của GCN liền sau (13/10/2026).
  - Người một dòng (`Bà ... - Sinh năm ..., CCCD số ..., ...; Nơi thường trú: ...`): địa chỉ lấy ngay trên dòng tên.
  - Ngày sinh 2 dạng: `Sinh ngày: DD/MM/YYYY` và `Sinh năm YYYY` (không dấu hai chấm cũng nhận). Quy ước owner 06/10/2026 (phương án 1): chỉ có năm thì `ngay_sinh` giữ đúng `YYYY` (không tự thêm 01/01), kèm cờ `chi_co_nam_sinh: true` để phân biệt với ngày đủ (nhận diện chắc vì luôn có nhãn `Sinh năm` đi kèm, không đoán số năm trôi nổi).
  - CCCD sau `Căn cước công dân số` / `Căn cước số` / `CCCD số` (kể cả `số:` dính hai chấm) hoặc `CCCD:`/`CC:` trực tiếp trước 6–12 chữ số không cần chữ `số` (mẫu ngân hàng `CCCD: 036078005311` — 11/10/2026); nơi cấp sau `do ... cấp ngày`, nếu thiếu `do` thì lấy cụm sau số giấy tờ; ngày cấp sau `cấp/ký ngày` hoặc `do <cơ quan> ngày DD/MM/YYYY` (nguồn gõ thiếu chữ `cấp`; `do <cơ quan> ký ngày` thì loại — đó là ngày ký giấy tờ khác, không phải ngày cấp CCCD — 13/10/2026); địa chỉ sau `Thường trú tại:` / `Cư trú tại:` / `Nơi thường trú:` / `Nơi thường trú tại:` / `Hộ khẩu (thường trú):` (kể cả giữa dòng sau `;`), cắt đuôi `Là vợ/con của...` và đầu người kế khi IFilter gộp dòng, trừ `Nơi thường trú cuối cùng trước khi chết` của người đã chết.
  - Dừng trước `Người để lại di sản:`, `Chúng tôi/Tôi tự nguyện lập Văn bản này`.
  - *Không đưa người để lại di sản, bố mẹ đẻ đã chết, phần kể phả hệ, người làm chứng trong Lời chứng vào danh sách đương sự. Người đã chết trích riêng ở `raw.nguoi_chet` (bắt buộc có `chết/đã chết ngày DD/MM/YYYY`), gồm tên gọi khác, năm sinh, trích lục khai tử, địa chỉ cuối. Điều kiện loại người chết trong khối đương sự là `chết ngày + ngày tháng` hoặc `chết năm YYYY` **ngay trên dòng tên** (12/10/2026 — `chết năm` trong khối thường là kể bố/mẹ đẻ chết, không phải người đang khai; vẫn trích riêng vào `nguoi_chet` khi đủ bằng chứng) (không loại khi chỉ có chữ `chết` chung chung). Cặp vợ chồng chết ghi chung 1 dòng (`Ông A và bà B; Sinh năm...; chết ngày...`) tách thành 2 bản ghi (09/10/2026); tên người chết là câu văn (từ thường, dấu câu, > 6 từ) bị loại và báo R04; khi cụm tên > 6 từ mà chứa danh xưng + tên hợp lệ ở cuối (`Ông X có mẹ đẻ là bà Y; chết ngày...`) thì lấy `bà Y` làm người chết thay vì bỏ hẳn (09/10/2026); tên trần sau `là` không danh xưng (`là Trần Văn Phúc, sinh năm..., đã chết ngày`) cũng nhận, `gioi_tinh` để trống không suy (11/10/2026); nhãn sinh của người chết cũng chấp nhận lẫn định dạng (`Sinh năm: 01/01/1948` → `ngay_sinh` đầy đủ; `Sinh ngày: 1948` → chỉ năm), kể cả không dấu (`Sinh nam`, `Ngay sinh`) (10/10/2026). Chấp nhận thêm `chết năm YYYY` (không ngày đầy đủ) **chỉ khi** ngay sau có `trích lục`/`khai tử`/`đơn xin xác nhận`/`đơn đề nghị`/`giấy xác nhận` (giấy UBND xác nhận đã chết — 11/10/2026; `đơn đề nghị`/`giấy xác nhận` do UBND xác nhận — mẫu khai nhận ông Nhiểm 12/10/2026) — trích lục khai tử là bằng chứng đây là người để lại di sản; `chết năm` trôi không giấy tờ vẫn bỏ để không hốt nhầm bố mẹ đẻ chỉ nhắc thoáng. Địa chỉ cuối nhận cả nhãn `Nơi thường trú trước khi chết:` không `cuối cùng`, cắt tại `;`/`.`/xuống dòng (11/10/2026); thêm biến thể `Nơi cư trú ... trước khi chết tại:` và `Cả hai có nơi cư trú cuối cùng trước khi chết tại:` — tiền tố `Cả hai` nghĩa là địa chỉ chung của cặp vợ chồng chết cùng dòng nên điền ngược cho người đứng trước (12/10/2026). Riêng văn bản **từ chối** nhận di sản: `chết năm YYYY` không trích lục vẫn được nhận khi trước tên có từ quan hệ (`Bố/Mẹ đẻ tôi là ông/bà X`, `vợ/chồng/con/cháu`) — cha/mẹ của người từ chối mặc định là người để lại di sản; các loại khác vẫn cần trích lục (11/10/2026).* Cụm `(sinh năm N, đã chết ngày D)` gộp trong ngoặc cũng là dấu hiệu người chết — tách riêng khỏi ngoặc alias (11/10/2026). Ngoặc cũng có thể lặp lại danh xưng + tên rút gọn trước ngày sinh (`ông Lương Văn Nguyên (ông Nguyên Sinh năm 1952; chết ngày ...)`) — tên đầy đủ ngoài ngoặc được giữ, không tạo người chết riêng từ phần lặp trong ngoặc; trích lục nằm trong ngoặc vẫn được đọc; tên người chết rút gọn còn 1 âm tiết (`Bà Yểng Sinh năm...`) được mở rộng thành tên đầy đủ kết thúc bằng âm tiết đó khi tên dài hơn xuất hiện ngay trước trong cùng đoạn (`bà Nguyễn Thị Yểng. Bà Yểng Sinh năm...` → `Nguyễn Thị Yểng` — 13/10/2026). Người đã vào `nguoi_chet` mà vẫn bị danh sách thành viên hộ/danh sách người kéo vào đương sự thì bị **loại khỏi bên** khi `ho_ten` fold-trùng **và** `ngay_sinh` tương thích không mâu thuẫn (bắt buộc có `ngay_sinh` ở bản đương sự — tránh giết nhầm người sống cùng tên như con trùng tên bố) (13/10/2026 — `Ông Bùi Văn Ngà` trong danh sách hộ gia đình, đã chết theo trích lục ở đoạn sau) `ho_ten` người chết tách danh xưng đầu (`Ông Nguyễn Văn Toản` → `Nguyễn Văn Toản`, danh xưng làm `gioi_tinh`) — hai lần nhắc cùng người gộp đúng và bản giàu địa chỉ hơn được giữ (13/10/2026).
- **Tài sản**:
  - *Điểm bắt đầu*: Sau heading `Di sản:` / `Di sản của ... để lại là:` hoặc dòng `quyền sử dụng đất ... có địa chỉ tại:` / `... tại địa chỉ:` / `Phần quyền sử dụng đất ... trong khối tài sản chung ...`; mở được cả khi địa chỉ đi thẳng sau `đất tại:` không nhãn (`có quyền sử dụng đất tại: Thửa đất số ...`) (10/10/2026).
  - *Điểm kết thúc*: Dừng trước `Người thừa kế:`, `Những người thừa kế`, `Những người nhận thừa kế` (kể cả `III. ...`, `III. | ...` của `.doc`), `Nội dung phân chia di sản`, `Bằng Văn bản này`, `Lời chứng`.
  - *Loại sổ (`loai_gcn`)*: cụm sau `Giấy chứng nhận` trước `số` (ví dụ `quyền sử dụng đất`).
  - *Tách thửa* (quyết định owner 05/10/2026, bổ sung 07/10/2026): mỗi thửa 1 dòng trong `raw.danh_sach_thua_dat` — dòng bảng/bullet nào có số thửa thì mở thửa mới (nhãn `Thửa đất số` hoặc `Số thửa`, `Tờ bản đồ số` — kể cả `Tờ bản đổ số`, `Tờ bàn đồ số` (chính tả `bàn` thay `bản`), `Tờ bản đồ:` không `số` (11/10/2026) và `Tờ bản đồ địa chính số` — hoặc `Số tờ`); dòng `Thửa đất số N` đứng đầu dòng (kể cả bullet `-Thửa đất số`) là neo khối tài sản khai nhận/phân chia; `theo “Giấy chứng nhận` chấp nhận ngoặc kép; nhãn `Địa chỉ thửa đất:`; `Những người thuộc hàng thừa kế`/`Nội dung khai nhận` là ranh giới kết thúc khối (11/10/2026); dòng `Trong đó` hoặc dòng ngắn không số thửa thì gộp vào `chi_tiet_dien_tich` của thửa đang mở (không ghi đè diện tích thửa); `trong đó` viết liền trên dòng diện tích tách từng vế theo `,`/`;` (dấu `,` kẹp giữa 2 chữ số là phần thập phân, không tách) — vế không nhãn `X:` như `diện tích chưa được cấp 89,4 m2 ONT` vẫn là 1 chi tiết (11/10/2026); một vế nhiều cặp `Nhãn: N m2` bắt hết (`Đất ở là 180 m2 Đất vườn: 20 m2` → 2 chi tiết); đuôi nhãn cắt trước `theo/tại/bản đồ/giấy/năm` (11/10/2026); trong bảng, bộ 3 ô số liền kề (tờ, thửa, tổng DT) sau `Trong đó` mở **thửa mới** thay vì gộp vào chi tiết thửa trước (`23\|32\|160\|Ao nuôi cá\|12/2043 (nay là...)` — 11/10/2026); `Diện tích` bỏ `(bằng chữ: ...)`, cắt phần thừa sau `,`/`;`/`trong`/`theo`, giá trị không có chữ số bị loại; `so_to_ban_do` chỉ giữ số/ký hiệu, cắt đuôi `Bản đồ địa chính năm ...` và đuôi marker mục kế (`20 b` → `20`, marker `b.` dính trước `Diện tích` — 13/10/2026); ô bảng `.doc` dạng `a) <Nhãn>: <giá trị>` (marker mục dính trong ô nhãn) vẫn gộp thành dòng bullet, kể cả ô mở bằng rác `;` (`;tờ bản đồ số:` — 13/10/2026); ghi chú `(tách/gộp từ thửa số N)` chấp nhận khoảng trắng sau `(` (`108 ( tách từ thửa số 99)` → thửa `108` + ghi chú — 13/10/2026); `Nguồn gốc (sử dụng đất)` → `nguon_goc`; dòng `Hiện nay là thửa đất số X; Tờ Y` là đánh số lại của cùng thửa → `phan_ghi_them`, không mở thửa; đuôi `Nay là thửa/tờ...` hoặc ngoặc nguồn `(được tách từ thửa N)` trong ô số thửa/tờ cũng vào `phan_ghi_them`, giữ ký hiệu đầu (09/10/2026); thửa cùng `so_thua_dat` + (cùng `so_to_ban_do` hoặc một bên trống tờ) lặp lại thì **gộp**: đổ trường trống, cộng dồn `phan_ghi_them`/`chi_tiet_dien_tich` vào bản ghi đầu (09/10/2026 — trước chỉ bỏ bản sau, mất dữ liệu nếu lần nhắc sau giàu hơn; IFilter cũng hay cắt `2067 được tách từ thửa X` thành 2 bản ghi cùng số); note nguồn bị cắt đoạn (`được tách từ` không kèm số) bị loại; số vào sổ cắt từ thừa; context GCN/địa chỉ/ngày cấp/cơ quan cấp copy vào từng thửa. `phan_ghi_them` cộng dồn (`; `), không ghi đè. Thửa "ma" — không có trường dữ liệu nào ngoài trường kế thừa context và không có chi tiết có `dien_tich` — bị loại (09/10/2026). Trường xe/tàu (`Số khung`, `Số máy`, `Số đăng ký`, `Nhãn hiệu`, `Biển số`, `Loại xe/tàu`, `Dung tích`, `Mã số`) và heading `Tài sản thứ N:` không tạo thửa (09/10/2026). Bullet `.doc` dạng `a|Thửa đất số: ...` (letter-prefixed) cũng là nhãn thửa. Dòng dữ liệu kiểu `04 Nay là tờ bản đồ 24 | 104 Nay là thửa đất số 321 | ...` không được nhận nhầm làm tiêu đề bảng. Khối đất mở được cả khi không có cụm địa chỉ mà chỉ có `... theo Giấy chứng nhận` (ví dụ `Quyền sử dụng đất mang tên Hộ ông ... 450 m2 đất theo GCN`). Serial chấp nhận `Đ` (`Đ 364866`). Dòng bảng liệt kê người (ô chứa `Sinh ngày/năm`, `CCCD`, `Hộ khẩu`, ô đầu `1. Ông/Bà ...`, cột `STT|HỌ VÀ TÊN|QUAN HỆ|THUỘC HÀNG THỪA KẾ`, hay ô đầu là STT kèm ô vai trò `Vợ|Con đẻ|Thứ nhất`) không vào `chi_tiet_dien_tich` (10/10/2026); nhãn tờ chấp nhận lỗi chính tả `Tờ bản đổ số`; văn bản chỉ mô tả đất ở mức GCN (`theo Giấy chứng nhận ... Số X do ... cấp ngày`) mà không có số thửa/tờ vẫn tạo 1 bản ghi giữ `so_gcn`/`dia_chi`/`co_quan_cap`/`ngay_cap_gcn` (10/10/2026). Mở khối tài sản chấp nhận `có địa chỉ:` (không bắt buộc `tại`) và `Phần quyền sử dụng đất ... là:` kết dòng bằng `là:` thay `địa chỉ tại:` (đơn từ chối kể lại di sản mẹ/bố để lại — 11/10/2026); ô bảng `.doc` bắt đầu `- Thửa đất số:`/`- Tờ bản đồ số:` (dấu gạch đầu ô) vẫn nhận nhãn (10/10/2026).
  - *Bảng `.doc` đọc bằng IFilter*: IFilter giữ ô bảng bằng TAB (code đổi thành ` | `, cắt `|` thừa đầu/cuối dòng do TAB thụt đầu dòng); bảng dồn 1 dòng thì tách theo dòng ô (ô `Số thửa` làm neo, hết `Phần ghi thêm` thì vào dữ liệu, gặp `2.2.`/chữ thường thì dừng).

  - *Bảng GCN 2 dòng cùng 1 thửa*: dòng chính ghi `muc_dich_su_dung` chính (VD `Đất ở` lâu dài), dòng phụ chỉ ghi phần diện tích còn lại (`160 | Đất vườn | 12.2043`) → tổng `chi_tiet` **nhỏ hơn** tổng thửa là hợp lệ (phần dư ngầm là mục đích chính); R10 chỉ báo khi tổng chi tiết **lớn hơn** tổng, hoặc thửa không có `muc_dich_su_dung` dòng chính (11/10/2026). Biến thể gộp 2 dòng vào 1 ô (`Trong đó 324,9 46,8 | Đất ở Vườn | Lâu dài 2043`): ô diện tích chứa nhiều số trần (không chữ) thì tách — số đầu giữ mục đích gốc, số sau thành chi tiết riêng để tổng khớp (11/10/2026).
### 2.6. Văn bản từ chối nhận di sản (`DOC_KIND_INHERITANCE_REFUSAL`)
- **Nhóm HĐ**: `Từ chối nhận di sản thừa kế`
- **Tiêu đề canonical**: `Văn bản từ chối nhận di sản`
- **Đương sự**:
  - Đơn phương 1 người (`Tôi là:`) hoặc tập thể (`Chúng tôi là:`, kể cả từ chối hưởng thế vị): `NGƯỜI TỪ CHỐI NHẬN DI SẢN`; cũng nhận form mở `Văn bản từ chối nhận di sản này được lập bởi` và dạng viết liền `Tôi là Vũ Đình Lân - Sinh năm ...` không danh xưng (10/10/2026) — kể cả khi chỉ ngăn bằng khoảng trắng/tab trước `Sinh` (`Tôi là: Nguyễn Thị Mơ<TAB>Sinh ngày`, đơn xác nhận). Nhãn mở đầu `Tôi là:`/`Chúng tôi là:` bị cắt khỏi `raw_text` hiển thị — `duong_su` bắt đầu bằng tên/danh xưng.
  - Tên người đứng sau `Ông`/`Bà`/`Anh`/`Chị` (kể cả `1. Chị ...`, `3. Anh ...`).
  - Dừng trước `Nay, tôi/chúng tôi tự nguyện lập Văn bản này`, `Theo quy định của pháp luật`.
  - *Người đã chết (`chết ngày...`) không vào danh sách đương sự*.
- **Tài sản**:
  - Hỗ trợ đơn tài sản hoặc đa tài sản (`1. Tài sản thứ nhất:`, `2. Tài sản thứ hai:`...); khối tài sản mở được cả khi chỉ ghi `Di sản của ông/bà X để lại là <mô tả>` không qua cụm `quyền sử dụng đất` (11/10/2026).
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

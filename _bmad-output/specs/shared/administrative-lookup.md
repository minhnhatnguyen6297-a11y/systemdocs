# Tra cứu địa chỉ — thao tác, luật tìm và kho lịch sử

**Cập nhật:** 15/10/2026. Một tài liệu cho toàn luồng. Tra kho cục bộ, trả tên hiện hành để người dùng Copy; không tự sửa hồ sơ. Các mốc đo/nghiệm thu dưới đây là lịch sử có nguồn, không phải kiểm lại trong lần gom docs.

<a id="usage"></a>
## 1. Dùng khi soạn hồ sơ

### 1.1. Công dụng và Tại sao?

Giúp chuyên viên đổi địa chỉ trên giấy tờ cũ sang tên xã/tỉnh hiện hành khi lập
hồ sơ. Máy chỉ trả kết quả để copy; người dùng tự quyết ghi gì vào ô.

### 1.2. Nơi gọi

| Ô | Chuỗi được tra |
|---|---|
| Địa chỉ Người | Nội dung ô địa chỉ của người đó |
| Địa chỉ Tài sản | Nội dung ô địa chỉ của tài sản đó |
| Nơi niêm yết | Nội dung chính ô Nơi niêm yết; không bắt chọn tài sản nguồn |
| Nơi cấp giấy khai tử | Địa chỉ của chính người đã chết; kết quả là xã mới để người dùng ghi nơi cấp |

Mọi ô dùng kiểu trình bày `drafting` (`xã Ý Yên, tỉnh Ninh Bình`), nút Tra bên
phải ô, kết quả bên dưới ô và copy được. Quá 10 kết quả → popup "Nhiều kết quả khớp. Xem đầy
đủ?", bấm đồng ý mới mở tool tra cứu dạng popup đè lên hồ sơ; đóng popup về
đúng chỗ cũ, không mất nháp đang nhập. Không cần ngày cấp giấy hay
`ngay_lap_ho_so`. *Tại sao:* lõi chỉ trả bước cuối (Owner 05/10).

### 1.3. Quy tắc riêng của hồ sơ

- Máy không ghi, đè hay nối `(nay là …)` vào ô hoặc Stage. Người dùng dán/sửa
  tay rồi lưu như mọi chỉnh sửa khác; lưu metadata dùng revision hiện hành,
  xung đột không ghi đè cưỡng bức.
- Không tự sửa thôn, số nhà hoặc chi tiết ranh giới.
- Nơi cấp giấy khai tử: tra xã mới từ địa chỉ của người đó, không phụ thuộc
  ngày (Owner 05/10/2026). Máy vẫn không tự ghi; người dùng copy và sửa nếu
  giấy ghi khác. Quy tắc nơi cấp giấy tờ người sống theo MIN-141 vẫn độc lập.
- Không gửi địa chỉ khách hàng ra website; chỉ đọc kho cục bộ.

### 1.4. Bản cài

Bản cài cần helper, schema và đúng ledger/snapshots công khai. Không đóng gói
database văn phòng, cấu hình riêng, khóa ghi hoặc archive lịch sử của người
quản lý. Nâng cấp định dạng kho theo migration của
spec timeline.

### 1.5. Luồng giao diện của TASK-4

#### Chuỗi tra và nội dung đang nhập

- Khi bấm Tra, lấy đúng chữ đang hiện trong ô nguồn, kể cả phần chưa lưu;
  không lấy lại giá trị cũ từ Stage. Nơi cấp giấy khai tử dùng ô địa chỉ của
  chính người chết như bảng Nơi gọi; không dùng chữ đang nhập trong ô nơi cấp.
- Gửi `{query, presentation: "drafting"}`. Không gửi ngày, tỉnh/xã tách sẵn,
  `case_id` hay `base_revision`. Tra cứu không phải thao tác lưu hồ sơ.
- Gắn mỗi lần tra với hồ sơ, người/tài sản, ô đích và chuỗi nguồn lúc bấm.
  Đổi một trong các giá trị đó khi đang chờ thì bỏ phản hồi cũ. Lần tra sau
  không được bị kết quả của lần tra trước ghi đè. Đặc biệt, đổi địa chỉ người
  chết làm kết quả nơi cấp khai tử đang chờ hết hiệu lực.
  Đổi từ A sang B rồi quay lại A cũng không làm phản hồi cũ của A hợp lệ lại.
- Người dùng được tra lại cùng chuỗi bằng nút Tra; không giữ luật chặn chuỗi
  không đổi của giao diện cũ (spec lõi mục 11).

#### Phản hồi và cửa sổ tra cứu

| Phản hồi | Hành vi |
|---|---|
| Đang tra | Báo đang tra tại vùng thao tác; không tự ghi vào ô |
| `found` | Hiện đủ `results[].display`; người dùng copy rồi tự dán/sửa |
| `not_found` | Báo không tìm thấy; không suy đoán hoặc hiện kết quả cũ |
| `invalid_input` | Báo đầu vào không hợp lệ; cho người dùng sửa rồi bấm Tra |
| `reload_failed` | Báo không đọc được kho cục bộ; không thay bằng kết quả từ bản kho cũ |
| `too_many` | Không hiện dòng nào; hỏi đúng câu “Nhiều kết quả khớp. Xem đầy đủ?” |
| Lỗi gửi lệnh/nhận phản hồi | Báo lỗi tại vùng tra; giữ nguyên nháp, cho bấm Tra lại |

Đồng ý câu hỏi `too_many` mới gửi lại **đúng chuỗi đã tra** với
`presentation: "full"`; không lấy một chuỗi khác vừa sửa trong ô. Nếu hồ sơ,
ô hoặc chuỗi nguồn đã đổi, bỏ yêu cầu cũ, người dùng bấm Tra lại. Hủy câu hỏi
không gọi `full` và trở lại chỗ soạn thảo.

Cửa sổ full hiện toàn bộ kết quả, gồm cả xã và tỉnh theo đúng thứ tự lõi trả;
không cắt còn 10 dòng, không tự lọc tỉnh khỏi kết quả nơi cấp khai tử. Người
dùng chọn dòng phù hợp để copy. Giữ riêng các dòng nguồn khớp, kể cả cùng
`unit_id` hoặc `display`; không chọn/gộp hay báo lỗi vì có nhiều dòng.

**Bố cục đã chốt:** ô tìm kiếm sửa được và nút Tra ở trên; danh sách cuộn ở
dưới, mỗi dòng có Copy; có nút Đóng. Mở lần đầu sau xác nhận dùng đúng query
vừa tra. Sửa query trong cửa sổ không sửa ô hồ sơ và không tự tra; bấm Tra
mới gửi query mới với `presentation: "full"`. Mỗi dòng full hiện nguyên đoạn
nguồn tương ứng để người dùng phân biệt và chọn. *Tại sao:* thao tác ngay
bên ô đang sửa; tra thêm trong cửa sổ mà vẫn giữ nguyên nháp hồ sơ (Owner 05/10).

#### Giữ nháp và vị trí đang sửa

- Cửa sổ full phủ lên màn hình hồ sơ đang mở; không điều hướng sang module
  khác, không nạp lại hồ sơ, không gọi lưu hoặc reset form khi mở/đóng/copy.
- Ghi nhớ ô đang sửa và vị trí con trỏ/vùng chữ được chọn trước khi nút Tra
  lấy focus. Giữ nguyên chữ đang nhập, nháp chưa lưu và vị trí cuộn.
- Chỉ một hộp thoại của luồng tra cứu tại một thời điểm: đóng câu hỏi trước
  khi mở cửa sổ full. Giữ thao tác bàn phím trong hộp thoại; Esc, nút × hoặc
  Đóng đều đóng và trả về vị trí đang sửa. Áp dụng
  [quy tắc dialog chung](../ui/README.md), với yêu cầu riêng của tính năng
  này là khôi phục con trỏ trong ô đang sửa trước khi bấm Tra, thay vì chỉ
  focus nút mở. Ô lấy chuỗi để tra và ô trả focus có thể khác nhau: Tra nơi
  cấp khai tử đọc địa chỉ người chết nhưng không ép focus sang ô địa chỉ đó.
- Copy không tự đóng cửa sổ, không sửa dữ liệu hồ sơ. Copy lỗi phải báo rõ;
  không báo đã copy khi thao tác clipboard thất bại.

<a id="lookup"></a>
## 2. Luật tra cứu dùng chung

### 2.1. Công dụng và Tại sao?

Trả lời một câu: **tên xã/tỉnh người dùng gõ (cũ hoặc mới) nay là đơn vị nào,
gồm những đơn vị cũ nào.**

| Việc | Người dùng có | Cần nhận | Tần suất |
|---|---|---|---|
| A | Địa chỉ cũ đủ xã/huyện/tỉnh | Tên hiện hành | ~85% |
| B | Chỉ tên xã cũ (đã biết tỉnh mới) | Tên xã hiện hành, một lần tra | ít |
| C | Tên xã mới | Các xã cũ đã gộp/tách thành nó | ít |

Không làm: suy đoán, sửa ô nhập, tra thôn, tra huyện, dựng lịch sử.

**Tại sao dùng chung:** ô địa chỉ khi soạn hồ sơ, tool tra cứu riêng và module
khác về sau cần cùng một câu trả lời. Một luật + một kho → không lệch giữa các
nơi. Đây là ngoại lệ có chủ ý của luật "chưa tạo shared core khi chưa đủ hai
consumer" tại [spec hệ thống](data-rules.md#tách-và-dùng-chung).

### 2.2. Nguyên lý

1. **Chỉ phản ánh DB.** Có dữ liệu → xuất; không có → không có. Engine không
   suy cấp, không đoán đơn vị, không ghép lịch sử. *Tại sao:* gợi ý sai mất
   lòng tin hơn nhiều gợi ý đúng; quan hệ tách/gộp/tách-gộp liên tục là việc
   của kho, không của engine.
2. **Chỉ đúng hoặc sai.** Đúng = ít nhất một kết quả. Sai = không trả gì; không
   trả nửa kết quả kiểu "đã hiểu tỉnh X, chưa hiểu cụm Y". *Tại sao:* nửa kết
   quả dễ bị chép như kết quả thật.
3. **Không cần ngày.** Không có `source_date`/`target_date`. *Tại sao:* lõi chỉ
   trả bước cuối; bắt ngày đang chặn ca chỉ gõ tên xã (DC-01) và khiến máy đoán
   cấp theo ngày (DC-04).
4. **Tiêu chí hoàn thành = đúng bước cuối:** đơn vị hiện hành và các đơn vị liền
   trước nó. Phủ ~90% ca. Không cố truy lịch sử nhiều đời.

### 2.3. Cấp được tra

| Cấp | Tra? | Tại sao |
|---|---|---|
| Xã/phường/thị trấn, cũ và mới | Có | Trục chính, khó tra nhất |
| Tỉnh, cũ và mới | Có | Cùng dạng kết quả với xã |
| Huyện | Không có đơn vị cấp huyện trong kết quả | Kho không có danh mục huyện; Bando chỉ ghi huyện trong ngoặc — nhưng cụm `quận Hà Đông` vẫn khớp đoạn gốc của xã/tỉnh và in ra các xã đó (mục 7) |
| Thôn/xóm | Không | Chưa có dữ liệu tổng hợp |

### 2.4. Dữ liệu dùng

Nguồn duy nhất: kho timeline (owner
dữ liệu hiện là `notary_v2`). Mỗi đơn vị hiện hành dùng: tên chính thức có tiền
tố, tỉnh cha (với xã), **đoạn chữ gốc "sáp nhập từ" của Bando nguyên văn**, ID
dòng nguồn, `dataset_version`, `revision`.

**MVP tra thẳng trên tên + đoạn chữ gốc; không tách đoạn chữ thành từng xã cũ.**
*Tại sao:* Bando chỉ lưu xã mới thành trường; xã cũ là một đoạn văn kèm ghi chú
như `(quận Hà Đông)`, `(phần còn lại sau khi sáp nhập vào phường Đại Mỗ)`. Tách
dễ sai; đoạn gốc đã tự nói gộp toàn bộ hay một phần.
Owner chấp nhận: cụm có thể khớp vào ghi chú trong ngoặc, ví dụ `phường Đại Mỗ`
ra cả dòng phường Hà Đông.

Tỉnh cũ nằm trong đoạn chữ của tỉnh mới, nên `tỉnh Nam Định` có thể khớp dòng
tỉnh Ninh Bình. Đây là một dòng kết quả độc lập, không giới hạn phạm vi tra
các cụm khác vào tỉnh đó (mục 7). Không cần bảng tỉnh cũ riêng.

Kết quả phải cùng một phiên bản kho: tên trả về lấy từ đúng bản đang hoạt động
(DC-08 là lỗi hiện có, ngoài luật tra). Kho mới lỗi → báo lỗi kho, không trả
kết quả cũ dưới nhãn mới. Bổ sung/sửa lịch sử theo spec timeline.

**Nhiều dòng nguồn:** trong bản dữ liệu đang hoạt động, một đơn vị có nhiều
dòng nguồn thì tra và trả từng dòng khớp, giữ nguyên đoạn chữ và bằng chứng
của dòng đó. Không chọn hộ, nối các đoạn nguồn hay báo lỗi chỉ vì có nhiều
dòng. *Tại sao:* đây là công cụ truy vấn kho; người dùng xem dữ liệu và tự
chọn (Owner chốt 05/10/2026).

### 2.5. Chuẩn hóa đầu vào

- **Tách cụm** theo `,` và `-`. Bỏ cụm rỗng.
- **Viết tắt:** danh mục cố định chỉ đổi viết tắt → tiền tố đầy đủ: `X.`→Xã,
  `P.`→Phường, `TT.`→Thị trấn, `TP.`/`TP`→Thành phố, `H.`→Huyện, `Q.`→Quận,
  `TX.`→Thị xã. Danh mục thêm mục = sửa spec.
- **Giữ tiền tố đầy đủ** (`xã`, `phường`, `thị trấn`, `tỉnh`…). *Tại sao:* tiền tố
  là một phần tên chính thức trong DB. Giữ nó thì `xã Yên Bình` không lẫn
  `Phường Yên Bình` (DC-02), `thôn Yên Bình` không khớp `Xã Yên Bình`.
  `Thị trấn Lâm` → ít kết quả; `Lâm` → hàng trăm.
- **Hoa/thường:** không phân biệt.
- **Unicode:** chuẩn hóa NFC trước khi so để hai cách mã hóa cùng một chữ có
  dấu cho cùng kết quả (ví dụ chữ `ế` dựng sẵn và chữ ghép dấu).
- **Dấu:** cụm có dấu → so có dấu. Cụm hoàn toàn không dấu → bỏ dấu phía DB rồi
  so (`yen binh` ra cả `Yên Bình`, `Yến Bình`); ở phép so không dấu, đổi `đ`/`Đ`
  phía DB thành `d`/`D`. Phép so có dấu giữ phân biệt `d` và `đ`.
  Xác định có dấu từ cụm người dùng nhập sau NFC, trước khi mở rộng viết tắt;
  chữ có dấu do máy thêm (`P.` → `Phường`) không đổi cách so của đầu vào.
  Ví dụ `P. yen binh`: mở rộng tiền tố rồi so hai phía ở dạng không dấu.
- **Số:** không quy đổi `1`/`01`/`I`. DB ghi ký tự nào thì tìm ký tự đó; sai thì
  người dùng gõ lại.

### 2.6. Luật khớp

Cụm sau chuẩn hóa phải **nằm nguyên vẹn, liên tiếp, đúng thứ tự** trong tên hoặc
đoạn chữ gốc. Không chèn, không cắt ký tự.
So riêng từng trường: không nối tên với đoạn chữ gốc để tạo một chuỗi khớp
vắt qua ranh giới hai trường. *Tại sao:* một cụm như vậy không nằm trong tên
hay đoạn nguồn nào như luật đã chốt.

| Gõ `yên bình` | Khớp? |
|---|---|
| `Xã Yên Bình`, `Phường Yên Bình`, `Xã Yên Bình Đông` | Có |
| `Xã Bình Yên`, `Xã Yên Thịnh Bình` | Không |

Tên thật có `-` (`Bà Rịa - Vũng Tàu`) bị tách thành hai cụm; `Vũng Tàu` vẫn khớp
tên đầy đủ. Mảnh còn lại nếu khớp đơn vị khác thì thêm dòng, người dùng tự chọn.

### 2.7. Flow — mọi cụm tra độc lập

Engine không phân biệt vị trí hay vai trò của cụm. Dán một đoạn địa chỉ cũ
(thôn, xã, huyện, tỉnh) hay gõ một tên lẻ đều chạy cùng một luật:

1. **Mỗi cụm** so với các dòng **xã** (tên + đoạn chữ gốc) trên **toàn quốc**
   bằng đúng luật khớp mục 6; gom mọi dòng khớp. Một dòng khớp nhiều cụm chỉ
   xuất hiện một lần; các dòng nguồn khác nhau của cùng đơn vị vẫn giữ riêng.
2. **Mỗi cụm** cũng so với các dòng **tỉnh** (tên + đoạn chữ gốc); mọi tỉnh
   khớp in một dòng riêng, **kể cả** khi tỉnh đó đã là tỉnh cha của một xã
   trong kết quả.
3. **Không có luật bỏ qua theo tiền tố, không có phạm vi tỉnh.** Cụm
   `huyện Ý Yên` được tra như mọi cụm — khớp đoạn gốc chứa `(huyện Ý Yên)`
   thì in các xã từng thuộc huyện đó. `quận Hà Đông` → các phường Hà Đông,
   Kiến Hưng… *Tại sao:* engine chỉ phản ánh kho; một luật nhất quán ít lỗi
   hơn ngoại lệ; nhiễu đã có luật >10 của mục 8 lo (Owner 05/10, thay luật
   "đọc phải→trái, cụm cuối khoanh phạm vi tỉnh, bỏ qua cụm huyện").
4. 0 kết quả → **sai**.

Thứ tự hiển thị: các dòng xã trước, các dòng tỉnh sau; trong mỗi nhóm theo
thứ tự kho. Gõ `Yên Bình, Ý Yên, Nam Định` → xã Ý Yên + dòng chứa Xã Yên
Bình + `tỉnh Ninh Bình`; người dùng chọn.

### 2.8. Kết quả

**Lõi luôn trả đủ dữ liệu có cấu trúc** (mục 4). Nơi gọi chỉ chọn **kiểu trình
bày**; lõi không biết feature nào gọi. *Tại sao:* thêm nơi gọi không sửa lõi.

| Kiểu | Nơi dùng | Dạng mỗi dòng |
|---|---|---|
| `full` | Tool tra cứu riêng | `Xã Ý Yên = <đoạn chữ gốc>, Tỉnh Ninh Bình` |
| `drafting` | Trình soạn thảo | `xã Ý Yên, tỉnh Ninh Bình` |

- Mỗi dòng kết quả gắn với một đơn vị **hiện hành** và một dòng nguồn. Cùng
  `unit_id` có thể xuất hiện nhiều lần khi có nhiều dòng nguồn khớp; mỗi dòng
  giữ `observation_id`, `source_text`, `evidence` riêng. Đơn vị không có đoạn
  nguồn vẫn có thể khớp tên và trả một dòng với `source_text: null`.
- Bỏ lặp theo cùng dòng `(unit_id, observation_id)` khi nhiều cụm cùng khớp;
  không bỏ dòng chỉ vì tên, `unit_id` hoặc `display` giống nhau. Không có
  observation thì dùng một dòng tên của đơn vị. Thứ tự các dòng nguồn cùng
  đơn vị theo thứ tự trong kho. `total` đếm **dòng kết quả**, không đếm số
  `unit_id` khác nhau; ngưỡng 10 áp dụng theo số dòng này.
- Với `full`, mỗi dòng hiện đúng đoạn nguồn của nó để người dùng chọn.
  `drafting` giữ dạng ngắn đã chốt, kể cả khi hai dòng có cùng `display`.
- Tra tên mới hay tên cũ đều cùng dạng; không gắn nhãn chiều cũ→mới.
- `drafting`: danh từ chung (`xã`, `phường`, `tỉnh`…) viết thường, tên riêng viết
  hoa, theo thể thức NĐ 30/2020. Owner bỏ bước xác minh văn bản gốc (05/10).
- `drafting` quá **10** kết quả → không hiện dòng nào; hiện popup
  **"Nhiều kết quả khớp. Xem đầy đủ?"**. Người dùng bấm đồng ý mới mở tool tra
  cứu (`full`) với cùng chuỗi; bấm hủy thì ở lại ô soạn thảo.
- Tool tra cứu mở dạng **popup đè lên màn hình đang làm**, không chuyển màn
  hình. Đóng popup → về đúng chỗ cũ; nội dung đang nhập, nháp chưa lưu, vị trí
  con trỏ giữ nguyên. Copy từ popup rồi dán vào ô như bình thường.
- *Tại sao:* danh sách dài không đọc được ở ô soạn thảo; hiện 10 dòng đầu là
  nửa kết quả; chuyển màn hình làm mất việc người dùng đang làm dở (Owner 05/10,
  thay quyết định "chuyển thẳng").

### 2.9. Thao tác — mọi nơi gọi

- **Chỉ tra khi người dùng bấm nút Tra.** Không tự tra khi gõ, dán, rời ô, trỏ
  chuột hay mở hồ sơ. *Tại sao:* tra tự động trả kết quả liên tục, lệch với
  thao tác, mỗi lần nhìn một khác; bấm nút thì không có truy vấn thừa.
- **Kết quả copy được; máy không tự ghi, đè hay nối `(nay là …)` vào ô.**
  Người dùng tự quyết. Đây là câu trả lời Q3 của báo cáo điều tra cho phần tra
  cứu.
- Phản hồi về khi chuỗi/ô đã đổi → bỏ.
- Chỉ đọc kho cục bộ; không gửi địa chỉ khách hàng ra website.

### 2.10. Ví dụ đầu vào → cách hiểu

Ví dụ minh họa luật; kết quả thật phụ thuộc dữ liệu kho.

| Gõ | Máy hiểu | Trả |
|---|---|---|
| `xã YÊn Bình` | 1 cụm → toàn quốc | Mọi đơn vị hiện hành có tên/đoạn gốc chứa `xã yên bình`; chỉ thêm dòng tỉnh nếu chính dòng tỉnh khớp |
| `Yên Bình` | Không tiền tố → cả xã, phường, `Yên Bình Đông`… | Nhiều dòng; `drafting` >10 → popup "Nhiều kết quả khớp. Xem đầy đủ?" |
| `yen binh` | Không dấu → so bỏ dấu | Thêm `Yến Bình`… |
| `P. Yên Bình` | `P.` → `Phường` | Chỉ dòng chứa `phường yên bình` |
| `tỉnh Nam Định` | Khớp đoạn gốc tỉnh Ninh Bình | `tỉnh Ninh Bình` |
| `huyện Ý Yên` | Cụm thường → khớp `(huyện Ý Yên)` trong đoạn gốc | Các xã từng thuộc huyện Ý Yên |
| `quận Hà Đông` | Như trên | Các phường từng thuộc quận Hà Đông |
| `xã Yên Bình, tỉnh Nam Định` | Hai cụm tra độc lập | Mọi Xã Yên Bình toàn quốc + dòng `tỉnh Ninh Bình` |
| `Thôn A, xã Yên Bình, huyện Ý Yên, tỉnh Nam Định` | Bốn cụm tra độc lập; `Thôn A` không khớp | Như dòng trên + các xã thuộc huyện Ý Yên (có thể >10 → popup) |
| `Yên Bình, Ý Yên, Nam Định` | Ba cụm độc lập | Xã Ý Yên + dòng chứa Xã Yên Bình + `tỉnh Ninh Bình` |
| `Phường 01` | Không quy đổi | Chỉ khớp nếu DB ghi `01` |
| `abc, xyz` | Không cụm nào khớp | Sai |

### 2.11. Phạm vi MVP (MoSCoW, Owner chốt 05/10)

- **Must:** mục 2–9, gồm tool tra cứu riêng dạng `full` (Owner chuyển từ
  Should 05/10 vì luật >10 của `drafting` cần nơi để chuyển tới).
- **Could:** nút "Chi tiết" hiện JSON/timeline lịch sử nhiều đời khi kho có;
  thêm ký tự ngăn cách dự phòng ngoài `,` `-`.
- **Won't (lần này):** tra huyện → tỉnh; dữ liệu thôn; tách đoạn gốc thành
  trường riêng; tự tra khi gõ/bong bóng gợi ý; chặn tra lại chuỗi không đổi.

### 2.12. Mốc triển khai và giới hạn bằng chứng

Runtime đã chuyển sang `notary.address-lookup.v2`: payload `query` +
`presentation`, mọi cụm tra độc lập vào xã và tỉnh trên toàn quốc, mỗi
dòng nguồn khớp trả riêng để người dùng chọn, không tự tra/không tự
ghi/không nối `(nay là …)`. Schema v1
(`address-lookup.schema.json`) đã xóa; contract §14 và
[schema v2](../../../contracts/notary-case-drafting/address-lookup.v2.schema.json)
là SOT. Renderer đã có nút Tra và overlay full của TASK-4; không tự tra
hoặc áp dụng kết quả. Ghi chép nghiệm thu 06/10 được giữ bên dưới; lần gom docs này không chạy lại chương trình.

Lịch sử: runtime từng trả v1 (bắt hai ngày, tách xã+tỉnh, `coverage`,
bỏ tiền tố khi so, đoán cấp theo mốc 01/07/2025, tách tên cũ bằng regex,
nối `(nay là …)`, renderer chỉ gửi khi đủ địa chỉ + hai ngày) → trái mục
2, 7, 8; đã thay toàn bộ tại TASK-3.

Ghi chép trong spec về kiểm tra độc lập 05/10/2026 cho biết đã tìm thêm 2 lỗi
lõi và sửa xong: raw khớp nhiều observation chỉ trả dòng
đầu (R1); tên/tỉnh cha lấy bản ghi cũ nhất thay vì đúng version (R2).
Sau sửa: kiểm importer thật hai snapshot (đổi tên + tỉnh cha), raw khớp
2/11 dòng, ngưỡng `too_many` đếm dòng — pytest 211 pass/3 skip.

Review tiếp tìm lỗi đơn vị đã mất khỏi catalog mới, thứ tự dòng nguồn và
xã thiếu tỉnh. Đã sửa/kiểm lại 06/10: ID phiên bản importer phân biệt lịch sử
với đơn vị tên-only hợp lệ; xuất nguồn theo thứ tự kho; không phát found sai schema.
*Tại sao:* đáp ứng mục 4, 7, 8 và contract hiện có; không thêm luật tra.
Python 294 đạt/2 bỏ qua symlink, npm 403 đạt, examples 82/0; kiểm bỏ sửa
trong bộ nhớ bắt lỗi cũ. Producer frozen với kho public và component Word
trên Electron thật đã kiểm, gồm full 3.001 dòng, clipboard và lỗi snapshot.
Các kết quả và số liệu nghiệm thu trên được giữ lại như ghi chép trong spec.
[Danh sách tên file gốc đã dọn](../../archive/removed-agents-files.md)
không chứa nội dung báo cáo hoặc review.

### 2.13. Còn mở

- Mở rộng danh mục viết tắt hoặc ký tự ngăn cách ngoài danh mục cố định mục 5
  là việc sau MVP; không phải điều kiện chặn TASK-3.
- Bố cục TASK-4 đã chốt tại spec nơi gọi.
- Contract cho module ngoài `notary_v2` gọi lõi.
- Nguồn dữ liệu huyện (Won't hiện tại).
- `drafting` >10: vì kết quả giờ gồm cả các cụm huyện khớp, ca dán địa chỉ cũ
  đầy đủ dễ vượt 10 → popup/tool phải đọc được số lượng lớn.

### 2.14. Lịch sử

Owner 05/10/2026 chốt nhiều dòng nguồn: “in dữ liệu ra, chọn dòng nào là việc
của user”, vì đây là tool truy vấn database. Thay đề xuất báo lỗi kho và
quy tắc bỏ trùng theo đơn vị: giữ các dòng nguồn khớp riêng, chỉ bỏ cùng dòng
bị tìm thấy lặp lại qua nhiều cụm. Không thêm cơ chế xét đúng/sai giữa các nguồn.

Owner 05/10/2026, sau khi quan sát hành vi Bando (`quận hà đông` ra các xã
từng thuộc quận; `phường linh đàm, tỉnh nam định` trả xã và tỉnh độc lập),
thay mục 7: bỏ luật đọc phải→trái, bỏ phạm vi tỉnh và luật bỏ qua cụm huyện;
mọi cụm tra độc lập vào xã lẫn tỉnh, tỉnh khớp luôn in dòng riêng. Lý do:
luật nhất quán, ít lỗi hơn; tiền tố huyện chỉ là chữ trong đoạn gốc.

Owner 05/10/2026 thay các quy tắc Draft cũ tại
`notary_v2/administrative-address.md`:
bắt ngày giấy/ngày lập hồ sơ, bắt xã+tỉnh, nối `(nay là …)` khi áp dụng, gợi ý
nơi niêm yết theo tài sản nguồn. Bằng chứng lỗi: mục 5 của
ghi chép trong spec về điều tra 04/10; danh sách tên file gốc đã dọn được giữ tại
[removed-agents-files.md](../../archive/removed-agents-files.md), không chứa báo cáo điều tra.

<a id="timeline"></a>
## 3. Kho tên và lịch sử hành chính

### 3.1. Công dụng và Tại sao?

Owner chọn [Bando](https://sapnhap.bando.com.vn/) làm nguồn tên xã/tỉnh hiện hành
và mô tả lần chuyển đổi gần nhất. Owner sẽ cung cấp lịch sử cũ hơn sau; đợt này
không tìm hoặc đoán thêm nghị quyết. Kho lưu được cả xã, huyện, tỉnh, nhiều lần
đổi tên, sáp nhập, chia tách, chuyển nơi quản lý hoặc bỏ đơn vị.

Tên giống nhau chưa chứng minh cùng một nơi; mã có thể được dùng lại. Mỗi đơn
vị có `id` nội bộ ổn định; tên/mã/nơi quản lý là các bản ghi riêng theo thời gian.
Đổi tên A→B→C→D có thể vẫn là **một** đơn vị. Sáp nhập A+B→C có nhiều đầu vào;
C→D+E có nhiều đầu ra. Lịch sử không bắt buộc chỉ có một đường.

Ngày tải website không phải ngày có hiệu lực. Bando có cả cập nhật 2026; không
gán chung 01/07/2025. Ngày thiếu nguồn giữ `null`, trạng thái `pending` (chờ xác
nhận). Dòng nói “một phần” không được biến thành nhập toàn bộ.

### 3.2. Lưu ở đâu và cấu trúc

[Ledger JSON](../../../notary_v2/data/administrative_units/ledger.json) là nguồn
dữ liệu chính; [schema](../../../contracts/administrative-timeline/ledger.schema.json)
là mẫu máy kiểm tra, không phải kho thứ hai. Đây là schema kho cục bộ NAIA-9,
chưa publish thành contract tích hợp giữa module.

| Nhóm | Ý nghĩa |
|---|---|
| `units` | ID riêng, cấp `commune`/`district`/`province` (xã/huyện/tỉnh) |
| `names`, `codes`, `parents` | Tên/mã/nơi quản lý từng giai đoạn, liên kết sự kiện khi có |
| `events` | Nhiều tham chiếu `from`/`to`; ngày hiệu lực, khoảng ngày tùy chọn, trạng thái và ghi chú lãnh thổ |
| `mentions` | Chuỗi nơi cũ chưa rõ danh tính; mỗi dòng nguồn có tham chiếu riêng |
| `observations` | Nguyên văn Bando và toàn bộ bảng chi tiết; phân biệt “giữ nguyên” |
| `sources` | URL, cách tải, ngày/giờ lấy, SHA-256 (dấu kiểm tra nội dung), snapshot và nguồn dòng |

`snapshots/<sha256>.raw` giữ **nguyên byte** của catalog và 34 bảng. Không ghi đè
snapshot. `dataset_version` dựa trên hash toàn bộ lần nhập; `revision` tăng mỗi
lần ghi. Snapshot cũ còn nguyên khi refresh. Lần tải scratch chỉ chắc đến ngày
nên lưu `2026-10-04`; tải trực tiếp mới lưu thời điểm có múi giờ.

ID Bando ban đầu được tạo xác định từ `malk`, không từ tên hay `ma`. `ma` là mã
hiện tại dạng chuỗi giữ số 0 đầu; `magoc` là mã tỉnh hiện tại; `malk` là khóa đối
tượng bản đồ hiện tại. Chúng **không chứng minh cùng danh tính qua mọi thời kỳ**.
Refresh giữ ID của cùng khóa nguồn hiện tại để nối các lần quan sát. Mã tái
dùng với khóa nguồn khác tạo ID riêng. Curator (người phụ trách dữ liệu) xác
nhận danh tính lịch sử bằng nguồn, không gộp theo tên/mã. Nếu nguồn tái dùng cả
khóa bản đồ, phải đối chiếu và migration có kiểm tra, không coi đó là bằng chứng
lịch sử tự động.

`observed` nghĩa là website đang nêu giá trị đó, không hứa đúng cho ngày quá khứ.
`confirmed` là bản ghi lịch sử có nguồn và ngày được curator xác nhận. Khoảng
ngày dùng `[valid_from, valid_to)`: gồm ngày đầu, không gồm ngày cuối; ngày cuối
`null` của bản ghi confirmed nghĩa là còn tiếp tục.
Trạng thái của từng assertion (một khẳng định tên/mã/cha) độc lập với trạng thái
sự kiện được dẫn tới. Có thể đã biết chắc tên và ngày bắt đầu, nhưng vẫn chưa
biết danh tính nơi tiền thân: tên confirmed không tự làm sự kiện pending thành
confirmed, cũng không cho phép nối lịch sử qua tiền thân ấy.

### 3.3. Nguồn Bando và giới hạn

Đường đọc công khai: `POST https://sapnhap.bando.com.vn/p.co_dvhc`, form `ma=0`;
`POST /p.co_bangbieu`, form `ma=<malk tỉnh>`. Bảng trả đối tượng tỉnh, `.synt.`,
rồi mảng xã. Đây là đường website đang dùng, chưa có cam kết API/version ổn định.
Chỉ tải catalog/bảng đầy đủ; không gửi hồ sơ, địa chỉ khách hàng hay yêu cầu tra
tên ra ngoài. Chưa nối CLI này vào runtime ứng dụng.

Snapshot 04/10/2026: **3.355 đơn vị: 34 tỉnh, 3.321 xã, 0 huyện**. Tên/mã/tỉnh
cha giữ đúng catalog; bảng kiểm đối chiếu từng dòng. 136 dòng “giữ nguyên” là
quan sát, không tạo tên cũ giả. 3.219 mô tả khác giữ nguyên trong mention/sự
kiện chờ; 161 dòng nhắc phần lãnh thổ. Không tách văn xuôi thành đơn vị lịch sử
đã xác nhận: `candidate_names` đang trống; report `unparsed_rows=3219` nói rõ
phần chưa phân tích. Chú thích huyện trong ngoặc giữ nguyên. `details` giữ cả
`cancu`, `link` và mọi trường nguồn khác.

Ví dụ Phường Duy Hà, mã `13336`: nguồn nói Duy Minh, Duy Hải và một phần Hoàng
Đông. Kho giữ đủ câu; chưa biết ID/mã/tỉnh/huyện cũ và ngày hiệu lực của đơn vị
nguồn. Không biến thành sáp nhập toàn bộ đã xác nhận. Huyện được schema hỗ trợ
để Owner thêm sau dù Bando không có danh mục huyện.

### 3.4. CLI và cách Owner bổ sung lịch sử

Chạy từ root với Python; [helper](../../../notary_v2/administrative_timeline.py)
chỉ dùng thư viện chuẩn, không đổi database văn phòng, Word hay dữ liệu hồ sơ.

```powershell
python -m notary_v2.administrative_timeline validate
python -m notary_v2.administrative_timeline refresh-bando
python -m notary_v2.administrative_timeline import-bando --catalog .agent/scratch/multica-address-research/bando-public-current.json --tables .agent/scratch/multica-address-research/bando-public-tables --retrieved-at 2026-10-04
python -m notary_v2.administrative_timeline update .agent/scratch/owner-history.json
python -m notary_v2.administrative_timeline query owner:demo --as-on 2007-01-01
```

`refresh-bando` tải đủ trước khi ghi. Sai/thiếu bảng/hỏng hash bị từ chối; ledger
cũ còn nguyên. Nội dung giống nhau không tăng revision hoặc viết lại dữ liệu.
Nội dung mới thêm quan sát/tên/mã/sự kiện chờ, **không xóa lịch sử thủ công**.
Có khóa ghi để hai CLI không ghi đồng thời. Nếu sau sự cố còn `.write.lock`,
không tự xóa khóa. Khóa hiện không ghi PID (mã tiến trình); trước tiên kiểm các
tiến trình Python có thể đang chạy CLI/helper:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python' } | Select-Object ProcessId, CreationDate, CommandLine
```

Đối chiếu command có `notary_v2.administrative_timeline` và `--folder` với kho
đang sửa. Nếu dùng folder mặc định hoặc helper được gọi từ script khác, xác
minh cửa sổ/command chạy nó thuộc checkout nào; chưa rõ thì giữ khóa và chờ
hoặc kiểm với người mở tiến trình. Khi chắc chắn không còn writer của kho này,
mới xóa đúng file `.write.lock` trong folder đó và chạy `validate`. Không dùng
tuổi file làm bằng chứng rằng writer đã chết.

`validate`, `query`, `update` báo lỗi nếu chưa có `ledger.json`; chỉ lần import
đầu được khởi tạo kho mới. CLI hiện chặn catalog khác mốc **34/3.321** để tránh
nhập nhầm một phần nguồn. Nếu danh mục thực tế đổi số lượng, phải tải/đối chiếu
đủ catalog và tất cả bảng công khai, ghi nguồn và tổng số mới, rồi cập nhật
baseline và tests trong cùng thay đổi có kiểm; không bỏ kiểm chỉ để nhập được.

Patch JSON gồm `base_revision` bằng revision đang có và `upsert` chứa các nhóm
cần thêm/sửa. Mỗi record ghi đầy đủ theo schema. ID cũ cập nhật record cùng ID;
ID mới thêm record; không có xóa. Nguồn và bằng chứng Bando bất biến. Muốn xác
nhận lịch sử thì thêm record curator, không sửa câu nguồn. Mention cho phép
cập nhật riêng `resolved_unit_id`/`status`; trường nguồn khác giữ nguyên. Sự kiện
Bando vẫn là bằng chứng chờ; thêm sự kiện confirmed tham chiếu `unit` và nguồn
ngày. Nhờ vậy lời website tách khỏi kết luận của curator.

Quyền sửa dựa trên người tạo record, không dựa riêng vào nguồn được trích dẫn.
`sources` đã lưu luôn bất biến; `observations`, ID `bando:`/`unit:bando:`, các ID
phiên bản do importer sinh (`name|code|parent|event|mention|observation` + hash
dataset) và `units.source_key` dành cho importer. Patch thủ công không được tạo
giả các bản ghi đó. Record gốc chỉ có ngoại lệ resolve danh tính mention như
trên. Kết luận curator dùng ID riêng, chẳng hạn `owner:...`, có thể trích nguồn
Bando và được đính chính cùng ID; bản trước vẫn nằm trong archive. Mỗi nhóm
upsert phải có ID không trùng, không áp dụng quy tắc “dòng cuối thắng”.

Trước mỗi lần cập nhật thủ công hợp lệ, CLI lưu nguyên byte ledger cũ trong
`revisions/revision-<revision>-<sha256>.json.gz` (JSON nén). Bản này bất biến,
giúp xem/khôi phục dữ liệu trước một lần đính chính cùng ID; không là nguồn
đọc thứ hai. Nếu không lưu được bản cũ thì toàn bộ update dừng, ledger hiện
tại không đổi. Khi khôi phục cần giải nén bản chọn, đối chiếu hash trong tên,
kiểm schema/nguồn và revision trước khi thay kho; không có tự động rollback
hoặc xóa các bản phục hồi. Refresh vẫn thêm bằng chứng mới và giữ lịch sử cũ.

Mention Bando hiện giữ cả câu, có thể chứa nhiều xã. Chỉ gán `resolved_unit_id`
khi đã xác minh mention tương ứng **một** đơn vị. Với câu A+B, Owner tạo các
unit và sự kiện curator có nhiều `from`/`to` cùng nguồn; giữ nguyên mention
tổng hợp làm bằng chứng, không resolve cả câu thành một ID.

Ví dụ **giả lập** A→B trên cùng ID, không phải lịch sử Việt Nam. Chỉ chạy trong
bản sao thử; thay `base_revision` bằng revision bản sao. Khi cập nhật kho chính,
thay nguồn/ngày bằng nguồn thật:

```json
{
  "base_revision": 1,
  "upsert": {
    "sources": [{"id":"owner:demo-source","provider":"Owner synthetic demo","url":"urn:demo:not-history","protocol":"manual","request_body":null,"retrieved_at":"2026-10-04","sha256":null,"snapshot":null,"description":"Ví dụ giả lập; không phải lịch sử"}],
    "units": [{"id":"owner:demo","level":"district","source_key":null,"evidence":[{"source_id":"owner:demo-source","row_key":"demo"}]}],
    "names": [
      {"id":"owner:demo:A","unit_id":"owner:demo","value":"A","valid_from":"2000-01-01","valid_to":"2005-01-01","status":"confirmed","event_id":null,"evidence":[{"source_id":"owner:demo-source","row_key":"demo"}]},
      {"id":"owner:demo:B","unit_id":"owner:demo","value":"B","valid_from":"2005-01-01","valid_to":null,"status":"confirmed","event_id":"owner:demo:ab","evidence":[{"source_id":"owner:demo-source","row_key":"demo"}]}
    ],
    "events": [{"id":"owner:demo:ab","type":"rename","from":[{"kind":"unit","id":"owner:demo"}],"to":[{"kind":"unit","id":"owner:demo"}],"effective_on":"2005-01-01","valid_from":null,"valid_to":null,"status":"confirmed","territory":"whole","notes":"Ví dụ giả lập A→B","evidence":[{"source_id":"owner:demo-source","row_key":"demo"}]}]
  }
}
```

Thêm B→C→D: cập nhật ngày cuối tên B, thêm tên C/D và sự kiện rename trên cùng
ID. Thêm A+B→C: tạo các ID riêng có bằng chứng danh tính, dùng `merge` với hai
`from` và một `to`. Chia C→D+E dùng `split` nhiều `to`; giữ `territory=partial`
và ghi chú nếu chỉ chuyển một phần. Không biến mỗi tên cũ trong câu thành ID
verified. Chưa đủ danh tính/ngày thì dùng mention, ngày `null`, trạng thái
`pending`; curator bổ sung có nguồn sau.

Đích C của merge có thể là đơn vị đã tồn tại rồi nhận thêm lãnh thổ. Việc C
xuất hiện ở `to` không tự chứng minh ngày thành lập; muốn khẳng định thành lập
cần nguồn riêng và cấu trúc assertion được duyệt sau. Hiện kho không tự suy
ngày sinh của đơn vị từ sự kiện sáp nhập.

Query trả `chronological_events` (confirmed theo ngày) riêng với `pending_evidence`
(bằng chứng chưa chắc). Chỉ tên confirmed có giai đoạn bao phủ ngày hỏi mới vào
`confirmed_name_at_date`; thiếu lịch sử trả `insufficient_confirmed_history`,
không suy từ tên hiện hành. Quan sát hiện tại ở `current_source_observations`.
CLI query hiện trả lịch sử **tên**, sự kiện và quan sát nguồn; chưa trả truy vấn
theo ngày cho `codes`/`parents` và chưa giải quyết địa chỉ đầy đủ. Các phiên bản
mã/cha vẫn được lưu và validate trong ledger để consumer sau dùng đúng nguồn.
CLI query kiểm cả snapshot hỗ trợ trước khi trả kết quả: file nguồn mất hoặc
hash sai phải báo lỗi, không tiếp tục trình bày như dữ liệu đã kiểm.
Chỉ quan hệ confirmed nối lịch sử giữa các ID. Mention đã xác nhận danh tính
giúp tìm bằng chứng pending liên quan; quan hệ đó vẫn pending và không đưa
lịch sử của nơi bên kia vào kết quả confirmed.

### 3.5. Kiểm tra và cách phát triển sau này

Đã triển khai: schema `1.0`; validator chặn ID trùng, nguồn/tham chiếu thiếu,
ngày sai/đảo, khoảng confirmed chồng nhau, mã tái dùng chồng thời gian, cha sai
cấp/quay vòng, confirmed thiếu ngày/danh tính, rename đổi ID, merge/split sai
số đầu vào/ra, chuỗi quay vòng/ngược ngày, dùng đơn vị sau khi bỏ/tiêu thụ toàn
bộ; quan hệ con không được kéo dài quá ngày kết thúc của cha. Hai sự kiện tiêu
thụ toàn bộ xung đột, hoặc đổi tên và bỏ đơn vị cùng ngày, bị từ chối. Ngày
phải đúng `YYYY-MM-DD`. Revision cũ bị từ chối. Ledger và raw snapshot đều ghi
file tạm rồi thay một lần; lỗi trước đó không để file đích bị ghi nửa chừng.

Chuỗi kế thừa toàn đơn vị khác với chuyển một phần lãnh thổ. Chuyển partial
A→B rồi B→A ở ngày khác có thể hợp lệ vì cả hai ID vẫn tồn tại; không đưa các
movement partial vào phép kiểm cycle/ngược ngày của chuỗi kế thừa. Sự kiện
`reported_transition` confirmed và whole cũng kết thúc input không còn trong
outputs; bằng chứng Bando pending không áp quy tắc kết thúc ấy. Một giai đoạn
tên confirmed không được trùm qua ngày rename confirmed, dù `event_id` để null.
Giai đoạn cha confirmed cũng không được trùm qua ngày reparent confirmed.
Chỉ chuyển whole với input không còn trong output tạo cạnh kế thừa để kiểm
cycle/ngày. Ví dụ B→B+C rồi A+B→B vẫn giữ ID B; không coi B kết thúc ở lần chia.
Lãnh thổ unknown không khẳng định kế thừa toàn đơn vị. Abolish confirmed phải
whole; `reported_transition` confirmed phải có cả nguồn và đích. Bản pending
Bando giữ nguyên và không áp các kết luận về kết thúc đơn vị ấy.

[Tests](../../../notary_v2/tests/test_administrative_timeline.py) dùng ví dụ giả
lập có nhãn: chuỗi rename, merge/split, ba cấp, mã tái dùng, cùng tên khác nơi,
ngày chờ, nguồn hỏng, refresh/giữ lịch sử, toàn bộ snapshot thật. Chạy:
`python -m pytest notary_v2/tests/test_administrative_timeline.py -q`.

CLI hiện validate và quét toàn ledger theo lần chạy, phù hợp công cụ local/batch.
Lõi tra cứu nạp và kiểm khi bản kho đổi
rồi dựng index (bảng giúp tìm nhanh) theo tên chính thức, tỉnh và đoạn chữ gốc
Bando. Chỉ mục phải nhận cả revision khi Owner bổ sung lịch sử;
dataset_version của Bando có thể chưa đổi. Truy
merge/split theo ID, không theo tên; không gọi CLI/quét ledger hoặc tải web mỗi
lần gõ địa chỉ. Index/cache dựng lại từ ledger được và không là nguồn chính.
Validator chuỗi hiện dùng lời gọi lặp sâu (recursion); lịch sử cực sâu khoảng
1.000 bước có thể vượt giới hạn Python. Khi có dữ liệu dài như vậy, chuyển sang
duyệt lặp bằng hàng đợi/stack cùng index và kiểm lại cycle/ngày; đợt này chưa
đổi thuật toán cho trường hợp cực sâu.

Chỉ chuyển database khi có nhu cầu thực và quyết định owner/contract; hiện
chưa cần dịch vụ hoặc DB mới. Đổi schema phải tăng version, giữ bản trước,
viết migration rõ ràng; kiểm số record, ID, chuỗi lịch sử, trạng thái, ngày và
hash nguồn trước/sau. Không âm thầm nhận version không hỗ trợ.

### 3.6. Nguồn quyết định và phần còn thiếu

Owner 03/10: nơi niêm yết theo `ngay_lap_ho_so`; ngày giấy nguồn giúp đọc địa
chỉ cũ/mới, nơi cấp khai tử riêng. Owner 04/10: Bando là nguồn tên hiện hành,
lấy bước gần nhất trước, Owner thêm A→B→C→D sau; hỗ trợ huyện/sáp nhập/chia tách;
ghi hướng mở rộng để agent sau tiếp tục đúng. Kho chuẩn bị dữ liệu, chưa thay
quy tắc địa chỉ hồ sơ. API không có ngày hiệu lực, ID lịch sử hay parent cũ;
các giới hạn đó còn thiếu thật, không được che bằng ngày tải.

# Bộ quy tắc nghiệp vụ chia thừa kế (R-xx)

> **Trạng thái:** bản chuẩn hoá 26/10/2026 để đưa reviewer độc lập đánh giá.
> Thay toàn bộ bản "draft vòng 2" (24/08/2026); bản cũ xem Git trước commit
> `7e4e9e4` (các tham chiếu `BR §x` cũ trong tài liệu khác trỏ về bản đó).
> **Nguồn:** BLDS 2015 (số điều tóm tắt tại [`legal-baseline.md`](./legal-baseline.md)),
> Luật HNGĐ 2014, và quyết định owner D-xxx tại
> [`decision-80`](../../../../../docs/decisions/decision-80-so-quyet-dinh-nghiep-vu-thua-ke.md).
> **Nguyên tắc:** mặc định theo luật (D-019). Quy tắc nào khác luật ghi
> **Lệch** kèm lý do; "Giới hạn phạm vi" = app không làm, không phải nói luật khác.
> Tài liệu này mô tả **hành vi đích**. Chỗ code hiện khác ghi ở §6, không sửa code ở đây.

## 1. Thuật ngữ

| Từ | Nghĩa trong app |
|---|---|
| Người | Một hồ sơ cá nhân trong Stage (có giấy tờ cá nhân). Một người có thể xuất hiện ở nhiều ô trên sơ đồ (D-005). |
| Tài sản `k` | Một trong tối đa 5 tài sản của hồ sơ (D-036). |
| Chủ đất của `k` | Người có dấu "Chủ" trên tài sản `k` (`ownPositions` chứa `k`). |
| Người nhận của `k` | Người có dấu "Nhận" trên tài sản `k` (`receivePositions` chứa `k`). |
| Vòng di sản | Phần tài sản `k` mà một người đang nắm tại ngày người đó chết, đem chia. |
| Ô vợ/chồng (ô node kép) | Ô gắn vào node **người đã chết có tài sản** (tài sản sẵn có hoặc nhận từ người khác). Người đang sống không có ô này, trừ chủ đất còn sống (D-042). Mỗi ô chứa tối đa một vợ/chồng hợp pháp; người được kéo vào sau cùng là người hợp pháp (D-041). |
| Đơn vị | Một suất trong hàng 1 của một vòng: mỗi cha, mẹ, vợ/chồng là một đơn vị; mỗi con (kể cả con chết trước được thế vị) là một đơn vị nhánh. |
| Nhánh | Một con của người để lại di sản cùng toàn bộ hậu duệ được gắn của con đó, tới chắt. |
| Từ chối (nhãn nghiệp vụ) | Người có suất mà không có dấu "Nhận" trên tài sản đó (D-024). Người còn sống chưa tích Nhận thì chỉ được nhắc, **không** tính là từ chối (D-046). **Không** phải văn bản từ chối theo Điều 620. |

## 2. Bất biến tính toán

| Mã | Bất biến |
|---|---|
| INV-1 | Tính bằng phân số chính xác; phần trăm chỉ để hiển thị. |
| INV-2 | Quan hệ chỉ lấy từ liên kết tường minh (cha/mẹ, vợ/chồng), không suy từ vị trí, nhãn, thế hệ. |
| INV-3 | Mỗi tài sản tính độc lập. Mỗi vòng bảo toàn: phần đã chia + phần chưa có người nhận = giá trị vòng. Tổng mỗi tài sản luôn = 1. |
| INV-4 | Kết quả không phụ thuộc thứ tự dữ liệu vào; cùng dữ liệu cho cùng kết quả. |
| INV-5 | Một người nhận từ nhiều nguồn/vai thì cộng dồn. |
| INV-6 | Không mở vòng giá trị 0. |
| INV-7 | App không tạo người, không đoán quan hệ, không kết luận điều không có trên sơ đồ (D-015). Ngoại lệ đã được owner chốt: R-07 (ngày trống = còn sống, D-001, D-032) và R-19 (không dấu Nhận = từ chối, D-024). |
| INV-8 | Mọi số hiển thị và in ra Word đọc từ cùng một kết quả của cùng một bản đã lưu (D-003). |

## 3. Quy tắc phạm vi

| Mã | Điều kiện | Kết quả | Nguồn | Lệch luật? |
|---|---|---|---|---|
| R-01 | Mọi hồ sơ | Chỉ chia **thừa kế theo pháp luật**. Không xử lý di chúc, phần bắt buộc. | BLDS 650.1(a), 644; D-026 | Giới hạn phạm vi |
| R-02 | Người đã thành thai nhưng chưa sinh lúc mở thừa kế | Không xét; chỉ người có giấy tờ cá nhân mới được đưa vào. Khách hàng tự chịu trách nhiệm. | BLDS 613, 660.1, 662.1; D-026 | **Lệch**: luật buộc dành lại một suất cho thai nhi trước khi chia (660.1); thai nhi sinh ra còn sống sau khi đã chia thì phát sinh người thừa kế mới (662.1). App bỏ qua để đơn giản; trách nhiệm thuộc khách |
| R-03 | Bất kỳ | App không xác định ai phải ký; ai có tên trong Stage là người liên quan. | BLDS 656; D-027 | **Lệch** (không can thiệp): luật yêu cầu thoả thuận của những người thừa kế, app không kiểm |
| R-04 | Bất kỳ | Tính đủ ba hàng thừa kế theo pháp luật: hàng 1, nếu không còn ai hàng 1 thì hàng 2, nếu không còn ai hàng 2 thì hàng 3 (R-15, R-32). | BLDS 651; D-038 | Không |
| R-05 | Bất kỳ | Áp quy tắc BLDS 2015 cho mọi ngày mở thừa kế; không có logic theo phiên bản luật. | D-021 (tạm; Q-002) | **Lệch tạm**: luật áp dụng là luật tại thời điểm mở; owner đánh giá quy tắc ổn định |
| R-06 | Bất kỳ | Mỗi **thửa đất** là một tài sản. Tối đa **5** tài sản mỗi hồ sơ, ở mọi nơi (nhập, tính, Word). | D-036 (thay D-029) | Kỹ thuật |
| R-30 | Người chết có nghĩa vụ tài sản (nợ, chi phí mai táng…) | App **không** khấu trừ nghĩa vụ trước khi chia; chia toàn bộ phần đứng tên. | BLDS 615, 658 | **Lệch** (giới hạn phạm vi, có chủ ý): luật buộc thanh toán nghĩa vụ trước khi chia; app chỉ chia quyền sử dụng/sở hữu đứng tên, việc thanh toán do các bên tự thoả thuận ngoài app |
| R-31 | Thời điểm mở thừa kế đã lâu | App **không** cảnh báo thời hiệu. | BLDS 623 | **Lệch** (giới hạn phạm vi, có chủ ý): luật có thời hiệu yêu cầu chia di sản; app không kiểm, công chứng viên tự đánh giá |
| R-35 | Đất hộ gia đình | Không có khái niệm riêng: user tự đánh dấu Chủ cho các thành viên hộ; chia theo R-13. | D-037 | **Lệch** (quy ước): app không xác định ai là thành viên có quyền chung; user tự chọn và tự chịu trách nhiệm |

## 4. Quy tắc dữ liệu và quan hệ

| Mã | Điều kiện | Kết quả | Nguồn | Lệch luật? |
|---|---|---|---|---|
| R-07 | Ngày chết trống hoặc không đọc được, **và không** chọn trạng thái "chết trước người để lại di sản, không rõ ngày" | Coi là **còn sống**. Nếu chọn trạng thái đó (thường gặp với cha mẹ "đã chết từ lâu"): coi là chết **trước** mọi người để lại di sản trên sơ đồ — không hưởng, không mở vòng di sản. Trạng thái in đúng như nhập. | D-001, D-032 | **Lệch**: luật cần chứng cứ chết; app giảm nhập liệu. Ngoại lệ của INV-7 đã chốt |
| R-08 | Ngày chết nhập thiếu (chỉ năm `yyyy`, hoặc tháng/năm `mm/yyyy`) | **Hiển thị** luôn đúng như user nhập ở mọi đầu ra (màn hình, Word). Chỉ khi **tính** cần ngày đủ, backend quy đổi ngầm: `yyyy` → `01/01/yyyy`, `mm/yyyy` → `01/mm/yyyy`, rồi so như ngày đủ. | D-033 (thay D-007) | **Lệch (quy ước)**: ngày quy đổi có thể đảo thứ tự thật khi hai người chết cùng năm/tháng; owner chấp nhận |
| R-09 | Hai người chết cùng ngày (sau quy đổi R-08) | Coi là cùng thời điểm: không thừa kế của nhau; nếu một người là con của người kia thì áp thế vị (R-17). | BLDS 619, 652; D-006 | **Lệch (quy ước)**: 619 nói "cùng thời điểm"; app coi **cùng ngày** là cùng thời điểm, không xét giờ chết |
| R-10 | Con trên sơ đồ | "Con" gồm con đẻ và con nuôi, không phân loại. Mỗi con gắn tối đa 1 cha + 1 mẹ (được trống). Con chỉ hưởng từ cha/mẹ **được gắn**. | BLDS 651.1(a), 653, 654; D-023 | **Lệch**: (1) giới hạn 1 cha + 1 mẹ nên không biểu diễn được con nuôi vẫn hưởng của cha mẹ đẻ (653) hay con riêng hưởng của cả cha/mẹ đẻ lẫn bố dượng/mẹ kế (654), cũng không biểu diễn chiều bố dượng/mẹ kế hưởng của con riêng; (2) con riêng – bố dượng/mẹ kế chỉ hưởng khi user tự gắn, app không xét điều kiện nuôi dưỡng. Lý do: mô hình sơ đồ đơn giản (mỗi ô một cặp cha mẹ) |
| R-11 | Vợ/chồng của người X đã chết có tài sản | Vợ/chồng = người nằm trong **ô vợ/chồng (ô node kép) của X** = **vợ/chồng hợp pháp tại ngày X chết, theo user nhập** (651.1(a); một người chỉ có một vợ/chồng hợp pháp tại một thời điểm). Chỉ người chết có tài sản (sẵn có hoặc được nhận) mới có ô; người đang sống không có ô, chỉ có thể *là* vợ/chồng trong ô của người chết. Nhiều người được kéo vào ô → **người kéo vào sau cùng** là vợ/chồng hợp pháp, thẻ được làm nổi bật; những người trước **không** có tư cách vợ/chồng; không hỏi xác nhận, không chặn kéo thả. **Một chiều theo ô**: hai vợ chồng cùng chết thì mỗi người có ô riêng, không bắt hai ô khớp nhau (vd. vợ tái hôn sau khi chồng chết là hợp lệ). Liên kết con–cha/mẹ (R-10) giữ riêng để phân biệt con chung/con riêng; vợ/chồng cũ là node thường, không có suất. **Hồ sơ cũ nhiều ứng viên**: chuyển đổi đưa tất cả vào ô theo thứ tự cố định, người cuối là vợ/chồng hợp pháp; không cảnh báo, không `incomplete` (D-041). | BLDS 651.1(a), 655; HNGĐ 65; D-022, D-039, D-041 | **Lệch** (trách nhiệm user): thứ tự kéo thả thay cho căn cứ pháp lý về hôn nhân; các trường hợp 655 (đang ly hôn, tái hôn sau) do user tự chọn đúng người; app không kiểm |
| R-12 | Cha mẹ của người chết | = hai người được gắn làm cha/mẹ của người đó (tối đa 1 cha + 1 mẹ). | BLDS 651.1(a), 653 | **Lệch**: người chết là con nuôi có thể có cả cha mẹ đẻ và cha mẹ nuôi trong hàng 1 (653); app chỉ biểu diễn được một cặp (cùng lý do R-10) |

## 5. Quy tắc chia

| Mã | Điều kiện | Kết quả | Nguồn | Lệch luật? |
|---|---|---|---|---|
| R-13 | Tài sản `k` có `n` chủ đất | Phần di sản xác định **chỉ** theo những người user đánh dấu Chủ: mỗi người phần gốc `1/n`. App **không** suy luận tài sản chung vợ chồng và **không cảnh báo**. | BLDS 612; HNGĐ 33, 66.2; D-020, D-017, D-040 | **Lệch có chủ ý** (trách nhiệm user): giấy tờ ghi tỷ lệ không đều vẫn chia đều; tài sản chung vợ chồng chỉ đứng tên một người (66.2: chia đôi) hay tài sản riêng đứng tên hai người đều do user tự đánh dấu |
| R-14 | Một người chết khi đang nắm phần `p > 0` của `k` | Mở một vòng giá trị `p` tại ngày chết. Các vòng xử lý theo thứ tự ngày; các vòng cùng ngày (sau quy đổi R-08) được coi là cùng thời điểm (619): lấy giá trị đồng thời trước khi chia bất kỳ vòng nào trong nhóm đó. Phần của người chết về 0 sau khi chia. | BLDS 611, 612, 619 | Không |
| R-15 | Vòng của người X | Đơn vị hàng 1 = cha, mẹ (R-12), vợ/chồng (R-11) **còn sống lúc X chết và là người nhận của `k`**, hoặc **chết sau X** (R-16); cộng mỗi con của X (R-10) mà nhánh còn ít nhất một người nhận (R-17, R-19). Giá trị vòng chia **đều** cho các đơn vị. Không còn đơn vị hàng 1 (không có, chết trước, hoặc từ chối) → xét hàng 2, rồi hàng 3 (R-32). Cả ba hàng trống → "chưa có người nhận", `incomplete`. | BLDS 651.1(a), 651.2, 651.3; D-038 | Không |
| R-16 | Người thừa kế (hàng 1 hoặc thế vị) chết **sau** X | Vẫn hưởng phần của mình tại lúc X chết (**chuyển tiếp**), luôn coi là nhận (không áp R-19 vì người chết không thể khai). Phần đó mở vòng mới khi người này chết (R-14). | BLDS 613, 614; D-010 | Không (quy ước "luôn nhận" là của app) |
| R-17 | Con C của X chết **trước hoặc cùng lúc** với X (R-09) | Thế vị: nhánh C chia đều cho các con được gắn của C; cháu cũng ở tình huống đó thì xuống chắt, chia đều từng cấp trong nhánh. Phần thế vị không thuộc di sản của C. Vợ/chồng của C không nhận phần thế vị. | BLDS 652; D-016 | Không |
| R-18 | Thế vị phải xuống **dưới chắt** để có người nhận | Dừng ở chắt; hồ sơ trạng thái `unsupported` mã `representation_depth_exceeded`, không đưa phân số. | BLDS 652; D-012 | **Lệch / giới hạn phạm vi**: theo luật nhánh không có người thế vị trong giới hạn chắt chỉ không thành đơn vị và vòng vẫn chia được; app chọn thận trọng trả `unsupported` |
| R-19 | Người có suất (hàng 1 hoặc thế vị), còn sống lúc X chết, **không** có dấu Nhận trên `k` | Coi là **từ chối** phần của mình trên `k`. Chủ đất không có dấu Nhận vẫn giữ phần gốc R-13, chỉ không nhận thêm. | BLDS 620, 621; D-024 | **Lệch**: luật đòi văn bản từ chối (620) và tách riêng người không được quyền hưởng (621); app gộp cả hai (và cả "nhường theo thoả thuận") vào nhãn "từ chối", user sửa tay khi khác. Đây cũng là ngoại lệ của INV-7 (app kết luận từ việc thiếu dấu) (đã chốt: D-024; Q-013 đóng ở D-032) |
| R-20 | Có người từ chối (R-19) trong một nhánh thế vị | Phần của họ **ở lại nhánh**: chia đều cho những người còn nhận trong nhánh, theo từng cấp. Cả nhánh không còn ai nhận → nhánh không thành đơn vị; giá trị chia đều cho các đơn vị còn lại của vòng (R-15). | BLDS 651.2, 652; D-024 (nhãn từ chối nghiệp vụ, không phải văn bản 620); D-025, D-011 | **Lệch nghiệp vụ** (theo D-011): cách hiểu suất gắn với nhánh và cách chia lại khi nhánh rỗng là quy ước của app |
| R-21 | Người là đơn vị trực tiếp (cha, mẹ, vợ/chồng, con còn sống) từ chối | Không thành đơn vị; giá trị chia đều cho các đơn vị còn lại. | BLDS 651.2; D-024 (nhãn từ chối nghiệp vụ, không phải văn bản 620) | Không (ngoài lệch đã ghi ở R-19) |
| R-22 | Một người nhận từ nhiều vòng/vai | Cộng dồn (INV-5). | D-005 | Không |
| R-32 | Vòng của X không còn đơn vị hàng 1 (R-15) | **Hàng 2** (651.1(b)): ông bà nội/ngoại (cha/mẹ của cha/mẹ X); anh chị em ruột (chung ít nhất một cha/mẹ được gắn với X); cháu ruột mà X là ông/bà (con của con X). Không còn ai hàng 2 → **Hàng 3** (651.1(c)): cụ nội/ngoại (cha/mẹ của ông bà); bác, chú, cậu, cô, dì ruột (con khác của ông bà); cháu ruột mà X là bác/chú/cậu/cô/dì (con của anh chị em ruột X); chắt ruột mà X là cụ (con của cháu X). Mỗi **người** một suất, chia đều; một người nhiều vai trong cùng hàng chỉ một suất. Người chết trước/cùng lúc X không hưởng; **không thế vị** trong hàng 2/3 (652 chỉ áp cho con/cháu của X). Chết sau X: chuyển tiếp (R-16). Không dấu Nhận: từ chối (R-19), chia cho người còn lại cùng hàng; cả hàng từ chối → hàng sau. | BLDS 651.1(b)(c), 651.2, 651.3, 652; D-038 | Không. Cách hiểu cần reviewer kiểm: anh chị em cùng cha khác mẹ/cùng mẹ khác cha là "ruột" |
| R-33 | Từ chối trên Word | Engine phân bổ theo nhánh (R-20, D-025). Văn bản từ chối ký riêng theo nhánh (người cùng nhánh cùng cách xưng hô); văn bản phân chia tổng kết liệt kê/đếm người từ chối **theo đầu người**. | D-034 | Không (cách trình bày) |
| R-34 | Hai người gốc đều chết, một người nhận hết | Engine tính theo vòng (R-14, R-16). Word được viết gọn "A và B để lại di sản cho C". Chỉ cảnh báo khi kết quả cuối theo cách viết gọn **khác** kết quả tính theo vòng. | D-035 | Không (cách hành văn; kết quả giống nhau) |

## 6. Quy tắc thao tác sơ đồ và lưu

| Mã | Điều kiện | Kết quả | Nguồn | Lệch luật? |
|---|---|---|---|---|
| R-23 | Mỗi tài sản | Dấu Chủ/Nhận đặt riêng cho từng người × tài sản; tính riêng từng tài sản. | D-008 | Kỹ thuật |
| R-24 | Dấu chọn trỏ tới tài sản không còn tồn tại | Tự gỡ, kèm cảnh báo. | Kỹ thuật | Không |
| R-25 | Lỗi cấu trúc: cha/mẹ trỏ tới ô không có, quá 2 cha/mẹ, tự làm cha/mẹ/vợ chồng mình, vòng tổ tiên **thật**. Vợ/chồng **không** còn là lỗi cấu trúc: không đòi hai chiều, không có `spouse_conflict` (D-041 thay yêu cầu cũ); ô có nhiều người thì lấy người cuối (R-11) | **Vẫn lưu** nguyên trạng, trạng thái `invalid` kèm danh sách lỗi; không đưa phân số; Word in nhãn lỗi. | D-002, D-030, D-041 | Kỹ thuật |
| R-26 | Một người nối tới tổ tiên qua hai đường (vd. họ hàng lấy nhau) | **Không** phải vòng tổ tiên; tính bình thường. | D-030 | Kỹ thuật |
| R-27 | Xoá một **người gốc** (chủ đất) | Không xoá cả hồ sơ. Gỡ những người thuộc nhánh người đó; vợ/chồng người đó giữ nếu cũng là chủ đất, gỡ nếu không. Người bị gỡ trở về Pool, không xoá khỏi Stage. Người còn vai ở nhánh khác vẫn giữ. | D-031, D-009 | Kỹ thuật |
| R-28 | Lưu/xuất Word ở mọi trạng thái | Không bao giờ chặn; trạng thái `invalid`/`unsupported`/`incomplete`/`complete` hiện trên UI và Word. | D-002 | Kỹ thuật |
| R-29 | Nhận diện nhánh | Dùng ID ổn định và đường nhánh do engine trả; không dùng mã 1.x.x làm định danh. | D-004, D-028 | Kỹ thuật |

## 7. Trạng thái kết quả

| Trạng thái | Khi nào | Có phân số? |
|---|---|---|
| `complete` | Mọi vòng của mọi tài sản đều có đơn vị nhận | Có |
| `incomplete` | Có vòng "chưa có người nhận" (R-15) | Có, kèm phần chưa có người nhận |
| `unsupported` | R-18 | Không |
| `invalid` | R-25 | Không |

**Thứ tự ưu tiên:** `invalid` > `unsupported` > `incomplete` > `complete`. Khi nhiều điều kiện cùng xảy ra, lấy trạng thái đứng trước.

**Phạm vi:** trạng thái áp **cho cả hồ sơ** (một trạng thái cho một kết quả tính), khớp với engine hiện trả một `status` cho mỗi lần tính. Trạng thái hồ sơ = trạng thái ưu tiên cao nhất trong các tài sản; phần "chưa có người nhận" vẫn ghi riêng theo tài sản.

## 8. Đối chiếu code hiện tại (chỉ ghi, không sửa)

| Quy tắc | Hiện trạng code |
|---|---|
| R-07, R-08 | Quy đổi `yyyy` → 01/01 khi tính đã có; chưa có `mm/yyyy`; chưa kiểm hiển thị luôn giữ nguyên chuỗi nhập ở mọi đầu ra; chưa có trạng thái "chết trước, không rõ ngày" (D-032). |
| R-18 | Engine không kiểm độ sâu, đi xuống không giới hạn. |
| R-23 | Bước chuyển dữ liệu gộp dấu theo tài sản thành một cờ chung; engine tính một kết quả cho mọi tài sản. |
| R-25, R-28 | Lỗi cấu trúc chặn cả xem kết quả lẫn lưu (`diagram_invalid_state`). |
| R-11, R-25 | Code hiện dùng liên kết vợ/chồng giữa hai node (UI coi một chiều là vợ chồng; server đòi hai chiều; nhánh `agent/omp/hang-2-3` commit `b352aac` thêm lỗi `spouse_conflict` một chiều và UI ghi hai chiều). Theo D-041 phải thay bằng ô vợ/chồng một chiều trên node người chết có tài sản + chuyển đổi hồ sơ cũ — chưa làm. |
| R-15, R-32 | Engine chỉ có hàng 1; hàng 2/3 đang cài trên nhánh `agent/omp/hang-2-3` (D-038). |
| R-33, R-34 | Chưa đối chiếu Word: liệt kê người từ chối theo đầu người; cảnh báo khi cách viết gọn khác kết quả. |
| R-26 | Kiểm vòng tổ tiên báo nhầm khi một người được tới bằng hai đường. |
| R-27 | Chưa đối chiếu với code gỡ node. |
| INV-8 | Lưu nhiều bản sao; Word có thể đọc bản cũ hoặc tỷ lệ của bảng người tham gia. |

## 9. Ánh xạ D-xxx → R-xx

D-001→R-07 · D-002→R-25, R-28 · D-003→INV-8 · D-004→R-29 · D-005→R-22 ·
D-006→R-09 · D-007 (bị D-033 thay) · D-008→R-23 · D-009→R-27 · D-010→R-16 ·
D-011→R-20 · D-012→R-18 · D-013/D-020→R-13 · D-014/D-024→R-19 · D-015→INV-7 ·
D-016→R-17 · D-017→R-13 · D-021→R-05 · D-022/D-039/D-041→R-11 · D-023→R-10 ·
D-025→R-20 · D-026→R-01, R-02 · D-027→R-03 · D-028→R-29 · D-029 (bị D-036 thay) ·
D-030→R-25, R-26 · D-031→R-27. D-032→R-07 · D-033→R-08 · D-034→R-33 · D-035→R-34 · D-036→R-06 · D-037→R-35 · D-038→R-04, R-15, R-32 (gác bởi D-044) · D-041/D-042→R-11 · D-043→diagram-rules.md §9/§11 · D-045→R-07 · D-046→R-19 · D-047, D-048→R-25 (ngoại lệ) · D-049→R-01.D-039→R-11 · D-040→R-13 · D-041→R-11, R-25 (và thuật ngữ §1). R-30, R-31 không có D (lệch có chủ ý, ghi từ review độc lập 26/10/2026). (D-018, D-019 là quy trình.)

## 10. Câu hỏi mở Q-xxx

Q-001, Q-003…Q-013 đã chốt (Q-013 ở D-032); các điểm từ phân tích 476 hồ sơ thật chốt ở D-033…D-040 (26/10/2026). Còn mở:

| Q | Câu hỏi | Trạng thái |
|---|---|---|
| Q-002 | Thừa kế mở trước 01/01/2017 có điểm nào luật cũ khác ảnh hưởng hồ sơ đất? | Mở, ưu tiên thấp; tạm theo R-05 (D-021); cần giải thích lại cho owner |

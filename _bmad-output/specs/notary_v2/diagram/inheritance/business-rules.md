# Bộ quy tắc nghiệp vụ chia thừa kế (R-xx)

> **Trạng thái:** bản chuẩn hoá 26/10/2026 để đưa reviewer độc lập đánh giá.
> Thay toàn bộ bản "draft vòng 2" (24/08/2026); bản cũ xem Git trước commit
> `7e4e9e4` (các tham chiếu `BR §x` cũ trong tài liệu khác trỏ về bản đó).
> **Nguồn:** BLDS 2015 (số điều tóm tắt tại [`legal-baseline.md`](./legal-baseline.md)),
> Luật HNGĐ 2014, và quyết định owner D-xxx tại
> [`decision-80`](../../../../decisions/decision-80-so-quyet-dinh-nghiep-vu-thua-ke.md).
> **Nguyên tắc:** mặc định theo luật (D-019). Quy tắc nào khác luật ghi
> **Lệch** kèm lý do; "Giới hạn phạm vi" = app không làm, không phải nói luật khác.
> Tài liệu này mô tả **hành vi đích**. Chỗ code hiện khác ghi ở §6, không sửa code ở đây.

## 1. Thuật ngữ

| Từ | Nghĩa trong app |
|---|---|
| Người | Một hồ sơ cá nhân trong Stage (có giấy tờ cá nhân). Một người có thể xuất hiện ở nhiều ô trên sơ đồ (D-005). |
| Tài sản `k` | Một trong tối đa 3 tài sản của hồ sơ (`k ∈ {1,2,3}`). |
| Chủ đất của `k` | Người có dấu "Chủ" trên tài sản `k` (`ownPositions` chứa `k`). |
| Người nhận của `k` | Người có dấu "Nhận" trên tài sản `k` (`receivePositions` chứa `k`). |
| Vòng di sản | Phần tài sản `k` mà một người đang nắm tại ngày người đó chết, đem chia. |
| Đơn vị | Một suất trong hàng 1 của một vòng: mỗi cha, mẹ, vợ/chồng là một đơn vị; mỗi con (kể cả con chết trước được thế vị) là một đơn vị nhánh. |
| Nhánh | Một con của người để lại di sản cùng toàn bộ hậu duệ được gắn của con đó, tới chắt. |
| Từ chối (nhãn nghiệp vụ) | Người có suất mà không có dấu "Nhận" trên tài sản đó (D-024). **Không** phải văn bản từ chối theo Điều 620. |

## 2. Bất biến tính toán

| Mã | Bất biến |
|---|---|
| INV-1 | Tính bằng phân số chính xác; phần trăm chỉ để hiển thị. |
| INV-2 | Quan hệ chỉ lấy từ liên kết tường minh (cha/mẹ, vợ/chồng), không suy từ vị trí, nhãn, thế hệ. |
| INV-3 | Mỗi tài sản tính độc lập. Mỗi vòng bảo toàn: phần đã chia + phần chưa có người nhận = giá trị vòng. Tổng mỗi tài sản luôn = 1. |
| INV-4 | Kết quả không phụ thuộc thứ tự dữ liệu vào; cùng dữ liệu cho cùng kết quả. |
| INV-5 | Một người nhận từ nhiều nguồn/vai thì cộng dồn. |
| INV-6 | Không mở vòng giá trị 0. |
| INV-7 | App không tạo người, không đoán quan hệ, không kết luận điều không có trên sơ đồ (D-015). |
| INV-8 | Mọi số hiển thị và in ra Word đọc từ cùng một kết quả của cùng một bản đã lưu (D-003). |

## 3. Quy tắc phạm vi

| Mã | Điều kiện | Kết quả | Nguồn | Lệch luật? |
|---|---|---|---|---|
| R-01 | Mọi hồ sơ | Chỉ chia **thừa kế theo pháp luật**. Không xử lý di chúc, phần bắt buộc. | BLDS 650.1(a), 644; D-026 | Giới hạn phạm vi |
| R-02 | Người đã thành thai nhưng chưa sinh lúc mở thừa kế | Không xét; chỉ người có giấy tờ cá nhân mới được đưa vào. Khách hàng tự chịu trách nhiệm. | BLDS 613, 660.1, 662.1; D-026 | **Lệch**: luật buộc dành lại một suất cho thai nhi trước khi chia (660.1); thai nhi sinh ra còn sống sau khi đã chia thì phát sinh người thừa kế mới (662.1). App bỏ qua để đơn giản; trách nhiệm thuộc khách |
| R-03 | Bất kỳ | App không xác định ai phải ký; ai có tên trong Stage là người liên quan. | BLDS 656; D-027 | **Lệch** (không can thiệp): luật yêu cầu thoả thuận của những người thừa kế, app không kiểm |
| R-04 | Bất kỳ | Chỉ tính hàng thừa kế thứ nhất. Hàng 2, 3 không tính; khi người chết không có ai thuộc hàng 1 trên sơ đồ thì vòng đó `unsupported` (R-15). | BLDS 651; BR cũ | Giới hạn phạm vi |
| R-05 | Bất kỳ | Áp quy tắc BLDS 2015 cho mọi ngày mở thừa kế; không có logic theo phiên bản luật. | D-021 (tạm; Q-002) | **Lệch tạm**: luật áp dụng là luật tại thời điểm mở; owner đánh giá quy tắc ổn định |
| R-06 | Bất kỳ | Tối đa **3** tài sản mỗi hồ sơ, ở mọi nơi (nhập, tính, Word). | D-029 | Kỹ thuật |
| R-30 | Người chết có nghĩa vụ tài sản (nợ, chi phí mai táng…) | App **không** khấu trừ nghĩa vụ trước khi chia; chia toàn bộ phần đứng tên. | BLDS 615, 658 | **Lệch** (giới hạn phạm vi, có chủ ý): luật buộc thanh toán nghĩa vụ trước khi chia; app chỉ chia quyền sử dụng/sở hữu đứng tên, việc thanh toán do các bên tự thoả thuận ngoài app |
| R-31 | Thời điểm mở thừa kế đã lâu | App **không** cảnh báo thời hiệu. | BLDS 623 | **Lệch** (giới hạn phạm vi, có chủ ý): luật có thời hiệu yêu cầu chia di sản; app không kiểm, công chứng viên tự đánh giá |

## 4. Quy tắc dữ liệu và quan hệ

| Mã | Điều kiện | Kết quả | Nguồn | Lệch luật? |
|---|---|---|---|---|
| R-07 | Ngày chết trống hoặc không đọc được | Coi là **còn sống**. | D-001 | **Lệch**: luật cần chứng cứ chết; app giảm nhập liệu. Ngoại lệ của INV-7 ("coi là còn sống" là một kết luận) — chờ owner quyết ở Q-013 |
| R-08 | So thứ tự chết của hai người | Cả hai có ngày đủ: so ngày. Khác năm: so năm. **Cùng năm và ít nhất một người chỉ có năm** (kể cả cả hai cùng chỉ có năm): "không xác định thứ tự". Một người ngày đủ, người kia chỉ năm, khác năm: so năm. Ngày dạng **tháng/năm** (`mm/yyyy`) không thuộc định dạng nhận (`yyyy`, `dd/mm/yyyy`, ISO) nên hiện rơi vào R-07 (coi là còn sống) — khoảng trống, cần nhập lại dạng năm. | D-007 | **Lệch** (quy ước nhập): luật không quy định ngày thiếu |
| R-09 | Hai người chết cùng ngày, hoặc "không xác định thứ tự" | Không thừa kế của nhau; nếu một người là con của người kia thì áp thế vị (R-17). | BLDS 619, 652; D-006 | **Lệch (quy ước)**: 619 nói "cùng thời điểm"; app coi **cùng ngày** là cùng thời điểm, không xét giờ chết, để đơn giản nhập liệu |
| R-10 | Con trên sơ đồ | "Con" gồm con đẻ và con nuôi, không phân loại. Mỗi con gắn tối đa 1 cha + 1 mẹ (được trống). Con chỉ hưởng từ cha/mẹ **được gắn**. | BLDS 651.1(a), 653, 654; D-023 | **Lệch**: (1) giới hạn 1 cha + 1 mẹ nên không biểu diễn được con nuôi vẫn hưởng của cha mẹ đẻ (653) hay con riêng hưởng của cả cha/mẹ đẻ lẫn bố dượng/mẹ kế (654), cũng không biểu diễn chiều bố dượng/mẹ kế hưởng của con riêng; (2) con riêng – bố dượng/mẹ kế chỉ hưởng khi user tự gắn, app không xét điều kiện nuôi dưỡng. Lý do: mô hình sơ đồ đơn giản (mỗi ô một cặp cha mẹ) |
| R-11 | Vợ/chồng | Mỗi người có **tối đa một** vợ/chồng = vợ/chồng hợp pháp **cuối cùng**. Liên kết phải hai chiều. Vợ/chồng cũ không có suất; chỉ dùng làm cha/mẹ của con để phân biệt con chung/con riêng. | BLDS 651, 655; HNGĐ 65; D-022 | **Lệch**: trường hợp 655 (đang ly hôn, tái hôn sau) do user tự chọn ai là vợ/chồng cuối cùng |
| R-12 | Cha mẹ của người chết | = hai người được gắn làm cha/mẹ của người đó (tối đa 1 cha + 1 mẹ). | BLDS 651.1(a), 653 | **Lệch**: người chết là con nuôi có thể có cả cha mẹ đẻ và cha mẹ nuôi trong hàng 1 (653); app chỉ biểu diễn được một cặp (cùng lý do R-10) |

## 5. Quy tắc chia

| Mã | Điều kiện | Kết quả | Nguồn | Lệch luật? |
|---|---|---|---|---|
| R-13 | Tài sản `k` có `n` chủ đất | Mỗi chủ đất có phần gốc `1/n` của `k`. Hai vợ chồng cùng là chủ → mỗi người 1/2. | BLDS 612; HNGĐ 33, 66; D-020, D-017 | **Lệch** khi giấy tờ ghi tỷ lệ không đều: app luôn chia đều |
| R-14 | Một người chết khi đang nắm phần `p > 0` của `k` | Mở một vòng giá trị `p` tại ngày chết. Các vòng xử lý theo thứ tự ngày; các vòng cùng ngày, hoặc không xác định được ai chết trước (R-08), được coi là cùng thời điểm (619): lấy giá trị đồng thời trước khi chia bất kỳ vòng nào trong nhóm đó. Phần của người chết về 0 sau khi chia. | BLDS 611, 612, 619 | Không |
| R-15 | Vòng của người X | Đơn vị hàng 1 = cha, mẹ (R-12), vợ/chồng (R-11) **còn sống lúc X chết và là người nhận của `k`**, hoặc **chết sau X** (R-16); cộng mỗi con của X (R-10) mà nhánh còn ít nhất một người nhận (R-17, R-19). Giá trị vòng chia **đều** cho các đơn vị. Có người hàng 1 trên sơ đồ nhưng không còn đơn vị nào (tất cả từ chối theo R-19/R-21) → giá trị vòng là "chưa có người nhận", trạng thái `incomplete`. Không có người hàng 1 nào trên sơ đồ (cần hàng 2/3) → `unsupported` mã `heir_rank_not_supported` (R-04, D-002, D-026). | BLDS 651.1(a), 651.2, 651.3 | Không (hàng 2/3 là giới hạn phạm vi, R-04) |
| R-16 | Người thừa kế (hàng 1 hoặc thế vị) chết **sau** X | Vẫn hưởng phần của mình tại lúc X chết (**chuyển tiếp**), luôn coi là nhận (không áp R-19 vì người chết không thể khai). Phần đó mở vòng mới khi người này chết (R-14). | BLDS 613, 614; D-010 | Không (quy ước "luôn nhận" là của app) |
| R-17 | Con C của X chết **trước, cùng lúc, hoặc không xác định thứ tự** với X | Thế vị: nhánh C chia đều cho các con được gắn của C; cháu cũng ở tình huống đó thì xuống chắt, chia đều từng cấp trong nhánh. Phần thế vị không thuộc di sản của C. Vợ/chồng của C không nhận phần thế vị. | BLDS 652; D-016 | Không |
| R-18 | Thế vị phải xuống **dưới chắt** để có người nhận | Dừng ở chắt; hồ sơ trạng thái `unsupported` mã `representation_depth_exceeded`, không đưa phân số. | BLDS 652; D-012 | **Lệch / giới hạn phạm vi**: theo luật nhánh không có người thế vị trong giới hạn chắt chỉ không thành đơn vị và vòng vẫn chia được; app chọn thận trọng trả `unsupported` |
| R-19 | Người có suất (hàng 1 hoặc thế vị), còn sống lúc X chết, **không** có dấu Nhận trên `k` | Coi là **từ chối** phần của mình trên `k`. Chủ đất không có dấu Nhận vẫn giữ phần gốc R-13, chỉ không nhận thêm. | BLDS 620, 621; D-024 | **Lệch**: luật đòi văn bản từ chối (620) và tách riêng người không được quyền hưởng (621); app gộp cả hai (và cả "nhường theo thoả thuận") vào nhãn "từ chối", user sửa tay khi khác. Đây cũng là ngoại lệ của INV-7 (app kết luận từ việc thiếu dấu) — chờ owner quyết ở Q-013 |
| R-20 | Có người từ chối (R-19) trong một nhánh thế vị | Phần của họ **ở lại nhánh**: chia đều cho những người còn nhận trong nhánh, theo từng cấp. Cả nhánh không còn ai nhận → nhánh không thành đơn vị; giá trị chia đều cho các đơn vị còn lại của vòng (R-15). | BLDS 651.2, 652; D-024 (nhãn từ chối nghiệp vụ, không phải văn bản 620); D-025, D-011 | **Lệch nghiệp vụ** (theo D-011): cách hiểu suất gắn với nhánh và cách chia lại khi nhánh rỗng là quy ước của app |
| R-21 | Người là đơn vị trực tiếp (cha, mẹ, vợ/chồng, con còn sống) từ chối | Không thành đơn vị; giá trị chia đều cho các đơn vị còn lại. | BLDS 651.2; D-024 (nhãn từ chối nghiệp vụ, không phải văn bản 620) | Không (ngoài lệch đã ghi ở R-19) |
| R-22 | Một người nhận từ nhiều vòng/vai | Cộng dồn (INV-5). | D-005 | Không |

## 6. Quy tắc thao tác sơ đồ và lưu

| Mã | Điều kiện | Kết quả | Nguồn | Lệch luật? |
|---|---|---|---|---|
| R-23 | Mỗi tài sản | Dấu Chủ/Nhận đặt riêng cho từng người × tài sản; tính riêng từng tài sản. | D-008 | Kỹ thuật |
| R-24 | Dấu chọn trỏ tới tài sản không còn tồn tại | Tự gỡ, kèm cảnh báo. | Kỹ thuật | Không |
| R-25 | Lỗi cấu trúc: vợ/chồng một chiều hoặc xung đột, cha/mẹ trỏ tới ô không có, quá 2 cha/mẹ, tự làm cha/mẹ/vợ chồng mình, vòng tổ tiên **thật** | **Vẫn lưu** nguyên trạng, trạng thái `invalid` kèm danh sách lỗi; không đưa phân số; Word in nhãn lỗi. | D-002, D-030 | Kỹ thuật |
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
| R-06 | Hồ sơ/UI giới hạn 3; xuất Word cho tới 5 (`MAX_WORD_ASSETS = 5`). Hoãn sửa (D-029). |
| R-08 | Ngày chỉ năm bị ép thành 01/01, mất cờ "chỉ năm". |
| R-18 | Engine không kiểm độ sâu, đi xuống không giới hạn. |
| R-23 | Bước chuyển dữ liệu gộp dấu theo tài sản thành một cờ chung; engine tính một kết quả cho mọi tài sản. |
| R-25, R-28 | Lỗi cấu trúc chặn cả xem kết quả lẫn lưu (`diagram_invalid_state`). |
| R-11 | UI coi một chiều là vợ chồng; server đòi hai chiều → lỗi. |
| R-15 | Engine trả `incomplete` (unresolved) cả khi không có ai hàng 1; chưa có mã `heir_rank_not_supported`. |
| R-26 | Kiểm vòng tổ tiên báo nhầm khi một người được tới bằng hai đường. |
| R-27 | Chưa đối chiếu với code gỡ node. |
| INV-8 | Lưu nhiều bản sao; Word có thể đọc bản cũ hoặc tỷ lệ của bảng người tham gia. |

## 9. Ánh xạ D-xxx → R-xx

D-001→R-07 · D-002→R-25, R-28 · D-003→INV-8 · D-004→R-29 · D-005→R-22 ·
D-006→R-09 · D-007→R-08 · D-008→R-23 · D-009→R-27 · D-010→R-16 ·
D-011→R-20 · D-012→R-18 · D-013/D-020→R-13 · D-014/D-024→R-19 · D-015→INV-7 ·
D-016→R-17 · D-017→R-13 · D-021→R-05 · D-022→R-11 · D-023→R-10 ·
D-025→R-20 · D-026→R-01, R-02 · D-027→R-03 · D-028→R-29 · D-029→R-06 ·
D-030→R-25, R-26 · D-031→R-27. R-30, R-31 không có D (lệch có chủ ý, ghi từ review độc lập 26/10/2026). (D-018, D-019 là quy trình.)

## 10. Câu hỏi mở Q-xxx

Q-001, Q-003…Q-012 đã chốt (xem ánh xạ §9 và decision-80). Còn mở:

| Q | Câu hỏi | Trạng thái |
|---|---|---|
| Q-002 | Thừa kế mở trước 01/01/2017 có điểm nào luật cũ khác ảnh hưởng hồ sơ đất? | Mở, ưu tiên thấp; tạm theo R-05 (D-021); cần giải thích lại cho owner |
| Q-013 | R-07 (ngày trống = còn sống, kể cả cha mẹ ghi "chết đã lâu" không ngày) và R-19 (không dấu Nhận = từ chối) là kết luận app tự rút ra, mâu thuẫn INV-7. Giữ hay đổi? | Mở, chờ owner |

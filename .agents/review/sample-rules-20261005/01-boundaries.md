# Nhận diện văn bản và ranh giới từng bản ghi — chờ duyệt

Bảng này chi tiết hóa A02–A06 trong [dàn ý](00-outline.md). Đây là quy tắc dự kiến rút từ bộ mẫu S01–S20, chưa phải spec và chưa được đưa vào engine. Dấu hiệu trong bảng là chữ đã thấy; cách gom dữ liệu là đề xuất, trừ những quyết định người dùng đã chốt.

## Cách đọc

Tách theo thứ tự: **file → từng văn bản → vùng có vai trò rõ → từng Người/thửa/bộ giấy → từng trường**. Một vùng Người có thể nằm ở phần đầu hoặc trong điều khoản riêng. “Kết thúc vùng Người” không có nghĩa kết thúc cả văn bản.

`p17` nghĩa là đường dẫn `/body/p[17]` được công cụ đọc Word trả về; `paraId` là mã đoạn khi công cụ dùng mã thay số. `tbl/tr/tc` lần lượt là bảng/hàng/ô. Riêng S07/S20 là số đoạn của Word vì nguồn là `.doc`. Các vị trí chỉ dùng tra lại đúng bản mẫu đã lưu mã băm; không phải số cố định dùng viết engine.

## Nhận loại và chọn vùng chính

| Mã | Cấu trúc và dấu nhận diện đã thấy | Vùng Người: bắt đầu → kết thúc | Vùng đất/giấy: bắt đầu → kết thúc | Mẫu chứng minh |
|---|---|---|---|---|
| D01 | `HỢP ĐỒNG CHUYỂN NHƯỢNG…` hoặc `HỢP ĐỒNG TẶNG CHO…`; tiếp `Chúng tôi gồm có:` | Nhãn bên chuyển nhượng/tặng cho và bên nhận → trước câu `Hai bên tự nguyện…` mở nội dung | `ĐIỀU 1: ĐỐI TƯỢNG…`, mô tả quyền sử dụng đất → trước mục chuyển sang thỏa thuận/giá; không lấy thửa gốc thành tài sản giao dịch khác | S01 p4–24; S02 p4–28 |
| D02 | `HỢP ĐỒNG ỦY QUYỀN` + các bên | `I. BÊN ỦY QUYỀN`, `II. BÊN NHẬN ỦY QUYỀN` → trước `Hai bên tự nguyện thỏa thuận…` | `ĐIỀU 1: CĂN CỨ ỦY QUYỀN`, mô tả thửa và GCN → trước `ĐIỀU 2: NỘI DUNG ỦY QUYỀN` | S04 p4–28; Người p6–16, câu mở nội dung p17; đất p19–26, mục kế p28 |
| D03 | `GIẤY UỶ QUYỀN`; `Tôi là:`/`Chúng tôi là:` | Khối người ủy quyền; khối riêng sau `Nay bằng giấy này … uỷ quyền cho:` → trước `Được thay mặt, nhân danh…` | Có thể không có đất; cũng có thể chỉ ghi địa chỉ/GCN, thiếu số thửa/tờ/diện tích | S03 p4–11; S15 p4–14 |
| D04 | `VĂN BẢN PHÂN CHIA DI SẢN` | Người lập; `I. Người để lại di sản:`; `III. Người thừa kế:` và các nhóm bố mẹ/vợ con → hết từng tiểu vùng, trước ký/lời chứng | `II. Di sản:` → trước `III. Người thừa kế:` | S05 p4–53; đất p13–22 |
| D05 | `VĂN BẢN TỪ CHỐI NHẬN DI SẢN` | `Tôi là:` và đoạn người để lại di sản → trước đoạn mô tả tài sản tương ứng | `Phần quyền sử dụng đất…` và các nhãn thửa → trước `Bằng Văn bản này, tôi… tự nguyện từ chối…` | S06: tiêu đề `7432E439`; người khai `28181FDD`; người chết `36A7EC4A`; tài sản mở `14F665D9`, thuộc tính cuối `29977F85`, đoạn kế `280A9DDA` |
| D06 | `DI CHÚC`; có trang bìa trước nội dung | `tôi là:` trong phần mở đầu và khối người được hưởng sau câu để lại tài sản → hết khối nhân thân; dừng trước `NGƯỜI LẬP DI CHÚC`/vùng làm chứng | `I. Về tài sản:` + GCN rồi bảng mô tả đất → `II. Định đoạt tài sản:` | S07 Word P39–74; Người P40–42/P63–66; đất P46–61, mục kế P62; bảng T1 có cột tờ/thửa/diện tích |
| D07 | `VĂN BẢN CAM KẾT TÀI SẢN RIÊNG` | `Chúng tôi gồm có:` + hai người và địa chỉ chung → trước nội dung cam kết | Đoạn trúng đấu giá thửa/lô p13 và diễn giải p14 → trước `Hai vợ chồng chúng tôi cam đoan:` p15. Thiếu GCN vẫn giữ tài sản đã mô tả | S08 p4–16; đất p13–14 |
| D08 | `BIÊN BẢN HỌP GIA ĐÌNH` | `Chúng tôi là những người thừa kế hợp pháp…` + danh sách → trước câu xác nhận và mục `Người chứng kiến:`; khối đại diện trong nội dung cần giữ riêng vị trí | Khối đại diện được giao xử lý tài sản + mô tả GCN/thửa → `Gia đình chúng tôi cam đoan…` | S14 p10–38; danh sách p11–26; chứng kiến p29–30; đại diện lặp p32; đất p32–37 |
| D09 | Hợp đồng thế chấp có đoạn văn | Tên vai trò `BÊN NHẬN THẾ CHẤP`/`BÊN THẾ CHẤP` → câu mở thỏa thuận. Mở thêm vùng riêng `Người có nghĩa vụ được bảo đảm:` → mục nghĩa vụ kế tiếp | `Điều 1. Tài sản thế chấp`; các nhóm đất, công trình, giấy tờ sở hữu → trước `4. Giá trị Tài sản bảo đảm` | S09 Người p11–25/p65–66; tài sản/giấy p27–46; giá p47 |
| D10 | Hợp đồng thế chấp có bảng nhân thân và đoạn đất dài | Nhãn bên + bảng tương ứng → `CÁC BÊN THỎA THUẬN NHƯ SAU:`. Trong nghĩa vụ còn có đoạn người vay trực tiếp | `ĐIỀU 2. TÀI SẢN BẢO ĐẢM` + `(i)/(ii) quyền sử dụng đất…` → `ĐIỀU 3. GIÁ TRỊ…` | S16 bảng 1–2; câu đóng `73EA9650`; người vay `14C2E555`; đất `0D372655`/`7C580C73`; đóng `5C13FE0D` |
| D11 | File chỉ có `LỜI CHỨNG CỦA CÔNG CHỨNG VIÊN` | `CHỨNG NHẬN:` + câu hợp đồng/văn bản được giao kết + nhãn các bên → trước câu `Các bên đã…` hoặc `Người có tên nêu trên đã…` tương ứng | Chỉ trả tài sản nếu chính vùng này mô tả. Không tìm sang file hợp đồng bên cạnh | S13 lời chứng ủy quyền; S18 thế chấp p6–16; S19 sửa đổi: mở `621C0AB7`, các bên `03322BB8`/`4E6EA905`, đóng `589D4C0C`. Công chứng viên bị loại |
| D12 | `VĂN BẢN THOẢ THUẬN VỀ VIỆC HUỶ` + `HỢP ĐỒNG THẾ CHẤP…` | Các bên/ngân hàng Word P7–24 → nội dung thỏa thuận | Đoạn dẫn đất/GCN Word P26 trong nội dung hủy; vẫn thuộc phần chính → hết mô tả, trước nội dung khác/ký; lời chứng bắt đầu P45 | S20; không nhầm P24 là cuối toàn bộ vùng chính |
| D13 | Đơn theo Mẫu 18, các mục đánh số | `1. Người sử dụng đất…`, `a. Tên…`, giấy tờ, địa chỉ → `2. Nội dung…` | Nội dung thay đổi/giấy kèm chỉ tạo tài sản khi có mô tả trực tiếp. Nhắc tên loại GCN trong checklist chưa đủ | S10; S12 đơn 1 p5–12/đơn 2 p24–31; S17 p8–13 |
| D14 | Các tờ khai thuế/lệ phí, nhãn `[04]`, `[41.1]`… | Mục người nộp thuế/người chuyển giao/người nhận; kết thúc khi chuyển mục vai trò hoặc nhóm giấy/tài sản. Các loại địa chỉ giữ đúng nhãn thuế | Nhóm `Thông tin về đất`, `ĐẶC ĐIỂM NHÀ ĐẤT`, `Thửa đất chịu thuế` → nhóm nhà/công trình/người chuyển giao/nhóm thuế kế tiếp tương ứng | S12: tiêu đề p43/p155/p218; đất p94–107/p170–181/p237–248 |
| D15 | Phiếu yêu cầu đăng ký biện pháp bảo đảm trong bảng | Các hàng người yêu cầu, bên bảo đảm, bên nhận bảo đảm → hết hàng vai trò | Hàng `5. Mô tả tài sản bảo đảm` → trước hàng `6. Giấy tờ kèm theo` | S11 bảng 1: Người hàng 5–10; tài sản hàng 11; giấy kèm hàng 12 |
| D16 | `ĐƠN XIN TRẢ LẠI ĐẤT`; biên bản kiểm tra hiện trạng là văn bản riêng kế tiếp | Đơn: `Tên tôi là` → hết giấy/địa chỉ trước mô tả đất. Biên bản: `I- THÀNH PHẦN GỒM` → hết thành phần; phạm vi Người đối với cán bộ chưa chốt | Đơn: câu hai thửa và GCN → câu chuyển bản đồ mới, rồi nội dung đề nghị. Biên bản: khối mô tả đất riêng; không điền ngược vào đơn | S17: đơn p40–54, Người p45–47, đất p48–49; biên bản p60–97, thành phần p68–79, đất p84 |

Đây là các cấu trúc đã quan sát, **chưa chốt thành 16 bộ engine độc lập**. Nhiều dòng dùng chung các thành phần nhận tên, giấy tờ, địa chỉ và thửa; chỉ khác cách tìm vùng và gán vai trò. Chưa xác nhận bộ mẫu bao phủ đủ danh sách khoảng 30 loại văn bản người dùng thường gặp.

## Một file chứa nhiều văn bản

| Mã | Bắt đầu/kết thúc thực tế | Quy tắc dự kiến |
|---|---|---|
| V01 | S12: đơn 1 p1–19 + bảng 1; đơn 2 p20–37 + bảng 2; thuế thu nhập mở p40/p43, cam đoan p149 + bảng ký; lệ phí trước bạ mở p153/p155, cam đoan p213 + bảng ký; thuế đất mở mã mẫu p216/tiêu đề p218 | Mỗi văn bản có mã vùng riêng. Tên/ngày/GCN trong văn bản sau không bù văn bản trước. p270 là phần cơ quan chức năng của tờ khai thứ năm, không phải đầu một văn bản mới |
| V02 | S17: đơn biến động p1–22 và bảng ký; đơn trả đất mở p37/p40, kết thúc p53–54 và bảng ký; biên bản mở p56/p60, câu kết p92, ký tới p97 | Không xem tên lặp qua ba văn bản là căn cứ tự gộp Người. Không dùng số dòng tổng chưa duyệt làm đáp án chấm |
| V03 | S01/S20 hợp đồng có lời chứng nối phía sau; S13/S18/S19 chỉ lời chứng đứng riêng | Phân biệt lời chứng kèm và lời chứng độc lập bằng cấu trúc file/văn bản. Lời chứng kèm không là nguồn tìm bù; lời chứng độc lập đọc các bên ngay trong chính nó |

## Ranh giới một Người, một tài sản, một bộ giấy

| Mã | Dấu hiệu bắt đầu | Dấu hiệu kết thúc | Cách gom dự kiến và trường hợp phải tránh | Bằng chứng |
|---|---|---|---|---|
| R01 | Danh xưng + tên trong vùng các bên: `Ông`, `Bà`, `Ông/bà:`, có thể sau số thứ tự/dấu đầu dòng/quan hệ vợ chồng | Người kế tiếp cùng cấp hoặc mốc đóng vùng. Tên kết thúc trước nhãn sinh/chức vụ/giấy; khối Người còn tiếp qua các đoạn giấy/địa chỉ | Không mặc định một đoạn là một Người; không bắt buộc đủ ngày sinh/CCCD mới giữ khối đã nhận ra | S01 p7–13; S02 p8–18; S14 p11–26 |
| R02 | `Tôi là:`, `tôi là:` sau phần mở đầu; `Tên tôi là` | Nhãn trường kế tiếp kết thúc tên; người/vùng nội dung kế tiếp kết thúc khối | Áp dụng đúng vùng người khai; câu `Tôi,… Công chứng viên` không mở Người cần trích | S03 p5–7; S07 Word P39–42; S17 p45–47 |
| R03 | Nhãn tên trong biểu mẫu/ô bảng: `a. Tên:`, `Họ tên:`, `Họ và tên`, `Tên người nộp thuế` | Kết thúc ô/nhãn kế tiếp cho tên; hết nhóm mục của chủ thể cho bản ghi | Không đòi có Ông/Bà. Với nhãn đặt ở ô riêng, lấy giá trị từ ô đúng hàng/cột. Ô gộp cần giữ cấu trúc; không đọc lại giá trị hai lần | S10 mục 1; S11 bảng 1; S12 p49/p79/p222 |
| R04 | Câu quan hệ có đích rõ `Bố đẻ … là ông …`, `Mẹ đẻ … là bà …`, các mục `i. Bà`, `ii. Ông` | Hết khối nhân thân; người kế tiếp hoặc tiểu mục kế tiếp | Tên trước `là ông/bà` có thể là người đang được nói đến, không phải người mới. Một người chết thiếu CCCD vẫn là khối có dữ liệu | S05 p25–42 |
| R05 | `Cả hai cùng thường trú tại:` và các biến thể câu chung đã thấy | Hết địa chỉ/nhãn kế tiếp | Gán địa chỉ cho đúng cặp vừa được giới thiệu trong cùng nhóm; không gán cho mọi Người của cả file | S02 p12/p18; S08 p10; S15 p10; S19 `47936435` |
| R06 | `Đại diện:`, `Người đại diện:` trong khối ngân hàng | Trước căn cứ đại diện/bên kế tiếp; các trường cá nhân có thể nằm cùng câu | Tạo Người từ phần cá nhân; giữ chức vụ. Địa chỉ/MST/giấy đăng ký ngân hàng không sang Người đại diện | S09 p16–17; S16 bảng 2 hàng 5; S18 p10–12 |
| R07 | Nhãn giấy cá nhân `Căn cước…`, `CCCD…`, `CC/CCCD…`; giấy cũ được ghi rõ trong ngoặc hoặc cụm `trước đây` | Trước giấy kế tiếp/địa chỉ/người kế tiếp; ngày/nơi cấp theo đúng giấy | Nhiều bộ số/ngày/cơ quan thuộc một Người. Cùng số khác lần cấp vẫn giữ hai bản giấy; chỉ nối CMND 9 số ↔ căn cước 12 số khi nguồn ghi rõ | S15 p7; S20 Word P15; S16 `14C2E555` |
| R08 | Cụm `theo Trích lục khai tử…` bên người chết | Hết số/cơ quan/ngày ký của chính trích lục | Giữ giấy khai tử khác giấy căn cước. Ngày chết khác ngày ký; `ký ngày` chưa tự đổi thành `cấp ngày` | S05 p11/p26; S06 `36A7EC4A` |
| R09 | Đề mục đất + mô tả thửa; thửa có thể ghi sau đoạn GCN | Thửa giao dịch kế tiếp hoặc mốc đóng nhóm đất; giấy chung có phạm vi riêng | Mỗi thửa giao dịch một tài sản. Số thửa cũ/thửa gốc trong cùng mô tả chưa làm phát sinh tài sản khác | S01 p16–22; S02 p21–28 |
| R10 | `(i) quyền sử dụng đất…`, `(ii) quyền sử dụng đất…` | Mục cùng cấp kế tiếp hoặc mốc đóng vùng | Hai mục mô tả hai thửa. Mục `(iii) tất cả các tài sản…`, `(iv) tất cả các quyền, lợi ích…` là điều khoản chung, không tự tạo thửa mới | S16 `0D372655`, `7C580C73`, `17C653C9`, `2E8915BF` |
| R11 | Hai cụm `thửa đất số…` trong một đoạn mô tả đất giao dịch | Mô tả thửa tiếp theo; phần căn cứ GCN chung giữ riêng phạm vi | Tách hai thửa; có thể dùng chung serial. Không cộng diện tích, không đoán phần diện tích chưa nêu loại | S17 p48: hai thửa dùng một GCN |
| R12 | Mô tả tài sản trong một ô bảng hoặc qua bảng có cột thửa/tờ/diện tích | Hết hàng/khối mô tả trước nhóm giấy kèm hoặc vùng kế tiếp | Nhãn và giá trị có thể nằm khác ô; không nối mọi ô thành chuỗi rồi mất quan hệ hàng/cột | S11 bảng 1 hàng 11; S07 Word P48–61 |
| R13 | Địa chỉ/GCN hoặc thửa cụ thể trong vùng tài sản nhưng thiếu vài trường | Hết mô tả trực tiếp | Vẫn trả tài sản thiếu để sửa ở Stage. `22 thửa đất` trong tên giấy đấu giá không tạo 22 tài sản | S08 p13; S15 p11; S20 Word P26 |
| R14 | Đoạn GCN đi với thửa/các thửa; các trường `số`, `số vào sổ`, cơ quan và ngày cấp | Trước hợp đồng/quyết định/giấy khác hoặc hết khối giấy | Giữ đúng loại số/ngày. GCN chung thuộc các thửa mà câu đang mô tả; danh sách đính kèm không tự tạo GCN đủ thông tin | S01 p16; S09 p41–46; S12 p69–77; S17 p48 |
| R15 | Tên ngân hàng trong vùng bên nhận thế chấp/nhận bảo đảm | Nhãn trụ sở/địa chỉ/đăng ký/đại diện kế tiếp | Giữ nguyên cả tên + chi nhánh + PGD thành một chuỗi. Mỗi giấy ủy quyền có bộ số/ngày/bên ban hành riêng; không chỉ lấy giấy đầu tiên | S09 p12–17; S18 p7–11; S19/S20 có nhiều căn cứ |
| R16 | `Người chứng kiến:`, `NGƯỜI LÀM CHỨNG`, vai trò `Công chứng viên` | Hết vùng vai trò đó | Loại vai trò này theo quyết định đã chốt. Tên tổ chức công chứng/địa chỉ văn phòng không phải địa chỉ Người của hồ sơ | S14 p29–30; S07 Word P76 trở đi; S18 p3–4 |
| R17 | Tiêu đề tên Người rồi dòng trường `Họ tên:` trong chính khối đó | Người/vùng tiếp theo; mỗi nhãn trường không tự đóng khối | Đề xuất đọc tiêu đề và các trường ngay dưới thành một khối, giữ cả vị trí tên. Không tạo thêm Người chỉ vì có thêm nhãn tên trong khối đang mở; khác việc tự gộp hai khối lặp ở hai vùng | S09 p19 là tiêu đề tên, p20 là `Họ tên:` và ngày sinh, p21–25 là giấy/địa chỉ/điện thoại |

## Thành phần dùng chung cần có

| Mã | Thành phần | Giới hạn cụ thể từ mẫu |
|---|---|---|
| C01 | Chữ hoa/thường, cách mã hóa dấu tiếng Việt, khoảng trắng/tab, khoảng trắng không ngắt dòng, dấu hai chấm | Chuẩn hóa bản dùng tìm kiếm; giữ nguyên chữ nguồn và vị trí. S18 có khoảng trắng đặc biệt trong `Chức vụ :`; tiêu đề S20 có dấu tiếng Việt ghép từ nhiều ký tự; không sửa bản gốc |
| C02 | Danh xưng/nhãn có phần giống nhau | Xử lý trọn `Ông/bà` trước `Ông`, `Căn cước công dân` trước nhãn ngắn; không trả tên bắt đầu bằng `/bà`. S14 không cho căn cứ đoán giới tính |
| C03 | Nhãn → giá trị cùng đoạn/đoạn sau/ô bên cạnh | S12 nhãn số giấy ở p51, số ở p52; nhãn ngày/nơi cấp ở p53. Không coi xuống đoạn là trường không có giá trị ngay |
| C04 | Mốc dừng theo từng trường/vùng | Tên dừng ở nhãn ngày sinh/chức vụ; địa chỉ dừng ở nhãn/vùng kế tiếp, không ở mọi dấu chấm/chấm phẩy. S03 có `P.`/`TP.`; địa chỉ S18 p9 có dấu `;` bên trong |
| C05 | Ngày và độ đầy đủ | Đã thấy `dd/mm/yyyy`, khoảng trắng quanh `/`, `ngày … tháng … năm …`. Nhãn `Sinh năm`/`năm sinh` có thể ghi ngày đầy đủ. Nếu nguồn chỉ có năm thì không tự thêm ngày/tháng; chưa có ví dụ năm riêng trong bộ 20 để chốt biến thể |
| C06 | Diện tích và đơn vị | `m2`, `m²`, dấu phẩy thập phân; tách tổng/từng loại/riêng/chung/nhà. S12 loại đất 0 m² không tạo tài sản mới, nhưng không vì có giá trị 0 mà bỏ bản ghi cha |
| C07 | Cụm ngoặc/cũ–mới/căn cứ | Giữ phạm vi ngoặc `nay là…`, `số CMND cũ…`; số QĐ và ngày QĐ là căn cứ riêng. Chưa tự lựa chọn giá trị cũ/mới vào một ô Stage |
| C08 | Ô/dòng để trống | Dấu chấm, ô tên trống, ngày mẫu trống, chữ lỗi `#REF!` khác dữ liệu thật. Giữ được khối đã nhận diện; báo nguồn trống/lỗi thay vì tự tìm bù |

Không mở việc xác nhận lại bằng chữ ký/lời chứng hoặc tự thử lại bộ khác sau lớp đánh giá. Xung đột giữa các dấu hiệu cần được giải quyết bằng phạm vi và ví dụ cụ thể khi duyệt bộ rule.

## Các phần vẫn chưa chốt

- Tên chỉ dẫn chiếu trong câu tài sản, hoặc khối nhân thân lặp trong **vùng chính**: chưa tự tạo mọi tên thành Người, cũng chưa tự gộp theo tên/số giấy.
- Cán bộ/đại diện cơ quan trong biên bản kiểm tra S17: chưa chốt phạm vi Người cần trả.
- Nhiều loại địa chỉ hoặc giá trị cũ–mới nhưng Stage chỉ có một ô: giữ nhãn nguồn trong bản trích dự kiến; cách nhập chưa được quyết định.
- Cách trình bày nhiều văn bản trong một file, chỗ lưu dữ liệu ngân hàng, giao diện nhiều phiên bản giấy: chưa thiết kế trong lượt này.

Bằng chứng chi tiết: [Người](people-evidence.md), [tài sản theo mẫu Người](people-assets-evidence.md), [ngân hàng/thế chấp](bank-evidence.md), [biểu mẫu](forms-evidence.md). Đây là tài liệu để duyệt cấu trúc và dấu hiệu, không chứng minh engine hiện tại đã nhận đúng.

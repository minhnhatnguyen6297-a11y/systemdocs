# Dấu hiệu từng trường — lọc theo mẫu, chờ duyệt

Giữ mã N/T/H/B của [bảng 56 mục trước](../field-recognition-20261005.md) để tiện duyệt. Tên trường dùng trao đổi, chưa phải tên khóa database. Chỉ các nhãn có dẫn chứng dưới đây mới được gọi là **đã thấy trong bộ mẫu**; một nhãn in sẵn với ô trống không chứng minh đã có dữ liệu để trích.

Đọc bảng cùng [ranh giới](01-boundaries.md). Một nhãn chỉ áp dụng bên trong đúng Người/thửa/giấy/ngân hàng. “Dừng ở nhãn kế tiếp” nghĩa là nhãn hợp lệ trong vùng hiện tại, không phải mọi chữ giống một nhãn xuất hiện trong câu mô tả.

## Người và giấy tờ cá nhân — N01–N21

| Mã / trường | Dấu hiệu đã thấy trong mẫu | Cách lấy giá trị và dấu kết thúc dự kiến | Mẫu/vị trí; giới hạn |
|---|---|---|---|
| N01 — Tên người | `Ông`, `Bà`, `Ông/bà:`, `Tôi là:`, `tôi là:`, `Tên tôi là`; `Họ tên:`, `a. Tên:`, `a. Tên Ông:`, `Tên ông(bà)`, `Họ và tên`, `Tên người nộp thuế`; sau `Đại diện:`, `Người đại diện:`, `Và vợ là bà`, `Bố đẻ … là ông …` | Bỏ trọn danh xưng/nhãn; lấy tên đến nhãn ngày sinh/chức vụ/giấy, dấu phân cách thực sự của mẫu hoặc cuối ô tên. Khối Người có thể tiếp ở đoạn sau | S01 p7/p11; S03 p5; S05 p26–27; S07 Word P39–40; S09 p16/p20; S10 mục 1; S12 p49/p79/p222; S14 p11; S17 p9/p45. Không dùng mọi `ông/bà` trong câu làm đầu Người mới |
| N02 — Ngày sinh | `Sinh ngày:`, `Ngày sinh:`, `Sinh năm:`, `năm sinh:` | Đọc giá trị ngày ngay sau nhãn; dừng trước trường kế tiếp. Xét giá trị, không ép nhãn “năm” chỉ được có bốn chữ số | S01 p7; S05 p27 ghi `Sinh năm: 01/01/1943`; S09 p20/p66. Cách ghi dấu gạch/chấm ngày chưa có ví dụ được xác minh trong bộ này |
| N03 — Chỉ năm sinh | Chưa xác minh được ví dụ chỉ bốn chữ số trong bộ 20 | Nếu nguồn chỉ ghi năm thì giữ năm; không tạo ngày/tháng. Cần mẫu chứng minh riêng trước khi gọi đây là biến thể đã bao phủ | Giữ mục để duyệt; không lấy `Sinh năm` có ngày đầy đủ ở S05 làm bằng chứng “chỉ năm” |
| N04 — Giới tính | Danh xưng `Ông`, `Bà`; có cả nhãn không rõ `Ông/bà:` | Nếu ánh xạ danh xưng thì chỉ dùng danh xưng xác định trong khối Người. `Ông/bà` giữ chưa rõ; không đoán từ tên | S01 p7/p11; S14 p11/p15/p19/p23. Nhãn `Giới tính: Nam/Nữ` chưa được xác minh ở các mẫu này |
| N05 — Số giấy cá nhân | `Căn cước số:`, `Căn cước công dân số:`, `CC số:`, `CCCD:`, `số CCCD:`, `CCCD số:`, `CC/CCCD số`; `[06] Số CMND/CCCD/Hộ chiếu`, `Định danh cá nhân…`; nhãn dài `Giấy chứng minh nhân dân/ Căn cước công dân/Hộ chiếu/Căn Cước:` | Lấy giá trị ngay sau nhãn/cùng ô/đoạn giá trị kế tiếp; dừng trước nhãn cấp/ngày/cơ quan/giấy khác. Không bắt mọi số 9/12 chữ số của văn bản thành căn cước | S01 p8/p12; S09 p21/p66; S12 p51–53/p225; S15 p7; S16 `14C2E555`; S20 Word P11/P14. Hộ chiếu mới thấy nhãn chung/ô trống, chưa thấy số hộ chiếu được điền |
| N06 — Loại giấy | `Căn cước`, `Căn cước công dân`, `CCCD`, `CC`, `CMND`; nhãn kết hợp `CMND/CCCD/Hộ chiếu`, `CC/CCCD` | Giữ tên/nhãn giấy. Nhãn kết hợp không chỉ rõ loại thì giữ chưa rõ, không tự xác nhận loại chỉ từ độ dài số | S01; S15 p7; S16 `14C2E555`; S12 p51/p54 |
| N07 — Ngày cấp giấy | `cấp ngày`, `ngày cấp:`, `Ngày cấp:` | Đọc ngày thuộc bộ giấy đang mở, dừng trước nhãn/cơ quan/giấy tiếp theo. Có dạng nhãn riêng và dạng câu `do … cấp ngày …` | S01 p8; S09 p21; S12 p53/p82; S20 Word P11/P14/P15/P22. Không lấy ngày văn bản ủy quyền ngân hàng |
| N08 — Nơi cấp giấy | `do … cấp ngày …`, `nơi cấp:`, `Nơi cấp:` | Dạng câu lấy cơ quan giữa `do` và `cấp ngày`; dạng nhãn lấy đến trường/vùng kế tiếp. Thuộc đúng bộ giấy, kể cả giấy cũ trong ngoặc | S01 p8/p12; S09 p21/p66; S12 p53/p82; S15 p7 |
| N09 — Số giấy cũ/phiên bản trước | `(số CMND cũ là: …)`, cụm căn cước `trước đây` | Mở bộ giấy riêng trong khối cùng Người; lấy số, rồi các trường cấp của chính bộ đó. Không tạo Người thứ hai | S15 p7 CMND 9 số đi cùng giấy 12 số; S20 Word P15 hai phiên bản cùng số. Chỉ S15 hỗ trợ liên kết CMND ↔ căn cước được nói rõ |
| N10 — Ngày cấp giấy cũ | `cấp ngày` trong cụm giấy cũ/phiên bản trước | Cùng quy tắc N07 nhưng phạm vi là bộ giấy cũ; không ghi đè ngày giấy mới | S15 p7; S20 Word P15 |
| N11 — Nơi cấp giấy cũ | `do … cấp ngày` trong cụm giấy cũ/phiên bản trước | Cùng quy tắc N08 nhưng phạm vi là bộ giấy cũ; không ghi đè cơ quan giấy mới | S15 p7; S20 Word P15 |
| N12 — Địa chỉ cư trú/thường trú | `Nơi thường trú tại:`, `Thường trú tại:`, `Cư trú tại:`, `Nơi thường trú:`, `Địa chỉ nơi cư trú:`, `c. Địa chỉ:`; người chết có `Nơi thường trú cuối cùng trước khi chết:` | Lấy đến nhãn/vùng kế tiếp; giữ trọn địa chỉ và ngoặc cũ–mới. Giữ loại địa chỉ nguồn; nhãn `Địa chỉ` trong đơn không tự xác nhận là thường trú | S01 p9; S03 p7/p10; S05 p11/p26; S09 p22; S10 mục 1; S14 p17/p21/p25; S17 p11; S20 Word P9/P13. S03 có `P.`/`TP.`, không dừng ở dấu chấm |
| N13 — Tạm trú | `Nơi tạm trú:`, `địa chỉ tạm trú:` | Lấy trong khối Người hiện tại đến trường kế; giữ khác thường trú và địa chỉ hiện tại | S09 p23/p66. Cách chọn một địa chỉ vào Stage chưa chốt |
| N14 — Chỗ ở/địa chỉ hiện tại | `Địa chỉ hiện tại:`, `[08] Địa chỉ chỗ ở hiện tại:` | Lấy đến nhóm trường kế tiếp. Giữ nhãn gốc, không tự đổi thành thường trú | S09 p24; S12 p56 |
| N15 — Địa chỉ dùng chung | `Cả hai cùng thường trú tại:`, `Cả hai ông bà cùng thường trú tại:`, câu `cùng thường trú…` sau cặp người | Lấy một địa chỉ, gán phạm vi đúng cặp vừa nêu trong nhóm; không tạo Người thứ ba từ câu địa chỉ | S02 p12/p18; S08 p10; S15 p10; S19 `47936435`. Không gán cho đại diện ngân hàng ở nhóm khác |
| N16 — Ngày chết | `chết ngày` | Đọc ngày gắn với Người chết trong khối; dừng trước dẫn giấy khai tử/câu kế. Ngày chết khác ngày ký khai tử | S05 p11/p26; S06 `36A7EC4A`. Biến thể `Từ trần ngày`/`Mất ngày` chưa xác minh trong 20 mẫu |
| N17 — Số trích lục khai tử | `theo Trích lục khai tử số`, `Trích lục khai tử (Bản sao) số:` | Giữ toàn bộ số giấy tới `do`/nhãn cơ quan/ngày ký. Chữ `Bản sao` là thành phần mô tả, không đổi giấy thành căn cước | S05 p11/p26; S06 `36A7EC4A` |
| N18 — Ngày trên giấy khai tử | `ký ngày` trong cụm trích lục | Lấy ngày ký; giữ nghĩa nguồn. Chưa coi “ký”/“cấp”/“đăng ký” là một nghĩa chung | S05 p11/p26; S06 `36A7EC4A`. Cách đưa vào trường database còn phải xác định |
| N19 — Cơ quan trên giấy khai tử | `do … ký ngày …` | Lấy cơ quan giữa `do` và `ký ngày` trong bộ khai tử; không thành địa chỉ hoặc nơi cấp căn cước | S05 p11/p26; S06 `36A7EC4A` |
| N20 — Điện thoại cá nhân | `Số điện thoại:`, `Điện thoại:`, nhãn điện thoại/email trong đơn | Lấy giá trị của điện thoại trước email/nhãn kế; ô trống giữ trống. Không lấy điện thoại ngân hàng cho đại diện | S09 p25; S10 `297D72A3`; S15 p13; S17 p12. Nhãn không có giá trị chưa chứng minh trích được số |
| N21 — Chức vụ đại diện | `Chức vụ:`, `Chức vụ :`; nhãn chức vụ ở bảng ngân hàng | Lấy từ nhãn tới giấy/căn cứ đại diện hoặc mốc đóng ô; không nối chức vụ vào tên Người | S09 p16; S16 bảng 2 hàng 5; S18 p10; S19 `30909A24`; S20 Word P23 |

## Đất và giấy chứng nhận — T01–T16

| Mã / trường | Dấu hiệu đã thấy trong mẫu | Cách lấy giá trị và dấu kết thúc dự kiến | Mẫu/vị trí; giới hạn |
|---|---|---|---|
| T01 — Địa chỉ đất | `có địa chỉ tại:`, `có địa chỉ tại`, `Địa chỉ:`, `Địa chỉ thửa đất:`, `[41.2] Địa chỉ`, `[17] Địa chỉ thửa đất` | Chỉ trong khối thửa/đất. Dừng trước `theo Giấy chứng nhận…` hoặc nhãn kế phù hợp; giữ ngoặc `nay là…`. Các ô địa chỉ thuế có thể chia xã/tỉnh riêng | S01 p16/p22; S05 p17; S09 p34; S11 hàng 11; S12 p96/p239; S16 hai đoạn đất; S20 Word P26. Không mượn địa chỉ Người khi nguồn đất thiếu |
| T02 — Số thửa | `Thửa đất số:`, `thửa đất số`, `[41.1] Thửa đất số (Số hiệu thửa đất)` | Lấy số đến nhãn tờ/diện tích/câu chuyển thửa. Phân biệt vai trò giao dịch, gốc, cũ, tách; không chỉ tìm mọi lần chữ “thửa” | S01 p17; S02 p21–28; S12 p95; S16 `(i)/(ii)`; S17 p48 |
| T03 — Số tờ bản đồ | `tờ bản đồ số:`, `tờ bản đồ số`, `Tờ bản đồ số (số hiệu)` | Lấy số và giữ cụm biến đổi thuộc trường nếu có; dừng trước diện tích/nhãn kế | S01 p17; S14 p32 có cũ–mới; S16 `(i)/(ii)`; S17 p48–49. Không tự chọn cũ/mới |
| T04 — Diện tích tổng | `Diện tích:`, `diện tích`, nhãn diện tích trong bảng mô tả toàn thửa | Lấy số và đơn vị thuộc **toàn thửa**; dừng trước bằng chữ/hình thức/loại/nhãn kế. Không cộng các loại đất để điền thay | S01 p18; S05 p18; S09 p30; S07 bảng đất; S12 p180; S16 `(i)/(ii)`; S17 p48. **S12 tờ khai thu nhập p95–107 không ghi tổng riêng**, chỉ có diện tích theo loại |
| T05 — Loại đất/mục đích | `Loại đất:`, `Mục đích sử dụng:`, `mục đích sử dụng đất:`, `Loại đất1:…`; tên đầy đủ hoặc mã | Lấy từng mục đích/loại; giữ diện tích và thời hạn cùng dòng/cùng loại nếu nguồn có. Mã cũ–mới giữ cả cụm | S01 p19; S05 p20; S12 p101–104; S14 hai loại; S16 hai đoạn. Danh mục mã đất đầy đủ chưa xác lập ở đây |
| T06 — Diện tích từng loại | `ONT: …`, `CLN: …`; `Loại đất1: … Diện tích: …`; mã `ODT (nay là ONT): …` | Thuộc loại đang mở, không thay tổng. Dòng loại 0 m² không là một tài sản mới; cách giữ dòng loại 0 trong kết quả chưa chốt | S05 p20; S12 p101–104; S14 p32–37; S17 p48. Không suy diện tích chưa phân loại của thửa S17 |
| T07 — Thời hạn sử dụng | `Thời hạn sử dụng:`, `thời hạn sử dụng đất:`; giá trị `Lâu dài`, ngày, cũ–mới | Lấy đến nhãn kế. Nếu có nhiều loại thì gắn đúng loại; giữ `nay là…` cùng thời hạn | S01 p20; S05 p21; S14 p32–37; S16 `(i)/(ii)` |
| T08 — Nguồn gốc sử dụng | `Nguồn gốc sử dụng:`, `Nguồn gốc đất` | Lấy mô tả đến nhãn/mốc vùng kế. `#REF!` ghi là lỗi có sẵn trong nguồn, không một nguồn gốc hợp lệ | S04 p19–26; S05 p22; S12 p106 |
| T09 — Hình thức sử dụng | `Hình thức sử dụng:`, `hình thức sử dụng:`; `Riêng`, `Chung` trong nhóm này | Giữ hình thức và các phần diện tích riêng/chung theo nhãn. Không gộp với sở hữu nhà | S01 p21; S04 mô tả đất; S05 p19; S16 `(i)/(ii)` |
| T10 — Diện tích sử dụng riêng | `Riêng: … m2`, `sử dụng riêng: … m2` | Lấy diện tích thuộc nhãn riêng, không thay tổng chỉ vì bằng nhau | S05 p19; S16 `(i)/(ii)` |
| T11 — Diện tích sử dụng chung | `Chung: … m2`, `sử dụng chung: Không` | Giữ số/đơn vị hoặc chữ `Không` đúng nguồn; không tự biến thành số tổng hoặc tự chuẩn hóa “Không” thành 0 khi chưa duyệt | S05 p19; S16 `(i)/(ii)` |
| T12 — Serial/số phát hành GCN | `Giấy chứng nhận … số`, `Giấy chứng nhận …: Số …`, `[30.1] Số` trong nhóm giấy QSDĐ | Lấy chuỗi đến nhãn vào sổ/cơ quan/giấy khác. Giữ chữ, khoảng trắng, số đúng nguồn; không ép hai chữ cái, không bắt buộc, không dùng làm khóa duy nhất tài sản | S01 p16; S02 p21–28; S07 Word P47; S09 p43; S12 p70; S14 đất; S17 p48; S20 Word P26 |
| T13 — Số vào sổ GCN | `Số vào sổ cấp Giấy chứng nhận:`, `Số vào sổ cấp GCN số:`, `số vào sổ cấp GCN:` | Lấy chuỗi số vào sổ; phân biệt cụm `QĐ số…` đi kèm. Không cắt máy móc mọi `/`/`QĐ` vì số vào sổ cũ có thể tự chứa các thành phần đó | S01 p16; S05 p15; S09 p43; S14 số vào sổ cũ; S16 hai đoạn đất. Ranh giới trường hợp số vào sổ cũ cần duyệt bằng nguyên văn mẫu |
| T14 — Ngày cấp GCN | `do … cấp ngày`, `[30.3] Cấp ngày` | Lấy ngày cấp của đúng GCN. Ngày quyết định/ngày tách thửa/ngày cập nhật/ngày hợp đồng là trường dẫn chiếu riêng | S01 p16; S02 đất và giấy tách; S07 Word P47; S09 p43 ghi ngày bằng chữ; S12 p70; S16 hai đoạn; S20 Word P26 |
| T15 — Cơ quan cấp GCN | `do … cấp ngày`, `[30.2] Do cơ quan` | Lấy cơ quan cấp trong bộ GCN tới nhãn cấp/giấy kế; không lấy cơ quan chứng thực hợp đồng | S01 p16; S05 p15; S09 p43; S12 p70 so với p77; S16 hai đoạn |
| T16 — Giá trị cũ–mới/biến động | `(nay là …)`, `nay là tờ bản đồ số…`, `ODT (nay là ONT)`, `Theo bản đồ đo đạc hiện trạng năm…`; cụm cập nhật biến động | Gắn với đúng địa chỉ/tờ/loại/thời hạn/giấy. Phần mới để chấm thì giữ trống, không chép số cũ vào. Không tự gọi tra cứu địa chỉ để sửa kết quả gốc | S05 p20; S07 giấy; S14 đất; S16 hai đoạn; S17 p49 |

Năm trường đất cần hoàn thiện ở Stage đã chốt: địa chỉ, số thửa, số tờ, diện tích tổng, loại đất. Yêu cầu đó không dùng để loại tài sản còn thiếu khỏi kết quả trích.

## Nhà/công trình — chỉ giữ phạm vi đã liệt kê, H01–H07

Không mở thêm câu hỏi hoặc nghiệp vụ nhà ở trong tài liệu này. Các mục vẫn được đối chiếu vì có trong bảng 56 mục trước.

| Mã / trường | Dấu hiệu thấy được | Cách đọc dự kiến / giới hạn | Mẫu/vị trí |
|---|---|---|---|
| H01 — Phần nhà/công trình | `2. Tài sản gắn liền với đất chưa được cấp GCN quyền sở hữu`, `Loại nhà:`, `[42] Thông tin về nhà ở, công trình xây dựng` | Nhận đúng vùng; tên phôi GCN có chữ “nhà ở” chưa chứng minh có nhà thật. Không tự mở thêm tài sản đất | S09 p36–40; S12 p108 trở đi |
| H02 — Diện tích xây dựng | `Diện tích xây dựng:` | Lấy diện tích trong từng mô tả công trình tới nhãn diện tích sàn/nhãn kế; không thay tổng đất | S09 p37–39 |
| H03 — Diện tích sàn | `diện tích sàn:` | Lấy trong cùng công trình; không cộng thành đất hoặc trộn giữa ba công trình | S09 p37–39 |
| H04 — Kết cấu | `Kết cấu:` | Mô tả có dấu phẩy/chấm; dừng trước nhãn tiếp theo, không ở mọi dấu câu | S09 p37–39 |
| H05 — Số tầng | `Nhà ở 3 tầng` | Lấy thông tin tầng trực tiếp trong loại nhà; không suy số tầng từ diện tích sàn/xây dựng | S09 p37; mới có một kiểu có giá trị được xác minh |
| H06 — Cấp/hạng công trình | Chưa xác minh được nhãn có giá trị trong bộ 20 | Giữ mục để bổ sung mẫu; không đưa toàn bộ biến thể giả định thành dấu hiệu đã thấy | Có trong danh sách tham khảo Upload Lab; chưa đủ bằng chứng mẫu của lượt này |
| H07 — Hình thức sở hữu nhà | Chưa xác minh được nhãn có giá trị trong bộ 20 | Không lấy `Sử dụng riêng/chung` của đất thành sở hữu nhà | Giữ mục chờ mẫu; không suy giá trị |

## Ngân hàng và căn cứ đại diện — B01–B12

| Mã / trường | Dấu hiệu đã thấy trong mẫu | Cách lấy giá trị và dấu kết thúc dự kiến | Mẫu/vị trí; giới hạn |
|---|---|---|---|
| B01 — Tên ngân hàng | Tên `NGÂN HÀNG … – CHI NHÁNH …`; có cả `-PGD …`; trong khối bên nhận thế chấp/nhận bảo đảm | Giữ nguyên cả cụm thành một chuỗi JSON; dừng trước trụ sở/giấy đăng ký/nhãn khác, không tách ở dấu gạch nối | S09 p12; S16 bảng 2; S18 p7; S19 `45AF9EB6`; S20 Word P17. Tên khóa/chỗ lưu chưa thiết kế |
| B02 — Địa chỉ ngân hàng | `Trụ sở tại:`, `Địa chỉ:`, `Địa chỉ đăng ký:`; nhãn địa chỉ trong bảng | Giữ toàn địa chỉ và ngoặc cũ–mới. Dừng trước trường ngân hàng/đại diện kế; không dừng ở dấu `;` bên trong địa chỉ | S09 p13; S16 bảng 2; S18 p9; S19 `7D688820`; S20 Word P18 |
| B03 — Mã số thuế | `Mã số thuế` | Lấy đúng nhãn MST; không đổi mã đăng ký chi nhánh/giấy hoạt động thành MST chỉ vì giống định dạng | S19 `2E3B35ED`; S11 bảng 1 có nhãn mã tổ chức. Không là số căn cước đại diện |
| B04 — Giấy đăng ký/mã chi nhánh | `Mã số ĐK chi nhánh:`, `Giấy CNĐKDN: Số`, `Giấy chứng nhận đăng ký hoạt động số:` | Giữ số và loại nhãn; dừng trước cơ quan/ngày/địa chỉ. Không gom các loại mã thành một loại đã xác nhận | S09 p14; S18 p8; S20 Word P20 |
| B05 — Ngày đăng ký/cấp đầu | `đăng ký lần đầu ngày`; `cấp ngày` trước cụm thay đổi trong giấy đăng ký hoạt động | Lấy ngày đúng giấy; hỗ trợ ngày viết bằng chữ. Không dùng thay ngày cấp căn cước của đại diện | S18 p8; S20 Word P20. S20 không ghi nguyên nhãn `cấp lần đầu ngày` |
| B06 — Cơ quan đăng ký/cấp | S18: `do … đăng ký lần đầu ngày…`; S20: `do … cấp ngày…` trong giấy đăng ký hoạt động | Lấy cơ quan thuộc giấy tổ chức tới mốc ngày/cấp/thay đổi; giữ nghĩa nguồn, không đổi hai nhãn thành cùng nghĩa đã xác nhận | S18 p8; S20 Word P20 |
| B07 — Lần/ngày thay đổi đăng ký | `Đăng ký thay đổi lần thứ … ngày …`, `thay đổi lần thứ … ngày …` | Lấy lần và ngày tương ứng; tách ngày đầu khỏi ngày thay đổi | S18 p8; S20 Word P20 |
| B08 — Người đại diện | `Người đại diện:`, `Đại diện:`; nhãn người ký trong bảng ngân hàng | Tách Người với N01–N21, vẫn giữ nếu thiếu sinh/CCCD. Không gán địa chỉ/giấy ngân hàng cho họ | S09 p16; S16 bảng 2 hàng 5; S18 p10; S19 đại diện; S20 Word P21–22 |
| B09 — Số căn cứ đại diện | `(Theo Quyết định số:`, `và văn bản số:`, `(Theo văn bản ủy quyền số:`, `(Theo giấy ủy quyền số:`, `và giấy ủy quyền số`, `và theo quyết định số:` | Mỗi giấy có loại/số riêng; dừng trước ngày/bên ban hành hoặc giấy tiếp theo. Không chỉ lấy giấy đầu | S09 p17; S16 bảng 2 hàng 5 có hai giấy; S18 p11; S19 `702E0E4E` hai quyết định; S20 Word P24 hai giấy |
| B10 — Ngày căn cứ đại diện | `ngày`, `ký ngày` theo từng giấy trong B09 | Gắn ngày với đúng số giấy trước đó; giữ nhãn ngày/ký ngày, không lấy mọi ngày trong đoạn rồi trộn các bộ | S09 p17; S18 p11; S19 `702E0E4E`; S20 Word P24 |
| B11 — Bên ban hành căn cứ | `của …` sau số/ngày giấy | Giữ bên/chức danh ghi trong chính căn cứ. Tên người được nhắc là người ban hành chưa tự tạo thêm Người của hồ sơ | S09 p17; S18 p11; S19 căn cứ; S20 Word P24 |
| B12 — Điện thoại/fax | `Điện thoại:`, `Fax:` | Hai giá trị riêng; cùng dòng có tab vẫn tách theo nhãn. Không chuyển sang điện thoại cá nhân | S09 p15; S20 Word P19 |

## Biến thể ở bảng trước chưa được bộ mẫu này chứng minh

Các ví dụ sau **không bị kết luận là sai**. Chúng cần mẫu hoặc phép kiểm riêng trước khi đưa vào phạm vi “đã bao phủ”.

| Nhóm | Ví dụ chưa có bằng chứng trong bộ được xác minh |
|---|---|
| Tên | `Anh:`, `Chị:`, các kiểu không dấu như `Ong`, `Ba`; bảng/code cũ có thể nhắc nhưng không thay mẫu đối chứng |
| Sinh | Năm sinh chỉ bốn số; ngày dạng `01-02-1980`, `01.02.1980`; nhãn `Ngày, tháng, năm sinh` |
| Giấy cá nhân | Số hộ chiếu có chữ được điền; `CMTND`, `Chứng minh thư nhân dân`, `Cấp tại`, `Cấp bởi`, `Cấp đổi ngày` |
| Cư trú | `HKTT`, `Đăng ký hộ khẩu thường trú`, `Chỗ ở hiện nay`; không tự cộng mọi nhãn dự đoán vào danh sách đã quan sát |
| Khai tử | `Từ trần ngày`, `Giấy chứng tử số`, `Đăng ký khai tử ngày`; chỉ giữ nhóm trích lục đã có mẫu |
| Đất/nhà | `Tọa lạc tại`, `Tổng diện tích`, `Diện tích chiếm đất`; cấp/hạng nhà, hình thức sở hữu nhà có giá trị; chưa khảo sát đủ để gọi các biến thể là hoàn thiện |

## Cách duyệt

Có thể duyệt theo mã, ví dụ: “N01 giữ các nhãn đã thấy; N03 chờ mẫu; T13 giữ nguyên chuỗi số vào sổ; B04 giữ đúng loại mã.” Không cần duyệt các tên khách hàng. Dữ liệu thật và vị trí đối chiếu nằm trong [manifest](../../brainstorming/brainstorm-trich-van-ban-2026-10-04/sample-answers/selected-samples.json), [đáp án nháp](../../brainstorming/brainstorm-trich-van-ban-2026-10-04/sample-answers/answers-draft.md) và các bảng bằng chứng liên kết từ [README](README.md).

Tài liệu này chưa chứa biểu thức regex chạy được, chưa đo độ chính xác và chưa thay đổi code/spec/plan.

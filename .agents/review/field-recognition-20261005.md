# Bảng dấu hiệu nhận biết từng trường — chờ Owner duyệt

Ngày: 05/10/2026. Tạm dừng hỏi brainstorming; tài liệu này phục vụ duyệt dấu hiệu nhận biết, chưa phải spec hoặc bộ rule đã triển khai. Các tên trường dưới đây dùng để trao đổi, chưa phải tên khóa database/API.

**Đã tìm thấy tài liệu:** [catalog Upload Lab](../../docs/spec/upload_lab/regex-rules.md). Catalog mô tả loại văn bản và vùng dữ liệu, chưa liệt kê đủ dấu hiệu từng trường. Bảng dưới diễn giải thêm từ [code trích xuất](../../upload_lab/extract_contract.py), đặc biệt các dòng 989–1118. Cột cuối là biến thể đề xuất, không khẳng định code đã hỗ trợ.

**Cách đọc:** “Bắt đầu bằng” là chữ đứng trước giá trị trong vùng dữ liệu phù hợp. Ví dụ `Ngày sinh: 01/02/1980` → lấy `01/02/1980`. Dấu hiệu giúp tìm trường; không có nghĩa gặp chữ đó ở mọi nơi đều tạo bản ghi. Các nhãn có dấu `:` và không có dấu `:` được liệt kê khi cần phân biệt hành vi hiện tại.

Upload Lab đang trả tài sản thành **cả đoạn mô tả**. Các ô “chưa tách” dưới đây có thể vẫn xuất hiện trong đoạn đó nhưng chưa được bóc thành trường riêng. Các dấu hiệu nhà ở đang có chủ yếu dùng để phân loại có công trình; bảng chỉ ghi nhận, không mở thêm nghiệp vụ nhà ở.

## Bảng duyệt

| Mã | Trường | Dấu hiệu trong Upload Lab hiện tại | Biến thể bổ sung / nội dung để duyệt |
|---|---|---|---|
| N01 | **Tên người — `tennguoi`** | Đầu dòng `Ông`, `Ông:`, `Bà`, `Bà:`; nhận cả `Ong`, `Ba`, chữ hoa/thường. Có thể đứng sau số thứ tự dạng `1.`, dấu `-`/`*`, `Đại diện:`, `Đại diện theo ủy quyền:`, `Người chồng -`, `Người vợ -`, `và vợ là`, `và chồng là`, `người vợ`, `người chồng`, `và`. Sau các cụm này vẫn cần `Ông/Bà` theo nghĩa một trong hai danh xưng. | **`Ông/bà`, `Ông/bà:`, `Tôi là`, `Tôi là:`, `Tên tôi là`, `Tên tôi là:`, `Họ tên`, `Họ tên:`, `Họ và tên`, `Họ và tên:`.** `Tôi là:` hiện chỉ mở vùng từ chối di sản; nếu tiếp ngay tên không có Ông/Bà thì chưa lấy được. Chuỗi viết liền `Ông/bà` hiện bị bắt sai, xem ghi chú kiểm tra. |
| N02 | **Ngày sinh — `ngaysinh`** | `Sinh ngày`, `Sinh ngày:`, `Ngày sinh`, `Ngày sinh:`; cả `Sinh ngay`, `Ngay sinh`. Giá trị hiện nhận dạng ngày/tháng/năm với dấu `/`, ngày/tháng có 1 hoặc 2 chữ số. | **`Năm sinh`, `Năm sinh:`, `Sinh năm`, `Sinh năm:`, `Sinh ngày tháng năm`, `Ngày, tháng, năm sinh`, `Ngày tháng năm sinh`**. Thực tế có nhãn “Năm sinh” nhưng giá trị là ngày đầy đủ. Biến thể cách ghi ngày: `01-02-1980`, `01.02.1980`, `ngày 01 tháng 02 năm 1980`. |
| N03 | **Chỉ có năm sinh — `namsinh`** | Chưa có rule lấy riêng năm sinh bốn chữ số. | `Năm sinh: 1980`, `Sinh năm 1980`, `Sinh: 1980`. Giữ đúng mức thông tin nguồn có; không tự thêm ngày/tháng. |
| N04 | **Giới tính — `gioitinh`** | Lấy danh xưng `Ông` hoặc `Bà` từ đầu dòng Người; giá trị code hiện ghi là danh xưng. Chưa đọc nhãn “Giới tính”. | `Giới tính: Nam`, `Giới tính: Nữ`. `Ông/bà` không chỉ rõ giới tính; không đoán từ tên. |
| N05 | **Số giấy tờ — `sogiayto`** | `Căn cước`, `Căn cước công dân`, `CCCD`, `CMND`; có hoặc không có `số` và `:`. Có biến thể `Can cuoc`, `Can cuoc cong dan`, `so`. Lấy dãy chữ số ngay sau nhãn. | `Số căn cước`, `Số CCCD`, `Số CMND`, `Chứng minh nhân dân`, `Chứng minh thư nhân dân`, `CMTND`, `Số định danh cá nhân`. Hộ chiếu là biến thể đề xuất riêng, cần giữ cả chữ và số nếu duyệt. |
| N06 | **Loại giấy tờ — `loaigiayto`** | Nhận ra các từ Căn cước/CCCD/CMND để tìm số, nhưng kết quả hiện đều đưa số vào một ô `cccd`; chưa giữ loại thành trường riêng. | Giữ nhãn nguồn: `Căn cước`, `Căn cước công dân`, `Chứng minh nhân dân`; `Hộ chiếu` nếu được bổ sung. |
| N07 | **Ngày cấp giấy tờ — `ngaycap`** | `cấp ngày`, `cap ngay` rồi đến ngày/tháng/năm có dấu `/`. Rule hiện chưa nhận dấu `:` ngay sau “cấp ngày”. | `Cấp ngày:`, `Ngày cấp`, `Ngày cấp:`, `Được cấp ngày`, `Cấp lần đầu ngày`, `Cấp đổi ngày`. Gắn với đúng giấy đang mô tả. |
| N08 | **Nơi cấp giấy tờ — `noicap`** | Lấy chữ giữa **`do … cấp ngày`** hoặc `do … cap ngay`; cơ quan cấp phải nằm trước cụm “cấp ngày”. | `Nơi cấp`, `Nơi cấp:`, `Cơ quan cấp`, `Cơ quan cấp:`, `Cấp tại`, `Cấp bởi`; dạng `cấp ngày … tại …`. |
| N09 | **Số giấy tờ cũ / phiên bản trước** | CMND được nhận như một số giấy tờ thông thường; chưa có rule bóc nhiều giấy của cùng Người hoặc quan hệ giấy cũ–mới. | `CMND cũ`, `Số CMND cũ`, `CMND trước đây`, `Trước đây sử dụng CMND`, `CCCD trước đây`, `Căn cước trước đây`, `Giấy tờ trước đây`. Các dấu hiệu chỉ phân biệt bộ giấy; liên kết 9 số ↔ 12 số phải được nguồn thể hiện rõ theo quyết định đã có. |
| N10 | **Ngày cấp giấy tờ cũ / phiên bản trước** | Chưa tách riêng khỏi ngày cấp giấy đầu tiên tìm được trong khối Người. | Các nhãn ở N07, khi nằm trong chính cụm giấy cũ/phiên bản trước. |
| N11 | **Nơi cấp giấy tờ cũ / phiên bản trước** | Chưa tách riêng khỏi nơi cấp giấy đầu tiên tìm được trong khối Người. | Các nhãn ở N08, khi nằm trong chính cụm giấy cũ/phiên bản trước. |
| N12 | **Địa chỉ cư trú / thường trú** | Đầu dòng `Thường trú tại`, `Cư trú tại`, `Nơi thường trú tại`, `Nơi cư trú tại`, `Địa chỉ nơi cư trú`, `Địa chỉ đăng ký`; có hoặc không có `:`. | `Thường trú`, `Nơi thường trú`, `Địa chỉ thường trú`, `Đăng ký thường trú tại`, `Đăng ký hộ khẩu thường trú tại`, `Hộ khẩu thường trú`, `HKTT`, `Trú tại`, `Cư trú`, `Địa chỉ`. Nhãn “Địa chỉ” chỉ dùng trong vùng Người để tránh lấy địa chỉ đất/ngân hàng. |
| N13 | **Địa chỉ tạm trú** | Chưa có nhãn riêng. | `Tạm trú tại`, `Tạm trú`, `Nơi tạm trú`, `Địa chỉ tạm trú`, `Đăng ký tạm trú tại`. |
| N14 | **Chỗ ở / địa chỉ hiện tại** | Chưa có nhãn riêng. | `Chỗ ở hiện nay`, `Nơi ở hiện nay`, `Nơi ở hiện tại`, `Địa chỉ hiện tại`, `Hiện cư trú tại`, `Hiện ở tại`. |
| N15 | **Dấu hiệu địa chỉ dùng chung** | Cho phép thêm `Cùng` hoặc `Cả hai ông bà` hoặc `Cả hai ông bà cùng` trước các nhãn ở N12. Đây là dấu hiệu câu chung, chưa bảo đảm tự gán cho đủ hai Người. | `Cả hai cùng`, `Hai người cùng`, `Cả hai vợ chồng cùng`, `Cùng địa chỉ`, `Cùng nơi thường trú`. Cần giữ phạm vi nhóm người mà câu đang nói đến. |
| N16 | **Ngày mất — `ngaymat`** | Chưa có trường/rule riêng. | `Chết ngày`, `Mất ngày`, `Ngày chết`, `Ngày mất`, `Đã chết ngày`, `Đã mất ngày`, `Từ trần ngày`. |
| N17 | **Số giấy khai tử / trích lục khai tử** | Chưa có trường/rule riêng. | `Giấy chứng tử số`, `Giấy khai tử số`, `Trích lục khai tử số`, `Trích lục chứng tử số`, `Đăng ký khai tử số`. |
| N18 | **Ngày cấp / đăng ký khai tử** | Chưa có trường/rule riêng. | `Cấp ngày`, `Ngày cấp`, `Đăng ký ngày`, `Đăng ký khai tử ngày` trong cụm giấy khai tử. Giữ đúng nhãn cấp/đăng ký; khác với ngày mất. |
| N19 | **Cơ quan cấp / đăng ký khai tử** | Chưa có trường/rule riêng. | `Do … cấp`, `Nơi cấp`, `Cơ quan cấp`, `Đăng ký tại` trong cụm giấy khai tử. |
| N20 | **Điện thoại cá nhân** | Chưa có trường/rule riêng. | `Điện thoại`, `Số điện thoại`, `ĐT`, `SĐT`, `Điện thoại liên hệ`, `Di động`. |
| N21 | **Chức vụ người đại diện** | `Chức vụ:` / `Chuc vu:` được dùng làm điểm dừng tên và dấu hiệu giữ dòng Người; chưa bóc giá trị chức vụ thành trường riêng. | `Chức vụ`, `Chức danh`, `Giữ chức vụ`; ví dụ `Giám đốc`, `Phó Giám đốc`, `Trưởng phòng giao dịch` khi văn bản ghi rõ cùng tên đại diện. |
| T01 | **Địa chỉ đất — `diachidat`** | Có dấu hiệu mở cả đoạn: `quyền sử dụng đất … có địa chỉ tại`, `nhà ở và quyền sử dụng đất ở … có địa chỉ tại`. Chưa lấy địa chỉ thành ô riêng. | `Địa chỉ thửa đất`, `Địa chỉ đất`, `Thửa đất tại`, `Địa chỉ`, `Tọa lạc tại`, `Toạ lạc tại`, `Tại` trong mô tả thửa đất. |
| T02 | **Số thửa — `sothua`** | Chưa bóc thành trường riêng. | `Thửa đất số`, `Thửa số`, `Số thửa`, `Số thửa đất`, `Thuộc thửa đất số`. Khi có thửa gốc/thửa tách/thửa cũ phải giữ nhãn, không coi mọi số là các tài sản ngang nhau. |
| T03 | **Số tờ bản đồ — `soto`** | Chưa bóc thành trường riêng. | `Tờ bản đồ số`, `Tờ bản đồ`, `Số tờ bản đồ`, `Tờ số`, `Tờ bản đồ địa chính số`. |
| T04 | **Diện tích tổng — `dientichtong`** | Chưa bóc thành trường riêng. | `Diện tích`, `Diện tích đất`, `Diện tích thửa đất`, `Tổng diện tích`, `Diện tích toàn thửa`. Phải ở phạm vi cả thửa; nhãn “Diện tích” trong dòng loại đất/nhà có nghĩa khác. |
| T05 | **Loại đất / mục đích sử dụng** | Chưa bóc từng loại đất. | `Mục đích sử dụng`, `Mục đích sử dụng đất`, `Loại đất`; giá trị bằng tên hoặc mã như `Đất ở tại nông thôn` / `ONT`, `Đất ở tại đô thị` / `ODT`, `Đất trồng cây lâu năm` / `CLN`. Đây là ví dụ, chưa phải toàn bộ danh mục mã. |
| T06 | **Diện tích từng loại đất** | Chưa bóc thành từng dòng. | `ONT: … m²`, `CLN: … m²`, `Đất ở … m²`, `Trong đó: …`; ô “Diện tích” trong cùng hàng loại đất. Không dùng số này tự thay diện tích tổng. |
| T07 | **Thời hạn sử dụng đất** | Chưa bóc thành trường riêng. | `Thời hạn sử dụng`, `Thời hạn`, `Sử dụng đến`, `Đến ngày`, `Lâu dài`; giữ cùng loại đất tương ứng. |
| T08 | **Nguồn gốc sử dụng đất** | Chưa bóc thành trường riêng. | `Nguồn gốc sử dụng`, `Nguồn gốc sử dụng đất`, `Nguồn gốc`. |
| T09 | **Hình thức sử dụng đất** | Chưa bóc thành trường riêng. | `Hình thức sử dụng`, `Sử dụng riêng`, `Sử dụng chung`. |
| T10 | **Diện tích sử dụng riêng** | Chưa bóc thành trường riêng. | `Sử dụng riêng: … m²`, `Diện tích sử dụng riêng`, `Riêng: … m²`. |
| T11 | **Diện tích sử dụng chung** | Chưa bóc thành trường riêng. | `Sử dụng chung: … m²`, `Diện tích sử dụng chung`, `Chung: … m²`. |
| T12 | **Serial / số phát hành GCN** | Chưa bóc thành trường riêng. | `Số phát hành`, `Số serial`, `Số seri`, `Giấy chứng nhận … số`, `GCN … số`, `Số:` thuộc phần nhận diện GCN. Theo quyết định đã có: giữ nguyên giá trị, không ép mẫu chữ/số và không bắt buộc có. |
| T13 | **Số vào sổ cấp GCN** | Chưa bóc thành trường riêng. | `Số vào sổ`, `Số vào sổ cấp GCN`, `Số vào sổ cấp giấy chứng nhận`, `Vào sổ số`. |
| T14 | **Ngày cấp GCN** | Chưa bóc thành trường riêng. | `Cấp ngày`, `Ngày cấp`, `Được cấp ngày`, `Cấp … ngày` trong cụm GCN. Ngày hợp đồng/quyết định/tách thửa không tự thay ngày cấp GCN. |
| T15 | **Cơ quan cấp GCN** | Chưa bóc thành trường riêng. | `Do … cấp`, `Cơ quan cấp`, `Nơi cấp`, `Được … cấp` trong cụm GCN. |
| T16 | **Dấu hiệu giá trị cũ–mới / thay đổi trên giấy** | Chưa tách thành nhóm riêng. | `Nay là`, `Nay thuộc`, `Trước đây`, `Cũ`, `Mới`, `Theo bản đồ mới`, `Đính chính`, `Cập nhật biến động`, `Xác nhận thay đổi`. Giữ kèm đúng trường thửa/tờ/địa chỉ/loại đất; chưa chọn bỏ một giá trị khi đưa vào Stage. |
| H01 | **Nhận diện phần nhà/công trình** | `Nhà ở:`, `Công trình xây dựng:`, `Tài sản gắn liền với đất:`, `Tài sản khác gắn liền với đất:`, `Quyền sở hữu nhà ở`. Đang dùng để phân loại đất có công trình. | Ghi nhận các dấu hiệu sẵn có; tên đầy đủ của phôi GCN có chữ “nhà ở” chưa chứng minh tài sản thực có nhà. |
| H02 | **Diện tích xây dựng** | Có chữ `Diện tích xây dựng` để phân loại có công trình; chưa bóc số. | `Diện tích xây dựng`, `Diện tích chiếm đất` nếu mẫu ghi theo nghĩa diện tích công trình chiếm đất. Giữ nguyên nhãn nguồn. |
| H03 | **Diện tích sàn** | Có chữ `Diện tích sàn` để phân loại; chưa bóc số. | `Diện tích sàn`, `Tổng diện tích sàn`, `Diện tích sàn xây dựng`. |
| H04 | **Kết cấu nhà/công trình** | Có chữ `Kết cấu` để phân loại; chưa bóc mô tả. | `Kết cấu`, `Kết cấu nhà`, `Kết cấu công trình`. |
| H05 | **Số tầng** | Có chữ `Số tầng` để phân loại; chưa bóc số. | `Số tầng`, `Tổng số tầng`, `Nhà … tầng`. |
| H06 | **Cấp/hạng công trình** | Có dấu hiệu `Cấp (hạng)`, `Cấp công trình` để phân loại; chưa bóc giá trị. Riêng pattern “Cấp (hạng)” cần kiểm tra dấu ngoặc trước khi tái sử dụng. | `Cấp nhà`, `Cấp công trình`, `Cấp (hạng)`, `Cấp hạng`, `Nhà cấp …`. |
| H07 | **Hình thức sở hữu nhà** | Có chữ `Hình thức sở hữu` để phân loại; chưa bóc giá trị. | `Hình thức sở hữu`, `Sở hữu riêng`, `Sở hữu chung` trong phần nhà. |
| B01 | **Tên ngân hàng — giữ nguyên cả cụm** | Chưa có rule tách trường ngân hàng. Code chỉ giữ các dòng trước Người đầu tiên trong một bên nếu nhận ra Người đó. | `Ngân hàng …`, `Tên ngân hàng: …`; tên tổ chức trong vùng `Bên nhận thế chấp`. Giữ đầy đủ cả chi nhánh/PGD trong một giá trị JSON theo quyết định đã có. |
| B02 | **Địa chỉ ngân hàng** | Chưa có trường/rule riêng. | `Trụ sở`, `Trụ sở chính`, `Địa chỉ trụ sở`, `Địa chỉ`, `Địa chỉ đăng ký`, `Có trụ sở tại` trong khối ngân hàng. |
| B03 | **Mã số thuế ngân hàng** | Chưa có trường/rule riêng. | `Mã số thuế`, `MST`; giữ đúng nhãn nguồn, không tự coi mọi số đăng ký là mã số thuế. |
| B04 | **Số giấy đăng ký / mã số chi nhánh** | Chưa có trường/rule riêng. | `Giấy chứng nhận đăng ký doanh nghiệp số`, `CNĐKDN số`, `Đăng ký kinh doanh số`, `Giấy chứng nhận đăng ký hoạt động số`, `Mã số doanh nghiệp`, `Mã số chi nhánh`. Giữ nhãn từng loại. |
| B05 | **Ngày đăng ký / cấp lần đầu** | Chưa có trường/rule riêng. | `Đăng ký lần đầu ngày`, `Cấp lần đầu ngày`, `Ngày cấp`, `Cấp ngày` trong cụm giấy đăng ký ngân hàng. |
| B06 | **Cơ quan đăng ký / cấp giấy ngân hàng** | Chưa có trường/rule riêng. | `Do … cấp`, `Cơ quan cấp`, `Cơ quan đăng ký`, `Nơi cấp` trong cụm giấy đăng ký ngân hàng. |
| B07 | **Lần/ngày thay đổi đăng ký** | Chưa có trường/rule riêng. | `Đăng ký thay đổi lần thứ … ngày …`, `Thay đổi lần … ngày …`, `Đăng ký thay đổi ngày …`. |
| B08 | **Người đại diện ngân hàng** | Người sau `Đại diện: Ông/Bà …`, hoặc `Đại diện …: Ông/Bà …`, có thể được nhận bằng rule Người N01. Chưa có trường ngân hàng riêng để giữ quan hệ đại diện. | `Người đại diện`, `Đại diện bởi`, `Đại diện theo pháp luật`, `Đại diện theo ủy quyền`; các trường cá nhân áp dụng N01–N21, chức vụ theo N21. |
| B09 | **Số văn bản ủy quyền / căn cứ đại diện** | Chưa có trường/rule riêng. | `Theo giấy ủy quyền số`, `Văn bản ủy quyền số`, `Theo văn bản ủy quyền số`, `Quyết định số`, `Căn cứ … số`; giữ cùng tên loại giấy trong vùng căn cứ đại diện. |
| B10 | **Ngày văn bản ủy quyền / căn cứ đại diện** | Chưa có trường/rule riêng. | `Ngày`, `Lập ngày`, `Ban hành ngày` đi cùng văn bản ở B09. Mỗi giấy giữ đúng ngày của chính giấy đó. |
| B11 | **Bên ban hành văn bản ủy quyền** | Chưa có trường/rule riêng. | `Của …`, `Do …`, `Người ủy quyền`, `Bên ủy quyền` trong cụm căn cứ đại diện; giữ cả tên/chức danh được ghi. |
| B12 | **Điện thoại/fax ngân hàng** | Chưa có trường/rule riêng. | `Điện thoại`, `ĐT`, `Tel`, `Fax` trong khối ngân hàng; tách nhãn điện thoại và fax. |

## Giới hạn đang có trong code cần biết khi duyệt dấu hiệu

- Tên Người hiện phải mở đầu một dòng sau các tiền tố nêu ở N01. Tên dừng trước dấu `;`, cuối dòng, hoặc nhãn `Sinh ngày:` / `Ngày sinh:` / `Chức vụ:` trên cùng dòng. Dấu `:` ở các điểm dừng này có ảnh hưởng: bỏ dấu có thể khiến code lấy lẫn nhãn vào tên.
- Một dòng có tên nhưng thiếu cả ngày sinh, số giấy tờ và nhãn chức vụ hiện bị bỏ. Đây là hành vi cũ, xung đột với quyết định trả cả record thiếu thông tin; **không mang điều kiện bỏ dòng này thành yêu cầu mới**.
- “Anh:”, “Chị:”, “Họ và tên:”, “Họ tên:” có trong [công cụ khảo sát bố cục](../../upload_lab/tools/regex_lab.py), dòng 42–70. Công cụ đó chỉ đánh dấu dòng, chưa chứng minh engine trích được tên tương ứng.
- Rule đầu hàm trích Người được gán lại nhiều lần. Bảng dùng bản gán cuối cùng đang chạy, ở dòng 1013–1028; không cộng các bản đã bị ghi đè thành tính năng.
- Catalog cũ loại người để lại di sản khỏi danh sách đương sự của Upload Lab. Mục tiêu Người của luồng mới đã khác; chỉ tham khảo dấu hiệu, không sao chép nguyên phạm vi loại bỏ đó. Công chứng viên/người làm chứng không nằm trong bảng Người cần trích theo quyết định đã có.

## Dấu hiệu khoanh vùng có thể lấy lại từ tài liệu/code

Đây là các cụm dùng tìm vùng chứa trường, không phải giá trị của trường:

- **Bên A:** `Bên chuyển nhượng`, `Bên thế chấp`, `Bên cho vay`, `Bên cho thuê`, `Bên ủy quyền`, `Bên tặng cho`, `Bên bán`, `Bên A`.
- **Bên B:** `Bên nhận chuyển nhượng`, `Bên nhận thế chấp`, `Bên vay`, `Bên thuê`, `Bên được ủy quyền`, `Bên nhận tặng cho`, `Bên mua`, `Bên B`.
- **Mở vùng Người:** `Chúng tôi gồm có:`, `Chúng tôi gồm:`, `Chúng tôi là những người được hưởng di sản`, `Văn bản phân chia di sản này được lập bởi`, `Tôi là:`, `Văn bản từ chối nhận di sản này được lập bởi`.
- **Mở vùng tài sản:** `Đối tượng của Hợp đồng này là`, `Điều 1`, `Quyền sử dụng đất … có địa chỉ tại`, `Nhà ở và quyền sử dụng đất ở … có địa chỉ tại`, `Tài sản là`, `Ông/Bà … hiện đang sở hữu tài sản là`, `Tài sản:`, `1. Tài sản thứ nhất:`.
- **Dừng vùng tài sản:** tùy loại văn bản, có `1.2`, `Điều 2`, `Giá chuyển nhượng`, `Phương thức thanh toán`, `Bằng Hợp đồng này`, `Bằng văn bản này`, `Hai vợ chồng chúng tôi cam kết/cam đoan`, `Chúng tôi công nhận`, `Người thừa kế:`, `Những người thừa kế`, `Nội dung phân chia di sản`, `Tôi xin cam đoan`, `Lời chứng`, `Số công chứng`, các heading người/bên ký hoặc điểm chỉ. Trong đoạn dẫn hợp đồng cũ còn có `và được Công chứng viên …`, `và được … chứng nhận`.

Các mốc này phản ánh Upload Lab hiện tại, chưa phải quy tắc dùng cho mọi file. Ví dụ file lời chứng độc lập được phép có vùng Người chính ngay trong lời chứng theo quyết định đã có.

## Nguồn và kiểm tra

- [Catalog đang có](../../docs/spec/upload_lab/regex-rules.md): dòng 36–94 mô tả từng loại và vùng. Catalog chưa có mục riêng cho tặng cho, trong khi code đã có; một số mô tả chưa trùng hoàn toàn code. Bảng này phân biệt hiện trạng đọc được và đề xuất, chưa sửa catalog.
- [Code đang chạy](../../upload_lab/extract_contract.py): dòng 1013–1075 nhận Người/trường; 1078–1118 địa chỉ và dòng tổ chức; 640–811 vùng tài sản; 822–892 phân loại nhà/đất; 1154–1309 vùng các bên; 1336–1392 đường gọi tạo kết quả.
- [Công cụ khảo sát bố cục](../../upload_lab/tools/regex_lab.py): dòng 42–70; dấu hiệu khảo sát không tự thành rule trích trường.
- Đã thử trực tiếp hàm hiện tại bằng **12 biến thể mở đầu tên, 4 nhãn ngày sinh và 1 trường hợp “Tôi là” trong vùng từ chối di sản**, dùng dữ liệu giả. `Ông/Bà` có/không dấu `:` nhận tên; chuỗi `Ông/bà` lấy sai thành `/bà Nguyễn Văn A`; `Tôi là`, `Tên tôi là`, `Họ và tên` chưa trả Người trong phép thử; `Sinh ngày`/`Ngày sinh` đọc được, `Năm sinh`/`Sinh năm` chưa đọc được. Đây là kiểm tra dấu hiệu hẹp, không phải đo độ chính xác trên kho mẫu.

Owner có thể duyệt/sửa theo mã, ví dụ: **“N01 thêm Anh/Chị; N02 chấp nhận nhãn Năm sinh; T12 giữ nguyên chữ.”** Chưa bổ sung rule vào code hoặc sửa spec/plan.

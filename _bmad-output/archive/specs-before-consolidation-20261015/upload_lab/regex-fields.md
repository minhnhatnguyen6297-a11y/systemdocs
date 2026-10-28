> **Lịch sử trước đợt gom 15/10/2026. Không phải nguồn hành vi hiện hành; không nạp mặc định đầu phiên. Trạng thái Draft/đã duyệt trong bản gốc được giữ nguyên.**

# Quy tắc trích từng trường Word

**Trạng thái:** Active cho các mục “Theo spec hiện hành”; các mục “Chờ quyết định” không dùng để đổi hành vi hoặc duyệt kết quả. **Task:** TASK-10.1.

**Quyết định:** mỗi trường có một nơi sở hữu ý nghĩa, cách đọc và cách kiểm.
**Tại sao:** cùng một tên/diện tích đang được mô tả khác nhau ở catalog và spec loại; test có thể báo đạt dù trả sai trường.

Trang này sở hữu quy tắc **trường** của engine thừa kế đang chạy trong Upload Lab và bản tool nhân viên. [Core](regex-core.md) sở hữu quy trình; [thừa kế](regex-thua-ke.md) sở hữu loại/vùng và đầu-cuối bản ghi; [catalog](regex-rules.md) dẫn đường và giữ các biến thể cấu trúc khác. Không thay contract Stage hoặc tự port sang lõi workbench.

## 1. Cách đọc và trạng thái

- Trích từ đúng bản ghi, đúng vùng và đúng file; không mượn ngày/giấy tờ của người kế hoặc vùng ký/lời chứng.
- Giữ nguyên giá trị nguồn theo luật từng trường. Thống nhất đáp án không có nghĩa sửa số liệu hoặc sửa tên người theo phỏng đoán.
- Đáp án có `""` = đã kiểm và trường cần để trống; `[]` = đã kiểm và không có bản ghi; `null`/thiếu = chưa kiểm. Mục chưa kiểm không được tính đạt.
- R00..R13 là cảnh báo/kiểm điều kiện; không bảo đảm phát hiện mọi trường sai hoặc mọi bản ghi bị mất. Nghiệm thu phải so đáp án.
- Nguồn đã chốt: regex-decision-46, TASK-5, TASK-9 và quy tắc trường hiện hành trong `regex-thua-ke.md`. TASK-10.1 tổ chức lại các luật này; không duyệt lại quyết định còn mở.
- Ngoại lệ thuộc loại/vùng phải dẫn tới trường tương ứng ở đây. Mâu thuẫn được ghi ở §8, không tự chọn theo độ mới của file.

## 2. Người

### ho_ten — Theo spec hiện hành

**Ý nghĩa:** tên người trong bản ghi; danh xưng/vai trò là dấu hiệu nhận người, không thuộc tên.

**Đọc:** sau Ông/Bà/Anh/Chị hoặc nhãn người, vai trò hay tên trần có bằng chứng người. Cắt tại ranh trường: `|`, giấy tờ, địa chỉ, dấu câu/ngoặc chứa thông tin người khác; nhãn sinh chỉ là ranh khi kèm ngày/năm. `Sinh`, `Năm`, `Cấp` đứng riêng có thể là âm tiết tên.

**Giữ:** chữ nguồn; bỏ vai trò đầu/cuối như `Đồng sở hữu – Cháu`, `Con đẻ –`, `- Con đẻ ông X` và dòng quan hệ riêng. Không nhập tổ chức/câu kể thành tên. Họ Đỗ/La/Từ và tên Văn Phong không bị loại chỉ vì trùng từ thường.

**Kiểm:** `Đồng sở hữu – Cháu Lê Minh An; Sinh ngày 21/11/2011` trả `Lê Minh An`. Khi chỉ có tên được quy tắc loại cho phép, vẫn trả bản ghi để kiểm thiếu trường; không tự loại để hết cờ.

**Nguồn:** Owner 07/10, TASK-9; thừa kế §2; catalog cũ §2.5.

### ten_goi_khac — Theo spec hiện hành

Lấy bí danh được nguồn ghi rõ trong ngoặc/nhãn tên gọi khác; ngoặc có sinh/chết/giấy tờ không tự coi là bí danh. Không đổi tên chính thành một người khác chỉ để khớp ngày hoặc giấy tờ.

### gioi_tinh — Theo spec hiện hành

| Bằng chứng trong nguồn | Kết quả |
|---|---|
| Ông/Anh hoặc vai trò nam rõ đã được hỗ trợ (chồng, bố/cha, con trai) | Ông |
| Bà/Chị hoặc vai trò nữ rõ đã được hỗ trợ (vợ, mẹ, con gái) | Bà |
| Ông/bà, Cháu, Con, Em, đồng sở hữu hoặc không có căn cứ | `""`, giữ R13 |

Chỉ chuẩn hóa dấu hiệu **rõ** đã được spec hỗ trợ. Không suy từ Thị, tên riêng, năm sinh hoặc căn cước. Bỏ danh xưng khỏi tên và chọn giới tính là hai kết quả phải kiểm riêng; không mặc định mọi danh xưng ngoài nhóm nam thành Bà.

**Kiểm:** cả `Cháu Lê Minh An` và `Con Lê Minh An` có tên sạch nhưng giới tính trống.
**Nguồn:** regex-decision-46; thừa kế §2; catalog cũ §2.5, vai trò 12–13/10.

### ngay_sinh, chi_co_nam_sinh — Theo spec hiện hành

Đọc nhãn Sinh ngày/Ngày sinh/Sinh năm/Năm sinh/Sinh và biến thể không dấu hoặc ô ngày sinh của bảng người. Ngày đủ giữ ngày đủ; năm riêng giữ YYYY và `chi_co_nam_sinh=true`, không tự thêm 01/01. Nhãn nguồn viết nhầm “Sinh năm: DD/MM/YYYY” vẫn giữ ngày đủ.

Trong bảng người, ngày sinh ở trước giấy tờ không trở thành ngày cấp; ô ngày cấp sau giấy tờ không trở thành nơi cấp. Đọc theo cột/nhãn, không lấy ngày đầu tiên làm ngày cấp. Năm tách khoảng trắng ở nguồn chỉ nối lại khi cấu trúc ngày đã rõ.

**Kiểm:** `Sinh 26/04/1985` trả ngày đó qua hàm đọc người thật; `Sinh năm 1985` trả 1985; bảng TAB có 01/01/1980 và ngày cấp 10/05/2021 giữ hai trường riêng.
**Nguồn:** thừa kế §2; catalog cũ §2.5 (Sinh trần, năm tách).

### cccd, noi_cap, ngay_cap_cccd — Theo spec hiện hành

Đọc đúng giấy tờ của người từ Căn cước/CCCD/CMND/CC và nhãn số đã hỗ trợ; số viết cách nhóm 3–4 chữ số được bỏ khoảng trắng theo luật hiện hành. Không tự liên kết nhiều giấy khi nguồn không xác nhận.

Ngày cấp từ cấp/ký ngày hoặc cấu trúc `do <cơ quan> ngày` đã hỗ trợ; nơi cấp là cơ quan, không phải ngày sinh/ngày cấp hay địa chỉ. Hộ chiếu riêng không tự điền vào ngày cấp căn cước. Trường thiếu để trống, R03 phản ánh thiếu.

Ranh giấy tờ kết thúc trước mô tả GCN/tài sản hoặc người kế. Không lấy nơi/ngày cấp ở vùng sau để bù thiếu. Dính chữ/sai chính tả trong nguồn giữ phần đọc được để kiểm tay theo [ranh giới chấp nhận](regex-acceptance.md), không sửa chữ nguồn.

**Nguồn:** regex-decision-46; thừa kế §2; các biến thể nhãn giấy tờ catalog cũ §2.5.

### dia_chi — Theo spec hiện hành

Đọc Thường trú/Cư trú/Hộ khẩu/Địa chỉ và các nhãn liên hệ đã hỗ trợ. Cắt phần quan hệ, nhãn người kế và đuôi giới từ treo; không nhận “Nơi chết” làm địa chỉ cuối nếu không có nhãn phù hợp.

Địa chỉ chung chỉ áp cho nhóm được nguồn chỉ rõ; địa chỉ keyed áp cho tên được nhãn chỉ. Giá trị chỉ là DD/MM/YYYY không phải địa chỉ: để trống ở mọi đường đọc (riêng, chung, keyed, bảng và địa chỉ cấp bên). R03 kiểm thiếu, không lấy lại ngày từ một đường bổ sung.

**Kiểm:** `Cả hai cùng thường trú tại: 23/10/2023` không điền ngày làm địa chỉ cho bất kỳ người nào.
**Nguồn:** thừa kế §2; catalog cũ §2.5 (địa chỉ ô dịch trường).

## 3. Người chết — Theo spec hiện hành

Dùng chung quy tắc tên/ngày/địa chỉ/giới tính ở §2 với vùng và dấu hiệu chết thuộc spec loại. Theo luật lọc tên người chết hiện hành, tên tối đa 6 từ, viết hoa đầu từ; câu kể phả hệ không tạo bản ghi. `ngay_chet` từ chết/đã chết/mất ngày; chết năm chỉ trong phạm vi và bằng chứng giấy tờ đã được spec loại quy định. Trích lục khai tử đi vào `so_giay_to, loai_giay_to, ngay_cap, noi_cap` của người chết.

Không lấy căn cước vợ/chồng trong ngoặc làm giấy của người chết. `Nơi thường trú/cư trú cuối cùng/trước khi chết` là nhãn địa chỉ cuối; giới tính vẫn cần căn cứ rõ. Giữ tên đọc được từ nguồn; không đổi sang tên của người khác để bù dữ liệu.

**Nguồn:** regex-decision-46; thừa kế §3.

## 4. Định danh thửa — Theo spec hiện hành

`so_thua_dat` là ký hiệu thửa; `so_to_ban_do` là ký hiệu tờ. Đọc nhãn/cột tương ứng kể cả đảo thứ tự; ô trống phải giữ vị trí và trả trường trống, không dịch cột. Ký hiệu thửa có / như 26/9 thuộc thửa, không phải thời hạn.

Ký hiệu tờ bỏ mô tả “Bản đồ địa chính năm…”, `do <cơ quan>` và phần nhãn thừa. Danh sách số thuần `112, 115` tách theo nguồn; dấu phẩy của địa chỉ/diện tích không thành danh sách số thửa. “Hiện nay/Nay là thửa/tờ…” là ghi chú đánh số lại theo spec loại, không tự mở tài sản khác.

**Kiểm:** cột `Số thửa | Số tờ`, giá trị `211 | 9` trả thửa 211/tờ 9; bảng có tờ trống vẫn trả thửa và các dữ liệu còn lại.
**Owner 15/10/2026:** thông tin của một thửa được viết liên tục trong cùng
khối nguồn; cặp `so_thua_dat` + `so_to_ban_do` là dấu hiệu phân biệt chính.
Đọc các dòng chi tiết nối tiếp vào đúng thửa, không tạo thửa mới chỉ vì đổi
loại đất/diện tích/thời hạn. Cặp thửa/tờ khác mở thửa khác. Thiếu dấu hiệu rõ
thì giữ nguồn và gắn cờ; không tự nối sang file/địa phương/hồ sơ khác hoặc bỏ
bản lặp mâu thuẫn. Đây không phải khóa định danh chung liên module.

**Nguồn:** thừa kế §4; Owner 07/10/TASK-9 và 15/10/2026. Cách giữ giá trị mâu thuẫn xem §8.

## 5. Diện tích và chi tiết đất — Theo spec hiện hành, trừ cách gộp

- `dien_tich`: tổng diện tích nguồn ghi riêng; giữ chữ/số gốc theo luật đã có, bỏ phần bằng chữ và đuôi mô tả. Không suy tổng từ chi tiết hay làm tròn.
- `chi_tiet_dien_tich`: từng dòng chi tiết với diện tích, mục đích, thời hạn, ghi chú. Tổng và chi tiết là hai dữ liệu phải kiểm riêng.
- `muc_dich_su_dung`: giữ loại/mục đích nguồn ghi; không suy mã khi thiếu căn cứ. Nhãn đất dài không tự biến thành văn xuôi rác vì vượt một số ký tự.
- `thoi_han_su_dung`: đúng ô thời hạn; không nuốt số diện tích chi tiết kế. MM.YYYY là biến thể đã hỗ trợ.
- `phan_ghi_them`, `nguon_goc`: giữ ghi chú/quyền sử dụng/đánh số lại hoặc nguồn gốc vào đúng trường; không bỏ dữ liệu chỉ để hết R10.
- `land_rows`: dữ liệu đất đọc được từ chi tiết, giữ loại nguồn và thời hạn. Diện tích không đọc chắc thành số để nguyên + báo mơ hồ; “1.234” chỉ dấu chấm vẫn theo regex-decision-46.

Chỉ loại khỏi kiểu đất khi có bằng chứng cấu trúc là tiêu đề/câu kể như “Di sản của ... để lại”, “Chúng tôi thống nhất ...” hoặc “Các bên thống nhất phân chia ...”; giữ đoạn nguồn/diện tích/thời hạn trong `phan_ghi_them` và gắn R13 cần kiểm mục đích. Nhãn đất dài và ô trống không tự trở thành văn xuôi; không dùng chiều dài làm bằng chứng duy nhất. Không tự chốt cách xử lý hai phiên bản diện tích/thời hạn ở §8.

**Kiểm:** `40 | Đất trồng cây lâu năm và đất nuôi trồng thủy sản | 12/2043` giữ chi tiết và land_rows. Một phép kiểm đạt tổng nhưng chưa kiểm chi tiết/thời hạn/ghi chú chưa phải nghiệm thu toàn bộ.
**Nguồn:** regex-decision-46; thừa kế §4; catalog cũ về bảng GCN/chi tiết.

## 6. Giấy chứng nhận — Theo spec hiện hành

`loai_gcn` là loại giấy ghi trong nguồn; `so_gcn/so_gcn_raw` là chuỗi nguồn, không áp điều kiện hai chữ hoa + số để công nhận bản ghi. Có thể trống/trùng theo quyết định owner. `so_vao_so, ngay_cap_gcn, co_quan_cap` đọc đúng nhãn/ô cấp giấy; không lấy ngày cấp căn cước hoặc ngày ký văn bản khác.

Context GCN/địa chỉ chung thuộc đúng nhóm thửa có thể copy vào các thửa theo spec loại. Nhiều giấy hoặc nhiều giá trị trái nhau không được tự chọn; các quyết định phạm vi gộp chưa rõ vẫn chờ.

Danh sách mô tả tài sản đánh số, mỗi mục một GCN rõ, giữ từng bản ghi dù không ghi số thửa; không suy số thửa pháp lý. Địa chỉ trước số thửa thuộc cùng mục vẫn được giữ. Nhãn `Số vào sổ cấp GCN:` hoặc `Số vào sổ cấp giấy chứng nhận số:` đọc đúng giá trị sau nhãn. Chỉ dùng vùng tài sản, không quét toàn văn để bù.

**Nguồn:** Owner 06/10/regex-decision-46; thừa kế §4. Các tầng khác còn theo TASK-8; trang này không tuyên bố đã sửa tất cả runtime.

## 7. Trường chưa hỗ trợ và phạm vi

Sổ tiết kiệm/tài khoản và bảo hiểm chỉ nhận diện `tai_san_chua_ho_tro` + R12 theo regex-decision-46, không tạo dòng tài sản đầy đủ. Xe/tàu theo giới hạn loại hiện hành. Quê quán giữ khả năng đọc snapshot cũ; intake không tự điền.

Số/ngày công chứng và tên công chứng viên phục vụ upload/audit theo flow riêng; không dùng làm tiêu chí “trích đúng người/tài sản”. Trang này không tự mở schema hoặc field mới.

## 8. Quyết định 15/10 và phần cần đối chiếu

| Mục | Owner đã chốt | Phần phải đối chiếu trước khi đổi engine/đáp án |
|---|---|---|
| F04 | Theo §4: khối liên tục, phân biệt chính bằng số thửa + số tờ | Các mẫu có tổng trái nhau phải đọc nguồn; không tự lấy bản đầu hoặc bỏ phần khác |
| F05 | Trường/định dạng theo DB đã duyệt; chi tiết thuộc đúng thửa/cụm | Giữ bộ loại đất–diện tích–thời hạn theo `contracts/entities.md`; alias cũ phải ánh xạ rõ. Hai giá trị mâu thuẫn không được tự chọn một phía |

Quyết định về cấu trúc không phê duyệt một thuật toán gộp hoặc đáp án mẫu chưa
được đọc tay. Engine/fixture có thể còn theo luật cũ; mục `pending_decision`
cũ vẫn phải được kiểm lại, không biến “bỏ qua” thành “đạt”.

## 9. Nguồn và bộ đáp án

- [Đáp án đích và trạng thái từng mẫu](regex-expected-results.md).
- [Core](regex-core.md), [thừa kế](regex-thua-ke.md), [catalog cấu trúc](regex-rules.md).
- regex-decision-46, TASK-5, TASK-9, TASK-10.1; review trong `.agents/review-sweep-20261007/` và `.agents/review-viewpoint-20261007/`.
- Catalog trước khi gom được lưu làm **tham khảo không quyết định hành vi** tại [bản trước](references/regex-rules-before-field-standardization.md); dùng để truy các biến thể đã có, không tái áp luật đang chờ.

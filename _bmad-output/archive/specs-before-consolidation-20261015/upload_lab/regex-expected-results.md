> **Lịch sử trước đợt gom 15/10/2026. Không phải nguồn hành vi hiện hành; không nạp mặc định đầu phiên. Trạng thái Draft/đã duyệt trong bản gốc được giữ nguyên.**

# Đáp án đích cho trích trường Word

**Trạng thái:** quy tắc/đáp án theo spec hiện hành cho các dòng Closed; các mẫu F04/F05 còn cần đối chiếu nguồn sau quyết định 15/10/2026, chưa được chấm đạt. **Task:** TASK-10.1. Đây là kết quả phải kiểm, không phải bản chép output máy.

## 1. Cách ghi

Mỗi ca có mã, nguồn, phạm vi, trường phải kiểm, đáp án, cảnh báo và trạng thái. `closed_existing_spec` nghĩa là suy ra từ yêu cầu đã có; không phải một Golden được owner duyệt mới. `pending_decision` không chạy như test đã đạt. Đáp án là tập trường đã đọc tay, không tuyên bố toàn bộ hồ sơ đã đúng.

| Giá trị | Nghĩa | Tính vào đã kiểm? |
|---|---|---|
| `""` | Đã đọc và trường cần để trống | Có |
| `[]` | Đã đọc và không có bản ghi | Có; máy trả thừa phải thất bại |
| `null`/thiếu | Chưa trả lời trường đó | Không |
| Pending | Chưa chốt hành vi | Không; phải hiện danh sách riêng |

Nguồn thật phải có đường dẫn, dấu vân tay file/text, đoạn được kiểm và phiên bản engine. Dữ liệu cá nhân ở `.agents/task-10.1/`; các test lưu lâu dài dùng tên/số giả và giữ cấu trúc.

## 2. Mẫu Closed từ quy tắc đã có

| Ca | Đầu vào trọng tâm | Đáp án đích phải kiểm | Cờ | Quy tắc |
|---|---|---|---|---|
| C01 | Đồng sở hữu – Cháu Lê Minh An; Sinh ngày 21/11/2011 | ho_ten=Lê Minh An; gioi_tinh=""; ngay_sinh=21/11/2011; không mất người | R13 | [Tên/giới tính](regex-fields.md#2-người) |
| C02 | Đồng sở hữu – Con Lê Minh An; Sinh ngày 21/11/2011 | Tên sạch; giới tính trống; không tự biến thành Bà | R13 | §2 |
| C03 | Số thửa \| Số tờ; hàng 211 \| 9; hàng 212 \| 10 chung dòng | Đúng 2 thửa; thửa/tờ tương ứng 211/9 và 212/10; giữ diện tích/mục đích/thời hạn | Không tạo R10 giả | [Định danh thửa](regex-fields.md#4-định-danh-thửa--theo-spec-hiện-hành) |
| C04 | Số tờ \| Số thửa; tờ đầu trống, thửa 211; tiếp thửa 212 | Giữ cả 2 thửa; thửa 211 có tờ trống; các cột không dịch | Thiếu dữ liệu được phản ánh trung thực | §4 |
| C05 | 40 \| Đất trồng cây lâu năm và đất nuôi trồng thủy sản \| 12/2043 | Chi tiết có đủ 3 trường; land_rows có loại, diện tích 40, thời hạn | Không bỏ dữ liệu vì nhãn dài | [Chi tiết đất](regex-fields.md#5-diện-tích-và-chi-tiết-đất--theo-spec-hiện-hành-trừ-cách-gộp) |
| C06 | STT TAB Bà Lê Ngọc Mai TAB 01/01/1980 TAB CCCD TAB số TAB 10/05/2021 TAB Bộ Công an TAB xã Minh Tân | ngay_sinh=01/01/1980; ngay_cap_cccd=10/05/2021; noi_cap=Bộ Công an; địa chỉ đúng | Không lấy ngày sinh làm ngày cấp | §2 |
| C07 | Bà Lê Ngọc Mai – Sinh 26/04/1985, có CCCD và địa chỉ | Đúng 1 người, tên và ngày sinh đúng qua hàm thật | Theo dữ liệu còn thiếu | §2 |
| C08 | Người có ngày sinh; Địa chỉ: 23/10/2023 | Đúng người; dia_chi=""; địa chỉ cấp bên cũng không là ngày | R03 thiếu địa chỉ | §2 |
| C09 | Hai người; Cả hai cùng thường trú tại: 23/10/2023 | Cả hai địa chỉ trống; không gán lại ngày từ đường chung | R03 | §2 |
| C10 | Người có nhãn địa chỉ keyed chỉ mang 23/10/2023 | Tên/ngày sinh vẫn giữ; địa chỉ trống | R03 | §2 |
| C11 | Mẫu không có người/không có đất đã đọc xác nhận | Danh sách tương ứng [] | Theo loại; không tự bịa bản ghi | §1 |
| C12 | Bà Lê Ngọc Mai; Sinh năm 1980 | ngay_sinh=1980, chi_co_nam_sinh=true; không tự thêm 01/01 | Theo trường khác | §2 |

R03/R13 kiểm ở payload đầy đủ bằng validator, không đoán cờ từ số lượng ô. Cờ về các trường khác của mẫu thiếu có thể vẫn xuất hiện; phải kiểm cờ liên quan cụ thể.

Các ca đất C03–C05 có câu mở vùng tài sản trong đầu vào Word; kiểm danh sách
thửa từ `extract(filepath)` nguyên trạng, không thay bằng kết quả hàm phụ.
Fixture thực thi tại [Upload Lab](../../../../upload_lab/tests/fixtures/word_field_cases.json)
và bản snapshot [tool nhân viên](../../../../regex-test-tool/tool/tests/fixtures/word_field_cases.json).

Các biến thể giữ cùng quy tắc và được kiểm riêng:

| Nhóm | Biến thể phải kiểm |
|---|---|
| C01/C02 | Danh xưng trung tính kết hợp Ông/bà sau vai trò, tên sạch + R13 |
| C03/C04 | Dòng tiếp không có thửa, đuôi ô định dạng, ghi chú đánh số lại; đường `.doc` qua bước chuẩn hóa cũng giữ ô tờ trống |
| C05 | Nhãn đất dài hơn 100 ký tự vẫn giữ; câu kể “Di sản của…”, “Chúng tôi thống nhất…”, “Các bên thống nhất phân chia…” chuyển đủ nguồn vào ghi chú + R13, không thành loại đất |
| C06/C12 | Năm sinh trong bảng trước/sau giấy tờ; thiếu sinh hoặc thiếu số giấy tờ không lấy ngày cấp làm sinh; nơi cấp trống không nuốt địa chỉ |
| C07/C08 | Người chết cũng nhận Sinh trần và bỏ địa chỉ cuối thuần ngày |

Mẫu `.doc` tổng hợp giả phần đọc IFilter để kiểm đường chuẩn hóa và `extract`,
không được gọi là file `.doc` thật. Bằng chứng file thật thuộc §4 dưới đây.

## 3. Pending — giữ đầu vào, chưa chọn số bản ghi/giá trị

| Ca | Nguồn vấn đề | Điều đã thấy | Chưa chấm |
|---|---|---|---|
| P04/F04 | Cùng thửa/tờ, tổng 210 / 210,0 / 210 m2 hoặc tổng thật khác | Owner đã chốt ranh thửa theo khối liên tục + thửa/tờ | Cần đọc nguồn để ghi đáp án tổng/chi tiết; không tự duyệt số bản ghi của mẫu mâu thuẫn |
| P05/F05 | Chi tiết cùng diện tích+loại nhưng bổ sung hoặc đổi thời hạn/ghi chú | Owner đã chốt trường/format theo DB, giữ đúng cụm đất | Cần đọc nguồn để ghi đáp án từng trường; không tự chọn một giá trị mâu thuẫn |

Không coi nguồn tự viết là hồ sơ thật. Mẫu tổng hợp chứng minh hành vi trên cấu trúc đã hỗ trợ; tần suất trên hồ sơ thật cần đo riêng.

## 4. Mẫu Word thật

R01-real (mã ca, không phải cờ R01): file cam kết đồng sở hữu trong batch s283, vùng mở đầu có 4 người, 3 người mở bằng Cháu. Đáp án được đọc độc lập **chưa xem output máy** tại `.agents/task-10.1/chau.expected.json`; nguồn và dấu vân tay tại `chau.provenance.json`.

Kiểm đúng 4 người và từng trường tên/giới tính/sinh/căn cước/nơi cấp/ngày cấp/địa chỉ; giữ R13 cho ba người Cháu. Các trường tài sản, người chết, thông tin chung và vùng ký **chưa được chấm** ở ca này. Không suy toàn bộ file đúng từ 7 trường đã kiểm.

## 5. Điều kiện kết thúc một vòng

1. Closed: mọi trường kê trong ca đã kiểm bằng hàm thật; số người/thửa đúng, không bỏ chi tiết.
2. Pending và trường chưa trả lời được báo riêng, không cộng vào số đạt.
3. Bỏ một hỗ trợ trong code phải khiến phép kiểm tương ứng thất bại; hai engine có cùng đáp án.
4. Có ít nhất một lượt đọc Word thật qua đường đọc đang dùng, không chỉ truyền text.
5. Không gọi approve/ghi Golden mới cho các mục chưa được owner duyệt.

Code test/fixture là bản thực thi đáp án ở đây; không có quyền sửa đáp án để hợp output máy. So theo số trường được kiểm, không dùng số test xanh hay số cờ làm tỷ lệ chính xác.

TASK-10.3 áp dụng [ranh giới chấp nhận](regex-acceptance.md). Bộ chấm phải kiểm cờ năm sinh cả false và true, tên có dấu, từng trường người chết và ghép một-một; lỗi đọc không được thành đạt. Báo `MATCH_CHECKED_FIELDS` cùng phạm vi và số trường chưa trả lời thay vì suy cả file đạt. Lượt mới giữ nguyên bằng chứng TASK-10.2, dùng lớp đính chính có dòng nguồn và output/hash mới.

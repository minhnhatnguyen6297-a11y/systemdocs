# Bóc tách dữ liệu — Word, quy tắc trường và kiểm chứng

**Cập nhật:** 20/10/2026. Tập trung quy tắc để không phải ghép nhiều file. **Một đường luật duy nhất** cho văn bản Word: `tools/regex_workbench/engine/contract_extract.py` (`extract_text` + các hàm nhóm/thửa, identity `contract_word` + `ENGINE_VERSION`). Document Intake, Word Upload và tool nhân viên đều gọi vào đó qua adapter của mình — adapter chỉ giữ đọc file + ánh xạ payload, không chép luật: `upload_lab/extraction_adapter.py` (Upload/tool) và `notary_v2/services/document_intake/adapters/docx.py` (Document Intake, dựng `source_refs` span/`rule_id`/identity lõi). Pipeline profile/zoning cũ đã gỡ cùng cutover 16/10/2026; bản chép `extract_contract.py` trong repo và trong tool cũng đã gỡ — bản tool đóng gói lõi qua script release. Gom spec không chứng minh đã thống nhất code hoặc cho phép sao chép luật giữa các bên.

## 1. Nguyên tắc

Đọc đúng vùng → đúng người/thửa → đúng trường DB đích → giữ nguồn → cảnh báo thiếu/mơ hồ → người kiểm tra. Không gộp hồ sơ hoặc phán quyết pháp lý. Lõi chung nhận Word/text và hỗ trợ đề xuất placeholder; adapter phải ánh xạ rõ tên trường, không tự tạo schema.

Có người/thửa nào giữ người/thửa đó; khi không chắc giữ bằng chứng và gắn cờ, không cắt/gộp mất im lặng. Không bóc người từ Lời chứng; R11 đã bỏ. Sổ tiết kiệm/bảo hiểm chỉ nhận diện chưa hỗ trợ + R12. Quê quán chỉ đọc snapshot cũ, intake không tự điền. Số công chứng dùng riêng cho Upload, không là tiêu chí đủ của core Người/Tài sản.

<a id="sample-iteration"></a>
### Vòng làm việc theo mẫu thực — owner 19/10/2026

**Quy tắc bắt buộc, bền vững cho các phiên sau:** owner yêu cầu
“ghi lại rule test này lại, tôi không muốn nhắc lại lần sau”.
LLM phải đọc mẫu thực theo lô trước, nhận diện cấu trúc, đối chiếu **spec/code**,
chỉnh code có căn cứ rồi test; sai thì lặp cho tới khi xuất đủ, đúng thông tin
hợp đồng. Đọc `D:\testcase\README.md` và quy tắc này trước khi tạo fixture.
Không khôi phục kế hoạch mười ca trước lệnh dừng. Phần unresolved không tính
pass và không bị âm thầm loại khỏi mẫu số để báo toàn bộ đã đạt.
**Gate mới trước vòng trên:** mọi lượt quét/đọc mẫu thực mới, mass survey của
owner, corpus và vòng E2E theo mẫu phải chờ
[#41 chuẩn hóa trường Upload](../../backlog/story-upload-business-field-standardization.md)
được nghiệm thu **chuẩn DB/contract đã duyệt + cutover consumer + proof luồng
thật**, không chỉ có bảng mapping. Proof riêng #41 khi được giao dùng input
tổng hợp/kiểm soát và DB/profile cô lập; không bắt khảo sát `D:\testcase` trước
khi đóng issue, tránh vòng phụ thuộc. Inventory source tĩnh hiện tại không phải
lô khảo sát mẫu. Sau gate vẫn phải được giao thực thi, không tắt Scan/Upload
production hoặc coi tài liệu là quyền code/chạy mẫu.


Thứ tự khi được giao chạy: **LLM đọc hàng loạt file mẫu thực → nhận diện
cấu trúc trước → so sánh với code → điều chỉnh code → test lại → nếu sai thì
lặp lại**. Mục tiêu là xuất **đủ, đúng thông tin hợp đồng**, không chỉ xuất được
DOCX hoặc có hash giống nhau. Trước khi đối chiếu code, ghi độc lập vùng/nhóm
Người, Tài sản, Hồ sơ, giá trị có bằng chứng và mapping vào trường canonical
hiện có. Không lấy parser output làm đáp án; raw và vị trí nguồn không bị sửa.
Không thêm entity/field nghiệp vụ, DTO ghi DB riêng hoặc nhét thông tin sai nghĩa
vào ghi chú để làm phép kiểm có vẻ đạt. Phần cần schema mới phải được duyệt.
Ngoại lệ hẹp là cụm trường phụ website theo hướng owner cho phép có điều kiện (mục 2.7);
đó là trường đã chốt, không phải ghi chú chung/raw capture, và không tự biến mọi
editor thành block.

**Sau gate #41**, loại đã biết nhưng cấu trúc/mapping chưa chốt có issue riêng theo loại; thiếu
enum runtime không tự chứng minh cấu trúc chưa biết hoặc parser có lỗi.
Văn bản lạ/không tự quyết được hoặc gap mapping được ghi theo từng file/ứng viên
vào [#39 — tổng hợp để owner xem sau](../../backlog/spike-unfamiliar-document-review-queue.md),
kèm tham chiếu nguồn/hash, vị trí, thông tin có căn cứ, phần còn chưa quyết,
mapping Người/Tài sản/Hồ sơ và issue theo loại nếu có. Đây là metadata theo dõi,
không phải schema nghiệp vụ mới. Đánh dấu **pending/chưa kiểm, không phải pass**;
giữ nguyên nguồn/ứng viên và tiếp tục các file/phần đã rõ, không dừng cả lô hoặc
tự đoán câu trả lời. Thông tin hợp đồng chưa biểu diễn được phải hiện trong
phần thiếu/issue, không bỏ mất để báo đủ.

Mỗi vòng khi chạy thực tế ghi phần đã sửa, kết quả test với đáp án độc lập,
lỗi còn lại và phần pending; không tự tuyên bố hoàn tất nếu còn thiếu thông tin.
LLM có thể là agent đọc file cục bộ; không có quyền cloud/provider mới hoặc
runtime LLM fallback từ chỉ dẫn này. Trạng thái hiện tại vẫn **chỉ ghi tài liệu**,
chưa bắt đầu đọc nội dung file mẫu, sửa code hoặc test. So byte/định dạng/trang
Word là các lớp kiểm riêng; tiêu chuẩn binary/pixel chưa được owner chọn,
không tự coi đã nới hoặc đã đạt.

### Báo cáo ổn định và gate hoàn thành

Sau mỗi lô LLM phải cập nhật **`D:\testcase\BAO_CAO_KHAO_SAT.md`**; phiên sau
đọc báo cáo trước lô mới, dùng lại kết quả có nguồn còn phù hợp. Giữ kết quả cũ
bằng mục lô có ngày hoặc tham chiếu lịch sử thuộc sở hữu, không ghi đè mất
khảo sát, không dùng tmp/log làm báo cáo duy nhất.

Trước khi gọi chuẩn trường đã rõ, báo cáo audit phải liệt kê **tên trường,
kiểu, format/độ đầy đủ ngày, cách nhóm/thứ tự, đích DB hoặc wire, ràng buộc và
nguồn canonical** cho Người, Tài sản, Hồ sơ. Tách trường defined khỏi Draft và
ambiguous/unmapped. Có key trong code/contract không tự chứng minh mọi biến thể
hợp đồng đã có mapping đủ; báo cáo là audit hiện tại, không thay SOT contract.
Sau gate #41, gap từng file chỉ chặn phần phụ thuộc, không tự mở schema hoặc
dừng file đã rõ. Catalog nền trước đây chưa khép kín trường Hồ sơ/Upload.

Gate kết quả lô: báo cáo có đường dẫn/ref nguồn + version/ngày, phạm vi
đã đọc/chưa đọc và phương pháp; vùng/đoạn/bảng và vị trí/vai trò các bên;
mapping ba đối tượng và coverage có nguồn; code gap + issue; đề xuất/sửa đã áp
dụng; retest đã/chưa chạy, kết quả quan sát, pending và next resume. Phần thiếu
không tính pass hoặc bị loại im lặng. Metadata/danh mục chưa đọc body phải ghi
**coverage nội dung 0**, không gọi là khảo sát mẫu đã hoàn tất.

Báo cáo owner-local giữ tham chiếu/chi tiết theo quyền riêng tư hiện có.
Repo issue/tài liệu commit chỉ dùng ref an toàn và trích cấu trúc đã che giá trị
cá nhân; không chép raw Word/CCCD/thông tin khách vào Git hoặc log rộng. Không
tạo tính năng logging/telemetry. Lượt hiện tại chỉ ghi quy tắc và audit canonical
nếu được giao, không suy file báo cáo khởi tạo là đã đọc nội dung lô mẫu.

<a id="fields"></a>
## 2. Giá trị từng trường

**Quyết định owner 19/10/2026 cho toàn bộ trường nghiệp vụ:** **chủ đất thuộc
Hồ sơ**, không là chủ sở hữu cố định của Tài sản và không mặc định node `owner`
Thừa kế. Thông tin công chứng thuộc Hồ sơ, độc lập ngày tạo hồ sơ; inventory
phải gồm số/ngày công chứng, công chứng viên, thư ký và mọi trường Upload trước
khi claim đủ. Key/kiểu/format/nhóm/cardinality/DB-wire-output còn thiếu phải
chốt trong #41, không tự suy schema mới hoặc chỉ dùng cột workspace Notary.

**Không lấy trường thông tin giao dịch** (giá, cọc, tiền thuê, khoản vay, lãi
suất, điều khoản thanh toán) **hoặc thời hạn nghiệp vụ** vào extraction/
normalized. Không áp dụng việc bỏ qua cho thời hạn sử dụng đất đúng cụm
`land_rows[].thoihan` hoặc timeout kỹ thuật. Portal cần trường bị loại thì ghi
xung đột để refine, không giữ extraction ngầm, bịa/default hay tự chọn bước
nhập tay mới. Không xóa/viết lại raw, lịch sử hoặc runtime trong lượt docs-only.
Một Người nhiều giấy tờ và địa chỉ là
[#42 riêng](../../backlog/story-person-multiple-identities-addresses.md);
không ép ô đơn hiện tại thành đa trị hoặc tự thêm prerequisite cho gate #41.
[Quyết định](../../decisions/decision-owner-upload-field-standardization-20261019.md).

### 2.1. Cách đọc và trạng thái

- Trích từ đúng bản ghi, đúng vùng và đúng file; không mượn ngày/giấy tờ của người kế hoặc vùng ký/lời chứng.
- Giữ nguyên giá trị nguồn theo luật từng trường. Thống nhất đáp án không có nghĩa sửa số liệu hoặc sửa tên người theo phỏng đoán.
- Đáp án có `""` = đã kiểm và trường cần để trống; `[]` = đã kiểm và không có bản ghi; `null`/thiếu = chưa kiểm. Mục chưa kiểm không được tính đạt.
- R00..R13 là cảnh báo/kiểm điều kiện; không bảo đảm phát hiện mọi trường sai hoặc mọi bản ghi bị mất. Nghiệm thu phải so đáp án.
- Nguồn đã chốt: regex-decision-46, TASK-5, TASK-9. Quy tắc hiện hành nằm trong chính tài liệu này: [giá trị từng trường (§2)](#fields) và [vùng thừa kế, ranh bản ghi (§4)](#inheritance). [`regex-thua-ke.md` trước đợt gom 15/10/2026 (lịch sử, không phải nguồn hiện hành)](../../archive/specs-before-consolidation-20261015/upload_lab/regex-thua-ke.md). TASK-10.1 tổ chức lại các luật này; không duyệt lại quyết định còn mở.
- Ngoại lệ thuộc loại/vùng phải giữ đúng nghĩa trường. Giá trị mâu thuẫn phải đối chiếu nguồn, không chọn theo độ mới của file.

### 2.2. Người

#### ho_ten — Theo spec hiện hành

**Ý nghĩa:** tên người trong bản ghi; danh xưng/vai trò là dấu hiệu nhận người, không thuộc tên.

**Đọc:** sau Ông/Bà/Anh/Chị hoặc nhãn người, vai trò hay tên trần có bằng chứng người. Cắt tại ranh trường: `|`, giấy tờ, địa chỉ, dấu câu/ngoặc chứa thông tin người khác; nhãn sinh chỉ là ranh khi kèm ngày/năm. `Sinh`, `Năm`, `Cấp` đứng riêng có thể là âm tiết tên.

**Giữ:** chữ nguồn; bỏ vai trò đầu/cuối như `Đồng sở hữu – Cháu`, `Con đẻ –`, `- Con đẻ ông X` và dòng quan hệ riêng. Không nhập tổ chức/câu kể thành tên. Họ Đỗ/La/Từ và tên Văn Phong không bị loại chỉ vì trùng từ thường.

**Kiểm:** `Đồng sở hữu – Cháu Lê Minh An; Sinh ngày 21/11/2011` trả `Lê Minh An`. Khi chỉ có tên được quy tắc loại cho phép, vẫn trả bản ghi để kiểm thiếu trường; không tự loại để hết cờ.


#### ten_goi_khac — policy đích owner R05, 20/10/2026

Bỏ tự động điền và mở rộng chuẩn hóa alias; nếu cần user điền tay. Không nối
alias vào tên chính hoặc thêm field alias mới; giữ raw/lịch sử. Code cũ có thể
còn bóc nhãn/ngoặc tên gọi khác: đó là hiện trạng chưa cutover, không authority
để tiếp tục mở chuẩn. Ngoặc sinh/chết/giấy tờ không tự thành alias.

#### gioi_tinh — Theo spec hiện hành

| Bằng chứng trong nguồn | Kết quả |
|---|---|
| Ông/Anh hoặc vai trò nam rõ đã được hỗ trợ (chồng, bố/cha, con trai) | Ông |
| Bà/Chị hoặc vai trò nữ rõ đã được hỗ trợ (vợ, mẹ, con gái) | Bà |
| Ông/bà, Cháu, Con, Em, đồng sở hữu hoặc không có căn cứ | `""`, giữ R13 |

Chỉ chuẩn hóa dấu hiệu **rõ** đã được spec hỗ trợ. Không suy từ Thị, tên riêng, năm sinh hoặc căn cước. Bỏ danh xưng khỏi tên và chọn giới tính là hai kết quả phải kiểm riêng; không mặc định mọi danh xưng ngoài nhóm nam thành Bà.

**Kiểm:** cả `Cháu Lê Minh An` và `Con Lê Minh An` có tên sạch nhưng giới tính trống.

#### ngay_sinh, chi_co_nam_sinh — Theo spec hiện hành

Đọc nhãn Sinh ngày/Ngày sinh/Sinh năm/Năm sinh/Sinh và biến thể không dấu hoặc ô ngày sinh của bảng người. Ngày đủ giữ ngày đủ; năm riêng giữ YYYY và `chi_co_nam_sinh=true`, không tự thêm 01/01. Nhãn nguồn viết nhầm “Sinh năm: DD/MM/YYYY” vẫn giữ ngày đủ.

Trong bảng người, ngày sinh ở trước giấy tờ không trở thành ngày cấp; ô ngày cấp sau giấy tờ không trở thành nơi cấp. Đọc theo cột/nhãn, không lấy ngày đầu tiên làm ngày cấp. Năm tách khoảng trắng ở nguồn chỉ nối lại khi cấu trúc ngày đã rõ.

**Kiểm:** `Sinh 26/04/1985` trả ngày đó qua hàm đọc người thật; `Sinh năm 1985` trả 1985; bảng TAB có 01/01/1980 và ngày cấp 10/05/2021 giữ hai trường riêng.

#### cccd, noi_cap, ngay_cap_cccd — Theo spec hiện hành

Đọc đúng giấy tờ của người từ Căn cước/CCCD/CMND/CC và nhãn số đã hỗ trợ; số viết cách nhóm 3–4 chữ số được bỏ khoảng trắng theo luật hiện hành. Không tự liên kết nhiều giấy khi nguồn không xác nhận.

Ngày cấp từ cấp/ký ngày hoặc cấu trúc `do <cơ quan> ngày` đã hỗ trợ; nơi cấp là cơ quan, không phải ngày sinh/ngày cấp hay địa chỉ. Hộ chiếu riêng không tự điền vào ngày cấp căn cước. Trường thiếu để trống, R03 phản ánh thiếu.

Ranh giấy tờ kết thúc trước mô tả GCN/tài sản hoặc người kế. Không lấy nơi/ngày cấp ở vùng sau để bù thiếu. Dính chữ/sai chính tả trong nguồn giữ phần đọc được để kiểm tay theo ranh giới chấp nhận, không sửa chữ nguồn.


#### dia_chi — Theo spec hiện hành

Đọc Thường trú/Cư trú/Hộ khẩu/Địa chỉ và các nhãn liên hệ đã hỗ trợ. Cắt phần quan hệ, nhãn người kế và đuôi giới từ treo; không nhận “Nơi chết” làm địa chỉ cuối nếu không có nhãn phù hợp.

Địa chỉ chung chỉ áp cho nhóm được nguồn chỉ rõ; địa chỉ keyed áp cho tên được nhãn chỉ. Giá trị chỉ là DD/MM/YYYY không phải địa chỉ: để trống ở mọi đường đọc (riêng, chung, keyed, bảng và địa chỉ cấp bên). R03 kiểm thiếu, không lấy lại ngày từ một đường bổ sung.

**Kiểm:** `Cả hai cùng thường trú tại: 23/10/2023` không điền ngày làm địa chỉ cho bất kỳ người nào.

### 2.3. Người chết — Theo spec hiện hành

Dùng chung quy tắc tên/ngày/địa chỉ/giới tính ở phần Người với vùng và dấu hiệu chết thuộc spec loại. Theo luật lọc tên người chết hiện hành, tên tối đa 6 từ, viết hoa đầu từ; câu kể phả hệ không tạo bản ghi. `ngay_chet` từ chết/đã chết/mất ngày; chết năm chỉ trong phạm vi và bằng chứng giấy tờ đã được spec loại quy định. Trích lục khai tử đi vào `so_giay_to, loai_giay_to, ngay_cap, noi_cap` của người chết.

Không lấy căn cước vợ/chồng trong ngoặc làm giấy của người chết. `Nơi thường trú/cư trú cuối cùng/trước khi chết` là nhãn địa chỉ cuối; giới tính vẫn cần căn cứ rõ. Giữ tên đọc được từ nguồn; không đổi sang tên của người khác để bù dữ liệu.


### 2.4. Định danh thửa — Theo spec hiện hành

`so_thua_dat` là ký hiệu thửa; `so_to_ban_do` là ký hiệu tờ. Đọc nhãn/cột tương ứng kể cả đảo thứ tự; ô trống phải giữ vị trí và trả trường trống, không dịch cột. Ký hiệu thửa có / như 26/9 thuộc thửa, không phải thời hạn.

Ký hiệu tờ bỏ mô tả “Bản đồ địa chính năm…”, `do <cơ quan>` và phần nhãn thừa. Danh sách số thuần `112, 115` tách theo nguồn; dấu phẩy của địa chỉ/diện tích không thành danh sách số thửa. “Hiện nay/Nay là thửa/tờ…” là ghi chú đánh số lại theo spec loại, không tự mở tài sản khác.

**Kiểm:** cột `Số thửa | Số tờ`, giá trị `211 | 9` trả thửa 211/tờ 9; bảng có tờ trống vẫn trả thửa và các dữ liệu còn lại.
**Owner 15/10/2026:** thông tin của một thửa được viết liên tục trong cùng
khối nguồn; cặp `so_thua_dat` + `so_to_ban_do` là dấu hiệu phân biệt chính.
Đọc các dòng chi tiết nối tiếp vào đúng thửa, không tạo thửa mới chỉ vì đổi
loại đất/diện tích/thời hạn. Cặp thửa/tờ khác mở thửa khác. Thiếu dấu hiệu rõ
thì giữ nguồn và gắn cờ; không tự nối sang file/địa phương/hồ sơ khác hoặc bỏ
bản lặp mâu thuẫn. Đây không phải khóa định danh chung liên module.


### 2.5. Diện tích và chi tiết đất — Theo spec hiện hành, trừ cách gộp

- `dien_tich`: tổng diện tích nguồn ghi riêng; giữ chữ/số gốc theo luật đã có, bỏ phần bằng chữ và đuôi mô tả. Không suy tổng từ chi tiết hay làm tròn.
- `chi_tiet_dien_tich`: từng dòng chi tiết với diện tích, mục đích, thời hạn, ghi chú. Tổng và chi tiết là hai dữ liệu phải kiểm riêng.
- `muc_dich_su_dung`: giữ loại/mục đích nguồn ghi; không suy mã khi thiếu căn cứ. Nhãn đất dài không tự biến thành văn xuôi rác vì vượt một số ký tự.
- `thoi_han_su_dung`: đúng ô thời hạn; không nuốt số diện tích chi tiết kế. MM.YYYY là biến thể đã hỗ trợ.
- `phan_ghi_them`, `nguon_goc`: giữ ghi chú/quyền sử dụng/đánh số lại hoặc nguồn gốc vào đúng trường; không bỏ dữ liệu chỉ để hết R10.
- `land_rows`: dữ liệu đất đọc được từ chi tiết, giữ loại nguồn và thời hạn. Diện tích không đọc chắc thành số để nguyên + báo mơ hồ; “1.234” chỉ dấu chấm vẫn theo regex-decision-46.

Chỉ loại khỏi kiểu đất khi có bằng chứng cấu trúc là tiêu đề/câu kể như “Di sản của ... để lại”, “Chúng tôi thống nhất ...” hoặc “Các bên thống nhất phân chia ...”; giữ đoạn nguồn/diện tích/thời hạn trong `phan_ghi_them` và gắn R13 cần kiểm mục đích. Nhãn đất dài và ô trống không tự trở thành văn xuôi; không dùng chiều dài làm bằng chứng duy nhất. Không tự chốt cách xử lý hai phiên bản diện tích/thời hạn ở phần Quyết định 15/10 và phần cần đối chiếu.

**Kiểm:** `40 | Đất trồng cây lâu năm và đất nuôi trồng thủy sản | 12/2043` giữ chi tiết và land_rows. Một phép kiểm đạt tổng nhưng chưa kiểm chi tiết/thời hạn/ghi chú chưa phải nghiệm thu toàn bộ.

### 2.6. Giấy chứng nhận — Theo spec hiện hành

`loai_gcn` là loại giấy ghi trong nguồn; `so_gcn/so_gcn_raw` là chuỗi nguồn, không áp điều kiện hai chữ hoa + số để công nhận bản ghi. Có thể trống/trùng theo quyết định owner. `so_vao_so, ngay_cap_gcn, co_quan_cap` đọc đúng nhãn/ô cấp giấy; không lấy ngày cấp căn cước hoặc ngày ký văn bản khác.

Context GCN/địa chỉ chung thuộc đúng nhóm thửa có thể copy vào các thửa theo spec loại. Nhiều giấy hoặc nhiều giá trị trái nhau không được tự chọn; các quyết định phạm vi gộp chưa rõ vẫn chờ.

Danh sách mô tả tài sản đánh số, mỗi mục một GCN rõ, giữ từng bản ghi dù không ghi số thửa; không suy số thửa pháp lý. Địa chỉ trước số thửa thuộc cùng mục vẫn được giữ. Nhãn `Số vào sổ cấp GCN:` hoặc `Số vào sổ cấp giấy chứng nhận số:` đọc đúng giá trị sau nhãn. Chỉ dùng vùng tài sản, không quét toàn văn để bù.


### 2.7. Trường chưa hỗ trợ và phạm vi

Sổ tiết kiệm/tài khoản và bảo hiểm chỉ nhận diện `tai_san_chua_ho_tro` + R12 theo regex-decision-46, không tạo dòng tài sản đầy đủ. Xe/tàu theo giới hạn loại hiện hành. Quê quán giữ khả năng đọc snapshot cũ; intake không tự điền.

**W05 owner 20/10/2026:** đất đai có tài sản (thường nhà ở trên đất) vẫn là loại
nghiệp vụ có thật, có option Nam Định **ID1**. Chưa có hợp đồng mẫu để rút rule
regex nhà/công trình không có nghĩa loại không tồn tại/thuộc A10 bị loại. Ghi
thiếu catalog/rule/nguồn; không tự dựng schema/regex hoặc đọc mẫu khi gate đóng.
**A10 đã duyệt** giữ xe/sổ tiết kiệm/bảo hiểm nhận diện + nguồn, pending structured;
#29 mua bán xe vẫn DEFERRED, không tự mở tài chính/extraction đầy đủ.

Số/ngày công chứng và tên công chứng viên phục vụ upload/audit theo flow riêng; không dùng làm tiêu chí “trích đúng người/tài sản”. Trang này không tự mở schema hoặc field mới.

**Pháp nhân — owner 20/10/2026:** pháp nhân **không đưa vào Người**, không thêm
loại pháp nhân vào Person và không tự phân loại tổ chức thành thể nhân. Theo
policy, người dùng nhập tay; code hiện tại chưa cutover. Hướng chuẩn hóa thành một bảng riêng sau này là định hướng,
**chưa duyệt schema/build**. Hồ sơ thế chấp là trường hợp mặc định có pháp nhân;
loại khác ít xảy ra. Điều này không cho phép tự tạo tên ngân hàng/đại diện/default;
pháp nhân khác giữ nguồn và để
người dùng nhập tay, không âm thầm bỏ hoặc tự xếp loại.

**Cụm trường phụ website — owner 20/10/2026:** có thể dùng thêm một trường để
giữ cả cụm khi cụm phức tạp, không lặp lại và thuộc một ô nhập của một website
cụ thể. Đây là ngoại lệ hẹp, không phải quyết định biến ba editor hoặc mọi ô web
thành block/trường phụ. Khi chọn cụm phải xác định website/phạm vi ô, nghĩa
nghiệp vụ, lý do không tách, kiểu lưu và provenance; ưu tiên trường canonical
Người/Tài sản/Hồ sơ đã biết; chỉ hỏi owner khi có quyết định nghiệp vụ thực sự
chưa rõ, chi tiết kỹ thuật do implementation sở hữu theo contract/rule đã duyệt.
Không dùng `ghiChu` chung hoặc JSON bag chung thay trường; raw capture chỉ là
provenance, không thay trường nghiệp vụ; không tự đặt canonical key/tên/kiểu/
nhóm/storage; không dùng cụm để tự bóc pháp nhân. Cụm có thể là trường riêng
theo ô; phần tái dùng được vẫn map canonical, không mặc định coi cụm là dữ liệu
chưa map/orphan. Chưa chọn cụm/ô nào trong lượt tài liệu này.

**Nam Định §7 — owner trả lời 20/10/2026, policy đích chưa runtime cutover:**

- **R06 — requester Nam Định/Upload theo đáp án #43:** mọi cá nhân sống A/B/
  đại diện theo ủy quyền; không người chết, công chứng viên, nhân viên trong
  output này. Không xóa dữ kiện Người chết/Stage/Hồ sơ thừa kế/raw/history
  hoặc metadata nhân sự. Cá nhân dùng chuẩn, không prose/lookup/firstperson.
  Ngân hàng thế chấp hiện cả cụm nhưng không Person; **BANKMODE chưa chọn**
  mode user dán hay app lấy-điền cụm ngân hàng thế chấp; cá nhân khác vẫn chuẩn.
  Requester không cần tag A/B đã gán: cá nhân sống một bên/đại diện ủy quyền
  vẫn vào khi nhóm chưa gán hoặc conflict.
- **D04** lời tư cách/căn cứ phức tạp bỏ khỏi tự động điền, user tự sửa; không
  block mới, không mất nguồn hoặc mở manual fallback mọi gap. **D08 theo R06**,
  không residual prose block và không hỏi lại.
- **D05 đã trả lời:** ủy quyền A=người ủy quyền/B=người được ủy quyền; một bên
  không gán A/B; nguồn trái nhau giữ conflict/xác nhận phần nhóm, không tự
  winner hoặc thu hẹp requester. “Nhận” không universal regex/“không nhận=A”.
- **D06+D07 #43:** phân tích 16 ca và kết luận bảo toàn đã có; membership/
  A-B đã trả lời, chỉ BANKMODE còn cần làm rõ. Không tự extractor/canonical
  pháp nhân, không blanket raw block mọi editor; nhập tay pháp nhân trước đó
  không tự quyết mode “dán” mới. Chưa model/FK/schema/cutover; #42 độc lập.
- **A09 chưa duyệt block**: toàn đoạn tài sản ghép từ các field chuẩn khác
  lời dư thật chưa map. [SOT §7.5.1](../upload_lab/nam-dinh-website-sot.md) lưu
  trường thực/ví dụ tổng hợp và wire/model gaps; không nhét `phan_ghi_them`
  hỗn hợp vào hình thức sử dụng/ghi chú hoặc bịa trường nhà.

**Owner 20/10/2026 chốt chỉ dùng placeholder và trường tĩnh**: không mở trường
tầng 2 động/tính toán, engine công thức/điều kiện, hay persisted canonical text
từ suy ra. Đề xuất hai tầng trước đây chỉ là lịch sử chưa triển khai. Cụm **text
tĩnh** theo ô website vẫn theo quyền có điều kiện ở trên, chưa chọn field và
A09 chưa duyệt; dữ kiện nguồn tĩnh tách khỏi output/placeholder. Không quyền
parser/test/corpus từ lượt docs này; #41 mở, gate mẫu vẫn **ĐÓNG**.

### 2.8. Quyết định 15/10 và phần cần đối chiếu

| Mục | Owner đã chốt | Phần phải đối chiếu trước khi đổi engine/đáp án |
|---|---|---|
| F04 | Theo quy tắc định danh thửa: khối liên tục, phân biệt chính bằng số thửa + số tờ | Các mẫu có tổng trái nhau phải đọc nguồn; không tự lấy bản đầu hoặc bỏ phần khác |
| F05 | Trường/định dạng theo DB đã duyệt; chi tiết thuộc đúng thửa/cụm | Giữ bộ loại đất–diện tích–thời hạn theo `contracts/entities.md`; alias cũ phải ánh xạ rõ. Hai giá trị mâu thuẫn không được tự chọn một phía |

Quyết định về cấu trúc không phê duyệt một thuật toán gộp hoặc đáp án mẫu chưa
được đọc tay. Engine/fixture có thể còn theo luật cũ; mục `pending_decision`
cũ vẫn phải được kiểm lại, không biến “bỏ qua” thành “đạt”.

<a id="types"></a>
## 3. Nhận loại và vùng văn bản

### 3.1. Catalog theo loại

#### 2.1. Hợp đồng chuyển nhượng (`DOC_KIND_TRANSFER`)
- **Nhóm HĐ**: `Chuyển nhượng - Mua bán`
- **Tiêu đề canonical**: `Hợp đồng chuyển nhượng quyền sử dụng đất` (hoặc kèm tài sản gắn liền với đất)
- **Đương sự**:
  - `Bên A`: Bên chuyển nhượng
  - `Bên B`: Bên nhận chuyển nhượng
  - Người yêu cầu công chứng: **tất cả Người trong Hồ sơ** theo R06; ưu tiên Bên B là luật cũ đã bị thay trong business spec, runtime có thể chưa cutover.
- **Tài sản**:
  - *Điểm bắt đầu*: `quyền sử dụng đất ... có địa chỉ tại:` hoặc `Đối tượng của Hợp đồng này là...`
  - *Điểm kết thúc*: Dừng trước `1.2`, `Điều 2`, `Giá chuyển nhượng`, `Phương thức thanh toán`, `Bằng Hợp đồng này`.

#### 2.2. Văn bản cam kết tài sản riêng (`DOC_KIND_ASSET_COMMITMENT`)
- **Nhóm HĐ**: `Thoả thuận - Cam kết`
- **Tiêu đề canonical**: `Văn bản cam kết tài sản riêng`
- **Đương sự**:
  - Gồm cả 2 vợ chồng (Người chồng - Ông ... / Người vợ - Bà ...).
  - Người yêu cầu công chứng: **tất cả Người trong Hồ sơ** theo R06, không chỉ người đứng tên cam kết.
- **Tài sản**:
  - *Điểm bắt đầu*: `quyền sử dụng đất ... có địa chỉ tại:` hoặc `hiện đang sở hữu Tài Sản là` / `Tài Sản là`.
  - *Điểm kết thúc*: Dừng trước `Bằng văn bản này chúng tôi xác định`, `Hai vợ chồng chúng tôi cam kết`, `Chúng tôi công nhận`.

#### 2.3. Văn bản thỏa thuận hủy bỏ / sửa đổi / bổ sung (`DOC_KIND_TRANSFER_CANCELLATION`)
- **Nhóm HĐ**: `Thoả thuận - Cam kết` (hoặc `Phụ lục hợp đồng - văn bản sửa đổi`)
- **Tiêu đề canonical**: `Văn bản thỏa thuận về việc hủy bỏ hợp đồng chuyển nhượng quyền sử dụng đất`
- **Đương sự**: 2 bên tham gia thỏa thuận hủy bỏ.
- **Tài sản**: Đoạn trích tham chiếu thông tin thửa đất/GCN từ hợp đồng gốc, dừng trước `và được Công chứng viên chứng nhận`, `số công chứng`.

#### 2.4. Hợp đồng thế chấp (`DOC_KIND_MORTGAGE`)
- **Nhóm HĐ**: `Cầm cố - Thế chấp - Vay`
- **Tiêu đề canonical**: `Hợp đồng thế chấp quyền sử dụng đất` (hoặc kèm tài sản gắn liền với đất)
- **Đương sự (hành vi hiện tại, giữ để đối chiếu):**
  - `Bên A`: Bên thế chấp (cá nhân/hộ gia đình).
  - `Bên B`: Bên nhận thế chấp; nguồn thường nêu ngân hàng/pháp nhân/chi nhánh + người đại diện ký. Đây là vai trò theo nguồn, không phải dữ kiện mặc định.
  - Không có heading `BÊN NHẬN THẾ CHẤP` thì phần mở đầu trước `BÊN THẾ CHẤP` (ngân hàng + đại diện, mẫu Lời chứng Agribank/VB sửa đổi) được coi là Bên B (11/10/2026, hành vi legacy).
  - Người yêu cầu công chứng: cá nhân sống A/B/đại diện ủy quyền theo #43, không người chết/CCV/nhân viên; ngân hàng cả cụm không Person, BANKMODE còn mở. Không xóa dữ liệu nguồn/Person lịch sử, không chỉ B/đại diện ngân hàng.
  - **Pháp nhân không bóc thành Người (policy đích 20/10/2026):** người dùng nhập
    tay; không tự tạo tên ngân hàng/chi nhánh/người đại diện hoặc default party
    fact, không thêm loại pháp nhân vào Person. Hành vi legacy ở trên vẫn là hiện
    trạng cần đối chiếu, chưa phải target extraction. Bảng pháp nhân riêng tương
    lai là định hướng, chưa duyệt schema/build (decision 20/10/2026).
- **Tài sản**:
  - Trích xuất thông tin thửa đất / GCN từ phần mô tả tài sản hoặc trích xuất tối thiểu `Quyền sử dụng đất`.

#### 2.5. Phân chia di sản

Nhóm Thừa kế (khai nhận - phân chia di sản thừa kế ); tiêu đề Văn bản phân chia di sản. Vùng người/tài sản và marker tại thừa kế §1–4. Tên, danh xưng, ngày, giấy tờ, địa chỉ và dữ liệu đất tại quy tắc trường.

#### 2.6. Từ chối nhận di sản

Nhóm Từ chối nhận di sản thừa kế; tiêu đề Văn bản từ chối nhận di sản. Tôi là/Chúng tôi là hoặc Văn bản từ chối nhận di sản này được lập bởi mở nhóm người từ chối; dừng trước Nay, tôi/chúng tôi tự nguyện lập Văn bản này hoặc Theo quy định của pháp luật. Tài sản có thể nhiều mục Tài sản thứ N, mở từ mô tả di sản; dừng trước Bằng Văn bản này ... từ chối, Tôi xin cam đoan, Người từ chối hưởng di sản, Lời chứng. Trường dùng luật chung; phạm vi người chết chỉ-năm theo spec loại.

#### 2.7. Khai nhận di sản

Tiêu đề chứa khai nhận di sản; nhóm thừa kế. Marker mở dùng chung với phân chia; nhãn NGƯỜI KHAI NHẬN DI SẢN. Xem spec loại, giữ quy tắc giá trị trường đã trình bày ở trên.

#### 2.8. Sổ tiết kiệm/tài khoản và 2.9. Bảo hiểm

Theo regex-decision-46, chỉ nhận diện tài sản chưa hỗ trợ và R12; không trích dòng tiền/sổ/quyền lợi đầy đủ. Mô tả bóc chi tiết trong catalog cũ là lịch sử đã bị thay thế, không phải luật hiện hành.

<a id="inheritance"></a>
## 4. Vùng thừa kế và ranh bản ghi

### 4.1. Ba loại con

| Loại | Dấu hiệu tiêu đề | Mở đầu đương sự | Nhãn hiển thị |
|---|---|---|---|
| Phân chia (`inheritance_partition`) | `phân chia di sản`, `thỏa thuận phân chia di sản` | `Chúng tôi/Tôi là [những người] được hưởng di sản...`, `Người được hưởng di sản theo pháp luật/thừa kế của...`, `Tôi/Chúng tôi là người được hưởng di sản...`, `Hàng thừa kế... gồm những người có tên sau đây`, `Tôi tên là:` | NHỮNG NGƯỜI HƯỞNG DI SẢN |
| Từ chối (`inheritance_refusal`) | `từ chối nhận di sản` | `Tôi là:` / `Chúng tôi là:` (kể cả hưởng thế vị Anh/Chị) | NGƯỜI TỪ CHỐI NHẬN DI SẢN |
| Khai nhận (`inheritance_declaration`) | `khai nhận di sản` | dùng chung luật mở đầu với phân chia | NGƯỜI KHAI NHẬN DI SẢN |

Kết khối đương sự trước: `tự nguyện lập Văn bản này`, `Người để
lại di sản:`, `Di sản:`, `Khi còn sống`, `Trước khi chết`,
`Bố/mẹ đẻ`, `Chúng tôi là những người thừa kế`, `LỜI CHỨNG`.

### 4.2. Người sống (mỗi người 1 bản ghi)

| Trường | Quy tắc áp dụng |
|---|---|
| `ho_ten, ten_goi_khac, gioi_tinh` | Người: tên sạch, danh xưng trung tính để trống |
| `ngay_sinh, chi_co_nam_sinh` | Ngày/năm, không tự thêm 01/01; bảng phải giữ đúng cột |
| `cccd, noi_cap, ngay_cap_cccd` | Giấy tờ đúng người; không lấy ngày làm nơi cấp |
| `dia_chi` | Nhãn/vùng đúng người; ngày thuần không phải địa chỉ |

Bỏ cả dòng phả hệ (`Ông X có vợ là bà Y (Sinh ngày...)`) và khối
dừng trước dòng `chết ngày`.

### 4.3. Người chết (`raw.nguoi_chet`, bắt buộc có `chết/đã chết ngày DD/MM/YYYY`)

Trường người chết dùng quy tắc trường §3.
Dấu hiệu chết và vùng khai ở đây quyết định đây là người để lại di sản;
không đổi người chỉ để đầy đủ giấy tờ.

Dạng ngoặc gộp (11–12/10/2026): `ông X (sinh năm 1956, đã chết ngày ...)` và
`ông X (Tên khác); (Sinh năm 1945, đã chết ngày ... theo trích lục...)` —
ngoặc bí danh có thể đứng trước ngoặc sinh/chết; phần trong ngoặc sau
ngày chết (`theo trích lục`, `Nơi thường trú`) vẫn được chấp nhận.

**Lần nhắc lặp:** luật “bản sau điền trường trống” của v1.2 là hiện trạng đã ghi,
không tự mở rộng cách gộp tài sản. Ranh giới owner đã chốt và phần cần đối
chiếu xem quy tắc trường §8.
Danh sách số thửa 112,115 và ghi chú đánh số lại vẫn theo quy tắc định danh trường;
không tự chọn cách gộp các bản lặp.

### 4.4. Tài sản đất (mỗi thửa 1 dòng `danh_sach_thua_dat` + `land_rows` cấu trúc đầu ra)

`danh_sach_thua_dat`/`land_rows` ở đây mô tả kết quả bóc theo từng hàng để
giữ và kiểm dữ liệu thửa; đây có thể là kết quả một phần từ nguồn. Cụm “cấu trúc đầu ra”
trong heading là cách gọi cũ cho hướng nhóm dữ liệu, không chứng minh kết
quả trùng schema DB hoặc Stage wire của module khác. Nếu chuyển kết quả một phần
sang chức năng khác, ánh xạ theo contract đích; việc xác nhận với người dùng và
ghi DB đi theo luồng của chức năng nhận, không tự lưu kết quả một phần hoặc gộp
hàng thiếu căn cứ.

Khối đất mở bằng: `quyền sử dụng đất ... có/tại địa chỉ:`, `Phần
quyền sử dụng đất ... trong khối tài sản chung...`, `... theo
Giấy chứng nhận`, hoặc `thửa đất số ... (có địa chỉ tại/theo
GCN/theo bản đồ)`. Dừng trước: `Người/Những người thừa kế/nhận
thừa kế` (kể cả `III.`, `III. |`), `Nội dung/Thống nhất phân chia`,
`Bằng Văn bản này`, `Lời chứng`.

| Trường thửa | Quy tắc áp dụng |
|---|---|
| `so_thua_dat, so_to_ban_do` | Định danh thửa, giữ nhãn/cột cả khi đảo thứ tự |
| `dien_tich, chi_tiet_dien_tich, land_rows` | Diện tích/chi tiết, tổng độc lập |
| `muc_dich_su_dung, thoi_han_su_dung, phan_ghi_them, nguon_goc` | Giữ dữ liệu đúng ô; không cắt vì nhãn dài |
| `dia_chi, loai_gcn, so_gcn, so_vao_so, ngay_cap_gcn, co_quan_cap` | Giấy chứng nhận |

Owner 15/10/2026: trong khối tài sản liên tục, phân biệt chính bằng số thửa
+ số tờ; các chi tiết nối tiếp thuộc đúng thửa đó. Không tự giữ bản đầu rồi
bỏ thông tin khác. Các giá trị tổng/thời hạn mâu thuẫn vẫn phải đối chiếu nguồn
theo quy tắc trường §8.

Hai luật chống nhiễu (10/10/2026): **bảng liệt kê người** (ô chứa
`Sinh ngày/năm`, `CCCD`, `Hộ khẩu`, hoặc ô đầu dạng `1. Ông/Bà ...`)
không được nhập vào `chi_tiet_dien_tich`; **thửa chỉ có GCN** — văn bản
mô tả đất bằng `theo Giấy chứng nhận ... Số X do ... cấp ngày` nhưng
không có số thửa/tờ — vẫn tạo 1 bản ghi giữ `so_gcn`/`dia_chi`/
`co_quan_cap`/`ngay_cap_gcn` thay vì trả về rỗng (R09 hết báo sai).

Bảng `.doc` (IFilter giữ ô bằng TAB → code đổi thành `|`,
cắt `|` thừa đầu/cuối, tên cắt trước `|`): bảng dồn 1 dòng thì tách
theo dòng ô (ô `Số thửa` làm neo); tiêu đề tách 2 dòng thì nối lại;
dòng văn xuôi >100 ký tự trong vùng bảng thì bỏ; `Trong đó: | ...`
thì cắt mốc giữ ô.

**Chưa được owner duyệt (xác nhận lại 15/10/2026):** đoạn bảng đơn dòng
dưới đây thuộc đề xuất decision-72, không phải luật Active để triển khai hoặc
chấm đạt. Không suy việc duyệt từ engine hiện có.

Bảng **đơn dòng** (không `|`, không xuống dòng — đề xuất 12/10/2026): token hóa
thành "ô giả" — số đứng riêng, cụm chữ gộp, `Trong đó`/`Lâu dài` thành
ô riêng — rồi dùng chung bộ tách ô với bảng `|`; hỗ trợ **nhiều thửa**
liên tiếp (`35 44 150 NTS 2063  35 103 299  Trong đó ...  35 134 168`).
Ô số ngay sau thửa chỉ được nuốt làm `thoi_han_su_dung` khi giống kỳ
hạn (4 số, ngày `dd/mm/yyyy`, `Lâu dài`) — số diện tích nhỏ (`119`,
`299`) là thửa/chi tiết tiếp theo.

### 4.5. Tài sản sổ tiết kiệm / tài khoản — TẠM DỪNG (regex-decision-46)

Không bóc dòng. Khi văn bản có khối `sổ tiết kiệm` / `số dư tài khoản`,
engine chỉ ghi `"so_tiet_kiem"` vào `raw.tai_san_chua_ho_tro` và R12
cảnh báo để nhân viên biết file có phần này.

### 4.6. Quyền lợi bảo hiểm — TẠM DỪNG (regex-decision-46)

Tương tự sổ tiết kiệm: nhận diện khối `quyền lợi bảo hiểm` → `"bao_hiem"` trong
`raw.tai_san_chua_ho_tro` + R12. Không trích `so_hop_dong`, `ben_bao_hiem`...

### 4.7. Lời chứng — KHÔNG TRÍCH (regex-decision-46)

Không đối chiếu với người đầu văn bản nên không bóc người trong Lời chứng;
không còn `raw.loi_chung_nguoi` và luật R11.

<a id="acceptance"></a>
## 5. Đọc nguồn và đánh giá kết quả

### 5.1. Phân loại trước khi sửa

| Loại | Cách xử lý | Có tính là máy đọc đúng? |
|---|---|---|
| Đáp án thiếu/sai, bộ chấm bỏ qua trường hoặc dùng output cũ | Sửa bộ chấm; sửa đáp án bằng bằng chứng nguồn, lưu lớp đính chính riêng | Chỉ các trường đã kiểm lại |
| Nhãn/vùng rõ thuộc loại đã hỗ trợ nhưng mất người, đất hoặc lấy nhầm trường | Sửa engine chung, kiểm cả đầu vào và đầu ra thật | Sau khi so đúng trường và số bản ghi |
| Nguồn dính chữ, sai chính tả hoặc giá trị không hợp lệ | Giữ phần regex lấy được; người dùng kiểm/sửa tại các ô Stage hiện có | Ghi cần kiểm nguồn, không biến thành đạt |
| Không đủ ranh nhóm/nhãn hoặc bố cục khác ngoài phạm vi công bố | Giữ nguồn, ghi lý do; đề xuất mẫu/phiên bản riêng nếu cần | Chưa hỗ trợ, không tính đạt |
| Quyết định nghiệp vụ chưa chốt | Giữ Pending, không chọn nghĩa hộ owner | Không |

Không đặt tỷ lệ 90/95% hay mục tiêu hoàn hảo. Mỗi lượt báo rõ số file, số bản ghi, trường đã kiểm, lỗi máy, nguồn cần sửa, ngoài phạm vi và Pending. Kết quả đúng một phần phải gọi là **khớp các trường đã kiểm**, không gọi cả file đạt.

### 5.2. Đợt 50 file Hưng 3930–3979

E1/E2/E3 là nhãn đại diện rõ, kể cả thiếu dấu hai chấm, chức danh sau dấu gạch hoặc ô TAB. Giữ đúng bên A/B bất kể thứ tự; không gán địa chỉ người thế chấp cho đại diện ngân hàng.

E5 là các mục GCN đánh số rõ: giữ mỗi mô tả tài sản riêng dù không có số thửa; không suy số lượng thửa pháp lý. E6 giữ địa chỉ đứng trước số thửa trong cùng vùng. E7 mở đúng vùng tài sản của cam kết hai dòng; parser đất hiện có đọc được dòng gạch. Không đọc toàn văn rồi mượn CCCD/địa chỉ văn phòng làm dữ liệu đất. Đây là lỗi engine, không có căn cứ đẩy sang mẫu ngoài phạm vi.

E4 có token dính `036064005865do` ngay trong byte Word: lỗi nguồn có thể kiểm tay. Nhưng lấy cơ quan cấp GCN để điền nơi cấp CCCD vẫn là lỗi engine phải chặn. Thiếu bằng chứng thì giữ trống/phần đọc được; không đoán hoặc sửa “Bộ Coongan” thành “Bộ Công an”.

Đáp án 3970 thiếu đuôi `, tỉnh Ninh Bình`; đính chính phải dựa trên dòng nguồn, giữ nguyên bộ đáp án TASK-10.2 để truy lại. Batch này chưa kiểm các mẫu F04/F05; phần phân biệt thửa/cấu trúc đầu ra đã được owner làm rõ 15/10/2026 tại regex-fields, chưa duyệt lại đáp án các mẫu mâu thuẫn.

### 5.3. Kết quả cho người dùng sửa

Owner chốt: **không thêm chức năng hoặc luật sửa lỗi nguồn**. Regex lấy được gì thì điền vào kết quả tương ứng trong Stage hiện có. Số giấy tờ/nơi cấp là chữ tự do; giữ chữ nguồn, không vứt giá trị chỉ vì sai chính tả hoặc khác mẫu. Chỉ gắn cảnh báo khi có căn cứ xác định trường cần kiểm; không hứa phát hiện mọi lỗi.

Không thêm ô nguyên văn, bảng hay nút mới; không dán dữ liệu vào một trường khác nghĩa. Bằng chứng gốc vẫn thuộc nguồn nhập. Nhiều giá trị chưa chọn hoặc ngày/diện tích không hợp lệ vẫn theo quy tắc kiểm hiện hành trước khi nhận/lưu, không lấy một giá trị tùy ý.

### 5.4. Bộ chấm

- `null`/thiếu là chưa trả lời; `""`/`[]` là đã kiểm và cần rỗng. Giữ riêng hai nghĩa.
- Kiểm tên có dấu, cờ năm sinh cả true/false, từng trường người chết và chi tiết đất đã trả lời; so mỗi bản ghi một lần, không dùng một thửa để khớp hai đáp án.
- Lỗi extract không được thành đạt. Báo số trường đã kiểm/chưa kiểm; ca chỉ có một trường không chứng minh cả file đúng.
- Output phải gắn hash nguồn, engine, validator, bộ chấm, đáp án và lớp đính chính. Đổi bất kỳ phần nào thì chạy mới; không gắn tên engine mới cho output cũ.
- Giữ 50 đường dẫn trong mẫu số kể cả bản sao giống byte. Đáp án đọc từ nguồn, không sửa để khớp máy.

Luật trường, đáp án và Pending nằm trong các phần tương ứng của chính tài liệu này. Luồng Stage ở [nhập DOCX](../notary_v2/word-templates.md#docx-import).

<a id="expected"></a>
## 6. Ví dụ và đáp án phải kiểm

### 6.1. Cách ghi

Mỗi ca có mã, nguồn, phạm vi, trường phải kiểm, đáp án, cảnh báo và trạng thái. `closed_existing_spec` nghĩa là suy ra từ yêu cầu đã có; không phải một Golden được owner duyệt mới. `pending_decision` không chạy như test đã đạt. Đáp án là tập trường đã đọc tay, không tuyên bố toàn bộ hồ sơ đã đúng.

| Giá trị | Nghĩa | Tính vào đã kiểm? |
|---|---|---|
| `""` | Đã đọc và trường cần để trống | Có |
| `[]` | Đã đọc và không có bản ghi | Có; máy trả thừa phải thất bại |
| `null`/thiếu | Chưa trả lời trường đó | Không |
| Pending | Chưa chốt hành vi | Không; phải hiện danh sách riêng |

Nguồn thật phải có đường dẫn, dấu vân tay file/text, đoạn được kiểm và phiên bản engine. Dữ liệu cá nhân ở `.agents/task-10.1/`; các test lưu lâu dài dùng tên/số giả và giữ cấu trúc.

### 6.2. Mẫu Closed từ quy tắc đã có

| Ca | Đầu vào trọng tâm | Đáp án đích phải kiểm | Cờ | Quy tắc |
|---|---|---|---|---|
| C01 | Đồng sở hữu – Cháu Lê Minh An; Sinh ngày 21/11/2011 | ho_ten=Lê Minh An; gioi_tinh=""; ngay_sinh=21/11/2011; không mất người | R13 | Tên/giới tính |
| C02 | Đồng sở hữu – Con Lê Minh An; Sinh ngày 21/11/2011 | Tên sạch; giới tính trống; không tự biến thành Bà | R13 | Quy tắc Người |
| C03 | Số thửa \| Số tờ; hàng 211 \| 9; hàng 212 \| 10 chung dòng | Đúng 2 thửa; thửa/tờ tương ứng 211/9 và 212/10; giữ diện tích/mục đích/thời hạn | Không tạo R10 giả | Định danh thửa |
| C04 | Số tờ \| Số thửa; tờ đầu trống, thửa 211; tiếp thửa 212 | Giữ cả 2 thửa; thửa 211 có tờ trống; các cột không dịch | Thiếu dữ liệu được phản ánh trung thực | Quy tắc thửa |
| C05 | 40 \| Đất trồng cây lâu năm và đất nuôi trồng thủy sản \| 12/2043 | Chi tiết có đủ 3 trường; land_rows có loại, diện tích 40, thời hạn | Không bỏ dữ liệu vì nhãn dài | Chi tiết đất |
| C06 | STT TAB Bà Lê Ngọc Mai TAB 01/01/1980 TAB CCCD TAB số TAB 10/05/2021 TAB Bộ Công an TAB xã Minh Tân | ngay_sinh=01/01/1980; ngay_cap_cccd=10/05/2021; noi_cap=Bộ Công an; địa chỉ đúng | Không lấy ngày sinh làm ngày cấp | Quy tắc Người |
| C07 | Bà Lê Ngọc Mai – Sinh 26/04/1985, có CCCD và địa chỉ | Đúng 1 người, tên và ngày sinh đúng qua hàm thật | Theo dữ liệu còn thiếu | Quy tắc Người |
| C08 | Người có ngày sinh; Địa chỉ: 23/10/2023 | Đúng người; dia_chi=""; địa chỉ cấp bên cũng không là ngày | R03 thiếu địa chỉ | Quy tắc Người |
| C09 | Hai người; Cả hai cùng thường trú tại: 23/10/2023 | Cả hai địa chỉ trống; không gán lại ngày từ đường chung | R03 | Quy tắc Người |
| C10 | Người có nhãn địa chỉ keyed chỉ mang 23/10/2023 | Tên/ngày sinh vẫn giữ; địa chỉ trống | R03 | Quy tắc Người |
| C11 | Mẫu không có người/không có đất đã đọc xác nhận | Danh sách tương ứng [] | Theo loại; không tự bịa bản ghi | Cách ghi đáp án |
| C12 | Bà Lê Ngọc Mai; Sinh năm 1980 | ngay_sinh=1980, chi_co_nam_sinh=true; không tự thêm 01/01 | Theo trường khác | Quy tắc Người |

R03/R13 kiểm ở payload đầy đủ bằng validator, không đoán cờ từ số lượng ô. Cờ về các trường khác của mẫu thiếu có thể vẫn xuất hiện; phải kiểm cờ liên quan cụ thể.

Các ca đất C03–C05 có câu mở vùng tài sản trong đầu vào Word; kiểm danh sách
thửa từ `extract(filepath)` nguyên trạng, không thay bằng kết quả hàm phụ.
Fixture thực thi tại [Upload Lab](../../../upload_lab/tests/fixtures/word_field_cases.json) (nguồn duy nhất; bản snapshot trong tool đã gỡ 16/10/2026 — tool assemble từ repo, không chép tay).

Các biến thể giữ cùng quy tắc và được kiểm riêng:

| Nhóm | Biến thể phải kiểm |
|---|---|
| C01/C02 | Danh xưng trung tính kết hợp Ông/bà sau vai trò, tên sạch + R13 |
| C03/C04 | Dòng tiếp không có thửa, đuôi ô định dạng, ghi chú đánh số lại; đường `.doc` qua bước chuẩn hóa cũng giữ ô tờ trống |
| C05 | Nhãn đất dài hơn 100 ký tự vẫn giữ; câu kể “Di sản của…”, “Chúng tôi thống nhất…”, “Các bên thống nhất phân chia…” chuyển đủ nguồn vào ghi chú + R13, không thành loại đất |
| C06/C12 | Năm sinh trong bảng trước/sau giấy tờ; thiếu sinh hoặc thiếu số giấy tờ không lấy ngày cấp làm sinh; nơi cấp trống không nuốt địa chỉ |
| C07/C08 | Người chết cũng nhận Sinh trần và bỏ địa chỉ cuối thuần ngày |

Mẫu `.doc` tổng hợp giả phần đọc IFilter để kiểm đường chuẩn hóa và `extract`,
không được gọi là file `.doc` thật. Bằng chứng file thật ở phần Mẫu Word thật bên dưới.

### 6.3. Pending — giữ đầu vào, chưa chọn số bản ghi/giá trị

| Ca | Nguồn vấn đề | Điều đã thấy | Chưa chấm |
|---|---|---|---|
| P04/F04 | Cùng thửa/tờ, tổng 210 / 210,0 / 210 m2 hoặc tổng thật khác | Owner đã chốt ranh thửa theo khối liên tục + thửa/tờ | Cần đọc nguồn để ghi đáp án tổng/chi tiết; không tự duyệt số bản ghi của mẫu mâu thuẫn |
| P05/F05 | Chi tiết cùng diện tích+loại nhưng bổ sung hoặc đổi thời hạn/ghi chú | Owner đã chốt trường/format theo DB, giữ đúng cụm đất | Cần đọc nguồn để ghi đáp án từng trường; không tự chọn một giá trị mâu thuẫn |

Không coi nguồn tự viết là hồ sơ thật. Mẫu tổng hợp chứng minh hành vi trên cấu trúc đã hỗ trợ; tần suất trên hồ sơ thật cần đo riêng.

### 6.4. Mẫu Word thật

R01-real (mã ca, không phải cờ R01): file cam kết đồng sở hữu trong batch s283, vùng mở đầu có 4 người, 3 người mở bằng Cháu. Đáp án được đọc độc lập **chưa xem output máy** tại `.agents/task-10.1/chau.expected.json`; nguồn và dấu vân tay tại `chau.provenance.json`.

Kiểm đúng 4 người và từng trường tên/giới tính/sinh/căn cước/nơi cấp/ngày cấp/địa chỉ; giữ R13 cho ba người Cháu. Các trường tài sản, người chết, thông tin chung và vùng ký **chưa được chấm** ở ca này. Không suy toàn bộ file đúng từ 7 trường đã kiểm.

### 6.5. Điều kiện kết thúc một vòng

1. Closed: mọi trường kê trong ca đã kiểm bằng hàm thật; số người/thửa đúng, không bỏ chi tiết.
2. Pending và trường chưa trả lời được báo riêng, không cộng vào số đạt.
3. Bỏ một hỗ trợ trong code phải khiến phép kiểm tương ứng thất bại. Tiêu chí
   nghiệm thu là **test của lõi chung đối chiếu đáp án độc lập** (Closed C01–C12
   và ca mới có nhãn ghi rõ nguồn, tự soạn theo catalog trước khi xem output);
   bằng chứng lịch sử before/after của cutover 16/10/2026 (corpus nhãn tự soạn,
   duy nhất ca DOCX tổng hợp được lợi) nằm ở backlog/decision #22 và
   `_bmad-output/tmp/issue-22-regex-consumer-cutover/evidence/` — **không thay
   tiêu chí chung** và không được đọc thành "đã chứng minh mọi ca".
4. Có ít nhất một lượt đọc Word thật qua đường đọc đang dùng, không chỉ truyền text.
5. Không gọi approve/ghi Golden mới cho các mục chưa được owner duyệt.

Code test/fixture là bản thực thi đáp án ở đây; không có quyền sửa đáp án để hợp output máy. So theo số trường được kiểm, không dùng số test xanh hay số cờ làm tỷ lệ chính xác.

TASK-10.3 áp dụng ranh giới chấp nhận. Bộ chấm phải kiểm cờ năm sinh cả false và true, tên có dấu, từng trường người chết và ghép một-một; lỗi đọc không được thành đạt. Báo `MATCH_CHECKED_FIELDS` cùng phạm vi và số trường chưa trả lời thay vì suy cả file đạt. Lượt mới giữ nguyên bằng chứng TASK-10.2, dùng lớp đính chính có dòng nguồn và output/hash mới.

<a id="core"></a>
## 7. Vòng sửa engine

### 7.1. Cách làm việc (vòng lặp bắt buộc)

```text
mẫu thật → agent đọc MÙ source → viết đáp án expected.json (chưa nhìn output máy)
→ chạy engine → compare diff từng trường → sửa code → test giữ hành vi
→ quét hàng loạt → báo cáo vòng
```

1. Mỗi vòng làm **1 loại văn bản** (thừa kế trước, thế chấp tiếp).
2. Đáp án viết **trước khi nhìn output máy** — hai lượt tách rõ,
   vì nhìn trước sẽ làm agent chép lỗi của máy. Không dùng số ô
   được điền hay số cảnh báo làm thước đo đúng.
3. Không commit khi test đỏ. Không đoán số liệu trôi nổi: pattern
   nào cũng phải có nhãn neo (`Sinh năm`, `Số thửa`, ...).
4. Số liệu giữ nguyên chữ trong văn bản (diện tích tuyệt đối chính
   xác, không làm tròn). Thiếu căn cứ thì để trống + gắn cờ, không
   tự bịa, không tự suy mã.
5. Trong `expected.json`: `null`/thiếu = **chưa trả lời** (compare bỏ
   qua, nhưng file toàn null = lỗi); `[]` = **đã xác nhận không có**
   — máy bóc thừa sẽ bị bắt. JSON hỏng, thiếu thư mục đáp án hoặc
   cache từ engine/luật cũ (fingerprint lệch) đều khiến compare báo
   lỗi thay vì trả "đạt".
6. Golden đổi kết quả ≠ tự động tách phiên bản rule: trước hết xác
   định đáp án cũ sai, code cũ sai, hay biểu mẫu thật sự khác.

#### Lệnh của vòng (engine hiện hành: lõi chung; adapter `upload_lab/extraction_adapter.py`)

```bash
## quet hang loat + tong hop theo luat
python tools/quet_kiem_tra.py "D:\thu-muc-mau" --full --ra ket-qua.json

## tao goi doc mu: *.source.txt + *.expected.json (khong lo output)
python tools/regex_lab.py ingest --input "D:\thu-muc-mau" --cache .cache/rl
python tools/regex_lab.py review --blind --input "D:\thu-muc-mau" --cache .cache/rl --packets .cache/pk

## agent doc .source.txt, dien .expected.json, roi so
python tools/regex_lab.py compare --answers .cache/pk/<run> --cache .cache/rl

## sau khi sua code: golden hoi quy
python tools/regex_lab.py verify --input "D:\thu-muc-mau" --cache .cache/rl --golden regex_review_samples/golden
python tools/regex_lab.py approve --cluster <id>   # chi khi owner da duyet ket qua moi
```

### 7.2. Rule do developer quản lý (owner 16/10/2026)

Rule regex văn bản và rule upload theo từng website thuộc phạm vi developer;
rule có phân biệt phiên bản để nhận biết. Owner chốt 16/10/2026: "đây là phân
biệt dành cho developers, có phân biệt phiên bản để nhận biết. Users không
được dùng tính năng này."

Người dùng sản phẩm không có chức năng thử, công bố, chọn phiên bản hoặc
quay lui rule. Người dùng vẫn xem và sửa kết quả bóc tách trước khi nhận vào
Stage như quy tắc hiện hành; phần bị loại là quản lý rule, không phải duyệt
kết quả. Nơi lưu rule, định dạng, ghi nhận version/hash, kích hoạt/quay lui
nội bộ và phạm vi chạy lại là lựa chọn kỹ thuật của developer khi triển khai,
không phải câu hỏi nghiệp vụ; không thêm role/permission mới. Ghi canonical:
[decision-owner-regex-rule-developer-only-20261016](../../decisions/decision-owner-regex-rule-developer-only-20261016.md).

## 8. Tool nhân viên và thêm loại mới

Mở file/thư mục không cần phân loại trước; lỗi một file không dừng cả lượt. Chuột phải copy ô ngay, nút cuối dòng copy cả dòng; log JSONL là bản giao có phiên bản engine. PII chỉ ở máy nội bộ và gói người dùng chủ động gửi, không ghi log rộng. Bản tool gọi trực tiếp lõi chung qua adapter (chuyển 16/10/2026); không chép tay engine/validator.

Thêm loại văn bản cần mẫu thật, nhãn/vùng và đầu ra đã chốt; cập nhật nhận diện, parser, phép so từng trường và kiểm qua extract thật. Không dùng đáp án máy sinh làm chuẩn. Mục pending không gọi approve hoặc ghi Golden mới. Test/validator không thay việc đọc nguồn.

Các ý tưởng runtime hybrid/LLM và xử lý bảng đơn dòng chưa được duyệt; không tự thêm fallback. F04/F05 đã chốt nguyên tắc thửa/tờ và DB, nhưng đáp án mẫu mâu thuẫn vẫn cần đọc nguồn.

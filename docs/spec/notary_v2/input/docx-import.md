# Nhập hợp đồng Word và xuất theo bản gốc — NAIA-4 / MIN-139

**Trạng thái:** Active cho luồng DOCX local; độ chính xác trên hồ sơ văn phòng
chưa nghiệm thu. **Nguồn:** Owner NAIA-4 ngày 02–03/10/2026, bình luận
`01a0fd96-dc6d-77f5-a301-053b7eb6a651`, `01a0fd9b-ff2e-7e8c-be10-bbf2bfe91391`,
`01a0ff5c-5cf6-7e55-a2e8-597143bfb0d3`; Owner yêu cầu triển khai trong chat
04/10/2026. Bản Draft Document Field Studio được thu hồi để giữ ý tưởng
Word-first; hướng nhiều nguồn/tab thứ ba cũ không thuộc đợt này.

## Công dụng và thao tác

Một hợp đồng `.docx` có chữ → các gợi ý Người/Tài sản → chuyên viên xem chữ
gốc, chọn/sửa giá trị → Đưa vào Stage → Cập nhật/Lưu hồ sơ → Xuất Word →
Dùng hợp đồng Word đã nhập → chọn từng vị trí → Xác nhận và lưu → xuất vào
thư mục đích. Nút Tải JSON giữ bản kết quả phân tích ban đầu, trước mọi sửa đổi;
chỉ tải về máy. Các sửa đổi được lưu vào Stage, không ghi vào JSON ban đầu.

Giữ dialog Nhập file hiện có và đúng hai tab Upload Lab. `.doc`, ảnh/OCR,
Excel không dùng bản đồ vị trí DOCX trong đợt này. Mỗi trường giữ chữ gốc;
sửa là giá trị người dùng kiểm tra, không sửa bằng chứng ban đầu.
Hỗ trợ DOCX Word thông thường dùng namespace
`http://schemas.openxmlformats.org/wordprocessingml/2006/main`.
DOCX Strict dùng namespace khác chưa được hỗ trợ; cần lưu lại bằng Word theo
định dạng DOCX thông thường trước khi nhập, không coi file Strict là đã đọc đủ.
Cụm đất được sửa theo từng dòng loại đất/diện tích/thời hạn, không buộc người
dùng nhập mã JSON. Cả một dòng lẫn nhiều dòng đều giữ được.
Mỗi ô mơ hồ phải được chọn hoặc sửa riêng. Chọn ngày từ chữ gốc đổi về dạng
`YYYY-MM-DD` theo quy tắc ngày hiện có trước khi nhận vào Stage.
Ngày đầy đủ trong nguồn phải đúng lịch, kể cả dạng ISO như `1980-02-31`.
Ngày sai giữ nguyên chữ/vị trí nguồn, hiện cảnh báo và phải sửa trước khi nhận;
không lấy riêng `1980` để che phần tháng/ngày sai. Năm sinh đứng riêng vẫn được giữ.
Diện tích âm hoặc không phải số hữu hạn bị chặn ngay khi kiểm tra; giữ chữ
đang sửa và các ô đã duyệt khác. Phân tích thêm nguồn không làm mất thẻ hay
nội dung đang sửa của các gợi ý trước, kể cả khi lần mới lỗi hoặc bị hủy.
Ô diện tích nhận cả `1.234,5`. Có thể bỏ toàn bộ dòng đất đọc sai và giữ các
trường tài sản còn đúng; danh sách đất rỗng không gắn lại vị trí nguồn đã bỏ.

## Bóc trường, nhóm và Tại sao?

Document Intake đọc đoạn và bảng theo thứ tự XML thật, gồm ô vật lý và bảng
lồng; ô gộp không bị đọc hai lần. Text không bị strip trước khi tạo vị trí.
Mỗi vị trí là `[start,end)` theo ký tự Unicode, không theo byte. Chữ xuống
dòng/ngắt/tab cũng có vị trí nhưng không được thay như chữ bình thường.

Lõi regex chung `tools/regex_workbench/engine` sở hữu quy tắc có phiên bản;
không sao chép regex sang adapter (Owner NAIA-4 02/10/2026, khẳng định lại
06/10/2026). Lõi nhận input là file Word hoặc đoạn text thô dán vào; ngoài
trích xuất còn dùng kết quả chia vùng để đề xuất placeholder cho mẫu Word
chưa gắn template ở chức năng soạn hồ sơ (Owner 06/10/2026). Profile
`transfer` 1.1.2 chia người trong
vùng đương sự và tài sản có nhãn `Tài sản [thứ] N:`. Dòng `Loại đất:` mở một
cụm đất riêng. Một GCN có nhiều cụm vẫn là một tài sản. Đây là phạm vi mẫu đã
kiểm tra, chưa phải lời hứa nhận đúng mọi loại hợp đồng.
Nhãn tài sản ở tiêu đề trước vùng tài sản không mở nhóm chứa dữ liệu đương
sự. Dòng đất không có giá trị đọc được tạo cảnh báo thiếu dữ liệu; không
tạo bằng chứng giả và không làm mất người/tài sản hợp lệ của cả nguồn.

Không có ranh giới chắc thì giữ `ambiguous_group`; nhiều giá trị giữ mọi lần
thấy và `normalized_value=null`. Phải chọn/sửa trường mơ hồ trước khi nhận.
Serial là chuỗi nguyên văn tùy nguồn — không ép format, có thể trống,
có thể trùng giữa thửa (Owner 06/10/2026, `entities.md` §2). Trùng giấy
tờ/serial chỉ cảnh báo, không gộp. Không suy giới tính, vai trò, quan hệ
hoặc sở hữu từ lời hợp đồng. Lời chứng ngoài vùng đương sự giữ nguyên,
không tự thành người mới và không dùng để đối chiếu/đếm lại đương sự
(TASK-5). Người chết là một `person_row` có `ngay_chet`; giấy tờ của họ
(trích lục khai tử...) điền vào `so_giay_to`/`ngay_cap`/`noi_cap`/
`loai_giay_to` cùng format với người sống — không tạo entity riêng.
Sổ tiết kiệm và bảo hiểm **tạm dừng**: nhận diện sự hiện diện và gắn cờ
"loại tài sản chưa hỗ trợ", không bóc dòng (Owner 06/10/2026).
Thiếu trường vẫn cho kiểm tra và bổ sung ở Stage; quy tắc commit MIN-141 giữ
nguyên. Đủ 3 tài sản thì gợi ý tiếp theo vẫn còn, kèm lời báo hết chỗ.
Tài sản có bằng chứng địa chỉ hoặc cụm đất vẫn được giữ khi thiếu mọi mã
định danh; nhãn trống không tạo tài sản rỗng. Diện tích âm/không hữu hạn trong
nguồn giữ nguyên chữ và dấu trong bằng chứng, giá trị chuẩn là null và phải sửa
trước khi nhận. Diện tích lấy số đứng trước `m2`/`m²` làm mốc: `1234,5`,
`1.234,5`, `1234.0` đều đọc được; số chỉ có dấu chấm (`1.234`) là mơ hồ —
giữ nguyên văn, `normalized_value=null` + cờ (Owner 06/10/2026).
Bằng chứng mỗi ô đất hiển thị vị trí ký tự trong nguồn.

## Nguồn, dữ liệu và đối chiếu

Sidecar lưu byte Word gốc và `extraction.json` ở
`<engine-data/notary_v2>/docx_sources/<source_id>/`. `source_id` do backend
tạo, không phải đường dẫn do renderer chọn. `sha256` là dấu kiểm nội dung;
nguồn được kiểm lại trước mỗi lần lưu đối chiếu/xuất. Không ghi hồ sơ thật
vào Git, log rộng hoặc localStorage.
`extraction.sha256` giữ dấu kiểm byte của `extraction.json`. Thiếu, hỏng hoặc
không khớp thì phải nhập và kiểm tra lại; không tin bản đồ vị trí cũ.
Nguồn và mẫu chưa dùng vẫn được giữ cục bộ, kể cả khi hủy lần lưu hồ sơ.
Chưa có thời hạn giữ hoặc cách tự dọn được duyệt. Sao lưu/dọn thủ công phải
giữ mọi nguồn và mẫu còn được hồ sơ tham chiếu; **Gỡ nguồn** không xóa file.

Sao lưu chung: đóng ứng dụng và chờ sidecar dừng; xác định đúng thư mục
engine-data `notary_v2` mà phiên này đang dùng. Sao chép `notary.db` thực tế
cùng toàn bộ `docx_sources/` (gồm bằng chứng và mẫu) vào cùng một bản sao lưu,
không lấy DB trong source checkout thay cho DB engine-data. Khôi phục cả hai
từ cùng bản sao khi ứng dụng vẫn đóng. Thử trước trong môi trường bản sao:
mở hồ sơ đã nhập, kiểm hash nguồn/bằng chứng/mẫu và thử xuất theo bản gốc để
phát hiện thiếu hoặc lệch dữ liệu. Đây là cách thao tác đề nghị; chưa kiểm
phục hồi thực tế và chưa thay đổi giới hạn sao lưu/phục hồi đã ghi bên dưới.

`case_state_json.docx_import` version 1 chỉ giữ ID/hash nguồn,
`candidate_id→row_id`, danh tính từng dòng đất và vị trí đã duyệt. Nguồn có tên
file an toàn do backend tạo để phân biệt nhiều hợp đồng. Chữ gốc/quan sát ở package backend;
giá trị người dùng sửa ở Stage đã lưu. Context và Stage ghi trong cùng
transaction (một lần ghi trọn vẹn), dùng `base_revision` cũ thì từ chối cả
lần ghi. Create/get/commit trả lại context để mở hồ sơ khác hoặc tải lại không
mất đối chiếu. Hủy thay đổi khôi phục cả context đã lưu.

Đối chiếu Word là **một lần xuất hiện → ID dòng + trường + slot catalog**,
không phải “thay mọi chuỗi giống nhau”. Màn Word hiện chữ gốc, tên/ID dòng,
slot và giá trị sẽ xuất; checkbox hiển thị đúng lựa chọn đã lưu, nguồn mới chưa
chọn. Bỏ chọn hết rồi lưu sẽ xóa toàn bộ vị trí đã gắn.
Lúc đang lưu, khóa chọn vị trí; nếu lưu lỗi thì giữ lựa chọn và khôi phục
đối chiếu cục bộ trước lần xác nhận để người dùng thử lưu lại.
Nếu lưu thành công nhưng tải lại danh sách lỗi, đối chiếu và revision đã lưu
vẫn giữ nguyên. Màn báo rõ đã lưu, xóa lựa chọn cũ và cho chọn lại nguồn để thử
tải lại; không dùng danh sách cũ để xuất. Chọn nguồn khác cũng xóa ngay bảng cũ.
Người N theo Stage đã lưu, Bên A/B theo ô `p1..p30` đã lưu, tài sản N theo thứ tự Stage. Đổi thứ tự
hoặc ô làm slot khác phải xác nhận lại. Xóa dòng làm mất binding của dòng ấy,
không chuyển sang người kế tiếp. Slot trống/không hỗ trợ thì báo lỗi.
Mỗi dòng đất giữ số dòng trong bản nguồn riêng với vị trí hiện tại.
Nguồn có thể có dòng số 21 trở lên; giới hạn 20 áp dụng cho số dòng chọn vào
Stage, không áp dụng cho số thứ tự trong bản nguồn.
Xóa dòng đầu không chuyển bằng chứng của dòng ấy sang dòng kế tiếp; sửa danh sách đất
gỡ vị trí đất cũ và yêu cầu xác nhận lại. Vị trí mới chỉ được lưu khi khớp
dòng/ô và giá trị của bản Stage/sơ đồ được ghi trong cùng lần lưu.

Mỗi hồ sơ giữ tối đa 8 nguồn Word; nguồn thứ 9 bị chặn trước khi thêm dòng
Stage và gợi ý vẫn còn. Nút **Gỡ nguồn Word** bỏ đối chiếu nguồn, giữ dữ liệu
Stage. Thao tác này không đọc file gốc nên dùng được khi nguồn đã hỏng.
Nếu lưu việc gỡ nguồn thất bại thì khôi phục đối chiếu và trạng thái bản nháp
trước thao tác, giữ nguồn hiện trên màn để thử lại. Không khôi phục sang hồ sơ khác.

Binding được xác nhận tạo bản mẫu riêng tại
`docx_sources/<source_id>/templates/<template_sha256>.docx`; context giữ hash
đó. Source và mẫu không bị ghi đè. Xuất đọc dữ liệu đã commit qua catalog Word
tích hợp. Nguồn/mẫu mới được ghi xong ở vị trí tạm rồi mới công bố (cho phép
đọc bằng ID/hash); lỗi giữa chừng không để lại bản đích ghi dở, có thể thử lại.
Mẫu hợp lệ đã có không bị thay. File tạm xuất Word được dọn nếu hủy trước
khi công bố đầu ra; bản gốc còn nguyên. Khi xuất, chỉ thay đúng các span
`w:t`, giữ run/kiểu chữ/bảng/ảnh/section và nguyên
byte của mọi package part khác. Span chồng nhau hoặc qua hyperlink, tracked
change, textbox, field code, tab/ngắt/separator bị từ chối. Đầu/chân trang giữ
nguyên và có cảnh báo phạm vi đọc. Không hứa giống từng pixel khi chưa đối
chiếu bằng Word thật.
Một vị trí trải qua các run (đoạn chữ nhỏ trong Word) có kiểu chữ khác nhau
cũng bị từ chối, kèm lý do trên màn chọn; chưa có quy tắc tự chia định dạng
cho chữ mới. Các run gốc và vị trí chưa chọn vẫn được giữ nguyên.

## Contract, lỗi và phần chưa có bằng chứng

Contract nội bộ bổ sung ở
[`notary-case-drafting.md` §13.17](../../../../contracts/notary-case-drafting.md).
Input vẫn tối đa 8 nguồn, 20 MB/file; DOCX tối đa 100.000 ký tự đọc và tổng
package giải nén 100 MB. Nguồn hỏng không làm mất nguồn khác. Đổi hồ sơ bỏ
response nhập/xuất đến muộn. `word.original_mapping_invalid` yêu cầu kiểm tra
lại; lỗi thư mục/file vẫn dùng lỗi Word hiện hành, file đầu vào giữ nguyên.

Tests dùng DOCX giả lập sinh trong thư mục thử: nhiều người/tài sản, bảng xen
đoạn, gộp/lồng, Unicode tổ hợp/emoji, split-run, ảnh, trùng/mơ hồ, serial ngoài
chuẩn, stale revision, hash/slot đổi, nguồn/mẫu và package không đổi ngoài vị
trí được chọn. Chưa có corpus văn phòng gán nhãn, kiểm trang bằng Word thật,
hoặc bản cài sạch trên máy khác. Tách/gộp tùy ý ứng viên từ nguồn không rõ
ranh giới chưa có thao tác riêng; có thể sửa/bỏ ứng viên và thêm dòng Stage
bằng tay, nhưng không tự tạo binding cho phần thêm tay.

Không tra lịch sử địa chỉ từ nguồn pending; kho
[`administrative-timeline.md`](../administrative-timeline.md) vẫn là nguồn
lịch sử duy nhất. Đợt này chưa nối lịch sử hành chính vào nhập Word.

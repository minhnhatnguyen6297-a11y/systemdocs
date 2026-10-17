# Word — xuất văn bản, placeholder và nguồn DOCX

**Cập nhật:** 16/10/2026. Đọc theo luồng nhập nguồn → kiểm tra/lưu → chọn mẫu → xuất. Tab tự tạo/quản lý mẫu lâu dài vẫn chưa đặc tả.

## 1. Nguyên tắc và khoảng lệch hiện hành

Owner muốn điền được trường nào thì xuất trường đó; không bắt hoàn thành sơ đồ nếu văn bản chỉ cần Stage. Trường hợp lệ chưa có dữ liệu để trống. Token không hỗ trợ, dữ liệu chưa cập nhật và lỗi nguồn/mẫu không phải dữ liệu trống.

Phần dưới giữ rõ giới hạn hiện hành. Đã đồng bộ theo owner 15/10/2026: gate
nhóm (Chủ/Nhận, sơ đồ hai bên) chỉ áp theo **token mẫu thực sự dùng** — nhận
diện theo registry key engine sinh, không theo chuỗi con; catalog backend áp
theo mẫu từng `document_key`, folder mode giữ semantics nhóm thiếu để trống;
gate kỹ thuật (thiếu người/tài sản, giới hạn số lượng) giữ nguyên; slot chưa
giải quyết và người được ủy quyền mẫu cần vẫn làm riêng file đó lỗi.

<a id="docx-import"></a>
## 2. Nhập hợp đồng và dùng lại bản gốc

### 2.1. Công dụng và thao tác

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

### 2.2. Bóc trường, nhóm và Tại sao?

Document Intake đọc đoạn và bảng theo thứ tự XML thật, gồm ô vật lý và bảng
lồng; ô gộp không bị đọc hai lần. Text không bị strip trước khi tạo vị trí.
Mỗi vị trí là `[start,end)` theo ký tự Unicode, không theo byte. Chữ xuống
dòng/ngắt/tab cũng có vị trí nhưng không được thay như chữ bình thường.

Lõi luật chung `tools/regex_workbench/engine/contract_extract.py` sở hữu quy
tắc có phiên bản (identity `contract_word` + `ENGINE_VERSION`); không sao chép
regex sang adapter (Owner NAIA-4 02/10/2026, khẳng định lại 06/10/2026). Từ
cutover 16/10/2026 lõi này là **một đường luật duy nhất** cho văn bản Word:
Document Intake gọi qua adapter
`notary_v2/services/document_intake/adapters/docx.py` (dựng `source_refs`
span/`rule_id`/identity lõi) và Word Upload/tool gọi qua adapter
`upload_lab/extraction_adapter.py`; pipeline profile/zoning cũ đã gỡ cùng
cutover. Lõi nhận input là văn bản của file Word
(adapter đọc file) hoặc đoạn text thô; ngoài trích xuất, phần gợi ý điền mẫu
Word chưa gắn template ở chức năng soạn hồ sơ dùng thẳng các field/span của
gợi ý intake (Owner 06/10/2026). Người được chia theo vùng đương sự; tài sản có
nhãn `Tài sản [thứ] N:` mở một nhóm tài sản riêng; serial đọc nguyên văn
theo nguồn (lệch chuẩn chỉ cảnh báo, giữ raw) và nhãn `Địa chỉ thửa đất:`
điền địa chỉ thửa. Dòng `Loại đất:` mở một
cụm đất riêng. Một GCN có nhiều cụm vẫn là một tài sản. Đây là phạm vi mẫu đã
kiểm tra, chưa phải lời hứa nhận đúng mọi loại hợp đồng.
Nhãn tài sản ở tiêu đề trước vùng tài sản không mở nhóm chứa dữ liệu đương
sự. Dòng đất không có giá trị đọc được tạo cảnh báo thiếu dữ liệu; không
tạo bằng chứng giả và không làm mất người/tài sản hợp lệ của cả nguồn.

Không có ranh giới chắc thì giữ `ambiguous_group`; nhiều giá trị giữ mọi lần
thấy và `normalized_value=null`. Phải chọn/sửa trường mơ hồ trước khi nhận.
Serial là chuỗi nguyên văn tùy nguồn — không ép format, có thể trống,
có thể trùng giữa thửa (Owner 06/10/2026, `entities.md` §2). Trùng giấy
tờ/serial chỉ cảnh báo, không gộp. Khối sổ tiết kiệm/quyền lợi bảo hiểm/xe
chỉ được nhận diện (lõi giữ trong `raw.tai_san_chua_ho_tro`), không bóc dòng;
khi văn bản vẫn còn người/tài sản để lập gợi ý thì gợi ý tài sản mang thêm
cảnh báo `intake.unsupported_asset` để người kiểm tra biết phần chưa hỗ trợ.
Không suy giới tính, vai trò, quan hệ
hoặc sở hữu từ lời hợp đồng. Lời chứng ngoài vùng đương sự giữ nguyên,
không tự thành người mới và không dùng để đối chiếu/đếm lại đương sự
(TASK-5). Người chết là một `person_row` có `ngay_chet`; giấy tờ của họ
(trích lục khai tử...) điền vào `so_giay_to`/`ngay_cap`/`noi_cap`/
`loai_giay_to` cùng format với người sống — không tạo entity riêng.
Sổ tiết kiệm và bảo hiểm **tạm dừng**: nhận diện sự hiện diện và gắn cờ
"loại tài sản chưa hỗ trợ", không bóc dòng (Owner 06/10/2026).
Thiếu trường vẫn cho kiểm tra và bổ sung ở Stage; quy tắc commit MIN-141 giữ
nguyên. Đủ 3 tài sản thì gợi ý tiếp theo vẫn còn, kèm lời báo hết chỗ.

Owner TASK-10.3 (08/10/2026): lỗi gõ/dính chữ không cần chức năng mới.
Phần regex lấy được điền vào các ô tương ứng đang có ở Stage để sửa;
số giấy tờ/nơi cấp là chữ tự do, giữ chữ nguồn kể cả sai chính tả.
Không thêm ô nguyên văn hoặc luật sửa chữ; cảnh báo chỉ khi nhận biết được
trường cần kiểm. Không bỏ giá trị chữ chỉ vì khác mẫu. Nhiều giá trị chưa
chọn, ngày/diện tích không hợp lệ vẫn phải chọn/sửa theo quy tắc trên.
Bằng chứng gốc và vị trí Word không đổi; không dán khối nguồn vào ô khác nghĩa.
Tài sản có bằng chứng địa chỉ hoặc cụm đất vẫn được giữ khi thiếu mọi mã
định danh; nhãn trống không tạo tài sản rỗng. Diện tích âm/không hữu hạn trong
nguồn giữ nguyên chữ và dấu trong bằng chứng, giá trị chuẩn là null và phải sửa
trước khi nhận. Diện tích lấy số đứng trước `m2`/`m²` làm mốc: `1234,5`,
`1.234,5`, `1234.0` đều đọc được; số chỉ có dấu chấm (`1.234`) là mơ hồ —
giữ nguyên văn, `normalized_value=null` + cờ (Owner 06/10/2026).
Bằng chứng mỗi ô đất hiển thị vị trí ký tự trong nguồn.

### 2.3. Nguồn, dữ liệu và đối chiếu

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
phát hiện thiếu hoặc lệch dữ liệu. Đây là cách thao tác đề nghị. Ngày 16/10/2026
đã khôi phục một DB + `docx_sources` file-backed cô lập bằng dữ liệu tổng hợp
(đã kiểm bằng các ca tổng hợp cô lập; bằng chứng sau khi dừng app là ca 3):
`integrity_check` thành công, hồ sơ mở lại với binding đã lưu và xuất bản gốc
thành công. Kết quả này không kiểm cài sạch, máy khác hoặc filesystem ngoài
NTFS, và không thay đổi giới hạn vận hành/retention bên dưới; xem
[Notes của issue #9](../../backlog/spike-word-real-route-acceptance.md#notes).

`case_state_json.docx_import` version 1 chỉ giữ ID/hash nguồn,
`candidate_id→row_id`, danh tính từng dòng đất và vị trí đã duyệt. Nguồn có tên
file an toàn do backend tạo để phân biệt nhiều hợp đồng. Chữ gốc/quan sát ở package backend;
giá trị người dùng sửa ở Stage đã lưu. Context và Stage ghi trong cùng
transaction (một lần ghi trọn vẹn), dùng `base_revision` cũ thì từ chối cả
lần ghi. Create/get/commit trả lại context để mở hồ sơ khác hoặc tải lại không
mất đối chiếu. Nút `Hủy thay đổi` của Stage đã bỏ cùng cơ chế khôi phục riêng:
bỏ nháp khi mở hồ sơ khác không ghi context chưa commit, và mở lại hồ sơ thì
đọc đúng context đã lưu; dirty, cảnh báo rời/đóng và nhánh bỏ nháp giữ nguyên.

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

### 2.4. Contract, lỗi và phần chưa có bằng chứng

Contract nội bộ bổ sung ở
[`notary-case-drafting.md` §13.17](../../../contracts/notary-case-drafting.md).
Input vẫn tối đa 8 nguồn, 20 MB/file; DOCX tối đa 100.000 ký tự đọc và tổng
package giải nén 100 MB. Nguồn hỏng không làm mất nguồn khác. Đổi hồ sơ bỏ
response nhập/xuất đến muộn. `word.original_mapping_invalid` yêu cầu kiểm tra
lại; lỗi thư mục/file vẫn dùng lỗi Word hiện hành, file đầu vào giữ nguyên.

Tests dùng DOCX giả lập sinh trong thư mục thử: nhiều người/tài sản, bảng xen
đoạn, gộp/lồng, Unicode tổ hợp/emoji, split-run, ảnh, trùng/mơ hồ, serial ngoài
chuẩn, stale revision, hash/slot đổi, nguồn/mẫu và package không đổi ngoài vị trí
được chọn.

Evidence #9 (16/10/2026): direct `word_batch_export` API xuất hai mẫu copy
với hồ sơ synthetic; không đi qua renderer command transport hoặc native picker.
Đã kiểm bằng các ca tổng hợp cô lập; bằng chứng sau khi dừng app là ca 3 —
paired DB + `docx_sources` restore cho một binding synthetic và original export
sau khi service mở lại đều thành công. Word COM `Documents.Open` bị timeout;
không tạo PDF/ảnh trang. Xem [Notes của issue #9](../../backlog/spike-word-real-route-acceptance.md#notes).

Chưa có corpus văn phòng gán nhãn, kiểm trang bằng Word thật, hoặc bản cài sạch trên máy khác. Tách/gộp tùy ý ứng viên từ nguồn không rõ
ranh giới chưa có thao tác riêng; có thể sửa/bỏ ứng viên và thêm dòng Stage
bằng tay, nhưng không tự tạo binding cho phần thêm tay.

Không tra lịch sử địa chỉ từ nguồn pending; kho
[`administrative-timeline.md`](../shared/administrative-lookup.md#timeline) vẫn là nguồn
lịch sử duy nhất. Đợt này chưa nối lịch sử hành chính vào nhập Word.

<a id="export"></a>
## 3. Chọn mẫu và xuất văn bản

### 3.1. Flow

```text
Chọn thư mục mẫu + chọn văn bản + thư mục đích
→ kiểm workspace và loại hồ sơ
→ đọc Stage và Diagram đã lưu
→ backend dựng placeholder
→ tạo từng DOCX
→ trả kết quả saved/failed/skipped theo file
```

Đổi thư mục mẫu xoá ngay lựa chọn cũ và khoá Xuất/Chọn trong lúc quét; chỉ
kết quả của lần quét mới nhất được hiển thị — không để response của thư mục
trước đè danh sách thư mục sau.

Dialog có ô **Nơi niêm yết**: nạp giá trị đã lưu của hồ sơ, cho sửa và lưu
qua `notary.workspace_update`. Lệnh cập nhật cả cột hồ sơ và đúng key của
snapshot đã lưu trong một lần ghi; không đổi Stage, tài sản hoặc sơ đồ.
Lưu lỗi giữ nội dung đang nhập; revision cũ phải báo xung đột. Bản nháp metadata
khác trong card Tài sản không bị mất khi lưu riêng Nơi niêm yết.
Nếu ô Nơi niêm yết khác bản đã lưu, dialog yêu cầu lưu trước khi xuất, kể cả
bản nháp đã có từ card Tài sản. Không hiển thị nơi mới rồi xuất theo nơi cũ.

Tra nơi niêm yết theo [tra cứu địa chỉ](../shared/administrative-lookup.md#usage): bấm Tra
trên chính nội dung ô, không chọn tài sản nguồn, không cần ngày. Kết quả chỉ để
copy; không tự lưu hoặc thay giá trị đang nhập (Owner 05/10/2026, TASK-2).

### 3.2. Input và output

Input: `case_id`, danh sách `document_keys` và thư mục đích local đã tồn tại;
optional `template_dir` (thư mục chứa mẫu `.docx` người dùng chọn) và
`create_case_subdir` (ghi vào `<đích>/HS-<case_id>/`). Nhánh mẫu thư mục/catalog
không nhận `base_revision`; nhánh hợp đồng gốc cần revision đã lưu. Output liệt kê từng document, tên file thực, path, trạng thái
và lỗi; breakdown luôn có `succeeded`, `failed`, `skipped`.

#### Nguồn mẫu

Luồng nhập hợp đồng DOCX có thêm **Dùng hợp đồng Word đã nhập** trong dialog
này. Chọn riêng từng lần xuất hiện → dòng đã lưu → slot catalog rồi lưu đối
chiếu trước khi xuất. `original_source_id` chỉ resolve nguồn backend thuộc
hồ sơ, không nhận đường dẫn mẫu tùy ý; batch này cần `base_revision`. Mẫu gốc
và mẫu dẫn xuất đều kiểm hash; đổi thứ tự/ô phải xác nhận lại. Không thay mọi
chuỗi giống nhau. Quy tắc và giới hạn hiện hành tại
[§2. Nhập hợp đồng và dùng lại bản gốc](#docx-import).
[Bản trước đợt gom 15/10/2026 (lịch sử, không phải nguồn hiện hành)](../../archive/specs-before-consolidation-20261015/notary_v2/input/docx-import.md).

Nguồn mẫu thông thường chọn từ thư mục. Catalog cố định còn được backend
giữ để tương thích với các lệnh cũ, không phải lựa chọn trong dialog.
Không `template_dir` → catalog backend cố định (hành vi cũ). Có `template_dir`
→ backend quét file `.docx` ngay trong thư mục (bỏ `~$*` lock file, bỏ
non-DOCX, không vào thư mục con, thứ tự theo tên). `document_key` = basename
gốc; `document_keys` được đối chiếu lại với đúng tập file của thư mục đã cấp
quyền — renderer không gửi được path tùy ý hay thoát thư mục qua traversal.

### 3.3. Quy tắc dữ liệu

| Nội dung | Nguồn |
|---|---|
| Thông tin cá nhân | Stage |
| Quan hệ | Diagram |
| Kết quả/phân số | Engine result Python |
| Tài sản | Stage assets + vị trí Diagram |
| Mẫu và placeholder | Thư mục người dùng chọn hoặc catalog backend |

Không lấy dữ liệu chưa commit hoặc kết quả frontend tự tính. Placeholder chưa
giải quyết phải làm file đó thất bại, không âm thầm để sót trong văn bản.

Gate nhóm phân loại theo **token mẫu thực sự dùng** (owner 15/10/2026):
`no_landowner`/`no_deceased_landowner`/`no_receiver` chỉ áp khi mẫu dùng
token của đúng nhóm đó — catalog backend áp theo mẫu của từng
`document_key`; `no_diagram` của hai bên chỉ áp khi mẫu dùng ghế
`Bên A`/`Bên B`. Nhận diện theo đúng registry key engine sinh (nhóm
`Chủ đất sống`, `Chủ đất chết`, `Người nhận`, ghế hai bên) sau chuẩn hoá
không dấu — không đoán theo chuỗi con, nên token metadata/ủy quyền kiểu
`[Người nhận ủy quyền]` không kéo nhầm gate Người nhận.

Folder mode giữ hành vi hiện hành: nhóm thiếu dữ liệu render rỗng — không
thêm gate mới. Gate kỹ thuật luôn áp: thiếu người/tài sản đã lưu, giới hạn
số lượng, mẫu/đường dẫn không hợp lệ và token không hỗ trợ. Tại sao: owner
muốn điền dần — xuất được file không phải xác nhận hồ sơ đã hoàn thiện
pháp lý.

#### Placeholder và context

- Placeholder mới dùng `[Tên danh sách N - Trường]`; alias cũ chỉ để mở
  template cũ, không làm chuẩn đặt tên mới.
- **`[Người N - *]` lấy đúng thứ tự danh sách Stage** (NAIA-8), gồm cả người
  chưa có node — đảo/xóa node Diagram không đổi số Người. Vai trò lấy từ dữ
  liệu nghiệp vụ đã lưu, không suy từ vị trí node.
- Các alias viết liền MIN-141 (`[tenN]`, `[ngaysinhN]`, …) vẫn giữ slot legacy;
  field đọc snapshot, chỉ fallback master khi key thiếu. Null/rỗng đã lưu
  giữ nguyên; giấy chứng tử và nơi cấp đã xác nhận không bị suy lại từ địa chỉ.
  Metadata hồ sơ và cụm đất 1..20 cũng ưu tiên snapshot.
- Context thừa kế phân loại thành `Người`, `Chủ đất sống`, `Chủ đất chết`,
  `Người nhận`, `Người không nhận`; `Người từ chối` chỉ có khi có bằng chứng
  pháp lý xác nhận riêng.
- Context hai bên (`case_type:two_party`, NAIA-8): `[Bên A N - *]`/`[Bên B
  N - *]` theo slot `p1..p15`/`p16..p30` (ô trống render rỗng, không dồn);
  `[Bên A - Họ tên]`, `[Bên B - Họ tên]`, `[Tên bên A]`, `[Tên bên B]` =
  danh sách họ tên từng bên; placeholder riêng thừa kế render rỗng.
  Readiness hai bên chỉ kiểm tra kỹ thuật (`word.no_people`,
  `word.no_assets`, `word.too_many_*`) và `word.no_diagram` khi mẫu thực
  sự dùng ghế `Bên A`/`Bên B` — không áp điều kiện chủ đất/người nhận
  của thừa kế, không thêm kiểm định pháp lý.
- Ngày Người render theo đúng độ đầy đủ đã lưu: `YYYY` in nguyên năm
  (`2010`), `YYYY-MM-DD` in `dd/mm/yyyy`; token `Năm sinh`/`Năm chết` chỉ
  in năm. Token câu/dòng dựng sẵn không in ISO thô. Năm riêng đã lưu không
  bị đệm thành `01/01`; hồ sơ cũ thiếu key ngày dùng master và ghi nhận là
  ngày đầy đủ.
- **Người được ủy quyền** lấy từ vai trò đã lưu trong `participants.vai_tro`,
  không yêu cầu node Diagram (đại diện hợp lệ có thể không nằm trên sơ đồ;
  người bị ẩn/xóa trên Diagram không tính). Mẫu khai báo nhu cầu qua hậu tố
  số của token — `[Dòng người được ủy quyền N]`,
  `[Người được ủy quyền N - <trường>]`, `[<Trường> người được ủy quyền N]`,
  `[Người được ủy quyền inline N]` đều là slot `N`; token không số là slot 1.
  Hồ sơ thiếu đại diện cho slot mẫu đòi → file đó lỗi
  `word.missing_authorized_person`, không render rỗng rồi xuất.
- **Diện tích đất theo vị trí** (quyết định Owner 02/10/2026, NAIA-8 comment
  `01a0fd42-5cbe-7076-976e-ef907c8ca086`): `[ONT]`/`[CLN]`/`[NTS]`/`[LUC]`
  (và hậu tố ` N` theo tài sản) là diện tích của dòng loại đất ở VỊ TRÍ
  1/2/3/4 — không tra theo mã loại đất thật. Nhãn loại đất trong bản migrate
  mới dùng `[Loại đất tài sản N.M]` (loại đất thật của dòng) hoặc
  `[Tài sản N - Loại đất]`/`[Loại đất tài sản N]` (loại đất cấp tài sản);
  chữ ONT/CLN/NTS/LUC in cứng trong mẫu cũ được migration đổi thành
  placeholder đó thay vì giữ nhãn cứng sai dữ liệu (chi tiết §10 của catalog
  `placeholder_mapping.md`).
- Tầng 1 lấy field trực tiếp. Tầng 2 dựng trọn câu/dòng và trả rỗng toàn bộ khi
  không áp dụng, tránh để lại dấu câu rác. Chưa có block `if/for` cho template.
- Resolver không được đoán nghiệp vụ từ tên placeholder. Catalog hiện hành nằm
  cạnh template tại `notary_v2/word_templates/placeholder_mapping.md`.

### 3.4. File và an toàn

- Tên: `<filename_stem>_HS-<case_id>[_n].docx`.
- Không ghi đè file có sẵn; trùng tên tăng `_2`, `_3`, ...
- Output phải nằm trong thư mục người dùng chọn; cấm UNC/path traversal theo
  contract hiện hành.
- Cancel giữ file đã lưu, đánh dấu file chưa bắt đầu là `skipped`.
- File đang ghi dở phải được dọn khi có thể.

### 3.5. Lỗi

- Không chọn văn bản, key lạ/lặp, thiếu template, placeholder còn sót, file bị
  khóa hoặc path sai đều có code riêng.
- Mẫu có mặt nhưng không mở/parse được: danh sách sẵn sàng báo đúng data-code
  per-file mà lượt xuất sẽ trả (`word.render_failed`, `file_locked`,
  `file_not_found`) — không nuốt lỗi thành gate dữ liệu cũ.
- `word.missing_authorized_person`: mẫu đòi slot đại diện N lớn hơn số vai
  trò `Người được ủy quyền` đã lưu — file đó thất bại, không tạo DOCX.
- Một file lỗi không bắt buộc làm mất file khác đã tạo.
- Tất cả file lỗi: job `word_batch_failed`; trộn kết quả: `partial`.

<a id="placeholders"></a>
## 4. Cách viết placeholder

### 4.1. Quy tắc placeholder

Placeholder mới dùng dạng:

```text
[Tên danh sách N - Trường]
```

Ví dụ:

```text
[Người 3 - Họ tên]
[Người 3 - Quan hệ]
[Người nhận 1 - Họ tên]
[Chủ đất chết 1 - Ngày chết]
```

- `[Người 3 - ...]`: `3` là thứ tự dòng Stage đã lưu, kể cả chưa có node.
  Hai bên dùng cùng thứ tự Stage cho Người; `[Bên A N - ...]`/`[Bên B N - ...]`
  theo ghế cố định, ghế trống giữ nguyên vị trí.
- `[Người nhận 1 - ...]`: `1` là thứ tự của người nhận trong danh sách.
- Trường dùng chung: họ tên, xưng hô, giới tính, ngày sinh, ngày chết,
  giấy tờ, ngày/nơi cấp, địa chỉ, quan hệ, vai trò, tỷ lệ.
- Tên chuẩn [`entities.md` §9.1](../../../contracts/entities.md) (viết liền,
  không dấu, không `_` — tên trường/khóa canonical) cũng được
  thay: `[noiniemyet]`, `[nguoinhanuyquyen]`, `[noidungviec]`,
  `[ngaylaphoso]`, `[ghichu]`, `[documenttype]` cho hồ sơ; `[ten1]`,
  `[gioitinh1]`, `[ngaysinh1]`, `[ngaychet1]`, `[sogiayto1]`,
  `[ngaycap1]`, `[diachi1]`, `[loaigiayto1]`, `[noicap1]`,
  `[loaicutru1]`/`[loaidiachi1]` cho người số `N` (giá trị trùng alias
  tiếng Việt tương ứng). Quy ước viết liền đó đặt tên trường/khóa;
  dạng nhóm dễ đọc ở trên mới là chuẩn viết cho mẫu mới.
- Alias cũ được giữ để mở template cũ nhưng không dùng làm mẫu mới.

### 4.2. Tầng placeholder

#### Tầng 1 — trường trực tiếp

Lấy một giá trị từ snapshot:

```text
[Người 3 - Họ tên]
[Tài sản - Địa chỉ]
[Chủ đất sống 1 - Số giấy tờ]
```

#### Tầng 2 — câu/dòng dựng sẵn

Một placeholder tầng 2 bao trọn câu hoặc dòng có dấu câu. Nếu điều kiện không
đúng, toàn bộ placeholder rỗng.

Ví dụ:

```text
[Dòng người không nhận 3]
[Dòng người từ chối 3]
[Dòng chủ đất sống tặng cho 1]
[Dòng mô tả quan hệ người 5]
```

`[Dòng người không nhận N]` lấy từ quyết định trên Diagram. `[Dòng người từ
chối N]` chỉ có giá trị khi hồ sơ có dữ liệu từ chối pháp lý được xác nhận; nó
không được resolver tự điền từ danh sách người không nhận.

Không để user tự ghép nhiều placeholder điều kiện với dấu câu rời nếu có thể
dùng một dòng tầng 2.

#### Tầng 3

Chưa triển khai. Chỉ thêm khi cần đối chiếu nhiều đoạn trong cùng văn bản và
được chốt bằng một case nghiệp vụ cụ thể.

## 5. Bộ tạo file và chuyển mẫu

Python giữ catalog, mapping, tên file và dựng câu; giao diện chỉ chọn/hiển thị. Phải xử lý placeholder trong đoạn, bảng, đầu/chân trang và khi Word chia chữ thành nhiều run. Không suy nghiệp vụ từ tên token. Mô tả nhiều tài sản đánh số 1, 2…; cụm đất trong tài sản N đánh số N.1, N.2…

Chuyển mẫu đọc bản sao DOCX/DOC, ghi thư mục mới và báo cáo từng file; không sửa nguồn. DOC dùng Word COM, giữ kiểm danh tính file và hash. Không tự tạo giá trị cho token lạ. Đã chốt bỏ token Số công chứng, Giá chuyển nhượng, Người ủy quyền2; giữ nhãn cần điền tay. Mã cố định biểu mẫu thuế chỉ miễn kiểm trên đúng mẫu đã xác minh.

Kiểm chứng cũ không thay nghiệm thu mới: từng có batch 22 mẫu; chưa kiểm trực quan mọi trang. Luồng DOCX có kiểm mô phỏng và Electron. Evidence #9 ngày 16/10/2026 xác nhận direct service batch và paired DB+`docx_sources` backup/restore với dữ liệu synthetic (đã kiểm bằng các ca tổng hợp cô lập; bằng chứng sau khi dừng app là ca 3), nhưng native picker/renderer command transport chưa được chứng minh; Word COM timeout trước khi xuất trang. Chưa có corpus văn phòng gán nhãn đầy đủ hoặc bản cài sạch trên máy khác. Không tự tuyên bố giữ từng pixel.

## 6. Tab Word dự kiến

Nhập văn bản → đề xuất placeholder từ regex → tải về chỉnh → nhập lại xác nhận lưu mẫu. Chưa chốt trải nghiệm, danh mục template và tiêu chí phát hành; không biến mô tả này thành quyền tự triển khai.

**DEFERRED — owner 17/10/2026:** “chức năng này tôi sẽ tự làm sau, cần spec kỹ. Chuyển issue khác”. Tab tạo/lưu mẫu cần spec chi tiết trước implementation tương lai; chưa giao đặc tả hay triển khai lúc này. Nguồn vào/giữ bố cục, storage/catalog và tiêu chí nghiệm thu chưa chốt; không tự chọn hoặc hỏi tiếp trong lượt này. Không áp việc hoãn lên Xuất Word hoặc original-DOCX intake hiện có. [Decision](../../decisions/decision-owner-word-authoring-deferred-20261017.md).

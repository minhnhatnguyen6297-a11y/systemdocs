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
thư mục đích. Nút Tải JSON chỉ tải kết quả về máy; không gửi ra ngoài.

Giữ dialog Nhập file hiện có và đúng hai tab Upload Lab. `.doc`, ảnh/OCR,
Excel không dùng bản đồ vị trí DOCX trong đợt này. Mỗi trường giữ chữ gốc;
sửa là giá trị người dùng kiểm tra, không sửa bằng chứng ban đầu.
Cụm đất được sửa theo từng dòng loại đất/diện tích/thời hạn, không buộc người
dùng nhập mã JSON. Cả một dòng lẫn nhiều dòng đều giữ được.

## Bóc trường, nhóm và Tại sao?

Document Intake đọc đoạn và bảng theo thứ tự XML thật, gồm ô vật lý và bảng
lồng; ô gộp không bị đọc hai lần. Text không bị strip trước khi tạo vị trí.
Mỗi vị trí là `[start,end)` theo ký tự Unicode, không theo byte. Chữ xuống
dòng/ngắt/tab cũng có vị trí nhưng không được thay như chữ bình thường.

Lõi regex chung `tools/regex_workbench/engine` sở hữu quy tắc có phiên bản;
không sao chép regex sang adapter. Profile `transfer` 1.1.0 chia người trong
vùng đương sự và tài sản có nhãn `Tài sản [thứ] N:`. Dòng `Loại đất:` mở một
cụm đất riêng. Một GCN có nhiều cụm vẫn là một tài sản. Đây là phạm vi mẫu đã
kiểm tra, chưa phải lời hứa nhận đúng mọi loại hợp đồng.

Không có ranh giới chắc thì giữ `ambiguous_group`; nhiều giá trị giữ mọi lần
thấy và `normalized_value=null`. Phải chọn/sửa trường mơ hồ trước khi nhận.
Serial ngoài chuẩn không được biến thành số giả. Trùng giấy tờ/serial chỉ
cảnh báo, không gộp. Không suy giới tính, vai trò, quan hệ hoặc sở hữu từ lời
hợp đồng. Lời chứng ngoài vùng đương sự giữ nguyên, không tự thành người mới.
Thiếu trường vẫn cho kiểm tra và bổ sung ở Stage; quy tắc commit MIN-141 giữ
nguyên. Đủ 3 tài sản thì gợi ý tiếp theo vẫn còn, kèm lời báo hết chỗ.

## Nguồn, dữ liệu và đối chiếu

Sidecar lưu byte Word gốc và `extraction.json` ở
`<engine-data/notary_v2>/docx_sources/<source_id>/`. `source_id` do backend
tạo, không phải đường dẫn do renderer chọn. `sha256` là dấu kiểm nội dung;
nguồn được kiểm lại trước mỗi lần lưu đối chiếu/xuất. Không ghi hồ sơ thật
vào Git, log rộng hoặc localStorage.

`case_state_json.docx_import` version 1 chỉ giữ ID/hash nguồn,
`candidate_id→row_id`, và vị trí đã duyệt. Chữ gốc/quan sát ở package backend;
giá trị người dùng sửa ở Stage đã lưu. Context và Stage ghi trong cùng
transaction (một lần ghi trọn vẹn), dùng `base_revision` cũ thì từ chối cả
lần ghi. Create/get/commit trả lại context để mở hồ sơ khác hoặc tải lại không
mất đối chiếu. Hủy thay đổi khôi phục cả context đã lưu.

Đối chiếu Word là **một lần xuất hiện → ID dòng + trường + slot catalog**,
không phải “thay mọi chuỗi giống nhau”. Màn Word hiện chữ gốc, tên/ID dòng,
slot và giá trị sẽ xuất; checkbox ban đầu không chọn. Người N theo Stage đã
lưu, Bên A/B theo ô `p1..p30` đã lưu, tài sản N theo thứ tự Stage. Đổi thứ tự
hoặc ô làm slot khác phải xác nhận lại. Xóa dòng làm mất binding của dòng ấy,
không chuyển sang người kế tiếp. Slot trống/không hỗ trợ thì báo lỗi.

Binding được xác nhận tạo bản mẫu riêng tại
`docx_sources/<source_id>/templates/<template_sha256>.docx`; context giữ hash
đó. Source và mẫu không bị ghi đè. Xuất đọc dữ liệu đã commit qua catalog Word
tích hợp, thay đúng các span `w:t`, giữ run/kiểu chữ/bảng/ảnh/section và nguyên
byte của mọi package part khác. Span chồng nhau hoặc qua hyperlink, tracked
change, textbox, field code, tab/ngắt/separator bị từ chối. Đầu/chân trang giữ
nguyên và có cảnh báo phạm vi đọc. Không hứa giống từng pixel khi chưa đối
chiếu bằng Word thật.

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

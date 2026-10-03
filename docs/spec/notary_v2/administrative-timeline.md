# Lịch sử đơn vị hành chính — NAIA-9

**Trạng thái:** Active cho kho và CLI cục bộ · **Nguồn quyết định:** Owner trong
chat 03–04/10/2026, ghi tại [quyết định NAIA-9](../../../.agent/tasks/NAIA-9/decisions.md).
Tra cứu trên giao diện, nhập DOCX và tự điền nơi niêm yết vẫn chưa triển khai.

## Công dụng và Tại sao?

Owner chọn [Bando](https://sapnhap.bando.com.vn/) làm nguồn tên xã/tỉnh hiện hành
và mô tả lần chuyển đổi gần nhất. Owner sẽ cung cấp lịch sử cũ hơn sau; đợt này
không tìm hoặc đoán thêm nghị quyết. Kho lưu được cả xã, huyện, tỉnh, nhiều lần
đổi tên, sáp nhập, chia tách, chuyển nơi quản lý hoặc bỏ đơn vị.

Tên giống nhau chưa chứng minh cùng một nơi; mã có thể được dùng lại. Mỗi đơn
vị có `id` nội bộ ổn định; tên/mã/nơi quản lý là các bản ghi riêng theo thời gian.
Đổi tên A→B→C→D có thể vẫn là **một** đơn vị. Sáp nhập A+B→C có nhiều đầu vào;
C→D+E có nhiều đầu ra. Lịch sử không bắt buộc chỉ có một đường.

Ngày tải website không phải ngày có hiệu lực. Bando có cả cập nhật 2026; không
gán chung 01/07/2025. Ngày thiếu nguồn giữ `null`, trạng thái `pending` (chờ xác
nhận). Dòng nói “một phần” không được biến thành nhập toàn bộ.

## Lưu ở đâu và cấu trúc

[Ledger JSON](../../../notary_v2/data/administrative_units/ledger.json) là nguồn
dữ liệu chính; [schema](../../../contracts/administrative-timeline/ledger.schema.json)
là mẫu máy kiểm tra, không phải kho thứ hai. Đây là schema kho cục bộ NAIA-9,
chưa publish thành contract tích hợp giữa module.

| Nhóm | Ý nghĩa |
|---|---|
| `units` | ID riêng, cấp `commune`/`district`/`province` (xã/huyện/tỉnh) |
| `names`, `codes`, `parents` | Tên/mã/nơi quản lý từng giai đoạn, liên kết sự kiện khi có |
| `events` | Nhiều tham chiếu `from`/`to`; ngày hiệu lực, khoảng ngày tùy chọn, trạng thái và ghi chú lãnh thổ |
| `mentions` | Chuỗi nơi cũ chưa rõ danh tính; mỗi dòng nguồn có tham chiếu riêng |
| `observations` | Nguyên văn Bando và toàn bộ bảng chi tiết; phân biệt “giữ nguyên” |
| `sources` | URL, cách tải, ngày/giờ lấy, SHA-256 (dấu kiểm tra nội dung), snapshot và nguồn dòng |

`snapshots/<sha256>.raw` giữ **nguyên byte** của catalog và 34 bảng. Không ghi đè
snapshot. `dataset_version` dựa trên hash toàn bộ lần nhập; `revision` tăng mỗi
lần ghi. Snapshot cũ còn nguyên khi refresh. Lần tải scratch chỉ chắc đến ngày
nên lưu `2026-10-04`; tải trực tiếp mới lưu thời điểm có múi giờ.

ID Bando ban đầu được tạo xác định từ `malk`, không từ tên hay `ma`. `ma` là mã
hiện tại dạng chuỗi giữ số 0 đầu; `magoc` là mã tỉnh hiện tại; `malk` là khóa đối
tượng bản đồ hiện tại. Chúng **không chứng minh cùng danh tính qua mọi thời kỳ**.
Refresh giữ ID của cùng khóa nguồn hiện tại để nối các lần quan sát. Mã tái
dùng với khóa nguồn khác tạo ID riêng. Curator (người phụ trách dữ liệu) xác
nhận danh tính lịch sử bằng nguồn, không gộp theo tên/mã. Nếu nguồn tái dùng cả
khóa bản đồ, phải đối chiếu và migration có kiểm tra, không coi đó là bằng chứng
lịch sử tự động.

`observed` nghĩa là website đang nêu giá trị đó, không hứa đúng cho ngày quá khứ.
`confirmed` là bản ghi lịch sử có nguồn và ngày được curator xác nhận. Khoảng
ngày dùng `[valid_from, valid_to)`: gồm ngày đầu, không gồm ngày cuối; ngày cuối
`null` của bản ghi confirmed nghĩa là còn tiếp tục.

## Nguồn Bando và giới hạn

Đường đọc công khai: `POST https://sapnhap.bando.com.vn/p.co_dvhc`, form `ma=0`;
`POST /p.co_bangbieu`, form `ma=<malk tỉnh>`. Bảng trả đối tượng tỉnh, `.synt.`,
rồi mảng xã. Đây là đường website đang dùng, chưa có cam kết API/version ổn định.
Chỉ tải catalog/bảng đầy đủ; không gửi hồ sơ, địa chỉ khách hàng hay yêu cầu tra
tên ra ngoài. Chưa nối CLI này vào runtime ứng dụng.

Snapshot 04/10/2026: **3.355 đơn vị: 34 tỉnh, 3.321 xã, 0 huyện**. Tên/mã/tỉnh
cha giữ đúng catalog; bảng kiểm đối chiếu từng dòng. 136 dòng “giữ nguyên” là
quan sát, không tạo tên cũ giả. 3.219 mô tả khác giữ nguyên trong mention/sự
kiện chờ; 161 dòng nhắc phần lãnh thổ. Không tách văn xuôi thành đơn vị lịch sử
đã xác nhận: `candidate_names` đang trống; report `unparsed_rows=3219` nói rõ
phần chưa phân tích. Chú thích huyện trong ngoặc giữ nguyên. `details` giữ cả
`cancu`, `link` và mọi trường nguồn khác.

Ví dụ Phường Duy Hà, mã `13336`: nguồn nói Duy Minh, Duy Hải và một phần Hoàng
Đông. Kho giữ đủ câu; chưa biết ID/mã/tỉnh/huyện cũ và ngày hiệu lực của đơn vị
nguồn. Không biến thành sáp nhập toàn bộ đã xác nhận. Huyện được schema hỗ trợ
để Owner thêm sau dù Bando không có danh mục huyện.

## CLI và cách Owner bổ sung lịch sử

Chạy từ root với Python; [helper](../../../notary_v2/administrative_timeline.py)
chỉ dùng thư viện chuẩn, không đổi database văn phòng, Word hay dữ liệu hồ sơ.

```powershell
python -m notary_v2.administrative_timeline validate
python -m notary_v2.administrative_timeline refresh-bando
python -m notary_v2.administrative_timeline import-bando --catalog .agent/scratch/multica-address-research/bando-public-current.json --tables .agent/scratch/multica-address-research/bando-public-tables --retrieved-at 2026-10-04
python -m notary_v2.administrative_timeline update .agent/scratch/owner-history.json
python -m notary_v2.administrative_timeline query owner:demo --as-on 2007-01-01
```

`refresh-bando` tải đủ trước khi ghi. Sai/thiếu bảng/hỏng hash bị từ chối; ledger
cũ còn nguyên. Nội dung giống nhau không tăng revision hoặc viết lại dữ liệu.
Nội dung mới thêm quan sát/tên/mã/sự kiện chờ, **không xóa lịch sử thủ công**.
Có khóa ghi để hai CLI không ghi đồng thời. Nếu sau sự cố còn `.write.lock`,
kiểm tra không có tiến trình ghi rồi mới xóa khóa.

Patch JSON gồm `base_revision` bằng revision đang có và `upsert` chứa các nhóm
cần thêm/sửa. Mỗi record ghi đầy đủ theo schema. ID cũ cập nhật record cùng ID;
ID mới thêm record; không có xóa. Nguồn và bằng chứng Bando bất biến. Muốn xác
nhận lịch sử thì thêm record curator, không sửa câu nguồn. Mention cho phép
cập nhật riêng `resolved_unit_id`/`status`; trường nguồn khác giữ nguyên. Sự kiện
Bando vẫn là bằng chứng chờ; thêm sự kiện confirmed tham chiếu `unit` và nguồn
ngày. Nhờ vậy lời website tách khỏi kết luận của curator.

Mention Bando hiện giữ cả câu, có thể chứa nhiều xã. Chỉ gán `resolved_unit_id`
khi đã xác minh mention tương ứng **một** đơn vị. Với câu A+B, Owner tạo các
unit và sự kiện curator có nhiều `from`/`to` cùng nguồn; giữ nguyên mention
tổng hợp làm bằng chứng, không resolve cả câu thành một ID.

Ví dụ **giả lập** A→B trên cùng ID, không phải lịch sử Việt Nam. Chỉ chạy trong
bản sao thử; thay `base_revision` bằng revision bản sao. Khi cập nhật kho chính,
thay nguồn/ngày bằng nguồn thật:

```json
{
  "base_revision": 1,
  "upsert": {
    "sources": [{"id":"owner:demo-source","provider":"Owner synthetic demo","url":"urn:demo:not-history","protocol":"manual","request_body":null,"retrieved_at":"2026-10-04","sha256":null,"snapshot":null,"description":"Ví dụ giả lập; không phải lịch sử"}],
    "units": [{"id":"owner:demo","level":"district","source_key":null,"evidence":[{"source_id":"owner:demo-source","row_key":"demo"}]}],
    "names": [
      {"id":"owner:demo:A","unit_id":"owner:demo","value":"A","valid_from":"2000-01-01","valid_to":"2005-01-01","status":"confirmed","event_id":null,"evidence":[{"source_id":"owner:demo-source","row_key":"demo"}]},
      {"id":"owner:demo:B","unit_id":"owner:demo","value":"B","valid_from":"2005-01-01","valid_to":null,"status":"confirmed","event_id":"owner:demo:ab","evidence":[{"source_id":"owner:demo-source","row_key":"demo"}]}
    ],
    "events": [{"id":"owner:demo:ab","type":"rename","from":[{"kind":"unit","id":"owner:demo"}],"to":[{"kind":"unit","id":"owner:demo"}],"effective_on":"2005-01-01","valid_from":null,"valid_to":null,"status":"confirmed","territory":"whole","notes":"Ví dụ giả lập A→B","evidence":[{"source_id":"owner:demo-source","row_key":"demo"}]}]
  }
}
```

Thêm B→C→D: cập nhật ngày cuối tên B, thêm tên C/D và sự kiện rename trên cùng
ID. Thêm A+B→C: tạo các ID riêng có bằng chứng danh tính, dùng `merge` với hai
`from` và một `to`. Chia C→D+E dùng `split` nhiều `to`; giữ `territory=partial`
và ghi chú nếu chỉ chuyển một phần. Không biến mỗi tên cũ trong câu thành ID
verified. Chưa đủ danh tính/ngày thì dùng mention, ngày `null`, trạng thái
`pending`; curator bổ sung có nguồn sau.

Đích C của merge có thể là đơn vị đã tồn tại rồi nhận thêm lãnh thổ. Việc C
xuất hiện ở `to` không tự chứng minh ngày thành lập; muốn khẳng định thành lập
cần nguồn riêng và cấu trúc assertion được duyệt sau. Hiện kho không tự suy
ngày sinh của đơn vị từ sự kiện sáp nhập.

Query trả `chronological_events` (confirmed theo ngày) riêng với `pending_evidence`
(bằng chứng chưa chắc). Chỉ tên confirmed có giai đoạn bao phủ ngày hỏi mới vào
`confirmed_name_at_date`; thiếu lịch sử trả `insufficient_confirmed_history`,
không suy từ tên hiện hành. Quan sát hiện tại ở `current_source_observations`.
Chỉ quan hệ confirmed nối lịch sử giữa các ID. Mention đã xác nhận danh tính
giúp tìm bằng chứng pending liên quan; quan hệ đó vẫn pending và không đưa
lịch sử của nơi bên kia vào kết quả confirmed.

## Kiểm tra và cách phát triển sau này

Đã triển khai: schema `1.0`; validator chặn ID trùng, nguồn/tham chiếu thiếu,
ngày sai/đảo, khoảng confirmed chồng nhau, mã tái dùng chồng thời gian, cha sai
cấp/quay vòng, confirmed thiếu ngày/danh tính, rename đổi ID, merge/split sai
số đầu vào/ra, chuỗi quay vòng/ngược ngày, dùng đơn vị sau khi bỏ/tiêu thụ toàn
bộ; quan hệ con không được kéo dài quá ngày kết thúc của cha. Hai sự kiện tiêu
thụ toàn bộ xung đột, hoặc đổi tên và bỏ đơn vị cùng ngày, bị từ chối. Ngày
phải đúng `YYYY-MM-DD`. Revision cũ bị từ chối. Ledger và raw snapshot đều ghi
file tạm rồi thay một lần; lỗi trước đó không để file đích bị ghi nửa chừng.

[Tests](../../../notary_v2/tests/test_administrative_timeline.py) dùng ví dụ giả
lập có nhãn: chuỗi rename, merge/split, ba cấp, mã tái dùng, cùng tên khác nơi,
ngày chờ, nguồn hỏng, refresh/giữ lịch sử, toàn bộ snapshot thật. Chạy:
`python -m pytest notary_v2/tests/test_administrative_timeline.py -q`.

Hướng mở rộng **chưa triển khai**: CLI hiện validate và quét toàn ledger theo
lần chạy, phù hợp công cụ local/batch. Khi tích hợp UI, nạp và kiểm một lần rồi
dựng index (bảng giúp tìm nhanh) theo ID/tên/tỉnh/ngày và đồ thị sự kiện. Truy
merge/split theo ID, không theo tên; không gọi CLI/quét ledger hoặc tải web mỗi
lần gõ địa chỉ. Index/cache dựng lại từ ledger được và không là nguồn chính.

Chỉ chuyển database khi có nhu cầu thực và quyết định owner/contract; hiện
chưa cần dịch vụ hoặc DB mới. Đổi schema phải tăng version, giữ bản trước,
viết migration rõ ràng; kiểm số record, ID, chuỗi lịch sử, trạng thái, ngày và
hash nguồn trước/sau. Không âm thầm nhận version không hỗ trợ.

## Nguồn quyết định và phần còn thiếu

Owner 03/10: nơi niêm yết theo `ngay_lap_ho_so`; ngày giấy nguồn giúp đọc địa
chỉ cũ/mới, nơi cấp khai tử riêng. Owner 04/10: Bando là nguồn tên hiện hành,
lấy bước gần nhất trước, Owner thêm A→B→C→D sau; hỗ trợ huyện/sáp nhập/chia tách;
ghi hướng mở rộng để agent sau tiếp tục đúng. Kho chuẩn bị dữ liệu, chưa thay
quy tắc địa chỉ hồ sơ. API không có ngày hiệu lực, ID lịch sử hay parent cũ;
các giới hạn đó còn thiếu thật, không được che bằng ngày tải.

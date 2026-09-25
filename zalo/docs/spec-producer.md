# Producer spec — module Zalo intake (phía thu nhận)

**Producer SOT.** Nội dung chuẩn tắc trong file này được chuyển nguyên văn từ
`notary_v2/docs/platform/zalo-document-inbox/spec.md` §2 (CAP-01..16) tại
MIN-103; file đó giờ chỉ trỏ về đây cho phần producer. Ranh giới trao đổi với
máy chính (gói file, feed pending, ACK, yêu cầu OCR lại, status) do contract
`contracts/zalo-intake/` trong monorepo quy định — bản vendored read-only ở
`schemas/` của repo này. Khi spec này và contract mâu thuẫn về **dây truyền**,
contract đã duyệt thắng; về **hành vi nội bộ module**, file này là SOT.

Phần consumer (parse/review/apply trên máy chính) vẫn thuộc spec
`zalo-document-inbox` của notary_v2 — module không sở hữu phần đó.

## 1. Vai trò của module

Module nhận sự kiện Zalo, giữ ảnh tạm, gọi Qwen OCR và làm các bước xử lý cần
byte ảnh (xoay/cắt/đọc lại vùng) để OCR lại. Nó bàn giao **raw OCR, trạng
thái và dấu vết nguồn trong gói file/folder có version** — không bàn giao
person/property/group đã bóc, không có `results.json` từ bot, không có byte
ảnh/thumbnail/base64/URL/path ảnh trong gói. Parse/ghép/nhóm hồ sơ chạy ở
Document Intake của máy chính sau Sync.

Module có vòng đời riêng, chạy được kể cả khi app công chứng tắt. Giai đoạn
đầu chạy trong repo local độc lập (`D:\zalo-intake`); triển khai Windows
server là bước sau.

## 2. Yêu cầu producer (CAP-01..16)

Bảng dưới là nguyên văn normative từ spec v2 §2. Cột "Chủ đề" thêm vào để tra
nhanh, không thay đổi nội dung yêu cầu.

| Mã | Chủ đề | Yêu cầu giai đoạn đầu |
|---|---|---|
| CAP-01 | Listener / process | Một dịch vụ sở hữu listener của một tài khoản văn phòng; chạy bằng bộ khởi động local độc lập và khởi động lại khi lỗi; cấu hình tự chạy Windows boot thuộc triển khai server sau, không cần app công chứng hay phiên Remote Desktop. Chặn hai listener cùng tài khoản. |
| CAP-02 | Phiên & chính sách nguồn | Phiên đăng nhập và cấu hình nguồn ở server. Máy chính tắt hoặc mạng tới máy chính lỗi không xóa phiên Zalo hay bị hiểu thành logout. Chỉ xác nhận từ nguồn mới yêu cầu đăng nhập lại. |
| CAP-03 | Journal / captured_at | Khi bot nhận sự kiện, cấp captured_at và ghi nhật ký bền vững trước khi gọi OCR hoặc truyền gói. Mỗi đính kèm đã biết có ID, thứ tự và trạng thái riêng; lỗi một ảnh không làm mất các ảnh khác. |
| CAP-04 | Media tải tạm | Ảnh thuộc nguồn đã bật được tải và giữ tạm ở server để gọi Qwen API. File dở không được coi là bản gốc đã lưu; ghi size/hash, lỗi tải và lần thử. Không tạo bản sao ảnh tại máy chính. |
| CAP-05 | Qwen OCR ownership | Module luôn đưa ảnh hỗ trợ đã tải thành công qua Qwen API OCR. Không xây hoặc chạy OCR engine riêng. Thử xoay/cắt/đọc lại vùng ảnh nếu cần byte ảnh tại module; giữ **mọi biến thể text OCR và dấu vết từng lượt**, đánh dấu transcript mặc định theo tiêu chí kỹ thuật. Khi đường Qwen được duyệt trả vị trí dòng chữ, giữ vị trí đó theo từng lượt OCR cùng kích thước khung tọa độ và dấu vết ánh xạ xoay/cắt/đổi kích thước; không ép thành chuỗi chữ phẳng rồi làm mất bố cục. Nếu thiếu hoặc không kiểm chứng được khung/vị trí, ghi rõ không có bố cục đáng tin và giữ đường parser chỉ dùng chữ. Document Intake chọn chứng cứ tốt nhất theo quy tắc nghiệp vụ, không để bot chọn trường/ngày cấp GCN. Nếu v1 chưa giữ được chất lượng đường OCR hiện tại, phải hiện giới hạn chất lượng/trạng thái, không ngầm báo tương đương. Mỗi ảnh/trang có trạng thái chờ, thành công hoặc lỗi; lỗi Qwen có retry riêng, không chặn listener. Khi chưa có text do lỗi, vẫn bàn giao trạng thái và nguồn, không bịa text. |
| CAP-06 | Vòng đời ảnh 168h | Ảnh gốc và ảnh dẫn xuất/cache trên server hết hạn tại captured_at + 168 giờ và tự xóa, kể cả máy chính chưa ACK. Tải lại hoặc OCR lại không kéo dài hạn. Trước khi xóa, ghi bền vững trạng thái OCR/tải cuối cùng và công bố gói dữ liệu mới nếu cần cập nhật; không sửa gói đã công bố. Công việc chưa xong chuyển sang hết hạn. Xóa ảnh không được xóa gói dữ liệu hoặc sổ gửi đang chờ ACK. |
| CAP-07 | Source policy | Chỉ nhận nội dung từ tài khoản văn phòng, nhóm và nguồn đã bật theo chính sách. Không mở thêm nguồn vì lỗi hoặc vì nút Sync. Sự kiện không rõ nguồn giữ dấu kỹ thuật tối thiểu và chờ xác định, không tự thu nội dung ngoài phạm vi. |
| CAP-08 | Dedupe / payload lạ | ID thiếu, loại file chưa hỗ trợ hoặc payload lạ được ghi trạng thái rõ. Cùng ID nguồn được giao lại không tạo thêm tin/ảnh; hai tin khác ID nhưng ảnh giống nhau vẫn là hai nguồn. |
| CAP-09 | Self-message / My Documents | Ảnh do chính tài khoản văn phòng gửi trong nhóm đã bật có quy tắc thử riêng; không bỏ mọi self-message. My Documents là capability riêng, chưa được suy ra từ các tin tự gửi khác. |
| CAP-10 | Lỗi vận hành | Mất mạng, hết dung lượng, Qwen lỗi, hàng đợi nghẽn và tiến trình treo được báo bằng trạng thái/sự cố có ID. Ưu tiên nhận và ghi nhật ký trước OCR; không âm thầm bỏ công việc. |
| CAP-11 | Nội dung gói | Gói bàn giao chứa raw text/OCR, trạng thái của từng tin/ảnh/trang, `captured_at`, nguồn hội thoại/người gửi, ID tin/attachment/trang/dòng và version Qwen/cấu hình. Khi provider trả vị trí dòng chữ, gói giữ nguyên `location`/`rotate_rect`, thứ tự phần tử nhận được, kích thước ảnh thực gửi, dấu vết biến đổi và `geometry_status`; trạng thái chưa xác minh vẫn được giữ như raw evidence nhưng Document Intake không dùng để suy bố cục cho tới khi phép đối chiếu khung đạt kiểm thử. Không giả định Qwen cấp sẵn `page_index` hoặc `reading_order`. Ảnh OCR lỗi hoặc provider không trả vị trí vẫn có record trạng thái/chữ nếu có, không bịa chữ hay tọa độ. **Không có `results.json` từ bot** hoặc các thực thể người/tài sản/nhóm đã xử lý trong base contract. Không có file ảnh, thumbnail, base64, URL hay path ảnh trong manifest, record hoặc payload. |
| CAP-12 | Gói bất biến & chờ ACK | Gói đã công bố là bất biến. Gói dữ liệu chưa được ACK phải giữ qua restart và sau khi ảnh 7 ngày đã xóa. Gửi lại cùng gói không tạo dữ liệu trùng tại máy chính; lỗi ảnh không ngăn gói dữ liệu được bàn giao. Máy chính giữ bản gói file đã nhập trong `imported/` để người vận hành mở lại raw/status/hash khi kiểm lỗi, đồng thời giữ raw cần thiết cho parser/review. MIN-92 chốt thời hạn và giới hạn dung lượng **hữu hạn** của raw/status trên bot sau ACK trước thử dữ liệu thật. MIN-102 chốt chính sách giữ/dọn bản file `imported/` và raw nội bộ trên máy chính; MIN-99 thực hiện. Dọn file không được làm mất raw còn cần để phân tích lại. Không để chính sách giữ vô hạn mặc định. |
| CAP-13 | Quan sát/quota | Theo dõi tốc độ nhận, tuổi hàng đợi OCR, tuổi gói chưa ACK và dung lượng journal/gói dữ liệu. Khi sắp đầy đĩa, báo sớm và giảm việc phụ; quy tắc tự xóa 7 ngày chỉ áp dụng cho ảnh, không áp dụng cho gói dữ liệu chưa ACK. |
| CAP-14 | Sửa/thu hồi/reaction | Sửa/thu hồi/reaction nếu adapter giao được ghi như sự kiện nguồn riêng, có tham chiếu tin gốc; không xóa text OCR cũ một cách âm thầm. Loại sự kiện adapter không cung cấp được báo là chưa hỗ trợ, không hứa đã thu đủ. |
| CAP-15 | Nhật ký kết nối | Module ghi bền vững các lần kết nối, ngắt kết nối và đăng nhập lại quan sát được của listener, kèm mốc bắt đầu/kết thúc và lý do nếu biết. Máy chính thấy khoảng thời gian bot có thể không nghe được để người dùng đối chiếu trong Zalo thật. Khoảng này chỉ là cảnh báo; không chứng minh đã thiếu tin hoặc đã thu đủ ở phần còn lại. |
| CAP-16 | OCR lại có giới hạn | Document Intake được gửi yêu cầu OCR lại có loại định sẵn theo `logical_id` ảnh/trang đã nhận, raw revision đã phân tích, ID yêu cầu chống lặp và lý do. Bot kiểm quyền consumer/nguồn, revision còn mới, ảnh còn trước `captured_at + 168 giờ`, ngân sách lượt Qwen và loại yêu cầu; không chấp nhận byte ảnh, tọa độ cắt tự do, prompt hoặc lệnh Qwen tùy ý. Cùng yêu cầu lặp không gọi Qwen nhiều lần. Thành công/lỗi/hết hạn đều có trạng thái bền vững; job đã nhận công bố gói raw revision mới bất biến với chữ hoặc status lỗi, `captured_at` gốc và `ocr_pass_id`/vùng/lần thử khi có OCR. Yêu cầu bị từ chối trước job chỉ có status theo request_id. Máy chính Sync/ACK gói mới như gói raw thường, parser tạo revision nội bộ và không ghi đè giá trị người dùng đã duyệt. |

## 3. Ghi chú vận hành đi kèm (nguyên văn §2, phần sau bảng)

Module có thể giữ ảnh trong 7 ngày cho công việc OCR và kiểm tra vận hành tại
nơi có ảnh, nhưng đường bàn giao sang máy chính chỉ là chữ, trạng thái và
metadata. Hết 7 ngày, nếu OCR chưa thành công thì máy chính chỉ nhận trạng
thái lỗi/hết hạn; không có đường để máy chính yêu cầu ảnh đã xóa.

Vị trí từng dòng chữ là **dấu vết OCR**, không phải trường nghiệp vụ.
[Tài liệu Qwen VL OCR](https://www.alibabacloud.com/help/en/model-studio/qwen-vl-ocr-api-reference)
mô tả `advanced_recognition` có `words_info` gồm chữ và vị trí theo dòng, nhưng
không hứa tọa độ riêng cho mỗi từ/ký tự hoặc giải thích đầy đủ khung tọa độ
sau khi dịch vụ tự đổi kích thước/xoay. Đường code hiện tại mới lấy chuỗi chữ,
chưa có khả năng này. MIN-92 chốt schema, đơn vị/kích thước khung tọa độ, dấu
vết ánh xạ và cách đánh dấu thiếu hoặc sai vị trí; MIN-95/98 dùng ảnh có mốc
để kiểm cách đối chiếu khung và đo chất lượng trước khi bật đường nhận diện
nâng cao. Với ảnh đã xoay, cắt hoặc đổi kích thước, phải biết vị trí đang tính
trên bản ảnh nào và cách đối chiếu giữa các lượt; không tự xem các số tọa độ
khác khung là cùng một chỗ. Không chuyển ảnh hay đường dẫn ảnh sang máy chính.

## 4. Bản đồ chủ đề → nơi chi tiết hóa

| Chủ đề | CAP | Chi tiết kỹ thuật ở |
|---|---|---|
| Listener, session/QR, single-account | CAP-01, CAP-02, CAP-15 | `docs/connector-protocol.md` (wire connector↔module), `docs/local-runbook.md` (chạy) |
| Source policy, consent, discovery | CAP-07, CAP-08, CAP-09 | `docs/connector-protocol.md` (event discovery/policy_ack); policy storage ở `connector_accounts`/`conv_sources` (engine, MIN-94) |
| Journal + raw provenance | CAP-03, CAP-08 | `journal_entries`/`records`/`sources` m0001; `docs/migration-notes.md` |
| Media download + 168h | CAP-04, CAP-06 | `storage/` media + retention; `ZALO_INBOX_STORAGE_ROOT`, `ZALO_CONNECTOR_RETENTION_HOURS` |
| Qwen OCR | CAP-05 | `src/zalo_module/ocr/` (MIN-95), env `QWEN_*` |
| Gói raw + ACK | CAP-11, CAP-12 | `contracts/zalo-intake/` (SOT wire), `delivery/` |
| OCR lại có giới hạn | CAP-16 | `contracts/zalo-intake/` (ocr-request schema), `ocr/` request ledger |
| Quan sát, gap, sự kiện adapter | CAP-10, CAP-13, CAP-14, CAP-15 | `listener_sessions`, `jobs`, `/connector/v1/state` |

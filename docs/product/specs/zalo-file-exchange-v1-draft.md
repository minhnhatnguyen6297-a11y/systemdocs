# Gói raw OCR Zalo v1 — file và API nháp

**Status: DRAFT — MIN-89, 24/09/2026, revision 4 của riêng bản nháp này; contract chính thức thuộc MIN-92.** Revision của [thiết kế tổng thể](2026-09-24-zalo-independent-intake.md) được đánh số riêng, không phải version contract. File này chỉ đề xuất hình dạng gói raw OCR, API Sync/ACK và yêu cầu OCR bổ sung. API, tên trường và cách lưu còn cần duyệt; chưa publish vào `contracts/`.

**Chỉ MIN-92 dùng file này để soạn/duyệt contract.** Agent làm runtime phải đọc bản được publish trong `contracts/`; nếu bản đó chưa có thì phần tích hợp qua ranh giới hai repo chưa được mở. [Trang chỉ đường](../../../notary_v2/docs/platform/zalo-document-inbox/README.md) nêu nguồn chuẩn cho từng phần.

Theo [spec Zalo Inbox chính](../../../notary_v2/docs/platform/zalo-document-inbox/spec.md), bot bàn giao chữ OCR/trạng thái/nguồn; Document Intake xử lý nghiệp vụ sau Sync. Bản nháp cũ có `results.json` do bot xử lý đã bị thay thế. Gói mới không chứa kết quả bóc/ghép hoặc ảnh và đường truy cập ảnh.

## 1. Ranh giới và dữ liệu tối thiểu

| Bên | Sở hữu |
|---|---|
| Module Zalo | Listener, phiên đăng nhập, journal sự kiện, `captured_at`, ảnh tạm, chuẩn bị/xoay/cắt ảnh khi cần, Qwen OCR, trạng thái từng attachment/trang, gói raw và API bàn giao |
| Document Intake trên máy công chứng | Nhập raw bền vững, parser/regex/phân loại, bóc trường, ghép hai mặt/người/tài sản, gợi ý nhóm, phiên bản kết quả riêng và thẻ chờ người dùng duyệt |
| Giao tiếp giữa hai repo | Chỉ raw text/OCR, trạng thái, ID nguồn, thời gian và thông tin kỹ thuật để kiểm tra/nhập lại an toàn; không gọi parser hoặc DB của repo kia |

Mỗi attachment bot đã ghi nhận phải có record chữ OCR hoặc record trạng thái chưa có chữ. Không tạo người/tài sản giả từ một ảnh OCR lỗi. `producer_id`, `source_account_id`, `consumer_id` ổn định qua restart; đăng nhập lại cùng tài khoản không đổi identity. Máy chính có một bộ Sync và credential riêng. ACK là biên nhận **raw đã nhập an toàn**, không chờ Document Intake phân tích hoặc người dùng duyệt.

## 2. Endpoint đề xuất

API chỉ cho consumer đã xác thực truy cập gói của mình. Thử local trên cùng máy cho phép HTTP có xác thực trên loopback (`127.0.0.1` hoặc `::1`), không bind mạng LAN/công cộng. Khi chuyển server và máy chính kết nối qua mạng, dùng HTTPS. URL và credential cấu hình trong backend máy chính, không đặt trong renderer, file gói hoặc log.

| Endpoint | Tác dụng |
|---|---|
| `GET /intake/v1/packages?delivery=pending&after=<sequence>&limit=100` | Liệt kê gói raw đã công bố mà consumer chưa ACK, theo sequence tăng dần |
| `GET /intake/v1/packages/{package_id}/manifest` | Tải `manifest.json` |
| `GET /intake/v1/packages/{package_id}/records` | Tải `records.jsonl` dạng văn bản |
| `GET /intake/v1/packages/{package_id}/ready` | Tải `READY.json` ràng buộc hash manifest |
| `POST /intake/v1/receipts` | Báo raw đã nhập an toàn hoặc lỗi gói/hash/schema |
| `GET /intake/v1/status` | Trạng thái kết nối, OCR chờ/lỗi, số gói pending và thời điểm quan sát |
| `POST /intake/v1/ocr-requests` | Máy chính yêu cầu một biến thể OCR có giới hạn cho **ảnh bot đã ghi nhận và còn hạn**, chỉ truyền ID/kiểu yêu cầu, không truyền ảnh |
| `GET /intake/v1/ocr-requests/{request_id}` | Xem trạng thái yêu cầu đã nhận; kết quả chữ vẫn đi bằng gói raw revision mới |

Không có endpoint `/results` hoặc endpoint lấy ảnh trong contract này. Text chỉ được hiển thị như dữ liệu; consumer không thực thi HTML/lệnh hoặc tự tải URL xuất hiện trong chữ OCR. Hash phát hiện file hỏng, còn quyền đọc/gửi do xác thực và phân quyền thực hiện.

### Yêu cầu OCR thêm từ Document Intake

OCR mặc định chạy khi bot bắt ảnh, để máy chính mở vào buổi sáng đã có chữ. Document Intake trong Soạn hồ sơ xét chữ và nguồn; khi thiếu chứng cứ như ngày cấp GCN, nó có thể yêu cầu **một biến thể OCR đã định nghĩa** trong thời hạn ảnh. Bot không phân loại giấy hay chọn ngày cấp; nó chỉ thực hiện thao tác ảnh và gọi Qwen tại nơi giữ ảnh. Đây là phần bổ sung đã được owner chọn ngày 24/09/2026; không phải tính năng lấy bù tin bot chưa từng bắt của MIN-90.

Request đề xuất gồm `request_id` (UUID do consumer cấp, làm khóa chống lặp), `consumer_id`, `logical_id` của ảnh/trang đã xuất trong raw, `observed_revision` mà consumer đã phân tích, `variant`, tham số preset nếu có và `requested_at`. Enum ban đầu để MIN-92 duyệt: `rotate`, `crop_bottom`, `full_res`. `crop_bottom` chỉ nhận preset vùng chân ảnh do contract định nghĩa (ví dụ `bottom_quarter` hoặc `bottom_third`), không nhận tọa độ/tỷ lệ tự do, URL, đường dẫn, byte ảnh, prompt hoặc lệnh Qwen tùy ý. Module kiểm danh tính consumer, ảnh thuộc tài khoản/nguồn đã bật, ảnh gốc còn tồn tại và `now < image_expires_at`. Yêu cầu quá hạn trả `source_image_expired`, không tải lại ảnh để kéo dài hạn 168 giờ. Nếu producer đã có revision mới hơn bản consumer dùng để quyết định, trả `stale_revision` để máy chính Sync/parse lại trước khi yêu cầu thêm.

Một `request_id` gửi lặp với cùng nội dung trả cùng job/result; cùng ID nhưng nội dung khác trả `request_conflict`. Cùng `logical_id + variant + tham số + OCR config version` không gọi Qwen lại nếu lượt đó đã có. Trần thử ban đầu được đề xuất là **hai job biến thể bổ sung cho mỗi khóa quota trong toàn hạn 168 giờ** ngoài OCR mặc định; MIN-92 phải chốt khóa quota là attachment hay từng trang trước khi code. Retry lỗi nhà cung cấp có trần riêng, không tạo job mới để lách hạn mức. Có thêm hạn mức Qwen/consumer/ngày và số job đồng thời; MIN-92 chốt số cụ thể trước code và MIN-98 đo đủ/chi phí. Module ghi yêu cầu/job bền vững trước khi phản hồi `accepted`, trả `request_id`/trạng thái; lỗi có mã `unknown_source`, `unsupported_variant`, `source_image_expired`, `source_image_unavailable`, `budget_exceeded`, `rate_limited`, `stale_revision`, `unauthorized`, `request_conflict` hoặc `provider_failed` tương ứng. Việc chấp nhận job không có nghĩa Qwen đã hoàn tất.

Ví dụ request giả cho một lượt cắt vùng chân ảnh; schema/trường vẫn chờ MIN-92 duyệt:

```json
{
  "schema_version": "intake.ocr-request.v1",
  "request_id": "50000000-0000-4000-8000-000000000001",
  "consumer_id": "10000000-0000-4000-8000-000000000003",
  "logical_id": "20000000-0000-4000-8000-000000000002",
  "observed_revision": 1,
  "variant": "crop_bottom",
  "preset": "bottom_quarter",
  "reason_code": "insufficient_text",
  "requested_at": "2026-09-24T08:01:00+07:00"
}
```

Ví dụ trạng thái sau khi Qwen xong; chữ thật và provenance chỉ nằm trong **gói file raw mới**, không nằm trong response này:

```json
{
  "schema_version": "intake.ocr-request-status.v1",
  "request_id": "50000000-0000-4000-8000-000000000001",
  "state": "completed",
  "published_package_id": "50000000-0000-4000-8000-000000000002",
  "completed_at": "2026-09-24T08:02:00+07:00",
  "error_code": null
}
```

Khi job **đã được nhận** hoàn tất hoặc Qwen/file lỗi trong lúc chạy, module công bố **gói file raw revision mới, bất biến** có chữ mới hoặc record status lỗi, giữ nguyên `captured_at` và ID nguồn. `ocr.attempts[]` thêm lượt với `ocr_pass_id`, thao tác/vùng và chữ nếu Qwen thành công. Yêu cầu **bị từ chối trước khi tạo job** (quyền sai, revision cũ, ảnh đã hết hạn, hết ngân sách) chỉ lưu/trả trạng thái theo `request_id`, không phải tạo gói raw giả. Máy chính lấy gói được công bố bằng cùng feed pending/ACK hiện tại, nhập chống trùng rồi tự chạy lại Document Intake khi có chữ mới. Kết quả mới là revision nội bộ để so sánh; không ghi đè field, nhóm hoặc hồ sơ người dùng đã duyệt. Yêu cầu thất bại không xóa chữ của lượt OCR trước. **Còn mở cho MIN-92:** thứ tự giữa revision raw, request/job và gói nhận khi hai yêu cầu tới gần nhau; gộp biến thể vào một request không tự giải quyết trường hợp hai request đồng thời. Cần test crash/ACK thất lạc và quyền gửi yêu cầu.

### Sequence và một lượt Sync

`sequence` là số thứ tự module công bố **gói raw**, tăng bền vững cho producer/consumer; không phải số tin nhắn Zalo và không dựa vào `captured_at`. OCR xong muộn vẫn được công bố với sequence mới.

Mỗi lượt Sync bắt đầu với `after=0, delivery=pending`. Trang đầu chốt `until_sequence` là gói cao nhất tại lúc bắt đầu; các trang tiếp dùng cùng `until_sequence` và `after` là sequence cuối trang trước. Server trả `next_after`, `has_more`, `until_sequence` và danh sách `package_id`/`sequence`/`manifest_hash`. Gói công bố sau mốc này lấy ở lượt kế tiếp. Không dùng offset trên danh sách đang co lại do ACK.

Bộ Sync ghi bền vững danh sách gói cần nhận trước khi chuyển trang. Gói tải lỗi vẫn pending; các gói độc lập khác tiếp tục. Lượt mới quét pending từ đầu nên gói cũ tải lỗi không mất vĩnh viễn. `after` chỉ dùng phân trang, **không phải ACK**. Kích hoạt Sync khi backend khởi động, nối lại mạng, đến chu kỳ cấu hình hoặc người dùng bấm **Sync**; chỉ một lượt active. Nút Sync không gọi lịch sử Zalo hoặc yêu cầu OCR lại.

## 3. File và folder cục bộ

Module công bố gói bất biến. Máy chính tự tải vào đường dẫn cấu hình:

```text
<data_root>/zalo-intake/
  staging/<package_id>/
  ready/<package_id>/
    manifest.json
    records.jsonl
    READY.json
  imported/<package_id>/
    manifest.json
    records.jsonl
    READY.json
  quarantine/<package_id>/
  sync-state/                 # sổ gói raw đã lưu, gói lỗi, receipt cần gửi lại
```

Toàn bộ folder chỉ chứa chữ OCR/trạng thái/metadata. Không có `results.json`, folder ảnh hoặc cache ảnh kể cả tạm thời. Consumer không truy cập filesystem, DB hoặc cookie của bot. Kết quả parser và revision do Document Intake tạo trong kho nghiệp vụ của hệ thống công chứng. Ứng dụng Zalo khác có lưu ảnh trên cùng máy nằm ngoài phạm vi này.

1. Module ghi `records.jsonl` và `manifest.json` trong staging, flush xuống lưu trữ, ghi `READY.json` cuối rồi công bố gói bằng thao tác đổi tên nguyên tử trên cùng filesystem đã kiểm chứng. Startup quét phục hồi gói dở.
2. Client tải vào staging riêng. Xác minh đủ file, hash, size, count, schema và identity nguồn. Không đọc file đang tải dở như gói hoàn chỉnh.
3. Client chuyển sang ready, nhập raw và sổ nhập/database bền vững theo khóa phiên bản. Không chờ parser chạy xong.
4. Chuyển sang imported theo nhật ký phục hồi; không copy thành nhiều bản không cần thiết. Chỉ sau **raw và sổ nhập** an toàn mới gửi ACK. Crash giữa các bước dùng sổ để tiếp tục.
5. Gói sai vào quarantine có lý do, chưa ACK accepted; không chặn gói độc lập khác.

Không phụ thuộc filesystem watcher. Bộ nhập quét ready/sổ khi startup và sau tải; không dựa vào thời gian sửa file để biết dữ liệu mới. Không ghi một JSONL chung đang append đồng thời với reader.

## 4. Manifest và READY

| Trường | Ý nghĩa |
|---|---|
| `schema_version` | `intake.raw-package.v1` — tên đề xuất, cần MIN-92 phê duyệt |
| `package_id`, `producer_id`, `consumer_id` | UUID; consumer phải đúng máy chính logic |
| `sequence` | Thứ tự công bố gói raw, tăng bền vững |
| `package_ready_at` | Giờ gói hoàn tất, có múi giờ |
| `record_count` | Số dòng JSON thực tế trong `records.jsonl` |
| `files[]` | Chỉ `records.jsonl`, có size byte, SHA-256 và MIME văn bản |

Ví dụ hình dạng; size/hash là **giá trị giả**, không phải fixture đã kiểm hash với file thật:

```json
{
  "schema_version": "intake.raw-package.v1",
  "package_id": "10000000-0000-4000-8000-000000000001",
  "producer_id": "10000000-0000-4000-8000-000000000002",
  "consumer_id": "10000000-0000-4000-8000-000000000003",
  "sequence": 42,
  "package_ready_at": "2026-09-24T00:03:00+07:00",
  "record_count": 2,
  "files": [{
    "path": "records.jsonl",
    "size_bytes": 1700,
    "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "mime_type": "application/x-ndjson"
  }]
}
```

`READY.json` gồm `schema_version=intake.ready.v1`, `package_id`, `manifest_sha256`, `published_at`. Hash tính trên byte UTF-8 gốc, không parse rồi serialize lại. File/path ngoài danh sách cho phép bị từ chối; chặn absolute path, `..`, junction/symlink thoát thư mục, alternate data stream và trùng tên khác hoa/thường trên Windows. Giới hạn size/count cần cấu hình trong contract. READY chứng minh gói đã ghi xong; không chứng minh bot bắt đủ mọi ảnh trên Zalo, OCR thành công hoặc người dùng đã duyệt.

## 5. Mỗi dòng raw OCR/trạng thái

Một record là chữ tin nhắn (`message_text`), chữ OCR của một attachment/trang (`ocr_page`), trạng thái attachment chưa có chữ (`processing_status`), sự kiện nguồn mà adapter phát được (`source_event`) hoặc mốc kết nối listener (`listener_session`). Record giữ dòng text theo thứ tự, không chuyển thẳng toàn bộ phản hồi Qwen nếu payload chứa ảnh, URL ảnh hay secret.

| Trường | Quy định đề xuất |
|---|---|
| `schema_version` | `intake.raw-record.v1` |
| `record_kind` | `message_text`, `ocr_page`, `processing_status`, `listener_session`; `source_event` cho sửa/thu hồi/reaction nếu adapter phát được và MIN-92 duyệt shape |
| `record_id` | UUID của phiên bản record bất biến này |
| `logical_id`, `revision`, `supersedes_record_id` | ID ổn định của cùng nguồn ảnh/trang/tin/sự kiện, revision tăng từ 1; bản mới trỏ bản trước |
| `source` | provider, source_account_id, conversation_id/type, provider_message_id, sender_id; tên hiển thị tùy chọn. Với listener_session chỉ cần account; conversation/message/sender null. |
| `attachment_id`, `attachment_index`, `page_index` | Nhận diện nguồn, không phải file/path/link ảnh; null cho message_text/source_event/listener_session |
| `captured_at` | Bắt buộc; với tin/ảnh là giờ bot lần đầu nhận tin, giữ nguyên qua retry/revision. Với source_event/listener_session là giờ module quan sát sự kiện/chuyển trạng thái. |
| `source_sent_at` | Giờ Zalo báo đã gửi nếu có; nullable, chỉ để đối chiếu |
| `image_expires_at` | `captured_at + 168 giờ`; chỉ metadata về ảnh trên module, null cho message_text/source_event/listener_session |
| `ocr` | status, provider/model/config_version, started_at/completed_at, error; nếu đã OCR nhiều lần từ ảnh gốc/xoay/cắt vùng thì giữ `attempts[]` có `ocr_pass_id`, tác vụ OCR, biến thể text, thao tác ảnh, `region`, khung ảnh thực gửi và trạng thái tọa độ từng lượt; `selected_pass_ids[]` chỉ transcript mặc định đề xuất. Null cho message_text/source_event/listener_session. Tên trường hình học chính thức chờ MIN-92. |
| `source_event` | Chỉ với record_kind tương ứng: `event_type`, ID tin đích, ID sự kiện nếu Zalo cấp, trạng thái hỗ trợ và nội dung text mới nếu adapter thực sự giao; không chứa ảnh/link ảnh, không tự sửa raw OCR hoặc hồ sơ cũ |
| `listener_session` | Chỉ với record_kind tương ứng: session_id, `connected`/`disconnected`/`login_required`, giờ quan sát, lý do nếu biết và heartbeat cuối; các đoạn mất kết nối do crash chỉ là ước lượng có gắn cờ, không cam kết bắt đủ tin. |
| `text_lines[]` | Các dòng được chọn để parser đọc: `line_id`, text, `captured_at`, page_index, `ocr_pass_id`, `region` và tham chiếu về dòng provider trong đúng lượt nếu có; thứ tự mảng là transcript mặc định, không khẳng định thứ tự hình học do provider bảo đảm |
| `recorded_at` | Giờ phiên bản raw được ghi bền vững |

Hai ví dụ tổng hợp minh họa hai ảnh của cùng một tin: ảnh đầu OCR thành công, ảnh sau còn chờ thử lại. Đây **không phải dữ liệu cá nhân thật** và không phải ví dụ kết quả bóc/ghép. Mỗi đối tượng trong file thật nằm trên **một dòng JSONL**.

```json
{
  "schema_version": "intake.raw-record.v1",
  "record_kind": "ocr_page",
  "record_id": "20000000-0000-4000-8000-000000000001",
  "logical_id": "20000000-0000-4000-8000-000000000002",
  "revision": 1,
  "supersedes_record_id": null,
  "source": {
    "provider": "zalo_personal",
    "source_account_id": "10000000-0000-4000-8000-000000000004",
    "conversation_id": "demo-group",
    "conversation_type": "group",
    "provider_message_id": "demo-message",
    "sender_id": "demo-sender"
  },
  "attachment_id": "demo-attachment-0",
  "attachment_index": 0,
  "page_index": 1,
  "captured_at": "2026-09-24T00:01:00+07:00",
  "source_sent_at": "2026-09-24T00:00:58+07:00",
  "image_expires_at": "2026-10-01T00:01:00+07:00",
  "ocr": {
    "status": "succeeded",
    "provider": "qwen",
    "model": "qwen-vl-ocr-2025-11-20",
    "config_version": "ocr-config-v1",
    "started_at": "2026-09-24T00:01:03+07:00",
    "completed_at": "2026-09-24T00:02:00+07:00",
    "error": null,
    "selected_pass_ids": ["demo-pass-original"],
    "attempts": [{
      "ocr_pass_id": "demo-pass-original",
      "image_operation": "original",
      "region": {"kind": "full_image"},
      "status": "succeeded",
      "provider": "qwen",
      "model": "qwen-vl-ocr-2025-11-20",
      "config_version": "ocr-config-v1",
      "text_lines": [{"line_id": "40000000-0000-4000-8000-000000000001", "text": "CHỮ OCR MINH HỌA"}]
    }]
  },
  "text_lines": [{
    "line_id": "40000000-0000-4000-8000-000000000001",
    "text": "CHỮ OCR MINH HỌA",
    "captured_at": "2026-09-24T00:01:00+07:00",
    "page_index": 1,
    "ocr_pass_id": "demo-pass-original",
    "region": {"kind": "full_image"}
  }],
  "recorded_at": "2026-09-24T00:02:01+07:00"
}
```

```json
{
  "schema_version": "intake.raw-record.v1",
  "record_kind": "processing_status",
  "record_id": "20000000-0000-4000-8000-000000000003",
  "logical_id": "20000000-0000-4000-8000-000000000004",
  "revision": 1,
  "supersedes_record_id": null,
  "source": {
    "provider": "zalo_personal",
    "source_account_id": "10000000-0000-4000-8000-000000000004",
    "conversation_id": "demo-group",
    "conversation_type": "group",
    "provider_message_id": "demo-message",
    "sender_id": "demo-sender"
  },
  "attachment_id": "demo-attachment-1",
  "attachment_index": 1,
  "page_index": 1,
  "captured_at": "2026-09-24T00:01:00+07:00",
  "source_sent_at": "2026-09-24T00:00:58+07:00",
  "image_expires_at": "2026-10-01T00:01:00+07:00",
  "ocr": {
    "status": "retry_pending",
    "provider": "qwen",
    "model": "qwen-vl-ocr-2025-11-20",
    "config_version": "ocr-config-v1",
    "started_at": "2026-09-24T00:01:03+07:00",
    "completed_at": null,
    "error": {"code": "demo-ocr-timeout", "retryable": true}
  },
  "text_lines": [],
  "recorded_at": "2026-09-24T00:02:02+07:00"
}
```

### Thời gian, lỗi và bản OCR mới

`captured_at` do collector ghi khi callback nhận tin lần đầu, trước OCR; mọi attachment/trang/dòng cùng tin kế thừa mốc đó. `imported_at` ghi riêng tại máy chính. Replay cùng tin không đổi ngày nhận thành ngày Sync. Lỗi OCR không làm mất dấu attachment.

Trạng thái OCR gồm `succeeded`, `retry_pending`, `failed`, `source_image_expired`, `unsupported`. Có thể bàn giao status khi OCR còn chờ để người dùng thấy ảnh bot đã nhận mà chưa có chữ; sau thành công tạo revision mới của logical_id. Danh sách attachment đã biết phải được hạch toán đủ thành record hoặc trạng thái chờ. Số ảnh bot đếm **không xác minh** được tổng số ảnh thật trên Zalo.

`text_lines[]` ngoài `ocr` là transcript **mặc định theo tiêu chí kỹ thuật** để Document Intake đọc trước. Nếu module thử xoay ảnh hoặc cắt vùng cuối giấy rồi gọi Qwen thêm lần nữa, record giữ cả các biến thể text OCR trong `ocr.attempts[]`. Mỗi dòng mặc định có `ocr_pass_id` và `region` để quay về đúng lượt OCR/vùng ảnh; nhiều lượt có thể cùng đóng góp vào transcript, nên `selected_pass_ids[]` là mảng. **Document Intake được xét mọi attempt và chọn chứng cứ cho từng trường**; bot không quyết định ảnh là loại giấy nào, ngày cấp nào đúng hoặc trường nào thuộc ai. `region` chỉ là mô tả phần ảnh đã đọc, không chứa bytes, path hoặc URL ảnh. Cách biểu diễn vùng, ID dòng ở biến thể phụ và giới hạn kích thước do MIN-92 duyệt. **Còn mở cho MIN-92:** tiêu chí kỹ thuật chọn transcript mặc định và việc transcript có thay khi OCR bổ sung về; phải giữ nguồn từng pass/dòng để parser xét. Việc bắt buộc luôn chọn lượt `original` hoặc bỏ `selected_pass_ids[]` chưa được duyệt. Nếu bước đầu chưa đạt chất lượng tương đương đường OCR có rescue hiện tại, công bố trạng thái/giới hạn chất lượng để người dùng biết, không âm thầm khẳng định ảnh đã được đọc đủ. Yêu cầu OCR bổ sung đi qua endpoint có giới hạn ở §2 và raw revision mới; máy chính vẫn không nhận ảnh.

### Chữ và vị trí từng dòng OCR

Theo [Qwen-OCR API reference](https://www.alibabacloud.com/help/en/model-studio/qwen-vl-ocr-api-reference) và [hướng dẫn text extraction](https://www.alibabacloud.com/help/en/model-studio/qwen-vl-ocr) (kiểm ngày 24/09/2026), DashScope native API có tác vụ `parameters.ocr_options.task=advanced_recognition`. Tác vụ này trả `ocr_result.words_info[]` gồm chữ và vị trí **từng dòng**; `text_recognition` trả chữ thường. Đây là dữ liệu vị trí do provider trả, khác JSON trường nghiệp vụ do prompt yêu cầu. Model `qwen-vl-ocr-2025-11-20` hiện dùng cũng là model trong ví dụ chính thức. Khả năng lấy vị trí dòng là **năng lực đích dự kiến dùng mặc định**, cần đánh giá trước triển khai. MIN-92 định nghĩa contract cho cả chữ và vị trí cùng cấu hình thử an toàn; MIN-98 đo chất lượng chữ, vị trí, thời gian và số lượt gọi trên mẫu CCCD/GCN rồi mới chốt tác vụ mặc định cho vận hành. Trước phép đo đó, không coi `advanced_recognition` đã tốt hơn hoặc bật mặc định trong runtime.

Ví dụ tối thiểu cho nhánh thử ở cùng DashScope native endpoint hiện có; không chứa ảnh, key hoặc dữ liệu thật:

```json
{
  "model": "qwen-vl-ocr-2025-11-20",
  "input": {"messages": [{"role": "user", "content": [{"image": "<ảnh nội bộ module>"}]}]},
  "parameters": {"ocr_options": {"task": "advanced_recognition"}}
}
```

Gói raw dự kiến giữ **theo từng `ocr_pass_id` và trang nguồn**: tác vụ/model/config của lượt, ID khung ảnh đã thực gửi, chiều rộng/cao khung đó, chuỗi thao tác từ ảnh nguồn đến khung (`EXIF` orientation, cắt vùng, đổi kích thước, xoay nếu đã làm), và từng phần tử `words_info` hợp lệ với text, `location` tám tọa độ, `rotate_rect` năm giá trị. Theo hướng dẫn Alibaba, `location` là tọa độ tuyệt đối trên "ảnh gốc", gốc góc trên trái, bốn đỉnh theo thứ tự trên trái → trên phải → dưới phải → dưới trái; `rotate_rect` là tâm, rộng, cao và góc so với chiều ngang trong khoảng `[-90, 90]`. Tài liệu chưa nói rõ "ảnh gốc" được hiểu theo khung nào sau khi provider tự đổi kích thước hoặc tự xoay. Vì vậy module phải ghi kích thước ảnh thực gửi và các phép biến đổi phía client, rồi MIN-95/98 kiểm bằng ảnh có mốc trước khi coi tọa độ khớp khung đó hoặc ánh xạ về ảnh Zalo. Tên thao tác `original` cũng không chứng minh khung này trùng ảnh Zalo nguyên gốc vì module có thể đã xoay theo EXIF hoặc resize. Dạng trường/ID, giới hạn số dòng, quy tắc map lại ảnh nguồn và cách lưu metadata transform do MIN-92 duyệt; không tự tạo tọa độ toàn ảnh từ crop hoặc quy ước đơn vị/góc/trang mà tài liệu provider không ghi rõ.

Ví dụ một dòng trong khung ảnh gửi rộng `1000`, cao `600` (chỉ minh họa **envelope do module/contract dự kiến tạo**, chưa là schema duyệt hoặc response nguyên dạng của Qwen). Trong ví dụ, chỉ `text`, `location` và `rotate_rect` ở phần tử dòng là các trường vị trí được tài liệu provider mô tả; `ocr_pass_id`, `source_page_index`, `submitted_frame`, `geometry_status`, `provider_lines` và `element_index` là cách module đề xuất lưu nguồn, chờ MIN-92 duyệt:

```json
{
  "ocr_pass_id": "demo-pass-advanced",
  "source_page_index": 1,
  "submitted_frame": {"frame_id": "demo-frame-1", "width": 1000, "height": 600},
  "geometry_status": "provider_returned_mapping_unverified",
  "provider_lines": [{
    "element_index": 0,
    "text": "CHỮ MINH HỌA",
    "location": [100, 100, 300, 100, 300, 130, 100, 130],
    "rotate_rect": [200, 115, 200, 30, 0]
  }]
}
```

MIN-92 cần định nghĩa kiểm tra khung/đỉnh, dữ liệu thiếu/sai và trạng thái cảnh báo. Nếu provider chỉ trả chữ hoặc khung không hợp lệ, bàn giao chữ cùng trạng thái **không có vị trí đáng tin**, không bịa hộp chữ. Nếu `enable_rotate=true`, provider tự đổi kích thước theo `min_pixels/max_pixels`, hoặc module cắt/xoay/resize ảnh, chưa được suy rằng tọa độ đã map đúng về ảnh Zalo hay khung đã ghi; chỉ dùng vị trí sau khi phép đối chiếu khung đã được MIN-95/98 kiểm chứng, nếu chưa thì giữ làm raw kèm trạng thái chưa xác minh. Không giả định `words_info` có thứ tự đọc, số trang, confidence hay tọa độ từng ký tự.

Module gán `element_index` từ vị trí thực của phần tử trong mảng `words_info` của **đúng lượt OCR**, kết hợp với `ocr_pass_id`/frame/trang nguồn để truy lại một phần tử xác định; chỉ số này không có nghĩa là thứ tự đọc được provider bảo đảm. MIN-92 chốt kiểu ID/khóa chính thức. Mỗi `line_id` đã làm sạch/tách/gộp để parser đọc phải giữ tham chiếu ổn định tới **một hoặc nhiều** phần tử provider tương ứng. Không gắn hộp của một dòng provider cho dòng tổng hợp nếu quan hệ nguồn không còn đúng. Contract chỉ cho phép chữ, tọa độ provider, `geometry_status`, kích thước/ID khung và metadata transform an toàn; không xuất ảnh, URL/path ảnh, base64 hay toàn bộ payload provider. Tọa độ có mapping chưa xác minh vẫn được giữ nguyên như raw evidence, nhưng Document Intake chỉ dùng vị trí để đề xuất trường CCCD/GCN sau khi trạng thái khung đã đạt kiểm thử; nếu chưa thì chạy text-only. Bot không tự gán trường nghiệp vụ.

**Còn mở cho MIN-92 và các task consumer:** thời điểm tự gửi đề xuất OCR bổ sung so với thao tác bấm tay trên UI; cách đếm hạn mức khi một attachment có nhiều trang với `logical_id` riêng. Các con số và đơn vị trong bản nháp/plan là đề xuất, chưa là quota đã duyệt. Cần chốt cả hai trước khi viết client hoặc cơ chế đếm job.

Khi chưa biết số trang, processing_status có `page_index=null` và logical_id ở mức attachment. Sau tách trang, trang có logical_id riêng; record trạng thái attachment ghi `page_record_refs` liên kết chúng. Ảnh một trang dùng `page_index=1` ngay từ đầu. Consumer đếm ảnh theo attachment_id, trang theo page_index, không cộng status thành ảnh mới. Quy tắc chi tiết này cần MIN-92 chốt qua fixtures.

Với sửa/thu hồi/reaction adapter thực sự phát được, module ghi `source_event` riêng, liên kết tin đích và giờ bắt sự kiện; không dùng revision OCR để âm thầm sửa chữ cũ hoặc hồ sơ đã duyệt. MIN-92 phải chốt schema, ví dụ hợp lệ/không hợp lệ và quy tắc chống trùng cho `source_event` **trước khi** bật bàn giao loại này. Nếu adapter không phát được loại nào, bảng năng lực và trạng thái vận hành ghi rõ loại đó chưa hỗ trợ; không báo đã thu đủ. Lấy bù tin bot chưa từng nhận thuộc MIN-90.

`listener_session` ghi thay đổi trạng thái kết nối quan sát được; consumer ghép khoảng ngắt từ record `disconnected` đến `connected` kế tiếp để hiện cảnh báo buổi sáng. Nếu tiến trình hoặc máy chứa bot chết không kịp ghi ngắt kết nối, lần khởi động sau dùng heartbeat cuối để đánh dấu **khoảng có thể không nghe được**, không bịa thời điểm bắt đầu chính xác. Loại record này không đi vào parser giấy tờ hoặc phép nhóm hồ sơ. MIN-92 phải chốt ví dụ và cách ghép qua restart trước khi công bố giao diện.

## 6. Document Intake xử lý sau khi nhập raw

Sau khi raw đã lưu và ACK độc lập, Document Intake đọc các record hợp lệ, phân loại giấy tờ, bóc trường, ghép mặt giấy tờ/người/tài sản và gợi ý nhóm từ `captured_at` cùng dấu vết nguồn. Một tin có 10 ảnh không tự suy ra số người hoặc một hồ sơ. Mỗi giá trị ứng viên giữ ID record/trang/dòng nguồn; dữ liệu thiếu hoặc mâu thuẫn vẫn hiển thị để người dùng duyệt. Parser lỗi có thể chạy lại từ raw đã nhập mà không gọi Qwen hoặc yêu cầu bot gửi ảnh; mỗi lần xử lý tạo run/revision **nội bộ consumer**. Bản xử lý đến muộn không ghi đè dữ liệu người dùng đã xác nhận.

MarkItDown cho file upload thủ công là hướng tích hợp của Document Intake; bản `tools/document_conversion_poc` hiện là POC, chưa phải runtime chung. Nguồn MarkItDown và Zalo cần cùng một lớp biểu diễn chữ/đoạn/nguồn trước parser khi triển khai, nhưng không cần copy ảnh Zalo sang máy chính.

Phương án `intake.result.v1` do bot tạo ở bản nháp trước chỉ là **lịch sử đề xuất đã thay thế**. Không validator, ACK, UI hay task triển khai nào được giả định bot đã gửi person/property/group. Nếu sau này muốn chuyển nơi chạy parser, phải mở quyết định và contract version mới trước khi triển khai.

## 7. Chống nhập trùng và biên nhận

Khóa nguồn của ảnh/trang: `(provider, source_account_id, conversation_id, provider_message_id, attachment_id hoặc chỉ số ổn định, page_index)`. Message text dùng cùng khóa đến message ID và namespace `message_text`; tin có caption và ảnh giữ cả hai. Collector giữ map logical_id qua restart. Thiếu ID upstream thì cấp UUID cục bộ, ghi mức chắc chắn của identity; chưa khẳng định phát hiện đủ trùng khi nguồn thiếu ID.

Máy chính chống trùng theo `package_id + manifest_hash`, `record_id/revision` và logical_id/revision. Cùng package_id khác hash, cùng record_id khác nội dung hoặc cùng logical_id/revision khác nội dung là xung đột, không overwrite. Tin mới gửi ảnh giống vẫn là nguồn mới; không gộp theo hash ảnh hoặc chữ OCR. Feed sequence và `captured_at` không làm khóa nghiệp vụ.

Receipt đề xuất: `schema_version=intake.receipt.v1`, receipt_id, producer_id, consumer_id, package_id, manifest_sha256, record_count, status, imported_at và error nếu có. `accepted` nghĩa manifest, READY, records.jsonl và sổ nhập/database đã giữ an toàn; **không nói OCR thành công, parser đã chạy hoặc người dùng đã duyệt**. `rejected` nghĩa thiếu file, hash/schema/identity sai; module giữ pending và consumer quarantine.

ACK cùng ID/hash gửi lại trả cùng kết quả. Mất kết nối sau raw commit trước ACK: consumer phát lại ACK từ sổ, không nhập raw lần hai. Module nhận ACK rồi response thất lạc cũng trả accepted khi consumer gửi lại. Gói chỉ rời danh sách pending sau accepted hợp lệ; ACK không tự xóa raw trên module. Nếu parser lỗi sau ACK, consumer giữ raw và retry nội bộ; không yêu cầu bot gửi lại gói để sửa lỗi parser.

## 8. Ảnh và raw có thời hạn khác nhau

- Ảnh module: `image_expires_at=captured_at+168 giờ`. Dọn ảnh gốc, ảnh tách trang/dẫn xuất/cache đúng hạn, không chờ ACK; tải lại/OCR lại không kéo dài hạn.
- OCR chưa xong khi ảnh đến hạn: ngừng tác vụ cần ảnh đã hết hạn, dọn ảnh, công bố record trạng thái `source_image_expired`; không báo thành công hoặc giữ ảnh trái hạn. Chữ Qwen đã nhận trước đó vẫn được giữ.
- Raw/status/metadata chưa ACK: giữ qua restart và sau khi ảnh bị xóa; không xóa gói chưa giao để giải quyết đầy đĩa.
- Raw trên module sau ACK: **phải chốt thời hạn dọn hữu hạn và cách kiểm consumer đã lưu an toàn trong MIN-92 trước khi dùng dữ liệu thật**. Trong thử nghiệm chỉ dùng fixture giả thì chưa tự dọn để dễ kiểm; đó không phải chính sách vận hành và không cho phép giữ raw cá nhân vô hạn.
- Máy chính giữ bản gói file `imported/` để đối chiếu raw/status/hash khi lỗi, cùng raw nội bộ phục vụ parser/review. MIN-102 chốt thời hạn và giới hạn dung lượng cho từng bản theo chính sách máy chính; MIN-99 thực hiện. Không lấy thời hạn raw trên bot do MIN-92 chốt để tự dọn file máy chính; không có ảnh Zalo trong gói hoặc cache.

Việc xóa ảnh module không tác động dữ liệu của ứng dụng Zalo khác. Khôi phục ảnh/OCR sau hạn và soát bot bắt trượt thuộc issue fallback MIN-90.

## 9. Gate contract

Consumer chưa hỗ trợ major schema version thì quarantine và báo lỗi, không ACK accepted. Trường tùy chọn mới có thể được giữ/bỏ qua nếu không đổi nghĩa; field bắt buộc thay đổi phải đổi version. Record/file có giới hạn kích thước và định dạng, raw text không được thực thi như lệnh hoặc HTML.

MIN-92 phải duyệt và publish JSON Schema cùng fixtures hợp lệ/không hợp lệ, hash thật cho manifest, raw, READY và receipt trước implementation; gồm identity, revision, xác thực consumer/API, phục hồi sau reboot/file dở/ACK mất. Chốt request OCR: enum/tham số, hạn 168 giờ, hạn mức, idempotency, job/status, raw revision và lỗi tương ứng. Chốt `listener_session`/heartbeat và cảnh báo vùng có thể không nghe được. Chốt rõ `source_event` nếu adapter hỗ trợ sửa/thu hồi/reaction và cách consumer hiển thị cờ cần xem lại; không để callback đã nhận bị bỏ qua chỉ vì record kind chưa định nghĩa. **Không yêu cầu schema `results.json` từ producer.** Consumer sẽ có schema result/revision nội bộ riêng của Document Intake. Bản nháp này không phải validator hoàn chỉnh và không cấp phép triển khai code cùng task theo [quy định repo](../../../contracts/README.md).

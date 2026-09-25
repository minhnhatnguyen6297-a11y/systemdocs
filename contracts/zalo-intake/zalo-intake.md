# Contract: Zalo Intake `v1` — gói raw OCR và API bàn giao

**Version:** `v1` — các `schema_version` ở §3.1 · **Status:** DRAFT — chờ owner
duyệt trong MIN-92; sau duyệt publish sang `contracts/zalo-intake/` ·
**Hai bên:** module Zalo độc lập `zalo-intake` (**producer**) ↔ máy công chứng —
Document Intake trong Soạn hồ sơ (**consumer**) · **Linear:** MIN-92 ·
**Spec hành vi:** `notary_v2/docs/platform/zalo-document-inbox/spec.md`
(CAP-11…CAP-16)

Contract này mô tả **toàn bộ ranh giới trao đổi** giữa hai repo: gói file raw
(manifest/records/READY), feed pending + biên nhận ACK, API yêu cầu OCR bổ sung
có giới hạn, status endpoint và catalog mã lỗi. Nó không mô tả hành vi nội bộ
của một bên — parser, kết quả Document Intake, DB và UI của máy chính thuộc
MIN-102/MIN-96/MIN-99; listener, media và job của module thuộc MIN-94/95/97.

## 1. Trạng thái & phạm vi

- Đây là contract **file + API** có version. Mọi JSON document mang
  `schema_version` dạng `intake.*.v1`; mọi schema là JSON Schema draft 2020-12
  theo tập con ở §12.4.
- **Gói và mọi payload chỉ chứa text OCR, trạng thái và metadata nguồn. KHÔNG có
  ảnh, thumbnail, base64 ảnh, URL tải ảnh hay đường dẫn ảnh** — trong file gói,
  record, request, response hay log, kể cả dưới dạng trường tự do. Vi phạm là
  lỗi contract (`image_payload_forbidden`, `file_forbidden`,
  `request_forbidden_field`), không phải dữ liệu cần bỏ qua.
- Không có endpoint `/results`, không có endpoint lấy ảnh, không có
  `results.json` hay thực thể person/property/group đã xử lý. Module không phân
  loại giấy tờ, không chọn trường/ngày cấp, không quyết định nhóm hồ sơ.
- **Quan hệ với `contracts/entities.md`:** contract này không vận chuyển khóa
  định danh nghiệp vụ (CCCD, serial GCN, thửa/tờ, số công chứng). Việc trích
  xuất và chuẩn hóa các khóa đó diễn ra hoàn toàn ở consumer theo
  `entities.md`; producer chỉ giao chữ và provenance để consumer trích.
- Text trong gói là **dữ liệu**, không phải lệnh: consumer không thực thi
  HTML/lệnh và không tự tải URL xuất hiện trong chữ OCR.

**Những gì v1 không có (chủ đích, không phải thiếu sót):**

- Event `edit` (sửa tin): adapter zca-js 2.1.2 **không phát** loại này; chỉ có
  `undo` (thu hồi) và `reaction`. `/status` báo `edit: unsupported` — không hứa
  đã thu đủ.
- `geometry_status = present_mapping_verified`: **bị cấm** ở v1. Khung tọa độ
  provider sau resize/rotate chưa được kiểm chứng — UNVERIFIED (§6.4); việc
  kiểm chứng thuộc MIN-95/MIN-98.
- Multi-consumer: v1 đúng **một** consumer đã đăng ký; consumer khác bị
  `consumer_mismatch`/`unauthorized`.
- Lấy bù/đối chiếu tin bot chưa từng nhận: ngoài phạm vi, thuộc MIN-90.
- Không có khẳng định bot đã bắt đủ mọi tin trên Zalo: số record trong gói là
  số sự kiện module ghi nhận được, không suy ra tổng tin thật.

## 2. Vai trò & sở hữu

| Bên | Sở hữu |
|---|---|
| Module Zalo (`zalo-intake`, producer) | Listener zca-js, phiên đăng nhập Zalo, journal sự kiện bền vững, media tạm **168 giờ**, chuẩn bị/xoay/cắt ảnh, gọi Qwen OCR, trạng thái từng attachment/trang, đóng gói raw bất biến, API bàn giao (packages/receipts/status), API OCR bổ sung |
| Máy công chứng (consumer) | Sync/tải gói, kiểm chứng gói, lưu raw + sổ nhập bền vững, gửi ACK; **Document Intake**: regex, phân loại giấy, bóc trường, ghép mặt/người/tài sản, gợi ý nhóm, result/revision nội bộ, thẻ chờ người dùng duyệt; client gửi yêu cầu OCR bổ sung |
| Ranh giới | Chỉ raw text/OCR, trạng thái, ID nguồn, thời gian và thông tin kỹ thuật để kiểm/nhập lại an toàn. Không bên nào gọi parser, đọc DB, filesystem hay cookie của bên kia |

Quy tắc gốc:

- **ACK là biên nhận "raw package đã được lưu bền vững"** (đủ ba file + sổ
  nhập/database của consumer đã commit). ACK **không** có nghĩa OCR đã thành
  công, parser đã chạy hay người dùng đã duyệt nghiệp vụ.
- Mỗi attachment/trang module đã ghi nhận phải có **record chữ OCR hoặc record
  trạng thái** giải thích vì sao chưa có chữ. Lỗi một ảnh không làm mất các ảnh
  khác; không bịa chữ hay tọa độ.
- `producer.service`/`producer.build_id`, `account_id` và `consumer_id` ổn định
  qua restart; đăng nhập lại cùng tài khoản Zalo không đổi `account_id`.
- Tin mới gửi lại ảnh giống hệt vẫn là **nguồn mới**: không gộp record theo
  hash ảnh hay chữ OCR.

## 3. Gói raw (thư mục file)

### 3.1 Danh mục schema

Mỗi file schema nằm trong folder contract; `common.schema.json` chỉ chứa
`$defs` dùng chung (`$id` `zalo-intake:common:v1`), tham chiếu chéo bằng
`"common.schema.json#/$defs/<name>"`.

| File schema | `schema_version` | Document áp dụng |
|---|---|---|
| `manifest.schema.json` | `intake.raw-package.v1` | `manifest.json` trong gói |
| `raw-record.schema.json` | `intake.raw-record.v1` | mỗi dòng của `records.jsonl` |
| `ready.schema.json` | `intake.ready.v1` | `READY.json` trong gói |
| `receipt.schema.json` | `intake.receipt.v1` | body + response `POST /intake/v1/receipts` |
| `package-list.schema.json` | `intake.package-list.v1` | response `GET /intake/v1/packages` |
| `service-status.schema.json` | `intake.service-status.v1` | response `GET /intake/v1/status` |
| `ocr-request.schema.json` | `intake.ocr-request.v1` | body `POST /intake/v1/ocr-requests` |
| `ocr-request-status.schema.json` | `intake.ocr-request-status.v1` | response `POST` + `GET /intake/v1/ocr-requests/{request_id}` |
| `error.schema.json` | `intake.error.v1` | body lỗi của mọi endpoint (§10.2) |
| `common.schema.json` | — (chỉ `$defs`) | `uuid`, `iso_datetime`, `sha256_hex`, `nonempty_string`, `error_object` |

### 3.2 Cấu trúc gói & quy tắc file

Một gói raw là một thư mục bất biến gồm **đúng ba file**:

```text
<package_id>/
  manifest.json     # mô tả gói + hash payload
  records.jsonl     # raw records, một JSON object mỗi dòng
  READY.json        # dấu niêm phong, ràng buộc hash manifest
```

- Whitelist file gói: `manifest.json`, `records.jsonl`, `READY.json`.
  `receipt.json` **không** nằm trong gói — receipt là document API (§7.3).
  `results.json`, file ảnh/thumbnail, executable, script hay bất kỳ file nào
  ngoài whitelist → `file_unexpected`/`file_forbidden`.
- **Đóng gói:** producer ghi `records.jsonl` rồi `manifest.json` trong staging,
  flush xuống lưu trữ, ghi `READY.json` **sau cùng**, rồi công bố bằng đổi tên
  nguyên tử trên cùng filesystem. `READY.json` là chứng cứ "đã ghi xong" — nó
  không chứng minh bot bắt đủ tin, OCR thành công hay ai đã duyệt.
- **Path:** `files[].path` chỉ là basename an toàn trong thư mục gói. Chặn
  absolute path, `..`, junction/symlink thoát thư mục, alternate data stream
  và trùng tên chỉ khác hoa/thường trên Windows → `path_escape`.
- Consumer tải vào staging **riêng của consumer**, kiểm đủ file/hash/size/
  count/schema/identity rồi mới nhập; không đọc file đang tải dở như gói hoàn
  chỉnh; không phụ thuộc filesystem watcher hay mtime.

### 3.3 `manifest.json` — `intake.raw-package.v1`

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `schema_version` | const `"intake.raw-package.v1"` | |
| `package_id` | uuid | ID gói, bất biến, do producer cấp |
| `producer` | object `{service, build_id}` | `service` = `"zalo-intake"`; `build_id` nhận diện bản build producer |
| `consumer_id` | uuid | đúng consumer đã đăng ký; sai → `consumer_mismatch` |
| `created_at` | iso_datetime | giờ gói hoàn tất |
| `sequence` | int ≥ 1 | số thứ tự công bố — §7.1 |
| `files` | array `{path, sha256, bytes}`, `minItems: 1` | khai báo file payload; ở v1 **chỉ `records.jsonl` được khai** (manifest không tự hash mình; READY viết sau). `path` = basename an toàn (§3.2), `sha256` = sha256_hex trên byte gốc file, `bytes` = kích thước thật; sai → `manifest_hash_mismatch`/`size_mismatch`; khai tên khác → `file_forbidden` |
| `record_count` | int ≥ 0 | số dòng record thực tế trong `records.jsonl`; sai → `record_count_mismatch` |

### 3.4 `READY.json` — `intake.ready.v1`

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `schema_version` | const `"intake.ready.v1"` | |
| `package_id` | uuid | phải khớp `manifest.package_id` |
| `manifest_sha256` | sha256_hex | sha256 của **byte gốc** `manifest.json`; sai → `ready_hash_mismatch` |
| `sealed_at` | iso_datetime | giờ niêm phong gói |

### 3.5 Hash & canonical form

- **Hash file/payload:** sha256 hex lowercase trên **đúng byte gốc** của file —
  không parse rồi serialize lại. Áp dụng cho `files[].sha256`,
  `manifest_sha256`, `image_sha256`.
- **Canonical hash** (dùng cho nội dung record khi so trùng và cho body OCR
  request khi kiểm idempotency): sha256 hex của chuỗi JSON **đã canonical hóa
  kiểu Python** — `json.dumps(obj, sort_keys=True, separators=(",", ":"),
  ensure_ascii=False, allow_nan=False)` mã hóa UTF-8. Đây **KHÔNG phải** RFC
  8785/JCS: khác biệt escaping và định dạng số thực có thể xảy ra với
  canonicalizer khác; hai bên phải dùng đúng định nghĩa này.
- Mọi ID do contract định nghĩa (`package_id`, `record_id`, `logical_id`,
  `receipt_id`, `request_id`, `job_id`, `session_id`, `frame_id`, `line_id`,
  `consumer_id`, `account_id`, `attachment_id`) là **UUID canonical lowercase**
  8-4-4-4-12. `attachment_id` do module tự cấp — Zalo không cung cấp attachment
  ID — bắt buộc ổn định và duy nhất trong phạm vi tin. Riêng `ocr_pass_id` là
  chuỗi không rỗng do module tự cấp (không buộc dạng UUID).
- Mọi timestamp (`captured_at`, `source_sent_at`, `recorded_at`, `created_at`,
  `sealed_at`, `received_at`, `submitted_at`, `accepted_at`, `observed_at`,
  `image_expires_at`, `started_at`, `completed_at`, `finished_at`,
  `last_heartbeat_at`, `ended_at`) là ISO-8601/RFC 3339 **có offset bắt buộc**
  (`Z` hoặc `±HH:MM`, giây bắt buộc; naive time bị từ chối).

### 3.6 Giới hạn định lượng

| Đối tượng | Giới hạn |
|---|---|
| `records.jsonl` | ≤ 16 MiB, ≤ 1000 record/gói |
| `manifest.json`, `READY.json` | ≤ 64 KiB mỗi file |
| Receipt body, OCR request body | ≤ 16 KiB |
| `text_lines` mỗi record | ≤ 2000 dòng; mỗi dòng `text` ≤ 4096 ký tự |
| `ocr.attempts` mỗi record | ≤ 16 lượt |
| `provider_lines` mỗi attempt | ≤ 5000 phần tử |
| `processing_status.status.note`, `error_object.message`, `ocr-request.note` | ≤ 500 ký tự |
| `source.sender_display_name`, `listener.reason` | ≤ 200 ký tự |
| `event.reaction_icon` | 1–64 ký tự (bắt buộc khi `reaction`, cấm khi `recall`) |
| `transform_step.params` | object ≤ 24 key, chỉ giá trị scalar |
| `package-list.packages` mỗi trang | ≤ 100 |
| `sequence` | int ≥ 1 |

Vượt giới hạn transport → `size_limit_exceeded`/`request_too_large`; vượt giới
hạn trong record → `schema_invalid` theo schema.

## 4. Quy tắc byte & JSONL

Áp dụng cho **mọi document** trong contract (file gói, body API, fixtures):

- UTF-8 **không BOM**; UTF-8 lỗi hay BOM → `json_invalid`
  (`records_format_invalid` cho `records.jsonl`).
- Object key **duy nhất** trong từng object; key trùng → `json_invalid`.
- Không `NaN`/`Infinity` và không số thực không hữu hạn → `json_invalid`.
- JSON document đơn (`manifest.json`, `READY.json`, receipt, request, status):
  không có dữ liệu thừa sau giá trị JSON.

`records.jsonl` (JSON Lines) thêm:

- Mỗi dòng kết thúc `\n` — **kể cả dòng cuối**; thiếu newline cuối →
  `records_format_invalid`.
- Không chứa `\r` ở bất kỳ đâu → `records_format_invalid`.
- Không dòng rỗng; mỗi dòng là **đúng một** JSON object (không phải scalar/
  array/hai giá trị) → `records_format_invalid`.
- Bên trong một dòng, key trùng hoặc số không hữu hạn vẫn là `json_invalid`.
- File rỗng = gói không record (hợp lệ nếu `record_count` = 0).
- Byte-exact là yêu cầu bảo đảm hash: khi publish, fixtures phải được giữ ở
  dạng binary (`.gitattributes` `-text`) để `core.autocrlf` không viết lại
  `\r\n` làm hỏng hash.

## 5. Raw record

Mỗi dòng `records.jsonl` là một raw record `intake.raw-record.v1` — bất biến,
ghi một lần, không bao giờ sửa byte của phiên bản đã công bố. Mọi object trong
record tuân `additionalProperties: false`.

### 5.1 Envelope (mọi record)

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `schema_version` | const `"intake.raw-record.v1"` | |
| `record_kind` | enum | `message_text` · `ocr_page` · `processing_status` · `source_event` · `listener_session` |
| `record_id` | uuid | ID của **phiên bản record bất biến** này |
| `logical_id` | uuid | ID ổn định của đối tượng nguồn — scope theo kind (§5.3) |
| `revision` | int ≥ 1 | tăng liên tiếp từ 1 theo `logical_id` |
| `supersedes` | `{record_id: uuid, revision: int}`, optional | **bắt buộc** khi `revision ≥ 2` (`supersedes.revision = revision − 1`, trỏ record đã công bố trong `context.supersedes_targets`); **cấm ở `revision = 1`** — record đầu không có gì để thay thế. Vi phạm → `revision_chain_broken` |
| `captured_at` | iso_datetime | tin/ảnh: giờ bot **lần đầu** nhận tin; `source_event`/`listener_session`: giờ module quan sát sự kiện/chuyển trạng thái. Bất biến qua retry/revision; thiếu → `missing_captured_at` |
| `recorded_at` | iso_datetime | giờ phiên bản record này được ghi bền vững (revision mới → `recorded_at` mới) |
| `source` | object | khối nguồn — §5.2 |

**Bất biến qua revision:** record mới của cùng `logical_id` phải giữ nguyên
`captured_at`, `logical_id` và các khóa `source` (account, conversation,
message, attachment, page). Đổi một trong các trường đó ở revision mới →
`immutable_field_changed` (validator kiểm `captured_at` đối chiếu
`context.existing_revisions`). Cùng `record_id` khác canonical hash →
`record_conflict`; cùng `logical_id + revision` khác nội dung →
`source_revision_conflict`. Re-import cùng byte là no-op — không đụng byte cũ.

### 5.2 Khối `source`

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `provider` | const `"zalo_personal"` | nhà cung cấp nguồn |
| `account_id` | uuid | tài khoản Zalo văn phòng do module quản lý; ổn định qua restart/đăng nhập lại |
| `conversation_id` | string | `threadId` của hội thoại |
| `conversation_type` | enum `user` \| `group` | |
| `provider_message_id` | string, optional | `msgId` Zalo (fallback `cliMsgId` khi msgId trống) |
| `client_message_id` | string, optional | `cliMsgId` — **phải giữ**: event `recall`/`reaction` link về tin gốc bằng `globalMsgId`/`cliMsgId` (`cMsgID`) |
| `sender_id` | string, optional | `uidFrom` người gửi |
| `sender_display_name` | string ≤ 200, optional | tên hiển thị nếu có |
| `source_sent_at` | iso_datetime, optional | giờ Zalo báo đã gửi (`ts`, epoch ms → ISO); chỉ để đối chiếu, không thay `captured_at` |
| `attachment_id` | uuid, optional | **module tự cấp** (Zalo không cung cấp attachment ID); ổn định, duy nhất trong phạm vi tin |
| `attachment_index` | int ≥ 0, optional | vị trí 0-based trong các attachment được giữ (JPEG/PNG/PDF) |
| `page_index` | int ≥ 1, optional | **1-based**; ảnh đơn = `1`; trang PDF = `page_number` |

Trường không áp dụng theo `record_kind` mang giá trị `null` (không bịa). Với
`listener_session`, `source` chỉ mang `provider` + `account_id` — các trường
conversation/message/sender/attachment là `null` vì phiên listener ở scope
tài khoản, không gắn hội thoại.

### 5.3 Quan hệ `logical_id` ↔ attachment/trang

| `record_kind` | `logical_id` chỉ | Ghi chú |
|---|---|---|
| `message_text` | tin nhắn nguồn (scope `"msg"`) | một logical_id/tin; tin có cả text và ảnh giữ hai nhóm record riêng |
| `ocr_page` | **một trang** = attachment + `page_index` | khóa quota OCR bổ sung (§9.6) |
| `processing_status` | attachment (khi `page_index` null) hoặc trang | attachment-scope khi chưa tách trang; sau tách trang, trang có logical_id riêng |
| `source_event` | sự kiện nguồn (recall/reaction) | link tin đích qua `event.target_*` |
| `listener_session` | phiên listener (scope session) | **mỗi lần kết nối = một `session_id` + một `logical_id` mới** — reconnect sau crash/disconnect mở phiên mới (khoảng mất tin trước đó được phiên mới khai báo qua `uncertain_gap`, không phải revision của phiên cũ); không đi vào parser giấy tờ |

### 5.4 Body theo `record_kind`

**Loại trừ lẫn nhau:** body field của kind khác phải **vắng hoặc `null`** —
`message`/`ocr`/`status`/`event`/`listener`/`image_sha256`/`image_expires_at`/
`image_state` chỉ được mang non-null trên kind tương ứng bảng dưới. Vi phạm →
`kind_body_mismatch`.

**`message_text`** — `message: {text: string}`; các trường ảnh/`ocr` là `null`.

**`ocr_page`** — một trang ảnh đã OCR (thành công hoặc có trạng thái):

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `image_sha256` | sha256_hex | hash byte ảnh nguồn tại module — chỉ là định danh metadata, không phải ảnh |
| `image_expires_at` | iso_datetime | **đúng** `captured_at + 168 giờ`; sai → `expires_mismatch` |
| `image_state` | enum | `captured` · `retained` · `expired` · `missing` — §8.2 |
| `ocr` | object | `{status, attempts[], text_lines?, selected_pass_ids?}` — §6 |

**`processing_status`** — attachment/trang đã ghi nhận nhưng chưa có chữ OCR:

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `status` | object | `{code, note?}`; `code` ∈ `captured` · `media_missing` · `image_expired` · `ocr_partial` · `ocr_requested` · `note`; `note` ≤ 500 ký tự |

**`source_event`** — sự kiện adapter phát được, record riêng, **không** âm thầm
sửa record/hồ sơ cũ:

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `event` | object | `{event_type, target_provider_message_id, target_client_message_id?, observed_at, reaction_icon?}` |
| `event.event_type` | enum | `recall` · `reaction` (`edit` không có ở v1) |
| `event.target_provider_message_id` | string | `msgId`/`globalMsgId` của tin đích — **bắt buộc** theo rule (recall/reaction phải trỏ được tin gốc); thiếu → `source_event_invalid` |
| `event.target_client_message_id` | string, optional | `cliMsgId`/`cMsgID` của tin đích |
| `event.observed_at` | iso_datetime | giờ module quan sát event (= `captured_at` của record) |
| `event.reaction_icon` | string 1–64 ký tự | **bắt buộc khi `reaction`** (token icon Zalo, vd `:handclap`, `:>` hoặc emoji); **cấm khi `recall`**; vi phạm → `source_event_invalid` |

**`listener_session`** — mốc kết nối/ngắt/đăng nhập của listener, để consumer
đánh dấu khoảng **có thể không nghe được**:

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `listener` | object | `{session_id, state, observed_at, last_heartbeat_at?, reason?, uncertain_gap?}` |
| `listener.session_id` | uuid | ID phiên listener do module cấp |
| `listener.state` | enum | `connected` · `disconnected` · `login_required` |
| `listener.observed_at` | iso_datetime | giờ module quan sát chuyển trạng thái (= `captured_at`) |
| `listener.last_heartbeat_at` | iso_datetime, optional | heartbeat cuối biết được |
| `listener.reason` | string ≤ 200, optional | mã/lý do ngắn nếu biết |
| `listener.uncertain_gap` | `{started_at, ended_at, start_is_estimate: true}`, optional | **chỉ khi `state = connected`**; `started_at < ended_at` bắt buộc; đánh dấu khoảng có thể không nghe được sau crash — bắt đầu là ước lượng (heartbeat cuối), không khẳng định thiếu hay đủ tin; sai vị trí/shape → `listener_gap_invalid` |

Loại record này chỉ phục vụ cảnh báo vận hành; không đi vào parser giấy tờ hay
phép nhóm hồ sơ.

## 6. OCR & geometry

### 6.1 `ocr.status` — enum (record level và attempt level)

`succeeded` · `retry_pending` · `failed` · `source_image_expired` ·
`unsupported`.

- `succeeded`: ít nhất một attempt thành công và `text_lines` không rỗng.
- `retry_pending`: chưa có kết quả cuối, còn lượt retry trong hạn ảnh.
- `failed`: **không** attempt nào succeeded (hết retry/lỗi dứt điểm).
- `source_image_expired`: ảnh hết hạn 168 giờ trước khi OCR thành công.
- `unsupported`: loại attachment/định dạng module không OCR.

Ràng buộc nhất quán (vi phạm → `ocr_status_inconsistent`):
`status` = `succeeded` ⇒ `text_lines` ≠ ∅ **và** ≥ 1 attempt `succeeded`;
`status` = `failed` ⇒ không `text_lines` **và** không attempt `succeeded`;
`text_lines` ≠ ∅ ⇒ ≥ 1 attempt `succeeded`.

### 6.2 `ocr.attempts[]` — mỗi lượt gọi provider

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `ocr_pass_id` | nonempty string | ID lượt OCR do module cấp, duy nhất trong record; `text_lines[].ocr_pass_id` tham chiếu về đây; sai → `line_pass_ref_unknown` |
| `provider` | string | `"qwen"` ở v1 |
| `model` | string | vd `qwen-vl-ocr-2025-11-20` |
| `task` | enum `text_recognition` \| `advanced_recognition` | task `ocr_options` gửi provider |
| `image_operation` | enum | `original` · `rotate` · `crop_bottom` · `full_res` — thao tác ảnh của lượt |
| `region` | object `{kind, fraction?}` | `kind` ∈ `full_image` · `bottom_fraction`; `bottom_fraction` bắt buộc `fraction` number `0 < f < 1` |
| `submitted_frame` | object `{frame_id: uuid, width: int>0, height: int>0}` | khung ảnh **thực gửi** provider (sau mọi biến đổi phía module); bắt buộc khi có geometry |
| `transform_chain` | array `{op, params?}` | chuỗi biến đổi client-side từ ảnh nguồn tới `submitted_frame`; `op` ∈ `exif_transpose` · `resize` · `crop` · `rotate`; `params` optional — object ≤ 24 key, chỉ giá trị scalar (string/number/bool/null). Đây là **ngoại lệ duy nhất có chủ đích** của `additionalProperties:false` |
| `geometry_status` | enum | §6.4 |
| `provider_lines` | array, optional | verbatim các phần tử `words_info` provider trả — §6.5; ≤ 5000 |
| `status` | enum | như §6.1 |
| `error` | error_object, optional | `{code, message?, retryable?}` |
| `started_at` / `completed_at` | iso_datetime, optional | |
| `config_version` | string | version cấu hình OCR của module; nằm trong khóa dedupe (§9.5) |
| `request_id` | uuid, optional | ID yêu cầu OCR bổ sung sinh ra lượt này (§9) — **chỉ có trên attempt do request §9 tạo**, tức luôn nằm ở revision ≥ 2; attempt của pipeline capture-time không mang `request_id` |

Ràng buộc: `task = text_recognition` ⇒ `geometry_status = not_applicable` và
**không** `provider_lines`; `geometry_status = present_*` ⇒ có
`submitted_frame` và `provider_lines` không rỗng; vi phạm →
`geometry_frame_mismatch`/`geometry_invalid`.

### 6.3 Transcript mặc định `text_lines[]`

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `line_id` | uuid | ID dòng, ổn định; thiếu → `missing_line_id` |
| `text` | string | ≤ 4096 ký tự |
| `captured_at` | iso_datetime | kế thừa `captured_at` của record |
| `page_index` | int ≥ 1 | trang chứa dòng |
| `ocr_pass_id` | string | lượt OCR sinh dòng — phải tồn tại trong `attempts[]` |
| `region` | object, optional | vùng ảnh dòng thuộc về (cùng shape `region` của attempt) |
| `provider_refs` | array int ≥ 0, optional | `element_index` của các `provider_lines` nguồn trong **cùng attempt**; trỏ ngoài mảng → `provider_ref_unknown` |

**Quyết định owner:** `text_lines` (transcript mặc định) = lượt thành công của
**pipeline OCR mặc định lúc bắt ảnh**. Lượt OCR bổ sung chỉ thêm
`ocr.attempts[]` ở revision mới; `text_lines` và `selected_pass_ids` **không
đổi** chỉ vì có OCR bổ sung. `selected_pass_ids[]` liệt kê các `ocr_pass_id`
đóng góp vào transcript mặc định (nhiều lượt có thể cùng đóng góp). Document
Intake tự xét **mọi** attempt để chọn chứng cứ từng trường — producer không
quyết định trường nghiệp vụ. Thứ tự mảng là transcript mặc định, không khẳng
định thứ tự đọc do provider bảo đảm.

### 6.4 `geometry_status` — trạng thái vị trí dòng

Từ vựng contract có **5 giá trị**, nhưng schema v1 chỉ nhận **4 giá trị đầu**;
giá trị thứ năm `present_mapping_verified` là **reserved** — producer v1 CẤM
phát (schema từ chối → `schema_invalid`), chỉ được dùng sau khi MIN-95/98
kiểm chứng ánh xạ khung trên dữ liệu thật.

| Giá trị | Ý nghĩa |
|---|---|
| `not_applicable` | Task không trả geometry (`text_recognition`) — không có `provider_lines` |
| `absent` | Task có thể trả geometry (`advanced_recognition`) nhưng provider không trả/thiếu dữ liệu |
| `present_unverified` | Provider trả `location`/`rotate_rect` hợp lệ hình thức, nhưng **khung tọa độ và phép ánh xạ về ảnh nguồn chưa được kiểm chứng** — giá trị mặc định cho dữ liệu có vị trí ở v1 |
| `present_invalid` | Provider trả geometry nhưng vi phạm shape (location ≠ 8 số hữu hạn, rotate_rect ≠ 5 phần tử…) — giữ làm evidence, không dùng |
| `present_mapping_verified` | **RESERVED — không có trong enum v1.** Phép ánh xạ khung đã kiểm chứng trên dữ liệu thật; chỉ sau khi MIN-95/98 kiểm chứng, và việc cho phép phát là một thay đổi contract (§13) |

**UNVERIFIED:** tài liệu provider mô tả `location` là tọa độ tuyệt đối trên
"ảnh gốc" (gốc trên-trái, đỉnh theo thứ tự TL→TR→BR→BL) nhưng **không nói rõ**
"ảnh gốc" là khung nào sau khi dịch vụ tự resize theo `min_pixels`/`max_pixels`
hoặc tự xoay khi `enable_rotate=true`. Vì vậy:

- Producer giữ nguyên `provider_lines` như raw evidence kèm `submitted_frame` +
  `transform_chain` để lần kiểm chứng sau có đủ dữ kiện.
- Consumer chỉ được suy bố cục/vị trí khi `present_mapping_verified`; mọi giá
  trị khác → **text-only fallback hợp lệ** (đọc chữ, không suy vị trí, đánh dấu
  trường mơ hồ cho người dùng).
- `rotate_rect` `[cx, cy, w, h, deg]` với `deg ∈ [-90, 90]` chỉ theo ví dụ tài
  liệu — UNVERIFIED chính thức; kiểu số int/float không nói → schema nhận
  `number` hữu hạn.
- Không giả định `words_info` có thứ tự đọc, số trang, confidence hay tọa độ
  từng ký tự; không tự tạo tọa độ toàn ảnh từ crop hay quy ước đơn vị/góc mà
  tài liệu không ghi.

### 6.5 `provider_lines[]` — verbatim provider

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `element_index` | int ≥ 0 | **module gán** = vị trí phần tử trong mảng `words_info` của đúng lượt; chỉ giữ provenance, **không** phải thứ tự đọc |
| `text` | string | chữ provider trả cho dòng đó |
| `location` | array 8 số hữu hạn, optional | `[x1,y1,x2,y2,x3,y3,x4,y4]` — 4 đỉnh TL→TR→BR→BL; sai → `geometry_invalid` |
| `rotate_rect` | array 5 số hoặc `null`, optional | `[cx, cy, w, h, deg]`; sai → `geometry_invalid` |

`provider_lines` giữ **nguyên giá trị** provider trả (text + tọa độ). Module
không sửa/chuẩn hóa tọa độ, không suy thêm khung mới. Tuyệt đối **không dump
toàn bộ provider payload thô** (response JSON nguyên dạng, usage, header,
ẢNH base64 nếu có) vào record → `provider_payload_forbidden`/
`image_payload_forbidden`.

## 7. Sequence, pending & ACK

### 7.1 `sequence`

- `sequence` là số nguyên ≥ 1 do **producer** cấp theo thứ tự công bố gói,
  tăng liên tục, bền vững qua restart, trong phạm vi một cặp
  producer/consumer. Đóng gói thất bại trước công bố không được để lộ gap.
- `sequence` **không** phải số tin nhắn Zalo và không suy từ `captured_at`;
  gói OCR xong muộn hay revision mới vẫn nhận `sequence` mới.
- Trùng/lùi/gap so với kỳ vọng → `sequence_invalid`; cùng `package_id` khác
  `manifest_sha256` → `package_conflict`; tham chiếu `package_id` không tồn
  tại → `package_unknown`.

### 7.2 Feed pending & một lượt Sync

Gói nằm trong feed `delivery=pending` cho tới khi có receipt `accepted` hợp
lệ; receipt `rejected` **không** rút gói khỏi pending.

| Endpoint | Nghĩa |
|---|---|
| `GET /intake/v1/packages?delivery=pending&after=<seq>&limit=<n>` | Liệt kê gói chưa ACK theo `sequence` tăng; `limit` ≤ 100; response `intake.package-list.v1` |
| `GET /intake/v1/packages/{package_id}/manifest` | Byte gốc `manifest.json` |
| `GET /intake/v1/packages/{package_id}/records` | Byte gốc `records.jsonl` |
| `GET /intake/v1/packages/{package_id}/ready` | Byte gốc `READY.json` |

`package-list` response:

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `schema_version` | const `"intake.package-list.v1"` | |
| `packages` | array `{package_id: uuid, sequence: int, manifest_sha256: sha256_hex}` | theo `sequence` tăng |
| `next_after` | int ≥ 0 | cursor trang kế: truyền làm `after` ở request sau |
| `until_sequence` | int ≥ 0 | mốc trên của lượt Sync — gói công bố sau mốc này thuộc lượt sau; `0` khi không có pending |
| `has_more` | bool | còn trang trong cùng `until_sequence` |

Một lượt Sync:

1. `after=0` (và không truyền `until_sequence`) ở trang đầu — server chốt
   `until_sequence` = `sequence` cao nhất pending tại thời điểm đó và trả trong
   response.
2. Trang tiếp: `after` = `next_after` của trang trước, **giữ nguyên**
   `until_sequence`; lặp tới `has_more = false`.
3. `after` chỉ là cursor phân trang — **không phải ACK**. ACK gói trang trước
   trong lúc phân trang không làm bỏ sót gói trang sau.
4. Consumer ghi bền vững danh sách `package_id`/`manifest_sha256` cần nhận
   trước khi chuyển trang. Gói tải lỗi vẫn pending; lượt Sync sau quét lại từ
   `after=0` nên gói cũ tải lỗi không mất.
5. Trigger Sync: backend khởi động, mạng nối lại, chu kỳ cấu hình, nút
   **Sync** — một lượt active tại một thời điểm; nút Sync không gọi lịch sử
   Zalo và không phát yêu cầu OCR.

### 7.3 Receipt — `POST /intake/v1/receipts`

Body và response đều là `intake.receipt.v1`:

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `schema_version` | const `"intake.receipt.v1"` | |
| `receipt_id` | uuid | ID biên nhận do consumer cấp — khóa idempotent |
| `package_id` | uuid | gói được nhận; không tồn tại → `package_unknown` |
| `consumer_id` | uuid | phải khớp `manifest.consumer_id`; sai → `receipt_consumer_mismatch` |
| `status` | enum `accepted` \| `rejected` | quyết định của consumer |
| `received_at` | iso_datetime | giờ consumer phát biên nhận |
| `manifest_sha256` | sha256_hex | hash manifest mà consumer đã kiểm; khác gói → `receipt_hash_mismatch` |
| `record_count` | int ≥ 0 | số record consumer đã nhập; khác manifest → `receipt_count_mismatch` |
| `error` | error_object | **bắt buộc khi `rejected`, cấm khi `accepted`** (schema if/then/else → `schema_invalid`) |

- Consumer chỉ gửi `accepted` **sau khi** ba file gói + sổ nhập/database đã
  commit bền vững — không chờ parser hay người dùng duyệt (§2).
- `rejected` = thiếu file, hash/schema/identity sai; consumer quarantine gói
  kèm lý do, gói vẫn pending ở producer.
- **Idempotent:** cùng `receipt_id` → producer trả cùng quyết định đã lưu, kể
  cả khi response trước thất lạc; consumer phát lại ACK sau crash mà không
  nhập raw lần hai.
- Producer lưu quyết định receipt bền vững; gói chỉ rời pending sau
  `accepted` hợp lệ. ACK không xóa raw trên module (retention §8).
- Re-import cùng byte là no-op; khác byte cùng khóa (`package_id`,
  `record_id`, `logical_id+revision`) → conflict tương ứng — không overwrite.

## 8. Retention — hai thời hạn tách biệt

### 8.1 Ảnh tại module — 168 giờ, không chờ ACK

- `image_expires_at = captured_at + 168 giờ` (tính chính xác tới giây). Áp
  dụng cho ảnh gốc, ảnh tách trang/dẫn xuất và cache của module.
- Module tự xóa đúng hạn **kể cả khi gói chưa ACK**; tải lại hay OCR lại
  không kéo dài hạn.
- OCR còn dở khi ảnh hết hạn: ngừng tác vụ cần ảnh, dọn ảnh, công bố record
  trạng thái `source_image_expired`; chữ Qwen đã nhận trước đó giữ nguyên;
  không báo thành công giả.
- Xóa ảnh **không** xóa gói raw, record hay sổ chờ ACK.

### 8.2 `image_state` trong record `ocr_page`

| Giá trị | Ý nghĩa tại thời điểm ghi record |
|---|---|
| `captured` | ảnh nguồn đã được module tải/lưu tại nơi giữ |
| `retained` | ảnh còn được giữ trong hạn 168 giờ (gồm bản cần cho OCR bổ sung) |
| `expired` | ảnh đã bị dọn đúng hạn `captured_at + 168 giờ` |
| `missing` | file ảnh mất/lỗi **trước** hạn — khác `expired` |

### 8.3 Raw package trên module sau ACK — chính sách đã chốt

- Giữ **30 ngày** tính từ receipt `accepted`.
- Trần tổng **1 GiB** cho phần gói đã ACK; cảnh báo khi dùng ≥ **80%**
  (`status.storage.ack_warn`, §10.1).
- Chạm trần: chỉ dọn sớm các gói **đã ACK** cũ nhất.
- **Không bao giờ** xóa gói chưa ACK — kể cả khi đầy đĩa hay ảnh đã hết hạn;
  thiếu dung lượng là lỗi vận hành phải báo, không giải quyết bằng xóa gói.
- Chính sách giữ bản `imported/` và raw nội bộ tại **máy chính** là quyết
  định consumer — MIN-102 chốt, MIN-99 thực hiện. Contract này không áp TTL
  của bot lên file máy chính, và máy chính không dùng retention bot làm lý do
  xóa raw đang cần để replay.

## 9. API yêu cầu OCR bổ sung — `intake.ocr-request.v1`

Document Intake gửi khi quy tắc của nó đề xuất đọc lại một trang (tự động từ
backend hoặc nút tay theo quyền — chính sách consumer, API như nhau). **Một
request = một variant** cho một `logical_id` (một trang).

### 9.1 Endpoints & auth

| Endpoint | Nghĩa |
|---|---|
| `POST /intake/v1/ocr-requests` | Tạo yêu cầu; response `intake.ocr-request-status.v1` |
| `GET /intake/v1/ocr-requests/{request_id}` | Đọc lại trạng thái qua restart; response cùng schema |

- Auth: `Authorization: Bearer <token>` theo consumer — v1 đúng một consumer;
  token cấu hình trong backend máy chính, không nằm trong gói/log/URL.
- Chạy local: chỉ bind loopback (`127.0.0.1`/`::1`); qua mạng LAN/server:
  bắt buộc HTTPS.

### 9.2 Request body (≤ 16 KiB)

Bắt buộc: `schema_version`, `request_id`, `consumer_id`, `logical_id`,
`variant`, `reason_code`, `observed_revision`, `submitted_at`.
Optional: `preset`, `note`.

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `schema_version` | const `"intake.ocr-request.v1"` | |
| `request_id` | uuid | consumer cấp — khóa idempotency |
| `consumer_id` | uuid | phải khớp consumer xác thực |
| `logical_id` | uuid | trang/ảnh **đã bàn giao** qua gói raw — khóa quota; sai phạm vi → `unknown_source` |
| `observed_revision` | int ≥ 1 | revision mới nhất consumer đã phân tích; producer có revision mới hơn → `stale_revision` (consumer Sync/parse lại trước) |
| `variant` | enum | `rotate` · `crop_bottom` · `full_res` — một variant/request; giá trị lạ → `unsupported_variant` |
| `preset` | string \| null, optional | bắt buộc/cho phép theo variant — bảng dưới |
| `reason_code` | enum | §9.7 |
| `note` | string ≤ 500, optional | text tự do cho journal vận hành — vẫn bị quét `request_forbidden_field` |
| `submitted_at` | iso_datetime | giờ consumer phát yêu cầu |

| `variant` | `preset` |
|---|---|
| `crop_bottom` | **bắt buộc**: `bottom_quarter` · `bottom_third` · `bottom_42pct` — thiếu → `missing_preset`; sai → `unsupported_variant`. Producer suy ra vùng đọc tương ứng `bottom_fraction` ≈ 0.25 / ⅓ / 0.42 — consumer **không gửi `region` tự do** (không tồn tại trong schema; chỉ `variant`+`preset` quyết định vùng) |
| `rotate` | `auto` (provider `enable_rotate=true`), `null` hoặc vắng — không có góc client |
| `full_res` | `null` hoặc vắng — đọc lại ở độ phân giải đầy đủ trong giới hạn provider |

**Cấm trong request** (quét đệ quy ở mọi depth → `request_forbidden_field`):
key chứa phân đoạn `image`, `base64`, `url`, `uri`, `href`, `link`, `path`,
`file`, `prompt`, `token`, `secret`, `key`, `password`, `credential`, `data`,
`payload`, `blob`, `bytes`; value chứa `data:` URI, token kết thúc bằng phần
mở rộng ảnh (URL/path/tên file), chuỗi base64 ≥ 256 ký tự. Nói cách khác:
không byte ảnh/base64, không URL, không đường dẫn, không prompt hay lệnh
provider tùy ý, không secret — body chỉ là ID + tham số khép kín (body quá
16 KiB → `request_too_large`).

### 9.3 Kiểm lúc accept — pipeline theo thứ tự

Stage đầu tiên sinh mã lỗi là câu trả lời; trong một stage, các check độc lập
có thể trả **nhiều mã cùng lúc** (vd body vừa sai schema vừa chứa key cấm →
`{schema_invalid, request_forbidden_field}`):

1. **Auth** consumer → `unauthorized`.
2. **Screening** (ba góc nhìn độc lập trên cùng byte, hợp kết quả):
   schema (kèm `x-error-code` `unsupported_variant`/`missing_preset`/
   `schema_invalid`) · size > 16 KiB → `request_too_large` · quét field cấm →
   `request_forbidden_field`.
3. **Nguồn:** `logical_id` không có trong phạm vi consumer → `unknown_source`;
   nguồn chưa bật → `source_not_enabled`.
4. **Idempotent replay:** `request_id` đã có — cùng canonical body → trả lại
   quyết định đã lưu (không kiểm tiếp, kể cả khi ảnh đã hết hạn); khác body →
   `request_conflict`.
5. **Dedupe:** job cùng `(logical_id, variant, preset, config_version)` đang
   `queued`/`running`/`completed` → trả job cũ, không tốn ngân sách.
6. **Revision:** `observed_revision` < `current_revision` → `stale_revision`.
7. **Hạn & tồn tại ảnh:** `now ≥ captured_at + 168h` → `source_image_expired`
   (kiểm trước); file ảnh không đọc được → `source_image_unavailable`.
8. **Ngân sách** (các giới hạn độc lập, báo đủ): `key_jobs ≥ 2` →
   `budget_exceeded`; `day_calls ≥ 100` → `rate_limited`; `concurrent ≥ 2` →
   `rate_limited`.
9. **Tạo job** — ghi bền vững trước khi phản hồi, trả `queued`/`running`;
   việc nhận job không nghĩa Qwen đã xong.

Vì replay/dedupe (bước 4–5) đứng **trước** kiểm hạn và quota: request lặp lại
đúng nội dung hay trùng job cũ không bị từ chối chỉ vì ảnh đã quá hạn, và
không tốn lượt gọi mới.

**Kiểm hạn hai lần:** tại bước accept **và** ngay trước khi worker đọc ảnh/gọi
Qwen; ảnh hết hạn giữa chừng → job `failed` + công bố raw revision trạng thái
(§9.5). Không có cơ chế kéo dài hạn ảnh, không tải lại ảnh để gia hạn.

### 9.4 Idempotency & dedupe

- Cùng `request_id` + cùng canonical body (§3.5) → trả **cùng job/trạng
  thái**, không gọi Qwen lần hai — kể cả sau restart.
- Cùng `request_id` khác body → `request_conflict`.
- Đã có job cùng khóa **`(logical_id, variant, preset, config_version)`** ở
  trạng thái `queued`/`running`/`completed` → trả job đã có (dedupe theo nội
  dung, kể cả `request_id` khác; response đánh dấu `deduplicated: true`).
  `config_version` là cấu hình OCR **hiện hành của producer** — không phải
  trường trong request body (body đóng). Job `failed`/`rejected` không chặn
  request mới nhưng request mới vẫn tính ngân sách.
- Chỉ một job đang chạy cho một `logical_id`.

### 9.5 Kết quả đi qua gói raw — không trả text trong response

- Request **bị từ chối trước khi chạy** (auth/revision/hạn/quota…): chỉ
  lưu + trả trạng thái bền vững theo `request_id` (`state = rejected` +
  `error` + `finished_at`), **không** tạo gói raw giả.
- Job **đã nhận** xong (thành công hoặc lỗi Qwen/file/hết hạn trong lúc
  chạy): producer công bố **gói raw mới** (`package_id` + `sequence` mới)
  chứa **revision mới** của cùng `logical_id` — giữ nguyên `captured_at` và
  khóa `source`, `supersedes` trỏ revision trước, `ocr.attempts[]` thêm lượt
  mới kèm `request_id`; `text_lines`/`selected_pass_ids` transcript mặc định
  không đổi chỉ vì OCR bổ sung (§6.3). Qwen lỗi → `provider_failed`, gói mang
  record trạng thái lỗi — không xóa chữ cũ, không bịa chữ thành công.
- `POST`/`GET` chỉ trả **trạng thái + ID**, tuyệt đối không trả chữ OCR —
  consumer nhận kết quả qua feed pending/ACK như gói thường.

`intake.ocr-request-status.v1` response — bắt buộc: `schema_version`,
`request_id`, `job_id`, `state`, `attempt`, `max_attempts`:

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `schema_version` | const `"intake.ocr-request-status.v1"` | |
| `request_id` | uuid | echo khóa idempotency |
| `job_id` | uuid | ID job do producer cấp — **có cả với request bị reject trước khi chạy** (ledger gán ID lúc intake) |
| `state` | enum | `queued` · `running` · `completed` · `rejected` · `failed` |
| `attempt` | int ≥ 0 | số lần đã thử gọi provider (0 khi chưa chạy) |
| `max_attempts` | int ≥ 1 | trần retry của job — **≤ 3**; `attempt ≤ max_attempts`; vi phạm → `status_invalid` |
| `accepted_at` | iso_datetime, optional | giờ producer nhận yêu cầu |
| `started_at` | iso_datetime, optional | giờ job bắt đầu chạy |
| `finished_at` | iso_datetime, optional | giờ job kết thúc |
| `result` | `{package_id, manifest_sha256, new_revision}`, optional | **bắt buộc khi `completed`, cấm ở state khác**; `package_id` phải là gói đã publish cho consumer này → sai `package_reference_invalid`; vi phạm điều kiện → `status_invalid` |
| `error` | error_object, optional | **bắt buộc khi `rejected`/`failed`, cấm ở state khác** (vd `error.code = provider_failed`, `source_image_expired`); vi phạm → `status_invalid` |
| `deduplicated` | bool, optional | `true` khi producer trả job đã có (replay hay trùng khóa dedupe) — không tốn ngân sách mới |

### 9.6 Ngân sách (quota) — đã chốt

Ba giới hạn độc lập, báo đủ mã vi phạm:

- **Khóa quota = `logical_id` (từng trang).** `key_jobs` = số job OCR bổ sung
  đã tiêu trên khóa trong toàn hạn 168 giờ; `key_jobs ≥ 2` →
  **`budget_exceeded`** (hết hạn mức vòng đời — không retry được trên cùng
  khóa).
- **100 lượt gọi Qwen/consumer/24 giờ** — cửa sổ trượt; `day_calls ≥ 100` →
  **`rate_limited`** (giới hạn tạm, retry sau khi cửa sổ nhả).
- **2 job đồng thời** toàn module; `concurrent ≥ 2` → **`rate_limited`**.
- **Retry lỗi provider ≤ 3 lần/job** (`attempt ≤ max_attempts ≤ 3`) có
  backoff, trong cùng job — không tạo job mới để lách hạn mức.
- Lượt **timeout hoặc không rõ provider đã nhận** vẫn tính vào ngân sách.
- Ảnh hết hạn 168 giờ tính từ `captured_at` dù job đã xếp hàng — không gia
  hạn bằng retry.
- Request trúng replay/dedupe (§9.4) trả về job cũ **không** tốn lượt gọi.

### 9.7 `reason_code` — catalog lý do consumer gửi

| Mã | Ý nghĩa |
|---|---|
| `missing_issue_date` | thiếu/mờ ngày cấp (vd chân GCN) |
| `missing_identity_number` | thiếu số định danh/CCCD |
| `missing_parcel_info` | thiếu thửa/tờ/địa phương |
| `suspected_rotation` | nghi ảnh bị xoay — gợi ý `variant = rotate` |
| `insufficient_text` | quá ít chữ để phân tích |
| `truncated_footer` | nghi mất vùng chân trang — gợi ý `crop_bottom` |
| `other` | lý do khác |

## 10. Status endpoint & error envelope

### 10.1 `GET /intake/v1/status` — `intake.service-status.v1`

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `schema_version` | const `"intake.service-status.v1"` | |
| `producer` | `{service, build_id}` | `service` = `"zalo-intake"` |
| `observed_at` | iso_datetime | giờ quan sát tại module |
| `listener` | `{state, last_heartbeat_at?, session_id?}` | `state` ∈ `connected` · `disconnected` · `login_required` |
| `pending` | `{packages: int, oldest_sequence?: int, oldest_age_seconds?: int}` | số gói chưa ACK + độ già gói cũ nhất; hai trường `oldest_*` **đi theo cặp** — `packages = 0` ⇒ cấm cả hai, `packages > 0` ⇒ bắt buộc cả hai (sai → `status_invalid`) |
| `storage` | `{ack_bytes: int, ack_cap_bytes: int, ack_warn: bool}` | dung lượng gói đã ACK / trần 1 GiB / `ack_warn` = true **đúng khi** `5·ack_bytes ≥ 4·ack_cap_bytes` (≥ 80%, so sánh nguyên); sai → `status_invalid` |
| `capabilities` | `{source_event_types: {recall, reaction, edit}}` | mỗi loại `supported` \| `unsupported` |

`capabilities.source_event_types` báo **loại sự kiện adapter phát được thật**:
với zca-js 2.1.2 → `recall: supported` (event `undo`), `reaction: supported`,
`edit: unsupported`. Loại chưa hỗ trợ phải báo `unsupported` — không được báo
đã thu đủ. Document sai shape → `status_invalid`.

### 10.2 Error envelope — `intake.error.v1`

Mọi lỗi HTTP của API trả body:

```json
{"schema_version": "intake.error.v1", "error": {"code": "…", "message": "…", "retryable": true}}
```

- `error.code`: bắt buộc, `^[a-z0-9_]+$`, ≤ 64 ký tự, thuộc catalog §11.
- `error.message`: optional, ≤ 500 ký tự, cho người đọc — không chứa secret,
  path ảnh hay payload PII.
- `error.retryable`: optional bool — gợi ý consumer có nên thử lại (vd
  `rate_limited` retryable sau khi cửa sổ nhả; `budget_exceeded` chỉ sau khi
  ngân sách reset).
- HTTP status tương ứng loại lỗi (401 auth, 404 unknown, 409 conflict,
  429 rate limit, 400 validation…); **body luôn là envelope này** — không trả
  lỗi dạng text/HTML tùy ý.

## 11. Catalog mã lỗi

Mã ổn định, là một phần contract — mọi code xuất hiện trong validator và
fixtures. `json_invalid`/`records_format_invalid`/`schema_invalid` do tầng
byte/schema phát; các mã còn lại do rule tương ứng.

### 11.1 Framework

| Mã | Ý nghĩa | Xử lý |
|---|---|---|
| `json_invalid` | Document không parse được theo strict profile: BOM, UTF-8 lỗi, key trùng, NaN/Infinity, dữ liệu thừa | Consumer: reject gói/document; không sửa tay |
| `records_format_invalid` | `records.jsonl` vi phạm framing: `\r`, thiếu `\n` cuối, dòng rỗng, dòng không phải đúng một object | Consumer: reject gói |
| `schema_invalid` | Document không khớp JSON Schema của `schema_version` | Consumer: reject/quarantine; producer: lỗi lập trình phía mình |

### 11.2 Gói & transport (phía consumer kiểm trừ khi ghi khác)

| Mã | Ý nghĩa |
|---|---|
| `file_missing` | thiếu file bắt buộc trong whitelist |
| `file_unexpected` | file ngoài whitelist ba file (kể cả `records.jsonl` trên đĩa không được khai trong `manifest.files[]`, entry lạ trong case `package_sequence`) |
| `file_forbidden` | file bị cấm: `results.json`/`receipt.json` (payload protocol), ext ảnh/thumbnail, ext executable/script, thư mục con, tên chỉ gồm `.`/chứa `..`, tên khác-hoa/thường của 3 file gói, `files[]` khai tên khác `records.jsonl` |
| `path_escape` | `files[].path` thoát thư mục gói (absolute, `..`, junction/symlink, ADS, trùng tên khác hoa/thường) |
| `manifest_hash_mismatch` | sha256(`records.jsonl`) ≠ `files[].sha256` khai trong manifest |
| `ready_hash_mismatch` | sha256(`manifest.json`) ≠ `READY.manifest_sha256`, **hoặc** `READY.package_id` ≠ `manifest.package_id` (cùng lỗi gãy binding READY↔manifest) |
| `size_mismatch` | byte file ≠ `files[].bytes` |
| `size_limit_exceeded` | vượt giới hạn §3.6 (16 MiB/64 KiB/16 KiB) |
| `record_count_mismatch` | số dòng `records.jsonl` ≠ `record_count` |
| `consumer_mismatch` | `manifest.consumer_id` ≠ consumer đã đăng ký |
| `producer_mismatch` | khối `producer` không khớp producer đã đăng ký |
| `sequence_invalid` | `sequence` trùng/lùi/gap so với kỳ vọng |
| `package_conflict` | cùng `package_id` khác `manifest_sha256` — không overwrite, báo xung đột |
| `package_unknown` | tham chiếu `package_id` producer không có |
| `receipt_consumer_mismatch` | `receipt.consumer_id` ≠ consumer của gói (producer từ chối) |
| `receipt_hash_mismatch` | `receipt.manifest_sha256` ≠ hash gói (producer từ chối) |
| `receipt_count_mismatch` | `receipt.record_count` ≠ `record_count` gói (producer từ chối) |
| `status_invalid` | document `service-status`/`ocr-request-status` vi phạm rule nhất quán trạng thái (ack_warn, oldest_* pair, result/error theo state, attempt ≤ max_attempts ≤ 3) |

### 11.3 Raw record

| Mã | Ý nghĩa |
|---|---|
| `record_conflict` | cùng `record_id` khác canonical hash — không overwrite |
| `source_revision_conflict` | cùng `logical_id` + `revision` khác nội dung |
| `revision_chain_broken` | `supersedes` trỏ sai target / `supersedes.revision` ≠ `revision−1` / thiếu `supersedes` khi `revision ≥ 2` / **có `supersedes` ở `revision = 1`** |
| `missing_captured_at` | thiếu `captured_at` |
| `missing_line_id` | dòng `text_lines` có text mà thiếu `line_id` |
| `expires_mismatch` | `image_expires_at` ≠ `captured_at + 168 giờ` |
| `immutable_field_changed` | revision mới đổi `captured_at`/`logical_id`/khóa `source` |
| `line_pass_ref_unknown` | `text_lines[].ocr_pass_id` **hoặc** `selected_pass_ids[]` trỏ `ocr_pass_id` không có trong `attempts[]` |
| `provider_ref_unknown` | `provider_refs[]` trỏ `element_index` ngoài `provider_lines` |
| `geometry_invalid` | `location` ≠ 8 số hữu hạn / `rotate_rect` ≠ 5 phần tử; **hoặc** `geometry_status` ∈ `absent`/`not_applicable` mà attempt vẫn mang `provider_lines` không rỗng |
| `geometry_frame_mismatch` | `geometry_status` = `present_*` nhưng thiếu `submitted_frame`/`provider_lines` |
| `ocr_status_inconsistent` | `succeeded` mà `text_lines` rỗng/vắng hoặc không attempt nào succeeded; `failed` mà có `text_lines` hay attempt succeeded; có `text_lines` mà không attempt succeeded |
| `image_payload_forbidden` | record chứa `data:image`, URL/path kết thúc ext ảnh/tài liệu (`.jpg` `.jpeg` `.png` `.webp` `.pdf`), blob base64 ≥ 128 ký tự |
| `provider_payload_forbidden` | key `provider_raw`/`provider_response`/`raw_response` ở bất kỳ depth — cấm dump provider payload thô vào record |
| `listener_gap_invalid` | `uncertain_gap` sai: khi `state` ≠ `connected`, `start_is_estimate` ≠ true, `started_at ≥ ended_at`; hoặc gap quan sát ≠ `context.expected_gaps` |
| `kind_body_mismatch` | record mang non-null body field của kind khác (§5.4 — body field loại trừ lẫn nhau) |
| `source_event_invalid` | thiếu `target_provider_message_id`; `reaction_icon` thiếu/ngoài 1–64 ký tự khi `reaction`, hoặc có khi `recall` |

### 11.4 OCR request (phía producer kiểm/trả)

| Mã | Ý nghĩa |
|---|---|
| `unauthorized` | thiếu/sai bearer; consumer không có quyền trên nguồn |
| `unknown_source` | `logical_id` không tồn tại / không thuộc consumer |
| `source_not_enabled` | nguồn chứa `logical_id` chưa bật theo chính sách |
| `unsupported_variant` | `variant` lạ, hoặc `preset` không hợp cho variant đó |
| `missing_preset` | `variant` bắt buộc `preset` (crop_bottom) mà thiếu |
| `stale_revision` | `observed_revision` cũ hơn revision hiện có — consumer Sync/parse lại trước |
| `source_image_expired` | `now ≥ image_expires_at` (kiểm lúc accept lẫn trước đọc ảnh) |
| `source_image_unavailable` | file ảnh mất trước hạn |
| `budget_exceeded` | hết 2 job/khóa-168h hoặc 100 lượt/consumer-24h |
| `rate_limited` | quá 2 job đồng thời — giới hạn tạm thời, retry được |
| `request_conflict` | cùng `request_id` khác canonical body |
| `provider_failed` | job đã nhận mà Qwen lỗi/hết retry |
| `request_forbidden_field` | request chứa image/prompt/bytes/URL/path/secret |
| `request_too_large` | body > 16 KiB |
| `package_reference_invalid` | `result.package_id` trong status trỏ gói chưa publish cho consumer |

Nguyên tắc xử lý: lỗi gói/record do **consumer** phát hiện khi kiểm/nhập →
không `accepted`, quarantine + receipt `rejected` (hoặc không gửi được
receipt hợp lệ thì giữ pending và báo); lỗi receipt/request do **producer**
phát hiện → trả error envelope với `code` ở trên.

## 12. Kiểm tra contract (validator & fixtures)

### 12.1 Chạy

Trong folder contract (sau publish: `contracts/zalo-intake/`):

```text
python validate_examples.py                  # chạy mọi case examples/{valid,invalid}/*
python validate_examples.py --case valid/<name>   # một case, verbose
python validate_examples.py --hashes <case>       # in size_bytes + sha256 của file trong case
python -m _validator.run_slice rules_record rec- gap-   # chạy theo slice khi phát triển song song
python -m unittest discover -s _validator/tests -t .    # test framework (không phải fixture)
```

- Exit `0` = mọi case đúng kỳ vọng; exit `1` = có **unexpected outcome** (case
  valid bị reject, case invalid không ra đúng `expected_errors`, case lỗi
  authoring) hoặc không có case nào.
- Dòng tổng kết: `N valid, M invalid, K unexpected outcomes;
  contract=<CONTRACT_REVISION>`. File `CONTRACT_REVISION` giữ revision của bộ
  contract (hiện `zalo-intake-v1-draft`).
- Validator chỉ dùng stdlib, không chạy service/Qwen/network — nó kiểm cấu
  trúc + quan hệ dữ liệu, **không** chứng minh hành vi runtime (đó là việc
  của test MIN-97/99).

### 12.2 Bố cục fixture

`examples/{valid,invalid}/<case-name>/` — mỗi case một thư mục gồm
`case.json` + các file document cần kiểm:

| Khóa `case.json` | Quy tắc |
|---|---|
| `kind` | bắt buộc — chọn đúng một validator đã đăng ký (bảng §12.3) |
| `description` | bắt buộc — case chứng minh điều gì |
| `expected_errors` | invalid: bắt buộc, liệt kê đúng tập mã mong đợi (so khớp **bằng tập hợp**, không thừa không thiếu); valid: không khai/để rỗng |
| `context` | object tùy chọn — dữ liệu thuần cho validator (clock cố định, trạng thái trước, quota đã dùng…) |

Quy ước tên theo slice: `pkg-*` `seq-*` `rcpt-*` `status-*` (gói/transport),
`rec-*` `gap-*` (record + listener gap), `req-*` `rstat-*` (OCR request).
Tên = `<prefix><số>-<slug>` (vd `pkg-03-hash-mismatch`).

**Thêm fixture mới:** chọn đúng `kind` + prefix; viết file document
byte-exact (LF, không BOM — dùng `--hashes` để lấy hash thật điền vào
manifest/READY); `expected_errors` chỉ được chứa mã trong catalog §11; valid
case không khai `expected_errors`; file thừa/thiếu trong dir case là một phần
của kịch bản (validator tự kiểm).

### 12.3 Case kinds & context

| `kind` | File trong case | `context` |
|---|---|---|
| `package` | `manifest.json`, `records.jsonl`, `READY.json` (+ file thừa/thiếu theo kịch bản) | `consumer_id`, `expected_sequence`, `previously_imported` = `[{package_id, manifest_sha256}]`. Kiểm file/hash/manifest/READY/JSONL framing/count — **không** kiểm nội dung record |
| `package_sequence` | nhiều subdir `package_1…n` đủ ba file | `expected_start` (+ `consumer_id`, `previously_imported` truyền xuống từng gói con) — kiểm mỗi gói như kind `package` và sequence liên tiếp từ `expected_start` (vắng → từ gói đầu) |
| `receipt` | `receipt.json` (+ optional `package/` subdir gồm ba file gói) | `consumer_id`, `existing_packages` = `[{package_id, manifest_sha256, record_count}]`; `package/` overlay ghi đè bằng hash manifest byte thật |
| `service_status` | `status.json` | — |
| `record` | `record.json` một raw record | `existing_records` = `[{record_id, canonical_sha256}]`, `existing_revisions` = `[{logical_id, revision, canonical_sha256, captured_at?}]`, `supersedes_targets` = `[{record_id, revision}]` |
| `listener_gap` | `records.jsonl` các `listener_session` theo thứ tự | `expected_gaps` = `[{started_at, ended_at, start_is_estimate}]` — gap thu được phải khớp đúng tập này |
| `ocr_request` | `request.json` | `now`, `authenticated` (bool), `config_version` (OCR config hiện hành của producer, cho dedupe), `sources` = `{logical_id: {captured_at, current_revision, image_available, enabled}}`, `quota_used` = `{key_jobs, day_calls, concurrent}`, `existing_requests` = `[{request_id, body_canonical_sha256, job_id, state, logical_id?, variant?, preset?, config_version?}]` (tuple optional chỉ cần cho dedupe) |
| `ocr_request_status` | `status.json` | `existing_packages` (cho `package_reference_invalid`; `existing_requests` được chấp nhận nhưng không tra trong v1) |

Inventory fixture cụ thể theo nhóm (slice ghi kèm schema):

- **valid**: gói đầy đủ nhiều loại record; chuỗi gói sequence đúng; receipt
  accepted + rejected hợp lệ; service-status; record từng `record_kind`
  (hai mặt giấy, GCN nhiều trang, tin chỉ text, OCR lỗi một trang, revision
  mới, listener crash không kịp `disconnected`); OCR request từng variant;
  request status.
- **invalid**: theo mã — gói thiếu/thừa/cấm file, hash/size/count sai, path
  thoát, sequence gãy; record vi phạm từng rule §11.3; receipt sai
  consumer/hash/count; request sai variant/preset/quyền/quota/hạn, cùng ID
  khác body, status trỏ gói không tồn tại.

### 12.4 Quy tắc schema file

- JSON Schema **draft 2020-12**, chỉ dùng keyword mà validator hỗ trợ
  (`_validator/schema_subset.py`: annotations, `$defs`/`$ref` cùng file hoặc
  file tương đối, `type`/`enum`/`const`, `properties`/`required`/
  `additionalProperties`/`patternProperties`/`propertyNames`/
  `minProperties`/`maxProperties`/`dependentRequired`, `items`/`prefixItems`/
  `minItems`/`maxItems`/`uniqueItems`, `minLength`/`maxLength`/`pattern`/
  `format`, `minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum`,
  `allOf`/`anyOf`/`oneOf`/`not`/`if`/`then`/`else`). Keyword lạ → schema bị
  từ chối lúc load (`UnsupportedSchemaKeyword`) — không âm thầm bỏ qua.
- `format` chỉ có `date-time` (offset bắt buộc) và `uuid` (lowercase).
- `additionalProperties: false` ở **mọi** object.
- `x-error-code` trên subschema gán mã lỗi khi nhánh đó fail — mã phải thuộc
  catalog §11.
- `$id` chỉ ở root file; `$ref` không dùng anchor/URI tuyệt đối/query.

## 13. Quy tắc nâng version

- Trong `v1`, mọi thay đổi phải **additive**: trường optional mới, giá trị
  enum mới ở vị trí consumer được phép bỏ qua, file fixture mới. Đổi additive
  → bump `CONTRACT_REVISION` + fixture chứng minh + cập nhật doc này.
- **Đổi phá vỡ** — đổi/tên/kiểu/nghĩa trường, đổi trường optional thành bắt
  buộc, đổi byte rules/hash rules, đổi enum trạng thái cốt lõi, đổi whitelist
  file — → schema version mới (`intake.*.v2`) + bộ schema/fixtures riêng.
- Consumer chưa hỗ trợ major schema version của gói → quarantine + báo lỗi,
  **không** `accepted`.
- Trường optional mới mà consumer cũ không hiểu được giữ hoặc bỏ qua, nhưng
  không được đổi nghĩa dữ liệu đã hiểu.
- Không agent nào tự tạo contract tích hợp mới rồi tự implement trong cùng
  một task (`contracts/README.md`).

## 14. Phần mở — KHÔNG chặn MIN-93

| Mục mở | Hướng xử lý |
|---|---|
| Ánh xạ geometry thật về khung gửi/ảnh nguồn | MIN-95 implement giữ `provider_lines` + frame; MIN-98 kiểm chứng trên ảnh có mốc; chỉ sau đó producer được phát `present_mapping_verified` |
| Event `edit` (sửa tin) | zca-js 2.1.2 không phát; nếu adapter sau này hỗ trợ → thêm `event_type` mới theo quy tắc §13 + capability `supported` |
| Multi-consumer | v1 đúng một consumer; mở rộng = contract version mới |
| Lấy bù tin bot chưa nhận / đối chiếu đủ tin | MIN-90 — ngoài contract này |

## Phụ lục A. Facts adapter & provider đã kiểm chứng (zca-js 2.1.2, Qwen)

Cơ sở: audit code `notary_v2/zalo_connector/` + typings zca-js 2.1.2 + tài
liệu Qwen-OCR (nguồn: `.agent/scratch/MIN-92/source-facts.md`).

- zca-js 2.1.2 phát `undo` (thu hồi) và `reaction`; **không** có event sửa
  tin (`edit`). `undo` tham chiếu tin gốc bằng `globalMsgId` + `cliMsgId`;
  `reaction` bằng `gMsgID`/`cMsgID` → module phải giữ `client_message_id`.
- **UNVERIFIED:** `msgId` (string) của tin gốc có bằng `globalMsgId`/`gMsgID`
  mà undo/reaction dùng để trỏ về hay không — typings không chứng minh; giữ
  cả hai ID.
- ID tới module: `msg_id` (`msgId`, fallback `cliMsgId`), `sender_id`
  (`uidFrom`), `conversation_id` (`threadId`), `source_sent_at` (`ts` epoch
  **ms**).
- Một tin zca-js có tối đa **1 attachment** (`data.attachments` không tồn
  tại — multi-attachment chỉ thấy trong test tổng hợp, runtime UNVERIFIED);
  `attachment_index` 0-based trong các file JPEG/PNG/PDF giữ được; không có
  attachment ID gốc → `attachment_id` module tự cấp.
- **UNVERIFIED:** tên trường URL ảnh HD thật (`hdUrl` vs `href`…) trong
  payload Zalo — chỉ ảnh hưởng việc module tải, không vào contract.
- PDF: PyMuPDF zoom 2× (~144 DPI), `page_number` 1-based → `page_index`
  contract 1-based.
- Prep ảnh hiện tại cho Qwen: EXIF transpose → resize max 2400px →
  median+contrast → JPEG q90 → resize max side 1800 → JPEG q82.
- Qwen: DashScope native, `qwen-vl-ocr-2025-11-20`, task `text_recognition`
  (mặc định) / `advanced_recognition` (geometry `words_info`), min/max_pixels
  3072/8388608, `enable_rotate=false` mặc định, timeout 90s.
- "Rotate" hiện tại = gửi lại `enable_rotate=true` (provider tự xoay) —
  không có góc client; cứu chân GCN hiện tại = crop đáy 42%
  (`top=int(h*0.58)`), resize ≤1400, q88 → nguồn của preset `bottom_42pct`.
- `location`: 4 đỉnh TL→TR→BR→BL gốc trên-trái "ảnh gốc"; `rotate_rect`
  `[cx,cy,w,h,deg]`, `deg ∈ [-90,90]` theo ví dụ (UNVERIFIED chính thức);
  kiểu số chưa nói → schema nhận `number`. Khung tọa độ sau provider
  resize/rotate **CHƯA xác minh** (§6.4).
- Connector hiện tại gửi state mỗi 15s; backend coi stale sau 45s —
  `last_heartbeat_at`/`uncertain_gap` của `listener_session` là cơ chế
  contract cho cảnh báo tương đương.


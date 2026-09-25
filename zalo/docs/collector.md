# Collector — hành vi thu nhận connector → module (MIN-94/95/97)

SOT nội bộ cho lớp collector của module Zalo: cách connector Node
(`connector/`, zca-js) đệm event qua outbox bền, cách attachment slot được
giữ hiển thị khi tải hỏng, và cách module Python (`src/zalo_module/`) ghi
nhận chúng thành trạng thái durable. Wire contract chi tiết ở
`docs/connector-protocol.md` — file này mô tả **hành vi** hai phía, không
lặp lại bảng route.

## 1. Pipeline & outbox bền

```
[event zca-js] → normalizeMessage (connector) → FileOutbox
   (webhook-outbox / download-queue / unknown-source-queue)
→ publish HMAC → POST /connector/v1/events
→ journal_entries + records / media_assets / listener_sessions (module)
→ gói raw cho consumer (MIN-97)
```

- Mọi event đi qua `FileOutbox`: ghi `*.tmp` + `rename` atomic, mode `0600`;
  file chỉ xóa sau exact-ACK — outbox sống qua restart của cả connector lẫn
  module (module down → outbox tích lũy, flush lại khi ACK trở lại).
- `entries()` chịu được race `readdir → readFile`: entry biến mất (`ENOENT`)
  bị bỏ qua; `EPERM`/`EACCES`/`EBUSY` thoáng qua trên Windows (AV/indexer
  lock file vừa rename) được retry tối đa 3 lần × 25 ms — lỗi bền vẫn
  propagate. `remove()` coi file đã xóa là thành công.
- `flush()` **không dừng ở lỗi đầu tiên**: entry hỏng vẫn pending, các entry
  phía sau vẫn được gửi — một event "độc" không chặn hàng đợi. Flush rethrow
  lỗi đầu tiên sau khi đi hết danh sách.
- Mỗi lần gửi thất bại được đếm bền trong sidecar `<name>.attempts` (sống
  qua restart, reset khi `enqueue` ghi đè cùng key). Sau **>8** lần thất bại
  entry bị quarantine sang `<outbox>/dead/` — file giữ nguyên làm dead-letter
  (không xóa, không nằm trong `pending()`). Warning chỉ chứa mã sanitized
  (`HTTP <status>` / `ack-mismatch` / `storage_full` / `<ErrorClass>` /
  `send-failure`) — không URL, path hay payload provider.
- `download-queue` entry là durable retry: mỗi attachment tải hỏng giữ lại
  entry (tối đa `MAX_DOWNLOAD_ATTEMPTS = 3` lần) và mỗi lần publish cập nhật
  slot trong assembly của message.

## 2. Attachment slots — downloaded vs failed marker

- `media_object_key` là **reserved key** connector tính deterministic từ
  `(account_id, msg_id, attachment_index, mime_type, sent_at)` — slot tồn
  tại kể cả khi download chưa/ không bao giờ thành công.
- Download hỏng → slot publish dạng failed marker:
  `{attachment_index, mime_type, media_object_key, status: "failed",
  error_code}`. `error_code` là tập cố định `[a-z0-9_]{1,64}`:
  `download_failed`, `download_aborted`, `download_http_error`,
  `storage_full` (khi quota đầy). Chuỗi lỗi upstream, URL, filename **không
  bao giờ** đi qua wire/log/journal — chỉ còn mã ổn định.
- `download_url`/`original_filename` chỉ sống trong download-queue nội bộ;
  envelope publish chỉ chứa `{attachment_index, mime_type,
  media_object_key, size_bytes}` hoặc failed marker.
- Khi `MediaStore.prune` báo `storage_full`, connector đánh cờ
  `storage_full` trên state event và gắn marker `error_code="storage_full"`
  cho mọi attachment — text vẫn chảy, media không biến mất âm thầm.

### Phía module (`intake/engine.py`)

- Failed marker ingest → `media_assets` row `state="missing"`
  (`sha256=""`, expiry theo `sent_at + 168h`) + `sources` row
  `scope="attachment"`, `image_available=0` + record
  `processing_status` code `media_missing` (note = `error_code`).
- Envelope chứa failed marker vẫn import bình thường: text và các media
  tải được không bị slot hỏng kéo chết; media-only-failure vẫn là message
  hợp lệ (`raw_text: null`).
- ACK `components.media[].status ∈ imported | duplicate | ignored |
  missing` — `missing` là ACK hợp lệ trong exact-ACK.

## 3. Media supplements — missing → captured

- Attachment retry **sau khi** envelope đã publish phát
  `event_type: "media"` supplement (cùng `media_object_key`, kèm
  `size_bytes`) thay vì publish lại message — một tin nhắn = một envelope.
- Module upgrade **cùng `attachment_id`**: `state` missing → `captured`,
  `sha256` thật, `image_available=1`, thêm revision `processing_status`
  `captured`; dedupe journal row được rewrite sang component đã tải.
- Replay sạch: supplement lặp → `same`; envelope replay dạng downloaded →
  `same`. Payload khác `media_object_key`/mime/size trên cùng dedupe key →
  409 `conflict`; failed marker đến **sau** khi slot đã captured cũng là
  conflict (không downgrade).

## 4. Source events — recall & reaction (undo/reaction)

- zca-js listener phát `undo` (thu hồi tin) và `reaction`. Connector
  normalize qua `sourceEventsFromUndo`/`sourceEventsFromReaction`
  (`connector/src/core.mjs`) → envelope `event_type: "source_event"`,
  `event_subtype: recall|reaction`, qua `enqueueOperation` + `FileOutbox`
  + `sendEvent` như mọi event khác (`installSourceEventHandlers`,
  `connector/src/connector.mjs`).
- Giữ nguyên identity nguồn: `target_provider_message_id` từ
  `content.globalMsgId`/`rMsg[].gMsgID` (fallback `msgId`/`cliMsgId`/
  `cMsgID`), `target_client_message_id` từ `cliMsgId`/`cMsgID`,
  `reaction_icon` (`content.rIcon`) verbatim, `observed_at` từ `data.ts`,
  conversation metadata + sender nếu có. `eventId` derive từ nội dung →
  redelivery cùng zca event ghi cùng outbox file (dedupe-safe).
- `conversation_type` resolve **lúc emit** qua `conversationTypeFor` (map
  `sourceNames` bị rebind mỗi reconcile — snapshot cũ không dùng được;
  fallback cờ `isGroup` của event).
- Reaction với icon rỗng (gỡ reaction) **không** emit — v1 yêu cầu icon
  non-empty, thà bỏ qua còn hơn tạo record sai contract.
- Module (`_ingest_source_event`): validate theo record contract (subtype,
  target id bắt buộc, reaction phải có icon 1–64 ký tự, recall cấm icon,
  conversation_type user|group) → record `source_event` schema-valid trên
  `Source(scope="source_event")` riêng, rev-1 — record chỉ *quan sát*
  event, không mutate tin đích. Dedupe anchor = digest của
  (account, conversation, subtype, target ids, icon, actor) — replay
  giống hệt → `duplicate`, khác payload → 409.
- `client_message_id` (`cliMsgId`) đi cùng message envelope →
  `source.client_message_id` của `message_text` record — recall/reaction
  link về tin gốc qua cả provider lẫn client id (contract §5.2).
- Discovery (source mới phát hiện) cũng là `kind="source_event"` nhưng
  là row nội bộ — ghi `packaged_in="__internal__"` ngay lúc ingest nên
  `package_build` (select `packaged_in IS NULL`) không bao giờ đưa nó
  vào gói consumer; payload cố tình không claim `schema_version` (enum
  `event_type` v1 chỉ recall|reaction).

## 5. Listener sessions & coverage gaps

- `state`/`heartbeat` event → `apply_connector_report`: generation guard
  (stale generation không bao giờ đảo state mới), `qr_login_success` +
  `bound_zalo_id`, `storage_full`, `qr_image` TTL 100s.
- Chỉ report **được chấp nhận** (`changed=True`) mới ghi
  `listener_sessions` — report generation cũ chỉ vào journal (revoked/
  stale session không hồi sinh).
- Quy tắc row: transition khác state → row mới; cùng state → heartbeat
  cập nhật `last_heartbeat_at` in-place (không phình row); generation bump
  → luôn row mới (mỗi lần connect = một `session_id`). `reason` lấy từ
  `payload.reason`/`error_code` (tối đa 200 ký tự).
- **Heartbeat không tạo raw record** — chỉ có transition/generation bump
  (tức row mới) phát `listener_session` record, `logical_id =
  session_id` — mỗi phiên là một logical chain rev-1 (reconnect sau
  crash/disconnect mở chain mới, không revision chain cũ). Record
  `listener_session` **là packageable kind** — vào gói consumer bình
  thường.
- `listener.observed_at`/`captured_at` = giờ **module** quan sát; cột
  `observed_at` của row và marker `gap_started_at` giữ giờ connector (so
  sánh detection cùng một clock domain); `last_heartbeat_at`/`last_seen_at`
  dùng giờ backend (backend-authoritative).
- `uncertain_gap` chỉ gắn vào record `connected`: `{started_at, ended_at,
  start_is_estimate: true}`; `ended_at` = `listener.observed_at` của phiên
  mới. `started_at` là ước lượng = coverage chắc chắn cuối:
  `observed_at` của row disconnect/login_required kế trước, hoặc
  `last_heartbeat_at` của phiên trước cho gap dạng crash (marker
  `connector_accounts.gap_started_at` chỉ dùng để **phát hiện** gap im lặng
  — phải mới hơn observation session cuối theo giờ connector; marker cũ của
  episode đã đóng không được tái kích hoạt).
- `connector_accounts.gap_started_at` được **refresh mỗi episode** mất
  coverage (report disconnect/login_required khi đang usable, hoặc
  generation bump khi đang usable) — marker đã "tiêu thụ" không chặn
  detection của episode sau. `listener_gaps()` ghép session rows + marker
  thành khoảng `{started_at, ended_at, ongoing}` cho `/state.gaps`.

## 6. Retention & storage

- `ZALO_CONNECTOR_RETENTION_HOURS` (default **168**): `expire_media(now)`
  quét `media_assets.state != 'expired'`, due khi `captured_at + hours <=
  now` (fallback `expires_at`) → xóa file gốc `runtime/media/...` + mọi
  derived variant `media/derived/<attachment_id>/{…,-*,_*,.*}` → prune
  thư mục rỗng → `state='expired'`.
- Records / `sources` / journal / packages **không** bị động vào; hàng
  `missing` hết hạn theo cùng luật; package ACK **không** gia hạn media.
- `retention_sweep` là job kind + sweeper định kỳ đầu mỗi worker pass —
  đăng ký qua `media_jobs.register`/`register_sweepers` →
  `jobs/handlers.build_sweepers()`.
- `ZALO_CONNECTOR_QUOTA_BYTES` (default 5 GiB): connector-side quota; khi
  chạm trần module lật `connector_accounts.storage_full` và
  `/state.media.storage_full`; `/state.media.usage_bytes` là tổng bytes
  thực dưới `runtime/media` (gốc + derived).

## 7. `GET /connector/v1/state` — ops snapshot

Shape legacy giữ nguyên (`connector`/`policy`/`sources`/`data_sync`/
`connector_error`); các block **additive** MIN-94:

| Block | Nội dung |
|---|---|
| `gaps[]` | `{started_at, ended_at, ongoing}` — khoảng mất coverage từ `listener_gaps()` |
| `queue` | `{pending_jobs, oldest_age_s}` — backlog `jobs` (`queued`/`retry_wait`) |
| `media` | `{usage_bytes, quota_bytes, storage_full}` |
| `warnings[]` | `{code, message}` — `listener_heartbeat_stale` (>45 s khi đang `usable`), `gap_open`, `disk_pressure` (≥90% quota), `storage_full` |

Không có vocabulary consumer (`batches`, `media_grid`, `exports`).

## 8. Invariants kiểm bằng test

- Không image bytes/base64 trên wire — media chỉ đi qua file chia sẻ
  `ZALO_INBOX_STORAGE_ROOT`.
- Không `download_url`, `original_filename`, chuỗi exception upstream trong
  event publish, warning outbox hay log.
- Dedupe/replay/restart recovery: journal `source_key` là anchor;
  `listener_sessions`/`media_assets`/`records` durable qua `init_db` lại.
- `source_event`/`listener_session` records validate đúng vendored
  `raw-record` schema và **packageable**; discovery nội bộ không bao giờ
  vào gói (`packaged_in="__internal__"`).
- Heartbeat/stale-generation report không tạo record; `uncertain_gap` chỉ
  trên record `connected` với `started_at < ended_at`,
  `start_is_estimate: true`.
- Xem `tests/test_collector_wave.py` (missing media, upgrade, sessions,
  source events, gaps, retention, state helpers, package exclusion) và
  `connector/test/connector.test.mjs` + `connector/test/core.test.mjs`
  (outbox race, failed markers, supplement, retry bound, quarantine,
  undo/reaction normalize, redaction).

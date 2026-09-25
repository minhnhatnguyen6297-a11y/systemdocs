# Connector protocol — ranh giới nội bộ connector ↔ module

Contract **nội bộ** giữa tiến trình Node connector (`connector/`, zca-js) và
module Python (`/connector/v1`, internal control plane). Đây **không phải**
contract trao đổi với máy chính — ranh giới đó là `contracts/zalo-intake/`
(`/intake/v1`, vendored ở `schemas/`). File này là SOT cho dây truyền
connector↔module; được chuyển/diễn lại từ baseline v1
`notary_v2/zalo_connector/` + `services/zalo_inbox.py` tại MIN-103.

## 1. Route table — `/connector/v1`

Module FastAPI mount router prefix `/connector/v1`. Cột "legacy" là endpoint
v1 tương đương trong `notary_v2` (prefix `/zalo-inbox/api`), giữ để đối chiếu
parity.

| Method + Path (module) | Legacy v1 | Handler / semantics |
|---|---|---|
| `POST /connector/v1/connectors/onboard` | `.../api/connectors/onboard` | Header `x-zalo-bootstrap` → `{connector_account_id}` (single-account: account đầu theo `created_at`) |
| `POST /connector/v1/events` | `.../api/webhook` | `x-zalo-timestamp` + `x-zalo-signature` HMAC(`{ts}.{body}`) ±300s → `{"ack": true, "components": {...}}` |
| `GET /connector/v1/connectors/{id}/config` | `.../api/connectors/{id}/config` | Signature trên body rỗng → `{listener_generation, policy_version, policy_acked_version, source_sync_request_version, source_sync_acked_version, sources[...], protected_media_object_keys[]}` |
| `GET /connector/v1/connectors/{id}/commands/next` | `.../commands/next` | Derived-key `HMAC(webhook_secret, account_id)` → `204` \| `{command_type:"data_sync", run_id, cutoff_at, deadline_at, source_ids[]}` |
| `POST /connector/v1/connectors/{id}/consent` | `.../api/connectors/{id}/consent` | `apply_intake_consent` |
| `POST /connector/v1/connectors/{id}/sources/refresh` | `.../sources/refresh` | `request_source_sync` |
| `POST /connector/v1/connectors/{id}/data-sync` | `.../data-sync` | `start_data_sync` |
| `PATCH /connector/v1/sources/{id}` | `.../api/sources/{id}` | `set_source_policy` |
| `GET /connector/v1/media/{id}/content` | `.../api/media/{id}/content` | `FileResponse` media của module — chỉ ops/debug local |
| `GET /connector/v1/state` | `.../api/state` | Ops snapshot của module — **chỉ** phần connector+policy+sources+data_sync (không có phần batch/media-grid của consumer) |
| `POST /connector/v1/connectors/start` | `.../api/connectors/start` | Spawn connector subprocess (process manager `connector_proc.py`) |

`protected_media_object_keys`: trong v1 derive từ `ZaloBatch.items_json`;
trong module derive từ `media_assets` chưa hết hạn (mọi media còn sống đều
protected). Nới theo ACK ghi ở `[MIN-97]` khi cần.

## 2. Xác thực

### 2.1 Onboard — bootstrap secret

```
POST /connector/v1/connectors/onboard
x-zalo-bootstrap: <ZALO_INBOX_BOOTSTRAP_SECRET>
→ {"connector_account_id": "<uuid>"}
```

### 2.2 Event webhook — HMAC `{ts}.{body}` ±300s

```
POST /connector/v1/events
content-type: application/json
x-zalo-timestamp: <unix seconds>
x-zalo-signature: <hex HMAC-SHA256>

signature = HMAC_SHA256(key=ZALO_INBOX_WEBHOOK_SECRET,
                        msg="{x-zalo-timestamp}.{raw_body}")
```

- Module kiểm `|now − timestamp| ≤ 300s` (chống replay) trước khi so chữ ký;
  so sánh bằng `hmac.compare_digest`.
- Response phải qua **exact-ACK**: `{"ack": true}` chưa đủ — connector kiểm
  `components` khớp event (xem §3.6).
- `GET .../config` ký trên **body rỗng**: `HMAC("{ts}.")` (dấu `.` vẫn có,
  body là chuỗi rỗng).

### 2.3 Command poll — derived key

`GET .../commands/next` **không** ký bằng webhook secret trực tiếp:

```
account_key = HMAC_SHA256(key=ZALO_INBOX_WEBHOOK_SECRET, msg=account_id).hex()
x-zalo-signature = HMAC_SHA256(key=account_key, msg="{ts}.")
```

Response: `204` khi không có lệnh; nếu có → `{command_type: "data_sync",
run_id, cutoff_at, deadline_at, source_ids[]}`. Connector validate đủ trường
và `cutoff_at`/`deadline_at` parse được ISO trước khi chạy.

## 3. Event JSON shapes

Mọi event gửi qua `POST /connector/v1/events` đều có `schema_version: 1` và
`connector_account_id`. Body serialize JSON thô chính là chuỗi được ký.

### 3.1 `discovery` — metadata nguồn

```json
{
  "schema_version": 1,
  "event_type": "discovery",
  "connector_account_id": "<uuid>",
  "conversation_id": "<threadId>",
  "conversation_type": "user|group",
  "source_type": "friend|group|stranger|my_documents",
  "source_display_name": "<tên>",
  "last_activity_at": "<ISO 8601|null>"
}
```

Phát khi Source Sync quét friends/groups, khi `friend_event`/`group_event`,
listener reconnect, targeted lookup cho unknown thread và reconcile 60 phút.

### 3.2 `message` — envelope tin nhắn

```json
{
  "schema_version": 1,
  "event_type": "message",
  "connector_account_id": "<uuid>",
  "conversation_id": "<threadId>",
  "conversation_type": "user|group",
  "source_type": "friend|group|stranger|my_documents",
  "source_display_name": "<tên>",
  "msg_id": "<msgId|cliMsgId>",
  "sender_id": "<uidFrom>",
  "sent_at": "<ISO 8601>",
  "raw_text": "<string|null>",
  "attachments": [
    {
      "attachment_index": 0,
      "mime_type": "image/jpeg|image/png|application/pdf",
      "media_object_key": "<accountId>/<YYYY-MM-DD>/<sha256(msgId:idx)>.<jpg|png|pdf>",
      "size_bytes": 12345,
      "original_filename": "<tên>"
    }
  ]
}
```

- `download_url` **bị xóa** trước khi publish — URL CDN Zalo không đi qua
  wire; module chỉ resolve `media_object_key` trong storage root chia sẻ.
- Self-message bị drop trừ khi `threadId == session send2me_id` (My
  Documents). `raw_text == null` và `attachments == []` → không normalize.
- Dedupe key: `(connector_account_id, conversation_id, msg_id)`; mỗi
  attachment thêm `:{attachment_index}`. Cùng key + payload khác → conflict,
  không overwrite.

### 3.3 `state` — trạng thái listener/session

```json
{
  "schema_version": 1,
  "event_type": "state",
  "connector_account_id": "<uuid>",
  "state": "login_required|connected|disconnected",
  "listener_generation": 3,
  "observed_at": "<ISO 8601>",
  "storage_full": false,
  "qr_image": "data:image/png;base64,...",
  "qr_login_success": true,
  "bound_zalo_id": "<ownId>",
  "error_code": "..."
}
```

- `listener_generation` tăng mỗi lần khởi động connector (file
  `generation.json`); event generation cũ không đảo trạng thái generation mới.
- `qr_image`: data-URL PNG từ zca-js QR callback (TTL 100s); QR token không
  bao giờ forward. `qr_login_success` + `bound_zalo_id` đi khi login/session
  restore thành công (ACK trước khi `saveSession`).
- **`error_code` bị backend v1 drop** — connector gửi, module không lưu
  (drift đã ghi ở `baseline-open-issues.md`).

### 3.4 `policy_ack` / `source_sync_ack`

```json
{"schema_version":1, "event_type":"policy_ack",
 "connector_account_id":"...", "policy_version": 4}
{"schema_version":1, "event_type":"source_sync_ack",
 "connector_account_id":"...", "source_sync_request_version": 2}
```

Connector chỉ ACK sau khi đã áp dụng policy staged (fail-closed) / đã chạy
xong `syncSources` cho version được yêu cầu.

### 3.5 `data_sync_progress` / `data_sync_complete` / `data_sync_failed`

```json
{"schema_version":1, "event_type":"data_sync_progress",
 "connector_account_id":"...", "run_id":"...",
 "counters":{"received":0,"duplicates":0,"imported_text":0,
             "imported_media":0,"media_download_failures":0}}
{"schema_version":1, "event_type":"data_sync_complete", "...", "counters":{...}}
{"schema_version":1, "event_type":"data_sync_failed", "...",
 "error_code":"deadline_expired|listener_disconnected|
              history_request_failed|history_processing_failed",
 "counters":{...}}
```

Đúng một `requestOldMessages(User)` + một `requestOldMessages(Group)` phạm vi
thread-type toàn account; lọc cục bộ theo snapshot nguồn bật và cửa sổ
**7 ngày** từ `cutoff_at` (≠ retention 168h của media — xem drift). Terminal
event retry đến khi ACK; HTTP 409 coi như đã nhận.

### 3.6 ACK response (module → connector)

```json
{"ack": true,
 "components": {"text": "absent|imported|duplicate|ignored",
                "media": [{"attachment_index": 0,
                           "status": "imported|duplicate|ignored"}]}}
```

- `policy_ack`: response phải có `policy_version` khớp event.
- `source_sync_ack`: phải có `source_sync_request_version` khớp.
- `message`: `components.media` phải đúng thứ tự và đủ số attachment.
- `data_sync_progress|complete|failed`: chỉ `{"ack": true}`.
- Các event còn lại (`discovery`, `state`/`heartbeat`, `media`): trả
  `{"ack": true, "id": <id đối tượng|null>}` — `id` là conv_source_id /
  media attachment_id; `null` cho state/heartbeat và media bị ignore.
- Không khớp → connector throw, giữ event trong outbox và retry.
- Event `heartbeat` và `media` (media-only) module v1 **chấp nhận** nhưng
  connector **không bao giờ phát** — giữ parity, không loại bỏ ngầm.

## 4. Env names (verbatim — đổi tên = đổi wire contract)

| Env | Bên đọc | Ý nghĩa |
|---|---|---|
| `ZALO_INBOX_BACKEND_URL` | connector | Base URL module, vd `http://127.0.0.1:8790` (process manager set `http://{bind}:{port}`) |
| `ZALO_INBOX_BOOTSTRAP_SECRET` | connector + module | Header `x-zalo-bootstrap` onboard |
| `ZALO_INBOX_WEBHOOK_SECRET` | connector + module | Khóa HMAC event/config + gốc derive command key |
| `ZALO_INBOX_STORAGE_ROOT` | connector + module | Root media chia sẻ (`MediaStore` ghi, module đọc/resolve) |
| `ZALO_CONNECTOR_STATE_ROOT` | connector | Root state file + outbox (default `{runtime_root}/connector`) |
| `ZALO_CONNECTOR_QUOTA_BYTES` | connector (module settings cũng đọc, default 5GiB) | Quota đĩa `MediaStore.prune` |
| `ZALO_CONNECTOR_RETENTION_HOURS` | connector (module default 168) | Retention mtime media |
| `ZALO_CONNECTOR_PARENT_PID` | connector | Process manager set; connector tự exit khi parent chết (watch 2s) |
| `ZALO_CONNECTOR_FORCE_QR` | connector | `=1` bỏ session restore, bắt QR mới |
| `ZALO_DATA_SYNC_TIMEOUT_SECONDS` | module | Deadline `data_sync` run (default 900) |

Đọc config module ở `src/zalo_module/settings.py` — Settings đọc đúng các tên
trên. Đổi tên env phải qua decision riêng (defer MIN-94), không đổi trong
task port.

## 5. State root & outbox layout (phía connector)

Dưới `ZALO_CONNECTOR_STATE_ROOT` (module default `{runtime_root}/connector`):

```
<state_root>/
  account.json            connector_account_id do module cấp (onboard)
  session.json            session zca-js — cookie/imei/userAgent
  generation.json         listener_generation hiện tại
  login-qr.png            QR png tạm trong phiên login
  webhook-outbox/         FileOutbox — event chờ ACK: sha256(eventId).json
  download-queue/         FileOutbox — attachment chờ tải/publish
  unknown-source-queue/   FileOutbox — event chờ resolve nguồn
```

`FileOutbox`: mỗi entry là file `sha256(key).json`, ghi `tmp` + `rename`
(atomic), mode `0600`; flush tuần tự, xóa file chỉ sau exact-ACK. Outbox sống
qua restart — đây là cơ chế "event đã nhận không mất" (CAP-03/R-023).

**Secrets warning:** `session.json` chứa cookie/imei/userAgent = **chiếm
tài khoản hoàn toàn** nếu lộ. `account.json`, `login-qr.png` và 3 thư mục
outbox chứa JSON riêng tư + URL CDN. Toàn bộ `ZALO_CONNECTOR_STATE_ROOT` và
`ZALO_INBOX_STORAGE_ROOT` phải nằm dưới `runtime/` đã gitignore — **không bao
giờ commit**, không đưa vào snapshot (`tools/export_snapshot.ps1` loại trừ
`runtime/`).

## 6. Process manager (module spawn connector)

`POST /connector/v1/connectors/start` → `connector_proc.py` spawn
`node connector/bin/run.mjs` với `cwd` = repo root, env whitelist + secrets +
`ZALO_CONNECTOR_STATE_ROOT`/`ZALO_INBOX_STORAGE_ROOT` trỏ vào
`{runtime_root}/connector` và `{runtime_root}/media`, kèm
`ZALO_CONNECTOR_PARENT_PID`. `serve` **không** auto-spawn connector — không
tự chạy listener. Chỉ một listener cho một account (CAP-01); xem
`docs/rollback-runbook.md` cho quy tắc chuyển đổi legacy↔module.

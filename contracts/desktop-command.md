# Contract: DesktopCommand `v1`

**Version:** `desktopcommand.v1` · **Status:** APPROVED (owner duyệt 14/09/2026)
· **Owner:** module `shell/` (runtime) — trước đây branch `electron-system-shell` ·
**Published:** P3 / MIN-72 · **Supersedes:** POC `v0.experimental`
(`upload_lab@f18a42f:poc/desktop_command/` — không tương thích ngầm)

Contract giữa **Electron main** (consumer) và **Python sidecar** (producer)
trên **một máy Windows**. Renderer không bao giờ gọi sidecar trực tiếp.
Phạm vi G1-SM: loopback `127.0.0.1`; không LAN.

## 1. Kênh & auth

- HTTP `http://127.0.0.1:<port>`; **port động** — Electron main chọn port rảnh
  trước khi spawn; sidecar nhận qua env `SIDECAR_PORT`.
- Bearer token: main sinh ngẫu nhiên mỗi lần start, truyền qua env
  `SIDECAR_TOKEN`; sidecar yêu cầu `Authorization: Bearer <token>` trên mọi
  endpoint trừ `/healthz`. Token chỉ nằm trong bộ nhớ Electron main — không
  renderer, không log, không URL, không storage, không payload.
- Không CORS middleware. Sidecar từ chối Origin lạ là hợp lệ.

## 2. Endpoints

| Endpoint | Nghĩa |
|---|---|
| `GET /healthz` | liveness + `supported_versions`, `engine_version` — không cần auth (localhost-only); KHÔNG trả token/paths nhạy cảm |
| `POST /v1/commands` | nhận command → `{job_id, command_id, status:"accepted"}` hoặc job cũ nếu `command_id` trùng (idempotent) |
| `GET /v1/jobs/{job_id}` | trạng thái job hiện tại (client poll — không SSE trong v1) |
| `POST /v1/jobs/{job_id}/cancel` | hủy khi còn `accepted/running/waiting_user` |
| `POST /shutdown` | drain + thoát (exit 0); timeout phía main → kill |

## 3. Request shape

```yaml
contract_version: "desktopcommand.v1"     # bắt buộc, đúng literal
command_id: <uuid v4, client sinh>        # idempotency key
command: <namespaced string>              # vd upload.scan, ocr.analyze
payload: <object|null>
client_meta: { shell_version: <semver>, module: <module id> }
```

**Cấm đệ quy trong payload** (mọi cấp key, không phân biệt hoa thường):
`password, passwd, secret, token, credential, cookie, auth, session,
storage_state, api_key, bearer`. Vi phạm → `400 payload_rejected_sensitive_key`.
Lưu ý `authorization`/`authenticator` cũng chặn theo pattern `auth`.

## 4. Job / status shape

```yaml
contract_version: "desktopcommand.v1"
job_id: <server sinh>
command_id: <echo>
status: accepted | running | waiting_user | partial | succeeded | failed | canceled
waiting_on: login | review | finalize | confirm | null
progress: { done: <int>, total: <int>, current_label: <string> } | null
result: <object|null>        # shape theo g1-module-data.v1 §2
error:
  code: <namespace.snake_case>
  message: <string cho người đọc>
  retryable: <bool>
  next_action: login_required | pick_files | retry | contact_admin | null
  job_id: <id>
  details: <object, không chứa dữ liệu nhạy cảm> | null
updated_at: <iso8601 UTC>
```

## 5. Semantics

- **Idempotency:** cùng `command_id` → trả job cũ, không nhân đôi tác dụng
  phụ. Đây là cơ chế chống duplicate upload khi retry/cancel.
- **Terminal:** `succeeded/failed/canceled` là terminal; `partial` terminal và
  bắt buộc `result.data.breakdown={succeeded:[],failed:[]}`.
- **waiting_user:** engine cần người → `status=waiting_user` + `waiting_on`;
  client poll tiếp. Engine **không** tự hoàn thành bước đó (đặc biệt
  `finalize` — không auto-Save/auto-Finalize).
- **Cancel:** `POST .../cancel` → `canceling` → `canceled` với
  `error.code=user_canceled`; job terminal → `409 job_already_terminal`.
  Cancel bởi engine shutdown → `error.code=engine_shutdown`.
- **Reconnect:** client biết `job_id`/`command_id` → query lại sau crash.
- **Restart:** sidecar restart → in-flight jobs thành
  `failed{code:engine_restarted, retryable:true}`; registry không giả lưu.
- **Version:** request sai/thiếu `contract_version` → `400
  unsupported_contract_version`. Sidecar có thể hỗ trợ nhiều version qua
  `supported_versions`; client dùng version cao nhất giao nhau; không có giao
  → báo `engine_version_mismatch`, không chạy.

## 6. FileRef (machine scope — D0-7 đã duyệt)

```yaml
file_ref:
  path: <absolute path>        # cho phép \\?\ prefix; KHÔNG tương đối
  scope: machine_local         # v1 chỉ chấp nhận giá trị này
  sha256: <optional>
  media_type: <optional>
  size_bytes: <optional>
```

- UNC (`\\server\...`) hoặc `scope` khác → `400 file_scope_not_supported`.
- Path chỉ do Electron main đưa (sau native dialog); sidecar tin path từ main
  nhưng vẫn kiểm `scope` + tồn tại file.

## 7. Lifecycle nghĩa vụ

- Cold start: main poll `/healthz` tới 30s (PyInstaller cold ~3–6s, P1 đo).
- Restart: tối đa 3 lần, backoff 1s/3s/10s; hết → `engine_unavailable`.
- Shutdown: `/shutdown` rồi kill sau 3s nếu chưa thoát.
- Port conflict: instance 2 thoát với exit ≠0 → main báo lỗi, không nuốt.

## 8. Compatibility & migration

1. Field optional mới = backward-compatible.
2. Đổi nghĩa/kiểu/tên field, đổi enum status/waiting_on → tăng `v2`.
3. Deprecated field giữ ≥1 chu kỳ review + migration note trong changelog.
4. `v0.experimental` (POC): khác tên trạng thái (`completed`→`succeeded`),
   thiếu `progress/waiting_on/file_ref` — consumer nâng cấp explicit, không có
   fallback ngầm.
5. Zalo connector process: do **Python sidecar** spawn/quản (O4); connector
   nói chuyện với sidecar nội bộ, không qua contract này trừ khi expose lên
   shell qua command namespaced `zalo.*`.
6. Update app = thay thư mục; **không auto-update** trong G1-SM (O5).
7. Stack local OCR parked: không bundle; route liên quan trả
   `failed{code:engine_not_installed, retryable:false}` (O6).

## 9. Conformance checklist

Producer (sidecar) PHẢI:

- [ ] Bind chỉ `127.0.0.1`; reject Origin lạ; không CORS.
- [ ] Auth Bearer trên mọi endpoint trừ `/healthz`; token không lộ.
- [ ] Reject đệ quy key nhạy cảm ở §3; reject file_ref scope≠machine_local.
- [ ] `command_id` idempotent; terminal states không đổi lại.
- [ ] Không auto-Finalize; `waiting_on` đúng enum; error đủ 5 trường.
- [ ] Restart làm in-flight → `engine_restarted`.
- [ ] Log/diagnostics redact token, cookie, raw document, username trong path.

Consumer (Electron main) PHẢI:

- [ ] Giữ token trong memory main; không đưa renderer/preload/storage/log.
- [ ] Spawn sidecar port động + env token; poll healthz ≤30s; tôn trọng
      compatibility window.
- [ ] Mọi call renderer đi qua preload IPC allowlist có version — không có
      kênh renderer→sidecar.
- [ ] Retry chỉ khi `retryable:true`; hiển thị `next_action`.
- [ ] Không tự hoàn thành bước `waiting_user` (đặc biệt finalize).

## 10. Examples & validator

Valid/invalid examples: `contracts/g1/examples/` — kiểm tra bằng
`contracts/g1/validate_examples.py` (stdlib-only). Gate yêu cầu: mọi file
valid pass, mọi file invalid bị rule tương ứng reject với `expected_error`.

## 11. Changelog

| Version | Ngày | Thay đổi |
|---|---|---|
| v1 | 14/09/2026 | Publish đầu tiên sau owner duyệt spec P2; hợp nhất POC v0.experimental + production requirements (P2 spec) |

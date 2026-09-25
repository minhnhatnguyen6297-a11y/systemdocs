# SPEC — Electron core + DesktopCommand production cho G1 một máy (MIN-64)

> **Trạng thái: DRAFT — chờ owner duyệt (gate D2). Không code, không package
> production trong task này.**
>
> Phạm vi: app Electron đóng gói chạy **một máy Windows**, gọi engine Python
> thật qua DesktopCommand. Không LAN, không đa máy, không update server —
> những phần đó thuộc G1-LAN (MIN-76).
>
> Bằng chứng nền: `../G1_SINGLE_MACHINE_INVENTORY.md` (P0) và
> `../G1_SINGLE_MACHINE_COMPATIBILITY_MATRIX.md` (P1). POC:
> `upload_lab@f18a42f:poc/desktop_command/` — bằng chứng, không phải contract.
>
> Cập nhật phạm vi Zalo 24/09/2026: [spec chính](../../../notary_v2/docs/platform/zalo-document-inbox/spec.md)
> thay đích Zalo của bản nháp G1-SM này. Process model/packaging P1 bên dưới
> là bằng chứng cho helper legacy, không là yêu cầu đóng gói collector vào
> Electron. Module mới chạy thử trong repo local riêng trước, Windows server là
> bước sau; module sở hữu ảnh tạm và Qwen OCR. Máy chính Sync chữ thô/trạng thái
> OCR kèm nguồn, không nhận ảnh Zalo. Document Intake của Soạn hồ sơ chạy regex,
> ghép người-tài sản và nhóm hồ sơ tạm sau Sync để người dùng duyệt. Command
> cụ thể vẫn cần contract riêng.

## 1. Process model (đã chứng minh ở P1)

```text
┌─ Electron main (process.execPath, Node 20.18 trong app đóng gói)
│   ├─ window/navigation/file dialog/download/module registry
│   ├─ giữ sidecar token; spawn/kill helper; single-instance lock
│   └─ KHÔNG chứa business logic, KHÔNG chạm Playwright/DB
├─ Renderer (sandbox, contextIsolation, no nodeIntegration)
│   └─ UI thuần; chỉ gọi preload IPC allowlist
├─ Python sidecar (PyInstaller onedir exe, FastAPI @127.0.0.1)
│   ├─ toàn bộ engine: extract/scan/audit/word_engine/inheritance_engine/
│   │  OCR/DB SQLite; sở hữu Playwright thread duy nhất + Celery nếu cần
│   └─ /healthz + /v1/commands + /v1/jobs/{id} + /shutdown
├─ zalo_connector legacy trong phép thử P1 — ELECTRON_RUN_AS_NODE;
│   không là process model đích của Zalo theo MIN-89
└─ Playwright Chromium headed — con của Python sidecar; không nhúng
    web tỉnh vào Electron; không automate cửa sổ Electron
```

P1 evidence: packaged exe → spawn sidecar exe → healthz → engine thật →
exit 0 (`_scratch/g1-p1/electron-smoke/dist-app/`); lifecycle kill/restart/
shutdown/port-conflict đều PASS (`logs/lifecycle.json`).

## 2. DesktopCommand `v1` — request/result contract

Kênh: HTTP loopback `127.0.0.1:<port>` (port động, sidecar chọn + báo qua
stdout/handshake file — mục mở §7). Không CORS. Chỉ Electron main giữ token.

### 2.1 Request

```yaml
contract_version: "desktopcommand.v1"
command_id: <uuid v4 do client sinh>     # idempotency key
command: <namespaced, vd upload.prepare | upload.start_login |
          upload.confirm_login | upload.finalize | upload.cancel |
          notary.ocr_analyze | notary.case_save | ...>
payload: <object theo command; CẤM key credential/cookie/token/password/
          secret/storage_state (kiểm tra đệ quy như POC registry)>
client_meta: { shell_version: <semver>, module: <id> }
```

### 2.2 Job / status

```text
accepted → running → waiting_user → succeeded
   │          │           │
   │          │           └─→ (user xong → running tiếp)
   │          └─→ partial            # một phần thành công, phải nêu rõ
   └─→ failed | canceled             # canceled phân biệt user-cancel vs
                                    #   engine-shutdown (error.code)
```

```yaml
job_id: <server sinh>
command_id: <echo>
status: accepted|running|waiting_user|partial|succeeded|failed|canceled
progress: { done: n, total: m, current_label: "..." } | null
result: <object|null>               # chỉ khi succeeded/partial
error:  { code, message, retryable, next_action? } | null
waiting_on: login|review|finalize|confirm|null   # khi waiting_user
updated_at: <iso8601>
```

Endpoints tối thiểu: `GET /healthz` (kèm `supported_versions`),
`POST /v1/commands`, `GET /v1/jobs/{job_id}`, `POST /v1/jobs/{job_id}/cancel`,
`POST /shutdown`. Long-running: client poll `jobs/{id}` (SSE/WebSocket = mục
mở §7 — poll đã đủ cho một máy).

### 2.3 Semantics bắt buộc

- **Idempotency:** retry cùng `command_id` trả job cũ, không nhân đôi hành động
  (đặc biệt upload — không duplicate upload khi retry/cancel).
- **Cancel:** `cancel` chỉ được chấp nhận ở accepted/running/waiting_user;
  sidecar trả `canceled` với `error.code=user_canceled` hoặc `409` nếu đã
  terminal. Cancel không được tự Finalize.
- **Reconnect:** client crash → sidecar vẫn giữ job; client mới query theo
  `job_id`/`command_id` để nối lại. Sidecar restart → jobs in-flight chuyển
  `failed{code:engine_restarted, retryable:true}`; không giả vờ còn chạy.
- **Auth boundary:** Bearer token sinh ngẫu nhiên lúc sidecar start, chỉ nằm ở
  Electron main (env/memory); không vào renderer, URL, log, storage, payload.
- **waiting_user:** engine báo bước cần người (login tay, review, Finalize);
  shell hiển thị theo MIN-32 spec; shell không tự hoàn thành bước đó.
- **Structured error:** `code` snake_case có namespace (`upload.*`, `ocr.*`,
  `engine.*`); `message` cho người đọc; `retryable` bool; `next_action` gợi ý
  (`login_required`, `pick_files`, `retry`, `contact_admin`). Renderer không
  parse message để quyết nghiệp vụ.
- **Redaction:** không credential/cookie/raw-document trong log/payload;
  path trong log phải qua redaction helper (username mask) khi ghi diagnostics.

## 3. File reference có machine scope (đề xuất cho D0-7)

```yaml
file_ref:
  path: "D:/ho so/file.docx"          # absolute; cho phép dạng \\?\ prefix
  scope: machine_local                # G1-SM CHỈ chấp nhận giá trị này
  sha256: <digest nếu producer đã hash> # optional, dedup/verify
  media_type: <nếu biết>
```

Quy tắc đề xuất (owner chốt khi duyệt):

- `scope=machine_local` là mặc định và duy nhất trong G1-SM; UNC `\\server\...`
  hoặc `scope=lan_share` → sidecar từ chối `file_scope_not_supported` (G1-LAN
  mới định nghĩa). Xử `cases.py:780` UNC hardcode ở P6-B bằng config path local.
- Path >260 ký tự: engine dùng `\\?\` prefix nội bộ; Electron manifest khai
  `longPathAware` (finding F2).
- Sidecar **không** nhận file bằng đường dẫn tương đối hoặc path do renderer
  tự gõ — file do user chọn qua Electron dialog, main chuyển path tuyệt đối.

## 4. Auth, threat boundary

| Vùng | Trust | Quy tắc |
|---|---|---|
| Electron main | trusted host | giữ token, spawn helper, dialog, registry |
| Renderer | untrusted | sandbox; chỉ preload IPC có version; không token |
| Sidecar | semi-trusted local | bind 127.0.0.1; Bearer token; reject payload key nhạy cảm đệ quy |
| Renderer ↔ sidecar | **cấm trực tiếp** | renderer không fetch sidecar; mọi call qua main IPC |
| CSP | bắt buộc | meta CSP trong renderer HTML (finding F4); no remote content |

Single instance lock: instance 2 focus cửa sổ đang chạy, không spawn sidecar 2.
Port conflict → sidecar exit code ≠0, main detect + báo (đã chứng minh F-lifecycle).

## 5. Lifecycle

- **Start:** main spawn sidecar → poll /healthz (timeout 30s; PyInstaller cold
  start ~3-6s đo ở P1) → healthz trả `supported_versions` → kiểm compatibility
  window trước khi nhận command.
- **Restart:** sidecar crash → main restart tối đa 3 lần backoff (1s/3s/10s);
  hết → module `unavailable` + error `engine_unavailable` (không crash app).
- **Shutdown:** `POST /shutdown` (drain) → fallback `kill` sau 3s (đo ở P1).
- **App quit:** before-quit → stop sidecar + connector + Playwright (qua
  sidecar close); không để process con sống.
- **Update (một máy):** thay toàn bộ thư mục app; không auto-update server.
  Data (SQLite, storage_state, logs, output) nằm ngoài thư mục app tại
  `%APPDATA%/<app>` — update không động data. Auto-update = mục mở §7.

## 6. Packaging (đã chứng minh ở P1) + module registry

- `electron-builder --dir`/nsis; sidecar = `extraResources` onedir; golden/
  fixtures test-only không ship.
- `ELECTRON_MIRROR`/`ELECTRON_BUILDER_BINARIES_MIRROR` trong hướng dẫn build
  (finding F1 — GitHub release 32KB/s trên mạng hiện tại).
- Playwright browsers: `%LOCALAPPDATA%/ms-playwright` hoặc bundle
  + `PLAYWRIGHT_BROWSERS_PATH` — **F5 chưa đo**, follow-up P4/P7.
- Module registry (MIN-64): `upload`, `document-review` (notary), `excel-word`
  (merged vào document-review hay riêng — mục mở), `office` (placeholder
  "Chưa triển khai"), `search`, `status`, `settings`. Mỗi module: id, title,
  command namespace, capabilities.

## 7. Mục mở cần owner khi duyệt

| # | Câu hỏi | Đề xuất |
|---|---|---|
| O1 | File-ref policy (D0-7): chấp §3 không? | Theo §3 — machine_local only |
| O2 | Job events: poll `jobs/{id}` hay SSE? | Poll — đủ cho một máy, ít moving part |
| O3 | Port: động + handshake file hay cố định? | Động + token trong handshake; tránh đụng port |
| O4 | Ai spawn zalo_connector trong đề xuất G1-SM cũ? | Không còn áp dụng cho đích MIN-89: module chạy độc lập trong repo local riêng trước, server sau; Sync raw OCR/provenance, Document Intake xử lý chữ ở máy chính; command tương ứng cần contract riêng. |
| O5 | Auto-update trong G1-SM? | Không — portable/nsis replace; update tool là G1-LAN |
| O6 | OCR local parked trong package (D0-3)? | Đề xuất: route trả `engine_not_installed`; không bundle stack nặng |
| O7 | Tên contract: `desktopcommand.v1` OK? | Giữ hậu tố version riêng khỏi `v0.experimental` của POC |

## 8. Checklist nghiệm thu (MIN-64)

- [ ] Process model + threat boundary được duyệt.
- [ ] DesktopCommand v1: request/result/progress/waiting_user/cancel/
      reconnect/restart/idempotency/auth/error/file_ref/compat window đủ.
- [ ] Không embed web tỉnh; human Finalize giữ nguyên; không handler HTTP
      gọi Playwright trực tiếp.
- [ ] Module registry đủ 7 module; Office = placeholder.
- [ ] Packaging/update một máy + lifecycle + compatibility được duyệt.
- [ ] Runtime owner repo xác nhận = `systemdocs` branch `electron-system-shell`.
- [ ] Không có code trong spec task này.

# MIN-64 — Draft đặc tả UI chung và DesktopCommand

> **Trạng thái: DRAFT — chờ duyệt.**
>
> Tài liệu này chỉ mô tả vocabulary, boundary và tiêu chí quyết định UI ở cấp
> hệ thống. Nó không chọn Electron/PySide6 thay cho owner, không tạo HTTP
> production, không tạo UI code trong `systemdocs` và không thay đổi app đang
> chạy.

## 1. Mục tiêu và không nằm trong phạm vi

Đích thiết kế là một cửa UI chung có thể chứa các module Upload, Document
Review, Search, Status và Settings, trong khi Python engine vẫn sở hữu session,
Playwright, OCR và business rules. Một shell chung phải cho phép các repo dùng
cùng semantics và component/version sau khi có decision; không chỉ đổi màu ba
ứng dụng độc lập.

Không nằm trong phạm vi:

* tự chốt Electron hoặc loại bỏ PySide6;
* nhúng website tỉnh vào shell mặc định;
* rewrite toàn bộ `upload_lab` hoặc `notary_v2`;
* quyết định transport production, DB, auth identity hoặc package distribution;
* tạo component package/contract production trong task này.

## 2. Bằng chứng hiện trạng

### 2.1 `upload_lab` là UI PySide6 hiện hành

`UploadLabMainWindow` dùng `FluentWindow`, có các trang Audit Excel, Quét &
Upload, Cấu hình & Hệ thống và Nhật ký (`upload_lab_repo/ui_qt/main_window.py:77-162`).
UI phát signal cho login, preflight, download, prepare và close; worker xử lý
Playwright trong một Python thread riêng (`upload_lab_repo/ui_qt/main_window.py:77-116`;
`upload_lab_repo/ui_qt/workers.py:60-117,146-240`). Đây là boundary cần giữ khi
thử shell khác, không phải API production có sẵn.

### 2.2 DesktopCommand chỉ mới là POC sidecar

POC Electron khởi động FastAPI sidecar loopback, giữ bearer token ở main process,
renderer chỉ gọi qua preload IPC (`upload_lab_repo/.worktrees/desktop-command-poc/poc/desktop_command/electron/main.js:22-115`;
`upload_lab_repo/.worktrees/desktop-command-poc/poc/desktop_command/electron/preload.js:1-6`). Sidecar hiện có `/healthz`, `/v0/commands` và
`/v0/jobs/{job_id}` (`upload_lab_repo/.worktrees/desktop-command-poc/poc/desktop_command/server.py:41-68`). Đây là seam thí nghiệm, chưa phải
production API.

POC đã kiểm tra auth/sensitive-payload, queue fake-worker, duplicate command và
trạng thái `waiting_user`; scan mapping và restart/RSS browser chưa được chứng
minh (`upload_lab_repo/.worktrees/desktop-command-poc/docs/superpowers/specs/2026-09-11-desktop-command-poc.md:17-29`).
Số đo định hướng hiện tại là Electron 2.6 s/341.4 MiB process tree so với
PySide6 0.5 s/179.1 MiB một process, chưa apples-to-apples
(`upload_lab_repo/.worktrees/desktop-command-poc/docs/superpowers/specs/2026-09-11-desktop-command-poc.md:31-46`). Kết luận POC là `ITERATE`,
không phải chọn Electron.

### 2.3 `notary_v2` có web backend/frontend riêng

Backend hiện là FastAPI với template/static frontend (`notary_v2/main.py:60-64`;
`notary_v2/frontend/templates/base.html:1-10`). Đây là evidence có web UI của
repo, không chứng minh nó là shell chung hoặc có thể nhúng trực tiếp vào
Electron.

## 3. Vocabulary UI chung

### 3.1 Module và navigation

Shell chung (nếu được chọn) phải có các module logic sau; label/technology cụ
thể do consumer quyết định:

| Module | Trách nhiệm hiển thị | Không sở hữu |
|---|---|---|
| Upload | Chọn nguồn, chuẩn bị, trạng thái job, mở bước user login/finalize | Playwright session/business rule |
| Document Review | Xem raw/normalized/inferred, source refs và cảnh báo | Tự xác nhận thay người |
| Search | Tìm theo IdentityEvidence và filter trạng thái | Tự gộp Case khi ambiguity |
| Status | Job/progress/error/retry/reconnect | Quyết định retry vô hạn |
| Settings | Config được phép, diagnostics, provider/policy hiển thị | Lưu credential vào renderer/log |

Navigation phải giữ context module, `job_id`/`document_id` và deep-link source
ref khi chuyển trang. Không dùng URL website tỉnh làm identity UI.

### 3.2 Job và progress

UI chỉ hiển thị lifecycle chung, không ép enum nội bộ upload thành enum domain:

```text
accepted → running → waiting_user → completed
                       ├──────────→ partial
                       ├──────────→ failed
                       └──────────→ canceled
```

`waiting_user` là trạng thái cần người thao tác (login, review hoặc finalize),
không phải lỗi. `partial` phải nêu phần thành công/thất bại; `failed` phải có
error code; `canceled` phải phân biệt user cancel và engine shutdown nếu backend
biết được. Job response tối thiểu có `job_id`, `command_id`, `status`,
`updated_at`, `result|null`, `error|null`.

Enum này là display vocabulary; `upload_lab` vẫn giữ các status thật
`matched/extracted/prepared_dry_run/uploaded_success` ở domain của nó
(`upload_lab_repo/batch_scan.py:353-368,705-795`; `upload_lab_repo/playwright_uploader.py:81-83`).

### 3.3 Error và confirmation

Error object dùng mã ổn định, message cho người đọc, `retryable`, correlation/job
ID và next action tùy chọn:

```yaml
code: upload.session_expired
message: Phiên đăng nhập đã hết hạn
retryable: false
job_id: <id>
next_action: login_required
```

Renderer không parse message để quyết định nghiệp vụ. Credential, cookie, raw
document và token không đi qua log hoặc payload UI.

Confirmation phải hiển thị evidence/source refs, thay đổi trước/sau và actor;
chỉ thao tác explicit của người có quyền mới chuyển inferred → confirmed. Nút
Finalize không được tự bấm bởi shell, retry hay renderer.

## 4. DesktopCommand boundary

### 4.1 Experimental request

POC request có `contract_version`, `command_id`, `command`, `payload` và thời
điểm tùy chọn. Các command thử nghiệm là `start_upload`, `cancel_upload`,
`scan_document`, `get_status`; payload không được chứa credential/cookie
(`upload_lab_repo/.worktrees/desktop-command-poc/poc/desktop_command/registry.py:21-53`).

Semantics phải giữ độc lập transport:

```text
Shell → command request → Python engine queue
Shell ← job/status/result ← Python engine
```

HTTP loopback FastAPI chỉ là transport POC đã đo; production transport và auth
chưa được quyết định. Nếu đổi transport, semantics/request IDs/error phải giữ
được hoặc tăng version.

### 4.2 Ownership

| Lớp | Owner | Ranh giới |
|---|---|---|
| Shell/navigation | Runtime owner sau decision | Render, route, accessibility, display state |
| Preload/IPC hoặc adapter | Shell runtime owner | API hẹp, validate payload, không business logic |
| Command endpoint | Python app owner | Auth/session, enqueue, version/error |
| Browser/session | `upload_lab` hiện tại | Dedicated Playwright thread và manual login |
| OCR/conversion | Repo adapter đã được duyệt | Policy gate, provenance, provider abstraction |
| Confirmation/finalize | Domain workflow owner | Human action và audit |

Trong mọi phương án, shell không đọc DB trực tiếp, không truy cập cookie/browser
context và không gửi raw credential. Python engine không phụ thuộc vào component
rendering cụ thể.

## 5. Electron và PySide6 decision gate

### 5.1 Các phương án giữ mở

* **PySide6 shell tiếp tục:** chi phí tích hợp thấp nhất với `upload_lab`, nhưng
  cần chứng minh component/navigation dùng lại được cho module khác.
* **Electron candidate:** có thể làm cửa chung cho web technology, nhưng phải
  trả chi phí Chromium/sidecar và giữ main/preload/renderer boundary.
* **Hybrid chuyển tiếp:** shell mới gọi Python engine; UI cũ vẫn chạy rollback
  cho tới khi flow thật đạt acceptance.

Không phương án nào được gọi là đã chọn chỉ từ POC hoặc tên framework.

### 5.2 Evidence bắt buộc trước adoption

MIN-51/POC phải dùng protocol cold-start cố định và synthetic staging để đo:

1. startup tới cửa sổ usable;
2. idle RSS và active upload/browser RSS theo process tree;
3. restart/shutdown/sidecar disconnect và reconnect;
4. accessibility keyboard/screen-reader cho Upload + Review;
5. packaging/install/update và log redaction;
6. cùng một flow `start_upload → waiting_user → finalize/cancel`;
7. rollback về PySide6 hoặc adapter cũ.

Ngưỡng do owner chấp thuận; report kỹ thuật chỉ có thể kết luận
`review_required`, không tự ghi adoption.

## 6. Component reuse và conformance

Trước khi có runtime owner, chỉ cam kết reuse semantics:

| Component logic | Consumer cần chứng minh | Tiêu chí |
|---|---|---|
| Job/status/error display model | Upload + Document Review | Cùng field/error code/version, khác renderer được phép. |
| Confirmation/evidence view model | `notary_v2` + `notaryoffice` khi có runtime | Cùng source ref/raw-normalized-inferred-confirmed; không auto-confirm. |
| Navigation shell | Upload + Review trước | Một source component/version sau decision; không copy hai bản. |
| Command adapter | Electron/PySide6 consumer | Cùng idempotency/cancel/reconnect semantics; transport là adapter. |

Một component chỉ được gọi là shared code sau khi hai consumer thật chạy cùng
revision và conformance test. Cùng dùng Qt/React/Electron hoặc cùng tên field
chưa đủ.

## 7. Kế hoạch triển khai sau khi duyệt

### Gate A — Quyết định UI (MIN-51/MIN-64)

* Owner duyệt phương án shell và ngưỡng đo.
* Ghi lựa chọn công nghệ vào `TECH_STACK.md`, không ghi rải ở repo khác.
* Gán runtime owner và distribution; nếu chưa rõ, giữ candidate và không mở
  production API.

### Gate B — Contract và adapter

* Publish DesktopCommand request/result và UI view vocabulary từ draft sau khi
  MIN-62 được duyệt.
* Tạo adapter trong repo owner; Python engine/Playwright hiện tại không bị
  rewrite.
* Test offline auth/error/idempotency/cancel/reconnect; không dùng credential
  hoặc website tỉnh thật.

### Gate C — Lát cắt UI chung (MIN-67)

* Chọn Upload + Document Review làm lát cắt đầu.
* Dùng cùng component/version cho hai consumer; khác biệt nghiệp vụ nằm trong
  adapter/config, không fork source.
* Chạy synthetic staging, accessibility và rollback; human Finalize phải còn
  nguyên.

### Gate D — Mở rộng và consolidate

Chỉ sau khi Gate C đạt mới thêm Search/Status/Settings, nối DB contract MIN-63
và cân nhắc repo lớn. Không xóa PySide6, không embed website tỉnh, không đổi
transport production chỉ vì POC chạy được.

## 8. Checklist nghiệm thu

- [ ] UI module/navigation vocabulary được owner duyệt.
- [ ] Job/status/error/confirmation semantics không nhầm với enum upload nội bộ.
- [ ] Shell–Python boundary không lộ credential/cookie/DB/browser context.
- [ ] DesktopCommand version/idempotency/cancel/reconnect/error có acceptance.
- [ ] Electron/PySide6 được so sánh bằng cùng protocol và synthetic flow.
- [ ] Có ít nhất hai consumer dùng cùng component revision trước khi gọi là
      shared code.
- [ ] Upload + Review có accessibility, rollback và human Finalize test.
- [ ] Không có production API/UI code/package/migration trong `systemdocs`.
- [ ] MIN-51, MIN-57 và MIN-62 được duyệt trước MIN-67 implementation.

# Rollback runbook — quay về engine v1 trong notary_v2

Quy trình phục hồi khi module `zalo-intake` gặp sự cố không khắc phục được:
dừng module, bảo toàn dữ liệu chờ giao, trả listener về engine v1 trong
`notary_v2` (legacy vẫn còn nguyên cho tới MIN-101).

**Baseline đối chiếu:** snapshot monorepo `D:\systemdocs` @ commit
`67998868` (+ dirty docs tree) là trạng thái engine v1 ngay trước khi tách.
Repo module `D:\zalo-intake` @ `068ae58` là scaffold MIN-93 trước merge
MIN-103. Snapshot một chiều `D:\systemdocs\zalo\` do
`tools/export_snapshot.ps1` sinh — không sửa tay, không khôi phục ngược từ
snapshot sang source (chiều dữ liệu là `zalo-intake` → `zalo/`).

## 1. Nguyên tắc một listener (đọc trước mọi thao tác)

**Không bao giờ để hai listener cùng nghe một tài khoản Zalo** (CAP-01, và
v1 cũng chặn hai connector). Trước khi bật lại đường nào, đường kia phải
dừng hẳn.

Thứ tự bắt buộc khi quay về v1:

1. **Dừng connector process của module trước** — kill tiến trình
   `node connector/bin/run.mjs` do `connector_proc.py` spawn (module) hoặc
   dừng hẳn module `serve`. Kiểm tra không còn process node nào giữ
   `ZALO_CONNECTOR_STATE_ROOT`.
2. Sau khi chắc chắn connector module đã dừng, mới bật lại đường v1:
   `POST /zalo-inbox/api/connectors/start` trên backend notary_v2 (v1 spawn
   `zalo_connector/bin/run.mjs` với env riêng của nó).
3. Hai connector dùng **state root khác nhau** (module:
   `{runtime}/connector`; v1: `runtime/zalo_connector` trong notary) —
   session file không chia sẻ. Đăng nhập lại QR trên đường v1 là hành vi
   mong đợi, không phải lỗi.

## 2. Bảo toàn dữ liệu chờ giao trước khi dừng

Không xóa `runtime/` khi rollback. Các thư mục **phải sống qua restart** và
không bị rollback đụng vào:

| Đường dẫn | Chứa | Quy tắc |
|---|---|---|
| `runtime/packages/` | Gói `intake.raw-package.v1` đã công bố, **chưa ACK** | Bất biến; máy chính Sync lại sau. Xóa = mất dữ liệu chưa giao (CAP-12) |
| `runtime/outbox/` | Outbox chờ giao của module | Giữ nguyên qua restart |
| `runtime/connector/webhook-outbox/` · `download-queue/` · `unknown-source-queue/` | FileOutbox của connector — event/attachment chờ ACK (`sha256(key).json`) | Giữ; flush lại khi connector chạy lại |
| `runtime/zalo_intake.db` | journal_entries, sources, records, jobs, ocr_requests, packages, listener_sessions | Không xóa; `migrate` idempotent |
| `runtime/media/` | Media gốc tạm (168h lifecycle) | Không xóa tay; prune theo retention |
| `runtime/access.jsonl` | Audit log mọi mở file runtime | Giữ |

Nếu phải dọn dung lượng: chỉ xóa `runtime/media/` các file đã quá
`captured_at + 168h` theo đúng cơ chế prune — **không** xóa `packages/`,
`outbox/` hay DB.

## 3. Khôi phục module từ source

| Tình huống | Cách khôi phục |
|---|---|
| Repo `D:\zalo-intake` hỏng/mất | Clone/checkout lại repo nguồn (remote hoặc backup), rồi `git checkout <commit>`; `runtime/` không nằm trong git — giữ nguyên trên đĩa |
| Cần đúng baseline trước merge MIN-103 | `git checkout 068ae58` (scaffold MIN-93) — lưu ý connector chỉ là stub ở commit này |
| Chỉ có snapshot `D:\systemdocs\zalo\` | Copy ngược snapshot về một thư mục mới **chỉ để đọc/khôi phục file** — snapshot là flat copy không `.git`; dùng `SNAPSHOT_MANIFEST.json` (sha256 từng file, `source_commit`) để verify file đúng bản. Không biến snapshot thành working repo: clone lại source-of-truth nếu cần git |
| Schema DB lỗi | `python -m zalo_module.cli migrate` (idempotent). Reset sạch chỉ khi chấp nhận mất dữ liệu: xóa `runtime/` rồi migrate lại — **mất hết gói chưa ACK, journal, session** |

## 4. Session files — vị trí và cảnh báo

| File | Nơi | Nội dung nhạy cảm |
|---|---|---|
| `session.json` | `{ZALO_CONNECTOR_STATE_ROOT}` (default `runtime/connector/`) | cookie/imei/userAgent — **chiếm tài khoản hoàn toàn nếu lộ** |
| `account.json` | cùng state root | `connector_account_id` do module cấp |
| `generation.json` | cùng state root | `listener_generation` |
| `login-qr.png` | cùng state root | QR login tạm |

Toàn bộ `runtime/` đã gitignore và bị `tools/export_snapshot.ps1` loại trừ.
**Không bao giờ commit** session/state/outbox/media; không copy vào
snapshot; không gửi qua wire (contract cấm ảnh/path trong payload).

Quên session / cần đổi tài khoản: xóa `session.json` (hoặc set
`ZALO_CONNECTOR_FORCE_QR=1`) rồi login QR lại — đây là reset có chủ đích,
không phải lỗi của CAP-02.

## 5. Quy trình rollback chuẩn (checklist)

1. Ghi lại trạng thái: `python -m zalo_module.cli status`, kiểm
   `runtime/packages/` còn gói pending nào.
2. Dừng connector module (kill `node connector/bin/run.mjs` hoặc tắt serve).
3. Xác nhận không còn listener nào trên account (không có process node giữ
   state root).
4. Nếu máy chính cần dữ liệu ngay: để nguyên `runtime/` — gói chưa ACK vẫn
   serve được khi module chạy lại.
5. Bật lại v1: `POST /zalo-inbox/api/connectors/start` trên backend
   notary_v2; login QR lại trên state root của v1.
6. Khi quay lại module: làm ngược — dừng connector v1 trước, rồi start
   connector module.

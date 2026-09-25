# G1 — Chuyển nghiệp vụ thật sang vỏ Electron thống nhất

**Trạng thái:** owner chốt ngày 14/09/2026. **Goal Linear:** MIN-56.
**Nhánh runtime cấp hệ thống:** `electron-system-shell`; không merge runtime vào
`main` tài liệu trong G1.

## Kết quả phải đạt

Một ứng dụng Electron trên máy trạm Windows cho phép người dùng chuyển giữa
`notary_v2` và `upload_lab`, thực hiện nghiệp vụ hiện có bằng engine thật qua
LAN, theo dõi job, xử lý lỗi và khôi phục kết nối thống nhất.

- Electron là entrypoint và shell duy nhất của bản tích hợp.
- Python tiếp tục sở hữu nghiệp vụ; không viết lại sang Node chỉ vì đổi shell.
- `notaryoffice` chỉ có mục “Chưa triển khai”; chưa xây Sentinel/Hub.
- `excelTK` là dự án riêng, ngoài goal.
- G1 chuẩn hóa model, identity, provenance và quyền ghi; chưa chốt/gộp database
  vật lý. Chọn DB là gate riêng sau khi model ổn định.
- Đích monorepo có bốn module: `notary_v2`, `upload_lab`, `notaryoffice`,
  `zalo`. `shell` là hạ tầng Electron. Engine Zalo hiện vẫn trong `notary_v2`;
  chuyển sang repo độc lập và folder `zalo/` thuộc
  [MIN-103](https://linear.app/minhnotary/issue/MIN-103/migrate-engine-zalo-thanh-module-thu-tu-trong-repo-rieng-va-zalo),
  chưa thực hiện trong G1 này.
- Giữ UX hiện có khi phù hợp; chuyển đủ chức năng trước, redesign sau.

G1 không hoàn tất nếu Electron chỉ mở app cũ, chỉ chạy POC hoặc chưa chạy luồng
nghiệp vụ thật trên bản đóng gói qua LAN.

## Kiến trúc và interface bắt buộc

- Electron sở hữu window/navigation/file dialog/download/helper lifecycle.
- Renderer sandboxed, không Node integration; preload chỉ expose IPC allowlist
  có version.
- Helper Python xử lý file cục bộ và Chromium upload có human review.
- Backend LAN sở hữu dữ liệu nghiệp vụ, job dùng chung và xử lý tài liệu.
  Với Zalo, quyết định mới nhất ngày 24/09/2026 là làm module độc lập trong
  thư mục/repo local riêng trước (đề xuất `D:\zalo-intake`), chạy Windows server
  sau; chưa triển khai server ở giai đoạn này. Xem [Zalo Inbox spec](../../notary_v2/docs/platform/zalo-document-inbox/spec.md)
  và [draft MIN-89](../product/specs/2026-09-24-zalo-independent-intake.md).
  Module Zalo sở hữu connector/session/listener/journal, media tạm, nhận/chuẩn bị
  ảnh, Qwen OCR API, gói file raw và API OCR lại cho ảnh còn hạn; bàn giao chữ OCR thô,
  trạng thái và provenance qua giao diện trao đổi giữa hai repo. Soạn hồ sơ/
  Document Intake trên máy chính chạy regex, phân loại, bóc trường, ghép mặt
  giấy/người/tài sản và gợi ý nhóm, rồi cho người dùng kiểm tra/xác nhận trước
  khi đưa vào đầu vào soạn thảo. Module không chuyển ảnh về máy chính; ảnh
  xóa sau 168 giờ từ `captured_at`, raw chưa ACK phải giữ. Người dùng xem ảnh
  trên Zalo thật.
  Máy chính tự Sync khi mở, nối lại, theo chu kỳ hoặc bấm nút; HTTPS pull là đề
  xuất cho giai đoạn server. Contract kỹ thuật còn chờ duyệt; fallback nguồn
  thuộc MIN-90, giai đoạn sau. Runtime hiện tại chưa tách. Module có thể dùng
  DB/session/runtime riêng; DB nghiệp vụ chung của ba module còn lại không áp
  vào bot.
- Client không mở SQLite qua share mạng; truy cập qua backend owner.
- Module registry định nghĩa id, capability, version và health.
- DesktopCommand định nghĩa request/result, progress, `waiting_user`, cancel,
  reconnect, restart, idempotency, auth và structured error.
- Data model dùng source-qualified identity, provenance, confirmation state và
  write ownership.
- File reference phân biệt máy trạm/máy chủ; LAN auth khác token loopback.
- Contract được owner duyệt và publish trong task riêng trước consumer code.

## Các lát cắt triển khai

### G1.0 — Baseline và inventory

Ghi revision mọi nhánh đang phát triển; inventory màn hình, thao tác, I/O, job,
DB, quyền hệ thống, test và fixture. Mỗi chức năng được đánh dấu **chuyển / giữ
engine / ngoài phạm vi**, có owner, nguồn `file:dòng`, baseline test và lát cắt
tiếp nhận. Bảo toàn code/test/fixture cũ trước cutover.

### G1.1 — Tương thích và đặc tả production

Kiểm tra Windows packaging, Python/native dependency, `.doc/.docx`, Word export,
OCR worker, Chromium, Unicode, share mạng và quyền ghi. Hoàn tất MIN-64, phần UX
chuyển đổi của MIN-32 và contract G1 ở MIN-62/MIN-72. POC chỉ là bằng chứng.

**Gate:** ma trận tương thích, threat boundary, lifecycle và contract được owner
duyệt; contract và implementation không nằm cùng task.

### G1.2 — Electron foundation và navigation

Thực hiện MIN-65/MIN-67: single instance, app/helper lifecycle, module registry,
diagnostics redaction, version check và cấu hình server. Sidebar gồm Tổng quan,
`notary_v2`, `upload_lab`, `notaryoffice`. Đóng gói Windows sớm và chạy một
command read-only qua engine thật.

**Gate:** app mở không cần terminal; engine restart không treo shell; đổi module
không hủy job; IPC ngoài allowlist bị từ chối.

### G1.3 — Upload/Audit end-to-end

Chuyển chọn nguồn→scan/extract→review/edit; Excel→audit→queue; preflight→login→
điền form→human review/finalize→kết quả. Giữ parser và Playwright browser thread
ở Python. Qt còn lại phải ghi là chuyển tiếp; cửa sổ Qt ẩn không tính là migrate.

**Gate:** output khớp fixture; dry-run mặc định; không tự điền giá trị trống,
cướp focus hoặc upload trùng khi retry/cancel.

### G1.4 — notary_v2 đến đầu ra nghiệp vụ

Chuyển quản lý hồ sơ/đương sự/tài sản; document intake→OCR→review→confirm; Case
Workspace/thừa kế→Word export; Zalo Inbox và chức năng được chọn ở G1.0. Tái sử
dụng Jinja/static khi phù hợp, chỉ chỉnh integration cần thiết.

**Gate:** hồ sơ mẫu sinh Word đúng; dữ liệu chưa confirm không thành truth; job
OCR không mất khi đổi module. Với Zalo ở đích MIN-89: module độc lập với tài
khoản văn phòng sở hữu nhận ảnh và Qwen OCR; máy chính nhận raw/provenance rồi
chạy parser/ghép/nhóm Document Intake để kiểm tra/xác nhận và soạn thảo,
không tải/lưu ảnh Zalo. Module được làm trước ở repo local riêng; kiểm chứng
chạy server là bước sau. Không tính kết quả Zalo đã đạt gate này từ runtime
legacy chưa tách.

### G1.5 — LAN, model và đồng thời

Kiểm tra ít nhất hai máy trạm cùng backend; ownership job, concurrent update,
mất LAN, reconnect, version skew và command gửi lại. Áp dụng contract ở boundary
nhưng giữ mapping tới DB hiện hữu.

**Gate:** không ghi đè im lặng, nhận nhầm job hoặc sinh record trùng; model chung
được chứng minh mà chưa cần chọn DB engine.

### G1.6 — Debug, package và cutover bản tích hợp

Chạy parity theo inventory, packaged smoke và fault injection lifecycle/LAN.
Kiểm tra cài mới, update thử nghiệm, uninstall không xóa dữ liệu, backup/restore
và rollback. Electron thành entrypoint mặc định sau owner review. Giữ repo và
worktree legacy làm bằng chứng; loại bỏ trong task cutover riêng.

**Gate:** người dùng hoàn thành Upload/Audit và hồ sơ→Word trên bản đóng gói qua
LAN; không còn lỗi chặn hoặc nguy cơ sai/mất dữ liệu chưa được chấp nhận.

## Definition of Done

Mỗi lát cắt là issue/sub-issue riêng, có revision nguồn, contract, acceptance,
test evidence, rollback và review độc lập trước phần phụ thuộc. Kiểm tra tối thiểu:

- parity fixture không nhạy cảm và packaged smoke;
- mất LAN, crash, timeout, reconnect và duplicate command;
- đóng/chuyển module khi job chạy hoặc có dữ liệu chưa lưu;
- file hỏng, thiếu quyền, Unicode và download gián đoạn;
- IPC/navigation trái phép và secret trong log;
- hai client đồng thời, ownership và conflict handling.

G1 kết thúc ở shell dùng được cho nghiệp vụ thật trên LAN với model và ownership
nhất quán. DB chung, Office/Evidence, tính năng mới và redesign UI/UX là goal sau.

## Lộ trình sau G1

1. **G2 — Database vật lý:** ADR chọn engine, schema, migration authority,
   rehearsal, backup/restore và rollback.
2. **G3 — Phát triển tính năng:** capability mới theo spec; Office chỉ bắt đầu
   sau A1/A3/A4 và approval riêng.
3. **G4 — Redesign UI/UX:** design system, usability và accessibility dựa trên
   các luồng đã chạy.
4. **G5 — Ổn định:** pilot, sửa lỗi, performance, packaging/update và release.

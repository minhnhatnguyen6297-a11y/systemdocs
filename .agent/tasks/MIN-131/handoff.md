# Handoff — MIN-131

## Trạng thái khi bàn giao — 2026-09-28
**Xong — chờ review.** P8/MIN-131 (MIN-123): làm nhẹ hai màn Upload Lab theo
bộ giao diện chung đã duyệt (P4/MIN-127). Chỉ refactor renderer upload;
`state.js`/`client.js` **không đổi** — mọi semantics nghiệp vụ giữ nguyên.

## Commit
- `f82443a` docs(MIN-131): mở task record P8 — brief + progress + decisions
- `29295aa` feat(MIN-131): làm nhẹ 2 màn Upload Lab theo bộ giao diện chung
- `0fd4aa5` docs(MIN-131): progress + handoff P8

## File đã đổi
- `shell/src/renderer/upload/index.js` — bỏ `.ul-head` (h2+mô tả); notice
  dùng `.banner`/`.banner warn` + CTA `secondary sm` (giữ `.ul-login-confirm`
  hook); h3 'Job'→'Tác vụ'; `.slot` trên jobsBox giữ (e2e dump hook).
- `shell/src/renderer/upload/audit.js` — `.card`/`.card-body` + 1 row/ card;
  KPI `card ul-kpi` nhỏ (22px, bỏ tông màu); `.ul-meta` row (auditHead+stale
  `pill warn`); 2 `.audit-pane` + `.splitter-h` (kéo chuột + ↑/↓, guard
  `window.addEventListener` cho node test); `table.ul-grid`; `.ul-tbl-count`
  `N dòng`; `ul-invalid`→`err`+`aria-invalid`.
- `shell/src/renderer/upload/scan-upload.js` — ctx card 1 row; cfg card 1
  row nguồn+nhân sự + row tiến độ (2 `progress` riêng) + `.ul-note` muted;
  action card `ul-actions` nút `sm`; queue card `.card-head` đếm N/M +
  `.ul-queue-body` chứa reconcile/prepare-error/bảng; `table.ul-grid.
  ul-queue-grid` (min-width 760 cuộn ngang); path `.truncate-path` shared +
  `Mở` `.ul-open` ghost; checkbox class `cb`; td số class `num`.
- `shell/src/renderer/upload/upload.css` — viết lại toàn bộ theo token
  `:root`; chỉ scope `.upload-lab` + `ul-*`; `[hidden]` scoped giữ semantic
  ẩn (fix class-display thắng `[hidden]` UA); `.ul-badge*` style giống
  `.pill`; `.ul-error`/`.ul-reconcile` box inline err/warn; bảng `.ul-grid`
  sticky header/zebra bỏ → hover + trạng thái tông token.

## Button map cũ → mới (audit)
| Cũ (class) | Mới (class + vị trí) |
|---|---|
| `Kiểm tra môi trường` trần | giữ vị trí, mặc định (trung tính) |
| `Mở đăng nhập` trần | `secondary` |
| `Xác nhận đã đăng nhập` `primary` (card + notice) | card: `primary` giữ; notice: `ul-login-confirm secondary sm` |
| `Tải Excel từ Web` `primary` | `secondary` (primary duy nhất của vùng = Nạp) |
| `Chọn tệp Excel...` trần | trần (trung tính) |
| `Mở` `ul-open` | `ul-open` ghost nhỏ |
| `Nạp dữ liệu` trần | `primary sm` |
| Thử lại (errBox) trần | `sm` |

## Button map cũ → mới (scan)
| Cũ | Mới |
|---|---|
| `Đổi website…` trần | `sm` — đổi text "Sang tab Audit để đổi website" |
| `Chọn thư mục` trần | trần |
| `Bắt đầu Quét` `primary` | `primary sm` |
| `Cập nhật danh sách` trần | trần |
| `Dừng` `danger ul-stop` (nền đỏ) | `danger sm` (outline đỏ) |
| `Chọn/Bỏ chọn tất cả`, `Lọc số lỗi`, `Số thiếu trong Excel` trần | `sm` |
| `Upload file đã chọn (N)` `primary` | `primary sm` |
| `Tiếp tục…` trần | `secondary sm` |
| `Đóng browser upload` `danger` | `danger sm` |
| `Đối chiếu với sổ mới` `ul-reconcile-btn` | `ul-reconcile-btn secondary sm` |
| `Mở` trong bảng `ul-open` | `ul-open` ghost nhỏ (giữ) |

## States đã bao phủ (giữ nguyên logic, đổi skin)
- Chọn website/pendingWebsite (`banner` info "Đang đổi website…") —
  disabled khi busy; option disabled khi `status!=='available'`.
- waiting_user login/review → `.banner warn` + CTA trong `.ul-notice`;
  confirm card button `hidden` trừ khi `waitingBanner.on==='login'`.
- env_check passed/steps/error → `.ul-env` + `ul-badge-ok/warn/err`.
- download/audit/pick/audit lỗi → `.ul-error` inline trong `.ul-src-msg` /
  `.ul-site-err` + `Thử lại` khi retryable.
- KPI 4 giá trị; `auditHead` (website+range+audit_id); `auditStale` →
  `pill warn` (không che dữ liệu cũ); `metaRow` ẩn khi cả hai ẩn.
- scan: tiến độ quét/chuẩn bị riêng, sessLine tab-portal counts,
  scanSummary; queue selected-top, `ul-row-selected/open/reconcile/issue`;
  reconcile banner + nút; prepareError inline; 6 cột + path truncate +
  `title` đầy đủ + `Mở`/dblclick mở file.
- Đổi tab giữ DOM/scroll (`state.tabs`), selection/job/polling nguyên —
  `syncTbody` theo khoa, `acceptScopedResult` từ chối late result.

## Test
- `cd shell && node --test test/upload-state.test.mjs` — **19/19 pass**.
- `cd shell && node --test test/upload-routing.test.mjs` — **45/45 pass**
  (gồm: dúng 2 tab ARIA, DOM/scroll giữ qua đổi tab, syncTbody
  placeholder, confirm hidden khi không waiting, audit head/KPI hooks,
  reconcile banner, prepare-error, race stale_revision…).
- `python test/test_upload_workspace.py` — **27/27 OK**;
  `test_upload_workflow.py` — **22/22 OK**;
  `test_upload_recovery.py` — **16/16 OK** (sidecar unit, không đụng
  renderer — chạy để xác nhận không regression chuỗi tích hợp).
- `git diff --check` — sạch.
- Không sửa `state.js`/`client.js` → không cần `node --test test/*.test.mjs`
  full (đã chạy 2 file bắt buộc 64 test pass).

## Chưa verify / manual-check
- Chưa chạy `test_upload_e2e.py` (Playwright + app Electron thật + fake
  portal) — môi trường phiên này không có app build; các hook e2e dùng
  được giữ nguyên (`brief.md` liệt kê), nên e2e mong đợi pass như trước.
- Manual P9 cần: 1280×800/1366×768/1920×1080, Windows 125%/150%; Tab/
  Shift+Tab qua tab/splitter/nút; focus-visible; dialog; empty/scanning/
  error/waiting/continuation/reconcile/stale/tên-dài; đổi tab + module
  giữa lúc job chạy (selection/scroll/polling).
- Splitter `.splitter-h` kéo chuột chưa test trên DOM thật (handler guard
  `window.addEventListener`; node test không có window events).

## Điểm P9/MIN-132 cần biết
- Hook `ul-*` e2e dùng giữ nguyên — e2e selector không cần sửa; layout
  nội bộ đổi (card/row). Nếu e2e có selector cấu trúc sâu (`.ul-row` con
  của `.ul-card`) cần chỉnh — không thấy trong `test_upload_e2e.py` hiện.
- `.ul-notice` item giờ là `.banner(.warn)` + `span.grow` + nút — e2e
  select `.ul-notice .ul-login-confirm`/`button:has-text` vẫn đúng.
- `.ul-table-wrap` = vùng cuộn chứa tbody (không còn `.ul-scroll`).
- Module full-height: bảng flex fill viewport; khi tràn `#view` cuộn —
  scroll lưu theo tab trong `state.tabs` như cũ.
- `state.js`/`client.js` không đổi — P9 tiếp tục dùng state hiện có.
- `.agent/tasks/MIN-128/` (worker khác) KHÔNG đụng; các file dirty
  `notary_v2/*`, `shell/sidecar/notary_*` là của worker khác, không stage.

## File tạm đã dọn
- Không tạo file tạm nào ngoài `.agent/tasks/MIN-131/` (không scratch/log).

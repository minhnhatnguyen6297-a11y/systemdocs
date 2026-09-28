# Decisions — MIN-131

## 2026-09-28 — Giữ nguyên `state.js`/`client.js` (không sửa)
- **Chọn:** Chỉ refactor `audit.js`, `scan-upload.js`, `index.js`, `upload.css`.
- **Lý do:** Khảo sát cho thấy mọi semantics bắt buộc đã có sẵn: scope/late-result rejection (`acceptScopedResult`), stale audit (`auditStale`/`markAuditStale`), selection/reconcile/open-tab sets, tab persistence (`state.tabs`), polling self-chain (`maybePollSession`/`scheduleSessionTick`), prepareRetry stale_revision. Task là làm nhẹ UI — không có defect state nào được phát hiện.
- **Loại bỏ:** Thêm state cho splitter vị trí bảng audit — không yêu cầu persist qua session; flex + drag tại chỗ đủ dùng.
- **Nguồn:** spec_UI.md + đọc code state.js/client.js + 64 test mjs hiện hữu.

## 2026-09-28 — Giữ toàn bộ DOM hook `ul-*` mà test node/Python dùng
- **Chọn:** Đổi cấu trúc bên trong (card/row/table-wrap) nhưng giữ tên hook: `.ul-tablist`, `#ul-panel-*`, `select.ul-site`, `.ul-site-url`, `.ul-badge-slot .ul-badge`, `.ul-login-confirm` (cả trong `.ul-notice` lẫn audit panel), `.ul-env`, `.ul-src-msg .ul-error`, `.ul-audit-head`, `.ul-stale`, `.ul-kpi[data-kpi] .ul-kpi-v`, `.ul-table-wrap tbody`, `.ul-progress-label`, `.ul-reconcile*`, `.ul-prepare-error`, `tr.ul-row-reconcile`, `tr.ul-row-issue`, `.ul-date`, `.slot` trên jobsBox; giữ text nút nguyên văn (e2e `has-text`).
- **Lý do:** `test/upload-routing.test.mjs` + `test_upload_e2e.py` (Playwright) assert trên các hook này; đổi tên = phá test mà không lợi gì.
- **Loại bỏ:** Đổi `.ul-badge`/`ul-badge-*` sang `.pill`/`pill.*` trên element — e2e select `.ul-badge` trực tiếp; thay vào đó `.ul-badge` được style giống `.pill` trong `upload.css`.
- **Nguồn:** grep test files + brief.md hook list.

## 2026-09-28 — Bảng `.ul-grid` riêng thay vì dùng `table.grid` shared
- **Chọn:** `table.ul-grid` trong `.ul-table-wrap` (scroll riêng, border hairline) — copy mat-bang `.grid` nhưng đặt tên `ul-*`.
- **Lý do:** `table.grid` shared có `margin: 6px 0` và không có wrap scroll — audit cần hai vùng cuộn riêng chia chiều cao bằng splitter; queue cần `min-width` cuộn ngang. Đặt tên `ul-grid` giữ ranh giới sở hữu CSS rõ.
- **Loại bỏ:** Dùng `table.grid` + CSS override — vi phạm "không định nghĩa lại class không-tiền-tố".
- **Nguồn:** prototype `table.ul-grid` + DESIGN.md §10.

## 2026-09-28 — `.ul-error`/`.ul-reconcile` style inline thay `.banner err`/`.waiting-banner` shared
- **Chọn:** `.ul-error` (err-bg/ err-text), `.ul-reconcile` (warn-bg/warn-text) là `ul-*` box riêng; `.ul-notice` item dùng `.banner`/`banner warn` shared.
- **Lý do:** e2e/node select `.ul-prepare-error`, `.ul-reconcile`, `.ul-src-msg .ul-error` — giữ class; box inline đứng giữa form/table (không full-width banner).
- **Nguồn:** test hooks + spec §4 (lỗi inline tại vùng liên quan).

## 2026-09-28 — Bỏ header module + bỏ card titles; gom vào 1–2 hàng/card
- **Chọn:** Bỏ `.ul-head` (h2 + mô tả); card không tiêu đề (trừ queue "Hàng chờ (N · đã chọn M)"); audit: 1 card website (row: select+badge+env/login) + 1 card nguồn (row: ngày+tải+file+nạp) + KPI + meta row + 2 bảng + splitter; scan: card ngữ cảnh + card nguồn/nhân sự/tiến độ + card action + card queue.
- **Lý do:** Task "làm nhẹ": giảm giải thích, gom 1–2 thanh, bảng là vùng chính; rail icon + tab đã định danh module.
- **Loại bỏ:** Giữ h2 'Upload Lab' — trùng thông tin với rail/nav; e2e không select nó.
- **Nguồn:** prototypes/upload.js + EXPERIENCE.md (compact, data-first).

## 2026-09-28 — Nút chính/phụ theo prototype
- **Chọn:** `primary`: Nạp dữ liệu, Bắt đầu Quét, Upload file đã chọn, Xác nhận đã đăng nhập (trong card); `secondary`: Tải Excel từ Web, Mở đăng nhập, Tiếp tục, Đối chiếu, CTA banner; `danger` (outline): Dừng, Đóng browser upload; hành động trong bảng/action bar dùng `sm`; 'Mở' dùng `.ul-open` ghost nhỏ.
- **Lý do:** Một primary nổi nhất trong cùng phạm vi; nguy hiểm nhẹ = outline đỏ (không nền đỏ) — đúng DESIGN.
- **Nguồn:** prototypes/upload.js + DESIGN.md §10 (modifier shared).

## 2026-09-28 — `[hidden]` scoped rule trong upload.css
- **Chọn:** `.upload-lab [hidden] { display: none; }`.
- **Lý do:** `.ul-panel`, `.ul-reconcile`, `.ul-error`, `.ul-meta`, `.pill` đều set `display` (class specificity thắng `[hidden]` của UA) → element `.hidden` vẫn hiện. Rule scope phục hồi semantic ẩn mà không cần `!important`.
- **Nguồn:** phát hiện khi viết CSS — reconcile/prepErr/stale sẽ kẹt hiển thị nếu thiếu.

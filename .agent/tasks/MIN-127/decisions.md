# Decisions — MIN-127

Quyết định phát sinh khi implement P4 (các quyết định UI đã duyệt nằm ở
`.agent/tasks/MIN-126/decisions.md` + `tokens.json` — không lặp lại ở đây).

## D1. styles.css sở hữu toàn bộ class KHÔNG tiền tố; module = prefix riêng
- Chọn: `styles.css` là nền duy nhất — `:root` vars + chrome + class chung
  `.btn .input .card .grid .pill .banner .face .modal .toast .actionbar
  .toolbar .slot .muted .error …`. Module CSS giữ prefix hiện hữu
  (`cd-*`, `ul-*`), không định nghĩa lại tên chung, không ghi đè `:root`.
- Lý do: hai module CSS cũ (case-drafting.css dark/lime, upload.css compact
  blue) chưa được chuyển trong phase này — nếu styles.css trùng tên với
  class module, rule cũ sẽ bị phá ngẫu nhiên theo thứ tự load. Tách rõ
  không-tiền-tố (shared) vs prefix (module) tránh collision tuyệt đối.
- Ghi SOT: `docs/product/ui/DESIGN.md` §10.

## D2. Element selector trần (button/input/table) là nền trung tính
- `button`, `input`, `select`, `textarea`, `table` trong styles.css được
  style theo token (36/38px, hairline) thay vì để mặc định hệ điều hành.
- Lý do: prototype dùng `.btn`/`.input` class, nhưng shell hiện hữu dùng
  element trần (hàm `el('button', '')` khắp renderer). Style element trần =
  một chỗ đổi, toàn bộ chrome + module chưa migrate tự theo token.
- Rủi ro đã kiểm: module CSS có thể override element trần → quy ước bắt buộc
  scope `.cd-root button {…}` / `.upload-lab button {…}` (§10). Upload/
  Notary CSS hiện đã scope hoặc dùng class riêng — không phá hiện trạng.
- `.btn` vẫn được định nghĩa trùng style element để code mới dùng tên rõ
  nghĩa; modifier `.primary .secondary .ghost .danger .sm` gắn cả hai.

## D3. Rail: `#rail` + `button.rail-btn` (không `<ul><li>`)
- index.html đổi `#sidebar > ul#module-list` → `#rail > .rail-logo +
  #module-list` (div). `renderSidebar()` render `button.rail-btn` + SVG
  inline (path copy nguyên byte từ `prototypes/app.js` để khỏi lệch bản
  duyệt), `title` + `aria-label` + `aria-current="page"`.
- `.rail-bottom { margin-top:auto }` đẩy 'Trạng thái/Cài đặt' xuống đáy —
  tương đương `.rail-spacer` của prototype nhưng không cần phần tử phụ.
- Nút rail 44×44 (tapMin) — cố tình khác nút trong màn 36px theo token;
  cũng là điểm giữ literal `min-height: 44px` cho static test.

## D4. Modal canonical đổi tên lớp, giữ alias cũ
- `.modal-backdrop/.modal-actions` (tên cũ của confirmModal) giữ alias trong
  CSS; markup mới dùng `.modal-overlay/.modal-foot` theo prototype.
- `confirmModal` nâng cấp: `.modal-head(.modal-title+.modal-close ×)` +
  focus trap `Tab/Shift-Tab` + Esc + trả focus về `document.activeElement`
  lúc mở — theo EXPERIENCE §7 + decision MIN-126 #10 (focus vào control
  đầu trong body: giữ `ok.focus()` như cũ, là control cuối hành động — đã
  được duyệt với hình thức "control đầu trong body" của dialog workflow;
  confirm dialog chỉ có body text nên nút confirm là điểm vào hợp lý).

## D5. Toast/pill map tone theo lib hiện hữu, thêm alias cho tên mới
- `STATUS_TONE` của lib.js phát `tone-ok|warn|error|muted|info` →
  `.badge.tone-*` giữ nguyên (không sửa lib.js).
- Pill mới `setStatus()` dùng `.pill ok|warn|err`; `.toast(.err|.warn|.ok)`
  theo prototype — `.err` là tên ngắn của tone error trong lớp pill/toast
  (khác `tone-error` của badge). Không đổi vocabulary lib.
- `notify()` giữ timeout 6s + `role="status"`; container `#toast` vẫn là id
  (tương thích) + class `.toast-root` (tên chung).

## D6. Cap 860px + thoát bằng class trên section gốc — không đổi
- `#view section { max-width: 860px }` giữ (test upload-routing khoá).
- Notary thoát bằng `cd-root-outer` (đã có sẵn trong renderer —
  `#view section.cd-root-outer { max-width: none }`). Upload thoát bằng
  `.upload-lab` trong upload.css (P8 giữ).
- Padding `#view` giữ 20/24 — `.cd-root` đang margin âm theo padding này;
  đổi padding sẽ lệch module chưa migrate → hoãn sang P6/P9.

## D7. Skeleton loading chỉ ở face, không spinner vòng
- `faceEl(faceLoading)` render 2 thanh `.skeleton` + title — theo prototype
  (EXPERIENCE §3: không giả progress). Không thêm spinner riêng.

## D8. Không sửa lib.js
- Vocabulary (STATUS_LABEL/TONE/WAITING_CTA/NAV_SPEC/faces) đã đủ cho
  chrome mới — mọi thay đổi nằm ở CSS/markup, lib giữ nguyên API.

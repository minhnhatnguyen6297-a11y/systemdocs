# Handoff — MIN-127 (P4: nền giao diện + thành phần dùng chung Electron)

## Commit

| Hash | Nội dung | File |
|---|---|---|
| `694be2b` | mở task record | `.agent/tasks/MIN-127/{brief,progress}.md` |
| `0c8b3ed` | nền token + chrome + component chung | `shell/src/renderer/{styles.css,index.html,renderer.js}` |
| `db0d06c` | duyệt token + sở hữu CSS §10 | `docs/product/ui/{tokens.json,DESIGN.md,EXPERIENCE.md,README.md}` |
| `a391f7f` | trang mẫu component + đồng bộ approved | `docs/product/ui/prototypes/{components.html,README.md,index.html,prototype.css}` |
| `8c2bb4e` | progress + decisions | `.agent/tasks/MIN-127/{progress.md,decisions.md}` |
| (commit này) | handoff | `.agent/tasks/MIN-127/handoff.md` |

`lib.js` **không đổi** — vocabulary giữ nguyên. File ngoài sở hữu
(P5/P6/P7/P8) không đụng: `case-drafting-*.js/css`, `intake-dialog.js`,
`relationship-diagram.js`, `upload/*`, backend, `notary_v2/`, `upload_lab/`.
`.agent/tasks/MIN-128/` (worker P5) để nguyên untracked — không stage.

## Đã thay đổi (vùng shell)

- `styles.css` rewrite: biến `:root` = tokens.json approved (nền `#f4f6fa`,
  card trắng, accent `#2563eb`, radius 10/8/12, shadow mảnh, font 15px,
  button 36 / input 38 / row 36 / rail 60 / focus 2px offset 1). Xóa CSS
  chết `#sidebar .brand .biz-sec .kv-card`.
- `index.html`: `#sidebar>ul` → `#rail` (aria-label) + `.rail-logo` +
  `#module-list`; statusbar 3 pill. Thứ tự link/script giữ nguyên.
- `renderer.js` chrome-only: rail button icon SVG (path byte-exact từ
  `prototypes/app.js`), `button.rail-btn + title/aria-label/aria-current`;
  `notify()` → `.toast-root/.toast(.err)` role=status; `setStatus()` →
  `.pill ok|warn|err`; `faceEl()` skeleton; `confirmModal()` canonical
  `.modal-overlay>.modal.narrow` + focus trap + Esc + trả focus opener.
- Giữ nguyên hoàn toàn: `views` Map persistent + `scroll` save +
  `canLeave()` dirty guard, jobs/tracker/`submit`/`retryJob`/`confirmCancel`,
  `buildUploadView` delegate G1_UPLOAD, NAV_SPEC allowlist, `showModule`
  unmount-free (innerHTML swap trên `#view`, subtree module bền).

## Class/component P6–P8 dùng lại (SOT: DESIGN.md §10)

| Nhu cầu | Dùng |
|---|---|
| Nút | `button` hoặc `.btn` + `.primary .secondary .ghost .danger .primary.danger .sm`; dirty `.dirty-dot`; disabled `:disabled` |
| Ô nhập | `input/select/textarea` hoặc `.input`; lỗi `.err` + `aria-invalid` |
| Action bar màn | `.actionbar > .ab-back .ab-title select.input .pill .save-state .spacer button*` |
| Hàng nút trong vùng | `.toolbar` |
| Card | `.card > .card-head(.card-title+.card-tools) .card-body` |
| Bảng | `table.grid` (sticky thead, hairline, `tr.selected`); legacy `table.tbl` |
| Trạng thái | `.pill .ok/.warn/.err/.info/.accent` (alias `.badge.tone-*`); `.banner(.warn/.err/.ok)`, `.waiting-banner` |
| Mặt trạng thái | `faceEl()`/`.face.face-{loading|empty|error|unavailable}` + `.skeleton` |
| Dialog | tái dùng `deps.confirm`/`h.confirmModal` (overlay+trap+Esc+trả focus) — không tự viết overlay; class `.modal-overlay .modal(.narrow/.wide) .modal-head/.modal-body/.modal-foot` |
| Toast | gọi `notify(text, isError)` — không tự render |
| Kéo-thả | `.drag-handle .dragging .drop-hint .row-drop-above/.row-drop-below .col-drop-before` |
| Splitter | `.splitter-h` (row-resize) / `.splitter-v` (col-resize) + `.active` khi kéo |
| Tiện ích | `.muted .small .error .warn-text .num .truncate .truncate-path .icon-x .progress+.progress-lbl .kv/.kv-k/.kv-v .slot(unstyled marker)` |

Luật scope: element override của module phải nằm dưới `.cd-root`/`.upload-lab`
hoặc prefix `cd-*`/`ul-*`; không ghi đè `:root`; không tái định nghĩa class
không-tiền-tố ở trên.

## Vùng ĐÃ áp nền vs chưa (P6–P8 tiếp)

- **Đã áp**: chrome shell (rail, statusbar, view padding), trang Trạng thái/
  placeholder/Search/Engine-generic (job-card, conn, health), modal/toast/
  face/pill/banner dùng chung.
- **Chưa áp (cố ý)**: `notary/case-drafting.css` vẫn dark rail + lime accent
  (P6); `upload/upload.css` vẫn compact blue + `ul-*` (P8); diagram canvas
  (P7). Hai file này load sau styles.css nên giữ nguyên hiện trạng — nhưng
  element trần giờ đã có style token, nên vùng module chưa scope sẽ trông
  khác (đúng hướng chuyển, không vỡ).
- **Hoãn có chủ đích**: `#view` padding 20/24 — `.cd-root` margin âm theo
  nó; `#view section` cap 860px (Notary thoát `cd-root-outer`, Upload thoát
  `.upload-lab`).

## Kiểm chứng

- `cd shell && node --test test/*.test.mjs` → **197/197 pass** (baseline
  cũng 197). `node --check renderer.js` OK. `git diff --check` sạch.
- `git show --stat` 3 commit chính chỉ gồm file sở hữu.
- `components.html` + `styles.css` serve qua `python -m http.server` từ root:
  stylesheet resolve đúng, script so khớp class↔CSS pass (mọi class non-demo
  có rule; `face-empty/face-loading/rail-items` là tên semantic unstyled).
- Icon rail: 5 path SVG so byte-exact với `prototypes/app.js`.

### Đã kiểm trên trang component (server tĩnh)
- `components.html` + stylesheet serve 200; markup/màu render theo token
  (mở qua static server từ repo root — link tương đối resolve đúng).
- Inline JS demo modal/toast pass `node --check`; code cùng shape
  `confirmModal`/`notify` của renderer.
- Chưa click-tab thử modal/toast trong browser thật — cần người xác nhận
  qua preview (đã mở) hoặc P9.
### Chưa kiểm
- **DPI thật 125%/150% trên Windows** — chỉ mô phỏng CSS-pixel ở P3.
- **Chuột/bàn phím trong Electron thật** — chưa mở app Electron; focus ring,
  Tab-trap, Esc đã code theo pattern prototype nhưng cần P9 xác nhận tay.
- Screenshot visual-diff trang component (không có Playwright trong task).

## Rủi ro / việc cho worker sau

1. Module CSS cũ (P6/P8) load sau styles.css: rule element trần của chúng
   (nếu có) giờ chồng lên nền token — khi migrate, xóa element-trần khỏi
   module CSS hoặc scope vào class gốc.
2. `button` trong styles.css có `border + nền card` mặc định; module cũ có
   nút trần thiết kế không-viền sẽ hiện viền → P6/P8 chọn `.ghost` hoặc
   override scoped.
3. `.face` có `max-width:640px` — đủ cho face text; face trong panel hẹp
   tự co theo flex.
4. Toast `notify` vẫn 6s (spec retryable-error: toast ngắn + banner inline
   — banner inline thuộc module view, P6/P8 giữ theo EXPERIENCE §5).
5. `components.html` link `../../../../shell/src/renderer/styles.css` —
   tương đối từ repo root; nếu tách docs khỏi shell thì link chết (ghi lại
   khi restructure).
6. `.agent/tasks/MIN-128/` (P5) hiện untracked — worker P5 tự commit.

## Dọn dẹp

Không tạo scratch/log ngoài `.agent/scratch`. Preview server
(http.server :8137) là tiến trình phiên — dừng khi đóng; không file tạm.

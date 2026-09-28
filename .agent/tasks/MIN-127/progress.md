# Progress — MIN-127

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: phần chính xong, còn commit + handoff — 2026-09-28

## Đã làm
- Đọc toàn bộ nguồn: AGENTS.md, plan MIN-123, DESIGN/EXPERIENCE/tokens,
  prototypes (index/css/js), decisions MIN-126 (12 đề xuất = đã duyệt hết),
  visual-design hai module, spec_UI upload, code shell hiện trạng.
- Baseline test: `node --test test/*.test.mjs` @ 5f1de32 → **197/197 pass**.
- `tokens.json`: meta.status `proposed` → `approved` (v1.0.0, approvedBy
  owner qua bản mẫu MIN-126 27/09/2026).
- `DESIGN.md`: trạng thái approved, §9 ghi 7 quyết định đã chốt, **§10 mới** =
  sở hữu CSS + quy ước đặt tên cho P6/P7/P8.
- `EXPERIENCE.md` + `README.md` (docs/product/ui): approved + trỏ P4.
- `prototypes/`: index.html + README + prototype.css cập nhật marker
  proposed→approved; README ghi components.html.
- **`styles.css` rewrite hoàn toàn** (142 → ~570 dòng): token vars :root theo
  tokens.json; layout `#app/#rail/#module-list/#content/#statusbar/#view`;
  rail sáng 60px `.rail-logo/.rail-btn(44px)/.rail-bottom`; base button 36px +
  modifier `.primary/.secondary/.ghost/.danger/.primary.danger/.sm`; input
  38px + `.err`; `.pill(+tone) .badge.tone-*`; `.banner .waiting-banner`;
  `.card*`; `.actionbar .ab-* .toolbar`; `table.grid/table.tbl` giữ hairline +
  sticky header; `.face(.face-{kind}) .skeleton`; `.modal-overlay .modal
  (.narrow/.wide) .modal-head/.modal-body/.modal-foot(.modal-actions alias)`;
  `#toast/.toast-root/.toast(.err/.warn/.ok)` (+alias `.toast-item`);
  `.drag-* .drop-* .splitter-*`; `.progress`; `.dirty-dot`; `.truncate-path`;
  `.job-* .health-* .conn-card .kv .file-row .form-row .tools .files`;
  responsive @800px. Giữ nguyên: `#view section { max-width: 860px }`,
  `cd-root-outer` thoát cap, `min-height: 44px` (rail-btn), `:focus-visible`
  2px ring. Bỏ CSS chết: `.biz-sec`, `.kv-card`, `#sidebar`, `.brand`.
- `index.html`: sidebar `#sidebar>ul` → `#rail > .rail-logo + #module-list`
  (nav aria-label "Điều hướng chính"); statusbar 3 pill; thứ tự
  script/css giữ nguyên.
- `renderer.js` (chỉ chrome, không business):
  - `NAV_ICONS` = 5 path SVG **copy nguyên byte** từ prototypes/app.js
    (notary/upload/office/search/gear→status) + helper `railIcon()`.
  - `renderSidebar()` render `button.rail-btn` + `title`/`aria-label`/
    `aria-current=page` + `.unavailable` + `.rail-bottom` cho 'status'.
  - `notify()` → `.toast-root` + `.toast(.err)` role=status (giữ 6s timeout).
  - `setStatus()` → `.pill ok|warn|err` (engine-state).
  - `faceEl()` → skeleton bars cho face loading.
  - `confirmModal()` → canonical `.modal-overlay > .modal.narrow >
    .modal-head(title+×)/.modal-body/.modal-foot`, focus trap Tab, Esc đóng,
    trả focus về opener; nút ghost/primary.danger giữ nguyên nhãn.
  - Giữ nguyên: `views` persistent + scroll save + `canLeave()` guard,
    jobs/tracker, submit/retry/cancel, buildUploadView delegation, NAV allowlist.
- `components.html` mới: 11 mục demo (rail, button, input, pill/banner, card,
  actionbar/toolbar, table.grid, faces, modal+toast live, drag/splitter/
  progress, text util) link THẬT `../../../../shell/src/renderer/styles.css`
  + inline JS cho modal/toast. Verify class coverage bằng script: mọi class
  non-demo đều có trong styles.css.
- Test sau thay đổi: `node --test test/*.test.mjs` → **197/197 pass**.
- lib.js: không đổi (vocabulary/tone giữ nguyên — pill/banner tone đã map đúng).

## Đang làm dở
- Commit theo nhóm file nhỏ + handoff.md + decisions.md.

## Bước tiếp theo
1. `git diff --check`; `git status` (chỉ file sở hữu, không đụng staged của P5).
2. Commit nhóm: (a) styles.css+index.html+renderer.js, (b) components.html +
   prototypes marker, (c) DESIGN §10 + task record.
3. Viết decisions.md + handoff.md (commit hashes, class guide, test, giới
   hạn: chưa DPI thật, chưa manual mouse/keyboard trong Electron).
4. Đóng preview server + dọn scratch nếu có.

## Check đã chạy
- `node --test test/*.test.mjs` @ baseline → 197 pass (27.4s).
- `node --test test/*.test.mjs` sau thay đổi → **197 pass, 0 fail** (27.2s).
- `node --check renderer.js` → syntax OK.
- Script đối chiếu class components.html vs styles.css → chỉ face-empty/
  face-loading/rail-items là tên semantic unstyled (đã ghi chú trong CSS).
- SVG path 5 icon rail = byte-exact với prototypes/app.js (diff script).
- components.html + styles.css serve OK qua http.server 8137 (preview mở).

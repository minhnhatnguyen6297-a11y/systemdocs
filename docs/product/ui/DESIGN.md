# DESIGN — Ngôn ngữ thị giác chung cho shell Electron (MIN-124)

> **Trạng thái: APPROVED — owner duyệt toàn bộ đề xuất trên bản mẫu P3
> (MIN-126), 27/09/2026.** Hướng thiết kế đã được chốt bằng hai ảnh approved
> (`references/approved-drafting.png`, `references/approved-land-types.png`)
> và bản mẫu tương tác `prototypes/index.html`. Giá trị chuẩn ghi trong
> [`tokens.json`](./tokens.json) (`status: approved`); P4 (MIN-127) đã ánh
> xạ vào `shell/src/renderer/styles.css` — các mục "đang mở" ở §9 đã chốt
> theo bản mẫu (xem §10 cho phạm vi file/tên lớp).
>
> **Cập nhật MIN-133 (owner duyệt mockup 28/09/2026):** mật độ cao hơn cho
> màn data-heavy — nền app `#e9edf2`, card viền 1px `#dde3ea`, khoảng cách
> vùng 8 px, nút 32/28 px, hàng bảng 25 px, chữ dữ liệu 14 px, bỏ thanh
> trạng thái engine, nội dung module giãn hết chiều ngang. Ảnh chuẩn:
> `references/approved-drafting-v2.png`; token: `tokens.json` v1.1.0. Chi
> tiết ở §9.1. Các giá trị trong §2–§6 đã sửa theo đợt này.
>
> Phạm vi: thị giác dùng chung cho hai module nghiệp vụ (Notary + Upload
> Lab) và các mặt shell chung. Không định nghĩa hành vi/dữ liệu — đó là SOT
> của `drafting-tab.md` (Notary) và `spec_UI.md` (Upload). Cách thao tác
> chung → [`EXPERIENCE.md`](./EXPERIENCE.md).

## 1. Nguyên tắc thị giác

| # | Nguyên tắc | Nguồn căn cứ |
|---|---|---|
| V1 | **Trắng/xanh.** Nền app xám-xanh rất nhạt, card/surface trắng, điểm nhấn xanh primary. Không nền kem, không gam màu riêng theo vùng. | Ảnh approved + plan MIN-123 |
| V2 | **Vùng sáng phân biệt nhẹ.** Vùng con trong card chỉ đậm/nhạt hơn nền một chút; phân biệt bằng độ sáng và khoảng trắng, không bằng viền trang trí. | Ảnh approved: bảng/chip trong card dùng nền xanh-nhạt/xám-nhạt |
| V3 | **Bo góc, ít bóng.** Card/dialog bo 10–12 px; control bo 6–8 px; bóng chỉ cho lớp nổi (dialog, menu, toast). | Ảnh approved |
| V4 | **Đường chỉ khi cần.** Không viền trang trí quanh vùng con trong card; giữ đường lưới trong bảng dữ liệu và đường nối quan hệ trong sơ đồ vì chúng mang ngữ nghĩa. Ngoại lệ MIN-133: **card cấp ngoài cùng** có viền 1px `border.card` để tách khỏi nền app `#e9edf2` | Plan MIN-123; ảnh: bảng người/tài sản có separator, sơ đồ có đường nối; `approved-drafting-v2.png` |
| V5 | **Data-first, compact.** Chữ data đậm hơn nhãn; hành động gọn trên thanh riêng; không khối giải thích lâu dài trên màn chính. | Ảnh approved + plan |
| V6 | **Focus rõ.** Mọi phần tử tương tác có focus ring nhìn thấy được; selected khác focus. | Plan MIN-123; contrast rule |
| V7 | **Không sample-data hóa.** Lựa chọn trong ảnh approved là dữ liệu mẫu — không thành mặc định nghiệp vụ/fixture. | Ràng buộc MIN-123 |

## 2. Màu sắc (đề xuất → `tokens.json`)

Bảng dưới là tên token và **khoảng/gợi ý giá trị**; số hex chính xác lấy từ
`tokens.json` sau khi duyệt. Hiện trạng có ba bảng màu khác nhau
(`styles.css` `#f3f2f1/#0f6cbd`, `case-drafting.css` `#f3f4f8/#d9f76a`,
`upload.css` `#ffffff/#0067c0`) — đích là **một bảng chung**.

| Token | Vai trò | Đề xuất (khoảng) |
|---|---|---|
| `color.bg.app` | Nền cả app | `#e9edf2` (MIN-133; trước đó `#f4f6fa` quá gần trắng) |
| `color.bg.canvas` | Nền canvas sơ đồ, nằm trong card trắng | `#f5f7fa` + lưới chấm (MIN-133) |
| `color.surface.card` | Card/panel | Trắng `#ffffff` |
| `color.surface.subtle` | Vùng trong card, header bảng, input fill | Xám-xanh nhạt (`#f1f5fb`) |
| `color.border.hairline` | Đường lưới bảng, separator, viền mảnh | `#e2e8f0` |
| `color.border.card` | Viền 1px quanh card cấp ngoài cùng và mép rail | `#dde3ea` (MIN-133) |
| `color.text.primary` | Chữ chính/data | `#1f2937`–`#0f172a` |
| `color.text.muted` | Nhãn phụ, caption | `#64748b` |
| `color.accent.primary` | Nút chính, chip selected, focus | Xanh (`#2563eb`–`#1d4ed8`; đối chiếu `#0067c0` hiện hữu và `#0f6cbd` shell — chốt 1 giá trị) |
| `color.accent.soft` | Nền nút phụ, chip, dòng selected | `#e8f0fe`–`#dbeafe` |
| `color.state.ok` | Thành công | `#15803d` chữ trên `#e7f6ec` |
| `color.state.warn` | Cảnh báo / waiting_user | `#b45309` chữ trên `#fef3c7` |
| `color.state.error` | Lỗi | `#b91c1c` chữ trên `#fee2e2` |
| `color.state.info` | Thông tin | `#0369a1` chữ trên `#e0f2fe` |
| `color.focus.ring` | Vòng focus | `color.accent.primary`, 2 px |
| `color.diagram.edge` | Đường nối quan hệ | `#94a3b8`; selected `#2563eb` |
| `color.rail` | Thanh nav trái | rail sáng trắng `#ffffff`, icon `#334155`, active `#2563eb` — đã chốt §9.3; hiện trạng cũ rail tối `#121418`/`#201f1e` |

**Ngữ nghĩa tông** (giữ nguyên từ `lib.js` JOB_DISPLAY): informational = tông
xanh/trung tính; warning = `waiting_user`/`canceling`/`partial`; muted =
`canceled`; error = `failed`; success = `succeeded`. Không đặt màu khác cho
cùng một nghĩa ở hai module.

## 3. Chữ (đề xuất)

| Token | Đề xuất |
|---|---|
| `font.family` | `"Segoe UI", system-ui, sans-serif` (Windows-first, theo hiện trạng) |
| `font.size.base` | 15 px (đã chốt §9) |
| `font.size.data` | 14 px — chữ dữ liệu trong bảng, node, ô nhập tại chỗ (MIN-133) |
| `font.size.small` | 13 px — nhãn, header bảng, nút, caption |
| `font.size.chip` | 12 px — chip/pill/badge (MIN-133) |
| `font.size.cardTitle` | 15 px đậm 700 (MIN-133; trước đó 14 px/600) |
| `font.size.title` | 18 px (tên màn lớn) |
| `font.weight.regular/medium/semibold` | 400 / 500 / 600 — data & nhãn bảng dùng 500–600, caption 400 |
| `line.height` | 1.4 |

Số liệu bảng (diện tích, ngày) dùng chữ thường không cần tabular font ở P1 —
ghi nhận tùy chọn `font-variant-numeric: tabular-nums` cho cột số ở P4.

## 4. Kích thước & khoảng (đề xuất)

| Token | Đề xuất | Căn cứ ảnh |
|---|---|---|
| `size.input.height` | 38 px cho ô nhập form rời; ô nhập trong ô bảng theo chiều cao hàng | Ô nhập trong ảnh loại đất cao ~36–38 so với chữ 15 |
| `size.button.height` | 32 px; nút `sm` 28 px (MIN-133; trước đó 36 px) | `approved-drafting-v2.png` |
| `size.table.row` | 25 px (MIN-133; trước đó 36 px); ô nhập không nền/viền tới khi hover/focus | `approved-drafting-v2.png` |
| `size.card.head` | 34 px, padding `0 10px`; card body padding `0 10px 8px` | `approved-drafting-v2.png` |
| `space.gap` vùng / padding `#view` | 8 px / 8 px (MIN-133; trước đó 16 px / 20–24 px) | `approved-drafting-v2.png` |
| `size.tap.min` | ≥ 44 px vùng bấm logic — giữ cho nút rail | Giữ nguyên tắc accessibility hiện hữu |
| `space.scale` | 4 / 8 / 12 / 16 / 20 / 24 px | |
| `radius.card` | 10–12 px | |
| `radius.control` | 6–8 px | |
| `radius.chip` | 999 px (pill) hoặc 6 px | Chip `3 loại` trong ảnh là pill nhỏ |
| `shadow.dialog` | `0 8px 28px rgb(15 23 42 / .18)` | |
| `shadow.card` | `0 1px 2px rgb(15 23 42 / .06)` — mảnh, hoặc **không bóng** | Ảnh: card gần phẳng |
| `size.sidebar` | **60 px** — icon rail sáng (đã chốt §9.3, tokens `layout.sidebarWidth`/`color.rail`) | Ảnh vẽ icon rail sáng |

## 5. Layout chung (đích)

- **Nav trái** theo taxonomy MIN-104 (5 mục) — đã chốt **rail icon sáng
  60 px** (§9.3, owner duyệt 27/09/2026); không đổi thứ tự mục.
- **Vùng nội dung module** chiếm hết phần còn lại, giãn hết chiều ngang
  (MIN-133). Cap 860 px chỉ còn cho `<section>` con trực tiếp của `#view` ở
  trang shell (trạng thái/placeholder); section lồng trong module không bị
  cap.
- **Không có thanh trạng thái engine** trên đầu nội dung (bỏ `#statusbar`,
  MIN-133). Trạng thái engine + version + contract xem ở tooltip logo `G1`
  trên rail và module `Trạng thái`.
- **Thanh ngữ cảnh/thanh hành động** nằm trên đầu vùng nội dung của module,
  gọn một dòng, nút chính ở phải.
- **Card** là đơn vị nhóm duy nhất trong vùng nội dung; card cấp ngoài cùng
  có viền 1px `border.card`; card trong card không thêm viền — chỉ đổi nền
  subtle. Khoảng cách giữa các card 8 px.
- **Bảng** giữ đường lưới mảnh (`border.hairline`), header nền
  `surface.subtle`, sticky header khi bảng có vùng cuộn riêng.
- **Sơ đồ** giữ đường nối quan hệ; node là card nhỏ trắng trên nền canvas
  nhạt; đường nối chỉ mang ngữ nghĩa quan hệ, không trang trí.

## 6. Component pattern (đích, chi tiết module ở visual-design riêng)

| Pattern | Quy tắc chung |
|---|---|
| Nút primary | nền `accent.primary`, chữ trắng, bo `radius.control`; một màn tối đa 1 primary visible cùng lúc cho cùng phạm vi |
| Nút secondary | nền `accent.soft`, chữ `accent.primary` — như `+ Loại đất`, `Lưu sơ đồ` trong ảnh |
| Nút ghost/tertiary | không nền, chữ `text.primary`; hành động phụ, đóng |
| Nút disabled | mờ rõ (`opacity` hoặc màu muted), **không** tooltip giả lỗi; Zalo disable theo ràng buộc |
| Input | nền `surface.subtle` hoặc trắng, viền mảnh `border.hairline` chỉ khi hover/focus, bo `radius.control`, cao `size.input.height` |
| Bảng | header sticky + `surface.subtle`; dòng hover rất nhẹ; dòng selected `accent.soft`; đường lưới hairline |
| Card | trắng, `radius.card`, viền 1px `border.card`, head 34 px (padding `0 10px`), body padding `0 10px 8px` (card chỉ có body: thêm 8 px phía trên) |
| Dialog | trắng, `radius.card`, `shadow.dialog`, header có tiêu đề + `×`, footer nút phải-trái (primary phải), overlay mờ nhẹ |
| Banner/notice | viền trái hoặc nền tông state, một dòng gọn + CTA; `waiting_user` tông warn và **không** đỏ |
| Badge/pill | `accent.soft` nền, `accent.primary` chữ; số lượng (vd `3 loại`) |
| Chip chọn số (vị trí 1/2/3) | ô nhỏ ~24 px bo 4–6; selected = `accent.primary` nền + chữ trắng/`✓` | 
| Thẻ node sơ đồ | card mini trắng, tiêu đề tên đậm, dòng meta muted, hàng chip vai trò |
| Drag handle | icon `⋮⋮`/khai báo ARIA `role=button` + keyboard fallback (menu Gán vị trí) |
| Toast | góc dưới-phải, tông theo state, tự tắt với info/success |
| Zoom control sơ đồ | cụm `−`, `%`, `+`, `Mở rộng` ở mép canvas | 

## 7. Responsive & DPI (đích — check thật thuộc P3/P9)

Cửa sổ phải dùng được trọn vẹn ở ba viewport và hai mức scale Windows:

| Viewport | Kỳ vọng |
|---|---|
| **1280×800** | Mặc định tối thiểu đẹp: không clip nút chính, bảng có cuộn riêng; card Stage vẫn cạnh nhau (bảng chuyển vị tài sản cuộn ngang nếu thiếu chỗ) |
| **1366×768** | Phổ biến nhất: như 1280 với chiều cao hẹp hơn — vùng scroll của bảng/diagram co giãn, action bar không vỡ |
| **1920×1080** | Mở rộng vùng data (bảng/diagram) lấp khoảng trống; không căn giữa trang giấy |
| **DPI 125%** (logical 1280×800 → ~1024×640) | Font **không** thu nhỏ; thay vào đó vùng scroll co lại; bảng chuyển vị + queue 6 cột cuộn ngang; diagram pan/zoom vẫn đủ chỗ |
| **DPI 150%** | Như 125%, chặt hơn: kiểm tra không tràn nhãn tiếng Việt có dấu; text truncate thay vì vỡ layout |

Quy tắc chung:

- **Không shrink font** khi viewport/DPI co — chỉ co vùng cuộn, truncate
  chuỗi dài (đường dẫn file, tên), hoặc bật cuộn ngang cho bảng.
- Breakpoint đề xuất (hợp nhất ba hệ hiện hữu 1000/900/800): `≤1000 px`
  hai card Stage xếp dọc và bảng audit xếp dọc full-width; `≤800 px` giảm
  padding ngoài. Chốt chính xác ở P3.
- Tên dài/đường dẫn: `text-overflow: ellipsis` + tooltip xem đủ (khớp
  `spec_UI.md` §1).
- Sơ đồ lớn: pan + zoom (cụm control trong ảnh approved), không ép node
  nhỏ hơn kích thước đọc được.

## 8. Hiện trạng ≠ đích — các delta lớn cần ghi nhận

| Vùng | Hiện trạng (CSS đang chạy) | Đích |
|---|---|---|
| Palette shell | cream `#f3f2f1`, xanh `#0f6cbd`, viền `#e1dfdd` | trắng/xanh theo §2 |
| Palette Notary | rail đen `#121418`, accent lime `#d9f76a`, nền `#f3f4f8` | cùng palette chung; rail sáng 60 px đã chốt (§9.3) — đã triển khai |
| Palette Upload | `#0067c0`, radius 8 px, control ~30 px | hợp nhất token; kiểm lại chiều cao 36–40 |
| Stage Tài sản | form nhóm trường xếp dọc (`assetRowEl`) | **bảng chuyển vị** thuộc tính × cột tài sản theo ảnh — đã triển khai (P6/MIN-129) |
| Dialog loại đất | chưa tồn tại (land_rows inline) | dialog riêng theo ảnh — đã triển khai (P6/MIN-129) |
| Diagram node | nút `Chủ đất`/`Nhận` boolean | chip số theo vị trí tài sản — ngữ nghĩa đã chốt §13 v2, triển khai P7/MIN-130 |
| Sơ đồ toolbar | chưa có zoom | cụm zoom + `Mở rộng` overlay trong app — đã triển khai (P7/MIN-130) |

## 9. Quyết định thị giác — ĐÃ CHỐT qua bản mẫu MIN-126 (owner duyệt 27/09/2026)

Các mục mở trước đây đã được owner chốt khi duyệt bản mẫu
(`.agent/tasks/MIN-126/decisions.md` — "duyệt hết"):

1. `accent.primary` = `#2563eb` (bộ hover/pressed/soft theo `tokens.json`).
2. `font.size.base` = 15 px; `size.input.height` = 38 px; `size.button.height` = 36 px.
3. Rail nav = **icon rail sáng 60 px** theo ảnh approved (không sidebar nhãn).
4. Card dùng `radius.card` 10 px + bóng mảnh `shadow.card`.
5. Breakpoint = 1000 px (xếp dọc) / 800 px (compact) theo `layout.breakpoint`.
6. `Mở rộng` sơ đồ = overlay gần toàn màn trong app (Esc/× đóng, trả focus).
7. Zalo: **hiển thị disabled + tooltip**, không ẩn hẳn.

### 9.1 Cập nhật mật độ — owner duyệt mockup MIN-133 (28/09/2026)

Nguồn: `references/approved-drafting-v2.png` (gốc
`.agent/tasks/MIN-133/mockup/`), `tokens.json` v1.1.0. Mục này thay các giá
trị tương ứng ở §9 (2) và §9 (4):

1. `color.bg.app` = `#e9edf2`; `color.bg.canvas` = `#f5f7fa`; thêm
   `color.border.card` = `#dde3ea` (viền 1px card cấp ngoài cùng + mép rail).
2. `size.button.height` = 32 px, nút `sm` = 28 px; `size.table.row` = 25 px;
   card head 34 px; khoảng giữa vùng 8 px; padding `#view` 8 px.
3. Cỡ chữ: dữ liệu 14 px (`font.size.data`), nhãn/header 13 px, chip 12 px,
   tiêu đề card 15 px/700. `font.size.base` giữ 15 px; ô nhập form rời giữ
   38 px.
4. Bỏ `#statusbar` (engine/version/contract); thông tin chuyển vào tooltip
   logo `G1` và module `Trạng thái`. Polling trạng thái sidecar giữ nguyên.
5. `layout.contentMaxWidth` = không giới hạn cho nội dung module; cap 860 px
   chỉ áp cho section con trực tiếp của `#view`.
6. Tỷ lệ Stage Tài sản : Người = 35 : 65 (38 : 62 ở màn ≥ 1920 px); Pool
   176 px. Chi tiết màn `Soạn hồ sơ` thuộc visual-design của Notary.

## 10. Sở hữu CSS & quy ước đặt tên (P4 → P6/P7/P8)

`shell/src/renderer/styles.css` (MIN-127) là nền duy nhất của shell. Module
CSS load **sau** nó trong `index.html` (thứ tự: `styles.css` →
`notary/case-drafting.css` → `upload/upload.css`).

| Lớp | Sở hữu | Rule |
|---|---|---|
| Biến `:root` (`--bg-*`, `--surface-*`, `--border-*`, `--accent*`, `--fs-*`, `--btn-h(-sm)`, `--row-h`, `--gap`, `--view-pad`, `--card-pad-x`, `--card-head-h`, `--r-*`, `--sh-*`, `--rail-*`, state/`--dis-*`…) | `styles.css` | Module đọc thoải mái, **không ghi đè**; đổi giá trị phải qua `tokens.json` rồi đồng bộ `styles.css` (`prototypes/prototype.css` giữ v1.0.0 làm bản ghi MIN-126) |
| Layout chrome: `#app #rail #module-list #content #view`, `.rail-logo .rail-btn .rail-spacer .rail-bottom` (`#statusbar` đã bỏ ở MIN-133) | `styles.css` | Module không đụng |
| Class chung **không tiền tố**: `.btn .input .card .card-head/.card-title/.card-tools/.card-body .pill .badge(.tone-*) .banner .waiting-banner .face(.face-*) .skeleton .modal(.narrow/.wide/.modal-head/.modal-body/.modal-foot) .modal-overlay .toast(-root) .actionbar(.ab-*) .toolbar .grid(.tbl) .slot .tools .form-row .progress .dirty-dot .drag-* .drop-* .splitter-* .muted .small .error .warn-text .num .truncate(-path) .icon-x .kv(-k/-v) .job-* .health-* .conn-card .file-row .files .breakdown` | `styles.css` | Module **dùng lại**, không định nghĩa lại tên này |
| Class Notary `cd-*` | `notary/case-drafting.css` (P6) | Scope trong `.cd-root`; element override phải nằm dưới `.cd-root` |
| Class Upload `ul-*` | `upload/upload.css` (P8) | Scope trong `.upload-lab`; thoát cap `#view > section` bằng `.upload-lab` |

Quy ước:

- **Cap nội dung**: `#view > section { max-width: 860px }` — chỉ section con
  trực tiếp của `#view` (trang shell/placeholder). Module data-heavy thoát
  bằng class riêng trên `<section>` gốc: `cd-root-outer` (Notary) /
  `.upload-lab` (Upload, trong upload.css). Section lồng bên trong module
  (vd `section.cd-root`) không bị cap (sửa ở MIN-133 — trước đó
  `#view section` cap cả section lồng nên Soạn hồ sơ không giãn hết màn).
- **Element selector** (`button`, `input`, `table`…) trong styles.css là nền
  trung tính theo token. Module cần kiểu khác phải scope:
  `.cd-root button { … }` — tuyệt đối không viết `button { … }` trần trong
  module CSS (sẽ phá module khác).
- **Nút/ô nhập mới** dùng `button` + modifier (`.primary .secondary .ghost
  .danger .primary.danger .sm`) và `input` / `.input`; lỗi trường = `.err` +
  `aria-invalid`.
- **Trạng thái**: pill tông `ok|warn|err|info|accent` (alias `.badge.tone-*`
  cho code hiện hữu); banner `.banner(.warn/.err/.ok)` + `.waiting-banner`;
  dirty = `.dirty-dot` trên nút commit + nhãn text; loading = `.face
  .skeleton`; kéo-thả = `.drag-handle .dragging .drop-hint
  .row-drop-above/.row-drop-below .col-drop-before`.
- **Dialog** canonical: `.modal-overlay > .modal(.narrow|.wide) >
  .modal-head(.modal-title+.modal-close) / .modal-body / .modal-foot`;
  `confirmModal` của renderer đã implement focus trap + Esc + trả focus —
  module nên tái dùng `h.confirmModal`/`deps.confirm` thay vì tự viết overlay.
- **Toast**: `notify(text, isError)` của renderer → `#toast/.toast-root +
  .toast(.err|.warn|.ok)` — module gọi `notify` qua deps, không tự render.
- Tên mới nếu thiếu: thêm vào `styles.css` theo hướng không-tiền-tố
  (dùng chung) hoặc prefix module (riêng) — ghi vào handoff P4→P6–P8.
- Trang mẫu thành phần thật: `docs/product/ui/prototypes/components.html`
  (link trực tiếp styles.css).

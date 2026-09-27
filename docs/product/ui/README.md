# G1 Electron — UI dùng chung (MIN-124)

> **Trạng thái: ACTIVE — hướng thiết kế đã duyệt bằng hai ảnh tham chiếu
> (owner duyệt 27/09/2026 trong phiên MIN-123); giá trị token cụ thể trong
> `tokens.json` đang `proposed`, chốt sau prototype P3 (MIN-126).**

Thư mục này là **nguồn sự thật duy nhất cho lớp thị giác và cách thao tác
dùng chung** của hai module nghiệp vụ trong shell Electron một máy:
Notary (`notary_v2`) và Upload Lab (`upload_lab`). Pha P1 chỉ lập tài liệu —
chưa đụng CSS/runtime; CSS hiện hữu là hiện trạng, **không phải** đích.

## 1. File trong thư mục này

| File | Nội dung | Trạng thái |
|---|---|---|
| [`DESIGN.md`](./DESIGN.md) | Ngôn ngữ thị giác: màu, chữ, bóng, bo góc, kích thước, layout chung, component pattern | Proposed — chờ duyệt giá trị |
| [`EXPERIENCE.md`](./EXPERIENCE.md) | Cách thao tác chung: focus/bàn phím, mặt trạng thái, dialog, busy/waiting/cancel/dirty/conflict, responsive | Proposed — chờ duyệt |
| [`tokens.json`](./tokens.json) | Token đề xuất (đúp vai trò contract cho P4) | `status: proposed` |
| [`references/`](./references/README.md) | Hai ảnh thiết kế đã duyệt + metadata nguồn/ngày duyệt | Approved — chỉ tham chiếu thị giác |

## 2. Phân chia SOT — đọc file nào cho việc gì

| Cần | Đọc | Không đọc file này cho |
|---|---|---|
| Ngôn ngữ thị giác chung, token, layout shell | `DESIGN.md` + `tokens.json` | Ngữ nghĩa nghiệp vụ |
| Thao tác chung (trạng thái, dialog, focus, waiting) | `EXPERIENCE.md` | Bố cục riêng từng module |
| Hành vi/dữ liệu tab Soạn hồ sơ (Notary) | `notary_v2/docs/platform/case-workspace/drafting-tab.md` | Màu/kích thước/thị giác |
| UX cấp sản phẩm Notary (taxonomy, luồng, nút) | `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md` | Giá trị token (§3 của spec đó đã superseded) |
| Thị giác riêng Notary | `notary_v2/docs/platform/case-workspace/visual-design.md` | Wire shape command |
| Wire contract Notary | `contracts/notary-case-drafting.md` | Hành vi nghiệp vụ |
| Hành vi Upload Lab | `upload_lab/docs/spec_UI.md` | Thị giác/token |
| Thị giác riêng Upload Lab | `upload_lab/docs/visual-design.md` | Ngữ nghĩa nghiệp vụ |
| UX chuyển module + vocabulary trạng thái shell (draft MIN-32) | `docs/product/specs/2026-09-14-module-transition-ux-spec.md` | Hướng thị giác mới |
| Kiến trúc Electron | `docs/architecture/TECH_STACK.md`, `ELECTRON_G1_PLAN.md` | Màu/kích thước |

## 3. Ràng buộc đã chốt (áp cho mọi file dùng bộ thiết kế này)

- Ảnh approved là **tham chiếu thị giác**: mọi lựa chọn trong ảnh (tài sản,
  tên, ngày) là dữ liệu mẫu, **không** trở thành mặc định nghiệp vụ hay
  fixture. Xem `references/README.md`.
- Ngôn ngữ **trắng/xanh**: nền sáng xám-xanh, surface trắng, điểm nhấn xanh
  primary; **không** quay lại nền kem, **không** gam màu riêng theo vùng.
- Vùng sáng chỉ phân biệt nhẹ so với nền quanh; bo góc; **không** viền
  trang trí quanh vùng tổng quát; giữ đường lưới trong bảng dữ liệu và
  đường nối quan hệ trong sơ đồ.
- Focus rõ; thanh hành động gọn; không khối giải thích lâu dài trên màn
  chính; không popup báo thành công thường ngày hay popup "dạy cách dùng".
- Nút **Zalo** trong bản thật phải **disable** (ảnh vẽ chưa rõ ràng) — không
  tái giới thiệu UI Zalo, lệnh, hay trạng thái Zalo vào shell này.
- Electron vẫn là shell được duyệt; Python giữ nghiệp vụ/OCR/Playwright/DB/
  Word — thiết kế này không đổi ranh giới đó.

## 4. Bản đồ màn hình/trạng thái → file sở hữu

Bảng đầy đủ phân theo lớp. Cột "đích" là file bộ thiết kế này chi phối;
cột "hiện trạng" là code renderer hiện có (P1 chỉ đọc, không sửa).

### Lớp shell chung (module-agnostic)

Đường dẫn cột hiện trạng nằm trong `shell/src/renderer/` (trừ `main.js` ở
`shell/src/main/`).

| Màn hình / trạng thái | File sở hữu hiện trạng | File thiết kế đích |
|---|---|---|
| Frame, nav trái, statusbar, module switching | `shell/src/renderer/renderer.js`, `lib.js` (`NAV_SPEC`), `styles.css` | `DESIGN.md` §layout shell; `EXPERIENCE.md` §navigation |
| 4 mặt trạng thái (loading/empty/error/unavailable) | `lib.js` (`face*` helpers) | `EXPERIENCE.md` §faces |
| Vocabulary trạng thái job (idle…succeeded/partial) | `lib.js` (`JOB_DISPLAY`) | `EXPERIENCE.md` §status vocabulary (dẫn spec MIN-32) |
| Toast thông báo | `renderer.js` `notify()` + `styles.css` | `EXPERIENCE.md` §notifications |
| Confirm modal chung | `renderer.js` `confirmModal` | `DESIGN.md` §dialog; `EXPERIENCE.md` §dialog |
| Job running/progress/cancel tổng | `renderer.js` `renderJobs`, `jobCardEl` | `EXPERIENCE.md` §busy/cancel |
| Dirty-leave guard cấp shell | `renderer.js` `canLeave` + `main.js` close guard | `EXPERIENCE.md` §dirty |
| Màn Trạng thái/Cài đặt, env check, diagnostics | `renderer.js` `buildStatus` | `DESIGN.md` (ngoài phạm vi 2 module — style kế thừa shell) |
| Responsive/scroll shell-level | `styles.css` | `DESIGN.md` §responsive |

### Module Notary — tab `Soạn hồ sơ`

Tất cả đường dẫn cột hiện trạng nằm trong `shell/src/renderer/notary/`;
`visual-design.md` = `notary_v2/docs/platform/case-workspace/visual-design.md`.

| Màn hình / trạng thái | File sở hữu hiện trạng | File thiết kế đích |
|---|---|---|
| Tab cục bộ + khung màn | `case-drafting-view.js` (`TABS`) | `visual-design.md` §1 |
| Thanh ngữ cảnh hồ sơ | `case-drafting-view.js` `contextBar` | `visual-design.md` §6 |
| Stage — card Tài sản (form dọc hiện hữu) | `assetRowEl`, `landRowsEl` | `visual-design.md` §2 — đích bảng chuyển vị theo ảnh |
| Stage — card Người | `personRowEl` | `visual-design.md` §3 |
| Tray suggestion + lỗi intake | `suggestionTrayEl` | `visual-design.md` §7 |
| Pool | `relationship-diagram.js` (pool card) | `visual-design.md` §5 |
| Diagram node/edge/calc panel | `relationship-diagram.js` | `visual-design.md` §5 |
| Dialog nhập file | `intake-dialog.js` | `DESIGN.md` §6 + `visual-design.md` §7 |
| Dialog loại đất (theo ảnh approved) | *(chưa có — đích P3/P6)* | `visual-design.md` §4 |
| Dialog xuất Word | `word-export-dialog.js` | `visual-design.md` §7 |
| Dialog conflict (workspace_conflict) | `case-drafting-view.js` `conflictDialog` | `EXPERIENCE.md` §6 |
| Menu "Gán vị trí" (thay thế kéo thả) | `relationship-diagram.js` `openAssignMenu` | `EXPERIENCE.md` §2 |
| Modal shell + focus trap | `case-drafting-view.js` `openModal` | `EXPERIENCE.md` §7 |
| State/flag (dirty, locked, unsupported, stale…) | `case-drafting-model.js` | `drafting-tab.md` (SOT nghiệp vụ) |
| CSS module | `case-drafting.css` | `DESIGN.md` + `tokens.json` (P4 mới sửa) |

### Module Upload Lab

Tất cả đường dẫn cột hiện trạng nằm trong `shell/src/renderer/upload/`;
`visual-design.md` = `upload_lab/docs/visual-design.md`.

| Màn hình / trạng thái | File sở hữu hiện trạng | File thiết kế đích |
|---|---|---|
| Khung 2 tab + banner waiting_user | `index.js` `buildView`, `renderNotice` | `visual-design.md` §4 |
| Tab Audit (website/env/Excel/KPI/2 bảng) | `audit.js` | `visual-design.md` §2 |
| Tab Quét & Upload (source/staff/progress/queue) | `scan-upload.js` | `visual-design.md` §3 |
| State module (scope guard, tab persistence) | `state.js` | `spec_UI.md` (SOT hành vi) |
| Client/scope/versioning | `client.js` | `spec_UI.md` + contract |
| Bảng có sticky header, cuộn riêng, đường dẫn cắt gọn | `upload.css`, `audit.js`/`scan-upload.js` | `visual-design.md` §2–3 |
| CSS module | `upload.css` | `DESIGN.md` + `tokens.json` (P4/P8 mới sửa) |

### Dialog/window ngoài renderer (main-process owned)

| Màn hình | File sở hữu hiện trạng | Ghi chú |
|---|---|---|
| File open/save dialog | `shell/src/main/main.js` IPC pickFiles/saveDialog | OS-native, không restyle |
| Cửa sổ Chromium Playwright (login/review) | sidecar Python | Hệ thống song song; `EXPERIENCE.md` §waiting_user |
| Download/save-as | `shell/src/main/main.js` | OS-native |

## 5. Cách cập nhật bộ file này

- Giá trị token chỉ đổi `tokens.json` khi owner duyệt (kèm đổi `status`).
- Đổi ngữ nghĩa màn hình/trạng thái → sửa đúng file sở hữu trong §4, không
  nhân bản mô tả vào file khác.
- Khi một pha P2–P9 đổi hành vi → sửa SOT hành vi tương ứng (drafting-tab/
  spec_UI) **cùng commit** hoặc trỏ rõ sang nó; khi đổi thị giác → sửa
  `DESIGN.md`/`visual-design.md`.
- Ảnh approved mới: thêm vào `references/` + ghi hàng mới trong
  `references/README.md`; không ghi đè ảnh cũ.

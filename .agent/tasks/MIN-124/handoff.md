# MIN-124 — Handoff (P1: bộ file thiết kế + cách thao tác chung)

## Trạng thái

**DONE — documentation/reference-preparation only.** Không đụng runtime,
CSS, Python, contract. Commit trên `consolidate/monorepo`, không push.

## File đã tạo

| File | Nội dung |
|---|---|
| `docs/product/ui/README.md` | Chỉ mục + phân chia SOT + ràng buộc + **bản đồ màn hình/trạng thái → file sở hữu** (shell chung / Notary / Upload / dialog main-process) |
| `docs/product/ui/DESIGN.md` | Ngôn ngữ thị giác: nguyên tắc V1–V7, màu/chữ/kích thước đề xuất, component pattern, responsive+DPI, delta hiện trạng↔đích, quyết định mở §9 |
| `docs/product/ui/EXPERIENCE.md` | Thao tác chung: navigation/giữ state, bàn phím/focus, 4 mặt trạng thái, busy/waiting/cancel, dirty, conflict, dialog/toast, quyết định mở §10 |
| `docs/product/ui/tokens.json` | Token đề xuất — `meta.status: "proposed"`; **chưa wire runtime** |
| `docs/product/ui/references/approved-drafting.png` | Ảnh approved (1496×1051, byte-identical nguồn MIN-123) |
| `docs/product/ui/references/approved-land-types.png` | Ảnh approved (1631×964, byte-identical) |
| `docs/product/ui/references/README.md` | Metadata: nguồn, kích thước, phiên bản `approved-*` v1, ngày duyệt 27/09/2026, quy tắc "chỉ tham chiếu thị giác / dữ liệu mẫu cấm thành default" |
| `notary_v2/docs/platform/case-workspace/visual-design.md` | Thị giác/bố cục tab Soạn hồ sơ theo ảnh: action bar, bảng chuyển vị Tài sản, bảng Người, dialog Loại đất, Pool/Diagram + chip vị trí + zoom, responsive, delta P4/P6/P7 |
| `upload_lab/docs/visual-design.md` | Lớp thị giác bổ sung cho `spec_UI.md` (không phải spec song song): map token, từng tab, trạng thái, responsive, delta P4/P8 |

## File đã sửa (chỉ marker/route link, không đổi semantics)

| File | Thay đổi |
|---|---|
| `notary_v2/docs/platform/case-workspace/drafting-tab.md` | Thêm block MIN-124 phân lớp SOT; sửa mọi marker "MIN-105 chưa tồn tại/chờ chốt" → contract đã publish (`notary.case-drafting.v1`, rev 1.1 MIN-121); §10 điểm mở cập nhật (chip vị trí, Hủy thay đổi, Apply loại đất → chờ P2) |
| `notary_v2/docs/platform/case-workspace/README.md` | drafting-tab: DRAFT → đã duyệt; contract "chưa tồn tại" → đã publish; thêm `visual-design.md` + `docs/product/ui/` |
| `upload_lab/docs/spec_UI.md` | Block MIN-124 phân lớp (hành vi = file này, thị giác = visual-design.md); §6 thêm 2 dòng tài liệu |
| `upload_lab/README.md` | §4 dẫn thêm `docs/visual-design.md` + `docs/product/ui/`; giữ cảnh báo không spec song song (visual-design là phụ lục token) |
| `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md` | §3 bảng token cũ (rail đen + lime) đánh dấu **SUPERSEDED** → `docs/product/ui/`; lưu ý ảnh approved vẽ Tài sản dạng bảng chuyển vị (khác diễn giải 26/09) → xác nhận lại ở P3; sửa 2 marker "contract chưa tồn tại" |
| `docs/product/specs/2026-09-14-module-transition-ux-spec.md` | Header: file giữ vocabulary trạng thái shell (vẫn DRAFT); EXPERIENCE.md dẫn lại, không nhân bản |
| `contracts/README.md` | Thêm 2 hàng index `notary-case-drafting` (đã publish nhưng index thiếu); "ba contract nội bộ" → bốn |
| `README.md` (root) | Bảng "Đọc gì khi nào" thêm hàng `docs/product/ui/` |
| `shell/README.md` | Mục Navigation thêm dòng dẫn `docs/product/ui/`; nhấn mạnh CSS hiện hữu là hiện trạng, token wire ở P4 |

## Kiểm chứng đã chạy

- `python -c json.load` `tokens.json` → **OK** (9 top keys).
- Link checker tự viết quét 15 file md mới/sửa: **0 broken link** (relative
  links resolve đúng, kể cả `../../docs/product/ui/` từ `upload_lab/docs/`).
- `md5sum` 2 ảnh nguồn vs bản chép → **byte-identical**.
- `git status --porcelain` → chỉ file trong scope P1; không file
  runtime/CSS/Python/contract nào bị sửa nội dung nghiệp vụ.
- `git diff --check` → sạch.

## Chưa verify (ngoài phạm vi P1)

- Chưa chạy app/check thủ công màn hình (viewport 1280×800, 1366×768,
  1920×1080; DPI 125%/150%; keyboard nav, focus, dialog, drag/drop, Stage
  edit, diagram assign, giữ state Upload, stale-job) — đó là việc P3/P9.
- Giá trị token hex/px trong `tokens.json` là **proposed** — chưa duyệt.

## Quyết định đang chờ owner (đầy đủ: `docs/product/ui/DESIGN.md` §9 + `EXPERIENCE.md` §10 + `decisions.md`)

1. Hex `accent.primary` chính xác (`#2563eb` vs `#0067c0`) + tông phụ.
2. `font.size.base` 15/16; `inputHeight` 36–40; `radius.card` 10/12; bóng card.
3. Rail nav: icon rail sáng (ảnh) hay sidebar có nhãn (hiện trạng).
4. Ngữ nghĩa chip số `Chủ đất`/`Nhận đất` ↔ tài sản/vị trí; mô hình hai
   bên 30 vị trí; `position 16`; thả lên vị trí đã chiếm → **P2/P7**.
5. `Hủy thay đổi` semantics (phạm vi discard) → **P2**; tạm không render.
6. `Apply` dialog loại đất: draft hay commit Stage → **P2**.
7. `Mở rộng` sơ đồ: fullscreen hay modal → **P3**.
8. Ngưỡng breakpoint cuộn ngang/xếp dọc bảng chuyển vị + bảng 6 cột Upload → **P3**.
9. Zalo disabled: ẩn hẳn hay hiển thị mờ → **P3** (ảnh vẽ nút hiện hữu).
10. Toast lỗi retryable: tự tắt hay persist → **P3**.
11. Focus vào dialog: vào nút hay input đầu → **P3**.

## Việc tiếp theo (P2 = MIN-125)

- Contract dữ liệu cho Stage/assets/land types/inheritance/hai bên — đọc
  `drafting-tab.md` §10 điểm mở + `visual-design.md` §5 PENDING trước khi
  viết.
- Khi P3 làm prototype: lấy token proposed trong `tokens.json`, đổi status
  khi owner duyệt; ảnh/screenshot mới thêm vào `references/` kèm metadata.

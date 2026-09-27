# MIN-124 — P1: Chốt bộ file thiết kế và cách thao tác chung

> Task con của MIN-123 (thiết kế lại UI Electron chung cho Notary + Upload Lab).
> Pha P1 — chỉ tài liệu + tài nguyên tham chiếu; **không đụng runtime**.

## 1. Mục tiêu

Dựng bộ file thiết kế dùng chung theo hướng UI đã được owner duyệt (2 ảnh
approved trong MIN-123), phân tách rõ **hiện trạng / đích / chờ duyệt**, và lập
bản đồ màn-hình-và-trạng-thái → file sở hữu để P2–P9 làm việc không trùng nhau.

Kết quả phải giao được:

- Nguồn sự thật (SOT) hệ thống thị giác + thao tác chung tại `docs/product/ui/`.
- Token đề xuất (`tokens.json`) — **proposed, chờ owner duyệt**, chưa wire code.
- Hai ảnh approved lưu lâu dài tại `docs/product/ui/references/` kèm metadata
  nguồn/phiên bản/ngày duyệt.
- File thiết kế riêng cho từng module: `visual-design.md` ở case-workspace
  (Notary) và `upload_lab/docs/` (Upload Lab) — chỉ quy định thị giác/bố cục,
  không viết spec nghiệp vụ trùng.
- Đánh dấu hiện trạng/đích/chờ duyệt trong `drafting-tab.md` + `spec_UI.md`.
- Chỉ mục/spec cũ trỏ sang nguồn mới thay vì giữ hai bản quy định tương đương.
- Bảng màn hình/trạng thái → file sở hữu đầy đủ (shell, Notary, Upload, dialog,
  busy/waiting/dirty/conflict, responsive).
- Danh sách quyết định cần owner chốt trước P2/P3.
- Hướng dẫn responsive cho `1280×800`, `1366×768`, `1920×1080` + DPI 125%/150%.

## 2. Phạm vi

**Làm:** tạo/cập nhật tài liệu thiết kế theo bộ file trên; chép ảnh approved;
ghi bản đồ sở hữu; đánh dấu trạng thái; commit trên `consolidate/monorepo`.

**Không làm:** đổi CSS/runtime/Python/Word; đổi contract; thêm thư viện; vẽ
prototype hay chụp ảnh (P3); quyết định nghiệp vụ chưa chốt (đó là P2); push.

## 3. Ràng buộc thiết kế đã chốt

- Hai ảnh approved là **tham chiếu thị giác**; các lựa chọn trong ảnh
  (tài sản/người/ngày tháng cụ thể) là dữ liệu mẫu — **không** thành mặc định
  nghiệp vụ.
- Nút Zalo trong bản thật phải disable dù ảnh vẽ chưa rõ.
- Không quay lại nền kem; không dùng gam màu riêng cho từng vùng.
- Ngôn ngữ trắng/xanh; vùng sáng phân biệt nhẹ so với nền quanh; bo góc;
  không viền trang trí quanh vùng tổng quát; giữ đường lưới bảng dữ liệu và
  đường nối quan hệ; focus rõ; thanh hành động gọn; không khối giải thích
  lâu dài trên màn chính.
- Không tạo spec UI Upload song song — `upload_lab/docs/spec_UI.md` vẫn là
  SOT hành vi; `visual-design.md` chỉ là lớp thị giác.
- Electron vẫn là shell được duyệt; Python giữ nghiệp vụ/OCR/Playwright/DB/Word.

## 4. File liên quan

- Nguồn ảnh approved: `.agent/tasks/MIN-123/references/approved-*.png`
- SOT hành vi Notary: `notary_v2/docs/platform/case-workspace/drafting-tab.md`
- SOT UX sản phẩm Notary: `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md`
- Contract Notary: `contracts/notary-case-drafting.md` (không sửa ở P1)
- SOT hành vi Upload: `upload_lab/docs/spec_UI.md`
- SOT UX shell hiện hữu (draft): `docs/product/specs/2026-09-14-module-transition-ux-spec.md`
- Renderer hiện hữu: `shell/src/renderer/**` (chỉ đọc để lập bản đồ sở hữu)

## 5. Cách kiểm

- `tokens.json` parse được; đúng bộ file cho phép; ảnh chép byte-identical.
- Link tương đối trong các file mới/sửa đều tới được đích.
- `git status` sạch ngoài bộ file P1; `git diff --check` sạch.
- Không ghi đè spec hiện hữu; phần nào draft phải ghi draft.
- Không chạy check hiện trạng thủ công ở P1 — ghi rõ vùng chưa verify.

# Visual design — Upload Lab trong Electron shell (MIN-124)

> **Trạng thái: PROPOSED — chờ owner duyệt giá trị.** File này là **lớp
> bổ sung thị giác** cho [`docs/spec_UI.md`](spec_UI.md) — SOT duy nhất về
> **hành vi và bố cục vùng** của Upload Lab. Nó **không** phải spec song
> song: mọi quy tắc hai tab, bốn cột audit, giữ trạng thái, scope website
> vẫn lấy `spec_UI.md` làm chuẩn. File này chỉ quy định thêm **màu, chữ,
> kích thước, trạng thái thị giác** theo hướng trắng/xanh đã duyệt.
>
> Ngôn ngữ chung → [`../../docs/product/ui/DESIGN.md`](../../docs/product/ui/DESIGN.md) + `tokens.json`;
> thao tác chung → [`../../docs/product/ui/EXPERIENCE.md`](../../docs/product/ui/EXPERIENCE.md). Ảnh approved hiện
> chỉ vẽ màn Notary — Upload Lab áp dụng cùng hệ token; chi tiết bố cục
> của Upload sẽ có prototype riêng ở P3 (MIN-126) nếu cần.

## 1. Áp dụng hệ token chung

- Palette hiện hữu của `upload.css` (`#0067c0` primary, nền `#f8fafc`,
  viền `#e2e8f0`, radius 8 px) **đã gần** hướng trắng/xanh — đây là module
  ít delta nhất. Đích: map sang token chung (`accent.primary`,
  `surface.*`, `state.*`) thay vì màu cứng; giá trị hex cuối chờ duyệt
  (`DESIGN.md` §9).
- Radius card 8 px hiện hữu → chuẩn `radius.card` 10–12 px (chờ duyệt).
- Chiều cao control ~30 px hiện hữu → đề xuất `size.input.height` 36–38,
  `size.button.height` ~36; **giữ compact** — Upload là màn data-dense.
- KPI card (`ul-kpi`) giữ dạng 4 thẻ; chuyển tông sang `surface.card` +
  số `semibold` theo DESIGN §6, không gam màu riêng từng KPI.

## 2. Tab Audit Sổ Công Chứng — thị giác

(Bố cục/vùng theo `spec_UI.md` §2 — file này chỉ thêm lớp nhìn.)

- **Thanh website + env check**: một dòng gọn; trạng thái kết nối là pill
  nhỏ tông `state.*` (`ok` khi sẵn sàng, `warn` khi cần đăng nhập, `error`
  khi lỗi env) — không dùng đỏ cho "chưa đăng nhập".
- **Vùng nguồn sổ** (`Từ ngày`/`Đến ngày`/Excel): input `DD/MM/YYYY` cố
  định chiều rộng vừa đủ; đường dẫn file cắt giữa + tooltip (spec_UI §1).
- **KPI cards**: 4 thẻ ngang hàng, co giãn; giá trị to đậm, nhãn muted.
- **Hai bảng audit**: cùng full-width, xếp trên/dưới, kéo chia chiều cao
  được (spec_UI §2); header sticky `surface.subtle`, lưới hairline, dòng
  hover rất nhẹ; **không** đổi bốn cột `STT | Ngày | Số công chứng | Ghi chú`.
- Lỗi env/audit: banner `state.error` ngay dưới vùng liên quan — không
  modal cho lỗi đọc được chữa tại chỗ.

## 3. Tab Quét & Upload Hồ Sơ — thị giác

(Bố cục/quy tắc theo `spec_UI.md` §3.)

- **Context bar** (website + session): một dòng, phải có trạng thái
  session/remaining rõ — số còn lại là con số data, không phải badge
  trang trí.
- **Progress**: thanh tiến độ tông `accent.primary`; `waiting_user` của
  login/review hiện **banner warn** với CTA rõ (EXPERIENCE §4), không
  phải progress đỏ.
- **Bảng queue 6 cột** `✓ | STT | Ngày | Số công chứng | Ghi chú | Địa chỉ
  file`: cột `✓` hẹp cố định; cột `Địa chỉ file` lấy phần dư và truncate
  + tooltip + mở file gốc; header sticky; dòng selected `accent.soft`;
  trạng thái dòng (đã lưu/cần reconcile/lỗi) là pill tông `state.*`
  trong `Ghi chú` hoặc cột riêng — **chi tiết chờ P3**, không thêm cột
  thứ 7.
- **Action bar** (Lọc/Chọn thiếu/Upload/Đóng trình duyệt…): một dòng,
  primary chỉ một nút trong ngữ cảnh (Upload = primary khi có lựa chọn);
  nút phá hủy nhẹ (`Đóng trình duyệt`) là ghost/danger-outline.
- **Banner reconcile**: tông `warn`, inline ngay trên bảng, kèm hành động
  — không modal (spec_UI §5, EXPERIENCE §4).

## 4. Trạng thái dùng chung — map sang Upload

| Trạng thái | Trình bày trong module |
|---|---|
| Job đang chạy (scan/prepare/upload) | khối jobs của shell (`renderJobs`) + progress inline trong tab; nút `Hủy` có confirm |
| `waiting_user` login/review | banner warn + CTA `Xác nhận`/`Mở lại trình duyệt`; Chromium focus chỉ một lần chủ đích (spec_UI §5) |
| Lỗi vùng (env, tải Excel, scan) | box `state.error` inline tại vùng; `error.code` + message + retry theo contract |
| `partial` | breakdown đúng chỗ kết quả (bảng/summary), không toast thoáng |
| Tab đổi / module đổi | giữ form, chọn lọc, scroll, job — hiện trạng đã làm, giữ nguyên |
| Website đổi | reset theo `state.js` `setWebsite` — UI phải phản ánh sạch ngay (không lẫn dữ liệu website cũ) |
| Response job trễ/sai scope | hủy ngầm (`acceptScopedResult`) — không hiện lỗi vô cớ |

## 5. Responsive riêng Upload

- `≤1000 px` (đề xuất chung): hai bảng audit xếp dọc full-width (đã là
  dạng này — chỉ giảm khoảng chia); queue 6 cột **cuộn ngang** thay vì ép
  cột `Địa chỉ file`; KPI cards wrap 2×2.
- `≤800 px`: padding ngoài co lại; action bar wrap theo cụm.
- DPI 125%/150%: giữ nguyên cỡ chữ — vùng scroll bảng co; cột đường dẫn
  truncate sớm hơn; kiểm tra nhãn tiếng Việt có dấu không tràn.
- Không có yêu cầu đổi cấu trúc hai tab ở viewport hẹp — chỉ cuộn/wrap.

## 6. Hiện trạng → đích (delta cho P4/P8)

| Vùng | Hiện trạng (`upload.css` + `audit.js`/`scan-upload.js`) | Đích |
|---|---|---|
| Palette | `#0067c0`, `#f8fafc`, `#e2e8f0` — gần đích | map sang `accent.primary`/`surface.*` chung |
| Radius/height | card 8 px, control ~30 px | `radius.card` 10–12, input 36–38 (chờ duyệt) |
| KPI cards | QSS-like style riêng | `surface.card` + token |
| Notice/banner | `ul-notice` tùy biến | tông `state.*` chung |
| Trạng thái dòng queue | text/badge hiện hữu | pill `state.*`; chi tiết P3 |

## 7. Không thuộc file này

- Ngữ nghĩa nghiệp vụ, quy tắc bảng, scope website, dry-run/Lưu, waiting
  semantics → `spec_UI.md` + `contracts/upload-workflow.md`.
- Selector portal → `uploader_selectors.py` (theo README §4 repo con).
- Log/nhật ký → không có trang riêng (spec_UI §1) — thiết kế này không
  thêm lại.

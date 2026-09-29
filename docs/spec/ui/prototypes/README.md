# Bản mẫu tương tác — Notary & Upload Lab (MIN-126 / P3)

Bản mẫu **độc lập** (HTML + CSS + JS thuần, không framework, không build) để
owner duyệt **bố cục và tương tác** trước khi P4 implement vào Electron shell.

- **Dữ liệu giả hoàn toàn** (`data.js`) — deterministic, không random.
- **Không gọi** backend, Electron IPC, FastAPI, website cổng công chứng, Excel
  thật, hay Chromium thật. Mọi hành động "chạy" chỉ mô phỏng trong trang.
- Token màu/kích thước lấy từ `../tokens.json` **(status: approved — owner
  duyệt 27/09/2026)** ánh xạ tay vào biến CSS trong `prototype.css`.
- Toàn bộ đề xuất ở mục "Quyết định CHỜ CHỐT" dưới đây **đã được chốt** (duyệt
  hết qua `.agent/tasks/MIN-126/decisions.md`) — danh sách giữ lại làm record.
- Trang thành phần dùng chung của P4: `components.html` (link thật
  `shell/src/renderer/styles.css`).

## Mở / chạy

Cách nhanh nhất — mở file trực tiếp:

```
docs/spec/ui/prototypes/index.html
```

(không dùng ES module nên `file://` chạy được trên Chrome/Edge).

Hoặc qua static server:

```powershell
cd docs/spec/ui/prototypes
python -m http.server 8137
# mở http://localhost:8137/
```

## Thanh điều khiển bản mẫu (thanh tối trên cùng — KHÔNG phải UI sản phẩm)

| Điều khiển | Tác dụng |
|---|---|
| Module | Chuyển Notary ↔ Upload Lab |
| Loại việc / sơ đồ | Thừa kế (sơ đồ quan hệ) ↔ Hai bên (30 chỗ) |
| Kịch bản (Notary) | `3 tài sản·7 người` (gần ảnh duyệt) · `1 tài sản` · `Trống` · `30 người` · `60 người` (chứng minh không chặn 30) · `Tên dài & trùng` |
| Kịch bản (Upload) | `Có dữ liệu` (bảng dài, tên file dài) · `Chưa nạp` · `Nhiều trạng thái dòng` |
| Trạng thái | Cờ bật/tắt mặt trạng thái: Lỗi trường, Đang tải, Đã cũ, Xung đột, Đã khóa, Mock (Notary); Đang tải, waiting_user, Cần đối chiếu, Lỗi môi trường, Mock (Upload) |
| Khung nhìn | Mô phỏng cửa sổ: 1280×800 · 1366×768 · 1920×1080 · 1536×864 (≈1920 @125%) · 1280×720 (≈1920 @150%) |

## Bản đồ màn / trạng thái

### Notary — Soạn hồ sơ (`module = notary`)

| Vùng | Có gì |
|---|---|
| Action bar | `‹` quay lại, select Loại việc, pill mã hồ sơ, nhãn "Đã lưu/Có thay đổi", **Nhập file**, **Zalo (disabled — cố ý)**, **Hủy thay đổi** (chỉ bật khi dirty), **Cập nhật/Lưu hồ sơ** (primary) |
| Stage — Tài sản | Bảng **chuyển vị**: cột = tài sản, hàng = thuộc tính; kéo `⋮⋮` hoặc **Ctrl+←/→** đổi thứ tự cột; chip `n loại ↗` mở **dialog Loại đất** |
| Stage — Người | Bảng dòng: họ tên, ngày sinh/mất, giấy tờ, địa chỉ; kéo `⋮⋮` hoặc **Ctrl+↑/↓** đổi thứ tự; `×` xóa (draft); khay gợi ý intake nằm dưới bảng |
| Splitter ngang | Kéo (chuột hoặc focus + ↑/↓) đổi chiều cao Stage ↔ sơ đồ |
| Sơ đồ thừa kế | Pool trái (thẻ compact, lọc tên) — **kéo thẻ vào slot/node**, nút `→` = "Gán vị trí" cho bàn phím; kéo node↔node/node↔slot = đổi chỗ; kéo về Pool = bỏ gán; `− 100% +` zoom; `Mở rộng` = overlay toàn màn; splitter dọc đổi Pool↔canvas; footer `Lưu sơ đồ` + `Xuất Word` (stub — giữ đúng vị trí nút) |
| Sơ đồ hai bên | Hai cột Bên A (chỗ 1–15) / Bên B (chỗ 16–30), card = Chỗ N + tên + năm; kéo thả như thừa kế; cuộn dọc khi đủ chỗ |
| Dialog Loại đất | Một cột/thửa × loại đất + diện tích + thời hạn; `+ Loại đất`; **Áp dụng/Hủy** (draft riêng — Hủy không đụng Stage); Esc đóng, focus trả về chip mở |
| Node | Tên + năm sinh–mất + 2 hàng chip số **Chủ đất / Nhận đất** (✓ = chọn; *đề xuất*: số = thứ tự cột tài sản) |

### Upload Lab (`module = upload`)

| Tab | Có gì |
|---|---|
| Audit Sổ Công Chứng | Website + phiên đăng nhập + "Kiểm tra môi trường"/"Mở đăng nhập"; khoảng ngày + nguồn Excel (tải từ web/chọn tệp); 4 KPI; **hai bảng dọc tách được**: Số còn thiếu / Số lỗi-trùng (splitter kéo bằng chuột hoặc ↑/↓) |
| Quét & Upload Hồ Sơ | Context (website + nguồn sổ), chọn thư mục, CCV/Thư ký, số tab mỗi đợt, 2 thanh tiến độ, banner **waiting_user** + **cần đối chiếu**, thanh thao tác (chọn/bỏ chọn, lọc lỗi, "Số thiếu trong Excel", Upload đã chọn, Tiếp tục N số, Đóng browser), **bảng hàng chờ 6 cột** với pill trạng thái + đường dẫn dài cắt đầu (`…\Scan\HS_0012.pdf`, tooltip full) |
| Chuyển tab | Hai panel luôn mounted — **giữ trạng thái + vị trí cuộn** |

### Trạng thái — ở đâu xem

| Trạng thái | Cách xem |
|---|---|
| Empty | Kịch bản `Trống` (Notary), `Chưa nạp` (Upload) |
| Lỗi trường | Cờ `Lỗi trường`; hoặc `Lưu hồ sơ` ở kịch bản Trống (validate thật) |
| Loading | Cờ `Đang tải` |
| Dirty | Sửa ô bất kỳ → chấm trên `Cập nhật` + nhãn "Có thay đổi chưa cập nhật" |
| Conflict | Cờ `Xung đột` (dialog không có nút ghi đè) |
| Waiting user | Cờ `waiting_user` (Upload) |
| Disabled | `Zalo` luôn disabled; cờ `Đã khóa` khóa toàn Stage; nút phụ thuộc ngữ cảnh (VD `Tiếp tục N số` chỉ bật khi waiting) |
| Mock | Cờ `Mock` → banner MOCK trên đầu module |
| Selected vs focus | Dòng queue chọn = nền accent nhạt; focus = vòng viền 2px — khác nhau rõ |

## Kích thước / DPI đã kiểm

Chụp headless bằng Playwright (Chromium, `device_scale_factor` mặc định) —
ảnh trong `.agent/tasks/MIN-126/screenshots/`:

| Kích thước CSS-pixel | Tương đương | Kết quả |
|---|---|---|
| 1366×768 | laptop phổ biến | bố cục giữ, bảng cuộn trong card |
| 1280×800 | cửa sổ nhỏ | giữ 2 cột Stage, bảng cuộn ngang/dọc |
| 1920×1080 | desktop | tận dụng chỗ rộng, sơ đồ thoáng |
| 1536×864 | ≈1920 @125% scale | như 1366–1920, không vỡ |
| 1280×720 | ≈1920 @150% scale | chật hơn nhưng cuộn được, không co font |

**Giới hạn DPI:** chưa chạy Windows scale 125%/150% thật — hai dòng trên chỉ
mô phỏng *không gian CSS-pixel tương đương*. Cần owner mở thật ở scale 125/150%
để xác nhận crispness (text/SVG đều vector nên kỳ vọng ổn).

Quy tắc đã áp: **không co font** để nhồi — vùng dữ liệu cuộn ngang/dọc;
text dài cắt `…` + `title` tooltip; node sơ đồ giữ cỡ tối thiểu đọc được.

## Tương tác đã kiểm chứng (script `.agent/scratch/p3_test.py`, 18/18 PASS)

kéo Pool→node / Pool→slot hai bên · kéo node↔node đổi chỗ (swap) · "Gán vị
trí" bằng bàn phím · Ctrl+↑/↓ reorder dòng Người · Ctrl+←/→ reorder cột Tài
sản · splitter ngang/dọc (chuột + phím) · zoom +/− · Mở rộng overlay (Esc
đóng, trả focus) · dialog Loại đất (focus vào trong, Esc trả về chip) · chuyển
tab Upload giữ chọn/cuộn · hai bảng audit chia chiều cao · 60 người không
chặn · focus-visible 2px.

## Khác biệt có chủ đích vs 2 ảnh approved

Ảnh `references/approved-drafting.png` + `approved-land-types.png` định hướng
thị giác; bản mẫu **giữ bố cục** nhưng:

- Thanh demo trên cùng là công cụ duyệt, không phải UI sản phẩm.
- Dữ liệu là tưởng tượng hoàn toàn (yêu cầu "không sample-data hóa" — dữ liệu
  ở đây là trang trí để duyệt layout, không phải mặc định nghiệp vụ).
- `Xuất Word` giữ vị trí nút nhưng chỉ mở stub — **không** thiết kế popup mới.
- `Zalo` hiển thị **disabled** (xám + tooltip), không ẩn hẳn.
- Node thừa kế: thêm nút `×` góc + `⋮⋮` handle để demo kéo/xóa — ảnh approved
  chưa vẽ chi tiết tới mức này.
- "Mở rộng" render là overlay gần-toàn-màn (đã duyệt qua prototype).

## Giới hạn của bản mẫu

- Dữ liệu giả, tính trong RAM; reload = reset.
- Không lưu trữ, không đồng bộ đa phiên (conflict chỉ là dialog demo).
- Edge sơ đồ vẽ đơn giản (bus dọc + ngang), không phải engine layout thật.
- "Số tab mỗi đợt", "Lọc số lỗi", sắp xếp queue… chỉ mô phỏng quy tắc.
- Icon rail: SVG vẽ tay, chưa phải bộ icon chốt.
- Không có screen-reader pass đầy đủ — mới đảm bảo label/focus cơ bản.

## Lịch sử quyết định từ bản mẫu

Các đề xuất dưới đây đã được owner chốt qua MIN-126/MIN-132 ngày 27–28/09/2026;
spec hiện hành nằm ở [`../README.md`](../README.md), contract v2 và các spec
feature. Bản mẫu không phải SOT.

- Chip `1/2/3` bám vị trí cột tài sản; thả vào slot có người thì swap.
- `Hủy thay đổi` khôi phục cả Stage và Diagram draft về committed.
- `Áp dụng` Loại đất chỉ sửa Stage draft; `Cập nhật` mới commit.
- `Mở rộng` là overlay gần toàn màn trong app.
- Rail sáng 60 px; breakpoint 1000/800 px; token trong `tokens.json` Approved.
- Hai bên: A=`p1..p15`, B=`p16..p30`.
- Dialog focus control đầu và trả focus khi đóng; toast lỗi retryable tự tắt,
  trạng thái còn lại giữ inline.

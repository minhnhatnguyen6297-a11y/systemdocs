# Thiết kế thị giác — tab Soạn hồ sơ (Notary, Electron)

> **Trạng thái: PROPOSED — chờ owner duyệt giá trị; hướng đã duyệt qua ảnh
> 27/09/2026.** File này chỉ quy định **thị giác và bố cục** của tab
> `Soạn hồ sơ`. Hành vi/dữ liệu (Stage/Pool/Diagram, revision, suggestion,
> `case_type`) là SOT của [`drafting-tab.md`](./drafting-tab.md); UX cấp
> sản phẩm (taxonomy, luồng, bảng nút) là
> `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md`;
> wire contract là `contracts/notary-case-drafting.md`.
>
> Ngôn ngữ chung (màu, chữ, token, component, responsive) →
> `docs/product/ui/DESIGN.md` + `tokens.json`; thao tác chung →
> `docs/product/ui/EXPERIENCE.md`. File này **chỉ giữ phần riêng của
> Notary**, không chép lại quy tắc chung.
>
> Ảnh chuẩn: `docs/product/ui/references/approved-drafting.png`
> (toàn màn) và `approved-land-types.png` (dialog loại đất).

## 1. Bố cục màn hình (đích, theo ảnh approved)

```text
┌──────────────────────────────────────────────────────────────┐
│ Thanh trên (tab cục bộ + hành động, MIN-133 D4/D5):          │
│   [Tổng quan] [Soạn hồ sơ] │ [Thừa kế ▾] [Nhập file]        │
│   [Zalo*] [Hủy thay đổi] [●Cập nhật]                        │  ← một dòng, primary phải
├───────────────────────────────┬──────────────────────────────┤
│ TÀI SẢN  (~35%)               │ NGƯỜI  (~65%)                │
│ bảng CHUYỂN VỊ:               │ bảng dòng 7 cột (Customer):  │
│   dòng = thuộc tính           │   ⋮⋮ | Họ tên | Ngày sinh |  │
│   cột = Tài sản 1 · 2 · 3     │   Giới tính | Ngày mất |      │
│   (+ Tài sản ở header)        │   Số giấy tờ | Ngày cấp |     │
│   ô "Loại đất" → chip mở      │   Địa chỉ · Để lại (+Người)   │
│   dialog loại đất             │   KHÔNG thanh cuộn riêng —   │
│                               │   nhiều dòng → trang cuộn    │
├──────────┬───────────────────────────────────────────────────┤
│ POOL     │ SƠ ĐỒ THỪA KẾ  — head: [+Slot][Cách tính][Đánh giá]│
│ 176px    │   [−100%+][⛶ Mở rộng] | [Lưu sơ đồ][Xuất Word]    │
│ thẻ người│ canvas: node cards + đường nối quan hệ            │
│ kéo được │ node đã gán 144px: tên · năm sinh–mất · chip      │
│          │   Chủ [1][2][3]   Nhận [1][2][3]                  │
│          │ node trống 88×24 viền đứt — không chữ             │
└──────────┴───────────────────────────────────────────────────┘
```

\* Zalo giữ **disabled** trong bản thật (ràng buộc MIN-123).

Mật độ/tỉ lệ theo mockup MIN-133 đã duyệt (28/09/2026 —
`docs/product/ui/references/approved-drafting-v2.png`): Stage 35:65
(38:62 ở ≥1920), Pool 176px, một thanh trên gộp tab + hành động (bỏ «quay
lại», tiêu đề, pill Nháp), `Lưu sơ đồ`/`Xuất Word` nằm trong header vùng
sơ đồ (không còn footer), bảng Người 7 cột đúng cột DB `Customer` (bỏ ô
`Nơi cấp`/`Nguyên quán` khỏi UI — trường vẫn giữ trên wire), bảng Stage
không có thanh cuộn riêng (dữ liệu vượt màn → cả trang cuộn, D8).

Tỉ lệ 36/64 và 22/78 giữ từ spec UX §3 đã được thay bằng tỉ lệ MIN-133 ở
trên; thay đổi so với spec UX là **dạng
bảng** của hai card Stage — spec UX ghi "form nhóm trường xếp dọc" (diễn
giải 26/09), còn ảnh approved 27/09 vẽ **bảng chuyển vị cho Tài sản** và
**bảng dòng cho Người** → theo nguyên tắc "nguồn mới hơn và đã duyệt
thắng", đích là hai bảng; xác nhận lại bằng prototype P3.

## 2. Stage — card Tài sản (đích)

- **Bảng chuyển vị**: cột đầu là nhãn thuộc tính (`Số serial`,
  `Số vào sổ`, `Thửa đất`, `Tờ bản đồ`, `Loại đất`, `Địa chỉ`…); mỗi cột
  sau là một tài sản (`Tài sản 1`, `Tài sản 2`, …).
- Cột tài sản có thể cuộn ngang khi nhiều tài sản; header cột có `×` xóa
  (draft UI, xem EXPERIENCE §7) và nhãn `+ Tài sản` thêm cột.
- Ô `Loại đất` hiển thị **chip số lượng + `↗`** (vd `3 loại ↗`) — bấm mở
  **dialog loại đất** (§4); không nhập trực tiếp danh sách parcel trên
  bảng.
- Ô nhập là input nền `surface.subtle`, không viền mạnh; lỗi field-level
  vẫn gắn đúng `row_id`/field theo `drafting-tab.md` §3 — trên bảng
  chuyển vị, lỗi tô đỏ **ô** (cột tài sản × dòng thuộc tính) và cột header.
- Số cột tài sản tối đa đã chốt: **3** (v2 §13.3 — bảng cuộn ngang khi
  đầy 3 cột; ảnh vẽ 3 trùng khớp). Cap xuất Word riêng theo drafting-tab §5
  `word.too_many_assets` = 5.

## 3. Stage — card Người (đích)

- **Bảng dòng**: `⋮⋮` kéo thả | `Để lại` (radio owner, chỉ inheritance) |
  `Họ tên` | `Giới tính` | `Ngày sinh` | `Ngày mất` | `Số giấy tờ` |
  `Ngày cấp` | `Địa chỉ` | `×` — **7 cột đúng các trường DB `Customer`**
  (MIN-133 D1; `noi_cap`/`place_of_origin` bỏ khỏi UI nhưng giữ trên
  wire).
- Header bảng `surface.subtle`; **bảng không có thanh cuộn riêng** —
  danh sách dài thì cả trang (`#view`) cuộn (MIN-133 D8, thay quyết định
  "cuộn trong card" trước đây).
- Drag handle `⋮⋮` chỉ sắp xếp draft; lỗi gắn đúng dòng (`row_id`).
- `+ Người` thêm dòng cuối; `×` trên dòng xóa draft — hiệu lực chỉ sau
  `Cập nhật` (hành vi giữ nguyên drafting-tab).

## 4. Dialog `Loại đất` (đích, theo `approved-land-types.png`)

- Title `Loại đất · Tài sản N`; `×` đóng góc phải; `+ Loại đất` (secondary,
  `accent.soft`) trên cùng phải.
- **Bảng chuyển vị**: dòng = `Loại đất` (select) / `Diện tích (m²)`
  (input số) / `Thời hạn` (select); cột = từng thửa; header cột có `×`
  xóa thửa.
- Footer: `Hủy` (ghost) trái — `Áp dụng` (primary) phải. `Áp dụng` đưa
  kết quả về ô `Loại đất` của cột tài sản (dạng chip `N loại`); **ngữ
  nghĩa Apply đã chốt: ghi vào draft buffer `land_rows`, persist
  qua `Cập nhật` (contract §13.2 — APPROVED 27/09/2026, đã triển khai)**.
- Dialog rộng (`modalWideMaxWidth` ~1100 px tại 1496), cuộn ngang khi
  nhiều thửa; cuộn dọc khi thiếu chiều cao.
- Đây là **file-intake-độc-lập-không**: dialog này chỉnh `land_rows` của
  một tài sản — khác `intake-dialog.js` (nhập file → suggestion).

## 5. Tầng quan hệ (đích)

- **Pool (176 px)**: danh sách thẻ nhỏ trên nền `diagram.poolBg`; mỗi
  thẻ = tên (+ meta nhỏ khi trùng tên); nút gán `→` hiện khi
  hover/focus. Pool = `Stage đã commit − đang gán trên
  Diagram` (định nghĩa giữ nguyên `drafting-tab.md` §2 — file này chỉ đổi
  cách hiển thị). Splitter kéo đổi rộng Pool giữ nguyên.
- **Diagram (phần còn lại)**: canvas nền `bg.canvas` + lưới chấm;
  **node đã gán người** = card mini trắng 144 px (`diagram.nodeBg`):
  tên đậm + năm sinh–mất muted + hai hàng chip số `Chủ`/`Nhận`, mỗi chip
  là một **vị trí tài sản** (1..3 theo số tài sản Stage); chip selected =
  `accent.primary` nền đặc; **node trống** = ô 88×24 viền đứt, không
  nhãn/hint/chip (vai trò đọc qua `aria-label`/tooltip; vẫn là drop
  target). Nút hành động trên node (gán lại `→`, bỏ gán `↩`, xóa `×`)
  chỉ hiện khi hover/focus — vẫn trong tab order.
  - Ánh xạ chip số ↔ tài sản/vị trí đã chốt ở contract §13.4 (APPROVED
    27/09/2026, triển khai P7): `ownPositions`/`receivePositions` thay
    boolean `isLandOwner`/`willReceive`; mô hình **hai bên 30 vị trí** —
    §13.5 (`p1..p30`, `p16` = ghế đầu bên B). File này chốt hình thức;
    ngữ nghĩa lấy §13 làm chuẩn.
- **Đường nối**: giữ và làm rõ quan hệ cha→con (`diagram.edge`, selected
  `edgeSelected`); đường nối mang ngữ nghĩa — không trang trí. MIN-133:
  không mũi tên; cha/me→con là elbow xuống thanh ngang giữa khe thế hệ,
  vợ/chồng là đoạn ngang nét đứt; con của một cặp vợ/chồng kéo từ giữa
  đoạn vợ/chồng.
- **Header vùng sơ đồ** (MIN-133 D6 — gộp vào `card-head`, không còn
  footer): `+ Slot`, `Xem cách tính`, `Đánh giá thử` (chỉ inheritance),
  cụm zoom `− % +`, `⛶ Mở rộng` (overlay gần toàn màn, DESIGN §9.6), rồi
  `Lưu sơ đồ` (secondary + chấm `diagramDirty`) và `Xuất Word` (primary).
- Kéo lên vị trí đã có người — đã chốt: **swap** hai `personId`
  (contract §13.5 Q9 — APPROVED, cài đặt P7); `position 16` trong lưới
  30 vị trí — `p16` cố định = ghế đầu bên B (§13.5), cài đặt P7.

## 6. Thanh trên — tab cục bộ + hành động gộp một hàng (MIN-133 D4/D5)

- Tab cục bộ `Tổng quan`/`Soạn hồ sơ` nằm cùng hàng với hành động
  (không còn action bar riêng, không nút «quay lại», không tiêu đề
  `Soạn văn bản`, không pill `Nháp — chưa lưu`).
- Dropdown loại việc `Thừa kế ▾`/`Hai bên ▾` đọc được (≥128 px — gating
  `case_type` giữ nguyên drafting-tab §7; pill loại hồ sơ khi mở case
  thật).
- Phải: `Nhập file` (ghost — mở dialog intake chung, thay cho hai nút
  `Nhập dữ liệu` trên từng card), `Zalo` (**disabled**), `Hủy thay đổi`
  (ghost — đã chốt §13.2 Q2: client-only, restore cả Stage lẫn Diagram về
  committed — đã triển khai),
  `Cập nhật` (primary — commit Stage; khi nháp mới là `Lưu hồ sơ`).
- Dirty: **chấm** cạnh `Cập nhật`/`Lưu sơ đồ` theo tầng dirty tương ứng
  (`stageDirty`/`diagramDirty`) — không còn nhãn "Chưa lưu hồ sơ"; xem
  EXPERIENCE §5.
- Card `Thông tin hồ sơ` đã bỏ khỏi màn chính (MIN-133 D2 — meta
  `document_type`/`ngay_lap_ho_so`/`noi_niem_yet`/`ghi_chu` vẫn persist
  với mặc định vì Word đọc; chỗ nhập dành cho task Word riêng).

## 7. Dialog khác (đã có, giữ hành vi — chỉ restyle theo DESIGN)

- **Nhập file** (`intake-dialog.js`): danh sách nguồn, loại, progress;
  kết quả → suggestion tray.
- **Suggestion tray** (`suggestionTrayEl`): chip/rows gợi ý với
  `normalized/observed/inferred` badge — giữ phân biệt nguồn dữ liệu;
  nút `Đưa vào Stage`/`Bỏ qua`; lỗi per-source inline.
- **Xuất Word** (`word-export-dialog.js`): chọn nhiều văn bản, folder
  đích, breakdown kết quả từng văn bản — giữ ngữ nghĩa spec UX §7.
- **Conflict** (`conflictDialog`): tải bản mới / giữ nháp — không nút
  ghi đè (EXPERIENCE §6).
- **Gán vị trí** (`openAssignMenu`): đường bàn phím thay kéo-thả — giữ.

## 8. Trạng thái riêng của tab

| Trạng thái | Hiển thị đích | Nguồn dữ liệu |
|---|---|---|
| `locked` | Toàn workspace chỉ đọc; `Xem cách tính`/`Xuất Word` trong header sơ đồ vẫn đọc được, nút ghi mờ | `state.locked` — drafting-tab §3 |
| `case_type` không hỗ trợ | Mặt Unavailable của workspace + lý do | `state.unsupported` — drafting-tab §7 |
| `conflict` | Dialog conflict; không ghi đè | `workspace_conflict` |
| `stale` | Nhãn `đã cũ` cạnh dữ liệu; không khóa màn | `state.stale` |
| intake partial | Tray hiện phần đọc được + lỗi per-source | `state.intakePartial/intakeErrors` |
| mock backend | banner mock liên tục | `MOCK_BANNER` |

## 9. Responsive riêng Notary

- `≤900 px`: hai card Stage xếp dọc, Tài sản trước; Pool/Diagram xếp dọc;
  bảng người giữ `table-layout: fixed` (cả trang cuộn ngang nếu thiếu
  chỗ — không co chữ).
- 1366×768 & DPI 125%/150%: canvas sơ đồ co giãn theo flex (không height
  cố định — MIN-133); pan/zoom là đường thoát khi node nhiều — **không**
  thu nhỏ node dưới kích thước đọc được (đã gán 144 px).
- Bảng người: cột `Họ tên` co cuối cùng; cột ngày giữ `tabular-nums` căn
  phải.

## 10. Hiện trạng → đích (delta cho P4/P6/P7)

| Vùng | Hiện trạng (`case-drafting-view.js`/`relationship-diagram.js`) | Đích |
|---|---|---|
| Card Tài sản | Form nhóm trường dọc (`assetRowEl` + `landRowsEl` inline) | Bảng chuyển vị + dialog loại đất |
| Intake | `Nhập dữ liệu` trên từng card | `Nhập file` một nút trên action bar |
| Node flags | Toggle `Chủ đất`/`Nhận` boolean | Chip số per-tài-sản (ngữ nghĩa đã chốt §13.4 — v2 APPROVED) |
| Đường nối | SVG edges liệt kê | Đường nối canvas trực quan + zoom |
| Zoom sơ đồ | không có | cụm `−/%/+/Mở rộng` |
| `Hủy thay đổi` | không có API | §13.2 client-only — đã triển khai |
| Zalo | không có | hiển thị **disabled** |

## 11. Quyết định cho Notary — ĐÃ CHỐT (§13 v2 APPROVED 27/09/2026 + DESIGN §9)

- Ngữ nghĩa chip vị trí ↔ tài sản; hai bên 30 vị trí; `position 16`;
  thả lên vị trí đã chiếm — đã chốt ở contract §13.4–13.5 (MIN-125);
  cài đặt P7 (MIN-130).
- `Hủy thay đổi` phạm vi — chốt §13.2 Q2: restore **cả hai** buffer về
  committed; đã triển khai.
- `Apply` loại đất — chốt §13.2: ghi vào draft buffer, persist qua
  `Cập nhật`; đã triển khai.
- `Mở rộng` = overlay gần toàn màn trong app — chốt DESIGN §9.6; đã
  triển khai P7.
- Giới hạn cột tài sản trước khi cuộn ngang; thứ tự cột bảng Người — **P3**.

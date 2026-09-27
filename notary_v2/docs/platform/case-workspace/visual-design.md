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
│ Action bar: «quay lại» · Soạn văn bản · [Thừa kế ▾] ·        │
│             [Nhập file] [Zalo*] [Hủy thay đổi] [Cập nhật]    │  ← một dòng, primary phải
├───────────────────────────────┬──────────────────────────────┤
│ TÀI SẢN  (~36%)               │ NGƯỜI  (~64%)                │
│ bảng CHUYỂN VỊ:               │ bảng dòng:                   │
│   dòng = thuộc tính           │   ⋮⋮ | Họ tên | Ngày sinh |  │
│   cột = Tài sản 1 · 2 · 3     │        Ngày mất | Số giấy tờ │
│   (+ Tài sản ở header/footer) │   (+ Người)                  │
│   ô "Loại đất" → chip mở      │                              │
│   dialog loại đất             │                              │
├──────────┬───────────────────────────────────────────────────┤
│ POOL ~22%│ SƠ ĐỒ THỪA KẾ  ~78%                               │
│ thẻ người│ canvas: node cards + đường nối quan hệ            │
│ kéo được │ mỗi node: tên · ngày sinh–mất · hàng chip         │
│          │   Chủ đất [1][2][3]   Nhận đất [1][2][3]          │
│          │ cụm zoom góc:  −  100%  +  Mở rộng                │
│          │ footer phải:  [Lưu sơ đồ] [Xuất Word]             │
└──────────┴───────────────────────────────────────────────────┘
```

\* Zalo giữ **disabled** trong bản thật (ràng buộc MIN-123).

Tỉ lệ 36/64 và 22/78 giữ từ spec UX §3; thay đổi so với spec UX là **dạng
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
- **PENDING**: giới hạn số cột tài sản hiển thị trước khi cuộn (ảnh vẽ 3 —
  dữ liệu mẫu, không phải cap nghiệp vụ; cap thật theo drafting-tab §5
  `word.too_many_assets` = 5 khi xuất Word).

## 3. Stage — card Người (đích)

- **Bảng dòng**: `⋮⋮` kéo thả | `Họ tên` | `Ngày sinh` | `Ngày mất` |
  `Số giấy tờ` (+ các cột trường còn lại của PERSON_FIELDS — độ rộng và
  thứ tự cột chốt ở P3; không được bỏ trường nghiệp vụ).
- Header bảng `surface.subtle` + sticky khi danh sách dài; cuộn dọc trong
  card, không cuộn cả màn.
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
  nghĩa Apply (có phải commit Stage ngay không) chờ P2**.
- Dialog rộng (`modalWideMaxWidth` ~1100 px tại 1496), cuộn ngang khi
  nhiều thửa; cuộn dọc khi thiếu chiều cao.
- Đây là **file-intake-độc-lập-không**: dialog này chỉnh `land_rows` của
  một tài sản — khác `intake-dialog.js` (nhập file → suggestion).

## 5. Tầng quan hệ (đích)

- **Pool (~22%)**: danh sách thẻ nhỏ trên nền `diagram.poolBg`; mỗi thẻ
  = drag handle + tên (+ meta nhỏ). Pool = `Stage đã commit − đang gán trên
  Diagram` (định nghĩa giữ nguyên `drafting-tab.md` §2 — file này chỉ đổi
  cách hiển thị).
- **Diagram (~78%)**: canvas nền `bg.canvas`; node = card mini trắng
  (`diagram.nodeBg`), header tên đậm + dòng meta (ngày sinh–mất) muted;
  hai hàng chip số: `Chủ đất` và `Nhận đất`, mỗi chip là một **vị trí tài
  sản** (số lượng chip = số tài sản trên Stage); chip selected =
  `accent.primary` + `✓`.
  - **PENDING (P2)**: ánh xạ chip số ↔ tài sản/vị trí, quan hệ với
    `land_owner`/`will_receive` boolean hiện hữu, và mô hình **hai bên 30
    vị trí** — file này chỉ chốt hình thức, không chốt ngữ nghĩa.
- **Đường nối**: giữ và làm rõ quan hệ cha→con (`diagram.edge`, selected
  `edgeSelected`); đường nối mang ngữ nghĩa — không trang trí.
- **Cụm zoom**: `−`, nhãn `%`, `+`, `Mở rộng` ở mép canvas (ảnh: trên cùng
  phải); `Mở rộng` chờ chốt (fullscreen hay modal — EXPERIENCE §10).
- **Action footer**: `Lưu sơ đồ` (secondary) + `Xuất Word` (primary)
  phải-dưới canvas; `Xem cách tính`/`+ Slot`/`⋯` giữ trong toolbar theo
  spec UX §3 — vị trí chính xác chốt ở P3.
- **PENDING**: kéo lên vị trí đã có người (swap? push?) — theo danh sách
  mở của MIN-123, chờ owner; `position 16` trong lưới 30 vị trí — P7.

## 6. Action bar trên cùng

- Trái: quay lại + tên màn (`Soạn văn bản`) + dropdown loại việc
  (`Thừa kế` — gating `case_type` giữ nguyên drafting-tab §7).
- Phải: `Nhập file` (ghost — mở dialog intake chung, thay cho hai nút
  `Nhập dữ liệu` trên từng card), `Zalo` (**disabled**), `Hủy thay đổi`
  (ghost — **chờ P2** cho ngữ nghĩa discard, tạm không render),
  `Cập nhật` (primary — commit Stage; khi nháp mới là `Lưu hồ sơ`).
- Dirty: nhãn/chấm cạnh `Cập nhật`/`Lưu sơ đồ` theo tầng dirty tương ứng
  (`stageDirty`/`diagramDirty`) — xem EXPERIENCE §5.
- Trạng thái lưu ("Đã lưu …/đã cũ") hiển thị trên thanh này, không toast.

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
| `locked` | Toàn workspace chỉ đọc; action bar giữ `Xem cách tính`/`Xuất Word` đọc được, nút ghi mờ | `state.locked` — drafting-tab §3 |
| `case_type` không hỗ trợ | Mặt Unavailable của workspace + lý do | `state.unsupported` — drafting-tab §7 |
| `conflict` | Dialog conflict; không ghi đè | `workspace_conflict` |
| `stale` | Nhãn `đã cũ` cạnh dữ liệu; không khóa màn | `state.stale` |
| intake partial | Tray hiện phần đọc được + lỗi per-source | `state.intakePartial/intakeErrors` |
| mock backend | banner mock liên tục | `MOCK_BANNER` |

## 9. Responsive riêng Notary

- `≤1000 px` (đề xuất): hai card Stage xếp dọc, Tài sản trước; bảng
  chuyển vị cuộn ngang; Pool/Diagram giữ cuộn ngang thay vì ép node nhỏ
  (khớp spec UX §3).
- 1280×800 & DPI 125%/150%: canvas sơ đồ ưu tiên giữ vùng nhìn tối thiểu;
  pan/zoom là đường thoát khi node nhiều — **không** thu nhỏ node dưới
  kích thước đọc được (~160–180 px ngang, chờ duyệt).
- Bảng người: cột `Họ tên` co cuối cùng; cột ngày giữ `tabular-nums` căn
  phải.

## 10. Hiện trạng → đích (delta cho P4/P6/P7)

| Vùng | Hiện trạng (`case-drafting-view.js`/`relationship-diagram.js`) | Đích |
|---|---|---|
| Card Tài sản | Form nhóm trường dọc (`assetRowEl` + `landRowsEl` inline) | Bảng chuyển vị + dialog loại đất |
| Intake | `Nhập dữ liệu` trên từng card | `Nhập file` một nút trên action bar |
| Node flags | Toggle `Chủ đất`/`Nhận` boolean | Chip số per-tài-sản (ngữ nghĩa chờ P2) |
| Đường nối | SVG edges liệt kê | Đường nối canvas trực quan + zoom |
| Zoom sơ đồ | không có | cụm `−/%/+/Mở rộng` |
| `Hủy thay đổi` | không có API | chờ P2, tạm không render |
| Zalo | không có | hiển thị **disabled** |

## 11. Quyết định mở cho Notary (đầy đủ ở EXPERIENCE §10 + DESIGN §9)

- Ngữ nghĩa chip vị trí ↔ tài sản; hai bên 30 vị trí; `position 16`;
  thả lên vị trí đã chiếm — **P2/P7**, không suy ra từ ảnh.
- `Hủy thay đổi` phạm vi (Stage only hay cả Diagram) — **P2**.
- `Apply` loại đất có commit Stage hay chỉ draft — **P2**.
- `Mở rộng` = fullscreen canvas hay modal — **P3**.
- Giới hạn cột tài sản trước khi cuộn ngang; thứ tự cột bảng Người — **P3**.

# Decisions — MIN-129

## 2026-09-27 — Hủy thay đổi: restore cả Stage lẫn Diagram draft
- **Chọn:** nút `Hủy thay đổi` trên action bar restore `state.stage` ←
  `committed` và `state.diagram` ← `committedDiagram`, xoá
  `stageDirty`/`diagramDirty`/`fieldErrors`/`diagramErrors`; emit qua
  `model.dismissNotice()` (model không export `cancelDraft()` — ghi gap
  vào handoff).
- **Lý do:** contract §13.2 Q2 đã duyệt: Hủy = client-only restore cả hai
  buffer; không gọi command nào ra ngoài.
- **Loại bỏ:** chỉ revert Stage giữ diagram draft (quyết định tạm P3) —
  contract v2 Q2 đã chốt lại.
- **Nguồn:** `contracts/notary-case-drafting.md` §13.2 Q2.

## 2026-09-27 — Gate thao tác truyền dữ liệu khi Stage dirty
- **Chọn:** trên case đã commit (`caseId != null`), khi `stageDirty` thì
  disable `Lưu sơ đồ`/`Đánh giá thử`/`Xuất Word` + pill warn
  "Stage chưa cập nhật"; `scheduleEvaluate` cũng bỏ qua. Nháp mới
  (`caseId == null`) không gate — evaluate nháp gửi draft stage tường
  minh là luồng duy nhất của nó.
- **Lý do:** issue yêu cầu thao tác truyền dữ liệu ra ngoài phải yêu cầu
  hoàn thành/Cập nhật/Hủy — evaluate trên case thật chỉ thấy committed
  stage nên kết quả sẽ "lạc" với Stage đang sửa nếu chạy ngầm.
- **Nguồn:** mô tả issue MIN-129.

## 2026-09-27 — Select loại đất theo mã canonical backend
- **Chọn:** `Loại đất` = select với mã canonical
  (`ONT, ODT, CLN, NTS, LUC, BHK, SKC, TMD, DV, DGT, DKV, DHT`) từ
  `notary_v2/docs/platform/document-intake/property-rules.md` §loai_dat;
  giá trị ngoài danh sách được thêm thành option riêng (không mất dữ
  liệu). `Thời hạn` = text input (contract `string|null`, mẫu cho phép
  "Lâu dài" hoặc ngày).
- **Lý do:** mẫu duyệt dùng select cho loại đất + input cho thời hạn;
  giữ wire `string|null`.
- **Nguồn:** approved-land-types.png + property-rules.md.

## 2026-09-27 — Pool chỉ người, tên + meta khi trùng tên
- **Chọn:** Pool render chỉ `pool().people` (asset không gán được vào
  node — contract §13.4); card = drag-handle + `.nm` + `.sub` chỉ khi
  ≥2 người cùng `ho_ten` trong pool (meta = năm sinh / số giấy tờ) +
  nút `→` (aria `Gán vị trí`). Kéo giữ payload `text/plain`
  `{kind:'person', row_id}` y như cũ cho P7.
- **Lý do:** issue: "Pool chỉ tên gọn, người trùng tên phân biệt theo
  cách đã duyệt trong bản mẫu" — mẫu phân biệt bằng meta năm/ngày trên
  node card; pool giữ tối thiểu + meta khi trùng.
- **Nguồn:** approved-drafting.png + issue MIN-129.

## 2026-09-27 — Zalo disabled placeholder: label thuộc exception kiểm tra
- **Chọn:** giữ nút `Zalo` visible + `disabled` trên action bar; static
  test `view khong co Zalo...` được cập nhật thành cấm *engine
  identifiers* (`zalo.`, `zalo_`, `zaloStatus`, `zaloSec`,
  `ZaloDocument`...) — nhãn `Zalo` chỉ được phép đúng một chỗ
  (placeholder).
- **Lý do:** issue: "Zalo remains visible but disabled; do not hide it" —
  bản mẫu approved có nút Zalo xám; test cũ cấm cả chuỗi label → xung
  đột trực tiếp với yêu cầu mới; ý định test là chặn engine, không phải
  nhãn disabled.
- **Nguồn:** issue MIN-129 + approved-drafting.png.

## 2026-09-27 — Owner picker: cột radio "Để lại" đầu bảng Người
- **Chọn:** cột `Để lại` (radio, chỉ inheritance) đứng ngay sau cột
  drag-handle của bảng Người — trường bắt buộc của contract §13.1 phải
  dễ thấy.
- **Lý do:** v1 giấu trong row detail; trường required cần hiện mặt.
- **Nguồn:** contract §13.1 (owner_row_id bắt buộc khi commit).

## 2026-09-27 — Case type: select ở action bar (nháp) / pill (case thật)
- **Chọn:** nháp mới → `<select>` case_type trên action bar (ghi qua
  `updateCaseMeta('case_type')`); case đã tồn tại → `pill` hiển thị loại
  việc (immutable sau create, §13.5).
- **Lý do:** bản mẫu hiển thị dropdown loại việc trong action bar; meta
  case thật immutable nên pill tránh gợi hành động không tồn tại.
- **Nguồn:** approved-drafting.png + contract §13.5.

## 2026-09-27 — Re-render: defer khi đang gõ + data-fid focus restore
- **Chọn:** giữ guard "defer rebuild khi activeElement là
  input/textarea/select trong drafting panel" và thêm (a) `data-fid`
  ổn định trên control (`p:<row_id>:<field>`, `a:<row_id>:<field>`,
  `pdrag:<row_id>`...) để re-focus sau rebuild khi focus đang ở nút
  (drag handle/delete), (b) `syncChromeUI()` cập nhật dirty-dot/nhãn
  save/disabled ngay cả khi rebuild bị defer.
- **Lý do:** issue: "thao tác reorder/render KHÔNG làm mất giá trị đang
  gõ hay focus" — defer giữ value+focus khi gõ; data-fid giữ focus khi
  reorder bằng nút/keyboard.
- **Nguồn:** issue MIN-129; pattern defer sẵn có trong view.

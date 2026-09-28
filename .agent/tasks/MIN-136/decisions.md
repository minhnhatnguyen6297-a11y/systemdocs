# Decisions — MIN-136

Các quyết định owner chốt trong thread review UI (28/09) + quyết định kỹ thuật
phát sinh khi implement.

## D1 — Luồng sơ đồ đơn node (owner chốt phương án 1b)

- Draft thừa kế mới: **đúng 1 node `owner` trống** — bỏ seed 7 slot client
  (`seedDiagramSlots`, `seedBase`, nút "Tạo sơ đồ mẫu").
- Thả người đầu vào node `owner` → mặc định chủ đất: `owner_row_id` mirror +
  `ownPositions` = tất cả vị trí tài sản (`applyAssignDefaults` giữ nguyên).
- Node sau **chỉ** sinh từ engine `requiredSlots` sau mỗi `diagram_evaluate`
  — bỏ mọi đường thêm thủ công: nút `+ Slot`, mục "Con của X"/"Vợ-chồng của X"
  trong menu gán, `ensureEmptyChildSlot` (engine đã lo `minimumEmptyChildSlots`).
- Case cũ persist 7 slot vẫn render nguyên — không migrate.
- Chủ đất sống (chưa `ngay_chet`): engine không spawn — **đúng nghiệp vụ**
  (thừa kế chỉ phát sinh khi có người chết). UI hiện hint "điền Ngày mất"
  thay vì sửa rule engine.

## D2 — Bỏ cột `Để lại`

- `owner_row_id` chỉ chọn qua sơ đồ (thả người vào node owner) — cột radio
  trong bảng Người là đường ghi thứ hai vào cùng trường → bỏ.
- `workspace_owner_required` (backend bắt buộc) map sang message chỉ vào sơ đồ
  qua error-catalog.

## D3 — Pool chỉ người, nguồn theo trạng thái case

- Bỏ thẻ tài sản khỏi Pool — không có flow kéo-thả tài sản (dead UI).
- Nháp mới (`caseId == null`): Pool = `stage.people` nháp − đã gán — trước đây
  committed-only nên nháp không có gì để thả (nghẽn "không có gì xuống pool").
- Case thật: Pool = `committed.people` − đã gán (giữ nguyên).

## D4 — Header sơ đồ tối giản

- Chỉ giữ `Xem cách tính` (read-only evaluate + panel tỷ lệ/breakdown/warnings)
  · zoom · `Mở rộng` · `Lưu sơ đồ` · `Xuất Word`.
- Bỏ `Đánh giá thử` + `+ Slot` khỏi UI; evaluate vẫn chạy tự qua
  `scheduleEvaluate` debounce.

## D5 — Danh mục lỗi (error-catalog)

- `error-catalog.js` mới: map mã backend/infra → thông điệp thân thiện +
  rule ẩn sau lỗi ("liệt kê các rule ẩn trong hệ thống"). Load trước các
  module notary trong `index.html`.
- `case_list` retry tối đa 5 lần/1.5s khi lỗi infra (race sidecar chưa ready)
  — hết `submit_failed` thô.
- F-1 (phát sinh từ W4 MIN-133): emit defer khi đang gõ không được nuốt
  render conflict — conflict hiện ngay.

## D6 — Các sửa nhỏ đã chốt

- `+ Hồ sơ mới` trong empty-state tab Soạn hồ sơ (owner chọn hướng này).
- Draft công bố `capabilities.intake` đủ 5 loại (`image/pdf/docx/xlsx/text`)
  → `Nhập file` mở được trên nháp (backend đã hỗ trợ intake không case_id).
- `Hình thức sử dụng` → `Hình thức SD`.
- Ô ngày Stage = text mask `dd/mm/yyyy` (không `type=date` — control đó theo
  locale OS); wire ISO `yyyy-mm-dd`; trường Người cho nhập chỉ `yyyy`.
- `ngay_lap_ho_so` giữ `date.today()` phía sidecar (máy local — không có
  nguồn giờ online theo thiết kế offline); user đối chiếu bằng mắt.

## D7 — Bug phát hiện khi verify harness (không phải yêu cầu mới)

- `Identifier 'errText' has already been declared`: `error-catalog.js` và
  `relationship-diagram.js` cùng khai báo `errText` top-level — classic script
  share global lexical scope → file sau không parse, sơ đồ `module_missing`.
  Đổi tên binding trong relationship-diagram → `relErrText`. Regression
  guard: test quét trùng top-level identifier giữa các script notary.
- Comment CSS `row-drop-*/col-drop-*` chứa `*/` giữa comment (từ MIN-129) —
  đóng comment sớm, text rác nuốt rule `.cd-diagram` → `.cd-diagram` mất
  `display:flex`/`flex:1` → canvas co theo content (lỗi "sơ đồ nhỏ sát góc
  trái" khi còn 1 node). Sửa comment; guard: số `/*` == số `*/` trong cả 2 css.

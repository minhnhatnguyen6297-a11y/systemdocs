# Quy tắc sơ đồ Hai bên và Thừa kế

**Cập nhật:** 16/10/2026. Quy tắc dưới đây giữ contract đã chốt. Các thiết kế tính thừa kế mở rộng, engine v2 và case-state cũ vẫn chưa được duyệt toàn bộ; chuyển vào lịch sử không phải loại bỏ ý tưởng hay duyệt triển khai.

## 1. Luồng chung

Gán người đã cập nhật trong Stage vào vị trí; chọn Chủ/Nhận theo tài sản; xem kết quả Python; lưu sơ đồ. Thao tác chỉ đổi quan hệ, không sửa Người/Tài sản. Pool phản ánh sơ đồ đang xem và không lưu riêng. Cho lưu cấu trúc hợp lệ còn thiếu dữ liệu, kèm cảnh báo; không cho lưu cấu trúc sai. Xuất Word theo nhu cầu trường dữ liệu, không thêm lệnh chặn chỉ vì kết quả incomplete.

<a id="common"></a>
## 2. Input và output

Input chung là `diagram.state` draft và domain của Case. Cụ thể:

- `diagram_evaluate` có `case_id`; nếu chưa có Case thì bỏ `case_id` và gửi
  thêm Stage draft. Đây là read-only, không có `base_revision`.
- `diagram_save` có `case_id`, `base_revision` và Diagram; `case_type` lấy từ
  workspace server, không phải field tự do trong payload.

Output:

- `diagram.state` canonical đã validate;
- `render_model` do Python tạo;
- `requiredSlots`, warnings, errors và kết quả nghiệp vụ;
- revision mới sau `diagram_save`.

## 3. Thao tác

- Kéo người từ Pool vào slot: gán `personId` cho node.
- Di chuyển node: đổi slot/quan hệ trong Diagram draft.
- Gỡ node: xóa gán, không xóa người khỏi Stage.
- Chọn quan hệ/tài sản: sửa field Diagram draft theo domain.
- `Xem cách tính`: gọi evaluate read-only, chỉ hiển thị render model backend.
- `Lưu sơ đồ`: validate và ghi state trong một transaction.
- Cơ chế Hủy cũ khôi phục hai bản nháp; owner đã yêu cầu bỏ nút trong backlog, không coi cơ chế cũ là yêu cầu giữ nút.

## 4. Cách biểu diễn và lưu

Diagram không tự ghi một bảng quan hệ chung. Với hồ sơ thừa kế hiện hành, state
được lưu trong `case_state_json.diagram.engineInput`; backend tạo
`engineResult` cùng lần save và có thể cập nhật projection participant theo
quy tắc module.

Ví dụ: kéo người A vào slot `child_1` của owner và spouse:

```json
{
  "id": "child_1",
  "personId": "<row_id-cua-A>",
  "parentSlotIds": ["owner", "spouse"],
  "spouseSlotId": null
}
```

Ý nghĩa: A là con của người tại slot `owner` và `spouse`. Backend kiểm các slot
tồn tại, `personId` thuộc Stage, không có vòng quan hệ và chạy engine. Không
được suy thành bảng cha-con khác nếu spec/schema chưa chốt.

## 5. Contract v2

- `diagram_state.version = 3` và `domain` bắt buộc.
- Domain `inheritance` dùng node quan hệ cha/mẹ/vợ-chồng/con.
- Domain `two_party` dùng 30 slot `p1..p30`; không mang field quan hệ thừa kế.
- Node domain `inheritance` dùng `ownPositions` và `receivePositions` theo vị
  trí tài sản 1..3; node domain `two_party` cấm hai field này (§8.2).
- `isLandOwner` và `willReceive` là field legacy, bị cấm trên wire v2.

Contract chuẩn và schema máy đọc:
[`contracts/notary-case-drafting.md`](../../../contracts/notary-case-drafting.md)
và `contracts/notary-case-drafting/*.schema.json`.

## 6. Quy tắc lưu

- `personId` phải thuộc Stage committed.
- Save mang đúng `base_revision`; conflict không được ghi đè.
- Frontend không gửi kết quả tính như sự thật. Backend luôn tính lại từ input.
- State sai cấu trúc/nghiệp vụ (`invalid`) không được persist. State hợp lệ
  nhưng kết quả `incomplete` vẫn được lưu; backend trả `requiredSlots`/warning
  để người dùng bổ sung sau.
- Save chạy đúng một đường đánh giá với `Xem cách tính`: `render_model` đã lưu
  là kết quả evaluate tại thời điểm ghi (gồm warning Pool và trạng thái
  `incomplete`); engine trả `invalid` bị từ chối trước khi ghi.
- Save lỗi giữ nguyên Stage, Diagram và projection cũ.
- Reload và Word phải dùng cùng snapshot đã lưu.

## 7. Lỗi và ngoại lệ

- Node trỏ ra ngoài Stage: `diagram_reference_outside_stage`.
- Quan hệ sai, vòng lặp, slot/position không hợp lệ: `diagram_invalid_state`.
- Domain không khớp `case_type`: `diagram_domain_mismatch`.
- Field legacy trong state v2: reject, không âm thầm chuyển nghĩa.

<a id="two-party"></a>
## 8. Hai bên — vị trí hợp đồng

### 8.1. Vị trí và thao tác

- Có đúng 30 slot ổn định: `p1..p15` là Bên A, `p16..p30` là Bên B.
- Slot trống được giữ nguyên; không dồn người sang trái hoặc đổi số slot.
- Thả người vào slot trống: gán `personId`.
- Thả vào slot đã có người: hoán đổi hai `personId`.
- Gỡ người: slot trở lại rỗng và người quay về Pool.
- Mọi thao tác có đường bàn phím qua menu gán vị trí.

### 8.2. Dữ liệu và giới hạn

State dùng `version: 3`, `domain: two_party` và 30 node có `id` cố định.
Node chỉ giữ `id`, `personId`, `hidden`, `deleted` (contract §13.5 APPROVED
27/09/2026); cấm field quan hệ thừa kế như `parentSlotIds`/`spouseSlotId` và
**cấm** `ownPositions`/`receivePositions`. Stage tối đa 30 người và
cấm `owner_row_id` cho Case hai bên.

### 8.3. Lưu, lỗi và contract

Save dùng `case_id`, `base_revision` và state canonical đủ 30 slot. Slot ngoài
`p1..p30`, người ngoài Stage, trùng người hoặc mang field thừa kế đều bị từ
chối. Không được tự đổi domain của Case, **trừ** đường chuyển loại đã lưu đã
duyệt (reset Diagram rỗng theo domain mới; spec notary §2, contract §13.18).

Word export đã hỗ trợ hồ sơ hai bên (NAIA-8): `capabilities.word_export`
trả `true`, `word_export_*` không còn trả `case_type_unsupported` cho
domain này; readiness riêng qua `block_reason` `word.*` (chỉ kiểm tra kỹ
thuật — không áp điều kiện thừa kế). Mapping `[Bên A N - *]`/`[Bên B
N - *]` theo slot `p1..p15`/`p16..p30` và mẫu do người dùng chọn trong
thư mục mẫu — spec hiện hành tại
`_bmad-output/specs/notary_v2/word-templates.md`. Chi tiết wire
và fixture:
[`contracts/notary-case-drafting.md`](../../../contracts/notary-case-drafting.md)
mục 13.5 và `contracts/notary-case-drafting/examples/draft-v2/`.

Ví dụ kiểm chứng bản tích hợp 04/10/2026: p1 trống, p2 có A thì
`[Bên A 1 - Họ tên]` rỗng, `[Bên A 2 - Họ tên]` là A; không dồn lên p1.
Nhóm `[Người N - ...]` luôn theo dòng Stage đã lưu, không theo số ghế.

<a id="inheritance"></a>
## 9. Thừa kế — quan hệ và lựa chọn

### 9.1. Dữ liệu vào

- Người đã commit trong Stage.
- `owner_row_id` của người để lại di sản.
- Node, `parentSlotIds`, `spouseSlotId`.
- `ownPositions` và `receivePositions` theo vị trí tài sản 1..3.
- Ngày chết và các dữ kiện pháp lý đã được xác nhận.

### 9.2. Quy tắc chính

- Owner là một người Stage riêng, không suy từ cờ chủ đất cũ.
- Quan hệ vợ/chồng và cha-con phải nhất quán hai chiều theo engine.
- Không cho vòng quan hệ hoặc một người nằm ở nhiều slot xung đột.
- Người chết trước/sau owner ảnh hưởng nhánh thế vị; dữ liệu ngày thiếu phải tạo
  warning hoặc slot cần bổ sung, không tự đoán.
- Người từ chối nhận di sản là khái niệm pháp lý riêng, không đồng nghĩa người
  không được đánh dấu nhận trên UI.
- Frontend không tính phân số. Python tạo allocation, breakdown, warning và
  `requiredSlots`.
- `Người không nhận = tất cả người trên Diagram − Chủ đất − Người nhận` là
  công thức UI owner giữ ngày 24/09/2026. Đây không đồng nghĩa từ chối pháp lý.

Các công thức mở rộng còn Draft; không có quyền thay công thức đang được duyệt.

### 9.3. Tài sản

- Tối đa 3 tài sản trong contract v2.
- Vị trí tài sản là index 1..3 của Stage assets.
- `ownPositions`: tài sản người đó sở hữu.
- `receivePositions`: tài sản người đó nhận.
- Reorder tài sản đổi vật đang ở vị trí; dấu chọn bám số vị trí, không bám
  `row_id`. UI phải cảnh báo khi reorder/xóa làm đổi nghĩa.

### 9.4. Kết quả và nơi lưu

`engineInput` lưu quan hệ và lựa chọn đã validate trong `case_state_json`.
`engineResult` do backend tạo cùng lần save để audit và Word dùng. Projection
participant có thể được thay trong transaction, nhưng không được quyết định
ngược Stage/Pool/Diagram.

### 9.5. Word

- Thông tin cá nhân lấy từ Stage.
- Quan hệ và người nhận lấy từ Diagram/engine result.
- Chủ tài sản lấy từ `ownPositions`.
- Người không nhận và người từ chối phải theo rule riêng; không suy một nhóm từ
  nhóm kia.

### 9.6. Giao diện

- Tree theo thế hệ; cặp vợ/chồng thành một cụm, nhánh thế vị nằm dưới đúng
  người trung gian. Node đã có dữ liệu không tự biến mất sau evaluate.
- Card chỉ có quyết định `Chủ`/`Nhận` theo vị trí tài sản; không có nút `Từ
  chối`. Slot chỉ sinh khi backend trả là cần.
- `Xem cách tính` hiển thị một dòng cho mỗi người, gồm tổng và từng nguồn; UI
  không hiển thị JSON và không tự tính lại.
- Canvas rộng dùng cuộn ngang/pan/zoom, không bẻ nhánh hoặc thu node đến mức
  khó đọc. Cảnh báo gom thành vùng rõ ràng, không chồng popup.
- Khi panel `Xem cách tính` đóng, vùng cảnh báo dưới sơ đồ hiện trạng thái tính
  và danh sách chỗ engine yêu cầu (`requiredSlots`) dạng chỉ-đọc, kể cả ngay
  sau khi lưu hoặc mở lại; ô chỉ được sinh khi người dùng bấm `Xem cách tính`.

### 9.7. Lỗi và ngoại lệ

- Thiếu slot bắt buộc: trả `requiredSlots`, không bịa node.
- State `invalid`: save bị chặn, chi tiết lỗi engine nằm trong
  `diagram_invalid_state.details.errors`. State hợp lệ nhưng `incomplete`: contract hiện
  hành cho lưu và trả `requiredSlots`/warning. Owner chốt 15/10/2026: cho
  lưu bản nháp này, hiển thị rõ phần còn thiếu. Xuất Word vẫn theo điều kiện
  mode/mẫu hiện hành; không thêm lệnh chặn chỉ vì `incomplete`.
- Engine lỗi: không xóa state cũ.
- Hiển thị lỗi dùng formatter của danh mục lỗi (`errText` ở
  `error-catalog.js`); Sơ đồ đọc đúng export này khi script nạp theo
  `index.html`. Ghi chú runtime 16/10/2026: binding `relErrText → errText` đã
  khôi phục, nên lỗi evaluate/danh sách lỗi/lưu hiện thông điệp thân thiện;
  ghi chú này chỉ mô tả hiện trạng runtime, không đổi quy tắc nghiệp vụ trên.
- Hồ sơ legacy: migrate khi đọc theo rule đã có; GET không âm thầm ghi DB.

### 9.8. Câu hỏi và lịch sử

- Các lựa chọn “Nhận 1/2/3”, contract A/B và quyền sở hữu per-asset cần data
  model được duyệt; không suy từ `willReceive`/`isLandOwner` cũ.
- Nghiệp vụ từ chối, không nhận, thừa kế thế vị và ngoại lệ phải được owner/legal
  xác nhận trước khi đổi engine. Authority chưa xác minh phải ghi `[CONFIRM]`.
- Spec nghiệp vụ v2 cũ là draft; workflow/code đang chạy không tự biến mọi đề
  xuất trong draft thành quy tắc hiện hành.
- Owner đã chốt riêng việc lưu `incomplete` ngày 15/10/2026 trong phần Lỗi và ngoại lệ. Quyết định
  này không duyệt toàn bộ [`business-rules.md`](../../archive/specs-before-consolidation-20261015/notary_v2/diagram/inheritance/business-rules.md), không
  mở quyền lưu `invalid`/`unsupported`, và chưa chứng minh runtime đã tuân thủ.
- Còn rủi ro migration giữa `case_state_json.diagram.*`, `engine_state_json`,
  `diagram_payload` và projection legacy. Save phải ưu tiên state canonical,
  prune ghost/orphan nhưng giữ metadata hợp lệ; không suy API mới từ tên field cũ.
- Việc nối cạnh/mũi tên mới cần fixture hoặc ảnh chấp nhận riêng; không rebuild
  toàn Graph/Diagram chỉ để sửa một connector.

## 10. Điểm chưa chốt

Ngày nhập/hiển thị phải giữ đúng độ đầy đủ; ngày quy ước chỉ nằm trong tính toán. Cách tính các tình huống thừa kế mở rộng, thuật toán và ví dụ Draft vẫn cần đối chiếu/duyệt riêng. Không dùng ngày quy ước để tạo bằng chứng về thời điểm chết. Xóa nút giữa phải báo ảnh hưởng; cách giữ/gỡ nhánh phía sau chưa chốt. Không tự mở quyền lưu invalid/unsupported.

# Quy tắc sơ đồ Hai bên và Thừa kế

**Cập nhật:** 17/10/2026. Gỡ cả nhánh **#21B BUILT**, retained Quick CODE t3 **No actionable findings**, parent chấp nhận AC1–4; behavior §9.9 không đổi. Node full 198 + affected-file 25 sau patch test-only; service 106 (24 warnings hiện có), Source Electron real IPC/SQLite riêng. Không nghiệm thu packaged/Word hoặc các thiết kế/công thức thừa kế Draft mở rộng.

## 1. Luồng chung

Gán người từ Stage đang sửa vào vị trí; chọn Chủ/Nhận theo tài sản; xem kết quả Python; Lưu hồ sơ khi muốn ghi DB. Thao tác sơ đồ chỉ đổi quan hệ, không sửa Người/Tài sản. Stage/Pool/Diagram dùng chung bản đang sửa; Pool, nhãn người và dữ kiện evaluate không chờ Cập nhật. Không có nút Cập nhật/Lưu nháp trong Soạn hồ sơ, không tự ghi khi rời/đóng. Cho lưu cấu trúc hợp lệ còn thiếu dữ liệu, kèm cảnh báo; không cho lưu cấu trúc sai. Xuất Word đọc bản đã lưu theo nhu cầu trường dữ liệu, không thêm lệnh chặn chỉ vì kết quả incomplete.

<a id="common"></a>
## 2. Input và output

Input chung là Stage và `diagram.state` đang sửa cùng domain của Case. Cụ thể:

- Trong Soạn hồ sơ, `diagram_evaluate` luôn gửi Stage và Diagram đang sửa,
  kể cả khi đã có `case_id`; bản mới gửi thêm hint `case.case_type`.
  Đây là read-only, không có `base_revision`, không tạo/lưu nháp vào DB.
- `workspace_save_case` nhận Stage+meta+Diagram; hồ sơ đã có gửi `case_id` +
  `base_revision`, bản mới dùng nhánh tạo với `draftId`/`idempotency_key`
  ổn định qua retry cùng ý định. Domain phải khớp loại hồ sơ.
- `diagram_save` với `case_id`, `base_revision` và Diagram vẫn là API cho
  consumer khác; không phải đường ghi của màn Soạn hồ sơ.

Output:

- `diagram.state` canonical đã validate;
- `render_model` do Python tạo;
- `requiredSlots`, warnings, errors và kết quả nghiệp vụ;
- revision mới sau khi Lưu hồ sơ thành công (hoặc `diagram_save` ở consumer khác).

## 3. Thao tác

- Kéo người từ Pool vào slot: gán `personId` cho node.
- Di chuyển node: đổi slot/quan hệ trong Diagram draft.
- Gỡ node: không xóa người khỏi Stage. Với Thừa kế, xóa slot gỡ cả nhánh theo §9.9; bỏ gán một người về Pool bằng thao tác hiện có không đổi thành xóa nhánh.
- Chọn quan hệ/tài sản: sửa field Diagram draft theo domain.
- `Xem cách tính`: gọi evaluate read-only trên Stage+Diagram đang sửa, chỉ hiển thị kết quả Python; không dùng tên/ngày từ render model cũ thay bản Stage đang sửa.
- `Lưu hồ sơ`: flush ô đang nhập, đồng bộ mặc định vị trí chưa user chỉnh rồi validate và ghi Stage+meta+Diagram trong một transaction, chuyển draft→done.
- Không có nút Cập nhật/Lưu nháp hay Hủy thay đổi của Stage; giữ dirty, `canLeave` và cảnh báo đóng cửa sổ. Hủy rời/đóng giữ bản đang sửa; đồng ý bỏ không phát lệnh lưu.

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
  trí tài sản 1..5; node domain `two_party` cấm hai field này (§8.2).
- `isLandOwner` và `willReceive` là field legacy, bị cấm trên wire v2.

Contract chuẩn và schema máy đọc:
[`contracts/notary-case-drafting.md`](../../../contracts/notary-case-drafting.md)
và `contracts/notary-case-drafting/*.schema.json`.

## 6. Quy tắc lưu

- `personId` phải thuộc Stage đang sửa được gửi cùng lần evaluate/Lưu hồ sơ; người vừa thêm gán được ngay, không cần ghi trung gian. Xóa người dọn tham chiếu trong bản Diagram đang sửa.
- Save mang đúng `base_revision` khi đã có hồ sơ; conflict giữ bản đang sửa, cho tải mới hoặc sao chép, không được ghi đè.
- Frontend không gửi kết quả tính như sự thật. Backend luôn tính lại từ input; bản committed chỉ là mốc đã lưu/dirty/revision.
- State sai cấu trúc/nghiệp vụ (`invalid` do wire, tham chiếu, quan hệ) không
  được persist. State hợp lệ nhưng kết quả `incomplete` vẫn được lưu; backend
  trả `requiredSlots`/warning để người dùng bổ sung sau.
- Ranh giới "không tính được" (owner 23/10/2026): engine chỉ báo thiếu dữ
  kiện (`missing_land_owner`, `invalid_death_date`) thì Lưu hồ sơ vẫn ghi với
  `render_model.status = incomplete` và giữ danh sách lỗi; lỗi cấu trúc
  (wire/reference/domain/quan hệ/chu kỳ) vẫn bị từ chối trước khi ghi.
  Đường `diagram_evaluate` vẫn báo nguyên trạng thái chưa tính được của
  engine; `diagram_evaluate` chế độ nháp không chặn vì lỗi field tùy chọn —
  trả `incomplete` kèm warning `stage.incomplete_fields`.
- Save chạy đúng một đường đánh giá với `Xem cách tính`: `render_model` đã lưu
  là kết quả evaluate tại thời điểm ghi (gồm warning Pool và trạng thái
  `incomplete`).
- Save lỗi không đổi Stage, Diagram và projection đã lưu trong DB; giữ bản đang sửa để sửa tiếp.
- Reload và Word phải dùng cùng snapshot đã lưu, không tự xuất nội dung chưa Lưu hồ sơ.

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

- Người trong Stage đang sửa, gồm tên/ngày và dữ kiện hiện tại, không chỉ bản đã lưu.
- `owner_row_id` của người để lại di sản trong Stage đang sửa.
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

- Tối đa 5 tài sản (owner 23/10/2026).
- Vị trí tài sản là index 1..5 của Stage assets.
- `ownPositions`: tài sản người đó sở hữu.
- `receivePositions`: tài sản người đó nhận.
- Mặc định khi gán: owner nhận đủ vị trí Chủ, node thừa kế khác nhận đủ
  vị trí Nhận nếu mảng đang rỗng. Khi thêm/gỡ tài sản hoặc Lưu hồ sơ/Lưu
  nháp, mảng chưa được user chỉnh chip cho đúng node + Chủ/Nhận trong phiên
  đồng bộ đủ tập vị trí hiện có. Mảng đã chỉnh, kể cả tắt hết, giữ nguyên.
  Owner đang rỗng không tự điền nếu node khác đã có vị trí Chủ; không đổi
  mặc định tại thời điểm gán. Dấu đã chỉnh chỉ ở phiên, reset khi mở hồ sơ/
  phiên mới, không vào wire. Hiệu chỉnh G1 vòng sửa lỗi E2E 23/10 (B).
- Reorder tài sản đổi vật đang ở vị trí; dấu chọn bám số vị trí, không bám
  `row_id`. UI phải cảnh báo khi reorder/xóa làm đổi nghĩa.

### 9.4. Kết quả và nơi lưu

`engineInput` lưu quan hệ và lựa chọn đã validate trong `case_state_json`.
`engineResult` do backend tạo cùng lần save để audit và Word dùng. Projection
participant có thể được thay trong transaction, nhưng không được quyết định
ngược Stage/Pool/Diagram.

Metadata Case `chudat` theo owner **“người được gán chủ đất trong diagram”**:
lấy node đã lưu có `ownPositions` trỏ tài sản hiện có, không hidden/deleted;
đọc tên Stage snapshot bằng `personId`, theo thứ tự Stage và dedup row ID.
Không lấy `owner_row_id` hoặc tự gắn người chết làm chủ. Không gán là `null`.
Đây là projection Case mới; nhóm Word legacy có nhánh force-flag người chết
vẫn giữ hiện trạng, không được dùng nhánh fallback đó làm nguồn `chudat`.
[Catalog](../../../contracts/entities.md#94-metadata-hồ-sơ-upload--triển-khai-phạm-vi-case).

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

<a id="branch-removal"></a>
### 9.9. Gỡ cả nhánh khỏi Diagram

Owner chốt ngày **17/10/2026**, nguyên văn **“B - gỡ cả nhánh”** ([decision](../../decisions/decision-owner-inheritance-remove-entire-branch-20261017.md)).

1. Từ node được xóa, lấy node đó và toàn bộ hậu duệ **active** qua cạnh `parentSlotIds` cha/mẹ → con, ở mọi độ sâu. Slot rỗng/ẩn cũng thuộc graph active. Con có hai cha/mẹ vẫn bị gỡ khi chỉ một cha/mẹ trong tập bị gỡ. Không dùng cạnh `spouseSlotId` để mở rộng tập; spouse chỉ bị gỡ nếu bản thân cũng là hậu duệ theo cạnh cha/mẹ.
2. Trước mutation, hiện danh sách node sẽ gỡ (tên người + slot để phân biệt; slot chưa gán ghi ô trống) và các quan hệ cha/mẹ–con, vợ/chồng thực tế sẽ ngắt. Báo người vẫn ở Stage/trở lại Pool, kết quả/phần hưởng có thể đổi, chỉ Lưu hồ sơ mới ghi. Danh sách dài cuộn được; không chỉ báo số lượng.
3. Hủy, Escape, nút đóng và đóng nền không đổi draft/dirty/revision hay phát evaluate/save từ thao tác gỡ. Xác nhận chỉ áp tập tác động vừa xem; graph hoặc phiên hồ sơ đã đổi thì không gỡ âm thầm theo cảnh báo cũ. Xác nhận hợp lệ thực hiện **một** mutation draft rồi dùng evaluate/debounce hiện có, không tự save.
4. Đánh dấu toàn bộ tập `deleted:true` và giữ trong canonical Node v3 hiện có; giữ ID, `personId`, `ownPositions`, `receivePositions`, `hidden`. Xóa `parentSlotIds`/`spouseSlotId` đi ra từ node bị gỡ và dọn mọi tham chiếu đi vào tập này trên tất cả node, **kể cả tombstone cũ**. Không còn spouse một chiều hoặc parent không hợp lệ do thao tác; node/quan hệ/Chủ/Nhận không bị tác động giữ nguyên.
5. Stage Người/Tài sản (ID, thứ tự, giá trị) không đổi. Pool vẫn là Stage trừ gán trên node active, không tính `personId` còn giữ trên tombstone. Không dồn/đánh lại số slot, đổi vị trí tài sản, tự reparent hoặc giữ ô trung gian rỗng thay cho node đã xóa.
6. Dùng evaluate/Save hiện có; không store/API/schema mới. Save giữ atomic/revision/errors: invalid hoặc lỗi không ghi và giữ draft; Save thành công rồi mở lại khớp state canonical. Giữ nguyên cơ chế slot trống do `requiredSlots` tạo khi evaluate hiện hành, không hồi sinh người/quan hệ nhánh đã gỡ hoặc tái dùng ID tombstone. Không đổi công thức Python.

Ví dụ A → B → C, B↔S, C có parents `[B,S]`: xóa B gỡ B, C và hậu duệ của C; S còn node nhưng mất spouse B và các liên kết tới tập bị gỡ. A cùng các nhánh khác giữ nguyên; không nối C lên A. Đây là quy tắc đã chọn, chưa phải nghiệm thu implementation #21B.

## 10. Điểm chưa chốt

Ngày nhập/hiển thị phải giữ đúng độ đầy đủ; ngày quy ước chỉ nằm trong tính toán. Cách tính các tình huống thừa kế mở rộng, thuật toán và ví dụ Draft vẫn cần đối chiếu/duyệt riêng. Không dùng ngày quy ước để tạo bằng chứng về thời điểm chết. Xóa node Thừa kế áp dụng quy tắc gỡ cả nhánh đã chốt ở §9.9, không còn câu hỏi giữ/gỡ nhánh đang chờ owner. Không tự mở quyền lưu invalid/unsupported.

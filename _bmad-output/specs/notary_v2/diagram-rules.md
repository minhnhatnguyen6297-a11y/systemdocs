# Quy tắc sơ đồ Hai bên và Thừa kế

**Cập nhật:** 27/10/2026. WP0 chốt lại luật sơ đồ v2; chỉ sửa tài liệu, chưa triển khai/nghiệm thu runtime mới. Luật gỡ thẻ §9.9 thay “B - gỡ cả nhánh” ngày 17/10/2026; bằng chứng #21B cũ không chứng minh luật mới. WP-S (27/10/2026) bổ sung luồng theo cặp cho ô Con (§9.2/§9.6), luật ngày chỉ có năm và ngày không hợp lệ (§9.7), và §11 Engine — engine spec duy nhất còn nằm trong archive nên luật engine viết tại đây.

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
được lưu trong `case_state_json.diagram` (v3); backend tạo `render_model` cùng
lần save và cập nhật projection participant theo quy tắc module.

Mỗi lần **Lưu hồ sơ**/Lưu sơ đồ, dòng `inheritance_participants` của người có
node được ghi lại theo hình dạng Diagram đã lưu gần nhất — kể cả dòng đã tồn
tại: `vai_tro` và `hang_thua_ke` đổi theo quan hệ mới. Có hai nguồn vai trò
trong cùng cột `vai_tro`, phân biệt bằng chính giá trị đang lưu (không có cột
nguồn riêng):

- **Suy từ sơ đồ:** `Vợ/Chồng`, `Cha`, `Mẹ`, `Cha_vc`, `Me_vc`, `Con_dau_re`,
  `Con`, `Anh/Chị/Em`, `Cháu`, `Khac` (owner không thành dòng participant).
  Đây là bộ giá trị hữu hạn của projection; mỗi lần Lưu ghi đè bằng giá trị
  suy từ Diagram hiện tại.
- **Gán tay:** mọi giá trị khác (ví dụ `Người được ủy quyền`). Projection giữ
  nguyên qua các lần Lưu; hạng thừa kế tính từ chính vai trò đó.

Một dòng chỉ mang một `vai_tro`: nếu người vừa có vị trí quan hệ vừa được gán
tay vai trò khác thì vai trò gán tay thắng ở cột này; Word vẫn đọc vị trí sơ
đồ cho các nhóm người/thừa kế khác. Người bị gỡ/ẩn node bị xóa khỏi bảng như
trước. Cặp vợ–chồng thuộc nhánh (con dâu/rể) hiện chỉ còn trong state Diagram,
chưa có trường chuẩn — #45 TC3 (chỉ còn trong lịch sử Git: `git show f6705c8:docs/archive/backlog/bug-participant-role-projection-stale-spouse-anchor.md`)
đang mở, tạm dừng chờ chốt mô hình quan hệ.

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
`word-templates.md` (bản BMAD, chưa chuyển sang docs/; xem tag bmad-archive-20261028). Chi tiết wire
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
- `owner_row_id` của người để lại di sản trong Stage đang sửa (có thể chưa gán
  khi Lưu hồ sơ — xem §6).
- Node, `parentSlotIds`, `spouseSlotId`.
- `ownPositions` và `receivePositions` theo vị trí tài sản 1..5.
- Ngày chết và các dữ kiện pháp lý đã được xác nhận.

### 9.2. Quy tắc chính

- Owner là một người Stage riêng, không suy từ cờ chủ đất cũ.
- **Ô Con thuộc cặp (người gốc + ô vợ/chồng), không tách cạnh cha/mẹ riêng.**
  Con thả vào ô Con của cặp được ghi nhận cả hai cha/mẹ; nếu ô vợ/chồng của cặp
  còn trống lúc thả thì thả người vào ô đó sẽ điền cha/mẹ còn thiếu; nút
  `Con riêng` trên thẻ con xóa cha/mẹ được điền tự động. Mỗi vợ/chồng tiếp theo
  thả vào ô dự phòng có ô Con riêng của cặp mình và sinh thêm ô vợ/chồng dự phòng.
  Mỗi ô Con được thả thì sinh lại một ô dự phòng.
- **Quan hệ đã có trên sơ đồ thì gắn vào ô đang có, không sinh ô mới.** Con chết
  sau chủ đất (chuyển tiếp) là con của cặp đang có: gắn vào đúng hai ô đó, không
  sinh Cha/Mẹ mới. Vợ/chồng chết sau chủ đất: con chung đã nằm dưới cặp là con
  của người này nên không sinh ô Con trùng; vợ/chồng của người này là chủ đất đã
  có trên sơ đồ nên không sinh ô vợ/chồng mới.
- Vợ/chồng theo D-041 sửa đổi: nhiều thẻ vợ/chồng, người đặt cuối là hợp pháp;
  ô dự phòng nằm cuối. Vợ/chồng đặt trước bị làm nhạt, con của họ vẫn là người
  thừa kế của người gốc. Không cảnh báo vợ/chồng.
- Gỡ tích `Chủ` ở thẻ chủ đất duy nhất không làm thẻ rời vị trí; trần tài sản
  vẫn 5 (§9.3).
- Con sinh sau khi người chết: không luật riêng, không cảnh báo.
- Không cho vòng quan hệ hoặc một người nằm ở nhiều slot xung đột.
- Sau mỗi thay đổi thả/di chuyển/gỡ thẻ, tích Chủ/Nhận hoặc sửa ngày mất/còn
  sống ở Stage, engine chạy lại tới ổn định; không chờ `Xem cách tính`.
- Thiếu ngày mất: chưa sinh ô cho người đó, hiện nhãn `thiếu ngày mất` trên thẻ
  tới khi nhập đủ. Ngày chỉ có năm (`2020`) được tính là **01/01 của năm đó**
  khi so trước/sau. Ngày không hợp lệ/thiếu phần thì báo lỗi tại field và thẻ đó
  không thả được (§9.7). Không đoán nhánh; ngày quy ước chỉ dùng trong tính toán,
  input luôn hiển thị đúng như nhập.
- Trên sơ đồ, người không tích Chủ/Nhận được coi là từ chối:
  `Người không nhận = tất cả người trên Diagram − Chủ đất − Người nhận`.
  Đây là quy ước sản phẩm; đoạn Word từ chối hoãn sang đợt Word sau (Q3),
  không tự bịa văn bản từ chối hoặc coi đã đáp ứng thủ tục pháp lý.
- App không suy loại giao dịch, không suy tài sản chung, không cảnh báo vợ/chồng.
- Frontend không tính phân số. Python tạo allocation, breakdown và `requiredSlots`.
- Chỉ hỗ trợ hàng 1 + thế vị + chuyển tiếp. Hàng 2/3 (D-038, R-32) gác sau
  `ENABLE_LATER_LINES=False`, không nối vào sơ đồ; thiếu hàng 1 trả
  `Chưa hỗ trợ`, không sinh ô hàng 2/3.

Các công thức mở rộng còn Draft; không có quyền thay công thức đang được duyệt.

### 9.3. Tài sản

- Tối đa 5 tài sản (owner 23/10/2026).
- Vị trí tài sản là index 1..5 của Stage assets.
- `ownPositions`: tài sản người đó sở hữu.
- `receivePositions`: tài sản người đó nhận.
- Mặc định người mới thả vào ô chủ đất tích Chủ cho mọi vị trí hiện có,
  không tích Nhận. Mọi ô khác có `ownPositions = []`, `receivePositions = []`
  (= từ chối trong văn bản); không tự điền Nhận.
- Khi thêm tài sản, chỉ người đã tích mới được nối thêm vị trí mới vào
  đúng loại Chủ/Nhận đã tích; người chưa tích giữ rỗng. Lựa chọn đã lưu
  giữ nguyên, không xóa `receivePositions` cũ khi mở hồ sơ.
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
- Người không tích Chủ/Nhận được coi là từ chối trên sơ đồ. Đoạn Word từ chối
  hoãn sang đợt Word sau (Q3); không coi cập nhật spec này là đã cập nhật Word.

### 9.6. Giao diện

- Ô (node) là chỗ trống do engine tạo/xóa; thẻ là người được thả vào ô.
  Người dùng chỉ thả/di chuyển/gỡ thẻ và tích Chủ/Nhận; không có nút tạo ô,
  xóa ô, nối quan hệ hoặc menu thêm cha/mẹ/con.
- Sau mỗi thay đổi, engine chạy tới ổn định: thêm ô thiếu; ô thừa trống bỏ
  im lặng, ô thừa có thẻ thì thẻ về Pool. ID ô ổn định theo
  (người gốc, vai trò, thứ tự). Không mất Người khỏi Stage.

| Người trong ô | Ô engine sinh ra |
|---|---|
| Chủ đất còn sống | Chỉ nhóm Vợ/chồng (+1 ô dự phòng); không có Cha/Mẹ/Con. |
| Chủ đất đã chết | Cha, Mẹ, Vợ/chồng (+1 dự phòng), và ô Con của cặp (người gốc + ô Vợ/chồng) +1 dự phòng. |
| Người chết SAU chủ đất (chuyển tiếp) | Cha, Mẹ, Vợ/chồng (+1 dự phòng), ô Con của cặp +1 dự phòng — quan hệ nào đã có trên sơ đồ thì gắn vào ô đang có, không sinh ô mới. |
| Người chết TRƯỚC chủ đất (thế vị, Điều 652 BLDS 2015) | Chỉ Con (+1 dự phòng), tối đa tới chắt (D-012); không ô vợ/chồng. |
| Người còn sống, không phải chủ đất | Không sinh ô. |

- Lần thả đầu vào ô Chủ đất chỉ phân biệt còn sống/đã chết theo bảng trên.
  Thiếu ngày mất áp dụng Q1 tại §9.2, không đoán.
  Mỗi nhóm vợ/chồng hoặc con được phép sinh luôn có đúng một ô trống dự phòng;
  thả vào dự phòng thì engine sinh dự phòng mới. Người vợ/chồng đặt cuối là
  hợp pháp (D-041); ca nhiều vợ hợp pháp hoãn (Q2).
- WP2 trả tập ô đích `requiredSlots[].slots` với ID UUIDv5 theo
  `(anchorSlotId, role, ordinal)`, thứ tự bắt đầu 0. Cha/Mẹ mỗi vai trò
  một ô; nhóm Vợ/chồng/Con tối thiểu hai ô, tăng theo số người đã gán + 1.
  Ô Con gắn theo cặp: `parentSlotIds` của con là cặp (người gốc + ô vợ/chồng
  của cặp); thả vợ/chồng số 1 vào sau thì cha/mẹ còn thiếu được điền, nút
  `Con riêng` xóa cha/mẹ tự điền; quan hệ đã có trên sơ đồ thì gắn vào ô đang có.
  Nhánh thế vị chỉ theo cạnh con, không lấy vợ/chồng chết trước làm gốc.
  Q1 trả warning `missing_death_date` kèm `personId`/`anchorSlotId`.
  Ngày chỉ có năm (`2020`) được tính là 01/01 của năm đó khi so trước/sau:
  con `2020` so với chủ đất 01/06/2020 là chết trước → nhánh thế vị.
  Không đổi dữ kiện ngày nhập.
- Mỗi thế hệ một hàng: cha/mẹ trên, vợ/chồng cùng hàng ngay cạnh người gốc,
  ô Con của cặp nằm dưới đúng cặp, con trong nhóm theo ngày sinh; dự phòng cuối
  nhóm. Thế vị nằm dưới đúng người trung gian. Không chồng thẻ: thẻ vợ/chồng
  không che ô Con đang trống và không đè thẻ con.
- Ô trống có nhãn vai trò kèm tên người gốc: `Cha của …`, `Mẹ của …`,
  `Vợ/chồng của …`, `Con của … và …`; nhãn ô không chứa UUID/ID thô.
- Thả/gỡ không debounce; gõ chữ khoảng 300ms. Mục tiêu thả → ô hiện
  ≤200ms p95; sửa sống/chết ở Stage → đối chiếu tập ô ≤200ms.
  Mỗi thay đổi chỉ vẽ lại một lần sau khi ổn định.
- Card chỉ có lựa chọn `Chủ`/`Nhận` theo vị trí tài sản; không nút `Từ chối`.
- `Xem cách tính` hiển thị một dòng cho mỗi người, gồm tổng và từng nguồn; UI
  không hiển thị JSON và không tự tính lại.
- Canvas rộng dùng cuộn ngang/pan/zoom, không bẻ nhánh hoặc thu node đến mức
  khó đọc. Cảnh báo gom thành vùng rõ ràng, không chồng popup.
- Khi panel `Xem cách tính` đóng, vùng trạng thái dưới sơ đồ vẫn hiện
  trạng thái tính và phần thiếu; việc sinh/thu hồi ô luôn chạy tự động,
  không phụ thuộc mở panel, kể cả sau khi lưu hoặc mở lại.
- Nhãn hiển thị (owner 23/10/2026): người chưa có tên dùng đúng **một** nhãn
  `(chưa có tên)` ở mọi vị trí (Pool, node, menu, Hai bên). Node còn sống chỉ
  hiện năm sinh; có năm mất hiện `{sinh} – {mất}`; không dùng dấu `…` lửng.
  Node không hiện badge `%` — phần trăm chỉ nằm trong panel `Xem cách tính`.
  Phụ chú phân biệt trùng tên trong Pool (`sinh {năm}` /
  `GT {số}`) được giữ vì giúp chọn đúng người. Nhãn provenance
  (`đọc được`/`đã chuẩn hóa`/`suy luận`) không gắn lên giá trị hiển thị;
  provenance vẫn nằm trong record.

### 9.7. Lỗi và ngoại lệ

- Thiếu slot bắt buộc: trả `requiredSlots`, không bịa node.
- State `invalid`: save bị chặn, chi tiết lỗi engine nằm trong
  `diagram_invalid_state.details.errors`. State hợp lệ nhưng `incomplete`: contract hiện
  hành cho lưu và trả `requiredSlots`/warning. Owner chốt 15/10/2026: cho
  lưu bản nháp này, hiển thị rõ phần còn thiếu. Xuất Word vẫn theo điều kiện
  mode/mẫu hiện hành; không thêm lệnh chặn chỉ vì `incomplete`.
- Ngày không hợp lệ/thiếu phần (`06/2001`, `31/02/2001`): lỗi tiếng Việt hiện
  ngay tại ô ngày; thẻ có ngày không hợp lệ **không thả được** (Stage hoặc Pool)
  và có tooltip ngắn nêu lý do. Sửa một thẻ đã đặt thành ngày không hợp lệ không
  được xóa sơ đồ: đánh giá không fail toàn cục, giữ trạng thái hợp lệ cuối của
  những người khác và chỉ hiện lỗi ở field đó.
- Engine lỗi: không xóa state cũ.
- Hiển thị lỗi dùng formatter của danh mục lỗi (`errText` ở
  `error-catalog.js`); `errText` chỉ trả **một câu** (title), không hint dạy
  thao tác, không in mã snake_case. Lỗi evaluate/lưu hiện đúng một dòng trong
  vùng lỗi dành sẵn của Sơ đồ — không toast/banner trùng. Slot lỗi có chiều
  cao cố định nên canvas và các vùng khác không nhảy khi lỗi hiện/biến mất.
  Thành công không có câu chữ: nút hiện spinner khi chạy, tích xanh ngắn khi
  xong.
- Hồ sơ legacy: migrate khi đọc theo rule đã có; GET không âm thầm ghi DB.

### 9.8. Câu hỏi và lịch sử

- Các lựa chọn “Nhận 1/2/3”, contract A/B và quyền sở hữu per-asset cần data
  model được duyệt; không suy từ `willReceive`/`isLandOwner` cũ.
- Nghiệp vụ từ chối, không nhận, thừa kế thế vị và ngoại lệ phải được owner/legal
  xác nhận trước khi đổi engine. Authority chưa xác minh phải ghi `[CONFIRM]`.
- Spec nghiệp vụ v2 cũ là draft; workflow/code đang chạy không tự biến mọi đề
  xuất trong draft thành quy tắc hiện hành.
- Owner đã chốt riêng việc lưu `incomplete` ngày 15/10/2026 trong phần Lỗi và ngoại lệ. Quyết định
  này không duyệt toàn bộ [`business-rules.md`](diagram/inheritance/business-rules.md), không
  mở quyền lưu `invalid`/`unsupported`, và chưa chứng minh runtime đã tuân thủ.
- Còn rủi ro migration giữa `case_state_json.diagram.*`, `engine_state_json`,
  `diagram_payload` và projection legacy. Save phải ưu tiên state canonical,
  prune ghost/orphan nhưng giữ metadata hợp lệ; không suy API mới từ tên field cũ.
- Việc nối cạnh/mũi tên mới cần fixture hoặc ảnh chấp nhận riêng; không rebuild
  toàn Graph/Diagram chỉ để sửa một connector.

<a id="branch-removal"></a>
### 9.9. Gỡ thẻ

Owner chốt **27/10/2026**, thay quyết định **“B - gỡ cả nhánh” 17/10/2026**
([quyết định mới](../../decisions/decision-owner-diagram-rules-v2-20261027.md)).

1. Người dùng gỡ **thẻ**, không xóa ô. Người về Pool, vẫn nguyên ID/thứ tự/
   dữ kiện trong Stage; engine tính lại tập ô tới ổn định theo §9.6.
   Ô thừa trống bỏ im lặng; ô thừa có thẻ thì đưa người về Pool.
2. Gỡ chủ đất trả mọi người trong ô sinh ra từ chủ đất về Pool, **kể cả
   vợ/chồng**. Không chỉ duyệt hậu duệ qua `parentSlotIds` và bỏ sót spouse;
   không tự reparent. Nhánh/Chủ/Nhận ngoài tác động giữ nguyên.
3. Không modal, không xác nhận trước mutation. Nếu không có người khác về
   Pool theo thì gỡ im lặng. Nếu có cascade, hiện toast
   `Đã đưa N người về Pool · Hoàn tác` khoảng **5 giây**.
   Hoàn tác khôi phục nguyên trạng trước thay đổi, gồm gán người, quan hệ
   và Chủ/Nhận. Sau Hoàn tác, engine chạy lại trên dữ liệu hiện tại và bỏ
   những ô vừa khôi phục mà luật hiện hành không cho phép. Công tắc thông báo
   trong cài đặt **mặc định bật** (Q4);
   tắt thì hoàn toàn im lặng, không toast.
4. Một thay đổi draft, chạy engine tới ổn định, vẽ lại một lần; thả/gỡ không
   debounce và không autosave. Lưu hồ sơ dùng transaction/revision/errors
   hiện có; lỗi giữ bản đang sửa và bản lưu cũ, không ghi một phần.
5. Khi mở hồ sơ cũ, engine đối chiếu tập ô: ô trống thừa bỏ im lặng; thẻ
   trong ô thừa về Pool, không mất khỏi Stage. Ghi chú một lần khi mở:
   `N người đã về Pool do luật sơ đồ mới`. Giữ `receivePositions` đã lưu;
   mặc định mới chỉ dành cho người mới thả. Tombstone `deleted:true` cũ
   bỏ qua khi đọc, dọn khi lưu; ID `slot_n` cũ ánh xạ sang ID ổn định khi migrate.

Ví dụ: A chủ đất chết 2020; B vợ chết 1997; C con chết 2001; D con còn sống.
A sinh Cha/Mẹ, Vợ/chồng + dự phòng, Con + dự phòng. C chỉ sinh Con thế vị,
không ô vợ/chồng; D không sinh ô. Chỉ A mặc định tích Chủ. Sửa A thành còn
sống thì chỉ còn nhóm vợ/chồng, C/D về Pool và có toast; gỡ A thì B cũng về Pool.

## 10. Điểm chưa chốt

Ngày nhập/hiển thị giữ đúng độ đầy đủ; ngày quy ước chỉ dùng trong tính toán, không làm bằng chứng thứ tự chết. Q1–Q4 đã chốt tại §9.2/§9.5/§9.6/§9.9; nhiều vợ hợp pháp và đoạn Word từ chối hoãn sang đợt sau. Hàng 2/3 gác sau `ENABLE_LATER_LINES=False`; không sinh ô và không tự mở quyền lưu invalid/unsupported. Những công thức mở rộng khác vẫn cần duyệt riêng; WP0 chỉ sửa spec, không chứng minh runtime đã tuân thủ.

<a id="engine"></a>
## 11. Engine

Engine spec duy nhất còn nằm trong archive
([`engine.md`](diagram/inheritance/engine.md),
đã đính chính có giới hạn), nên luật engine của luật sơ đồ v2 viết tại đây.
Mục này chỉ ghi hành vi engine phải theo; không nâng thiết kế React/API/DB cũ
trong archive thành spec hiện hành và không chứng minh runtime đã tuân thủ.

- Ô do engine sở hữu: engine trả `requiredSlots` và không tự tạo Người, không
  đoán người vào ô. Tập ô theo bảng §9.6, sinh theo cặp ở §9.2.
- Sinh ô theo cặp: mỗi cặp (người gốc + vợ/chồng) có ô Con riêng; ô Con được
  thả thì sinh ô dự phòng mới; ô vợ/chồng dự phòng được thả thì sinh ô Con của
  cặp mới và một ô vợ/chồng dự phòng mới. ID ô ổn định theo
  `(anchorSlotId, role, ordinal)`, ordinal bắt đầu 0.
- Không sinh ô cho quan hệ đã có trên sơ đồ: con chết sau chủ đất gắn vào cặp
  đang có, không sinh Cha/Mẹ mới; vợ/chồng chết sau chủ đất gắn vào chủ đất
  đang có, không sinh ô vợ/chồng mới, con chung đã nằm dưới cặp không sinh lại.
  Đây là điều kiện bắt buộc để không tạo ba cha/mẹ làm sơ đồ đứng và lưu báo
  `Quan hệ cha/mẹ không hợp lệ`.
- Ngày chỉ có năm = **01/01 của năm đó** khi so trước/sau; `bounds()` phải theo
  luật này thay vì so theo khoảng cả năm. Dữ liệu lưu/hiển thị vẫn đúng như nhập.
- Ngày không hợp lệ/thiếu phần không được làm đánh giá fail toàn cục: engine bỏ
  qua người có ngày không hợp lệ, giữ trạng thái hợp lệ cuối của những người
  khác và trả lỗi ở mức field để UI hiện tại ô ngày.
- Vợ/chồng chết trước chủ đất: engine không sinh ô vợ/chồng cho người đó; nhánh
  chỉ có ô Con thế vị, tối đa tới chắt (Điều 652 BLDS 2015, D-012).
- Sau `Hoàn tác`, engine chạy lại trên dữ liệu hiện tại và bỏ ô vừa khôi phục
  nếu luật hiện hành không cho phép.
- Con sinh sau khi người chết: engine không có luật riêng, không cảnh báo.
- Nhãn ô do engine/UI sinh không chứa UUID/ID thô (§9.6).

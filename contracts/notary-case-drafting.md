# Contract: Notary Case Drafting `v1` (doc rev 1.1) + `v2` ở §13

**Version:** `notary.case-drafting.v1` · **Status:** APPROVED — owner duyệt
24/09/2026 (MIN-105); rev 1.1 mở rộng tương thích (MIN-121) ·
**§13 chứa `notary.case-drafting.v2` (MIN-125) — APPROVED 27/09/2026,
implement ở P5 (MIN-128)** ·
**Owner:** `systemdocs` · **Published:** MIN-105 ·
**Kênh mang:** `desktopcommand.v1` (`contracts/desktop-command.md`) ·
**Domain data shape:** `g1.module.v1` (`contracts/g1-module-data.md`)

Contract wire cho tab **Soạn hồ sơ** của module `notary_v2` trong shell
Electron một máy: mười command `notary.*` phục vụ tạo/tải workspace, intake
đa nguồn thành suggestion, commit Stage, cập nhật meta, đánh giá/lưu
Diagram, xuất
Word hàng loạt và tra cứu địa chỉ hành chính local (§14). Envelope `desktopcommand.v1` giữ nguyên — file này chỉ
định nghĩa `payload`/`result.data`/error code của từng command.
Rev 1.1 **additive** (MIN-121): thêm `notary.workspace_create` và chế độ
nháp cho `intake_analyze`/`diagram_evaluate` — `schema_version` giữ
`notary.case-drafting.v1`, mọi field mới tương thích ngược với consumer
cũ (field `case` thêm key nullable; command mới chỉ client mới gọi).

SOT hành vi nghiệp vụ: `_bmad-output/specs/notary_v2/`; chi tiết đã duyệt MIN-104 để
đối chiếu implementation nằm tại
`_bmad-output/specs/notary_v2/workspace-detail.md`. File này là wire
contract, không định nghĩa lại hành vi.
Schema chuẩn: `contracts/notary-case-drafting/*.schema.json`
(JSON Schema draft-07). Examples kiểm chứng:
`contracts/notary-case-drafting/examples/`.

**Ghi chú khác biệt có chủ đích so với plan §2:** mã job-level dùng dạng
underscore — `word_batch_failed` thay literal `word.batch_failed` trong
plan — theo convention error code của envelope (`user_canceled`,
`file_scope_not_supported`). Mã dạng `word.*` có chấm chỉ là
**data-code** trong payload/result (§2.5), không phải `error.code`
job-level. Quyết định giữ nguyên sau review round 1.

## 1. Phạm vi và danh mục command

| Command | Mục đích | Tính chất | `result.kind` |
|---|---|---|---|
| `notary.workspace_create` | Tạo hồ sơ mới từ nháp Stage + Diagram trong một transaction | atomic write, idempotent | `workspace_create` |
| `notary.workspace_get` | Tải case + Stage (Người/Tài sản) + Diagram + revision + capabilities | read-only | `workspace_get` |
| `notary.intake_analyze` | Phân tích file/text thành suggestion chờ review | long-running, không commit | `intake_analyze` |
| `notary.workspace_commit_stage` | Commit toàn bộ Stage trong một transaction | atomic write | `workspace_commit_stage` |
| `notary.workspace_update` | Cập nhật meta hồ sơ đã lưu (`ngay_lap_ho_so`, `noi_niem_yet`, `ghi_chu`) — không đụng Stage/Diagram | atomic write | `workspace_update` |
| `notary.diagram_evaluate` | Đánh giá/tính thử draft Diagram | read-only theo DB, không persist draft | `diagram_evaluate` |
| `notary.diagram_save` | Lưu Diagram đã hợp lệ | atomic write | `diagram_save` |
| `notary.word_export_options` | Liệt kê văn bản sẵn sàng/bị chặn | read-only | `word_export_options` |
| `notary.word_export_batch` | Tạo nhiều DOCX vào một folder đích | long-running, per-item result | `word_export_batch` |
| `notary.address_lookup` | Tra cứu tên xã/tỉnh hiện hành từ chuỗi người dùng gõ (ledger local, lõi dùng chung) | read-only, local-only | `address_lookup` |

- `result.kind` = tên command bỏ namespace `notary.` (snake_case nguyên
  vẹn). `result` theo shape `g1-module-data.md` §2: `{kind, data,
  evidence?, warnings?, source_files?}`.
- Mọi `result.data` của chín command **bắt buộc** mang
  `schema_version: "notary.case-drafting.v1"` (literal). Đây là version
  của domain data shape; version kênh vẫn là `contract_version` của
  envelope — hai tầng độc lập. `notary.address_lookup` (§14) là ngoại
  lệ có chủ đích: domain data riêng — `notary.address-lookup.v2`.
- Request envelope theo `desktop-command.md` §3; `client_meta.module` =
  `document-review` (module id đã claim namespace `notary.*` trong
  `shell/src/main/registry.js:16-21`).
- Không command/field/trạng thái Zalo trong contract này — module Zalo
  là phần mềm riêng.
- **Ngoài phạm vi:** mock/real backend, renderer, `command_registry.py`,
  DB migration — contract này duyệt trước, runtime implement trong các
  task sau (MIN-106…MIN-112).

## 2. Quy ước chung

### 2.1 Khóa định danh và version

| Khóa | Kiểu | Rule |
|---|---|---|
| `case.id` (`case_id`) | integer | ID hồ sơ trong DB |
| `row_id` | string UUID v4 | Do UI tạo khi thêm dòng Stage; ổn định qua commit/reload; dùng gắn lỗi đúng dòng (`field_errors[].row_id`) |
| `entity_id` | integer \| null | ID DB thật; `null` trước lần commit đầu của dòng; backend gán khi commit |
| `revision` | integer ≥ 1 | Số phiên bản workspace của case; mọi write thành công (`workspace_commit_stage`, `workspace_update`, `diagram_save`) tăng đúng 1 |
| `base_revision` | integer ≥ 1 | Revision client đang giữ khi ghi; bắt buộc trên mọi command **ghi** (`workspace_commit_stage`, `workspace_update`, `diagram_save`); khác server (`<` **hoặc** `>`) → `workspace_conflict` |
| `source_id`, `suggestion_id` | string UUID v4 | `source_id` do client sinh khi build request; `suggestion_id` do backend sinh |
| `document_key` | string `^[a-z][a-z0-9_]*$` | Khóa ổn định của văn bản; không đổi khi đổi tên hiển thị/template; registry mở — backend được thêm key mới, không được đổi nghĩa key đã publish |
| `node.id` (Diagram slot) | string non-empty | Định danh slot trên Diagram do UI đặt; khác namespace với `row_id`/`personId` |
| `personId` (Diagram node) | string UUID v4 \| null | Tham chiếu `row_id` của một **dòng Người trong Stage đã commit**; `null` = slot trống. Trong `workspace_create` và `diagram_evaluate` chế độ nháp, tham chiếu `row_id` trong **`stage` của cùng payload** (chưa commit) |
| `idempotency_key` | string UUID v4 | Bắt buộc trên `notary.workspace_create`; client sinh một lần cho mỗi nháp — retry gửi lại đúng key → backend trả cùng case (`created:false`), không tạo trùng |

### 2.1a `case_id` — bắt buộc vs chế độ nháp

- `case_id: <int ≥ 1>` **bắt buộc** trên `workspace_get`,
  `workspace_commit_stage`, `workspace_update`, `diagram_save`,
  `word_export_options`, `word_export_batch`.
- **Chế độ nháp** (hồ sơ chưa từng lưu — spec UX §2, MIN-121):
  `intake_analyze` và `diagram_evaluate` cho phép **absent** `case_id`
  = phân tích/đánh giá trên nháp phiên, không đụng DB case.
  - `case_id` absent + `diagram_evaluate` → payload PHẢI kèm `stage`
    (§7.4); `personId` trong diagram được kiểm theo stage payload đó.
  - `case_id` absent + `intake_analyze` → chỉ phân tích nguồn thành
    suggestion; result shape không đổi.
  - `case_id: null` **tường minh** → `validation_error` (phân biệt
    "thiếu = nháp" với "null = lỗi client").
  - `case_id` present nhưng không phải int ≥ 1 → `validation_error`.
- `notary.workspace_create` **không nhận** `case_id` (server gán id);
  payload có `case_id` → `validation_error`.

Kiểu ID không được đổi giữa mock và real backend.

### 2.2 Ngày và thời điểm

- Ngày không giờ (ngày sinh/chết/cấp): `YYYY-MM-DD` **hoặc** `YYYY`
  (chỉ có năm — phải giữ đúng độ đầy đủ của dữ liệu nhập) **hoặc**
  `null`. Wire chỉ hai dạng đó: producer phải chuẩn hóa mọi format khác
  (hiện trạng web trộn `dd/mm/YYYY`, `yyyy`, ISO) trước khi emit.
- Owner 15/10/2026: lưu và hiển thị đúng dữ liệu ngày đã nhập. `2010` phải
  đọc lại/hiển thị là `2010`; `01/01/2010` thật vẫn là ngày đầy đủ. Quy ước
  `01/01` cho dữ liệu chỉ có năm chỉ được dùng nội bộ khi cần tính toán;
  không ghi đè dữ liệu nhập và không tạo bằng chứng về thứ tự sự kiện chưa biết.
  Chuẩn hóa định dạng truyền không được làm mất độ đầy đủ. Cách lưu vật lý cần
  được kiểm khi triển khai; lần cập nhật docs này không đổi schema/runtime.
- Thời điểm (`updated_at`, `observed_at`): ISO-8601 có múi giờ.
- `""` **không hợp lệ** thay `null` ở mọi field nullable — consumer
  reject bằng `validation_error` (g1-module-data §6).

### 2.3 Null / boolean / cấm `confirmed`

- `null` = không quan sát được / không áp dụng. Renderer hiển thị "—".
- Boolean strict: `true`/`false` JSON; `"false"` chuỗi →
  `diagram_invalid_state` (bám rule engine `invalid_boolean`).
- Suggestion/intake **không bao giờ** mang key `confirmed` ở bất kỳ cấp
  nào. Xác nhận duy nhất = người dùng đưa gợi ý vào Stage rồi
  `Cập nhật`. Xuất hiện `confirmed` → `validation_error`.
- `Người không nhận` là nhãn derived phía sản phẩm (`Tất cả − Chủ đất −
  Nhận` — SOT ở drafting-tab §6 / workflow.md): **không** nằm trong
  contract, không phải engine output, không có field riêng.

### 2.4 `case_type` — V1 chỉ cam kết `inheritance`

- `workspace_get` trả `case.case_type` cho mọi hồ sơ; `capabilities`
  phản ánh phần nào bật (`intake`/`diagram`/`word_export`). Loại việc
  chưa có engine → `capabilities` tắt tương ứng, UI hiển thị
  `Chưa hỗ trợ`.
- Mọi command ghi/evaluate/export trên `case_type` chưa hỗ trợ →
  `failed{code:case_type_unsupported}` — không chạy logic giả.
- `Chưa hỗ trợ` cấp **loại việc** (case_type) khác `unsupported` cấp
  **kết quả engine** (§7) — hai tầng riêng.

### 2.5 Error object, `validation_error` và data-codes

- Shape `error` theo `desktop-command.md` §4
  (`code/message/retryable/next_action/job_id/details`).
- `validation_error` là mã **chung** cho vi phạm shape không có mã
  riêng: sai kiểu, thiếu field bắt buộc, `""` thay null, `confirmed`
  cấm, `is_dir` sai ngữ cảnh, date format sai ngoài Stage row. Mã nghiệp
  vụ riêng liệt kê ở §9 — ưu tiên dùng mã riêng khi có.
- `error.code` job-level dạng `snake_case` **không chấm** (theo
  convention envelope `user_canceled`, `file_scope_not_supported`).
- **Data-codes** là registry mở các mã nằm **trong dữ liệu**, không phải
  `error.code` job-level: `block_reason` (§8.1), per-file
  `documents[].error.code` (§8.4), intake `errors[].code` (§5.3),
  `warnings[].code`, engine `errors[].code` (§7.3). Dạng
  `<ns>.<snake_case>` (vd `word.template_missing`,
  `intake.parse_failed`, `intake.low_confidence`,
  `diagram.unassigned_pool_person`, `intake.unsupported_target`).
  Producer được thêm mã mới vào registry này; consumer render theo mã,
  không parse `message`.

## 3. FileRef — mở rộng `is_dir`

Contract này **mở rộng** FileRef của `desktop-command.md` §6 thêm một
field optional — tương thích ngược (rule 1, §8 envelope):

```yaml
file_ref:
  path: <absolute path>        # cho phép \\?\ prefix; KHÔNG tương đối
  scope: machine_local
  is_dir: <boolean, optional>  # true = tham chiếu thư mục
  sha256: <optional>
  media_type: <optional>
  size_bytes: <optional>
```

Rule (quyết định owner 2A):

- FileRef dùng làm **destination** của `word_export_batch` PHẢI có
  `is_dir: true`, path absolute local, `scope: machine_local`, **cấm
  UNC**, và path phải là folder **đang tồn tại**. Thiếu `is_dir:true`
  hoặc `is_dir:false` → `validation_error`; UNC/scope khác →
  `file_scope_not_supported`.
- FileRef tham chiếu **file** (intake source, `output_file`): `is_dir`
  phải absent hoặc `false`; `is_dir:true` → `validation_error`.
- FileRef của intake source **bắt buộc** khai `size_bytes` để pre-check
  giới hạn §5.2 trước khi đọc file.

## 4. `notary.workspace_get` — payload + result

```yaml
payload:
  case_id: <int>
```

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  backend_mode: real | mock        # optional; default "real" — mock
                                   # PHẢI trả "mock" (nhãn "Dữ liệu mô phỏng")
  case:
    id: <int>
    case_type: <string>            # v1 cam kết "inheritance"; giá trị khác → xem §2.4
    document_type: khai_nhan | thoa_thuan
    status: draft | locked
    locked: <bool>
    revision: <int ≥ 1>
    ngay_lap_ho_so: <YYYY-MM-DD | null>   # ngày lập hồ sơ (rev 1.1)
    noi_niem_yet: <string | null>        # nơi niêm yết (rev 1.1)
    nguoi_nhan_uy_quyen: <string | null>  # tên người nhận ủy quyền —
                                        # denormalized từ danh bạ (đợt 3)
    nguoi_nhan_uy_quyen_id: <int | null>  # tham chiếu ổn định tới
                                        # customers.id (đợt 3)
    noi_dung_viec: <string | null>       # cụm nội dung việc (đợt 3)
    ghi_chu: <string | null>             # ghi chú hồ sơ (rev 1.1)
  stage:
    people: [<person_row>]         # §4.1
    assets: [<asset_row>]          # §4.2
  diagram:
    domain: <string>               # v1: "inheritance"
    state: <diagram_state>         # §7.1
    render_model: <render_model | null>   # §7.2 — cache lần evaluate/save gần nhất
    warnings: [{code, message}]    # optional — cảnh báo ngoài engine
  capabilities:
    intake: [image | pdf | docx | xlsx | text]
    diagram: <bool>
    word_export: <bool>
```

- `stage` luôn trả cấu trúc `{people, assets}` kể cả rỗng (`[]`).
- `diagram.render_model` luôn là output của lần evaluate/save/commit
  gần nhất và **khớp `state` hiện tại** — `workspace_commit_stage`
  re-evaluate sau khi prune (§6.1) nên không có render_model cũ lệch
  state; `null` chỉ khi hồ sơ chưa từng được evaluate.
- `case.locked:true` → mọi command **ghi** (`workspace_commit_stage`,
  `workspace_update`, `diagram_save`, `word_export_batch`) →
  `failed{code:workspace_locked}`; các command read-only — kể cả
  `diagram_evaluate` — vẫn được phép (§7.4).
- `case_id` không tồn tại → `failed{code:case_not_found}`.
- `backend_mode` là field duy nhất phân biệt mock/real; renderer bắt
  buộc hiển thị nhãn khi `mock`.

### 4.1 `person_row` — dòng Người Stage

```yaml
person_row:
  row_id: <uuid4>
  entity_id: <int | null>
  ho_ten: <string non-empty>         # bắt buộc
  gioi_tinh: Nam | Nữ | null
  ngay_sinh: <YYYY-MM-DD | YYYY | null>
  ngay_chet: <YYYY-MM-DD | YYYY | null>   # null = không có thông tin ngày chết
  so_giay_to: <string | null>        # số giấy người sống hoặc khai tử/chứng tử;
                                     # free text, được trùng; gợi ý/liên kết do user chọn (§8.3 entities), UX chưa triển khai
  ngay_cap: <YYYY-MM-DD | YYYY | null>
  noi_cap: <string | null>
  dia_chi: <string | null>
  place_of_origin: <string | null>   # giữ để đọc snapshot cũ; intake/UI
                                     # hiện hành không dùng — engine không
                                     # điền (Owner 06/10/2026)
  loai_giay_to: <string | null>      # (đợt 3) loại giấy tờ ĐÃ XÁC NHẬN —
                                     # người chết: lựa chọn/OCR của user;
                                     # người sống: server suy theo mốc
                                     # ngay_cap 01/10/2024 khi trống
  loai_dia_chi: <string | null>      # (đợt 3) nhãn địa chỉ — Thường trú
                                     # tại/Cư trú tại/Nơi chết; server suy
                                     # khi trống
```

Không thêm field ngoài danh sách này — producer strip field lạ (tiền lệ
backend hiện strip ngoài 10 key). `ho_ten` rỗng/`""` →
`stage_validation_error{field:ho_ten, code:required}`.

**Owner 21/10/2026 — nghĩa trường đã chốt, đã giao runtime hẹp, không đổi wire/key:**
- `dia_chi` là **một trường hiện có** dùng chung cho `Nơi chết` và nơi thường
  trú/cư trú cuối cùng của người chết. Không tạo field mới hoặc chọn ngầm khi
  giá trị mâu thuẫn. Địa chỉ chung ghi rõ trong cùng văn bản chỉ áp đúng nhóm.
- Ba loại người chết: `Trích lục khai tử`, `Trích lục khai tử (bản sao)`,
  `Giấy chứng tử`; `Giấy chứng tử (bản sao)` nguồn quy về `Giấy chứng tử`.
  Số giữ nguyên giá trị gồm dấu phẩy/quyển, nhãn ngoài số. `ngay_cap` là ngày
  cấp chính giấy; `noi_cap` giữ loại đơn vị xã/phường/thị trấn, không ép xã,
  tên lịch sử theo ngày cấp giấy, không suy bằng lịch sử chưa xác nhận.
- Mỗi văn bản độc lập: **không đề xuất bổ sung, không tự ghép giữa văn bản**
  kể cả cùng bộ hồ sơ, không mượn trường thiếu hoặc chọn bản đầy nhất/mới
  nhất. Không gợi ý sinh/chết/giấy tờ Người từ `Đơn xin xác nhận`.
  Đây không cấm gợi ý ID theo CCCD/liên kết user chọn bên dưới; không được
  biến lựa chọn liên kết thành auto enrichment hay tự ghi đè master.
- `ngay_chet=null` chỉ là không có thông tin ngày chết, không tự kết luận
  còn sống. Các trường hợp lệ khác được điền độc lập; thiếu ngày chết/giấy
  không chặn Người. Không tạo ngày giả/01/01, Boolean hoặc status mới.
  Không xóa raw/history, phá liên kết đã có hoặc đổi logic câu Word.

**Identity/persistence hiện tại (không phải chuẩn đích toàn bộ):** số giấy
không UNIQUE, không lookup/ghép Người theo số/tên; cho phép số CCCD trùng.
Chỉ ID được chọn rõ hoặc row_id trong snapshot của chính hồ sơ cập nhật
lại cùng Người; trùng entity vẫn bị từ chối.
Loại/nơi cấp/nhãn nguồn giữ trong snapshot; key đã có kể cả null chặn
borrow master. Ngày chết thiếu nhưng có loại giấy chết/nhãn Nơi chết nguồn
thì không derive CCCD/issuer người sống. Migration giữ IDs/FKs/history,
không thêm field/version. Actual proof synthetic fresh+migrated DB/Word đạt;
**BUILT bounded hẹp**, chưa nghiệm thu #41.
**Policy owner 21/10 thay thiết kế UNIQUE của `6eaf42b`, UX chưa triển khai:**
một bảng Người, `Customer.id` ổn định; chết vẫn là cùng Người. CCCD đã có DB
thì gợi ý Người/ID cũ; user bấm chọn liên kết dòng input với ID đó, gợi ý
biến mất. Sai khác trường không chặn, ghi vào “thông tin liên kết” để user
xem/xóa/sửa bất cứ lúc nào. Không chọn/bỏ qua → tạo ID mới, không auto merge.
Lifecycle gợi ý bị bỏ qua và shape/key/nơi lưu/cardinality thông tin liên kết
còn mở trong [#44](../_bmad-output/backlog/story-person-cccd-suggestion-link.md);
không tự thêm nút, modal hay xác nhận. Chưa chọn field/model vật lý.
Liên kết explicit không tự chọn field thắng/ghi đè master hoặc auto enrichment
giữa văn bản. Runtime hiện tại cập nhật master qua ID rõ, chưa có đầy đủ UX này;
không coi đó là thực hiện policy mới. Chi tiết ở [entities §8.3](entities.md#83-owner-21102026--gợi-ý-cccd-người-dùng-quyết-định-liên-kết).
#41 OPEN/gate mẫu ĐÓNG; #42 độc lập. Không làm conditional UNIQUE/chặn CCCD.

- **Key canonical (MIN-141 đợt 3):** server đọc được cả key wire legacy
  trên và tên nghiệp vụ canonical liền không dấu (entities.md §9.1):
  `ten`↔`ho_ten`, `gioitinh`↔`gioi_tinh`, `ngaysinh`↔`ngay_sinh`,
  `ngaychet`↔`ngay_chet`, `sogiayto`↔`so_giay_to`, `ngaycap`↔`ngay_cap`,
  `noicap`↔`noi_cap`, `diachi`↔`dia_chi`, `loaigiayto`↔`loai_giay_to`,
  `loaidiachi`↔`loai_dia_chi`. Cùng trường ở cả hai spelling mà giá trị
  mâu thuẫn → `validation_error`. Wire emit giữ bộ legacy.
- **Giá trị suy ra:** người sống thiếu `loai_giay_to`/`noi_cap`/
  `loai_dia_chi` → derive theo mốc `ngay_cap` 01/10/2024; thiếu ngày cấp
  không suy. Khi có ngày chết **hoặc** loại giấy chết/nhãn `Nơi chết` có
  nguồn trong snapshot, server không dựng CCCD/nơi cấp người sống; loại/nơi
  cấp theo bằng chứng được xác nhận, nhãn địa chỉ `Nơi chết`. Không biến
  mọi người thiếu ngày chết thành người chết hoặc thêm field trạng thái.
- **Phân biệt bằng chứng xác nhận vs giá trị suy ra (MIN-141 fix
  `eff4f12`):** giá trị suy ra đã ghi trong snapshot trước KHÔNG được
  coi là bằng chứng người dùng xác nhận. Tại commit mới, server tính
  lại giá trị suy ra trước đó từ input nguồn của **snapshot của chính
  hồ sơ** (`ngay_chet`/`ngay_cap` đã lưu trong `case_state_json`), không
  lấy master live — master dùng chung có thể đã bị hồ sơ khác sửa. Row
  incoming echo đúng giá trị suy ra trước đó hoặc trống → tính lại theo
  input nguồn mới; row incoming khác giá trị suy ra trước đó → đó là
  bằng chứng đã xác nhận → giữ nguyên (kể cả giấy khai tử người chết).
- **Word đọc bằng chứng Người từ snapshot (MIN-141 fix `eff4f12`):**
  các slot Người trong Word (`[tenN]`…`[loaigiaytoN]`/`[noicapN]`/`[loaicutruN]`
  và alias cũ) đọc từ phần tử `stage[]` đã commit trong
  `case_state_json` của chính hồ sơ — đối chiếu theo `id` entity, giữ
  nguyên thứ tự slot legacy. Ngữ nghĩa key-presence: key có trong
  snapshot (kể cả `null`) → dùng snapshot; key vắng → fallback master
  live cho hồ sơ cũ. Hai hồ sơ dùng chung một `Customer` xuất đúng
  bằng chứng riêng đã commit, không bị sửa master kéo lệch nhau.
- **Độ đầy đủ ngày Người (Owner 15/10/2026):** cùng ngữ nghĩa key-presence áp
  cho ba field ngày: `workspace_get`/`create`/`commit_stage` emit đúng giá trị
  đã commit trong snapshot (`YYYY` giữ nguyên năm riêng, không đệm thành
  `YYYY-01-01`); snapshot vắng key ngày → fallback master và ghi nhận là dạng
  đầy đủ. Ngày quy ước `date(y,1,1)` chỉ dùng trong tính toán nội bộ, không
  ghi đè giá trị đã biết.

### 4.2 `asset_row` — dòng Tài sản Stage

```yaml
asset_row:
  row_id: <uuid4>
  entity_id: <int | null>
  is_primary: <bool>
  so_serial: <string>                # nguyên văn tùy nguồn, có thể rỗng,
                                     # có thể trùng — entities.md §2
                                     # (Owner 06/10/2026: không ép format)
  so_vao_so: <string | null>
  so_thua_dat: <string | null>
  so_to_ban_do: <string | null>
  dia_chi: <string non-empty>        # bắt buộc
  loai_so: <string | null>
  hinh_thuc_su_dung: <string | null>
  thoi_han: <string | null>          # lẻ cấp tài sản — CHỈ còn nghĩa trên
                                     # emit/legacy (xem ghi chú dưới)
  nguon_goc: <string | null>
  ngay_cap: <YYYY-MM-DD | null>      # asset chỉ nhận dạng đầy đủ
  co_quan_cap: <string | null>
  land_rows:
    - loai_dat: <string | null>
      dien_tich: <number | null>
      thoi_han: <string | null>
```

- `assets` non-empty → **đúng một** dòng `is_primary:true`; 0 hoặc ≥2 →
  `stage_validation_error{code:primary_count}`.
- `land_rows` null-safe: thiếu/`[]` hợp lệ; phần tử null-safe từng field.
- **`thoi_han` lẻ cấp tài sản (MIN-141):** phía input (payload
  `workspace_create`/`workspace_commit_stage`/`diagram_evaluate` nháp) KHÔNG
  còn bắt buộc — schema `asset_row_input`. Client mới không gửi key này;
  key vắng nghĩa là "giữ nguyên giá trị lịch sử trên master", server không
  xóa. Client legacy vẫn được phép gửi key (giá trị sẽ ghi như cũ). Phía
  emit (`workspace_get`/result.data.stage) server vẫn luôn trả key
  `thoi_han` (nullable) — schema `asset_row` — để đối chiếu lịch sử và báo
  `stage.orphan_thoi_han` khi giá trị lẻ không gắn cụm nào. Thời hạn mới
  chỉ thuộc `land_rows[].thoihan`; không tự đắp giá trị lẻ vào cụm.
- **Key cụm đất (MIN-141 đợt 2):** tên nghiệp vụ canonical mới là
  `loaidat` / `dientich` / `thoihan` (trùng cột bảng con
  `property_land_rows` và tên placeholder Word `loaidat<M><N>`... —
  entities.md §9.2). Server đọc được cả bộ legacy
  `loai_dat`/`dien_tich`/`thoi_han` để UI hiện hành không hỏng; wire
  emit tiếp tục dùng bộ legacy (shape trên không đổi). Trong một phần
  tử, cặp cũ-mới của cùng trường mang giá trị **mâu thuẫn** →
  `stage_validation_error` (`code:"conflict"`), không âm thầm chọn một.
  Vị trí cụm = index trong `land_rows` + 1 (cột `vitri`), kể cả dòng
  trống hoàn toàn — giữ nguyên vị trí trống.

### 4.3 `notary.workspace_create` — tạo hồ sơ từ nháp (rev 1.1)

```yaml
payload:
  idempotency_key: <uuid4>          # §2.1 — client sinh 1 lần/nháp
  case:
    document_type: khai_nhan | thoa_thuan    # bắt buộc
    ngay_lap_ho_so: <YYYY-MM-DD | null>      # optional, default null
    noi_niem_yet: <string | null>            # optional, default null
    nguoi_nhan_uy_quyen: <string | null>     # (đợt 3) tên người được ủy
                                           # quyền — optional
    nguoi_nhan_uy_quyen_id: <int | null>     # (đợt 3) customers.id — tham
                                           # chiếu ổn định; id có → tên
                                           # resolve theo danh bạ, id sai →
                                           # validation_error; name+id lệch
                                           # nhau → validation_error
    noi_dung_viec: <string | null>           # (đợt 3) cụm nội dung việc
    ghi_chu: <string | null>                 # optional, default null
  stage:
    people: [<person_row>]          # ≥1; entity_id phải null
    assets: [<asset_row>]           # ≥1; đúng một is_primary:true;
                                    # entity_id phải null
  diagram:
    state: <diagram_state>          # §7.1 — personId tham chiếu row_id
                                    # trong stage của payload này
```

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  backend_mode: real | mock
  created: <bool>                   # true = vừa tạo; false = idempotent
                                    # replay trả case đã có
  case: <case>                      # shape §4 — revision: 1
  stage: {people, assets}           # snapshot sau tạo — entity_id đã gán
  diagram:
    domain: "inheritance"
    state: <diagram_state>          # state đã persist
    render_model: <render_model | null>   # kết quả evaluate tại thời
                                          # điểm tạo (null nếu state
                                          # không evaluate được — xem
                                          # semantics)
    warnings: [{code, message}]
  capabilities: {intake, diagram, word_export}
```

Semantics:

- **Một transaction:** validate → tạo case + person + asset + link +
  persist stage/diagram + `revision=1` → commit. Một phần sai → rollback
  trọn vẹn, không ghi nửa vời. Lỗi field Stage → `stage_validation_error`
  (đủ `{row_id, field, code, message}`); diagram sai →
  `diagram_invalid_state` / `diagram_reference_outside_stage`.
- **Owner bắt buộc:** node `id == "owner"` (chính xác một, không
  `deleted`) phải có `personId` trỏ tới đúng một `person_row` trong
  payload → người để lại di sản của case. Thiếu/`null` →
  `failed{code:workspace_owner_required}`. Cờ `isLandOwner` là nghiệp vụ
  engine riêng — **không** thay thế được yêu cầu owner này.
- **Đúng một `is_primary:true`** trong `assets` — rule `primary_count`
  của §4.2 áp dụng và `assets` rỗng → `stage_validation_error`
  (`primary_count=0`). `assets` rỗng/people rỗng → `stage_validation_error`.
- **Idempotent:** `idempotency_key` được persist; request lặp cùng key —
  kể cả sau retry mạng/timeout — trả cùng case với `created:false`,
  không tạo bản ghi trùng. Key khác nhau = nháp khác nhau → case mới.
  Không suy ra giống-nhau-về-nội-dung.
- `case_type` luôn `"inheritance"` (V1); `status:draft`, `locked:false`,
  `revision:1`.
- `case` trong payload chỉ chứa meta cho phép: `document_type`,
  `ngay_lap_ho_so`, `noi_niem_yet`, `ghi_chu` — field khác →
  `validation_error` (additionalProperties false).
- `notary.case_create` legacy giữ nguyên — command này là đường tạo hồ sơ
  duy nhất của tab Soạn hồ sơ.

## 5. `notary.intake_analyze` — payload + result

### 5.1 Payload

```yaml
payload:
  case_id: <int>                    # §2.1a — absent = chế độ nháp;
                                    # null → validation_error
  sources:                          # 1..8 phần tử
    - source_id: <uuid4, client sinh>
      kind: image | pdf | docx | xlsx | text
      file_ref: <file_ref>          # bắt buộc khi kind ≠ text; cấm khi
                                    # kind = text
      text: <string non-empty>      # bắt buộc khi kind = text; cấm khi
                                    # kind ≠ text
```

### 5.2 Giới hạn contract v1

| Giới hạn | Giá trị | Code khi vi phạm |
|---|---|---|
| Số sources | ≤ 8 | `intake_too_many_sources` |
| Kích thước mỗi file | ≤ 20 MB | `intake_source_too_large` |
| Số trang PDF | ≤ 50 | `intake_source_too_large` |
| Độ dài `text` | ≤ 100.000 ký tự | `intake_text_too_long` |
| `kind` ngoài enum | — | `intake_unsupported_source` |

Backend được siết **chặt hơn** các giới hạn này (vd ảnh ≤ 8MB) nhưng
**không được nới** — client căn cứ bảng trên để pre-check.
`source_id` trùng trong cùng request → `validation_error`.

### 5.3 Result

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  suggestions:
    - suggestion_id: <uuid4>
      source_id: <uuid4>            # echo nguồn sinh ra
      target: person | asset
      fields:
        <field_name>:               # vd ho_ten, ngay_sinh, so_serial
          raw_value: <string | null>
          normalized_value: <string | number | null>
          observation_state: observed | normalized | inferred
          confidence: <number 0..1 | null>   # chỉ ý nghĩa khi inferred
          source_refs: [<object>]   # vd {page:1}, {cell:"B3"} — shape
                                    # tự do theo adapter, không PII ngoài
                                    # nội dung nguồn đã gửi
      warnings: [{code, message}]
  errors:                           # lỗi theo từng nguồn — không làm
    - source_id: <uuid4 | null>     #   mất suggestion của nguồn khác
      code: <data-code>             # <ns>.<snake>, registry mở — §2.5
      message: <string>
```

- `observation_state` chỉ ∈ `observed|normalized|inferred` — **không
  `confirmed`** (§2.3). `normalized_value:null` hợp lệ khi
  `observed`; khi `normalized|inferred` nên có giá trị.
- Job lifecycle: `running → succeeded | partial`. Không dùng
  `waiting_on` — review là thao tác client-side sau khi job xong.
- `partial` khi một phần nguồn lỗi: bắt buộc
  `result.data.breakdown={succeeded:[<source_id>], failed:[<source_id>]}`
  (quy tắc `partial` của envelope §5).
- Suggestion **không** tự ghi hồ sơ/tạo quan hệ/chọn người nhận/xuất
  Word — chỉ hiển thị review (drafting-tab §5).
- Loại `marriage` của pipeline OCR hiện trạng **ngoài phạm vi V1**:
  intake chỉ emit `target: person|asset`; quan hệ vợ chồng được gán tay
  trên Diagram (`spouseSlotId`), không qua suggestion. Adapter gặp loại
  không map được có thể ghi `errors[]` với data-code
  `intake.unsupported_target`.
- `case_id` present nhưng không tồn tại/`locked`/case_type khác →
  `case_not_found`/`workspace_locked`/`case_type_unsupported`. Engine
  OCR thiếu → `engine_not_installed` (reuse envelope §8).
  Chế độ nháp (`case_id` absent) bỏ qua các kiểm tra case — suggestion
  không gắn hồ sơ nào.

## 6. `notary.workspace_commit_stage` — payload + result

```yaml
payload:
  case_id: <int>
  base_revision: <int ≥ 1>
  case:                             # (đợt 3) OPTIONAL — metadata hồ sơ
                                    # ghi cùng Stage trong một transaction
    ngay_lap_ho_so: <YYYY-MM-DD | null>    # null = giữ nguyên (NOT NULL)
    noi_niem_yet: <string | null>          # canonical `noiniemyet` cũng OK
    nguoi_nhan_uy_quyen: <string | null>   # `nguoinhanuyquyen`
    nguoi_nhan_uy_quyen_id: <int | null>   # `nguoinhanuyquyenid`
    noi_dung_viec: <string | null>         # `noidungviec`
    ghi_chu: <string | null>               # `ghichu`
  stage:
    people: [<person_row>]
    assets: [<asset_row>]
```

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  revision: <int>                  # revision mới sau commit
  stage:
    people: [<person_row>]         # snapshot sau commit — entity_id
    assets: [<asset_row>]          #   đã gán cho dòng mới
  diagram:
    state: <diagram_state>         # state sau prune — §6.1
    render_model: <render_model>   # non-null — kết quả re-evaluate
                                   # trong cùng transaction — §6.1
```

### 6.1 Semantics

- **Atomic:** validate → upsert/link → prune Diagram → **re-evaluate
  Diagram đã prune** → `revision+1` → commit, trong **một
  transaction**. Một dòng sai → Stage không đổi. `render_model` mới được
  lưu cùng state để `workspace_get` luôn trả model khớp state hiện tại.
- **`payload.case` (đợt 3):** metadata hồ sơ ghi cùng transaction —
  validate fail hoặc stage fail → không cái nào ghi. `case_type`/
  `document_type` gửi kèm phải khớp giá trị đã lưu (immutable qua
  commit — **trừ đường chuyển loại đã duyệt**, §13.18) — khác →
  `validation_error`. `nguoi_nhan_uy_quyen_id` phải
  tồn tại trong `customers`; kèm `nguoi_nhan_uy_quyen` lệch tên master →
  `validation_error`. Snapshot `case_state_json` đóng băng meta dưới
  block `payload.case` với key **canonical**
  (`noiniemyet`,`nguoinhanuyquyen:{id,ten}`,`noidungviec`,
  `ngaylaphoso`,`ghichu`) — Word đọc meta từ block này trước, cột
  `inheritance_cases` chỉ là fallback cho hồ sơ cũ.
- **Metadata Case Upload (owner 19/10, phạm vi Case):** create/commit nhận thêm
  `tenvanban`, `nhomhopdong`, `loaivanbannhandien`, `socongchung`,
  `ngaycongchung`, `congchungvien`, `thuky` theo entities §9.4; key không gửi
  khi commit giữ snapshot cũ, `null` là xóa giá trị. `workspace_get/create`
  emit cùng key và `chudat` chỉ đọc, derived từ Diagram đã lưu + tên Stage.
  `chudat` không là input tự do; slot owner/người chết không tự là chủ đất.
  Lựa chọn Chủ phải trỏ tài sản hiện có, không hidden/deleted. Metadata mới
  không thay enum Notary, không tự nối Upload với DB Notary hoặc khép #41.
- `base_revision` khác `revision` hiện server — **nhỏ hơn HOẶC lớn
  hơn** — → `failed{code:workspace_conflict,
  details:{server_revision}}`. Không có ghi đè cưỡng bức — client tải
  bản mới hoặc giữ nháp.
- Xóa phần tử khỏi Stage → backend prune mọi `personId`/`slot` Diagram
  tham chiếu phần tử đó trong cùng transaction; `diagram.state` trả về
  đã prune.
- `row_id` trùng trong payload → `stage_validation_error`
  `{code:duplicate_row_id}`.
- Lỗi field → `failed{code:stage_validation_error,
  details.field_errors:[{row_id, field, code, message}]}`. `code` nội
  bộ gợi ý: `required, invalid_type, invalid_enum, invalid_date,
  invalid_format, duplicate_row_id, primary_count, duplicate_entity`
  (rev 1.1 — `duplicate_entity` khi row gắn `entity_id` trùng một entity
  đã thuộc Stage/cùng payload).
- `so_serial` nhận chuỗi bất kỳ kể cả rỗng — không ép format
  (entities.md §2, Owner 06/10/2026); `so_giay_to` không ép format.
- Stage Người trùng tên/tài sản trùng là quyền người dùng — backend
  không tự merge.

### 6.2 `notary.workspace_update` — cập nhật meta hồ sơ đã lưu (NAIA-8)

```yaml
payload:
  case_id: <int>
  base_revision: <int ≥ 1>
  case:
    ngay_lap_ho_so: <YYYY-MM-DD | null>   # optional
    noi_niem_yet: <string | null>          # optional
    ghi_chu: <string | null>               # optional
```

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  revision: <int>                  # revision mới sau update
  case: <case>                     # shape §4 — meta mới
```

- `payload.case` chỉ chứa meta cập nhật được: `ngay_lap_ho_so`,
  `noi_niem_yet`, `ghi_chu` — key lạ (kể cả `case_type`,
  `document_type` — định danh nghiệp vụ không đổi sau create) →
  `validation_error`; `case` rỗng/không phải object →
  `validation_error`. Chỉ key nào có mặt mới được cập nhật.
- Validate giá trị theo §4.3 (`noi_niem_yet`/`ghi_chu`: chuỗi non-empty
  hoặc `null`; `ngay_lap_ho_so`: `YYYY-MM-DD` hoặc `null`).
- **Không** đụng Stage/Diagram: `people`/`assets`/`state` giữ nguyên;
  `revision` tăng đúng 1 như mọi write khác; `base_revision` khác server
  → `workspace_conflict`; case locked → `workspace_locked`; `case_id`
  không tồn tại → `case_not_found`.
- Dùng cho ô meta trong dialog Xuất Word (Nơi niêm yết) và các chỉnh sửa
  meta tương lai — không tạo nguồn lưu meta thứ hai ngoài case DB.
- Tích hợp MIN-141 (04/10/2026): cập nhật đúng key canonical trong
  `case_state_json.case` cùng cột hồ sơ, trong cùng transaction/revision.
  Không thay các key metadata khác, Stage, tài sản hoặc Diagram. Hồ sơ legacy
  chưa có snapshot giữ đường đọc legacy, không tạo snapshot thiếu Stage.
  Result giữ đủ `nguoi_nhan_uy_quyen`, `nguoi_nhan_uy_quyen_id`, `noi_dung_viec`
  theo case shape MIN-141; schema `workspace-update.schema.json` đã đối chiếu.

## 7. `notary.diagram_evaluate` + `notary.diagram_save`

### 7.1 `diagram_state` — wire ENGINE V2 (không legacy JS)

```yaml
diagram_state:
  version: 2                        # literal — khác → diagram_invalid_state
  nodes:
    - id: <string non-empty>        # slot id — vd father, mother,
                                    #   spouse, owner, child_1, sibling_1
      personId: <uuid4 | null>      # row_id dòng Người trong Stage
                                    #   ĐÃ COMMIT; null = slot trống
      parentSlotIds: [<node.id>]    # 0..2 — tham chiếu slot cha/mẹ
      spouseSlotId: <node.id | null>
      isLandOwner: <bool>
      willReceive: <bool>
      hidden: <bool>
      deleted: <bool>
```

- `personId` PHẢI là `row_id` tồn tại trong `stage.people` đã commit →
  vi phạm → `failed{code:diagram_reference_outside_stage}`. Áp dụng cả
  `workspace_get` result (server emit tham chiếu ngoài Stage = vi phạm
  contract).
- `parentSlotIds`/`spouseSlotId` tham chiếu `node.id` trong cùng
  `nodes`; dangling/self/>2/cycle → `diagram_invalid_state` với
  `details.errors[]` mang engine code (§7.3).
- `assignments` **không** tồn tại như dữ liệu persist riêng — suy ra từ
  `nodes[].personId` trên node **active** (`deleted:false`); `personId`
  giữ trên tombstone không giữ người ngoài Pool. `hidden`/`deleted` giữ
  trong state (engine bỏ qua node `deleted`).
- `version` literal `2` (engine `ENGINE_VERSION=2`); legacy JS shape
  (`parentSlotId`, `parentPersonId`, `familyGroupId`, `role`,
  `relationType`, `person` embedded) **không** thuộc wire này.

### 7.2 `render_model` — output engine đã cache

```yaml
render_model:                       # null = chưa từng evaluate
  engineVersion: 2
  status: invalid | unsupported | incomplete | complete
  allocations:
    <personId>:
      baseShare: <fraction string, vd "1/2" hoặc "1">
      inheritedShare: <fraction>
      distributedShare: <fraction>
      finalShare: <fraction>
      displayPercent: <string, vd "50.00">
  breakdowns:
    - personId: <uuid4>
      total: <fraction>
      terms:
        - kind: base | inheritance | representation
          fraction: <fraction>
          sourcePersonId: <uuid4 | null>
          viaBranchPersonIds: [<uuid4>]
  requiredSlots:
    - anchorSlotId: <node.id>
      reason: active_estate | representation_branch
      slotTypes: [father | mother | spouse | child]
      minimumEmptyChildSlots: <int>
  warnings: [{code, message}]
  errors: [{code, message, ...details}]
  unresolvedEstates:
    - sourcePersonId: <uuid4>
      eventDate: <YYYY-MM-DD | null>
      fraction: <fraction>
      reason: no_valid_heir
  conservation:
    allocated: <fraction>
    unresolved: <fraction>
    total: <fraction>
```

- `status:unsupported` **reserved** cho trường hợp engine chưa hỗ trợ
  (code hiện chưa sinh trạng thái này — spec.md §8 DRAFT). Candidate
  error code khi unsupported: `second_order_required`,
  `representation_depth_exceeded`. Không trình bày `unsupported` như
  kết quả đã tính.
- `allocations` phủ mọi active person (kể cả share `0`); `breakdowns`
  chỉ người có `finalShare > 0`. `unresolvedEstates[].reason` v1 chỉ
  `no_valid_heir`.
- Fraction biểu diễn chuỗi `"a/b"` hoặc số nguyên dạng string
  (`"1"`, `"0"`) theo output engine — consumer **không** tự tính tỷ lệ;
  `Xem cách tính` chỉ đọc output này (drafting-tab §6).

### 7.3 Engine error codes

Dùng trong `render_model.errors[]` và
`diagram_invalid_state.details.errors[]`.

Bộ code thật của engine v2:

```
invalid_input, invalid_version, invalid_nodes, invalid_node,
missing_node_id, duplicate_node_id, invalid_parent_slots,
invalid_boolean, duplicate_person, unknown_person, too_many_parents,
dangling_parent, self_parent, dangling_spouse, self_spouse,
spouse_conflict, ancestry_cycle, invalid_death_date, missing_land_owner,
conservation_failed
```

Reserved cho `unsupported`: `second_order_required`,
`representation_depth_exceeded`.

### 7.4 `notary.diagram_evaluate` — payload + result

```yaml
payload:
  case_id: <int>                    # §2.1a — absent = chế độ nháp;
                                    # null → validation_error
  stage:                            # BẮT BUỘC khi case_id absent; cấm
    people: [<person_row>]          # khi case_id present
    assets: [<asset_row>]
  diagram:
    state: <diagram_state>          # draft state — KHÔNG persist
```

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  evaluated_revision: <int | null>  # revision Stage server dùng để
                                    # evaluate — client so với revision
                                    # đang giữ để cảnh báo Stage đã đổi;
                                    # null trong chế độ nháp
  render_model: <render_model>
```

- Read-only theo DB: evaluate **không** ghi state, không đổi Stage,
  không đổi revision. Vì read-only, evaluate **được phép trên case
  `locked`** (chỉ các command ghi bị `workspace_locked`).
- `personId` ngoài Stage → `diagram_reference_outside_stage` — Stage của
  case khi `case_id` present; Stage trong payload khi chế độ nháp.
  State sai cấu trúc → `diagram_invalid_state`.
- Chế độ nháp (`case_id` absent): `stage` trong payload thay thế Stage
  DB; `diagram` được đánh giá trên đó; `evaluated_revision: null`;
  `personId` trỏ `row_id` của stage payload (§2.1). `stage` vẫn phải qua
  validation của `person_row`/`asset_row` (sai → `stage_validation_error`,
  không phải `validation_error`).

### 7.5 `notary.diagram_save` — payload + result

```yaml
payload:
  case_id: <int>
  base_revision: <int ≥ 1>
  diagram:
    state: <diagram_state>
```

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  revision: <int>                   # revision mới — save cũng tăng
                                    # revision (một counter workspace)
  diagram:
    state: <diagram_state>          # state đã persist (đã prune nếu có)
    render_model: <render_model>    # kết quả evaluate tại thời điểm save
```

- Atomic write: validate state → evaluate → persist → `revision+1` →
  commit. State invalid → không persist (`diagram_invalid_state`).
- Save **không** đổi `stage.people`/`stage.assets` (drafting-tab §6).
- `base_revision` khác revision server (cả nhỏ hơn lẫn lớn hơn) →
  `workspace_conflict`; case locked → `workspace_locked`.

## 8. `notary.word_export_options` + `notary.word_export_batch`

### 8.1 `notary.word_export_options`

```yaml
payload:
  case_id: <int>
  template_dir: <file_ref is_dir:true>   # optional (NAIA-8) — folder mode
```

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  documents:
    - document_key: <snake_case | basename .docx>
      display_name: <string>
      ready: <bool>
      block_reason: <null | code>   # chỉ khi ready:false
```

`block_reason` code hóa (v1 — data-code dạng `word.*`, §2.5):

```
word.no_people              # Stage chưa có người nào (NAIA-8)
word.no_diagram             # hồ sơ chưa lưu diagram state (NAIA-8)
word.no_assets              # hồ sơ chưa có tài sản
word.no_landowner           # chưa có chủ đất trên Diagram (inheritance)
word.no_deceased_landowner  # không có chủ đất đã chết (inheritance)
word.no_receiver            # chưa có người nhận (inheritance)
word.too_many_assets        # > 5 tài sản
word.too_many_people        # Stage: > 20 người (inheritance) / > 30 (two_party)
word.too_many_signers       # > 20 người ký (inheritance)
word.template_missing       # văn bản chưa có template
```

Mapping từ validation thật của `word_engine`: Stage rỗng → `no_people`;
chưa có diagram state → `no_diagram`; không tài sản → `no_assets`; >5 tài
sản → `too_many_assets`. Riêng `inheritance`: không chủ đất →
`no_landowner`; không chủ đất đã chết → `no_deceased_landowner`; không
người nhận → `no_receiver`; >20 người trên **Stage** → `too_many_people`
(`[Người N]` lấy theo Stage đã lưu, không phải node Diagram); >20 người
ký → `too_many_signers`. `two_party` **không** áp điều kiện chủ đất/người
nhận; >30 người trên Stage → `too_many_people` (placeholder `[Người
N]`/`[Bên A N]`/`[Bên B N]` phủ 30 slot); >30 người ký → lỗi render
per-file (§8.4), `block_reason` không liệt kê riêng.
Các code này là kiểm tra **kỹ thuật** xuất file — không phải kiểm định
pháp lý (§13.5).

Readiness theo **dữ liệu mẫu thực sự cần** (owner 15/10/2026): gate nhóm —
`no_landowner`, `no_deceased_landowner`, `no_receiver` (thừa kế) và
`no_diagram` của `two_party` — chỉ áp khi template **thực sự dùng token của
nhóm đó**; nhận diện theo đúng registry key engine sinh (nhóm `Chủ đất
sống`/`Chủ đất chết`/`Người nhận`, ghế `Bên A`/`Bên B`) sau chuẩn hoá không
dấu, không theo chuỗi con, nên token metadata/ủy quyền không kéo nhầm gate
Người nhận. Template không dùng nhóm thì bỏ qua gate, không áp blanket —
catalog legacy áp theo mẫu thật của từng `document_key`; folder mode giữ
semantics hiện hành (nhóm thiếu render rỗng, không gate nhóm), còn
`no_diagram` hai bên cũng theo mẫu. Gate kỹ thuật luôn áp: `no_people`,
`no_assets`, các giới hạn số lượng. Nhóm mà resolver hiện hành đã điền rỗng
vẫn để trống (không đổi mapping/resolver). Token không hỗ trợ/không xác minh,
slot chưa giải quyết (`word.unresolved_placeholders`) và thiếu người được ủy
quyền mà mẫu cần (`word.missing_authorized_person`, NAIA-12) vẫn làm riêng
file đó lỗi — không coi là field trống. Mẫu hiện diện nhưng không mở/parse
được: readiness trả đúng data-code per-file mà batch sẽ trả (`word.render_failed`,
`file_locked`, `file_not_found`) thay vì fallback gate cũ.

Catalog `document_key` v1 (registry mở — backend được thêm):

| `document_key` | `display_name` | Ghi chú |
|---|---|---|
| `khai_nhan_di_san` | Văn bản khai nhận di sản | map `document_type=khai_nhan` |
| `thoa_thuan_phan_chia` | Thỏa thuận phân chia di sản | map `document_type=thoa_thuan` |
| `niem_yet` | Thông báo niêm yết | chưa có template → `ready:false, block_reason:word.template_missing` là hợp lệ |

**Folder mode (NAIA-8):** khi `template_dir` có mặt (FileRef thư mục
hợp lệ — §3, chỉ path local), nguồn mẫu là **các file `.docx` ngay
trong thư mục đó**: bỏ file khóa `~$*`, bỏ non-DOCX và thư mục con,
sắp xếp ổn định theo tên. `document_key` = **basename gốc** của file,
`display_name` = stem (tên bỏ `.docx`). Catalog cố định chỉ dùng khi
`template_dir` absent. Thư mục trống → `documents:[]` hợp lệ.

### 8.2 `notary.word_export_batch` — payload

```yaml
payload:
  case_id: <int>
  document_keys: [<document_key>]   # 1..n, unique
  destination: <file_ref>           # PHẢI is_dir:true — §3
  template_dir: <file_ref>          # optional — PHẢI is_dir:true (NAIA-8)
  create_case_subdir: <bool>        # optional — default false (NAIA-8)
```

- `document_keys` rỗng → `word_no_documents_selected`; trùng →
  `word_duplicate_document_key`; key ngoài tập mẫu đã quét (catalog
  hoặc đúng `template_dir`) → `word_unknown_document_key`; key sai
  pattern → `word_unknown_document_key`. Folder mode chỉ chấp nhận
  basename `.docx` — key chứa separator/`..` là sai pattern; engine
  resolve file **chỉ trong thư mục đã cấp quyền**, không theo path
  tùy ý.
- `create_case_subdir:true` → ghi vào `<destination>/HS-<case_id>/`
  (tạo nếu thiếu); `data.destination` trong result vẫn là thư mục
  người dùng chọn.
- Validate **trước khi tạo file đầu tiên**: mọi lỗi trên + destination
  + `workspace_locked` → `failed`, không file nào được tạo. File mẫu
  biến mất sau khi quét → per-file `failed{code:word.template_missing}`
  (§8.4).

### 8.3 Naming và không-ghi-đè

```
<filename_stem>_HS-<case_id>[_{n}].docx      n ≥ 2
```

- `filename_stem`: catalog mode = chuỗi ASCII do **catalog backend**
  sở hữu cho mỗi `document_key` (không phải transform cơ học của
  `display_name`); folder mode = stem tên file rút về ASCII an toàn
  (`^[A-Za-z0-9_-]+$`, rỗng → `Mau`). Backend quyết
  `actual_filename`, UI chỉ hiển thị.
- Trùng tên với file **đã tồn tại** trong destination hoặc với tên đã
  dùng **trong cùng batch** (reservation nội batch) → tăng `n` từ 2.
- **KHÔNG BAO GIỜ ghi đè** file có sẵn. Không ZIP.
- `actual_filename`/`output_file.path` phải nằm trong `destination`;
  chứa `..`, dấu tách đường dẫn, hoặc drive khác → reject
  `word_path_traversal` (áp dụng cả chiều result — server emit sai =
  vi phạm contract).

### 8.4 Result + job semantics

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  destination: <file_ref is_dir:true>
  documents:
    - document_key: <key>
      display_name: <string>
      status: saved | failed | skipped
      actual_filename: <string | null>   # tên file thật khi saved
      output_file: <file_ref | null>     # path tuyệt đối file đã ghi
      error: {code, message} | null      # per-file — data-code (§2.5)
  breakdown:
    succeeded: [<document_key>]
    failed: [<document_key>]
    skipped: [<document_key>]            # file chưa bắt đầu khi cancel
```

- `breakdown` **luôn** có mặt cả ba list (kể cả khi `succeeded` toàn
  bộ — lúc đó `failed`/`skipped` rỗng) — đồng nhất với quy tắc
  `partial` của envelope.
- Job status: tất cả `saved` → `succeeded`; trộn → `partial`; tất cả
  `failed` → `failed{code:word_batch_failed,
  details.documents:[per-file errors]}`.
- Cancel: file đã lưu **giữ nguyên** (không xóa); file chưa bắt đầu →
  `status:skipped` và vào `breakdown.skipped`; job
  `canceled{code:user_canceled}`; file đang ghi dở được dọn theo chính
  sách engine (không để file nửa vời nếu tránh được).
- Per-file `error.code` là **data-code** `<ns>.<snake>` (§2.5): registry
  v1 gồm `word.template_missing`, `word.unresolved_placeholders` và mã
  envelope reuse (`file_locked`, `file_not_found`). Producer được thêm
  data-code mới.

## 9. Bảng error code

Namespace `notary.*` (snake_case không chấm):

| Code | Khi nào | `details` |
|---|---|---|
| `case_not_found` | `case_id` không tồn tại | — |
| `case_type_unsupported` | `case_type` engine chưa hỗ trợ trên command ghi/evaluate/export; word_export chấp nhận `inheritance` + `two_party` (NAIA-8) | `{case_type}` |
| `workspace_locked` | write trên case `locked` | — |
| `workspace_conflict` | `base_revision` khác revision server (cả nhỏ hơn lẫn lớn hơn) | `{server_revision}` |
| `workspace_owner_required` | `workspace_create` thiếu node `owner` đã gán person (rev 1.1) | — |
| `stage_validation_error` | field Stage vi phạm | `{field_errors:[{row_id,field,code,message}]}` |
| `intake_unsupported_source` | `kind` ngoài enum | `{source_id, kind}` |
| `intake_source_too_large` | file > 20MB / PDF > 50 trang | `{source_id, limit}` |
| `intake_too_many_sources` | sources > 8 | `{count, limit}` |
| `intake_text_too_long` | text > 100.000 ký tự | `{source_id, length, limit}` |
| `diagram_reference_outside_stage` | `personId` không thuộc Stage đã commit | `{personId}` |
| `diagram_invalid_state` | state sai cấu trúc/engine reject | `{errors:[{code,message,...}]}` |
| `word_no_documents_selected` | `document_keys` rỗng | — |
| `word_duplicate_document_key` | key lặp | `{document_key}` |
| `word_unknown_document_key` | key ngoài catalog/sai pattern | `{document_key}` |
| `word_template_missing` | văn bản chưa có template *(reserved — dạng per-file dùng data-code `word.template_missing`)* | `{document_key}` |
| `word_unresolved_placeholders` | DOCX còn placeholder chưa thay *(reserved — dạng per-file dùng data-code `word.unresolved_placeholders`)* | `{document_key, tokens[]}` |
| `word_batch_failed` | tất cả file trong batch lỗi | `{documents:[per-file]}` |
| `word_path_traversal` | output thoát khỏi destination | `{path}` |
| `validation_error` | vi phạm shape chung (§2.5) | `{detail}` |

Reuse nguyên từ envelope/g1: `file_scope_not_supported`,
`file_not_found`, `file_locked`, `payload_rejected_sensitive_key`,
`unsupported_contract_version`, `engine_not_installed`,
`engine_restarted`, `engine_unavailable`, `engine_version_mismatch`,
`user_canceled`, `job_already_terminal`, `engine_shutdown`.

## 10. Conformance checklist

Producer (sidecar/backend) PHẢI:

- [ ] Trả `result.kind` đúng tên command bỏ `notary.`; mọi
      `result.data` có `schema_version:"notary.case-drafting.v1"`.
- [ ] Normalize ngày về `YYYY-MM-DD`/`YYYY`/null trước khi emit; không
      emit `""` thay `null`; boolean strict.
- [ ] Không emit `confirmed` ở bất kỳ cấp nào của suggestion/intake.
- [ ] Commit Stage atomic: một dòng sai → Stage không đổi; lỗi gắn
      `row_id`+field; prune **và re-evaluate** Diagram trong cùng
      transaction; `revision+1`; `render_model` trả về khớp state mới.
- [ ] Reject `base_revision` khác server (`<` hoặc `>`) bằng
      `workspace_conflict` trên mọi command ghi; reject write trên case
      locked/unsupported — `diagram_evaluate` vẫn cho phép khi locked.
- [ ] Reject `personId` ngoài Stage đã commit
      (`diagram_reference_outside_stage`); chỉ emit `diagram_state`
      version 2.
- [ ] Enforce giới hạn intake §5.2; `partial` kèm breakdown source_id.
- [ ] Destination FileRef: `is_dir:true`, absolute, `machine_local`,
      không UNC, folder tồn tại — kiểm trước khi tạo file đầu tiên.
- [ ] Naming `*_HS-<case_id>[_n].docx`; reservation nội batch; không
      ghi đè; output nằm trong destination.
- [ ] `word_export_batch`: tất cả lỗi → `word_batch_failed`; cancel →
      file chưa bắt đầu `status:skipped` + vào `breakdown.skipped`,
      giữ file đã lưu; `breakdown` luôn đủ ba list.
- [ ] `workspace_create`: một transaction; owner bắt buộc (node `owner`
      có personId ∈ payload stage); đúng một `is_primary`; idempotent
      theo `idempotency_key` (`created:false` khi replay); result mang
      workspace shape §4 + `created`.
- [ ] `intake_analyze`/`diagram_evaluate`: chấp nhận `case_id` absent
      (nháp); reject `case_id:null` và `case_id` present-not-int ≥1
      bằng `validation_error`; evaluate nháp yêu cầu `stage` payload và
      trả `evaluated_revision:null`.
- [ ] Mock backend trả `backend_mode:"mock"` trong `workspace_get` và
      `workspace_create`.

Consumer (Electron main/renderer) PHẢI:

- [ ] `row_id`/`source_id` UUID v4 do client sinh; giữ ổn định qua
      commit/reload; gửi `base_revision` trên mọi write.
- [ ] Không tự tính tỷ lệ/quan hệ — `Xem cách tính` chỉ đọc
      `render_model`; không suy `Người từ chối` từ `Nhận`.
- [ ] Reject result chứa `confirmed`, `""`-as-null, output ngoài
      destination — coi như `validation_error`/`word_path_traversal`.
- [ ] Hiển thị `Chưa hỗ trợ` khi `case_type` ngoài cam kết hoặc
      capability tắt; phân biệt với engine `unsupported`.
- [ ] Hiển thị nhãn `Dữ liệu mô phỏng` khi `backend_mode:"mock"`.
- [ ] Draft chỉ sống trong phiên — không persist PII vào
      localStorage/log/diagnostics.

## 11. Examples & validator

- Examples: `contracts/notary-case-drafting/examples/{valid,invalid}/`.
- Validator: `contracts/notary-case-drafting/validate_examples.py`
  (stdlib-only). Gate: mọi `*.valid.json` pass hết rule; mọi
  `*.invalid.json` bị reject với `expected_error` khớp bảng §9.
- Fixture được phép mang `fixture_context` (object, top-level) mô tả
  trạng thái server giả định — vd `{"server_revision":7,
  "stage_row_ids":[...]}` — để validator kiểm rule ngữ cảnh
  (`workspace_conflict`, `diagram_reference_outside_stage` trên
  request). `fixture_context` **không** nằm trên wire.

## 12. Changelog

| Version | Ngày | Thay đổi |
|---|---|---|
| v1 (DRAFT) | 24/09/2026 | Publish draft đầu tiên (MIN-105): 7 command `notary.*` cho tab Soạn hồ sơ trên envelope `desktopcommand.v1`; mở rộng FileRef `is_dir`; chờ owner duyệt |
| v1 (DRAFT, fix r1) | 24/09/2026 | Review round 1: commit re-evaluate + `render_model` non-null; `breakdown.skipped`; conflict khi base_revision `<` hoặc `>`; evaluate được phép trên case locked; registry data-codes `<ns>.<snake>`; `word.no_deceased_landowner`/`word.too_many_signers`; schema nâng normative (if/then intake, status↔file link); `document_type`/`text` siết chặt |
| v1 (fix r2) | 24/09/2026 | Residuals round 2: `breakdown.skipped` vào schema; `workspace_conflict` `!=` server đồng bộ §9/§7.5; fraction integer form trong doc |
| v1 (APPROVED) | 24/09/2026 | Owner duyệt — contract trở thành SOT wire cho tab Soạn hồ sơ; mở cổng MIN-106+ |
| v1.1 | 26/09/2026 | MIN-121 (additive, tương thích ngược): `notary.workspace_create` + `idempotency_key`; chế độ nháp (`case_id` absent) cho `intake_analyze`/`diagram_evaluate` (evaluate nháp kèm `stage` payload, `evaluated_revision:null`); `case` +`ngay_lap_ho_so`/`noi_niem_yet`/`ghi_chu`; field_error +`duplicate_entity`; error +`workspace_owner_required` |
| v2 MIN-141 | 03/10/2026 | Owner xác nhận hành vi cuối 14 commit worker và yêu cầu gộp vào nhánh chính; thay các quy tắc MIN-140 mâu thuẫn, đồng bộ dữ liệu Người/cụm đất/Hồ sơ. Xem §13.16 |
| v2 (APPROVED) | 27/09/2026 | Owner duyệt §13 (MIN-125, toàn bộ Q1–Q12): `schema_version` bump `notary.case-drafting.v2`; Stage draft/committed + create nguyên khối; `owner_row_id`; asset theo vị trí 1..3, bỏ `is_primary`; `ownPositions`/`receivePositions`; domain `two_party` 30 slot `p1..p30`; `case_type` immutable; error codes §13.9. Implement ở P5 (MIN-128). C1–C4 xử lý theo §13.13 |
| v2 + conversion (owner) | 16/10/2026 | Owner duyệt chuyển loại hồ sơ **đã lưu** (#3): ngoại lệ `case_type`/`document_type` immutable (§6.1, §13.5) — giữ Người/Tài sản Stage, reset Diagram, buộc chọn `document_type` mới kèm xác nhận, `owner_row_id` theo loại đích; §13.18. [Decision](../_bmad-output/decisions/decision-owner-saved-case-type-conversion-20261016.md) |
| v2 + branch removal (#21B) | 17/10/2026 | **BUILT — retained Quick CODE t3 No actionable findings; parent accepted AC1–4**. Owner “B - gỡ cả nhánh” semantics §7.1/§13.4 unchanged; no new wire/API/store. Node full 198 before test-only wording-assert deletion, affected file 25 after; service 106 (24 existing warnings), Source Electron real IPC/isolated SQLite proof. Not packaged/Word acceptance. |
| additive NAIA-9 | 04/10/2026 | Thêm command thứ mười `notary.address_lookup` (§14): tra cứu đơn vị hành chính đích theo địa chỉ nguồn + `source_date`/`target_date` đầy đủ; read-only, local-only trên ledger Bando đóng gói; `result.data.schema_version` = `notary.address-lookup.v1` — ngoại lệ rule §1 |
| address-lookup v2 (APPROVED, triển khai TASK-3) | 05/10/2026 | TASK-2, Owner duyệt 05/10: thay v1 bằng `notary.address-lookup.v2` (§14) — payload `query`+`presentation`, bỏ ngày/tách xã-tỉnh/`coverage`/`partial`; result `found\|not_found\|too_many\|invalid_input\|reload_failed`. **Breaking**; runtime và schema v1 đã chuyển/xóa tại TASK-3. |

---

# PHẦN II — `notary.case-drafting.v2` (MIN-125, APPROVED 27/09/2026)

> **TRẠNG THÁI: APPROVED — owner duyệt toàn bộ đề xuất Q1–Q12 ngày
> 27/09/2026.** §13 là wire contract v2; runtime implement ở
> **P5 (MIN-128)**. Phần I (`v1`, §1–§12) vẫn hiệu lực cho consumer v1;
> backend emit `v2` thống nhất theo §13.1.
>
> Các câu hỏi C1–C4 (§13.13) vẫn mở — xử lý theo ghi chú từng mục,
> không chặn implement phần đã duyệt.
>
> **Bổ sung 16/10/2026 (owner):** hồ sơ **đã lưu** được chuyển loại
> (`inheritance` ↔ `two_party`) — ngoại lệ `case_type`/`document_type`
> immutable, xem §13.18.
>
> Mọi mục dưới đây gắn mã `Q#` ↔ bảng quyết định tại
> `_bmad-output/archive/linear-tasks/MIN-125/decisions.md` (đề xuất + phương án thay thế).
> Fixtures v2 nằm ở `examples/draft-v2/` với
> `fixture_context.draft_v2:true` — validator hiểu flag này (§13.15).

## 13. `notary.case-drafting.v2`

### 13.1 Vì sao bump version thay vì rev additive

Rev 1.1 additive được vì chỉ thêm field nullable / command mới. §13
**đổi nghĩa** các phần đã publish: bỏ `asset_row.is_primary`, thay
`node.isLandOwner`/`willReceive` bằng dấu chọn theo vị trí, thêm
`stage.owner_row_id`, thêm `domain` bắt buộc trong `diagram_state`, thêm
`case_type` thứ hai. Consumer v1 đọc payload v2 sẽ hiểu sai → bắt buộc
`schema_version` mới: `notary.case-drafting.v2`. Envelope vẫn
`desktopcommand.v1`, giữ đúng 8 command `notary.*` — chỉ đổi shape
`payload`/`result.data` và ngữ nghĩa vòng đời. Shell desktop ship
sidecar + renderer trong cùng bản → không cần negotiate version trên
wire; backend P5 emit `v2` thống nhất.

| Điểm | v1 (APPROVED) | v2 (§13, APPROVED) |
|---|---|---|
| `schema_version` | `notary.case-drafting.v1` | `notary.case-drafting.v2` |
| `diagram_state.version` | `2` | `3` (+ `domain` bắt buộc) |
| `case.case_type` | cam kết `inheritance` | `inheritance` \| `two_party` |
| `asset_row.is_primary` | bắt buộc, đúng 1 `true` | **bỏ** — primary = vị trí 1 |
| `stage.owner_row_id` | không có | bắt buộc với `inheritance`, cấm với `two_party` |
| node cờ thừa kế | `isLandOwner`, `willReceive` bool | `ownPositions`, `receivePositions` ⊆ {1,2,3} |
| `diagram` trong `workspace_create` | bắt buộc, phải có owner node | **optional** — server tự seed |
| Pool của hồ sơ mới | đòi owner/primary trước khi gán | `Cập nhật` đầu = `workspace_create` (Q1) |

### 13.2 Vòng đời Stage: draft / committed / Cập nhật / bỏ nháp khi mở hồ sơ khác

Contract chỉ định nghĩa trạng thái **committed** (server persist, trả
qua `workspace_get`/result của write) và payload `stage` trên wire. Phần
này chốt nghĩa vụ hai phía về **vòng đời** — buffer draft là khái niệm
client nhưng contract phải nói rõ khi nào server thấy thay đổi.

```text
stage draft buffer (client, không wire)          committed stage (server)
        │  Cập nhật ──► workspace_commit_stage ──►│  (hoặc workspace_create
        │            payload.stage = snapshot      │   với hồ sơ mới — Q1)
        │                                          │
        │  bỏ nháp khi mở hồ sơ khác / khi đóng ◄──┤
        ◄── (client-only, KHÔNG ghi) buffer := ────┘
            committed của hồ sơ được mở
```

- **`stage draft buffer`** — bản đang sửa trong phiên (thêm/xóa/sửa
  row, reorder tài sản). Server **không** biết buffer này.
- **`stage committed`** — snapshot sau lần `workspace_commit_stage` /
  `workspace_create` thành công gần nhất; `workspace_get` trả đúng bản
  này. Mọi `personId` trên diagram chỉ được trỏ row của stage committed
  (hoặc `stage` trong cùng payload ở chế độ nháp — §2.1a).
- **Cập nhật (Update) nguyên khối** — semantics §6.1 giữ nguyên: một
  transaction, `base_revision` chống conflict, prune + re-evaluate trong
  cùng transaction, `revision+1`.
- **Xóa row trong draft KHÔNG prune diagram ngay** (sửa hành vi hiện
  trạng `removeStageRow` — `case-drafting-model.js`): xóa dòng Người
  hay Tài sản trong buffer chỉ đánh dấu pending; `personId`/dấu chọn
  `ownPositions`/`receivePositions` trên diagram buffer giữ nguyên cho
  tới khi `Cập nhật` thành công — lúc đó server prune theo §6.1 và trả
  `diagram.state` đã prune. UI được đánh dấu "sẽ gỡ khi Cập nhật" trên
  node (quyết định hiển thị của P6, không phải field wire).
- **Bỏ nháp khi mở hồ sơ khác / khi đóng** — *client-only, không
  command GHI*: buffer chưa commit **không** được ghi (không write nào
  lên wire; điều hướng/đọc vẫn dùng `workspace_get` bình thường);
  mở lại hồ sơ thì đọc đúng bản committed — `row_id`, thứ tự asset,
  `personId`, positions đúng như bản committed; `revision` không đổi.
  Nút `Hủy thay đổi` của Stage đã bỏ cùng cơ chế khôi phục riêng
  (b541); dirty, cảnh báo rời/đóng và nhánh bỏ nháp giữ nguyên.
  Ví dụ "xóa asset rồi bỏ nháp" ở §13.12.2.
- **Pool** = `stage.people` **committed** trừ những `personId` đang gán
  trên diagram committed (giữ nguyên nghĩa §7/SOT). Pool **không** đọc
  draft buffer — tránh bug `caseId=null` hiện trạng (model đọc buffer
  chưa commit làm Pool). Hồ sơ mới (chưa từng commit) ⇒ committed stage
  rỗng ⇒ **Pool rỗng** → người dùng phải `Cập nhật` trước khi gán sơ
  đồ, đúng yêu cầu MIN-125.
- **Chu trình hồ sơ mới (Q1):** mở nháp → nhập Người/Tài sản + đánh dấu
  `owner_row_id` → `Cập nhật` = **`workspace_create`** (một transaction,
  case persist, `revision=1`) → Pool lấy từ stage vừa committed → gán sơ
  đồ → `diagram_save` (mang `base_revision` như thường). Như vậy vòng
  phụ thuộc "tạo hồ sơ đòi owner trên diagram trước khi có Pool" bị phá:
  owner trở thành **con trỏ trong stage** (§13.6), không còn là điều
  kiện của việc được gán diagram.
- `diagram_evaluate` chế độ nháp (`case_id` absent) giữ semantics v1 —
  evaluate trên `stage` payload (snapshot buffer tại thời điểm gửi).
  Trong v2 payload stage của evaluate nháp là `stage_v2` (§13.3, kể cả
  `owner_row_id` với inheritance).

### 13.3 Tài sản: tối đa 3, vị trí = thứ tự mảng (Q3, Q4)

```yaml
asset_row_v2:               # giống §4.2, TRỪ is_primary (bị loại)
  row_id: <uuid4>           # ổn định — KHÔNG phải vị trí
  entity_id: <int | null>
  so_serial: <string>   # nguyên văn tùy nguồn — entities.md §2
  ...                       # mọi field còn lại giữ nguyên §4.2; `thoi_han`
                            # lẻ OPTIONAL ở input (key vắng = giữ lịch sử
                            # master) — quy tắc tách input/emit ở §4.2
  land_rows:                # giữ nguyên shape v1 — hàng cấu trúc
    - loai_dat: <string | null>   #   (mục đích sử dụng)
      dien_tich: <number | null>  #   diện tích
      thoi_han: <string | null>   #   thời hạn
      # key canonical loaidat/dientich/thoihan đọc được — §4.2 (MIN-141 đợt 2)
```

- **Vị trí = index + 1.** `stage.assets[i]` là "tài sản ở vị trí
  `i+1`"; không có field `position`, không hệ đánh số thứ hai. Vị trí 1
  là primary theo nghĩa engine (`tai_san_id` của case — §13.6).
- **`is_primary` bị loại khỏi wire v2** — producer không emit; consumer
  thấy key này → `validation_error` (trường lạ, cùng rule strip-field
  hiện trạng). `primary_count` không còn áp dụng ở v2.
- **Tối đa 3 asset** trong `stage.assets` của payload
  `workspace_create`/`workspace_commit_stage`/`diagram_evaluate` nháp;
  phần tử thứ 4 trở lên → `stage_validation_error` với
  `field_errors[].code:"asset_limit"` (gắn `row_id` của dòng thừa).
- **Reorder đổi nghĩa vị trí, không đổi identity:** kéo asset từ vị trí
  1 xuống 2 nghĩa là *dữ liệu tại vị trí 1 đổi*; `row_id` của asset đi
  theo dòng. Dấu chọn `ownPositions`/`receivePositions` (§13.4) **không
  tự chuyển theo `row_id`** — số vị trí giữ nguyên, nghĩa là "người đó
  vẫn sở hữu/nhận *tài sản đang ở vị trí đó*". Đây là hành vi có chủ
  đích của MIN-125 — xem ví dụ §13.12.1.
- **Xóa asset:** xóa ở draft = pending (§13.2). Tại commit thành công,
  vị trí đánh lại dày (dense): asset đứng sau dịch lên; mọi dấu chọn
  giữ nguyên số vị trí (không bám `row_id` cũ); dấu chọn tới vị trí
  `> len(assets)` mới bị server prune trong cùng transaction. UI PHẢI
  cảnh báo khi xóa asset làm trôi nghĩa vị trí (ghi chú cho P6 —
  không phải field wire).
- **Hồ sơ cũ >3 asset:** `workspace_get` được emit đủ (không cắt dữ
  liệu) kèm `result.data.warnings[]` data-code
  `stage.legacy_asset_overflow`; `workspace_commit_stage` từ chối tới
  khi người dùng giảm còn ≤3 (`asset_limit`). §13.8.
- **Cụm đất tối đa 20/tài sản** (entities.md §9.2): phần tử
  `land_rows[20]` trở đi → `stage_validation_error` với
  `field_errors[].code:"land_row_limit"`. Persist là bảng con
  `property_land_rows(property_id, vitri)` UNIQUE; commit ghi master +
  cụm đất + `case_state_json` snapshot + revision trong **một**
  transaction — rollback lỗi bất kỳ không để lại nửa ghi.
- **Snapshot asset trong `case_state_json` (MIN-141 đợt 2):** mỗi phần
  tử `assets[]` đã commit mang đủ field §4.2 + `land_rows` key canonical
  + `loai_dat`/`dien_tich` tổng hợp. Word export đọc snapshot này → mỗi
  hồ sơ xuất đúng bản đã commit, không đổi theo master `properties` khi
  hai hồ sơ dùng chung tài sản. `properties.land_rows_json` giữ mirror
  tương thích; data cũ được migrate-on-startup, JSON lỗi không bị ghi
  đè.
- **Thời hạn thuộc từng cụm** (MIN-141 đợt 2): xuất Word không tự lấy
  `properties.thoi_han` lẻ đắp vào cụm. Dữ liệu cũ chỉ có thời hạn lẻ
  không xác định được cụm tương ứng → `workspace_get` emit
  `result.data.warnings[]` code `stage.orphan_thoi_han`, giữ nguyên bản
  gốc, không tự đoán; `land_rows_json` lỗi/không parse được →
  `stage.legacy_land_rows_invalid`; JSON >20 cụm →
  `stage.legacy_land_rows_overflow`.
- **`result.data.warnings`** (optional, array `{code, message}`) là mở
  rộng v2 cho cảnh báo cấp-stage (không thuộc `diagram.warnings`).

### 13.4 Node v3 — dấu chọn tài sản độc lập (Q4, Q5, Q10)

```yaml
diagram_state v3 (domain inheritance):
  version: 3                        # literal — khác → diagram_invalid_state
  domain: "inheritance"             # BẮT BUỘC trong state (§13.5)
  nodes:
    - id: <string non-empty>        # slot id — giữ namespace v1
      personId: <uuid4 | null>      # row_id dòng Người stage committed
      parentSlotIds: [<node.id>]    # giữ nguyên 0..2
      spouseSlotId: <node.id | null>
      ownPositions: [<int 1..3>]    # vị trí tài sản người này SỞ HỮU
      receivePositions: [<int 1..3>]# vị trí tài sản người này ĐƯỢC NHẬN
      hidden: <bool>
      deleted: <bool>
```

- `isLandOwner`/`willReceive` **cấm** trên wire v2 →
  `diagram_invalid_state` (`invalid_node` — trường lạ trên node).
- `ownPositions`/`receivePositions`: array không trùng phần tử ⊆
  {1,2,3}; phần tử ngoài khoảng / trùng / không phải int →
  `diagram_invalid_state{errors:[{code:"invalid_position"}]}`.
  `null`/thiếu → `diagram_invalid_state` (`invalid_node`).
- Hai mảng **độc lập**: một người vừa sở hữu vừa nhận, vừa chọn nhiều
  vị trí, đều hợp lệ. **Nhiều node cùng chọn một vị trí** = đồng sở
  hữu / nhận chung — hợp lệ (Q10).
- Dấu chọn tới vị trí `> len(stage.assets)` hiện tại (asset chưa tạo
  hoặc vừa bị prune): cho phép tồn tại trong draft buffer; server prune
  tại commit/save (cùng cơ chế prune `personId` §6.1) — ghi vào commit
  result qua `diagram.warnings` data-code `diagram.selection_pruned`;
  UI được disable chip tài sản chưa tồn tại (quyết định hiển thị của
  P6). Không reject cả commit.
- **Mặc định khi gán (Q5):** node `owner` → `ownPositions` mặc định =
  tất cả vị trí đang có ({1..len(assets)}); person gán vào slot thừa
  kế → `receivePositions` mặc định = tất cả vị trí đang có. Đây là
  tiện ích **client-side** — wire luôn mang mảng explicit; thêm asset
  sau đó **không** tự mở rộng mảng đã chọn.
- **Slot `owner` (mirror):** node `id:"owner"` tồn tại như v1 nhưng
  `personId` của nó do server căn theo `stage.owner_row_id` (§13.6).
  `diagram_save` gửi `owner.personId` khác `owner_row_id` →
  `failed{code:diagram_owner_mismatch}` — không tự sửa lặng.
- **Engine Python giữ nguyên** (A4): backend project xuống boolean khi
  gọi engine — `isLandOwner := ownPositions ≠ []`,
  `willReceive := receivePositions ≠ []`. `missing_land_owner`,
  `word.no_landowner`, `word.no_receiver` theo projection đó. *Giới hạn
  đã biết:* engine coi di sản là một khối — ownership theo từng vị trí
  được lưu cho văn bản/Word (tương lai) nhưng **chưa** ảnh hưởng công
  thức chia; cần task engine riêng nếu muốn tính theo từng tài sản.
- Quan hệ (`parentSlotIds`, `spouseSlotId`), `duplicate_person` (1
  người / 1 node active — A3), `hidden`/`deleted`, auto-seed slot theo
  `requiredSlots` — **giữ nguyên** semantics §7.1.
- **Gỡ cả nhánh Thừa kế (owner 17/10/2026, “B - gỡ cả nhánh”):**
  xóa node gỡ node đó và mọi hậu duệ active theo cạnh cha/mẹ → con,
  kể cả slot trống/ẩn hoặc con còn parent khác. Không mở rộng tập theo
  spouse, không tự reparent hoặc giữ ô trung gian rỗng. Trước mutation
  phải liệt kê node/quan hệ thực tế bị tác động và cảnh báo phần hưởng.
  Hủy/Escape/đóng không mutate draft/dirty/revision hay phát evaluate/save
  do thao tác này; xác nhận một mutation draft rồi evaluate hiện có,
  không autosave. Graph thay đổi thì không áp cảnh báo cũ âm thầm.
  Giữ Node v3 canonical với `deleted:true`, ID/`personId`/Chủ/Nhận;
  xóa toàn bộ quan hệ đi ra từ tập bị gỡ và mọi tham chiếu đi vào tập
  này trên tất cả node, kể cả tombstone cũ, để không sinh spouse lệch
  hai chiều/parent sai. Stage Người/Tài sản, thứ tự/vị trí/giá trị và
  graph/dấu không bị tác động giữ nguyên. Save/revision/atomic/errors
  dùng đường hiện có; mở lại giữ đúng canonical, không store/API mới.
  Quy tắc đầy đủ: `_bmad-output/specs/notary_v2/diagram-rules.md` §9.9;
  quyết định: `decision-owner-inheritance-remove-entire-branch-20261017.md`.

### 13.5 Domain `two_party` — sơ đồ hai bên 30 vị trí (Q7, Q8)

```yaml
diagram_state v3 (domain two_party):
  version: 3
  domain: "two_party"
  nodes:                            # ĐÚNG 30 phần tử, id cố định
    - id: "p1".."p30"               # p1..p15 = bên A; p16..p30 = bên B
      personId: <uuid4 | null>      # null = vị trí trống
      hidden: <bool>
      deleted: <bool>
```

- `case.case_type` nhận thêm `"two_party"` (Q8); `document_type` enum
  `{chuyen_nhuong, tang_cho, cho_thue, dat_coc}` — **đã chốt** (Q11,
  owner duyệt 27/09/2026; NV2 xác nhận khi implement).
- **30 vị trí cố định, canonical:** state luôn đủ 30 node theo đúng thứ
  tự `p1..p30`; thiếu node → `diagram_invalid_state` (`missing_position`);
  `id` ngoài tập hoặc sai thứ tự → `invalid_position`. Bên = suy ra từ
  số (`≤15` → A, `≥16` → B) — **không** field `side`, không hệ đánh số
  thứ hai.
- **Ô trống giữ nguyên:** `personId:null` = chỗ trống; xóa người khỏi
  `p16` làm `p16` trống, `p17..p30` **không dồn**. Thứ tự nhập row
  trong `stage.people` độc lập với thứ tự vị trí (cùng một `row_id`
  được gán vào bất kỳ ô nào).
- Cấm trường quan hệ/`ownPositions`/`receivePositions` trên node
  two_party → `invalid_node`. `duplicate_person` áp dụng y như domain
  inheritance (đề xuất giữ A3 — 1 người chỉ ngồi 1 ô).
- **Stage:** `stage.people` ≤ 30 cho `case_type:two_party` → quá →
  `stage_validation_error{code:"people_limit"}`; `owner_row_id` **cấm**
  (absent — `validation_error` nếu có); assets ≤3 giữ nguyên.
- **Không engine:** `diagram_evaluate` trên `two_party` trả `succeeded`
  với `render_model{engineVersion:2, status:"unsupported",
  allocations:{}, breakdowns:[], requiredSlots:[],
  unresolvedEstates:[], conservation:{allocated:"0",unresolved:"0",
  total:"0"}, warnings:[{code:"diagram.two_party_unsupported",...}]}` —
  sơ đồ hai bên **không bao giờ** đi vào engine thừa kế (rào kiến
  trúc: `InheritanceCase` hiện chỉ chở inheritance; persist hai bên cần
  backend riêng ở P5).
- `diagram_save`/`workspace_commit_stage` persist + structural validate
  như thường (theo shape two_party). `workspace_get` trả domain
  `two_party`, `capabilities:{intake:[…], diagram:true,
  word_export:true}` (NAIA-8: Word engine đã hỗ trợ context hai bên —
  §13.10); `word_export_*` trên `two_party` chạy bình thường, readiness
  riêng qua `block_reason` (§8.1) — **không** còn
  `case_type_unsupported`. `word_export:false` chỉ còn cho case_type
  engine chưa hỗ trợ (ngoài `inheritance`/`two_party`).
- **Drop lên ô đã có người (Q9):** hoán đổi `personId` hai ô — áp dụng
  cho cả hai domain (thống nhất với hành vi kéo-thả hiện trạng). Đây
  là semantics client; wire chỉ thấy state sau hoán đổi.
- `case_type` **immutable** sau khi tạo; đổi loại ở draft chưa tạo =
  client reset diagram buffer theo domain mới (rule client, Q8).
- **Ngoại lệ (owner 16/10/2026):** hồ sơ **đã lưu** chuyển loại qua
  đường chuyển loại đã duyệt — §13.18; ngoài đường đó `case_type`/
  `document_type` vẫn bất biến (§6.1).

### 13.6 `workspace_create` v2 — owner trong Stage, diagram optional (Q1)

```yaml
payload:
  idempotency_key: <uuid4>          # giữ nguyên §2.1
  case:
    case_type: inheritance | two_party   # optional — default "inheritance"
    document_type: <enum theo case_type> # inheritance: khai_nhan|thoa_thuan
                                         # two_party: §13.5 (Q11)
    ngay_lap_ho_so, noi_niem_yet, ghi_chu  # giữ nguyên
  stage:                            # stage_v2
    owner_row_id: <uuid4>           # BẮT BUỘC khi inheritance; phải là
                                    # row_id có trong stage.people;
                                    # CẤM khi two_party
    people: [<person_row>]          # ≥1 (giữ nguyên)
    assets: [<asset_row_v2>]        # ≥1, ≤3 — §13.3
  diagram:                          # OPTIONAL (đổi từ v1 bắt buộc)
    state: <diagram_state v3>       # domain phải khớp case.case_type
```

- **`stage.owner_row_id`** là chỉ định "người để lại / bên chủ" ở cấp
  Stage — phá vòng phụ thuộc: tạo hồ sơ không còn cần diagram. Server
  suy `nguoi_chet_id` = entity của row đó; `tai_san_id` = entity của
  `assets[0]` (vị trí 1) → **không cần sửa schema DB** (hai cột vẫn
  NOT NULL, giá trị có sẵn).
- `owner_row_id` thiếu/null/không thuộc `stage.people` →
  `workspace_owner_required` (cùng nghĩa v1). `owner_row_id` mutable
  qua commit: đổi giá trị = đổi người để lại → server sync node
  `owner` (`personId := owner_row_id`) trong cùng transaction §6.1 và
  cập nhật `nguoi_chet_id`.
- `diagram` present: `state.domain` phải khớp `case.case_type` → sai →
  `diagram_domain_mismatch`; với inheritance, node `owner` (nếu có
  `personId`) phải bằng `owner_row_id` → sai → `diagram_owner_mismatch`.
- `diagram` absent: server seed state mặc định — inheritance: node
  `owner` gán `owner_row_id` + bộ slot rỗng chuẩn như hiện trạng;
  two_party: 30 ô trống. `render_model` của create-result = null khi
  chưa evaluate được (giữ §4.3).
- `owner_row_id` trong `stage` result của `workspace_get` /
  `workspace_commit_stage` / `workspace_create`: emit luôn với
  inheritance (`null` cho hồ sơ legacy chưa có owner — commit kế tiếp
  sẽ bắt buộc chọn); absent với `two_party`.

### 13.7 Bảng chuyển trường v1 → v2

| v1 | v2 (draft) | Quy tắc chuyển |
|---|---|---|
| `schema_version:"notary.case-drafting.v1"` | `"notary.case-drafting.v2"` | emit cứng theo version |
| `diagram_state.version:2` | `3` | literal mới; state v2 trên wire v2 → `diagram_invalid_state` |
| — (không có `state.domain`) | `state.domain` bắt buộc | `"inheritance"` cho hồ sơ cũ |
| `node.isLandOwner:bool` | `node.ownPositions:int[]` | `true`→`[1..min(3,len(assets))]`; `false`→`[]` (Q6) |
| `node.willReceive:bool` | `node.receivePositions:int[]` | `true`→`[1..min(3,len(assets))]`; `false`→`[]` (Q6) |
| `asset.is_primary:bool` | — (bỏ) | asset `is_primary:true` → đứng vị trí 1; reorder mảng khi đọc hồ sơ cũ |
| `stage` = `{people,assets}` | `{owner_row_id,people,assets}` | `owner_row_id := personId` của node `owner` persist; không có → `null` |
| `payload.case` (create): meta-only | + `case_type` optional | default `"inheritance"` |
| — | + `payload.case` (commit) optional | đợt 3: meta cùng Stage 1 transaction |
| `case` emit: ngay_lap_ho_so/noi_niem_yet/ghi_chu | + `nguoi_nhan_uy_quyen(_id)`, `noi_dung_viec` | đợt 3 (canonical ↔ snake đọc được) |
| `person_row` 10 key | + `loai_giay_to`, `loai_dia_chi` | đợt 3: bằng chứng xác nhận/suy theo mốc |
| `diagram` (create): required | optional | server seed (§13.6) |
| error: — | + `diagram_domain_mismatch`, `diagram_owner_mismatch` | §13.9 |
| field_error: `primary_count` | thay bằng `asset_limit` / `people_limit` | `primary_count` không còn ở v2 |
| engine codes: §7.3 | + `invalid_position`, `missing_position` | dùng trong `details.errors[]`/`render_model.errors[]` |
| data-codes | + `stage.legacy_asset_overflow`, `stage.legacy_primary_ambiguous`, `diagram.two_party_unsupported`, `diagram.selection_pruned` | §13.3/13.4/13.5/13.8 |
| `person_row`, `personId`, `row_id`, revision, `idempotency_key` | giữ nguyên | — |

### 13.8 Tương thích hồ sơ cũ (persisted → v2)

| Tình trạng persisted | Hành vi đọc v2 (đề xuất) |
|---|---|
| `case_state_json` schemaVersion 1/2 | migrate-on-read hiện trạng → tiếp tục nâng shape: node flags → mảng positions (Q6); emit `domain:"inheritance"` |
| người không `row_id` | gán uuid4 khi migrate — giữ nguyên rule hiện trạng |
| nhiều node `isLandOwner:true` | nhiều node `ownPositions` non-empty — bảo toàn (đa chủ sở hữu hợp lệ ở v2) |
| không node `owner` / owner `personId:null` | `stage.owner_row_id:null` trong result; commit kế phải chọn (=`workspace_owner_required` nếu bỏ sót) |
| >3 asset | emit đủ + `warnings:[stage.legacy_asset_overflow]`; commit từ chối >3 (`asset_limit`) tới khi người dùng giảm — không tự cắt |
| `is_primary` bất thường (0 hoặc ≥2 `true`) | reorder ưu tiên dòng `is_primary:true` đầu tiên lên vị trí 1; còn lại giữ thứ tự; thêm warning `stage.legacy_primary_ambiguous` |
| `co_nhan_tai_san`/participant cũ | projection `willReceive` của engine giữ nguyên; không suy ngược thành positions ngoài rule Q6 |
| hồ sơ `two_party` | không tồn tại dữ liệu cũ — domain mới hoàn toàn |

### 13.9 Error codes mới

Job-level (namespace `notary.*`):

| Code | Khi nào | `details` |
|---|---|---|
| `diagram_domain_mismatch` | `state.domain` khác `case.case_type` (create/save/evaluate) | `{expected, got}` |
| `diagram_owner_mismatch` | `owner` node `personId` ≠ `stage.owner_row_id` (create/save) | `{owner_row_id, node_personId}` |

Field-error code mới trong `stage_validation_error.details.field_errors[]`:

| Code | Nghĩa |
|---|---|
| `asset_limit` | `stage.assets` > 3 (v2) |
| `people_limit` | `stage.people` > 30 với `case_type:two_party` |

Engine/detail codes mới (`details.errors[]`, `render_model.errors[]`):
`invalid_position` (phần tử ngoài {1..3} / `id` ngoài `p1..p30` / sai
thứ tự), `missing_position` (state two_party thiếu slot canonical).
Data-codes mới: `stage.legacy_asset_overflow`,
`stage.legacy_primary_ambiguous`, `diagram.two_party_unsupported`,
`diagram.selection_pruned`.

`primary_count` (v1) không dùng trong v2 — asset không `is_primary`.

### 13.10 Ranh giới Word — giới hạn + mapping theo Stage (NAIA-8)

- Giới hạn giữ nguyên: `MAX_WORD_ASSETS = 5`; `person`/`signer` > 20 →
  `word.too_many_people`/`word.too_many_signers`; `[Tài sản N - field]`
  đọc tài sản theo **thứ tự** 1..5.
- **`[Người N]` = thứ tự danh sách Stage** (NAIA-8 — quyết định Leader
  trên NAIA-8): gồm cả người chưa có node; đảo thứ tự/xóa node Diagram
  **không** đổi số Người. Vai trò (Bên A/B, chủ đất, người nhận) lấy từ
  dữ liệu nghiệp vụ đã lưu, không suy từ vị trí node. Mọi alias
  placeholder cũ (`ngườ`, `ngườ ký`, `ngườ nhận`, …) giữ nguyên.
- Vì v2 chặn `stage.assets` ≤ 3 (inheritance), dữ liệu v2 luôn nằm
  trong giới hạn 5 của Word; vị trí 1..3 trên Stage tương ứng
  `[Tài sản 1..3 - *]` — **không đổi nghĩa placeholder**.
- `two_party` (NAIA-8 — đã hỗ trợ): `word_export:true`,
  `word_export_*` chạy bình thường. `[Người N - *]` = toàn bộ dòng
  Stage theo thứ tự; `[Bên A N - *]`/`[Bên B N - *]` = người gán vào
  slot `p1..p15`/`p16..p30` (ô trống → render rỗng, không dồn);
  `[Bên A - Họ tên]`/`[Bên B - Họ tên]`/`[Tên bên A]`/`[Tên bên B]`
  = danh sách họ tên từng bên; placeholder riêng thừa kế (chủ đất,
  người nhận, phụ lục di sản) render rỗng trên văn bản hai bên.
- Không đưa `two_party` vào engine thừa kế (§13.5 — `diagram_evaluate`
  vẫn `unsupported`, không chạy allocation).

### 13.11 Revision / retry / late-response — giữ nguyên, nêu lại cho rõ

- Mọi write mang `base_revision`; lệch (cả `<` lẫn `>`) →
  `workspace_conflict{details:{server_revision}}`; không ép ghi — client
  reload hoặc giữ draft (`_bmad-output/specs/ui/README.md`). Commit retry sau conflict phải
  gửi `base_revision` mới.
- `workspace_create`: retry dùng **cùng** `idempotency_key` →
  `created:false`, trả case đã persist — không hồi sinh bản nháp đã
  bỏ. Timeout giữa chừng không phân biệt được "đã commit chưa" → luôn
  retry bằng key cũ.
- `diagram_save`/`workspace_commit_stage` retry an toàn: gửi lại
  request nguyên vẹn; nếu request đầu đã commit → `base_revision` cũ
  sẽ `<` server → `workspace_conflict` (idempotent qua revision).
- Late response: client tương quan `job_id`/`command_id` + `case_id` của
  phiên hiện tại; result/job trễ từ phiên trước / case đã đổi / draft
  đã bỏ nháp PHẢI bị discard — không apply vào buffer (`_bmad-output/specs/ui/README.md`, giữ
  nguyên).

### 13.12 Ví dụ trước/sau (JSON rút gọn)

#### 13.12.1 Reorder tài sản — dấu chọn giữ theo vị trí (Q4)

```jsonc
// TRƯỚC (stage committed)
"assets": [
  {"row_id": "aaaa-…-1", "so_serial": "DD100001"},   // vị trí 1
  {"row_id": "bbbb-…-2", "so_serial": "EE200002"},   // vị trí 2
  {"row_id": "cccc-…-3", "so_serial": "FF300003"}    // vị trí 3
]
// node: {"id":"owner","personId":"…p1","ownPositions":[1,2],"receivePositions":[]}

// SAU khi user kéo aaaa xuống cuối + Cập nhật thành công
"assets": [
  {"row_id": "bbbb-…-2", "so_serial": "EE200002"},   // vị trí 1 (primary mới)
  {"row_id": "cccc-…-3", "so_serial": "FF300003"},   // vị trí 2
  {"row_id": "aaaa-…-1", "so_serial": "DD100001"}    // vị trí 3
]
// node owner vẫn "ownPositions":[1,2] → nghĩa mới: sở hữu EE200002 + FF300003.
// row_id aaaa KHÔNG được "kéo dấu" theo — không remap số sang ID cũ.
```

#### 13.12.2 Xóa asset rồi bỏ nháp — buffer vs committed (Q2, §13.2)

```jsonc
// committed: assets [A1,B2,C3]; node X.receivePositions=[2]
// draft: user xóa B2  → buffer assets [A1,C3]; node X GIỮ [2] trong
//        buffer (chưa prune ngay — khác hiện trạng)
// bỏ nháp (mở hồ sơ khác / đóng, KHÔNG command ghi): buffer := committed →
//        assets [A1,B2,C3], node X [2] — như chưa xóa.
//        revision không đổi, không write nào lên wire (đọc vẫn workspace_get).
// (Nếu Cập nhật thay vì bỏ nháp: server persist [A1,C3] → vị trí dồn:
//  C3 = 2; X.receivePositions giữ [2] = giờ là C3.)
```

#### 13.12.3 Ô trống + vị trí 16 (Q7)

```jsonc
// two_party — nodes[4] và nodes[15] trích ra:
{"id": "p5",  "personId": null,              "hidden": false, "deleted": false},
{"id": "p16", "personId": "99999999-…-9999", "hidden": false, "deleted": false}
// p16 = ghế đầu bên B; xóa personId khỏi p16 → p16 trống, p17..p30 đứng yên.
```

#### 13.12.4 Một tài sản được nhiều người chọn (Q10)

```jsonc
{"id": "child_1", "personId": "…p3", "ownPositions": [],    "receivePositions": [1,2]},
{"id": "child_2", "personId": "…p4", "ownPositions": [],    "receivePositions": [1]},
{"id": "owner",   "personId": "…p1", "ownPositions": [1,2], "receivePositions": []}
// vị trí 1 vừa được child_1 + child_2 nhận và owner sở hữu — hợp lệ.
```

### 13.13 Quyết định owner (tập trung)

Q1–Q12 **đã duyệt nguyên đề xuất** (owner, 27/09/2026); phương án thay
thế bị loại giữ trong `_bmad-output/archive/linear-tasks/MIN-125/decisions.md` làm record.
Các quyết định then chốt:

- **Q1** — phá vòng phụ thuộc bằng `stage.owner_row_id` + create không
  cần diagram (thay vì "commit phiên" cục bộ hay nullable
  `nguoi_chet_id`).
- **Q4** — dấu chọn theo vị trí, không bám `row_id` khi reorder/xóa.
- **Q6** — `willReceive:true` legacy → nhận tất cả vị trí hiện có.
- **Q7** — `p1..p30` cố định, bên suy ra từ số.
- **Q11** — `document_type` `two_party` = `{chuyen_nhuong, tang_cho,
  cho_thue, dat_coc}`.

C1–C4 vẫn mở và đã có hướng xử lý: C1/C2 chốt cùng NV2 trước khi P6
cần; C3 quy ước tôn trọng `entity_id` (chi tiết persistence ở P5);
C4 là task Word riêng — §13.10 chỉ ghi ý định đánh số.

### 13.14 Checklist conformance bổ sung (áp dụng cho producer v2)

Producer v2 PHẢI (thêm vào §10):

- [ ] Emit `schema_version:"notary.case-drafting.v2"`;
      `diagram_state.version:3` + `domain` bắt buộc.
- [ ] Không emit `is_primary`, `isLandOwner`, `willReceive`; stage
      inheritance mang `owner_row_id` (result) — absent với `two_party`.
- [ ] `stage.assets` ≤3 trên mọi payload; `two_party` people ≤30;
      canonical 30 node `p1..p30` cho domain `two_party`.
- [ ] `workspace_create` v2: cho phép `diagram` absent; seed owner theo
      `owner_row_id`; `tai_san_id` = asset vị trí 1.
- [ ] Prune `personId` + dấu chọn vị trí `> len(assets)` trong cùng
      transaction commit/save — không prune tại thời điểm client sửa
      draft.
- [ ] `diagram_evaluate` two_party → `unsupported` render_model, không
      chạy engine thừa kế; `word_export_*` trên two_party được hỗ trợ
      (NAIA-8) — readiness qua `block_reason` §8.1.

Consumer v2 PHẢI (thêm vào §10):

- [ ] Giữ buffer draft tách committed; bỏ nháp không ghi buffer chưa
      commit (mở lại hồ sơ đọc bản committed); không prune diagram khi
      xóa row trong draft.
- [ ] Map chip `[1][2][3]` ↔ positions; không theo `row_id`; disable
      chip vị trí chưa có asset.
- [ ] Reject state v2/v3 sai domain, `is_primary`/`isLandOwner` dư —
      coi như `validation_error`/`diagram_invalid_state`.

### 13.15 Examples & validator draft

- Fixtures: `contracts/notary-case-drafting/examples/draft-v2/` —
  `*.valid.json` / `*.invalid.json` đặt
  `fixture_context.draft_v2:true` (+ `case_type` khi hai bên) để
  validator áp rule v2; file draft không ảnh hưởng bộ v1.
- Schema tham chiếu: `draft-v2.schema.json` (định nghĩa `stage_v2`,
  `diagram_state_v3`, payload create/commit v2). Normative text là
  §13 — file schema draft hỗ trợ đọc, không phải nguồn duy nhất cho
  tới khi owner duyệt.

### 13.16 Quy tắc Stage hiện hành sau gộp MIN-141

**Nguồn:** Owner xác nhận 03/10/2026 rằng 14 commit worker là cập nhật đúng,
yêu cầu đưa vào nhánh chính và đồng bộ tài liệu/code. Mục này thay các quy
tắc MIN-140 ngày 29/09/2026 bị mâu thuẫn; không đổi envelope/schema version.

- Người: họ tên bắt buộc; giới tính Nam/Nữ/null; ngày sinh/chết/cấp nhận
  YYYY-MM-DD, YYYY hoặc null; số giấy tờ/nơi cấp/địa chỉ/quê quán/loại giấy
  tờ/nhãn địa chỉ nhận chuỗi hoặc null. Số giấy tờ có giá trị vẫn kiểm trùng.
- Tài sản: serial là chuỗi nguyên văn tùy nguồn (Owner 06/10/2026 bỏ
  bắt buộc `[A-Z]{2}\d{6,8}` ở mọi tầng), địa chỉ không rỗng;
  số thửa/số tờ và các trường còn lại nullable. Cụm đất có thể null/[];
  mỗi cụm kiểm kiểu, không cho alias khác giá trị, tối đa 20 cụm.
- Đọc hồ sơ cũ: serial giữ nguyên văn trong master, không chuẩn hóa,
  không thay mã `XX`.
- `thoi_han` lẻ bỏ khỏi form và payload renderer; dữ liệu lịch sử vẫn giữ
  để đối chiếu/cảnh báo. Không tự gán vào thời hạn từng cụm.
- Quy tắc suy trường Người, nguồn snapshot và phần tra cứu xã chưa có:
  [`entities.md`](entities.md) §8–§9.
- Giữ nháp khi chuyển tab và khi commit lỗi; kiểm dữ liệu khi `Cập nhật`.
  Giữ kiểm revision, owner, khóa hồ sơ, giới hạn người/tài sản và trùng ID.

### 13.17 Nhập hợp đồng DOCX và mẫu gốc — additive NAIA-4 / MIN-139

**Nguồn:** Owner NAIA-4 chọn Word-first/lõi regex chung 02/10/2026, yêu cầu
triển khai 03–04/10/2026. Đây là bổ sung kênh nội bộ hiện hành, không tạo
contract trao đổi hồ sơ giữa Upload Lab và Soạn hồ sơ. Envelope vẫn v2.

- Intake giữ shape suggestion/field_value; `source_refs` DOCX có opaque
  `source_id` do backend tạo, `source_sha256`, `text_map_version:1`,
  candidate/occurrence ID, backend-produced `source_label`, raw code-point `span`, `raw_snippet`, rule/profile
  version/state, `docx_refs` part/path/node_span/supported. Một trường có thể
  nhiều refs. `land_rows` vẫn là JSON string của danh sách cụm trong nguồn;
  người dùng chọn tối đa 20 cụm cho mỗi tài sản Stage,
  refs từng trường con có `land_row` 1-based và `land_field`. Intake không
  emit confirmed. Mơ hồ giữ normalized null và mọi alternative.
- Create/commit/get và result có optional `docx_import`, schema tại
  [`common.schema.json`](notary-case-drafting/common.schema.json) definition
  `docx_import`: version 1, tối đa 8 nguồn; mỗi nguồn có source_id/hash,
  records candidate_id→row_id, bindings candidate_id/occurrence_id/field_key/
  slot, optional template_sha256 và label do backend tạo. Mỗi record tài sản
  có optional `land_rows`: danh sách số dòng nguồn theo vị trí cụm hiện tại;
  số nguyên dương không lặp, có thể lớn hơn 20, `null` cho cụm thêm tay.
  Danh sách đã chọn tối đa 20 phần tử. Record cũ thiếu khóa này
  được nâng từ thứ tự extraction; số cụm phải khớp Stage. Context chỉ chứa
  định danh/mã băm/tên file an toàn, không chứa đường dẫn khách, chữ gốc hay
  field nghiệp vụ tùy ý. `label` client gửi không được tin; backend lấy từ kho.
- Backend chỉ nhận ứng viên/vị trí từ extraction package đã lưu khi intake
  được cấp quyền. Stage và context lưu cùng transaction và revision; omit
  context giữ bản cũ, `sources:[]` là xóa đối chiếu. Xóa row prune record và
  binding, không gắn sang row khác. Bỏ nháp không ghi context chưa commit;
  mở lại hồ sơ đọc đúng context đã commit (nút `Hủy thay đổi` của Stage đã bỏ).
  Client kiểm giới hạn 8 nguồn trước khi thêm row. Gỡ nguồn gửi context còn
  lại (kể cả sources rỗng); không đọc file của nguồn được gỡ. Xóa cụm đất
  loại binding của chính cụm nguồn ấy; không lấy vị trí mảng mới làm danh tính.
- Word options/batch nhận optional `original_source_id`, không đi cùng
  template_dir. Options trả thêm `binding_proposals` gồm chữ gốc, candidate/
  occurrence/field/slot, row_id/row_label, giá trị đã lưu, supported, reason
  (null khi hợp lệ) và selected (lựa chọn đã lưu còn khớp). Proposal không
  hỗ trợ có thể có slot rỗng; proposal hỗ trợ và binding đã lưu phải có slot.
  Slot trống hoặc
  định dạng hỗn hợp không cho chọn; lưu bindings rỗng xóa mẫu đối chiếu.
  Proposal không phải binding đã xác nhận. Batch gốc cần base_revision và
  document_keys chính xác `["original.docx"]`; folder/catalog giữ hành vi cũ.
- Người N theo Stage; Bên A/B theo ô Diagram; tài sản N theo thứ tự Stage.
  Binding dùng row_id+field, slot phải khớp lại lúc xuất. N/seat đổi, source/
  derivative hash đổi, row mất hoặc slot trống → `word.original_mapping_invalid`,
  không thay ngầm. Span unsupported/chồng nhau từ chối khi lưu binding.
  Binding mới phải khớp catalog và giá trị bản Stage/sơ đồ vừa được dựng
  trong transaction; sai slot hủy cả lần lưu. Đổi thứ tự của binding cũ
  vẫn cần xác nhận lại trước khi xuất. Nhận giá trị ngày từ evidence dùng
  quy tắc chuẩn hóa ngày hiện có; mơ hồ đất kiểm từng ô, không cả field.
  Ngày sửa sai chặn Đưa vào Stage cho tới khi sửa đúng, không dùng giá trị cũ.
- Kho nguồn kiểm hash byte `extraction.json` qua `extraction.sha256`; dấu kiểm
  thiếu/hỏng hoặc nội dung đổi phải nhập và kiểm tra lại. Không tự tin dữ liệu cũ.
  Nguồn/mẫu chưa dùng vẫn giữ local; chưa duyệt thời hạn giữ hay dọn tự động.
  Sao lưu/dọn thủ công phải giữ tất cả nguồn/mẫu còn được hồ sơ tham chiếu.
- Bản derivative tạo riêng, hash/path backend cố định; xuất dùng mapping
  Word tích hợp và sửa đúng w:t span. Giữ package part khác byte-exact;
  không dùng paragraph.text/global replace để làm mất format/ảnh. Output
  độc lập, exclusive create và tăng hậu tố khi trùng; cancellation dọn temp,
  giữ file đã publish. Giới hạn và phạm vi đọc tại
  [`spec DOCX`](../_bmad-output/specs/notary_v2/word-templates.md#docx-import).

### 13.18 Chuyển loại hồ sơ đã lưu — ngoại lệ `case_type` immutable (owner 16/10/2026)

**Nguồn:** owner duyệt nguyên đề xuất #3 ngày 16/10/2026 —
[`decision-owner-saved-case-type-conversion-20261016.md`](../_bmad-output/decisions/decision-owner-saved-case-type-conversion-20261016.md);
evidence `_bmad-output/tmp/issue-3-saved-case-policy/evidence.md`. Đây là ngoại lệ
duy nhất cho luật `case_type`/`document_type` immutable (§6.1, §13.5, §13.6);
ngoài đường này hai key vẫn bất biến.

Phạm vi: hồ sơ **đã lưu** đổi giữa `inheritance` và `two_party`.

- **Giữ Stage:** `stage.people`/`stage.assets` giữ nguyên `row_id` và giá trị;
  không migrate/copy Người/Tài sản, không thêm bớt.
- **Reset Diagram:** state mới mang domain của loại đích, seed rỗng — two_party:
  đủ 30 node `p1..p30` với `personId:null`, không field quan hệ/dấu; inheritance:
  seed **chỉ** node `owner` mirror đúng người vừa chọn — **không** seed khung 7
  slot mặc định của tạo mới, không slot/quan hệ nào khác. Node này **vẫn đủ 8 key**
  bắt buộc của `node_v3_inheritance` (§13.4; `draft-v2.schema.json`), **rỗng giá
  trị chứ không bỏ key**: `id:"owner"`, `personId:<owner_row_id>`,
  `parentSlotIds:[]`, `spouseSlotId:null`, `ownPositions:[]`, `receivePositions:[]`,
  `hidden:false`, `deleted:false` (thiếu/`null` mảng → `invalid_node` như §13.4).
  Không có mapping liên miền; không suy ghế/quan hệ/tài sản từ domain cũ.
- **`document_type`:** hai tập enum rời nhau (`{khai_nhan, thoa_thuan}` ↔
  `{chuyen_nhuong, tang_cho, cho_thue, dat_coc}`); client **buộc người dùng chọn**
  giá trị hợp lệ của loại đích, không tự gán giá trị đầu enum.
- **Xác nhận:** một bước xác nhận nêu rõ phần Diagram sẽ mất trước khi ghi.
- **`owner_row_id`:** chuyển **vào** inheritance bắt buộc chọn `owner_row_id` là
  `row_id` có trong Stage hiện có (thiếu → `workspace_owner_required`); chuyển
  **vào** two_party **cấm** `owner_row_id` như §13.5/§13.6.
- **Không reset gì thêm** ngoài Diagram/domain và các guard `document_type`/owner.
- **Guard (không thêm cơ chế mới):** ghi kèm `base_revision`, lệch →
  `workspace_conflict`; hồ sơ `locked` chỉ đọc; một transaction, lỗi/hủy → hoàn
  tác toàn bộ, `revision` không đổi, bản cũ còn dùng được.
- **Word/binding:** giữ nguyên §13.17 — không remap ngầm; N/ghế đổi, hash/slot
  đổi → `word.original_mapping_invalid`; không thêm chặn cho hồ sơ đã xuất/bound.
- **Đường ghi:** `notary.workspace_convert_type`; commit Stage và
  `workspace_update` vẫn từ chối đổi loại. Schema:
  [`workspace-convert-type.schema.json`](notary-case-drafting/workspace-convert-type.schema.json).

```yaml
payload:
  case_id: <int >= 1>
  base_revision: <int >= 1>
  case_type: inheritance | two_party # phải khác loại đã lưu
  document_type: <enum hợp lệ loại đích, người dùng chọn rõ>
  confirm_diagram_reset: true
  owner_row_id: <uuid4> # chỉ inheritance, row_id Stage hiện có
result:
  kind: workspace_convert_type
  data: <workspace_get v2 đầy đủ, case.revision tăng 1>
```

Key ngoài schema, loại không đổi, văn bản sai enum hoặc chưa xác nhận →
`validation_error`; owner inheritance thiếu/ngoài Stage →
`workspace_owner_required`. Không gửi Stage hoặc Diagram draft trong command.
Stage/meta chưa lưu phải Cập nhật trước; UI không tự lưu/bỏ nháp để đổi loại.
Nháp Diagram chỉ bị reset sau thành công; hủy dialog/Escape/nền trước Áp dụng
không gửi command. Sau Áp dụng dialog chờ kết quả, không thêm nút hủy in-flight.
Command cancel được chấp nhận trước giao dịch thì không ghi; giao dịch ngắn
và publish succeeded được phân xử cùng khóa job, cancel đến sau thành công
bị từ chối terminal. Các command khác không thay semantics hủy.

---

## 14. `notary.address_lookup` — lõi tra cứu tên xã/tỉnh (v2, TASK-2)

**Trạng thái:** v2 APPROVED 05/10/2026 — Owner duyệt, runtime đã chuyển
sang v2 tại TASK-3 (schema v1 đã xóa).
**Breaking** so với v1.
**SOT hành vi:** [`_bmad-output/specs/shared/administrative-lookup.md`](../_bmad-output/specs/shared/administrative-lookup.md#lookup);
cách hồ sơ gọi: [`_bmad-output/specs/notary_v2/administrative-address.md`](../_bmad-output/specs/shared/administrative-lookup.md#usage).

Command thứ mười của nhóm `notary.*`; `result.data.schema_version` =
`notary.address-lookup.v2` (literal), ngoại lệ của rule §1. **Read-only,
local-only**: chỉ đọc ledger hành chính đóng gói; không gọi Bando hay dịch vụ
ngoài, không ghi DB, không cần `case_id`/`base_revision`. Địa chỉ khách hàng
không rời máy. Chỉ gửi khi người dùng bấm nút Tra.

### 14.1 Payload

```yaml
payload:
  query: <string 1..4000>         # bắt buộc — nguyên văn người dùng gõ/dán
  presentation: drafting | full   # bắt buộc — kiểu trình bày của nơi gọi
```

- Key ngoài danh sách (kể cả `source_date`, `target_date`, `province`,
  `commune`, `district` của v1), `query` không phải chuỗi 1..4000 ký tự,
  `presentation` lạ → `invalid_input`. *Tại sao bỏ ngày và tách xã/tỉnh:* lõi
  chỉ trả bước cuối; mỗi cụm được tra độc lập vào xã và tỉnh trên toàn quốc,
  không khoanh phạm vi theo tỉnh hay bỏ qua cụm huyện (spec §2, §7).

### 14.2 Result

```yaml
result.data:
  schema_version: "notary.address-lookup.v2"
  status: found | not_found | too_many | invalid_input | reload_failed
  presentation: drafting | full | null    # null chỉ khi invalid_input
  total: <int >= 0>                        # số dòng kết quả khớp, kể cả cùng đơn vị
  results:                                 # rỗng nếu status != found
    - unit_id: <string>                    # đơn vị HIỆN HÀNH
      level: commune | province
      name: <string>                       # tên chính thức trong kho, có tiền tố
      province: {unit_id, name} | null     # null khi level = province
      source_text: <string | null>         # đoạn "sáp nhập từ" Bando nguyên văn
      display: <string>                    # chuỗi theo presentation
      observation_id: <id>                 # optional
      evidence: [{source_id, row_key}]
  dataset_version: <string | null>
  revision: <int | null>
```

- `found`: `total = len(results) >= 1`. Với `drafting`, `total <= 10`.
- Mỗi dòng nguồn khớp trả riêng với `source_text`, `evidence`, `observation_id`
  của nó. Cùng `unit_id` được có nhiều dòng; client không bỏ trùng theo tên,
  `unit_id` hoặc `display`. Chỉ bỏ cùng dòng `(unit_id, observation_id)` khớp
  nhiều cụm. Đơn vị không có observation khớp tên thì trả một dòng, không có
  `observation_id`, `source_text: null`. Không tự chọn/gộp nguồn hay trả lỗi
  vì có nhiều nguồn; người dùng xem và chọn (Owner 05/10/2026).
- `too_many`: chỉ khi `presentation = drafting` và `total > 10`; `results`
  rỗng. Client hiện popup "Nhiều kết quả khớp. Xem đầy đủ?"; chỉ khi người
  dùng đồng ý mới mở tool tra cứu dạng popup đè lên màn hình hiện tại (không
  điều hướng, không mất nháp), gửi lại cùng `query` với `presentation: full`.
  *Tại sao:* không hiện nửa kết quả ở ô soạn thảo.
- `not_found`, `invalid_input`, `reload_failed`: `total = 0`, `results` rỗng.
  `reload_failed` = ledger/snapshot cục bộ lỗi; không trả kết quả cũ dưới nhãn
  phiên bản mới.
- `display`: `drafting` → `xã Ý Yên, tỉnh Ninh Bình` (danh từ chung viết
  thường); `full` → `Xã Ý Yên = <source_text>, Tỉnh Ninh Bình`.
- Command không chọn thay người dùng; client không tự ghi kết quả vào ô.
- Mọi lỗi đầu vào/kho nằm trong `result.data.status` (job thành công), không
  phải `error.code` job-level.
- Bỏ so với v1: `parsed`, `candidates`, `provenance`, `coverage`, `historical`,
  `partial`, `event_ids`, `old_parent_unconfirmed`, status `match`/`ambiguous`.
  *Tại sao:* lõi chỉ phản ánh bước cuối của kho; đoạn chữ gốc đã chứa ghi chú
  gộp/tách.
- Ledger reload có chữ ký file (path+mtime+size) và validate toàn phần trước
  khi đổi index — không đọc ledger theo từng lần gọi.

### 14.3 Schema & examples

- Schema máy đọc v2:
  [`address-lookup.v2.schema.json`](notary-case-drafting/address-lookup.v2.schema.json).
- Examples:
  `examples/valid/command.address-lookup.valid.json` (payload),
  `examples/valid/job.address-lookup.valid.json` (`found`, `drafting`),
  `examples/valid/job.address-lookup-too-many.valid.json` (`too_many`),
  `examples/invalid/command.address-lookup-year.invalid.json`
  (gửi trường ngày của v1 bị từ chối).

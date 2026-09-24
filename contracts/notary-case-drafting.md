# Contract: Notary Case Drafting `v1`

**Version:** `notary.case-drafting.v1` · **Status:** DRAFT — chờ owner duyệt
(MIN-105) · **Owner:** `systemdocs` · **Published:** MIN-105 ·
**Kênh mang:** `desktopcommand.v1` (`contracts/desktop-command.md`) ·
**Domain data shape:** `g1.module.v1` (`contracts/g1-module-data.md`)

Contract wire cho tab **Soạn hồ sơ** của module `notary_v2` trong shell
Electron một máy: bảy command `notary.*` phục vụ tải workspace, intake
đa nguồn thành suggestion, commit Stage, đánh giá/lưu Diagram và xuất
Word hàng loạt. Envelope `desktopcommand.v1` giữ nguyên — file này chỉ
định nghĩa `payload`/`result.data`/error code của từng command.

SOT hành vi nghiệp vụ:
`notary_v2/docs/platform/case-workspace/drafting-tab.md` (đã duyệt qua
MIN-104) — file này là wire contract, không định nghĩa lại hành vi.
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
| `notary.workspace_get` | Tải case + Stage (Người/Tài sản) + Diagram + revision + capabilities | read-only | `workspace_get` |
| `notary.intake_analyze` | Phân tích file/text thành suggestion chờ review | long-running, không commit | `intake_analyze` |
| `notary.workspace_commit_stage` | Commit toàn bộ Stage trong một transaction | atomic write | `workspace_commit_stage` |
| `notary.diagram_evaluate` | Đánh giá/tính thử draft Diagram | read-only theo DB, không persist draft | `diagram_evaluate` |
| `notary.diagram_save` | Lưu Diagram đã hợp lệ | atomic write | `diagram_save` |
| `notary.word_export_options` | Liệt kê văn bản sẵn sàng/bị chặn | read-only | `word_export_options` |
| `notary.word_export_batch` | Tạo nhiều DOCX vào một folder đích | long-running, per-item result | `word_export_batch` |

- `result.kind` = tên command bỏ namespace `notary.` (snake_case nguyên
  vẹn). `result` theo shape `g1-module-data.md` §2: `{kind, data,
  evidence?, warnings?, source_files?}`.
- Mọi `result.data` của bảy command **bắt buộc** mang
  `schema_version: "notary.case-drafting.v1"` (literal). Đây là version
  của domain data shape; version kênh vẫn là `contract_version` của
  envelope — hai tầng độc lập.
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
| `revision` | integer ≥ 1 | Số phiên bản workspace của case; mọi write thành công (`workspace_commit_stage`, `diagram_save`) tăng đúng 1 |
| `base_revision` | integer ≥ 1 | Revision client đang giữ khi ghi; bắt buộc trên mọi command **ghi** (`workspace_commit_stage`, `diagram_save`); khác server (`<` **hoặc** `>`) → `workspace_conflict` |
| `source_id`, `suggestion_id` | string UUID v4 | `source_id` do client sinh khi build request; `suggestion_id` do backend sinh |
| `document_key` | string `^[a-z][a-z0-9_]*$` | Khóa ổn định của văn bản; không đổi khi đổi tên hiển thị/template; registry mở — backend được thêm key mới, không được đổi nghĩa key đã publish |
| `node.id` (Diagram slot) | string non-empty | Định danh slot trên Diagram do UI đặt; khác namespace với `row_id`/`personId` |
| `personId` (Diagram node) | string UUID v4 \| null | Tham chiếu `row_id` của một **dòng Người trong Stage đã commit**; `null` = slot trống |

Kiểu ID không được đổi giữa mock và real backend.

### 2.2 Ngày và thời điểm

- Ngày không giờ (ngày sinh/chết/cấp): `YYYY-MM-DD` **hoặc** `YYYY`
  (year-only — tương đương 01/01 năm đó, dùng khi chỉ biết năm) **hoặc**
  `null`. Wire chỉ hai dạng đó: producer phải chuẩn hóa mọi format khác
  (hiện trạng web trộn `dd/mm/YYYY`, `yyyy`, ISO) trước khi emit.
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
  `diagram_save`, `word_export_batch`) →
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
  ngay_chet: <YYYY-MM-DD | YYYY | null>   # null = còn sống/không rõ
  so_giay_to: <string | null>        # CCCD/CMND/hộ chiếu — free text,
                                     # không ép 12 số (không phải khóa)
  ngay_cap: <YYYY-MM-DD | YYYY | null>
  noi_cap: <string | null>
  dia_chi: <string | null>
  place_of_origin: <string | null>
```

Không thêm field ngoài danh sách này — producer strip field lạ (tiền lệ
backend hiện strip ngoài 10 key). `ho_ten` rỗng/`""` →
`stage_validation_error{field:ho_ten, code:required}`.

### 4.2 `asset_row` — dòng Tài sản Stage

```yaml
asset_row:
  row_id: <uuid4>
  entity_id: <int | null>
  is_primary: <bool>
  so_serial: <string non-empty>      # bắt buộc; canonical [A-Z]{2}\d{6,8}
                                     # theo entities.md §2 (producer
                                     # chuẩn hóa trước khi emit)
  so_vao_so: <string | null>
  so_thua_dat: <string | null>
  so_to_ban_do: <string | null>
  dia_chi: <string non-empty>        # bắt buộc
  loai_so: <string | null>
  hinh_thuc_su_dung: <string | null>
  thoi_han: <string | null>
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

## 5. `notary.intake_analyze` — payload + result

### 5.1 Payload

```yaml
payload:
  case_id: <int>
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
- `case_id` không tồn tại/`locked`/case_type khác →
  `case_not_found`/`workspace_locked`/`case_type_unsupported`. Engine
  OCR thiếu → `engine_not_installed` (reuse envelope §8).

## 6. `notary.workspace_commit_stage` — payload + result

```yaml
payload:
  case_id: <int>
  base_revision: <int ≥ 1>
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
  invalid_format, duplicate_row_id, primary_count`.
- `so_serial` không canonical `[A-Z]{2}\d{6,8}` →
  `invalid_format` (entities.md §2); `so_giay_to` không ép format.
- Stage Người trùng tên/tài sản trùng là quyền người dùng — backend
  không tự merge.

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
  `nodes[].personId`. `hidden`/`deleted` giữ trong state (engine bỏ qua
  node `deleted`).
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
      baseShare: <fraction string, vd "1/2">
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
- Fraction biểu diễn chuỗi `"a/b"` — consumer **không** tự tính tỷ lệ;
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
  case_id: <int>
  diagram:
    state: <diagram_state>          # draft state — KHÔNG persist
```

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  evaluated_revision: <int>         # revision Stage server dùng để
                                    # evaluate — client so với revision
                                    # đang giữ để cảnh báo Stage đã đổi
  render_model: <render_model>
```

- Read-only theo DB: evaluate **không** ghi state, không đổi Stage,
  không đổi revision. Vì read-only, evaluate **được phép trên case
  `locked`** (chỉ các command ghi bị `workspace_locked`).
- `personId` ngoài Stage đã commit → `diagram_reference_outside_stage`;
  state sai cấu trúc → `diagram_invalid_state`.

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
- `base_revision` cũ → `workspace_conflict`; case locked →
  `workspace_locked`.

## 8. `notary.word_export_options` + `notary.word_export_batch`

### 8.1 `notary.word_export_options`

```yaml
payload:
  case_id: <int>
```

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  documents:
    - document_key: <snake_case>
      display_name: <string>
      ready: <bool>
      block_reason: <null | code>   # chỉ khi ready:false
```

`block_reason` code hóa (v1 — data-code dạng `word.*`, §2.5):

```
word.no_assets              # hồ sơ chưa có tài sản
word.no_landowner           # chưa có chủ đất trên Diagram
word.no_deceased_landowner  # không có chủ đất đã chết
word.no_receiver            # chưa có người nhận
word.too_many_assets        # > 5 tài sản
word.too_many_people        # > 20 người trên Diagram
word.too_many_signers       # > 20 người ký
word.template_missing       # văn bản chưa có template
```

Mapping từ validation thật của `word_engine` (audit `services/word_engine.py`
:809-910): không tài sản → `no_assets`; >5 tài sản → `too_many_assets`;
không chủ đất → `no_landowner`; không chủ đất đã chết →
`no_deceased_landowner`; không người nhận → `no_receiver`; >20 người trên
Diagram → `too_many_people`; >20 người ký → `too_many_signers`.

Catalog `document_key` v1 (registry mở — backend được thêm):

| `document_key` | `display_name` | Ghi chú |
|---|---|---|
| `khai_nhan_di_san` | Văn bản khai nhận di sản | map `document_type=khai_nhan` |
| `thoa_thuan_phan_chia` | Thỏa thuận phân chia di sản | map `document_type=thoa_thuan` |
| `niem_yet` | Thông báo niêm yết | chưa có template → `ready:false, block_reason:word.template_missing` là hợp lệ |

### 8.2 `notary.word_export_batch` — payload

```yaml
payload:
  case_id: <int>
  document_keys: [<document_key>]   # 1..n, unique
  destination: <file_ref>           # PHẢI is_dir:true — §3
```

- `document_keys` rỗng → `word_no_documents_selected`; trùng →
  `word_duplicate_document_key`; key ngoài catalog →
  `word_unknown_document_key`; key sai pattern →
  `word_unknown_document_key`.
- Validate **trước khi tạo file đầu tiên**: mọi lỗi trên + destination
  + `case_type_unsupported`/`workspace_locked` → `failed`, không file
  nào được tạo.

### 8.3 Naming và không-ghi-đè

```
<filename_stem>_HS-<case_id>[_{n}].docx      n ≥ 2
```

- `filename_stem`: chuỗi ASCII do **catalog backend** sở hữu cho mỗi
  `document_key` (không phải transform cơ học của `display_name`);
  pattern `^[A-Za-z0-9_-]+$`. Backend quyết `actual_filename`, UI chỉ
  hiển thị.
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
| `case_type_unsupported` | `case_type` khác `inheritance` trên command ghi/evaluate/export | `{case_type}` |
| `workspace_locked` | write trên case `locked` | — |
| `workspace_conflict` | `base_revision` < revision server | `{server_revision}` |
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
- [ ] Mock backend trả `backend_mode:"mock"` trong `workspace_get`.

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

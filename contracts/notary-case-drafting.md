# Contract: Notary Case Drafting — v2, doc rev G4 single-save (23/10/2026)

**Version hiện hành:** `notary.case-drafting.v2` · **Doc revision:** G4 single-save,
23/10/2026; Storage B **vòng 2 ĐÃ TRIỂN KHAI 22/10/2026, có proof** (chi tiết ở §13.20/§13.21). V1 APPROVED 24/09/2026 (MIN-105),
rev 1.1 MIN-121 và v2 APPROVED 27/09/2026 (MIN-125/P5 MIN-128) là mốc lịch sử. ·
**Owner:** `systemdocs` · **Published:** MIN-105 ·
**Kênh mang:** `desktopcommand.v1` (`contracts/desktop-command.md`) ·
**Domain data shape:** `g1.module.v1` (`contracts/g1-module-data.md`)

Contract wire cho tab **Soạn hồ sơ** của module `notary_v2` trên envelope
`desktopcommand.v1`: payload, result và error của các command bên dưới.
**Vòng 2 issue 13 ĐÃ TRIỂN KHAI 22/10/2026:** Storage B vòng 1 (rows case-owned + `draft|done` +
`notary.workspace_save_case`, §13.19) đã có code chạy; vòng 2 bổ sung
`notary.workspace_source_latest` (§13.20), `notary.workspace_duplicate` (§13.21) và
đường tạo nháp ít dữ liệu trên `workspace_create` (§4.3/§13.6). Mọi hành vi vòng 2
dưới đây **đã có proof** (`test_issue13_source_latest.py`,
`test_issue13_workspace_duplicate.py`, `test_issue13_partial_draft.py`,
`test_issue13_storage_b_proof.py`). Đây là contract cho cutover
phối hợp renderer/backend tiền MVP, **không tương thích client cũ**.
Giữ literal `notary.case-drafting.v2` và Diagram v3. V1/rev 1.1 là lịch sử;
các shape v1 minh họa phần nền được §13 thay bằng v2. Không phát hành song song
consumer v1. Các quy tắc Storage B ghi trực tiếp ở phần nền cũng áp cho v2.
**G4 — quyết định owner 23/10:** renderer Soạn hồ sơ không còn nút **Cập nhật/
Lưu nháp**; Stage, Pool và Diagram cùng đọc bản đang sửa. Chỉ **Lưu hồ sơ**
gửi `workspace_save_case` để persist nội dung đang soạn (§13.2/§13.19).
Các API ghi riêng vẫn hỗ trợ consumer khác; ngoại lệ meta trong dialog Word
qua `saveCaseMeta`/`workspace_update` giữ nguyên (§6.2).


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
| `notary.workspace_create` | API tạo hồ sơ draft từ Stage + Diagram; giữ cho consumer khác, renderer Soạn hồ sơ không gọi để lưu nháp | atomic write, idempotent | `workspace_create` |
| `notary.workspace_get` | Tải case + Stage (Người/Tài sản) + Diagram + revision + capabilities | read-only | `workspace_get` |
| `notary.workspace_source_latest` | Đọc toàn bộ Người/Tài sản của case Done lưu gần nhất làm nguồn cho nháp mới | read-only, không ghi DB | `workspace_source_latest` |
| `notary.workspace_duplicate` | Nhân bản toàn bộ nội dung đã lưu của một hồ sơ thành case mới | atomic write, idempotent | `workspace_duplicate` |
| `notary.intake_analyze` | Phân tích file/text thành suggestion chờ review | long-running, không commit | `intake_analyze` |
| `notary.workspace_commit_stage` | API commit toàn bộ Stage trong một transaction; server/adapter/REST giữ hỗ trợ, renderer Soạn hồ sơ không gọi | atomic write | `workspace_commit_stage` |
| `notary.workspace_update` | Cập nhật meta hồ sơ đã lưu (`ngay_lap_ho_so`, `noi_niem_yet`, `ghi_chu`) — không đụng Stage/Diagram | atomic write | `workspace_update` |
| `notary.diagram_evaluate` | Đánh giá/tính thử draft Diagram | read-only theo DB, không persist draft | `diagram_evaluate` |
| `notary.diagram_save` | Lưu Diagram đã hợp lệ | atomic write | `diagram_save` |
| `notary.workspace_save_case` | Đường Lưu hồ sơ duy nhất của renderer Soạn hồ sơ: toàn bộ Stage/meta/Diagram/ngữ cảnh Word đang sửa; chuyển draft→done | atomic write; tạo mới idempotent, case cũ revision-guarded | `workspace_save_case` |
| `notary.word_export_options` | Liệt kê văn bản sẵn sàng/bị chặn | read-only | `word_export_options` |
| `notary.word_export_batch` | Tạo nhiều DOCX vào một folder đích | long-running, per-item result | `word_export_batch` |
| `notary.address_lookup` | Tra cứu tên xã/tỉnh hiện hành từ chuỗi người dùng gõ (ledger local, lõi dùng chung) | read-only, local-only | `address_lookup` |

- `result.kind` = tên command bỏ namespace `notary.` (snake_case nguyên
  vẹn). `result` theo shape `g1-module-data.md` §2: `{kind, data,
  evidence?, warnings?, source_files?}`.
- Mọi `result.data` Soạn hồ sơ hiện hành mang
  `schema_version:"notary.case-drafting.v2"`; literal v1 trong ví dụ phần nền
  chỉ mô tả lịch sử. `notary.address_lookup` (§14) dùng domain riêng
  `notary.address-lookup.v2`. Version envelope độc lập với domain.
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
| `row_id` | string UUID v4 | Định danh dòng case-owned do UI tạo; ổn định qua ghi/đọc, là khóa Diagram/participant/đất, không phải identity dùng chung. `workspace_source_latest` và `workspace_duplicate` trả **UUID v4 mới** cho mọi dòng, không tái dùng row_id nguồn |
| `entity_id` | integer \| null | ID Customer/Property dùng chung do server resolve trong transaction ghi; có thể null kéo dài khi thiếu neo, không tạo identity giả. Đây là **trường nội bộ (wire echo)**, không có ô nhập: mọi `entity_id` client gửi chỉ là gợi ý và server tự quyết (§4.1 mục 5); không bao giờ phát `stage_validation_error` cho field này |
| `revision` | integer ≥ 1 | Case mới revision=1; mọi write case đã có tăng đúng 1, kể cả lưu lại Done sạch |
| `base_revision` | integer ≥ 1 | Bắt buộc với write case đã có, gồm save_case/convert_type; khác server (`<` hoặc `>`) → workspace_conflict trước ghi; cấm khi tạo mới |
| `source_id`, `suggestion_id` | string UUID v4 | `source_id` do client sinh khi build request; `suggestion_id` do backend sinh |
| `document_key` | string `^[a-z][a-z0-9_]*$` | Khóa ổn định của văn bản; không đổi khi đổi tên hiển thị/template; registry mở — backend được thêm key mới, không được đổi nghĩa key đã publish |
| `node.id` (Diagram slot) | string non-empty | Định danh slot trên Diagram do UI đặt; khác namespace với `row_id`/`personId` |
| `personId` (Diagram node) | string UUID v4 \| null | Trỏ row_id Người trong Stage của ngữ cảnh hiện tại: bản đang sửa ở renderer, Stage cùng payload với create/save_case/evaluate nháp, bản DB với get/diagram_save; null là slot trống (§13.2, §13.19 quy định prune refs pending) |
| `idempotency_key` | string UUID v4 | Bắt buộc khi workspace_create, save_case mới hoặc `workspace_duplicate`; cùng key + creation hash trả workspace hiện tại created=false, không ghi; khác hash → idempotency_conflict (§13.19/§13.21). Duplicate dùng hash `{command, intent, source_case_id}`, không hash snapshot nguồn |

### 2.1a `case_id` — bắt buộc vs chế độ nháp

- `case_id: <int ≥ 1>` **bắt buộc** trên `workspace_get`,
  `workspace_commit_stage`, `workspace_update`, `diagram_save`,
  `word_export_options`, `word_export_batch`.
- **Chế độ nháp phiên** (không phụ thuộc hồ sơ đã có ID hay chưa):
  `intake_analyze` và `diagram_evaluate` cho phép **absent** `case_id`
  = phân tích/đánh giá trên nháp phiên, không đụng DB case. Renderer dùng
  chế độ này để evaluate bản đang sửa cả khi đang mở hồ sơ đã lưu (§13.2).
  - `case_id` absent + `diagram_evaluate` → payload PHẢI kèm `stage`
    (§7.4); `personId` trong diagram được kiểm theo stage payload đó.
  - `case_id` absent + `intake_analyze` → chỉ phân tích nguồn thành
    suggestion; result shape không đổi.
  - `case_id: null` **tường minh** → `validation_error` (phân biệt
    "thiếu = nháp" với "null = lỗi client").
  - `case_id` present nhưng không phải int ≥ 1 → `validation_error`.
- `notary.workspace_create` **không nhận** `case_id` (server gán id);
  payload có `case_id` → `validation_error`.
- `notary.workspace_source_latest` **không nhận** `case_id` hay bất kỳ
  key nào khác: payload bắt buộc `{}` (§13.20). Nguồn do server chọn,
  không do client chỉ định.
- `notary.workspace_duplicate` nhận `source_case_id` (không phải
  `case_id`) + `idempotency_key`; **cấm** `case_id`/`base_revision`/
  `case`/`stage`/`diagram`/`status`. Đây là tạo **case mới** từ nội dung
  nguồn, nên luật "mọi write case đã có cần `base_revision`" không áp.
  `source_case_id: null`/Boolean/sai kiểu → `validation_error`.
- `workspace_save_case`: `case_id` **absent** → bắt buộc `idempotency_key`,
  cấm `base_revision`; `case_id` **present** → int ≥1, bắt buộc
  `base_revision`, cấm `idempotency_key`. Null/Boolean/sai kiểu là
  `validation_error`. Stage và Diagram được kiểm tham chiếu theo cùng payload.

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
- Thời điểm wire (`observed_at`, `created_at`/`updated_at` của result):
  ISO-8601 có múi giờ. **Không đồng nhất** với mốc lưu nội bộ: cột
  `updated_at` của case lưu Python UTC-naive đủ **microsecond** và là khóa
  chọn nguồn (§13.20); `Diagram.updatedAt` trong JSON chỉ tới giây.
  Ngày nghiệp vụ (`ngay_lap_ho_so`, ngày cấp…) vẫn là ngày không giờ.
- Mốc lưu: mọi writer case (create, save_case, commit, update_meta,
  convert_type, diagram_save, participant add/edit/delete, legacy create)
  đóng **cùng một** stamp microsecond trong transaction của nó; replay/
  lỗi/đọc/evaluate/export không đóng stamp. Không backfill timestamp cũ.
- `""` **không hợp lệ** thay `null` ở mọi field nullable — consumer
  reject bằng `validation_error` (g1-module-data §6).

### 2.3 Null / boolean / cấm `confirmed`

- `null` = không quan sát được / không áp dụng. Renderer hiển thị "—".
- Boolean strict: `true`/`false` JSON; `"false"` chuỗi →
  `diagram_invalid_state` (bám rule engine `invalid_boolean`).
- Suggestion/intake **không bao giờ** mang key `confirmed` ở bất kỳ cấp
  nào. Xác nhận duy nhất = người dùng đưa gợi ý vào Stage rồi
  **Lưu hồ sơ**. Xuất hiện `confirmed` → `validation_error`.
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
    status: draft | done          # Done vẫn sửa được; không có field locked
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
    owner_row_id: <uuid4 | null>   # v2 inheritance: null khi nháp chưa gán;
                                   # absent với two_party (§13.6)
    people: [<person_row>]         # §4.1 — ho_ten có thể null khi nháp
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
- Chỉ `draft|done`; Done cho phép sửa Stage/meta/Diagram, chuyển loại và xuất
  Word theo guard hiện hành, không read-only theo status. Không có
  `case.locked` hoặc error `workspace_locked` trong luồng soạn.
- GET đọc ordered case rows thuần, kể cả rỗng; không ghi DB, migrate-on-read,
  tăng revision hoặc fallback Customer/Property. Hồ sơ nháp tạo bằng
  `workspace_create` vòng 2 có thể đọc lại với `people`/`assets` rỗng, tên
  `null` hoặc `owner_row_id=null`; đây là dữ liệu hợp lệ của **đọc**, không
  nới validation của save_case/commit/convert. Nhãn hiển thị: `draft` = Nháp,
  `done` = Đã lưu; `trang_thai` raw vẫn là giá trị cho máy.
- Với wire v2, `stage` mang thêm `owner_row_id` (§13.6): inheritance luôn
  emit key (UUID hoặc `null` cho nháp chưa gán); two_party không có key.
- `case_id` không tồn tại → `failed{code:case_not_found}`.
- `backend_mode` là field duy nhất phân biệt mock/real; renderer bắt
  buộc hiển thị nhãn khi `mock`.

### 4.1 `person_row` — dòng Người Stage

```yaml
person_row:
  row_id: <uuid4>
  entity_id: <int | null>
  ho_ten: <string non-empty | null>    # output: null được với nháp chưa có tên
                                       # input create partial/save_case: null/absent được
                                       # input commit strict: bắt buộc non-empty
  gioi_tinh: Nam | Nữ | null
  ngay_sinh: <YYYY-MM-DD | YYYY | null>
  ngay_chet: <YYYY-MM-DD | YYYY | null>   # null = không có thông tin ngày chết
  so_giay_to: <string | null>        # free text, được trùng; thiếu → entity_id null
  ngay_cap: <YYYY-MM-DD | YYYY | null>
  noi_cap: <string | null>
  dia_chi: <string | null>
  place_of_origin: <string | null>   # case row; intake/UI không nhập mới (Owner 06/10)
  loai_giay_to: <string | null>      # (đợt 3) loại giấy tờ ĐÃ XÁC NHẬN —
                                     # người chết: lựa chọn/OCR của user;
                                     # người sống: server suy theo mốc
                                     # ngay_cap 01/10/2024 khi trống
  loai_dia_chi: <string | null>      # (đợt 3) nhãn địa chỉ — Thường trú
                                     # tại/Cư trú tại/Nơi chết; server suy
                                     # khi trống
```

Không thêm field ngoài danh sách này — producer strip field lạ (tiền lệ
backend hiện strip ngoài 10 key). `ho_ten` là **mức tối thiểu duy nhất**
của dòng Người: rỗng/`""`/toàn khoảng trắng → `stage_validation_error
{field:ho_ten, code:required}` trên save_case/commit; `null` chỉ hợp lệ ở
**output đọc** và **input create partial** (vòng 2). Mọi field Người khác
được để trống mà không chặn; sáu field chữ tùy chọn (`so_giay_to`,
`noi_cap`, `dia_chi`, `place_of_origin`, `loai_giay_to`, `loai_dia_chi`)
nhận `""`/toàn khoảng trắng và **chuẩn hóa thành null khi ghi** (S4d,
owner 23/10/2026), không sinh lỗi. Ngày trống bỏ qua; ngày có nội dung
nhưng sai lịch/không parse được → `invalid_date`; giới tính ngoài
Nam/Nữ/null → `invalid_enum`.
Ô chỉ có số giấy/ngày cấp mà chưa có tên chỉ được lưu qua `workspace_create`
(partial) với `ho_ten=null`, không dùng chuỗi giả.

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
  Đây không cấm gom ID theo điểm neo bên dưới; không được tự mượn trường
  thiếu giữa văn bản hoặc cập nhật ngược Hồ sơ đã lưu.
- `ngay_chet=null` chỉ là không có thông tin ngày chết, không tự kết luận
  còn sống. Các trường hợp lệ khác được điền độc lập; thiếu ngày chết/giấy
  không chặn Người. Không tạo ngày giả/01/01, Boolean hoặc status mới.
  Không xóa raw/history, phá liên kết đã có hoặc đổi logic câu Word.

**Storage B — vòng 1 có code, vòng 2 ĐÃ TRIỂN KHAI 22/10/2026:** mỗi dòng thuộc đúng một Hồ sơ.
`case_person_rows` lưu nguyên tên, số và toàn bộ dữ kiện §4.1; `entity_id`
ánh xạ `customer_id` nullable, không dùng Customer làm SOT hoặc fallback.
`row_id/case_id/vitri` là khóa dòng/quyền sở hữu/thứ tự; mọi field nghiệp vụ
snake_case ở shape trên ánh xạ cột cùng tên. Ba ngày lưu String(10)
`YYYY|YYYY-MM-DD|null`, không ghi ngày 01/01 quy ước. `place_of_origin`,
loại giấy/nơi cấp/nhãn địa chỉ nằm trên row, không trong Stage JSON.

**Resolve identity trong transaction ghi; ở renderer Soạn hồ sơ chỉ tại Lưu hồ sơ (`workspace_save_case`), không khi sửa ô/gán node. Các API create/commit cho consumer khác vẫn resolve theo cùng luật:**
1. Khóa tên: Unicode NFD → bỏ category Mn → đ/Đ thành d/D → lower →
   split/join whitespace bằng một space. Không bỏ dấu câu/đảo từ/fuzzy.
2. Khóa số giấy: trim ngoài; chỉ khi toàn chuỗi gồm chữ số, dấu chấm,
   whitespace và bỏ dấu phân cách được đúng 12 chữ số thì dùng 12 số đó.
   Còn lại giữ nguyên sau trim, kể cả số 0 đầu, dấu phẩy/quyển/gạch/hoa thường.
   Không lấy một CCCD nằm trong text, không đưa loại giấy vào match.
3. Thiếu tên hoặc số → identity null, kể cả trước đã có ID; không xóa identity.
   **Vòng 2:** row mới của `workspace_create` được phép `ho_ten=null` (nháp ít
   dữ liệu); row đó có identity null cho tới khi bổ sung đủ neo. Save/commit
   strict vẫn cần tên trước khi ghi.
4. Row cũ có ID mà neo vẫn khớp khóa identity đó → giữ ID dù có ID trùng nhỏ hơn.
   Neo đổi chỉ rebind row đang ghi, không sửa neo identity cũ hoặc Hồ sơ khác.
   Row mới/đổi neo chọn ID nhỏ nhất trong các match; không có thì tạo identity
   tối thiểu tên/số/khóa. Cache anchor trong transaction để dùng chung ID.
5. **Gợi ý identity (`entity_id`) chỉ là gợi ý nội bộ — không chặn user:**
   client có thể gửi `entity_id` trên mọi dòng như echo/gợi ý từ GET, nguồn
   Done hoặc nhân bản. Server chuẩn hóa: chỉ giá trị int ≥ 1 mới là hint;
   giá trị rác coi như không có hint. Hint không tồn tại, lệch identity đang
   gắn dòng hoặc không khớp neo đều bị **bỏ** và identity được resolve lại
   theo neo chuẩn: Người = (tên chuẩn hóa + số giấy tờ), Tài sản = serial.
   Không có neo khớp → dòng lưu với `entity_id=null` như dòng mới; **không
   bao giờ** phát `stage_validation_error` cho `entity_id`. Neo của payload
   còn khớp identity nguồn → giữ đúng ID (kể cả ID cao khi có ID cũ trùng
   neo); neo bị sửa → resolve lại theo neo mới, không sửa master. Không lấy
   trường từ identity để lấp Stage, không upsert dữ kiện vào master.
6. Hai row_id cùng identity vẫn hai dòng độc lập; không duplicate_entity,
   không compact, UNIQUE neo hoặc merge/xóa/chuyển link Hồ sơ khác.

Serial resolve theo §4.2. Chọn ID không phải chọn **bộ nguồn**: nguồn cho
Hồ sơ mới là bộ của case Done lưu gần nhất (§13.20), không master ID nhỏ nhất;
UI lấy nguồn, nhân bản toàn Hồ sơ (§13.21); copy/paste Excel vẫn ngoài vòng 2.
Một Hồ sơ chỉ một snapshot hiện hành, không lịch sử mỗi ô/lần lưu; #41 OPEN/gate mẫu ĐÓNG, #42 riêng.

- **Key canonical (MIN-141 đợt 3):** server đọc được cả key wire legacy
  trên và tên nghiệp vụ canonical liền không dấu (entities.md §9.1):
  `ten`↔`ho_ten`, `gioitinh`↔`gioi_tinh`, `ngaysinh`↔`ngay_sinh`,
  `ngaychet`↔`ngay_chet`, `sogiayto`↔`so_giay_to`, `ngaycap`↔`ngay_cap`,
  `noicap`↔`noi_cap`, `diachi`↔`dia_chi`, `loaigiayto`↔`loai_giay_to`,
  `loaidiachi`↔`loai_dia_chi`. Cùng trường ở cả hai spelling mà giá trị
  mâu thuẫn → `validation_error`. Wire emit giữ bộ legacy.
- **Suy ra trên case row:** `derive_person_fields` và `_resolve_derived_field`
  dùng input cũ của chính row trước ghi, input mới của payload. Incoming khác
  stored → giữ ý định sửa kể cả null; stored khác prev_derived → giữ bằng
  chứng xác nhận; còn lại derive theo input mới. Dòng mới như stored rỗng.
  Giữ heuristic echo hiện có: explicit bằng đúng giá trị derive chưa phân biệt
  được, không thêm flag. Context chết dùng ngày chết hoặc loại giấy/nhãn
  Nơi chết có nguồn; không derive CCCD/cơ quan người sống trong context chết.
  Thiếu ngày cấp không đoán cơ quan. Năm riêng chỉ parse quy ước khi tính toán.
- **Word/GET dùng rows B duy nhất:** mọi slot Người, cả owner/participant,
  đọc theo row_id và thứ tự case rows, kể cả null; không fallback master hoặc
  Stage JSON thiếu key. `loaicutru` chỉ derived cho consumer, không thêm wire.

### 4.2 `asset_row` — dòng Tài sản Stage

```yaml
asset_row:
  row_id: <uuid4>
  entity_id: <int | null>
  is_primary: <bool>                # chỉ shape v1 lịch sử; v2 cấm
  so_serial: <string>                # nguyên văn tùy nguồn, có thể rỗng,
                                     # có thể trùng — entities.md §2
                                     # (Owner 06/10/2026: không ép format)
  so_vao_so: <string | null>
  so_thua_dat: <string>             # BẮT BUỘC có nội dung khi ghi dòng (S5b)
  so_to_ban_do: <string>            # BẮT BUỘC có nội dung khi ghi dòng (S5b)
  dia_chi: <string | null>           # nullable: thiếu dữ kiện vẫn lưu
  loai_so: <string | null>
  hinh_thuc_su_dung: <string | null>
  thoi_han: <string | null>          # lẻ cấp tài sản — CHỈ còn nghĩa trên
                                     # emit/legacy (xem ghi chú dưới)
  nguon_goc: <string | null>
  ngay_cap: <YYYY-MM-DD | YYYY | null>  # nhận chỉ-năm như Người (S5c)
  co_quan_cap: <string | null>
  land_rows:
    - loai_dat: <string | null>
      dien_tich: <number | null>
      thoi_han: <string | null>
```

- Output (`workspace_get`/Stage result) luôn emit đủ field trên, kể cả
  `thoi_han` lẻ nullable, `land_rows` null/[]/hàng trống và mọi cụm đất;
  `dia_chi` nullable. `workspace_source_latest`/`workspace_duplicate` giữ
  nguyên field/cụm/null của nguồn, chỉ đổi `row_id`; không mở nhập mới và
  không phân bổ `thoi_han` lẻ xuống cụm.
- **Mức tối thiểu khi ghi (S5b/S5c, owner 23/10/2026):** dòng Tài sản chỉ
  bắt buộc `so_thua_dat` + `so_to_ban_do` có nội dung (rỗng/toàn khoảng
  trắng → `stage_validation_error{code:"required"}`). Các field chữ còn lại
  nhận `""`/khoảng trắng và chuẩn hóa null khi ghi, không lỗi. `so_serial`
  vẫn phải là chuỗi khi có mặt (S5a). `ngay_cap` nhận `YYYY-MM-DD` hoặc
  `YYYY`; ngày có nội dung sai lịch vẫn `invalid_date`. Không yêu cầu đủ
  tài sản/địa chỉ để Lưu hồ sơ.
- `land_rows` phân biệt null, [] và mảng có hàng trống; giữ thứ tự/vị trí.
- **`thoi_han` lẻ cấp tài sản (MIN-141):** phía input (payload
  `workspace_create`/`workspace_commit_stage`/`workspace_save_case`/`diagram_evaluate` nháp) KHÔNG
  còn bắt buộc — schema `asset_row_input`. Client mới không gửi key này;
  key vắng nghĩa là giữ giá trị hiện hành của **case row**, không master;
  key có giá trị/null ghi đúng ý định vào row, không phân bổ xuống cụm.
  emit (`workspace_get`/result.data.stage) server vẫn luôn trả key
  `thoi_han` (nullable) — schema `asset_row` — để đối chiếu lịch sử và báo
  `stage.orphan_thoi_han` khi giá trị lẻ không gắn cụm nào. Thời hạn mới
  chỉ thuộc `land_rows[].thoihan`; không tự đắp giá trị lẻ vào cụm.
- **Key cụm đất (MIN-141 đợt 2; nới S6 23/10/2026):** tên nghiệp vụ
  canonical mới là `loaidat` / `dientich` / `thoihan` (trùng cột bảng con
  `case_asset_land_rows` và tên placeholder Word `loaidat<M><N>`... —
  entities.md §9.2). Server đọc được cả bộ legacy
  `loai_dat`/`dien_tich`/`thoi_han` để UI hiện hành không hỏng; wire
  emit tiếp tục dùng bộ legacy (shape trên không đổi). Trong một phần
  tử, cặp cũ-mới của cùng trường mang giá trị **mâu thuẫn** → **không còn
  lỗi**: ghi theo key canonical mới và bỏ giá trị key cũ. `dientich`
  không parse được thành số hữu hạn (kể cả bool/kiểu lạ) → ghi `null`,
  giữ các trường còn lại của cụm. Không còn trần 20 cụm/tài sản trên đường
  Lưu; unknown key trong cụm vẫn bị chặn (S9).
  Vị trí cụm = index trong `land_rows` + 1 (cột `vitri`), kể cả dòng
  trống hoàn toàn — giữ nguyên vị trí trống.
- Storage B: mọi field §4.2 (trừ is_primary v1) ánh xạ cột cùng tên trên
  `case_asset_rows`; `entity_id` → property_id nullable. Đất thuộc row
  `case_asset_land_rows(case_asset_row_id,vitri,loaidat,dientich,thoihan)`,
  không PropertyLandRow/mirror JSON. land_rows_present phân biệt null và [].
- Serial lookup exact/no-op, binary case-sensitive, không trim/uppercase/
  gộp space; `"AB 001"` khác `"AB001"`, `"ab 001"`, `" AB 001 "`.
  Rỗng/toàn whitespace là thiếu neo → entity_id null, giữ nguyên chuỗi.
  Row cũ khớp neo identity giữ ID; row mới/đổi neo chọn ID nhỏ nhất hoặc tạo
  Property tối thiểu serial trong transaction. Quy tắc echo ID như Người.
  Cùng serial/identity khác thửa vẫn giữ nhiều row_id, nội dung và vị trí riêng.

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
    owner_row_id: <uuid4 | null>    # v2 inheritance: được absent/null khi
                                    # create nháp; non-null phải có trong
                                    # people; two_party cấm key (§13.6)
    people: [<person_row>]          # v2: ≥0; ho_ten có thể null; v1 lịch sử ≥1
                                    # entity_id: null hoặc gợi ý dương có kiểm neo
    assets: [<asset_row_v2>]        # v2: ≥0, ≤5; entity_id như trên;
                                    # v1 lịch sử ≥1 + is_primary
  diagram:
    state: <diagram_state>          # v2 OPTIONAL — absent thì server seed
                                    # theo domain; personId tham chiếu row_id
                                    # trong stage của payload này
```

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  backend_mode: real | mock
  created: <bool>                   # true = vừa tạo; false = idempotent
                                    # replay trả case đã có
  case: <case>                      # shape §4 — revision: 1
  stage: {people, assets}           # rows sau tạo; identity có thể null khi thiếu neo
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

- **Một transaction:** validate → tạo case + resolve identity + ghi case rows,
  đất/projection + Diagram/meta → revision=1, status=draft → commit duy nhất.
  Lỗi bất kỳ rollback cả identity mới/key/hash; field Stage trả
  `stage_validation_error`, Diagram sai trả mã tương ứng, không partial.
- **Owner khi tạo (S2 23/10/2026):** v1 lịch sử dùng node owner có
  personId; v2 dùng stage.owner_row_id trong people (§13.6), diagram
  optional khi create. **Create nháp và Lưu hồ sơ** đều được
  absent/null owner (chưa gán Chủ đất); owner **non-null** sai/ngoài Stage
  → `workspace_owner_required`; two_party vẫn cấm key. Chỉ định này không
  là chudat và không được thay bằng ownPositions/isLandOwner.
- **Validation theo ý định, không dùng chung một guard:** `workspace_create`
  (partial-create vòng 2) cho ≥0 Người, ≥0 Tài sản, `ho_ten=null`, owner
  `null`. `workspace_save_case` (S1/S2 23/10/2026) cũng cho ≥0 Người/≥0
  Tài sản và owner null; mức tối thiểu mỗi dòng là họ tên (Người) và số
  thửa + số tờ (Tài sản). `workspace_commit_stage` và `convert_type` cho
  consumer khác vẫn strict: tên non-empty, owner inheritance hợp lệ.
  Không biến incomplete thành invalid và không thêm cờ partial.
- Địa chỉ tài sản nullable ở mọi đường ghi (thiếu dữ kiện vẫn lưu; chuỗi
  rỗng ghi null); không còn rule "địa chỉ không rỗng". `is_primary` chỉ là
  rule v1 lịch sử. Không tạo tên/identity giả.
- Thiếu số giấy hoặc serial rỗng/toàn whitespace vẫn lưu row với entity_id null;
  ô chỉ số/ngày mà chưa có tên lưu `ho_ten=null`, không lưu chuỗi rỗng.
- Idempotency: cùng key **và hash payload/ý định draft** → workspace hiện tại,
  created=false, không ghi/tăng revision; khác hash → idempotency_conflict.
- Case mới status=draft, revision=1; không locked. Lưu thẳng Done dùng save_case.
- Meta allowlist theo schema hiện hành: case_type/document_type và các trường
  Hồ sơ §6.1/§13.6/§13.17; key ngoài allowlist → validation_error.
- `workspace_create` vẫn là API tạo draft cho consumer khác; renderer Soạn
  hồ sơ không gọi để lưu nháp. **Lưu hồ sơ** mới hoặc đã có đều dùng
  `workspace_save_case`. Không dùng legacy case_create cho tab này.

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
- `case_id` không tồn tại/case_type chưa hỗ trợ →
  `case_not_found`/`case_type_unsupported`; Done không chặn intake.
  Engine OCR thiếu → `engine_not_installed` (reuse envelope §8).
  Chế độ nháp (`case_id` absent) bỏ qua các kiểm tra case — suggestion
  không gắn hồ sơ nào.

## 6. `notary.workspace_commit_stage` — payload + result

API này giữ nguyên trên server/adapter/REST cho consumer khác. Renderer Soạn
hồ sơ không gọi, không có nút Cập nhật/Lưu nháp hoặc commit ngầm trước Lưu hồ sơ.

```yaml
payload:
  case_id: <int>
  base_revision: <int ≥ 1>
  case:                             # (đợt 3) OPTIONAL — metadata hồ sơ
                                    # ghi cùng Stage trong một transaction
    ngay_lap_ho_so: <YYYY-MM-DD | null>    # null = ghi null; absent = giữ nguyên
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
    people: [<person_row>]         # rows sau commit; entity_id vẫn null nếu thiếu neo
    assets: [<asset_row>]
  diagram:
    state: <diagram_state>         # state sau prune — §6.1
    render_model: <render_model>   # non-null — kết quả re-evaluate
                                   # trong cùng transaction — §6.1
```

### 6.1 Semantics

- **Atomic diff rows:** validate → resolve identity + diff case rows/đất/
  projection → prune/re-evaluate Diagram đã lưu → revision+1 → commit duy nhất.
  Full payload là ý định tập dòng, không delete/insert lại toàn tập hoặc upsert
  master. Chỉ UPDATE field/vitri đổi, INSERT row mới, DELETE row bị bỏ và
  phụ thuộc của chính case. Đất diff parent row_id+vitri, giữ hàng trống.
  `commit_stage` trên draft giữ draft, trên Done giữ done; Word đọc snapshot DB mới.
- **Strict của API:** `commit_stage` và `convert_type` giữ validation
  strict hiện hành cho consumer khác — tên non-empty, owner inheritance hợp
  lệ trong Stage. `workspace_save_case` từ 23/10/2026 đi theo đường Soạn
  hồ sơ điền dần: không bắt ≥1 Người/≥1 Tài sản và không bắt Chủ đất
  (S1/S2); mức tối thiểu field dùng chung là họ tên + số thửa/số tờ. Nháp
  thiếu dữ liệu mở/sửa/Lưu được; không có cờ partial hay API bypass.
- **`payload.case` (đợt 3):** metadata hồ sơ ghi cùng transaction —
  validate fail hoặc stage fail → không cái nào ghi. `case_type`/
  `document_type` gửi kèm phải khớp giá trị đã lưu (immutable qua
  commit — **trừ đường chuyển loại đã duyệt**, §13.18) — khác →
  `validation_error`. `nguoi_nhan_uy_quyen_id` phải
  tồn tại trong `customers`; kèm `nguoi_nhan_uy_quyen` lệch tên master →
  `validation_error`. Meta có cột lưu đúng cột case làm SOT; bảy scalar
  metadata Upload còn lại trong JSON case (§13.19). Null ghi null,
  absent giữ giá trị cũ; không fallback meta master hoặc nhân đôi SOT.
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
  invalid_format, duplicate_row_id`; hai row_id cùng entity không là lỗi.
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
  → `workspace_conflict`; Done vẫn cập nhật được; `case_id`
  không tồn tại → `case_not_found`. Status được giữ nguyên.
- Dùng cho ô meta trong dialog Xuất Word (Nơi niêm yết):
  `saveCaseMeta` → `workspace_update` vẫn là ngoại lệ ghi meta trực tiếp.
  Không ghi kèm Stage/Diagram/ngữ cảnh Word đang sửa và không đánh dấu chúng
  đã lưu; không tạo nguồn lưu meta thứ hai ngoài case DB.
- Ghi cột metadata làm SOT, không lặp vào JSON; giữ các scalar khác và
  Stage/Diagram. Không đường legacy fallback/migrate-on-read cho case B.
  Result giữ đầy đủ case shape; null ghi null, không `new or old`.

## 7. `notary.diagram_evaluate` + `notary.diagram_save`

### 7.1 `diagram_state` — wire ENGINE V2 (không legacy JS)

```yaml
diagram_state:
  version: 2                        # literal — khác → diagram_invalid_state
  nodes:
    - id: <string non-empty>        # slot id — vd father, mother,
                                    #   spouse, owner, child_1, sibling_1
      personId: <uuid4 | null>      # row_id dòng Người trong Stage cùng
                                    # ngữ cảnh (§13.2); null = slot trống
      parentSlotIds: [<node.id>]    # 0..2 — tham chiếu slot cha/mẹ
      spouseSlotId: <node.id | null>
      isLandOwner: <bool>
      willReceive: <bool>
      hidden: <bool>
      deleted: <bool>
```

- `personId` PHẢI là `row_id` tồn tại trong Stage dùng cho thao tác: Stage DB
  với get/diagram_save, Stage cùng payload với create/save_case/evaluate nháp.
  Vi phạm → `failed{code:diagram_reference_outside_stage}` (refs đã lưu bị
  xóa trong save_case được prune theo §13.19). `workspace_get` không được emit
  tham chiếu ngoài Stage DB.
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

- Read-only theo DB: evaluate không ghi state/Stage/revision; áp dụng
  cho cả draft và done, không có khóa nghiệp vụ.
- `personId` ngoài Stage → `diagram_reference_outside_stage` — Stage của
  case khi `case_id` present; Stage trong payload khi chế độ nháp.
  State sai cấu trúc → `diagram_invalid_state`.
- Chế độ nháp (`case_id` absent): `stage` trong payload thay thế Stage
  DB; `diagram` được đánh giá trên đó; `evaluated_revision: null`;
  `personId` trỏ `row_id` của stage payload (§2.1). Lỗi field Stage không
  chặn evaluate (S19, owner 23/10/2026): engine vẫn chạy theo cấu trúc sơ
  đồ và `render_model.status` trả `incomplete` kèm warning
  `stage.incomplete_fields`; không còn `stage_validation_error` chỉ vì
  field tùy chọn. Lỗi cấu trúc wire/reference/domain vẫn raise như §7.
- Renderer Soạn hồ sơ dùng chế độ nháp với Stage + Diagram đang sửa, cả
  khi hồ sơ đã có `case_id`; không gửi `case_id` trong request evaluate này.
  Nhãn/cảnh báo/tính thử không được đọc baseline đã lưu thay cho dữ liệu
  đang hiển thị. Evaluate không lưu nháp hay thay revision.

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
  commit. State sai CẤU TRÚC → không persist (`diagram_invalid_state`).
  Lỗi engine chỉ vì THIẾU DỮ KIỆN (`missing_land_owner`,
  `invalid_death_date`) không chặn ghi: `render_model.status=incomplete`
  giữ nguyên `errors` (S3, owner 23/10/2026); đường evaluate vẫn trả
  nguyên trạng thái chưa tính được của engine.
- Chỉ lưu Diagram trên rows đã commit, không Stage/meta và không đổi status.
  Nút **Lưu hồ sơ** dùng workspace_save_case, không gọi đường này.
  Incomplete hợp lệ giữ warnings/requiredSlots/Pool; lỗi cấu trúc reject và rollback.
- base_revision khác server → workspace_conflict; Done vẫn lưu Diagram được.

## 8. `notary.word_export_options` + `notary.word_export_batch`

### 8.1 `notary.word_export_options`

```yaml
payload:
  case_id: <int | null>                  # null = hồ sơ chưa lưu (phần W)
  template_dir: <file_ref is_dir:true>   # optional (NAIA-8) — folder mode
```

`case_id` null/absent chỉ quét nguồn mẫu (readiness mức mẫu); lượt xuất mới
là lúc renderer tự tạo + lưu hồ sơ. `original_source_id` (nhánh hợp đồng
gốc) đòi hồ sơ đã lưu.

```yaml
result.data:
  schema_version: "notary.case-drafting.v1"
  documents:
    - document_key: <snake_case | basename .docx>
      display_name: <string>
      ready: <bool>
      block_reason: <null | code>   # chỉ khi ready:false
```

`block_reason` code hóa (v1 — data-code dạng `word.*`, §2.5). Owner
23/10/2026 (phần W): **thiếu dữ kiện không còn là lý do chặn** — Người/Tài
sản/sơ đồ Hai bên/chủ đất/chủ đất đã mất/người nhận thiếu chỉ làm
placeholder tương ứng rỗng và được ghi vào `missing` của kết quả từng file.
Chỉ còn gate **kỹ thuật**:

```
word.too_many_assets        # > 5 tài sản
word.too_many_people        # Stage: > 20 người (inheritance) / > 30 (two_party)
word.too_many_signers       # > 20 người ký (inheritance)
word.template_missing       # văn bản chưa có template
```

`word.no_people`, `word.no_diagram`, `word.no_assets`, `word.no_landowner`,
`word.no_deceased_landowner`, `word.no_receiver` đã nghỉ hưu (reserved —
không producer nào trả nữa).

Mapping từ validation thật của `word_engine`: chỉ vượt trần số lượng mới
chặn (`too_many_assets`, `too_many_people`, `too_many_signers`); `two_party`
không áp điều kiện chủ đất/người nhận và dùng trần 30 người. `[Người N]`
lấy theo Stage đã lưu, không phải node Diagram. Các code này là kiểm tra
**kỹ thuật** xuất file — không phải kiểm định pháp lý (§13.5).

Readiness theo **dữ liệu mẫu thực sự cần** (owner 15/10/2026) chỉ còn dùng
để quyết định ghi chú `missing` nào vào kết quả file (nhóm `Chủ đất
sống`/`Chủ đất chết`/`Người nhận`, ghế `Bên A`/`Bên B` nhận diện theo đúng
registry key engine sinh sau chuẩn hoá không dấu, không theo chuỗi con).
Nhóm thiếu luôn render rỗng. Token không hỗ trợ/không xác minh, slot chưa
giải quyết và thiếu người được ủy quyền mà mẫu cần **không còn làm file
lỗi**: DOCX vẫn ra với chỗ trống và kết quả liệt kê trong `missing`.
Mẫu hiện diện nhưng không mở/parse được: readiness trả đúng data-code
per-file mà batch sẽ trả (`word.render_failed`, `file_locked`,
`file_not_found`) thay vì fallback gate cũ.

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

- `case_id` là hồ sơ **đã lưu**: renderer tự lưu bản đang sửa (hoặc tạo mới)
  trong cùng hành động xuất trước khi gọi batch; lỗi lưu thật dừng hành
  động, không xuất bản cũ thay thế (phần W, owner 23/10/2026).
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
- Validate trước file đầu tiên: các lỗi trên + destination → failed, không
  tạo file nào. Không chặn theo status done. File mẫu biến mất sau quét →
  per-file failed{code:word.template_missing} (§8.4).

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
      missing: [<string>]                # dữ kiện còn thiếu của file đã xuất
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
- `missing` là **kết quả**, không phải lỗi: file vẫn `saved` với chỗ đó để
  trống. Ví dụ: `tài sản`, `chủ đất`, `chủ đất đã mất`, `người nhận`,
  `người được ủy quyền <slot>`, `1 trường chưa hỗ trợ: [token]`. Producer
  luôn emit (có thể `[]`); consumer coi vắng mặt = không có ghi chú.
- Per-file `error.code` là **data-code** `<ns>.<snake>` (§2.5) và chỉ dành
  cho lỗi kỹ thuật thật. Từ phần W (23/10/2026), thiếu dữ kiện/token chưa hỗ
  trợ **không** còn sinh `word.unresolved_placeholders` hay
  `word.missing_authorized_person` per-file; các mã đó giữ reserved.
  `word.missing_authorized_person` và `word.unresolved_placeholders` không
  còn producer. Registry còn dùng: `word.template_missing`,
  `word.too_many_assets`, `word.too_many_people`, `word.too_many_signers`,
  `word_path_traversal`, `word.invalid_filename`, `word.render_failed` và
  mã envelope reuse (`file_locked`, `file_not_found`). Producer được thêm
  data-code mới.

## 9. Bảng error code

Namespace `notary.*` (snake_case không chấm):

| Code | Khi nào | `details` |
|---|---|---|
| `case_not_found` | `case_id` không tồn tại; `workspace_duplicate` với `source_case_id` không tồn tại (khi chưa replay) | `{source_case_id}` cho duplicate |
| `case_type_unsupported` | `case_type` engine chưa hỗ trợ trên command ghi/evaluate/export; `workspace_source_latest` chọn case Done có loại ngoài `inheritance`/`two_party` (không lùi sang case khác); word_export chấp nhận `inheritance` + `two_party` (NAIA-8) | `{case_type}` |
| `idempotency_conflict` | Key tạo đã dùng với creation hash khác (command/ý định draft hoặc done cũng thuộc hash); duplicate dùng cùng key cho source khác hoặc command khác | — |
| `workspace_conflict` | `base_revision` khác revision server (cả nhỏ hơn lẫn lớn hơn) | `{server_revision}` |
| `workspace_owner_required` | Owner inheritance **non-null** sai/ngoài Stage ở create/save_case/diagram_evaluate; chuyển vào inheritance không chọn owner hợp lệ. Chưa gán owner (absent/null) hợp lệ trên create/save_case/evaluate; commit/convert vẫn bắt buộc | — |
| `stage_validation_error` | field Stage vi phạm | `{field_errors:[{row_id,field,code,message}]}` |
| `workspace_storage_error` | Ràng buộc integrity khi ghi không ánh xạ được sang ô user thấy (row_id/vitri/entity_id là wire nội bộ). Dữ liệu chưa đổi | `{constraint, retryable:false}` — không field_errors, không row giả |
| `intake_unsupported_source` | `kind` ngoài enum | `{source_id, kind}` |
| `intake_source_too_large` | file > 20MB / PDF > 50 trang | `{source_id, limit}` |
| `intake_too_many_sources` | sources > 8 | `{count, limit}` |
| `intake_text_too_long` | text > 100.000 ký tự | `{source_id, length, limit}` |
| `diagram_reference_outside_stage` | `personId` không thuộc Stage của thao tác (DB hoặc cùng payload); prune refs pending khi save_case theo §13.19 | `{personId}` |
| `diagram_invalid_state` | state sai cấu trúc; engine reject vì lỗi quan hệ/wire. Trên đường Lưu, engine `invalid` chỉ vì `missing_land_owner`/`invalid_death_date` → render_model `incomplete`, không lỗi | `{errors:[{code,message,...}]}` |
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
      `workspace_conflict` với case đã có; reject loại chưa hỗ trợ,
      không chặn Done hoặc dùng workspace_locked.
- [ ] Reject personId ngoài Stage (cùng payload khi create/save_case/evaluate
      nháp); diagram_reference_outside_stage. Wire hiện hành Diagram v3;
      shape version 2 phần nền chỉ là lịch sử.
- [ ] Enforce giới hạn intake §5.2; `partial` kèm breakdown source_id.
- [ ] Destination FileRef: `is_dir:true`, absolute, `machine_local`,
      không UNC, folder tồn tại — kiểm trước khi tạo file đầu tiên.
- [ ] Naming `*_HS-<case_id>[_n].docx`; reservation nội batch; không
      ghi đè; output nằm trong destination.
- [ ] `word_export_batch`: tất cả lỗi → `word_batch_failed`; cancel →
      file chưa bắt đầu `status:skipped` + vào `breakdown.skipped`,
      giữ file đã lưu; `breakdown` luôn đủ ba list.
- [ ] `workspace_create` (partial-create vòng 2): cho ≥0 Người/Tài sản,
      `ho_ten=null`, owner inheritance absent/null; vẫn kiểm kiểu/ngày/
      giới hạn; owner non-null sai → workspace_owner_required.
      `workspace_save_case` từ 23/10/2026 cho ≥0 Người/≥0 Tài sản và owner
      null; tối thiểu họ tên + số thửa/số tờ. Địa chỉ tài sản nullable.
      Key+hash replay không ghi, hash khác idempotency_conflict.
      Case mới revision=1; workspace_save_case ghi nguyên tử và done.
- [ ] `workspace_source_latest`: payload `{}` strict, chỉ đọc case Done
      lưu gần nhất (updated_at DESC, id DESC, null-last); trả UUID v4 mới,
      owner remap, identity giữ; không trả meta/Diagram, không ghi DB.
      Không có Done → kết quả rỗng thành công, không lỗi.
- [ ] `workspace_duplicate`: copy toàn bộ nội dung đã lưu trong một
      transaction; UUID/land PK/participant PK mới, identity giữ, owner/
      participant/Diagram personId/records.row_id remap; key+hash
      `{command,intent,source_case_id}` replay trả workspace hiện tại
      created=false; lỗi rollback toàn bộ, nguồn không đổi.
- [ ] `intake_analyze`/`diagram_evaluate`: chấp nhận `case_id` absent
      (nháp); reject `case_id:null` và `case_id` present-not-int ≥1
      bằng `validation_error`; evaluate nháp yêu cầu `stage` payload và
      trả `evaluated_revision:null`.
- [ ] Mock backend trả `backend_mode:"mock"` trong `workspace_get` và
      `workspace_create`.

Consumer (Electron main/renderer) PHẢI:

- [ ] `row_id`/`source_id` UUID v4 do client sinh; giữ ổn định qua
      lưu/reload; gửi `base_revision` trên mọi write case đã có.
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

- Examples: `contracts/notary-case-drafting/examples/{valid,invalid}/`
  (và corpus v2 trong `examples/draft-v2/`).
- Validator: `contracts/notary-case-drafting/validate_examples.py`
  (stdlib + jsonschema). Gate: mọi `*.valid.json` pass hết rule; mọi
  `*.invalid.json` bị reject với `expected_error` khớp bảng §9.
- Schema cho vòng 2: `workspace-source-latest.schema.json`,
  `workspace-duplicate.schema.json`; `draft-v2.schema.json` tách
  person/stage **output**, **create partial** và **strict input**;
  `workspace.schema.json` có definition workspace result v2 dùng chung.
  Schema v1 vẫn chỉ mô tả corpus lịch sử, không là quyền nới case hiện hành.
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
| v2 Storage B vòng 1 (đang triển khai) | 22/10/2026 | Cutover tiền MVP không tương thích client cũ: rows case-owned là SOT, identity nullable khi thiếu neo, draft/done không khóa; thêm workspace_save_case nguyên tử (§13.19). Giữ validation create vòng 1; nới tên/tập rỗng/owner null thuộc vòng 2. Không proof BUILT. |
| v2 Storage B vòng 2 (ĐÃ TRIỂN KHAI 22/10/2026) | 22/10/2026 | Thêm `workspace_source_latest` (§13.20: chọn case Done theo updated_at microsecond/id, Stage UUID mới + identity hint) và `workspace_duplicate` (§13.21: copy toàn bộ đã lưu, hash command+intent+source, draft/rev1 là chốt kỹ thuật chờ owner). Nới `workspace_create` cho nháp ít dữ liệu; save_case/commit/convert giữ strict (save_case nới tiếp 23/10/2026 — §13.19). Proof: `test_issue13_source_latest.py`, `test_issue13_workspace_duplicate.py`, `test_issue13_partial_draft.py`, `test_issue13_storage_b_proof.py`. |
| v2 gate inventory S1–S7/S19 (owner) | 23/10/2026 | Đường Lưu phía server đi theo triết lý điền dần: save_case không bắt ≥1 Người/≥1 Tài sản (S1) và không bắt Chủ đất (S2); engine `invalid` chỉ vì thiếu dữ kiện (`missing_land_owner`/`invalid_death_date`) → `incomplete` trên đường Lưu (S3); Người chỉ bắt buộc họ tên, chuỗi rỗng → null (S4/S4d); Tài sản bắt buộc số thửa + số tờ, `ngay_cap` nhận chỉ-năm (S5b/S5c); cụm đất bỏ trần 20, alias mâu thuẫn ghi theo key mới, diện tích không parse → null (S6); trần 5 tài sản (S7); evaluate nháp không chặn field tùy chọn (S19). §4.1/§4.2/§4.3/§7.4/§7.5/§13.2/§13.3/§13.6/§13.16/§13.19. |
| v2 G4 single-save (owner) | 23/10/2026 | Bỏ Cập nhật/Lưu nháp ở renderer; Stage/Pool/Diagram dùng chung bản đang sửa, baseline chỉ là lần lưu gần nhất; chỉ Lưu hồ sơ persist qua workspace_save_case. Không lưu ngầm khi rời/đóng, giữ canLeave/window-close và revision/conflict. API commit/create/diagram_save vẫn hỗ trợ consumer khác; Word saveCaseMeta giữ workspace_update. §13.2/§13.17–§13.19. |

---

# PHẦN II — `notary.case-drafting.v2` (MIN-125, APPROVED 27/09/2026)

> §13 là contract v2 hiện hành. **Storage B đang triển khai vòng 1**, chưa
> chứng minh runtime hoàn tất. V1/ánh xạ persisted cũ là lịch sử, không còn
> nghĩa vụ client compatibility hoặc migration dữ liệu test. Cutover renderer
> và backend cùng bản; giữ literal v2, Diagram v3, envelope desktopcommand.v1.
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
`desktopcommand.v1`; danh mục command theo §1 và §13.18–13.19; đổi shape
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
| node cờ thừa kế | `isLandOwner`, `willReceive` bool | `ownPositions`, `receivePositions` ⊆ {1..5} |
| `diagram` trong `workspace_create` | bắt buộc, phải có owner node | **optional** — server tự seed |
| Pool của hồ sơ mới | đòi owner/primary trước khi gán | Đọc Stage đang sửa, gán ngay trước lần Lưu hồ sơ đầu (§13.2; thay Q1 lịch sử) |

### 13.2 Vòng đời: một bản đang sửa / baseline đã lưu / Lưu hồ sơ / bỏ nháp

Stage, Pool và Diagram ở renderer dùng **một trạng thái soạn hiện tại**:
Stage Người/Tài sản/meta, Diagram và `docx_import` đang sửa trong phiên.
Thay đổi hiển thị ngay giữa các vùng, không có nhánh hiển thị draft/committed
theo việc hồ sơ đã có ID hay chưa.

- **Bản đang sửa** sống trong bộ nhớ phiên; gõ ô, thêm/xóa dòng, reorder,
  gán/gỡ node, sửa dấu Chủ/Nhận hoặc ngữ cảnh Word không tự ghi DB.
- **Baseline `committed`** chỉ là snapshot **đã lưu gần nhất** của chính hồ
  sơ (draft hoặc done), nạp từ GET/result ghi thành công. Dùng cho dirty,
  đối chiếu/revision và ý định wire/identity; **không** là nguồn hiển thị
  Pool/nhãn Diagram hoặc tập Người có thể gán. Baseline của nháp mới rỗng;
  case draft trong DB vẫn mở lại được, khác buffer chưa lưu.
- **Không có Cập nhật/Lưu nháp** trong renderer. Không gọi `workspace_create`,
  `workspace_commit_stage` hoặc `diagram_save` để persist nội dung soạn,
  kể cả khi điều hướng, đổi loại hoặc chuẩn bị xuất Word. Server/adapter/REST
  vẫn giữ các API này cho consumer khác. Ngoại lệ Word `saveCaseMeta` →
  `workspace_update` chỉ ghi meta theo §6.2.
- **Lưu hồ sơ** dùng `workspace_save_case`: flush cả ô đang focus, đồng bộ
  mặc định vị trí chưa touched (§13.4), chụp Stage/meta/Diagram/`docx_import`
  hiện tại trong một payload; một transaction → done. Hồ sơ mới dùng
  `draftId` của phiên làm `idempotency_key`, không cần tạo draft trung gian;
  revision=1. Case đã có gửi `base_revision`, revision+1 kể cả Done sạch;
  không đòi diagramDirty. Lỗi giữ nguyên bản đang sửa/dirty.
- **Pool** = `stage.people` **đang sửa** trừ những `personId` đang gán
  trên node active của Diagram **đang sửa**. Tập Người có thể gán, tên,
  ngày sinh/mất và nhãn node đều từ Stage hiện tại. Thêm Người xuất hiện
  ngay; sửa Người cập nhật Pool/node ngay; node trỏ dòng đã xóa không được
  mượn dữ kiện baseline. Hồ sơ mới cũng gán được trước lần lưu đầu.
- **Xóa row trong bản đang sửa:** dòng Người biến mất khỏi Stage/Pool ngay;
  client đồng thời xóa `personId` ấy khỏi mọi node Diagram, kể cả node owner,
  và xóa `owner_row_id` nếu đang trỏ dòng bị xóa. Không lấy tên/nhãn từ
  baseline để hiển thị lại Người đã xóa. Xóa Tài sản cập nhật Stage ngay;
  dấu chọn vị trí pending được normalize/prune khi Lưu hồ sơ theo Stage
  cùng payload (§13.19); vị trí vẫn theo số, không theo row_id.
- **Rời/đóng hồ sơ thực sự** (mở hồ sơ khác, tạo nháp khác hoặc đóng cửa
  sổ): giữ dirty + guard `canLeave` và window-close. Hủy rời → giữ bản
  đang sửa; xác nhận bỏ → bỏ buffer, **không command ghi**, không tự lưu
  nháp. Mở lại đọc bản đã lưu gần nhất qua `workspace_get`, revision DB
  không đổi. Chuyển sidebar/module/tab chỉ tạm ẩn view theo chính sách cache
  buffer trong RAM (`_bmad-output/specs/ui/README.md`), không tự bỏ bản đang
  sửa hoặc coi như đã lưu; quay lại trong cùng phiên vẫn có buffer. Cache
  ấy không bền vững khi đóng app hay mở hồ sơ khác. Không persist PII trong
  localStorage/log/diagnostics để khôi phục. Nút `Hủy thay đổi` Stage và
  cơ chế khôi phục riêng đã bỏ; ví dụ §13.12.2.
- **API partial-create vẫn hỗ trợ:** consumer khác có thể gọi
  `workspace_create` với tập rỗng/tên null/owner null, status draft/rev1.
  Đây không phải một thao tác lưu của renderer Soạn hồ sơ. Mở draft ấy
  dùng chung bản đang sửa như mọi case khác; Lưu hồ sơ chỉ đòi mức tối
  thiểu (họ tên mỗi dòng Người, số thửa + số tờ mỗi dòng Tài sản) — không
  còn ≥1 Người/≥1 Tài sản hay Chủ đất bắt buộc (S1/S2 23/10/2026).
  Không có cờ partial cho save_case/commit/convert; `diagram_save` riêng
  không chuyển Done.
- **Tính thử:** renderer dùng `diagram_evaluate` chế độ nháp (`case_id`
  absent) với Stage + Diagram đang sửa, kể cả case đã có ID (§7.4).
  Payload Stage là `stage_v2`, có `owner_row_id` với inheritance; không
  persist, không tăng revision, `evaluated_revision:null`. Thiếu dữ kiện
  vẫn theo incomplete của engine, không tự chặn thành invalid.

### 13.3 Tài sản: tối đa 5, vị trí = thứ tự mảng (Q3, Q4; S7 23/10/2026)

```yaml
asset_row_v2:               # giống §4.2, TRỪ is_primary (bị loại)
  row_id: <uuid4>           # ổn định — KHÔNG phải vị trí
  entity_id: <int | null>
  so_serial: <string>   # nguyên văn tùy nguồn — entities.md §2
  ...                       # mọi field còn lại giữ nguyên §4.2; `thoi_han`
                            # lẻ OPTIONAL input (absent giữ case row), không master
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
- **Tối đa 5 asset** trong `stage.assets` của payload
  `workspace_create`/`workspace_commit_stage`/`workspace_save_case`/`diagram_evaluate` nháp
  (owner 23/10/2026 — trần 5 thống nhất mọi tầng; client + Word cập nhật ở
  lát riêng); phần tử thứ 6 trở lên → `stage_validation_error` với
  `field_errors[].code:"asset_limit"` (gắn `row_id` của dòng thừa).
- **Reorder đổi nghĩa vị trí, không đổi identity:** kéo asset từ vị trí
  1 xuống 2 nghĩa là *dữ liệu tại vị trí 1 đổi*; `row_id` của asset đi
  theo dòng. Dấu chọn `ownPositions`/`receivePositions` (§13.4) **không
  tự chuyển theo `row_id`** — số vị trí giữ nguyên, nghĩa là "người đó
  vẫn sở hữu/nhận *tài sản đang ở vị trí đó*". Đây là hành vi có chủ
  đích của MIN-125 — xem ví dụ §13.12.1.
- **Xóa asset:** xóa ở bản đang sửa = pending (§13.2). Khi Lưu hồ sơ thành công,
  vị trí đánh lại dày (dense): asset đứng sau dịch lên; mọi dấu chọn
  giữ nguyên số vị trí (không bám `row_id` cũ); dấu chọn tới vị trí
  `> len(assets)` mới bị server prune trong cùng transaction. UI PHẢI
  cảnh báo khi xóa asset làm trôi nghĩa vị trí (ghi chú cho P6 —
  không phải field wire).
- Không migrate/đọc legacy test data trong cutover B; mô tả overflow/mirror
  lịch sử ở §13.8 không còn yêu cầu runtime.
- **Cụm đất (S6 23/10/2026):** đường Lưu không còn trần 20 cụm/tài sản.
  Alias cũ-mới mâu thuẫn ghi theo key canonical mới; `dientich` không parse
  được thành số → null (không chặn). Unknown key vẫn bị chặn.
  Lưu case_asset_land_rows theo parent row_id + vitri, không master/mirror
  JSON. Null → land_rows_present=false, không con; [] → true, không con;
  mảng → true, giữ cả hàng trống. Diff từng vị trí, không clear collection.
- **Word đọc case rows duy nhất**, không assets[] persisted JSON hay tổng
  loại_dat/diện_tích master fallback khi mảng trống. Có thể dựng view RAM cho
  consumer; không persist thêm Stage/assets.
- Thời hạn thuộc từng cụm. thoi_han lẻ hiện hành chỉ giữ để đối chiếu/cảnh báo
  stage.orphan_thoi_han, không tự đắp xuống đất.
- **`result.data.warnings`** (optional, array `{code, message}`) là mở
  rộng v2 cho cảnh báo cấp-stage (không thuộc `diagram.warnings`).

### 13.4 Node v3 — dấu chọn tài sản độc lập (Q4, Q5, Q10)

```yaml
diagram_state v3 (domain inheritance):
  version: 3                        # literal — khác → diagram_invalid_state
  domain: "inheritance"             # BẮT BUỘC trong state (§13.5)
  nodes:
    - id: <string non-empty>        # slot id — giữ namespace v1
      personId: <uuid4 | null>      # row_id Người trong Stage cùng ngữ cảnh (§13.2)
      parentSlotIds: [<node.id>]    # giữ nguyên 0..2
      spouseSlotId: <node.id | null>
      ownPositions: [<int 1..5>]    # vị trí tài sản người này SỞ HỮU
      receivePositions: [<int 1..5>]# vị trí tài sản người này ĐƯỢC NHẬN
      hidden: <bool>
      deleted: <bool>
```

- `isLandOwner`/`willReceive` **cấm** trên wire v2 →
  `diagram_invalid_state` (`invalid_node` — trường lạ trên node).
- `ownPositions`/`receivePositions`: array không trùng phần tử ⊆
  {1..5}; phần tử ngoài khoảng / trùng / không phải int →
  `diagram_invalid_state{errors:[{code:"invalid_position"}]}`.
  `null`/thiếu → `diagram_invalid_state` (`invalid_node`).
- Hai mảng **độc lập**: một người vừa sở hữu vừa nhận, vừa chọn nhiều
  vị trí, đều hợp lệ. **Nhiều node cùng chọn một vị trí** = đồng sở
  hữu / nhận chung — hợp lệ (Q10).
- Dấu chọn tới vị trí `> len(stage.assets)` hiện tại (asset chưa tạo
  hoặc vừa bị prune): cho phép tồn tại trong bản đang sửa; server prune
  tại save_case (hoặc API commit cho consumer khác), cùng cơ chế prune
  `personId` §13.19 — trả `diagram.warnings` data-code
  `diagram.selection_pruned`; UI được disable chip tài sản chưa tồn tại.
  Không reject cả lần ghi chỉ vì dấu chọn pending này.
- **Mặc định khi gán (Q5):** node `owner` → `ownPositions`, slot thừa
  kế khác → `receivePositions`: mảng rỗng được điền tất cả vị trí đang có
  ({1..len(assets)}). Khi thêm/gỡ tài sản và khi Lưu hồ sơ, client
  đồng bộ đầy đủ tập vị trí hiện có nếu user chưa tự chỉnh chip cho đúng
  node + loại Chủ/Nhận trong phiên; lựa chọn tay, kể cả tắt hết, không bị
  tự ghi đè. Riêng owner đang rỗng không được tự điền nếu node khác đã có
  `ownPositions` không rỗng. Đây là tiện ích **client-side**, wire luôn
  mang mảng explicit; dấu đã chỉnh chỉ ở state phiên, reset khi mở hồ sơ/
  phiên mới. *Hiệu chỉnh từ vòng lặp sửa lỗi E2E 23/10 — phương án B.*
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
  (absent — `validation_error` nếu có); assets ≤5 (§13.3).
- **Không engine:** `diagram_evaluate` trên `two_party` trả `succeeded`
  với `render_model{engineVersion:2, status:"unsupported",
  allocations:{}, breakdowns:[], requiredSlots:[],
  unresolvedEstates:[], conservation:{allocated:"0",unresolved:"0",
  total:"0"}, warnings:[{code:"diagram.two_party_unsupported",...}]}` —
  sơ đồ hai bên **không bao giờ** đi vào engine thừa kế (rào kiến
  trúc: `InheritanceCase` hiện chỉ chở inheritance; persist hai bên cần
  backend riêng ở P5).
- `workspace_save_case` (renderer), `diagram_save`/`workspace_commit_stage`
  (consumer khác) persist + structural validate như thường. `workspace_get` trả domain
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
  stage:                            # stage_v2 create (vòng 2)
    owner_row_id: <uuid4 | null>    # OPTIONAL/absent/null khi create nháp;
                                    # non-null phải là row_id trong
                                    # stage.people; CẤM khi two_party
    people: [<person_row>]          # ≥0 — ho_ten có thể null (nháp ít dữ liệu)
    assets: [<asset_row_v2>]        # ≥0, ≤5 — §13.3
  diagram:                          # OPTIONAL (đổi từ v1 bắt buộc)
    state: <diagram_state v3>       # domain phải khớp case.case_type
```

- **Vòng 2 — create nháp ít dữ liệu (ĐÃ TRIỂN KHAI 22/10/2026; proof:
  `test_issue13_partial_draft.py`):** create cho
  ≥0 Người/≥0 Tài sản, `ho_ten=null`, owner inheritance absent/null; kiểu/
  ngày/enum/giới hạn vẫn strict. Owner **non-null** sai/ngoài Stage →
  `workspace_owner_required`; two_party vẫn cấm key. Thiếu số giấy hoặc
  serial rỗng/toàn whitespace không chặn ghi row: entity_id=null, không
  identity giả. Dòng không tên lưu `ho_ten=null`, không chuỗi rỗng. Create
  không nhận `is_primary`; địa chỉ tài sản nullable.
- `commit_stage` **không** dùng nới `ho_ten=null`: vẫn cần tên non-empty
  và owner inheritance hợp lệ. `workspace_save_case` từ 23/10/2026 đi theo
  mức tối thiểu của Soạn hồ sơ (S1/S2): ≥0 Người/≥0 Tài sản, owner null,
  mỗi dòng Người cần họ tên, mỗi dòng Tài sản cần số thửa + số tờ.
  Không có API bypass.
- nguoi_chet_id chỉ projection identity của owner (two_party không neo people[0]
  vào người chết); tai_san_id chỉ projection identity asset vị trí 1. Hai
  projection nullable khi row thiếu neo, không nguồn dữ kiện Word/hiển thị.
- owner_row_id absent/null khi create = chưa gán owner (hợp lệ); chỉ
  **non-null** sai/ngoài Stage mới → workspace_owner_required. Đổi owner khi
  save_case/commit sync node owner/projection cùng transaction, không sửa identity.
- `diagram` present: `state.domain` phải khớp `case.case_type` → sai →
  `diagram_domain_mismatch`; với inheritance, node `owner` (nếu có
  `personId`) phải bằng `owner_row_id` → sai → `diagram_owner_mismatch`.
- `diagram` absent: server seed state mặc định — inheritance **có owner**:
  node `owner` gán `owner_row_id` + bộ slot rỗng chuẩn như hiện trạng;
  inheritance **owner null**: không seed node owner giả và không có dấu
  Chủ — `nodes=[]`; two_party: 30 ô trống. `render_model` của create-result
  = null/hay incomplete theo engine khi chưa evaluate được (giữ §4.3);
  không giả complete.
- Result inheritance luôn emit owner_row_id (UUID hoặc `null` cho nháp chưa
  gán); two_party absent. Không yêu cầu đọc/nâng pointer hồ sơ test legacy.
  Owner là pointer row, không đồng nhất chudat; save_case dùng owner của
  Stage cùng payload.

### 13.7 Lịch sử bảng chuyển trường v1 → v2 (không phải yêu cầu migration B)

Chỉ lưu dấu vết contract trước cutover. B tạo DB test mới, không backfill,
migrate-on-read hoặc dual-read/write; bảng dưới không áp làm requirement runtime.

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
| data-codes | + `stage.legacy_asset_overflow`, `stage.legacy_primary_ambiguous`, `diagram.two_party_unsupported`, `diagram.selection_pruned`, `stage.incomplete_fields` (warning evaluate nháp khi Stage còn lỗi field tùy chọn, S19) | §13.3/13.4/13.5/13.8/§7.4 |
| `person_row`, `personId`, `row_id`, revision, `idempotency_key` | giữ nguyên | — |

### 13.8 Lịch sử tương thích persisted cũ (không áp cutover Storage B)

Các hành vi trong bảng là lịch sử, không yêu cầu runtime B thực hiện.
Không giữ fallback master, pointer-only hoặc nghĩa locked; GET B không ghi DB.

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
| `diagram_domain_mismatch` | `state.domain` khác `case.case_type` (create/save/evaluate); duplicate khi state nguồn không khớp domain nguồn | `{expected, got}` |
| `diagram_owner_mismatch` | `owner` node `personId` ≠ `stage.owner_row_id` (create/save); duplicate khi mirror nguồn không khớp | `{owner_row_id, node_personId}` |
| `idempotency_conflict` | Key create/save_case mới hoặc duplicate đã dùng nhưng hash khác. Duplicate hash gồm `{command,intent,source_case_id}` — cùng key khác source/command | — |
| `case_type_unsupported` | `workspace_source_latest` chọn case Done mới nhất có `case_type` ngoài `inheritance`/`two_party`; duplicate nguồn loại chưa hỗ trợ | `{case_type}` |

Field-error code mới trong `stage_validation_error.details.field_errors[]`:

| Code | Nghĩa |
|---|---|
| `asset_limit` | `stage.assets` > 5 (v2, S7 23/10/2026) |
| `people_limit` | `stage.people` > 30 với `case_type:two_party` |

`entity_id` không còn mã field-error: hint lệch/không tồn tại/không khớp neo
bị bỏ và resolve lại theo neo chuẩn (§4.1 mục 5, owner 23/10/2026). Ràng buộc
integrity không ánh xạ được sang ô user thấy → `workspace_storage_error`
(`details.constraint`, `retryable:false`), không giả danh field và không gắn
row giả.

Engine/detail codes mới (`details.errors[]`, `render_model.errors[]`):
`invalid_position` (phần tử ngoài {1..5} / `id` ngoài `p1..p30` / sai
thứ tự), `missing_position` (state two_party thiếu slot canonical).
Data-codes hiện hành: diagram.two_party_unsupported, diagram.selection_pruned.
stage.legacy_asset_overflow/stage.legacy_primary_ambiguous chỉ là lịch sử §13.8.

`primary_count` (v1) không dùng trong v2 — asset không `is_primary`.
`workspace_owner_required` áp khi create inheritance có owner **non-null**
sai/ngoài Stage và khi chuyển loại vào inheritance thiếu owner; create nháp
với owner absent/null được phép. Không dùng để thêm điều kiện hoàn tất pháp
lý cho Done. Duplicate giữ owner pointer của nguồn (kể cả null) và làm lại
mirror; lỗi mirror là `diagram_owner_mismatch`, không bịa owner.
Không có workspace_locked hiện hành.

### 13.10 Ranh giới Word — giới hạn + mapping theo Stage (NAIA-8)

- Giới hạn giữ nguyên: `MAX_WORD_ASSETS = 5`; `person`/`signer` > 20 →
  `word.too_many_people`/`word.too_many_signers`; `[Tài sản N - field]`
  đọc tài sản theo **thứ tự** 1..5.
- **`[Người N]` = thứ tự danh sách Stage** (NAIA-8 — quyết định Leader
  trên NAIA-8): gồm cả người chưa có node; đảo thứ tự/xóa node Diagram
  **không** đổi số Người. Vai trò (Bên A/B, chủ đất, người nhận) lấy từ
  dữ liệu nghiệp vụ đã lưu, không suy từ vị trí node. Mọi alias
  placeholder cũ (`ngườ`, `ngườ ký`, `ngườ nhận`, …) giữ nguyên.
- `stage.assets` ≤ 5 (S7 23/10/2026) nằm đúng giới hạn 5 của Word; vị trí
  1..5 trên Stage tương ứng `[Tài sản 1..5 - *]` — **không đổi nghĩa
  placeholder**. Client/UI cập nhật số cụm hiển thị ở lát riêng.
- `two_party` (NAIA-8 — đã hỗ trợ): `word_export:true`,
  `word_export_*` chạy bình thường. `[Người N - *]` = toàn bộ dòng
  Stage theo thứ tự; `[Bên A N - *]`/`[Bên B N - *]` = người gán vào
  slot `p1..p15`/`p16..p30` (ô trống → render rỗng, không dồn);
  `[Bên A - Họ tên]`/`[Bên B - Họ tên]`/`[Tên bên A]`/`[Tên bên B]`
  = danh sách họ tên từng bên; placeholder riêng thừa kế (chủ đất,
  người nhận, phụ lục di sản) render rỗng trên văn bản hai bên.
- Không đưa `two_party` vào engine thừa kế (§13.5 — `diagram_evaluate`
  vẫn `unsupported`, không chạy allocation).
- Mọi slot/nhóm và binding lấy dữ kiện từ view B trong RAM: ordered case rows,
  key row_id, kể cả null. Không Customer/Property/participant.customer fallback,
  không tự thêm owner hoặc lấy Stage JSON cũ. Giữ luật template readiness §8.1,
  không đồng nhất done với đủ trường/slot pháp lý.
- Xuất Word chỉ dùng dữ kiện **đã lưu trong DB**, không dùng buffer đang sửa.
  Có thay đổi Stage/meta/Diagram hoặc ngữ cảnh Word pending thì renderer yêu
  cầu **Lưu hồ sơ** trước, không commit hoặc lưu ngầm để xuất. Ngoại lệ
  `saveCaseMeta` trong dialog chỉ ghi meta qua `workspace_update` (§6.2).

### 13.11 Revision / retry / late-response — giữ nguyên, nêu lại cho rõ

- Write case đã có bắt buộc base_revision; lệch → workspace_conflict với
  server_revision, không ghi/tăng lần hai, không exactly-once response cache.
  Sau timeout giữ payload/revision cũ; reload/đối chiếu trước quyết định ghi
  bằng revision mới, không tự retry bằng revision mới.
- workspace_create/save_case mới: sinh key một lần; retry đúng key **và
  payload đã chụp**, không ô đã gõ thêm. Hash canonical JSON sau alias/shape
  normalization, trước resolve: sort object keys, giữ array order/null/serial/
  precision ngày và tên command/ý định draft hoặc done. Cùng hash trả workspace
  hiện tại created=false, không hồi sinh payload tạo; khác → idempotency_conflict.
- **Nguồn cho nháp (`workspace_source_latest`):** renderer khóa sửa/lưu
  nháp đến khi response xong, bỏ response của phiên cũ, lỗi hiện rõ và
  không coi nguồn rỗng là thành công khi request lỗi. Không tự ghi DB và
  không tự refresh nguồn khi người dùng đang sửa. Nguồn rỗng (không Done)
  là kết quả thành công với Stage rỗng; retry do người dùng chủ động.
- **Nhân bản (`workspace_duplicate`):** sinh `idempotency_key` **một lần
  cho một ý định** và giữ `{source_case_id,key}` khi timeout/lỗi hạ tầng
  để retry đúng payload. Click Nhân bản mới sau success sinh key mới.
  Hash chỉ gồm command+intent+source_case_id, **không** hash snapshot/
  revision/timestamp nguồn: nguồn đổi/đổi revision/bị xóa sau lần tạo vẫn
  replay đúng bản sao đã có (created=false), không tạo clone mới và không
  trả conflict. Khác source/command cùng key → idempotency_conflict.
  Không tự retry bằng key mới; không clear pending key trước khi biết
  success; late response khác phiên bị discard.
- Khi save đang chạy khóa editor và mọi mutation Stage/meta/Diagram/đổi case/
  đổi loại/intake accept/reorder; lỗi giữ buffer+dirty. Chỉ nhận success sau
  commit, hydrate đầy đủ rồi clear dirty; không ghi đè edit mới bằng response cũ.
- Late response: client tương quan `job_id`/`command_id` + `case_id` của
  phiên hiện tại; result/job trễ từ phiên trước / case đã đổi / draft
  đã bỏ nháp PHẢI bị discard — không apply vào buffer (`_bmad-output/specs/ui/README.md`, giữ
  nguyên).

### 13.12 Ví dụ trước/sau (JSON rút gọn)

#### 13.12.1 Reorder tài sản — dấu chọn giữ theo vị trí (Q4)

```jsonc
// TRƯỚC (baseline đã lưu; bản đang sửa ban đầu giống baseline)
"assets": [
  {"row_id": "aaaa-…-1", "so_serial": "DD100001"},   // vị trí 1
  {"row_id": "bbbb-…-2", "so_serial": "EE200002"},   // vị trí 2
  {"row_id": "cccc-…-3", "so_serial": "FF300003"}    // vị trí 3
]
// node: {"id":"owner","personId":"…p1","ownPositions":[1,2],"receivePositions":[]}

// SAU khi user kéo aaaa xuống cuối (hiển thị ngay), rồi Lưu hồ sơ thành công
"assets": [
  {"row_id": "bbbb-…-2", "so_serial": "EE200002"},   // vị trí 1 (primary mới)
  {"row_id": "cccc-…-3", "so_serial": "FF300003"},   // vị trí 2
  {"row_id": "aaaa-…-1", "so_serial": "DD100001"}    // vị trí 3
]
// node owner vẫn "ownPositions":[1,2] → nghĩa mới: sở hữu EE200002 + FF300003.
// row_id aaaa KHÔNG được "kéo dấu" theo — không remap số sang ID cũ.
```

#### 13.12.2 Xóa asset rồi bỏ nháp — bản đang sửa vs baseline đã lưu (Q2, §13.2)

```jsonc
// baseline đã lưu: assets [A1,B2,C3]; node X.receivePositions=[2]
// đang sửa: user xóa B2 → Stage/Pool dùng assets [A1,C3] ngay;
//           node X giữ [2] trong buffer (chưa server prune).
// xác nhận bỏ nháp khi rời/đóng hồ sơ thực sự (không phải tạm chuyển sidebar),
// KHÔNG command ghi; mở lại đọc baseline →
//        assets [A1,B2,C3], node X [2] — như chưa xóa.
//        revision không đổi, không write nào lên wire (đọc vẫn workspace_get).
// (Nếu Lưu hồ sơ bằng workspace_save_case thay vì bỏ nháp: persist [A1,C3] → vị trí dồn:
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

- **Q1 lịch sử** — owner trong Stage phá vòng phụ thuộc Pool; B hiện dùng
  nullable projection identity, không giữ giả định FK NOT NULL của Q1 cũ.
- **Q4** — dấu chọn theo vị trí, không bám `row_id` khi reorder/xóa.
- **Q6** — `willReceive:true` legacy → nhận tất cả vị trí hiện có.
- **Q7** — `p1..p30` cố định, bên suy ra từ số.
- **Q11** — `document_type` `two_party` = `{chuyen_nhuong, tang_cho,
  cho_thue, dat_coc}`.

C1–C4 là record thiết kế cũ; resolve entity_id hiện theo §4.1/§4.2/§13.19,
không dùng C3 để cho client ép master ID. Quy tắc Word hiện hành ở §13.10.

### 13.14 Checklist conformance bổ sung (áp dụng cho producer v2)

Producer v2 PHẢI (thêm vào §10):

- [ ] Emit `schema_version:"notary.case-drafting.v2"`;
      `diagram_state.version:3` + `domain` bắt buộc.
- [ ] Không emit `is_primary`, `isLandOwner`, `willReceive`; stage
      inheritance mang `owner_row_id` (result) — absent với `two_party`.
- [ ] `stage.assets` ≤5 trên mọi payload; `two_party` people ≤30;
      canonical 30 node `p1..p30` cho domain `two_party`.
- [ ] `workspace_create` v2: cho phép `diagram` absent; seed owner theo
      `owner_row_id`; `tai_san_id` = asset vị trí 1.
- [ ] Server prune `personId` bị xóa khỏi Stage và dấu chọn vị trí
      `> len(assets)` trong transaction commit/save. Client đã gỡ
      `personId`/owner ngay khi xóa Người; dấu vị trí pending theo §13.2.
- [ ] `diagram_evaluate` two_party → `unsupported` render_model, không
      chạy engine thừa kế; `word_export_*` trên two_party được hỗ trợ
      (NAIA-8) — readiness qua `block_reason` §8.1.
- [ ] Rows/đất case-owned là SOT; không upsert/fallback master hoặc persisted
      Stage JSON; cùng identity nhiều row không mất dữ kiện.
- [ ] Tách validation theo ý định: `workspace_create` partial cho ≥0/tên
      null/owner null; `workspace_save_case` cho ≥0/owner null với mức tối
      thiểu họ tên + số thửa/số tờ; commit + convert giữ strict. Không
      biến incomplete thành invalid hoặc ngược lại.
- [ ] `workspace_source_latest`: chỉ đọc case Done lưu gần nhất, không ghi
      DB; UUID v4 mới, owner remap, entity_id giữ nguyên; không trả
      case/meta/Diagram/docx_import; lấy nguồn lặp lại được phép sinh UUID
      khác.
- [ ] `workspace_duplicate`: copy nội dung **đã lưu** (không buffer), draft/
      rev1 cho lần tạo đầu, key/hash `{command,intent,source_case_id}`;
      remap mọi row ref/participant/Diagram personId/records.row_id, giữ
      slot ID/vị trí/identity/provenance; replay trả workspace hiện tại
      created=false; lỗi rollback toàn bộ.
- [ ] Save case ghi Stage/meta/Diagram/status/revision/key/hash nguyên tử,
      lỗi rollback tất cả. Nhãn Nháp/Đã lưu theo status, không thay dirty
      và không đổi cách tính báo cáo.
- [ ] Chỉ draft|done, không locked field; API commit_stage giữ status và
      thay snapshot DB; save_case draft→done, case mới rev1/cũ +1.

Consumer v2 PHẢI (thêm vào §10):

- [ ] Stage/Pool/Diagram dùng chung bản đang sửa cho cả case mới/đã có;
      baseline committed chỉ là lần lưu gần nhất, không nguồn hiển thị/gán.
      Chỉ Lưu hồ sơ gửi save_case; không create/commit/diagram_save ngầm.
      Bỏ nháp không ghi, giữ canLeave/window-close; mở lại đọc bản đã lưu.
      Xóa Người gỡ personId/owner ngay; normalize/prune dấu vị trí pending
      trong transaction lưu, không mượn dữ kiện baseline.
- [ ] Map chip `[1][2][3]` ↔ positions; không theo `row_id`; disable
      chip vị trí chưa có asset.
- [ ] Reject state v2/v3 sai domain, `is_primary`/`isLandOwner` dư —
      coi như `validation_error`/`diagram_invalid_state`.

### 13.15 Examples & validator draft

- Fixtures v2 trước cutover: `examples/draft-v2/`, flag
  `fixture_context.draft_v2:true`; tên thư mục/flag là lịch sử, không nhãn
  chất lượng hiện tại. Save-case dùng examples/valid và examples/invalid.
- draft-v2.schema.json định nghĩa person/stage output, stage create
  partial, stage strict, diagram_state_v3, create/commit;
  workspace-save-case.schema.json định nghĩa command đó;
  workspace-source-latest.schema.json và workspace-duplicate.schema.json
  định nghĩa hai command vòng 2; workspace.schema.json có workspace
  result v2 dùng chung. Schema draft-07 và validator kiểm wire, normative
  text xác định transaction/resolve B.
  Fixtures v1 chỉ đối chiếu shape lịch sử, không quyền khóa case hiện hành.

### 13.16 Quy tắc Stage hiện hành sau gộp MIN-141

**Nguồn:** Owner xác nhận 03/10/2026 rằng 14 commit worker là cập nhật đúng,
yêu cầu đưa vào nhánh chính và đồng bộ tài liệu/code. Mục này thay các quy
tắc MIN-140 ngày 29/09/2026 bị mâu thuẫn; không đổi envelope/schema version.

- Người: họ tên non-empty ở save/commit; `workspace_create` nháp vòng 2
  cho `ho_ten=null`/absent (không chuỗi rỗng). Giới tính Nam/Nữ/null; ngày
  sinh/chết/cấp nhận YYYY-MM-DD, YYYY hoặc null; số giấy tờ/nơi cấp/địa chỉ/
  quê quán/loại giấy tờ/nhãn địa chỉ nhận chuỗi hoặc null (chuỗi rỗng ghi
  null). Số giấy được trùng, match tên+số theo §4.1.
- Tài sản: serial là chuỗi nguyên văn tùy nguồn (Owner 06/10/2026 bỏ
  bắt buộc `[A-Z]{2}\d{6,8}` ở mọi tầng), **địa chỉ nullable**;
  số thửa/số tờ bắt buộc có nội dung, các trường còn lại nullable. Cụm đất
  có thể null/[]; không còn trần 20 cụm, alias mâu thuẫn ghi theo key mới,
  diện tích không parse được → null (S6).
- Case B giữ serial nguyên văn tại row; identity lookup exact, thiếu neo null.
- `thoi_han` lẻ bỏ khỏi form và payload renderer; dữ liệu lịch sử vẫn giữ
  để đối chiếu/cảnh báo. Không tự gán vào thời hạn từng cụm.
- Suy trường Người từ case row, không master/Stage JSON fallback; entities §8–§9.
- Giữ nháp khi chuyển tab/lỗi; renderer kiểm khi Lưu hồ sơ. Giữ revision,
  owner khi owner được chỉ định/strict, giới hạn/row/FK/date; bỏ guard trùng
  shared identity. Done sửa được. Vòng 2: create nháp cho tập rỗng/tên null/
  owner null; save_case từ 23/10 cho tập rỗng/owner null (tối thiểu họ tên +
  số thửa/tờ), commit vẫn strict như trên.

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
- Create/commit/save_case/get và result có optional `docx_import`, schema tại
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
  binding, không gắn sang row khác. Ở renderer, gỡ nguồn/detach hoặc xác nhận/
  sửa binding chỉ đổi `docx_import` đang sửa và đánh dirty; **chỉ Lưu hồ sơ**
  gửi `workspace_save_case` để persist, không commit trực tiếp trong dialog.
  Bỏ nháp không ghi context pending; mở lại đọc context đã lưu.
  Client kiểm giới hạn 8 nguồn trước khi thêm row. Gỡ nguồn gửi context còn
  lại khi Lưu hồ sơ (kể cả sources rỗng); không đọc file của nguồn được gỡ. Xóa cụm đất
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
  Renderer tải proposals/readiness ban đầu từ hồ sơ đã lưu sạch. Thay lựa
  chọn binding chỉ đổi selection cục bộ, cho phép sửa lại lựa chọn pending;
  không tự tạo template hash, suy lại slot/giá trị hoặc giả readiness đã lưu.
  Stage/Diagram/revision đổi thì cache proposals hết hiệu lực. Có pending
  context thì hành động xuất tự lưu (gồm provenance/vị trí) rồi nạp lại
  readiness/proposals trên bản vừa lưu trước khi render; lưu/lỗi cấu trúc
  thật dừng hành động, không export bản DB cũ (phần W, 23/10/2026).
- Người N theo Stage; Bên A/B theo ô Diagram; tài sản N theo thứ tự Stage.
  Binding dùng row_id+field, slot phải khớp lại lúc xuất. N/seat đổi, source/
  derivative hash đổi, row mất hoặc slot trống → `word.original_mapping_invalid`,
  không thay ngầm. Span unsupported/chồng nhau từ chối khi lưu binding.
  Binding mới phải khớp catalog và giá trị bản Stage/sơ đồ vừa được dựng
  trong transaction; sai slot hủy cả lần lưu. Đổi thứ tự của binding cũ
  vẫn cần xác nhận lại trước khi xuất. Nhận giá trị ngày từ evidence dùng
  quy tắc chuẩn hóa ngày hiện có; mơ hồ đất kiểm từng ô, không cả field.
  Với B, validate bindings sau flush rows bằng materialized view case-owned
  của chính transaction; save_case cũng nhận docx_import. Absent giữ provenance
  đã lưu, không serialize Stage/assets vào JSON làm SOT; lỗi binding rollback
  cả rows, identity mới, meta, Diagram/status/revision/key/hash.
  Ngày sửa sai chặn Đưa vào Stage cho tới khi sửa đúng, không dùng giá trị cũ.
- Kho nguồn kiểm hash byte `extraction.json` qua `extraction.sha256`; dấu kiểm
  thiếu/hỏng hoặc nội dung đổi phải nhập và kiểm tra lại. Không tự tin dữ liệu cũ.
  Nguồn/mẫu chưa dùng vẫn giữ local; chưa duyệt thời hạn giữ hay dọn tự động.
  Sao lưu/dọn thủ công phải giữ tất cả nguồn/mẫu còn được hồ sơ tham chiếu.
- **Nhân bản (§13.21):** copy nguyên `docx_import` đã lưu — source_id/
  candidate_id/occurrence_id/field_key/slot/template hash/label giữ nguyên;
  chỉ `records[].row_id` remap theo map Người/Tài sản của bản sao.
  `records[].land_rows` là số dòng **nguồn Word**, giữ nguyên, không map
  theo PK đất. `bindings` không có row_id trực tiếp nên gián tiếp qua
  candidate → record. `slot_for` trước/sau remap phải cùng slot; binding
  đã stale vẫn stale, không tự xác nhận/chữa và không prune im lặng.
  Kiểm mọi ref có map trước khi validate; thiếu map/source bytes → lỗi rõ,
  rollback, không bỏ `docx_import`.
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
- **Guard:** base_revision lệch → workspace_conflict; draft và Done đều đổi
  loại được, giữ nguyên status. Một transaction, lỗi/hủy rollback toàn bộ,
  revision không đổi, bản cũ còn dùng được. Write thành công đóng stamp
  microsecond như mọi writer (§2.2/§13.20); không nới guard
  `confirm_diagram_reset`/`owner_row_id` của đường chuyển loại.
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
Stage/meta/ngữ cảnh Word chưa lưu phải **Lưu hồ sơ** trước; UI không tự lưu/bỏ nháp để đổi loại.
Nháp Diagram chỉ bị reset sau thành công; hủy dialog/Escape/nền trước Áp dụng
không gửi command. Sau Áp dụng dialog chờ kết quả, không thêm nút hủy in-flight.
Command cancel được chấp nhận trước giao dịch thì không ghi; giao dịch ngắn
và publish succeeded được phân xử cùng khóa job, cancel đến sau thành công
bị từ chối terminal. Các command khác không thay semantics hủy.

### 13.19 Storage B, draft/done và workspace_save_case — cutover tiền MVP

**Vòng 2 issue 13 ĐÃ TRIỂN KHAI 22/10/2026.** Vòng 1 (rows
case-owned, draft/done, save_case) có code; vòng 2 thêm source_latest/
duplicate/partial-create (proof: `test_issue13_source_latest.py`,
`test_issue13_workspace_duplicate.py`, `test_issue13_partial_draft.py`,
`test_issue13_storage_b_proof.py`). Thay dữ liệu test bằng DB
test mới; không migration bảo toàn, backfill, migrate-on-read, dual-read/write
hoặc tương thích locked. Không xóa raw/provenance/evidence/tài liệu repo.
Đây là breaking cutover phối hợp app/backend, giữ literal wire v2 và Diagram v3.

**Ownership/SOT:** case_person_rows và case_asset_rows chứa dữ kiện đầy đủ,
ordered theo vitri, row_id UUID ổn định. entity_id nullable chỉ identity dùng
chung Customer/Property; neo resolve theo §4.1–§4.2 trong transaction ghi:
renderer chỉ tại **Lưu hồ sơ**; API create/commit của consumer khác vẫn hỗ trợ.
Không cập nhật master theo sửa case, không cascade đổi Hồ sơ khác,
không UNIQUE neo/merge. Đất case_asset_land_rows thuộc row tài sản, không master.
Participant/link là projection theo row_id, identity FK nullable; không dedupe
hai row theo shared identity, giữ participant PK/vai trò tay/ghi chú còn tồn tại.
Mỗi lần ghi Stage/Sơ đồ (commit_stage, save_case, diagram_save, convert_type sang
inheritance), `vai_tro`/`hang_thua_ke` của dòng suy-từ-sơ-đồ được TÍNH LẠI theo
Diagram đã lưu gần nhất, kể cả dòng đã tồn tại. Hai nguồn vai trò phân biệt
bằng giá trị đang lưu — không thêm cột nguồn:
- suy từ sơ đồ = `Vợ/Chồng`, `Cha`, `Mẹ`, `Cha_vc`, `Me_vc`, `Con_dau_re`,
  `Con`, `Anh/Chị/Em`, `Cháu`, `Khac` (bộ giá trị hữu hạn của
  `_project_role_nodes`; `Owner` không thành dòng participant);
- gán tay = mọi giá trị khác (vd `Người được ủy quyền`) → projection giữ
  nguyên `vai_tro` qua các lần ghi, chỉ tính lại `hang_thua_ke` từ vai trò đó.
Một dòng chỉ mang một `vai_tro`: vai trò gán tay thắng cột này khi cùng người
vừa có vị trí quan hệ. Dòng không còn node (gỡ/ẩn/xóa hoặc trùng owner) bị
xóa như trước. Neo cặp vợ–chồng theo nhánh chưa có trường chuẩn (#45 TC3 mở).
Nguoi_chet_id/tai_san_id chỉ projection owner/asset1, không fallback dữ kiện.

Case metadata có cột là SOT; JSON case chỉ bảy scalar
tenvanban/nhomhopdong/loaivanbannhandien/socongchung/ngaycongchung/congchungvien/thuky.
case_state_json nội bộ schemaVersion=4 chỉ owner_row_id (inheritance), case
scalar, diagram {state:v3,render_model,warnings?,updatedAt}, docx_import.
Không Stage/assets/engineInput/assignments persisted; engine_state_json không
đọc/ghi (null). View RAM ghép rows/meta/Diagram dùng chung cho Word/binding.
chudat derived active ownPositions + tên rows + asset count, không input tay/
Property/slot owner. Null meta ghi null; scalar absent giữ giá trị trước.

**Validation theo ý định (vòng 2):** `workspace_create` là **partial-create**
— cho `people`/`assets` ≥0, `ho_ten=null`, owner inheritance absent/null;
giữ kiểu ngày/Boolean, row ownership/FK, giới hạn 5 tài sản/30 Người
two_party (không còn trần 20 cụm — S6), và owner **non-null** sai →
`workspace_owner_required`. `workspace_save_case` từ 23/10/2026 đi theo
đường điền dần (S1/S2): ≥0 Người/≥0 Tài sản, owner null, tối thiểu họ tên
+ số thửa/số tờ; `commit_stage` và convert_type vẫn **strict** (tên
non-empty, owner inheritance hợp lệ). Địa chỉ tài sản nullable ở mọi đường
(thiếu dữ kiện vẫn lưu, chuỗi rỗng ghi null). Row thiếu số giấy/serial
rỗng hoặc toàn whitespace vẫn lưu với `entity_id=null`; dòng chỉ số/ngày
lưu `ho_ten=null`, không chuỗi giả. `entity_id` là wire echo/gợi ý nội bộ:
hint lệch/không tồn tại/không khớp neo bị bỏ và resolve lại theo neo chuẩn,
không chặn Lưu (§4.1 mục 5). Nháp thiếu dữ liệu mở/sửa được
và **Lưu hồ sơ** được ở mức tối thiểu (S1/S2); API commit của consumer
khác vẫn có ngưỡng strict riêng; không có cờ partial và không biến
incomplete thành invalid.

**Payload `notary.workspace_save_case`:**

```yaml
# Mới: case_id ABSENT, không phải null
idempotency_key: <uuid4>
case: <meta hiện có; case_type/document_type bắt buộc hợp lệ>
stage: <stage_v2; mức tối thiểu S1/S2 — 0 Người/Tài sản, owner null được>
diagram: {state: <v3, domain khớp case_type>} # bắt buộc
# docx_import optional theo §13.17

# Đã có: cấm idempotency_key
case_id: <int >= 1>
base_revision: <int >= 1>
case: <meta đầy đủ tại thời điểm chụp; không đổi loại>
stage: <stage_v2>
diagram: {state: <v3, domain khớp case_type>}
# docx_import absent giữ provenance đã lưu
```
Đây là đường persist nội dung soạn duy nhất của renderer, không gọi create/
commit trước. Case mới dùng `draftId` ổn định của phiên làm idempotency_key;
retry giữ đúng key + snapshot payload (§13.11). `stageForWire` giữ nguyên
`entity_id` server trả (echo/gợi ý); server tự bỏ hint khi lệch/không khớp
neo theo §4.1 mục 5 — client không phải lọc. Baseline đã lưu chỉ hỗ trợ
phân biệt row mới/cũ, không thay Stage hiện tại.


Case mới cấm base_revision; case cũ cấm key; null/Boolean/sai kiểu ID reject.
Không nhận status/locked/render_model từ client; không chudat nhập tay.
Meta allowlist/alias như hiện có; null ghi null, scalar absent giữ cũ.
result.kind=workspace_save_case; data = workspace_get v2 đầy đủ từ rows vừa
commit + created:boolean, case.status=done. Case mới revision=1; cũ N+1,
kể cả re-save Done sạch. Không yêu cầu diagramDirty/sáu trường/đủ mọi slot.

**Một transaction, một commit:** validate wire/meta/Stage → chiếm SQLite write
reservation BEGIN IMMEDIATE trên session sạch trước load revision/resolve →
check revision/key/hash/type → tạo case nếu mới → resolve/diff rows/đất/meta/
provenance, flush → normalize/check/prune Diagram theo Stage **cùng payload**
→ evaluate → diff projections/validate bindings → done/revision/updated_at →
commit → trả workspace đầy đủ. Helper không commit lồng; CAS UPDATE case cũ
theo base_revision và kiểm rowcount, không điều kiện status=draft.

Prune refs tới row của case đã lưu nhưng bị xóa trong payload; UUID chưa từng
thuộc bản cũ/payload là diagram_reference_outside_stage, không sanitize.
Prune positions > asset count với diagram.selection_pruned, không remap khi
reorder. Owner mirror mâu thuẫn → diagram_owner_mismatch. Inheritance evaluate
bằng rows mới; two_party trả unsupported_render_model, không engine thừa kế.
Incomplete hợp lệ giữ warning/requiredSlots/Pool và vẫn done; invalid reject.
Bất kỳ lỗi sau flush rollback cả case/identity mới/rows/đất/projections/JSON/
status/revision/key/hash. Không publish success trước commit.

**Errors:** validation_error (shape/meta/type/date ngoài Stage/key cấm),
stage_validation_error (field_errors row_id/field/code/message/index như hiện có),
case_not_found/case_type_unsupported, workspace_conflict {server_revision},
diagram_domain_mismatch/diagram_owner_mismatch/diagram_reference_outside_stage,
diagram_invalid_state {errors}, idempotency_conflict và lỗi binding/Word gốc
hiện có. Không partial write. SQLite busy/file lock là engine_unavailable
retryable=true, không workspace_locked và không tự retry bằng revision mới.

**Lifecycle/replay:** key+hash theo §13.11; replay mới trả workspace hiện tại
created=false không ghi/revision bump, hash khác lỗi. Case cũ retry revision
cũ sau commit → conflict, không double-write/journal exactly-once.
API `workspace_create` tạo draft; `workspace_commit_stage` giữ status draft/
done và thay snapshot DB, nhưng renderer không gọi hai API để lưu nội dung soạn.
diagram_save/update_meta/convert_type giữ status. Chỉ save_case chuyển
draft→done; không unlock→draft. Route /cases/{cid}/lock và /unlock là tombstone
HTTP 410 {code:"endpoint_deprecated",message:"Dùng Lưu hồ sơ; Hồ sơ không còn khóa"},
không query/mutate/commit DB, không redirect hoặc giả save thiếu payload.

**Client:** Stage/Pool/Diagram cùng bản đang sửa; baseline committed chỉ là lần
lưu gần nhất. Không nút Cập nhật/Lưu nháp, không lưu ngầm khi rời/đóng/chuyển
loại/xuất Word; giữ canLeave/window-close và base_revision/conflict. Ngoại lệ
Word saveCaseMeta → workspace_update chỉ meta, không persist context pending.
Lưu hồ sơ flush ô focus, đồng bộ mặc định chưa touched (§13.4), giữ snapshot
request khi retry, khóa mutation in-flight; lỗi giữ dirty/nháp, thay/dọn lỗi
theo lần ghi gần nhất và khi sửa dữ liệu liên quan. Success hydrate workspace rồi clear
dirty. Discard late response khác job/command/case/phiên. Nhãn trạng thái
nghiệp vụ: `draft` → **Nháp**, `done` → **Đã lưu**, hiển thị trong danh sách
và text định danh hồ sơ đã có ID; không thêm pill Nháp riêng, không đồng
nhất nhãn với chấm dirty. Nháp mới chưa có ID giữ header chọn loại.
Không tự apply/hủy modal đất đang mở: **B6 pending**, không claim vòng 2
hoàn tất.
Vòng 2 có nguồn latest-done và nhân bản (§13.20/§13.21). Vẫn ngoài vòng 2:
copy/paste Excel, cách tính/bộ lọc báo cáo, UX rời/đóng/khôi phục, xóa Done,
#42; giữ delete draft-only, Done sửa được không tự cấp quyền xóa Done.
Không đóng toàn #13 hoặc mở gate mẫu #41 bằng commit contract này.

### 13.20 `notary.workspace_source_latest` — đọc nguồn Done mới nhất (vòng 2)

**Trạng thái:** ĐÃ TRIỂN KHAI 22/10/2026 (proof: `test_issue13_source_latest.py`,
`test_issue13_storage_b_proof.py`). Read-only trên
DB case: lấy **toàn bộ Người + toàn bộ Tài sản/cụm đất của đúng một Hồ sơ
`done`** làm nguồn cho nháp mới. Không tạo/nhân bản case, không lấy buffer
editor của nguồn, không đọc/lưu file DOCX như một phần của Stage nguồn.

```yaml
payload: {}                         # bắt buộc object rỗng — mọi key khác
                                    # (case_id/base_revision/idempotency_key/
                                    # filter…) → validation_error
```

```yaml
result:
  kind: workspace_source_latest
  data:
    schema_version: notary.case-drafting.v2
    backend_mode: real | mock
    source_case_id: <int >= 1 | null>
    source_status: done | null
    stage:                          # đúng field/type/thứ tự Stage output
      owner_row_id: <uuid4 | null>  # chỉ inheritance và chỉ khi có nguồn
      people: [<person_row output>] # ho_ten có thể null
      assets: [<asset_row_v2 output>]
  evidence: []
  warnings: []
  source_files: []
```

**Chọn nguồn (một read transaction/snapshot):**

```sql
SELECT ... FROM inheritance_cases
WHERE trang_thai = 'done'
ORDER BY (updated_at IS NULL) ASC, updated_at DESC, id DESC
LIMIT 1;
```

- `updated_at` là mốc lưu kỹ thuật, **không** phải ngày giấy/ngày lập/độ đầy
  đủ/identity. Bằng timestamp tuyệt đối → `id` case lớn hơn thắng.
- `updated_at=null` (seed/ngoài luồng) xếp **sau** mọi timestamp có giá trị
  (null-last), rồi `id DESC`; đọc không backfill/không ghi.
- Chọn trên **toàn hệ thống**, không lọc theo loại việc/neo Người/Tài sản.
  Case được chọn có tập rỗng → trả rỗng của **case đó**, không lùi sang case
  khác. Loại nguồn ngoài `inheritance`/`two_party` → `case_type_unsupported`
  với `details.case_type`, không lẳng lặng đổi case.
- Không có case Done → **thành công** với `source_case_id=null`,
  `source_status=null`, `stage={people:[],assets:[]}` (không owner key).
  Không phải `case_not_found`.
- Hai source field null đồng thời hoặc id+`done`; status khác `done` là lỗi
  output. Không ghi DB, không tăng revision, không tạo Customer/Property/
  case/revision.

**Mốc lưu microsecond:** `updated_at` lưu Python UTC-naive đủ microsecond;
mọi writer case (create, save_case mới/cũ, commit_stage, update_meta,
convert_type, diagram_save kể cả child-only, participant add/edit/delete,
legacy case_create) đóng đúng một stamp trong transaction của nó. Lỗi/
rollback/conflict/replay/get/evaluate/export/import gợi ý không đóng stamp.
Case mới gán explicit stamp; flush mọi mutation case/status **trước** CAS
cuối để ORM/default không ghi đè. Độ mịn này tách hai lần lưu trong cùng
giây; clock trùng tuyệt đối giải bằng `id`. `Diagram.updatedAt` trên wire
vẫn chỉ tới giây, không dùng làm khóa chọn nguồn.

**Remap:** mọi `row_id` Người/Tài sản trả về là **UUID v4 mới**; map
person cũ→mới remap `owner_row_id`; asset cũ→mới thay row_id parent, đất
không có wire ID nên giữ nguyên vị trí/giá trị. Giữ `entity_id` (kể cả ID
cao/null), serial nguyên văn, độ đầy đủ năm và `null` khác `[]` của cụm đất.
Không trả `case`/meta/`revision`/`diagram`/`docx_import`/`capabilities`;
`source_case_id` chỉ là provenance kỹ thuật của phép đọc, không phải liên
kết nghiệp vụ mới. Đọc lặp lại được phép sinh UUID khác (không phải
allocator idempotent đã persist).

**Giữ identity qua lần lưu đầu (khoảng nối bắt buộc):** UI gửi Stage nguồn
vào `workspace_create`/save_case mới với `entity_id` của nguồn như **gợi ý
có kiểm neo** (§4.1 mục 5). Neo payload còn khớp identity đó → giữ đúng ID
(kể cả ID cao khi có ID cũ trùng neo); neo bị sửa → resolve lại, không sửa
master; thiếu neo → `null`. Không strip ID nguồn rồi để resolver chọn
min-ID, không dùng row_id nguồn để lách ownership, không lấy trường từ
identity lấp Stage. Gợi ý không phải int dương/tồn tại đúng bảng →
`stage_validation_error` gắn row/field.

**Errors:** `validation_error` (payload không phải object rỗng),
`case_type_unsupported {case_type}`, lỗi envelope hiện có
(`engine_not_installed`/`engine_unavailable`; retryable theo adapter).
Không có Done **không là lỗi**; không fallback rỗng khi runtime lỗi.

**Client:** `newDraft` đọc nguồn **một lần**, khóa sửa/lưu đến khi xong,
bỏ response phiên cũ, lỗi hiện rõ và không tự ghi DB. Thành công đặt Stage
nguồn vào bản đang sửa (baseline `committed` vẫn rỗng, không chi phối Pool),
`stageDirty=true` nếu có dòng; Pool/nhãn/gán node dùng ngay Stage nguồn;
meta/diagram luôn mới của nháp, không copy ngụ ý từ nguồn. Loại do người
dùng chọn; two_party bỏ owner key; nguồn two_party/không nguồn → owner
`null`, không tự gán người đầu. Nguồn rỗng là Stage rỗng, không notice lỗi.
`thoi_han` lẻ có trong nguồn phải giữ khi tạo dòng mới; không mở ô nhập mới.

### 13.21 `notary.workspace_duplicate` — nhân bản toàn bộ hồ sơ (vòng 2)

**Trạng thái:** ĐÃ TRIỂN KHAI 22/10/2026 (proof:
`test_issue13_workspace_duplicate.py`). Command tạo
case **mới** bằng cách copy nội dung **đã lưu** của nguồn trong một
transaction; KHÔNG copy buffer editor chưa **Lưu hồ sơ**. Nguồn được phép
`draft` hoặc `done`; `case_type` phải thuộc `inheritance`/`two_party`.

> **Chốt kỹ thuật vòng 2, chờ owner xác nhận:** bản sao lần tạo đầu mang
> `status=draft`, `revision=1`. Toàn bộ nội dung copy là yêu cầu đã có của
> owner; **trạng thái bản sao chưa được owner duyệt**. Đây không phải
> quyết định nghiệp vụ đã nghiệm thu và không chặn các phần đã rõ của vòng 2.

```yaml
payload:
  source_case_id: <int >= 1>        # strict; cấm bool/string/null
  idempotency_key: <uuid4>          # bắt buộc, giữ qua retry cùng ý định
                                    # cấm case_id/base_revision/case/stage/
                                    # diagram/status/field override
```

```yaml
result:
  kind: workspace_duplicate
  data:
    schema_version: notary.case-drafting.v2
    backend_mode: real | mock
    case: <workspace_get.case của bản sao>       # revision như get, không bịa
    stage: <workspace_get.stage của bản sao>
    diagram: <workspace_get.diagram của bản sao>
    capabilities: <workspace_get.capabilities>
    docx_import: <optional, như workspace_get>
    source_case_id: <int >= 1>
    created: <bool>                 # true lần tạo; false replay
```

**Idempotency:** hash SHA-256 canonical JSON
`{command:"workspace_duplicate", intent:"draft", source_case_id:N}`
(sort keys, separators như `_creation_hash`). **Không** hash snapshot,
revision/timestamp nguồn, UUID mới, case đích hay thời gian: retry sau khi
nguồn đổi vẫn trả bản sao đã tạo. Dùng cặp cột key/hash sẵn có, không thêm
cột `source_case_id`. Thứ tự: validate → chiếm write lock → **lookup key
trước khi load nguồn** → hash khớp trả workspace hiện tại của bản sao +
`source_case_id`, `created=false` (kể cả nguồn đã bị xóa sau lần đầu) →
hash khác `idempotency_conflict` → chưa có key mới load nguồn và tạo.
Replay **không** ép lại draft/rev1 nếu bản sao đã được sửa/lưu Done và
không tăng revision.

**Copy/remap đầy đủ (một snapshot transaction):**

| Nội dung | Quy tắc bản sao |
|---|---|
| Case ID/key/hash/revision/status/timestamps | ID mới; key/hash của duplicate; `draft`/rev1 lần tạo đầu; `created_at`/`updated_at` mới (§13.20). Không copy status/revision/key/hash/thời gian nguồn |
| Meta cột + 7 scalar | Giữ `case_type`/`document_type`, ngày lập, nơi niêm yết, người nhận ủy quyền + ID, nội dung việc, ghi chú, kể cả null; giữ nguyên snapshot tên UQ, không resolve lại master. 7 scalar (`tenvanban`, `nhomhopdong`, `loaivanbannhandien`, `socongchung`, `ngaycongchung`, `congchungvien`, `thuky`) copy nguyên; `chudat` không copy mà derived lại |
| Person/asset rows | Map `P[old]=uuid4()`/`A[old]=uuid4()` một-một; case_id mới; `customer_id`/`property_id` giữ nguyên (kể cả null/ID cao trùng neo); mọi cột dữ kiện/vị trí/`thoi_han`/serial giữ nguyên, không derive lại hoặc lấp master |
| Land rows | PK integer mới; parent = `A[old]`; loại/diện tích/thời hạn/vị trí copy kể cả hàng trống; `null` vs `[]` giữ qua present flag; không thay identity đất bằng PK DB mới |
| Owner pointer | `P[old owner]` hoặc `null`; two_party không key; không dùng `nguoi_chet_id` làm row pointer |
| Diagram state | Chỉ `nodes[].personId` map qua `P`, kể cả hidden/deleted. `node.id`/`parentSlotIds`/`spouseSlotId` là slot ID → giữ topology; `ownPositions`/`receivePositions` là vị trí 1-based → giữ nguyên, không map qua asset. Không global string-replace UUID |
| Diagram render/warnings | Cache derived rebuild từ state+rows đã remap bằng IW helper nếu nguồn có cache; null giữ null. `requiredSlots.anchorSlotId` là slot. Giữ warning ngoài engine; không copy warning trỏ row cũ |
| Participants | PK mới, `ho_so_id` mới; person/parent pointer non-null map `P`; identity projection từ rows mới, pointer null legacy giữ null + identity nguồn; giữ vai trò/hàng thừa kế/`co_nhan_tai_san`/tỷ lệ/ghi chú. Không chỉ dựng lại derived rồi bỏ manual role/note |
| Property links | PK mới/case_id mới; `case_asset_row_id` map `A`; `property_id` từ rows mới; primary theo vị trí. Không copy ID link/timestamps |
| JSON case | schemaVersion 4, scalar/owner/diagram/docx_import; không resurrect Stage/assets/engine_state_json; `Diagram.updatedAt` là dấu kỹ thuật của bản mới |
| `docx_import` | Giữ source_id/candidate/occurrence/field/slot/hash/label; **remap `sources[].records[].row_id` bằng P hoặc A**. `records[].land_rows` là số dòng nguồn Word → giữ nguyên. `bindings` gián tiếp qua candidate; `slot_for` trước/sau remap cùng slot; stale vẫn stale, không tự xác nhận/chữa/prune im lặng |

- Dùng helper copy rows riêng (copy cột/PK/FK/thứ tự tường minh), **không**
  serialize→strip→derive→upsert và không dùng `_write_stage_rows` cho clone.
  Không gọi `_sync_participants_and_owner` (helper hiện hành loại participant
  ngoài active role set và ghi lại field tay).
- Kiểm mọi participant/record/diagram ref có map **trước** khi validate;
  thiếu map/source bytes/context hỏng → lỗi rõ, rollback, không bỏ phần lỗi
  để success. Validate context ở chế độ **read-only** (không save template,
  không prune, không đổi label/hash); transaction DB không rollback file
  ngoài DB.
- Một transaction, một commit: tạo case mới → rows/đất → link/owner
  projection → participants → remap Diagram/evaluate không commit →
  copy/validate provenance → JSON v4 → stamp mới → `engine_state_json=null`
  → commit. Lỗi ở bất kỳ bước nào rollback case/rows/đất/participants/
  links/key/hash; nguồn và identity không UPDATE/DELETE.

**Errors:** `validation_error` (shape/key/ID/type, binding/provenance không
hợp lệ), `case_not_found {source_case_id}` (nguồn không tồn tại khi chưa
replay), `case_type_unsupported`, `idempotency_conflict`, các lỗi Diagram
(`diagram_invalid_state`/`diagram_reference_outside_stage`/
`diagram_owner_mismatch`) nếu nội dung nguồn không copy đúng, lỗi binding/
kho nguồn hiện có, lỗi hạ tầng envelope (`engine_unavailable` retryable
cho SQLite busy → retry nguyên key). Không partial clone; không trả
`workspace_conflict` vì payload không có `base_revision` — snapshot lấy
tại transaction đã giữ writer.

**Client:** nút **Nhân bản** là thao tác nhỏ trên từng dòng danh sách
(container + button riêng, không nested button; Enter/Space không mở nguồn).
Sinh key **một lần cho một ý định**, giữ `{sourceId,key}` khi timeout/lỗi
hạ tầng; success hydrate workspace bản sao (caseId mới, dirty=false) rồi
refresh list; lỗi giữ workspace/dirty trước đó + pending retry. Xác nhận
bỏ sửa chưa lưu như open/newDraft; không lấy buffer nguồn làm dữ liệu clone;
không gọi `newDraft`/source_latest trước duplicate.

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

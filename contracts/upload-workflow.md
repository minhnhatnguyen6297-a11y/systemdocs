# Contract: Upload Workflow `v1`

**Version:** `upload.workflow.v1` · **Status:** APPROVED v1 (publish theo plan
MIN-69, task T1 — 24/09/2026) · **Owner:** `systemdocs` branch
`electron-system-shell` · **Kênh mang:** `desktopcommand.v1`
([`desktop-command.md`](./desktop-command.md)) + shape `g1.module.v1`
([`g1-module-data.md`](./g1-module-data.md)) · **Spec UI:**
[`../upload_lab/docs/spec_UI.md`](../upload_lab/docs/spec_UI.md)

Contract giữa **Electron shell (module `upload` — nhãn "Upload Lab")** và
**Python sidecar** cho nghiệp vụ quét hồ sơ Word, audit sổ công chứng Excel và
chuẩn bị biểu mẫu upload trên một máy Windows. Mọi message đi trong envelope
`desktopcommand.v1`; file này chỉ định nghĩa `payload`, `result.data`, error
codes và quy tắc nghiệp vụ của namespace `upload.*`.

## 1. Nền tảng dùng lại (không định nghĩa lại)

- Envelope request/response, auth, lifecycle, idempotency theo
  `desktop-command.md` §1–§5. `command_id` idempotent: cùng `command_id` +
  cùng nội dung → cùng job; cùng `command_id` + nội dung khác →
  `command_id_conflict`.
- `result` theo JobResult `g1-module-data.md` §2 (`kind`, `data`, `evidence`,
  `warnings`, `source_files`); `error` theo §4 của cùng contract.
- `file_ref` theo `desktop-command.md` §6: `scope: "machine_local"`, path
  tuyệt đối, không UNC.
- Trạng thái job: `accepted|running|waiting_user|partial|succeeded|failed|
  canceled`; `waiting_on: login|review|finalize|confirm|null`.
- `next_action ∈ {login_required, pick_files, retry, contact_admin, null}`.

## 2. Nhận diện luồng: `workflow_version`

- Mọi payload và mọi `result.data` của luồng mới mang
  `workflow_version: "upload.workflow.v1"` (literal, bắt buộc).
- Consumer mới **phải** kiểm tra capability trước khi gửi payload có version
  (§9); backend từ chối `unsupported_workflow_version` khi version sai hoặc
  thiếu ở command chỉ tồn tại trong luồng mới.
- Payload **không có** `workflow_version` trên các command cũ (`upload.scan`,
  `upload.audit_excel`, `upload.env_check`, `upload.session_start`,
  `upload.session_status`, `upload.confirm_login`, `upload.session_close`,
  `upload.download_export`, `upload.prepare`, `upload.finish_review`) chạy
  **legacy path nguyên trạng** — không áp scope/revision của contract này,
  giữ data root legacy và shape legacy (vd `data.file` thay `file_ref`).

## 3. Vocabulary — khóa và phạm vi

| Khóa | Kiểu | Nguồn phát sinh | Ghi chú |
|---|---|---|---|
| `website_id` | string slug `[a-z][a-z0-9_]{1,31}` | backend registry | hiện chỉ `nam_dinh` |
| `browser_id` | string không rỗng | backend khi mở Chromium | mã tham chiếu **không bí mật**; không mang quyền portal |
| `run_id` | string không rỗng | backend khi `upload.scan` xong | backend giữ binding run→manifest |
| `audit_id` | string không rỗng | backend khi `upload.audit_excel` xong | gắn website + file + khoảng ngày |
| `record_id` | int ≥ 1 | engine registry trong manifest | **không** phải số thứ tự hiển thị |
| `job_id` | string | server sinh (desktopcommand) | — |
| `target_job_id` | string | client lấy từ job đang chờ | chỉ dùng trong confirm_login/finish_review |
| `revision` | int ≥ 0 | backend workspace | tăng khi website/nguồn/binding đổi |
| `queue_revision` | int ≥ 0 | backend per run | tăng khi queue của run đổi |
| `expected_revision` | int ≥ 0 | client gửi | giá trị `revision` client đã đọc — bảo vệ workspace/source |
| `command_id` | uuid v4 | client sinh | idempotency (desktopcommand §5) |

**Quy tắc phạm vi (bắt buộc):**

1. `website_id`, `browser_id`, `run_id`, `audit_id`, `record_ids`,
   `target_job_id` trong một request phải **cùng phạm vi**: các tham chiếu
   phải thuộc `website_id` đã khai; `record_ids` phải thuộc `run_id` đã khai.
   Vi phạm → từ chối **trước** khi mở tab/chạy engine (`website_mismatch` khi
   tham chiếu thuộc website khác; `scope_violation` khi tham chiếu không tồn
   tại hoặc ngoài phạm vi trong website).
2. `expected_revision` bảo vệ thay đổi workspace/nguồn (đổi website, run mới,
   audit mới, đổi folder): lệch → `stale_revision`. `queue_revision` bảo vệ
   queue đang gửi: lệch → `stale_revision`. Poll tiến độ/trạng thái **không**
   tự tăng revision nguồn — tránh làm thao tác hợp lệ bị từ chối liên tục.
3. `manifest_ref` là FileRef tới **file manifest thật** của đúng run đó (JSON
   trong `runs/` của website). Backend giữ binding `run_id → manifest_ref`,
   kiểm tồn tại và hash trước khi dùng. Renderer **không** tự dựng path từ
   tên thư mục. Manifest thiếu → `file_not_found`; hash/binding sai →
   `manifest_mismatch`. Lỗi đọc registry/manifest là **lỗi** — không đổi
   thành thành công với danh sách rỗng.
4. Backend tính danh sách loại trừ (đã có trên web / đã Lưu / cần đối chiếu)
   từ audit và registry thật — không tin danh sách số do renderer tự dựng.

**Quy ước null:** giá trị không có/không áp dụng là `null`; `""` **không hợp
lệ** thay `null` trên các khóa ID/tham chiếu. `ghi_chu` rỗng là dữ liệu hiển
thị hợp lệ (ô trống theo MIN-77). Ngày trên wire: ISO `YYYY-MM-DD` hoặc
`null`; UI hiển thị `DD/MM/YYYY`; bộ xử lý website đổi sang định dạng portal.

**Khóa cấm:** không key nào trong payload (mọi cấp) được mang tên khớp bộ lọc
nhạy cảm của `desktop-command.md` §3 — bao gồm **`session_id`** và mọi key
chứa `session`, `password`, `token`, `credential`, `cookie`, `auth`,
`storage_state`, `api_key`, `bearer` → `payload_rejected_sensitive_key`.
Không credential/cookie/token trong payload, result, error.details, log hay
ví dụ.

## 4. Danh mục website

Registry hiện có đúng một website:

| website_id | label | display_url | capabilities |
|---|---|---|---|
| `nam_dinh` | Nam Định | `https://congchungnamdinh.ninhbinh.gov.vn` | `login`, `download_export`, `audit_excel`, `scan`, `prepare`, `staff_options`, `reconcile` |

- `capabilities` liệt kê thao tác website đó hỗ trợ thật; UI chỉ bật nút theo
  capability. Frontend **không** chứa danh sách URL hay nhánh nghiệp vụ theo
  tỉnh.
- `website_id` không đăng ký → `unknown_website`; không quay về `nam_dinh`
  ngầm.
- Website thứ hai chỉ được thêm khi có bộ xử lý và mẫu file **thật**; contract
  mở rộng bằng thêm hàng registry — không đổi schema. Bộ xử lý giả cho test
  không xuất hiện trong catalog production.

## 5. Bảng command

`— mới` = chỉ tồn tại trong luồng `upload.workflow.v1`; `— bổ sung` = command
đã có ở luồng legacy, thêm `workflow_version` và scope/revision khi tham gia
luồng mới.

| Command | Request chính | Result chính (trong `result.data`) |
|---|---|---|
| `upload.websites` — mới | `workflow_version` | `websites[]` (website_id, label, display_url, capabilities, status), `selected_website_id` |
| `upload.workspace_get` — mới | `workflow_version`, `website_id` (null = đọc lựa chọn đã lưu) | workspace: `website_id`, `revision`, `run_id`, `audit_id`, `browser_id`, `active_job_ids`, `needs_reconcile_record_ids`, `has_excel`, `queue_revision` |
| `upload.website_select` — mới | `workflow_version`, `website_id`, `expected_revision` | workspace của website mới; từ chối khi website cũ còn hoạt động |
| `upload.env_check` — bổ sung | `workflow_version`, `website_id` | `status`, `steps[]` đạt/cảnh báo/bị chặn + hướng dẫn đã lọc |
| `upload.session_start` — bổ sung | `workflow_version`, `website_id`, `expected_revision` | job → `waiting_user(login)`; result `session_state` gồm `browser_id`, `login`, `staff_options`; không chứa credential |
| `upload.confirm_login` — bổ sung | `workflow_version`, `website_id`, `browser_id`, `target_job_id` | xác nhận đúng job `waiting_on=login`; backend vẫn kiểm trạng thái đăng nhập thật |
| `upload.session_status` — bổ sung | `workflow_version`, `website_id`, `browser_id` | `login`, `tabs` (open/saved/closed/unknown record ids); không trả cookie |
| `upload.session_close` — bổ sung | `workflow_version`, `website_id`, `browser_id` | `closed`, `verified_record_ids`, `needs_reconcile_record_ids` |
| `upload.download_export` — bổ sung | `workflow_version`, `website_id`, `browser_id`, `from_date`, `to_date` | `file_ref` sổ tải xong kèm `from_date`/`to_date` |
| `upload.audit_excel` — bổ sung | `workflow_version`, `website_id`, `file_ref`, `from_date`, `to_date` | `audit_id`, `summary`, `missing[]`, `issues[]`; backend giữ tập số phục vụ đối chiếu |
| `upload.scan` — bổ sung | `workflow_version`, `website_id`, `folder`, `expected_revision` (+`full_rescan`, `modified_since` tùy chọn) | `run_id`, `manifest_ref` tới **file**, `stats`, `records[]`, `revision` mới |
| `upload.queue_get` — mới | `workflow_version`, `website_id`, `run_id`, `audit_id` (null được) | `queue_revision`, `folder_rows[]`, `missing_in_excel_record_ids`, `has_excel` |
| `upload.staff_options` — mới | `workflow_version`, `website_id`, `browser_id` (null được), `refresh` | `cong_chung_vien[]`, `source` (cache/portal), `fetched_at` |
| `upload.preferences` — mới | `workflow_version`, `website_id`, `values` (thiếu = đọc) | `chunk_size`, `cong_chung_vien`, `thu_ky`; không nhận URL/token tự do |
| `upload.prepare` — bổ sung | `workflow_version`, `website_id`, `browser_id`, `run_id`, `audit_id` (null được), `queue_revision`, `record_ids[]`, `chunk_size`, `cong_chung_vien`, `thu_ky` | job → `waiting_user(review)`; result `upload_prepare`: `summary`, `breakdown`, `saved_record_ids`, `needs_reconcile_record_ids` |
| `upload.finish_review` — bổ sung | `workflow_version`, `website_id`, `browser_id`, `target_job_id` | kết thúc đúng bước kiểm tra; **không** tự đánh dấu `uploaded_success` |
| `upload.reconcile` — mới | `workflow_version`, `website_id`, `run_id`, `audit_id` (mới, bắt buộc) | `verified_record_ids`, `needs_reconcile_record_ids`; không tự gửi lại |

## 6. Schema chi tiết

Quy ước bảng: **R** = bắt buộc, **O** = tùy chọn, **N** = cho phép `null`.
`workflow_version` là **R** của mọi payload và lặp lại trong mọi
`result.data`; các bảng dưới không liệt kê lại.

### 6.1 `upload.websites` → kind `website_catalog`

Payload: không trường nào thêm.

```yaml
data:
  websites:
    - website_id: "nam_dinh"
      label: "Nam Định"
      display_url: "https://congchungnamdinh.ninhbinh.gov.vn"
      capabilities: [login, download_export, audit_excel, scan, prepare, staff_options, reconcile]
      status: "available"        # available | unavailable
  selected_website_id: "nam_dinh" | null
```

### 6.2 `upload.workspace_get` / `upload.website_select` → kind `upload_workspace`

`workspace_get` payload: `website_id` (R, **N** — null để đọc lựa chọn đã lưu).
`website_select` payload: `website_id` (R), `expected_revision` (R, int ≥ 0 —
revision đọc được từ `workspace_get`; `0` chỉ khi chưa từng chọn website).

```yaml
data:
  website_id: "nam_dinh" | null
  revision: 4                    # int; 0 = workspace trống/chưa chọn
  run_id: "run_x9k2" | null
  audit_id: "aud_7" | null
  browser_id: "brw_1" | null
  active_job_ids: ["job_..."]    # job chưa terminal của website này
  needs_reconcile_record_ids: [140, 141]
  has_excel: true
  queue_revision: 7 | null       # null khi chưa có run
```

`website_select` trả workspace của website **mới** (revision mới). Từ chối
`workflow_busy` khi website cũ còn `active_job_ids` hoặc tab chờ kiểm tra;
`stale_revision` khi `expected_revision` lệch; `unknown_website` khi ID chưa
đăng ký. Chọn lại đúng website đang dùng trả workspace hiện tại (idempotent).

### 6.3 `upload.env_check` → kind `env_check`

Payload: `website_id` (R).

```yaml
data:
  website_id: "nam_dinh"
  status: "passed"               # passed | warning | blocked
  steps:
    - key: "disk_space"
      label: "Dung lượng đĩa"
      status: "passed"           # passed | warning | blocked
      message: "Con 42.5 GB"
      guidance: ""               # hướng dẫn đã lọc, không dữ liệu nhạy cảm
      details: { free_gib: 42.5 }
```

### 6.4 `upload.session_start` → kind `session_state` (job `waiting_on=login`)

Payload: `website_id` (R), `expected_revision` (R).

Job vào `waiting_user(login)` tới khi `upload.confirm_login` đúng
`target_job_id`, cancel, hoặc `upload.login_timeout` (15 phút). Result cuối:

```yaml
data:
  website_id: "nam_dinh"
  browser_id: "brw_1"
  login: { status: "authenticated", checked_at: "2026-09-24T10:00:30Z" }
  staff_options: { cong_chung_vien: ["Phạm Minh Chi", "..."], source: "portal" }
```

`login.status ∈ {authenticated, awaiting_login, closed, unknown}` —
**không** chứa credential/cookie/storage_state.

### 6.5 `upload.confirm_login` / `upload.finish_review` → kind `session_state`

Payload: `website_id` (R), `browser_id` (R), `target_job_id` (R).

```yaml
data:
  website_id: "nam_dinh"
  browser_id: "brw_1"
  target_job_id: "job_..."
  login_confirmed: true          # confirm_login
  # hoặc review_finished: true   # finish_review
```

- `target_job_id` phải là job `upload.session_start` đang `waiting_on=login`
  (cho confirm_login) hoặc job `upload.prepare` đang `waiting_on=review` (cho
  finish_review), cùng `website_id` + `browser_id`. Sai → `wrong_job`;
  **không giải phóng** bước đang chờ.
- `confirm_login` chỉ *xin* xác nhận — job `session_start` vẫn kiểm trạng
  thái portal thật trước khi `succeeded`; không đăng nhập thật →
  `upload.login_not_confirmed`.
- `finish_review` kết thúc bước chờ của job prepare; **không** tự đánh dấu
  `uploaded_success` — trạng thái Lưu tiếp tục đọc qua `session_status`.

### 6.6 `upload.session_status` → kind `session_state`

Payload: `website_id` (R), `browser_id` (R).

```yaml
data:
  website_id: "nam_dinh"
  browser_id: "brw_1"
  login: { status: "authenticated", checked_at: "2026-09-24T10:05:00Z" }
  tabs:
    open_record_ids: [140, 141]        # đang mở/đã điền, chờ người kiểm
    saved_record_ids: [138, 139]       # đã xác minh Lưu trên portal
    closed_record_ids: [137]           # đóng trước khi Lưu
    unknown_record_ids: [142]          # mất dấu trước khi xác định
```

Đây là lệnh poll gộp trong lúc job chờ — được gọi thoải mái, không đổi
revision, không trả cookie/storage state.

### 6.7 `upload.session_close` → kind `session_state`

Payload: `website_id` (R), `browser_id` (R).

```yaml
data:
  website_id: "nam_dinh"
  browser_id: "brw_1"
  closed: true
  verified_record_ids: [138, 139]
  needs_reconcile_record_ids: [142]
```

Trước khi đóng, backend poll/reconcile các tab còn đọc được; tab không xác
định → `needs_reconcile_record_ids`. Đóng không hoàn tác một lần Lưu đã xảy
ra.

### 6.8 `upload.download_export` → kind `export_download`

Payload: `website_id` (R), `browser_id` (R), `from_date` (R, ISO), `to_date`
(R, ISO).

```yaml
data:
  website_id: "nam_dinh"
  file_ref: { path: "D:/.../downloads/so_cong_chung.xlsx", scope: "machine_local",
              sha256: "...", size_bytes: 18233 }
  from_date: "2026-01-01"
  to_date: "2026-09-24"
```

Legacy path trả `data.file` (object `{path, scope}`); luồng versioned **chỉ**
dùng `file_ref`.

### 6.9 `upload.audit_excel` → kind `audit_report`

Payload: `website_id` (R), `file_ref` (R, FileRef tới `.xlsx`/`.xlsm`), 
`from_date` (R, ISO), `to_date` (R, ISO).

```yaml
data:
  website_id: "nam_dinh"
  audit_id: "aud_7"
  from_date: "2026-01-01"
  to_date: "2026-09-24"
  summary:
    excel_total: 120            # Tổng số đã nạp
    valid_count: 115            # Hợp lệ trong sổ
    missing_count: 4            # Số còn thiếu
    issue_count: 1              # Lỗi / Trùng lặp
    duplicate_count: 0
  missing:                      # bảng "Số còn thiếu" — cột MIN-77
    - { stt: 1, ngay: null, so_cong_chung: "130/2026", ghi_chu: "" }
  issues:                       # bảng "Số lỗi, trùng" — cột MIN-77
    - { stt: 1, ngay: "2026-03-14", so_cong_chung: "98/2026", ghi_chu: "trung_so: ..." }
```

Backend giữ binding `audit_id → website + file_ref + khoảng ngày + tập số hợp
lệ` để phục vụ `queue_get`/`prepare` loại trừ. `ngay` ISO hoặc `null`;
`ghi_chu` có thể `""`.

### 6.10 `upload.scan` → kind `scan_report`

Payload: `website_id` (R), `folder` (R, FileRef tới **thư mục**),
`expected_revision` (R), `full_rescan` (O, bool, mặc định false),
`modified_since` (O, ISO date, **N**).

```yaml
data:
  website_id: "nam_dinh"
  run_id: "run_x9k2"
  manifest_ref: { path: "D:/.../runs/2026-09-24_10-12-00.json",
                  scope: "machine_local", sha256: "...", size_bytes: 54012 }
  folder: { path: "D:/ho so/2026", scope: "machine_local" }
  stats: { candidates_found: 31, processed_files: 31 }
  records:
    - { record_id: 138, contract_no: "138/2026", status: "extracted",
        reason: "", last_error: "", file_path: "D:/ho so/2026/GD-138.docx" }
  revision: 5                    # workspace revision sau khi gắn run mới
```

`manifest_ref` trỏ tới **file** manifest của chính `run_id` — không phải
thư mục `runs/`, không fallback "file mới nhất". Scan mới tạo run mới; các
`record_id`/selection của run cũ hết hiệu lực tham chiếu.

### 6.11 `upload.queue_get` → kind `upload_queue`

Payload: `website_id` (R), `run_id` (R), `audit_id` (R, **N** — null = phân
loại không Excel; có giá trị = audit phải thuộc website).

```yaml
data:
  website_id: "nam_dinh"
  run_id: "run_x9k2"
  audit_id: "aud_7" | null
  queue_revision: 7
  has_excel: true
  folder_rows:
    - record_id: 138
      contract_no: "138/2026/CCGD"        # số gốc trích được
      normalized_contract_no: "138/2026"  # canonical entities.md §5; null khi không chuẩn hóa được
      ngay: "2026-04-15" | null           # ISO
      ghi_chu: "chua co trong Excel"
      file_path: "D:/ho so/2026/GD-138.docx"
      status: "extracted"                 # matched | extracted | extract_failed | ...
      selected: true                      # chọn mặc định theo phân loại
      has_issue: false
      missing_fields: []
  missing_in_excel_record_ids: [138, 139]
```

- `has_excel=false`: `selected=false` mọi dòng, `ghi_chu` "chua load Excel";
  không tự chọn là thiếu trên web.
- `ghi_chu` theo engine: `chua co trong Excel`, `da co trong Excel`,
  `sai format`, `sai nam`, `khong co so`, `trung trong folder`,
  `missing: <fields>`, `chua load Excel` — ghép bằng `; `.

### 6.12 `upload.staff_options` → kind `staff_options`

Payload: `website_id` (R), `browser_id` (R, **N** — null chỉ cho đọc cache),
`refresh` (R, bool).

```yaml
data:
  website_id: "nam_dinh"
  cong_chung_vien: ["Phạm Minh Chi", "..."]
  source: "portal"              # portal | cache
  fetched_at: "2026-09-24T10:06:00Z" | null
```

`refresh: true` cần `browser_id` đã đăng nhập (thiếu → `validation_error`;
chưa đăng nhập → `upload.login_not_confirmed`). `refresh: false` trả cache
đúng website (có thể `source: "cache"`, `fetched_at` của lần thật gần nhất).

### 6.13 `upload.preferences` → kind `preferences`

Payload: `website_id` (R), `values` (O — object; thiếu = đọc hiện tại).

```yaml
values (chỉ các key này, mỗi key tùy chọn):
  chunk_size: 10                # int 1..30
  cong_chung_vien: "Phạm Minh Chi" | null
  thu_ky: "Nguyễn Nhật Minh" | null

data (luôn trả đầy đủ sau đọc/lưu):
  website_id: "nam_dinh"
  chunk_size: 10
  cong_chung_vien: "Phạm Minh Chi" | null
  thu_ky: "Nguyễn Nhật Minh" | null
```

`values` chứa key ngoài ba key trên → `validation_error` (không nhận
URL/token/giá trị tự do; key nhạy cảm vẫn bị §3 chặn trước).
`chunk_size` ngoài 1–30 → `validation_error`.

### 6.14 `upload.prepare` → kind `upload_prepare` (job `waiting_on=review`)

Payload: `website_id` (R), `browser_id` (R), `run_id` (R), `audit_id` (R,
**N**), `queue_revision` (R, int ≥ 0), `record_ids` (R, list int ≥ 1, không
rỗng, không trùng), `chunk_size` (R, int 1–30), `cong_chung_vien` (R, **N**),
`thu_ky` (R, **N**).

Job mở tối đa `chunk_size` tab đã điền (dry-run) rồi `waiting_user(review)`
tới khi `finish_review` đúng `target_job_id`, cancel, hoặc
`upload.review_timeout` (60 phút). Trong lúc chờ, trạng thái tab đọc qua
`upload.session_status` — job **không** nhận result hoàn tất giả.

```yaml
data (result cuối):
  website_id: "nam_dinh"
  browser_id: "brw_1"
  run_id: "run_x9k2"
  audit_id: "aud_7" | null
  summary:
    total_requested: 5
    prepared_count: 4
    remaining: 26                # hồ sơ đã chọn còn lại chưa mở (đợt sau)
    open_record_ids: [138, 139, 141, 142]
  breakdown:
    succeeded: [{ record_id: 138, stage: "prepared" }, ...]
    failed:    [{ record_id: 140, stage: "prepared",
                  code: "extract_failed", message: "..." }]
  saved_record_ids: [138, 139]   # đã xác minh Lưu khi job kết thúc
  needs_reconcile_record_ids: [142]
```

- `stage ∈ {prepared, saved}`: `prepared` = điền biểu mẫu/mở tab;
  `saved` = ghi nhận Lưu trên portal. Một phần lỗi → job `partial` với
  `data.breakdown` đầy đủ (desktopcommand §5) + `error.code
  upload.partial_failure`.
- Backend loại trừ theo audit/registry thật; `record_ids` ngoài run →
  `scope_violation`; `queue_revision` cũ → `stale_revision`; browser đang bận
  → `browser_busy`; manifest thiếu/sai → `file_not_found`/`manifest_mismatch`.

### 6.15 `upload.reconcile` → kind `reconcile_report`

Payload: `website_id` (R), `run_id` (R), `audit_id` (R — audit **mới** đã nạp,
bắt buộc: đối chiếu theo sổ mới, không theo Excel cũ).

```yaml
data:
  website_id: "nam_dinh"
  run_id: "run_x9k2"
  audit_id: "aud_8"
  verified_record_ids: [142]          # xác minh đã có trên web
  needs_reconcile_record_ids: [143]   # vẫn cần người kiểm tra
```

Không tự gửi lại: `verified` chỉ mở khóa hiển thị "đã có trên web";
`needs_reconcile` giữ chặn cho tới khi người dùng/audit kế xác minh.

## 7. Quy tắc vận hành

1. **Browser:** một browser thread duy nhất sở hữu mọi Playwright call (kể cả
   poll/close). Xác nhận cũ/khác website/khác job **không** giải phóng bước
   đang chờ (`wrong_job`). Hai website không dùng chung browser; một website
   một `browser_id` tại một thời điểm.
2. **waiting_user:** job `waiting_on=login|review` vẫn theo dõi được qua
   `session_status`; không đưa result hoàn tất giả vào job đang chạy. Poll
   được gộp, không chồng request; kết quả truy vấn ngắn hạn dọn khỏi bộ nhớ
   theo giới hạn xác định.
3. **Hủy:** `POST .../cancel` → `canceled`; cancel **không** hoàn tác Lưu đã
   xảy ra, không tự đóng tab người đang kiểm. Trước khi đóng browser backend
   reconcile các tab đọc được; không xác định → `needs_reconcile`.
4. **Restart:** sidecar restart → in-flight `failed{engine_restarted,
   retryable:true}`. Job store giữ tối thiểu `command_id`, hash request,
   website, run, job, browser, `record_ids`, kết quả đã xác minh — **không**
   lưu cookie. Không phát lại upload mù sau crash; hồ sơ chưa rõ vào nhóm
   Cần đối chiếu.
5. **Ngày:** wire ISO `YYYY-MM-DD`; UI `DD/MM/YYYY`; bộ xử lý đổi sang định
   dạng portal.
6. **`file` → `file_ref`:** luồng versioned dùng `file_ref` (FileRef) ở
   `download_export`/`audit_excel`/`manifest_ref`; legacy giữ `file`/path
   như cũ. Renderer không tự dựng path.
7. **Dry-run:** không auto-Save/Finalize; `Đã điền sẵn` ≠ `Đã lưu trên web`;
   `finish_review` không phải bằng chứng Lưu.

## 8. Error codes

`next_action ∈ {login_required, pick_files, retry, contact_admin, null}`.
Code mới của contract này ở nhóm đầu; nhóm sau là code tái sử dụng.

| code | Khi nào | retryable | next_action |
|---|---|---|---|
| `unsupported_workflow_version` | `workflow_version` thiếu ở command chỉ-có-ở-v1 hoặc ≠ literal | false | null |
| `unknown_website` | `website_id` không trong registry | false | null |
| `website_mismatch` | browser/run/audit/job thuộc website khác `website_id` | false | null |
| `scope_violation` | tham chiếu không tồn tại/ngoài phạm vi trong website (record ngoài run, run/audit/browser lạ) | false | null |
| `stale_revision` | `expected_revision`/`queue_revision` lệch hiện tại — đọc lại workspace/queue rồi thử lại | true | retry |
| `workflow_busy` | đổi website khi còn job/tab chờ ở website cũ | true | retry |
| `browser_busy` | browser đang phục vụ job/thao tác khác | true | retry |
| `workflow_conflict` | luồng legacy và versioned tranh browser/dữ liệu ghi | false | null |
| `wrong_job` | `target_job_id` không phải job đang chờ đúng bước/scope | false | null |
| `command_id_conflict` | `command_id` trùng nhưng nội dung request khác | false | null |
| `manifest_mismatch` | manifest_ref không khớp binding run→manifest (hash/path) | false | null |
| `file_not_found` | file_ref/folder/manifest không tồn tại | true | pick_files (file người chọn) hoặc retry (manifest — quét/audit lại) |
| `file_scope_not_supported` | FileRef sai scope/UNC/không tuyệt đối | false | pick_files |
| `file_locked` | file bị khóa | true | retry |
| `validation_error` | sai kiểu/khoảng/date/thiếu trường/key lạ/`""`-as-null | false | null |
| `payload_rejected_sensitive_key` | key nhạy cảm trong payload | false | null |
| `unsupported_contract_version` | envelope `contract_version` sai/thiếu | false | null |
| `upload.login_not_confirmed` | chưa đăng nhập/đăng nhập chưa xác minh được | true | login_required |
| `upload.login_timeout` | hết 15 phút chờ đăng nhập | true | retry |
| `upload.review_timeout` | hết 60 phút chờ review | true | retry |
| `upload.partial_failure` | một phần hồ sơ lỗi (kèm status `partial`) | true | retry |
| `engine_unavailable` | sidecar/engine/browser không chạy được | true | retry |
| `engine_not_installed` | engine chưa cài/thiếu trên máy | false | contact_admin |
| `engine_version_mismatch` | engine sai version tối thiểu | false | contact_admin |
| `engine_restarted` | restart giữa chừng — không phát lại mù | true | retry |
| `engine_shutdown` | hủy do shutdown | true | retry |
| `user_canceled` | người hủy | false | null |
| `job_already_terminal` | thao tác lên job đã kết thúc | false | null |

`error.details` chỉ chứa dữ liệu không nhạy cảm (id, path, số liệu) — không
credential/cookie.

## 9. Versioning, capability, tương thích

1. **Capability:** sidecar công bố `upload.workflow.v1` trong
   `/healthz.supported_versions` và module `upload` trong module registry
   mang capability `upload.workflow.v1`. Consumer mới kiểm **trước** lần gọi
   đầu; thiếu → hiển thị trạng thái Unavailable, **không** fallback ngầm sang
   legacy payload.
2. `workflow_version` là **opt-in**: command cũ không mang trường này giữ
   nguyên xử lý/data root/shape legacy (`data.file`, không scope check của
   contract này). Backend **không** tự gán website cho payload legacy rồi ghi
   vào kho mới.
3. Command mới (không tồn tại legacy): `upload.websites`,
   `upload.workspace_get`, `upload.website_select`, `upload.queue_get`,
   `upload.staff_options`, `upload.preferences`, `upload.reconcile` — gọi
   không có/ sai `workflow_version` → `unsupported_workflow_version`.
4. **Khóa xung đột:** backend không cho luồng legacy và versioned đồng thời
   chiếm browser hoặc ghi dữ liệu Upload → `workflow_conflict`.
5. Thêm field optional = backward-compatible. Đổi nghĩa/kiểu/tên field, đổi
   enum → `upload.workflow.v2`. Bỏ hỗ trợ payload legacy là thay đổi phiên
   bản riêng sau này — **không** nằm trong đợt này.
6. `command_id` idempotent cho mọi command gây tác dụng phụ (scan, prepare,
   session_start, download_export...): retry an toàn, không nhân đôi tab/hồ
   sơ.

## 10. Examples & validator

- Ví dụ: `contracts/upload-workflow/examples/` — file `*.valid.json` phải
  pass, `*.invalid.json` bị reject với `expected_error` khớp code §8.
- Chạy: `python contracts/upload-workflow/validate_examples.py` (stdlib-only).
- Quy ước `fixture`: file JSON có thể mang khối `fixture` — **metadata test,
  không đi trên wire** — mô phỏng binding phía backend (`websites`,
  `workspace`, `browsers`, `runs`, `audits`, `queues`, `waiting_jobs`,
  `legacy_holds_browser`). Validator dùng nó để kiểm scope/revision/job
  deterministically. `expected_error` và `fixture` không phải field của
  envelope.
- Ví dụ phủ: command hợp lệ từng loại; job succeeded/waiting/partial/failed;
  sai website, ID ngoài run, revision cũ, manifest mất, xác nhận sai job,
  partial, browser busy, engine restart (recovery qua `upload.reconcile`),
  website chưa hỗ trợ, `file`→`file_ref`, khóa nhạy cảm, `""`-as-null, date
  sai, `chunk_size` ngoài 1–30.

## 11. Conformance checklist

Producer (sidecar) PHẢI:

- [ ] Reject envelope/version/sensitive-key theo desktopcommand §3 và
      `workflow_version` §2 trước khi dispatch.
- [ ] Kiểm scope cùng `website_id` + `record_ids ⊆ run` trước khi mở tab;
      không tin danh sách loại trừ từ renderer.
- [ ] Giữ binding `run→manifest_ref` (kiểm tồn tại/hash), `audit→website`,
      `browser→website`; một browser thread cho mọi Playwright call.
- [ ] `expected_revision`/`queue_revision` đúng ngữ nghĩa; poll không tăng
      revision nguồn.
- [ ] `waiting_on` đúng; confirm đúng `target_job_id`; không auto-Save/
      Finalize; `partial` kèm breakdown `record_id`+`stage`.
- [ ] Restart → `engine_restarted`; lưu recovery tối thiểu không cookie;
      terminal không đổi ngược; `command_id` trùng-nội-dung-khác →
      `command_id_conflict`.
- [ ] Khóa `workflow_conflict` legacy↔versioned; `unknown_website` cho ID lạ.

Consumer (Electron main/renderer) PHẢI:

- [ ] Kiểm capability `upload.workflow.v1` trước khi gửi payload versioned.
- [ ] Luôn gửi `workflow_version` trong luồng mới; dùng `file_ref`/`browser_id`/
      `run_id`/`audit_id` từ result backend — không tự dựng path/ID.
- [ ] Gửi `expected_revision`/`queue_revision` đọc được; khi `stale_revision`
      → đọc lại workspace/queue rồi retry.
- [ ] Không tự hoàn thành `waiting_user`; hiển thị lỗi theo `next_action`;
      không parse `error.message` cho nghiệp vụ.
- [ ] Giữ scope khi render kết quả: bỏ qua result của website/run/job khác
      ngữ cảnh đang xem.

## 12. Changelog

| Version | Ngày | Thay đổi |
|---|---|---|
| v1 | 24/09/2026 | Publish đầu tiên theo plan MIN-69 (§4) — 17 command, scope/revision, capability + compatibility policy, examples + validator |

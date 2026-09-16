# Kiến trúc hệ thống

## 0. Đọc mục này trước

Đích đến của hệ thống: **một hệ thống thống nhất, database chung, UI chung và
các thành phần chức năng chung được tái sử dụng.**

Từ 15/09/2026 (MIN-83) ba sản phẩm đã gộp thành **module trong monorepo này**
(nhánh `consolidate/monorepo`): `notary_v2/`, `upload_lab/`, `notaryoffice/`,
cộng thêm `shell/` — vỏ Electron + sidecar Python là kênh tích hợp đã duyệt đầu
tiên. "Repo con" trong tài liệu cũ = module trong repo này.

[`docs/g1/COMPONENT_MAP.md`](./docs/g1/COMPONENT_MAP.md) là bản đồ ownership/reuse
**draft** (issue MIN-57 đã cancel — chỉ còn giá trị tham chiếu); không phải
thiết kế vật lý hay quyền thực hiện migration.

**Giai đoạn hiện tại: hai module nghiệp vụ có thể chạy độc lập hoặc qua
`shell/`; module thứ ba mới có đặc tả.** Việc bây giờ là làm tốt từng phần,
đồng thời **không để chúng phân kỳ** ở bốn chỗ: khóa định danh
([`contracts/entities.md`](./contracts/entities.md)), lựa chọn công nghệ
([`TECH_STACK.md`](./TECH_STACK.md)), schema/tên trường (`TECH_STACK.md` mục 3),
và ranh giới dữ liệu/provenance (mục 6 dưới đây).

Vì vậy đọc mục 1–3 dưới đây là **hiện trạng**, không phải trạng thái cuối cùng.

## 1. Hiện trạng: tích hợp duy nhất qua shell

Hai nhánh đầu là hiện trạng; nhánh `notaryoffice` là thiết kế, chưa có runtime
(`notaryoffice/AGENTS.md`). **Không có API trực tiếp giữa ba module nghiệp vụ**,
chưa có DB dùng chung, chưa có luồng dữ liệu tự động nào giữa chúng.

Kênh tích hợp đã duyệt duy nhất: `shell/` gọi `notary_v2`/`upload_lab` qua
sidecar (`desktopcommand.v1`, `contracts/desktop-command.md`) — sidecar import
engine trong-process qua `engine_roots.py`/`sys.path`, không qua HTTP tới
engine và không phải API giữa hai module nghiệp vụ.

```mermaid
flowchart TB
    subgraph NV2["notary_v2 — Soạn thảo hồ sơ mới"]
        direction TB
        NV2IN["Ảnh giấy tờ / Zalo Inbox"]
        NV2OCR["Cloud AI OCR + parser regex<br/>(CCCD, sổ đỏ, giấy khai tử)"]
        NV2CASE["Case Workspace<br/>Stage / Pool / Diagram<br/>engine thừa kế"]
        NV2OUT["Word hợp đồng / văn bản<br/>(word_engine + template)"]
        NV2IN --> NV2OCR --> NV2CASE --> NV2OUT
    end

    subgraph UL["upload_lab — Số hóa hồ sơ giấy"]
        direction TB
        ULIN["Kho Word cũ .doc/.docx<br/>trên ổ đĩa"]
        ULEX["python-docx + Windows IFilter<br/>→ trích trường web form"]
        ULDB["output/*.json<br/>registry.sqlite3"]
        ULAUD["Đối chiếu sổ Excel<br/>phát hiện số công chứng bị hở"]
        ULUP["Playwright → web CSDL<br/>công chứng tỉnh Nam Định"]
        ULIN --> ULEX --> ULDB --> ULAUD --> ULUP
    end

    subgraph NO["notaryoffice — Theo dõi hồ sơ đang chạy (chưa code)"]
        direction TB
        NOSEN["Activity Sentinel trên 6 máy con<br/>file save · print spooler · scan"]
        NOEV["Evidence Record<br/>(dữ kiện quan sát được)"]
        NODC["Draft Case Builder<br/>+ confidence ranking"]
        NOCF["Popup xác nhận tại máy trạm"]
        NOSE["Search: hồ sơ bà Gái ở đâu?"]
        NOSEN --> NOEV --> NODC --> NOCF --> NOSE
    end

    subgraph SH["shell — vỏ Electron + sidecar (desktopcommand.v1)"]
        direction TB
        SHUI["Electron main/renderer"] --> SHSC["Python sidecar<br/>import engine qua sys.path"]
    end

    SD["docs gốc<br/>vocabulary · ranh giới · quyết định mở"]
    SD -.->|tham chiếu, không ràng buộc runtime| NV2
    SD -.->|tham chiếu, không ràng buộc runtime| UL
    SD -.->|tham chiếu, không ràng buộc runtime| NO

    SHSC ==>|"gọi hàm engine thật (in-process)"| NV2
    SHSC ==>|"gọi hàm engine thật (in-process)"| ULEX
    NV2OUT -. "hoặc: người copy file thủ công" .-> ULIN
```

Giữa hai module nghiệp vụ vẫn chỉ có **thao tác tay của con người**: Word do
`notary_v2` sinh ra được lưu vào ổ đĩa, và sau đó `upload_lab` quét ổ đĩa đó
như quét bất kỳ Word nào khác — không có tích hợp code giữa chúng. `shell/`
gọi vào từng engine riêng lẻ; nó không tạo luồng dữ liệu `notary_v2` →
`upload_lab`.

## 2. Ai sở hữu dữ liệu gì

Quy tắc chống chồng chéo: mỗi loại dữ liệu có **đúng một** công cụ chủ sở hữu.
Quy tắc này vẫn giữ sau khi gộp DB — dùng chung database **không** có nghĩa là ai
cũng được ghi vào bảng của người khác.

| Dữ liệu | Chủ sở hữu | Ghi chú |
|---|---|---|
| Hồ sơ đang soạn, các bên, tài sản, quan hệ thừa kế | `notary_v2` | `notary.db` |
| Kết quả Cloud OCR giấy tờ + metadata Zalo | `notary_v2` | `notary.db`: `extracted_documents` + các bảng `zalo_*` (`notary_v2/models.py:161-300`); file media ở storage backend. Stack Celery/`ocr_jobs.db` **đã gỡ khi merge** — không còn trong module |
| Word/hợp đồng sinh ra từ template | `notary_v2` | |
| Trường dữ liệu bóc từ kho Word cũ | `upload_lab` | `output/*.json`, `registry.sqlite3` |
| Trạng thái quét/chuẩn bị/upload lên web tỉnh | `upload_lab` | Ví dụ thật: `matched`, `extracted`, `prepared_dry_run`, `uploaded_success` (`upload_lab/batch_scan.py`, `playwright_uploader.py`). Enum nội bộ module — xem `upload_lab/docs/SPEC.md` §2; không phải enum chung xuyên module |
| Session đăng nhập web tỉnh | `upload_lab` | `nd_storage_state.json` |
| Dấu vết thao tác trên máy con | `notaryoffice` | chưa tồn tại |
| Trạng thái/giai đoạn/người đang giữ hồ sơ đang chạy | `notaryoffice` | chưa tồn tại |

**Hôm nay: không công cụ nào đọc DB của công cụ khác.** Đây là trạng thái của
giai đoạn hiện tại, không phải nguyên tắc vĩnh viễn — đích đến là DB dùng chung.

Nhưng cho tới khi việc gộp được thiết kế và duyệt, mọi dữ liệu chéo phải đi qua
một contract thống nhất trước (`contracts/README.md`). **Agent không được tự mở
kết nối đọc DB của module khác** vì "dù sao sau này cũng gộp".

Khi gộp thật: quyền **ghi** vẫn thuộc đúng một chủ sở hữu như bảng trên; các công
cụ khác chỉ **đọc**.

## 3. Chồng chéo đã biết — không phải bug, nhưng phải theo dõi

Ba sản phẩm cùng bóc tách thực thể công chứng và đang có **ba cách làm riêng**:

| Việc | `notary_v2` | `upload_lab` | `notaryoffice` (dự kiến) |
|---|---|---|---|
| Nguồn đầu vào | ảnh giấy tờ | file Word | file Word đang sửa |
| Cách lấy text | Cloud AI OCR | `python-docx` + IFilter | IFilter |
| Bóc trường | regex trong `routers/ocr_ai.py` | regex trong `extract_contract.py` | regex phía Central Hub |

Đây là trùng lặp **có chủ ý ở giai đoạn này** — ba nguồn đầu vào khác nhau về
bản chất, hợp nhất sớm sẽ tạo abstraction sai. Nhưng ba nơi cùng định nghĩa "số
GCN hợp lệ là gì" là rủi ro thật: sửa một nơi, hai nơi kia lệch.

**Cách xử lý đã chốt:** giai đoạn này chưa gộp code, nhưng **bắt buộc thống nhất
định nghĩa thực thể** ở `contracts/entities.md`. Ba module tự implement, cùng tham
chiếu một định nghĩa.

Đây chính là việc quan trọng nhất phải làm đúng từ bây giờ: nếu ba nơi lưu CCCD
theo ba định dạng khác nhau, lúc gộp DB sẽ không join được và phải làm lại toàn
bộ dữ liệu cũ.

## 4. Kiến trúc dự kiến của notaryoffice

Sản phẩm này chưa có code nên toàn bộ mục này là **thiết kế**, không phải hiện
trạng. Nguồn: `notaryoffice/docs/SPEC.md` (Nguồn Chân lý Duy nhất: quyết định
kỹ thuật, 14 bảng DB, Evidence Record, Draft Case — trước đây là `intent.md`).

Mô hình đã chọn: **Hybrid Pipeline — Edge IFilter + Central Processing Hub**

- **Máy trạm (~6 máy):** Sentinel C# .NET 8 siêu mỏng. Bắt file save
  (`ReadDirectoryChangesW`, debounce 3–5 phút), bắt print job (Event ID 307),
  gọi Windows IFilter (`query.dll`) lấy plain text — mục tiêu xử lý cả `.doc` cũ
  và `.docx`; khả năng đọc khi Word đang mở và số đo thời gian vẫn phải kiểm
  chứng trên 6 máy thật (`OPEN_DECISIONS.md` A1). Gửi JSON text
  (20–50KB) về Hub, **không gửi file nhị phân**. Có SQLite FIFO buffer local,
  tự flush khi LAN trở lại.
- **Máy chủ (1 máy/NAS trong văn phòng):** Central Hub — Python FastAPI + DB.
  Lưu `document_snapshots`, tính text diff, chạy regex tất định trên delta, ghép
  print job để phân biệt bản nháp và bản chuẩn ký, dựng Draft Case, phục vụ
  search.
- **Lớp AI:** chỉ vào 10–15% ca mơ hồ (semantic diff, suy luận bàn giao, quét
  hồ sơ chết lâm sàng, dịch câu hỏi tự nhiên thành truy vấn). Phải thay thế
  được, không được giữ trạng thái nghiệp vụ riêng.

Hai tín hiệu xương sống đã chốt:

1. **Word text diff** → biến động thực thể (thêm/sửa CCCD, GCN, thửa/tờ, số
   tiền, diện tích) → cập nhật Case, phát hiện việc phát sinh.
2. **Print spooler** → mức độ hoàn thiện tài liệu. Ý tưởng ban đầu là phân biệt
   `DRAFT_PRINTED` / `FINAL_PRINTED` theo **số bản in** (in 1 bản = soát lỗi; in
   ≥2 bản = bản chuẩn sẵn sàng ký, vì hợp đồng công chứng phải in 3–4 bản).

   ⚠️ **Cách này không dùng được.** Print Spooler **không cung cấp số bản in**
   (`OPEN_DECISIONS.md` A2 — đã chốt = Không). Số bản chỉ suy ra được từ tổng số
   trang, tức là **suy đoán**. Vì vậy phải phân biệt bằng tín hiệu khác: thời
   điểm in so với lần sửa cuối, có sửa file sau khi in hay không, số lần in. Đừng
   thiết kế tính năng nào cần biết chính xác số bản in.

Ba phương án đã **loại bỏ** (đừng đề xuất lại):

- ❌ FileWatcher tập trung trên máy chủ — SMB/NAS trễ, sinh event ảo, không
  định danh được user nào trên máy nào, và bỏ sót 20% file nằm trên ổ máy con.
- ❌ Full edge processing (máy trạm tự diff + tự chạy regex) — biến máy nhân
  viên thành heavy client, và mỗi lần sửa regex phải đi cài lại 6 máy.
- ❌ Tự động ghép cứng 100% theo điểm ≥90 không cần người xác nhận — trùng tên,
  trùng số thửa giữa các xã dẫn tới ghép nhầm hồ sơ.

## 5. Lộ trình đi tới hệ thống thống nhất

Thứ tự bắt buộc là:

```text
DECIDE → SPEC/CONTRACT → FOUNDATION → MIGRATE → VERIFY/CUTOVER
```

### 5.1. DECIDE — đã chốt desktop shell

Owner đã chọn Electron làm desktop shell đích ngày 14/09/2026 (MIN-50). G1 chỉ
bao gồm `notary_v2` và `upload_lab`; `notaryoffice` là placeholder và `excelTK`
nằm ngoài phạm vi. Repo con tiếp tục sở hữu nghiệp vụ Python.

Runtime cấp hệ thống trước nằm trên nhánh `electron-system-shell`; từ khi gộp
monorepo nó là module `shell/` trên nhánh `consolidate/monorepo` — nhánh
`electron-system-shell` đã xóa sau khi merge. Kế hoạch và gate:
`docs/g1/ELECTRON_G1_PLAN.md`.

### 5.2. SPEC/CONTRACT — trước implementation

POC cũ chỉ là bằng chứng. MIN-64 và contract phải được owner duyệt trước khi mở
consumer production. Bắt buộc tách task publish contract khỏi task implement.

- không tạo dependency runtime giữa các repo;
- không thay production adapter;
- không ghi shape experimental vào `contracts/`;
- không coi kết quả chạy được là quyết định công nghệ đã duyệt.

### 5.3. FOUNDATION/MIGRATE — lát cắt chạy được

MIN-65/MIN-67 dựng shell/navigation; MIN-69 chuyển Upload/Audit; MIN-68 chuyển
toàn bộ `notary_v2` được chọn trong inventory. Mỗi lát cắt phải chạy engine thật,
có parity, packaged smoke và rollback. Business rules, quyền ghi và bước người
dùng xác nhận không đổi chỉ vì đổi UI shell.

### 5.4. VERIFY/CUTOVER — rồi mới loại legacy

G1 chuẩn hóa model/identity/provenance/ownership nhưng giữ DB vật lý hiện có sau
adapter. Chọn DB chung là G2/ADR riêng sau khi model ổn định. Điều kiện để không
phải viết lại:

- khóa định danh đã thống nhất;
- cùng một việc không có hai công nghệ production không chủ ý;
- không dùng tính năng riêng của SQLite ở tầng nghiệp vụ;
- ID không trùng giữa các nguồn;
- mỗi loại dữ liệu vẫn có đúng một chủ sở hữu quyền ghi.

Điều kiện chặn mọi bước tích hợp production: cả hai bên phải đồng ý một contract
ghi ở `contracts/` **trước khi** viết code tích hợp. Không agent nào được tự tạo
contract rồi tự implement trong cùng một task.

## 6. Ranh giới hội tụ và shape experimental

**Trạng thái:** Electron đã được chọn làm shell đích ngày 14/09/2026; contract
production `desktopcommand.v1` + `g1.module.v1` đã APPROVED và có runtime thật
trong `shell/`. DB engine chung vẫn chưa được duyệt (MIN-63 backlog); shape
`v0.experimental` chỉ là bằng chứng POC. POC conversion có code trong repo
(`notary_v2/tools/document_conversion_poc/`, `upload_lab/poc/conversion_benchmark/`);
chưa có bằng chứng đủ để nghiệm thu golden dataset. Snapshot source/giới hạn
kiểm chứng ở `docs/g1/COMPONENT_MAP.md` §2/6.2 (draft MIN-57 đã cancel).

### 6.1. Trạng thái hiện tại và trạng thái dự định

**Hiện tại có trong monorepo:** hai module nghiệp vụ (`notary_v2`,
`upload_lab`) + `shell/` (Electron + sidecar, contract đã duyệt); đặc tả
Evidence/Draft Case ở `notaryoffice`.

Các điểm này được kiểm chứng tại:

- Scope upload: `upload_lab/README.md:3`; dry-run/finalize: `:44-57`;
  UI PySide6: `upload_lab/ui_qt/`; Chromium headed:
  `upload_lab/playwright_uploader.py` (`NamDinhUploaderSession` ~:816).
- Worker/signals/thread + command queue: `upload_lab/ui_qt/workers.py:60-105,211-240`.
- `notary_v2/docs/platform/document-intake/spec.md`;
  `notary_v2/docs/domains/inheritance/workflow.md`.
- OCR dispatch per-file: `notary_v2/routers/ocr_ai.py` (native DashScope call
  `:381-414`). Chưa có policy gate đã implement; xem §6.5 về các đường gọi khác.
- `notaryoffice/AGENTS.md`; `notaryoffice/docs/SPEC.md` §5.

**POC trong repo (không phải production):** `ConversionEnvelope`/converter/gate
ở `notary_v2/tools/document_conversion_poc/`; harness benchmark ở
`upload_lab/poc/conversion_benchmark/`; POC desktop command ở
`upload_lab/poc/desktop_command/` (tiền thân của `shell/sidecar`, contract
`v0.experimental` — không tương thích ngầm với `desktopcommand.v1`).

**Hiện tại vẫn không có:** Document Router dùng chung, API trực tiếp giữa ba
module nghiệp vụ, database dùng chung, `notaryoffice` runtime. `shell/` chỉ gọi
vào từng engine riêng lẻ qua sidecar.

Riêng `upload_lab`: không có **HTTP server/API surface cho desktop command**
trong app PySide6; UI/worker trao đổi in-process qua Qt signals + command queue
(`upload_lab/ui_qt/workers.py`). Khi chạy qua `shell/`, sidecar
(`shell/sidecar/upload_adapter.py` + `upload_session.py`) là điểm gọi duy nhất
— không gắn vào app PySide6 đang chạy. Điều này không có nghĩa module không gọi
HTTP tới web tỉnh.

**Dự định:** dùng các shape dưới đây để viết spec và POC. Chúng chưa phải
contract production, không cam kết tương thích và không cấp quyền triển khai
tích hợp giữa các module.

### 6.2. Chuỗi trạng thái dữ liệu chung

```text
SOURCE → RAW → NORMALIZED → INFERRED → CONFIRMED
```

| Lớp | Ý nghĩa | Quy tắc quyền ghi |
|---|---|---|
| `SOURCE` | File, ảnh, message hoặc event gốc cùng hash/thời gian/nguồn | Repo thu nhận nguồn sở hữu; không sửa source để che lỗi downstream |
| `RAW` | Text/OCR/event máy thực sự quan sát được cùng provenance | Adapter/provider chỉ tạo kết quả thô; không ghi thành sự thật nghiệp vụ |
| `NORMALIZED` | Giá trị được chuẩn hóa tất định, ví dụ CCCD/GCN theo `contracts/entities.md` | Repo nghiệp vụ sở hữu rule; luôn truy ngược được về RAW |
| `INFERRED` | Candidate, phân loại, confidence hoặc quan hệ do rule/AI suy ra | Không ghi đè RAW/NORMALIZED; phải nêu rule/model và bằng chứng |
| `CONFIRMED` | Business fact được người có thẩm quyền xác nhận; trạng thái kỹ thuật có thể do system-of-record xác nhận | Chỉ repo chủ sở hữu loại dữ liệu đó được ghi; giữ liên kết về bằng chứng |

Các bất biến:

1. Không đi thẳng từ OCR/LLM tới database truth.
2. Sửa normalization/inference không được xóa raw hoặc provenance cũ.
3. Dữ liệu thiếu bằng chứng phải ghi `unknown`/warning, không tự điền theo suy
   đoán.
4. OCR/LLM không được tạo `CONFIRMED` business fact; con người xác nhận cuối.

### 6.3. Ownership xuyên module

| Phạm vi | Owner nghiệp vụ/quyền ghi | Consumer được phép |
|---|---|---|
| Ảnh/Zalo, OCR giấy tờ, Stage và Case Workspace hiện hành | `notary_v2` | `shell/` đọc/ghi qua `notary_adapter` (contract v1); module khác chỉ đọc sau contract production |
| Kho Word cũ, extraction, registry và upload lifecycle | `upload_lab` | `shell/` gọi qua `upload_adapter` (contract v1); module khác chỉ đọc sau contract production |
| Workstation event, Evidence Record, Draft Case và trạng thái công việc dự định | `notaryoffice` | Chưa có runtime; owner chỉ là thiết kế |
| Vocabulary, shape xuyên sản phẩm và versioning | docs gốc repo này | Chỉ quản trị tài liệu; không sở hữu runtime hay dữ liệu nghiệp vụ |
| Electron shell cấp hệ thống | `shell/` | Sở hữu shell/lifecycle/navigation; không sở hữu nghiệp vụ — ghi DB engine chỉ qua adapter đã duyệt |

Dùng chung database sau này không thay đổi owner quyền ghi. `ConversionEnvelope`
không biến converter thành owner của Evidence/Case; Evidence không cho phép
`notaryoffice` ghi vào bảng Case Workspace của `notary_v2`.

### 6.4. `DesktopCommand v0.experimental` — ĐÃ HẾT HẠN

`v0.experimental` đã được thay bằng **`desktopcommand.v1` APPROVED** tại
[`contracts/desktop-command.md`](./contracts/desktop-command.md) — shape mới
không tương thích ngầm (status `completed`→`succeeded`, thêm
`progress/waiting_on/file_ref`). Implementation thật: `shell/sidecar/`. Mục này
giữ lại làm lịch sử thiết kế.

Mục đích ban đầu: kiểm chứng một desktop shell có thể gửi intent tới backend
Python mà không biết internals của `upload_lab`.

Shape tối thiểu của request:

```text
contract_version = "v0.experimental"
command_id        = UUID
command           = start_upload | cancel_upload | scan_document | get_status
requested_at      = ISO-8601 có múi giờ
payload           = object theo command
```

Shape tối thiểu của response/job:

```text
command_id
job_id
status     = accepted | waiting_user | running | failed | completed | canceled
updated_at = ISO-8601 có múi giờ
result     = object | null
error      = { code, message, retryable } | null
```

Ranh giới: UI chỉ gửi lệnh và hiển thị trạng thái; Python vẫn sở hữu session,
business logic, browser thread và Chromium headed. Không gửi credential, cookie
hoặc nội dung hồ sơ qua log/diagnostics. POC không tạo API production.

Transport POC và bảo mật được chốt tại `TECH_STACK.md` §1.1: server loopback
tối thiểu trong POC, khởi động riêng, không đụng app PySide6 đang chạy.
Shape ở đây độc lập với transport; queue hiện hành chỉ là điểm tham chiếu
semantics, không phải API có sẵn (`upload_lab/ui_qt/workers.py:83-105,211-240`).
Trạng thái job experimental không phải enum registry nội bộ của `upload_lab`.

### 6.5. `ConversionEnvelope v0.experimental`

Mục đích: mọi converter có thể trả nội dung trung gian cùng provenance mà parser
nghiệp vụ không phụ thuộc trực tiếp vào một thư viện.

```text
ConversionEnvelope
├── contract_version = "v0.experimental"
├── source
│   ├── source_id
│   ├── sha256
│   ├── media_type
│   └── size_bytes
├── converter
│   ├── name
│   ├── version
│   └── config_fingerprint
├── content
│   ├── format = markdown | text
│   └── value
├── segments[]
│   ├── segment_id
│   ├── text
│   └── source_ref
├── ocr_calls[]
│   ├── provider / model / input_hash
│   ├── status / duration_ms
│   └── error
├── warnings[]
└── errors[]
```

`source_ref` chỉ ghi vị trí converter thực sự chứng minh được: page cho PDF,
sheet/cell/range cho XLSX, paragraph/table/relationship cho DOCX. Trang Word
không ổn định theo file DOCX nên không được bịa page number. Khi adapter không
có location đủ tin cậy, ghi `null` kèm warning.

Document Router và OCR gate thuộc orchestration của repo gọi converter:

```text
file
├── PDF có text / DOCX / XLSX ── local conversion
├── .doc cũ ─────────────────── Windows IFilter hiện hành
└── PDF scan / ảnh giấy tờ ──── policy gate ── Qwen nếu được phép
```

OCR gate phải ghi policy/version, lý do cho phép, provider/model được phép và
input hash. Converter hoặc plugin không được tự chọn gửi ảnh nhúng ra cloud.

Điểm chèn tham chiếu ở §6.1 chỉ bao phủ đường `_process_single_image`. Source
còn gọi native OCR ở nhánh tài sản, xoay lại và crop
(`notary_v2/routers/ocr_ai.py:2501,2514,2541`). POC phải chứng minh mọi lần gửi
cloud, kể cả retry/crop/ảnh nhúng, đều nằm trong policy được cấp phép; không
coi gate ở một entrypoint là đã bảo vệ toàn bộ các đường gọi.

### 6.6. Evidence/Domain mapping experimental

`ConversionEnvelope` là bằng chứng kỹ thuật đầu vào, **không phải** Evidence
Record hay Case. Mapping dự định:

```text
SOURCE
  → ConversionEnvelope/RAW
  → extracted facts/NORMALIZED
  → Evidence Record
  → candidate link hoặc Draft Case/INFERRED
  → người dùng xác nhận
  → CONFIRMED state của owner
```

`notaryoffice` sở hữu Evidence Record/Draft Case dự định; `notary_v2` vẫn sở hữu
Case Workspace hiện hành; `upload_lab` vẫn sở hữu registry/upload lifecycle.
Evidence chưa ghép được phải được giữ, không bị loại chỉ vì chưa suy ra Case.

### 6.7. Versioning và đường nâng cấp

- Ba shape trên do `systemdocs` quản trị ở mức vocabulary; runtime owner vẫn là
  repo nghiệp vụ trong bảng 6.3.
- `v0.experimental` được phép breaking change. Mỗi POC phải ghi exact revision
  hoặc issue snapshot đã dùng.
- Không đặt shape vào `contracts/` và không tạo shared package ở giai đoạn này.
- Muốn nâng thành `v1`: hai producer/consumer phải duyệt semantics, error model,
  owner và compatibility; sau đó tạo file trong `contracts/` bằng một task spec
  riêng. Implementation phải là task khác.

### 6.8. Golden dataset chung cho POC

Golden dataset không dùng hồ sơ thật chưa khử dữ liệu. Chỉ dùng dữ liệu tổng hợp
hoặc đã thay toàn bộ định danh; tuyệt đối không có API key, cookie, account hay
ảnh CCCD thật.

| ID | Loại mẫu | Route mong đợi | Provenance tối thiểu |
|---|---|---|---|
| GD-01 | PDF có text | local | page |
| GD-02 | PDF scan | OCR gate → Qwen khi được phép | page + input hash + OCR call |
| GD-03 | DOCX có đoạn/bảng/ảnh nhúng | text local; ảnh chỉ qua OCR gate | paragraph/table/relationship hoặc warning |
| GD-04 | XLSX nhiều sheet/cell/ảnh | cell local; ảnh chỉ qua OCR gate | sheet + cell/range |
| GD-05 | `.doc` cũ | Windows IFilter | file hash + warning nếu không có vị trí |
| GD-06 | Ảnh giấy tờ tổng hợp | OCR gate → Qwen khi được phép | input hash + OCR call |
| GD-07 | File hỏng/không hỗ trợ | lỗi có cấu trúc, không crash batch | error + source hash |

Manifest của mỗi mẫu phải có `sample_id`, SHA-256, media type, mức nhạy cảm,
route mong đợi, facts/text mong đợi và provenance tối thiểu. POC chỉ đạt khi so
được chất lượng, thời gian, lỗi, partial failure và không có cloud call ngoài
route đã duyệt.

Đây là tiêu chuẩn cho bộ mẫu/manifest. Code test/harness bước đầu đã có trong
repo (`upload_lab/poc/conversion_benchmark/`), nhưng chưa chứng minh đủ
GD-01–07, expected facts và provenance (`docs/g1/COMPONENT_MAP.md` §6.2).
Duyệt MIN-50 cho POC không phải xác nhận
POC/golden dataset đã đạt; report kỹ thuật chỉ ghi `review_required`, không thay
quyết định của người duyệt.

## 7. Kiến trúc đích — mức ownership & vocabulary

**Dự định, không phải thiết kế vật lý hay lệnh migration:** một hệ thống dùng
chung một database, ba công cụ là ba đường xử lý. Lựa chọn DB theo
`TECH_STACK.md` §3; chưa chốt engine cho DB đích.

- Mỗi bảng có đúng một owner ghi theo phạm vi §6.3. Công cụ khác chỉ đọc qua
  contract đã duyệt; dùng chung DB không cấp quyền ghi chéo.
- Chuẩn hóa tham chiếu theo `contracts/entities.md`, phân biệt định danh
  **người**, **giấy chứng nhận/tài sản** và **hồ sơ**. Không có một thứ bậc khóa
  dùng thay thế lẫn nhau cho cả ba loại.
- CCCD, serial GCN và thửa/tờ/địa phương là bằng chứng để tìm ứng viên hồ sơ,
  không phải khóa chính của Case. Một người hoặc tài sản có thể xuất hiện trong
  nhiều hồ sơ; trùng các giá trị này không đủ để tự gộp hồ sơ.
- Số công chứng là tham chiếu khi đã có, phải xét phạm vi sổ/đơn vị/năm và
  provenance. Trước khi có số, chưa chốt một business key chung duy nhất.

Hai ngữ cảnh cần nối nhưng không được đồng nhất tên gọi:

- `notary_v2`: aggregate soạn thảo hiện có `InheritanceCase`, bảng
  `inheritance_cases` (`notary_v2/models.py:83-103`).
- `notaryoffice`: aggregate theo dõi công việc **dự kiến**, bảng `cases` và
  quan hệ `case_entities` M:N (`notaryoffice/docs/SPEC.md` — mục 14 bảng DB,
  `case_entities` ~:461).

Đây là hai aggregate ở hai bounded context có thể cùng liên quan tới một hồ sơ
nghiệp vụ. Chưa chứng minh cardinality giữa chúng, không mặc định 1:1; quan hệ
M:N trong thiết kế `case_entities` cũng không chứng minh cardinality xuyên repo.
Ở mức vocabulary, chỉ cam kết cùng nghĩa của tham chiếu và khả năng xây dựng
liên kết có bằng chứng, không cam kết join trực tiếp hay hợp nhất bảng.

Không ép dùng chung ID ngay, cũng không cấm canonical ID/mapping sau này.
Schema gộp, khóa liên kết cuối cùng, migration và cutover thuộc thiết kế vật lý
được duyệt sau; điều kiện CONSOLIDATE giữ tại §5.4. Các câu hỏi máy thật còn mở
ở `OPEN_DECISIONS.md` A1/A3/A4 không được coi là đã giải quyết bởi mục này.

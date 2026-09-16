# MIN-62 — Draft contract dữ liệu chung

> **Trạng thái: DRAFT — chờ duyệt.**
>
> Tài liệu này là bản nháp ngoài `contracts/` để kiểm tra khả năng hội tụ giữa
> `notary_v2`, `upload_lab` và `notaryoffice`. Nó chỉ chốt vocabulary, ownership
> và quy tắc tương thích; chưa phải production contract, package, migration hay
> schema cơ sở dữ liệu. Không có code consumer nào được suy ra từ tài liệu này.

## 1. Phạm vi và nguyên tắc

MIN-62 trả lời bốn câu hỏi:

1. Dữ liệu dùng chung có nghĩa gì và nằm ở lớp nào của pipeline?
2. Repo nào được phép ghi từng loại dữ liệu; repo khác đọc bằng cách nào?
3. Làm sao giữ raw value, normalized value, suy luận và xác nhận của người
   thành các trạng thái khác nhau?
4. Một consumer có thể nâng cấp hoặc từ chối envelope mà không làm hỏng
   consumer còn lại như thế nào?

Không nằm trong phạm vi: chọn database engine, thiết kế bảng vật lý, canonical
Case ID, transport production, package distribution, chọn converter/OCR provider
hoặc chuyển code giữa các repo. Các quyết định đó vẫn mở ở
`OPEN_DECISIONS.md` và các issue MIN-61/MIN-63/MIN-64.

Nguyên tắc nền:

```text
SOURCE → RAW → NORMALIZED → INFERRED → CONFIRMED
```

* `RAW` là những gì nguồn hoặc máy quan sát được, không sửa mất dữ liệu gốc.
* `NORMALIZED` là cùng dữ liệu sau khi chuẩn hóa định dạng/khóa nhận dạng.
* `INFERRED` là kết quả parser, OCR, ranking hoặc rule; luôn phải trỏ về
  evidence đầu vào.
* `CONFIRMED` chỉ được tạo khi actor có thẩm quyền xác nhận; AI/OCR không tự
  biến thành sự thật nghiệp vụ.

`notaryoffice` đã mô tả Evidence Record là quan sát khách quan có nguồn gốc và
thời điểm (`notaryoffice/intent.md:143-159`). Nhánh upload hiện có các trạng
thái nghiệp vụ riêng và không được đổi tên chỉ để khớp vocabulary chung; enum
đầy đủ được giữ ở docs của repo đó (`upload_lab_repo/README.md:28` là follow-up
do còn stale).

## 2. Vocabulary chung

### 2.1 IdentityEvidence

`IdentityEvidence` là một mẩu bằng chứng dùng để so khớp người, tài sản hoặc hồ
sơ. Nó **không phải** khóa chính của Case và không tự tạo quan hệ sở hữu.

| Trường | Bắt buộc | Ý nghĩa |
|---|---:|---|
| `evidence_id` | Có | ID bất biến trong phạm vi producer; không dùng làm Case ID chung. |
| `subject_type` | Có | `person`, `property` hoặc `case`. |
| `kind` | Có | `cccd`, `gcn_serial`, `land_parcel`, `map_sheet`, `notary_number`, `locality` hoặc loại đã được duyệt khác. |
| `raw_value` | Có | Giá trị đọc/nhập nguyên dạng; có thể chứa lỗi OCR. |
| `normalized_value` | Có nếu chuẩn hóa được | Giá trị theo `contracts/entities.md`; nếu chưa đủ chắc thì để `null`. |
| `source_ref` | Có | Con trỏ tới `Evidence`/`ConversionEnvelope` và đoạn/trang/cell tương ứng nếu có. |
| `observation_state` | Có | `observed`, `normalized`, `inferred` hoặc `confirmed`. |
| `confidence` | Có khi là máy suy ra | Điểm hoặc bucket do producer định nghĩa; không được hiểu là xác nhận pháp lý. |
| `observed_at` | Có | Thời điểm quan sát theo ISO-8601. |

Thứ tự ưu tiên hiện hành để matching là: CCCD → serial GCN → số công chứng →
thửa/tờ/địa phương → số vào sổ. Đây là thứ bậc bằng chứng, không phải thứ tự
để sinh một ID mới. Chuẩn serial GCN và CCCD đang được `notaryoffice` mô tả tại
`notaryoffice/intent.md:323-328`.

Các quy tắc bắt buộc:

* Không ghi đè `raw_value` bằng `normalized_value`.
* Một giá trị không nhận dạng được vẫn giữ `raw_value`, `source_ref` và trạng
  thái `observed`; không bịa `normalized_value`.
* `cccd`, `land_parcel` và `map_sheet` là matching evidence của người/tài sản,
  không phải Case PK.
* `notary_number` chỉ trở thành bằng chứng liên kết mạnh sau khi có số công
  chứng; trước đó matching có thể dùng CCCD/thửa-tờ nhưng phải ghi rõ trạng thái.

### 2.2 Hai bounded context cho Case

`notary_v2` có aggregate `InheritanceCase` phục vụ soạn thảo hồ sơ; hiện model
đang liên kết người, tài sản và participant (`notary_v2/models.py:99-103`).
`notaryoffice` mô tả aggregate `case` phục vụ theo dõi công việc, artifacts và
timeline (`notaryoffice/intent.md:338-381`). Hai aggregate này cùng nói về một
thực thể nghiệp vụ có thể liên quan, nhưng **không mặc định 1:1** và không hợp
nhất thành một bảng vocabulary ở giai đoạn này.

Mỗi context giữ bảng/ID nội bộ của mình. Liên kết tạm thời dùng tập
`IdentityEvidence` đã chuẩn hóa và source refs; nếu không đủ bằng chứng thì
trạng thái phải là `unmatched`/`review_required`, không tạo shared ID đoán mò.
Canonical Case ID, cardinality và quy trình merge là quyết định CONSOLIDATE
riêng, chưa được chốt trong MIN-62.

### 2.3 ConversionEnvelope `v0.experimental`

Envelope là kết quả chuyển đổi một source thành nội dung trung gian và metadata
để consumer tiếp tục phân tích. Converter **không** là owner nghiệp vụ.

Shape tham chiếu (giữ trong tài liệu này cho tới khi được duyệt; không tạo file
trong `contracts/`):

```yaml
contract_version: v0.experimental
source:
  source_id: sha256:<digest>
  sha256: <digest>
  media_type: application/pdf
  size_bytes: 12345
created_at: 2026-09-11T00:00:00Z
converter:
  name: markitdown | upload_lab_ifilter | other
  version: <producer-version>
  config_fingerprint: <stable-config-id>
content:
  format: markdown | text
  value: <intermediate-content>
segments:
  - segment_id: <stable-within-envelope>
    text: <segment-text>
    source_ref: {page: 1} # null khi converter chưa chứng minh được vị trí
ocr_calls: []
warnings: []
errors: []
```

Các field trên bám POC đã có: `contract_version`, source hash/media type,
converter, content, segments, OCR calls, warnings và errors
(`notary_v2/.worktrees/markitdown-qwen-poc/tools/document_conversion_poc/models.py:11-145`).
POC hiện cố ý để `source_ref: null` cho local conversion và gắn page ref cho
đầu vào OCR (`notary_v2/.worktrees/markitdown-qwen-poc/tools/document_conversion_poc/converter.py:67-78,93-135`); vì vậy provenance chưa được
coi là đầy đủ chỉ vì envelope có field này.

Quy tắc envelope:

* `source.sha256` là khóa bất biến để deduplicate; không dùng đường dẫn file
  làm identity vì đường dẫn có thể đổi.
* `segments` giữ thứ tự producer phát hiện. Mỗi segment phải có `source_ref`
  nếu producer chứng minh được vị trí; `null` là giá trị hợp lệ và phải kèm
  warning phù hợp.
* `ocr_calls` chỉ ghi lần gọi đã được policy cho phép, provider/model, input
  hash, attempt, trạng thái, lỗi và policy version; không ghi credential.
* `errors` là lỗi có cấu trúc (`code`, `message`, `retryable`); message không
  được dùng làm mã ổn định.
* `warnings` không làm envelope thành confirmed; consumer phải quyết định có
  cho phép tiếp tục hay đưa vào review.

### 2.4 Evidence và DraftCase

`Evidence` là bản ghi quan sát độc lập với việc đã gắn vào Case nào. Producer
phải có thể gửi Evidence ngay cả khi chưa match được Case; đây là yêu cầu
explicit trong kịch bản `UNCLASSIFIED` của `notaryoffice`
(`notaryoffice/intent.md:132-137`).

Mapping tối thiểu:

```text
source/desktop event
    ↓
ConversionEnvelope (nếu có chuyển đổi tài liệu)
    ↓
Evidence {raw, source_ref, observed_at, producer}
    ↓
IdentityEvidence[] / extracted facts
    ↓
DraftCase hoặc link tới bounded-context Case
    ↓
human confirmation → Confirmed fact
```

`DraftCase` là candidate do matching/inference tạo ra, không phải Case đã được
chấp nhận. Nó phải giữ các Evidence đã gom, lý do ranking, trạng thái
`UNCLASSIFIED` hoặc `review_required` khi chưa đủ bằng chứng và không được xóa
Evidence chỉ vì chưa hiểu ý nghĩa.

## 3. Ownership và quyền ghi

| Dữ liệu | Producer/owner ghi | Consumer được phép | Ràng buộc |
|---|---|---|---|
| Source metadata + hash | Connector nhận file/sự kiện | Converter, Evidence builder, audit | Bất biến sau khi ghi. |
| ConversionEnvelope | Adapter chuyển đổi của repo sở hữu | Extractor, harness, Evidence builder | Không ghi Case/business tables. |
| OCR call/audit | OCR gateway của repo chạy policy | Review/audit | Không credential; cloud phải được gate cho phép. |
| Evidence | Pipeline Evidence của bounded context nhận quan sát | Matching, review, timeline | Append-only về mặt ngữ nghĩa; sửa dùng correction event. |
| IdentityEvidence | Extractor/normalizer; producer giữ raw | Matching của các context | Không tự sinh Case ID. |
| DraftCase | Bounded context quản lý workflow | UI/reviewer và context được cấp quyền đọc | Chưa phải confirmed Case. |
| InheritanceCase | `notary_v2` | Adapter/read model theo contract | ID nội bộ; không bị consumer khác ghi trực tiếp. |
| Work-tracking Case | `notaryoffice` khi có runtime | Review/timeline consumers | Hiện `notaryoffice` chưa có code; chỉ là dự định. |
| Upload job/status | `upload_lab` | Desktop UI/diagnostics | Giữ enum nội bộ thật của repo; không ánh xạ cưỡng bức thành Evidence state. |

POC DesktopCommand hiện là sidecar FastAPI localhost riêng, có `/healthz`,
`/v0/commands` và `/v0/jobs/{job_id}` (`upload_lab_repo/.worktrees/desktop-command-poc/poc/desktop_command/server.py:9-90`). Registry POC giữ job in-memory, kiểm tra
version, command, idempotency và cấm field nhạy cảm
(`upload_lab_repo/.worktrees/desktop-command-poc/poc/desktop_command/registry.py:21-75`). Điều này chỉ chứng minh boundary command tối thiểu;
không biến sidecar thành owner database hay production API.

## 4. Unknown, null và lỗi

| Tình huống | Cách biểu diễn | Không được làm |
|---|---|---|
| Không quan sát được | `null` + `warning`/`source_ref` phù hợp | Điền chuỗi rỗng như dữ liệu thật. |
| Quan sát được nhưng chưa chuẩn hóa | `raw_value` + `normalized_value: null`, state `observed` | Đoán giá trị chuẩn. |
| Chuẩn hóa thất bại | giữ raw + `error.code` ổn định | Nuốt lỗi hoặc coi là confirmed. |
| Một phần thành công | các segment/call thành công + `warnings`/error retryable | Báo completed toàn bộ mà không nêu phần thiếu. |
| Không được phép gọi cloud | `warning: cloud_not_authorized`, không có `ocr_call` | Tự fallback sang cloud khác. |
| Không match Case | Evidence vẫn được ghi; DraftCase `UNCLASSIFIED`/`review_required` | Loại bỏ ảnh/tài liệu. |

Mã lỗi tối thiểu dùng snake_case, có namespace khi cần (`conversion.*`,
`ocr.*`, `matching.*`). Producer có thể thêm mã mới nhưng không đổi nghĩa mã đã
phát hành; consumer không được parse message tự do để phân nhánh.

## 5. Provenance, idempotency và bảo mật

Mỗi kết quả phải truy ngược được theo chuỗi:

```text
source.sha256 → envelope → segment/source_ref → evidence → identity/fact
```

`source_ref` có thể gồm `page`, `sheet`, `cell`/`range`, paragraph/table hoặc
`evidence_excerpt`. Khi format không có khái niệm page ổn định (ví dụ DOCX),
producer dùng locator ổn định nhất có thể và ghi limitation thay vì hứa “trang
N”.

Idempotency:

* Conversion lặp cùng `source.sha256 + converter.version + config_fingerprint`
  phải cho kết quả có thể so sánh; nếu không deterministic phải ghi lý do.
* OCR call deduplicate theo `source.sha256`/input hash, model, policy version
  và attempt; retry không được tạo Evidence trùng mà không có liên kết.
* Evidence append-only về mặt nghiệp vụ; correction tạo bản ghi mới trỏ bản ghi
  cũ.
* Command POC dùng `command_id` để trả lại job cũ khi retry, như registry đang
  làm (`upload_lab_repo/.worktrees/desktop-command-poc/poc/desktop_command/registry.py:46-53`).

Không transport nào được đưa credential vào envelope/command payload. Token
sidecar chỉ dùng trong POC local; transport production và phân quyền là quyết
định riêng. Không ghi raw tài liệu hoặc ảnh vào log nếu không có policy lưu trữ.

## 6. Version và compatibility policy

`v0.experimental` là version thử nghiệm, không cam kết backward compatibility.
Trong giai đoạn này:

1. Producer luôn phát `contract_version` và metadata converter.
2. Consumer phải kiểm tra major/version trước khi đọc; version không hỗ trợ thì
   trả `unsupported_contract_version` hoặc đưa item vào `review_required`.
3. Thêm field là backward-compatible nếu consumer bỏ qua được; đổi nghĩa hoặc
   đổi kiểu field phải tăng version.
4. Không xóa field đang dùng trong cùng version; deprecate ít nhất một chu kỳ
   review và ghi migration note.
5. Golden fixtures phải kiểm tra route, status, text/facts, provenance và lỗi;
   thiếu expected field không được tính là pass. Harness POC hiện đã giữ các
   expected fields và trả `decision: review_required` thay vì tự adopt
   (`notary_v2/.worktrees/markitdown-qwen-poc/tools/document_conversion_poc/harness.py:76-90,108-114,155-165,210-224`).

### 6.1. Golden revision không đồng nghĩa cùng mã mẫu

Hai POC hiện có cùng mã GD-01..07, loại mẫu canonical và route
`ocr_candidate`, nhưng manifest/fixture vẫn do từng repo sở hữu và SHA-256 chưa
giống nhau. Việc mỗi harness chạy đủ 7 mẫu chỉ chứng minh tính đầy đủ nội bộ,
không chứng minh parity xuyên repo.

Gate dataset revision chung chỉ đạt khi một manifest/hash artifact bất biến được
chủ sở hữu công bố, cả hai consumer kiểm tra cùng SHA-256 và report ghi rõ revision
đó. Artifact có thể được copy/pin trong từng POC để tránh runtime dependency; không
được coi là shared production contract cho tới khi Gate A được duyệt và Gate B có
issue riêng. Cho tới lúc đó, MIN-61 phải giữ kết luận `ITERATE` và không mở ADOPT.

Chỉ sau khi MIN-61 được owner quyết định và MIN-54/MIN-57 được duyệt mới được
copy shape này vào `contracts/`, chốt version production và mở issue consumer.

## 7. Kế hoạch triển khai sau khi duyệt

### Gate A — Duyệt semantics (MIN-62)

* Owner xác nhận bảng vocabulary, thứ bậc IdentityEvidence, phân biệt hai Case
  context và các quy tắc null/error/provenance.
* Owner xác nhận đây là contract tài liệu, chưa phải schema DB hay package.
* Ghi lại các mục còn mở: canonical Case ID, DB engine, runtime owner,
  distribution, production UI transport, A1/A3/A4 của `notaryoffice`.

**Đầu ra:** bản Markdown được duyệt; chưa merge vào `contracts/` trong cùng
task nếu chưa có quyết định explicit.

### Gate B — Publish contract và fixtures

Sau Gate A, hai issue riêng mới được phép chạy song song:

1. **MIN-72** chuyển shape được owner duyệt từ draft vào `contracts/`, thêm
   JSON/YAML examples hợp lệ, null/unknown/error, invalid examples và policy
   compatibility/migration;
2. **MIN-70** tạo golden fixture revision có hash/changelog và validator/
   conformance check trong repo owner đã được chỉ định, không thêm runtime vào
   `systemdocs`.

MIN-70 không tự publish contract; MIN-72 không tự chọn byte artifact. Cả hai
đều bị chặn bởi Gate A và không mở consumer production trong cùng task.

### Gate C — Consumer adoption theo repo sở hữu

* `notary_v2`: adapter `ConversionEnvelope → Evidence/IdentityEvidence`, giữ
  OCR gate và database owner hiện tại; không rewrite inheritance business logic.
* `upload_lab`: adapter đọc envelope hoặc xuất dữ liệu theo contract trong
  command/upload flow; giữ parser nghiệp vụ và enum trạng thái thật.
* `notaryoffice`: khi bắt đầu code, Evidence/DraftCase pipeline phải dùng cùng
  vocabulary; Sentinel/Hub chỉ ghi dữ kiện thuộc owner của nó.

Các lát cắt này tương ứng các issue ADOPT MIN-68/MIN-69 và task notaryoffice
riêng; chúng chỉ mở sau MIN-70, MIN-72 và các spec blocker liên quan được duyệt.
Không tạo shared runtime package trước khi có hai consumer thật và quyết định
distribution.

### Gate D — Database/UI/consolidate

MIN-63 mới quyết định ownership mapping và migration cho database chung. MIN-64
mới quyết định Desktop UI contract production. Chỉ sau khi hai boundary ổn định
mới đánh giá schema gộp, cutover hoặc monorepo theo điều kiện CONSOLIDATE ở
`SYSTEM_ARCHITECTURE.md:196-210`.

## 8. Checklist nghiệm thu

- [ ] Mỗi thuật ngữ có semantics, producer/owner và consumer rõ ràng.
- [ ] Raw/normalized/inferred/confirmed không bị trộn.
- [ ] CCCD/thửa-tờ/serial được coi là evidence matching, không phải Case PK.
- [ ] Hai aggregate Case không bị giả định 1:1 hoặc ép chung bảng.
- [ ] Envelope có source hash, converter version, segments, provenance,
      OCR audit, warning và error.
- [ ] Unknown/null/partial/failure/retryable có ví dụ và hành vi rõ.
- [ ] Version/compatibility/idempotency policy có điểm kiểm thử.
- [ ] Golden harness có expected fields và không tự quyết định adopt.
- [ ] Không có credential trong payload/log.
- [ ] Không tạo file trong `contracts/`, package runtime, DB schema hay code
      trong task spec này.
- [ ] Owner của MIN-61, MIN-54 và MIN-57 đã phản hồi; mục mở không bị tự chốt.

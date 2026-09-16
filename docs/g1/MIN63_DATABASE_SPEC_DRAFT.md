# MIN-63 — Draft đặc tả database chung

> **Trạng thái: DRAFT — chờ duyệt.**
>
> Đây là đặc tả quan hệ, ownership và lộ trình migration ở cấp
> `systemdocs`. Không đọc database khách hàng, không chạy migration, không
> tạo schema vật lý và không chọn engine đích thay cho owner. Mọi code
> migration/rehearsal phải là issue riêng trong repo sở hữu database.

## 1. Mục tiêu và ranh giới

Đích kiến trúc là một hệ thống dùng chung database, nhưng mỗi miền dữ liệu vẫn
có đúng một owner ghi. Database chung không cấp cho công cụ khác quyền ghi
chéo. Nguyên tắc này đã được chốt ở kiến trúc cấp cha
(`SYSTEM_ARCHITECTURE.md:65-90,196-210`).

MIN-63 phải trả lời được:

* Hiện có bao nhiêu database/broker/backend, cái nào là nghiệp vụ thật?
* Dữ liệu nào được chuyển, dữ liệu nào chỉ giữ làm archive hoặc reference?
* Mỗi field/domain sau hợp nhất có một write owner nào?
* Mapping identity, collision, duplicate và retry được chứng minh ra sao?
* Có thể backup, restore, rehearsal, cutover và rollback mà không mất
  provenance/confirmation không?

Không nằm trong phạm vi: thay đổi code repo con, đọc dữ liệu production, chốt
PostgreSQL/SQLite, chốt canonical Case ID, xây API production hoặc hợp nhất
ngay các bảng `cases`.

## 2. Inventory hiện trạng (đã kiểm chứng bằng source)

### 2.1 `notary_v2`

* `notary.db` là SQLite được mở qua SQLAlchemy; `DB_PATH` nằm cạnh source và
  engine dùng `sqlite:///...` (`notary_v2/database.py:1-24`).
* Các model nghiệp vụ hiện gồm customers, properties, inheritance cases,
  participants, templates, extracted documents và các bảng Zalo; `OCRJob` là
  bảng `ocr_jobs` trong cùng metadata (`notary_v2/models.py:10-151,161-184,186-314`).
* `ocr_jobs.db` **không phải** database nghiệp vụ: mặc định nó là Celery broker
  và result backend (`notary_v2/celery_app.py:5-11`). Không được nhập file này
  vào business schema.
* Timestamp, migration helper và SQLite foreign-key behavior hiện là chi tiết
  của implementation; migration phải đo và lập mapping, không suy ra semantics
  mới từ tên cột.

### 2.2 `upload_lab`

* `registry.sqlite3` được chọn tương đối theo repo/work directory
  (`upload_lab_repo/batch_scan.py:24-30,143-148`).
* Bảng thật hiện là `file_registry`, có `file_key` unique, path/stat, folder,
  contract number, status, timestamps, error, run/output/artifact fields và
  các index theo contract/status/run (`upload_lab_repo/batch_scan.py:106-140`).
* `file_key` hiện được tính từ resolved path + mtime nanoseconds + size
  (`upload_lab_repo/batch_scan.py:90-92`); đây là identity của lần quét file,
  không được tự coi là identity hồ sơ xuyên repo.
* Upsert giữ các mốc `matched`, `extracted`, `prepared_dry_run`,
  `uploaded_success` và lỗi/partial; các trạng thái này thuộc upload workflow,
  không phải enum Evidence hay Case chung
  (`upload_lab_repo/batch_scan.py:353-368,705-795`; `playwright_uploader.py:81-83`).

### 2.3 `notaryoffice`

`notaryoffice` hiện chỉ có đặc tả, chưa có runtime. `intent.md` mô tả 14 bảng
dự kiến, trong đó `entities`, `cases`, `case_entities`, `artifacts`, snapshots,
timeline và calibration là vocabulary thiết kế (`notaryoffice/intent.md:330-381`).
Không được coi các bảng đó đã tồn tại hoặc đọc chúng trong migration hiện tại.
Evidence phải được giữ ngay cả khi chưa match Case và có thể tạo Draft Case
`UNCLASSIFIED` (`notaryoffice/intent.md:132-137`).

## 3. Ownership đích ở mức domain

| Domain | Owner ghi hiện tại/định hướng | Consumer khác | Quy tắc khi DB chung |
|---|---|---|---|
| Inheritance draft, participants, properties, templates | `notary_v2` | UI/read adapter | Chỉ `notary_v2` ghi; giữ ID nội bộ hoặc mapping có provenance. |
| OCR job/result và Zalo metadata | `notary_v2` | Evidence/review | Nhập từ `notary.db`; loại `ocr_jobs.db` broker/backend. |
| Legacy file registry, extraction/upload workflow | `upload_lab` | Desktop UI, audit | Không đổi enum nội bộ để “đẹp” hơn; mapping qua adapter. |
| Evidence/observation stream | Context tiếp nhận quan sát của record đó; phân vùng owner cụ thể chốt ở Gate A | Matching, review | Mỗi record chỉ có một owner ghi; không cross-write. Append-only về ngữ nghĩa. |
| Work-tracking Case, artifacts, timeline | `notaryoffice` khi runtime tồn tại | `notary_v2`/upload read model | Chưa migrate bảng vật lý trước khi A1/A3/A4 và intent được duyệt. |
| Shared identity vocabulary | contract owner được chỉ định ở Gate A | tất cả consumer | Không tự sinh Case PK từ CCCD/thửa-tờ. |

Nếu một domain có hơn một ứng viên owner, migration bị dừng ở discovery; không
giải quyết bằng cách cho cả hai repo cùng ghi.

## 4. Identity mapping và collision policy

### 4.1 Khóa nguồn và khóa liên kết

Mỗi record chuyển đổi phải giữ bộ khóa nguồn tối thiểu:

```text
source_system + source_store + source_record_type + source_record_id
             + source_revision + observed_at
```

Đây là địa chỉ truy nguyên, không phải canonical ID mới. `sha256` của source
file dùng để deduplicate artifact/conversion; `file_key` của upload_lab chỉ là
khóa lần quét (xem §2.2).

Identity matching dùng `IdentityEvidence` theo MIN-62:

```text
CCCD → serial GCN → số công chứng → thửa/tờ/địa phương → số vào sổ
```

Thứ bậc này là sức mạnh bằng chứng, không phải thứ tự ghép khóa. CCCD/thửa-tờ
có thể xuất hiện ở nhiều hồ sơ; trùng giá trị không đủ để tự gộp. Hai aggregate
`InheritanceCase` và work-tracking `cases` không mặc định 1:1
(`SYSTEM_ARCHITECTURE.md:436-469`).

### 4.2 Kết quả match

| Kết quả | Hành động |
|---|---|
| Exact match một ứng viên, bằng chứng đủ và cùng phạm vi | Tạo liên kết có `matched_by`, source refs và revision. |
| Nhiều ứng viên cùng điểm | Không chọn tự động; tạo conflict/review item. |
| Chỉ có raw value hoặc evidence yếu | Giữ raw, để `unmatched`/`review_required`; không tạo Case ID. |
| Không match | Giữ Evidence/DraftCase `UNCLASSIFIED`; không drop artifact. |
| Cùng source record replay | Idempotent theo source address + revision/hash; không nhân bản business fact. |
| Hai source khác nhau cùng normalized value | Ghi nhiều evidence; chỉ merge sau rule/phạm vi và human confirmation. |

Collision report phải đếm theo domain và loại bằng chứng, nêu source refs và
không sửa dữ liệu nguồn. Không dùng row integer của SQLite làm khóa join giữa
repo.

## 5. Mapping hiện tại → đích (không phải schema vật lý)

| Hiện trạng | Đích vocabulary | Cách chuyển | Rủi ro cần đo |
|---|---|---|---|
| `notary_v2.customers/properties` | entity/person/property + IdentityEvidence | Giữ source IDs và raw/normalized; lập mapping evidence | Trùng người/tài sản, thiếu phạm vi. |
| `notary_v2.inheritance_cases` | InheritanceCase context | Giữ aggregate riêng; liên kết Evidence theo contract | Không có số công chứng ở draft. |
| `notary_v2.ocr_jobs` | OCR audit/result của owner | Chuyển result + source hash; bỏ broker metadata | Payload JSON/version/provider khác nhau. |
| `notary_v2` Zalo tables/media refs | Evidence/artifact refs | Giữ media URI/hash và connector provenance | File ngoài DB, retention, quyền truy cập. |
| `upload_lab.file_registry` | ingestion/upload record của upload context | Giữ `file_key` như source key; map status nội bộ | Path/mtime đổi làm key mới; partial/failure. |
| `upload_lab/output/*.json` | Conversion/Evidence input | Import theo file hash + converter revision | JSON thiếu provenance hoặc schema cũ. |
| `notaryoffice` intent tables | Future work-tracking context | Chỉ map sau khi runtime và A1/A3/A4 được duyệt | Đây mới là thiết kế, chưa có rows/schema thật. |

Không migration dữ liệu nào chỉ bằng `INSERT SELECT` dựa trên tên cột. Mỗi dòng
mapping phải có: source revision, transform version, source hash/ID, warning,
quyết định match và người duyệt khi chuyển từ inferred sang confirmed.

## 6. Engine và source of truth

Hiện trạng đều thiên về SQLite nhưng khác file/store và lifecycle. SQLite là
default hiện tại; database đích có thể là PostgreSQL nhưng **chưa được chọn**
(`TECH_STACK.md:122-134`; `SYSTEM_ARCHITECTURE.md:438-440`).

Gate chọn engine (ADR riêng, owner duyệt):

1. Liệt kê query/index/transaction/locking thực tế của từng consumer.
2. Chứng minh workload đồng thời, backup/restore, WAL/replication và đường
   mạng của văn phòng.
3. Đối chiếu type/timezone/JSON/unique constraint và semantics null.
4. Chạy rehearsal trên bản sao synthetic, đo latency và collision; không đụng
   DB khách hàng.
5. Chỉ ghi engine vào `TECH_STACK.md` sau khi owner ký; nếu chưa đạt, giữ
   SQLite hiện trạng và không mở migration production.

Source of truth sau hợp nhất là domain owner, không phải “database mới” tự động.
Read model/cache/broker/result backend không được coi là business truth.

## 7. Provenance, encoding và thời gian

* Mọi record chuyển phải giữ source path/URI nếu có, hash, media type, source
  system, source revision và converter/parser version.
* Raw bytes/text không được normalize phá hủy; encoding lỗi phải là warning/error
  có mã, không thay bằng ký tự đoán.
* Lưu thời gian kèm offset hoặc UTC rõ ràng. `notary_v2` cấu hình Celery timezone
  `Asia/Ho_Chi_Minh` (`notary_v2/celery_app.py:14-19`), trong khi upload `now_iso()` hiện
  tạo timestamp không offset (`upload_lab_repo/batch_scan.py:39-40`); migration phải phân loại
  các giá trị cũ trước khi quy đổi, không âm thầm giả định UTC.
* File/blob lớn giữ ở storage owner; database chỉ giữ reference, hash, size,
  media type và retention metadata. `notaryoffice` intent cũng tách artifact
  path/storage/hash khỏi Case (`notaryoffice/intent.md:375`), nhưng đây vẫn là thiết kế.

## 8. Backup, restore, coexistence và cutover

### 8.1 Trước rehearsal

1. Khóa revision source và manifest metadata; không copy dữ liệu khách hàng vào
   worktree/log.
2. Tạo backup mã hóa theo policy owner và kiểm thử restore vào môi trường cô lập.
3. Chạy inventory chỉ đọc: table/model names, row counts nếu là fixture/synthetic,
   schema version và foreign-key/index metadata.
4. Sinh mapping report và collision report; mọi mismatch là `review_required`.

### 8.2 Rehearsal và coexistence

* Import vào namespace/staging của môi trường rehearsal, với transform version
  và idempotency key.
* So sánh counts/checksums, quan hệ, source refs, trạng thái confirmation và
  sample golden fixtures.
* Cho phép old store và target cùng tồn tại **chỉ ở rehearsal**; production
  dual-write chưa được phép trong MIN-63.
* Chạy read-only shadow queries để đo kết quả mà không đổi owner ghi.

### 8.3 Cutover/rollback gate

Cutover chỉ mở khi owner duyệt engine, mapping, collision threshold, backup
restore, observability và runbook. Runbook tối thiểu phải có:

```text
freeze writes → final manifest/hash → import → verify invariants
→ switch readers by feature flag → monitor → accept hoặc rollback
```

Rollback phải chỉ rõ điểm quay về old owner, dữ liệu phát sinh trong khoảng
chuyển tiếp và cách tránh duplicate khi retry. Nếu verification fail, giữ old
writer/readers và dừng; không “sửa nóng” trên DB thật.

## 9. Kế hoạch triển khai theo gate

### Gate A — Duyệt đặc tả (MIN-63)

Owner duyệt inventory, single-writer matrix, identity/collision policy và các
điểm còn mở (engine, Case ID, A1/A3/A4, retention, permissions). Không đổi
status issue hoặc DB thật trong gate này.

### Gate B — Inventory/rehearsal implementation

Issue riêng trong repo DB-owner thực hiện tool read-only trên fixtures/synthetic:

* export schema metadata, source manifest và revision;
* mapping/collision report;
* backup/restore smoke test;
* conformance với MIN-62 Envelope/Evidence.

Nghiệm thu là report có hash/revision, không phải “đã merge database”.

### Gate C — Engine/migration ADR

Sau khi Gate B có số đo, owner so sánh engine theo checklist §6, chốt source of
truth và mapping vật lý ở ADR riêng. Nếu chưa đủ bằng chứng, giữ nguyên hiện
trạng và ghi blocker; không tự chọn PostgreSQL.

### Gate D — Dry-run rồi mới production

Chỉ khi ADR, backup/restore, collision threshold, permission và runbook được
duyệt mới mở issue cutover. UI/consumer adoption phải đi qua contract, không
cho phép công cụ khác ghi trực tiếp bảng owner.

## 10. Checklist nghiệm thu MIN-63

- [ ] Inventory phân biệt business DB với Celery broker/result backend.
- [ ] `notary.db`, `registry.sqlite3` và 14 bảng `notaryoffice` được đánh dấu
      đúng hiện trạng/dự định, có source revision/citation.
- [ ] Mỗi domain có đúng một write owner; read consumer và boundary rõ.
- [ ] Source key, hash, revision, idempotency và collision policy có ví dụ.
- [ ] CCCD/thửa-tờ không bị dùng làm Case PK; hai aggregate không bị giả định
      1:1.
- [ ] Mapping giữ raw, normalized, inferred/confirmed và provenance.
- [ ] Encoding/timezone/blob-reference có chiến lược và danh sách rủi ro.
- [ ] Engine chưa bị tự chốt; có tiêu chí ADR và evidence cần thu thập.
- [ ] Backup/restore, rehearsal, coexistence, cutover và rollback có gate.
- [ ] Không đọc DB khách hàng, không tạo schema/migration/runtime trong
      `systemdocs`.
- [ ] MIN-62 và MIN-54/MIN-57 được owner duyệt trước khi publish contract hoặc
      mở consumer/migration implementation.

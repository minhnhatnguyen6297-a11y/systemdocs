# MIN-66 — Draft checklist merge-readiness và diễn tập DB chung

> **Trạng thái: DRAFT — chưa phải kết luận sẵn sàng gom repo.**
>
> Tài liệu này chỉ ghi ownership, vocabulary, bằng chứng hiện tại và các gate
> cần kiểm tra. Không có migration, rehearsal script, runtime code, cutover hay
> thay đổi schema trong `systemdocs`. Kết luận cuối phải dựa trên báo cáo của
> repo runtime/DB-owner và được người dùng duyệt.

## 1. Mục đích và phạm vi

MIN-66 là review liên sản phẩm sau ALIGN: kiểm tra ba repo có thể hội tụ về
vocabulary, owner quyền ghi, component boundary, database và UI mà không phải
rewrite business logic chỉ để đổi tổ chức source. Đây là checklist chuẩn bị
cho review; chưa phải bằng chứng rằng monorepo, DB chung hoặc UI chung đã được
triển khai.

Trong phạm vi:

- đối chiếu ownership và vocabulary với `SYSTEM_ARCHITECTURE.md` §6–§7;
- lập ma trận bằng chứng cho contract, provenance, identity, idempotency và
  human confirmation;
- xác định các rehearsal cần chạy trong worktree của repo owner;
- ghi rõ điều kiện đạt, chưa đạt, chưa quan sát và blocker.

Ngoài phạm vi:

- không merge branch, không cutover DB thật, không di chuyển dữ liệu thật;
- không tạo package/contract production trong `contracts/`;
- không chọn Electron/PySide6 hoặc DB engine thay cho decision gate đang mở;
- không sửa bug nhỏ lẻ của repo con.

## 2. Baseline kiến trúc đã có bằng chứng

| Mặt kiểm tra | Bằng chứng hiện tại | Ý nghĩa cho review |
|---|---|---|
| DB nghiệp vụ và hạ tầng | Ownership hiện tại phân biệt `notary.db` với `ocr_jobs.db` tại `SYSTEM_ARCHITECTURE.md:65-90`; bảng OCR/Zalo thuộc `notary_v2` theo `notary_v2/models.py:161-171,186-300`, còn Celery dùng file broker/result tại `notary_v2/celery_app.py:5-11` | Không được coi file broker là DB nghiệp vụ hoặc cấp quyền ghi chéo chỉ vì cùng thư mục |
| Raw → normalized → inferred → confirmed | Ranh giới dữ liệu và human confirmation tại `SYSTEM_ARCHITECTURE.md:260-314` | Rehearsal phải giữ provenance/raw và không biến OCR/LLM thành truth trực tiếp |
| ConversionEnvelope | Shape `v0.experimental`, source hash, converter, segments, OCR calls và warning/error tại `SYSTEM_ARCHITECTURE.md:327-430` | Chỉ là vocabulary thí nghiệm; chưa phải production contract |
| Ownership đích | Topology một DB, ba đường xử lý, một owner ghi mỗi bảng tại `SYSTEM_ARCHITECTURE.md:436-469` | Có thể đánh giá boundary trước khi thiết kế schema gộp |
| UI/engine boundary | UI chỉ gửi command, Python giữ session/browser/OCR tại `SYSTEM_ARCHITECTURE.md:300-325`; POC command queue bám `upload_lab_repo/ui_qt/workers.py:105-117,146-153` | Không được truy cập DB/cookie/browser context trực tiếp từ shell |
| Upload lifecycle | Các giá trị thật `matched`, `extracted`, `prepared_dry_run`, `uploaded_success` tại `upload_lab_repo/batch_scan.py:705-795` và `upload_lab_repo/playwright_uploader.py:81-83` | Không dùng enum display của DesktopCommand để thay registry nội bộ |
| Golden dataset POC | `upload_lab_repo` có manifest/fixture persistent GD-01..GD-07 và SHA-256 riêng tại `upload_lab_repo/poc/conversion_benchmark/golden_manifest.json:1-12`, `upload_lab_repo/poc/conversion_benchmark/golden/`; `notary_v2` có manifest `gd-3` riêng tại `notary_v2/tools/document_conversion_poc/golden_manifest.json:1-16`, với canonical test provenance tại `notary_v2/tests/test_document_conversion_poc.py:452-483` | Hai POC hội tụ mã case/route và vocabulary synthetic, nhưng SHA-256 fixture chưa giống nhau; chưa có shared dataset revision, contract production hay DB rehearsal |
| Bounded contexts | `notary_v2` có `InheritanceCase`/`inheritance_cases` tại `notary_v2/models.py:83-103`; `notaryoffice` mới là thiết kế dự kiến tại `notaryoffice/intent.md:365-373` | Chưa chứng minh cardinality hay runtime join xuyên repo |

Các dòng trên là baseline kiểm chứng từ source/tài liệu hiện tại. Chúng không
chứng minh rằng các POC đã được adoption hoặc các repo đã dùng cùng database.

## 3. Ma trận merge-readiness

| Gate | Câu hỏi phải trả lời | Bằng chứng cần nộp | Trạng thái baseline |
|---|---|---|---|
| G1 — Vocabulary | Hai consumer có cùng nghĩa của IdentityEvidence, ConversionEnvelope, Evidence và job/error không? | Diff/schema snapshot của producer-consumer; ví dụ golden dataset | **Chưa đạt** — mới có shape/vocabulary experimental |
| G2 — Ownership | Mỗi bảng/dữ liệu có một owner ghi; consumer đọc qua boundary đã duyệt? | Bảng ownership + access path + negative test ghi chéo | **Một phần** — ownership đã mô tả, chưa có runtime kiểm chứng |
| G3 — Provenance | Mọi fact có source ref/hash và giữ được raw/normalized/inferred/confirmed? | Fixture report, collision/partial/error cases, human confirmation evidence | **Chưa đạt** — chưa có rehearsal report |
| G4 — Identity/collision | Trùng CCCD, serial GCN hoặc thửa/tờ có bị tự gộp hồ sơ không? | Golden cases collision + quyết định mapping có actor/evidence | **Chưa đạt** — chỉ có quy tắc vocabulary |
| G5 — Idempotency/retry | Lặp command/import/replay không tạo duplicate hoặc mất evidence? | Test matrix command/import/retry/cancel/restart | **Chưa đạt** — chưa có production contract |
| G6 — DB rehearsal | Schema mapping, backup/restore, rollback và integrity đã diễn tập ở DB tạm? | Báo cáo rehearsal do DB-owner giữ, không dùng DB thật | **Chưa chạy** — phụ thuộc MIN-63 và child implementation được duyệt |
| G7 — UI/component | Upload và Review dùng cùng semantics/revision mà không làm lộ credential hay business logic? | Component/revision matrix, accessibility và lifecycle evidence | **Chưa đạt** — Electron/PySide6 decision còn mở |
| G8 — Repository merge | Module, dependency, build/test/versioning có boundary không xung đột? | Bản đồ source tree + dry-run build/test trong repo đích | **Chưa chạy** — chưa có quyết định monorepo |
| G9 — `notaryoffice` | Có runtime evidence đủ để nhận ownership dự kiến không? | Intent-to-runtime delta; máy thật cho A1/A3/A4 nếu cần | **Conditional** — hiện chỉ có intent, chưa có code |

Một gate chỉ được chuyển sang **Đạt** khi có artifact và người owner xác nhận.
“Chưa thấy lỗi” hoặc việc hai file cùng tên không đủ làm bằng chứng.

## 4. Kế hoạch rehearsal theo owner

### 4.1 Contract và golden dataset

Producer/consumer của mỗi repo tạo fixture tổng hợp, không chứa CCCD thật,
cookie, token hay API key. Fixture tối thiểu phải phủ: PDF có text, PDF scan,
DOCX có bảng/ảnh, XLSX nhiều sheet, ảnh giấy tờ, file hỏng và collision identity.

Mỗi fixture ghi `sample_id`, SHA-256, media type, route mong đợi, facts/text,
provenance tối thiểu, warnings/errors và expected confirmation state. Report phải
ghi rõ test nào chạy local, test nào được phép cloud qua policy gate.

### 4.2 Database tạm và rollback

DB-owner dựng database tạm từ mapping được duyệt, nạp fixture theo thứ tự raw →
normalized → inferred → confirmed, rồi kiểm tra:

1. foreign-key/referential integrity và uniqueness trong từng owner;
2. không có đường ghi chéo ngoài owner;
3. collision không tự gộp `Case` khác bounded context;
4. provenance/raw retention sau retry và partial failure;
5. backup, restore, rollback và checksum trước/sau rehearsal.

Không dùng `notary.db`, `registry.sqlite3` đang chạy hoặc database production.
Nếu cần script/migration mới, tạo child issue trong repo DB-owner; báo cáo cuối
chỉ được đưa về `systemdocs` sau khi chạy xong và review.

### 4.3 UI và component conformance

Chạy cùng một flow synthetic `start_upload → waiting_user/running →
finalize/cancel` qua boundary đã duyệt. Đo startup, RSS process tree,
disconnect/reconnect, restart, accessibility và log redaction. Không coi kết quả
POC Electron là quyết định adoption; ngưỡng và lựa chọn shell phải theo MIN-51.

## 5. Điều kiện kết luận

MIN-66 chỉ được ghi **ready for consolidation design** khi:

- G1–G5 có artifact producer/consumer và owner review;
- G6 có rehearsal DB tạm với restore/rollback đạt;
- G7 có decision Electron/PySide6 và component matrix được duyệt;
- G8 có source-tree/dependency/build-test report;
- G9 ghi rõ phần nào của `notaryoffice` vẫn conditional;
- không còn mâu thuẫn giữa `SYSTEM_ARCHITECTURE.md`, `PROJECTS.md`,
  `TECH_STACK.md` và source repo con.

Nếu một gate chưa đạt, kết luận phải là `not ready` kèm blocker, owner và issue
follow-up. Không dùng từ “đã gom”, “DB chung đã hoạt động” hoặc “UI chung đã
adopt” chỉ dựa trên tài liệu thiết kế.

## 6. Trình tự issue và bàn giao

Trình tự dự kiến, không tự đổi trạng thái Linear:

```text
MIN-50 ALIGN
   ├── MIN-51/MIN-65  UI shell decision + POC
   ├── MIN-57         component/owner map
   ├── MIN-61         conversion/OCR decision
   ├── MIN-62         data contract draft
   └── MIN-63         DB ownership/mapping draft
              ↓
        MIN-64 / MIN-67 / MIN-68 / MIN-69 adoption slices
              ↓
        MIN-66 merge-readiness review + DB rehearsal
```

Các draft trên chỉ là đầu vào review. Mỗi implementation phải chạy trong
worktree của repo sở hữu, có acceptance evidence và không đưa code vào
`systemdocs`. Bản này không tạo `contracts/` và không thay đổi trạng thái issue.

## 7. Khoảng trống đã biết và bàn giao

- `upload_lab/README.md:28` còn có mô tả trạng thái cũ; đây là follow-up của
  repo con, không sửa trong tài liệu cha.
- `notaryoffice` chưa có runtime; branch đặc tả chỉ có thể ghi nhận local nếu
  chưa có remote GitHub hợp lệ.
- MIN-52 đã có bằng chứng synthetic: chạy `tests/test_markitdown_conversion_poc.py`
  bằng POC venv cho kết quả `6 passed`; manifest persistent GD-01..07 được đối
  chiếu SHA-256/route/provenance và `cloud_call_count=0`. POC `notary_v2` chạy
  `22 passed` và reviewer độc lập APPROVE cho manifest `gd-3` riêng. Hai bên cùng
  mã case/route nhưng khác SHA-256 fixture, nên shared dataset revision vẫn là gap;
  đây chưa thay thế contract review production hoặc DB rehearsal.
- MIN-51 và MIN-57 còn là gate trước MIN-64/MIN-67; chưa có owner approval trong
  baseline review này.
- Chưa có rehearsal DB thật hoặc cutover; mọi quyết định physical schema,
  canonical ID và migration vẫn theo `SYSTEM_ARCHITECTURE.md:196-210`.

Kết luận baseline: **chưa sẵn sàng gom repo/DB/UI**. Artifact này chỉ làm rõ
cách chứng minh readiness và không thay thế quyết định của owner.

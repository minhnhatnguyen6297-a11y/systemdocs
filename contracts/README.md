# Contracts giữa các sản phẩm

Thư mục này chứa contract đã publish và bản Draft đang review; trạng thái ở
đầu từng file quyết định có được code tích hợp hay chưa. Ý tưởng chưa thành
contract không đặt tại đây.

## Trạng thái: kênh nội bộ đã publish; Zalo và Upload còn draft

Cột **Trạng thái** ghi rõ đã duyệt hay draft — không ngầm coi draft là đã
publish. Đã publish: một kênh nội bộ shell (`desktopcommand.v1` +
`g1.module.v1` + `notary.case-drafting.v1`, owner duyệt 14/09–24/09/2026;
`notary.case-drafting.v2` thêm ở §13, duyệt 27/09/2026 — MIN-125).
`intake.*.v1` (MIN-92) và `upload.workflow.v1` vẫn DRAFT theo chính file
contract; fixture/validator tồn tại không tự biến draft thành đã duyệt.

Ba công cụ nghiệp vụ vẫn **chạy độc lập** — chưa có API giữa chúng, chưa đọc DB
của nhau, chưa có file trao đổi tự động. Đó là trạng thái của **giai đoạn hiện
tại**, không phải đích đến: hệ thống sẽ gộp lại và dùng chung database
([spec hệ thống](../docs/spec/README.md) mục 5).

Contract xuyên-sản-phẩm đang soạn — kênh Zalo intake → Document Intake
(MIN-92, chờ owner duyệt):

| File | Nội dung | Trạng thái |
|---|---|---|
| [`zalo-intake/zalo-intake.md`](./zalo-intake/zalo-intake.md) + 9 schema `*.schema.json` | `intake.*.v1` — gói raw (manifest/records.jsonl/READY), feed pending, receipt/ACK, service status, error envelope, raw record 5 kind (text/OCR/status/event/listener), OCR bổ sung có quota; Zalo giữ ảnh 168h, máy chính **không nhận ảnh** | **DRAFT** — chờ owner duyệt MIN-92 |
| [`zalo-intake/examples/`](./zalo-intake/examples/) + [`zalo-intake/validate_examples.py`](./zalo-intake/validate_examples.py) | 27 valid + 72 invalid fixtures + validator kiểm chứng được (byte-exact, `.gitattributes -text`) | kiểm draft: `python contracts/zalo-intake/validate_examples.py` |

Kênh nội bộ shell↔engine (owner duyệt 14/09/2026, spec P2; `upload.workflow.v1`
đang DRAFT chờ owner duyệt — MIN-69):

| File | Nội dung | Trạng thái |
|---|---|---|
| [`desktop-command.md`](./desktop-command.md) | `desktopcommand.v1` — kênh lệnh Electron main ↔ Python sidecar trên một máy: auth, lifecycle, idempotency, waiting_user, error, file_ref machine-scope | APPROVED v1 |
| [`g1-module-data.md`](./g1-module-data.md) | `g1.module.v1` — shape dữ liệu trong payload/result/error (FileRef, JobResult, ErrorObject, IdentityEvidence, ownership) | APPROVED v1 |
| [`g1/examples/`](./g1/examples/) + [`g1/validate_examples.py`](./g1/validate_examples.py) | valid/invalid JSON + validator kiểm chứng được | kiểm: `python contracts/g1/validate_examples.py` |
| [`notary-case-drafting.md`](./notary-case-drafting.md) | `notary.case-drafting.v1` (§1–12) — tám command `notary.*` cho tab Soạn hồ sơ: workspace get/create, intake → suggestion, stage commit, diagram evaluate/save, word export batch. §13 là `notary.case-drafting.v2` — contract runtime của luồng Electron mới (Stage draft/commit, `owner_row_id`, assets position-based, diagram v3 + domain `two_party` 30 slot) | v1 APPROVED (rev 1.1 additive MIN-121) — giữ cho consumer legacy; **v2 APPROVED 27/09/2026 (MIN-125)**, triển khai MIN-128…MIN-130 |
| [`notary-case-drafting/`](./notary-case-drafting/) + examples + `validate_examples.py` | JSON Schema draft-07 + examples kiểm chứng được — schema/examples mô tả shape v1 (contract v1 vẫn hợp lệ); `draft-v2.schema.json` + `examples/draft-v2/` là schema payload v2 MIN-125 | kiểm: `python contracts/notary-case-drafting/validate_examples.py` |
| [`upload-workflow.md`](./upload-workflow.md) | `upload.workflow.v1` — 17 command `upload.*` giữa shell (module `upload`/Upload Lab) và sidecar: website registry, workspace/scope binding, revision, run→manifest, waiting_user login/review, partial breakdown, compatibility với payload legacy | **DRAFT** — chờ owner duyệt (MIN-69) |
| [`upload-workflow/examples/`](./upload-workflow/examples/) + [`upload-workflow/validate_examples.py`](./upload-workflow/validate_examples.py) | valid/invalid JSON có `fixture` mô phỏng binding backend + validator kiểm chứng được | kiểm: `python contracts/upload-workflow/validate_examples.py` |

Bốn contract `desktopcommand.v1`/`g1.module.v1`/`notary.case-drafting.v1`/
`upload.workflow.v1` là
**kênh nội bộ shell↔engine** — không phải contract giữa ba sản phẩm nghiệp
vụ. ConversionEnvelope/Evidence/DraftCase dùng chung xuyên repo vẫn theo
Gate A–D lịch sử của MIN-62 (xem Git/Linear; nội dung hiện hành đã chuyển vào spec và contract) (branch
`min-62-data-contract-draft`) và chưa được publish tại đây.

Các shape `v0.experimental` từng nằm trong tài liệu kiến trúc cũ chỉ dùng để
review/POC. Chúng **không phải contract đã duyệt**, không được dùng làm lý do tạo
runtime integration và vì vậy chưa được đặt thành file riêng trong thư mục này.

Nhưng "sau này sẽ gộp" **không phải giấy phép** để nối bừa bây giờ. Mỗi kết nối
vẫn phải có contract được duyệt trước. Xem
[`../docs/spec/README.md`](../docs/spec/README.md) mục 5.

Ngoài hai contract kênh nội bộ G1 ở trên, thư mục này còn có chuẩn định danh
dùng chung dưới đây. Hiện chưa có contract trao đổi dữ liệu xuyên sản phẩm:

| File | Nội dung | Trạng thái |
|---|---|---|
| [`entities.md`](./entities.md) | Định nghĩa & chuẩn hóa các khóa định danh hồ sơ (CCCD, số GCN, thửa/tờ, số công chứng) | Bắt buộc tham chiếu, mỗi repo tự implement |
| [`../docs/spec/README.md`](../docs/spec/README.md) | Công nghệ dùng chung + ràng buộc để lúc gộp DB không xung đột | Đọc trước khi chọn công nghệ mới |

## Quy tắc: contract trước, code sau

Khi hai sản phẩm cần nối với nhau:

1. Viết một file contract trong thư mục này: ai gọi ai, dữ liệu gì, ai sở hữu,
   xử lý lỗi thế nào, ai chịu trách nhiệm khi schema đổi.
2. Người dùng (chủ dự án) duyệt.
3. Rồi mới viết code ở hai repo.

Không viết code tích hợp trước rồi mô tả lại sau. Không agent nào được tự tạo
contract mới rồi tự implement trong cùng một task.

## Tại sao chưa có "shared core library"

Định nghĩa dùng chung ≠ code dùng chung. Ba repo cùng cần trích CCCD nhưng ba
ngữ cảnh khác nhau (ảnh OCR / text Word / text IFilter theo thời gian thực), độ
chịu lỗi khác nhau. Gộp thành thư viện chung lúc này sẽ khóa cả ba vào một
abstraction chưa ai chứng minh được.

Lưu ý phân biệt: **gộp hệ thống ≠ gộp code.** Đích đến là chung **dữ liệu và định
nghĩa**; thư viện code dùng chung là chuyện riêng, chỉ làm khi có domain thật thứ
hai chứng minh được contract.

Nguyên tắc đã chốt trong `notary_v2`
(`docs/platform/case-workspace/README.md`): **không tách abstraction dùng chung
cho tới khi có domain thật thứ hai chứng minh contract.** Áp dụng cho toàn hệ
thống.

## Ba mục trong file cũ đã bị xóa vì sai

File `contracts/README.md` trước đây liệt kê ba contract không tồn tại. Ghi lại
để không ai dựng lại chúng từ ký ức:

- ~~"OCR Extraction Contract: output JSON của pipeline OCR (`upload_lab_repo`)
  nạp vào `notary_v2`"~~ — `upload_lab` không làm OCR ảnh (đầu vào là file
  Word) và không có luồng nạp sang `notary_v2`.
- ~~"Case Schema chuẩn dùng chung"~~ — chưa từng được thống nhất. Mỗi repo có
  mô hình riêng. Xem `entities.md` cho phần *thật sự* cần khớp nhau.
- ~~"Legal Audit Contract: `notary_v2` truy vấn dịch vụ pháp lý từ
  `researchskill`"~~ — `researchskill` là skill hỗ trợ coding, không phải dịch
  vụ tra cứu pháp luật, và nằm ngoài phạm vi hệ thống công chứng.

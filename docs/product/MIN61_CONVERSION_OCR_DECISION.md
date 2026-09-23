# MIN-61 — Decision record: conversion/OCR adapter

**Trạng thái:** DRAFT để chủ dự án duyệt, 11/09/2026  
**Khuyến nghị kỹ thuật:** **ITERATE**  
**Quyết định cuối cùng của chủ dự án:** _chưa ghi_  
**Phạm vi:** chỉ đánh giá POC của `upload_lab` (MIN-52) và `notary_v2`
(MIN-59). Không tạo contract production, không chọn runtime owner, không đổi
`TECH_STACK.md` từ candidate thành công nghệ đã chọn.

## 1. Kết luận ngắn

Chưa có căn cứ để adopt MarkItDown, `markitdown-ocr`, hay OpenAI-compatible
Qwen transport vào production. Baseline theo từng loại file vẫn giữ nguyên:

| Đầu vào | Quyết định hiện tại | Lý do |
|---|---|---|
| PDF có text / DOCX / XLSX | **Iterate, giữ adapter hiện hữu** | POC text-PDF đã ghi `source_ref` theo trang; DOCX/XLSX vẫn explicit unavailable và chưa có dataset revision chung/chất lượng đủ để adopt. |
| `.doc` cũ | **Không adopt MarkItDown; giữ Windows IFilter** | POC `upload_lab` cố ý route sang external legacy adapter; chưa có phép đo IFilter trên máy thật. |
| PDF scan / ảnh | **Không adopt** | Gate đã được mô phỏng và ghi provenance theo trang, nhưng không có cloud smoke được duyệt và không test plugin. |
| `markitdown-ocr` + Qwen compatible | **NOT VERIFIED** | Không có thử nghiệm plugin hoặc provider thật; Qwen-native đang chạy không chứng minh compatible surface. |

`ConversionEnvelope v0.experimental` chỉ tiếp tục là shape POC trong
[`SYSTEM_ARCHITECTURE.md` §6.5](../architecture/SYSTEM_ARCHITECTURE.md#65-conversionenvelope-v0experimental),
không phải contract tại `contracts/`.

## 2. Bằng chứng đã đọc và giới hạn của bằng chứng

### MIN-52 — upload_lab

- Revision bất biến: `ce05b52` trên branch
  `min-52-conversion-benchmark`; không phải `main` và chưa merge.
- Router POC nhận biết PDF có text, `.doc`, và ảnh/PDF scan; nó khởi tạo
  MarkItDown với plugin bị tắt (`poc/conversion_benchmark/router.py:19-40`).
- Với conversion local, segment trả về `source_ref: null`
  (`poc/conversion_benchmark/router.py:66-71`). Harness vì vậy phân loại đây
  là provenance warning, không phải provenance đạt chuẩn
  (`poc/conversion_benchmark/harness.py:94-105`).
- Harness luôn trả `review_required`, đo cloud call từ `ocr_calls`, và không
  tự suy ra approval (`poc/conversion_benchmark/harness.py:145-169`).
- Kết quả chạy và test đã được ghi ở [comment MIN-52](https://linear.app/minhnotary/issue/MIN-52/specpoc-benchmark-markitdown-va-ocr-gate#comment-d38239ac).
  Focused suite hiện tại là `7 passed`, gồm manifest persistent, route
  `ocr_candidate`; đây là evidence POC tổng hợp, không phải benchmark trên corpus
  nghiệp vụ.

### MIN-59 — notary_v2

- Revision POC bất biến: `664edb4` trên
  branch `codex/markitdown-qwen-poc`; đây là worktree riêng, không phải `main`
  và chưa merge.
- POC tắt plugin khi gọi MarkItDown (`tools/document_conversion_poc/converter.py:41-47`),
  ghi segment text-PDF theo trang (`:50-101`), render đầu vào OCR theo từng ảnh/trang, rồi ghi `source_ref`, hash input,
  policy, lý do cho phép và attempt cho từng call
  (`tools/document_conversion_poc/converter.py:117-153`; `models.py:45-68`).
- Test POC mô phỏng PDF hai trang, retry bounded và partial failure; đây là fake
  test, không phải cloud proof (`tests/test_document_conversion_poc.py:211-289`).
- Manifest POC `gd-3` buộc GD-01 có provenance `{"page": 1}`; canonical test gọi
  `convert_path` với converter offline injected, nên không che mismatch provenance
  (`golden_manifest.json:1-16`; `tests/test_document_conversion_poc.py:452-483`).
- Harness chủ động trả `review_required` và ghi chi phí cloud là `None`
  (`tools/document_conversion_poc/harness.py:205-226`). Focused suite hiện tại là
  `22 passed`; kết quả execution và independent review được ghi ở [comment MIN-59](https://linear.app/minhnotary/issue/MIN-59/poc-kiem-chung-ocr-gate-pdf-nhieu-trang-va-provenance#comment-3bb7ecfd).

### Không được suy diễn quá mức

Hai POC hiện đã thống nhất mã case GD-01…07, loại mẫu canonical và route
`ocr_candidate`; manifest và fixture vẫn do từng repo sở hữu. SHA-256 hiện chưa
giống nhau giữa hai bộ byte (`upload_lab`:
`poc/conversion_benchmark/golden_manifest.json:4-10`; `notary_v2`:
`tools/document_conversion_poc/golden_manifest.json:4-92`). Vì vậy gate **dataset
revision chung** vẫn chưa đạt: chưa có một artifact/hash manifest duy nhất để chạy
parity hai phía, cũng chưa có quality threshold hoặc kết luận latency/memory/cost
so sánh được.

Không có cloud call/provider thật hay integration `markitdown-ocr` trong hai
POC. Đây không phải failure của code POC: chúng chủ đích giữ plugin off và zero
cloud trước khi có phê duyệt. Nhưng nó là lý do không được đổi integration
DashScope native hiện hữu. `TECH_STACK.md` §1.1 vẫn mô tả compatible mode là
giả thuyết POC, không phải transport đã chọn.

## 3. Những phần được tái sử dụng — nhưng chỉ ở mức ý tưởng/POC

| Phần | Mức được tái sử dụng | Không được suy ra |
|---|---|---|
| Router phân loại local / legacy / OCR candidate | Mẫu orchestration: hệ thống quyết định route trước converter | Không phải shared Document Router hay runtime API. |
| `ConversionEnvelope` với source hash, warnings/errors, segment và OCR-call audit | Shape experimental để MIN-62 review semantics | Không phải schema production hoặc file contract. |
| Gate deny-by-default, per-page source reference, retry bounded | Acceptance behavior cần giữ trong POC sau | Không chứng minh Qwen-compatible hay plugin hoạt động. |
| MarkItDown local, plugin disabled | Candidate conversion cho PDF text/DOCX/XLSX | Không chứng minh giữ cấu trúc/provenance đủ nghiệp vụ. |

Provider **Qwen** không đồng nghĩa với một integration chung: native DashScope
trong `notary_v2` và OpenAI-compatible/plugin surface là hai bề mặt phải kiểm
chứng riêng. Không thêm provider thứ hai và không thay native adapter trong
quyết định này.

## 4. Gate để chuyển từ Iterate sang quyết định mới

| Gate còn thiếu | Evidence tối thiểu | Owner/đích issue |
|---|---|---|
| Một golden dataset revision chung | Manifest cùng SHA-256, sensitivity, expected text/facts/provenance; chạy được ở cả hai POC | MIN-70 sau Gate A/MIN-62 và khi owner chỉ định nơi lưu artifact. |
| Provenance local | PDF page; DOCX paragraph/table/relationship hoặc warning; XLSX sheet+cell/range hoặc warning | Adapter owner được chỉ định trong task ADOPT. |
| `.doc` boundary | Đo IFilter trên máy thật theo A1, có owner fallback và lỗi có cấu trúc | `upload_lab` / `notaryoffice`; A1 vẫn mở, không tự chốt. |
| Compatible/plugin cloud proof | Synthetic/de-identified smoke được duyệt trước chi phí; kiểm tra MIME/base64, timeout, rate limit, retry/idempotency, response mapping và audit | MIN-71 sau MIN-70 và approval model/base URL/budget; **không** tự dùng key production. |
| Quality/performance/cost | Ngưỡng text/table/Unicode, latency, memory, cloud cost và partial failure đã được chủ dự án chấp thuận | Chủ dự án duyệt threshold trước smoke MIN-71 và trước task ADOPT. |
| Reproducibility | Commit hoặc artifact version cố định cho cả hai phía; test/report lặp lại | MIN-70 xuất chung manifest revision/report; hai POC hiện mới có commit riêng. |

Unit test pass chỉ xác nhận hành vi giả lập; nó không thay thế benchmark trên
dataset chung hoặc cloud proof. Các dữ liệu thật, credential, cookie và raw
payload vẫn bị cấm trong fixture/report.

## 5. Boundary migration và rollback

Không có migration production trong quyết định Iterate này. `python-docx`,
Windows IFilter, `openpyxl`, PyMuPDF và đường OCR DashScope native hiện tại giữ
nguyên; không có DB migration, package chung, API, hoặc consumer runtime mới.

Nếu một task ADOPT được phê duyệt sau này, task đó phải nêu rõ từng loại file
được thay adapter, feature flag/boundary, corpus regression, rollback về
adapter cũ, và cách giữ RAW/provenance. Rollback không được làm mất source hash,
OCR audit hoặc trạng thái người dùng đã xác nhận.

## 6. Ownership, consumers, version và distribution

Chưa gán runtime owner, hai consumer production, hay phương thức distribution.
Gán chúng ngay bây giờ sẽ biến shape POC thành contract/runtime integration,
trái với [`contracts/README.md`](../../contracts/README.md) và giai đoạn ALIGN.

Khi các gate đạt, task contract riêng phải để người duyệt chốt tối thiểu:

1. owner ghi/duy trì adapter và `ConversionEnvelope` production;
2. hai consumer đầu tiên và quyền đọc/ghi của mỗi bên;
3. versioning, distribution (package hay monorepo) và compatibility window;
4. migration boundary, rollback và người chịu trách nhiệm vận hành.

`notaryoffice` chưa có code nên không được ghi là consumer runtime hiện hữu.

## 7. Xác nhận cần từ chủ dự án

Chọn một trong ba dòng sau trong review của MIN-61:

- **Adopt:** chỉ khi toàn bộ gate §4 có evidence được duyệt; sau đó mở task
  ADOPT riêng.
- **Reject:** bỏ candidate và ghi lý do/kết quả đo để không lặp lại POC.
- **Iterate (khuyến nghị hiện tại):** giữ baseline theo file type, thực hiện các
  gate §4 và quay lại decision record này. Không mở production integration.

**Chữ ký quyết định:** _chủ dự án — chưa có_  
**Ngày:** _chưa có_

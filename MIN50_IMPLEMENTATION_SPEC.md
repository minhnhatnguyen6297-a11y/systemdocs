# MIN-50 — Đặc tả và kế hoạch triển khai hội tụ

**Trạng thái:** **ĐÃ DUYỆT ngày 11/09/2026.** Đây là kế hoạch thực hiện sau
MIN-50; tài liệu này không phải contract production và không cấp quyền tạo
integration production.

**Phạm vi:** đồng bộ tài liệu repo con, kiểm chứng hai POC độc lập (chuẩn hóa tài
liệu/OCR và desktop command), giữ nguyên business logic hiện hành. Không merge
repo, không tạo shared package, không gộp database trong kế hoạch này.

## 1. Mục tiêu và kết quả phải có

Sau chu kỳ này, ba repo phải dùng cùng vocabulary và không còn mô tả sai về
endpoint, database, trạng thái registry hoặc ownership. Hai giả thuyết kỹ thuật
phải có số đo để quyết định tiếp tục hay loại bỏ:

1. MarkItDown có thể làm adapter trung gian cho PDF có text, DOCX và XLSX; OCR
   ảnh chỉ chạy qua policy gate và có thể gọi Qwen qua bề mặt tương thích.
2. Electron có thể gửi command tới Python qua FastAPI loopback trong khi
   `upload_lab` vẫn giữ Playwright session, browser thread và bước người dùng
   xác nhận.

Kết quả không đạt nếu chỉ “chạy được demo”; phải có provenance, lỗi có cấu trúc,
đo hiệu năng, chi phí cloud và quyết định rõ ràng (adopt / reject / cần thử lại).

## 2. Ràng buộc bất biến

- Chỉ owner hiện tại được ghi dữ liệu nghiệp vụ; repo khác chỉ đọc sau contract
  production được duyệt.
- Không đi thẳng từ OCR/LLM tới business truth. Luồng bắt buộc:
  `SOURCE → RAW → NORMALIZED → INFERRED → CONFIRMED`.
- Không gửi credential, cookie, ảnh thật hoặc dữ liệu định danh thật vào log,
  golden dataset hay payload debug.
- Không bật `markitdown-ocr` toàn cục; Document Router/OCR gate của hệ thống
  quyết định từng nhánh được phép gửi cloud.
- Không dùng Playwright để điều khiển cửa sổ Electron. Chromium của upload vẫn
  là tiến trình headed do Python quản lý.
- Không sửa các quyết định 🔴 A1/A3/A4 trong `OPEN_DECISIONS.md` bằng suy luận;
  task chạm `notaryoffice` phải dừng để đo và hỏi chủ dự án.
- Không tạo file mới trong `contracts/` cho tới khi semantics production được
  duyệt qua một task spec riêng.

## 3. Phân rã workstream

### W0 — Duyệt và đóng phạm vi — HOÀN TẤT

**Phụ thuộc:** không.

**Việc:**

- Chủ dự án duyệt bốn tài liệu MIN-50 và tài liệu này.
- Ghi revision commit làm baseline cho mọi POC.
- Xác nhận POC được phép chạy bằng dữ liệu tổng hợp/đã khử định danh.

**Đầu ra:** quyết định “MIN-50 approved for POC” ngày 11/09/2026; chưa thay đổi
`TECH_STACK.md` từ candidate thành công nghệ đã chọn.

### W1 — Đồng bộ tài liệu repo con

**Phụ thuộc:** W0.

**Owner:** từng repo; `systemdocs` chỉ review cross-repo.

**`upload_lab`:**

- Sửa `README.md:28`, bỏ `SCANNED`; mô tả các trạng thái thực tế và dry-run /
  finalize.
- Ghi rõ UI hiện là PySide6, worker/Qt signals/command queue in-process, chưa
  có HTTP desktop API.
- Không đổi lifecycle hoặc tên trạng thái trong code chỉ để làm đẹp tài liệu.

**`notary_v2`:**

- Rà các docs còn mô tả Qwen là OpenAI-compatible; dùng endpoint DashScope
  native làm hiện trạng.
- Rà các docs gọi `ocr_jobs.db` là DB nghiệp vụ; sửa thành Celery broker/result
  backend, còn bảng `ocr_jobs` ở `notary.db`.
- Kiểm tra citation sau khi source thay đổi; không sửa business behavior trong
  workstream đồng bộ docs.

**`notaryoffice`:**

- Chỉ đồng bộ intent nếu phát hiện sai với `contracts/entities.md`.
- Chưa viết code trước khi A1/A3/A4 có dữ liệu thật.

**Gate W1:** `rg` không còn mô tả stale trong docs owner; `git diff --check`;
review chéo bởi `systemdocs`; mỗi claim repo con có `file:line`.

### W2 — Chuẩn bị golden dataset và harness đo

**Phụ thuộc:** W0; có thể chạy song song W1.

Golden dataset chỉ là manifest + fixture tổng hợp, không chứa hồ sơ thật:

| ID | Input | Route kỳ vọng | Provenance bắt buộc |
|---|---|---|---|
| GD-01 | PDF có text | local | page |
| GD-02 | PDF scan | OCR gate → Qwen | page, input hash, OCR call |
| GD-03 | DOCX đoạn/bảng/ảnh | text local; ảnh qua gate | paragraph/table/relationship hoặc warning |
| GD-04 | XLSX nhiều sheet/ảnh | cell local; ảnh qua gate | sheet, cell/range hoặc warning |
| GD-05 | `.doc` cũ | Windows IFilter | file hash, warning nếu thiếu location |
| GD-06 | ảnh giấy tờ tổng hợp | OCR gate → Qwen | input hash, OCR call |
| GD-07 | file hỏng/không hỗ trợ | structured error | source hash |

Mỗi fixture có `sample_id`, SHA-256, MIME, độ nhạy cảm, expected facts/text,
expected route và provenance tối thiểu. Harness phải ghi duration, peak memory,
cloud call count, token/chi phí ước tính, warning, error và partial failure.

**Gate W2:** cùng một fixture chạy lặp lại cho kết quả canonical ổn định; không
có cloud call ngoài route; sai khác phải truy về source segment.

### W3 — POC MarkItDown/Qwen

**Phụ thuộc:** W2.

**Ranh giới:** chạy độc lập trong workspace POC của repo được chỉ định sau khi
W0 duyệt; không thay converter production và không tạo contract file.

**Thiết kế thử:**

1. Router nhận file, hash và policy context.
2. Chọn local converter cho PDF có text/DOCX/XLSX; `.doc` giữ IFilter hiện hành.
3. Chỉ PDF scan/ảnh hoặc ảnh nhúng được policy cho phép mới đi qua OCR gate.
4. Adapter gọi thử Qwen qua OpenAI-compatible surface, giữ Qwen là provider
   duy nhất; so sánh payload MIME/base64, response mapping và lỗi với đường
   DashScope native hiện hành.
5. Bao kết quả vào `ConversionEnvelope v0.experimental` trong bộ nhớ/fixture;
   provenance không phụ thuộc MarkItDown tự cung cấp.

**Ca kiểm thử bắt buộc:** text Unicode, bảng, ảnh nhúng, nhiều trang, file lớn,
MIME sai, base64 hỏng, HTTP 4xx/5xx, timeout, retry, rate limit, plugin bị tắt,
plugin cố gửi ảnh ngoài policy, partial failure trong batch.

**Tiêu chí đạt:**

- Route đúng 100% trên manifest; zero cloud call ngoài gate.
- Mọi fact có segment/source reference hoặc warning rõ ràng.
- Không làm mất text/bảng so với baseline hiện hành ngoài ngưỡng đã duyệt.
- Lỗi/timeout không làm crash batch; retry có giới hạn và idempotent.
- Có bảng đo chất lượng, latency, memory, chi phí và quyết định adopt/reject.

**Nếu fail:** giữ adapter hiện hành, ghi nguyên nhân và mở issue follow-up; không
đưa MarkItDown vào `TECH_STACK.md` như công nghệ đã chọn.

### W4 — POC DesktopCommand

**Phụ thuộc:** W0; có thể chạy song song W3.

**Transport cố định:** FastAPI HTTP loopback tối thiểu, bind `127.0.0.1`, port
cấu hình được, tiến trình/entrypoint riêng. Electron main process là caller;
renderer không gọi trực tiếp. Token phiên ngắn hạn, không CORS rộng, không log
credential/cookie.

**Commands tối thiểu:** `start_upload`, `cancel_upload`, `scan_document`,
`get_status`. Request có `contract_version`, `command_id`, timestamp và payload;
response có `job_id`, status, result/error. Đây vẫn là shape experimental, không
phải API production.

**Luồng thử:**

```text
Electron main → localhost FastAPI → queue Python → UploadWorker browser thread
                                      ↓
                         waiting_user / running / completed / failed
                                      ↓
                         Chromium headed + người dùng xác nhận
```

POC phải chứng minh start/cancel/status, duplicate command, restart server,
client timeout, browser chưa đăng nhập, user cancel và lỗi Playwright. Không
được nhúng web tỉnh vào Electron và không được gọi object worker từ thread HTTP.

**Tiêu chí đạt:** command không làm lộ credential; không deadlock Qt/Playwright;
job status đúng khi restart/client disconnect; browser lifecycle vẫn do Python
sở hữu; curl có thể debug toàn bộ happy path và error path.

**Nếu fail:** giữ PySide6; không ghi Electron là lựa chọn chính thức.

### W5 — Review kết quả và quyết định adopt

**Phụ thuộc:** W3, W4.

Tạo decision record cho từng candidate:

- Adopt: lợi ích đo được, chi phí vận hành, migration boundary, rollback.
- Reject: dữ liệu đo và lý do kỹ thuật.
- Iterate: gap cụ thể, fixture/test bổ sung, người chịu trách nhiệm, deadline.

Chỉ sau decision record mới được mở task ADOPT. ADOPT thay adapter từng repo,
không rewrite business logic. Mọi contract production phải qua `contracts/`
trước khi viết integration code.

### W6 — Chuẩn bị CONSOLIDATE (chưa thực hiện)

Chỉ mở khi W5 đã ổn định và các owner đồng ý. Khi đó mới thiết kế canonical ID,
schema chung, migration, cutover, backup/rollback và quyền ghi. Không suy ra
cardinality giữa `inheritance_cases` và `notaryoffice.cases` từ POC này.

## 4. Thứ tự thực thi đề xuất

```text
W0 duyệt
  ↓
W1 đồng bộ docs ─────┐
                     ├─→ W3 MarkItDown/Qwen → W5 decision
W2 dataset/harness ──┘
  ↓
W4 DesktopCommand (song song W3 nếu đủ người)
                     └─→ W5 decision
                              ↓
                         W6 chỉ khi được mở riêng
```

Ưu tiên thực tế: W1 trước để loại sai lệch mô tả; W2 ngay sau đó; W3 trước W4
vì conversion/provenance ảnh hưởng nhiều đường dữ liệu hơn. W4 có thể song song
nếu có người phụ trách riêng.

## 5. Checklist bàn giao mỗi workstream

- [ ] Nêu repo/owner và commit baseline.
- [ ] Liệt kê file/source evidence đã kiểm chứng.
- [ ] Tách rõ hiện trạng, POC, quyết định dự kiến.
- [ ] Có fixture/test và tiêu chí pass/fail đo được.
- [ ] Ghi security/privacy boundary và cách rollback.
- [ ] Không sửa repo ngoài scope, không tạo contract production sớm.
- [ ] `git diff --check` và review diff hoàn tất.
- [ ] Cập nhật issue/decision record sau khi owner duyệt, không tự đổi trạng thái
      quyết định 🔴.

## 6. Điều kiện kết thúc chu kỳ

Chu kỳ chỉ được coi là hoàn tất khi:

1. W1 đạt và các docs owner không còn stale fact đã biết.
2. Golden manifest/harness có kết quả tái lập.
3. W3 và W4 có report pass/fail, không chỉ ảnh chụp demo.
4. Có quyết định adopt/reject riêng cho MarkItDown và Electron.
5. Không có thay đổi production hoặc DB migration chưa được duyệt.

Nếu một tiêu chí chưa đạt, trạng thái phải là **Blocked/Iterate**, không tuyên bố
hệ thống đã hội tụ.

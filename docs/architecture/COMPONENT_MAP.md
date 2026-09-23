# Bản đồ thành phần chung — MIN-57

**Trạng thái: DRAFT để chủ dự án duyệt, ngày 11/09/2026.** Đây là thiết kế
ownership/vocabulary phục vụ goal MIN-56, không phải contract production,
quyết định chọn công nghệ hay quyền triển khai tích hợp. Kế hoạch, dependency
và tiến độ ở [MIN-56](https://linear.app/minhnotary/issue/MIN-56) và
[MIN-57](https://linear.app/minhnotary/issue/MIN-57), không duy trì task list ở đây.

## 1. Kết quả thiết kế cần duyệt

Đích đã được chủ dự án yêu cầu: **một hệ thống, database chung, UI chung; các
chức năng chung có cùng nguồn implementation/version, sẵn sàng gom repo**.
Chỉ cùng tên trường hoặc cùng thư viện chưa đạt đích này.

Bốn đề xuất của bản đồ:

1. Bắt đầu reuse code bằng **chuẩn hóa định danh sau nhận diện**, với hai consumer
   hiện có là intake của `notary_v2` và extraction của `upload_lab`; không gộp
   regex nhận diện hoặc parser nghiệp vụ. Cụ thể ở §5.
2. Đề xuất `notary_v2` bảo trì thành phần canonical/conversion/OCR dùng chung;
   `upload_lab` tiếp tục bảo trì phần đọc `.doc` và browser engine. Owner code
   không trở thành owner mọi dữ liệu chạy qua component đó.
3. Đề xuất `upload_lab` chủ trì shell/UI chung và cầu command; module nghiệp vụ
   vẫn thuộc owner hiện tại. Công nghệ shell và contract còn qua decision gate.
4. Database chung có một đầu mối quản lý migration được duyệt riêng, **không**
   cấp quyền ghi tự do cho ba module. Canonical Case ID, engine, schema và vị trí
   package trong repo lớn chưa được quyết định tại đây.

Các đề xuất owner ở trên chưa có hiệu lực production cho đến khi được duyệt.
Nguồn chuẩn: [kiến trúc](./SYSTEM_ARCHITECTURE.md) §6–7,
[định danh](../../contracts/entities.md), [công nghệ](./TECH_STACK.md),
[quyết định mở](./OPEN_DECISIONS.md). Không sao chép lựa chọn công nghệ sang bản đồ.

## 2. Phạm vi bằng chứng

Đọc source ngày 11/09/2026 tại các checkout sau. Ký hiệu trong citation bên dưới
là tiền tố đường dẫn, không phải tên package/import.

| Ký hiệu | Checkout | Revision kiểm tra |
|---|---|---|
| `N/` | `D:/notary_v2/` | `cabfff98cd4e33eba2a06ce3998eb9f0d2a7be36` |
| `U/` | `D:/upload_lab_repo/` | `a4349a24572faa8a593d6f0484eaadbf9c48e6bd` |
| `O/` | `D:/notaryoffice/` | `1c1b160d0de3959d15573027f6f3ebd770235042` |
| `P/` | `D:/notary_v2/.worktrees/markitdown-qwen-poc/` | `664edb4` |
| `D/` | `D:/upload_lab_repo/.worktrees/desktop-command-poc/` | `f18a42fbbeb0a0c578a8e976e557b5594ff7761e` |

`N/AGENTS.md` có thay đổi chưa commit của người dùng; không sửa hoặc dùng thay đổi
đó để suy ra runtime khác. Các source được viện dẫn dưới đây được đọc trực tiếp.
Đây là kiểm chứng thiết kế/code, **không** phải chứng nhận triển khai trên máy thật.

**Giới hạn kiểm chứng:** client không đăng ký Graphify/context-mode MCP. Dùng
`rg`, đọc source và Git có giới hạn; không cài tool, không rebuild graph, không
đọc `.env`, session/cookie, DB hay hồ sơ khách hàng.

**Những gì chưa có/chưa được chứng minh trong phạm vi này:**

- `O/` chỉ có hai file tracked `AGENTS.md`, `intent.md`; `O/AGENTS.md:3,8-17`
  xác nhận chưa có code và gate máy thật. Mọi ô `O` ở §3 là thiết kế dự kiến.
- Checkout `D/` đã có source POC DesktopCommand tại revision
  `f18a42fbbeb0a0c578a8e976e557b5594ff7761e`; các thay đổi MIN-65 về shell,
  renderer và fake-worker đã được commit trong cùng POC branch. FastAPI/uvicorn chỉ
  nằm trong `D/poc/desktop_command/server.py:9-90`; đây là sidecar POC, không
  phải API của app PySide6. UI/worker production của `U/` vẫn dùng
  signals/queue (`U/ui_qt/workers.py:60-117`). Không suy rộng thành
  “upload_lab không gọi HTTP ra web tỉnh”.
- Chưa chứng minh có component code/version dùng chung giữa hai repo. Các
  implementation tìm thấy ở §3 nằm trong từng repo; model/envelope mới ở POC.
- Chưa có bằng chứng trong các nguồn đã kiểm tra về UI chung, DB chung hay
  production contract xuyên repo. Không gọi trạng thái đó là đã triển khai chỉ
  vì có shape experimental trong tài liệu.

## 3. Ma trận hiện trạng — sáu lớp, ba repo

Chỉ giữ bằng chứng cần để xác định quan hệ và ranh giới; không mô tả lại thuật
toán, schema chi tiết hay workflow nội bộ của các sản phẩm.

| Lớp | `notary_v2` — source hiện hành | `upload_lab` — source hiện hành | `notaryoffice` — chỉ thiết kế |
|---|---|---|---|
| **Định danh / chuẩn hóa** | Số giấy tờ được xử lý trong `_normalize_person_data`; nhận diện 12 số và serial có helper riêng (`N/routers/ocr_ai.py:162-176,466-468,919-939`). | Nhận người/số theo nhãn Word, trường `cccd`; nhánh plain text giữ `raw_text` và vị trí dòng (`U/extract_contract.py:392-419,1023-1025,1044-1057`). | Chuẩn khóa và `entities.raw_value/normalized_value` trong intent (`O/intent.md:323-328,365-373`). |
| **Nguồn / conversion / OCR / provenance** | Có reader Word cho audit và cloud OCR có bước chuẩn bị ảnh riêng (`N/services/fast_audit/word_parser.py:27-61`; `N/routers/ocr_ai.py:326-344,381-417`). | Reader `.docx/.doc` riêng trước extraction; `.doc` qua IFilter (`U/extract_contract.py:133-158,247-263`). Registry có nhận diện file theo metadata (`U/batch_scan.py:90-92`). | Source → Evidence → enrichment; artifact/snapshot có nguồn/hash (`O/intent.md:144-159,230-260,375-378`). |
| **Job / command / error** | Có `OCRJob`, worker và broker/result backend (`N/models.py:161-171`; `N/tasks.py:81-93,113-138`; `N/celery_app.py:5-11`). Đây không phải chứng cứ mọi cloud OCR đi qua cùng queue. | UI signals → queue → thread giữ session; registry chuẩn bị/upload có trạng thái riêng (`U/ui_qt/workers.py:60-117,146-153`; `U/playwright_uploader.py:81-83`). DesktopCommand POC mới thêm sidecar FastAPI/registry, không phải API production (`D/poc/desktop_command/server.py:9-90`; `D/poc/desktop_command/registry.py:21-75`). | Event buffer → Hub → xử lý/dựng ứng viên được mô tả, chưa có command API (`O/intent.md:263-277`; `O/AGENTS.md:3`). |
| **Config / secret / diagnostics** | Nạp cấu hình tiến trình và logging tại repo (`N/main.py:24-27`; `N/observability.py:30-60`). | Settings/session path và log helper thuộc uploader (`U/playwright_uploader.py:121-128,298-306,343-347`); diagnostics có điểm gọi UI (`U/ui_qt/main_window.py:561-567`). | Ranh giới privacy, tài khoản VP, xử lý LAN là thiết kế (`O/intent.md:66-85`). Chưa có config/logging implementation (`O/AGENTS.md:3`). |
| **Persistence / ownership** | Business DB có `Customer`, `InheritanceCase`, `OCRJob`; hạ tầng job cấu hình riêng (`N/database.py:8-24`; `N/models.py:12-29,83-102,161-171`; `N/celery_app.py:5-11`). | `file_registry` được quản lý bởi batch/upload, có ID cục bộ và file key (`U/batch_scan.py:106-148`; `U/playwright_uploader.py:132-138`). | 14 bảng dự kiến, tách entities/cases/case_entities/artifacts (`O/intent.md:330-381`). Không có schema chạy thật. |
| **UI / navigation / xác nhận** | Web routes/static/templates; Stage/Pool thuộc workflow thừa kế (`N/main.py:103-112`; `N/docs/domains/inheritance/workflow.md:25-30,35-55,78-89`; `N/docs/platform/case-workspace/README.md:6-9`). | Navigation Audit/Upload/Settings/Logs; browser headed riêng (`U/ui_qt/main_window.py:138-162`; `U/playwright_uploader.py:896-910`). | Search/case card, nhãn confirmed/draft và popup được đặc tả (`O/intent.md:385-413,428-466`), chưa là UI runtime. |

## 4. Bản đồ reuse đích và trách nhiệm đề xuất

Phân biệt mức reuse:

- **Quy ước:** cùng nghĩa/semantics và fixture đối chiếu; chưa có code chung.
- **Component:** một nguồn implementation/version, có consumer adapter mỏng.
- **Tích hợp:** gọi contract/đọc dữ liệu của owner, đã duyệt và kiểm chứng.
- Dùng cùng thư viện nền hoặc copy cùng đoạn code **không chứng minh** đạt
  Component/Tích hợp. Không buộc mọi lớp phải trở thành một thư viện duy nhất.

| Thành phần / phạm vi chung | Owner code đề xuất; consumer | Điều phải giữ ở owner nghiệp vụ | Đích reuse và gate |
|---|---|---|---|
| Canonical identity sau nhận diện | `notary_v2` bảo trì; intake `N` + extraction `U`; Hub `O` là consumer tương lai. Điểm nhận diện thật ở §3. | Regex tìm candidate, phân loại giấy tờ, ngữ cảnh OCR/Word, quyết định ghép hồ sơ và giá trị raw. | Component thuần, không I/O; spec MIN-62 trước MIN-68/69. Phạm vi đầu tiên ở §5. |
| Conversion + nguồn + provenance | `notary_v2` bảo trì facade/envelope và adapter OCR; `upload_lab` bảo trì adapter `.doc`. Consumer là caller intake/extraction, không phải mọi file tự qua cloud. | Source owner quản lý file; parser nghiệp vụ đọc cấu trúc riêng; quyền cloud do orchestration cấp; adapter không cấp quyền cho chính nó. | Component sau benchmark MIN-52/58/59, decision MIN-61 và contract MIN-62. MarkItDown/plugin không mặc định được adopt. |
| Job/command/error công khai | `upload_lab` bảo trì cầu desktop và client dùng chung cho shell; từng engine xử lý command mình sở hữu. | Queue/thread/cancel/session nội bộ; registry state không bị đổi thành job enum chung. | Quy ước → Component/Tích hợp sau MIN-60/65, MIN-51 và MIN-64. Chưa chọn queue mới hoặc một scheduler toàn hệ thống. |
| Config/secret/diagnostics | Mỗi runtime sở hữu credential/config riêng; đề xuất `upload_lab` hiển thị diagnostics trong shell, `notary_v2` bảo trì core quy ước/masking khi được duyệt. | Nguồn secret, lifecycle session, lưu vết nghiệp vụ và chính sách retention của owner. | Chung policy và metadata lỗi trước; code masking/config reader chỉ share khi hai consumer chứng minh cùng yêu cầu. Ranh giới auth/redaction thuộc MIN-62/64, công nghệ theo TECH_STACK.md. |
| Persistence | Module nghiệp vụ là owner ghi; đề xuất `notary_v2` chủ trì kiểm kê/mapping. **Chưa chọn** migration authority cuối cùng. Consumer khác đọc contract. | ID cục bộ, vòng đời record, xác nhận và provenance; không nhập nhằng Case soạn thảo với Case theo dõi. | Một DB chung ở đích, không phải ba DB độc lập vĩnh viễn. MIN-63 duyệt topology/identity/migration; rehearsal trước cutover. |
| UI/navigation/confirmation | `upload_lab` chủ trì shell/component UI; `notary_v2` sở hữu nội dung Review/Case; `notaryoffice` sở hữu Search/Work-tracking dự kiến. | Stage/Pool và rule nghiệp vụ, Finalize web tỉnh, popup theo privacy; shell không tự xác nhận thay người. | Một UI với module dùng cùng component/version; MIN-64 trước MIN-67. POC công nghệ và production UI là hai bước khác nhau. |

Owner quản trị vocabulary/contract là `systemdocs`, **không phải runtime owner**.
Tên người/đơn vị vận hành và vị trí package cụ thể cần được chỉ định ở task
spec liên quan; bảng này không tạo một repo/package “shared” mới.

## 5. Lát cắt code chung nhỏ nhất: canonical CCCD

**Đề xuất để duyệt, chưa implement.** Hai consumer có điểm bám cụ thể:

- Intake `N`: `_normalize_person_data` xử lý `so_giay_to`
  (`N/routers/ocr_ai.py:162-172`), còn `_extract_id12` tìm candidate
  (`N/routers/ocr_ai.py:466-468`).
- Extraction `U`: `find_persons` / `_extract_plain_text_person_entries` nhận
  số theo nhãn rồi ghi `cccd` (`U/extract_contract.py:392-419,1023-1025,1044-1057`).

Đây là **hai điểm tiêu thụ có nhu cầu**, chưa chứng minh đang có cùng semantics.
Nhất là `so_giay_to` không mặc nhiên có nghĩa CCCD và nhãn Word cũng nhận CMND.
Không thay toàn bộ hai trường đó bằng validator CCCD rồi làm mất dữ liệu cũ.

Phần dự kiến chung chỉ chuẩn hóa/kiểm tra candidate đã nhận diện theo
`contracts/entities.md` §1; raw, loại giấy tờ, vị trí nguồn và lý do không thể
canonical phải được giữ qua adapter của consumer. Không đoán chữ thành số,
không tự thêm số 0, không cắt 9 số cuối để ghép, không tự điền định danh thiếu.

Những việc **không** đi vào component đầu tiên:

- Tìm tên/người trong Word hoặc ảnh; nhận diện nhãn/loại giấy tờ.
- Phân loại hợp đồng, tư cách người tham gia, rule thừa kế, tính confidence.
- Gộp Case, chọn người/tài sản, viết DB hoặc nâng thành `CONFIRMED`.
- Chuẩn hóa toàn bộ ngày/số/serial/địa phương trong một lần; mở rộng sau bằng
  contract và fixture riêng khi có consumer thứ hai thật.

Minh chứng trước khi coi reuse thành công:

1. Hai owner duyệt semantics/input/output/error/compatibility ở MIN-62; không
   tạo production contract mới rồi implement trong MIN-57.
2. Cùng fixture tổng hợp bao phủ đủ 12 số, số 0 đầu, khoảng trắng/dấu phân cách
   được phép, CMND 9 số, thiếu/thừa số, ký tự không rõ, empty/null. Expected của
   trường hợp mơ hồ được duyệt trong spec, không lấy output code hiện tại làm chuẩn.
3. MIN-68/69 chứng minh hai caller thật dùng **cùng implementation/revision**,
   giữ payload/DB behavior cũ ngoài thay đổi đã duyệt; rollback adapter rõ ràng.
4. Package/distribution có owner và version cố định được duyệt; không copy
   source, không import qua đường dẫn tuyệt đối sang checkout bên cạnh, không
   chạy qua nhánh Git nổi. MIN-57 chưa chọn cách publish package.

Sentinel không phải consumer Python giả định. Khi `O` có code, dùng contract và
fixture để thiết kế adapter phù hợp ranh giới máy trạm/Hub; chưa buộc nó tải
library Python hoặc gọi cloud (`O/intent.md:263-277`; `O/AGENTS.md:8-17`).

## 6. Những khác biệt không được xóa khi hội tụ

### 6.1. Người, tài sản, hồ sơ và nguồn không phải một khóa

CCCD/serial/thửa-tờ là evidence đối chiếu người/tài sản và tìm Case liên quan,
không phải Case primary key. `N` có aggregate `InheritanceCase`, còn `O` thiết
kế `cases`/`case_entities` (`N/models.py:83-102`; `O/intent.md:365-373`). Chưa
chứng minh cardinality xuyên hai aggregate; không gán 1:1 từ tên “Case”.

`U` dùng `file_key` băm path/mtime/size (`U/batch_scan.py:90-92`), còn `P` băm
**bytes** thành source hash (`P/tools/document_conversion_poc/models.py:113-123`).
Hai thứ không tương đương. Bản đồ DB sau này phải phân biệt source content,
source occurrence/location, record ID, job/command ID và Case identity; không
thay khóa registry hay dùng hash nội dung làm khóa hồ sơ trong task này.

### 6.2. Cùng conversion boundary không có nghĩa một converter cho mọi việc

Reader hiện có trả cấu trúc khác nhau theo mục đích (`N/services/fast_audit/word_parser.py:27-61`;
`U/extract_contract.py:247-263`). Chuẩn conversion cần giữ bằng chứng nội dung/
vị trí; không suy ra bảo toàn thứ tự bảng chỉ vì cùng dùng thư viện nền.
Benchmark phải so với nhu cầu nghiệp vụ, không chỉ kiểm tra có text.

POC tại `P` có envelope và gate (`P/tools/document_conversion_poc/models.py:102-123`;
`P/tools/document_conversion_poc/policy.py:51-74`). Local converter tắt plugin
(`P/tools/document_conversion_poc/converter.py:24-30`); đó **không phải** bằng
chứng đã tích hợp plugin OCR. Adapter gửi data URL trực tiếp
(`P/tools/document_conversion_poc/qwen_compatible.py:66-83`) chưa tự chứng minh
PDF nhiều trang/cloud-compatible hoạt động.

Text-PDF local trong POC đã gắn `source_ref` theo trang mà vẫn giữ Markdown của
converter (`P/tools/document_conversion_poc/converter.py:50-101`); DOCX/XLSX vẫn
dùng `source_ref: null` cùng warning. Nhánh OCR đã gắn `source_ref` theo
input/page cho cả segment và mỗi OCR call (`P/tools/document_conversion_poc/converter.py:117-153`).
Điều này chứng minh được provenance theo trang trong POC, nhưng chưa biến
provenance DOCX/XLSX thành chuẩn production. Harness hiện đã so các trường
expected, gồm cả facts và provenance, rồi đánh dấu mismatch là failed
(`P/tools/document_conversion_poc/harness.py:76-90,155-164`);
nó luôn phát hành `decision: review_required` và yêu cầu human approval
(`P/tools/document_conversion_poc/harness.py:211-220`). Vì vậy **POC vẫn chưa
phải nghiệm thu MIN-50/W2/W3**: còn thiếu dataset revision chung, plugin/cloud
proof và ngưỡng chất lượng đã duyệt. Đây là gap cần theo dõi trong MIN-58/59,
không phải lý do rewrite production hay quay sang backlog bug vặt.

### 6.3. Job thành công không phải hồ sơ đã xác nhận

State kỹ thuật của worker/registry không thể thay thế state nghiệp vụ
(`N/models.py:92,166`; `U/playwright_uploader.py:81-83`; `O/intent.md:367-374`).
Contract command cần mô tả completion/cancel/retry theo tác vụ; shell chỉ hiển
thị, không suy ra “hồ sơ đã ký” hoặc tự Finalize từ job completed.

UI chung không thay owner nghiệp vụ: Stage xác nhận theo workflow `N`, upload
vẫn do engine `U` quản lý browser, Search/Work-tracking `O` còn là thiết kế
(`N/docs/domains/inheritance/workflow.md:78-89`; `U/ui_qt/workers.py:60-65,109-117`;
`O/intent.md:428-448`). Dùng chung UI cần chung module/component và contract,
không chỉ thống nhất màu hoặc bọc nguyên ba app rồi gọi là đã hoàn tất.

## 7. Điều kiện chuyển từ bản đồ sang hệ thống chung

- **Duyệt bản đồ:** chủ dự án xác nhận các owner đề xuất ở §1/4 và lát cắt §5;
  đây không phải duyệt toàn bộ contract/migration.
- **Duyệt công nghệ/contract riêng:** MIN-61/62/64 dựa bằng chứng và decision của
  chủ dự án. `TECH_STACK.md` là SOT công nghệ; shape experimental giữ ở §6 của
  kiến trúc cho đến task production spec được duyệt.
- **Chứng minh reuse thật:** hai consumer dùng cùng version, conformance đúng,
  giữ raw/provenance và human confirmation. Không đạt chỉ bằng unit mock.
- **DB/UI chung:** MIN-63 xác định owner migration/schema và identity mapping;
  MIN-67 kiểm chứng module UI, MIN-66 tổng hợp rehearsal/readiness. Đích vẫn là
  DB/UI chung, chưa là quyền cutover hoặc merge monorepo ngay.
- **Ranh giới máy thật:** A1/A3/A4 và privacy B3 chưa được giải quyết bằng bản đồ
  này. `O` chỉ được làm spec với nhánh điều kiện; code Sentinel/Hub phải chờ
  gate thực tế (`O/AGENTS.md:8-17`; `OPEN_DECISIONS.md` A/B).

Không có code, schema production, package hay runtime được tạo bởi tài liệu
này. Không đóng goal MIN-56 khi mới có bản đồ hoặc khi chỉ một repo đạt test.

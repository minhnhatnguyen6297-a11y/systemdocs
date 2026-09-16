# Lựa chọn công nghệ — SOT toàn hệ thống

**Đây là file agent phải đọc TRƯỚC KHI ra quyết định kiến trúc hoặc chọn công
nghệ mới trong bất kỳ module nào.**

Lý do file này tồn tại: các module sẽ **gộp thành một hệ thống dùng chung
database** ở giai đoạn sau. Code đã nằm chung một monorepo (nhánh
`consolidate/monorepo`) — nghiệp vụ vẫn tách theo module, nhưng nếu mỗi module
tự chọn công nghệ khác nhau cho cùng một việc (ví dụ module này OCR bằng Qwen,
module kia OCR bằng thứ khác), lúc gộp DB sẽ phải viết lại. Chọn khác là được —
nhưng phải **có lý do và ghi vào đây**, không chọn theo quán tính.

Cập nhật sau khi gộp monorepo: 16/09/2026. Module = thư mục con trong repo này;
đường `D:\...` ở tài liệu cũ là từ trước khi gộp.

---

## 1. Bảng công nghệ đang dùng thật

| Việc | Công nghệ đã chọn | Đang dùng ở | Ghi chú |
|---|---|---|---|
| **OCR ảnh giấy tờ** | **Qwen-VL-OCR** qua DashScope **native multimodal API** (`qwen-vl-ocr-2025-11-20`) | `notary_v2/routers/ocr_ai.py:38-39,381-414` | Base mặc định `https://dashscope-intl.aliyuncs.com`; endpoint `{base}/api/v1/services/aigc/multimodal-generation/generation` (`:386`). File **không còn** nhánh `OPENAI_API_KEY`/OpenAI-compatible nào — transport duy nhất là native DashScope |
| **Đọc `.docx`** | `python-docx` | `notary_v2`, `upload_lab` | Phải giữ thứ tự đoạn + bảng, nếu không sẽ trộn Bên A / Bên B |
| **Đọc `.doc` cũ** | **Windows IFilter (`query.dll`)** | `upload_lab/`; `notaryoffice/` (dự kiến) | Không cần cài Word. Khả năng đọc ổn định khi Word đang giữ file **chưa được đo trên 6 máy thật** (`OPEN_DECISIONS.md` A1). `notary_v2` **không** dùng |
| **Đọc PDF / render ảnh** | `PyMuPDF` (`fitz`) | `notary_v2` | |
| **Đọc QR / barcode** | `zxing-cpp` | `notary_v2` (tùy chọn; local OCR stack đã gỡ — QR đi kèm pipeline đó, mở lại cần review) | |
| **Sinh file Word** | `python-docx` + template placeholder | `notary_v2` (`services/word_engine.py`) | |
| **Đọc/ghi Excel** | `openpyxl` | `notary_v2`, `upload_lab` | |
| **So khớp chuỗi mờ** | `rapidfuzz` | `notary_v2` (fast audit) | Dùng cho soát chính tả, **không** dùng để ghép hồ sơ |
| **Web backend** | **Python FastAPI** | `notary_v2`; `notaryoffice` Central Hub (dự kiến) | |
| **ORM** | SQLAlchemy 2.x | `notary_v2` | |
| **Database** | **SQLite** | `notary_v2` (`notary.db`), `upload_lab` (`registry.sqlite3`) | `notary.db` chứa bảng nghiệp vụ + bảng Zalo (`notary_v2/database.py`, `models.py`); sidecar `shell/` ghi cùng DB này qua `notary_adapter.py`. Xem mục 3 về giai đoạn gộp |
| **UI web** | Jinja2 template + static (không SPA framework) | `notary_v2` (`frontend/`) | |
| **Desktop shell đích** | **Electron** | module `shell/` (main + preload + renderer; sidecar FastAPI `shell/sidecar/`) | Owner chốt ngày 14/09/2026 qua MIN-50; contract `desktopcommand.v1` APPROVED ở `contracts/desktop-command.md`; Electron sở hữu shell/UI, không sở hữu nghiệp vụ Python. POC tiền thân: `upload_lab/poc/desktop_command/` |
| **UI desktop legacy** | **PySide6 / Qt** | `upload_lab` (`ui_qt/`) | Baseline chuyển đổi; không tiếp tục là shell đích |
| **Tự động hóa web nhà nước** | **Playwright** (Chromium) | `upload_lab`; `shell/sidecar/upload_session.py` | Session lưu ở `nd_storage_state.json`; Chromium headed riêng do Python quản lý — không điều khiển cửa sổ Electron |
| **Agent trên máy trạm** | **C# .NET 8** | `notaryoffice` (dự kiến) | Ràng buộc: <30MB RAM, <0.5% CPU |
| **Nhận media từ Zalo** | `zca-js` (Node) như connector thay thế được | `notary_v2` (Zalo Document Inbox, `zalo_connector/`) | Xem mục 4 |
| **Test** | `pytest`/`unittest`; `node --test` cho JS; `playwright` cho e2e | `notary_v2`, `upload_lab`, `shell` | |

**API key và secret:** đặt trong `.env` của từng module, đã `.gitignore`. Không
bao giờ ghi key vào tài liệu, không commit `.env`. Mẫu biến ở `.env.example`.

### 1.1. Candidate còn đang đánh giá

Electron đã được owner chọn làm desktop shell đích ngày 14/09/2026 và đã có
runtime thật trong module `shell/` (contract `desktopcommand.v1` APPROVED —
xem `contracts/`). POC conversion có code trong repo
(`notary_v2/tools/document_conversion_poc/`, `upload_lab/poc/conversion_benchmark/`),
nhưng chưa có đủ bằng chứng golden dataset/benchmark để chọn candidate vào
production. Snapshot source và gap ở [`docs/g1/COMPONENT_MAP.md`](./docs/g1/COMPONENT_MAP.md)
§2/6.2 (draft MIN-57 — issue đã cancel, chỉ còn giá trị tham chiếu). Các
candidate dưới đây chỉ được triển khai sau khi được duyệt, bằng task riêng;
không diễn giải bảng này thành migration hoặc dependency production.

| Việc | Candidate | Baseline hiện tại | Lý do kỹ thuật để POC | Gate trước khi chọn |
|---|---|---|---|---|
| Adapter chuẩn hóa tài liệu | **Microsoft MarkItDown** | `python-docx`, Windows IFilter, `openpyxl`, PyMuPDF theo từng module | Thử một lớp conversion thống nhất cho PDF có text, DOCX và XLSX trước hậu xử lý nghiệp vụ | Golden dataset phải chứng minh chất lượng, cấu trúc, provenance, lỗi và thời gian. `.doc` cũ không được giả định là đã giải quyết |
| OCR ảnh nhúng trong adapter | **POC `markitdown-ocr` gọi Qwen qua giao diện OpenAI-compatible** | Đường OCR hiện hành dùng DashScope native (`notary_v2/routers/ocr_ai.py:381-414`) | Cùng provider, nhưng là **bề mặt tích hợp thứ hai**, chưa chứng minh tương đương đường hiện hành | Kiểm chứng payload, MIME/base64, phản hồi, lỗi, timeout và giới hạn; OCR gate phải cấp quyền trước từng nhánh, không bật plugin toàn cục |

Ranh giới chuyển đổi desktop đã chốt:

- Electron là shell đích; không chuyển business logic Python sang Node chỉ vì
  đổi shell. UI PySide6 là baseline để kiểm chứng parity trước cutover.
- Backend Python tiếp tục mở **Chromium headed riêng** bằng Playwright để người
  dùng xem form và tự xác nhận. Không dùng Playwright để điều khiển chính cửa sổ
  Electron trong luồng upload.
- Chưa nhúng web tỉnh vào Electron. Nếu sau này cần embed, phải mở lại review về
  bảo mật, session, download/upload và lifecycle; không dùng `<webview>` theo
  quán tính.
- DesktopCommand production đã được đặc tả/duyệt (MIN-64) và publish thành
  `desktopcommand.v1` ở `contracts/desktop-command.md`; implementation thật ở
  `shell/`. POC localhost FastAPI cũ (`upload_lab/poc/desktop_command/`) chỉ là
  bằng chứng đầu vào, không tương thích ngầm với v1.
- Bind `127.0.0.1`, port cấu hình được; xác thực bằng token phiên ngắn hạn,
  không ghi token vào log. Caller là Electron **main process**, không phải
  renderer; không bật CORS rộng. Không đưa credential web tỉnh vào command.
- Điểm bám là mẫu command queue của `UploadWorker`
  (`upload_lab/ui_qt/workers.py:83-105,211-240`), không phải một
  HTTP endpoint có sẵn hay object được phép gọi từ thread tùy ý.

Ranh giới của POC conversion/OCR:

- MarkItDown là **adapter**, không phải chủ sở hữu `ConversionEnvelope`, OCR
  policy hay provenance.
- `markitdown-ocr` đăng ký converter ưu tiên trước converter mặc định và có thể
  OCR ảnh nhúng trong PDF/DOCX/PPTX/XLSX. Vì vậy không khởi tạo một instance có
  plugin OCR rồi đưa mọi file vào mà không qua Document Router/OCR gate.
- Qwen vẫn là OCR provider duy nhất. POC adapter không được thêm provider thứ
  hai hoặc hồi sinh local OCR đang parked.
- **Cổng kiểm chứng transport:** đối chiếu 10/09/2026 trên repo cũ, vẫn đúng
  sau gộp — trong `notary_v2/routers/ocr_ai.py` chưa có OpenAI-compatible OCR
  transport (chỉ có native DashScope ở `:381-414`). Hit `compatible` trong file
  là helper so khớp trường, không phải transport; nhánh chọn `OPENAI_API_KEY`
  cũ **đã bị gỡ khỏi file** (`tests/test_ocr_ai.py:248` xác nhận env openai
  legacy bị bỏ qua). Không suy rộng kết luận này ra toàn module.
- Vì vậy, tái sử dụng **provider Qwen** không đồng nghĩa tái sử dụng nguyên
  tích hợp hiện tại. Khả năng chạy qua OpenAI-compatible là giả thuyết POC;
  chưa đạt gate thì không thay adapter production.

Nguồn kỹ thuật được kiểm tra ngày 10/09/2026:

- Playwright mô tả hỗ trợ Electron là experimental:
  <https://playwright.dev/docs/api/class-electron>.
- Electron khuyến nghị tránh `<webview>` và cân nhắc `WebContentsView` hoặc kiến
  trúc không embed nội dung:
  <https://www.electronjs.org/docs/latest/api/webview-tag>.
- Plugin OCR của MarkItDown và cơ chế converter ưu tiên:
  <https://github.com/microsoft/markitdown/tree/main/packages/markitdown-ocr>.

---

## 2. Quy tắc chọn công nghệ mới

Trước khi thêm một thư viện/dịch vụ mới, agent phải kiểm tra theo thứ tự:

1. **Bảng mục 1 đã có công nghệ cho việc này chưa?** Có → dùng nó.
2. Nếu muốn dùng thứ khác: viết được **một câu lý do kỹ thuật** vì sao cái đang
   có không đủ (không phải "cái này quen hơn", "cái này mới hơn").
3. Nếu vẫn muốn đổi → **dừng, hỏi chủ dự án**, rồi cập nhật bảng mục 1 kèm lý do.
4. Việc chưa có trong bảng → chọn, rồi **thêm dòng vào bảng** trong cùng task.

**Không được** đưa vào một OCR provider thứ hai, một ORM thứ hai, một cơ chế
queue thứ hai, hay một framework UI thứ ba mà không qua bước 3.

---

## 3. Ràng buộc thiết kế để lúc gộp không xung đột

Định hướng: gộp thành **một hệ thống, một database dùng chung**; các module trở
thành công cụ xử lý dữ liệu theo mục đích riêng. Chưa làm bây giờ. Nhưng từ giờ,
mỗi module nên tuân theo mấy điều dưới đây để lúc gộp không phải viết lại:

- **Định danh người/tài sản và tham chiếu hồ sơ chuẩn hóa giống nhau.** Xem
  `contracts/entities.md`. CCCD cùng định dạng giúp đối chiếu người, không tự
  chứng minh cùng Case; liên kết hồ sơ cần đủ phạm vi và bằng chứng. Không dùng
  CCCD hoặc thửa/tờ làm khóa chính hồ sơ để giải quyết việc gộp DB.
- **SQLite là mặc định hiện tại; đừng dùng tính năng riêng của SQLite ở tầng
  nghiệp vụ.** DB chung sau này có thể là PostgreSQL. Cụ thể: đi qua SQLAlchemy
  hoặc SQL chuẩn, tránh `rowid` ẩn, tránh dựa vào kiểu lỏng của SQLite, không
  lưu số/ngày dưới dạng chuỗi tự do.
- **ID phải không trùng giữa các module.** Đừng dùng số tự tăng bắt đầu từ 1 làm
  khóa nghiệp vụ nếu record đó sẽ đi vào DB chung. Dùng UUID hoặc tiền tố nguồn.
- **Ngày tháng lưu ISO-8601, giờ lưu kèm múi giờ hoặc quy ước rõ ràng.** Không
  lưu `dd/mm/yyyy` vào cột dữ liệu (hiển thị thì tùy).
- **Tên trường cho cùng một thứ phải giống nhau khi tạo bảng mới.** Đang có sẵn
  từ `notary_v2/docs/platform/document-intake/property-rules.md`: `so_serial`,
  `so_vao_so`, `so_thua_dat`, `so_to_ban_do`, `dia_chi`, `ngay_cap`,
  `co_quan_cap`, `dien_tich`. Module khác tạo bảng tài sản thì dùng đúng các
  tên này.
- **Không hard-code đường dẫn tuyệt đối và không hard-code môi trường.** Cấu
  hình qua `.env`.

---

## 4. Điểm gọi ra ngoài văn phòng — danh sách đầy đủ

Mặc định hệ thống chạy trong LAN. Mọi lần gọi ra Internet phải nằm trong danh
sách này; thêm điểm mới là quyết định kiến trúc, phải hỏi.

| Điểm | Ra đâu | Gửi gì | Module |
|---|---|---|---|
| Cloud OCR | DashScope (Alibaba) | ảnh giấy tờ khách hàng | `notary_v2` (gọi trực tiếp; qua `shell/` vẫn là cùng engine này) |
| Upload CSDL công chứng | web tỉnh Nam Định (`congchungnamdinh.ninhbinh.gov.vn`) | dữ liệu hồ sơ đã hoàn tất | `upload_lab` (kể cả khi chạy qua `shell/`) |
| Zalo | server Zalo | tin nhắn/ảnh của tài khoản văn phòng | `notary_v2`; `notaryoffice` (dự kiến) |

`notaryoffice` Sentinel trên máy trạm: **không gọi Internet**, chỉ gửi JSON về
Hub trong LAN.

Lưu ý pháp lý: ảnh CCCD gửi ra dịch vụ OCR nước ngoài thuộc phạm vi **Nghị định
13/2023**. Đây là quyết định đã có chủ ý, không phải mặc định — đừng mở thêm
điểm gọi ra ngoài mà không hỏi.

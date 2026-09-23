# Từng repo: giải bài toán gì — feature gì — công nghệ gì

Mỗi repo được mô tả theo đúng ba câu hỏi đó, cộng thêm một mục **"KHÔNG phải"** để
chặn các giả định sai mà agent trước đã ghi vào folder này.

Mọi thông tin dưới đây đã được đối chiếu với file thật trong repo. Chọn công nghệ
mới → đọc [`TECH_STACK.md`](./TECH_STACK.md) trước.

Cập nhật: 10/09/2026

| Repo | Đường dẫn | Git | Trạng thái |
|---|---|---|---|
| `notary_v2` | `D:\notary_v2` | `github.com/minhnhatnguyen6297-a11y/notary_v2` | Đang phát triển; chưa triển khai production |
| `upload_lab` | `D:\upload_lab_repo` | `github.com/minhnhatnguyen6297-a11y/upload_lab` | Đang phát triển; chưa triển khai production |
| `notaryoffice` | `D:\notaryoffice` | Git local đã init; chưa cấu hình remote | **Chỉ có tài liệu, chưa có code** (`notaryoffice/` chỉ chứa `intent.md`) |
| `researchskill` | `D:\researchskill` | `github.com/minhnhatnguyen6297-a11y/researchskill` | **Ngoài phạm vi** |

`excelTK` là dự án riêng, không phải sản phẩm con của hệ thống công chứng và
không thuộc goal Electron MIN-56/G1.

Snapshot Git `notaryoffice` ngày 10/09/2026: HEAD `1c1b160`, 4 commits;
kiểm tra bằng `git log -1`, `git rev-list --count HEAD`, `git remote -v`
(không có remote). Đây là trạng thái kiểm chứng, không phải điều kiện kiến trúc.

---

## 1. `notary_v2`

### Giải bài toán gì

Chuyên viên phải **gõ lại bằng tay** thông tin đã nằm sẵn trên giấy tờ khách hàng
(CCCD, sổ đỏ, giấy khai tử, đăng ký kết hôn) vào mẫu hợp đồng Word — mỗi hồ sơ
một lần, mỗi lần vài chục trường. Gõ lại thì chậm và dễ sai; sai một số thửa hoặc
một số CCCD trong hợp đồng công chứng là lỗi nặng.

`notary_v2` đọc giấy tờ ra dữ liệu có cấu trúc, rồi sinh thẳng file Word.

### Feature gì

- **Intake giấy tờ bằng OCR AI** — upload ảnh/PDF giấy tờ, trích ra các trường
  (họ tên, CCCD, ngày cấp, serial GCN, thửa/tờ, địa chỉ, diện tích), parser regex
  ba nhóm (CCCD / sổ đỏ / giấy khai tử), **người dùng soát trước khi dùng**.
- **Sinh văn bản Word** (`services/word_engine.py`) — điền dữ liệu vào template
  hợp đồng, giữ định dạng.
- **Engine thừa kế** (`services/inheritance_engine.py`) — dựng hàng thừa kế, phần
  chia, sinh văn bản thừa kế. Case Workspace hiện **inheritance-first**.
- **Case Workspace: Stage / Pool / Diagram** — gom giấy tờ theo hồ sơ, có sơ đồ
  quan hệ đương sự.
- **Fast text audit** (`services/fast_audit/`) — CLI độc lập soát sai lệch giữa
  văn bản đã soạn và dữ liệu gốc bằng so khớp mờ. Không dính vào web OCR.
- **Đọc QR trên giấy tờ** — CCCD gắn chip có QR, dữ liệu chính xác hơn OCR.
- **Zalo Document Inbox** (spec APPROVED) — nhận text/media qua `zca-js`, chọn lô
  ảnh, xuất JSON/Excel/PDF vào hồ sơ. Ranh giới quyền riêng tư:
  `OPEN_DECISIONS.md` B2.
- **Job OCR nền** — OCR nhiều trang chạy bất đồng bộ qua Celery, không chặn UI.

### Công nghệ gì

| Lớp | Công nghệ |
|---|---|
| Backend | Python **FastAPI** 0.111 + uvicorn (`main.py`) |
| Frontend | **Jinja2 template + static** (`frontend/templates`, `frontend/static`) — server-rendered, **không có** SPA, không có `package.json` |
| OCR | Qwen qua DashScope **native multimodal API** (`notary_v2/routers/ocr_ai.py:38-39,381-414`); endpoint và gate candidate tại `TECH_STACK.md` §1/§1.1 |
| DB | SQLite `notary.db` chứa cả bảng `ocr_jobs` và Zalo (`notary_v2/database.py:8-24`, `models.py:161-171,186-300`), qua SQLAlchemy; không nhầm với file hạ tầng `ocr_jobs.db` |
| Job nền | Celery: broker và result backend mặc định cùng dùng `ocr_jobs.db`; cấu hình tại `notary_v2/celery_app.py:5-11` |
| PDF / ảnh | PyMuPDF (`fitz`), Pillow |
| QR | `zxing-cpp` (tùy chọn) |
| Word / Excel | `python-docx`, `openpyxl` |
| So khớp mờ | `rapidfuzz` |
| Zalo | `zca-js` (Node) như connector thay thế được |

Cấu hình qua `.env` (mẫu ở `.env.example`). **Không bao giờ ghi giá trị key vào
tài liệu.**

### KHÔNG phải

- **Không phải "core platform"** mà hai repo kia gọi vào. Là sản phẩm ngang hàng;
  không repo nào import code của nó.
- **Không nhận dữ liệu từ `upload_lab`.** Không có luồng nào cả.
- **Local OCR đang parked.** Có config `vietocr vgg_transformer` trong repo nhưng
  đường local **không dùng**. Mở lại cần redesign được duyệt riêng.
- **Chưa có shared abstraction cho Stage/Pool** — có chủ ý, chờ domain thật thứ hai.

**Ràng buộc khi sửa repo này:** SOT nội bộ là `notary_v2/docs/` — domain spec
đã duyệt, ADR và platform contract. Repo gốc `D:\notary_v2` còn duy trì
`AGENTS.md` với scope-lock chặt (SCOPE BREAK REQUEST, review gate); file đó
không được snapshot vào monorepo.

---

## 2. `upload_lab`

### Giải bài toán gì

Hai vấn đề chồng lên nhau:

1. Văn phòng **đã có** phần mềm quản lý hồ sơ công chứng, nhưng phần mềm đó
   **không có API để lấy dữ liệu ra**. Dữ liệu bị khóa bên trong. Muốn dùng lại
   dữ liệu cũ chỉ còn một đường: đọc từ chính **các file Word chuyên viên đã
   soạn**. **Đó là lý do `upload_lab` ra đời** (`OPEN_DECISIONS.md` B1).
2. Hàng nghìn hồ sơ Word cũ phải được **nhập tay lên web CSDL công chứng tỉnh** —
   mở từng file, đọc bằng mắt, gõ lại vào form web. Tốn hàng trăm giờ.

`upload_lab` đọc file Word cũ → trường có cấu trúc → điền web tỉnh → người dùng
kiểm tra/xác nhận lưu (`upload_lab_repo/README.md:15,32-47`).

### Feature gì

Ba giai đoạn:

1. **Quét & trích xuất** (`batch_scan.py`, `extract_contract.py`)
   - Đọc `.docx` bằng `python-docx` **giữ đúng thứ tự đoạn + bảng** — điểm mấu
     chốt, đọc sai thứ tự thì thông tin Bên A và Bên B trộn vào nhau.
   - Đọc `.doc` cũ bằng **Windows IFilter `query.dll`**, không cần cài Word.
   - Phân loại văn bản: `transfer_contract`, `asset_commitment`,
     `mortgage_contract`, `inheritance_partition`, `inheritance_refusal`,
     `generic`; phân loại tài sản `loai_tai_san`.
   - Ghi JSON + SQLite; quét khớp là `matched`, trích xuất thành công là
     `extracted` (`upload_lab_repo/batch_scan.py:713,786`).
2. **Đối chiếu sổ công chứng** (`ui/services/contract_book_audit.py`,
   `scan_classification_service.py`)
   - So danh sách quét với sổ Excel, **chuẩn hóa số công chứng** về `xxx/yyyy`
     (`428.2026/CCGD` → `428/2026`; `2433.2025/PCDS/CCGD` → `2433/2025`).
   - **Phát hiện số bị hở** theo năm (gap detection).
   - Phân loại hàng đợi upload: `chưa có` / `đã có` / `sai format` / `sai năm` /
     `không có số`.
3. **Upload** (`playwright_uploader.py`, `uploader_selectors.py`)
   - Chromium điều khiển web CSDL công chứng **tỉnh Nam Định**, session ở
     `nd_storage_state.json`.
   - **Dry-run** (điền hết, dừng trước nút Lưu để người kiểm tra) và **Finalize**
     (ghi nhận lưu thành công → `uploaded_success`,
     `upload_lab_repo/batch_scan.py:353-364`).

**Snapshot trạng thái registry — không phải enum contract xuyên repo:**

| Nhóm | Giá trị thật | Nguồn trong `upload_lab_repo` |
|---|---|---|
| Quét/trích xuất thành công | `matched`, `extracted` | `batch_scan.py:713,786` |
| Chuẩn bị đầy đủ/một phần | `prepared_dry_run`, `prepared_partial` | `playwright_uploader.py:81-83,2011,2141-2157` |
| Đã upload thành công | `uploaded_success` | `batch_scan.py:353-364` |
| Thất bại | `extract_failed`, `upload_failed` | `batch_scan.py:744`; `playwright_uploader.py:2170` |
| Bỏ qua | `skipped_unsupported`, `skipped_old_file`, `skipped_duplicate` | `batch_scan.py:575,627,687` |

Mười giá trị trên đối chiếu source ngày 10/09/2026, không khẳng định thứ tự
chuyển trạng thái hay thay thế quy tắc nội bộ. Snapshot chỉ tạm đặt ở đây vì
`upload_lab_repo/README.md:28` còn mô tả sai trạng thái quét. Follow-up ở repo
con: sửa README, đưa enum về tài liệu owner; sau đó ở đây chỉ giữ dẫn chiếu.

UI desktop cho chuyên viên tự chạy (`run.bat` bootstrap venv + mở UI), đóng gói
ra `_release/`.

### Công nghệ gì

| Lớp | Công nghệ |
|---|---|
| UI | **PySide6 / Qt** (`ui_qt/`) |
| Đọc `.docx` | `python-docx`, đọc theo cấu trúc (đoạn + bảng theo thứ tự) |
| Đọc `.doc` | **Windows IFilter `query.dll`** |
| Tự động hóa web | **Playwright** (Chromium) |
| DB | SQLite `registry.sqlite3`; output JSON trong `output/` |
| Excel | `openpyxl` |
| Trích xuất | regex có label-anchor (`docs/regex-rules.md`) |

### KHÔNG phải

- **Không phải "lab OCR ảnh".** Đầu vào là **file Word**, không phải ảnh scan.
  Không có OCR ảnh trong repo này.
- **Không có pipeline "thuật toán kiểm thử rồi chuyển sang `notary_v2`".** Đây là
  sản phẩm production độc lập.
- **Không tách `thửa`/`tờ` thành hai trường riêng.** Hiện lưu chung. Chỉ cần tách
  khi thật sự nối với `notaryoffice`.
- **Không đọc dữ liệu từ phần mềm quản lý hồ sơ cũ.** Không có API (B1).
- **Không tự lưu.** Luôn cho người soát ở dry-run trước.

---

## 3. `notaryoffice`

> **Trạng thái: TÀI LIỆU THIẾT KẾ. Đã git init local, chưa có code.**
> Mọi thứ dưới đây là **dự định**, không phải hiện thực. Đừng mô tả nó như phần
> mềm đang chạy.

Nguồn trạng thái code: `notaryoffice/` chỉ chứa `intent.md`; trạng thái Git theo snapshot
đầu tài liệu.

### Giải bài toán gì

Mỗi chuyên viên giữ 30–70 hồ sơ cùng lúc. Không ai giữ được toàn bộ tình trạng
trong đầu, và **không ai có thời gian ghi chép** — nên mọi phần mềm quản lý yêu
cầu nhập liệu tay đều chết sau hai tuần.

`notaryoffice` không mở form cho ai nhập. Nó **thu dấu vết thao tác hằng ngày**
trên các máy trạm (lưu file Word, in, đổi tên, tải ảnh Zalo) rồi **tự gom thành
một record hồ sơ**. Nhân viên chỉ xác nhận, không nhập liệu.

Mục tiêu cụ thể: trả lời "hồ sơ bà Gái đang ở đâu?" dưới 1 giây.

### Feature gì (dự kiến)

- **Sentinel trên ~6 máy trạm** — theo dõi thay đổi file bằng
  `ReadDirectoryChangesW`, debounce cửa sổ trượt 3–5 phút để không bắn event mỗi
  lần Ctrl+S.
- **Dự kiến đọc nội dung tài liệu bằng IFilter** ra plain text. Khả năng đọc khi
  Word còn giữ file và số đo thời gian **chưa được kiểm chứng trên 6 máy thật**
  (`OPEN_DECISIONS.md` A1). Nếu đạt, gửi về Hub dưới dạng **JSON 20–50KB, không
  gửi file nhị phân.**
- **Bắt sự kiện in** qua Print Spooler **Event ID 307** — tín hiệu xương sống thứ
  hai, vì "in ra" gần như luôn nghĩa là hồ sơ tới một mốc thật.
- **Buffer SQLite cục bộ trên máy trạm** — mất LAN thì xếp hàng FIFO, LAN về thì
  đẩy, không mất dữ liệu.
- **Central Hub**: nhận → chuẩn hóa → **Evidence Record** → **Draft Case Builder**
  → **popup xác nhận 1 lần** → **Search Projection** để tra cứu.
- **Xếp hạng ứng viên thay vì loại bỏ** — độ tin cậy dùng để *sắp thứ tự* các hồ
  sơ có thể khớp, không dùng để im lặng bỏ dữ liệu.
- **Timeline hồ sơ** — `DRAFT_PRINTED` / `FINAL_PRINTED` và các mốc khác.
  Lưu ý: **không** phân biệt bằng số bản in, vì Spooler không cho biết số bản in
  (`OPEN_DECISIONS.md` A2).
- **Đọc Zalo của tài khoản chung văn phòng**, chỉ trên máy chủ, theo ranh giới đã
  chốt ở `OPEN_DECISIONS.md` B2. **Làm, không hoãn.**
- **Lớp LLM (OpenClaw) giới hạn 10–15% ca mơ hồ**, và phải thay thế được — không
  để LLM thành đường dẫn chính.

Dự kiến ~14 bảng (`document_snapshots`, `document_deltas`, `print_jobs`,
`calibration_logs`, `case_timeline_events`, …).

### Công nghệ gì (dự kiến)

| Lớp | Công nghệ | Ràng buộc |
|---|---|---|
| Agent máy trạm | **C# .NET 8** | <30MB RAM, <0.5% CPU — chạy trên máy nhân viên đang làm việc |
| Đọc nội dung | Windows IFilter | Candidate đã chọn trong thiết kế; hành vi khi Word giữ file còn chờ đo A1 |
| Theo dõi file | `ReadDirectoryChangesW` | |
| Tín hiệu in | Print Spooler Event ID 307 | Không có số bản in (A2) |
| Buffer cục bộ | SQLite | FIFO, đẩy khi LAN hồi |
| Central Hub | **Python FastAPI** + DB, 1 máy/NAS trong LAN | Cùng stack `notary_v2` để sau này gộp dễ |
| Truyền tin | JSON qua LAN | Không gửi file nhị phân |

**Sentinel không gọi Internet.** Chỉ nói chuyện với Hub trong LAN.

### Tài liệu trong repo — Nguồn chân lý duy nhất

| File | Vai trò |
|---|---|
| `intent.md` | **Nguồn Chân lý Duy nhất (v1.0 Consolidated).** Hợp nhất toàn diện: Tầm nhìn, phân tích nghiệp vụ, Hybrid Pipeline, Evidence Record, Draft Case, 14 bảng DB, quyết định đã chốt, phương án đã loại, lộ trình & chi phí |

### KHÔNG phải

- **Không phải phần mềm giám sát nhân viên.** Không quay màn hình, không
  keylogger, không theo dõi web cá nhân, không dùng để chấm công hay đánh giá
  năng suất. Quan tâm hồ sơ, không quan tâm người.
- **Không phải phần mềm đang chạy.** Chưa có code.
- **Không đọc gì ngoài thư mục nghiệp vụ đã thống nhất bằng văn bản.**
- **Không đọc DB của `upload_lab` hay `notary_v2`** ở thời điểm này.
- **Hai lỗi regex cũ đã sửa trong `intent.md` v1.0 §7.2:** CCCD là
  `\b\d{12}\b`, serial GCN là `[A-Z]{2}\s*\d{6,8}`
  (`notaryoffice/intent.md:325-326`). Không còn là blocker sửa intent;
  chuẩn thống nhất ở
  [`contracts/entities.md`](../../contracts/entities.md).

**Ba câu còn phải đo trên máy thật trước khi code:** `OPEN_DECISIONS.md` A1, A3,
A4 (A2 đã có câu trả lời = Không).

---

## 4. `researchskill` — NGOÀI PHẠM VI

Là **skill hỗ trợ AI agent làm việc coding** (`researching-solutions`,
`review-skill.md`, `evaluation/`, `search/`).

Không liên quan gì đến nghiệp vụ công chứng. **Không phải** "AI tra cứu luật công
chứng, luật đất đai" như tài liệu cũ ghi sai. Đừng đưa nó vào sơ đồ kiến trúc hệ
thống công chứng.

---

## 5. `systemdocs` — folder này, và thẩm quyền của nó

- **Đường dẫn:** `D:\systemdocs`. `main` không có code/runtime. Nhánh
  `electron-system-shell` là ngoại lệ owner chọn làm nhánh tích hợp cấp hệ thống;
  runtime chỉ được thêm theo `ELECTRON_G1_PLAN.md` và contract đã duyệt.
- **Quyết định:** ranh giới sản phẩm, chuẩn hóa khóa định danh
  (`contracts/entities.md`), **lựa chọn công nghệ** (`TECH_STACK.md`), và những gì
  đang mở (`OPEN_DECISIONS.md`).
- **Không quyết định:** hành vi nội bộ của một repo. Khi xung đột, docs của repo
  con thắng về hành vi nội bộ — nhưng phải báo lại để sửa ở đây theo
  [`AGENTS.md`](../../AGENTS.md).

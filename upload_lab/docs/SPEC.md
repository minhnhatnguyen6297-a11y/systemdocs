# SPEC — upload_lab (Nguồn SOT nghiệp vụ duy nhất)

Đặc tả nghiệp vụ của module `upload_lab` trong monorepo `systemdocs`
(nhánh `consolidate/monorepo`). Chi tiết regex ở `docs/regex-rules.md`, UI ở
`docs/spec_UI.md` — khi xung đột, file này + code thắng và file này phải được
sửa lại.

Cập nhật: 16/09/2026 (sau khi gộp monorepo; trước đây repo `upload_lab_repo`).

## 1. Bài toán

Văn phòng **đã có** phần mềm quản lý hồ sơ công chứng nhưng nó **không có API
để lấy dữ liệu ra** (`../../OPEN_DECISIONS.md` B1 — đã chốt, đừng đề xuất lại). Hàng
nghìn hồ sơ Word cũ trên ổ đĩa phải nhập tay lên web CSDL công chứng tỉnh —
mở từng file, đọc bằng mắt, gõ lại vào form web.

`upload_lab` đọc file Word cũ → trường có cấu trúc → điền web tỉnh → **người
dùng kiểm tra và tự bấm Lưu**.

## 2. Pipeline 3 giai đoạn (hiện trạng)

### Giai đoạn 1 — Quét & trích xuất (`batch_scan.py`, `extract_contract.py`)

- `.docx` đọc bằng `python-docx` **giữ đúng thứ tự đoạn + bảng** — đọc sai
  thứ tự thì trộn Bên A / Bên B.
- `.doc` cũ đọc bằng **Windows IFilter `query.dll`**, không cần cài Word.
- Phân loại văn bản: `transfer_contract`, `asset_commitment`,
  `mortgage_contract`, `inheritance_partition`, `inheritance_refusal`,
  `generic`; phân loại tài sản `loai_tai_san`.
- Ghi `output/*.json`, `registry.sqlite3`, manifest `runs/<timestamp>.json`.

### Giai đoạn 2 — Đối chiếu sổ công chứng (`ui/services/`)

- `contract_book_audit.py`: đọc sổ Excel từ web, chuẩn hóa số công chứng về
  `xxx/yyyy` (`428.2026/CCGD` → `428/2026`), **phát hiện số bị hở** theo năm.
- `scan_classification_service.py`: phân loại hàng đợi — `chưa có` / `đã có` /
  `sai format` / `sai năm` / `không có số`.

### Giai đoạn 3 — Upload (`playwright_uploader.py`, `uploader_selectors.py`)

- Playwright điều khiển **Chromium headed riêng** tới web CSDL công chứng tỉnh
  (hiện `congchungnamdinh.ninhbinh.gov.vn`); session ở `nd_storage_state.json`,
  **không lưu mật khẩu** — người dùng tự đăng nhập.
- **Dry-run là mặc định**: điền hết, mở tab đã điền, **dừng trước nút Lưu**;
  người dùng soát và tự bấm Lưu. App nhận diện đã lưu qua phản hồi `POST
  /api/hoso` rồi ghi `uploaded_success`.
- Finalize (ghi nhận lưu thành công) chỉ sau khi người xác nhận.

### Trạng thái registry (enum thực tế trong code)

| Nhóm | Giá trị | Nguồn |
|---|---|---|
| Quét/trích xuất thành công | `matched`, `extracted` | `batch_scan.py` |
| Chuẩn bị đủ / một phần | `prepared_dry_run`, `prepared_partial` | `playwright_uploader.py` |
| Đã upload | `uploaded_success` | `batch_scan.py` |
| Thất bại | `extract_failed`, `upload_failed` | `batch_scan.py`, `playwright_uploader.py` |
| Bỏ qua | `skipped_unsupported`, `skipped_old_file`, `skipped_duplicate` | `batch_scan.py` |

Đây là enum nội bộ module, không phải contract xuyên module.

## 3. Dữ liệu module sở hữu

- `registry.sqlite3` — registry quét/trạng thái upload; `output/*.json` —
  trường đã trích; `runs/*.json` — manifest theo đợt; `nd_storage_state.json`
  — session web tỉnh.
- `shell/sidecar` gọi nghiệp vụ qua `upload_adapter.py` (import trong-process):
  `upload.scan` → `batch_scan.run_batch_scan`, `upload.audit_excel` →
  `contract_book_audit`, `upload.env_check` → `environment_check_service`,
  phiên browser qua `upload_session.py` (`NamDinhUploaderSession` trên thread
  `g1-upload-browser`, dry-run, `waiting_user` ở login/review).

## 4. UI & vận hành

- UI desktop **PySide6 + qfluentwidgets** (`ui_qt/`, không file `.ui`); worker
  QThread ở `ui_qt/workers.py`. `run.bat`/`bootstrap_ui.py` bootstrap venv.
- Service layer tách khỏi Qt ở `ui/services/` để shell tái dùng.
- `poc/` là **tiền thân/thí nghiệm, không phải production**:
  `poc/desktop_command/` = POC của kiến trúc `shell/sidecar`;
  `poc/conversion_benchmark/` = harness MarkItDown song song với
  `notary_v2/tools/document_conversion_poc/`.
- Test: `tests/` (unittest, 13 file); đánh giá regex qua
  `regex_review_samples/` + `review_regex_samples.py`.

## 5. Quy chuẩn trường web form

| Trường web | Quy tắc |
|---|---|
| `ten_hop_dong` | chuẩn hóa theo loại văn bản |
| `so_cong_chung` | canonical `xxx/yyyy`, bỏ hậu tố nghiệp vụ (`../../contracts/entities.md` §5) |
| `ngay_cong_chung` | ngày lập HĐ trong lời chứng/tiêu đề |
| `nhom_hop_dong`, `loai_tai_san` | ánh xạ danh mục dropdown web tỉnh |
| `cong_chung_vien`, `thu_ky` | nhận diện hoặc mặc định cấu hình |
| `nguoi_yeu_cau`, `duong_su`, `tai_san` | bóc theo khối Bên A/B; tài sản là text mô tả, **chưa tách thửa/tờ riêng** |

Toàn bộ regex nhận diện: `docs/regex-rules.md` (quy tắc phải cập nhật cùng
code — xem `AGENTS.md`).

## 6. KHÔNG phải / đã loại

- **Không phải "lab OCR ảnh"** — đầu vào là file Word, không OCR ảnh.
- **Không đọc API/DB phần mềm quản lý cũ** — không có API (B1).
- **Không tự Lưu/Finalize** — luôn dry-run cho người soát trước.
- **Không điều khiển cửa sổ Electron bằng Playwright** — Chromium headed do
  Python quản lý, tách khỏi shell (`../../TECH_STACK.md` §1.1).
- **Không share code với `notary_v2`** — không cross-import.

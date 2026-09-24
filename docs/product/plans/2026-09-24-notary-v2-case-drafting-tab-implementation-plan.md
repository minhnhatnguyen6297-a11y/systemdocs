# notary_v2 — Tab Soạn hồ sơ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

Các ô `- [ ]` là danh sách kiểm khi review, không phải trạng thái thực thi. Linear là nơi giữ trạng thái task; `.agent/tasks/<ID>/` giữ tiến độ và bằng chứng. [MIN-68](https://linear.app/minhnotary/issue/MIN-68/migrate-document-reviewocr-vao-electron) là issue bao trùm hiện có. Trước khi code, tách các chặng dưới đây thành issue con để contract và runtime không nằm trong cùng một task.

**Goal:** Hoàn thiện tab `Soạn hồ sơ` trong module `notary_v2`: nhận dữ liệu từ file hoặc nhập tay, chuẩn hóa thành Người/Tài sản để người dùng xác nhận, sắp quan hệ bằng Pool + sơ đồ, lưu hồ sơ, rồi xuất nhiều văn bản Word vào thư mục người dùng chọn.

**Architecture:** Electron renderer chỉ hiển thị và nhận thao tác. Electron main giữ quyền chọn/mở file. Python sidecar nhận lệnh `desktopcommand.v1` và gọi dịch vụ thật trong `notary_v2`. Stage là nguồn dữ liệu đã xác nhận; Pool luôn được tính từ Stage trừ các phần tử đã đặt lên sơ đồ; engine Python mới được phép tính nghiệp vụ. Backend giả và backend thật cùng tuân một contract, nên frontend không có hai luồng riêng.

**Tech Stack:** Electron + JavaScript/CSS thuần trong `shell/`; Python/FastAPI/SQLAlchemy trong sidecar và `notary_v2`; SQLite hiện có; Qwen OCR hiện có; `python-docx`, `openpyxl`, `PyMuPDF` hiện có. Không thêm framework UI, thư viện sơ đồ hoặc database mới trong kế hoạch này.

**Spec:** `notary_v2/docs/domains/inheritance/workflow.md`, `notary_v2/docs/domains/inheritance/ux.md`, `notary_v2/docs/domains/inheritance/word-export.md`, `notary_v2/docs/platform/document-intake/spec.md`, `contracts/desktop-command.md`, và quyết định owner ngày 23–24/09/2026 được khóa lại trong §1 của plan này.

## Global Constraints

- Trình tự bắt buộc: **Product Flow → UI/UX tổng thể → API Contract → Mock Backend và Real Backend → Frontend → kiểm chứng đóng gói**.
- Contract mới phải được duyệt/publish trong task riêng trước khi sửa runtime. Không tạo contract và triển khai contract trong cùng issue.
- Đích production là Electron. Web cũ `notary_v2/frontend/templates/cases/form.html` chỉ là bằng chứng về hành vi và bản fallback cho đến cutover; không xóa trong plan này.
- Ba module nghiệp vụ chính trên UI là `notary_v2`, `upload_lab`, `notaryoffice`. `Tổng quan hồ sơ`, `Soạn hồ sơ`, `Word` là ba tab **bên trong** `notary_v2`; Excel import nằm trong Soạn hồ sơ, không là module chính. Tra cứu và Trạng thái/Cài đặt là tiện ích của shell.
- Không có nút, popup, command hay trạng thái Zalo trong tab Soạn hồ sơ. Zalo là phần mềm riêng. Nguồn dữ liệu trao đổi trong tương lai phải đi qua contract riêng, không làm UI Zalo quay lại tab này.
- Stage là nguồn chuẩn đã xác nhận. Kết quả OCR/import chỉ là gợi ý `observed`; không được tự ghi vào hồ sơ, tự tạo quan hệ, tự chọn người nhận hoặc tự xuất Word.
- Pool không được lưu như nguồn dữ liệu riêng: `Pool = Stage đã commit - phần tử đang được gán trên Diagram`.
- Sơ đồ không được sửa thông tin Người/Tài sản trong Stage. Xóa thẻ khỏi sơ đồ chỉ trả thẻ về Pool nếu Stage vẫn còn thẻ đó.
- V1 backend thật chỉ cam kết loại việc **thừa kế**. Contract có `case_type` và capability để mở rộng, nhưng loại việc chưa có engine phải hiện `Chưa hỗ trợ`, không chạy logic giả.
- Không lưu CCCD, dữ liệu OCR, raw text hoặc ảnh giấy tờ vào log, diagnostics hay `localStorage`. Draft chưa xác nhận chỉ sống trong phiên UI; khi rời màn phải cảnh báo nếu có thay đổi chưa lưu.
- Mọi thao tác ghi dùng `base_revision` để tránh ghi đè thay đổi mới hơn. Khi xung đột, UI cho tải bản mới hoặc giữ bản nháp để sao chép; không có nút “ghi đè cưỡng bức”.
- Xuất Word: checkbox là chọn **nhiều văn bản riêng**; mỗi văn bản tạo một `.docx` riêng trong folder đã chọn; không ZIP; không ghi đè; trùng tên tự thêm `_2`, `_3`, ...; file nào lỗi báo đúng file đó và giữ nguyên các file đã thành công.
- Mock chỉ chạy ở chế độ phát triển, phải có nhãn `Dữ liệu mô phỏng`; bản đóng gói production luôn dùng backend thật hoặc báo không khả dụng.
- Mỗi task runtime viết test lỗi trước, thấy test fail đúng lý do, rồi mới viết code. Trước handoff dùng `superpowers:verification-before-completion`.

## 1. Product Flow và UI/UX đã khóa

### 1.1 Luồng chính

```text
Mở hồ sơ từ Tổng quan
  → tải Workspace
  → nhập file / dán text / nhập Excel / thêm tay
  → kiểm tra các gợi ý Người và Tài sản
  → đưa gợi ý đã chọn vào Stage (vẫn là draft UI)
  → bấm Cập nhật Stage
  → backend kiểm tra và commit toàn bộ Stage
  → Pool tự tính lại
  → kéo thả hoặc chọn menu để gán quan hệ trên sơ đồ
  → backend đánh giá, báo thiếu/sai, trả kết quả tính
  → bấm Lưu sơ đồ
  → bấm Xuất Word
  → chọn nhiều văn bản + một folder đích
  → tạo từng DOCX độc lập
  → hiển thị Đã lưu/Lỗi cho từng văn bản
```

### 1.2 Bố cục desktop

- Thanh ngữ cảnh trên cùng: nút quay lại, mã/tên hồ sơ, loại việc, trạng thái lưu; không có breadcrumb dài hoặc thẻ thống kê.
- Tầng Stage ngay dưới thanh ngữ cảnh:
  - card `Tài sản` bên trái khoảng 36%; đầu card có `Nhập dữ liệu`, `+ Tài sản`;
  - card `Người` bên phải khoảng 64%; đầu card có `Nhập Excel`, `OCR giấy tờ`, `+ Người`, `Cập nhật`;
  - chỉ hiện trường quan trọng trên dòng; bấm dòng mở phần chi tiết.
- Tầng quan hệ nằm ngay dưới Stage:
  - `Pool` bên trái khoảng 22%;
  - sơ đồ bên phải khoảng 78%;
  - toolbar gọn: `Lưu sơ đồ`, `Xem cách tính`, `Xuất Word`, menu `⋯`.
- Ở cửa sổ hẹp dưới 1.000 px, hai card Stage xếp dọc; Pool và sơ đồ vẫn giữ cuộn ngang thay vì ép thẻ quá nhỏ.
- Phong cách: nền `#f3f4f8`, card trắng, viền `#dfe3e9`, rail tối `#121418`, màu chính `#d9f76a`, cảnh báo `#ffe4d6`, card 16 px, control 12 px, vùng bấm tối thiểu 44 px.

### 1.3 Nút và màn hình con

| Vị trí | Nút/thao tác | Màn hình con/kết quả | Dữ liệu được phép đổi |
|---|---|---|---|
| Tài sản | `Nhập dữ liệu` | Popup nhận ảnh/PDF/Word/text | Chỉ tạo gợi ý; chưa đổi Stage |
| Người | `Nhập Excel` | Cùng popup intake, lọc `.xlsx` | Chỉ tạo gợi ý; chưa đổi Stage |
| Người | `OCR giấy tờ` | Chọn ảnh/PDF → review kết quả | Chỉ tạo gợi ý; chưa đổi Stage |
| Stage | `+ Người`, `+ Tài sản` | Drawer/form ngắn | Thêm dòng draft UI |
| Stage | `✕` trên dòng | Không mở popup | Xóa dòng draft; chỉ có hiệu lực sau `Cập nhật` |
| Stage | `Cập nhật` | Lỗi nằm ngay đúng dòng; thành công cập nhật Pool | Commit Stage theo một transaction |
| Pool | Kéo thả thẻ | Gợi ý slot trên Diagram | Chỉ đổi draft Diagram |
| Pool | Menu `Gán vị trí` | Popup chọn vai trò/quan hệ | Cách thay thế kéo thả, cùng kết quả |
| Diagram | `Chủ đất`, `Nhận` | Trạng thái ngay trên card | Chỉ đổi draft Diagram cho tài sản hiện tại |
| Diagram | `Lưu sơ đồ` | Banner thành công/lỗi | Commit Diagram, không đổi Stage |
| Diagram | `Xem cách tính` | Panel thu gọn trong vùng sơ đồ | Chỉ đọc output engine |
| Toolbar | `Xuất Word` | Popup chọn nhiều văn bản và folder | Chỉ tạo file đầu ra |
| Popup | `×` | Đóng/ẩn | Không tự lưu, không tự xóa kết quả |

### 1.4 Các trạng thái UI bắt buộc

- Đang tải Workspace.
- Hồ sơ không tồn tại.
- Hồ sơ đã khóa: toàn bộ trường chỉ đọc, vẫn xem/sao chép được.
- Stage rỗng, Pool rỗng, Diagram chưa có gán.
- Có draft chưa cập nhật.
- OCR/import thành công một phần, lỗi theo từng nguồn.
- Stage validation lỗi theo từng dòng/trường.
- `workspace_conflict` do revision cũ.
- Engine/Qwen không khả dụng.
- Sơ đồ có cảnh báo nghiệp vụ hoặc trường hợp chưa hỗ trợ.
- Xuất Word: đang chạy, thành công toàn bộ, thành công một phần, lỗi toàn bộ.

## 2. API Contract đích

Contract task phải publish các command sau dưới envelope `desktopcommand.v1`:

| Command | Mục đích | Tính chất |
|---|---|---|
| `notary.workspace_get` | Lấy case, Stage Người/Tài sản, Diagram, revision và capability | read-only |
| `notary.intake_analyze` | Đọc ảnh/PDF/DOCX/XLSX/text và trả gợi ý chuẩn hóa có nguồn | long-running, không commit |
| `notary.workspace_commit_stage` | Commit toàn bộ Stage Người/Tài sản với `base_revision` | atomic write |
| `notary.diagram_evaluate` | Kiểm tra/tính thử draft Diagram | read-only theo DB, không persist draft |
| `notary.diagram_save` | Lưu Diagram đã hợp lệ với `base_revision` | atomic write |
| `notary.word_export_options` | Trả danh sách văn bản/mẫu và lý do sẵn sàng hoặc bị chặn | read-only |
| `notary.word_export_batch` | Tạo nhiều DOCX vào một directory FileRef | long-running, per-item result |

Workspace result tối thiểu:

```json
{
  "schema_version": "notary.case-drafting.v1",
  "case": {
    "id": 42,
    "case_type": "inheritance",
    "document_type": "khai_nhan",
    "status": "draft",
    "locked": false,
    "revision": 7
  },
  "stage": { "people": [], "assets": [] },
  "diagram": {
    "domain": "inheritance",
    "state": {},
    "render_model": null,
    "warnings": []
  },
  "capabilities": {
    "intake": ["image", "pdf", "docx", "xlsx", "text"],
    "diagram": true,
    "word_export": true
  }
}
```

Kiểu ID/version không được đổi giữa mock và real:

- `row_id`: UUID v4 do UI tạo, ổn định qua commit/reload và dùng để gắn lỗi đúng dòng;
- `entity_id`: số nguyên DB hoặc `null` trước lần commit đầu;
- `case.id`: số nguyên;
- `revision` và `base_revision`: số nguyên từ 1 trở lên;
- `source_id`, `suggestion_id`: UUID v4;
- `document_key`: chuỗi lowercase `snake_case`, ổn định dù đổi tên hiển thị hoặc template;
- ngày không có giờ dùng `YYYY-MM-DD`; thời điểm dùng ISO-8601 có múi giờ.

Intake result phải tách rõ `raw_value`, `normalized_value`, `observation_state`, `confidence`, `source_refs`, warning và lỗi theo từng nguồn. Kết quả không có field `confirmed=true`.

Batch Word result tối thiểu:

```json
{
  "kind": "word_export_batch",
  "partial": true,
  "data": {
    "destination": { "path": "D:/Ho-so/HS-42", "scope": "machine_local", "is_dir": true },
    "documents": [
      {
        "document_key": "khai_nhan_di_san",
        "display_name": "Văn bản khai nhận di sản",
        "status": "saved",
        "actual_filename": "Van_ban_khai_nhan_HS-42_2.docx",
        "output_file": { "path": "D:/Ho-so/HS-42/Van_ban_khai_nhan_HS-42_2.docx", "scope": "machine_local" },
        "error": null
      },
      {
        "document_key": "niem_yet",
        "display_name": "Thông báo niêm yết",
        "status": "failed",
        "actual_filename": null,
        "output_file": null,
        "error": { "code": "word.unresolved_placeholders", "message": "Mẫu còn trường chưa hỗ trợ" }
      }
    ],
    "breakdown": {
      "succeeded": ["khai_nhan_di_san"],
      "failed": ["niem_yet"]
    }
  }
}
```

Quy tắc job:

- tất cả file thành công → `succeeded`;
- có cả thành công và lỗi → `partial` + `breakdown`;
- tất cả lỗi → `failed`, `error.code=word.batch_failed`, và `error.details.documents` chứa lỗi từng văn bản;
- hủy giữa lượt chỉ dừng các file chưa bắt đầu; file đã lưu không bị xóa.

## 3. File Structure đích

```text
contracts/
  notary-case-drafting.md
  notary-case-drafting/
    *.schema.json
    examples/{valid,invalid}/
    validate_examples.py

notary_v2/
  services/
    case_workspace.py
    inheritance_workspace.py
    word_batch_export.py
    document_intake/
      __init__.py
      models.py
      service.py
      normalization.py
      adapters/{image_ocr,pdf,docx,excel,text}.py
  tests/
    test_case_workspace.py
    test_document_intake.py
    test_inheritance_workspace.py
    test_word_batch_export.py

shell/
  sidecar/
    notary_gateway.py
    notary_mock_adapter.py
    notary_adapter.py
    command_registry.py
  src/renderer/notary/
    case-drafting-model.js
    case-drafting-view.js
    intake-dialog.js
    relationship-diagram.js
    word-export-dialog.js
    case-drafting.css
  test/
    fixtures/notary-case-drafting/*.json
    notary-case-drafting-model.test.mjs
    notary-case-drafting-static.test.mjs
    test_notary_mock_adapter.py
    test_notary_adapter_contract.py
```

Không đưa logic mới vào `frontend/templates/cases/form.html`. Nếu phải sửa web cũ để giữ tương thích, chỉ gọi service mới thay vì chép lại nghiệp vụ.

## 4. Dependency Map và chia issue

```text
P1 Product Flow + UI spec
        │
        ▼
P2 API Contract publish (không runtime)
        │
        ├───────────────┐
        ▼               ▼
P3 Mock Backend     P4–P7 Real Backend
        │               │
        ▼               │
P8 Frontend nền         │
        └───────┬───────┘
                ▼
P9 Frontend nối đủ luồng
                ▼
P10 Parity, package, cutover
```

Issue con đã tạo dưới MIN-68 ngày 24/09/2026:

1. [MIN-104](https://linear.app/minhnotary/issue/MIN-104) — `SPEC — Product Flow và Electron UX tab Soạn hồ sơ`
2. [MIN-105](https://linear.app/minhnotary/issue/MIN-105) — `CONTRACT — notary.case-drafting.v1`
3. [MIN-106](https://linear.app/minhnotary/issue/MIN-106) — `MOCK — Backend giả cho tab Soạn hồ sơ`
4. [MIN-107](https://linear.app/minhnotary/issue/MIN-107) — `BACKEND — Workspace và Stage transaction`
5. [MIN-108](https://linear.app/minhnotary/issue/MIN-108) — `BACKEND — Document Intake đa nguồn`
6. [MIN-109](https://linear.app/minhnotary/issue/MIN-109) — `BACKEND — Diagram thừa kế evaluate/save`
7. [MIN-110](https://linear.app/minhnotary/issue/MIN-110) — `BACKEND — Xuất Word nhiều văn bản`
8. [MIN-111](https://linear.app/minhnotary/issue/MIN-111) — `FRONTEND — Khung UI tab Soạn hồ sơ`
9. [MIN-112](https://linear.app/minhnotary/issue/MIN-112) — `FRONTEND — Nối Intake, Stage, Diagram và Word export`
10. [MIN-113](https://linear.app/minhnotary/issue/MIN-113) — `VERIFY — Parity, packaged smoke và cutover`

P3 và P4–P7 có thể làm song song sau P2. P8 dùng mock để dựng UI; P9 chỉ hoàn tất khi cùng bộ contract test chạy được với mock và real.

## 5. Task 1 — Publish Product Flow và UI spec

**Files:**

- Create: `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md`
- Create: `notary_v2/docs/platform/case-workspace/drafting-tab.md`
- Modify: `docs/product/specs/2026-09-14-module-transition-ux-spec.md`
- Modify: `notary_v2/docs/platform/case-workspace/README.md`
- Modify: `notary_v2/docs/domains/inheritance/workflow.md`
- Modify: `notary_v2/docs/domains/inheritance/word-export.md`
- Modify: `notary_v2/docs/platform/document-intake/spec.md`

- [ ] Chuyển §1 của plan thành spec bền vững; ghi rõ hiện trạng và đích Electron.
- [ ] Khóa ba module chính và ba tab con của `notary_v2`; phân biệt module nghiệp vụ với tiện ích shell.
- [ ] Cập nhật Word spec từ “một template + browser download” sang popup nhiều văn bản + native folder + per-file result.
- [ ] Ghi rõ intake thủ công hỗ trợ ảnh/PDF/DOCX/XLSX/text và không có Zalo control.
- [ ] Ghi rõ backend thật đầu tiên chỉ là inheritance; case type khác hiện `Chưa hỗ trợ`.
- [ ] Gắn bảng nút/popup/action và tất cả trạng thái UI §1.3–1.4.
- [ ] Owner review spec; sửa mọi khác biệt trước khi mở contract task.

**Check:**

```powershell
rg -n "Zalo|Stage|Pool|Diagram|word_export_batch|_2|partial|Chưa hỗ trợ" `
  docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md `
  notary_v2/docs/platform/case-workspace/drafting-tab.md `
  notary_v2/docs/domains/inheritance/word-export.md
```

Expected: Zalo chỉ xuất hiện trong câu loại trừ; mọi quyết định Stage/Pool/Diagram/Word đều có một nguồn chuẩn, không mâu thuẫn với nhau.

**Commit:** `docs(notary): specify complete case drafting tab flow`

## 6. Task 2 — Publish API contract, chưa sửa runtime

**Files:**

- Create: `contracts/notary-case-drafting.md`
- Create: `contracts/notary-case-drafting/*.schema.json`
- Create: `contracts/notary-case-drafting/examples/valid/*.json`
- Create: `contracts/notary-case-drafting/examples/invalid/*.json`
- Create: `contracts/notary-case-drafting/validate_examples.py`
- Modify: `contracts/README.md`

- [ ] Viết schema cho bảy command ở §2, dùng envelope `desktopcommand.v1` hiện có.
- [ ] Chốt `revision/base_revision`, null, ngày ISO, ID UI tạm và ID DB thật.
- [ ] Chốt Stage commit atomic: một dòng sai thì không đổi Stage; response trả lỗi theo `row_id` và field.
- [ ] Chốt intake suggestion luôn là `observed|normalized|inferred`, không có `confirmed` trước thao tác người dùng.
- [ ] Chốt Diagram chỉ tham chiếu `row_id/entity_id` có trong Stage đã commit.
- [ ] Chốt directory FileRef có `is_dir=true`, absolute local path, không UNC.
- [ ] Chốt batch Word naming, reservation trong cùng batch, partial/all-failed/cancel semantics.
- [ ] Valid fixtures: hồ sơ rỗng; Stage nhiều người/tài sản; OCR một phần; sơ đồ hợp lệ; collision `_2/_3`; batch Word partial.
- [ ] Invalid fixtures: revision cũ; Diagram tham chiếu người ngoài Stage; file type không hỗ trợ; directory là UNC/file; checkbox rỗng; document key trùng; output traversal `../`; response giả `confirmed` từ OCR.
- [ ] Contract review và owner duyệt; chỉ sau đó mới giải phóng Task 3–7.

**Test first:** validator chưa có phải fail khi chạy:

```powershell
python contracts/notary-case-drafting/validate_examples.py
```

Expected trước implementation: file/script chưa tồn tại hoặc invalid fixtures chưa bị reject.

**Test after:** cùng lệnh exit `0`, in số valid pass và invalid bị từ chối đúng `expected_error`.

**Commit:** `contract(notary): publish case drafting desktop commands`

## 7. Task 3 — Mock Backend đúng contract

**Files:**

- Create: `shell/sidecar/notary_gateway.py`
- Create: `shell/sidecar/notary_mock_adapter.py`
- Create: `shell/test/fixtures/notary-case-drafting/*.json`
- Create: `shell/test/test_notary_mock_adapter.py`
- Modify: `shell/sidecar/command_registry.py`
- Modify: `shell/src/main/config.js`
- Modify: `shell/src/main/main.js`
- Modify: `shell/test/test_sidecar_contract.py`

- [ ] Viết test cho đủ bảy command và các scenario: empty, ready, locked, conflict, intake partial, diagram warning, Word collision/partial.
- [ ] Chạy test và xác nhận fail vì command chưa đăng ký.
- [ ] Tạo gateway chọn mock khi `G1_DEV_NOTARY_MOCK=1` **và** Electron không packaged; mặc định luôn real.
- [ ] Mock trả fixture bất biến, có revision giả, progress thật và idempotency theo command ID hiện có.
- [ ] Mock export tạo DOCX hợp lệ trong temp folder test, dùng đúng naming rule; không viết ra folder người dùng khi chạy unit test.
- [ ] `workspace_get` trả `backend_mode=mock`; renderer sau này phải hiện banner `Dữ liệu mô phỏng`.
- [ ] Packaged mode gặp env mock phải bỏ qua và ghi warning đã redact, không khởi động mock.

**Test:**

```powershell
python -m pytest shell/test/test_notary_mock_adapter.py -q
python shell/test/test_sidecar_contract.py
```

Expected: pass; gọi lại cùng `command_id` không nhân đôi file; fixtures không chứa PII thật.

**Commit:** `feat(shell): add contract-faithful notary drafting mock`

## 8. Task 4 — Real Backend: Workspace và Stage transaction

**Files:**

- Create: `notary_v2/services/case_workspace.py`
- Create: `notary_v2/tests/test_case_workspace.py`
- Modify: `notary_v2/models.py`
- Modify: `notary_v2/database.py`
- Modify: `shell/sidecar/notary_adapter.py`
- Modify: `shell/sidecar/command_registry.py`
- Create: `shell/test/test_notary_adapter_contract.py`

- [ ] Viết migration idempotent thêm `workspace_revision INTEGER NOT NULL DEFAULT 1` và `updated_at` cho case; không phá DB cũ.
- [ ] Viết failing tests: load case cũ không có `case_state_json`; Stage nhiều tài sản; commit hợp lệ; một dòng lỗi rollback toàn bộ; case locked; stale revision; xóa người làm prune Diagram.
- [ ] Tạo `CaseWorkspaceService.get(case_id)` để compose dữ liệu từ Customer, Participant, Property links và state JSON; không để sidecar đọc ORM rải rác.
- [ ] Tạo `commit_stage(case_id, base_revision, people, assets)` trong một transaction: validate → upsert/link → prune Diagram → tăng revision → commit.
- [ ] Giữ duplicate do người dùng quản lý; chỉ upsert theo `entity_id` hoặc khóa giấy tờ đã tồn tại, không tự merge hai row chỉ vì tên giống.
- [ ] Sidecar handlers `workspace_get` và `workspace_commit_stage` chỉ chuyển contract ↔ service; không chứa business rule.
- [ ] Web cũ vẫn đọc được dữ liệu sau migration; không đổi route web trong task này nếu không cần.

**Tests:**

```powershell
python -m pytest notary_v2/tests/test_case_workspace.py -q
python -m pytest shell/test/test_notary_adapter_contract.py -q -k workspace
```

Expected: mọi test pass; test stale revision trả `notary.workspace_conflict`; DB không đổi sau atomic rollback.

**Commit:** `feat(notary): add revisioned case workspace service`

## 9. Task 5 — Real Backend: Document Intake đa nguồn

**Files:**

- Create: `notary_v2/services/document_intake/__init__.py`
- Create: `notary_v2/services/document_intake/models.py`
- Create: `notary_v2/services/document_intake/service.py`
- Create: `notary_v2/services/document_intake/normalization.py`
- Create: `notary_v2/services/document_intake/adapters/image_ocr.py`
- Create: `notary_v2/services/document_intake/adapters/pdf.py`
- Create: `notary_v2/services/document_intake/adapters/docx.py`
- Create: `notary_v2/services/document_intake/adapters/excel.py`
- Create: `notary_v2/services/document_intake/adapters/text.py`
- Create: `notary_v2/tests/test_document_intake.py`
- Modify: `notary_v2/routers/ocr_ai.py`
- Modify: `notary_v2/routers/customers.py`
- Modify: `shell/sidecar/notary_adapter.py`

- [ ] Viết fixtures giả cho CCCD hai mặt, giấy khai tử, GCN nhiều thửa, file lạ, PDF scan, DOCX text, Excel người và text dán.
- [ ] Viết failing tests chứng minh: source nào lỗi chỉ đánh dấu source đó; gợi ý không tự confirmed; raw và normalized tách riêng; source refs còn truy vết được.
- [ ] Tách parser/normalizer hiện có khỏi router để web route và sidecar cùng gọi một service; không copy parser.
- [ ] Adapter ảnh gọi Qwen hiện có; adapter PDF dùng PyMuPDF, OCR trang không có text; DOCX dùng python-docx; XLSX dùng openpyxl; text dùng parser chung.
- [ ] Giới hạn mỗi lượt theo contract (số file, trang, byte, text length) và check cancel giữa từng source/trang.
- [ ] Trả `partial` khi có source thành công và source lỗi; lỗi ghi filename hiển thị, mã lỗi và cách xử lý.
- [ ] Không ghi raw text/PII vào log; telemetry chỉ có source ID, loại, thời gian, trạng thái.

**Tests:**

```powershell
python -m pytest notary_v2/tests/test_document_intake.py notary_v2/tests/test_ocr_ai.py notary_v2/tests/test_customers_excel.py -q
python -m pytest shell/test/test_notary_adapter_contract.py -q -k intake
```

Expected: adapters trả cùng shape; Qwen thiếu key báo `ocr.engine_unavailable`; file khác vẫn được xử lý theo partial rule.

**Commit:** `feat(notary): normalize multi-source document intake`

## 10. Task 6 — Real Backend: Diagram thừa kế evaluate/save

**Files:**

- Create: `notary_v2/services/inheritance_workspace.py`
- Create: `notary_v2/tests/test_inheritance_workspace.py`
- Modify: `notary_v2/services/inheritance_engine.py`
- Modify: `shell/sidecar/notary_adapter.py`
- Modify: `shell/sidecar/command_registry.py`

- [ ] Viết failing tests cho Pool invariant, reference ngoài Stage, owner/receiver, nhánh thế vị, xóa assignment trả về Pool, lưu revision cũ và case locked.
- [ ] `diagram_evaluate` nhận draft state + Stage snapshot đã commit, validate reference rồi gọi engine; không persist.
- [ ] Engine trả `render_model` gồm node, cạnh, slot hợp lệ, warning và các dòng giải thích tỷ lệ; renderer không tự tính pháp lý.
- [ ] `diagram_save` validate lại bằng dữ liệu DB mới nhất, lưu state + output engine trong transaction và tăng revision.
- [ ] Giữ đúng hai quyết định trên card: `Chủ đất`, `Nhận`; không thêm `Từ chối` hoặc suy từ “không nhận”.
- [ ] `case_type` khác `inheritance` trả capability false hoặc `notary.case_type_unsupported`.

**Tests:**

```powershell
python -m pytest notary_v2/tests/test_inheritance_workspace.py notary_v2/tests/test_inheritance_engine.py notary_v2/tests/test_diagram_payload_parser.py -q
python -m pytest shell/test/test_notary_adapter_contract.py -q -k diagram
```

Expected: không test nào tính tỷ lệ trong JavaScript; output giải thích khớp engine fixture.

**Commit:** `feat(notary): expose inheritance diagram evaluate and save`

## 11. Task 7 — Real Backend: Xuất Word nhiều văn bản

**Files:**

- Create: `notary_v2/services/word_batch_export.py`
- Create: `notary_v2/tests/test_word_batch_export.py`
- Modify: `notary_v2/services/word_engine.py`
- Modify: `shell/sidecar/fileref.py`
- Modify: `shell/sidecar/notary_adapter.py`
- Modify: `shell/sidecar/command_registry.py`
- Modify: `shell/test/test_notary_adapter_contract.py`

- [ ] Viết failing tests: 0 lựa chọn; directory sai; hai document cùng tên; file đã tồn tại; một template lỗi; placeholder còn sót; hủy giữa batch; path traversal; tên Windows không hợp lệ.
- [ ] `word_export_options` ánh xạ mỗi văn bản đến đúng template và trả `ready/blocked_reasons`; không coi “template active” là toàn bộ danh sách xuất.
- [ ] Chuẩn hóa tên file Windows; fallback `{ten_mau}_HS-{case_id}.docx`; không cho `..`, separator, tên thiết bị Windows.
- [ ] Chọn tên bằng reservation riêng cho cả file đã có và file trùng trong cùng batch: tên gốc, rồi `_2`, `_3`, ...
- [ ] Render mỗi DOCX vào file tạm trong destination, sau đó ghi file đích bằng create-exclusive; nếu copy lỗi thì xóa file dở của đúng item, không xóa item khác.
- [ ] Bọc từng document trong `try/except`; tiếp tục item kế tiếp; trả per-item status và partial breakdown đúng §2.
- [ ] Không tạo ZIP, không ghi vào `G1_OUTPUT_DIR/exports`, không overwrite.

**Tests:**

```powershell
python -m pytest notary_v2/tests/test_word_batch_export.py notary_v2/tests/test_word_engine.py -q
python -m pytest shell/test/test_notary_adapter_contract.py -q -k word
```

Expected: folder fixture có các file `.docx` hợp lệ; file có sẵn giữ nguyên byte; lỗi nêu đúng `document_key`; thành công không bị rollback.

**Commit:** `feat(notary): export independent Word documents as a batch`

## 12. Task 8 — Frontend foundation và bố cục

**Files:**

- Create: `shell/src/renderer/notary/case-drafting-model.js`
- Create: `shell/src/renderer/notary/case-drafting-view.js`
- Create: `shell/src/renderer/notary/case-drafting.css`
- Create: `shell/test/notary-case-drafting-model.test.mjs`
- Create: `shell/test/notary-case-drafting-static.test.mjs`
- Modify: `shell/src/renderer/index.html`
- Modify: `shell/src/renderer/renderer.js`
- Modify: `shell/src/renderer/styles.css`
- Modify: `shell/src/renderer/lib.js`
- Modify: `shell/src/main/registry.js`
- Modify: `shell/test/navigation.test.mjs`

- [ ] Viết pure-state tests trước: load, dirty Stage, commit success/fail, derived Pool, draft Diagram, revision conflict, locked read-only, mock banner.
- [ ] Chạy test và xác nhận fail vì module chưa có.
- [ ] Tách view notary khỏi `renderer.js`; giữ file UMD/CommonJS-compatible để chạy `node --test`, không thêm bundler.
- [ ] Dựng local navigation của notary_v2 gồm `Tổng quan hồ sơ`, `Soạn hồ sơ`, `Word`; task này chỉ hoàn thiện nội dung `Soạn hồ sơ`.
- [ ] Navigation chính chỉ trình bày `notary_v2`, `upload_lab`, `notaryoffice` là module nghiệp vụ. Giữ `document-review` làm ID kỹ thuật tương thích trong một chu kỳ nếu cần; bỏ `Excel → Word` khỏi nav chính nhưng chưa xóa registry/command cũ trong task này.
- [ ] Dựng đúng bố cục §1.2 và token hình ảnh; không chép Bootstrap/ReactFlow từ web cũ.
- [ ] Render đủ loading/empty/error/locked/conflict/unavailable; không render JSON kỹ thuật cho người dùng.
- [ ] Nút 44 px, focus visible, label/aria; mọi thao tác kéo thả có menu/nút thay thế bằng bàn phím.
- [ ] Xóa màn kỹ thuật “nhập ID bằng tay” khỏi view production; có thể giữ debug view sau dev flag.

**Tests:**

```powershell
npm --prefix shell test
```

Expected: pure model và static source tests pass; nav Soạn hồ sơ không chứa `Zalo`, `zalo.status` hoặc input ID kỹ thuật.

**Commit:** `feat(shell): build notary case drafting workspace layout`

## 13. Task 9 — Frontend workflows: Intake, Stage, Diagram, Word

**Files:**

- Create: `shell/src/renderer/notary/intake-dialog.js`
- Create: `shell/src/renderer/notary/relationship-diagram.js`
- Create: `shell/src/renderer/notary/word-export-dialog.js`
- Modify: `shell/src/renderer/notary/case-drafting-model.js`
- Modify: `shell/src/renderer/notary/case-drafting-view.js`
- Modify: `shell/src/renderer/notary/case-drafting.css`
- Modify: `shell/src/preload/preload.js`
- Modify: `shell/src/main/ipc.js`
- Modify: `shell/src/main/main.js`
- Modify: `shell/test/ipc.test.mjs`
- Modify: `shell/test/notary-case-drafting-model.test.mjs`
- Modify: `shell/test/notary-case-drafting-static.test.mjs`

- [ ] Intake: native picker theo loại file, drop zone, paste text, danh sách source, progress/cancel, review cards và lỗi từng source.
- [ ] Preview: main chỉ đọc file đã được native picker cấp opaque token; giới hạn type/byte/page; renderer không được gửi path tùy ý. Token mất khi app đóng và không vào log/storage.
- [ ] `Đưa vào Stage` chỉ thêm draft; đóng popup giữ kết quả trong phiên; chạy intake lần nữa thêm kết quả mới lên trên, không xóa ngầm.
- [ ] Stage: inline trường chính + drawer chi tiết; remove chỉ đổi draft; `Cập nhật` gửi toàn snapshot với revision; lỗi gắn đúng row/field.
- [ ] Pool: derive từ committed Stage trừ Diagram assignment; tìm kiếm/filter chỉ đổi hiển thị.
- [ ] Diagram: HTML/SVG render từ backend `render_model`; drag/drop chỉ tạo draft assignment; menu `Gán vị trí` cho keyboard; debounce evaluate; `Lưu sơ đồ` mới persist.
- [ ] `Xem cách tính` hiển thị câu engine trả về, không tự dựng công thức.
- [ ] Word popup: load options, checkbox nhiều văn bản, chọn một folder qua `pickFiles({directory:true})`, bấm một lần, theo dõi job.
- [ ] Kết quả Word từng dòng: `Đã lưu` + actual path + nút mở file, hoặc `Lỗi` + lý do; không đóng popup tự động khi có lỗi.
- [ ] Nếu rời tab với Stage/Diagram chưa lưu, hiện confirm; close popup thông thường không lưu/xóa.
- [ ] Chạy toàn bộ cùng mock trước; sau đó đổi sang real mà không sửa component hoặc nhánh `if mock` trong business UI.

**Tests:**

```powershell
npm --prefix shell test
python -m pytest shell/test/test_notary_mock_adapter.py shell/test/test_notary_adapter_contract.py -q
```

Expected: cùng bộ UI state tests pass với fixture mock và contract fixture real; directory picker chỉ trả `is_dir=true`; không có path tùy ý từ renderer.

**Manual review ở 1440×1024 và 1280×820:**

- Stage Tài sản/Người đúng ưu tiên 36/64.
- Pool/Diagram nằm ngay dưới Stage, đúng ưu tiên 22/78.
- Nút tập trung, không có phụ đề dài, không có Zalo.
- OCR/import không tự commit.
- Xóa trên Diagram không xóa Stage.
- Export 3 văn bản, ép 1 lỗi: 2 file vẫn tồn tại, đúng tên và đúng trạng thái.

**Commit:** `feat(shell): connect complete case drafting interactions`

## 14. Task 10 — Parity, package và cutover

**Files:**

- Create: `.agent/tasks/<VERIFY-ISSUE>/brief.md`
- Create: `.agent/tasks/<VERIFY-ISSUE>/progress.md`
- Create: `.agent/tasks/<VERIFY-ISSUE>/decisions.md`
- Create: `.agent/tasks/<VERIFY-ISSUE>/handoff.md`
- Modify: `shell/README.md`
- Modify: `docs/architecture/ELECTRON_G1_PLAN.md`
- Modify: `notary_v2/docs/platform/case-workspace/drafting-tab.md`

- [ ] Dùng fixture giả hoàn chỉnh: 1 hồ sơ, ít nhất 6 người, 2 tài sản, quan hệ thừa kế, 3 văn bản Word.
- [ ] Chạy flow từ mở hồ sơ → OCR/import → Stage → Pool/Diagram → reload → export.
- [ ] Fault injection: Qwen thiếu key; sidecar restart; revision conflict; case locked; template hỏng; destination read-only; hủy batch.
- [ ] Đối chiếu web cũ: mọi hành vi nguồn chuẩn còn tồn tại; ghi rõ khác biệt có chủ ý.
- [ ] Kiểm privacy: log không có họ tên, CCCD, raw OCR, path username chưa redact.
- [ ] Build sidecar + Electron packaged; smoke mở/đóng và export Word từ bản packaged.
- [ ] Owner review UI thật. Chỉ sau khi owner duyệt mới đổi entry mặc định sang tab mới; web cũ vẫn giữ một chu kỳ release để rollback.
- [ ] Cập nhật Linear, progress/handoff và bằng chứng; không dùng checkbox file plan làm trạng thái.

**Full verification:**

```powershell
python contracts/notary-case-drafting/validate_examples.py
python -m pytest notary_v2/tests/test_case_workspace.py `
  notary_v2/tests/test_document_intake.py `
  notary_v2/tests/test_inheritance_workspace.py `
  notary_v2/tests/test_word_batch_export.py `
  notary_v2/tests/test_inheritance_engine.py `
  notary_v2/tests/test_word_engine.py -q
npm --prefix shell test
python shell/test/test_sidecar_contract.py
python -m pytest shell/test/test_notary_mock_adapter.py `
  shell/test/test_notary_adapter_contract.py -q
Set-Location notary_v2
$env:FULL_VERIFY="1"
.\verify.bat
Set-Location ..\shell
npm run build:sidecar
npm run dist
$env:G1_SMOKE="1"
$env:G1_SMOKE_LOG="$PWD/smoke-notary-drafting.json"
.\dist-app\win-unpacked\g1-shell.exe
```

Expected:

- mọi lệnh exit `0`;
- smoke JSON báo sidecar healthy và contract tương thích;
- không có test Zalo mới trong phạm vi tab này;
- không có file Word bị overwrite;
- fixture export trả đúng per-item result;
- `git diff --check` sạch.

**Commit:** `test(notary): verify drafting parity and packaged workflow`

## 15. Definition of Done

Tab `Soạn hồ sơ` chỉ được coi là hoàn tất khi:

- [ ] Người dùng mở được hồ sơ có sẵn, không nhập ID kỹ thuật.
- [ ] Ảnh/PDF/DOCX/XLSX/text và nhập tay đều đi qua cùng mô hình suggestion → review → Stage.
- [ ] Không nguồn tự trở thành dữ liệu confirmed.
- [ ] Stage Người/Tài sản commit an toàn, báo lỗi đúng dòng và chống stale revision.
- [ ] Pool luôn được derive đúng; thao tác Diagram không làm mất Stage.
- [ ] Sơ đồ thừa kế lưu/reload đúng và mọi phép tính đến từ Python engine.
- [ ] Loại việc chưa có backend hiện `Chưa hỗ trợ` rõ ràng.
- [ ] Popup Word chọn nhiều văn bản, lưu thẳng vào folder, tự tăng hậu tố, lỗi từng file.
- [ ] Mock và real cùng pass contract fixtures; production không thể âm thầm chạy mock.
- [ ] UI không có Zalo, không có JSON kỹ thuật, không có chú thích thừa.
- [ ] Test, full verify, packaged smoke và manual fixture đều có bằng chứng trong task folder.

## 16. Ước lượng và đường găng

Với một người làm tuần tự: khoảng **18–25 ngày làm việc tập trung**. Phần có thể song song sau khi contract duyệt là Mock, Workspace, Intake, Diagram và Word. Đường găng là:

```text
Spec duyệt → Contract duyệt → Workspace/Diagram thật → Frontend integration → Packaged verification
```

Không rút ngắn bằng cách cho frontend gọi thẳng route web cũ hoặc DB; cách đó tạo thêm một luồng tạm phải bỏ sau.

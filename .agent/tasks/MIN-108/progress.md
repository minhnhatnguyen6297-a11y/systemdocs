# Progress — MIN-108

## Trạng thái: implement xong — đã verify tests + contract validator (25/09/2026)

Worktree `D:\systemdocs-min-108` từ `consolidate/monorepo @6da4eb0`.

## Đã làm

### notary_v2 — `services/document_intake/` (mới, dùng chung)

- `ocr_pipeline.py` — toàn bộ Qwen OCR + parser (CCCD/GCN/giấy báo tử,
  pairing front/back, `process_image_bytes`, `_normalize_native_ocr_doc`,
  `_pair_persons`, `_normalize_person_data`, `parse_cccd_qr`...) tách từ
  `routers/ocr_ai.py` — không duplicate parser.
- `routers/ocr_ai.py` — còn thin wrapper: endpoints `/api/ocr/analyze`,
  `/api/ocr/config` + re-export symbol cho tests/`zalo_inbox`/sidecar.
  Response shape giữ nguyên (44 tests OCR pass).
- `excel_parse.py` — helper Excel dùng chung (`normalize_excel_header`,
  `consonant_skeleton`, `header_matches_keyword`, `parse_date`,
  `format_date_display`, `normalize_gender`, `as_input_value`,
  `parse_people_workbook`); `routers/customers.py` re-import + upload_excel
  vẫn ghi DB như cũ (15 tests pass).
- `models.py` — `IntakeError` (job-level), `SourceFailed` (per-source),
  `IntakeCancelled`, `SourceSpec`, `AdapterContext`, `IntakeOutcome`,
  constants §5.2 (8 sources / 20MB / 50 trang / 100k chars).
- `normalization.py` — field_value contract shape: raw + normalized +
  observation_state (observed|normalized|inferred) + confidence +
  source_refs; `intake.low_confidence` warning cho inferred < 0.7;
  KHÔNG emit `confirmed`, KHÔNG emit `""` thay null.
- `adapters/` — `image_ocr` (Qwen qua pipeline), `pdf` (PyMuPDF text
  layer + OCR trang scan + pairing person nhiều trang), `docx`
  (python-docx paragraph+table), `excel` (shared parser → person
  suggestions với sheet/cell/row refs), `text` (QR pipe-format + native
  doc parser, span refs).
- `service.py` — validate payload strict (uuid4 source_id, key presence
  không truthiness, unknown keys, `is_dir` phải absent/false đúng
  schema, size_bytes bắt buộc int ≥0); limit khai báo → job-level
  IntakeError; limit chỉ phát hiện lúc mở file (file thật >20MB,
  PDF >50 trang) → per-source SourceFailed; mọi lỗi per-source vào
  `errors[]` {source_id,code,message} + `breakdown`; status
  succeeded|partial (contract không có failed cho intake); telemetry
  chỉ source_id/kind/status/ms/code — không filename/PII.

### shell sidecar

- `notary_adapter.intake_analyze` — validate payload keys/case_id,
  check case tồn tại + không locked (`case_not_found`/
  `workspace_locked`), gọi `svc.analyze` với `job.check_cancel` +
  `job.report_progress`, map `IntakeError` → `CommandError`, trả
  `_result("intake_analyze", data, source_files=...)` + `partial` flag.
- `command_registry.py` — thêm `notary.intake_analyze` (append-only).
- Fix bug cũ: `ocr_analyze` gọi `ocr._get_api_key(model)` trong khi
  hàm không nhận tham số → đổi `ocr._get_api_key()`.

### Tests

- `notary_v2/tests/test_document_intake.py` — 40 tests: 5 adapters,
  limits, uuid4/dup id, unknown keys, file_ref invalid, isolation,
  OCR key thiếu chỉ ảnh hưởng image, provenance (page/cell/span),
  cancel, no-`confirmed` invariant.
- `shell/test/test_notary_intake_adapter.py` — 6 tests qua registry
  thật: contract shape, partial breakdown, xlsx cells, validation
  codes, `notary.intake_analyze` registered, result chạy qua
  contract validator `violations()`.

## Kết quả verify

- `pytest tests/test_document_intake.py` — 40 passed.
- `pytest tests/test_ocr_ai.py tests/test_customers_excel.py` — 59 passed.
- `python shell/test/test_notary_intake_adapter.py` — 6 passed.
- `contracts/notary-case-drafting/validate_examples.py` — 34 files, 0
  unexpected (cả output thật của service qua `violations()` cũng 0).
- `verify.ps1` — py_compile pass (ruff không cài trong venv).

## Quyết định đáng nhớ

- Limit §5.2 chia 2 mức: vi phạm khai báo (size_bytes, text length,
  số sources, kind, dup id) → job-level `IntakeError`; vi phạm chỉ
  biết khi mở file (size thật, số trang PDF) → per-source `SourceFailed`
  — giữ failure isolation, khớp `intake_source_too_large` §9.
- `intake_error` shape đúng schema: chỉ {source_id, code, message};
  filename đi trong message khi cần.
- Engine OCR thiếu key → per-source `ocr.engine_unavailable` (data-code
  `<ns>.<snake>` giống `ocr.analyze`), các nguồn khác vẫn chạy.

## Giới hạn còn lại

- Image/PDF-scan path cần QWEN_API_KEY khi chạy thật (test inject
  `ocr_call`).
- Doc type pipeline `marriage`/unknown → `intake.parse_failed`
  (`intake.unsupported_target` chưa có doc type tương ứng trong
  pipeline hiện trạng).
- Sidecar test ghi case fixture vào notary.db dev (giống
  test_engine_adapters hiện có).

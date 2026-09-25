# MIN-99 — progress slice A (raw-package consumer core)

Trạng thái: **xong — 46 test xanh** (`pytest tests/test_zalo_exchange_client.py tests/test_zalo_exchange_sync.py` → 46 passed; 13 client + 33 sync). Tương thích slice B đã kiểm: `pytest tests/test_zalo_sync_api.py tests/test_zalo_parse_runner.py` → 27 passed với API slice A hiện tại.

## File đã viết (đúng ownership)

- `services/zalo_exchange/__init__.py` — docstring only.
- `services/zalo_exchange/client.py` — `IntakeClient(base_url, token, timeout, transport?)`, sync `httpx.Client`; `service_status`, `list_packages(after_sequence, until_sequence=, limit≤100)`, `fetch_bytes` (whitelist manifest/records/ready + fallback file-spelling, `ValueError` cho mọi tên khác — image bytes không bao giờ đi ra wire), `send_receipt`, `create_ocr_request`, `get_ocr_request`. `IntakeClientError(code, message, status, retryable)` map `intake.error.v1`.
- `services/zalo_exchange/validate.py` — validate toàn bộ package dir: whitelist file (flat, image/exec/protocol names → `file_forbidden`), byte limits (64KiB manifest/READY, 16MiB records, 1000 records), strict JSON/JSONL (UTF-8 no BOM, unique keys, finite numbers, `\n` framing), schema subset engine (port nguyên `_validator/schema_subset.py` — `jsonschema` KHÔNG có trong requirements nên không thêm dependency), per-record schema + `_record_rules` context-free port (kind-body, `expires_mismatch`, supersedes rev-1, `_ocr_rules`, `_source_event_rules`, `_listener_rules`, payload scans image/provider).
- `services/zalo_exchange/store.py` — helpers trên models có sẵn: exchange dirs + write exact bytes nằm ở sync.py; ở đây có `ledger_get`/`last_imported_sequence`/`ledger_counts`, `check_record_conflicts` (dedupe same-bytes no-op, `record_conflict`, `source_revision_conflict`, `revision_chain_broken` kèm điều kiện `sup.revision == rev-1`, `immutable_field_changed` so captured_at qua payload_json verbatim — cột SQLite naive không đủ tin cậy), `insert_raw_records` (payload_json = verbatim JSONL line), `add_ledger_row`, `mark_receipt`, `enqueue_parse_job`, `store/load_receipt_doc` trong `zalo_sync_state`, `get/set_state`, `next_result_revision`/`add_intake_result`/`results_for_package`/`records_for_package`/`pending_parse_jobs` (cho slice B).
- `services/zalo_exchange/sync.py` — `SyncSettings(+from_env)`, `SyncReport(listed, imported, skipped, quarantined, receipts_sent, errors)`, `run_sync`. Luồng: feed `after=0` + `until_sequence` pinned từ page đầu, persist `pending_list` vào sync_state mỗi page; per package ascending: ledgered → chỉ replay stored receipt khi chưa confirm; `sequence <= last_imported` → skip không tải; download 3 file vào `staging/`; validate → quarantine hoặc `ready/` → ONE commit (ledger+raw+job+receipt doc) → `imported/` → POST receipt. Receipt 4xx = definitive → mark + không retry; 5xx/transport → retry run sau.
- `tests/test_zalo_exchange_client.py` — 13 test MockTransport.
- `tests/test_zalo_exchange_sync.py` — 33 test: happy path, quarantine đủ loại (hash/schema/consumer/feed-hash/file_forbidden/READY thiếu/revision/record_conflict/expires_mismatch/ocr_status_inconsistent/immutable_field/source_event/listener_gap), lost-ACK replay cùng receipt_id, restart-resume, out-of-order skip, dedupe same-bytes, verbatim payload + alignment khi dedupe, whitelist fetch, business tables untouched, paging, env settings, unauthorized feed, fetch-fail.

## Divergence / quyết định nhỏ

- `jsonschema` không có trong venv/requirements → port schema-subset engine của contract validator (giống cách producer `delivery/_schema.py` làm). Không thêm dependency.
- `list_packages` nhận `until_sequence` + params wire `delivery/after/until_sequence/limit` theo contract §7.2 và producer impl thật (không phải `consumer_id/after_sequence` như sheet phác thảo — consumer identity nằm ở Bearer token).
- `SyncReport` thêm counter `listed` (hữu ích cho `/sync/state` slice B).
- `page_limit` default 200 như sheet nhưng clamp 100 trên wire (cap contract).
- Quarantined packages KHÔNG nâng `last_sequence` (rejected không bao giờ import được — nâng cursor sẽ nuốt mọi gói sequence sau).
- Receipt bị producer từ chối 4xx (mismatch/conflict) được mark `receipt_status` theo status đã gửi + log `report.errors` — permanent refusal, không retry vô hạn; ledger vẫn giữ decision đúng.
- `SyncSettings.from_env` đọc 4 biến (ZALO_MODULE_URL/TOKEN/CONSUMER_ID/EXCHANGE_ROOT); `ZALO_SYNC_INTERVAL_SECONDS` là knob của run-loop slice B, không phải field của settings.
- `send_receipt`/`create_ocr_request`/`get_ocr_request` nằm ở client (sheet để ở client — đúng), OCR proxy endpoint là việc của slice B router.

## Unverified / lưu ý

- `verify.bat`/`verify.ps1` chưa chạy (repo-con quirk + scope slice A); đã chạy tay 46 + 27 test liên quan — all green.
- Chưa integration test với producer thật tại `D:\zalo-intake` (fake module mirror `api/intake.py` + `delivery/ledger.py`; cần test thật khi deploy).
- Ngoài ownership: `parse_runner.py`, `routers/zalo_sync.py`, `main.py`, `.env.example`, `test_zalo_parse_runner.py`, `test_zalo_sync_api.py` là của slice B — đã chạy test tương thích (27 passed) nhưng không sửa.
- Parity với contract corpus (`contracts/zalo-intake/examples/`, script `.agent/scratch/parity_zalo_validate.py`): 37/37 rec-* cases khớp tuyệt đối expected_errors; 17/17 pkg-* cases sinh đủ code expected — phần dư là `missing_captured_at`/`schema_invalid` trên records placeholder (fixtures pkg chỉ chứa `{}`/`{"x":1}`, contract pkg kind chỉ kiểm framing còn consumer gate kiểm nội dung record — superset có chủ đích). Không case nào MISSING code.

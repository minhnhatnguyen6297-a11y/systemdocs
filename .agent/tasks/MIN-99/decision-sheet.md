# MIN-99 decision sheet — Zalo raw-package consumer (notary_v2)

## Contract authority
`contracts/zalo-intake/zalo-intake.md` + vendored byte-identical schemas in
`notary_v2/schemas/zalo-intake/` (11 files, sha256 verified). Do NOT modify
schemas; validation failures on the vendored set are code bugs, not schema bugs.

## Consumer semantics (pinned from contract)
- Pull model: GET /intake/v1/packages (package-list.v1, params: consumer_id,
  after_sequence?, limit?) → per package GET bytes via logical names
  manifest/records/ready (or file spellings). READY gate: only import when
  READY.json exists+valid.
- Validate before import: manifest vs actual bytes (manifest sha256 of each
  file), schema validate manifest + every records.jsonl line + READY,
  consumer_id match, record_count match, size limits (body ≤ limits),
  sequence strictly > last imported sequence (else skip → idempotent).
- Import txn (one commit): ledger row + all raw rows → move dir
  staging→imported/<package_id> → then POST /intake/v1/receipts
  (intake.receipt.v1: accepted). Receipt id = uuid4, stored on ledger row.
  ACK only AFTER durable commit.
- Corrupt/failed validation: move to quarantine/<package_id>/ + ledger
  decision=quarantined + quarantine_reason; send receipt status=rejected
  with error{code,message} (contract allows rejected receipt — does NOT
  remove from producer pending; consumer tracks own decision and never
  re-imports a ledgered package_id).
- Lost ACK / replay: re-run finds ledger row → decision imported → re-send
  same receipt_id (receipts are immutable; identical replay is safe) → skip
  import. Never re-import package_id already in ledger.
- No image bytes anywhere: fetch ONLY manifest/records/ready logical names.
- captured_at semantics: raw records keep producer captured_at verbatim;
  imported_at is local receipt time.
- Parse jobs: after import, enqueue zalo_parse_jobs(package_id) durable —
  parser error NEVER un-ACKs; retry from stored raw only.

## Files already written by controller (DO NOT EDIT)
- `models.py`: ZaloRawRecord, ZaloImportLedger, ZaloSyncState, ZaloParseJob,
  ZaloIntakeResult (appended — see field comments).
- `database.py`: migrate_zalo_exchange_schema() (already runs green).
- `schemas/zalo-intake/` vendored (byte-exact).
- `services/zalo_exchange/__init__.py` (empty marker — create if missing).

## Environment/config (extend .env.example)
- ZALO_MODULE_URL (default http://127.0.0.1:8765)
- ZALO_INTAKE_API_TOKEN (Bearer for consumer auth; empty = open loopback)
- ZALO_CONSUMER_ID (uuid4 — must equal module settings.consumer_id)
- ZALO_EXCHANGE_ROOT (default data/zalo_exchange)
- ZALO_SYNC_INTERVAL_SECONDS (default 300; 0/negative = periodic sync off)

## Exchange dirs (created lazily under ZALO_EXCHANGE_ROOT)
staging/<package_id>/ → ready/<package_id>/ → imported/<package_id>/ |
quarantine/<package_id>/. Package files kept flat: manifest.json,
records.jsonl, READY.json.

## Slice A — services/zalo_exchange/ core + tests
Own: `services/zalo_exchange/{client.py, store.py, validate.py, sync.py}`,
`tests/test_zalo_exchange_client.py`, `tests/test_zalo_exchange_sync.py`.

- client.py: `IntakeClient(base_url, token=None, timeout=30)` — httpx.Client;
  methods: service_status(), list_packages(after_sequence=None, limit=200)
  → parsed package-list.v1 entries, fetch_bytes(package_id, logical_name)
  → raw bytes (logical names: manifest|records|ready; try `manifest` then
  `manifest.json` fallback), send_receipt(receipt_dict) → response dict,
  create_ocr_request(body) / get_ocr_request(request_id). Bearer header when
  token set. Raise `IntakeClientError(code,message)` on intake.error.v1.
- store.py: upsert raw records verbatim (payload as received — keep exact
  JSON text), ledger insert/decision update, sync_state get/set, parse_job
  enqueue, imported result helpers.
- validate.py: validate_package(dir) → manifest+records+READY schema
  validation (jsonschema lib already in requirements? CHECK requirements.txt
  first — if absent use the vendored-schemas approach of the module or a
  small local validator; DO NOT add deps without noting), byte-hash check,
  consumer match, record_count, limits; returns structured errors list.
- sync.py: `run_sync(db: Session, settings: SyncSettings) -> SyncReport`
  orchestrating the contract semantics above; `SyncReport{imported, skipped,
  quarantined, receipts_sent, errors[]}`; crash-safe at every stage boundary
  (staging is rebuilt, ready/imported are the durable states).
- Tests: httpx.MockTransport fake server implementing the intake surface;
  cover: happy path multi-package ascending sequence, corrupt manifest hash
  → quarantine+rejected receipt, lost-ACK replay (ledger has row, no
  re-import, resends same receipt_id), schema violation → quarantine,
  consumer mismatch, sequence out-of-order (skip lower), image-name fetch
  never attempted beyond manifest/records/ready, no writes to business
  tables (customers/properties unchanged), restart mid-flow resumes.
  Check requirements.txt for pytest/httpx — reuse existing test patterns
  from tests/test_document_intake.py conventions.

## Slice B — routers + parser runner + wiring + tests
Own: `routers/zalo_sync.py`, `services/zalo_exchange/parse_runner.py`,
`main.py` (wire), `.env.example` (append block), `tests/test_zalo_sync_api.py`,
`tests/test_zalo_parse_runner.py`.

- routers/zalo_sync.py (prefix /api/zalo): POST /sync → run_sync inline
  (manual Sync button); GET /sync/state → last_run/cursor/ledger counts/
  last_error; POST /ocr-requests → validate minimal intake.ocr-request.v1
  shape then client.create_ocr_request; GET /ocr-requests/{request_id} →
  proxy status doc; GET /results?package_id → stored zalo_intake_results.
  All endpoints 503 when ZALO_MODULE_URL unreachable (client error →
  CommandError-style JSON, match existing routers' error shape — read
  routers/ocr_ai.py error convention first).
- parse_runner.py: `run_pending_parse_jobs(db) -> int` — per pending job:
  load package's raw ocr_page/message_text records → for each, take
  text_lines from default transcript (record.body.transcript /
  selected_pass_ids path — CHECK actual raw-record payload shape in
  contract examples `contracts/zalo-intake/examples/valid/rec-0*` for the
  ocr_page body shape) → `ocr_pipeline._normalize_native_ocr_doc(lines,
  filename)` per page → aggregate via `_pair_persons` + property merge
  helpers in ocr_pipeline → store ZaloIntakeResult (revision = count of
  prior results for package +1, parser_version="ocr_pipeline-<date>").
  Job→succeeded/failed w/ sanitized error; retryable on next run.
  NEVER calls Qwen / network / reads image paths — text-only.
- main.py: `from routers import zalo_sync` + include_router + call
  migrate_zalo_exchange_schema() at startup (next to migrate_zalo_schema())
  + optional background periodic task honoring ZALO_SYNC_INTERVAL_SECONDS
  (asyncio task in lifespan, task cancellation on shutdown — mirror the
  existing lifespan connector-process cleanup pattern).
- .env.example: append the 5 vars with comments.
- Tests: FastAPI TestClient for router shapes + parse_runner on seeded raw
  records (two CCCD pages → paired person; one GCN page → property; parser
  exception → job failed, raw intact, ACK unaffected).

## Guards (both slices)
- NOT business tables: never write customers/properties/cases/participants
  or legacy zalo_* tables.
- NOT images: never fetch store/serve any image path/URL/bytes.
- NOT legacy paths: do not touch zalo_inbox.py/zalo_connector/ (MIN-101).
- Keep file writes confined to ZALO_EXCHANGE_ROOT subtree.
- Follow existing code style (Vietnamese comments ok, module docstring).
- Run the slice's tests with .\venv\Scripts\python.exe -m pytest tests/<files>
  and report counts. PYTHONPATH=repo root when needed.
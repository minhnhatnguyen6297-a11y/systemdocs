# MIN-99 slice B — progress (routers + parser runner + wiring)

Ngay: 25/09/2026 · Owner: subagent slice B · Trang thai: DONE (tests green)

## Da lam

- `routers/zalo_sync.py` (moi): `APIRouter(prefix="/api/zalo")` —
  POST /sync (run_sync + drain parse jobs), GET /sync/state (kv cursor +
  ledger/raw/parse/result counts), POST /ocr-requests (minimal
  intake.ocr-request.v1 validation khong can jsonschema, auto-fill
  request_id/consumer_id/submitted_at), GET /ocr-requests/{id} (proxy),
  GET /results?package_id (latest/package hoac moi revision khi co filter).
  `run_sync_once(db)` dung chung cho endpoint + periodic task.
- `services/zalo_exchange/parse_runner.py` (moi): `run_pending_parse_jobs(db)`
  — job pending+failed (retry), running->succeeded/failed + sanitized error,
  dedupe logical_id theo revision moi nhat (superseded -> marker),
  `selected_pass_ids` filter transcript, `_normalize_native_ocr_doc` per page,
  `_pair_persons` + `_merge_property_pair` fold cho property,
  `ZaloIntakeResult` revision = count+1, `PARSER_VERSION="ocr_pipeline-2026-09-24"`.
- `services/zalo_exchange/__init__.py` (moi): marker trong — sheet liet ke
  nhu controller file nhung chua ton tai; can cho package imports.
- `main.py`: import router + `migrate_zalo_exchange_schema()` sau
  `migrate_zalo_schema()`; gan `lifespan=lifespan` vao FastAPI (truoc do
  lifespan ton nhanh nhung khong duoc wire); periodic task asyncio theo
  `ZALO_SYNC_INTERVAL_SECONDS` (default 300, <=0 tat), cancel sach khi
  shutdown, `run_sync_once` chay trong `asyncio.to_thread`.
- `.env.example`: block 5 bien MIN-99.
- `tests/test_zalo_sync_api.py` (13 test), `tests/test_zalo_parse_runner.py`
  (7 test) — fake module qua sys.modules nen doc lap voi slice A.

## Divergence / quyet dinh nho

- `SyncSettings` field names cua slice A chua chot: `_build_sync_settings`
  doc accepted fields (dataclass/pydantic/signature) va map env theo ten
  (`module_url|base_url`, `token|api_token`, `consumer_id`,
  `exchange_root|storage_root`). Dieu chinh khi slice A merge.
- Intake client errors -> 502 `{"detail":{"code","message"}}`; transport
  (httpx.HTTPError) -> 503 `module_unreachable`. Sheet chi dinh 503 cho
  unreachable; 502 cho upstream rejection la them de khong nham voi loi local.
- `message_text` van normalize vao raw_results (status `message`) nhung
  KHONG aggregate len persons/properties (ngu canh, khong phai giay to).
- Failed parse jobs duoc retry o luot sau (pending+failed trong query).
- `main.lifespan` gio duoc attach that vao FastAPI — periodic task chi chay
  khi app serve; test dung `main.lifespan(app)` truc tiep nhu cu.

## Unverified / luu y

- Slice A (`client.py`/`sync.py`) chua merge — moi diem cham deu lazy import
  + test voi fake; can integration test lai khi slice A xong.
- `verify.ps1` changed-file detection khong resolve duoc path `notary_v2/...`
  tu repo-con trong monorepo -> no skip het test steps (quirk co san);
  da chay tay pytest: 27 test moi + 141 zalo/intake + 45 ocr_ai/env — all green.
- `PARSER_VERSION` la const ngay co dinh; update thu cong khi parser logic doi.

## Test counts

`pytest tests/test_zalo_sync_api.py tests/test_zalo_parse_runner.py` -> 27 passed.
Regression: test_zalo_inbox.py + test_zalo_inbox_api.py + test_document_intake.py
-> 141 passed; test_ocr_ai.py + test_zalo_env_setup.py -> 45 passed.

# Migration notes — MIN-103 slice B (Python engine port)

Ported from `notary_v2` (`services/zalo_inbox.py`, `routers/zalo_inbox.py`,
`models.py` Zalo tables) into this repo. This file is the single list of
**intentional differences** from the legacy baseline; everything else is a
parity port.

## Wire contract (unchanged)

- Env names kept verbatim: `ZALO_INBOX_BOOTSTRAP_SECRET`,
  `ZALO_INBOX_WEBHOOK_SECRET`, `ZALO_INBOX_BACKEND_URL`,
  `ZALO_INBOX_STORAGE_ROOT`, `ZALO_CONNECTOR_STATE_ROOT`,
  `ZALO_CONNECTOR_QUOTA_BYTES`, `ZALO_CONNECTOR_RETENTION_HOURS`,
  `ZALO_CONNECTOR_PARENT_PID`, `ZALO_CONNECTOR_FORCE_QR`,
  `ZALO_DATA_SYNC_TIMEOUT_SECONDS`.
- HMAC-SHA256 event signature over `{timestamp}.{body}`, ±300 s replay
  window; `GET config` signs an empty body; `GET commands/next` uses the
  derived key `HMAC(webhook_secret, account_id)` — the raw webhook secret is
  rejected there.
- Error envelope `{"error": {"code", "message"}}` with 400/409/503 mapping
  per legacy `_raise_http` semantics.

## Deliberate differences

| Tag | Difference | Reason |
|---|---|---|
| [MIN-103] | Route prefix `/zalo/inbox` → `/connector/v1` | New connector control-plane namespace for the independent module. |
| [MIN-103] | Table names `zalo_connector_accounts`/`zalo_sources`/`zalo_data_sync_runs` → `connector_accounts`/`conv_sources`/`data_sync_runs`; JSON columns stored as canonical TEXT; timestamps TEXT ISO-8601; booleans INTEGER | Module schema (m0002) is TEXT/INTEGER-only like m0001; column names otherwise preserved. |
| [MIN-103] | Dedupe anchor moved to `journal_entries.source_key` (unique); `event_json` = `{"component": <digest basis>, "result_id": <module id>}` | Sheet §4: journal is the dedupe anchor; same-identity-different-payload still raises 409 conflict. Every accepted event also writes one audit journal row. |
| [MIN-103] | Message records land in `records` (`kind="message_text"`); discovery lands as `kind="source_event"` on a `scope="source_event"` source row | Replaces `zalo_message_texts`/`zalo_media` write targets; `source_event` chosen over journal-only per sheet §4 default. |
| [MIN-97] | `message_text` record payloads validate against `schemas/raw-record.schema.json`; internal `attachments`/`conv_source_id` moved to the dedupe `journal_entries.event_json`. `source_event` payloads carry **no** `schema_version` claim — internal envelope pending contract-conformant emission (`event_body` enum has no `discovery`) | Record payload must not claim a schema it violates; the message↔media linkage survives on the dedupe journal row (`{"component","result_id","conv_source_id","attachments"}`). |
| [MIN-103] | `POST /connector/v1/connectors/start` always returns HTTP 200 with `{"status": "starting"|"running"}`; legacy emitted 202 on spawn | Body shape restored verbatim (routers/zalo_inbox.py:395); the 202 variant is dropped — loopback ops endpoint, connector never polls it. |
| [MIN-103] | Config `sources[]` is a superset of the legacy entry: adds `conv_source_id`, `conversation_type`, `policy_acked_version` on top of the legacy keys (`conversation_id`, `display_name`, `source_type`, `enabled`, `desired_enabled`, `acked_enabled`, `policy_version`) — the three enable flags are JSON booleans | Additive only; the connector reads a fixed field set and ignores extras. `acked_enabled === true` gating requires real booleans, not 0/1. |
| [MIN-94] | Text-quota FIFO eviction **dropped** (baseline `zalo_inbox.py:717-740`) | Retention is a uniform 168 h per contract; no per-source text cap exists in the module. |
| [MIN-97] | `protected_media_object_keys` derives from **all non-expired** `media_assets.rel_path` (`media/` prefix stripped) | Legacy fed this from active-batch items; the module has no batches. Correct under "chưa xóa được" semantics; narrowing to un-ACKed packages is a MIN-97 decision. |
| [MIN-97] | Media registered as `media_assets` rows with `rel_path="media/{media_object_key}"`, `sha256` of file bytes, `expires_at = sent_at + 168h` | Module storage vocabulary; file bytes are **not copied** — the row references the connector-staged object (same semantics as legacy register). |
| [MIN-103] | Single-account model retained: `onboard` returns the first account by `created_at`; `GET /state` reports that account only | Parity with legacy; multi-account is out of scope. |
| [MIN-103] | `heartbeat` and `media` events accepted but `media` relies on `message.attachments` for the main path; standalone `media` events dedupe/register identically and are otherwise unused | Baseline kept the event types live for the same contract; nothing downstream consumes a bare `media` event yet. |
| [MIN-95] | `GET /state` exposes only connector/policy/sources/data-sync — **no** batch, media-grid, export, or consumer state | `ZaloBatch`/consumer features are explicitly not ported (MIN-95 territory). |
| [MIN-95] | Module `/state` is an ops surface (no connector dependency); drops `consent_required`/`policy_pending`/`qr_generated_at`/`stranger_sources` split/`source_sync.status`/latest-data-sync fields pending MIN-95 needs | Those fields served the legacy consumer UI; the module's ops snapshot carries only what the connector lifecycle needs. |
| [MIN-103] | `my_documents` real-time ingest stays gated behind `MY_DOCUMENTS_REALTIME_VERIFIED = False` (metadata only) | Parity flag — source discovered + policy-managed but never ingests until verified live. |
| [MIN-103] | No connector auto-spawn in app lifespan; `POST /connector/v1/connectors/start` is the only trigger | Deliberate: module starts clean; connector lifecycle is explicit ops action. |
| [MIN-103] | `listener_sessions` rows are written only for *applied* state reports (stale-generation reports still journal but don't log sessions) | Session log reflects accepted observations; audit trail lives in the journal. |
| [MIN-103] | `media` event without `conversation_id` now 400s via source-metadata validation instead of a legacy `KeyError`/500 | Hardening; contract requires the field anyway. |
| [MIN-103] | Backend receipt time (`utcnow()` at event handling) governs `last_seen_at`/`gap_started_at`; connector `observed_at` is only recorded | Parity — backend clock is authoritative for state. |
| [MIN-103] | `intake_consent`/`sources/refresh`/`data-sync`/`sources PATCH`/`connectors/start` are unauthenticated loopback ops endpoints (same as legacy) | Parity; auth is only on the connector-facing webhook/config/commands surface. |

## Slice A — connector (Node)

| Tag | Difference | Reason |
|---|---|---|
| [MIN-103] | `WebhookClient` URL paths: `/zalo-inbox/api/connectors/onboard`→`/connector/v1/connectors/onboard`, `/zalo-inbox/api/webhook`→`/connector/v1/events`, `.../config`+`.../commands/next` same re-prefix; 2 URL literals in `core.test.mjs` | New module control-plane namespace; all other connector code is byte-verbatim from baseline. |
| [MIN-94] | `npm test` flakes 87–89/90: `runDataSync` tests race `FileOutbox.entries()` readdir→readFile ENOENT on Windows temp dirs | **Baseline-identical flake** — proven on unmodified source copy (88/90, same ENOENT). Not a port regression. Candidate fix for MIN-94: tolerate ENOENT between readdir/readFile in `FileOutbox.entries()`. |
| [MIN-103] | `package.json` renamed `zalo-intake-connector` 0.2.0; `zca-js` stays pinned 2.1.2 | Ownership rename only; no dep changes. |

## Slice C — OCR primitives (`ocr/qwen.py`, `ocr/prep.py`)

| Tag | Difference | Reason |
|---|---|---|
| [MIN-103] | `HTTPException(502)` → `OcrTransportError`/`OcrApiError`; `resp.json()` failure → `OcrParseError` | Sheet §1.4 — no FastAPI below api/ layer; legacy let JSON failure bubble into `error_stage="model"`. |
| [MIN-103] | No `notary_v2/.env` dotenv read — `os.environ` + Settings only | Module owns its key contract; env names identical (`QWEN_API_KEY`/`DASHSCOPE_API_KEY`/`QWEN_OCR_*`/`OCR_AI_*`). |
| [MIN-95] | `write_processed_image` takes explicit `dst_full`/`dst_crop` paths (no `target_dir`+`input_item_id` derivation); legacy Vietnamese error messages kept but raised as `OcrError` (was `InboxValidationError`) | Library-shaped primitives; wiring decides paths. |
| [MIN-103] | `inspect_media`/`render_pdf_pages` accept bytes + path; mime sniffed when absent | Convenience superset, same behavior on path input. |
| [MIN-103] | `enable_rotate` accepts `"0"/"1"` strings normalized via legacy env-parse set, emitted as JSON bool | Legacy emitted bool in payload — preserved. |
| [MIN-103] | Logging is plain `logger` calls (filename/model/latency_ms/lines), not legacy `_log_ocr_ai` JSON-event helper | Module logging policy. |

## Not ported (out of scope for slice B)

- `ZaloBatch`, export/package endpoints, media-grid consumer endpoints —
  MIN-95.
- Live Zalo/zca-js behavior and Qwen OCR calls — connector binary is spawned
  but never invoked in tests (mocked `Popen`).
- CLI `serve` still only mounts; connector start remains a POST.

## Schema version

`SCHEMA_VERSION = 2`: m0001 contract tables + m0002 engine tables
(`connector_accounts`, `conv_sources`, `data_sync_runs` with partial unique
index `uq_data_sync_runs_running_account WHERE status='running'`).

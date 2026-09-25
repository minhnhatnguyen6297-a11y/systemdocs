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
| [MIN-94] | `media` events are now the **supplement path**: a failed-attachment retry that succeeds after the envelope shipped emits `event_type:"media"` and upgrades the same `attachment_id` `missing`→`captured` (dedupe row rewritten to the downloaded basis) | One message = one envelope; the wire `media` event existed in v1 but was never emitted. |
| [MIN-94] | Failed attachment downloads ingest as `status:"failed"` + sanitized `error_code` (`download_failed`/`download_aborted`/`download_http_error`/`storage_full`) → `media_assets` row `state="missing"` + attachment `Source` (`image_available=0`) + `processing_status` `media_missing` record | v1 dropped or whole-message-retried failed media; the module keeps slots visible and non-fatal (`components.media[].status:"missing"` is a valid ACK). |
| [MIN-95] | `GET /state` exposes only connector/policy/sources/data-sync — **no** batch, media-grid, export, or consumer state | `ZaloBatch`/consumer features are explicitly not ported (MIN-95 territory). |
| [MIN-94] | `GET /state` adds `gaps[]` (from `listener_gaps()`), `queue{pending_jobs, oldest_age_s}`, `media{usage_bytes, quota_bytes, storage_full}` and `warnings[]` (`listener_heartbeat_stale`/`gap_open`/`disk_pressure`/`storage_full`) | Additive blocks only; the legacy keys are unchanged and consumer vocabulary stays excluded. |
| [MIN-95] | Module `/state` is an ops surface (no connector dependency); drops `consent_required`/`policy_pending`/`qr_generated_at`/`stranger_sources` split/`source_sync.status`/latest-data-sync fields pending MIN-95 needs | Those fields served the legacy consumer UI; the module's ops snapshot carries only what the connector lifecycle needs. |
| [MIN-103] | `my_documents` real-time ingest stays gated behind `MY_DOCUMENTS_REALTIME_VERIFIED = False` (metadata only) | Parity flag — source discovered + policy-managed but never ingests until verified live. |
| [MIN-103] | No connector auto-spawn in app lifespan; `POST /connector/v1/connectors/start` is the only trigger | Deliberate: module starts clean; connector lifecycle is explicit ops action. |
| [MIN-103] | `listener_sessions` rows are written only for *applied* state reports (stale-generation reports still journal but don't log sessions) | Session log reflects accepted observations; audit trail lives in the journal. |
| [MIN-94] | `listener_sessions` update rule: same-state report = heartbeat (`last_heartbeat_at` in place); state change = new row; `listener_generation` bump always opens a new row even when state repeats. `payload.reason`/`error_code` is persisted as `ListenerSession.reason` (≤200 chars) | Durable session semantics per contract "mỗi lần kết nối = một session_id"; v1 dropped `error_code` (baseline-open-issues drift now closed). |
| [MIN-94] | Media retention sweep: `expire_media` expires rows at `captured_at + ZALO_CONNECTOR_RETENTION_HOURS` (default 168h), deletes the original file + `media/derived/<attachment_id>{/, -, _, .}` variants, prunes empty dirs, flips `state="expired"`; `retention_sweep` job kind + per-pass sweeper registered via `media_jobs`/`build_sweepers()` | Contract lifetime is fixed per asset and never extended by package ACK; records/journal/packages survive; `missing` rows age out identically. |
| [MIN-103] | `media` event without `conversation_id` now 400s via source-metadata validation instead of a legacy `KeyError`/500 | Hardening; contract requires the field anyway. |
| [MIN-103] | Backend receipt time (`utcnow()` at event handling) governs `last_seen_at`/`gap_started_at`; connector `observed_at` is only recorded | Parity — backend clock is authoritative for state. |
| [MIN-103] | `intake_consent`/`sources/refresh`/`data-sync`/`sources PATCH`/`connectors/start` are unauthenticated loopback ops endpoints (same as legacy) | Parity; auth is only on the connector-facing webhook/config/commands surface. |

|| [MIN-97] | `Package.status` lifecycle is `sealed` → `acked` → `expired` (rows are always written explicitly; the m0001 column default `'pending'` is a dead value) | Contract lifecycle has no "pending" state — a package exists in the feed only once READY.json is published. |
|| [MIN-97] | Unknown package ids → `package_unknown` (contract §11 catalog name; no `package_not_found` code exists) | Contract error catalog is closed. |
|| [MIN-97] | Acked-package retention anchor = `max(sealed_at, receipt.received_at)` + 30d, cap 1 GiB total acked bytes | Union of the 30-day TTL and post-ACK window; un-ACKed packages are never purged. |
|| [MIN-97] | OCR `request_id` idempotent replay is looked up **before** the source-existence check (contract order would re-reject and hit the PK on replayed rejections); fresh-request semantics unchanged | Replay must return the stored decision. |
|| [MIN-97] | Quota counting: concurrent = `queued|running|retry_wait` jobs; per-day = provider **calls** = `SUM(CASE WHEN attempts>0 THEN attempts ELSE 1 END)` over non-rejected, non-deduped `ocr_request` jobs `updated_at` within a sliding 24 h window (`updated_at` keeps straddling retries in-window; over-counts rather than under-counts); multi-page attachments count per page | MIN-92 owner decision: 2/key · 100/day · 2 concurrent. |
|| [MIN-97] | OCR `GET /{request_id}` on an unknown id → 404 `unknown_source` (no dedicated not-found code in the catalog) | Contract error catalog is closed. |
|| [MIN-97] | Byte endpoints serve both contract paths (`.../manifest`, `.../records`, `.../ready`) and file-name spellings (`manifest.json`/`records.jsonl`/`READY.json`) | Contract names the logical resources; the on-disk names include `.json`. |
|| [MIN-95] | OCR job handlers **commit before raising** retryable/`JobExpired` errors so the worker's session rollback cannot erase completed page records or request state; permanent errors cap `job.attempts` so the worker marks `failed` immediately | Worker rolls back the whole session on raise; partial OCR progress must survive retries. |
|| [MIN-95] | OCR dedupe key = `(logical_id, variant, preset, config_version, image sha256)` against `succeeded` attempts only — failed passes never satisfy dedupe | §9.4: a re-ask for identical input must not bill Qwen again; a failed pass must not block a real retry. |
|| [MIN-95] | OCR task selector lives in env `ZALO_INTAKE_OCR_TASK` (default `text_recognition`), not a Settings field | Sheet constraint: no new settings fields this wave. |
|| [MIN-95] | `clean_message` sanitizer strips paths/URLs/blob-like tokens from every error/status string that lands in a raw record | Packages must never leak image paths/URLs/secrets to the consumer. |
|| [MIN-94] | `source_event` is a real wire event (`schema_version:1, event_type:"source_event"`): connector `undo`/`reaction` zca-js listeners normalize to `{event_subtype:"recall"|"reaction", targets, icon?}`; module ingest branch writes `Record(kind="source_event")` contract-shaped with own dedupe key (`InboxConflict` on same-key/different-payload) | Contract §5 source events were declared supported but never wired — now end-to-end. |
|| [MIN-94] | `cliMsgId` forwarded as `client_message_id` on message envelopes + `message_text.source.client_message_id`; `target_client_message_id`/`target_provider_message_id` link source events to captured messages | Contract Appendix A linking relied on a field that was dropped in `normalizeMessage`. |
|| [MIN-94] | `FileOutbox` durable attempt ledger (`.attempts` sidecar files): >8 send failures → entry moves to `outbox-dead/` + sanitized warning; `flush()` continues past a failed entry | A permanently-rejected first entry used to wedge the whole queue forever (head-of-line blocking). |
|| [MIN-94] | `listener_session` rows also emit `Record(kind="listener_session")` (logical_id=session_id, per-session revision chain); a closed gap interval emits `listener.uncertain_gap{started_at, ended_at, start_is_estimate:true}`; records are packaged (PACKAGE_KINDS now includes the kind) | Contract body enum requires the kind; heartbeats update the row only (no record spam). |
|| [MIN-94] | Internal `discovery` source_event rows are written `packaged_in="__internal__"` | They are ops observations, not contract records — keeps them out of packages without skip-note noise. |
|| [MIN-95] | Completed `ocr_request` jobs build a **dedicated sealed package** for their new records inside the handler; result `{package_id, manifest_sha256, new_revision}` satisfies `intake.ocr-request-status.v1`; dedupe path resolves the deduped record's package via `Record.packaged_in` | Contract `result` block must name the package that carries the new revision. |
|| [MIN-95] | Terminal request errors persist on the `ocr_requests` row (`terminal_error` in payload_json + `result_json.error`) before the job is raised; GET recovers codes from payload first with a `_REQUEST_ERROR_CODES` whitelist | Worker stores exceptions as strings — the catalog code must not degrade to `provider_failed`. |
|| [MIN-97] | OCR request auth is a router-level dependency (Bearer before body parse); day quota counts provider calls = `SUM(jobs.attempts)` over `ocr_request` jobs updated in a sliding 24 h window (+ queued×1); `Job.logical_id`/`request_id` set at enqueue; one running job per logical_id is enforced handler-side (conflicting active job → retryable backoff, `max_attempts` ≥8) | §9.3 auth-first, §9.6 calls-not-requests, §9.4 single-flight. |
|| [MIN-97] | Receipts are immutable once stored: byte-identical replay returns the stored decision; any different receipt on a decided package (or a `receipt_id` reused elsewhere) → 409 `package_conflict`; `received_at`/`sent_at` validated as ISO datetime (malformed → `schema_invalid`) | §8 ledger must never overwrite or flip a decided package. |
|| [MIN-97] | `claim_jobs` claims atomically: `UPDATE … SET state/lease/attempts/updated_at WHERE job_id AND state IN (queued,retry_wait)` per job, `rowcount==1` required | Two workers could double-claim the same job under select-then-update. |
|| [MIN-97] | Ops surface `/connector/v1` now requires `Authorization: Bearer <api_token>` when `ZALO_INTAKE_API_TOKEN` is set (state, media content, consent, sources refresh/PATCH, data-sync, connectors/start); unset → open loopback as before. Onboard keeps `x-zalo-bootstrap`; signed routes keep HMAC | Loopback parity plus fail-closed defense-in-depth for deployments that re-bind. |
|| [MIN-97] | `_clean_orphan_staging` also removes published `packages/<id>` dirs with no ledger row and newest mtime >10 min (crash between rename and commit) | Ledger is the feed; orphan dirs would otherwise persist forever. |
|| [MIN-94] | `media_assets.expires_at` derives from `ZALO_CONNECTOR_RETENTION_HOURS` (default 168) via `register_media(settings=…)` or env fallback — no longer a literal +168 h | Stored expiry must match the sweep's configured window or consumer `expires_mismatch` can fire. |
|| [MIN-97] | m0003 `ALTER TABLE` self-guards via `PRAGMA table_info(records)` | Crash/partial apply or a concurrent runner must not fail on duplicate column. |
|| [MIN-94] | Webhook `int()` casts (`attachment_index`, `listener_generation`, tail-hex parse) → 400 `validation_failed` instead of 500 | Unverified payload fields are input errors, not server bugs. |
|| [MIN-94] | Onboard bootstrap secret compare uses `hmac.compare_digest` (fails closed when unset) | Same policy as the webhook HMAC compare. |
|| [MIN-97] | `GET /intake/v1/status` no longer calls `record_access` per acked dir | Audit log only records real byte serves. |
|| [MIN-94] | `InboxConflictError` → HTTP 409 code `conflict` on the connector envelope | Connector wire has no closed catalog; `conflict` is the legacy parity name. |
|| [MIN-95] | `ocr_request` single-flight (§9.4): handler re-checks running same-`logical_id` jobs at entry — the oldest (`created_at`,`job_id`) proceeds, younger claimants raise retryable `SameLogicalBusyError` → backoff requeue; `max_attempts=8` for requeue headroom (response `attempt` still reports min(attempts,3)) | CAS claim alone cannot stop two workers racing the same logical. |
|| [MIN-94] | Contract amended (still `zalo-intake-v1-draft`): `event.reaction_icon` bound 1–4 → **1–64** chars — real zca-js tokens (`:handclap`) exceed the draft bound; `_validator/rules_record.py` + fixture `rec-37` updated in `contracts/zalo-intake/` | Producer-side truncation would corrupt icon data the consumer needs. |
## Slice A — connector (Node)

| Tag | Difference | Reason |
|---|---|---|
| [MIN-103] | `WebhookClient` URL paths: `/zalo-inbox/api/connectors/onboard`→`/connector/v1/connectors/onboard`, `/zalo-inbox/api/webhook`→`/connector/v1/events`, `.../config`+`.../commands/next` same re-prefix; 2 URL literals in `core.test.mjs` | New module control-plane namespace; all other connector code is byte-verbatim from baseline. |
|| [MIN-94] | `FileOutbox` hardened: `entries()` skips vanished files (`ENOENT`) and retries transient Windows `EPERM`/`EACCES`/`EBUSY` ≤3×25ms; `remove()` retries the same transient set then tolerates `ENOENT` | Fixed the baseline-identical readdir→readFile race (previously logged here as an 87–89/90 `npm test` flake, proven on unmodified baseline); persistent errors still propagate. |
|| [MIN-94] | `replaceOwned` helper in `processHistoryMessage`: a `replace()` that lands after abort-driven cleanup removes its own file again (`guard()` abandons raced-out work, so a late rename would resurrect an entry); the disconnect test now polls for the durable postcondition | Closes the residual flake where the disconnect test observed leftover queue files; connector passes 92/92 repeatedly. |
| [MIN-94] | Published envelopes ship `status:"failed"` + `error_code` markers for failed downloads (kept in `download-queue`, ≤3 attempts, `storage_full` doesn't consume attempts); a post-publish success emits a `media` supplement instead of re-publishing the message; exact-ACK accepts media status `missing` | Failed media stays visible instead of rejecting/dropping whole messages; upstream error text/URLs never cross the wire. |
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

`SCHEMA_VERSION = 3`: m0001 contract tables + m0002 engine tables +
m0003 `records.packaged_in` (durable marker — record đã phát trong gói nào;
phục vụ package build crash-safe/idempotent của MIN-97)
(`connector_accounts`, `conv_sources`, `data_sync_runs` with partial unique
index `uq_data_sync_runs_running_account WHERE status='running'`).

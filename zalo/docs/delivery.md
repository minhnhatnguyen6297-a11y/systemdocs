# Delivery & OCR-request surface — module Zalo intake

Covers the slice-C implementation of `contracts/zalo-intake/` (vendored
read-only under `schemas/`): raw package construction + ledger, the
authenticated consumer API, receipts, post-ACK retention, and bounded OCR
re-requests. Internal producer behavior defers to `docs/spec-producer.md`;
the wire contract defers to the vendored schemas.

## 1. Components

| Piece | File | Role |
|---|---|---|
| Package builder | `src/zalo_module/delivery/package.py` | `build_package(payloads, consumer_id, settings, session)` — writes `records.jsonl`, `manifest.json`, `READY.json` through a `packages/.staging-<id>/` dir then atomically renames; inserts the `packages` ledger row (`status="sealed"`, monotonic `sequence` per consumer, `manifest_sha256`, `record_count`). All bytes are UTF-8 / no BOM / LF-only canonical JSON (`sort_keys`, compact separators, `ensure_ascii=False`, `allow_nan=False`), each file ends in `\n`. |
| Ledger | `src/zalo_module/delivery/ledger.py` | `list_pending` feeds sealed packages; `record_receipt` validates each receipt against the vendored `receipt.schema.json`, enforces the `receipt_id` idempotency key, and keeps stored decisions immutable (`package_conflict`). |
| Schema engine | `src/zalo_module/delivery/_schema.py` | Stdlib-only port of the contract's JSON-Schema subset (incl. `x-error-code` propagation and strict JSON reading) so validation never drifts from `contracts/zalo-intake/_validator`. |
| Record check | `src/zalo_module/delivery/record_check.py` | `validate_record(payload)` → sorted contract codes: vendored `raw-record.schema.json` + the §11.3 forbidden-content scan (`provider_payload_forbidden`, `image_payload_forbidden`). |
| Package jobs | `src/zalo_module/jobs/package_jobs.py` | `scan_unpacked_records` sweeper, `handle_package_build`, `handle_package_sweep` + `expire_packages` + `package_retention_sweep`. Registers `package_build`/`package_sweep` handlers and both sweepers via `jobs.handlers`. |
| Intake API | `src/zalo_module/api/intake.py` | `/intake/v1/status` (open), `/packages` feed, package file endpoints, `/receipts`. |
| OCR API | `src/zalo_module/api/ocr_requests.py` | `POST /intake/v1/ocr-requests` (9-stage accept pipeline), `GET /intake/v1/ocr-requests/{id}`. |
| Auth | `src/zalo_module/api/_auth.py` | `require_consumer_auth` dependency + `IntakeRoute` route class that translates `ConsumerAuthError` into the `intake.error.v1` 401 envelope. |

## 2. Authentication (contract §3/§11.1)

- `settings.api_token` set → every endpoint under `/intake/v1/*` **except**
  `GET /status` requires `Authorization: Bearer <token>` (exact match,
  `Bearer` scheme only). Failures return HTTP 401 with
  `{"schema_version": "intake.error.v1", "error": {"code": "unauthorized"}}`.
- `settings.api_token` unset → loopback-as-auth: requests are allowed
  without a token. This mode is only sane on loopback; the token path is
  the production posture.
- Auth is enforced by a router-level dependency; `IntakeRoute` catches
  `ConsumerAuthError` inside the route handler so no app-factory exception
  wiring is needed.
- Body-level `consumer_id` is checked separately: receipts use
  `receipt_consumer_mismatch`; OCR requests return `unauthorized` when the
  body's consumer does not equal `settings.consumer_id` (fail-closed when
  no consumer is registered).
- The same guard protects the connector ops/mutation surface as
  defense-in-depth (fix I7): `GET /connector/v1/state`,
  `GET /connector/v1/media/{id}/content`, consent, sources refresh,
  data-sync, `PATCH /connector/v1/sources/{id}` and
  `POST /connector/v1/connectors/start` require Bearer when `api_token` is
  configured, and stay open on loopback when it is not. Onboard keeps its
  dedicated `x-zalo-bootstrap` check; `/events`, `/config` and
  `/commands/next` keep HMAC — neither takes the consumer Bearer.

## 3. Package build (contract §5, §7)

`scan_unpacked_records` (every worker pass) enqueues one `package_build`
job when `records.packaged_in IS NULL` rows exist with kinds
`message_text | ocr_page | processing_status | source_event |
listener_session` and no build job is already `queued|running|retry_wait`.
Internal discovery rows never wait: ingest writes them with
`packaged_in="__internal__"` (a sentinel, not a package id), so the
`IS NULL` selection skips them naturally.

`handle_package_build`:

1. Deletes orphan dirs under `packages/` (crash safety: a build that died
   before rename left no READY and no ledger row, so the next pass
   rebuilds cleanly and idempotently). Two shapes: `.staging-*` dirs —
   always orphaned, removed unconditionally — and published-looking
   `<package_id>/` dirs with **no** ledger row (crash between the atomic
   rename and the ledger commit), removed only when their newest mtime is
   older than 10 minutes so an in-flight build on another worker is never
   swept from under it.
2. Collects waiting rows ordered by `(captured_at, record_id)`.
3. Validates each payload via `validate_record`. Invalid rows are *never*
   dropped silently: a `processing_status` note (`status.code="note"`) is
   minted as the **next revision of the same `logical_id`** — reusing the
   invalid record's `captured_at`/`source` (immutable per contract §5.1),
   `supersedes` pointing at the previous revision — and shipped in the
   same package. When the payload cannot supply a usable `source` block
   (or the note itself would not validate / would overflow the package),
   the row is still consumed and the skip is reported in the job result +
   log warning; a dropped note never burns a revision number.
4. Enforces `PACKAGE_RECORD_LIMIT` (1000) and `PACKAGE_BYTES_LIMIT`
   (16 MiB); overflow rows stay unpackaged for the next build.
5. Calls `build_package` → sealed package on disk + ledger row
   `status="sealed"`.
6. Sets `records.packaged_in` **only after** sealing, in the same
   transaction — so `packaged_in` is exactly "emitted by a sealed package".

## 4. Package feed & file endpoints (contract §7.2)

- `GET /intake/v1/packages?delivery=pending&after=&until_sequence=&limit=`
  returns `intake.package-list.v1`. Only `sealed` packages are listed
  (acked/expired drop out). The first page of a sync run fixes
  `until_sequence` to the current max sequence — a **high-water mark**:
  packages ACKed or sealed mid-sync neither shift nor enter the window;
  order is ascending `sequence`, `limit` caps at 100.
- File serves, byte-exact from disk (`FileResponse`), available while the
  package exists — including after ACK until retention expiry:
  - `/packages/{id}/manifest` and `/manifest.json` → `manifest.json`
  - `/packages/{id}/records` and `/records.jsonl` → `records.jsonl`
  - `/packages/{id}/ready` and `/READY.json` → `READY.json`
  Unknown package or missing file → 404 `package_unknown`.
- `GET /intake/v1/status` computes acked-byte totals by walking package
  dirs but emits **no** `record_access` audit entries — audit is written
  only by real byte serves (the manifest/records/READY endpoints above),
  not by a stats poll.

## 5. Receipts (contract §7.3)

`POST /intake/v1/receipts` validates against the vendored
`receipt.schema.json` via the same subset validator used for records
(strict JSON profile first: BOM/NaN/dup keys → `json_invalid`; body
≤ 16 KiB → `request_too_large`). The schema's closed key set, uuid/sha256
formats and the RFC 3339 `received_at` (mandatory offset) all bound the
document — a malformed timestamp fails `schema_invalid` and can never
silently become a post-ACK retention anchor. Field checks map to contract
codes:

| Check | Code | HTTP |
|---|---|---|
| `consumer_id` ≠ registered consumer | `receipt_consumer_mismatch` | 409 |
| `package_id` unknown | `package_unknown` | 404 |
| `manifest_sha256` ≠ stored | `receipt_hash_mismatch` | 409 |
| `record_count` ≠ manifest | `receipt_count_mismatch` | 409 |
| stored decision exists, different body | `package_conflict` | 409 |
| `receipt_id` reused with different contents | `package_conflict` | 409 |
| receipt schema violation | `schema_invalid` | 400 |

`receipt_id` is the idempotency key: a byte-identical receipt replay
returns the stored decision (accepted receipts stay ACKed). A stored
decision is **immutable** — the same `receipt_id` carrying a different
canonical body, or *any* new receipt for a package that already recorded
one, is a `package_conflict`: `receipt_json` is never overwritten and the
package status never flips. `accepted` sets `status="acked"` and persists
the receipt; `rejected` (requires `error{}` per schema) leaves the
package `sealed` — the consumer quarantines but the package stays
pending.

## 6. Post-ACK retention (contract §8.3)

`expire_packages` runs every worker pass (`package_retention_sweep`) and
on demand (`package_sweep` job). Only `acked` packages are touched:

- TTL: `max(sealed_at, receipt.received_at) + 30 days ≤ now` → expire.
- Cap: total acked payload bytes > 1 GiB → expire oldest-first (ascending
  `sequence`) until under the cap.

Expiry deletes the package directory but **keeps the ledger row** with
`status="expired"`. `sealed`/un-ACKed packages are retained indefinitely —
even under disk pressure (CAP-12: pending raw survives restarts and the
media-retention sweep).

## 7. OCR re-requests (contract §9)

`POST /intake/v1/ocr-requests` runs the §9.3 accept pipeline:

1. **auth** — bearer (when configured) + body `consumer_id` match →
   `unauthorized`.
2. **screening** — size ≤ 16 KiB → `request_too_large`; strict JSON →
   `json_invalid`; vendored `ocr-request.schema.json` → `schema_invalid` /
   `unsupported_variant` / `missing_preset` (closed variant×preset matrix:
   `crop_bottom` needs `bottom_quarter|bottom_third|bottom_42pct`,
   `rotate` takes `auto`/null, `full_res` takes none); recursive
   forbidden-field scan (image refs, base64, data URIs, prompt/secret-ish
   keys) → `request_forbidden_field`.
3. **source** — `logical_id` must exist → `unknown_source`; disabled →
   `source_not_enabled`.
4. **replay** — same `request_id` + identical canonical body → the stored
   decision (`deduplicated: true`); different body → `request_conflict`
   (409 envelope). The idempotency-key lookup runs *before* the
   rejection stages so stored rejections replay safely.
5. **dedupe** — same `(logical_id, variant, preset, config_version)` with
   a job in `queued|running|completed` → persisted deduped row pointing
   at the original job (`deduplicated: true`); no second provider call.
6. **revision** — `observed_revision < sources.current_revision` →
   `stale_revision`.
7. **image lifetime** — `now ≥ image_expires_at` (or
   `captured_at + connector_retention_hours` fallback) →
   `source_image_expired`; `image_available = 0` →
   `source_image_unavailable`.
8. **quota** — > 2 supplementary jobs per `logical_id` → `budget_exceeded`;
   > 100 provider calls in the sliding 24 h window, or > 2 concurrent
   `ocr_request` jobs → `rate_limited` (`retryable: true`).
9. **accept** — `ocr_requests` row `state="queued"` + `ocr_request` job
   (`payload {request_id, logical_id, variant, preset, reason_code,
   observed_revision, config_version}`; execution is the provider
   handler's job).

Stages 3–8 return HTTP 200 with an `intake.ocr-request-status.v1`
document whose `state="rejected"` — the rejection is **persisted**
(`ocr_requests` row + marker job carrying the error), so restart-replays
return the same stored decision.

`GET /intake/v1/ocr-requests/{request_id}` returns the same status
document: `state` (job-state mapped onto the doc enum), `attempt`,
`max_attempts` (3), `job_id`, `deduplicated`, `accepted_at`,
`finished_at`, `result{package_id, manifest_sha256, new_revision}` on
completion, `error{code, message, retryable}` on rejection/failure.
Unknown `request_id` → 404 `unknown_source` (nearest catalog-legal code).

## 8. Package contents — what is never shipped

The forbidden-content scan (`record_check.forbidden_codes`) enforces
contract §11.3 on every packaged record and is also applied to
manifest/records bytes in tests: no image bytes, base64, image URLs or
paths, provider dumps (`provider_raw`, `provider_response`,
`raw_response`), secrets, parser output, or person/property/group
entities. Packages carry raw records + status + provenance only.

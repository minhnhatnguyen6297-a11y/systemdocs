# Zalo intake — OCR (MIN-95)

The OCR layer turns captured Zalo media into schema-valid `ocr_page`
records. It emits **raw text plus unverified provider evidence only** —
no document classification, CCCD/GCN extraction, person/asset merging,
grouping, or any other parser/business logic. All of that belongs to the
notary consumer; this repository must never grow it.

Code lives in `src/zalo_module/ocr/` (provider call, media prep, variant
frames, geometry parsing, record builders) and
`src/zalo_module/jobs/ocr_jobs.py` (sweeper + worker handlers). The
authoritative contracts are the vendored schemas under `schemas/` and
`D:\systemdocs\contracts\zalo-intake\zalo-intake.md` — never edit them to
make implementation easier.

## Scope / ownership

| This repo owns | The consumer owns |
|---|---|
| media→OCR sweep, default OCR pass | document classification |
| supplementary OCR on request (`ocr_request`) | regex/field extraction |
| `ocr_page` / `processing_status` raw records | person/asset merging, grouping |
| provider geometry as unverified evidence | business interpretation, UI |

## Record model

- **One `ocr_page` logical per page.** Image media → page 1. PDFs are
  rendered page-by-page; each page gets `Source(scope="page",
  page_index=N)` (1-based) plus its own record chain.
- Attachment-wide outcomes (`media_missing`, `image_expired`,
  `ocr_partial`) are `processing_status` records on a
  `Source(scope="attachment")` logical — never a substitute for page
  records.
- `image_expires_at` always equals `captured_at + 168h`; `image_sha256`
  and `image_state` mirror the `media_assets` row.
- Revisions **append, never overwrite**: `captured_at` and `source` are
  copied verbatim, `revision` increments, `supersedes` points at the
  previous record. `Source.current_revision` follows the newest revision.
- A supplementary attempt is appended to `ocr.attempts` with a fresh
  `ocr_pass_id` and its `request_id`. `ocr.text_lines` and
  `ocr.selected_pass_ids` keep describing the **default transcript** —
  a supplementary pass must not steal the default view.
- Error/status strings are sanitized (`ocr.records.clean_message`) so
  paths, URLs, provider payload fragments, or base64 blobs can never
  leak into a raw record (the record-check validator rejects them).

## Default pass — `ocr_default`

Payload: `{"attachment_id": "<uuid>"}`. Enqueued by the sweeper or by
intake-time code.

1. Resolve `media_assets` row → runtime file (audit-logged via
   `record_access`).
2. Missing file before expiry → `media_missing` status record, done.
   Expired media → `image_expired` status record, done.
3. Images → EXIF-transpose + JPEG-normalize. PDFs → render each page
   (≤300 DPI cap) and treat each as an independent page job.
4. Call Qwen (`build_qwen_ocr_body` + injectable transport) with
   `image_operation="original"`, `enable_rotate=False`,
   `region={kind:full_image}`.
5. Emit one `ocr_page` rev-1 record per page. Zero provider lines →
   `status=failed` with `error.code=empty_result` — never `succeeded`.

**Multi-page resilience:** pages are committed individually. A retryable
failure on page *N* preserves completed pages (the handler commits before
raising so the worker rollback can't erase them), and the re-run skips
pages that already have records. A terminal run with some pages failed
→ `ocr_partial` status record on the attachment.

## Sweeper — `scan_media_for_ocr`

Registered as a worker sweeper; runs every `run_once`/`run_forever`
pass *before* job claims.

- Scans `media_assets` in `captured`/`retained` state, **oldest
  `captured_at` first**, bounded to `SCAN_LIMIT` (20) per pass.
- Skips: expired media (datetime-aware, `Z`/`+00:00`-safe), media with
  an active `ocr_default` job, media whose pages already have
  `ocr_page` records, and assets that already burned
  `JOB_CAP_PER_ASSET` (5) failed jobs — permanent failures are not
  retried forever.
- Enqueues `ocr_default` with `logical_id`-style dedupe via the job
  payload.

## Supplementary pass — `ocr_request`

Payload: `{"request_id": "<uuid>"}` — the durable `ocr_requests` row
(written by the MIN-97 API) is authoritative for variant/preset.

Closed variant matrix (`ocr/variants.normalize_preset`):

| `variant` | `preset` | `image_operation` | `region` |
|---|---|---|---|
| `rotate` | `null` or `"auto"` | `rotate` | `full_image` — provider-side rotation (`enable_rotate=True`) |
| `crop_bottom` | `bottom_quarter` / `bottom_third` / `bottom_42pct` | `crop_bottom` | `bottom_fraction` 0.25 / 0.333… / 0.42 — client-side crop |
| `full_res` | `null`/omitted | `full_res` | `full_image` — original resolution |

Anything outside the matrix → request `failed` (`unsupported_variant`),
no provider call. Belt-and-suspenders: the schema is the API's job, the
handler refuses anyway.

Flow: `running` → expiry re-check (`expired` state + `JobExpired`, but a
status revision with `attempt.status="source_image_expired"` is still
published) → media read → single-page resolution (PDFs: the page this
`logical_id` covers) → **content dedupe** on
`(logical_id, variant, preset, config_version, image_sha256)` against
*succeeded* attempts only → frame build → Qwen → new revision appending
the attempt. Failed attempts never satisfy dedupe (§9.4).

**Dedicated result package** (`_publish_result_package`): a completed
request seals the revision it produced into its own raw package inside
the same transaction — it does not wait for the periodic `package_build`
sweep. The job result and the status document's `result` block expose
the pointer `{package_id, manifest_sha256, new_revision}` (contract
§9.5/§9.7). A deduplicated request resolves the same pointer through the
existing record's `packaged_in` — it never builds a second package. When
no consumer is configured or the payload cannot validate, the record
simply flows through the normal feed build (which flags invalid records
loudly).

**Terminal error durability** (`_request_terminal_error`): before the
handler raises, it writes a sanitized structured `{code, message,
retryable}` into `job.payload_json.terminal_error` **and**
`job.result_json.error`, sets `ocr_requests.state="failed"`, caps the
attempt counter, and commits. The worker's own `result_json` overwrite on
failure can never erase the terminal code — the status document's
`error` object reads `payload_json.terminal_error` first, then a
structured `result_json.error`, then the `"XxxError: <code>: …"` string
form, restricted to the recognized request error codes.

Request→job mapping: `queued`/`running`/`completed`/`rejected`/`failed`
live on `ocr_requests.state`; `expired` only when the image outlived its
168h window before OCR ran.

## Error taxonomy (worker-contract)

| Condition | Behavior |
|---|---|
| timeout / connect error / 429 / 5xx / malformed JSON | **raise** → worker `retry_wait` backoff (≤3 attempts); last attempt writes failure records for remaining pages |
| HTTP 401 / 403 | attempt `failed`, records written, **no retry** (attempt counter capped → job `failed`) |
| empty provider text | `failed` + `empty_result`, not retryable |
| unsupported media / corrupt file | `source_image_unavailable` failure records |
| media gone before expiry | `media_missing` (default) / `source_image_unavailable` (request) |
| image past `expires_at` | `image_expired` status (default) / `source_image_expired` revision + `JobExpired` (request) |

Two rules that make this safe under the worker's session rollback:
handlers **commit before raising** (records and request state must
survive the retry), and permanent errors **cap the attempt counter** so
`run_once` marks the job `failed` instead of looping.

## Geometry (contract §6.4/§6.5)

`ZALO_INTAKE_OCR_TASK` selects the provider task
(`text_recognition` default, `advanced_recognition` opt-in; anything
else falls back to `text_recognition`).

- `text_recognition` → `geometry_status="not_applicable"`, **no**
  `provider_lines` key.
- `advanced_recognition` + provider `words_info` → each element is kept
  **verbatim** as `provider_lines` (+ module `element_index` only).
  Valid `location` (8 finite numbers) / `rotate_rect` (5 finite numbers
  or `null`) → `present_unverified`; any malformed or non-finite shape
  → `present_invalid` with the raw element still preserved (bad fields
  dropped, text kept); no `words_info` → `absent`.
- Geometry-bearing attempts always carry `submitted_frame`
  (`{frame_id, width, height}`) and the real `transform_chain` — the
  provider saw *that* frame.
- `present_mapping_verified` is **never** emitted. Provider geometry is
  unverified evidence; consumers must use text-only fallback until a
  future contract defines verified coordinate mapping.

## Testing

Offline only — no real Qwen calls, no network.

- `tests/test_ocr_jobs.py` — sweeper bounds/dedupe/caps, happy path,
  error taxonomy, missing/expired media, empty results, multi-page PDF,
  partial success, commit-before-raise retry safety.
- `tests/test_ocr_requests.py` — all three variants + preset matrix,
  revision-2 immutability, dedupe (and dedupe-skips-failed), expired/
  missing media, provider-error mapping, invalid variant, dedicated
  result-package publishing + status-doc pointer, dedupe package
  resolution, and terminal-error persistence across worker overwrites.
- `tests/test_ocr_geometry.py` — `words_info` fixture
  (`tests/fixtures/ocr/words_info_ok.json`), valid/invalid/absent/
  not-applicable geometry, verbatim `provider_lines`.
- Every emitted record is asserted through
  `zalo_module.delivery.record_check.validate_record` — the same
  validator the delivery layer gates packages with — so a
  contract-invalid record fails the test, not the package.
- Provider stubbing: `monkeypatch` `zalo_module.jobs.ocr_jobs.OCR_CLIENT`
  with an object exposing `async post(url, headers=, json=, timeout=)`
  — the real body-build/taxonomy/parse path still runs.

Run: `.\.venv\Scripts\python.exe -m pytest tests -q`

> **ARCHIVED — kết quả và việc còn mở của v1, không là gate v2.** Việc còn mở của v2 theo [MIN-92](https://linear.app/minhnotary/issue/MIN-92), [MIN-102](https://linear.app/minhnotary/issue/MIN-102) và [MIN-90](https://linear.app/minhnotary/issue/MIN-90).

# Zalo Document Inbox — open issues

Status: open acceptance and shared-platform blockers
Updated: 2026-09-24 (baseline notes clarified; no new live acceptance)

This file records unresolved work only. It does not override the archived `spec-v1-legacy.md` or the current `spec.md`.

V2 redesign is tracked by MIN-89: [spec.md](spec.md) and
[source audit](v2-current-state-audit.md). The historical v1 limits below are
baseline evidence, not the target behavior for the new independent collector.

## ZALO-LIVE-001 — Realtime My Documents is not live-verified

- Status: open.
- Required evidence: on a controlled account, send one text and one supported JPG/JPEG/PNG/PDF to `My Documents`; confirm only events with `threadId == session send2me_id` are classified as `my_documents`.
- Negative evidence required: an ordinary outgoing self-message in another thread must not be classified as `my_documents`.
- Current evidence: unit/connector tests pass; no live `my_documents` text or media was observed.
- Stop condition: do not broaden the self-message rule to make the live test pass.
- History remains out of scope until a separate live spike proves upstream behavior.

## ZALO-LIVE-002 — Controlled Data Sync is not live-verified

- Status: open.
- Blocker: the live account discovered 975 enabled sources. Running account-wide history sync would risk importing private conversations outside the controlled acceptance set.
- Required setup: use a dedicated controlled account, or explicitly disable every source outside the approved test set and wait for policy ACK.
- Required evidence: manual click is the only trigger; one User and one Group history request; local seven-day/source-snapshot filtering; five counters; safe rerun/duplicates; My Documents excluded; gap warning retained; a new realtime event is not blocked.
- Upstream limitation: result is always best-effort and cannot prove completeness.

## ZALO-LIVE-003 — Remaining optional live matrix

- Status: open, non-blocking for merging Tasks 1–8 to the module branch.
- Verify a stranger event creates metadata only and persists no text/media.
- Verify external friend text and one non-private PDF. Live evidence currently covers a friend JPEG and group text.
- DOCX is intentionally unsupported; dropping DOCX without a placeholder is expected behavior.
- Verify outbox retry with a controlled temporary backend interruption if production-readiness evidence is required.

## OCR-SHARED-001 — Active OCR runtime must remove QR OCR

- Decision: approved by user on 2026-08-11.
- Normative rule: `docs/platform/document-intake/spec.md` is Qwen-only. Active Cloud AI OCR must not use server QR decode, client QR scan, QR rescue/fallback, QR-first routing, or QR/source priority.
- Historical blocker (2026-08-11): the integrated verifier reported a missing `ocr_ai.shape_cached_ocr`. Source recheck on 2026-09-24 found `shape_cached_ocr` in `routers/ocr_ai.py:2584` and the active Qwen-only route at `:2641`. The old missing-symbol note no longer describes this snapshot; no test suite or live OCR was rerun in MIN-89.
- Required task: a separate shared-OCR implementation/review must align `routers/ocr_ai.py`, its frontend callers, and tests with the normative Qwen-only contract.
- Scope boundary: do not solve this by restoring QR helpers or silently changing the Zalo module contract.

## Live evidence already completed

- QR login and user account approval.
- Single bound connector process and heartbeat-connected state.
- Source discovery, consent defaults, exact policy ACK, and manual Source Sync ACK.
- Friend JPEG intake and durable ACK.
- Group text intake after independent text quota/retention setup.
- Connector reconnect with persisted gap warning.
- Text quota recovery; media remained operational while text configuration was missing.

## Verification baseline

- Connector: 90/90.
- UI/setup: 18/18 after text quota provisioning.
- Focused integrated Python: 97 passed, one shared OCR failure.
- Canonical `verify.bat` with project venv: 135 passed, the same shared OCR failure.

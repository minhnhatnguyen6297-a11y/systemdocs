# Baseline open issues — module Zalo intake

Danh sách rủi ro/việc còn mở mà module thừa kế từ baseline v1
(`notary_v2/docs/platform/zalo-document-inbox/open-issues-v1-legacy.md`,
copy nguyên văn ở §1) **cộng drift phát hiện khi kiểm kê MIN-103** (§2).

File gốc v1 vẫn nằm ở notary_v2 làm bằng chứng lịch sử; file này là danh sách
rủi ro **đang sống** của module — cập nhật ở repo này, không cập nhật bản v1.

## 1. Open issues kế thừa từ v1 (copy nguyên văn)

> Nguồn: `open-issues-v1-legacy.md`, updated 2026-09-24. Trạng thái "open"
> vẫn nguyên — chưa có live acceptance nào bổ sung kể từ đó.

### ZALO-LIVE-001 — Realtime My Documents is not live-verified

- Status: open.
- Required evidence: on a controlled account, send one text and one supported JPG/JPEG/PNG/PDF to `My Documents`; confirm only events with `threadId == session send2me_id` are classified as `my_documents`.
- Negative evidence required: an ordinary outgoing self-message in another thread must not be classified as `my_documents`.
- Current evidence: unit/connector tests pass; no live `my_documents` text or media was observed.
- Stop condition: do not broaden the self-message rule to make the live test pass.
- History remains out of scope until a separate live spike proves upstream behavior.

### ZALO-LIVE-002 — Controlled Data Sync is not live-verified

- Status: open.
- Blocker: the live account discovered 975 enabled sources. Running account-wide history sync would risk importing private conversations outside the controlled acceptance set.
- Required setup: use a dedicated controlled account, or explicitly disable every source outside the approved test set and wait for policy ACK.
- Required evidence: manual click is the only trigger; one User and one Group history request; local seven-day/source-snapshot filtering; five counters; safe rerun/duplicates; My Documents excluded; gap warning retained; a new realtime event is not blocked.
- Upstream limitation: result is always best-effort and cannot prove completeness.

### ZALO-LIVE-003 — Remaining optional live matrix

- Status: open, non-blocking for merging Tasks 1–8 to the module branch.
- Verify a stranger event creates metadata only and persists no text/media.
- Verify external friend text and one non-private PDF. Live evidence currently covers a friend JPEG and group text.
- DOCX is intentionally unsupported; dropping DOCX without a placeholder is expected behavior.
- Verify outbox retry with a controlled temporary backend interruption if production-readiness evidence is required.

### OCR-SHARED-001 — Active OCR runtime must remove QR OCR

- Decision: approved by user on 2026-08-11.
- Normative rule: `docs/platform/document-intake/spec.md` is Qwen-only. Active Cloud AI OCR must not use server QR decode, client QR scan, QR rescue/fallback, QR-first routing, or QR/source priority.
- Historical blocker (2026-08-11): the integrated verifier reported a missing `ocr_ai.shape_cached_ocr`. Source recheck on 2026-09-24 found `shape_cached_ocr` in `routers/ocr_ai.py:2584` and the active Qwen-only route at `:2641`. The old missing-symbol note no longer describes this snapshot; no test suite or live OCR was rerun in MIN-89.
- Required task: a separate shared-OCR implementation/review must align `routers/ocr_ai.py`, its frontend callers, and tests with the normative Qwen-only contract.
- Scope boundary: do not solve this by restoring QR helpers or silently changing the Zalo module contract.

### Live evidence already completed (v1)

- QR login and user account approval.
- Single bound connector process and heartbeat-connected state.
- Source discovery, consent defaults, exact policy ACK, and manual Source Sync ACK.
- Friend JPEG intake and durable ACK.
- Group text intake after independent text quota/retention setup.
- Connector reconnect with persisted gap warning.
- Text quota recovery; media remained operational while text configuration was missing.

### Verification baseline (v1)

- Connector: 90/90.
- UI/setup: 18/18 after text quota provisioning.
- Focused integrated Python: 97 passed, one shared OCR failure.
- Canonical `verify.bat` with project venv: 135 passed, the same shared OCR failure.

## 2. Drift discovered at MIN-103 (kiểm kê `67998868`)

Những điểm lệch giữa tài liệu/spec và code baseline thật, phát hiện trong
inventory MIN-103. Đây là **ghi nhận drift**, không phải lỗi đã sửa — port
phải giữ parity hoặc ghi rõ trong `docs/migration-notes.md`.

- **`MY_DOCUMENTS_REALTIME_VERIFIED=false` gate** — `connector.mjs` hardcode
  gate này; realtime `my_documents` bị chặn ở code chứ không chỉ ở spec
  (ZALO-LIVE-001). Port nguyên gate; không bật ngầm.
- **`error_code` trong state event bị backend drop** — connector gửi
  `error_code` trong event `state` nhưng `apply_connector_report` v1 không
  lưu. Field chết trên wire — module giữ parity nhận-và-bỏ hoặc ghi
  migration-note nếu quyết định lưu.
- **`heartbeat` và `media` event: backend chấp nhận, connector không bao giờ
  phát.** Dispatcher v1 có nhánh cho cả hai; connector không có call site
  nào emit. Giữ nhánh accept cho parity; đừng giả định heartbeat tồn tại
  trên wire.
- **Cửa sổ history 7 ngày ≠ retention 168h.** `runDataSync` lọc history theo
  `cutoff_at − 7d` (source: `connector.mjs` ~:587); retention media là
  `captured_at + 168h` (`MediaStore.prune` theo mtime + `run.bat` provision).
  Hai con số "7 ngày" khác nhau không được trộn.
- **Single-account assumption là thiết kế cố định cả hai phía** — onboard
  trả "first account by created_at", `_receiving_connector_identity` dùng
  `.first()`, commands derive key trên một account. Mọi nơi port phải giữ
  giả định này; multi-account chưa được thiết kế.
- **`ocr_ai.py` là facade** — sau MIN-108, machinery thật nằm ở
  `routers/ocr_pipeline.py` (env `QWEN_OCR_{MIN,MAX}_PIXELS`,
  `QWEN_MAX_IMAGE_PX`, `ENABLE_ROTATE`, `OCR_AI_TIMEOUT_SECONDS`,
  `OCR_AI_CONCURRENCY`, `OCR_PAIR_FUZZY_*` đọc ở đó). Tham chiếu "ocr_ai.py"
  trong tài liệu cũ phải đọc là `ocr_pipeline.py` khi đối chiếu code
  (v2-current-state-audit.md có line refs đã stale).
- **`shell/sidecar` vẫn wire `zalo.status` vào engine cũ** —
  `command_registry.py:205` → `notary_adapter.py:529-562` import
  `services.zalo_inbox` và gọi `migrate_zalo_schema()`; comment trong
  `registry.js`/`navigation.test.mjs` claim "đã tách MIN-103" nhưng command
  còn nối. Cross-repo consumer stale — sẽ break khi engine rời notary
  (MIN-101 territory). **FLAG, không fix trong migration này.**

## 3. Điểm mở của v2 liên quan producer (trỏ SOT)

- **MIN-90**: lấy bù/đối chiếu sự kiện bot chưa từng nhận — ngoài phạm vi
  module v2 giai đoạn đầu.
- **MIN-92**: contract `contracts/zalo-intake/` — wire producer↔consumer
  (SOT: monorepo).
- **MIN-94/95/97**: rebuild listener/OCR/quota-dedupe-config_version trong
  module — xem `docs/spec-producer.md` §4.

# MIN-94 progress — durable collector + listener health + 168h retention

## Trạng thái: SLICE A CODE DONE — verify xanh cả hai suite; chưa commit (yêu cầu wave).

## Kết quả (repo `D:\zalo-intake`, working tree — commit cuối vẫn `13ea96c`)

Connector (`connector/`):

- `FileOutbox.entries()` skip file biến mất (`ENOENT`) giữa readdir→readFile,
  retry transient `EPERM`/`EACCES`/`EBUSY` ≤3×25ms (Windows AV/indexer);
  `remove()` chịu file đã xóa; exact-ACK nhận media status `missing`.
- Attachment hỏng → publish marker `{status:"failed", error_code}` (mã cố
  định `download_failed|download_aborted|download_http_error|storage_full`);
  `download_url`/`original_filename` chỉ sống trong download-queue, không
  bao giờ lên wire/log.
- Assembly publish khi mọi slot resolved (bytes hoặc marker) — không
  reject/drop cả message; media-only failure vẫn thành message
  (`raw_text:null`).
- Retry attachment bền ≤ `MAX_DOWNLOAD_ATTEMPTS=3` (`storage_full` không tính
  attempt); retry thành công sau publish → `event_type:"media"` supplement
  cùng `media_object_key`, không republish envelope.

Module (`src/zalo_module/`):

- `ingest_message_envelope`/`ingest_webhook_event`: failed marker →
  `media_assets` `state="missing"` + `sources` attachment (`image_available=0`)
  + `processing_status` `media_missing`; supplement → upgrade cùng
  `attachment_id` sang `captured` (sha256 thật, dedupe rewrite) → replay sạch.
- `listener_sessions` durable: transition → row mới; same-state →
  `last_heartbeat_at` in-place; generation bump → luôn row mới; stale
  generation chỉ journal (revoked không hồi sinh); `reason`/`error_code` lưu
  vào `ListenerSession.reason`.
- `GET /connector/v1/state` additive: `gaps[]` (listener_gaps), `queue`
  (pending_jobs/oldest_age_s), `media` (usage/quota/storage_full),
  `warnings[]` (listener_heartbeat_stale/gap_open/disk_pressure/storage_full).
- `storage/retention.py::expire_media`: due = `captured_at +
  ZALO_CONNECTOR_RETENTION_HOURS` (default 168h) → xóa file gốc + derived
  `media/derived/<aid>{/,-,_,.}` + prune dir rỗng → `state="expired"`;
  records/journal/packages giữ nguyên; `missing` hết hạn cùng luật; ACK gói
  không gia hạn.
- `jobs/media_jobs.py`: `retention_sweep` job kind + sweeper per-pass đăng ký
  qua `register`/`register_sweepers` → `handlers.build_sweepers()`.

Docs:

- `docs/collector.md` (mới): SOT hành vi collector — pipeline, failed
  markers, supplements, sessions/gaps, retention, /state, invariants.
- `docs/connector-protocol.md`: §3.2 wire attachments (+status/error_code,
  bỏ original_filename khỏi wire), §3.3 error_code→reason, §3.6 ACK
  `missing` + media supplements, /state blocks, env retention/quota,
  FileOutbox race.
- `docs/migration-notes.md`: +5 dòng MIN-94 (media supplements, missing
  ingest, /state blocks, listener_sessions rule, retention sweep, FileOutbox
  fix đánh dấu đã sửa flake baseline).
- `docs/baseline-open-issues.md`: đóng 2 drift (state error_code →
  reason; media event nay có call site).

## Verify

- `pytest tests -q`: **278/278 passed** (bao gồm 17 test mới
  `tests/test_collector_wave.py` + 1 test `/state` enrichment mới trong
  `tests/test_connector_api.py`).
- `connector npm test`: **92/92 passed** (bao gồm outbox ENOENT race,
  failed markers, sibling supplement, storage_full marker, bounded retry,
  sensitive-data redaction).
- Không commit — theo yêu cầu wave (report-only).

## Còn lại / parked

- `tests/test_ocr_requests.py::test_request_rotate_new_revision` từng fail
  ordering-dependent (fake client exhausted) — full suite run mới nhất qua
  sạch 278/278; không thấy tái phát, giữ quan sát (helper `_default_pass`
  gán `ocr_jobs.OCR_CLIENT` trực tiếp — có thể leaky giữa test).
- `tests/unit/test_package_bytes.py` từng fail status expectation trong 1
  run cũ — cũng qua trong run 278/278; nếu tái phát cần đối chiếu
  `delivery/package.py` (MIN-97 territory).
- `heartbeat` event: module vẫn accept như `state` nhưng connector chưa có
  call site emit (parity note).
- Shared worker/m0003/settings do controller wave khác own (decision-sheet
  §2) — file `jobs/worker.py`, `migrations/`, `settings.py` đã có thay đổi
  từ controller trong cùng working tree.


## Wave ket thuc (trang thai cuoi)

- 3 slice hoan tat trong `D:\zalo-intake` @ `488454f` + `9b0f797` (fixtures .gitattributes).
- Review doc lap vong 1: NEEDS_FIX (3 Critical + 9 Important + 12 Minor) -> fix F1/F2 da giai quyet het.
- Review doc lap vong 2: 3 muc con lai da xu ly trong commit wave:
  - I4: quota ngay dem provider calls that `SUM(CASE attempts>0 THEN attempts ELSE 1)` tren job `updated_at` trong 24h (bao gom retry lac window; over-count an toan).
  - I5: single-flight `ocr_request` per logical_id — handler `_check_single_flight` (job cu nhat thang, job tre requeue retryable; `max_attempts=8` headroom, doc `attempt`/`max_attempts` van cap 3 theo §9.5) + regression test.
  - Icon: contract amend 1-4 -> **1-64 ky tu** (`zalo-intake.md`, `rules_record.py`, fixture `rec-37` moi) — token Zalo that (`:handclap`) vuot bound draft; validate 100 case / 0 unexpected.
- Verify cuoi: **320/320 pytest** · **98/98 connector npm test** · `npm run check` clean · `verify.ps1` PASS.
- Snapshot `zalo/` re-export: 106 file @ `9b0f797`, manifest sha256 khop.
- Dead code: `src/zalo_module/ocr/request_ledger.py` (stub khong importer) da xoa.
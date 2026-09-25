# MIN-99 — Progress (controller tổng hợp)

> Trạng thái: **hoàn tất implementation** — chờ owner xác nhận Done trên Linear.
> Cập nhật cuối: 2026-09-25 (review round 2 fixes + full suite green).

## Kết quả

Consumer `services/zalo_exchange/` trong `notary_v2` đã hoàn chỉnh:

- **Slice A** (`progress-slice-a.md`): `client.py` (IntakeClient sync, Bearer,
  pagination, bytes, receipts, OCR request/status), `validate.py` (port line-
  faithful `_validator` contract — 10 schema vendored byte-identical ở
  `notary_v2/schemas/zalo-intake/`), `store.py` (ledger/raw/state/parse_jobs),
  `sync.py` (staging→ready→imported/quarantine, commit-trước-ACK, lost-ACK
  replay cùng `receipt_id`, 4xx dừng retry, 5xx/transport retry).
- **Slice B** (`progress-slice-b.md`): `routers/zalo_sync.py` (5 endpoint),
  `parse_runner.py` (latest-revision-per-logical, selected-pass filter,
  text-only, pairing person/property, raw markers, retry), periodic task +
  `lifespan` trong `main.py`, `.env.example` 5 biến.
- Models: 5 bảng `zalo_sync_state/import_ledger/raw_records/parse_jobs/
  intake_results` (`models.py` + `database.migrate_zalo_exchange_schema`).

## Verify

- Full suite: **519 passed, 1 skipped** (0 failed) — lần đầu sạch.
- Contract parity: 37/37 `rec-*`, 17/17 `pkg-*` (slice A).
- Seam A↔B smoke: app load, 5 endpoint đăng ký, `SyncSettings` bind đúng env.
- Boundary: fetch whitelist chỉ `manifest/records/ready`; không image byte/
  path/base64; không ghi business tables (test `test_business_tables_untouched`).

## Review độc lập (2 vòng)

- Vòng 1 (NEEDS_FIX → fixed):
  - I-1 **single-flight §7.2.5**: `threading.Lock` non-blocking trong
    `run_sync_once` — lượt 2 trả `{"already_running": true}` (test mới).
  - I-2 **parse-job wedge `running`**: `run_pending_parse_jobs` reclaim
    `running→pending` ở entry (single-process runner) + cap retry
    `_MAX_PARSE_ATTEMPTS=8` (2 test mới).
  - Minor: `sequence_invalid` diagnostic khi package mới tái dùng sequence
    cũ; `consumer_id` rỗng → fail-fast không quarantine hàng loạt;
    `IntakeClient.close()` ở OCR endpoints; `_exchange_root()` neo repo root
    thay vì CWD; gọn `_build_sync_settings` (bỏ alias-seam slice-time).
- Docs-structure pre-existing failures đã sửa: README trỏ contract MIN-105
  bỏ inline-code; `test_agents_routed_markdown_exists` skip khi `AGENTS.md`
  cố tình vắng (monorepo rule, commit be14999).
- Env: thêm `tzdata` vào `requirements.txt` (Windows thiếu IANA tzdb — 5 test
  legacy `test_zalo_inbox*` fail trên venv mới nếu thiếu).

## Deferred minors (ghi nhận, không sửa wave này)

- `pending_list` kv write-only (rescan after=0 là recovery thật).
- `service_status()` dead surface; `_download` return flag chưa dùng.
- File move post-commit có thể để lại evidence ở `ready/` (DB là truth).
- `_validate_ocr_request` lax (uuid non-canonical, submitted_at format) —
  producer enforce đầy đủ phía sau.
- `field_sources` degrade `front/back/merged` sau merge đầu (cosmetic).
- `/sync/state` expose toàn bộ kv (low-sensitivity, theo convention router mở).
- Periodic `to_thread` shutdown race (window nhỏ lúc tắt app).

## Còn lại

- Linear MIN-99 → Done (sau commit).
- MIN-100/101: integration + cutover — cần chạy thật 2 repo (ngoài scope build).
- MIN-98: bị chặn bởi dữ liệu thật (account Zalo + ≥100 ảnh nhãn + Qwen key).

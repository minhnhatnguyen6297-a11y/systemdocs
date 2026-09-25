# MIN-97 progress — raw package + pending/ACK + OCR request API

Status: slice C agent xong, chờ review độc lập (`4e5c8f18`) trước khi Done.

## Kết quả slice (agent report)

- `api/_auth.py`: `require_consumer_auth` + `IntakeRoute` (401 `unauthorized` envelope khi token set; loopback-as-auth khi unset, serve warn); `check_consumer_id`.
- `delivery/_schema.py` + `record_check.py`: port JSON-Schema subset + `validate_record` (raw-record schema + forbidden-content scan).
- `jobs/package_jobs.py`: `scan_unpacked_records` sweeper, `handle_package_build` (staging→atomic rename→ledger sealed→`packaged_in`), `package_sweep`/`expire_packages` (acked >30d hoặc >1GiB; unacked tuyệt đối không xóa).
- `api/intake.py`: auth trên mọi route trừ `/status`; feed chỉ `sealed` + consumer filter; 6 byte endpoints (contract + file-name spellings); `package_unknown`.
- `api/ocr_requests.py`: pipeline 9 stage §9.3 — strict JSON → schema codes → forbidden-field → consumer → idempotent replay/`request_conflict` → dedupe → `stale_revision` → `source_image_expired`/`unavailable` → quota (`budget_exceeded`/`rate_limited`) → accept+enqueue `ocr_request`.
- Tests: 50 mới (16 delivery + 34 intake api). `docs/delivery.md` SOT.

## Divergences đã merge vào migration-notes

package_unknown naming · anchor max(sealed_at, received_at)+30d · replay trước source check · concurrent=queued|running|retry_wait · day=sliding-24h non-rejected · GET unknown → 404 unknown_source · dual path spellings.

## Verify

- 50/50 test slice xanh; full suite 278/278; `npm run check` clean; `verify.ps1` PASS.

## Mở

- Review độc lập đang chạy.
- `Package.status` default `'pending'` trong models.py = dead value (ghi migration-notes; không sửa schema vì locked).
- `ZALO_INTAKE_SCHEMAS_DIR` override cho deployment schemas không cùng repo root.


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
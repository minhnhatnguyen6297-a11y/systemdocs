# MIN-95 progress — Qwen OCR wiring + variants + geometry

Status: slice B agent xong, chờ review độc lập (`4e5c8f18`) trước khi Done.

## Kết quả slice (agent report)

- `ocr/qwen.py`: `call_qwen_ocr_detailed` (lines+words_info+model), task kwarg, transport injectable.
- `ocr/pipeline.py`: SubmittedFrame, default/variant frame builders, geometry parse/validate, sync `run_ocr_call`.
- `ocr/records.py`: page/attachment Source+Record builders, provenance, `clean_message` sanitizer.
- `ocr/variants.py`: preset khép rotate→auto/null, crop_bottom→quarter/third/42pct, full_res→null.
- `jobs/ocr_jobs.py` (1170 ln): sweeper `scan_media_for_ocr` (20/pass, oldest-first, cap 5 job/asset), `ocr_default`, `ocr_request`.
- Tests: 49 mới (`test_ocr_jobs` 24, `test_ocr_requests` 14, `test_ocr_geometry` 11) + fixture `words_info_ok` + `sample_package` cho MIN-96/97.
- Quyết định đáng chú ý: commit-before-raise giữ page records; dedupe (logical_id, variant, preset, config_version, sha256) chỉ tính succeeded; `ZALO_INTAKE_OCR_TASK` env; geometry chỉ present_unverified/present_invalid/absent/not_applicable — không bao giờ present_mapping_verified.

## Verify

- 49/49 OCR test xanh; full suite 278/278 (sau khi sửa drift sealed).
- Controller: `npm run check` clean; `verify.ps1` PASS (278 pytest + 92 connector advisory + replay/status).
- Flake đã vá ở controller: `remove()` EPERM retry + `replaceOwned` self-clean + test poll postcondition → 92/92 × 6 lần.

## Mở

- Review độc lập đang chạy — verdict quyết định Done.
- Live Qwen measure (advanced_recognition trên ảnh thật) = việc của MIN-98.
- `OCR_CLIENT` module-global trong test_ocr_requests — flagged flake tiềm ẩn nếu tái xuất.


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
# MIN-97 — Raw package + pending/ACK + OCR request API (repo `D:\zalo-intake`)

Linear: https://linear.app/minhnotary/issue/MIN-97
Status: In Progress (agent slice C `d7eb9d2c` đang chạy nền).

Giao diện pin: `D:\systemdocs\.agent\scratch\MIN-94-95-97\decision-sheet.md` §4.
Contract authority: `contracts/zalo-intake/` + `D:\zalo-intake\schemas\*`.

Own (slice C): `delivery/**`, `api/intake.py`, `api/ocr_requests.py`,
`api/_auth.py` (mới), `jobs/package_jobs.py`, `tests/test_delivery*` +
`test_intake*`, `docs/delivery.md`.

Deliverables: `_auth.py` (Bearer khi api_token set; status mở;
consumer_mismatch); byte endpoints packages list/manifest.json/records.jsonl/
READY.json (cursor pagination ổn định); `package_build` handler + sweeper
`scan_unpacked_records` qua `records.packaged_in` (validate raw-record schema,
atomic staging→rename, sequence monotonic, crash-safe rebuild); receipt
validation đầy đủ (manifest_mismatch/receipt_count_mismatch/idempotent);
`package_sweep` xóa acked >30d/>1GiB — KHÔNG BAO GIỜ pending/unacked;
OCR request API hoàn chỉnh (unknown_source, variant khép, image_expired,
request_id idempotent, quota 2/key+100/day+2 concurrent đếm theo page,
enqueue job `ocr_request` — handler ở slice B); GET status theo
ocr-request-status schema; forbidden-field scan (không ảnh/base64/path/url).

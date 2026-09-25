# MIN-95 — Qwen OCR wiring + variants + geometry (repo `D:\zalo-intake`)

Linear: https://linear.app/minhnotary/issue/MIN-95
Status: In Progress (agent slice B `2a7994b8` đang chạy nền).

Giao diện pin: `D:\systemdocs\.agent\scratch\MIN-94-95-97\decision-sheet.md` §3.
Contract authority: `schemas/raw-record.schema.json` + `ocr-request*.schema.json`.

Own (slice B): `ocr/**`, `jobs/ocr_jobs.py`, `tests/test_ocr_*`,
`tests/fixtures/ocr/**`, `docs/ocr.md`. KHÔNG đụng `api/` (MIN-97),
`intake/` (MIN-94 — default OCR đi qua sweeper, không cần engine hook).

Deliverables: sweeper `scan_media_for_ocr` + handler `ocr_default` (prep →
Qwen → ocr_page record schema-conformant, strip base64/URL); handler
`ocr_request` (expired→JobExpired; dedupe (logical_id,variant,preset,sha256);
pass mới = record revision+1, default pass giữ); geometry
advanced_recognition → present_unverified/present_invalid/absent/not_applicable;
taxonomy retry (401/403 fail, timeout/429/5xx retry, partial → ocr_partial);
test mock timeout/429/401/malformed/partial/2-page/empty/missing.

Không parser/ghép/regex — boundary giữ ở notary.

# MIN-94 — Durable collector + listener health + 168h retention (repo `D:\zalo-intake`)

Linear: https://linear.app/minhnotary/issue/MIN-94
Status: In Progress (agent slice A `1ceddd60` đang chạy nền).

Scope trong wave song song MIN-94/95/97 — giao diện pin ở
`D:\systemdocs\.agent\scratch\MIN-94-95-97\decision-sheet.md` §2.

Own (slice A): `intake/**`, `connector/**`, `storage/**`, `jobs/media_jobs.py`,
`api/connector.py`, `cli.py`, `tests/test_collector_*`, `docs/collector.md`.

Deliverables: fix FileOutbox ENOENT race (flake baseline đã chứng minh);
listener_sessions durable + heartbeat; `/connector/v1/state` additive
(gaps/queue/media/warnings); attachments `status:"failed"` → media_missing
không reject envelope; expire_media sweep `captured_at+168h` bất kể ACK;
job `retention_sweep`; test synthetic (10 attachment, replay, crash, revoked
session, storage_full, fake-clock expiry).

Shared (controller đã làm): worker run_once/run_forever + JobExpired +
build_handlers/build_sweepers; cli `worker --once`; m0003 records.packaged_in;
settings.api_token default None.

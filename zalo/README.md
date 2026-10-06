# zalo-intake

Module thu nhận Zalo độc lập (MIN-91, scaffold tạo ở MIN-93). Repo này là
**source-of-truth** cho engine Zalo: listener, journal, media tạm, Qwen OCR,
gói raw và API OCR lại. `D:\systemdocs\zalo\` chỉ là snapshot một chiều — xem
`docs/repo-ownership.md`.

## Yêu cầu

- Python >= 3.12 (dev đang dùng 3.12.10)
- Node.js >= 20 — chỉ cần khi chạy connector (zca-js listener) ở `connector/`
- Windows: `run.bat`, `verify.ps1` chạy trực tiếp

## Cài đặt

```bat
pip install -r requirements.txt
```

Copy `.env.example` thành `.env` nếu cần override. **Không commit `.env` hay
secret thật** — repo chỉ chứa placeholder.

## Lệnh

```bat
run.bat migrate                                  rem tạo/nâng schema DB (runtime/zalo_intake.db)
run.bat replay tests\fixtures\synthetic\event_text_message.json
run.bat status                                   rem in intake.service-status.v1 JSON
run.bat serve --port 8790                        rem FastAPI loopback
```

Tương đương trực tiếp:

```bat
set PYTHONPATH=src
python -m zalo_module.cli migrate
python -m zalo_module.cli replay tests\fixtures\synthetic\event_text_message.json
python -m zalo_module.cli status
python -m zalo_module.cli serve --port 8790
```

## Test

```bat
set PYTHONPATH=src
python -m pytest tests -q
```

hoặc chạy toàn bộ kiểm tra:

```powershell
.\verify.ps1
```

## Layout

```
connector/     Node listener (zca-js) — port thật từ notary_v2 @67998868 (MIN-103)
docs/          Tài liệu nội bộ repo (xem mục Tài liệu bên dưới)
tools/         export_snapshot.ps1 — export snapshot một chiều sang monorepo
schemas/       Contract schema vendored — READ-ONLY, SOT ở monorepo contracts/zalo-intake/
src/zalo_module/
  settings.py    env + runtime dirs (mkdir là side effect duy nhất)
  audit.py       access.jsonl ghi mọi mở file/dir runtime
  types.py       contract types + signature ranh giới (plan §3.1)
  database.py    engine/session/migration runner
  models.py      declarative models khớp DDL
  migrations/    m0001_initial ...
  intake/        journal capture_event
  storage/       media + retention 168h
  jobs/          worker lease/claim
  ocr/           Qwen + variants + request ledger (stub ranh giới)
  delivery/      build_package + receipt ledger
  api/           /intake/v1 routers
  app.py  cli.py
tests/         unit + integration + fixtures/synthetic
runtime/       GITIGNORED — DB/session/media/packages/outbox/access.jsonl
```

## Tài liệu (`docs/`)

- [`docs/spec-producer.md`](docs/spec-producer.md) — **producer SOT**:
  CAP-01..16 chuyển từ `notary_v2` spec.md §2 tại MIN-103
- [`docs/connector-protocol.md`](docs/connector-protocol.md) — wire contract
  nội bộ connector↔module (`/connector/v1`, event shapes, HMAC, env)
- [`docs/local-runbook.md`](docs/local-runbook.md) — cài đặt, env, lệnh chạy
  module + connector
- [`docs/rollback-runbook.md`](docs/rollback-runbook.md) — quy trình quay về
  engine v1, quy tắc một listener, bảo toàn gói chưa ACK
- [`docs/baseline-open-issues.md`](docs/baseline-open-issues.md) — open issues
  v1 kế thừa + drift phát hiện tại MIN-103
- [`docs/repo-ownership.md`](docs/repo-ownership.md) — repo này là SOT;
  `D:\systemdocs\zalo\` là snapshot một chiều + cách dùng export

## Ghi chú quan trọng

- `runtime/` (DB, media, packages, outbox, access.jsonl) đã gitignore — dữ
  liệu thật không bao giờ commit.
- Không có secret nào trong repo; `QWEN_API_KEY` chỉ đọc từ env.
- `connector/` là connector thật — port hoàn chỉnh từ baseline
  `notary_v2/zalo_connector/` (commit `67998868`) tại MIN-103; xem
  [`docs/connector-protocol.md`](docs/connector-protocol.md) cho wire
  contract connector↔module.
- `schemas/` là **bản copy read-only** vendored từ
  `D:\systemdocs\contracts\zalo-intake\`. Không sửa ở đây; SOT nằm ở monorepo.
  Muốn đổi contract: sửa ở monorepo, duyệt, rồi vendor lại.

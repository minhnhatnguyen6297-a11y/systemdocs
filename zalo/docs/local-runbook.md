# Local runbook — zalo-intake

Chạy module độc lập trên máy dev. Module **không** phụ thuộc repo notary;
`PYTHONPATH=src` là đủ.

## Cài đặt

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Python >= 3.12 (dev: 3.12.10). Node >= 20 cần cho connector (`connector/`) —
xem mục Connector bên dưới.

## Cấu hình env

Copy `.env.example` → `.env` nếu cần override; **không bao giờ commit `.env`**
(đã gitignore). `settings.py` đọc biến môi trường thật — `.env` là tài liệu
tham chiếu; trên Windows `set` từng biến hoặc export trong shell trước khi chạy.
Biến chính:

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `ZALO_INTAKE_RUNTIME_DIR` | `./runtime` | Gốc dữ liệu runtime (DB, media, packages, outbox, access.jsonl) |
| `ZALO_INTAKE_DB_URL` | `sqlite:///<runtime>/zalo_intake.db` | DB nghiệp vụ của module |
| `ZALO_INTAKE_BIND` / `ZALO_INTAKE_PORT` | `127.0.0.1` / `8790` | Loopback serve |
| `ZALO_INTAKE_CONSUMER_ID` | — | uuid consumer; serve cần có để chấp nhận OCR request |
| `QWEN_API_KEY` | — | **Không default**; chỉ đọc từ env |
| `ZALO_ACCOUNT_ID` | — | uuid tài khoản sau khi login |

## Lệnh (PYTHONPATH=src)

```bat
set PYTHONPATH=src

rem tạo/nâng schema — in {"applied": n}
python -m zalo_module.cli migrate

rem journal một event thô — in {"capture_id","source_key","created"}
rem chạy lại cùng file: cùng capture_id, created=false (idempotent)
python -m zalo_module.cli replay tests\fixtures\synthetic\event_text_message.json

rem in intake.service-status.v1 JSON (đi qua app thật — khớp output serve)
python -m zalo_module.cli status

rem FastAPI loopback (status/packages/receipts/ocr-requests ở /intake/v1)
python -m zalo_module.cli serve --port 8790
```

`run.bat <subcommand>` là wrapper tương đương trên Windows (tự set PYTHONPATH).

## Test

```bat
set PYTHONPATH=src
python -m pytest tests -q
```

`pyproject.toml` đã khai báo `pythonpath = ["src"]` nên pytest cũng chạy được
mà không cần `set`. `tests/integration/` spawn subprocess với
`PYTHONPATH=<repo>/src` **thay thế hoàn toàn** — chứng minh module chạy độc
lập, không import được `notary*`.

## Connector

Connector là tiến trình Node (zca-js) trong `connector/`, nói với module qua
`/connector/v1` — wire contract ở `docs/connector-protocol.md` (route, event
shapes, HMAC, env). Cần Node >= 20.

```bat
rem cài dependency connector (zca-js pinned) — chạy một lần / sau khi đổi lock
npm --prefix connector ci

rem chạy connector trực tiếp từ repo root
npm --prefix connector start
```

Hoặc start qua API khi module đang serve (module spawn `node
connector/bin/run.mjs` với env đúng — khuyến nghị đường này):

```bat
curl -X POST http://127.0.0.1:8790/connector/v1/connectors/start
```

`serve` **không** auto-spawn connector — listener chỉ chạy khi được start
rõ ràng. Env connector cần (`ZALO_INBOX_BACKEND_URL`,
`ZALO_INBOX_BOOTSTRAP_SECRET`, `ZALO_INBOX_WEBHOOK_SECRET`,
`ZALO_INBOX_STORAGE_ROOT`, `ZALO_CONNECTOR_STATE_ROOT`, `ZALO_CONNECTOR_*`):
xem bảng env ở `docs/connector-protocol.md` §4 và block trong `.env.example`.
State session/outbox của connector nằm dưới `runtime/connector/` — đã
gitignore, không commit.

## Dữ liệu runtime

Mọi state nằm dưới `ZALO_INTAKE_RUNTIME_DIR` (mặc định `./runtime/`, đã
gitignore):

```
runtime/
  zalo_intake.db    SQLite — journal_entries, sources, records, jobs,
                    ocr_requests, packages, listener_sessions, schema_migrations
  access.jsonl      audit log mọi file/dir runtime module mở
  media/  packages/  outbox/  serve.log (khi chạy qua test fixture)
```

Reset sạch: xóa hẳn `runtime/` rồi `migrate` lại — thư mục tự tạo khi load
settings. Không commit gì trong `runtime/`.

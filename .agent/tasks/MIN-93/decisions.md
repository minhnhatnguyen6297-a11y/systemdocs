# Decisions — MIN-93

## D1. Repo nguồn chính = `D:\zalo-intake` (git local, main)

`D:\zalo-intake` là SOT code; `D:\systemdocs\zalo\` (nhánh consolidate/monorepo)
chỉ là **snapshot một chiều** do MIN-103 tạo: export script copy file + ghi
`SNAPSHOT_MANIFEST.json` (`source_commit`, `exported_at`, `files{path:sha256}`)
để đối chiếu; snapshot không mang `.git`, không submodule — tuân AGENTS.md cấm
nested git. Sửa chỉ ở `D:\zalo-intake`; snapshot tái tạo, không sửa tay.

*Lý do:* plan yêu cầu MIN-93 chốt nguồn chính + cơ chế một chiều; manifest/
checksum là cơ chế plan đặt tên ("ghi commit/manifest/checksum và cơ chế cập
nhật một chiều để hai bản không phân kỳ").

## D2. Migration runner tay, không alembic

`notary_v2/requirements.txt` không có alembic; plan cấm thêm công nghệ ngoài
TECH_STACK. `database.run_migrations` áp `migrations/m000N_*.py` theo thứ tự
qua bảng `schema_migrations` — idempotent, đủ cho scaffold và MIN-103.

## D3. Connector chỉ là chỗ đặt

`connector/` có `package.json` (engines node>=20, scripts check/test) + stub
`src/*.mjs` + `test/smoke.test.mjs` chạy được `node --test`. **Không** khai báo
`zca-js` dep — dep đi cùng code connector ở MIN-103 (baseline move), tránh
node_modules rỗng/không lockfile.

## D4. API scaffold: status/feed/receipt/OCR-request-idempotent thật; quota đầy đủ để MIN-97

`GET /intake/v1/status`, `GET /packages?after`, `POST /receipts`, `POST|GET
/ocr-requests` implement tối thiểu trên ledger DB. Quota 2/100/2 + dedupe
`config_version` + retry theo contract là **MIN-97** — scaffold chỉ giữ
idempotent theo `request_id` + `request_conflict`. `ocr/qwen.py`/`variants.py`
là stub NotImplementedError có signature — MIN-95 implement.

## D5. `audit.record_access` là bằng chứng isolation

Module ghi `runtime/access.jsonl` mọi file/dir runtime nó mở; integration test
assert mọi path dưới `runtime_root` và không chứa "notary" — đáp ứng acceptance
"đường runtime chỉ trỏ folder module" thay vì kiểm import tĩnh.

## D6. Subprocess test dùng PYTHONPATH=src duy nhất

`module_process` spawn `python -m zalo_module.cli` với env `PYTHONPATH` =
`D:\zalo-intake\src` (chỉ src của module) + `ZALO_INTAKE_RUNTIME_DIR` tạm —
thỏa "notary không trên PYTHONPATH" mà không cần `pip install -e`.

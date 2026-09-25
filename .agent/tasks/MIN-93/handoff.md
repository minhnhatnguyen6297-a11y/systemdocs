# Handoff — MIN-93

Viết khi kết thúc phiên hoặc chuyển giao cho agent/người khác.

## Trạng thái khi bàn giao — 2026-09-25

**MIN-93 hoàn tất.** Repo độc lập `D:\zalo-intake` (git local, nhánh `main`) đã
scaffold + verify xanh + 2 commit:

- `a2de16b` — scaffold (64 file, ~5400 dòng)
- `068ae58` — verify.ps1 dùng `.venv` python + PYTHONPATH=src

Nguồn chính = `D:\zalo-intake` (decision D1, `docs/repo-ownership.md`).
`D:\systemdocs\zalo\` chưa tạo — MIN-103 tạo snapshot một chiều +
`SNAPSHOT_MANIFEST.json`. Linear MIN-93 = In Progress (chưa đổi Done — owner
tự chốt trên Linear khi hài lòng).

## Repo có gì

- `src/zalo_module/` — settings(env) + audit(access.jsonl) + types;
  models/database/migrations(m0001, 9 bảng, runner tay — không alembic);
  intake/journal (`capture_event` idempotent theo `source_key`);
  storage/media + retention (168h); jobs/worker (queued/running/retry_wait/
  succeeded/failed/expired, lease 300s + reclaim);
  delivery/package (gói byte-exact manifest/records.jsonl/READY, sequence per
  consumer, atomic publish) + ledger (pending feed, receipt ACK idempotent,
  mã lỗi đúng contract §7.3);
  api/intake (status/package-list/receipts, error envelope, strict JSON
  BOM/NaN/dup → json_invalid) + api/ocr_requests (idempotent request_id +
  request_conflict + enqueue_job — quota đầy đủ là MIN-97);
  ocr/{qwen,variants,request_ledger} stub NotImplementedError (MIN-95/97).
- `cli.py`: `migrate | replay <event.json> | status | serve [--port]`
  (serve fail-fast nếu thiếu ZALO_INTAKE_CONSUMER_ID).
- `connector/` — stub Node (package.json + smoke test); zca-js 2.1.2 + code
  thật chuyển ở MIN-103.
- `schemas/` — 10 schema + CONTRACT_REVISION vendored byte-identical từ
  `contracts/zalo-intake/` (read-only).
- `tests/` — 36 unit + 4 integration (subprocess PYTHONPATH=src-only, tmp
  runtime, restart giữ captured_at, access.jsonl chứng minh không đường nào
  ra ngoài/không 'notary').

## Cách verify

```powershell
cd D:\zalo-intake
.\verify.ps1            # PASS: python check + pytest 40 + replay + status
# hoặc thủ công:
.venv\Scripts\python.exe -m pytest tests -q     # 40 passed
$env:PYTHONPATH='D:\zalo-intake\src'
.venv\Scripts\python.exe -m zalo_module.cli replay tests\fixtures\synthetic\event_text_message.json
.venv\Scripts\python.exe -m zalo_module.cli status
```

`.venv` do agents tạo khi verify (gitignored) — chứa dep đã pin. `runtime/`
gitignored — xóa để reset.

## Việc còn lại / rủi ro (chuyển MIN-103/94/95/97)

- **MIN-103**: migrate baseline connector/session/media/Qwen theo
  `docs/repo-ownership.md` + export snapshot `zalo/` + SNAPSHOT_MANIFEST;
  cập nhật `connector/package.json` dep zca-js@2.1.2 cùng lúc chuyển code.
- **MIN-94**: journal bền vững đã có hình hài — harden event shapes thật
  (attachment event, undo/reaction → source_event records), listener_sessions
  writer (hiện bảng trống → status luôn `disconnected`).
- **MIN-95**: `ocr/qwen.py` + `variants.py` implement; vendored validator
  raw-record chưa được gắn (TODO trong package.py/api) — fixture synthetic
  `account_id` không phải uuid sẽ bị validator bắt, đổi fixture lúc đó.
- **MIN-97**: quota 2/100/2 + dedupe `config_version` + forbidden-field scan
  + bearer auth + package byte endpoints `GET /packages/{id}/manifest|
  records|ready` (chưa có — reviewer đánh dấu) + `deduplicated` populate.
- Minor đã park (ledger): auth trước screening ở §9.3; `unknown_source` cho
  GET 404; types.py stubs trả None; python-dotenv chưa load_dotenv;
  pending/ack_bytes không scope consumer (v1 single-consumer);
  cli status tạo DB rỗng (TestClient lifespan); settings mkdir không log
  audit; run_after so sánh chuỗi ISO.

## File tạm đã dọn

- Giữ `.agent/scratch/MIN-93/` (decision-sheet + 5 slice reports + check_json.py)
  làm record cho MIN-103; dọn khi MIN-103 xong. `.agent/tasks/MIN-93/` đầy đủ
  brief/plan/decisions/progress/handoff.
- Không có file lạ trong repo; `.venv`, `runtime/`, `.pytest_cache` gitignored.

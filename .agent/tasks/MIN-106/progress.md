# Progress — MIN-106

## Trạng thái: DONE (chờ review) — 25/09/2026

## Đã xong

- `shell/sidecar/notary_gateway.py` — chọn mock khi `G1_DEV_NOTARY_MOCK=1`
  + không packaged (`sys.frozen`); packaged → strip + warning redact
  (một lần, chỉ tên biến). Dispatch real → `engine_not_installed`
  (retryable=false) tới khi MIN-107..110 thêm handler thật.
- `shell/sidecar/notary_mock_adapter.py` — 7 handler đúng contract
  `notary.case-drafting.v1`: workspace_get (`backend_mode:"mock"`),
  intake_analyze (giới hạn §5.2, marker `mock_fail`/`mock_unsupported`,
  partial+breakdown source_id), workspace_commit_stage (atomic,
  entity_id backend cấp, prune + re-evaluate cùng transaction,
  revision+1), diagram_evaluate/save (validate state v2, render_model
  deterministic, conflict/locked/outside-stage), word_export_options/
  batch (readiness theo block_reason enum, DOCX thật python-docx,
  naming `*_HS-<id>[_n].docx`, reservation trong batch, không ghi đè,
  all-failed → `word_batch_failed`, cancel giữa batch giữ file đã ghi).
- `shell/test/fixtures/notary-case-drafting/*.json` — 11 scenario
  (ready/empty/locked/conflict/intake-partial/diagram-warning/
  word-collision/word-partial/word-all-failed/word-canceled/unsupported),
  toàn tên/địa chỉ mẫu giả; `$ref_scenario` tái dùng ready/empty.
- `shell/test/test_notary_mock_adapter.py` — 65 test, reuse
  `contracts/notary-case-drafting/validate_examples.py` (`violations`)
  để chứng minh wire shape; TDD đã confirm fail trước implement.
- `shell/sidecar/command_registry.py` — append block `_notary_drafting`
  + `COMMANDS.update` 7 command (không reorder code cũ).
- `shell/src/main/config.js` — `NOTARY_MOCK_ENV` + `stripNotaryMockEnv`:
  packaged strip flag khỏi env con (sidecar kế thừa process.env) +
  warning redact; dev để nguyên để truyền xuống.
- `shell/src/main/main.js` — gọi `stripNotaryMockEnv` trước
  `sidecarCommand`/`SidecarManager`.
- `shell/test/test_sidecar_contract.py` — spawn sidecar thật với
  `G1_DEV_NOTARY_MOCK=1`, +5 test notary.* (workspace_get mock marker,
  case_not_found, intake partial breakdown, workspace_locked,
  word export idempotent không trùng file + DOCX mở được).

## Kiểm chứng

- `pytest shell/test/test_notary_mock_adapter.py -q` → 65 passed.
- `python shell/test/test_sidecar_contract.py` → 25 ran, OK.
- `pytest test_jobstore.py test_engine_adapters.py` → 18 passed, 1 skipped.
- `node --test shell/test/*.test.mjs` → 39 pass; `node --check` config/main OK.
- `git status` chỉ file trong scope; `rg -in zalo shell/sidecar/notary_*`
  → 0 hit trong 2 file mới (test file dùng `zalo_media` làm kind bị từ
  chối — phục vụ test `intake_unsupported_source`).

## Review round 1 (commit tiep theo)

- Error-code parity voi validator oracle: container-shape (stage khong
  dict / people|assets khong list; document_keys thieu/khong list;
  diagram/diagram.state thieu) -> `validation_error`; `stage_validation_error`
  / `word_no_documents_selected` / `diagram_invalid_state` chi cho dung
  ngu nghia (row-level / list rong / state co mat ma sai).
- JobStore pop marker `partial` khoi result truoc khi len wire.
- `_reserve_and_write` dung `open('xb')` exclusive-create — khu TOCTOU,
  giu reservation `taken` intra-batch; ghi loi -> unlink file hong.
- `g1-shell-sidecar.spec` comment: mock bundle nhung bat hoat packaged.
- Tests: +3 case container-shape -> validation_error; sidecar test assert
  `partial` khong len wire. 68 pass adapter, 25 pass contract, 10 pass
  jobstore.

## Giới hạn đã biết (platform, không sửa trong task)

- Job canceled/failed → jobstore `result=null` — per-file `skipped` của
  word batch chỉ tồn tại trên đĩa/đã bắt đầu ghi, không vào result job
  (giống real backend MIN-110 sẽ gặp).
- Mock engine v2 chỉ tính estate đơn giản (1 chủ đất đã chết → chia đều
  willReceive); status invalid/incomplete/complete đủ shape cho UI.

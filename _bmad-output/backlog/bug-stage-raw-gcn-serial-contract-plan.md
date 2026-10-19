---
title: 'Đồng bộ serial GCN Stage với chuẩn nguyên văn đã chốt'
type: 'bugfix'
ticket: '40'
created: '2026-10-20'
status: 'built'
route: 'full'
route_source: 'pinned'
review: 'quick'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context:
  - '{project-root}/AGENTS.md'
  - '{project-root}/contracts/entities.md'
  - '{project-root}/contracts/notary-case-drafting.md'
  - '{project-root}/_bmad-output/specs/notary_v2/README.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Stage từ chối serial ngoài `[A-Z]{2}\d{6,8}`, serial rỗng và serial trùng; DB mới còn `NOT NULL/UNIQUE`; đọc thay serial lạ bằng `XX…`; upsert ghép dòng theo serial. Repro 20/10/2026 qua `notary_adapter.workspace_commit_stage` trên DB tổng hợp đã từ chối cả ba ca.

**Approach:** Bỏ kiểm/chuẩn hóa serial ở Stage; đọc/xuất nguyên văn; cho phép rỗng/trùng. Đổi `properties.so_serial` thành nullable, không unique bằng migration tại chỗ giữ ID/khóa ngoại/giá trị. Chỉ `entity_id` liên kết tài sản. Chứng minh commit → mở lại phiên mới → xuất Word thật.

## Boundaries & Constraints

**Always:** Serial là SOT nguyên văn; không sửa giá trị cũ, sinh mã thay thế hoặc gộp thửa. Ghi trong một transaction, lỗi rollback. Migration chỉ đổi ràng buộc serial, giữ bản ghi/ID/link/land-row. `entities.md` §2, contract §4.2/§6.1, spec Stage §4 và decision-46 là nguồn chuẩn; không hỏi lại quy tắc serial.

**Never:** Không sửa contract/schema wire/spec; không đụng extraction #7/#22, `D:\testcase`, mẫu thực, gate #41; không sửa DB người dùng trong lượt implement/verify (chỉ test trên bản sao cô lập). Không thêm bảng/cột serial, không hậu tố hóa trùng, không tự chuẩn hóa chữ hoa/khoảng trắng.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| RAW | `so_serial="TEST-RAW/001"` | Commit OK; DB/snapshot/reopen/Word đúng chuỗi | Không lỗi serial |
| EMPTY | `so_serial=""` | Commit OK; đọc/xuất rỗng, không `XX` | Không lỗi serial |
| DUP | Hai thửa/tờ khác nhau cùng `DD123456` | Hai `Property.id`, hai link, giữ serial | Không lỗi serial |
| LEGACY | Master cũ `raw legacy 12/34` | `workspace_get`/Word trả đúng chuỗi | Không thay mã |
| TYPE | `so_serial=None`/số | `invalid_type` như contract string | `stage_validation_error` |
| DB-DUP | DB đã có hai dòng cùng serial | Migration giữ cả hai, không unique | Rollback nếu lỗi |

</frozen-after-approval>

## Code Map

- `notary_v2/services/case_workspace.py:83,226-231` — `_SERIAL_RE`/`_canonical_serial`, xóa.
- `...:2419-2438` — required/format/trùng trong `_validate_stage`; dùng ở `commit_stage` (:1118) và `create` (:1506).
- `...:1930-1940` — `_asset_wire` sinh `XX{entity:06d}`; bỏ.
- `...:2604-2620` — `_upsert_assets` tìm `Property` theo serial; bỏ, chỉ `entity_id`.
- `notary_v2/models.py:104` — `nullable=False, unique=True`.
- `notary_v2/database.py:42-85,109-119` — mẫu rebuild bảng và thêm cột.
- `notary_v2/main.py:33-41`, `shell/sidecar/notary_adapter.py:53-79` — chạy migration trước `create_all`.
- `notary_v2/routers/properties.py:80-87,248-257,346-357` — required/chặn trùng ở write path tài sản (inline-create là nút Stage web cũ).
- `notary_v2/frontend/templates/properties/form.html:28-29` — `required`; `cases/form.html:1403` — placeholder còn `*`.
- `shell/src/renderer/notary/case-drafting-model.js:85-100,132-143,977` — serial Stage luôn chuỗi, `''` không thành null.
- `notary_v2/services/word_engine.py:204` — `_serial_text` giữ nguyên văn (không strip).
- `shell/sidecar/notary_adapter.py:298-304` — `property_create` không còn bắt buộc serial.
- `shell/sidecar/notary_mock_adapter.py:71,985-997,1031` — validator mock.
- `shell/sidecar/notary_adapter.py:716-742,661-677,1077-1156` — commit/get/`word_export_batch` thật.
- `notary_v2/services/word_engine.py:1277-1290,1766,1789-1791,1959-1960` — Word đọc snapshot, `[Serial]`/`[Serial N]`.
- `notary_v2/tests/test_case_workspace.py:584-593,954-963`; `shell/test/test_notary_mock_adapter.py:860-870,898-907` — test đang khóa hành vi sai.

## Tasks & Acceptance

**Execution:**
- [x] `notary_v2/models.py` — `so_serial = Column(String(100))`.
- [x] `notary_v2/database.py` — thêm `migrate_properties_serial()` idempotent: nếu `PRAGMA table_info` notnull hoặc `PRAGMA index_list` có unique trên `so_serial` thì rebuild qua bảng tạm cố định `properties_serial_new`, copy đủ cột/ID, `DROP`/`RENAME`, tạo lại `ix_properties_id`, trong transaction `PRAGMA foreign_keys=off`; lỗi rollback + raise; no-op khi đã đúng.
- [x] `notary_v2/main.py`, `shell/sidecar/notary_adapter.py` — gọi migration mới sau `migrate_properties_schema()`, trước `migrate_property_land_rows()`.
- [x] `notary_v2/services/case_workspace.py` — xóa `_SERIAL_RE`/`_canonical_serial`; validator chỉ kiểm `str`; bỏ `seen_serials` và query DB; `_asset_wire` trả `"" if raw is None else str(raw)`; `_upsert_assets` chỉ resolve `entity_id`.
- [x] `notary_v2/routers/properties.py`, `properties/form.html`, `cases/form.html` — bỏ bắt buộc/chặn trùng serial; giữ địa chỉ bắt buộc.
- [x] `shell/sidecar/notary_mock_adapter.py` — bỏ `SERIAL_RX`, required/format/duplicate; giữ kiểm string.
- [x] `notary_v2/tests/test_case_workspace.py` — thay test từ chối bằng raw/empty/dup; thay test surrogate bằng giữ raw; thêm dup hai thửa → hai `entity_id`, mở lại service mới.
- [x] `notary_v2/tests/test_properties_serial_migration.py` — DB legacy `NOT NULL UNIQUE` có case/link/land-row; assert giữ ID/giá trị/link, nullable/non-unique; lần hai no-op; pre-create view `properties_serial_new` ép lỗi, assert DB cũ nguyên.
- [x] `shell/test/test_notary_adapter_contract.py` — commit raw/empty/dup qua adapter → `workspace_get` phiên mới → `word_export_batch` với DOCX tổng hợp `[Serial 1]`/`[Serial 2]`; assert đúng chuỗi, hai tài sản, không `XX`, trường khác không đổi.
- [x] `shell/test/test_notary_mock_adapter.py` — cập nhật hai test serial.
- [x] `_bmad-output/backlog/bug-stage-raw-gcn-serial-contract.md` — chỉ sau duyệt plan: ghi trạng thái/evidence, không đổi AC.

**Acceptance Criteria:**
- Given Stage có serial `TEST-RAW/001`, rỗng, hoặc hai thửa/tờ khác nhau cùng serial, when commit qua `notary_adapter.workspace_commit_stage`, then không lỗi serial, giữ đúng giá trị/từng tài sản, không `XX`/gộp.
- Given các ca đã commit, when `workspace_get` bằng session/service mới rồi `word_export_batch`, then serial Stage và DOCX đúng nguyên văn, đúng tài sản; Người/trường khác/nguồn không đổi.
- Given bản sao DB legacy `NOT NULL/UNIQUE`, when migration chạy, then nullable/non-unique, ID/property/link/land-row/giá trị nguyên vẹn; chạy lại không đổi; lỗi ép buộc để lại DB nguyên trạng.
- Given bộ test liên quan, when chạy sau sửa, then có bằng chứng trước/sau raw/rỗng/trùng/commit/reopen/export kèm lệnh/kết quả.
- Given repro trước sửa đã từ chối cả ba ca qua consumer thật, when đối chiếu AC5, then AC5 không áp dụng; evidence tại `_bmad-output/tmp/issue-40-repro/`.

## Implementation Notes

- 20/10/2026: `Property.so_serial` nullable/non-unique; `migrate_properties_serial()` rebuild in place (`properties_serial_new`, IDs/values/FKs preserved, `ix_properties_id` recreated, rollback on error), registered in `main.py` and sidecar `_ensure_db`.
- Review-fix round 20/10/2026: renderer `newAssetRow`/`updateAssetField`/`stageForWire` keep `so_serial=''` (null from old server maps to ''), with Node model tests; Word `_serial_text` bypasses `_safe_text` trim at all serial sites; adapter `property_create` no longer `_require`s serial; empty-serial DOCX assertion is exact.
- Stage validator no longer checks required/pattern/duplicate; `_canonical_serial`/`_SERIAL_RE` removed. `_asset_wire` emits stored raw (NULL→""); `_upsert_assets` resolves only by `entity_id`.
- Legacy properties router/form and case-form placeholder cut over; mock adapter matches contract (string type only).
- Tests: obsolete rejection/surrogate expectations replaced; migration preservation/failure/idempotence tests added; adapter end-to-end commit→fresh get→`word_export_batch` test added.
- Live-DB copy migration: 14 properties/14 cases preserved; serial_notnull 0; unique index removed; FK check clean; second run idempotent. No user DB written.
- Commit pending; no push.

## Plan Change Log

## Review Triage Log

- 20/10/2026 — independent Quick review: 3 blocking + 3 minor, all accepted and fixed. Re-check same day: CLEAN. Rerun: Notary 122 passed; shell adapter/mock 244 passed + 2 skipped; word_engine 71 passed; Node 97 passed (4 wire + 93 renderer). Findings: (1) renderer coerced empty serial to null → fixed in `newAssetRow`/`updateAssetField`/`stageForWire`/case-open normalization; (2) Word `_safe_text` trimmed serial → added `_serial_text`; (3) adapter `property_create` required serial → removed `_require`; (4) DOCX empty-serial assertion only prefix → exact line + negative unreplaced; (5) stale backlog note → updated with history marked; (6) adapter docstring claimed unique serial → corrected.

## Design Notes

Đối chiếu live `notary_v2/notary.db`: `properties.so_serial VARCHAR(100) UNIQUE` (đã nullable), 14 dòng; model/`create_all` vẫn `NOT NULL UNIQUE` (repro DDL). Vậy UNIQUE là ràng buộc thật; NOT NULL thật ở DB mới, không phải live; cả hai phải đồng bộ. Validator và nhánh surrogate `_asset_wire` cũng là ràng buộc thật, không phải báo cáo sai. Rebuild bảng vì SQLite không bỏ được `NOT NULL`/`UNIQUE` tại chỗ; giữ unique + hậu tố vi phạm nguyên văn. `entity_id` là liên kết duy nhất; dòng mới không khớp master theo serial. Snapshot `case_state_json` giữ serial nguyên văn; Word đọc snapshot trước master.

## Verification

**Commands (20/10/2026):**
- `cd notary_v2 && venv/Scripts/python.exe -m pytest tests/test_case_workspace.py tests/test_properties_router.py tests/test_property_land_rows.py tests/test_properties_serial_migration.py -q` → `122 passed, 37 warnings in 58.17s`.
- `cd D:/systemdocs && notary_v2/venv/Scripts/python.exe -m pytest shell/test/test_notary_adapter_contract.py shell/test/test_notary_mock_adapter.py -q` → `244 passed, 2 skipped, 34 warnings in 53.55s` (gồm test commit raw/rỗng/trùng + `word_export_batch` thật).
- `cd notary_v2 && venv/Scripts/python.exe -m pytest tests/test_word_engine.py -q` → `71 passed in 1.70s`.
- `cd D:/systemdocs && node --test shell/test/notary-wire-payload-schema.test.mjs` → `4 pass, 0 fail, 88.51ms`.
- `cd D:/systemdocs && node --test shell/test/notary-case-drafting-model.test.mjs` → `93 pass, 0 fail, 165.94ms` (new empty/null serial cases).
- `repro_adapter.py` → `raw OK revision=2`, `empty OK revision=3`, `duplicate OK revision=4`, serials `['DD123456','DD123456']`.
- `repro.py` → raw/empty/duplicate OK; `db-nonunique OK duplicate serial rows: 3`; legacy read returns `raw legacy 12/34`; schema `so_serial VARCHAR(100)`.
- Live-DB copy (`_bmad-output/tmp/issue-40-migration-livecopy/notary-copy.db`): 14 properties/14 cases, data_equal True for props/links/land/cases, FK `[]`, unique index removed, second run idempotent.
- Independent re-check 20/10/2026: CLEAN — 122 / 244+2 skipped / 71 / Node 97 (4 wire + 93 renderer). Commit pending; no push.

**Manual checks:**
- DOCX export text lines contain exactly `S1=TEST-RAW/001`, `S2=`, `S3=TEST-RAW/001`, `T1=123`, `T2=456`, `T3=789`; unreplaced `S2=[Serial 2]` absent; no `XX`.

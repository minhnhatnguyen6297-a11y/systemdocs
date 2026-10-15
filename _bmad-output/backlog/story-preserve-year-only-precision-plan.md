---
title: 'Giữ độ đầy đủ ngày Người (năm riêng vs 01/01) qua lưu/đọc/xuất Word'
type: 'bugfix'
ticket: '6'
created: '2026-10-16'
status: 'built'
baseline_revision: '4746d38993aea4829cf542583eb83cbfba1d300e'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: ['{project-root}/contracts/notary-case-drafting.md', '{project-root}/_bmad-output/specs/notary_v2/word-templates.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `_person_wire` (`case_workspace.py:1757-1764`) đọc ngày Người từ master `customers` (cột `Date`, `_parse_date_or_year` đệm năm riêng → `date(y,1,1)`) trước snapshot, nên `workspace_get` trả `2010-01-01` cho giá trị đã lưu `2010`; UI gửi lại đúng giá trị đó ở lần Cập nhật sau và **xóa bằng chứng năm riêng trong snapshot**. Probe trước sửa (`_bmad-output/tmp/issue-6-year-only-precision/`, SQLite tạm): commit wire `["2010","2010-01-01"]` → get `["2010-01-01","2010-01-01"]` → snapshot cả hai `"2010-01-01"`. Word cũng không phân biệt hai người và rò ISO trong token văn xuôi (`[Dòng người 1]`: “Sinh ngày: 2010-01-01”).

**Approach:** `case_state_json.stage[]` là bằng chứng đã commit của riêng hồ sơ (contract §4.1, MIN-141): đọc/emit ngày Người và render Word **theo snapshot trước, chỉ fallback master khi key vắng** (snapshot cũ). Formatter render đúng độ đầy đủ đã lưu — `YYYY` là năm, `YYYY-MM-DD` là dd/mm/yyyy; bỏ heuristic ngày-1/1 và rò ISO trên đường snapshot. **Không schema, không migration, không tái tạo dữ liệu đã mất**.

## Boundaries & Constraints

**Always:** Quyết định owner 15/10/2026 (`contracts/entities.md` §8.1, `specs/README.md` §6) — lưu/đọc/hiển thị phải phân biệt `2010` với `01/01/2010`, ngày quy ước chỉ dùng trong tính toán; giữ revision/ghi nguyên tử và ID field/slot hiện hành; raw nguồn intake còn nguyên; ngày sai lịch không bị cắt thành năm để che lỗi; **key ngày vắng trong snapshot cũ → fallback master và render ĐẦY ĐỦ `dd/mm/yyyy`** (date master không bị hạ thành năm riêng trên đường case); **key có mặt kể cả `null` → chặn fallback master** (cùng quyền key-presence MIN-141).

**Never:** Không đổi schema/DB, không migration phá hủy, không tự tạo cột mới; không sửa `routers/cases.py` (web cũ) hay module `customers`/Danh bạ; không đổi validation/retry/security ngoài phạm vi precision cutover; không đệm năm riêng thành ngày cho dữ kiện hiển thị/xuất; không tái tạo precision đã mất từ dữ liệu cũ; không Autoresearch/experiment; không commit trước khi có review độc lập.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Lưu năm riêng | commit wire `ngay_sinh:"2010"` | snapshot `"2010"`; get trả `"2010"`; Word `[Người N - Ngày sinh]`=`2010`, `[Năm sinh N]`=`2010` | không lỗi |
| Lưu ngày đầy đủ | commit wire `"2010-01-01"` | snapshot/get `"2010-01-01"`; Word `01/01/2010`, năm `2010` | không lỗi |
| Mở lại → sửa ô khác → Cập nhật | get rồi commit lại stage nguyên | snapshot giữ `"2010"` vs `"2010-01-01"` (không phình) | — |
| Sửa chính ô ngày | nhập `2010` (view gửi `"2010"`) | lưu `"2010"` (giữ năm riêng) | input sai lịch → view chặn tại ô |
| Snapshot cũ thiếu key | master `date(1980,1,1)`, snapshot không có `ngay_sinh` | get **và Word** trả `1980-01-01`/`01/01/1980` (đầy đủ, không hạ thành năm) | — |
| Key `null` chặn fallback | snapshot `"ngay_sinh": null`, master có `date(1980,1,1)` | get/Word để trống (không đọc master) | — |
| Lưu sơ đồ (diagram_save) | snapshot `"2010"` → Lưu sơ đồ | `save_diagram` ghi lại snapshot giữ `"2010"` (không phình qua `_compose_stage`) | — |
| Intake năm riêng | nguồn “Sinh năm 1980” | suggestion raw nguyên văn, normalized `"1980"` | không đệm ngày |
| Intake ngày sai lịch | nguồn “31/02/1980” | raw nguyên văn, normalized `null` + `intake.invalid_date` | commit `"1980-02-31"`/`"31/02/1980"` → `invalid_date`; không cắt thành `"1980"` |
| Token Word alias cũ | snapshot `"2010"` → `[ngaysinh1]`, `[ngaychet1]` | `2010` (không `01/01/2010`) | — |
| Token văn xuôi | snapshot ISO → `[Dòng người N]`, `[Ngày sinh hàng thừa kế N]` | dd/mm/yyyy, không rò `YYYY-MM-DD` | — |

</frozen-after-approval>

## Code Map

- `notary_v2/services/case_workspace.py:1757-1764` (`_person_wire`) — điểm sửa 1: ba field ngày đọc snapshot trước theo key-presence, fallback master khi key vắng; `_emit_date_or_year` (198-225) giữ nguyên.
- `notary_v2/services/case_workspace.py:1655-1666` (`persisted_people` trong `_compose_stage`) + `:2020-2058` (`_persist_migrated`) — dùng lại `wire`; sửa 1 tự chặn ghi đè khi migrate-on-read. `:2410-2413` (`_upsert_people`) và `:2232` (`_validate_stage`) giữ nguyên (đã nhận `YYYY|YYYY-MM-DD`, wire commit đã đúng — probe xác nhận).
- `notary_v2/services/word_engine.py:1175-1197` (`_snap_date_value`, `_snapshot_person_view`) — điểm sửa 2: bỏ collapse `"YYYY"`/ISO → `date(y,1,1)`; giữ nguyên giá trị đã commit, formatter quyết định hiển thị.
- `notary_v2/services/word_engine.py:130-160` (`_fmt_date`, `_fmt_snapshot_date`, `_fmt_birth_or_year`, `_fmt_year`) — sửa 3: `_fmt_birth_or_year` render chuỗi `YYYY` → năm, chuỗi ISO → dd/mm/yyyy, và **`date` (chỉ đến từ master fallback) → `dd/mm/yyyy` đầy đủ**; bỏ heuristic ngày-1/1 khỏi đường case (web cũ có bản riêng `routers/cases.py:1218`, không đụng).
- `notary_v2/services/inheritance_workspace.py:440-500` (`save_diagram` — command `diagram_save` của app) — ghi lại `case_state_json.stage` từ `_compose_stage.persisted_people`: cùng điểm sửa 1 bảo vệ đường "Lưu sơ đồ" (regression riêng).
- `notary_v2/services/word_engine.py:499-517` (`_word_person_from_stage`, giữ chuỗi snapshot), `:908-980` (`_person_placeholder_values`) — chỉ đọc.
- `notary_v2/services/word_batch_export.py:591+` (`export_batch`, folder mode `doc_specs`) — đường export thật để smoke introspect DOCX.
- `shell/src/renderer/notary/case-drafting-view.js:160-200` (`fmtDisplayDate`/`parseDisplayDate`) — chỉ đọc: UI đã giữ `YYYY` (test `shell/test/notary-case-drafting-view.test.mjs:748-775`), không cần sửa.
- `notary_v2/routers/cases.py`, `customers` router/`excel_parse.py` — **không đụng** (web cũ, Danh bạ master).
- Mẫu test theo convention: `notary_v2/tests/test_case_workspace.py`, `test_case_metadata.py`, `test_word_engine.py`, `test_word_batch_export.py`, `test_document_intake.py`.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/specs/notary_v2/README.md` §4 + `_bmad-output/specs/notary_v2/word-templates.md` §3.3 + `contracts/notary-case-drafting.md` §4.1 — ghi hành vi đang áp dụng: ngày Người đọc theo bằng chứng snapshot (key-presence), master chỉ fallback và ghi nhận đầy đủ; token render năm riêng là năm, ngày đầy đủ dd/mm/yyyy, không rò ISO — spec trước code vì thay đổi cách biểu diễn.
- [x] `notary_v2/services/case_workspace.py:1752-1777` — `_person_wire` dùng helper `date_wire` cho ba field ngày: `snap` có key → `_emit_date_or_year(snap[key])` (kể cả `null` chặn fallback); vắng → master.
- [x] `notary_v2/services/word_engine.py:1159-1190` — bỏ `_snap_date_value` (không ép `YYYY`/ISO về `date(y,1,1)`), `_snapshot_person_view` giữ nguyên giá trị đã commit; `:150-168` `_fmt_birth_or_year` xử lý chuỗi `YYYY`/ISO và `date` master → `dd/mm/yyyy` đầy đủ.
- [x] `notary_v2/tests/test_case_workspace.py` — 3 test: round-trip năm riêng vs 01/01 (create→get→sửa ô khác→commit→get + snapshot), key-null chặn fallback + key-vắng dùng master, migrate-on-read giữ năm riêng.
- [x] `notary_v2/tests/test_inheritance_workspace.py` — `save_diagram` giữ năm riêng khi ghi lại snapshot (consumer thứ ba qua `_compose_stage`).
- [x] `notary_v2/tests/test_snapshot_person_review.py` — export THẬT (mẫu DOCX tạm, `doc_specs` folder mode) + introspect docx: `[Người N - Ngày sinh]`, `[ngaysinhN]`, `[Dòng người N]` phân biệt `2010` vs `01/01/2010`, không rò ISO; hồ sơ cũ không snapshot → `date` master Jan-1 ra `01/01/1950`.
- [x] `notary_v2/tests/test_docx_word_first.py` — nguồn DOCX “1980” → stage/commit/get giữ `1980`. Criterion 2 (raw nguyên văn, `intake.invalid_date`, commit từ chối) đã có sẵn: `test_invalid_source_date_requires_correction_and_commits_exact_original_evidence`, `test_valid_iso_and_year_only_source_dates_remain_accepted`, `test_all_recognized_complete_dates_validate_calendar` — chạy lại đạt, không cần test mới.
- [x] `_bmad-output/specs/product-overview.md` + `_bmad-output/decisions/decision-6-date-precision-snapshot-authority.md` — trạng thái #6 + decision biểu diễn (snapshot là nguồn, không schema).
- [x] Dọn probe tạm: xoá `probe_before.py`; giữ log/JSON bằng chứng trong `_bmad-output/tmp/issue-6-year-only-precision/`.

**Acceptance Criteria:**
- Given hai Người (một `2010` chỉ năm, một `2010-01-01`), when lưu → mở lại → sửa trường khác → Cập nhật → mở lại, then giá trị vẫn `2010` vs `2010-01-01` và snapshot giữ đúng cả hai.
- Given cùng hồ sơ, when xuất Word bằng engine thật, then trường ngày được hỗ trợ phân biệt năm riêng (`2010`) với ngày đầy đủ (`01/01/2010`); token văn xuôi không chứa ISO thô.
- Given nguồn chỉ có năm sinh, when xem gợi ý, then raw còn nguyên và giá trị chuẩn hóa là `1980` (không đệm ngày).
- Given nguồn ngày sai lịch `31/02/1980`, when xem gợi ý, then raw còn nguyên, `normalized_value=null` + `intake.invalid_date`; giá trị sai không được lưu và không bị cắt thành `1980`.
- Given snapshot cũ thiếu key ngày, when đọc/xuất, then dùng master và ghi nhận là ngày đầy đủ (không suy năm riêng).
- Given test mới chạy trên baseline `4746d38`, when chạy round-trip/Word, then đỏ đúng hành vi phình `2010`→`2010-01-01`; sau sửa đạt.

## Implementation Notes

- Route `full` (auto): sau inspect còn chọn lựa biểu diễn/migration cần chốt (master Date vs snapshot) và cách kiểm chứng Word; rủi ro cao vì ảnh hưởng dữ kiện pháp lý (không hỏi lại quyết định owner đã chốt 15/10).
- Waiver: `_bmad-output/decisions/decision-bmad-all-active-loose-issues-no-autoresearch.md` (owner 16/10, “triển khai liên tục, không cần duyệt plan”) — không dừng chờ duyệt plan; vẫn giữ review độc lập + commit đúng phạm vi.
- Baseline `4746d38993aea4829cf542583eb83cbfba1d300e`; probe trước sửa đã chạy trong phiên (bằng chứng trong `_bmad-output/tmp/issue-6-year-only-precision/`), không chạy lại lỗi người dùng báo.

### Thực thi (append-only)

- **Sửa nguồn:** `case_workspace.py:1752-1777` (`date_wire` trong `_person_wire`); `word_engine.py:1159-1190` (bỏ `_snap_date_value`, `_snapshot_person_view` passthrough) + `:150-168` (`_fmt_birth_or_year`). Không đổi `_upsert_people`/validate/revision; không đổi UI (`shell/`).
- **Amendment frozen block (16/10, theo soát representation constraints):** bản đầu vừa ghi “fallback master = ngày đầy đủ” vừa giữ heuristic Jan-1→năm cho `date` — tự mâu thuẫn. Sửa: `date` (chỉ đến từ fallback master) render ĐẦY ĐỦ `dd/mm/yyyy` trên toàn đường case; heuristic chỉ còn ở bản riêng của web cũ (`routers/cases.py:1218`, ngoài consumer). Thêm hàng ma trận: key `null` chặn fallback; thêm consumer thứ ba `save_diagram` (`inheritance_workspace.py:440-500` ghi lại snapshot qua `_compose_stage`). Waiver 16/10 bỏ checkpoint duyệt plan nên amendment áp dụng trước code, ghi lại tại đây + Plan Change Log.
- **Bằng chứng (giữ trong `_bmad-output/tmp/issue-6-year-only-precision/`):**
  - `01-red-before.log` — 7 test mới đỏ đúng hành vi cũ: get `"2010"`→`"2010-01-01"`; key `null` vẫn đọc master; migrate-on-read ghi `"2010-01-01"`; `save_diagram` `"1950"`→`"1950-01-01"`; Word `[Người 1 - Ngày sinh]`=`01/01/2010`; hồ sơ cũ `Sinh ngày: 1950` (mất mức đầy đủ); intake “1980” lưu được nhưng get phình `1980-01-01`.
  - `02-green-focused.log` — 11/11 đạt (7 test mới + 4 guard sẵn có).
  - `03-focused-regression.log` — 612 passed, 2 skipped (12 file liên quan: workspace/metadata/snapshot/word/intake/docx/inheritance/property/customers).
  - `04-probe-after.json` — probe end-to-end sau sửa: get `["2010","2010-01-01"]`; snapshot sau “sửa ô khác + Cập nhật” giữ `["2010","2010-01-01"]`; export DOCX thật `["2010","2010","01/01/2010","2010","2010"]`; `[Dòng người 1]` = “Sinh ngày: 2010.” (hết ISO).
  - `05-full-suite.log` (chạy từ repo root — sai cwd, 39 lỗi đường dẫn tương đối) và `06-full-suite-root.log` (đúng cwd nhưng chạy song song với pytest khác dùng chung basetemp — 8 lỗi: 5 môi trường + 2 tranh basetemp + 1 env) — **superseded** bởi `07-full-suite-clean.log` (chạy một mình, basetemp riêng).
  - `plan.html`/`plan.packed.html` — exhibit-first present trước triển khai (pack sạch, 1 warning về độ dài prose); kiểm bằng browser: 4 claim, 1 machine, 2 mock, 0 error box — chỉ kiểm cấu trúc/tree, chưa mở từng state trực quan.
- **Fix theo review (new-catalog Word fallback):** `_word_person_from_stage` nhận map khách hàng của hồ sơ và áp **key-presence cho đúng 3 field ngày** (`key in stage_person`, kể cả `null`, chặn fallback; key vắng → master, render đầy đủ dd/mm/yyyy); `_build_word_persons` dựng map theo `id` entity từ `nguoi_chet` + `participants[].customer` (nguồn giống `_pick_core_people`) — không thêm public surface/schema/master write, không đổi thứ tự/row_id/phân loại chủ đất chết. Regression mở rộng: export THẬT cho snapshot cũ thiếu cả 3 key (`[Người 1 - Ngày sinh|Ngày chết|Ngày cấp]`, `[Dòng người 1]`, `[Chủ đất chết 1 - Họ tên]`) + phase key `null` chặn fallback. Targeted run: `tests/test_snapshot_person_review.py tests/test_word_engine.py tests/test_word_batch_export.py -q` → **149 passed, 2 skipped**.
- **Criterion 2 (raw/intake) không cần code mới:** đã phủ sẵn bởi `test_docx_word_first.py::test_invalid_source_date_requires_correction_and_commits_exact_original_evidence` (+ 2 test year-only/calendar) và `norm_date`; chạy lại trong `03`.
- **Exhibit (trình bày trước triển khai):** `_bmad-output/tmp/issue-6-year-only-precision/plan.packed.html` (nguồn `plan.html`); pack sạch, browser kiểm cấu trúc: 4 claim · 1 machine · 2 mock · 0 error box. Giới hạn: chưa mở từng state trực quan; theo waiver 16/10 không phê duyệt qua HTML.
- **Giới hạn:** web cũ `routers/cases.py` và Danh bạ `customers` giữ hành vi riêng (ngoài đường case, không đụng); master vẫn là cột `Date` (fallback ghi nhận đầy đủ); probe/export dùng fixture tạm, không đụng dữ liệu production.

### Smoke thật (đường người dùng, fixture tạm) — lệnh + JSON đầy đủ

Lệnh đã chạy (probe scratch `probe_before.py`, đã xoá sau khi lưu output; bản durable tương đương là test export bên dưới):

```sh
cd D:/systemdocs/notary_v2
"D:/systemdocs/notary_v2/venv/Scripts/python.exe" \
  "D:/systemdocs/_bmad-output/tmp/issue-6-year-only-precision/probe_before.py" \
  > "D:/systemdocs/_bmad-output/tmp/issue-6-year-only-precision/04-probe-after.json"
```

Lệnh durable (chạy lại được, không cần script scratch):

```sh
cd D:/systemdocs/notary_v2
PYTHONPATH=D:/systemdocs "D:/systemdocs/notary_v2/venv/Scripts/python.exe" -m pytest \
  tests/test_snapshot_person_review.py::test_year_only_and_full_dates_stay_distinct_through_export \
  tests/test_case_workspace.py::test_year_only_dates_survive_save_reopen_edit_unrelated_and_recommit -q
```

`04-probe-after.json` — create (2 Người: `2010` chỉ năm, `2010-01-01` đầy đủ) → get → sửa `dia_chi` Người 1 → Cập nhật → get → mapping Word → **export DOCX thật** (`word_batch_export.export_batch`, mẫu DOCX tạm):

```json
{
  "create_wire_dates": ["2010", "2010-01-01"],
  "get_dates": ["2010", "2010-01-01"],
  "commit2_wire_dates": ["2010", "2010-01-01"],
  "snapshot_stage_dates": ["2010", "2010-01-01"],
  "get2_dates": ["2010", "2010-01-01"],
  "mapping": {
    "[Người 1 - Ngày sinh]": "2010",
    "[Người 1 - Năm sinh]": "2010",
    "[Người 2 - Ngày sinh]": "01/01/2010",
    "[Người 2 - Năm sinh]": "2010",
    "[ngaysinh1]": "2010",
    "[Năm sinh 1]": "2010",
    "[Ngày sinh hàng thừa kế 1]": "01/01/2010",
    "[Dòng người 1]": "1. ông Nguyễn Văn Chết; Sinh ngày: 2010.\nsố: TLK 12/2011 ngày 16/05/2011.\nNơi chết: xã đã sửa.\nLà chủ đất."
  },
  "batch_status": [["probe", "saved", null]],
  "exported_paragraphs": ["2010", "2010", "01/01/2010", "2010", "2010"]
}
```

(`exported_paragraphs` theo thứ tự token trong mẫu tạm: `[Người 1 - Ngày sinh]`, `[Người 1 - Năm sinh]`, `[Người 2 - Ngày sinh]`, `[Người 2 - Năm sinh]`, `[ngaysinh1]`.)

### Dọn test pin lỗi thời (việc riêng, ngoài phạm vi precision)

- **Xoá** `notary_v2/tests/test_docs_structure.py` — thuần kiểm bố cục/tài liệu/SOT pin (README module phải tồn tại, `docs/` không được tồn tại, link Markdown phải tracked, `**Trạng thái:**` phải có). File này đỏ sẵn ở baseline vì 2 README phụ và dòng trạng thái không còn; theo chỉ đạo "xoá, không repin" nên gỡ hẳn, không sửa tài liệu để chiều test.
- **Gỡ coupling tài liệu** trong `notary_v2/tests/test_administrative_timeline.py`: hai test từng đọc `_bmad-output/specs/notary_v2/administrative-timeline.md` (file đã bị gỡ) để lấy ví dụ JSON. Thay bằng fixture tất định trong file (`demo_owner_patch()` dựng từ helper sẵn có `fixture()/unit()/name()`), giữ **nguyên** phần kiểm hành vi thật: `manual_update` + `query` (2007-01-01 → "B"), CLI thật (`update`, biên ngày 2004-12-31 → "A" / 2005-01-01 → "B", `invalid date` rc 2, `stored ledger missing` rc 2, `requires base_revision` rc 2, không Traceback). Test 1 đổi tên `test_spec_json_patch_is_valid_and_cli_query_semantics` → `test_manual_patch_update_and_query_semantics` cho đúng nội dung. Không xoá test hành vi nào khác (77 test còn lại giữ nguyên).
- **Targeted runs sau dọn:** `pytest tests/test_administrative_timeline.py -q` → **79 passed**; riêng hai test cũ → **2 passed**; `pytest tests --collect-only -q` → **1113 tests collected** (không còn file đã xoá). Không đụng `test_document_conversion_poc` (ngoài phạm vi).

### Dọn cô lập fixture test OCR (việc riêng, ngoài phạm vi #6)

- `notary_v2/tests/test_ocr_ai.py::…test_stale_legacy_openai_env_does_not_configure_cloud_ocr` — fixture patch sai namespace: test patch `ocr_ai._read_env` (chỉ là re-export), nhưng `_get_api_key`/`_get_model` resolve `_read_env` trong globals của module định nghĩa `ocr_pipeline`, nên vẫn đọc dotenv thật → `configured` True. Sửa **một dòng**: patch `ocr_ai._ocr_pipeline._read_env` (module định nghĩa, alias đã import sẵn ở `routers/ocr_ai.py:22`), giữ nguyên assertion hành vi (env OpenAI cũ KHÔNG bật provider hiện tại). Không đổi runtime sản phẩm, không đọc giá trị env mới, không framework test mới, không xoá hành vi consumer.
- **Targeted runs:** test cụ thể → **1 passed**; cả file `tests/test_ocr_ai.py` → **44 passed**.

## Design Notes

- **Vì sao snapshot-first, không phải master:** master `customers.ngay_sinh` là cột `Date` (`models.py:43`) — không biểu diễn được “chỉ năm”; `_upsert_people:2410-2413` ghi năm riêng thành `date(y,1,1)` (giới hạn biểu diễn của danh bạ dùng chung, không phải quyền làm mất precision của hồ sơ). Master là danh bạ chia sẻ giữa nhiều hồ sơ nên không phải bằng chứng của một hồ sơ (MIN-141 đã chốt hướng này cho trường suy ra/tài sản/Word). Không thêm cột = không schema/migration; precision của hồ sơ nằm trong `case_state_json` — đúng nguồn owner `entities.md` §8.1 yêu cầu “kiểm riêng khi triển khai”.
- **Vì sao ngày cũ ghi nhận là đầy đủ:** `date(2010,1,1)` từ master không phân biệt được “chỉ năm” với “01/01 thật”; tái tạo là đoán — owner đã cấm; render đầy đủ là trạng thái bảo toàn nhất và không hạ dữ kiện đã biết xuống mức thấp hơn.
- **Đường case không dùng heuristic 1/1:** `date` chỉ đến từ fallback master (hồ sơ cũ thiếu key) → render `dd/mm/yyyy`; chuỗi snapshot luôn mang độ đầy đủ (`YYYY`/`YYYY-MM-DD`) và được render theo đúng độ đầy đủ đó. Vì vậy không còn nhánh nào biến `01/01` thành chỉ-năm trên đường case (web cũ giữ bản riêng, ngoài consumer này).
- Token `[Năm sinh N]`/`[Năm chết N]` tiếp tục chỉ in năm cho cả hai loại — đúng catalog `word_templates/placeholder_mapping.md:46-49,207`.

## Verification

**Commands** (từ `D:/systemdocs/notary_v2`, `.venv` trong repo):
- `venv/Scripts/python.exe -m pytest tests/test_case_workspace.py tests/test_case_metadata.py tests/test_snapshot_person_review.py -q` — round-trip + snapshot regressions đạt.
- `venv/Scripts/python.exe -m pytest tests/test_word_engine.py tests/test_word_batch_export.py -q` — mapping/export docx đạt.
- `venv/Scripts/python.exe -m pytest tests/test_document_intake.py tests/test_docx_word_first.py -q` — guard intake đạt.
- `node --test shell/test/notary-case-drafting-view.test.mjs shell/test/notary-case-drafting-model.test.mjs` — UI date field giữ `YYYY` (không đổi surface).

**Manual checks:** introspect DOCX xuất ra từ test như `python-docx` paragraphs (đã có trong test); diff chỉ chạm các file trong Code Map; probe tạm xóa sau khi lưu log.

**Đã chạy trong phiên (evidence):**
- `pytest notary_v2/tests/test_case_workspace.py … test_customers_excel.py -q` (12 file liên quan) — 612 passed, 2 skipped (`03-focused-regression.log`).
- `pytest notary_v2/tests` (cwd `notary_v2/`, `PYTHONPATH=D:/systemdocs`, basetemp riêng, chạy một mình) — **1110 passed, 3 skipped, 6 failed** (`07-full-suite-clean.log`). Cả 6 lỗi thuộc trạng thái có sẵn của repo/môi trường, đã đối chứng:
  - 2 × `test_administrative_timeline.py` — đỏ vì đọc spec Markdown đã bị gỡ; **đã xử lý ở mục “Dọn test pin lỗi thời”** (decouple, giữ hành vi CLI/algorithm) → file 79 passed.
  - 2 × `test_docs_structure.py` — README module + dòng `**Trạng thái:**` không có ở baseline; **file đã bị xoá** theo chỉ đạo (pin SOT lỗi thời) → không còn trong bộ.
  - 1 × `test_ocr_ai.py::…stale_legacy_openai_env…` — fixture patch sai namespace (patch re-export thay vì module định nghĩa); **đã xử lý ở mục “Dọn cô lập fixture test OCR”** → file 44 passed. Không đổi runtime.
  - 1 × `test_document_conversion_poc.py::…byte_repeatable` — chỉ import `tools.document_conversion_poc`, **đạt khi chạy một mình** (flaky theo tải); ngoài phạm vi, không sửa.
  Không chạy lại full suite sau khi dọn (theo chỉ đạo chỉ chạy targeted); parent chạy full suite cuối cùng.
- `pytest tests/test_naia12_e2e_migrate_export.py` (chạy một mình) — 102 passed (lỗi ở lần full-suite đầu là do tranh basetemp khi chạy song song).
- `node --test shell/test/notary-case-drafting-view.test.mjs shell/test/notary-case-drafting-model.test.mjs shell/test/notary-wire-payload-schema.test.mjs` — 166/166 đạt (UI không đổi mã).

## Plan Change Log

- 2026-10-16 (trước code, theo soát representation của parent): Frozen block trước đó tự mâu thuẫn — “fallback master = ngày đầy đủ” nhưng Design Notes lại giữ heuristic Jan-1→năm cho `date`. Sửa: `date` master render đầy đủ trên toàn đường case; heuristic chỉ còn ở web cũ; bổ sung hàng ma trận key `null` chặn fallback + consumer `save_diagram`; yêu cầu regression phủ cả 3 field ngày. Tránh trạng thái xấu: đọc hồ sơ cũ mà ngày `01/01` bị âm thầm hạ xuống chỉ-năm, và bỏ sót đường `diagram_save` ghi lại snapshot.

## Review Triage Log

- 2026-10-16 — Ghi nhận tại thời điểm implementation trước khi reviewer độc lập phản hồi: coordinator giữ Quick review; plan `built` và chờ review trước commit. Trạng thái này được cập nhật bởi xác nhận cuối tại mục dưới.

- 2026-10-16 — Parent-confirmed independent Quick review: the Q1 medium-risk `word_engine.py` fallback patch is fixed and clean on recheck. The unrelated OCR fixture cleanup received a separate clean review. Latest full Notary suite: 1,111 passed, 2 skipped, 0 failed (115 warnings); real DOCX fallback paragraphs were read. No outstanding business decision; implementation is built.

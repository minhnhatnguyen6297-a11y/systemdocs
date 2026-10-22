---
title: 'Regex giữ serial nguyên văn và địa chỉ thửa có nhãn vào gợi ý intake'
type: 'bugfix'
ticket: 7
created: '2026-10-16'
status: 'built'
baseline_revision: '1ab1f046400fea9168ce603f05e796c0b53350d7'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: ['{project-root}/_bmad-output/decisions/regex-decision-46.md', '{project-root}/_bmad-output/specs/shared/extraction-rules.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Fixture tổng hợp `synthetic-transfer.docx` chạy qua core (`run(source.text, load_profile('transfer'))`) và qua intake Notary thật đã ghi hai Người + một Tài sản nhưng `so_serial` nguồn `TEST-001` và `dia_chi_thua` nhãn `Địa chỉ thửa đất:` đều `missing`; gợi ý tài sản thiếu hai trường kèm `intake.fragment`. Bằng chứng `_bmad-output/tmp/notary-flow-remediation/runtime-synthetic/{core-result,intake-result}.json`; không chạy lại chỉ để xác nhận lỗi.

**Approach:** Sửa đúng profile `transfer.json` mà intake nạp: `asset.so_serial` bắt **raw serial theo nhãn hiện hành**, cắt tại biên field/dòng đang dùng (không quota định dạng, không chuỗi con `do` tùy ý); `asset.dia_chi_thua` thêm đúng nhãn `Địa chỉ thửa đất` bên cạnh nhánh `có địa chỉ tại` cũ. Validator chuẩn serial giữ nguyên: lệch chuẩn → `warning_nonstandard`, giữ raw, không tự nâng cấp. Test workbench cho biên + test service thật (DOCX qua `analyze`) + replay fixture chứng minh value/span/raw và không mượn dữ liệu.

## Boundaries & Constraints

**Always:** Giữ `rule_id`/`name`/`zone`/`expect` và alias hiện hành (`asset.so_serial`, `asset.dia_chi_thua`, `dia_chi_thua→dia_chi`); `span`/`raw_snippet` trỏ văn bản nguồn gốc; decision-46: serial nguyên văn mọi định dạng, trống/trùng hợp lệ, không chuẩn hóa; thiếu vẫn `missing`, không mượn người/field kế/Lời chứng; giữ `asset_groups`/`land_rows`; bump version profile + đồng bộ docs có nhắc version.

**Never:** Không sửa `engine/extractor.py|zoner.py|runner.py`, `adapters/docx.py`, `service.py`, `normalization.py`; không chạm `upload_lab/extract_contract.py`, `regex-test-tool/`, `shell/`, UI; không OCR fallback/schema/retry; không nới nhãn ngoài phạm vi báo cáo; không mở Pending F04/F05; không commit trong phiên này.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| HAPPY | `Giấy chứng nhận số: TEST-001;` + `Địa chỉ thửa đất: xã Mẫu, tỉnh Mẫu;` | serial raw `TEST-001` (state `warning_nonstandard`, giữ raw); địa chỉ `matched` `xã Mẫu, tỉnh Mẫu`; gợi ý tài sản đủ 2 field, hết `intake.fragment` | không lỗi |
| RAW không quota | `123456789`, `TEST/001-A`, `SERIES-123456`, `ENDDO123`, `DO 123456` | giữ nguyên chuỗi nguồn, không cắt cụt; vẫn `warning_nonstandard` | không lỗi |
| BIÊN `do` | `AB 123456 do Sở … cấp ngày …` | value `AB 123456` (không nuốt `do …`); `TEST-001 do …` cũng dừng trước ` do ` | không lỗi |
| BIÊN dòng/`;` | serial cuối dòng hoặc trước `; Thửa đất số` | dừng đúng, không sang field kế | không lỗi |
| TRỐNG | `Giấy chứng nhận số:` không giá trị (kể cả trước `;`/dòng mới) | `so_serial` `missing`, không mượn `Thửa đất số` | không lỗi |
| ĐỊA CHỈ cũ | `có địa chỉ tại: Nhà A` | giữ nguyên hành vi (matched `Nhà A`) | không lỗi |
| NHÃN mới ngoài phạm vi | `Địa chỉ: Thôn A` | `dia_chi_thua` vẫn `missing` | không lỗi |

</frozen-after-approval>

## Code Map

- `tools/regex_workbench/engine/profiles/transfer.json:276-289` (`asset.so_serial`) — điểm sửa 1: value group raw + biên; validator `^[A-Z]{2}\s*\.?\s*\d{6,8}$` + `warning_nonstandard` giữ nguyên; `:3` version 1.1.3; `:243-249` (`asset.dia_chi_thua`) — điểm sửa 2 thêm nhánh nhãn.
- `tools/regex_workbench/engine/extractor.py` (`extract_fields` group span→raw, `_apply_validators`) — chỉ dùng lại, không đổi.
- `notary_v2/services/document_intake/adapters/docx.py:16-17,36-132` — alias `dia_chi_thua→dia_chi`, refs `profile_id/profile_version/rule_id`, `warning_nonstandard→observed+normalized null`, `required=("so_serial","dia_chi")`; chỉ đọc.
- `notary_v2/services/document_intake/normalization.py` (`norm_serial`) — chỉ đọc: `TEST-001` → `normalized null`, `observed` (không nâng cấp).
- `notary_v2/services/document_intake/service.py` (`analyze`) — entry consumer thật cho test smoke.
- `tools/regex_workbench/tests/test_workbench.py` + `tests/fixtures/transfer_serial_va_dia_chi_thua.txt` (mới, dữ liệu giả lập “Mẫu”) — test engine; `notary_v2/tests/test_document_intake.py` (`DocxAdapterTests`, `_make_docx`, `_file_source`) — test service thật.
- `_bmad-output/tmp/notary-flow-remediation/runtime-synthetic/` — bằng chứng trước sửa (giữ nguyên); replay sau sửa ghi file mới cùng thư mục.
- Docs đồng bộ version: `tools/regex_workbench/README.md:5`, `_bmad-output/specs/notary_v2/word-templates.md:53-57`.
- Không đụng: `upload_lab/extract_contract.py`, `regex-test-tool/tool/`, `shell/`, `notary_v2/services/case_workspace.py` (layer canonical serial riêng), `.agent/`, `docs/`.

## Tasks & Acceptance

**Execution:**
- [x] `tools/regex_workbench/engine/profiles/transfer.json` — `asset.so_serial`: nhãn `so phat hanh` nhận annotation trong ngoặc `(serial\|seri)` như một phần nhãn; value raw `([a-z0-9][^,;|)\n:]*?)` không quota chữ/số, gap `[ \t]*` (không cắt qua dòng), biên `(?=[,;|)]|[ \t]*$|\.(?=[ \t]|$)|[ \t]+do(?:[ \t]|$))`; connector `[^a-z0-9,;\n|]{0,12}` chặn `;`/dòng mới; `asset.dia_chi_thua` thêm nhánh literal `dia\s*chi\s*thua\s*dat`; version 1.1.3 — nguồn gợi ý intake dùng chính profile này.
- [x] `tools/regex_workbench/tests/fixtures/transfer_serial_va_dia_chi_thua.txt` + `test_workbench.py` — test đỏ trước (chỉ regression mới), rồi xanh: raw mọi định dạng, biên ` do `/dòng/`;`, trống không mượn, nhãn địa chỉ mới, nhãn trần không khớp.
- [x] `notary_v2/tests/test_document_intake.py` — test DOCX qua `analyze` thật: serial raw `TEST-001` + địa chỉ + span/raw refs + hết fragment + không có người Lời chứng.
- [x] Replay smoke trên `runtime-synthetic/synthetic-transfer.docx` (core + `analyze_async`) — ghi log mới, không đè bằng chứng cũ.
- [x] Docs sync version 1.1.3 + mô tả ngắn; dọn script tạm sau khi lưu log.

**Acceptance Criteria:**
- Given fixture chuyển nhượng tổng hợp chạy qua intake Notary thật, when xem gợi ý tài sản, then `so_serial` raw `TEST-001` (normalized null, observed, warning nonstandard) + `dia_chi` `xã Mẫu, tỉnh Mẫu`, span/raw_snippet đúng nguồn, không còn `intake.fragment`.
- Given serial nguồn bất kỳ (TEST-001, 123456789, TEST/001-A, ENDDO123, DO 123456), when trích, then giữ nguyên chuỗi nguồn, không cắt theo quota hay chuỗi con `do`; warning chỉ khi lệch chuẩn hiện hành.
- Given serial trống (kể cả trước dòng mới/`;`), when trích, then `missing`; không mượn field kế/người/Lời chứng.
- Given fixture cũ (AB 123456, M 012345, DD 123456, ZZ123456), when chạy suite liên quan, then hành vi giữ nguyên.
- Given nhãn `Địa chỉ thửa đất:`, when trích, then `dia_chi_thua` matched đúng giá trị; `có địa chỉ tại` giữ nguyên; nhãn `Địa chỉ:` trần không khớp.

## Verification

**Commands** (từ `D:/systemdocs`):
- `notary_v2\venv\Scripts\python.exe -m pytest tools\regex_workbench\tests -q` — engine/profile đạt, gồm test mới.
- `cd notary_v2` + `venv\Scripts\python.exe -m pytest tests/test_document_intake.py tests/test_docx_word_first.py -q` — service thật + regression DOCX đạt.
- Replay §8 assessment-plan trên fixture thật (ghi JSON bằng chứng mới) — core trả serial/địa chỉ, intake hết fragment.

**Manual checks:** đối chiếu `runtime-synthetic` cũ vs log mới; `git diff` chỉ chạm Code Map.

**Đã chạy trong phiên (evidence — `_bmad-output/tmp/issue-7-regex-serial-dia-chi-thua/`, gitignore):**
- `01-red-before.log` — chỉ regression mới, đỏ đúng hành vi cũ: workbench `missing`/`None != TEST-001`; intake `KeyError: 'so_serial'`. Không chạy lại để xác nhận lỗi người dùng báo.
- `02-green-focused.log` — sau sửa: workbench `5 passed, 10 subtests passed`; intake `1 passed`.
- `03-regression*.log` + `04-verification.log` — vòng đầy đủ cuối: `tools/regex_workbench/tests` **43 passed, 10 subtests passed**; `notary_v2/tests/test_document_intake.py tests/test_docx_word_first.py` **107 passed** (basetemp riêng). Ghi chú: lần chạy giữa vòng bắt được hồi quy `test_docx_property` do nhánh nhãn `(serial)`; đã sửa pattern (digit-anchor) trước khi chạy lại.
- `05-smoke-after.{log,json}` — replay bản pattern trước rework (digit-anchor): PASS cùng kết quả dương tính; giữ lịch sử, **đã bị thay** bởi `07-*` sau rework.
- `06-rework-verification.log` — sau rework: focused `6 passed, 12 subtests passed`; workbench đầy đủ `44 passed, 12 subtests passed`; notary `test_document_intake.py` + `test_docx_word_first.py` **107 passed** (basetemp riêng).
- `07-smoke-after-rework.{log,json}` — replay service thật + core: dương tính (TEST-001 + địa chỉ, hết fragment, không người Lời chứng); raw không quota giữ nguyên (`SERIALONLY`, `ABC/RAW`, `TEST/001-A`, `123456789` → `warning_nonstandard`); annotation `Số phát hành (serial):` → `TEST-001`; biên trống qua service (DOCX mới cùng cấu trúc): không có `so_serial`, không mượn `Thửa đất số`/`Tờ bản đồ số`, warning `intake.fragment` giữ. Script replay tạm đã xoá sau khi lưu log.
- `09-smoke-after-review.{log,json}` — replay sau fix review: tiền tố `-TEST-001`/`/TEST-001` giữ raw + span khớp; blank serial + blank address qua service thật → `missing` cả hai, không có `so_serial`/`dia_chi`, không mượn `Thửa đất số`/`Loại đất`, warning `intake.fragment`; positive + annotation giữ nguyên.
- `08-review-fix-verification.log` — sau fix review: workbench `45 passed, 16 subtests passed`; notary `test_document_intake.py` + `test_docx_word_first.py` **108 passed** (basetemp riêng).
- `10-recheck-fix-verification.log` — sau fix recheck 2: workbench `45 passed, 18 subtests passed`; notary targeted `108 passed, 49 warnings, 2 subtests passed` (basetemp riêng).
- `11-smoke-after-recheck.{log,json}` — replay sau fix recheck 2: `(serial) TEST-001` sau nhãn GCN giữ raw + span khớp; annotation `Số phát hành (serial):` → `TEST-001`; blank serial + địa chỉ (dòng mới VÀ cùng dòng `Loại đất:`) qua service thật → `missing`, không mượn, `intake.fragment`; positive giữ nguyên.
- `plan.html`/`plan.packed.html` — exhibit-first cho plan; pack sạch (0 warning), Chromium kiểm: 6 claim (5 + scope), 0 error box, doc-calls nở excerpt, viewport 390px không tràn ngang. Không có UI đổi nên không có mock/screenshot sản phẩm.

## Implementation Notes

- Route `full` (auto): thay đổi nằm trên shared profile mà intake thật tiêu thụ; cần test biên + smoke service thật để chứng minh hành vi, không chỉ một test đơn vị.
- Waiver: `_bmad-output/decisions/decision-bmad-all-active-loose-issues-no-autoresearch.md` (owner 16/10: “trien khai lien tuc, khong can duyet plan, chi dung lai khi can hoi”) + `decision-clear-intent-no-plan-approval.md` — không dừng xin duyệt plan; vẫn giữ verification và review Quick độc lập (parent chạy review sau).
- Baseline `1ab1f046400fea9168ce603f05e796c0b53350d7`; bug đã có bằng chứng service/core, không chạy lại lỗi để xác nhận.

### Thực thi (append-only)

- **Profile `transfer.json` 1.1.3 (final):** `asset.so_serial` giá trị raw không quota chữ/số: letter-only (`SERIALONLY`, `ABC/RAW`), số thuần (`123456789`), tiền tố `-`/`/`, `(serial) TEST-001`, `TEST/001-A`, `TEST-001`, `AB 123456` đều giữ nguyên chuỗi; nhãn hiện hành (annotation `(serial|seri)` chỉ trong nhánh `so phat hanh`) + guard nhãn kế + separator `[ \t]*[:.]?[ \t]*` (không nhảy `;`/dòng mới — trống vẫn `missing`); biên `(?=[,;|]|[ \t]*$|\.(?=[ \t]|$)|[ \t]+do(?:[ \t]|$))` dừng ở dấu/dòng/` do ` có whitespace, không cắt qua dòng. Validator `^[A-Z]{2}\s*\.?\s*\d{6,8}$` giữ nguyên — lệch chuẩn chỉ `warning_nonstandard` + giữ raw.
- **Rework theo chỉ đạo parent (thay bản digit-anchor trước đó):** bản đầu thêm `\d` bắt buộc và bỏ letter-only — trái decision-46 (serial nguyên văn mọi định dạng). Bỏ digit-anchor; nguyên nhân gốc của `test_docx_property` đỏ là **biên nhãn**: `Số phát hành (serial):` phải được đọc như MỘT nhãn (annotation `(serial|seri)` tùy chọn thuộc nhánh `so phat hanh`) thay vì nuốt chữ "serial" làm giá trị. Không thêm hạn chế định dạng nào cho value.
- **`asset.dia_chi_thua`:** thêm đúng nhánh literal `dia\s*chi\s*thua\s*dat`; nhánh cũ `co\s*dia\s*chi\s*tai` và class capture `[^\n;.]+` giữ nguyên; `Địa chỉ:` trần vẫn không khớp.
- **Tests:** fixture giả lập `transfer_serial_va_dia_chi_thua.txt` (tên "Mẫu"); 6 test workbench (raw/chuẩn gồm letter-only `SERIALONLY`/`ABC/RAW`, annotation `Số phát hành (serial):`, biên ` do `/EOL, trống, nhãn địa chỉ, nhãn trần) + 1 test service thật trong `DocxAdapterTests` (span→`read_docx(text)`, refs `rule_id/profile_id`, không `intake.fragment`, không người Lời chứng).
- **Docs:** `tools/regex_workbench/README.md` + `_bmad-output/specs/notary_v2/word-templates.md` cập nhật 1.1.3 + mô tả serial raw/`Địa chỉ thửa đất`.
- **Giới hạn:** annotation trong ngoặc khác `(serial)/(seri)` tại vị trí nhãn `Số phát hành` chưa được mô hình; ngoặc nằm trong raw value được giữ tới biên field thật (`(serial) TEST-001`); `:` không nằm trong value và không là biên (chặn mượn nhãn kế khi thiếu dấu phân cách).
- **Matrix audit note (RAW không quota):** hàng liệt kê `DO 123456` chung nhóm nonstandard, nhưng giá trị này **thỏa chuẩn hiện hành** (`^[A-Z]{2}\s*\.?\s*\d{6,8}$`) nên test giữ `state=matched` — đổi thành `warning_nonstandard` sẽ là bịa lỗi chuẩn và phá validator đã chốt. Hành vi cốt lõi của hàng (giữ nguyên chuỗi, không cắt cụt/không cắt chuỗi con `do`) vẫn được kiểm cho cả 7 ví dụ; các ví dụ nonstandard thật (`123456789`, `TEST/001-A`, `SERIES-123456`, `ENDDO123`) assert đúng `warning_nonstandard`. Frozen block giữ nguyên.
- **Fix theo review (Q1/Q2 + recheck 2):** bỏ connector generic; `asset.so_serial` = nhãn (nhánh `so phat hanh` nhận annotation `(serial|seri)`) + guard âm `(?![:. \t]*(?:nhãn asset hiện có: loai dat, thua dat/so, to ban do/so, dien tich, thoi han, so vao so, cap ngay/ngay cap, so phat hanh/serial/seri/ma phoi/so phoi, gcn so, giay chung nhan))` + separator `[ \t]*[:.]?[ \t]*` + value raw `[^ \t\n;|,:][^\n;|,:]*?` + biên `(?=[,;|]|[ \t]*$|\.(?=[ \t]|$)|[ \t]+do(?:[ \t]|$))`; `asset.dia_chi_thua` cùng guard + separator + `([^ \t\n;.:][^\n;.]*)`. Hệ quả: giữ raw tiền tố `-`/`/` và `(serial) TEST-001` sau nhãn khác (annotation chỉ thuộc `Số phát hành`, không bị strip); nhãn trống (dòng mới/`;`/nhãn kế cùng dòng `Loại đất:`) → `missing`, không trả giá trị nhãn kế. Test mới: workbench blank địa chỉ 3 biến thể + tiền tố/`(serial)` serial (span), intake blank 2 biến thể (dòng mới/cùng dòng).
- **Dọn dẹp:** script replay tạm đã xoá; giữ log/JSON bằng chứng trong `_bmad-output/tmp/issue-7-regex-serial-dia-chi-thua/` (thư mục `_bmad-output/tmp/` bị gitignore).

- **Final verification:** Independent Quick review CLEAN (0 findings after two patch rounds); workbench full suite **45 passed, 18 subtests passed**. The final full Notary run using the short, isolated `D:\systemdocs\.tmp\p7final` basetemp passed: **1113 passed, 2 skipped, 115 warnings, 2 subtests passed**. The initial full run using the long issue-local basetemp reported 11 `WinError 3` template-publication failures (`os.link`), alongside 1102 passed, 2 skipped, and 2 subtests; one full short-path rerun passed with no source/test changes. Smoke `11-smoke-after-recheck.{log,json}` PASS. Exact commands/results are preserved in the ignored `_bmad-output/tmp/issue-7-regex-serial-dia-chi-thua/final-verification.md`.

## Design Notes

- Serial: nhãn hiện hành + annotation `(serial|seri)` là phần nhãn của `so phat hanh`; value raw `([a-z0-9][^,;|)\n:]*?)` không quota chữ/số (letter-only/numeric/`/`/`-`/`.` giữ nguyên), gap `[ \t]*`, biên `(?=[,;|)]|[ \t]*$|\.(?=[ \t]|$)|[ \t]+do(?:[ \t]|$))` — dừng ở dấu/dòng/`)`/` do ` (whitespace hai bên, theo quy ước `person.noi_cap` tách `do <cơ quan> cấp`); không cắt chuỗi con `do` (`ENDDO123`, `DO 123456`). Lazy + lookahead giữ `raw_snippet` sạch, không cắt qua dòng.
- Serial blank/newline: connector `[^a-z0-9,;\n|]{0,12}` không nhảy qua `;`/dòng mới nên không nuốt nhãn kế.
- Địa chỉ: giữ `[^\n;.]+` cũ, chỉ thêm đúng nhãn báo cáo; `Địa chỉ:` trần và nhãn người giữ nguyên ngoài phạm vi.

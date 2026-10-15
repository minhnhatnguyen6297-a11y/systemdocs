---
title: 'Sửa binding thông báo lỗi Sơ đồ (relErrText → errText)'
type: 'bugfix'
ticket: '4'
created: '2026-10-16'
status: 'built'
baseline_revision: '40e59f02b1b5ac9bab1ef461c94dc803d289face'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: ['{project-root}/_bmad-output/specs/notary_v2/diagram-rules.md', '{project-root}/_bmad-output/backlog/bug-diagram-error-messages.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `shell/src/renderer/notary/relationship-diagram.js:47-49` đọc `window.G1_NOTARY_ERRORS.relErrText`, nhưng catalog thật chỉ export `errText` (`error-catalog.js:256`). Khi Electron nạp catalog trước sơ đồ (`index.html:25-28`), ba nơi gọi — `:312` evaluate, `:1278` dựng danh sách lỗi, `:1333` lưu — ném `TypeError: relErrText is not a function` thay cho thông báo lỗi. Test hiện xanh vì nạp tách file nên rơi vào nhánh dự phòng.

**Approach:** Đổi duy nhất phép đọc binding sang `.errText`; giữ tên biến ngoài cùng `relErrText`, ba nơi gọi và nhánh dự phòng nguyên trạng. Thêm **một** test hồi quy hành vi theo convention test hiện có, nạp catalog thật trước sơ đồ theo đúng thứ tự `index.html`; các hàng còn lại phủ bằng harness tạm chạy Electron thật, không thêm wiring hay hook sản phẩm.

## Boundaries & Constraints

**Always:** Giữ dữ liệu người dùng đang nhập và state/nháp khi evaluate hoặc save trả lỗi; giữ nhánh riêng `diagram_invalid_state` (hiện lỗi dưới sơ đồ, không toast riêng) và `workspace_conflict` (luồng xung đột hiện có); giữ hành vi đã chốt ở `diagram-rules.md` §9.7 — `invalid` chặn lưu, `incomplete` cho lưu kèm `requiredSlots`/warning, engine lỗi không xóa state cũ; mọi dữ liệu thử là giả, dùng thư mục riêng.

**Never:** Không đổi tên biến ngoài cùng thành `errText` (trùng top-level `const errText` ở `case-drafting-view.js:221` → script sau không load); không thêm export `.relErrText`; không thêm guard/cơ chế báo lỗi mới, không catch rỗng che lỗi, không test hook trong sản phẩm; không đổi engine, schema, Stage/Pool, bố cục sơ đồ; không đóng 12 report thiếu mô tả ở `implementation-artifacts/diagram-error-fix-20261009/open-reports.md`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Đánh giá lỗi | evaluate trả `stage_validation_error` | toast bằng `errText(error)`, model hết busy | không TypeError; `notify` gọi 1 lần, cờ lỗi `true` |
| Tự đánh giá sau thao tác | cùng lỗi, chạy sau debounce 500 ms | có toast như trên | không `unhandledrejection` |
| Dựng danh sách lỗi | model trả `diagram_invalid_state` + `details.errors` | lỗi hiện dưới sơ đồ; card sơ đồ và Stage còn hiện | không toast riêng |
| Lưu lỗi thường | save trả `workspace_locked` sau khi bấm | toast đúng catalog; nháp/dirty còn, revision không tăng | không ghi DB thành công giả |
| Lưu xung đột | save trả `workspace_conflict` | luồng xung đột hiện có; không toast riêng | không ghi đè |
| Thành công | evaluate/save `ok:true`; lưu rồi mở lại | không toast lỗi; revision tăng một lần; lựa chọn đã lưu còn nguyên | — |
| Hai bên A/B | `domain:two_party` | không gọi engine thừa kế | — |
| Nạp tách file trong Node | không có `window`/catalog | nhánh dự phòng `` `${code}: ${message}` `` | không ReferenceError |

</frozen-after-approval>

## Code Map

- `shell/src/renderer/notary/relationship-diagram.js:47-49` — chỗ sửa: phép đọc binding; giữ alias `relErrText` và nhánh dự phòng.
- `shell/src/renderer/notary/relationship-diagram.js:312,1278,1333` — ba nơi gọi dùng chung alias (evaluate toast, render `diagramErrors`, save toast); chỉ đọc.
- `shell/src/renderer/notary/error-catalog.js:250-260` — export thật `{ERROR_CATALOG, describeError, errText}`; chỉ đọc.
- `shell/src/renderer/index.html:25-28` — thứ tự nạp catalog trước sơ đồ; điều kiện tái hiện defect.
- `shell/src/renderer/notary/case-drafting-view.js:217-223` — mẫu binding đúng (`errCatalog.errText`), đồng thời khai báo top-level `const errText`; chỉ đọc.
- `shell/src/renderer/notary/case-drafting-model.js:451-469` (`emit` nuốt lỗi subscriber), `:1334-1423` (giữ state khi lỗi); chỉ đọc.
- `shell/test/notary-case-drafting-static.test.mjs` (MIN-136) — chặn trùng top-level identifier và sai thứ tự script.
- `shell/test/notary-diagram.test.mjs:88-95` — cách test hiện tại dựng `window` (không kèm `G1_NOTARY_ERRORS`); dùng làm mẫu cấu trúc cho test mới cùng `shell/test/dom-stub.mjs`.

## Tasks & Acceptance

**Execution:**
- [x] `shell/test/notary-diagram-errors.test.mjs` — thêm một test hồi quy hành vi deterministic: nạp `error-catalog.js` thật rồi `relationship-diagram.js` theo thứ tự `index.html`, dựng model/pane thật với client giả trả lỗi, kiểm thông báo ở evaluate, ở danh sách `diagramErrors` và ở lưu; chạy trên source hiện tại phải đỏ đúng `relErrText is not a function` (bằng chứng trước khi sửa) — chặn tái phát đúng nhánh browser, không phải kiểm tra export/source/wiring.
- [x] `shell/src/renderer/notary/relationship-diagram.js` — đổi duy nhất `window.G1_NOTARY_ERRORS.relErrText` thành `.errText`; giữ nguyên tên biến, ba nơi gọi, nhánh dự phòng — cả ba nhánh lỗi dùng chung một alias.
- [x] Harness tạm `_bmad-output/tmp/diagram-error-messages-20261016/probe.cjs` — chạy `shell/node_modules/electron/dist/electron.exe` mở `shell/src/renderer/index.html` thật, dựng pane thật (`window.G1_NOTARY_DIAGRAM.createDiagramPane`) với model thật + client giả, bấm nút thật từ DOM, ghi `notify`/DOM/`pageerror`/`unhandledrejection`, lưu JSON + ảnh trong thư mục riêng; **xóa harness và thư mục tạm ngay sau khi lấy đủ bằng chứng**.
- [x] `npm test` — hồi quy toàn bộ suite shell.

**Acceptance Criteria:**
- Given evaluate trả `stage_validation_error`, when bấm "Xem cách tính", then toast bằng `G1_NOTARY_ERRORS.errText(error)` và không có pageerror/TypeError.
- Given model trả `diagram_invalid_state` kèm `details.errors`, when view dựng lại, then lỗi hiện dưới sơ đồ cùng card sơ đồ/Stage, không toast riêng.
- Given save trả `workspace_locked`, when bấm "Lưu sơ đồ", then toast đúng catalog và nháp/revision giữ nguyên như trước khi bấm.
- Given save trả `workspace_conflict`, when bấm lưu, then luồng xung đột hiện có chạy, không toast riêng, không ghi đè.
- Given evaluate/save `ok:true`, when lưu rồi mở lại, then không toast lỗi, revision tăng đúng một lần, lựa chọn đã lưu còn nguyên.
- Given test mới chạy trên source chưa sửa, when gọi ba nhánh lỗi, then nó đỏ đúng `relErrText is not a function`; sau khi sửa, cùng test cùng kỳ vọng đạt.
- Given thay đổi đã áp dụng, when soát diff, then chỉ dòng binding đổi cùng đúng một file test hành vi mới; không export/alias/guard mới.

## Implementation Notes

- Route `full` (auto): rủi ro trung bình — defect nằm ở binding toàn cục trong browser thật, cùng một alias phục vụ ba nhánh lỗi, và harness smoke lịch sử không còn nên cách kiểm chứng phải chốt trong plan.
- Lập plan 16/10/2026; build bắt đầu ngay sau đó trong cùng phiên. Baseline `40e59f02b1b5ac9bab1ef461c94dc803d289face`; status `ready-for-dev` → `in-progress` → `built` sau khi hoàn tất implementation, kiểm chứng và Quick review.
- Bằng chứng defect gốc đã có, không chạy lại chỉ để xác nhận: `_bmad-output/implementation-artifacts/diagram-error-fix-20261009/review-evidence.json` (stack tại 312/1278/1333) và `.../acceptance.md` (ca C01–C12).

### Thực thi (append-only)

- **Sửa nguồn:** `shell/src/renderer/notary/relationship-diagram.js:48` — `window.G1_NOTARY_ERRORS.relErrText` → `.errText`. Không đổi tên alias, ba nơi gọi, nhánh dự phòng, không thêm export/guard.
- **Test mới:** `shell/test/notary-diagram-errors.test.mjs` — 7 ca, nạp `error-catalog.js` thật trước `relationship-diagram.js` theo thứ tự `index.html` (`delete require.cache` để binding được đọc lại đúng như browser), dựng model/view thật + client giả.
- **Bằng chứng (giữ trong `_bmad-output/tmp/diagram-error-messages-20261016/`):** `01/02-red-before-fix*.log` (test đỏ trước sửa), `04-red-final-test-unfixed-source.log` (đỏ đúng `TypeError` tại 312 ×2, 1278, 1333 sau khi tạm hoàn nguyên dòng binding), `05-green-final.log` (7/7 đạt), `06-focused-regression.log` (217/217), `07-full-npm-test.log` (403/404), `probe-evidence.json` + `row0..row7.png` + `08-probe-run.log` + `app-probe.log` (Electron thật), `appdata/` (userData/log của app khi probe).
- **Electron thật (harness tạm, đã xóa code sau khi lưu bằng chứng):** chạy `shell/node_modules/electron/dist/electron.exe . --remote-debugging-port=9333 --user-data-dir=<tmp>` từ `shell/` với `G1_DEV_NOTARY_MOCK=1` + thư mục dữ liệu riêng, điều khiển qua CDP (`/json/list` + WebSocket) trong cửa sổ app thật (`index.html` thật, thứ tự script thật: catalog trước sơ đồ; `catalogErrText=function`, `catalogHasRelErrText=false`), dựng pane + module view thật với client giả trong page. `errors: []` cho cả phiên (không pageerror/unhandled rejection).
- **Phát hiện khi làm:**
  - `movePerson` trên slot `owner` gọi `setOwnerRow()` → `touchStage()` → `stageDirty`; `stageGate()` khi đó tắt `Xem cách tính`/`Lưu sơ đồ` và bỏ qua `scheduleEvaluate()`. Test/probe vì vậy sửa diagram qua slot không phải owner (`child_1`, `p16`) để đi đúng đường người dùng.
  - Ở môi trường này sidecar không sẵn sàng nên app hiện toast `engine_unavailable`; các nhánh lỗi được trả bằng client giả trong cửa sổ app thật (đúng cách checklist lịch sử cho phép), không cần engine.
  - `npm test` còn 1 ca đỏ ngoài phạm vi: `notary-docx-intake.test.mjs` gọi `python` hệ thống và thiếu module `jsonschema` — lỗi môi trường có sẵn, không liên quan thay đổi này (không sửa).
  - Plan cũ dùng `rtk proxy node --test …`; rtk đang cài không còn subcommand `proxy` (kiểm bằng `rtk --help`) nên lệnh chạy là `node --test …` / `npm test`.
- **Matrix:** phủ đủ 8 hàng bằng test đã chạy và đạt — hàng 1–5 + 8: test mới (`05-green-final.log`); hàng 6: test mới + `two_party: assign → save → reopen …`; hàng 7: `two_party: assign/drop KHONG goi diagram_evaluate` (`06-focused-regression.log`); probe Electron phủ lại hàng 1–7 trong browser thật.
- **Docs sau smoke:** `_bmad-output/specs/notary_v2/diagram-rules.md` §9.7 thêm ghi chú runtime (thông báo lỗi hiển thị qua formatter `errText`; binding đã khôi phục) và cập nhật ngày; `_bmad-output/specs/product-overview.md` thêm dòng trạng thái #4 (đã sửa + kiểm chứng, chờ review độc lập) và cập nhật ngày. Repo không có CHANGELOG; không tạo doc mới, không đổi quy tắc hành vi, không tạo decision, không nâng Draft.
- **Giới hạn:** probe dùng client giả nên không chạy vòng save/reload qua engine thật; hàng 6 được phủ bằng test và round-trip test có sẵn, không có bằng chứng IPC thật trong phiên này.
- Không tạo HTML plan: thay đổi formatter, không có thiết kế/hình mới (ngoại lệ việc nhỏ của `visual-html-plans.md`).

## Plan Change Log

- 2026-10-16: Ghi trạng thái built sau khi hoàn tất execution và nhận Quick review sạch; không đổi phạm vi.
## Review Triage Log
- 2026-10-16 — Independent Quick review: clean; no findings. Không có finding cần xử lý.

## Design Notes

- Giữ tên `relErrText`: hai script classic dùng chung global lexical scope; `case-drafting-view.js:221` đã có `const errText` nên đổi tên sẽ làm script sau không load (lỗi `module_missing` từng gặp).
- Không export thêm `.relErrText`: export giả che lại chính lệch tên cần bắt.
- Không thêm guard `typeof … === 'function'`: giữ đúng mẫu binding đang dùng ở view, không thêm cơ chế ngoài phạm vi.

## Verification

Chạy từ `shell/`, mỗi lệnh riêng:
- `node --test test/notary-diagram-errors.test.mjs` — trước sửa: đỏ đúng `relErrText is not a function`; sau sửa: đạt.
- `node --test test/notary-diagram.test.mjs test/notary-case-drafting-static.test.mjs test/notary-case-drafting-model.test.mjs test/notary-case-drafting-view.test.mjs` — hồi quy sơ đồ, nhánh dự phòng Node và guard tĩnh.
- `npm test` — bộ Node toàn shell.
- Harness Electron (đã chạy xong và xóa code; bằng chứng `probe-evidence.json` + `row0..row7.png` còn trong `_bmad-output/tmp/diagram-error-messages-20261016/`) — Electron thật, catalog thật theo thứ tự `index.html`; JSON từng hàng của matrix (thông điệp, `notify`, DOM, `pageerror`, unhandled rejection) + ảnh; `errors: []` cho cả phiên.
### Kết quả đóng hồ sơ (2026-10-16)

- `05-green-final.log`: test hồi quy mới — 7/7 đạt.
- `06-focused-regression.log`: hồi quy tập trung — 217/217 đạt.
- Full shell suite: `NOTARY_TEST_PYTHON=../notary_v2/venv/Scripts/python.exe npm test` — 404/404 đạt. Kết quả dùng Python trong repository này supersedes lần chạy mặc định ghi ở `07-full-npm-test.log` (403/404, `ModuleNotFoundError: No module named 'jsonschema'`).
- Probe chạy trong Electron thật trên renderer thật; client stub chỉ cung cấp kết quả command có kiểm soát, nên không xác minh command IPC hay hành vi engine. `probe-evidence.json` báo `errors: []`, `ok: true`; chi tiết và screenshot được liệt kê trong `final-verification.md`.
- Quick review độc lập: clean, no findings.

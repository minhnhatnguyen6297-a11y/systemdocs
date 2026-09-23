# Electron G1 trên một máy — thiết kế điều phối

**Ngày:** 14/09/2026
**Goal gốc:** Linear MIN-56
**Nhánh tích hợp:** `electron-system-shell`
**Trạng thái:** chờ owner duyệt trước khi viết implementation plan hoặc code

## 1. Kết quả cần đạt

Đợt này tạo một bản Electron đóng gói chạy được nghiệp vụ thật trên **một máy
Windows**. Người dùng phải hoàn thành được hai đường đi:

1. `upload_lab`: chọn nguồn → scan/extract → review/edit → audit/queue →
   preflight → điền form ở chế độ dry-run → người dùng tự quyết định Finalize.
2. `notary_v2`: hồ sơ → document intake/OCR → review/confirm →
   Case Workspace/thừa kế → xuất Word.

Electron chỉ sở hữu cửa sổ, điều hướng, hộp chọn file, tải file và vòng đời
helper. Python tiếp tục sở hữu nghiệp vụ, OCR, sinh Word và Playwright.

Đợt này **không chứng minh LAN**. Loopback như `127.0.0.1`, giả lập mất kết nối,
hai process trên cùng máy hoặc test đồng thời trên cùng máy đều không được ghi
thành “LAN đã đạt”.

## 2. Tách goal

### Goal hiện tại — G1-SM: một máy

Bao gồm:

- khóa revision và inventory;
- kiểm tra tương thích Windows trên một máy;
- duyệt Electron core, DesktopCommand, UX chuyển đổi và data contract;
- foundation, shell, Upload/Audit và `notary_v2`;
- đóng gói, smoke test và hai luồng nghiệp vụ thật trên một máy;
- rollback về entrypoint cũ.

### Goal hoãn — G1-LAN: LAN và nhiều máy

Giữ riêng để làm khi có môi trường:

- hai máy trạm thật cùng backend;
- mất LAN/reconnect, version skew và timeout mạng thật;
- ownership job giữa hai máy, concurrent update và conflict;
- auth qua LAN, đường dẫn client/server và share mạng;
- cài/update qua nhiều máy, backup/restore và cutover toàn văn phòng.

MIN-76 thuộc hoàn toàn G1-LAN. Phần LAN trong MIN-75 cũng chuyển sang G1-LAN.
MIN-66 chỉ được đóng sau G1-LAN; G1-SM cần một issue nghiệm thu một máy riêng,
không dùng MIN-66 để tuyên bố cutover toàn hệ thống.

Đây là thay đổi kế hoạch đề xuất. Không đổi trạng thái hoặc nội dung Linear cho
đến khi owner duyệt tài liệu này.

## 3. Bằng chứng hiện có

- Nhánh `electron-system-shell` được phép chứa runtime; không merge runtime
  vào `main` trong G1
  (`AGENTS.md` — phần ngoại lệ nhánh `electron-system-shell`).
- Contract và implementation phải ở hai task khác nhau
  (`AGENTS.md` — quy tắc contract-trước-code; `../../architecture/ELECTRON_G1_PLAN.md:49-56`).
- Bàn giao hiện tại yêu cầu thứ tự MIN-74 → MIN-75 → MIN-64/MIN-32/MIN-62 và
  cấm mở consumer trước approval
  (`HANDOFF_2026-09-14.md:50-51` — file đã dọn khỏi root, xem git history).
- `notary_v2` yêu cầu scope-lock trước sửa, spec duyệt cho thay đổi nghiệp vụ,
  reviewer độc lập và `verify.bat`
  (`D:/notary_v2/AGENTS.md:23-35,57-60,79-93,100-110`, kiểm tra tại revision
  `9a9bf9a`).
- `notary_v2` có route OCR thật và Word export
  (`D:/notary_v2/routers/ocr_ai.py:2471,2580,2689`;
  `D:/notary_v2/routers/cases.py:1304,1398,1454,1574,1600,1635`, revision
  `9a9bf9a`).
- Nhánh `codex/zalo-document-inbox-v2` chứa test đang đỏ
  `tests/test_ocr_ai.py:17::test_active_cloud_path_has_no_document_qr`.
  Đây là baseline cần phân loại, không được âm thầm sửa trong task khác.
- `upload_lab` quy định dry-run là mặc định
  (`D:/upload_lab_repo/AGENTS.md:10`, revision `a4349a2`).
- Đọc `.doc` dùng Windows IFilter và có nguy cơ mất cấu trúc bảng/header/footer
  (`D:/upload_lab_repo/extract_contract.py:134-160,250,335`, revision
  `a4349a2`).
- Registry phân biệt `prepared_dry_run`, `prepared_partial` và
  `uploaded_success`
  (`D:/upload_lab_repo/playwright_uploader.py:81-83,761-766,1942,2011`;
  `D:/upload_lab_repo/batch_scan.py:353-365`, revision `a4349a2`).
- UI hiện dùng các `QThread` riêng cho environment, scan và upload
  (`D:/upload_lab_repo/ui_qt/main_window.py:92-105,746-761,997-1034,1390-1402`,
  revision `a4349a2`).
- POC `codex/desktop-command-poc` có Electron 31, Node tests và Python
  FastAPI/uvicorn/httpx, nhưng POC không phải production acceptance
  (`poc/desktop_command/electron/package.json`,
  `requirements-poc-desktop-command.txt`, revision `f18a42f`).

Các đường dẫn `D:/notary_v2` và `D:/upload_lab_repo` ở trên là tên repo nguồn
để truy vết. Mọi agent sửa repo con phải dùng worktree riêng, không sửa trực
tiếp các checkout đó.

## 4. Task DAG

`A → B` nghĩa là B chỉ được bắt đầu sau khi A đã có bằng chứng đạt và review
độc lập.

| ID | Task | Phụ thuộc | Đầu ra bắt buộc |
|---|---|---|---|
| SM-00 | Đồng bộ Linear theo scope một máy | owner duyệt spec này | G1-SM active; G1-LAN deferred; MIN-75/MIN-76/MIN-66 không còn gây hiểu nhầm |
| SM-01 | Khóa baseline và inventory | SM-00 | revision, chức năng, I/O, job, DB, test, fixture, quyền; mỗi dòng có source và owner |
| SM-02 | Ma trận tương thích Windows một máy | SM-01 | pass/fail/blocker cho package, Python/native, Word, IFilter, Chromium, Unicode và quyền file |
| SM-03 | Chốt MIN-50 + MIN-64 + UX slice | SM-02 | spec Electron core/DesktopCommand/threat boundary được owner duyệt |
| SM-04 | Chốt MIN-62 | SM-01 | identity, provenance, state, error, version và write ownership được owner duyệt |
| SM-05 | Publish contract MIN-72 | SM-04 | contract + valid/invalid examples; chưa có consumer implementation |
| SM-06 | Foundation MIN-65 | SM-03, SM-05 | app sandboxed, IPC allowlist, helper lifecycle, command read-only, package smoke |
| SM-07 | Shell/navigation MIN-67 | SM-06 | Tổng quan, hai module, Office placeholder; đổi module không mất state/job |
| SM-08 | Upload/Audit MIN-69 | SM-06, SM-07 | engine thật đến dry-run; human Finalize được giữ |
| SM-09 | notary_v2 MIN-68 | SM-06, SM-07 | fixture hồ sơ đi đến Word; dữ liệu chưa confirm không thành truth |
| SM-10 | Nghiệm thu và rollback một máy | SM-08, SM-09 | installer, smoke, E2E, fault test nội bộ, rollback; ghi rõ “LAN chưa kiểm tra” |

SM-03 và SM-04 có thể làm song song sau SM-02/SM-01. SM-08 và SM-09 có thể làm
song song sau foundation, vì mỗi task dùng repo/worktree và write set riêng.
Độ sâu phụ thuộc không vượt quá bốn task; SM-06 là điểm hợp dòng.

## 5. Gate cho từng task

Mỗi task phải khai báo trước khi giao:

```text
GOAL:
AUTHORIZED BEHAVIOR:
REPO + BASE REVISION:
WORKTREE:
EXPECTED FILES:
SHARED BOUNDARIES:
INPUT FIXTURES:
ACCEPTANCE COMMANDS:
KNOWN BASELINE FAILURES:
ROLLBACK:
STOP CONDITIONS:
SCOPE: LOCKED
```

Một task chỉ được chuyển sang `completed` khi có đủ:

- commit SHA và base-to-head diff;
- danh sách file đã đổi;
- focused test output mới;
- full-suite status ghi riêng, không đánh tráo bằng focused test;
- reviewer độc lập kết luận SCOPE/SPEC/SHARED IMPACT/TEST EVIDENCE;
- rủi ro còn lại và rollback;
- không có credential hoặc dữ liệu khách hàng trong diff/log/artifact.

## 6. Các tầng kiểm thử

| Tầng | Nội dung | Có thuộc G1-SM |
|---|---|---|
| T0 | unit/static test không credential | Có |
| T1 | integration với fixture không nhạy cảm | Có |
| T2 | packaged smoke và engine thật cục bộ | Có |
| T3 | thao tác external có credential, ở chế độ không phá hủy và có người dùng | Có điều kiện |
| T4 | LAN/nhiều máy/share mạng/version skew thật | Không; chuyển G1-LAN |

T3 không tự chạy cloud OCR, Zalo hoặc portal Finalize. Nếu nghiệm thu cần
credential, tài khoản thật, chi phí, dữ liệu khách hàng hoặc nút Lưu/Finalize,
agent dừng và xuất checklist để người dùng thực hiện.

G1-SM hoàn thành khi:

- app Windows đóng gói mở không cần terminal;
- renderer không có Node quyền rộng, IPC ngoài allowlist bị từ chối;
- helper khởi động/restart/shutdown không treo app và không làm mất command;
- một command lặp lại không tạo side effect trùng;
- `upload_lab` chạy engine thật đến dry-run và chờ người dùng;
- `notary_v2` chạy fixture thật đến file Word;
- đổi module không mất job hoặc dữ liệu chưa lưu;
- log không chứa secret; installer/uninstaller không xóa dữ liệu;
- rollback về entrypoint cũ đã được chạy thử;
- báo cáo cuối ghi nổi bật: **LAN và nhiều máy chưa được kiểm tra**.

## 7. Điểm nghẽn và cách xử lý

| Điểm nghẽn | Dấu hiệu | Xử lý trong G1-SM | Dừng khi |
|---|---|---|---|
| Nhánh/fixture phân tán | tính năng hoặc test chỉ có trên branch | SM-01 inventory, giữ revision chính xác | không xác định được source/owner |
| Baseline test đỏ | test đỏ trước thay đổi, gồm test Zalo đã biết | ghi baseline, mở issue riêng hoặc owner chấp nhận | task muốn sửa ké ngoài scope |
| POC bị dùng như production | POC test pass nhưng chưa package/engine thật | chỉ dùng làm bằng chứng thiết kế | không có đường nâng cấp/rollback |
| IFilter và file Word | `.doc` mất cấu trúc hoặc quyền file lỗi | fixture trên Windows, so output từng format | cần dữ liệu khách hàng để tái hiện |
| Playwright/thread | browser bị gọi sai thread hoặc retry trùng | một Python browser owner, idempotency test | ownership chưa chốt |
| Packaging native | Electron chạy dev nhưng thiếu Python/Chromium/native DLL | test installer trên máy sạch hoặc profile sạch | không thể tái tạo package |
| Contract chưa duyệt | consumer cần tự đoán payload/state | chờ MIN-62/MIN-72 | không implement trước approval |
| Dữ liệu thành truth quá sớm | OCR output được ghi như confirmed | giữ RAW/NORMALIZED/INFERRED/CONFIRMED | thiếu confirmation semantics |
| Secret lọt renderer/log | token/cookie xuất hiện trong payload | allowlist + redaction tests | phát hiện secret thật trong artifact |
| Nhầm local là LAN | loopback test được ghi “LAN pass” | nhãn rõ T2, defer T4 | acceptance yêu cầu LAN |
| Agent ghi đè nhau | hai agent cùng checkout/file | một task–một writer–một worktree | không xác định ownership |
| Orchestration không giao prompt | `codex-trust-workspace` hoặc `agent_prompt_stalled` | sửa trust/config ngoài task rồi chạy lại có provenance | breaker đạt ngưỡng |

## 8. Circuit-break và chống vòng lặp

### Mức task

- Tối đa ba attempt cho một task.
- Attempt 2 chỉ được mở khi có chẩn đoán mới và một thay đổi cụ thể so với
  attempt 1.
- Attempt 3 chỉ được mở khi nguyên nhân trước đã có bằng chứng được xử lý.
- Attempt 3 thất bại: task thành `blocked`; không spawn thêm, không đổi tên task
  để né bộ đếm.
- Với một câu hỏi kỹ thuật chưa giải quyết, tối đa hai hướng điều tra có lý do.

### Mức hạ tầng

- Cùng lỗi startup/permission/prompt xảy ra ở hai task độc lập: dừng toàn bộ
  dispatch cùng loại.
- Timeout chờ worker không phải failure. Kiểm tra liveness một lần; nếu worker
  còn hoạt động thì tiếp tục chờ theo cửa sổ dài.
- Không dùng terminal output để tuyên bố hoàn thành. Chỉ chấp nhận
  `worker_done` đúng task/dispatch và sau đó Codex tự kiểm tra diff/test.

### Mức phạm vi và an toàn

Dừng ngay, không retry khi:

- cần mở rộng behavior, shared core, contract, DB schema hoặc công nghệ chưa
  được owner duyệt;
- phát hiện thay đổi chưa commit của người khác trong write set;
- cần dữ liệu khách hàng, secret, chi phí cloud hoặc thao tác không thể hoàn tác;
- test có thể bấm Finalize/Lưu thật mà không có người dùng;
- nguồn tài liệu và runtime mâu thuẫn;
- rollback chưa xác định.

## 9. Quy tắc điều phối Codex → Devin

- Codex là coordinator: tạo Run/Task/DAG, trả lời question, kiểm tra bằng chứng,
  gọi reviewer và tổng hợp.
- Devin là implementer/reviewer. Implementer không tự duyệt phần mình.
- Mọi task repo con dùng worktree riêng từ exact base revision. Không sửa
  `D:/notary_v2` hoặc `D:/upload_lab_repo` trực tiếp.
- Một worktree chỉ có một writer. Task song song phải có write set không giao
  nhau.
- Task spec phải chứa scope-lock, lệnh test, stop condition và định dạng bàn
  giao.
- Trước khi gọi là “đã giao qua Orca”, phải kiểm tra task và dispatch tồn tại.
- Coordinator chờ `worker_done`, `escalation`, `question`; không poll ngắn.
- Sau settlement, release đúng worker; không đóng terminal đang active chỉ vì
  chờ lâu.
- Devin sửa lỗi review trong cùng worktree/attempt khi còn đúng scope. Lỗi làm
  rộng scope phải quay về decision gate.

### Trạng thái orchestration lúc viết spec

Run `run_aa30cfe25151` đã được tạo. Hai audit task ban đầu không chạy code:

1. `codex-trust-workspace` chặn startup trước khi prompt được giao.
2. Sau khi owner duyệt trust, Devin CLI mở nhưng Orca dừng ở
   `agent_prompt_stalled`; prompt chỉ nằm ở trạng thái pasted.
3. Hai worktree repo con đã được tạo đúng và terminal thất bại đã được release.

Theo circuit-break ở trên, không mở thêm worker Devin cho đến khi Orca/Devin có
bằng chứng gửi prompt thành công. Đây là blocker điều phối, không phải failure
của source code.

## 10. Kế hoạch bàn giao và báo cáo tổng

Mỗi worker trả:

```text
TASK/ATTEMPT:
BASE + HEAD:
CHANGED FILES:
WHAT CHANGED:
FOCUSED TESTS:
FULL SUITE:
BASELINE FAILURES:
REVIEW VERDICT:
ROLLBACK:
REMAINING RISKS:
NEXT UNBLOCKED TASKS:
```

Codex chỉ báo G1-SM hoàn thành sau khi đối chiếu toàn bộ bảng SM-00..SM-10,
chạy lại các lệnh nghiệm thu phù hợp và nêu riêng:

- cái đã chứng minh trên một máy;
- cái chỉ được mock/fixture;
- cái cần người dùng chạy với credential;
- cái bị hoãn sang G1-LAN;
- task/blocker còn mở và lý do dừng.

## 11. Ngoài phạm vi

- LAN, nhiều máy, SMB/share mạng và cutover toàn văn phòng;
- chọn hoặc gộp database vật lý (MIN-63/G2);
- Sentinel/Hub của `notaryoffice`;
- `excelTK`;
- redesign UI tổng thể;
- xóa repo, branch, worktree, fixture hoặc entrypoint legacy;
- tự đóng quyết định mở trong `OPEN_DECISIONS.md`.

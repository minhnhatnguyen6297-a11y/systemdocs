# Bàn giao cho Devin — Electron G1 chạy trên một máy Windows

## Vai trò

Bạn là **Devin implementer**. Codex hoặc owner sẽ kiểm tra kết quả và tổng hợp.
Bạn không tự duyệt spec, contract hoặc code do chính mình viết.

Đây là một goal dài, nhưng không phải quyền làm mọi thứ không giới hạn. Hãy tự
chạy qua các task đã được mở gate; dừng đúng các decision gate và stop condition
trong tài liệu này.

## Mục tiêu

Tạo một bản Electron đóng gói chạy được hai luồng nghiệp vụ thật trên **một máy
Windows**:

1. `upload_lab`: chọn nguồn → scan/extract → review/edit → audit/queue →
   preflight → dry-run → chờ người dùng Finalize.
2. `notary_v2`: hồ sơ → document intake/OCR → review/confirm →
   Case Workspace/thừa kế → xuất Word.

Electron sở hữu shell/UI và vòng đời helper. Python tiếp tục sở hữu nghiệp vụ,
OCR, sinh Word và Playwright.

## Điều chỉnh quan trọng ngày 14/09/2026

Goal này chỉ nghiệm thu trên một máy.

Không làm và không tuyên bố đạt:

- LAN hoặc hai máy trạm thật;
- SMB/share mạng;
- ownership job giữa nhiều máy;
- version skew giữa client;
- mất LAN/reconnect trên mạng thật;
- cutover toàn văn phòng.

`127.0.0.1`, hai process trên cùng máy, mock mạng hoặc giả lập timeout không
phải bằng chứng LAN. Ghi chúng là test local.

MIN-76 và phần LAN của MIN-75 thuộc goal sau. Không đóng MIN-66 bằng bằng chứng
một máy.

## Nguồn phải đọc trước

Repo cấp hệ thống:

- `AGENTS.md`
- `ELECTRON_G1_PLAN.md`
- `HANDOFF_2026-09-14.md`
- `docs/superpowers/specs/2026-09-14-electron-g1-single-machine-orchestration-design.md`
- `TECH_STACK.md`
- `SYSTEM_ARCHITECTURE.md`
- `contracts/README.md`
- `OPEN_DECISIONS.md`

Linear:

- Goal: MIN-56
- Decision/spec: MIN-50, MIN-64, MIN-32, MIN-62, MIN-72
- Foundation/shell: MIN-65, MIN-67
- Migration: MIN-68, MIN-69
- Baseline/test: MIN-74, MIN-75, MIN-76
- Deferred DB/cutover: MIN-63, MIN-66

Repo con:

- Đọc `AGENTS.md` của repo trước mọi thao tác.
- Đọc đúng routed spec do `AGENTS.md` chỉ ra cho phần đang làm.
- Nếu spec, runtime và issue mâu thuẫn, dừng và báo; không tự chọn bên thắng.

## Revision nguồn ban đầu

Xác minh lại trước khi dùng; không tin mù quáng vào bảng:

| Repo | Branch/ref | SHA bàn giao |
|---|---|---:|
| `systemdocs` | `origin/electron-system-shell` | `aea764a` |
| `notary_v2` | `origin/main` | `9a9bf9a` |
| `notary_v2` | `origin/codex/inheritance-diagram-v2` | `14fb368` |
| `notary_v2` | `origin/codex/ocr-stage-pool-diagram-v1` | `a800406` |
| `notary_v2` | `origin/codex/zalo-document-inbox-v2` | `d350048` |
| `notary_v2` | `origin/codex/markitdown-qwen-poc` | `664edb4` |
| `upload_lab` | `origin/main` | `a4349a2` |
| `upload_lab` | `origin/codex/desktop-command-poc` | `f18a42f` |
| `upload_lab` | `origin/min-52-conversion-benchmark` | `ce05b52` |

Nếu SHA remote hiện tại khác bảng, ghi cả SHA cũ và mới, đọc diff, rồi dừng nếu
thay đổi làm sai phạm vi hoặc acceptance. Không tự cập nhật baseline trong im
lặng.

## Luật worktree và quyền ghi

- Không sửa trực tiếp `D:/notary_v2`, `D:/upload_lab_repo` hoặc checkout
  `systemdocs/main`.
- Mỗi issue có một worktree riêng từ exact base revision.
- Mỗi worktree có một writer.
- Reviewer dùng worker/worktree khác và chỉ review.
- Hai task chạy song song chỉ khi write set không giao nhau.
- Không xóa branch, worktree, fixture, entrypoint hoặc code legacy.
- Không merge runtime vào `systemdocs/main`.
- Không commit/push/merge khi review gate chưa đạt.
- Không sửa file ngoài `EXPECTED FILES`. Nếu cần, gửi `SCOPE BREAK REQUEST`.

Trước khi sửa, phải ghi:

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

## Thứ tự thực hiện

### P0 — Khóa baseline và inventory

Liên quan MIN-74.

Làm:

- fetch remote refs, không merge;
- ghi exact revision của mọi branch/POC cần dùng;
- inventory màn hình, thao tác, input/output, job, DB, quyền hệ thống, test và
  fixture;
- mỗi dòng đánh dấu `CHUYỂN UI`, `GIỮ PYTHON ENGINE`, `NGOÀI PHẠM VI`;
- mỗi dòng có owner, source `repo@sha:path:line`, baseline test và issue nhận;
- ghi riêng code/test/fixture chỉ tồn tại trên branch chưa merge;
- phân loại test đỏ có trước.

Bằng chứng đã biết cần xác minh:

- `notary_v2` branch `codex/zalo-document-inbox-v2` có
  `tests/test_ocr_ai.py::test_active_cloud_path_has_no_document_qr` đang đỏ.
  Chỉ xác minh và phân loại; không sửa ké.
- POC DesktopCommand của `upload_lab` không phải production acceptance.

Đầu ra:

- `G1_SINGLE_MACHINE_INVENTORY.md`;
- bảng baseline tests và known failures;
- danh sách quyết định còn thiếu.

Gate P0:

- Không có chức năng hiện hữu nào bị bỏ ngầm.
- Mọi mô tả repo con có source + line + revision.
- Owner duyệt inventory trước khi dùng làm parity checklist.

**DỪNG D0:** nếu inventory cần owner chọn giữ/bỏ chức năng, gửi report và chờ
duyệt. Không tự chuyển mục mơ hồ thành ngoài phạm vi.

### P1 — Ma trận tương thích Windows một máy

Là phần local của MIN-75. Không test LAN.

Kiểm tra:

- Electron dev và package;
- Python runtime/sidecar cùng native dependency;
- `.doc` qua Windows IFilter, `.docx`, PDF/ảnh, Excel;
- Word export/open/download;
- Chromium/Playwright và storage state;
- Unicode trong đường dẫn/tên file/nội dung;
- quyền đọc/ghi, file đang mở, path dài;
- helper start/health/restart/shutdown;
- phân loại chức năng chạy client/helper/server.

Mỗi capability phải có:

```text
CAPABILITY:
REAL OR MOCK:
INPUT FIXTURE:
COMMAND:
EXPECTED:
ACTUAL:
PASS/FAIL/BLOCKED:
OWNER:
FOLLOW-UP ISSUE:
```

Không dùng dữ liệu khách hàng. Không gọi cloud OCR, Zalo hoặc portal thật nếu
chưa có approval/credential riêng.

Đầu ra:

- `G1_SINGLE_MACHINE_COMPATIBILITY_MATRIX.md`;
- log đã redaction;
- blocker list và cách tái hiện.

Gate P1:

- Có pass/fail/blocker rõ cho mọi capability cần P2-P6.
- Ít nhất một packaged smoke read-only gọi engine thật cục bộ.
- Mock không che blocker.

**DỪNG D1:** nếu package không chứa được Python/Chromium/native dependency, hoặc
không xác định client/server ownership, không bắt đầu foundation.

### P2 — Đặc tả production và contract

Gồm ba nhánh công việc, có thể song song khi write set tách biệt:

1. MIN-50/MIN-64: Electron main, preload, renderer sandbox, DesktopCommand,
   lifecycle, packaging/update, auth và structured error.
2. MIN-32 slice: UX chuyển module, loading/empty/error/unavailable,
   `waiting_user`, cancel và dữ liệu chưa lưu.
3. MIN-62: identity, provenance, RAW/NORMALIZED/INFERRED/CONFIRMED, null/unknown,
   warnings/errors, version và write ownership.

DesktopCommand tối thiểu phải định nghĩa:

- `command_id`, command type và version;
- accepted/running/progress/waiting_user/succeeded/failed/canceled;
- status, cancel, reconnect và restart behavior;
- idempotency và duplicate handling;
- auth boundary;
- structured error, retryable flag và redaction;
- file reference có machine scope;
- compatibility window.

Không tạo contract và implement consumer trong cùng issue.

**DỪNG D2 — OWNER APPROVAL BẮT BUỘC:** sau khi viết draft MIN-64/MIN-32/MIN-62,
gửi owner review. Không bắt đầu P3 trước approval. Devin không tự duyệt.

### P3 — Publish contract

Liên quan MIN-72. Chỉ bắt đầu sau khi MIN-62 được owner duyệt.

Publish vào `systemdocs/contracts/`:

- contract version;
- valid/invalid examples;
- compatibility/migration policy;
- producer/consumer conformance checklist;
- changelog và owner.

Không viết runtime package hoặc consumer code trong P3.

Gate P3:

- contract location/version/owner rõ;
- examples kiểm tra được;
- reviewer độc lập approve.

### P4 — Electron foundation

Liên quan MIN-65. Chỉ bắt đầu sau P2/P3.

Làm trên worktree riêng từ `electron-system-shell`:

- Electron main/renderer/preload;
- context isolation, sandbox, không Node integration ở renderer;
- IPC allowlist có version;
- module registry;
- single instance;
- Python helper lifecycle;
- local auth/version check;
- diagnostics redaction;
- một command read-only gọi engine thật;
- Windows dev/package scripts.

Không chuyển nghiệp vụ Python sang Node.

Gate P4:

- packaged app mở không cần terminal;
- IPC ngoài allowlist bị từ chối;
- helper lỗi/restart không treo app;
- shutdown không tắt server dùng chung;
- command lặp không tạo side effect trùng;
- focused tests + full-suite status + independent review.

### P5 — Shell và navigation

Liên quan MIN-67. Chỉ bắt đầu sau P4.

Navigation:

- Tổng quan: connection local, version, module health, job thật;
- `notary_v2`;
- `upload_lab`;
- `notaryoffice`: chỉ “Chưa triển khai”;
- không có `excelTK`.

Gate P5:

- đổi module không hủy job;
- dữ liệu chưa lưu không mất im lặng;
- loading/empty/error/unavailable rõ;
- navigation ngoài allowlist bị từ chối;
- shell không chỉ mở app legacy bên ngoài.

### P6-A — Migrate Upload/Audit

Liên quan MIN-69. Có thể song song P6-B sau P5, trong repo/worktree riêng.

Giữ Python/Playwright:

- source → scan/extract → review/edit;
- Excel → audit → queue;
- preflight → login → fill;
- dry-run mặc định;
- browser hiển thị để người dùng soát;
- người dùng tự Finalize;
- result ghi đúng registry sau thành công thật.

Ràng buộc:

- một Python browser thread sở hữu Playwright sync API;
- retry/cancel không upload trùng;
- không tự chọn giá trị trống;
- không cướp focus;
- cửa sổ Qt ẩn không được tính là migrate UI;
- Qt còn lại phải ghi dependency chuyển tiếp.

Gate P6-A:

- output khớp fixture P0;
- packaged app gọi engine thật;
- progress/waiting_user/error/cancel/reconnect local rõ;
- dừng trước Finalize nếu không có owner trực tiếp;
- independent review.

### P6-B — Migrate notary_v2

Liên quan MIN-68. Có thể song song P6-A sau P5, trong repo/worktree riêng.

Theo inventory P0:

- hồ sơ, đương sự, tài sản;
- intake → OCR → review → confirm;
- Case Workspace/thừa kế;
- Word export/download/open;
- Zalo và capability khác chỉ khi P0 chọn.

Ràng buộc:

- dữ liệu chưa confirm không thành database truth;
- giữ provenance theo nguồn/trang;
- partial failure rõ;
- Zalo chỉ chạy server với tài khoản văn phòng;
- local test không gọi cloud/Zalo nếu thiếu approval;
- không sửa baseline Zalo đỏ trong task migration nếu issue không cho phép.

Gate P6-B:

- fixture hồ sơ hoàn thành đến file Word đúng;
- job OCR không mất khi đổi module/restart local;
- packaged smoke đạt;
- focused tests + `verify.bat` status + independent review.

### P7 — Nghiệm thu một máy và rollback

Chỉ bắt đầu sau P6-A và P6-B.

Kiểm tra:

- cài mới;
- mở app không cần terminal;
- hai luồng E2E bằng fixture không nhạy cảm;
- helper crash/restart, timeout local, cancel và duplicate command;
- đổi module khi job đang chạy hoặc có dữ liệu chưa lưu;
- file hỏng, thiếu quyền, Unicode, path dài;
- log redaction;
- update thử nghiệm;
- uninstall không xóa dữ liệu;
- rollback về entrypoint cũ.

Đầu ra:

- report từng acceptance có command/log/artifact;
- danh sách known failure còn lại;
- rollback record;
- dòng nổi bật: **LAN và nhiều máy chưa được kiểm tra**.

Không đánh Done MIN-66. Tạo/đóng issue nghiệm thu một máy riêng theo quyết định
owner.

## Tiêu chí hoàn thành goal một máy

Chỉ báo hoàn thành khi tất cả đúng:

- P0-P7 đã đạt gate và review;
- app Windows đóng gói mở không cần terminal;
- renderer sandboxed; IPC ngoài allowlist bị từ chối;
- helper lifecycle và idempotency có test;
- `upload_lab` chạy engine thật đến dry-run/human Finalize;
- `notary_v2` chạy fixture thật đến Word;
- đổi module không mất job/dữ liệu chưa lưu;
- secret không vào renderer, command, log hoặc artifact;
- installer/uninstaller không xóa dữ liệu;
- rollback đã chạy thử;
- báo cáo không tuyên bố LAN pass.

Tests pass không đủ nếu parity checklist, review hoặc rollback còn thiếu.

## Circuit-break: chống fail lặp

### Theo task

- Tối đa 3 attempt cho một task.
- Attempt 2 chỉ khi có chẩn đoán mới và thay đổi cụ thể.
- Attempt 3 chỉ khi có bằng chứng nguyên nhân cũ đã được xử lý.
- Attempt 3 fail: đánh `BLOCKED`, gửi report, dừng spawn/retry.
- Không tạo task tên mới để né bộ đếm.
- Một câu hỏi kỹ thuật tối đa hai hướng điều tra có lý do.

### Theo hạ tầng

- Cùng lỗi startup/permission/prompt ở hai task độc lập: dừng toàn bộ dispatch
  cùng loại.
- Timeout đơn thuần không phải fail. Kiểm tra liveness một lần; còn hoạt động
  thì chờ cửa sổ dài.
- Không kill/restart worker chỉ vì chậm.

### Dừng ngay, không retry

- cần mở rộng behavior/shared core/contract/DB/công nghệ chưa được duyệt;
- write set có thay đổi chưa commit của người khác;
- cần dữ liệu khách hàng hoặc secret;
- cần trả phí cloud hoặc thao tác không thể hoàn tác;
- có nguy cơ bấm Lưu/Finalize thật;
- source/spec/runtime mâu thuẫn;
- không có rollback;
- test artifact chứa dữ liệu nhạy cảm.

## Quy tắc test

- Chạy test hẹp trước, rồi test đầy đủ theo repo.
- Ghi riêng `FOCUSED TESTS` và `FULL SUITE`.
- Test đã pass trước đó không phải bằng chứng mới.
- Không nói “pass” nếu chưa có output mới, exit code và số fail.
- Baseline đỏ phải tái hiện trên base revision hoặc có artifact cũ đáng tin.
- Regression mới phải chứng minh red → green khi khả thi.
- Không đổi test chỉ để làm xanh nếu behavior/spec chưa đổi.

Các tầng:

| Tầng | Nội dung | Goal này |
|---|---|---|
| T0 | unit/static không credential | Bắt buộc |
| T1 | integration với fixture | Bắt buộc |
| T2 | package + engine thật local | Bắt buộc |
| T3 | external có credential, không phá hủy, có owner | Có điều kiện |
| T4 | LAN/nhiều máy | Hoãn |

## Báo cáo sau mỗi task

```text
TASK/ATTEMPT:
GOAL + SCOPE:
WORKTREE:
BASE + HEAD:
CHANGED FILES:
WHAT CHANGED:
SOURCE EVIDENCE:
FOCUSED TESTS:
FULL SUITE:
BASELINE FAILURES:
REVIEW VERDICT:
ROLLBACK:
REMAINING RISKS:
NEXT UNBLOCKED TASKS:
STOP/GO:
```

Reviewer phải kết luận:

```text
SCOPE: PASS/FAIL
SPEC: PASS/FAIL
SHARED IMPACT: PASS/FAIL
TEST EVIDENCE: SUFFICIENT/INSUFFICIENT
VERDICT: APPROVE/BLOCK
```

## Cách bắt đầu ngay

1. Xác minh đang ở worktree riêng của đúng repo; nếu không, dừng.
2. Đọc toàn bộ nguồn bắt buộc.
3. Fetch remote refs và đối chiếu bảng revision, không merge.
4. Thực hiện **P0 read-only**.
5. Trả inventory + blocker report.
6. Dừng ở D0 để owner duyệt trước khi viết code.

Không bắt đầu P1-P7 trong lần chạy đầu nếu P0 chưa được owner duyệt.

## Ngoài phạm vi

- LAN/nhiều máy/SMB/cutover toàn văn phòng;
- gộp database vật lý (MIN-63/G2);
- Sentinel/Hub `notaryoffice`;
- `excelTK`;
- redesign toàn bộ UI;
- xóa legacy;
- tự chốt mục mở trong `OPEN_DECISIONS.md`.

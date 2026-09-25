# MIN-113 progress — VERIFY parity, packaged smoke, cutover prep

## Trạng thái: verification hoàn tất — chờ owner review UI để cutover

Verifier agent `e33d87e3` bị treo sau khi hoàn thành phần build (npm install,
sidecar PyInstaller, electron-builder `dist-app/win-unpacked`, fixture
`full-flow.json`). Parent agent tiếp quản và hoàn tất phần verify còn lại.

## Fixture nghiệm thu

`shell/test/fixtures/notary-case-drafting/full-flow.json` — case 47: **6 người,
2 tài sản, sơ đồ V2 hoàn chỉnh (6 node), revision 3, 3 văn bản Word** (trong đó
`niem_yet` cố ý block `word.template_missing` để test partial). Mock auto-load
qua glob `*.json`. Toàn bộ dữ liệu mẫu giả, không PII.

## Bằng chứng chạy thật (worktree `D:\systemdocs-min-113`)

### Regression baseline
- `npm test` → **113/113 pass** (~20.8s)
- `pytest test_notary_mock_adapter.py test_notary_adapter_contract.py test_jobstore.py` → **112 passed**
- `contracts/notary-case-drafting/validate_examples.py` → **34 files, 0 unexpected**

### Scripted E2E qua gateway — MOCK (`G1_DEV_NOTARY_MOCK=1`)
Script `.agent/scratch/min113_e2e.py` — JobStore thật + `command_registry.COMMANDS` thật (không mock JobStore):

**21/21 hành vi đúng contract** (2 "FAIL" ban đầu là lỗi assertion của script —
backend trả `workspace_locked` đúng contract §192, script expect `case_locked`):

| Bước | Kết quả |
|---|---|
| `case_list` | succeeded — case 47 có trong list `[47..42]` |
| `workspace_get(47)` | 6 người / 2 tài sản / diagram 6 node / `revision:3` / `backend_mode:mock` |
| `intake_analyze` (text) | succeeded, 1 suggestion, **không auto-confirm** |
| `workspace_commit_stage` (+1 người) | succeeded, rev 3→4 |
| commit `base_revision` cũ | failed `workspace_conflict` |
| `diagram_evaluate` | succeeded, render_model đủ `allocations/breakdowns/conservation` |
| `diagram_save` | succeeded, rev→5 |
| `word_export_options` | 3 docs: `khai_nhan_di_san`, `thoa_thuan_phan_chia`, `niem_yet` |
| `word_export_batch` 3 docs → temp dir | **partial**: 2 saved (file .docx tồn tại thật trên disk), 1 failed `word.template_missing` |
| destination thiếu `is_dir` | `validation_error` |
| `workspace_get(99999)` | `case_not_found` |
| case 44 locked | read OK; commit → `workspace_locked`; save → `workspace_locked`; **evaluate vẫn succeeded** (read-only đúng contract) |
| reload workspace_get | revision 5 persist, người mới commit còn nguyên |

### Scripted E2E — REAL (không mock flag; DB `D:\systemdocs-min-113\notary_v2\notary.db` worktree-local/temp, KHÔNG phải DB user chính)

| Bước | Kết quả |
|---|---|
| `workspace_get(1)` | succeeded — 7 người, inheritance, `backend_mode:real` |
| `intake_analyze` (text không parse được) | `partial` + `errors[0].code=intake.parse_failed` — source-failure isolated đúng contract |
| `diagram_evaluate` | succeeded — render_model thật: `allocations` (`inheritedShare:'1/6'`, `displayPercent:'16.67'`), `breakdowns`, `conservation:{allocated:'1',total:'1'}` |
| `word_export_options` | 3 docs, không blocked |
| `word_export_batch` 1 doc → temp | **succeeded, .docx thật trên disk** |
| commit `base_revision` cũ | `workspace_conflict` |
| case 2 locked | read OK; commit → `workspace_locked`; evaluate → succeeded |

**Parity mock↔real: khớp** — cùng envelope, cùng shape `data.case/stage/diagram`,
cùng error codes, cùng semantics (locked/evaluate/conflict/word per-doc).

### Fault injection
- `QWEN_API_KEY` vắng + intake ảnh (real) → `partial` + `ocr.engine_unavailable`
  "thiếu API key OCR" — lỗi có kiểm soát, không crash.
- Stale revision → `workspace_conflict` (cả mock lẫn real).
- Locked case → `workspace_locked` cho mọi command ghi; evaluate read-only OK.
- Destination thiếu `is_dir` → `validation_error`; word partial/all-failed/cancel
  đã cover bởi test suite + JobStore result-preservation (MIN-115).

### Packaged smoke — THẬT
`shell/dist-app/win-unpacked/g1-shell.exe` (electron-builder --dir, sidecar
PyInstaller bundled), chạy 25s trên Windows desktop:

```
{"level":"warn","msg":"G1_DEV_NOTARY_MOCK bi bo qua tren ban packaged — backend real"}
{"level":"info","msg":"spawn sidecar","meta":{"port":49290,"cmd":"...resources\\sidecar\\g1-shell-sidecar\\g1-shell-sidecar.exe"}}
{"level":"info","msg":"sidecar healthy","meta":{"engine":"g1-shell-sidecar/0.1.0",...}}
```

- **Packaged KHÔNG nhận `G1_DEV_NOTARY_MOCK=1`** — strip env + log warning, route real (đúng nghiệm thu "packaged không âm thầm mock").
- Sidecar exe packaged spawn + healthy trên port động.
- Đóng app → sidecar exit + restart-log (timeout kill expected, không orphan/crash dai dẳng).
- Log không chứa PII: chỉ path build dir `D:\systemdocs-min-113`, không username `C:\Users\MINH`, không nội dung case.

### Privacy
Packaged log sạch PII. Log renderer/ipc đi qua `redactString` (mask
`C:\Users\<user>`, bearer token, sensitive keys — đã có test). Token file không
vào log (SENSITIVE_KEY match `token`).

## Khác biệt có chủ ý so với web cũ (đối chiếu)
- Diagram render từ `render_model` backend (HTML/CSS thuần) thay ReactFlow.
- `Excel→Word` không còn trong nav chính (registry giữ command tương thích 1 chu kỳ).
- `zalo.*` trả `command_unknown` ở renderer (migration MIN-103); sidecar còn handler nhưng unreachable.
- File access qua opaque `file_token` — renderer không bao giờ gửi path thô.
- `notary.case_list` route qua gateway (mock parity) thay gọi real trực tiếp.

## Chưa làm (đúng ranh giới)
- **Owner review UI thật + cutover entry mặc định** — gate owner, không tự đổi.
- Manual checklist 1440×1024 + 1280×820 — cần mắt người (owner).
- Sidecar restart fault injection thủ công (covered bởi test `missing exe`/`restart` trong shell suite).

# Progress — MIN-113

## Trạng thái: xong phần verify — 2026-09-25 (chờ owner review để cutover)

Base `6799886`. Task VERIFY — không sửa runtime, chỉ fixture + task docs +
doc drift thật. Evidence tạm ở `.tmp/min113/` (gitignored), script E2E ở
`.agent/scratch/min113_e2e.py` (gitignored).

## 1. Fixture

- Fixture cũ `ready.json` chỉ có 4 người — thiếu tiêu chí "≥6 người".
- Đã thêm `shell/test/fixtures/notary-case-drafting/full-flow.json`
  (scenario `full-flow`, case `47`): stage 6 người + 2 tài sản, diagram
  6 node hoàn chỉnh (pool rỗng), revision 3, 3 văn bản Word
  (`khai_nhan_di_san`/`thoa_thuan_phan_chia` ready, `niem_yet`
  `word.template_missing`). Toàn bộ dữ liệu giả (tên "Người Mẫu …", CCCD
  dạng `000000000xxx`, địa chỉ "Địa chỉ mẫu") — không PII.
- Không sửa adapter/contract — mock adapter đọc scenario từ fixture dir sẵn có.

## 2. Baseline regression — đã chạy, pass

| Lệnh | Kết quả |
|---|---|
| `npm install` (shell/) | OK — Electron postinstall thiếu `electron.exe`, đã fix bằng `Expand-Archive` từ cache `electron-v31.7.7-win32-x64.zip`; `electron --version` = 31.7.7 |
| `npm test` (shell/) | **113 pass / 0 fail** |
| `pytest test/test_notary_mock_adapter.py test/test_notary_adapter_contract.py` (venv) | **100 pass** |
| `python shell/test/test_sidecar_contract.py` | **Ran 25 tests — OK** (cần cài `httpx` vào venv — đã cài) |
| `pytest` 6 suite notary_v2 (venv, **cwd = notary_v2**) | **188 pass, 37 warnings** (deprecation) |
| `python contracts/notary-case-drafting/validate_examples.py` | **34 files, 0 unexpected outcomes** |
| `FULL_VERIFY=1 .\verify.bat` (notary_v2) | FAIL tại bước `npm Zalo connector tests` — 3 test `runDataSync …` ENOENT file tạm trong `%TEMP%`, **pre-existing ngoài scope** (xem §7); các bước trước pass: py_compile, `test_ocr_ai` 44, `fast_audit` 36, Zalo inbox pytest 142, Zalo inbox UI node 18 |

Lưu ý: chạy 6 suite notary từ worktree root (cwd sai) cho 12 fail do
`word_templates/...` resolve tương đối — lỗi môi trường, không phải
regression; chạy lại từ `notary_v2/` pass 188.

## 3. Full flow E2E qua gateway (script `.agent/scratch/min113_e2e.py`)

Flow: `case_list` → `workspace_get` → `intake_analyze(text QR giả)` →
`workspace_commit_stage(+1 người)` → `diagram_evaluate` → `diagram_save` →
`word_export_options` → `word_export_batch` (3 docs, dest `.tmp`) →
`workspace_get` reload kiểm persist.

### Mock (case 47, scenario full-flow) — 10/10 PASS

```text
[PASS] case_list mock: ids=[47, 46, 45, 44, 43, 42]
[PASS] workspace_get: rev=3 people=6 assets=2 nodes=6 backend=mock
[PASS] fixture>=6people,>=2assets: people=6 assets=2
[PASS] intake_analyze(text QR): suggestions=1 errors=[]
[PASS] workspace_commit_stage(+1 person): rev=4 entity_id_new=[500]
[PASS] diagram_evaluate: status=complete warnings=0
[PASS] diagram_save: rev=5 status=complete
[PASS] word_export_options(3 docs): khai_nhan:ready; thoa_thuan:ready; niem_yet:word.template_missing
[PASS] word_export_batch: partial — saved=[khai_nhan, thoa_thuan] failed=[niem_yet] skipped=[]
        on_disk: Van_ban_khai_nhan_di_san_HS-47.docx, Thoa_thuan_phan_chia_di_san_HS-47.docx
[PASS] reload persist: rev=5 people=7 nodes=7
```

Evidence: `.tmp/min113/e2e-mock.json`, DOCX ở `.tmp/min113/dest-mock/`.

### Real (DB test tạm trong worktree — không phải DB user) — 10/10 PASS

```text
[PASS] case_list real: case_id=1 err=None
[PASS] workspace_get: rev=1 people=6 assets=2 nodes=0 backend=real
[PASS] intake_analyze(text QR giả): suggestions=1 errors=[]
[PASS] workspace_commit_stage(+1 person): rev=2 entity_id_new=[7]
[PASS] diagram_evaluate: status=complete warnings=0
[PASS] diagram_save: rev=3 status=complete
[PASS] word_export_options: khai_nhan:ready; thoa_thuan:ready; niem_yet:word.template_missing
[PASS] word_export_batch: partial — 2 saved + niem_yet fail
        on_disk: Van_ban_khai_nhan_di_san_HS-1.docx, Thoa_thuan_phan_chia_di_san_HS-1.docx
[PASS] reload persist: rev=3 people=7 nodes=7
```

Evidence: `.tmp/min113/e2e-real.json`, DOCX ở `.tmp/min113/dest-real/`.
Sửa script (không sửa product): import `models` trước `create_all` (thiếu
table), dọn `*.docx` dest trước mỗi batch (tránh đếm nhầm file `_2` cũ).

## 4. Fault injection — đã chạy cả hai backend

Evidence: `.tmp/min113/e2e-mock-faults.json` (9/9 PASS),
`.tmp/min113/e2e-real-faults.json` (8/9 — 1 defect thật, xem §4b),
`.tmp/min113/faults-real.log`, `.tmp/min113/bisect.log`,
`.tmp/min113/restart-probe.json` (7/7 PASS).

### 4a. Bảng kết quả

| Fault | Mock | Real |
|---|---|---|
| Thiếu `QWEN_API_KEY` (intake ảnh) | n/a (mock parse marker) — `intake.parse_failed` controlled | PASS — `ocr.engine_unavailable` "thiếu API key OCR (QWEN_API_KEY/DASHSCOPE_API_KEY)" |
| `base_revision` cũ | PASS — `workspace_conflict` "base_revision=1 khác server_revision=3" | PASS — `workspace_conflict` "Revision server hiện là 3" |
| Case locked → commit | PASS — `workspace_locked` "hồ sơ #44 đã khóa" | PASS — `workspace_locked` "Hồ sơ #2 đang bị khóa" |
| Case locked → diagram_save | PASS — `workspace_locked` | PASS — `workspace_locked` |
| Dest không tồn tại | PASS — `file_not_found` | PASS — `file_not_found` "khong tim thay: no-such-dir-xyz" |
| Dest là file (không phải dir) | PASS — `file_not_found` | PASS — `file_not_found` "khong phai thu muc" |
| Dest read-only (icacls deny WD,DC) | PASS — error envelope PermissionError | **FAIL — DEFECT, xem §4b** |
| Cancel giữa batch | PASS — `breakdown.skipped=[thoa_thuan, niem_yet]` trên wire, per-doc status `skipped` | PASS — giống mock |
| Template hỏng/thiếu | PASS — `niem_yet` per-doc `word.template_missing`, status job `partial` | PASS — giống mock |
| Sidecar restart giữa job | — | PASS (packaged exe): inst mới, job cũ → 404 `job_not_found`, job mới `succeeded` (7/7) |

### 4b. DEFECT phát hiện — `word_export_batch` real + dest read-only → HANG

- Triệu chứng: `word_export_batch` (backend thật) với destination bị ACL
  deny write (`icacls /deny MINH:(WD,DC)`) **quay >60s, job không về
  terminal, không cancel được**.
- Stack bắt được khi timeout (`.tmp/min113/bisect.log`):
  `tempfile._mkstemp_inner` ← `tempfile.mkstemp` ←
  `notary_v2/services/word_batch_export.py:242` `_render_temp` ←
  `:336` `_export_one_document` ← `:453` `export_batch`.
- Cơ chế: `_render_temp` ghi file tạm NGAY TRONG dest; trên Windows
  `tempfile._mkstemp_inner` (stdlib `tempfile.py:260-265`) khi gặp
  `PermissionError` mà `_os.access(dir, W_OK)` trả True (ACL deny không
  được `_waccess` nhận đúng) → `continue` retry tới TMP_MAX — trông như
  hang vô hạn từ phía job.
- Mock không đi đường này (ghi trực tiếp) nên trả `PermissionError`
  envelope đúng — **đây là khác biệt mock/real thật**, không phải lỗi
  test.
- Đề xuất fix (ngoài phạm vi VERIFY — cần issue/owner quyết): probe ghi
  thử vào dest trước batch + check cancel giữa retry, hoặc render temp ra
  `%TEMP%` rồi publish (đổi semantic same-volume). Ghi vào decisions.md.

## 5. Privacy — PASS

Chạy intake ảnh (tên file `CCCD_NguoiMau_000000000999.png`, thiếu key) +
text chứa CCCD giả + word batch lỗi template, bật log:

- Log intake chỉ ghi `source_id`, `kind`, `status`, `ms`, `code` —
  KHÔNG tên file, KHÔNG raw OCR, KHÔNG nội dung text
  (`.tmp/min113/privacy-log.txt`).
- Grep log cho: tên fixture ("NguoiMau"), CCCD giả (`000000000999`),
  raw OCR, `C:\Users\MINH` → **0 match** (path user trong log JS đã qua
  `src/main/redact.js`).

## 6. Packaged smoke — PASS (1 giới hạn môi trường, xem §6b)

```text
npm run build:sidecar   → OK: sidecar/dist/g1-shell-sidecar/g1-shell-sidecar.exe
npm run dist            → electron-builder --dir → dist-app/win-unpacked/g1-shell.exe
```

- Launch `g1-shell.exe` với `G1_DEV_NOTARY_MOCK=1` cố tình bật:
  sidecar packaged log `WARN: G1_DEV_NOTARY_MOCK bi bo qua tren ban
  packaged (backend real)` — **mock flag bị strip đúng spec**
  (`.tmp/min113/sidecar-packaged.log`, `notary_gateway.py:36-40`).
- Smoke probe (G1_SMOKE): sidecar ready, `file.inspect` succeeded,
  app exit code 0 (`.tmp/min113/smoke-packaged.json`,
  `.tmp/min113/app-launch.log`).
- Window thật: title `G1 Shell`, 1280x820, nav mới hiển thị — screenshot
  `.tmp/min113/packaged-window.png`.
- Tắt sạch: `g1-shell.exe` / `g1-shell-sidecar.exe` không còn process.

### 6b. Giới hạn packaged real-engine (ghi nhận, không che)

- Không `G1_NOTARY_V2_ROOT` → `notary.*` trả `engine_not_installed`
  "chua cau hinh engine root cho notary_v2" (controlled).
- Có `G1_NOTARY_V2_ROOT` → `engine_unavailable` "khong import duoc
  models ... No module named 'sqlalchemy'" (bundle PyInstaller thiếu
  deps nặng của engine; trước đó gặp `sqlite3`).
- Hệ quả: "mở case thật / export Word trên bản packaged" CHƯA verify
  được end-to-end — chỉ verify được đường lỗi controlled. Cần task
  packaging riêng (bundle engine deps hoặc đóng gói engine kèm venv).
  Owner phải biết trước cutover → đã đưa vào checklist + handoff.

## 7. verify.bat (FULL_VERIFY=1) — FAIL ngoài scope, đã định danh

- Lần đầu fail môi trường: `verify.ps1` tìm `notary_v2/venv` — worktree
  không có venv → tạo junction `notary_v2/venv` →
  `D:\systemdocs\notary_v2\venv` (gitignored, không phải repo change).
- Lần hai fail: 5 test `test_zalo_inbox*` —
  `ZoneInfoNotFoundError: Asia/Ho_Chi_Minh` (venv Windows thiếu `tzdata`)
  → `pip install tzdata` vào venv → pytest Zalo step pass (142).
- Lần ba fail: `npm Zalo connector tests` — 3 test `runDataSync …`
  ENOENT `…\Temp\zalo-history-*\*.json` (`connector.test.mjs:693+`,
  `core.mjs:238` — read sau cleanup race trên Windows). Chạy lại độc lập
  vẫn fail deterministic (87 pass / 3 fail); chạy cùng suite trên
  worktree canonical `D:\systemdocs` cũng fail (88 pass / 2 fail cùng
  lớp ENOENT) → **pre-existing, Windows/Zalo scope (MIN-103), không
  liên quan diff MIN-113** (diff không đụng `notary_v2` code).
- Log đầy đủ: `.tmp/min113/verify-bat.log`. Các bước pass trước khi
  throw: py_compile, `test_ocr_ai` 44, `test_fast_audit` 36, Zalo inbox
  pytest 142, Zalo inbox UI node 18. verify.ps1 không chứa step chạy 6
  suite nghiệp vụ — 6 suite đó verify riêng ở §2 (188 pass).

## 8. Đối chiếu web cũ (form.html / routers/cases.py) — khác biệt có chủ ý

Đã đọc `frontend/templates/cases/{list,detail,form,templates}.html` +
`routers/cases.py`. Bảng đầy đủ theo khối đã có trong spec
`notary_v2/docs/platform/case-workspace/drafting-tab.md` §9 — phần dưới
là xác nhận verify trên code thật, không phải regression:

| Khối | Web cũ | Electron tab (hiện tại) |
|---|---|---|
| Intake | Ảnh OCR qua modal `/ocr_ai`; Excel ghi DB ngay (`customers.py:356+`); `+ Tài sản` → `/properties/inline-create` ghi DB ngay; không PDF/DOCX/text | 5 nguồn `image/pdf/docx/xlsx/text` qua `notary.intake_analyze`; mọi nguồn (kể cả Excel, Tài sản) thành suggestion → review → Stage commit một lần |
| Review suggestion | Có review cho OCR nhưng không `observation_state`/`confidence`/`source_refs` | Mọi suggestion có `observed/normalized/inferred` + confidence + source_refs; không có `confirmed` |
| Stage commit | Person ghi per-row trước rồi snapshot `case_state_json` qua `POST /cases/{cid}/stage-update` — không `base_revision` | `workspace_commit_stage` một transaction gồm upsert + prune Diagram + tăng revision; lỗi theo `row_id`/field |
| Conflict | Không có revision — last-write-wins | `base_revision` + `workspace_conflict`; không nút ghi đè |
| Diagram | ReactFlow gán slot; `inheritance_engine.js` THIẾU FILE → fallback `engine_missing` share 0.00; engine Python không router gọi | `diagram_evaluate`/`diagram_save` qua engine Python thật; `Xem cách tính` đọc verbatim engine output |
| Word export | 1 template → 1 DOCX browser download (`routers/cases.py:1610`) | `word_export_options` + `word_export_batch`: nhiều văn bản → 1 folder, per-doc result, naming `_2` khi trùng |
| Draft persist | OCR staging trong `localStorage` (`form.html:11084`) | Bỏ — draft chỉ trong phiên (đúng spec §4) |
| File access | Browser upload bytes | `file_ref` machine_local qua file_token — renderer không thấy path |
| Zalo | `form.html` 0 tham chiếu; `zalo.status` chỉ ở command surface | Tab không có nút/command Zalo — giữ loại trừ |
| Mở hồ sơ | URL `/cases/{cid}` (ID kỹ thuật trong URL) | Overview list chọn case — không nhập ID |

Web cũ **giữ nguyên** làm fallback 1 chu kỳ — không sửa, không xóa.

## 9. Checklist owner review trước cutover (KHÔNG tự cutover)

1. Mở app packaged/dev, vào module `notary_v2` → tab `Soạn hồ sơ`.
2. Overview: mở một hồ sơ thật từ danh sách — không nhập ID kỹ thuật.
3. Intake: nạp file/text → thấy suggestion ở tray → đưa vào Stage →
   `Cập nhật` → reload vẫn thấy (persist + revision tăng).
4. Stage: sửa lỗi validation tô đúng dòng; mở 2 phiên → commit sau bị
   `workspace_conflict` (cho tải lại / giữ nháp, không ghi đè).
5. Pool/Diagram: gán thẻ, `Xem cách tính` là output engine; `Lưu sơ đồ`
   → reload giữ nguyên; xóa người khỏi Stage → commit → diagram prune.
6. Case locked → toàn màn chỉ đọc.
7. Word: popup chọn nhiều văn bản → export ra folder → per-doc status;
   file trùng → hậu tố `_2`; doc thiếu template → `partial` không chặn
   doc khác.
8. Không thấy Zalo; không thấy JSON/ID kỹ thuật trong UI production.
9. Packaged: `G1_DEV_NOTARY_MOCK=1` bị ignore + WARN — không thể mock
   lén trên production.
10. **Biết trước**: defect §4b (dest read-only hang) + giới hạn §6b
    (packaged chưa import được engine thật) — quyết block hay accept.
11. Quyết định đổi default entry — quyền owner; giữ web cũ 1 chu kỳ.

## 10. Rollback plan

- Default entry chưa đổi → rollback = không cutover (không làm gì).
- Nếu owner đã bật entry mới rồi từ chối: revert flag/entry về legacy
  (web cũ `form.html` còn nguyên, routes `/cases/*` không đổi), tab
  Electron giữ code nhưng không là entry mặc định.
- Dữ liệu: mọi write đều qua `inheritance_cases`/`case_state_json` +
  `workspace_revision` — web cũ đọc cùng schema, không cần migration
  ngược. Diagram state V2 persist trong `diagram` JSON — web cũ đọc được
  phần nó hiểu (đã có migration-on-read).
- Không có thay đổi contract/DB/Zalo trong task này → không có gì để
  revert ngoài entry.

## Đã làm
- Fixture `full-flow.json` (mới); E2E script `.agent/scratch/min113_e2e.py`;
  probes `.tmp/min113/{privacy_probe,readonly_probe,fault_bisect,cancel_real,restart_probe,shot}.py/ps1`.
- Toàn bộ verify §2–§6, §8–§10; records `progress/decisions/handoff.md`.
- Doc drift: `drafting-tab.md` §8 "hiện trạng shell" đã cũ (7 command +
  gateway đã tồn tại) → cập nhật; `shell/README.md` nav 7 mục → 5 +
  chưa nhắc tab/gateway/mock → cập nhật phần liên quan.
  `ELECTRON_G1_PLAN.md` là plan-level, không có drift cần sửa.

## Check đã chạy
- Toàn bộ bảng §2 + §3 + §4 + §5 + §6 — output trích trong file này;
  raw JSON/log tại `.tmp/min113/`.

## Owner review round — 2 bug runtime moi lo, da fix (`d0d93b1`)

Phat hien khi owner chay `npm start` tren main checkout:

1. **Renderer SyntaxError**: `case-drafting-view.js` redeclare
   `INTAKE_KIND_LABEL`/`OBS_STATE_LABEL` trung `intake-dialog.js` —
   script thuong share global scope → init chet → sidebar khong render,
   module khong bam duoc. Sua: xoa duplicate, view dung
   `_OBS_STATE_LABEL` + typeof fallback (UMD require doc lap van di).
2. **Sidecar restart-loop**: `config.js` dev spawn `python` tren PATH —
   system Python thieu uvicorn → sidecar exit 1 → 3 retry roi
   unavailable. Sua: dev fallback auto-detect
   `notary_v2/venv/Scripts/python.exe` khi `G1_PYTHON` khong set.

**Verify headless (Playwright qua CDP, `--remote-debugging-port`)**:
launch electron.exe mock mode → sidebar render 5 modules → click
notary_v2 → case 47 mo duoc → Stage (2 tai san, 6 nguoi, rev 3) +
Pool + So do quan he + Word tab render day du → **0 console error,
0 page error**. Screenshots: `.tmp/ui_notary.png`,
`.tmp/flow_overview.png`. npm test 113/113.

Bonus: `path.txt` cua electron npm package co trailing `\n` ma
`index.js` khong trim → spawn ENOENT tren main checkout — da fix local
(ghi file khong newline). Worktree khac gap loi tuong tu thi ap dung.

## Owner review UI (2026-09-25) — ket qua

**Dat (merge de):** tab "Soạn ho so" + "Tổng quan ho so" — layout, Stage,
Pool, case list, mock banner deu duoc duyet.

**Chua dat / defect moi:**

1. **Tab Word chua dat — can spec lai.** Noi dung surface Word hien chi
   la placeholder (spec §1); diem vao Xuat Word nam trong Soạn ho so.
   Owner yeu cau spec rieng cho tab Word truoc khi lam tiep.
2. **Diagram mat thao tac keo-tha.** Drag da implement
   (`relationship-diagram.js` card.draggable person + drop tren node)
   NHUNG: (a) pool person card chi draggable khi `canWrite`; (b) case
   fixture da gan het nguoi → pool chi con asset (draggable=false) →
   khong con gi keo duoc; (c) node DA GAN khong keo duoc de doi slot /
   bo gan bang keo-tha. Owner thao tac khong thay keo-tha → can fix:
   node draggable + drop giua nodes + pool person luon keo duoc.
3. **Stage tai san phai render COT, khong phai hang** nhu hien tai
   (hien asset la card-hang xep doc, owner muon layout cot).

Verify evidence keo-tha: headless CDP tren case 47 —
`[draggable]` chi 2 phan tu, ca hai `d:false` (asset card), khong co
person card nao draggable.

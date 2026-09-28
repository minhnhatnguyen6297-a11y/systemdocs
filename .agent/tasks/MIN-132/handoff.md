# Handoff — MIN-132 (P9: Gộp các phase, kiểm tra toàn luồng và bàn giao UI)

**Ngày:** 2026-09-28 · **Nhánh:** `consolidate/monorepo` · **Repo:** `D:\systemdocs`
**Baseline đầu task:** `6d70c97` · **Commit cuối task:** xem mục "Commit" dưới.

## 1. Phạm vi đã làm

P9 = kiểm chứng tích hợp, không replay commit P1–P8 (đã commit trực tiếp).
Đã chạy: toàn bộ nhóm test được yêu cầu, Electron thật + sidecar thật, đi
luồng UI end-to-end qua CDP, checklist viewport/bàn phím/focus/dialog/cuộn,
đối chiếu docs trạng thái, ghi task record + commit theo path sở hữu.

**Không có sửa code app nào.** Mọi "fail" trong probe đều do driver/harness —
xem `decisions.md` D1.

## 2. Bảng test/check — pass / skip / fail

| # | Nhóm | Lệnh | Kết quả | Ghi chú |
|---|---|---|---|---|
| 1 | Contract examples | `python contracts/notary-case-drafting/validate_examples.py` | **PASS** — 68 files, 0 unexpected | root |
| 2 | Shell renderer/model | `cd shell && node --test test/*.test.mjs` | **PASS** — 254/254 | full suite P4–P8 |
| 3 | Notary adapters | `cd shell && python -m pytest test/test_notary_adapter_contract.py test/test_notary_intake_adapter.py test/test_notary_mock_adapter.py -q` | **PASS** — 194 | 23 warning SQLAlchemy/py3.12 |
| 4 | Upload python | `cd shell && python -m pytest test/test_upload_workspace.py test/test_upload_workflow.py test/test_upload_recovery.py -q` | **PASS** — 65 | `test_upload_recovery.py` resolve ở `shell/test/` |
| 5 | Notary workspace | `cd notary_v2 && python -m pytest tests/test_case_workspace.py tests/test_inheritance_workspace.py -q` | **PASS** — 87 | cwd=notary_v2 bắt buộc |
| 6 | Notary full suite | `cd notary_v2 && python -m pytest tests -q --ignore tests/test_fast_audit_*` | **507 pass / 9 fail / 1 skip** — fail **pre-existing** (không sửa): customers_excel, docs_structure, document_conversion_poc, zalo×6 | ghi từ MIN-128 |
| 7 | fast_audit collect | — | **SKIP/BLOCKED** — thiếu dep `rapidfuzz` | môi trường, ngoài phạm vi |
| 8 | verify.ps1 | `cd notary_v2 && powershell -NoProfile -ExecutionPolicy Bypass -File verify.ps1` | **PASS** — py_compile OK; ruff không cài (skip); OCR/fast_audit/Zalo skip do không file changed | incremental |
| 9 | Whitespace | `git diff --check` | **PASS** — clean | |
| 10 | Electron + sidecar | `cd shell && npm start` + `G1_SMOKE=1` | **PASS** — app mở, sidecar Python thật healthy, `file.inspect` OK, exit 0 | Electron 31 |
| 11 | Luồng UI Electron | CDP drive (`.agent/scratch/drive*.mjs`) | **PASS** — toàn luồng mục 3 | 57 ảnh `screenshots/` |
| 12 | Viewport/DPI | CDP emulation | **PASS** phần CSS-pixel; **DPI Windows thật chưa kiểm** — xem §4 | |

## 3. Luồng end-to-end đã kiểm chứng trên Electron thật

### Notary
- **Hồ sơ mới:** nhập fixed fields → `Lưu hồ sơ` → validation errors inline
  đúng field/dòng → điền đủ → save → Pool nạp người → gán node qua menu
  `Gán vị trí` → evaluate → `Xem cách tính` mở panel → `Lưu sơ đồ` → persist
  → mở lại thấy đủ. (b1–b6)
- **Hồ sơ cũ:** mở case 47; locked metadata; loại việc unsupported render
  đúng thông báo. (b10/b11)
- **Hủy thay đổi:** sửa Stage → `stageDirty` gate chặn evaluate/`Lưu sơ đồ`
  đến khi `Cập nhật`; `Hủy thay đổi` confirm → restore cả Stage lẫn Diagram
  về committed. (b7/b7b)
- **3 tài sản + reorder:** thêm đến cap 3; đổi thứ tự bằng drag/▲▼; số vị trí
  nhận bám vị trí cột sau reorder. (a4/a6/a7)
- **Dialog loại đất:** chip `N loại` mở dialog bảng chuyển vị; `Áp dụng` ghi
  draft (dirty, cần `Cập nhật`); `Hủy` bỏ thay đổi dialog. (a5)
- **Two-party:** đúng 30 slot `p1..p30` cố định; gán vào `p16` = ghế đầu bên
  B; gán lên ô đã có người = swap; ô trống giữ nguyên không dồn; gỡ người trả
  về Pool; `Mở rộng` overlay gần toàn màn, Esc đóng + trả focus. (b9/c2b/c4/
  d1/d2/d3)
- **Thừa kế >30 node:** case 49 render 34 node, không co nhỏ dưới mức đọc.
  (g1/g2)
- **Conflict:** bump revision ngoài band → commit stale `base_revision` →
  dialog "Hồ sơ đã thay đổi trên máy chủ" → `Tải bản mới` load revision mới.
  (h3/h4)
- **Zalo:** nút hiển thị **disabled** + tooltip — đúng DESIGN §9.7.
- **Dirty-guard:** rời module khi dirty → confirm qua confirmModal. (e6)
- **Word (chỉ regression/biên):** tab Word + dialog mở được trên case thừa
  kế (g3); two-party `word_export` = `case_type_unsupported` khóa đúng;
  biên 5 tài sản/20 người vẫn là rule backend/contract. **P9 KHÔNG triển
  khai và KHÔNG claim hoàn tất chức năng xuất Word mới nào.**

### Upload Lab
- Hai tab `Audit Sổ Công Chứng` / `Quét & Upload Hồ Sơ` đúng spec_UI.
- State engine thật: website Nam Định, trạng thái `Chưa đăng nhập`, các nút
  env/login; banner stale "Kết quả chưa cập nhật — đã đổi ngày/tệp" khi đổi
  ngày/file sau khi nạp; KPI reset đúng.
- Khôi phục state phiên trước: run quét `7abeb945` "Đã quét xong", hàng chờ
  6 hồ sơ với trạng thái đối chiếu (`đã có trong Excel`, `missing:
  ten_hop_dong/tai_san`, `trùng trong folder`); nút `Đối chiếu với sổ mới`.
- Dry-run chờ Lưu: `Upload file đã chọn (0)` khóa khi chưa chọn; nhân sự +
  `Số tab mỗi đợt` render đúng.
- Chuyển tab/module giữ state (e5/f3/f4).
- **Không** thực hiện upload/finalize thật; **không** bấm Lưu trên cổng tỉnh;
  **không** mở session Playwright thật.

### Bàn phím / focus / dialog
- Tab order: rail → tab module → actionbar → control Stage (DOM order hợp
  lý). Focus ring hiển thị: outline 2 px trên nút, box-shadow accent trên
  input (k1).
- Dialog: mở → focus vào modal; Tab×8 + Shift+Tab giữ trong modal (trap);
  Esc đóng; focus trả về element mở (k2). Enter/Space kích hoạt nút native.

### Viewport / cuộn / dữ liệu lớn
- 1280×800, 1366×768, 1920×1080 (CSS px): không tràn ngang document.
- Bảng Người: cuộn ngang nội bộ đúng thiết kế (scroll≈1326 > client≈455).
- Two-party 30 slot render đầy tại 1280×800; Upload không tràn.
- DPR emulated 1.25/1.5 tại 1280×800: không tràn ngang (vp-*).

## 4. Giới hạn / chưa kiểm chứng

- **DPI Windows thật chưa kiểm** — không đổi được OS scaling trong phiên;
  CDP `Browser.getWindowForTarget` vắng trên Electron 31 nên không resize
  cửa sổ OS được; kết quả DPI là DPR emulated 1.25/1.5.
- **Visual acceptance của owner vẫn là bước riêng** — bằng chứng P9 là DOM/
  hành vi + ảnh chụp CDP; không thay thế nghiệm thu mắt người.
- Upload: chưa kiểm bằng session Playwright/cổng thật (có chủ đích — cấm
  upload/finalize/Lưu thật); "late/stale result" đã phủ bởi unit test scope/
  revision, không chạy race thật trên app.
- `submit_failed` tức thời khi module Notary vừa mount (request đầu) — tự
  khỏi sau refresh; ghi nhận như trạng thái race nhỏ của UI, không sửa trong
  P9 vì không lỗi chức năng (đề xuất task nhỏ nếu owner muốn chặn flash).
- Case list mock/seed của dev-DB có vài bản ghi lạ (kết quả probe trước) —
  không ảnh hưởng contract.

## 5. Docs đã đối chiếu (12 file — chỉ ngôn ngữ trạng thái)

`contracts/README.md`, `shell/README.md`,
`notary_v2/docs/platform/case-workspace/drafting-tab.md`,
`notary_v2/docs/platform/case-workspace/visual-design.md`,
`upload_lab/docs/spec_UI.md`, `upload_lab/docs/visual-design.md`,
`docs/product/ui/DESIGN.md`, `docs/product/ui/EXPERIENCE.md`,
`docs/product/ui/README.md`, `docs/product/ui/prototypes/README.md`,
`docs/product/ui/tokens.json`, `docs/product/ui/prototypes/notary.js`.

Nội dung: tham chiếu wire v1→v2 (§13 APPROVED 27/09/2026), dọn marker
"chờ duyệt/DRAFT/PENDING/chưa có" đã lỗi thời → trạng thái thật. Marker còn
đúng giữ nguyên: `upload.workflow.v1` DRAFT; `domains/inheritance/spec.md`
DRAFT; C1–C4 §13.13 mở; schema/examples v1 giữ (v1 còn hợp lệ).

## 6. Word — mục hoãn tường minh

- P9 không triển khai, không sửa, không nghiệm thu chức năng xuất Word mới.
- Chỉ xác nhận không hồi quy: tab/dialog Word mở đúng trên loại việc hỗ trợ;
  two-party khóa đúng `case_type_unsupported`; biên 5 assets/20 người giữ
  theo contract/backend.
- `document_key`/danh mục `document_type` cho `two_party` vẫn mở (§13.13 C/Q
  tương ứng) — việc của task sau, ngoài phạm vi P9.
- **Task này KHÔNG claim toàn bộ chức năng xuất tài liệu đã hoàn tất.**

## 7. Việc còn lại / đề xuất bước tiếp

- Owner visual acceptance (bước riêng — xem §4).
- Kiểm DPI Windows thật trên máy owner nếu cần nghiệm thu DPI.
- Nếu muốn chặn flash `submit_failed` lúc mount module: task nhỏ render
  trạng thái "đang tải" thay vì lỗi cho request đầu.
- `upload.workflow.v1` vẫn DRAFT — cần owner duyệt contract trước khi coi
  kênh upload là publish.
- C1–C4 §13.13 + `document_type` cho two_party — mở, task sau.

## 8. Bằng chứng

- Ảnh: `.agent/tasks/MIN-132/screenshots/` (57 ảnh: a*/b*/c*/d*/e*/f*/g*/h*/
  k*/vp-* series theo luồng ở §3).
- Script probe tạm: `.agent/scratch/cdp.mjs`, `drive*.mjs`, `probe*.mjs` —
  gitignored, KHÔNG commit.
- Task record: `.agent/tasks/MIN-132/{brief,progress,decisions,handoff}.md`.

## 9. Commit

- `COMMIT_PENDING` — cập nhật hash sau khi commit (commit path sở hữu:
  `.agent/tasks/MIN-132/` + 12 file docs ở §5). Không push, không nhánh mới.
- Footer theo convention repo + Devin co-author.

# Progress — MIN-132

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: hoàn thành phần kiểm chứng + docs — 2026-09-28

## Đã làm
- Tạo task record (brief.md). Đọc AGENTS.md, plan MIN-123 §6/§8/§9, handoff
  MIN-124..MIN-131, contract §13.
- **Test sweep — tất cả đã chạy, kết quả:**

| Nhóm | Lệnh | Kết quả |
|---|---|---|
| Contract root | `python contracts/notary-case-drafting/validate_examples.py` | **68 files, 0 unexpected outcomes** — PASS |
| Shell renderer/model | `cd shell && node --test test/*.test.mjs` | **254/254 pass** (~27s) |
| Shell adapter Notary | `cd shell && python -m pytest test/test_notary_adapter_contract.py test/test_notary_intake_adapter.py test/test_notary_mock_adapter.py -q` | **194 passed** (~27s) |
| Shell upload | `cd shell && python -m pytest test/test_upload_workspace.py test/test_upload_workflow.py test/test_upload_recovery.py -q` | **65 passed** (~15s) — engine upload_lab resolve được qua `<repo>/upload_lab` bundled |
| Notary services | `cd notary_v2 && python -m pytest tests/test_case_workspace.py tests/test_inheritance_workspace.py -q` | **87 passed** (~29s) — cwd=notary_v2 bắt buộc |
| Notary full suite | `cd notary_v2 && python -m pytest tests -q --ignore tests/test_fast_audit_*` (4 file ignore) | **507 passed, 9 failed, 1 skipped** — đúng 9 fail pre-existing đã ghi ở MIN-128: customers_excel asyncio, docs_structure, document_conversion_poc hash, zalo×6 (zalo đã tách D:\zalo-intake). KHÔNG sửa — ngoài phạm vi |
| fast_audit | — | 4 file test không collect được: thiếu dep `rapidfuzz` (pre-existing, ngoài phạm vi) |
| verify.ps1 | `cd notary_v2 && powershell -NoProfile -ExecutionPolicy Bypass -File verify.ps1` | **PASS** — py_compile OK; ruff không cài (skip); OCR/fast_audit/Zalo skip vì tree sạch (không file changed) |
| Whitespace | `git diff --check` | CLEAN |

- **Electron thật (đã chạy được — KHÔNG phải "chưa kiểm"):**
  - `npm start` tại `shell/` (Electron 31 trong node_modules). Window "G1 Shell".
  - Sidecar spawn Python thật `D:\systemdocs\notary_v2\venv\Scripts\python.exe`
    (chọn qua `src/main/config.js` dev chain); healthy; `G1_SMOKE=1` probe:
    `file.inspect` hoàn tất, exit code 0.
  - Điều khiển qua CDP (script tạm ở `.agent/scratch/drive*.mjs` — gitignored).
  - Real adapter Notary (không mock) — case list load đúng sau refresh
    (`submit_failed` tức thời lúc module mới mount là trạng thái request đầu,
    refresh hiển thị đúng — không phải lỗi app).
- **Đi luồng trên Electron thật (bằng chứng: `screenshots/`):**
  - Hồ sơ mới: nhập fixed fields → `Lưu hồ sơ` → validation errors hiển thị
    inline đúng dòng (a8) → điền đủ → save → Pool nạp người (b3) → gán sơ đồ
    qua menu (b4) → evaluate + `Xem cách tính` (b5) → `Lưu sơ đồ` → persist
    (b6) → mở lại thấy đủ.
  - Hồ sơ cũ (case 47): mở, locked khi metadata khóa; loại việc unsupported
    hiển thị đúng (b10/b11).
  - `Hủy thay đổi`: sửa Stage → dirty gate chặn evaluate/save sơ đồ (b7) →
    `Cập nhật` mở lại (b7b); Hủy có confirm + restore về committed.
  - 3 tài sản + reorder: thêm đến 3 (cap đúng), kéo đổi thứ tự (a4/a7).
  - Dialog loại đất: mở qua chip `N loại`, `Áp dụng` ghi draft, `Hủy` bỏ
    (a5-land-dialog-*).
  - Two-party 30 slot: render đủ p1..p30; gán người qua menu vào p16 (bên B
    đầu); thả/chọn ô đã có người = swap; ô trống giữ không dồn (b9/c2b/c4/d1/
    d2); `Mở rộng` overlay gần toàn màn + Esc đóng (d3).
  - Thừa kế >30 node: case 49 render 34 node, không co nhỏ dưới mức đọc được
    (g1/g2).
  - Conflict thật: bump revision ngoài band -> commit stale base → dialog
    "Hồ sơ đã thay đổi trên máy chủ" → `Tải bản mới` load revision mới (h3/h4).
  - Zalo: nút hiển thị **disabled** + tooltip (trên action bar).
  - Dirty-guard: rời module khi dirty → confirm (e6).
  - Word: tab Word render; dialog Word mở trên case thừa kế (g3); two-party
    `word_export` = `case_type_unsupported` (capability khóa UI). **Chỉ kiểm
    regression/biên — KHÔNG có Word mới, không claim hoàn tất xuất Word.**
  - Upload Lab: 2 tab Audit/Quét&Upload đúng spec; state engine thật (Nam
    Định, chưa đăng nhập); banner stale "Kết quả chưa cập nhật — đã đổi
    ngày/tệp"; run quét cũ `7abeb945` + hàng chờ 6 hồ sơ (trạng thái `đã có
    trong Excel`, `missing`, `trùng trong folder`) khôi phục đúng; nút
    `Upload file đã chọn (0)` khóa khi chưa chọn (dry-run chờ Lưu); chuyển
    tab/module giữ state (e5/f3/f4). KHÔNG upload/finalize/bấm Lưu cổng tỉnh.
  - Bàn phím: Tab đi rail → tabs → actionbar → điều khiển Stage (grip xóa,
    input, chip loại đất) theo DOM order hợp lý; focus ring nhìn được
    (outline 2px nút, box-shadow accent input — k1); mở dialog → focus vào
    modal, Tab×8 + Shift+Tab không thoát (trap); Esc đóng và trả focus về
    element mở (k2); Enter/Space kích hoạt nút native.
  - Viewport (CSS pixels, qua emulation CDP): 1280×800, 1366×768, 1920×1080,
    DPR 1.25/1.5 — **không** tràn ngang cấp document ở tất cả; bảng Người
    cuộn ngang nội bộ (scrollWidth≈1326 > clientWidth≈455, đúng thiết kế);
    two-party render đủ 30 slot tại 1280×800; Upload không tràn (vp-*).
    **Chưa kiểm DPI Windows thật** (không đổi được OS scaling trong phiên;
    CDP `Browser.getWindowForTarget` không có trên bản này → không resize OS
    được; DPR chỉ emulate).
- **Lỗi tích hợp tìm thấy: KHÔNG có.** Mọi "fail" trong probe đều do driver
  (modal chồng, click element ẩn, mở sai case/upload module khi đo, Enter
  dispatch thiếu char) — đã chạy lại đúng cách và pass. Không sửa dòng code
  nào của app.
- **Đối chiếu docs (chỉ ngôn ngữ trạng thái, không đổi semantics)** — 12 file:
  - `contracts/README.md`: dòng notary-case-drafting ghi cả v1 (§1–12, legacy)
    + v2 §13 APPROVED 27/09/2026; intro publish đếm đúng; ghi schema/examples
    là artifact v1 + `draft-v2.schema.json`/`examples/draft-v2/` là v2.
  - `shell/README.md`: wire contract → `notary.case-drafting.v2` (§13) cho
    workspace, v1 giữ cho consumer legacy.
  - `notary_v2/docs/platform/case-workspace/drafting-tab.md`: blockquote đầu,
    §1 wire contract, §10 intro → §13 v2 APPROVED + đã triển khai.
  - `notary_v2/.../visual-design.md`: PENDING/DRAFT markers §13 → APPROVED
    (Apply loại đất, chip↔vị trí, swap, Hủy thay đổi, 30 vị trí, Mở rộng).
  - `upload_lab/docs/spec_UI.md` + `visual-design.md`: "token chờ duyệt" →
    đã chốt DESIGN §9.
  - `docs/product/ui/DESIGN.md`: `color.rail`/`size.sidebar`/`Hủy`-delta rows
    "chờ duyệt" → giá trị đã chốt §9 + "đã triển khai".
  - `docs/product/ui/EXPERIENCE.md` §10: danh sách quyết định mở → ĐÃ CHỐT
    (Hủy, Mở rộng, focus, phím sơ đồ, cuộn ngang, toast).
  - `docs/product/ui/README.md`: header cập nhật trạng thái sau P6–P9; hàng
    dialog loại đất "chưa có" → `openLandDialog` đã có.
  - `docs/product/ui/prototypes/README.md`: thêm note danh sách chờ chốt đã
    được duyệt 27/09/2026 (giữ lịch sử đề xuất).
  - `docs/product/ui/tokens.json`: note "CHỜ DUYỆT" → đã chốt (rail bg,
    sidebarWidth, accent.primary, font base/title, shadow.card, radius.card).
  - `docs/product/ui/prototypes/notary.js`: 3 comment "ĐỀ XUẤT chờ duyệt" →
    đã chốt (chỉ comment; không đổi code prototype).

## Bước tiếp theo
- Handoff + commit path sở hữu.

## Check đã chạy
- Xem hai bảng trên + `handoff.md` (bảng pass/skip/fail đầy đủ).

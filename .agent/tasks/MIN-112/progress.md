# Progress — MIN-112

## Trạng thái: xong — 2026-10 (chờ review/merge)

Nối đủ 4 surface Intake → Stage → Pool/Diagram → Word export theo spec UX
MIN-104 + contract notary-case-drafting (READ-ONLY). Một component chung cho
mock/real (swap qua `makeCommandRunner` seam), draft in-memory cho tới
commit/save tường minh.

## Đã làm

- **Opaque file token (bảo mật cốt lõi)**
  - `shell/src/main/file-tokens.js` (mới): `makeFileTokenStore()` (issue/
    resolve/clear, Map token→FileRef thật, UUID) + `pickedEntry()` (shape
    renderer `{file_token,name,size_bytes,is_dir}` — không path/scope).
  - `shell/src/main/ipc.js`: `resolveFileTokens()` quét đệ quy payload
    (object+array), thay mọi node `{file_token}` bằng FileRef
    `{path,scope,size_bytes?,is_dir?}` ngay trước forward sidecar; token
    lạ/hết hạn → `validation_error`, KHÔNG forward. Sibling key renderer
    tự khai bị bỏ qua. Handler mới `desktop.v1.registerDroppedFile`
    (reject path UNC/rỗng) + `desktop.v1.setDirtyState`.
  - `shell/src/main/main.js`: `pickFiles` trả token entry; drop qua
    `registerDroppedFile` (stat trong main); token clear khi `closed`,
    `did-start-navigation` (reload dev), `before-quit`; close-guard chặn
    khi `tracker.listActive()>0` HOẶC `rendererDirty` (dialog "Vẫn
    thoát"); reset `rendererDirty` khi navigation/reload (draft chết cùng
    renderer cũ).
  - `shell/src/preload/preload.js`: `registerDroppedFile(file)` qua
    `webUtils.getPathForFile` (Electron 31 — path thật không thể forge),
    `setDirtyState(dirty)`. Renderer KHÔNG đọc `file.path`.
  - `shell/src/renderer/renderer.js`: `engine`/`upload` views đổi sang
    `{file_token}` payload + hiển thị `f.name`; `makeCommandRunner().run`
    nhận `opts` → gọi `opts.onJob(job)` ngay sau submit + mỗi poll +
    terminal (dialog cần `job_id` cho cancel + progress); notary view
    truyền `onUnsavedChange` → `api.setDirtyState` + `canLeave()` chặn
    module-switch khi dirty.

- **Intake dialog** — `shell/src/renderer/notary/intake-dialog.js` (mới):
  picker theo kind (ảnh/PDF/DOCX/XLSX, preset cho từng nút), drop-zone
  (drag/drop + Enter/Space mở picker — keyboard parity), dán văn bản
  (kind:text), danh sách source với per-source status (chờ/đang phân
  tích/xong/lỗi/bỏ qua) + lỗi riêng từng nguồn, progress + `cancelJob`,
  review card trong dialog; `user_canceled` là notice không phải lỗi;
  `Đưa vào Stage` chỉ `model.acceptSuggestion` (draft row).

- **Model** — `case-drafting-model.js`: `emit()` phát `onUnsavedChange`
  khi `stageDirty||diagramDirty` đổi; `intakeAnalyze(sources, opts)`
  passthrough opts, suggestion mới PREPEND (`d.suggestions.concat(cũ)`),
  `intakeErrors` tích lũy theo source_id, `user_canceled` → notice;
  `exportWord(keys, dest, opts)` passthrough + `normalizeWordResult`
  chuẩn hóa success/partial/`word_batch_failed.details.documents`
  (compact) về `{documents[], breakdown{succeeded,failed,skipped}}`;
  key trong `breakdown.skipped` không có row → tổng hợp row `skipped`
  (cancel giữa batch, MIN-115).

- **Diagram pane** — `relationship-diagram.js` (mới): Pool (committed
  Stage − assignments, search chỉ lọc hiển thị), drag/drop + menu "Gán
  vị trí…" (keyboard alternative, slot trống / con của / vợ-chồng của /
  slot đầu), SVG edge strip (nhãn tên người khi slot đã gán), allocation
  badge đọc `render_model` engine (JS không tính %), debounce evaluate
  500ms sau mọi draft mutation, "Đánh giá thử"/"Xem cách tính" (render
  `explanations`/`warnings`/`unresolvedEstates` verbatim — không raw
  JSON), `Lưu sơ đồ` persist với base_revision, xóa node chỉ đổi draft
  (Stage giữ nguyên), read-only trên locked (`evaluate` vẫn chạy).

- **Word dialog** — `word-export-dialog.js` (mới): load
  `word_export_options` → checkbox (disable + `block_reason` label khi
  chưa ready), `pickFiles({directory:true})` → token `is_dir`, submit 1
  lần `word_export_batch` với `{file_token}` destination, progress +
  cancel, per-doc `Đã lưu`(+Mở file qua `openPath`)/`Lỗi`+reason/`Bỏ
  qua`, partial/canceled đều render, KHÔNG tự đóng khi còn lỗi.

- **View/CSS** — `case-drafting-view.js`: mount 3 pane qua
  `window.G1_NOTARY_*` ctx (`openModal`, `pickFiles`,
  `registerDroppedFile`, `cancelJob`, `openPath`); `field_errors` render
  theo `field` dưới đúng input (person + asset) + banner theo row;
  `openModal` focus-trap Tab/Shift+Tab + Escape; tray suggestion trong
  workspace (sống qua đóng dialog). `case-drafting.css`: `.cd-field-err`,
  `.cd-edge-row` padding (fix tap-target static test), dropzone/badge/
  calc/word styles. `index.html`: load 3 file mới trước `renderer.js`.

- **`notary.case_list` mock parity** — `command_registry.py`: route qua
  `_notary_drafting("case_list")` (gateway); `notary_mock_adapter.py`:
  `case_list()` + `_mock_case_row()` cùng shape `_case_row` real adapter
  (`nguoi_chet`/`tai_san`/`tong_ty_le`/...), `id DESC` + `limit` +
  substring-over-serialized-row filter giống real; `notary_gateway.py`
  docstring. Test row-shape + query filter trong
  `test_notary_mock_adapter.py`.

## Check đã chạy (sau chỉnh cuối)

- `cd shell && npm test` → 100/100 pass.
- `node --test test/ipc.test.mjs test/notary-case-drafting-model.test.mjs
  test/notary-case-drafting-static.test.mjs` → 66/66 pass.
- `pytest test/test_notary_mock_adapter.py
  test/test_notary_adapter_contract.py -q` → 100 pass (venv
  `D:\systemdocs\notary_v2\venv`).
- `contracts/notary-case-drafting/validate_examples.py` → 34 files, 0
  unexpected.
- `node -e require()` 6 module renderer/main → load sạch (không DOM lúc
  import).

## Fix trong phiên (sau khi test chính pass)

- `registerDroppedFile` handler trả `data:{file:entry}` (khớp renderer
  `r.data.file` + comment preload); test ipc cập nhật.
- `did-start-navigation` reset cả `rendererDirty` (reload mất draft).
- `normalizeWordResult` tổng hợp row `skipped` từ breakdown (MIN-115).
- Edge strip hiển thị tên người thay slot id khi đã gán.

## Còn lại / giới hạn đã biết

- Chưa chạy smoke Electron thật (`npm start` + `G1_DEV_NOTARY_MOCK=1`) —
  chỉ kiểm chứng unit/static/contract; smoke tay nên làm trước merge nếu
  có môi trường desktop.
- Intake drop-zone trên Linux/Wayland chưa kiểm (webUtils chuẩn Electron
  31, Windows OK).
- Tab "Word" ở local nav vẫn là placeholder có hướng dẫn (surface văn
  bản thuộc lát cắt sau) — điểm vào export thực tế ở Soạn hồ sơ → Xuất
  Word.

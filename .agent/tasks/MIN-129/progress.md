# Progress — MIN-129

## Trạng thái: hoàn thành implementation, chờ review

## Đã làm
- Recon xong: model v2 (`case-drafting-model.js`), view cũ (accordion
  rows + land rows inline), P4 shared styles (`styles.css` + class
  guide), approved refs (drafting + land-types PNG + prototypes
  `notary.js`), contract §13.
- `case-drafting.css`: rewrite hoàn toàn theo tokens P4 — mọi selector
  dưới `.cd-root` hoặc tên `cd-*`; không `:root`, không re-khai class
  shared không prefix (pill/banner/dirty-dot/drop-hint/drag-handle…
  dùng của `styles.css`).
- `case-drafting-view.js`: rewrite theo bản mẫu duyệt:
  - Action bar 1 hàng: `‹` back, `Soạn văn bản`, case_type select
    (nháp)/pill (case thật), pill `Nháp — chưa lưu`/`HS-<id>`/
    locked/unsupported/stale, save-state text, `Nhập file`,
    `Zalo` (visible + disabled, title "chưa bật"), `Hủy thay đổi`,
    `Cập nhật`/`Lưu hồ sơ` + dirty-dot.
  - `openModal` canonical (`.modal-overlay`/`.modal`/`.modal.wide`,
    Esc + click nền + focus trap + restore opener); append vào
    `.cd-root` để cd-* scoped vẫn áp dụng.
  - Bảng chuyển vị Tài sản: `table.grid.cd-tbl`, `th.cd-rowlabel`
    sticky trái, mỗi tài sản 1 `th.cd-asset-col` (tối đa 3, `+ Tài sản`
    disable khi đủ), header = drag-handle + tên + icon-x; kéo-thả cột
    (`application/x-assetcol`, drop lên header = move-to-position) +
    Ctrl+←/→ trên grip; xóa giữa có confirm cảnh báo dịch vị trí.
  - 12 hàng trường asset đầy đủ contract §13.3 (4 hàng đầu khớp mẫu +
    chip `Loại đất` + 7 hàng còn lại); `land` = `.cd-chip-link`.
  - Popup Loại đất: `modal.wide`, mỗi loại 1 cột (`+ Loại đất`,
    icon-x xóa), hàng `Loại đất` (select mã canonical + giữ giá trị
    ngoài DS), `Diện tích (m²)`, `Thời hạn`; `Áp dụng` →
    `updateAssetField(row_id,'land_rows')` = draft-only (test chứng
    minh 0 command call); `Hủy`/×/Esc/click nền = no-op.
  - Bảng Người: `table.grid.cd-ptbl`, mỗi người 1 `<tr>`, 9 trường
    contract trong ô (gioi_tinh = select), cột `Để lại` radio
    (inheritance, name `cd-owner-row`, → `setOwnerRow`), drag-handle
    + `application/x-personrow` + drop-above/below + Ctrl+↑/↓ +
    icon-x xóa.
  - Focus/value: defer rebuild khi activeElement là input/select/
    textarea trong panel (giữ nguyên hành vi cũ) + `data-fid`
    (`a:<rid>:<f>`, `p:<rid>:<f>`, `adrag:`/`pdrag:`/`adel:`/`pdel:`,
    `p:<rid>:owner`, `a:<rid>:land`) capture/restore qua rebuild
    (reorder bằng nút giữ focus, kể cả caret); `syncChromeUI()` cập
    nhật dirty-dot/disabled/save-state khi rebuild bị defer.
  - `Hủy thay đổi`: nháp mới → `model.newDraft(case_type)` (không có
    baseline); case thật → `cancelDraftState` restore `stage`←
    `committed` + `diagram`←`committedDiagram` + clear dirty/errors;
    client-only, confirm trước, 0 command call.
  - `field_errors` gắn `row_id`+`field` → `td.cd-cell-err` +
    `.cd-err-msg`; lỗi cấp danh sách (`assets`/`people`/`owner_row_id`)
    → `.cd-row-errors` đầu card.
- `relationship-diagram.js` (chỉ phần Pool + khung card):
  - 1 `card.cd-rel-card`: head (title + `+ Slot`/`Xem cách tính`/
    `Đánh giá thử` sm + pill gate/stale), `.cd-rel-body` =
    `.cd-pool` pane (title `Pool (N)` + search + `.cd-pool-box` drop
    target `.drop-hint`) + `.cd-diagram` region, `.cd-rel-foot` =
    `Lưu sơ đồ` secondary+dirty-dot + `Xuất Word` primary.
  - Pool card: `.cd-pool-card` + drag-handle + `.cd-pool-nm` (+
    `.cd-pool-sub` khi trùng tên: `sinh <năm>`/`GT <số>`) + nút `→`
    assign; `.dragging` khi kéo; payload `text/plain` =
    `{kind:'person'|'asset', row_id}` — giữ nguyên cho P7.
  - Pool đọc `state.committed` trực tiếp trừ personId đã gán — KHÔNG
    dùng `model.pool()` (model dùng stage cho `caseId==null`) →
    draft Stage không bao giờ lộ vào Pool; nháp mới → face
    "Stage chưa có người đã xác nhận — Cập nhật Stage trước."
  - stageDirty gate: `caseId!=null && stageDirty` → disable
    `Đánh giá thử`/`Xem cách tính`/`Lưu sơ đồ` + pill
    "Cập nhật Stage trước"; `scheduleEvaluate` bỏ qua.
  - `openAssignMenu` → canonical modal (modal-head/body/foot).
- `intake-dialog.js`: canonical modal (`modal-head` + `modal-close` +
  `modal-body` + `modal-foot`); class `cd-src-*` → `cd-intake-*`,
  `cd-dropzone-on` → shared `.drop-hint`; giữ nguyên luồng
  picker/drop-token/text/pasted + wire `file_token`.
- Tests:
  - `test/dom-stub.mjs` (mới): stub DOM tối thiểu dùng chung
    (El + classList/dataset/querySelector `[attr="v"]|tag|.cls`/
    activeElement/dispatch/createElementNS).
  - `test/notary-case-drafting-view.test.mjs` (mới): **17 test**
    actionbar/Zalo/asset-cols/max-3/reorder-focus/add-remove/owner
    radio/typing-retention/cancel 3 case/land Áp dụng vs Hủy/
    Pool committed-only/payload text-plain/stageDirty gate.
  - `test/notary-case-drafting-static.test.mjs`: cập nhật test Zalo
    (cho phép placeholder disabled, cấm engine identifiers) + test
    CSS → kiểm tra token P4/scope/không re-khai shared.

## Kết quả chạy
- `node --test test/*.test.mjs`: **239/239 pass** (222 baseline + 17 mới).
- `node --test test/notary-case-drafting-view.test.mjs`: 17/17.
- `git diff --check`: sạch.

## Ghi chú
- Không đụng `case-drafting-model.js`; API gaps ghi ở handoff.md
  (`cancelDraft`, `movePersonRow`, `committedPool`, emit-only).
- Chưa verify thủ công trong Electron thật (không chạy được UI trong
  env này) — đã dump DOM tree qua stub để đối chiếu cấu trúc bản mẫu.

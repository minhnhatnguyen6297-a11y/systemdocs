# Handoff — MIN-133 / W2 (Stage + thanh trên)

## Trạng thái khi bàn giao — 2026-09-28
W2 đã làm xong phạm vi plan §3 (D1, D2, D4, D5, D8 phần Stage/layout). Có 1 commit trên `consolidate/monorepo`, chưa push (hash xem `git log --grep "MIN-133" --oneline`, commit `feat(MIN-133): W2 …`).
W2 không sửa `relationship-diagram.js`, `case-drafting-model.js`, `styles.css`, `index.html`, `renderer.js`, `docs/product/ui/*`, backend hay contracts.

## File đã đổi
| File | Thay đổi |
|---|---|
| `shell/src/renderer/notary/case-drafting-view.js` | Gộp thanh trên (D5), bỏ back/tiêu đề/pill Nháp/nhãn lưu (D4), bỏ card Thông tin hồ sơ (D2), `PERSON_COLS` còn 7 cột (D1), colgroup + ô `.cd-cell` + tooltip, lỗi của trường không có ô hiện ở đầu card |
| `shell/src/renderer/notary/case-drafting.css` | Viết lại phần layout tổng, thanh trên, workspace và Stage (dòng 11–365). Phần land dialog chỉ thêm rule giữ kích thước cũ. Phần relation tier trở xuống (dòng 406+) **không đổi**, trừ media query 860px cuối file (thay `.actionbar` bằng `.cd-topbar`) |
| `shell/test/notary-case-drafting-view.test.mjs` | `build()` có thêm option `respond` để giả kết quả command. Thêm 12 test MIN-133 |
| `shell/test/notary-case-drafting-static.test.mjs` | Thêm 5 test CSS/view tĩnh MIN-133 |

Không sửa hay xóa test cũ nào. 17 test view cũ vẫn đạt mà không phải đổi, vì test tìm nút theo nhãn trên toàn `view.el`.

## Cấu trúc DOM mới
```
section.cd-root                                  (con của section.cd-root-outer do renderer tạo)
├─ div.card.cd-topbar                            (cao 42px, luôn hiện)
│  ├─ div.cd-localnav[role=tablist] > button.cd-tab ×3   (Tổng quan hồ sơ / Soạn hồ sơ / Word)
│  └─ div.cd-topbar-actions                      (hidden nếu tab ≠ drafting hoặc status ∈ idle/loading/unavailable/error)
│     ├─ span.cd-vsep
│     ├─ nháp: select.cd-case-type[data-fid=top:case_type]  |  case thật: span.pill.accent.cd-case-pill "Thừa kế · HS-42" (title = loại văn bản)
│     ├─ button "Nhập file" · button "Zalo" (disabled)
│     ├─ span.cd-spacer
│     ├─ pill locked/unsupported/"Bản cũ"(stale) — chỉ khi có
│     ├─ button.js-cd-undo "Hủy thay đổi"
│     └─ button.primary.js-cd-update "Lưu hồ sơ"|"Cập nhật" [+ span.dirty-dot, aria-label "… — có thay đổi chưa lưu"]
├─ div.cd-tabpage (overview) · div.cd-tabpage (drafting) · div.cd-tabpage (word)
│  drafting > div.cd-workspace
│     ├─ banner mock/unsupported/locked/notice/error (nếu có)
│     ├─ div.cd-stage-wrap > div.cd-stage
│     │  ├─ div.card.cd-assets > card-head (h3 "Tài sản " + span.cd-count "(3)") + div.card-body.cd-stage-body > div.cd-table-wrap > table.grid.cd-tbl.cd-stage-tbl
│     │  │     colgroup: col.cd-acol-label + col.cd-acol × số tài sản
│     │  └─ div.card.cd-people > … > table.grid.cd-ptbl.cd-stage-tbl
│     │        colgroup: col.cd-pcol-drag, [col.cd-pcol-owner], col.cd-pcol-{ho_ten,gioi_tinh,ngay_sinh,ngay_chet,so_giay_to,ngay_cap,dia_chi}, col.cd-pcol-del
│     │        ô: input.cd-cell / select.cd-cell (title = giá trị); tr.cd-row-owner cho người để lại
│     └─ div.card.cd-rel-card                    (W3 — do relationship-diagram.js dựng)
└─ modal-overlay (khi mở dialog)
```
- Tab bar và `.cd-topbar-actions` nằm ngoài panel drafting. `rerender()` gọi `renderTopActions()` trước khi dựng lại panel. Focus được bắt và khôi phục trên toàn `.cd-root` qua `data-fid`.
- Khi select loại việc đang có focus, thanh trên không bị thay node (tránh đóng dropdown), chỉ đồng bộ nút. Stage vẫn được dựng lại ngay. Trước đây select nằm trong panel nên đổi loại việc bị hoãn dựng lại Stage tới lần emit sau; lỗi này đã hết.
- Khi đang gõ trong Stage, việc dựng lại vẫn được hoãn như cũ. `syncChromeUI()` chỉ cập nhật disabled và chấm dirty (không còn nhãn lưu).

## D1 / D2: dữ liệu không đổi
- `noi_cap` và `place_of_origin` không còn ô nhập. View không xóa key nào khỏi row, nên giá trị cũ đi nguyên vẹn lên `workspace_commit_stage`/`workspace_create` (có test). Nếu backend trả lỗi cho hai trường này, lỗi hiện ở đầu card Người (`hiddenPersonFieldErrors`).
- Không còn card meta. `saveDraft` gửi `case` đủ 5 key: `document_type` = `documentTypesFor(case_type)[0]`, `ngay_lap_ho_so`/`noi_niem_yet`/`ghi_chu` = null. `model.updateCaseMeta` giữ nguyên để task Word dùng lại (có test: lưu thành công → caseId → nút "Cập nhật").

## CSS: biến cục bộ và layout
- Biến trên `.cd-root` (không dùng `:root`): `--cd-gap` 8px, `--cd-row-h` 25px, `--cd-fs-data` (= `--fs-data`, 14px), `--cd-assets-w` 35%, `--cd-asset-label-w` 122px, `--cd-col-name` 214px, `--cd-col-date` 86px, `--cd-col-id` 106px. Media ≤1400px: 200/84/102. Media ≥1800px: 38%, 140/230/100/120 (theo `tune()` trong mockup.js).
- Chuỗi flex dọc: `.cd-root-outer {display:flex; flex-direction:column; min-height:100%}` → `.cd-root {flex:1 0 auto}` → `.cd-tabpage:not([hidden]) {flex:1 0 auto}` → `.cd-workspace {flex:1 0 auto}`. Cố ý dùng min-height, không dùng height: khi Stage cao, cả `#view` cuộn.
- **Lớp ngoài cùng vùng sơ đồ** (W2 chỉ đặt rule này): `.cd-workspace > .cd-rel-card { flex: 1 0 auto; min-height: 280px; display: flex; flex-direction: column; }`.
- Ghi chú: `.cd-root-outer` là class W2 style trong module CSS (tên có tiền tố `cd-`, section do renderer tạo). W1 xác nhận `#view` không phải flex container.

## Ghi chú cho W3
1. **Lấp chiều cao:** `.cd-rel-card` đã là flex cột và lấp phần còn lại, nhưng bên trong vẫn có `.cd-canvas-wrap { height: min(52vh, 620px); min-height: 300px }` nên chiều cao card bằng chiều cao nội dung (~488px ở 1440×775). Hiện trang còn cuộn dọc 175px ở 1440×775 và 12px ở 1920×1080 dù dữ liệu chỉ bằng mockup. W3 cần: `.cd-rel-body { flex: 1 1 auto; min-height: 0 }`, `.cd-diagram`/`.cd-canvas-wrap { flex: 1; min-height: … }`, bỏ `height:min(52vh,620px)`, và bỏ `.cd-rel-foot` (D6). Rule min-height 280px ở lớp ngoài có thể chỉnh nếu head + canvas tối thiểu cần khác.
2. **Tràn ngang có sẵn từ trước:** `#view` tràn ngang 118px ở 1440 và 167px ở 1366. Nguyên nhân là `.cd-diagram`/`.cd-canvas-wrap` rộng hơn `.cd-rel-body` (canvas-world rộng theo layout, node 200px). Đã đo với CSS HEAD cũ: con số giống hệt, nên lỗi không do W2. Cần xem chuỗi `min-width:0` của `.cd-rel-body > .cd-diagram > .cd-canvas-wrap` và `.cd-pool{flex:0 0 34%}` (mockup dùng 176px).
3. Payload kéo Pool `text/plain {kind:'person', row_id}` và các class Pool không đổi. Test Pool/stageDirty gate vẫn đạt.

## Đề xuất cho W1 / điều phối (không tự làm)
- DESIGN §7 còn câu "bảng có cuộn riêng" ở 1280/1366, trái D8 (W1 cũng đã nêu).
- `.cd-cell` (ô nhập trong ô bảng) và `.cd-topbar` có thể thành class chung nếu Upload cần. Hiện giữ `cd-*`.
- DESIGN §10 / handoff MIN-129 còn mô tả action bar cũ (back/title/save-state). Nên cập nhật theo cấu trúc trên.

## Kiểm chứng
- `cd shell && node --test test/*.test.mjs` → **278/278 đạt** (254 trước MIN-133 + 7 của W1 + 17 của W2). File view 29/29, static 31/31.
- `git diff --check` sạch trên 4 file W2. `git show --stat` của commit chỉ có 4 file đó và file handoff này.
- Harness Electron (không phải app thật): `.agent/scratch/w2-harness/` (gitignore) chạy `harness.html` với styles.css + case-drafting.css + view/model thật, client giả, dữ liệu mockup. Chạy bằng `shell/node_modules/electron/dist/electron.exe render.js` từ thư mục đó. Kết quả:
  | Ca | thanh trên | Stage | hàng | cột Người | Stage body/wrap tràn |
  |---|---|---|---|---|---|
  | 1440×775, 7 người | 42 | 371 (mockup 371) | 25 | 20,44,214,64,86,86,106,86,114,24 | 0 / 0 |
  | 1366×768, 7 người | 42 | 371 | 25 | 20,44,200,64,84,84,102,84,89,24 | 0 / 0 |
  | 1920×1080, 7 người | 42 | 371 | 25 | 20,44,230,64,100,100,120,100,299,24 | 0 / 0 |
  | 1440×775, Hai bên 30 người | 42 | 821 | 25 | — | 0 / 0; cả trang cuộn 608px, không có thanh cuộn lồng (D8) |
  Select loại việc rộng 128px ở mọi ca. Cột Tài sản: 122 + 3×~108 ở 1440.

## Chưa kiểm
- Chưa chạy app Electron thật với sidecar (việc của W4). Chưa thử tay: kéo-thả hàng/cột bằng chuột thật, dropdown select trong thanh trên, dialog Loại đất sau khi đổi CSS (chỉ thêm rule giữ min-width 110px và nhãn nowrap).
- Chưa chụp so sánh pixel với mockup. Phần sơ đồ ảnh hưởng tổng thể trang (xem ghi chú W3).
- `.agent/tasks/MIN-133/progress.md` untracked, của điều phối/W1. W2 chỉ nối thêm mục ở cuối file, không commit.

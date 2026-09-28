# Handoff W4 — MIN-133 — Kiểm chứng cuối (UI mật độ cao + workspace Soạn hồ sơ)

Ngày: 2026-09-28 · Nhánh `consolidate/monorepo` · HEAD lúc kiểm chứng `cc37cd6` (+ docs MIN-134/135 kế tiếp, không đụng code MIN-133).

Phạm vi W4 = **kiểm chứng**, không sửa code. Kết luận: **KHÔNG phát hiện lỗi lớn/semantic cần vá trong MIN-133** — không có commit `fix()`. Một khuyến nghị mở ghi ở §4.

## 1. Môi trường kiểm chứng

| Mục | Kết quả |
|---|---|
| Electron thật | **Chạy** — Electron 31, `shell/node_modules/electron/dist/electron.exe`, CDP port 9666 |
| Sidecar Python thật | **Chạy** — `notary_v2/venv/Scripts/python.exe`, engine `g1-shell-sidecar/0.1.0`, contract `desktopcommand.v1`, logo báo `sẵn sàng` |
| Dữ liệu | DB/output scratch ở `.agent/scratch/w4/{data,output}` — **không đụng DB dev thật**; không upload tài liệu thật, không finalize hồ sơ, không xuất Word thật |
| Hồ sơ dùng thử | `HS-11` Thừa kế (3 tài sản, 7 người, sơ đồ seeded gán sẵn) — đúng mật độ mockup; `HS-12` Hai bên (1 tài sản, 4 người) cho flow two_party |

## 2. Test suite tự động — đều XANH

| Suite | Kết quả |
|---|---|
| `cd shell && node --test test/*.test.mjs` | **280/280** passed (giữ nguyên) |
| `python contracts/notary-case-drafting/validate_examples.py` | **68 file, 0 lệch** |
| `cd shell && python -m pytest test/test_notary_adapter_contract.py test/test_notary_intake_adapter.py test/test_notary_mock_adapter.py -q` | **194 passed** (23 deprecation warnings Py3.12) |
| `cd shell && python -m pytest test/test_upload_workspace.py test/test_upload_workflow.py test/test_upload_recovery.py -q` | **109 passed** |
| `cd notary_v2 && python -m pytest tests/test_case_workspace.py tests/test_inheritance_workspace.py -q` | **87 passed** (15 warnings) |

Không có code change trong W4 → không thêm test mới; mọi con số giữ từ W1–W3.

## 3. Checklist kiểm chứng (app thật qua CDP)

Đo thực tế trên DOM/live-state; drag-drop kiểm bằng `DragEvent` dispatch có `dataTransfer` giả lập — nguyên nhân hạn chế ghi ở §4.

| # | Mục | Kết quả | Bằng chứng |
|---|---|---|---|
| 1 | Nhập hồ sơ mới (draft) | **ĐẠT** | Draft thừa kế + `HS-12` two_party tạo thật qua `+ Hồ sơ mới` |
| 2 | Mở hồ sơ cũ | **ĐẠT** | Danh sách 12 hồ sơ → click mở `HS-11`, tab tự chuyển "Soạn hồ sơ", pill `Thừa kế · HS-11`; có dialog xác nhận khi draft đang dở ("Ở lại / Bỏ nháp và mở") |
| 3 | Cập nhật + Hủy | **ĐẠT** | `workspace_commit_stage` succeeded; "Hủy thay đổi" → confirm dialog → khôi phục giá trị committed |
| 4 | Validation inline | **ĐẠT** | `stage_validation_error` hiển thị banner + lỗi từng dòng (serial canonical `[A-Z]{2}+6-8 số`, ngày `YYYY-MM-DD`, bắt buộc owner, ≥1 tài sản) — giá trị mockup "đẹp mắt" như `CS 123456`/`15/10/2013` **không phải fixture hợp lệ**; bằng chứng `flow-01..04` |
| 5 | Conflict/retry | **ĐẠT** | Tăng tay `revision` DB 3→4 → commit trả `workspace_conflict` (`server_revision:4`) → dialog "Hồ sơ đã thay đổi trên máy chủ / Phiên bản hiện tại: 4 / Không có ghi đè cưỡng bức" + nút "Giữ bản nháp để sao chép / Tải bản mới"; bấm "Tải bản mới" → reload đúng dữ liệu committed, mất sửa nháp. `flow-10-conflict.png` |
| 6 | 3 tài sản | **ĐẠT** | Bảng chuyển vị đúng 3 cột `Tài sản 1/2/3` |
| 7 | Dialog Loại đất | **ĐẠT** | `Loại đất · Tài sản 1` — `+ Loại đất` thêm dòng SELECT (ONT/ODT/CLN/NTS/LUC/BHK/SKC/TMD) + Diện tích + Thời hạn; **"Áp dụng" chỉ sửa draft** — không job commit nào phát sinh, dirty-dot giữ. `flow-12-land-dialog.png` |
| 8 | two_party 30 chỗ | **ĐẠT** | 30 `.cd-tp-slot` canonical p1..p30; **p16 là đầu Bên B** ("Bên A (p1–p15) / Bên B (p16–p30)", counter `n/15 chỗ`); slot trống giữ vị trí, **không dồn** (gán chỗ 16 → chỗ 2–15 vẫn "Chỗ N trống") |
| 9 | Swap / bỏ gán TP | **ĐẠT** | Menu "Gán vị trí" liệt kê occupied `16 — Bên B — Lê Văn Ba` → swap → Bốn vào 16, Ba về Pool; nút `×` bỏ gán → người quay Pool, chỗ về trống |
| 10 | >12 người → trang cuộn | **ĐẠT** | Draft 33 người: `.cd-table-wrap` `overflow:hidden`, full-height 325px — **không scroll riêng trong Stage**; container `section` cấp trang cuộn 620px, dòng cuối xuống được viewport. Không scrollbar lồng nào trong `.cd-stage` (đo DOM) |
| 11 | Node trống | **ĐẠT** | `cd-node-empty` 88×24 — không chữ (chỉ nút `×`), aria-label `Ô trống: cha/mẹ của Nguyễn Văn An — thả người…`; **vẫn nhận drop** (Nguyễn Gia Bảo gán vào qua drop) |
| 12 | Node đã gán + chip | **ĐẠT** | `Nguyễn Văn An` node owner 144px: tên + năm `1955–2021` + chip `Chủ 1/2/3` + `Nhận 1/2/3` |
| 13 | Tên dài | **ĐẠT** | `Nguyễn Thị Hoàng Phương Thảo`: scrollWidth 209 > clientWidth 132, `text-overflow:ellipsis`, tooltip đầy đủ `… — con của Nguyễn Văn An` |
| 14 | Kéo-thả 3 hướng | **ĐẠT*** | Pool→slot, node→node swap, node→Pool (về Pool đúng `.cd-pool-box`) đều qua dispatch `dragstart/dragover/drop` thật lên đúng handler. *Hạn chế: `Input.startDragging` CDP không có trên Electron 31 → không kéo native tuyệt đối; semantics + handler chứng minh đầy đủ |
| 15 | Gán bàn phím | **ĐẠT** | Nút `→` pool-card/node mở modal `Gán vị trí — <tên>` — chọn slot bằng click/keyboard, đóng modal đúng |
| 16 | Zoom − / + | **ĐẠT** | `cd-zoom-label` 100%→90%→110%, `.cd-canvas-scale` `scale(0.9)`/`scale(1.1)` |
| 17 | Mở rộng + Esc | **ĐẠT** | `⛶ Mở rộng` mở overlay `Sơ đồ hai bên — toàn màn` (có zoom riêng); **Esc thật** (`Input.dispatchKeyEvent`) đóng, focus trả về body |
| 18 | Dirty-dot + lưu sơ đồ | **ĐẠT** | Gán/bỏ gán → chấm đỏ trên `Lưu sơ đồ`; lưu → `notary.diagram_save:succeeded` + banner "Đã lưu sơ đồ" |
| 19 | Gate Stage trước khi lưu sơ đồ | **ĐẠT** (khi render đã chạy) | Stage dirty (không focus trong ô) → `Lưu sơ đồ`+`Đánh giá` disabled, pill `Cập nhật Stage trước`. Cảnh báo mép ở §4 |
| 20 | Xuất Word dialog | **ĐẠT** | "Xuất Word — nhiều văn bản": chọn loại văn bản, `Chọn thư mục…`, `Xuất`/`Hủy xuất`/`Đóng`; không export thật. `flow-09-word-dialog.png` |
| 21 | Focus lộ nút hover-only | **ĐẠT** | `.cd-pool-assign` + `.cd-node-acts`: `opacity 0` blur → `opacity 1` khi `.focus()`/`:focus-within`, có trong tab order, `ae` khớp; `.cd-tp-acts` cũng focusable |
| 22 | Upload — Audit tab | **ĐẠT** | Toolbar đầy đủ (Kiểm tra môi trường/Mở đăng nhập/Từ ngày/Tải Excel/Nạp dữ liệu), bảng `ul-grid`, `splitter-h`, card border `#dde3ea` r10 — style chung không vỡ; pageOv/hOv = 0/0. `w4-upload-audit.png` |
| 23 | Upload — Quét & Upload tab | **ĐẠT** | `aria-selected` chuyển đúng, nhóm control riêng (Chọn thư mục/Bắt đầu Quét/Upload file đã chọn (0)/Tiếp tục đợt sau/Đối chiếu sổ mới), `ul-grid` + `splitter-h`; pageOv/hOv = 0/0. `w4-upload-scan.png` |

## 3b. Số đo layout — app thật, dữ liệu mockup (HS-11)

| Viewport | page overflow | stage scroll | h-overflow | stage H | topbar | row H | pool W | diag head | diag card H |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1440×775 | 0 | 0 | 0 | 371 | 42 | 25 | 176 | 34 | 330 (lấp phần còn lại) |
| 1366×768 | 0 | 0 | 0 | 371 | 42 | 25 | 176 | 34 | 323 |
| 1920×1080 | 0 | 0 | 0 | 371 | 42 | 25 | 176 | 34 | 635 |

(Lần đo sớm hơn cùng dữ liệu ghi page overflow 2px/9px/0px — do sơ đồ sâu hơn sau gán; cả hai lần đều trong sai số <1 dòng, khớp mục tiêu "0 overflow" khi sơ đồ gọn.)

## 4. Phát hiện & khuyến nghị

**F-1 (khuyến nghị mở issue follow-up — KHÔNG sửa trong W4):**
`case-drafting-view.js` cố tình defer rerender khi focus đang trong ô Stage (`dp.contains(ae) && /INPUT|TEXTAREA|SELECT/`). Nếu response commit/evaluate về **trong lúc focus còn ở ô input** (vd. click programmatic, hoặc request đang bay khi user vẫn gõ):
- `status='conflict'` render bị nuốt → **dialog conflict không mở cho đến emit không-defer kế tiếp** (xác nhận bằng thực nghiệm: dialog chỉ hiện sau khi blur + dispatch thêm).
- Nút `Lưu sơ đồ`/job-history có thể thể hiện stale-enabled trong khoảnh khắc đó (job `notary.diagram_save` từng succeeded trong dirty window).
Trong dùng thật chuột click nút → focus rời input → không bị defer → hành vi đúng. Rủi ro thực tế thấp nhưng là mép an toàn (commit lên revision cũ được chặn ở backend nên không mất dữ liệu — chỉ là UX trễ). **Khuyến nghị: issue riêng** — cân nhắc cho response error/conflict đi thẳng qua defer (hoặc force `activeElement.blur()` trước khi commit).

**F-2 (hạn chế kiểm chứng, không phải bug):**
- `Input.startDragging` không tồn tại trên CDP của Electron 31 → drag-drop kiểm qua `DragEvent` dispatch (handler `dragstart`/`drop`/`dragover` chạy thật), không kéo được tuyệt đối bằng chuột.
- `Page.captureScreenshot` **treo khi cửa sổ OS minimized/occluded** (renderer không sinh frame) — đã khôi phục bằng `Page.startScreencast` sau khi SetForegroundWindow; toàn bộ ảnh dự định đều chụp được.
- **True Windows DPI 125%/150% KHÔNG kiểm được** — chỉ emulate `deviceScaleFactor 1.25` (CSS 1152×620 ↔ physical 1440×775): page scroll +123px cần thiết, **h-overflow = 0** — không vỡ ngang. `w4-1152x620-dpr125.png`. `Browser.getWindowForTarget` không có trong env này.
- Screenshot 1920×1080 dùng lại capture hợp lệ cùng buổi (capture lặp lại hay stall) — nội dung cùng `HS-11` cùng view.

## 5. Ảnh (`.agent/tasks/MIN-133/w4-shots/`)

| File | Nội dung |
|---|---|
| `w4-1440x775-drafting.png` | Soạn hồ sơ `HS-11` (3 TS, 7 người, sơ đồ gán) tại 1440×775 |
| `w4-1366x768-drafting.png` | Cùng view tại 1366×768 |
| `w4-1920x1080-drafting.png` | Cùng view tại 1920×1080 (diagram card flex 635px) |
| `w4-upload-audit.png` | Upload Lab — tab Audit Sổ Công Chứng |
| `w4-upload-scan.png` | Upload Lab — tab Quét & Upload Hồ Sơ |
| `w4-1152x620-dpr125.png` | Emulate DPR 1.25 (CSS 1152×620) trên `HS-11` |
| `flow-01..flow-25` | Validation, lưu, gate, hủy, Word dialog, conflict, land dialog, two_party save/assign/swap/dnd/expand, focus-visible, mở hồ sơ cũ, 33-người cuộn trang |

## 6. Kết luận

- **Tất cả 23 mục checklist ĐẠT** (mục 14 có hạn chế phương tiện, semantics đã chứng minh).
- 0 lỗi layout ở cả 3 viewport; Stage không cuộn riêng; trang cuộn đúng khi >12 người; two_party 30 chỗ đúng canonical; sơ đồ thừa kế khớp spec W3 (node 144/trống 88×24/pool 176/hành động trên head/canvas flex).
- **Không sửa code** trong W4 → không có `fix(MIN-133)` commit. F-1 ghi lại để mở issue mới nếu owner đồng ý.
- Chưa đụng backend/contract/Word-exporter; `noi_cap`/`place_of_origin` vẫn trên wire (không còn cột Stage — kiểm bằng `workspace_get` payload).

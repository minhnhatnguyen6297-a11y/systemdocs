# Handoff — MIN-130

Viết khi kết thúc phiên hoặc chuyển giao cho agent/người khác.

## Trạng thái khi bàn giao — 2026-09-28
P7 đã xong: sơ đồ thừa kế + sơ đồ hai bên theo bản mẫu đã implement,
test P7 đầy đủ, toàn bộ shell test xanh. Commit:

- `9795e1e` `feat(MIN-130): P7 — sơ đồ thừa kế + hai bên theo bản mẫu`
  (4 file: JS + CSS + dom-stub + test mới).
- Commit docs kèm theo: task record này (`brief/progress/decisions/
  handoff`) — xem `git log -1` sau commit này.

Linear MIN-130: cập nhật trạng thái trên Linear là bước của người/agent
điều phối — không tự chốt.

## File đã đổi
- `shell/src/renderer/notary/relationship-diagram.js` — viết lại vùng
  diagram: canvas world×zoom + pan + overlay Mở rộng; inheritance card
  gọn + 2 hàng chip độc lập + SVG edges; two_party 30 chỗ canonical;
  `applyRequiredSlots()` theo engine; debounce evaluate chỉ
  inheritance. Pool + payload P6 giữ nguyên.
- `shell/src/renderer/notary/case-drafting.css` — block `cd-*` sơ đồ
  mới; xoá `.cd-edges`, `.cd-node-id`, `.cd-tp-sub`, `.cd-diagram-body`,
  `.cd-nodes`, `.cd-edge-*` cũ.
- `shell/test/dom-stub.mjs` — `setAttribute` sync `class`/`data-*`,
  `scrollLeft` init (đúng DOM thật; SVG bắt buộc setAttribute class).
- `shell/test/notary-diagram.test.mjs` (mới) — 15 case P7.
- `case-drafting-view.js` — KHÔNG sửa (wiring P6 đã đủ).

## Cách verify
- `cd shell && node --test test/*.test.mjs` → kỳ vọng 254/254 pass
  (15 case mới ở `notary-diagram.test.mjs`).
- `git diff --check` → sạch. `git show --stat 9795e1e` → chỉ 4 file
  sở hữu.

## Việc còn lại / rủi ro
- P8/P9 (MIN-131/MIN-132) tiếp nối: sơ đồ dùng `model.*` + engine
  `requiredSlots` — nếu contract đổi shape requiredSlots thì chỉ
  `applyRequiredSlots()` cần chỉnh.
- Model gap đã ghi: `seedDiagramSlots`/`newTwoPartyState` chỉ export
  module-level (view gọi qua `window.G1_NOTARY_MODEL`); `pool()` của
  model dùng stage cho draft — view tự tính committed-only từ
  `state.committed`. Nếu P9 refactor model, expose `committedPool()` +
  touch-only API sẽ sạch hơn (workaround hiện tại hoạt động đúng).
- Test chạy trên DOM stub — chưa verify visual thật trong Electron
  (không có harness UI). Kiểm tra tay nên làm ở P9 acceptance.
- Zoom/pan không có unit-test hành vi con trỏ thật (stub không mô
  phỏng layout); logic scroll đã test qua dispatch event.

## File tạm đã dọn
- Không tạo file scratch/log nào trong phiên; `../electron.exe -
  Shortcut.lnk` và `../nul` là file ngoài repo, không đụng.

# Handoff — MIN-136

**Trạng thái:** implement xong, test + harness Electron xanh. **2026-09-28.**

## Kết quả

Luồng sơ đồ đơn node + sửa trọn bộ lỗi nghiệm thu owner báo sau MIN-133 +
danh mục lỗi liệt kê rule ẩn. Không đụng contract/backend/Word/30 slot
two_party/legacy 7-slot.

## Đọc gì

- `brief.md` — phạm vi. `decisions.md` — D1–D7 (quyết định owner + kỹ thuật).
- Code: `shell/src/renderer/notary/{error-catalog,case-drafting-model,
  relationship-diagram,case-drafting-view}.js`, `case-drafting.css`,
  `index.html`. Tests: `shell/test/notary-*`.

## Bằng chứng

- `node --test test/*.test.mjs` trong `shell/` → **292/292**.
- Harness `.agent/scratch/w2-harness/render.js` (Electron thật, mock client):
  canvas flex-fill + căn giữa ở 3 viewport; Pool chỉ người; hint chủ đất
  sống; two_party 30 slot; không tràn ngang. Ảnh: `shots/`.

## Lưu ý cho người tiếp

- **Không khôi phục** `seedDiagramSlots`/`ensureEmptyChildSlot` — quyết định
  owner: node phụ chỉ sinh từ engine `requiredSlots`. Case cũ 7 slot vẫn
  render vì nodes đọc từ persisted state, không qua seed.
- Chủ đất sống không spawn nhánh — đúng nghiệp vụ; UI chỉ hint "điền Ngày
  mất". Nếu muốn spawn trước cây cho chủ đất sống → đổi rule engine
  (`active_estate`), phạm vi contract riêng.
- 2 regression guard mới trong static test: (a) trùng top-level identifier
  giữa các `<script>` classic — bug `errText` làm sơ đồ `module_missing`;
  (b) cân bằng `/* */` trong CSS — comment `*/` giữa dòng từng nuốt rule
  `.cd-diagram` (tồn tại từ MIN-129, lộ khi sơ đồ còn 1 node).
- `date.today()` của sidecar = ngày máy local cho `ngay_lap_ho_so` — theo
  thiết kế offline; máy sai giờ thì sai theo, user tự đối chiếu.
- Linear MIN-136 lúc tạo ở Backlog; kết nối Linear tạm lỗi khi cập nhật —
  chuyển Done khi owner nghiệm thu.

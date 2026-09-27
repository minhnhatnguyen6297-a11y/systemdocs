# Handoff — MIN-126

Viết khi kết thúc phiên hoặc chuyển giao cho agent/người khác.

## Trạng thái khi bàn giao — 2026-09-28

**Xong** phần bản mẫu P3 — chờ owner mở `index.html` duyệt và chốt các quyết
định mở. Linear MIN-126 nên chuyển sang review sau khi owner xác nhận.

Commit: `0939840` trên `consolidate/monorepo` — 40 file, chỉ
`docs/product/ui/prototypes/` + `.agent/tasks/MIN-126/`. Không push.

> Lưu ý lịch sử: commit đầu `422b8c8` bị race với worker P2 (đã lấy file họ
> đang staged) — đã reset và commit lại sạch. Worker P2 sau đó amend
> `78a557f` (MIN-124) thành `ae2ac2d` — nội dung MIN-124 còn nguyên, message
> commit đổi sang MIN-125. Việc đó thuộc P2 xử lý, không đụng ở đây.

## File đã đổi

- `docs/product/ui/prototypes/index.html` — shell + thanh điều khiển demo
  (module/scenario/flags/viewport).
- `docs/product/ui/prototypes/prototype.css` — toàn bộ style; token ánh xạ tay
  từ `tokens.json` (proposed) vào CSS var.
- `docs/product/ui/prototypes/data.js` — dữ liệu giả deterministic: 6 kịch bản
  Notary + 3 kịch bản Upload.
- `docs/product/ui/prototypes/app.js` — helper DOM, modal (focus trap + trả
  focus), toast, rail, thanh demo, snapshot/restore scroll.
- `docs/product/ui/prototypes/notary.js` — Stage (Tài sản chuyển vị + Người),
  Pool + sơ đồ thừa kế + hai bên 30 chỗ, dialog Loại đất/Nhập file/conflict/
  Word-stub, splitter, zoom, Mở rộng.
- `docs/product/ui/prototypes/upload.js` — tab Audit + Quét & Upload (giữ
  state), KPI, 2 bảng audit chia được, queue 6 cột, các banner trạng thái.
- `docs/product/ui/prototypes/README.md` — cách mở, bản đồ trạng thái, kích
  thước đã kiểm, giới hạn, danh sách quyết định chờ chốt.
- `.agent/tasks/MIN-126/{brief,progress,decisions,handoff}.md` +
  `screenshots/` (29 ảnh PNG).

## Cách verify

- Mở `docs/product/ui/prototypes/index.html` bằng Chrome/Edge (file:// được —
  không dùng ES module).
- Hoặc `python -m http.server` trong thư mục đó.
- Re-run check tương tác (cần venv có playwright — dùng `notary_v2/venv`):
  `notary_v2/venv/Scripts/python.exe .agent/scratch/p3_test.py` → 18/18 PASS.
  (script ở scratch — đã xóa theo quy ước; nội dung test nằm trong git log/
  handoff này nếu cần tái tạo).

## Việc còn lại / rủi ro

- **Owner duyệt trên bản mẫu** + chốt 12 mục mở trong `decisions.md` (chip số,
  swap-on-drop, phạm vi Hủy, Apply loại đất, Mở rộng, rail vs sidebar,
  breakpoint, 30 chỗ, token, focus dialog, toast retryable, Zalo disabled).
- Windows scale 125%/150% **chưa kiểm thật** — chỉ mô phỏng viewport
  1536×864 / 1280×720; cần owner mở thật nếu muốn xác nhận DPI.
- Edge sơ đồ vẽ tay (bus dọc+ngang) — P7 (MIN-130) sẽ dùng layout thật; bản
  mẫu chỉ để duyệt bố cục.
- Song song: worker P2/MIN-125 đang sửa `contracts/` + docs Notary — khi
  merge, P4 cần đối chiếu lại tên field/pill state cho khớp contract mới.

## File tạm đã dọn

- `.agent/scratch/p3_shot.py` + `p3_test.py` — đã xóa sau khi chụp/test xong
  (scratch không commit).

# Decisions — MIN-111

Chỉ ghi quyết định **trong phạm vi task** đã được chốt (bởi user/owner hoặc
theo spec đã duyệt). Quyết định xuyên sản phẩm hoặc câu hỏi mở: **không** tự
chốt ở đây — đưa lên `docs/architecture/OPEN_DECISIONS.md`.

## 2026-09-26 — Model/view tách; model pure + inject client
- **Chọn:** `case-drafting-model.js` pure state machine (không DOM, UMD),
  nhận `client.run(command, payload)` inject; `case-drafting-view.js` render
  thuần từ `model.state`; seam runtime `makeCommandRunner` trong renderer.js
  (submit → awaitJob → {ok,data}|{ok,error}).
- **Lý do:** test được bằng node --test không DOM; MIN-112 chỉ cần thay
  client thật; mock chạy ngay qua G1_DEV_NOTARY_MOCK.
- **Loại bỏ:** gọi `window.desktop` trực tiếp trong model (không test được,
  vi phạm ràng buộc "model no DOM").

## 2026-09-26 — 'document-review' giữ làm id kỹ thuật compat
- **Chọn:** registry giữ module id `document-review` (title notary_v2);
  `NAV_SPEC` dùng id mới `notary_v2` + `aliases: ['document-review']`;
  `navEntry` resolve alias → cùng entry.
- **Lý do:** nghiệm thu yêu cầu giữ `document-review` ID tương thích một
  chu kỳ; command `notary.*` route qua registry không đổi.
- **Loại bỏ:** đổi id registry luôn (gãy moduleForCommand/deep link cũ).

## 2026-09-26 — 'Excel → Word' rời nav chính, module registry giữ
- **Chọn:** bỏ mục nav `excel-word`; module `excel-word` (namespace `word`)
  giữ trong registry cho compat — chưa xóa command cũ.
- **Lý do:** nghiệm thu "Bỏ Excel → Word khỏi nav chính; chưa xóa command cũ".
- **Loại bỏ:** xóa module khỏi registry (command word.* sẽ gãy sớm).

## 2026-09-26 — 'Tổng quan' cũ gộp vào 'Trạng thái/Cài đặt'
- **Chọn:** module-health + job list (trước ở Overview) render trong view
  Status; bỏ mục nav `overview`; default module `notary_v2`.
- **Lý do:** taxonomy mới chỉ có 3 module nghiệp vụ + 2 tiện ích; nội dung
  Overview vốn là health/jobs — đúng ngữ nghĩa Status.
- **Nguồn:** UX spec MIN-104 §1 + nghiệm thu MIN-111.

## 2026-09-26 — Zalo ra khỏi registry; zalo.* → command_unknown
- **Chọn:** bỏ namespace `zalo` khỏi module document-review; bỏ Zalo section
  trong view; `zalo.status` nay bị submitCommand từ chối (command_unknown).
- **Lý do:** Zalo tách thành module độc lập (MIN-103); nghiệm thu cấm Zalo
  trong nav/registry surface của task này.
- **Lưu ý:** nếu lát cắt cần gọi zalo.* trước khi MIN-103 xong thì phải mở
  lại namespace — đã ghi trong handoff.

## 2026-09-26 — devQuickOpen sau flag G1_DEV
- **Chọn:** input số hồ sơ + nút mở fixture nhanh chỉ render khi
  `window.G1_DEV === true` (đặt tay trong DevTools).
- **Lý do:** cần cách mở workspace demo/mock nhanh cho dev mà nghiệm thu
  cấm "nhập ID tay trong production view".

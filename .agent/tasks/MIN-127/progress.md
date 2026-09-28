# Progress — MIN-127

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: đang làm — 2026-09-28

## Đã làm
- Đọc toàn bộ nguồn: AGENTS.md, plan MIN-123, DESIGN/EXPERIENCE/tokens,
  prototypes (index/css/js), decisions MIN-126 (12 đề xuất = đã duyệt hết),
  visual-design hai module, spec_UI upload, code shell hiện trạng
  (styles.css 142 dòng, renderer.js 836, lib.js 198, index.html 41).
- Baseline test: `node --test test/*.test.mjs` @ 5f1de32 → **197/197 pass**.
- Xác định ràng buộc test: `min-height: 44px` + `:focus-visible` trong
  styles.css; `#view section` giữ cap 860px; index.html giữ thứ tự script.

## Đang làm dở
- Viết brief.md + progress.md (file này), chuẩn bị rewrite styles.css.

## Bước tiếp theo
1. tokens.json → approved + banner docs.
2. Rewrite styles.css (token vars + rail + shared classes).
3. index.html + renderer.js chrome (rail icon, modal, toast, face, pill).
4. components.html + DESIGN.md §10 (phạm vi/tên lớp cho P6/P7/P8).
5. Test + commit theo nhóm file nhỏ.

## Check đã chạy
- `node --test test/*.test.mjs` @ baseline → 197 pass, 0 fail (27.4s).

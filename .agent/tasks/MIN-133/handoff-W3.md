# Handoff W3 — MIN-133: Sơ đồ (D6, D7, D9 + lấp chiều cao/hết tràn)

**Trạng thái:** xong (code + test + đo 3 viewport). Worker gốc chết giữa
chừng (hết quota) sau khi viết phần JS; coordinator hoàn thành phần còn
lại và sửa 1 bug edge trùng trong code worker.

## Commit

- `feat(MIN-133): W3 — sơ đồ mockup: node 144/ô trống 88×24, nút lên head, canvas flex`

## File đổi

| File | Nội dung |
|---|---|
| `shell/src/renderer/notary/relationship-diagram.js` | Hằng layout mới; layout mới (hàng căn giữa, cặp vợ/chồng 28px); node trống D7; nút Lưu sơ đồ/Xuất Word lên head (D6), bỏ `.cd-rel-foot`; edges không mũi tên + 1 edge từ giữa đoạn vợ/chồng; Pool card gọn, nút → hiện khi hover/focus; slot hai bên gọn |
| `shell/src/renderer/notary/case-drafting.css` | Viết lại phần relation/canvas/node/two-party theo mockup; bỏ `.cd-rel-foot`, `cd-node-head/-role/-hint/-foot`; canvas-wrap `flex:1; min-height:0` (bỏ `height:min(52vh,620px)`); Pool 176px; lưới chấm canvas |
| `shell/test/notary-diagram.test.mjs` | Cập nhật test theo DOM mới + 2 test mới (D6 head buttons, D7 hằng/pos kích thước) — 17/17 |
| `docs/product/ui/DESIGN.md` | §7: Stage không cuộn riêng (D8); canvas flex |
| `docs/product/ui/tokens.json` | `size.chipPosition` 24px → `22x19px` (D7) |
| `notary_v2/docs/platform/case-workspace/visual-design.md` | ASCII + §3/§5/§6/§8/§9 theo D4–D9 (thanh trên, 7 cột, Pool 176, node mới, hành động trong head) |
| `.agent/tasks/MIN-133/w3-shots/` | 4 ảnh đo Electron thật (harness W2) |

## Hằng layout mới (relationship-diagram.js ~dòng 44)

```js
NODE_W = 144, NODE_H = 87        // node đã gán
EMPTY_W = 88, EMPTY_H = 24       // node trống (viền đứt, không chữ)
PAD = 6, GAP_X = 14, SPOUSE_GAP = 28, GAP_Y = 14
ROW_H = NODE_H + GAP_Y
// hai bên:
TP_COL_W = 288, TP_SLOT_H = 26, TP_SLOT_GAP = 4, TP_TITLE_H = 26
TP_W = 600, TP_H = 484 (tính từ hằng)
```

`layoutInheritance` trả `pos[id] = {x, y, w, h, gen}` — w/h theo trạng
thái node; hàng rộng nhất căn giữa, hàng còn lại bám tâm cha/me (dưới)
hoặc tâm con (trên). CSS `.cd-node` (144px) / `.cd-node-empty` (88×24)
phải khớp các hằng này — đổi kích thước thì sửa cả hai nơi.

## Node trống (D7)

- DOM: `.cd-node.cd-node-empty`, chỉ `.cd-node-acts` (nút × xóa slot).
- Không `.cd-node-name/-meta/-posrow` — không chữ trong ô.
- `role=group` + `aria-label="Ô trống: <vai trò> — thả người từ Pool vào đây"` + `title` — vai trò vẫn đọc được cho screen reader/bàn phím.
- `wirePersonDrop` giữ nguyên → vẫn là drop target.

## Node đã gán (D7)

- `.cd-node-name` (tên, ellipsis + title) → `.cd-node-meta` (năm sinh–mất
  + alloc badge) → 2 `.cd-posrow` `Chủ`/`Nhận` (chip 1|2|3, 22×19 CSS).
- `.cd-node-acts` nổi góc phải trên (→ gán lại, ↩ bỏ gán, × xóa slot) —
  `opacity:0`, hiện khi `:hover`/`:focus-within`; nút vẫn trong tab order.

## Edges

- Bỏ marker mũi tên + `edgeSeq` (không còn `<defs>`).
- `cd-edge-spouse`: đoạn ngang nét đứt giữa hai card cùng hàng.
- `cd-edge-parent`: elbow `M ox oy V busY H cx V y`; khi cha/me là một
  cặp vợ/chồng → **một** edge từ giữa đoạn vợ/chồng (dedupe theo điểm
  xuất phát — bug duplicate trong bản worker để lại đã sửa).

## Head actions (D6)

`.cd-rel-foot` bỏ hẳn. Trong `.card-tools` (sau cụm zoom/Mở rộng + vsep):
`Lưu sơ đồ` (`sm secondary` + dirty-dot, disable theo
`gate || caseId==null || !canWrite || !diagramDirty || !capabilities.diagram`)
và `Xuất Word` (`sm primary`, disable `!word_export || wordBusy`).
Gate `stageDirty` + pill "Cập nhật Stage trước" giữ nguyên.

## Số đo (harness Electron thật, view/CSS thật + client giả)

| Ca | page overflow h×w | Stage overflow | tràn ngang |
|---|---|---|---|
| 1440×775, 7 người, 3 tài sản | **0×0** | 0 | không |
| 1366×768 | **0×0** | 0 | không |
| 1920×1080 | **0×0** | 0 | không |
| 1440×775, two_party 30 người | **648×0** (trang cuộn — đúng D8) | 0 | không |

- rel-card: 330px @1440×775, 323px @1366, 635px @1920 — lấp phần còn lại.
- Tràn ngang trước đây (118px@1440 / 167px@1366, do Pool `flex:0 0 34%` +
  body không padding): **hết** — `wide[]` rỗng.
- Ảnh: `.agent/tasks/MIN-133/w3-shots/w2-{1440x775,1366x768,1920x1080}-inheritance-7.png`,
  `w2-1440x775-two_party-30.png`.

## Test

`node --test test/*.test.mjs`: **280/280** (trước W3: 278; +2 test mới
D6/D7, các test cũ cập nhật theo DOM mới — lý do ghi trong từng test).

## Chưa kiểm — dành cho W4

- Electron thật có sidecar (harness chỉ dùng client giả): drop kéo-thả
  thật lên node trống, swap, Mở rộng overlay, pan/zoom giữa lúc node nhỏ.
- >30 người thừa kế: canvas pan/cuộn (D9), node không co.
- Tên dài ở node 144px / slot hai bên (tooltip đã có — kiểm bằng mắt).
- Cửa sổ hẹp ≤900px: media query xếp dọc (Pool full rộng).
- DPI Windows thật 125%/150% — hạn chế chung toàn MIN-123.
- `cd-tp-acts`/`cd-node-acts` hiện bằng `:hover`/`:focus-within` — kiểm
  focus bàn phím trên Electron thật (stub không render CSS).

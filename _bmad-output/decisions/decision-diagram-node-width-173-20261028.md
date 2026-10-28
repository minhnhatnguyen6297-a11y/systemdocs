---
id: decision-diagram-node-width-173-20261028
title: "Node thẻ có người 173×87 — bỏ 144 vì cắt chip Chủ/Nhận"
date: '2026-10-28'
status: accepted
---

## Bối cảnh

Card `.cd-node` 144px + `overflow:hidden` (case-drafting.css) chứa 2 hàng chip
vị trí. Hàng chip cần 163px nội dung: nhãn 38 + 5 gap ×3 + 5 chip ×22.
Flex không co được `.cd-posrow-label` (`flex: 0 0 38px`), nên ép chip
22→15px; kèm `overflow:hidden` chip bị cắt mép, Playwright hit-test trượt —
`clickOwn` trong drafting-explore.cjs phải dùng `page.evaluate` + `el.click()`
để bấm hộ. Chiều cao 87 vẫn khớp: 2×(2 margin) + 2×19 chip + name 14/meta
13 — không đổi.

## Quyết định

`NODE_W` (relationship-diagram.js) và `.cd-node` width = **173px**
(163 + 2×5 padding). Không đổi `NODE_H`, không đổi `overflow:hidden`,
không đổi `.cd-poschip`/`.cd-posrow-label`.

Đã loại: giữ 144 + gỡ `flex: 0 0 38px` cho nhãn co — nhãn "Chủ/Nhận" cụt
chữ; giữ 144 + chip 15px — quá nhỏ để bấm, sai mockup MIN-133 D7.
Đã loại: bỏ `overflow:hidden` — che nội dung tràn bằng cách khác là mở rộng
phạm vi; tràn nội dung chiều ngang không còn sau khi rộng card.

## Phạm vi ảnh hưởng

- `shell/test/notary-diagram.test.mjs` MIN-133 D7 kỳ vọng 173.
- `_bmad-output/specs/notary_v2/README.md` dòng bố cục node 173.
- `tools/visual-bug-reporting/drafting-explore.cjs`: `clickOwn` bấm bằng
  Playwright locator thật (chip 22×19 thấy đủ, hit-test trúng); bỏ
  workaround `page.evaluate`.

## Bằng chứng

- Unit: `node --test test/notary-diagram.test.mjs` 39/39 pass.
- E2E explore: `clickOwn` chip rect 22×19 (trước đây bị ép/cắt), các ca
  X1/X2 pass bằng click thật.

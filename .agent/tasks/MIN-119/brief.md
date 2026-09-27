# MIN-119 — BUG/UX: Sơ đồ quan hệ mất thao tác kéo-thả

Linear: MIN-119 (parent MIN-68, Backlog). Làm sau MIN-122 model
(`movePerson` là nền).

## Scope (Linear)

- Pool person card kéo được khi `canWrite` — đã đúng, kiểm lại khi pool
  chỉ còn asset.
- **Diagram node kéo được** khi đã gán person: node→node = đổi slot
  (đích trống move / đích có người swap), node→Pool = bỏ gán. Draft-only,
  qua `model.movePerson` — không persist.
- Giữ keyboard `Gán vị trí…`.
- Pool là drop target cho node.

## Files

- `shell/src/renderer/notary/relationship-diagram.js` (draggable node,
  drop handlers, payload `{kind:'person', row_id, source_node_id}`)
- `shell/src/renderer/notary/case-drafting.css` nếu cần affordance
- Test: static + model test movePerson; verify headless CDP (case 47
  regression: pool rỗng person vẫn thao tác được).

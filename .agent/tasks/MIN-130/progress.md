# Progress — MIN-130

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: hoàn thành — chờ commit ghi nhận

## Đã làm
- Đọc rules + plan MIN-123, handoff P5/P6, contract §13, DESIGN/EXPERIENCE,
  tokens, prototype `docs/product/ui/prototypes/notary.js`.
- Đọc `case-drafting-model.js` (API v2 đủ: `movePerson` swap, `addSlot`,
  `setNodeRelation`, `toggleNodePosition`, `evaluateDiagram` → render_model
  có `requiredSlots`, `saveDiagram` round-trip).
- Đọc `notary_v2/services/inheritance_engine.py` `_validate_and_build_graph`:
  spouse 1 chiều hợp lệ (`other.spouseSlotId ∈ (None, node.id)`), parent
  ≤2, `hidden`/`deleted` loại khỏi active_people — layout không cần suy
  luận thêm.
- Viết lại `shell/src/renderer/notary/relationship-diagram.js` (P7):
  - canvas: `.cd-canvas-wrap` scroll+pan (kéo nền) + `.cd-canvas-world`
    kích thước logic×zoom + `.cd-canvas-scale` `transform: scale(zoom)`;
    zoom −/%/+ trong 0.5–1.6; overlay "Mở rộng" qua `openModal` (bare,
    Esc/× + trả focus) với canvas riêng đồng bộ qua `model.subscribe`.
  - inheritance: `layoutInheritance()` pure — gen = max(gen cha/mẹ)+1,
    cặp vợ/chồng dồn kề; card `.cd-node` gọn (tên, năm sinh–mất, vai
    trò hiển thị từ quan hệ draft, 2 hàng chip `Chủ đất`/`Nhận đất` =
    `ownPositions`/`receivePositions` độc lập, `aria-pressed`, chip >
    len(assets) disable); SVG edges từ `parentSlotIds`/`spouseSlotId`
    (cha-con elbow + mũi tên, vợ/chồng ngang dashed); `+ Slot`, `×`
    xóa slot (draft-only), `Bỏ gán`, nút `→` menu gán bằng bàn phím.
  - two_party: đúng 30 chỗ canonical p1..p30 — cột "Bên A (p1–p15)"
    / "Bên B (p16–p30)", p16 đầu B theo id (không theo Stage); card chỉ
    "Chỗ N" + tên; drop lên chỗ có người = `movePerson` swap; drop về
    Pool = `movePerson(row, null)`; chỗ trống giữ nguyên (không
    compact); không chip/quan hệ/evaluate.
  - `applyRequiredSlots()` sau evaluate OK: anchor phải có `personId`
    (mock dev emit cho slot trống → bỏ qua); `slotTypes` engine quyết
    định tạo father/mother/spouse/child; id mới theo pattern
    `<kind>_<anchor>`, không trùng (`freeId`); child nối về anchor +
    spouse kể cả khi spouse khai báo 1 chiều từ phía spouse.
  - Debounce evaluate 500ms sau mọi draft-mutation — CHỈ inheritance
    (`isTp()` return sớm); stageDirty gate giữ nguyên.
  - Payload kéo-thả giữ contract P6: `text/plain` = JSON
    `{kind:'person', row_id}`; parse lỗi → bỏ qua (không throw).
- CSS `cd-*` trong `case-drafting.css`: block canvas/node/chip cũ thay
  bằng `.cd-canvas-*`, `.cd-node*` (200px, drop-hint/dragging từ
  styles.css), `.cd-posrow`/`.cd-poschip`, `.cd-sides`/`.cd-side-col`/
  `.cd-tp-*`, `.cd-zoom`/`.cd-expand*`; xoá `.cd-edges`, `.cd-node-id`,
  `.cd-tp-sub`, `.cd-diagram-body`, `.cd-nodes`, `.cd-edge-*` cũ.
- `shell/test/dom-stub.mjs`: `setAttribute('class')` → sync `_cls`,
  `setAttribute('data-*')` → sync `dataset` (đúng DOM thật — cần cho
  SVG, vì `SVGElement.className` read-only), thêm `scrollLeft` init.
- Test mới `shell/test/notary-diagram.test.mjs` — 15 case P7 (xem mục
  Check đã chạy).

## Bug sửa trong phiên
1. `openExpanded`: `rebuildExpand()` bị `isConnected===false` chặn vì
   `openModal` build box TRƯỚC khi append vào DOM → overlay mở rỗng.
   Fix: build trực tiếp `expandBody.append(canvasEl())`; guard
   isConnected chỉ còn phục vụ rebuild từ subscribe.
2. `applyRequiredSlots` child: chỉ nối `anchor.spouseSlotId` → mất cạnh
   tới spouse khai báo 1 chiều ngược (spouse→anchor). Fix: tìm spouse
   qua cả `spouseSlotId` trên anchor LẪN `n.spouseSlotId === anchor.id`.
3. `tpSlotEl` render năm sinh phụ — design yêu cầu card hai bên CHỈ
   tên + số chỗ → bỏ `cd-tp-sub` (JS + CSS).

## Check đã chạy
- `cd shell && node --test test/*.test.mjs` → **254/254 pass** (gồm 15
  case P7 mới: seed 7 slot + edges, card trước/sau gán, chip độc lập,
  layoutInheritance pure, 30 chỗ/p16 đầu B/không compact, swap + về
  Pool, menu bàn phím 30 chỗ, requiredSlots tạo/bỏ qua anchor trống,
  zoom + Mở rộng overlay, pan scroll, 60 node, round-trip save→open
  inheritance + two_party, two_party không gọi evaluate).
- `git diff --check` → sạch.

## Bước tiếp theo
- Commit `--only` file sở hữu; ghi `handoff.md`; báo cáo hash + stat.

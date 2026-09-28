# Decisions — MIN-130

## 2026-09-28 — Sơ đồ hai domain trong một file, không framework
- **Chọn:** Viết lại `relationship-diagram.js` bằng DOM thuần —
  canvas world/scale + SVG edges cho inheritance, danh sách 30 chỗ
  canonical cho two_party. Không React/ReactFlow/layout lib.
- **Lý do:** Static invariant MIN-128 cấm React/ReactFlow/Bootstrap/
  Tailwind; bản mẫu `prototypes/notary.js` cũng là DOM thuần nên cấu
  trúc tương đương giữ đúng thiết kế đã duyệt.
- **Loại bỏ:** Port `ReactFlowApp.jsx` legacy — nó chứa luật thừa kế
  JS cũ, không có `requiredSlots`/v2 fields → chỉ dùng làm tham chiếu
  interaction, không port.
- **Nguồn:** brief MIN-123 P7 + static test `notary-case-drafting-
  static.test.mjs`.

## 2026-09-28 — Engine là SOT cho slot thiếu; view không suy luận luật
- **Chọn:** `applyRequiredSlots()` chỉ đọc `render_model.requiredSlots`
  sau evaluate OK và tạo slot trống theo `slotTypes`; bỏ qua anchor
  chưa gán người (mock dev emit cho slot trống — không nổ canvas).
  JS không tính phần/%, không phân biệt cha vs mẹ (`parentSlotIds` là
  tập cha/mẹ — engine cũng vậy), không validate luật (chu kỳ/conflit
  do engine báo qua `diagramErrors`).
- **Lý do:** contract §7/§13 — Python engine là SOT nghiệp vụ; JS chỉ
  presentation + tạo slot tương ứng quan hệ đã khai báo.
- **Loại bỏ:** Materialize cả cho anchor trống (mock `requiredSlots`
  cho node trống sẽ nổ canvas mỗi lần evaluate).
- **Nguồn:** `notary_v2/services/inheritance_engine.py`, contract
  §13.5, mock adapter `notary_v2_mock.py`.

## 2026-09-28 — Two_party 30 chỗ canonical, card chỉ tên + số chỗ
- **Chọn:** Render đúng `p1..p15` (Bên A) / `p16..p30` (Bên B) theo id,
  không suy ra từ thứ tự Stage; chỗ thiếu trong state → placeholder
  `deleted` (degenerate). Card chỉ "Chỗ N" + tên người — bỏ phụ đề
  năm sinh (spec: chỉ tên + số chỗ). Không chip, không edge, không
  evaluate.
- **Lý do:** Spec P7 — p16 luôn đầu Bên B; chỗ trống giữ nguyên vị
  trí (không compact) để ánh xạ giấy tờ ổn định; card hai bên tối
  giản theo design.
- **Loại bỏ:** Dùng `personYears`/chip row trên card hai bên (lẫn
  ngữ nghĩa inheritance).
- **Nguồn:** brief MIN-130 + `prototypes/notary.js` (15 chỗ/bên).

## 2026-09-28 — Zoom/pan thay vì co nhỏ; ≥60 node vẫn thao tác
- **Chọn:** Node giữ cỡ đọc được (200px); `.cd-canvas-wrap` scroll 2
  chiều + pan kéo nền (document listener đăng ký một lần) + zoom
  0.5–1.6 + overlay "Mở rộng" ~toàn màn.
- **Lý do:** Spec yêu cầu ≥60 node không ép nhỏ chữ; auto-fit sẽ làm
  chữ/chip không đọc được khi node nhiều.
- **Nguồn:** brief MIN-130 §interaction + prototype canvas.

## 2026-09-28 — DOM stub sync `class`/`data-*` qua setAttribute
- **Chọn:** `dom-stub.mjs` `setAttribute('class')` cập nhật `_cls`,
  `setAttribute('data-*')` cập nhật `dataset` camelCase, thêm
  `scrollLeft` init — khớp DOM thật.
- **Lý do:** Renderer bắt buộc `setAttribute('class')` cho SVG
  (`SVGElement.className` là `SVGAnimatedString` read-only); stub cũ
  không sync → test không tìm được `.cd-canvas-edges` dù markup đúng.
- **Nguồn:** MDN DOM behavior; cần cho test edges SVG P7.

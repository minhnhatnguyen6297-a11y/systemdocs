# Case workspace

Status: active
Source of truth: `../../../../docs/spec/notary_v2/` — cây spec sản phẩm; các file dưới đây là nguồn chi tiết/đối chiếu implementation
Read when: extracting or changing shared Stage/Pool mechanics across two or more business modules

- Current implementation is inheritance-first
- `drafting-tab.md` — chi tiết hành vi/dữ liệu đích Electron đã duyệt tại MIN-104; cây spec mới sở hữu bản hiện hành
- `visual-design.md` — lớp thị giác/bố cục đích của tab (MIN-124, hướng ảnh đã duyệt 27/09/2026; giá trị token proposed chờ duyệt). Chỉ thị giác — hành vi lấy `drafting-tab.md`
- `contract.md` — ghi chú cơ chế domain provisional, non-normative; không phải
  wire contract. Wire contract `desktopcommand.v1` của tab đã publish tại
  [`../../../../contracts/notary-case-drafting.md`](../../../../contracts/notary-case-drafting.md)
  (MIN-105, rev 1.1 MIN-121)
- Ngôn ngữ thị giác + thao tác dùng chung hai module:
  [`../../../../docs/spec/ui/`](../../../../docs/spec/ui/) (`README.md`,
  `tokens.json`, ảnh tại `../../../../docs/spec/ui/references/`)
- Do not extract a shared abstraction until a second real domain proves the contract
- Inheritance behavior remains in `docs/domains/inheritance/README.md`

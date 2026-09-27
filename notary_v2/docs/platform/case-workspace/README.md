# Case workspace

Status: active
Source of truth: `../../domains/inheritance/workflow.md` — hiện trạng web (`frontend/templates/cases/form.html`, fallback đến cutover); `drafting-tab.md` — đích Electron cho tab Soạn hồ sơ
Read when: extracting or changing shared Stage/Pool mechanics across two or more business modules

- Current implementation is inheritance-first
- `drafting-tab.md` — SOT hành vi/dữ liệu tab Soạn hồ sơ đích Electron (MIN-104, đã duyệt 24/09/2026)
- `visual-design.md` — lớp thị giác/bố cục đích của tab (MIN-124, hướng ảnh đã duyệt 27/09/2026; giá trị token proposed chờ duyệt). Chỉ thị giác — hành vi lấy `drafting-tab.md`
- `contract.md` — ghi chú cơ chế domain provisional, non-normative; không phải wire contract. Wire contract `desktopcommand.v1` của tab đã publish: `contracts/notary-case-drafting.md` (MIN-105, rev 1.1 MIN-121)
- Ngôn ngữ thị giác + thao tác dùng chung hai module: `docs/product/ui/` (`DESIGN.md`, `EXPERIENCE.md`, `tokens.json`, `references/`)
- Do not extract a shared abstraction until a second real domain proves the contract
- Inheritance behavior remains in `docs/domains/inheritance/README.md`

# Case workspace

Status: active
Source of truth: `../../domains/inheritance/workflow.md` — hiện trạng web (`frontend/templates/cases/form.html`, fallback đến cutover); `drafting-tab.md` — đích Electron cho tab Soạn hồ sơ
Read when: extracting or changing shared Stage/Pool mechanics across two or more business modules

- Current implementation is inheritance-first
- `drafting-tab.md` — SOT hành vi/dữ liệu tab Soạn hồ sơ đích Electron (MIN-104, DRAFT chờ owner duyệt)
- `contract.md` — ghi chú cơ chế domain provisional, non-normative; không phải wire contract. Wire contract `desktopcommand.v1` của tab sẽ là `contracts/notary-case-drafting.md` (MIN-105, chưa tồn tại)
- Do not extract a shared abstraction until a second real domain proves the contract
- Inheritance behavior remains in `docs/domains/inheritance/README.md`

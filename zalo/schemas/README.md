# schemas/ — vendored contract copies

Các file `*.schema.json` và `CONTRACT_REVISION` trong thư mục này là bản copy
**nguyên byte (byte-exact)** từ monorepo:

- Nguồn: `D:\systemdocs\contracts\zalo-intake\`
- Ngày vendor: 2026-09-25
- Revision: `zalo-intake-v1-draft` (xem `CONTRACT_REVISION`)

**READ-ONLY — không sửa ở đây.** Source-of-truth của contract nằm ở monorepo
(`systemdocs/contracts/zalo-intake/`). Muốn thay đổi contract: sửa và duyệt ở
monorepo theo `contracts/README.md`, rồi vendor lại toàn bộ thư mục này.

Chỉ có schema + `CONTRACT_REVISION` được vendor. `zalo-intake.md` (prose spec),
`_validator/`, `examples/` và `.gitattributes` của monorepo **không** được copy
vào đây — validator/examples của contract sống cùng SOT ở monorepo.

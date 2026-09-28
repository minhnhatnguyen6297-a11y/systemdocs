# Brief — MIN-127

**Linear:** <https://linear.app/minhnotary/issue/MIN-127/ui-p4-ap-dung-nen-giao-dien-va-thanh-phan-dung-chung-cua-electron> · **Ngày bắt đầu:** 2026-09-28 · **Nhánh:** `consolidate/monorepo` @ `5f1de32` — sửa/commit trực tiếp (owner chốt, không worktree).

## Mục tiêu
P4 của MIN-123: áp bộ token trắng/xanh đã duyệt vào shell Electron và tách
lớp thành phần dùng chung (button, ô nhập, card, bảng, dialog, toast, focus,
trạng thái) để P6/P7/P8 chuyển màn module mà không sửa chồng. Chi tiết yêu
cầu ở Linear — không chép lại vào đây.

## Phạm vi
- Repo: `shell/src/renderer/` (styles.css, index.html, phần chrome của
  renderer.js; lib.js trong vùng sở hữu nhưng không cần đổi nếu vocabulary
  giữ nguyên).
- `docs/product/ui/prototypes/components.html` — trang mẫu thành phần chung.
- `docs/product/ui/tokens.json` — meta.status `proposed` → `approved`
  (owner duyệt qua bản mẫu MIN-126, 27/09/2026) + banner trạng thái trong
  DESIGN.md/EXPERIENCE.md/README.md + hướng dẫn phạm vi CSS.
- `.agent/tasks/MIN-127/` — task record.
- KHÔNG sửa: `notary/*.js`, `notary/case-drafting.css`, `upload/*.js`,
  `upload/upload.css`, backend/sidecar/notary_v2/upload_lab (P5/P6/P7/P8).
- Git discipline: chỉ `git add`/`commit --only` trên file sở hữu; commit
  nhỏ; không amend/rebase commit của worker khác.

## Ràng buộc kỹ thuật phát hiện khi đọc code
- `shell/test/notary-case-drafting-static.test.mjs`: styles.css phải còn
  `:focus-visible` + literal `min-height: 44px` (vùng bấm — giữ ở rail-btn/
  nav 44px; nút/ô nhập theo token 36/38 đã duyệt).
- `shell/test/upload-routing.test.mjs`: `#view section` giữ
  `max-width: 860px` — module data-heavy thoát bằng class riêng
  (`cd-root-outer`, `.upload-lab`), không đổi cap chung.
- `.cd-root` đang bleed `margin: -20px -24px` theo padding `#view` — giữ
  nguyên padding 20/24 cho tới khi P6 viết lại (ghi trong handoff).
- `.slot` là marker unstyled của renderer.js + upload/index.js (vùng
  refresh); `.tools`/`.files`/`.muted`/`.error` cũng đang dùng — module CSS
  không được tái định nghĩa các tên này (ghi trong guide).

## Bằng chứng nghiệm thu
- Tại `shell/`: `node --test test/*.test.mjs` — 197/197 pass (baseline
  197 pass @ 5f1de32).
- Mở được `docs/product/ui/prototypes/components.html` (file://), các
  thành phần hiển thị đúng token.
- `git diff --check` sạch; `git show --stat` mỗi commit chỉ file sở hữu.

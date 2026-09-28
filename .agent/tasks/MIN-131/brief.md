# Brief — MIN-131

**Linear:** MIN-131 (phase P8 của MIN-123) · **Ngày bắt đầu:** 2026-09-28 · **Nhánh:** `consolidate/monorepo` (work trực tiếp, không worktree)

## Mục tiêu
Làm nhẹ hai màn hình Upload Lab (Electron renderer) theo bộ giao diện chung đã duyệt (P4/MIN-127): 2 tab gọn `Audit Sổ Công Chứng` + `Quét & Upload Hồ Sơ`, ưu tiên bảng dữ liệu, giữ nguyên mọi semantics nghiệp vụ và DOM hook mà test đang dùng.

## Phạm vi
- Repo/module ảnh hưởng: `shell/` — chỉ renderer Upload Lab.
- File dự kiến sửa: `shell/src/renderer/upload/{index.js,audit.js,scan-upload.js,upload.css}` + `.agent/tasks/MIN-131/*`. `state.js`/`client.js` chỉ động nếu chứng minh được defect giữ-state (ghi vào decisions).
- Ranh giới giữ nguyên: `styles.css`, `renderer.js`, `lib.js`, `index.html`, mọi `notary/*`, mọi `upload_lab/*`, backend/sidecar/selector, `.agent/tasks/MIN-128/` (worker khác).
- CSS: chỉ `ul-*` + scope `.upload-lab`; class không-tiền-tố (`.card .pill .banner .btn .grid .progress .splitter-* .toolbar .muted .small .truncate-path…`) dùng lại từ `styles.css`, không định nghĩa lại.
- DOM hook phải giữ (node + Python e2e đang dùng): `.ul-tablist`, `role=tab/tabpanel`, `#ul-panel-audit`, `#ul-panel-scan-upload`, `select.ul-site`, `.ul-site-url`, `.ul-badge-slot .ul-badge`, `.ul-login-confirm` (trong `.ul-notice` và audit panel), `.ul-env`, `.ul-src-msg .ul-error`, `.ul-audit-head`, `.ul-stale`, `.ul-kpi[data-kpi] .ul-kpi-v`, `.ul-table-wrap tbody`, `.ul-progress-label`, `.ul-reconcile(-text/-btn/-hint)`, `.ul-prepare-error`, `tr.ul-row-reconcile`, `tr.ul-row-issue`, `.ul-date`, `.slot` trên jobsBox. Text nút giữ nguyên (e2e `has-text`): 'Tải Excel từ Web', 'Chọn tệp Excel...', 'Nạp dữ liệu', 'Mở đăng nhập', 'Kiểm tra môi trường', 'Xác nhận đã đăng nhập', 'Xong kiểm tra', 'Chọn thư mục', 'Bắt đầu Quét', 'Dừng', 'Đóng browser upload', 'Tiếp tục…', 'Chọn tất cả', 'Bỏ chọn tất cả', 'Số thiếu trong Excel'.

## Bằng chứng nghiệm thu
- `cd shell && node --test test/upload-state.test.mjs test/upload-routing.test.mjs` — pass.
- Nếu sửa `state.js`/`client.js`: thêm `node --test test/*.test.mjs` + Python `test_upload_{workspace,workflow,recovery}.py` khi môi trường cho phép.
- `git diff --check` sạch; commit chỉ gồm file sở hữu (`git commit --only -- <paths>`), footer Devin.
- `handoff.md`: button map cũ→mới, states đã test, commit hash, điểm chưa verify.

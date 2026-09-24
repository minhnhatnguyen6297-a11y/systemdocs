# Decisions — MIN-104

Chỉ ghi quyết định **trong phạm vi task** đã được chốt (bởi user/owner hoặc
theo spec đã duyệt). Quyết định xuyên sản phẩm hoặc câu hỏi mở: **không** tự
chốt ở đây — đưa lên `docs/architecture/OPEN_DECISIONS.md`.

## 2026-09-24 — worktree base
- **Chọn:** Snapshot pending state từ main checkout vào worktree bằng sync commit `f966f74`, spec viết trên đó.
- **Lý do:** `document-intake/spec.md` trong pending state đã được viết lại theo quyết định owner 24/09; spec trên HEAD cũ sẽ mâu thuẫn với hướng đã duyệt.
- **Loại bỏ:** Commit pending changes lên `consolidate/monorepo` (side effect ngoài worktree, cần owner); spec trên HEAD cũ (mâu thuẫn hiện trạng).
- **Nguồn:** controller ruling — xem ledger `.superpowers/sdd/.../progress.md`

## 2026-09-24 — owner duyệt spec + quyết định mở
- **Chọn (owner):** (1) giữ công thức `Người không nhận` hiện tại `Tất cả − Chủ đất − Nhận` — spec.md §11.3 DRAFT nếu duyệt sau phải sửa cho khớp; (2) MIN-105 pin `is_dir:true` + absolute local path + cấm UNC cho directory FileRef; (3) chỉ commit thay đổi chung, mọi thứ Zalo không commit (Zalo đã chuyển repo riêng — `zalo/` + `D:\zalo-intake`; conflict git → tạo issue); (4) duyệt spec → merge + mở MIN-105.
- **Nguồn:** trả lời trực tiếp của owner trong phiên (1A, 2A, 3-custom, 4-duyệt).

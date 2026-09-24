# Decisions — MIN-105

Chỉ ghi quyết định **trong phạm vi task** đã được chốt (owner hoặc spec đã duyệt).

## 2026-09-24 — ràng buộc đã có từ MIN-104/owner
- `is_dir: true` + absolute local path + chỉ folder + cấm UNC cho directory FileRef (owner 2A).
- Công thức `Người không nhận` giữ hiện trạng (owner 1A) — contract chỉ mang dữ liệu, không khóa công thức nghiệp vụ (engine Python quyết).
- Không Zalo: contract không chứa command/field Zalo; `zalo.status` không liên quan.
- Schema version: `notary.case-drafting.v1` trên envelope `desktopcommand.v1`; `result.kind` theo command.

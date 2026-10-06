- source_plan: `D:/systemdocs/.agent/scratch/module-cleanup-plan-2026-09-25.md`
  summary: Thêm automated smoke test nối stage allowlist với dynamic import `upload_services`.
  evidence: Đã stage engine và import động ba service pass; hiện mới có smoke thủ công, chưa có test regression riêng.

- source_plan: `D:/systemdocs/.agent/scratch/module-cleanup-plan-2026-09-25.md`
  summary: Thêm automated smoke test cho standalone release và hai CLI regex sau khi copy.
  evidence: Bản standalone tạm đã build, chạy CLI và import service pass; chưa có test tự động giữ hành vi này.

- source_plan: `D:/systemdocs/.agent/scratch/module-cleanup-plan-2026-09-25.md`
  summary: Retire launcher/UI Qt cũ và frontend web cũ sau cutover Electron.
  evidence: `MIN-69 T10`/full packaged Windows E2E chưa có bằng chứng trong đợt này; giữ đường lui để không làm mất khả năng rollback.

- source_plan: `D:/systemdocs/_bmad-output/implementation-artifacts/plan-notary-v2-docs-consolidation.md`
  summary: Owner rà nội dung 38 file notary_v2 cũ với spec đã gom trước khi phê duyệt các Draft thừa kế.
  evidence: Mapping nguồn-đích và trạng thái đã ghi trong handoff; test chỉ xác nhận cấu trúc/liên kết, không thể chứng minh tương đương nghiệp vụ từng đoạn.

## Deferred from: code review of task5-regex-hop-dong-word (2026-10-06)

- Test file thật (D:\Minh...) skip ngoài máy owner; cân nhắc fixture tổng hợp ~9 người.
- TAB→" | " của .doc có thể lọt vào dia_chi/mo_ta (maybe-false, medium) — kiểm bằng .doc mẫu.
- `_tach_thua_bang_don_dong` chỉ bắt 1 thửa trong bảng dồn 1 dòng (maybe-false, medium).
- Tách dòng bảo hiểm/sổ tiết kiệm có thể sai với "CCCD số" / tài khoản chưa có STK (maybe-false, medium).
- regex-rules.md §0 trùng bảng file với regex-core.md §6 — gộp về 1 chỗ.
- progress.md của task5 gộp brief/decisions thay vì file riêng.

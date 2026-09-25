- source_plan: `D:/systemdocs/.agent/scratch/module-cleanup-plan-2026-09-25.md`
  summary: Thêm automated smoke test nối stage allowlist với dynamic import `upload_services`.
  evidence: Đã stage engine và import động ba service pass; hiện mới có smoke thủ công, chưa có test regression riêng.

- source_plan: `D:/systemdocs/.agent/scratch/module-cleanup-plan-2026-09-25.md`
  summary: Thêm automated smoke test cho standalone release và hai CLI regex sau khi copy.
  evidence: Bản standalone tạm đã build, chạy CLI và import service pass; chưa có test tự động giữ hành vi này.

- source_plan: `D:/systemdocs/.agent/scratch/module-cleanup-plan-2026-09-25.md`
  summary: Retire launcher/UI Qt cũ và frontend web cũ sau cutover Electron.
  evidence: `MIN-69 T10`/full packaged Windows E2E chưa có bằng chứng trong đợt này; giữ đường lui để không làm mất khả năng rollback.

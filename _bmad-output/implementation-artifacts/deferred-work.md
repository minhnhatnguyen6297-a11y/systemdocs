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

- source_plan: `plan-multica-word-integration.md`
  summary: Verify the real Electron native-picker workflow and visually inspect representative Word output pages.
  evidence: Component tests and Word COM checks passed, but native picker operation and page-by-page visual acceptance remain unrun. End-user defects at that surface are medium unverified; an isolated desktop run and inspected output settle the question.

- source_plan: `plan-multica-administrative-timeline.md`
  summary: Confirm coordinated same-day partial transfers and abolition against Owner-provided historical acts before adding more temporal rules.
  evidence: Same-day partial movement can be part of the act abolishing an identity; the ledger has no intra-day ordering or act grouping. A universally rejected same-day transfer would also reject legitimate coordinated changes. Medium unverified until historical sources establish the intended relationship.

- source_plan: `plan-multica-docx-intake.md`
  summary: Measure grouping and field ownership on a labeled, representative office-contract corpus.
  evidence: Medium unverified; current fixtures establish labelled transfer blocks, not all office layouts. Representative source documents and expected person/asset groups settle which profile expansions are needed.

- source_plan: `plan-multica-docx-intake.md`
  summary: Establish whether a candidate split/merge editor is needed from actual incorrect group boundaries.
  evidence: Medium unverified; no supplied contract demonstrates a boundary error that field review and Stage correction cannot handle. Such a labeled example is needed before designing additional regrouping and provenance operations.

- source_plan: `plan-multica-docx-intake.md`
  summary: Verify the full isolated Electron picker-to-original-Word-export workflow.
  evidence: Medium unverified; backend lifecycle and DOM component checks exist but native file selection, real IPC, and visible output have not yet run together. An isolated Electron flow with synthetic DOCX and a inspected output would settle it.
- source_plan: `_bmad-output/implementation-artifacts/plan-multica-docx-intake.md`
  summary: Kiểm luồng DOCX trên bản cài sạch và sao lưu/khôi phục đồng thời database cùng docx_sources.
  evidence: Chỉ môi trường source/dev và Electron cô lập đã chạy; chưa có phép thử cài sạch hay phục hồi toàn bộ các file nguồn/mẫu được hồ sơ tham chiếu. Đây là giới hạn nghiệm thu chưa xác minh lỗi.

- source_plan: plan-multica-docx-intake.md
  summary: Verify original-template publication on any supported data filesystem without hard-link support.
  evidence: Medium unverified; default NTFS works, but no supported FAT/network data-directory installation has been demonstrated. Installation filesystem checks settle applicability before adding an alternate atomic publication path.

- source_plan: plan-multica-docx-intake.md
  summary: Clarify whether repeated Analyze should rerun completed sources or only new sources in the retained Intake queue.
  evidence: Existing MIN112 at baseline sends all listed nonerror sources including completed ones; DOCX reanalysis produces new review candidates. A deliberate rerun/new-only interaction belongs to existing batch selection behavior; no automatic Stage acceptance occurs.

## Deferred from: code review tái cấu trúc SOT (2026-10-07)

- summary: 47 file `_bmad-output/decisions/*.md` chỉ có tiêu đề, phần Context/Decision/Consequences rỗng.
  evidence: pre-existing — bản gốc `bf161a5:backlog/decisions/` đã rỗng y hệt; lần chuyển chỉ copy nguyên.
- summary: 21 tiêu đề decision chứa chữ `\r` thừa (vd decision-33).
  evidence: pre-existing — có sẵn trong backlog gốc.
- summary: `_bmad-output/specs/README.md` §9 vẫn mô tả mô hình cũ (Backlog giữ task, `.agent/tasks/` giữ tiến độ, decision-31).
  evidence: cần quyết định có viết lại lịch sử spec không; AGENTS.md mới đã là luật hiện hành.

- source_plan: `D:/systemdocs/_bmad-output/tmp/core-versions-20261008.html`
  summary: Nang Electron 31 (het ho tro tu 14/01/2025, Chromium 126 khong con va bao mat) len ban stable moi nhat, kem electron-builder va bundle playwright-browsers, chay lai E2E.
  evidence: E2E hien xanh tren 31.7.7 nhung khong con ban va bao mat; app xu ly ho so nhay cam. Tieu chi xong: E2E xanh + check.cjs PASS + dong goi thu thanh cong.

- source_plan: `_bmad-output/backlog/story-upload-web-official-sot-cutover-plan.md`
  summary: Upload UI drops file_token for picked/downloaded refs; audit/scan rejected before sidecar
  evidence: `shell/src/renderer/upload/index.js:488-492,548` passes raw path references without `file_token`; `shell/src/main/ipc.js:68-109` `resolveFileTokens` rejects a path without a valid token with `validation_error`. Copied blocker logs `_bmad-output/tmp/issue-28-implementation/e2e_blocker_evidence.txt`, `e2e_upload_blocked.log`, and `e2e_pick_blocker.log` show both picker/download failures and no `upload.audit_excel` job; the separate passing real-engine run is recorded in `real-engine-upload-sot-smoke.json`.

# Handoff — MIN-87

Viết khi kết thúc phiên hoặc chuyển giao cho agent/người khác.

## Trạng thái khi bàn giao — 2026-09-22
- `MIN-87`: `In Progress` vì còn hai issue chờ xóa/archive.
- `MIN-88`: `In Review`; artifact design brief đã hoàn thành và có comment kiểm chứng.
- 55 issue được giữ đã có trong project `systemdocs` với component label và đã read-back.

## Điểm bắt đầu cho team design
1. Đọc [design brief HTML](./he-thong-cong-chung-ui-design-brief.html) từ đầu đến cuối; đây là artifact giao việc chính.
2. Dùng [UX Vòng 02](./he-thong-cong-chung-ux-spec.html) làm tài liệu tham chiếu, không coi là spec production đã duyệt.
3. Dựng một prototype offline, click được theo stable screen IDs và 16 acceptance scenarios; không chỉ trả screenshot hoặc kế hoạch.
4. Đối chiếu [snapshot Linear sau migration](./linear-scope-after-summary.json) và [kết quả phân loại issue UI cũ](./linear-delete-readiness-summary.json) khi cần tra lịch sử.

## File đã đổi
- `.agent/tasks/MIN-87/{brief,progress,decisions,handoff}.md`: record thực thi theo issue.
- `.agent/tasks/MIN-87/he-thong-cong-chung-ui-design-brief.html`: brief self-contained gửi Agent Design.
- `.agent/tasks/MIN-87/he-thong-cong-chung-ux-spec.html`: UX Vòng 02 tham chiếu, chưa phải spec module.
- `.agent/tasks/MIN-87/linear-scope-after-summary.json`: snapshot tổng hợp sau migration.
- `.agent/tasks/MIN-87/linear-delete-readiness-summary.json`: kết quả phân loại bảy candidate UI.
- Bản làm việc và raw audit chi tiết vẫn ở `.agent/scratch/`, được gitignore.

## Cách verify
- Mở `.agent/tasks/MIN-87/he-thong-cong-chung-ui-design-brief.html` trực tiếp bằng browser; kiểm tra heading `BRIEF CHO AGENT DESIGN · PROTOTYPE TRƯỚC`.
- Validator kỳ vọng: 21 unique `data-screen-id`, 16 `.scenario`, 0 external URL.
- Browser kỳ vọng: không overflow ngang tại 1440×900, 1280×820, 760×520; TOC mobile có 15 link; copy/download hoạt động.
- Linear: đọc `MIN-88` phải thấy state `In Review`, parent `MIN-87`, project `systemdocs` và comment kiểm chứng ngày 2026-09-22.

## Việc còn lại / rủi ro
- `MIN-34`, `MIN-38` đủ điều kiện loại nhưng chưa xóa/archive vì thiếu capability và web chưa đăng nhập.
- Không đổi hai issue sang `Cancelled` thay cho delete/archive.
- Chưa cập nhật spec `notary_v2`, `upload_lab`, `notaryoffice` hoặc runtime; việc này phải là task riêng sau UX review.
- Worktree có nhiều thay đổi staged từ trước; không stage/commit hoặc nhận chúng là kết quả task này.

## File tạm đã dọn
- Đã xóa `docs/architecture/CHANGE_REVIEW.md` tạo ngoài phạm vi trước đó.
- Đã chép design brief, UX Vòng 02 và hai snapshot tổng hợp cần bàn giao vào `.agent/tasks/MIN-87/` để commit; raw audit chi tiết và bản làm việc vẫn ở `.agent/scratch/` và được gitignore.

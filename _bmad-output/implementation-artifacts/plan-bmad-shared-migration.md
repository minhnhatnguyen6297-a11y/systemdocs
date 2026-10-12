---
title: 'Hợp nhất bản cài BMAD và chỉ dẫn flow'
type: chore
ticket: ''
created: '2026-10-12'
status: built
route: oneshot
route_source: auto
review: quick
review_source: pinned
lenses_ran: [quick]
baseline_revision: 9c419f03cb8c76bf0ba1672ee78551af3659a9fe
context:
  - '{project-root}/_bmad-output/tmp/story-bmad-shared-install-coding-flow.md'
---

<frozen-after-approval reason="user requested execution of the drafted ticket">

## Intent

**Problem:** BMAD có bản riêng trong Codex/Pi bên cạnh thư viện dùng chung. AGENTS.md lặp quy trình đã nằm trong BMAD/customization, dễ lệch chỉ dẫn.

**Approach:** Cài lại dòng skills từ upstream chính thức vào `C:\Users\MINH\.agents\skills`, liên kết các agent vào bản này. Giữ HTML Thariq trực tiếp trong Build/Spec qua override và bỏ chỉ dẫn flow trùng trong AGENTS.md. User duyệt thực thi bằng “xử lý luôn”. Không tạo workflow mới hoặc đổi orchestration.

**Acceptance:** Agent discovery chỉ có một bản BMAD chuẩn; bản cũ và customization có backup. Setup và render dùng bản mới, HTML contract được nạp ở đúng điểm trình bày. Daily loop giữ verification trước review và sau patch, independent review. AGENTS.md giữ luật repo không thuộc flow. Skills không thuộc BMAD và user files không liên quan không bị thay đổi.

</frozen-after-approval>

## Implementation Notes

- Route oneshot: yêu cầu và nơi tích hợp đã rõ; dùng installer chính thức, backup trước thay thế; không có lựa chọn sản phẩm/UX mới. Đây là bảo trì môi trường và policy, không đổi UI app nên không cần thêm HTML plan giả.
- Phần cài đặt và phần policy có phạm vi mutation tách biệt. BmadInstall chỉ quản lý global BMAD và script/config do setup sở hữu. BmadPolicy chỉ quản lý AGENTS, overrides, spec và README. Coordinator tích hợp, chạy smoke sau khi cả hai hoàn thành, review và commit.
- Tracked workspace ban đầu sạch; untracked artifacts hiện có được giữ nguyên. Không stage toàn repo.
- Cài 30 skills chính thức tại upstream `9f1987169a2e5626e5ccb31bb9cee051fdb3df20` (skills preview `6.13.0-next`); chuyển `bmad-preview-ticketing` sang `bmad-ticket`, sửa link và chạy setup chính thức.
- Không đổi runtime Thariq. Smoke phát hiện CSS của mock trong ví dụ đang hiện như chữ; bọc lại bằng `<style>` trong shared template và kiểm tra lại tất cả state.
- Sửa hướng dẫn bảo toàn spec thành “spec kernel” thay vì tên `SPEC.md` cũ, tương thích template upstream mới mà không đổi vai trò spec.

## Verification

- Fresh discovery Codex, Claude, Pi: 30 BMAD skills, không còn tên ticketing cũ. Codex/Pi trả canonical paths; Claude được đối chiếu các junction đã inspect. OMP fresh `read skill://bmad` trỏ tới canonical root. OMP RPC không hỗ trợ `get_commands`; không dùng lỗi đó làm bằng chứng discovery.
- Setup trả `current: true`, không đổi config project, không thêm câu hỏi hoặc module. Inventory: 30 canonical folders, 58 Codex/Claude links, không broken link hoặc bản BMAD real-folder legacy; backup được giữ.
- Build render: oneshot/quick, full/quick, full/thorough và default không pin review; Review quick render thành công. Spec là entry trực tiếp `SKILL.md`, không có `workflow.md`: dùng resolver để xác minh HTML activation.
- Coding smoke trên thay đổi wrapper CSS mock: trước sửa CSS xuất hiện thành chữ; sau sửa pack lại ví dụ và exercise 5 state ở 1280×900 và 390×844 offline. Đúng active/visible state, 2 stylesheet trong shadow root, không tràn ngang, không browser error; đã xem screenshot.
- Bằng chứng: `_bmad-output/tmp/bmad-shared-migration/migration-evidence.json`, `post-install-state.json`, `smoke-proof.json`. Đây không phải smoke một task autonomous coding toàn vòng; chưa chứng minh mọi agent tương lai tuân thủ instructions. Codex có cảnh báo OfficeCLI frontmatter ngoài phạm vi.

## Review Triage Log

- Independent Quick reviewer `MigrationReview`: không có finding. Reviewer đối chiếu project shared scripts với canonical `bmad/scripts`, và `tickets.py` với `bmad-ticket/scripts/tickets.py`; không khác biệt. Không chạy lại smoke hoặc sửa implementation.
- Reviewer xác nhận policy repo, HTML presentation points, verification-before-review, independent review, patch re-verification và blocked completion được giữ. Kết quả lưu tại `_bmad-output/tmp/bmad-shared-migration/independent-review.md`.

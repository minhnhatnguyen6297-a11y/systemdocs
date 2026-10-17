---
id: 21B
type: story
title: "Gỡ cả nhánh Thừa kế sau cảnh báo tác động"
parent: none
covers: []
after: [21]
assignee: ""
refined: true
hitl: false
risk: high
---

# Gỡ cả nhánh Thừa kế sau cảnh báo tác động

## Description

Triển khai đáp án owner của spike #21 ngày 17/10/2026, nguyên văn **“B - gỡ cả nhánh”**. Trước khi xóa node Thừa kế, cảnh báo đúng node và quan hệ bị tác động; xác nhận gỡ node đó cùng mọi hậu duệ active qua cạnh cha/mẹ, dù con còn parent khác. Spouse không tự là hậu duệ. Người giữ trong Stage, về Pool; chỉ Lưu sơ đồ mới ghi.

## Acceptance Criteria

1. **Xem đúng tác động trước khi quyết định**
   **Given** graph A→B→C nhiều thế hệ, B↔S và C có parents `[B,S]`, cùng nhánh không liên quan và slot trống/ẩn
   **When** người dùng chọn × trên B
   **Then** cảnh báo liệt kê B, C, mọi hậu duệ active và đúng quan hệ sẽ ngắt; S không thuộc tập chỉ vì là spouse; draft, dirty, revision và bản lưu chưa đổi.
2. **Hủy không tác động; xác nhận một lần**
   **Given** cảnh báo đang mở
   **When** Hủy, Escape, đóng × hoặc đóng nền
   **Then** draft/dirty/revision không đổi và thao tác không phát evaluate/save.
   **Given** người dùng xác nhận cảnh báo đúng graph/phiên hồ sơ hiện tại
   **When** áp dụng
   **Then** toàn bộ tập được gỡ trong một mutation draft, sau đó dùng evaluate hiện có, không tự save; cảnh báo cũ không được áp âm thầm khi graph/phiên đã đổi.
3. **Giữ Stage và graph ngoài tác động**
   **Given** tập gỡ đã xác nhận
   **When** quan sát Diagram/Pool và state canonical
   **Then** mọi người vẫn ở Stage với cùng ID/thứ tự/giá trị, người không còn gán active về Pool; node bị gỡ giữ tombstone cùng ID và metadata, dọn mọi quan hệ đi ra/đi vào kể cả tombstone cũ, không còn spouse lệch hoặc parent sai do thao tác. Spouse/nhánh ngoài tập và dấu Chủ/Nhận/vị trí tài sản không bị tác động giữ nguyên; không reparent, dồn số hoặc giữ ô trung gian rỗng. Slot mặc định từ evaluate giữ quy tắc hiện có, không hồi sinh nhánh.
4. **Lưu và mở lại đúng canonical**
   **Given** draft sau gỡ hợp lệ, kể cả còn thiếu dữ liệu
   **When** Lưu sơ đồ rồi mở mới hồ sơ
   **Then** nhận đúng graph/tombstone/Pool đã lưu, Stage giữ nguyên và revision tăng đúng luồng hiện có.
   **Given** invalid, stale revision, hồ sơ khóa hoặc lỗi Save
   **When** thử ghi
   **Then** không ghi nửa chừng, bản lưu cũ/revision còn nguyên và draft được giữ theo guard hiện có; mở lại không Save vẫn trả bản lưu cũ.

## Boundaries

- Chỉ Diagram Thừa kế; không đổi thao tác bỏ gán đơn lẻ, Hai bên hoặc Stage.
- Dùng Node v3/Save/evaluate/transaction hiện có; không API/store/schema mới hoặc sửa công thức pháp lý.
- #21 vẫn là spike 3 AC; story này mới chứa implementation. #19/#20/Office deferred và #18 removed không nằm trong phạm vi.
- Không Autoresearch, đổi initiative/config, chạm thay đổi ngoại lai hoặc gói dist-app.

## References

- source — _bmad-output/specs/notary_v2/diagram-rules.md, §9.9 và §6
- source — _bmad-output/specs/notary_v2/README.md, §5 và §9
- contract — contracts/notary-case-drafting.md, §7.1, §13.4 và §13.11
- decision — _bmad-output/decisions/decision-owner-inheritance-remove-entire-branch-20261017.md
- prerequisite — _bmad-output/backlog/spike-inheritance-middle-node-deletion.md, Notes
- design — _bmad-output/tmp/issue-21b-branch-removal/plan.html (đề xuất, chưa implement)
- tracking — _bmad-output/backlog/README.md, C20B

## Notes

- **BUILT 17/10/2026.** Retained Quick CODE t3 **No actionable findings**; parent đọc full diff + test-only patch + actual UI/proof/logs và chấp nhận AC1–4. Trước đó PLAN t2/Ticket validation clean và parent release; owner B semantics không đổi. Commit/push tách khỏi nghiệm thu hành vi; receipt lưu riêng.
- Bằng chứng: Node full **198 passed trước** patch bỏ incidental wording assert; affected `notary-diagram.test.mjs` **25 passed sau** patch, không chạy lại full suite. Real SQLite service **106 passed**, 24 warnings datetime hiện có. [Source Electron real IPC proof](../tmp/issue-21b-branch-removal/evidence/ui-ipc-proof.json) giữ hiệu lực vì patch chỉ test: 4 dismiss/focus không mutate/command, 1 graph transition, Stage/Pool/tombstones/default slots, invalid Save giữ draft/DB, Save revision 1→2 và fresh renderer reopen exact. Owned executable probe đã xóa sau review; toàn bộ evidence giữ nguyên.
- Giới hạn proof: source app, không packaged/native Word; startup toast `engine_unavailable` vẫn quan sát, không thuộc sửa này. Screenshot chỉ cho thấy phần đang nhìn; full graph được assert từ actual model/real workspace state, không suy thiếu node từ vùng ngoài màn hình.
- Risk: high — gỡ nhiều gán/quan hệ có thể thay phần hưởng, graph sai có thể từ chối Save hoặc mất nhánh ngoài ý định. Kiểm tra ngoài AC: parent đọc full scoped diff và một Quick reviewer độc lập đối chiếu spec, runtime Electron thật và real-service/SQLite proof trước chấp nhận.
- Prerequisite #21 đã trả lời; không phụ thuộc #20. Không có story/bug implementation bao phủ riêng policy B trong mapping C20 đã inspect; tạo leaf #21B riêng theo assignment, không đổi ba AC spike.
- Bằng chứng nghiên cứu trước owner chọn ở `../tmp/issue-21-middle-node-deletion/`, không chạy lại để xác nhận lỗi đã biết và không dùng làm bằng chứng feature built.

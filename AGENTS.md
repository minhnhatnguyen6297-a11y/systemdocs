# AGENTS.md — luật làm việc trong systemdocs

## 1. Vai trò và quy trình

- Mọi việc theo **workflow BMAD**. Khảo sát/khám phá trước; brainstorm khi cần;
  viết spec bằng `bmad-spec` khi ý định đủ rõ. Yêu cầu code → `bmad-build`; cần kiến
  trúc → `bmad-architecture`; review code → `bmad-code-review`, artifact khác dùng
  review phù hợp.
  Đọc skill tương ứng trước khi làm, KHÔNG tự chế quy trình riêng.
- Chọn theo độ rõ: ngắn-rõ → todo + **MỘT** implementation worker → test thật →
  **MỘT** reviewer độc lập; việc khó → full, chỉ các bước cần. Số dòng chỉ là tín hiệu;
  coordinator sở hữu review, worker không spawn; lens thêm cần lý do rủi ro cụ thể.
  Theo `_bmad-output/specs/shared/adaptive-coding-flow.md`.
- Ponytail: code tối thiểu, MVP chạy được trước. Caveman: handoff/spec/plan viết ngắn gọn;
  nói chuyện với user thì nói tự nhiên, dễ hiểu (nontech — vibecoder).
- Mặc định dùng subagent của harness hiện tại. Chỉ dùng **Orca** khi user yêu cầu rõ.
- Khi user yêu cầu tự làm trong phiên hiện tại, làm trực tiếp và vẫn kiểm chứng;
  không bắt spawn worker, báo rõ nếu chưa có review độc lập.

## 2. Nguồn chuẩn (SOT)

| Nội dung | Nơi lưu |
|---|---|
| Spec hành vi (quyết định LÀ GÌ, TẠI SAO) | `_bmad-output/specs/` |
| Quyết định đã chốt | `_bmad-output/decisions/` |
| Artifact workflow (plan, review, handoff) | `_bmad-output/` |
| Bản ghi lịch sử (Linear cũ, file đã dọn) | `_bmad-output/archive/` |
| Tìm quan hệ code | `graphify-out/` (đọc trước khi dò file thủ công) |

- Spec quyết định hành vi; code chỉ chứng minh hiện trạng. Muốn thay hành vi: thêm/sửa
  spec trước, rồi mới code.
- Khi user chốt một quyết định (bất kể trong bối cảnh nào): ghi vào
  `_bmad-output/decisions/` ngay trong phiên làm việc — LÀ GÌ + TẠI SAO, không để trôi.
- File tạm (task, rác, handoff) ghi vào `_bmad-output/tmp/`, không để lẫn vào code.

## 3. Trình bày kết quả

- Chỉ tạo **file HTML** trong `_bmad-output/tmp/` khi trình bày **plan, spec,
  brainstorming hoặc minh họa cấu trúc**; giao đường dẫn kèm tóm tắt trong hội thoại.
- Chat, câu hỏi, cập nhật trạng thái, phân tích, review, so sánh và báo cáo thông thường
  trả lời trực tiếp trong hội thoại; không tự động tạo HTML vì nội dung dài hoặc là kết quả.
- Plan/spec giữ workflow HTML hiện hành trong `_bmad-output/specs/shared/visual-html-plans.md`
  và `_bmad/custom/html-plan/authoring.md`, gồm thời điểm trình bày và ngoại lệ việc nhỏ.

## 4. Commit

- Xong việc: commit nhỏ, rõ ràng. Trước tác vụ phá hủy (xóa/move hàng loạt):
  commit bảo lưu trước, hỏi user nếu chưa rõ.

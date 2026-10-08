# AGENTS.md — luật làm việc trong systemdocs

## 1. Vai trò và quy trình

- Mọi việc theo **workflow BMAD**. Yêu cầu code → `bmad-build`; ý tưởng còn mơ hồ →
  `bmad-spec`; cần kiến trúc → `bmad-architecture`; review → `bmad-code-review`.
  Đọc skill tương ứng trước khi làm, KHÔNG tự chế quy trình riêng.
- Ponytail: code tối thiểu, MVP chạy được trước. Caveman: handoff/spec/plan viết ngắn gọn;
  nói chuyện với user thì nói tự nhiên, dễ hiểu (nontech — vibecoder).
- Orchestration chỉ dùng **Orca**. Không dùng 1DevTool, Codex multi-agent, hay công cụ
  khác đã gỡ.

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

- Kết quả phân tích, review, so sánh, báo cáo cho user xem → tạo **file HTML** trong
  `_bmad-output/tmp/` rồi đưa đường dẫn, thay vì in text dài trong hội thoại.
- Trong hội thoại chỉ tóm tắt vài dòng: quyết định là gì, cần user xác nhận gì.

## 4. Commit

- Xong việc: commit nhỏ, rõ ràng. Trước tác vụ phá hủy (xóa/move hàng loạt):
  commit bảo lưu trước, hỏi user nếu chưa rõ.

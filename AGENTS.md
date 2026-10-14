# AGENTS.md — luật làm việc trong systemdocs

## Dùng BMAD

- Dùng workflow BMAD và customization của repo trong `_bmad/custom/`; đọc skill
  tương ứng trước khi dùng. Không dựng flow song song.
- Code tối giản; artifact và handoff ngắn gọn; trao đổi với user tự nhiên, dễ hiểu.

## Nguồn chuẩn

- Đầu phiên, đọc [nền sản phẩm và khái niệm chung](./_bmad-output/specs/README.md),
  rồi đọc [sổ tay sản phẩm theo màn hình](./_bmad-output/specs/product-overview.md)
  để tìm UI và việc đang mở. Cập nhật sổ tay khi UI, trạng thái module hoặc việc
  đang mở đổi.

| Nội dung | Nơi lưu |
|---|---|
| Hành vi | `_bmad-output/specs/` |
| Quyết định đã chốt (LÀ GÌ + TẠI SAO) | `_bmad-output/decisions/` |
| Artifact workflow | `_bmad-output/` |
| Lịch sử | `_bmad-output/archive/` |
| Quan hệ code | `graphify-out/` |

- Spec quyết định hành vi; code chứng minh hiện trạng. Đổi hành vi thì cập nhật
  spec liên quan trước khi sửa code.
- Ghi quyết định của owner vào `_bmad-output/decisions/` trong phiên hiện tại.
  Task, handoff và file tạm nằm trong `_bmad-output/tmp/`.
- Đọc `graphify-out/` trước khi dò code thủ công.

## Trình bày

- Chỉ tạo file HTML trong `_bmad-output/tmp/` cho plan, spec, brainstorming hoặc
  minh họa cấu trúc; chat, trạng thái, phân tích, review và báo cáo thường trả lời
  trong hội thoại.
- HTML plan/spec là lớp trình bày; Markdown và artifact BMAD vẫn là nguồn chuẩn.

## Commit

- Khi xong, tạo commit nhỏ, rõ ràng. Trước khi xóa hoặc move hàng loạt, tạo commit
  bảo lưu; hỏi owner nếu phạm vi chưa rõ.

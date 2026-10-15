# AGENTS.md — luật làm việc trong systemdocs

## Dùng BMAD

- Dùng workflow BMAD và customization của repo trong `_bmad/custom/`; đọc skill
  tương ứng trước khi dùng. Không dựng flow song song.
- Code tối giản; artifact và handoff ngắn gọn; trao đổi với user tự nhiên, dễ hiểu.

## Nguồn chuẩn

- Đầu phiên, đọc [nền sản phẩm và khái niệm chung](_bmad-output/specs/README.md),
  rồi đọc [sổ tay sản phẩm theo màn hình](_bmad-output/specs/product-overview.md)
  để tìm UI và việc đang mở. Cập nhật sổ tay khi UI, trạng thái module hoặc việc
  đang mở đổi.

| Nội dung | Nơi lưu |
|---|---|
| Hành vi | `_bmad-output/specs/` |
| Issue/task, trạng thái và tiêu chí hoàn thành | `_bmad-output/backlog/` |
| Quyết định: đã chọn, lý do, phương án đã loại/chốt bỏ qua | `_bmad-output/decisions/` |
| Artifact workflow | `_bmad-output/` |
| Lịch sử | `_bmad-output/archive/` |
| Quan hệ code | `graphify-out/` |

- Spec quyết định hành vi; code chứng minh hiện trạng. Đổi hành vi thì cập nhật
  spec liên quan trước khi sửa code.
- Ghi quyết định của owner vào `_bmad-output/decisions/` trong phiên hiện tại.
  Kế hoạch thực hiện, handoff và file tạm nằm trong `_bmad-output/tmp/`;
  issue/task cần giữ lâu dài nằm trong backlog. Ghi nhận issue chưa phải duyệt làm.
- Đọc `graphify-out/` trước khi dò code thủ công.

## Viết spec

- Mỗi module một file chính; Soạn thảo có thêm quy tắc sơ đồ và mẫu Word.
  Viết theo luồng người dùng, ngắn gọn nhưng đủ mục đích, hành vi, giới hạn và ngoại lệ.
- Spec ghi trực tiếp quyết định đang áp dụng, kể cả trùng decision. Không dùng link
  thay cho quy tắc cần hiểu; link chỉ tra thêm. Decision giữ lý do và phương án bỏ.
- Không tách mỗi feature nhỏ thành file mới. Chỉ mở tài liệu chuyên sâu khi cần;
  không nạp archive mặc định và không nâng Draft thành đã duyệt khi gom tài liệu.
- Khi quyết định đổi, cập nhật spec và decision cùng phiên; tiến độ để trong backlog.

## Trình bày

- Chỉ tạo file HTML trong `_bmad-output/tmp/` cho plan, spec, brainstorming hoặc
  minh họa cấu trúc; chat, trạng thái, phân tích, review và báo cáo thường trả lời
  trong hội thoại.
- HTML plan/spec là lớp trình bày; Markdown và artifact BMAD vẫn là nguồn chuẩn.

## Commit

- Khi xong, tạo commit nhỏ, rõ ràng. Trước khi xóa hoặc move hàng loạt, tạo commit
  bảo lưu; hỏi owner nếu phạm vi chưa rõ.

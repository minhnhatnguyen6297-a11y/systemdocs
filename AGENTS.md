# AGENTS.md — luật làm việc trong systemdocs

## Dùng BMAD

- Dùng workflow BMAD và customization của repo trong `_bmad/custom/`; đọc skill
  tương ứng trước khi dùng. Không dựng flow song song.
- Code tối giản; artifact và handoff ngắn gọn; trao đổi với user tự nhiên, dễ hiểu.

## Nguồn chuẩn

| Nội dung | Nơi lưu |
|---|---|
| Hành vi | `_bmad-output/specs/` |
| Quyết định đã chốt (LÀ GÌ + TẠI SAO) | `_bmad-output/decisions/` |
| Artifact workflow | `_bmad-output/` |
| Lịch sử | `_bmad-output/archive/` |
| Quan hệ code | `graphify-out/` |
| Sổ quyết định nghiệp vụ thừa kế (D-xxx) | `_bmad-output/decisions/decision-80-so-quyet-dinh-nghiep-vu-thua-ke.md` |
| Điều luật thừa kế (BLDS 2015, HNGĐ 2014) | `_bmad-output/specs/notary_v2/diagram/inheritance/legal-baseline.md` |
| Câu hỏi mở (Q-xxx), bảng luật ↔ app | `business-rules.md` §8–§10 (cùng thư mục; quy tắc R-xx) |

- Spec quyết định hành vi; code chứng minh hiện trạng. Đổi hành vi thì cập nhật
  spec liên quan trước khi sửa code.
- Ghi quyết định của owner vào `_bmad-output/decisions/` trong phiên hiện tại.
  Task, handoff và file tạm nằm trong `_bmad-output/tmp/`.
- Đọc `graphify-out/` trước khi dò code thủ công.

## Thứ tự đọc và giao thức hỏi owner

- Đọc trước khi làm việc nghiệp vụ: `_bmad-output/specs/product-overview.md`
  (bối cảnh, triết lý) → sổ D-xxx → `legal-baseline.md` → `business-rules.md`
  → code.
- Trước khi hỏi owner: tra D-xxx → luật → code. Đã có câu trả lời thì dùng, không
  hỏi lại. Mặc định theo luật trừ khi D-xxx chốt lệch.
- Chỉ hỏi lựa chọn nghiệp vụ thật; gom một lượt; mỗi câu có bối cảnh, mặc định
  luật (số điều), khuyến nghị, lý do, ảnh hưởng code. Ghi câu hỏi vào Q-xxx.
- Owner trả lời xong: ghi D-xxx ngay trong phiên và đánh dấu Q-xxx đã chốt.

## Trình bày

- Chỉ tạo file HTML trong `_bmad-output/tmp/` cho plan, spec, brainstorming hoặc
  minh họa cấu trúc; chat, trạng thái, phân tích, review và báo cáo thường trả lời
  trong hội thoại.
- HTML plan/spec là lớp trình bày; Markdown và artifact BMAD vẫn là nguồn chuẩn.

## Commit

- Khi xong, tạo commit nhỏ, rõ ràng. Trước khi xóa hoặc move hàng loạt, tạo commit
  bảo lưu; hỏi owner nếu phạm vi chưa rõ.

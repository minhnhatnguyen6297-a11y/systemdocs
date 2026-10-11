# Quyết định: luồng code thích ứng — việc ngắn-rõ một worker, việc khó mở full

Ngày: 2026-10-12. Người dùng đã duyệt triển khai ngay trong phiên này.

Yêu cầu transport Orca trong quyết định này đã được thay thế bởi
[native subagents, Orca on request](decision-native-subagents-orca-on-request.md).
Phần dưới giữ nguyên lịch sử; các luật adaptive khác vẫn có hiệu lực.

## LÀ GÌ

- Việc **ngắn, rõ** → todo list + **một** Orca implementation worker → test/smoke
  thật → **một** reviewer độc lập → sửa finding và verify lại → xong.
- Việc **khó** → mở full workflow, nhưng chỉ thêm bước/lens thật cần; vẫn **một**
  implementation worker và mặc định **một** reviewer.
- Route chọn theo độ rõ, mẫu đã biết, cách kiểm chứng đã biết, rủi ro và quyết định
  hệ quả còn mở. Số dòng/số file chỉ là tín hiệu phụ; bỏ ngưỡng 100 dòng làm tiêu chí
  quyết định.
- Coordinator sở hữu review: tự dispatch reviewer; implementation worker không tự
  review và không spawn ai. Topology Orca phẳng, một worker.
- Bỏ quota finding tối thiểu của blind-hunter; kết quả sạch là hợp lệ. Lens phụ chỉ
  chạy khi có lý do rủi ro cụ thể, công bố lý do trước và ghi kết luận theo bằng chứng
  sau.
- Giữ luật nạp/cập nhật spec trước khi đổi hành vi và giữ contract HTML plan/spec
  (ngoại lệ việc nhỏ; không HTML cho báo cáo/chat thường).

- Làm rõ sau review được coordinator duyệt: khảo sát/khám phá trước khi chọn luồng,
  brainstorm khi cần, spec khi ý định đủ rõ; code review chỉ cho code; việc khó chỉ
  dùng các bước cần thiết. Test thật trước review và chạy lại sau mỗi patch do chính
  worker ban đầu sửa. Mỗi lens ghi accepted/rejected kèm bằng chứng hoặc no findings;
  thorough giữ Quick không điều kiện, none chỉ khi user chủ động chọn.

## TẠI SAO

- Owner: “short clear work => todo list + ONE implementation worker => test => review;
  hard problem activates full workflow”, kèm băn khoăn bốn review lens tự chạy không
  được giải thích.
- Review độc lập (role slow) chỉ ra: ngưỡng 100 dòng là luật cứng trên một con số
  đoán; oneshot không tự tạo worker/todo; blind-hunter ép đủ số finding; handoff/lens
  chưa nối Orca. Đây là dữ liệu, owner đã chốt luật tối thiểu tương ứng.
- Giữ một worker và một reviewer giúp việc nhỏ không gánh ceremony, nhưng vẫn có kiểm
  chứng thật và review độc lập trước khi báo xong.

## Bối cảnh kỹ thuật

- Thực thi bằng field customization được cài đặt hỗ trợ: `route_selection`,
  `implementation_handoff`, `review`, `quick_lenses`, `thorough_lenses`,
  `activation_steps_append` của `bmad-build`; và override tương ứng cho
  `bmad-code-review`. Không sửa installed skill hay snapshot sinh tự động.
- Reviewer slow map `openai-codex/gpt-6.1-sol:high` → Orca
  `--agent codex --model gpt-6.1-sol --effort high`, xác nhận `launch.effective` khớp
  `launch.requested`.
- Spec hành vi: `_bmad-output/specs/shared/adaptive-coding-flow.md`.

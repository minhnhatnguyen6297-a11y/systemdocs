---
id: 3
type: spike
title: "Chốt quy tắc đổi loại hồ sơ đã lưu"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Chốt quy tắc đổi loại hồ sơ đã lưu

## Description

Chốt tác động khi đổi loại hồ sơ Hai bên/Thừa kế đã lưu. Nhu cầu cho sửa loại đã được người báo yêu cầu; phần còn mở là quy tắc chuyển đổi. Owner chọn quy tắc để #25 triển khai; không chặn các sửa giao diện độc lập.

## Approach

Đọc nguồn hiện hành và bằng chứng sẵn có trước. Chỉ so phương án trong ranh issue; không đoán phần nguồn thiếu. Người có vai trò ghi trong Notes cung cấp bằng chứng không thể lấy từ repo hoặc nhận đáp án cần lựa chọn. Không triển khai sản phẩm trong spike.

## Acceptance Criteria

1. **Trả lời đúng câu hỏi hoặc xác định bằng chứng thiếu**
   Verify: Notes ghi đối chiếu có ngày theo từng câu hỏi, nguồn/phương án/hệ quả và phần thông tin còn thật sự không lấy được.
2. **Đáp án dùng được cho đúng bên chờ**
   Verify: Notes chỉ rõ ai chờ, cần quyết định/capability gì, nơi ghi đáp án canonical và việc độc lập không phải chờ.
3. **Người chịu trách nhiệm nhận đáp án đúng phạm vi**
   Verify: owner nhận lựa chọn sản phẩm; người thao tác/reviewer nhận bằng chứng đo. Notes ghi vai trò/ngày; phần Draft/Pending chưa chọn vẫn giữ trạng thái.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C02
- source — _bmad-output/specs/notary_v2/README.md, §2, §9

## Notes

- Tracking: C02; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Chọn sai cách giữ/xóa gán người hoặc mapping có thể làm sai quan hệ và văn bản hồ sơ đã lưu.
- Open question: Khi đổi loại hồ sơ đã lưu, gán người, quyền sở hữu, lựa chọn văn bản và binding được giữ hay chuyển thế nào? Chuyển nào bị cấm; cần xem trước/xác nhận gì?
- Ai chờ: #25. Nơi ghi đáp án: Notes của issue này, spec Notary và decision có ngày trước khi refinement #25. Giữ bất biến loại ở runtime hiện tại tới khi contract chuyển đổi được duyệt. Report d9da640e.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

---
id: 15
type: spike
title: "Đối chiếu các lỗ hổng bằng chứng quyết định còn thực sự tồn tại"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: low
---

# Đối chiếu các lỗ hổng bằng chứng quyết định còn thực sự tồn tại

## Description

Đối chiếu lỗ hổng provenance còn thật sự tồn tại với spec tự đủ nghĩa và decision đã bổ sung. Số 56 accepted và 6 proposed thân trống là baseline audit lịch sử, không phải số hiện tại.

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
- tracking — _bmad-output/backlog/README.md, C14
- source — _bmad-output/decisions/decision-owner-doc-clarifications-20261015.md, items 7–8
- source — _bmad-output/tmp/owner-doc-decisions-20261015/56-quyet-dinh.md, historical pre-update list
- source — _bmad-output/tmp/docs-consistency-20261014/decisions-audit.md, baseline and limitations

## Notes

- Tracking: C14; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: low — Khôi phục sai lịch sử có thể làm người đọc tưởng một lựa chọn đã được duyệt.
- Open question: Sau khi đọc nguồn hiện hành, quy tắc quan trọng nào vẫn thiếu bằng chứng? Original task-3/decision48 còn ở đâu ngoài tombstone, và đúng việc nào thật sự bị thiếu nguồn đó chặn?
- Ai chờ: chỉ quy tắc thật sự cần nguồn còn thiếu; không blanket gate. Nơi ghi: ledger theo nguồn và tham chiếu sửa. Không dựng lý do từ tiêu đề hoặc duyệt lại toàn bộ 56; giữ ghi nhận nguồn mất nếu không tìm thấy.

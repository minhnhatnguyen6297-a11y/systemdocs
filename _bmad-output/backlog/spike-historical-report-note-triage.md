---
id: 18
type: spike
title: "Khôi phục bằng chứng và phân loại 12 report mất ghi chú"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: low
---

# Khôi phục bằng chứng và phân loại 12 report mất ghi chú

## Description

Giữ riêng mười hai UUID lịch sử và khôi phục phần bằng chứng còn lấy được. Chỉ hỏi người báo phần triệu chứng thực sự đã mất; đây là một việc lập kế hoạch/bằng chứng, không là mười hai bug đoán ra.

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
- tracking — _bmad-output/backlog/README.md, C17
- source — _bmad-output/tmp/review-37-reports-20261009/inventory.json, 12 non-E2E selections
- source — _bmad-output/implementation-artifacts/diagram-error-fix-20261009/open-reports.md, individual records and recovery limits

## Notes

- Tracking: C17; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: low — Gộp hoặc đóng nhầm record làm mất dấu phản ánh người dùng; không sửa runtime.
- Open question: Với từng UUID vẫn không còn triệu chứng sau khi đọc nguồn sẵn có, người báo gốc có thể bổ sung triệu chứng/kết quả mong đợi không? Không phát lại để bác bỏ phản ánh.
- Ai chờ: phân loại/đóng đúng mười hai record này. Nơi ghi: ledger che dữ liệu theo UUID trong Notes, dẫn nguồn private; không suy root cause chung từ console.

### Mười hai record độc lập

Giữ từng record chưa xác minh; không khẳng định cùng nguyên nhân.

- `0d1b1ff1-73ce-4e8b-a6bf-2c695f06dd3f` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.
- `2f352897-ab9b-4f11-84e4-a44c43145bf0` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.
- `377d8486-e885-4a21-8e84-497241546eaa` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.
- `534545cf-f020-4e22-8e03-362294f72508` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.
- `5db58074-cf8b-4a67-ab5a-09c0dd449a94` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.
- `60e02a79-727d-4de3-be7f-488b3f1a39ee` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.
- `643496a0-c4a4-4e5a-ab2f-bbbfa39d438a` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.
- `6714de6f-0049-4b4c-8d0d-2a2b179f15d9` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.
- `aaf29f16-68b4-4a92-b15c-b811043d9c80` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.
- `b5999b39-dce5-48dc-954a-66d231cce6ee` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.
- `bb496551-82b6-4f72-bd80-77df2e396e2f` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.
- `e3bba3ef-0f1f-4730-a505-cf0d282b75b1` — thiếu ghi chú gốc; đọc provenance private sẵn có trước khi hỏi người báo.

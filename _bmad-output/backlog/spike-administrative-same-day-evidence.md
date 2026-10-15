---
id: 27
type: spike
title: "Đối chiếu văn bản chuyển một phần và bãi bỏ hành chính cùng ngày"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Đối chiếu văn bản chuyển một phần và bãi bỏ hành chính cùng ngày

## Description

Tìm và đọc văn bản lịch sử chứng minh quan hệ giữa chuyển một phần lãnh thổ và bãi bỏ đơn vị cùng ngày. Người có nguồn/chuyên môn xác nhận cách đọc sự kiện. Đây là nghiên cứu độc lập với extraction/OCR #12; không triển khai thuật toán thời gian.

## Approach

Đọc giới hạn ledger và deferred trước, tận dụng văn bản đã có. Theo từng ca, ghi đơn vị nguồn/đích, toàn bộ hay một phần, ngày hiệu lực và phần văn bản cho biết các việc có phối hợp trong cùng văn bản hay không. Không suy thứ tự nội ngày hoặc nhóm văn bản khi nguồn không có. Nếu không lấy được văn bản đủ căn cứ, giữ câu hỏi unresolved.

## Acceptance Criteria

1. **Nguồn gắn đúng từng nhận định**
   Verify: Notes/ledger có danh mục văn bản, trích vị trí liên quan, ngày và ID đơn vị có căn cứ; phần không xác định hoặc pending được ghi riêng.
2. **Phân biệt lịch sử whole/partial và giới hạn ledger**
   Verify: bảng đối chiếu giải thích nguồn nào chứng minh phối hợp chuyển một phần/bãi bỏ cùng ngày, nguồn nào chưa đủ; không lấy vòng partial ở ngày khác làm bằng chứng tự động cho cùng ngày.
3. **Kết luận nghiên cứu có người nhận**
   Verify: owner/người có chuyên môn nhận cách đọc nguồn với ngày xác nhận, hoặc ghi rõ thiếu nguồn chưa giải quyết. Chỉ thay luật thời gian dùng kết luận này chờ đáp án; extraction/OCR #12 không chờ.

## Boundaries

- Không thêm temporal algorithm, thứ tự nội ngày, nhóm văn bản, migration/schema hoặc luật cấm toàn bộ cùng ngày.
- Không đổi pending thành confirmed, không dùng ngày tải làm ngày hiệu lực, không suy whole từ partial/unknown.
- Không mở lại hướng DB/dịch vụ mới hoặc tối ưu recursion khi chưa có nhu cầu thực.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C26
- source — _bmad-output/specs/shared/administrative-lookup.md, §3.5–§3.6, dòng 568–621
- source — _bmad-output/implementation-artifacts/deferred-work.md, dòng 30–33

## Notes

- Tracking: C26; draft/chưa refined, chỉ nghiên cứu bằng chứng.
- Risk: medium — diễn giải sai văn bản có thể dẫn tới đề xuất luật kết thúc/chuyển đơn vị sai; issue này không sửa ledger hay thuật toán.
- Open question: văn bản nào xác lập chuyển một phần và bãi bỏ phối hợp cùng ngày, với đơn vị/ngày hiệu lực cụ thể? Thiếu nguồn thì giữ chưa xác minh, không chọn luật thay.
- Ai chờ: đề xuất thay quy tắc thời gian cụ thể sau này. Nơi ghi đáp án: Notes và ledger nguồn có vị trí tra cứu; chưa tự phê duyệt implementation.

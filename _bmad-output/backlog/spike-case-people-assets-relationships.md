---
id: 43
type: spike
title: "Làm rõ quan hệ nhiều Người–nhiều Tài sản trong Hồ sơ"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Làm rõ quan hệ nhiều Người–nhiều Tài sản trong Hồ sơ

## Description

Gộp D06 và D07 của ma trận Nam Định thành một câu hỏi thiết kế nghiệp vụ: Hồ sơ chứa những Người/Tài sản nào, thứ tự và nhóm/vai trò của từng lần tham gia là gì, và Người/nhóm liên quan phạm vi Tài sản nào. Owner duyệt kết quả nghiệp vụ trước khi chọn model/contract để phần quan hệ của #41 có thể cutover đúng. Đây là issue làm rõ, không phải implementation.

**Thứ tự owner:** xử lý ngay sau làm rõ các ô trong SOT §7, không chờ toàn #41 hoàn thành. #41 là nơi nhận kết quả, không là prerequisite hoàn tất của spike; `after: []` không mã hóa thứ tự công việc thành hard dependency. #42 nhiều giấy tờ/địa chỉ không là prerequisite. Hiện chỉ ghi nhận ticket, chưa bắt đầu thiết kế hoặc triển khai.

## Approach

1. Đọc quyết định owner, SOT §6–7 và chuẩn Người–Tài sản–Hồ sơ đã có. Tách dữ kiện nguồn, cách trình bày, membership/vai trò và scope liên quan; không suy quan hệ từ việc cùng xuất hiện trong payload.
2. Dùng tình huống tổng hợp, không PII: nhiều Người cùng nhóm, một Người xuất hiện nhiều vai trò, nhiều Tài sản với phạm vi toàn nhóm/toàn tập và từng cặp, liên kết chưa rõ, văn bản một bên, người chết và cá nhân đại diện. Không đọc mẫu thật khi gate #41 còn đóng.
3. So sánh phương án bảo toàn các nghĩa trên và cách giữ thứ tự, thiếu/mơ hồ/nguồn. Phân biệt danh tính Người với lần tham gia; phân biệt chủ đất Diagram với nhóm A/B/người đứng tên GCN. Không mặc định FK, bảng nối hoặc cardinality hiện có là quyết định nghiệp vụ.
4. Trình owner những câu hỏi nghiệp vụ còn thật sự mở; ghi đáp án và ảnh hưởng vào decision hiện có, spec và #41. Sau đó mới đề xuất contract/model kỹ thuật; không hỏi owner duyệt từng ID/key kỹ thuật.

Đủ để khép spike khi mọi tình huống có đáp án hoặc giới hạn được owner chấp nhận, phần phụ thuộc của #41 tìm được nguồn chuẩn và không phải đoán quan hệ. Chưa ấn định time box; không tự đặt thời hạn hoặc estimate.

## Acceptance Criteria

1. **Membership, thứ tự và vai trò được phân biệt khỏi danh tính**
   Verify: bảng tình huống tổng hợp ghi Người/Tài sản thuộc Hồ sơ, nhóm/thứ tự/lần tham gia có căn cứ và phần chưa rõ; không cắt người đầu, dedup theo tên hoặc gộp nhiều Người thành một chuỗi định danh.
2. **Scope Người/nhóm–Tài sản được mô tả đúng và có nguồn**
   Verify: bảng phân biệt cả nhóm/cả tập, từng cặp và chưa xác định; không tự suy mọi Người×mọi Tài sản, chủ đất từ Bên A/GCN hoặc chuyển quan hệ từ module khác.
3. **R06 và D05 được áp đúng mà không tự lấp ngoại lệ**
   Verify: đáp án giữ policy “Người yêu cầu công chứng = tất cả người có trong hồ sơ”, thuần dữ liệu chuẩn, không lookup/firstperson/role prose. Owner làm rõ phạm vi người chết/cá nhân đại diện trong membership, không mặc định loại họ. Nhóm output A/B không dùng chữ “nhận” làm universal regex hoặc “không nhận=A”; trường hợp một bên/ủy quyền/nhãn mâu thuẫn có đáp án hoặc giới hạn rõ. Pháp nhân không thuộc Người, vẫn nhập tay.
4. **Đáp án được owner chấp nhận và bàn giao cho #41**
   Verify: decision/spec và Notes #41 dẫn cùng đáp án có ngày, nêu phần đã chọn/chưa chọn và tác động contract/cutover; không chỉ chọn sơ đồ/bảng lưu mà bỏ nghĩa nghiệp vụ. Trước owner chấp nhận, ticket giữ `refined: false` và không tự khép bằng suy đoán.
5. **Giữ phạm vi docs/design và gate hiện hành**
   Verify: không code/schema/migration/DB/parser/browser/customer sample/corpus/runtime test, không nối module hoặc thêm đối tượng nghiệp vụ; không mở gate mẫu từ spike. Implementation chỉ bắt đầu khi được giao riêng và có contract phù hợp.

## Boundaries

- Gộp D06+D07 trong một issue, không tách nhiều người và nhiều tài sản thành hai thiết kế bỏ rơi liên kết.
- Không nhận trùng #42, không tự thiết kế pháp nhân tương lai hoặc engine trường động. R05 alias không tự điền/không mở rộng schema; D04 lời phức tạp user sửa tay; D08 theo R06, không duyệt block dư.
- Raw/history/provenance giữ nguyên; không bịa người thiếu, quyền đại diện hoặc quan hệ pháp lý.

## References

- parent — none
- decision — _bmad-output/decisions/decision-owner-upload-field-standardization-20261019.md, Trả lời ma trận Nam Định §7
- behavior — _bmad-output/specs/upload_lab/nam-dinh-website-sot.md, §6.1, §6.3, §7 R06/D05/D06/D07
- consumer — _bmad-output/backlog/story-upload-business-field-standardization.md, AC1–2 và Notes ma trận Nam Định
- authority — contracts/entities.md, §8–9
- companion — _bmad-output/backlog/story-person-multiple-identities-addresses.md, Boundaries

## Notes

- Decision 20/10/2026: owner yêu cầu D06 issue riêng ngay sau rõ các ô; D07 cùng issue D06. Chưa duyệt model/FK/cardinality; không implementation lúc ghi nhận.
- Open question: membership cụ thể của Hồ sơ, thứ tự, nhiều lần tham gia và scope Người–Tài sản là nội dung spike; giữ nguyên nghĩa R06 “tất cả người”, không thay bằng chỉ B/người ký/lookup.
- Risk: high — sai membership hoặc scope có thể điền thiếu Người hoặc gắn nhầm Tài sản. Ngoài AC, reviewer độc lập cần đối chiếu đáp án với các tình huống tổng hợp và ranh giới #41 trước đề xuất cutover.
- Identity: `next_id: 43` từ `tickets.py status _bmad-output/backlog` ngày 20/10/2026; status đã đọc không có issue cùng phạm vi. Repo store/loose backlog theo waiver hiện có; không đổi active initiative hoặc setup/install/config. Independent docs review CLEAN, mandatory Ticket validation PASS 20/10/2026; parent cho commit đúng phạm vi, không publish remote/push hoặc giao implementation.

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

**Thứ tự owner:** sau rõ ô Nam Định §7, không chờ toàn #41/#42. Phân tích16ca hoàn tất; owner trả lời Q1 requester/Q2 A-B. Chỉ BANKMODE “dán cả cụm” ngân hàng còn clarification; AC4 chưa khép, chưa model/schema/cutover hoặc runtime.

## Approach

1. Đọc quyết định owner, SOT §6–7 và chuẩn Người–Tài sản–Hồ sơ đã có. Tách dữ kiện nguồn, cách trình bày, membership/vai trò và scope liên quan; không suy quan hệ từ việc cùng xuất hiện trong payload.
2. Dùng tình huống tổng hợp, không PII: nhiều Người cùng nhóm, một Người xuất hiện nhiều vai trò, nhiều Tài sản với phạm vi toàn nhóm/toàn tập và từng cặp, liên kết chưa rõ, văn bản một bên, người chết và cá nhân đại diện. Không đọc mẫu thật khi gate #41 còn đóng.
3. So sánh phương án bảo toàn các nghĩa trên và cách giữ thứ tự, thiếu/mơ hồ/nguồn. Phân biệt danh tính Người với lần tham gia; phân biệt chủ đất Diagram với nhóm A/B/người đứng tên GCN. Không mặc định FK, bảng nối hoặc cardinality hiện có là quyết định nghiệp vụ.
4. Trình owner những câu hỏi nghiệp vụ còn thật sự mở; ghi đáp án và ảnh hưởng vào decision hiện có, spec và #41. Sau đó mới đề xuất contract/model kỹ thuật; không hỏi owner duyệt từng ID/key kỹ thuật.

Đủ để khép spike khi mọi tình huống có đáp án hoặc giới hạn được owner chấp nhận, phần phụ thuộc của #41 tìm được nguồn chuẩn và không phải đoán quan hệ. Chưa ấn định time box; không tự đặt thời hạn hoặc estimate.

## Acceptance Criteria

1. **Membership, thứ tự và vai trò được phân biệt khỏi danh tính**
   Verify: bảng tình huống tổng hợp ghi Người/Tài sản thuộc Hồ sơ, nhóm/thứ tự/lần tham gia có căn cứ và phần chưa rõ; phân biệt một Người nhiều vai trò với nhiều Người trùng tên, hàng thửa với cụm đất có thứ tự và nhiều thửa cùng GCN. Không cắt người đầu, dedup theo tên/serial hoặc gộp nhiều Người thành một chuỗi định danh; không để thay đổi Hồ sơ/module khác ghi đè snapshot đã xác nhận.
2. **Scope Người/nhóm–Tài sản được mô tả đúng và có nguồn**
   Verify: bảng phân biệt cả nhóm/cả tập, từng cặp tách rời, tập con chồng nhau và chưa xác định; không tự suy mọi Người×mọi Tài sản, tỷ lệ/quyền sở hữu, chủ đất từ Bên A/GCN hoặc chuyển quan hệ từ module khác. Tách identity tài sản, thứ tự trình bày và nghĩa dấu chọn Diagram hiện hành; không âm thầm đổi quan hệ cũ.
3. **R06 và D05 được áp đúng mà không tự lấp ngoại lệ**
   Verify: requester Nam Định/Upload gồm cá nhân sống tham gia và đại diện ủy quyền, không đòi tag A/B đã gán kể cả một bên/conflict; người chết/CCV/nhân viên không vào output đó, không xóa Person chết/Stage/Hồ sơ thừa kế/raw/history/metadata nhân sự. Cá nhân chuẩn, mỗi identity xác nhận một lần theo nguồn, không prose/lookup/firstperson/dedup tên. Ngân hàng thế chấp cả cụm không Person; BANKMODE chỉ user dán hay app lấy/điền cụm ngân hàng, không extractor/schema tự chọn hoặc mở prose cá nhân. Ủy quyền A=ủy quyền/B=được ủy quyền; một bên không gán; nguồn trái nhau giữ conflict/xác nhận nhóm không winner. “Nhận” không universal regex; alias/D04/D08 giữ policy.
4. **Đáp án được owner chấp nhận và bàn giao cho #41**
   Verify: decision/spec và Notes #41 dẫn cùng đáp án có ngày, nêu phần đã chọn/chưa chọn và tác động contract/cutover; không chỉ chọn sơ đồ/bảng lưu mà bỏ nghĩa nghiệp vụ. Trước owner chấp nhận, ticket giữ `refined: false` và không tự khép bằng suy đoán.
5. **Giữ phạm vi docs/design và gate hiện hành**
   Verify: không code/schema/migration/DB/parser/browser/customer sample/corpus/runtime test, không nối module hoặc thêm đối tượng nghiệp vụ; không mở gate mẫu từ spike. Implementation chỉ bắt đầu khi được giao riêng và có contract phù hợp.

## Boundaries

- Gộp D06+D07 trong một issue, không tách nhiều người và nhiều tài sản thành hai thiết kế bỏ rơi liên kết.
- Không nhận trùng #42, không tự thiết kế pháp nhân tương lai. Owner đã chốt **chỉ placeholder và trường tĩnh**; không tạo tầng 2 đoạn động, formula engine hoặc điều kiện cấu hình, không xóa/đổi nghĩa block token Word legacy đang hoạt động. R05 alias không tự điền/không mở rộng schema; D04 lời phức tạp user sửa tay; D08 theo R06, không duyệt block dư.
- Raw/history/provenance giữ nguyên; không bịa người thiếu, quyền đại diện hoặc quan hệ pháp lý.

## References

- parent — none
- decision — _bmad-output/decisions/decision-owner-upload-field-standardization-20261019.md, Trả lời ma trận Nam Định §7
- behavior — _bmad-output/specs/upload_lab/nam-dinh-website-sot.md, §6.1, §6.3, §7 R06/D05/D06/D07
- consumer — _bmad-output/backlog/story-upload-business-field-standardization.md, AC1–2 và Notes ma trận Nam Định
- authority — contracts/entities.md, §8–9
- companion — _bmad-output/backlog/story-person-multiple-identities-addresses.md, Boundaries
- proposed design/current plan — _bmad-output/backlog/spike-case-people-assets-relationships-plan.md, 16ca, Q1/Q2 đã trả lời, BANKMODE còn mở; model chưa schema áp dụng

## Notes

- Decision 20/10/2026: owner yêu cầu D06 issue riêng ngay sau rõ các ô; D07 cùng issue D06. Chưa duyệt model/FK/cardinality; không implementation lúc ghi nhận.
- Decision 20/10/2026: Q1 requester/Q2 A-B đã trả lời; scope output không xóa Person/Stage/Hồ sơ thừa kế/history. Không hỏi lại nghĩa đã chọn hoặc gate engineering.
- Risk: high — sai membership hoặc scope có thể điền thiếu Người hoặc gắn nhầm Tài sản. Ngoài AC, reviewer độc lập cần đối chiếu đáp án với các tình huống tổng hợp và ranh giới #41 trước đề xuất cutover.
- Identity: `next_id: 43` từ `tickets.py status _bmad-output/backlog` ngày 20/10/2026; status đã đọc không có issue cùng phạm vi. Repo store/loose backlog theo waiver hiện có; không đổi active initiative hoặc setup/install/config. Independent docs review CLEAN, mandatory Ticket validation PASS 20/10/2026; parent cho commit đúng phạm vi, không publish remote/push hoặc giao implementation.
- Decision 20/10/2026 (lệnh tiếp tục mới nhất): owner “chốt chỉ dùng placeholder và trường tĩnh, tiếp tục”. Lệnh này cho phép thiết kế spike #43, **không cho phép runtime**; không tự chọn membership/scope/ngoại lệ A/B hoặc duyệt tầng động. Phương án hai tầng đang cân nhắc trong nguồn cũ không còn là phương án tiếp tục.
- Evidence mới:16ca và bảo toàn đã hoàn tất; đáp án nguyên văn trong decision, phần đã rõ đồng bộ SOT/module/shared/overview/#41. Composition/model/cutover chưa implement; BANKMODE còn clarification, không extractor pháp nhân/blanket raw editor.
- Decision mới: cá nhân sống A/B/đại diện ủy quyền vào requester; người chết/CCV/nhân viên không vào output đó. Ngân hàng thế chấp cả cụm, không Person. A=ủy quyền/B=được ủy quyền; một bên không gán; conflict nguồn xác nhận phần nhóm không winner/thu hẹp requester.
- Boundary: không dùng tag A/B làm filter requester; cá nhân sống văn bản một bên/đại diện ủy quyền vẫn vào output khi nhóm không gán/conflict, chỉ phần nhãn nhóm chờ xác nhận.
- Open question BANKMODE duy nhất: ô người yêu cầu Nam Định, cụm ngân hàng thế chấp do user tự dán hay app tự lấy/điền từ nguồn? Chưa chọn mode; cá nhân khác vẫn chuẩn, không hỏi mở rộng whole-cluster. Policy pháp nhân manual cũ không tự chọn mode mới; không JSON/FK/limits/old gates.
- Review: delta owner-answer independent review CLEAN, mandatory BMAD Ticket validation PASS cho draft, không closure. Parent cho commit đúng11file, không push/runtime. Giữ refined:false/hitl:true, draft/blocked chỉ BANKMODE, AC4 chưa khép; không schema/cutover hoặc đổi gate #41.

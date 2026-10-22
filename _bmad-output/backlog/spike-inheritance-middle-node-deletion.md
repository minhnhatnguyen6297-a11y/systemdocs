---
id: 21
type: spike
title: "Chốt xử lý nhánh khi xóa nút giữa sơ đồ thừa kế"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Chốt xử lý nhánh khi xóa nút giữa sơ đồ thừa kế

## Description

Chốt xử lý con/nhánh khi xóa nút giữa thừa kế. Owner đã trả lời ngày 17/10/2026: “B - gỡ cả nhánh”; cảnh báo ảnh hưởng giữ nguyên. Spike chỉ ghi đáp án và bằng chứng; implementation nằm ở #21B, không ở spike này.

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
- tracking — _bmad-output/backlog/README.md, C20
- source — _bmad-output/specs/notary_v2/README.md, §5, §9
- source — _bmad-output/specs/notary_v2/diagram-rules.md, §10

## Notes

- **17/10/2026 — owner đã trả lời; spike scope answered, không built sản phẩm.** Nguyên văn: **“B - gỡ cả nhánh”**. Tập gỡ gồm node được xóa và mọi hậu duệ active qua cạnh cha/mẹ → con, kể cả con còn parent khác; không gỡ spouse chỉ vì hôn nhân. Không giữ ô trung gian rỗng hoặc tự reparent. [Decision canonical](../decisions/decision-owner-inheritance-remove-entire-branch-20261017.md); spec Soạn thảo §5/§9, Diagram §9.9/§10 và contract §7.1/§13.4 đã đồng bộ trước code. Giữ ba AC spike nguyên văn và `refined: false`; không dùng spike để triển khai.
- **Bàn giao đúng vai trò ngày 17/10/2026:** owner chọn policy; coordinator nhận đáp án; implementer/reviewer dùng [#21B](story-inheritance-remove-entire-branch.md) và [plan](story-inheritance-remove-entire-branch-plan.md) riêng. PLAN t2/Ticket validation clean; implementation #21B **BUILT 17/10/2026**, retained Quick CODE t3 **No actionable findings**, parent accepted AC1–4. Spike này chỉ ghi đáp án/bàn giao, giữ nguyên ba AC và `refined: false`, không chứa implementation.
- **Đối chiếu ba AC ngày 17/10/2026:** (1) câu hỏi giữ/gỡ nhánh có đáp án B; nguồn/hệ quả và các phương án A/C đã loại nằm trong decision; (2) implementer có spec/contract canonical và implementation leaf riêng, việc độc lập không phải chờ; (3) owner đã nhận lựa chọn ở ví dụ A→B→C với spouse S và chọn nguyên văn ở trên, người thao tác/reviewer nhận bằng chứng đo giữ nguyên bên dưới. Quick research trước quyết định lưu ở `../tmp/issue-21-middle-node-deletion/quick-review.md`; không thay bằng review plan/code mới.
- **Lịch sử nghiên cứu trước owner chọn — 17/10/2026:** Tracking C20; #1 chỉ tracking, không chạy cùng leaf. Research worker đối chiếu nguồn và chạy phép đo cô lập; coordinator tiếp nhận bằng chứng, không coi research là quyết định sản phẩm.
- **Đã chọn:** cảnh báo ảnh hưởng khi xóa nút giữa (Description; spec Soạn thảo §5/§9 và Diagram §10, cập nhật 16/10/2026). Gỡ Diagram không xóa Người khỏi Stage; mutation chỉ sửa draft, không tự lưu; evaluate chỉ đọc; Save dùng transaction/revision hiện có, invalid không được persist, mở lại đọc canonical đã lưu. Không tự đổi cháu thành con ông/bà.
- **Hiện trạng đo ngày 17/10/2026 — hai khoảng lệch chưa sửa:** (1) × cắt quan hệ nhánh ngay, không cảnh báo/xác nhận; graph một parent Save/mở lại thành công revision 3, engine `complete`, warnings rỗng, phần của cháu synthetic đổi `1/2 → 0`; (2) nút giữa có spouse làm evaluate/Save trả `diagram_invalid_state` / `spouse_conflict` do tombstone còn link ngược, draft lỗi vẫn giữ, mở lại còn graph lưu cũ. Stage không đổi trong cả hai; mở lại không Save phục hồi bản lưu trước. Đây là evidence hiện trạng, không phải quyền giữ/cắt/xóa nhánh.
- **Phép đo và giới hạn:** actual Diagram button/model → real Python workspace services → SQLite synthetic riêng, dùng DOM stub có sẵn; không phải Electron/native UI. Không dùng user DB/process/native Word; không kiểm concurrent writes. [Source ledger và đối chiếu](../tmp/issue-21-middle-node-deletion/evidence.md), [kết quả graph/engine thật](../tmp/issue-21-middle-node-deletion/runtime-result.json), [lệnh/output và giới hạn](../tmp/issue-21-middle-node-deletion/runtime-output.txt).
- **Lịch sử trước quyết định — ba phương án đã trình owner:** khi × trên B trong **A (ông/bà) → B (con) → C (cháu)**, B có spouse S, C có parents `[B,S]`. Ngày 17/10/2026 owner đã chọn **B**; A/C không được chọn:
  - **A — Gỡ slot B, giữ hậu duệ nhưng tách B:** B về Pool; C còn trên Diagram, mất parent B và giữ parent S; S mất spouse B; quan hệ khác giữ. Không nối C lên A. Có thể cắt nhánh thế vị và đổi phần hưởng như phép đo.
  - **B — Gỡ B và toàn bộ hậu duệ theo cạnh cha/mẹ khỏi Diagram:** B, C và hậu duệ sâu hơn về Pool, kể cả C còn parent S; S không tự bị gỡ vì spouse không phải hậu duệ, nhưng dọn cạnh tới phần bị gỡ. Không xóa Stage.
  - **C — Chỉ bỏ gán người B, giữ slot trung gian và các cạnh:** B về Pool; slot B trống còn nối A–B–C và với S, C giữ cả hai parent slot. Thiếu người trung gian phải được bổ sung/đánh giá lại; không bảo đảm phần hưởng giữ nguyên.
- **Lý do từng cần owner (đã giải quyết 17/10/2026):** leaf và hai spec trước quyết định nói rõ chưa chọn giữ/gỡ nhánh; bounded search không có lựa chọn riêng. Code/test chỉ trả lời hiện trạng, không chứng minh owner muốn A/B/C. Nay decision/spec ghi B, không còn câu hỏi policy này; không hỏi lại API/schema/confirmation UI.
- **Người chờ / nơi nhận đáp án:** implementer #21B nhận semantics B tại decision + spec/contract và Notes này trước code. [Handoff nghiên cứu](../tmp/issue-21-middle-node-deletion/handoff.md) là record trước owner chọn, không là authority hiện hành; các bằng chứng đo vẫn giữ nguyên. #20 capture/defer không là technical dependency; #19/#14 deferred và #18 ngoài phạm vi, không mở lại.
- **Independent check:** reviewer không phải người thực hiện đối chiếu quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan; kết quả review lưu riêng ngoài bằng chứng tự kiểm của issue. Review không thay thế owner chọn policy, không nâng Draft/Pending thành đã duyệt.

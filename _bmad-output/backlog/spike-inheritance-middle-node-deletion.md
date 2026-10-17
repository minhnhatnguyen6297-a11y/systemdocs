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

Chốt xử lý con/nhánh khi xóa nút giữa thừa kế. Cảnh báo ảnh hưởng đã chọn; chưa chọn thuật toán cắt nhánh hoặc đổi cha.

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

- **17/10/2026 — chờ owner chọn; Draft/chưa refined, không built.** Tracking C20; #1 chỉ tracking, không chạy cùng leaf. Research worker đã đối chiếu nguồn và chạy phép đo cô lập; coordinator tiếp nhận bằng chứng, không coi research là quyết định sản phẩm.
- **Đã chọn:** cảnh báo ảnh hưởng khi xóa nút giữa (Description; spec Soạn thảo §5/§9 và Diagram §10, cập nhật 16/10/2026). Gỡ Diagram không xóa Người khỏi Stage; mutation chỉ sửa draft, không tự lưu; evaluate chỉ đọc; Save dùng transaction/revision hiện có, invalid không được persist, mở lại đọc canonical đã lưu. Không tự đổi cháu thành con ông/bà.
- **Hiện trạng đo ngày 17/10/2026 — hai khoảng lệch chưa sửa:** (1) × cắt quan hệ nhánh ngay, không cảnh báo/xác nhận; graph một parent Save/mở lại thành công revision 3, engine `complete`, warnings rỗng, phần của cháu synthetic đổi `1/2 → 0`; (2) nút giữa có spouse làm evaluate/Save trả `diagram_invalid_state` / `spouse_conflict` do tombstone còn link ngược, draft lỗi vẫn giữ, mở lại còn graph lưu cũ. Stage không đổi trong cả hai; mở lại không Save phục hồi bản lưu trước. Đây là evidence hiện trạng, không phải quyền giữ/cắt/xóa nhánh.
- **Phép đo và giới hạn:** actual Diagram button/model → real Python workspace services → SQLite synthetic riêng, dùng DOM stub có sẵn; không phải Electron/native UI. Không dùng user DB/process/native Word; không kiểm concurrent writes. [Source ledger và đối chiếu](../tmp/issue-21-middle-node-deletion/evidence.md), [kết quả graph/engine thật](../tmp/issue-21-middle-node-deletion/runtime-result.json), [lệnh/output và giới hạn](../tmp/issue-21-middle-node-deletion/runtime-output.txt).
- **Chưa chọn — đúng một policy nghiệp vụ:** khi × trên B trong **A (ông/bà) → B (con) → C (cháu)**, B có spouse S, C có parents `[B,S]`, chọn cách nào dưới đây? Cả ba đều là phương án chưa duyệt, không mặc định phương án nào an toàn hơn:
  - **A — Gỡ slot B, giữ hậu duệ nhưng tách B:** B về Pool; C còn trên Diagram, mất parent B và giữ parent S; S mất spouse B; quan hệ khác giữ. Không nối C lên A. Có thể cắt nhánh thế vị và đổi phần hưởng như phép đo.
  - **B — Gỡ B và toàn bộ hậu duệ theo cạnh cha/mẹ khỏi Diagram:** B, C và hậu duệ sâu hơn về Pool, kể cả C còn parent S; S không tự bị gỡ vì spouse không phải hậu duệ, nhưng dọn cạnh tới phần bị gỡ. Không xóa Stage.
  - **C — Chỉ bỏ gán người B, giữ slot trung gian và các cạnh:** B về Pool; slot B trống còn nối A–B–C và với S, C giữ cả hai parent slot. Thiếu người trung gian phải được bổ sung/đánh giá lại; không bảo đảm phần hưởng giữ nguyên.
- **Vì sao cần owner:** leaf và hai spec hiện hành nói rõ chưa chọn giữ/gỡ nhánh; bounded search decision không tìm thấy lựa chọn riêng. Code/test chỉ trả lời hiện trạng, không thể chứng minh owner muốn A/B/C. Không hỏi lại API/schema, transaction, quyền cảnh báo hoặc thiết kế confirmation UI để thay câu hỏi sản phẩm này.
- **Ai chờ / ghi ở đâu:** implementer đổi semantics xóa chờ owner chọn; coordinator ghi đáp án có ngày vào decision Diagram, spec Soạn thảo/Diagram và Notes này trước implementation. [Handoff](../tmp/issue-21-middle-node-deletion/handoff.md) dành cho coordinator; người thao tác/reviewer nhận bằng chứng đo ở các link trên. #20 capture/defer không là technical dependency; #19/#14 đã deferred và #18 ngoài phạm vi, không mở lại.
- **Independent check:** reviewer không phải người thực hiện đối chiếu quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan; kết quả review lưu riêng ngoài bằng chứng tự kiểm của issue. Review không thay thế owner chọn policy, không nâng Draft/Pending thành đã duyệt.

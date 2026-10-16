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

- Tracking: C02; **answered 2026-10-16** — owner chốt nguyên đề xuất ([decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md)). #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Chọn sai cách giữ/xóa gán người hoặc mapping có thể làm sai quan hệ và văn bản hồ sơ đã lưu.
- **Đáp án owner (2026-10-16, đã chốt — không còn lựa chọn mở):** khi hồ sơ **đã lưu** đổi giữa Hai bên ↔ Thừa kế: giữ ID + giá trị Người/Tài sản của Stage; **reset Diagram** (ghế/quan hệ/dấu Chủ/Nhận) rỗng theo domain mới (Thừa kế: seed **chỉ** node `owner` mới chọn — không seed khung 7 slot mặc định; quan hệ/dấu rỗng nhưng vẫn đủ key bắt buộc §13.4); **buộc chọn `document_type` hợp lệ** của loại mới + xác nhận phần Diagram mất trước khi ghi (không tự gán giá trị đầu enum); chuyển vào Thừa kế cần `owner_row_id` từ Stage, vào Hai bên cấm; giữ guard revision/khóa/atomic; binding Word không remap ngầm, không thêm chặn hồ sơ đã xuất/bound. Ngoại lệ `case_type`/`document_type` immutable — chỉ đường này (contract §13.18). Đường ghi/API do developer chọn khi triển khai #25.
- Open question (đã đóng): Khi đổi loại hồ sơ đã lưu, gán người, quyền sở hữu, lựa chọn văn bản và binding được giữ hay chuyển thế nào? Chuyển nào bị cấm; cần xem trước/xác nhận gì?
- Đối chiếu 2026-10-16 (read-only, trước khi owner chốt): chi tiết nguồn/dòng ở [`../tmp/issue-3-saved-case-policy/evidence.md`](../tmp/issue-3-saved-case-policy/evidence.md). Theo từng câu hỏi mở:
  - **Giữ gì khi đổi loại** (owner đã chọn (A)): `case_type`/`document_type` suy từ một cột `loai_van_ban`, hai enum rời nhau; Stage type-independent (Người ≤30, Tài sản ≤3 ở cả hai); Diagram hai miền khác namespace/field; repo **không** có mapping liên miền. (A) giữ ID + giá trị Người/Tài sản của Stage, **reset** Diagram đã lưu (ghế Hai bên, quan hệ Thừa kế, dấu Chủ/Nhận) theo domain mới — đúng tiền lệ nháp chưa tạo; (B) cố giữ một phần Diagram — chưa định nghĩa/nơi lưu phần "lõi" nào. Nguồn: `contracts/notary-case-drafting.md` §13.5/§13.6; `notary_v2/services/case_workspace.py`; `shell/src/renderer/notary/case-drafting-model.js:688-715`.
  - **Lựa chọn văn bản / binding Word** (**không phải câu hỏi owner**): lựa chọn mẫu không lưu trên hồ sơ (`document_keys` là input mỗi lượt xuất) nên không có gì migrate; binding DOCX đã có guard **không remap ngầm** — N/ghế đổi, hash/slot đổi → `word.original_mapping_invalid`, buộc xác nhận lại. Không thêm chặn suy đoán cho hồ sơ đã xuất/binding.
  - **Xem trước/xác nhận** (owner đã chọn): **một** confirm nêu phần mất khi reset Diagram **và** buộc chọn `document_type` hợp lệ của loại mới; phương án tự gán giá trị đầu enum bị loại.
  - **Không hỏi owner** (đủ bằng chứng/kỹ thuật): cơ chế lưu, version/revision, role/permission, và giả định cấm hồ sơ đã xuất/binding. Khóa/revision/atomic đã chốt, #25 phải giữ.
- **Phân xử thẩm quyền (2026-10-16, đã xong — không phải câu hỏi owner):** mâu thuẫn `../specs/notary_v2/diagram-rules.md` §8.2 ↔ contract §13.5 trước đây do §8.2 ghi sai. Contract §13.5 APPROVED 27/09/2026 (MIN-125; owner duyệt Q1–Q12 ngày 27/09/2026 — [`../archive/linear-tasks/MIN-125/decisions.md`](../archive/linear-tasks/MIN-125/decisions.md); `contracts/notary-case-drafting/draft-v2.schema.json` ghi "Normative text là §13") chỉ cho node two_party giữ `id`/`personId`/`hidden`/`deleted` và cấm `ownPositions`/`receivePositions`. Đã đồng bộ §8.2 và thu hẹp README §5 Chủ/Nhận về Thừa kế; không phân xử kiểu "đa số nguồn".
- Vai trò/ngày: owner (business) chốt 16/10/2026; developer/reviewer nhận bằng chứng đo (đối chiếu + phân xử §8.2). Việc UI/Diagram độc lập không chờ quyết định này.
- Ai chờ: #25 (`after: [3]`) — đã có semantics để refinement/triển khai, **chưa built**. Nơi ghi đáp án: Notes này + [decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md) + spec Notary (`../specs/notary_v2/README.md`) + contract §13.18. Bất biến loại ở runtime giữ tới khi #25 triển khai. Report d9da640e.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue. 16/10/2026 (closeout): reviewer `saved-case-decision-record-review` CLEAN — đọc đủ patch, đã kiểm liên kết + phân xử thẩm quyền; ghi nhận tài liệu, không phải bằng chứng runtime. · 16/10/2026 (t3 recheck sau Q1): reviewer `saved-case-decision-record-review` **CLEAN** — Q1 (required arrays) đã sửa: node `owner` giữ **đủ 8 key bắt buộc** với `parentSlotIds`/`ownPositions`/`receivePositions` rỗng + `spouseSlotId:null`, khớp §13.4 và `draft-v2.schema.json`; ghi nhận **tài liệu**, không phải bằng chứng code/runtime.

---
id: decision-owner-saved-case-type-conversion-20261016
title: "Owner chốt: chuyển loại hồ sơ đã lưu (Hai bên ↔ Thừa kế)"
date: '2026-10-16'
status: accepted
---

## Bối cảnh

Report `d9da640e-43fd-435e-b892-f05b517eff1f` yêu cầu sửa loại hồ sơ đã lưu; contract §13.5/§13.6 (MIN-125, owner duyệt 27/09/2026) chốt `case_type`/`document_type` **immutable** sau khi tạo nên việc này cần một ngoại lệ được duyệt. Spike #3 đối chiếu bằng chứng 16/10/2026 (`_bmad-output/backlog/spike-saved-case-conversion-semantics.md`, `_bmad-output/tmp/issue-3-saved-case-policy/evidence.md`) và nêu hai lựa chọn nghiệp vụ còn thiếu. Trong phiên 16/10/2026 owner chốt **nguyên đề xuất** của #3.

## Quyết định

Áp dụng khi hồ sơ **đã lưu** đổi giữa Hai bên (`two_party`) và Thừa kế (`inheritance`):

- **Giữ nguyên Người/Tài sản của Stage:** ID và giá trị đã lưu (`row_id` và mọi trường) không đổi. Chỉ **reset Diagram** theo domain mới — bỏ toàn bộ gán ghế (Hai bên), quan hệ Thừa kế và dấu Chủ/Nhận; domain mới bắt đầu **rỗng** (Thừa kế: seed **chỉ** node `owner` mirror đúng người vừa chọn — không seed khung 7 slot mặc định, không giữ quan hệ/dấu cũ; node `owner` vẫn **đủ 8 key bắt buộc** (§13.4) với `parentSlotIds:[]`, `spouseSlotId:null`, `ownPositions:[]`, `receivePositions:[]`).
- **Đổi `document_type`:** hai tập enum cũ/mới rời nhau nên không giữ được; người dùng **buộc chọn** `document_type` hợp lệ của loại mới. **Không** tự gán giá trị đầu enum.
- **Một bước xác nhận trước khi áp dụng:** nêu rõ phần Diagram sẽ mất rồi mới ghi.
- **Liên kết owner:** chuyển **vào** Thừa kế bắt buộc có `owner_row_id` trỏ tới một dòng Stage hiện có (người dùng chọn lúc chuyển); chuyển vào Hai bên **cấm** `owner_row_id`.
- **Không reset gì thêm** ngoài Diagram/domain cùng các guard `document_type`/owner nêu trên.
- **Guard giữ nguyên, không thêm cơ chế mới:** ghi kèm `base_revision` như mọi write; hồ sơ `locked` chỉ đọc; commit một transaction và hoàn tác toàn bộ khi lỗi; hủy/thất bại → không đổi gì (không tạo hồ sơ dở, bản cũ còn dùng được).
- **Binding Word:** giữ guard hiện hành, **không remap ngầm**; N/ghế đổi, hash/slot đổi → `word.original_mapping_invalid`. Không thêm chặn mới cho hồ sơ đã xuất/đã binding.
- **Ngoại lệ immutable:** `case_type`/`document_type` vẫn immutable sau khi tạo **trừ** đúng đường chuyển loại đã duyệt này (contract §13.18); không mở đường sửa loại tùy ý khác.
- **Đường ghi/API backend** do developer chọn khi triển khai #25; decision này không chốt command/wire cụ thể.

## Hệ quả

- #3: câu hỏi nghiệp vụ đã trả lời — leaf ghi đáp án, không còn chờ owner.
- #25: đã có semantics để triển khai; **chưa built**.
- **Lịch sử / hiệu lực:** giữ nguyên quyết định MIN-125 §13.5/§13.6 (`_bmad-output/archive/linear-tasks/MIN-125/decisions.md`) làm record. Decision này **có hiệu lực trước** trong riêng phạm vi chuyển loại đã lưu — bổ sung ngoại lệ immutable, không thay các quyết định Q1–Q12 khác.
- Spec cập nhật cùng phiên: `_bmad-output/specs/notary_v2/README.md`, `_bmad-output/specs/notary_v2/diagram-rules.md`, contract `contracts/notary-case-drafting.md` §6.1/§13.5 + §13.18; sổ tay `_bmad-output/specs/product-overview.md`; catalog C02/#3 và C24/#25.
- Schema/API (mô tả `immutable` trong `contracts/notary-case-drafting/stage.schema.json`, `draft-v2.schema.json`) do implementer #25 cập nhật cùng code — không sửa trong lượt doc này.

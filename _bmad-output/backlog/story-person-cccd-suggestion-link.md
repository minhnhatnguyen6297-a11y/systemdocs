---
id: 44
type: story
title: "Gợi ý CCCD và liên kết Người do người dùng chọn, không chặn luồng"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Gợi ý CCCD và liên kết Người do người dùng chọn, không chặn luồng

> **21/10/2026 — policy đã bị thay thế, chưa triển khai:** owner chốt tự dùng
> cùng ID khi **tên + số giấy tờ đồng thời giống nhau**, không đòi user chọn
> gợi ý. Ngày cấp/địa chỉ khác vẫn cùng ID; đổi tên/số chấp nhận ID khác.
> Lấy vào Hồ sơ mới dùng bộ mới nhất, Hồ sơ đã lưu không tự cập nhật.
> Nội dung bên dưới (mô tả, tiêu chí, giới hạn, ghi chú) giữ làm lịch sử thiết kế
> cũ, **không dùng để thực thi**.
> Chưa refine lại ticket/schema; `refined:false`, không tuyên bố built/done.
> [Quyết định hiện hành](../decisions/decision-owner-entity-anchors-case-snapshots-20261021.md).

## Description

**Mô tả cũ đã bị thay:** cho người dùng chọn liên kết dòng input với Người đã có khi CCCD có trong DB, hoặc bỏ qua để tạo Người mới. Sai khác không cản lựa chọn; người dùng quản lý thông tin liên kết. Không tiếp tục thiết kế lifecycle gợi ý này làm luồng mặc định; phạm vi thay thế tra ở quyết định hiện hành.

## Acceptance Criteria — lịch sử, đã bị thay thế

1. **Gợi ý Người hiện có**
   **Given** CCCD của dòng input đã có trong DB.
   **When** hệ thống xử lý dòng input đó.
   **Then** hiển thị gợi ý Người với ID hiện có, không tự liên kết/merge hoặc chặn luồng vì CCCD trùng.
2. **Chọn liên kết**
   **Given** đang có gợi ý Người/ID cũ cho dòng input.
   **When** người dùng bấm chọn gợi ý.
   **Then** dòng input liên kết với ID cũ và gợi ý đã chọn biến mất; không tạo ID mới cho lựa chọn này.
3. **Sai khác không chặn**
   **Given** các trường của dòng input khác Người được gợi ý.
   **When** người dùng chọn liên kết.
   **Then** liên kết vẫn được thực hiện, sai khác được ghi trong “thông tin liên kết”.
   **And** không thêm bước xác nhận vì trùng/khác tên hoặc tự chọn trường thắng/ghi đè master.
4. **Người dùng quản lý thông tin liên kết**
   **Given** đã có thông tin liên kết.
   **When** người dùng cần xem, xóa hoặc sửa thông tin đó.
   **Then** có thể thực hiện bất cứ lúc nào; không dùng thông tin này làm điều kiện chặn tiếp tục luồng.
5. **Không chọn thì tạo Người mới**
   **Given** có gợi ý CCCD đã tồn tại nhưng người dùng không chọn/bỏ qua.
   **When** dòng input được tạo thành Người.
   **Then** tạo ID mới, cho phép CCCD trùng, không auto merge hoặc tái dùng ID cũ.
6. **Lifecycle gợi ý bị bỏ qua**
   **Given** người dùng không chọn gợi ý.
   **When** owner chọn cách xử lý lifecycle và issue được triển khai.
   **Then** hành vi gợi ý tuân theo quyết định được ghi lại của owner, không tự thêm dismiss/snooze/modal/nút hoặc bước bắt buộc.
   **And** câu hỏi UX này không trở thành gate mới với người dùng; tiêu chí tạo ID mới ở mục 5 vẫn giữ.
7. **Đọc lại đúng lựa chọn và dữ liệu**
   **Given** lựa chọn liên kết hoặc tạo mới và thông tin liên kết đã được lưu.
   **When** mở lại qua consumer nghiệp vụ liên quan.
   **Then** ID và thông tin liên kết đúng lựa chọn của người dùng, không đổi snapshot đã lưu/raw/history hoặc Case links ngoài lựa chọn đó.

## Boundaries

- Một bảng Người, `Customer.id` ổn định; sống/chết vẫn là cùng Người. Không tách bảng, không mở model nhiều giấy tờ/địa chỉ #42 hoặc thực thể mới.
- Không auto merge, xóa ID, suy field thắng hoặc auto enrichment nội dung giữa văn bản. Gợi ý CCCD và user chọn liên kết là hành vi được duyệt, không phải quyền tự ghép dữ kiện giấy tờ.
- Giữ ba loại giấy chết canonical, sáu quy tắc owner, một địa chỉ, không confirmation hints, trường có căn cứ vẫn điền khi thiếu ngày chết.
- Giữ raw/history PII local, nguồn và snapshot có key null. Không thêm conditional UNIQUE, chặn CCCD/khác tên hoặc xác nhận vì trùng tên.
- Không tự thêm business/UX gate hoặc đổi hành vi chưa báo và được owner duyệt. Ưu tiên tối thiểu 80% kết quả hơn 90% cộng 10 thao tác, không đánh đổi tính đúng hoặc provenance.
- Không tự gỡ safeguard hiện có hoặc đổi wire/security/FK/atomicity. Không code/schema/tests, production DB audit, sample/corpus, cloud/portal trong lượt ghi issue.
- #41 vẫn OPEN/gate mẫu ĐÓNG; issue này không mở gate hoặc mặc định phụ thuộc #42.

## References

- quyết định owner — _bmad-output/decisions/decision-owner-upload-field-standardization-20261019.md, “Owner 21/10/2026 — gợi ý/liên kết do người dùng chọn, thay thiết kế UNIQUE”.
- contract identity — contracts/entities.md, §8.3.
- luồng chức năng được duyệt — _bmad-output/specs/notary_v2/README.md, “Luồng Người owner duyệt 21/10”.
- policy dữ liệu dùng chung — _bmad-output/specs/shared/data-rules.md, policy owner 21/10.

## Notes

- Identity: `next_id: 44` từ `tickets.py status _bmad-output/backlog` ngày 21/10/2026. Loose backlog theo waiver hiện có; active initiative unset, không setup/install/publish remote.
- Decision: owner yêu cầu “Ghi issue để làm riêng” ngày 21/10/2026. Chỉ tạo issue này, không tự tạo task audit riêng.
- Decision: UNIQUE/chặn trùng CCCD của `6eaf42b` bị thay thế; đề xuất assistant chặn khác tên hoặc thêm xác nhận vì trùng tên bị bác bỏ.
- Current fact: `f6d53b5` cho số trùng và cập nhật master theo ID explicit, chưa có đầy đủ UX gợi ý/liên kết/evidence mới. Proof death subset lịch sử không chứng minh issue này đã built.
- Open question: owner chọn lifecycle của gợi ý bị bỏ qua; hiện chưa có cơ chế được chốt làm gợi ý đó biến mất. Không đoán UI/layout hoặc thêm thao tác để lấp chỗ trống.
- Open question: shape/key/nơi lưu/cardinality và cách trình bày “thông tin liên kết” chưa chọn. Đây là khái niệm nghiệp vụ, không phải tên field/bảng/alias đã duyệt. Thiết kế lưu bền là việc của issue, không là gate mới cho người dùng.
- Open question: khi DB có nhiều ID cùng CCCD, cách trình bày danh sách gợi ý chưa chọn; không tự xếp hạng/chọn thay người dùng hoặc bịa thuật toán/fuzzy threshold.
- Risk: high — liên kết sai ID hoặc tự ghi đè trường có thể làm sai dữ liệu pháp lý. Khi triển khai được giao, cần review độc lập ngoài các AC về bảo toàn ID/nguồn/snapshot và không auto overwrite; đây không phải bước UX bắt buộc.
- Existing safeguards: blocker tên/ngày/revision/khóa hồ sơ và lớp ẩn khác chưa kiểm kê/xác minh trong lượt này. Không claim audit, không tự gỡ/chạy kiểm tra hoặc tạo thêm task audit.
- Validation (docs-only): tự kiểm theo `bmad-ticket/references/validate-checks.md` §Ticket, không delegate theo phạm vi được giao. Các reference đã mở; AC bao phủ chọn/bỏ qua/sai khác/chỉnh thông tin/đọc lại, không placeholder hay thuật toán bịa. UX/lưu bền còn mở được đánh dấu; `refined:false`, chưa sẵn sàng triển khai. Không chạy runtime/tests.

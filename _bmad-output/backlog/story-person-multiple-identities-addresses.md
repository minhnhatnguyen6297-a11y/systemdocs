---
id: 42
type: story
title: "Một Người có nhiều giấy tờ định danh và nhiều địa chỉ"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Một Người có nhiều giấy tờ định danh và nhiều địa chỉ

## Description

Owner yêu cầu ghi riêng việc một Người có nhiều giấy tờ và nhiều địa chỉ. Model hiện hành mô tả một bộ số/loại/ngày cấp/nơi cấp giấy tờ và một địa chỉ cùng nhãn; không đại diện đầy đủ nhu cầu nhiều bản ghi của cùng Người. Thiết kế model/schema, migration, cách chọn dữ liệu theo hồ sơ, extraction và export cần được refine và duyệt trước implementation; người có thẩm quyền tham gia chốt các lựa chọn này.

## Acceptance Criteria

1. **Hiện trạng và toàn bộ consumer được đối chiếu**
   **Given** model Người, dữ liệu master/snapshot, luồng nhập/bóc tách, sửa/lưu/đọc và các output đang sử dụng giấy tờ/địa chỉ
   **When** khảo sát có nguồn trong phạm vi được giao
   **Then** ghi rõ nơi đang dùng một bộ giấy tờ và một địa chỉ, giới hạn/ràng buộc hiện có và mọi consumer bị ảnh hưởng; không gọi model một giấy hiện tại là hỗ trợ nhiều giấy.
2. **Thiết kế nhiều giấy tờ và địa chỉ cho một Người được duyệt**
   **Given** nhu cầu một Người có nhiều giấy tờ định danh và nhiều địa chỉ
   **When** refine model và contract tương lai với người có thẩm quyền
   **Then** chốt key/kiểu/format/cardinality, cách nhóm giấy tờ và địa chỉ, bảo toàn nguồn, ý nghĩa và cách chọn bản dùng trong mỗi hồ sơ/output khi có nhiều bản hoặc mâu thuẫn; không tự chọn bản đầu/mới nhất hoặc ghép trường của hai giấy thành một.
   **And** thiết kế vẫn thuộc đối tượng **Người**, không thêm đối tượng nghiệp vụ thứ tư. Child records trong Người là phương án được phép xem xét, chưa phải lựa chọn đã chốt; không ép ô/chuỗi hiện có thành đa trị hoặc âm thầm nhân bản Người theo số giấy/địa chỉ.
3. **Schema/contract/migration bảo toàn dữ liệu**
   **Given** thiết kế được duyệt và dữ liệu một bộ giấy tờ/một địa chỉ hiện có
   **When** triển khai schema, contract và migration được giao trên bản sao cô lập trước cutover
   **Then** dữ liệu cũ, Người, ID/tham chiếu hồ sơ, master/snapshot và nguồn được giữ đúng nghĩa; dữ liệu chưa rõ không được tự phát minh hoặc hợp nhất. Ghi–đọc–mở lại theo contract mới giữ đủ các giấy/địa chỉ và lựa chọn của hồ sơ; lỗi không để dữ liệu ghi nửa chừng.
4. **Nhập, bóc tách và chọn dùng nhất quán**
   **Given** nguồn kiểm soát có một Người với nhiều giấy tờ/địa chỉ và đáp án độc lập
   **When** nhập/bóc tách rồi kiểm tra, sửa và lưu theo thiết kế được duyệt
   **Then** giữ đúng người, từng bộ giấy tờ và từng địa chỉ, giữ nguồn/độ đầy đủ ngày; chỗ không rõ được chỉ ra để xử lý theo quy tắc đã chốt, không gộp sai, bỏ mất hoặc đoán bản dùng. Mọi adapter/writer/reader và consumer bị ảnh hưởng được chuyển sang model mới, không để chuẩn song song chưa duyệt.
5. **Xuất đúng lựa chọn và có bằng chứng luồng thật**
   **Given** Người có nhiều giấy tờ và địa chỉ đã lưu với lựa chọn theo hồ sơ/output được duyệt
   **When** mở lại bằng consumer thật và xuất Word/điền web trong phạm vi được hỗ trợ
   **Then** output dùng đúng bản và nhóm trường đã chọn; một thay đổi master không tự làm đổi dữ kiện snapshot hồ sơ đã xác nhận. Có hồi quy một giấy/một địa chỉ, nhiều giấy/nhiều địa chỉ, thiếu/mơ hồ/xung đột, migration và lưu–đọc–xuất qua đường thật với dữ liệu cô lập; báo đúng giới hạn chưa kiểm, không dùng parser output làm golden.

## Boundaries

- Lượt này chỉ ghi issue, không thiết kế/chọn schema thay owner, không code/migration, mẫu/Word/parser/app/test/E2E.
- Không đổi chuẩn định danh/ghép Người hoặc tự gộp Case. Không chọn shared Case ID, engine DB chung, DB merge hoặc quyền tích hợp liên module.
- #41 chuẩn hóa Upload là gate riêng trước future sample batch; **#42 không tự là prerequisite** của #41 hoặc quét mẫu. Nếu implementation tương lai phát hiện phụ thuộc thật, ghi căn cứ và refine thay vì ngầm thêm gate.
- Website là SOT, người dùng tự kiểm tra/bấm Lưu; raw/provenance và dữ liệu lịch sử không bị viết lại để làm đẹp model.

## References

- parent — none
- decision — _bmad-output/decisions/decision-owner-upload-field-standardization-20261019.md, Quyết định hiện hành
- current model — contracts/entities.md, §8.1–8.2
- current behavior — _bmad-output/specs/notary_v2/README.md, Stage
- current extraction — _bmad-output/specs/shared/extraction-rules.md, §2.2–2.3
- data boundaries — _bmad-output/specs/shared/data-rules.md, §4.2

## Notes

- Decision 19/10/2026: owner “1 người có nhiều giấy tờ, địa chỉ -> ghi lại issue giải quyết riêng”. Đây là **một** issue cho cả hai nhu cầu, chưa chọn cách triển khai.
- Open question: model/schema, migration, cách chọn bản dùng, extraction và export cần thiết kế khi refine; không mặc định child table, danh sách, bản ưu tiên hoặc cách chọn UI nào đã được duyệt.
- Risk: high — chọn sai giấy tờ/địa chỉ có thể điền sai văn bản hoặc làm đổi hồ sơ cũ. Ngoài AC, cần reviewer độc lập đối chiếu thiết kế lựa chọn/snapshot và an toàn migration trước cutover.
- Identity: `next_id: 42` từ `tickets.py status _bmad-output/backlog` sau khi ghi #41 ngày 19/10/2026. Loose backlog, active initiative unset; `refined: false`, chưa giao build. Independent review lượt cập nhật docs 20/10/2026 CLEAN; parent cho commit đúng phạm vi, không publish remote/push.
- Evidence 19/10/2026: nguồn tĩnh có giới hạn ở `tools/regex_workbench/engine/contract_extract.py` dòng 3751 và 4540–4560 ghi nhánh giấy tờ phụ và các trường Người chết; `notary_v2/models.py` dòng 36–48 mô tả model Notary hiện có. Có `cccd` chính, `dia_chi` và một nhánh `cccd_khac` không chứng minh hỗ trợ đa giấy tờ/đa địa chỉ end-to-end. Chưa đọc mẫu hoặc chạy runtime. Owner R05 20/10 đã chọn alias nếu cần user điền tay, không mở rộng chuẩn hóa hoặc phạm vi #42; giữ raw/history.

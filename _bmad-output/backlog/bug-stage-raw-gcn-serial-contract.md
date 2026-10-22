---
id: 40
type: bug
title: "Đồng bộ serial GCN Stage với chuẩn nguyên văn đã chốt"
parent: none
covers: []
after: []
assignee: ""
refined: true
hitl: false
risk: high
severity: P2
---

# Đồng bộ serial GCN Stage với chuẩn nguyên văn đã chốt

## Description

Chuẩn serial GCN đã được owner chốt 06/10/2026: giữ nguyên văn tùy nguồn, có thể rỗng hoặc trùng giữa các thửa, không ép format hoặc thay mã giả. Audit nguồn hiện ghi Stage vẫn bắt buộc serial theo mẫu hẹp, chặn trùng và DB có UNIQUE; đường đọc còn có thể tạo serial thay thế. Đây là **gap implementation/spec được đối chiếu tĩnh**, không phải câu hỏi cần owner duyệt lại chuẩn serial.

Chưa tái hiện qua runtime/service/UI trong lượt docs-only này; chưa có lỗi file mẫu thực. Chỉ phần ghi/đọc serial Stage và persistence liên quan thuộc issue; không mở lại lỗi extraction đã built #7/#22, không đưa gap tĩnh này vào queue văn bản lạ #39 đang rỗng.

## Reproduction — kịch bản cần chạy khi được giao implementation

1. Dùng DB/profile cô lập và dữ liệu tổng hợp; tạo Stage hợp lệ theo contract hiện hành, không đụng dữ liệu khách hoặc DB người dùng.
2. Thử riêng serial nguyên văn ngoài mẫu hẹp, ví dụ `TEST-RAW/001`; thử serial `""`; thử hai tài sản khác thửa/tờ cùng serial nguyên văn, trong giới hạn số tài sản hiện hành.
3. Commit qua consumer Stage thật; đọc lại và mở lại bằng phiên/service mới; đi tới export thật trong phạm vi được hỗ trợ. Giữ nguyên dữ liệu người/tài sản không liên quan và nguồn đầu vào.
4. **Expected theo chuẩn đã chốt:** không từ chối chỉ do format/rỗng/trùng serial, không tự gộp thửa hoặc sửa/thay serial; lưu/đọc/xuất đúng nguyên văn và đúng tài sản.
5. **Actual đã quan sát:** chưa chạy các bước trên. Bằng chứng hiện là audit source: validator Stage yêu cầu non-empty + pattern hai chữ hoa/sáu–tám số và chặn trùng; cột DB serial có UNIQUE/NOT NULL; đường asset wire có nhánh surrogate. NOT NULL tự nó không cấm chuỗi rỗng, nhưng UNIQUE và validator hẹp phải được đối chiếu với quy tắc cho phép rỗng/trùng.

Không ghi log lỗi runtime tưởng tượng hoặc coi ca tổng hợp chưa chạy là finding trên file mẫu.

## Cause Hypothesis

Một số ràng buộc validation/persistence/projection serial cũ có thể chưa đồng bộ với chuẩn nguyên văn đã chốt, dù extraction đã được sửa. Cần xác định consumer thực sự đi qua nhánh nào và tác động schema/DB hiện có trước khi chọn cách sửa. Thiết kế migration/ràng buộc là việc kỹ thuật chưa chọn, không đổi kỳ vọng nghiệp vụ hoặc hỏi owner chốt lại serial.

## Acceptance Criteria khi được giao thực hiện

1. **Commit Stage dùng đúng serial nguyên văn**
   **Given** Stage hợp lệ với serial ngoài mẫu, serial rỗng hoặc hai tài sản khác thửa/tờ có serial trùng
   **When** commit qua consumer thật
   **Then** không chặn chỉ vì ba điều kiện serial đó, giữ đúng giá trị và từng tài sản; không tự chuẩn hóa, gộp hoặc thay surrogate.
2. **Lưu, đọc lại và xuất nhất quán**
   **Given** các ca serial trên đã commit
   **When** đọc snapshot/master theo semantics hiện hành, mở lại qua service mới rồi xuất Word bằng đường thật được hỗ trợ
   **Then** serial không bị sửa hoặc thay thế, gắn đúng tài sản; nguồn đầu vào và trường không liên quan không đổi. Không bypass gate kỹ thuật để lấy kết quả xanh.
3. **Persistence được xử lý có bằng chứng an toàn**
   **Given** DB hiện có và ràng buộc serial đã được xác định
   **When** chọn/thực hiện thay đổi cần thiết trong phạm vi được giao
   **Then** giữ bản ghi/ID/tham chiếu, serial và dữ liệu cũ; lỗi không ghi nửa chừng. Notes ghi thiết kế kỹ thuật đã chọn và kiểm chứng trên DB bản sao cô lập, không tự mặc định một chiến lược migration hoặc sửa DB người dùng.
4. **Test hồi quy có ý nghĩa ở consumer thật**
   **Given** điều kiện source tĩnh và kịch bản trên
   **When** chạy các test liên quan sau sửa
   **Then** có bằng chứng trước/sau về raw ngoài mẫu, rỗng, trùng, commit/reopen/export và bảo toàn nguồn; báo cáo ổn định ghi lệnh/kết quả/coverage còn thiếu. Output parser không trở thành golden tự sinh.
5. **Hoặc chứng minh không cần sửa ở đúng đường hiện hành**
   **Given** kịch bản trên chạy trên consumer hiện hành
   **When** hành vi đã đúng
   **Then** ghi bằng chứng thực và giải thích nhánh/ràng buộc tĩnh nào không áp dụng hoặc vì sao báo cáo sai; kết quả này thay AC sửa tương ứng, không chỉ che test hoặc xóa expected.

## References

- parent — none
- authority — contracts/entities.md, §2, owner 06/10/2026: serial nguyên văn, tùy chọn, có thể trùng
- authority — contracts/notary-case-drafting.md, §4.2 và §6.1: `so_serial` nguyên văn, không ép format
- authority — _bmad-output/specs/notary_v2/README.md, Stage / Tài sản
- evidence — D:\testcase\BAO_CAO_KHAO_SAT.md, §3.1 và §6: audit source có bounds; bản audit không thay contract
- related — _bmad-output/backlog/bug-regex-raw-serial-parcel-address.md, phạm vi extraction #7
- related — _bmad-output/backlog/story-shared-regex-consumer-cutover.md, cutover extraction #22

## Notes

- Implementation 20/10/2026 (plan approved at CHECKPOINT 1): runtime repro qua `notary_adapter.workspace_commit_stage` trên DB tổng hợp cô lập từ chối `TEST-RAW/001`, `""`, và hai thửa cùng serial; sau sửa cả ba commit OK, `workspace_get` phiên mới giữ nguyên, `word_export_batch` thật xuất đúng 3 tài sản (không `XX`). Migration chạy trên bản sao `notary_v2/notary.db`: 14 properties/14 cases, IDs/values/links giữ nguyên, `UNIQUE` bị bỏ, FK check sạch, chạy lại idempotent; **không ghi DB người dùng**. Scoped re-run after review fixes: Notary 122 passed; shell adapter/mock 244 passed, 2 skipped; word_engine 71 passed; wire Node 4 pass; renderer model Node 93 pass. Independent Quick review returned 3 blocking + 3 minor — all fixed; independent re-check 20/10/2026 CLEAN (122 / 244+2 skipped / 71 / Node 97). Commit 096495f; chưa push. [Plan](bug-stage-raw-gcn-serial-contract-plan.md) · evidence `_bmad-output/tmp/issue-40-repro/`.
- Historical evidence 19/10/2026: parent đã đối chiếu tĩnh validator Stage và ràng buộc DB được audit ghi nhận; chưa chạy runtime. Chuẩn expected đã chốt, **không có business question mới về serial**.
- Deduplication: tìm bounded backlog chưa thấy leaf riêng cho serial Stage/persistence; #7 chỉ extraction và plan của #7 loại Stage validation khỏi phạm vi. #22 là consumer regex, không phải sửa constraint Stage/DB.
- Risk: high — thay đổi liên quan định danh tài sản/ràng buộc DB có thể làm sai serial, tham chiếu hoặc dữ liệu cũ. Ngoài AC, cần reviewer độc lập xem thiết kế bảo toàn/migration và bằng chứng DB bản sao trước khi chạm dữ liệu thực.
- Severity: P2 đề xuất theo gap chức năng; tần suất/tác động runtime chưa đo, không suy outage hoặc mất dữ liệu đã xảy ra.
- Status 20/10/2026: plan approved at CHECKPOINT 1; implemented and built; independent review findings fixed and re-check CLEAN; commit 096495f; chưa push. Historical: `refined:false`/docs-only before approval; #39 vẫn rỗng, audit tĩnh không thành lỗi mẫu lạ.
- Không tạo bug từ ngày quy ước nội bộ/master khi snapshot giữ `YYYY` theo semantics đã chốt #6; optional ngày lập hồ sơ versus default DB cần phân biệt tầng, chưa là lỗi đã chứng minh. `so_giay_to` UNIQUE và không dùng làm Case key là hai quy tắc khác nhau, không tự coi mâu thuẫn.
- Identity: `next_id: 40` từ scoped `tickets.py status _bmad-output/backlog` 19/10/2026, không dùng lại ID cũ.

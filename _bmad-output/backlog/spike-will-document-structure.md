---
id: 30
type: spike
title: "Nhận diện cấu trúc Di chúc và vùng người nhận từ mẫu thực"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Nhận diện cấu trúc Di chúc và vùng người nhận từ mẫu thực

## Description

**Đã biết:** Di chúc pháp lý là đơn phương; theo context nghiệp vụ có hai bên vì có người nhận. Owner nói “Người nhận tài sản theo di chúc có vị trí khác so với các văn bản khác” trong context cấu trúc văn bản, không chỉ định ghế Diagram.

**Chưa chốt / UNSELECTED:** Vùng/vị trí người nhận, cách gắn từng người nhận với tài sản và thông tin đã ghi trong các mẫu thực chưa được cung cấp/đối chiếu. Không tự chuyển “vị trí” thành bài toán ghế Diagram.

Issue ghi riêng cấu trúc/mapping của loại văn bản này theo chỉ dẫn owner 19/10/2026, không phải lỗi parser đã xác nhận, quyết định pháp lý hoặc phê duyệt implementation. Chỉ phần phụ thuộc cấu trúc này chờ kết quả; các file/phần đã rõ tiếp tục, không chặn cả lô.

## Approach

Khi được giao bắt đầu: LLM đọc lô Di chúc thực để nhận diện phần người lập, vùng người nhận, tài sản và tham chiếu giữa các phần; phân biệt người nhận với người làm chứng/soạn thảo chỉ khi có bằng chứng. Sau khi có cấu trúc/nhãn nguồn độc lập, đối chiếu spec/code; điều chỉnh code có căn cứ và test theo quy tắc chung trong phạm vi được giao. Không tự mở rộng schema hoặc triển khai tính năng chưa được duyệt.

Phần không tự quyết được hoặc thiếu mapping ghi theo file/ứng viên vào #39 để owner xem sau, giữ pending và tiếp tục phần đã rõ. Không lấy parser output làm đáp án. Lượt hiện tại chỉ ghi tài liệu/issue, chưa đọc nội dung mẫu hoặc chạy code/test.

## Acceptance Criteria khi thực hiện

1. **Cấu trúc được nhận diện từ mẫu thực trước khi so code**
   Verify: Notes ghi danh sách nguồn/hash, vùng/nhãn và biến thể đã đọc, phần chưa có nguồn; không có mẫu tưởng tượng được gọi là bằng chứng thực.
2. **Mapping có căn cứ trong đúng ba đối tượng chuẩn**
   Verify: Notes dẫn vùng/vị trí người nhận trong mẫu, thông tin gắn đúng Người/Tài sản/Hồ sơ và những liên hệ còn pending; không có ghế Diagram tự chọn.
3. **Kết quả và phần chưa quyết được theo dõi trung thực**
   Verify: Notes ghi kết quả đối chiếu spec/code và kiểm thử nếu thực sự chạy, hoặc giới hạn chưa thực hiện. Gap dẫn #39 và giữ pending, không tính pass; không dừng các file đã rõ hoặc tự chốt nghiệp vụ/field thay owner.

4. **Chuẩn trường và báo cáo bền vững được kiểm**
   Verify: `D:\testcase\BAO_CAO_KHAO_SAT.md` liệt kê trường liên quan của Người/Tài sản/Hồ sơ: tên, kiểu, format, nhóm/thứ tự, đích DB/wire, ràng buộc và nguồn canonical; defined/Draft/ambiguous/unmapped tách riêng. Không suy mọi biến thể đã sẵn sàng từ danh sách key trong contract.
5. **Kết quả lô dùng lại được ở phiên sau**
   Verify: sau mỗi lô, báo cáo ổn định giữ nguồn/version/ngày, đã/chưa đọc/phương pháp, cấu trúc/vai trò, mapping/coverage, gap/issue, proposed/applied fix, retest đã/chưa chạy và next resume; bảo lưu kết quả cũ. Repo chỉ giữ tham chiếu/bằng chứng cấu trúc đã che dữ liệu riêng tư, raw ở nơi cục bộ của owner.

## References

- parent — none
- source — _bmad-output/decisions/decision-owner-sample-first-iteration-20261019.md, Quyết định / Phân tuyến issue
- source — _bmad-output/specs/notary_v2/README.md, Context theo loại hồ sơ
- source — _bmad-output/specs/shared/extraction-rules.md, Vòng làm việc theo mẫu thực
- source — _bmad-output/specs/shared/data-rules.md, §4.2
- follow-up — _bmad-output/backlog/spike-unfamiliar-document-review-queue.md

## Notes

- Decision: owner 19/10/2026 yêu cầu issue riêng cho loại chưa chốt cấu trúc; LLM đọc mẫu theo lô trước, thông tin luôn thuộc Người/Tài sản/Hồ sơ.
- Risk: medium — suy nhầm cấu trúc hoặc đích trường có thể xuất thiếu/sai thông tin hợp đồng.
- Status: câu hỏi nghiên cứu cấu trúc/mapping **UNSELECTED**, `refined: false`; không phải lệnh bắt đầu implementation. Owner xem phần không tự quyết được sau, không là gate dừng toàn bộ batch.
- Evidence: chưa đọc nội dung mẫu trong lượt tài liệu này; không ghi nhận file lỗi/finding thực tế hoặc khẳng định mẫu đã có trong D:\testcase.

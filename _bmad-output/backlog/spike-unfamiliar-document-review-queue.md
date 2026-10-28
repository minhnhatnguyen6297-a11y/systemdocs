---
id: 39
type: spike
title: "Tổng hợp văn bản lạ và gap mapping để owner xem sau"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Tổng hợp văn bản lạ và gap mapping để owner xem sau

## Description

Owner yêu cầu giữ vòng LLM đọc lô mẫu → nhận diện cấu trúc → so spec/code → điều chỉnh code → test lại → sai thì lặp, nhằm xuất đủ đúng thông tin hợp đồng. Văn bản lạ, thông tin không tự quyết được hoặc chưa có mapping chuẩn được tập hợp ở đây để owner xem sau, **không dừng các file/phần đã rõ**.

Đây là queue theo dõi và nhận quyết định về sau, không phải finding đã xác nhận, schema DB mới hoặc quyền triển khai. Issue riêng #30–#38 giữ câu hỏi cấu trúc theo loại đã biết; queue này liên kết tới leaf phù hợp thay vì gom mọi câu hỏi vào một câu chung. Xe vẫn theo #29 DEFERRED.

## Approach khi được giao chạy lô

- Đọc `D:\testcase\README.md` và báo cáo ổn định `D:\testcase\BAO_CAO_KHAO_SAT.md` trước; dùng lại kết quả có nguồn còn phù hợp thay vì tự khảo sát lại mọi thứ.
- LLM đọc file mẫu thực và lập nhãn/giá trị nguồn độc lập trước so code. Chỉ ghi vào queue khi gặp phần cụ thể không tự quyết được; không suy lỗi từ thiếu enum.
- Mỗi record repo theo file/ứng viên chỉ ghi ref nguồn an toàn hoặc đường dẫn đã che dữ liệu riêng tư, version/ngày/hash và vị trí trang/đoạn/bảng/ô; trích cấu trúc đã che giá trị cá nhân khi cần. Ghi mapping Người/Tài sản/Hồ sơ tới trường canonical đã duyệt, trạng thái ambiguous/unmapped, tác động, issue theo loại và điều cần owner xem. Đường dẫn nhạy cảm, raw Word, CCCD và chi tiết khách chỉ ở báo cáo/nguồn owner-local theo quyền hiện có, không chép vào Git/log rộng.
- Các thông tin trên là metadata workflow/bằng chứng, không phải tên trường nghiệp vụ mới. Không nhét gap vào ghi chú nghiệp vụ, không đặt field/alias/thuế/quan hệ theo suy đoán.
- Giữ nguyên nguồn/ứng viên, đánh dấu pending/chưa kiểm và tiếp tục các file/phần đã rõ. Không tính record pending là pass, không xóa/âm thầm loại khỏi mẫu số để báo đủ đúng toàn lô. Thiếu mapping chặn phần phụ thuộc, không chặn batch.
- Sau mỗi lô cập nhật báo cáo ổn định nêu phần đã đọc/chưa đọc/phương pháp, cấu trúc và vị trí các bên, field catalog có tên/kiểu/format/nhóm thứ tự/đích DB-wire/ràng buộc và nguồn thẩm quyền; phân biệt defined/Draft/unmapped. Ghi code gap, issue, đề xuất/sửa đã áp dụng và retest thực sự quan sát được, pending và điểm tiếp tục. Giữ kết quả lô trước bằng mục có ngày hoặc tham chiếu lịch sử thuộc sở hữu; không chỉ để báo cáo trong tmp.
- Không tạo logging/telemetry hoặc schema DB nghiệp vụ từ queue. Báo cáo field catalog là audit hiện tại, không phải contract mới; chưa đọc body phải ghi coverage nội dung 0.

## Acceptance Criteria khi thực hiện

1. **Bằng chứng thật, không tạo lỗi giả**
   Verify: từng record có ref an toàn/version/hash/vị trí/phương pháp và điều chưa quyết có căn cứ; không nhận diện nào được ghi là đã đọc khi chỉ biết tên file. Không có raw Word, CCCD hoặc dữ liệu khách trong repo/log rộng.
2. **Chuẩn trường được kiểm trước tuyên bố mapping đủ**
   Verify: báo cáo liệt kê trường Người/Tài sản/Hồ sơ liên quan với tên, kiểu, format/độ đầy đủ ngày, cách nhóm/thứ tự, đích DB/wire, ràng buộc và nguồn canonical; defined, Draft và ambiguous/unmapped tách riêng. Có code không tự chứng minh trường đã được duyệt.
3. **Không chặn vòng và không làm sai số đạt**
   Verify: record unresolved giữ pending, dẫn issue theo loại và phần bị ảnh hưởng; kết quả file đã rõ tiếp tục được ghi. Không có field tự tạo, record bị loại im lặng hoặc claim toàn bộ đạt khi còn thiếu.
4. **Báo cáo ổn định dùng lại được sau mỗi lô**
   Verify: `D:\testcase\BAO_CAO_KHAO_SAT.md` ghi kết quả lô, nguồn/coverage, code gap/issue, proposed/applied fix, retest đã/chưa chạy và next resume; giữ kết quả cũ. Phiên sau đọc báo cáo trước lô mới, không chỉ có log/tmp hoặc snapshot ghi đè mất lịch sử.
5. **Owner có dữ liệu để xem sau đúng phần**
   Verify: câu hỏi/đề xuất dẫn bằng chứng và leaf loại văn bản nếu có; quyết định owner được ghi có ngày khi thực sự nhận, không tự chốt thay. Trạng thái chưa quyết không trở thành nghiệm thu pháp lý hoặc implementation approval.

## References

- parent — none
- source — _bmad-output/decisions/decision-owner-sample-first-iteration-20261019.md
- source — _bmad-output/specs/shared/extraction-rules.md, Vòng làm việc theo mẫu thực
- source — _bmad-output/specs/shared/data-rules.md, §4.2
- context — _bmad-output/specs/notary_v2/README.md, Context theo loại hồ sơ

## Queue bằng chứng thực tế

**Rỗng tại lúc lập issue 19/10/2026.** Chưa đọc nội dung file mẫu, chưa nhận diện văn bản lạ hoặc ghi nhận lỗi thực tế trong lượt chỉ tài liệu này. Không có record giả để minh họa.

## Notes

- Decision: owner 19/10/2026 — văn bản lạ/không tự quyết được ghi issue tổng hợp để xem sau, không dừng vòng; quy tắc lưu bền vững để không phải nhắc lại.
- Risk: medium — bỏ mất thông tin pending có thể làm claim xuất đủ đúng không trung thực.
- Status: `refined: false`; ghi quy trình và queue rỗng, không bắt đầu khảo sát/code/test trong lượt này. Metadata queue không bổ sung schema nghiệp vụ.
- Báo cáo ổn định do tác giả ngoài repo phụ trách tại `D:\testcase\BAO_CAO_KHAO_SAT.md`; không suy rằng báo cáo khởi tạo đồng nghĩa đã đọc lô mẫu. Chuẩn trường chỉ được gọi là rõ khi có audit nguồn canonical thực tế.

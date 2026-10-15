---
id: decision-owner-doc-clarifications-20261015
title: "Chốt ranh giới dữ liệu và dọn yêu cầu sau audit docs"
date: '2026-10-15'
status: accepted
---
## Bối cảnh

Owner trả lời từng mục của danh sách audit ngay trong phiên 15/10/2026.
Nguồn chốt là các câu trả lời đó; không đòi owner dẫn lại kế hoạch cũ đã mất.

## Quyết định

- Mục 2: Zalo chỉ gợi ý Case; chuyên viên xác nhận rồi mới liên kết tài liệu.
- Mục 3: loại bỏ toàn bộ thiết kế theo dõi bản in khỏi tài liệu dự án, kể cả
  connector, bảng dữ liệu, ví dụ và ý tưởng cũ. Không chỉ đổi nhãn trạng thái.
- Mục 5: lưu/hiển thị đúng dữ liệu ngày nhập và độ đầy đủ. Ngày quy ước cho
  dữ liệu chỉ có năm chỉ phục vụ tính toán nội bộ, không ghi đè đầu vào.
- Mục 6: cho lưu sơ đồ hợp lệ nhưng `incomplete` làm bản nháp, hiển thị rõ
  phần thiếu. Xuất Word giữ điều kiện mode/mẫu đã có; không thêm chặn mới.
- Mục 9: bỏ link HTML báo cáo launcher cũ đã mất, không tạo lại bằng chứng giả.
- Mục 10: loại đề xuất tự phục hồi tên người chết theo tên gọi tắt vì owner
  chưa từng yêu cầu. Không tự mở lại dưới dạng tính năng hoặc câu hỏi chờ duyệt.
- Mục 11: trong cùng khối nguồn, thông tin một thửa được viết liên tục; số
  thửa đất + số tờ là dấu hiệu phân biệt chính. Chi tiết nối tiếp thuộc thửa
  tương ứng. Không suy thành khóa chung để tự nối file/địa phương/module.
- Mục 12: giữ bộ trường/format theo DB đã duyệt; engine phải theo chuẩn đó,
  alias cũ ánh xạ tường minh, không tạo dữ liệu mồ côi. Không duyệt thuật toán
  chọn một phía khi hai giá trị nguồn mâu thuẫn.

## Phạm vi chưa duyệt

- Mục 1 là yêu cầu kiểm tra cơ chế Lưu portal, chưa duyệt tín hiệu mới hoặc
  nâng `upload-workflow` Draft thành Approved.
- Mục 4: bảng đơn dòng/decision-72 chưa được duyệt.
- Mục 7: chỉ cung cấp đủ danh sách 56 quyết định accepted có thân trống;
  không tự bổ sung nội dung hoặc coi owner vừa duyệt lại cả 56 mục.
- Mục 8: trình bày nội dung còn đọc được của decision-48 để owner xem rồi
  duyệt. Chưa có phê duyệt mới; không dựng lại nội dung kế hoạch task-3 đã mất.

## Hệ quả

Spec/module ghi đúng ranh giới trên; phần Office và nghiệp vụ thừa kế Draft
còn lại vẫn Draft. Đây là thay đổi tài liệu, chưa sửa hay nghiệm thu engine,
schema, UI hoặc bộ đáp án. Nội dung đã dọn vẫn có thể truy lại trong Git khi
cần lịch sử, nhưng không còn được dùng như yêu cầu hiện hành.

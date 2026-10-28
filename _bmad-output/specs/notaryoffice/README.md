# NotaryOffice — hỗ trợ theo dõi công việc văn phòng

**Cập nhật:** 17/10/2026. **DEFERRED theo owner:** “notaryoffice để lại, tôi sẽ làm sau”. Giữ toàn bộ thiết kế Draft, chưa có runtime được nghiệm thu; không giao pilot, phép đo A1/A3/A4, code, schema hoặc runtime Office lúc này. Không xóa spec/công việc, không tự đặt hạn mở lại hoặc triển khai các con số đề xuất. [Quyết định owner](../../decisions/decision-owner-notaryoffice-deferred-20261017.md).

## 1. Vấn đề và mục đích

Một người/tài sản có thể liên quan tới nhiều việc kéo dài: soạn văn bản, nộp hồ sơ chuyển nhượng, chỉnh lý giấy chứng nhận, đo đạc, đổi địa chỉ. Thông tin rải trong file và trí nhớ; khi hỏi “Hồ sơ đang ở đâu?” khó nhìn lại toàn bộ diễn biến.

Module gom dấu vết công việc để hỗ trợ nhân viên và quản lý. Không ép nhập một quy trình quản lý doanh nghiệp cứng nhắc, không dùng dấu vết để chấm công hay phán quyết pháp lý.

## 2. Luồng dự kiến

Thay đổi nội dung Word trong phạm vi được phép → đọc chữ bằng IFilter/công cụ đã chốt → bóc Người/Tài sản/Hồ sơ → tạo dấu vết có nguồn → nhóm thành ứng viên công việc → hiện thẻ ngắn cho nhân viên xác nhận/sửa/gộp/bỏ qua → lưu vào dòng thời gian → tìm lại.

Thay đổi file chưa chứng minh đã hoàn thành thủ tục. Chỉ dữ liệu được người có quyền xác nhận mới mang nhãn đã xác nhận. Điểm tin cậy chỉ xếp thứ tự gợi ý, không tự loại bằng chứng hoặc gộp hồ sơ.

## 3. Dữ liệu và ranh giới

Mỗi dấu vết cần nguồn, thời gian, máy trạm và Người/Tài sản/Hồ sơ có căn cứ; thiếu thì để trống/cảnh báo. Giữ nguồn gốc và các thay đổi, không sửa raw để khớp kết luận. Hồ sơ vận hành không mặc định tương ứng một-một với hồ sơ soạn thảo.

Mô hình dự kiến gồm nguồn tài liệu/snapshot/thay đổi, bằng chứng, ứng viên, hồ sơ xác nhận, đối tượng liên quan, công việc, sự kiện dòng thời gian và phản hồi hiệu chỉnh. Các tên bảng cũ như evidence_records, draft_cases, cases, case_entities, work_items, artifacts, document_snapshots, document_deltas, calibration_logs, case_timeline_events chỉ là thiết kế logic chưa cấp quyền tạo DB production.

Zalo hiện nghiên cứu tách riêng, không nối vào flow. Nếu sau này được cho phép dùng, trùng GCN chỉ tạo gợi ý; chuyên viên xác nhận mới gắn vào hồ sơ. Không đọc tin riêng/tài khoản riêng của nhân viên.

## 4. Thẻ xác nhận và tìm kiếm

Thẻ hiển thị việc được đề xuất, Người/Tài sản/Hồ sơ liên quan và bằng chứng. Có Đúng, Bỏ qua, Sửa/Gộp; trạng thái dự đoán luôn có nhãn. Tìm kiếm dự kiến theo tên, giấy tờ, GCN, thửa/tờ hoặc chuyên viên; kết quả phân biệt đã xác nhận với dự đoán.

Giảm làm phiền để tránh nhân viên bấm theo phản xạ. Mốc tối đa 3 popup/người/ngày và bấm dưới 1,5 giây là đề xuất cũ có điều kiện, không phải quy tắc đã duyệt toàn bộ. Dùng chung tài khoản Windows thì không tự nhận diện người thao tác. Không suy việc bấm nhanh là hành vi gian dối.

## 5. Hướng kỹ thuật và phần chưa chốt

Đề xuất máy trạm thu dấu vết, giữ hàng chờ khi mất LAN; Hub trong LAN chuẩn hóa, so thay đổi và dựng ứng viên. Rule xử lý phần chắc chắn, AI chỉ hỗ trợ mơ hồ; không có state nghiệp vụ riêng trong AI. Máy trạm không gọi Internet.

Phương án xử lý tất cả tập trung hoặc tất cả tại máy con từng được cân nhắc; lý do và phương án bỏ nằm trong hồ sơ quyết định. Thiết kế hybrid hiện cũng chưa được duyệt toàn bộ.

| Cần xác minh/chốt | Vì sao |
|---|---|
| IFilter đọc file Word đang mở (A1) | Không giả định file khóa vẫn luôn đọc được |
| Sự kiện trên ổ mạng (A3) | Không giả định nhận đủ mọi thay đổi |
| Tài khoản riêng trên sáu máy (A4) | Quyết định có thể nhận biết người làm hay phải bỏ phần đó |
| Ghép phiên và dấu vết thành công việc | Tránh cùng người/tài sản bị nối sai hồ sơ |
| Thời điểm/thông tin popup, lịch nhắc | Cần kiểm thực tế, không mặc định các ngưỡng cũ |
| Schema, lưu giữ, quyền xác nhận | Chưa là hợp đồng triển khai production |

## 6. Cách đánh giá khi triển khai

Đo bằng câu hỏi thực tế “hồ sơ ở đâu/chờ gì”, độ đúng định danh và công sức xác nhận. Các mốc cũ 8/10 câu hỏi, gần 0 ghép sai, một thao tác ngắn/ngày là mục tiêu Draft; chưa phải kết quả đo hoặc điều kiện đã được duyệt. Tập mẫu và tiêu chí phải chốt trước nghiệm thu.

Code menu hiện chỉ là điểm vào thông báo; không suy có UI đầy đủ từ việc có module trong thanh bên. Bản ý tưởng cũ được lưu trong archive để tra cứu, không phải spec bắt buộc đọc đầu phiên.

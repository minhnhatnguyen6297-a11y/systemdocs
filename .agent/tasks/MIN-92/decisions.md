# Decisions — MIN-92

## 2026-09-24 — Owner chốt các điểm mở của contract liên repo

Nguồn: owner trả lời trực tiếp trong phiên triển khai MIN-91 (24/09/2026). Đây là các điểm issue MIN-92 ghi "cần quyết định trong contract trước runtime".

- **Khóa quota OCR bổ sung:** từng trang = `logical_id` của ảnh/trang. **Loại bỏ:** cả attachment (GCN nhiều trang dễ hết lượt).
- **Hạn mức:** 2 job OCR bổ sung mỗi khóa trong toàn hạn 168 giờ; 100 lượt Qwen mỗi consumer trong cửa sổ trượt 24 giờ; 2 job đồng thời; retry lỗi provider tối đa 3 lần/job có backoff; lượt timeout/không rõ đã tới provider vẫn tính ngân sách. **Loại bỏ:** 1/50/1 (dễ thiếu chữ), 3/200/2 (chi phí cao).
- **Raw trên bot sau ACK:** giữ 30 ngày tính từ ACK accepted, trần 1 GiB cho gói đã ACK, cảnh báo ở 80%; chạm trần chỉ dọn sớm gói đã ACK cũ nhất; không bao giờ xóa gói chưa ACK. **Loại bỏ:** 14 ngày/512 MiB, 90 ngày/2 GiB.
- **Transcript mặc định:** `text_lines` là lượt thành công của pipeline OCR mặc định lúc bắt ảnh; lượt bổ sung chỉ thêm vào `ocr.attempts[]` ở revision mới, `selected_pass_ids` giữ nguyên; Document Intake tự xét mọi attempt. **Loại bỏ:** thay bằng lượt mới nhất; gộp các lượt.
- **Kích hoạt OCR bổ sung:** backend Document Intake tự gửi khi quy tắc đề xuất và ảnh còn hạn, trong ngân sách; UI có nút gửi tay theo quyền. Đây là chính sách consumer, API như nhau. **Loại bỏ:** chỉ bấm tay; chỉ tự động.
- **Một variant mỗi request.** **Loại bỏ:** nhiều variant/request (lỗi và quota từng phần).
- **`source_event` có trong v1** cho loại adapter phát được thật; loại khác báo chưa hỗ trợ ở `/status`; không tự sửa raw/hồ sơ cũ. **Loại bỏ:** hoãn sang v1.1.

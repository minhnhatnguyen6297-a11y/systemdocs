# Thuật ngữ (systemdocs)

Nguồn chuẩn nghĩa nghiệp vụ thừa kế: [`business-rules.md` §1](specs/notary_v2/diagram/inheritance/business-rules.md#1-thuật-ngữ) và sổ [`decision-80`](decisions/decision-80-so-quyet-dinh-nghiep-vu-thua-ke.md). File này là danh mục tra nhanh; khi lệch, `business-rules.md` và D-xxx thắng.

| Từ | Nghĩa ngắn | Nguồn |
|---|---|---|
| Stage | Danh sách Người của hồ sơ (có giấy tờ cá nhân); nguồn sự thật duy nhất, mọi màn hình là view | D-003, `specs/notary_v2/stage.md` |
| Pool | Người có trong Stage nhưng chưa gán lên sơ đồ; người bị gỡ trả về Pool | D-009, `specs/notary_v2/pool.md` |
| Diagram / sơ đồ | Sơ đồ thừa kế; chỉ dùng cho hồ sơ thừa kế | D-049, `specs/notary_v2/diagram-rules.md` |
| Ô (slot) | Chỗ trống do engine tạo/xoá theo luật; user không tạo/xoá ô | decision v2, D-043 |
| Thẻ (card) | Người được thả vào một ô; user chỉ thả/di chuyển/gỡ thẻ, tích Chủ/Nhận | decision v2 |
| Chủ đất | Người có dấu "Chủ" trên tài sản `k`; di sản = phần của chủ đất, chia đều | D-020, D-040 |
| Người nhận | Người có dấu "Nhận" trên tài sản `k` | D-008 |
| Từ chối (nhãn) | Người có suất, không tích Nhận — **trừ** người còn sống chưa tích: chỉ nhắc, không phải từ chối. Không phải văn bản 620 | D-024, D-046, D-014 |
| Nhường phần | Không phải từ chối nhận di sản | D-014 |
| Vòng di sản | Phần tài sản một người nắm tại ngày chết, đem chia | R-xx §1 |
| Đơn vị / suất | Một suất trong hàng 1 của một vòng (cha, mẹ, vợ/chồng, mỗi nhánh con) | §1 |
| Nhánh | Một con của người để lại di sản cùng hậu duệ, tới chắt | D-012 |
| Thế vị | Con chết **trước** người để lại di sản: cháu/chắt hưởng thay, tối đa tới chắt | D-012, D-025 |
| Chuyển tiếp | Con chết **sau** người để lại di sản: phần của con thành di sản của con | D-010 |
| Ô vợ/chồng (node kép) | Nhóm ô vợ/chồng trên node người chết có tài sản và trên chủ đất còn sống; người thả cuối là hợp pháp, người trước bị làm nhạt, không in Word | D-041, D-042 |
| Con riêng | Nút trên thẻ con xoá cha/mẹ tự điền | D-043 (luật A) |
| Hàng 1 / 2 / 3 | Hàng thừa kế theo BLDS 651; hàng 2/3 đang gác sau cờ `ENABLE_LATER_LINES` | D-038, D-044 |
| Hoàn tác | Khôi phục nguyên trạng trước thay đổi cascade; engine chạy lại sau khi khôi phục | decision v2, D-047 |
| D-xxx / Q-xxx / R-xx | Mục quyết định (decision-80) / câu hỏi mở (business-rules §10) / quy tắc (business-rules) | decisions/README.md |
| S5b | Điều kiện số thửa/tờ bản đồ bắt buộc khi Lưu | D-048 |

# G1 — đồng bộ mặc định vị trí tài sản (B)

Owner chốt phương án B trong lượt tiếp LÁT 1; hiệu chỉnh vòng sửa lỗi E2E 23/10.

- Thừa kế: owner đã gán người có mặc định Chủ; node khác đã gán người có mặc định Nhận. Mảng chưa được user tự chỉnh chip cho đúng node + kind trong phiên đồng bộ đầy đủ `{1..len(assets)}` khi thêm/gỡ tài sản và trước Lưu hồ sơ/Lưu nháp.
- Mảng đã chỉnh tay, kể cả rỗng, không tự ghi đè. Dấu touched chỉ ở state phiên, ngoài Diagram/wire; giữ qua Lưu trong cùng phiên, reset khi mở hồ sơ/phiên mới hoặc reset Diagram do đổi loại.
- Owner đang rỗng không tự điền nếu node khác đã có vị trí Chủ. Không đổi `applyAssignDefaults()` tại thời điểm gán.
- Bỏ quy tắc cũ không mở rộng mảng mặc định khi thêm tài sản: mảng chưa chỉnh phải theo đủ tập tài sản hiện có; phân biệt rỗng mặc định và rỗng do user tắt hết.

Phạm vi chỉ G1; giữ nguyên G2 hiện có, không đổi backend/schema và không mở gate mẫu. Contract §13.4 và spec Sơ đồ §9.3 ghi hành vi áp dụng.

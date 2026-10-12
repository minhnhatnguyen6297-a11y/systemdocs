# Làm rõ chuyển bước, ngoại lệ và hoàn tất flow coding

## LÀ GÌ

User duyệt sửa các khoảng trống trong review file adaptive-coding-flow.md:
- Chọn route sau inspect dựa trên điểm bất định/rủi ro cụ thể, không dựa đơn thuần số dòng hay số owner.
- Các bước planning có điều kiện kích hoạt và thoát; phần phụ thuộc quyết định user phải chờ.
- Handoff có mục tiêu, nguồn hành vi, phạm vi, constraints, nghiệm thu và verification.
- Worker mất phiên được thay thế sau kiểm tra trạng thái; reviewer thiếu kết quả không được coi là sạch.
- Test phải chứng minh hành vi; patch phải kiểm tra lại; lỗi nền tảng lặp lại quay về intent/plan.
- Tự implement trực tiếp không đồng nghĩa bỏ review. Orca không khả dụng khi được yêu cầu thì báo blocked, không âm thầm đổi transport.
- Tách điều kiện hoàn tất task khỏi nghiệm thu cấu hình workflow.

## TẠI SAO

Review chỉ đọc file chỉ ra policy chưa đủ quyết định bước tiếp theo hoặc xử lý thất bại. Bổ sung quy tắc ngắn trong contract và field customization hiện có, không tạo framework/daemon hoặc sửa installed skills.

Các phần worker ban đầu và ngoại lệ review không rõ trong quyết định trước được thay bằng contract cập nhật. Quyết định transport native mặc định, Orca on request không đổi.

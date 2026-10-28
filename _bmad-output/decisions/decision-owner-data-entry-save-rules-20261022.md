---
id: decision-owner-data-entry-save-rules-20261022
title: "Owner chốt nguồn done, cách đối chiếu và rà soát hai bước lưu"
date: '2026-10-22'
status: accepted
---

## Các quyết định owner đã trả lời

1. Bộ thông tin lấy lại mặc định theo **Hồ sơ được lưu mới nhất**; không lấy
   theo ngày giấy tờ hoặc độ đầy đủ. **Draft không được đưa làm nguồn**.
2. Điểm neo Người vẫn là tên + số giấy tờ đồng thời. Tên chấp nhận không dấu/
   có dấu, không phân biệt hoa/thường, ví dụ `nguyen van a` và `nguyễn văn A`.
   Giữ tên gốc để hiển thị/xuất; chi tiết chuẩn hóa ký tự chưa phải thuật toán
   đã triển khai, không suy đã duyệt so gần đúng mọi lỗi gõ hoặc đổi số giấy.
3. Thiếu điểm neo thì không gom cùng ID với đối tượng khác. Quy tắc này chưa
   quyết định lifecycle ID của chính dòng đang nhập dở qua nhiều lần Cập nhật.
4. Nhiều ID trùng đã có trong DB **giữ nguyên, không tự gom**; dùng nguyên tắc
   lấy bộ cuối cùng. Lịch sử để user xử lý; không tự xóa/chuyển các liên kết cũ.
5. Tài sản cùng serial gom vào một ID dù khác thửa; giữ từng bộ thông tin
   theo Hồ sơ, không tự thêm điều kiện phải cùng thửa/tờ hoặc gộp mất hàng.
6. **Nhân bản toàn bộ** nội dung Hồ sơ sang Hồ sơ mới; không tự bớt một phần
   theo đề xuất trước đó. Cách lưu và liên kết vẫn phải được thiết kế.
7. Owner yêu cầu đổi nút **Lưu sơ đồ** thành **Lưu hồ sơ**: lưu Diagram và
   chuyển `draft` sang `done`. Không tự hiểu done là đủ sáu trường hoặc đã
   công chứng. Cách tính các báo cáo còn chưa chốt.
8. Owner đã giao tạo issue/chỉnh nút lưu và chức năng copy/paste kiểu Excel,
   sau đó yêu cầu **tạm dừng, chưa code để rà soát cấu trúc dữ liệu**.

## Yêu cầu rà soát hiện tại

Mô phỏng hai ý định: **Cập nhật** ghi thông tin Người/Tài sản vào database;
**Lưu hồ sơ** ghi quan hệ bảng liên kết và trạng thái Hồ sơ. Đây là mục tiêu
để phản biện, chưa duyệt thiết kế vật lý hoặc mọi chi tiết chuyển trạng thái.

Tình huống trọng tâm: nhập tên nhưng chưa có số → Cập nhật tạo một ID → bổ
sung số → Cập nhật tiếp. Phải phân biệt mã dòng trong Hồ sơ với ID Người và
kiểm các nhánh điểm neo chưa có/đã có, đổi/xóa neo, nhiều ID cũ, các thứ tự
bấm nút và sửa Hồ sơ done.

Các đề xuất giữ ID tạm, đổi liên kết của dòng hiện tại, giải quyết điểm neo
tại Cập nhật hay Lưu hồ sơ, tự cập nhật Stage khi Lưu hồ sơ và cách xử lý sửa
Hồ sơ done **chưa được owner chọn**. Không đưa đề xuất mô phỏng vào runtime.

## Ranh giới

- Địa chỉ cũ–mới giữ cách hiện tại, không mở mô hình mới.
- Một Hồ sơ một snapshot hiện hành; không lịch sử từng ô/lần lưu; Hồ sơ khác
  không tự đổi, raw/nguồn/history kỹ thuật đã có vẫn giữ.
- Không chạy code sản phẩm, test, migration, đọc mẫu khách hàng hoặc production
  DB trong lượt rà soát. Git sạch ở `b89a482513f8b714141f75dda664a712bebbfe6c`
  trước ghi tài liệu; lượt triển
  khai bị ngắt mới đọc source/render workflow, chưa đổi code sản phẩm.
- Quy tắc 21/10 còn hiệu lực trong phần không bị làm rõ ở đây; không tự đặt
  thiết kế DB còn mở làm gate cho mọi việc regex/placeholder đã rõ.

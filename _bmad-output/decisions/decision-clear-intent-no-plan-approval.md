# Yêu cầu rõ: triển khai đến khi kiểm chứng, không xin duyệt plan

Ngày: 2026-10-12

## Quyết định của user

Khi yêu cầu đã rõ và không còn lựa chọn business/UX nào chưa chốt, agent tự triển khai đến khi kiểm chứng xong rồi báo kết quả; không dừng xin duyệt plan.

## Vì sao

User là solo-vibecoder, muốn quyết định sản phẩm thay vì điều hành quy trình coding. Độ khó kỹ thuật có thể đòi hỏi chuẩn bị, plan nội bộ hoặc worker, nhưng riêng độ khó đó không phải lý do yêu cầu user duyệt plan.

## Ranh giới

- Không bỏ kiểm chứng hoặc review theo workflow đã chọn.
- Quyết định này không cho phép agent tự chốt lựa chọn business/UX còn mở, mở rộng scope, hoặc bỏ qua yêu cầu xác nhận an toàn cho thao tác rủi ro/phá hủy.
- Giữ nguyên cấu trúc HTML Plan của Thariq theo quyết định đã ghi; không yêu cầu HTML chỉ để thêm một checkpoint duyệt vào việc đã rõ.
- Đây là quyết định hành vi từ phiên brainstorming; chưa sửa spec, override hay implementation để áp dụng nó.

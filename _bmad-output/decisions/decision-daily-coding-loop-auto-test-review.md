# Coding loop tự chạy đủ, không chờ user nhắc test/review

Ngày: 2026-10-12

## Quyết định của user

- Yêu cầu tối thiểu: agent tự thực hiện đầy đủ vòng lặp coding, gồm triển khai, kiểm chứng/test và review; không đợi user ra lệnh riêng "test đi" hay "review đi".
- Khi user phát hiện và report lỗi, agent chạy lại vòng lặp đó cho lần sửa.
- Không đặt điều kiện brainstorming phải hoàn hảo trước khi coding. User chấp nhận tiếp tục phát hiện lỗi qua sử dụng và phản hồi.

## Vì sao

User là solo-vibecoder, không muốn điều hành các bước kỹ thuật mỗi ngày. Mục tiêu là kỷ luật thực thi ổn định, không hứa không có lỗi hoặc tăng ceremony để bảo đảm mọi ý định được khám phá hoàn hảo.

## Phạm vi

- Giữ BMAD làm nguồn workflow và OMP làm nơi điều phối thực thi; không dựng workflow độc lập thay thế.
- Thiết kế điểm kích hoạt và cơ chế áp dụng phải dựa trên implementation hiện có. Quyết định này mới ghi yêu cầu hành vi; chưa thay đổi spec/override/code.
- Bổ sung quyết định yêu cầu rõ thì không dừng xin duyệt plan; không thay đổi cấu trúc HTML Plan Thariq đã chốt.

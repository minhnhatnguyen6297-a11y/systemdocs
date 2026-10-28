# HTML plan là tài liệu trực quan, không phải app developer mode

> **Bị thay bởi [decision-81](decision-81%20-%20Bo-BMAD-thu-Superpowers-docs-chuyen-sang-docs.md) (28/10/2026).** Giữ để tra lịch sử.

Ngày: 2026-10-10. Nguồn: yêu cầu hiện tại của owner.

## Quyết định

Cải thiện plan/spec HTML của BMAD để owner nhìn và hiểu kết quả sau implementation: giao diện dự kiến, trạng thái user nhìn thấy và hành vi thay đổi. Exhibit là nội dung chính; không bọc Markdown, không biến tài liệu thành dashboard review hoặc app developer mode. Tương tác phục vụ hiểu nội dung (mở chi tiết, xem trạng thái, đối chiếu hình), không lấy form/feedback/export JSON làm mục tiêu chính. Giữ WHY → WHAT → HOW → WHERE dưới dạng cây hành vi, không bốn section chữ dài. HTML không thay spec/code/Git làm nguồn chuẩn.

## Lý do

Owner báo bản hiện tại tệ hơn HTML BMAD trước đây. Quan sát bản `docs/tmp/diagram-error-plan-20261009/plan.html`: nút duy nhất là copy, không có input lựa chọn và không có sơ đồ; generator chuyển Markdown theo dòng. Bọc chữ bằng HTML không đáp ứng mục tiêu đọc nhanh, hiểu đúng và phản hồi ngay tại ngữ cảnh.

Owner đã bác đề xuất renderer/ingest và app review của agent ngay trong phiên: “thứ tôi cần là 1 bản plan hoặc spec đủ trực quan, thậm chí có hình minh họa app thật sẽ trông như thế nào sau khi implement”. Đề xuất này chưa được duyệt, không được triển khai hoặc tự resume.

## Giới hạn

Giữ BMAD và Orca hiện hành; chưa sửa core/override. Plugin đúng đã xác minh qua metadata tác giả: `anthropics/claude-plugins-community/html-plan`, Thariq Shihipar. Đã đọc SKILL.md, references/blocks.md, example scheduled-send và pack.mjs; chạy packer gốc và browser để kiểm tra mock composer, màn hình failed/sent. Bản cùng tên của Plannotator không phải plugin này. Chưa xác minh bản HTML BMAD cũ cụ thể; không tuyên bố đã so sánh với bản đó.

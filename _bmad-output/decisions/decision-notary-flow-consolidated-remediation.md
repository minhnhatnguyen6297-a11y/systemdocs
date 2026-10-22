# Một ticket sửa đồng bộ flow Notary

## Quyết định owner · 2026-10-13

Owner yêu cầu tổng hợp một ticket từ sáu report mới, đánh giá tổng quan thiết kế, tối ưu UI/UX, kiểm tra specs/docs rồi sửa đồng bộ. Ticket còn bao gồm hiện trạng regex core dùng chung, tích hợp vào flow thật để chỉnh dần khi test, và khả năng tìm file Word mẫu có placeholder.

## Lý do

Các vấn đề cùng ảnh hưởng flow Input → Stage → Pool → Diagram → Word. Không xử lý như sáu bản vá UI rời nhau hoặc nghiệm thu regex bằng tool độc lập rồi coi như đã tích hợp sản phẩm.

## Phạm vi phiên hiện tại

Lập ticket và phương án có bằng chứng trước implementation. Không coi artifact đề xuất, kích thước mock hoặc phương án chuyển loại hồ sơ chưa được owner chốt là hành vi đã duyệt. Không sửa code ở bước tổng hợp này.

## Nguồn

Yêu cầu owner trong hội thoại; sáu report schema v2 tại `_bmad-output/tmp/visual-bug-reporting/reports/` có id bắt đầu `18ae1083`, `d9da640e`, `e86a02bb`, `802bd69e`, `2c232a28`, `b54184b3`.

---
id: decision-owner-case-snapshot-as-history-20261021
title: "Owner chốt: mỗi Hồ sơ một snapshot, lịch sử là các Hồ sơ"
date: '2026-10-21'
status: accepted
---

## Quyết định

Owner: “mỗi bản ghi chỉ có 1 trạng thái snapshot duy nhất, lịch sử chính là
các bản ghi đó, không lưu thông tin vụn vặt”.

- Record nghiệp vụ là Hồ sơ: ai, tài sản gì, làm gì. Mỗi Hồ sơ giữ một
  snapshot hiện hành, kể cả Hồ sơ Nháp đã lưu database.
- Lưu lại cùng Hồ sơ cập nhật snapshot hiện hành; sửa ô/lưu nhiều lần
  không tự sinh Hồ sơ mới hoặc một chuỗi snapshot của các lần lưu.
- Lịch sử nghiệp vụ của Người/Tài sản được xem qua những Hồ sơ liên quan.
  **Làm rõ sau đó cùng phiên:** Người gom ID bằng tên + số giấy tờ đồng thời,
  Tài sản bằng serial. Lấy vào Hồ sơ mới mặc định bộ mới nhất, không chọn phiên
  bản. Mỗi Hồ sơ đã lưu giữ snapshot riêng, chỉ user sửa thủ công, không tự đổi
  theo dữ liệu mới ở nơi khác. Các bộ thông tin khác nhau vẫn giữ qua các Hồ sơ.
- Không thêm bảng phiên bản Người/Tài sản theo từng lần sửa, lịch sử từng ô
  hoặc bitemporal để đáp ứng yêu cầu lịch sử nghiệp vụ này.

## Lý do và phương án bỏ

Owner xem Hồ sơ là đơn vị công việc và lịch sử, ưu tiên thiết kế tối giản.
Phương án assistant gợi hỏi giữ snapshot mọi lần lưu trong cùng Hồ sơ bị
bác bỏ. Các mô hình bảng phiên bản độc lập/bitemporal từng được nêu để tìm
hiểu không trở thành yêu cầu; không có schema đó đã được duyệt cần migration.

## Ranh giới

- Một snapshot là trạng thái logic của Hồ sơ, có thể được lưu bằng nhiều
  dòng/bảng. Chưa chọn JSON, bảng quan hệ hoặc cấu trúc vật lý cụ thể.
- Bộ đếm revision phục vụ chống ghi đè đồng thời không phải kho snapshot
  lịch sử; giữ các bảo đảm ghi trọn vẹn/quyền ghi hiện hành.
- Giữ raw, nguồn, `source_refs` và lịch sử kỹ thuật đã có theo quy tắc hiện
  hành; quyết định không cấp quyền xóa dữ liệu/lịch sử hoặc tạo logging mới.
- #42 nhiều giấy tờ/địa chỉ và phạm vi schema toàn #41 vẫn còn thiết kế.
  Policy user chọn liên kết ở #44 bị thay; không suy đã duyệt mô hình năm bảng.

## Hiệu lực

Đồng bộ trong shared data-rules, spec Notary và sổ tay cùng phiên.
Yêu cầu chọn snapshot/ID do user trước đó đã được thay bằng
[điểm neo và mặc định mới nhất](decision-owner-entity-anchors-case-snapshots-20261021.md).
Đây là quyết định thiết kế; cập nhật văn bản contract, chưa sửa runtime/schema hoặc chạy
migration/test. Brainstorming tiếp tục; #41 mở/gate mẫu đóng.

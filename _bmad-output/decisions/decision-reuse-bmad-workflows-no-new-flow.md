# Dùng workflow BMAD hiện có, không xây thêm flow

Ngày: 2026-10-12

## Quyết định của user

- Không build thêm flow; hiểu và tái dùng luồng BMAD hiện có trước khi sửa.
- HTML Plan giữ cấu trúc Thariq đã chốt, là lớp trình bày trong workflow BMAD, không thành workflow hay nguồn chuẩn riêng.
- Orchestration vẫn chưa chốt; không gắn quyết định này với OMP/Orca.

## Vì sao

User cần coding loop daily ổn định và biết BMAD đang làm gì, bước tiếp theo là gì. Thêm flow song song gây mơ hồ về chỉ dẫn và tăng việc bảo trì.

## Phạm vi phiên kiểm tra

Kiểm tra remote, vị trí HTML và routing skill. Không tự update/cài skills hoặc đổi override. Điểm trình bày HTML đang tồn tại và thay đổi upstream là bằng chứng hiện trạng, không tự động được coi là quyết định mới đã duyệt.

# Progress — MIN-139

## Trạng thái: chờ owner review — 2026-09-29

## Đã làm
- Ghi `handoff.md` ngắn cho quyết định kiến trúc còn mở; gom lại tám đầu việc
  đã nêu trước khi so sánh các repo/công cụ regex.
- Tạo Linear MIN-139 và liên kết MIN-137, MIN-108, MIN-96, MIN-100, MIN-131.
- Viết product brief về lý do tồn tại, vấn đề, sản phẩm, phạm vi v1 và cách đo.
- Viết addendum về schema kết quả, chiến lược từng nguồn, noise/duplicate,
  Word assistant, ma trận test, quyết định mở và lộ trình.
- Đối chiếu Upload Lab SOT, kiến trúc parser, Document Intake adapters, contract
  Word và công cụ MIN-137 hiện có.

## Đang làm dở
- Chưa sửa SOT kiến trúc, `upload_lab/docs/spec_UI.md`, contract hoặc runtime.

## Bước tiếp theo
- Thử trên corpus nhiều nguồn và Word mẫu, rồi chốt quyền sở hữu engine/schema
  kết quả từ bằng chứng; bàn giao hiện tại đề xuất giữ lõi ở Document Intake.
- Sau khi chốt, tạo hoặc cập nhật contract trong task riêng trước khi implement.

## Check đã chạy
- `git diff --check`: pass sau lần soạn đầu.
- Kiểm tra trực tiếp 7 file Markdown mới/chưa được Git theo dõi: không có lỗi
  khoảng trắng cuối dòng, link nội bộ hoặc phạm vi 12 dẫn chứng source.
- Review cấu trúc và văn phong brief: đã chạy hai lượt độc lập và sửa câu chữ,
  bổ sung quyết định mở, phân biệt đề xuất triển khai với yêu cầu owner.
- Review cấu trúc addendum: đã chạy; bổ sung trạng thái đề xuất, giải thích từ,
  ranh giới schema, giữ mọi lần xuất hiện và liên kết tới file Word gốc.
- Review văn phong addendum: đã chạy; làm rõ quan hệ `duplicate_of` và các
  bước triển khai. Định nghĩa sản phẩm đã hoàn tất ở mức đề xuất; thuật toán
  nhóm dữ liệu và quyền sở hữu engine vẫn là câu hỏi mở.

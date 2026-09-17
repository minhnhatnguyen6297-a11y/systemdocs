# Luồng hồ sơ — đường dẫn chuyển tiếp

Trạng thái: **redirect-only từ 17/09/2026**, không còn định nghĩa hành vi riêng.
Bộ [SPEC module](../../SPEC.md) chỉ định file cần sửa cho từng chủ đề.

## 1. Core principles

Sửa nguyên tắc dữ liệu/hành vi tại [Stage / Pool / Diagram](../../platform/case-workspace/contract.md).
Không thêm quy tắc ở file chuyển tiếp này.

## 2. Data zones

Hồ sơ, Người, Tài sản ở [SPEC tổng](../../SPEC.md).
Nháp/đã duyệt và quan hệ Diagram ở [chương Stage](../../platform/case-workspace/contract.md#1-ba-lớp-dữ-liệu).

## 3. Person CCCD OCR modal

[Cửa sổ OCR và input](../../platform/document-intake/spec.md):
OCR chỉ xem, sửa tại Stage; không dùng hành vi sửa/xác nhận modal cũ.

## 4. Stage

[Cập nhật toàn cục](../../platform/case-workspace/contract.md#3-cập-nhật-là-một-hành-động-toàn-cục).

## 5. Pool

[Pool và dữ liệu riêng của Diagram](../../platform/case-workspace/contract.md#6-pool-và-dữ-liệu-riêng-của-diagram).

## 6. Diagram

[Ảnh hưởng Stage → Diagram](../../platform/case-workspace/contract.md#5-ảnh-hưởng-stage--diagram-đã-được-bàn-trước).
[UX Diagram](ux.md) và [thuật toán thừa kế](spec.md) còn nháp; không được duyệt
ngầm qua quy tắc đồng bộ Stage.

### Asset decision rule

Ý nghĩa các nhóm người trong văn bản tại [Word §2](word-export.md#2-nguồn-dữ-liệu-và-thẩm-quyền).
Không nhân bản quy tắc này tại workflow.

## 7. Delete / clear permissions

[Xóa/bỏ gán, xác nhận cả nhánh](../../platform/case-workspace/contract.md#52-xóa-người-và-ảnh-hưởng-hết-nhánh).
[Dọn cache](../../platform/case-workspace/contract.md#3-cập-nhật-là-một-hành-động-toàn-cục).

## 8. Agent checklist

Tìm đúng chủ đề trong [bảng file cần sửa](../../SPEC.md#1-sửa-yêu-cầu-ở-đúng-một-nơi),
sửa chương sở hữu và kiểm tra consumer. Word: [word-export.md](word-export.md).
Nhánh cũ trong Memory Bank/kế hoạch không phải quyền phục hồi hành vi đã thay thế.

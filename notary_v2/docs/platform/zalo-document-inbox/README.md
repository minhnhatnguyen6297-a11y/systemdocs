# Zalo Intake — bắt đầu tại đây

Code hiện tại vẫn theo luồng v1. Thiết kế v2 chưa được triển khai. MIN-103 chuyển engine Zalo sang module thứ tư: repo riêng `D:\zalo-intake` (source-of-truth, đã có) và `zalo/` trong monorepo (snapshot một chiều, controller export). Tài liệu **producer** đã chuyển sang `docs/` của repo module — `spec-producer.md`, `connector-protocol.md`, `baseline-open-issues.md`, `rollback-runbook.md` (snapshot tương ứng ở `zalo/docs/`); spec trong thư mục này giữ phần consumer và trỏ sang repo module. Trang này không có nghĩa code đã chuyển.

## Đường đọc chi tiết cho agent

| Câu hỏi | Đọc ở đâu | Giá trị |
|---|---|---|
| Task nào, phạm vi, trạng thái và điều kiện hoàn thành? | Issue [MIN-91](https://linear.app/minhnotary/issue/MIN-91) và issue con được giao | **Nguồn chuẩn cho công việc**; `.agent/tasks/<ID>/` chỉ ghi tiến độ/bàn giao |
| Sản phẩm phải làm gì, lỗi và bài thử nào? | [spec Zalo cấp sản phẩm](../../../../docs/spec/notary_v2/input/zalo.md), rồi [CAP/T chi tiết](spec.md) | Cây `docs/spec` sở hữu hành vi; CAP/T là phụ lục nghiệm thu |
| Parser của Soạn hồ sơ sở hữu gì? | [Document Intake spec](../document-intake/spec.md) cho luồng OCR upload hiện có; [MIN-102](https://linear.app/minhnotary/issue/MIN-102) cho schema kết quả mới | Hành vi Zalo cần đạt vẫn theo `spec.md`; schema kết quả mới chưa được duyệt |
| Hai repo trao đổi file/API thế nào? | Contract Zalo trong [contracts/](../../../../contracts/README.md) **sau khi MIN-92 duyệt và publish** | Nguồn chuẩn cho giao tiếp; hiện chưa có contract Zalo đã duyệt |

## Tài liệu hỗ trợ, đọc khi cần

- [Spec Zalo cấp sản phẩm](../../../../docs/spec/notary_v2/input/zalo.md): lý do
  và ranh giới đã chọn; chi tiết hành vi theo `spec.md`.
- Linear MIN-91: thứ tự, trạng thái và lịch sử triển khai. Git giữ lại bản kế
  hoạch cũ khi cần đối chiếu.
- [Kiểm kê source v1](v2-current-state-audit.md): bằng chứng về code đang có, không là hành vi v2.
- [Spec v1 lịch sử](spec-v1-legacy.md) và [điểm còn mở v1](open-issues-v1-legacy.md): chỉ để đối chiếu quá khứ.

## Đường đọc theo task

Mọi task đọc `AGENTS.md`, issue Linear được giao, [spec Zalo cấp sản phẩm](../../../../docs/spec/notary_v2/input/zalo.md),
các CAP/T liên quan trong [spec hành vi](spec.md), rồi contract Draft MIN-92.
Contract chỉ có hiệu lực sau khi được duyệt và publish; bản nháp không thay
thế contract.

| Task | Đọc thêm theo phạm vi |
|---|---|
| MIN-92 | [Contract Zalo Draft](../../../../contracts/zalo-intake/zalo-intake.md), [quy tắc contract](../../../../contracts/README.md), [chuẩn định danh](../../../../contracts/entities.md). |
| MIN-102 | Contract Zalo Draft MIN-92, [Document Intake spec](../document-intake/spec.md), [quy tắc tài sản](../document-intake/property-rules.md) phần nhiều thửa và model hiện tại. Không code tích hợp trước khi publish. |
| MIN-93 | Contract Zalo Draft MIN-92 và [kiểm kê source v1](v2-current-state-audit.md). |
| MIN-103 | Contract Zalo Draft MIN-92, [kiểm kê source v1](v2-current-state-audit.md) và source engine Zalo hiện tại. **Tài liệu producer đã chuyển** sang `docs/` của repo module `D:\zalo-intake` (snapshot `zalo/docs/`); tài liệu consumer giữ ở thư mục này. |
| MIN-94/95/97 | Contract Zalo Draft MIN-92 và tài liệu module trong `zalo/docs/`; dùng kiểm kê source v1 để đối chiếu code cũ. |
| MIN-96 | Contract Zalo Draft MIN-92, bridge kết quả nội bộ của MIN-102, Document Intake spec và quy tắc tài sản. |
| MIN-98 | Contract Zalo Draft MIN-92. |
| MIN-99/100 | Contract Zalo Draft MIN-92, bridge kết quả nội bộ của MIN-102 và Document Intake spec. |
| MIN-101 | Các contract sau khi được owner duyệt/publish và kiểm kê source v1. |

Các quyết định còn mở theo [MIN-92](https://linear.app/minhnotary/issue/MIN-92) (giao tiếp), [MIN-102](https://linear.app/minhnotary/issue/MIN-102) (kết quả nội bộ) và [MIN-90](https://linear.app/minhnotary/issue/MIN-90) (tin bot chưa từng bắt). Khi hai tài liệu mâu thuẫn, agent dừng phần liên quan và sửa mâu thuẫn tại đúng nguồn chuẩn trước khi code; không tự chọn đoạn viết mới hơn làm quy tắc.

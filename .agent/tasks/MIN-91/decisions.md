# Decisions — MIN-91

## 2026-09-24 — Chốt phạm vi plan theo owner

- **Chọn:** toàn bộ OCR/regex/ghép người-tài sản/nhóm tạm thuộc module Zalo độc lập; thử repo local trước, chuyển Windows server sau.
- **Chọn:** kết quả bàn giao có processed JSON cùng raw/provenance, tuyệt đối không ảnh. Máy công chứng tự Sync và chỉ nhận/duyệt/đưa vào đầu vào soạn hồ sơ.
- **Chọn:** MIN-98 phải đo dữ liệu thật sau khi module đã chạy trọn luồng, rồi MIN-99/100 mới tích hợp UI theo thứ tự owner yêu cầu.
- **Nguồn:** yêu cầu owner trong task và spec MIN-89 revision 3.

## 2026-09-24 — Bảo vệ dữ liệu nghiệp vụ trong plan

- **Chọn:** dùng DraftInput riêng trước nút Cập nhật vì `case_state_json.stage` được Word đọc trực tiếp. GCN nhiều thửa phải có mapping được duyệt hoặc giữ đủ ở DraftInput; `Property.land_rows_json` không phải danh sách thửa.
- **Nguồn:** review source `notary_v2/services/word_engine.py:404`, `routers/cases.py:801`, `models.py:57`; contract cụ thể cần MIN-92 chốt.

## 2026-09-24 — Chống ghi đè khi người dùng đang xem trước

- **Chọn:** plan yêu cầu MIN-92 định nghĩa dấu kiểm hash của hồ sơ/Customer/Property được preview sử dụng. `InheritanceCase` chưa có cột version; khi bấm Cập nhật phải khóa ghi, kiểm lại snapshot và transaction trước khi thay dữ liệu. Một chỉnh sửa qua router cũ làm preview hết hiệu lực.
- **Chọn:** tạo `InheritanceCase` cần `nguoi_chet_id`, `tai_san_id`, `ngay_lap_ho_so`; `Customer.ngay_chet` được phép trống. Không tự tạo hồ sơ chỉ từ nhóm tạm.
- **Nguồn:** review source `notary_v2/models.py:16`, `:88`, `:90` và `routers/cases.py:801`.

## 2026-09-24 — Owner đổi ranh giới OCR và engine hiểu tài liệu

- **Chọn:** Zalo nhận/giữ ảnh và gọi Qwen OCR; Soạn hồ sơ/Document Intake sở hữu và chạy parser, regex, ghép mặt/người/tài sản và nhóm hồ sơ sau khi Sync raw. Bản quyết định đầu file giao toàn bộ xử lý cho module Zalo đã được thay.
- **Hệ quả:** MIN-92 contract phải bắt buộc gói raw/status/provenance không ảnh; kết quả xử lý/revision do notary tạo cục bộ. MIN-95 chỉ OCR tại Zalo, MIN-96 là parser ở notary, MIN-97 giao raw, MIN-98 dùng harness headless đánh giá cả hai từ dữ liệu thật, rồi MIN-99/100 tích hợp Sync/UI.
- **Nguồn:** lựa chọn trực tiếp của owner trong task hiện tại và audit source hiện hành.

## 2026-09-24 — Gói file, OCR theo yêu cầu và tách contract nội bộ

- **Chọn:** tiếp tục gói file/folder bất biến, không đổi sang outbox/cursor vì owner muốn giữ file để kiểm lỗi. API gói file vẫn cần MIN-92 duyệt.
- **Chọn:** Document Intake quyết định lúc nào thiếu chứng cứ và gửi yêu cầu OCR biến thể có giới hạn theo ID cho module; bot chỉ chạy Qwen ở nơi giữ ảnh rồi phát raw revision mới. MIN-95/97/96/99/98 chia phần tương ứng và đo chi phí/chất lượng trên dữ liệu thật.
- **Chọn:** MIN-92 chỉ chốt contract liên repo, gồm lệnh OCR lại, retention raw sau ACK, lịch sử listener và event nguồn. MIN-102 chốt result/DraftInput/fingerprint/mapping nhiều thửa nội bộ; bot không bị chặn bởi các quyết định nội bộ này.
- **Giữ:** thứ tự phát triển repo local trước, thử dữ liệu thật trên module độc lập rồi mới tích hợp UI. Không dùng đường Zalo legacy trên máy chính để thử vì nó lưu ảnh trong notary và TTL cũ không tính theo `captured_at`.

## 2026-09-24 — Bổ sung module Zalo thứ tư và quyền sở hữu tài liệu

- **Chọn theo yêu cầu owner:** MIN-93 chỉ dựng khung repo local; MIN-103 chuyển toàn bộ engine do Zalo sở hữu và SOT producer vào repo riêng cùng snapshot `zalo/` trong monorepo. Chốt một repo nguồn chính, commit/manifest và cách cập nhật một chiều khi thực thi; chưa coi các đích đã tồn tại, không nested Git/submodule tự phát.
- **Giữ ranh giới:** Document Intake/parser, OCR upload thủ công và consumer Sync/review ở notary. Contract liên repo ở `contracts/`; spec producer chuyển sang `zalo/docs` cùng code trong MIN-103. Chỉ MIN-101 mới cutover/gỡ legacy; không chạy hai listener một account.
- **Retention:** MIN-92 chốt raw bot sau ACK; MIN-102 chốt folder imported/raw máy chính theo nhu cầu mở file tra lỗi; MIN-99 hiện thực. Đây là bổ sung thay cho câu phân công cả hai nơi cho MIN-92 trong bản plan cũ.
- **Chưa chốt:** các góp ý Claude về transcript, quota, auto/manual và gộp variant; contract phải đánh giá riêng, không tự đổi hành vi. Thí nghiệm `enable_rotate=true` lượt đầu nằm ở MIN-98, không đổi production mặc định.

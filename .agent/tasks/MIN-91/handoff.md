# Handoff — MIN-91

## Trạng thái khi bàn giao — 2026-09-24

Bộ plan và task đã bổ sung module thứ tư theo quyết định owner: bot OCR, Soạn hồ sơ xử lý chữ. Owner chọn giữ gói file raw và cho OCR bổ sung có giới hạn. Goal triển khai trên Linear tiếp tục Todo. Có 12 issue con MIN-92..103; MIN-103 mới phụ trách migration engine Zalo, còn MIN-93 là scaffold. Không tạo repo/code/runtime trong lượt này.

## File chính

- `docs/product/plans/2026-09-24-zalo-independent-implementation-plan.md` — điểm vào cho agents.
- `docs/product/specs/2026-09-24-zalo-independent-intake.md` và `zalo-file-exchange-v1-draft.md` — ranh giới bot OCR/Document Intake parse, gói raw và OCR bổ sung DRAFT.
- `notary_v2/docs/platform/zalo-document-inbox/spec.md` — hành vi sản phẩm.

## Việc còn lại / rủi ro

- MIN-92 phải có hợp đồng/schema liên repo được duyệt, gồm quota OCR và retention raw bot sau ACK. Sau đó MIN-93 tạo scaffold repo bot, MIN-103 chuyển baseline và SOT producer vào repo riêng + snapshot `zalo/`. MIN-102 chốt kết quả/retention gói máy chính trước MIN-96/99; chưa chạy Zalo/Qwen hoặc thử dữ liệu thật.
- Dependency Linear đã đọc lại: 92→93→103→94/95/97; 92→102→96; 94/95/96/97→98→99→100→101. Chỉ MIN-101 cutover/gỡ legacy. Repo `D:/zalo-intake` và folder `D:/systemdocs/zalo/` là target chưa tồn tại; không nested Git/submodule tự phát, không DB/media/session chung.
- Khi thực thi, từng agent tạo/cập nhật `.agent/tasks/<ID>/` của mình, báo test và các giới hạn. Goal chỉ Done sau MIN-101 đạt.

## Kiểm chứng

- Các kiểm tra 28 Markdown/132 link/6 JSON/CAP-01..16/T01..24 ở revision trước. Kiểm mới riêng file plan: 26 link Markdown, 0 đường nội bộ thiếu, 0 dòng thừa khoảng trắng, đúng một heading MIN-103 và không còn yêu cầu skill cứng. Graph 12 issue con đã đọc lại trực tiếp từ Linear, parent/blockers khớp plan. Reviewer tổng hợp kiểm toàn bộ docs sau khi các worker xong.
- Chỉ có tài liệu/task thay đổi; không chạy runtime test hoặc live Zalo/Qwen.

## File tạm

Không có file tạm hoặc dữ liệu khách hàng tạo trong lượt plan.

## Bổ sung handoff 24/09 — geometry OCR

Code Qwen hiện tại chỉ trả chữ; tài liệu Alibaba xác nhận `advanced_recognition` có `words_info` text/location/rotate_rect. Plan và Linear MIN-89/91/92/95/96/98/99/102 đã được cập nhật để giữ geometry có kiểu ở producer, dùng bố cục tại Document Intake notary, đánh giá trước khi bật mặc định. Cần contract MIN-92 duyệt khung ảnh/pass/trang, 8 tọa độ, transform và trạng thái chưa xác minh; MIN-98 đo mapping với ảnh trên máy module, không gửi ảnh sang máy chính. Text-only fallback vẫn phải chạy. Chưa có code/test live; 12 issue con và blockers không đổi.

Kiểm cuối đã sửa thêm hai điểm: không coi tọa độ provider chắc chắn nằm trong khung ảnh gửi trước phép thử overlay; khóa quota OCR lại cho attachment nhiều trang vẫn để MIN-92 chọn. Linear MIN-92/MIN-95 và plan/draft đã đồng bộ. `contracts/README.md` không còn tự mâu thuẫn về số contract. Kết quả kiểm cuối: 31 Markdown, 162 link local, 8 JSON, 42 code block, CAP-01..16, T01..24 và 12 task đều hợp lệ; `git diff --check` sạch ngoài cảnh báo LF/CRLF. Không chạy Zalo/Qwen live và chưa đổi runtime.

# Progress — MIN-89

## Trạng thái: tài liệu revision 4 đã đồng bộ; Linear MIN-89 In Review — 2026-09-24

## Đã làm

- Giữ spec v1 cũ tại `spec-v1-legacy.md`; spec chính mới ở `spec.md`. Bỏ file trỏ `spec-v2.md` và file điểm mở v2 trùng Linear để agent có một lối vào.
- Cập nhật thiết kế tổng thể, draft giao tiếp gói raw OCR, spec Zalo chính, README/open-issues/audit và các tài liệu kiến trúc liên quan theo quyền sở hữu module mới.
- Kiểm kê source hiện tại: listener vẫn gắn vòng đời notary; OCR manual dùng cùng router; Stage đang được Word đọc. Ghi khác biệt hiện trạng/đích vào spec và plan.
- Lập GOAL MIN-91 và 11 task: MIN-92, MIN-102, MIN-93..101; plan giao việc nằm trong `docs/product/plans/2026-09-24-zalo-independent-implementation-plan.md`.
- Review chéo đã phát hiện và sửa hai lỗi mapping: không dùng `case_state_json.stage` làm DraftInput chưa xác nhận; `Property.land_rows_json` không chứa các thửa đất.
- Chốt theo owner: giữ gói file raw để soát lỗi; OCR bổ sung có giới hạn từ ảnh bot còn giữ, qua yêu cầu có ID/chủng loại định sẵn. Bot giữ ảnh tối đa 168 giờ từ lúc bắt tin; Document Intake của Soạn hồ sơ bóc tách/ghép/nhóm sau Sync.
- Bổ sung cảnh báo khoảng listener mất kết nối, sự kiện nguồn nếu adapter cung cấp, xử lý status OCR và giới hạn giữ raw trên bot sau ACK trước khi thử dữ liệu thật. MIN-92 chốt contract liên repo; MIN-102 chốt schema kết quả nội bộ.
- Dọn nguồn đọc cho agents: `zalo-document-inbox/README.md` chỉ rõ SOT theo từng câu hỏi; root và notary README trỏ về đó; bỏ `spec-v2.md` chỉ chứa link và `open-issues.md` trùng Linear. Giữ hai bản v1 lịch sử và kiểm kê source để đối chiếu, tách khỏi luồng đọc triển khai.

## Còn lại

- Chưa publish contract APPROVED, tạo repo bot, chạy tài khoản/Qwen thật hay sửa runtime. MIN-92 phải chốt ngân sách OCR bổ sung và hạn giữ raw sau ACK trước dữ liệu thật.
- Fallback cho sự kiện bot không bắt được vẫn là vấn đề MIN-90; không có bằng chứng hệ thống đã bắt đủ tin.

## Bổ sung 24/09 — ranh giới module thứ tư

- Số 11 task ở bản revision 4 phía trên là lịch sử. Hiện MIN-91 có 12 issue con sau khi tạo đúng một task mới MIN-103. MIN-93 chỉ scaffold; MIN-103 chuyển engine Zalo và tài liệu producer vào repo riêng + snapshot `zalo/` trong monorepo. Chưa tạo repo/folder hoặc chạy runtime.
- Parser Document Intake, OCR upload thủ công và dữ liệu nghiệp vụ vẫn thuộc Soạn hồ sơ. MIN-101 mới cutover/gỡ đường Zalo legacy. Spec producer hiện ở notary là nguồn tạm cho tới khi MIN-103 chuyển sang `zalo/docs`; contract liên repo ở `contracts/`.
- MIN-92 chốt retention raw trên bot sau ACK; MIN-102 chốt retention folder imported/raw trên máy chính để vẫn mở gói tra lỗi, MIN-99 thực hiện. Các đề xuất Claude khác cần contract quyết định, chưa tự áp.

## Bổ sung 24/09 — geometry OCR

- Alibaba Qwen-OCR chính thức có `advanced_recognition` trả `words_info` với chữ và vị trí dòng. Code hiện tại chỉ gọi `text_recognition` và rút `list[str]`, nên chưa có geometry trong runtime. MIN-89/91 cùng task MIN-92/95/96/98/99/102 đã bổ sung mục tiêu raw chữ + vị trí có kiểu, parser bố cục ở Soạn hồ sơ, đánh giá chất lượng/khung tọa độ trước bật mặc định. Không sửa code hoặc gọi Qwen thật; số task vẫn 12.

## Check đã chạy

- Đọc AGENTS/contract/source; sau khi dọn SOT, kiểm 28 Markdown đang đổi, 132 liên kết nội bộ, 6 JSON ví dụ: 0 lỗi. `git diff --check` exit 0; chỉ có cảnh báo LF/CRLF của Windows.
- CAP-01..16 và T01..24 có đủ, đúng thứ tự, không trùng. Agent draft đã kiểm 7 source refs trong ví dụ giao tiếp.

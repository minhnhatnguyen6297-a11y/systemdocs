# Handoff — MIN-89

## Trạng thái khi bàn giao — 2026-09-24

Spec revision 4 đã đồng bộ theo quyết định owner: bot giữ ảnh tạm và gọi Qwen OCR; Document Intake của Soạn hồ sơ phân loại, bóc trường, ghép và nhóm từ raw sau Sync. Gói file raw được giữ trên máy chính để soát lỗi. Tài liệu và plan MIN-91 ở working tree; Linear MIN-89 In Review. Chưa có runtime, repo `D:/zalo-intake` hay server thật.

## File chính

- `docs/product/specs/2026-09-24-zalo-independent-intake.md`: luồng và ranh giới hai repo.
- `docs/product/specs/zalo-file-exchange-v1-draft.md`: chỉ raw OCR/status/provenance từ bot, API gói file/ACK/OCR bổ sung DRAFT; kết quả bóc/ghép do Document Intake tạo nội bộ.
- `notary_v2/docs/platform/zalo-document-inbox/spec.md`: yêu cầu hiện hành; bản v1 ở `spec-v1-legacy.md`.
- `docs/product/plans/2026-09-24-zalo-independent-implementation-plan.md`: bản revision 4 lúc đó có 11 task; hiện đã bổ sung MIN-103 thành 12 task con, gồm scaffold MIN-93 và migration module thứ tư MIN-103.
- `notary_v2/docs/platform/zalo-document-inbox/README.md`: điểm vào duy nhất cho agents, ghi nguồn chuẩn theo từng loại nội dung. Bản nháp contract và plan là tài liệu hỗ trợ; các quyết định mở theo Linear.

## Việc còn lại và rủi ro

- Contract kỹ thuật phải được duyệt trong MIN-92 trước runtime: gói raw, ACK, OCR bổ sung, ngân sách Qwen và thời hạn giữ raw sau ACK. MIN-102 chốt mapping nhiều thửa và DraftInput nội bộ trước parser.
- Dữ liệu thật, độ chính xác ghép, sự sống của bot và lỗi bắt trượt chưa được kiểm chứng. MIN-98 đo pipeline; MIN-90 nghiên cứu fallback riêng.
- Ảnh thật không vào notary; người dùng đối chiếu trên Zalo thật. OCR manual trong notary phải giữ khi tách module. Cảnh báo khoảng listener mất kết nối không chứng minh đã bắt đủ sự kiện.

## Kiểm chứng

- Sau khi dọn SOT, kiểm 28 Markdown đang đổi, 132 link nội bộ, 6 JSON ví dụ, CAP-01..16/T01..24: 0 lỗi. `git diff --check` exit 0; chỉ có cảnh báo LF/CRLF của Windows.
- Không chạy test runtime vì chỉ sửa tài liệu. Không có bằng chứng bot chạy liên tục hoặc thuật toán ghép đạt độ chính xác; phải đo ở MIN-98.

## File tạm

Không tạo scratch/log dữ liệu khách hàng hoặc ảnh.

## Cập nhật handoff 24/09 — module thứ tư

MIN-103 là task duy nhất mới cho việc chuyển connector/session/listener/media/Qwen primitives/tests và tài liệu producer sang repo Zalo riêng + snapshot `zalo/`; chưa thực thi migration. MIN-93 chỉ tạo scaffold. Parser, OCR upload thủ công và consumer Sync/review giữ ở notary; chỉ MIN-101 cutover/gỡ đường cũ. MIN-92 chốt retention raw bot sau ACK, MIN-102 chốt retention gói imported/raw máy chính, MIN-99 thực hiện. Trạng thái và graph mới xác nhận ở Linear; các số lượng link/file và check revision 4 phía trên là bằng chứng lịch sử, không phải kết quả check sau thay đổi này.

Sau audit Qwen OCR, bổ sung mục tiêu giữ chữ và geometry dòng có kiểu từ `advanced_recognition` trong raw khi provider trả, kèm frame/pass/page/transform và trạng thái xác minh. Code hiện tại vẫn chỉ text; MIN-92 duyệt schema, MIN-95 xây adapter, MIN-96 dùng bố cục tại notary, MIN-98 đánh giá trước quyết định bật mặc định. Không ảnh Zalo ở máy chính, không chuyển ngữ nghĩa CCCD/GCN sang bot; text-only fallback giữ nguyên.

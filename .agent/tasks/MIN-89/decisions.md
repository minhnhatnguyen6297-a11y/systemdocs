# Decisions — MIN-89

## 2026-09-24 — Yêu cầu ban đầu, trước lần chỉnh revision 2

- **Chọn:** viết lại đặc tả đầy đủ; collector nghiên cứu độc lập trên Windows server; dữ liệu nghiệp vụ ở một máy chính dùng chung; có thẻ, nhóm tạm, human review và lấy bù.
- **Nguồn:** yêu cầu và câu trả lời của owner trong task hiện tại.
- Vị trí OCR, đường truyền, retention, tham số grouping và nghiệm thu vẫn là đề xuất cần chốt trong spec; không ghi thành quyết định đã duyệt.

## 2026-09-24 — Owner chỉnh revision 2, thay nội dung tương ứng phía trên

- Server gọi API Qwen OCR, không phát triển engine OCR riêng; máy chính chỉ nhận raw text/data và metadata, không tải/lưu ảnh Zalo kể cả cache/preview.
- Ảnh server tự xóa sau 7 ngày. Quy ước spec tính từ captured_at; raw chưa ACK giữ riêng, không xóa theo hạn ảnh.
- captured_at lúc bot bắt tin là ngày/giờ chính mỗi dòng và dùng phân loại; ngày import chỉ phụ.
- Có nút Sync ngoài cơ chế tự nhận. Root đề xuất HTTPS pull để lưu raw vào folder; API cụ thể vẫn draft.
- Regex/phân loại/ghép chạy server hay hệ thống chưa chốt, không tự chốt main.
- Fallback bot bắt thiếu tạm hoãn, theo MIN-90 Backlog; phase đầu giả định thu đủ để chuẩn flow, không coi đó là bằng chứng thực tế.
- Nguồn: các gạch đầu dòng owner gửi khi review file tổng thể trong task hiện tại.

## 2026-09-24 — Owner chốt revision 3, thay quyết định raw-only/parser-open ở trên

- **Chọn:** module Zalo độc lập sở hữu cả Qwen OCR, regex, bóc tách, ghép người/tài sản và nhóm hồ sơ tạm. Bàn giao processed JSON + raw text/provenance, không ảnh cho máy công chứng. Máy chính cho người dùng duyệt rồi đưa vào input soạn hồ sơ.
- **Chọn:** tạo repo local riêng và thử trọn luồng trước; Windows server là bước sau. Giao tiếp hai repo giữ nguyên ý nghĩa khi chuyển máy.
- **Chọn:** contract/API chi tiết giữ DRAFT tới task MIN-92, không tự triển khai trong MIN-89. Fallback bắt trượt giữ ở MIN-90.
- **Nguồn:** chỉ đạo owner “việc regex, bóc tách, gộp nhóm data sẽ được làm tại máy chủ” và danh sách bốn bước giao agents.

## 2026-09-24 — Owner chốt revision 4, thay ranh giới parser ở revision 3

- **Chọn:** module Zalo chỉ giữ ảnh tạm, xử lý ảnh cần bytes và gọi Qwen OCR. Gói sang máy công chứng chứa chữ OCR theo ảnh/trang/dòng, trạng thái và provenance; không chứa ảnh hoặc kết quả người/tài sản/nhóm do bot tạo.
- **Chọn:** Document Intake của Soạn hồ sơ chạy regex, phân loại, bóc trường, ghép mặt giấy/người/tài sản và nhóm hồ sơ từ raw sau Sync. Mọi nguồn tài liệu dùng một bộ quy tắc nghiệp vụ; MarkItDown hiện vẫn là POC adapter.
- **Giữ:** repo Zalo local riêng trước, 168 giờ ảnh, captured_at, pending/ACK, auto/manual Sync và fallback MIN-90 mở.
- **Nguồn:** owner trả lời chọn “Ở Soạn hồ sơ” cho nơi xử lý raw sau Qwen OCR; source audit `routers/ocr_ai.py` và quyết định POC MIN-61.

## 2026-09-24 — Owner chọn file và vòng OCR bổ sung trong revision 4

- **Chọn:** giữ gói file raw trong folder máy chính để kiểm tra sai sót. `manifest.json`, `records.jsonl`, `READY.json` và biên nhận là hình thức giao tiếp dự kiến; schema/API chi tiết thuộc MIN-92.
- **Chọn:** Soạn hồ sơ được yêu cầu bot OCR thêm biến thể có giới hạn cho ảnh bot đã bắt và còn trong 168 giờ. Không chuyển ảnh; bot công bố raw revision mới, máy chính parse lại mà không tự ghi đè dữ liệu đã duyệt.
- **Ghi nhận review:** nhánh OCR GCN hiện dựa vào kết quả parser để quyết định xoay/cắt chân ảnh; cần giao thức yêu cầu lại hoặc đo chênh lệch chất lượng. Lịch sử listener/heartbeat cảnh báo vùng có thể không nghe được; không chứng minh mọi tin khác đã thu đủ. Raw cá nhân trên bot sau ACK phải có hạn dọn hữu hạn trước thử dữ liệu thật.
- **Nguồn:** câu trả lời trực tiếp của owner cho hai câu hỏi về file và OCR lại, plus review kiến trúc đính kèm; source `notary_v2/routers/ocr_ai.py:2505` và `zalo_connector/src/core.mjs:339` được đối chiếu.

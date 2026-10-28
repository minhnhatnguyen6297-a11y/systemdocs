# Handoff: phiên brainstorm G1 measurement design → Codex

File này là điểm vào cho session Codex tiếp tục phiên brainstorm đang dở. Đọc xong thì tiếp tục hội thoại với user, KHÔNG cần tóm tắt lại.

## Nguồn context chuẩn — đọc theo thứ tự

1. `docs/brainstorming/brainstorm-g1-measurement-design-2026-09-26/.memlog.md` — state phiên đang dở: toàn bộ quyết định, ý tưởng, câu hỏi.
2. `docs/brainstorming/brainstorm-notaryoffice-mvp-path-2026-09-25/brainstorm-intent.md` — kết quả phiên 1: reframe sản phẩm, cây G0–G6+, MoSCoW, luật split-bias.
3. `notaryoffice/intent.md` + `contracts/entities.md` — spec nguồn (là phác thảo, được phép thách thức).
4. `upload_lab/docs/regex-rules.md` + `upload_lab/extract_contract.py` — implementation thật duy nhất đang có (extractor hoàn chỉnh-file, chưa đủ mạnh cho thương mại).

## Bối cảnh ngắn

Module `notaryoffice`: hệ thống "bộ nhớ dấu vết" cho văn phòng công chứng — từ dấu vết trên máy tính/Zalo suy ra record **"Khách nào / Tài sản nào / Làm gì"** cho người quản lý. Phiên này đang thiết kế **bài đo G1**: chứng minh pipeline trích xuất + gom nhóm trên kho hồ sơ Word cũ, trước khi viết Sentinel hay cài gì lên máy.

## Quyết định đã chốt trong phiên này (đừng mở lại trừ khi user yêu cầu)

- Phân loại theo thứ bậc anchor: **tiêu đề > câu mở đầu > thân văn bản**; thân không quyết định loại, chỉ dùng để gom nhóm.
- Engine: **chia vùng ngữ nghĩa trước, bóc thực thể sau** (4 vùng: banner → loại văn bản → người tham gia → tài sản).
- Timeline trục = **số serial GCN**; cấp sổ mới = timeline mới; thửa/diện tích/địa chỉ = trường phụ chấm điểm.
- Chỉ đọc **file đã đóng**, bỏ file đang mở; autosave để đo thực tế ở G3.
- Kế toán lọc định kỳ hồ sơ đã xong = tín hiệu đóng timeline (không cần cơ chế riêng).
- Metric: **gộp nhầm phải ≈ 0** (độc hơn tách thừa); engine split-biased.
- Phần Must chạy được với quyền user thường (tray app); admin chỉ cần lúc cài (print log, service).
- Sự kiện file bị sót → có fallback reconciliation (path+size+mtime); USN journal là tối ưu, không bắt buộc.
- Engine thương mại độc lập với upload_lab: code chung, khác biệt văn phòng = dữ liệu cấu hình.

## Điểm đang dở

Kỹ thuật Morphological Analysis vừa trình bày ma trận 6 yếu tố khó của mẫu đo (loại VB / định dạng+font / cách xếp folder / số serial / thời kỳ địa danh 2025 / cách soạn). **Câu hỏi đang treo chờ user**: "Theo kinh nghiệm của anh, còn yếu tố nào khiến văn bản ở văn phòng anh khó đọc mà bảng này chưa có?" — hỏi lại câu này hoặc tiếp từ nơi user trả lời.

Sau đó còn các việc chưa chốt trong thiết kế bài đo: kích thước/cách lấy mẫu, gán nhãn ground-truth mức hạng mục, định nghĩa "đủ đúng" từng lớp, format output để user kiểm tay nhanh, ngưỡng pass cho tách thừa, xử lý văn bản không-serial và nhiều-serial.

## Luật chơi (user đặt, giữ nguyên)

- Chỉ brainstorm tương tác trong chat: **không code, không implementation plan, không commit, không sửa tài liệu nguồn**.
- Mỗi lượt chỉ hỏi **MỘT** câu quan trọng; user là nguồn ý tưởng chính, agent đưa ý + phê phán.
- Phân biệt rõ cái đang tồn tại vs cái chỉ là dự định; không tự chốt thứ repo đánh dấu cần kiểm chứng thực tế.
- Ghi state vào memlog mỗi quyết định/ý tưởng:
  `uv run _bmad/scripts/memlog.py append --workspace "docs/brainstorming/brainstorm-g1-measurement-design-2026-09-26" --type decision|idea|question|constraint --by user|coach --text "..."`

## Việc đầu tiên

Đọc memlog + intent doc → nạp context → chào user một câu ngắn và hỏi lại câu đang treo ở mục "Điểm đang dở".

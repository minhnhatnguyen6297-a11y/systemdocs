---
id: 12
type: spike
title: "Đối chiếu nguồn mâu thuẫn, nhóm dữ liệu và các quy tắc OCR còn mở"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Đối chiếu nguồn mâu thuẫn, nhóm dữ liệu và các quy tắc OCR còn mở

## Description

Đối chiếu xung đột trích xuất và ranh nhóm bằng nguồn cụ thể với owner. Bao gồm chuẩn hóa/classifier/gộp ảnh OCR so với contract đầu ra. Bằng chứng chuyển một phần/bãi bỏ hành chính cùng ngày được theo dõi độc lập ở C26/#27.

## Approach

Đọc nguồn hiện hành và bằng chứng sẵn có trước. Chỉ so phương án trong ranh issue; không đoán phần nguồn thiếu. Người có vai trò ghi trong Notes cung cấp bằng chứng không thể lấy từ repo hoặc nhận đáp án cần lựa chọn. Không triển khai sản phẩm trong spike.

## Acceptance Criteria

1. **Trả lời đúng câu hỏi hoặc xác định bằng chứng thiếu**
   Verify: Notes ghi đối chiếu có ngày theo từng câu hỏi, nguồn/phương án/hệ quả và phần thông tin còn thật sự không lấy được.
2. **Đáp án dùng được cho đúng bên chờ**
   Verify: Notes chỉ rõ ai chờ, cần quyết định/capability gì, nơi ghi đáp án canonical và việc độc lập không phải chờ.
3. **Người chịu trách nhiệm nhận đáp án đúng phạm vi**
   Verify: owner nhận lựa chọn sản phẩm; người thao tác/reviewer nhận bằng chứng đo. Notes ghi vai trò/ngày; phần Draft/Pending chưa chọn vẫn giữ trạng thái.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C11
- source — _bmad-output/specs/shared/extraction-rules.md, §2.8, §4.4, §5–6, §8
- source — _bmad-output/specs/shared/ocr-rules.md, lines 11,15,59–63
- source — _bmad-output/implementation-artifacts/deferred-work.md, dòng 20–22,34–41
- source — _bmad-output/decisions/decision-owner-doc-clarifications-20261015.md, items 11–12, unapproved scope

## Notes

- Tracking: C11; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Chọn ngầm nguồn hoặc gộp sai người/thửa có thể tạo dữ liệu nghiệp vụ sai dù schema hợp lệ.
- Open question: Đáp án từng trường của các nguồn mâu thuẫn là gì? Có chọn quy tắc mới nào cho gộp nguồn/gộp ảnh, chuẩn hóa tiếng Việt hoặc classifier fallback sau khi đọc bằng chứng không?
- Ai chờ: chỉ thay luật/thuật toán dùng đáp án này. Nơi ghi: ledger nguồn của issue và decision hiện hành. Nguyên tắc F04/F05 đã chọn; đáp án mẫu trái nhau còn Pending. Decision72/editor tách-gộp chưa duyệt; sổ tiết kiệm/bảo hiểm chỉ nhận diện chưa hỗ trợ. Không OCR local/QR rescue, không nâng sửa xác suất thành dữ kiện; chu_su_dung chưa có đích persist.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

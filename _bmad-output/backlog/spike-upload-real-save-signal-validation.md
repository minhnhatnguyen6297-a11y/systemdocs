---
id: 26
type: spike
title: "Kiểm chứng ý nghĩa tín hiệu Lưu trên portal thật"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Kiểm chứng ý nghĩa tín hiệu Lưu trên portal thật

## Description

Thu bằng chứng an toàn về ý nghĩa phản hồi Lưu của portal thật: host, body, lỗi nghiệp vụ, từng trường và trường hợp chỉ lưu một phần. Một người có quyền cung cấp môi trường/nguồn đã che và xác nhận đối chiếu. Đây là kết quả verification độc lập với sửa race #11; HTTP 2xx một mình không đủ đóng scope này.

## Approach

Đọc bằng chứng sẵn có trước. Lập bảng điều gì đã biết từ code/mô phỏng và điều gì cần portal thật. Chỉ quan sát/thử trên môi trường và dữ liệu được phép, không tạo bản ghi thật ngoài phạm vi cho phép. Nếu thiếu môi trường hoặc nguồn phản hồi an toàn, ghi đúng giới hạn chưa giải quyết; không bịa kết quả đạt.

## Acceptance Criteria

1. **Có ma trận ý nghĩa phản hồi thật hoặc lỗ hổng được chỉ rõ**
   Verify: Notes ghi nguồn/host/phương thức/path/status và ý nghĩa body đã che cho thành công, lỗi nghiệp vụ và lưu một phần; từng trường chưa kiểm ghi chưa kiểm, không lấy 2xx làm bằng chứng đủ.
2. **Đối chiếu kết quả nghiệp vụ**
   Verify: người có quyền đối chiếu bản ghi và giá trị trường trong nguồn kiểm hợp lệ, ghi ca nào lưu đủ, thiếu hoặc chưa xác minh; không dựa chỉ vào điều hướng, đóng tab hoặc kết thúc chờ.
3. **Giữ phần chưa biết và người chờ**
   Verify: Notes có ngày, người xác nhận, phạm vi đã kiểm và phần unresolved. Chỉ các kết luận về độ tin cậy tín hiệu Lưu/đề xuất đổi tín hiệu sau này chờ đáp án; #11 không phải chờ.

## Boundaries

- Không thêm tín hiệu thành công, tự bấm Lưu, timeout thành thành công hoặc tự gửi lại.
- Record chưa rõ vẫn cần đối chiếu và không được gửi lại trước khi đối chiếu xong.
- Không nâng contract workflow Draft thành đã duyệt; không ghi cookie/token/body có dữ liệu cá nhân vào bằng chứng rộng.
- Thiếu bằng chứng portal thật là unresolved, không là kết quả passing từ mô phỏng hoặc HTTP 2xx.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C25
- source — _bmad-output/specs/upload_lab/README.md, §3.2, §5, dòng 197–205,225–226
- source — _bmad-output/tmp/owner-doc-decisions-20261015/save-detection-evidence.md, bằng chứng có sẵn và giới hạn

## Notes

- Tracking: C25; draft/chưa refined, chưa duyệt triển khai.
- Risk: medium — diễn giải sai bằng chứng có thể khiến đóng nhầm rủi ro gửi trùng hoặc lưu thiếu; spike này không đổi engine/tín hiệu.
- Open question: có môi trường portal/nguồn phản hồi đã che và quyền đối chiếu nào để chứng minh host/body/lỗi nghiệp vụ/từng trường/lưu một phần? Chỉ hỏi phần không lấy được từ nguồn sẵn có.
- Ai chờ: kết luận nghiệm thu tín hiệu thật và mọi đề xuất thay tín hiệu sau này. Nơi ghi đáp án: Notes issue và ledger bằng chứng private đã che, không mở gate cho sửa race #11.

## Tracking update — 15/10/2026

**Dropped:** quyết định owner [dùng dữ liệu web chính thức làm SOT và bỏ theo dõi Save](../decisions/decision-upload-web-sot-without-save-tracking.md) loại bỏ nhu cầu kiểm chứng tín hiệu Save thật làm gate. Nội dung spike được giữ làm lịch sử; C27/#28 là draft cutover runtime, không có approval triển khai.

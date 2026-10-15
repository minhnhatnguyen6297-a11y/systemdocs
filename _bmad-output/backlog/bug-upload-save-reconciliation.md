---
id: 11
type: bug
title: "Kết quả Lưu portal bị lệch khi đóng tab hoặc mất phản hồi"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: high
severity: P2
---

# Kết quả Lưu portal bị lệch khi đóng tab hoặc mất phản hồi

## Description

Mô phỏng đã ghi nhận phản hồi Lưu rồi đóng tab ngay có thể thành closed/cần đối chiếu; mất phản hồi có thể chờ vô hạn. Cần trạng thái đã biết/chưa rõ đúng và lối đối chiếu không mời gửi trùng.

## Reproduction

Bằng chứng Save ngày 15/10 và spec Upload ghi mô phỏng: nhận POST /api/hoso HTTP 2xx rồi đóng tab trước monitor; kết quả có thể closed/cần đối chiếu. Mất phản hồi khi còn ở trang tạo có thể chờ vô hạn. Không phải bằng chứng có bản ghi trùng trên portal thật.

## Cause Hypothesis

Xử lý tab đóng có thể được ưu tiên trước phản hồi đã nhận; đường chờ mất phản hồi chưa có ranh kết thúc/đối chiếu an toàn rõ.

## Acceptance Criteria

1. **Không mất phản hồi đã biết**
   **Given** tab v1 đã nhận tín hiệu Lưu thành công đang được công nhận
   **When** người dùng đóng trước vòng monitor kế
   **Then** giữ kết quả đã biết thay vì hạ trạng thái chỉ vì tab đóng
2. **Kết quả chưa rõ an toàn**
   **Given** chưa biết kết quả sau gián đoạn/mất phản hồi
   **When** người dùng tiếp tục kiểm hoặc kết thúc chờ
   **Then** dòng hiện rõ chưa xác minh/cần đối chiếu và có lối đối chiếu dùng được; không tự coi đã lưu, mở lại hoặc gửi lại
3. **Không mời gửi trùng**
   **Given** record chưa rõ và đợt chuẩn bị mới
   **When** người dùng chọn việc
   **Then** record chưa rõ không được gửi lại tới khi hoàn tất đối chiếu theo quy tắc
4. **Bằng chứng regression hoặc hành vi hiện có đúng**
   **Given** điều kiện đã ghi và các ca hợp lệ liền kề
   **When** nghiệm thu kết quả cuối
   **Then** bằng chứng theo hành vi phủ điều kiện và các biên đã đổi; hoặc chứng minh phạm vi hành vi không đổi đã đúng với phản ánh chưa xác minh. Không dùng kết luận này để bỏ yêu cầu hành vi mới của owner.

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C10
- source — _bmad-output/specs/upload_lab/README.md, §2.3, §3.2, §5
- source — _bmad-output/tmp/owner-doc-decisions-20261015/save-detection-evidence.md, recorded simulation and limitations

## Notes

- Tracking: C10; draft/chưa refined, chưa duyệt bắt đầu. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Đánh sai kết quả hoặc cho gửi lại hồ sơ chưa rõ có thể gây bản ghi trùng trên portal.
- Không thêm tín hiệu thành công, tự bấm Lưu, timeout thành thành công hoặc tự gửi lại. Phạm vi body/host/phản hồi portal thật vẫn chưa nghiệm thu; không nâng contract Draft. Điểm vào code: workflow/monitor browser của upload_lab. Refinement chốt đúng thao tác kết thúc chờ/đối chiếu.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

## Tracking update — 15/10/2026

**Dropped:** quyết định owner [bỏ theo dõi kết quả Lưu](../decisions/decision-upload-web-sot-without-save-tracking.md) thay thế hướng trong leaf này. Nội dung và acceptance cũ được giữ làm lịch sử, không còn là yêu cầu hiện hành. Phạm vi cutover runtime được theo dõi riêng ở C27/#28; không có approval triển khai.

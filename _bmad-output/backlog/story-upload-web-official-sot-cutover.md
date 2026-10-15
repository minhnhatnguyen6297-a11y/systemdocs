---
id: 28
type: story
title: "Bỏ theo dõi kết quả Lưu và giữ tiến độ chuẩn bị theo lượt"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: high
---

# Bỏ theo dõi kết quả Lưu và giữ tiến độ chuẩn bị theo lượt

## Description

App tiếp tục điền sẵn để người dùng tự Lưu trên website, nhưng chỉ giữ tiến độ chuẩn bị theo lượt và dùng dữ liệu website chính thức làm nguồn sự thật thay vì theo dõi kết quả Lưu.

## Acceptance Criteria

1. **Không suy kết quả Lưu**
   **Given** người dùng có thể tự Lưu hoặc chủ ý không Lưu biểu mẫu
   **When** POST, route/điều hướng, đóng tab, `finish_review` hoặc sự kiện cục bộ xảy ra
   **Then** app không hiển thị hoặc tích lũy trạng thái/số đếm đã Lưu, không tạo `needs_reconcile`, khóa hay bước giải phóng chỉ vì chưa rõ kết quả Lưu, không thực hiện retry/phục hồi hoặc lệnh/thao tác đối chiếu để phục hồi kết quả Lưu; trạng thái tab chỉ mô tả tài nguyên.
2. **Tiến lô thủ công không mang hồ sơ đã chuẩn bị sang lô sau**
   **Given** một lượt có lô tối đa 10 hồ sơ, trong đó 5 hồ sơ đã chuẩn bị nhưng người dùng chưa Lưu
   **When** người dùng chủ động tiếp tục lô
   **Then** chỉ các hồ sơ đã chọn còn chưa chuẩn bị trong lượt hiện tại được đưa tiếp; 5 hồ sơ đã chuẩn bị không tự được xếp lại, retry hoặc mở trong lô sau, và không có lô tự chạy.
3. **Dữ liệu website chính thức quyết định hiện diện trên web**
   **Given** sổ Excel chính thức được nạp theo website và khoảng ngày/năm
   **When** app phân loại hồ sơ có/thiếu trong sổ hoặc quét/chọn lại thủ công
   **Then** kết quả dùng ảnh chụp sổ hiện hành; không suy trạng thái từ browser; thao tác tải/nạp và đối chiếu thường lệ vẫn do người dùng khởi tạo, không thêm fetch hoặc phục hồi tự động.
4. **Giữ các bước không thuộc theo dõi Lưu**
   **Given** đăng nhập, job, chuẩn bị, lỗi thông thường, bước chờ kiểm tra hoặc phiên browser
   **When** người dùng xem tiến độ, xử lý lỗi, kết thúc chờ hoặc đóng phiên
   **Then** các trạng thái và điều khiển tương ứng vẫn hoạt động theo contract của chúng, không bị thay bằng trạng thái Lưu.

## Boundaries

- Giữ điền sẵn rồi dừng trước nút Lưu để người dùng tự kiểm tra và quyết định. Người dùng có thể chủ ý không Lưu do form lỗi, trùng hoặc lý do nghiệp vụ; owner chấp nhận rủi ro sự cố khi app không còn theo dõi kết quả Lưu.
- Giữ tiến độ chuẩn bị và quyền sở hữu tài nguyên trong lượt hiện tại; không biến chúng thành bằng chứng Lưu hoặc blacklist vĩnh viễn.
- Giữ phân loại theo dữ liệu website chính thức, tải/nạp Excel, quét, đăng nhập, tiến độ/lỗi job thông thường, kết thúc chờ và đóng phiên browser.
- Không thêm tự động fetch, retry/requeue hồ sơ chưa Lưu, tự mở lô kế hoặc đối chiếu phục hồi bắt buộc.
- Draft này không chứng nhận runtime đã đổi, không nâng contract Draft và không tự duyệt implementation ngoài phạm vi.

## References

- decision — _bmad-output/decisions/decision-upload-web-sot-without-save-tracking.md
- source — _bmad-output/specs/upload_lab/README.md, §1, §2.3, §3.2, §5
- contract — contracts/upload-workflow.md, §3–§7 (Draft)
- tracking — _bmad-output/backlog/README.md, C27

## Notes

- Tracking: C27; draft, `refined: false`, chưa duyệt bắt đầu. Thay thế phạm vi thực thi cũ #11 và gate bằng chứng #26; hai ID cũ được giữ nguyên ở trạng thái dropped.
- Risk: high — không còn theo dõi Save có thể khiến người dùng không nhận biết hồ sơ chưa được website ghi nhận; owner chấp nhận rủi ro này, nhưng tiến độ chuẩn bị không được làm người dùng hiểu nhầm hoặc tự lặp hồ sơ.
- Code map: `upload_lab/playwright_uploader.py:1930–2025`; `shell/sidecar/upload_session.py:466–532`; `shell/sidecar/upload_workspace_store.py:102–108, 140–177, 464–514`; `shell/sidecar/upload_adapter.py:1609–1659, 1787–2018, 2094–2134, 2137–2250`; `shell/src/renderer/upload/scan-upload.js:182–194, 243–284, 294–360, 487–510`; `shell/src/renderer/upload/index.js:454–466, 607–655`.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng SOT từ sổ chính thức, tiến độ khi năm hồ sơ đã chuẩn bị nhưng chưa Lưu, việc không phát sinh trạng thái browser-derived và các điều khiển thường lệ được giữ; ghi nhận ngoài tự kiểm của issue.

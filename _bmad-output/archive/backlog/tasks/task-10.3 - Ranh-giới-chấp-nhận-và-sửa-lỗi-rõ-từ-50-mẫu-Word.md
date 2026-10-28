---
id: TASK-10.3
title: Ranh giới chấp nhận và sửa lỗi rõ từ 50 mẫu Word
status: Done
assignee:
  - '@codex'
created_date: '2026-10-08 01:14'
updated_date: '2026-10-08 06:52'
labels:
  - regex
  - acceptance
  - corpus
dependencies: []
references:
  - .agents/task-10.2/DIFFS.md
  - docs/spec/upload_lab/regex-fields.md
  - docs/spec/upload_lab/regex-expected-results.md
parent_task_id: TASK-10
type: enhancement
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Owner yêu cầu phân loại E1-E7 và sửa lỗi đánh giá/regex rõ, đặt ranh giới chấp nhận. Phần regex lấy được từ nguồn lỗi điền vào ô Stage tương ứng đang có để user sửa; không thêm luật sửa lỗi nguồn hoặc UI/nút. Mẫu lạ ghi ngoài phạm vi/ứng viên phiên bản riêng; không tự đoán/sửa tên hay dữ liệu nguồn. Giữ F04/F05, TASK-10.2 evidence và working tree.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Mỗi nhóm E1-E7 có phân loại dựa nguồn/spec và ranh giới model lỗi/nguồn lỗi/mẫu ngoài phạm vi, không tự miễn lỗi máy
- [x] #2 Bộ so không chấm thiếu/null/sai cache thành đạt; so đúng tên/cờ năm/số dòng/field và báo kết quả theo phạm vi đã kiểm
- [x] #3 Các lỗi engine rõ được sửa dùng chung, mirror và có test baseline-fail/current-pass; chạy mới 50 file với hash/phiên bản
- [x] #4 Phần regex lấy được giữ chữ nguồn trong các ô Stage tương ứng đang có để user sửa; cảnh báo khi có căn cứ; không thêm luật sửa lỗi nguồn/UI, không tự sửa Word hoặc tự approve mẫu mới
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [x] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [x] #3 Tests pass
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Phân loại E1-E7 bằng nguồn/spec; ghi ranh giới owner. 2. Sửa comparator và lỗi engine rõ; mirror/native tests và review. 3. Giữ phần regex lấy được ở ô Stage tương ứng hiện có, sửa nhãn nơi cấp đúng nghĩa; thử sửa tay/lưu/mở lại, giữ typed guards. 4. Chạy mới50file và extract độc lập; lưu hashes/scope, source_review/unsupported/Pending riêng.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Owner trả lời rõ: không thêm chức năng. Dán khối nghi vấn vào kết quả ở Stage cho user tự sửa; ví dụ CCCD0123456789do Bộ Coongan cấp. Không tự sửa chính tả hay lấy nơi cấp GCN bù CCCD.

Owner làm rõ lần cuối: không thêm luật xử lý lỗi nguồn. Regex lấy được gì thì điền vào ô Stage tương ứng đang có; cảnh báo khi có căn cứ. Không yêu cầu thêm ô nguyên văn hay bắt chọn một kiểu dán riêng. Spec: docs/spec/upload_lab/regex-acceptance.md, input/docx-import.md và stage.md. Plan .agents/task-10.3/plan.md; thực thi trong phạm vi đã được yêu cầu triển khai/tiếp tục.

Decision-74 ghi quyết định owner; lý do và phạm vi tại docs/spec/upload_lab/regex-acceptance.md. Đã chạy độc lập native baseline50:61 người/4 bản ghi đất; hash nguồn50/50. Giữ đáp án/bằng chứng cũ; địa chỉ3970 đính chính theo nguồn line42.

Hoàn tất: .agents/task-10.3/RESULT.md. Fresh50-final-reviewed:76người/13mô tả đất;48file khớp trường đã kiểm+2source_review do chữ dính;638checked/520unanswered. Payload độc lập50/50; nguồn50 và110evidence cũ giữ nguyên. Source-party41người/15file:0sai sau sửa. Review patches đã kiểm/mirror; F04/F05 nguyên trạng. Stage Chromium+realDB nhận chữ nguồn/sửa tay/lưu/mở lại và chặn ngày sai đạt. Upload424/2skip,Tool207/1skip,DOCX62,renderer99pass;3Word-dialog failures có sẵn tái hiện trên beforeview, không thuộc task. Decision74/spec đã ghi là gì/tại sao; không commit/push.

Owner 08/10/2026 yêu cầu commit và gộp vào nhánh chính, xử lý xung đột. Cho phép commit thay giới hạn no-commit trước đó. Main consolidate/monorepo tại76bb9a8 đã chuyển SOT sang _bmad-output/specs, bỏ Backlog live. Khi gộp giữ cấu trúc/quyết định48 của main; chuyển các spec và decision mới, lưu task cũ ở archive. Giữ corpus/bằng chứng cá nhân tại máy, không đưa môi trường test/database/Word thật vào commit. Kiểm lại kết quả sau gộp; không push.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Sửa lỗi rõ E1-E7 và bộ chấm theo ranh giới owner; giữ chữ nguồn tại ô Stage hiện có để sửa tay. Fresh50:48khớp các trường đã kiểm,2cần kiểm nguồn; đủ76người/13mô tả đất. Native/mutation/review/Stage thực đã kiểm; các test liên quan đạt,3lỗi Word-dialog cũ tách riêng. Bằng chứng .agents/task-10.3/RESULT.md, final-evidence.json. F04/F05 Pending; mốc3980.
<!-- SECTION:FINAL_SUMMARY:END -->

---
id: decision-owner-remove-historical-report-issue-20261017
title: "Owner bỏ issue 12 report lịch sử, sẽ tạo issue khác"
date: '2026-10-17'
status: accepted
---

## Bối cảnh

Sau khi công bố bằng chứng còn lấy được của **#18 / C17** (12 report lịch sử mất ghi chú) và **gửi câu hỏi một lần dạng bảng 12 dòng trong hội thoại**, owner trả lời trong phiên 17/10/2026, nguyên văn:

> xóa bỏ luôn issue gồm các lỗi này, tôi sẽ tạo issue khác và giải quyết

Câu trả lời áp cho **#18 cùng C17 và cả 12 report lịch sử** liên quan — đúng issue vừa được hỏi.

## Quyết định

- **Bỏ issue đang hoạt động** gồm các lỗi này: gỡ leaf `_bmad-output/backlog/spike-historical-report-note-triage.md` và mọi tham chiếu đang hoạt động của C17/#18 khỏi catalog/backlog.
- Đây **không** phải kết luận 12 report là bug đã xác định, cũng **không** phải đã xử lý/đóng triệu chứng nào. Owner sẽ **tự tạo issue khác** để giải quyết; **không** tạo issue thay owner và **không** dùng placeholder.
- **Không dùng lại ID #18** cho việc khác.
- Giữ nguyên bản ghi lịch sử: toàn bộ nội dung leaf cũ còn nguyên ở Git trong commit `8e8d0c1b298a13ab752166b5c6fdef1c06bcb826` (baseline `366073b526ac59dbea08d22bbb3a7a465e956872`), nên không cần bản sao archive/di chuyển khối. Không viết lại commit lịch sử và không sửa decision cũ đã accepted.
- Không xóa báo cáo gốc, JSON/PNG private, evidence tmp hoặc lịch sử; các issue khác không bị ảnh hưởng.

## Hệ quả

- Backlog đang hoạt động giữ **một dòng lịch sử ngắn** cho #18 (đã bỏ theo owner, có ngày + link decision này), **không** còn bảng 12 record, **không** còn câu hỏi chờ người báo và **không** còn cổng `UNVERIFIED`/chờ đầu vào.
- **Không** theo đuổi triệu chứng nữa: câu hỏi một lần (bảng 12 dòng) **đã được gửi trong hội thoại**; owner yêu cầu **bỏ issue** thay vì bổ sung triệu chứng, nên **không tiếp tục hỏi/thu thập** và không suy đoán câu trả lời cho từng trường.
- Việc built **riêng** trước đó vẫn nguyên: flow lưu comment tự gõ (plan `plan-visual-bug-comment-capture.md`, harness hiện hành `tools/visual-bug-reporting/`) và lỗi console dòng 312 đã xử lý ở #4/C03 — không mở lại ở đây.
- Quyết định này **gỡ chặn #18**: tiếp tục thứ tự backlog, kế tiếp **#19** sau khi xuất bản bản ghi này. Không cần decision mới cho phần bỏ issue.
- Đồng bộ [catalog](../backlog/README.md) và các guard liên quan trong backlog cùng phiên; không đổi spec, code hay NotaryOffice.

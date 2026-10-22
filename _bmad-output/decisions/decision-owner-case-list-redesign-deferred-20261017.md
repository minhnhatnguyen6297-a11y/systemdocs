---
id: decision-owner-case-list-redesign-deferred-20261017
title: "Owner để Danh sách hồ sơ làm lại, sẽ tự triển khai spec sau"
date: '2026-10-17'
status: accepted
---

## Nguồn

Sau khi công bố bằng chứng và đề xuất phạm vi của **#20 / C19** trong hội thoại, owner trả lời trong phiên 17/10/2026, nguyên văn:

```
chức năng này cần làm lại, note lại phương hướng (chưa chốt chắc chắn):
- tuân theo rule mọi input, output phải theo chuẩn database.
- Mỗi hồ sơ (hiển thị dạng thẻ) trong danh sách hồ sơ sẽ hiển thị những trường gì? được quyền search trường gì?
- Khi filter thì filter trường gì?
- Search và filter tôi chưa chốt những trường gì mà chức năng này được phép gửi request đến database? 
- Dự kiến: Mỗi thẻ chia làm 3 vùng: 
+ NGười: Tên, số giấy tờ
+ Tài sản: Số serial, địa chỉ, tên chủ đất (trường này chưa tồn tại hoặc chưa được chốt rõ ở bảng dữ liệu nào, chỉ có quan hệ chủ đất trong hồ sơ thừa kế)
+ Hồ sơ: ngày tạo, loại hồ sơ, tình trạng xử lý (đang làm, xuất xong)
### ghi lại đoạn này vào issue, nguyên văn, tôi sẽ triển khai spec sau. Chuyển issue tiếp
```

## Quyết định

- Chức năng Danh sách hồ sơ **làm lại**; nay **DEFERRED** — owner sẽ tự triển khai spec sau. Lượt này **không** giao viết spec, không đổi runtime, contract hoặc code.
- Owner yêu cầu mọi input/output tuân theo chuẩn database; whitelist trường, mapping cụ thể và phạm vi request chưa chốt.
- Phần còn lại của đoạn trên là **phương hướng Draft, owner tự ghi "chưa chốt chắc chắn"**: bố cục thẻ 3 vùng (Người/Tài sản/Hồ sơ), enum trạng thái ("đang làm"/"xuất xong"), nghĩa "ngày tạo", vị trí DB của "tên chủ đất", whitelist trường hiển thị/search/filter và mapping cụ thể **chưa được duyệt**.
- Đề xuất phạm vi Q1/Q2 của trợ lý trước đó **chưa được duyệt; không còn là câu hỏi đang hoạt động**; giữ nguyên làm bằng chứng lịch sử, không xóa.
- **Không** hỏi lại #20 và không tạo câu hỏi nghiệp vụ mới cho lượt này.

## Hệ quả

- Trạng thái #20 đổi từ "BLOCKED — chờ owner trả lời" thành "owner trả lời 17/10/2026 — làm lại DEFERRED"; giữ leaf, Draft/`refined: false`, không built.
- Ranh giới lượt này: **không** sửa runtime/contract/code, kể cả lỗi lọc-sau-`limit` trong `case_list` đã tái hiện 17/10/2026 vẫn **chưa sửa** (việc developer độc lập, không thuộc quyết định hoãn này).
- Đồng bộ [leaf #20](../backlog/spike-case-list-query-labels.md), [catalog C19](../backlog/README.md), [spec Notary §2/§9](../specs/notary_v2/README.md) và [sổ tay](../specs/product-overview.md) trong cùng phiên.

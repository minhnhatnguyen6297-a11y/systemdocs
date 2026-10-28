---
id: decision-issues-reconciliation-20261015
title: Gom report và việc chưa hoàn tất thành nhiều issue có thứ tự
date: '2026-10-15'
status: accepted
---

## Quyết định về cách theo dõi

Owner yêu cầu sau lần viết lại spec: gom mọi bug đã báo và các việc chưa rõ/chưa triển khai thành các issue, cùng đề xuất thứ tự thực hiện. Yêu cầu nhiều issue thay riêng lựa chọn giữ một ticket tổng ngày 13/10 được ghi trong backlog #1.

Lúc lập ban đầu, catalog ánh xạ 26 draft C01–C26 tới #2–#27. Hai scope bổ sung sau review là kiểm chứng tín hiệu Lưu portal thật (#26) và văn bản hành chính cùng ngày (#27). Quyết định owner ngày 15/10 sau đó đã bỏ scope theo dõi Lưu: #11 và #26 được giữ nguyên ID nhưng chuyển dropped; C27/#28 là draft cutover mới. Mười hai report mất ghi chú vẫn là 12 bản ghi độc lập; không đoán triệu chứng hoặc root cause.

## Ranh giới

Đợt này chỉ tạo draft issue, catalog và ánh xạ nguồn. Tất cả leaf mới giữ `refined: false`; không duyệt triển khai sản phẩm, không tự chọn luật nghiệp vụ, không thay active initiative. Theo quy tắc repo, commit tài liệu sau kiểm độc lập; commit tài liệu không duyệt triển khai hoặc publishing sản phẩm. Thứ tự khuyến nghị không tự thành dependency cứng.

Các quyết định sản phẩm mới nhất vẫn có hiệu lực theo spec và quyết định 15/10. Không khôi phục thiết kế theo dõi bản in hoặc phục hồi tên người chết theo tên viết tắt. Zalo giữ nghiên cứu/pháp lý riêng; các ý tưởng chưa chốt không trở thành quyền implementation do có mặt trong catalog.

## Nguồn và hệ quả

Nguồn: yêu cầu owner trong phiên gom issue 15/10/2026; `_bmad-output/decisions/decision-readable-module-specs-20261015.md`; `_bmad-output/decisions/decision-owner-doc-clarifications-20261015.md`.

Dữ liệu cá nhân, raw notes và ảnh report giữ trong bằng chứng private ignored; catalog và issue chỉ ghi tóm tắt đã che và ID truy vết. Spec mô tả yêu cầu, không là bằng chứng runtime đã hoàn tất. Catalog ghi rõ lựa chọn còn chờ, phạm vi verification chưa có và các việc parked/excluded.

## Cập nhật theo quyết định owner — 15/10/2026

Catalog hiện có 27 ID leaf #2–#28; 25 active leaf chưa refined và hai leaf #11/#26 dropped. #1 vẫn tracking-only. #26 không còn là gate kiểm chứng tín hiệu portal; plan #11 giữ nguyên lịch sử nhưng câu hỏi A/B đã retired. C27/#28 ghi cutover runtime theo quyết định mới, vẫn là draft và không duyệt implementation.
